"""HC-R0.3 portable deterministic golden vector bank, for future Python/Rust parity."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import ReferenceEngine

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "golden" / "hc_r03_reference_vectors.json"


class R03PortableGoldens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.golden = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_schema_and_coverage(self):
        bank = self.golden
        self.assertEqual(bank["schema"], "FENGINE_HC_R03_GOLDENS_V1")
        self.assertEqual(bank["status"], "MATHEMATICAL_REFERENCE_ONLY_NOT_FINANCE_S2")
        self.assertEqual(len(bank["vectors"]), 7)
        self.assertEqual(len({v["id"] for v in bank["vectors"]}), 7)
        self.assertEqual(len({(v["model"], v["variant"]) for v in bank["vectors"]}), 7)
        self.assertTrue("DELETE_AFTER_ACK" in bank["retentionPolicy"])

    def test_all_reference_goldens(self):
        for case in self.golden["vectors"]:
            with self.subTest(model=case["model"], variant=case["variant"], id=case["id"]):
                result = self.engine.calculate(
                    case["model"], case["variant"], case["inputs"],
                    case["config"], reference_mode=True
                )
                self.assertEqual(result.execution_class, "PYTHON_REFERENCE_NOT_S2")
                tol = Decimal(case["tolerance"])
                for field, value in case["expectedDecimal"].items():
                    actual = Decimal(result.output[field])
                    self.assertLessEqual(abs(actual - Decimal(value)), tol, field)
                for field, value in case["expectedExact"].items():
                    self.assertEqual(result.output[field], value, field)


if __name__ == "__main__":
    unittest.main()
