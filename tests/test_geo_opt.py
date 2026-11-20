from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
import random
import unittest

from geo_opt import (
    Aggregation, GeoEdge, GeoGraphRevision, GeoHierarchyRelation, GeoNode,
    GeoWeightDefinition, GeoWeightProfile, GeoWeightValue, GraphValidationError,
    RoutingPolicy, SearchLimitExceeded, WeightKind, WeightSubject, astar,
    compile_graph, dijkstra, yen_top_k, verify_route, RoutePath,
)


def make_graph(*, nodes=None, edges=None, hierarchy=None, edge_costs=None,
               node_costs=None, demand=None, revision="r1"):
    if nodes is None:
        nodes = ("ROOT", "A", "B", "C", "T")
    nodes = tuple(GeoNode(n, "CENTRAL" if n == "ROOT" else "TERMINAL" if n == "T" else "TRANSIT") for n in nodes)
    if edges is None:
        edges = (("ra", "ROOT", "A"), ("at", "A", "T"),
                 ("rb", "ROOT", "B"), ("bt", "B", "T"),
                 ("rc", "ROOT", "C"), ("ct", "C", "T"))
    if hierarchy is None:
        hierarchy = tuple(("ROOT", n.node_id) for n in nodes if n.node_id != "ROOT")
    if edge_costs is None:
        edge_costs = {"ra": "2", "at": "3", "rb": "3", "bt": "4", "rc": "4", "ct": "5"}
    definitions = [GeoWeightDefinition("cost", WeightSubject.EDGE, WeightKind.COST, "unit")]
    profiles = [GeoWeightProfile(WeightSubject.EDGE, e[0], (GeoWeightValue("cost", edge_costs[e[0]]),))
                for e in edges if e[0] in edge_costs]
    if node_costs is not None:
        definitions.append(GeoWeightDefinition("visit", WeightSubject.NODE, WeightKind.COST, "unit"))
        profiles.extend(GeoWeightProfile(WeightSubject.NODE, n.node_id,
                                         (GeoWeightValue("visit", node_costs.get(n.node_id, "0")),)) for n in nodes)
    if demand is not None:
        definitions.append(GeoWeightDefinition("demand", WeightSubject.NODE, WeightKind.DEMAND, "kg", Aggregation.SUM))
        for n in nodes:
            v = GeoWeightValue("demand", demand.get(n.node_id, "0"))
            match = next((p for p in profiles if p.subject == WeightSubject.NODE and p.subject_id == n.node_id), None)
            if match is None:
                profiles.append(GeoWeightProfile(WeightSubject.NODE, n.node_id, (v,)))
            else:
                profiles[profiles.index(match)] = GeoWeightProfile(WeightSubject.NODE, n.node_id, match.values + (v,))
    return GeoGraphRevision(
        "tenant-test", "g1", revision, "ROOT", nodes, tuple(GeoEdge(*e) for e in edges),
        tuple(GeoHierarchyRelation(*rel) for rel in hierarchy),
        tuple(definitions), tuple(profiles),
    )


class ContractTests(unittest.TestCase):
    def test_invalid_coordinates(self):
        for lat, lon in [("91", "0"), ("0", "181"), ("NaN", "0"), ("0", "Inf")]:
            with self.subTest(lat=lat, lon=lon), self.assertRaises(GraphValidationError):
                GeoNode("A", "TRANSIT", lat, lon)
        with self.assertRaises(GraphValidationError):
            GeoNode("A", "TRANSIT", "1", None)
        self.assertEqual(GeoNode("A", "X", "43.25", "76.9").latitude, Decimal("43.25"))

    def test_float_rejected_and_null_is_not_zero(self):
        with self.assertRaises(GraphValidationError):
            GeoWeightValue("cost", 2.0)
        with self.assertRaises(GraphValidationError):
            GeoWeightValue("cost", "NaN")
        self.assertIsNone(GeoWeightValue("cost", None).value)

    def test_frozen_contract(self):
        node = GeoNode("A", "TRANSIT")
        with self.assertRaises(FrozenInstanceError):
            node.node_type = "B"  # type: ignore[misc]

    def test_unknown_crs(self):
        from dataclasses import replace
        with self.assertRaises(GraphValidationError):
            replace(make_graph(), crs="EPSG:3857")

    def test_immutable_profiles(self):
        values = [GeoWeightValue("cost", "1")]
        p = GeoWeightProfile(WeightSubject.EDGE, "E", values)  # type: ignore[arg-type]
        values.append(GeoWeightValue("other", "3"))
        self.assertEqual(len(p.values), 1)
        with self.assertRaises(GraphValidationError):
            GeoWeightProfile(WeightSubject.EDGE, "E", (GeoWeightValue("cost", "1"), GeoWeightValue("cost", "2")))


