"""QUAL-R1.4 deterministic cross-ledger PVM and inventory conservation.

Each property case uses a seeded synthetic identity and separately derived
Decimal money/quantity oracles. Hashes are for source consistency only,
never an expected numeric oracle. No FIN, Redis, Rust, or S2 admission.
"""
from __future__ import annotations

import copy
import random
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from fengine_hc.reference import CalculationError, ReferenceEngine
from fengine_hc.r07_pvm import CONVENTION, pvm_revision_hashes
from qualification_r13_precision import independent_decimal_precision

ROOT=Path(__file__).resolve().parents[1]
SEED_PVM=0xC0571401
SEED_STOCK=0x570C1402
PVM_CASES=96
STOCK_CASES=80
PVM_VARIANTS=("PRICE_VARIANCE","QUANTITY_VARIANCE","MIX_VARIANCE")
STOCK_VARIANTS=("FIFO_LOT_REPLAY","MOVING_WAC","PERIODIC_WAC")
ABS=Decimal("1e-25")


def D(x):
    return Decimal(str(x))


def close(test, actual, expected, label, eps=ABS):
    difference=abs(D(actual)-D(expected))
    test.assertLessEqual(difference, eps, msg=(
        f"QUAL_R14_MATH_MISMATCH {label}: actual={actual} "
        f"expected={expected}; delta={difference}"
    ))


def pvm_case(rows):
    evidence=pvm_revision_hashes("2025-12-31","2026-12-31","KZT","PCS",rows)
    inp={
        "baselinePeriod":"2025-12-31","actualPeriod":"2026-12-31",
        "currency":"KZT","quantityUnit":"PCS","rows":copy.deepcopy(rows),
        "baselineRevisionSha256":evidence["baselineRevisionSha256"],
        "actualRevisionSha256":evidence["actualRevisionSha256"],
    }
    cfg={
        "interactionAllocation":CONVENTION,
        "standardCostVintage":evidence["standardCostVintage"],
        "volumeBaseline":evidence["volumeBaseline"],
    }
    return inp,cfg


def independent_pvm(rows):
    with localcontext() as ctx:
        ctx.prec=70
        old_qty=sum((D(x["baselineQuantity"]) for x in rows),D(0))
        new_qty=sum((D(x["actualQuantity"]) for x in rows),D(0))
        old_cost=sum((D(x["baselineQuantity"])*D(x["baselineUnitCost"])
                      for x in rows),D(0))
        new_cost=sum((D(x["actualQuantity"])*D(x["actualUnitCost"])
                      for x in rows),D(0))
        same_qty_base_price=sum(
            (D(x["actualQuantity"])*D(x["baselineUnitCost"]) for x in rows),D(0)
        )
        volume=(new_qty/old_qty-1)*old_cost
        mix=same_qty_base_price-(old_cost+volume)
        price=new_cost-same_qty_base_price
        return {
            "baselineTotalCost":old_cost, "actualTotalCost":new_cost,
            "baselineQuantity":old_qty,"actualQuantity":new_qty,
            "quantityVariance":volume,"mixVariance":mix,
            "priceVariance":price,"totalCostVariance":new_cost-old_cost,
        }


def inventory_case(rng, index):
    # All purchases first, issues afterwards. Thus periodic and moving WAC
    # must agree; FIFO depends on the original purchase lot sequence.
    costs=[D(rng.randrange(5,200))/10 for _ in range(3)]
    quantities=[D(rng.randrange(2,50)) for _ in range(3)]
    total=sum(quantities,D(0))
    issue=D(rng.randrange(1,int(total)+1))
    events=[]
    for k,(qty,cost) in enumerate(zip(quantities,costs)):
        events.append({
            "date":f"2026-01-{k+1:02d}","id":f"R{index}-P{k}",
            "quantity":str(qty),"unitCost":str(cost),
        })
    events.append({
        "date":"2026-01-07","id":f"R{index}-S",
        "quantity":str(-issue),
    })
    purchases=sum((q*c for q,c in zip(quantities,costs)),D(0))
    remaining=issue
    fifo_cost=D(0)
    for qty,cost in zip(quantities,costs):
        used=min(remaining,qty)
        fifo_cost+=used*cost
        remaining-=used
    with localcontext() as ctx:
        ctx.prec=70
        wac=issue*(purchases/total)
    return events, total-issue, purchases, fifo_cost, wac


