# FEngine — Financial & Economic Calculation Engine

FEngine is a specification-first, evidence-driven financial and economic calculation platform. Its purpose is to turn immutable, typed source facts into reproducible numerical outputs, versioned methods and auditable results.

## Authoritative branch

**main** is the single development and integration branch. The former methodology, OPT, GEO-OPT and flexible-method-variants branches were merged via pull requests; the old feature branch `feat/fengine-flex-method-variants-r1` was retired. Do not develop new work on historical feature branches.

## Current implemented vs designed scope (20 November 2026)

| Scope | Verified status |
|---|---|
| Financial/economic HC catalogue | **116 candidate model contracts** — W1 14 + W2 42 + W3 27 + W4 12 + W5 21; financial HC still not implemented |
| Input datasets | D01–D114 logical typed DTO candidates, not verified FIN source bindings |
| Fact catalogue | 235 unique DRAFT source fact definitions |
| Financial 116-model Python Calculation Hub | **Not implemented**; mathematical, numerical and financial admission gates remain closed |
| GEO-OPT Python reference | Typed directed graph compiler, Dijkstra, A*, Yen K-shortest paths; **38/38 unittest tests** on Python 3.11 and 3.13 in GitHub Actions |
| Functional finance E2E / PostgreSQL / Inbox-Outbox | Not implemented, not tested |

Prior 83-model review: 83/83 external synthetic arithmetic and 34/34 external boundary examples (historical). New R95 CI: 34/34 unittest methods on Python 3.11 and 3.13, including 95 specification-level subtests plus independent Decimal invariants. None of these tests import executable financial HC model code, and do not constitute financial S2, regulatory qualification, or functional finance engine acceptance.

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

**R3 integration:** 732 parameter/222 variant candidates cover all 116 model codes and preserve the earlier 417 parameter entries. All R3 records remain unapproved financial method candidates, not executable HC methods. `main` is authoritative; the 95-model R2 tables are historical inputs, not the current complete registry.


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
