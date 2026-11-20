# FEngine Wave 5 — Risk, Hedge & Insurance: математические формулы и контракты
Document ID: FENGINE-W5-RISK-HEDGE-INS-R2-V1 | Дата: 2026-11-20 | Branch: main | Status: REQUIREMENTS_DRAFT / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD

## 1. Область и идентичность
До Wave 5: **95** кандидатных моделей и **D01–D93**. В Wave 5 добавлены **7 HEDGE + 14 INS** с независимыми TaskCode W5.*.V1 и схемами D94–D114. 7 существующих RISK сохраняют их прежние W2/W3 TaskCode: всего **116 моделей-кандидатов**, **114 набора DTO**, при этом 28 формул в новом пополняемом каталоге. Ничего из этого не является запущенным финансовым Python runtime.
Canonical registry: catalog/risk_hedge_insurance_formula_candidates_r2.tsv; wave-only candidates: catalog/model_extensions_r2.tsv. No historical contract SHA is rewritten. Формула — методическая кандидатная запись, а не произвольный исполняемый Python код.

## 2. Типы входных наборов D94–D114
Every row must carry scoped rowKey, field valueState, sourceRevisionRef/SHA, asOf/period and canonical numeric/FX policy. Types: MONEY = exact decimal + currency; RATE = decimal fraction; MONEY_PER_UNIT = exact money per physical unit; FX includes currency pair and quote orientation; REF must be authorized and versioned.

### D94 — FX_FORWARD
`contractId REF; foreignCurrency ISO; domesticCurrency ISO; notionalForeign MONEY; quoteConvention CODE; strike FX; terminalSpot FX?; maturityDate DATE; contractRevision REF`

### D95 — INTEREST_RATE_SWAP_LEG
`swapId REF; legId REF; startDate DATE; endDate DATE; payReceive ENUM; notional MONEY; fixedRate RATE?; floatIndexRef REF?; floatingFixing RATE?; accrualFactor DECIMAL; discountFactor DECIMAL; curveRevision REF`

### D96 — FUTURES_POSITION
`positionId REF; side ENUM; quantityContracts INTEGER; multiplier QUANTITY; entryPrice MONEY_PER_UNIT; exitPrice MONEY_PER_UNIT?; settlementCurrency ISO; marginPolicyRevision REF`

### D97 — OPTION_POSITION
`optionId REF; underlyingId REF; type CALL|PUT; exerciseStyle CODE; strike MONEY_PER_UNIT; expiry DATE; spotAtExpiry MONEY_PER_UNIT?; premium MONEY_PER_UNIT; quantity QUANTITY; sourceRevision REF`

### D98 — HEDGE_RETURN_PAIR
`exposureRef REF; date DATE; changeSpot MONEY; changeFuturesPerUnit MONEY; quantityConversionRef REF; windowId REF; asOf DATE`

### D99 — HEDGE_EFFECTIVENESS_PAIR
`hedgeRelationRef REF; measurementDate DATE; unhedgedChange MONEY; hedgedChange MONEY; designatedHedgeRatio RATIO; creditRiskEffect MONEY?; IFRS9DocumentationRef REF?`

### D100 — HEDGE_PORTFOLIO_SCENARIOS
`portfolioRef REF; scenarioRef REF; candidateRef REF; residualLoss MONEY; hedgeCost MONEY; margin MONEY?; liquidityLimit MONEY?; permitted BOOLEAN`

### D101 — INS_POLICY_COVERAGE
`policyRef REF; groupRef REF; inception DATE; expiry DATE; writtenPremium MONEY; coverageUnits QUANTITY; earnedUnits QUANTITY; currency ISO; basis CODE`

### D102 — INS_UNDERWRITING_RESULT
`portfolioRef REF; period PERIOD; earnedPremium MONEY; incurredLoss MONEY; underwritingExpense MONEY; basis GROSS|NET; currency ISO`

### D103 — INS_CLAIM_EXPOSURE
`cohortRef REF; period PERIOD; exposure QUANTITY; claimCount INTEGER; ultimateClaimCost MONEY; claimDefinitionRef REF; currency ISO`

### D104 — INS_CUMULATIVE_TRIANGLE
`accidentPeriod PERIOD; developmentAge INTEGER; cumulativePaid MONEY?; cumulativeIncurred MONEY?; reportedIncurred MONEY?; caseReserve MONEY?; asOf DATE; triangleBasis CODE`

