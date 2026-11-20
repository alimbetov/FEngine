# FEngine ModelTemporalCapabilityV1.2 — XNPV, weighted CAPM and fixed-baseline PVM

**Date:** 2026-11-20 · **Branch:** `main` · **Execution:** Python/Decimal bounded reference, **NOT financial S2**.

## Architectural result

The same versioned calendar/coverage kernel `TASE` processes the date series and output buckets. A unified entry point `calculate_universal_model_temporal()` resolves a reviewed *model + variant + output field* into its executable time strategy; callers do not select unqualified mathematical reducers. Legacy scalar calls and V1/V1.1 temporal contracts remain unchanged.

**V1.2 introduces five explicitly allowlisted temporal contracts across three existing HC models. No additional HC mathematical model has been implemented in this wave.**

| Model | Variant | Output | Date source | Temporal reducer |
|---|---|---|---|---|
| HC.DCF.02 | EXACT_DATE_XNPV | xnpv | EVENT_AT | DATED_FULL_WINDOW_REEXECUTE |
| HC.CAP.01 | CAPM_BASE | costOfEquity | EVENT_AT | EXPOSURE_WEIGHTED_MODEL_RATE |
| HC.COST.08 | PRICE_VARIANCE | priceVariance | AS_OF | FIXED_BASELINE_LAST_SNAPSHOT |
| HC.COST.08 | QUANTITY_VARIANCE | quantityVariance | AS_OF | FIXED_BASELINE_LAST_SNAPSHOT |
| HC.COST.08 | MIX_VARIANCE | mixVariance | AS_OF | FIXED_BASELINE_LAST_SNAPSHOT |

Current explicit temporal capability ledger:

| Source | Temporal contracts | Distinct model codes |
|---|---:|---|
| V1 | 9 | 5 |
| V1.1 | 4 | 2 (one overlaps V1) |
| V1.2 | 5 | 3 |
| **Unified exact union** | **18** | **9 of 116 HC model codes** |

Note: older V1.1 prose incorrectly described 13 contracts as seven distinct models; the exact V1+V1.1 union is **6** model codes. V1.2 extends that union to **9**. These are **reference temporal capability counts**, not production finance approvals. The HC executable mathematical model count stays **27/116**.

Code: [capability registry](../catalog/model_temporal_capabilities_v12.tsv), [V1.2 executor](../tase/model_temporal_v12.py), [unified dispatcher](../tase/temporal_dispatch.py), [tests](../tests/test_model_temporal_capability_v12.py), [independent JSON goldens](../tests/golden/model_temporal_v12_reference_vectors.json), [portable golden runner](../tests/test_model_temporal_v12_portable_golden.py).

## 1. Dated XNPV — actual dates, annual ACT/365 fixed rate

Only `HC.DCF.02 EXACT_DATE_XNPV` is admitted. `APPROVED_DAYCOUNT_XNPV` is not claimed, since that mathematical variant has not been executed/qualified.

Every atomic event has a real ISO date, distinct source event ID, source revision hash, one cashflow amount and the fixed `valuationDate = request.startInclusive`. Currency is bound by the run envelope. Exactly one **effective annual** discount rate is allowed for the entire selected series, including when `include_total=False`. The only accepted day-count convention is `ACT_365_FIXED`.

- For each DAY/MONTH/QUARTER/YEAR output bucket, the real HC XNPV model is called on that bucket's original dated cashflows, **using the same global valuation origin**.
- For the full-range total, the real HC XNPV model is called again on all original dated cashflows over the requested range; it does **not** add independently valued local-origin bucket outputs.
- TASE validates event dates, month/quarter boundaries, unique event identities, completeness/watermark, group isolation and resource budget.

Synthetic cashflows:

| Date | Amount |
|---|---:|
| 2026-01-01 | -100 |
| 2026-02-01 | +110 |
| 2026-03-15 | +200 |

At a 10% annual effective rate, the full-period XNPV reference is **205.33686130106055979543684209776897423253…**. No false monthly rate conversion, 30-day-month approximation or ACT/360 substitution is permitted. Timezone-specific intraday cashflow timestamps and FX conversion are not admitted.

**Zero-event periods:** The current TASE `SUM` reference rejects empty buckets rather than inferring zero. For a trusted, complete event stream this may eventually be treated as a verified zero, but no such conversion is admitted in this wave. The caller must not invent rows.

## 2. CAPM rate — explicit exposure-weighted mean

Each source event is an actual `HC.CAP.01 CAPM_BASE` execution:

```text
costOfEquity = riskFreeRate + beta * marketRiskPremium
exposureWeightedRate = sum(costOfEquity_i * exposureWeight_i) / sum(exposureWeight_i)
```

