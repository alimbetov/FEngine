# FEngine HPC-W1 — Техническое задание: 14 моделей, входные массивы DTO и единый массив результатов

**ID:** FENGINE-HPC-W1-TZ-V1  
**Дата:** 2026-11-20  
**Репозиторий:** alimbetov/FEngine, main  
**Статус:** REQUIREMENTS_DRAFT / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD  
**Источник:** FENGINE_MASTER_SPEC.md v0.4; FIN Analyzer feat/fin-form-library-standalone, snapshot 854fac8cbff67986b05159271fc5231cc712baa0.  
**Область изменений:** только этот отдельный Markdown-документ. Python, Rust, PostgreSQL, REST, миграции и тесты не реализуются на данном этапе.

## 1. Цель и границы

Спроектировать 14 финансово-экономических расчётных моделей первой волны в качестве независимых, версионируемых кандидатов. Каждая модель принимает один или несколько массивов структурированных данных, фиксированный набор методологических параметров и возвращает массив типизированных рассчитанных значений через единый Result DTO. Будущая последовательность: методологическое решение → независимые ожидаемые результаты → Python Decimal reference → проверка на общих golden fixtures → Rust parity → измерение скорости. Ни один этап не является автоматически независимым финансовым S2.

### 1.1. Ровно 14 показателей

| № | FEngine metric | TaskCode | Результат / shape |
|---:|---|---|---|
| 01 | HC.SET.01 | W1.SET.AR_BALANCE.V1 | ROW_ALIGNED + AGGREGATE |
| 02 | HC.SET.02 | W1.SET.AP_BALANCE.V1 | ROW_ALIGNED + AGGREGATE |
| 03 | HC.SET.03 | W1.SET.AGING.V1 | ROW_ALIGNED + GROUPED |
| 04 | HC.SET.06 | W1.SET.REPLAY.V1 | EVENT_SERIES + ROW_ALIGNED |
| 05 | HC.LOAN.01 | W1.LOAN.INTEREST.V1 | TIME_SERIES |
| 06 | HC.LOAN.02 | W1.LOAN.PRINCIPAL.V1 | TIME_SERIES |
| 07 | HC.LOAN.03 | W1.LOAN.EIR.V1 | AGGREGATE + TIME_SERIES |
| 08 | HC.CASH.01 | W1.CASH.WEEK13.V1 | TIME_SERIES |
| 09 | HC.CASH.04 | W1.CASH.CFO_DIRECT.V1 | GROUPED + AGGREGATE |
| 10 | HC.CASH.05 | W1.CASH.CFO_INDIRECT.V1 | GROUPED + AGGREGATE |
| 11 | HC.DCF.01 | W1.DCF.NPV.V1 | TIME_SERIES + AGGREGATE |
| 12 | HC.DCF.03 | W1.DCF.IRR_ROOTS.V1 | ROOT_SET |
| 13 | HC.STOCK.01 | W1.STOCK.FIFO.V1 | EVENT_SERIES + GROUPED |
| 14 | HC.STOCK.02 | W1.STOCK.WAC_MOVING.V1 | EVENT_SERIES + GROUPED |

HC.* — предлагаемые коды FEngine, не утвержденные финансовые показатели FIN. Не создавать 167-ю форму в FIN. Предлагаемые связи с FIN и готовность указываются отдельно. Каждая модель получает самостоятельные MethodRevision, ParamsRevision, InputSchemaRevision и OutputSchemaRevision.

## 2. Режим асинхронной обработки

A. RegisterInput: PUT /v1/jobs/{key}/input с exact входными массивами, схемой, pinned source manifest, tenant scope. Атомарно создать PREPARED, проверить canonical InputSha256. Same scoped key + same payload возвращает существующий handle; другой payload — 409 IDEMPOTENCY_PAYLOAD_CONFLICT.

B. Execute: POST /v1/jobs/{key}/execute с taskCode, immutable CalcPlan/MethodRevision, parameter manifest SHA и ResultShape. Поставить один Job в durable Inbox/queue. Same key + same execution binding → тот же Job; same key + different task/params/plan → 409 IDEMPOTENCY_EXECUTION_CONFLICT.

C. Status: GET /v1/jobs/{key}; PREPARED, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED, ARCHIVING, ARCHIVED, EXPIRED. Result: GET /v1/jobs/{key}/result; до готовности 202 + Retry-After, после завершения typed CalculationResponseDTO.

D. Transactional Outbox: завершение Job, immutable Result и Outbox Event фиксируются атомарно в локальном PostgreSQL. Потребитель повторно получает событие, записывает результат в долговременную БД по idempotent receipt и подтверждает ACK с ResultSha256. Exactly-once CPU или доставка не обещаются; гарантировать единственный committed outcome на scoped key с fencing/unique constraints.

E. Cleanup: PREPARED без запуска истекает через 3 часа от регистрации. SUCCEEDED result payload допускается очищать не ранее чем через 3 часа после финализации при доказанной архивной записи. RUNNING/QUEUED не чистить без terminal transition. Lightweight key tombstone и аудит держать дольше (проектный ориентир ≥7 дней; потребуется утверждение). Истечение 3 часов не отменяет идемпотентность.

Scope key = (tenantId, clientNamespace, idempotencyKey); ключ не служит credential. Расчёт может включать несколько независимых result sets, но immutable execution binding должен зафиксировать точный состав задач. Для другого taskCode использовать другой key либо заранее зарегистрированный versioned composite taskCode.

## 3. Канонические типы входов, параметров и единиц

| Тип | Wire DTO | Единица / контроль |
|---|---|---|
| DECIMAL | canonical decimal string | precision/scale + roundingPolicy, no JSON float |
| MONEY | decimal string + currencyCode | ISO 4217, signPolicy, рабочая vs display scale |
| RATE | decimal string, доля единицы | 0.12 = 12%, nominal/effective/discount basis обязателен |
| PERCENT | decimal string, шкала 0..100 | не путать с RATE/ratio |
| RATIO | decimal string, безразмерный | 0.5 ≠ 50% без явного преобразования |
| QUANTITY | decimal string + unitCode | шт/кг/м/ч; версия конверсии единиц |
| INTEGER | JSON integer | индексы, дни, periods; диапазон проверять |
| INT64 | decimal integer string | eventSequence/timestamp index без JS precision loss |
| BOOLEAN | true/false | null и false отличаются |
| STRING | UTF-8 string | только метки/основания, не исполняемый код |
| CODE/ENUM | allowlisted string | status, method, classification, dayCount |
| REFERENCE/UUID | canonical string | stable business key / source revision |
| LOCAL_DATE | YYYY-MM-DD | accounting asOf / maturity / due dates |
| INSTANT | UTC ISO8601 Z | postedAt, source event order |
| ZONED_DATETIME | INSTANT + zoneId | only when operational calendar requires |
| PERIOD | {kind,start,end,asOf,calendarRevision} | AS_OF vs INTERVAL; never SUM stocks across dates |
| DATE_RANGE | {from,to,boundary} | [from,to) при accrual unless policy states otherwise |
| DURATION / DAY_COUNT | integer days + convention | ACT/365F, ACT/360, ACT/ACT etc only when approved |
| CURRENCY_PAIR/FX | from/to/rate/sourceDate/revision | no implicit conversion |
| ENUM_SET | allowlisted CODE[] | categories, included cash events |
| LIST<T> / STRUCT | versioned typed arrays/objects | bounded sizes/depth, schema validation |
| DIMENSIONS | typed key-value list | organization/project/item/segment/warehouse |
| HASH / EVIDENCE_REF | 64-hex SHA256 / reference | exact source, method, artifact, result |
| VALUE_STATE | PRESENT/EXPLICIT_NULL/MISSING/NOT_APPLICABLE/INVALID | zero is PRESENT "0"; no silent defaults |

