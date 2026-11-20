# FENGINE-MODEL-EXT-R1 — Расширение Financial Calculation Engine: Wave 4 (12 candidate models)

- **Document ID:** FENGINE-MODEL-EXT-R1-V1
- **Date:** 2026-11-20
- **Repository/branch:** alimbetov/FEngine / `feat/fengine-model-ext-r1-12-contracts`
- **Status:** REQUIREMENTS_DRAFT / MODEL_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD
- **Base:** FENGINE_MASTER_SPEC.md v0.7; 83 pre-existing HC.* models and D01–D81 typed dataset candidates remain unchanged.
- **Scope:** 12 *new* `HC.*` candidate task contracts, `W4.*.V1` codes, additional typed input data families D82–D93, governance and independent test vectors. This is **not** a Python/Java/Rust implementation, not FIN contract admission, and does not change any historical methodology SHA.
- **Decision:** Register 12 new advanced B2B models, prioritizing cost of capital, loan economics, customer economics, project finance and bank ALM. Regulatory LCR/NSFR, IFRS17 and other sector packages remain independently gated backlog, not silent additions to the 12.

## 1. Baseline, identity and anti-duplication

| Baseline | Existing count | W4 increment | Target candidate count |
|---|---:|---:|---:|
| Calculation/model contracts | 83 | 12 | 95 |
| Typed dataset families | 81 | 12 | 93 |
| Waves | W1 (14), W2 (42), W3 (27) | W4 (12) | 4 |

These are **candidate specification counts**, not executable/qualified model counts. W1–W3 and their taskCode namespaces must not be renumbered, reinterpreted or overwritten.

- CAPM/WACC *feed* HC.DCF.07/08; they do not duplicate discounted valuation or FCFE.
- Credit pricing/RAROC reuse HC.LOAN and HC.ECL; credit pricing is not IFRS EIR or KZ GESV.
- CLV and CAC payback use distinct customer cohort contracts, avoiding double deduction of acquisition cost.
- LLCR/PLCR are not the existing HC.LOAN.07 contractual DSCR; project waterfall allocates money under contract order.
- ALM repricing/ΔEVE are bank-balance-sheet risks, not HC.RISK.07 generic multi-shock planning.
- FTP is internal funding allocation, not ordinary interest accrual; price optimization is not HC.COST.04 cost-volume-profit break-even.

## 2. Registry — exactly 12 new candidates

| # | Metric candidate | Name | TaskCode | Priority | Complexity | New dataset | Reuse |
|---:|---|---|---|---|:---:|---|---|
| 1 | HC.CAP.01 | CAPM: требуемая доходность собственного капитала | W4.CAP.01.V1 | EXT-P0 | M | D82 | NONE |
| 2 | HC.CAP.02 | WACC: средневзвешенная стоимость капитала | W4.CAP.02.V1 | EXT-P0 | T | D83 | HC.CAP.01 |
| 3 | HC.CREDIT.01 | Risk-based loan pricing: минимальная допустимая ставка | W4.CREDIT.01.V1 | EXT-P0 | N | D84 | HC.LOAN.01/02/03;HC.ECL.02/03;HC.FTP.01 |
| 4 | HC.CREDIT.02 | RAROC: риск-скорректированная доходность капитала | W4.CREDIT.02.V1 | EXT-P0 | T | D85 | HC.ECL.02/03;HC.CREDIT.01 |
| 5 | HC.CUST.01 | Customer LTV/CLV: дисконтированная когортная маржа | W4.CUST.01.V1 | EXT-P0 | M | D86 | HC.PLAN.01/02;HC.CASH.01 |
| 6 | HC.CUST.02 | CAC payback: срок окупаемости привлечения | W4.CUST.02.V1 | EXT-P0 | T | D87 | HC.CUST.01;HC.COST.01 |
| 7 | HC.PF.01 | LLCR/PLCR: покрытие долга проектными потоками | W4.PF.01.V1 | EXT-P1 | N | D88 | HC.LOAN.02/07;HC.DCF.02 |
| 8 | HC.PF.02 | Waterfall денежных средств и DSRA | W4.PF.02.V1 | EXT-P1 | E | D89 | HC.CASH.01;HC.LOAN.02/07;HC.PF.01 |
| 9 | HC.ALM.01 | Repricing GAP и чувствительность NII | W4.ALM.01.V1 | EXT-P1 | T | D90 | HC.LOAN.01;HC.RISK.07 |
| 10 | HC.ALM.02 | ΔEVE: изменение экономической стоимости капитала | W4.ALM.02.V1 | EXT-P1 | N | D91 | HC.ALM.01;HC.DCF.02 |
| 11 | HC.FTP.01 | Funds Transfer Pricing: сроковая стоимость фондирования | W4.FTP.01.V1 | EXT-P1 | T | D92 | HC.LOAN.01 |
| 12 | HC.PRICE.01 | Оптимизация цены с эластичностью и ограничениями | W4.PRICE.01.V1 | EXT-P1 | O | D93 | HC.COST.04;HC.PLAN.02/04;HC.PLAN.08 |

