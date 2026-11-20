"""HC-R0.7 — nontrivial true three-factor Price/Total-Volume/Mix cost bridge.

Sequential reference convention:
- Volume holds baseline proportions and baseline unit costs.
- Mix changes shares at actual total quantity, holding baseline unit costs.
- Price changes unit costs at actual product quantities.
Every original SKU must carry an actual quantity (possibly zero) and a
strictly positive baseline quantity/cost revision; new SKU attribution is
blocked pending a separately qualified baseline policy. No persistence.
"""
from __future__ import annotations

import re
from decimal import Decimal, localcontext
from typing import Any, Mapping

from .reference import CalculationError, day, fingerprint, number

ZERO = Decimal(0)
SHA = re.compile(r"[0-9a-f]{64}\Z")
SKU = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
UNIT = re.compile(r"[A-Z][A-Z0-9_]{0,15}\Z")
FOCUS = {
    "PRICE_VARIANCE": "PRICE",
    "QUANTITY_VARIANCE": "TOTAL_VOLUME",
    "MIX_VARIANCE": "MIX",
}
CONVENTION = "SEQUENTIAL_BASELINE_MIX_ACTUAL_QUANTITY_PRICE"


def _fields(value: Any, required: set[str], error: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != required:
        raise CalculationError(error)
    return value


def _date(value: Any) -> str:
    d = day(value)
    if not isinstance(value, str) or value != d.isoformat():
        raise CalculationError("PVM_NONCANONICAL_DATE")
    return value


def _sha(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA.fullmatch(value) is None:
        raise CalculationError(code)
    return value


def _fmt(v: Decimal) -> str:
    return format(+v, "f")


def _parse_rows(value: Any) -> tuple[tuple[str, Decimal, Decimal, Decimal, Decimal], ...]:
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 500:
        raise CalculationError("PVM_PRODUCT_UNIVERSE_REQUIRED")
    parsed = []
    used = set()
    for row in value:
        r = _fields(row, {"sku", "baselineQuantity", "actualQuantity",
                          "baselineUnitCost", "actualUnitCost"}, "PVM_ROW_SCHEMA")
        sku = r["sku"]
        if not isinstance(sku, str) or SKU.fullmatch(sku) is None:
            raise CalculationError("PVM_SKU_INVALID")
        if sku in used:
            raise CalculationError("PVM_DUPLICATE_SKU")
        used.add(sku)
        q0, q1, p0, p1 = (number(r[k]) for k in (
            "baselineQuantity", "actualQuantity", "baselineUnitCost", "actualUnitCost"
        ))
        if q0 <= ZERO:
            raise CalculationError("PVM_NEW_OR_ZERO_BASE_SKU_REQUIRES_POLICY", sku)
        if min(q1, p0, p1) < ZERO:
            raise CalculationError("PVM_NEGATIVE_QUANTITY_OR_COST")
        parsed.append((sku, q0, q1, p0, p1))
    return tuple(sorted(parsed, key=lambda line: line[0]))


def pvm_revision_hashes(baseline_period: Any, actual_period: Any,
                        currency: Any, quantity_unit: Any, rows: Any) -> dict[str, str]:
    """Reconstruct four normalized, content-addressed evidence revisions.

    Hashes guarantee self-consistency only. Signed facts, contract provenance
    and independent standard-cost qualification are separate S2 questions.
    """
    start, end = _date(baseline_period), _date(actual_period)
    if start >= end:
        raise CalculationError("PVM_BASELINE_MUST_PRECEDE_ACTUAL")
    if not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None:
        raise CalculationError("PVM_CURRENCY_REQUIRED")
    if not isinstance(quantity_unit, str) or UNIT.fullmatch(quantity_unit) is None:
        raise CalculationError("PVM_QUANTITY_UNIT_REQUIRED")
    data = _parse_rows(rows)
    baseline_lines = [
        {"sku": sku, "quantity": _fmt(q0), "unitCost": _fmt(p0)}
        for sku, q0, _, p0, _ in data
    ]
    actual_lines = [
        {"sku": sku, "quantity": _fmt(q1), "unitCost": _fmt(p1)}
        for sku, _, q1, _, p1 in data
    ]
    root = {"currency": currency, "quantityUnit": quantity_unit}
    return {
        "baselineRevisionSha256": fingerprint({
            "contract": "HC_R07_BASELINE_COST_QUANTITY_V1",
            "period": start, **root, "lines": baseline_lines,
        }),
        "actualRevisionSha256": fingerprint({
            "contract": "HC_R07_ACTUAL_COST_QUANTITY_V1",
            "period": end, **root, "lines": actual_lines,
        }),
        "standardCostVintage": fingerprint({
            "contract": "HC_R07_BASE_STANDARD_UNIT_COST_V1",
            "period": start, **root,
            "lines": [{"sku": r["sku"], "unitCost": r["unitCost"]} for r in baseline_lines],
        }),
        "volumeBaseline": fingerprint({
            "contract": "HC_R07_BASELINE_SKU_QUANTITY_V1",
            "period": start, **root,
            "lines": [{"sku": r["sku"], "quantity": r["quantity"]} for r in baseline_lines],
        }),
    }


def price_volume_mix(inputs: Mapping[str, Any], config: Mapping[str, Any],
                     variant: str) -> dict[str, Any]:
    if variant not in FOCUS:
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
    _fields(inputs, {"baselinePeriod", "actualPeriod", "currency", "quantityUnit",
                     "rows", "baselineRevisionSha256", "actualRevisionSha256"},
            "PVM_INPUT_SCHEMA")
    if config["interactionAllocation"] != CONVENTION:
        raise CalculationError("PVM_ALLOCATION_POLICY_NOT_SUPPORTED")
    digests = pvm_revision_hashes(
        inputs["baselinePeriod"], inputs["actualPeriod"],
        inputs["currency"], inputs["quantityUnit"], inputs["rows"]
    )
    if (inputs["baselineRevisionSha256"] != digests["baselineRevisionSha256"]
            or inputs["actualRevisionSha256"] != digests["actualRevisionSha256"]):
        raise CalculationError("PVM_SOURCE_DIGEST_MISMATCH")
    if config["standardCostVintage"] != digests["standardCostVintage"]:
        raise CalculationError("PVM_STANDARD_COST_REVISION_MISMATCH")
    if config["volumeBaseline"] != digests["volumeBaseline"]:
        raise CalculationError("PVM_VOLUME_BASELINE_REVISION_MISMATCH")

    data = _parse_rows(inputs["rows"])
    with localcontext() as ctx:
        ctx.prec = 50
        q0 = sum((a for _, a, _, _, _ in data), ZERO)
        q1 = sum((a for _, _, a, _, _ in data), ZERO)
        if q0 <= ZERO or q1 <= ZERO:
            raise CalculationError("PVM_TOTAL_VOLUME_UNDEFINED")
        base_cost = sum((bq * bc for _, bq, _, bc, _ in data), ZERO)
        current_cost_at_base_prices = sum((aq * bc for _, _, aq, bc, _ in data), ZERO)
        actual_cost = sum((aq * ac for _, _, aq, _, ac in data), ZERO)
        # Q0>0, so the baseline weighted unit cost is defined.
        baseline_weight = base_cost / q0
        volume = (q1 - q0) * baseline_weight
        price = actual_cost - current_cost_at_base_prices
        mix = (current_cost_at_base_prices - base_cost) - volume
        delta = actual_cost - base_cost
        residual = delta - (volume + mix + price)
        allowed_residual = Decimal("1e-38") * max(
            Decimal(1), abs(delta), abs(base_cost), abs(actual_cost)
        )
        if abs(residual) > allowed_residual:
            raise CalculationError("PVM_DECIMAL_RECONCILIATION_FAILED")
        selected = {"PRICE": price, "TOTAL_VOLUME": volume, "MIX": mix}[FOCUS[variant]]
        return {
            "baselinePeriod": inputs["baselinePeriod"],
            "actualPeriod": inputs["actualPeriod"],
            "currency": inputs["currency"], "quantityUnit": inputs["quantityUnit"],
            "baselineRevisionSha256": inputs["baselineRevisionSha256"],
            "actualRevisionSha256": inputs["actualRevisionSha256"],
            "standardCostVintage": config["standardCostVintage"],
            "volumeBaseline": config["volumeBaseline"],
            "baselineQuantity": _fmt(q0), "actualQuantity": _fmt(q1),
            "baselineWeightedUnitCost": _fmt(baseline_weight),
            "baselineTotalCost": _fmt(base_cost),
            "actualTotalCost": _fmt(actual_cost),
            "baselineUnitCostAtActualQuantities": _fmt(current_cost_at_base_prices),
            "totalCostVariance": _fmt(delta),
            "priceVariance": _fmt(price),
            "quantityVariance": _fmt(volume),
            "mixVariance": _fmt(mix),
            "reconciliationDifference": _fmt(residual),
            "selectedFactor": FOCUS[variant],
            "selectedVariance": _fmt(selected),
            "costSignConvention": "POSITIVE_COST_INCREASE_ADVERSE",
            "allocation": CONVENTION,
            "classification": "THREE_FACTOR_COST_REFERENCE_NOT_FINANCIAL_S2",
        }
