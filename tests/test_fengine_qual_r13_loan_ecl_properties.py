"""QUAL-R1.3: 600+ seeded, independently reconstructed loan/ECL cases.

Independent oracles use Decimal arithmetic and closed-form contract identities;
never call fengine_hc math primitives to compute expected outputs.
No external dependencies, nondeterministic inputs, FIN, Redis or Rust.
"""
from __future__ import annotations

import random
import unittest
from datetime import date, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

from qualification_r13_precision import independent_decimal_precision

from fengine_hc.reference import CalculationError, ReferenceEngine

ROOT = Path(__file__).resolve().parents[1]
SEED_LOAN = 0xA0513001
SEED_ECL = 0xEC113002
LOAN_CASES = 64
ECL_CASES_PER_METHOD = 100
LOAN_VARIANTS = (
    "ANNUITY_EQUAL_PAYMENT_DATED",
    "EQUAL_PRINCIPAL_DATED",
    "INTEREST_ONLY_BALLOON",
    "BULLET",
)
EPS = Decimal("1e-25")


def d(x):
    return Decimal(str(x))


def assert_near(case: unittest.TestCase, actual, expected, *, info="", eps=EPS):
    difference = abs(d(actual) - d(expected))
    case.assertLessEqual(difference, eps, msg=(
        f"QUAL_R13_NUMERIC_MISMATCH {info}: delta={difference}; "
        f"expected={expected}; actual={actual}"
    ))


def make_loan_cases():
    rng = random.Random(SEED_LOAN)
    out = []
    origin = date(2026, 1, 1)
    for index in range(LOAN_CASES):
        periods = rng.randrange(2, 7)
        days = [rng.randrange(19, 95) for _ in range(periods)]
        current = origin
        dates = []
        for span in days:
            current += timedelta(days=span)
            dates.append(current)
        amount = d(rng.randrange(500, 20000)) / 10
        rate = d(rng.randrange(1, 310)) / 1000
        out.append((index, amount, rate, origin, dates))
    return out


def independently_derive_amortization(principal, rate, origin, dates, variant):
    # Derive annuity using inverse present value of one-unit dated payments,
    # independently from engine's loop and source SHA implementation.
    with localcontext() as ctx:
        ctx.prec = 65
        periods = [(d - p).days for p, d in
                   zip((origin,) + tuple(dates[:-1]), tuple(dates))]
        factors = [d(1) + rate * d(days) / d(365) for days in periods]
        discount = d(1)
        pv = d(0)
        for factor in factors:
            discount /= factor
            pv += discount
        level_payment = principal / pv
        balance = principal
        cumulative_bullet_interest = d(0)
        rows = []
        for k, factor in enumerate(factors):
            interest = balance * (factor - d(1))
            last = (k == len(factors) - 1)
            if variant == "ANNUITY_EQUAL_PAYMENT_DATED":
                paid_principal = balance if last else level_payment - interest
                payment = paid_principal + interest
            elif variant == "EQUAL_PRINCIPAL_DATED":
                paid_principal = balance if last else principal / len(factors)
                payment = paid_principal + interest
            elif variant == "INTEREST_ONLY_BALLOON":
                paid_principal = balance if last else d(0)
                payment = paid_principal + interest
            elif variant == "BULLET":
                cumulative_bullet_interest += interest
                paid_principal = balance if last else d(0)
                payment = paid_principal + cumulative_bullet_interest if last else d(0)
            else:
                raise AssertionError("UNREGISTERED_VARIANT")
            ending = balance - paid_principal
            rows.append({
                "opening": balance, "interest": interest,
                "principal": paid_principal, "payment": payment,
                "closing": ending,
            })
            balance = ending
        return rows


def make_ecl_cases(lifetime: bool):
    rng = random.Random(SEED_ECL ^ (0x51 if lifetime else 0x12))
    origin = date(2026, 1, 1)
    for index in range(ECL_CASES_PER_METHOD):
        count = rng.randrange(2, 6)
        if lifetime:
            starts = sorted(rng.sample(range(40, 1200), count))
        else:
            starts = sorted(rng.sample(range(10, 335), count))
        rate = d(rng.randrange(0, 301)) / 1000
        events = []
        for days in starts:
            default_at = origin + timedelta(days=days)
            settled_at = default_at + timedelta(days=rng.randrange(0, 490))
            pd = d(rng.randrange(10, 150)) / 1000
            lgd = d(rng.randrange(50, 950)) / 1000
            exposure = d(rng.randrange(1000, 25000)) / 10
            events.append({
                "defaultDate": default_at.isoformat(),
                "lossDate": settled_at.isoformat(),
                "pd": str(pd), "lgd": str(lgd),
                "exposure": str(exposure),
            })
        yield index, origin, rate, events


