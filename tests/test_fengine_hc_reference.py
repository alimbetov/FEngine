"""Golden and fail-closed tests for the genuine, bounded HC Python executor.

These mathematical reference checks do NOT constitute independent financial S2.
"""
from __future__ import annotations

import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from fengine_hc import CalculationError, ContractRegistry, ReferenceEngine, npv

ROOT = Path(__file__).resolve().parents[1]


class HCReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = ReferenceEngine(ROOT)

    def run_model(self, model, variant, inputs, config=None):
        return self.e.calculate(model, variant, inputs, config or {}, reference_mode=True)

    def fails(self, code, fn):
        with self.assertRaises(CalculationError) as cm:
            fn()
        self.assertEqual(cm.exception.code, code)

    def test_catalogue_integrity_116_732_222(self):
        r = ContractRegistry(ROOT)
        self.assertEqual((len(r.models), len(r.params), len(r.variants)), (116, 732, 222))
        self.assertEqual(len({v["family"] for v in r.models.values()}), 20)

    def test_npv_golden_and_midperiod(self):
        inputs = {"cashflows": ["-1000", "600", "600"], "discountRate": "0.10"}
        result = self.run_model("HC.DCF.01", "PERIOD_END_NPV", inputs)
        expected = Decimal("-1000") + Decimal(600) / Decimal("1.1") + Decimal(600) / Decimal("1.21")
        self.assertLess(abs(Decimal(result.output["npv"]) - expected), Decimal("1e-30"))
        mid = self.run_model("HC.DCF.01", "MIDPERIOD_NPV", inputs)
        self.assertGreater(Decimal(mid.output["npv"]), Decimal(result.output["npv"]))
        self.assertEqual(result.execution_class, "PYTHON_REFERENCE_NOT_S2")

    def test_dated_npv_zero_discount(self):
        data = {"cashflows": [{"date": "2026-01-01", "amount": "-100"},
                               {"date": "2027-01-01", "amount": "110"}],
                "valuationDate": "2026-01-01", "discountRate": "0"}
        r = self.run_model("HC.DCF.02", "EXACT_DATE_XNPV", data, {"dayCount": "ACT_365_FIXED"})
        self.assertEqual(Decimal(r.output["xnpv"]), Decimal("10"))
        data["discountRate"] = "0.11"
        r2 = self.run_model("HC.DCF.02", "EXACT_DATE_XNPV", data, {"dayCount": "ACT_365_FIXED"})
        self.assertLess(Decimal(r2.output["xnpv"]), Decimal("0"))

    def test_capm_and_wacc(self):
        a = self.run_model("HC.CAP.01", "CAPM_BASE",
                           {"riskFreeRate": "0.04", "beta": "1.2", "marketRiskPremium": "0.06"})
        self.assertEqual(Decimal(a.output["costOfEquity"]), Decimal("0.112"))
        b = self.run_model("HC.CAP.02", "MARKET_VALUE_WACC",
                           {"equityValue": "60", "debtValue": "40",
                            "costOfEquity": "0.12", "costOfDebt": "0.08", "taxRate": "0.25"})
        self.assertEqual(Decimal(b.output["wacc"]), Decimal("0.096"))

    def test_asset_straight_line_and_syd(self):
        base = {"cost": "1200"}
        r = self.run_model("HC.ASSET.01", "STRAIGHT_LINE", base,
                           {"residualValue": "200", "usefulLifePeriods": 5})
        self.assertEqual([Decimal(x["depreciation"]) for x in r.output["periods"]],
                         [Decimal("200")] * 5)
        self.assertEqual(r.output["closingBalance"], "200")
        s = self.run_model("HC.ASSET.01", "SUM_OF_YEARS_DIGITS", {"cost": "1000"},
                           {"residualValue": "100", "usefulLifePeriods": 4})
        self.assertEqual(Decimal(s.output["periods"][0]["depreciation"]), Decimal(360))
        self.assertEqual(Decimal(s.output["periods"][-1]["depreciation"]), Decimal(90))

    def test_asset_production_and_declining(self):
        p = self.run_model("HC.ASSET.01", "UNITS_OF_PRODUCTION",
                           {"cost": "1000", "production": ["9000", "21000"]},
                           {"residualValue": "100", "usefulLifePeriods": 2,
                            "estimatedTotalProduction": "30000"})
        self.assertEqual(Decimal(p.output["periods"][0]["depreciation"]), Decimal(270))
        d = self.run_model("HC.ASSET.01", "DECLINING_BALANCE", {"cost": "1000"},
                           {"residualValue": "100", "usefulLifePeriods": 3,
                            "decliningRate": "0.4", "terminalTrueUpPolicy": "FINAL_PERIOD"})
        self.assertEqual(Decimal(d.output["closingBalance"]), Decimal(100))

    def test_dated_loan_annuity_reconciles(self):
        data = {"principal": "1000", "annualRate": "0.12",
                "startDate": "2026-01-01", "paymentDates": ["2026-02-01", "2026-03-01"],
                "dayCount": "ACT_365_FIXED"}
        r = self.run_model("HC.LOAN.02", "ANNUITY_EQUAL_PAYMENT_DATED", data)
        self.assertEqual(Decimal(r.output["closingPrincipal"]), Decimal(0))
        self.assertEqual(sum(Decimal(x["principal"]) for x in r.output["schedule"]), Decimal(1000))
        with localcontext() as ctx:
            ctx.prec = 40
            self.assertEqual(sum(Decimal(x["payment"]) for x in r.output["schedule"]),
                             Decimal(r.output["totalPayment"]))
        self.assertGreater(Decimal(r.output["totalInterest"]), Decimal(0))

    def test_dated_loan_equal_principal_and_balloon(self):
        data = {"principal": "1000", "annualRate": "0.12",
                "startDate": "2026-01-01", "paymentDates": ["2026-02-01", "2026-03-01"],
                "dayCount": "ACT_365_FIXED"}
        equal = self.run_model("HC.LOAN.02", "EQUAL_PRINCIPAL_DATED", data)
        self.assertEqual([Decimal(x["principal"]) for x in equal.output["schedule"]],
                         [Decimal(500), Decimal(500)])
        interest_only = self.run_model("HC.LOAN.02", "INTEREST_ONLY_BALLOON", data)
        self.assertEqual(Decimal(interest_only.output["schedule"][0]["principal"]), Decimal(0))
        self.assertEqual(Decimal(interest_only.output["schedule"][-1]["principal"]), Decimal(1000))
        bullet = self.run_model("HC.LOAN.02", "BULLET", data)
        self.assertEqual(Decimal(bullet.output["schedule"][0]["payment"]), Decimal(0))

    def test_fifo_and_wac_costing(self):
        events = [{"date": "2026-01-01", "id": "1", "quantity": "10", "unitCost": "10"},
                  {"date": "2026-01-02", "id": "2", "quantity": "10", "unitCost": "20"},
                  {"date": "2026-01-03", "id": "3", "quantity": "-12"}]
        fifo = self.run_model("HC.STOCK.01", "FIFO_LOT_REPLAY", {"events": events})
        wac = self.run_model("HC.STOCK.02", "MOVING_WAC", {"events": events})
        periodic = self.run_model("HC.STOCK.02", "PERIODIC_WAC", {"events": events})
        self.assertEqual(Decimal(fifo.output["costOfGoodsSold"]), Decimal(140))
        self.assertEqual(Decimal(wac.output["costOfGoodsSold"]), Decimal(180))
        self.assertEqual(Decimal(periodic.output["endingInventory"]), Decimal(120))

    def test_ageing_bucket_boundaries(self):
        data = {"obligations": [{"dueDate": "2026-03-15", "unpaidAmount": "10"},
                                 {"dueDate": "2026-02-15", "unpaidAmount": "20"},
                                 {"dueDate": "2026-01-01", "unpaidAmount": "30"}],
                "asOf": "2026-03-01"}
        c = {"ageingBucketEdges": [30, 60]}
        r = self.run_model("HC.SET.03", "DUE_DATE_AGING", data, c)
        self.assertEqual({k: Decimal(v) for k, v in r.output["buckets"].items()},
                         {"CURRENT": Decimal(10), "1-30": Decimal(20),
                          "31-60": Decimal(30), "61+": Decimal(0)})

    def test_llcr_plcr_different_horizons(self):
        d = {"cfads": ["100", "100", "100"], "outstandingDebt": "100",
             "discountRate": "0", "loanPeriods": 2}
        llcr = self.run_model("HC.PF.01", "LLCR_DEBT_LIFE", d)
        plcr = self.run_model("HC.PF.01", "PLCR_PROJECT_LIFE", d)
        self.assertEqual(Decimal(llcr.output["coverageRatio"]), Decimal(2))
        self.assertEqual(Decimal(plcr.output["coverageRatio"]), Decimal(3))

    def test_non_s2_guard_and_missing_models(self):
        self.fails("FINANCIAL_S2_REQUIRED", lambda:
                   self.e.calculate("HC.DCF.01", "PERIOD_END_NPV", {}, {}))
        self.fails("MODEL_NOT_IMPLEMENTED", lambda:
                   self.run_model("HC.ECL.03", "LIFETIME_TERM_PD", {}, {}))
        self.fails("VARIANT_NOT_IMPLEMENTED", lambda:
                   self.run_model("HC.ASSET.01", "SINKING_FUND_MGMT",
                                  {"cost": "1000"}, {"residualValue": "0", "usefulLifePeriods": 2}))

    def test_reject_float_missing_and_configuration_conflicts(self):
        self.fails("BINARY_FLOAT_FORBIDDEN", lambda:
                   self.run_model("HC.DCF.01", "PERIOD_END_NPV",
                                  {"cashflows": ["-1", "2"], "discountRate": 0.1}))
        self.fails("DAY_COUNT_REQUIRED", lambda:
                   self.run_model("HC.DCF.02", "EXACT_DATE_XNPV", {}, {}))
        self.fails("VARIANT_CONFIG_CONFLICT", lambda:
                   self.run_model("HC.DCF.01", "PERIOD_END_NPV",
                                  {"cashflows": ["1"], "discountRate": "0"},
                                  {"timingConvention": "MIDPERIOD"}))
        self.fails("UNKNOWN_PARAMETER", lambda:
                   self.run_model("HC.CAP.01", "CAPM_BASE", {}, {"notInCatalogue": "1"}))
        self.fails("UNCONSUMED_CONFIGURATION", lambda:
                   self.run_model("HC.CAP.01", "CAPM_BASE", {},
                                  {"riskFreeCurve": "unresolved"}))

    def test_stock_never_negative(self):
        self.fails("NEGATIVE_INVENTORY", lambda:
                   self.run_model("HC.STOCK.01", "FIFO_LOT_REPLAY",
                                  {"events": [{"date": "2026-01-01", "id": "x", "quantity": "-1"}]}))

    def test_results_pinned_hashes(self):
        d = {"cashflows": ["-1", "2"], "discountRate": "0.1"}
        r1 = self.run_model("HC.DCF.01", "PERIOD_END_NPV", d)
        r2 = self.run_model("HC.DCF.01", "PERIOD_END_NPV", d)
        r3 = self.run_model("HC.DCF.01", "PERIOD_END_NPV",
                            {"cashflows": ["-1", "3"], "discountRate": "0.1"})
        self.assertEqual(r1.output_sha256, r2.output_sha256)
        self.assertNotEqual(r1.output_sha256, r3.output_sha256)


    def test_all_implemented_variant_mathematical_controls(self):
        target = self.run_model("HC.CAP.02", "TARGET_WEIGHT_WACC",
                                {"equityValue": "60", "debtValue": "40",
                                 "costOfEquity": "0.12", "costOfDebt": "0.08",
                                 "taxRate": "0.25"})
        self.assertEqual(Decimal(target.output["wacc"]), Decimal("0.096"))
        ddb = self.run_model("HC.ASSET.01", "DOUBLE_DECLINING", {"cost": "1000"},
                             {"residualValue": "100", "usefulLifePeriods": 4})
        self.assertEqual(Decimal(ddb.output["periods"][0]["depreciation"]), Decimal(500))
        self.assertEqual(Decimal(ddb.output["closingBalance"]), Decimal(100))
        grace = self.run_model("HC.SET.03", "GRACE_ADJUSTED_AGING",
                               {"asOf": "2026-03-01",
                                "obligations": [{"dueDate": "2026-02-28", "unpaidAmount": "10"}]},
                               {"ageingBucketEdges": [30, 60], "graceDays": 2})
        self.assertEqual(Decimal(grace.output["buckets"]["CURRENT"]), Decimal(10))

    def test_result_is_deeply_immutable(self):
        result = self.run_model("HC.ASSET.01", "STRAIGHT_LINE", {"cost": "1200"},
                                {"residualValue": "200", "usefulLifePeriods": 5})
        with self.assertRaises(TypeError):
            result.output["closingBalance"] = "0"
        with self.assertRaises(TypeError):
            result.output["periods"][0]["closingBalance"] = "0"

    def test_unconsumed_input_fail_closed(self):
        self.fails("UNCONSUMED_INPUT", lambda:
                   self.run_model("HC.ASSET.01", "STRAIGHT_LINE",
                                  {"cost": "1000", "serviceDate": "2026-07-01"},
                                  {"residualValue": "0", "usefulLifePeriods": 5}))
        self.fails("UNCONSUMED_INPUT", lambda:
                   self.run_model("HC.ASSET.01", "STRAIGHT_LINE",
                                  {"cost": "1000", "production": ["100"]},
                                  {"residualValue": "0", "usefulLifePeriods": 1}))


if __name__ == "__main__":
    unittest.main()