### D105 — INS_EXPECTED_LOSS_PRIOR
`accidentPeriod PERIOD; earnedPremium MONEY; expectedLossRatio RATE; expectedUltimate MONEY; reportedDevelopmentFraction RATE; evidenceRevision REF`

### D106 — INS_RESERVE_SIMULATION
`modelRunRef REF; drawIndex INT64; simulatedReserve MONEY; weight RATE; seed INT64; prngRevision REF; sourceModelRevision REF`

### D107 — INS_REINSURANCE_TREATY
`treatyRef REF; treatyType ENUM; claimRef REF; coverageDate DATE; quota RATE?; attachment MONEY?; limit MONEY?; grossEligibleClaim MONEY; priority INTEGER; currency ISO`

### D108 — INS_CATASTROPHE_EVENT
`eventSetRef REF; scenarioRef REF; eventProbability RATE; annualAggregateLoss MONEY; timeHorizon PERIOD; geolocationRef REF?; correlationRevision REF`

### D109 — INS_IFRS17_CASHFLOW
`groupRef REF; contractBoundaryRef REF; flowDate DATE; inflowOutflow ENUM; flowAmount MONEY; discountFactor DECIMAL; cashType CODE; riskAdjustmentRef REF; currency ISO`

### D110 — INS_NONFINANCIAL_RISK_CAPITAL
`groupRef REF; riskType CODE; period PERIOD; riskCapital MONEY; costOfCapitalRate RATE; discountFactor DECIMAL; qualifiedMethodRef REF`

### D111 — INS_CSM_MOVEMENT
`groupRef REF; period PERIOD; openingCsm MONEY; accretion MONEY; futureServiceChanges MONEY; currentServiceRelease MONEY; otherAdjustments MONEY?; coverageUnits QUANTITY; model CODE`

### D112 — INS_PAA_LRC_MOVEMENT
`groupRef REF; period PERIOD; openingLrc MONEY; eligiblePremium MONEY; recognizedInsuranceRevenue MONEY; otherQualifiedAdjustments MONEY?; eligibilityRevision REF; lossComponent MONEY?`

### D113 — INS_PRUDENTIAL_CAPITAL
`insurerRef REF; regulatoryDate DATE; legalRuleRevision REF; eligibleCapital MONEY; requiredSolvencyMargin MONEY; currency ISO; evidenceRevision REF`

### D114 — INS_TARIFF_LOAD
`pricingCohortRef REF; expectedClaims MONEY; fixedExpenses MONEY; variableExpenseRate RATE; margin MONEY?; regulatoryTariffRevision REF; period PERIOD; currency ISO`

## 3. Формулы и контрольные сценарии всех 28 моделей

### 01. HC.RISK.01 — W3.RISK.01.V1
**Задача:** W3.RISK.01.FORMULA.V1. **Вход:** D75,D79,D13. **DAG:** HC.DCF.01.

**Математика (формула-кандидат):** `NPV_k=sum_t CF_t,k/(1+r_t,k)^t; mean=sum_k(w_k*NPV_k)/sum_k(w_k)`.

**Варианты/настроечные параметры:** `seed:INT64; prngRevision:REFERENCE; sampleCount:INTEGER; distributionRevision:REFERENCE; convergenceTolerance:RATIO`.

**Синтетический арифметический эталон:** NPV=[-10,0,10,20] equal weights: mean=5.

**Hard gate:** Simulation draws must be scenario-reproducible; no model accuracy implied by arithmetic.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 02. HC.RISK.02 — W3.RISK.02.V1
**Задача:** W3.RISK.02.FORMULA.V1. **Вход:** D76. **DAG:** HC.RISK.01.

**Математика (формула-кандидат):** `VaR_alpha=inf{x:P(L<=x)>=alpha}; empirical nearest-rank=sortedLoss[ceil(alpha*N)-1]`.

**Варианты/настроечные параметры:** `alpha:RATE; lossSign:CODE; horizon:PERIOD; quantileDefinition:CODE; sampleWindow:PERIOD`.

**Синтетический арифметический эталон:** L=[0,10,20,30] alpha=.75 => VaR=20.

**Hard gate:** Quantile/tie policy, weights and tail confidence must be bound; no universal regulatory VaR.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 03. HC.RISK.03 — W3.RISK.03.V1
**Задача:** W3.RISK.03.FORMULA.V1. **Вход:** D76. **DAG:** HC.RISK.02.

**Математика (формула-кандидат):** `ES_alpha=(1/(1-alpha))*integral_alpha^1 VaR_u du`.

