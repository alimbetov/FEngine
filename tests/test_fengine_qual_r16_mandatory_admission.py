"""QUAL-R1.6 strict admission reference; synthetic fixtures only."""
from __future__ import annotations

import random
import unittest
from dataclasses import replace
from pathlib import Path

from fengine_hc.admission_r16 import POLICIES, QualifiedReferenceEngine
from fengine_hc.reference import CalculationError, fingerprint
from fengine_hc.r07_pvm import CONVENTION, pvm_revision_hashes
from fengine_hc.source_context_r15 import SourceContext

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 64
ROWS = [
    {"sku": "A", "baselineQuantity": "60", "actualQuantity": "50",
     "baselineUnitCost": "10", "actualUnitCost": "11"},
    {"sku": "B", "baselineQuantity": "40", "actualQuantity": "60",
     "baselineUnitCost": "20", "actualUnitCost": "18"},
]


def context(role, payload, *, currency="KZT", period_start="2025-01-01",
            period_end="2025-12-31", sku_set=("A", "B"),
            methodology_id="HC.COST.08"):
    return SourceContext(
        source_id="SYN-" + role, role=role, user_id="SYN-U",
        project_id="SYN-P", currency=currency, period_start=period_start,
        period_end=period_end, period_type="YEAR", sku_set=sku_set,
        methodology_id=methodology_id, methodology_version="1.0",
        methodology_sha256=SHA, payload_sha256=fingerprint(payload),
    )


def fixture():
    payloads = {
        "BASELINE": {"rows": [
            {"sku": r["sku"], "quantity": r["baselineQuantity"],
             "unitCost": r["baselineUnitCost"]} for r in ROWS
        ]},
        "ACTUAL": {"rows": [
            {"sku": r["sku"], "quantity": r["actualQuantity"],
             "unitCost": r["actualUnitCost"]} for r in ROWS
        ]},
    }
    b = context("BASELINE", payloads["BASELINE"])
    a = context("ACTUAL", payloads["ACTUAL"], period_start="2026-01-01",
                period_end="2026-12-31")
    evidence = pvm_revision_hashes(b.period_end, a.period_end, b.currency, "PCS", ROWS)
    inp = {
        "baselinePeriod": b.period_end, "actualPeriod": a.period_end,
        "currency": b.currency, "quantityUnit": "PCS", "rows": [dict(r) for r in ROWS],
        "baselineRevisionSha256": evidence["baselineRevisionSha256"],
        "actualRevisionSha256": evidence["actualRevisionSha256"],
    }
    cfg = {"interactionAllocation": CONVENTION,
           "standardCostVintage": evidence["standardCostVintage"],
           "volumeBaseline": evidence["volumeBaseline"]}
    return (b, a), payloads, inp, cfg


