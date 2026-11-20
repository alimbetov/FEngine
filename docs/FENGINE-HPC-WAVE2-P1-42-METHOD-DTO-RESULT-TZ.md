# FEngine HPC-W2 — техническое задание: 42 показателя P1, Python Calculation Hub

**Document ID:** FENGINE-HPC-W2-P1-TZ-V1  
**Date:** 2026-11-20  
**Status:** REQUIREMENTS_DRAFT / METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD  
**Reference:** FENGINE_MASTER_SPEC.md v0.4 (83 codes), Wave-1 14-model DTO v1.1, Python Memory Hub PY-R0.  
**Owner architecture:** one shared Python reference engine, one InputBatchDTO, one CalculationResponseDTO with results[] → rows[] → values[], one memory/session/job protocol.  
**Scope:** 42 existing P1 codes; no 42 new services, no new FIN form, no code/migrations/tests. The numbers below are synthetic arithmetic test candidates, not audited financial examples or independent finance S2.

## 1. General conventions

Each model requires **the exact version** of input schema, calculation method, parameter contract and output schema, with effective SHA-256 and independent example. Abbreviations: R required, C conditional, O optional. A field of type MONEY uses decimal string + explicit ISO4217 currency and source accounting basis. RATE is decimal fraction (0.10=10%); RATIO fraction; DAYS is integer or Decimal when weighted; QUANTITY has a physical unit. All date ranges, credit stages and statuses are versioned. Every row has rowKey/businessKey, source revision hash, tenant/project scope and valueState (PRESENT, MISSING, EXPLICIT_NULL, NOT_APPLICABLE, INVALID), inherited from the common input contract.

**Source list:** references such as C01, P07, A05 denote candidate FIN source/contract families, not proven field bindings or E2E coverage. The completed upstream record must be reconstructible from FIN immutable source revision; when the required event or field does not exist, model status is BLOCKED_SOURCE, never fabricated.

**Output:** common CalculationResultSetDTO includes modelCode/taskCode/methodRevision/algorithmManifest/resultShape/currency/period/status/sourceLineage plus rows[]. Every output metricCode listed below is a newly proposed FEngine contract (not automatically a FIN metric). Root errors, statistical confidence, and NOT_COMPARABLE are statuses, not zero.

**Synthetic fixtures:** formulas below are valid only with their stated simplified assumptions. Accounting and regulatory applicability requires separate source and policy evidence. Golden vectors for production must be independently reviewed with a second calculator/control example.

## 2. Additional typed Dataset DTO schemas (extend Wave-1 D01–D15)

Fields marked (!) mandatory for indicated variant, (?) conditional; all have a sourceRevisionRef and per-row valueState. Numeric display examples use KZT but wire contract never hardcodes currency. Period/asOf/basis/currency are explicitly pinned per dataset.

### D16. ARAP_BALANCE_SNAPSHOT

obligationKey:REF!; counterpartyKey:REF!; side:ENUM(AR; AP)!; asOf:LOCAL_DATE!; balance:MONEY!; overdue:MONEY?; currency:ISO4217!; classification:CODE!; sourceRevisionRef:REF!.


### D17. RECOGNIZED_SALES_COST_FLOW

entityKey:REF!; period:PERIOD!; flowType:ENUM(SALES_CREDIT; COGS; PURCHASES)!; amount:MONEY!; currency:ISO4217!; basis:CODE!; sourceRevisionRef:REF!.


### D18. LEGAL_OFFSET_RIGHT

partyKey:REF!; instrumentA:REF!; instrumentB:REF!; rightEffectiveFrom:LOCAL_DATE!; enforceableRight:BOOLEAN!; intentNetOrSimultaneous:BOOLEAN!; approvalRef:REF!; nettingSetKey:REF!.


### D19. CREDIT_EXPOSURE

instrumentKey:REF!; cohort:CODE!; stage:ENUM(1; 2; 3; POCI)!; asOf:LOCAL_DATE!; grossExposure:MONEY!; effectiveRate:RATE?; reportCurrency:ISO4217!; eclMethodEligibility:CODE!; sourceRevisionRef:REF!.


### D20. PROVISION_MATRIX

cohort:CODE!; agingBucket:CODE!; lossRate:RATE!; effectiveFrom:LOCAL_DATE!; historicalEvidenceRef:REF!; policyRevisionRef:REF!; currency:ISO4217?.


### D21. CREDIT_SCENARIO_WEIGHT

scenarioKey:REF!; probability:RATE!; effectiveDate:LOCAL_DATE!; macroEvidenceRef:REF!; adjustmentRuleRef:REF!; sourceRevisionRef:REF!.


### D22. CREDIT_TERM_POINT

instrumentKey:REF!; scenarioKey:REF!; periodIndex:INTEGER!; startDate:LOCAL_DATE!; endDate:LOCAL_DATE!; conditionalDefaultProbability:RATE!; ead:MONEY!; lgd:RATE!; discountFactor:DECIMAL!; survivalStart:RATE?; sourceRevisionRef:REF!.


### D23. LOAN_CARRYING_EVENT

loanKey:REF!; effectiveDate:LOCAL_DATE!; openingCarrying:MONEY!; eirRate:RATE!; interestExpense:MONEY?; cashPaid:MONEY!; principalPaid:MONEY!; adjustment:MONEY?; closingCarrying:MONEY?; eventRef:REF!; sourceRevisionRef:REF!.


### D24. LOAN_MODIFICATION_CASHFLOW

loanKey:REF!; changeRevision:REF!; eventDate:LOCAL_DATE!; oldExpectedCash:MONEY?; newExpectedCash:MONEY?; originalEir:RATE!; modificationFee:MONEY?; recognitionPolicyRef:REF!.


### D25. COVENANT_CASH_DEFINITION

contractKey:REF!; period:PERIOD!; cfads:MONEY!; eligibleDebtService:MONEY!; threshold:RATIO!; comparison:ENUM(GE; GT; LE; LT)!; contractDefinitionRef:REF!; sourceRevisionRef:REF!.


### D26. LIQUIDITY_BUCKET_FLOW

entityKey:REF!; bucketStart:LOCAL_DATE!; bucketEnd:LOCAL_DATE!; inflow:MONEY!; outflow:MONEY!; currency:ISO4217!; flowStatus:ENUM(POSTED; FORECAST)!; scenarioKey:REF!; sourceRevisionRef:REF!.


### D27. LIQUIDITY_THRESHOLD

entityKey:REF!; scenarioKey:REF!; asOf:LOCAL_DATE!; minCash:MONEY!; openingCash:MONEY!; cashFloorKind:CODE!; sourceRevisionRef:REF!.


### D28. BANK_TRANSACTION

bankTxnKey:REF!; accountKey:REF!; valueDate:LOCAL_DATE!; postingAt:INSTANT!; direction:ENUM(IN; OUT)!; amount:MONEY!; currency:ISO4217!; counterpartyRef:REF?; externalRef:REF?; sourceRevisionRef:REF!.


### D29. FX_RATE_QUOTE

pairCode:CODE!; quoteDate:LOCAL_DATE!; rate:DECIMAL!; quoteConvention:ENUM(LOCAL_PER_FOREIGN; FOREIGN_PER_LOCAL)!; rateType:ENUM(TRANSACTION; CLOSING; APPROVED_AVERAGE)!; sourceRevisionRef:REF!.


### D30. FX_CASH_STOCK

accountKey:REF!; currency:ISO4217!; openingAmount:MONEY!; closingAmount:MONEY!; openingRate:DECIMAL!; closingRate:DECIMAL!; transactionFxImpact:MONEY?; period:PERIOD!; sourceRevisionRef:REF!.


### D31. DCF_TERMINAL_AND_BRIDGE

projectKey:REF!; scenarioKey:REF!; terminalYearIndex:INTEGER!; lastFCFF:MONEY?; nextFCFF:MONEY?; wacc:RATE?; growth:RATE?; costOfEquity:RATE?; netDebt:MONEY?; nonoperatingAdjustments:MONEY?; terminalPolicyRef:REF!.


### D32. SENSITIVITY_GRID

scenarioKey:REF!; parameterCode:CODE!; parameterValue:DECIMAL!; parameterUnit:CODE!; baseScenarioRef:REF!; orderIndex:INTEGER!; policyRef:REF!.


### D33. STATEMENT_LINE

entityKey:REF!; statement:ENUM(BS; PL; CF)!; lineCode:CODE!; period:PERIOD!; basis:CODE!; amount:MONEY!; currency:ISO4217!; sourceRevisionRef:REF!.


### D34. INTERCOMPANY_MATCH

entityFrom:REF!; entityTo:REF!; transactionKey:REF!; counterpartyTransactionKey:REF?; period:PERIOD!; accountCode:CODE!; amount:MONEY!; currency:ISO4217!; eliminationClass:CODE!; sourceRevisionRef:REF!.


### D35. LEASE_PAYMENT

leaseKey:REF!; dueDate:LOCAL_DATE!; payment:MONEY!; discountRate:RATE!; leaseCurrency:ISO4217!; paymentEligibility:CODE!; revisionRef:REF!; modificationDate:LOCAL_DATE?.


### D36. IDENTIFIED_STOCK_ITEM

serialKey:REF!; itemKey:REF!; warehouseKey:REF!; unitCost:MONEY!; quantity:QUANTITY!; movementKey:REF!; movementType:ENUM(RECEIPT; ISSUE; RETURN)!; effectiveAt:INSTANT!; sourceRevisionRef:REF!.


### D37. STOCK_NRV_ESTIMATE

itemKey:REF!; asOf:LOCAL_DATE!; quantity:QUANTITY!; costTotal:MONEY!; estimatedSellingPriceTotal:MONEY!; completionCost:MONEY!; sellingCost:MONEY!; evidenceRef:REF!; valuationPolicyRef:REF!.


### D38. STOCK_ROLL_FORWARD

