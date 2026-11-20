"""Temporal V1.2 real HC reference golden arithmetic and explicit denial tests."""
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

from fengine_hc.reference import ReferenceEngine
from fengine_hc.r07_pvm import CONVENTION, pvm_revision_hashes
from tase import (
    TaseError, ModelTemporalRegistryV12, ModelTemporalRunV12,
    ModelTemporalRequest, temporal_v12_source_sha256,
    UnifiedModelTemporalRegistry, calculate_universal_model_temporal,
)

ROOT = Path(__file__).resolve().parents[1]
JAN, FEB, MAR, APR = (date(2026, m, 1) for m in (1, 2, 3, 4))
DIMS = ()
BASELINE_DATE = "2025-12-31"
BASELINE = (
    ("A", "60", "10"),
    ("B", "40", "20"),
)


def request(model, variant, field, **options):
    defaults = {
        "model_code": model, "variant_code": variant, "output_field": field,
        "scope": "synthetic-user:synthetic-project",
        "start": JAN, "end": APR,
        "source_grain": "AS_OF" if model == "HC.COST.08" else "EVENT_AT",
        "output_grain": "MONTH", "currency": "KZT",
        "include_total": True, "coverage_attested": True, "watermark": APR,
    }
    defaults.update(options)
    return ModelTemporalRequest(**defaults)


def run(model, variant, when, inputs, config, *, identifier, group=(),
        currency="KZT", exposure=None):
    sha = temporal_v12_source_sha256(
        model, variant, when, None, currency, inputs, config,
        identifier, group, exposure,
    )
    return ModelTemporalRunV12(
        when, None, currency, inputs, config, sha, identifier, group, exposure,
    )


def dated(when, amount, *, rate="0.1", identifier=None, group=()):
    inp = {
        "cashflows": [{"date": when.isoformat(), "amount": str(amount)}],
        "discountRate": rate, "valuationDate": JAN.isoformat(),
    }
    return run("HC.DCF.02","EXACT_DATE_XNPV",when,inp,
               {"dayCount": "ACT_365_FIXED"},
               identifier=identifier or when.isoformat(),group=group)


def capm(when, beta, weight, *, identifier=None, rf="0.02", premium="0.06",
         group=()):
    inp = {
        "riskFreeRate": rf, "beta": str(beta),
        "marketRiskPremium": premium,
    }
    return run("HC.CAP.01","CAPM_BASE",when,inp,{},identifier=identifier or when.isoformat(),
               group=group,exposure=str(weight))


def pvm(when, *, variant="PRICE_VARIANCE",
        quantities=("50","60"), costs=("11","18"), group=()):
    products = [
        {"sku": sku, "baselineQuantity": q, "actualQuantity": actual_q,
         "baselineUnitCost": c0, "actualUnitCost": actual_c}
        for (sku,q,c0),actual_q,actual_c in zip(BASELINE,quantities,costs)
    ]
    pins = pvm_revision_hashes(
        BASELINE_DATE,when.isoformat(),"KZT","PCS",products
    )
    inp = {
        "baselinePeriod": BASELINE_DATE,
        "actualPeriod": when.isoformat(),
        "currency": "KZT", "quantityUnit": "PCS",
        "rows": products,
        "baselineRevisionSha256": pins["baselineRevisionSha256"],
        "actualRevisionSha256": pins["actualRevisionSha256"],
    }
    cfg = {
        "standardCostVintage": pins["standardCostVintage"],
        "volumeBaseline": pins["volumeBaseline"],
        "interactionAllocation": CONVENTION,
    }
    return run("HC.COST.08",variant,when,inp,cfg,
               identifier=when.isoformat(),group=group)


