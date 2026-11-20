"""HC Temporal V1.1: component ratios and full-window model reruns, with goldens."""
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

from fengine_hc.reference import ReferenceEngine, number
from tase import TaseError
from tase.model_temporal import ModelTemporalRequest
from tase.model_temporal_v11 import (
    ModelTemporalRegistryV11, ModelTemporalRunV11,
    temporal_v11_source_sha256, calculate_model_temporal_v11,
)

ROOT = Path(__file__).resolve().parents[1]
JAN, FEB, MAR, APR = (date(2026, m, 1) for m in (1,2,3,4))
PERIODS = ((JAN, FEB),(FEB,MAR),(MAR,APR))
BASELINE = "a" * 64
SCOPE = "synthetic:project:temporal-v11"


def request(model, variant, field, **kwargs):
    options = {
        "model_code": model, "variant_code": variant,
        "output_field": field, "scope": SCOPE,
        "start": JAN, "end": APR,
        "source_grain": "AS_OF" if model == "HC.COST.07" else "MONTH",
        "output_grain": "MONTH", "currency": "KZT",
        "include_total": True, "coverage_attested": True, "watermark": APR,
    }
    options.update(kwargs)
    return ModelTemporalRequest(**options)


def run(model, variant, start, end, inputs, config, dims=(), *, currency="KZT"):
    sha = temporal_v11_source_sha256(
        model, variant, start, end, currency, inputs, config, dims,
    )
    return ModelTemporalRunV11(
        start, end, currency, inputs, config, sha, dims,
    )


def evm(as_of, earned, actual, variant="EVM_BAC_CPI", *, baseline=BASELINE,
        dims=()):
    inp = {
        "asOf": as_of.isoformat(), "currency": "KZT",
        "baselineRevision": baseline, "plannedValue": "80",
        "earnedValue": str(earned), "actualCost": str(actual),
        "budgetAtCompletion": "120",
    }
    config = {
        "earnedValueRule": "EXTERNALLY_SUPPLIED_EV",
        "eacFormula": "BAC_DIV_CPI" if variant == "EVM_BAC_CPI"
                     else "AC_PLUS_REMAINING_AT_BUDGET",
    }
    return run("HC.COST.07",variant,as_of,None,inp,config,dims)


def npv(begin, end, amount, rate="0.1", *, variant="PERIOD_END_NPV",
        dims=(), currency="KZT"):
    inp = {"cashflows": [str(amount)], "discountRate": rate}
    cfg = {"timingConvention": "MIDPERIOD" if variant=="MIDPERIOD_NPV"
           else "PERIOD_END"}
    return run("HC.DCF.01",variant,begin,end,inp,cfg,dims,currency=currency)