Complexity classes: E event replay, T time-bounded reconciliation, N numerical solver/PV, O optimization, M scenario/cohort modeling. EXT-P0/P1 is W4 research priority, not a change to W1–W3 priority. The technical source of truth for each model is its **own** MethodRevision, ParamsRevision, InputSchemaRevision, OutputSchemaRevision and immutable Method/Algorithm Manifest.

## 3. Shared contract and typed dataset rules

**Inputs:** canonical `InputBatchDTO` with `datasets[]` and pinned source revisions, per-row `rowKey`, tenant/project scope, `valueState` (`PRESENT`, `MISSING`, `EXPLICIT_NULL`, `NOT_APPLICABLE`, `INVALID`), period/asOf, unit, original currency, data lineage and complete `InputSha256`. These D82–D93 schemas add *incremental* row/dataset families; they may reference rather than copy qualified D01–D81 arrays. `MONEY` and rates are decimal strings; MONEY carries currency, quantity has units; no binary float for settlement, rounding or legal money.

**Outputs:** existing `CalculationResponseDTO.results[].rows[].values[]`, with modelCode, exact taskCode, source+parameter+plan SHA, output metricCode, metricKind, period, unit, value state, solver/qualification status, warnings and lineage. Undefined ratios are `UNDEFINED_DENOMINATOR`; absent source is `BLOCKED_SOURCE`; incompatible evidence is `BLOCKED_METHODOLOGY`; optimization must expose feasibility/optimality flags. Numerical tolerances are approved parameters, never inferred from display precision.

**Execution:** same shared Calculation Hub / CalcPlan / idempotency semantics as W1–W3. No 12 new microservices. W4 adds neither new FIN forms nor public production claims. S2 sign-off is independent of arithmetic test passes.

### D82–D93 typed DTO proposals

All required schema fields marked `!`, conditional `?`; referenced source manifests and tenant scope mandatory as in the base shared contract.