class TemporalV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = UnifiedModelTemporalRegistry.load(ROOT,reference_mode=True)
        cls.engine = ReferenceEngine(ROOT)

    def calc(self, request_obj, rows):
        return calculate_universal_model_temporal(
            self.registry,request_obj,rows,reference_mode=True
        )

    def rejects(self,code,call):
        with self.assertRaises(TaseError) as context:
            call()
        self.assertEqual(context.exception.code,code)

    def test_five_new_reviewed_descriptors_do_not_authorize_other_methods(self):
        reg=self.registry.dated_weighted_pvm
        self.assertEqual(len(reg.capabilities),5)
        self.assertEqual(len(self.registry.sum_stock.capabilities),9)
        self.assertEqual(len(self.registry.model_derived.capabilities),4)
        self.assertEqual(len(set(reg.capabilities) |
                             set(self.registry.sum_stock.capabilities) |
                             set(self.registry.model_derived.capabilities)),18)
        self.assertEqual(len({key[0] for key in set(reg.capabilities) |
                              set(self.registry.sum_stock.capabilities) |
                              set(self.registry.model_derived.capabilities)}),9)
        with self.assertRaises(TypeError):
            reg.capabilities[("FAKE","FAKE","FAKE")]="inject"

    def test_dated_xnpv_irregular_dates_reexecutes_real_model(self):
        dates=(date(2026,1,1),date(2026,2,1),date(2026,3,15))
        flows=("-100","110","200")
        rows=[dated(when,amt) for when,amt in zip(dates,flows)]
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv")
        result=self.calc(req,rows)
        with localcontext() as ctx:
            ctx.prec=40
            rate=Decimal("1.1")
            origin=JAN
            expected=sum((
                Decimal(value)/(rate ** (Decimal((when-origin).days)/Decimal(365)))
                for when,value in zip(dates,flows)
            ),Decimal(0))
        actual=Decimal(result.result.total_rows[0].value)
        self.assertLess(abs(actual-expected),Decimal("1e-33"))
        self.assertEqual(len(result.result.rows),3)
        self.assertEqual(result.result.total_rows[0].observation_count,3)
        direct=self.engine.calculate(
            "HC.DCF.02","EXACT_DATE_XNPV",
            {"cashflows":[{"date":when.isoformat(),"amount":val}
                          for when,val in zip(dates,flows)],
             "discountRate":"0.1","valuationDate":"2026-01-01"},
            {"dayCount":"ACT_365_FIXED"},reference_mode=True,
        )
        self.assertEqual(Decimal(direct.output["xnpv"]),actual)

    def test_xnpv_daily_and_quarter_views_do_not_change_valuation_origin(self):
        rows=[dated(JAN,"-100"),dated(date(2026,2,1),"110"),
              dated(date(2026,3,15),"200")]
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv",
                    output_grain="QUARTER")
        out=self.calc(req,rows).result
        self.assertEqual(len(out.rows),1)
        self.assertEqual(out.rows[0].value,out.total_rows[0].value)
        self.assertEqual(out.rows[0].observation_count,3)

    def test_xnpv_rate_basis_valuation_date_and_source_sha_guards(self):
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv",end=FEB,
                    watermark=FEB)
        a=dated(JAN,"-100")
        self.rejects("TEMPORAL_V12_SOURCE_REVISION_MISMATCH",
                     lambda:self.calc(req,[replace(a,source_window_sha256="b"*64)]))
        changed=run("HC.DCF.02","EXACT_DATE_XNPV",JAN,
                    {**a.inputs,"valuationDate":"2026-02-01"},a.config,
                    identifier=a.event_id)
        self.rejects("TEMPORAL_V12_VALUATION_ORIGIN_MISMATCH",
                     lambda:self.calc(req,[changed]))
        changed=run("HC.DCF.02","EXACT_DATE_XNPV",JAN,
                    a.inputs,{"dayCount":"ACT_360"},identifier=a.event_id)
        self.rejects("TEMPORAL_V12_DAYCOUNT_NOT_ADMITTED",
                     lambda:self.calc(req,[changed]))

    def test_xnpv_changed_annual_rate_and_incomplete_event_stream_block(self):
        rows=[dated(JAN,"-100",rate="0.1"),
              dated(date(2026,2,1),"110",rate="0.2"),
              dated(date(2026,3,15),"200",rate="0.1")]
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv")
        self.rejects("TEMPORAL_V12_ANNUAL_RATE_MISMATCH",
                     lambda:self.calc(req,rows))
        no_total=replace(req,include_total=False)
        self.rejects("TEMPORAL_V12_ANNUAL_RATE_MISMATCH",
                     lambda:self.calc(no_total,rows))
        self.rejects("COVERAGE_UNKNOWN",lambda:self.calc(
            replace(req,coverage_attested=False),[dated(JAN,"100")]))

    def test_source_batch_hash_changes_when_coverage_watermark_changes(self):
        # A stronger or newer completeness claim is a distinct input snapshot,
        # even if its currently observed financial values remain identical.
        rows=[dated(JAN,"-100")]
        base=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv",
                     end=FEB,watermark=FEB)
        current=self.calc(base,rows)
        amended=self.calc(replace(base,watermark=MAR),rows)
        self.assertEqual(current.result.total_rows[0].value,
                         amended.result.total_rows[0].value)
        self.assertNotEqual(current.source_batch_sha256,
                            amended.source_batch_sha256)
        self.assertNotEqual(current.result_sha256,amended.result_sha256)

    def test_xnpv_multiple_events_same_date_need_distinct_ids(self):
        a=dated(JAN,"-100",identifier="A")
        b=dated(JAN,"50",identifier="B")
        rows=[a,b,dated(date(2026,2,1),"100")]
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv",
                    end=MAR,watermark=MAR)
        result=self.calc(req,rows)
        self.assertEqual(result.result.total_rows[0].observation_count,3)
        self.rejects("TEMPORAL_V12_DUPLICATE_SOURCE_EVENT",
                     lambda:self.calc(req,[a,a]))

    def test_capm_unequal_exposure_weight_not_simple_rate_mean(self):
        rows=[
            capm(date(2026,1,15),"1","100"),
            capm(date(2026,2,15),"2","300"),
            capm(date(2026,3,15),"1.5","100"),
        ]
        req=request("HC.CAP.01","CAPM_BASE","costOfEquity")
        result=self.calc(req,rows)
        self.assertEqual([Decimal(x.value) for x in result.result.rows],
                         [Decimal("0.08"),Decimal("0.14"),Decimal("0.11")])
        self.assertEqual(Decimal(result.result.total_rows[0].value),
                         Decimal("0.122"))
        self.assertNotEqual(Decimal(result.result.total_rows[0].value),
                            Decimal("0.11"))
        self.assertEqual(result.result.total_rows[0].unit,"fraction")

    def test_capm_exposure_weighting_keeps_business_dimension_groups_separate(self):
        a=(("branch","A"),)
        b=(("branch","B"),)
        rows=[
            capm(date(2026,1,15),"1","100",group=a),
            capm(date(2026,2,15),"2","300",group=a),
            capm(date(2026,3,15),"1.5","100",group=a),
            capm(date(2026,1,15),"0.5","50",group=b),
            capm(date(2026,2,15),"0.5","50",group=b),
            capm(date(2026,3,15),"0.5","50",group=b),
        ]
        req=request("HC.CAP.01","CAPM_BASE","costOfEquity",
                    group_by=("branch",))
        result=self.calc(req,rows).result
        self.assertEqual([row.group for row in result.total_rows],[a,b])
        self.assertEqual([Decimal(row.value) for row in result.total_rows],
                         [Decimal("0.122"),Decimal("0.05")])

    def test_capm_weights_zero_and_basis_change_fail(self):
        req=request("HC.CAP.01","CAPM_BASE","costOfEquity")
        rows=[
            capm(date(2026,1,15),"1","0"),
            capm(date(2026,2,15),"2","0"),
            capm(date(2026,3,15),"1.5","0"),
        ]
        self.rejects("ZERO_TOTAL_WEIGHT",lambda:self.calc(req,rows))
        rows=[capm(date(2026,1,15),"1","100"),
              capm(date(2026,2,15),"2","300",premium="0.07"),
              capm(date(2026,3,15),"1.5","100")]
        self.rejects("TEMPORAL_V12_RATE_BASIS_CHANGED",
                     lambda:self.calc(req,rows))

    def test_capm_negative_weight_float_and_duplicate_rate_date_rejected(self):
        req=request("HC.CAP.01","CAPM_BASE","costOfEquity",
                    end=FEB,watermark=FEB)
        self.rejects("NEGATIVE_WEIGHT",lambda:
                     self.calc(req,[capm(date(2026,1,15),"1","-1")]))
        a=capm(date(2026,1,15),"1","100",identifier="A")
        b=capm(date(2026,1,15),"2","200",identifier="B")
        self.rejects("TEMPORAL_V12_WEIGHT_PAIR_DUPLICATE",lambda:
                     self.calc(req,[a,b]))
        from fengine_hc.reference import CalculationError
        with self.assertRaises(CalculationError) as error:
            run("HC.CAP.01","CAPM_BASE",date(2026,1,15),
                a.inputs,a.config,identifier=a.event_id,exposure=100.0)
        self.assertEqual(error.exception.code,"BINARY_FLOAT_FORBIDDEN")

    def test_pvm_price_volume_mix_three_fixed_baseline_snapshots(self):
        dates=(date(2026,1,31),date(2026,2,28),date(2026,3,31))
        specs=[
            (("50","60"),("11","18")),
            (("55","65"),("12","17")),
            (("60","70"),("11","19")),
        ]
        for variant, field, expected in (
            ("PRICE_VARIANCE","priceVariance",("-70","-85","-10")),
            ("QUANTITY_VARIANCE","quantityVariance",("140","280","420")),
            ("MIX_VARIANCE","mixVariance",("160","170","180")),
        ):
            with self.subTest(variant=variant):
                rows=[pvm(when,variant=variant,quantities=q,costs=c)
                      for when,(q,c) in zip(dates,specs)]
                req=request("HC.COST.08",variant,field)
                out=self.calc(req,rows).result
                self.assertEqual([Decimal(x.value) for x in out.rows],
                                 [Decimal(x) for x in expected])
                self.assertEqual(Decimal(out.total_rows[0].value),
                                 Decimal(expected[-1]))
                self.assertNotEqual(Decimal(out.total_rows[0].value),
                                    sum((Decimal(x) for x in expected),Decimal(0)))

    def test_pvm_baseline_mutation_and_snapshot_date_rejected(self):
        dates=(date(2026,1,31),date(2026,2,28),date(2026,3,31))
        rows=[
            pvm(dates[0]),pvm(dates[1],quantities=("55","65"),costs=("12","17")),
            pvm(dates[2],quantities=("60","70"),costs=("11","19")),
        ]
        req=request("HC.COST.08","PRICE_VARIANCE","priceVariance")
        changed=rows[1]
        new_baseline=[dict(r) for r in changed.inputs["rows"]]
        new_baseline[0]["baselineUnitCost"]="9"
        pins=pvm_revision_hashes(
            BASELINE_DATE,dates[1].isoformat(),"KZT","PCS",new_baseline,
        )
        changed_inputs={
            **changed.inputs,"rows":new_baseline,
            "baselineRevisionSha256":pins["baselineRevisionSha256"],
            "actualRevisionSha256":pins["actualRevisionSha256"],
        }
        changed_config={**changed.config,
                        "standardCostVintage":pins["standardCostVintage"]}
        modified=run("HC.COST.08","PRICE_VARIANCE",dates[1],
                     changed_inputs,changed_config,identifier=changed.event_id)
        self.rejects("TEMPORAL_V12_PVM_BASELINE_CHANGED",lambda:
                     self.calc(req,[rows[0],modified,rows[2]]))
        misdate=run("HC.COST.08","PRICE_VARIANCE",dates[0],
                    {**rows[0].inputs,"actualPeriod":"2026-02-01"},
                    rows[0].config,identifier=rows[0].event_id)
        self.rejects("TEMPORAL_V12_PVM_SNAPSHOT_DATE_MISMATCH",lambda:
                     self.calc(req,[misdate]))

    def test_pvm_missing_month_and_wrong_currency_not_hidden(self):
        req=request("HC.COST.08","PRICE_VARIANCE","priceVariance")
        rows=[pvm(date(2026,1,31)),pvm(date(2026,3,31))]
        self.rejects("MISSING_SNAPSHOT",lambda:self.calc(req,rows))
        wrong=pvm(date(2026,1,31))
        changed=run("HC.COST.08","PRICE_VARIANCE",wrong.start,
                    wrong.inputs,wrong.config,
                    identifier=wrong.event_id,currency="USD")
        self.rejects("TEMPORAL_MODEL_CURRENCY_MISMATCH",lambda:
                     self.calc(req,[changed]))

    def test_fail_closed_on_unsupported_source_grain_and_catalog_method(self):
        row=dated(JAN,"-100")
        req=request("HC.DCF.02","APPROVED_DAYCOUNT_XNPV","xnpv",
                    end=FEB,watermark=FEB)
        self.rejects("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:self.calc(req,[row]))
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv",
                    source_grain="MONTH",end=FEB,watermark=FEB)
        self.rejects("TEMPORAL_SOURCE_GRAIN_NOT_ALLOWED",lambda:self.calc(req,[row]))
        req=request("HC.COST.08","PRICE_VARIANCE","priceVariance",
                    output_grain="DAY")
        self.rejects("TEMPORAL_OUTPUT_GRAIN_NOT_ALLOWED",lambda:
                     self.calc(req,[pvm(date(2026,1,31))]))

    def test_v12_registry_loader_rejects_unaudited_changes(self):
        raw=(ROOT/"catalog"/"model_temporal_capabilities_v12.tsv").read_text()
        for old,new,code in (
            ("\tDATED_FULL_WINDOW_REEXECUTE\t",
             "\tSUM\t","TEMPORAL_V12_POLICY_NOT_REVIEWED"),
            ("\tPYTHON_REFERENCE_NOT_S2",
             "\tFINANCIAL_S2_APPROVED","TEMPORAL_V12_UNREVIEWED"),
            ("HC.DCF.02\tEXACT_DATE_XNPV",
             "HC.DCF.02\tUNKNOWN_XNPV","TEMPORAL_V12_UNKNOWN_VARIANT"),
        ):
            with self.subTest(code=code),tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/"variants.tsv"
                path.write_text(raw.replace(old,new,1))
                self.rejects(code,lambda:ModelTemporalRegistryV12.load(
                    ROOT,reference_mode=True,path=path
                ))

    def test_reference_only_and_dispatch_mismatch_rejected(self):
        req=request("HC.DCF.02","EXACT_DATE_XNPV","xnpv",
                    end=FEB,watermark=FEB)
        rows=[dated(JAN,"-100")]
        self.rejects("FINANCIAL_S2_REQUIRED",lambda:
                     calculate_universal_model_temporal(self.registry,req,rows))
        self.rejects("TEMPORAL_INPUT_CONTRACT_MISMATCH",lambda:
                     self.calc(req,[object()]))
        self.rejects("FINANCIAL_S2_REQUIRED",lambda:
                     ModelTemporalRegistryV12.load(ROOT))


if __name__ == "__main__":
    unittest.main()
