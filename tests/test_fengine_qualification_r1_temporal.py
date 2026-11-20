"""FEngine Model Qualification R1: independent temporal ratio source-universe invariants.

All data synthetic; no FIN adapter, source truth, Redis, production S2 or Rust.
"""
from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

from tase import Catalog, Dataset, Observation, PeriodRequest, TaseError, calculate

ROOT = Path(__file__).resolve().parents[1]
JAN, FEB, MAR, APR = (date(2026, m, 1) for m in (1, 2, 3, 4))


def fact(metric: str, amount: str, begin: date, end: date, branch: str):
    return Observation(
        product="FIN", metric=metric, scope="synthetic",
        start=begin, end=end, value=amount, unit="KZT",
        source_sha="a" * 64, dimensions=(("branch", branch),)
    )


def period(*, group_by=(), include_total=True, require_full_coverage=True):
    return PeriodRequest(
        product="FIN", metric="GROSS_MARGIN", operation="RATIO_OF_SUMS",
        scope="synthetic", start=JAN, end=APR, grain="MONTH",
        source_grain="MONTH", group_by=group_by, include_total=include_total,
        require_full_coverage=require_full_coverage,
    )


def data(*rows, attested=True):
    return Dataset(
        scope="synthetic", content_sha="b" * 64, rows=tuple(rows),
        watermark=APR, interval_coverage_attested=attested,
    )


class QualifiedTemporalRatioInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = Catalog.load(ROOT, reference_mode=True)

    def reject(self, code, func):
        with self.assertRaises(TaseError) as exc:
            func()
        self.assertEqual(exc.exception.code, code)

    def test_unrelated_business_universes_must_not_produce_false_margin(self):
        numerator = [fact("GROSS_PROFIT", v, a, b, "A")
                     for (a, b), v in zip(((JAN, FEB), (FEB, MAR), (MAR, APR)),
                                         ("20", "36", "8"))]
        denominator = [fact("REVENUE", v, a, b, "B")
                       for (a, b), v in zip(((JAN, FEB), (FEB, MAR), (MAR, APR)),
                                           ("100", "120", "80"))]
        # Before QUAL-R1 this returned the misleading 64/300 for two
        # disjoint branches because each component was individually complete.
        self.reject("COMPONENT_ALIGNMENT", lambda:
                    calculate(self.cat, period(), data(*(numerator + denominator))))

    def test_aligned_atomic_branches_recompute_correct_months_and_grand_total(self):
        source = []
        for branch, scale in (("A", 1), ("B", 2)):
            for (a, b), revenue, profit in zip(
                ((JAN, FEB), (FEB, MAR), (MAR, APR)),
                (100, 120, 80), (20, 36, 8)
            ):
                source.append(fact("REVENUE", str(scale * revenue), a, b, branch))
                source.append(fact("GROSS_PROFIT", str(scale * profit), a, b, branch))
        out = calculate(self.cat, period(), data(*reversed(source)))
        # Six bucket rows, one per month and same leaf union. TASE is
        # allowed to aggregate aligned branches only after checking keys.
        self.assertEqual(len(out.rows), 3)
        self.assertEqual(len(out.total_rows), 1)
        expected = (Decimal("0.2"), Decimal("0.3"), Decimal("0.1"))
        self.assertEqual(tuple(Decimal(r.value) for r in out.rows), expected)
        self.assertLess(
            abs(Decimal(out.total_rows[0].value) - Decimal(64) / Decimal(300)),
            Decimal("1e-39"),
        )
        self.assertEqual(out.total_rows[0].unit, "fraction")

    def test_grouped_margin_also_checks_every_dimension_leaf(self):
        values = []
        for branch in ("A", "B"):
            for a, b in ((JAN, FEB), (FEB, MAR), (MAR, APR)):
                values.append(fact("GROSS_PROFIT", "20", a, b, branch))
                if branch == "A":
                    values.append(fact("REVENUE", "100", a, b, branch))
        # Branch B numerator never gets its own denominator; it cannot
        # silently pair with branch A when group_by is empty.
        self.reject("COMPONENT_ALIGNMENT", lambda:
                    calculate(self.cat, period(), data(*values)))

    def test_partial_mode_does_not_allow_component_period_drift(self):
        values = [
            fact("GROSS_PROFIT", "20", JAN, FEB, "A"),
            fact("REVENUE", "100", FEB, MAR, "A"),
        ]
        self.reject("COMPONENT_ALIGNMENT", lambda:
                    calculate(self.cat, period(require_full_coverage=False),
                              data(*values, attested=False)))

    def test_full_coverage_remains_source_attested_not_inferred(self):
        values = [
            fact(metric, value, JAN, FEB, "A")
            for metric, value in (("REVENUE", "100"), ("GROSS_PROFIT", "20"))
        ]
        self.reject("COVERAGE_UNKNOWN", lambda:
                    calculate(self.cat, period(), data(*values, attested=False)))


if __name__ == "__main__":
    unittest.main()
