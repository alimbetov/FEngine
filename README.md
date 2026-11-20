# FEngine — Financial & Economic Calculation Engine

FEngine is a specification-first, evidence-driven financial and economic calculation platform. Its purpose is to turn immutable, typed source facts into reproducible numerical outputs, versioned methods and auditable results.

## Authoritative branch

**main** is the single development and integration branch. The former methodology, OPT, GEO-OPT and flexible-method-variants branches were merged via pull requests; the old feature branch `feat/fengine-flex-method-variants-r1` was retired. Do not develop new work on historical feature branches.

## Current implemented vs designed scope (20 November 2026)

| Scope | Verified status |
|---|---|
| Financial/economic HC catalogue | **116 candidate model contracts** — W1 14 + W2 42 + W3 27 + W4 12 + W5 21; bounded Python mathematical reference for 27 model codes (not finance S2) |
| Input datasets | D01–D114 logical typed DTO candidates, not verified FIN source bindings |
| Fact catalogue | 235 unique DRAFT source fact definitions |
| Financial 116-model Python Calculation Hub | **Partial:** 27 model codes, 48 named variants with real bounded Python Decimal reference executors; remaining 89 model codes not implemented; financial S2 and Redis ACK/TTL runtime gates remain closed |
| GEO-OPT Python reference | Typed directed graph compiler, Dijkstra, A*, Yen K-shortest paths; **38/38 unittest tests** on Python 3.11 and 3.13 in GitHub Actions |
| Functional finance E2E / ephemeral Redis ACK/TTL session runtime | Not implemented, not tested. PostgreSQL persistence of calculation data is prohibited by current FEngine design |

Prior 83-model review: 83/83 external synthetic arithmetic and 34/34 external boundary examples (historical). New R95 CI: 34/34 unittest methods on Python 3.11 and 3.13, including 95 specification-level subtests plus independent Decimal invariants. Historical R95 tests do not import executable financial HC model code; the new HC reference tests do exercise a bounded set of genuine calculations. Neither test suite constitutes financial S2, regulatory qualification, or durable finance engine acceptance.


## Mandatory QUAL-R1 semantic integrity gate — all 48 executable variants

Numerically plausible but false calculations are release blockers. The [central integrity gate](tests/test_fengine_integrity_pattern_gate.py) now runs **before the full reference regression on Python 3.11 and 3.13**. It executes adversarial checks for cross-branch numerator/denominator misalignment, incomplete source cohorts, overlapping intervals even with partial coverage, mismatched rate/exposure keys, and receipt mutation/permutation. Every one of the **48 executable HC variants** has a mandatory model-family risk-pattern declaration and named test evidence in the [qualification inventory](catalog/hc_reference_execution_inventory_r1.tsv). This is a reference/test governance requirement **not** certification of financial S2 or independent per-variant adversarial completeness.

**Three kernel defects were addressed:** ratio-of-sums previously mixed separate business universes, partial source intervals allowed double counting, and complete monthly aggregates could omit a disappearing dimension leaf. See [pattern, examples, test rules, and remaining scope](docs/FENGINE-QUAL-R1-MANDATORY-INTEGRITY-PATTERN.md). New executable variants must be registered with test evidence and risk patterns rather than silently treated as qualified.

## QUAL-R1.1 — executable adversarial gate for every HC variant

The reference tests now verify **actual successful execution** of every one of the 48 inventoried HC method variants (27 model codes); a variant name merely mentioned in a test file is insufficient. [QUAL-R1.1](tests/test_fengine_qual_r11_per_variant_adversarial.py) captures independently passing synthetic model invocations, rejects **missing or newly successful but unregistered variants**, and runs baseline/replay SHA checks, S2 refusal, unknown configuration/input injection, known numeric source tampering and forbidden binary-float checks **against the actual model executable for each variant**. An initial gap was found and corrected: `HC.DCF.03 SINGLE_IF_UNAMBIGUOUS` previously had only a multi-root rejection test, and now has successful 10% and 21% independent IRR goldens.

