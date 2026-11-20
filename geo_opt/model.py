"""Immutable, typed contracts for a single-scope, static weighted spatial graph.

All numeric inputs are decimal strings/Decimal; binary floats are rejected.
Hierarchy is a strict rooted tree; routing edges are independent and directed.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional


class GraphValidationError(ValueError):
    """Unusable or inconsistent graph contract."""


class WeightSubject(str, Enum):
    NODE = "NODE"
    EDGE = "EDGE"


class WeightKind(str, Enum):
    COST = "COST"
    DEMAND = "DEMAND"
    CAPACITY = "CAPACITY"
    PRIORITY = "PRIORITY"
    RISK = "RISK"
    REWARD = "REWARD"


class Aggregation(str, Enum):
    SUM = "SUM"
    MIN = "MIN"
    MAX = "MAX"
    NONE = "NONE"


def dec(value: Decimal | str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, str)):
        raise GraphValidationError("numeric values must be Decimal or decimal strings")
    try:
        d = Decimal(value)
    except InvalidOperation as e:
        raise GraphValidationError(f"invalid decimal: {value!r}") from e
    if not d.is_finite():
        raise GraphValidationError("NaN/infinite values are forbidden")
    return d


def required_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise GraphValidationError(f"{name} must be a nonempty normalized identifier")


@dataclass(frozen=True, slots=True)
class GeoNode:
    node_id: str
    node_type: str
    latitude: Decimal | str | None = None
    longitude: Decimal | str | None = None

    def __post_init__(self) -> None:
        required_id("node_id", self.node_id)
        required_id("node_type", self.node_type)
        if (self.latitude is None) != (self.longitude is None):
            raise GraphValidationError("latitude and longitude must both be present or absent")
        if self.latitude is not None:
            lat, lon = dec(self.latitude), dec(self.longitude)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise GraphValidationError("invalid WGS84 coordinates")
            object.__setattr__(self, "latitude", lat)
            object.__setattr__(self, "longitude", lon)


@dataclass(frozen=True, slots=True)
class GeoEdge:
    edge_id: str
    from_node: str
    to_node: str

    def __post_init__(self) -> None:
        for field in ("edge_id", "from_node", "to_node"):
            required_id(field, getattr(self, field))
        if self.from_node == self.to_node:
            raise GraphValidationError("self-loop routing edges are not supported in R0")


@dataclass(frozen=True, slots=True)
class GeoHierarchyRelation:
    parent_id: str
    child_id: str

    def __post_init__(self) -> None:
        required_id("parent_id", self.parent_id)
        required_id("child_id", self.child_id)
        if self.parent_id == self.child_id:
            raise GraphValidationError("hierarchy self-parent is forbidden")


@dataclass(frozen=True, slots=True)
class GeoWeightDefinition:
    code: str
    subject: WeightSubject
    kind: WeightKind
    unit: str
    aggregation: Aggregation = Aggregation.NONE

    def __post_init__(self) -> None:
        required_id("weight code", self.code)
        required_id("unit", self.unit)
        if not isinstance(self.subject, WeightSubject) or not isinstance(self.kind, WeightKind):
            raise GraphValidationError("weight subject/kind must be typed enum")
        if not isinstance(self.aggregation, Aggregation):
            raise GraphValidationError("aggregation must be typed enum")
        if self.kind in (WeightKind.COST, WeightKind.CAPACITY, WeightKind.DEMAND) and self.aggregation == Aggregation.MIN:
            # MIN is mathematically meaningful for some capacities, but a different
            # contract is needed to prevent a mistaken subtree demand aggregation.
            if self.kind == WeightKind.DEMAND:
                raise GraphValidationError("demand with MIN aggregation is unsupported")


@dataclass(frozen=True, slots=True)
class GeoWeightValue:
    code: str
    value: Decimal | str | None

    def __post_init__(self) -> None:
        required_id("weight code", self.code)
        if self.value is not None:
            object.__setattr__(self, "value", dec(self.value))


@dataclass(frozen=True, slots=True)
class GeoWeightProfile:
    subject: WeightSubject
    subject_id: str
    values: tuple[GeoWeightValue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.subject, WeightSubject):
            raise GraphValidationError("weight profile subject must be enum")
        required_id("subject_id", self.subject_id)
        object.__setattr__(self, "values", tuple(self.values))
        if any(not isinstance(v, GeoWeightValue) for v in self.values):
            raise GraphValidationError("invalid weight value type")
        codes = [v.code for v in self.values]
        if len(codes) != len(set(codes)):
            raise GraphValidationError("duplicate weight code in one profile")


@dataclass(frozen=True, slots=True)
class GeoGraphRevision:
    scope_id: str
    graph_id: str
    revision: str
    root_id: str
    nodes: tuple[GeoNode, ...]
    edges: tuple[GeoEdge, ...]
    hierarchy: tuple[GeoHierarchyRelation, ...]
    definitions: tuple[GeoWeightDefinition, ...]
    profiles: tuple[GeoWeightProfile, ...]
    crs: str = "EPSG:4326"

    def __post_init__(self) -> None:
        for k in ("scope_id", "graph_id", "revision", "root_id"):
            required_id(k, getattr(self, k))
        if self.crs != "EPSG:4326":
            raise GraphValidationError("R0 supports EPSG:4326 only")
        for f in ("nodes", "edges", "hierarchy", "definitions", "profiles"):
            object.__setattr__(self, f, tuple(getattr(self, f)))