class QualR16MandatoryAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = QualifiedReferenceEngine(ROOT)

    def pvm(self, sources=None, payloads=None, inputs=None, config=None):
        ss, pp, ii, cc = fixture()
        return self.engine.calculate(
            "HC.COST.08", "PRICE_VARIANCE", ii if inputs is None else inputs,
            cc if config is None else config,
            sources=ss if sources is None else sources,
            payloads_by_role=pp if payloads is None else payloads,
            reference_mode=True,
        )

    def refuse(self, expected, **changes):
        with self.assertRaises(CalculationError) as ex:
            self.pvm(**changes)
        self.assertEqual(ex.exception.code, expected)

    def test_valid_two_period_pvm_produces_independent_bridge(self):
        r = self.pvm()
        self.assertEqual(r.result.output["baselineTotalCost"], "1400")
        self.assertEqual(r.result.output["actualTotalCost"], "1630")
        self.assertEqual(r.result.output["priceVariance"], "-70")
        self.assertEqual(r.result.output["mixVariance"], "160")
        self.assertEqual(r.result.output["quantityVariance"], "140")
        self.assertEqual(len(r.admission_sha256), 64)
        ss, pp, ii, cc = fixture()
        reversed_result = self.pvm(sources=ss[::-1], payloads=pp)
        self.assertEqual(r.admission_sha256, reversed_result.admission_sha256)

    def test_missing_admission_cannot_execute(self):
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate("HC.CAP.02", "MARKET_VALUE_WACC", {}, {},
                                  reference_mode=True)
        self.assertEqual(ex.exception.code, "CONTEXT_ADMISSION_REQUIRED")
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate("HC.CAP.02", "MARKET_VALUE_WACC", {}, {})
        self.assertEqual(ex.exception.code, "FINANCIAL_S2_REQUIRED")

    def test_admitted_wacc_input_policy(self):
        inputs = {"equityValue": "300", "debtValue": "100", "costOfEquity": "0.12",
                  "costOfDebt": "0.06", "taxRate": "0.2"}
        s = context("INPUT", inputs, methodology_id="HC.CAP.02", sku_set=("CAPITAL",))
        result = self.engine.calculate(
            "HC.CAP.02", "MARKET_VALUE_WACC", inputs, {},
            sources=[s], payloads_by_role={"INPUT": inputs}, reference_mode=True,
        )
        self.assertEqual(result.result.output["wacc"], "0.102")
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate(
                "HC.CAP.02", "MARKET_VALUE_WACC", {**inputs, "debtValue": "900"}, {},
                sources=[s], payloads_by_role={"INPUT": inputs}, reference_mode=True,
            )
        self.assertEqual(ex.exception.code, "SOURCE_INPUT_MISMATCH")

    def test_seeded_cross_context_pvm_denials(self):
        rng = random.Random(0x161616)
        mutants = [
            ("currency", "USD", "CROSS_CURRENCY_DATASET"),
            ("project_id", "OTHER", "CROSS_SCOPE_DATASET"),
            ("user_id", "OTHER", "CROSS_SCOPE_DATASET"),
            ("sku_set", ("A", "C"), "CROSS_SKU_DATASET"),
            ("period_type", "MONTH", "CROSS_PERIOD_DATASET"),
            ("period_start", "2025-12-31", "PVM_PERIOD_ORDER_MISMATCH"),
            ("methodology_id", "HC.COST.07", "CROSS_METHODOLOGY_DATASET"),
            ("methodology_version", "2.0", "CROSS_METHODOLOGY_DATASET"),
            ("methodology_sha256", "b" * 64, "CROSS_METHODOLOGY_DATASET"),
        ]
        count = 0
        for _ in range(50):
            for field, value, expected in rng.sample(mutants, len(mutants)):
                ss, _, _, _ = fixture()
                with self.subTest(field=field, count=count):
                    self.refuse(expected, sources=(ss[0], replace(ss[1], **{field: value})))
                    count += 1
        self.assertEqual(count, 450)

    def test_period_overlap_wrong_order_and_altered_source_fail(self):
        ss, pp, inp, _ = fixture()
        self.refuse("PVM_PERIOD_ORDER_MISMATCH",
                    sources=(ss[0], replace(ss[1], period_start="2025-12-01")))
        self.refuse("PVM_CONTEXT_INPUT_MISMATCH",
                    inputs={**inp, "actualPeriod": "2026-11-30"})
        edited = {**pp, "ACTUAL": {"rows": [
            {**r, "unitCost": "100"} for r in pp["ACTUAL"]["rows"]
        ]}}
        self.refuse("SOURCE_PAYLOAD_DIGEST_MISMATCH", payloads=edited)
        recomputed = replace(ss[1], payload_sha256=fingerprint(edited["ACTUAL"]))
        self.refuse("PVM_SOURCE_INPUT_MISMATCH", sources=(ss[0], recomputed), payloads=edited)

    def test_sku_schema_role_and_method_registry(self):
        ss, pp, _, _ = fixture()
        self.refuse("SOURCE_ROLE_MISMATCH",
                    sources=(ss[0], replace(ss[1], role="BASELINE")))
        invalid = {**pp, "ACTUAL": {"rows": [
            {"sku": "A", "quantity": "1"}]}}
        self.refuse("PVM_SOURCE_ROW_SCHEMA",
                    sources=(ss[0], replace(ss[1], payload_sha256=fingerprint(invalid["ACTUAL"]))),
                    payloads=invalid)
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate("HC.UNLISTED.01", "UNKNOWN", {}, {},
                                  sources=[], payloads_by_role={}, reference_mode=True)
        self.assertEqual(ex.exception.code, "CONTEXT_POLICY_NOT_APPROVED")
        self.assertEqual(len(POLICIES), 27)

    def test_single_sku_inventory_policy(self):
        inp = {"events": [{"date": "2026-01-01", "id": "P1",
                           "quantity": "10", "unitCost": "3"}]}
        s = context("INPUT", inp, methodology_id="HC.STOCK.01",
                    sku_set=("SKU_A", "SKU_B"))
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate("HC.STOCK.01", "FIFO_LOT_REPLAY", inp, {},
                                  sources=[s], payloads_by_role={"INPUT": inp},
                                  reference_mode=True)
        self.assertEqual(ex.exception.code, "MULTI_SKU_POOL_UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
