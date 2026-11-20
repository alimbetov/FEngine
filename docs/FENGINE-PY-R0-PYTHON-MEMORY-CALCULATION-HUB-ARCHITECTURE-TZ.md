# FEngine PY-R0 — Python-first Memory Calculation Hub: архитектура и требования

**Документ:** FENGINE-PY-R0-ARCH-TZ-V1.1  
**Дата:** 2026-11-20  
**Статус:** DESIGN / REQUIREMENTS_COLLECTION / NOT_IMPLEMENTED  
**Проект:** alimbetov/FEngine, main  
**Основание:** FENGINE_MASTER_SPEC.md v0.5 и W1/P0, W2/P1, W3/P2 подробные model/DTO спецификации.  
**Внешний FIN source context:** alimbetov/fin-analyzer, feat/fin-form-library-standalone, snapshot для сверки 2026-11-20; наследовать FIN production-qualification и финансовый S2 нельзя.  
**Ограничение:** этот файл — только проектирование. Не создавать Python-файлы, миграции, контейнеры, сервисы, данные и не заявлять о запуске тестов без отдельного решения.

## 1. Архитектурный выбор

**Предлагаемое решение:** сначала спроектировать проверяемый Python reference system для поведения Memory Calculation Hub и 14 вычислительных моделей, затем заморозить независимые DTO/golden vectors, и только после этого решать, какие data-plane компоненты переносить на Rust. Python должен воспроизводить **не только математику**, но и жизненный цикл задания: contract admission → immutable dataset → calculation session → two-phase job → independent worker → result array → durable outbox → archive ACK → 3h temporary cleanup.

**Что НЕ строим:** полный клон Redis, собственный распределённый key-value protocol, Python-код внутри Redis Lua/server, произвольный код-исполнитель, повторный financial source writer для FIN, альтернативный registry финансовых метрик без mapping к FIN.

**Главная целевая характеристика:** immutable source datasets можно зарегистрировать/верифицировать один раз и безопасно переиспользовать в нескольких независимых вычислительных job с разными ключами идемпотентности, не загружая источник заново при cache hit. Все job/results должны оставаться восстановимыми без оперативного кеша.

## 2. Контур ответственности

| Слой | Назначение | Python-first выбор (предложение) | Источник истины |
|---|---|---|---|
| HTTP/API | регистрация схем, наборов данных, сессий, заданий; статус, результат, ACK | FastAPI + Pydantic v2 | Контракты + PostgreSQL |
| Typed contracts | InputBatchDTO, Dataset, TaskCode, Params, ResultSet, states | Pydantic для boundaries; отдельные frozen domain types | Версионируемый реестр |
| Canonicalization | нормализация decimal/date/order/typing + SHA-256 | стандартная библиотека Python и строгая canonical format specification | Проверяемый manifest |
| Calculation Session | immutable dataset references и rights for multiple jobs | независимый SessionService | Durable metadata |
| Hot memory | ограниченный cache validated immutable datasets | backend interface: local bounded prototype или Redis | Только cache |
| Staging | recoverable input data / chunk manifests | PostgreSQL metadata + durable blob storage | Durable payload |
| Inbox/jobs/leases | одна задача на scoped idempotency key, retries/fencing | explicit PostgreSQL transactions | PostgreSQL |
| Math/reference | чистые финансовые функции Decimal, versioned policies | decimal.Decimal + explicit Context | Goldens + approved methodology |
| Worker | отдельный процесс/контейнер; CPU не блокирует API | Python isolated worker with quotas | Job state only in PG |
| Result store | immutable multi-result array + evidence hash | Python serializer, durable result manifests | PostgreSQL/blob |
| Outbox & archive | publication after local commit; trusted external ACK | PG outbox relay; idempotent consumer contract | PostgreSQL and external DB |
| Cleanup | 3h payload retention, tombstone and cache eviction | separate sweeper process | PG lifecycle |
| Observability | memory/CPU/queue/p95/error metrics; no raw finance logs | structured telemetry contracts | Metrics + immutable audit |

**Пакетные вычисления должны запускаться вне FastAPI request worker.** BackgroundTasks в веб-процессе не является долговечной очередью финансовых CPU задач. Python GIL, копирование больших структур между процессами и стоимость Decimal loops учитываются в benchmark и не маскируются словом in-memory.