A separate [mandatory Python 3.11/3.13 CI step](.github/workflows/reference-checks.yml) runs the executable per-variant gate **after** the cross-source semantic integrity gate and **before** the full regression suite. High-precision reference goldens now use explicit local Decimal contexts to avoid accidental dependence on unrelated test-import order. See the [detailed acceptance notes and limitations](docs/FENGINE-QUAL-R11-PER-VARIANT-ADVERSARIAL-ACCEPTANCE.md). This is **reference mathematical and interface evidence, not financial S2**, and is not comprehensive independent adversarial proof of every financial formula.

## QUAL-R1.2 — independent math and domain denials, 48/48 executable variants

In addition to the existing QUAL-R1/QUAL-R1.1 integrity and real-execution gates, **every one of the 48 executable HC model+variant combinations** now has a [hand-authored independent numerical golden](tests/qualification_r12_goldens.py), executed in [R1.2 numerical verification](tests/test_fengine_qual_r12_independent_math.py), and a [domain-specific fail-closed test](tests/test_fengine_qual_r12_domain_denials.py). Expected numeric outputs come from separately documented formulas rather than from the FEngine executor or its SHA; per-variant negative controls assert precise error codes for forbidden financial or source states. [The exact 48-row inventory](catalog/hc_reference_execution_inventory_r1.tsv) binds both evidence files and keeps S2 closed.

These are now **mandatory steps** in both Python 3.11 and 3.13 GitHub Actions reference checks, preceding independent isolated Decimal suites and the full regression. This demonstrates bounded **synthetic reference numerical coverage**, not complete mathematically exhaustive proof, independent S2 finance approval, real FIN source authority, Redis Runtime/ACK, or Rust. [QUAL-R1.2 technical acceptance and remaining risks](docs/FENGINE-QUAL-R12-INDEPENDENT-MATH-ACCEPTANCE.md).

## QUAL-R1.3 — 1,348 deterministic, source-derived mathematical property cases

The [seeded loan/ECL suite](tests/test_fengine_qual_r13_loan_ecl_properties.py), [algebraic IRR/EIR and risk-tail suite](tests/test_fengine_qual_r13_irr_eir_risk_properties.py), and [TASE/source-grain suite](tests/test_fengine_qual_r13_temporal_properties.py) provide **1,348 generated scenario executions** across high-risk HC models and the shared temporal engine. An [isolated Decimal precision policy](tests/qualification_r13_precision.py) makes the independent math checks reproducible in standalone unittest execution, regardless of other test imports. All suites are explicit mandatory Python 3.11/3.13 CI steps, prior to the full regression. [Detailed mathematical derivations, seed budgets, negative cases and limitations](docs/FENGINE-QUAL-R13-SEEDED-METAMORPHIC-ACCEPTANCE.md).

Coverage includes nonzero-rate ACT/365 dated schedules, ECL conditional PD and present-value recursion, planted unique/multiple/tangent IRR roots, irregular EIR, independent VaR/ES tails, daily leap-year source events, month/quarter/year cashflows and margins, NPV full-window re-execution, CAPM exposure weights and actual-date XNPV. **These are 1,348 bounded case executions, not 1,348 unittest functions, not exhaustive coverage of all 48 HC variants, and not financial S2 approval.** Previously approved R1.2 single-case independent numeric/negative proof remains mandatory for all 48 variants. FIN, Redis Runtime and Rust remain separate deferred tasks.

## QUAL-R1.4 — financial conservation and source-pool isolation

The [R1.4 financial-invariant acceptance report](docs/FENGINE-QUAL-R14-FINANCIAL-INVARIANT-ACCEPTANCE.md) adds **1,560 deterministic independently checked synthetic scenarios** across **19 executable variants of 9 HC model codes**. New mandatory seeded gates test PVM's three-factor bridge and original SKU revision, FIFO/Moving/Periodic WAC inventory value conservation, five depreciation methods' acquisition-cost reconciliation, after-tax WACC scaling, and direct/indirect CFO, FCFF and both FCFE variants. The earlier independent numeric and negative evidence for **all 48 variants** remains mandatory.

