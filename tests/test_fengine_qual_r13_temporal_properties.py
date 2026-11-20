"""QUAL-R1.3 deterministic temporal property and metamorphic portfolio checks.

Independent numeric reference values come from original synthetic atomic facts:
SUM of individual money flows, ratio of independent component totals, the
last AS_OF snapshot per leaf, weighted rate and reexecuted discounted windows.
This suite NEVER uses a returned bucket as the oracle for its full-range total.
"""
from __future__ import annotations

import random
import unittest
from datetime import date, timedelta
from decimal import Decimal, localcontext
from pathlib import Path

from tase import Catalog, Dataset, Observation, PeriodRequest, TaseError, calculate
from tase import (
    ModelTemporalRegistryV11, ModelTemporalRegistryV12,
    calculate_model_temporal_v11, calculate_model_temporal_v12,
)
from test_model_temporal_capability_v11 import npv as v11_npv, request as v11_request
from test_model_temporal_capability_v12 import (
    capm as v12_capm, dated as v12_dated, request as v12_request,
)

ROOT=Path(__file__).resolve().parents[1]
SEED_TEMP=0x7A531305
SCOPE="qual-r13:synthetic-only"
MONTH_STARTS=tuple(date(2026,m,1) for m in range(1,13))+(date(2027,1,1),)
EPS=Decimal("1e-28")


def dec(value):
    return Decimal(str(value))


def exact(testcase, actual, expected, *, eps=EPS, scenario=""):
    testcase.assertLessEqual(
        abs(dec(actual)-dec(expected)),eps,
        msg=f"QUAL_R13_TEMPORAL_MISMATCH {scenario}: "
            f"actual={actual} expected={expected}",
    )


def fact(code,value,start,end,branch):
    return Observation(
        product="FIN",metric=code,scope=SCOPE,start=start,end=end,
        value=str(value),unit="KZT",source_sha="c"*64,
        dimensions=(("branch",branch),),
    )


def request(metric, operation, grain, *, group_by=(), start=MONTH_STARTS[0],
            end=MONTH_STARTS[-1],source_grain="MONTH"):
    return PeriodRequest(
        product="FIN",metric=metric,operation=operation,scope=SCOPE,
        start=start,end=end,grain=grain,source_grain=source_grain,
        group_by=group_by,require_full_coverage=True,include_total=True,
    )


def dataset(rows, watermark=MONTH_STARTS[-1]):
    return Dataset(
        scope=SCOPE,content_sha="d"*64,rows=tuple(rows),
        interval_coverage_attested=True,
        complete_event_stream=True,watermark=watermark,
    )


