"""Optional, product-agnostic interval and semantic grand-total extension.

No runtime data storage. Uses the existing TASE typed metric descriptor for
every admitted product. Calculations only in reference mode, not financial S2.
"""
from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from tase import Catalog, Dataset, Observation, PeriodRequest, TaseError, calculate, compile_plan

ROOT = Path(__file__).resolve().parents[1]
JAN = date(2026, 1, 1)
FEB = date(2026, 2, 1)
MAR = date(2026, 3, 1)
APR = date(2026, 4, 1)


def row(metric, start, end, value, *, product="FIN", unit="KZT",
        dims=(), observation_id=""):
    return Observation(product=product, metric=metric, scope="sample-project",
                       start=start, end=end, value=value, unit=unit,
                       source_sha="a"*64, dimensions=tuple(sorted(dims)),
                       observation_id=observation_id)


def source(*records, watermark=APR, attested=True, events=False):
    return Dataset(scope="sample-project", content_sha="b"*64, rows=tuple(records),
                   watermark=watermark, interval_coverage_attested=attested,
                   complete_event_stream=events)


def request(metric="REVENUE", operation="SUM", *, product="FIN", start=JAN,
            end=APR, output_grain="MONTH", source_grain="MONTH",
            group_by=(), include_total=True, **kw):
    return PeriodRequest(product=product, metric=metric, operation=operation,
                         scope="sample-project", start=start, end=end,
                         grain=output_grain, group_by=group_by,
                         source_grain=source_grain, include_total=include_total,
                         **kw)


def monthly(metric, values, *, dims=()):
    intervals = [(JAN,FEB), (FEB,MAR), (MAR,APR)]
    return [row(metric, a, b, str(value), dims=dims) for (a,b), value in zip(intervals, values)]


class UniversalTemporalExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = Catalog.load(ROOT, reference_mode=True)

    def reject(self, code, call):
        with self.assertRaises(TaseError) as raised:
            call()
        self.assertEqual(raised.exception.code, code)

    def test_monthly_flow_results_and_grand_total(self):
        inp = source(*monthly("REVENUE", ("100000","120000","80000")))
        out = calculate(self.cat, request(), inp)
        self.assertEqual([x.value for x in out.rows],
                         ["100000","120000","80000"])
        self.assertEqual(len(out.total_rows), 1)
        total = out.total_rows[0]
        self.assertEqual(total.value, "300000")
        self.assertEqual((total.start, total.end), (JAN,APR))
        self.assertEqual(total.observation_count, 3)
        self.assertEqual(total.status, "COMPLETE")
        self.assertEqual(total.unit, "KZT")
        self.assertEqual(out.execution_class, "PYTHON_REFERENCE_NOT_S2")

    def test_daily_source_to_monthly_and_total_in_one_request(self):
        days = []
        cursor = JAN
        while cursor < MAR:
            end = cursor + timedelta(days=1)
            days.append(row("REVENUE",cursor,end,"1"))
            cursor = end
        out = calculate(self.cat, request(start=JAN,end=MAR,
                                          source_grain="DAY"), source(*days))
        self.assertEqual([x.value for x in out.rows], ["31", "28"])
        self.assertEqual(out.total_rows[0].value, "59")
        self.assertEqual(out.total_rows[0].observation_count, 59)

    def test_daily_output_supported_on_industry_pack(self):
        days = [
            row("ENERGY_KWH",JAN,JAN+timedelta(days=1),"5",product="INDUSTRY",unit="kWh"),
            row("ENERGY_KWH",JAN+timedelta(days=1),JAN+timedelta(days=2),"7",
                product="INDUSTRY",unit="kWh"),
            row("ENERGY_KWH",JAN+timedelta(days=2),JAN+timedelta(days=3),"9",
                product="INDUSTRY",unit="kWh"),
        ]
        out = calculate(self.cat, request(metric="ENERGY_KWH",product="INDUSTRY",
                        start=JAN,end=JAN+timedelta(days=3),
                        source_grain="DAY",output_grain="DAY"),source(*days))
        self.assertEqual([x.value for x in out.rows],["5","7","9"])
        self.assertEqual(out.total_rows[0].value,"21")

    def test_monthly_source_can_group_to_calendar_quarter(self):
        inp = source(*monthly("REVENUE", ("100","120","80")))
        out = calculate(self.cat, request(output_grain="QUARTER"),inp)
        self.assertEqual(len(out.rows),1)
        self.assertEqual(out.rows[0].value,"300")
        self.assertEqual(out.total_rows[0].value,"300")
        self.assertEqual(out.total_rows[0].observation_count,3)

    def test_stock_month_end_is_not_sum_of_snapshots(self):
        snapshots = [
            row("CASH_BALANCE",date(2026,1,31),None,"100"),
            row("CASH_BALANCE",date(2026,2,28),None,"300"),
            row("CASH_BALANCE",date(2026,3,31),None,"200"),
        ]
        out = calculate(self.cat, request(metric="CASH_BALANCE",
                            operation="LAST_AS_OF",source_grain="AS_OF",
                            max_snapshot_age_days=31),source(*snapshots))
        self.assertEqual([r.value for r in out.rows],["100","300","200"])
        self.assertEqual(out.total_rows[0].value,"200")
        self.assertNotEqual(out.total_rows[0].value,"600")

    def test_ratio_of_sums_is_not_sum_or_average_of_monthly_ratios(self):
        inp = source(*monthly("REVENUE",("100","120","80")),
                     *monthly("GROSS_PROFIT",("20","36","8")))
        out = calculate(self.cat,request(metric="GROSS_MARGIN",operation="RATIO_OF_SUMS"),inp)
        monthly_rates=[Decimal(row.value) for row in out.rows]
        self.assertEqual(monthly_rates,[Decimal("0.2"),Decimal("0.3"),Decimal("0.1")])
        total_rate=Decimal(out.total_rows[0].value)
        self.assertLess(abs(total_rate-Decimal(64)/Decimal(300)),Decimal("1e-40"))
        self.assertNotEqual(total_rate,sum(monthly_rates)/3)

    def test_period_totals_are_per_dimension_group_not_cross_mixed(self):
        a=(("branch","A"),)
        b=(("branch","B"),)
        inp=source(*monthly("REVENUE",("100","120","80"),dims=a),
                   *monthly("REVENUE",("10","20","30"),dims=b))
        out=calculate(self.cat,request(group_by=("branch",)),inp)
        self.assertEqual([x.value for x in out.total_rows],["300","60"])
        self.assertEqual([x.group for x in out.total_rows],
                         [(("branch","A"),),(("branch","B"),)])
        overall=calculate(self.cat,request(),inp)
        self.assertEqual(overall.total_rows[0].value,"360")

    def test_opt_in_preserves_existing_unmodified_plan_sha_and_result_sha(self):
        inp=source(*monthly("REVENUE",("100","120","80")))
        legacy=PeriodRequest("FIN","REVENUE","SUM","sample-project",JAN,APR,"MONTH")
        new=replace(legacy,include_total=False)
        a=calculate(self.cat,legacy,inp)
        b=calculate(self.cat,new,inp)
        self.assertEqual(compile_plan(self.cat,legacy).plan_sha,
                         compile_plan(self.cat,new).plan_sha)
        self.assertEqual(a.result_sha,b.result_sha)
        self.assertFalse(a.total_rows)
        self.assertEqual(len(b.rows),3)
        with_total=replace(legacy,source_grain="MONTH",include_total=True)
        c=calculate(self.cat,with_total,inp)
        self.assertEqual(c.total_rows[0].value,"300")
        self.assertNotEqual(c.plan_sha,a.plan_sha)
        self.assertNotEqual(c.result_sha,a.result_sha)

    def test_unknown_or_missing_source_grain_fails_closed(self):
        self.reject("SOURCE_GRAIN_REQUIRED",lambda:
                    request(source_grain=None,include_total=True))
        self.reject("SOURCE_GRAIN_NOT_SUPPORTED",lambda:
                    request(source_grain="MAGIC",include_total=True))
        self.reject("INVALID_INCLUDE_TOTAL",lambda:
                    request(include_total="true"))

    def test_source_grain_must_match_actual_half_open_intervals(self):
        inp=source(*monthly("REVENUE",("100","120","80")))
        self.reject("SOURCE_GRAIN_MISMATCH",lambda:
                    calculate(self.cat,request(source_grain="DAY"),inp))
        rows=monthly("REVENUE",("100","120","80"))
        rows[0]=replace(rows[0],end=date(2026,1,31))
        self.reject("SOURCE_GRAIN_MISMATCH",lambda:
                    calculate(self.cat,request(),source(*rows)))

    def test_missing_month_and_overlapping_windows_still_block_total(self):
        inp=source(*monthly("REVENUE",("100","120","80"))[::2])
        self.reject("PARTIAL_COVERAGE",lambda:calculate(self.cat,request(),inp))
        duplicated=[
            row("REVENUE",JAN,MAR,"100"),
            row("REVENUE",FEB,APR,"200")
        ]
        self.reject("SOURCE_GRAIN_MISMATCH",lambda:
                    calculate(self.cat,request(),source(*duplicated)))

    def test_unapproved_operator_and_disallowed_output_grain_not_unlocked(self):
        inp=source(*monthly("REVENUE",("100","120","80")))
        self.reject("GRAIN_NOT_ALLOWED",lambda:
                    calculate(self.cat,request(output_grain="DAY"),inp))
        self.reject("OPERATOR_NOT_ALLOWED",lambda:
                    calculate(self.cat,request(operation="LAST_AS_OF"),inp))

    def test_no_coverage_attestation_cannot_claim_complete_total(self):
        inp=source(*monthly("REVENUE",("100","120","80")),attested=False)
        self.reject("COVERAGE_UNKNOWN",lambda:calculate(self.cat,request(),inp))
        partially=calculate(self.cat,request(require_full_coverage=False),inp)
        self.assertEqual(partially.status,"PARTIAL")
        self.assertEqual(partially.total_rows[0].status,"PARTIAL")
        self.assertEqual(partially.total_rows[0].coverage,"UNKNOWN")


if __name__ == "__main__":
    unittest.main()