Two stock-reference defects were reproduced and repaired: **replayed source event IDs on a different date** could previously double count inventory; the stock source parser silently ignored unreviewed **SKU/currency/multi-pool fields** and raised raw KeyError for a missing purchase cost. The reference now requires globally unique source event IDs and exact purchase/issue schemas, refusing unsupported mixed pools with a typed `STOCK_EVENT_SCHEMA` error. Multi-SKU costing, source signatures and financial S2 remain **unimplemented**. FIN, Redis Runtime and Rust are not part of R1.4.

## Universal optional temporal series calculation extension

**TASE-R1 temporal capability:** All FEngine models/variants that legitimately accept dated observations must use **one shared interval/grain kernel**, with source-grain validation, per-day/month/quarter/year buckets, business grouping and an **opt-in** overall period total. FLOW values sum; STOCK values use an end-of-period as-of snapshot; ratios recompute on aligned source components; nonlinear HC model outputs must be recalculated from full-window facts under a separately reviewed capability or blocked. The new `PeriodRequest(source_grain="DAY"|"MONTH"|"AS_OF", grain="MONTH", include_total=True)` returns `rows` and `total_rows`; default `include_total=False` keeps legacy calls and hashes unchanged. The common TASE reference currently covers configured candidate product/metric semantics; **not all 116 HC models are automatically interval-enabled**. No Redis runtime is implemented.

See [universal temporal extension contract](docs/FENGINE-TEMPORAL-SERIES-EXTENSION-V1.md), [TASE reference](tase/reference.py) and [cross-product/day-month/total tests](tests/test_tase_universal_temporal_extension.py).

## ModelTemporalCapabilityV1 — model-by-model admission to shared intervals

The [universal temporal extension](docs/FENGINE-TEMPORAL-SERIES-EXTENSION-V1.md) now has a **declarative, fail-closed HC model adapter**, [ModelTemporalCapabilityV1](tase/model_temporal.py), driven by a [versioned capability registry](catalog/model_temporal_capabilities_v1.tsv). It executes the **actual model** for each dated input interval, checks source revision SHA, currency and exact input date binding, then passes the selected output to the **one existing TASE calendar and semantic reducer**. Interval results and the full-range total are returned together.

**Current limited reference scope: 9 model+variant+output bindings across 5 of 116 HC model codes** (direct/indirect CFO, FCFF, undiscounted FCFE and as-of EVM estimate at completion). Source SUM is **not** granted to discounted FCFE PV, PVM, ratios or nonlinear models. Posted CFO enforces consecutive opening/closing cash continuity; EVM snapshots enforce a stable baseline. Undeclared model outputs and calendar grains fail closed, while scalar execution remains unchanged. This is **reference only, not financial S2 or FIN FactSet admission**, and does not implement Redis sessions.

[ModelTemporalCapabilityV1 implementation and limitations](docs/FENGINE-MODEL-TEMPORAL-CAPABILITY-V1-ACCEPTANCE.md) · [Real HC-to-TASE E2E tests](tests/test_model_temporal_capability_v1.py).

## ModelTemporalCapabilityV1.1 — non-additive time series reducers

The shared temporal extension now supports 13 reference-mode model+variant+output contracts across 6 distinct HC models: the previous 9 additive/as-of bindings and **four V1.1** derived contracts. V1.1 implements **RECOMPUTE_FROM_COMPONENTS** for dated EVM CPI (latest EV / AC, not an average of CPI values) and **RE_EXECUTE_FULL_WINDOW** for PERIOD_END_NPV / MIDPERIOD_NPV (recalculate actual HC NPV from the full monthly cashflow series instead of summing monthly NPVs). Both use the **same TASE calendar/coverage kernel**; the [unified reference API](tase/temporal_dispatch.py) selects the method by reviewed declarative model/variant/output policy only. Undeclared models and unsafe aggregations remain blocked. No new HC mathematical model code is claimed.