class QualR13TemporalProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=Catalog.load(ROOT,reference_mode=True)
        cls.registry11=ModelTemporalRegistryV11.load(ROOT,reference_mode=True)
        cls.registry12=ModelTemporalRegistryV12.load(ROOT,reference_mode=True)

    def test_120_month_quarter_year_sums_independent_original_atomic_facts(self):
        rng=random.Random(SEED_TEMP)
        count=0
        for index in range(40):
            branches=("A","B","C")
            rows=[]
            values={branch:[] for branch in branches}
            for month,(begin,end) in enumerate(zip(MONTH_STARTS,MONTH_STARTS[1:])):
                for branch in branches:
                    val=dec(rng.randrange(-50000,100000))/100
                    rows.append(fact("REVENUE",val,begin,end,branch))
                    values[branch].append(val)
            ds=dataset(rows)
            for grain in ("MONTH","QUARTER","YEAR"):
                with self.subTest(seed=SEED_TEMP,index=index,grain=grain):
                    result=calculate(self.catalog,request(
                        "REVENUE","SUM",grain,group_by=("branch",)
                    ),ds)
                    periods=1 if grain=="YEAR" else 4 if grain=="QUARTER" else 12
                    self.assertEqual(len(result.rows),periods*3)
                    self.assertEqual(len(result.total_rows),3)
                    for row in result.rows:
                        branch=row.group[0][1]
                        expected=sum((
                            value for m,value in enumerate(values[branch])
                            if row.start<=MONTH_STARTS[m]<row.end
                        ),dec(0))
                        exact(self,row.value,expected,
                              scenario=f"sum {index} {branch} {grain} {row.start}")
                    for row in result.total_rows:
                        branch=row.group[0][1]
                        exact(self,row.value,sum(values[branch],dec(0)),
                              scenario=f"grand total {index} {branch} {grain}")
                    count+=1
        self.assertEqual(count,120)

    def test_90_ratio_month_quarter_year_recompute_from_components(self):
        rng=random.Random(SEED_TEMP ^ 0x524154)
        count=0
        for index in range(30):
            rows=[]
            gross={};revenue={}
            for m,(start,end) in enumerate(zip(MONTH_STARTS,MONTH_STARTS[1:])):
                for branch in ("A","B"):
                    val=dec(rng.randrange(100,20000))/10
                    profit=val*dec(rng.randrange(1,95))/100
                    rows.append(fact("REVENUE",val,start,end,branch))
                    rows.append(fact("GROSS_PROFIT",profit,start,end,branch))
                    revenue[m,branch]=val
                    gross[m,branch]=profit
            ds=dataset(rows)
            for grain in ("MONTH","QUARTER","YEAR"):
                with self.subTest(seed=SEED_TEMP,index=index,grain=grain):
                    out=calculate(self.catalog,request(
                        "GROSS_MARGIN","RATIO_OF_SUMS",grain
                    ),ds)
                    for b in out.rows:
                        months=[m for m in range(12)
                                if b.start<=MONTH_STARTS[m]<b.end]
                        numerator=sum(
                            (gross[m,branch] for m in months for branch in ("A","B")),
                            dec(0),
                        )
                        denominator=sum(
                            (revenue[m,branch] for m in months for branch in ("A","B")),
                            dec(0),
                        )
                        with localcontext() as ctx:
                            ctx.prec=65
                            expected=numerator/denominator
                        exact(self,b.value,expected,
                              scenario=f"ratio {index} {grain} {b.start}")
                    with localcontext() as ctx:
                        ctx.prec=65
                        whole=sum(gross.values(),dec(0))/sum(revenue.values(),dec(0))
                    exact(self,out.total_rows[0].value,whole,
                          scenario=f"source-components grand margin {index} {grain}")
                    count+=1
        self.assertEqual(count,90)

    def test_50_daily_to_monthly_partitions_including_leap_february(self):
        rng=random.Random(SEED_TEMP ^ 0x444159)
        start=date(2028,2,1)
        end=date(2028,3,1)
        self.assertEqual((end-start).days,29)
        count=0
        for index in range(50):
            rows=[]
            full=dec(0)
            for i in range((end-start).days):
                begin=start+timedelta(days=i)
                value=dec(rng.randrange(-10000,10000))/10
                rows.append(fact("REVENUE",value,begin,begin+timedelta(days=1),"A"))
                full+=value
            ds=dataset(rows,watermark=end)
            monthly=calculate(self.catalog,request(
                "REVENUE","SUM","MONTH",start=start,end=end,source_grain="DAY"
            ),ds)
            daily=calculate(self.catalog,request(
                "REVENUE","SUM","DAY",start=start,end=end,source_grain="DAY"
            ),ds)
            exact(self,monthly.total_rows[0].value,full,
                  scenario=f"leap February {index}")
            self.assertEqual(len(daily.rows),29)
            exact(self,daily.total_rows[0].value,full,
                  scenario=f"daily partition {index}")
            self.assertEqual(len(monthly.rows),1)
            count+=1
        self.assertEqual(count,50)

    def test_48_temporal_adapter_npv_and_capm_source_derived_totals(self):
        rng=random.Random(SEED_TEMP ^ 0x414450)
        count=0
        mstarts=(date(2026,1,1),date(2026,2,1),date(2026,3,1),date(2026,4,1))
        for index in range(24):
            p=dec(rng.randrange(100,2000))
            a=dec(rng.randrange(100,2000))
            b=dec(rng.randrange(100,2000))
            r=dec(rng.randrange(5,350))/1000
            runs=[v11_npv(begin,end,amount,rate=str(r)) for
                  (begin,end),amount in zip(zip(mstarts,mstarts[1:]),(-p,a,b))]
            req=v11_request(
                "HC.DCF.01","PERIOD_END_NPV","npv",output_grain="QUARTER"
            )
            result=calculate_model_temporal_v11(
                self.registry11,req,runs,reference_mode=True,
            )
            with localcontext() as ctx:
                ctx.prec=65
                expected=-p+a/(1+r)+b/(1+r)**2
            exact(self,result.result.total_rows[0].value,expected,
                  scenario=f"V11 full-range independent NPV {index}")
            self.assertEqual(
                result.result.rows[0].value,
                result.result.total_rows[0].value,
            )
            count+=1
            when=(date(2026,1,15),date(2026,2,15),date(2026,3,15))
            beta=[dec(rng.randrange(0,260))/100 for _ in when]
            weight=[dec(rng.randrange(1,1000)) for _ in when]
            capm_runs=[v12_capm(t,str(bb),str(w)) for t,bb,w in zip(
                when,beta,weight
            )]
            creq=v12_request(
                "HC.CAP.01","CAPM_BASE","costOfEquity",
                output_grain="QUARTER"
            )
            actual=calculate_model_temporal_v12(
                self.registry12,creq,capm_runs,reference_mode=True,
            )
            with localcontext() as ctx:
                ctx.prec=65
                independent=sum((
                    (dec("0.02")+bb*dec("0.06"))*w for bb,w in zip(beta,weight)
                ),dec(0))/sum(weight)
            exact(self,actual.result.total_rows[0].value,independent,
                  scenario=f"V12 exposure-weighted CAPM {index}")
            count+=1
        self.assertEqual(count,48)

    def test_24_dated_xnpv_actual_day_exponents_and_same_origin(self):
        rng=random.Random(SEED_TEMP ^ 0x584E50)
        count=0
        for index in range(24):
            dates=(date(2026,1,1),date(2026,2,12),date(2026,3,18))
            amounts=(-dec(rng.randrange(100,2000)),
                     dec(rng.randrange(100,2000)),
                     dec(rng.randrange(100,2000)))
            rate=dec(rng.randrange(1,230))/1000
            runs=[v12_dated(at,amount,rate=str(rate)) for at,amount
                  in zip(dates,amounts)]
            req=v12_request(
                "HC.DCF.02","EXACT_DATE_XNPV","xnpv",
                output_grain="QUARTER"
            )
            out=calculate_model_temporal_v12(
                self.registry12,req,runs,reference_mode=True,
            )
            with localcontext() as ctx:
                ctx.prec=65
                independent=sum((
                    amount/(1+rate)**(
                        dec((when-dates[0]).days)/365
                    ) for amount,when in zip(amounts,dates)
                ),dec(0))
            exact(self,out.result.total_rows[0].value,independent,
                  scenario=f"V12 dated independent XNPV {index}")
            self.assertEqual(out.result.rows[0].value,
                             out.result.total_rows[0].value)
            count+=1
        self.assertEqual(count,24)

    def test_adversarial_branch_loss_rejected_in_all_year_views(self):
        # No silent incomplete full-year total if branch B is absent in June.
        rows=[]
        for m,(start,end) in enumerate(zip(MONTH_STARTS,MONTH_STARTS[1:])):
            for branch in ("A","B"):
                if branch=="B" and m==5:
                    continue
                rows.append(fact("REVENUE","100",start,end,branch))
        for grain in ("MONTH","QUARTER"):
            with self.subTest(grain=grain):
                with self.assertRaises(TaseError) as error:
                    calculate(self.catalog,request(
                        "REVENUE","SUM",grain
                    ),dataset(rows))
                self.assertEqual(error.exception.code,
                                 "PARTIAL_COHORT_COVERAGE")


if __name__=="__main__":
    unittest.main()
