# FEngine — ModelTemporalCapabilityV1 technical acceptance and reference contract

**Date:** 2026-11-20  
**Branch:** main  
**Status:** implemented bounded Python reference; **NOT FINANCIAL S2**, **NOT distributed production runtime**.

## Decision

All HC/FEngine models which support time-bounded facts use **one shared TASE time bucketing and aggregation engine**. Per-model calendars, separately coded monthly/quarterly sums, and ad-hoc "total all outputs" are forbidden. The original scalar method call remains available.

The extension **does not automatically admit all 116 HC models**. Model/variant/output eligibility is an explicit, revisioned, catalog-backed declaration. Output semantics determine which aggregate can be computed. Financial S2 is a separate decision.

### Implemented files

- [Nine explicit model+variant+output temporal capability bindings](../catalog/model_temporal_capabilities_v1.tsv).
- [Typed immutable capability and generic HC-to-TASE execution adapter](../tase/model_temporal.py).
- [TASE common interval/aggregation/quality kernel](../tase/reference.py).
- [Direct model-run integration, deliberate denial and semantic negative tests](../tests/test_model_temporal_capability_v1.py).
- [TASE universal interval tests](../tests/test_tase_universal_temporal_extension.py).

## Reference capability truth table

| HC model | Variant(s) | Selected output | Temporal semantics | Full-range total |
|---|---|---|---|---|
| HC.CASH.04 | DIRECT_POSTED_CFO; DIRECT_RECLASSIFIED_CFO | cashFlowFromOperations | FLOW, interval | SUM of separately executed posted-period CFO |
| HC.CASH.05 | INDIRECT_CFO_ADJUSTMENT; INDIRECT_CFO_RECONCILED | cashFlowFromOperations | FLOW, interval | SUM of independently calculated periodic CFO |
| HC.DCF.05 | FCFF_UNLEVERED | freeCashFlowToFirm | FLOW, interval | SUM, if sourced facts are genuinely period-bounded |
| HC.DCF.06 | FCFE_LEVERED; FCFE_NORMALIZED | freeCashFlowToEquity | FLOW, interval | SUM of **undiscounted FCFE**; NEVER add separately discounted presentValueOfFcfe |
| HC.COST.07 | EVM_BAC_CPI; EVM_EAC_FORECAST | estimateAtCompletion | AS_OF snapshot | LAST_AS_OF; never sum EAC estimates |

**9 distinct variant/output entries across 5 model codes**, all reference-only. All other variants, output fields, currency conversion, and unqualified models return `TEMPORAL_CAPABILITY_NOT_ADMITTED`. The other **111/116 HC models** do not yet have this temporal descriptor. That does NOT imply those models are not mathematical executors: 27 HC model codes have bounded Python reference calculations, of which 5 are covered by this temporal adapter.

Neither EVM CPI nor derived ratios should be averaged over months from already-computed ratio cells. Ratio-of-sums must operate on independently eligible aligned components (EV, AC, revenues, counts) with explicit time semantics. PVM requires a consistent baseline and price/cost vintage, so generic SUM is disallowed. NPV, XNPV, IRR and other nonlinear outputs require re-execution on full-window facts under a method-specific reviewed contract, not summation.

### Temporal contract

`ModelTemporalCapabilityV1` binds:

- modelCode + variantCode + **exact outputField** (never a generic model-wide enable flag);
- quantityKind/timeKind/temporalReducer;
- allowedSourceGrains and allowedOutputGrains;
- periodBinding to actual model input date(s);
- continuityRule and currency unit kind;
- reviewStatus and a deterministic capability SHA-256.

`ModelTemporalRegistry.load(root, reference_mode=True)` rejects unknown HC variants, mismatched reducers, invalid calendars, unsupported continuity policies, duplicate entries, unreviewed status, and missing fields. It validates model and variant identities against the existing 116/222 catalogue. A new compatible HC output can be added through a **reviewed declarative row** rather than an additional calendar kernel, but mathematical output and period applicability still need verified tests before admission. A descriptor SHA is a content identity, **not** an independent financial S2 signature.

### Input/output API — implemented Python reference

~~~python
from datetime import date
from pathlib import Path
from tase import (
    ModelTemporalRegistry, ModelTemporalRequest, ModelTemporalRun,
    calculate_model_temporal,
)

registry = ModelTemporalRegistry.load(Path("."), reference_mode=True)

request = ModelTemporalRequest(
    model_code="HC.CASH.05",
    variant_code="INDIRECT_CFO_ADJUSTMENT",
    output_field="cashFlowFromOperations",
    scope="authorized-user:authorized-project",
    start=date(2026, 1, 1),
    end=date(2026, 4, 1),             # exclusive
    source_grain="MONTH",
    output_grain="MONTH",
    currency="KZT",
    include_total=True,
    coverage_attested=True,         # ONLY by a trusted source adapter
    watermark=date(2026, 4, 1),
)
# ModelTemporalRun requires start, endExclusive (or None for snapshots),
# the real ReferenceEngine inputs and config, the matching source revision SHA,
# and optional stable dimension keys.
# model_runs = [ModelTemporalRun(...), ...]
response = calculate_model_temporal(
    registry, request, model_runs, reference_mode=True
)
monthly_rows = response.result.rows
overall_by_group = response.result.total_rows
~~~