- **D82 MARKET_EQUITY_FACTOR** — valuationDate:LOCAL_DATE!; marketCurrency:CODE!; riskFreeRate:RATE!; equityBeta:DECIMAL!; marketRiskPremium:RATE!; riskFreeTenor:PERIOD!; premiumSourceRevision:REFERENCE!; betaCalibrationRevision:REFERENCE!; segmentKey:REFERENCE?
- **D83 CAPITAL_STRUCTURE_SNAPSHOT** — valuationDate:LOCAL_DATE!; marketEquityValue:MONEY!; marketDebtValue:MONEY!; debtPreTaxCost:RATE!; taxShieldEligibleRate:RATE!; targetOrObserved:ENUM!; currencyCode:CODE!; sourceRevisionRef:REFERENCE!
- **D84 CREDIT_PRICING_COMPONENT** — loanRef:REFERENCE!; pricingDate:LOCAL_DATE!; principal:MONEY!; datedCashflows:LIST<STRUCT>!; fundingCostCurveRef:REFERENCE!; expectedLossAmount:MONEY!; operatingCostAmount:MONEY!; capitalChargeAmount:MONEY!; eligibleFeeCashflows:LIST<STRUCT>?; sourceRevisionRef:REFERENCE!
- **D85 RAROC_ECONOMIC_CAPITAL** — scopeRef:REFERENCE!; period:PERIOD!; grossIncome:MONEY!; fundingExpense:MONEY!; operatingExpense:MONEY!; expectedLoss:MONEY!; allocatedEconomicCapital:MONEY!; otherRiskAdjustments:MONEY?; currencyCode:CODE!; sourceRevisionRef:REFERENCE!
- **D86 CUSTOMER_COHORT_MARGIN** — cohortKey:REFERENCE!; periodIndex:INTEGER!; cashflowDate:LOCAL_DATE!; expectedContributionMargin:MONEY!; marginGrain:ENUM(PER_CUSTOMER,COHORT_TOTAL)!; survivalProbability:RATE!; discountFactor:DECIMAL?; customerCount:INTEGER!; currencyCode:CODE!; evidenceRef:REFERENCE!
- **D87 ACQUISITION_COHORT_SPEND** — cohortKey:REFERENCE!; acquisitionDate:LOCAL_DATE!; recognizedAcquisitionCost:MONEY!; datedContributionMargin:LIST<STRUCT>!; attributedNewCustomers:INTEGER!; currencyCode:CODE!; spendEvidenceRef:REFERENCE!; attributionRevisionRef:REFERENCE!
- **D88 PROJECT_FINANCE_CFADS** — projectRef:REFERENCE!; valuationDate:LOCAL_DATE!; datedCFADS:LIST<STRUCT>!; debtLifeEndDate:LOCAL_DATE!; projectLifeEndDate:LOCAL_DATE!; outstandingDebt:MONEY!; discountCurveRef:REFERENCE!; sourceRevisionRef:REFERENCE!
- **D89 PROJECT_CASH_WATERFALL** — projectRef:REFERENCE!; waterfallDate:LOCAL_DATE!; availableCash:MONEY!; debtServiceDue:MONEY!; dsraOpening:MONEY!; dsraTarget:MONEY!; otherApprovedPriorities:LIST<STRUCT>?; waterfallContractRevisionRef:REFERENCE!; sourceRevisionRef:REFERENCE!
- **D90 ALM_REPRICING_POSITION** — positionRef:REFERENCE!; asOf:LOCAL_DATE!; bookSide:ENUM(ASSET,LIABILITY,OFF_BALANCE)!; principal:MONEY!; nextRepricingDate:LOCAL_DATE!; maturityDate:LOCAL_DATE!; benchmarkRateRef:REFERENCE?; currencyCode:CODE!; behavioralAssumptionRev:REFERENCE?; evidenceRef:REFERENCE!
- **D91 ALM_DISCOUNTED_CASHFLOW** — positionRef:REFERENCE!; bookSide:ENUM(ASSET,LIABILITY,OFF_BALANCE)!; cashflowDate:LOCAL_DATE!; cashflowAmount:MONEY!; discountCurveKey:REFERENCE!; currencyCode:CODE!; optionRevisionRef:REFERENCE?; sourceRevisionRef:REFERENCE!
- **D92 FTP_CURVE_POINT** — curveRevisionRef:REFERENCE!; currencyCode:CODE!; valuationDate:LOCAL_DATE!; tenor:PERIOD!; transferRate:RATE!; liquidityPremium:RATE?; basisAdjustment:RATE?; sourceEvidenceRef:REFERENCE!
- **D93 PRICE_DEMAND_OBSERVATION** — productRef:REFERENCE!; observedDate:LOCAL_DATE!; observedPrice:MONEY_PER_UNIT!; observedQuantity:QUANTITY!; unitVariableCost:MONEY_PER_UNIT!; channelKey:REFERENCE!; exposureDays:INTEGER!; stockoutCensored:BOOLEAN!; evidenceRef:REFERENCE!

## 4. Individual model contracts and control examples

Each synthetic golden vector below is an *independent arithmetic fixture candidate*. It must be independently calculated, reviewed and converted to executable Decimal golden tests before claim of qualification; rounded display is not a computation rule. Each section defines the model-specific params **in addition** to shared numericPrecision, roundingPolicy, calendarRevision, currency policy, period contract, effectiveDate, source SHA, method SHA, result schema and admission evidence.

### 01. HC.CAP.01 — CAPM: требуемая доходность собственного капитала

- **TaskCode:** `W4.CAP.01.V1`; **priority:** EXT-P0; **complexity:** M; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D82 (`MARKET_EQUITY_FACTOR`); source observations only, no upstream HC.* numerical model dependency. FIN bindings remain unverified.
- **Method-specific typed parameters:** capmVariant:ENUM(STANDARD,ADJUSTED)!; riskFreeTenorPolicyRef:REFERENCE!; betaLeveringPolicyRef:REFERENCE!; marketPremiumPolicyRef:REFERENCE!; regionalPremiumPolicyRef:REFERENCE?; roundingPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** STANDARD: Ke = rf + beta × ERP. ADJUSTED may add a separately justified country/size premium; never silently double-count such risk in ERP and premium. Currency and risk-free tenor must match cash-flow valuation context.
- **Result metrics:** COST_OF_EQUITY:RATE; BETA_USED:DECIMAL; RISK_PREMIUM_APPLIED:RATE. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** rf=0.04, beta=1.2, ERP=0.06, STANDARD ⇒ Ke=0.112 (11.2%).
- **Hard negative tests:** Absent beta calibration, mismatched valuation currency, stale factor series, silent country-risk premium or arbitrary beta default.
- **Business boundary:** Corporate valuation candidate, not universal cost of equity for unlisted businesses without reviewed proxies.

### 02. HC.CAP.02 — WACC: средневзвешенная стоимость капитала

