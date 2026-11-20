# FENGINE-FLEX-METHOD-R1 — универсальные варианты расчётных методик

**Дата:** 2026-11-20. **Статус:** REQUIREMENTS_DRAFT / NOT_IMPLEMENTED / CONTRACT_FREEZE_BLOCKED / FINANCIAL_S2_HOLD.

## 1. Цель и строгое правило

Все **95 FEngine HC-моделей** должны иметь конфигурируемую и версионируемую методику, без произвольного внедрения новых формул и без изменения уже квалифицированных вычислений. Один стабильный modelCode может иметь несколько MethodVariant с разными финансовыми смыслами; каждый вариант — отдельная immutable MethodRevision с собственным ParameterContractRevision и OutputSchemaRevision при изменении формы результата. UI показывает только применимые варианты, а не свободный список переключателей.

Общая структура: ModelDescriptor → MethodVariantDefinition → MethodRevision → ParameterContractRevision → ConfigRevision → immutable CalcPlanBinding → immutable Result. Все значения конфигурации сохраняются в разрешённой редакции, а изменения задним числом запрещены. Изменение учетной оценки после признания оформляется новой dated revision, последовательно (prospective), если утверждённая учетная политика не требует иного.

**Universal fields, each of 95 models:** modelCode, modelFamily, variantCode, methodRevisionSha, paramsContractSha, configRevisionSha, inputSchemaSha, outputSchemaSha, calculationNumericPolicySha, sourceFactSetSha, asOf/period, reportingBasis, jurisdiction/entityScope, currency/unit, approvalEvidenceSha, effectiveFrom/To, algorithmBuildSha, reasonCodes. ParameterDefinition is typed and includes requiredness/requiredWhen, allowlist, units, numeric bounds, defaultPolicy, source, effective date, override authority, and cross-param validation.

**Key gate:** unrestricted user-defined expressions, dynamic SQL, eval/Python code, unreviewed numerical policies or unspecified business-day/day-count rules are FORBIDDEN. A change from LINEAR to SYD to ANNUITY changes the method variant + revision, not only a numeric parameter. 10 suggested configurations may be shown in the UI, but the catalogue may support more reviewed variants.

## 2. Варианты амортизации ОС — HC.ASSET.01

Distinct meanings: STRAIGHT_LINE means proportional to elapsed **time**; UNITS_OF_PRODUCTION means proportional to **production volume**. Loan annuity repayment is NOT a depreciation method of an asset.

For C recognized cost, S residual/salvage value, n approved useful-life *periods*, t period index 1..n, BV prior net book value:

| VariantCode candidate | Financial method (base period) | Required parameters | Applicability gate |
|---|---|---|---|
| STRAIGHT_LINE | (C-S)/n, with dated proration | serviceDate, n, S, calendar, partialPeriodConvention | IAS16 candidate |
| UNITS_OF_PRODUCTION | (C-S)×actualUnits/totalEstimatedUnits | productionUnit, totalUnits>0, actualUnits>=0, source revision | IAS16 candidate |
| DECLINING_BALANCE | min(BV×rate,BV-S) | decliningRate, terminalTrueUpPolicy, n | IAS16 candidate with consumption evidence |
| DOUBLE_DECLINING | min(BV×(2/n),BV-S), optional reviewed switch-to-SL | n, switchToStraightLine, terminalTrueUpPolicy | accelerated; eligible entity policy required |
| SUM_OF_YEARS_DIGITS | (C-S)×(n-t+1)/(n(n+1)/2) | n, partialPeriodPolicy, rounding policy | cumulative; independent qualification |
| ANNUITY_CAPITAL_RECOVERY_MGMT | constant A=(C-S/(1+r)^n)×r/(1-(1+r)^(-n)); interest=r×BV; depreciation=A-interest; BVnew=BV-depreciation | n,r>0, interestBasis, periodic compounding, original cost/residual | **management only** unless separately approved under applicable financial basis |
| SINKING_FUND_MGMT | sinking-fund cash recovery with approved accumulation/interest rules | n, interest rate, reserve-fund policy, fund segregation | management only until separately qualified |
| CUSTOM_APPROVED | published audited external MethodRevision, fixed reviewed parameter schema | signed artifact, golden reference, reviewer | no free-code execution |

**Validation:** n>0, 0<=S<=C, correct currency and time unit, no unauthorized negative depreciation, no BV below residual without a documented separate variant. r=0 in ANNUITY_CAPITAL_RECOVERY_MGMT has explicitly approved limiting branch (C-S)/n to avoid division by zero; zero interest must not generate NaN. For production units, measure in fixed unit and block zero totalEstimatedUnits. Dated upgrades, component disposals, impairment and residual estimate changes require effective-dated recalculation of remaining basis and never retroactively mutate archived results.

**Accounting applicability:** IAS16 explicitly names straight-line, diminishing balance, units-of-production; methods should reflect consumption of economic benefits and annual review of useful life/residual/method. Revenue-based depreciation is generally inappropriate. SYD and ANNUITY variants do NOT get default IAS16 approval; annuity is recognized as a specialised vendor calculation, not proof of IFRS eligibility. Tax depreciation (including Kazakhstan rules) must be separate policy with effective legal revision. Sources: https://www.iasplus.com/en/standards/ias/ias16 ; https://docs.oracle.com/en/cloud/saas/financials/25d/faias/example-of-annuity-depreciation-and-interest-calculation.html

