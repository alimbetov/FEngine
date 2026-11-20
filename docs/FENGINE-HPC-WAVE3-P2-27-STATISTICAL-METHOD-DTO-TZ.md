# FEngine HPC-W3 — ТЗ: 27 показателей P2, статистические модели, оптимизация и регуляторные расчёты

**Document ID:** FENGINE-HPC-W3-P2-TZ-V1  
**Date:** 2026-11-20  
**Status:** REQUIREMENTS_DRAFT / MATH_AND_STATISTICAL_REVIEW_REQUIRED / NOT_IMPLEMENTED  
**Authority:** FENGINE_MASTER_SPEC.md v0.4 + FENGINE-HPC-WAVE1-14 v1.1 + FENGINE-HPC-WAVE2-P1-42 v1.0; all 83 models execute under one Python Calculation Hub, no independent worker/service per indicator.  
**Regulatory caution:** IFRS/IAS and Kazakhstan regulations have variant/date/entity-specific applicability; this document defines candidate methods, not attested statutory calculations. Numeric examples are hand-specified synthetic arithmetic fixtures requiring independent review.

## 1. Architecture, semantics and 27-model scope

- Shared InputBatchDTO/CalculationSession/Job states and scoped idempotencyKey; every task has own immutable TaskCode, exact method revision, input/params SHA, resultSet schema and source lineage.
- Typed numeric fields: MONEY=canonical Decimal string + ISO4217 currency; RATE=Decimal unit fraction; RATIO=Decimal; QUANTITY=Decimal+unit; LOCAL_DATE, PERIOD, INSTANT, REFERENCE, ENUM, BOOLEAN, INT64, MATRIX, POINT_SERIES and VECTOR are versioned typed arrays, not arbitrary JSON payloads.
- Probability fields RATE must be within [0,1], scenario probability weights sum to 1 within policy tolerance; PD conditional vs marginal must be tagged; exposure, cash and loss cannot silently convert currencies/discount dates.
- Statistical model results must include approved distribution method, sample window, missingness policy, random generator revision/seed, confidence/sampling error where meaningful; Monte Carlo precision is different from exact-money final rounding.
- Optimizers return objective, admissible decision vector, capacity violations, solver status, feasibility gap and any unproven optimality gap; a locally feasible proposal must not claim global optimality.
- ResultSet shape variants extend Wave-1: GROUPED, AGGREGATE, TIME_SERIES, ROW_ALIGNED, EVENT_SERIES, ROOT_SET, SCENARIO_MATRIX, DISTRIBUTION, OPTIMIZATION_PLAN; new variants require explicit output schema revision.
- Python prototype is a mathematical reference and protocol simulator; financial S2 and production admission are **separate**. Rust accelerator selection only after correctness and full-path benchmarks.
- FIN Analyzer source refs are suggestive and do not imply actual field coverage or a formally qualified IFRS/S2 method.

## 2. Additional input DTO schemas D55–D81

Fields with (!) REQUIRED and (?) CONDITIONAL. Every dataset has rowCount, rowKeys[], per-column states[], sourceRevisionRef/sha, tenant scope, appropriate asOf/period/currency metadata. Input arrays must be immutable and aligned by declared keys. Rules such as per-observation currency/units must be pinned by schema.


### D55. PD_HAZARD_OBSERVATION

instrumentKey:REF!; period:PERIOD!; cohortKey:CODE!; atRiskCount:INTEGER!; defaultCount:INTEGER!; censoredCount:INTEGER?; scenarioKey:REF!; riskGrade:CODE?; evidenceRef:REF!.


### D56. LGD_RECOVERY_PATH

instrumentKey:REF!; defaultDate:LOCAL_DATE!; eadAtDefault:MONEY!; recoveryDate:LOCAL_DATE!; grossRecovery:MONEY!; recoveryCost:MONEY!; discountRate:RATE!; securedAssetRef:REF?; evidenceRef:REF!.


### D57. EAD_CREDIT_LINE

instrumentKey:REF!; asOf:LOCAL_DATE!; drawnAmount:MONEY!; undrawnCommitted:MONEY!; ccf:RATE!; facilityLimit:MONEY!; projectedDraw:MONEY?; scheduledRepayment:MONEY?; defaultScenarioRef:REF!.


### D58. CREDIT_STAGE_MIGRATION

instrumentKey:REF!; originStage:CODE!; destinationStage:CODE!; effectiveAt:LOCAL_DATE!; openingAllowance:MONEY!; closingAllowance:MONEY?; transferReason:CODE!; decisionEvidenceRef:REF!.


### D59. FOREIGN_OPERATION_LINE

entityKey:REF!; functionalCurrency:ISO4217!; presentationCurrency:ISO4217!; statementType:CODE!; lineCode:CODE!; period:PERIOD!; amount:MONEY!; rateType:CODE!; rateRevisionRef:REF!; ownershipPct:RATE?.


### D60. TAX_TEMP_DIFFERENCE

taxEntityKey:REF!; assetLiabilityKey:REF!; asOf:LOCAL_DATE!; carryingAmount:MONEY!; taxBase:MONEY!; enactedTaxRate:RATE!; taxCharacter:CODE!; recognitionEligibilityRef:REF!; reversalPeriod:PERIOD?.


### D61. EQUITY_MOVEMENT

entityKey:REF!; period:PERIOD!; eventKey:REF!; eventType:ENUM(PROFIT; OCI; DIVIDEND; ISSUE; BUYBACK; OTHER)!; signedAmount:MONEY!; recognitionBasis:CODE!; sourceRevisionRef:REF!.


### D62. STOCK_AGE_COHORT

itemKey:REF!; lotKey:REF!; asOf:LOCAL_DATE!; receiptDate:LOCAL_DATE!; onHandQty:QUANTITY!; unitCost:MONEY_PER_UNIT!; saleableStatus:CODE!; evidenceRef:REF!.


### D63. REPLENISHMENT_POSITION

skuKey:REF!; warehouseKey:REF!; asOf:LOCAL_DATE!; stockOnHand:QUANTITY!; stockOnOrder:QUANTITY!; reservedQty:QUANTITY!; leadTimeDays:INTEGER!; dailyDemand:QUANTITY!; safetyQty:QUANTITY!; moq:QUANTITY?; capacityQty:QUANTITY?.


### D64. CGU_RECOVERABLE_VALUE

cguKey:REF!; asOf:LOCAL_DATE!; carryingAmount:MONEY!; fairValueLessDisposalCost:MONEY?; forecastCashflow:MONEY!; flowDate:LOCAL_DATE!; discountRate:RATE!; currency:ISO4217!; policyRef:REF!.


### D65. ASSET_DISPOSAL_EVENT