- **TaskCode:** `W4.CAP.02.V1`; **priority:** EXT-P0; **complexity:** T; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D83 (`CAPITAL_STRUCTURE_SNAPSHOT`) plus pinned result `HC.CAP.01` when admitted; do not depend on a downstream DCF valuation output.
- **Method-specific typed parameters:** weightBasis:ENUM(MARKET,TARGET)!; costOfEquitySourceRef:REFERENCE!; debtCostBasis:ENUM(PRETAX_EFFECTIVE)!; taxShieldPolicyRef:REFERENCE!; capitalInclusionPolicyRef:REFERENCE!; debtEquityConsistencyRef:REFERENCE!.
- **Mathematics / eligibility:** For qualified, consistent market-value weights: WACC = E/(D+E)×Ke + D/(D+E)×Kd×(1−T). Apply tax shield only where admissible; valuation currency and nominal/real conventions must match FCFF.
- **Result metrics:** WACC:RATE; EQUITY_WEIGHT:RATIO; DEBT_WEIGHT:RATIO; AFTER_TAX_DEBT_COST:RATE. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** E=60, D=40, Ke=0.12, Kd=0.08, T=0.20 ⇒ WACC=0.0976 (9.76%).
- **Hard negative tests:** Zero D+E, inconsistent market vs book weights, negative unreviewed capital, non-deductible interest treated as deductible, currency mismatch.
- **Business boundary:** Discount-rate provider; do not replace HC.DCF.07 or HC.DCF.08.

**METHOD-HARDENING-R1 pre-freeze:** `fcffCompatibilityPolicyRef`, capital weights basis, tax shield eligibility, valuation currency and observed/target debt/equity are mandatory. WACC is for matched FCFF; no automatic FCFE discounting. Addendum §4.

### 03. HC.CREDIT.01 — Risk-based loan pricing: минимальная допустимая ставка

- **TaskCode:** `W4.CREDIT.01.V1`; **priority:** EXT-P0; **complexity:** N; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D84 (`CREDIT_PRICING_COMPONENT`) plus explicitly admitted existing data `HC.LOAN.01/02/03;HC.ECL.02/03;HC.FTP.01` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** pricingPerspective:ENUM(LENDER)!; rateQuoteBasis:ENUM(NOMINAL,EFFECTIVE)!; dayCountPolicyRef:REFERENCE!; lossHorizonRef:REFERENCE!; capitalAllocationRevision:REFERENCE!; feeTreatmentRevision:REFERENCE!; solverDomain:STRUCT!; rootTolerance:DECIMAL!; profitabilityTarget:MONEY!.
- **Mathematics / eligibility:** Solve dated, lender-perspective NPV of priced contract cashflows less funding/operating/expected-credit-loss/capital charges for the rate meeting specified target. Simplified single-year non-compounding test: rate=(funding+operations+EL+capitalCharge−eligibleFees)/principal. Never equate this nominal quote with IFRS EIR or local APR.
- **Result metrics:** MIN_PRICE_RATE:RATE; EXPECTED_MARGIN:MONEY; PRICING_NPV_RESIDUAL:MONEY; BREAKEVEN_STATUS:CODE. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** One-year principal=100, funding=4, operations=1, expected loss=2, capital charge=3, eligible fees=0, target=0 ⇒ rate=0.10.
- **Hard negative tests:** ECL charged twice, fees counted twice, zero/negative principal, price root absent, disallowed rate cap breached, inconsistent horizon and borrower/lender sign.
- **Business boundary:** Management pricing candidate, not a legally approved credit offer or regulatory GESV.

**METHOD-HARDENING-R1 pre-freeze:** `lossAndFundingNoDoubleCountPolicyRef` and fee-funding-ECL alignment mandatory. The quoted lender rate is management pricing; it is NOT automatically IFRS EIR or Kazakhstan GESV and must not be reused as statutory rate. Addendum §3.

### 04. HC.CREDIT.02 — RAROC: риск-скорректированная доходность капитала

- **TaskCode:** `W4.CREDIT.02.V1`; **priority:** EXT-P0; **complexity:** T; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D85 (`RAROC_ECONOMIC_CAPITAL`) plus explicitly admitted existing data `HC.ECL.02/03;HC.CREDIT.01` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** capitalDefinitionRevision:REFERENCE!; lossInclusionPolicyRef:REFERENCE!; revenueRecognitionBasis:CODE!; taxTreatmentPolicyRef:REFERENCE!; annualizationPolicyRef:REFERENCE!; periodAlignmentPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** Base unannualized management RAROC = (grossIncome−fundingExpense−operatingExpense−expectedLoss−approvedOtherRiskAdjustments)/allocatedEconomicCapital; if annualization needed, make it an explicit qualified variant. Distinguish economic from regulatory capital.
- **Result metrics:** RAROC:RATIO; RISK_ADJUSTED_PROFIT:MONEY; ECONOMIC_CAPITAL:MONEY. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** Income=15, funding=4, opex=2, expected loss=3, economic capital=40, no other adjustment ⇒ profit=6, RAROC=0.15.
- **Hard negative tests:** Capital zero, expected loss already netted in income, annual income against monthly capital with no annualization, conflicting currency or portfolio scope.
- **Business boundary:** Portfolio/product pricing economics; not a substitute for prudential capital calculation.