itemKey:REF!; warehouseKey:REF!; period:PERIOD!; openingQty:QUANTITY!; receiptsQty:QUANTITY!; issuesQty:QUANTITY!; adjustmentsQty:QUANTITY!; closingQty:QUANTITY?; unitCode:CODE!; sourceRevisionRef:REF!.


### D39. ASSET_COMPONENT

assetKey:REF!; componentKey:REF!; inServiceDate:LOCAL_DATE!; cost:MONEY!; residualValue:MONEY!; usefulLifeYears:DECIMAL!; depreciationMethod:CODE!; currency:ISO4217!; policyRevisionRef:REF!; sourceRevisionRef:REF!.


### D40. ASSET_MEASUREMENT_EVENT

assetKey:REF!; componentKey:REF?; effectiveDate:LOCAL_DATE!; eventType:ENUM(ADDITION; DEPRECIATION; IMPAIRMENT; REVERSAL; REVALUATION; DISPOSAL)!; amount:MONEY!; signPolicyRef:REF!; accountingPolicyRef:REF!; sourceRevisionRef:REF!.


### D41. CAPITAL_COMMITMENT

projectKey:REF!; assetKey:REF?; commitmentKey:REF!; expectedPaymentDate:LOCAL_DATE!; expectedInServiceDate:LOCAL_DATE?; amount:MONEY!; currency:ISO4217!; status:CODE!; capitalizationPolicyRef:REF!.


### D42. COST_POOL

period:PERIOD!; costCenter:REF!; poolKey:REF!; amount:MONEY!; currency:ISO4217!; allocationPolicyRef:REF!; sourceRevisionRef:REF!.


### D43. ALLOCATION_DRIVER

period:PERIOD!; poolKey:REF!; targetCostObject:REF!; driverCode:CODE!; driverQuantity:QUANTITY!; unitCode:CODE!; weight:DECIMAL?; sourceRevisionRef:REF!.


### D44. RESOURCE_BOM

workKey:REF!; resourceKey:REF!; quantityPerUnit:QUANTITY!; unitCode:CODE!; wasteRate:RATE?; effectiveFrom:LOCAL_DATE!; sourceRevisionRef:REF!.


### D45. RESOURCE_PRICE

resourceKey:REF!; effectiveFrom:LOCAL_DATE!; unitCost:MONEY_PER_UNIT!; currency:ISO4217!; unitCode:CODE!; vendorOrTariffRef:REF!; sourceRevisionRef:REF!.


### D46. SALES_PRICE_VOLUME

skuKey:REF!; period:PERIOD!; basePrice:MONEY_PER_UNIT!; actualPrice:MONEY_PER_UNIT!; baseQty:QUANTITY!; actualQty:QUANTITY!; currency:ISO4217!; unitCode:CODE!; sourceRevisionRef:REF!.


### D47. BOQ_LINE

projectKey:REF!; workKey:REF!; workQuantity:QUANTITY!; unitCode:CODE!; materialRate:MONEY_PER_UNIT!; laborRate:MONEY_PER_UNIT!; equipmentRate:MONEY_PER_UNIT!; overheadPolicyRef:REF!; sourceRevisionRef:REF!.


### D48. EARNED_VALUE_POINT

projectKey:REF!; asOf:LOCAL_DATE!; plannedValue:MONEY!; earnedValue:MONEY!; actualCost:MONEY!; budgetAtCompletion:MONEY!; progressEvidenceRef:REF!; sourceRevisionRef:REF!.


### D49. COST_DRIVER_BUDGET

period:PERIOD!; costObject:REF!; budgetFixed:MONEY!; budgetVariablePerUnit:MONEY_PER_UNIT!; plannedActivity:QUANTITY!; actualActivity:QUANTITY!; actualTotalCost:MONEY!; sourceRevisionRef:REF!.


### D50. FINANCIAL_FORECAST_LINE

entityKey:REF!; scenarioKey:REF!; period:PERIOD!; statementType:ENUM(PL; BS; CF)!; lineCode:CODE!; amount:MONEY!; currency:ISO4217!; sourceRevisionRef:REF!.


### D51. SCENARIO_SHOCK

scenarioKey:REF!; shockKey:REF!; targetMetric:CODE!; shockType:ENUM(ADDITIVE; MULTIPLICATIVE)!; shockValue:DECIMAL!; unitCode:CODE!; effectivePeriod:PERIOD!; sourceRevisionRef:REF!.


### D52. FUNDING_INSTRUMENT

instrumentKey:REF!; scenarioKey:REF!; capacity:MONEY!; drawLimit:MONEY!; minimumDraw:MONEY?; rate:RATE!; availabilityStart:LOCAL_DATE!; availabilityEnd:LOCAL_DATE!; priority:INTEGER!; currency:ISO4217!; eligibilityRef:REF!.


### D53. BANK_LEDGER_POSTING

postingKey:REF!; bankTxnKey:REF?; accountKey:REF!; postingDate:LOCAL_DATE!; direction:ENUM(DEBIT; CREDIT)!; amount:MONEY!; currency:ISO4217!; matchRuleRef:REF!; sourceRevisionRef:REF!.


### D54. SALES_COGS_MARGIN

productKey:REF!; period:PERIOD!; baseRevenue:MONEY!; actualRevenue:MONEY!; baseCost:MONEY!; actualCost:MONEY!; currency:ISO4217!; sourceRevisionRef:REF!.


## 3. Cross-family dependencies and reuse

- All contracts from Wave-1 D01–D15 are reused without redefinition; P1 adds D16–D54.
- D16 balances reconcile HC.SET.01/.02 and asOf on C01/C02; D23 contract accrual follows HC.LOAN.03; D26 cashflow path follows HC.CASH.01.
- D13 dated flows and D31 terminal/bridge back HC.DCF.02/.04/.07/.08/.09.
- D33 and D50 P&L/BS/CF line contracts share one metric graph and cannot create new uncontrolled source writer.
- D38/D39/D40 follow stock/asset event snapshots; D42–D49 management costs use same dimension+unit registry.
- One Calculation Session may share dataset content across multiple permitted jobs; each task has **its own idempotencyKey and immutable execution binding**; dependency outputs are referenced by committed ResultSetSha, not by mutable memory pointers.
- All terminal results use the same CalculationResponseDTO and six ResultShapes (GROUPED, AGGREGATE, TIME_SERIES, ROW_ALIGNED, EVENT_SERIES, ROOT_SET); SENSITIVITY_GRID introduces the existing candidate SCENARIO_MATRIX shape to ResultShape allowlist after versioned schema revision.

## 4. Individual metric contracts (42 P1)

Each task spec below enumerates logical source, typed dataset arrays, necessary parameter variants, deterministic candidate formula, output metric codes/types and a **synthetic** worked arithmetic vector. Every model has required independent financial-policy review before any Python reference implementation. Standard DayCount, rounding, sign, materiality and currency values must be explicit from immutable Plan and must not be inferred from examples.


### 01. HC.SET.04 — Взвешенный срок просрочки портфеля

**TaskCode:** W2.SET.04.V1 · **FIN candidate refs:** C01;C02;A01 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D16 balances + W1 D02 installments; balances >0 asOf |
| Method parameters / variants | weightBasis=OVERDUE_AMOUNT \| OPEN_BALANCE, cutoff=AS_OF, denominatorPolicy=UNDEFINED_ZERO, calendarPolicyRef; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | WDPD = Σ_i max(0,asOf-due_i)×weight_i / Σ_i weight_i, using verified unpaid due amounts; do not average invoiced face values |
| Unified OutputDTO values | WEIGHTED_DPD:DECIMAL[DAYS], WEIGHT_TOTAL:MONEY, COUNT:INTEGER; AGGREGATE |
| Independent synthetic control candidate | 2 overdue installments: 100 KZT aged 10 days, 50 KZT aged 30 days → weighted DPD=(1000+1500)/150=16.6666667 days |
| Blockers / negative tests | sum weights zero ⇒ UNDEFINED; mixed currency, already settled lines, changed due dates |
| Dependency DAG / Session reuse | HC.SET.03; D16; allocation/replay; same asOf |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 02. HC.SET.05 — Юридически допустимый свёрнутый остаток контрагента

**TaskCode:** W2.SET.05.V1 · **FIN candidate refs:** C01;C02;C11 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D16 AR/AP by counterparty + D18 LEGAL_OFFSET_RIGHT; exact same legal entities, instruments and date |
| Method parameters / variants | nettingRule=ELIGIBLE_ONLY, legalApprovalRev, sameCurrencyPolicy, intendedSettlementBasis, asOf; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Compute net eligible instrument-by-instrument only for verified enforceable right AND net/simultaneous intent; present gross otherwise. This is not universal per-counterparty netting |
| Unified OutputDTO values | ELIGIBLE_NET_RECEIVABLE:MONEY, ELIGIBLE_NET_PAYABLE:MONEY, GROSS_AR:MONEY, GROSS_AP:MONEY, BLOCK_REASON:CODE; GROUPED |
| Independent synthetic control candidate | Eligible AR 100, AP 80 same netting set with verified right+intent → net receivable 20; absent right: gross AR100 / AP80, no net20 |
| Blockers / negative tests | law/source/intent unverified ⇒ BLOCK_NETTING; currency or entity mismatch ⇒ separate gross |
| Dependency DAG / Session reuse | HC.SET.01;HC.SET.02; D18 legal scope |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 03. HC.SET.07 — DSO и DPO по согласованным потокам

**TaskCode:** W2.SET.07.V1 · **FIN candidate refs:** C01;C02;P06;C07 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D16 opening and closing stock snapshots + D17 creditSales/costOfSales or policy-specific creditPurchases; same period |
| Method parameters / variants | averageStockPolicy=TWO_POINT \| DAILY_WEIGHTED, denominatorSalesPolicy=CREDIT_ONLY, dayCount, currency/basis; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | DSO = avg eligible AR / eligible period credit sales × days; DPO = avg eligible AP / eligible purchases or COGS (versioned alternative) × days. Never swap denominators without variant revision |
| Unified OutputDTO values | DSO:DAYS, DPO:DAYS, AVG_AR:MONEY, AVG_AP:MONEY, SALES_BASE:MONEY; AGGREGATE |
| Independent synthetic control candidate | AR open 80 and close120, credit sales 1000 across 365 days => DSO=36.5 days |
| Blockers / negative tests | zero denominator⇒UNDEFINED; COGS vs purchases mismatch; non-comparable snapshots |
| Dependency DAG / Session reuse | HC.SET.01/02; D17; period validation |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 04. HC.ECL.01 — Портфельный резерв ECL по ageing matrix

