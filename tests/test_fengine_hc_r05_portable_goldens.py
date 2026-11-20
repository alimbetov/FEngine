"""Portable R0.5 JSON arithmetic and SHA goldens, future cross-engine comparator."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import ReferenceEngine
from fengine_hc.r05_cashflow import (
    RECONCILIATION_SHA256, posted_source_sha256, classification_rules_sha256,
    override_revision_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tests" / "golden" / "hc_r05_cashflow_vectors.json"


class R05PortableCashflowGoldens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = json.loads(FILE.read_text(encoding="utf-8"))
        cls.engine = ReferenceEngine(ROOT)

    def test_fixture_pins_independent_sha_and_schema(self):
        bank = self.bank
        self.assertEqual(bank["schema"], "FENGINE_HC_R05_CASHFLOW_GOLDENS_V1")
        self.assertEqual(bank["status"], "PYTHON_MATH_REFERENCE_NOT_FINANCIAL_S2")
        self.assertEqual(RECONCILIATION_SHA256, bank["reconciliationPolicySha256"])
        self.assertEqual(len(bank["vectors"]), 2)
        ids = set()
        for case in bank["vectors"]:
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["id"], ids)
                ids.add(case["id"])
                inp, cfg = case["inputs"], case["config"]
                self.assertEqual(classification_rules_sha256(inp["classificationRules"]),
                                 cfg["cashClassification"])
                snapshot = {name: inp[name] for name in (
                    "periodStart", "periodEnd", "currency",
                    "openingCash", "closingCash", "postings"
                )}
                self.assertEqual(posted_source_sha256(snapshot), inp["sourceRevisionSha256"])
                self.assertEqual(inp["sourceRevisionSha256"], bank["sourceBindingSha256"])
                if case["variant"] == "DIRECT_RECLASSIFIED_CFO":
                    self.assertEqual(override_revision_sha256(
                        inp["sourceRevisionSha256"], inp["reclassificationOverrides"]
                    ), inp["reclassificationRevisionSha256"])

    def test_both_independent_synthetic_golden_values(self):
        for case in self.bank["vectors"]:
            with self.subTest(case=case["id"]):
                result = self.engine.calculate(
                    case["model"], case["variant"], case["inputs"], case["config"],
                    reference_mode=True
                )
                self.assertEqual(result.execution_class, "PYTHON_REFERENCE_NOT_S2")
                self.assertEqual(result.output_sha256,
                                 self.engine.calculate(
                                     case["model"], case["variant"],
                                     case["inputs"], case["config"],
                                     reference_mode=True
                                 ).output_sha256)
                tolerance = Decimal(case["tolerance"])
                for name, expected in case["expectedDecimal"].items():
                    self.assertLessEqual(abs(Decimal(result.output[name]) -
                                             Decimal(expected)), tolerance)
                for name, expected in case["expectedExact"].items():
                    self.assertEqual(result.output[name], expected)


if __name__ == "__main__":
    unittest.main()
