"""HC-R0.6 — two independently derived FCFE mathematical reference methods.

No user-data persistence, method S2, approval of source bookkeeping, tax
benefit modelling, or rate-curve interpolation. Input source and rate digests
provide local integrity, not external financial authentication.
"""
from __future__ import annotations

import re
from decimal import Decimal, localcontext
from typing import Any, Mapping

from .reference import CalculationError, day, fingerprint, integer, number

ZERO, ONE = Decimal(0), Decimal(1)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CURRENCY = re.compile(r"[A-Z]{3}\Z")

POLICY = {
    "debtFlowPolicy": "GROSS_DRAWDOWN_LESS_PRINCIPAL",
    "cashflowToEquityPolicy": "NO_INTEREST_READD",
    "netBorrowingMethod": "DRAWDOWNS_MINUS_PRINCIPAL_REPAYMENTS",
    "taxShieldEligibility": "NO_EXTRA_TAX_SHIELD",
}
BASIS = {
    "FCFE_LEVERED": "POST_INTEREST_OPERATING_CFO",
    "FCFE_NORMALIZED": "POST_INTEREST_NET_INCOME_BRIDGE",
}


def _fields(value: Any, fields: set[str], error: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise CalculationError(error)
    return value


def _sha(value: Any, error: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise CalculationError(error)
    return value


def _date(value: Any) -> str:
    d = day(value)
    if not isinstance(value, str) or d.isoformat() != value:
        raise CalculationError("FCFE_NONCANONICAL_DATE")
    return value


def _currency(value: Any) -> str:
    if not isinstance(value, str) or CURRENCY.fullmatch(value) is None:
        raise CalculationError("FCFE_CURRENCY_REQUIRED")
    return value


def _nonnegative(value: Any) -> Decimal:
    x = number(value)
    if x < ZERO:
        raise CalculationError("FCFE_NONNEGATIVE_MAGNITUDE_REQUIRED")
    return x


def _fmt(value: Decimal) -> str:
    return format(+value, "f")


def cost_of_equity_rate_sha256(rate: Any) -> str:
    r = number(rate)
    if not ZERO <= r <= ONE:
        raise CalculationError("FCFE_COST_OF_EQUITY_OUT_OF_REFERENCE_DOMAIN")
    return fingerprint({
        "contract": "HC_R06_ANNUAL_PERIOD_END_NOMINAL_KE_V1",
        "annualRate": format(r, "f"),
        "basis": "NOMINAL_ANNUAL_PERIOD_END",
    })


def fcfe_source_sha256(inputs_without_source_sha: Mapping[str, Any], variant: str) -> str:
    if variant not in BASIS:
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
    if not isinstance(inputs_without_source_sha, Mapping) or "sourceRevisionSha256" in inputs_without_source_sha:
        raise CalculationError("FCFE_SOURCE_SNAPSHOT_SCHEMA")
    return fingerprint({
        "contract": "HC_R06_FCFE_INPUT_SNAPSHOT_V1",
        "method": variant,
        "snapshot": inputs_without_source_sha,
    })


def fcfe(inputs: Mapping[str, Any], config: Mapping[str, Any], variant: str) -> dict[str, Any]:
    if variant not in BASIS:
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
    base = {
        "asOf", "currency", "sourceRevisionSha256",
        "costOfEquityRate", "costOfEquityRevisionSha256", "periodIndex",
        "cashCapex", "grossDebtDrawdowns", "principalRepayments",
    }
    variant_fields = (
        {"operatingCashFlowAfterInterest"} if variant == "FCFE_LEVERED"
        else {"netIncome", "noncashOperatingCharges", "deltaOperatingNwc"}
    )
    _fields(inputs, base | variant_fields, "FCFE_INPUT_SCHEMA")
    _date(inputs["asOf"])
    currency = _currency(inputs["currency"])
    for name, expected in POLICY.items():
        if config[name] != expected:
            raise CalculationError("FCFE_UNREVIEWED_POLICY", name)
    if config["equityCashflowBasis"] != BASIS[variant]:
        raise CalculationError("FCFE_BASIS_VARIANT_CONFLICT")
    source = _sha(inputs["sourceRevisionSha256"], "FCFE_SOURCE_SHA_REQUIRED")
    if source != fcfe_source_sha256({k: v for k, v in inputs.items()
                                    if k != "sourceRevisionSha256"}, variant):
        raise CalculationError("FCFE_SOURCE_DIGEST_MISMATCH")
    pinned_rate = _sha(inputs["costOfEquityRevisionSha256"],
                       "FCFE_COST_OF_EQUITY_SHA_REQUIRED")
    if pinned_rate != config["costOfEquityRef"]:
        raise CalculationError("FCFE_RATE_REVISION_MISMATCH")
    rate = number(inputs["costOfEquityRate"])
    if pinned_rate != cost_of_equity_rate_sha256(rate):
        raise CalculationError("FCFE_RATE_DIGEST_MISMATCH")
    period = integer(inputs["periodIndex"], minimum=1)
    if period > 100:
        raise CalculationError("FCFE_PERIOD_INDEX_TOO_LARGE")
    with localcontext() as ctx:
        ctx.prec = 40
        capex = _nonnegative(inputs["cashCapex"])
        draw = _nonnegative(inputs["grossDebtDrawdowns"])
        repay = _nonnegative(inputs["principalRepayments"])
        net_borrowing = draw - repay
        if variant == "FCFE_LEVERED":
            operating = number(inputs["operatingCashFlowAfterInterest"])
        else:
            ni = number(inputs["netIncome"])
            noncash = _nonnegative(inputs["noncashOperatingCharges"])
            nwc = number(inputs["deltaOperatingNwc"])
            operating = ni + noncash - nwc
        fcfe_value = operating - capex + net_borrowing
        present = fcfe_value / ((ONE + rate) ** period)
        return {
            "asOf": inputs["asOf"],
            "currency": currency,
            "sourceRevisionSha256": source,
            "costOfEquityRevisionSha256": pinned_rate,
            "costOfEquityRate": _fmt(rate),
            "periodIndex": period,
            "cashflowBasis": BASIS[variant],
            "operatingCashFlowAfterInterest": _fmt(operating),
            "capitalExpenditureCashEffect": _fmt(-capex),
            "grossDebtDrawdowns": _fmt(draw),
            "principalRepayments": _fmt(repay),
            "netBorrowing": _fmt(net_borrowing),
            "freeCashFlowToEquity": _fmt(fcfe_value),
            "presentValueOfFcfe": _fmt(present),
            "discountPolicy": "NOMINAL_ANNUAL_PERIOD_END_AT_KE_NOT_WACC",
            "classification": "FCFE_REFERENCE_NOT_ACCOUNTING_OR_TAX_S2",
        }


def reconcile_fcfe_methods(levered: Mapping[str, Any],
                           normalized: Mapping[str, Any]) -> dict[str, Any]:
    """Cross-check two *independent* reference outputs; no automatic admission."""
    if not isinstance(levered, Mapping) or not isinstance(normalized, Mapping):
        raise CalculationError("FCFE_RECONCILIATION_INPUT_REQUIRED")
    required = ("currency", "asOf", "periodIndex",
                "costOfEquityRevisionSha256", "costOfEquityRate")
    for name in required:
        if name not in levered or name not in normalized or levered[name] != normalized[name]:
            raise CalculationError("FCFE_RECONCILIATION_CONTEXT_MISMATCH", name)
    if (levered.get("cashflowBasis") != BASIS["FCFE_LEVERED"]
            or normalized.get("cashflowBasis") != BASIS["FCFE_NORMALIZED"]):
        raise CalculationError("FCFE_RECONCILIATION_METHOD_MISMATCH")
    if ("freeCashFlowToEquity" not in levered or "freeCashFlowToEquity" not in normalized):
        raise CalculationError("FCFE_RECONCILIATION_INPUT_REQUIRED")
    delta = number(levered["freeCashFlowToEquity"]) - number(normalized["freeCashFlowToEquity"])
    if delta != ZERO:
        raise CalculationError("FCFE_RECONCILIATION_MISMATCH")
    return {
        "status": "MATCHED_REFERENCE_NOT_S2",
        "difference": "0",
        "currency": levered["currency"],
        "asOf": levered["asOf"],
        "periodIndex": levered["periodIndex"],
        "costOfEquityRevisionSha256": levered["costOfEquityRevisionSha256"],
    }