assetKey:REF!; disposalDate:LOCAL_DATE!; grossProceeds:MONEY!; directDisposalCosts:MONEY!; carryingAmount:MONEY!; derecognitionRef:REF!; disposalType:CODE!.


### D66. ASSET_MAINTENANCE_RULE

assetKey:REF!; componentKey:REF!; lastServiceDate:LOCAL_DATE!; serviceIntervalDays:INTEGER!; plannedCost:MONEY!; runtimeHours:QUANTITY?; wearModelRevision:REF?; priorityCode:CODE!.


### D67. PRODUCT_BREAK_EVEN

productKey:REF!; unitPrice:MONEY_PER_UNIT!; variableUnitCost:MONEY_PER_UNIT!; salesMix:RATE!; fixedCostPoolKey:REF!; fixedCost:MONEY!; minimumBatchQty:INTEGER?; unitCode:CODE!.


### D68. COST_ESCALATION_CURVE

projectKey:REF!; costObjectKey:REF!; baseAmount:MONEY!; baseDate:LOCAL_DATE!; forecastDate:LOCAL_DATE!; escalationRate:RATE!; periodCount:DECIMAL!; contingencyAmount:MONEY?; priceIndexRevision:REF?.


### D69. SEASONAL_DEMAND_HISTORY

skuKey:REF!; period:PERIOD!; observedDemand:QUANTITY!; seasonKey:CODE!; daysExposed:INTEGER!; stockoutCensoring:BOOLEAN!; sourceRevisionRef:REF!.


### D70. DEMAND_LEAD_TIME_DISTRIBUTION

skuKey:REF!; warehouseKey:REF!; meanDailyDemand:QUANTITY!; stdDailyDemand:QUANTITY!; meanLeadTimeDays:DECIMAL!; stdLeadTimeDays:DECIMAL?; targetServiceLevel:RATE!; distributionRevision:REF!.


### D71. CAPACITY_SLOT

resourceKey:REF!; date:LOCAL_DATE!; availableHours:QUANTITY!; requiredHours:QUANTITY!; setupHours:QUANTITY?; skillCode:CODE!; calendarRevisionRef:REF!.


### D72. PROJECT_DEPENDENCY_EDGE

projectKey:REF!; activityKey:REF!; predecessorKey:REF?; durationDays:DECIMAL!; lagDays:DECIMAL?; calendarRef:REF!; dependencyType:ENUM(FS; SS; FF; SF)!; evidenceRef:REF!.


### D73. PAYROLL_EMPLOYMENT_EVENT

employeeRef:REF!; effectiveDate:LOCAL_DATE!; effectiveTo:LOCAL_DATE?; monthlyGrossPay:MONEY!; fte:RATIO!; benefitRate:RATE!; taxPayrollPolicyRef:REF!; costCenterRef:REF!; eventType:CODE!.


### D74. CAPEX_PORTFOLIO_CANDIDATE

projectKey:REF!; period:PERIOD!; capexRequired:MONEY!; projectNpv:MONEY!; mutuallyExclusiveGroup:REF?; earliestStart:LOCAL_DATE?; deadline:LOCAL_DATE?; dependencyProjectRef:REF?; riskBudget:MONEY?.


### D75. STOCHASTIC_FACTOR_DRAW

simulationRunKey:REF!; drawIndex:INT64!; scenarioKey:REF!; driverCode:CODE!; driverValue:DECIMAL!; driverUnit:CODE!; prngVersion:CODE!; seed:INT64!; sourceDistributionRevision:REF!.


### D76. LOSS_OBSERVATION

portfolioKey:REF!; scenarioOrObservationKey:REF!; eventDate:LOCAL_DATE!; lossAmount:MONEY!; weight:RATE?; sourceRevisionRef:REF!; censoringPolicy:CODE?.


### D77. MACRO_CREDIT_FACTOR

scenarioKey:REF!; period:PERIOD!; macroFactorCode:CODE!; value:DECIMAL!; unitCode:CODE!; probability:RATE!; calibrationRevision:REF!; policyRevisionRef:REF!.


### D78. CORRELATED_SHOCK_FACTOR

scenarioKey:REF!; period:PERIOD!; factorCode:CODE!; shock:DECIMAL!; unitCode:CODE!; correlationMatrixRevision:REF!; calibrationEvidenceRef:REF!.


### D79. SIMULATION_DESIGN

simulationKey:REF!; scenarioFamily:CODE!; sampleCount:INTEGER!; seed:INT64!; prngRevision:REF!; distributionRevision:REF!; dependencyRevision:REF!; stoppingCriterionRef:REF!.


### D80. KZ_GESV_CASH_EVENT

loanKey:REF!; eventDate:LOCAL_DATE!; eventKind:ENUM(LOAN_DISBURSEMENT; CLIENT_PAYMENT; BANK_FEE; THIRD_PARTY_FEE)!; amount:MONEY!; currency:ISO4217!; payerPayee:CODE!; regulatoryInclusionFlag:CODE!; legalEvidenceRef:REF!; contractRevisionRef:REF!.


### D81. RISK_MODEL_SCORE

instrumentKey:REF!; asOf:LOCAL_DATE!; riskFactorCode:CODE!; factorValue:DECIMAL!; factorUnit:CODE!; calibrationVersion:REF!; classificationDecisionRev:REF!; sourceRevisionRef:REF!.


## 3. Individual model specifications — 27 P2

**TaskCode rule:** W3.<family>.<number>.V1, immutable allowlisted key. Every task has version-pinned source schema, parameter revision, method revision, Formula/Algorithm Manifest SHA, numeric policy and output schema.

**Statistical acceptance rule:** an arithmetic example may check a candidate equation, but cannot validate its actuarial, macroeconomic or statistical calibration. Require separate sample-quality tests, independent benchmarks, uncertainty/censoring/selection bias analysis, time-based out-of-sample validation and finance/credit-risk S2 where applicable.


### 01. HC.ECL.04 — Срочная структура PD / hazard curves

**TaskCode:** W3.ECL.04.V1 · **FIN candidate:** A02; SF-K01 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D55 PD_HAZARD_OBSERVATION; D81 risk score when model calibrated; D21 scenarios |
| Explicit parameters and variants | hazardEstimator=BINOMIAL_MLE \| SURVIVAL_MODEL, censoringPolicyRef, cohortSegmentation, smoothing, scenarioProbabilityPolicy; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For elementary uncensored period q_t=defaults_t/atRisk_t; S_t=Π_(j≤t)(1−q_j); marginalPD_t=S_(t−1)q_t; cumulativePD_t=1−S_t. Model with censoring/competing risks requires separate estimation variant |
| Output values in common results[].rows[].values[] | CONDITIONAL_PD:RATE, MARGINAL_PD:RATE, CUMULATIVE_PD:RATE, SURVIVAL:RATE; TIME_SERIES |
| Independently checkable synthetic arithmetic | q1=0.10 and q2=0.20 ⇒ survival at 2=0.9×0.8=0.72; cumulative PD=0.28 |
| Negative cases / hard gates | negative sample size; default count>at-risk, censoring ignored, sparse cohort unstable, cohort drift |
| Prerequisite DAG / Calculation Session reuse | HC.ECL.02/.03; D55/D81 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 02. HC.ECL.05 — LGD по временны́м путям взысканий

