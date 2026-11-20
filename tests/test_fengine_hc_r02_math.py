"""HC-R0.2B independent mathematical goldens, out-of-domain and finance fail-closed."""
import unittest
from pathlib import Path
from decimal import Decimal

from fengine_hc import CalculationError, ReferenceEngine
from fengine_hc.r02_math import (
    all_periodic_irr, dated_eir_single_sign_change,
    empirical_var, empirical_es, expected_loss
)

ROOT = Path(__file__).resolve().parents[1]


class R02MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def calc(self, m, v, inputs, config):
        return self.engine.calculate(m, v, inputs, config, reference_mode=True)

    def err(self, code, fun):
        with self.assertRaises(CalculationError) as e:
            fun()
        self.assertEqual(e.exception.code, code)

    def test_irr_two_real_roots_10_and_20_percent(self):
        cfg = {"rootDomain": {"minRate": "-0.9", "maxRate": "5"},
               "rootCompletenessPolicy": "CERTIFIED_ALL"}
        a = self.calc("HC.DCF.03", "ALL_REAL_IRR_ROOTS",
                      {"cashflows": ["-100", "230", "-132"]}, cfg)
        self.assertEqual(a.output["rootCount"], 2)
        for x, y in zip(a.output["roots"], [Decimal("0.10"), Decimal("0.20")]):
            self.assertLess(abs(Decimal(x) - y), Decimal("1e-20"))
        self.assertEqual(a.output["completeness"], "FINITE_INTERVAL_CERTIFIED_REFERENCE")
        self.err("MULTIPLE_IRR_ROOTS", lambda:
                 self.calc("HC.DCF.03", "SINGLE_IF_UNAMBIGUOUS",
                           {"cashflows": ["-100", "230", "-132"]}, cfg))

    def test_tangent_root_and_unique_irr(self):
        x = all_periodic_irr(["-100", "200", "-100"], "-0.9", "5")
        self.assertEqual(len(x), 1)
        self.assertLess(abs(x[0]), Decimal("1e-22"))
        simple = all_periodic_irr(["-100", "110"], "-0.9", "5")
        self.assertEqual(len(simple), 1)
        self.assertLess(abs(simple[0] - Decimal("0.1")), Decimal("1e-20"))

    def test_no_irr_root_and_invalid_domain(self):
        self.err("IRR_REQUIRES_OPPOSING_SIGNS", lambda:
                 all_periodic_irr(["1", "2"], "-0.9", "5"))
        self.err("RATE_OUT_OF_DOMAIN", lambda:
                 all_periodic_irr(["-100", "110"], "-1", "5"))
        self.err("NO_IRR_ROOT_IN_DOMAIN", lambda:
                 self.calc("HC.DCF.03", "ALL_REAL_IRR_ROOTS",
                           {"cashflows": ["-100", "110"]},
                           {"rootDomain": {"minRate": "0.2", "maxRate": "5"},
                            "rootCompletenessPolicy": "CERTIFIED_ALL"}))

    def test_dated_eir_reference_one_year(self):
        cashflows = [{"date": "2026-01-01", "amount": "-100"},
                     {"date": "2027-01-01", "amount": "110"}]
        r = self.calc("HC.LOAN.03", "EIR_ORIGINAL", {"cashflows": cashflows},
                      {"discountOrigin": "2026-01-01",
                       "rootCompletenessPolicy": "CERTIFIED_ALL"})
        self.assertLess(abs(Decimal(r.output["effectiveRate"]) - Decimal("0.1")),
                        Decimal("1e-20"))
        self.assertEqual(r.output["classification"],
                         "CASHFLOW_ROOT_REFERENCE_NOT_IFRS_EIR")

    def test_eir_nonconventional_and_revised_blocked(self):
        rows = [{"date": "2026-01-01", "amount": "-100"},
                {"date": "2027-01-01", "amount": "120"},
                {"date": "2028-01-01", "amount": "-30"}]
        self.err("EIR_NONCONVENTIONAL_CASHFLOWS", lambda:
                 dated_eir_single_sign_change(rows, "2026-01-01"))
        self.err("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
                 self.calc("HC.LOAN.03", "EIR_REVISED_MODIFICATION", {}, {}))

    def test_var_nearest_rank_and_es_fractional_tail(self):
        loss = ["1", "2", "3", "4", "5"]
        v = self.calc("HC.RISK.02", "EMPIRICAL_LEFT_QUANTILE", {"losses": loss},
                      {"alpha": "0.8", "lossSignPolicy": "POSITIVE_LOSS",
                       "quantileDefinition": "NEAREST_RANK"})
        self.assertEqual(Decimal(v.output["valueAtRisk"]), Decimal(4))
        e = self.calc("HC.RISK.03", "QUANTILE_INTEGRAL_ES", {"losses": loss},
                      {"confidenceAlpha": "0.7",
                       "esTailMassRule": "QUANTILE_INTEGRAL_FRACTIONAL_ATOM"})
        self.assertLess(abs(Decimal(e.output["expectedShortfall"]) - Decimal(14)/3),
                        Decimal("1e-25"))
        self.assertEqual(empirical_es(["3", "3", "3", "3"], "0.95"), Decimal(3))

    def test_var_confidence_and_loss_sign_rejected(self):
        self.err("INVALID_CONFIDENCE", lambda: empirical_var(["0", "1"], "1"))
        self.err("NEGATIVE_LOSS_VALUE", lambda: empirical_es(["-1", "2"], "0.8"))
        self.err("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
                 self.calc("HC.RISK.02", "PARAMETRIC_NORMAL_VaR", {}, {}))

    def _ev(self, default, settlement, pd, lgd="0.5", exposure="100"):
        return {"defaultDate": default, "lossDate": settlement,
                "pd": pd, "lgd": lgd, "exposure": exposure}

    def test_12month_ecl_default_window_not_recovery_window(self):
        events = [self._ev("2026-06-01", "2028-01-01", "0.1"),
                  self._ev("2026-12-01", "2028-12-01", "0.2")]
        r = self.calc("HC.ECL.02", "FIRST_12_MONTH_DEFAULT_EVENTS",
                      {"events": events, "asOf": "2026-01-01", "annualEir": "0"},
                      {"defaultEventWindow": "FIRST_12_MONTHS"})
        self.assertEqual(Decimal(r.output["expectedCreditLoss"]), Decimal("15"))
        self.assertEqual(len(r.output["events"]), 2)
        self.err("DEFAULT_OUTSIDE_12M_WINDOW", lambda:
                 expected_loss([self._ev("2027-02-01", "2027-04-01", "0.1")],
                               "2026-01-01", "0", lifetime=False))

    def test_lifetime_conditional_pd_survival_recursion(self):
        events = [self._ev("2027-01-01", "2027-01-01", "0.1"),
                  self._ev("2028-01-01", "2028-01-01", "0.2")]
        r = self.calc("HC.ECL.03", "LIFETIME_TERM_PD",
                      {"events": events, "asOf": "2026-01-01", "annualEir": "0"},
                      {"hazardConditionality": "CONDITIONAL_PD"})
        self.assertEqual(Decimal(r.output["expectedCreditLoss"]), Decimal("14"))
        self.assertEqual(Decimal(r.output["survivalProbability"]), Decimal("0.72"))
        self.assertEqual(Decimal(r.output["events"][1]["marginalPd"]), Decimal("0.18"))

    def test_pd_and_timing_invalid(self):
        self.err("ECL_INPUT_OUT_OF_RANGE", lambda:
                 expected_loss([self._ev("2026-03-01", "2026-04-01", "1.2")],
                               "2026-01-01", "0", lifetime=False))
        self.err("MARGINAL_PD_SUM_EXCEEDS_ONE", lambda:
                 expected_loss([self._ev("2026-03-01", "2026-04-01", "0.7"),
                                self._ev("2026-05-01", "2026-06-01", "0.7")],
                               "2026-01-01", "0", lifetime=False))
        self.err("ECL_DATE_ORDER", lambda:
                 expected_loss([self._ev("2025-01-01", "2026-01-01", "0.1")],
                               "2026-01-01", "0", lifetime=True))

    def test_unsupported_finance_admission_fails(self):
        self.err("FINANCIAL_S2_REQUIRED", lambda:
                 self.engine.calculate("HC.DCF.03", "ALL_REAL_IRR_ROOTS", {}, {}))


if __name__ == "__main__":
    unittest.main()
