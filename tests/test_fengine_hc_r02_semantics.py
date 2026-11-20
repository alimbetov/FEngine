"""HC-R0.2A tests — actual 732-row audit and typed variant constraints."""
import unittest
from pathlib import Path
from decimal import Decimal

from fengine_hc.reference import CalculationError
from fengine_hc.semantics import ParameterSemantics, KNOWN_TYPE_COLLISIONS

ROOT = Path(__file__).resolve().parents[1]


class ParameterSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ParameterSemantics(ROOT)

    def fails(self, code, f):
        with self.assertRaises(CalculationError) as got:
            f()
        self.assertEqual(code, got.exception.code)

    def test_parameter_catalog_has_complete_typed_baseline(self):
        r = self.registry
        self.assertEqual(len(r.bindings), 732)
        self.assertEqual(r.unique_names, 704)
        self.assertEqual(len(r.typed_candidate_ids), 709)
        self.assertEqual(set(r.collisions), KNOWN_TYPE_COLLISIONS)
        self.assertEqual(set(r.collisions["horizon"]), {"INTEGER", "PERIOD"})
        self.assertTrue(all(b.approval == "NOT_APPROVED" for b in r.bindings.values()))

    def test_incompatible_parameter_names_remain_separate(self):
        types = {b.semantic_candidate_id for b in self.registry.bindings.values()
                 if b.name == "dayCount"}
        self.assertEqual(types, {"CAND.CODE.dayCount", "CAND.ENUM.dayCount"})

    def test_resolve_npv_is_config_hash_stable(self):
        a = self.registry.resolve("HC.DCF.01", "PERIOD_END_NPV",
                                  {"timingConvention": "PERIOD_END"}, reference_mode=True)
        b = self.registry.resolve("HC.DCF.01", "PERIOD_END_NPV",
                                  {"timingConvention": "PERIOD_END"}, reference_mode=True)
        self.assertEqual(a.config_sha256, b.config_sha256)
        self.assertEqual(a.status, "REFERENCE_NOT_S2")
        with self.assertRaises(TypeError):
            a.config["timingConvention"] = "MIDPERIOD"
        self.fails("ENUM_OUT_OF_RANGE", lambda:
                   self.registry.resolve("HC.DCF.01", "PERIOD_END_NPV",
                                         {"timingConvention": "MIDPERIOD"}, reference_mode=True))

    def test_domain_and_decimal_type(self):
        good = self.registry.resolve("HC.DCF.03", "ALL_REAL_IRR_ROOTS",
                                     {"rootDomain": {"minRate": "-0.9", "maxRate": "5"},
                                      "rootCompletenessPolicy": "CERTIFIED_ALL"},
                                     reference_mode=True)
        self.assertEqual(good.config["rootDomain"]["minRate"], "-0.9")
        self.fails("INVALID_ROOT_DOMAIN", lambda:
                   self.registry.resolve("HC.DCF.03", "ALL_REAL_IRR_ROOTS",
                       {"rootDomain": {"minRate": "-1", "maxRate": "5"},
                        "rootCompletenessPolicy": "CERTIFIED_ALL"}, reference_mode=True))
        self.fails("DECIMAL_STRING_REQUIRED", lambda:
                   self.registry.resolve("HC.DCF.03", "ALL_REAL_IRR_ROOTS",
                       {"rootDomain": {"minRate": -0.9, "maxRate": "5"},
                        "rootCompletenessPolicy": "CERTIFIED_ALL"}, reference_mode=True))

    def test_strict_rules_no_unqualified_default(self):
        self.fails("FINANCIAL_S2_REQUIRED", lambda:
                   self.registry.resolve("HC.DCF.01", "MIDPERIOD_NPV", {}))
        self.fails("VARIANT_RULE_NOT_IMPLEMENTED", lambda:
                   self.registry.resolve("HC.ASSET.01", "STRAIGHT_LINE", {},
                                         reference_mode=True))
        self.fails("REQUIRED_PARAMETER_MISSING", lambda:
                   self.registry.resolve("HC.RISK.02", "EMPIRICAL_LEFT_QUANTILE", {},
                                         reference_mode=True))
        self.fails("UNCONSUMED_CONFIGURATION", lambda:
                   self.registry.resolve("HC.DCF.01", "MIDPERIOD_NPV",
                                         {"riskFreeCurve": "x"}, reference_mode=True))


if __name__ == "__main__":
    unittest.main()