**TaskCode:** W2.ECL.01.V1 · **FIN candidate refs:** C01;A02;DF-CSH-04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D19 eligible trade exposures, D20 cohort/bucket loss rates, D21 approved scenario overlay; D16 asOf ageing |
| Method parameters / variants | approach=SIMPLIFIED_IFRS9_ELIGIBLE, cohortPolicyRef, scenarioWeightRev, forwardOverlayPolicyRef, discountEligibility; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For eligible simplified provision-matrix cohort compute Σ exposure_i × approved adjusted lifetime lossRate(cohort,aging,scenario); weights sum 1; any overlay requires evidence and approved calibration, not arbitrary multiplier |
| Unified OutputDTO values | ECL_ALLOWANCE:MONEY, ECL_BY_BUCKET:MONEY, ECL_COVERAGE:RATIO, SCENARIO_ECL:MONEY; GROUPED |
| Independent synthetic control candidate | Two cohorts: 100 KZT×0.01 + 200 KZT×0.10 = 21 KZT under single approved scenario rates |
| Blockers / negative tests | missing loss-rate source, unsupported instrument class, weights!=1, allowance automatically capped ⇒ BLOCKED |
| Dependency DAG / Session reuse | HC.SET.03; D19–D21; independent IFRS9 eligibility |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 05. HC.ECL.02 — 12-month ECL по кредитному портфелю

**TaskCode:** W2.ECL.02.V1 · **FIN candidate refs:** C01;C05;A02 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D19 instruments + D22 term PD/EAD/LGD with dated recovery discount and D21 scenario weights |
| Method parameters / variants | defaultWindow=FIRST_12_MONTHS, discountBasis=ORIGINAL_EIR where applicable, PDType=CONDITIONAL_HAZARD, recoveryTimingRef; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | ECL_12m=Σ_s w_s Σ_t(default within next 12m) survival_{t-1}×conditionalPD_t×discounted lifetime cash shortfall attributable to default_t. Simplified EAD×LGD approximation only validated for loss timing |
| Unified OutputDTO values | ECL_12M:MONEY, MARGINAL_PD_12M:RATE, ECL_BY_SCENARIO:MONEY; AGGREGATE |
| Independent synthetic control candidate | One 1-year default point: EAD100, PD0.02, LGD0.4, discount1/1.1 => ECL=0.7272727273 KZT |
| Blockers / negative tests | t>12m default probabilities included erroneously; EIR missing; PD annual vs conditional mismatch; IFRS staging unknown |
| Dependency DAG / Session reuse | D19–D22; W1 LOAN.EIR; source financial S2 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 06. HC.ECL.03 — Lifetime ECL по term structure

**TaskCode:** W2.ECL.03.V1 · **FIN candidate refs:** C01;C05;A02 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D19 instruments, D22 year-by-year conditional PD/LGD/EAD, D21 scenarios; exact dates and discount factors |
| Method parameters / variants | horizon=EXPECTED_LIFE, survivalRecursion, scenarioWeightRev, cashShortfallModelRef, amortizingExposurePolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | ECL_life=Σ_s w_s Σ_t S_(t-1)q_t EAD_t LGD_t DF_t for explicitly approved approximation; S_t=S_(t-1)(1-q_t), no sum of conditional PD without survival |
| Unified OutputDTO values | LIFETIME_ECL:MONEY, LIFETIME_PD:RATE, MARGINAL_DEFAULT:RATE per time; TIME_SERIES + AGGREGATE |
| Independent synthetic control candidate | Two years: conditional PD=[0.10,0.20], EAD100, LGD0.5, DF=[1/1.1,1/1.21] → ECL≈11.9834710744 KZT |
| Blockers / negative tests | survival outside [0,1], stage classification absent, unbounded horizon, wrong recovery timing |
| Dependency DAG / Session reuse | HC.ECL.02; D19–D22; method S2 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 07. HC.LOAN.04 — Амортизированная стоимость по EIR

**TaskCode:** W2.LOAN.04.V1 · **FIN candidate refs:** C05;F01;A05 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D23 actual dated accounting cash events + W1 D06/D08/D09 contract and verified initial carrying |
| Method parameters / variants | originalEirRev, accountingCashflowDirection, interestAccrualPeriod, modificationPolicyRef, roundingStage; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Closing gross carrying = opening gross carrying + effective interest accrual − qualifying contractual cash collection ± approved modifications/other events. Separate cash principal from EIR interest and booked fees |
| Unified OutputDTO values | GROSS_CARRYING:MONEY, EIR_INTEREST:MONEY, ACCRUED_CASH_INTEREST:MONEY, ROLL_FORWARD_RESIDUAL:MONEY; TIME_SERIES |
| Independent synthetic control candidate | Opening carrying980, period EIR accrual 98, cash received 80 → closing gross carrying998 KZT (illustrative no other event) |
| Blockers / negative tests | cash vs book basis, incorrectly net ECL, missing time gap or modification, double charge |
| Dependency DAG / Session reuse | HC.LOAN.03; D23; approved IFRS9 measurement |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 08. HC.LOAN.05 — Модификация долга: пересмотр дисконтированных потоков

**TaskCode:** W2.LOAN.05.V1 · **FIN candidate refs:** C05;F01/F02;A05 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D24 old/new expected cashflows + D23 carrying + originalEir; modification classification evidence |
| Method parameters / variants | modificationType=NON_DERECOGNITION \| DERECOGNITION_REVIEW, originalEirRev, discountOriginDate, financialDerecognitionGate; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For qualified non-derecognition case new carrying = PV(revised cashflows, original EIR); modification gain/loss = new carrying − pre-modification carrying by agreed asset/liability sign. Derecognition cases use distinct policy and cannot pass generic branch |
| Unified OutputDTO values | MODIFIED_PV:MONEY, MODIFICATION_GAIN_LOSS:MONEY, NEW_CARRYING:MONEY, CLASSIFICATION:CODE; AGGREGATE |
| Independent synthetic control candidate | Old carrying100, one revised receipt 110 in 1 year at original EIR10% ⇒ new PV100, modification difference0 |
| Blockers / negative tests | missing derecognition assessment; wrong discount rate; signed cashflow inconsistency; fees classification |
| Dependency DAG / Session reuse | HC.LOAN.03/.04; D24; S2 derecognition policy |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 09. HC.LOAN.06 — Экономический эффект досрочного погашения

**TaskCode:** W2.LOAN.06.V1 · **FIN candidate refs:** C05;P04;A05;A01 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | W1 D06/D07/D08/D09 loan cash events + D24 revised expected cashflows, scenario baseline vs early |
| Method parameters / variants | earlyDate, prepaymentAmount, earlyFeePolicyRef, recalcMethod=REDUCE_TERM \| REDUCE_INSTALLMENT, discountRateBasis; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Construct two admissible contractual schedules under same basis: baseline vs accelerated; delta interest=baseline future interest−scenario future interest; net borrower benefit = interest saved−early repayment fees, excluding principal timing unless discount/PV policy is selected |
| Unified OutputDTO values | INTEREST_SAVED:MONEY, EARLY_FEE:MONEY, NET_NOMINAL_BENEFIT:MONEY, NEW_SCHEDULE:TIME_SERIES |
| Independent synthetic control candidate | Baseline future nominal interest100, early scenario interest60, penalty10 ⇒ nominal benefit30 KZT, ignoring timing by stated variant |
| Blockers / negative tests | wrong principal schedule, repayment posted twice, cash-time comparison presented as NPV, fee eligibility missing |
| Dependency DAG / Session reuse | HC.LOAN.01/.02; HC.SET.06; D24 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 10. HC.LOAN.07 — DSCR и договорные ковенанты

**TaskCode:** W2.LOAN.07.V1 · **FIN candidate refs:** P09;P04;C05;A05 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D25 authorized contractual CFADS/debt service + W1 loan scheduled cash, covenant definition and exact period |
| Method parameters / variants | cfadsContractRev, serviceIncludesFees, threshold, comparison, grace/cure policyRef, zeroServicePolicy=UNDEFINED; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | DSCR=eligible CFADS / eligible cash debt service on same interval; covenant PASS/FAIL only if legally verified definition, threshold and remedies; analytical DSCR must have separate metric code |
| Unified OutputDTO values | CONTRACT_DSCR:RATIO, COVENANT_STATUS:CODE, CFADS:MONEY, ELIGIBLE_SERVICE:MONEY; AGGREGATE |
| Independent synthetic control candidate | CFADS150, debt service100, contractual minimum1.20 → DSCR1.5 and candidate PASS only when approved contract |
| Blockers / negative tests | missing contract definition; denominator zero; management CFADS used as legal covenant |
| Dependency DAG / Session reuse | HC.LOAN.02; D25; contract S2 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 11. HC.CASH.02 — Разрыв ликвидности по корзинам

**TaskCode:** W2.CASH.02.V1 · **FIN candidate refs:** P03;P10;C01/C02 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D26 time-bucket in/out + D27 opening cash/minimum thresholds, scenario with all eligible obligations |
| Method parameters / variants | bucketCalendarRev, openingCashPolicy, includeUndrawnFacilities=EXPLICIT_ONLY, minimumBufferPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For ordered buckets B_t=B_(t-1)+inflows−outflows; liquidity gap_t=max(0,minimumCash_t−B_t); funding need is not just sum gaps if deficits persist |
| Unified OutputDTO values | CASH_END:MONEY, LIQUIDITY_SHORTFALL:MONEY, MAX_SHORTFALL:MONEY, FIRST_GAP_DATE:DATE; TIME_SERIES |
| Independent synthetic control candidate | Cash starts50, inflow10, outflow80, minimum buffer0 => cash−20, gap20 KZT |
| Blockers / negative tests | overlapping buckets; double-count loans; missing currency/forecast statuses; 0 incorrectly substituted for missing |
| Dependency DAG / Session reuse | HC.CASH.01; D26–D27 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 12. HC.CASH.03 — Cash runway по сценариям