### 05. HC.CUST.01 — Customer LTV/CLV: дисконтированная когортная маржа

- **TaskCode:** `W4.CUST.01.V1`; **priority:** EXT-P0; **complexity:** M; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D86 (`CUSTOMER_COHORT_MARGIN`) plus explicitly admitted existing data `HC.PLAN.01/02;HC.CASH.01` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** valuationDate:LOCAL_DATE!; discountRateSourceRef:REFERENCE!; retentionDefinitionRef:REFERENCE!; marginRecognitionPolicyRef:REFERENCE!; retentionAlreadyWeighted:BOOLEAN!; acquisitionCostTreatment:ENUM(EXCLUDED,INCLUDED_SEPARATELY)!; terminalValuePolicyRef:REFERENCE?.
- **Mathematics / eligibility:** For marginGrain=PER_CUSTOMER, CLV per customer = Σ(period margin per customer × survival probability × dated discount factor) − per-customer CAC only under an explicit inclusion variant. Cohort total = CLV per customer × eligible cohort count. For marginGrain=COHORT_TOTAL, compute cohort total directly and do not multiply by customer count again. If expectedContributionMargin already retention-weighted, set retentionAlreadyWeighted=true and do NOT multiply survival twice.
- **Result metrics:** CLV_PER_CUSTOMER:MONEY (valueState=MISSING unless per-customer denominator eligible); CLV_COHORT_TOTAL:MONEY; DISCOUNTED_MARGIN:MONEY; SURVIVAL_PROBABILITY:RATE (TIME_SERIES shape); CAC_APPLIED:MONEY. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** Year1 margin=110, year2 margin=121, survival=1 both, annual discount=10%, no CAC ⇒ CLV=110/1.1 + 121/1.21 = 200.
- **Hard negative tests:** Survival probability outside [0,1], duplicate retention weighting, missing cohort cardinality, CAC double deducted, unsupported perpetual terminal assumption.
- **Business boundary:** Management estimate for subscription/retail cohorts; forecasted CLV is not observed revenue.

### 06. HC.CUST.02 — CAC payback: срок окупаемости привлечения

- **TaskCode:** `W4.CUST.02.V1`; **priority:** EXT-P0; **complexity:** T; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D87 (`ACQUISITION_COHORT_SPEND`) plus explicitly admitted existing data `HC.CUST.01;HC.COST.01` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** attributionWindow:PERIOD!; contributionDefinitionRef:REFERENCE!; paybackBasis:ENUM(NOMINAL,DISCOUNTED)!; fractionalInterpolationPolicy:ENUM(NONE,LINEAR_ASSUMED)!; cutoffDate:LOCAL_DATE!; costAllocationPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** Cumulative qualified period contribution must cover cohort acquisition cost to reach payback. Default returns first fully completed period; optional within-period interpolation requires explicit assumption, is not an observed fact. No crossing ⇒ NOT_REACHED.
- **Result metrics:** PAYBACK_PERIODS:DECIMAL (valueState=MISSING if not reached); PAYBACK_DATE:LOCAL_DATE (valueState=MISSING if not reached); CUMULATIVE_MARGIN:MONEY; PAYBACK_STATUS:CODE. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** CAC=120; period contribution 50,80,50 ⇒ first completed crossing period is 2, cumulative through period2=130; no implicit interpolation.
- **Hard negative tests:** No crossing reported as zero, negative or missing CAC, mixing cohort and per-customer units, historical attribution leakage, contributions in conflicting currencies.
- **Business boundary:** Cohort profitability diagnostic; can reuse CLV contributions but must never include CAC twice.

### 07. HC.PF.01 — LLCR/PLCR: покрытие долга проектными потоками

