"""HC-R0.5: independently calculated direct CFO feeds indirect CFO in typed DAG."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.graphs import CalculationJob, InputBinding, InMemoryCalculationPlan
from test_fengine_hc_r05_cashflow import ledger, configuration

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTING_SHA = "d" * 64


def direct_job(*, currency=None):
    data = ledger()
    if currency is not None:
        # Preserve the explicit source snapshot SHA for the modified ledger.
        from fengine_hc.r05_cashflow import posted_source_sha256
        data["currency"] = currency
        data["sourceRevisionSha256"] = posted_source_sha256({
            key: data[key] for key in (
                "periodStart", "periodEnd", "currency", "openingCash", "closingCash", "postings"
            )
        })
    return CalculationJob("direct", "HC.CASH.04", "DIRECT_POSTED_CFO",
                          data, configuration())


def indirect_job(*, currency="KZT", asof="2026-12-31", start="2026-12-01",
                 net_income="100", variant="INDIRECT_CFO_RECONCILED",
                 source_field="cashFlowFromOperations"):
    data = {
        "asOf": asof,
        "periodStart": start,
        "currency": currency,
        "sourceRevisionSha256": ACCOUNTING_SHA,
        "netIncome": net_income,
        "noncashAdjustments": [{"code": "DEPRECIATION", "amount": "40"}],
        "deltaOperatingNwc": "20",
    }
    config = {
        "netIncomeBasis": "REPORTED_AFTER_TAX_NET_INCOME",
        "noncashAdjustment": "SIGNED_NONCASH_LINES",
        "workingCapitalSign": "INCREASE_OF_NWC_IS_OUTFLOW",
        "directIndirectComparisonPolicy": "EXACT_EQUALITY",
    }
    if variant == "INDIRECT_CFO_ADJUSTMENT":
        config.pop("directIndirectComparisonPolicy")
    return CalculationJob("indirect", "HC.CASH.05", variant, data, config,
                          (InputBinding("direct", source_field, "directCfo"),))


class DirectIndirectGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)

    def expect_error(self, code, fun):
        with self.assertRaises(CalculationError) as result:
            fun()
        self.assertEqual(result.exception.code, code)

    def test_direct_indirect_cfo_reconciles_end_to_end_without_supplied_direct_number(self):
        plan = InMemoryCalculationPlan(self.engine, [indirect_job(), direct_job()])
        self.assertEqual(plan.order, ("direct", "indirect"))
        self.assertEqual(len(plan.plan_sha256), 64)
        results = plan.execute(reference_mode=True)
        direct = results["direct"].output
        indirect = results["indirect"].output
        self.assertEqual(Decimal(direct["cashFlowFromOperations"]), Decimal(120))
        self.assertEqual(Decimal(indirect["cashFlowFromOperations"]), Decimal(120))
        self.assertEqual(Decimal(indirect["directCfo"]), Decimal(120))
        self.assertEqual(Decimal(indirect["reconciliationDifference"]), Decimal(0))
        self.assertEqual(results["indirect"].execution_class, "PYTHON_REFERENCE_NOT_S2")
        with self.assertRaises(TypeError):
            results["direct"] = "tamper"
        self.assertNotIn("postings", direct)
        self.assertNotIn("noncashAdjustments", indirect)

    def test_indirect_drift_fails_with_actual_direct_computed_cfo(self):
        plan = InMemoryCalculationPlan(self.engine, [
            direct_job(), indirect_job(net_income="101")])
        self.expect_error("CFO_RECONCILIATION_MISMATCH", lambda:
                          plan.execute(reference_mode=True))

    def test_currency_mismatch_rejected_before_execution(self):
        self.expect_error("MODEL_BINDING_CURRENCY_MISMATCH", lambda:
                          InMemoryCalculationPlan(self.engine, [
                              direct_job(), indirect_job(currency="USD")]))

    def test_period_mismatch_rejected_before_execution(self):
        self.expect_error("MODEL_BINDING_PERIOD_MISMATCH", lambda:
                          InMemoryCalculationPlan(self.engine, [
                              direct_job(), indirect_job(asof="2026-11-30")]))
        self.expect_error("MODEL_BINDING_PERIOD_MISMATCH", lambda:
                          InMemoryCalculationPlan(self.engine, [
                              direct_job(), indirect_job(start="2026-11-01")]))

    def test_unreviewed_field_edge_rejected(self):
        self.expect_error("MODEL_BINDING_NOT_REVIEWED", lambda:
                          InMemoryCalculationPlan(self.engine, [
                              direct_job(), indirect_job(source_field="operatingReceipts")]))

    def test_unreconciled_method_cannot_receive_direct_cfo_binding(self):
        self.expect_error("MODEL_BINDING_VARIANT_MISMATCH", lambda:
                          InMemoryCalculationPlan(self.engine, [
                              direct_job(), indirect_job(variant="INDIRECT_CFO_ADJUSTMENT")]))

    def test_plan_hash_changes_when_source_postings_change(self):
        from fengine_hc.r05_cashflow import posted_source_sha256
        original = direct_job()
        amended = dict(original.inputs)
        new_postings = [dict(x) for x in amended["postings"]]
        new_postings[0]["amount"] = "210"
        amended["postings"] = new_postings
        amended["closingCash"] = "1150"
        amended["sourceRevisionSha256"] = posted_source_sha256({
            key: amended[key] for key in (
                "periodStart", "periodEnd", "currency", "openingCash", "closingCash", "postings"
            )
        })
        old_plan = InMemoryCalculationPlan(self.engine, [original, indirect_job()])
        new_plan = InMemoryCalculationPlan(self.engine, [
            CalculationJob("direct", "HC.CASH.04", "DIRECT_POSTED_CFO", amended,
                           configuration()), indirect_job()])
        self.assertNotEqual(old_plan.plan_sha256, new_plan.plan_sha256)
        self.expect_error("CFO_RECONCILIATION_MISMATCH", lambda:
                          new_plan.execute(reference_mode=True))

    def test_normal_reference_admission_remains_closed(self):
        plan = InMemoryCalculationPlan(self.engine, [direct_job(), indirect_job()])
        self.expect_error("FINANCIAL_S2_REQUIRED", lambda: plan.execute())


if __name__ == "__main__":
    unittest.main()
