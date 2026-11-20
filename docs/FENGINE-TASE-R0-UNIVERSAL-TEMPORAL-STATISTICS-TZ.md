# FEngine TASE-R0 — Universal Temporal Aggregation & Statistical Scope Engine

**Документ:** FENGINE-TASE-R0-TZ-V1, 2026-11-20
**Репозиторий:** alimbetov/FEngine, main
**Статус:** DESIGN / REQUIREMENTS_DRAFT / NOT_IMPLEMENTED / CONTRACT_FREEZE_BLOCKED
**Существующая база:** FENGINE_MASTER_SPEC.md v0.11, InputBatchDTO, CalculationSession, CalcPlan, CalculationResponseDTO, MethodParameterContractV2. 116 кандидатов финансово-экономических моделей и логические D01–D114 остаются неизменными.
**Смысл TASE:** универсальный слой, а не 117-я предметная модель и не микросервис для каждой функции.

## 0. Цель, архитектурное решение и границы

В одну неизменяемую CalculationSession поступают N типизированных временных рядов с интервалами, ключами бизнес-объектов, валютами, единицами измерения, источниками и статусами наблюдений. Пользователь выбирает разрешённый продукт/Scope, показателей, временных гранулярностей, группировок, статистических операций и сравниваемых баз. TASE компилирует допустимый DAG и возвращает значения, статистики, отклонения, статус полноты, качество, lineage, исходные и методические SHA.

**Архитектура:**
- Product Pack Registry — подписанные декларативные плагины предметных областей;
- Metric Semantic Registry — трактовка FLOW/STOCK/RATE/derived ratio, единиц, и допустимых операций;
- Calendar & Interval Bucketing — exact calendar/fiscal intervals and coverage;
- Dimension & Scope Resolver — tenant/project/business hierarchy and security, grouping, dedup;
- Operator Registry & Algebra — typed shared aggregate/statistics operations;
- Stats/Comparisons Planner — planned computation DAG and reusable partial states;
- Calculation Hub Adapter — immutable input/session/job/outbox/archive; no second control plane.

~~~text
Product Pack (FIN/BANK/INS/LOGISTICS/INDUSTRY/CUSTOM)
        ↓ resolves only allowed semantics, calendars and operators
Typed InputBatchDTO → Immutable DatasetManifest → CalculationSession
        ↓
Semantic + Unit + ACL Validation → Calendar Buckets → Group/Statistic DAG
        ↓                                  ↓
Exact Decimal aggregates           Qualified statistical kernels
        └───────────────┬──────────────────┘
                        ↓
Typed CalculationResponseDTO.results[] + Quality + Source Lineage
                        ↓
Durable ResultSet + PostgreSQL Outbox → Archive ACK → bounded cache cleanup
~~~

TASE is not the engine for accounting recognition, IFRS ECL/17, statutory KZ capital norms, hedge accounting, or prospective ML forecasts. It may consume qualified results of those methods as pinned immutable inputs.

## 1. Расширяемость по продуктам — ProductPackContractV1

### 1.1. Правила архитектуры

Product Packs do not fork/duplicate mathematical kernels. A pack supplies:
1. productCode / issuerNamespace / immutable revision / signed artifact manifest;
2. allowed metric definitions and semantics;
3. dimension definitions, source adapters and attribution policy;
4. calendar options, default reporting periods, currency and accounting basis;
5. allowed operator IDs and parameter envelopes, applicability of preset profiles;
6. scope/ABAC policy, source authority, cross-tenant prohibition;
7. optional reviewed methodology bindings and coverage thresholds;
8. quotas: cardinality, bucket count, operations, number of output cells;
9. algorithm and contract compatibility requirements and review evidence.

Customer-pack data is declarative. No untrusted user Python, dynamic SQL, code expressions or runtime-loaded arbitrary algorithms. New kernels require separate developer-owned OperatorDescriptor with artifactSha, typed inputs/outputs, numerical semantics and independent review. Product pack revisions are immutable; every CalculationPlan binds exact pack/source/calendar/numeric/operator SHA. Installation/revocation affects admission of new executions, not historical signed finished results.