- **TaskCode:** `W4.PF.01.V1`; **priority:** EXT-P1; **complexity:** N; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D88 (`PROJECT_FINANCE_CFADS`) plus explicitly admitted existing data `HC.LOAN.02/07;HC.DCF.02` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** cfadsDefinitionRef:REFERENCE!; debtLifeBoundaryRef:REFERENCE!; projectLifeBoundaryRef:REFERENCE!; discountBasisPolicyRef:REFERENCE!; debtBalanceRecognitionRef:REFERENCE!; reserveCashInclusionPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** LLCR = PV(CFADS during eligible loan life)/outstanding debt; PLCR = PV(CFADS during eligible project life)/outstanding debt. Both cashflow sets discounted at the valuation date using approved curve; do not confuse DSCR, cash balance or financing sources with CFADS.
- **Result metrics:** LLCR:RATIO; PLCR:RATIO; PV_DEBT_LIFE_CFADS:MONEY; PV_PROJECT_LIFE_CFADS:MONEY. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** Outstanding debt=100; qualifying CFADS=60 at years1 and2, discount=10%, loan and project end year2 ⇒ both=(60/1.1 + 60/1.21)/100 ≈ 1.041322314.
- **Hard negative tests:** Debt zero, project horizon before loan horizon, CFADS double discounted, currency mismatch, CFADS includes refinancing cash as operations.
- **Business boundary:** Project finance covenant evaluation, subject to exact loan agreement definitions.

### 08. HC.PF.02 — Waterfall денежных средств и DSRA

- **TaskCode:** `W4.PF.02.V1`; **priority:** EXT-P1; **complexity:** E; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D89 (`PROJECT_CASH_WATERFALL`) plus explicitly admitted existing data `HC.CASH.01;HC.LOAN.02/07;HC.PF.01` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** waterfallOrderRef:REFERENCE!; dsraFundingRuleRef:REFERENCE!; permittedDistributionRuleRef:REFERENCE!; paymentShortfallPolicyRef:REFERENCE!; restrictedCashTreatmentRef:REFERENCE!; sourceEventOrderPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** Replay contractually ordered distributions of eligible available cash. Only pay up to eligible available amounts; allocate senior service, reserve replenishment and distributable residual in exact priority order. Reconcile available cash = allocations + ending unallocated cash (same currency).
- **Result metrics:** DEBT_SERVICE_PAID:MONEY; DSRA_TOPUP:MONEY; EQUITY_DISTRIBUTION:MONEY; PAYMENT_SHORTFALL:MONEY; RECONCILIATION_RESIDUAL:MONEY. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** Available cash=100, senior debt service due=80, opening DSRA=0, DSRA target=10, order debt→DSRA→equity ⇒ paid=80, topup=10, equity=10, residual=0.
- **Hard negative tests:** Negative cash silently distributed, reserve funded before mandatory senior debt in contrary contract, duplicate distribution events, missing contract priority or restricted-cash flags.
- **Business boundary:** Contract-specific simulation; no cash movement or FIN financial statement mutation.

### 09. HC.ALM.01 — Repricing GAP и чувствительность NII

- **TaskCode:** `W4.ALM.01.V1`; **priority:** EXT-P1; **complexity:** T; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D90 (`ALM_REPRICING_POSITION`) plus explicitly admitted existing data `HC.LOAN.01;HC.RISK.07` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** bucketCalendarRef:REFERENCE!; niiHorizon:PERIOD!; shockCurveRevisionRef:REFERENCE!; depositBehaviorPolicyRef:REFERENCE!; basisRiskRuleRef:REFERENCE!; embeddedOptionPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** For qualified single parallel-rate shock and a simplified one-year fully repricing bucket: ΔNII ≈ (repricingAssets−repricingLiabilities)×rateShock. General IRRBB earnings projection must use dated rate reset, contractual/behavioral cashflows and curve scenarios; do not extrapolate simple GAP to official ΔNII reporting.
- **Result metrics:** REPRICING_GAP:MONEY; DELTA_NII:MONEY; NII_BASE:MONEY (valueState=MISSING until base scenario supplied); NII_STRESS:MONEY (valueState=MISSING until stress supplied). Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** Eligible assets=100, eligible liabilities=60, each resets immediately for full one-year horizon; +100bp shock ⇒ GAP=40 and ΔNII=0.4.
- **Hard negative tests:** Deposit behavior absent, currency aggregation without FX, off-balance position omitted, repricing after horizon treated as instantaneous, sign reversal.
- **Business boundary:** Management IRRBB prototype; Basel supervisory IRRBB method requires separate jurisdiction/date- and scenario-specific qualification.

**METHOD-HARDENING-R1 pre-freeze:** time-specific curve shock, actual repricing vs maturity and approved non-maturity deposit behavior must be pinned. Gap×shock is only a simplified illustration and not qualified Basel ΔNII. Addendum §1/§6.

### 10. HC.ALM.02 — ΔEVE: изменение экономической стоимости капитала

