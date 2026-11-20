"""HC-R0.3 executable goldens and adversarial numerical controls.

Reference only: no financial S2, no source-fact qualification or persistence.
"""
from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.semantics import ParameterSemantics

ROOT = Path(__file__).resolve().parents[1]


class NewModelReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.semantic = ParameterSemantics(ROOT)

    def calc(self, model, variant, inputs, config):
        return self.engine.calculate(model, variant, inputs, config, reference_mode=True)

    def fails(self, code, call):
        with self.assertRaises(CalculationError) as raised:
            call()
        self.assertEqual(raised.exception.code, code)

    @staticmethod
    def runway_input(flows=None):
        return {
            "asOf": "2026-01-01", "openingCash": "100", "currency": "KZT",
            "cashflows": flows or [
                {"date": "2026-01-03", "netCashflow": "-30"},
                {"date": "2026-01-10", "netCashflow": "-50"},
                {"date": "2026-01-11", "netCashflow": "-1"},
            ],
        }

    def test_runway_strict_breach_vs_equality(self):
        r = self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", self.runway_input(),
                      {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR"})
        self.assertEqual(r.output["firstBreachDate"], "2026-01-11")
        self.assertEqual(r.output["elapsedDays"], 10)
        self.assertEqual(r.output["cashAtFirstBreach"], "19")
        self.assertEqual(r.output["closingCash"], "19")
        self.assertEqual(r.output["timeline"][1]["closingCash"], "20")
        self.assertEqual(r.output["currency"], "KZT")
        inclusive = self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", self.runway_input(),
                              {"floorValue": "20", "firstPassageRule": "AT_OR_BELOW_FLOOR"})
        self.assertEqual(inclusive.output["firstBreachDate"], "2026-01-10")
        self.assertEqual(inclusive.output["elapsedDays"], 9)
        self.assertNotEqual(r.output_sha256, inclusive.output_sha256)

    def test_runway_without_breach_preserves_no_breach_not_zero(self):
        inp = self.runway_input([{"date": "2026-01-03", "netCashflow": "10"}])
        r = self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", inp,
                      {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR"})
        self.assertEqual(r.output["status"], "NO_BREACH_WITHIN_HORIZON")
        self.assertIsNone(r.output["firstBreachDate"])
        self.assertIsNone(r.output["elapsedDays"])
        self.assertEqual(r.output["closingCash"], "110")

    def test_runway_opening_cash_breach_is_zero_days(self):
        inp = self.runway_input([{"date": "2026-01-02", "netCashflow": "100"}])
        inp["openingCash"] = "10"
        r = self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", inp,
                      {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR"})
        self.assertEqual(r.output["firstBreachDate"], "2026-01-01")
        self.assertEqual(r.output["elapsedDays"], 0)
        self.assertEqual(r.output["closingCash"], "110")

    def test_scenario_runway_separates_paths_no_probabilities(self):
        inp = {"asOf": "2026-01-01", "openingCash": "100", "currency": "KZT",
               "scenarios": [
                   {"scenarioId": "BASE", "cashflows": [
                       {"date": "2026-01-05", "netCashflow": "10"}]},
                   {"scenarioId": "STRESS", "cashflows": [
                       {"date": "2026-01-05", "netCashflow": "-95"}]},
               ]}
        config = {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR"}
        r = self.calc("HC.CASH.03", "SCENARIO_RUNWAY", inp, config)
        self.assertEqual(r.output["classification"], "DETERMINISTIC_PATHS_NO_PROBABILITIES")
        self.assertEqual(r.output["scenarios"][0]["status"], "NO_BREACH_WITHIN_HORIZON")
        self.assertEqual(r.output["scenarios"][1]["firstBreachDate"], "2026-01-05")
        self.assertEqual(r.output["scenarios"][1]["elapsedDays"], 4)

    def test_runway_rejects_wrong_order_duplicates_and_unknown_fields(self):
        conf = {"floorValue": "0", "firstPassageRule": "STRICT_BELOW_FLOOR"}
        self.fails("CASHFLOW_DATES_NOT_STRICTLY_INCREASING", lambda:
            self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY",
                      self.runway_input([{"date": "2026-01-03", "netCashflow": "10"},
                                         {"date": "2026-01-03", "netCashflow": "5"}]), conf))
        inp = self.runway_input()
        inp["cashflows"][0]["currency"] = "USD"
        self.fails("CASHFLOW_ROW_SCHEMA", lambda:
            self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", inp, conf))
        self.fails("CURRENCY_CODE_REQUIRED", lambda:
            self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY",
                      {**self.runway_input(), "currency": "kzt"}, conf))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
            self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", self.runway_input(),
                      {"floorValue": "0", "firstPassageRule": "UNKNOWN"}))

    def test_runway_scenario_duplicate_rejected(self):
        inp = {"asOf": "2026-01-01", "openingCash": "100", "currency": "KZT",
               "scenarios": [{"scenarioId": "A", "cashflows": [
                   {"date": "2026-01-02", "netCashflow": "0"}]}] * 2}
        self.fails("RUNWAY_SCENARIO_ID_INVALID_OR_DUPLICATE", lambda:
            self.calc("HC.CASH.03", "SCENARIO_RUNWAY", inp,
                      {"floorValue": "0", "firstPassageRule": "STRICT_BELOW_FLOOR"}))

    @staticmethod
    def single_input(fixed="1000"):
        return {"fixedCost": fixed, "unitPrice": "100", "unitVariableCost": "60",
                "currency": "KZT", "quantityUnit": "PCS"}

    def test_single_product_breakeven_exact_and_integer(self):
        r = self.calc("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN",
                      self.single_input(), {"minimumLotRule": "WHOLE_UNITS"})
        self.assertEqual(Decimal(r.output["unitContribution"]), Decimal("40"))
        self.assertEqual(Decimal(r.output["breakEvenUnitsExact"]), Decimal("25"))
        self.assertEqual(r.output["minimumWholeUnits"], 25)
        self.assertEqual(Decimal(r.output["revenueAtMinimumUnits"]), Decimal("2500"))
        edge = self.calc("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN",
                         self.single_input("1001"), {"minimumLotRule": "WHOLE_UNITS"})
        self.assertEqual(edge.output["minimumWholeUnits"], 26)
        self.assertGreaterEqual(Decimal(edge.output["contributionAtMinimumUnits"]), Decimal(1001))
        self.assertLess(Decimal(25) * Decimal(40), Decimal(1001))

    def test_single_breakeven_rejects_negative_margin_float_and_policy(self):
        inp = self.single_input()
        inp["unitPrice"] = "60"
        self.fails("NONPOSITIVE_CONTRIBUTION_MARGIN", lambda:
                   self.calc("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN", inp,
                             {"minimumLotRule": "WHOLE_UNITS"}))
        self.fails("BINARY_FLOAT_FORBIDDEN", lambda:
                   self.calc("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN",
                             {**self.single_input(), "fixedCost": 1000.0},
                             {"minimumLotRule": "WHOLE_UNITS"}))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
                   self.calc("HC.COST.04", "SINGLE_PRODUCT_BREAKEVEN",
                             self.single_input(), {"minimumLotRule": "CONTINUOUS"}))

    def test_fixed_bundle_product_mix_breakeven(self):
        inp = {"fixedCost": "1000", "currency": "KZT", "products": [
            {"sku": "A", "unitsPerBundle": 2, "unitPrice": "100", "unitVariableCost": "60"},
            {"sku": "B", "unitsPerBundle": 1, "unitPrice": "70", "unitVariableCost": "40"},
        ]}
        conf = {"minimumLotRule": "WHOLE_BUNDLES", "mixtureBundleIntegrality": True}
        r = self.calc("HC.COST.04", "PRODUCT_MIX_BREAKEVEN", inp, conf)
        self.assertEqual(Decimal(r.output["bundleContribution"]), Decimal(110))
        self.assertEqual(Decimal(r.output["bundleRevenue"]), Decimal(270))
        self.assertEqual(r.output["minimumWholeBundles"], 10)
        self.assertEqual(r.output["minimumUnitsByProduct"][0]["units"], 20)
        self.assertEqual(r.output["minimumUnitsByProduct"][1]["units"], 10)
        self.assertEqual(Decimal(r.output["revenueAtMinimumBundles"]), Decimal(2700))
        self.assertLess(Decimal(9) * Decimal(110), Decimal(1000))

    def test_mix_breakeven_rejects_fractional_bundle_and_duplicate_sku(self):
        inp = {"fixedCost": "100", "currency": "KZT",
               "products": [{"sku": "A", "unitsPerBundle": 2,
                             "unitPrice": "5", "unitVariableCost": "1"}]}
        cfg = {"minimumLotRule": "WHOLE_BUNDLES", "mixtureBundleIntegrality": True}
        self.fails("INVALID_INTEGER", lambda:
            self.calc("HC.COST.04", "PRODUCT_MIX_BREAKEVEN",
                      {**inp, "products": [{**inp["products"][0], "unitsPerBundle": "2"}]}, cfg))
        self.fails("BREAK_EVEN_DUPLICATE_SKU", lambda:
            self.calc("HC.COST.04", "PRODUCT_MIX_BREAKEVEN",
                      {**inp, "products": inp["products"] * 2}, cfg))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
            self.calc("HC.COST.04", "PRODUCT_MIX_BREAKEVEN",
                      inp, {"minimumLotRule": "WHOLE_BUNDLES",
                            "mixtureBundleIntegrality": False}))

    @staticmethod
    def evm_input():
        return {"asOf": "2026-06-30", "baselineRevision": "BASELINE-SHA-A",
                "plannedValue": "80", "earnedValue": "60", "actualCost": "75",
                "budgetAtCompletion": "120", "currency": "KZT"}

    def test_evm_cpi_and_two_distinct_forecasts(self):
        inp = self.evm_input()
        a = self.calc("HC.COST.07", "EVM_BAC_CPI", inp,
                      {"earnedValueRule": "EXTERNALLY_SUPPLIED_EV",
                       "eacFormula": "BAC_DIV_CPI"})
        b = self.calc("HC.COST.07", "EVM_EAC_FORECAST", inp,
                      {"earnedValueRule": "EXTERNALLY_SUPPLIED_EV",
                       "eacFormula": "AC_PLUS_REMAINING_AT_BUDGET"})
        self.assertEqual(Decimal(a.output["costPerformanceIndex"]), Decimal("0.8"))
        self.assertEqual(Decimal(a.output["costVariance"]), Decimal("-15"))
        self.assertEqual(Decimal(a.output["scheduleVariance"]), Decimal("-20"))
        self.assertEqual(Decimal(a.output["estimateAtCompletion"]), Decimal(150))
        self.assertEqual(Decimal(a.output["varianceAtCompletion"]), Decimal(-30))
        self.assertEqual(Decimal(b.output["estimateAtCompletion"]), Decimal(135))
        self.assertEqual(Decimal(b.output["varianceAtCompletion"]), Decimal(-15))
        self.assertNotEqual(a.output_sha256, b.output_sha256)

    def test_evm_zero_denominator_and_unqualified_inputs_fail(self):
        cfg = {"earnedValueRule": "EXTERNALLY_SUPPLIED_EV", "eacFormula": "BAC_DIV_CPI"}
        self.fails("EVM_ZERO_ACTUAL_COST_CPI_UNDEFINED", lambda:
            self.calc("HC.COST.07", "EVM_BAC_CPI",
                      {**self.evm_input(), "actualCost": "0"}, cfg))
        self.fails("EVM_ZERO_CPI_FORECAST_UNDEFINED", lambda:
            self.calc("HC.COST.07", "EVM_BAC_CPI",
                      {**self.evm_input(), "earnedValue": "0"}, cfg))
        self.fails("EVM_INVALID_BASELINE_OR_PROGRESS", lambda:
            self.calc("HC.COST.07", "EVM_BAC_CPI",
                      {**self.evm_input(), "earnedValue": "130"}, cfg))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
            self.calc("HC.COST.07", "EVM_BAC_CPI",
                      self.evm_input(), {**cfg, "eacFormula": "AC_PLUS_REMAINING_AT_BUDGET"}))

    def test_gordon_terminal_exact_independent_goldens(self):
        inp = {"finalForecastFCFF": "100", "wacc": "0.10",
               "forecastPeriods": 1, "currency": "KZT"}
        r = self.calc("HC.DCF.07", "GORDON_FCFF_TERMINAL", inp,
                      {"terminalMethod": "GORDON_FCFF", "terminalGrowth": "0.02"})
        self.assertEqual(Decimal(r.output["nextPeriodFCFF"]), Decimal(102))
        self.assertEqual(Decimal(r.output["terminalAtForecastHorizon"]), Decimal(1275))
        self.assertLess(abs(Decimal(r.output["presentValueOfTerminal"]) -
                            Decimal(12750)/Decimal(11)), Decimal("1e-32"))
        self.assertEqual(r.output["classification"], "GORDON_FCFF_REFERENCE_NOT_FINANCIAL_S2")

    def test_gordon_rejects_wacc_below_growth_and_negative_fcff(self):
        inp = {"finalForecastFCFF": "100", "wacc": "0.03",
               "forecastPeriods": 1, "currency": "KZT"}
        self.fails("GORDON_RATE_OR_GROWTH_DOMAIN", lambda:
                   self.calc("HC.DCF.07", "GORDON_FCFF_TERMINAL", inp,
                             {"terminalMethod": "GORDON_FCFF", "terminalGrowth": "0.03"}))
        self.fails("NEGATIVE_TERMINAL_FCFF_UNSUPPORTED", lambda:
                   self.calc("HC.DCF.07", "GORDON_FCFF_TERMINAL",
                             {**inp, "finalForecastFCFF": "-1"},
                             {"terminalMethod": "GORDON_FCFF", "terminalGrowth": "0.01"}))
        self.fails("BINARY_FLOAT_FORBIDDEN", lambda:
                   self.calc("HC.DCF.07", "GORDON_FCFF_TERMINAL",
                             {**inp, "forecastPeriods": 1.5},
                             {"terminalMethod": "GORDON_FCFF", "terminalGrowth": "0.01"}))

    def test_variant_resolver_has_deep_immutable_and_stable_config(self):
        cfg = {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR"}
        r = self.semantic.resolve("HC.CASH.03", "DETERMINISTIC_RUNWAY",
                                  cfg, reference_mode=True)
        self.assertEqual(r.config["floorValue"], "20")
        self.assertEqual(r.config_sha256,
                         self.semantic.resolve("HC.CASH.03", "DETERMINISTIC_RUNWAY",
                                               cfg, reference_mode=True).config_sha256)
        with self.assertRaises(TypeError):
            r.config["floorValue"] = "10000"
        cfg["floorValue"] = "999"
        self.assertEqual(r.config["floorValue"], "20")
        nested = self.semantic.resolve("HC.DCF.03", "ALL_REAL_IRR_ROOTS",
                        {"rootDomain": {"minRate": "-0.9", "maxRate": "5"},
                         "rootCompletenessPolicy": "CERTIFIED_ALL"}, reference_mode=True)
        with self.assertRaises(TypeError):
            nested.config["rootDomain"]["minRate"] = "-0.8"

    def test_uncertified_variants_and_production_remain_closed(self):
        inp = {"finalForecastFCFF": "100", "wacc": "0.1",
               "forecastPeriods": 1, "currency": "KZT"}
        self.fails("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
            self.calc("HC.DCF.07", "EXIT_MULTIPLE_APPROVED", inp, {}))
        self.fails("FINANCIAL_S2_REQUIRED", lambda:
            self.engine.calculate("HC.DCF.07", "GORDON_FCFF_TERMINAL", inp,
                                  {"terminalMethod": "GORDON_FCFF", "terminalGrowth": "0.02"}))
        self.fails("UNKNOWN_PARAMETER", lambda:
            self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", self.runway_input(),
                      {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR",
                       "unapproved": "any"}))
        self.fails("UNCONSUMED_CONFIGURATION", lambda:
            self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", self.runway_input(),
                      {"floorValue": "20", "firstPassageRule": "STRICT_BELOW_FLOOR",
                       "horizon": 12}))

    def test_result_is_deeply_immutable_and_source_is_not_mutated(self):
        inp = self.runway_input()
        snapshot = [dict(x) for x in inp["cashflows"]]
        r = self.calc("HC.CASH.03", "DETERMINISTIC_RUNWAY", inp,
                      {"floorValue": "0", "firstPassageRule": "STRICT_BELOW_FLOOR"})
        self.assertEqual(inp["cashflows"], snapshot)
        with self.assertRaises(TypeError):
            r.output["closingCash"] = "0"
        with self.assertRaises(TypeError):
            r.output["timeline"][0]["closingCash"] = "0"


if __name__ == "__main__":
    unittest.main()