### 1.2. ProductPackManifest fields

| Field | Type | Contract rule |
|---|---|---|
| productCode, namespace, productClass | CODE | stable namespace and no collision with TASE core |
| productPackRevision, effectiveSha256 | REFERENCE/HASH | immutable, signed and reviewed |
| signingKeyRef, signature, admissionStatus | REFERENCE/STRING/ENUM | unsigned/revoked pack blocked |
| metricDescriptors[], dimensionDescriptors[] | typed LIST | allowlisted types, unique codes |
| sourceBindings[], adapterRevisionRefs[] | typed LIST/REF | exact field origin with tenant permission |
| allowedOperatorIds[], allowedGrains[] | LIST<CODE> | cannot enable unsupported or unsafe math |
| calendarProfileRefs[], currencyPolicies[] | LIST<REF> | period and quote convention pinned |
| profileDescriptors[] | typed LIST | BASIC, FINANCIAL, EXTENDED_STATS, FORECAST_ACCURACY |
| applicability | STRUCT | entity, sector, accounting basis, jurisdiction, product class |
| requiredReviewRefs, qualityPolicies[] | REFERENCE/LIST | independent financial/actuarial approval remains separate |
| quotaPolicyRef, ACLPolicyRef | REFERENCE | no privilege escalation |
| dependencyPacks[] | LIST<REF> | immutable dependency DAG, no cycles |

### 1.3. Initial product candidates (not implemented)

| Product | Indicative metrics | Shared TASE behavior | Method-specific guard |
|---|---|---|---|
| FIN | revenue, cash balance, profit margin, DSO | SUM flow, LAST_AS_OF stock, RATIO_OF_SUMS | identical scope/currency/basis |
| BANK | principal balance, interest flow, ECL, PD | STOCK, FLOW, derived risk outputs | stage/horizon/PD semantic and S2 |
| INSURANCE | earned premium, claims, combined ratio, reserve | FLOW, STOCK, ratio recompute | IFRS17 != management underwriting |
| LOGISTICS | kilometers, fuel liters, on-time deliveries | SUM, ratio of counts, cost per km | matching journeys and transfer semantics |
| INDUSTRY | kWh, units manufactured, OEE | sums plus recomputed ratios | production hours and component consistency |
| CUSTOM | user-defined metrics | only validated typed profile | no free-form math, explicit source authorization |

**Compatibility:** an identical symbolic operator can be shared across products, but product-specific metric definition and source applicability are never inferred from operator equivalence. Product packs can define new dimensions, not bypass tenant ABAC, financial S2, null/zero or numeric rules.

## 2. TASE-R0.1 — Semantic Registry и контроль допустимости

### 2.1. MetricSemanticDescriptorV1

~~~text
metricCode; productNamespace; semanticRevision; displayName/translations;
quantityKind=FLOW|STOCK|EVENT|UNIT_VALUE|RATE|DERIVED_RATIO|
             TIME_WEIGHTED_STOCK|COHORT|DISTRIBUTION|NON_ADDITIVE;
logicalType=MONEY|DECIMAL|INTEGER|RATE|RATIO|QUANTITY|BOOLEAN|STRUCT;
unitCode; currencyCode?; signPolicy; accountingBasis; reportingMethod?;
timeKind=EVENT_AT|AS_OF|INTERVAL_FLOW|COVERAGE_INTERVAL|RATE_FIXING;
sourceGrain; fiscalCalendarRef; validFrom/validTo; observationAsOf;
aggregationAcrossTime=SUM|LAST_AS_OF|TIME_WEIGHTED_MEAN|
                      RECOMPUTE_FROM_COMPONENTS|NONE;
aggregationAcrossDimensions=SUM|DISTINCT_GLOBAL|WEIGHTED_MEAN|
                            RECOMPUTE_FROM_COMPONENTS|NONE;