- **TaskCode:** `W4.ALM.02.V1`; **priority:** EXT-P1; **complexity:** N; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D91 (`ALM_DISCOUNTED_CASHFLOW`) plus explicitly admitted existing data `HC.ALM.01;HC.DCF.02` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** shockScenarioSetRef:REFERENCE!; baseCurveRevisionRef:REFERENCE!; discountingConventionRef:REFERENCE!; behavioralCashflowPolicyRef:REFERENCE!; negativeRatePolicyRef:REFERENCE!; optionalityPolicyRef:REFERENCE!; capitalMappingPolicyRef:REFERENCE!.
- **Mathematics / eligibility:** EVE(s) = PV_s(eligible asset and signed off-balance cashflows) − PV_s(eligible liability cashflows), each using scenario-consistent discount curves and behavior; ΔEVE(s)=EVE(s)−EVE(base). Report risk scenarios and any max-loss aggregation separately with approved policy.
- **Result metrics:** EVE_BASE:MONEY; EVE_SCENARIO:MONEY; DELTA_EVE:MONEY; MAX_SCENARIO_LOSS:MONEY (valueState=MISSING until approved scenario set supplied). Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** One-year asset payoff=110, liability payoff=60; flat base discount=10% ⇒ EVE=50/1.1≈45.454545; shock=20% ⇒ EVE=50/1.2≈41.666667, ΔEVE≈−3.787879.
- **Hard negative tests:** Inconsistent base/shock cashflows, missing non-maturity deposit behavior, unmatched currencies, invalid discount factor, inappropriate regulator label.
- **Business boundary:** Economic value sensitivity, not automatic Basel supervisory IRRBB compliance.

### 11. HC.FTP.01 — Funds Transfer Pricing: сроковая стоимость фондирования

- **TaskCode:** `W4.FTP.01.V1`; **priority:** EXT-P1; **complexity:** T; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D92 (`FTP_CURVE_POINT`) plus optional pinned loan cashflow `HC.LOAN.01`; FTP provides an input to pricing and never depends on `HC.CREDIT.01`.
- **Method-specific typed parameters:** ftpApproach:ENUM(MATCHED_MATURITY,CASHFLOW_WEIGHTED)!; termCurvePolicyRef:REFERENCE!; liquidityPremiumPolicyRef:REFERENCE!; interestDayCountRef:REFERENCE!; fundingSpreadAllocationRef:REFERENCE!; collateralEligibilityRef:REFERENCE?.
- **Mathematics / eligibility:** For an approved single-period cashflow, transfer interest charge=principal×applicable matched-tenor FTP rate×yearFraction; product spread=client interest income−transfer charge. Multi-date products require cashflow-weighted tenor matching, not one universal headline rate.
- **Result metrics:** FTP_TRANSFER_CHARGE:MONEY; FTP_RATE:RATE; PRODUCT_SPREAD:MONEY; MATCHED_TENOR:PERIOD. Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** One year, asset principal=100, customer income=9 (9%), matched FTP=4% ⇒ transfer charge=4 and product spread=5.
- **Hard negative tests:** Wrong currency curve, missing interpolated tenor policy, funding charge double applied in RAROC, transfer charge computed on maturity principal for all amortizing periods.
- **Business boundary:** Internal management pricing transfer, not external market funding quote.

### 12. HC.PRICE.01 — Оптимизация цены с эластичностью и ограничениями

- **TaskCode:** `W4.PRICE.01.V1`; **priority:** EXT-P1; **complexity:** O; **status:** METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.
- **Typed input arrays:** D93 (`PRICE_DEMAND_OBSERVATION`) plus explicitly admitted existing data `HC.COST.04;HC.PLAN.02/04;HC.PLAN.08` when verified; do not assume upstream FIN bindings.
- **Method-specific typed parameters:** demandModelRevision:REFERENCE!; optimizationObjective:ENUM(CONTRIBUTION_PROFIT)!; priceFloor:MONEY_PER_UNIT!; priceCeiling:MONEY_PER_UNIT!; quantityCapacity:QUANTITY?; demandCalibrationWindow:PERIOD!; competitorReactionPolicyRef:REFERENCE?; solverTolerance:DECIMAL!.
- **Mathematics / eligibility:** Initial approved LINEAR_DEMAND variant Q(p)=max(0,a−bp), with b>0, contribution=(p−unitVariableCost)×Q(p)−approvedFixedCost. Optimize only within price floor/ceiling, nonnegative quantity and capacity; future models may be ML-estimated but must satisfy out-of-sample quality and causal/elasticity assumptions.
- **Result metrics:** RECOMMENDED_PRICE:MONEY_PER_UNIT; EXPECTED_QUANTITY:QUANTITY; EXPECTED_CONTRIBUTION:MONEY; SOLVER_STATUS:CODE; OPTIMALITY_GAP:DECIMAL (valueState=MISSING if solver provides no bound). Use existing typed result shapes (AGGREGATE / TIME_SERIES / GROUPED / SCENARIO_MATRIX / OPTIMIZATION_PLAN as applicable) with schema revision.
- **Independent-control arithmetic candidate:** Linear demand Q=120−2p, unit variable cost=20, fixed cost=0, allowed p∈[20,60], unlimited capacity ⇒ optimal p=40, Q=40, profit=800.
- **Hard negative tests:** Negative/zero demand slope asserted as valid, out-of-range price, censored stockout mistaken for zero demand, unqualified model trained on promotional leakage, infeasible constraint treated as optimum.
- **Business boundary:** Recommendation and scenario only, no automatic market repricing.