The source weight must be an explicit nonnegative Decimal exposure in the request currency. TASE matches rate+exposure by canonical **(date, group)** atomic key, and rejects repeated rate entries on the same date/group, missing weights, negative weights and zero aggregate weight. Across a comparable dimension group, the reference requires the **same riskFreeRate and marketRiskPremium** for the selected series; beta may vary.

Synthetic example: betas 1 / 2 / 1.5, risk-free 2%, premium 6%, giving rates **8% / 14% / 11%**; exposures **100 / 300 / 100** yield a weighted full-range rate of **12.2%**, not the arithmetic 11%.

**Methodological boundary:** This is a discrete **exposure-event-weighted statistic**, not a time-duration-weighted rate, bond yield, stock valuation or regulatory capital requirement. Repeated exposure positions on different dates contribute again; a different financial methodology and source evidence would be required for time-weighted account balances. A caller's weights and completeness flag are not qualified FIN sources.

## 3. PVM — last fixed-baseline comparison, never sum of cumulative changes

All three real `HC.COST.08` variants are admitted separately. Every AS_OF snapshot is the original HC PVM executor run with the exact **same immutable baseline period, baseline quantity/cost SHA, standard cost vintage, volume baseline SHA, currency and physical quantity unit** within each dimension leaf.

- Each period's value is the selected factor from that snapshot's full three-factor decomposition.
- The overall result is the **last comparable snapshot's** factor over the requested date range, comparing the final actuals with the same baseline. It is not SUM of month-end deltas.
- New SKUs without reviewed baseline, changed baselines, inconsistent currency/unit or stale/missing snapshot fail closed through the existing HC and TASE validation.
- All three factors remain available from the original HC model's returned output, but the temporal request selects **one explicitly allowed field**.

Synthetic controls with a fixed 2025-12-31 baseline:

| Selected variance | Jan 2026 | Feb 2026 | Mar 2026 | Full-range result |
|---|---:|---:|---:|---:|
| PRICE_VARIANCE | -70 | -85 | -10 | **-10** |
| QUANTITY_VARIANCE | +140 | +280 | +420 | **+420** |
| MIX_VARIANCE | +160 | +170 | +180 | **+180** |

These are baseline-to-snapshot comparisons, **not monthly incremental PVM results**. Their full-range factors on the March snapshot reconcile to the change from the agreed 2025 baseline to March actuals; do not report them as a sum of January, February and March variances.

## API and source evidence

~~~python
from tase import (
    UnifiedModelTemporalRegistry, ModelTemporalRequest,
    ModelTemporalRunV12, temporal_v12_source_sha256,
    calculate_universal_model_temporal,
)
registry = UnifiedModelTemporalRegistry.load(root, reference_mode=True)
result = calculate_universal_model_temporal(
    registry, request, model_runs, reference_mode=True
)
buckets = result.result.rows
totals = result.result.total_rows
~~~

`ModelTemporalRunV12` binds date, model/variant-specific inputs, configuration, event ID, currency, dimensions, optional exposure weight, and SHA of the exact immutable event. The batch SHA includes all executed input/config/output receipt SHA values, source completeness assertion and watermark; a change to the source or coverage claim changes the fingerprint.

**Source SHA equality is not external signature verification or financial S2.** Before real FIN integration, authentication must bind `user_id`/`project_id` to authorized signed and complete fact revisions. There is no real FIN adapter or authenticated source attestation here. The code operates synchronously in memory and does not persist customer facts.

## Security, retention and follow-up

- **Redis only**, absolute maximum calculation-session lifetime **10,800 seconds (3 h)**, never renewed by reads or retries; successful authenticated FIN ACK must **atomically delete all session keys immediately**.
- Redis RDB/AOF backups, persistent job payloads, PostgreSQL calculations, customer facts in logs/traces and durable retry payloads remain disallowed. **Redis runtime / ACK implementation and its integration tests remain OPEN**. This module does not provide them.
- Rust remains deferred. Python-reference golden parity and reference regression on 3.11/3.13 precede any change of implementation language.
- Financial S2 remains CLOSED. Full temporal support for every 116-model candidate is not claimed.
- Further work: trusted input/coverage envelopes, zero-event-but-complete policy, dated XNPV irregular-intraday time support, method-approved duration-weighted rates, PVM new-SKU/period-baseline policies, Redis ACK/expiry correctness tests.

## Acceptance

Tests cover real model invocation, numeric independent goldens, duplicate/different-day atomic keys, signed source revision changes, exact date origins and daycount, group isolation, missing periods, zero weights, drift in rate/baseline/quantity unit, no unauthorized variants, disabled S2 and deterministic result SHA across run permutations.

`python -m unittest discover -s tests -v` on Python 3.11 and 3.13. CI acceptance is valid only on the final HEAD.
