"""R1 pre-freeze mathematical controls and draft parameter registry checks.

These tests deliberately do not import a financial HC engine. They test independent
reference properties and that **all 95** model candidates have parameter proposals,
while financial S2 and immutable contract freeze remain blocked.
"""
from __future__ import annotations

import csv
import io
import re
import unittest
from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 48
D = Decimal
ROOT = Path(__file__).resolve().parents[1]
METHOD_FILES = (
    "docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md",
    "docs/FENGINE-HPC-WAVE2-P1-42-METHOD-DTO-RESULT-TZ.md",
    "docs/FENGINE-HPC-WAVE3-P2-27-STATISTICAL-METHOD-DTO-TZ.md",
    "docs/FENGINE-MODEL-EXT-R1-WAVE4-12-CONTRACTS-TZ.md",
)
AMENDED = {
    "HC.LOAN.01", "HC.LOAN.03", "HC.DCF.03", "HC.ECL.02",
    "HC.ECL.03", "HC.DCF.04", "HC.DCF.07", "HC.COST.03",
    "HC.ECL.04", "HC.RISK.01", "HC.RISK.02", "HC.RISK.03",
    "HC.PLAN.08", "HC.CAP.02", "HC.CREDIT.01", "HC.ALM.01", "HC.PRICE.01",
}


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def load_tsv(path):
    return list(csv.DictReader(io.StringIO(source(path)), delimiter="\t"))


def pvm(p0, p1, q0, q1):
    if len(p0) != len(p1) or len(q0) != len(q1) or len(p0) != len(q0):
        raise ValueError("SKU alignment")
    if not p0 or sum(q0) <= 0 or sum(q1) <= 0:
        raise ValueError("total quantities require nonzero comparable base and actual")
    if any(q < 0 for q in q0 + q1):
        raise ValueError("negative units require separate approved variant")
    Q0 = sum(q0)
    Q1 = sum(q1)
    base_average_price = sum(p*q for p, q in zip(p0, q0))/Q0
    price = sum(q*(p1_i-p0_i) for p0_i,p1_i,q in zip(p0,p1,q1))
    volume = (Q1-Q0)*base_average_price
    mix = sum(p0_i*(q1_i-Q1*q0_i/Q0) for p0_i,q0_i,q1_i in zip(p0,q0,q1))
    revenue_delta = sum(p*q for p,q in zip(p1,q1))-sum(p*q for p,q in zip(p0,q0))
    return price, volume, mix, revenue_delta, revenue_delta-price-volume-mix


def probability_mass(losses, weights, alpha):
    """Independent empirical left-CDF quantile & upper quantile-integral ES oracle."""
    if not len(losses) or len(losses) != len(weights):
        raise ValueError("empty/misaligned distribution")
    if not (D(0) < alpha < D(1)) or any(w < 0 for w in weights):
        raise ValueError("invalid alpha/weights")
    if sum(weights) != D(1):
        raise ValueError("unapproved weight normalization")
    points = sorted(zip(losses,weights), key=lambda pair: pair[0])
    cumulative = D(0)
    var = None
    for loss, weight in points:
        cumulative += weight
        if cumulative >= alpha:
            var = loss
            break
    # Integrate step quantile over top (1-alpha) probability mass.
    cumulative = D(0)
    top_sum = D(0)
    for loss, weight in points:
        lower = cumulative
        upper = cumulative + weight
        overlap = max(D(0), upper-max(alpha,lower))
        top_sum += loss*overlap
        cumulative = upper
    return var, top_sum/(D(1)-alpha)


def marginal_pd(hazards):
    survival = D(1)
    out = []
    for hazard in hazards:
        if not D(0) <= hazard <= D(1):
            raise ValueError("hazard outside [0,1]")
        out.append(survival*hazard)
        survival *= D(1)-hazard
    return out, survival


