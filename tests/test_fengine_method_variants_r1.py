"""FENGINE-FLEX-METHOD-R1: specification checks and independent Decimal arithmetic only.

This suite has no access to executable HC financial models or financial S2 approval.
It tests 95 model variant profiles, 31 proposed variants, 36 specific typed parameter
definitions, and independently calculated depreciation invariants.
"""
from __future__ import annotations

import csv
import io
import unittest
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 48
D = Decimal
ROOT = Path(__file__).resolve().parents[1]


def rows(path: str):
    return list(csv.DictReader(io.StringIO(
        (ROOT / path).read_text(encoding="utf-8")), delimiter="\t"))


def depreciation_input(cost, residual, life):
    if cost < 0 or residual < 0 or residual > cost or life <= 0:
        raise ValueError("invalid cost/residual/life")


def straight_line(cost, residual, life):
    depreciation_input(cost, residual, life)
    return (cost - residual) / D(life)


def sum_years_digits(cost, residual, life):
    depreciation_input(cost, residual, life)
    denom = D(life) * D(life + 1) / D(2)
    return [(cost - residual) * D(life - t + 1) / denom
            for t in range(1, life + 1)]


def units_production(cost, residual, total, used):
    if cost < 0 or residual < 0 or residual > cost:
        raise ValueError("cost")
    if total <= 0 or used < 0 or used > total:
        raise ValueError("production volume")
    return (cost - residual) * used / total


def declining_schedule(cost, residual, life, rate):
    depreciation_input(cost, residual, life)
    if not (D(0) < rate <= D(1)):
        raise ValueError("rate")
    nbv = cost
    results = []
    for _ in range(life):
        amount = max(D(0), min(nbv * rate, nbv - residual))
        nbv -= amount
        results.append((amount, nbv))
    return results


def double_declining_with_terminal_trueup(cost, residual, life):
    depreciation_input(cost, residual, life)
    nbv = cost
    schedule = []
    rate = D(2) / D(life)
    for t in range(1, life + 1):
        amount = (nbv - residual if t == life
                  else min(max(nbv * rate, D(0)), nbv - residual))
        nbv -= amount
        schedule.append((amount, nbv))
    return schedule


def annuity_asset_schedule(cost, residual, life, rate):
    depreciation_input(cost, residual, life)
    if rate < 0:
        raise ValueError("negative interest rate")
    if rate == 0:
        return straight_line(cost, residual, life), [
            (straight_line(cost, residual, life), D(0),
             cost - D(t) * straight_line(cost, residual, life))
            for t in range(1, life + 1)]
    factor = (D(1) + rate) ** life
    annuity = (cost - residual / factor) * rate / (D(1) - D(1) / factor)
    balance = cost
    result = []
    for _ in range(life):
        interest = balance * rate
        depreciation = annuity - interest
        balance -= depreciation
        result.append((depreciation, interest, balance))
    return annuity, result


