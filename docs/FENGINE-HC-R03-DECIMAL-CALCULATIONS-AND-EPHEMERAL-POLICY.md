# FEngine HC-R0.3 — Decimal calculation wave and golden acceptance

**2026-11-20 • Python reference only • Financial S2: NOT_APPROVED**

## Verified scope

- Existing R3 catalogues unchanged: **116 model codes / 222 candidate method variants / 732 candidate parameter bindings**, all financial S2 still blocked.
- This wave adds **4 executable mathematical reference model codes** and **7 selected method variants**, on top of the previous 16 codes / 29 selected variants, for a total of **20 model codes / 36 variants**. Neither counter represents qualified financial methodology.
- Executors: [r03_reference.py](../fengine_hc/r03_reference.py). Strict option/schema binding: [semantics.py](../fengine_hc/semantics.py). Integration: [reference.py](../fengine_hc/reference.py).
- Portable independent numerical examples: [hc_r03_reference_vectors.json](../tests/golden/hc_r03_reference_vectors.json).
- [Golden/negative unit tests](../tests/test_fengine_hc_r03_reference.py) and [machine-readable fixture tests](../tests/test_fengine_hc_r03_portable_golden.py).

## Implementation truth table

| Model / method | Reference algorithm | Golden / constraints | Qualification |
|---|---|---|---|
| `HC.CASH.03 DETERMINISTIC_RUNWAY` | Ordered dated net cashflows; first breach under explicit strict or inclusive floor policy | 100 → 70 → 20 → 19: strict floor=20 breaches 2026-01-11; inclusive breaches 2026-01-10 | Mathematical reference only |
| `HC.CASH.03 SCENARIO_RUNWAY` | Same first-passage calculation for each explicit scenario, **without inventing scenario probabilities** | No-breach state is not zero; distinct scenarios and paths | Mathematical reference only |
| `HC.COST.04 SINGLE_PRODUCT_BREAKEVEN` | Fixed costs / positive contribution per unit; ceil to whole unit | Fixed 1000 / contribution 40 → 25 units; 1001 → 26 | Mathematical reference only |
| `HC.COST.04 PRODUCT_MIX_BREAKEVEN` | Fixed integral bundle ratio; contribution per bundle; ceil to whole bundles | A×2 + B×1 yields 110 contribution/bundle; fixed 1000 → 10 bundles | Mathematical reference only |
| `HC.COST.07 EVM_BAC_CPI` | EV/AC CPI, variance, EAC = BAC/CPI | PV=80, EV=60, AC=75, BAC=120: CPI .8 and EAC 150 | Mathematical reference only |
| `HC.COST.07 EVM_EAC_FORECAST` | AC + (BAC−EV), remaining work at budget rate | Same source: EAC 135, not 150; **not** algebraically equivalent to BAC/CPI | Mathematical reference only |
| `HC.DCF.07 GORDON_FCFF_TERMINAL` | FCFF next year = final FCFF × (1+g); TV=FCFF_next/(WACC−g); discount at WACC | FCFF 100, g .02, WACC .10 → TV 1275 | Mathematical reference only |

### Restrictive input contract and negative gates

- Python Decimal strings only for financial magnitudes, no binary floats; negative fixed/variable cost, zero/negative margin, incompatible bundle mix, invalid currency token, unknown nested row fields, duplicate scenario/stock codes are rejected.
- A **single 3-letter uppercase currency token** is required, but this reference does **not** itself certify an ISO-4217 registry, source FX vintage, or cross-currency conversions.
- `CASH.03` requires strictly increasing dated events and uses supplied points only. `NO_BREACH_WITHIN_HORIZON` is explicitly different from immediate breach (0 elapsed days). Intraday troughs between observations are out of scope.
- `COST.04` assumes fixed product bundle composition and positive unit margins. Split-bundle optimization, mixed units/FX, taxes and cost-base qualification remain out of scope.
- `COST.07` assumes already-reviewed source EV, PV, AC and BAC *as supplied*: the engine does not calculate earned-value eligibility and does not certify the baseline revision. Zero actual cost/CPI for EAC, EV > BAC, unmatched variant config fail closed.
- `DCF.07` assumes matching **nominal annual** FCFF/WACC/growth basis and a perpetual Gordon continuation. Requires `WACC > g > -1`, WACC positive and nonnegative terminal FCFF. Neither exit multiples nor FCFE basis are silently substituted.
- Explicit reference-mode only: `PYTHON_REFERENCE_NOT_S2`; all unimplemented named methods reject `VARIANT_RULE_NOT_IMPLEMENTED`. No fallback or inferred financial approval.

## Mandatory data lifecycle: Redis-only ephemeral

Earlier PostgreSQL storage proposals in historical design notes are **superseded**. Effective architecture mandate:

1. FEngine calculation input facts, intermediate DAG snapshots, result payloads, receipt state and consumer-delivery data may live **only in ephemeral Redis**, never in PostgreSQL or other durable user-data stores; in-process reference calculation holds only transient local values.
2. Create an **absolute session deadline** of at most 10,800 seconds; neither read nor retry extends it. All descendants share the same non-sliding expiry.
3. Consumer delivery does not equal successful consumption. On authenticated, idempotent ACK verifying the intended result/session and consumer identity, **atomically invalidate/delete all related keys immediately**.
4. Missing ACK permits replay only until the absolute deadline. After expiry, access must fail even if Redis has not yet physically reclaimed a key.
5. AOF/RDB, backup, application logs, tracing, exception bodies, dead-letter queues, crash dumps and third-party telemetry must not retain calculation user data beyond the policy. In Redis, consider `appendonly no` and `save ""`, with deployment-level verification.
6. The math library does not implement Redis or claim deletion tests. A separately implemented ephemeral Redis runtime is required before any distributed production use.

**Persistent artifacts allowed:** source code, static formula definitions, anonymized synthetic golden cases, method templates. **Not allowed:** customer values, input FactSets, result payloads, or event-level receipts after session purge.

## Acceptance and Rust order

Run on Python **3.11 and 3.13**:

```bash
python -m unittest discover -s tests -v
```

Inspect results from the exact HEAD's GitHub Actions rather than inheriting historical PASS. Next work: semantic qualifiers and variant predicates for all 732/222 (not just code/type labels), dimensionality/temporal source guards, mathematically independent goldens for additional model families; only then Redis ACK purge contract, and only after frozen reference numerical semantics should Rust and performance comparison begin.