Каждый InputFieldContract требует fieldCode, logicalType, precision, scale, unitCode, currency policy, period kind, nullable/valueStatePolicy, requiredness (REQUIRED/CONDITIONAL/OPTIONAL), cardinality, source binding revision и semantic role. Для MONETARY никакой f32/f64. Для nonfinancial stochastic scenario models (позже) возможна отдельная числовая политика, не переносимая автоматически на денежные результаты.

### 3.1. Универсальный пакет InputBatchDTO

InputBatchDTO = {contractVersion, tenantContextRef, sourceManifestRef, datasetSchemas[], datasets[], inputSha256}. Каждый datasets[] элемент — InputDatasetDTO:

| Поле | Тип | Смысл |
|---|---|---|
| datasetId, datasetType, schemaRevision | REFERENCE, CODE, CODE | тип и frozen версия таблицы данных |
| rowCount, rowKeys[] | INTEGER, REFERENCE[] | одна длина для всех колонок; rowKeys уникальны |
| columns[] | InputColumnDTO[] | колонные массивы, не свободный JSON |
| scope, period, currency | STRUCT / PERIOD / CODE | same tenant, time and monetary basis |
| sourceRevisionRefs[] | REFERENCE[] | exact source revisions, verified on Execute |
| contentSha256 | HASH | canonical contents incl. states/order/metadata |

InputColumnDTO = {fieldCode, logicalType, unitCode?, currencyCode?, precision?, scale?, values[], states[], sourceFieldRevisionRef?}. Для PRESENT значение не null, для MISSING/EXPLICIT_NULL/NOT_APPLICABLE значение null и отдельное state. Логический порядок event series фиксируется по effectiveAt, postedAt, eventSequence и deterministic tie breaker. Разные datasets[] могут иметь разные rowCount, их объединяют по typed business keys.

### 3.2. Системные параметры ModelParametersDTO

ParameterValueDTO = {code,type,unitCode?,value,state,policyRevisionRef,sourceEvidenceRef?,effectiveRange?}. Модель получает map parameterCode → typed parameter, а effectiveManifest включает все defaults, resolved approved policies и overrides. Никаких отсутствующих «неявных» defaults в хеше.

Общие параметры: asOf(PERIOD), calendarRevision(REF), reportingBasis(ENUM IFRS/MANAGEMENT), currency(CODE), numberPrecision(INTEGER), roundingMode(ENUM), roundingStage(ENUM), finalScale(INTEGER), missingPolicy(ENUM), signPolicy(ENUM), orderingPolicy(ENUM), scopeRef(REF), sourceHash(HASH), methodRevisionRef(REF), algorithmArtifactHash(HASH), resultShape(ENUM), resourceBounds(STRUCT), deduplicationPolicy(ENUM), dataSpace(ENUM).

## 4. Библиотека входных dataset schemas для всех 14 моделей

Ниже перечислены исходные **проектные** DTO: существующие поля FIN могут иметь другой уровень детализации. Наличие файла/поля в FIN не означает готовность этих 14 inputs. R — required, C — conditional, O — optional; рядом с названиями приведён тип каждого поля.

### D01. OBLIGATION
obligationKey(REFERENCE R), side(ENUM AR/AP R), contractRef(REFERENCE R), recognizedAmount(MONEY R), currencyCode(CODE R), recognitionDate(LOCAL_DATE R), status(ENUM R), sourceRevisionRef(REFERENCE R), counterpartyRef(REFERENCE O), accountingClass(CODE C), effectiveFrom(LOCAL_DATE C), componentEligibilityRef(REFERENCE C).
Invariant: recognizable amount cannot be counted twice alongside installment components.

### D02. INSTALLMENT
installmentKey(REFERENCE R), obligationKey(REFERENCE R), component(ENUM PRINCIPAL/INTEREST/FEE/OTHER R), dueAmount(MONEY R), effectiveDueDate(LOCAL_DATE R), currencyCode(CODE R), sourceRevisionRef(REFERENCE R), originalScheduleRef(REFERENCE O), partialPaymentAllowed(BOOLEAN C). INSTALLMENT grain — contractual payment unit, not full invoice duplicate.

### D03. SETTLEMENT
eventKey(REFERENCE R), obligationKey(REFERENCE R), type(ENUM PAYMENT/REFUND/REVERSAL/WRITE_OFF/ADJUSTMENT R), amount(MONEY R, positive magnitude), currencyCode(CODE R), effectiveDate(LOCAL_DATE R), postedAt(INSTANT R), externalEventKey(REFERENCE R), sequence(INT64 R), sourceSystem(CODE R), evidenceRef(REFERENCE R), originalEventRef(REFERENCE C for reversals), sourceRevisionRef(REFERENCE R).

### D04. ALLOCATION
allocationKey(REFERENCE R), eventKey(REFERENCE R), installmentKey(REFERENCE R), allocatedAmount(MONEY R), effectiveDate(LOCAL_DATE R), allocationOrder(INTEGER R), policyRevisionRef(REFERENCE R), sourceRevisionRef(REFERENCE R). Required for EXPLICIT_POSTED; otherwise generation must be permitted by specific policy, never guessed.

### D05. AMENDMENT
amendmentKey(REFERENCE R), obligationKey(REFERENCE R), installmentKey(REFERENCE C), effectiveDate(LOCAL_DATE R), postedAt(INSTANT R), revisedDueDate(LOCAL_DATE C), revisedAmount(MONEY C), amendmentType(ENUM R), supersedesRevisionRef(REFERENCE R), sourceEvidenceRef(REFERENCE R), sequence(INT64 R). No history rewrite.

### D06. LOAN
loanBusinessKey(REFERENCE R), contractRevisionRef(REFERENCE R), principal(MONEY R), currencyCode(CODE R), contractDate(LOCAL_DATE R), accrualStart(LOCAL_DATE R), maturity(LOCAL_DATE R), repaymentMethod(ENUM ANNUITY/EQUAL_PRINCIPAL/CUSTOM R), paymentFrequency(ENUM R), calendarRevisionRef(REFERENCE R), direction(ENUM BORROWER/LENDER R), accountingBasis(ENUM R), sourceSha256(HASH R), endOfMonthRule(ENUM C), fundingDate(LOCAL_DATE C).

