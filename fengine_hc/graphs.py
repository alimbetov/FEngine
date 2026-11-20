"""Typed dependency and strategy graph references for FEngine.

Two different layers:
* catalogue candidate graph (116 model nodes, only stated candidate dependencies);
* explicitly bound in-memory calculation job DAG (executable in reference mode).
A candidate edge never becomes an executable input binding automatically.
"""
from __future__ import annotations

import csv
import heapq
import re
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .reference import CalculationError, CalculationResult, ContractRegistry, ReferenceEngine, number, fingerprint, _freeze


def _sort_dag(nodes: set[str], arcs: set[tuple[str, str]]) -> tuple[str, ...]:
    """Arcs point from prerequisite to dependent."""
    children = {k: set() for k in nodes}
    degree = {k: 0 for k in nodes}
    for source, target in arcs:
        if source not in nodes or target not in nodes:
            raise CalculationError("UNKNOWN_DAG_NODE")
        if source == target:
            raise CalculationError("DAG_CYCLE")
        if target not in children[source]:
            children[source].add(target)
            degree[target] += 1
    ready = [k for k, n in degree.items() if n == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        n = heapq.heappop(ready)
        order.append(n)
        for child in sorted(children[n]):
            degree[child] -= 1
            if degree[child] == 0:
                heapq.heappush(ready, child)
    if len(order) != len(nodes):
        raise CalculationError("DAG_CYCLE")
    return tuple(order)


@dataclass(frozen=True)
class CandidateEdge:
    source_model: str
    target_model: str
    qualification: str = "CANDIDATE_NO_TYPED_RESULT_BINDING"


class CandidateModelGraph:
    def __init__(self, root: Path):
        models = set(ContractRegistry(root).models)
        edges: set[tuple[str, str]] = set()
        for filename in ("model_extensions_r1.tsv", "model_extensions_r2.tsv"):
            with (root / "catalog" / filename).open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader((line for line in f
                                           if line.strip() and not line.lstrip().startswith("#")), delimiter="\t"))
            for row in rows:
                target = row["modelCode"]
                if target not in models:
                    raise CalculationError("UNKNOWN_DAG_NODE")
                # A registry may abbreviate HC.LOAN.01/02/03; expand exact numeric suffixes.
                for token in re.split(r"[|;]", row["upstreamCandidateRefs"]):
                    match = re.fullmatch(r"(HC\.[A-Z]+\.)((?:\d{2})(?:/\d{2})*)", token.strip())
                    if not match:
                        if token.strip().startswith("HC."):
                            raise CalculationError("INVALID_CANDIDATE_REFERENCE", token)
                        continue
                    for n in match.group(2).split("/"):
                        dep = match.group(1) + n
                        if dep not in models:
                            raise CalculationError("UNKNOWN_DAG_NODE", dep)
                        edges.add((dep, target))
        self.models = frozenset(models)
        self.edges = frozenset(CandidateEdge(s, t) for s, t in edges)
        self.order = _sort_dag(models, edges)


@dataclass(frozen=True)
class TypedPort:
    model_code: str
    field: str
    value_kind: str
    unit_semantics: str


# Allowed cross-model field bindings are separately reviewed for the bounded
# Python reference. Existence of a catalog dependency never implies this edge.
REFERENCE_PORTS: dict[tuple[str, str], TypedPort] = {
    ("HC.CAP.01", "costOfEquity"): TypedPort("HC.CAP.01", "costOfEquity", "DECIMAL_RATE", "PER_ANNUAL"),
    ("HC.CAP.02", "costOfEquity"): TypedPort("HC.CAP.02", "costOfEquity", "DECIMAL_RATE", "PER_ANNUAL"),
}
REFERENCE_EDGE_ALLOWLIST = frozenset({
    ("HC.CAP.01", "costOfEquity", "HC.CAP.02", "costOfEquity"),
})


def _validate_typed_reference_edge(source: "CalculationJob", target: "CalculationJob",
                                    binding: "InputBinding") -> None:
    key = (source.model_code, binding.source_field, target.model_code, binding.target_field)
    if key not in REFERENCE_EDGE_ALLOWLIST:
        raise CalculationError("MODEL_BINDING_NOT_REVIEWED", ".".join(key))
    src = REFERENCE_PORTS.get((source.model_code, binding.source_field))
    dst = REFERENCE_PORTS.get((target.model_code, binding.target_field))
    if src is None or dst is None or src.value_kind != dst.value_kind or src.unit_semantics != dst.unit_semantics:
        raise CalculationError("MODEL_PORT_TYPE_MISMATCH")


@dataclass(frozen=True)
class InputBinding:
    source_job: str
    source_field: str
    target_field: str
    # Validated when the target input contract is reviewed. This reference
    # compiler cannot claim that semantic/financial qualification has occurred.


@dataclass(frozen=True)
class CalculationJob:
    job_id: str
    model_code: str
    variant_code: str
    inputs: Mapping[str, Any]
    config: Mapping[str, Any]
    bindings: tuple[InputBinding, ...] = ()