### 2.1. Логическое разбиение будущего Python package (не реальные файлы)

- api: boundaries/http, auth context, DTO version routing, consistent errors;
- contracts: schemas, type registry, parameter resolution, SHA manifests;
- sessions: scoped session, immutable datasets, reference counting and close;
- memory: CacheBackend interface, admission, pin/unpin, eviction, load integrity;
- inbox: staged registration, conflict checks, job atomic creation;
- scheduler: due job claims, lease/fence, quotas, deadlines, cancellation;
- calc: pure batch core, typed DAG evaluation and 14 model plugins by TaskCode allowlist;
- results: result set shaping, canonicalization, lineage and durable commit;
- outbox: publish/retry, archive ACK handling;
- cleanup: terminal retention, session and temporary blob lifecycle;
- observability: traces, metrics, audit reasons;
- testspec: golden corpus, state machine/property/race/fault acceptance (пока только план).

**Правило зависимостей:** calc не импортирует api, DB, Redis, HTTP or sessions; calc принимает immutable typed arrays и plan, возвращает typed result sets. Python core и Rust core должны выглядеть одинаково снаружи, но не обязаны иметь одинаковую внутреннюю структуру.

## 3. Contract → Dataset → Session → Job

### 3.1. Четыре независимые идентичности

1. ContractRevisionId: версия типа входных данных и разрешённых задач (политика, поля, validation constraints).
2. DatasetId + InputContentSha256: идентичность immutable typed data и exact source revision. Дедупликация только в пределах разрешённого tenant/scope с одинаковой канонизацией; hash не является proof of approval.
3. SessionId + SessionRevision: логический набор разрешённых DatasetRef, на котором можно запускать разные расчёты. Сессия не хранит бухгалтерские truth сама.
4. (tenantId, clientNamespace, idempotencyKey) + ExecutionBindingSha256: отдельная идентичность одного **конкретного запуска**. Binding includes task(s), task/method/params versions, dataset hashes, numeric policy, exact plan and output shape.

**Критический инвариант:** одна Session может обслуживать 14 jobs; но разные задачи (даже над одной Session) получают разные idempotency keys. Повтор одного key с изменением задачи, версии, входов или параметров → 409. Нельзя превращать SessionId в общий ключ идемпотентности для всех задач.

### 3.2. Session status / immutable datasets

Session DRAFT → READY → CLOSED → EXPIRED.
- DRAFT: зарегистрирована metadata, пока принимаются initial datasets; нельзя считать dataset snapshot complete.
- READY: frozen SessionRevision/dataset manifest SHA, разрешённые tasks и tenant scope определены; READY нельзя изменять in-place. Дополнительные данные = **новая SessionRevision/новая SessionId по ADR**, а ранее созданные jobs ссылаются на предыдущую ревизию.
- CLOSED: новых job не создаём; существующие jobs завершаются, а pinned source сохранён.
- EXPIRED: новая задача не запускается; уже committed result доступен по собственной retention/архивной политике.

Hot cache state ABSENT / FETCHING / READY / PINNED / EVICTED / FAILED_LOAD / PURGED не равен durable Session/Job state. Cache miss не создаёт новую задачу.

### 3.3. Протокол совместимости с Wave-1

**Сохранить существующий простой путь без сессии:**
- PUT /v1/jobs/{key}/input: принимает typed datasets и contract, сохраняет durable staged input, возвращает PREPARED + InputSha.
- POST /v1/jobs/{key}/execute: taskCode + pinned CalcPlan/Params revisions, затем QUEUED.
- GET /v1/jobs/{key} и GET /v1/jobs/{key}/result: status + массив resultSets.
- POST /v1/jobs/{key}/archive-ack: проверка durable external write receipt.