**TaskCode:** W3.ECL.05.V1 · **FIN candidate:** A02; C05; SF-K01 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D56 dated recovery cash and costs; D19 EAD at default with consistent currency |
| Explicit parameters and variants | recoveryEligibility, recoveryCostTreatment, recoveryDiscountOrigin, discountRateSource, collateralSeniority, noRecoveryState; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | NetPVRecovery=Σ(recoveryCash−recoveryCosts)/(1+r)^yearFraction; loss=EAD−NetPVRecovery; LGD=loss/EAD for permitted nonnegative exposure; disputed overrecoveries require classification rather than clipping by default |
| Output values in common results[].rows[].values[] | NET_PV_RECOVERY:MONEY, LOSS_AMOUNT:MONEY, LGD:RATE; TIME_SERIES/AGGREGATE |
| Independently checkable synthetic arithmetic | EAD100, recovery60 and recovery costs5 after one year, discount r0.10 ⇒ netPV50; LGD0.5 |
| Negative cases / hard gates | EAD zero; recoveries before default wrongly dated; unconfirmed collateral; percentage bounds forced silently |
| Prerequisite DAG / Calculation Session reuse | HC.ECL.04; D56; recovery S2 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 03. HC.ECL.06 — EAD с будущими траншами/погашениями

**TaskCode:** W3.ECL.06.V1 · **FIN candidate:** A02; C05; A05 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D57 drawn/undrawn credit limits with conditional conversion factor + D09 future draws/repayments |
| Explicit parameters and variants | ccfRevision, exposureDate, expectedRepaymentPolicy, drawableEligibility, undrawnCommitmentState, collateralNettingPolicy; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For simple approved facility EAD_t=max(0, projectedDrawn_t)+CCF_t×eligibleUndrawn_t; contractual limit/commitment and expected credit conversion must be evidenced, not assume undrawn always fully drawn |
| Output values in common results[].rows[].values[] | EAD_BY_DATE:MONEY, EXPECTED_DRAW:MONEY, UNDRAWN_EXPOSURE:MONEY; TIME_SERIES |
| Independently checkable synthetic arithmetic | Current drawn40, undrawn100, approved CCF0.30 => EAD70 KZT, no repayments |
| Negative cases / hard gates | CCF outside [0,1] without separate model; double-count future draws; suspended facility incorrectly drawable |
| Prerequisite DAG / Calculation Session reuse | HC.LOAN.02; D57; ECL calibration |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 04. HC.ECL.07 — Миграция стадий кредита и резервов

**TaskCode:** W3.ECL.07.V1 · **FIN candidate:** A02; C01; F01 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D58 stage transition events + D19 balances + D81 risk decisions, vintage/date |
| Explicit parameters and variants | stageTransitionPolicyRev, SICRRuleRevision, POCIClassification, forwardScenarios, reconciliationPolicy; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Build instrument-level old→new stage movement, aggregate transfer matrix and independently reconcile opening allowance+new provisions−releases−writeoffs±FX = closing allowance; stage migration alone does not determine provision |
| Output values in common results[].rows[].values[] | STAGE_TRANSITION_COUNT:INTEGER, STAGE_EXPOSURE:MONEY, ALLOWANCE_ROLLFORWARD:MONEY, RECONCILIATION_RESIDUAL:MONEY; GROUPED |
| Independently checkable synthetic arithmetic | 100 instruments stage1 with 20 transferred to stage2 ⇒ 80 remain stage1, 20 are transfers; reserve amount still needs ECL model |
| Negative cases / hard gates | SICR decision absent; stage3 misclassified; movement count mistaken for credit loss; unverified opening reserve |
| Prerequisite DAG / Calculation Session reuse | HC.ECL.02/.03; D58/D81 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 05. HC.LOAN.08 — ГЭСВ Казахстана — нормативный расчёт

**TaskCode:** W3.LOAN.08.V1 · **FIN candidate:** C05; A05 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D80 contract dated borrower/bank disbursements+all legally included fees; D06 exact contract/legal entity type |
| Explicit parameters and variants | regulationId=KZ-ARRFR-2026-04-03-N44, effectiveDate, borrowerType=LEGAL_PERSON \| NATURAL_PERSON, includedCommissionRulesRev, dateBase, rootTolerance, solverDomain, resultRounding=2_DECIMAL_PERCENT_PLACES; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For dated eligible cash flows solve present value of borrower disbursements net initial eligible fees equal PV of eligible borrower repayments/fees on legally specified day basis, following exact law/p11 formula and amendments as of calculation date. Never use IFRS9 EIR fee eligibility instead. Report rate as fraction and separately display % rounded under p23 |
| Output values in common results[].rows[].values[] | KZ_GESV:RATE, KZ_GESV_DISPLAY:PERCENT, NPV_RESIDUAL:MONEY, INCLUDED_FEE_TOTAL:MONEY, RULE_VERSION:CODE; AGGREGATE |
| Independently checkable synthetic arithmetic | Simplified 365-day loan D=100 KZT, initial eligible fee k=2 KZT, one client repayment P=110 KZT exactly day365: net98, effective annual r=110/98−1≈0.1224489796 (12.24% displayed to hundredths) under stated simple facts |
| Negative cases / hard gates | regulation wrong date/loan class, third-party fee missing, exclusion of ineligible penalties, credit line assumptions missing, APR conflated with EIR |
| Prerequisite DAG / Calculation Session reuse | HC.LOAN.01/.02; D80; regulatory legal review of №44 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 06. HC.ACC.03 — Валютная трансляция консолидации

**TaskCode:** W3.ACC.03.V1 · **FIN candidate:** F08;C14 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D59 foreign operation lines + D29 FX rates; equity historical rate, ownership and OCI movement |
| Explicit parameters and variants | functionalCurrency, presentationCurrency, closingVsTransactionRatePolicy, averageRateEligibility, hyperinflationGate, CTAclassificationRef; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Translate foreign operation assets/liabilities at closing FX, income/expenses at transaction rates or appropriately approved approximate averages; equity/OCI and CTA through qualified consolidation bridge, no generic spot multiplication for every line |
| Output values in common results[].rows[].values[] | TRANSLATED_LINE:MONEY, CTA_MOVEMENT:MONEY, FX_RATE_APPLIED:DECIMAL, BLOCKED_RATE_LINES:INTEGER; GROUPED |
| Independently checkable synthetic arithmetic | Asset100 USD at closing500 KZT/USD → 50,000 KZT; income10 USD at supported transaction495 → 4,950 KZT. CTA cannot be inferred from only these two rows |
| Negative cases / hard gates | wrong quote orientation, presentation currency match, historical equity rate absent, IAS29 applicability ignored |
| Prerequisite DAG / Calculation Session reuse | HC.ACC.01/.02; D59,D29; IAS21 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 07. HC.ACC.05 — Отложенные налоги по временным разницам

