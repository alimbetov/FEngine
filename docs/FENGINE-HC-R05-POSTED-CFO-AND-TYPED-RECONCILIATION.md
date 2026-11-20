# FEngine HC-R0.5 — posted direct CFO and typed direct–indirect reconciliation

**Date:** 2026-11-20  
**Status:** executable Python Decimal mathematical reference; independent financial S2 **NOT_APPROVED**.

## Implementation scope and evidence

Existing R3 catalogue is unchanged: **116 models / 222 candidate variants / 732 parameter bindings**. This wave adds real reference execution for **HC.CASH.04**, two named method variants, and a typed reference link to **HC.CASH.05**. The resulting mathematical reference totals are **25/116 model codes** and **43/222 variant selections**. There are **24 explicitly bound reference-mode variant rules**; the total of 43 selected executor variants is not synonymous with the rule count, because earlier variants use internally validated reference branches.

- [Source-bound direct CFO implementation](../fengine_hc/r05_cashflow.py)
- [Reference engine integration](../fengine_hc/reference.py)
- [Versioned semantic variant rules](../fengine_hc/semantics.py)
- [Typed CFO DAG edge and currency/period validation](../fengine_hc/graphs.py)
- [Posted and reclassified numerical/negative tests](../tests/test_fengine_hc_r05_cashflow.py)
- [Actual direct CFO → indirect CFO E2E](../tests/test_fengine_hc_r05_direct_indirect_graph.py)
- [Independent portable SHA and golden checks](../tests/test_fengine_hc_r05_portable_goldens.py)
- [Portable synthetic input/output vectors](../tests/golden/hc_r05_cashflow_vectors.json)

## Real arithmetic

A synthetic dated ledger contains these posted movements in KZT:

| Posted entry | Direction | Magnitude | Classification |
|---|---|---:|---|
| Customer receipt | IN | 200 | OPERATING |
| Supplier payment | OUT | 80 | OPERATING |
| Capital expenditure | OUT | 30 | INVESTING |
| Financing draw | IN | 50 | FINANCING |
| Internal cash transfer, sender leg | OUT | 40 | INTERNAL_TRANSFER |
| Internal cash transfer, receiver leg | IN | 40 | INTERNAL_TRANSFER |

**Direct CFO = 200 - 80 = 120**. Investing cash flow = -30, financing = +50, balanced internal transfer = 0. All booked cash movements reconcile: **opening 1,000 + 140 = closing 1,140**. Unbalanced / unmatched internal transfer legs, duplicate posting IDs, missing classification, unexpected fields, invalid direction/date, missing source digest or inconsistent overall balance all fail closed.

The second variant, DIRECT_RECLASSIFIED_CFO, permits an explicitly attributed change of the 30-unit capital-expenditure payment to an operating payment, with a separate SHA-256 bound to the original posted source revision. Then CFO = **90**, investing = 0, financing = +50, and total cash movement remains 140. Internal-transfer postings may not be silently reclassified.

The independent indirect CFO example uses after-tax net income 100, noncash adjustment +40 and increase in operating NWC +20: **100 + 40 - 20 = 120**. The typed runtime graph binds *the actual calculated* DIRECT_POSTED_CFO.output.cashFlowFromOperations to INDIRECT_CFO_RECONCILED.input.directCfo. It does **not** pass a caller-supplied direct CFO value. The reconciliation difference is zero. If the indirect calculation produces 121, the plan fails with CFO_RECONCILIATION_MISMATCH.

## Classification and reference integrity

- The input ledger carries a complete source snapshot SHA-256 of period, source currency, balances and ordered postings.
- An explicit model-scoped set of classification rules maps *posted classification codes* into OPERATING, INVESTING, FINANCING and INTERNAL_TRANSFER. An event cannot classify itself arbitrarily by setting a class field; it references an existing code.
- The classification rules are normalized and SHA-256 pinned; the arithmetic reconciliation policy also has a fixed versioned SHA.
- Each reclassification override is bound to the exact original posted-source SHA and pinned reclassification revision SHA. No anonymous reclassification, reclassification of transfers, duplicate overrides, unknown code, or same-code no-op is allowed.
- Only POSTING_DATE_ONLY and fully paired intra-period internal transfers are supported. All postings must be explicitly inside an inclusive accounting interval and the configured cutoff must match the period end.
- No FX conversion, timestamp-based intraday ordering, multi-account fragmented transfer, cross-period transfer matching, partial payment allocation, bank source authentication, or automatic IFRS/IAS 7 classification is implied. These require a separately reviewed financial methodology and source adapters.
- **SHA content equality is not proof of external audit, signature, authentic source ownership or financial approval.** The classification mapping is supplied as reference input and may be unapproved, even if internally consistent.

## Typed graph contract

The new allowlisted reference edge is:

```text
HC.CASH.04.cashFlowFromOperations (DECIMAL_MONEY, CURRENCY_AND_PERIOD)
    -> HC.CASH.05.directCfo (DECIMAL_MONEY, CURRENCY_AND_PERIOD)
```

The graph compiler requires identical source/target currency and reporting start/end dates, and the target must use INDIRECT_CFO_RECONCILED. Unqualified cross-model edges remain blocked. This calculation graph is immutable in memory and not a persistent financial audit receipt.

## Redis lifecycle: immutable user architectural mandate

**FEngine only processes ephemeral user data**. Any future distributed runtime may hold submitted facts, intermediate DAG results and delivery state **only in Redis** with an absolute maximum **3 hours (10,800 seconds)**; no sliding TTL. Successful authenticated ACK must atomically revoke/delete all session data immediately. Never write user source payloads/results to PostgreSQL, Redis AOF/RDB, persistent backups, logs, traces or retry payload stores. A Redis ACK/TTL runtime and its integration tests **are not yet implemented**: this wave is synchronous in-process Python calculation. Synthetic golden vectors and static method definitions in Git are not customer session data.

## Qualification and next phases

After this mathematical E2E passes Python 3.11 and Python 3.13 CI, prioritize HC.DCF.06 FCFE basis and HC.COST.08 full PVM decomposition, each with independent numerical examples and method guards. Rust remains deferred. Financial method S2 and source classification admission remain closed.
