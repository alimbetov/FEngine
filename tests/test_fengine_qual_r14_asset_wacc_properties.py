"""QUAL-R1.4: seeded independent amortization and WACC capital structure tests."""
from __future__ import annotations

import random
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from qualification_r13_precision import independent_decimal_precision

ROOT=Path(__file__).resolve().parents[1]
SEED_ASSET=0xA5511403
SEED_WACC=0xCAC11404
ASSET_CASES=72
WACC_CASES=120
METHODS=("STRAIGHT_LINE","DECLINING_BALANCE","DOUBLE_DECLINING",
         "SUM_OF_YEARS_DIGITS","UNITS_OF_PRODUCTION")
VARIANTS=("MARKET_VALUE_WACC","TARGET_WEIGHT_WACC")
EPS=Decimal("1e-23")


def d(x):
    return Decimal(str(x))


def near(test,actual,expected,label):
    test.assertLessEqual(abs(d(actual)-d(expected)),EPS,
                         f"QUAL_R14_INVARIANT_MISMATCH: {label}, "
                         f"{actual} vs {expected}")


def independent_depreciation(cost,residual,n,variant,production):
    with localcontext() as ctx:
        ctx.prec=70
        basis=cost-residual
        balance=cost
        charges=[]
        total_units=sum(production,d(0))
        for k in range(n):
            if variant=="STRAIGHT_LINE":
                expected=basis/n
            elif variant=="DECLINING_BALANCE":
                expected=balance*d("0.4")
            elif variant=="DOUBLE_DECLINING":
                expected=balance*d(2)/n
            elif variant=="SUM_OF_YEARS_DIGITS":
                expected=basis*d(n-k)/d(n*(n+1)//2)
            else:
                expected=basis*production[k]/total_units
            expected=max(d(0),min(expected,balance-residual))
            if k==n-1 and variant in ("DECLINING_BALANCE","DOUBLE_DECLINING"):
                expected=balance-residual
            charges.append(expected)
            balance-=expected
        return charges,balance


class QualR14AssetCapitalProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=ReferenceEngine(ROOT)

    @independent_decimal_precision
    def test_360_asset_depreciation_schedules_conserve_acquisition_cost(self):
        rng=random.Random(SEED_ASSET)
        count=0
        for index in range(ASSET_CASES):
            cost=d(rng.randrange(100,100000))/10
            residual=cost*d(rng.randrange(0,50))/100
            periods=rng.randrange(2,10)
            production=[d(rng.randrange(1,200)) for _ in range(periods)]
            for variant in METHODS:
                with self.subTest(seed=SEED_ASSET,index=index,variant=variant):
                    cfg={"residualValue":str(residual),
                         "usefulLifePeriods":periods}
                    inp={"cost":str(cost)}
                    if variant=="DECLINING_BALANCE":
                        cfg.update({"decliningRate":"0.4",
                                    "terminalTrueUpPolicy":"FINAL_PERIOD"})
                    elif variant=="UNITS_OF_PRODUCTION":
                        cfg["estimatedTotalProduction"]=str(sum(production,d(0)))
                        inp["production"]=[str(x) for x in production]
                    rows=self.engine.calculate(
                        "HC.ASSET.01",variant,inp,cfg,reference_mode=True
                    ).output
                    reference,balance=independent_depreciation(
                        cost,residual,periods,variant,production
                    )
                    self.assertEqual(len(rows["periods"]),periods)
                    running=cost
                    for k,(row,expected) in enumerate(zip(rows["periods"],reference)):
                        near(self,row["depreciation"],expected,
                             f"period {k} {variant}")
                        running-=d(row["depreciation"])
                        near(self,row["closingBalance"],running,
                             "per-period acquisition-balance reconciliation")
                        self.assertGreaterEqual(d(row["closingBalance"]),residual-EPS)
                    near(self,rows["closingBalance"],balance,"closing residual")
                    near(self,rows["totalDepreciation"],cost-residual,
                         "total depreciable basis")
                    near(self,
                         sum((d(v["depreciation"]) for v in rows["periods"]),d(0))
                         +d(rows["closingBalance"]),cost,
                         "cost conservation")
                    count+=1
        self.assertEqual(count,ASSET_CASES*len(METHODS))

    @independent_decimal_precision
    def test_240_wacc_capital_weights_tax_and_scaling_invariants(self):
        rng=random.Random(SEED_WACC)
        count=0
        for index in range(WACC_CASES):
            equity=d(rng.randrange(1,20000))/10
            debt=d(rng.randrange(1,20000))/10
            ke=d(rng.randrange(10,450))/1000
            kd=d(rng.randrange(10,200))/1000
            tax=d(rng.randrange(0,501))/1000
            params={
                "equityValue":str(equity),"debtValue":str(debt),
                "costOfEquity":str(ke),"costOfDebt":str(kd),
                "taxRate":str(tax),
            }
            with localcontext() as ctx:
                ctx.prec=70
                independent=(equity*ke + debt*kd*(1-tax))/(equity+debt)
            for variant in VARIANTS:
                with self.subTest(seed=SEED_WACC,index=index,variant=variant):
                    out=self.engine.calculate(
                        "HC.CAP.02",variant,params,{},reference_mode=True
                    ).output
                    near(self,out["wacc"],independent,
                         f"WACC independent weighted capital {variant}")
                    # Scale book capital without changing capital ratios.
                    scaled={**params,"equityValue":str(equity*7),
                            "debtValue":str(debt*7)}
                    other=self.engine.calculate(
                        "HC.CAP.02",variant,scaled,{},reference_mode=True
                    ).output
                    near(self,other["wacc"],independent,
                         f"WACC scaling {variant}")
                    # Greater corporate tax cannot increase a positive-debt
                    # after-tax WACC when debt cost is nonnegative.
                    higher=self.engine.calculate(
                        "HC.CAP.02",variant,{**params,"taxRate":"1"},
                        {},reference_mode=True
                    ).output
                    self.assertLessEqual(d(higher["wacc"]),d(out["wacc"])+EPS)
                    count+=1
        self.assertEqual(count,WACC_CASES*len(VARIANTS))

    @independent_decimal_precision
    def test_asset_and_capital_domain_fail_closed_not_plausible_number(self):
        with self.assertRaises(CalculationError) as exc:
            self.engine.calculate(
                "HC.ASSET.01","UNITS_OF_PRODUCTION",
                {"cost":"500","production":["10","20"]},
                {"residualValue":"100","usefulLifePeriods":2,
                 "estimatedTotalProduction":"100"},
                reference_mode=True,
            )
        self.assertEqual(exc.exception.code,"INVALID_PRODUCTION_COVERAGE")
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                with self.assertRaises(CalculationError) as err:
                    self.engine.calculate(
                        "HC.CAP.02",variant,{
                            "equityValue":"0","debtValue":"0",
                            "costOfEquity":"0.1","costOfDebt":"0.05",
                            "taxRate":"0.2",
                        },{},reference_mode=True,
                    )
                self.assertEqual(err.exception.code,"INVALID_CAPITAL_WEIGHTS")

if __name__=="__main__":
    unittest.main()