numeratorMetricRef?; denominatorMetricRef?; weightMetricRef?;
allowedOperatorIds; coveragePolicyRef; missing/zero/negativePolicies;
numericPolicySha; sourceAuthorityRef; tenantACLPolicyRef; reviewStatus;
dimensionKeys[]; effectiveDatedHierarchyRef?; sourceRevisionRef.
~~~

### 2.2. Finance/math invariants

1. **Flow additivity:** SUM only for disjoint verified FLOW intervals, same currency/unit/recognition basis and eligible scope; reject overlap and invalid duplicate event.
2. **Stock semi-additivity:** balances LAST_AS_OF at end cutoff, or time-weighted average only with verified snapshots/interval coverage; sum monthly cash balances is invalid.
3. **Rate/ratio non-additivity:** quarterly margin = Σqualified profit / Σqualified revenue, not average of monthly percentages. A descriptive arithmetic mean of monthly rates may be requested under a *different* metricCode and weighting policy.
4. **Weighted means:** weight metric/code, time dimension, currency/unit and scope explicitly declared. Average interest rate often exposure-weighted; average stock often time-weighted. Weight sum zero → UNDEFINED.
5. **Distinct counting:** monthly distinct clients cannot be summed to annual distinct clients without deduplicated IDs or a qualified approximation contract.
6. **MONEY:** Decimal string and ISO currency, no silent FX, float64, display rounding or fallback zero. Derived variance unit is squared; STDDEV returns original unit; coefficient of variation dimensionless.
7. **Hierarchy:** only eligible leaf business objects aggregate; ancestor and descendants must not double count, and many-to-many joins require attribution/allocation policy.
8. **Null states:** MISSING, EXPLICIT_NULL, NOT_APPLICABLE, INVALID and numeric zero have distinct meaning; no global skip-null for regulated metrics.
9. **Provenance:** exact operatorId+revision, semanticRevision, source/content SHA, calendar/date policy and numeric policy pinned to every output.
10. **Immutable revision:** product-config update generates new pack and Plan SHA, never mutates published result.

### 2.3. Operator registry

The initial **53 candidate reusable operators** are documented in catalog/tase_operator_candidates_r0.tsv. Families BASIC, AVERAGE, DISTRIBUTION, DISPERSION, FORECAST_ERROR, STRUCTURE, TEMPORAL, DEPENDENCE; each operator has supported semantic class, algebra/partial merge strategy, mandatory policy fields, output type and reason when blocking. Product packs select only compatible allowlisted operator IDs.

**R0.1 exit criteria:** all six example product profiles schema-linted; negative tests reject unsigned pack, duplicate metric ID, inherited privilege, illegal SUM(STOCK), AVG(DERIVED_RATIO) as qualified margin, mixed currency/basis, unknown unit, missing numerator/denominator and unqualified event duplication. Exit requires typed schemas and semantic golden candidates; no operational PASS claimed.


## 3. TASE-R0.2 — календарь, интервалы, группировки, полнота

### 3.1. CalendarProfileV1

calendarId; revisionSha; IANATimezone; dataTimeBasis=INSTANT|LOCAL_DATE;
startInclusive/endExclusive; weekStart; isoWeekYearPolicy;
fiscalPattern=GREGORIAN|FISCAL_445|FISCAL_454|FISCAL_544|CUSTOM;
fiscalStartMonth/day; leapYearRule; 53rdWeekRule; DSTpolicy;
businessHolidayCalendarRevision?; customPeriodMappingRevision?.

Supported grains: DAY, ISO_WEEK, MONTH, QUARTER, HALF_YEAR, YEAR, FISCAL_PERIOD, FISCAL_QUARTER, FISCAL_HALF_YEAR, FISCAL_YEAR, ROLLING_N_DAYS, ROLLING_N_MONTHS, CUSTOM_INTERVAL. Every generated bucket carries exact start/end, calendar revision, reporting timezone, periodKey and completeness status.

**Strict interval semantics:** source and output intervals [start,end) on an explicitly defined local/UTC timeline. EVENT timestamps require effectiveTime and postedAt, AS_OF snapshots do not become flows. Leap years (29 Feb), month lengths, boundary inclusivity, week 53, fiscal 4-4-5/4-5-4/5-4-4, holiday calendars and daylight saving must be versioned.

