# FENGINE-R0 Calculation & Financial Semantics Contract

**Status:** DESIGN DRAFT. No automated formula execution is admitted to production by this document.

## 1. Canonical records
`FactDefinition(code, label, unit, basis, dimensions, semantic_version)`; `MetricDefinition(code, purpose, unit, dimensionality, applicability)`; `FormulaDefinition(metric_code, formula_version, ast, dependencies, params, period_rules, null_policy, zero_policy, source, qualification, content_sha256)`; `Methodology(analysis_type, version, formula_bindings, assumptions, control_checks, approval)`; `FactObservation(organization_id, fact_code, period_start, period_end, as_of, currency, value, scope, revision, source_sha256)`; `CalcPlan(qualified_bindings, factset_sha, exact periods, effective config sha)`; `CalcResult(values, lineage, rounding, run metadata)`.

## 2. Mandatory numerical contracts
- Decimal math (`BigDecimal` in Java and NUMERIC in PostgreSQL); never binary-float for money.
- Money amount and currency mandatory; FX conversion has official/provider rate source, quote direction, date, group policy and missing-rate fail-close.
- Never add currencies, different units, or non-congruent segments.
- Flows use `[periodStart, periodEnd)` reporting intervals; balance stocks use `asOf` date and close-of-period convention. All inputs from one coherent FactSet.
- `AVG_STOCK(stock)` = (opening_stock + closing_stock)/2 only when both observed; this is a default *simplification* and must be versioned. Where material, use daily/monthly weighted average.
- `DAYS_IN_PERIOD()` calendar days for annualization; DSO/DIO/DPO calculations must use the same measurement window. `DAYS_IN_YEAR()` is configured (365/366/actual) per methodology.
- Ratios stored as dimensionless decimals, not percentages. `0.25` displays as `25%`. Explicit `PERCENT_POINTS` used for rate comparison.
- `SAFE_DIV(a,b)` **does not** silently return zero: `b=0` results in typed `UNDEFINED_DENOMINATOR`. Negative denominator is allowed only with explicit financial interpretation and warning.
- Missing inputs => `BLOCKED_MISSING_INPUT`; no implicit zero substitution.
- Negative revenue, equity, or prior-year values may invalidate conventional ratios; mark `NOT_MEANINGFUL` by methodology rather than misleading arithmetic.
- Expenses and outflows are positive magnitudes in the fact registry. Net/signed result may be negative. Reconciliations explicitly subtract positive expenditures.
- Final result rounding only for presentation unless a legally prescribed intermediate rounding mode exists; compare unrounded values under documented tolerance.
- `LAG(x,1)` is the matching prior period (same duration and comparable scope). Undefined without prior observation.
- `SUM_PERIOD(x)` aggregate flow observations within requested reporting horizon, never sum snapshot balances.

## 3. Formula AST / deterministic functions
Allowed initial expression grammar: `+`, `-`, `*`, `/` with explicit `SAFE_DIV`, `AVG_STOCK`, `LAG`, `ABS`, `MIN`, `MAX`, `SUM_PERIOD`, `DAYS_IN_PERIOD`, `POW`, `IF`, `NPV`, `IRR`, `MIRR`, `PERCENTILE`. No SQL/code execution in definitions. `IRR/NPV` require dated/currency-consistent flows and rate conventions; numerical algorithm specifications are separate.

`CASE`, exception handling, FX and special time-series operations must become typed DSL operations with versioned signatures, not free-form scripts. Dependencies form a DAG. Cycle/unknown-symbol/unit incompatibility is rejected before publishing.

## 4. Essential provenance and controls
Each result references exact FactSet SHA, metric/formula SHA, methodology SHA, parameter SHA, plan SHA, engine build SHA, timestamps, org/scope/currency, source revisions, reviewer and qualification status. Any modified active methodology invalidates draft or stale plan for commit. No execution substitutes a newer version without compilation.

## 5. Temporal and regulatory overlays
- Entity financial year, reporting basis (`IFRS`, `LOCAL_GAAP`, `MANAGEMENT`, `STATISTICAL`), restatements, consolidation, eliminated intercompany transactions.
- `IFRS18` applies to annual periods starting on/after 2027-01-01 unless earlier adopted; IFRS 18 classification and definitions must be explicitly modeled. Do not impose a universal operating profit formula on banks, insurers, or all IFRS periods.
- Basel capital/LCR/NSFR indicators require the full prudential regulatory definitions, eligibility, adjustments, floors/caps and national implementation. Ratios in seed catalog are *conceptual prototypes*.
- Emissions: require organizational boundary, Scope 2 location/market basis, gas coverage, factor vintage, GWP version and Scope 3 categories.

## 6. Test contract
For every published formula: valid numerical example with manually verified expected result, zero denominator, absent fact, inconsistent currency/unit/period, negative values, overflow/precision, input revision change, dependency cycles, duplicate code/version, restated data, concurrency and deterministic repeat. For financial reporting create reconciliation invariants (assets = liabilities + equity, CFS opening+net-change=closing) with configurable tolerance. Formula outputs must not be exposed as qualified if input/approval gates fail.

## 7. Minimal TDD acceptance
- Catalog parse/unique codes/known dependency symbols/acyclic graph.
- No formula without period, unit, applicability and explicit `DRAFT` or approved status.
- At least ten hand-calculated core financial examples before implementation of R1 calculation path.
- Explainability API: show selected variant, equation, operand values, transformations, source and any warnings.
