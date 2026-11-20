"""Mandatory QUAL-R1 semantic integrity pattern gate.

Not a declaration that all 48 mathematical methods are independently
financially qualified. It requires every currently executable method to
declare test evidence plus risk patterns, and executes adversarial test
transformations against the *shared kernels* used across the methods.

All fixtures are synthetic. No FIN, Redis or Rust.
"""
from __future__ import annotations

import csv
import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import ContractRegistry
from tase import (
    Catalog, Dataset, Observation, PeriodRequest, TaseError, calculate,
    UnifiedModelTemporalRegistry,
)
from qualification_integrity_patterns import (
    PATTERN_IDS, CORE_PATTERNS, required_patterns,
    same_numeric, conserved, rejects_code, same_replay,
    mutation_changes_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
JAN, FEB, MAR, APR = (date(2026, month, 1) for month in (1, 2, 3, 4))
MONTHS = ((JAN, FEB), (FEB, MAR), (MAR, APR))


def row(metric, value, start, end, *, branch="A", cost_centre=None,
        source="a", product="FIN", unit="KZT", oid=""):
    dims = [("branch", branch)]
    if cost_centre is not None:
        dims.append(("costCentre", cost_centre))
    return Observation(
        product=product, metric=metric, scope="synthetic-qual-r1",
        start=start, end=end, value=value, unit=unit,
        source_sha=source * 64, dimensions=tuple(sorted(dims)),
        observation_id=oid,
    )


def data(*observations, attested=True, event=False, watermark=APR):
    return Dataset(
        scope="synthetic-qual-r1", content_sha="b" * 64,
        rows=tuple(observations), interval_coverage_attested=attested,
        complete_event_stream=event, watermark=watermark,
    )


def req(metric="REVENUE", operation="SUM", *,
        grain="MONTH", source_grain="MONTH",
        group_by=(), start=JAN, end=APR,
        include_total=True, require_full_coverage=True,
        product="FIN", **kwargs):
    return PeriodRequest(
        product=product, metric=metric, operation=operation,
        scope="synthetic-qual-r1", start=start, end=end,
        grain=grain, source_grain=source_grain, group_by=group_by,
        include_total=include_total,
        require_full_coverage=require_full_coverage, **kwargs,
    )


def revenue_rows():
    return [row("REVENUE", str(value), start, end)
            for (start, end), value in zip(MONTHS, (100, 120, 80))]


class QualificationIntegrityPatternGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog.load(ROOT, reference_mode=True)

    def run_tase(self, plan, observations, **dataset_kwargs):
        return calculate(self.catalog, plan, data(*observations, **dataset_kwargs))

    def test_48_executable_variants_must_have_explicit_risk_pattern_contract(self):
        inventory = ROOT / "catalog" / "hc_reference_execution_inventory_r1.tsv"
        with inventory.open(encoding="utf-8", newline="") as file:
            records = list(csv.DictReader(file, delimiter="\t"))
        self.assertEqual(len(records), 48)
        self.assertEqual(len({r["modelCode"] for r in records}), 27)
        keys = {(r["modelCode"], r["variantCode"]) for r in records}
        self.assertEqual(len(keys), 48)
        hc = ContractRegistry(ROOT)
        self.assertTrue(keys <= set(hc.variants))
        self.assertEqual(len(hc.models), 116)
        self.assertEqual(len(hc.variants), 222)
        loaded = {}
        for entry in records:
            with self.subTest(key=(entry["modelCode"], entry["variantCode"])):
                self.assertEqual(entry["referenceStatus"], "EXECUTABLE_PYTHON_REFERENCE")
                self.assertEqual(entry["qualificationState"],
                                 "R1_PATTERNS_REQUIRED_REFERENCE_NOT_S2")
                self.assertEqual(entry["financialS2"], "CLOSED")
                named = entry["qualificationPatternIds"].split("|")
                self.assertEqual(len(named), len(set(named)))
                self.assertTrue(set(named) <= PATTERN_IDS)
                self.assertTrue(
                    required_patterns(entry["modelCode"]) <= set(named),
                )
                evidence = entry["existingIndependentTest"]
                self.assertTrue(evidence.startswith("tests/test_"))
                self.assertTrue((ROOT / evidence).is_file())
                if evidence not in loaded:
                    loaded[evidence] = (ROOT / evidence).read_text(encoding="utf-8")
                self.assertIn(entry["variantCode"], loaded[evidence],
                              msg="variant lacks named executable test evidence")
        # This is a manifest-and-test presence gate, not proof that every
        # financial variant has independently validated S2 methodology.

    def test_all_temporal_strategies_have_one_unique_registered_output(self):
        registry = UnifiedModelTemporalRegistry.load(ROOT, reference_mode=True)
        v1 = registry.sum_stock.capabilities
        v11 = registry.model_derived.capabilities
        v12 = registry.dated_weighted_pvm.capabilities
        self.assertEqual((len(v1), len(v11), len(v12)), (9, 4, 5))
        self.assertEqual(len(set(v1) | set(v11) | set(v12)), 18)
        self.assertEqual(len({key[0] for key in set(v1) | set(v11) | set(v12)}), 9)
        self.assertFalse(set(v1) & set(v11))
        self.assertFalse(set(v1) & set(v12))
        self.assertFalse(set(v11) & set(v12))
        self.assertEqual(
            {c.strategy for c in v11.values()},
            {"RECOMPUTE_FROM_COMPONENTS", "RE_EXECUTE_FULL_WINDOW"},
        )
        self.assertEqual(
            {c.strategy for c in v12.values()},
            {"DATED_FULL_WINDOW_REEXECUTE", "EXPOSURE_WEIGHTED_MODEL_RATE",
             "FIXED_BASELINE_LAST_SNAPSHOT"},
        )

    def test_numeric_oracle_and_conservation_helpers_reject_corruption(self):
        same_numeric(Decimal("0.2"), Decimal("20")/Decimal("100"))
        conserved(("140", "160", "-70"), "230")
        with self.assertRaisesRegex(AssertionError, "INDEPENDENT_NUMERIC_ORACLE_MISMATCH"):
            same_numeric("230.01", "230")
        with self.assertRaisesRegex(ValueError, "BINARY_FLOAT_FORBIDDEN"):
            same_numeric(0.1, "0.1")

    def test_valid_monthly_and_daily_total_independent_partition_oracles(self):
        monthly = revenue_rows()
        a = self.run_tase(req(), monthly)
        self.assertEqual(tuple(Decimal(x.value) for x in a.rows),
                         (Decimal(100), Decimal(120), Decimal(80)))
        conserved((x.value for x in a.rows), a.total_rows[0].value)
        same_numeric(a.total_rows[0].value, "300")
        daily = []
        cursor = JAN
        while cursor < MAR:
            day_after = cursor + timedelta(days=1)
            daily.append(row("REVENUE", "1", cursor, day_after))
            cursor = day_after
        b = self.run_tase(req(source_grain="DAY", end=MAR), daily)
        self.assertEqual([Decimal(x.value) for x in b.rows],
                         [Decimal(31), Decimal(28)])
        same_numeric(b.total_rows[0].value, "59")

    def test_result_replay_permutation_and_mutation_receipt(self):
        case = revenue_rows()
        plan = req()
        def calculate_values(rows):
            return self.run_tase(plan, rows)
        same_replay(calculate_values, case, lambda result: result.result_sha)
        changed = [replace(case[0], value="101")] + case[1:]
        mutation_changes_receipt(calculate_values, case, changed,
                                 lambda result: result.result_sha)
        with self.assertRaisesRegex(AssertionError, "SOURCE_MUTATION_NOT_BOUND_TO_RECEIPT"):
            mutation_changes_receipt(calculate_values, case, list(case),
                                     lambda result: result.result_sha)

    def test_partial_mode_overlap_detected_even_without_attestation(self):
        observations = [
            row("REVENUE", "100", JAN, date(2026, 2, 15)),
            row("REVENUE", "150", FEB, MAR, oid="other"),
        ]
        plan = req(grain="QUARTER",source_grain=None,
                   include_total=False, require_full_coverage=False)
        rejects_code(
            lambda: self.run_tase(plan, observations, attested=False),
            "SOURCE_OVERLAP", TaseError,
        )

    def test_full_mode_overlap_is_not_silently_rounded_or_deduplicated(self):
        records = [
            row("REVENUE", "100", JAN, MAR, oid="one"),
            row("REVENUE", "50", FEB, APR, oid="two"),
        ]
        plan = req(grain="QUARTER",source_grain=None,include_total=False)
        rejects_code(
            lambda: self.run_tase(plan, records),
            "SOURCE_OVERLAP", TaseError,
        )

    def test_complete_ungrouped_sum_rejects_vanished_branch(self):
        rows = []
        for start,end in MONTHS:
            rows.append(row("REVENUE","100",start,end,branch="A"))
            if start != FEB:
                rows.append(row("REVENUE","200",start,end,branch="B"))
        rejects_code(
            lambda: self.run_tase(req(),rows),
            "PARTIAL_COHORT_COVERAGE", TaseError,
        )

    def test_complete_grouped_sum_rejects_vanished_cost_centre(self):
        rows = []
        for start,end in MONTHS:
            rows.append(row("REVENUE","100",start,end,branch="A",cost_centre="X"))
            if start != FEB:
                rows.append(row("REVENUE","200",start,end,branch="A",cost_centre="Y"))
        rejects_code(
            lambda: self.run_tase(req(group_by=("branch",)),rows),
            "PARTIAL_COHORT_COVERAGE", TaseError,
        )

    def test_complete_ratio_rejects_vanished_branch_component(self):
        rows = []
        for start,end in MONTHS:
            for branch in ("A","B"):
                rows.append(row("REVENUE","100",start,end,branch=branch))
                if not (branch == "B" and start == FEB):
                    rows.append(row("GROSS_PROFIT","20",start,end,branch=branch))
        rejects_code(
            lambda: self.run_tase(
                req(metric="GROSS_MARGIN",operation="RATIO_OF_SUMS"),rows
            ),
            "PARTIAL_COHORT_COVERAGE", TaseError,
        )

    def test_same_time_different_dim_ratio_is_not_allowed(self):
        rows = []
        for start,end in MONTHS:
            rows.append(row("GROSS_PROFIT","20",start,end,branch="A"))
            rows.append(row("REVENUE","100",start,end,branch="B"))
        rejects_code(
            lambda: self.run_tase(
                req(metric="GROSS_MARGIN",operation="RATIO_OF_SUMS"),rows
            ),
            "COMPONENT_ALIGNMENT", TaseError,
        )

    def test_matched_components_can_roll_up_without_cross_dim_swaps(self):
        records = []
        for start,end in MONTHS:
            for branch, scale in (("A",1),("B",2)):
                records.append(row("REVENUE",str(100*scale),start,end,branch=branch))
                records.append(row("GROSS_PROFIT",str(20*scale),start,end,branch=branch))
        out = self.run_tase(req(metric="GROSS_MARGIN",operation="RATIO_OF_SUMS"),records)
        self.assertEqual([Decimal(r.value) for r in out.rows],
                         [Decimal("0.2")]*3)
        same_numeric(out.total_rows[0].value,"0.2")

    def test_weight_rates_must_match_exposure_by_full_key_and_date(self):
        when1=date(2026,1,15)
        when2=date(2026,2,15)
        rate = row("PORTFOLIO_NOMINAL_RATE","0.1",when1,None,
                   product="BANK",unit="fraction")
        exposure = row("LOAN_OUTSTANDING","100",when2,None,product="BANK")
        plan=req(product="BANK",metric="PORTFOLIO_NOMINAL_RATE",
                 operation="WEIGHTED_MEAN",grain="QUARTER",
                 source_grain="AS_OF")
        rejects_code(
            lambda: self.run_tase(plan,[rate,exposure]),
            "PAIR_ALIGNMENT",TaseError,
        )

    def test_weight_rate_cannot_pair_exposure_from_other_branch(self):
        rate = row("PORTFOLIO_NOMINAL_RATE","0.1",date(2026,1,15),None,
                   product="BANK",unit="fraction",branch="A")
        exposure = row("LOAN_OUTSTANDING","100",date(2026,1,15),None,
                       product="BANK",branch="B")
        plan=req(product="BANK",metric="PORTFOLIO_NOMINAL_RATE",
                 operation="WEIGHTED_MEAN",grain="QUARTER",
                 source_grain="AS_OF")
        rejects_code(
            lambda: self.run_tase(plan,[rate,exposure]),
            "PAIR_ALIGNMENT",TaseError,
        )

    def test_weighted_rate_uses_independent_numeric_oracle(self):
        day1=date(2026,1,15)
        day2=date(2026,2,15)
        observations=[
            row("PORTFOLIO_NOMINAL_RATE","0.1",day1,None,
                product="BANK",unit="fraction"),
            row("LOAN_OUTSTANDING","100",day1,None,product="BANK"),
            row("PORTFOLIO_NOMINAL_RATE","0.2",day2,None,
                product="BANK",unit="fraction"),
            row("LOAN_OUTSTANDING","300",day2,None,product="BANK"),
        ]
        plan=req(product="BANK",metric="PORTFOLIO_NOMINAL_RATE",
                 operation="WEIGHTED_MEAN",grain="QUARTER",
                 source_grain="AS_OF")
        result = self.run_tase(plan,observations)
        same_numeric(result.total_rows[0].value,"0.175")
        self.assertNotEqual(Decimal(result.total_rows[0].value),Decimal("0.15"))

    def test_as_of_stock_complete_result_rejects_vanishing_leaf(self):
        snapshots=[]
        for when in (date(2026,1,31), date(2026,2,28),date(2026,3,31)):
            snapshots.append(row("CASH_BALANCE","100",when,None,branch="A"))
            if when.month != 2:
                snapshots.append(row("CASH_BALANCE","200",when,None,branch="B"))
        rejects_code(
            lambda: self.run_tase(
                req(metric="CASH_BALANCE",operation="LAST_AS_OF",
                    source_grain="AS_OF"),snapshots),
            "PARTIAL_COHORT_COVERAGE",TaseError,
        )

    def test_dimension_split_has_same_grand_total_as_verified_unsplit_flow(self):
        rows=[]
        for start,end in MONTHS:
            rows.extend((
                row("REVENUE","100",start,end,branch="A"),
                row("REVENUE","200",start,end,branch="B"),
            ))
        grouped=self.run_tase(req(group_by=("branch",)),rows)
        ungrouped=self.run_tase(req(),rows)
        conserved((r.value for r in grouped.total_rows),ungrouped.total_rows[0].value)
        same_numeric(ungrouped.total_rows[0].value,"900")

    def test_scope_mismatch_fails_not_empty_or_partial(self):
        rows=revenue_rows()
        altered=replace(rows[0],scope="another-project")
        with self.assertRaises(TaseError) as exc:
            data(altered,*rows[1:])
        self.assertEqual(exc.exception.code,"CROSS_SCOPE_DATASET")

    def test_all_pattern_categories_are_accounted_for_in_ci_gate(self):
        self.assertEqual(len(CORE_PATTERNS), 5)
        used = set()
        for model in {("HC."+part+".01") for part in (
            "ASSET","CAP","CASH","COST","DCF","ECL","LOAN",
            "PF","RISK","SET","STOCK"
        )}:
            used.update(required_patterns(model))
        self.assertEqual(used,PATTERN_IDS)


if __name__ == "__main__":
    unittest.main()
