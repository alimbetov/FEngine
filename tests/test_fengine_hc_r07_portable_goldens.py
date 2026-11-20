"""HC-R0.6/R0.7 portable goldens and independently content-pinned SHA evidence."""
from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import ReferenceEngine, NUMERIC_POLICY_ID
from fengine_hc.r06_fcfe import cost_of_equity_rate_sha256, fcfe_source_sha256, reconcile_fcfe_methods
from fengine_hc.r07_pvm import pvm_revision_hashes

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tests" / "golden" / "hc_r06_r07_reference_vectors.json"


class R07PortableGoldens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = json.loads(FILE.read_text(encoding="utf-8"))
        cls.engine = ReferenceEngine(ROOT)

    def test_fixture_schema_no_customer_data_and_five_variants(self):
        self.assertEqual(self.bank["schema"], "FENGINE_HC_R06_R07_GOLDEN_V1")
        self.assertEqual(self.bank["provenance"], "SYNTHETIC_NO_CUSTOMER_DATA")
        self.assertEqual(self.bank["status"], "MATHEMATICAL_REFERENCE_NOT_FINANCIAL_S2")
        self.assertEqual(self.bank["numericPolicy"], NUMERIC_POLICY_ID)
        self.assertEqual(len(self.bank["vectors"]), 5)
        self.assertEqual(len({x["id"] for x in self.bank["vectors"]}), 5)
        self.assertEqual(len({(x["model"], x["variant"]) for x in self.bank["vectors"]}), 5)

    def test_independent_golden_values_and_replay_sha(self):
        outputs = {}
        for item in self.bank["vectors"]:
            with self.subTest(case=item["id"]):
                inp, cfg = item["inputs"], item["config"]
                if item["model"] == "HC.DCF.06":
                    self.assertEqual(cost_of_equity_rate_sha256(inp["costOfEquityRate"]),
                                     cfg["costOfEquityRef"])
                    self.assertEqual(inp["costOfEquityRevisionSha256"], cfg["costOfEquityRef"])
                    self.assertEqual(fcfe_source_sha256(
                        {key: value for key, value in inp.items()
                         if key != "sourceRevisionSha256"}, item["variant"]
                    ), inp["sourceRevisionSha256"])
                else:
                    pins = pvm_revision_hashes(
                        inp["baselinePeriod"], inp["actualPeriod"],
                        inp["currency"], inp["quantityUnit"], inp["rows"]
                    )
                    self.assertEqual(inp["baselineRevisionSha256"],
                                     pins["baselineRevisionSha256"])
                    self.assertEqual(inp["actualRevisionSha256"],
                                     pins["actualRevisionSha256"])
                    self.assertEqual(cfg["standardCostVintage"], pins["standardCostVintage"])
                    self.assertEqual(cfg["volumeBaseline"], pins["volumeBaseline"])
                a = self.engine.calculate(
                    item["model"], item["variant"], inp, cfg, reference_mode=True
                )
                b = self.engine.calculate(
                    item["model"], item["variant"], inp, cfg, reference_mode=True
                )
                self.assertEqual(a.output_sha256, b.output_sha256)
                self.assertEqual(a.execution_class, "PYTHON_REFERENCE_NOT_S2")
                tolerance = Decimal(item["tolerance"])
                for name, value in item["expectedDecimal"].items():
                    self.assertLessEqual(abs(Decimal(a.output[name]) - Decimal(value)),
                                         tolerance, name)
                for name, value in item["expectedExact"].items():
                    self.assertEqual(a.output[name], value, name)
                outputs[item["variant"]] = a.output
        self.assertEqual(
            reconcile_fcfe_methods(outputs["FCFE_LEVERED"], outputs["FCFE_NORMALIZED"])["difference"],
            "0",
        )


if __name__ == "__main__":
    unittest.main()