### D07. RATE_RULE
rateRuleKey(REFERENCE R), loanBusinessKey(REFERENCE R), effectiveFrom(LOCAL_DATE R), effectiveTo(LOCAL_DATE C), rateType(ENUM FIXED/FLOATING/STEP R), nominalAnnualRate(RATE C for FIXED/STEP), referenceRateRevisionRef(REFERENCE C for FLOATING), spread(RATE C), floor(RATE C), cap(RATE C), dayCount(ENUM R), compoundingRule(ENUM R), resetCalendarRef(REFERENCE C), sourceRevisionRef(REFERENCE R).

### D08. LOAN_FEE
feeKey(REFERENCE R), loanBusinessKey(REFERENCE R), eventDate(LOCAL_DATE R), amount(MONEY R), feeType(ENUM R), payerPayee(ENUM R), deductedAtFunding(BOOLEAN R), cashClassification(ENUM R), eirEligibility(ENUM INCLUDED/EXCLUDED/UNREVIEWED R), accountingPolicyRef(REFERENCE R), evidenceRef(REFERENCE R), sourceRevisionRef(REFERENCE R).

### D09. LOAN_CASH_EVENT
eventKey(REFERENCE R), loanBusinessKey(REFERENCE R), eventDate(LOCAL_DATE R), type(ENUM DRAW/PRINCIPAL/INTEREST/FEE/OTHER R), amount(MONEY R), planActual(ENUM PLANNED/ACTUAL R), currencyCode(CODE R), sourceRevisionRef(REFERENCE R), relatedObligationKey(REFERENCE C), originalEventRef(REFERENCE C). Cash directions are governed by position perspective.

### D10. CASH_OPENING
cashScopeRef(REFERENCE R), asOf(LOCAL_DATE R), openingCash(MONEY R), currencyCode(CODE R), basis(ENUM R), sourceRevisionRef(REFERENCE R), scenarioRef(REFERENCE C). Stock snapshot, not cash event.

### D11. CASH_EVENT
eventKey(REFERENCE R), cashScopeRef(REFERENCE R), valueDate(LOCAL_DATE R), postedAt(INSTANT C for ACTUAL), amount(MONEY R positive magnitude), direction(ENUM INFLOW/OUTFLOW R), cashClass(ENUM OPERATING/INVESTING/FINANCING/FX_EFFECT/INTERNAL_TRANSFER R), eventStatus(ENUM POSTED/FORECAST/VOID R), cashAccountRef(REFERENCE R), sourceRevisionRef(REFERENCE R), scenarioRef(REFERENCE C), originalEventRef(REFERENCE C), probability(RATE C only for separately approved probabilistic variant).

### D12. CFO_BRIDGE
bridgeKey(REFERENCE R), period(PERIOD R), basis(ENUM R), adjustmentType(ENUM NET_INCOME/NONCASH/OPERATING_ASSET_DELTA/OPERATING_LIABILITY_DELTA/RECLASSIFICATION/OTHER R), signedAmount(MONEY R), sourceMetricRef(REFERENCE R), sourceRevisionRef(REFERENCE R), adjustmentEvidenceRef(REFERENCE R), workingCapitalPolicyRef(REFERENCE C).

### D13. DCF_FLOW
projectRef(REFERENCE R), scenarioRef(REFERENCE R), cashflowRef(REFERENCE R), periodIndex(INTEGER >=0 R), cashflowAmount(MONEY signed R), currencyCode(CODE R), basis(ENUM PROJECT/FCFF/FCFE R), sourceRevisionRef(REFERENCE R), eventDate(LOCAL_DATE C for dated model), sourceCategory(CODE O). Multiple flows per period require explicit aggregation and no duplicate t=0 investment.

### D14. STOCK_LOT
lotKey(REFERENCE R), itemKey(REFERENCE R), warehouseRef(REFERENCE R), openingDate(LOCAL_DATE R), openingQty(QUANTITY R), quantityUnit(CODE R), openingUnitCost(MONEY/QUANTITY R), currencyCode(CODE R), sourceRevisionRef(REFERENCE R), itemAccountingClass(CODE C). Inventory source is by item and location.

### D15. STOCK_MOVEMENT
movementKey(REFERENCE R), itemKey(REFERENCE R), warehouseRef(REFERENCE R), lotKey(REFERENCE C), effectiveAt(INSTANT R), eventSequence(INT64 R), movementType(ENUM RECEIPT/ISSUE/RETURN/TRANSFER/ADJUSTMENT/REVERSAL R), quantity(QUANTITY positive R), quantityUnit(CODE R), receiptUnitCost(MONEY/QUANTITY C for RECEIPT), currencyCode(CODE R), originalMovementKey(REFERENCE C for RETURN/REVERSAL), destinationWarehouseRef(REFERENCE C for TRANSFER), sourceRevisionRef(REFERENCE R), posted(BOOLEAN R).

Контракты D01-D15 не являются новым финансовым writer: они описывают транспортные и compute-view DTO над immutable verified source, не записывают состояние в FIN intake.

## 5. Индивидуальные технические задания — Wave-1

Каждая модель имеет отдельную code/revision и отдельный список зависимостей. В вариантах обязательность CONDITIONAL активируется методическим выбором, а не отсутствием поля в форме FIN. Все числовые тестовые примеры ниже синтетические, для проверки правил до независимого финансового утверждения.


### 01. HC.SET.01 — Реконструкция остатка дебиторской задолженности

**Task:** W1.SET.AR_BALANCE.V1. **Связь с FIN:** C01; C11; DF-CSH-02/04; A01. **ResultShape:** ROW_ALIGNED + AGGREGATE. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D01(side AR), D02, D03; D04 при EXPLICIT_POSTED; D05 при изменении графика. Контекст asOf/period, original recognition и source revisions. |
| Типизированные параметры | allocationMethod(ENUM EXPLICIT_POSTED/EARLIEST_DUE), asOf(LOCAL_DATE), recognizedComponentSet(ENUM_SET), effectiveVsPostingCutoff(ENUM), reversalPolicyRef(REFERENCE), overpaymentPolicy(ENUM), roundingPolicyRef(REFERENCE). |
| Правило вычисления | Выбрать признанные обязательства и верифицированные event revisions на asOf; определить due installments, применить settlement allocations/corrections, исключить отменённые economic events. OpenAR = eligible initial recognized amount ± valid adjustments − applied settlements − authorized write-offs, без ECL allowance. Не вычитать payment повторно из already-paid-down snapshot. |
| Выходные поля и типы | AR_OPEN_BALANCE(MONEY per obligation), AR_PORTFOLIO_OPEN(MONEY per scope), RECONCILIATION_DIFFERENCE(MONEY), UNALLOCATED_PAYMENT(MONEY), AS_OF(LOCAL_DATE). |
| Синтетический golden пример | 100 KZT invoice, один payment 40 KZT, no write-off → AR_OPEN_BALANCE 60 KZT. |
| Ошибки и блокировки | Duplicate externalEventKey; payment>balance without policy; missing obligationKey; mismatched currency; source revised after pin; double paid-down adjustment. |
| Проверяемый invariant | SUM per-installment unpaid = per-obligation output и затем portfolio output при совпадающем currency/asOf; no double counting. Finance status CANDIDATE. |