**No invented prorating:** a monthly reported flow cannot be automatically split into daily data or partially overlapping week sums unless source supplies verified daily events or explicit approved allocation method. Otherwise BLOCKED_INSUFFICIENT_GRANULARITY. A source time window larger than output window is not automatically interpolated.

### 3.2. Dimensions and grouping

DimensionDescriptor: dimensionCode, logicalIdType, parent/children mapping revision, effectiveDateRange, hierarchyType=TREE|DAG, dedupAlgorithm, permittedGrouping, cardinalityLimit and tenant security labels. Grouping by stable IDs only; human labels and translation changes cannot reassign group identity. For multi-parent DAG require nonduplicating allocation weights or an explicit unique descendant-set aggregation policy. Cross-dataset join multiplicity declared ONE_ONE or MANY_ONE by source; unexpected MANY_MANY blocks.

### 3.3. CoverageResultV1 and statuses

~~~text
observedRowCount; expectedRowCount?; coveredDuration?; expectedDuration?;
gapWindows[]; overlapWindows[]; watermarkAsOf?; ingestionCutoff?;
sourcePeriodLower/Upper; missingCount; explicitNullCount; invalidCount;
valueCoverageRatio?; durationCoverageRatio?; coverageStatus;
qualityReasonCodes[]; sourceManifestSha; expectedObservationPolicyRef.
~~~

CoverageStatus = FULL|PARTIAL|GAPPED|OVERLAPPING|UNKNOWN; no fake 100% from just 3 observed monthly rows absent authoritative expected schedule. An empty event stream is zero only when a complete authoritative no-event interval is attested. STOCK_LAST can block if snapshot age > maxStaleness. A partial YTD or rolling horizon must declare cutoff and may not be compared with a full year without explicit alignment.

**R0.2 exit:** deterministic month/quarter/half-year/fiscal buckets, leap and DST, week-53, fiscal calendars, incomplete months, overlapping intervals, scope hierarchy roll-ups and join cardinality tests; no silent partial data as FULL.

## 4. TASE-R0.3 — средние, квадратичные отклонения, статистики

### 4.1. Exact operation definitions

- ARITH_MEAN = sum(x)/n for n>0, using qualified present observations.
- WEIGHTED_MEAN = sum(w*x)/sum(w), weights nonnegative and compatible with semantic basis, positive total required.
- TIME_WEIGHTED_MEAN = sum(level_i * validDuration_i)/sum(validDuration_i), requires fully declared piecewise state or interpolator, complete validity windows and type-consistent duration.
- VAR_POP = sum((x-mean)^2)/n, n>=1; VAR_SAMPLE = sum((x-mean)^2)/(n-1), n>=2. Different operator IDs, no hidden normalization. UNIT^2 result.
- STDDEV_POP/SAMPLE = sqrt(variance), original unit; RMS = sqrt(sum(x^2)/n) and is NOT the same as STDDEV.
- MSE = sum((actual-pred)^2)/n, RMSE = sqrt(MSE), MAE = sum(abs(actual-pred))/n, BIAS = sum(actual-pred)/n on **aligned period/business keys**; missing pairs not silently fabricated.
- GEOMETRIC_MEAN only for positive observations under an explicit numerical policy; compounding returns use product(1+r_i) with r_i>-1 and equal basis, not raw geometric mean of signed returns.
- HARMONIC_MEAN requires positive supported values and explicit zero rule.
- MEDIAN/QUANTILE/IQR/MAD need exact quantile definition (ties, weights, interpolation), not median-of-medians. Weighted quantile mode is a separately versioned method.
- COVARIANCE_POP and CORRELATION_PEARSON need actual row/date pair alignment, enough observations and positive variance of each nonconstant side; pairwise vs listwise deletion policy required.

### 4.2. Algebra and numerics

Aggregation partials may use sum/count/weighted numerator+denominator, min/max, or stable n/mean/M2 (Welford/Chan) and covariance moments. Each operator declares whether partial merges are mathematically legitimate and whether merge-order changes may affect approximation tolerance. **Never build quarterly MEDIAN from monthly MEDIANs or annual DISTINCT from summed monthly DISTINCT.**

