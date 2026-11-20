"""HC-R0.4 algebraic invariant matrices, independently of fixture constants."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import ReferenceEngine

ROOT = Path(__file__).resolve().parents[1]
SHA = "c" * 64


class R04AlgebraicInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def calc(self, model, variant, inputs, config):
        return self.engine.calculate(model, variant, inputs, config, reference_mode=True).output

    def test_cfo_matches_independent_signed_reconciliation(self):
        cfg = {"netIncomeBasis": "REPORTED_AFTER_TAX_NET_INCOME",
               "noncashAdjustment": "SIGNED_NONCASH_LINES",
               "workingCapitalSign": "INCREASE_OF_NWC_IS_OUTFLOW"}
        for ni, noncash, nwc in (
            ("0", "0", "0"), ("120", "40", "10"), ("-10", "20", "-5"),
            ("1000.25", "-30.75", "125.5"), ("123456789", "0.0001", "-8.03"),
        ):
            with self.subTest(ni=ni, noncash=noncash, nwc=nwc):
                inp = {"asOf": "2026-12-31", "currency": "KZT",
                       "sourceRevisionSha256": SHA,
                       "netIncome": ni,
                       "noncashAdjustments": [{"code": "A", "amount": noncash}],
                       "deltaOperatingNwc": nwc}
                r = self.calc("HC.CASH.05", "INDIRECT_CFO_ADJUSTMENT", inp, cfg)
                self.assertEqual(Decimal(r["cashFlowFromOperations"]),
                                 Decimal(ni) + Decimal(noncash) - Decimal(nwc))

    def test_fcff_derived_components_reconcile_without_financing(self):
        cfg = {"taxPolicy": "EBIT_TIMES_EFFECTIVE_TAX_REFERENCE",
               "capitalExpenditurePolicy": "CASH_CAPEX_POSITIVE_OUTFLOW",
               "workingCapitalBasis": "INCREASE_NWC_IS_OUTFLOW"}
        for ebit, tax, da, capex, nwc in (
            ("0", "0", "0", "0", "0"),
            ("200", "0.25", "30", "50", "20"),
            ("100.5", "0.3", "0.5", "40", "-10"),
            ("900", "1", "30", "35", "0"),
        ):
            with self.subTest(ebit=ebit, tax=tax):
                inp = {"asOf": "2026-12-31", "currency": "KZT",
                       "sourceRevisionSha256": SHA, "ebit": ebit,
                       "taxRate": tax, "noncashOperatingCharges": da,
                       "cashCapex": capex, "deltaOperatingNwc": nwc}
                result = self.calc("HC.DCF.05", "FCFF_UNLEVERED", inp, cfg)
                expected = (Decimal(ebit) * (Decimal(1) - Decimal(tax))
                            + Decimal(da) - Decimal(capex) - Decimal(nwc))
                self.assertEqual(Decimal(result["freeCashFlowToFirm"]), expected)

    def test_ev_equity_bidirectional_reconciliation(self):
        cfg = {"valuationDate": "2026-12-31",
               "netDebtDefinition": "GROSS_DEBT_LESS_UNRESTRICTED_CASH",
               "minorityInterests": "NCI_DEDUCT_FROM_ENTERPRISE"}
        for ev, debt, cash, other, nci, pref in (
            ("1000", "300", "50", "20", "40", "10"),
            ("100", "300", "50", "20", "40", "10"),
            ("0", "0", "0", "0", "0", "0"),
            ("100.50", "10.25", "5.10", "1.25", "2.05", "1.75"),
        ):
            with self.subTest(ev=ev, debt=debt):
                inp = {"valuationDate": "2026-12-31", "currency": "KZT",
                       "sourceRevisionSha256": SHA,
                       "enterpriseValue": ev, "grossInterestDebt": debt,
                       "unrestrictedCash": cash, "nonOperatingAssets": other,
                       "nonControllingInterest": nci, "preferredClaims": pref}
                r = self.calc("HC.DCF.08", "EV_TO_EQUITY_BRIDGE", inp, cfg)
                self.assertEqual(Decimal(r["equityValue"]),
                                 Decimal(ev) - Decimal(debt) + Decimal(cash)
                                 + Decimal(other) - Decimal(nci) - Decimal(pref))
                self.assertEqual(Decimal(r["bridgeReconciliation"]), Decimal(0))

    def test_escalation_exact_product_and_permutation_invariance(self):
        for rates in (("0.1", "0.05"), ("0.2", "-0.1", "0.1"),
                      ("0", "0", "0"), ("-0.25", "0.25", "0.25", "-0.25")):
            with self.subTest(rates=rates):
                inp = {"baseCost": "1234.50", "currency": "KZT",
                       "rateSeriesRevisionSha256": SHA, "annualRates": list(rates)}
                cfg = {"inflationIndexRev": SHA,
                       "compoundingBasis": "DISCRETE_ANNUAL_END",
                       "contingencyOverlap": "NO_CONTINGENCY_DOUBLE_COUNT"}
                r = self.calc("HC.COST.05", "COMPOUND_ESCALATION", inp, cfg)
                exact = Decimal("1234.50")
                for rate in rates:
                    exact *= (Decimal(1) + Decimal(rate))
                self.assertEqual(Decimal(r["escalatedCost"]), exact)
                shuffled = self.calc("HC.COST.05", "COMPOUND_ESCALATION",
                                     {**inp, "annualRates": list(reversed(rates))}, cfg)
                self.assertEqual(Decimal(shuffled["escalatedCost"]), exact)


if __name__ == "__main__":
    unittest.main()