### 02. HC.SET.02 — Реконструкция остатка кредиторской задолженности

**Task:** W1.SET.AP_BALANCE.V1. **Связь с FIN:** C02; C11; DF-CSH-02/05; A01. **ResultShape:** ROW_ALIGNED + AGGREGATE. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D01(side AP), D02, D03; conditional D04/D05. Supplier advances and recognised tax/penalty components must have separately typed classification. |
| Типизированные параметры | asOf(LOCAL_DATE), allocationMethod(ENUM), payableRecognitionPolicyRef(REFERENCE), supplierAdvanceOffset(ENUM DISALLOW/QUALIFIED_ONLY), componentPolicyRef(REFERENCE), currencyPolicy(ENUM STRICT_SAME_CURRENCY). |
| Правило вычисления | AP = eligible recognized unpaid contractual obligations after verified posted payments and amendments. Supplier advances or credit balances are separately classified; counterparty matching does not imply legal offset. Financial instruments can require another valuation method. |
| Выходные поля и типы | AP_OPEN_BALANCE(MONEY), AP_PORTFOLIO_OPEN(MONEY), UNMATCHED_ADVANCE(MONEY separate scope), RECONCILIATION_DIFFERENCE(MONEY). |
| Синтетический golden пример | 250 KZT payable, payment 75 KZT → AP 175 KZT. Separate 30 KZT supplier advance does not automatically reduce AP. |
| Ошибки и блокировки | Unapproved supplier offset; duplicate invoice business key; currency mismatch; negative positive-stock AP; unreviewed tax/interest inclusion. |
| Проверяемый invariant | Portfolio total equals aggregate of eligible obligations, not net of unrelated advances; dated revisions immutable. |


### 03. HC.SET.03 — Aging, дни и сумма просрочки по взносам

**Task:** W1.SET.AGING.V1. **Связь с FIN:** C01; C02; DF-CSH; A01. **ResultShape:** ROW_ALIGNED + GROUPED. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D02 installment, reconciled D01–D05 or pinned outputs from HC.SET.01/02. effectiveDueDate after valid amendments, outstanding amount asOf. |
| Типизированные параметры | asOf(LOCAL_DATE), graceDays(INTEGER >=0), bucketBoundaries(LIST<INTEGER> strictly ascending), bucketAssignmentPolicy(ENUM), compareDueDatePolicy(ENUM), calendarRevisionRef(REFERENCE), groupingCurrencyPolicy(ENUM). |
| Правило вычисления | Unpaid eligible due amount is allocated from dated obligations/settlements. daysPastDue=max(0,calendarDays(asOf-effectiveDueDate)−graceDays), subject to due-date cutoff. Overdue MONEY includes only installments satisfying overdue rule; bucket by nonoverlapping age intervals, not by invoice gross. |
| Выходные поля и типы | DAYS_PAST_DUE(INTEGER DAYS), OVERDUE_AMOUNT(MONEY), AGING_BUCKET_AMOUNT(MONEY per bucket), NOT_YET_DUE_AMOUNT(MONEY). |
| Синтетический golden пример | Installment 100 with effective due 10th, paid 40; installment 50 due 30th. On 20th, no grace → overdue amount 60 KZT, second not overdue. |
| Ошибки и блокировки | Unsorted/overlapping buckets; due-date amendment ignored; asOf before recognition; mixed currencies in bucket; absence of settlement mapping. |
| Проверяемый invariant | One unpaid installment occupies at most one bucket, sum overdue buckets equals all overdue amounts, overdue<=eligible outstanding for positive pilot. |


### 04. HC.SET.06 — Replay частичных погашений, возвратов и сторно

**Task:** W1.SET.REPLAY.V1. **Связь с FIN:** A01; DF-CSH-02/04/05. **ResultShape:** EVENT_SERIES + ROW_ALIGNED. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D01, D02, D03 and conditional D04/D05; unique external event identity, effectiveAt and postedAt plus ordered source revision chain. |
| Типизированные параметры | eventOrderPolicy(ENUM), reversalMatchingPolicy(ENUM EXACT_ORIGINAL), allocationPolicyRef(REFERENCE), cutoff(LOCAL_DATE), overpaymentPolicy(ENUM FAIL/SEPARATE_ADVANCE), tieBreaker(ENUM). |
| Правило вычисления | Validate immutable event graph, reject cycles; replay eligible payments/repayments and inverse effects of exact referenced reversals; allocate to approved installments; compute applied and unapplied cash after each event. |
| Выходные поля и типы | BALANCE_AFTER_EVENT(MONEY), APPLIED_SETTLEMENT(MONEY), REVERSAL_EFFECT(MONEY), UNALLOCATED_CASH(MONEY), EVENT_SEQUENCE(INT64), FINAL_OPEN_BALANCE(MONEY). |
| Синтетический golden пример | Obligation 100, payment 40, full reversal of original payment → residual 100. Reposting same external event must not add money. |
| Ошибки и блокировки | Double reversal; reversal of unknown event; ambiguous same-time event ordering; negative balance; duplicate external ID with different payload. |
| Проверяемый invariant | Replay from same source SHA/order yields byte-identical financial rows and result hash. Old version never mutated. |


### 05. HC.LOAN.01 — График договорных процентов

**Task:** W1.LOAN.INTEREST.V1. **Связь с FIN:** C05; P04; A05. **ResultShape:** TIME_SERIES. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D06 loan terms, D07 rate rules, D09 cash events (drawdown/principal), conditional D08 fees only if contractual cash payment included separately. Exact date-ranged rate version. |
| Типизированные параметры | dayCountConvention(ENUM ACT/365F/ACT/360/ACT/ACT/30E360), accrualBoundary(ENUM [START,END)), compoundingRule(ENUM SIMPLE/COMPOUND), rateResetPolicy(ENUM), businessDayCalendarRef(REFERENCE), roundingStage(ENUM), interestScale(INTEGER). |
| Правило вычисления | Split accrual intervals when nominal rate, principal or effective contract changes. SIMPLE interest for segment = outstanding principal × nominal annual RATE × approved day-count fraction. Never substitute EIR for contractual nominal interest. |
| Выходные поля и типы | ACCRUED_CONTRACT_INTEREST(MONEY per dated period), OPENING_PRINCIPAL(MONEY), CLOSING_PRINCIPAL(MONEY), NOMINAL_RATE(RATE), ACCRUAL_START/END(LOCAL_DATE). |
| Синтетический golden пример | 1000 KZT, nominal RATE=0.12, ACT/365F, 30 actual days unchanged → 1000×0.12×30/365=9.8630136986… KZT before approved rounding. |
| Ошибки и блокировки | Overlapping rate intervals; missing index reset; principal event boundary omitted; date convention unknown; mixing loan/fee/EIR interest. |
| Проверяемый invariant | Each accrual day segment covered exactly once, no overlapping interest on same principal balance. |


