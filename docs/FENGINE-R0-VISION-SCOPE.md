# FENGINE-R0 — Enterprise & Organization Analysis Atlas

**Status:** initial architecture baseline / DRAFT, 2026-11-20. **Repository:** `alimbetov/FEngine`. **Working branch:** `feat/fengine-metric-methodology-foundation`.

## 1. Outcome
FEngine builds a reproducible, versioned knowledge base of **facts, metrics, formulas, methodologies and analytical decisions** for businesses and organizations. A universal catalog must not assert that all organizations share a single accounting model or that any finite set can cover every future methodology.

### Hierarchy
`OrganizationType → SectorProfile → AnalysisType → MethodologyVersion → MetricDefinition → FormulaVersion → InputFactDefinition → FactSet → CalcPlan → CalcRun → Evidence/Result`

Definitions are immutable upon publication. Drafts may change; published versions are superseded, not edited. Store canonical content hashes and an explicit approval state.

## 2. Analysis coverage / required families
| Code | Family | Example studies |
| --- | --- | --- |
| FS | Financial statements | common-size, horizontal, trend, restatement, reconciliation |
| PROF | Profitability | gross/net/operating margin, ROA, ROE, ROIC, DuPont |
| LIQ | Liquidity | current, quick, cash coverage, liquidity gap |
| SOLV | Solvency & capital | leverage, gearing, debt service, interest coverage |
| WC | Working capital | DSO, DIO, DPO, CCC, turnover |
| CASH | Cash flow | CFO, FCF, accrual quality, cash conversion |
| EFF | Asset efficiency | asset turnover, fixed asset turnover, capital efficiency |
| COST | Management accounting | fixed/variable costs, contribution, break-even, ABC |
| BUD | Budgeting | budget–actual, forecast error, flexible budget, variance |
| INVEST | Capital projects | NPV, IRR, MIRR, PI, payback, scenario/sensitivity |
| VAL | Corporate valuation | DCF, multiples, EVA, WACC, terminal value |
| RISK | Enterprise risk | stress, VaR, concentration, sensitivity, ECL where applicable |
| REV | Sales & revenue | growth, pricing, cohort, net revenue, retention |
| MKT | Marketing | CAC, conversion, LTV, payback, attribution assumptions |
| OPS | Production | productivity, OEE, yield, scrap, downtime, utilization |
| LAB | Workforce & HR | FTE, churn, overtime, wage productivity, safety |
| SUP | Procurement & inventory | supply turns, lead time, fill rate, spend |
| LOG | Transport & logistics | cost per km, on-time delivery, vehicle utilization |
| ENERGY | Utilities & energy | specific consumption, load factor, losses |
| ESG | Sustainability | energy/water intensity, Scope 1/2/3 GHG |
| MACRO | External economics | inflation adjustment, FX impacts, market sensitivity |
| STRAT | Strategy | market share, growth, BCG/Pareto, competition |
| BANK | Banking | NIM, NPL, cost of risk, LCR, NSFR, regulatory capital |
| INS | Insurance | claims, expense/combined ratios, IFRS 17 reporting metrics |
| SAAS | SaaS/subscription | ARR, MRR, NRR, churn, CAC/LTV |
| AGRI | Agriculture | yield, input efficiency, cost per hectare |
| CONST | Construction | earned value, CPI, SPI, EAC, WIP |
| REAL | Property/hospitality | occupancy, RevPAR, NOI, cap rate |
| HEALTH | Healthcare | bed occupancy, LOS, clinical throughput |
| EDUC | Education | enrolment, completion, cost per learner |
| PUBLIC | Government/not-for-profit | program cost, budget execution, impact, fundraising |

**Applicability matrix:** `GENERIC_NON_FINANCIAL`, `BANK`, `INSURER`, `MANUFACTURER`, `RETAIL`, `SERVICE`, `SAAS`, `AGRICULTURE`, `CONSTRUCTION`, `LOGISTICS`, `UTILITY`, `REAL_ESTATE`, `HEALTHCARE`, `EDUCATION`, `PUBLIC`, `NONPROFIT`, extensible. `GENERIC` formulas are not presumed valid for banks/insurers without explicit mapping.

## 3. KPI and formula qualification
1. **FACT:** collected data, not an equation; must have explicit provenance.
2. **DERIVED:** deterministic and dimensionally valid expression.
3. **MODEL:** algorithmic indicator requiring assumptions, calibration, controls and uncertainty.
4. **REGULATORY:** jurisdiction/date/entity-dependent; regulator-specific template overrides simple prototypes.
5. **DIAGNOSTIC:** internal benchmarking rules; never misleadingly label a threshold as international regulatory standard.

A formula in the seed catalog is a **candidate**, not audited financial production logic. A catalog entry needs: clear meaning, inputs, period/stock-flow convention, sign convention, units, missing/zero policy, applicability, source/reference, worked example, test fixture, mathematical review, independent financial qualification.

## 4. Multi-organization principle
A non-profit has program/fundraising ratios; a public institution has budget/service-delivery metrics; an insurer follows insurance-contract reporting; a bank has prudential metrics. These should share the engine but not inherit inappropriate industrial-company denominators.

## 5. Scope boundaries and execution order
- R0: taxonomy, canonical fact and metric codes, source list, candidate formula registry and validator.
- R1: finance core (P&L/BS/CFS, cash, working capital, capital) with exact examples and qualification.
- R2: economic/operational, budgets, investments, valuation, risk/stress.
- R3: sector packs for manufacturing/trade/services/construction/transport/agri/energy.
- R4: banks, insurers, public/NPO, healthcare/education and specialized regulatory overlays.
- R5: ingestion, reproducible compiled plans, PostgreSQL/Java engine, API, UI/reporting.
- R6: extensive test fixtures, cross-engine numerical reconciliation, regulation change management, controlled release.

## 6. Non-goals at R0
No assertion that every conceivable analysis has been implemented; no inference of verified numbers from raw documents; no production-grade Basel/IFRS result based only on symbolic sample formulas; no automatic regulatory approvals.

## 7. Authoritative reference starting points
- IFRS Foundation IAS 7: https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows.html
- IFRS Foundation IFRS 18 (effective 2027-01-01): https://www.ifrs.org/issued-standards/list-of-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/
- IFRS Foundation IFRS 17: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/
- OECD Labour Productivity: https://www.oecd.org/en/data/indicators/labour-productivity-and-utilisation.html
- BIS LCR: https://www.bis.org/committees/bcbs/basel-framework/standard/lcr
- BIS NSFR: https://www.bis.org/committees/bcbs/basel-framework/standard/nsf
- GHG Protocol: https://ghgprotocol.org/standards-guidance
- Business Queensland ratios: https://www.business.qld.gov.au/running-business/finance/improve-performance/ratios/infographic-transcript

Reference inclusion does not mean any unreviewed catalog formula is endorsed by the standard setter.