def independently_derive_ecl(origin, rate, events, lifetime):
    with localcontext() as ctx:
        ctx.prec = 65
        survival = d(1)
        total = d(0)
        marginals = []
        for event in events:
            pd, lgd, exposure = (
                d(event[name]) for name in ("pd", "lgd", "exposure")
            )
            marginal = survival * pd if lifetime else pd
            if lifetime:
                survival *= 1 - pd
            maturity = date.fromisoformat(event["lossDate"])
            years = d((maturity - origin).days) / d(365)
            discounted = (marginal * exposure * lgd) / ((1 + rate) ** years)
            total += discounted
            marginals.append(marginal)
        return +total, +survival, marginals


class QualR13LoanEclPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    @independent_decimal_precision
    def test_256_positive_rate_dated_loan_schedules_and_per_row_oracles(self):
        count = 0
        for index, principal, rate, origin, dates in make_loan_cases():
            values = {
                "principal": str(principal),
                "annualRate": str(rate),
                "startDate": origin.isoformat(),
                "paymentDates": [x.isoformat() for x in dates],
                "dayCount": "ACT_365_FIXED",
            }
            for variant in LOAN_VARIANTS:
                with self.subTest(seed=SEED_LOAN,case=index,variant=variant):
                    out = self.engine.calculate(
                        "HC.LOAN.02",variant,values,{},reference_mode=True,
                    ).output
                    expected = independently_derive_amortization(
                        principal,rate,origin,dates,variant,
                    )
                    self.assertEqual(len(out["schedule"]),len(expected))
                    for idx,(row,reference) in enumerate(zip(out["schedule"],expected)):
                        self.assertEqual(row["date"],dates[idx].isoformat())
                        for field,expect in reference.items():
                            assert_near(
                                self,row[field],expect,
                                info=f"{variant} case={index} row={idx} {field}",
                            )
                        assert_near(
                            self,d(row["opening"])-d(row["principal"]),
                            d(row["closing"]),info="principal continuity",
                        )
                    assert_near(self,
                                sum((d(r["principal"]) for r in out["schedule"]),d(0)),
                                principal,info="original principal conservation")
                    assert_near(self,
                                sum((d(r["interest"]) for r in out["schedule"]),d(0)),
                                out["totalInterest"],info="interest conservation")
                    assert_near(self,
                                sum((d(r["payment"]) for r in out["schedule"]),d(0)),
                                out["totalPayment"],info="cash payment conservation")
                    assert_near(self,out["closingPrincipal"],"0")
                    count+=1
        self.assertEqual(count,LOAN_CASES * len(LOAN_VARIANTS))

    @independent_decimal_precision
    def test_64_loan_principal_scale_metamorphic_relations(self):
        # Fixed source policy, interest rate, dates: linearity in principal.
        count=0
        for index,principal,rate,origin,dates in make_loan_cases()[:16]:
            data={
                "principal":str(principal),"annualRate":str(rate),
                "startDate":origin.isoformat(),
                "paymentDates":[day.isoformat() for day in dates],
                "dayCount":"ACT_365_FIXED",
            }
            for variant in LOAN_VARIANTS:
                with self.subTest(seed=SEED_LOAN,index=index,variant=variant):
                    initial=self.engine.calculate(
                        "HC.LOAN.02",variant,data,{},reference_mode=True,
                    ).output
                    doubled=self.engine.calculate(
                        "HC.LOAN.02",variant,
                        {**data,"principal":str(principal*2)}, {},
                        reference_mode=True,
                    ).output
                    for key in ("totalInterest","totalPayment"):
                        assert_near(self,d(doubled[key]),d(initial[key])*2,
                                    info=f"{variant} principal scaling {key}")
                    count+=1
        self.assertEqual(count,64)

    @independent_decimal_precision
    def test_200_lifetime_and_first_year_ecl_numeric_oracles(self):
        total=0
        for lifetime in (False,True):
            model = "HC.ECL.03" if lifetime else "HC.ECL.02"
            variant = "LIFETIME_TERM_PD" if lifetime else "FIRST_12_MONTH_DEFAULT_EVENTS"
            cfg = {"hazardConditionality":"CONDITIONAL_PD"} if lifetime else {
                "defaultEventWindow":"FIRST_12_MONTHS",
            }
            for index,origin,rate,events in make_ecl_cases(lifetime):
                with self.subTest(seed=SEED_ECL,lifetime=lifetime,index=index):
                    actual=self.engine.calculate(
                        model,variant,{"asOf":origin.isoformat(),
                                       "annualEir":str(rate),"events":events},
                        cfg,reference_mode=True,
                    ).output
                    expected,survival,marginals=independently_derive_ecl(
                        origin,rate,events,lifetime,
                    )
                    assert_near(self,actual["expectedCreditLoss"],expected,
                                info=f"ecl index={index} lifetime={lifetime}")
                    self.assertEqual(len(actual["events"]),len(events))
                    for obs,marginal in zip(actual["events"],marginals):
                        assert_near(self,obs["marginalPd"],marginal,
                                    info=f"marginal pd at {obs['defaultDate']}")
                    if lifetime:
                        assert_near(self,actual["survivalProbability"],survival,
                                    info="conditional survival recursion")
                    else:
                        self.assertIsNone(actual["survivalProbability"])
                    total+=1
        self.assertEqual(total,2*ECL_CASES_PER_METHOD)

    @independent_decimal_precision
    def test_24_ecl_exposure_scale_and_discount_monotonicity(self):
        count=0
        for lifetime in (False,True):
            model="HC.ECL.03" if lifetime else "HC.ECL.02"
            variant="LIFETIME_TERM_PD" if lifetime else "FIRST_12_MONTH_DEFAULT_EVENTS"
            cfg={"hazardConditionality":"CONDITIONAL_PD"} if lifetime else {
                "defaultEventWindow":"FIRST_12_MONTHS",
            }
            for index,origin,rate,events in list(make_ecl_cases(lifetime))[:12]:
                base={"asOf":origin.isoformat(),"annualEir":str(rate),"events":events}
                original=self.engine.calculate(
                    model,variant,base,cfg,reference_mode=True,
                ).output
                doubled=[{**ev,"exposure":str(d(ev["exposure"])*2)} for ev in events]
                scaled=self.engine.calculate(
                    model,variant,{**base,"events":doubled},
                    cfg,reference_mode=True,
                ).output
                assert_near(self,scaled["expectedCreditLoss"],
                            2*d(original["expectedCreditLoss"]),
                            info=f"exposure linearity {lifetime}:{index}")
                rate2=rate + d("0.15")
                discounted=self.engine.calculate(
                    model,variant,{**base,"annualEir":str(rate2)},
                    cfg,reference_mode=True,
                ).output
                self.assertLessEqual(
                    d(discounted["expectedCreditLoss"]),
                    d(original["expectedCreditLoss"]),
                    msg=f"discount rate monotonicity {lifetime}:{index}",
                )
                count+=1
        self.assertEqual(count,24)

    @independent_decimal_precision
    def test_invalid_cases_reject_calendar_and_probability_domain(self):
        baseline={
            "principal":"1000","annualRate":"0.1",
            "startDate":"2026-01-01",
            "paymentDates":["2026-02-01","2026-03-01"],
            "dayCount":"ACT_365_FIXED",
        }
        for variant in LOAN_VARIANTS:
            with self.subTest(variant=variant):
                with self.assertRaises(CalculationError) as ex:
                    self.engine.calculate(
                        "HC.LOAN.02",variant,
                        {**baseline,"paymentDates":["2026-03-01","2026-02-01"]},
                        {},reference_mode=True,
                    )
                self.assertEqual(ex.exception.code,"PAYMENT_DATES_NOT_INCREASING")
        events=[
            {"defaultDate":"2026-03-01","lossDate":"2026-04-01",
             "pd":"0.8","lgd":"0.5","exposure":"100"},
            {"defaultDate":"2026-07-01","lossDate":"2026-08-01",
             "pd":"0.8","lgd":"0.5","exposure":"100"},
        ]
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate(
                "HC.ECL.02","FIRST_12_MONTH_DEFAULT_EVENTS",
                {"asOf":"2026-01-01","annualEir":"0.1","events":events},
                {"defaultEventWindow":"FIRST_12_MONTHS"},reference_mode=True,
            )
        self.assertEqual(ex.exception.code,"MARGINAL_PD_SUM_EXCEEDS_ONE")


if __name__ == "__main__":
    unittest.main()