class VariantRegistryTests(unittest.TestCase):
    def test_all_95_models_have_one_unique_profile(self):
        baseline = rows("docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv")
        profiles = rows("catalog/model_variant_profiles_r1.tsv")
        self.assertEqual(len(profiles), 95)
        self.assertEqual(len({r["modelCode"] for r in profiles}), 95)
        self.assertEqual({r["modelCode"] for r in profiles},
                         {r["metricCode"] for r in baseline})
        for p in profiles:
            with self.subTest(model=p["modelCode"]):
                self.assertEqual(p["family"], p["modelCode"].split(".")[1])
                self.assertTrue(p["methodParameterCandidates"])
                self.assertEqual(p["defaultVariantPolicy"], "NONE_UNTIL_REVIEW")
                self.assertEqual(p["variantFreezeStatus"], "NOT_FROZEN")
                self.assertEqual(p["financialS2"], "NOT_APPROVED")

    def test_explicit_candidate_variants_have_catalogue_definitions(self):
        profiles = rows("catalog/model_variant_profiles_r1.tsv")
        definitions = rows("catalog/method_variant_definitions_r1.tsv")
        self.assertEqual(len(definitions), 31)
        keys = [(r["modelCode"], r["variantCode"]) for r in definitions]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(
            {(r["modelCode"], v)
             for r in profiles for v in r["candidateVariantCodes"].split("|")
             if v != "BASE_METHOD_REVIEW"},
            set(keys),
        )
        for d in definitions:
            with self.subTest(model=d["modelCode"], variant=d["variantCode"]):
                self.assertEqual(d["status"], "CANDIDATE_NOT_IMPLEMENTED_NOT_S2")
                self.assertEqual(d["methodRevisionProposal"], "NEW_REVISION_REQUIRED")
                self.assertTrue(d["requiredParameterCodes"])

    def test_asset_and_loan_are_different_families(self):
        rows_by_model = {p["modelCode"]: p for p in
                         rows("catalog/model_variant_profiles_r1.tsv")}
        asset = rows_by_model["HC.ASSET.01"]["candidateVariantCodes"].split("|")
        loan = rows_by_model["HC.LOAN.02"]["candidateVariantCodes"].split("|")
        self.assertEqual(len(asset), 8)
        self.assertEqual(len(loan), 5)
        self.assertIn("ANNUITY_CAPITAL_RECOVERY_MGMT", asset)
        self.assertIn("ANNUITY_EQUAL_PAYMENT_DATED", loan)
        self.assertNotIn("ANNUITY_EQUAL_PAYMENT_DATED", asset)
        self.assertNotIn("SUM_OF_YEARS_DIGITS", loan)

    def test_variant_conditional_parameters_typed(self):
        definitions = rows("catalog/method_variant_definitions_r1.tsv")
        params = rows("catalog/variant_specific_parameters_r1.tsv")
        self.assertEqual(len(params), 36)
        code_set = {(p["modelCode"], p["parameterCode"]) for p in params}
        self.assertEqual(len(code_set), 36)
        variants_by_model = {
            model: {d["variantCode"] for d in definitions if d["modelCode"] == model}
            for model in {"HC.ASSET.01", "HC.LOAN.02"}
        }
        allowed_types = {"MONEY", "INTEGER", "LOCAL_DATE", "ENUM", "QUANTITY",
                         "RATE", "CODE", "REFERENCE", "LIST"}
        for p in params:
            with self.subTest(model=p["modelCode"], parameter=p["parameterCode"]):
                self.assertIn(p["logicalType"], allowed_types)
                self.assertEqual(p["defaultPolicy"], "NONE")
                self.assertEqual(p["financialS2"], "NOT_APPROVED")
                self.assertEqual(p["status"], "DRAFT_UNQUALIFIED")
                if p["variantScope"] not in ("ALL", "ALL_EXCEPT_UNITS"):
                    self.assertTrue(set(p["variantScope"].split("|")).issubset(
                        variants_by_model[p["modelCode"]]))

        for d in definitions:
            if d["modelCode"] in variants_by_model:
                for param in d["requiredParameterCodes"].split("|"):
                    self.assertIn((d["modelCode"], param), code_set)

    def test_references_to_existing_310_base_proposals(self):
        base = rows("catalog/method_parameter_candidates_r1.tsv")
        self.assertEqual(len(base), 310)
        self.assertEqual(len({p["modelCode"] for p in base}), 95)
        additional = rows("catalog/variant_specific_parameters_r1.tsv")
        self.assertFalse({(p["modelCode"], p["parameterCode"]) for p in base} &
                         {(p["modelCode"], p["parameterCode"]) for p in additional})

    def test_financial_qualification_not_auto_granted(self):
        spec = (ROOT / "docs/FENGINE-FLEX-METHOD-R1-METHOD-VARIANTS-TZ.md"
                ).read_text(encoding="utf-8")
        self.assertIn("CONTRACT_FREEZE_BLOCKED", spec)
        self.assertIn("FINANCIAL_S2_HOLD", spec)
        self.assertIn("ANNUITY_CAPITAL_RECOVERY_MGMT", spec)
        self.assertIn("management only", spec.lower())


