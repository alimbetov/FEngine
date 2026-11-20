"""Temporal V1.2: dated XNPV, exposure-weighted CAPM, fixed-baseline PVM.

A separate, declared strategy for each mathematical meaning. The existing TASE
calendar and coverage engine validates all windows and performs weighted means
and latest-snapshot selections. XNPV re-executes the actual HC model on raw
dated cashflows using one immutable annual rate and valuation origin.

Mathematical reference only; content digests are NOT signatures or FIN source
authorization. No user data is persisted or logged by this module.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from fengine_hc.reference import (
    ContractRegistry, IMPLEMENTATION_REVISION, ReferenceEngine,
    fingerprint, number,
)
from tase.reference import (
    Catalog, Dataset, Metric, Observation, PeriodRequest, ProductPack,
    ResultRow, TaseError, TaseResult, _buckets, calculate,
)
from tase.model_temporal import (
    ModelTemporalRequest, ModelTemporalResult, _date, _datestring, _sha,
)

SCHEMA = "FENGINE_MODEL_TEMPORAL_CAPABILITY_V12"
STATUS = "PYTHON_REFERENCE_NOT_S2"
PRODUCT = "HC_TEMPORAL_V12_REFERENCE"
COLUMNS = ("modelCode", "variantCode", "outputField", "strategy",
           "sourceGrain", "outputGrains", "basisPolicy", "status")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,95}\Z")
REVIEWED = {
    ("HC.DCF.02", "EXACT_DATE_XNPV", "xnpv"): (
        "DATED_FULL_WINDOW_REEXECUTE", "EVENT_AT", "DAY,MONTH,QUARTER,YEAR",
        "ACT_365_FIXED_SAME_ANNUAL_EFFECTIVE_RATE_AND_VALUATION_ORIGIN",
    ),
    ("HC.CAP.01", "CAPM_BASE", "costOfEquity"): (
        "EXPOSURE_WEIGHTED_MODEL_RATE", "EVENT_AT", "MONTH,QUARTER,YEAR",
        "NONNEGATIVE_EXPOSURE_SAME_RF_AND_PREMIUM",
    ),
    **{
        ("HC.COST.08", variant, output): (
            "FIXED_BASELINE_LAST_SNAPSHOT", "AS_OF", "MONTH,QUARTER,YEAR",
            "SAME_PVM_BASELINE_AND_PRICE_VINTAGE",
        )
        for variant, output in (
            ("PRICE_VARIANCE", "priceVariance"),
            ("QUANTITY_VARIANCE", "quantityVariance"),
            ("MIX_VARIANCE", "mixVariance"),
        )
    },
}


@dataclass(frozen=True)
class ModelTemporalCapabilityV12:
    model_code: str
    variant_code: str
    output_field: str
    strategy: str
    source_grain: str
    output_grains: frozenset[str]
    basis_policy: str
    revision_sha256: str


class ModelTemporalRegistryV12:
    def __init__(self, root: Path,
                 definitions: Mapping[tuple[str, str, str], ModelTemporalCapabilityV12]):
        self.root = Path(root)
        self._definitions = MappingProxyType(dict(definitions))

    @property
    def capabilities(self) -> Mapping[tuple[str, str, str], ModelTemporalCapabilityV12]:
        return self._definitions

    @classmethod
    def load(cls, root: Path, *, reference_mode: bool = False,
             path: Path | None = None) -> "ModelTemporalRegistryV12":
        if not reference_mode:
            raise TaseError("FINANCIAL_S2_REQUIRED")
        root = Path(root)
        contracts = ContractRegistry(root)
        with (path or root / "catalog" / "model_temporal_capabilities_v12.tsv").open(
            encoding="utf-8", newline=""
        ) as fp:
            reader = csv.DictReader(fp, delimiter="\t")
            if reader.fieldnames != list(COLUMNS):
                raise TaseError("TEMPORAL_V12_SCHEMA_MISMATCH")
            records = list(reader)
        if not records:
            raise TaseError("TEMPORAL_V12_EMPTY")
        definitions: dict[tuple[str, str, str], ModelTemporalCapabilityV12] = {}
        for entry in records:
            if (None in entry or set(entry) != set(COLUMNS)
                    or any(not isinstance(entry[col], str) or not entry[col]
                           for col in COLUMNS)):
                raise TaseError("TEMPORAL_V12_SCHEMA_MISMATCH")
            key = entry["modelCode"], entry["variantCode"], entry["outputField"]
            if key in definitions:
                raise TaseError("TEMPORAL_V12_DUPLICATE_DESCRIPTOR")
            if key[:2] not in contracts.variants:
                raise TaseError("TEMPORAL_V12_UNKNOWN_VARIANT")
            if entry["status"] != STATUS:
                raise TaseError("TEMPORAL_V12_UNREVIEWED")
            declared = tuple(entry[field] for field in COLUMNS[3:-1])
            if REVIEWED.get(key) != declared:
                raise TaseError("TEMPORAL_V12_POLICY_NOT_REVIEWED")
            grains = entry["outputGrains"].split(",")
            if len(grains) != len(set(grains)) or not grains or any(not g for g in grains):
                raise TaseError("TEMPORAL_V12_GRAINS_INVALID")
            definitions[key] = ModelTemporalCapabilityV12(
                key[0], key[1], key[2], entry["strategy"], entry["sourceGrain"],
                frozenset(grains), entry["basisPolicy"],
                fingerprint({"schema": SCHEMA, "definition": entry}),
            )
        return cls(root, definitions)

    def resolve(self, request: ModelTemporalRequest) -> ModelTemporalCapabilityV12:
        key = request.model_code, request.variant_code, request.output_field
        capability = self._definitions.get(key)
        if capability is None:
            raise TaseError("TEMPORAL_CAPABILITY_NOT_ADMITTED")
        if request.source_grain != capability.source_grain:
            raise TaseError("TEMPORAL_SOURCE_GRAIN_NOT_ALLOWED")
        if request.output_grain not in capability.output_grains:
            raise TaseError("TEMPORAL_OUTPUT_GRAIN_NOT_ALLOWED")
        return capability


@dataclass(frozen=True)
class ModelTemporalRunV12:
    start: date
    end: date | None
    currency: str
    inputs: Mapping[str, Any]
    config: Mapping[str, Any]
    source_window_sha256: str
    event_id: str
    dimensions: tuple[tuple[str, str], ...] = ()
    exposure_weight: str | None = None


def temporal_v12_source_sha256(
    model: str, variant: str, start: date, end: date | None,
    currency: str, inputs: Mapping[str, Any], config: Mapping[str, Any],
    event_id: str, dimensions: tuple[tuple[str, str], ...] = (),
    exposure_weight: str | None = None,
) -> str:
    _date(start)
    if end is not None:
        _date(end)
    return fingerprint({
        "contract": "HC_TEMPORAL_V12_SOURCE_V1",
        "model": model, "variant": variant, "start": start,
        "end": end, "currency": currency,
        "inputs": inputs, "config": config, "eventId": event_id,
        "dimensions": list(dimensions), "exposureWeight": exposure_weight,
    })


def _request(req: ModelTemporalRequest, metric: str,
             reducer: str, product: str = PRODUCT) -> PeriodRequest:
    return PeriodRequest(
        product=product, metric=metric, operation=reducer,
        scope=req.scope, start=req.start, end=req.end, grain=req.output_grain,
        group_by=req.group_by, fiscal_start_month=req.fiscal_start_month,
        require_full_coverage=req.require_full_coverage,
        max_snapshot_age_days=req.max_snapshot_age_days,
        source_grain=req.source_grain, include_total=req.include_total,
    )


def _catalog(root: Path, cap: ModelTemporalCapabilityV12,
             req: ModelTemporalRequest) -> Catalog:
    original = Catalog.load(root, reference_mode=True)
    strat = cap.strategy
    if strat == "DATED_FULL_WINDOW_REEXECUTE":
        metric = Metric(PRODUCT, "CASHFLOW", "MONEY", req.currency,
                        "FLOW", "EVENT_AT", "SUM", frozenset(("SUM",)),
                        "", "", STATUS)
        metrics = {"CASHFLOW": metric}
        operations = frozenset(("SUM",))
    elif strat == "EXPOSURE_WEIGHTED_MODEL_RATE":
        metric = Metric(PRODUCT, "MODEL_RATE", "RATE", "fraction",
                        "RATE", "EVENT_AT", "WEIGHTED_MEAN",
                        frozenset(("WEIGHTED_MEAN",)), "", "EXPOSURE", STATUS)
        weight = Metric(PRODUCT, "EXPOSURE", "MONEY", req.currency,
                        "FLOW", "EVENT_AT", "SUM", frozenset(("SUM",)),
                        "", "", STATUS)
        metrics = {"MODEL_RATE": metric, "EXPOSURE": weight}
        operations = frozenset(("WEIGHTED_MEAN", "SUM"))
    elif strat == "FIXED_BASELINE_LAST_SNAPSHOT":
        metric = Metric(PRODUCT, "PVM_EFFECT", "MONEY", req.currency,
                        "STOCK", "AS_OF", "LAST_AS_OF",
                        frozenset(("LAST_AS_OF",)), "", "", STATUS)
        metrics = {"PVM_EFFECT": metric}
        operations = frozenset(("LAST_AS_OF",))
    else:
        raise TaseError("TEMPORAL_V12_STRATEGY_NOT_REVIEWED")
    pack = ProductPack(PRODUCT, "HC_TEMPORAL_V12_REFERENCE",
                       cap.output_grains, operations, STATUS)
    return Catalog(
        {**original.products, PRODUCT: pack},
        {**original.metrics, **{(PRODUCT, k): v for k, v in metrics.items()}},
        original.operators, original.predicates, reference_mode=True,
    )


def _validate_run(cap: ModelTemporalCapabilityV12, req: ModelTemporalRequest,
                  run: ModelTemporalRunV12) -> None:
    _date(run.start)
    if run.end is not None:
        _date(run.end)
    if run.end is not None or not req.start <= run.start < req.end:
        raise TaseError("TEMPORAL_V12_EVENT_DATE_OUTSIDE_RANGE")
    if (not isinstance(run.event_id, str)
            or ID.fullmatch(run.event_id) is None):
        raise TaseError("TEMPORAL_V12_EVENT_ID_REQUIRED")
    if (not isinstance(run.dimensions, tuple)
            or run.dimensions != tuple(sorted(run.dimensions))
            or tuple(k for k, _ in run.dimensions) != req.group_by):
        raise TaseError("TEMPORAL_V12_DIMENSION_MISMATCH")
    if not isinstance(run.inputs, Mapping) or not isinstance(run.config, Mapping):
        raise TaseError("TEMPORAL_V12_INPUT_SCHEMA")
    if run.currency != req.currency:
        raise TaseError("TEMPORAL_MODEL_CURRENCY_MISMATCH")
    _sha(run.source_window_sha256, "TEMPORAL_MODEL_SOURCE_SHA_REQUIRED")
    if run.source_window_sha256 != temporal_v12_source_sha256(
        cap.model_code, cap.variant_code, run.start, run.end, run.currency,
        run.inputs, run.config, run.event_id, run.dimensions, run.exposure_weight,
    ):
        raise TaseError("TEMPORAL_V12_SOURCE_REVISION_MISMATCH")
    if cap.strategy == "DATED_FULL_WINDOW_REEXECUTE":
        if run.exposure_weight is not None:
            raise TaseError("TEMPORAL_V12_UNEXPECTED_WEIGHT")
        if set(run.inputs) != {"cashflows", "discountRate", "valuationDate"}:
            raise TaseError("TEMPORAL_V12_XNPV_INPUT_SCHEMA")
        if set(run.config) != {"dayCount"} or run.config["dayCount"] != "ACT_365_FIXED":
            raise TaseError("TEMPORAL_V12_DAYCOUNT_NOT_ADMITTED")
        if _datestring(run.inputs["valuationDate"]) != req.start.isoformat():
            raise TaseError("TEMPORAL_V12_VALUATION_ORIGIN_MISMATCH")
        flows = run.inputs["cashflows"]
        if not isinstance(flows, (tuple, list)) or len(flows) != 1:
            raise TaseError("TEMPORAL_V12_ONE_DATED_FLOW_REQUIRED")
        row = flows[0]
        if (not isinstance(row, Mapping) or set(row) != {"date", "amount"}
                or _datestring(row["date"]) != run.start.isoformat()):
            raise TaseError("TEMPORAL_V12_DATED_EVENT_MISMATCH")
        number(row["amount"])
        if number(run.inputs["discountRate"]) <= -1:
            raise TaseError("TEMPORAL_V12_ANNUAL_RATE_INVALID")
    elif cap.strategy == "EXPOSURE_WEIGHTED_MODEL_RATE":
        if set(run.inputs) != {"riskFreeRate", "beta", "marketRiskPremium"} or run.config:
            raise TaseError("TEMPORAL_V12_CAPM_INPUT_SCHEMA")
        for k in run.inputs:
            number(run.inputs[k])
        if run.exposure_weight is None:
            raise TaseError("TEMPORAL_V12_EXPOSURE_REQUIRED")
        if number(run.exposure_weight) < 0:
            raise TaseError("NEGATIVE_WEIGHT")
    elif cap.strategy == "FIXED_BASELINE_LAST_SNAPSHOT":
        if run.exposure_weight is not None:
            raise TaseError("TEMPORAL_V12_UNEXPECTED_WEIGHT")
        if _datestring(run.inputs.get("actualPeriod")) != run.start.isoformat():
            raise TaseError("TEMPORAL_V12_PVM_SNAPSHOT_DATE_MISMATCH")
        if _datestring(run.inputs.get("baselinePeriod")) >= req.start.isoformat():
            raise TaseError("TEMPORAL_V12_PVM_BASELINE_NOT_PRIOR")
        if run.inputs.get("currency") != req.currency:
            raise TaseError("TEMPORAL_MODEL_CURRENCY_MISMATCH")
        required = {"standardCostVintage", "volumeBaseline", "interactionAllocation"}
        if set(run.config) != required:
            raise TaseError("TEMPORAL_V12_PVM_CONFIGURATION_SCHEMA")
    else:
        raise TaseError("TEMPORAL_V12_STRATEGY_NOT_REVIEWED")


def _reexecute_xnpv(cap: ModelTemporalCapabilityV12, req: ModelTemporalRequest,
                   runs: Sequence[tuple[ModelTemporalRunV12, Any]],
                   periods: tuple[tuple[date, date], ...],
                   engine: ReferenceEngine) -> tuple[tuple[ResultRow, ...],
                                                    tuple[ResultRow, ...]]:
    groups = sorted({r.dimensions for r, _ in runs})
    def window(begin: date, end: date,
               group: tuple[tuple[str, str], ...]) -> ResultRow:
        window_runs = sorted(
            (run for run, _ in runs
             if begin <= run.start < end and run.dimensions == group),
            key=lambda r: (r.start, r.event_id),
        )
        if not window_runs:
            raise TaseError("MISSING_PERIOD_SOURCE")
        rates = {format(number(r.inputs["discountRate"]).normalize(), "f")
                 for r in window_runs}
        # Full-period rate consistency is also checked in the caller for
        # include_total=False, so bucket-only requests never bypass it.
        if len(rates) != 1:
            raise TaseError("TEMPORAL_V12_ANNUAL_RATE_MISMATCH")
        flow_values = [dict(run.inputs["cashflows"][0]) for run in window_runs]
        output = engine.calculate(
            cap.model_code, cap.variant_code,
            {"cashflows": flow_values,
             "discountRate": next(iter(rates)),
             "valuationDate": req.start.isoformat()},
            {"dayCount": "ACT_365_FIXED"}, reference_mode=True,
        )
        result = number(output.output[cap.output_field])
        return ResultRow(
            group, begin, end, format(+result, "f"), req.currency,
            len(flow_values),
            "FULL" if req.require_full_coverage else "UNKNOWN",
            "COMPLETE" if req.require_full_coverage else "PARTIAL",
        )
    buckets = tuple(window(b, e, group) for b, e in periods for group in groups)
    totals = tuple(window(req.start, req.end, group) for group in groups
                   ) if req.include_total else ()
    return buckets, totals


def calculate_model_temporal_v12(
    registry: ModelTemporalRegistryV12,
    request: ModelTemporalRequest,
    runs: Sequence[ModelTemporalRunV12],
    *, reference_mode: bool = False,
) -> ModelTemporalResult:
    if not reference_mode:
        raise TaseError("FINANCIAL_S2_REQUIRED")
    if not isinstance(registry, ModelTemporalRegistryV12):
        raise TaseError("TEMPORAL_V12_REGISTRY_REQUIRED")
    cap = registry.resolve(request)
    if not isinstance(runs, (tuple, list)) or not 1 <= len(runs) <= 10000:
        raise TaseError("TEMPORAL_MODEL_RUN_BUDGET")
    if cap.strategy != "FIXED_BASELINE_LAST_SNAPSHOT":
        if (not request.coverage_attested or request.watermark is None
                or request.watermark < request.end):
            raise TaseError("COVERAGE_UNKNOWN")
    catalog = _catalog(registry.root, cap, request)
    target = {
        "DATED_FULL_WINDOW_REEXECUTE": ("CASHFLOW", "SUM"),
        "EXPOSURE_WEIGHTED_MODEL_RATE": ("MODEL_RATE", "WEIGHTED_MEAN"),
        "FIXED_BASELINE_LAST_SNAPSHOT": ("PVM_EFFECT", "LAST_AS_OF"),
    }[cap.strategy]
    period_req = _request(request, *target)
    # Enforce aligned date bucketing and operator semantics before running HC.
    from tase.reference import compile_plan
    tase_plan = compile_plan(catalog, period_req)
    engine = ReferenceEngine(registry.root)
    observations: list[Observation] = []
    receipts = []
    executed: list[tuple[ModelTemporalRunV12, Any]] = []
    seen_events = set()
    seen_rate_dates = set()
    per_group: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}
    for run in runs:
        _validate_run(cap, request, run)
        event_key = run.dimensions, run.start, run.event_id
        if event_key in seen_events:
            raise TaseError("TEMPORAL_V12_DUPLICATE_SOURCE_EVENT")
        seen_events.add(event_key)
        if cap.strategy == "EXPOSURE_WEIGHTED_MODEL_RATE":
            rate_date = run.dimensions, run.start
            if rate_date in seen_rate_dates:
                # TASE weighted pairs use date+dimensions as their atomic key.
                raise TaseError("TEMPORAL_V12_WEIGHT_PAIR_DUPLICATE")
            seen_rate_dates.add(rate_date)
        group = run.dimensions
        if cap.strategy == "DATED_FULL_WINDOW_REEXECUTE":
            rate = format(number(run.inputs["discountRate"]).normalize(), "f")
            basis = {"rate": rate, "origin": run.inputs["valuationDate"]}
            if group in per_group and per_group[group] != basis:
                raise TaseError("TEMPORAL_V12_ANNUAL_RATE_MISMATCH")
            per_group.setdefault(group, basis)
        elif cap.strategy == "EXPOSURE_WEIGHTED_MODEL_RATE":
            basis = {
                "riskFree": format(number(run.inputs["riskFreeRate"]).normalize(), "f"),
                "premium": format(number(run.inputs["marketRiskPremium"]).normalize(), "f"),
            }
            if group in per_group and per_group[group] != basis:
                raise TaseError("TEMPORAL_V12_RATE_BASIS_CHANGED")
            per_group.setdefault(group, basis)
        else:
            basis = {
                "baselinePeriod": run.inputs["baselinePeriod"],
                "baselineRevision": run.inputs["baselineRevisionSha256"],
                "standardCostVintage": run.config["standardCostVintage"],
                "volumeBaseline": run.config["volumeBaseline"],
                "unit": run.inputs.get("quantityUnit"),
            }
            if group in per_group and per_group[group] != basis:
                raise TaseError("TEMPORAL_V12_PVM_BASELINE_CHANGED")
            per_group.setdefault(group, basis)
        result = engine.calculate(
            cap.model_code, cap.variant_code,
            run.inputs, run.config, reference_mode=True,
        )
        output = result.output.get(cap.output_field)
        if not isinstance(output, str):
            raise TaseError("TEMPORAL_MODEL_OUTPUT_TYPE_MISMATCH")
        number(output)
        if cap.strategy == "FIXED_BASELINE_LAST_SNAPSHOT":
            if result.output.get("currency") != request.currency:
                raise TaseError("TEMPORAL_MODEL_OUTPUT_CURRENCY_MISMATCH")
        kind = target[0]
        if cap.strategy == "DATED_FULL_WINDOW_REEXECUTE":
            source_value = run.inputs["cashflows"][0]["amount"]
        else:
            source_value = output
        observations.append(Observation(
            product=PRODUCT, metric=kind, scope=request.scope, start=run.start,
            end=None, value=source_value,
            unit="fraction" if kind == "MODEL_RATE" else request.currency,
            source_sha=result.output_sha256, dimensions=run.dimensions,
            observation_id=run.event_id,
        ))
        if cap.strategy == "EXPOSURE_WEIGHTED_MODEL_RATE":
            observations.append(Observation(
                product=PRODUCT, metric="EXPOSURE", scope=request.scope,
                start=run.start, end=None, value=run.exposure_weight,
                unit=request.currency, source_sha=result.output_sha256,
                dimensions=run.dimensions, observation_id=run.event_id,
            ))
        executed.append((run, result))
        receipts.append({
            "start": run.start, "eventId": run.event_id,
            "group": run.dimensions, "sourceSha": run.source_window_sha256,
            "inputsSha": result.inputs_sha256, "configSha": result.config_sha256,
            "outputSha": result.output_sha256,
        })
    ordered = sorted(receipts,key=lambda r:(r["start"],r["group"],r["eventId"]))
    batch_sha = fingerprint({
        "contract": "HC_TEMPORAL_V12_EXECUTED_BATCH_V1",
        "capabilitySha": cap.revision_sha256, "scope": request.scope,
        "sourceAndResultReceipts": ordered,
        # Completeness claims and watermark are part of the source evidence
        # identity, even if two requests happen to yield the same numeric value.
        "coverageEvidence": {
            "attested": request.coverage_attested,
            "watermark": request.watermark.isoformat()
            if request.watermark is not None else None,
            "requireFullCoverage": request.require_full_coverage,
        },
    })
    ds = Dataset(
        scope=request.scope, content_sha=batch_sha,
        rows=tuple(observations),
        complete_event_stream=request.coverage_attested,
        interval_coverage_attested=request.coverage_attested,
        watermark=request.watermark,
    )
    checked = calculate(catalog, period_req, ds)
    if cap.strategy == "DATED_FULL_WINDOW_REEXECUTE":
        periods = _buckets(period_req)
        bucket_rows, total_rows = _reexecute_xnpv(
            cap, request, executed, periods, engine,
        )
        result_digest = fingerprint({
            "contract": "HC_TEMPORAL_V12_XNPV_RERUN_V1",
            "validatedTaseResult": checked.result_sha,
            "buckets": [{"group": r.group,"start":r.start,"end":r.end,
                         "value":r.value} for r in bucket_rows],
            "totals": [{"group": r.group,"start":r.start,"end":r.end,
                        "value":r.value} for r in total_rows],
        })
        output_result = TaseResult(
            checked.plan_sha, checked.dataset_sha,
            bucket_rows, result_digest, status=checked.status,
            total_rows=total_rows,
        )
    else:
        output_result = checked
    plan_sha = fingerprint({
        "contract": SCHEMA, "capability": cap.revision_sha256,
        "tasePlan": tase_plan.plan_sha, "batch": batch_sha,
        "modelRevision": IMPLEMENTATION_REVISION,
    })
    result_sha = fingerprint({
        "contract": "HC_TEMPORAL_V12_RESULT_V1",
        "plan": plan_sha, "typedResult": output_result.result_sha,
    })
    return ModelTemporalResult(
        cap.revision_sha256, batch_sha, plan_sha, result_sha,
        output_result, tuple(r["outputSha"] for r in ordered),
    )
