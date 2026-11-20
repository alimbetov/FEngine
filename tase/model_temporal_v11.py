"""ModelTemporalCapabilityV1.1 — non-additive, source-bound temporal strategies.

Four explicitly reviewed Python-reference-only projections:
- EVM CPI: recompute from *latest aligned* earnedValue/actualCost snapshots.
- NPV: execute the real HC NPV model again on each bucket and the complete
  source-period series, never add independently discounted bucket NPVs.

All calendar bucketing, source grain checks, gaps and last-as-of evaluation
reuse the existing TASE engine. No financial S2, FIN source authentication,
Redis session, IO or persistence is implemented here.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from fengine_hc.reference import (
    ContractRegistry, IMPLEMENTATION_REVISION, ReferenceEngine, fingerprint, number,
)
from tase.reference import (
    Catalog, Dataset, Metric, Observation, Operator, PeriodRequest, ProductPack,
    ResultRow, TaseError, TaseResult, _buckets, calculate, compile_plan,
)
from tase.model_temporal import (
    ModelTemporalRequest, ModelTemporalResult, _date, _sha, _datestring,
)

SCHEMA = "FENGINE_MODEL_TEMPORAL_CAPABILITY_V11"
PRODUCT = "HC_TEMPORAL_V11_REFERENCE"
STATUS = "PYTHON_REFERENCE_NOT_S2"
COLUMNS = (
    "modelCode", "variantCode", "outputField", "temporalStrategy",
    "sourceGrain", "outputGrains", "componentNumerator",
    "componentDenominator", "componentTimeSemantics", "ratePolicy", "status",
)

# Only explicitly reviewed model/variant/output contracts can be registered.
# Generic SQL/CSV edits cannot silently authorize any other numeric HC field.
REVIEWED = {
    ("HC.COST.07", "EVM_BAC_CPI", "costPerformanceIndex"): (
        "RECOMPUTE_FROM_COMPONENTS", "AS_OF", "MONTH,QUARTER,YEAR",
        "earnedValue", "actualCost", "LAST_AS_OF_MATCHED_BASELINE", "NONE",
    ),
    ("HC.COST.07", "EVM_EAC_FORECAST", "costPerformanceIndex"): (
        "RECOMPUTE_FROM_COMPONENTS", "AS_OF", "MONTH,QUARTER,YEAR",
        "earnedValue", "actualCost", "LAST_AS_OF_MATCHED_BASELINE", "NONE",
    ),
    ("HC.DCF.01", "PERIOD_END_NPV", "npv"): (
        "RE_EXECUTE_FULL_WINDOW", "MONTH", "MONTH,QUARTER,YEAR",
        "cashflows", "discountRate", "ONE_CASHFLOW_PER_SOURCE_PERIOD",
        "EFFECTIVE_RATE_PER_SOURCE_PERIOD_PERIOD_END",
    ),
    ("HC.DCF.01", "MIDPERIOD_NPV", "npv"): (
        "RE_EXECUTE_FULL_WINDOW", "MONTH", "MONTH,QUARTER,YEAR",
        "cashflows", "discountRate", "ONE_CASHFLOW_PER_SOURCE_PERIOD",
        "EFFECTIVE_RATE_PER_SOURCE_PERIOD_MIDPERIOD",
    ),
}


@dataclass(frozen=True)
class ModelTemporalCapabilityV11:
    model_code: str
    variant_code: str
    output_field: str
    strategy: str
    source_grain: str
    output_grains: frozenset[str]
    numerator_field: str
    denominator_field: str
    component_time_semantics: str
    rate_policy: str
    revision_sha256: str


class ModelTemporalRegistryV11:
    def __init__(self, root: Path,
                 definitions: Mapping[tuple[str, str, str], ModelTemporalCapabilityV11]):
        self.root = Path(root)
        self._definitions = MappingProxyType(dict(definitions))

    @property
    def capabilities(self) -> Mapping[tuple[str, str, str], ModelTemporalCapabilityV11]:
        return self._definitions

    @classmethod
    def load(cls, root: Path, *, reference_mode: bool = False,
             path: Path | None = None) -> "ModelTemporalRegistryV11":
        if not reference_mode:
            raise TaseError("FINANCIAL_S2_REQUIRED")
        contracts = ContractRegistry(Path(root))
        target = path or Path(root) / "catalog" / "model_temporal_capabilities_v11.tsv"
        with Path(target).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != list(COLUMNS):
                raise TaseError("TEMPORAL_V11_SCHEMA_MISMATCH")
            records = list(reader)
        if not records:
            raise TaseError("TEMPORAL_V11_EMPTY")
        mapping = {}
        for row in records:
            if (None in row or set(row) != set(COLUMNS)
                    or any(not isinstance(row[k], str) or not row[k] for k in COLUMNS)):
                raise TaseError("TEMPORAL_V11_SCHEMA_MISMATCH")
            key = row["modelCode"], row["variantCode"], row["outputField"]
            if key in mapping:
                raise TaseError("TEMPORAL_V11_DUPLICATE_DESCRIPTOR")
            if (key[0], key[1]) not in contracts.variants:
                raise TaseError("TEMPORAL_V11_UNKNOWN_VARIANT")
            if row["status"] != STATUS:
                raise TaseError("TEMPORAL_V11_UNREVIEWED")
            actual = tuple(row[name] for name in COLUMNS[3:-1])
            if key not in REVIEWED or actual != REVIEWED[key]:
                raise TaseError("TEMPORAL_V11_POLICY_NOT_REVIEWED")
            grains = row["outputGrains"].split(",")
            if len(grains) != len(set(grains)) or any(not k for k in grains):
                raise TaseError("TEMPORAL_V11_GRAINS_INVALID")
            mapping[key] = ModelTemporalCapabilityV11(
                model_code=key[0], variant_code=key[1], output_field=key[2],
                strategy=row["temporalStrategy"], source_grain=row["sourceGrain"],
                output_grains=frozenset(grains),
                numerator_field=row["componentNumerator"],
                denominator_field=row["componentDenominator"],
                component_time_semantics=row["componentTimeSemantics"],
                rate_policy=row["ratePolicy"],
                revision_sha256=fingerprint({"contract": SCHEMA, "row": row}),
            )
        return cls(Path(root), mapping)

    def resolve(self, req: ModelTemporalRequest) -> ModelTemporalCapabilityV11:
        key = req.model_code, req.variant_code, req.output_field
        cap = self._definitions.get(key)
        if cap is None:
            raise TaseError("TEMPORAL_CAPABILITY_NOT_ADMITTED")
        if req.source_grain != cap.source_grain:
            raise TaseError("TEMPORAL_SOURCE_GRAIN_NOT_ALLOWED")
        if req.output_grain not in cap.output_grains:
            raise TaseError("TEMPORAL_OUTPUT_GRAIN_NOT_ALLOWED")
        return cap


@dataclass(frozen=True)
class ModelTemporalRunV11:
    """Source-unit-tagged temporal model input with self-consistency SHA.

    SHA does not prove financial source authorization; only local input identity.
    The caller must authenticate source account/user/project externally.
    """
    start: date
    end: date | None
    currency: str
    inputs: Mapping[str, Any]
    config: Mapping[str, Any]
    source_window_sha256: str
    dimensions: tuple[tuple[str, str], ...] = ()


def temporal_v11_source_sha256(
    model: str, variant: str, start: date, end: date | None,
    currency: str, inputs: Mapping[str, Any], config: Mapping[str, Any],
    dimensions: tuple[tuple[str, str], ...] = (),
) -> str:
    _date(start)
    if end is not None:
        _date(end)
    return fingerprint({
        "contract": "HC_TEMPORAL_V11_WINDOW_SOURCE_V1",
        "model": model, "variant": variant,
        "start": start.isoformat(), "end": end.isoformat() if end else None,
        "currency": currency, "inputs": inputs, "config": config,
        "dimensions": list(dimensions),
    })


def _build_catalog(root: Path, cap: ModelTemporalCapabilityV11,
                   req: ModelTemporalRequest, fields: tuple[str, ...],
                   operator: str) -> Catalog:
    original = Catalog.load(root, reference_mode=True)
    kind = "STOCK" if operator == "LAST_AS_OF" else "FLOW"
    temporal = "AS_OF" if kind == "STOCK" else "INTERVAL_FLOW"
    pack = ProductPack(
        PRODUCT, "HC_TEMPORAL_V11_REFERENCE",
        cap.output_grains, frozenset((operator,)), STATUS,
    )
    metrics = {
        (PRODUCT, field): Metric(
            PRODUCT, field, "MONEY", req.currency, kind, temporal,
            operator, frozenset((operator,)), "", "", STATUS,
        ) for field in fields
    }
    return Catalog(
        {**original.products, PRODUCT: pack},
        {**original.metrics, **metrics},
        original.operators, original.predicates, reference_mode=True,
    )


def _period(req: ModelTemporalRequest, field: str,
            operation: str) -> PeriodRequest:
    return PeriodRequest(
        product=PRODUCT, metric=field, operation=operation, scope=req.scope,
        start=req.start, end=req.end, grain=req.output_grain,
        group_by=req.group_by, fiscal_start_month=req.fiscal_start_month,
        require_full_coverage=req.require_full_coverage,
        max_snapshot_age_days=req.max_snapshot_age_days,
        source_grain=req.source_grain, include_total=req.include_total,
    )


def _check_run(cap: ModelTemporalCapabilityV11, req: ModelTemporalRequest,
               run: ModelTemporalRunV11) -> None:
    _date(run.start)
    if run.end is not None:
        _date(run.end)
    if not isinstance(run.inputs, Mapping) or not isinstance(run.config, Mapping):
        raise TaseError("TEMPORAL_V11_INPUT_SCHEMA")
    if run.currency != req.currency:
        raise TaseError("TEMPORAL_MODEL_CURRENCY_MISMATCH")
    if (not isinstance(run.dimensions, tuple)
            or run.dimensions != tuple(sorted(run.dimensions))
            or len({k for k, _ in run.dimensions}) != len(run.dimensions)
            or tuple(k for k, _ in run.dimensions) != req.group_by):
        raise TaseError("TEMPORAL_V11_DIMENSION_MISMATCH")
    _sha(run.source_window_sha256, "TEMPORAL_MODEL_SOURCE_SHA_REQUIRED")
    actual_sha = temporal_v11_source_sha256(
        cap.model_code, cap.variant_code, run.start, run.end, run.currency,
        run.inputs, run.config, run.dimensions,
    )
    if run.source_window_sha256 != actual_sha:
        raise TaseError("TEMPORAL_V11_SOURCE_REVISION_MISMATCH")
    if cap.strategy == "RECOMPUTE_FROM_COMPONENTS":
        if run.end is not None or not req.start <= run.start < req.end:
            raise TaseError("TEMPORAL_V11_SNAPSHOT_OUTSIDE_PERIOD")
        if _datestring(run.inputs.get("asOf")) != run.start.isoformat():
            raise TaseError("TEMPORAL_V11_SNAPSHOT_DATE_MISMATCH")
        if run.inputs.get("currency") != req.currency:
            raise TaseError("TEMPORAL_MODEL_CURRENCY_MISMATCH")
        _sha(run.inputs.get("baselineRevision"),
             "TEMPORAL_V11_BASELINE_SHA_REQUIRED")
    elif cap.strategy == "RE_EXECUTE_FULL_WINDOW":
        if (run.end is None or not req.start <= run.start < run.end <= req.end):
            raise TaseError("TEMPORAL_V11_INTERVAL_OUTSIDE_REQUEST")
        if (run.start.day != 1 or
                (run.end.year * 12 + run.end.month -
                 run.start.year * 12 - run.start.month) != 1
                or run.end.day != 1):
            raise TaseError("TEMPORAL_V11_SOURCE_MONTH_REQUIRED")
        if set(run.inputs) != {"cashflows", "discountRate"}:
            raise TaseError("TEMPORAL_V11_NPV_INPUT_SCHEMA")
        cashflows = run.inputs["cashflows"]
        if not isinstance(cashflows, (tuple, list)) or len(cashflows) != 1:
            raise TaseError("TEMPORAL_V11_ONE_FLOW_PER_PERIOD_REQUIRED")
        number(cashflows[0])
        number(run.inputs["discountRate"])
        if cap.rate_policy.endswith("PERIOD_END"):
            timing = "PERIOD_END"
        else:
            timing = "MIDPERIOD"
        if (set(run.config) != {"timingConvention"}
                or run.config["timingConvention"] != timing):
            raise TaseError("TEMPORAL_V11_TIMING_POLICY_MISMATCH")
    else:
        raise TaseError("TEMPORAL_V11_STRATEGY_NOT_REVIEWED")


def _join_receipt(cap: ModelTemporalCapabilityV11,
                  req: ModelTemporalRequest,
                  receipts: list[dict[str, Any]],
                  output: TaseResult,
                  tase_plan_shas: list[str],
                  sources: tuple[str, ...]) -> ModelTemporalResult:
    ordered = sorted(receipts, key=lambda row: (
        row["start"], row["end"] or "", row["dimensions"], row["source"],
    ))
    source_sha = fingerprint({
        "contract": "HC_TEMPORAL_V11_INPUT_BATCH_V1",
        "capability": cap.revision_sha256, "scope": req.scope,
        "windows": ordered,
    })
    plan_sha = fingerprint({
        "contract": SCHEMA, "capability": cap.revision_sha256,
        "tasePlans": tase_plan_shas,
        "modelRevision": IMPLEMENTATION_REVISION,
        "sources": source_sha,
    })
    result_sha = fingerprint({
        "contract": "HC_TEMPORAL_V11_RESULT_V1",
        "plan": plan_sha, "taseResult": output.result_sha,
    })
    return ModelTemporalResult(
        cap.revision_sha256, source_sha, plan_sha, result_sha,
        output, sources,
    )


def _ratio_rows(numerator: list[ResultRow],
                denominator: list[ResultRow]) -> tuple[ResultRow, ...]:
    if len(numerator) != len(denominator):
        raise TaseError("TEMPORAL_V11_COMPONENT_ALIGNMENT")
    result = []
    for n, d in zip(numerator, denominator):
        if (n.group, n.start, n.end) != (d.group, d.start, d.end):
            raise TaseError("TEMPORAL_V11_COMPONENT_ALIGNMENT")
        with localcontext() as ctx:
            ctx.prec = 40
            a, b = number(n.value), number(d.value)
            if b == 0:
                raise TaseError("ZERO_DENOMINATOR")
            value = a / b
            value_text = format(+value, "f")
        result.append(ResultRow(
            n.group, n.start, n.end, value_text, "fraction",
            n.observation_count + d.observation_count,
            "FULL" if n.coverage == d.coverage == "FULL" else "UNKNOWN",
            "COMPLETE" if n.status == d.status == "COMPLETE" else "PARTIAL",
        ))
    return tuple(result)


def _compute_component_ratio(
    root: Path, cap: ModelTemporalCapabilityV11,
    req: ModelTemporalRequest,
    executed: Sequence[tuple[ModelTemporalRunV11, Any]],
) -> tuple[TaseResult, list[str]]:
    cat = _build_catalog(
        root, cap, req, (cap.numerator_field, cap.denominator_field),
        "LAST_AS_OF",
    )
    obs = []
    baselines = {}
    for run, result in executed:
        group = run.dimensions
        revision = run.inputs["baselineRevision"]
        if group in baselines and baselines[group] != revision:
            raise TaseError("TEMPORAL_EVM_BASELINE_CHANGED")
        baselines[group] = revision
        with localcontext() as ctx:
            ctx.prec = 40
            a = number(run.inputs[cap.numerator_field])
            b = number(run.inputs[cap.denominator_field])
            if b == 0:
                raise TaseError("ZERO_DENOMINATOR")
            expected = a / b
            actual = number(result.output[cap.output_field])
            if abs(expected - actual) > Decimal("1e-34"):
                raise TaseError("TEMPORAL_V11_MODEL_COMPONENT_MISMATCH")
        for field in (cap.numerator_field, cap.denominator_field):
            obs.append(Observation(
                product=PRODUCT, metric=field, scope=req.scope,
                start=run.start, end=None, value=run.inputs[field],
                unit=req.currency, source_sha=result.output_sha256,
                dimensions=run.dimensions,
            ))
    batch_sha = fingerprint({
        "scope": req.scope, "model": cap.model_code,
        "source": sorted(r.source_window_sha256 for r, _ in executed),
        "componentResults": sorted(r.output_sha256 for _, r in executed),
    })
    dataset = Dataset(
        req.scope, batch_sha, tuple(obs),
        watermark=req.watermark,
        interval_coverage_attested=req.coverage_attested,
    )
    p_num = _period(req, cap.numerator_field, "LAST_AS_OF")
    p_den = _period(req, cap.denominator_field, "LAST_AS_OF")
    a = calculate(cat, p_num, dataset)
    b = calculate(cat, p_den, dataset)
    rows = _ratio_rows(list(a.rows), list(b.rows))
    totals = _ratio_rows(list(a.total_rows), list(b.total_rows))
    digest = fingerprint({
        "contract": "HC_TEMPORAL_V11_COMPONENT_RATIO_V1",
        "numeratorResult": a.result_sha, "denominatorResult": b.result_sha,
        "rows": [{"group": r.group, "start": r.start, "end": r.end,
                  "value": r.value, "unit": r.unit} for r in rows],
        "totals": [{"group": r.group, "start": r.start, "end": r.end,
                    "value": r.value, "unit": r.unit} for r in totals],
    })
    combined = TaseResult(
        fingerprint({"num": a.plan_sha, "den": b.plan_sha}),
        batch_sha, rows, digest,
        status="COMPLETE" if req.require_full_coverage else "PARTIAL",
        total_rows=totals,
    )
    return combined, [a.plan_sha, b.plan_sha]


def _compute_reexecuted(
    root: Path, cap: ModelTemporalCapabilityV11,
    req: ModelTemporalRequest,
    executed: Sequence[tuple[ModelTemporalRunV11, Any]],
    engine: ReferenceEngine,
) -> tuple[TaseResult, list[str]]:
    cat = _build_catalog(root, cap, req, ("CASHFLOW",), "SUM")
    observations = [
        Observation(
            product=PRODUCT, metric="CASHFLOW", scope=req.scope,
            start=run.start, end=run.end,
            value=run.inputs["cashflows"][0], unit=req.currency,
            source_sha=receipt.output_sha256,
            dimensions=run.dimensions,
        ) for run, receipt in executed
    ]
    batch_sha = fingerprint({
        "sourceReceipts": sorted(r.source_window_sha256 for r, _ in executed),
        "modelOutputs": sorted(r.output_sha256 for _, r in executed),
    })
    dataset = Dataset(
        req.scope, batch_sha, tuple(observations),
        watermark=req.watermark,
        interval_coverage_attested=req.coverage_attested,
    )
    period = _period(req, "CASHFLOW", "SUM")
    # Reuse TASE's calendar, source-grain and full coverage validators. The
    # additive SUM return is deliberately *not* used for the NPV answer.
    checked = calculate(cat, period, dataset)
    windows = _buckets(period)
    groups = sorted({r.dimensions for r, _ in executed})
    outputs: list[ResultRow] = []
    whole: list[ResultRow] = []
    def reexecute(begin: date, end: date,
                  group: tuple[tuple[str, str], ...]) -> ResultRow:
        selected = sorted(
            (r for r, _ in executed if r.dimensions == group
             and r.start >= begin and r.end is not None and r.end <= end),
            key=lambda r: r.start,
        )
        if not selected:
            raise TaseError("MISSING_PERIOD_SOURCE")
        # Each selected month must use the exact same effective per-source
        # period rate, no implicit daily discounting or annual conversion.
        rates = {format(number(r.inputs["discountRate"]).normalize(), "f")
                 for r in selected}
        if len(rates) != 1:
            raise TaseError("TEMPORAL_V11_DISCOUNT_RATE_MISMATCH")
        rate = next(iter(rates))
        inputs = {"cashflows": [r.inputs["cashflows"][0] for r in selected],
                  "discountRate": rate}
        if any(dict(r.config) != dict(selected[0].config) for r in selected):
            raise TaseError("TEMPORAL_V11_METHOD_CONFIG_MISMATCH")
        receipt = engine.calculate(
            cap.model_code, cap.variant_code, inputs,
            selected[0].config, reference_mode=True,
        )
        value = receipt.output[cap.output_field]
        number(value)
        return ResultRow(
            group, begin, end, value, req.currency, len(selected),
            "FULL" if req.require_full_coverage else "UNKNOWN",
            "COMPLETE" if req.require_full_coverage else "PARTIAL",
        )

    for begin, end in windows:
        for group in groups:
            outputs.append(reexecute(begin, end, group))
    if req.include_total:
        for group in groups:
            whole.append(reexecute(req.start, req.end, group))
    digest = fingerprint({
        "contract": "HC_TEMPORAL_V11_REEXECUTE_V1",
        "validatedTaseResult": checked.result_sha,
        "bucketResults": [
            {"group": r.group, "begin": r.start, "end": r.end,
             "value": r.value} for r in outputs
        ],
        "grandTotals": [
            {"group": r.group, "begin": r.start, "end": r.end,
             "value": r.value} for r in whole
        ],
    })
    result = TaseResult(
        checked.plan_sha, batch_sha, tuple(outputs), digest,
        status="COMPLETE" if req.require_full_coverage else "PARTIAL",
        total_rows=tuple(whole),
    )
    return result, [checked.plan_sha]


def calculate_model_temporal_v11(
    registry: ModelTemporalRegistryV11,
    request: ModelTemporalRequest,
    runs: Sequence[ModelTemporalRunV11],
    *, reference_mode: bool = False,
) -> ModelTemporalResult:
    """One interface, two explicitly selected non-additive temporal strategies."""
    if not reference_mode:
        raise TaseError("FINANCIAL_S2_REQUIRED")
    if not isinstance(registry, ModelTemporalRegistryV11):
        raise TaseError("TEMPORAL_V11_REGISTRY_REQUIRED")
    cap = registry.resolve(request)
    if not isinstance(runs, (list, tuple)) or not 1 <= len(runs) <= 10000:
        raise TaseError("TEMPORAL_MODEL_RUN_BUDGET")
    if cap.strategy == "RE_EXECUTE_FULL_WINDOW":
        if (not request.coverage_attested or request.watermark is None
                or request.watermark < request.end):
            raise TaseError("COVERAGE_UNKNOWN")
    engine = ReferenceEngine(registry.root)
    executed = []
    receipts = []
    for run in runs:
        _check_run(cap, request, run)
        result = engine.calculate(
            cap.model_code, cap.variant_code,
            run.inputs, run.config, reference_mode=True,
        )
        if cap.output_field not in result.output:
            raise TaseError("TEMPORAL_MODEL_OUTPUT_FIELD_MISSING")
        number(result.output[cap.output_field])
        if cap.strategy == "RECOMPUTE_FROM_COMPONENTS":
            if result.output.get("currency") != request.currency:
                raise TaseError("TEMPORAL_MODEL_OUTPUT_CURRENCY_MISMATCH")
        executed.append((run, result))
        receipts.append({
            "start": run.start.isoformat(),
            "end": run.end.isoformat() if run.end else None,
            "dimensions": list(run.dimensions),
            "source": run.source_window_sha256,
            "inputs": result.inputs_sha256, "config": result.config_sha256,
            "output": result.output_sha256,
        })
    if cap.strategy == "RECOMPUTE_FROM_COMPONENTS":
        aggregates, tase_plans = _compute_component_ratio(
            registry.root, cap, request, executed,
        )
    elif cap.strategy == "RE_EXECUTE_FULL_WINDOW":
        aggregates, tase_plans = _compute_reexecuted(
            registry.root, cap, request, executed, engine,
        )
    else:
        raise TaseError("TEMPORAL_V11_STRATEGY_NOT_REVIEWED")
    return _join_receipt(
        cap, request, receipts, aggregates, tase_plans,
        tuple(sorted(r.output_sha256 for _, r in executed)),
    )
