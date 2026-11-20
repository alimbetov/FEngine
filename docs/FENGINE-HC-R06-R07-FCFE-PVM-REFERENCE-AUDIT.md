# FEngine HC-R0.6 / HC-R0.7 — FCFE and Price–Volume–Mix mathematical implementation

**Date:** 2026-11-20  
**Status:** Python Decimal executable **REFERENCE_NOT_S2**; no independently qualified source accounting, pricing policy or financial S2 approval.  
**Scope:** two HC.DCF.06 variants + three HC.COST.08 variants; existing R3 catalogues remain unchanged.

## Coverage truth

| Item | Previous | After this wave |
|---|---:|---:|
| Catalogued model candidates | 116 | 116 |
| Mathematical Python-reference executable models | 25 | **27** |
| Named catalog method candidates | 222 | 222 |
| Named reference-executable variants | 43 | **48** |
| Model+variant parameter rules | 24 | **29** |
| Independently approved financial S2 variants | 0 | **0** |

These counters are reference-runtime coverage only; do not infer model regulatory admission or completeness of every named catalogue method.

## HC-R0.6 — FCFE (free cash flow to equity)

Implemented [r06_fcfe.py](../fengine_hc/r06_fcfe.py) and [tests](../tests/test_fengine_hc_r06_fcfe.py). Both formulas use decimal strings for money and explicit positive gross borrowing/repayment magnitudes. Both **include interest at the underlying CFO/net-income stage** and prohibit adding interest and tax shields again.

Two separately selected methods:

1. **FCFE_LEVERED**: FCFE = operating cash flow *after interest* − cash CAPEX + gross new borrowing − principal debt repayments. The operating CFO is supplied as a separate source value, not automatically derived from arbitrary upstream financial models. No financing proceeds or repayments are allowed to be included in that CFO basis.
2. **FCFE_NORMALIZED**: operating CFO bridge = net income *after interest* + nonnegative noncash operating charges − increase in operating NWC. Then FCFE = operating CFO bridge − cash CAPEX + gross new borrowing − principal repayments.

Named policies must match the reviewed reference candidate rule:

- debtFlowPolicy = GROSS_DRAWDOWN_LESS_PRINCIPAL
- netBorrowingMethod = DRAWDOWNS_MINUS_PRINCIPAL_REPAYMENTS
- cashflowToEquityPolicy = NO_INTEREST_READD
- taxShieldEligibility = NO_EXTRA_TAX_SHIELD
- equityCashflowBasis is distinct and mandatory for each variant
- costOfEquityRef is a 64-character SHA-256 pin matching the separately hashed annual cost-of-equity reference.

### Independent example

- Post-interest CFO = **110**; normalized CFO = 100 net income + 30 noncash charges − 20 incremental operating NWC = **110**.
- Cash CAPEX = 50, gross new debt drawdowns = 40, principal repayments = 15; net borrowing = **25**.
- Both methods produce **FCFE = 110 − 50 + 25 = 85**.
- Nominal annual equity discount rate Ke = 10%, period index = 1: **PV(FCFE) = 85 / 1.10 = 77.27272727272727272727272727272727272727…**.
- Separate method reconciliation compares currency, date, time index and *rate revision*, then exact FCFE. Mismatch rejects; no quiet rebalancing, zero floor, or substitution of WACC for Ke.

**Important boundaries:** Source SHA hashes ensure local snapshot integrity; they do not verify an external lender, accounting ledger, signed FactSet, rate-source authenticity, or tax eligibility. The optional Ke present-value computation is a strict *annual period-end integer-index reference*, not ACT/365 dated discounting. The 0–100% annual Ke bound, nonnegative noncash charges and 1–100 year index are explicit reference limitations, not generally universal economic assumptions. No universal DAG edge from CFO to FCFE is admitted until the semantic source lineage and source-snapshot digest can be bound together without overrides.

## HC-R0.7 — cost Price / total Volume / Mix

Implemented [r07_pvm.py](../fengine_hc/r07_pvm.py) and [tests](../tests/test_fengine_hc_r07_pvm.py).

**Not** a naive SKU quantity variance or a two-factor price/volume calculation. All three named catalogue variants execute the same complete exact-source decomposition and expose a different selected factor:

- PRICE_VARIANCE: effect from changing SKU unit cost at **actual** quantity.
- QUANTITY_VARIANCE: **aggregate total quantity / volume**, holding baseline SKU proportions and baseline unit cost.
- MIX_VARIANCE: change in SKU proportions at actual total quantity, holding baseline SKU unit costs.