**TaskCode:** W2.CASH.03.V1 · **FIN candidate refs:** P03;P08 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D26 scenario cashflows, D27 lower bound thresholds, D51 dated scenario shocks |
| Method parameters / variants | horizon, cashFloor, interpolationPolicy=DISCRETE_BUCKET, nonMonotonicCashHandling, scenarioProbabilitiesRef; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Compute first time t where B_t < floor, not simply openingCash/averageBurn for nonconstant series; if threshold never crossed return NOT_REACHED horizon, not zero days |
| Unified OutputDTO values | RUNWAY_BUCKETS:INTEGER, FIRST_BREACH_DATE:DATE?, MIN_CASH:MONEY, RUNWAY_STATE:CODE; TIME_SERIES/AGGREGATE |
| Independent synthetic control candidate | Opening100, weekly net flow −30 → closes70,40,10,−20 ⇒ first breach week4 |
| Blockers / negative tests | horizon truncated; positive/negative flows mixed; ambiguity equality vs below; no initial cash |
| Dependency DAG / Session reuse | HC.CASH.01/.02; D26–D27 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 13. HC.CASH.06 — Банковская сверка операций с главной книгой

**TaskCode:** W2.CASH.06.V1 · **FIN candidate refs:** C06;F03;ACC-03 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D28 bank transactions + D53 ledger postings, valueDate, postedAt, amount/currency and match refs |
| Method parameters / variants | matchMode=EXACT \| APPROVED_TOLERANCE, dateWindow, cashAccountMapRev, reversalPolicy, manyToOneRule; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Bipartite/policy-allowed matching by account/date/ref/amount; reconcile unmatched bank rows, unmatched ledger and verified matched total; no arbitrary best-match writes |
| Unified OutputDTO values | MATCHED_TOTAL:MONEY, UNMATCHED_BANK:MONEY, UNMATCHED_LEDGER:MONEY, MATCH_STATUS:CODE per event; ROW_ALIGNED |
| Independent synthetic control candidate | Bank debit80, ledger matched80 ⇒ unmatched amount0, matched80, before other rows |
| Blockers / negative tests | duplicate bank txn, tolerance invalid, sign confusion, unmatched many-to-many, historic bank statement revision |
| Dependency DAG / Session reuse | W1.CASH.CFO_DIRECT; D28,D53 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 14. HC.CASH.07 — FX bridge денежных средств

**TaskCode:** W2.CASH.07.V1 · **FIN candidate refs:** F03;C06 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D30 opening/closing cash per currency + D29 closing/transaction rates and cash movements |
| Method parameters / variants | functionalCurrency, presentationCurrency, rateQuoteConvention, fxCashFlowPolicyRev, roundingStage; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For simplified one-currency roll-forward foreign cash opening×openingFX + net cashflow×transactionFX + FX_EFFECT = closing cash×closingFX; FX_EFFECT is balancing noncash conversion difference, not extra operating cash |
| Unified OutputDTO values | FX_EFFECT:MONEY, OPENING_PRESENTED:MONEY, CLOSING_PRESENTED:MONEY, CASHFLOW_PRESENTED:MONEY; GROUPED |
| Independent synthetic control candidate | USD cash opening100, no flows, FX opening500 KZT/USD, closing510 ⇒ FX effect1000 KZT |
| Blockers / negative tests | rate direction reversed; transaction versus closing rate mixed; multistate float; closing date missing |
| Dependency DAG / Session reuse | W1.CASH.WEEK13; D29/D30; IAS7 + IAS21 policy review |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 15. HC.CASH.08 — Потребность во внешнем финансировании

**TaskCode:** W2.CASH.08.V1 · **FIN candidate refs:** P10;P03;INV-08 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D26 cash path, D27 thresholds and D52 candidate facilities with borrowing rules |
| Method parameters / variants | fundingObjective=MIN_PEAK_DRAWDOWN \| MIN_COST, borrowLimit, costRate, availabilityWindow, minimumCash; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | At each bucket compute minimum eligible facility draw required to keep end cash>=threshold, obey capacity and eligibility; return infeasible if insufficient. Objective distinguishes minimal required draw vs cost-optimal financing |
| Unified OutputDTO values | REQUIRED_DRAW:MONEY per bucket, TOTAL_DRAW:MONEY, FINANCING_GAP:MONEY, FEASIBILITY:CODE; TIME_SERIES |
| Independent synthetic control candidate | Cash deficit30, facility capacity50 and minimum cash0 → required draw30, closing cash0; capacity20 => remaining gap10/infeasible |
| Blockers / negative tests | facility validity gap, circular draw interest unmodeled, source cash scenario mismatch |
| Dependency DAG / Session reuse | HC.CASH.02; D52; optimization gate |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 16. HC.DCF.02 — NPV датированных денежных потоков

**TaskCode:** W2.DCF.02.V1 · **FIN candidate refs:** P07;A06 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | W1 D13 with eventDate for every flow, pinned rate and date basis |
| Method parameters / variants | annualDiscountRate, dayCount=ACT/365F (illustrative), valuationDate, cashflowBasis, allowPreValuationFlows; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Dated NPV=Σ CF_i/(1+r)^yearFraction(date_i−valuationDate), same real/nominal and currency basis; each date explicit |
| Unified OutputDTO values | DATED_NPV:MONEY, DISCOUNT_FACTOR:DECIMAL per cashflow; AGGREGATE/TIME_SERIES |
| Independent synthetic control candidate | Valuation t0 cash−100, exactly365 days later +110 at annual rate0.10 => dated NPV0 KZT |
| Blockers / negative tests | missing dated cashflow, r≤−1, unequal date source, time basis and FX mismatch |
| Dependency DAG / Session reuse | HC.DCF.01; D13 with eventDate |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 17. HC.DCF.04 — XIRR по календарным датам

**TaskCode:** W2.DCF.04.V1 · **FIN candidate refs:** P07;A06 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | W1 D13 irregular dated flows, t0 and signed cash |
| Method parameters / variants | dayCount, domainMinRate>−1, domainMaxRate, solverTolerance, rootCompletenessPolicy, rootSearchStatus; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Find all admissible real roots of Σ CF_i/(1+r)^yearFraction_i=0; report no/multiple roots and residuals; not force unique XIRR |
| Unified OutputDTO values | XIRR_ROOT:RATE per root, SOLVER_RESIDUAL:MONEY, ROOT_COUNT:INTEGER, ROOT_SEARCH_STATE:CODE; ROOT_SET |
| Independent synthetic control candidate | −100 today and +110 exactly one year later on declared ACT/365F basis → XIRR0.10 |
| Blockers / negative tests | missing valuation date; t>0? wrong; multiple/no roots; roots only sign-change scan |
| Dependency DAG / Session reuse | HC.DCF.03; D13 exact dates |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 18. HC.DCF.05 — FCFF: свободный денежный поток фирмы

**TaskCode:** W2.DCF.05.V1 · **FIN candidate refs:** P07;P03;P05;INV-02 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D33 P&L source EBIT/taxes + D41 CAPEX + D16/38 operating working capital movements |
| Method parameters / variants | taxOnOperatingProfitPolicy, depreciationNonCashScope, capexScope, workingCapitalPolicy, financingExclusion; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Illustrative unlevered FCFF = EBIT×(1−qualified tax rate)+D&A−CAPEX−ΔOperatingNWC. Exclude financing cash movements, require operating basis and bridge |
| Unified OutputDTO values | FCFF:MONEY, NOPAT:MONEY, CAPEX:MONEY, DELTA_NWC:MONEY; TIME_SERIES |
| Independent synthetic control candidate | EBIT100, tax25%, D&A10, CAPEX20, ΔNWC5 → FCFF60 KZT |
| Blockers / negative tests | negative EBIT tax-shield fabricated, missing working capital, duplicate D&A, wrong tax basis |
| Dependency DAG / Session reuse | HC.ACC.01; D33,D41 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 19. HC.DCF.06 — FCFE: свободный поток на собственный капитал

**TaskCode:** W2.DCF.06.V1 · **FIN candidate refs:** P07;P04;INV-03 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | FCFF qualified result + D23 financing cash, tax shield interest information and W1 loan actual cash classification |
| Method parameters / variants | cfadsBase, interestTaxTreatmentPolicy, debtDrawsCash, principalPaymentsCash, debtFeesEligibility; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Under consistent derivation FCFE = FCFF − after-tax interest + net borrowings, where net borrowings = draws − principal paid; alternatively CFO−CAPEX+net borrowing if CFO includes financing interest; methods cannot be mixed |
| Unified OutputDTO values | FCFE:MONEY, AFTER_TAX_INTEREST:MONEY, NET_BORROWING:MONEY; TIME_SERIES |
| Independent synthetic control candidate | FCFF60, after-tax interest8, net borrowings +20 ⇒ FCFE72 KZT |
| Blockers / negative tests | interest double counted, wrong tax shield, debt service cash as earning, incompatible FCFF/CFO bases |
| Dependency DAG / Session reuse | HC.DCF.05; HC.LOAN.02; D23 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 20. HC.DCF.07 — DCF стоимость компании и терминальная стоимость

