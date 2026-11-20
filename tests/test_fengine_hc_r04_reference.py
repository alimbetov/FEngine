"""HC-R0.4 math goldens, strict source bindings, variants and failure modes."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.semantics import ParameterSemantics

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "a" * 64
OTHER_SHA = "b" * 64


def cfo_inputs():
    return {"asOf": "2026-12-31", "currency": "KZT", "sourceRevisionSha256": SOURCE_SHA,
            "netIncome": "100", "noncashAdjustments": [
                {"code": "DEPRECIATION", "amount": "20"},
                {"code": "GAIN_SALE", "amount": "-5"},
            ], "deltaOperatingNwc": "15"}


def cfo_config():
    return {"netIncomeBasis": "REPORTED_AFTER_TAX_NET_INCOME",
            "noncashAdjustment": "SIGNED_NONCASH_LINES",
            "workingCapitalSign": "INCREASE_OF_NWC_IS_OUTFLOW"}


def fcff_inputs():
    return {"asOf": "2026-12-31", "currency": "KZT", "sourceRevisionSha256": SOURCE_SHA,
            "ebit": "200", "taxRate": "0.25", "noncashOperatingCharges": "30",
            "cashCapex": "50", "deltaOperatingNwc": "20"}


def fcff_config():
    return {"taxPolicy": "EBIT_TIMES_EFFECTIVE_TAX_REFERENCE",
            "capitalExpenditurePolicy": "CASH_CAPEX_POSITIVE_OUTFLOW",
            "workingCapitalBasis": "INCREASE_NWC_IS_OUTFLOW"}


def equity_inputs():
    return {"valuationDate": "2026-12-31", "currency": "KZT",
            "sourceRevisionSha256": SOURCE_SHA, "enterpriseValue": "1000",
            "grossInterestDebt": "300", "unrestrictedCash": "50",
            "nonOperatingAssets": "20", "nonControllingInterest": "40",
            "preferredClaims": "10"}


def equity_config():
    return {"valuationDate": "2026-12-31",
            "netDebtDefinition": "GROSS_DEBT_LESS_UNRESTRICTED_CASH",
            "minorityInterests": "NCI_DEDUCT_FROM_ENTERPRISE"}


def escalation_inputs():
    return {"currency": "KZT", "baseCost": "1000", "annualRates": ["0.10", "0.05"],
            "rateSeriesRevisionSha256": SOURCE_SHA}


def escalation_config():
    return {"inflationIndexRev": SOURCE_SHA, "compoundingBasis": "DISCRETE_ANNUAL_END",
            "contingencyOverlap": "NO_CONTINGENCY_DOUBLE_COUNT"}


class HC04ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.semantics = ParameterSemantics(ROOT)

    def calc(self, model, variant, inputs, config):
        return self.engine.calculate(model, variant, inputs, config, reference_mode=True)

    def fails(self, code, f):
        with self.assertRaises(CalculationError) as context:
            f()
        self.assertEqual(context.exception.code, code)

    def test_indirect_cfo_signed_components(self):
        res = self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT", cfo_inputs(), cfo_config())
        out = res.output
        self.assertEqual(Decimal(out["noncashAdjustmentsTotal"]), Decimal(15))
        self.assertEqual(Decimal(out["workingCapitalCashEffect"]), Decimal(-15))
        self.assertEqual(Decimal(out["cashFlowFromOperations"]), Decimal(100))
        self.assertEqual(out["adjustmentCount"], 2)
        self.assertEqual(out["sourceRevisionSha256"], SOURCE_SHA)

    def test_cfo_reconciled_exact_value(self):
        config = {**cfo_config(), "directIndirectComparisonPolicy": "EXACT_EQUALITY"}
        inp = {**cfo_inputs(), "directCfo": "100"}
        result = self.calc("HC.CASH.05", "INDIRECT_CFO_RECONCILED", inp, config)
        self.assertEqual(Decimal(result.output["reconciliationDifference"]), Decimal(0))
        self.assertEqual(Decimal(result.output["directCfo"]), Decimal(100))
        self.fails("CFO_RECONCILIATION_MISMATCH", lambda:
                   self.calc("HC.CASH.05", "INDIRECT_CFO_RECONCILED",
                             {**inp, "directCfo": "100.01"}, config))

    def test_cfo_no_sign_double_count_and_negative_nwc_releases_cash(self):
        r = self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT",
                      {**cfo_inputs(), "deltaOperatingNwc": "-15"}, cfo_config())
        self.assertEqual(Decimal(r.output["cashFlowFromOperations"]), Decimal(130))

    def test_cfo_duplicate_adjustment_unknown_field_and_revision_guard(self):
        inp = cfo_inputs()
        self.fails("CFO_DUPLICATE_ADJUSTMENT_CODE", lambda:
                   self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT",
                             {**inp, "noncashAdjustments": inp["noncashAdjustments"] * 2},
                             cfo_config()))
        self.fails("CFO_ADJUSTMENT_SCHEMA", lambda:
                   self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT",
                             {**inp, "noncashAdjustments": [
                                 {"code": "DEP", "amount": "1", "sourceCurrency": "USD"}]},
                             cfo_config()))
        self.fails("REVISION_SHA256_REQUIRED", lambda:
                   self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT",
                             {**inp, "sourceRevisionSha256": "unsigned"},
                             cfo_config()))

    def test_fcff_ebit_tax_capex_nwc(self):
        result = self.calc("HC.DCF.05", "FCFF_UNLEVERED", fcff_inputs(), fcff_config())
        out = result.output
        self.assertEqual(Decimal(out["taxOnOperatingProfit"]), Decimal(50))
        self.assertEqual(Decimal(out["netOperatingProfitAfterTax"]), Decimal(150))
        self.assertEqual(Decimal(out["freeCashFlowToFirm"]), Decimal(110))
        self.assertEqual(Decimal(out["capitalExpenditureCashFlow"]), Decimal(-50))
        self.assertEqual(Decimal(out["workingCapitalCashFlow"]), Decimal(-20))

    def test_fcff_negative_working_capital_releases_cash(self):
        r = self.calc("HC.DCF.05", "FCFF_UNLEVERED",
                      {**fcff_inputs(), "deltaOperatingNwc": "-20"}, fcff_config())
        self.assertEqual(Decimal(r.output["freeCashFlowToFirm"]), Decimal(150))

    def test_fcff_loss_tax_and_ineligible_capex_fail_closed(self):
        self.fails("FCFF_NEGATIVE_EBIT_REQUIRES_TAX_POLICY", lambda:
                   self.calc("HC.DCF.05", "FCFF_UNLEVERED",
                             {**fcff_inputs(), "ebit": "-100"}, fcff_config()))
        self.fails("FCFF_TAX_RATE_OUT_OF_RANGE", lambda:
                   self.calc("HC.DCF.05", "FCFF_UNLEVERED",
                             {**fcff_inputs(), "taxRate": "1.1"}, fcff_config()))
        self.fails("NEGATIVE_MONETARY_MAGNITUDE", lambda:
                   self.calc("HC.DCF.05", "FCFF_UNLEVERED",
                             {**fcff_inputs(), "cashCapex": "-1"}, fcff_config()))

    def test_equity_bridge_independent_reconciliation(self):
        r = self.calc("HC.DCF.08", "EV_TO_EQUITY_BRIDGE",
                      equity_inputs(), equity_config())
        self.assertEqual(Decimal(r.output["netDebt"]), Decimal(250))
        self.assertEqual(Decimal(r.output["equityValue"]), Decimal(720))
        self.assertEqual(Decimal(r.output["bridgeReconciliation"]), Decimal(0))
        self.assertEqual(r.output["valuationDate"], "2026-12-31")

    def test_equity_bridge_negative_equity_allowed_no_artificial_floor(self):
        r = self.calc("HC.DCF.08", "EV_TO_EQUITY_BRIDGE",
                      {**equity_inputs(), "enterpriseValue": "100"},
                      equity_config())
        self.assertEqual(Decimal(r.output["equityValue"]), Decimal(-180))

    def test_equity_bridge_cutoff_and_cash_policies(self):
        self.fails("EQUITY_VALUATION_DATE_MISMATCH", lambda:
                   self.calc("HC.DCF.08", "EV_TO_EQUITY_BRIDGE",
                             {**equity_inputs(), "valuationDate": "2026-11-30"},
                             equity_config()))
        self.fails("NEGATIVE_MONETARY_MAGNITUDE", lambda:
                   self.calc("HC.DCF.08", "EV_TO_EQUITY_BRIDGE",
                             {**equity_inputs(), "unrestrictedCash": "-5"}, equity_config()))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
                   self.calc("HC.DCF.08", "EV_TO_EQUITY_BRIDGE",
                             equity_inputs(),
                             {**equity_config(),
                              "netDebtDefinition": "TOTAL_LIABILITIES_MINUS_ALL_CASH"}))

    def test_compound_annual_escalation(self):
        r = self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                      escalation_inputs(), escalation_config())
        self.assertEqual(Decimal(r.output["escalatedCost"]), Decimal("1155"))
        self.assertEqual(Decimal(r.output["incrementalCost"]), Decimal("155"))
        self.assertEqual(Decimal(r.output["years"][0]["escalatedCost"]), Decimal("1100"))
        self.assertEqual(len(r.output["years"]), 2)

    def test_compound_escalation_negative_valid_rate(self):
        r = self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                      {**escalation_inputs(), "annualRates": ["-0.2", "0.25"]},
                      escalation_config())
        self.assertEqual(Decimal(r.output["escalatedCost"]), Decimal("1000"))
        self.assertEqual(Decimal(r.output["incrementalCost"]), Decimal("0"))

    def test_compound_revision_sha_and_rate_domain_fail_closed(self):
        self.fails("ESCALATION_INDEX_REVISION_MISMATCH", lambda:
                   self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                             {**escalation_inputs(), "rateSeriesRevisionSha256": OTHER_SHA},
                             escalation_config()))
        self.fails("PINNED_REFERENCE_SHA_REQUIRED", lambda:
                   self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                             escalation_inputs(), {**escalation_config(), "inflationIndexRev": "source-A"}))
        self.fails("ESCALATION_RATE_OUT_OF_DOMAIN", lambda:
                   self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                             {**escalation_inputs(), "annualRates": ["-1"]},
                             escalation_config()))
        self.fails("ESCALATION_RATE_SERIES_REQUIRED", lambda:
                   self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                             {**escalation_inputs(), "annualRates": []},
                             escalation_config()))

    def test_all_new_variants_reject_unreviewed_options(self):
        self.fails("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
                   self.calc("HC.DCF.05", "FCFF_NORMALIZED", {}, {}))
        self.fails("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
                   self.calc("HC.DCF.08", "FCFE_EQUITY_DIRECT", {}, {}))
        self.fails("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
                   self.calc("HC.COST.05", "INDEX_LINKED_ESCALATION", {}, {}))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
                   self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT",
                             cfo_inputs(),
                             {**cfo_config(), "workingCapitalSign": "NO_POLICY"}))

    def test_source_and_output_immutability_and_hashes(self):
        inputs = cfo_inputs()
        before = [dict(row) for row in inputs["noncashAdjustments"]]
        result = self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT", inputs, cfo_config())
        self.assertEqual(before, inputs["noncashAdjustments"])
        with self.assertRaises(TypeError):
            result.output["cashFlowFromOperations"] = "0"
        more = self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT",
                         {**inputs, "netIncome": "101"}, cfo_config())
        self.assertNotEqual(more.inputs_sha256, result.inputs_sha256)
        self.assertNotEqual(more.output_sha256, result.output_sha256)

    def test_reference_only_runtime(self):
        with self.assertRaises(CalculationError) as err:
            self.engine.calculate("HC.COST.05", "COMPOUND_ESCALATION",
                                  escalation_inputs(), escalation_config())
        self.assertEqual(err.exception.code, "FINANCIAL_S2_REQUIRED")


if __name__ == "__main__":
    unittest.main()
