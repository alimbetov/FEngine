# FEngine — Financial & Economic Calculation Engine

FEngine is a specification-first, evidence-driven financial and economic calculation platform. Its purpose is to turn immutable, typed source facts into reproducible numerical outputs, versioned methods and auditable results.

## Authoritative branch

**main** is the single integration branch. The former methodology, OPT and GEO-OPT development pull requests have been merged. No new feature branch is the authoritative copy of the specification.

## Current implemented vs designed scope (20 November 2026)

| Scope | Verified status |
|---|---|
| Financial/economic HC catalogue | **95 candidate model contracts** — W1 14 + W2 42 + W3 27 + W4 12; financial HC not implemented |
| Input datasets | D01–D93 logical typed DTO candidates, not verified FIN source bindings |
| Fact catalogue | 235 unique DRAFT source fact definitions |
| Financial 95-model Python Calculation Hub | **Not implemented**; mathematical, numerical and financial admission gates remain closed |
| GEO-OPT Python reference | Typed directed graph compiler, Dijkstra, A*, Yen K-shortest paths; **38/38 unittest tests** on Python 3.11 and 3.13 in GitHub Actions |
| Functional finance E2E / PostgreSQL / Inbox-Outbox | Not implemented, not tested |

Prior 83-model review: 83/83 external synthetic arithmetic and 34/34 external boundary examples (historical). New R95 CI: 34/34 unittest methods on Python 3.11 and 3.13, including 95 specification-level subtests plus independent Decimal invariants. None of these tests import executable financial HC model code, and do not constitute financial S2, regulatory qualification, or functional finance engine acceptance.

## Current audit decision

**CONTRACT_FREEZE_BLOCKED** pending methodology and applicability review, pre-freeze typed parameter additions, source-to-field mappings, independent golden examples and full mathematical edge cases (ECL, EIR/GESV, DCF/IRR, VaR/ES, PVM and optimization).

- [95-model methodological and functional audit](docs/FENGINE-R95-METHODOLOGICAL-AND-FUNCTIONAL-AUDIT-2026-11-20.md)
- [95-model risk and pre-freeze parameter matrix](docs/FENGINE-R95-PREFREEZE-AUDIT-MATRIX-2026-11-20.tsv)
- [MethodParameterContractV2 pre-freeze design](docs/FENGINE-R95-PARAMETER-CONTRACT-V2-DESIGN.md)
- [R95 independent contract and arithmetic bank — Python 3.11/3.13, 34/34 CI PASS](https://github.com/alimbetov/FEngine/actions/runs/44703835282)
- [83-model original audit](docs/FENGINE-R83-METHODOLOGICAL-AUDIT-2026-11-20.md)
- [83-model pre-freeze parameter and negative-test matrix](docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv)
- [All 95 candidate models and architecture](FENGINE_MASTER_SPEC.md)
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

**Do not call any of the 95 financial model implementations production-ready until implemented and independently qualified.**
