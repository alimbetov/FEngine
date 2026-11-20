# FEngine ModelTemporalCapabilityV1.1 — nonadditive temporal reducers

**Implementation date:** 2026-11-20  
**Branch:** main only  
**Admission:** bounded Python reference, **NOT FINANCIAL S2**; production source authentication and Redis session runtime are **not implemented**.

## Architectural change

The first temporal adapter (V1) correctly computes SUM for additive flows and LAST_AS_OF for stocks, but **must never add or average ratios, discounted valuations, forecasts, IRR or other nonlinear output cells**. V1.1 extends the *same TASE calendar and source validation kernel* through two independent, explicitly registered reducers:

| Reducer | Model and method | Window computation | Full-range computation |
|---|---|---|---|
| RECOMPUTE_FROM_COMPONENTS | HC.COST.07 EVM_BAC_CPI and EVM_EAC_FORECAST, output costPerformanceIndex | Latest aligned earnedValue / actualCost from dated source snapshot | Latest compatible EV / AC, not average of period CPI |
| RE_EXECUTE_FULL_WINDOW | HC.DCF.01 PERIOD_END_NPV and MIDPERIOD_NPV, output npv | Re-execute real HC model using exactly the window's ordered source cashflows | Re-execute real HC model once using **all** ordered cashflows from the selected range |

An arbitrary HC model variant may not select these reducers from a caller request. [ModelTemporalCapabilityV1.1 catalogue](../catalog/model_temporal_capabilities_v11.tsv) has four specific, content-SHA-pinned declarations; the loader cross-checks the 116/222 existing HC model/variant catalogue and an explicit reviewed method-policy allowlist.

[Python reference](../tase/model_temporal_v11.py), [unified dispatcher](../tase/temporal_dispatch.py), [new E2E tests](../tests/test_model_temporal_capability_v11.py), [portable goldens](../tests/golden/model_temporal_v11_reference_vectors.json), [golden runner](../tests/test_model_temporal_v11_portable_golden.py), [unified API tests](../tests/test_unified_temporal_dispatch.py).

## One public API for V1 and V1.1

~~~python
from pathlib import Path
from tase import (
    UnifiedModelTemporalRegistry, ModelTemporalRequest,
    ModelTemporalRun, ModelTemporalRunV11,
    calculate_universal_model_temporal,
)
registry = UnifiedModelTemporalRegistry.load(Path("."), reference_mode=True)
result = calculate_universal_model_temporal(
    registry, request, model_runs, reference_mode=True
)
buckets = result.result.rows
grand_totals = result.result.total_rows
~~~

The unified registry dispatches **only on model+variant+output field from reviewed declarations**, never on output name heuristics, data type alone or client-supplied operation codes. V1 runs use ModelTemporalRun; V1.1 runs use ModelTemporalRunV11 with explicit currency and content-bound source SHA. Input types cannot cross strategies.

Current mathematical reference capability coverage after V1.1:

| Registry | Explicit bindings | Model codes |
|---|---:|---|
| V1 SUM/LAST_AS_OF | 9 | HC.CASH.04, HC.CASH.05, HC.DCF.05, HC.DCF.06, HC.COST.07 |
| V1.1 component recompute / full-window reexecute | 4 | HC.COST.07, HC.DCF.01 |
| **Combined** | **13** | **7 distinct model codes of 116** |

The total of 27 previously implemented Python-reference model codes is unchanged; new support is temporal execution/admission only. A further 109 HC model codes do not yet have reviewed declarations. Non-admitted nonlinear or output fields fail closed.

## EVM CPI — components, not average ratios

Synthetic dated EVM snapshots:

| Snapshot | Earned Value | Actual Cost | CPI |
|---|---:|---:|---:|
| Jan 31 | 60 | 75 | 0.8 |
| Feb 28 | 80 | 80 | 1.0 |
| Mar 31 | 100 | 200 | 0.5 |

**Full Jan–Mar CPI = 100 / 200 = 0.5**. Naively averaging 0.8, 1.0 and 0.5 gives 0.7666… and is incorrect.

