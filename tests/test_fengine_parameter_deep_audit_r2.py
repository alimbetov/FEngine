"""Deep 95-model variant and parameterization audit, not financial runtime tests.

Verifies that each HC model has explicit candidate method choices, cross-parameter
restrictions, typed parameter proposals and separate financial sign-off gates.
These checks DO NOT qualify any financial method or execute its real runtime.
"""
from __future__ import annotations

import csv
import io
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    "docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md",
    "docs/FENGINE-HPC-WAVE2-P1-42-METHOD-DTO-RESULT-TZ.md",
    "docs/FENGINE-HPC-WAVE3-P2-27-STATISTICAL-METHOD-DTO-TZ.md",
    "docs/FENGINE-MODEL-EXT-R1-WAVE4-12-CONTRACTS-TZ.md",
)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def table(path: str):
    return list(csv.DictReader(io.StringIO(text(path)), delimiter="\t"))


class AllModelVariantAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = table("docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv")
        cls.audit = table("docs/FENGINE-R95-DEEP-PARAMETERIZATION-REVIEW.tsv")
        cls.profiles = table("catalog/model_variant_profiles_r2.tsv")
        cls.variants = table("catalog/method_variant_definitions_r2.tsv")
        cls.params = table("catalog/method_parameter_candidates_r2.tsv")

    def test_all_95_models_individually_audited(self):
        baseline = {row["metricCode"] for row in self.baseline}
        self.assertEqual(len(baseline), 95)
        self.assertEqual(len(self.audit), 95)
        self.assertEqual({a["modelCode"] for a in self.audit}, baseline)
        for a in self.audit:
            with self.subTest(model=a["modelCode"]):
                self.assertEqual(a["family"], a["modelCode"].split(".")[1])
                self.assertNotEqual(a["reviewedCandidateVariants"], "BASE_METHOD_REVIEW")
                self.assertTrue(a["newTypedParameterGaps"])
                self.assertTrue(a["crossParameterGuard"])
                self.assertIn(a["priority"], {"CRITICAL", "HIGH", "MEDIUM"})
                self.assertEqual(a["methodVariantQualStatus"], "METHOD_REVIEW_REQUIRED")
                self.assertEqual(a["reviewDecision"], "DO_NOT_FREEZE")

    def test_95_method_profiles_not_generic_placeholders(self):
        baseline = {row["metricCode"] for row in self.baseline}
        self.assertEqual(len(self.profiles), 95)
        self.assertEqual({p["modelCode"] for p in self.profiles}, baseline)
        for p in self.profiles:
            with self.subTest(model=p["modelCode"]):
                self.assertNotIn("BASE_METHOD_REVIEW", p["candidateVariantCodes"])
                self.assertTrue(p["configurableDimensions"])
                self.assertTrue(p["crossParameterGuards"])
                self.assertEqual(p["defaultMethodPolicy"], "NONE_UNTIL_APPROVED")
                self.assertEqual(p["qualifiedVariantCount"], "0")
                self.assertEqual(p["financialS2"], "NOT_APPROVED")
                self.assertEqual(p["runtimeStatus"], "NOT_IMPLEMENTED")
                self.assertEqual(int(p["variantCount"]), len(p["candidateVariantCodes"].split("|")))

    def test_201_candidate_variants_exactly_match_profiles(self):
        expected = {
            (p["modelCode"], variant)
            for p in self.profiles
            for variant in p["candidateVariantCodes"].split("|")
        }
        actual = {(v["modelCode"],v["variantCode"]) for v in self.variants}
        self.assertEqual(len(self.variants), 201)
        self.assertEqual(len(actual), 201)
        self.assertEqual(expected, actual)
        self.assertEqual(sum(int(p["variantCount"]) for p in self.profiles), 201)
        for v in self.variants:
            with self.subTest(model=v["modelCode"], variant=v["variantCode"]):
                self.assertRegex(v["variantCode"], r"^[A-Za-z][A-Za-z0-9_]*$")
                self.assertEqual(v["financialS2"] if "financialS2" in v else
                                 v["approvalEvidence"], "FINANCIAL_S2_REQUIRED")
                self.assertEqual(v["runtimeStatus"], "NOT_IMPLEMENTED")
                self.assertEqual(v["methodRevisionStatus"], "NEW_IMMUTABLE_REVISION_REQUIRED")
                self.assertIn(v["definitionStatus"],{
                    "DRAFT_FORMULA_DESCRIPTOR_EXISTS",
                    "METHOD_FORMULA_REVIEW_REQUIRED",
                })

    def test_formula_maturity_transparent_not_201_fully_qualified(self):
        counts=Counter(v["definitionStatus"] for v in self.variants)
        self.assertEqual(counts["DRAFT_FORMULA_DESCRIPTOR_EXISTS"], 13)
        self.assertEqual(counts["METHOD_FORMULA_REVIEW_REQUIRED"], 188)
        self.assertTrue(all(v["formulaDescriptor"] for v in self.variants))
        # Formula description != finance-approved golden != production code.

    def test_625_unique_typed_parameters_for_95_models(self):
        self.assertEqual(len(self.params),625)
        self.assertEqual(
            len({(p["modelCode"],p["parameterCode"]) for p in self.params}),625)
        self.assertEqual(
            {p["modelCode"] for p in self.params},
            {row["metricCode"] for row in self.baseline},
        )
        counts=Counter(p["sourceClass"] for p in self.params)
        self.assertEqual(counts["R1_EXISTING"],310)
        self.assertEqual(counts["VARIANT_SPECIFIC_R1"],36)
        self.assertEqual(counts["DEEP_REVIEW_R2"],279)
        allowed_types={"CODE","ENUM","REFERENCE","LOCAL_DATE","BOOLEAN","INTEGER",
                       "INT64","PERIOD","RATIO","RATE","MONEY","DECIMAL",
                       "LIST","STRUCT","QUANTITY"}
        for p in self.params:
            with self.subTest(model=p["modelCode"], param=p["parameterCode"]):
                self.assertIn(p["logicalType"], allowed_types)
                self.assertEqual(p["defaultPolicy"],"NONE")
                self.assertEqual(p["financialS2"],"NOT_APPROVED")
                self.assertEqual(p["approvalState"],"PENDING_INDEPENDENT_FINANCE_REVIEW")
                self.assertEqual(p["definitionStatus"],"DRAFT_NOT_QUALIFIED")
                self.assertTrue(p["requiredWhen"])
                self.assertTrue(p["unitPolicy"])

    def test_all_18_families_have_full_model_review(self):
        base=Counter(x["metricCode"].split(".")[1] for x in self.baseline)
        audit=Counter(x["family"] for x in self.audit)
        profile=Counter(x["family"] for x in self.profiles)
        self.assertEqual(len(base),18)
        self.assertEqual(audit,base)
        self.assertEqual(profile,base)

    def test_method_specific_guards_present_in_review(self):
        audit={p["modelCode"]:p for p in self.audit}
        expected={
            "HC.ECL.02":"later cash shortfalls",
            "HC.LOAN.02":"annuity != asset depreciation",
            "HC.DCF.03":"tangent/multiple roots",
            "HC.COST.03":"total-volume vs mix",
            "HC.RISK.03":"fractional quantile atom",
            "HC.PLAN.08":"feasible != optimal",
            "HC.ASSET.01":"annuity management only",
            "HC.ACC.05":"unconditional DTA",
            "HC.STOCK.02":"moving vs periodic",
            "HC.PF.02":"senior service",
            "HC.ALM.02":"not automatic Basel qualification",
            "HC.PRICE.01":"feasible tick constraint",
        }
        for code,token in expected.items():
            with self.subTest(model=code):
                self.assertIn(token,audit[code]["crossParameterGuard"])

    def test_depreciation_loan_separate_variant_taxonomies(self):
        profiles={p["modelCode"]:p for p in self.profiles}
        asset=profiles["HC.ASSET.01"]["candidateVariantCodes"].split("|")
        loan=profiles["HC.LOAN.02"]["candidateVariantCodes"].split("|")
        self.assertEqual(len(asset),8)
        self.assertEqual(len(loan),5)
        self.assertIn("SUM_OF_YEARS_DIGITS",asset)
        self.assertIn("ANNUITY_CAPITAL_RECOVERY_MGMT",asset)
        self.assertIn("ANNUITY_EQUAL_PAYMENT_DATED",loan)
        self.assertFalse(set(asset)&set(loan))

    def test_95_source_specifications_retained(self):
        sections=set()
        for path in SPECS:
            doc=text(path)
            codes=re.findall(r"^### \d{2}\. (HC\.[A-Z]+\.\d{2})",doc,re.M)
            for code in codes:
                self.assertNotIn(code,sections)
                sections.add(code)
        self.assertEqual(sections,{x["modelCode"] for x in self.audit})

    def test_never_claim_this_is_financial_qualification(self):
        spec=text("docs/FENGINE-FLEX-METHOD-R1-METHOD-VARIANTS-TZ.md")
        self.assertIn("NOT_IMPLEMENTED",spec)
        self.assertIn("CONTRACT_FREEZE_BLOCKED",spec)
        self.assertIn("FINANCIAL_S2_HOLD",spec)
        self.assertTrue(all(a["financialS2"]=="HOLD" for a in self.audit))
        self.assertTrue(all(p["financialS2"]=="NOT_APPROVED" for p in self.profiles))


if __name__=="__main__":
    unittest.main()