[Review and numerical acceptance](docs/FENGINE-MODEL-TEMPORAL-CAPABILITY-V11-ACCEPTANCE.md) · [V1.1 capability registry](catalog/model_temporal_capabilities_v11.tsv) · [portable reference vectors](tests/golden/model_temporal_v11_reference_vectors.json) · [negative/functional tests](tests/test_model_temporal_capability_v11.py).

## ModelTemporalCapabilityV1.2 — dated XNPV, exposure-weighted CAPM and PVM series

Five additional **explicit reference-only** temporal contracts across three existing HC mathematical models: **HC.DCF.02 EXACT_DATE_XNPV** executes ACT/365-fixed dated cashflows by bucket and full range at one annual rate and fixed valuation origin; **HC.CAP.01 CAPM_BASE** produces an exposure-weighted rate from independently executed model outputs and aligned positive/zero exposure weights; **HC.COST.08** returns fixed-baseline Price, Volume and Mix comparisons using the latest comparable AS_OF snapshot rather than summing monthly deviations. All use the same TASE temporal calendar/coverage kernel via the [unified model temporal API](tase/temporal_dispatch.py).

**Temporal coverage: 18 reviewed reference contracts across 9 distinct HC model codes of 116.** The underlying mathematical reference model count remains 27/116, financial S2 is closed, and FIN source proof/Redis sessions are not implemented. The requirement remains Redis-only ephemeral user data, absolute TTL <= 10,800 seconds with atomic delete upon authenticated ACK; no data persistence in FEngine.

[Design, examples and limitations](docs/FENGINE-MODEL-TEMPORAL-CAPABILITY-V12-ACCEPTANCE.md) · [Bounded executor](tase/model_temporal_v12.py) · [V1.2 capability catalogue](catalog/model_temporal_capabilities_v12.tsv) · [numeric and negative tests](tests/test_model_temporal_capability_v12.py) · [portable golden vectors](tests/golden/model_temporal_v12_reference_vectors.json).

## Current user-data retention policy (supersedes historical PostgreSQL proposals)

FEngine is an **ephemeral computation engine**, not a durable source-fact warehouse. Runtime calculation inputs, intermediate state and results must be stored **only in Redis** for an absolute maximum of **3 hours (10,800 seconds)**. On explicit authenticated successful consumer ACK, the entire calculation session and results must be **atomically deleted immediately**. Reading or retrying must not renew the absolute expiration. No calculation user data may persist in PostgreSQL, Redis RDB/AOF, logs or backups. The Redis implementation and ACK/TTL cleanup acceptance remain **NOT IMPLEMENTED**; current Python functions are stateless in-process references and do not claim production data lifecycle compliance. Static algorithms and synthetic test fixtures may remain versioned in Git.

## HC-R0.1 — bounded real mathematical engine (Python reference)

**Executable in-process numerical calculations, not 116 production financial models.** HC-R0.2 added IRR/EIR, VaR/ES and ECL reference calculations; HC-R0.3 added CASH runway, COST break-even, COST EVM and Gordon terminal valuation; HC-R0.4 added indirect CFO, FCFF, EV-to-equity bridge and compound annual cost escalation. HC-R0.5 added two source-bound direct CFO variants and a typed direct-to-indirect reconciliation edge. HC-R0.6/R0.7 add two independent FCFE derivations and three-factor cost Price–Volume–Mix, giving **27 model codes and 48 named reference variants**, with **29 explicit reference variant rules**. All 222 catalogue variants remain financially unapproved. The package fengine_hc contains genuine Decimal reference functions for NPV/XNPV, CAPM/WACC, five depreciation methods, four dated loan schedules, FIFO/moving/periodic WAC, debt ageing and LLCR/PLCR. Explicitly selected variants are validated against the R3 catalogue; unsupported models/variants return typed errors instead of placeholder results.