**Дополнительный вариант reuse через Session (не ломает прежний API):**
- POST /v1/sessions: создать DRAFT (server-assigned SessionId).
- PUT /v1/sessions/{sessionId}/datasets/{datasetId}: immutable dataset registration; либо attach существующего проверенного content-addressed DatasetRef при выполненной авторизации.
- POST /v1/sessions/{sessionId}/seal: после проверки набора данных закрепить READY revision/SessionSha.
- PUT /v1/jobs/{key}/input: вместо дублирования bytes использовать {sessionId, exactSessionRevision, datasetRefs[], inputContractVersion}; сервер проверяет права и SHA, возвращает PREPARED job binding.
- POST /v1/jobs/{key}/execute: стандартный запуск той же схемы, как standalone.
- POST /v1/sessions/{sessionId}/close: запретить новые jobs; существующие завершаются, временные datasets подчиняются retention всех связанных jobs.

Этот Session API — **DRAFT**, выбор точных HTTP verb и nullable/required полей согласовывается с Wave-1 schema. Важно отделить reuse of physical chunks от полномочий: идентичный SHA не даёт одному клиенту доступ к данным другого.

## 4. Python Input DTO и математические представления

### 4.1. Канонический Control Plane DTO

InputContractDTO:
contractCode, contractRevision, datasetSchemas, accepted taskCode revisions, numericPolicyRef, sourcePolicyRef, allowed ResultShape, scope constraints, input validation policy SHA.

DatasetManifestDTO:
datasetId, datasetType (D01..D15), datasetSchemaRevision, rowCount, rowKeys, columnDescriptors, contentSha256, sourceRevisionRefs, scopeRef, period/basis, currency/unit contract, per-column valueState arrays, physical chunk references.

ColumnDescriptorDTO:
fieldCode, logicalType, scale/precision, unitCode, currencyCode, requiredness enum R/C/O, statePolicy, values[] and states[] for inline small batches or chunks[] for large inputs.

CalculationPlanDTO:
taskCode, methodRevisionRef, paramsRevisionRef, sourceContentHashes[], sessionRevision, dependency DAG SHA, numericPolicySha256, algorithmArtifactSha256, allowed overrides/expiration, outputSchemaRevision, executionMode allowed for UAT vs Production.

CalculationResponseDTO remains **unchanged** from Wave-1 §6: root results[] → CalculationResultSetDTO.rows[] → CalculatedRowDTO.values[], with lineage SHA, state, unit and source refs. Агрегаты/группы/периоды/корни имеют разные формы, но единый root contract.

### 4.2. Decimal policy (все 14 кандидатов)

- MONEY/DECIMAL/RATE/QUANTITY → canonical decimal string on external wire; Python Decimal constructed from decimal **string**, not binary floating-point input.
- Context precision/rounding/traps, intermediate vs final quantization and currency-scale policy fixed in numericPolicyRevision and included in execution binding SHA.
- EIR/IRR iterative solving: explicitly defined bracket/domain, root isolation, number of roots, residual/tolerance and maximum iterations; a numerically plausible value with bad residual is INVALID.
- Currency mismatch, period mismatch, AS_OF versus INTERVAL, inconsistent amount basis, MISSING vs zero, duplicate events — blocked, never silent conversion.
- For event ordering use effectiveDate + postedAt + sequence + deterministic business tie-breaker, as specified by the model; do not rely on Python dict insertion order or uncontrolled parallel reduction.
- Reproducibility: canonical output sorting, canonical decimal normalization **that preserves agreed significant scale when scale is part of semantics**, stable hash algorithm/version and error state included in result manifest.
- Python/Arrow/Pandas/Polars: never silently cast Money to float64. Binary columnar Decimal types may have precision limits and cost for conversion to Python Decimal; treat as transport/column storage, not automatic financially qualified arithmetic.

### 4.3. Batch layout и память

Small requests: inline JSON typed column vectors (length = rowCount, same rowKey alignment). Large requests: immutable chunked binary record batches with authoritative manifest, checksums, size/row limits; internal cache can use Redis or process-local bounded storage. 100k/1m rows require separate memory and serialization budget, no promise one enormous JSON response. For a 1m-row result, allow chunked resultSet retrieval and paginated immutable manifest.

Input cache key (logical): hash(scope, datasetContentSha, schemaRevision, encodingRevision). Result cache key: hash(scope, committedResultSha, outputSchemaRevision, numericPolicySha). No raw PII, credential or financial amount in key names; cache presence never bypasses authorization.