### 06. HC.LOAN.02 — Аннуитетный/дифференцированный график основного долга

**Task:** W1.LOAN.PRINCIPAL.V1. **Связь с FIN:** C05; P04; A05. **ResultShape:** TIME_SERIES. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D06 loan, D07 rate rules, conditional D09 disbursement/payment events and D08 fees. One loanBusinessKey and pinned contract revision. |
| Типизированные параметры | repaymentMethod(ENUM ANNUITY/EQUAL_PRINCIPAL/CUSTOM), frequency(ENUM), dateShiftRule(ENUM), EOMRule(ENUM), dayCountConvention(ENUM), finalResidualRule(ENUM), earlyRepaymentRule(ENUM), negativeAmortizationPolicy(ENUM), paymentScale(INTEGER). |
| Правило вычисления | Construct due dates; compute nominal interest from HC.LOAN.01 methodology; compute principal/payment schedule. For truly equal fixed periods ANNUITY A=P*r/(1−(1+r)^−n), r=0→P/n; irregular periods need dated solver variant. Enforce opening + draws − principal repayments ± approved adjustments = closing. |
| Выходные поля и типы | SCHEDULED_PRINCIPAL(MONEY), SCHEDULED_INTEREST(MONEY), CASH_PAYMENT_TOTAL(MONEY), OPENING/CLOSING_PRINCIPAL(MONEY), DUE_DATE(LOCAL_DATE). |
| Синтетический golden пример | Equal-principal principal 1200 KZT in 12 periods, zero interest → principal 100 each, closing balance 0 at final period. |
| Ошибки и блокировки | Periods=0; unscheduled balloon; stale reset rates; silent negative amortization; calendar shift affecting accrual without rule; nonzero rounding residual. |
| Проверяемый invariant | Sum principal repayments equals disbursed principal plus explicit adjustments by final date; cash interest separate from EIR. |


### 07. HC.LOAN.03 — IFRS effective interest rate EIR

**Task:** W1.LOAN.EIR.V1. **Связь с FIN:** C05; F01/F02; A05. **ResultShape:** AGGREGATE + TIME_SERIES. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D06, D08 (each fee with EIR eligibility status), D09 dated cash flows, approved initial carrying amount(MONEY) and source/valuation policy revision. Unknown EIR eligibility blocks. |
| Типизированные параметры | initialCarryingAmount(MONEY source-bound), cashflowEligibilityPolicyRef(REFERENCE), discountOriginDate(LOCAL_DATE), yearFractionConvention(ENUM), solverMinRate/MaxRate(RATE), residualTolerance(MONEY), rateTolerance(RATE), maxIterations(INTEGER), solverVersion(CODE), multipleRootsPolicy(ENUM). |
| Правило вычисления | For eligible financial instrument solve initial carrying amount = Σ permitted dated future cash flows/(1+r)^fraction under pinned cashflow direction and EIR method. Validate residual and root ambiguity. Accounting amortized-cost schedule is separate output; contractual nominal rate and KZ GESV are different metrics. |
| Выходные поля и типы | EIR_RATE(RATE), EIR_RESIDUAL(MONEY), SOLVER_ITERATIONS(INTEGER), AMORTIZED_COST(MONEY per period, conditional). |
| Синтетический golden пример | Illustrative exactly one-year 980 KZT initial carrying, 1080 KZT due cash → EIR =1080/980−1≈0.10204081632653, not normative endorsement of eligible fees. |
| Ошибки и блокировки | No initial carrying evidence; unreviewed fee; no/multiple root; wrong signed cash direction; missing dated payment; nonconvergence beyond tolerance. |
| Проверяемый invariant | EIR root residual within preapproved money tolerance, no automatic IFRS financial S2 or regulatory GESV claim. |


### 08. HC.CASH.01 — 13-недельный прогноз ликвидности

**Task:** W1.CASH.WEEK13.V1. **Связь с FIN:** DF-CSH-01/02/03; P03; CFO-02. **ResultShape:** TIME_SERIES. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D10 opening balance + D11 cash events (POSTED/FORECAST distinguishable), exact cash scope/calendar, scenario and evidence of commitments. |
| Типизированные параметры | horizonWeeks(INTEGER 13 pilot), weekCalendarRef(REFERENCE), weekStartDay(ENUM), snapshotDate(LOCAL_DATE), scenarioRef(REFERENCE), includeTentativeEvents(BOOLEAN by policy), safetyBuffer(MONEY), interaccountTransferPolicy(ENUM), FXPolicyRef(REFERENCE C). |
| Правило вычисления | For every week B_w = B_(w−1) + eligible receipts − eligible payments + explicit permitted non-flow effects. Respect actual vs forecast boundaries, inter-account transfer elimination and currency scope. |
| Выходные поля и типы | WEEK_OPEN(MONEY), WEEK_INFLOW(MONEY), WEEK_OUTFLOW(MONEY), WEEK_CLOSE(MONEY), BUFFER_GAP(MONEY), WEEK_START/END(LOCAL_DATE). |
| Синтетический golden пример | Opening 100 KZT, receipts30, payments45 in first week → closing 85. Full 13-week continuity required. |
| Ошибки и блокировки | Double forecast/posted same event; transfer counted twice; calendar gap; missing opening; wrong FX; events duplicated. |
| Проверяемый invariant | Exactly 13 contiguous week rows per authorized entity/scenario; closing_week[n]=opening_week[n+1]. |


### 09. HC.CASH.04 — Операционный денежный поток прямым методом

**Task:** W1.CASH.CFO_DIRECT.V1. **Связь с FIN:** F03; C06; C07; A01. **ResultShape:** GROUPED + AGGREGATE. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D11 cash events POSTED with source/economic classification, exact cash account, interval and revisions; conditional posted reclassification events. |
| Типизированные параметры | reportPeriod(PERIOD INTERVAL), operatingCashClasses(ENUM_SET), cashClassificationPolicyRef(REFERENCE), internalTransferTreatment(ENUM EXCLUDE), cashDateRule(ENUM), sourceBasis(CODE), FXPolicyRef(REFERENCE C). |
| Правило вычисления | CFO_DIRECT=Σ eligible posted OPERATING INFLOW − Σ eligible posted OPERATING OUTFLOW. Exclude financing/investing/internal transfers and reversed/deduplicated events as per admitted contract. |
| Выходные поля и типы | CFO_DIRECT(MONEY), OPERATING_RECEIPTS(MONEY), OPERATING_PAYMENTS(MONEY), CASH_CLASS(CODE grouped). |
| Синтетический golden пример | Operating inflow100, operating outflow70, internal transfer20 → CFO direct=30 KZT. |
| Ошибки и блокировки | Missing category; two ledger copies; actual/forecast mixing; transfer leak; wrong value date; mixed currency. |
| Проверяемый invariant | Sum category subtotals equals CFO direct, event lineage trace; no duplicate cash movements. |


### 10. HC.CASH.05 — Операционный денежный поток косвенным методом