- [Real Python HC reference implementation](fengine_hc/reference.py)
- [116-node candidate graph, typed in-memory calculation DAG and strategy graph](fengine_hc/graphs.py)
- [HC numerical golden and negative tests](tests/test_fengine_hc_reference.py)
- [Cross-model CAPM → WACC graph execution and cycle tests](tests/test_fengine_hc_graphs.py)
- [20-family primitive matrix, complete architecture and Rust parity gates](docs/FENGINE-HC-R01-METAMODEL-PRIMITIVE-MATRIX-AND-EXECUTION.md)
- [HC-R0.2 wave-by-wave implementation audit and outstanding gates](docs/FENGINE-HC-R02-WAVES-IMPLEMENTATION-AUDIT.md)
- [Typed parameter semantics and bounded variant resolver](fengine_hc/semantics.py)
- [IRR/EIR, VaR/ES and ECL numerical primitives](fengine_hc/r02_math.py)
- [Portable machine-readable golden reference cases](tests/golden/hc_r02_reference_vectors.json)
- [Typed plan/snapshot/edge negative tests](tests/test_fengine_hc_r02_graphs.py)
- [HC-R0.3 mathematical models and 3-hour Redis-only ACK purge mandate](docs/FENGINE-HC-R03-DECIMAL-CALCULATIONS-AND-EPHEMERAL-POLICY.md)
- [New reference model implementations](fengine_hc/r03_reference.py)
- [New numerical and boundary tests](tests/test_fengine_hc_r03_reference.py)
- [Portable golden vectors for seven variants](tests/golden/hc_r03_reference_vectors.json)
- [HC-R0.4 calculation methods, semantics and evidence](docs/FENGINE-HC-R04-CALCULATIONS-SEMANTICS-AND-TESTS.md)
- [HC-R0.4 real Python mathematical executors](fengine_hc/r04_reference.py)
- [HC-R0.4 synthetic portable golden vectors](tests/golden/hc_r04_reference_vectors.json)
- [HC-R0.4 unique/ambiguous auto-variant selection tests](tests/test_fengine_hc_r04_variant_resolution.py)
- [HC-R0.5 posted direct CFO + typed direct/indirect end-to-end](docs/FENGINE-HC-R05-POSTED-CFO-AND-TYPED-RECONCILIATION.md)
- [HC-R0.5 posted cashflow reference executor](fengine_hc/r05_cashflow.py)
- [Synthetic posted/reclassified portable SHA vectors](tests/golden/hc_r05_cashflow_vectors.json)
- [Strict source/classification cashflow tests](tests/test_fengine_hc_r05_cashflow.py)
- [Typed DAG reconciliation tests](tests/test_fengine_hc_r05_direct_indirect_graph.py)
- [HC-R0.6/R0.7 FCFE and Price–Volume–Mix full methodology, constraints and acceptance](docs/FENGINE-HC-R06-R07-FCFE-PVM-REFERENCE-AUDIT.md)
- [HC-R0.6 two FCFE methods and cross-method reconciliation](fengine_hc/r06_fcfe.py)
- [HC-R0.7 three-factor price / volume / mix executor](fengine_hc/r07_pvm.py)
- [FCFE mathematical tests and negative guards](tests/test_fengine_hc_r06_fcfe.py)
- [Price / volume / mix decomposition tests](tests/test_fengine_hc_r07_pvm.py)
- [Five portable Python/Rust golden vectors](tests/golden/hc_r06_r07_reference_vectors.json)
- [Portable SHA and numeric golden test runner](tests/test_fengine_hc_r07_portable_goldens.py)

**Risk control:** All 222 variants are *candidate method entries*; only the explicitly supported subset runs as PYTHON_REFERENCE_NOT_S2. The reference has no production-grade input source authority, independent financial qualification, Redis ephemeral job/ACK-purge implementation, signed calculation plan or certified Rust parity. Non-reference mode remains blocked. No generic fallback returns 0 or fabricated results.

## Method hardening R1 (2026-11-20)

**P0 draft corrections committed for review; no immutable financial freeze.** 17 method specification sections in W1–W4 now link to precise ECL, dated-rate/EIR, DCF/IRR, VaR/ES, true three-factor Price-Volume-Mix, and integer optimization requirements. No existing qualified contract is overwritten.