**Варианты/настроечные параметры:** `alpha:RATE; quantileDefinition:CODE; tailMassPolicy:CODE; weightedSamplePolicy:CODE; sampleWindow:PERIOD`.

**Синтетический арифметический эталон:** L=[0,10,20,20,100] equiprobable alpha=.75 => ES=84.

**Hard gate:** Do not use mean(loss|loss>VaR) in presence of atoms/ties.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 04. HC.RISK.04 — W2.RISK.04.V1
**Задача:** W2.RISK.04.FORMULA.V1. **Вход:** D26,D27,D51. **DAG:** HC.CASH.02.

**Математика (формула-кандидат):** `Cash_t=Cash_t-1+Inflows_t-Outflows_t+qualifiedFunding_t; Gap_t=max(0,Floor_t-Cash_t)`.

**Варианты/настроечные параметры:** `cashFloor:MONEY; horizon:PERIOD; shockOrderPolicy:CODE; scenarioRevision:REFERENCE; fundingFeedback:CODE`.

**Синтетический арифметический эталон:** Cash0=100; in=10; out=130; floor=0 => Cash1=-20 and gap=20.

**Hard gate:** Separate projected from posted and funding loop; no double shock.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 05. HC.RISK.05 — W3.RISK.05.V1
**Задача:** W3.RISK.05.FORMULA.V1. **Вход:** D77,D81,D19,D22. **DAG:** HC.ECL.02.

**Математика (формула-кандидат):** `DeltaECL=ECL(stressed calibrated PD/LGD/EAD)-ECL(baseline same portfolio)`.

**Варианты/настроечные параметры:** `calibrationRevision:REFERENCE; shockScenario:REFERENCE; scenarioWeights:LIST<RATE>; featureCutoff:LOCAL_DATE`.

**Синтетический арифметический эталон:** EAD=100 LGD=.4 PD=.02=>.8; stress PD=.03=>1.2; delta=.4 (same timing no discount).

**Hard gate:** No direct arbitrary macro PD multiplier; ECL policy must be qualified.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 06. HC.RISK.06 — W3.RISK.06.V1
**Задача:** W3.RISK.06.FORMULA.V1. **Вход:** D26,D27,D75,D79. **DAG:** HC.CASH.03.

**Математика (формула-кандидат):** `P(breach)=sum_k w_k*I(min_t Cash_k,t<Floor_t)/sum_k w_k`.

**Варианты/настроечные параметры:** `horizon:PERIOD; floor:MONEY; boundary:CODE; samplingPolicy:CODE; ciMethod:CODE`.

**Синтетический арифметический эталон:** Four equally weighted paths with two breached => probability .5.

**Hard gate:** Weighted paths/first-passage and confidence intervals not inferred from four samples.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 07. HC.RISK.07 — W3.RISK.07.V1
**Задача:** W3.RISK.07.FORMULA.V1. **Вход:** D78,D51,D29,D13. **DAG:** HC.DCF.09.

**Математика (формула-кандидат):** `DeltaOutput=F(base plus joint admissible rate/FX/CAPEX shocks)-F(base)`.

**Варианты/настроечные параметры:** `shockDagRevision:REFERENCE; covarianceRevision:REFERENCE; fxQuoteOrientation:CODE; shockOrder:CODE`.

**Синтетический арифметический эталон:** CAPEX100*(1+.2)=120; USD10*FX(550-500)=500 KZT extra cost.

**Hard gate:** Joint matrix must be PSD; no doubling FX or CAPEX shocks.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 08. HC.HEDGE.01 — W5.HEDGE.01.V1
**Задача:** W5.HEDGE.01.FORMULA.V1. **Вход:** D94. **DAG:** HC.CASH.07.

**Математика (формула-кандидат):** `LongForeignForwardPayoff=Q_foreign*(Spot_T-Forward_K); NetUnderlyingPurchaseCost=Q_foreign*Spot_T-Payoff`.

**Варианты/настроечные параметры:** `baseCurrency:ISO4217; quoteCurrency:ISO4217; forwardRate:FX; maturityDate:LOCAL_DATE; discountCurveRef:REFERENCE`.

**Синтетический арифметический эталон:** Buy USD100 at forward K=500, spotT=540 KZT/USD => payoff4000 KZT, net purchase cost50000 KZT.

**Hard gate:** Payoff not fair value or legal hedge accounting; spot/forward orientation and collateral excluded.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 09. HC.HEDGE.02 — W5.HEDGE.02.V1
**Задача:** W5.HEDGE.02.FORMULA.V1. **Вход:** D95. **DAG:** HC.LOAN.01.

