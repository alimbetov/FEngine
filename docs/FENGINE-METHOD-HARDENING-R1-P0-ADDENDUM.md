# FEngine METHOD-HARDENING-R1 — P0 methodology correction addendum

**Date:** 2026-11-20 · **Status:** PRE-FREEZE DRAFT / INDEPENDENT FINANCIAL REVIEW REQUIRED · **Financial S2:** HOLD · **Engine execution:** NOT IMPLEMENTED.

**Applies to:** existing 95 candidate calculation models (83 W1–W3, 12 W4) without adding any new model code. This addendum supersedes conflicting draft wording **only as a proposed replacement**; no already-issued SHA, published methodological revision, runtime API or production permission is changed. Require independent review, source bindings and golden manifest before freeze. All computations below are independent numerical control candidates, not FIN-qualified accounting entries.

## 1. Shared numeric, applicability and result rules

- Exact business money: decimal string, explicit currency, working precision and rounding stage; never round intermediate ECL hazard/discount or DCF terms to display cents. Statistical simulation may use validated floating-point numerical kernels, but archive monetary aggregates with approved conversion/rounding and error tolerances.
- Rates: \`RATE\` is unit fraction (0.10 = 10%); \`PERCENT\` is 0–100; \`RATIO\` dimensionless. Explicit nominal/effective, simple/compound, real/nominal, effective-from, day-count, discount origin, transaction side and original-versus-revised revision.
- Value missing/undefined/inapplicable must not be silently converted to zero. \`ValueState\` is separate from \`CalculationState\`, solver code and \`reasonCode\`.
- For risk/optimization, tolerances are part of *method binding*, not magic constants. Accepted result needs exact \`inputSha\`, \`paramsSha\`, \`methodSha\`, \`algorithmArtifactSha\`, \`outputSchemaSha\`, pinned source lineage and independent financial admission.
- Priority is correctness and versioning. No Python production algorithm, no new financial table, no implied financial S2 in this change.

## 2. HC.ECL.01–.07 — expected credit loss

**Correction ECL-R1:** \`defaultEventWindow\` and \`cashShortfallRecoveryHorizon\` are distinct. IFRS 9 12-month expected losses originate in defaults possible within 12 months after reporting date; life-of-instrument cash shortfalls from such defaults must still be included. Restrict default dates to remaining expected life when shorter than 12 months. Confirm policy applicability for Stage1/2/3 and POCI independently.

### Typed critical parameter candidates
- \`defaultDefinitionRevision\`: REFERENCE, REQUIRED; default trigger, reporting jurisdiction/entity/product.
- \`creditStageSicrPolicyRef\`: REFERENCE, REQUIRED for Stage1/2 transition; Stage3 and POCI qualification separately.
- \`hazardInputBasis\`: ENUM {CONDITIONAL_PD, MARGINAL_PD}, REQUIRED; cannot mix without explicit conversion.
- \`expectedLifeHorizon\`: PERIOD, REQUIRED; instrument/date-aligned.
- \`defaultEventWindow\`: ENUM {FIRST_12_MONTHS, LIFETIME}, REQUIRED, governed by approved method variant and stage.
- \`cashShortfallRecoveryHorizon\`: PERIOD, REQUIRED and may outlast first 12 months.
- \`discountRatePolicyRef\`: REFERENCE, REQUIRED (original EIR vs credit-adjusted POCI vs eligible method).
- \`scenarioWeightsRef\`: REFERENCE, REQUIRED when scenarios; total weights equals 1 within approved \`scenarioWeightTolerance\` (RATE).
- \`recoverySchedulePolicyRef\`: REFERENCE, REQUIRED when LGD is not pre-discounted; must label cost and recovery dates.
- \`postModelOverlayRevision\`: REFERENCE, CONDITIONAL; must be separately approved, no hidden adjustment.

For discrete conditional hazards \`q[t]\`:
\`S[0]=1; marginalPD[t]=S[t-1]*q[t]; S[t]=S[t-1]*(1-q[t])\`.
On approved simplified scenarios, \`ECL = sum_s weight_s * sum_t marginalPD_s,t * discountedLossGivenDefault_s,t\`; \`discountedLossGivenDefault\` is at a single declared origin and cannot also contain survival probability. For actual cash-shortfall model, discount each projected shortage/recovery event on its own date; \`EAD×LGD\` is a separately approved approximation, never an unconditional default.

**Independent arithmetic golden candidate ECL-1:** q=[0.10,0.20] gives S2=0.72, marginalPD=[0.10,0.18], cumulativePD=0.28, not 0.30.

**Independent arithmetic golden candidate ECL-2:** default probability 0.10 occurs during first 12 months; lifetime loss 50 KZT paid at year 2; discount rate 10% annual => 12-month ECL candidate = 0.10 * 50/(1.1^2) = 4.132231404958... KZT, **not zero** because the loss date is in year 2.

**Negative cases:** Stage2 incorrectly assessed as 12m, POCI using original non-credit-adjusted EIR, negative/over-one conditional hazard, conditional PD summed without survival, later recovery silently excluded, unqualified collateral netting, missing SICR, probability weights not one, EAD/PD cohort misalignment, missing cashflow origin.

## 3. HC.LOAN.01–.08, HC.CREDIT.01/.02, HC.FTP.01 — contractual rates, EIR and pricing

**Correction LOAN-R1:** four distinct semantics must be bound:
1. Contractual nominal rate, \`dayCountRule\`, \`accrualBoundaryPolicy\`, annualization/reset calendar; dated simple interest for eligible simple interest variant: \`principal * annualNominalRate * yearFraction(start,end)\`.
2. Dated payment schedule (annuity/equal-principal/custom) with precise compounding, fees and rounding allocation. Equal-period annuity shortcut is not applicable to arbitrary irregular dates without conversion to dated solver.
3. IFRS 9 EIR: solve \`initialCarrying = sum_k eligibleCash_k/(1+r)^yearFraction_k\` under approved accounting policy; original EIR, fee classification, day-count and algorithm diagnostics are frozen inputs.
4. Kazakhstan GESV: **independent statutory** output, not EIR. Legal act revision, effective date, entity/borrower eligibility, included/excluded charges, cash directions, root protocol and statutory display rule require counsel/regulator approval.

**Critical typed parameter candidates:** \`rateQuoteBasis\` ENUM{NOMINAL_ANNUAL,EFFECTIVE_ANNUAL}; \`dayCountConvention\` ENUM{ACT_365F,ACT_360,ACT_ACT_APPROVED,THIRTY_360_APPROVED}; \`holidayBusinessDayRuleRef\` REFERENCE; \`cashflowSignPerspective\` ENUM{LENDER,BORROWER}; \`interestRoundingStage\` ENUM{PER_PERIOD,AT_FINAL}; \`indexFixingCurveRevision\` REFERENCE for floating; \`rateFloorCapPolicyRef\` REFERENCE conditional; \`feeInclusionPolicyRef\` REFERENCE; \`originalEirPolicyRef\` REFERENCE for modification; \`rootDomainMin\` RATE > -1; \`rootDomainMax\` RATE; \`rootResidualTolerance\` MONEY; \`rootRateTolerance\` RATE; \`multipleRootsPolicy\` ENUM{RETURN_ALL,BLOCK_AMBIGUOUS}; \`gesvLegalActRevision\` REFERENCE and \`gesvEffectiveDate\` LOCAL_DATE for statutory calculation.

**Control LOAN-1:** 1000 KZT, nominal annual 12%, 31-day accrual => ACT/365F interest = 1000*.12*31/365 = 10.191780821917... KZT, ACT/360 = 10.333333... KZT. A silent day-count default changes the result.

**Control LOAN-2:** one-year initial carrying 980 KZT vs eligible repayment 1080 KZT => EIR = 1080/980 - 1 = 0.1020408163265...; this is neither contractual quote nor regulatory Kazakhstan GESV.

**Pricing/RAROC:** independent cashflow origins, funding curve, expected loss, economic capital and fees; do not deduct EL/funding twice through FTP and P&L. \`HC.CREDIT.01\` required explicit profitability target and quote legality; \`HC.CREDIT.02\` economic capital denominator >0 and a period alignment rule. No issued credit offer without separate admission.

## 4. HC.DCF.01–.09, HC.CAP.01/.02 — NPV/XIRR and capital valuation

**Correction DCF-R1:**
- \`NPV(r) = sum_t CF_t/(1+r)^{t}\` for explicitly regular periods; \`XNPV(r) = sum_k CF_k/(1+r)^{yearFraction(d0,dk)}\` only on dated eligible fractional-year basis and declared domain r>-1.
- IRR may have no root, one root, multiple roots or even-multiplicity/tangent roots. Plain sign-change scanning is insufficient for certified all-roots claim. \`rootCompleteness\` ENUM{CERTIFIED_ALL,PARTIAL,UNDETERMINED} and \`rootIsolationAlgorithmRevision\` required; output \`ROOT_SET\` or BLOCK_SINGLE when ambiguous.
- Integer period cashflow polynomials may use symbolic/isolated positive discount-factor roots and verified residuals; irregular-date XIRR usually lacks polynomial completeness proof. Do not assert \`CERTIFIED_ALL\` without a stated certified algorithm and domain.
- For valuation, FCFF/WACC, FCFE/Ke must match. Gordon terminal \`TV = FCFF_(n+1)/(WACC-g)\` requires WACC>g and an evidence-backed stable growth regime. For negative or zero normalized cashflow, domain applicability must be explicitly reviewed.
- WACC from qualified market/target weights and tax-deductibility; CAPM from matched market risk-free tenor/ERP/beta calibration; no arbitrary defaults.

**Critical typed parameters:** \`valuationDate\` LOCAL_DATE; \`discountCompoundingBasis\` CODE allowlist; \`discountDayCountConvention\` CODE allowlist; \`cashFlowTiming\` ENUM{END_PERIOD,MID_PERIOD,EXACT_DATES}; \`rateDomain\` STRUCT; \`rootIsolationAlgorithmRevision\` REFERENCE; \`rootCompletenessPolicy\` ENUM{CERTIFIED_ALL,RETURN_PARTIAL_WITH_REASON,BLOCK}; \`rootTolerance\` RATE; \`npvResidualTolerance\` MONEY; \`maxIterations\` INTEGER; \`cashFlowCurrency\` CODE; \`realNominalPolicy\` ENUM{REAL,NOMINAL}; \`fcffFcfeBasis\` ENUM{FCFF,FCFE}; \`discountRateSourceRevision\` REFERENCE; \`terminalGrowthEvidenceRef\` REFERENCE; \`terminalValueMethod\` ENUM{GORDON,EXIT_MULTIPLE_APPROVED}; \`taxShieldPolicyRef\` REFERENCE.

**Control DCF-1:** CF [-100,230,-132] at t=0,1,2 has exact two IRR roots 0.10 and 0.20.

**Control DCF-2:** CF [-100,200,-100] at t=0,1,2 has root r=0 of multiplicity 2; NPV is negative on either side, so sign-change-only scan misses it.

**Control DCF-3:** FCFF_1=106 KZT, WACC=.09 and g=.03 => Gordon TV=106/.06=1766.666... KZT; if g=.09, formula is inapplicable (zero denominator).

## 5. HC.RISK.01–.07 — quantiles, ES, stochastic scenarios

**Correction RISK-R1:** loss is a declared positive \`LOSS_MAGNITUDE\` or signed P&L transformed by a versioned \`lossSignPolicy\`. At alpha in (0,1), \`VaR_α = inf{x:F(x)>=α}\`. For empirical weighted loss values, sort by value and accumulate **normalized** weight. \`ES_α = (1/(1-α)) * integral_α^1 VaR_u du\`, including only the appropriate fractional mass at the threshold; \`E[L|L>VaR]\` is not generally equivalent with ties.

**Required typed parameters:** \`alpha\` RATE with 0<α<1; \`horizon\` PERIOD; \`lossSignPolicy\` ENUM{POSITIVE_LOSS,SIGNED_PNL_NEGATE}; \`quantileEstimator\` ENUM{EMPIRICAL_LEFT_CDF,PARAMETRIC_APPROVED}; \`weightNormalizationPolicy\` CODE; \`esTailMassRule\` ENUM{QUANTILE_INTEGRAL_FRACTIONAL_ATOM}; \`observationWindow\` PERIOD; \`minimumEffectiveTailSample\` INTEGER; \`prngAlgorithmRevision\` REFERENCE; \`prngSeed\` INT64; \`sampleCount\` INTEGER >0; \`distributionRevision\` REFERENCE; \`correlationMatrixPolicy\` ENUM{REQUIRE_PSD,ALLOW_EXPLICIT_APPROVED_PROJECTION}; \`mcErrorTolerance\` DECIMAL; \`backtestPolicyRef\` REFERENCE.

**Control RISK-1:** losses [0,10,20,20,100] equally weighted; α=.75; empirical left-quantile VaR=20; upper 25% mass includes 20% mass of loss 100 and 5% mass of loss 20. ES=(.2×100+.05×20)/.25=84, not 100.

**Control RISK-2:** weighted loss [0,20,100], weights [.50,.40,.10], α=.75 => VaR=20; top 25% mass has 10%*100 + 15%*20 => ES=52. Probability sum mismatch, negative weights, covariance non-PSD or insufficient tail sample must block with reason not zero.

Monte Carlo errors: fixed PRNG seed proves repeatability only. Forecast validity requires time-blocked train/evaluation windows, tail calibration, confidence/sampling errors, stress periods and independent financial policy. Same sample draws or means are insufficient.

## 6. HC.PLAN/HC.COST/HC.STOCK/HC.PRICE — constrained optimization

**Correction OPT-R1:** \`objectiveDirection\` ENUM{MINIMIZE,MAXIMIZE}, \`decisionDomain\` ENUM{BINARY,INTEGER,CONTINUOUS}, objective units and coefficients, bounds per decision, constraints with unit and sense, \`solverRevision\`, deterministic tie-break, \`timeBudgetMillis\`, \`feasibilityTolerance\`, \`relativeOptimalityGapLimit\`, \`absoluteGapLimit\`, \`boundProvenance\` and \`relaxationPolicy\` required.

Every optimization result exposes \`solverStatus\`: \`OPTIMAL_PROVEN\`, \`FEASIBLE_NOT_PROVEN\`, \`INFEASIBLE\`, \`TIME_LIMIT\`, \`UNBOUNDED\`, \`NUMERICAL_ERROR\`; \`objectiveValue\`, \`primalBound\`, \`dualBound\`, \`gap\`, \`constraintResiduals\`, \`decisionVariableUnits\`. An integer-capex heuristic or a continuous relaxation is not automatically a feasible project portfolio.

**Control OPT-1:** binary projects A: capex6/NPV12, B: capex5/NPV8, budget10 => only A is optimal, objective12, because A+B capex11 violates budget. Fractional B≈0.8 to reach 10 is not permitted in binary model.

**Control OPT-2:** feasible project A objective12 with a certified upper bound14 => relative gap (14−12)/max(1,|12|)=1/6 ≈ 0.1667, so solver cannot report \`OPTIMAL_PROVEN\` at tolerance 0.01.

## 7. HC.COST.03 — explicit 3-factor Price / Total Volume / Mix

**Known semantic defect:** current W2 variant \`PRICE_THEN_VOLUME\` returns \`VOLUME_EFFECT = sum_i (q1_i−q0_i)p0_i\`. This contains **both total-volume and sales-mix changes**, and must not be reported as pure total volume. Do not reinterpret that historical label without an output revision.

Propose *new* draft method variant \`PVM_THREE_FACTOR_SEQUENTIAL_V2\`, task proposal \`W2.COST.03.V2\` and new output schema (not yet frozen/published). For a stable product set, Q0=sum q0_i>0, Q1=sum q1_i>0; base shares s0_i=q0_i/Q0, actual shares s1_i=q1_i/Q1. With prices p0_i,p1_i, define:

- \`priceEffect = sum_i q1_i (p1_i - p0_i)\`;
- \`totalVolumeEffect = (Q1-Q0) * sum_i (s0_i*p0_i)\`;
- \`mixEffect = Q1 * sum_i (s1_i-s0_i)*p0_i\`;
- \`revenueDelta = sum_i q1_i*p1_i - sum_i q0_i*p0_i\`;
- \`reconciliationResidual = revenueDelta - priceEffect - totalVolumeEffect - mixEffect\` = 0 (before display rounding).

**Control PVM-1:** stable prices p=[20,10], q0=[5,5], q1=[8,2]. Q0=Q1=10, priceEffect=0, totalVolumeEffect=0, mixEffect=+30 KZT. Legacy 2-factor “volume” would erroneously classify +30.

**Control PVM-2:** prices p0=[10,20], p1=[12,22], q0=[4,6], q1=[5,5]: base revenue160, new revenue170 => delta10; price=20, total-volume=0, mix=-10 => 10 exactly.

Mandatory params: \`decompositionVariant\` ENUM{LEGACY_PRICE_THEN_QUANTITY,V2_PRICE_TOTAL_VOLUME_MIX}, \`productUniversePolicy\` ENUM{STABLE_SET,EXPLICIT_NEW_SKU_BRIDGE}, \`zeroBaseTotalPolicy\` ENUM{BLOCK_OR_SEPARATE_VARIANT}, \`priceBasisRevision\` REFERENCE, \`refundTaxPolicyRef\` REFERENCE, \`currencyPolicyRef\` REFERENCE, \`interactionAttributionOrder\` ENUM{ACTUAL_QUANTITY_PRICE_FIRST}. If Q0=0, missing prices, new SKUs without base price, returns/negative quantities or noncomparable unit definitions, report explicit block/bridge, not fake mix.

## 8. Source and qualification acceptance / next steps

**Within this hardening task:** draft amendments, param proposal registry, independent Decimal tests, negative/math property cases, CI evidence, and frozen/not-frozen decision. **Not in scope:** mutable FIN financial fact writes, production accounting/IFRS claims, auto-approval, training ML on synthetic fixtures, performance benchmarks without workload.

**After this task:** independent finance reviewer for each changed variant and legal counsel for local GESV; two audited golden cases per model; source-to-FIN verified mapping and exact period/currency; canonical typed parameter definitions, input/output schema and method manifest; THEN per-revision immutable freeze. Financial S2 stays HOLD until supported, even if tests turn green.

### External methodological anchors (applicability must be checked)
- IFRS 9 legal text definition of 12-month ECL: https://www.legislation.gov.uk/eur/2016/2067/annex/division/Appendix/adopted
- BIS explanatory summary of IFRS 9 expected losses: https://www.bis.org/publications/fsi-summary-ifrs-9-and-expected-loss-provisioning-executive-summary
- BIS IRRBB: https://www.bis.org/committees/bcbs/basel-framework/standard/srp/31/inforce/2026-01-01/published/2024-07-16