**TaskCode:** W3.ACC.05.V1 · **FIN candidate:** F01;F02;F05 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D60 carrying vs tax base per asset/liability + enacted rate/time of recovery and recognition evidence |
| Explicit parameters and variants | taxJurisdiction, deferredTaxRateRev, carryforwardEligibility, initialRecognitionExceptions, offsetEligibility, recoveryDatePolicy; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For a simple taxable temporary difference on an asset DTL=max(0,carrying−taxBase)×enactedRate when eligible. Deductible differences create DTA only after qualified recognition conditions and exceptions, separate tax effect on OCI/PL |
| Output values in common results[].rows[].values[] | DTL:MONEY, DTA:MONEY, TEMP_DIFFERENCE:MONEY, TAX_EFFECT_CLASS:CODE; ROW_ALIGNED |
| Independently checkable synthetic arithmetic | Asset carrying120, tax base100, applicable enacted tax rate0.20 => DTL4 KZT |
| Negative cases / hard gates | tax base missing, enacted rate unknown, DTA recognition unjustified, mandatory exceptions overlooked |
| Prerequisite DAG / Calculation Session reuse | HC.ACC.01; D60; IAS12 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 08. HC.ACC.07 — Мост движения капитала и совокупного результата

**TaskCode:** W3.ACC.07.V1 · **FIN candidate:** F04;F01;F02 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D61 equity movement event ledger + D33 PL/BS line revisions |
| Explicit parameters and variants | profitOrOCIClassification, dividendsPayableVsPaidPolicy, restatementRevision, ownershipNCIAllocation, asOf; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | EndingEquity=OpeningEquity+recognizedProfit+approvedOCI+ownerContributions−distributions±other qualified movements; link reported income and OCI without treating dividends as operating expense |
| Output values in common results[].rows[].values[] | ENDING_EQUITY:MONEY, OCI_MOVEMENT:MONEY, OWNER_DISTRIBUTIONS:MONEY, RECONCILIATION_RESIDUAL:MONEY; TIME_SERIES |
| Independently checkable synthetic arithmetic | Equity opening100, profit20, OCI+5, dividends10 => ending115 KZT, no other flows |
| Negative cases / hard gates | profit double-count OCI, own shares sign, minority ownership ignored, date mismatch |
| Prerequisite DAG / Calculation Session reuse | HC.ACC.01; D61 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 09. HC.STOCK.05 — Старение и риск обесценения складских остатков

**TaskCode:** W3.STOCK.05.V1 · **FIN candidate:** C03;DF-STK-04;A03 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D62 on-hand quantity per lot with inbound date, item cost and saleable status; D37 NRV evidence for write-down |
| Explicit parameters and variants | ageBucketBoundaries, lastMovementVsReceiptAge, slowMovingPolicy, nrvEvidencePolicy, asOf; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Compute daysInStock and quantities/values by age buckets; flag high-age inventory as analytical risk only. Actual IAS2 write-down requires separately verified cost vs NRV, not automatic age multiplier |
| Output values in common results[].rows[].values[] | AGING_QTY:QUANTITY, AGING_VALUE:MONEY, SLOW_STOCK_SHARE:RATIO, NRV_REVIEW_STATUS:CODE; GROUPED |
| Independently checkable synthetic arithmetic | 10 units aged40 days + 5 units aged100 days, threshold90 → slow share5/15=0.3333333 by quantity |
| Negative cases / hard gates | multiple receipts date unknown, obsolete status unsupported, age used directly as loss%, valuation not at same asOf |
| Prerequisite DAG / Calculation Session reuse | HC.STOCK.04; D62/D37 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 10. HC.STOCK.07 — Оптимизация пополнения с ограничениями

**TaskCode:** W3.STOCK.07.V1 · **FIN candidate:** DF-STK-05;MGT-03 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D63 inventory position, demand and safety stock; D70 distribution if probability model chosen |
| Explicit parameters and variants | reorderPolicy=ROP \| SERVICE_LEVEL, lotSizing=CONTINUOUS \| MOQ, leadTime, serviceLevel, capacityConstraint, inventoryPositionDefinition; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | ROP=expected demand during lead time+safety stock; inventoryPosition=onHand+eligibleOnOrder−reservedQty; proposedReplenishment=max(0,ROP−inventoryPosition), adjust MOQ and capacity through feasible optimization |
| Output values in common results[].rows[].values[] | REORDER_POINT:QUANTITY, REPLENISHMENT_QTY:QUANTITY, FEASIBILITY:CODE, EXPECTED_SHORTFALL:QUANTITY; OPTIMIZATION_PLAN |
| Independently checkable synthetic arithmetic | ROP70 units, onHand30,onOrder10,reserved0 ⇒ recommended order30 units, no MOQ/capacity restrictions |
| Negative cases / hard gates | negative lead time; false stock on order; MOQ/capacity infeasible; service level without uncertainty model |
| Prerequisite DAG / Calculation Session reuse | HC.STOCK.06; D63/D70 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 11. HC.ASSET.03 — VIU и impairment по CGU

**TaskCode:** W3.ASSET.03.V1 · **FIN candidate:** C04;F05;A04 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D64 CGU carrying, forward operating cash flows, FVLCD and discount rate, compatible currency; D39 components |
| Explicit parameters and variants | cashflowHorizon, terminalPolicy, discountRateConsistency, VIU_RiskAdjustmentPolicy, recoverableAmountMethod, impairmentAllocationOrder; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | VIU=Σ appropriate future in-use cashflows/(1+r)^t under IAS36 policy; recoverableAmount=max(VIU,FVLCD), impairment=max(0,carrying−recoverableAmount) for eligible CGU. Allocation across CGU assets requires separate IAS36 constraints |
| Output values in common results[].rows[].values[] | VIU:MONEY, RECOVERABLE_AMOUNT:MONEY, IMPAIRMENT_LOSS:MONEY, ALLOCATION_STATUS:CODE; AGGREGATE |
| Independently checkable synthetic arithmetic | CGU carrying100, next-year eligible CF100, discount10%, FVLCD85 ⇒ VIU90.9090909, impairment9.0909091 KZT |
| Negative cases / hard gates | interest/tax risk double count, inconsistent terminal rate, missing FVLCD eligibility, impairment allocation ignores goodwill |
| Prerequisite DAG / Calculation Session reuse | HC.ASSET.04; D64; IAS36 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 12. HC.ASSET.05 — Финансовый результат выбытия ОС