**Математика (формула-кандидат):** `PV_receiveFloatPayFixed=sum_i DF_i*N_i*(L_i-K)*tau_i (simplified same currency no exchange)`.

**Варианты/настроечные параметры:** `fixedLegScheduleRef:REFERENCE; floatingIndexRef:REFERENCE; dayCount:CODE; discountCurveRef:REFERENCE; resetLagDays:INTEGER`.

**Синтетический арифметический эталон:** N=1000, L=.12, fixed K=.10, tau=1, DF=.95 => PV=19 KZT.

**Hard gate:** Forward/reset fixing, basis, collateral discounting, principal exchange and cross-currency variant qualified separately.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 10. HC.HEDGE.03 — W5.HEDGE.03.V1
**Задача:** W5.HEDGE.03.FORMULA.V1. **Вход:** D96. **DAG:** HC.RISK.04.

**Математика (формула-кандидат):** `ShortFuturesPnL=N_contracts*contractMultiplier*(F_entry-F_exit)`.

**Варианты/настроечные параметры:** `positionSide:CODE; contractMultiplier:QUANTITY; settlementCurrency:ISO4217; expiry:LOCAL_DATE; marginPolicyRef:REFERENCE`.

**Синтетический арифметический эталон:** Short 5 contracts, 10 units/contract, F_entry120 F_exit110 => PnL=500 KZT.

**Hard gate:** Daily marking and cash margin distinct from terminal PnL; basis risk and margin calls not ignored.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 11. HC.HEDGE.04 — W5.HEDGE.04.V1
**Задача:** W5.HEDGE.04.FORMULA.V1. **Вход:** D97. **DAG:** HC.RISK.01.

**Математика (формула-кандидат):** `ProtectivePutNetPayoff=Q*max(K-Spot_T,0)-Q*Premium0 (undiscounted nominal)`.

**Варианты/настроечные параметры:** `optionType:CODE; exerciseStyle:CODE; premiumPerUnit:MONEY_PER_UNIT; expiry:LOCAL_DATE; volatilityModelRef:REFERENCE`.

**Синтетический арифметический эталон:** Q=10 put contracts per unit, K100, spot80, premium5/unit => payoff net150 KZT.

**Hard gate:** Terminal payoff not option fair value; American/exotic optionality separately modeled.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 12. HC.HEDGE.05 — W5.HEDGE.05.V1
**Задача:** W5.HEDGE.05.FORMULA.V1. **Вход:** D98. **DAG:** HC.RISK.07.

**Математика (формула-кандидат):** `h_star=Cov(DeltaSpotValuePerUnit,DeltaFuturesValuePerUnit)/Var(DeltaFuturesValuePerUnit)`.

**Варианты/настроечные параметры:** `returnWindow:PERIOD; covarianceMethod:CODE; unitConversionRef:REFERENCE; hedgeConstraints:STRUCT; minimumObs:INTEGER`.

**Синтетический арифметический эталон:** Cov=12, VarF=16 => h*=.75 dimension-adjusted exposure hedge ratio.

**Hard gate:** Variance zero => UNDEFINED; sample lookahead and changing hedging objectives; not hedge-accounting qualification.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 13. HC.HEDGE.06 — W5.HEDGE.06.V1
**Задача:** W5.HEDGE.06.FORMULA.V1. **Вход:** D99. **DAG:** HC.HEDGE.05.

**Математика (формула-кандидат):** `VarianceReduction=1-Var(HedgedValueChanges)/Var(UnhedgedValueChanges)`.

**Варианты/настроечные параметры:** `hedgeDesignationRef:REFERENCE; effectivenessMethod:CODE; creditRiskGate:CODE; sampleWindow:PERIOD; hedgeRatioRevision:REFERENCE`.

**Синтетический арифметический эталон:** Var unhedged100, hedged25 => 75% variance reduction.

**Hard gate:** Unhedged variance=0 => UNDEFINED; economic 75% reduction is not automatic IFRS9 hedge-accounting pass.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 14. HC.HEDGE.07 — W5.HEDGE.07.V1
**Задача:** W5.HEDGE.07.FORMULA.V1. **Вход:** D100. **DAG:** HC.HEDGE.01;HC.RISK.03.

**Математика (формула-кандидат):** `min_positions riskMeasure(NetExposureAcrossScenarios)+lambda*HedgeCost subject to limits; record feasibility and bound gap`.