Each EVM model is actually executed and its CPI is checked against its raw EV/AC inputs. The two input components are then passed to TASE's existing LAST_AS_OF calculation for each bucket and for the entire selected range. Exact dimensions, date, currency, a consistent baseline revision, absence of zero denominator and freshness limits are mandatory. Different model variants use the same CPI formula, although their independent EAC forecast formulas differ. This does **not** establish financial eligibility of reported EV or AC or an externally signed baseline.

No SUM of cumulative earned value, actual cost or CPI across snapshot dates is allowed.

## NPV — real full-window model execution

Reference example uses one monthly cashflow per source period and an **effective monthly discount rate**, not an annual rate silently reused each month.

| Month | Source cashflow | NPV when considered alone from its own first step |
|---|---:|---:|
| Jan | −100 | −100 |
| Feb | +121 | +121 |
| Mar | +121 | +121 |

For PERIOD_END_NPV, the full-window result is

```text
-100 + 121/(1.10)^1 + 121/(1.10)^2 = 110
```

The sum of the three *standalone monthly model results* would instead be **142** and must not be presented as the full NPV. For MIDPERIOD_NPV, the existing HC model's reference timing convention applies and gives **120.249858115731824868205237872786895679807090…** for this same input example.

The source granularity is explicitly **MONTH** with exact calendar-month start/end, one cashflow per source month and identical rate/method configuration across the full selected series, **even when include_total=False**. The effective rate is supplied *per source month* and never automatically converted from annual WACC/Ke; no day-count interpolation is implemented. Each calendar bucket resets NPV to that bucket's first cashflow as time zero, whereas the grand total restarts the model once at the complete range's first cashflow. This is a declared reference convention, **not a generally qualified dated DCF methodology**. For dated irregular cashflows use a separately approved XNPV temporal contract; no implicit reinterpretation is permitted.

TASE alone validates aligned source months, contiguous periods, duplicate/overlapping observations, required attestation/watermark, output calendars, group isolation and resource bounds. V1.1 calls the actual HC reference executable with the selected cashflow series; it never returns TASE's additive input-flow validation SUM as the NPV answer.

## Source revisions, financial qualification and operational limits

- Every run's source snapshot SHA includes model, variant, explicit source-unit currency, date interval, numeric model inputs, configuration and dimensions. Batch/plan/result SHAs bind sorted run evidence, the temporal capability SHA, current engine revision and final TASE outputs. Reordering the same runs does not change result fingerprint.
- **Self-consistent SHA is not authorization or signed financial provenance.** FIN must independently supply authorized, complete, immutable and qualified FactSet revisions tied to user_id/project_id before financial admission. Declaring a complete dataset in a client request does not authenticate it.
- Source/target time zones, month-end business cutoffs, fiscal calendars, partial-period discounting, multi-currency FX, date-precise XNPV, cumulative-stock-to-flow conversion, and complex model-specific assumptions are not implicitly inferred.
- V1.1 is **in-process only**, no HTTP or FIN connector. User-submitted financial facts, intermediate model runs and results must have **Redis-only, absolute max 10,800-second TTL** in a future distributed runtime. After authenticated successful consumer ACK, all calculation session keys must be **atomically invalidated and deleted immediately**; reads and retries cannot extend TTL. No PostgreSQL copies, user-data AOF/RDB/backups, logs or durable retry payloads.
- The Redis runtime, ACK/purge integration tests, S2 decisions, signed FIN source adapters, Rust parity, financial production admission and full 116-model temporal contracts remain **not implemented**.

## Regression and next step

Run on Python 3.11 and 3.13:

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions results must be checked at the **exact final HEAD**. Follow-up: define temporal capabilities for more explicit HC model fields (especially dated XNPV, weighted metrics and price/volume/mix), support strongly authenticated financial input revision envelopes, and test Redis ACK lifecycle separately. Do not expand HC model count by relabeling a catalogue entry as executable.
