"""HC-R0.6 FCFE: two independently derived Decimal methods and negative gates."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.r06_fcfe import (
    POLICY, BASIS, fcfe_source_sha256, cost_of_equity_rate_sha256,
    reconcile_fcfe_methods,
)

ROOT = Path(__file__).resolve().parents[1]


def fcfe_fixture(variant="FCFE_LEVERED", *, cfo="110", rate="0.10", income="100",
                 noncash="30", nwc="20", capex="50", draw="40", repay="15",
                 currency="KZT", period=1):
    rate_sha = cost_of_equity_rate_sha256(rate)
    config = {**POLICY, "equityCashflowBasis": BASIS[variant], "costOfEquityRef": rate_sha}
    inputs = {
        "asOf": "2026-12-31", "currency": currency,
        "costOfEquityRate": rate, "costOfEquityRevisionSha256": rate_sha,
        "periodIndex": period, "cashCapex": capex,
        "grossDebtDrawdowns": draw, "principalRepayments": repay,
    }
    if variant == "FCFE_LEVERED":
        inputs["operatingCashFlowAfterInterest"] = cfo
    else:
        inputs.update({"netIncome": income, "noncashOperatingCharges": noncash,
                       "deltaOperatingNwc": nwc})
    inputs["sourceRevisionSha256"] = fcfe_source_sha256(inputs, variant)
    return inputs, config


def amend_source(inputs, variant, **values):
    new = {**inputs, **values}
    new.pop("sourceRevisionSha256")
    new["sourceRevisionSha256"] = fcfe_source_sha256(new, variant)
    return new


class R06FcfeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def calc(self, variant, inp=None, config=None):
        if inp is None:
            inp, cfg = fcfe_fixture(variant)
        else:
            cfg = fcfe_fixture(variant)[1]
        return self.engine.calculate(
            "HC.DCF.06", variant, inp, cfg if config is None else config,
            reference_mode=True
        )

    def err(self, code, fun):
        with self.assertRaises(CalculationError) as raised:
            fun()
        self.assertEqual(raised.exception.code, code)

    def test_levered_direct_cfo_after_interest_and_no_double_count(self):
        result = self.calc("FCFE_LEVERED")
        out = result.output
        self.assertEqual(Decimal(out["operatingCashFlowAfterInterest"]), 110)
        self.assertEqual(Decimal(out["capitalExpenditureCashEffect"]), -50)
        self.assertEqual(Decimal(out["netBorrowing"]), 25)
        self.assertEqual(Decimal(out["freeCashFlowToEquity"]), 85)
        self.assertLess(abs(Decimal(out["presentValueOfFcfe"]) - Decimal(85) / Decimal("1.1")),
                        Decimal("1e-32"))
        self.assertEqual(out["discountPolicy"], "NOMINAL_ANNUAL_PERIOD_END_AT_KE_NOT_WACC")

    def test_normalized_independent_income_bridge_matches_levered(self):
        lev = self.calc("FCFE_LEVERED").output
        norm = self.calc("FCFE_NORMALIZED").output
        self.assertEqual(Decimal(norm["operatingCashFlowAfterInterest"]), 110)
        self.assertEqual(Decimal(norm["freeCashFlowToEquity"]), 85)
        matching = reconcile_fcfe_methods(lev, norm)
        self.assertEqual(matching["status"], "MATCHED_REFERENCE_NOT_S2")
        self.assertEqual(matching["difference"], "0")

    def test_cross_method_mismatch_is_rejected(self):
        lev = self.calc("FCFE_LEVERED").output
        inp, cfg = fcfe_fixture("FCFE_NORMALIZED", income="101")
        normalized = self.calc("FCFE_NORMALIZED", inp, cfg).output
        self.err("FCFE_RECONCILIATION_MISMATCH", lambda:
                 reconcile_fcfe_methods(lev, normalized))

    def test_cross_method_currency_rate_and_period_mismatch_fail(self):
        lev = self.calc("FCFE_LEVERED").output
        for change in ({"currency": "USD"}, {"rate": "0.12"}, {"period": 2}):
            with self.subTest(change=change):
                inp, cfg = fcfe_fixture("FCFE_NORMALIZED", **change)
                norm = self.calc("FCFE_NORMALIZED", inp, cfg).output
                self.err("FCFE_RECONCILIATION_CONTEXT_MISMATCH", lambda:
                         reconcile_fcfe_methods(lev, norm))

    def test_source_input_change_with_old_revision_rejected(self):
        inp, cfg = fcfe_fixture()
        inp["cashCapex"] = "51"
        self.err("FCFE_SOURCE_DIGEST_MISMATCH", lambda:
                 self.calc("FCFE_LEVERED", inp, cfg))

    def test_rate_revision_must_match_config_and_actual_rate(self):
        inp, cfg = fcfe_fixture()
        self.err("FCFE_RATE_REVISION_MISMATCH", lambda:
                 self.calc("FCFE_LEVERED", inp, {**cfg, "costOfEquityRef": "b"*64}))
        modified = amend_source(inp, "FCFE_LEVERED", costOfEquityRate="0.11")
        self.err("FCFE_RATE_DIGEST_MISMATCH", lambda:
                 self.calc("FCFE_LEVERED", modified, cfg))

    def test_rate_bounds_and_discount_year_count_fail_closed(self):
        self.err("FCFE_COST_OF_EQUITY_OUT_OF_REFERENCE_DOMAIN", lambda:
                 fcfe_fixture(rate="-0.01"))
        self.err("FCFE_COST_OF_EQUITY_OUT_OF_REFERENCE_DOMAIN", lambda:
                 fcfe_fixture(rate="1.01"))
        inp, cfg = fcfe_fixture(period=101)
        self.err("FCFE_PERIOD_INDEX_TOO_LARGE", lambda:
                 self.calc("FCFE_LEVERED", inp, cfg))
        inp, cfg = fcfe_fixture(period=0)
        self.err("INVALID_INTEGER", lambda: self.calc("FCFE_LEVERED", inp, cfg))

    def test_negative_equity_cashflow_is_not_hidden_by_zero_floor(self):
        inp, cfg = fcfe_fixture("FCFE_NORMALIZED", income="-10", noncash="0",
                                nwc="0", capex="50", draw="0", repay="0")
        r = self.calc("FCFE_NORMALIZED", inp, cfg)
        self.assertEqual(Decimal(r.output["freeCashFlowToEquity"]), -60)
        self.assertLess(Decimal(r.output["presentValueOfFcfe"]), 0)

    def test_negative_capex_or_repayment_magnitude_refused(self):
        for change in ({"capex": "-5"}, {"draw": "-1"}, {"repay": "-1"}):
            with self.subTest(change=change):
                inp, cfg = fcfe_fixture(**change)
                self.err("FCFE_NONNEGATIVE_MAGNITUDE_REQUIRED", lambda:
                         self.calc("FCFE_LEVERED", inp, cfg))

    def test_variant_specific_cashflow_eligibility_and_unknown_input_fail_closed(self):
        inp, cfg = fcfe_fixture("FCFE_LEVERED")
        self.err("FCFE_INPUT_SCHEMA", lambda:
                 self.calc("FCFE_LEVERED", {**inp, "interestPaid": "20"}, cfg))
        self.err("ENUM_OUT_OF_RANGE", lambda:
                 self.calc("FCFE_LEVERED", inp, {**cfg,
                                               "equityCashflowBasis": BASIS["FCFE_NORMALIZED"]}))
        self.err("UNCONSUMED_CONFIGURATION", lambda:
                 self.calc("FCFE_LEVERED", inp, {**cfg, "hiddenTaxPolicy": "ANY"}))

    def test_borrowing_and_rate_mutations_change_output_receipt(self):
        inp, cfg = fcfe_fixture()
        a = self.calc("FCFE_LEVERED", inp, cfg)
        amended = amend_source(inp, "FCFE_LEVERED", principalRepayments="16")
        b = self.calc("FCFE_LEVERED", amended, cfg)
        self.assertEqual(Decimal(a.output["freeCashFlowToEquity"]) -
                         Decimal(b.output["freeCashFlowToEquity"]), 1)
        self.assertNotEqual(a.output_sha256, b.output_sha256)
        with self.assertRaises(TypeError):
            a.output["freeCashFlowToEquity"] = "100000"

    def test_financial_s2_closed(self):
        inp, cfg = fcfe_fixture()
        self.err("FINANCIAL_S2_REQUIRED", lambda:
                 self.engine.calculate("HC.DCF.06", "FCFE_LEVERED", inp, cfg))


if __name__ == "__main__":
    unittest.main()