- [R1 P0 methodology corrections and independently reproducible controls](docs/FENGINE-METHOD-HARDENING-R1-P0-ADDENDUM.md)
- [310 draft typed parameter proposals for all 95 model candidates](catalog/method_parameter_candidates_r1.tsv)
- [R1 independent Decimal and parameter tests](tests/test_fengine_method_hardening_r1.py)
- [CI workflow for R95 + R1 banks](.github/workflows/fengine-r95-model-bank.yml)

Independent control tests do not invoke any financial HC calculation implementation. Financial review, FIN source binding, production S2 and immutable per-method contract freeze remain blocked.


## Wave 5: Risk, HEDGE and Insurance formula candidates

- 7 existing RISK methods retain their original task identities; their formula definitions are expanded without duplicate model codes.
- 7 new HEDGE + 14 new INS methods add 21 **candidate-only** model contracts; new input DTOs D94–D114.
- 28 formula expressions, 28 standalone synthetic math examples, typed candidate parameters and failure conditions are loaded in a separate registry, **not** a production-ready Python calculation engine.
- [28 formula candidates](catalog/risk_hedge_insurance_formula_candidates_r2.tsv)
- [21 Wave-5 model candidate registry](catalog/model_extensions_r2.tsv)
- [28 synthetic golden candidate fixtures](catalog/risk_hedge_insurance_golden_candidates_r2.tsv)
- [Wave-5 hedge/insurance mathematical methodology, inputs and guardrails](docs/FENGINE-RISK-HEDGE-INSURANCE-W5-28-FORMULAS-TZ.md)

**Insurance methodology warning:** earned premiums/combined ratio, Chain Ladder/Bornhuetter–Ferguson, IFRS 17 FCF/RA/CSM and Kazakhstan solvency are distinct regulatory/actuarial scopes. No source-to-field qualification or financial S2 exists for these new candidates. Mortality/life insurance actuarial math remains a separate future wave.


## TASE-R0: Product-Extensible Temporal Aggregation & Statistics

**In-process Python TASE reference implemented and tested; NO durable financial Hub or production admission.** A single TASE core can serve FIN, BANK, INSURANCE, LOGISTICS, INDUSTRY and CUSTOM Product Packs with shared versioned temporal, grouping, statistics and comparison operators.

