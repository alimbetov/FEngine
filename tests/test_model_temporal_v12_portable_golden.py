"""Independent portable numerical controls for all five V1.2 temporal contracts."""
from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from tase import (
    ModelTemporalRegistryV12, calculate_model_temporal_v12,
)
from test_model_temporal_capability_v12 import (
    dated, capm, pvm, request,
)

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tests" / "golden" / "model_temporal_v12_reference_vectors.json"


class TemporalV12PortableGoldens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = json.loads(FILE.read_text(encoding="utf-8"))
        cls.registry = ModelTemporalRegistryV12.load(ROOT, reference_mode=True)

    def test_fixture_contract_and_no_real_customer_data(self):
        self.assertEqual(self.bank["schema"], "FENGINE_TEMPORAL_V12_GOLDENS_V1")
        self.assertEqual(
            self.bank["classification"],
            "SYNTHETIC_REFERENCE_ONLY_NOT_FINANCIAL_S2",
        )
        cases = self.bank["cases"]
        self.assertEqual(len(cases), 5)
        self.assertEqual(len({c["id"] for c in cases}),5)
        self.assertEqual(
            len({(c["model"],c["variant"],c["field"]) for c in cases}),5
        )

    def test_reexecute_portable_goldens_and_replay_hash(self):
        for case in self.bank["cases"]:
            with self.subTest(case=case["id"]):
                if case["model"] == "HC.DCF.02":
                    items = [
                        dated(date.fromisoformat(at),amount,
                              rate=case["annualRate"])
                        for at,amount in zip(case["dates"],case["amounts"])
                    ]
                elif case["model"] == "HC.CAP.01":
                    items = [
                        capm(date.fromisoformat(at),beta,weight,
                             rf=case["riskFree"],premium=case["premium"])
                        for at,beta,weight in zip(
                            case["dates"],case["betas"],case["weights"]
                        )
                    ]
                else:
                    items = []
                    for at,actual in zip(case["dates"],case["actuals"]):
                        items.append(pvm(
                            date.fromisoformat(at),variant=case["variant"],
                            quantities=(actual["A"]["quantity"],actual["B"]["quantity"]),
                            costs=(actual["A"]["unitCost"],actual["B"]["unitCost"]),
                        ))
                req = request(case["model"],case["variant"],case["field"])
                result = calculate_model_temporal_v12(
                    self.registry,req,items,reference_mode=True
                )
                repeated = calculate_model_temporal_v12(
                    self.registry,req,list(reversed(items)),reference_mode=True
                )
                self.assertEqual(result.result_sha256,repeated.result_sha256)
                self.assertEqual(result.execution_class,"PYTHON_REFERENCE_NOT_S2")
                self.assertEqual(len(result.source_output_shas),3)
                self.assertEqual(len(result.result.rows),3)
                self.assertEqual(len(result.result.total_rows),1)
                tol = Decimal(case["tolerance"])
                for row,expected in zip(result.result.rows,case["expectedBuckets"]):
                    self.assertLessEqual(
                        abs(Decimal(row.value)-Decimal(expected)),tol
                    )
                self.assertLessEqual(
                    abs(Decimal(result.result.total_rows[0].value) -
                        Decimal(case["expectedTotal"])),tol
                )


if __name__ == "__main__":
    unittest.main()
