"""FEngine bounded mathematical calculation reference.

Real numerical execution, not a financial S2 approval, regulator calculation,
persistence, or an implementation of all catalogued models.
Only explicitly supported model/variant combinations execute; everything else
fails closed. Standard-library Python >=3.11.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, Mapping


class CalculationError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def _canonical(v: Any) -> Any:
    if isinstance(v, Decimal):
        if not v.is_finite():
            raise CalculationError("NONFINITE_DECIMAL")
        return format(v, "f")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float):
        raise CalculationError("BINARY_FLOAT_FORBIDDEN")
    if isinstance(v, Mapping):
        return {str(k): _canonical(v[k]) for k in sorted(v)}
    if isinstance(v, (list, tuple)):
        return [_canonical(x) for x in v]
    if v is None or isinstance(v, (str, int, bool)):
        return v
    raise CalculationError("INVALID_INPUT_TYPE", type(v).__name__)


def fingerprint(v: Any) -> str:
    raw = json.dumps(_canonical(v), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def number(v: Any) -> Decimal:
    if isinstance(v, bool) or isinstance(v, (float, int)):
        raise CalculationError("DECIMAL_STRING_REQUIRED")
    if not isinstance(v, (Decimal, str)):
        raise CalculationError("DECIMAL_STRING_REQUIRED")
    try:
        x = Decimal(v)
    except InvalidOperation as exc:
        raise CalculationError("INVALID_DECIMAL") from exc
    if not x.is_finite():
        raise CalculationError("NONFINITE_DECIMAL")
    return x


def day(v: Any) -> date:
    if isinstance(v, date) and not hasattr(v, "hour"):
        return v
    if not isinstance(v, str):
        raise CalculationError("DATE_REQUIRED")
    try:
        return date.fromisoformat(v)
    except ValueError as exc:
        raise CalculationError("INVALID_DATE") from exc


def integer(v: Any, *, minimum: int = 0) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v < minimum:
        raise CalculationError("INVALID_INTEGER")
    return v


def positive(v: Any) -> Decimal:
    x = number(v)
    if x <= 0:
        raise CalculationError("MUST_BE_POSITIVE")
    return x


def _rate(v: Any) -> Decimal:
    x = number(v)
    if x <= -1:
        raise CalculationError("RATE_OUT_OF_DOMAIN")
    return x


def _req(v: Mapping[str, Any], *names: str) -> tuple[Any, ...]:
    for name in names:
        if name not in v:
            raise CalculationError("REQUIRED_INPUT_MISSING", name)
    return tuple(v[k] for k in names)


def _keys(v: Mapping[str, Any], names: set[str]) -> None:
    unknown = set(v) - names
    if unknown:
        raise CalculationError("UNCONSUMED_CONFIGURATION", ",".join(sorted(unknown)))


def _money(x: Decimal) -> str:
    return format(+x, "f")


def npv(flows: list[Any], rate: Any, *, midperiod: bool = False) -> Decimal:
    r = _rate(rate)
    if not isinstance(flows, (list, tuple)) or not flows:
        raise CalculationError("CASHFLOWS_REQUIRED")
    with localcontext() as ctx:
        ctx.prec = 40
        values = [number(x) for x in flows]
        return sum((v / ((Decimal(1) + r) ** (
            Decimal(0) if i == 0 else Decimal(i) - (Decimal("0.5") if midperiod else Decimal(0))
        )) for i, v in enumerate(values)), Decimal(0))


def xnpv(flows: list[Mapping[str, Any]], rate: Any, origin: Any) -> Decimal:
    r = _rate(rate)
    d0 = day(origin)
    if not isinstance(flows, (list, tuple)) or not flows:
        raise CalculationError("DATED_CASHFLOWS_REQUIRED")
    with localcontext() as ctx:
        ctx.prec = 40
        total = Decimal(0)
        for row in flows:
            if not isinstance(row, Mapping):
                raise CalculationError("INVALID_DATED_FLOW")
            when, value = _req(row, "date", "amount")
            exponent = Decimal((day(when) - d0).days) / Decimal(365)
            total += number(value) / ((Decimal(1) + r) ** exponent)
        return +total


def capm(risk_free: Any, beta: Any, premium: Any) -> Decimal:
    return number(risk_free) + number(beta) * number(premium)


def wacc(equity: Any, debt: Any, cost_equity: Any, cost_debt: Any, tax: Any) -> Decimal:
    e, d = number(equity), number(debt)
    t = number(tax)
    if e < 0 or d < 0 or e + d <= 0 or not (0 <= t <= 1):
        raise CalculationError("INVALID_CAPITAL_WEIGHTS")
    return e / (e + d) * number(cost_equity) + d / (e + d) * number(cost_debt) * (1 - t)


def depreciation(cost: Any, salvage: Any, periods: int, method: str,
                 params: Mapping[str, Any], production: Any = None) -> dict[str, Any]:
    c, s, n = number(cost), number(salvage), integer(periods, minimum=1)
    if c < 0 or s < 0 or s > c:
        raise CalculationError("INVALID_DEPRECIABLE_BASIS")
    with localcontext() as ctx:
        ctx.prec = 40
        balance = c
        items: list[dict[str, str | int]] = []
        units = None
        if method == "UNITS_OF_PRODUCTION":
            _keys(params, {"residualValue", "usefulLifePeriods", "estimatedTotalProduction"})
            if not isinstance(production, (list, tuple)) or len(production) != n:
                raise CalculationError("PRODUCTION_SERIES_REQUIRED")
            units = [number(v) for v in production]
            total = positive(params["estimatedTotalProduction"])
            if any(x < 0 for x in units) or sum(units) != total:
                raise CalculationError("INVALID_PRODUCTION_COVERAGE")
        elif method == "DECLINING_BALANCE":
            _keys(params, {"residualValue", "usefulLifePeriods", "decliningRate", "terminalTrueUpPolicy"})
            decline = number(params["decliningRate"])
            if decline <= 0 or decline > 1:
                raise CalculationError("INVALID_DECLINING_RATE")
            if params.get("terminalTrueUpPolicy") not in ("FINAL_PERIOD", "NO_TRUE_UP"):
                raise CalculationError("TRUE_UP_POLICY_REQUIRED")
        elif method in ("STRAIGHT_LINE", "DOUBLE_DECLINING", "SUM_OF_YEARS_DIGITS"):
            _keys(params, {"residualValue", "usefulLifePeriods"})
        else:
            raise CalculationError("VARIANT_NOT_IMPLEMENTED", method)
        for index in range(1, n + 1):
            if method == "STRAIGHT_LINE":
                charge = (c - s) / n
            elif method == "UNITS_OF_PRODUCTION":
                charge = (c - s) * units[index - 1] / total
            elif method == "SUM_OF_YEARS_DIGITS":
                charge = (c - s) * (n - index + 1) / (n * (n + 1) / 2)
            elif method == "DOUBLE_DECLINING":
                charge = balance * Decimal(2) / n
            else:
                charge = balance * decline
            charge = min(max(Decimal(0), charge), balance - s)
            if index == n and method == "DECLINING_BALANCE" and params["terminalTrueUpPolicy"] == "FINAL_PERIOD":
                charge = balance - s
            if index == n and method == "DOUBLE_DECLINING":
                charge = balance - s
            balance -= charge
            items.append({"period": index, "depreciation": _money(charge), "closingBalance": _money(balance)})
        return {"periods": items, "totalDepreciation": _money(c - balance), "closingBalance": _money(balance)}


def loan_schedule(principal: Any, annual_rate: Any, start: Any, payment_dates: Any,
                  variant: str, day_count: str) -> dict[str, Any]:
    p, rate = positive(principal), number(annual_rate)
    if rate < 0:
        raise CalculationError("NEGATIVE_CONTRACT_RATE_UNSUPPORTED")
    if day_count != "ACT_365_FIXED":
        raise CalculationError("DAY_COUNT_NOT_IMPLEMENTED")
    previous = day(start)
    if not isinstance(payment_dates, (list, tuple)) or not payment_dates:
        raise CalculationError("PAYMENT_DATES_REQUIRED")
    dates = [day(x) for x in payment_dates]
    if any(a <= b for a, b in zip(dates, [previous] + dates[:-1])):
        raise CalculationError("PAYMENT_DATES_NOT_INCREASING")
    if variant not in ("ANNUITY_EQUAL_PAYMENT_DATED", "EQUAL_PRINCIPAL_DATED",
                       "INTEREST_ONLY_BALLOON", "BULLET"):
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
    with localcontext() as ctx:
        ctx.prec = 40
        factors = []
        for d in dates:
            factors.append(Decimal(1) + rate * Decimal((d - previous).days) / 365)
            previous = d
        annuity_payment = None
        if variant == "ANNUITY_EQUAL_PAYMENT_DATED":
            disc = Decimal(1)
            discounts = []
            for f in factors:
                disc /= f
                discounts.append(disc)
            annuity_payment = p / sum(discounts)
        opening = p
        rows = []
        accrued_bullet = Decimal(0)
        for i, (d, factor) in enumerate(zip(dates, factors)):
            interest = opening * (factor - 1)
            if variant == "ANNUITY_EQUAL_PAYMENT_DATED":
                payment = annuity_payment
                paid_principal = payment - interest
            elif variant == "EQUAL_PRINCIPAL_DATED":
                paid_principal = p / len(dates)
                payment = paid_principal + interest
            elif variant == "INTEREST_ONLY_BALLOON":
                paid_principal = opening if i == len(dates) - 1 else Decimal(0)
                payment = paid_principal + interest
            else:
                accrued_bullet += interest
                paid_principal = opening if i == len(dates) - 1 else Decimal(0)
                payment = (paid_principal + accrued_bullet) if i == len(dates) - 1 else Decimal(0)
            if i == len(dates) - 1 and variant in ("ANNUITY_EQUAL_PAYMENT_DATED", "EQUAL_PRINCIPAL_DATED"):
                paid_principal = opening
                payment = paid_principal + interest
            if paid_principal < 0 or paid_principal > opening:
                raise CalculationError("NEGATIVE_AMORTIZATION_OR_OVERPAYMENT")
            closing = opening - paid_principal
            rows.append({"date": d.isoformat(), "opening": _money(opening),
                         "interest": _money(interest), "principal": _money(paid_principal),
                         "payment": _money(payment), "closing": _money(closing)})
            opening = closing
        if opening != 0:
            raise CalculationError("PRINCIPAL_RECONCILIATION_FAILED")
        return {"schedule": rows, "totalPayment": _money(sum(number(r["payment"]) for r in rows)),
                "totalInterest": _money(sum(number(r["interest"]) for r in rows)),
                "closingPrincipal": _money(opening)}


def stock_cost(events: Any, variant: str) -> dict[str, str]:
    if not isinstance(events, (list, tuple)) or not events:
        raise CalculationError("STOCK_EVENTS_REQUIRED")
    data = []
    for row in events:
        when, event_id, quantity = _req(row, "date", "id", "quantity")
        qty = number(quantity)
        if qty == 0 or not isinstance(event_id, str) or not event_id:
            raise CalculationError("INVALID_STOCK_EVENT")
        unit = positive(row["unitCost"]) if qty > 0 else None
        data.append((day(when), event_id, qty, unit))
    if len({(x[0], x[1]) for x in data}) != len(data):
        raise CalculationError("DUPLICATE_STOCK_EVENT_ID")
    data.sort(key=lambda r: (r[0], r[1]))
    with localcontext() as ctx:
        ctx.prec = 40
        issued = Decimal(0)
        qty_left = Decimal(0)
        cost_left = Decimal(0)
        if variant == "FIFO_LOT_REPLAY":
            lots: list[list[Decimal]] = []
            for _, _, qty, unit in data:
                if qty > 0:
                    lots.append([qty, unit])
                else:
                    needed = -qty
                    if needed > sum(lot[0] for lot in lots):
                        raise CalculationError("NEGATIVE_INVENTORY")
                    while needed > 0:
                        first = lots[0]
                        used = min(needed, first[0])
                        issued += used * first[1]
                        first[0] -= used
                        needed -= used
                        if first[0] == 0:
                            lots.pop(0)
            qty_left = sum((r[0] for r in lots), Decimal(0))
            cost_left = sum((r[0] * r[1] for r in lots), Decimal(0))
        elif variant == "MOVING_WAC":
            for _, _, qty, unit in data:
                if qty > 0:
                    cost_left += qty * unit
                    qty_left += qty
                else:
                    if -qty > qty_left:
                        raise CalculationError("NEGATIVE_INVENTORY")
                    avg = cost_left / qty_left
                    cogs = (-qty) * avg
                    issued += cogs
                    cost_left -= cogs
                    qty_left += qty
                    if qty_left == 0:
                        cost_left = Decimal(0)
        elif variant == "PERIODIC_WAC":
            total_qty = sum((r[2] for r in data if r[2] > 0), Decimal(0))
            if total_qty <= 0:
                raise CalculationError("ZERO_WEIGHT_DENOMINATOR")
            total_cost = sum((r[2] * r[3] for r in data if r[2] > 0), Decimal(0))
            cumulative = Decimal(0)
            for _, _, qty, _ in data:
                cumulative += qty
                if cumulative < 0:
                    raise CalculationError("NEGATIVE_INVENTORY")
            qty_left = cumulative
            avg = total_cost / total_qty
            issued = (total_qty - qty_left) * avg
            cost_left = qty_left * avg
        else:
            raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
        return {"costOfGoodsSold": _money(issued), "endingQuantity": _money(qty_left),
                "endingInventory": _money(cost_left)}


def ageing(items: Any, as_of: Any, grace_days: int, edges: Any) -> dict[str, Any]:
    at = day(as_of)
    grace = integer(grace_days)
    if not isinstance(edges, (tuple, list)) or not edges:
        raise CalculationError("AGE_BUCKETS_REQUIRED")
    bounds = [integer(x, minimum=1) for x in edges]
    if bounds != sorted(set(bounds)):
        raise CalculationError("OVERLAPPING_AGE_BUCKETS")
    labels = ["CURRENT"] + [str((bounds[i-1] if i else 0) + 1) + "-" + str(b)
                            for i, b in enumerate(bounds)] + [str(bounds[-1] + 1) + "+"]
    values = {label: Decimal(0) for label in labels}
    if not isinstance(items, (tuple, list)):
        raise CalculationError("OBLIGATIONS_REQUIRED")
    for row in items:
        due, amount = _req(row, "dueDate", "unpaidAmount")
        value = number(amount)
        if value < 0:
            raise CalculationError("NEGATIVE_OUTSTANDING")
        late = (at - day(due)).days - grace
        index = 0 if late <= 0 else next((i + 1 for i, upper in enumerate(bounds) if late <= upper), len(bounds) + 1)
        values[labels[index]] += value
    return {"buckets": {k: _money(v) for k, v in values.items()},
            "totalOutstanding": _money(sum(values.values()))}


def pf_coverage(flows: Any, discount_rate: Any, debt: Any, variant: str, loan_periods: int) -> Decimal:
    principal = positive(debt)
    if not isinstance(flows, (list, tuple)) or not flows:
        raise CalculationError("CFADS_REQUIRED")
    count = integer(loan_periods, minimum=1)
    if count > len(flows):
        raise CalculationError("LOAN_LIFE_EXCEEDS_PROJECT")
    if variant == "LLCR_DEBT_LIFE":
        use = flows[:count]
    elif variant == "PLCR_PROJECT_LIFE":
        use = flows
    else:
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
    return npv(["0"] + list(use), discount_rate) / principal


@dataclass(frozen=True)
class CalculationResult:
    model_code: str
    variant_code: str
    execution_class: str
    inputs_sha256: str
    config_sha256: str
    output_sha256: str
    output: dict[str, Any]


class ContractRegistry:
    def __init__(self, root: Path):
        cat = root / "catalog"
        def read(name: str) -> list[dict[str, str]]:
            with (cat / name).open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader((line for line in f
                                            if line.strip() and not line.lstrip().startswith("#")),
                                           delimiter="\t"))
            if not rows or any(None in r for r in rows):
                raise CalculationError("INVALID_CATALOG", name)
            return rows
        profiles = read("model_variant_profiles_116_r3.tsv")
        variants = read("method_variant_definitions_116_r3.tsv")
        parameters = read("method_parameter_candidates_116_r3.tsv")
        self.models = {r["modelCode"]: r for r in profiles}
        self.variants = {(r["modelCode"], r["variantCode"]): r for r in variants}
        self.params = {(r["modelCode"], r["parameterCode"]): r for r in parameters}
        if len(profiles) != 116 or len(variants) != 222 or len(parameters) != 732:
            raise CalculationError("CATALOG_COUNT_MISMATCH")
        if len(self.models) != 116 or len(self.variants) != 222 or len(self.params) != 732:
            raise CalculationError("DUPLICATE_CATALOG_KEY")
        for (model, variant), row in self.variants.items():
            if model not in self.models:
                raise CalculationError("DANGLING_MODEL_REFERENCE")
            if variant not in self.models[model]["candidateVariantCodes"].split("|"):
                raise CalculationError("UNLISTED_VARIANT")
            for key in filter(None, row["variantParameterKeys"].split("|")):
                if (model, key) not in self.params:
                    raise CalculationError("DANGLING_PARAMETER")
        for model, profile in self.models.items():
            if len(profile["candidateVariantCodes"].split("|")) != int(profile["variantCount"]):
                raise CalculationError("VARIANT_COUNT_MISMATCH", model)


class ReferenceEngine:
    """Explicit opt-in mathematical reference; all unimplemented contracts fail closed."""
    def __init__(self, root: Path):
        self.registry = ContractRegistry(root)

    def calculate(self, model: str, variant: str, inputs: Mapping[str, Any],
                  config: Mapping[str, Any], *, reference_mode: bool = False) -> CalculationResult:
        if not reference_mode:
            raise CalculationError("FINANCIAL_S2_REQUIRED")
        if model not in self.registry.models:
            raise CalculationError("UNKNOWN_MODEL", model)
        if (model, variant) not in self.registry.variants:
            raise CalculationError("UNKNOWN_VARIANT", variant)
        if not isinstance(inputs, Mapping) or not isinstance(config, Mapping):
            raise CalculationError("INVALID_REQUEST")
        _canonical(inputs)
        _canonical(config)
        for key in config:
            if (model, key) not in self.registry.params:
                raise CalculationError("UNKNOWN_PARAMETER", key)
        with localcontext() as ctx:
            ctx.prec = 40
            if model == "HC.DCF.01":
                _keys(config, {"timingConvention"})
                if variant not in ("PERIOD_END_NPV", "MIDPERIOD_NPV"):
                    raise CalculationError("VARIANT_NOT_IMPLEMENTED")
                timing = "PERIOD_END" if variant == "PERIOD_END_NPV" else "MIDPERIOD"
                if config.get("timingConvention", timing) != timing:
                    raise CalculationError("VARIANT_CONFIG_CONFLICT")
                flows, rate = _req(inputs, "cashflows", "discountRate")
                output = {"npv": _money(npv(flows, rate, midperiod=timing == "MIDPERIOD"))}
            elif model == "HC.DCF.02":
                _keys(config, {"dayCount"})
                if config.get("dayCount") != "ACT_365_FIXED":
                    raise CalculationError("DAY_COUNT_REQUIRED")
                if variant not in ("EXACT_DATE_XNPV", "APPROVED_DAYCOUNT_XNPV"):
                    raise CalculationError("VARIANT_NOT_IMPLEMENTED")
                flows, rate, origin = _req(inputs, "cashflows", "discountRate", "valuationDate")
                output = {"xnpv": _money(xnpv(flows, rate, origin))}
            elif model == "HC.CAP.01":
                _keys(config, set())
                if variant != "CAPM_BASE":
                    raise CalculationError("VARIANT_NOT_IMPLEMENTED")
                rf, beta, premium = _req(inputs, "riskFreeRate", "beta", "marketRiskPremium")
                output = {"costOfEquity": _money(capm(rf, beta, premium))}
            elif model == "HC.CAP.02":
                _keys(config, set())
                if variant not in ("MARKET_VALUE_WACC", "TARGET_WEIGHT_WACC"):
                    raise CalculationError("VARIANT_NOT_IMPLEMENTED")
                eq, debt, ke, kd, tax = _req(inputs, "equityValue", "debtValue", "costOfEquity",
                                              "costOfDebt", "taxRate")
                output = {"wacc": _money(wacc(eq, debt, ke, kd, tax))}
            elif model == "HC.ASSET.01":
                cost, = _req(inputs, "cost")
                s, n = _req(config, "residualValue", "usefulLifePeriods")
                output = depreciation(cost, s, n, variant, config, inputs.get("production"))
            elif model == "HC.LOAN.02":
                _keys(config, set())
                principal, rate, start, dates, basis = _req(inputs, "principal", "annualRate", "startDate",
                                                            "paymentDates", "dayCount")
                output = loan_schedule(principal, rate, start, dates, variant, basis)
            elif model in ("HC.STOCK.01", "HC.STOCK.02"):
                _keys(config, set())
                events, = _req(inputs, "events")
                permitted = ("FIFO_LOT_REPLAY",) if model.endswith(".01") else ("MOVING_WAC", "PERIODIC_WAC")
                if variant not in permitted:
                    raise CalculationError("VARIANT_NOT_IMPLEMENTED")
                output = stock_cost(events, variant)
            elif model == "HC.SET.03":
                _keys(config, {"graceDays", "ageingBucketEdges"})
                if variant not in ("DUE_DATE_AGING", "GRACE_ADJUSTED_AGING"):
                    raise CalculationError("VARIANT_NOT_IMPLEMENTED")
                grace = config.get("graceDays", 0)
                if variant == "DUE_DATE_AGING" and grace != 0:
                    raise CalculationError("VARIANT_CONFIG_CONFLICT")
                if variant == "GRACE_ADJUSTED_AGING" and "graceDays" not in config:
                    raise CalculationError("GRACE_DAYS_REQUIRED")
                items, at = _req(inputs, "obligations", "asOf")
                edges, = _req(config, "ageingBucketEdges")
                output = ageing(items, at, grace, edges)
            elif model == "HC.PF.01":
                _keys(config, set())
                flows, rate, debt, loan_periods = _req(inputs, "cfads", "discountRate", "outstandingDebt", "loanPeriods")
                output = {"coverageRatio": _money(pf_coverage(flows, rate, debt, variant, loan_periods))}
            else:
                raise CalculationError("MODEL_NOT_IMPLEMENTED", model)
            inhash, confighash = fingerprint(inputs), fingerprint({"model": model, "variant": variant, "config": config})
            result_hash = fingerprint({"model": model, "variant": variant, "inputs": inhash,
                                       "config": confighash, "output": output, "class": "PYTHON_REFERENCE_NOT_S2"})
            return CalculationResult(model, variant, "PYTHON_REFERENCE_NOT_S2", inhash,
                                     confighash, result_hash, output)
