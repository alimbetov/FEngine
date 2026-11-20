"""HC-R0.4 portable Python goldens for eventual Rust numerical parity."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import ReferenceEngine, NUMERIC_POLICY_ID

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tests" / "golden" / "hc_r04_reference_vectors.json"


class R04PortableGoldens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_golden_contract(self):
        data = self.data
        self.assertEqual(data["schema"], "FENGINE_HC_R04_GOLDENS_V1")
        self.assertEqual(data["numericPolicy"], NUMERIC_POLICY_ID)
        self.assertEqual(data["status"], "MATHEMATICAL_REFERENCE_ONLY_NOT_FINANCE_S2")
        self.assertEqual(data["sourceClassification"], "SYNTHETIC_NO_USER_DATA")
        self.assertEqual(len(data["vectors"]), 5)
        self.assertEqual(len({v["id"] for v in data["vectors"]}), 5)
        self.assertEqual(len({(v["model"], v["variant"]) for v in data["vectors"]}), 5)

    def test_all_portable_golden_outputs_and_hash_replay(self):
        for case in self.data["vectors"]:
            with self.subTest(case=case["id"]):
                a = self.engine.calculate(case["model"], case["variant"],
                                          case["inputs"], case["config"],
                                          reference_mode=True)
                b = self.engine.calculate(case["model"], case["variant"],
                                          case["inputs"], case["config"],
                                          reference_mode=True)
                self.assertEqual(a.output_sha256, b.output_sha256)
                self.assertEqual(a.execution_class, "PYTHON_REFERENCE_NOT_S2")
                tolerance = Decimal(case["tolerance"])
                for key, expected in case["expectedDecimal"].items():
                    self.assertLessEqual(abs(Decimal(a.output[key]) - Decimal(expected)),
                                         tolerance, key)
                for key, expected in case["expectedExact"].items():
                    self.assertEqual(a.output[key], expected, key)


if __name__ == "__main__":
    unittest.main()