**TaskCode:** W2.DCF.07.V1 · **FIN candidate refs:** P07;INV-06;A06 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | periodic FCFF qualified output + D31 terminal basis, WACC, growth, horizon |
| Method parameters / variants | terminalMethod=GORDON \| EXIT_MULTIPLE_REVIEW, waccRate, growthRate, terminalYear, midyearConvention, currency; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Gordon TV_n=FCFF_(n+1)/(WACC−g), require WACC>g; EV=Σ_t FCFF_t/(1+WACC)^t+TV_n/(1+WACC)^n. Never FCFE/WACC |
| Unified OutputDTO values | ENTERPRISE_VALUE:MONEY, TERMINAL_VALUE:MONEY, PV_TERMINAL:MONEY, TERMINAL_SHARE:RATIO; AGGREGATE |
| Independent synthetic control candidate | n=1 FCFF1=100, nextFCFF=60, WACC0.10,g0.04 ⇒ TV1=1000; EV=(100+1000)/1.1=1000 KZT |
| Blockers / negative tests | g>=wacc, terminal dominates and unsupported, FCFE/WACC, mismatched inflation/FX |
| Dependency DAG / Session reuse | HC.DCF.05; HC.DCF.02; D31 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 21. HC.DCF.08 — Стоимость собственного капитала и мост EV→Equity

**TaskCode:** W2.DCF.08.V1 · **FIN candidate refs:** P07;INV-04;A06 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D31 EV and net debt/non-operating items + qualified FCFE and costOfEquity as separate valuation alternative |
| Method parameters / variants | valuationMethod=EV_BRIDGE \| DISCOUNT_FCFE, netDebtPolicyRef, bridgeAdjustmentsRef, Ke, currency; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Equity via EV bridge=EV−netDebt+eligible nonoperating adjustments; discounted FCFE/Ke is separate method, consistency check not automatic equivalence |
| Unified OutputDTO values | EQUITY_VALUE:MONEY, NET_DEBT:MONEY, BRIDGE_ADJUSTMENT:MONEY, VALUATION_BASIS:CODE; AGGREGATE |
| Independent synthetic control candidate | EV1000, netDebt300, nonoperating adjustments+20 ⇒ equity720 KZT |
| Blockers / negative tests | net debt signs; equity via FCFE discounted WACC; double cash/debt bridge |
| Dependency DAG / Session reuse | HC.DCF.07; HC.DCF.06; D31 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 22. HC.DCF.09 — Матрица чувствительности инвестиционной оценки

**TaskCode:** W2.DCF.09.V1 · **FIN candidate refs:** P08;P07;INV-07 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D32 sensitivity grid + D13 cashflows + D31 valuation params; immutable baseline scenario |
| Method parameters / variants | axesCodes, cellBudget, monotonicityNotAssumed, scenarioAxisPolicy, modelHash; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For each grid point substitute allowed policy parameter(s), recompute pinned DCF DAG, calculate delta to baseline; avoid treating correlated assumptions as independent unless explicit |
| Unified OutputDTO values | SENSITIVITY_VALUE:MONEY per grid cell, DELTA_TO_BASE:MONEY, AXIS_VALUES:DECIMAL[], CELL_STATE:CODE; SCENARIO_MATRIX |
| Independent synthetic control candidate | Single-period CF110: NPV at r0.10=100, at r0.20=91.6666667; delta=−8.3333333 KZT, no initial t0 by this fixture |
| Blockers / negative tests | axes inconsistent; wacc<=g; stale baseline; combinatorial explosion; nonfinancially allowed shocks |
| Dependency DAG / Session reuse | HC.DCF.01/.07; D32; Calculation Session reuse |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 23. HC.ACC.01 — Трёхотчётная интегрированная модель

**TaskCode:** W2.ACC.01.V1 · **FIN candidate refs:** F01/F02/F03;P01/P02/P03;CFO-01 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D33 BS/PL/CF lines + D50 projected statement lines, period mappings |
| Method parameters / variants | cashflowClassificationPolicy, assetLiabilityEquitySigns, retainedEarningsPolicy, openingBalanceRef, taxPolicyRef; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Propagate qualified net income/working capital/financing/capex through P&L, balance sheet and cashflow. Validate A−L−E=0, opening cash+CFO+CFI+CFF+FX=closing cash, income/equity bridge |
| Unified OutputDTO values | BALANCE_RESIDUAL:MONEY, CASH_RESIDUAL:MONEY, NET_PROFIT:MONEY, CASH_CLOSING:MONEY; TIME_SERIES |
| Independent synthetic control candidate | Assets200, liabilities120, equity80 ⇒ balance residual0; cash20 + CFO10 + CFI−5 + CFF0 ⇒ cash25 |
| Blockers / negative tests | source balance nonzero; mixed IFRS/management; mismatched years; missing OCI/FX corrections |
| Dependency DAG / Session reuse | HC.CASH.04/.05; D33,D50; statement taxonomy |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 24. HC.ACC.02 — Внутригрупповые элиминации

**TaskCode:** W2.ACC.02.V1 · **FIN candidate refs:** F08;C14;ACC-07 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D34 opposing intra-group entries with reconciliation keys, holding ownership and approved consolidation scope |
| Method parameters / variants | consolidationPerimeterRef, matchTolerance, intercompanyUnrealizedProfitRef, groupCurrencyPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Pair eligible intra-group AR/AP, revenue/expense and other matched transactions; eliminate both sides at group level, never eliminate external transactions, extra unrealized profit only with qualified inventory policy |
| Unified OutputDTO values | ELIM_AR:MONEY, ELIM_AP:MONEY, ELIM_REVENUE:MONEY, ELIM_EXPENSE:MONEY, UNMATCHED:MONEY; GROUPED |
| Independent synthetic control candidate | Subsidiary A AR100 to B and B AP100 to A => consolidated group eliminates AR100 and AP100 (net group exposure 0) |
| Blockers / negative tests | unmatched intercompany keys; foreign exchange difference; no group perimeter or ownership info |
| Dependency DAG / Session reuse | HC.ACC.01; D34; IFRS10 policy |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 25. HC.ACC.04 — Межфирменная сверка счетов

**TaskCode:** W2.ACC.04.V1 · **FIN candidate refs:** F06;C14;C11 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D34 intercompany entries with mirror account/date/party and authorized currency conversion |
| Method parameters / variants | matchingKeys, asOf, dateTolerance, currencyConversionPolicyRef, residualMateriality; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For each entity pair compare recognized intercompany debit/credit after lawful FX and timing adjustments; residual = signed mirrorA+mirrorB, exceptions per row |
| Unified OutputDTO values | MIRROR_DIFFERENCE:MONEY, MATCHED_AMOUNT:MONEY, UNMATCHED_COUNT:INTEGER; GROUPED |
| Independent synthetic control candidate | A shows +100 due from B, B shows −95 due to A → signed residual+5 KZT before allowed adjustment |
| Blockers / negative tests | mismatched effective time, fake netting, undisclosed bank charges, different economic entity |
| Dependency DAG / Session reuse | D34; HC.ACC.02 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 26. HC.ACC.06 — Обязательство по аренде IFRS16

**TaskCode:** W2.ACC.06.V1 · **FIN candidate refs:** C13;C05;ACC-06 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D35 lease payments with commencement, rate and eligibility plus modification revisions |
| Method parameters / variants | lesseeEligibility, discountRateRev, paymentTiming, extensionOptionEvidence, reassessmentPolicy, leaseTerm; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | At commencement PV=Σ eligible unpaid lease payments/(1+r)^t; subsequent closing liability = opening+interest−payment±qualified remeasurements. ROU asset separate, not equal to liability at all times |
| Unified OutputDTO values | LEASE_PV:MONEY, LEASE_INTEREST:MONEY, LEASE_LIABILITY_CLOSE:MONEY; TIME_SERIES |
| Independent synthetic control candidate | Two annual unpaid payments50 each at r0.10 ⇒ lease PV≈86.7768595041 KZT |
| Blockers / negative tests | exempt short/low value without policy; variable payments misclassified; incorrect remeasurement rate |
| Dependency DAG / Session reuse | D35; HC.LOAN.03 as solver capability only |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 27. HC.STOCK.03 — Specific identification запасов

**TaskCode:** W2.STOCK.03.V1 · **FIN candidate refs:** C03;DF-STK-01/02/03;A03 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D36 serial-number cost rows + W1 D15 movements, qualified unique item IDs |
| Method parameters / variants | valuationMethod=SPECIFIC_IDENTIFICATION, itemEligibilityPolicyRef, costCurrency, transferReturnPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Direct traced inventory cost: sum exact original unit acquisition cost of each uniquely identified disposed unit, never substitute FIFO/WAC for noninterchangeable items |
| Unified OutputDTO values | SPECIFIC_ISSUE_COST:MONEY, REMAINING_IDENTIFIED_COST:MONEY, SERIAL_LINEAGE:REF[]; ROW_ALIGNED |
| Independent synthetic control candidate | Serial A cost100, serial B cost200, issue B → cost200, remaining A100 KZT |
| Blockers / negative tests | serial duplicate; untraceable original cost; sold item unavailable; price currency mismatch |
| Dependency DAG / Session reuse | HC.STOCK.01/.02 (transport); D36 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 28. HC.STOCK.04 — NRV уценка запасов

**TaskCode:** W2.STOCK.04.V1 · **FIN candidate refs:** C03;A03 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D37 verified item-level cost and net realizable values asOf |
| Method parameters / variants | nrvEligibleItemsRef, expectedSellingPricePolicy, completionCostPolicy, sellingCostPolicy, reversalCeilingPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | NRV=estimatedSellingPrice−completionCost−necessarySellingCosts; write-down=max(0,cost−NRV) per eligible item, not arbitrarily netted across dissimilar item types. Reversal capped by original write-down |
| Unified OutputDTO values | NRV:MONEY, WRITEDOWN:MONEY, CARRYING_AT_LOWER:MONEY; ROW_ALIGNED |
| Independent synthetic control candidate | Inventory cost100, selling estimate90, completion5, selling3 => NRV82; write-down18 KZT |
| Blockers / negative tests | missing selling evidence; NRV as market price; aggregate netting of different items; reversal above original cost |
| Dependency DAG / Session reuse | D37; HC.STOCK.01/02; IAS2 approval |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 29. HC.STOCK.06 — Сверка складского roll-forward