class TemporalV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelTemporalRegistryV11.load(ROOT,reference_mode=True)
        cls.engine = ReferenceEngine(ROOT)

    def calculate(self, req, runs):
        return calculate_model_temporal_v11(
            self.registry,req,runs,reference_mode=True,
        )

    def rejects(self, code, fun):
        with self.assertRaises(TaseError) as exc:
            fun()
        self.assertEqual(exc.exception.code,code)

    def test_four_reviewed_capabilities_and_immutable_registry(self):
        self.assertEqual(len(self.registry.capabilities),4)
        self.assertEqual({c.strategy for c in self.registry.capabilities.values()},
                         {"RECOMPUTE_FROM_COMPONENTS","RE_EXECUTE_FULL_WINDOW"})
        for cap in self.registry.capabilities.values():
            self.assertEqual(len(cap.revision_sha256),64)
        with self.assertRaises(TypeError):
            self.registry.capabilities[("X","Y","Z")] = "bad"

    def test_evm_cpi_recomputed_from_latest_source_components_not_monthly_average(self):
        req=request("HC.COST.07","EVM_BAC_CPI","costPerformanceIndex")
        inputs=[
            evm(date(2026,1,31),"60","75"),
            evm(date(2026,2,28),"80","80"),
            evm(date(2026,3,31),"100","200"),
        ]
        output=self.calculate(req,inputs)
        self.assertEqual([Decimal(r.value) for r in output.result.rows],
                         [Decimal("0.8"),Decimal("1"),Decimal("0.5")])
        self.assertEqual(Decimal(output.result.total_rows[0].value),Decimal("0.5"))
        self.assertNotEqual(Decimal(output.result.total_rows[0].value),
                            (Decimal("0.8")+Decimal("1")+Decimal("0.5"))/3)
        self.assertEqual(output.result.total_rows[0].unit,"fraction")
        self.assertEqual(output.result.status,"COMPLETE")
        self.assertEqual(len(output.source_output_shas),3)

    def test_second_evm_forecast_variant_recomputes_cpi_same_way(self):
        req=request("HC.COST.07","EVM_EAC_FORECAST","costPerformanceIndex")
        inputs=[
            evm(date(2026,1,31),"60","75","EVM_EAC_FORECAST"),
            evm(date(2026,2,28),"80","100","EVM_EAC_FORECAST"),
            evm(date(2026,3,31),"120","150","EVM_EAC_FORECAST"),
        ]
        output=self.calculate(req,inputs)
        self.assertEqual([Decimal(x.value) for x in output.result.rows],
                         [Decimal("0.8")]*3)
        self.assertEqual(Decimal(output.result.total_rows[0].value),Decimal("0.8"))

    def test_evm_cpi_zero_actual_cost_is_rejected_not_faked(self):
        req=request("HC.COST.07","EVM_BAC_CPI","costPerformanceIndex",
                    end=FEB)
        data=[evm(date(2026,1,31),"60","0")]
        with self.assertRaises(Exception) as context:
            self.calculate(req,data)
        self.assertIn("EVM_ZERO_ACTUAL_COST_CPI_UNDEFINED",str(context.exception))

    def test_evm_baseline_change_fails_across_months(self):
        req=request("HC.COST.07","EVM_BAC_CPI","costPerformanceIndex",
                    end=MAR)
        data=[evm(date(2026,1,31),"60","75"),
              evm(date(2026,2,28),"80","100",baseline="b"*64)]
        self.rejects("TEMPORAL_EVM_BASELINE_CHANGED",
                     lambda:self.calculate(req,data))

    def test_evm_staleness_and_missing_snapshot_not_hidden(self):
        req=request("HC.COST.07","EVM_BAC_CPI","costPerformanceIndex")
        data=[evm(date(2026,1,31),"60","75"),
              evm(date(2026,2,28),"80","100")]
        self.rejects("MISSING_SNAPSHOT",lambda:self.calculate(req,data))

    def test_evm_grouping_and_full_range_ratio_by_branch(self):
        req=request("HC.COST.07","EVM_BAC_CPI","costPerformanceIndex",
                    group_by=("branch",),end=MAR)
        a=(("branch","A"),);b=(("branch","B"),)
        rows=[
            evm(date(2026,1,31),"60","75",dims=a),
            evm(date(2026,2,28),"80","100",dims=a),
            evm(date(2026,1,31),"20","50",dims=b),
            evm(date(2026,2,28),"40","50",dims=b),
        ]
        result=self.calculate(req,rows).result
        self.assertEqual([x.group for x in result.total_rows],[a,b])
        self.assertEqual([Decimal(x.value) for x in result.total_rows],
                         [Decimal("0.8"),Decimal("0.8")])

    def test_simple_three_month_npv_is_not_sum_of_independent_month_npvs(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv")
        data=[npv(a,b,x) for (a,b),x in zip(PERIODS,("-100","121","121"))]
        output=self.calculate(req,data)
        self.assertEqual([Decimal(r.value) for r in output.result.rows],
                         [Decimal(-100),Decimal(121),Decimal(121)])
        self.assertEqual(len(output.result.total_rows),1)
        with localcontext() as ctx:
            ctx.prec=40
            expected=Decimal("-100") + Decimal("121")/Decimal("1.1") + (
                Decimal("121")/Decimal("1.1")**2)
        actual=Decimal(output.result.total_rows[0].value)
        self.assertLess(abs(actual-expected),Decimal("1e-34"))
        self.assertNotEqual(actual,Decimal(142))
        self.assertEqual(output.result.total_rows[0].observation_count,3)
        independent=self.engine.calculate("HC.DCF.01","PERIOD_END_NPV",
                    {"cashflows":["-100","121","121"],"discountRate":"0.1"},
                    {"timingConvention":"PERIOD_END"},reference_mode=True)
        self.assertEqual(actual,Decimal(independent.output["npv"]))

    def test_output_quarter_uses_actual_model_on_all_three_months(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",
                    output_grain="QUARTER")
        data=[npv(a,b,x) for (a,b),x in zip(PERIODS,("-100","121","121"))]
        result=self.calculate(req,data).result
        self.assertEqual(len(result.rows),1)
        self.assertEqual(result.rows[0].value,result.total_rows[0].value)
        self.assertEqual(result.rows[0].observation_count,3)

    def test_midperiod_npv_preserves_different_timing_semantics(self):
        data=[npv(a,b,x,variant="MIDPERIOD_NPV") for (a,b),x
              in zip(PERIODS,("-100","121","121"))]
        req=request("HC.DCF.01","MIDPERIOD_NPV","npv")
        result=self.calculate(req,data)
        expected=self.engine.calculate("HC.DCF.01","MIDPERIOD_NPV",
                    {"cashflows":["-100","121","121"],"discountRate":"0.1"},
                    {"timingConvention":"MIDPERIOD"},reference_mode=True)
        self.assertEqual(Decimal(result.result.total_rows[0].value),
                         Decimal(expected.output["npv"]))

    def test_full_window_rate_mismatch_fails_instead_of_guessing_repricing(self):
        data=[npv(JAN,FEB,"-100","0.1"),
              npv(FEB,MAR,"121","0.2"),
              npv(MAR,APR,"121","0.1")]
        req=request("HC.DCF.01","PERIOD_END_NPV","npv")
        self.rejects("TEMPORAL_V11_DISCOUNT_RATE_MISMATCH",
                     lambda:self.calculate(req,data))

    def test_mixed_period_rate_is_rejected_even_when_total_is_disabled(self):
        data=[npv(JAN,FEB,"-100","0.1"),
              npv(FEB,MAR,"121","0.2")]
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",
                    end=MAR,include_total=False)
        self.rejects("TEMPORAL_V11_DISCOUNT_RATE_MISMATCH",
                     lambda:self.calculate(req,data))

    def test_npv_rejects_missing_month_and_double_entry(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv")
        data=[npv(JAN,FEB,"-100"),npv(MAR,APR,"121")]
        with self.assertRaises(TaseError):
            self.calculate(req,data)
        bad=[npv(a,b,x) for (a,b),x in zip(PERIODS,("-100","121","121"))]
        with self.assertRaises(TaseError):
            self.calculate(req,bad+[bad[0]])

    def test_month_source_cannot_be_treated_as_daily_or_annual(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",
                    source_grain="DAY")
        self.rejects("TEMPORAL_SOURCE_GRAIN_NOT_ALLOWED",lambda:
                     self.calculate(req,[npv(JAN,FEB,"1")]))
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",
                    output_grain="DAY")
        self.rejects("TEMPORAL_OUTPUT_GRAIN_NOT_ALLOWED",lambda:
                     self.calculate(req,[npv(JAN,FEB,"1")]))

    def test_rate_and_timing_are_exactly_pinned(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",end=FEB)
        bad=npv(JAN,FEB,"10")
        altered=replace(bad,config={"timingConvention":"MIDPERIOD"})
        self.rejects("TEMPORAL_V11_SOURCE_REVISION_MISMATCH",lambda:
                     self.calculate(req,[altered]))
        altered=run("HC.DCF.01","PERIOD_END_NPV",JAN,FEB,
                    bad.inputs,{"timingConvention":"MIDPERIOD"})
        self.rejects("TEMPORAL_V11_TIMING_POLICY_MISMATCH",lambda:
                     self.calculate(req,[altered]))

    def test_one_flow_per_source_month_only_and_positive_period(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",end=FEB)
        bad=npv(JAN,FEB,"10")
        source=run("HC.DCF.01","PERIOD_END_NPV",JAN,FEB,
                   {"cashflows":["10","20"],"discountRate":"0.1"},bad.config)
        self.rejects("TEMPORAL_V11_ONE_FLOW_PER_PERIOD_REQUIRED",lambda:
                     self.calculate(req,[source]))
        bad=run("HC.DCF.01","PERIOD_END_NPV",JAN,date(2026,1,31),
                bad.inputs,bad.config)
        self.rejects("TEMPORAL_V11_SOURCE_MONTH_REQUIRED",lambda:
                     self.calculate(req,[bad]))

    def test_source_input_mutation_currency_dimensions_and_provenance_fail(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",end=FEB)
        entry=npv(JAN,FEB,"10")
        self.rejects("TEMPORAL_V11_SOURCE_REVISION_MISMATCH",lambda:
                     self.calculate(req,[replace(entry,
                                                  inputs={"cashflows":["20"],
                                                          "discountRate":"0.1"})]))
        source=run("HC.DCF.01","PERIOD_END_NPV",JAN,FEB,
                   entry.inputs,entry.config,currency="USD")
        self.rejects("TEMPORAL_MODEL_CURRENCY_MISMATCH",lambda:
                     self.calculate(req,[source]))
        source=run("HC.DCF.01","PERIOD_END_NPV",JAN,FEB,
                   entry.inputs,entry.config,dims=(("branch","A"),))
        self.rejects("TEMPORAL_V11_DIMENSION_MISMATCH",lambda:
                     self.calculate(req,[source]))

    def test_unknown_nonlinear_operators_and_blind_sum_are_not_admitted(self):
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv")
        self.rejects("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:
                     self.calculate(req,[npv(JAN,FEB,"10")]))
        req=request("HC.COST.08","PRICE_VARIANCE","priceVariance")
        self.rejects("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:
                     self.calculate(req,[npv(JAN,FEB,"10")]))
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",end=FEB)
        self.assertFalse(hasattr(self.registry.resolve(req),"reducer"))

    def test_coverage_required_and_no_fabricated_total(self):
        data=[npv(a,b,x) for (a,b),x in zip(PERIODS,("-100","121","121"))]
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",
                    coverage_attested=False)
        self.rejects("COVERAGE_UNKNOWN",lambda:self.calculate(req,data))
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",watermark=MAR)
        self.rejects("COVERAGE_UNKNOWN",lambda:self.calculate(req,data))

    def test_optional_total_not_calculated_and_result_sha_changes(self):
        data=[npv(a,b,x) for (a,b),x in zip(PERIODS,("-100","121","121"))]
        req=request("HC.DCF.01","PERIOD_END_NPV","npv")
        with_total=self.calculate(req,data)
        without_total=self.calculate(replace(req,include_total=False),data)
        self.assertEqual(without_total.result.total_rows,())
        self.assertNotEqual(with_total.result_sha256,without_total.result_sha256)

    def test_permutation_invariant_source_and_result_receipts(self):
        data=[npv(a,b,x) for (a,b),x in zip(PERIODS,("-100","121","121"))]
        req=request("HC.DCF.01","PERIOD_END_NPV","npv")
        first=self.calculate(req,data)
        second=self.calculate(req,list(reversed(data)))
        self.assertEqual(first.source_batch_sha256,second.source_batch_sha256)
        self.assertEqual(first.result_sha256,second.result_sha256)

    def test_unreviewed_config_or_method_cannot_be_registered(self):
        path=ROOT/"catalog"/"model_temporal_capabilities_v11.tsv"
        original=path.read_text(encoding="utf-8")
        cases=[
            (original.replace("\tRECOMPUTE_FROM_COMPONENTS\t",
                              "\tSUM\t",1),
             "TEMPORAL_V11_POLICY_NOT_REVIEWED"),
            (original.replace("\tPYTHON_REFERENCE_NOT_S2",
                              "\tFINANCIAL_S2_APPROVED",1),
             "TEMPORAL_V11_UNREVIEWED"),
            (original.replace("HC.DCF.01\tPERIOD_END_NPV",
                              "HC.DCF.01\tFAKE_UNREGISTERED_NPV",1),
             "TEMPORAL_V11_UNKNOWN_VARIANT"),
        ]
        for value,error in cases:
            with self.subTest(error=error),tempfile.TemporaryDirectory() as d:
                f=Path(d)/"changed.tsv"
                f.write_text(value,encoding="utf-8")
                self.rejects(error,lambda:ModelTemporalRegistryV11.load(
                    ROOT,reference_mode=True,path=f))

    def test_reference_mode_only_and_no_financial_s2(self):
        req=request("HC.DCF.01","PERIOD_END_NPV","npv",end=FEB)
        self.rejects("FINANCIAL_S2_REQUIRED",lambda:
                     calculate_model_temporal_v11(self.registry,req,[npv(JAN,FEB,"1")]))
        self.rejects("FINANCIAL_S2_REQUIRED",lambda:
                     ModelTemporalRegistryV11.load(ROOT))


if __name__ == "__main__":
    unittest.main()