Money and canonical financial Decimal must not silently cast to float64. NUMERIC_POLICY includes precision, scale, overflow checks, roundingStage, finalRoundMode, sqrt/quantile algorithm revision, deterministic partition merge order. If a statistical kernel uses float/double, the OutputDTO must label APPROXIMATE, numerical error diagnostics, method version and whether legally admitted for the specific calculation.

**R0.3 exit:** independent exact examples for all 53 candidate operators where applicable, boundary zero/null/one observation, large/small Decimal, weight sum zero, quantile ties, consistent chunk merging, squared units and wrong date pairing.

## 5. TASE-R0.4 — доли, сравнения, динамика, план-факт

ComparisonDefinitionV1 includes comparisonCode, baseline=PREVIOUS|SAME_PERIOD_LAST_YEAR|BUDGET|FORECAST|CUSTOM, calendarRevision, periodAlignment=EXACT_INTERVAL|FISCAL_POSITION|EQUIVALENT_ELAPSED_DAYS|CUTOFF_ALIGNED, sourceRevisionSha, scenarioRevision, dimensionScopeJoinPolicy, negativeBasePolicy, percentagePointDisplay and materialityPolicy.

- ABS_DELTA = current - baseline with same unit; PCT_CHANGE requires explicit denominator convention and never returns zero for baseline=0.
- RATE_PP_CHANGE = 100*(rate_current-rate_baseline) in percentage-points when rates stored as fractions; this differs from relative percentage change.
- RATIO_OF_SUMS = sum(numerator)/sum(denominator), same scope/time/grain/currency; no ordinary mean of independently computed margins.
- SHARE = qualified group value / fully reconstructed parent value; disjoint groups, documented sign and nonzero denominator policy.
- CUMULATIVE_SHARE/PARETO require stable descending sort, deterministic ties, meaningful positive base; HHI requires all mutually exclusive groups and explicit output scale.
- TTM_12M for FLOW uses 12 complete aligned months; for STOCK returns end snapshot, not SUM. MoM/QoQ/YoY distinguish comparable complete interval from partial-to-partial.
- CAGR uses positive meaningful start/end and elapsed-year convention; sign changes block or require explicit alternative.

### 5.1. Core financial reference scenario (synthetic)

Monthly revenue [100,120,80], profit [20,36,8] KZT units (or consistently scaled MONEY):
- quarter revenue=300, profit=64;
- quarter profit margin=64/300=0.2133333333..., not monthly mean margin 0.20;
- revenue mean=100;
- population variance=(0^2+20^2+(-20)^2)/3=266.6666667 KZT^2;
- sample variance=400 KZT^2; population standard deviation≈16.3299316 KZT; sample standard deviation=20 KZT.
- month-end cash balances [20,30,10] ⇒ quarter-end balance=10, **not 60**.

These are arithmetic illustrations, not committed runtime golden evidence. Product/currency-specific metadata must not be inferred from examples.

**R0.4 exit:** acceptance vectors for MoM, QoQ, YoY, YTD, budget vs actual, ratio-of-sums, pp difference, parent shares, concentration, partial period, missing/zero/negative baseline, single-sided FX mismatch and fiscal year cutoff.


## 6. TASE-R0.5 — Calculation Session, executor, result and recovery

### 6.1. Typed control-plane DTO candidates

**TaseInputBindingV1:**
sessionId, sessionRevision, tenantScopeRef, ProductPackRevisionSha, sourceDatasetRefs[]/contentShas[], metricSemanticRevisions[], dimensionRevisionShas[], calendarProfileRevisionSha, qualityPolicyRef, numericPolicySha, permissionDecisionRef, resourceBudgetRef, sourceFactSetShas[].

**TaseAggregationPlanDTO:**
tasePlanRevision, requestedMetricCodes[], requestedGrains[], exactInterval, groupBy[], statisticOperatorRequests[], comparisonDefinitions[], resultProfiles[], outputSchemaRevision, numericPolicyRef, minCoveragePolicy, maxOutputCells, idempotencyKey, operatorArtifactRevisions[]; resolve complete DAG, canonical content SHA and PLAN_PREVIEW.

