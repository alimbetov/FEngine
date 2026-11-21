"""QUAL-R1.6 strict synthetic admitted execution facade.

Legacy ReferenceEngine remains a non-admitted research API for existing tests.
QualifiedReferenceEngine.calculate always validates source metadata and bound
payloads before calling that numerical implementation. No FIN/Rust/Redis/S2.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from .reference import CalculationError, ReferenceEngine, fingerprint
from .source_context_r15 import SourceContext, execute_guarded, validate_contexts, _source_shape


@dataclass(frozen=True)
class AdmissionPolicy:
    model: str
    roles: frozenset[str]
    period_mode: str
    sku_mode: str


# Explicit model allowlist. One exact input payload is the provisional
# contract for models without qualified multi-role source semantics.
# PVM uses independently bound BASELINE and ACTUAL payloads.
_MODELS = frozenset({
    "HC.ASSET.01", "HC.CAP.01", "HC.CAP.02", "HC.CASH.03",
    "HC.CASH.04", "HC.CASH.05", "HC.COST.04", "HC.COST.05",
    "HC.COST.07", "HC.COST.08", "HC.DCF.01", "HC.DCF.02",
    "HC.DCF.03", "HC.DCF.05", "HC.DCF.06", "HC.DCF.07",
    "HC.DCF.08", "HC.ECL.02", "HC.ECL.03", "HC.LOAN.02",
    "HC.LOAN.03", "HC.PF.01", "HC.RISK.02", "HC.RISK.03",
    "HC.SET.03", "HC.STOCK.01", "HC.STOCK.02",
})
POLICIES = {
    model: AdmissionPolicy(
        model=model,
        roles=frozenset({"BASELINE", "ACTUAL"}) if model == "HC.COST.08" else frozenset({"INPUT"}),
        period_mode="BASELINE_BEFORE_ACTUAL" if model == "HC.COST.08" else "EXACT",
        sku_mode="SINGLE" if model.startswith("HC.STOCK.") else (
            "PVM_EQUAL_UNIVERSE" if model == "HC.COST.08" else "EXACT"),
    )
    for model in _MODELS
}


def _pvm_check(sources: Sequence[SourceContext], payloads: Mapping[str, Any],
               inputs: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    from .r07_pvm import pvm_revision_hashes

    if not isinstance(sources, (tuple, list)) or len(sources) != 2:
        raise CalculationError("SOURCE_ROLE_MISMATCH")
    for s in sources:
        _source_shape(s)
    roles = {s.role: s for s in sources}
    if len(roles) != 2 or set(roles) != {"BASELINE", "ACTUAL"}:
        raise CalculationError("SOURCE_ROLE_MISMATCH")
    b, a = roles["BASELINE"], roles["ACTUAL"]
    if b.source_id == a.source_id:
        raise CalculationError("DUPLICATE_SOURCE_ID")
    if (b.user_id, b.project_id) != (a.user_id, a.project_id):
        raise CalculationError("CROSS_SCOPE_DATASET")
    if b.currency != a.currency:
        raise CalculationError("CROSS_CURRENCY_DATASET")
    if b.period_type != a.period_type:
        raise CalculationError("CROSS_PERIOD_DATASET")
    if date.fromisoformat(b.period_end) >= date.fromisoformat(a.period_start):
        raise CalculationError("PVM_PERIOD_ORDER_MISMATCH")
    if b.sku_set != a.sku_set:
        raise CalculationError("CROSS_SKU_DATASET")
    if (b.methodology_id, b.methodology_version, b.methodology_sha256) != (
        a.methodology_id, a.methodology_version, a.methodology_sha256
    ) or b.methodology_id != "HC.COST.08":
        raise CalculationError("CROSS_METHODOLOGY_DATASET")
    if not isinstance(payloads, Mapping) or set(payloads) != {"BASELINE", "ACTUAL"}:
        raise CalculationError("SOURCE_PAYLOAD_ROLES")
    for s in (b, a):
        if fingerprint(payloads[s.role]) != s.payload_sha256:
            raise CalculationError("SOURCE_PAYLOAD_DIGEST_MISMATCH")
    if not isinstance(inputs, Mapping) or not isinstance(config, Mapping):
        raise CalculationError("INVALID_REQUEST")
    if inputs.get("currency") != b.currency or inputs.get("baselinePeriod") != b.period_end or inputs.get("actualPeriod") != a.period_end:
        raise CalculationError("PVM_CONTEXT_INPUT_MISMATCH")
    if set(inputs) != {
        "baselinePeriod", "actualPeriod", "currency", "quantityUnit", "rows",
        "baselineRevisionSha256", "actualRevisionSha256",
    }:
        raise CalculationError("PVM_CONTEXT_INPUT_MISMATCH")
    baseline, actual = payloads["BASELINE"], payloads["ACTUAL"]
    if not isinstance(baseline, Mapping) or not isinstance(actual, Mapping) or (
        set(baseline) != {"rows"} or set(actual) != {"rows"}
    ):
        raise CalculationError("PVM_SOURCE_ROW_SCHEMA")
    def indexed(value: Any) -> dict[str, Mapping[str, Any]]:
        rows = value["rows"]
        if not isinstance(rows, (list, tuple)) or not rows:
            raise CalculationError("PVM_SOURCE_ROW_SCHEMA")
        out = {}
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != {"sku", "quantity", "unitCost"}:
                raise CalculationError("PVM_SOURCE_ROW_SCHEMA")
            sku = row["sku"]
            if not isinstance(sku, str) or sku in out:
                raise CalculationError("PVM_SOURCE_ROW_SCHEMA")
            out[sku] = row
        return out
    base_rows, actual_rows = indexed(baseline), indexed(actual)
    if set(base_rows) != set(b.sku_set) or set(actual_rows) != set(a.sku_set):
        raise CalculationError("PVM_SOURCE_SKU_MISMATCH")
    reconstructed = [{
        "sku": sku,
        "baselineQuantity": base_rows[sku]["quantity"],
        "baselineUnitCost": base_rows[sku]["unitCost"],
        "actualQuantity": actual_rows[sku]["quantity"],
        "actualUnitCost": actual_rows[sku]["unitCost"],
    } for sku in b.sku_set]
    if fingerprint(reconstructed) != fingerprint(sorted(inputs["rows"], key=lambda r: r["sku"])):
        raise CalculationError("PVM_SOURCE_INPUT_MISMATCH")
    evidence = pvm_revision_hashes(
        b.period_end, a.period_end, b.currency, inputs["quantityUnit"], reconstructed,
    )
    for key in ("baselineRevisionSha256", "actualRevisionSha256"):
        if inputs.get(key) != evidence[key]:
            raise CalculationError("PVM_SOURCE_INPUT_MISMATCH")
    for key in ("standardCostVintage", "volumeBaseline"):
        if config.get(key) != evidence[key]:
            raise CalculationError("PVM_SOURCE_INPUT_MISMATCH")
    return fingerprint({
        "policy": "QUAL-R1.6:PVM:V1",
        "baseline": vars(b), "actual": vars(a),
        "payloads": {"BASELINE": b.payload_sha256, "ACTUAL": a.payload_sha256},
    })


class QualifiedReferenceEngine:
    """Non-bypassable context gate for THIS facade, never production S2."""

    def __init__(self, root: Path):
        self._reference = ReferenceEngine(root)

    def calculate(self, model: str, variant: str, inputs: Mapping[str, Any],
                  config: Mapping[str, Any], *,
                  sources: Sequence[SourceContext] | None = None,
                  payloads_by_role: Mapping[str, Any] | None = None,
                  reference_mode: bool = False):
        if not reference_mode:
            raise CalculationError("FINANCIAL_S2_REQUIRED")
        policy = POLICIES.get(model)
        if policy is None:
            raise CalculationError("CONTEXT_POLICY_NOT_APPROVED")
        if (model, variant) not in self._reference.registry.variants:
            raise CalculationError("UNKNOWN_VARIANT")
        if sources is None or payloads_by_role is None:
            raise CalculationError("CONTEXT_ADMISSION_REQUIRED")
        if policy.period_mode == "BASELINE_BEFORE_ACTUAL":
            receipt = _pvm_check(sources, payloads_by_role, inputs, config)
        else:
            receipt, _ = execute_guarded(
                sources, payloads_by_role, required_roles=policy.roles,
                single_sku=policy.sku_mode == "SINGLE",
                executor=lambda payloads: None,
            )
            if len(sources) != 1 or sources[0].methodology_id != model:
                raise CalculationError("METHODOLOGY_MODEL_MISMATCH")
            if fingerprint(payloads_by_role["INPUT"]) != fingerprint(inputs):
                raise CalculationError("SOURCE_INPUT_MISMATCH")
        result = self._reference.calculate(model, variant, inputs, config, reference_mode=True)
        # The legacy numerical result hash does not include admission receipt.
        # Keep it unchanged to avoid falsely asserting S2; return both receipts.
        return AdmittedResult(result=result, admission_sha256=receipt)


@dataclass(frozen=True)
class AdmittedResult:
    result: Any
    admission_sha256: str