**Варианты/настроечные параметры:** `riskObjective:CODE; lambda:RATIO; capitalBudget:MONEY; positionBounds:STRUCT; solverGap:RATIO; solverTimeoutMs:INTEGER`.

**Синтетический арифметический эталон:** With lambda=1, A residual30+hedgeCost10=>40, B residual50+cost5=>55; choose A among two eligible candidates.

**Hard gate:** Test compares two finite choices, not global optimizer proof; liquidity/margin/credit and integrality constraints required.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 15. HC.INS.01 — W5.INS.01.V1
**Задача:** W5.INS.01.FORMULA.V1. **Вход:** D101. **DAG:** HC.CASH.04.

**Математика (формула-кандидат):** `EarnedPremium=WrittenPremium*EarnedCoverageUnits/TotalCoverageUnits; Unearned=WrittenPremium-Earned`.

**Варианты/настроечные параметры:** `earningPattern:CODE; coverageCalendarRef:REFERENCE; midtermChangePolicy:CODE; cancellationPolicy:CODE; reportingBasis:CODE`.

**Синтетический арифметический эталон:** Written premium1200 KZT; 90 earned of 360 uniformly weighted coverage days => earned300; unearned900.

**Hard gate:** Analytical earned premium/UPR not IFRS17 insurance revenue or PAA without formal eligibility and service rules.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 16. HC.INS.02 — W5.INS.02.V1
**Задача:** W5.INS.02.FORMULA.V1. **Вход:** D102. **DAG:** HC.INS.01.

**Математика (формула-кандидат):** `LossRatio=IncurredClaims/EarnedPremium; ExpenseRatio=UnderwritingExpenses/EarnedPremium; Combined=LossRatio+ExpenseRatio (same basis)`.

**Варианты/настроечные параметры:** `numeratorClaimsBasis:CODE; underwritingExpenseScope:CODE; premiumDenominator:CODE; grossNetBasis:CODE; lossAdjustmentExpense:CODE`.

**Синтетический арифметический эталон:** Incurred60 earned100 expenses25 => LR=.60 ER=.25 combined=.85.

**Hard gate:** Use matched earned premiums and expense/claims definitions; IFRS17 P&L not directly same as statutory combined ratio.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 17. HC.INS.03 — W5.INS.03.V1
**Задача:** W5.INS.03.FORMULA.V1. **Вход:** D103. **DAG:** HC.INS.02.

**Математика (формула-кандидат):** `Frequency=ClaimCount/ExposureUnits; Severity=TotalUltimateClaimCost/ClaimCount; PurePremium=Frequency*Severity`.

**Варианты/настроечные параметры:** `exposureUnit:CODE; claimDefinitionRef:REFERENCE; ultimateClaimsBasis:CODE; largeLossCapping:CODE; reportingPeriod:PERIOD`.

**Синтетический арифметический эталон:** 20 claims /1000 exposure-years, severity500 KZT/claim => frequency .02; pure premium10 KZT/exposure-year.

**Hard gate:** Zero count severity undefined; claims with no reported losses, inflation and development qualification.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 18. HC.INS.04 — W5.INS.04.V1
**Задача:** W5.INS.04.FORMULA.V1. **Вход:** D104. **DAG:** HC.INS.03.

**Математика (формула-кандидат):** `CDF_age=product selectedLDFs; Ultimate=LatestCumulativePaid*CDF_age; Unpaid=Ultimate-PaidToDate; IBNR=Ultimate-IncurredToDate (qualified paid-based development view)`.

**Варианты/настроечные параметры:** `triangleBasis:CODE; selectedLdfRevision:REFERENCE; tailFactor:DECIMAL; calendarInflationPolicy:CODE; zeroTrianglePolicy:CODE`.

**Синтетический арифметический эталон:** Paid100, selected CDF1.5 => ultimate150, unpaid50; incurred130 => IBNR20 and case reserve30.

**Hard gate:** Age-to-age aggregation needs enough credible cells; paid vs incurred triangles must never be silently mixed.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 19. HC.INS.05 — W5.INS.05.V1
**Задача:** W5.INS.05.FORMULA.V1. **Вход:** D104,D105. **DAG:** HC.INS.04.

**Математика (формула-кандидат):** `BF_Ultimate=ReportedIncurred+ExpectedUltimate*(1-ReportedDevelopmentFraction); BF_IBNR=BF_Ultimate-ReportedIncurred`.

**Варианты/настроечные параметры:** `expectedLossRatioRevision:REFERENCE; developmentFraction:RATE; selectedPatternRef:REFERENCE; accidentYear:PERIOD; credibilityBasis:CODE`.

