"""QUAL-R1.3: deterministic property/metamorphic tests for IRR/EIR and risk tails.

Financial oracles use independently constructed algebraic roots, discounted
one-cashflow EIR identities and discrete quantile/tail integration. No calls
to FEngine helper math functions to obtain expected outputs.
"""
from __future__ import annotations

import random
import unittest
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING, localcontext
from pathlib import Path

from fengine_hc.reference import ReferenceEngine, CalculationError

ROOT = Path(__file__).resolve().parents[1]
SEED_ROOT = 0x1AA13003
SEED_RISK = 0xAB131304
IRR_SIMPLE_CASES = 80
IRR_MULTIPLE_CASES = 56
IRR_TANGENT_CASES = 16
EIR_CASES = 80
RISK_CASES = 80


def as_decimal(x):
    return Decimal(str(x))


def near(testcase, actual, expected, *, eps="1e-20", location=""):
    testcase.assertLessEqual(
        abs(as_decimal(actual) - as_decimal(expected)), Decimal(eps),
        msg=f"QUAL_R13_ROOT_OR_RISK_MISMATCH {location}: "
            f"actual={actual} expected={expected}",
    )


def irr_cfg():
    return {"rootDomain":{"minRate":"-0.9","maxRate":"5"},
            "rootCompletenessPolicy":"CERTIFIED_ALL"}


def simple_cases():
    randoms=random.Random(SEED_ROOT)
    for index in range(IRR_SIMPLE_CASES):
        principal=as_decimal(randoms.randrange(300,100000))/10
        rate=as_decimal(randoms.randrange(-650,1501))/1000
        proceeds=principal*(1+rate)
        yield index,rate,[str(-principal),str(proceeds)]


def multiple_cases():
    randoms=random.Random(SEED_ROOT ^ 0x4D554C54)
    for index in range(IRR_MULTIPLE_CASES):
        principal=as_decimal(randoms.randrange(1000,10000))
        rate1=as_decimal(randoms.randrange(-300,400))/1000
        rate2=rate1 + as_decimal(randoms.randrange(80,500))/1000
        # -P + P*(2+r1+r2)/(1+r) - P*(1+r1)*(1+r2)/(1+r)^2 = 0
        cf=[-principal,principal*(2+rate1+rate2),
            -principal*(1+rate1)*(1+rate2)]
        yield index,rate1,rate2,[str(v) for v in cf]


