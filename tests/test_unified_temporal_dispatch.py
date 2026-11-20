"""Unified temporal model API accepts all reviewed reducers, never caller guesses."""
from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from tase import (
    TaseError, UnifiedModelTemporalRegistry, calculate_universal_model_temporal,
)
from test_model_temporal_capability_v1 import (
    JAN, FEB, MAR, APR, WINDOWS, request as v1_request, indirect_run,
)
from test_model_temporal_capability_v11 import (
    request as v11_request, evm, npv,
)

ROOT = Path(__file__).resolve().parents[1]


class UnifiedTemporalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = UnifiedModelTemporalRegistry.load(
            ROOT, reference_mode=True,
        )

    def dispatch(self, req, runs):
        return calculate_universal_model_temporal(
            self.registry,req,runs,reference_mode=True,
        )

    def rejects(self, code, action):
        with self.assertRaises(TaseError) as error:
            action()
        self.assertEqual(error.exception.code,code)

    def test_thirteen_reviewed_outputs_and_no_automatic_catalogue_admission(self):
        self.assertEqual(len(self.registry.sum_stock.capabilities),9)
        self.assertEqual(len(self.registry.model_derived.capabilities),4)
        self.assertEqual(len(set(self.registry.sum_stock.capabilities) |
                             set(self.registry.model_derived.capabilities)),13)

    def test_v1_additive_cfo_flows_use_same_unified_interface(self):
        rows=[indirect_run(a,b,v) for (a,b),v in
              zip(WINDOWS,("100","120","80"))]
        result=self.dispatch(v1_request(),rows)
        self.assertEqual([Decimal(r.value) for r in result.result.rows],
                         [Decimal(100),Decimal(120),Decimal(80)])
        self.assertEqual(Decimal(result.result.total_rows[0].value),Decimal(300))

    def test_v11_cpi_recomputed_without_averaging_cpi(self):
        req=v11_request("HC.COST.07","EVM_BAC_CPI","costPerformanceIndex",
                        end=MAR)
        items=[evm(date(2026,1,31),"60","75"),
               evm(date(2026,2,28),"80","100")]
        actual=self.dispatch(req,items)
        self.assertEqual([Decimal(r.value) for r in actual.result.rows],
                         [Decimal("0.8"),Decimal("0.8")])
        self.assertEqual(Decimal(actual.result.total_rows[0].value),Decimal("0.8"))

    def test_v11_npv_full_window_recomputed_via_shared_entrypoint(self):
        req=v11_request("HC.DCF.01","PERIOD_END_NPV","npv")
        rows=[npv(a,b,x) for (a,b),x in zip(WINDOWS,("-100","121","121"))]
        output=self.dispatch(req,rows)
        self.assertEqual(Decimal(output.result.total_rows[0].value),Decimal(110))
        self.assertEqual([Decimal(r.value) for r in output.result.rows],
                         [Decimal(-100),Decimal(121),Decimal(121)])

    def test_v1_inputs_cannot_be_submitted_to_v11_or_reverse(self):
        req=v11_request("HC.DCF.01","PERIOD_END_NPV","npv",end=FEB)
        self.rejects("TEMPORAL_INPUT_CONTRACT_MISMATCH",lambda:
                     self.dispatch(req,[indirect_run(JAN,FEB,"1")]))
        req=v1_request(end=FEB)
        self.rejects("TEMPORAL_INPUT_CONTRACT_MISMATCH",lambda:
                     self.dispatch(req,[npv(JAN,FEB,"1")]))

    def test_unknown_field_not_automatically_approved(self):
        req=v11_request("HC.DCF.01","PERIOD_END_NPV","cashflow",
                        end=FEB)
        self.rejects("TEMPORAL_CAPABILITY_NOT_ADMITTED",lambda:
                     self.dispatch(req,[npv(JAN,FEB,"1")]))

    def test_default_refuses_financial_admission(self):
        req=v1_request(end=FEB)
        self.rejects("FINANCIAL_S2_REQUIRED",lambda:
                     calculate_universal_model_temporal(
                         self.registry,req,[indirect_run(JAN,FEB,"1")]
                     ))
        self.rejects("FINANCIAL_S2_REQUIRED",lambda:
                     UnifiedModelTemporalRegistry.load(ROOT))


if __name__ == "__main__":
    unittest.main()
