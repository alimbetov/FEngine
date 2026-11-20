"""HC-R0.3 algebraic invariants, exact-value boundary matrices."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc import ReferenceEngine

ROOT = Path(__file__).resolve().parents[1]


class R03InvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def calc(self, model, variant, inputs, config):
        return self.engine.calculate(model, variant, inputs, config, reference_mode=True).output

    def test_break_even_whole_units_are_minimal_across_fixed_cost_edges(self):
        for fixed in ("0", "0.01", "1", "39.99", "40", "40.01",
                      "1000", "1001", "123456.789", "999999999.99"):
            with self.subTest(fixed=fixed):
                out = self.calc("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN",
                                {"fixedCost": fixed, "unitPrice": "100",
                                 "unitVariableCost": "60",
                                 "currency": "KZT", "quantityUnit": "PCS"},
                                {"minimumLotRule": "WHOLE_UNITS"})
                n = out["minimumWholeUnits"]
                margin = Decimal(out["unitContribution"])
                fixed_amount = Decimal(fixed)
                self.assertGreaterEqual(n * margin, fixed_amount)
                if n > 0:
                    self.assertLess((n - 1) * margin, fixed_amount)

    def test_both_evm_forecasts_reconcile_and_differ_with_overrun(self):
        for ev, ac, bac in (("1", "2", "10"), ("60", "75", "120"),
                            ("80", "40", "100"), ("45", "90", "150")):
            with self.subTest(ev=ev, ac=ac, bac=bac):
                inp = {"asOf": "2026-06-30", "baselineRevision": "BASELINE-REFERENCE",
                       "plannedValue": "50", "earnedValue": ev,
                       "actualCost": ac, "budgetAtCompletion": bac, "currency": "KZT"}
                e1 = self.calc("HC.COST.07", "EVM_BAC_CPI", inp,
                               {"earnedValueRule": "EXTERNALLY_SUPPLIED_EV",
                                "eacFormula": "BAC_DIV_CPI"})
                e2 = self.calc("HC.COST.07", "EVM_EAC_FORECAST", inp,
                               {"earnedValueRule": "EXTERNALLY_SUPPLIED_EV",
                                "eacFormula": "AC_PLUS_REMAINING_AT_BUDGET"})
                cpi = Decimal(ev) / Decimal(ac)
                self.assertLess(abs(Decimal(e1["estimateAtCompletion"]) -
                                    Decimal(bac) / cpi), Decimal("1e-30"))
                self.assertEqual(Decimal(e2["estimateAtCompletion"]),
                                 Decimal(ac) + Decimal(bac) - Decimal(ev))
                self.assertLess(abs(Decimal(e1["varianceAtCompletion"]) +
                                    Decimal(e1["estimateAtCompletion"]) - Decimal(bac)),
                                Decimal("1e-30"))

    def test_gordon_value_increases_with_growth_if_wacc_fixed(self):
        inp = {"finalForecastFCFF": "100", "wacc": "0.1",
               "forecastPeriods": 3, "currency": "KZT"}
        vals = []
        for g in ("-0.02", "0", "0.02", "0.05", "0.08"):
            out = self.calc("HC.DCF.07", "GORDON_FCFF_TERMINAL", inp,
                            {"terminalMethod": "GORDON_FCFF", "terminalGrowth": g})
            vals.append(Decimal(out["presentValueOfTerminal"]))
            self.assertGreater(vals[-1], 0)
        self.assertEqual(vals, sorted(vals))
        self.assertEqual(len(set(vals)), len(vals))


if __name__ == "__main__":
    unittest.main()
