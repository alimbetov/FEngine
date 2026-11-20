# FEngine HC-R0.4 — CFO, FCFF, Enterprise→Equity and Compound Cost Reference

**Reference status:** Python mathematical executable, financial S2 **NOT_APPROVED**.  
**Date:** 2026-11-20.  
**Repository baseline:** 116 model candidates, 222 method candidates, 732 parameter candidates. Original R3 files remain unchanged.

## Scope of this bounded wave

Five **real** reference-mode variants in four additional model codes, increasing coverage from **20 models / 36 variants** to **24 models / 41 variants**. The remaining **92 model codes / 181 variants** do not have executable reference implementations. All 222 method catalogue entries remain financial draft/not S2 approved.

| Code / variant | Algorithm | Independent reference example | Guard |
|---|---|---|---|
| `HC.CASH.05 INDIRECT_CFO_ADJUSTMENT` | CFO = afterTaxNetIncome + sum(signedNoncashItems) - increaseOperatingNWC | 100 + (20−5) − 15 = **100** | Duplicate adjustments, sign convention, source SHA, row schemas |
| `HC.CASH.05 INDIRECT_CFO_RECONCILED` | Identical CFO, additionally exact equality with separately supplied posted direct CFO | 100 − 100 = **0** | Mismatch rejects; does not fabricate reconciliation |
| `HC.DCF.05 FCFF_UNLEVERED` | FCFF = EBIT×(1−taxRate) + noncashOperatingCharges − cashCapex − changeOperatingNWC | 200×0.75 + 30 − 50 − 20 = **110** | Negative EBIT blocked until tax-loss policy approved; no finance costs deducted |
| `HC.DCF.08 EV_TO_EQUITY_BRIDGE` | Equity = EnterpriseValue − grossInterestDebt + unrestrictedCash + nonOperatingAssets − NCI − preferredClaims | 1000−300+50+20−40−10 = **720** | Matching valuation date, no duplicated bridge component, no equity floor |
| `HC.COST.05 COMPOUND_ESCALATION` | FutureCost = BaseCost × product(1+annualRate[i]) | 1000×1.10×1.05 = **1155** | Finite rates >−100%, absolute source SHA equality, explicit no-contingency-overlap |

**Direct CFO:** The `INDIRECT_CFO_RECONCILED` variant accepts an independently supplied `directCfo` value and rejects nonzero difference. It does *not* calculate direct CFO from bank transactions. That remains `HC.CASH.04` and is not implemented.

**Tax:** Simplified EBIT tax applies only to nonnegative EBIT and provided rate in [0,1]. This cannot replace qualified deferred/realized tax calculations, stage/revision policy, loss carryforwards, or current-law interpretation.

**Equity bridge:** Assumes no double-counted EV inclusions, non-operating asset classification and NCI/preferred definitions. A source SHA is evidence of input version *identity*, not evidence that source itself has been financially reviewed.

**Escalation:** `inflationIndexRev` must be a lowercase hex SHA-256 pin equal to the rates dataset revision supplied with the input. SHA matching is not official inflation-index certification or proof that a human-approved source was used.

## Semantic hardening

- R3 variant names, 732 parameter bindings and 5 name/type collisions are preserved. Each of the 5 newly executable variants has an explicit `VariantRule` with checked parameter types and exact variant-specific enum/reference codes.
- All **22 explicitly defined reference rules** are checked at registry initialization for actual catalog membership, bound model/parameter code, supported enum logical type and required SHA reference types.
- `ParameterSemantics.resolve_unique(model, config, reference_mode=True)` now offers **automatic, fail-closed** selection among those 22 reviewed reference rules. **Zero candidates** ⇒ `NO_COMPATIBLE_VARIANT`; **two+ candidates** ⇒ `AMBIGUOUS_VARIANT`. It does not silently select a financial method.
- The remaining 200 catalog variant candidates have **no automatically executable rule**. New code must not infer a rule from candidate prose.
- Full generalized parameter-DSL, source lineage proof, per-industry eligibility and automatic generation of every variant remain unimplemented.

## Mathematical evidence and tests

- [Python executor](../fengine_hc/r04_reference.py)
- [Model integration](../fengine_hc/reference.py)
- [Semantic resolver and type guards](../fengine_hc/semantics.py)
- [Five portable JSON golden cases](../tests/golden/hc_r04_reference_vectors.json)
- [Numerical, rejection and trace tests](../tests/test_fengine_hc_r04_reference.py)
- [Independent algebraic invariants](../tests/test_fengine_hc_r04_invariants.py)
- [Automatic variant selection and 222-variant catalog audit](../tests/test_fengine_hc_r04_variant_resolution.py)

Python 3.11 and 3.13 regression command:

```bash
python -m unittest discover -s tests -v
```

CI evidence must be from the final committed HEAD and two Python versions; prior commits' PASS does not qualify new code. This stage is **not** an IFRS/regulatory S2 financial sign-off.

## User-data lifecycle — superseding rule

**FEngine is not a database for users' financial data.**

Runtime user inputs, calculations, graphs, intermediate values, results and delivery state must be held **only in ephemeral Redis** with **absolute maximum TTL of 10,800 seconds**, no sliding renewal. On authenticated successful consumer ACK, the entire session/result key set must be **atomically deleted immediately**. After expiry all access must reject, even if Redis has not yet physically reclaimed keys.

No historical PostgreSQL persistence plan applies to user calculations. Redis snapshots, AOF, RDB, backups, application logs, distributed tracing, retry/dead-letter caches and third-party telemetry cannot retain user payloads outside this lifetime. This Python math package is in-memory/stateless; it does **not** implement Redis transport, ACK, purge, or Redis integration tests yet. Permanent source code, static method definitions and synthetic test vectors are permitted.

## Next safe wave

Extend only one related model family at a time with executable contract + independent goldens: `HC.CASH.04` verified posted direct CFO and exact reconciliation; `HC.DCF.06` equity cashflows with approved debt-flow eligibility; `HC.COST.08` balanced price/quantity/mix bridges. Separate Redis ephemeral ACK runtime acceptance remains required before distributed/production delivery; Rust stays on hold pending Python mathematical closure and parity test plan.