- [Full TASE-R0.1–R0.6 technical specification](docs/FENGINE-TASE-R0-UNIVERSAL-TEMPORAL-STATISTICS-TZ.md)
- [53 typed operator candidates](catalog/tase_operator_candidates_r0.tsv)
- [6 signed-pack design candidates](catalog/tase_product_pack_candidates_r0.tsv)
- [26 typed sample metric semantics](catalog/tase_metric_semantics_candidates_r0.tsv)
- [21 typed input predicate candidates](catalog/tase_input_predicates_r0.tsv)
- [42 TASE golden/negative acceptance seed cases](catalog/tase_golden_and_negative_candidates_r0.tsv)
- [Real Python TASE reference module](tase/reference.py)
- [TASE reference unit tests](tests/test_tase_reference.py)
- [Product extensibility/parameter audit tests](tests/test_tase_product_extensions.py)
- [Consolidated 116-model / 732-parameter R3 registry (current candidate baseline)](catalog/method_parameter_candidates_116_r3.tsv)
- [116 method-variant profiles (R3)](catalog/model_variant_profiles_116_r3.tsv)
- [222 method-variant definitions (R3)](catalog/method_variant_definitions_116_r3.tsv)
- [R3 integrity tests](tests/test_fengine_consolidated_r3.py)
- [PR #7 — merged method variants](https://github.com/alimbetov/FEngine/pull/7)
- [2026-11-20 R3 consolidation CI — 169 tests/97 contract tests on both Python 3.11 and 3.13](https://github.com/alimbetov/FEngine/actions/runs/44722823796)
- [Historical R0 inventory — 417 parameter candidates, fully included in R3](catalog/model_parameter_inventory_116_r0.tsv)
- [32 TASE core config parameter candidates](catalog/tase_core_parameter_candidates_r0.tsv)
- [Current implementation audit and Python→Rust gates](docs/FENGINE-TASE-PY-R01-IMPLEMENTATION-AUDIT.md)
- [Python 3.11/3.13 reference CI run (131/131 each)](https://github.com/alimbetov/FEngine/actions/runs/44721269472)

Semantics: FLOW SUM, STOCK LAST_AS_OF and RATIO_OF_SUMS are implemented in the strict reference; qualified time-weighted stock, custom fiscal 4-4-5, full Session/DAG and other complex operations remain future work. Missing interval authority or watermark blocks strict completeness. The 250-case TASE R0.6 suite is **not PASS**; the current confirmed 131 Python reference unittests include 34 TASE-focused test methods and preexisting tests, not all future acceptance scenarios. TASE is a platform capability and does not change the 116 candidate HC model count.

## Current audit decision

**R3 integration:** 732 parameter/222 variant candidates cover all 116 model codes and preserve the earlier 417 parameter entries. All R3 catalogue entries remain unapproved financial method candidates; a bounded subset now has separately implemented mathematical Python reference executors. `main` is authoritative; the 95-model R2 tables are historical inputs, not the current complete registry.


**CONTRACT_FREEZE_BLOCKED** pending methodology and applicability review, pre-freeze typed parameter additions, source-to-field mappings, independent golden examples and full mathematical edge cases (ECL, EIR/GESV, DCF/IRR, VaR/ES, PVM and optimization).

- [95-model methodological and functional audit](docs/FENGINE-R95-METHODOLOGICAL-AND-FUNCTIONAL-AUDIT-2026-11-20.md)
- [95-model risk and pre-freeze parameter matrix](docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv)
- [MethodParameterContractV2 pre-freeze design](docs/FENGINE-R95-PARAMETER-CONTRACT-V2-DESIGN.md)
- [R95 independent contract and arithmetic bank — Python 3.11/3.13, 34/34 CI PASS](https://github.com/alimbetov/FEngine/actions/runs/44703835282)
- [83-model original audit](docs/FENGINE-R83-METHODOLOGICAL-AUDIT-2026-11-20.md)
- [83-model pre-freeze parameter and negative-test matrix](docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv)
- [All 116 candidate models and architecture](FENGINE_MASTER_SPEC.md)
- [P0 Wave-1: 14 detailed model contracts](docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md)
- [P1 Wave-2: 42 detailed model contracts](docs/FENGINE-HPC-WAVE2-P1-42-METHOD-DTO-RESULT-TZ.md)
- [P2 Wave-3: 27 statistical/regulatory model contracts](docs/FENGINE-HPC-WAVE3-P2-27-STATISTICAL-METHOD-DTO-TZ.md)
- [Python-first Memory Calculation Hub design](docs/FENGINE-PY-R0-PYTHON-MEMORY-CALCULATION-HUB-ARCHITECTURE-TZ.md)
- [GEO-OPT reference code qualification notes](docs/FENGINE-GEO-OPT-R01-R04-REFERENCE.md)
- [GEO-OPT CI evidence](https://github.com/alimbetov/FEngine/actions/runs/44699098351)

## Core contracts

- Fact: sourced and typed stock/flow with currency, period, dimensions and provenance.
- Metric: stable meaning and qualified source linkage.
- Methodology revision: formula, business/legal applicability, parameters, financial semantics and evidence SHA.
- Calculation Session: sealed immutable datasets reused across multiple independently idempotent jobs.
- Calculation Response: versioned results array with typed rows, values, units, lineage, errors and statuses.
- Outbox and archive receipt: durable immutable committed results before temporary payload deletion.
- Finance S2: independent financial approval distinct from mathematical unit tests and Python/Rust parity.

**Do not call any of the 116 financial model implementations production-ready until implemented and independently qualified.**
