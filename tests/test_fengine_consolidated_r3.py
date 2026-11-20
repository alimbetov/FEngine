"""Consolidated method-variant R3 registry smoke/semantic integrity.

R3 is a candidate contract review, not finance S2 or executable HC implementation.
The tests never calculate or approve formulas.
"""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "catalog"


def read_catalog(name: str):
    with (ROOT / name).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise AssertionError("bad TSV data " + name)
    return rows


class ConsolidatedMethodContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = read_catalog("method_parameter_candidates_116_r3.tsv")
        cls.variants = read_catalog("method_variant_definitions_116_r3.tsv")
        cls.profiles = read_catalog("model_variant_profiles_116_r3.tsv")
        cls.legacy = read_catalog("method_parameter_candidates_r2.tsv")
        cls.legacy_variants = read_catalog("method_variant_definitions_r2.tsv")
        cls.w5 = read_catalog("model_extensions_r2.tsv")
        cls.w5_formulas = read_catalog("risk_hedge_insurance_formula_candidates_r2.tsv")

    def test_exact_registered_counts_and_uniqueness(self):
        self.assertEqual(len(self.params), 732)
        self.assertEqual(len(self.variants), 222)
        self.assertEqual(len(self.profiles), 116)
        self.assertEqual(len({p["modelCode"] for p in self.params}), 116)
        self.assertEqual(len({(p["modelCode"], p["parameterCode"]) for p in self.params}), 732)
        self.assertEqual(len({(v["modelCode"], v["variantCode"]) for v in self.variants}), 222)
        self.assertEqual(len({p["modelCode"] for p in self.profiles}), 116)

    def test_preserved_95_model_parameters_without_silent_overrides(self):
        old = {(p["modelCode"], p["parameterCode"]): p for p in self.legacy}
        new = {(p["modelCode"], p["parameterCode"]): p for p in self.params}
        self.assertEqual(len(old), 625)
        for key, row in old.items():
            with self.subTest(parameter=key):
                self.assertIn(key, new)
                for field, val in row.items():
                    self.assertEqual(new[key][field], val)

    def test_wave5_model_coverage_and_typed_parameters(self):
        model_codes = {r["modelCode"] for r in self.w5}
        self.assertEqual(len(model_codes), 21)
        wave = [p for p in self.params if p["modelCode"] in model_codes]
        self.assertEqual(len(wave), 107)
        form = {f["modelCode"]: f for f in self.w5_formulas}
        for x in self.w5:
            expected = dict(t.strip().split(":", 1)
                            for t in form[x["modelCode"]]["parametersWithLogicalTypes"].split(";")
                            if t.strip())
            got = {p["parameterCode"]: p["logicalType"] for p in wave
                   if p["modelCode"] == x["modelCode"]}
            self.assertEqual(expected, got)

    def test_variant_profiles_are_referentially_complete(self):
        variants = {(v["modelCode"], v["variantCode"]) for v in self.variants}
        params = {(p["modelCode"], p["parameterCode"]) for p in self.params}
        for profile in self.profiles:
            codes = profile["candidateVariantCodes"].split("|")
            with self.subTest(model=profile["modelCode"]):
                self.assertEqual(len(codes), int(profile["variantCount"]))
                self.assertEqual(len(set(codes)), len(codes))
                self.assertEqual(profile["qualifiedVariantCount"], "0")
                self.assertEqual(profile["financialS2"], "NOT_APPROVED")
                self.assertEqual(profile["runtimeStatus"], "NOT_IMPLEMENTED")
                for code in codes:
                    self.assertIn((profile["modelCode"], code), variants)
        for variant in self.variants:
            with self.subTest(variant=variant["modelCode"] + ":" + variant["variantCode"]):
                self.assertEqual(variant["runtimeStatus"], "NOT_IMPLEMENTED")
                for param in variant["variantParameterKeys"].split("|"):
                    if param:
                        self.assertIn((variant["modelCode"], param), params)

    def test_preserve_legacy_method_variants_unmodified(self):
        old = {(v["modelCode"], v["variantCode"]): v for v in self.legacy_variants}
        new = {(v["modelCode"], v["variantCode"]): v for v in self.variants}
        self.assertEqual(len(old), 201)
        for key, row in old.items():
            self.assertIn(key, new)
            self.assertEqual(row, new[key])

    def test_no_finance_approval_or_unqualified_defaults(self):
        self.assertTrue(all(p["financialS2"] == "NOT_APPROVED" for p in self.params))
        self.assertTrue(all(p["defaultPolicy"] == "NONE" for p in self.params))
        self.assertTrue(all(p["definitionStatus"] == "DRAFT_NOT_QUALIFIED" for p in self.params))
        self.assertEqual(sum(p["sourceClass"] == "W5_FORMULA_CANDIDATE" for p in self.params), 107)

    def test_wave5_candidate_variants_do_not_claim_approved_formulas(self):
        wave_models = {x["modelCode"] for x in self.w5}
        wave_variants = [v for v in self.variants if v["modelCode"] in wave_models]
        self.assertEqual(len(wave_variants), 21)
        self.assertTrue(all(v["variantCode"] == "W5_BASE_FORMULA_CANDIDATE" for v in wave_variants))
        self.assertTrue(all(v["definitionStatus"] == "FORMULA_CANDIDATE_REVIEW_REQUIRED"
                            for v in wave_variants))
        self.assertTrue(all(v["approvalEvidence"] == "FINANCIAL_S2_REQUIRED" for v in wave_variants))


if __name__ == "__main__":
    unittest.main()
