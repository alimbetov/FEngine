"""Reference Dijkstra, consistent-heuristic A*, and Yen loopless K-shortest paths.

Only directed, nonnegative, additive and static weights are supported in R0.
A* heuristics are validated for consistency before the search.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from heapq import heappop, heappush
from typing import Mapping

from .compiler import CompiledGeoGraph
from .model import GraphValidationError, WeightKind, WeightSubject, dec


class SearchLimitExceeded(RuntimeError):
    """Fail-closed resource limit instead of a partial claim of optimality."""


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    edge_cost_code: str
    node_visit_cost_code: str | None = None
    blocked_nodes: frozenset[str] = frozenset()
    blocked_edges: frozenset[str] = frozenset()
    allowed_node_types: frozenset[str] | None = None
    max_expansions: int = 100_000
    max_frontier_items: int = 500_000

    def __post_init__(self) -> None:
        if not self.edge_cost_code or self.max_expansions < 1 or self.max_frontier_items < 1:
            raise GraphValidationError("invalid routing policy")
        object.__setattr__(self, "blocked_nodes", frozenset(self.blocked_nodes))
        object.__setattr__(self, "blocked_edges", frozenset(self.blocked_edges))
        if self.allowed_node_types is not None:
            object.__setattr__(self, "allowed_node_types", frozenset(self.allowed_node_types))


@dataclass(frozen=True, slots=True)
class RoutePath:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    total_cost: Decimal


def _valid_policy(graph: CompiledGeoGraph, policy: RoutingPolicy) -> None:
    edge_def = graph.definitions.get((WeightSubject.EDGE, policy.edge_cost_code))
    if edge_def is None or edge_def.kind != WeightKind.COST:
        raise GraphValidationError("routing edge cost must have COST definition")
    if policy.node_visit_cost_code is not None:
        node_def = graph.definitions.get((WeightSubject.NODE, policy.node_visit_cost_code))
        if node_def is None or node_def.kind != WeightKind.COST:
            raise GraphValidationError("node visit cost must have COST definition")
        if edge_def.unit != node_def.unit:
            raise GraphValidationError("node and edge cost units differ")
    for edge in graph.edges.values():
        graph.weight(WeightSubject.EDGE, edge.edge_id, policy.edge_cost_code)
    if policy.node_visit_cost_code is not None:
        for node in graph.nodes:
            graph.weight(WeightSubject.NODE, node, policy.node_visit_cost_code)
    if not policy.blocked_nodes.issubset(graph.nodes) or not policy.blocked_edges.issubset(graph.edges):
        raise GraphValidationError("blocked ID does not exist")


def _step_cost(graph: CompiledGeoGraph, policy: RoutingPolicy, edge_id: str) -> Decimal:
    e = graph.edges[edge_id]
    cost = graph.weight(WeightSubject.EDGE, edge_id, policy.edge_cost_code)
    if policy.node_visit_cost_code is not None:
        cost += graph.weight(WeightSubject.NODE, e.to_node, policy.node_visit_cost_code)
    if cost < 0:
        raise GraphValidationError("routing requires nonnegative additive costs")
    return cost


def _allowed_node(graph: CompiledGeoGraph, policy: RoutingPolicy, node: str) -> bool:
    return (node not in policy.blocked_nodes and
            (policy.allowed_node_types is None or graph.nodes[node].node_type in policy.allowed_node_types))


def shortest_path(graph: CompiledGeoGraph, source: str, target: str, policy: RoutingPolicy,
                  *, heuristic: Mapping[str, Decimal | str] | None = None,
                  excluded_nodes: frozenset[str] = frozenset(),
                  excluded_edges: frozenset[str] = frozenset()) -> RoutePath | None:
    """Dijkstra (heuristic=None), or A* with provably consistent potential.

    Returns None on no path; resource limits raise, not return a fake solution.
    Node visit COST is charged on each entry, excluding the initial source.
    """
    _valid_policy(graph, policy)
    if source not in graph.nodes or target not in graph.nodes:
        raise GraphValidationError("unknown source or target")
    if not _allowed_node(graph, policy, source) or not _allowed_node(graph, policy, target):
        return None
    if source in excluded_nodes or target in excluded_nodes:
        return None
    blocked_nodes = policy.blocked_nodes | excluded_nodes
    blocked_edges = policy.blocked_edges | excluded_edges
    h = {v: Decimal(0) for v in graph.nodes}
    if heuristic is not None:
        if set(heuristic) != set(graph.nodes):
            raise GraphValidationError("A* heuristic must cover all nodes")
        h = {v: dec(value) for v, value in heuristic.items()}
        if any(val < 0 for val in h.values()) or h[target] != 0:
            raise GraphValidationError("A* heuristic must be nonnegative and target zero")
        for edge_id, edge in graph.edges.items():
            if h[edge.from_node] > _step_cost(graph, policy, edge_id) + h[edge.to_node]:
                raise GraphValidationError("A* heuristic is inconsistent (not proven safe)")
    heap: list[tuple[Decimal, Decimal, tuple[str, ...], tuple[str, ...], str]] = []
    heappush(heap, (h[source], Decimal(0), (), (source,), source))
    settled: set[str] = set()
    expanded = 0
    while heap:
        _, cost, edge_path, node_path, u = heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        expanded += 1
        if expanded > policy.max_expansions:
            raise SearchLimitExceeded("path search exceeded expansion budget")
        if u == target:
            return RoutePath(node_path, edge_path, cost)
        for edge_id in graph.outgoing[u]:
            if edge_id in blocked_edges:
                continue
            v = graph.edges[edge_id].to_node
            if v in settled or v in blocked_nodes or not _allowed_node(graph, policy, v):
                continue
            step = _step_cost(graph, policy, edge_id)
            new_cost = cost + step
            if len(heap) >= policy.max_frontier_items:
                raise SearchLimitExceeded("path search exceeded frontier budget")
            heappush(heap, (new_cost + h[v], new_cost,
                            edge_path + (edge_id,), node_path + (v,), v))
    return None


def dijkstra(graph: CompiledGeoGraph, source: str, target: str,
             policy: RoutingPolicy) -> RoutePath | None:
    return shortest_path(graph, source, target, policy)


def astar(graph: CompiledGeoGraph, source: str, target: str,
          policy: RoutingPolicy, heuristic: Mapping[str, Decimal | str]) -> RoutePath | None:
    return shortest_path(graph, source, target, policy, heuristic=heuristic)


def yen_top_k(graph: CompiledGeoGraph, source: str, target: str,
              policy: RoutingPolicy, *, k: int = 3,
              max_candidates: int = 25_000) -> tuple[RoutePath, ...]:
    """Up to K distinct loopless directed routes, sorted by total additive cost.

    Not a guarantee of edge-disjointness, geographic diversity, or 3 routes.
    """
    if k < 1 or k > 1000 or max_candidates < 1:
        raise GraphValidationError("invalid K or candidate budget")
    first = dijkstra(graph, source, target, policy)
    if first is None:
        return ()
    accepted = [first]
    candidates: list[tuple[Decimal, tuple[str, ...], tuple[str, ...], RoutePath]] = []
    seen = {first.edge_ids}
    for _ in range(1, k):
        last = accepted[-1]
        for spur_index in range(len(last.node_ids) - 1):
            root_nodes = last.node_ids[:spur_index + 1]
            root_edges = last.edge_ids[:spur_index]
            banned_edges = set()
            for path in accepted:
                if path.edge_ids[:spur_index] == root_edges and len(path.edge_ids) > spur_index:
                    banned_edges.add(path.edge_ids[spur_index])
            spur = shortest_path(
                graph, root_nodes[-1], target, policy,
                excluded_nodes=frozenset(root_nodes[:-1]),
                excluded_edges=frozenset(banned_edges),
            )
            if spur is None:
                continue
            nodes = root_nodes[:-1] + spur.node_ids
            edges = root_edges + spur.edge_ids
            if len(nodes) != len(set(nodes)) or edges in seen:
                continue
            cost = sum((_step_cost(graph, policy, e) for e in edges), Decimal(0))
            route = RoutePath(nodes, edges, cost)
            if len(candidates) >= max_candidates:
                raise SearchLimitExceeded("K-shortest exceeded candidate budget")
            heappush(candidates, (cost, edges, nodes, route))
            seen.add(edges)
        if not candidates:
            break
        accepted.append(heappop(candidates)[-1])
    return tuple(accepted)


def verify_route(graph: CompiledGeoGraph, source: str, target: str,
                 policy: RoutingPolicy, route: RoutePath) -> None:
    """Independent postsolve path, direction, policy and exact cost validation.

    Raises GraphValidationError if a solver returned an invalid path.
    """
    _valid_policy(graph, policy)
    if not route.node_ids or route.node_ids[0] != source or route.node_ids[-1] != target:
        raise GraphValidationError("route endpoints are invalid")
    if len(route.node_ids) != len(route.edge_ids) + 1:
        raise GraphValidationError("route shape is invalid")
    if len(set(route.node_ids)) != len(route.node_ids):
        raise GraphValidationError("route is not loopless")
    if not all(n in graph.nodes and _allowed_node(graph, policy, n) for n in route.node_ids):
        raise GraphValidationError("route contains blocked/unknown nodes")
    total = Decimal(0)
    for i, edge_id in enumerate(route.edge_ids):
        if edge_id not in graph.edges or edge_id in policy.blocked_edges:
            raise GraphValidationError("route contains blocked/unknown edge")
        e = graph.edges[edge_id]
        if e.from_node != route.node_ids[i] or e.to_node != route.node_ids[i + 1]:
            raise GraphValidationError("route violates directed connectivity")
        total += _step_cost(graph, policy, edge_id)
    if total != route.total_cost:
        raise GraphValidationError("route reported total cost is incorrect")
