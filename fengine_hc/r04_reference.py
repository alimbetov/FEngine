"""HC-R0.4 financial arithmetic reference: CFO, FCFF, equity bridge, escalation.

All functions require explicit bounded assumptions and exact Decimal inputs.
This is a mathematical reference, not financial S2, tax advice or authority for
source classifications. No storage or network operations.
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, localcontext
from typing import Any, Mapping

from .reference import CalculationError, day, number

ZERO, ONE = Decimal(0), Decimal(1)
_MAX_COMPONENTS = 1000
_SHA = re.compile(r"[0-9a-f]{64}")


def _schema(data: Any, required: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping) or set(data) != required:
        raise CalculationError(code)
    return data


def _format(x: Decimal) -> str:
    return format(+x, "f")


def _money(x: Any, *, nonnegative: bool = False) -> Decimal:
    amount = number(x)
    if nonnegative and amount < ZERO:
        raise CalculationError("NEGATIVE_MONETARY_MAGNITUDE")
    return amount


def _currency(text: Any) -> str:
    # Reference lexer only, not evidence of ISO-4217 qualification.
    if not isinstance(text, str) or not re.fullmatch(r"[A-Z]{3}", text):
        raise CalculationError("INVALID_CURRENCY_CODE")
    return text


def _rev(value: Any) -> str:
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise CalculationError("REVISION_SHA256_REQUIRED")
    return value


def _finance_context(inputs: Mapping[str, Any]) -> tuple[date, str]:
    return day(inputs["asOf"]), _currency(inputs["currency"])


def indirect_cfo(inputs: Mapping[str, Any], variant: str,
                 config: Mapping[str, Any]) -> dict[str, Any]:
    """CFO = NI + signed noncash adjustments - increase in operating NWC.

    The signed adjustment convention is explicit; this function cannot assert
    classification of journal entries or noncash eligibility.
    """
    base = {"asOf", "currency", "netIncome", "noncashAdjustments",
            "deltaOperatingNwc", "sourceRevisionSha256"}
    required = base | ({"directCfo"} if variant == "INDIRECT_CFO_RECONCILED" else set())
    if "periodStart" in inputs:
        required.add("periodStart")
    _schema(inputs, required, "CFO_INPUT_SCHEMA")
    as_of, currency = _finance_context(inputs)
    if "periodStart" in inputs and day(inputs["periodStart"]) > as_of:
        raise CalculationError("CFO_INVALID_PERIOD")
    source = _rev(inputs["sourceRevisionSha256"])
    if config["netIncomeBasis"] != "REPORTED_AFTER_TAX_NET_INCOME":
        raise CalculationError("CFO_NET_INCOME_BASIS_NOT_SUPPORTED")
    if config["noncashAdjustment"] != "SIGNED_NONCASH_LINES":
        raise CalculationError("CFO_NONCASH_CONVENTION_NOT_SUPPORTED")
    if config["workingCapitalSign"] != "INCREASE_OF_NWC_IS_OUTFLOW":
        raise CalculationError("CFO_NWC_CONVENTION_NOT_SUPPORTED")
    rows = inputs["noncashAdjustments"]
    if not isinstance(rows, (list, tuple)) or len(rows) > _MAX_COMPONENTS:
        raise CalculationError("CFO_ADJUSTMENT_LIST_REQUIRED")
    seen = set()
    parsed: list[tuple[str, Decimal]] = []
    for item in rows:
        row = _schema(item, {"code", "amount"}, "CFO_ADJUSTMENT_SCHEMA")
        code = row["code"]
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
            raise CalculationError("CFO_ADJUSTMENT_CODE_INVALID")
        if code in seen:
            raise CalculationError("CFO_DUPLICATE_ADJUSTMENT_CODE")
        seen.add(code)
        parsed.append((code, number(row["amount"])))
    with localcontext() as ctx:
        ctx.prec = 40
        ni = number(inputs["netIncome"])
        noncash = sum((amount for _, amount in parsed), ZERO)
        delta = number(inputs["deltaOperatingNwc"])
        cfo = ni + noncash - delta
        result = {
            "asOf": as_of.isoformat(), "currency": currency,
            "sourceRevisionSha256": source,
            "netIncome": _format(ni), "noncashAdjustmentsTotal": _format(noncash),
            "workingCapitalCashEffect": _format(-delta),
            "cashFlowFromOperations": _format(cfo),
            "adjustmentCount": len(parsed),
            "classification": "SIGNED_COMPONENT_REFERENCE_NOT_ACCOUNTING_S2",
        }
        if variant == "INDIRECT_CFO_RECONCILED":
            if config["directIndirectComparisonPolicy"] != "EXACT_EQUALITY":
                raise CalculationError("CFO_RECONCILIATION_POLICY_UNSUPPORTED")
            direct = number(inputs["directCfo"])
            delta_recon = cfo - direct
            if delta_recon != ZERO:
                raise CalculationError("CFO_RECONCILIATION_MISMATCH")
            result["directCfo"] = _format(direct)
            result["reconciliationDifference"] = _format(delta_recon)
        elif variant != "INDIRECT_CFO_ADJUSTMENT":
            raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
        return result


def unlevered_fcff(inputs: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    """Simple EBIT-based unlevered FCFF with no implicit loss tax benefit."""
    _schema(inputs, {"asOf", "currency", "sourceRevisionSha256",
                     "ebit", "taxRate", "noncashOperatingCharges",
                     "cashCapex", "deltaOperatingNwc"}, "FCFF_INPUT_SCHEMA")
    as_of, currency = _finance_context(inputs)
    source = _rev(inputs["sourceRevisionSha256"])
    if config["taxPolicy"] != "EBIT_TIMES_EFFECTIVE_TAX_REFERENCE":
        raise CalculationError("FCFF_TAX_POLICY_NOT_SUPPORTED")
    if config["capitalExpenditurePolicy"] != "CASH_CAPEX_POSITIVE_OUTFLOW":
        raise CalculationError("FCFF_CAPEX_CONVENTION_NOT_SUPPORTED")
    if config["workingCapitalBasis"] != "INCREASE_NWC_IS_OUTFLOW":
        raise CalculationError("FCFF_NWC_CONVENTION_NOT_SUPPORTED")
    with localcontext() as ctx:
        ctx.prec = 40
        ebit = number(inputs["ebit"])
        if ebit < ZERO:
            raise CalculationError("FCFF_NEGATIVE_EBIT_REQUIRES_TAX_POLICY")
        tax_rate = number(inputs["taxRate"])
        if tax_rate < ZERO or tax_rate > ONE:
            raise CalculationError("FCFF_TAX_RATE_OUT_OF_RANGE")
        da = _money(inputs["noncashOperatingCharges"], nonnegative=True)
        capex = _money(inputs["cashCapex"], nonnegative=True)
        nwc = number(inputs["deltaOperatingNwc"])
        tax = ebit * tax_rate
        nopat = ebit - tax
        value = nopat + da - capex - nwc
        return {
            "asOf": as_of.isoformat(), "currency": currency,
            "sourceRevisionSha256": source,
            "taxOnOperatingProfit": _format(tax),
            "netOperatingProfitAfterTax": _format(nopat),
            "noncashCharges": _format(da),
            "capitalExpenditureCashFlow": _format(-capex),
            "workingCapitalCashFlow": _format(-nwc),
            "freeCashFlowToFirm": _format(value),
            "classification": "SIMPLIFIED_UNLEVERED_REFERENCE_NOT_TAX_S2",
        }


def enterprise_to_equity(inputs: Mapping[str, Any],
                         config: Mapping[str, Any]) -> dict[str, Any]:
    """Equity = EV - interest debt + unrestricted cash + nonoperation assets
    - preferred and NCI, assuming every bridge component excluded from EV
    and no double-counted cash/asset claim.
    """
    _schema(inputs, {"valuationDate", "currency", "sourceRevisionSha256",
                     "enterpriseValue", "grossInterestDebt", "unrestrictedCash",
                     "nonOperatingAssets", "nonControllingInterest",
                     "preferredClaims"}, "EQUITY_BRIDGE_INPUT_SCHEMA")
    if config["valuationDate"] != day(inputs["valuationDate"]).isoformat():
        raise CalculationError("EQUITY_VALUATION_DATE_MISMATCH")
    if config["netDebtDefinition"] != "GROSS_DEBT_LESS_UNRESTRICTED_CASH":
        raise CalculationError("EQUITY_NET_DEBT_POLICY_UNSUPPORTED")
    if config["minorityInterests"] != "NCI_DEDUCT_FROM_ENTERPRISE":
        raise CalculationError("EQUITY_NCI_POLICY_UNSUPPORTED")
    d, currency, source = day(inputs["valuationDate"]), _currency(inputs["currency"]), _rev(inputs["sourceRevisionSha256"])
    with localcontext() as ctx:
        ctx.prec = 40
        ev = number(inputs["enterpriseValue"])
        debt = _money(inputs["grossInterestDebt"], nonnegative=True)
        cash = _money(inputs["unrestrictedCash"], nonnegative=True)
        assets = _money(inputs["nonOperatingAssets"], nonnegative=True)
        nci = _money(inputs["nonControllingInterest"], nonnegative=True)
        preferred = _money(inputs["preferredClaims"], nonnegative=True)
        net_debt = debt - cash
        equity = ev - net_debt + assets - nci - preferred
        return {
            "valuationDate": d.isoformat(), "currency": currency,
            "sourceRevisionSha256": source,
            "netDebt": _format(net_debt),
            "equityValue": _format(equity),
            "enterpriseValue": _format(ev),
            "bridgeReconciliation": _format(equity + net_debt - assets + nci + preferred - ev),
            "classification": "EV_EQUITY_BRIDGE_REFERENCE_NOT_S2",
        }


def compound_cost_escalation(inputs: Mapping[str, Any],
                             config: Mapping[str, Any]) -> dict[str, Any]:
    """Explicit dated/source-pinned discrete annual multipliers.

    Source SHA is a binding identifier, not proof that the rate series has been
    independently reviewed or sourced from an official index.
    """
    _schema(inputs, {"baseCost", "annualRates", "currency", "rateSeriesRevisionSha256"},
            "ESCALATION_INPUT_SCHEMA")
    currency, sha = _currency(inputs["currency"]), _rev(inputs["rateSeriesRevisionSha256"])
    if sha != config["inflationIndexRev"]:
        raise CalculationError("ESCALATION_INDEX_REVISION_MISMATCH")
    if config["compoundingBasis"] != "DISCRETE_ANNUAL_END":
        raise CalculationError("ESCALATION_BASIS_UNSUPPORTED")
    if config["contingencyOverlap"] != "NO_CONTINGENCY_DOUBLE_COUNT":
        raise CalculationError("ESCALATION_CONTINGENCY_POLICY_UNSUPPORTED")
    rates = inputs["annualRates"]
    if not isinstance(rates, (list, tuple)) or not 1 <= len(rates) <= 100:
        raise CalculationError("ESCALATION_RATE_SERIES_REQUIRED")
    with localcontext() as ctx:
        ctx.prec = 40
        base = _money(inputs["baseCost"], nonnegative=True)
        cost = base
        years = []
        for index, quote in enumerate(rates, start=1):
            r = number(quote)
            if r <= -ONE or r > Decimal("10"):
                raise CalculationError("ESCALATION_RATE_OUT_OF_DOMAIN")
            cost *= ONE + r
            years.append({"year": index, "annualRate": _format(r),
                          "escalatedCost": _format(cost)})
        return {"currency": currency, "rateSeriesRevisionSha256": sha,
                "baseCost": _format(base), "escalatedCost": _format(cost),
                "incrementalCost": _format(cost - base),
                "years": years, "classification": "PINNED_RATE_SERIES_MATH_NOT_INDEX_S2"}