**Синтетический арифметический эталон:** ReportedIncurred80, expectedUltimate120, reported development fraction .5 => BF ultimate140, IBNR60.

**Hard gate:** Reported incurred vs paid basis must match selected pattern; do not default missing ELR.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 20. HC.INS.06 — W5.INS.06.V1
**Задача:** W5.INS.06.FORMULA.V1. **Вход:** D106. **DAG:** HC.INS.04;HC.RISK.02.

**Математика (формула-кандидат):** `ReserveMean=sum_k w_k*R_k/sum w_k; ReserveVaR_alpha=weightedQuantile(R_k,alpha); TailRisk=ES_alpha(R_k)`.

**Варианты/настроечные параметры:** `methodVariant:CODE; quantileAlpha:RATE; simulationSeed:INT64; triangleResamplingRevision:REFERENCE; tailSampleMinimum:INTEGER`.

**Синтетический арифметический эталон:** Reserve scenarios [10,20,30,40] KZT equal weights => mean25; nearest-rank VaR_.75=30.

**Hard gate:** Quantile from four outcomes illustrative only; stochastic fit and MSEP/bootstrapping require actuarial evidence.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 21. HC.INS.07 — W5.INS.07.V1
**Задача:** W5.INS.07.FORMULA.V1. **Вход:** D107. **DAG:** HC.INS.04.

**Математика (формула-кандидат):** `QuotaCeded=q*EligibleClaim; XolCeded=min(max(EligibleClaim-Attachment,0),Limit); NetClaim=Claim-EffectiveCeded`.

**Варианты/настроечные параметры:** `treatyType:CODE; attachment:MONEY; limit:MONEY; quota:RATE; reinstatementPolicy:CODE; counterpartyCreditGate:CODE`.

**Синтетический арифметический эталон:** Claim1000 KZT and quota q=.3 -> ceded300 net700; separate XoL attachment500 limit300 -> ceded300 net700.

**Hard gate:** Single-treaty examples; layered treaties require priority, erosion, aggregation and deductibles.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 22. HC.INS.08 — W5.INS.08.V1
**Задача:** W5.INS.08.FORMULA.V1. **Вход:** D108. **DAG:** HC.RISK.02.

**Математика (формула-кандидат):** `AAL=sum_j p_j*EventLoss_j (exclusive event distribution); PML_alpha=LossQuantile_alpha by horizon/exceedance definition`.

**Варианты/настроечные параметры:** `eventSetRevision:REFERENCE; occurrenceAggregateBasis:CODE; horizon:PERIOD; pmlQuantileAlpha:RATE; correlationRevision:REFERENCE`.

**Синтетический арифметический эталон:** One Bernoulli event p=.01 loss1000 KZT => AAL10; VaR_.995=1000 under nearest-rank distribution definition.

**Hard gate:** Occurrence PML vs aggregate PML and return period differ; no confusion VaR_.99=0 in Bernoulli example.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 23. HC.INS.09 — W5.INS.09.V1
**Задача:** W5.INS.09.FORMULA.V1. **Вход:** D109. **DAG:** HC.INS.10.

**Математика (формула-кандидат):** `FCF_liability=PV(outflows)-PV(inflows)+RiskAdjustmentNonFinancial (positive liability sign)`.

**Варианты/настроечные параметры:** `ifrs17GroupRevision:REFERENCE; cashflowBoundaryRef:REFERENCE; discountCurveRef:REFERENCE; riskAdjustmentRevision:REFERENCE; measurementModel:CODE`.

**Синтетический арифметический эталон:** PV inflows120, PV outflows100, RA15 => FCF=-5 KZT; not full insurance liability without CSM.

**Hard gate:** FCF is not CSM or total LRC/LIC; contract groups, financial risks, cashflow boundary and nonfinancial risk RA need IFRS17 approval.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 24. HC.INS.10 — W5.INS.10.V1
**Задача:** W5.INS.10.FORMULA.V1. **Вход:** D110. **DAG:** HC.INS.06.

**Математика (формула-кандидат):** `RA_CoC=sum_t DF_t*CoC_t*RequiredNonFinancialRiskCapital_t (chosen cost-of-capital variant)`.

**Варианты/настроечные параметры:** `riskAdjustmentMethod:CODE; confidenceLevelEquivalent:RATE; riskCapitalDefinitionRef:REFERENCE; diversificationPolicy:CODE; capitalCostCurveRevision:REFERENCE`.