**TaskCode:** W3.ASSET.05.V1 · **FIN candidate:** C04;DF-AST-03;A04 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D65 proceeds/expenses and verified carrying at disposal from D39/D40 |
| Explicit parameters and variants | disposalRecognitionPolicy, transactionCostsEligibility, saleLeasebackGate, derecognitionDate; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | NetProceeds=grossProceeds−eligibleDirectDisposalCosts; disposalGainLoss=NetProceeds−carryingAtDisposal; derecognize cost/depr at exact event date |
| Output values in common results[].rows[].values[] | DISPOSAL_GAIN_LOSS:MONEY, NET_PROCEEDS:MONEY, DERECOGNIZED_CARRYING:MONEY; EVENT_SERIES |
| Independently checkable synthetic arithmetic | Proceeds120, selling costs5, carrying100 ⇒ gain15 KZT |
| Negative cases / hard gates | sale/leaseback misclassified, disposal date wrong, partial disposal not supported, double gain entry |
| Prerequisite DAG / Calculation Session reuse | HC.ASSET.04; D65 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 13. HC.ASSET.06 — План ремонтов и жизненного цикла компонентов

**TaskCode:** W3.ASSET.06.V1 · **FIN candidate:** C04;P05;DF-AST-01 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D66 service intervals/cost, approved life-cycle policy, D41 funded commitments optional |
| Explicit parameters and variants | maintenanceStrategy=TIME_BASED \| HOURS_BASED, degradationModelRef, businessCalendarRef, planningHorizon, sparePartsConstraint; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Deterministic version: nextScheduledService = lastServiceDate+serviceIntervalDays; build event-dated planned maintenance costs across horizon; probabilistic failure hazard requires evidence and another method variant |
| Output values in common results[].rows[].values[] | NEXT_SERVICE_DATE:LOCAL_DATE, PLANNED_MAINTENANCE_COST:MONEY, LATE_BY_DAYS:INTEGER; TIME_SERIES |
| Independently checkable synthetic arithmetic | Last service 2026-01-01, interval100 days → next due 2026-04-11; one planned service cost20 KZT |
| Negative cases / hard gates | interval zero, date offset assumptions, calendar mismatch, predictive wear invented from no observations |
| Prerequisite DAG / Calculation Session reuse | D66; HC.ASSET.07 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 14. HC.COST.04 — Точка безубыточности продуктового микса

**TaskCode:** W3.COST.04.V1 · **FIN candidate:** C07;C08;P02 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D67 unit selling price/variable cost/target mix and common fixed cost scope |
| Explicit parameters and variants | mixDefinition=UNIT_SHARES, discreteBatchRule, productContributionPolicy, taxFixedTreatment, feasibilityConstraints; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | WeightedCM=Σ_mixShare_i×(price_i−unitVariableCost_i); continuous BE_units=fixedCost/WeightedCM if >0. Discrete mixed package requires integer quantities honoring mix and min batches |
| Output values in common results[].rows[].values[] | BEP_UNITS:QUANTITY, WEIGHTED_CM:MONEY_PER_UNIT, MIN_FEASIBLE_BUNDLE:INTEGER; OPTIMIZATION_PLAN |
| Independently checkable synthetic arithmetic | Fixed100; mix 60% of unit margin5 and 40% margin10 → CM7, continuous BE14.2857 units; minimum integer mix bundle of 3:2 is 15 units (contribution105) |
| Negative cases / hard gates | CM<=0; incompatible product units, fractional package asserted as physical units, mix weights not1 |
| Prerequisite DAG / Calculation Session reuse | D67; HC.COST.03 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 15. HC.COST.05 — Инфляционная эскалация стоимости и contingency

**TaskCode:** W3.COST.05.V1 · **FIN candidate:** SF-F02;P08;CST-10 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D68 time-based cost curve and approved index, project risk/scenario optional |
| Explicit parameters and variants | priceIndexVariant=FIXED_RATE \| EXTERNAL_INDEX, compoundingPeriod, contingencyPolicyRef, baseDate, excludedTax; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | EscalatedCost=baseCost×(1+escalationRate)^periods for stated fixed periodic rate. Contingency cost is separate approved fixed or probability-based provision, never automatically lumped with price escalation |
| Output values in common results[].rows[].values[] | ESCALATED_COST:MONEY, ESCALATION_DELTA:MONEY, CONTINGENCY:MONEY, TOTAL_IF_INCLUDED:MONEY; TIME_SERIES |
| Independently checkable synthetic arithmetic | Base100, annual escalation5%, two years ⇒ escalated110.25 KZT, increase10.25 |
| Negative cases / hard gates | negative growth beyond domain, double escalation with nominal rates, risk reserve incorrectly treated as certainty |
| Prerequisite DAG / Calculation Session reuse | D68; HC.COST.06 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 16. HC.PLAN.02 — Прогноз спроса с сезонностью

**TaskCode:** W3.PLAN.02.V1 · **FIN candidate:** DF-SAL-01;C07;P02 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D69 demand history and season markers, D63 stockouts and D75 optional distribution inputs |
| Explicit parameters and variants | forecastMethod=SEASONAL_NAIVE \| MULTIPLICATIVE_INDEX \| STATE_SPACE, horizon, leakagePolicy, missingPeriods, outlierPolicy, hierarchyReconciliation; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Simple model forecast_demand = qualified deseasonalized baseline×seasonal index, with future index measured only from training periods. Report actual-vs-predicted, interval only if calibrated errors available |
| Output values in common results[].rows[].values[] | DEMAND_FORECAST:QUANTITY, FORECAST_ERROR:QUANTITY, PI_LOWER/UPPER:QUANTITY?; TIME_SERIES |
| Independently checkable synthetic arithmetic | Baseline forecast100 units, independently estimated next-season multiplier1.2 ⇒ predicted120 units |
| Negative cases / hard gates | censored sales due to stockouts, train/test leak, non-integer service units, uncalibrated interval |
| Prerequisite DAG / Calculation Session reuse | D69; D63; supply forecast S2 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 17. HC.PLAN.03 — Вероятностный страховой запас