class QualR14PvmStockProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=ReferenceEngine(ROOT)

    @independent_decimal_precision
    def test_288_pvm_factors_independent_source_cost_oracles(self):
        rng=random.Random(SEED_PVM)
        count=0
        for index in range(PVM_CASES):
            rows=[{
                "sku":f"SKU_{name}",
                "baselineQuantity":str(rng.randrange(1,500)),
                "actualQuantity":str(rng.randrange(0,500)),
                "baselineUnitCost":str(D(rng.randrange(1,1000))/100),
                "actualUnitCost":str(D(rng.randrange(0,1000))/100),
            } for name in ("A","B","C")]
            # Keep actual positive by contract.
            rows[0]["actualQuantity"]=str(max(1,int(rows[0]["actualQuantity"])))
            reference=independent_pvm(rows)
            inp,cfg=pvm_case(rows)
            for variant,focus in zip(PVM_VARIANTS,(
                "priceVariance","quantityVariance","mixVariance"
            )):
                with self.subTest(seed=SEED_PVM,index=index,variant=variant):
                    original=self.engine.calculate(
                        "HC.COST.08",variant,inp,cfg,reference_mode=True,
                    )
                    out=original.output
                    for field,expected in reference.items():
                        close(self,out[field],expected,f"{variant} {index} {field}")
                    close(self,
                          D(out["priceVariance"])+D(out["quantityVariance"])
                          +D(out["mixVariance"]),out["totalCostVariance"],
                          f"three-factor bridge {index}")
                    close(self,out["reconciliationDifference"],0,"residual")
                    close(self,out["selectedVariance"],reference[focus],focus)
                    # Reordering SKU rows is not changing their business identity
                    reordered,r_cfg=pvm_case(list(reversed(rows)))
                    self.assertEqual(cfg,r_cfg)
                    self.assertEqual(inp["baselineRevisionSha256"],
                                     reordered["baselineRevisionSha256"])
                    replay=self.engine.calculate(
                        "HC.COST.08",variant,reordered,r_cfg,reference_mode=True
                    )
                    self.assertEqual(out["selectedVariance"],
                                     replay.output["selectedVariance"])
                    count+=1
        self.assertEqual(count,3*PVM_CASES)

    @independent_decimal_precision
    def test_240_stock_models_purchase_value_conservation(self):
        rng=random.Random(SEED_STOCK)
        count=0
        for index in range(STOCK_CASES):
            events,remaining,bought,fifo,wac=inventory_case(rng,index)
            for variant in STOCK_VARIANTS:
                with self.subTest(seed=SEED_STOCK,index=index,variant=variant):
                    r=self.engine.calculate(
                        "HC.STOCK.01" if variant=="FIFO_LOT_REPLAY"
                        else "HC.STOCK.02",variant,
                        {"events":events},{},reference_mode=True,
                    )
                    out=r.output
                    cost=fifo if variant=="FIFO_LOT_REPLAY" else wac
                    close(self,out["costOfGoodsSold"],cost,"COGS")
                    close(self,out["endingQuantity"],remaining,"remaining stock")
                    close(self,D(out["costOfGoodsSold"])+D(out["endingInventory"]),
                          bought,"total acquisition-cost conservation")
                    close(self,out["endingInventory"],bought-cost,
                          "independent residual")
                    replay=self.engine.calculate(
                        r.model_code,variant,{"events":list(reversed(events))},
                        {},reference_mode=True,
                    )
                    self.assertEqual(out["costOfGoodsSold"],
                                     replay.output["costOfGoodsSold"])
                    count+=1
        self.assertEqual(count,STOCK_CASES*3)

    @independent_decimal_precision
    def test_stock_event_id_reuse_on_another_date_must_not_double_count(self):
        events=[
            {"date":"2026-01-01","id":"EXTERNAL-001",
             "quantity":"10","unitCost":"5"},
            {"date":"2026-01-02","id":"EXTERNAL-001",
             "quantity":"10","unitCost":"5"},
        ]
        for variant in STOCK_VARIANTS:
            with self.subTest(variant=variant):
                with self.assertRaises(CalculationError) as ex:
                    self.engine.calculate(
                        "HC.STOCK.01" if variant=="FIFO_LOT_REPLAY"
                        else "HC.STOCK.02",variant,
                        {"events":events},{},reference_mode=True,
                    )
                self.assertEqual(ex.exception.code,"DUPLICATE_STOCK_EVENT_ID")

    @independent_decimal_precision
    def test_stock_mixed_sku_currency_and_untyped_sale_cost_fail_closed(self):
        # HC.STOCK is deliberately ONE undimensioned cost pool. Unknown
        # fields must not be silently ignored: otherwise a two-SKU or
        # cross-currency feed can produce believable but false unit cost.
        base=[
            {"date":"2026-01-01","id":"A",
             "quantity":"10","unitCost":"10"},
            {"date":"2026-01-02","id":"B","quantity":"-3"},
        ]
        attacks=[
            [{**base[0],"sku":"OTHER-SKU"},base[1]],
            [{**base[0],"currency":"USD"},base[1]],
            [base[0],{**base[1],"unitCost":"999"}],
            [{k:v for k,v in base[0].items() if k!="unitCost"},base[1]],
        ]
        for variant in STOCK_VARIANTS:
            for index,events in enumerate(attacks):
                with self.subTest(variant=variant,attack=index):
                    with self.assertRaises(CalculationError) as error:
                        self.engine.calculate(
                            "HC.STOCK.01" if variant=="FIFO_LOT_REPLAY"
                            else "HC.STOCK.02",variant,
                            {"events":events},{},reference_mode=True
                        )
                    self.assertEqual(error.exception.code,
                                     "STOCK_EVENT_SCHEMA")

    @independent_decimal_precision
    def test_pvm_cross_period_cost_vintage_and_currency_tamper_rejected(self):
        rows=[
            {"sku":"A","baselineQuantity":"100","actualQuantity":"110",
             "baselineUnitCost":"3","actualUnitCost":"4"},
            {"sku":"B","baselineQuantity":"100","actualQuantity":"90",
             "baselineUnitCost":"9","actualUnitCost":"6"},
        ]
        inputs,cfg=pvm_case(rows)
        attacks=[
            ({**inputs,"currency":"USD"},cfg,"PVM_SOURCE_DIGEST_MISMATCH"),
            (inputs,{**cfg,"standardCostVintage":"a"*64},
             "PVM_STANDARD_COST_REVISION_MISMATCH"),
            (inputs,{**cfg,"volumeBaseline":"a"*64},
             "PVM_VOLUME_BASELINE_REVISION_MISMATCH"),
            ({**inputs,"actualPeriod":"2027-12-31"},cfg,
             "PVM_SOURCE_DIGEST_MISMATCH"),
        ]
        for inp,config,expected in attacks:
            with self.subTest(attack=expected):
                with self.assertRaises(CalculationError) as ex:
                    self.engine.calculate(
                        "HC.COST.08","MIX_VARIANCE",inp,config,
                        reference_mode=True,
                    )
                self.assertEqual(ex.exception.code,expected)

if __name__=="__main__":
    unittest.main()