### 4.4. Redis-backed vs Python in-process vs later Native Rust

| Режим | Роль | Ограничение |
|---|---|---|
| Python in-process bounded cache | простой математический reference test и single-process exploration | **не** общая RAM между worker processes; no durability |
| Redis-backed hot cache | общий быстрый lookup/TTL/ready state для нескольких processes, optional small/medium binary objects | TCP/copy serialization, maxmemory/eviction, отдельные authz checks; не источник истины |
| PostgreSQL + immutable blob storage | durable inbox/manifest/result and archive proof | дороже чем RAM, но обязателен для crash safety |
| Native Rust memory hub (future) | typed columnar worker-local buffers, optional no-copy within worker | только если parity+benchmark оправдывают собственный memory subsystem |

**Предварительная Python архитектура:** Python API + Python isolated workers + PostgreSQL durability, MemoryCacheBackend abstraction. Redis как дополнительный hot backend, а не обязательная внешняя зависимость reference math. Не добавлять самостоятельный Redis-compatible сервер в Python.

## 5. Calculation Session — системный контракт

SessionDTO:
sessionId, sessionRevision, scopeRef, calculationPurposeCode, acceptedTasks[], inputDatasetRefs[], datasetManifestSha256, sessionState, createdAt, sealedAt, closedAt, expiresAt, memoryPolicyRef, resourceBudgetRef, activeJobCount, sessionSha256.

SessionInputRef:
datasetId, schemaRevision, inputContentSha256, boundBusinessScopeRef, sourceFactSetRefs[], rightsGrantRef, status VERIFIED, pinnedUntil?, lastAccessAt?, cacheLocationHint? (hint не contract authority).

SessionTaskRequest:
taskCode, exact methodRevisionRef, parameter SHA, inputRefs, requested output shape, executionMode, idempotencyKey, admissionClass (UAT only until separately qualified).

Session life:
- atomic session seal/freeze; immutable READY revision;
- every job obtains ref-counted dataset pin and bounded resource budget;
- cancellation/failure release pin after worker fencing and durable job transition;
- READY Session with no running jobs can remain logical while RAM cache evicted;
- close forbids new jobs, not reading archived results;
- session expire after agreed max active duration, and payload purge only when all dependent jobs terminal/acked and retention gate passed.

## 6. Job execution и восстановление

1. HTTP validation: authorize tenant/org/project; validate per-task dataset requirements and exact numeric policy; canonicalize and verify SHA.
2. Commit staged input/session ref to durable PostgreSQL before claiming PREPARED. Memory fill can be asynchronous; PREPARED means recoverable after restart, not solely in RAM.
3. Execute transaction: compare scoped IdempotencyKey/input digest; lock staged registration; check approved method/source; insert one immutable job + queue state. Conflict → 409; exact replay → same job.
4. Worker claim via PostgreSQL SELECT ... FOR UPDATE SKIP LOCKED (queue-specific), write increasing fencing token + lease expiry; release DB transaction before CPU execution.
5. Worker loads pinned input through CacheBackend; on cache miss load immutable source storage, rehash, validate; run pure Python calculation kernels with explicit Context; no unbounded concurrency and no direct source DB mutations.
6. Before result commit verify current fence, cancellation, source validity, policy/plan revision admission and result hashes; atomically commit result manifest + job SUCCEEDED + transactional outbox in same PG transaction.
7. Outbox relay independently delivers event at-least-once. Consumer idempotently writes external durable financial result and sends archive ACK with resultSha/checkpoint. ACK cannot by itself constitute independent financial S2.
8. Cleanup removes hot cache under memory pressure when unpinned; after >=3h retention and verified archive receipt purge temporary blobs. Tombstones retained beyond retry window, independent audit retention.

**Сбои:** API crash before staged commit = no PREPARED; worker crash = lease expiry/reclaim (same job, new fencing); hot-cache loss = reload from durable store; outbox relay duplicate = consumer dedup; ACK lost after DB archive write = retry ACK; stale worker after fencing = discard outcome; failure before archive ACK = never delete sole durable result. At-least-once CPU execution + exactly one committed outcome per scoped key; no exactly-once network guarantee.

## 7. Первый Python математический scope — все 14 без изменения доменных контрактов

