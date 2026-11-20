"""ModelTemporalCapabilityV1: one typed TASE adapter for compatible HC outputs.

This is a bounded, synchronous Python reference. A capability descriptor only
admits a specific model / variant / output FIELD and temporal reducer. It does
NOT confer financial S2, prove the FIN source authority, persist customer data,
or allow arbitrary HC-model output aggregation.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from fengine_hc.reference import (
    CalculationError, ContractRegistry, ReferenceEngine, fingerprint, number,
)
from tase.reference import (
    Catalog, Dataset, Metric, Observation, PeriodRequest, ProductPack,
    TaseError, TaseResult, calculate, compile_plan,
)

SCHEMA = "FENGINE_MODEL_TEMPORAL_CAPABILITY_V1"
REFERENCE_PRODUCT = "HC_TEMPORAL_REFERENCE"
CAPABILITY_STATUS = "PYTHON_REFERENCE_NOT_S2"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CURRENCY = re.compile(r"[A-Z]{3}\Z")
FLOW_GRAINS = frozenset(("DAY", "ISO_WEEK", "MONTH", "QUARTER",
                         "HALF_YEAR", "YEAR", "FISCAL_PERIOD",
                         "FISCAL_QUARTER", "FISCAL_HALF_YEAR", "FISCAL_YEAR"))
BINDINGS = frozenset((
    "START_END_INCLUSIVE",
    "PERIOD_START_ASOF_INCLUSIVE",
    "ASOF_INCLUSIVE_SOURCE_EVIDENCE_REQUIRED",
    "ASOF_SNAPSHOT",
))
COLUMNS = (
    "modelCode", "variantCode", "outputField", "quantityKind", "timeKind",
    "temporalReducer", "sourceGrains", "outputGrains", "periodBinding",
    "unitKind", "reviewStatus",
)


def _datestring(value: Any) -> str:
    if not isinstance(value, str):
        raise TaseError("TEMPORAL_MODEL_DATE_REQUIRED")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise TaseError("TEMPORAL_MODEL_DATE_REQUIRED") from exc
    if parsed.isoformat() != value:
        raise TaseError("TEMPORAL_MODEL_DATE_NONCANONICAL")
    return value


def _sha(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise TaseError(code)
    return value


def _date(value: Any) -> date:
    if type(value) is not date:
        raise TaseError("TEMPORAL_MODEL_DATE_REQUIRED")
    return value


def _csv_set(value: str) -> frozenset[str]:
    parts = value.split(",")
    if any(not part or part != part.strip() for part in parts) or len(parts) != len(set(parts)):
        raise TaseError("TEMPORAL_CAPABILITY_INVALID_GRAINS")
    return frozenset(parts)


@dataclass(frozen=True)
class ModelTemporalCapabilityV1:
    model_code: str
    variant_code: str
    output_field: str
    quantity_kind: str
    time_kind: str
    reducer: str
    source_grains: frozenset[str]
    output_grains: frozenset[str]
    period_binding: str
    unit_kind: str
    review_status: str
    capability_sha256: str


class ModelTemporalRegistry:
    """Declarations checked against the actual 116 / 222 model catalogue."""

    def __init__(self, root: Path, definitions: Mapping[tuple[str, str, str],
                 ModelTemporalCapabilityV1], *, reference_mode: bool) -> None:
        self.root = Path(root)
        self._definitions = dict(definitions)
        self.reference_mode = reference_mode

    @property
    def capabilities(self) -> Mapping[tuple[str, str, str], ModelTemporalCapabilityV1]:
        # Don't expose mutable registry state.
        from types import MappingProxyType
        return MappingProxyType(self._definitions)

    @classmethod
    def load(cls, root: Path, *, reference_mode: bool = False,
             path: Path | None = None) -> "ModelTemporalRegistry":
        if not reference_mode:
            raise TaseError("FINANCIAL_S2_REQUIRED")
        root = Path(root)
        contracts = ContractRegistry(root)
        filename = path or root / "catalog" / "model_temporal_capabilities_v1.tsv"
        with Path(filename).open(encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp, delimiter="\t")
            if reader.fieldnames != list(COLUMNS):
                raise TaseError("TEMPORAL_CAPABILITY_SCHEMA_MISMATCH")
            records = list(reader)
        if not records:
            raise TaseError("TEMPORAL_CAPABILITY_EMPTY")
        definitions = {}
        for row in records:
            if None in row or any(not isinstance(v, str) or not v for v in row.values()):
                raise TaseError("TEMPORAL_CAPABILITY_SCHEMA_MISMATCH")
            model, variant, field = row["modelCode"], row["variantCode"], row["outputField"]
            key = (model, variant, field)
            if key in definitions:
                raise TaseError("TEMPORAL_CAPABILITY_DUPLICATE")
            if (model, variant) not in contracts.variants:
                raise TaseError("TEMPORAL_CAPABILITY_UNKNOWN_VARIANT")
            if row["reviewStatus"] != CAPABILITY_STATUS:
                raise TaseError("TEMPORAL_CAPABILITY_UNREVIEWED")
            kind, temporal, reducer = (row[k] for k in (
                "quantityKind", "timeKind", "temporalReducer"))
            allowed = (
                ("FLOW", "INTERVAL_FLOW", "SUM", "START_END_INCLUSIVE"),
                ("FLOW", "INTERVAL_FLOW", "SUM", "PERIOD_START_ASOF_INCLUSIVE"),
                ("FLOW", "INTERVAL_FLOW", "SUM", "ASOF_INCLUSIVE_SOURCE_EVIDENCE_REQUIRED"),
                ("STOCK", "AS_OF", "LAST_AS_OF", "ASOF_SNAPSHOT"),
            )
            if (kind, temporal, reducer, row["periodBinding"]) not in allowed:
                raise TaseError("TEMPORAL_CAPABILITY_UNSAFE_REDUCER")
            sources, outputs = _csv_set(row["sourceGrains"]), _csv_set(row["outputGrains"])
            if not sources or not outputs or not outputs <= FLOW_GRAINS:
                raise TaseError("TEMPORAL_CAPABILITY_INVALID_GRAINS")
            if kind == "FLOW" and not sources <= FLOW_GRAINS:
                raise TaseError("TEMPORAL_CAPABILITY_INVALID_GRAINS")
            if kind == "STOCK" and sources != {"AS_OF"}:
                raise TaseError("TEMPORAL_CAPABILITY_INVALID_GRAINS")
            if row["unitKind"] != "CURRENCY":
                raise TaseError("TEMPORAL_CAPABILITY_UNIT_UNSUPPORTED")
            manifest = {k: row[k] for k in COLUMNS}
            descriptor = ModelTemporalCapabilityV1(
                model_code=model, variant_code=variant, output_field=field,
                quantity_kind=kind, time_kind=temporal, reducer=reducer,
                source_grains=sources, output_grains=outputs,
                period_binding=row["periodBinding"],
                unit_kind=row["unitKind"], review_status=row["reviewStatus"],
                capability_sha256=fingerprint({"schema": SCHEMA, "record": manifest}),
            )
            definitions[key] = descriptor
        return cls(root, definitions, reference_mode=True)

    def resolve(self, model: str, variant: str, output_field: str,
                *, source_grain: str, output_grain: str) -> ModelTemporalCapabilityV1:
        if not self.reference_mode:
            raise TaseError("FINANCIAL_S2_REQUIRED")
        capability = self._definitions.get((model, variant, output_field))
        if capability is None:
            raise TaseError("TEMPORAL_CAPABILITY_NOT_ADMITTED")
        if source_grain not in capability.source_grains:
            raise TaseError("TEMPORAL_SOURCE_GRAIN_NOT_ALLOWED")
        if output_grain not in capability.output_grains:
            raise TaseError("TEMPORAL_OUTPUT_GRAIN_NOT_ALLOWED")
        return capability


@dataclass(frozen=True)
class ModelTemporalRequest:
    model_code: str
    variant_code: str
    output_field: str
    scope: str
    start: date
    end: date
    source_grain: str
    output_grain: str
    currency: str
    include_total: bool = True
    group_by: tuple[str, ...] = ()
    coverage_attested: bool = False
    watermark: date | None = None
    max_snapshot_age_days: int = 31
    fiscal_start_month: int = 1
    require_full_coverage: bool = True

    def __post_init__(self) -> None:
        _date(self.start)
        _date(self.end)
        if self.start >= self.end:
            raise TaseError("INVALID_REQUEST_INTERVAL")
        if not isinstance(self.scope, str) or not self.scope:
            raise TaseError("SCOPE_REQUIRED")
        if not isinstance(self.currency, str) or CURRENCY.fullmatch(self.currency) is None:
            raise TaseError("TEMPORAL_CURRENCY_INVALID")
        if not isinstance(self.include_total, bool):
            raise TaseError("INVALID_INCLUDE_TOTAL")
        if not isinstance(self.coverage_attested, bool):
            raise TaseError("INVALID_COVERAGE_ATTESTATION")
        if len(set(self.group_by)) != len(self.group_by):
            raise TaseError("DUPLICATE_GROUP_KEY")
        if not isinstance(self.require_full_coverage, bool):
            raise TaseError("INVALID_REQUIRE_FULL_COVERAGE")
        if self.watermark is not None:
            _date(self.watermark)
        if not 1 <= self.fiscal_start_month <= 12:
            raise TaseError("INVALID_FISCAL_START")
        if (type(self.max_snapshot_age_days) is not int
                or self.max_snapshot_age_days < 0):
            raise TaseError("INVALID_STALENESS")


@dataclass(frozen=True)
class ModelTemporalRun:
    """One independently executed, source-versioned model for a precise window.

    For AS_OF snapshots end is None, start is the snapshot date.
    source_window_sha256 must match the model's actual source/baseline revision.
    This does not prove the *authority* of its issuer.
    """
    start: date
    end: date | None
    inputs: Mapping[str, Any]
    config: Mapping[str, Any]
    source_window_sha256: str
    dimensions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ModelTemporalResult:
    capability_sha256: str
    source_batch_sha256: str
    plan_sha256: str
    result_sha256: str
    result: TaseResult
    source_output_shas: tuple[str, ...]
    execution_class: str = "PYTHON_REFERENCE_NOT_S2"


def _bind_run(cap: ModelTemporalCapabilityV1, run: ModelTemporalRun,
              req: ModelTemporalRequest) -> None:
    _date(run.start)
    if not isinstance(run.inputs, Mapping) or not isinstance(run.config, Mapping):
        raise TaseError("TEMPORAL_MODEL_INPUT_REQUIRED")
    if (not isinstance(run.dimensions, tuple)
            or run.dimensions != tuple(sorted(run.dimensions))
            or len(run.dimensions) != len({k for k, _ in run.dimensions})):
        raise TaseError("TEMPORAL_MODEL_DIMENSIONS_INVALID")
    _sha(run.source_window_sha256, "TEMPORAL_MODEL_SOURCE_SHA_REQUIRED")
    model_source = (run.inputs.get("sourceRevisionSha256")
                    if cap.time_kind == "INTERVAL_FLOW"
                    else run.inputs.get("baselineRevision"))
    if model_source != run.source_window_sha256:
        raise TaseError("TEMPORAL_MODEL_SOURCE_REVISION_MISMATCH")
    if run.inputs.get("currency") != req.currency:
        raise TaseError("TEMPORAL_MODEL_CURRENCY_MISMATCH")
    if cap.time_kind == "AS_OF":
        if run.end is not None or not req.start <= run.start < req.end:
            raise TaseError("TEMPORAL_MODEL_SNAPSHOT_BOUNDS")
        if _datestring(run.inputs.get("asOf")) != run.start.isoformat():
            raise TaseError("TEMPORAL_MODEL_SNAPSHOT_DATE_MISMATCH")
        return
    if run.end is None:
        raise TaseError("TEMPORAL_MODEL_END_REQUIRED")
    _date(run.end)
    if not req.start <= run.start < run.end <= req.end:
        raise TaseError("TEMPORAL_MODEL_WINDOW_OUTSIDE_REQUEST")
    inclusive_end = (run.end - timedelta(days=1)).isoformat()
    if cap.period_binding == "START_END_INCLUSIVE":
        if (_datestring(run.inputs.get("periodStart")) != run.start.isoformat()
                or _datestring(run.inputs.get("periodEnd")) != inclusive_end):
            raise TaseError("TEMPORAL_MODEL_WINDOW_BINDING_MISMATCH")
    elif cap.period_binding == "PERIOD_START_ASOF_INCLUSIVE":
        if (_datestring(run.inputs.get("periodStart")) != run.start.isoformat()
                or _datestring(run.inputs.get("asOf")) != inclusive_end):
            raise TaseError("TEMPORAL_MODEL_WINDOW_BINDING_MISMATCH")
    elif cap.period_binding == "ASOF_INCLUSIVE_SOURCE_EVIDENCE_REQUIRED":
        # Model inputs have only asOf, not a start date. This is an in-process
        # UAT adapter and requires upstream explicit source coverage evidence.
        if not req.coverage_attested:
            raise TaseError("TEMPORAL_MODEL_UNATTESTED_INTERVAL_SOURCE")
        if _datestring(run.inputs.get("asOf")) != inclusive_end:
            raise TaseError("TEMPORAL_MODEL_WINDOW_BINDING_MISMATCH")
    else:
        raise TaseError("TEMPORAL_CAPABILITY_UNSAFE_REDUCER")


def calculate_model_temporal(
    registry: ModelTemporalRegistry,
    request: ModelTemporalRequest,
    runs: Sequence[ModelTemporalRun],
    *, reference_mode: bool = False,
) -> ModelTemporalResult:
    """Use actual ReferenceEngine outputs; reuse TASE for dates, totals and gaps.

    No original input amounts are returned. All input/output structures remain
    in this process only; no Redis implementation, retention ACK or database.
    """
    if not reference_mode:
        raise TaseError("FINANCIAL_S2_REQUIRED")
    cap = registry.resolve(
        request.model_code, request.variant_code, request.output_field,
        source_grain=request.source_grain, output_grain=request.output_grain,
    )
    if not isinstance(runs, (tuple, list)) or not 1 <= len(runs) <= 10000:
        raise TaseError("TEMPORAL_MODEL_RUN_BUDGET")
    base = Catalog.load(registry.root, reference_mode=True)
    metric_code = ":".join((cap.model_code, cap.variant_code, cap.output_field))
    money = Metric(
        REFERENCE_PRODUCT, metric_code, "MONEY", request.currency,
        cap.quantity_kind, cap.time_kind,
        cap.reducer, frozenset((cap.reducer,)),
        "", "", CAPABILITY_STATUS,
    )
    product = ProductPack(
        REFERENCE_PRODUCT, "HC_TEMPORAL_REFERENCE_V1",
        cap.output_grains, frozenset((cap.reducer,)), CAPABILITY_STATUS,
    )
    catalog = Catalog(
        {**base.products, REFERENCE_PRODUCT: product},
        {**base.metrics, (REFERENCE_PRODUCT, metric_code): money},
        base.operators, base.predicates, reference_mode=True,
    )
    period = PeriodRequest(
        product=REFERENCE_PRODUCT, metric=metric_code,
        operation=cap.reducer, scope=request.scope,
        start=request.start, end=request.end, grain=request.output_grain,
        group_by=request.group_by, fiscal_start_month=request.fiscal_start_month,
        require_full_coverage=request.require_full_coverage,
        max_snapshot_age_days=request.max_snapshot_age_days,
        source_grain=request.source_grain, include_total=request.include_total,
    )
    # Refuse structurally invalid requests BEFORE any underlying model run.
    typed_plan = compile_plan(catalog, period)
    engine = ReferenceEngine(registry.root)
    observations = []
    source_receipts = []
    for run in runs:
        _bind_run(cap, run, request)
        receipt = engine.calculate(
            request.model_code, request.variant_code, run.inputs, run.config,
            reference_mode=True,
        )
        if cap.output_field not in receipt.output:
            raise TaseError("TEMPORAL_MODEL_OUTPUT_FIELD_MISSING")
        output = receipt.output[cap.output_field]
        if not isinstance(output, str):
            raise TaseError("TEMPORAL_MODEL_OUTPUT_TYPE_MISMATCH")
        number(output)
        if receipt.output.get("currency") != request.currency:
            raise TaseError("TEMPORAL_MODEL_OUTPUT_CURRENCY_MISMATCH")
        observations.append(Observation(
            product=REFERENCE_PRODUCT, metric=metric_code,
            scope=request.scope, start=run.start, end=run.end,
            value=output, unit=request.currency,
            source_sha=receipt.output_sha256,
            dimensions=run.dimensions,
        ))
        source_receipts.append({
            "window": [run.start.isoformat(),
                       run.end.isoformat() if run.end is not None else None],
            "dimensions": list(run.dimensions),
            "sourceWindowSha256": run.source_window_sha256,
            "inputsSha256": receipt.inputs_sha256,
            "configSha256": receipt.config_sha256,
            "outputSha256": receipt.output_sha256,
        })
    ordered = sorted(source_receipts, key=lambda item: (
        item["window"][0], item["window"][1] or "", item["dimensions"],
        item["outputSha256"],
    ))
    dataset_sha = fingerprint({
        "contract": "HC_MODEL_TEMPORAL_EXECUTED_BATCH_V1",
        "capabilitySha256": cap.capability_sha256,
        "scope": request.scope,
        "receipts": ordered,
    })
    dataset = Dataset(
        scope=request.scope, content_sha=dataset_sha, rows=tuple(observations),
        interval_coverage_attested=request.coverage_attested,
        watermark=request.watermark,
    )
    aggregates = calculate(catalog, period, dataset)
    plan_sha = fingerprint({
        "contract": SCHEMA,
        "capabilitySha256": cap.capability_sha256,
        "tasePlanSha256": typed_plan.plan_sha,
        "sourceBatchSha256": dataset_sha,
        "referenceEngineRevision": "PY_HC_REFERENCE_R0_7A",
    })
    response_sha = fingerprint({
        "modelTemporalPlanSha256": plan_sha,
        "taseResultSha256": aggregates.result_sha,
    })
    return ModelTemporalResult(
        capability_sha256=cap.capability_sha256,
        source_batch_sha256=dataset_sha,
        plan_sha256=plan_sha,
        result_sha256=response_sha,
        result=aggregates,
        source_output_shas=tuple(r["outputSha256"] for r in ordered),
    )