class InMemoryCalculationPlan:
    def __init__(self, engine: ReferenceEngine, jobs: Sequence[CalculationJob]):
        self.engine = engine
        self.jobs = {j.job_id: replace(j, inputs=_freeze(j.inputs), config=_freeze(j.config))
                     for j in jobs}
        if not jobs or len(jobs) != len(self.jobs):
            raise CalculationError("INVALID_OR_DUPLICATE_JOB_ID")
        arcs = set()
        for j in jobs:
            if not isinstance(j.job_id, str) or not j.job_id:
                raise CalculationError("INVALID_JOB_ID")
            if (j.model_code, j.variant_code) not in engine.registry.variants:
                raise CalculationError("UNKNOWN_VARIANT")
            seen = set()
            for b in j.bindings:
                if not b.source_field or not b.target_field or b.target_field in seen:
                    raise CalculationError("INVALID_OUTPUT_BINDING")
                if b.target_field in j.inputs:
                    raise CalculationError("INPUT_BINDING_OVERRIDE")
                seen.add(b.target_field)
                arcs.add((b.source_job, j.job_id))
        self.order = _sort_dag(set(self.jobs), arcs)
        # After structural cycle detection, refuse any unreviewed cross-model
        # binding even if fields share the same textual name or numeric type.
        for job in self.jobs.values():
            for binding in job.bindings:
                _validate_typed_reference_edge(self.jobs[binding.source_job], job, binding)
        self.plan_sha256 = fingerprint({
            "referencePlanContract": "HC_R02C_PORTS_V1",
            "jobs": [{
                "jobId": job_id, "model": self.jobs[job_id].model_code,
                "variant": self.jobs[job_id].variant_code,
                "inputs": self.jobs[job_id].inputs,
                "config": self.jobs[job_id].config,
                "bindings": [
                    {"source": b.source_job, "sourceField": b.source_field,
                     "targetField": b.target_field}
                    for b in self.jobs[job_id].bindings
                ],
            } for job_id in sorted(self.jobs)]
        })

    def execute(self, *, reference_mode: bool = False) -> Mapping[str, CalculationResult]:
        if not reference_mode:
            raise CalculationError("FINANCIAL_S2_REQUIRED")
        results: dict[str, CalculationResult] = {}
        for job_id in self.order:
            j = self.jobs[job_id]
            inputs = dict(j.inputs)
            for b in j.bindings:
                upstream = results[b.source_job].output
                if b.source_field not in upstream:
                    raise CalculationError("MISSING_BOUND_OUTPUT", b.source_field)
                value = upstream[b.source_field]
                # Contract explicitly expects canonical numeric decimal strings.
                # Never silently coerce a list, object, float or unknown unit.
                if not isinstance(value, str):
                    raise CalculationError("MODEL_PORT_TYPE_MISMATCH")
                number(value)
                inputs[b.target_field] = value
            results[job_id] = self.engine.calculate(
                j.model_code, j.variant_code, inputs, j.config, reference_mode=True
            )
        return MappingProxyType(results)


@dataclass(frozen=True)
class StrategyState:
    code: str
    active_families: frozenset[str]
    kind: str  # ENTRY, DECISION, ACTION, TERMINAL


@dataclass(frozen=True)
class StrategyTransition:
    source: str
    target: str
    model_code: str
    output_field: str
    comparator: str
    threshold: str


class StrategyGraph:
    """Validated decision graph; no automatic financial or investment advice."""
    def __init__(self, registry: ContractRegistry, states: Sequence[StrategyState],
                 transitions: Sequence[StrategyTransition]):
        self.states = {s.code: s for s in states}
        if not states or len(self.states) != len(states):
            raise CalculationError("DUPLICATE_STRATEGY_STATE")
        families = {p["family"] for p in registry.models.values()}
        for s in states:
            if s.kind not in ("ENTRY", "DECISION", "ACTION", "TERMINAL"):
                raise CalculationError("UNKNOWN_STATE_KIND")
            if not s.active_families <= families:
                raise CalculationError("UNKNOWN_STRATEGY_FAMILY")
        self.transitions = tuple(transitions)
        for t in transitions:
            if t.model_code not in registry.models:
                raise CalculationError("UNKNOWN_MODEL")
            if t.comparator not in ("LT", "LE", "EQ", "GE", "GT"):
                raise CalculationError("INVALID_COMPARATOR")
            if not t.output_field:
                raise CalculationError("MISSING_STRATEGY_OUTPUT")
            number(t.threshold)
        self.order = _sort_dag(set(self.states), {(x.source, x.target) for x in transitions})

    @staticmethod
    def condition(t: StrategyTransition, value: Any) -> bool:
        a, b = number(value), number(t.threshold)
        return {
            "LT": lambda: a < b,
            "LE": lambda: a <= b,
            "EQ": lambda: a == b,
            "GE": lambda: a >= b,
            "GT": lambda: a > b,
        }[t.comparator]()