**TaskCode:** W2.STOCK.06.V1 · **FIN candidate refs:** C03;DF-STK-01/02/03 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D38 opening/movement/closing per item+warehouse + W1 D15 events |
| Method parameters / variants | stockInterval, unitConversionPolicy, transferNettingPolicy, cutOffPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | ExpectedCloseQty=openingQty+receiptQty−issueQty±signedAdjustments; matched close from verified snapshot, missing close cannot be fabricated |
| Unified OutputDTO values | EXPECTED_CLOSE_QTY:QUANTITY, ACTUAL_CLOSE_QTY:QUANTITY, QTY_DIFFERENCE:QUANTITY; ROW_ALIGNED |
| Independent synthetic control candidate | Opening10 units, receipt5, issue8, no adjustments → expected close7 units |
| Blockers / negative tests | incompatible unit and date, transfer double counted, missing opening qty, negative stock without policy |
| Dependency DAG / Session reuse | HC.STOCK.01/.02; D38 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 30. HC.ASSET.01 — Покомпонентная амортизация

**TaskCode:** W2.ASSET.01.V1 · **FIN candidate refs:** C04;DF-AST-01;A04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D39 components with useful life/residual/cost/inService date + D40 changes |
| Method parameters / variants | method=STRAIGHT_LINE \| DECLINING \| UNITS_PRODUCTION, lifeRevisionPolicy, convention, suspended/disposal rule; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Straight-line per component annual depreciation=(cost−residual)/usefulLifeYears, apportioned by admitted in-service fraction; other variants use distinct methods. Stop when fully depreciated, at derecognition, or appropriate rule |
| Unified OutputDTO values | DEPRECIATION:MONEY, ACCUMULATED_DEPR:MONEY, NBV:MONEY; TIME_SERIES |
| Independent synthetic control candidate | Asset component cost1200, residual200, life5 full years ⇒ depreciation200 KZT/year |
| Blockers / negative tests | zero/negative life; residual>cost; change in estimates retroactive; inactive asset depreciated incorrectly |
| Dependency DAG / Session reuse | D39–D40; IAS16 policy |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 31. HC.ASSET.02 — Переоценка и impairment ОС

**TaskCode:** W2.ASSET.02.V1 · **FIN candidate refs:** C04;F01;A04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D40 ASSET_MEASUREMENT_EVENT + D39 carrying/revaluation policy and prior reserve |
| Method parameters / variants | revaluationModelRef, fairValueEvidenceRef, ociBalanceRef, reversalLimit, impairmentClassificationRef; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Apply sequenced events cost→depreciation→impairment/reversal/revaluation as approved policy; revaluation differences split OCI/P&L based on historic decrease/reversal policy; not a single unconditional credit |
| Unified OutputDTO values | NEW_CARRYING:MONEY, OCI_MOVEMENT:MONEY, PL_MOVEMENT:MONEY; EVENT_SERIES |
| Independent synthetic control candidate | Carrying80, reviewed eligible fair value100, no prior history under simplified revaluation policy ⇒ increase20 (classification subject to policy) |
| Blockers / negative tests | wrong OCI classification, missing fair value, impairment double recognition, change in policy without revision |
| Dependency DAG / Session reuse | HC.ASSET.01; D39/D40; IAS16/IAS36 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 32. HC.ASSET.04 — Балансовая стоимость основных средств на дату

**TaskCode:** W2.ASSET.04.V1 · **FIN candidate refs:** C04;A04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D39 components + D40 dated depreciation and impairment/revaluation events |
| Method parameters / variants | asOf, componentAggregationPolicy, duplicateEventGuard, currencyValuationPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Carrying cost/revaluation + capitalized additions − cumulative depreciation − impairment + lawful reversals − disposals, by exact component and asOf; do not sum multiple historical stock snapshots |
| Unified OutputDTO values | CARRYING_AMOUNT:MONEY, COST_BASIS:MONEY, ACCUM_DEPRECIATION:MONEY, IMPAIRMENT:MONEY; ROW_ALIGNED |
| Independent synthetic control candidate | Asset cost1000, accumulated depreciation200, impairment50 ⇒ carrying750 KZT |
| Blockers / negative tests | negative carrying without method, last revision ignored, assets mixed units, double asset component |
| Dependency DAG / Session reuse | HC.ASSET.01/.02; D39/D40 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 33. HC.ASSET.07 — CAPEX график и вводы в эксплуатацию

**TaskCode:** W2.ASSET.07.V1 · **FIN candidate refs:** P05;C04;INV-01 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D41 committed capex/payment/milestone rows, D39 asset identities, separate paid/forecast event status |
| Method parameters / variants | capitalizationPolicyRef, cashVsAccrualMode, delayHandling, periodCalendarRef, committedBudgetScope; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Aggregate projected CAPEX payments by period and separately recognize capital asset additions at permitted in-service / cost criterion date; cash payment ≠ capitalization automatically |
| Unified OutputDTO values | CAPEX_CASH_SCHEDULE:MONEY, CAPITALIZED_ADDITION:MONEY, UNPAID_COMMITMENT:MONEY; TIME_SERIES |
| Independent synthetic control candidate | 100 KZT qualifying asset paid in month1, commissioned in month2 → cash CAPEX month1=100; capitalization month2=100 only under stated assumption |
| Blockers / negative tests | payment and asset addition double counted; missing in-service date; work-in-progress classification unresolved |
| Dependency DAG / Session reuse | D41; HC.ASSET.04 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 34. HC.COST.01 — ABC многоступенчатое распределение расходов

**TaskCode:** W2.COST.01.V1 · **FIN candidate refs:** C08;F07;DF-CST-03;CFO-07 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D42 cost pools, D43 driver values by target activity and period, approved driver hierarchy |
| Method parameters / variants | allocationStages, driverZeroPolicy=BLOCK, unallocatedResidualPolicy, entityScope, roundingStage; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Allocate pool cost to target j as Cpool×driver_j/Σ driver for eligible cost objects; recursively distribute intermediary pools only through versioned acyclic cost graph; sum allocations+unallocated=original cost |
| Unified OutputDTO values | ALLOCATED_COST:MONEY, UNALLOCATED_COST:MONEY, ALLOCATION_RATE:MONEY_PER_UNIT; GROUPED |
| Independent synthetic control candidate | Pool100 KZT, drivers 3 and 2 units => allocated60 and40 KZT |
| Blockers / negative tests | zero driver denominator; cyclic cost allocation; wrong currency/cost center; allocation rounding drift |
| Dependency DAG / Session reuse | D42/D43; graph source |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 35. HC.COST.02 — Расчёт ресурсной себестоимости единицы

**TaskCode:** W2.COST.02.V1 · **FIN candidate refs:** SF-F02;DF-OPS-02;CST-04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D44 BOM quantities per finished unit + D45 resource unit rates with compatible units |
| Method parameters / variants | wasteRatePolicy, conversionPolicy, effectivePriceDate, laborOverheadVariant, resourceInclusionRule; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Unit direct resource cost=Σ requiredQty_perFinishedUnit×(1+wasteRate)×approved resourceUnitCost; indirect overhead separate from direct resource cost |
| Unified OutputDTO values | UNIT_DIRECT_COST:MONEY_PER_UNIT, RESOURCE_EXTENDED_COST:MONEY, RESOURCE_QTY:QUANTITY; ROW_ALIGNED |
| Independent synthetic control candidate | One unit uses 2 kg material×10 KZT/kg and 3 labor hours×5 KZT/h ⇒ direct cost35 KZT/unit |
| Blockers / negative tests | incompatible kg/h, stale rate, wrong waste factor (rate vs percent), duplicated BOM row |
| Dependency DAG / Session reuse | D44/D45; unit registry |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 36. HC.COST.03 — Price-volume-mix разложение изменения выручки

**TaskCode:** W2.COST.03.V1 · **FIN candidate refs:** C07;C08;C09;CFO-04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D46 SKU prices/quantities baseline and actual, stable mix categories and same currency |
| Method parameters / variants | attributionVariant=PRICE_THEN_VOLUME \| SHAPLEY, newSkuPolicy, missingSkuPolicy, aggregationPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Ordered decomposition for revenue ΔR=Σ(P1Q1−P0Q0), priceEffect=Σ(P1−P0)Q1 and volumeEffect=Σ(Q1−Q0)P0, exact sum under this stated order. Mix decomposition needs additional share/volume baseline and cannot be inferred from these two effects alone |
| Unified OutputDTO values | REVENUE_DELTA:MONEY, PRICE_EFFECT:MONEY, VOLUME_EFFECT:MONEY, RESIDUAL:MONEY; GROUPED |
| Independent synthetic control candidate | One SKU P0=10,Q0=10,P1=12,Q1=11 => ΔR=32, price effect22, volume effect10 KZT |
| Blockers / negative tests | mix called price effect; new SKU without base policy; refunds/returns basis wrong; arbitrary causal claim |
| Dependency DAG / Session reuse | D46; W1 Cash not required |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 37. HC.COST.06 — BoQ сметная стоимость строительных работ

**TaskCode:** W2.COST.06.V1 · **FIN candidate refs:** SF-F01/SF-F02;CST-01/04 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D47 verified quantities and material/labor/equipment unit rates; D44/D45 resources optional |
| Method parameters / variants | measurementStandardRevision, unitConversionPolicy, overheadMarginPolicy, taxEscalationVersion, contractCurrency; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | DirectBoQCost=Σ workQuantity×(materialRate+laborRate+equipmentRate) per eligible work unit; overhead/tax/contingency only as distinct policy outputs, not default implicit uplift |
| Unified OutputDTO values | BOQ_DIRECT_COST:MONEY, BOQ_BY_WORK:MONEY, TOTAL_WITH_APPROVED_ADDONS:MONEY; GROUPED |
| Independent synthetic control candidate | 2 units of work with rates 10 material +20 labor +5 equipment = 70 KZT direct cost |
| Blockers / negative tests | unrecognized work units, manual double counting overhead, excluded VAT mixed, rate effective date mismatch |
| Dependency DAG / Session reuse | D47; HC.COST.02 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 38. HC.COST.07 — Earned Value CPI/SPI/EAC

