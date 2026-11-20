"""HC-R0.3 reference wave: runway, contribution break-even, EVM, Gordon terminal.

Bounded, fully executed Decimal algorithms. Not reviewed financial methodology,
not verified source facts, not a durable runtime. Inputs are ephemeral in memory;
this module never persists them, including not to Redis or PostgreSQL.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_CEILING, localcontext
from typing import Any, Mapping

from .reference import CalculationError, day, integer, number

ZERO = Decimal(0)
ONE = Decimal(1)
REFERENCE_PRECISION = 40


def _fields(value: Any, expected: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise CalculationError(code)
    return value


def _currency(value: Any) -> str:
    # The 3-letter token is NOT an authoritative ISO-4217 currency registry.
    if (not isinstance(value, str) or len(value) != 3
            or not value.isascii() or not value.isalpha() or value != value.upper()):
        raise CalculationError("CURRENCY_CODE_REQUIRED")
    return value


def _amount(value: Any, *, nonnegative: bool = False) -> Decimal:
    result = number(value)
    if nonnegative and result < ZERO:
        raise CalculationError("NEGATIVE_AMOUNT_FORBIDDEN")
    return result


def _out(x: Decimal) -> str:
    return format(+x, "f")


def _flows(as_of: date, cashflows: Any) -> tuple[tuple[date, Decimal], ...]:
    if not isinstance(cashflows, (list, tuple)) or not 1 <= len(cashflows) <= 3660:
        raise CalculationError("CASHFLOW_HORIZON_REQUIRED")
    previous = as_of
    result = []
    for row in cashflows:
        r = _fields(row, {"date", "netCashflow"}, "CASHFLOW_ROW_SCHEMA")
        d = day(r["date"])
        if d <= previous:
            raise CalculationError("CASHFLOW_DATES_NOT_STRICTLY_INCREASING")
        previous = d
        result.append((d, number(r["netCashflow"])))
    return tuple(result)


def _runway_one(as_of: date, opening: Decimal, cashflows: Any,
                floor: Decimal, breach_rule: str) -> dict[str, Any]:
    data = _flows(as_of, cashflows)
    below = (lambda value: value < floor) if breach_rule == "STRICT_BELOW_FLOOR" else (
        lambda value: value <= floor
    )
    current = opening
    balance_at_breach = None
    first = None
    if below(current):
        first, balance_at_breach = as_of, current
    timeline: list[dict[str, str]] = []
    for d, net in data:
        current += net
        timeline.append({"date": d.isoformat(), "closingCash": _out(current)})
        if first is None and below(current):
            first, balance_at_breach = d, current
    return {
        "status": "BREACHED" if first is not None else "NO_BREACH_WITHIN_HORIZON",
        "firstBreachDate": first.isoformat() if first is not None else None,
        "elapsedDays": (first - as_of).days if first is not None else None,
        "cashAtFirstBreach": _out(balance_at_breach) if first is not None else None,
        "closingCash": _out(current),
        "horizonEnd": data[-1][0].isoformat(),
        "timeline": timeline,
    }


def cash_runway(inputs: Mapping[str, Any], variant: str,
                config: Mapping[str, Any]) -> dict[str, Any]:
    floor = number(config["floorValue"])
    rule = config["firstPassageRule"]
    if rule not in ("STRICT_BELOW_FLOOR", "AT_OR_BELOW_FLOOR"):
        raise CalculationError("INVALID_FIRST_PASSAGE_RULE")
    if variant == "DETERMINISTIC_RUNWAY":
        row = _fields(inputs, {"asOf", "openingCash", "currency", "cashflows"}, "RUNWAY_INPUT_SCHEMA")
        as_of, opening, currency = day(row["asOf"]), number(row["openingCash"]), _currency(row["currency"])
        one = _runway_one(as_of, opening, row["cashflows"], floor, rule)
        return {"currency": currency, "floor": _out(floor), "breachRule": rule, **one}
    if variant == "SCENARIO_RUNWAY":
        row = _fields(inputs, {"asOf", "openingCash", "currency", "scenarios"}, "RUNWAY_INPUT_SCHEMA")
        as_of, opening, currency = day(row["asOf"]), number(row["openingCash"]), _currency(row["currency"])
        scenarios = row["scenarios"]
        if not isinstance(scenarios, (list, tuple)) or not 1 <= len(scenarios) <= 100:
            raise CalculationError("RUNWAY_SCENARIOS_REQUIRED")
        result = []
        identifiers = set()
        for entry in scenarios:
            item = _fields(entry, {"scenarioId", "cashflows"}, "RUNWAY_SCENARIO_SCHEMA")
            scenario_id = item["scenarioId"]
            if not isinstance(scenario_id, str) or not scenario_id or scenario_id in identifiers:
                raise CalculationError("RUNWAY_SCENARIO_ID_INVALID_OR_DUPLICATE")
            identifiers.add(scenario_id)
            result.append({"scenarioId": scenario_id,
                           **_runway_one(as_of, opening, item["cashflows"], floor, rule)})
        return {"currency": currency, "floor": _out(floor), "breachRule": rule,
                "scenarios": result, "classification": "DETERMINISTIC_PATHS_NO_PROBABILITIES"}
    raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)


def _positive_contribution(price: Any, variable_cost: Any) -> tuple[Decimal, Decimal, Decimal]:
    p = _amount(price, nonnegative=True)
    v = _amount(variable_cost, nonnegative=True)
    margin = p - v
    if margin <= ZERO:
        raise CalculationError("NONPOSITIVE_CONTRIBUTION_MARGIN")
    return p, v, margin


def break_even(inputs: Mapping[str, Any], variant: str,
               config: Mapping[str, Any]) -> dict[str, Any]:
    with localcontext() as ctx:
        ctx.prec = REFERENCE_PRECISION
        if variant == "SINGLE_PRODUCT_BREAKEVEN":
            row = _fields(inputs, {"fixedCost", "unitPrice", "unitVariableCost",
                                   "currency", "quantityUnit"}, "BREAKEVEN_INPUT_SCHEMA")
            fixed = _amount(row["fixedCost"], nonnegative=True)
            c = _currency(row["currency"])
            unit = row["quantityUnit"]
            if not isinstance(unit, str) or not unit:
                raise CalculationError("QUANTITY_UNIT_REQUIRED")
            price, _, margin = _positive_contribution(row["unitPrice"], row["unitVariableCost"])
            exact = fixed / margin
            policy = config["minimumLotRule"]
            if policy != "WHOLE_UNITS":
                raise CalculationError("BREAK_EVEN_LOT_POLICY_NOT_SUPPORTED")
            units = int(exact.to_integral_value(rounding=ROUND_CEILING))
            sales = Decimal(units) * price
            return {"currency": c, "quantityUnit": unit,
                    "unitContribution": _out(margin),
                    "breakEvenUnitsExact": _out(exact),
                    "minimumWholeUnits": units,
                    "revenueAtMinimumUnits": _out(sales),
                    "contributionAtMinimumUnits": _out(Decimal(units) * margin),
                    "fixedCost": _out(fixed)}
        if variant == "PRODUCT_MIX_BREAKEVEN":
            row = _fields(inputs, {"fixedCost", "products", "currency"}, "BREAKEVEN_INPUT_SCHEMA")
            fixed = _amount(row["fixedCost"], nonnegative=True)
            c = _currency(row["currency"])
            if config["minimumLotRule"] != "WHOLE_BUNDLES" or config["mixtureBundleIntegrality"] is not True:
                raise CalculationError("BREAK_EVEN_BUNDLE_POLICY_REQUIRED")
            products = row["products"]
            if not isinstance(products, (list, tuple)) or not 1 <= len(products) <= 100:
                raise CalculationError("BREAK_EVEN_PRODUCTS_REQUIRED")
            ids: set[str] = set()
            total_margin, total_price = ZERO, ZERO
            detail = []
            for entry in products:
                item = _fields(entry, {"sku", "unitsPerBundle", "unitPrice", "unitVariableCost"},
                               "BREAK_EVEN_PRODUCT_SCHEMA")
                sku = item["sku"]
                if not isinstance(sku, str) or not sku or sku in ids:
                    raise CalculationError("BREAK_EVEN_DUPLICATE_SKU")
                ids.add(sku)
                n = integer(item["unitsPerBundle"], minimum=1)
                price, _, margin = _positive_contribution(item["unitPrice"], item["unitVariableCost"])
                total_price += price * n
                total_margin += margin * n
                detail.append((sku, n))
            exact = fixed / total_margin
            bundles = int(exact.to_integral_value(rounding=ROUND_CEILING))
            return {"currency": c, "bundleContribution": _out(total_margin),
                    "bundleRevenue": _out(total_price), "breakEvenBundlesExact": _out(exact),
                    "minimumWholeBundles": bundles,
                    "minimumUnitsByProduct": [
                        {"sku": sku, "units": n * bundles} for sku, n in detail
                    ],
                    "revenueAtMinimumBundles": _out(total_price * bundles),
                    "contributionAtMinimumBundles": _out(total_margin * bundles),
                    "fixedCost": _out(fixed)}
        raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)


def evm(inputs: Mapping[str, Any], variant: str, config: Mapping[str, Any]) -> dict[str, Any]:
    row = _fields(inputs, {"asOf", "baselineRevision", "plannedValue",
                           "earnedValue", "actualCost", "budgetAtCompletion", "currency"},
                  "EVM_INPUT_SCHEMA")
    baseline = row["baselineRevision"]
    if not isinstance(baseline, str) or not baseline:
        raise CalculationError("EVM_BASELINE_REVISION_REQUIRED")
    as_of, currency = day(row["asOf"]), _currency(row["currency"])
    pv = _amount(row["plannedValue"], nonnegative=True)
    ev = _amount(row["earnedValue"], nonnegative=True)
    ac = _amount(row["actualCost"], nonnegative=True)
    bac = _amount(row["budgetAtCompletion"], nonnegative=True)
    if bac <= ZERO or ev > bac:
        raise CalculationError("EVM_INVALID_BASELINE_OR_PROGRESS")
    if ac == ZERO:
        raise CalculationError("EVM_ZERO_ACTUAL_COST_CPI_UNDEFINED")
    if config["earnedValueRule"] != "EXTERNALLY_SUPPLIED_EV":
        raise CalculationError("EVM_UNREVIEWED_EARNED_VALUE_SOURCE")
    with localcontext() as ctx:
        ctx.prec = REFERENCE_PRECISION
        cpi = ev / ac
        if cpi == ZERO:
            raise CalculationError("EVM_ZERO_CPI_FORECAST_UNDEFINED")
        if variant == "EVM_BAC_CPI":
            if config["eacFormula"] != "BAC_DIV_CPI":
                raise CalculationError("EVM_VARIANT_FORMULA_MISMATCH")
            eac = bac / cpi
        elif variant == "EVM_EAC_FORECAST":
            if config["eacFormula"] != "AC_PLUS_REMAINING_AT_BUDGET":
                raise CalculationError("EVM_VARIANT_FORMULA_MISMATCH")
            eac = ac + (bac - ev)
        else:
            raise CalculationError("VARIANT_NOT_IMPLEMENTED", variant)
        return {
            "asOf": as_of.isoformat(), "currency": currency, "baselineRevision": baseline,
            "costPerformanceIndex": _out(cpi),
            "costVariance": _out(ev - ac), "scheduleVariance": _out(ev - pv),
            "estimateAtCompletion": _out(eac),
            "varianceAtCompletion": _out(bac - eac),
            "formula": config["eacFormula"],
            "classification": "PRECOMPUTED_EV_REFERENCE_NOT_BASELINE_APPROVED",
        }


def gordon_terminal(inputs: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    row = _fields(inputs, {"finalForecastFCFF", "wacc", "forecastPeriods", "currency"},
                  "TERMINAL_INPUT_SCHEMA")
    currency = _currency(row["currency"])
    fcff = number(row["finalForecastFCFF"])
    wacc, growth = number(row["wacc"]), number(config["terminalGrowth"])
    if fcff < ZERO:
        raise CalculationError("NEGATIVE_TERMINAL_FCFF_UNSUPPORTED")
    if not (-ONE < growth < wacc) or wacc <= ZERO:
        raise CalculationError("GORDON_RATE_OR_GROWTH_DOMAIN")
    periods = integer(row["forecastPeriods"], minimum=1)
    if periods > 1000:
        raise CalculationError("TERMINAL_HORIZON_TOO_LONG")
    if config["terminalMethod"] != "GORDON_FCFF":
        raise CalculationError("TERMINAL_VARIANT_CONFIG_CONFLICT")
    with localcontext() as ctx:
        ctx.prec = REFERENCE_PRECISION
        next_fcff = fcff * (ONE + growth)
        terminal = next_fcff / (wacc - growth)
        pv = terminal / ((ONE + wacc) ** periods)
        return {"currency": currency, "forecastPeriods": periods,
                "nextPeriodFCFF": _out(next_fcff),
                "terminalAtForecastHorizon": _out(terminal),
                "presentValueOfTerminal": _out(pv),
                "classification": "GORDON_FCFF_REFERENCE_NOT_FINANCIAL_S2"}
