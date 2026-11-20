# FEngine TASE — аудит полноты моделей/параметров и Python reference implementation

**Date:** 2026-11-20  
**Branch:** main  
**Status:** PYTHON_REFERENCE_PARTIAL / NOT_FINANCE_S2 / NO_RUST / CONTRACT_FREEZE_HOLD

## 1. Coverage and qualification matrix

| Area | Total | Verified in this phase | Not qualified yet |
|---|---:|---|---|
| HC model candidates | 116 | 116 unique model codes indexed across W1–W5 | 116 financial executors do not exist |
| HC parameter occurrences | 417 | 310 R95 + 107 W5, every model covered | 417 domain reviews PENDING; 399 requiredness reviews PENDING |
| TASE candidate operators | 53 | 13 implemented in Python reference | 40 remain explicitly NOT_IMPLEMENTED |
| TASE typed input predicates | 21 | registered and checked against 53 operator declarations | formal cross-language IDL/approval still draft |
| Product Packs | 6 | declarative FIN, BANK, INSURANCE, LOGISTICS, INDUSTRY, CUSTOM | all DRAFT/unsigned; reference_mode only |
| Example metric descriptors | 26 | 26 referentially valid candidates | 116 HC output-to-TASE semantics not yet mapped |
| Metric/operator bindings | 62 | all 62 checked at catalogue load | finance/product admission incomplete |
| TASE core parameter candidates | 32 | named, typed and status-classified | 10 future-only; no immutable admission |
| Seed acceptance scenarios | 42 | 42 requirements drafted | not equal to 42 passing runtime tests |

Exact repositories:
- catalog/model_parameter_inventory_116_r0.tsv
- catalog/tase_core_parameter_candidates_r0.tsv
- catalog/tase_operator_candidates_r0.tsv
- catalog/tase_input_predicates_r0.tsv
- catalog/tase_product_pack_candidates_r0.tsv
- catalog/tase_metric_semantics_candidates_r0.tsv
- catalog/tase_golden_and_negative_candidates_r0.tsv

**Resolved catalogue defects:** 19 permissions mismatches across six pack candidates were corrected by 16 missing entries; FIN.REVENUE variance was added after a failing unit test; 4 remaining type incompatibilities for industrial time-covered flow SUM/ROLLING_SUM were corrected by extending input predicates. The Python catalog now checks every single registered operator binding before processing requests.

## 2. Implemented Python functionality (real code)

- tase/reference.py, tase/__init__.py and tests/test_tase_*.py, Python >=3.11, only standard library.
- Live operators: SUM, LAST_AS_OF, ARITH_MEAN, WEIGHTED_MEAN, VAR_POP, VAR_SAMPLE, STDDEV_POP, STDDEV_SAMPLE, RMS, MIN, MAX, RATIO_OF_SUMS, QUANTILE_EXACT (nearest rank).
- Decimal rejects silent float input; missing/null is distinct from zero; non-finite values blocked; strict product/operator/type admission.
- Monthly/quarterly/half-year/year Gregorian and Gregorian fiscal start-month calendar, day/ISO week; custom 4-4-5 and timezone/DST not yet supported.
- Flow completeness requires synthetic source interval attestation, watermark not earlier than interval end, gap-free/non-overlapping leaf series; absent evidence BLOCKED COVERAGE_UNKNOWN. Event stream requires own complete watermark evidence. Production-grade verification of source authority is NOT available.
- STOCK uses last qualifying per-leaf as-of value and staleness policy, not sum of dated snapshots.
- Correct derived numerator/denominator ratio with money currency or physical unit algebra, rate weighted by exact dimension/date-matched exposure.
- Scoped, deterministic plan and result digests. These are Python in-memory reference hashes, NOT PostgreSQL durable result receipts.
- Declarative Product Pack extension tested by registering EXPERIMENT + NET_FLOW without changing Python core. Unsigned Product Packs rejected outside explicit reference_mode.

## 3. CI evidence and how to interpret it

On main commit 1946c09cdba292d036d358deb9488f627c90e90e:
- GitHub Actions reference suite: 129/129 unittest methods PASS on Python 3.11 and 129/129 PASS on Python 3.13 (GEO-OPT + TASE + existing tests).
- GitHub Actions separate contract bank: success on Python 3.11 and 3.13.
- Reference CI run: https://github.com/alimbetov/FEngine/actions/runs/44720599167
- Contract bank run: https://github.com/alimbetov/FEngine/actions/runs/44720599121

Do not infer 116 financial implementations, 53 real TASE operators, 250 R0.6 cases, production-readiness or financial S2 from the CI runs above. Tests check a specifically implemented, bounded in-process mathematical reference.

## 4. Blocking gaps and action priorities

**P0 before contract freeze:**
1. Complete 417 parameter domains, requiredness, allowed values, min/max, defaults, version/effective date and S2 for regulated models.
2. Map qualified HC model outputs and source FactSets to TASE MetricSemanticDescriptors; 26 current descriptors are illustrative.
3. Verify authoritative signed source manifest, interval coverage, watermark, permissions and content SHA. Reference-supplied metadata is not sufficient for production.
4. Sign/version Product Packs and bind issuer namespace, tenant ABAC, financial basis, exact calendar and source authorization.
5. Formalize Decimal precision, scale, rounding stage, quantile definition, target units, snapshot staleness and approval in immutable NumericPolicy/MethodParameterContract.
6. Implement multi-N metric operation DAG and qualified data reuse; present reference request is intentionally single metric/operation.
7. Add remaining 40 TASE operators only with independent positive/negative/edge goldens and typed value-state semantics.
8. Connect to actual PostgreSQL durable Inbox/Lease/Fencing/ResultSet/Outbox, archive acknowledgement and crash recovery.

**P1 after semantics:**
- Fiscal 4-4-5/4-5-4/5-4-4, week 53, DST/instant/timezone, historical dimension graph, multi-parent and joins.
- Exact quantile variants, median/MAD, covariance, streaming merge variance, plan-versus-actual, MoM/QoQ/YoY and large-window operators.
- Query/quantity cardinality limits and performance benchmark across 10k/100k/1m rows under stated hardware.

## 5. Planned Python → tests → Rust sequence

1. **Python reference first:** TASE-PY-R0.1 explicit semantic compiler/reference done in bounded form. Finish comprehensive contracts, calendar, statistics and comparison modules while maintaining strict fail-closed behavior.
2. **Tests before optimization:** complete 42 seed cases and the planned >=250 TASE acceptance bank; property based split/merge, input malformation, tenant security and failure recovery. Qualify math and finance applicability independently.
3. **Performance baseline:** profile full path with exact source, group cardinality, input normalization, aggregation, serialization, durable archive, p95/p99, memory, CPU and error rate. Compare Python Decimal, PostgreSQL set operations and candidate columnar engines on same immutable data.
4. **Rust only for proven hotspots:** keep shared Python orchestration/control plane unless benchmarks justify otherwise; build Rust aggregation modules with exact decimal semantic parity and consistent result status/units/rounding. No float substitution for MONEY.
5. **Shadow parity gate:** identical canonical input/parameter hashes, outputs, statuses, rejection reasons and resource limits in Python/Rust. Only approved statistical approximate paths can use a separately specified tolerance. Rust production admission requires faster measured full-path performance plus parity, not faster isolated loops.

**Decision:** proceed with Python-first incremental development; do not freeze 116 business methods or move all of FEngine to Rust now. Current Product Packs and models remain unqualified drafts until the separate review gates are passed.
