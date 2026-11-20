# FEngine — Financial & Economic Calculation Engine

FEngine is a specification-first, evidence-driven financial and economic calculation platform. Its purpose is to turn immutable, typed source facts into reproducible numerical outputs, versioned methods and auditable results.

## Authoritative branch

**main** is the single integration branch. The former methodology, OPT and GEO-OPT development pull requests have been merged. No new feature branch is the authoritative copy of the specification.

## Current implemented vs designed scope (20 November 2026)

| Scope | Verified status |
|---|---|
| Financial/economic HC catalogue | **83 candidate model contracts** — 14 P0 + 42 P1 + 27 P2; not implemented |
| Input datasets | D01–D81 logical typed DTO candidates, not verified FIN source bindings |
| Fact catalogue | 235 unique DRAFT source fact definitions |
| Financial 83-model Python Calculation Hub | **Not implemented**; mathematical, numerical and financial admission gates remain closed |
| GEO-OPT Python reference | Typed directed graph compiler, Dijkstra, A*, Yen K-shortest paths; **38/38 unittest tests** on Python 3.11 and 3.13 in GitHub Actions |
| Functional finance E2E / PostgreSQL / Inbox-Outbox | Not implemented, not tested |

Independent synthetic arithmetic checks performed during review: 83/83 positive examples and 34/34 boundary/invariant cases. These tests do **not** import executable HC model code, and do not constitute financial S2, regulatory qualification, or functional finance engine acceptance.

## Current audit decision

**CONTRACT_FREEZE_BLOCKED** pending methodology and applicability review, pre-freeze typed parameter additions, source-to-field mappings, independent golden examples and full mathematical edge cases (ECL, EIR/GESV, DCF/IRR, VaR/ES, PVM and optimization).

- [83-model methodology audit](docs/FENGINE-R83-METHODOLOGICAL-AUDIT-2026-11-20.md)
- [83-model pre-freeze parameter and negative-test matrix](docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv)
- [All 83 models and architecture](FENGINE_MASTER_SPEC.md)
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

**Do not call any of the 83 financial model implementations production-ready until implemented and independently qualified.**