**TaskCode:** W3.PLAN.03.V1 · **FIN candidate:** DF-STK-05;MGT-03 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D70 daily demand distribution and lead time; D63 policy position |
| Explicit parameters and variants | distribution=NORMAL_APPROX \| EMPIRICAL, zQuantileMethod, leadTimeVariancePolicy, serviceMetric=CYCLE_SERVICE \| FILL_RATE; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For constant lead time L and iid daily demand with σd, approximate safetyStock=z×σd×sqrt(L); ROP=μd×L+safetyStock. Stochastic lead time requires additional variance/covariance terms and cannot reuse simple formula |
| Output values in common results[].rows[].values[] | SAFETY_STOCK:QUANTITY, REORDER_POINT:QUANTITY, SERVICE_TARGET:RATE, MODEL_WARNINGS:CODE; AGGREGATE |
| Independently checkable synthetic arithmetic | μd10/day, σd2/day, L4 days, assumed z1.65 → safety6.6≈7 units (round up), reorder point47 units |
| Negative cases / hard gates | distribution/independence untested; correlated demand; lead time varies; float quantile reused as financial rate |
| Prerequisite DAG / Calculation Session reuse | HC.STOCK.07; D70 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 18. HC.PLAN.04 — Оптимизация производственной загрузки и мощностей

**TaskCode:** W3.PLAN.04.V1 · **FIN candidate:** DF-OPS-01/02;MGT-02 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D71 resource calendar slots/skills/tasks and workload durations |
| Explicit parameters and variants | capacityScope, calendarHolidays, objective=MIN_OVERTIME \| MAX_THROUGHPUT, skillCompatibility, taskPrecedence; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Solve assignment/scheduling satisfying resource availability and skill constraints; total load>capacity indicates unavoidable overtime or unmet workload unless alternate resources. Return feasible allocation or infeasibility certificate |
| Output values in common results[].rows[].values[] | CAPACITY_UTILIZATION:RATIO, UNALLOCATED_HOURS:QUANTITY, RESOURCE_ASSIGNMENTS:STRUCT[], FEASIBILITY:CODE; OPTIMIZATION_PLAN |
| Independently checkable synthetic arithmetic | 2 resources×8h×5days=80 available hours; 100 qualified hours required ⇒ at least20 unallocated/overtime hours |
| Negative cases / hard gates | skills mismatch, overlapping allocations, double counted available hours, unverified global optimum |
| Prerequisite DAG / Calculation Session reuse | D71; HC.PLAN.05 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 19. HC.PLAN.05 — Критический путь и задержки проекта

**TaskCode:** W3.PLAN.05.V1 · **FIN candidate:** DF-PRJ-06;MGT-08 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D72 tasks and precedence graph with durations, project calendar |
| Explicit parameters and variants | graphType=DAG, lagPolicy, startDate, durationPrecision, activityCalendarRevision, criticalityThreshold; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For a finite DAG compute earliest start/finish by max over predecessor EF+lag, latest dates backward, total float; critical path length = longest feasible precedence path under stated finish-start baseline |
| Output values in common results[].rows[].values[] | CRITICAL_DURATION:DAYS, CRITICAL_TASKS:REF[], TOTAL_FLOAT:DAYS per task; TIME_SERIES/OPTIMIZATION_PLAN |
| Independently checkable synthetic arithmetic | Two routes: A3→B5 days (8d), parallel C4 days ⇒ project critical path length8 days (FS, no holidays) |
| Negative cases / hard gates | cycles, negative duration, invalid lag, finish-to-finish treated as FS, calendar offsets unresolved |
| Prerequisite DAG / Calculation Session reuse | D72; HC.PLAN.04 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 20. HC.PLAN.06 — План ФОТ и численности

**TaskCode:** W3.PLAN.06.V1 · **FIN candidate:** DF-HR-03;DF-HR-01;MGT-04 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D73 employee effective-dated payroll contract and FTE, tax/benefits rates by policy |
| Explicit parameters and variants | grossVsNetPay, payrollTaxPolicyRef, partMonthProration, employerCostScope, benefitsRateRef, costCenterAllocation; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Monthly employer payroll plan = Σ eligible employee gross salary×FTE×valid month fraction + qualified employer contributions/benefits; withholding employee taxes is distinct from employer cost |
| Output values in common results[].rows[].values[] | PLANNED_GROSS_PAY:MONEY, PLANNED_EMPLOYER_COST:MONEY, FTE_TOTAL:QUANTITY, COST_BY_CENTER:MONEY; TIME_SERIES |
| Independently checkable synthetic arithmetic | 3 full-time workers at100 KZT gross each, employer benefit20% => base300, benefit60, total360 KZT |
| Negative cases / hard gates | payroll taxes double counted, effective date change ignored, benefits not legally fixed, PII leakage |
| Prerequisite DAG / Calculation Session reuse | D73; HC.PLAN.01 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 21. HC.PLAN.08 — Оптимальное распределение CAPEX портфеля

**TaskCode:** W3.PLAN.08.V1 · **FIN candidate:** P05/P07/P08;INV-09 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D74 projects with capital demand and qualified NPV, budget caps, mutually exclusive groups, dependencies |
| Explicit parameters and variants | objective=MAX_TOTAL_NPV, indivisibility=0_1, budgetPeriods, dependencyConstraints, discountPolicy, solverGapTolerance; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Binary capital budgeting maximize Σ NPV_i x_i subject Σ CAPEX_i x_i≤budget, mutual exclusion, precedence and other approved constraints; no assumption fractional projects unless allowed |
| Output values in common results[].rows[].values[] | SELECTED_PROJECTS:REF[], TOTAL_NPV:MONEY, USED_BUDGET:MONEY, OPTIMALITY_GAP:DECIMAL, FEASIBILITY:CODE; OPTIMIZATION_PLAN |
| Independently checkable synthetic arithmetic | Budget100, A capex100/NPV150, B capex60/NPV100, indivisible, no other projects => select A, totalNPV150 |
| Negative cases / hard gates | NPVs not comparable; dependencies violated; solver returns feasible but falsely optimal; implicit leverage assumption |
| Prerequisite DAG / Calculation Session reuse | HC.DCF.01/.07; D74 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 22. HC.RISK.01 — Monte Carlo распределение NPV

**TaskCode:** W3.RISK.01.V1 · **FIN candidate:** P07/P08;A06 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D75 factor draws, D79 generator/design, D13 baseline flows, D78 correlations when required |
| Explicit parameters and variants | distributionRevision, prngAlgorithm, seed, samplingScheme, sampleCount, scenarioCorrelation, statisticalErrorEstimate; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For draw k apply sampled typed factors to pinned DCF plan and compute NPV_k; summarize empirical mean, quantiles, dispersion, sampling error. Same seed+algorithm+draw sequencing must yield reproducible vector; distinguish financial Decimal outputs from statistical floats |
| Output values in common results[].rows[].values[] | SAMPLED_NPV:MONEY[], MEAN_NPV:MONEY, STD_NPV:MONEY, QUANTILES:STRUCT[], STANDARD_ERROR:MONEY; DISTRIBUTION |
| Independently checkable synthetic arithmetic | Illustrative four fixed sampled NPVs [−10,0,10,20] KZT ⇒ mean5, population σ≈11.1803398875 KZT; four draws are NOT robust forecast precision |
| Negative cases / hard gates | random generator unspecified; correlations missing; precision confidence from four samples falsely claimed; numeric overflow |
| Prerequisite DAG / Calculation Session reuse | HC.DCF.01; D75/D79 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 23. HC.RISK.02 — Value at Risk по распределению потерь

