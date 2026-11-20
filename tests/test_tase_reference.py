"""TASE Python reference tests: execute REAL in-process code, not HC financial engine.

Product Packs are unapproved DRAFT; tests deliberately opt into reference_mode.
No PostgreSQL/CalculationSession/finance S2 or Rust parity is implied.
"""
from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from tase import (Catalog, Dataset, Observation, PeriodRequest,
                  TaseError, calculate, compile_plan)

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
JAN, FEB, MAR, APR = (date(2026, i, 1) for i in (1, 2, 3, 4))


def obs(metric, value, start=JAN, end=FEB, *,
        product="FIN", unit="KZT", scope="demo", dims=(), state="PRESENT", oid=""):
    return Observation(product=product, metric=metric, scope=scope,
                       start=start, end=end, value=value, unit=unit,
                       source_sha="a"*64, dimensions=tuple(sorted(dims)),
                       state=state, observation_id=oid)


def ds(*rows, scope="demo", complete=False, watermark=APR, attested=True):
    # Synthetic fixtures explicitly represent an attested, watermark-complete
    # source. Real adapters must verify this; they must not simply set True.
    return Dataset(scope=scope, content_sha="b"*64, rows=tuple(rows),
                   complete_event_stream=complete, watermark=watermark,
                   interval_coverage_attested=attested)


def req(metric="REVENUE", operation="SUM", *, product="FIN", grain="QUARTER",
        start=JAN, end=APR, group_by=(), scope="demo", **kw):
    return PeriodRequest(product=product, metric=metric, operation=operation,
                         scope=scope, grain=grain, start=start, end=end,
                         group_by=group_by, **kw)


def revenue():
    return [
        obs("REVENUE", "100", JAN, FEB),
        obs("REVENUE", "120", FEB, MAR),
        obs("REVENUE", "80", MAR, APR)
    ]


def profits():
    return [
        obs("GROSS_PROFIT", "20", JAN, FEB),
        obs("GROSS_PROFIT", "36", FEB, MAR),
        obs("GROSS_PROFIT", "8", MAR, APR)
    ]


class TaseReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = Catalog.load(ROOT, reference_mode=True)

    def assertCode(self, code, fn):
        with self.assertRaises(TaseError) as cm:
            fn()
        self.assertEqual(cm.exception.code, code)

    def test_registered_catalogue_counts_and_integrity(self):
        self.assertEqual(len(self.cat.products), 6)
        self.assertEqual(len(self.cat.metrics), 26)
        self.assertEqual(len(self.cat.operators), 53)
        self.assertEqual(len(self.cat.predicates), 21)
        for metric in self.cat.metrics.values():
            pack = self.cat.products[metric.product]
            self.assertTrue(metric.operators <= pack.operators)
            for c in (metric.numerator, metric.denominator_or_weight):
                if c:
                    self.assertIn((metric.product, c), self.cat.metrics)

    def test_draft_packs_not_production_admitted(self):
        self.assertCode("UNAPPROVED_PRODUCT_PACK", lambda: Catalog.load(ROOT))

    def test_allowlist_and_semantic_controls(self):
        self.assertCode("OPERATOR_NOT_ALLOWED",
                        lambda: compile_plan(self.cat, req("CASH_BALANCE", "SUM")))
        self.assertCode("OPERATOR_NOT_ALLOWED",
                        lambda: compile_plan(self.cat, req("REVENUE", "LAST_AS_OF")))
        self.assertCode("OPERATOR_NOT_IMPLEMENTED",
                        lambda: compile_plan(self.cat, req("REVENUE", "YTD", grain="FISCAL_YEAR")))
        self.assertCode("GRAIN_NOT_ALLOWED",
                        lambda: compile_plan(self.cat, req(grain="CUSTOM_INTERVAL")))
        self.assertCode("UNKNOWN_METRIC",
                        lambda: compile_plan(self.cat, req("DOES_NOT_EXIST")))
        self.assertCode("UNKNOWN_PRODUCT",
                        lambda: compile_plan(self.cat, req(product="DOES_NOT_EXIST")))

    def test_quarter_revenue_and_decimal_exactness(self):
        result = calculate(self.cat, req(), ds(*revenue()))
        self.assertEqual(result.status, "COMPLETE")
        self.assertEqual(result.execution_class, "PYTHON_REFERENCE_NOT_S2")
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].value, "300")
        self.assertEqual(result.rows[0].unit, "KZT")
        self.assertEqual(result.rows[0].observation_count, 3)
        self.assertEqual(len(result.result_sha), 64)

    def test_quarter_margin_is_ratio_of_sums(self):
        result = calculate(self.cat, req("GROSS_MARGIN", "RATIO_OF_SUMS"),
                           ds(*revenue(), *profits()))
        self.assertAlmostEqual(D(result.rows[0].value), D(64)/D(300), places=40)
        self.assertEqual(result.rows[0].unit, "fraction")

    def test_fin_money_mean_variance_and_standard_deviation(self):
        data = ds(*revenue())
        expected = {
            "ARITH_MEAN": D("100"),
            "VAR_POP": D(800)/3,
            "STDDEV_POP": (D(800)/3).sqrt(),
        }
        for op, value in expected.items():
            with self.subTest(op=op):
                row = calculate(self.cat, req(operation=op), data).rows[0]
                self.assertAlmostEqual(D(row.value), value, places=25)
                if op == "VAR_POP":
                    self.assertEqual(row.unit, "KZT^2")

    def test_bounded_groups_and_dimension_aggregation(self):
        rows = []
        for branch, factor in (("A", 1), ("B", 2)):
            for start, end, val in ((JAN, FEB, 100), (FEB, MAR, 120), (MAR, APR, 80)):
                rows.append(obs("REVENUE", str(val*factor), start, end,
                                dims=(("branch", branch),)))
        result = calculate(self.cat, req(group_by=("branch",)), ds(*rows))
        self.assertEqual([r.value for r in result.rows], ["300", "600"])
        self.assertEqual([r.group[0][1] for r in result.rows], ["A", "B"])
        aggregate = calculate(self.cat, req(), ds(*rows))
        self.assertEqual(aggregate.rows[0].value, "900")

    def test_end_of_period_stock_not_sum(self):
        cash = [obs("CASH_BALANCE", "20", JAN, None),
                obs("CASH_BALANCE", "30", FEB, None),
                obs("CASH_BALANCE", "10", date(2026, 3, 31), None)]
        out = calculate(self.cat, req("CASH_BALANCE", "LAST_AS_OF"), ds(*cash))
        self.assertEqual(out.rows[0].value, "10")
        self.assertEqual(out.rows[0].observation_count, 1)

    def test_stale_snapshot(self):
        data = ds(obs("CASH_BALANCE", "20", JAN, None))
        self.assertCode("STALE_SNAPSHOT", lambda: calculate(self.cat,
                         req("CASH_BALANCE", "LAST_AS_OF"), data))

    def test_weighted_rate_uses_aligned_exposure(self):
        a = (("loan", "A"),)
        b = (("loan", "B"),)
        data = ds(
            obs("PORTFOLIO_NOMINAL_RATE", ".10", JAN, None, product="BANK", unit="fraction", dims=a),
            obs("PORTFOLIO_NOMINAL_RATE", ".20", JAN, None, product="BANK", unit="fraction", dims=b),
            obs("LOAN_OUTSTANDING", "100", JAN, None, product="BANK", dims=a),
            obs("LOAN_OUTSTANDING", "300", JAN, None, product="BANK", dims=b))
        result = calculate(self.cat, req("PORTFOLIO_NOMINAL_RATE", "WEIGHTED_MEAN",
                                         product="BANK", grain="QUARTER"), data)
        self.assertEqual(result.rows[0].value, "0.175")

    def test_weighted_rate_missing_pair_and_zero_weights(self):
        a = (("loan", "A"),)
        rate = obs("PORTFOLIO_NOMINAL_RATE", ".1", JAN, None,
                   product="BANK", unit="fraction", dims=a)
        self.assertCode("PAIR_ALIGNMENT", lambda: calculate(self.cat,
            req("PORTFOLIO_NOMINAL_RATE", "WEIGHTED_MEAN", product="BANK"),
            ds(rate)))
        weight = obs("LOAN_OUTSTANDING", "0", JAN, None, product="BANK", dims=a)
        self.assertCode("ZERO_TOTAL_WEIGHT", lambda: calculate(self.cat,
            req("PORTFOLIO_NOMINAL_RATE", "WEIGHTED_MEAN", product="BANK"),
            ds(rate, weight)))

    def test_empty_and_missing_quarter(self):
        self.assertCode("PARTIAL_COVERAGE", lambda: calculate(self.cat, req(),
            ds(revenue()[0], revenue()[2])))
        self.assertCode("MISSING_OBSERVATION", lambda: calculate(self.cat, req(),
            ds(revenue()[0], obs("REVENUE", None, FEB, MAR, state="MISSING"),
               revenue()[2])))

    def test_source_coverage_must_be_attested(self):
        self.assertCode("COVERAGE_UNKNOWN", lambda: calculate(self.cat, req(),
                         ds(*revenue(), attested=False)))
        self.assertCode("COVERAGE_UNKNOWN", lambda: calculate(self.cat, req(),
                         ds(*revenue(), watermark=MAR)))

    def test_optional_partial_result_never_mislabeled_complete(self):
        out = calculate(self.cat, req(require_full_coverage=False),
                        ds(*revenue(), attested=False, watermark=None))
        self.assertEqual(out.status, "PARTIAL")
        self.assertEqual(out.rows[0].status, "PARTIAL")
        self.assertEqual(out.rows[0].coverage, "UNKNOWN")

    def test_overlapping_intervals(self):
        data = ds(obs("REVENUE", "100", JAN, MAR),
                  obs("REVENUE", "120", FEB, APR))
        self.assertCode("SOURCE_OVERLAP", lambda: calculate(self.cat, req(), data))

    def test_no_unapproved_apportioning(self):
        data = ds(obs("REVENUE", "300", JAN, APR))
        self.assertCode("SOURCE_GRANULARITY_MISMATCH",
                        lambda: calculate(self.cat, req(grain="MONTH", start=JAN, end=FEB), data))

    def test_scope_isolation(self):
        self.assertCode("CROSS_SCOPE_DATASET",
                        lambda: calculate(self.cat, req(), ds(*revenue(), scope="different")))

    def test_period_identity_and_fiscal_calendar(self):
        data = ds(obs("REVENUE", "100", date(2025, 4, 1), date(2025, 7, 1)))
        request = req(start=date(2025, 4, 1), end=date(2025, 7, 1),
                      grain="FISCAL_QUARTER", fiscal_start_month=4)
        out = calculate(self.cat, request, data)
        self.assertEqual(out.rows[0].value, "100")
        self.assertCode("PARTIAL_BUCKET_UNSUPPORTED",
                        lambda: compile_plan(self.cat, req(start=date(2026, 1, 15))))

    def test_fiscal_period_is_gregorian_month_not_445(self):
        plan = compile_plan(self.cat, req(grain="FISCAL_PERIOD", start=JAN, end=FEB))
        self.assertEqual(plan.request.grain, "FISCAL_PERIOD")
        # 4-4-5 and 53rd-week fiscal profiles are NOT implemented by this reference.

    def test_quantile_nearest_rank_and_bounds(self):
        rows = [
            obs("OBSERVATION_VALUE", str(v), date(2026, 1, 10 + i), None,
                product="CUSTOM", unit="custom_unit", oid=str(i))
            for i, v in enumerate((0, 10, 20, 30))
        ]
        data = ds(*rows, complete=True, watermark=APR)
        out = calculate(self.cat, req("OBSERVATION_VALUE", "QUANTILE_EXACT",
                                       product="CUSTOM", quantile_alpha=".75"), data)
        self.assertEqual(out.rows[0].value, "20")
        self.assertCode("QUANTILE_ALPHA_REQUIRED", lambda: compile_plan(self.cat,
                        req("OBSERVATION_VALUE", "QUANTILE_EXACT", product="CUSTOM")))
        self.assertCode("INVALID_QUANTILE", lambda: req(quantile_alpha="1.0"))

    def test_source_values_cannot_be_float_or_nonfinite(self):
        self.assertCode("DECIMAL_STRING_REQUIRED",
                        lambda: obs("REVENUE", 0.1))
        self.assertCode("NONFINITE_VALUE",
                        lambda: obs("REVENUE", "NaN"))
        self.assertCode("VALUE_STATE_CONFLICT",
                        lambda: obs("REVENUE", "0", state="MISSING"))

    def test_currency_and_unit_mismatch(self):
        rows = revenue()
        rows[1] = replace(rows[1], unit="USD")
        self.assertCode("UNIT_OR_CURRENCY_MISMATCH",
                        lambda: calculate(self.cat, req(), ds(*rows)))

    def test_duplicate_observation_id(self):
        repeated = obs("REVENUE", "10", JAN, FEB)
        self.assertCode("DUPLICATE_OBSERVATION",
                        lambda: ds(repeated, repeated))

    def test_plan_is_deterministic_and_changes_on_policy(self):
        p1 = compile_plan(self.cat, req())
        p2 = compile_plan(self.cat, req())
        p3 = compile_plan(self.cat, req(require_full_coverage=False))
        self.assertEqual(p1.plan_sha, p2.plan_sha)
        self.assertNotEqual(p1.plan_sha, p3.plan_sha)
        self.assertEqual(calculate(self.cat, req(), ds(*revenue())).result_sha,
                         calculate(self.cat, req(), ds(*revenue())).result_sha)

    def test_not_an_immutable_durable_job(self):
        result = calculate(self.cat, req(), ds(*revenue()))
        self.assertEqual(result.execution_class, "PYTHON_REFERENCE_NOT_S2")
        self.assertFalse(hasattr(result, "outbox_receipt"))
        self.assertFalse(hasattr(result, "database_transaction"))


if __name__ == "__main__":
    unittest.main()
