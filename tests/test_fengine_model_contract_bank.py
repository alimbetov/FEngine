"""FEngine contract-level bank: 95/95 specification checks plus independent Decimal oracles.

These tests do NOT import or execute financial HC algorithms (not implemented). The
separate GEO-OPT Python reference suite is outside the 95-model catalogue.
Run from repo root: python -m unittest discover -s tests -p 'test_fengine_model_contract_bank.py' -v
"""
from __future__ import annotations

import csv
import io
import re
import unittest
from collections import Counter
from datetime import date
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 48
ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    ("W1", "docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md", 14),
    ("W2", "docs/FENGINE-HPC-WAVE2-P1-42-METHOD-DTO-RESULT-TZ.md", 42),
    ("W3", "docs/FENGINE-HPC-WAVE3-P2-27-STATISTICAL-METHOD-DTO-TZ.md", 27),
    ("W4", "docs/FENGINE-MODEL-EXT-R1-WAVE4-12-CONTRACTS-TZ.md", 12),
)
D = Decimal


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def tsv(path: str, *, skip_comments=False):
    text = read(path)
    if skip_comments:
        text = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def extract_contracts():
    sections = {}
    per_wave = {}
    for wave, path, expected in SPECS:
        text = read(path)
        heads = list(re.finditer(r"^### \d{2}\. (HC\.[A-Z]+\.\d{2})[^\n]*$", text, re.M))
        per_wave[wave] = len(heads)
        for i, m in enumerate(heads):
            key = m.group(1)
            if key in sections:
                raise AssertionError(f"duplicate model section: {key}")
            body = text[m.start():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            sections[key] = (wave, body)
    return sections, per_wave


class ContractBank(unittest.TestCase):
    def test_all_95_specifications_have_required_sections(self):
        sections, per_wave = extract_contracts()
        self.assertEqual(per_wave, {"W1": 14, "W2": 42, "W3": 27, "W4": 12})
        self.assertEqual(len(sections), 95)
        requirements = {
            "input": r"input|входн",
            "parameters": r"параметр|parameter|params|param",
            "method": r"метод|formula|method|математи|правило вычислен|calculation",
            "output": r"output|выход|result|результат",
            "positive_example": r"example|пример|synthetic|control|контрольн|arithmetic",
            "negative": r"negative|негатив|ошиб|blocker|ограничен|hard gate",
            "task_code": r"TaskCode|Task:",
        }
        for code, (wave, block) in sections.items():
            with self.subTest(model=code, wave=wave):
                for field, pattern in requirements.items():
                    self.assertRegex(block, re.compile(pattern, re.I), msg=f"{code} lacks {field}")
        # SPEC_COVERAGE only: these are documentation sections, not executable models.

    def test_master_and_matrix_exact_95_codes(self):
        master = read("FENGINE_MASTER_SPEC.md")
        codes = re.findall(r"^\| (HC\.[A-Z]+\.\d{2}) \|", master, re.M)
        self.assertEqual(len(codes), 95)
        self.assertEqual(len(set(codes)), 95)
        sections, _ = extract_contracts()
        self.assertEqual(set(codes), set(sections))
        rows = tsv("docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv")
        self.assertEqual(len(rows), 95)
        self.assertEqual(set(codes), {row["metricCode"] for row in rows})
        self.assertEqual(Counter(row["methodRisk"] for row in rows),
                         Counter({"CRITICAL": 28, "HIGH": 42, "MEDIUM": 25}))
        for row in rows:
            with self.subTest(model=row["metricCode"]):
                self.assertEqual(row["engineRuntime"], "NOT_IMPLEMENTED")
                self.assertEqual(row["financialS2"], "NOT_APPROVED")
                self.assertEqual(row["FINSourceBindings"], "UNVERIFIED")
                self.assertTrue(row["newParametersBeforeFreeze"])
                self.assertTrue(row["targetedNegativeCase"])

    def test_w4_registry_and_dataset_ids(self):
        rows = tsv("catalog/model_extensions_r1.tsv", skip_comments=True)
        self.assertEqual(len(rows), 12)
        self.assertEqual([r["inputDataset"] for r in rows],
                         [f"D{i}" for i in range(82, 94)])
        self.assertEqual(len({r["taskCode"] for r in rows}), 12)
        self.assertEqual(len({r["modelCode"] for r in rows}), 12)
        for row in rows:
            with self.subTest(model=row["modelCode"]):
                self.assertRegex(row["taskCode"], r"^W4\.[A-Z]+\.\d{2}\.V1$")
                self.assertEqual(row["status"], "REQUIREMENTS_DRAFT_NOT_IMPLEMENTED")
                self.assertEqual(row["bindingStatus"], "UNVERIFIED")

    def test_w4_dependencies_are_acyclic(self):
        rows = tsv("catalog/model_extensions_r1.tsv", skip_comments=True)
        new = {r["modelCode"] for r in rows}
        old = {r["metricCode"] for r in tsv(
            "docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv")}
        edges = {}
        for row in rows:
            upstream = []
            for item in row["upstreamCandidateRefs"].split("|"):
                if item == "NONE":
                    continue
                match = re.fullmatch(r"(HC\.[A-Z]+\.)(\d{2}(?:/\d{2})*)", item)
                self.assertIsNotNone(match, msg=item)
                for part in match.group(2).split("/"):
                    code = match.group(1) + part
                    self.assertIn(code, new | old)
                    upstream.append(code)
            edges[row["modelCode"]] = [x for x in upstream if x in new]
        visiting, done = set(), set()

        def dfs(node):
            if node in visiting:
                raise AssertionError(f"cycle at {node}")
            if node in done:
                return
            visiting.add(node)
            for dep in edges[node]:
                dfs(dep)
            visiting.remove(node)
            done.add(node)

        for node in edges:
            dfs(node)
        self.assertEqual(len(done), 12)

    def test_release_freeze_remains_blocked(self):
        master = read("FENGINE_MASTER_SPEC.md")
        self.assertIn("CONTRACT_FREEZE_BLOCKED", master)
        self.assertIn("FINANCIAL_S2_HOLD", read(SPECS[3][1]))
        self.assertIn("NOT_IMPLEMENTED", read(SPECS[3][1]))


class IndependentMathematicsBank(unittest.TestCase):
    """Reference invariant examples, not FEngine HC implementation tests."""

    def test_ecl_conditional_pd_to_marginal_pd(self):
        q1, q2 = D(".10"), D(".20")
        self.assertEqual((1-q1)*(1-q2), D(".72"))
        self.assertEqual((1-q1)*q2, D(".18"))
        self.assertEqual(1-(1-q1)*(1-q2), D(".28"))

    def test_ecl_12_month_default_can_recover_in_year_two(self):
        default_in_year_one, ead, lgd, discount = D(".1"), D("100"), D(".5"), D("1.1")
        loss_after_two_years = default_in_year_one*ead*lgd/(discount**2)
        self.assertAlmostEqual(loss_after_two_years, D("4.132231404958677686"), places=16)

    def test_ecl_scenarios_probability_mass(self):
        weights = [D(".2"), D(".3"), D(".5")]
        self.assertEqual(sum(weights), 1)
        self.assertNotEqual(sum([D(".2"), D(".3"), D(".4")]), 1)

    def test_credit_nominal_eir_and_apr_not_automatically_equal(self):
        nominal = D(".10")
        one_year_effective_with_fee = D("110")/D("98") - 1
        self.assertNotEqual(nominal, one_year_effective_with_fee)
        self.assertEqual(one_year_effective_with_fee.quantize(D(".00000001")), D(".12244898"))

    def test_actual_day_count_leap_year(self):
        days = (date(2025, 1, 1)-date(2024, 1, 1)).days
        self.assertEqual(days, 366)
        self.assertNotEqual(D(days)/D(365), D(1))

    def test_annuity_principal_reconciles(self):
        principal, rate, n = D("1000"), D(".01"), 12
        payment = principal * rate/(1-(1+rate)**(-n))
        outstanding = principal
        for _ in range(n):
            interest = outstanding*rate
            outstanding -= (payment-interest)
        self.assertAlmostEqual(outstanding, D("0"), places=33)

    def test_dcf_irregular_date_is_not_equal_period_index(self):
        cash = D("110")
        dated = cash / (D("1.10")**(D("366")/D("365")))
        annual = cash / D("1.10")
        self.assertNotEqual(dated, annual)

    def test_irr_tangent_double_root(self):
        def npv(r): return -D(100)+D(200)/(1+r)-D(100)/((1+r)**2)
        self.assertEqual(npv(D(0)), 0)
        self.assertLess(npv(D("-.1")), 0)
        self.assertLess(npv(D(".1")), 0)

    def test_irr_two_roots(self):
        def npv(r): return -D(100)+D(230)/(1+r)-D(132)/((1+r)**2)
        self.assertAlmostEqual(npv(D(".1")), D(0), places=33)
        self.assertAlmostEqual(npv(D(".2")), D(0), places=33)

    def test_gordon_growth_requires_wacc_above_g(self):
        wacc, g = D(".09"), D(".03")
        self.assertGreater(wacc, g)
        self.assertAlmostEqual((D("106")/(wacc-g))*(wacc-g), D("106"), places=33)
        self.assertFalse(D(".03")>D(".03"))

    def test_capm(self):
        self.assertEqual(D(".04")+D("1.2")*D(".06"), D(".112"))

    def test_wacc(self):
        e, d, ke, kd, tax = D("60"), D("40"), D(".12"), D(".08"), D(".2")
        self.assertEqual(e/(e+d)*ke+d/(e+d)*kd*(1-tax), D(".0976"))

    def test_risk_based_pricing_simplified(self):
        self.assertEqual((D(4)+D(1)+D(2)+D(3))/D(100), D(".1"))

    def test_raroc(self):
        self.assertEqual((D(15)-D(4)-D(2)-D(3))/D(40), D(".15"))

    def test_clv_discounted_margin_without_double_retention(self):
        self.assertEqual(D(110)/D("1.1")+D(121)/(D("1.1")**2), D(200))

    def test_cac_payback_first_completed_period(self):
        cash = [D(50), D(80), D(50)]
        cumulative = D(0)
        reached = None
        for i, x in enumerate(cash, 1):
            cumulative += x
            if cumulative >= D(120):
                reached = i
                break
        self.assertEqual(reached, 2)
        self.assertEqual(cumulative, D(130))

    def test_llcr(self):
        llcr = (D(60)/D("1.1")+D(60)/(D("1.1")**2))/D(100)
        self.assertAlmostEqual(llcr, D(126)/D(121), places=33)

    def test_cash_waterfall_never_overdraws(self):
        cash, due, reserve = D(100), D(80), D(10)
        paid = min(cash,due)
        topup = min(cash-paid, reserve)
        equity = cash-paid-topup
        self.assertEqual((paid,topup,equity), (D(80),D(10),D(10)))
        self.assertEqual(paid+topup+equity, cash)

    def test_alm_delta_nii(self):
        self.assertEqual((D(100)-D(60))*D(".01"), D(".4"))

    def test_alm_delta_eve(self):
        delta = D(50)/D("1.2")-D(50)/D("1.1")
        self.assertAlmostEqual(delta, D("-3.787878787878787879"), places=16)

    def test_ftp_spread(self):
        self.assertEqual(D(100)*(D(".09")-D(".04")), D(5))

    def test_constrained_price_optimization(self):
        def profit(p): return (p-D(20))*max(D(0), D(120)-2*p)
        feasible = [D(p) for p in range(20,61)]
        self.assertEqual(max(feasible, key=profit), D(40))
        self.assertEqual(profit(D(40)), D(800))

    def test_pvm_true_mix_effect(self):
        old_qty, new_qty = (D(5),D(5)),(D(8),D(2))
        prices=(D(20),D(10))
        self.assertEqual(sum(old_qty),sum(new_qty))
        delta=sum(p*(qn-qo) for p,qn,qo in zip(prices,new_qty,old_qty))
        self.assertEqual(delta,D(30))  # pure mix, zero total-volume change

    def test_var_es_discrete_tie_mass(self):
        loss=[D(0),D(10),D(20),D(20),D(100)]
        var=sorted(loss)[3]  # nearest rank alpha=.75: ceil(3.75)=4
        self.assertEqual(var,D(20))
        # upper quantile integral over last 0.25 mass:
        es=(D(100)*D(".2")+D(20)*D(".05"))/D(".25")
        self.assertEqual(es,D(84))
        self.assertNotEqual(es,D(100))  # incorrect strict >VaR conditional

    def test_non_psd_correlation_is_invalid(self):
        # symmetric 2x2 with rho > 1: eigenvalues 1+rho, 1-rho.
        rho=D("1.2")
        self.assertLess(D(1)-rho,0)

    def test_fifo_layer_replay(self):
        # 10@5 plus 10@7: consume 12.
        self.assertEqual(D(10)*D(5)+D(2)*D(7),D(64))
        self.assertEqual(D(8)*D(7),D(56))

    def test_weighted_average_cost_replay(self):
        unit_cost=(D(10)*D(5)+D(10)*D(7))/D(20)
        self.assertEqual(unit_cost,D(6))
        self.assertEqual(unit_cost*D(12),D(72))

    def test_integer_capex_not_fractional(self):
        projects=[(D(6),D(12)),(D(5),D(8))]
        feasible=[]
        for a in (0,1):
            for b in (0,1):
                cap=projects[0][0]*a+projects[1][0]*b
                if cap<=D(10):
                    feasible.append((projects[0][1]*a+projects[1][1]*b,(a,b)))
        self.assertEqual(max(feasible), (D(12),(1,0)))

    def test_cash_runway_first_passage_boundary(self):
        balances=[D(10),D(5),D(0),D(-2)]
        first=next(i for i,b in enumerate(balances) if b<=0)
        self.assertEqual(first,2)


if __name__ == "__main__":
    unittest.main()
