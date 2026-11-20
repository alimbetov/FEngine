"""HC-R0.4 safe automatic selection and catalog-bound 222-variant contract audit."""
from __future__ import annotations

import unittest
from pathlib import Path
from fengine_hc.reference import CalculationError
from fengine_hc.semantics import ParameterSemantics, RULES

ROOT = Path(__file__).resolve().parents[1]
REV = "a" * 64

CFO_CONFIG = {"netIncomeBasis": "REPORTED_AFTER_TAX_NET_INCOME",
              "noncashAdjustment": "SIGNED_NONCASH_LINES",
              "workingCapitalSign": "INCREASE_OF_NWC_IS_OUTFLOW"}
ESCALATION_CONFIG = {"inflationIndexRev": REV,
                     "compoundingBasis": "DISCRETE_ANNUAL_END",
                     "contingencyOverlap": "NO_CONTINGENCY_DOUBLE_COUNT"}


class CatalogSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = ParameterSemantics(ROOT)

    def err(self, code, func):
        with self.assertRaises(CalculationError) as raised:
            func()
        self.assertEqual(raised.exception.code, code)

    def test_all_rule_dependencies_are_registered_and_typed(self):
        self.assertEqual(len(self.p.registry.variants), 222)
        self.assertEqual(len(self.p.bindings), 732)
        self.assertEqual(len(RULES), 29)
        self.assertEqual({k for k in RULES if k not in self.p.registry.variants}, set())
        for (model, variant), rule in RULES.items():
            with self.subTest(model=model, variant=variant):
                self.assertTrue(set(rule.required).isdisjoint(rule.optional))
                for name in (*rule.required, *rule.optional):
                    self.assertIn((model, name), self.p.bindings)

    def test_resolve_auto_chooses_cfo_adjustment_only(self):
        value = self.p.resolve_unique("HC.CASH.05", CFO_CONFIG, reference_mode=True)
        self.assertEqual(value.variant_code, "INDIRECT_CFO_ADJUSTMENT")
        self.assertEqual(value.status, "REFERENCE_NOT_S2")
        self.assertEqual(value.config["workingCapitalSign"], "INCREASE_OF_NWC_IS_OUTFLOW")

    def test_resolve_auto_chooses_cfo_reconciled_only(self):
        cfg = {**CFO_CONFIG, "directIndirectComparisonPolicy": "EXACT_EQUALITY"}
        a = self.p.resolve_unique("HC.CASH.05", cfg, reference_mode=True)
        b = self.p.resolve("HC.CASH.05", "INDIRECT_CFO_RECONCILED",
                           cfg, reference_mode=True)
        self.assertEqual(a.variant_code, "INDIRECT_CFO_RECONCILED")
        self.assertEqual(a.config_sha256, b.config_sha256)

    def test_selector_is_ambiguous_for_same_config_dcf_irr(self):
        cfg = {"rootDomain": {"minRate": "-0.9", "maxRate": "5"},
               "rootCompletenessPolicy": "CERTIFIED_ALL"}
        self.err("AMBIGUOUS_VARIANT", lambda:
                 self.p.resolve_unique("HC.DCF.03", cfg, reference_mode=True))
        self.err("AMBIGUOUS_VARIANT", lambda:
                 self.p.resolve_unique("HC.DCF.01", {}, reference_mode=True))

    def test_selector_can_disambiguate_timing_convention(self):
        out = self.p.resolve_unique("HC.DCF.01",
                                    {"timingConvention": "MIDPERIOD"}, reference_mode=True)
        self.assertEqual(out.variant_code, "MIDPERIOD_NPV")

    def test_declared_but_unreviewed_catalog_variants_never_auto_admitted(self):
        self.err("NO_COMPATIBLE_VARIANT", lambda:
                 self.p.resolve_unique("HC.DCF.06", {}, reference_mode=True))
        self.err("NO_COMPATIBLE_VARIANT", lambda:
                 self.p.resolve_unique("HC.COST.05",
                                       {"compoundingBasis": "DISCRETE_ANNUAL_END"},
                                       reference_mode=True))
        self.err("NO_COMPATIBLE_VARIANT", lambda:
                 self.p.resolve_unique("HC.COST.05",
                                       {**ESCALATION_CONFIG, "inflationIndexRev": "unbound"},
                                       reference_mode=True))

    def test_source_pins_and_auto_select_strict(self):
        a = self.p.resolve_unique("HC.COST.05", ESCALATION_CONFIG, reference_mode=True)
        self.assertEqual(a.variant_code, "COMPOUND_ESCALATION")
        self.assertEqual(a.config["inflationIndexRev"], REV)
        self.err("FINANCIAL_S2_REQUIRED", lambda:
                 self.p.resolve_unique("HC.COST.05", ESCALATION_CONFIG))

    def test_unknown_model_does_not_claim_compatible_variant(self):
        self.err("UNKNOWN_MODEL", lambda:
                 self.p.resolve_unique("HC.NOSUCH.09", {}, reference_mode=True))


if __name__ == "__main__":
    unittest.main()