class IndependentDepreciationOracleTests(unittest.TestCase):
    def test_straight_line_200_per_full_year(self):
        self.assertEqual(straight_line(D(1200), D(200), 5), D(200))

    def test_straight_line_full_schedule_reconciles(self):
        annual = straight_line(D(1000), D(100), 4)
        self.assertEqual(sum((annual for _ in range(4)), D(0)), D(900))

    def test_cumulative_sum_years_digits(self):
        seq = sum_years_digits(D(1000), D(100), 4)
        self.assertEqual(seq, [D(360), D(270), D(180), D(90)])
        self.assertEqual(sum(seq), D(900))

    def test_units_of_production(self):
        self.assertEqual(units_production(D(1000), D(100), D(30000), D(9000)),
                         D(270))

    def test_units_of_production_full_volume_reconciles(self):
        charges = [units_production(D(1000), D(100), D(30000), x)
                   for x in (D(5000), D(7000), D(18000))]
        self.assertEqual(sum(charges), D(900))

    def test_declining_balance_does_not_cross_salvage(self):
        seq = declining_schedule(D(1000), D(100), 4, D(".5"))
        self.assertEqual(seq[0][0], D(500))
        for charge, balance in seq:
            self.assertGreaterEqual(charge, D(0))
            self.assertGreaterEqual(balance, D(100))

    def test_double_declining_terminal_trueup(self):
        seq = double_declining_with_terminal_trueup(D(1000), D(100), 4)
        self.assertEqual(seq[0][0], D(500))
        self.assertEqual(seq[-1][1], D(100))
        self.assertEqual(sum(x for x, _ in seq), D(900))

    def test_annuity_management_year_one_interest_depreciation(self):
        a, seq = annuity_asset_schedule(D(1000), D(100), 4, D(".1"))
        self.assertAlmostEqual(a, D("293.923723335488041370"), places=18)
        self.assertEqual(seq[0][1], D(100))
        self.assertAlmostEqual(seq[0][0], D("193.923723335488041370"), places=18)
        self.assertAlmostEqual(seq[-1][2], D(100), places=33)
        self.assertAlmostEqual(sum(x for x, _, _ in seq), D(900), places=33)

    def test_annuity_zero_rate_limit(self):
        a, seq = annuity_asset_schedule(D(1000), D(100), 4, D(0))
        self.assertEqual(a, D(225))
        self.assertEqual(seq[-1], (D(225), D(0), D(100)))

    def test_annuity_uses_asset_cost_not_loan_balance_legal_policy(self):
        _, seq = annuity_asset_schedule(D(1000), D(100), 4, D(".1"))
        # No equal depreciation: annuity total charge is constant, depreciation grows.
        self.assertLess(seq[0][0], seq[1][0])
        self.assertGreater(seq[0][1], seq[1][1])

    def test_reject_negative_or_overspecified_residual(self):
        bad = [(D(100), D(101), 4), (D(100), D(-1), 4),
               (D(-1), D(0), 4), (D(100), D(10), 0)]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                straight_line(*args)

    def test_reject_impossible_volume(self):
        for total, used in [(D(0), D(1)), (D(10), D(-1)),
                            (D(10), D(11))]:
            with self.subTest(total=total, used=used), self.assertRaises(ValueError):
                units_production(D(100), D(10), total, used)

    def test_annuity_negative_rate_forbidden_in_proposal(self):
        with self.assertRaises(ValueError):
            annuity_asset_schedule(D(100), D(10), 4, D("-0.01"))

    def test_cumulative_charge_nonnegative_and_monotonic(self):
        for n in range(1, 11):
            seq = sum_years_digits(D(1000), D(100), n)
            self.assertEqual(sum(seq), D(900))
            self.assertEqual(seq, sorted(seq, reverse=True))

    def test_no_automatic_zero_rate_division_error(self):
        for n in range(1, 6):
            a, seq = annuity_asset_schedule(D(100), D(10), n, D(0))
            self.assertEqual(a * n, D(90))
            self.assertEqual(seq[-1][2], D(10))


if __name__ == "__main__":
    unittest.main()
