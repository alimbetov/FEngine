"""HC-R0.5 posted direct CFO: real cross-ledger arithmetic and negative controls."""
from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.r05_cashflow import (
    RECONCILIATION_SHA256, classification_rules_sha256,
    override_revision_sha256, posted_source_sha256,
)
from fengine_hc.semantics import ParameterSemantics

ROOT = Path(__file__).resolve().parents[1]
CLASS_RULES = [
    {"code": "CLIENT_RECEIPT", "cashflowClass": "OPERATING"},
    {"code": "SUPPLIER_PAYMENT", "cashflowClass": "OPERATING"},
    {"code": "CAPEX_PAYMENT", "cashflowClass": "INVESTING"},
    {"code": "LOAN_DRAW", "cashflowClass": "FINANCING"},
    {"code": "TRANSFER_INTERNAL", "cashflowClass": "INTERNAL_TRANSFER"},
]


def posting(posting_id, direction, amount, category, transfer_id=None, date="2026-12-20"):
    return {"postingId": posting_id, "postingDate": date, "amount": amount,
            "direction": direction, "classificationCode": category,
            "transferId": transfer_id}


def ledger(postings=None, *, closing="1140", classification=None):
    rows = postings if postings is not None else [
        posting("P1", "IN", "200", "CLIENT_RECEIPT"),
        posting("P2", "OUT", "80", "SUPPLIER_PAYMENT"),
        posting("P3", "OUT", "30", "CAPEX_PAYMENT"),
        posting("P4", "IN", "50", "LOAN_DRAW"),
        posting("P5", "OUT", "40", "TRANSFER_INTERNAL", "TRANSFER-X"),
        posting("P6", "IN", "40", "TRANSFER_INTERNAL", "TRANSFER-X"),
    ]
    snapshot = {"periodStart": "2026-12-01", "periodEnd": "2026-12-31",
                "currency": "KZT", "openingCash": "1000",
                "closingCash": closing, "postings": rows}
    return {
        **snapshot, "sourceRevisionSha256": posted_source_sha256(snapshot),
        "classificationRules": [dict(rule) for rule in (CLASS_RULES if classification is None else classification)],
    }


def configuration(class_rules=None):
    return {
        "cashClassification": classification_rules_sha256(
            CLASS_RULES if class_rules is None else class_rules),
        "reconciliationRule": RECONCILIATION_SHA256,
        "periodCutoff": "2026-12-31",
        "transferExclusionRule": "BALANCED_INTERNAL_TRANSFER_PAIRS",
        "valueDateVsPostingDate": "POSTING_DATE_ONLY",
    }


def override_ledger(postings=None, replacements=None):
    data = ledger(postings=postings)
    changes = replacements or [
        {"postingId": "P3", "newClassificationCode": "SUPPLIER_PAYMENT",
         "reasonCode": "DOCUMENTED_RECLASSIFICATION"},
    ]
    data["reclassificationOverrides"] = changes
    data["reclassificationRevisionSha256"] = override_revision_sha256(
        data["sourceRevisionSha256"], changes
    )
    return data


class DirectCFOReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.sem = ParameterSemantics(ROOT)

    def run_model(self, inputs=None, config=None, variant="DIRECT_POSTED_CFO"):
        return self.engine.calculate(
            "HC.CASH.04", variant,
            ledger() if inputs is None else inputs,
            configuration() if config is None else config,
            reference_mode=True
        )

    def fails(self, code, fun):
        with self.assertRaises(CalculationError) as captured:
            fun()
        self.assertEqual(captured.exception.code, code)

    def test_posted_direct_cfo_independent_goldens_and_cash_balances(self):
        out = self.run_model().output
        self.assertEqual(Decimal(out["operatingReceipts"]), 200)
        self.assertEqual(Decimal(out["operatingPayments"]), 80)
        self.assertEqual(Decimal(out["cashFlowFromOperations"]), 120)
        self.assertEqual(Decimal(out["netInvestingCashFlow"]), -30)
        self.assertEqual(Decimal(out["netFinancingCashFlow"]), 50)
        self.assertEqual(Decimal(out["netAllCashFlow"]), 140)
        self.assertEqual(Decimal(out["closingCash"]), 1140)
        self.assertEqual(out["excludedTransferPostingCount"], 2)
        self.assertEqual(out["operatingPostingCount"], 2)
        self.assertEqual(out["postingCount"], 6)
        self.assertEqual(out["reclassifiedPostingCount"], 0)
        self.assertEqual(out["sourceRevisionSha256"], ledger()["sourceRevisionSha256"])

    def test_classification_revision_stable_for_different_rule_order(self):
        self.assertEqual(classification_rules_sha256(CLASS_RULES),
                         classification_rules_sha256(list(reversed(CLASS_RULES))))
        inp = ledger(classification=list(reversed(CLASS_RULES)))
        self.assertEqual(Decimal(self.run_model(inp).output["cashFlowFromOperations"]), 120)

    def test_reclassified_direct_cfo_has_explicit_revision(self):
        out = self.run_model(override_ledger(), variant="DIRECT_RECLASSIFIED_CFO").output
        self.assertEqual(Decimal(out["cashFlowFromOperations"]), 90)
        self.assertEqual(Decimal(out["netInvestingCashFlow"]), 0)
        self.assertEqual(Decimal(out["netFinancingCashFlow"]), 50)
        self.assertEqual(Decimal(out["netAllCashFlow"]), 140)
        self.assertEqual(out["reclassifiedPostingCount"], 1)
        self.assertEqual(out["excludedTransferPostingCount"], 2)

    def test_posted_variant_does_not_accept_silent_overrides(self):
        self.fails("DIRECT_CFO_INPUT_SCHEMA", lambda:
                   self.run_model(override_ledger()))

    def test_missing_and_duplicate_posting_rejected(self):
        inp = ledger()
        self.fails("DIRECT_CFO_DUPLICATE_POSTING_ID", lambda:
                   self.run_model(ledger(postings=inp["postings"] + [inp["postings"][0]])))
        self.fails("DIRECT_CFO_POSTINGS_REQUIRED", lambda:
                   self.run_model(ledger(postings=[])))

    def test_changed_posting_without_changed_sha_is_blocked(self):
        inp = ledger()
        inp["postings"][0]["amount"] = "201"
        self.fails("DIRECT_CFO_SOURCE_DIGEST_MISMATCH", lambda: self.run_model(inp))

    def test_changed_classification_without_new_sha_is_blocked(self):
        inp = ledger()
        inp["classificationRules"][0]["cashflowClass"] = "INVESTING"
        self.fails("DIRECT_CFO_CLASSIFICATION_SHA_MISMATCH", lambda: self.run_model(inp))

    def test_missing_approval_of_classification_code_fails(self):
        rows = ledger()["postings"]
        rows[0] = {**rows[0], "classificationCode": "UNKNOWN_PAYMENT"}
        self.fails("DIRECT_CFO_UNCLASSIFIED_POSTING", lambda:
                   self.run_model(ledger(postings=rows)))

    def test_cash_reconciliation_uses_all_classes(self):
        self.fails("DIRECT_CFO_CASH_BALANCE_MISMATCH", lambda:
                   self.run_model(ledger(closing="1141")))
        self.fails("DIRECT_CFO_RECON_REVISION_MISMATCH", lambda:
                   self.run_model(config={**configuration(), "reconciliationRule": "b" * 64}))

    def test_transfer_must_have_both_balanced_legs_in_same_period(self):
        rows = ledger()["postings"]
        self.fails("DIRECT_CFO_UNBALANCED_INTERNAL_TRANSFER", lambda:
                   self.run_model(ledger(postings=rows[:-1])))
        altered = [dict(row) for row in rows]
        altered[-1]["amount"] = "30"
        self.fails("DIRECT_CFO_UNBALANCED_INTERNAL_TRANSFER", lambda:
                   self.run_model(ledger(postings=altered)))
        incomplete = [dict(row) for row in rows]
        incomplete[-1]["transferId"] = None
        self.fails("DIRECT_CFO_TRANSFER_ID_REQUIRED", lambda:
                   self.run_model(ledger(postings=incomplete)))

    def test_non_internal_operation_cannot_claim_transfer(self):
        rows = ledger()["postings"]
        rows[0]["transferId"] = "TRANSFER-X"
        self.fails("DIRECT_CFO_NONTRANSFER_WITH_TRANSFER_ID", lambda:
                   self.run_model(ledger(postings=rows)))

    def test_outside_period_and_noncanonical_date_rejected(self):
        rows = ledger()["postings"]
        rows[0]["postingDate"] = "2027-01-01"
        self.fails("DIRECT_CFO_POSTING_OUTSIDE_PERIOD", lambda:
                   self.run_model(ledger(postings=rows)))
        rows = ledger()["postings"]
        rows[0]["postingDate"] = "20261220"
        self.fails("CASH_POSTING_DATE_NOT_CANONICAL", lambda:
                   self.run_model(ledger(postings=rows)))
        self.fails("DIRECT_CFO_PERIOD_CUTOFF_MISMATCH", lambda:
                   self.run_model(config={**configuration(), "periodCutoff": "2026-12-30"}))

    def test_amount_direction_and_fields_are_strict(self):
        rows = ledger()["postings"]
        rows[0]["amount"] = "0"
        self.fails("DIRECT_CFO_POSTING_AMOUNT_MUST_BE_POSITIVE", lambda:
                   self.run_model(ledger(postings=rows)))
        rows = ledger()["postings"]
        rows[0]["direction"] = "CREDIT"
        self.fails("DIRECT_CFO_DIRECTION_INVALID", lambda:
                   self.run_model(ledger(postings=rows)))
        rows = ledger()["postings"]
        rows[0]["owner"] = "CLIENT-A"
        self.fails("DIRECT_CFO_POSTING_SCHEMA", lambda:
                   self.run_model(ledger(postings=rows)))

    def test_no_binary_float_or_foreign_currency(self):
        rows = ledger()["postings"]
        rows[0]["amount"] = 200.0
        self.fails("BINARY_FLOAT_FORBIDDEN", lambda: self.run_model(ledger(postings=rows)))
        inp = ledger()
        inp["currency"] = "kzt"
        self.fails("DIRECT_CFO_SOURCE_DIGEST_MISMATCH", lambda: self.run_model(inp))
        self.fails("ENUM_OUT_OF_RANGE", lambda:
                   self.run_model(config={**configuration(),
                                          "valueDateVsPostingDate": "VALUE_DATE_ONLY"}))

    def test_reclassification_requires_matching_source_bound_digest(self):
        inp = override_ledger()
        inp["reclassificationRevisionSha256"] = "b" * 64
        self.fails("DIRECT_CFO_RECLASS_REVISION_MISMATCH", lambda:
                   self.run_model(inp, variant="DIRECT_RECLASSIFIED_CFO"))

    def test_reclassification_unknown_posting_and_class_rejected(self):
        data = override_ledger(replacements=[
            {"postingId": "P99", "newClassificationCode": "SUPPLIER_PAYMENT",
             "reasonCode": "DOCUMENTED_RECLASSIFICATION"}])
        self.fails("DIRECT_CFO_OVERRIDE_UNKNOWN_POSTING", lambda:
                   self.run_model(data, variant="DIRECT_RECLASSIFIED_CFO"))
        data = override_ledger(replacements=[
            {"postingId": "P3", "newClassificationCode": "NO_SUCH_CLASS",
             "reasonCode": "DOCUMENTED_RECLASSIFICATION"}])
        self.fails("DIRECT_CFO_OVERRIDE_UNKNOWN_CLASS", lambda:
                   self.run_model(data, variant="DIRECT_RECLASSIFIED_CFO"))

    def test_internal_transfer_reclassification_not_permitted(self):
        data = override_ledger(replacements=[
            {"postingId": "P5", "newClassificationCode": "CLIENT_RECEIPT",
             "reasonCode": "DOCUMENTED_RECLASSIFICATION"}])
        self.fails("DIRECT_CFO_FORBIDDEN_OVERRIDE", lambda:
                   self.run_model(data, variant="DIRECT_RECLASSIFIED_CFO"))

    def test_reclassification_cannot_be_noop_or_duplicate(self):
        data = override_ledger(replacements=[
            {"postingId": "P3", "newClassificationCode": "CAPEX_PAYMENT",
             "reasonCode": "DOCUMENTED_RECLASSIFICATION"}])
        self.fails("DIRECT_CFO_FORBIDDEN_OVERRIDE", lambda:
                   self.run_model(data, variant="DIRECT_RECLASSIFIED_CFO"))
        changes = [{"postingId": "P3", "newClassificationCode": "SUPPLIER_PAYMENT",
                    "reasonCode": "DOCUMENTED_RECLASSIFICATION"}] * 2
        self.fails("DIRECT_CFO_OVERRIDE_DUPLICATE", lambda:
                   override_ledger(replacements=changes))

    def test_reference_output_deep_frozen_and_replay_sha(self):
        a = self.run_model()
        b = self.run_model()
        self.assertEqual(a.output_sha256, b.output_sha256)
        with self.assertRaises(TypeError):
            a.output["cashFlowFromOperations"] = "0"
        self.assertEqual(len(a.output_sha256), 64)

    def test_non_reference_financial_admission_blocked(self):
        with self.assertRaises(CalculationError) as captured:
            self.engine.calculate("HC.CASH.04", "DIRECT_POSTED_CFO",
                                  ledger(), configuration())
        self.assertEqual(captured.exception.code, "FINANCIAL_S2_REQUIRED")

    def test_automatic_selection_ambiguity_fail_closed(self):
        self.fails("AMBIGUOUS_VARIANT", lambda:
                   self.sem.resolve_unique("HC.CASH.04", configuration(),
                                           reference_mode=True))


if __name__ == "__main__":
    unittest.main()