**TaseResultSetV1:**
resultSetRef, sourcePlanSha, tenantScopeRef, productCode/revision, metricCode/semanticRevision, operatorCode/revision, periodKey/calendarRevision, groupKeyTuple, typedValue/unit/currency, numerator/denominator? and weight? where needed, sampleCount, coverageStatus/ratio?, approximationEvidence?, methodState/reasonCode, sourceLineageRefs[], resultSha.

**Wire compatibility:** CalculationResponseDTO.results[] → rows[] → values[] remains unchanged conceptually. Add typed attachments only under version-negotiated output schema, don't break W1–W5 model results. Product Pack outputs remain namespace-scoped and versioned.

### 6.2. Execution lifecycle and data correctness

1. Validate source manifest, scope rights, product signature, allowed metric semantics and exact input revision.
2. Preview: compile typed operator DAG and estimate output groups/cells/resource cost, return reasons for blocked nodes; no durable financial output.
3. Stage datasets in durable metadata store and prepare immutable session; RAM or Redis are optional speed caches and never the sole source of data.
4. Execute a task with scoped independent idempotencyKey; same plan+same key returns original job, same key with changed execution binding returns 409.
5. Lease/fence worker executes bounded aggregation and writes immutable ResultSet + transactional outbox; no partial fake COMPLETE when limits exceeded.
6. Archive ACK from consumer, then release eligible temporary payload after retention; crash/retry reuses pinned source/method versions and commits one canonical result.

External APIs are **proposals**, not running endpoints:
- GET /v1/tase/products
- GET /v1/tase/products/{productCode}/metrics
- GET /v1/tase/operators
- POST /v1/tase/plans/preview
- POST /v1/tase/jobs
- GET /v1/tase/jobs/{jobId}
- GET /v1/tase/results/{resultSetId}

Every result includes lineage and exact period/calendar/semantic policy. No Product Pack may grant new row-level access; suppress restricted group totals, not only individual IDs.

**R0.5 exit:** simultaneous tasks reuse a sealed dataset without conflict, stale ACL/fact/currency/pack rejected, stable deterministic replay, archive semantics, tenant isolation, crash between durable write/outbox and worker re-claim, and no result mutation when new pack revision published.

## 7. TASE-R0.6 — независимый тестовый банк, нагрузка, восстановление

### 7.1. Test classes and planned minima

| Group | Planned cases | Invariants |
|---|---:|---|
| SEMANTIC_OPERATOR | 35 | no STOCK sum, no RATE naive sum, exact monetary units |
| PRODUCT_PACK | 25 | six product packs, signature, ACL, collision, revoked revision |
| CALENDAR_INTERVAL | 30 | leap/DST/fiscal/53-week/partial/overlapping |
| GROUP_SCOPE | 25 | hierarchy dedup, multi-parent, cross-tenant, join cardinality |
| STATISTICAL_MATH | 50 | variance sample vs pop, Welford/Chan, quantiles, paired errors, Decimal |
| PERIOD_COMPARISON | 35 | MoM/QoQ/YoY, YTD, plan-fact, ratio, HHI, pp |
| SESSION_RECOVERY | 30 | content SHA, idempotency, stale rules, outbox/crash/replay |
| PERFORMANCE_RESOURCE | 20 | output cell budget, 10k/100k/1m rows, p95/p99, RSS |
| **Total proposed** | **250** | **PLANNED ONLY — NOT EXECUTED** |

TestCaseDTO fields: caseId, testClass, productPackRevision, sourceSha, scope+calendarRevision, metricSemanticRevision, operatorRevision, paramsSha, exact input rows/manifestRef, expected typed output/status/reasonCode, error tolerance, independent reviewer, sourceFinancialBasis and evidenceRef. Financial and regulatory testcases require independent domain-specific S2 rather than relying on core arithmetic tests.

### 7.2. Performance and recovery