class ParameterRegistryQualification(unittest.TestCase):
    def test_95_models_have_unique_parameter_proposals(self):
        rows = load_tsv("catalog/method_parameter_candidates_r1.tsv")
        self.assertEqual(len(rows), 310)
        models = {r["modelCode"] for r in rows}
        self.assertEqual(len(models), 95)
        self.assertEqual(len({(r["modelCode"], r["parameterCode"]) for r in rows}), len(rows))
        base = load_tsv("docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv")
        self.assertEqual(models, {r["metricCode"] for r in base})

    def test_parameter_types_no_implicit_defaults_or_false_admission(self):
        rows = load_tsv("catalog/method_parameter_candidates_r1.tsv")
        allowed = {"CODE","ENUM","REFERENCE","LOCAL_DATE","BOOLEAN","INTEGER","INT64",
                   "PERIOD","RATIO","RATE","MONEY","DECIMAL","LIST","STRUCT","QUANTITY"}
        for row in rows:
            with self.subTest(model=row["modelCode"], param=row["parameterCode"]):
                self.assertIn(row["logicalType"], allowed)
                self.assertEqual(row["defaultPolicy"], "NONE")
                self.assertEqual(row["domainReview"], "PENDING")
                self.assertEqual(row["financialS2"], "NOT_APPROVED")
                self.assertEqual(row["evidenceStatus"], "DRAFT_UNQUALIFIED")
                self.assertIn(row["requirednessProposal"], {"REQUIRED","REVIEW_PENDING"})
                self.assertTrue(row["parameterCode"])
        self.assertEqual(sum(r["requirednessProposal"] == "REQUIRED" for r in rows), 18)

    def test_p0_parameter_guards_are_in_candidate_catalogue(self):
        rows = {(r["modelCode"],r["parameterCode"]):r for r in
                load_tsv("catalog/method_parameter_candidates_r1.tsv")}
        required = {
            ("HC.ECL.02","defaultEventWindow"),
            ("HC.ECL.02","cashShortfallRecoveryHorizon"),
            ("HC.ECL.03","hazardConditionality"),
            ("HC.LOAN.03","rootCompletenessPolicy"),
            ("HC.DCF.03","rootCompletenessPolicy"),
            ("HC.RISK.03","esTailMassRule"),
            ("HC.COST.03","decompositionVariant"),
            ("HC.PLAN.08","decisionDomain"),
            ("HC.CREDIT.01","lossAndFundingNoDoubleCountPolicyRef"),
        }
        self.assertTrue(required.issubset(rows.keys()))
        for key in required:
            with self.subTest(param=key):
                self.assertEqual(rows[key]["requirednessProposal"], "REQUIRED")

    def test_17_original_method_sections_reference_hardening(self):
        blocks = {}
        for path in METHOD_FILES:
            text = source(path)
            sections = list(re.finditer(r"^### \d{2}\. (HC\.[A-Z]+\.\d{2})[^\n]*$",text,re.M))
            for i, item in enumerate(sections):
                code = item.group(1)
                end = sections[i+1].start() if i+1 < len(sections) else len(text)
                blocks[code] = text[item.start():end]
        self.assertEqual(len(blocks),95)
        for code in AMENDED:
            with self.subTest(model=code):
                self.assertIn("**METHOD-HARDENING-R1",blocks[code])

    def test_no_premature_freeze_or_production_claim(self):
        addendum = source("docs/FENGINE-METHOD-HARDENING-R1-P0-ADDENDUM.md")
        self.assertIn("INDEPENDENT FINANCIAL REVIEW REQUIRED", addendum)
        self.assertIn("NOT IMPLEMENTED", addendum)
        self.assertIn("PVM_THREE_FACTOR_SEQUENTIAL_V2", addendum)
        self.assertIn("FINANCIAL_S2_HOLD", source("FENGINE_MASTER_SPEC.md"))