**TaskCode:** W2.COST.07.V1 · **FIN candidate refs:** SF-F01/SF-F02;CST-09 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D48 verified planned value PV, earned value EV, actual cost AC, BAC at same asOf |
| Method parameters / variants | EACVariant=BAC/CPI \| AC+(BAC−EV)/CPI, noCompletionBeyondBACPolicy, zeroDenominator; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | CPI=EV/AC; SPI=EV/PV; illustrative EAC=BAC/CPI if EAC variant assumes future CPI, VAC=BAC−EAC. Forecast assumptions versioned; zero denominators undefined not zero |
| Unified OutputDTO values | CPI:RATIO, SPI:RATIO, EAC:MONEY, VAC:MONEY, ETC:MONEY; AGGREGATE |
| Independent synthetic control candidate | EV80, AC100, PV100, BAC200 ⇒ CPI0.8,SPI0.8,EAC250,VAC−50 KZT |
| Blockers / negative tests | earned value from spending not progress; SPI as schedule days; zero PV/AC; baseline altered |
| Dependency DAG / Session reuse | D48; approved progress evidence |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 39. HC.COST.08 — План-факт затрат по драйверам

**TaskCode:** W2.COST.08.V1 · **FIN candidate refs:** C08;P02;CFO-03 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D49 budget fixed/variable costs and actual activity/cost, same period and cost object |
| Method parameters / variants | flexBudgetVariant=FIXED_PLUS_VARIABLE_ACTIVITY, varianceSign=ACTUAL_MINUS_FLEX, driversUnitRev; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | FlexibleBudget=fixedBudget+variableRate×actualActivity; spendingVariance=actualCost−flexBudget; volumeVariance=flexBudget−originalStaticBudget |
| Unified OutputDTO values | FLEX_BUDGET:MONEY, SPENDING_VARIANCE:MONEY, VOLUME_VARIANCE:MONEY; GROUPED |
| Independent synthetic control candidate | Fixed100, variable2 per unit, plan10 units, actual15, actual cost135 => flex130, spending variance+5, volume variance+10 KZT |
| Blockers / negative tests | fixed/variable classification missing; unit mismatch; F02 actual from incompatible scope |
| Dependency DAG / Session reuse | D49; HC.COST.01 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 40. HC.PLAN.01 — Rolling forecast финансовых показателей

**TaskCode:** W2.PLAN.01.V1 · **FIN candidate refs:** P01/P02/P03;MGT-05 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D50 financial multi-statement monthly lines + D51 assumption changes, verified historic actuals |
| Method parameters / variants | rollingHorizon, fiscalCalendarRef, forecastCutover, modelDependencyDAGRef, latestActualRevision; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For period t actual frozen and t+1..t+H forecast using approved time-series/driver methodology; ensure source periods not overwritten and forecast revision immutable, propagate dependencies through common graph |
| Unified OutputDTO values | ROLLING_FORECAST:MONEY, FORECAST_VARIANCE:MONEY, FORECAST_REVISION:CODE, HORIZON:INTEGER; TIME_SERIES |
| Independent synthetic control candidate | Annualized simple model: month actual100, next two monthly forecasts110 and120 => remaining two-month forecast230 KZT (not 3-month actual sum) |
| Blockers / negative tests | look-ahead leakage; actual overwritten by forecast; unit inconsistency; cyclic forecasting dependencies |
| Dependency DAG / Session reuse | HC.ACC.01; D50/D51; scenario |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 41. HC.PLAN.07 — Согласованный сценарный P&L/BS/CF

**TaskCode:** W2.PLAN.07.V1 · **FIN candidate refs:** P01/P02/P03;CFO-01 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D50 scenario statement lines + D51 shocks; D33 source actual/closing balances |
| Method parameters / variants | dependencyGraphRev, scenarioRevision, accountingRecognitionRules, cashFlowClassPolicy, balancingPolicy=BLOCK_NOT_PLUG; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | Recompute linked projected P&L, balance sheet and cash flow for exact scenario, with reconciled closing balances and no fabricated cash plug; prevent double shock application |
| Unified OutputDTO values | PL_NET_PROFIT:MONEY, BS_BALANCE_RESIDUAL:MONEY, CF_CASH_CLOSE:MONEY, SCENARIO_DIFFERENCE:MONEY; TIME_SERIES |
| Independent synthetic control candidate | Projected assets210, liabilities120, equity90 ⇒ BS residual0; forecast cash opening10 + net flows5 ⇒ close15 |
| Blockers / negative tests | auto plug fake balancing line, scenario mismatched, absent cashflow source bridge |
| Dependency DAG / Session reuse | HC.ACC.01; HC.PLAN.01; D50/D51 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |


### 42. HC.RISK.04 — Многопериодное стресс-тестирование ликвидности

**TaskCode:** W2.RISK.04.V1 · **FIN candidate refs:** P03;P08;CFO-02 · **Status:** METHOD_CANDIDATE / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Input arrays / fields | D26 baseline cashflows + D27 thresholds + D51 shocks by period/flow drivers; scenario dependent rate/FX |
| Method parameters / variants | shockApplicationOrder, scenarioWeight, riskHorizon, FXShockRef, cashFloor, liquidityConstraintPolicy; common NumericPolicy/Calendar/Scope/Revision SHA from Wave-1 |
| Method formula / conditions | For each stress scenario recompute dated eligible receipts/outflows and cash balances, first threshold breach and peak funding gap; do not average deterministic paths as though a probabilistic forecast without probability model |
| Unified OutputDTO values | STRESSED_CASH_PATH:MONEY, MIN_CASH:MONEY, PEAK_GAP:MONEY, FIRST_BREACH:DATE; TIME_SERIES |
| Independent synthetic control candidate | Opening100, first stress period inflows10 and outflows130 → closing−20, peak gap20 KZT at zero cash floor |
| Blockers / negative tests | negative scenario weights, shock applied twice, period leakage, unbounded stress grid |
| Dependency DAG / Session reuse | HC.CASH.01/.02/.03; D26/D27/D51 |
| Numeric acceptance | Exact Decimal money and unit arithmetic; solver root residual by pinned tolerance; matching dimensions, currency, period, stable ordering |



## 5. P1 acceptance and mathematical limits

- P1 coverage must equal **42 and only 42 codes** in FEngine v0.4; no duplicate TaskCode.
- Test for each metric: synthetic positive arithmetic, missing required input, zero denominator, invalid unit/currency/period, stale sha/policy, duplicate event where applicable, negative sign and reversal, cross-tenant access, repeated key and conflicting idempotency key.
- ECL: 12-month loss means loss from default events possible in next 12 months, **not only cash shortfalls paid in next 12 months**. Lifetime credit risk uses marginal PD = survival × conditional default hazard; recovery timing and EIR discounting are versioned. No arbitrary EAD×LGD×PD as universal IFRS9 model.
- OCI / derecognition / lease modifications and consolidation depend on approved instrument-level accounting evidence, not inferred account name.
- Value in use, terminal growth, DCF, FCFF/FCFE, cashflow real/nominal and tax treatment require explicit compatibility gates.
- Valid risk/error states: BLOCKED_SOURCE, BLOCKED_METHODOLOGY, REVIEW_REQUIRED, INVALID, NOT_COMPARABLE, UNDEFINED, NO_ROOT, PARTIAL_SEARCH. API job success does not mean financially approved output.
- Statistical inference, behavioral correlations or forecast confidence cannot be inferred from deterministic fixed-input formulas without variance/probability evidence.
- All models document 1 row, empty input, 1k/100k/1m row batches and restart/replay semantics at design stage; runtime performance tests are future work only.
- Python Decimal goldens must be independently specified; Python vs Rust parity alone is not independent proof. Numeric tolerances locked by policy, not ad hoc percentages.

## 6. Data storage / Python Memory Hub relationship

RegisterInput → durable typed InputManifest and hashes → optional Memory Dataset cache → CalculationSession sealed → Execute(TaskCode + independent idempotencyKey + exact method revision) → Python isolated worker candidate → one or more immutable ResultSet arrays → PG transactional Outbox → archive ACK → temporary payload cleanup after 3 hours only if archive exists. Evicted RAM is a cache miss, not financial data loss.

Derived source results can be referenced by result hash in later jobs; they are not implicitly copied or republished to FIN. If a P1 model depends on output of an unapproved predecessor, both cannot be treated as production-ready; staged UAT status must propagate the blocker.

## 7. Normative references — for future method review, not blanket approval

IFRS Foundation standards pages:
- IFRS 9 / 12-month and lifetime ECL — https://www.ifrs.org/content/dam/ifrs/project/fi-impairment/ifrs-standard/published-documents/project-summary-july-2014.pdf
- IFRS 10 consolidation — https://www.ifrs.org/issued-standards/list-of-standards/ifrs-10-consolidated-financial-statements/
- IAS 2 inventories — https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/
- IAS 16 fixed-asset depreciation and review — https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ias-16-property-plant-and-equipment.pdf
- IAS 21 foreign-exchange translation — https://www.ifrs.org/issued-standards/list-of-standards/ias-21-the-effects-of-changes-in-foreign-exchange-rates/
- IFRS 16 leases — https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2022/issued/part-a/ifrs-16-leases.pdf

**Release decision:** REQUIREMENTS_ONLY. All 42 P1 metrics have proposed method, typed input, parameter variants, output DTO, synthetic worked example and dependency gate. This document does NOT assert 42 implemented Python computations, accepted standards clauses or financial S2.


## 8. Typed MethodParameter Schema Matrix (W2/P1, проектная типизация)

