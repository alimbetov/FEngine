"""Portable V1.1 reference vectors; independently authored source/expected values."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from tase.model_temporal_v11 import (
    ModelTemporalRegistryV11, calculate_model_temporal_v11,
)
from test_model_temporal_capability_v11 import (
    JAN, FEB, MAR, APR, PERIODS, evm, npv, request,
)

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tests" / "golden" / "model_temporal_v11_reference_vectors.json"


class V11PortableGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelTemporalRegistryV11.load(ROOT, reference_mode=True)
        cls.bank = json.loads(FILE.read_text(encoding="utf-8"))

    def test_fixture_identity_and_coverage(self):
        self.assertEqual(self.bank["schema"], "FENGINE_TEMPORAL_V11_GOLDENS_V1")
        self.assertEqual(
            self.bank["classification"],
            "SYNTHETIC_NO_CUSTOMER_DATA_REFERENCE_NOT_FINANCIAL_S2",
        )
        cases = self.bank["cases"]
        self.assertEqual(len(cases), 4)
        self.assertEqual(len({x["id"] for x in cases}), 4)
        self.assertEqual(len({(x["model"], x["variant"]) for x in cases}), 4)

    def test_execute_four_independent_goldens_exact_nonlinear_and_component_results(self):
        for case in self.bank["cases"]:
            with self.subTest(id=case["id"]):
                if case["model"] == "HC.COST.07":
                    rows = [
                        evm(
                            __import__("datetime").date.fromisoformat(snapshot["date"]),
                            snapshot["earnedValue"], snapshot["actualCost"],
                            case["variant"],
                        ) for snapshot in case["snapshots"]
                    ]
                else:
                    rows = [
                        npv(start, end, amount, case["effectiveRatePerMonth"],
                            variant=case["variant"])
                        for (start,end),amount in zip(PERIODS,case["cashflows"])
                    ]
                req = request(case["model"],case["variant"],case["output"],
                              source_grain=case["sourceGrain"],
                              output_grain=case["outputGrain"])
                result = calculate_model_temporal_v11(
                    self.registry,req,rows,reference_mode=True,
                )
                result_again = calculate_model_temporal_v11(
                    self.registry,req,list(reversed(rows)),reference_mode=True,
                )
                self.assertEqual(result.result_sha256,result_again.result_sha256)
                self.assertEqual(result.execution_class,"PYTHON_REFERENCE_NOT_S2")
                self.assertEqual(len(result.result.rows),3)
                self.assertEqual(len(result.result.total_rows),1)
                tolerance = Decimal(case["tolerance"])
                for row,expected in zip(result.result.rows,case["expectedBuckets"]):
                    self.assertLessEqual(abs(Decimal(row.value)-Decimal(expected)),tolerance)
                self.assertLessEqual(
                    abs(Decimal(result.result.total_rows[0].value) -
                        Decimal(case["expectedTotal"])),tolerance,
                )


if __name__ == "__main__":
    unittest.main()
