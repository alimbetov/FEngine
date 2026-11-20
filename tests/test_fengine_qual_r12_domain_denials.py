"""QUAL-R1.2: one explicit *domain* rejection on every executable HC variant.

These are NOT generic unknown-field/type/S2 probes. They violate real
mathematical domains, source lineage, balances, valuation periods or economics.
The expected error code is precise and subject to continuous CI enforcement.
"""
from __future__ import annotations

import copy
import csv
import unittest
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from qualification_r12_goldens import build_goldens

ROOT=Path(__file__).resolve().parents[1]


def invalid_case(model, variant, inputs, config):
    """Return independently specified invalid domain and exact error code."""
    i,c=copy.deepcopy(inputs),copy.deepcopy(config)
    if model=="HC.ASSET.01":
        c["residualValue"]="999999999"
        return i,c,"INVALID_DEPRECIABLE_BASIS"
    if model=="HC.CAP.01":
        i["beta"]="nonnumeric"
        return i,c,"INVALID_DECIMAL"
    if model=="HC.CAP.02":
        i["equityValue"]="0"
        i["debtValue"]="0"
        return i,c,"INVALID_CAPITAL_WEIGHTS"
    if model=="HC.CASH.03":
        if variant=="DETERMINISTIC_RUNWAY":
            i["cashflows"].append(copy.deepcopy(i["cashflows"][0]))
            return i,c,"CASHFLOW_DATES_NOT_STRICTLY_INCREASING"
        i["scenarios"][1]["scenarioId"]=i["scenarios"][0]["scenarioId"]
        return i,c,"RUNWAY_SCENARIO_ID_INVALID_OR_DUPLICATE"
    if model=="HC.CASH.04":
        i["postings"][0]["amount"]="201"
        # Immutable posted-source SHA is not recomputed, intentionally.
        return i,c,"DIRECT_CFO_SOURCE_DIGEST_MISMATCH"
    if model=="HC.CASH.05":
        if variant=="INDIRECT_CFO_ADJUSTMENT":
            i["noncashAdjustments"].append(copy.deepcopy(i["noncashAdjustments"][0]))
            return i,c,"CFO_DUPLICATE_ADJUSTMENT_CODE"
        i["directCfo"]="101"
        return i,c,"CFO_RECONCILIATION_MISMATCH"
    if model=="HC.COST.04":
        if variant=="SINGLE_PRODUCT_BREAKEVEN":
            i["unitPrice"]=i["unitVariableCost"]
            return i,c,"NONPOSITIVE_CONTRIBUTION_MARGIN"
        i["products"].append(copy.deepcopy(i["products"][0]))
        return i,c,"BREAK_EVEN_DUPLICATE_SKU"
    if model=="HC.COST.05":
        i["annualRates"]=["-1"]
        return i,c,"ESCALATION_RATE_OUT_OF_DOMAIN"
    if model=="HC.COST.07":
        i["actualCost"]="0"
        return i,c,"EVM_ZERO_ACTUAL_COST_CPI_UNDEFINED"
    if model=="HC.COST.08":
        i["rows"][0]["actualUnitCost"]="999"
        # This cannot match immutable source and baseline content SHA.
        return i,c,"PVM_SOURCE_DIGEST_MISMATCH"
    if model=="HC.DCF.01":
        i["discountRate"]="-1"
        return i,c,"RATE_OUT_OF_DOMAIN"
    if model=="HC.DCF.02":
        c["dayCount"]="ACT_360"
        return i,c,"DAY_COUNT_REQUIRED"
    if model=="HC.DCF.03":
        if variant=="ALL_REAL_IRR_ROOTS":
            i["cashflows"]=["-100","110"]
            c["rootDomain"]={"minRate":"0.2","maxRate":"5"}
            return i,c,"NO_IRR_ROOT_IN_DOMAIN"
        i["cashflows"]=["-100","230","-132"]
        return i,c,"MULTIPLE_IRR_ROOTS"
    if model=="HC.DCF.05":
        i["taxRate"]="1.2"
        return i,c,"FCFF_TAX_RATE_OUT_OF_RANGE"
    if model=="HC.DCF.06":
        i["cashCapex"]="51"
        return i,c,"FCFE_SOURCE_DIGEST_MISMATCH"
    if model=="HC.DCF.07":
        i["wacc"]="0.02"
        return i,c,"GORDON_RATE_OR_GROWTH_DOMAIN"
    if model=="HC.DCF.08":
        i["valuationDate"]="2026-11-30"
        return i,c,"EQUITY_VALUATION_DATE_MISMATCH"
    if model=="HC.ECL.02" or model=="HC.ECL.03":
        i["events"][0]["pd"]="1.2"
        return i,c,"ECL_INPUT_OUT_OF_RANGE"
    if model=="HC.LOAN.02":
        i["paymentDates"]=list(reversed(i["paymentDates"]))
        return i,c,"PAYMENT_DATES_NOT_INCREASING"
    if model=="HC.LOAN.03":
        i["cashflows"]=[
            {"date":"2026-01-01","amount":"-100"},
            {"date":"2027-01-01","amount":"120"},
            {"date":"2028-01-01","amount":"-30"},
        ]
        return i,c,"EIR_NONCONVENTIONAL_CASHFLOWS"
    if model=="HC.PF.01":
        i["loanPeriods"]=len(i["cfads"])+1
        return i,c,"LOAN_LIFE_EXCEEDS_PROJECT"
    if model=="HC.RISK.02":
        c["alpha"]="1"
        return i,c,"INVALID_CONFIDENCE"
    if model=="HC.RISK.03":
        c["confidenceAlpha"]="1"
        return i,c,"INVALID_CONFIDENCE"
    if model=="HC.SET.03":
        c["ageingBucketEdges"]=[60,30]
        return i,c,"OVERLAPPING_AGE_BUCKETS"
    if model=="HC.STOCK.01" or model=="HC.STOCK.02":
        i["events"]=[{"date":"2026-01-01","id":"BAD","quantity":"-1"}]
        return i,c,"NEGATIVE_INVENTORY"
    raise AssertionError(f"NO_DOMAIN_NEGATIVE_CASE_FOR_MODEL_{model}")


class QualifiedDomainDenialsR12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=ReferenceEngine(ROOT)
        cls.goldens=build_goldens()

    def test_each_of_48_variants_has_explicit_domain_negative_case(self):
        with (ROOT/"catalog"/"hc_reference_execution_inventory_r1.tsv").open(
            encoding="utf-8",newline=""
        ) as stream:
            inventory=list(csv.DictReader(stream,delimiter="\t"))
        expected={(r["modelCode"],r["variantCode"]) for r in inventory}
        self.assertEqual(len(expected),48)
        self.assertEqual(set(self.goldens),expected)
        for key,case in sorted(self.goldens.items()):
            with self.subTest(model=key[0],variant=key[1]):
                inp,cfg,code=invalid_case(key[0],key[1],case.inputs,case.config)
                self.assertNotEqual((inp,cfg),(case.inputs,case.config))
                self.assertTrue(code and code not in {
                    "FINANCIAL_S2_REQUIRED","UNKNOWN_PARAMETER",
                    "UNCONSUMED_INPUT","BINARY_FLOAT_FORBIDDEN",
                })
                with self.assertRaises(CalculationError) as error:
                    self.engine.calculate(
                        key[0],key[1],inp,cfg,reference_mode=True,
                    )
                self.assertEqual(
                    error.exception.code,code,
                    msg=f"DOMAIN_NEGATIVE_MUST_FAIL_EXACTLY: {key}",
                )


if __name__=="__main__":
    unittest.main()
