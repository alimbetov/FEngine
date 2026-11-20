"""Typed, fail-closed temporal aggregation reference for FEngine TASE R0.

This is an in-process deterministic reference: no DB, durable jobs, Product Pack
signature verification or financial S2. Draft TSV catalogues may only be loaded
with reference_mode=True. Only explicitly listed SUPPORTED_OPERATORS execute.
All money-like values are Python Decimal (never silently cast from float).
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Iterable


class TaseError(ValueError):
    """A stable, scoped blocker code; do not turn missing data into zero."""
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def _fingerprint(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, str):
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise TaseError("INVALID_DECIMAL") from exc
    else:
        raise TaseError("DECIMAL_STRING_REQUIRED", "binary float and implicit number coercion are forbidden")
    if not result.is_finite():
        raise TaseError("NONFINITE_VALUE")
    return result


def _text(value: Decimal) -> str:
    return format(value, "f")


def _parse_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise TaseError("CATALOG_MISSING", str(path))
    with path.open(encoding="utf-8", newline="") as src:
        result = list(csv.DictReader(src, delimiter="\t"))
    if not result or any(None in row for row in result):
        raise TaseError("CATALOG_INVALID", str(path))
    return result


def _codes(value: str) -> frozenset[str]:
    return frozenset(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class ProductPack:
    code: str
    revision: str
    grains: frozenset[str]
    operators: frozenset[str]
    status: str


@dataclass(frozen=True)
class Metric:
    product: str
    code: str
    logical_type: str
    unit: str
    kind: str
    time_kind: str
    time_aggregate: str
    operators: frozenset[str]
    numerator: str
    denominator_or_weight: str
    status: str


@dataclass(frozen=True)
class Predicate:
    code: str
    quantity_kinds: frozenset[str]
    logical_types: frozenset[str]
    time_kinds: frozenset[str]


@dataclass(frozen=True)
class Operator:
    code: str
    predicates: frozenset[str]
    status: str


# Explicit implementation allowlist. Other 53 catalogued operator candidates
# must fail OPERATOR_NOT_IMPLEMENTED rather than silently fall back.
SUPPORTED_OPERATORS = frozenset({
    "SUM", "LAST_AS_OF", "ARITH_MEAN", "WEIGHTED_MEAN", "VAR_POP",
    "VAR_SAMPLE", "STDDEV_POP", "STDDEV_SAMPLE", "RMS",
    "MIN", "MAX", "RATIO_OF_SUMS", "QUANTILE_EXACT",
})


class Catalog:
    """Read-only, versioned candidate registry. No dynamic code execution."""
    def __init__(self, products: dict[str, ProductPack],
                 metrics: dict[tuple[str, str], Metric],
                 operators: dict[str, Operator],
                 predicates: dict[str, Predicate], *, reference_mode: bool) -> None:
        self.products = products
        self.metrics = metrics
        self.operators = operators
        self.predicates = predicates
        self.reference_mode = reference_mode

    @classmethod
    def load(cls, root: Path | None = None, *, reference_mode: bool = False) -> "Catalog":
        base = (root or Path(__file__).resolve().parents[1]) / "catalog"
        packs: dict[str, ProductPack] = {}
        for row in _parse_tsv(base / "tase_product_pack_candidates_r0.tsv"):
            code = row["productCode"]
            if code in packs:
                raise TaseError("DUPLICATE_PRODUCT", code)
            packs[code] = ProductPack(code, row["productPackRevision"],
                                      _codes(row["allowedGrains"]),
                                      _codes(row["candidateOperators"]), row["status"])
        metrics: dict[tuple[str, str], Metric] = {}
        for row in _parse_tsv(base / "tase_metric_semantics_candidates_r0.tsv"):
            key = (row["productCode"], row["metricCode"])
            if key in metrics:
                raise TaseError("DUPLICATE_METRIC", str(key))
            metrics[key] = Metric(row["productCode"], row["metricCode"],
                                  row["logicalType"], row["unitCode"],
                                  row["quantityKind"], row["timeKind"],
                                  row["aggregationAcrossTime"],
                                  _codes(row["allowedOperatorIds"]),
                                  row["numeratorRef"], row["denominatorOrWeightRef"],
                                  row["status"])
        predicates: dict[str, Predicate] = {}
        for row in _parse_tsv(base / "tase_input_predicates_r0.tsv"):
            code = row["predicateCode"]
            if code in predicates:
                raise TaseError("DUPLICATE_PREDICATE", code)
            predicates[code] = Predicate(code, _codes(row["allowedQuantityKinds"]),
                                         _codes(row["allowedLogicalTypes"]),
                                         _codes(row["allowedTimeKinds"]))
        ops: dict[str, Operator] = {}
        for row in _parse_tsv(base / "tase_operator_candidates_r0.tsv"):
            code = row["operatorCode"]
            if code in ops:
                raise TaseError("DUPLICATE_OPERATOR", code)
            ops[code] = Operator(code, _codes(row["inputTypePredicates"]), row["status"])
        for p in packs.values():
            if p.operators - ops.keys():
                raise TaseError("PRODUCT_UNKNOWN_OPERATOR", p.code)
        for m in metrics.values():
            p = packs.get(m.product)
            if p is None:
                raise TaseError("METRIC_PRODUCT_MISSING", m.code)
            if not m.operators <= p.operators:
                raise TaseError("PRODUCT_METRIC_OPERATOR_MISMATCH", m.code)
            for ref in (m.numerator, m.denominator_or_weight):
                if ref and (m.product, ref) not in metrics:
                    raise TaseError("METRIC_COMPONENT_MISSING", m.code + ":" + ref)
        for op in ops.values():
            if op.predicates - predicates.keys():
                raise TaseError("OPERATOR_UNKNOWN_PREDICATE", op.code)
        # Validate EVERY declarative metric/operator edge when loading a pack,
        # not only the operators that happen to be implemented in this worker.
        for m in metrics.values():
            for op_code in m.operators:
                op = ops[op_code]
                matched = any(
                    m.kind in predicates[pred].quantity_kinds
                    and m.logical_type in predicates[pred].logical_types
                    and m.time_kind in predicates[pred].time_kinds
                    for pred in op.predicates
                )
                if not matched:
                    raise TaseError("METRIC_OPERATOR_TYPE_MISMATCH",
                                    m.product + ":" + m.code + ":" + op_code)
        # There is no approved/signed Product Pack in the current repository.
        if not reference_mode:
            raise TaseError("UNAPPROVED_PRODUCT_PACK",
                            "current packs are DRAFT; pass reference_mode=True for UAT only")
        return cls(packs, metrics, ops, predicates, reference_mode=True)

    def resolve(self, product: str, metric_code: str, operation: str, grain: str) -> Metric:
        pack = self.products.get(product)
        metric = self.metrics.get((product, metric_code))
        op = self.operators.get(operation)
        if pack is None:
            raise TaseError("UNKNOWN_PRODUCT", product)
        if metric is None:
            raise TaseError("UNKNOWN_METRIC", product + ":" + metric_code)
        if grain not in pack.grains:
            raise TaseError("GRAIN_NOT_ALLOWED", grain)
        if op is None or operation not in pack.operators or operation not in metric.operators:
            raise TaseError("OPERATOR_NOT_ALLOWED", operation)
        if operation not in SUPPORTED_OPERATORS:
            raise TaseError("OPERATOR_NOT_IMPLEMENTED", operation)
        allowed = any(metric.kind in self.predicates[p].quantity_kinds
                      and metric.logical_type in self.predicates[p].logical_types
                      and metric.time_kind in self.predicates[p].time_kinds
                      for p in op.predicates)
        if not allowed:
            raise TaseError("OPERATOR_TYPE_MISMATCH", metric_code + ":" + operation)
        if operation == "SUM" and metric.time_aggregate != "SUM":
            raise TaseError("NON_ADDITIVE_METRIC")
        if operation == "LAST_AS_OF" and metric.kind != "STOCK":
            raise TaseError("NOT_A_STOCK")
        if operation == "RATIO_OF_SUMS" and (not metric.numerator or not metric.denominator_or_weight):
            raise TaseError("COMPONENT_SOURCE_MISSING")
        if operation == "WEIGHTED_MEAN" and not metric.denominator_or_weight:
            raise TaseError("WEIGHT_METRIC_MISSING")
        return metric


@dataclass(frozen=True)
class Observation:
    product: str
    metric: str
    scope: str
    start: date
    value: Decimal | str | None
    unit: str
    source_sha: str
    end: date | None = None
    dimensions: tuple[tuple[str, str], ...] = ()
    observation_id: str = ""
    state: str = "PRESENT"

    def __post_init__(self) -> None:
        if not isinstance(self.start, date) or (self.end is not None and not isinstance(self.end, date)):
            raise TaseError("INVALID_DATE")
        if self.end is not None and self.end <= self.start:
            raise TaseError("INVALID_INTERVAL")
        if len(set(k for k, _ in self.dimensions)) != len(self.dimensions):
            raise TaseError("DUPLICATE_DIMENSION")
        if self.dimensions != tuple(sorted(self.dimensions)):
            raise TaseError("DIMENSIONS_NOT_CANONICAL")
        if not self.source_sha or not self.scope or not self.product or not self.metric:
            raise TaseError("SOURCE_IDENTITY_REQUIRED")
        if self.state == "PRESENT":
            object.__setattr__(self, "value", _decimal(self.value))
        elif self.state not in {"MISSING", "EXPLICIT_NULL", "INVALID", "NOT_APPLICABLE"}:
            raise TaseError("UNKNOWN_VALUE_STATE", self.state)
        elif self.value is not None:
            raise TaseError("VALUE_STATE_CONFLICT")


@dataclass(frozen=True)
class Dataset:
    scope: str
    content_sha: str
    rows: tuple[Observation, ...]
    complete_event_stream: bool = False
    watermark: date | None = None

    def __post_init__(self) -> None:
        if not self.scope or not self.content_sha:
            raise TaseError("DATASET_IDENTITY_REQUIRED")
        if any(r.scope != self.scope for r in self.rows):
            raise TaseError("CROSS_SCOPE_DATASET")
        keys = [(r.product, r.metric, r.dimensions, r.start, r.end, r.observation_id)
                for r in self.rows]
        if len(set(keys)) != len(keys):
            raise TaseError("DUPLICATE_OBSERVATION")


@dataclass(frozen=True)
class PeriodRequest:
    product: str
    metric: str
    operation: str
    scope: str
    start: date
    end: date
    grain: str
    group_by: tuple[str, ...] = ()
    fiscal_start_month: int = 1
    require_full_coverage: bool = True
    max_snapshot_age_days: int | None = None
    quantile_alpha: Decimal | str | None = None

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise TaseError("INVALID_REQUEST_INTERVAL")
        if not 1 <= self.fiscal_start_month <= 12:
            raise TaseError("INVALID_FISCAL_START")
        if len(set(self.group_by)) != len(self.group_by):
            raise TaseError("DUPLICATE_GROUP_KEY")
        if self.max_snapshot_age_days is not None and self.max_snapshot_age_days < 0:
            raise TaseError("INVALID_STALENESS")
        if self.quantile_alpha is not None:
            alpha = _decimal(self.quantile_alpha)
            if not Decimal(0) < alpha < Decimal(1):
                raise TaseError("INVALID_QUANTILE")
            object.__setattr__(self, "quantile_alpha", alpha)


@dataclass(frozen=True)
class TasePlan:
    request: PeriodRequest
    pack_revision: str
    semantic_code: str
    operator_code: str
    plan_sha: str


@dataclass(frozen=True)
class ResultRow:
    group: tuple[tuple[str, str], ...]
    start: date
    end: date
    value: str
    unit: str
    observation_count: int
    coverage: str = "FULL"
    status: str = "COMPLETE"


@dataclass(frozen=True)
class TaseResult:
    plan_sha: str
    dataset_sha: str
    rows: tuple[ResultRow, ...]
    result_sha: str
    status: str = "COMPLETE"
    execution_class: str = "PYTHON_REFERENCE_NOT_S2"


def _month_add(d: date, months: int) -> date:
    i = d.year * 12 + d.month - 1 + months
    return date(i // 12, i % 12 + 1, 1)


def _start_of_bucket(day: date, grain: str, fiscal_start_month: int) -> date:
    if grain in {"MONTH", "FISCAL_PERIOD"}:
        return date(day.year, day.month, 1)
    if grain == "DAY":
        return day
    if grain == "ISO_WEEK":
        return day - timedelta(days=day.weekday())
    if grain in {"YEAR", "FISCAL_YEAR"}:
        first = 1 if grain == "YEAR" else fiscal_start_month
        return date(day.year if day.month >= first else day.year - 1, first, 1)
    if grain in {"QUARTER", "HALF_YEAR", "FISCAL_QUARTER", "FISCAL_HALF_YEAR"}:
        first = fiscal_start_month if grain.startswith("FISCAL_") else 1
        length = 6 if "HALF" in grain else 3
        offset = (day.month - first) % 12
        idx = day.year * 12 + day.month - 1 - (offset % length)
        return date(idx // 12, idx % 12 + 1, 1)
    raise TaseError("CALENDAR_GRAIN_NOT_IMPLEMENTED", grain)


def _next_bucket(day: date, grain: str) -> date:
    if grain == "DAY":
        return day + timedelta(days=1)
    if grain == "ISO_WEEK":
        return day + timedelta(days=7)
    if grain in {"MONTH", "FISCAL_PERIOD"}:
        return _month_add(day, 1)
    if grain in {"QUARTER", "FISCAL_QUARTER"}:
        return _month_add(day, 3)
    if grain in {"HALF_YEAR", "FISCAL_HALF_YEAR"}:
        return _month_add(day, 6)
    if grain in {"YEAR", "FISCAL_YEAR"}:
        return _month_add(day, 12)
    raise TaseError("CALENDAR_GRAIN_NOT_IMPLEMENTED", grain)


def _buckets(req: PeriodRequest) -> tuple[tuple[date, date], ...]:
    first = _start_of_bucket(req.start, req.grain, req.fiscal_start_month)
    if first != req.start:
        raise TaseError("PARTIAL_BUCKET_UNSUPPORTED", "start must align with calendar grain")
    result = []
    cursor = first
    while cursor < req.end:
        nxt = _next_bucket(cursor, req.grain)
        if nxt > req.end:
            raise TaseError("PARTIAL_BUCKET_UNSUPPORTED", "end must align with calendar grain")
        result.append((cursor, nxt))
        cursor = nxt
        if len(result) > 10000:
            raise TaseError("RESOURCE_BUDGET_EXCEEDED")
    return tuple(result)


def compile_plan(catalog: Catalog, req: PeriodRequest) -> TasePlan:
    metric = catalog.resolve(req.product, req.metric, req.operation, req.grain)
    _buckets(req)
    if req.operation == "QUANTILE_EXACT" and req.quantile_alpha is None:
        raise TaseError("QUANTILE_ALPHA_REQUIRED")
    manifest = {
        "revision": "TASE.REFERENCE.R0.1", "product": req.product,
        "metric": req.metric, "operator": req.operation, "scope": req.scope,
        "period": [req.start.isoformat(), req.end.isoformat(), req.grain, req.fiscal_start_month],
        "groups": req.group_by, "coverage": req.require_full_coverage,
        "staleness": req.max_snapshot_age_days,
        "alpha": _text(req.quantile_alpha) if req.quantile_alpha is not None else None,
        "productRevision": catalog.products[req.product].revision,
        "semantic": [metric.kind, metric.time_kind, metric.logical_type, metric.unit,
                     metric.time_aggregate, sorted(metric.operators)],
    }
    return TasePlan(req, catalog.products[req.product].revision,
                    req.product + ":" + req.metric, req.operation,
                    _fingerprint(manifest))


def _group(row: Observation, keys: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    dims = dict(row.dimensions)
    if any(key not in dims for key in keys):
        raise TaseError("GROUP_DIMENSION_MISSING")
    return tuple((k, dims[k]) for k in keys)


def _check_rows(rows: list[Observation], metric: Metric, begin: date, end: date,
                dataset: Dataset, require_full: bool, *, stock: bool = False) -> None:
    for row in rows:
        if row.state != "PRESENT":
            raise TaseError("MISSING_OBSERVATION", row.state)
        if row.unit != metric.unit:
            raise TaseError("UNIT_OR_CURRENCY_MISMATCH")
        if stock:
            if row.end is not None:
                raise TaseError("STOCK_MUST_BE_AS_OF")
        elif metric.time_kind in {"INTERVAL_FLOW", "COVERAGE_INTERVAL"}:
            if row.end is None or row.start < begin or row.end > end:
                raise TaseError("SOURCE_GRANULARITY_MISMATCH")
        elif metric.time_kind == "EVENT_AT":
            if row.end is not None:
                raise TaseError("EVENT_MUST_BE_INSTANT")
        elif metric.time_kind in {"AS_OF", "RATE_FIXING"}:
            if row.end is not None:
                raise TaseError("AS_OF_MUST_BE_INSTANT")
    if not require_full or stock:
        return
    if metric.time_kind == "EVENT_AT":
        if not dataset.complete_event_stream or dataset.watermark is None or dataset.watermark < end:
            raise TaseError("COVERAGE_UNKNOWN")
        return
    if metric.time_kind not in {"INTERVAL_FLOW", "COVERAGE_INTERVAL"}:
        return
    # Completeness/overlap is checked PER leaf identity, never across branches,
    # which can legitimately have overlapping dates for separate measurements.
    per_leaf: dict[tuple[tuple[str, str], ...], list[Observation]] = {}
    for row in rows:
        per_leaf.setdefault(row.dimensions, []).append(row)
    if not per_leaf:
        raise TaseError("MISSING_PERIOD_SOURCE")
    for leaf in per_leaf.values():
        cursor = begin
        for row in sorted(leaf, key=lambda r: (r.start, r.end or r.start)):
            if row.start < cursor:
                raise TaseError("SOURCE_OVERLAP")
            if row.start > cursor:
                raise TaseError("PARTIAL_COVERAGE")
            cursor = row.end  # type: ignore[assignment]
        if cursor != end:
            raise TaseError("PARTIAL_COVERAGE")


def _statistic(operation: str, values: list[Decimal], alpha: Decimal | None) -> Decimal:
    if not values:
        raise TaseError("EMPTY_INPUT")
    n = len(values)
    with localcontext() as ctx:
        ctx.prec = 50
        total = sum(values, Decimal(0))
        if operation == "SUM":
            return total
        if operation == "ARITH_MEAN":
            return total / n
        if operation == "MIN":
            return min(values)
        if operation == "MAX":
            return max(values)
        if operation in {"VAR_POP", "VAR_SAMPLE", "STDDEV_POP", "STDDEV_SAMPLE"}:
            sample = operation.endswith("_SAMPLE")
            if sample and n < 2:
                raise TaseError("N_LT_2")
            mean = total / n
            var = sum(((x - mean) ** 2 for x in values), Decimal(0)) / (n - 1 if sample else n)
            return var.sqrt() if operation.startswith("STDDEV_") else var
        if operation == "RMS":
            return (sum((x*x for x in values), Decimal(0)) / n).sqrt()
        if operation == "QUANTILE_EXACT":
            if alpha is None:
                raise TaseError("QUANTILE_ALPHA_REQUIRED")
            idx = int((alpha * n).to_integral_value(rounding="ROUND_CEILING")) - 1
            return sorted(values)[idx]
    raise TaseError("OPERATOR_NOT_IMPLEMENTED", operation)


def _selected(rows: tuple[Observation, ...], metric: str, group: tuple[tuple[str, str], ...],
              keys: tuple[str, ...], begin: date, end: date) -> list[Observation]:
    return [r for r in rows if r.metric == metric and _group(r, keys) == group
            and begin <= r.start < end]


def calculate(catalog: Catalog, req: PeriodRequest, dataset: Dataset) -> TaseResult:
    """Execute only a bounded in-memory reference, NOT a durable Hub job."""
    plan = compile_plan(catalog, req)
    if req.scope != dataset.scope:
        raise TaseError("CROSS_SCOPE_DATASET")
    if any(r.product != req.product for r in dataset.rows):
        raise TaseError("CROSS_PRODUCT_DATASET")
    metric = catalog.metrics[(req.product, req.metric)]
    all_rows = [r for r in dataset.rows if r.metric == req.metric or r.metric
                in {metric.numerator, metric.denominator_or_weight}]
    for row in all_rows:
        if row.metric not in {req.metric, metric.numerator, metric.denominator_or_weight}:
            raise TaseError("UNREGISTERED_SOURCE_METRIC")
    group_keys = req.group_by
    groups = sorted(set(_group(r, group_keys) for r in all_rows))
    if not groups:
        raise TaseError("MISSING_PERIOD_SOURCE")
    if len(groups) * len(_buckets(req)) > 100000:
        raise TaseError("RESOURCE_BUDGET_EXCEEDED")
    results: list[ResultRow] = []
    for begin, end in _buckets(req):
        for group in groups:
            selected = _selected(dataset.rows, req.metric, group, group_keys, begin, end)
            if req.operation == "RATIO_OF_SUMS":
                num = catalog.metrics[(req.product, metric.numerator)]
                den = catalog.metrics[(req.product, metric.denominator_or_weight)]
                numerator = _selected(dataset.rows, num.code, group, group_keys, begin, end)
                denominator = _selected(dataset.rows, den.code, group, group_keys, begin, end)
                _check_rows(numerator, num, begin, end, dataset, req.require_full_coverage)
                _check_rows(denominator, den, begin, end, dataset, req.require_full_coverage)
                if not numerator or not denominator:
                    raise TaseError("COMPONENT_SOURCE_MISSING")
                units = {num.unit, den.unit}
                if num.logical_type == "MONEY" and den.logical_type == "MONEY" and len(units) != 1:
                    raise TaseError("CURRENCY_MISMATCH")
                with localcontext() as ctx:
                    ctx.prec = 50
                    a = sum((r.value for r in numerator), Decimal(0))
                    b = sum((r.value for r in denominator), Decimal(0))
                    if b == 0:
                        raise TaseError("ZERO_DENOMINATOR")
                    value = a / b
                unit = "fraction" if num.unit == den.unit else num.unit + "/" + den.unit
                count = len(numerator) + len(denominator)
            elif req.operation == "WEIGHTED_MEAN":
                weight_metric = catalog.metrics[(req.product, metric.denominator_or_weight)]
                weights = _selected(dataset.rows, weight_metric.code, group, group_keys, begin, end)
                _check_rows(selected, metric, begin, end, dataset, req.require_full_coverage)
                _check_rows(weights, weight_metric, begin, end, dataset, req.require_full_coverage)
                # Preserve full atomic keys/dates rather than joining by bucket alone.
                key = lambda r: (r.dimensions, r.start, r.end)
                rate_map = {key(r): r.value for r in selected}
                weight_map = {key(r): r.value for r in weights}
                if len(rate_map) != len(selected) or len(weight_map) != len(weights):
                    raise TaseError("DUPLICATE_PAIR_KEY")
                if not rate_map or rate_map.keys() != weight_map.keys():
                    raise TaseError("PAIR_ALIGNMENT")
                if any(w < 0 for w in weight_map.values()):
                    raise TaseError("NEGATIVE_WEIGHT")
                with localcontext() as ctx:
                    ctx.prec = 50
                    denominator = sum(weight_map.values(), Decimal(0))
                    if denominator <= 0:
                        raise TaseError("ZERO_TOTAL_WEIGHT")
                    value = sum((v * weight_map[k] for k, v in rate_map.items()), Decimal(0)) / denominator
                unit = metric.unit
                count = len(selected)
            elif req.operation == "LAST_AS_OF":
                _check_rows(selected, metric, begin, end, dataset, False, stock=True)
                if not selected:
                    raise TaseError("MISSING_SNAPSHOT")
                by_leaf: dict[tuple[tuple[str, str], ...], Observation] = {}
                for r in sorted(selected, key=lambda r: r.start):
                    if r.dimensions in by_leaf and r.start == by_leaf[r.dimensions].start:
                        raise TaseError("DUPLICATE_SNAPSHOT")
                    by_leaf[r.dimensions] = r
                for row in by_leaf.values():
                    if (end - timedelta(days=1) - row.start).days > (req.max_snapshot_age_days
                             if req.max_snapshot_age_days is not None else 31):
                        raise TaseError("STALE_SNAPSHOT")
                value = sum((r.value for r in by_leaf.values()), Decimal(0))
                unit = metric.unit
                count = len(by_leaf)
            else:
                _check_rows(selected, metric, begin, end, dataset, req.require_full_coverage)
                value = _statistic(req.operation, [r.value for r in selected], req.quantile_alpha)
                unit = metric.unit
                if req.operation in {"VAR_POP", "VAR_SAMPLE"}:
                    unit += "^2"
                count = len(selected)
            results.append(ResultRow(group, begin, end, _text(value), unit, count))
    digest = _fingerprint({"plan": plan.plan_sha, "dataset": dataset.content_sha,
                           "rows": [{"group": list(r.group), "period": [r.start.isoformat(), r.end.isoformat()],
                                     "value": r.value, "unit": r.unit, "count": r.observation_count}
                                    for r in results]})
    return TaseResult(plan.plan_sha, dataset.content_sha, tuple(results), digest)
