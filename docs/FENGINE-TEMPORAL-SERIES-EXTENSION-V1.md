# FEngine Temporal Series Extension V1 — universal opt-in contract

> **Implementation update (2026-11-20):** ModelTemporalCapabilityV1 is now implemented as a **reference-only** declarative registry for nine explicitly admitted outputs across five HC models, with a real HC ReferenceEngine → TASE adapter. See [the implemented admission/acceptance specification](FENGINE-MODEL-TEMPORAL-CAPABILITY-V1-ACCEPTANCE.md). The wider 116-model admission and non-additive reducers remain open; the following original future steps describe that ongoing expansion, not an unimplemented core class.


**2026-11-20** • **main** • One temporal extension for all interval-compatible models; bounded Python/TASE reference, **not financial S2**.

## Architectural rule

Any FEngine model that legitimately uses time-series data must use the **same temporal envelope and calendar/aggregation kernel**, rather than a separate daily/monthly implementation per model. This extension is **optional**: existing scalar calls must remain unchanged. Neither all 116 candidate models nor all 222 candidate variants are automatically admitted by enabling the extension.

### Common request and output

A temporal request shall declare:

- `modelCode`, `variantCode`, authorized `userId/projectId`, source/method revision SHA.
- `startInclusive`, `endExclusive`, `sourceGrain` (DAY, MONTH, AS_OF, EVENT_AT, etc.), `outputGrain` (DAY/MONTH/QUARTER/YEAR, fiscal variants), calendar/timezone profile, `groupBy`, `includeTotal`, `requireFullCoverage`.
- One or more typed input series; each row has date or half-open interval, metric code, dimensions, unit/currency, Decimal value, source revision and missingness/quality state.
- `bucketResults[]` per requested group; `totalResults[]` per group and full selected range; statuses `COMPLETE` / `PARTIAL`, explicit coverage and matching plan/source/calculation SHA.
- Input date range may be years long even though **FEngine's runtime retention is at most 3 hours**.

### Mandatory semantics for every eligible model

| Metric kind | Each time bucket | Grand total over all buckets |
|---|---|---|
| FLOW: revenue, costs, posted cashflow | SUM eligible source facts | SUM **original facts**, not rounded display rows |
| STOCK / AS_OF: balances, debt outstanding | LAST_AS_OF validated snapshot | LAST_AS_OF at requested range end, **not SUM** |
| DERIVED_RATIO: margins, rates from counts | Recompute on aligned numerator/denominator | RATIO_OF_SUMS or qualified components; **not sum/mean of percentages** |
| WEIGHTED_RATE | Match data + weights on exact key/date | Recompute from approved weighted facts |
| NONLINEAR / MODEL_DEPENDENT: IRR, EIR, VaR, ECL, DCF, FCFE PV | Execute model against exact window inputs | **Re-run on full-window atomic facts** when a reviewed temporal contract exists, otherwise **BLOCK** |
| NON_AGGREGATABLE | Window-specific result | **BLOCK** until a qualified contract defines a grand total |

Key guards: source-grain must match actual observation boundaries; no unauthorized splitting of monthly values into days; one half-open period convention; calendar/fiscal rules pinned; no overlap/duplication or cross-project mixing; enforce unit/currency/measurement compatibility and completeness attestations; zero denominator, absent periods, stale stock, unknown model variant and unsupported aggregation fail closed. Both group bucket results and overall totals must be derived from **the same original atomic source**, not one another.

### Working Python reference (bounded TASE pilot)

[`tase/reference.py`](../tase/reference.py) now supports optional `source_grain` and `include_total` on `PeriodRequest` and returns `TaseResult.total_rows` alongside existing `TaseResult.rows`.

```python
req = PeriodRequest(
    product="FIN", metric="REVENUE", operation="SUM",
    scope="authorized-project",
    start=date(2026, 1, 1), end=date(2026, 4, 1),
    source_grain="MONTH",  # DAY works for monthly grouping as well
    grain="MONTH",         # requested output granularity
    include_total=True,    # opt-in, default False
)
result = calculate(catalog, req, dataset)
monthly_rows = result.rows
overall_per_group = result.total_rows
```

- Existing calls with `include_total=False` keep their legacy plan/result fingerprint and output shape; no additional totals are computed.
- If `include_total=True` the source grain is mandatory; unsupported source/output grains are rejected. A product's permitted grains/operators remain enforced.
- Existing TASE candidate catalogue comprises **26 metrics across six product packs**. New interval-compatible HC models/variants will be registered declaratively with a reviewed model-time capability descriptor; they are **not** silently upgraded.
- This Python path does **not** implement an HTTP endpoint, real FIN FactSet adapter, Redis sessions or financial S2.

### Independent numeric acceptance examples

| Data | Per-group values | Overall |
|---|---|---|
| Revenue JAN/FEB/MAR | 100,000 / 120,000 / 80,000 KZT | **300,000 KZT** |
| Daily 1 unit, all Jan + Feb 2026 | JAN 31, FEB 28 | **59** |
| Cash balances JAN/FEB/MAR end | 100 / 300 / 200 | **200**, not 600 |
| Monthly gross margins derived from revenue 100/120/80, profit 20/36/8 | 20% / 30% / 10% | **64/300 = 21.333…%**, not 20% |

Tests: [`tests/test_tase_universal_temporal_extension.py`](../tests/test_tase_universal_temporal_extension.py). They also reject missing buckets, source-grain mismatches, unsupported operators, insufficient attestation, and unknown interval types.

## Universal model admission next steps

1. Add `ModelTemporalCapabilityV1` per model/variant, declaring supported source/output grains, allowed temporal reducer, component lineage, calendar profile, currency/unit and coverage guards. No inference by parameter names or unapproved catalog prose.
2. Bind FIN source FactSets by authorized `user_id` + `project_id`, with exact content SHA and no durable copies in FEngine. Support input-day/output-month plus output-quarter/year where descriptor and product admit them.
3. Add separate method-specific time-window goldens to `HC.CASH.04`, `HC.DCF.06`, `HC.COST.08` before treating their nonadditive model outputs as temporal grand totals.
4. Implement and qualify Redis-only runtime: **absolute 10,800-second maximum TTL**, **immediate atomic delete after successful authenticated consumer ACK**, no sliding expiry or user-data AOF/RDB/backup/log copy.

Legacy TASE R0 references to PostgreSQL calculation storage are superseded. Rust remains postponed.