**Task:** W1.CASH.CFO_INDIRECT.V1. **Связь с FIN:** F02; F03; P06. **ResultShape:** GROUPED + AGGREGATE. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D12 CFO bridge with exactly one approved net income reference and noncash/working capital changes from comparable snapshots, pinned accounting basis. |
| Типизированные параметры | reportPeriod(PERIOD), incomeBasis(CODE), nonCashClasses(ENUM_SET), workingCapitalClasses(ENUM_SET), accountingSignPolicyRef(REFERENCE), classificationPolicyRef(REFERENCE), reconciliationTolerance(MONEY), FXBridgeRef(REFERENCE C). |
| Правило вычисления | CFO_INDIRECT = NI + noncash adjustments − Δ eligible operating current assets + Δ eligible operating liabilities ± approved reclassification effects. Δ=closing−opening; do not include Cash in working-capital assets; avoid double-counted adjustments. |
| Выходные поля и типы | CFO_INDIRECT(MONEY), NET_INCOME(MONEY), NONCASH_EFFECT(MONEY), ASSET_CHANGE_EFFECT(MONEY), LIABILITY_CHANGE_EFFECT(MONEY), BRIDGE_DIFFERENCE(MONEY conditional). |
| Синтетический golden пример | NI20 + depreciation5 − ΔAR(−3) + ΔAP(+2) = CFO30 KZT. |
| Ошибки и блокировки | Missing opening stock; wrong sign; IFRS/MANAGEMENT mixing; repeated NI; cash asset included as WC; direct/indirect not comparable. |
| Проверяемый invariant | Same time/basis/currency must match direct method within approved tolerance, else explicit NOT_COMPARABLE or DIFFERENCE. |


### 11. HC.DCF.01 — NPV периодических денежных потоков

**Task:** W1.DCF.NPV.V1. **Связь с FIN:** P07; P03; P05; INV-05; A06. **ResultShape:** TIME_SERIES + AGGREGATE. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D13 DCF_FLOW per project/scenario with periodIndex, signed flow and explicit flowBasis PROJECT/FCFF/FCFE, same currency and period unit. |
| Типизированные параметры | periodicDiscountRate(RATE), ratePeriodUnit(ENUM YEAR/MONTH/etc), valuationPeriodIndex(INTEGER), cashflowTiming(ENUM END/BEGIN), flowBasis(ENUM), discountPolicyRef(REFERENCE), roundingPolicyRef(REFERENCE). |
| Правило вычисления | NPV = Σ CF_t /(1+r)^(t−t0), rate period matches exact period unit, r>−1 and t0 correctly included. For enterprise valuation FCFF + WACC; for equity FCFE + Ke; arbitrary mismatches are blocked. |
| Выходные поля и типы | NPV(MONEY aggregate), DISCOUNTED_CASHFLOW(MONEY per period), DISCOUNT_FACTOR(DECIMAL), CUMULATIVE_PV(MONEY). |
| Синтетический golden пример | Cashflows [-100,60,60], r=0.10, t=0,1,2 → NPV≈4.1322314049587 KZT before output rounding. |
| Ошибки и блокировки | r<=−1; missing t=0; duplicate flow without grouping; nominal vs real mismatch; currency or time-basis mismatch. |
| Проверяемый invariant | Sum discounted cashflows equals aggregate NPV at pinned working precision, independent golden residual. |


### 12. HC.DCF.03 — Все допустимые корни IRR

**Task:** W1.DCF.IRR_ROOTS.V1. **Связь с FIN:** P07; INV-05; A06. **ResultShape:** ROOT_SET. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D13 DCF_FLOW, same project/scenario and periodic times, signed money, exact t0 and declared root search domain. |
| Типизированные параметры | domainMinRate(RATE >−1), domainMaxRate(RATE), rateTolerance(RATE), residualTolerance(MONEY), maxIterations(INTEGER), rootIsolationMethod(CODE), multipleRootsPolicy(ENUM RETURN_ALL/BLOCK_SINGLE), solverVersion(CODE). |
| Правило вычисления | Find all *certified* real roots of NPV(r)=0 in defined domain. Sign-change scanning alone misses tangent/repeated roots; if completeness not proven return PARTIAL_ROOT_SEARCH rather than claiming all. When no root, return ROOT_SET with empty rows and NO_ROOT state. |
| Выходные поля и типы | IRR_ROOT(RATE per root), NPV_RESIDUAL(MONEY), ROOT_ORDER(INTEGER), ITERATIONS(INTEGER), ROOT_SET_STATUS(CODE). |
| Синтетический golden пример | [-100,230,-132] with t=0/1/2 → r1=0.10 and r2=0.20; both satisfy NPV≈0. |
| Ошибки и блокировки | No roots; double root without sign change; root outside domain; multiple roots with forced single policy; unstable numeric solver. |
| Проверяемый invariant | Every returned root has verified residual; distinct roots sorted and deduplicated only by approved rate tolerance. |


### 13. HC.STOCK.01 — FIFO оценка списаний по партиям

**Task:** W1.STOCK.FIFO.V1. **Связь с FIN:** C03; DF-STK-02/03; A03. **ResultShape:** EVENT_SERIES + GROUPED. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D14 opening lots + D15 movements ordered by item/warehouse/date/sequence, receipt cost and unit conversion policy. |
| Типизированные параметры | valuationMethod(ENUM FIFO), asOf(LOCAL_DATE), stockBelowZeroPolicy(ENUM FAIL), eventOrderingPolicy(ENUM), returnCostPolicy(ENUM RESTORE_ORIGINAL_LAYER), transferPolicyRef(REFERENCE), unitConversionRef(REFERENCE), costRoundingPolicyRef(REFERENCE). |
| Правило вычисления | Issue consumes oldest eligible cost layers in deterministic order. ISSUE_COST=Σ takenQty×layerUnitCost; returns/reversals restore exact referenced layers as governed by accepted policy; transfers trace both warehouse sides. |
| Выходные поля и типы | ISSUE_COST(MONEY), LAYER_CONSUMED_QTY(QUANTITY), REMAINING_QTY(QUANTITY), REMAINING_COST(MONEY), LOT_REF(REFERENCE). |
| Синтетический golden пример | Receive 10 units@100, then 10 units@120; issue12 → FIFO cost1240, remaining 8 units@120=960 KZT. |
| Ошибки и блокировки | Negative inventory; duplicate lot event; return without original cost; unknown unit; same time ambiguous sequence; currency mismatch. |
| Проверяемый invariant | Opening value + receipts − issued cost ± approved adjustments = closing value with controlled rounding; unit conservation per item/warehouse. |


### 14. HC.STOCK.02 — Скользящая средневзвешенная себестоимость

**Task:** W1.STOCK.WAC_MOVING.V1. **Связь с FIN:** C03; DF-STK-02/03; A03. **ResultShape:** EVENT_SERIES + GROUPED. **Статус:** DRAFT / NOT S2.

