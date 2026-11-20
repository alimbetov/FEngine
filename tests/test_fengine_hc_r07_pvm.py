"""HC-R0.7 independent cost PVM goldens and fail-closed input tests."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.r07_pvm import CONVENTION, pvm_revision_hashes

ROOT = Path(__file__).resolve().parents[1]
BASE_ROWS = [
    {"sku": "A", "baselineQuantity": "60", "actualQuantity": "50",
     "baselineUnitCost": "10", "actualUnitCost": "11"},
    {"sku": "B", "baselineQuantity": "40", "actualQuantity": "60",
     "baselineUnitCost": "20", "actualUnitCost": "18"},
]


def pvm_fixture(rows=None, *, currency="KZT", unit="PCS",
                baseline="2025-12-31", actual="2026-12-31"):
    values = [dict(x) for x in (BASE_ROWS if rows is None else rows)]
    hashes = pvm_revision_hashes(baseline, actual, currency, unit, values)
    inputs = {"baselinePeriod": baseline, "actualPeriod": actual,
              "currency": currency, "quantityUnit": unit, "rows": values,
              "baselineRevisionSha256": hashes["baselineRevisionSha256"],
              "actualRevisionSha256": hashes["actualRevisionSha256"]}
    config = {"interactionAllocation": CONVENTION,
              "standardCostVintage": hashes["standardCostVintage"],
              "volumeBaseline": hashes["volumeBaseline"]}
    return inputs, config


class R07PvmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def calculate(self, variant="PRICE_VARIANCE", fixture=None, config=None):
        if fixture is None:
            inp, cfg = pvm_fixture()
        else:
            inp, cfg = fixture
        return self.engine.calculate(
            "HC.COST.08", variant, inp, cfg if config is None else config,
            reference_mode=True
        )

    def err(self, code, action):
        with self.assertRaises(CalculationError) as raised:
            action()
        self.assertEqual(raised.exception.code, code)

    def test_true_three_factor_sequential_cost_bridge(self):
        output = self.calculate().output
        self.assertEqual(Decimal(output["baselineTotalCost"]), 1400)
        self.assertEqual(Decimal(output["actualTotalCost"]), 1630)
        self.assertEqual(Decimal(output["baselineUnitCostAtActualQuantities"]), 1700)
        self.assertEqual(Decimal(output["baselineQuantity"]), 100)
        self.assertEqual(Decimal(output["actualQuantity"]), 110)
        self.assertEqual(Decimal(output["baselineWeightedUnitCost"]), 14)
        self.assertEqual(Decimal(output["quantityVariance"]), 140)
        self.assertEqual(Decimal(output["mixVariance"]), 160)
        self.assertEqual(Decimal(output["priceVariance"]), -70)
        self.assertEqual(Decimal(output["totalCostVariance"]), 230)
        self.assertEqual(Decimal(output["reconciliationDifference"]), 0)

    def test_each_catalog_variant_has_own_focus_without_changing_math(self):
        expected = {
            "PRICE_VARIANCE": ("PRICE", Decimal("-70")),
            "QUANTITY_VARIANCE": ("TOTAL_VOLUME", Decimal("140")),
            "MIX_VARIANCE": ("MIX", Decimal("160")),
        }
        for variant, (focus, effect) in expected.items():
            with self.subTest(variant=variant):
                result = self.calculate(variant)
                self.assertEqual(result.output["selectedFactor"], focus)
                self.assertEqual(Decimal(result.output["selectedVariance"]), effect)
                self.assertEqual(Decimal(result.output["totalCostVariance"]), 230)
                self.assertEqual(result.execution_class, "PYTHON_REFERENCE_NOT_S2")
                self.assertEqual(result.output["costSignConvention"],
                                 "POSITIVE_COST_INCREASE_ADVERSE")

    def test_pure_price_change_has_zero_volume_and_mix(self):
        rows = [dict(x) for x in BASE_ROWS]
        for r in rows:
            r["actualQuantity"] = r["baselineQuantity"]
        r = self.calculate(fixture=pvm_fixture(rows)).output
        self.assertEqual(Decimal(r["quantityVariance"]), 0)
        self.assertEqual(Decimal(r["mixVariance"]), 0)
        self.assertEqual(Decimal(r["priceVariance"]), 60 - 80)
        self.assertEqual(Decimal(r["totalCostVariance"]), -20)

    def test_only_total_volume_changes_for_unchanged_mix_and_cost(self):
        rows = [dict(x) for x in BASE_ROWS]
        for r in rows:
            r["actualQuantity"] = str(Decimal(r["baselineQuantity"]) * 2)
            r["actualUnitCost"] = r["baselineUnitCost"]
        out = self.calculate(fixture=pvm_fixture(rows)).output
        self.assertEqual(Decimal(out["quantityVariance"]), 1400)
        self.assertEqual(Decimal(out["mixVariance"]), 0)
        self.assertEqual(Decimal(out["priceVariance"]), 0)
        self.assertEqual(Decimal(out["totalCostVariance"]), 1400)

    def test_pure_mix_change_at_constant_total_quantity(self):
        rows = [dict(x) for x in BASE_ROWS]
        rows[0]["actualQuantity"] = "50"
        rows[1]["actualQuantity"] = "50"
        for r in rows:
            r["actualUnitCost"] = r["baselineUnitCost"]
        out = self.calculate(fixture=pvm_fixture(rows)).output
        self.assertEqual(Decimal(out["quantityVariance"]), 0)
        self.assertEqual(Decimal(out["priceVariance"]), 0)
        self.assertEqual(Decimal(out["mixVariance"]), 100)
        self.assertEqual(Decimal(out["totalCostVariance"]), 100)

    def test_product_order_does_not_change_revision_hashes_or_values(self):
        inp, cfg = pvm_fixture()
        reordered, reorder_config = pvm_fixture(list(reversed(BASE_ROWS)))
        self.assertEqual(inp["baselineRevisionSha256"], reordered["baselineRevisionSha256"])
        self.assertEqual(inp["actualRevisionSha256"], reordered["actualRevisionSha256"])
        self.assertEqual(cfg, reorder_config)
        self.assertEqual(self.calculate(fixture=(inp, cfg)).output["totalCostVariance"],
                         self.calculate(fixture=(reordered, reorder_config)).output["totalCostVariance"])

    def test_duplicate_sku_and_new_sku_without_baseline_policy_fail(self):
        self.err("PVM_DUPLICATE_SKU", lambda: pvm_fixture([BASE_ROWS[0], BASE_ROWS[0]]))
        new_sku = [dict(r) for r in BASE_ROWS]
        new_sku.append({"sku": "C", "baselineQuantity": "0", "actualQuantity": "1",
                        "baselineUnitCost": "5", "actualUnitCost": "6"})
        self.err("PVM_NEW_OR_ZERO_BASE_SKU_REQUIRES_POLICY", lambda: pvm_fixture(new_sku))

    def test_zero_total_actual_volume_and_negative_values_are_rejected(self):
        rows = [{**row, "actualQuantity": "0"} for row in BASE_ROWS]
        self.err("PVM_TOTAL_VOLUME_UNDEFINED", lambda:
                 self.calculate(fixture=pvm_fixture(rows)))
        bad = [dict(row) for row in BASE_ROWS]
        bad[0]["actualUnitCost"] = "-1"
        self.err("PVM_NEGATIVE_QUANTITY_OR_COST", lambda: pvm_fixture(bad))
        bad = [dict(row) for row in BASE_ROWS]
        bad[0]["actualQuantity"] = "-2"
        self.err("PVM_NEGATIVE_QUANTITY_OR_COST", lambda: pvm_fixture(bad))

    def test_source_digest_mismatch_and_standard_cost_drift_fail(self):
        inp, cfg = pvm_fixture()
        changed = {**inp, "rows": [dict(x) for x in inp["rows"]]}
        changed["rows"][0]["actualQuantity"] = "51"
        self.err("PVM_SOURCE_DIGEST_MISMATCH", lambda:
                 self.calculate(fixture=(changed, cfg)))
        self.err("PVM_STANDARD_COST_REVISION_MISMATCH", lambda:
                 self.calculate(fixture=(inp, {**cfg, "standardCostVintage": "a"*64})))
        self.err("PVM_VOLUME_BASELINE_REVISION_MISMATCH", lambda:
                 self.calculate(fixture=(inp, {**cfg, "volumeBaseline": "b"*64})))

    def test_unqualified_allocation_and_binary_float_fail(self):
        inp, cfg = pvm_fixture()
        self.err("ENUM_OUT_OF_RANGE", lambda:
                 self.calculate(fixture=(inp, {**cfg, "interactionAllocation": "SHAPLEY"})))
        rows = [dict(x) for x in BASE_ROWS]
        rows[0]["actualQuantity"] = 50.0
        self.err("BINARY_FLOAT_FORBIDDEN", lambda:
                 self.calculate(fixture=(pvm_fixture()[0] | {"rows": rows}, cfg)))

    def test_periods_currency_and_units_must_be_explicit(self):
        self.err("PVM_BASELINE_MUST_PRECEDE_ACTUAL", lambda:
                 pvm_fixture(actual="2024-12-31"))
        self.err("PVM_CURRENCY_REQUIRED", lambda: pvm_fixture(currency="kzt"))
        self.err("PVM_QUANTITY_UNIT_REQUIRED", lambda: pvm_fixture(unit="pieces"))
        inp, cfg = pvm_fixture()
        self.err("PVM_INPUT_SCHEMA", lambda:
                 self.calculate(fixture=({**inp, "additionalCurrency": "USD"}, cfg)))

    def test_multiple_datasets_reconcile_three_factors(self):
        for new_q1, new_q2, cost1, cost2 in (
            ("20", "80", "12.25", "17.75"),
            ("120", "10", "11", "19"),
            ("60", "40", "10", "20"),
            ("1", "1", "1", "1"),
            ("0", "100", "0", "40"),
        ):
            with self.subTest(q1=new_q1, q2=new_q2):
                rows = [dict(x) for x in BASE_ROWS]
                rows[0].update(actualQuantity=new_q1, actualUnitCost=cost1)
                rows[1].update(actualQuantity=new_q2, actualUnitCost=cost2)
                result = self.calculate(fixture=pvm_fixture(rows)).output
                effects = sum((
                    Decimal(result["priceVariance"]),
                    Decimal(result["quantityVariance"]),
                    Decimal(result["mixVariance"]),
                ))
                self.assertLessEqual(
                    abs(effects - Decimal(result["totalCostVariance"])),
                    Decimal("1e-30")
                )
                self.assertLessEqual(
                    abs(Decimal(result["baselineTotalCost"]) +
                        Decimal(result["totalCostVariance"]) -
                        Decimal(result["actualTotalCost"])), Decimal("1e-30")
                )

    def test_r07_source_and_output_receipt_hashes_change_with_data(self):
        a = self.calculate()
        inp, cfg = pvm_fixture()
        inp["rows"][0]["actualUnitCost"] = "12"
        revised, revised_cfg = pvm_fixture(inp["rows"])
        b = self.calculate(fixture=(revised, revised_cfg))
        self.assertNotEqual(a.inputs_sha256, b.inputs_sha256)
        self.assertNotEqual(a.output_sha256, b.output_sha256)
        with self.assertRaises(TypeError):
            a.output["priceVariance"] = "0"

    def test_financial_s2_admission_stays_closed(self):
        inp, cfg = pvm_fixture()
        self.err("FINANCIAL_S2_REQUIRED", lambda:
                 self.engine.calculate("HC.COST.08", "PRICE_VARIANCE", inp, cfg))


if __name__ == "__main__":
    unittest.main()