**This is not an HTTP endpoint.** The FIN `user_id / project_id` FactSet adapter is not implemented and must enforce ownership/authorization and source completeness independently; a caller-supplied `scope` or `coverage_attested=True` is not authentication. Read-only source SHA and output SHA do not establish source trust. Both `ModelTemporalRun` source and metric executor inputs remain ephemeral within this synchronous reference call.

### Per-run execution and model/time proof

1. Check capability admission and requested source/output grains. Build a typed TASE metric descriptor with the selected output and currency, no wildcard operation.
2. Verify model-run source revision equality and explicit period binding to the input model (e.g. direct posted CFO uses inclusive `periodEnd = endExclusive−1 day`; indirect CFO uses `asOf = endExclusive−1 day` and `periodStart = startInclusive`).
3. For FCFF/FCFE models exposing only `asOf` without an input start boundary, **require explicit coverage attestation**; real authorized FIN source-interval proof is pending and production admission is blocked.
4. Run the *actual* reviewed-bounded `ReferenceEngine.calculate(...)` for every source interval, validate its selected output numeric type and currency, and build a typed observation with source/result SHAs.
5. For direct posted CFO, require previous period closingCash to equal next period openingCash within each dimension leaf. For EVM AS_OF, require a stable baseline revision across the same comparable time series.
6. Let existing TASE detect missing/overlapping intervals, duplicate observations, incorrect source grain, missing coverage watermark, stale snapshots, incompatible types/currencies and unauthorized operators.
7. Compute each output bucket and, when requested, a full-range semantic total from the **same atomic model-executed observations**, rather than adding monthly ratios or balances.
8. Fingerprint capability, source batch, model execution inputs/config/results, typed TASE plan, and response separately; return the full planned/result SHA evidence without copying input facts to any database.

## Synthetic accepted examples

- HC.CASH.05 monthly net CFO **100, 120, 80 → 300**; grouping MONTH or output QUARTER uses the same interpreter.
- HC.DCF.05 monthly FCFF 110, 110, 110 → 330, retaining Decimal scale.
- HC.DCF.06 monthly undiscounted FCFE 85, 85, 85 → 255; presentValueOfFcfe cannot be passed as additive field.
- HC.CASH.04 three real month-end posted ledger computations with matching cash opening/closing, **120 + 100 + 70 = 290**; a cash balance discontinuity fails.
- HC.COST.07 dated monthly estimates at completion **150, 120, 120 → last AS_OF 120** (never 390). Baseline changes invalidate cross-period comparability.
- Two branches' monthly CFO computations are returned as two separate full-range totals. Missing months block a supposed complete total.
- Deliberately forged source SHA, altered dates, currency mismatch, unregistered method, unsafe reducer, unauthorized source grain, and omitted coverage attestation are rejected.

These are **synthetic mathematical control examples**, not FIN source financial qualification.

## Architectural constraints retained

1. All temporal-capable HC methods share the *same* versioned calendar, period grouping, dimensional and completeness engine; adding model-specific duplicate calendar logic is not allowed.
2. Full model-level totals require a semantically valid method. SUM is never inferred from an output's numeric type or name.
3. The read model only admits reference-mode execution; financial S2 and any production admission remain closed pending independent review, signed FactSet/source authority and operational gates.
4. **User calculation inputs, intermediate state, plans, results, receipts and series may live in FEngine only as Redis-ephemeral session data, absolute maximum 10,800 seconds, no sliding renewal. An authenticated, idempotent successful consumer ACK requires immediate atomic deletion of the complete session.** Never persist customer values to PostgreSQL, Redis RDB/AOF backups, logs or durable queue payloads.
5. The current code implements **no Redis session, TTL/ACK protocol, distributed worker, external API or FIN data adapter**. Python only holds in-process transient values and has no persistence calls.
6. Rust stays postponed until Python temporal/financial semantic reference closure and separately verified portable parity vectors.

## Next technical gates

- Expand ModelTemporalCapabilityV1 to compatible other HC models with **explicit temporal input proof**, not merely output field name matching.
- Strengthen typed model-specific model input period evidence for methods with only asOf date and source-revision SHA.
- Add RECOMPUTE_FROM_COMPONENTS and RE_EXECUTE_FULL_WINDOW adapters with independent golden controls; do not admit them through SUM.
- Integrate FIN scope authorization and complete source FactSet retrieval without durable FEngine copies.
- Implement and test Redis hard TTL (max three hours), ACK atomic consume/delete, network failures and repeat delivery.

**Reference testing command:** `python -m unittest discover -s tests -v` (Python 3.11 and 3.13). Current GitHub Actions status must be checked against exact HEAD before acceptance.