**Синтетический арифметический эталон:** Capital100 KZT, CoC=.06, DF=.95 for year => RA5.70 KZT.

**Hard gate:** IFRS17 does not mandate cost-of-capital formula; require disclosure, specific non-financial risk and independent actuarial review.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 25. HC.INS.11 — W5.INS.11.V1
**Задача:** W5.INS.11.FORMULA.V1. **Вход:** D111. **DAG:** HC.INS.09.

**Математика (формула-кандидат):** `ClosingCSM=OpeningCSM+eligibleAccretion+futureServiceChanges-CurrentServiceRelease+otherApprovedMovements`.

**Варианты/настроечные параметры:** `ifrs17MeasurementModel:CODE; coverageUnitsRuleRef:REFERENCE; lockedInRateRef:REFERENCE; lossComponentPolicyRef:REFERENCE; csmChangeClassification:CODE`.

**Синтетический арифметический эталон:** Opening CSM10, accretion1, future-service change3, release4 => close10 KZT.

**Hard gate:** No unconditional CSM = max(-FCF,0) across reinsurance/VFA/onerous; no release without coverage units.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 26. HC.INS.12 — W5.INS.12.V1
**Задача:** W5.INS.12.FORMULA.V1. **Вход:** D112. **DAG:** HC.INS.01;HC.INS.09.

**Математика (формула-кандидат):** `ClosingLRC=OpeningLRC+EligiblePremiumReceived-RecognizedInsuranceRevenue+QualifiedOtherMovements (simplified no acquisition/financing)`.

**Варианты/настроечные параметры:** `paaEligibilityRevision:REFERENCE; financingComponentPolicy:CODE; acquisitionCashFlowPolicy:CODE; onerousLossComponentRef:REFERENCE; revenueAllocationMethod:CODE`.

**Синтетический арифметический эталон:** Opening LRC100, qualifying premiums50, recognized insurance revenue60 => closing LRC90 KZT (no other movements).

**Hard gate:** PAA eligibility and LIC measured separately; do not infer IFRS17 revenue as simple UPR by default.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 27. HC.INS.13 — W5.INS.13.V1
**Задача:** W5.INS.13.FORMULA.V1. **Вход:** D113. **DAG:** HC.INS.09.

**Математика (формула-кандидат):** `IllustrativeAdequacyRatio=EligibleOwnFunds/RequiredSolvencyMargin for approved regulatory definitions only`.

**Варианты/настроечные параметры:** `jurisdiction:CODE; regulatorRuleRevision:REFERENCE; ruleEffectiveDate:LOCAL_DATE; eligibleCapitalEvidenceRef:REFERENCE; prudentialThresholdRef:REFERENCE`.

**Синтетический арифметический эталон:** Hypothetical eligible own funds150, required margin100 => adequacy1.5 (not statutory eligibility certification).

**Hard gate:** Regulator-specific eligible capital, margins, insurance class, adjustments and reporting schema require legal version; do not publish statutory indicator from this simplified quotient.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

### 28. HC.INS.14 — W5.INS.14.V1
**Задача:** W5.INS.14.FORMULA.V1. **Вход:** D114. **DAG:** HC.INS.03.

**Математика (формула-кандидат):** `GrossRiskPremium=(ExpectedClaims+FixedExpenses)/(1-VariableExpenseShare) for declared linear gross-premium loading variant`.

**Варианты/настроечные параметры:** `tariffPricingPolicyRef:REFERENCE; claimSeverityCalibrationRef:REFERENCE; expenseLoadShare:RATE; marginAndTaxPolicy:CODE; jurisdictionRestrictionRef:REFERENCE`.

**Синтетический арифметический эталон:** Expected claims60, fixed expenses20, variable load20% => gross premium100 KZT.

**Hard gate:** Variable load>=1 invalid, regulatory tariff caps, solvency margins and profit not inferred from simplified formula.

**Результат:** версионируемый CalculationResponseDTO.results[].rows[].values[] с точным method revision, currency/period/units, source/result SHA, typed INVALID/BLOCKED/UNDEFINED state and reason. No FIN/IFRS approval is implied.