**TaskCode:** W3.RISK.02.V1 · **FIN candidate:** P08;MGT-07 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D76 loss observations or committed scenario result distribution, sample weights/time horizon |
| Explicit parameters and variants | confidenceAlpha, horizon, lossSignConvention, estimator=EMPIRICAL_NEAREST_RANK \| MODEL_BASED, sampleWindow, quantileDefinition; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For loss variable L, VaR_α=inf{x:F_L(x)≥α}. Empirical unweighted nearest-rank at α: sorted losses index ceil(αN), with explicit sign and horizon. VaR is a loss quantile, not maximum possible loss |
| Output values in common results[].rows[].values[] | VAR_LOSS:MONEY, QUANTILE_ALPHA:RATE, SAMPLE_COUNT:INTEGER, ESTIMATION_STATE:CODE; AGGREGATE |
| Independently checkable synthetic arithmetic | Observed losses [0,10,20,30] KZT, α=0.75, nearest-rank empirical VaR=20 KZT |
| Negative cases / hard gates | mixed returns and losses; noncomparable horizon; unsupported distribution tail; alpha invalid; sample too short |
| Prerequisite DAG / Calculation Session reuse | HC.RISK.01; D76 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 24. HC.RISK.03 — Expected Shortfall / CVaR

**TaskCode:** W3.RISK.03.V1 · **FIN candidate:** P08;MGT-07 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D76 same observed loss distribution/weights and quantile method as VaR |
| Explicit parameters and variants | alpha, estimator=QUANTILE_INTEGRAL, tailMassTreatment, weightedSamplePolicy, horizon, zeroTailRule; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | ES_α=(1/(1−α))∫_α^1 VaR_u du. For discrete distributions integrate quantile mass correctly, not simply E[L\|L>VaR] when there is probability at VaR |
| Output values in common results[].rows[].values[] | EXPECTED_SHORTFALL:MONEY, TAIL_LOSS_DISTRIBUTION:STRUCT[], VAR_REFERENCE:MONEY; AGGREGATE |
| Independently checkable synthetic arithmetic | Losses [0,10,20,30] KZT equally weighted, α=.75 → upper quarter is loss30; ES30 KZT |
| Negative cases / hard gates | ties at quantile; naive conditional above threshold; weighted losses ignored; tail sample too small |
| Prerequisite DAG / Calculation Session reuse | HC.RISK.02; D76 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 25. HC.RISK.05 — Чувствительность ECL к макроэкономике

**TaskCode:** W3.RISK.05.V1 · **FIN candidate:** A02;C01;P08 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D77 macro scenarios + D81 model features + D19/D22 frozen portfolio exposure |
| Explicit parameters and variants | macroTransformRevision, scenarioWeights, sensitivityMeasure=DELTA_ECL, calibrationEvidence, pdLgdeAdRecalibration; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Recalculate qualified ECL portfolio under approved macro calibration of PD/LGD/EAD, then ΔECL=stressedECL−baselineECL. Do not multiply arbitrary PD by macro shock without calibrated link |
| Output values in common results[].rows[].values[] | BASE_ECL:MONEY, STRESS_ECL:MONEY, DELTA_ECL:MONEY, RISK_DRIVER:CODE; SCENARIO_MATRIX |
| Independently checkable synthetic arithmetic | Illustrative calibrated assumption: EAD100 LGD.4, PD baseline.02 vs stress.03 (same undiscounted timing) ⇒ ECL .8 vs1.2, delta .4 KZT |
| Negative cases / hard gates | model calibration unsupported, scenario double weighted, forecast info ignored, correlation confounded with causation |
| Prerequisite DAG / Calculation Session reuse | HC.ECL.02/.03; D77/D81 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 26. HC.RISK.06 — Вероятность кассового разрыва

**TaskCode:** W3.RISK.06.V1 · **FIN candidate:** P03;P08;CFO-02 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D26/D27 path/buffer + D75 stochastic scenario flows with D79 weights/design |
| Explicit parameters and variants | breachRule=BELOW_BUFFER, horizon, pathWeightPolicy, confidenceIntervalMethod, simulationStoppingPolicy; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | For each simulated cash path k compute indicator I(min_t Cash_{k,t}<floor); p_gap=Σ weights_k I_k/Σweights_k; first-passage bucket and bootstrap/binomial uncertainty reported as supported |
| Output values in common results[].rows[].values[] | PROBABILITY_GAP:RATE, PATH_BREACH_COUNT:INTEGER, FIRST_PASSAGE_DISTRIBUTION:STRUCT[], CI:STRUCT?; DISTRIBUTION |
| Independently checkable synthetic arithmetic | Four equiprobable paths, two below cash floor during horizon ⇒ empirical p_gap=0.5, sample tiny |
| Negative cases / hard gates | negative scenario weights, breached at equals policy mismatch, lookahead, independent scenarios falsely correlated |
| Prerequisite DAG / Calculation Session reuse | HC.CASH.03; HC.RISK.01; D75/D79 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |


### 27. HC.RISK.07 — Совместный сценарий ставок, FX и CAPEX

**TaskCode:** W3.RISK.07.V1 · **FIN candidate:** P07/P08;C05;A06 · **Status:** METHODOLOGY_DRAFT / FINANCE_S2_HOLD.

| Contract item | Specification |
|---|---|
| Typed input arrays | D78 correlated factor shocks + D51 shock mapping + D13 financial cash flows + D29 FX rates |
| Explicit parameters and variants | shockCorrelationRev, orderOfOperations, scenarioVectorRev, mappingPolicy, currencyAndRealNominalCompatibility; immutable policy/sha, numeric precision, calendar, unit/currency, scope from Wave-1 |
| Mathematical method / applicability | Apply all allowed rate/FX/CAPEX shocks jointly to identical baseline financial DAG; reprice dated cashflow/rate/FX and compute ΔNPV/cash/ECL as relevant; correlation matrix PSD and all factor effects once |
| Output values in common results[].rows[].values[] | SCENARIO_NPV:MONEY, RATE_SHOCK:RATE, FX_SHOCK:RATIO, CAPEX_DELTA:MONEY, COMBINED_DELTA:MONEY; SCENARIO_MATRIX |
| Independently checkable synthetic arithmetic | CAPEX base100 with +20% shock⇒120 KZT; FX 10 USD cash outflow at 500→550 KZT/USD increases cost from5000 to5500 KZT, delta+500 (separate components, not aggregate net effect) |
| Negative cases / hard gates | non-PSD correlation matrix; FX conversion direction wrong; cash flows mixed currencies; shocks applied twice |
| Prerequisite DAG / Calculation Session reuse | HC.DCF.09; HC.CASH.07; D78 |
| Validation standard | Exact decimal accounting money; statistics error estimates where applicable; solver residual/feasibility gap; independent financial calibration required |



