"""HC-R0.2B — real bounded Decimal mathematical reference primitives.

Not IFRS 9 financial qualification, statutory EIR, market risk model approval,
or evidence of source authority. No float, no arbitrary Python eval.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext
from typing import Any, Mapping

from .reference import CalculationError, day, number, _rate, _req, xnpv

ZERO, ONE = Decimal(0), Decimal(1)
# Fixed, versioned numerical reference policy. Rust must reproduce this.
ROOT_TOLERANCE = Decimal("1e-30")
ROOT_PRECISION = 55


def _polynomial(coeff: tuple[Decimal, ...], x: Decimal) -> Decimal:
    v = ZERO
    for c in reversed(coeff):
        v = v * x + c
    return v


def _bisect(f, left: Decimal, right: Decimal) -> Decimal:
    fl = f(left)
    fr = f(right)
    if fl == 0:
        return left
    if fr == 0:
        return right
    if (fl < 0) == (fr < 0):
        raise CalculationError("ROOT_NOT_BRACKETED")
    for _ in range(240):
        middle = (left + right) / 2
        fm = f(middle)
        if fm == 0 or right - left <= ROOT_TOLERANCE:
            return middle
        if (fm < 0) == (fl < 0):
            left, fl = middle, fm
        else:
            right, fr = middle, fm
    raise CalculationError("ROOT_SOLVER_DID_NOT_CONVERGE")


def _poly_real_roots_in_domain(coefs: tuple[Decimal, ...],
                               left: Decimal, right: Decimal) -> tuple[Decimal, ...]:
    """Isolate every real polynomial root inside a finite interval by recursive
    derivative critical points and monotonic intervals, including tangent roots.
    This is *not* a whole-domain IRR guarantee without the specified bounds.
    """
    if len(coefs) == 1:
        if coefs[0] == 0:
            raise CalculationError("INDETERMINATE_ROOTS")
        return ()
    if len(coefs) == 2:
        r = -coefs[0] / coefs[1]
        return (r,) if left <= r <= right else ()
    deriv = tuple(Decimal(i) * v for i, v in enumerate(coefs[1:], start=1))
    crits = _poly_real_roots_in_domain(deriv, left, right)
    cuts = (left,) + crits + (right,)
    f = lambda x: _polynomial(coefs, x)
    scale = max(ONE, *(abs(c) for c in coefs))
    roots: list[Decimal] = []
    for c in cuts:
        # Tiny *relative* residual allows stationary/tangent roots at Decimal
        # bisection limits. A separate independent golden must validate cases.
        if abs(f(c)) <= scale * Decimal("1e-26"):
            roots.append(c)
    for a, b in zip(cuts, cuts[1:]):
        if a < b and f(a) * f(b) < 0:
            roots.append(_bisect(f, a, b))
    roots.sort()
    dedup: list[Decimal] = []
    for r in roots:
        if not dedup or abs(r - dedup[-1]) > Decimal("1e-21"):
            dedup.append(r)
    return tuple(dedup)


def all_periodic_irr(cashflows: Any, min_rate: Any, max_rate: Any) -> tuple[Decimal, ...]:
    if not isinstance(cashflows, (list, tuple)) or len(cashflows) < 2 or len(cashflows) > 32:
        raise CalculationError("IRR_CASHFLOW_LENGTH_OUT_OF_RANGE")
    vals = [number(v) for v in cashflows]
    if not any(x < 0 for x in vals) or not any(x > 0 for x in vals):
        raise CalculationError("IRR_REQUIRES_OPPOSING_SIGNS")
    lo, hi = _rate(min_rate), _rate(max_rate)
    if hi <= lo or hi > 1000:
        raise CalculationError("INVALID_ROOT_DOMAIN")
    with localcontext() as ctx:
        ctx.prec = ROOT_PRECISION
        # r > -1 => q = 1/(1+r); polynomial in q with finite positive bounds.
        q_lo, q_hi = ONE / (ONE + hi), ONE / (ONE + lo)
        while vals[-1] == 0:
            vals.pop()
        roots = _poly_real_roots_in_domain(tuple(vals), q_lo, q_hi)
        return tuple(sorted((+(ONE / q - ONE) for q in roots)))


def dated_eir_single_sign_change(flows: Any, origin: Any) -> Decimal:
    """Monotonic all-positive future receipts from one negative origination flow.
    EIR numerical *root only*: no IFRS fee eligibility or cashflow admission.
    Search is explicitly bounded to [-0.99,100], not all possible real rates.
    """
    d0 = day(origin)
    if not isinstance(flows, (list, tuple)) or not (2 <= len(flows) <= 1024):
        raise CalculationError("EIR_CASHFLOWS_REQUIRED")
    data = []
    for row in flows:
        if not isinstance(row, Mapping) or set(row) != {"date", "amount"}:
            raise CalculationError("EIR_FLOW_SCHEMA")
        data.append((day(row["date"]), number(row["amount"])))
    if data[0][0] != d0 or data[0][1] >= 0 or any(
        d <= d0 or value < 0 for d, value in data[1:]
    ) or not any(value > 0 for _, value in data[1:]):
        raise CalculationError("EIR_NONCONVENTIONAL_CASHFLOWS")
    if any(data[i][0] > data[i+1][0] for i in range(len(data)-1)):
        raise CalculationError("EIR_DATES_NOT_ORDERED")
    with localcontext() as ctx:
        ctx.prec = ROOT_PRECISION
        f = lambda r: xnpv([{"date": d.isoformat(), "amount": format(v, "f")}
                            for d, v in data], r, d0)
        l, h = Decimal("-0.99"), Decimal("100")
        if f(l) * f(h) > 0:
            raise CalculationError("EIR_ROOT_OUTSIDE_REFERENCE_DOMAIN")
        return +_bisect(f, l, h)


def _loss_sample(sample: Any) -> list[Decimal]:
    if not isinstance(sample, (list, tuple)) or len(sample) < 2:
        raise CalculationError("RISK_SAMPLE_TOO_SMALL")
    if len(sample) > 1_000_000:
        raise CalculationError("RISK_SAMPLE_TOO_LARGE")
    values = [number(v) for v in sample]
    if any(v < 0 for v in values):
        raise CalculationError("NEGATIVE_LOSS_VALUE")
    return sorted(values)


def empirical_var(losses: Any, confidence: Any) -> Decimal:
    sample = _loss_sample(losses)
    alpha = number(confidence)
    if not ZERO < alpha < ONE:
        raise CalculationError("INVALID_CONFIDENCE")
    # Nearest-rank empirical quantile, upper LOSS tail.
    k = (alpha * len(sample)).to_integral_value(rounding="ROUND_CEILING")
    return sample[int(k) - 1]


def empirical_es(losses: Any, confidence: Any) -> Decimal:
    sample = _loss_sample(losses)
    alpha = number(confidence)
    if not ZERO < alpha < ONE:
        raise CalculationError("INVALID_CONFIDENCE")
    with localcontext() as ctx:
        ctx.prec = 40
        mass = (ONE - alpha) * Decimal(len(sample))
        remaining = mass
        tail_total = ZERO
        for value in reversed(sample):
            if remaining <= 0:
                break
            weight = min(ONE, remaining)
            tail_total += value * weight
            remaining -= weight
        if remaining != 0:
            raise CalculationError("ES_TAIL_MASS_MISMATCH")
        return +(tail_total / mass)


def _year_later(start: date) -> date:
    try:
        return start.replace(year=start.year + 1)
    except ValueError:
        return start.replace(year=start.year + 1, day=28)


def expected_loss(events: Any, as_of: Any, annual_eir: Any, *, lifetime: bool) -> dict[str, Any]:
    """Probability-weighted discounted loss reference.

    12-month version: events represent defaults ONLY in the first year; later
    loss settlement dates are allowed. Lifetime version: conditional period PD
    is converted to marginal PD via survival recursion. No credit-stage
    classification, scenario macro weights, or regulatory approval is inferred.
    """
    origin = day(as_of)
    r = _rate(annual_eir)
    if not isinstance(events, (list, tuple)) or not events:
        raise CalculationError("ECL_EVENTS_REQUIRED")
    if len(events) > 4096:
        raise CalculationError("ECL_TOO_MANY_EVENTS")
    survival, total = ONE, ZERO
    previous = origin
    rows = []
    with localcontext() as ctx:
        ctx.prec = 40
        for ev in events:
            if not isinstance(ev, Mapping):
                raise CalculationError("ECL_EVENT_SCHEMA")
            expected = {"defaultDate", "lossDate", "exposure", "lgd", "pd"}
            if set(ev) != expected:
                raise CalculationError("ECL_EVENT_SCHEMA")
            default_at, settlement = day(ev["defaultDate"]), day(ev["lossDate"])
            if default_at <= previous or settlement < default_at:
                raise CalculationError("ECL_DATE_ORDER")
            if not lifetime and default_at > _year_later(origin):
                raise CalculationError("DEFAULT_OUTSIDE_12M_WINDOW")
            previous = default_at
            pd, lgd, exposure = number(ev["pd"]), number(ev["lgd"]), number(ev["exposure"])
            if not ZERO <= pd <= ONE or not ZERO <= lgd <= ONE or exposure < 0:
                raise CalculationError("ECL_INPUT_OUT_OF_RANGE")
            marginal = survival * pd if lifetime else pd
            if lifetime:
                survival *= (ONE - pd)
            expected_amt = marginal * exposure * lgd
            power = Decimal((settlement - origin).days) / Decimal(365)
            discounted = expected_amt / (ONE + r) ** power
            rows.append({"defaultDate": default_at.isoformat(),
                         "marginalPd": format(marginal, "f"),
                         "discountedLoss": format(discounted, "f")})
            total += discounted
        if not lifetime and sum((number(e["pd"]) for e in events), ZERO) > ONE:
            raise CalculationError("MARGINAL_PD_SUM_EXCEEDS_ONE")
    return {"expectedCreditLoss": format(+total, "f"), "events": rows,
            "survivalProbability": format(+survival, "f") if lifetime else None}