class CompilerTests(unittest.TestCase):
    def test_golden_subtree_demand(self):
        graph = compile_graph(make_graph(demand={"ROOT": "1", "A": "4", "B": "2", "C": "3", "T": "5"}))
        self.assertEqual(graph.subtree_aggregate("ROOT", "demand"), Decimal("15"))
        self.assertEqual(graph.subtree_aggregate("A", "demand"), Decimal("4"))

    def test_nonadditive_aggregation_rejected(self):
        graph = compile_graph(make_graph())
        with self.assertRaises(GraphValidationError):
            graph.subtree_aggregate("ROOT", "cost")

    def test_max_depth_60_allowed(self):
        names = ("ROOT",) + tuple(f"N{i}" for i in range(1, 61))
        graph = compile_graph(make_graph(nodes=names, edges=(), hierarchy=tuple(zip(names, names[1:])), edge_costs={}))
        self.assertEqual(graph.depth["N60"], 60)
        with self.assertRaises(GraphValidationError):
            compile_graph(make_graph(nodes=names, edges=(), hierarchy=tuple(zip(names, names[1:])), edge_costs={}), max_depth=59)

    def test_5000_nodes_no_recursion(self):
        names = ("ROOT",) + tuple(f"N{i}" for i in range(1, 5000))
        graph = compile_graph(make_graph(nodes=names, edges=(), hierarchy=tuple(zip(names, names[1:])), edge_costs={}), max_depth=5000)
        self.assertEqual(graph.depth["N4999"], 4999)

    def test_hierarchy_cycle_rejected(self):
        graph = make_graph(nodes=("ROOT", "A", "B", "C"), edges=(), edge_costs={},
                           hierarchy=(("ROOT", "A"), ("B", "C"), ("C", "B")))
        with self.assertRaises(GraphValidationError):
            compile_graph(graph)

    def test_root_has_parent_rejected(self):
        graph = make_graph(nodes=("ROOT", "A"), edges=(), edge_costs={},
                           hierarchy=(("ROOT", "A"), ("A", "ROOT")))
        with self.assertRaises(GraphValidationError):
            compile_graph(graph)

    def test_second_parent_rejected(self):
        graph = make_graph(nodes=("ROOT", "A", "B"), edges=(), edge_costs={},
                           hierarchy=(("ROOT", "A"), ("ROOT", "B"), ("A", "B")))
        with self.assertRaises(GraphValidationError):
            compile_graph(graph)

    def test_disconnected_rejected(self):
        with self.assertRaises(GraphValidationError):
            compile_graph(make_graph(hierarchy=(("ROOT", "A"),)))

    def test_unknown_edge_endpoint_rejected(self):
        with self.assertRaises(GraphValidationError):
            compile_graph(make_graph(edges=(("e", "ROOT", "MISSING"),), edge_costs={"e": "1"}))

    def test_duplicate_node_and_edge_rejected(self):
        from dataclasses import replace
        source = make_graph()
        with self.assertRaises(GraphValidationError):
            compile_graph(replace(source, nodes=source.nodes + (source.nodes[0],)))
        with self.assertRaises(GraphValidationError):
            compile_graph(replace(source, edges=source.edges + (source.edges[0],)))

    def test_unknown_weight_subject_and_code(self):
        from dataclasses import replace
        source = make_graph()
        wrong = GeoWeightProfile(WeightSubject.NODE, "MISSING", (GeoWeightValue("cost", "1"),))
        with self.assertRaises(GraphValidationError):
            compile_graph(replace(source, profiles=source.profiles + (wrong,)))
        wrong = GeoWeightProfile(WeightSubject.EDGE, "ra", (GeoWeightValue("bogus", "1"),))
        with self.assertRaises(GraphValidationError):
            compile_graph(replace(source, profiles=(wrong,) + source.profiles[1:]))

    def test_duplicate_profile_rejected(self):
        from dataclasses import replace
        source = make_graph()
        with self.assertRaises(GraphValidationError):
            compile_graph(replace(source, profiles=source.profiles + (source.profiles[0],)))

    def test_negative_cost_rejected(self):
        with self.assertRaises(GraphValidationError):
            compile_graph(make_graph(edge_costs={"ra": "-1", "at": "3", "rb": "3", "bt": "4", "rc": "4", "ct": "5"}))

    def test_digest_stable_across_order_changes(self):
        from dataclasses import replace
        base = make_graph()
        shuffled = replace(base, nodes=tuple(reversed(base.nodes)), edges=tuple(reversed(base.edges)),
                           hierarchy=tuple(reversed(base.hierarchy)), profiles=tuple(reversed(base.profiles)))
        self.assertEqual(compile_graph(base).fingerprint, compile_graph(shuffled).fingerprint)
        modified = replace(base, revision="r2")
        self.assertNotEqual(compile_graph(base).fingerprint, compile_graph(modified).fingerprint)
        other_tenant = replace(base, scope_id="tenant-other")
        self.assertNotEqual(compile_graph(base).fingerprint, compile_graph(other_tenant).fingerprint)

    def test_routing_can_cycle_while_hierarchy_is_tree(self):
        graph = compile_graph(make_graph(edges=(("e1", "ROOT", "A"), ("e2", "A", "ROOT")),
                                         edge_costs={"e1": "1", "e2": "2"}))
        self.assertEqual(graph.depth["A"], 1)
        self.assertEqual(graph.outgoing["A"], ("e2",))

    def test_resource_bound(self):
        with self.assertRaises(GraphValidationError):
            compile_graph(make_graph(), max_edges=1)

    def test_compiled_mapping_read_only(self):
        graph = compile_graph(make_graph())
        with self.assertRaises(TypeError):
            graph.outgoing["A"] = ()  # type: ignore[index]


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.graph = compile_graph(make_graph())
        self.policy = RoutingPolicy("cost")

    def test_golden_dijkstra_and_astar(self):
        route = dijkstra(self.graph, "ROOT", "T", self.policy)
        self.assertEqual(route.node_ids, ("ROOT", "A", "T"))
        self.assertEqual(route.total_cost, Decimal("5"))
        h = {"ROOT": "5", "A": "3", "B": "4", "C": "5", "T": "0"}
        self.assertEqual(astar(self.graph, "ROOT", "T", self.policy, h), route)

    def test_postsolve_verification(self):
        route = dijkstra(self.graph, "ROOT", "T", self.policy)
        verify_route(self.graph, "ROOT", "T", self.policy, route)
        with self.assertRaises(GraphValidationError):
            verify_route(self.graph, "ROOT", "T", self.policy,
                         RoutePath(route.node_ids, route.edge_ids, Decimal("0")))
        with self.assertRaises(GraphValidationError):
            verify_route(self.graph, "ROOT", "T", self.policy,
                         RoutePath(("ROOT", "T", "A"), route.edge_ids, route.total_cost))

    def test_frontier_limit_fails_closed(self):
        with self.assertRaises(SearchLimitExceeded):
            dijkstra(self.graph, "ROOT", "T", RoutingPolicy("cost", max_frontier_items=1))

    def test_top_three_golden(self):
        routes = yen_top_k(self.graph, "ROOT", "T", self.policy)
        self.assertEqual([r.total_cost for r in routes], [Decimal("5"), Decimal("7"), Decimal("9")])
        self.assertEqual([r.node_ids[1] for r in routes], ["A", "B", "C"])
        self.assertEqual(len({r.edge_ids for r in routes}), 3)

    def test_two_routes_when_branch_blocked(self):
        policy = RoutingPolicy("cost", blocked_nodes=frozenset({"B"}))
        routes = yen_top_k(self.graph, "ROOT", "T", policy)
        self.assertEqual([r.total_cost for r in routes], [Decimal("5"), Decimal("9")])

    def test_direction_is_strict(self):
        self.assertIsNone(dijkstra(self.graph, "T", "ROOT", self.policy))

    def test_unreachable_without_fabrication(self):
        self.assertIsNone(dijkstra(self.graph, "ROOT", "T", RoutingPolicy("cost", blocked_nodes=frozenset({"T"}))))
        self.assertEqual(yen_top_k(self.graph, "ROOT", "T", RoutingPolicy("cost", blocked_nodes=frozenset({"T"}))), ())

    def test_node_service_cost_per_entry(self):
        graph = compile_graph(make_graph(node_costs={"A": "4"}))
        routes = yen_top_k(graph, "ROOT", "T", RoutingPolicy("cost", "visit"))
        self.assertEqual([r.total_cost for r in routes], [Decimal("7"), Decimal("9"), Decimal("9")])
        self.assertEqual(routes[0].node_ids[1], "B")

    def test_missing_cost_is_not_zero(self):
        costs = {"ra": "2", "at": "3", "rb": "3", "bt": "4", "rc": "4"}
        graph = compile_graph(make_graph(edge_costs=costs))
        with self.assertRaises(GraphValidationError):
            dijkstra(graph, "ROOT", "T", self.policy)

    def test_null_cost_is_not_zero(self):
        costs = {"ra": None, "at": "3", "rb": "3", "bt": "4", "rc": "4", "ct": "5"}
        graph = compile_graph(make_graph(edge_costs=costs))
        with self.assertRaises(GraphValidationError):
            dijkstra(graph, "ROOT", "T", self.policy)

    def test_bad_heuristic_is_rejected(self):
        with self.assertRaises(GraphValidationError):
            astar(self.graph, "ROOT", "T", self.policy, {"ROOT": "100", "A": "0", "B": "0", "C": "0", "T": "0"})
        with self.assertRaises(GraphValidationError):
            astar(self.graph, "ROOT", "T", self.policy, {"T": "0"})

    def test_type_filter(self):
        policy = RoutingPolicy("cost", allowed_node_types=frozenset({"CENTRAL", "TERMINAL"}))
        self.assertIsNone(dijkstra(self.graph, "ROOT", "T", policy))

    def test_search_budget_fails_closed(self):
        with self.assertRaises(SearchLimitExceeded):
            dijkstra(self.graph, "ROOT", "T", RoutingPolicy("cost", max_expansions=1))

    def test_k_budget_fails_closed(self):
        # Two alternative spurs are discovered while deviating from ROOT->A->T.
        edges = (("ra", "ROOT", "A"), ("at", "A", "T"),
                 ("rb", "ROOT", "B"), ("bt", "B", "T"),
                 ("ab", "A", "B"))
        costs = {"ra": "1", "at": "1", "rb": "2", "bt": "2", "ab": "1"}
        graph = compile_graph(make_graph(nodes=("ROOT", "A", "B", "T"), edges=edges, edge_costs=costs))
        with self.assertRaises(SearchLimitExceeded):
            yen_top_k(graph, "ROOT", "T", self.policy, max_candidates=1)

    def test_change_cost_changes_fingerprint_and_route(self):
        old = self.graph
        newcosts = {"ra": "20", "at": "3", "rb": "3", "bt": "4", "rc": "4", "ct": "5"}
        new = compile_graph(make_graph(edge_costs=newcosts))
        self.assertNotEqual(old.fingerprint, new.fingerprint)
        self.assertEqual(dijkstra(old, "ROOT", "T", self.policy).total_cost, Decimal("5"))
        self.assertEqual(dijkstra(new, "ROOT", "T", self.policy).total_cost, Decimal("7"))

    def test_randomized_small_graphs_against_exhaustive_reference(self):
        rng = random.Random(42)
        for case in range(20):
            names = ("ROOT", "A", "B", "C", "T")
            available = [(a, b) for a in names for b in names if a != b]
            chosen = rng.sample(available, 9)
            edges = tuple((f"e{i:02}", a, b) for i, (a, b) in enumerate(chosen))
            costs = {e[0]: str(rng.randint(1, 9)) for e in edges}
            graph = compile_graph(make_graph(nodes=names, edges=edges, edge_costs=costs))
            results = yen_top_k(graph, "ROOT", "T", self.policy, k=3)
            exhaustive = []
            def enumerate_paths(at, visited, selected, cost):
                if at == "T":
                    exhaustive.append((cost, tuple(selected)))
                    return
                for edge_id in graph.outgoing[at]:
                    edge = graph.edges[edge_id]
                    if edge.to_node not in visited:
                        enumerate_paths(edge.to_node, visited | {edge.to_node}, selected + [edge_id],
                                        cost + graph.weight(WeightSubject.EDGE, edge_id, "cost"))
            enumerate_paths("ROOT", {"ROOT"}, [], Decimal(0))
            expected = sorted(exhaustive)[:3]
            self.assertEqual([(r.total_cost, r.edge_ids) for r in results], expected, msg=f"case={case}")


if __name__ == "__main__":
    unittest.main()
