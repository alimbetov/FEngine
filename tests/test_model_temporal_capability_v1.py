"""ModelTemporalCapabilityV1: actual HC reference executions → one TASE kernel.

All source values are synthetic. No user data, financial S2, Redis or production
source authority is exercised by this reference suite.
"""
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from fengine_hc.reference import fingerprint
from fengine_hc.r05_cashflow import (
    RECONCILIATION_SHA256, posted_source_sha256, classification_rules_sha256,
)
from fengine_hc.r06_fcfe import cost_of_equity_rate_sha256, fcfe_source_sha256
from tase import TaseError
from tase.model_temporal import (
    ModelTemporalRegistry, ModelTemporalRequest, ModelTemporalRun,
    calculate_model_temporal,
)

ROOT = Path(__file__).resolve().parents[1]
JAN, FEB, MAR, APR = (date(2026, i, 1) for i in (1, 2, 3, 4))
WINDOWS = ((JAN, FEB), (FEB, MAR), (MAR, APR))
SCOPE = "synthetic-user:synthetic-project"
EVM_BASELINE = "a" * 64


def request(model="HC.CASH.05", variant="INDIRECT_CFO_ADJUSTMENT",
            field="cashFlowFromOperations", **overrides):
    fields = {
        "model_code": model,
        "variant_code": variant,
        "output_field": field,
        "scope": SCOPE,
        "start": JAN,
        "end": APR,
        "source_grain": "MONTH",
        "output_grain": "MONTH",
        "currency": "KZT",
        "include_total": True,
        "coverage_attested": True,
        "watermark": APR,
    }
    fields.update(overrides)
    return ModelTemporalRequest(**fields)


def indirect_run(begin, end, value, dims=(), *, source_sha=None):
    src = source_sha or fingerprint({
        "syntheticSource": "income-statement",
        "periodStart": begin.isoformat(),
        "periodEnd": end.isoformat(),
        "value": value,
    })
    inputs = {
        "periodStart": begin.isoformat(),
        "asOf": (end-timedelta(days=1)).isoformat(),
        "currency": "KZT",
        "sourceRevisionSha256": src,
        "netIncome": str(value),
        "noncashAdjustments": [],
        "deltaOperatingNwc": "0",
    }
    config = {
        "netIncomeBasis": "REPORTED_AFTER_TAX_NET_INCOME",
        "noncashAdjustment": "SIGNED_NONCASH_LINES",
        "workingCapitalSign": "INCREASE_OF_NWC_IS_OUTFLOW",
    }
    return ModelTemporalRun(begin, end, inputs, config, src, dims)


def fcff_run(begin, end, *, ebit="200"):
    sha = fingerprint({"syntheticFCFF": begin.isoformat(), "ebit": ebit})
    inputs = {
        "asOf": (end-timedelta(days=1)).isoformat(), "currency": "KZT",
        "sourceRevisionSha256": sha, "ebit": ebit, "taxRate": "0.25",
        "noncashOperatingCharges": "30", "cashCapex": "50",
        "deltaOperatingNwc": "20",
    }
    cfg = {
        "taxPolicy": "EBIT_TIMES_EFFECTIVE_TAX_REFERENCE",
        "capitalExpenditurePolicy": "CASH_CAPEX_POSITIVE_OUTFLOW",
        "workingCapitalBasis": "INCREASE_NWC_IS_OUTFLOW",
    }
    return ModelTemporalRun(begin, end, inputs, cfg, sha)


def fcfe_run(begin, end):
    from fengine_hc.r06_fcfe import POLICY, BASIS
    rate_sha = cost_of_equity_rate_sha256("0.10")
    inputs = {
        "asOf": (end-timedelta(days=1)).isoformat(), "currency": "KZT",
        "costOfEquityRate": "0.10", "costOfEquityRevisionSha256": rate_sha,
        "periodIndex": 1, "cashCapex": "50",
        "grossDebtDrawdowns": "40", "principalRepayments": "15",
        "operatingCashFlowAfterInterest": "110",
    }
    inputs["sourceRevisionSha256"] = fcfe_source_sha256(inputs, "FCFE_LEVERED")
    cfg = {**POLICY, "equityCashflowBasis": BASIS["FCFE_LEVERED"],
           "costOfEquityRef": rate_sha}
    return ModelTemporalRun(begin, end, inputs, cfg, inputs["sourceRevisionSha256"])


