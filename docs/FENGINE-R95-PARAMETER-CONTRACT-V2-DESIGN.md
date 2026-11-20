# FEngine R95 — MethodParameterContractV2 / pre-freeze schema design

**ID:** FENGINE-R95-PARAM-V2-DRAFT · **2026-11-20** · **NOT QUALIFIED / NOT FROZEN**

## 1. Scope / rule

Design-only contract that applies to **all 95** HC model candidates. Existing 83 individual rows use \`docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv\`; the 95-row consolidated audit matrix adds W4. Proposed fields in these files are **not yet reviewed canonical parameter contracts**. Do not silently retrofit old immutable method SHA. After review, create new MethodRevision/ParamsRevision/InputSchemaRevision/OutputSchemaRevision.

## 2. ParameterDefinition (one row per parameter of each method variant)

| Field | Type / rule | Mandatory |
|---|---|---|
| modelCode, taskCode, methodVariantCode | allowlisted stable codes, versioned | yes |
| parameterCode, parameterRevision | stable local code + immutable revision | yes |
| logicalType | DECIMAL / MONEY / RATE / RATIO / INTEGER / BOOLEAN / ENUM / CODE / REFERENCE / LOCAL_DATE / PERIOD / LIST / STRUCT | yes |
| unitCode, currencyPolicy | explicitly defined when dimensional; not omitted in MONEY / QUANTITY | conditional |
| requiredness | REQUIRED / OPTIONAL / CONDITIONAL | yes |
| requiredWhen, forbiddenWhen | typed, canonical pure predicates referencing approved parameters only | conditional |
| allowedEnum / allowlistedValueSetRevision | pinned version, no dynamic free strings for policy codes | when enum/code |
| minInclusive/maxInclusive/minExclusive/maxExclusive; step | inclusive/strict range, precision, normalised coordinate | when numerical |
| shapeConstraints | max list length; row uniqueness; temporal sort; matrix PSD/symmetry and timezone | when structured |
| defaultPolicy | NONE / LITERAL / FROM_IMMUTABLE_POLICY / FROM_SOURCE_REVISION | yes |
| defaultValue, defaultSourceRef | pinned deterministic origin; no implicit client defaults | conditional |
| effectiveFrom/effectiveTo | as-of and jurisdiction/sector/dataset basis | yes |
| applicabilities | entity class, sector, accounting basis, jurisdiction and product class | yes |
| sourceEvidenceRef / policyRevisionRef | immutable independently reconstructible sources and SHA | yes |
| overridePolicy and approvalAuthority | never allow unapproved overrides of legal/financial semantics | yes |
| crossParameterConstraints | unit, period, currency, probability sum, solver-domain coherence, mutual exclusion | yes |
| numericPolicyRef | Decimal precision/scale, intermediate vs report rounding, residual tolerance | yes |
| algorithmManifestSha, parameterContractSha, schemaRevision | cryptographically bound to CalcPlan before execution | yes |

A parameter binding may be published only when every resolved value has canonical type, source, effective date and validation outcome; **no placeholder constants** such as “5% by default” are allowed without a qualified policy.

## 3. Core immutable execution fingerprint

\`CalcPlanSha = SHA256(canonical(tenantScope, sourceFactSetSha, methodRevisionSha, inputSchemaRevisionSha, paramsRevisionSha, resolvedParamsSha, outputSchemaRevisionSha, numericPolicySha, algorithmArtifactSha, dependencyPlanSha, scenarioRevisionSha, admissionRevisionSha))\`

This is a **design formula**, not a tested cryptographic wire format. Canonicalisation must freeze encoding, ordering, scalar Decimal string, timezone/date, normalisation, null/valueState, unicode and collection order; implement JSON canonicalization or an equivalent explicitly versioned deterministic serializer and test cross-language parity. A revision cannot be qualified without the actual signed manifest and SHA.

**Separate enums:** \`JobState\` (lifecycle), \`CalculationState\` (execution outcome), \`ValueState\` (data meaning), and \`reasonCode\` (why a result blocked or undefined). Do not silently insert new statuses into existing W1/W2/W3 response enums. For optimization output include \`solverStatus\` (OPTIMAL_PROVEN / FEASIBLE_NOT_PROVEN / INFEASIBLE / TIME_LIMIT / NUMERICAL_ERROR), objective, primal/dual bounds where applicable, gap, feasibility residual, tolerance, runtime and solver version.

## 4. Mandatory family-level parameter candidates (must be resolved BEFORE contract freeze)

| Family / models | Parameter candidates that must become typed, sourced and reviewed | Blocks if absent |
|---|---|---|
| SET.01–.07 | eventEffectiveCutoff, postingCutoff, allocation order, due date and grace, reversal/overpayment treatment, enforceable offset evidence | invalid balances, aging, netting |
| ECL.01–.07 | defaultDefinitionRev, SICRRuleRev, Stage/POCI policy, marginal-vs-conditional PD, 12mDefaultWindow, cashShortfallRecoveryHorizon, lifetimeTermination, EIR basis, stage transitions, cure/writeoff, recovery cost and collateral policy, CCF and macro weights, calibration effective periods | ECL overstated/understated, wrong stage |
| LOAN.01–.08 | quoteBasis, accrual dayCount, reset/index vintage, compounding, cash direction, fee eligibility by policy, original/revised EIR, irregular-date root domain, prepayment, rounding, jurisdictional GESV regulation effectiveDate and subject/fee matrix | unqualified interest/EIR/APR |
| CASH.01–.08 | forecast-vs-actual, reporting period, restricted cash, FX rate vintage/direction, reversal controls, classification and reconciliation tolerance | incorrect liquidity/CFO |
| DCF.01–.09 | valuationDate, discountConvention, annualisation, rootIsolationMethod, rootCompleteness, rootDomain, multiple/tangent/noRoot reason, FCFE/Ke and FCFF/WACC compatibility, currency and real/nominal policy, terminalGrowth validation, cashflow timing | misleading valuation/IRR |
| ACC.01–.07 | reportingBasis, consolidation perimeter, minority/NCI/OCI, hyperinflation, lease policy, tax rule revision, elimination and FX exchange methodology | incorrect accounting balances |
| STOCK.01–.07 | lot ordering, inventory valuation variant, returns, adjustment event precedence, negative-stock policy, FX/unit conversion, NRV classification, shelf life and safety stock calibration | quantity and COGS inconsistency |
| ASSET.01–.07 | component recognition, useful-life version, date cutoffs, tax/accounting basis, impairment CGU, salvage value, reassessment and revaluation policy | carrying value wrong |
| COST.01–.08 | cost driver allocator, resource units, **true price/total-volume/mix decomposition variant**, EVM baseline, BoQ rate evidence, inflation, business unit aggregation | PVM semantic defect and wrong allocations |
| PLAN.01–.08 | forecasting horizon/baseline, objective direction, integer/binary domains, budget/capacity, solver, gap, tie rule, resource budget, calendar, scenario probability | false feasible/optimal status |
| RISK.01–.07 | positiveLossDefinition, quantileEstimator, confidenceLevel, ES tailMassRule, horizon, weights, PRNG/seed, minimumSamples, distributionRevision, PSD correlation policy, tailBacktestMethod, scenario shock order and first-passage threshold | invalid VaR/ES and weak Monte Carlo evidence |
| CAP.01/.02 | riskFreeCurveRev, tenor, equityBetaCalibration, leverage/unlever policy, country/size-premium overlap, market/target weights, cashflow currency, tax-shield and FCFF alignment | incorrect Ke/WACC |
| CREDIT.01/.02 | fundingTermCurveRev, expectedLossAttribution, economicCapitalDefinition, profitabilityTarget, fees, discounting, permitted quote ranges and quote-vs-EIR/GÉSV distinction | double-counted costs |
| CUST.01/.02 | cohort grain PER_CUSTOMER/COHORT_TOTAL, acquisition attribution, margin definition, discount origin, retention/censoring policy, payback missing state and interpolation eligibility | double-counted customer survival/CAC |
| PF.01/.02 | CFADS accounting and contract definition, debt/project life boundaries, discountCurve vintage, waterfall priority revision, restricted cash/DSRA, shortfall ordering | false covenant and cash distributions |
| ALM.01/.02 | behavioral deposit model, maturity/repricing, scenario yield curves, option model, currency bucketing, ΔNII/ΔEVE horizon and stress aggregation | invalid rate-risk result |
| FTP.01 | matched maturity curve, interpolation, liquidity premium, funding spread attribution, product amortization | incorrect internal margin |
| PRICE.01 | causal demand/calibration version, price floor/ceiling/tick, elasticity variant, stockout censoring, feasible capacity, solver tolerance/gap and human approval | unqualified price optimum |

## 5. Prioritization before further performance work

**Gate A (correctness P0):** HC.COST.03 true PVM, ECL hazard/horizon, LOAN day-count/EIR/GESV, DCF root completeness, RISK VaR/ES quantile-integral, OPT integer/solver status, W4 CAP/CREDIT/ALM parameter sources.

**Gate B (review P1):** source-to-FIN fields + normalized units, period/currency and fresh policy dates, independent worked examples (min 2 per model, 95 models), negative & boundary tests. W4 cannot inherit S2 from analogous old model.

**Gate C (freeze candidate):** formal machine-readable ParameterDefinition rows, canonical wire DTO schemas, golden manifest/SHA and independent sign-offs; freeze each qualified revision only, never the entire 95-model catalogue wholesale.

**Gate D (runtime):** Python Decimal reference, durable idempotent job/result and full execution test bank; only after PASS measure JDBC/Rust speed. GPU, cached histograms or ML inference cannot fix a financially false formula.

## 6. ML-facing parameters (shadow mode only)

\`predictionModelRev\`, \`trainingDatasetSha\`, \`featureSchemaSha\`, \`featureAvailabilityTime\`, \`labelDefinitionRev\`, \`timeSplitPolicySha\`, \`calibrationEvidenceSha\`, \`driftMonitorPolicyRev\`, \`humanReviewPolicyRef\` and \`fallbackToDeterministic\` must travel with ML inference. A forecast may feed W4 PRICE/CLV, ECL PD/LGD/EAD, ALM behavioral cashflows or PLAN forecasts **only** with explicit approved evidence and comparable baseline. Historical recognized transactions remain deterministic; financial record amendments need their own authorization.

## 7. Release-acceptance checks

- All 95 model codes and 93 proposed dataset families unique; W4 dependencies DAG; exact DTO/Method parameter schema reviewed.
- Per model: independent finance-reviewed reference cases ≥2 and negative matrix ≥5 cases, zero/undefined/missing, cross-currency/unit/date, legal S2; regulatory models have effective-date legal citations.
- Statistical model backtest and calibration, optimizer solver tolerances, ML out-of-time validation and model monitoring.
- Confirm \`PRODUCTION_ADMISSION=false\` and \`FINANCIAL_S2_HOLD\` until separate independent evidence is available.

**Result of this document:** precise pre-freeze **design** only; no contract SHA is asserted valid, no old contract is mutated, and no Python HC method implementation is represented as complete.
