"""QUAL-R1.2: independently authored, executed mathematical golden for all 48.

A model's own result is NEVER used to compute the expected value. Unlike
R1.1, a changed fingerprint cannot satisfy a wrong arithmetic answer.
Reference-only, synthetic input; no FIN/Redis/Rust/S2 admission.
"""
from __future__ import annotations

import csv
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from qualification_r12_goldens import build_goldens

ROOT = Path(__file__).resolve().parents[1]


def at_path(output, dotted: str):
    value = output
    for part in dotted.split("."):
        value = value[int(part)] if part.isdigit() else value[part]
    return value


class IndependentMathematicsR12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ReferenceEngine(ROOT)
        cls.cases = build_goldens()

    def test_all_48_have_a_separate_manual_numeric_golden(self):
        with (ROOT / "catalog" / "hc_reference_execution_inventory_r1.tsv").open(
            encoding="utf-8", newline=""
        ) as stream:
            inventory = list(csv.DictReader(stream, delimiter="\t"))
        declared = {(r["modelCode"], r["variantCode"]) for r in inventory}
        for entry in inventory:
            self.assertEqual(
                entry["r12NumericalOracleEvidence"],
                "tests/test_fengine_qual_r12_independent_math.py",
            )
            self.assertEqual(
                entry["r12DomainDenialEvidence"],
                "tests/test_fengine_qual_r12_domain_denials.py",
            )
            self.assertEqual(
                entry["r12QualificationStatus"],
                "R12_REFERENCE_GOLDEN_AND_NEGATIVE_NOT_S2",
            )
            self.assertEqual(entry["financialS2"], "CLOSED")
        self.assertEqual(len(inventory), 48)
        self.assertEqual(len(self.cases), 48)
        self.assertEqual(set(self.cases), declared)
        for key, case in self.cases.items():
            with self.subTest(method=key):
                self.assertEqual(key, (case.model, case.variant))
                self.assertTrue(case.rationale and len(case.rationale) > 10)
                self.assertTrue(case.expected)
                self.assertGreaterEqual(Decimal(case.tolerance), Decimal(0))
                for path, number in case.expected.items():
                    self.assertTrue(path)
                    self.assertIsInstance(number, str)
                    self.assertTrue(Decimal(number).is_finite())

    def test_real_executor_matches_independent_golden_for_every_variant(self):
        with localcontext() as ctx:
            ctx.prec = 70
            for key, case in sorted(self.cases.items()):
                with self.subTest(model=key[0], variant=key[1],
                                  rationale=case.rationale):
                    result = self.engine.calculate(
                        case.model, case.variant, case.inputs, case.config,
                        reference_mode=True,
                    )
                    self.assertEqual(
                        result.execution_class, "PYTHON_REFERENCE_NOT_S2",
                    )
                    for field, reference_value in case.expected.items():
                        actual = Decimal(str(at_path(result.output, field)))
                        delta = abs(actual - Decimal(reference_value))
                        self.assertLessEqual(
                            delta, Decimal(case.tolerance),
                            msg=f"INDEPENDENT_GOLDEN_MISMATCH: {key} {field}",
                        )

    def test_capm_numeric_metamorphic_beta_changes_true_rate_not_only_sha(self):
        original = self.cases["HC.CAP.01","CAPM_BASE"]
        result = self.engine.calculate(
            original.model, original.variant, original.inputs, original.config,
            reference_mode=True,
        )
        changed = self.engine.calculate(
            original.model, original.variant,
            {**original.inputs,"beta":"1.5"},original.config,
            reference_mode=True,
        )
        self.assertEqual(Decimal(result.output["costOfEquity"]), Decimal("0.112"))
        self.assertEqual(Decimal(changed.output["costOfEquity"]), Decimal("0.13"))
        self.assertEqual(
            Decimal(changed.output["costOfEquity"]) -
            Decimal(result.output["costOfEquity"]), Decimal("0.018"),
        )

    def test_npv_shift_in_initial_cashflow_is_exact_dollar_for_dollar(self):
        for variant in ("PERIOD_END_NPV","MIDPERIOD_NPV"):
            with self.subTest(variant=variant):
                base = self.cases["HC.DCF.01",variant]
                first = self.engine.calculate(
                    base.model,variant,base.inputs,base.config,reference_mode=True
                )
                altered = self.engine.calculate(
                    base.model,variant,
                    {**base.inputs,"cashflows":["-900","600","600"]},
                    base.config,reference_mode=True,
                )
                self.assertEqual(
                    Decimal(altered.output["npv"])-Decimal(first.output["npv"]),
                    Decimal("100"),
                )

    def test_asset_straight_line_cost_scale_is_exact_and_balanced(self):
        x=self.cases["HC.ASSET.01","STRAIGHT_LINE"]
        original=self.engine.calculate(x.model,x.variant,x.inputs,x.config,
                                       reference_mode=True)
        doubled=self.engine.calculate(
            x.model,x.variant,{"cost":"2200"},
            {"residualValue":"400","usefulLifePeriods":5},
            reference_mode=True,
        )
        self.assertEqual(Decimal(original.output["totalDepreciation"]),Decimal(1000))
        self.assertEqual(Decimal(doubled.output["totalDepreciation"]),Decimal(1800))
        self.assertEqual(Decimal(doubled.output["periods"][0]["depreciation"]),Decimal(360))
        self.assertEqual(
            sum(Decimal(row["depreciation"]) for row in doubled.output["periods"])
            + Decimal(doubled.output["closingBalance"]),
            Decimal(2200),
        )

    def test_price_volume_mix_three_factors_reconcile_and_are_not_additive_time(self):
        from test_fengine_hc_r07_pvm import pvm_fixture
        inputs,config=pvm_fixture()
        for variant in ("PRICE_VARIANCE","QUANTITY_VARIANCE","MIX_VARIANCE"):
            with self.subTest(variant=variant):
                result=self.engine.calculate(
                    "HC.COST.08",variant,inputs,config,reference_mode=True
                )
                o=result.output
                expected=(
                    Decimal(o["priceVariance"])+Decimal(o["quantityVariance"])
                    +Decimal(o["mixVariance"])
                )
                self.assertEqual(expected,Decimal("230"))
                self.assertEqual(Decimal(o["actualTotalCost"])-
                                 Decimal(o["baselineTotalCost"]),Decimal("230"))
                self.assertEqual(expected,Decimal(o["totalCostVariance"]))

    def test_fcff_negative_working_capital_change_has_correct_economic_sign(self):
        case=self.cases["HC.DCF.05","FCFF_UNLEVERED"]
        released=self.engine.calculate(
            case.model,case.variant,
            {**case.inputs,"deltaOperatingNwc":"-20"},case.config,
            reference_mode=True,
        )
        self.assertEqual(Decimal(released.output["freeCashFlowToFirm"]),Decimal(150))

    def test_irr_unique_variant_rejects_ambiguous_roots_instead_of_guess(self):
        case=self.cases["HC.DCF.03","SINGLE_IF_UNAMBIGUOUS"]
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate(
                case.model,case.variant,
                {"cashflows":["-100","230","-132"]},case.config,
                reference_mode=True,
            )
        self.assertEqual(ex.exception.code,"MULTIPLE_IRR_ROOTS")

    def test_reconciled_indirect_cfo_rejects_fabricated_direct_input(self):
        case=self.cases["HC.CASH.05","INDIRECT_CFO_RECONCILED"]
        with self.assertRaises(CalculationError) as ex:
            self.engine.calculate(
                case.model,case.variant,
                {**case.inputs,"directCfo":"101"},case.config,
                reference_mode=True,
            )
        self.assertEqual(ex.exception.code,"CFO_RECONCILIATION_MISMATCH")

    def test_loan_amortization_conservation_each_method(self):
        for variant in (
            "ANNUITY_EQUAL_PAYMENT_DATED","EQUAL_PRINCIPAL_DATED",
            "INTEREST_ONLY_BALLOON","BULLET",
        ):
            case=self.cases["HC.LOAN.02",variant]
            result=self.engine.calculate(
                case.model,case.variant,case.inputs,case.config,
                reference_mode=True,
            )
            rows=result.output["schedule"]
            principal=sum((Decimal(x["principal"]) for x in rows),Decimal(0))
            interest=sum((Decimal(x["interest"]) for x in rows),Decimal(0))
            payment=sum((Decimal(x["payment"]) for x in rows),Decimal(0))
            self.assertEqual(principal,Decimal("1000"))
            self.assertEqual(payment,principal+interest)
            self.assertEqual(Decimal(result.output["closingPrincipal"]),Decimal(0))


if __name__ == "__main__":
    unittest.main()
