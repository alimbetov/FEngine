# FENGINE-R0 — Delivery backlog and acceptance

| Stage | Deliverables | Exit gate |
| --- | --- | --- |
| R0.1 | 31-family taxonomy, organization-type matrix, metric/fact catalogs | Catalog syntax, unique IDs, documentation, no unknown refs |
| R0.2 | Data dictionary: meaning, dimensionality, stock/flow, source / applicability | Reviewed for conflicts, zero/negative & missing policy |
| R0.3 | Formula registry V1 with AST and immutable versions | DAG validator, deterministic behavior, samples |
| R0.4 | Financial methodology approval workflow | DRAFT -> TECH_VERIFIED -> FINANCE_REVIEWED -> QUALIFIED; evidence and revocation |
| R1.1 | P&L, balance, cash-flow ratios | 100% examples, IFRS/management differences explicit |
| R1.2 | Leverage, liquidity, working capital | Annualization, averaging and corner cases tested |
| R1.3 | E2E financial statement models | Reconciliation, golden fixtures, PostgreSQL/Java parity |
| R2 | Budget, costs, economics, capital budgeting, risk | Scenario inputs, risk assumptions and unit economics |
| R3 | Production, sales, HR, supply chain, sustainability | Sector profiles with approved sources and boundary definition |
| R4 | Bank, insurer, public/nonprofit, health, education, etc. | Independent sector reviewer, jurisdiction/regulation-aware |
| R5 | Platform, UI, reporting, ML-based anomaly assistance | No methodology duplication, complete traceability |

## Implementation rules
1. No sector-specific formula is activated merely because another sector has an identical textual expression.
2. Only compiled, immutable and admitted bindings may be used for qualified output.
3. Metric catalogs drive DB schema, UI field descriptions, dependency visualization and test generation.
4. Recalculate from frozen facts, never from display-rounded reports.
5. Generated guidance must always distinguish diagnostic observations from verified financial conclusions.
6. R0 sample formulas are *illustrative candidates*; do not report them as implemented calculations until numerical engine and tests exist.

## Recommended Java / PostgreSQL modules (future)
- `fengine-catalog` (metadata, import, versioning)
- `fengine-formula` (typed expression AST, dimensional validation)
- `fengine-qualification` (approvals, hashes, revoke, immutable binding)
- `fengine-facts` (observations, period/currency/scope, revisions)
- `fengine-calculation` (compile, execute, lineage, deterministic math)
- `fengine-analysis` (methodology orchestration and domain-specific checks)
- `fengine-report` (explainable results and comparisons)

## Core candidate golden scenarios
- Positive revenue, positive equity, normal financials.
- Zero sales and negative equity (ratio must not be deceptively numeric).
- Month/quarter/year changes, previous-period comparisons.
- Leap year and different fiscal year.
- Changed cash-flow classification before/after IFRS 18 effective dates.
- Incomplete bank capital and insurance service data (block, no approximation).
- Currency mix without approved FX conversion (block).
- Budget with zero budget baseline, loss-making business, and seasonal flows.
- Late fact revision and stale methodology approval (reject).

## Catalog source-of-truth
- `catalog/facts.tsv`: source facts.
- `catalog/metrics.tsv`: candidate computed indicators and expressions.
- `catalog/analysis_types.tsv`: taxonomy and sector applicability.
- Later: reviewed methodology JSON, formula AST JSON and executable golden fixtures.