| Семейство | Task Codes | Python module boundary | Главное требование |
|---|---|---|---|
| SET | W1.SET.AR_BALANCE.V1, AP_BALANCE.V1, AGING.V1, REPLAY.V1 | obligation_events_reference | Stable business keys, amendments, allocations, correct asOf |
| LOAN | W1.LOAN.INTEREST.V1, PRINCIPAL.V1, EIR.V1 | loan_cashflow_reference | Separate contractual cash vs nominal interest vs IFRS EIR |
| CASH | W1.CASH.WEEK13.V1, CFO_DIRECT.V1, CFO_INDIRECT.V1 | cashflow_reference | 13-week rolling balances, classified actual cash, reconciling bridge |
| DCF | W1.DCF.NPV.V1, IRR_ROOTS.V1 | investment_reference | Period/rate compatibility and certified root policy |
| STOCK | W1.STOCK.FIFO.V1, WAC_MOVING.V1 | inventory_reference | Deterministic event cost layers vs moving weighted average |

**Волны моделирования:** сначала независимые положительные/отрицательные worked examples, затем pure Python domain functions, потом protocol wrapper и concurrency/fault tests; **не** параллельно реализовать 14 семейных algorithms до согласования финансовых политик. По каждой методике отдельное golden fixture/точная ревизия и VariantStatus (DRAFT, MATH_VERIFIED, FINANCE_S2, PROD_ADMITTED) — на данном этапе все DRAFT.

Пример ожидаемой связи без исполнения:
- регистрируем одну Session с 100k immutable LOAN/RATE_RULE/LOAN_CASH_EVENT rows;
- запускаем три отдельных idempotency-key jobs с TaskCodes LOAN.INTEREST, LOAN.PRINCIPAL, LOAN.EIR;
- каждый job переиспользует одни и те же input content hashes, но имеет свой CalcPlan, params SHA, output and result hash;
- после archive ACK всех зависимых jobs и retention gate сессия освобождает временные данные; долговременные результаты и tombstone остаются.

## 8. Форматы ошибок и состояний

HTTP:
201/200 REGISTER accepted/replay; 202 EXECUTE queued or GET result pending; 200 completed result; 404 unknown/unauthorized key without cross-tenant leakage; 409 mismatch/existing immutable binding/input-not-ready; 410 expired with tombstone; 422 invalid contract/data/method; 429 resource quota; 503 backend unavailability with safe retry.

ErrorDTO:
{code,stage,scope-safe message, retryable, affectedDatasetId?, rowKey?, fieldCode?, taskCode?, sourceRevisionRef?, observedAt, correlationId}.
No full raw financial values/PII in error logs.

Result state:
COMPLETE, PARTIAL, INVALID, BLOCKED, UNDEFINED, NOT_APPLICABLE, NO_ROOT, PARTIAL_ROOT_SEARCH and valueState PRESENT/MISSING/NULL/etc. Empty ROOT_SET with NO_ROOT must not be presented as valid zero IRR. Failed job can have no committed financial results; an algorithm-level domain invalidity may be a committed typed result with BLOCKED/INVALID state, never pretend it is an approved financial number.

## 9. Memory/retention and operational thresholds — design targets

- Job input memory budget per tenant, API request and per worker process; numbers determined after fixture profile, not invented SLA.
- Cache eviction can happen before three hours for unpinned reproducible items; restart must not lose canonical registered input. No guarantee that OS shared memory between processes is safe without explicit pin lifetimes and cleanup.
- 3h staged PREPARED TTL from registration if no EXECUTE; completed job temporary output expires no earlier than 3h after terminal state **and archive ACK**. Failed/unarchived states require specific recovery retention policy.
- Session user-visible lifetime separate from buffer cache TTL; close or expire never invalidates an already accepted running job.
- Idempotency tombstone retained longer than client retry window (proposal minimum 7 days; open approval). Durable financial archive has independent accounting/regulatory retention.
- No leaks or cross-tenant dataset reuse; encrypted transport, service identity, source authorization and bounded remote callbacks. If memory cannot accommodate batch: explicit WAITING_CAPACITY/RESOURCE_EXHAUSTED or chunked stream, never silently truncate.