## 5. Integration dependencies and qualification gates

1. **Schema/registry gate:** unique 12 `HC.*` codes, unique 12 `W4.*.V1` codes, D82–D93 exact range, compatibility with W1–W3, no collisions or untyped parameters. Static catalog lint and reference integrity required.
2. **Methodology gate:** domain reviewer approves applicability, precise time basis, source references, day-count, gross/net treatment, currency/FX, tax/fee scope, ratios and zero-denominator policy. Each model has one independently recomputed numerical sample plus boundary controls.
3. **Runtime gate:** version-pinned `CalcPlan`, deterministic Decimal for accounting money; objective/solver tolerances and iteration limits; explicit `BLOCKED_*` for incomplete inputs. Results cannot silently mutate previously qualified SHA.
4. **Testing gate:** at least one positive golden, one zero/missing case, one date/basis mismatch, one malicious/stale revision and one domain negative per model; parity with any future Rust accelerator is optional until verified.
5. **Financial S2 gate:** standards/regulatory claims (Basel IRRBB, statutory credit rates, banking buffers, IFRS17) remain prohibited without independent review and jurisdiction-specific effective-date policies. Arithmetic `SMOKE_PASS` or CI does **not** grant S2.
6. **ML gate:** experimental demand/retention/risk predictions must record training data provenance, training/validation cutoff, feature availability, drift indicators, out-of-sample calibration, reproducibility and override/human review. ML output is an input scenario, not a replacement for the deterministic result contract.
7. **No unapproved side effects:** model calculation does not book a loan, set a customer price, alter FIN intake/fact revisions, approve a covenant, move cash or generate regulatory submission.

### Required acceptance evidence

| Evidence | Exit condition |
|---|---|
| Contract lint | 95 total **candidate** model codes, 93 typed dataset families, 12 W4 entries, zero duplicates |
| Param proof | Each of 12 models has type, unit, source, allowed range, scope, default policy (explicit/none), effective revision and SHA |
| Golden examples | 12 independent reference calculations; residual or feasible-solution tolerance recorded |
| Negative matrix | At least 60 model-specific negative cases (≥5 per model) before implementation qualification |
| Integration proof | Existing HC.* reused via pinned result/metric definitions; no inferred FIN field binding |
| Governance | S2 HOLD and NO PRODUCTION until separate signed decision for exact method/config/artifact |

## 6. Deferred model extensions (separate approval)

The following are **backlog topics only**. They carry **no** new W4 metric/task codes and are **not** included in the count of 95: prudential LCR and NSFR; portfolio risk/return optimization; IFRS 17 insurance fulfilment cashflows, risk adjustment and contractual service margin; real estate NOI/cap-rate and rent scenarios; energy LCOE/tariff scenarios; jurisdiction-specific regulatory ALM reporting. Existing pricing/portfolio/ALM models cannot be relabeled compliant without prescribed data, reporting horizons, calibration, legal review and S2.

References for future method review (not model admission):
- BIS IRRBB standard: https://www.bis.org/committees/bcbs/basel-framework/standard/srp/31/inforce/2026-01-01/published/2024-07-16
- Basel Framework LCR / NSFR: https://www.bis.org/committees/bcbs/basel-framework
- IFRS Foundation IFRS 17: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/

## 7. Future delivery order (separate coding authorization)

- **W4.A:** CAP.01/.02, CREDIT.01/.02 (pricing economics and financial controls).
- **W4.B:** CUST.01/.02, PF.01/.02 (cohorts and contractual cash waterfalls).
- **W4.C:** ALM.01/.02, FTP.01, PRICE.01 (asset/liability risk, internal term funding, constrained optimization).
- Freeze candidate input/output/parameter contract revisions after independent methodology review, *before* Python reference implementation. No automatic production approval.

**METHOD-HARDENING-R1 pre-freeze:** causal demand elasticity version, stockout censoring, price ticks and integer solver decision domain must be explicit; solver outputs `OPTIMAL_PROVEN` only with eligible bound/tolerance evidence, otherwise `FEASIBLE_NOT_PROVEN`. No automatic external repricing. Addendum §6.

