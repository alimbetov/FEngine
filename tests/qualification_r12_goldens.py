"""Synthetic independent arithmetic expectations for 48 executable HC variants.

Expected values and derivations are authored separately from FEngine logic.
Existing helper functions are used ONLY to construct valid SHA-bound source
envelopes, not to derive any expected mathematical result.
"""
from dataclasses import dataclass
from typing import Any

from test_fengine_hc_r04_reference import (
    cfo_inputs, cfo_config, fcff_inputs, fcff_config, equity_inputs,
    equity_config, escalation_inputs, escalation_config,
)
from test_fengine_hc_r05_cashflow import ledger, configuration, override_ledger
from test_fengine_hc_r06_fcfe import fcfe_fixture
from test_fengine_hc_r07_pvm import pvm_fixture


@dataclass(frozen=True)
class Golden:
    model: str
    variant: str
    inputs: dict[str, Any]
    config: dict[str, Any]
    expected: dict[str, str]
    rationale: str
    tolerance: str = "0"


def build_goldens() -> dict[tuple[str, str], Golden]:
    cases: dict[tuple[str, str], Golden] = {}

    def add(m, v, inp, cfg, expected, rationale, tolerance="0"):
        assert (m, v) not in cases and expected and rationale
        cases[m, v] = Golden(m, v, inp, cfg, expected, rationale, tolerance)

    add("HC.ASSET.01","STRAIGHT_LINE",{"cost":"1200"},
        {"residualValue":"200","usefulLifePeriods":5},
        {"periods.0.depreciation":"200","totalDepreciation":"1000","closingBalance":"200"},
        "(1200-200)/5")
    add("HC.ASSET.01","DECLINING_BALANCE",{"cost":"1000"},
        {"residualValue":"100","usefulLifePeriods":3,"decliningRate":"0.4",
         "terminalTrueUpPolicy":"FINAL_PERIOD"},
        {"periods.0.depreciation":"400","periods.1.depreciation":"240",
         "periods.2.depreciation":"260","closingBalance":"100"},
        "400, 600*0.4=240, remaining 360-100=260")
    add("HC.ASSET.01","DOUBLE_DECLINING",{"cost":"1000"},
        {"residualValue":"100","usefulLifePeriods":4},
        {"periods.0.depreciation":"500","periods.1.depreciation":"250",
         "periods.2.depreciation":"125","periods.3.depreciation":"25"},
        "2/4 declining rate and final residual true-up")
    add("HC.ASSET.01","SUM_OF_YEARS_DIGITS",{"cost":"1000"},
        {"residualValue":"100","usefulLifePeriods":4},
        {"periods.0.depreciation":"360","periods.3.depreciation":"90"},
        "900*(4/10) and 900*(1/10)")
    add("HC.ASSET.01","UNITS_OF_PRODUCTION",
        {"cost":"1000","production":["9000","21000"]},
        {"residualValue":"100","usefulLifePeriods":2,
         "estimatedTotalProduction":"30000"},
        {"periods.0.depreciation":"270","periods.1.depreciation":"630"},
        "900*9000/30000 and 900*21000/30000")

    add("HC.CAP.01","CAPM_BASE",
        {"riskFreeRate":"0.04","beta":"1.2","marketRiskPremium":"0.06"},{},
        {"costOfEquity":"0.112"},"0.04 + 1.2*0.06")
    wacc={"equityValue":"60","debtValue":"40","costOfEquity":"0.12",
          "costOfDebt":"0.08","taxRate":"0.25"}
    for variant in ("MARKET_VALUE_WACC","TARGET_WEIGHT_WACC"):
        add("HC.CAP.02",variant,wacc,{},{"wacc":"0.096"},
            "0.6*.12 + 0.4*.08*(1-.25)")

    runway={"asOf":"2026-01-01","openingCash":"100","currency":"KZT",
            "cashflows":[{"date":"2026-01-03","netCashflow":"-30"},
                         {"date":"2026-01-10","netCashflow":"-50"},
                         {"date":"2026-01-11","netCashflow":"-1"}]}
    runway_cfg={"floorValue":"20","firstPassageRule":"STRICT_BELOW_FLOOR"}
    add("HC.CASH.03","DETERMINISTIC_RUNWAY",runway,runway_cfg,
        {"elapsedDays":"10","closingCash":"19","cashAtFirstBreach":"19"},
        "100-30-50-1=19 first <20 on Jan 11")
    add("HC.CASH.03","SCENARIO_RUNWAY",
        {"asOf":"2026-01-01","openingCash":"100","currency":"KZT",
         "scenarios":[
             {"scenarioId":"BASE","cashflows":[{"date":"2026-01-05","netCashflow":"10"}]},
             {"scenarioId":"STRESS","cashflows":[{"date":"2026-01-05","netCashflow":"-95"}]},
         ]},runway_cfg,
        {"scenarios.1.elapsedDays":"4","scenarios.1.cashAtFirstBreach":"5"},
        "stress scenario has 100-95=5 on Jan 5")
    add("HC.CASH.04","DIRECT_POSTED_CFO",ledger(),configuration(),
        {"cashFlowFromOperations":"120","netInvestingCashFlow":"-30",
         "netFinancingCashFlow":"50","netAllCashFlow":"140"},
        "operating 200-80, investing -30, financing +50")
    add("HC.CASH.04","DIRECT_RECLASSIFIED_CFO",override_ledger(),configuration(),
        {"cashFlowFromOperations":"90","netInvestingCashFlow":"0",
         "netAllCashFlow":"140"},
        "30 capex recategorized as operating")
    add("HC.CASH.05","INDIRECT_CFO_ADJUSTMENT",cfo_inputs(),cfo_config(),
        {"cashFlowFromOperations":"100","noncashAdjustmentsTotal":"15"},
        "100+20-5-15=100")
    add("HC.CASH.05","INDIRECT_CFO_RECONCILED",
        {**cfo_inputs(),"directCfo":"100"},
        {**cfo_config(),"directIndirectComparisonPolicy":"EXACT_EQUALITY"},
        {"cashFlowFromOperations":"100","reconciliationDifference":"0"},
        "indirect 100 equals posted direct 100")

    add("HC.COST.04","SINGLE_PRODUCT_BREAKEVEN",
        {"fixedCost":"1000","unitPrice":"100","unitVariableCost":"60",
         "currency":"KZT","quantityUnit":"PCS"},
        {"minimumLotRule":"WHOLE_UNITS"},
        {"unitContribution":"40","breakEvenUnitsExact":"25",
         "minimumWholeUnits":"25"},
        "1000/(100-60)=25")
    add("HC.COST.04","PRODUCT_MIX_BREAKEVEN",
        {"fixedCost":"1000","currency":"KZT","products":[
            {"sku":"A","unitsPerBundle":2,"unitPrice":"100","unitVariableCost":"60"},
            {"sku":"B","unitsPerBundle":1,"unitPrice":"70","unitVariableCost":"40"}]},
        {"minimumLotRule":"WHOLE_BUNDLES","mixtureBundleIntegrality":True},
        {"bundleContribution":"110","minimumWholeBundles":"10"},
        "bundle 2*(100-60)+(70-40)=110, ceil(1000/110)=10")
    add("HC.COST.05","COMPOUND_ESCALATION",escalation_inputs(),
        escalation_config(),{"escalatedCost":"1155","incrementalCost":"155"},
        "1000*1.1*1.05=1155")
    evm={"asOf":"2026-06-30","baselineRevision":"BASELINE-SHA-A",
         "plannedValue":"80","earnedValue":"60","actualCost":"75",
         "budgetAtCompletion":"120","currency":"KZT"}
    for variant,formula,eac,vac in (
        ("EVM_BAC_CPI","BAC_DIV_CPI","150","-30"),
        ("EVM_EAC_FORECAST","AC_PLUS_REMAINING_AT_BUDGET","135","-15"),
    ):
        add("HC.COST.07",variant,evm,
            {"earnedValueRule":"EXTERNALLY_SUPPLIED_EV","eacFormula":formula},
            {"costPerformanceIndex":"0.8","estimateAtCompletion":eac,
             "varianceAtCompletion":vac},
            "EV/AC=60/75=.8; BAC/CPI=150 or AC+BAC-EV=135")
    pi,pc=pvm_fixture()
    for variant,field,value in (
        ("PRICE_VARIANCE","priceVariance","-70"),
        ("QUANTITY_VARIANCE","quantityVariance","140"),
        ("MIX_VARIANCE","mixVariance","160"),
    ):
        add("HC.COST.08",variant,pi,pc,
            {field:value,"selectedVariance":value,"totalCostVariance":"230",
             "reconciliationDifference":"0"},
            "baseline cost 1400 vs actual 1630 = +230; factors -70,140,160")

    dcf={"cashflows":["-1000","600","600"],"discountRate":"0.1"}
    add("HC.DCF.01","PERIOD_END_NPV",dcf,{"timingConvention":"PERIOD_END"},
        {"npv":"41.32231404958677685950413223140495867769"},
        "-1000+600/1.1+600/1.21","1e-30")
    add("HC.DCF.01","MIDPERIOD_NPV",dcf,{"timingConvention":"MIDPERIOD"},
        {"npv":"92.14805677222392496630696465844741659408"},
        "-1000+600/(1.1)^.5+600/(1.1)^1.5","1e-30")
    add("HC.DCF.02","EXACT_DATE_XNPV",
        {"cashflows":[{"date":"2026-01-01","amount":"-100"},
                      {"date":"2027-01-01","amount":"121"}],
         "discountRate":"0.1","valuationDate":"2026-01-01"},
        {"dayCount":"ACT_365_FIXED"},{"xnpv":"10"},
        "365 exact days: -100+121/1.1=10")

    irr_cfg={"rootDomain":{"minRate":"-0.9","maxRate":"5"},
             "rootCompletenessPolicy":"CERTIFIED_ALL"}
    add("HC.DCF.03","ALL_REAL_IRR_ROOTS",
        {"cashflows":["-100","230","-132"]},irr_cfg,
        {"rootCount":"2","roots.0":"0.1","roots.1":"0.2"},
        "-100+230/x-132/x² has roots x=1.1,1.2","1e-20")
    add("HC.DCF.03","SINGLE_IF_UNAMBIGUOUS",
        {"cashflows":["-100","110"]},irr_cfg,
        {"rootCount":"1","roots.0":"0.1"},
        "-100+110/(1+r)=0 implies r=.1","1e-20")
    add("HC.DCF.05","FCFF_UNLEVERED",fcff_inputs(),fcff_config(),
        {"taxOnOperatingProfit":"50","freeCashFlowToFirm":"110"},
        "EBIT 200 less tax50 + depreciation30 - capex50 - NWC20")
    for variant in ("FCFE_LEVERED","FCFE_NORMALIZED"):
        inp,cfg=fcfe_fixture(variant)
        add("HC.DCF.06",variant,inp,cfg,
            {"freeCashFlowToEquity":"85","netBorrowing":"25"},
            "110 after-interest CFO - capex50 + (40-15) net borrowing")
    add("HC.DCF.07","GORDON_FCFF_TERMINAL",
        {"finalForecastFCFF":"100","wacc":"0.10",
         "forecastPeriods":1,"currency":"KZT"},
        {"terminalMethod":"GORDON_FCFF","terminalGrowth":"0.02"},
        {"nextPeriodFCFF":"102","terminalAtForecastHorizon":"1275"},
        "100*(1+.02)/(.1-.02)=1275")
    add("HC.DCF.08","EV_TO_EQUITY_BRIDGE",equity_inputs(),equity_config(),
        {"netDebt":"250","equityValue":"720","bridgeReconciliation":"0"},
        "EV1000-debt300+cash50+assets20-minority40-preferred10")

    ev1={"defaultDate":"2026-06-01","lossDate":"2028-01-01",
         "pd":"0.1","lgd":"0.5","exposure":"100"}
    ev2={"defaultDate":"2026-12-01","lossDate":"2028-12-01",
         "pd":"0.2","lgd":"0.5","exposure":"100"}
    add("HC.ECL.02","FIRST_12_MONTH_DEFAULT_EVENTS",
        {"events":[ev1,ev2],"asOf":"2026-01-01","annualEir":"0"},
        {"defaultEventWindow":"FIRST_12_MONTHS"},
        {"expectedCreditLoss":"15"},".1*.5*100+.2*.5*100=15")
    ev3={"defaultDate":"2027-01-01","lossDate":"2027-01-01",
         "pd":"0.1","lgd":"0.5","exposure":"100"}
    ev4={"defaultDate":"2028-01-01","lossDate":"2028-01-01",
         "pd":"0.2","lgd":"0.5","exposure":"100"}
    add("HC.ECL.03","LIFETIME_TERM_PD",
        {"events":[ev3,ev4],"asOf":"2026-01-01","annualEir":"0"},
        {"hazardConditionality":"CONDITIONAL_PD"},
        {"expectedCreditLoss":"14","survivalProbability":"0.72"},
        "5+(.9*.2*.5*100)=14; survival .9*.8=.72")

    loan={"principal":"1000","annualRate":"0",
          "startDate":"2026-01-01","paymentDates":["2026-02-01","2026-03-01"],
          "dayCount":"ACT_365_FIXED"}
    for variant,first in (
        ("ANNUITY_EQUAL_PAYMENT_DATED","500"),
        ("EQUAL_PRINCIPAL_DATED","500"),
        ("INTEREST_ONLY_BALLOON","0"),("BULLET","0"),
    ):
        add("HC.LOAN.02",variant,loan,{},
            {"schedule.0.principal":first,"schedule.1.principal":
             "500" if first=="500" else "1000",
             "totalInterest":"0","closingPrincipal":"0"},
            "zero-rate principal repayment: 500+500 or balloon 0+1000")
    add("HC.LOAN.03","EIR_ORIGINAL",
        {"cashflows":[{"date":"2026-01-01","amount":"-100"},
                      {"date":"2027-01-01","amount":"110"}]},
        {"discountOrigin":"2026-01-01",
         "rootCompletenessPolicy":"CERTIFIED_ALL"},
        {"effectiveRate":"0.1"},"110/(1+r)=100","1e-20")
    coverage={"cfads":["100","100","100"],"outstandingDebt":"100",
              "discountRate":"0","loanPeriods":2}
    add("HC.PF.01","LLCR_DEBT_LIFE",coverage,{},
        {"coverageRatio":"2"},"Debt-life 2 periods: (100+100)/100 = 2")
    add("HC.PF.01","PLCR_PROJECT_LIFE",coverage,{},
        {"coverageRatio":"3"},"Project-life 3 periods: (100+100+100)/100 = 3")
    losses=["1","2","3","4","5"]
    add("HC.RISK.02","EMPIRICAL_LEFT_QUANTILE",{"losses":losses},
        {"alpha":"0.8","lossSignPolicy":"POSITIVE_LOSS",
         "quantileDefinition":"NEAREST_RANK"},
        {"valueAtRisk":"4"},"nearest rank ceil(5*.8)=4")
    add("HC.RISK.03","QUANTILE_INTEGRAL_ES",{"losses":losses},
        {"confidenceAlpha":"0.7",
         "esTailMassRule":"QUANTILE_INTEGRAL_FRACTIONAL_ATOM"},
        {"expectedShortfall":"4.666666666666666666666666666666666666667"},
        "(5+0.5*4)/1.5=14/3","1e-30")

    aging={"obligations":[
        {"dueDate":"2026-03-15","unpaidAmount":"10"},
        {"dueDate":"2026-02-15","unpaidAmount":"20"},
        {"dueDate":"2026-01-01","unpaidAmount":"30"}],
        "asOf":"2026-03-01"}
    add("HC.SET.03","DUE_DATE_AGING",aging,{"ageingBucketEdges":[30,60]},
        {"totalOutstanding":"60","buckets.CURRENT":"10",
         "buckets.1-30":"20","buckets.31-60":"30"},
        "due March15 current, Feb15 14 late, Jan1 59 late")
    add("HC.SET.03","GRACE_ADJUSTED_AGING",
        {"obligations":[{"dueDate":"2026-02-28","unpaidAmount":"10"}],
         "asOf":"2026-03-01"},
        {"ageingBucketEdges":[30,60],"graceDays":2},
        {"totalOutstanding":"10","buckets.CURRENT":"10"},
        "Feb28 due has 2-day grace as of Mar1")
    stock=[
        {"date":"2026-01-01","id":"1","quantity":"10","unitCost":"10"},
        {"date":"2026-01-02","id":"2","quantity":"10","unitCost":"20"},
        {"date":"2026-01-03","id":"3","quantity":"-12"},
    ]
    add("HC.STOCK.01","FIFO_LOT_REPLAY",{"events":stock},{},
        {"costOfGoodsSold":"140","endingQuantity":"8",
         "endingInventory":"160"},
        "10*10+2*20 COGS, remaining 8*20")
    for variant in ("MOVING_WAC","PERIODIC_WAC"):
        add("HC.STOCK.02",variant,{"events":stock},{},
            {"costOfGoodsSold":"180","endingQuantity":"8",
             "endingInventory":"120"},
            "WAC 300/20=15, COGS12*15 and remaining8*15")
    return cases