## 10. Acceptance tests to specify before any implementation

| Test ID | Scenario | Expected |
|---|---|---|
| PY-001 | Register same exact input/key twice | one durable inbox input and same inputSha |
| PY-002 | Reuse same key with altered column/value-state | 409; original remains |
| PY-003 | Seal Session and bind two distinct jobs | same immutable datasets, distinct jobs/results |
| PY-004 | Modify READY Session | rejected; new revision only |
| PY-005 | Reuse job key with different taskCode/params | 409; no second outcome |
| PY-006 | Unavailable Redis/local hot cache | durable cold reload, same checksum |
| PY-007 | Large batch exceeds memory limit | bounded backpressure/no incomplete result |
| PY-008 | Worker crash before result commit | new fence/retry; one committed result |
| PY-009 | Stale worker attempts commit | fenced out |
| PY-010 | API restart during job | state/lookup remain durable |
| PY-011 | Outbox event re-delivered | consumer stores result once |
| PY-012 | ACK lost after external commit | replay ACK accepted, no financial duplicate |
| PY-013 | 3h elapsed but no archive ACK | result NOT purged |
| PY-014 | Archived + retention elapsed | temporary blobs purged, tombstone retained |
| PY-015 | Cross-tenant SHA collision/access test | no unauthorized data leak |
| PY-016 | Currency/units/periods mismatch | typed blocker, not silent zero |
| PY-017 | Root solver has 0/2 roots | ROOT_SET state correct |
| PY-018 | FIFO vs WAC same movements | different legitimate values under fixed policies |
| PY-019 | SET duplicate payment/reversal replay | no double counting |
| PY-020 | LOAN nominal vs EIR | distinct outputs/lines with distinct policy refs |
| PY-021 | CFO direct vs indirect not comparable | NOT_COMPARABLE, no fabricated difference |
| PY-022 | Golden 14 models | independently verified expected vectors, no false PASS |
| PY-023 | 1M rows and paged output | no single unbounded JSON allocation |
| PY-024 | Hash/canonicalization cross-language manifest | Python↔Rust expected identical binding/result SHA where semantics exact |
| PY-025 | Kill/restart while Session has active jobs | dataset refs/pins recover by job states, no orphan leaks |
| PY-026 | No financial S2 for UAT algorithm | production admission rejected |

Future testing tools (not installed/used yet): pytest, Hypothesis, PostgreSQL 16 Testcontainers, controlled clock and fault injection harness; all model fixtures checked independently of Python implementation. Postgres-based queue uses SKIP LOCKED only for queue claims, not for general financial snapshots.

## 11. Proposed future development milestones (NOT STARTED)

| Milestone | Deliverable / evidence | Gate |
|---|---|---|
| PY-R0.0 | Настоящее design ТЗ, reviewed with Wave-1 DTO | documented |
| PY-R0.1 | Formal IDL/JSON schema, canonical hashing and numeric policy specification | contract approval |
| PY-R0.2 | Independent math golden dataset and control cases for SET/LOAN/DCF/STOCK/CASH | methodology review |
| PY-R0.3 | Pure Python Decimal reference for first narrow vertical, no network | exact math evidence |
| PY-R0.4 | Durable API/inbox/jobs/outbox/session and PG16 crash tests | protocol conformance |
| PY-R0.5 | MemoryBackend comparison local/Redis, scoped reuse and 3h retention tests | recovery/resource safety |
| PY-R0.6 | Full 14 model references + independent golden/negative cases | mathematical coverage |
| PY-R0.7 | Benchmark compute-only vs full-path, document Rust parity interface | measured optimization decision |
| RUST-R0.* | Rust substitution behind same contract, only after Python freeze | independent approval |

**Рекомендуемый первый Python implementation slice (будущая работа):**
start with one synthetic, fully pinned F02 or SET.01 case, not the entire 14 model set in a distributed architecture; GET returns exactly one immutable ResultSet and Outbox ACK; extend to Session reuse and multiple result shapes when protocol is accepted.

## 12. Открытые ADR и критерии выбора