Let Q0, Q1 be total baseline/current quantities; C0, C1 total baseline/current costs, and Cmix = sum(actual SKU quantity × baseline SKU unit cost). Using baseline weighted unit cost C0/Q0:

- Volume = (Q1 − Q0) × C0 / Q0.
- Mix = Cmix − C0 − Volume.
- Price = C1 − Cmix.
- Exact algebraic identity: **Price + Volume + Mix = C1 − C0**. Decimal computations use a 50-digit local precision and reject residual beyond an explicitly bounded precision tolerance. Finite-decimal reporting can have a tiny last-digit residual when Q0 does not divide evenly; that is reported rather than silently allocated.

### Independent golden example (one consistent physical unit and currency)

| SKU | Q0 | Q1 | Baseline unit cost | Current unit cost |
|---|---:|---:|---:|---:|
| A | 60 | 50 | 10 | 11 |
| B | 40 | 60 | 20 | 18 |

- Baseline total cost C0 = **1,400**; actual total cost C1 = **1,630**.
- Q0 = 100; Q1 = 110; baseline weighted unit cost = 14.
- **Aggregate volume effect = +140**.
- **SKU mix effect = +160**.
- **Unit-cost price effect = −70**.
- **Total cost variance = +230**. Accounting: 140 + 160 − 70 = 230 = 1630 − 1400. Positive cost movement is adverse by explicit convention.

### Guards

- Baseline/current dates and explicit *one* currency and physical quantity unit are required.
- SKU keys are unique; full SKU universe is present in a single response with a strictly positive baseline quantity for every entry. Discontinued SKUs may have zero actual quantity. **New SKUs with zero baseline are blocked** because their attribution requires an approved baseline-price/cost policy.
- No negative SKU quantities or unit costs, zero aggregate actual quantity, duplicate/unknown schema fields, binary floats, noncanonical dates or inconsistent signed revision hashes.
- Four independent SHA-256 values bind the baseline joint quantity/cost, actual joint quantity/cost, baseline unit cost schedule and baseline SKU quantity schedule. Matching digests alone does not confer independent accounting qualification.
- All three variants are explicit: they are not automatically chosen by the resolver when the same configuration satisfies all three, as that would be ambiguous.

## Executable synthetic controls

- [Five machine-readable independent golden vectors](../tests/golden/hc_r06_r07_reference_vectors.json)
- [Portable golden tests and revision checks](../tests/test_fengine_hc_r07_portable_goldens.py)
- [FCFE derivation, mismatch, SHA and policy negative tests](../tests/test_fengine_hc_r06_fcfe.py)
- [PVM pure price / volume / mix, cost reconciliation and SKU drift tests](../tests/test_fengine_hc_r07_pvm.py)
- [Variant-scoped bound parameters](../fengine_hc/semantics.py)
- [Reference engine integration](../fengine_hc/reference.py)

Regression uses Python 3.11 and Python 3.13:

```bash
python -m unittest discover -s tests -v
```

Completion requires both Python and financial-reference-bank GitHub workflows **SUCCESS for the exact final HEAD**. Historical GREEN is not sufficient proof.

## Data retention (mandatory superseding rule)

FEngine is an ephemeral computation engine. It must **not** persist customer financial source facts, calculation plans/results or deliveries in PostgreSQL or permanent object stores. The eventual distributed session runtime will use **Redis only**, maximum absolute TTL **10,800 seconds**, with **immediate atomic deletion on authenticated successful consumer ACK**. Reads/retries cannot extend the deadline; Redis persistent snapshots/AOF/backups/logging of user data are disallowed. This wave adds **no Redis state, persistent customer data or cross-service uploads**. The Redis ACK/TTL runtime and its network-failure/integration tests remain **unimplemented**.

## Deferred, not hidden

Financial S2, real-source classification admission, IFRS/nonstandard tax treatment, currency conversion, nominal/real rate matching across systems, new-SKU attribution, signed upstream-graph inputs, Monte Carlo/optimization generality, and Rust parity/performance benchmarking are not claimed.

**Next gates:** stricter source basis/evidence for cross-model FCFE, richer PVM policies with explicit new-SKU handling *only after financial review*, and eventually a separately tested Redis ACK+purge runtime. No Rust until the bounded Python reference and portable parity vectors are stable.