**Требование:** ParameterValueDTO = {parameterCode, logicalType, value, unitCode?, valueState, policyRevisionRef, sourceEvidenceRef?, effectiveRange?}. Каждое имя параметра в §4 имеет указанную ниже логическую типизацию; один параметр может быть REQUIRED или CONDITIONAL по точной MethodVariantRevision. Здесь типы **кандидатны**, не заменяют будущий однозначный IDL/S2. Неизвестный параметр либо изменённый тип запрещён до новой schema revision.

| FEngine code | Все объявленные параметры, типы и единицы |
|---|---|
| HC.SET.04 | weightBasis:CODE; cutoff:CODE; denominatorPolicy:CODE; calendarPolicyRef:REFERENCE |
| HC.SET.05 | nettingRule:CODE; legalApprovalRev:REFERENCE; sameCurrencyPolicy:ISO4217; intendedSettlementBasis:CODE; asOf:LOCAL_DATE |
| HC.SET.07 | averageStockPolicy:CODE; denominatorSalesPolicy:CODE; dayCount:CODE; currency/basis:STRUCT{currencyCode:ISO4217,accountingBasis:CODE} |
| HC.ECL.01 | approach:CODE; cohortPolicyRef:REFERENCE; scenarioWeightRev:REFERENCE; forwardOverlayPolicyRef:REFERENCE; discountEligibility:CODE |
| HC.ECL.02 | defaultWindow:CODE; discountBasis:CODE; PDType:CODE; recoveryTimingRef:REFERENCE |
| HC.ECL.03 | horizon:INTEGER[PERIODS]; survivalRecursion:CODE; scenarioWeightRev:REFERENCE; cashShortfallModelRef:REFERENCE; amortizingExposurePolicy:CODE |
| HC.LOAN.04 | originalEirRev:REFERENCE; accountingCashflowDirection:CODE; interestAccrualPeriod:PERIOD; modificationPolicyRef:REFERENCE; roundingStage:CODE |
| HC.LOAN.05 | modificationType:CODE; originalEirRev:REFERENCE; discountOriginDate:LOCAL_DATE; financialDerecognitionGate:CODE |
| HC.LOAN.06 | earlyDate:LOCAL_DATE; prepaymentAmount:MONEY; earlyFeePolicyRef:REFERENCE; recalcMethod:CODE; discountRateBasis:CODE |
| HC.LOAN.07 | cfadsContractRev:REFERENCE; serviceIncludesFees:BOOLEAN; threshold:RATIO; comparison:CODE; grace/cure policyRef:REFERENCE; zeroServicePolicy:CODE |
| HC.CASH.02 | bucketCalendarRev:REFERENCE; openingCashPolicy:CODE; includeUndrawnFacilities:BOOLEAN; minimumBufferPolicy:CODE |
| HC.CASH.03 | horizon:INTEGER[PERIODS]; cashFloor:MONEY; interpolationPolicy:CODE; nonMonotonicCashHandling:CODE; scenarioProbabilitiesRef:REFERENCE |
| HC.CASH.06 | matchMode:CODE; dateWindow:INTEGER[DAYS]; cashAccountMapRev:REFERENCE; reversalPolicy:CODE; manyToOneRule:CODE |
| HC.CASH.07 | functionalCurrency:ISO4217; presentationCurrency:ISO4217; rateQuoteConvention:CODE; fxCashFlowPolicyRev:REFERENCE; roundingStage:CODE |
| HC.CASH.08 | fundingObjective:CODE; borrowLimit:MONEY; costRate:RATE; availabilityWindow:PERIOD; minimumCash:MONEY |
| HC.DCF.02 | annualDiscountRate:RATE; dayCount:CODE; valuationDate:LOCAL_DATE; cashflowBasis:CODE; allowPreValuationFlows:BOOLEAN |
| HC.DCF.04 | dayCount:CODE; domainMinRate>−1:RATE(>-1); domainMaxRate:RATE; solverTolerance:RATE; rootCompletenessPolicy:CODE; rootSearchStatus:CODE |
| HC.DCF.05 | taxOnOperatingProfitPolicy:CODE; depreciationNonCashScope:CODE; capexScope:CODE; workingCapitalPolicy:CODE; financingExclusion:CODE |
| HC.DCF.06 | cfadsBase:CODE; interestTaxTreatmentPolicy:CODE; debtDrawsCash:BOOLEAN; principalPaymentsCash:BOOLEAN; debtFeesEligibility:CODE |
| HC.DCF.07 | terminalMethod:CODE; waccRate:RATE; growthRate:RATE; terminalYear:INTEGER[YEARS]; midyearConvention:CODE; currency:ISO4217 |
| HC.DCF.08 | valuationMethod:CODE; netDebtPolicyRef:REFERENCE; bridgeAdjustmentsRef:REFERENCE; Ke:RATE; currency:ISO4217 |
| HC.DCF.09 | axesCodes:LIST<CODE>; cellBudget:INTEGER[CELL_COUNT]; monotonicityNotAssumed:BOOLEAN; scenarioAxisPolicy:CODE; modelHash:HASH |
| HC.ACC.01 | cashflowClassificationPolicy:CODE; assetLiabilityEquitySigns:CODE; retainedEarningsPolicy:CODE; openingBalanceRef:REFERENCE; taxPolicyRef:REFERENCE |
| HC.ACC.02 | consolidationPerimeterRef:REFERENCE; matchTolerance:CODE; intercompanyUnrealizedProfitRef:REFERENCE; groupCurrencyPolicy:ISO4217 |
| HC.ACC.04 | matchingKeys:LIST<CODE>; asOf:LOCAL_DATE; dateTolerance:INTEGER[DAYS]; currencyConversionPolicyRef:REFERENCE; residualMateriality:MONEY |
| HC.ACC.06 | lesseeEligibility:CODE; discountRateRev:REFERENCE; paymentTiming:CODE; extensionOptionEvidence:REFERENCE; reassessmentPolicy:CODE; leaseTerm:INTEGER[PERIODS] |
| HC.STOCK.03 | valuationMethod:CODE; itemEligibilityPolicyRef:REFERENCE; costCurrency:ISO4217; transferReturnPolicy:CODE |
| HC.STOCK.04 | nrvEligibleItemsRef:REFERENCE; expectedSellingPricePolicy:CODE; completionCostPolicy:CODE; sellingCostPolicy:CODE; reversalCeilingPolicy:CODE |
| HC.STOCK.06 | stockInterval:PERIOD; unitConversionPolicy:CODE; transferNettingPolicy:CODE; cutOffPolicy:CODE |
| HC.ASSET.01 | method:CODE; lifeRevisionPolicy:CODE; convention:CODE; suspended/disposal rule:CODE |
| HC.ASSET.02 | revaluationModelRef:REFERENCE; fairValueEvidenceRef:REFERENCE; ociBalanceRef:REFERENCE; reversalLimit:MONEY; impairmentClassificationRef:REFERENCE |
| HC.ASSET.04 | asOf:LOCAL_DATE; componentAggregationPolicy:CODE; duplicateEventGuard:CODE; currencyValuationPolicy:ISO4217 |
| HC.ASSET.07 | capitalizationPolicyRef:REFERENCE; cashVsAccrualMode:CODE; delayHandling:CODE; periodCalendarRef:REFERENCE; committedBudgetScope:CODE |
| HC.COST.01 | allocationStages:LIST<CODE>; driverZeroPolicy:CODE; unallocatedResidualPolicy:CODE; entityScope:CODE; roundingStage:CODE |
| HC.COST.02 | wasteRatePolicy:CODE; conversionPolicy:CODE; effectivePriceDate:LOCAL_DATE; laborOverheadVariant:CODE; resourceInclusionRule:CODE |
| HC.COST.03 | attributionVariant:CODE; newSkuPolicy:CODE; missingSkuPolicy:CODE; aggregationPolicy:CODE |
| HC.COST.06 | measurementStandardRevision:REFERENCE; unitConversionPolicy:CODE; overheadMarginPolicy:CODE; taxEscalationVersion:CODE; contractCurrency:ISO4217 |
| HC.COST.07 | EACVariant:CODE; noCompletionBeyondBACPolicy:CODE; zeroDenominator:CODE |
| HC.COST.08 | flexBudgetVariant:CODE; varianceSign:CODE; driversUnitRev:REFERENCE |
| HC.PLAN.01 | rollingHorizon:INTEGER[PERIODS]; fiscalCalendarRef:REFERENCE; forecastCutover:LOCAL_DATE; modelDependencyDAGRef:REFERENCE; latestActualRevision:REFERENCE |
| HC.PLAN.07 | dependencyGraphRev:REFERENCE; scenarioRevision:REFERENCE; accountingRecognitionRules:CODE; cashFlowClassPolicy:CODE; balancingPolicy:CODE |
| HC.RISK.04 | shockApplicationOrder:CODE; scenarioWeight:RATE[0..1]; riskHorizon:INTEGER[PERIODS]; FXShockRef:REFERENCE; cashFloor:MONEY; liquidityConstraintPolicy:CODE |

**Type aliases and validation rules:**
- CODE = versioned allowlisted ENUM; REFERENCE = immutable scoped ID with required SHA/source evidence; HASH = canonical SHA-256 hex.
- RATE = Decimal fraction with dimension ONE (0.10 means 10%), unless separately constrained > −1 for rate-root domain; probability RATE is [0,1]; RATIO distinct but shares physical dimension ONE.
- MONEY = Decimal string with ISO4217 currency, time and accounting basis; DATE = LOCAL_DATE; INTEGER[DAYS]/[PERIODS]/[COUNT] has explicit unit; MONEY_PER_UNIT in dataset schemas = struct{money:Decimal,currency:ISO4217,denominatorUnit:CODE}.
- STRUCT / LIST<...> demand their own exact nested versioned schema. Free-form maps, arbitrary Python names or expressions are prohibited.
- Parameters with type CODE but carrying a numerical value by a future methodology decision MUST be revised to a numeric logical type prior to implementation; no silent coercion. Source authorization, effective param values and their SHA belong to the immutable execution binding.
- These assignments are architectural **initial type candidates**, not final finance-approved method metadata.