## 4. Output-shape and statistical contracts

**ResultShape allowlist v2:** ROW_ALIGNED, GROUPED, TIME_SERIES, EVENT_SERIES, AGGREGATE, ROOT_SET, SCENARIO_MATRIX, DISTRIBUTION, OPTIMIZATION_PLAN. New shapes must be formally versioned, not inserted into existing Wave-1 contracts without compatibility check.

Statistical supplementary outputs:
- RunEvidenceDTO = {simulationRunKey, seed(INT64), prngRevision, distributionRevision, factorCorrelationRevision, modelArtifactSha, sampleCount, dataWindow, selectionOrCensoringPolicy, convergenceState}.
- DistributionResultDTO = {observations[] or chunks[], weights[], moments, quantileSpec, quantiles, confidenceIntervals?, standardError?, effectiveSampleSize?, diagnostics[]}; money samples exact decimal serialization, numerical stats explicitly precision-tagged.
- OptimizationResultDTO = {objectiveCode, objectiveValue, decisionRows[], constraintResiduals[], feasibilityStatus, algorithmRevision, incumbentBound?, lowerOrUpperBound?, optimalityGap?, timeLimitReached, diagnostics[]}.
- Risk QuantileDefinition = {lossSignConvention, alpha(RATE), horizon, estimatorCode, weightedMassPolicy, tiePolicy, quantileInterpolationPolicy}; ES requires quantile-integral semantics to handle discrete mass at VaR threshold.
- Probability/scenario matrix = {scenarioRefs[], timeGrid, marginalDistributionRefs, correlationMatrixRevision, calibratedMacroEvidenceRef, probabilityWeights[], aggregationPolicy}; correlation matrix must be symmetric PSD within approved tolerance; normalize weights only by explicit policy, never silently.

**Quality of statistical methods:** calibration dataset lineage, training/validation/test time split, data leakage checks, bootstrap/analytical CIs where meaningful, backtesting error rate, probability calibration and monitoring plan. Risk forecast confidence cannot be proven from arithmetic fixtures; preserve REVIEW_REQUIRED status.

**Optimization:** every constraint unit/currency/period pinned, no false claim of optimum if solver timed out; expose exact incumbent/feasible status and gap; binary decision variables and SKU integer quantities separate from continuous Decimal money.

## 5. Cross-family computation DAG and memory reuse

- PD term structure (ECL.04) → EAD & LGD (ECL.05/.06) → Lifetime/12m ECL (P1 ECL.02/.03) → ECL sensitivity (RISK.05).
- Risk stage migration (ECL.07) depends on independent SICR/POCI source decisions, not only a threshold from PD curve.
- KZ GESV (LOAN.08) reuses eligible contract **data** with IFRS EIR but uses a **separate legal instrument/fee/cashflow/rate-calculation policy** and TaskCode; compare results only with explicit basis disclosure.
- Foreign operation translation (ACC.03) and deferred taxes (ACC.05) are source classifiers for consolidated three-statement integration, not simple arithmetic ratios on unverified journal rows.
- Inventory ageing does not write down cost automatically; stock NRV (P1 STOCK.04) owns valuation policy. Safety-stock model feeds stock replenishment only as approved derived input.
- Monte Carlo generated factors (RISK.01) → VaR (RISK.02) → Expected Shortfall (RISK.03) and Liquidity gap probability (RISK.06); each consumes exact scenario/result SHA and permissions.
- CAPEX portfolio optimization consumes admitted NPV/DCF outputs with scenario and currency comparability; project feasibility does not trump finance S2.
- Scenario calculations use one immutable Calculation Session to share typed source arrays/paths and many independent scoped idempotencyKey executions. Each dependency is pinned by committed ResultSetSha; no mutable in-memory pointer as financial truth.

## 6. Acceptance candidates and gate ordering

Every 27 methods needs:
1. one worked numeric boundary example plus an *independent* finance-reviewed golden;
2. regular, missing, negative, zero, duplicate, invalid method version, revoked source, unexpected currency, unit/period mismatch tests;
3. numerical precision policy per type (MONEY exact Decimal; statistics with explicit approximation/uncertainty; solvers with residual/gap);
4. immutable and reproducible dataset/result binding, scope isolation, and idempotency conflict handling;
5. statistical validation or legal-source applicability whenever needed (KZ GESV; IAS; IFRS; credit risk);
6. no source fabrication: any unqualified financial source leaves the model BLOCKED_SOURCE;
7. no runtime execution until separate user-approved implementation task.

**Document-only readiness states:** REGISTERED → METHOD_CANDIDATE → FORMAL_INPUT_CONTRACT_REVIEWED → INDEPENDENT_MATH_GOLDEN_REVIEWED → PYTHON_VERIFIED (future) → RUST_PARITY (future) → INDEPENDENT_FINANCE_S2 (future, when applicable) → PRODUCTION_ADMITTED (future). None of these statuses beyond METHOD_CANDIDATE is implied by this document.

## 7. Source and legal references for methodology review

- IFRS 9 (12-month versus lifetime ECL): https://www.ifrs.org/content/dam/ifrs/project/fi-impairment/ifrs-standard/published-documents/project-summary-july-2014.pdf
- IAS 12 (deferred tax): https://www.ifrs.org/issued-standards/list-of-standards/ias-12-income-taxes/
- IAS 21 (translation): https://www.ifrs.org/issued-standards/list-of-standards/ias-21-the-effects-of-changes-in-foreign-exchange-rates/
- IAS 36 (value in use): https://www.ifrs.org/issued-standards/list-of-standards/ias-36-impairment-of-assets/
- IFRS 10 (consolidation): https://www.ifrs.org/issued-standards/list-of-standards/ifrs-10-consolidated-financial-statements/
- Kazakhstan KZ_GESV bank loan APR, Resolution of ARDFM Board 03.04.2026 №44, registered 06.04.2026 №38333, clauses 11–23: https://zakon.uchet.kz/rus/docs/V2600038333; official legal registry link https://old.adilet.zan.kz/rus/docs/V2600038333. For other loan institution types, separate applicable legal variant is mandatory, not automatically inherited.
- Mathematical ES discrete quantile-integral/ties: https://danpele.github.io/MFM/web/ch7.html

**Release decision:** REQUIREMENTS_ONLY — all 27 P2 indicators specified with input arrays, typed numeric/period/parameter requirements, formula/estimation rules, output metrics, synthetic arithmetic vectors, statistical/financial failure conditions and dependencies. No Python/Rust code, no schema migrations, no running calculator.