- ADR-PY-01: достаточно ли PG-only + bounded local cache для первой квалификации, или Redis с первого этапа?
- ADR-PY-02: как точно canonicalize decimal with trailing scale, datetime precision, maps and rows for cross-language SHA?
- ADR-PY-03: какие размеры batch отделяют JSON inline, binary chunks, object store?
- ADR-PY-04: как стабилизировать правовую идентичность oblig/loan/stock events и historical event ordering?
- ADR-PY-05: какие memory quotas/fail-safe и процессная изоляция безопасны на целевом железе?
- ADR-PY-06: кто выдает независимый financial S2 и кто подписывает archiving receipt?
- ADR-PY-07: как задаётся horizon/key tombstone и политика после 3h без ACK?
- ADR-PY-08: какие сценарии требуют runtime Python (UAT) и какие допустимы для future Rust?
- ADR-PY-09: нужны ли Calculation Session version/revision либо always create new Session on changes?
- ADR-PY-10: какой контракт выбрать для async status/result streaming and chunked read?
- ADR-PY-11: какие виды финансовых unit/currency/period conversion запрещены автоматически?
- ADR-PY-12: какие показатели Wave-1 из FIN имеют source binding, а какие нуждаются в новых source contract revisions?

## 13. Проверяемые технические источники

- Python decimal: https://docs.python.org/3/library/decimal.html
- FastAPI background tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- PostgreSQL SELECT SKIP LOCKED: https://www.postgresql.org/docs/16/sql-select.html
- Redis eviction/maxmemory: https://redis.io/docs/latest/develop/reference/eviction/
- W1 14 models, input/output DTO and Memory Hub design: https://github.com/alimbetov/FEngine/blob/main/docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md

**Финальное ограничение документа:** DESIGN-ONLY. Никаких исходников Python/Rust, зависимостей, SQL-миграций, контейнеров, фактически выполненных тестов или production admission. Следующий переход только после явного разрешения пользователя.


---

## 14. PY-R0 v1.1 extension: one Python hub for 83 models / 81 dataset schemas

**Status:** REQUIREMENTS_ONLY / architecture expanded 2026-11-20, no Python code exists.

All 83 model specs use a single calculation orchestration mechanism, registry, input/output transport and Calculation Session abstraction. Detailed method contracts:
- W1/P0 14: docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md
- W2/P1 42: docs/FENGINE-HPC-WAVE2-P1-42-METHOD-DTO-RESULT-TZ.md
- W3/P2 27: docs/FENGINE-HPC-WAVE3-P2-27-STATISTICAL-METHOD-DTO-TZ.md

**Total:** D01–D81 typed dataset schema candidate families; 83 unique TaskCode model slots, *not* 83 processes, microservices or independently shipped engines.

Future Python modular calculation domain families (not source files): set, ecl_credit_risk, loans, cashflow, dcf, accounting_consolidation, inventory, fixed_assets, costing, planning_optimization, statistical_risk. Implement pure functions behind one common EvalContract and versioned task dispatcher. Separate EIR and KZ_GESV regulatory eligibility, 12m vs lifetime ECL, VaR vs ES, FIFO vs WAC, direct vs indirect CFO.

Result shape v2 allowlist adds SCENARIO_MATRIX, DISTRIBUTION and OPTIMIZATION_PLAN to existing six; use versioned OutputSchemaRevision and capability negotiation, not a breaking change to existing Wave-1 ResultSet layout. DISTRIBUTION requires sample/weight evidence, quantile/CI methodology; OPTIMIZATION_PLAN requires decision vector, constraints and feasibility/optimality gap. MONEY_PER_UNIT, VECTOR, MATRIX, POINT_SERIES are **composite typed DTO families** based on versioned Decimal/currency/quantity and immutable shape/ordering, not loose untyped JSON primitives.

**Session reuse:** one sealed immutable input Session can feed multiple TaskCodes with separate scoped idempotencyKeys. DAG edges pin upstream committed result SHA, never speculative cache entry. Cache backend local/Redis/Rust does not change finance result or metadata state.

**Financial/statistical hard-stop:** candidate documents provide synthetic worked examples only. Production requires verified source bindings, independent arithmetic goldens, finance S2 where relevant, calibrated risk assumptions and cross-language parity. No code generation, no tests, no data ingestion into FIN and no server deployment at this phase.
