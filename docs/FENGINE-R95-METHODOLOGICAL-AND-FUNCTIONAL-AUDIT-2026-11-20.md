# FEngine R95 — methodological review, functional diagnosis and pre-freeze decision

**ID:** FENGINE-R95-AUD-R0.2 · **Date:** 2026-11-20 · **Review status:** EVIDENCE-LIMITED METHOD REVIEW · **Freeze:** BLOCKED · **Independent finance S2:** HOLD

## 0. Decision in one sentence

Do **not** freeze the 95 financial calculation models or authorize production claims. Preserve their identities, repair method semantics and typed parameter coverage, qualify independent financial golden tests, then freeze **individual** reviewed method/input/parameter/output revisions before Python financial runtime implementation. Current added Python tests cover specification structure and independent arithmetic, **not** financial HC execution.

## 1. Evidence and project diagnosis

- The canonical main master v0.8 includes 83 original HC candidates (W1 14/W2 42/W3 27), 12 W4 candidates, and 93 proposed typed dataset families. All 95 candidates are draft specification artifacts.
- Existing FIN-R83 audit reported 83/83 external arithmetic smoke and 34/34 extra invariant cases, but those did not import HC financial runtime. This review retains that evidence **as historical**, not newly repeated.
- Current independent contract-bank implementation: \`tests/test_fengine_model_contract_bank.py\` checks documentation for 95 models, registry consistency, blocked status, and synthetic Decimal oracles. The CI workflow must report its own outcome before any PASS claim about the Python test suite.
- Financial Python HC calculation implementations: **0/95 verified**; FIN source bindings: **unverified**; PostgreSQL event/idempotency, loan/ECL/DCF E2E and immutable financial outputs: **not demonstrated**; independent finance S2: **none**. These are **scope limitations**, not silently counted failures of running implementations.
- GEO-OPT is separate Python executable reference (previously reported 38/38 tests on Python 3.11 and 3.13); this is not proof for HC computation, stochastic optimizers or bank regulatory formulas.
- Project correctness depends primarily on semantics/source quality, not on raw computation speed. No claim of Python, JDBC or Rust comparative performance is justified yet.

**Classification:** \`SPEC_COVERAGE\`, \`INDEPENDENT_ARITHMETIC\`, \`PROPERTY_INVARIANT\`, \`SOURCE_BINDING\`, \`REGULATORY_CONFORMANCE\`, \`MODEL_BACKTEST\`, \`PYTHON_RUNTIME_UNIT\`, \`PYTHON_RUNTIME_E2E\`, \`SQL_PARITY\`, \`RUST_PARITY\`, \`CRASH_RECOVERY\`, \`PERFORMANCE\` are distinct evidence classes.

## 2. Model-family assessment (95 model specifications, not deployed algorithm quality)

Levels: **B** = plausible design with finite clarification; **C** = substantial applicability or measurement risks; **D** = demonstrated conceptual inconsistency in a named variant. This is a qualitative expert review, **not** a calibrated accuracy score.

| Family | Count | Assessment | Principal pre-freeze issue | Suggested action |
|---|---:|---|---|---|
| SET | 7 | B | allocation, reversal, netting and time cutoff | harden policy, replay/invariants |
| ECL | 7 | C | PD conditional/marginal, staging/SICR, 12-month event vs loss horizon, cures/POCI | revise first; external credit-risk reviewer |
| LOAN | 8 | B/C | nominal vs IFRS EIR vs local GESV, day count, dated cash flows, fees, floating resets | explicit product/rule variants and legal admission |
| CASH | 8 | B | forecast vs posted cash, FX effects, cash-flow classification and duplicate events | source reconciliation and signed classification |
| DCF | 9 | B/C | terminal basis, multiple/tangent IRR roots, Ke/WACC currency/real-vs-nominal matching | numerical root completeness and capital-source revisions |
| ACC | 7 | C | OCI/NCI, IAS12/16/21/36, leasing and consolidation policy eligibility | ledger reconciliation with finance qualification |
| STOCK | 7 | B | returns/reversals, moving vs periodic WAC, NRV | immutable event replay test bank |
| ASSET | 7 | C | components, impairment CGU, changes in useful life | item-level evidence and policy dates |
| COST | 8 | B/D | HC.COST.03 Price-Volume-Mix incorrectly lacks isolated MIX | block false PVM label; introduce true 3-factor variant |
| PLAN | 8 | C | integer constraints, objective, bound/gap, temporal financial DAG | solver correctness + discrete feasibility |
| RISK | 7 | C | VaR/ES tie-mass, distributions, PSD correlation, backtesting | statistical qualification & calibration |
| CAP | 2 | C | market cap weights, beta source, risk-free tenor/currency, FCFF vs FCFE | no inferred WACC/Ke |
| CREDIT | 2 | C | funding/EL/capital double count, pricing quotes vs APR/EIR, RAROC denominator | linked term cashflow validation |
| CUST | 2 | B/C | per-customer vs cohort grain, CAC attribution, retention discount | cohort identity + leakage controls |
| PF | 2 | C | definition of CFADS, contractual priority and reserve eligibility | contract revision drives waterfall |
| ALM | 2 | C | behavioral maturity, repricing/non-maturity deposits, EVE/NII shocks | scenario version and bank-specific IRRBB review |
| FTP | 1 | B/C | curve source, tenor interpolation, product-level allocation | dated cashflows and curve vintage |
| PRICE | 1 | C | causal elasticity identification, stockout censoring, discrete price steps | bounded optimizer + out-of-time demand validation |
| **Total** | **95** | **Freeze blocked** | 28 CRITICAL, 42 HIGH, 25 MEDIUM method-risk candidates | phased remediation |

Risk counts are **reviewer triage labels**, not empirical probabilities of misstatement. Precise per-model blockers for **all 95** are in \`docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv\`.

## 3. P0 blocking methodological corrections

### 3.1 ECL: HC.ECL.01–.07

- Require explicit stage/SICR/default/cure/POCI policy versions with effective dates and entity applicability.
- For 12-month ECL, restrict *default occurrence horizon* to eligible 12 months; **not** recovery/cash-shortfall horizon. Later recovery losses remain eligible when caused by defaults during first 12 months.
- Conditional hazards transform through survival: marginalPD(t)=S(t−1)×conditionalPD(t); do not sum conditional PD directly. For a time grid tie to dated exposure and discount origin.
- Recovery-cost time and effective interest discounting need independent origin and recognition policies. Missing, invalid, zero EAD and legally unavailable collateral must have different result states.
- Scenarios require weights normalized to one **within approved tolerance**, calibrations with evidence, and coherent staging vs macro assumptions. POCI logic cannot be hidden as generic Stage3.
- **Critical controls:** stage migration not by arbitrary PD threshold; 12m default/late recovery; missing SICR, censoring, post-model overlay, unauthorized stage override.

### 3.2 Contract rates, IFRS EIR and KZ GESV: HC.LOAN.01–.08 and W4 CREDIT/FTP

- Distinguish **contractual nominal rate**, dated interest accrual, **IFRS 9 effective interest rate**, and **statutory local GESV**. Calculation outputs must not be interchangeable.
- Freeze date basis, inclusive/exclusive accrual boundaries, ACT conventions, floating index fixing, floors/caps, compounding, amortization and early repayment.
- IFRS EIR requires a financial eligibility decision for initial fees/costs and original versus revised cashflows; define root solver domain, residual and multi-root policy.
- Kazakhstan GESV requires a qualified jurisdiction-specific regulation revision, borrower/entity applicability, fee inclusions, reporting precision and governing effective date; no automatic claim based on EIR output.
- W4 risk-based pricing must avoid double counting capital and expected loss already priced in funding/fees; margin/RAROC must share an explicit compatible economic-capital allocation and horizon.

### 3.3 DCF: HC.DCF.01–.09, W4 CAP.01/.02

- NPV/XNPV and IRR/XIRR require exact dated cashflows, cash-direction conventions, discount date and annualization/day-count; equal periods are not inferred for irregular flows.
- **Tangent double root:** CF [-100,+200,-100] has r=0 despite no sign change; sign-change-only bracketing is incomplete.
- **Multiple roots:** CF [-100,+230,-132] has r=.10 and .20; report a root-set with completeness status, not an arbitrary single IRR.
- FCFF discounts at compatible WACC; FCFE at compatible Ke. Nominal vs real, currency, inflation and FX cannot be silently mixed. Gordon terminal variant blocks WACC<=g, non-evidenced terminal growth and unsupported persistent margins.
- CAPM risk-free tenor, beta calibration/relevering, market premium and country/size premium each require source versions and non-overlap checks.

### 3.4 Statistical risk: HC.RISK.01–.07

- Confirm whether loss is a positive loss or negated P&L; define quantile convention and weighting; avoid generic “95% risk” without horizon and base currency.
- Discrete-tail ES must include the **fraction of probability mass at VaR**. For [0,10,20,20,100] equal weights and alpha=.75, VaR=20, quantile-integral ES=84; naive E[L | L>20]=100 is wrong.
- Simulation requires immutable PRNG generator+seed, effective factor distribution, PSD covariance, fitted windows, tail sample adequacy and uncertainty / backtests. Identical seeds check reproducibility only, not statistical validity.

### 3.5 Optimization: HC.PLAN.03/.04/.05/.08, HC.STOCK.07, HC.COST.04, HC.PRICE.01 and GEO-OPT future

- Explicit objective MIN/MAX, decision domain INTEGER/BINARY/CONTINUOUS, units, hard constraints, ties, deterministic ordering and time budget.
- Feasible != proven globally optimal. Report bound/gap, timeout, infeasibility certificate/status where available, and a revised result shape to distinguish \`FEASIBLE_NOT_PROVEN\` and \`OPTIMAL_PROVEN\`.
- Never relax integer capex project decisions, batch/MOQ or price ticks into continuous variables without an explicit method variant, separately labeled approximate output and error bound.
- GEO-OPT routing correctness should not be conflated with general LP/MILP or stochastic finance solver readiness.

### 3.6 Cross-family semantic defect: HC.COST.03

True Price-Volume-Mix decomposes **price**, **total volume** and **mix** (and interaction according to the selected method). Existing two-term decomposition labels the pure mix example incorrectly as volume. Require a new reviewed method variant with reconciliation to total contribution/profit change, and deprecate incorrect PVM naming without changing existing immutable result identity.

## 4. Contract freeze and param policy

See \`docs/FENGINE-R95-PARAMETER-CONTRACT-V2-DESIGN.md\` for per-field types and required metadata. Existing W1–W3 must be revised after review, **without rewriting their previously published identifiers**. W4 proposal carries its own schema version. Do not assign final SHA or mark \`QUALIFIED\` based on draft YAML/TSV alone.

Gate checklist:
1. 95 candidate identities and method-family membership consistent; eliminate circular dependency and dimension mismatches.
2. Exact typed parameters, requiredness, enum ranges, date/version scope, default policy, override/admission and cross-parameter validation for each method.
3. At least **two independent finance-reviewed goldens** per model; domain boundary, missing-vs-zero, negative, currency, date, stale source, malformed policy, reproducibility and idempotency cases.
4. Family-specific evidence: ECL calibration/staging & macro scenarios; GESV current legal revision; IRR root completeness; VaR/ES backtesting and Monte Carlo error; optimizer feasibility+gap.
5. A stable reviewed artifact manifest and canonical SHA for InputSchemaRevision, MethodRevision, ParamsRevision, OutputSchemaRevision, algorithm build/dependencies, source facts and CalcPlan.
6. Independent finance S2 **separate** from static tests, arithmetic oracles and runtime engineering qualification.
7. Only then freeze **per model revision**; frozen results remain reproducible, revisions never mutate and revocation invalidates admission, not historical audit.

## 5. ML assistance: useful, not a formula replacement

| Candidate | Model families | Input labels and hazards | Evidence before integration |
|---|---|---|---|
| Survival / PD models | ECL.01–.04, RISK.05 | dated defaults, stage, censoring, rare events, leakage | rolling time split, Brier/log loss, calibration curves, concentration, stability |
| LGD/EAD regression | ECL.05/.06, CREDIT | dated recoveries, partial draws, selection/censoring | out-of-time bias, recovery horizon, segment stability, baseline comparison |
| Time-series cash and demand | CASH, PLAN, STOCK, CUST | historical cash, missing periods, promotions, stockouts | rolling-origin WAPE/MASE, quantile coverage, forecasts vs seasonal naive |
| CLV/churn | CUST.01/.02 | cohort attribution, retention, margin, survivorship | temporal survival calibration; avoid label leakage; uncertainty |
| Elasticity/price uplift | PRICE.01 | observational prices confounded by promotions/selection | causal validation or experiments, out-of-distribution boundaries, human approval |
| Rate/deposit behavior | ALM/FTP | repricing behavior, bank curves, optionality | sensitivity and stability under shocks, independently approved model |
| Risk factors/correlation | RISK/DCF | rare shocks, factor copulas, tails | PSD conditioning, historical stress, tail backtesting, scenario review |
| Data anomaly assistant | SET, CASH, ACC, COST | duplicate events, journal pair matching, miscoding | false-positive/false-negative cost, explainable suggestions and human confirmation |

**Architecture:** \`PredictionModelRevision\` produces **versioned forecasts, inferred factors or diagnostic proposals** with immutable train/validation/feature/calibration manifests. Deterministic \`CalcPlan\` may use an admitted prediction as an *explicit input scenario*, never as a silent patch to historical accounting, contractual fees, FIFO, GESV or optimizer-feasibility logic.

**Start only after source quality:** first build data inventory, label policy, time-aware baselines and shadow-mode evaluation. Synthetic arithmetic fixtures cannot train credit or business forecast models.

## 6. Performance and implementation order

**Optimization of source/code is not authorized by a mathematical draft.** Use full-path benchmarks on frozen, equivalent inputs: Python Decimal, PostgreSQL/JDBC set-based aggregation, then Rust batch only when p95/p99 and end-to-end total cost improve with exact financial parity. Measure queue delay, decode/serialize, memory, compute, persistence, recovery and cost per 1k/100k/1m rows. For numerical/statistical solvers use explicit error tolerance and numerical stability; never promise universal speedups.

- **AUD-R95.1:** methodological P0 blocker repair, W4 new parameter semantics, pre-freeze matrix and independent reference tests; status BLOCKED until reviewer evidence.
- **AUD-R95.2:** independent source-linked golden/reference pack and negative bank per model; legal/regulatory banking review separately.
- **AUD-R95.3:** versioned parameter/input/output IDL; proof of dependency types and canonical SHA; per-model immutable freeze when qualified.
- **PY-R0:** Python HC runtime only after approved contracts; verify each model through actual imports, E2E reconciliation and persisted results.
- **ML-R0:** optional shadow-model pilot for PD, cash/demand and outlier detection with time-based evaluation.
- **RUST/PERF-R0:** Rust/JDBC optimization strictly after reference correctness and repeatable full-path measurements.

**Exit decision:** R95 specification bank can be green while financial/production release remains HOLD. Publishing 95 financial engine PASS would be a material misrepresentation at this stage.