## 3. Loan amortization: HC.LOAN.02 is a separate family

| Loan variant | Description | Critical params |
|---|---|---|
| ANNUITY_EQUAL_PAYMENT_DATED | regular equal instalments or exact-date nonlinear solver | rates/fees/dayCount/compounding/irregular dates |
| EQUAL_PRINCIPAL_DATED | equal principal portions, floating dated interest | amortization unit, period boundaries and final remainder |
| INTEREST_ONLY_BALLOON | interest with final principal repayment | accrual/posting dates and final principal |
| BULLET | contractual single principal payment; interest accrual as approved | capitalization vs periodic interest |
| CUSTOM_CONTRACTUAL_DATED | immutable signed contract payment events | ordered dates, valid balances and no negative unauthorized principal |

GRACE_PERIOD is a versioned **modifier**, not an undocumented sixth method. Contract nominal interest, IFRS EIR and statutory KZ GESV are separately qualified metric families; not aliases for ANNUITY.

## 4. Framework for all 95 models

Maintain **one VariantProfile for each model** (catalog/model_variant_profiles_r1.tsv) with unique modelCode, canonical family and source matrix, family-level configurable axes and specific supported candidate variants. Profile is initially BASE_METHOD_REVIEW; it is extensible ONLY via versioned registered variants. If a model has no justified numerical alternative, keep one method with rich *parameters* rather than fabricate a second formula. Do not confuse 95 model candidates with executable runtime.

Proposed meaningful axes by family (only where applicable to exact model):
- SET: allocation, reversal ordering, time cutoff, netting evidence
- ECL: 12-month event vs lifetime horizon, hazard conversion, macro scenarios, recoveries, EIR origin, SICR policy
- LOAN: dated schedule, rate/fees, original versus revised EIR, legal GESV rule
- CASH: actual/forecast, cutoff, direct vs indirect cashflow reporting where applicable, FX classification
- DCF: discounted cashflow basis FCFF/WACC vs FCFE/Ke, dated/regular IRR root-set, terminal methods
- ACC: recognition/consolidation/OCI/tax policies
- STOCK: FIFO, moving/periodic weighted average, unit/currency conversion
- ASSET: eight candidate depreciation variants for ASSET.01; impairment/revaluation and repairs separate
- COST: allocation methodology and genuine price/total-volume/mix (distinct output revision)
- PLAN/PRICE: objective, integer/continuous variable domain, constraints, solver policy/optimality evidence
- RISK: VaR estimator, ES tail-mass, Monte Carlo PRNG/seed/distribution and model calibration
- CAP/CREDIT/CUST/PF/ALM/FTP: capital weights, funding curves, loan loss, customer cohort, covenant/waterfall, repricing, sensitivity and evidence

ML algorithms produce explicit versioned PredictionModelRevision input scenarios; they never silently rewrite cash accounting, ledger balances, statutory EIR/ГЭСВ, depreciation policy or optimality proof.

## 5. Preview, comparison, admission and audit

- GET /models/{modelCode}/variants: returns reviewed eligibility and candidate status; unsupported variants BLOCKED_POLICY with reasonCode
- POST /models/{modelCode}/variants/preview: validates typed conditional params, data sourcing, unit/currency/date, accounting applicability and produces potential output schema; no state mutation
- POST /models/{modelCode}/variants/compare: same frozen FactSet and allowed differing config revisions; explain results not comparable if basis differs
- POST /calc-plans/commit: append-only plan and immutable outputs only after explicit admission and independent S2 when required

Config SHA must cover normalized resolved parameter values + exact method/input/output/numeric/build source, scope, dates, accounting policy and approval SHA. Canonical serialization and signatures require real cross-language test vectors; merely writing SHA in a draft does not freeze an API.

## 6. Control examples and release gates

**Synthetic reference vectors, not production financial qualification:**
- STRAIGHT_LINE: C=1200, S=200, n=5 gives 200 per full year.
- SUM_OF_YEARS_DIGITS: C=1000, S=100, n=4 gives first year 360 and last 90, aggregate 900.
- UNITS_OF_PRODUCTION: C=1000, S=100, totalUnits=30000, actualUnits=9000 gives 270.
- ANNUITY_CAPITAL_RECOVERY_MGMT: C=1000, S=100, n=4, r=10% gives A≈293.923723335488; first depreciation≈193.923723335488; final BV≈100.
- A loan repayment annuity uses a different payment contract and financial direction even when algebra is superficially similar.

**Acceptance:** verify 95/95 unique profile entries; separate method variants for ASSET.01 and LOAN.02; typed numeric guards; prospective estimate revisions, hidden unapproved variants, negative dates/currencies/units, golden arithmetic, and immutable SHA policies. Keep FINANCIAL_S2_HOLD, CONTRACT_FREEZE_BLOCKED and HC financial runtime NOT_IMPLEMENTED. Approval is *per revision* after independent finance review, not by passing these structural tests.
