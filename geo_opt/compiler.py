"""Deterministic bounded graph compiler with independent hierarchy/route topology."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from json import dumps
from types import MappingProxyType
from typing import Mapping

from .model import (
    Aggregation, GeoGraphRevision, GeoNode, GeoEdge, GeoWeightDefinition,
    GeoWeightProfile, GeoHierarchyRelation, GraphValidationError,
    WeightKind, WeightSubject,
)


def _unique(items, key, label):
    result = {}
    for item in items:
        k = key(item)
        if k in result:
            raise GraphValidationError(f"duplicate {label}: {k}")
        result[k] = item
    return result


def _canonical_digest(obj) -> str:
    return sha256(dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CompiledGeoGraph:
    scope_id: str
    graph_id: str
    revision: str
    root_id: str
    nodes: Mapping[str, GeoNode]
    edges: Mapping[str, GeoEdge]
    children: Mapping[str, tuple[str, ...]]
    parents: Mapping[str, str | None]
    depth: Mapping[str, int]
    outgoing: Mapping[str, tuple[str, ...]]
    definitions: Mapping[tuple[WeightSubject, str], GeoWeightDefinition]
    weights: Mapping[tuple[WeightSubject, str, str], Decimal | None]
    fingerprint: str

    def weight(self, subject: WeightSubject, subject_id: str, code: str) -> Decimal:
        key = (subject, subject_id, code)
        if key not in self.weights or self.weights[key] is None:
            raise GraphValidationError(f"missing required weight: {key}")
        return self.weights[key]  # type: ignore[return-value]

    def subtree_aggregate(self, root_id: str, code: str) -> Decimal:
        definition = self.definitions.get((WeightSubject.NODE, code))
        if definition is None or definition.aggregation != Aggregation.SUM:
            raise GraphValidationError("subtree aggregation requires node SUM definition")
        if root_id not in self.nodes:
            raise GraphValidationError("unknown subtree root")
        total = Decimal(0)
        stack = [root_id]
        while stack:
            v = stack.pop()
            total += self.weight(WeightSubject.NODE, v, code)
            stack.extend(self.children[v])
        return total


def compile_graph(spec: GeoGraphRevision, *, max_depth: int = 60,
                  max_nodes: int = 100_000, max_edges: int = 500_000) -> CompiledGeoGraph:
    if not isinstance(spec, GeoGraphRevision):
        raise GraphValidationError("expected GeoGraphRevision")
    if max_depth < 0 or max_nodes < 1 or max_edges < 0:
        raise GraphValidationError("invalid resource bounds")
    if len(spec.nodes) > max_nodes or len(spec.edges) > max_edges:
        raise GraphValidationError("graph exceeds configured size limits")
    if any(not isinstance(x, GeoNode) for x in spec.nodes):
        raise GraphValidationError("node contracts are not GeoNode")
    if any(not isinstance(x, GeoEdge) for x in spec.edges):
        raise GraphValidationError("edge contracts are not GeoEdge")
    if any(not isinstance(x, GeoHierarchyRelation) for x in spec.hierarchy):
        raise GraphValidationError("hierarchy contracts are not GeoHierarchyRelation")
    if any(not isinstance(x, GeoWeightDefinition) for x in spec.definitions):
        raise GraphValidationError("weight definition contracts invalid")
    if any(not isinstance(x, GeoWeightProfile) for x in spec.profiles):
        raise GraphValidationError("weight profile contracts invalid")
    nodes = _unique(spec.nodes, lambda x: x.node_id, "node ID")
    edges = _unique(spec.edges, lambda x: x.edge_id, "edge ID")
    if spec.root_id not in nodes:
        raise GraphValidationError("root ID does not exist")
    children: dict[str, list[str]] = {k: [] for k in nodes}
    parents: dict[str, str | None] = {k: None for k in nodes}
    relation_pairs = set()
    for rel in spec.hierarchy:
        if rel.parent_id not in nodes or rel.child_id not in nodes:
            raise GraphValidationError("unknown hierarchy endpoint")
        pair = (rel.parent_id, rel.child_id)
        if pair in relation_pairs:
            raise GraphValidationError("duplicate hierarchy relation")
        relation_pairs.add(pair)
        if parents[rel.child_id] is not None:
            raise GraphValidationError("multiple hierarchy parents not supported in R0")
        parents[rel.child_id] = rel.parent_id
        children[rel.parent_id].append(rel.child_id)
    if parents[spec.root_id] is not None:
        raise GraphValidationError("root must not have a parent (cycle)")
    if any(parents[node_id] is None for node_id in nodes if node_id != spec.root_id):
        raise GraphValidationError("disconnected hierarchy / missing parent")
    depth = {spec.root_id: 0}
    stack = [spec.root_id]
    while stack:
        u = stack.pop()
        for v in children[u]:
            if v in depth:
                raise GraphValidationError("hierarchy cycle detected")
            d = depth[u] + 1
            if d > max_depth:
                raise GraphValidationError("hierarchy exceeds maximum depth")
            depth[v] = d
            stack.append(v)
    if len(depth) != len(nodes):
        raise GraphValidationError("hierarchy cycle or disconnected hierarchy")
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in edges.values():
        if edge.from_node not in nodes or edge.to_node not in nodes:
            raise GraphValidationError("routing edge refers to unknown endpoint")
        outgoing[edge.from_node].append(edge.edge_id)
    definitions = _unique(spec.definitions, lambda x: (x.subject, x.code), "weight definition")
    profiles = _unique(spec.profiles, lambda x: (x.subject, x.subject_id), "weight profile")
    weights = {}
    for (subject, entity_id), profile in profiles.items():
        if entity_id not in (nodes if subject == WeightSubject.NODE else edges):
            raise GraphValidationError("weight profile references unknown subject")
        for v in profile.values:
            key = (subject, v.code)
            if key not in definitions:
                raise GraphValidationError(f"undefined weight {key}")
            definition = definitions[key]
            if v.value is not None and definition.kind in (WeightKind.COST, WeightKind.CAPACITY, WeightKind.DEMAND) and v.value < 0:
                raise GraphValidationError("negative cost/capacity/demand unsupported in R0")
            weights[(subject, entity_id, v.code)] = v.value
    # Immutable canonical manifest: order of inputs does not change revision digest.
    manifest = {
        "schema": "GEO-R0.1", "scope": spec.scope_id, "graph": spec.graph_id, "revision": spec.revision,
        "root": spec.root_id, "crs": spec.crs,
        "nodes": sorted([(x.node_id, x.node_type, str(x.latitude) if x.latitude is not None else None,
                          str(x.longitude) if x.longitude is not None else None) for x in nodes.values()]),
        "edges": sorted([(x.edge_id, x.from_node, x.to_node) for x in edges.values()]),
        "relations": sorted(relation_pairs),
        "definitions": sorted([(x.subject.value, x.code, x.kind.value, x.unit, x.aggregation.value)
                               for x in definitions.values()]),
        "weights": sorted([(k[0].value, k[1], k[2], str(v) if v is not None else None)
                           for k, v in weights.items()]),
    }
    return CompiledGeoGraph(
        spec.scope_id, spec.graph_id, spec.revision, spec.root_id,
        MappingProxyType(nodes), MappingProxyType(edges),
        MappingProxyType({k: tuple(sorted(v)) for k, v in children.items()}),
        MappingProxyType(parents), MappingProxyType(depth),
        MappingProxyType({k: tuple(sorted(v)) for k, v in outgoing.items()}),
        MappingProxyType(definitions), MappingProxyType(weights), _canonical_digest(manifest),
    )