| Контракт | Точное проектное требование |
|---|---|
| Входные массивы | D14 lots + D15 same ordered movement dataset as FIFO but distinct method/contract revision; unit equivalence required. |
| Типизированные параметры | valuationMethod(ENUM MOVING_WAC), asOf(LOCAL_DATE), averagingScope(ENUM ITEM_WAREHOUSE), precisionScale(INTEGER), unitCostRoundingStage(ENUM), receiptPolicyRef(REFERENCE), returnCostPolicyRef(REFERENCE), stockBelowZeroPolicy(ENUM FAIL). |
| Правило вычисления | On receipt update weightedUnitCost=(previousQty×previousUnitCost+receiptQty×receiptUnitCost)/(previousQty+receiptQty); on issue cost=issueQty×currentWeightedUnitCost. Do not accidentally replace MOVING WAC by PERIODIC weighted average. |
| Выходные поля и типы | WAC_UNIT_COST(MONEY/QUANTITY), ISSUE_COST(MONEY), REMAINING_QTY(QUANTITY), REMAINING_COST(MONEY) per movement. |
| Синтетический golden пример | Receive10@100, then10@120, issue12 → moving WAC=110, issue cost1320, closing 8 units value880 KZT. |
| Ошибки и блокировки | Quantity denominator 0; premature rounding drift; negative stock; unlinked return; same-event order ambiguity; incorrect unit conversion. |
| Проверяемый invariant | Per-movement inventory value reconciles, and expected difference from FIFO is accepted as methodology difference (not parity error). |


## 6. Единый массив результатов: Output DTO v1

Единый root CalculationResponseDTO:
- contractVersion: CODE, значение FENGINE-W1-OUTPUT-V1;
- idempotencyKey: REFERENCE, scoped key из request;
- jobId: REFERENCE, immutable registered job;
- jobState: ENUM PREPARED/QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED/ARCHIVED/EXPIRED;
- inputSha256, executionBindingSha256, calcPlanSha256, algorithmManifestSha256, resultManifestSha256: HASH; для ещё не завершенного расчёта result hash = null с state NOT_READY;
- results: LIST<CalculationResultSetDTO>, **массив** для любого вида расчета, в том числе одного значения;
- errors: LIST<CalculationErrorDTO>, warnings: LIST<CalculationWarningDTO>;
- createdAt, completedAt: INSTANT (completedAt only when terminal);
- retention: {temporaryPayloadExpiresAt?, archiveStatus, archiveReceiptRef?, tombstoneUntil?}.

Каждый CalculationResultSetDTO:
resultSetId(REF), taskCode(CODE), modelCode(HC.* CODE), methodRevisionRef(REF), outputSchemaRevision(CODE), resultShape(ENUM), scope(STRUCT), period(PERIOD), currency(CODE), status(ENUM COMPLETE/PARTIAL/BLOCKED/INVALID/UNDEFINED/NO_ROOT/PARTIAL_ROOT_SEARCH/NOT_APPLICABLE), rows(LIST<CalculatedRowDTO>), sourceLineageRefs(LIST<REF>), resultSetSha256(HASH), diagnostics(LIST<CODE>).

Каждый CalculatedRowDTO:
rowKey(REF), parentRowKey(REF optional), dimensions(DIMENSIONS), period(PERIOD optional), eventDate(LOCAL_DATE optional), ordinal(INTEGER optional), state(ENUM), values(LIST<CalculatedValueDTO>), sourceRowRefs(LIST<REF>), lineageSha256(HASH).

Каждый CalculatedValueDTO:
metricCode(CODE), logicalType(DECIMAL/MONEY/RATE/RATIO/QUANTITY/INTEGER/LOCAL_DATE/CODE etc.), value(typed wire value or null), valueState(ENUM PRESENT/EXPLICIT_NULL/MISSING/NOT_APPLICABLE/INVALID), calculationState(ENUM COMPLETE/UNDEFINED/BLOCKED...), unitCode(CODE), currencyCode(CODE optional), precision(INTEGER optional), scale(INTEGER optional), roundingApplied(ENUM optional), formulaRevisionRef(REF), reasonCode(CODE optional).

ResultShape:
- ROW_ALIGNED: output per source business key.
- GROUPED: output per group/bucket/warehouse.
- TIME_SERIES: output per period; several metrics in same row.
- EVENT_SERIES: output per economic event, with ordered references.
- AGGREGATE: per scope/currency/period group; may contain multiple rows across groups.
- ROOT_SET: zero/multiple root rows and separate root-search status; not coerced to one value.

**Требование:** job SUCCEEDED означает успешное исполнение разрешенного плана, но отдельный model result может быть UNDEFINED, NO_ROOT или PARTIAL по математической/входной причине; это не считается финансово пригодным расчетом без допустимой методики. Для больших массивов допускается бинарное columnar представление с одинаковыми logical DTO и immutable chunk manifest; GET response может быть paginated or streaming.

### 6.1. Иллюстративный Input DTO (сокращенный)

~~~json
{
  "contractVersion":"FENGINE-W1-INPUT-V1",
  "datasets":[{
    "datasetId":"project-one",
    "datasetType":"DCF_FLOW",
    "datasetSchemaRevision":"1",
    "rowCount":3,
    "rowKeys":["cf0","cf1","cf2"],
    "columns":[
      {"fieldCode":"periodIndex","logicalType":"INTEGER","values":[0,1,2],"states":["PRESENT","PRESENT","PRESENT"]},
      {"fieldCode":"cashflowAmount","logicalType":"MONEY","currencyCode":"KZT","values":["-100","230","-132"],"states":["PRESENT","PRESENT","PRESENT"]}
    ],
    "timeContext":{"kind":"INTERVAL","periodUnit":"YEAR"},
    "sourceManifest":{"sourceRef":"pinned-synthetic-ref"}
  }]
}
~~~

Это сокращенное представление **не проходит полную схему**: для исполнения требуются projectRef, scenarioRef, cashflowRef, basis, sourceRevisionRef, scopes and SHA из §3–4; никакого вычисления по нему сейчас не запускалось.

### 6.2. Иллюстративный Execute DTO

~~~json
{
  "taskCode":"W1.DCF.IRR_ROOTS.V1",
  "methodRevisionRef":"versioned-synthetic-method",
  "calcPlanRef":"immutable-UAT-plan",
  "params":[
    {"code":"domainMinRate","type":"RATE","value":"-0.99","state":"PRESENT"},
    {"code":"domainMaxRate","type":"RATE","value":"1.00","state":"PRESENT"},
    {"code":"residualTolerance","type":"MONEY","unitCode":"KZT","value":"0.000001","state":"PRESENT"}
  ],
  "resultShape":"ROOT_SET"
}
~~~

### 6.3. Иллюстративный Output DTO с массивом rows