Benchmark suites with rows 10k, 100k, 1m; metric count 10,100,1000 and group counts 10,1000,100k where resource quotas permit; 4 calendar grains, dynamic output windows and BASIC/EXTENDED profiles. Estimate bounded output cells before executing; if requested combinations explode, BLOCKED_RESOURCE_BUDGET instead of exhausting memory. Limit maxGroups, maxBuckets, maxOperators, maxOutputCells, maxStatsSampleSize, maxRuntime and memory.

Record ingestion, canonicalization, plan compile, cache hit/miss, operator compute, serialization, durable archive, throughput, p50/p95/p99, CPU, peak RSS, fail rate and retries. **No invented performance SLO or Rust speedup claim** until representative benchmark and required target hardware profile approved.

Compare exact Python Decimal reference with candidate PostgreSQL SQL/Java set-based calculations and, where appropriate, Arrow/Polars/DuckDB. Rust acceleration only after proof of correctness and complete plan-level comparison; float kernels never silently replace financial exact aggregates.

### 7.3. Security and release criteria

- Verify Product Pack signature, source authorization, scope isolation, dimension ACL and absence of inference leakage via group totals.
- Reject code injection expressions in pack definitions, malicious labels, dangerous cardinality and excessive output requests.
- Financial S2 is per metric/method/basis and does **not** follow automatically from a passed generic SUM/AVG kernel.
- Metric telemetry must not include raw confidential rows or privileged group labels.

**R0.6 exit:** all agreed 250 bank cases PASS on the committed runtime in CI; verified source-to-result lineage; exact arithmetic; tests of crashes/recovery; calibrated SLO p95/p99; signed target product sample acceptance. This document alone grants none of these claims.

## 8. Stage exits, priorities and method-freeze constraints

| Stage | Main artifact | Exit gate |
|---|---|---|
| TASE-R0.1 | ProductPack/MetricSemantic/Operator Contracts | illegal aggregation blocked |
| TASE-R0.2 | Calendar/Interval/Scope/Coverage Contracts | no time overlap/double counting |
| TASE-R0.3 | Stable exact and qualified statistical operators | independent maths/edge goldens |
| TASE-R0.4 | Comparison/Ratio/Trend/Plan-fact Contract | comparable periods, correct ratios |
| TASE-R0.5 | Hub preview/job/result/outbox integration | scoped idempotency and crash recovery |
| TASE-R0.6 | 250-case bank, load and operational QA | regression and benchmark acceptance |

Implementation order R0.1 → R0.2 → R0.3 → R0.4 → R0.5 → R0.6. Freeze only independently reviewed exact revisions; no universal permanent mutable calculator configuration. Product packs remain independently versioned and may expand without duplicating core operators.

## 9. ADRs needing resolution before immutable freeze

- TASE-ADR-01: namespace and signature/approval governance of Product Packs.
- TASE-ADR-02: Decimal precision and max unit dimensions across Python/SQL/columnar.
- TASE-ADR-03: eventTime/ingestedTime, watermark and late corrections.
- TASE-ADR-04: fiscal 4-4-5 calendars and year/week 53.
- TASE-ADR-05: time weighted stock interpolation restrictions.
- TASE-ADR-06: exact and approximate quantile variants and error tags.
- TASE-ADR-07: exact distinct and private/approximate sketches.
- TASE-ADR-08: sample vs population variance and statistical float policy.
- TASE-ADR-09: effective-dated hierarchy and multi-parent attribution.
- TASE-ADR-10: ResultSet v2 attachments and backward compatibility.
- TASE-ADR-11: product pack revocation and tenant ABAC on aggregates.
- TASE-ADR-12: cardinality/output-cell cost model and full-path benchmark.

## 10. Decision

**ACCEPT AS DESIGN CANDIDATE.** This task does not create Python finance TASE code, database migrations, qualified financial models, or production permission. Existing 116 candidate model codes, D01–D114 source proposals and separate GEO reference retain their identities. Finalize semantic and numeric policies, independent financial math controls and product applicability before freezing TASE contracts.