class MethodologyControlBank(unittest.TestCase):
    def test_ecl_pd_survival(self):
        marginal, survival = marginal_pd([D(".1"),D(".2")])
        self.assertEqual(marginal,[D(".1"),D(".18")])
        self.assertEqual(survival,D(".72"))
        self.assertEqual(sum(marginal),D(".28"))

    def test_ecl_recovery_after_first_year(self):
        default_probability=D(".1")
        cash_shortfall_at_year_two=D(50)
        self.assertAlmostEqual(default_probability*cash_shortfall_at_year_two/
                               D("1.1")**2,D("4.132231404958677686"),places=16)

    def test_ecl_lifetime_later_default(self):
        marginal, _=marginal_pd([D(".1"),D(".2")])
        loss=D(100)*D(".5")
        life = marginal[0]*loss/D("1.1") + marginal[1]*loss/(D("1.1")**2)
        first12 = marginal[0]*loss/D("1.1")
        self.assertGreater(life,first12)
        self.assertAlmostEqual(life,D("11.983471074380165289"),places=16)

    def test_ecl_hazard_reject_invalid_probabilities(self):
        for bad in ([D("-0.01")],[D("1.01")],[D(".2"),D("1.2")]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                marginal_pd(bad)

    def test_nominal_interest_day_count_is_explicit(self):
        principal,r,days=D(1000),D(".12"),D(31)
        act365=principal*r*days/D(365)
        act360=principal*r*days/D(360)
        self.assertGreater(act360,act365)
        self.assertAlmostEqual(act365,D("10.191780821917808219"),places=16)

    def test_one_year_eir_not_nominal_or_regulatory(self):
        eir=D(1080)/D(980)-D(1)
        self.assertAlmostEqual(eir,D("0.102040816326530612"),places=16)
        self.assertNotEqual(eir,D(".10"))

    def test_irr_two_roots(self):
        def npv(r):return -D(100)+D(230)/(D(1)+r)-D(132)/(D(1)+r)**2
        self.assertAlmostEqual(npv(D(".1")),D(0),places=35)
        self.assertAlmostEqual(npv(D(".2")),D(0),places=35)

    def test_irr_tangent_root_missed_by_sign_change(self):
        def f(r):return -D(100)+D(200)/(D(1)+r)-D(100)/(D(1)+r)**2
        self.assertEqual(f(D(0)),D(0))
        self.assertLess(f(D("-.1")),0)
        self.assertLess(f(D(".1")),0)

    def test_gordon_terminal_eligibility(self):
        cf,wacc,g=D(106),D(".09"),D(".03")
        self.assertAlmostEqual(cf/(wacc-g), D("1766.666666666666666667"),places=15)
        self.assertFalse(D(".03")>D(".03"))

    def test_pvm_is_pure_mix_when_total_volume_constant(self):
        p,m,x,delta,res=pvm([D(20),D(10)],[D(20),D(10)],
                            [D(5),D(5)],[D(8),D(2)])
        self.assertEqual((p,m,x,delta,res),(D(0),D(0),D(30),D(30),D(0)))

    def test_pvm_mix_and_price_offset(self):
        p,v,m,delta,res=pvm([D(10),D(20)],[D(12),D(22)],
                            [D(4),D(6)],[D(5),D(5)])
        self.assertEqual((p,v,m,delta,res),(D(20),D(0),D(-10),D(10),D(0)))

    def test_pvm_grid_reconciliation_property(self):
        # Exhaustive deterministic integer grid, not synthetic financial qualification.
        prices=[(D(10),D(20)),(D(12),D(22))]
        for q0a in range(1,5):
            for q0b in range(1,5):
                for q1a in range(1,5):
                    for q1b in range(1,5):
                        p,v,m,delta,res=pvm(list(prices[0]),list(prices[1]),
                                            [D(q0a),D(q0b)],[D(q1a),D(q1b)])
                        # Decimal divisions of repeating ratios can leave sub-ulp residuals.
                        self.assertAlmostEqual(res,D(0),places=39)
                        self.assertAlmostEqual(p+v+m,delta,places=39)

    def test_pvm_reject_zero_base_or_misaligned_skus(self):
        with self.assertRaises(ValueError):
            pvm([D(10)],[D(11)],[D(0)],[D(5)])
        with self.assertRaises(ValueError):
            pvm([D(10)],[D(11),D(12)],[D(5)],[D(7)])

    def test_es_with_tied_var_atom(self):
        l=[D(0),D(10),D(20),D(20),D(100)]
        var,es=probability_mass(l,[D(".2")]*5,D(".75"))
        self.assertEqual((var,es),(D(20),D(84)))

    def test_es_weighted_mass(self):
        var,es=probability_mass([D(0),D(20),D(100)],
                                [D(".5"),D(".4"),D(".1")],D(".75"))
        self.assertEqual((var,es),(D(20),D(52)))

    def test_es_invariant_constant_distribution(self):
        var,es=probability_mass([D(5),D(5),D(5)],
                                [D(".2"),D(".3"),D(".5")],D(".95"))
        self.assertEqual((var,es),(D(5),D(5)))

    def test_es_reject_invalid_weights_and_alpha(self):
        examples=[
            ([D(0),D(1)],[D(".4"),D(".4")],D(".75")),
            ([D(0),D(1)],[D("1.2"),D("-.2")],D(".75")),
            ([D(0),D(1)],[D(".5"),D(".5")],D(1)),
        ]
        for loss,w,alpha in examples:
            with self.subTest(weights=w,alpha=alpha),self.assertRaises(ValueError):
                probability_mass(loss,w,alpha)

    def test_es_dominates_var_for_loss_tail(self):
        for alpha in [D(".5"),D(".7"),D(".75"),D(".9"),D(".99")]:
            var,es=probability_mass([D(0),D(10),D(20),D(20),D(100)],
                                    [D(".2")]*5,alpha)
            self.assertGreaterEqual(es,var)

    def test_binary_capex_budget_rejects_fractional(self):
        feasible=[]
        for a in (0,1):
            for b in (0,1):
                if a*6+b*5<=10:
                    feasible.append((a*12+b*8,a,b))
        self.assertEqual(max(feasible),(12,1,0))

    def test_feasible_solver_not_proven_optimal_at_large_gap(self):
        incumbent,dual_bound=D(12),D(14)
        gap=(dual_bound-incumbent)/max(D(1),abs(incumbent))
        self.assertGreater(gap,D(".01"))
        self.assertEqual(gap,D(1)/D(6))


if __name__ == "__main__":
    unittest.main()