## 4. Граница между математическими и нормативными методиками
### 4.1. IFRS 9 hedge accounting vs экономическая эффективность
Выигрыш по форварду, фьючерсу, опциону или variance reduction не означает права применять hedge accounting. IFRS 9 требует официальной документации инструмента, статьи, риска, экономической связи, недоминирования кредитного риска и фактически применяемого hedge ratio. Нельзя использовать универсальную автоматическую границу 80–125% в качестве допуска по IFRS 9. Межвалютные ставки, forward curves, reset/fixing/collateral and counterparty credit effects обязательны при полной оценке PV, а упрощённые payoff-примеры не равны fair value.
### 4.2. Страховые аналитические и актуарные резервы
UPR по времени, earned premium, loss/combined ratio, claim frequency/severity and actuarial ultimate are not IFRS 17 insurance revenue, total insurance contract liability or statutory reserves. Different recognition and reporting bases use distinct modelCode and methodVariant revision.
Chain Ladder must use a credible cumulative triangle, consistent paid or incurred development pattern, selected age-to-age factors and tail. Ultimate−paid = expected unpaid (reported reserves + IBNR/IBNER), not necessarily IBNR. Bornhuetter–Ferguson combines reported information with **independently estimated** expected ultimate and maturity; parameters cannot be estimated solely from the same incomplete triangle without evidence.
Reinsurance example applies one treaty at a time; treaty stacking, attachment, limits, aggregate reinstatement and counterparty recovery require new recognized variants. Cat PML requires occurrence-vs-aggregate definition, exceedance/quantile convention and correlation, not just one VaR label.
### 4.3. IFRS 17
IFRS 17 measures groups of contracts through probability-weighted fulfilment cashflows (discounted future cashflows + risk adjustment for non-financial risk) plus, where applicable, contractual service margin (CSM). Simplified FCF, RA_CoC, CSM roll-forward and PAA examples are educational/contract candidates, not complete IFRS 17 formulas. CSM depends on coverage units, locked-in rates, changes relating to future service, onerous groups, GMM/PAA/VFA classification, held reinsurance and contract boundary. Cost-of-capital is just one RA valuation method; it is not mandated as a universal IFRS 17 formula.
### 4.4. Пруденциальная платёжеспособность РК
For INS.13 the ratio of independently qualified eligible own funds to required solvency margin can be defined mathematically. Actual RK regulatory formulas, insurance class, admitted capital adjustments, legally applicable effective-date rules and actuarial review MUST be checked and bound before naming a result statutory. A demo 150/100=1.5 is not legal compliance certification.

## 5. Параметризация и приёмка до contract freeze
- Register every parameter under MethodParameterContractV2: logicalType, unit/currency, R/C/O applicability per variant, enum domain, min/max, default origin, legal/regulatory revision, effective dates, signed source and SHA; no arbitrary string formulas.
- Mandatory common fields: inputSchemaRevision, methodVariantRevision, paramsSha, numericPolicySha, resultShapeRevision, period/asOf, tenant/scope, sourceFactSetSha, algorithmManifestSha, reviewerDecision, calculation job/result state and reason.
- Independent golden bank: at least two real independently checked examples and explicit negative cases for each of 21 new models; existing 7 RISK reuse old negative tests and add tail mass/correlation/weights cases.
- Scenario/unit tests: missing vs zero, FX orientation, interest date convention, negative and reversal events, recovery and settlement, empty triangles/zero denominators, no root, quantile ties, heterogenous treaty units and incomplete regulatory evidence.
- Statistical models require calibration, temporal holdout, Monte Carlo convergence, uncertainty/backtest and independent actuarial sign-off; optimization uses feasibility/optimality gap and time-budget.
- No financial S2, source mapping to actual FIN tables, ISO currency qualification, executable Python HC engine or production admission is claimed by this wave.

## 6. Источники для последующей финансовой верификации
- IFRS Foundation — IFRS 17: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/
- IFRS 17 adopted text: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021R2036
- IFRS 9 hedge accounting: https://standards.aasb.gov.au/node/4292
- IFRS Foundation hedging and separate measurement: https://www.ifrs.org/news-and-events/updates/ifric/2021/ifric-update-april-2021/
- CAS reserving methodologies: https://www.casact.org/abstract/introduction-ratemaking-and-loss-reserving-for-property-and-casualty-insurance
- Kazakhstan actuarial reserves and Chain Ladder / BF: https://actuaries.org.kz/en/documents/reg-reserves-2019/
- Kazakhstan insurance liabilities IFRS — 84: https://actuaries.org.kz/en/documents/reg-reserves-84/
- Kazakhstan prudential requirements: https://actuaries.org.kz/en/documents/reg-prudential-304/
- Kazakhstan insurance activities law: https://old.adilet.zan.kz/eng/docs/Z000000126_

**Release:** FORMULAS_CATALOGUED / METHOD_CANDIDATE / FREEZE_HOLD / NO IMPLEMENTATION.
