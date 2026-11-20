"""Portable JSON mathematical goldens, seed input for future Rust parity."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc import ReferenceEngine
from fengine_hc.reference import NUMERIC_POLICY_ID

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "golden" / "hc_r02_reference_vectors.json"


class GoldenV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.data = json.loads(FIXTURES.read_text(encoding="utf-8"))

    def test_schema_contract_and_unique_case_ids(self):
        d = self.data
        self.assertEqual(d["schema"], "FENGINE_HC_R02_GOLDENS_V1")
        self.assertEqual(d["numericPolicy"], NUMERIC_POLICY_ID)
        self.assertEqual(d["status"], "MATHEMATICAL_REFERENCE_ONLY_NOT_FINANCE_S2")
        self.assertEqual(len(d["vectors"]), 6)
        self.assertEqual(len({x["id"] for x in d["vectors"]}), 6)

    def test_all_machine_readable_python_golden_outputs(self):
        for case in self.data["vectors"]:
            with self.subTest(case=case["id"]):
                r = self.engine.calculate(
                    case["model"], case["variant"], case["inputs"], case["config"],
                    reference_mode=True
                )
                self.assertEqual(r.execution_class, "PYTHON_REFERENCE_NOT_S2")
                tolerance = Decimal(case["tolerance"])
                for key, want in case["expected"].items():
                    actual = r.output[key]
                    if isinstance(want, list):
                        self.assertEqual(len(actual), len(want))
                        for a, b in zip(actual, want):
                            self.assertLessEqual(abs(Decimal(a) - Decimal(b)), tolerance)
                    else:
                        self.assertLessEqual(abs(Decimal(actual) - Decimal(want)), tolerance)


if __name__ == "__main__":
    unittest.main()