~~~json
{
  "contractVersion":"FENGINE-W1-OUTPUT-V1",
  "idempotencyKey":"example-key-001",
  "jobId":"example-job-001",
  "jobState":"SUCCEEDED",
  "results":[{
    "resultSetId":"set-1",
    "taskCode":"W1.DCF.IRR_ROOTS.V1",
    "modelCode":"HC.DCF.03",
    "resultShape":"ROOT_SET",
    "status":"COMPLETE",
    "rows":[
      {"rowKey":"root-1","ordinal":1,"values":[{"metricCode":"IRR_ROOT","logicalType":"RATE","value":"0.10","unitCode":"ONE","valueState":"PRESENT","calculationState":"COMPLETE"}]},
      {"rowKey":"root-2","ordinal":2,"values":[{"metricCode":"IRR_ROOT","logicalType":"RATE","value":"0.20","unitCode":"ONE","valueState":"PRESENT","calculationState":"COMPLETE"}]}
    ]
  }],
  "errors":[],
  "warnings":[],
  "retention":{"archiveStatus":"PENDING_ACK"}
}
~~~

JSON выше иллюстрирует структуру arrays; в нем намеренно опущены обязательные security scope, immutable SHA, lineage, method/output revisions и timestamps из полной схемы §6. В production-compatible message все REQUIRED поля валидируются по versioned IDL; приведённый пример не действующий результат выполнения.

## 7. Golden и negative acceptance: 14 обязательных векторов

| Модель | Синтетический числовой пример | Дополнительная приёмка |
|---|---|---|
| SET.01 | 100−40=60 KZT | no double payment / no ECL subtraction |
| SET.02 | 250−75=175 KZT | separate supplier advance |
| SET.03 | unpaid overdue 60 KZT | effective due date and bucket invariance |
| SET.06 | 100−40+reversal40=100 KZT | deterministic exact event chain |
| LOAN.01 | 1000×0.12×30/365=9.8630136986… KZT | day-count and rounding |
| LOAN.02 | 1200/12=100 KZT scheduled principal | full 12-row roll-forward |
| LOAN.03 | 1080/980−1≈0.10204081632653 RATE | fee eligibility + solver residual |
| CASH.01 | 100+30−45=85 KZT week1 close | 13-week exact time series |
| CASH.04 | 100−70=30 KZT CFO | internal transfers excluded |
| CASH.05 | 20+5−(−3)+2=30 KZT CFO | correct sign and balance changes |
| DCF.01 | CF=[−100,60,60], r=.10 → NPV≈4.13223140496 KZT | PV row sum equals aggregate |
| DCF.03 | CF=[−100,230,−132] → IRR roots 0.10, 0.20 | solver completeness / ambiguity |
| STOCK.01 | FIFO lots 10@100,10@120, issue12 → 1240 KZT | closing stock 960 |
| STOCK.02 | WAC on same events → 1320 KZT | unit cost 110, closing 880 |

Методологический reviewer должен independently verify each expected output; Python reference itself is not an independent source of financial truth. Тесты включают zero, null, not-applicable, invalid, duplicate events, missing source revisions, stock/flow time mismatch, currencies, tenant leakage, stale plan and source revocation. IRR repeated/no-root tests must not rely only on sign-change scanning. Numeric parity: exact Decimal for finance; iterative roots — admitted rate and NPV residual tolerances.

## 8. Будущие QA/операционные критерии

- All 14 Input/Method/Output schema revisions independent, canonical hashes pinned.
- One input key and same binding produces one durable committed Result; conflicting replay 409.
- Two workers race, stale lease holder fails fencing; restart and crash recovery are idempotent.
- Source or policy revoked between claim and commit → block result publication.
- Outbox event retry and duplicate notification → one consumer archived record and verified receipt.
- Unarchived unique result is **not deleted** merely because 3h elapsed.
- Mixed currency, unit, unsupported rate basis, AS_OF/INTERVAL, accounting basis → blocked, not converted to zero.
- Multiple result sets in one job and multiple rows in each result set, including 0/2 IRR roots.
- Python Decimal golden tests for all 14 and Rust differential tests only in later approved phase.
- CPU/memory/p95/p99 and serialization/network path must be compared with Java/SQL on equal source data, not assumed from language.
- Security: allowlisted taskCode, no arbitrary user SQL/Python/Rust expressions, maximum rows/bytes/iterations/roots, service auth, tenant/project isolation.
- 3h cleanup retains metadata and authorized archive records; tombstone TTL > agreed retry horizon.
- Phase status for every indicator: REQUIREMENTS_DRAFT → INPUT_CONTRACT_REVIEWED → MATH_GOLDEN_VERIFIED → PYTHON_REFERENCE_VERIFIED → RUST_PARITY_VERIFIED → FINANCIAL_S2_APPROVED → PRODUCTION_ADMITTED. No status can be inferred from merely creating this document.

## 9. Открытые решения для финансовых и технических владельцев

| Код | Вопрос к согласованию | Модели |
|---|---|---|
| O01 | Как долго сохраняется tombstone, когда разрешен reuse key | Все |
| O02 | Posted allocations или earliest-due; recognized vs net snapshot | SET.01/02/03/06 |
| O03 | Aging bucket boundaries, graceDays, holiday date policy | SET.03 |
| O04 | Accounting basis and VAT/penalties/advances treatment | SET.01/02 |
| O05 | Nominal accrual day-count, compounding, date shifts, cash fees | LOAN.01/02 |
| O06 | Financial IFRS9 EIR eligibility and root policy, not KZ GESV | LOAN.03 |
| O07 | Cash event classification, internal transfers, CFO reconciling scope | CASH.01/04/05 |
| O08 | Discount rate basis and IRR domain/certified root isolation | DCF.01/03 |
| O09 | Cost layers on returns, periodic vs moving WAC and unit conversions | STOCK.01/02 |
| O10 | JSON/Protobuf/Arrow thresholds, output pagination/chunks | Все |
| O11 | External archive owner/receipt, 3h expiry and audit retention | Все |
| O12 | Limits, benchmark workloads, production admission and independent S2 | Все |

## 10. Источники и решение о начале реализации

- FEngine master: https://github.com/alimbetov/FEngine/blob/main/FENGINE_MASTER_SPEC.md (v0.4, R0 deep indicator catalogue).
- FIN source: https://github.com/alimbetov/fin-analyzer/tree/feat/fin-form-library-standalone (snapshot 854fac8cbff67986b05159271fc5231cc712baa0).
- FIN architecture documents: docs/FIN-CALC-APPS-R0-SIX-APPLICATION-CONTRACTS-AND-ROADMAP.md; docs/FIN-CALC-A05-R1-LOAN-CONTRACT-PAYMENT-SCHEDULE-STUDIO-TZ.md; docs/FIN-CALC154-C01-C02-EDITORIAL-POLICIES-V2-2026-11-20.md; docs/FIN-DATA-CALC-R2-CROSS-FORM-OUTPUT-MATRIX.tsv; docs/FIN-MG-R01-METRIC-GRAPH-RUNTIME-FOUNDATION.md (all in FIN branch).

**Release decision:** DOCUMENTATION ONLY. Самостоятельное ТЗ включает 14 model contracts, 15 dataset DTO, полный словарь types/units/params, единый InputBatchDTO и Output results[]/rows[] контракт. Никакого исходного кода до отдельного согласования.