def posted_run(begin, end, open_cash="1000", receipt="200", payment="80"):
    rules = [
        {"code": "SALES", "cashflowClass": "OPERATING"},
        {"code": "VENDORS", "cashflowClass": "OPERATING"},
    ]
    post_date = (end - timedelta(days=1)).isoformat()
    postings = [
        {"postingId": "R1", "postingDate": post_date, "amount": receipt,
         "direction": "IN", "classificationCode": "SALES", "transferId": None},
        {"postingId": "P1", "postingDate": post_date, "amount": payment,
         "direction": "OUT", "classificationCode": "VENDORS", "transferId": None},
    ]
    close = Decimal(open_cash) + Decimal(receipt) - Decimal(payment)
    snapshot = {
        "periodStart": begin.isoformat(), "periodEnd": post_date,
        "currency": "KZT", "openingCash": str(open_cash),
        "closingCash": format(close, "f"), "postings": postings,
    }
    sha = posted_source_sha256(snapshot)
    inputs = {**snapshot, "sourceRevisionSha256": sha,
              "classificationRules": rules}
    cfg = {
        "cashClassification": classification_rules_sha256(rules),
        "reconciliationRule": RECONCILIATION_SHA256,
        "periodCutoff": post_date,
        "transferExclusionRule": "BALANCED_INTERNAL_TRANSFER_PAIRS",
        "valueDateVsPostingDate": "POSTING_DATE_ONLY",
    }
    return ModelTemporalRun(begin, end, inputs, cfg, sha)


def evm_run(asof, ev="60", ac="75", baseline=EVM_BASELINE):
    inputs = {
        "asOf": asof.isoformat(), "currency": "KZT",
        "baselineRevision": baseline,
        "plannedValue": "80", "earnedValue": ev,
        "actualCost": ac, "budgetAtCompletion": "120",
    }
    cfg = {"earnedValueRule": "EXTERNALLY_SUPPLIED_EV",
           "eacFormula": "BAC_DIV_CPI"}
    return ModelTemporalRun(asof, None, inputs, cfg, baseline)


class TemporalModelCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelTemporalRegistry.load(ROOT, reference_mode=True)

    def err(self, code, fun):
        with self.assertRaises(TaseError) as error:
            fun()
        self.assertEqual(error.exception.code, code)

    def calculate(self, request_obj, runs, *, registry=None):
        return calculate_model_temporal(
            registry or self.registry, request_obj, runs, reference_mode=True,
        )

    def test_descriptor_catalog_is_strictly_scoped_to_nine_supported_outputs(self):
        self.assertEqual(len(self.registry.capabilities), 9)
        self.assertEqual(len({m for m,v,f in self.registry.capabilities}), 5)
        self.assertEqual(len({(m,v) for m,v,f in self.registry.capabilities}), 9)
        for cap in self.registry.capabilities.values():
            self.assertEqual(len(cap.capability_sha256), 64)
            self.assertEqual(cap.unit_kind, "CURRENCY")
            self.assertEqual(cap.review_status, "PYTHON_REFERENCE_NOT_S2")
            self.assertIn(cap.reducer, ("SUM", "LAST_AS_OF"))
        with self.assertRaises(TypeError):
            self.registry.capabilities[("X","Y","Z")] = "any"

    def test_three_monthly_indirect_cfo_model_executions_and_grand_total(self):
        runs = [indirect_run(start,end,v) for (start,end),v in
                zip(WINDOWS,("100","120","80"))]
        out = self.calculate(request(), runs)
        self.assertEqual([r.value for r in out.result.rows], ["100","120","80"])
        self.assertEqual([r.start for r in out.result.rows], [JAN,FEB,MAR])
        self.assertEqual(out.result.total_rows[0].value, "300")
        self.assertEqual(out.result.total_rows[0].observation_count, 3)
        self.assertEqual(out.result.status, "COMPLETE")
        self.assertEqual(out.execution_class, "PYTHON_REFERENCE_NOT_S2")
        self.assertEqual(len(out.source_output_shas), 3)
        self.assertEqual(len(out.capability_sha256), 64)
        self.assertEqual(len(out.plan_sha256), 64)

    def test_one_quarter_bucket_and_total_from_same_monthly_cfo(self):
        runs = [indirect_run(start,end,v) for (start,end),v in
                zip(WINDOWS,("100","120","80"))]
        out = self.calculate(request(output_grain="QUARTER"),runs)
        self.assertEqual(len(out.result.rows),1)
        self.assertEqual(out.result.rows[0].value,"300")
        self.assertEqual(out.result.total_rows[0].value,"300")

    def test_actual_fcff_model_results_are_summed_without_special_calendar_code(self):
        runs=[fcff_run(start,end) for start,end in WINDOWS]
        out=self.calculate(request("HC.DCF.05","FCFF_UNLEVERED",
                                   "freeCashFlowToFirm"),runs)
        self.assertEqual([Decimal(r.value) for r in out.result.rows], [Decimal("110")]*3)
        self.assertEqual(Decimal(out.result.total_rows[0].value),Decimal("330"))

    def test_actual_fcfe_flow_sums_but_present_value_is_unadmitted(self):
        runs=[fcfe_run(start,end) for start,end in WINDOWS]
        r=request("HC.DCF.06","FCFE_LEVERED","freeCashFlowToEquity")
        out=self.calculate(r,runs)
        self.assertEqual([x.value for x in out.result.rows], ["85","85","85"])
        self.assertEqual(out.result.total_rows[0].value,"255")
        self.err("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:
                 self.calculate(replace(r,output_field="presentValueOfFcfe"),runs))
        self.err("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:
                 self.calculate(request("HC.COST.08","PRICE_VARIANCE","priceVariance"),
                                runs))

    def test_evm_snapshots_use_last_as_of_and_never_sum_eac(self):
        r=request("HC.COST.07","EVM_BAC_CPI","estimateAtCompletion",
                  source_grain="AS_OF")
        runs=[evm_run(date(2026,1,31),ev="60",ac="75"),
              evm_run(date(2026,2,28),ev="80",ac="80"),
              evm_run(date(2026,3,31),ev="100",ac="100")]
        result=self.calculate(r,runs).result
        self.assertEqual([x.value for x in result.rows], ["150","120","120"])
        self.assertEqual(result.total_rows[0].value,"120")
        self.assertNotEqual(result.total_rows[0].value,"390")

    def test_evm_baseline_change_requires_another_qualified_series(self):
        runs=[evm_run(date(2026,1,31)),evm_run(date(2026,2,28),baseline="b"*64)]
        req=request("HC.COST.07","EVM_BAC_CPI","estimateAtCompletion",
                    source_grain="AS_OF",end=MAR)
        self.err("TEMPORAL_EVM_BASELINE_CHANGED",lambda:
                 self.calculate(req,runs))

    def test_direct_cfo_model_executes_and_reconciles_month_to_month_cash(self):
        jan=posted_run(JAN,FEB,open_cash="1000",receipt="200",payment="80")
        feb=posted_run(FEB,MAR,open_cash="1120",receipt="150",payment="50")
        mar=posted_run(MAR,APR,open_cash="1220",receipt="100",payment="30")
        req=request("HC.CASH.04","DIRECT_POSTED_CFO","cashFlowFromOperations")
        out=self.calculate(req,[mar,jan,feb])
        self.assertEqual([r.value for r in out.result.rows],["120","100","70"])
        self.assertEqual(out.result.total_rows[0].value,"290")
        self.assertEqual(len(out.source_output_shas),3)

    def test_direct_cfo_discontinuous_cash_balances_fail(self):
        runs=[posted_run(JAN,FEB,"1000","200","80"),
              posted_run(FEB,MAR,"1000","150","50")]
        req=request("HC.CASH.04","DIRECT_POSTED_CFO","cashFlowFromOperations",
                    end=MAR)
        self.err("TEMPORAL_CASH_BALANCE_DISCONTINUITY",lambda:
                 self.calculate(req,runs))

    def test_cfo_group_by_keeps_branch_totals_separate(self):
        a=(("branch","A"),)
        b=(("branch","B"),)
        runs=[indirect_run(start,end,v,a) for (start,end),v in
              zip(WINDOWS,("100","120","80"))]
        runs += [indirect_run(start,end,v,b) for (start,end),v in
                 zip(WINDOWS,("10","20","30"))]
        out=self.calculate(request(group_by=("branch",)),runs)
        self.assertEqual([r.value for r in out.result.total_rows],["300","60"])
        self.assertEqual([r.group for r in out.result.total_rows],
                         [(("branch","A"),),(("branch","B"),)])

    def test_permutation_invariant_revisions_and_opt_in_totals(self):
        runs=[indirect_run(start,end,v) for (start,end),v in
              zip(WINDOWS,("100","120","80"))]
        r=request()
        a=self.calculate(r,runs)
        b=self.calculate(r,list(reversed(runs)))
        self.assertEqual(a.source_batch_sha256,b.source_batch_sha256)
        self.assertEqual(a.plan_sha256,b.plan_sha256)
        self.assertEqual(a.result_sha256,b.result_sha256)
        no_total=self.calculate(replace(r,include_total=False),runs)
        self.assertEqual(no_total.result.total_rows,())
        self.assertNotEqual(a.plan_sha256,no_total.plan_sha256)

    def test_missing_month_fails_no_false_grand_total(self):
        runs=[indirect_run(JAN,FEB,"100"),indirect_run(MAR,APR,"80")]
        self.err("MISSING_PERIOD_SOURCE",lambda:
                 self.calculate(request(),runs))

    def test_coverage_attestation_and_watermark_required_for_full_flow(self):
        runs=[indirect_run(start,end,v) for (start,end),v in
              zip(WINDOWS,("100","120","80"))]
        self.err("COVERAGE_UNKNOWN",lambda:
                 self.calculate(request(coverage_attested=False),runs))
        self.err("COVERAGE_UNKNOWN",lambda:
                 self.calculate(request(watermark=FEB),runs))
        partial=self.calculate(request(coverage_attested=False,
                                       require_full_coverage=False),runs)
        self.assertEqual(partial.result.status,"PARTIAL")
        self.assertEqual(partial.result.total_rows[0].status,"PARTIAL")

    def test_source_sha_and_currency_cannot_be_replaced_silently(self):
        run=indirect_run(JAN,FEB,"100")
        r=request(end=FEB)
        self.err("TEMPORAL_MODEL_SOURCE_REVISION_MISMATCH",lambda:
                 self.calculate(r,[replace(run,source_window_sha256="c"*64)]))
        self.err("TEMPORAL_MODEL_CURRENCY_MISMATCH",lambda:
                 self.calculate(r,[replace(run,inputs={**run.inputs,"currency":"USD"})]))

    def test_period_binding_rejects_reused_monthly_model_for_wrong_window(self):
        run=indirect_run(JAN,FEB,"100")
        self.err("TEMPORAL_MODEL_WINDOW_BINDING_MISMATCH",lambda:
                 self.calculate(request(end=FEB),[
                     replace(run,inputs={**run.inputs,"periodStart":FEB.isoformat()})
                 ]))
        self.err("TEMPORAL_MODEL_WINDOW_BINDING_MISMATCH",lambda:
                 self.calculate(request(end=FEB),[
                     replace(run,inputs={**run.inputs,"asOf":"2026-02-01"})
                 ]))

    def test_unknown_grain_and_output_cannot_infer_compatibility(self):
        self.err("TEMPORAL_SOURCE_GRAIN_NOT_ALLOWED",lambda:
                 self.calculate(request(source_grain="AS_OF"),
                                [indirect_run(JAN,FEB,"10")]))
        self.err("TEMPORAL_OUTPUT_GRAIN_NOT_ALLOWED",lambda:
                 self.calculate(request(output_grain="CUSTOM_INTERVAL"),
                                [indirect_run(JAN,FEB,"10")]))
        self.err("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:
                 self.calculate(request("HC.DCF.01","PERIOD_END_NPV","npv"),[]))

    def test_invalid_currency_and_date_request_rejected(self):
        self.err("TEMPORAL_CURRENCY_INVALID",lambda:request(currency="kzt"))
        self.err("INVALID_REQUEST_INTERVAL",lambda:request(end=JAN))
        self.err("TEMPORAL_MODEL_DATE_REQUIRED",lambda:request(start="2026-01-01"))
        self.err("INVALID_INCLUDE_TOTAL",lambda:request(include_total="yes"))

    def test_unregistered_model_variant_and_unsafe_tsv_fail_during_loading(self):
        path=ROOT/"catalog"/"model_temporal_capabilities_v1.tsv"
        originals=path.read_text(encoding="utf-8")
        for changed, code in [
            (originals.replace("HC.CASH.04\tDIRECT_POSTED_CFO",
                               "HC.CASH.04\tUNREGISTERED_VARIANT",1),
             "TEMPORAL_CAPABILITY_UNKNOWN_VARIANT"),
            (originals.replace("\tSUM\tDAY,MONTH",
                               "\tLAST_AS_OF\tDAY,MONTH",1),
             "TEMPORAL_CAPABILITY_UNSAFE_REDUCER"),
            (originals.replace("PYTHON_REFERENCE_NOT_S2",
                               "FINANCIAL_S2_APPROVED",1),
             "TEMPORAL_CAPABILITY_UNREVIEWED"),
            (originals.replace("\tCASH_BALANCE_CONTINUITY\t",
                               "\tNONE\t",1),
             "TEMPORAL_CAPABILITY_CONTINUITY_POLICY_MISMATCH"),
        ]:
            with self.subTest(code=code),tempfile.TemporaryDirectory() as directory:
                custom=Path(directory)/"capabilities.tsv"
                custom.write_text(changed,encoding="utf-8")
                self.err(code,lambda:ModelTemporalRegistry.load(
                    ROOT,reference_mode=True,path=custom
                ))

    def test_duplicate_descriptor_and_missing_fields_rejected(self):
        source=(ROOT/"catalog"/"model_temporal_capabilities_v1.tsv").read_text()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"data.tsv"
            path.write_text(source+source.splitlines()[1]+"\n")
            self.err("TEMPORAL_CAPABILITY_DUPLICATE",lambda:
                     ModelTemporalRegistry.load(ROOT,reference_mode=True,path=path))

    def test_unapproved_runtime_rejected_before_model_execution(self):
        runs=[indirect_run(JAN,FEB,"10")]
        self.err("FINANCIAL_S2_REQUIRED",lambda:
                 calculate_model_temporal(self.registry,request(end=FEB),runs))
        self.err("FINANCIAL_S2_REQUIRED",lambda:
                 ModelTemporalRegistry.load(ROOT))

    def test_interval_source_proof_required_for_fcff_and_fcfe(self):
        run=fcff_run(JAN,FEB)
        req=request("HC.DCF.05","FCFF_UNLEVERED","freeCashFlowToFirm",
                    end=FEB,coverage_attested=False)
        self.err("TEMPORAL_MODEL_UNATTESTED_INTERVAL_SOURCE",lambda:
                 self.calculate(req,[run]))
        alt=fcfe_run(JAN,FEB)
        req=request("HC.DCF.06","FCFE_LEVERED","freeCashFlowToEquity",
                    end=FEB,coverage_attested=False)
        self.err("TEMPORAL_MODEL_UNATTESTED_INTERVAL_SOURCE",lambda:
                 self.calculate(req,[alt]))

    def test_one_source_window_must_not_be_double_counted(self):
        run=indirect_run(JAN,FEB,"100")
        self.err("DUPLICATE_OBSERVATION",lambda:
                 self.calculate(request(end=FEB),[run,run]))


if __name__ == "__main__":
    unittest.main()