class QualR13RootRiskPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=ReferenceEngine(ROOT)

    def calc(self,model,variant,inputs,config):
        return self.engine.calculate(
            model,variant,inputs,config,reference_mode=True,
        ).output

    def test_160_independent_single_periodic_irr_roots(self):
        count=0
        for index,rate,flows in simple_cases():
            for variant in ("ALL_REAL_IRR_ROOTS","SINGLE_IF_UNAMBIGUOUS"):
                with self.subTest(seed=SEED_ROOT,index=index,variant=variant):
                    out=self.calc(
                        "HC.DCF.03",variant,{"cashflows":flows},irr_cfg(),
                    )
                    self.assertEqual(out["rootCount"],1)
                    near(self,out["roots"][0],rate,
                         location=f"IRR simple {index} {variant}")
                    # Oracle is a rearranged single-receipt equation.
                    p=-as_decimal(flows[0])
                    near(self,p*(1+as_decimal(out["roots"][0])),
                         as_decimal(flows[1]),eps="1e-16",
                         location="cash present-value identity")
                    count+=1
        self.assertEqual(count,IRR_SIMPLE_CASES*2)

    def test_56_two_root_irr_algebraic_goldens_and_single_refusal(self):
        count=0
        for index,r1,r2,flows in multiple_cases():
            with self.subTest(seed=SEED_ROOT,index=index):
                out=self.calc(
                    "HC.DCF.03","ALL_REAL_IRR_ROOTS",
                    {"cashflows":flows},irr_cfg(),
                )
                self.assertEqual(out["rootCount"],2)
                near(self,out["roots"][0],r1,
                     location=f"first real IRR root {index}")
                near(self,out["roots"][1],r2,
                     location=f"second real IRR root {index}")
                with self.assertRaises(CalculationError) as exc:
                    self.calc(
                        "HC.DCF.03","SINGLE_IF_UNAMBIGUOUS",
                        {"cashflows":flows},irr_cfg(),
                    )
                self.assertEqual(exc.exception.code,"MULTIPLE_IRR_ROOTS")
                count+=1
        self.assertEqual(count,IRR_MULTIPLE_CASES)

    def test_16_tangent_irr_roots_are_not_double_counted(self):
        randoms=random.Random(SEED_ROOT ^ 0x54414E47)
        count=0
        for index in range(IRR_TANGENT_CASES):
            principal=as_decimal(randoms.randrange(100,4000))
            rate=as_decimal(randoms.randrange(-250,850))/1000
            flows=[str(-principal),str(2*principal*(1+rate)),
                   str(-principal*(1+rate)**2)]
            with self.subTest(seed=SEED_ROOT,index=index):
                out=self.calc(
                    "HC.DCF.03","ALL_REAL_IRR_ROOTS",
                    {"cashflows":flows},irr_cfg(),
                )
                self.assertEqual(out["rootCount"],1)
                near(self,out["roots"][0],rate,
                     location=f"tangent IRR {index}")
                count+=1
        self.assertEqual(count,IRR_TANGENT_CASES)

    def test_80_irregular_calendar_eir_reproduces_closed_form_annual_rate(self):
        randoms=random.Random(SEED_ROOT ^ 0x454952)
        origin=date(2026,1,1)
        count=0
        for index in range(EIR_CASES):
            with localcontext() as ctx:
                ctx.prec=65
                principal=as_decimal(randoms.randrange(1000,20000))/10
                rate=as_decimal(randoms.randrange(-350,701))/1000
                days=randoms.choice((31,93,181,365,366,400,730))
                end=origin+timedelta(days=days)
                # Independent inverse of the ACT/365 XNPV zero equation.
                proceeds=principal*(1+rate)**(as_decimal(days)/365)
            with self.subTest(seed=SEED_ROOT,index=index,days=days):
                out=self.calc(
                    "HC.LOAN.03","EIR_ORIGINAL",
                    {"cashflows":[
                        {"date":origin.isoformat(),"amount":str(-principal)},
                        {"date":end.isoformat(),"amount":str(proceeds)},
                    ]},
                    {"discountOrigin":origin.isoformat(),
                     "rootCompletenessPolicy":"CERTIFIED_ALL"},
                )
                near(self,out["effectiveRate"],rate,eps="1e-18",
                     location=f"EIR {index} days={days}")
                count+=1
        self.assertEqual(count,EIR_CASES)

    def test_160_empirical_var_es_match_independent_sample_oracles(self):
        rng=random.Random(SEED_RISK)
        count=0
        for index in range(RISK_CASES):
            sample=[as_decimal(rng.randrange(0,4000))/10
                    for _ in range(rng.randrange(4,22))]
            alpha=as_decimal(rng.randrange(5,20))/20  # exact multiples .05
            ordered=sorted(sample)
            rank=int((alpha*len(ordered)).to_integral_value(
                rounding=ROUND_CEILING
            ))
            reference_var=ordered[rank-1]
            with localcontext() as ctx:
                ctx.prec=65
                mass=(1-alpha)*len(ordered)
                whole=int(mass)
                fraction=mass-whole
                # Python [-0:] selects the ENTIRE list. For a tail
                # smaller than one sample, the independent reference must
                # contain only the fractional highest loss, not all losses.
                fully_selected=ordered[-whole:] if whole else []
                fractional_loss=ordered[-whole-1] if fraction else Decimal(0)
                reference_es=(
                    sum(fully_selected,Decimal(0))+
                    fractional_loss*fraction
                )/mass
            with self.subTest(seed=SEED_RISK,index=index,alpha=str(alpha)):
                var=self.calc(
                    "HC.RISK.02","EMPIRICAL_LEFT_QUANTILE",
                    {"losses":[str(x) for x in sample]},
                    {"alpha":str(alpha),
                     "lossSignPolicy":"POSITIVE_LOSS",
                     "quantileDefinition":"NEAREST_RANK"},
                )
                es=self.calc(
                    "HC.RISK.03","QUANTILE_INTEGRAL_ES",
                    {"losses":[str(x) for x in sample]},
                    {"confidenceAlpha":str(alpha),
                     "esTailMassRule":"QUANTILE_INTEGRAL_FRACTIONAL_ATOM"},
                )
                self.assertEqual(as_decimal(var["valueAtRisk"]),reference_var)
                near(self,es["expectedShortfall"],reference_es,
                     eps="1e-26",location=f"ES {index}")
                # Upper tail expectation cannot be smaller than its
                # quantile threshold (for nonnegative loss convention).
                self.assertGreaterEqual(
                    as_decimal(es["expectedShortfall"]),
                    as_decimal(var["valueAtRisk"]),
                )
                count+=2
        self.assertEqual(count,2*RISK_CASES)

    def test_closed_nonconventional_eir_and_no_irr_roots(self):
        with self.assertRaises(CalculationError) as exc:
            self.calc(
                "HC.LOAN.03","EIR_ORIGINAL",
                {"cashflows":[
                    {"date":"2026-01-01","amount":"-100"},
                    {"date":"2027-01-01","amount":"110"},
                    {"date":"2028-01-01","amount":"-20"},
                ]},
                {"discountOrigin":"2026-01-01",
                 "rootCompletenessPolicy":"CERTIFIED_ALL"},
            )
        self.assertEqual(exc.exception.code,"EIR_NONCONVENTIONAL_CASHFLOWS")


if __name__=="__main__":
    unittest.main()
