# FEngine HC-R0.1 — мета-модель, повторное использование примитивов и квалификация расчётов

> **Architecture override (2026-11-20):** Any historical proposal in this document to persist calculation facts, plans, results or receipts to PostgreSQL has been superseded. Current FEngine runtime policy is **Redis-only, absolute TTL ≤10,800 seconds, immediate delete on authenticated consumer ACK, no durable user-data copies**. See [HC-R0.3 ephemeral policy](FENGINE-HC-R03-DECIMAL-CALCULATIONS-AND-EPHEMERAL-POLICY.md). This policy is documented; the Redis runtime itself is not implemented yet.

**Дата:** 2026-11-20. **Ветка:** main. **Статус:** PYTHON_REFERENCE_PARTIAL / FINANCIAL_S2_HOLD.
**Основание:** каталоги R3 (116 / 732 / 222). **Коррекция:** семейства — 20, а не 19.
Существующий каталог не означает 116 реализованных финансовых исполнителей.

## 1. Разделение Model / Parameter / Variant

- **MetricDefinition:** однозначный экономический смысл и единица измерения; RAW, DERIVED, MODEL_OUTPUT. Наблюдение FactSet имеет собственный snapshot, период, валюту, scope и происхождение.
- **FormulaRevision:** чистая типизированная операция над входными показателями (выражение / компилируемое AST / канонический алгоритм).
- **MethodologyRevision:** область допустимости, финансовая методика, правила исходных данных, точность, интерпретация, доказательства, reviewer, effective dates и SHA. Принципиально отличается от формулы.
- **ModelDescriptor:** именованный расчётный контракт с точными InputSchema, OutputSchema, используемыми методиками и стратегическими результатами. Один ModelDescriptor допускает несколько FormulaRevision при сохранении бизнес-смысла.
- **ParameterDefinition:** общая семантически типизированная сущность (id, name, value-type, dimension, bounds, source requirements). **ModelParameterBinding:** модельный/методический контекст того же параметра (requiredWhen, allowedOverrides, period, version).
- **VariantTemplate:** согласованная комбинация selector-осей методики и условно обязательных параметров. VariantInstance = VariantTemplate + normalised resolved values + provenance + effective revision + immutable SHA; не новый ModelDescriptor.
- **CalcPlanBinding:** неизменяемая ссылка на exact model/method/formula/input/output/numeric-policy/schema/source/approval/build hashes. Отдельно CalcRun/ResultReceipt.
- **StrategyVersion:** правила переходов по измеренным модельным результатам, не дублирующие формулы.

**Техническая граница:** разные законы начисления амортизации или оценки — разные MethodologyRevision/AlgorithmRef в ОДНОЙ модели (не просто замена ставки). Варианты только выбирают зарегистрированную, неизменяемую стратегию ядра. Ни eval, ни динамический SQL, ни произвольные формулы пользователей в reference/production не допускаются.

**Фактическое состояние:** R3 содержит явно перечисленные 222 кандидатные MethodVariant, а не истинное генеративное пространство. Автоматический вывод всех 222 из 732 параметров пока недоказуем: у ряда элементов отсутствуют окончательные allowlists, requiredWhen, конфликтующие типы и утверждённые правила совместимости. Это P0 до contract freeze.

## 2. Переиспользуемое ядро — девять категорий

| Код | Примитив | Типизированные аргументы и общие проверки | Основные потребители |
|---|---|---|---|
| PV | Present value/NPV | Decimal cashflow, date/term, rate quotation, day-count, origin; rate > -1; срок и валюты согласованы | DCF, LOAN, CAP, CREDIT, PF, INS, HEDGE |
| ROOT | EIR/IRR root isolation | Cashflow sign, root domain, numerical precision, exact-date basis, proof of uniqueness/completeness; tangent/multiple roots не скрывать | DCF.03/.04, LOAN.03/.08 |
| SCHED | Dated schedule & day-count | LocalDate, events, calendar, effective rate curve, payment waterfall; no backwards date or undisclosed capitalization | LOAN, ACC, ASSET, PF, ALM |
| AGG | Typed aggregate/statistics | Flow/stock/rate semantics, complete event windows, weighted denominator, quantile policy; no silent missing=0 | SET, CASH, COST, PLAN, RISK, INS |
| PROB | Expected loss/distributions | Conditional PD vs marginal, EAD, LGD, scenarios, hazard, exposure date, seeded PRNG; weights=1, PSD correlation | ECL, RISK, CREDIT, INS, HEDGE |
| FX | Exchange/translation | ISO currency pair, quote orientation, exact rate/curve/date and gain classification; no reversed quote silently | CASH, ACC, RISK, HEDGE |
| EVENT | Ordered event matching & inventory layers | eventId, entity, scope, effective date, reversals, idempotency, lot; reject negative/inconsistent stock | SET, STOCK, ACC, ASSET, LOAN |
| OPT | Constrained optimization | objective, decision domain (integer/continuous), limits, optimality gap, timeout; cannot mark feasible as optimal | PLAN, PRICE, COST, CASH, HEDGE |
| NUM | Numeric/units/rounding | Decimal canonicalization, dimensional units, precision, named quantization stage, nonfinite/missing/zero | ВСЕ 116, без финансовой интерпретации |

**Реальный код сейчас:** PV (regular and ACT/365 dated), SCHED (four bounded dated contractual schedules), EVENT (FIFO/WAC and ageing), NUM (Decimal), model-level CAPM/WACC/asset depreciation/LLCR/PLCR. TASE реализует отдельные 13 агрегаторов. ROOT/PROB/FX/OPT в финансовом HC пока не квалифицированы и **не должны подменяться заглушкой**. Python reference не является financial S2.

## 3. Матрица семейство × примитив — 20 × 9

Это **предлагаемая** карта переиспользования на основе семантики контрактов; указанные зависимости должны быть закреплены в typed bindings при квалификации. Пустая ячейка означает отсутствие обоснованного mapping на текущем этапе. Номер после точки приводится внутри семейства; например, DCF:01 = HC.DCF.01. В NUM «все» означает общую числовую политику.

| Family | PV | ROOT | SCHED | AGG | PROB | FX | EVENT | OPT | NUM |
|---|---|---|---|---|---|---|---|---|---|
| SET | — | — | 03,07 | 04,07 | — | — | 01,02,06 | — | все |
| ECL | 02,03,05 | — | 03,06 | 01,07 | 01–07 | — | 07 | — | все |
| LOAN | 03–05 | 03,08 | 01,02,06 | 07 | — | — | 02,05 | — | все |
| CASH | 08 | — | 01,02 | 01–05 | 03 | 07 | 06 | 08 | все |
| DCF | 01,02,05–08 | 03,04 | 02,04 | 09 | 09 | — | — | — | все |
| ACC | 06 | — | 06 | 01,07 | — | 03 | 02,04 | — | все |
| STOCK | — | — | 05 | 05,06 | 07 | — | 01–03,06 | 07 | все |
| ASSET | 03 | — | 01,07 | 04,06 | 06 | — | 01,02,05 | — | все |
| COST | — | — | 05 | 01,03,08 | 05 | — | 01,02 | 04 | все |
| PLAN | 08 | — | 01,05,06 | 02,03 | 02,03 | — | — | 04,08 | все |
| RISK | 01 | — | 04,06 | 02,03,05 | 01–07 | 07 | — | — | все |
| CAP | — | — | — | 01 | — | — | — | — | все |
| CREDIT | 01 | 01 | 01 | 02 | 01,02 | — | — | — | все |
| CUST | 01 | — | 02 | 01,02 | 01 | — | — | — | все |
| ALM | 02 | — | 01 | 01 | 02 | — | — | — | все |
| FTP | 01 | — | 01 | 01 | — | — | — | — | все |
| PF | 01 | — | 01,02 | 01 | — | — | 02 | — | все |
| PRICE | — | — | — | 01 | 01 | — | — | 01 | все |
| HEDGE | 02 | — | 02 | 05,06 | 04–07 | 01,03 | — | 07 | все |
| INS | 09,10,11 | — | 01,11 | 01–05 | 03–10,14 | — | 11,12 | — | все |

**Не считать «общий NUM» доказательством, что финансовые семейства автоматически взаимозаменяемы.** Выделение SCHED/EVENT/AGG как общих kernel modules предотвращает дублирование, а отраслевые методики остаются разными. Кандидатные mappings не определяют порядок исполнения без actual OutputSchema/InputSchema.

## 4. Пространство 732 привязок параметров

Реальные TSV R3: 732 уникальных (modelCode, parameterCode), 704 различных текстовых имени и **5 имён с несовместимыми типами**:
- calendarPolicy: CODE / REFERENCE;
- taxShieldEligibility: REFERENCE / CODE;
- horizon: INTEGER / PERIOD;
- dayCount: ENUM / CODE;
- capitalBudget: MONEY / REFERENCE.

**Решение:** новый глобальный SemanticParameterId вида PAR.<namespace>.<semantic-code>. В глобальном ParameterDefinition одна единица семантики; modelCode/methodRevision лишь ссылается через ParameterBinding. Два одинаковых name объединять только после проверки экономического смысла, единиц, domain, времени, знака и нормативного контекста. Не объединять указанные пять имён автоматически.

Минимальный типизированный контракт:
- parameterId, valueType (DECIMAL, MONEY, RATE, INTEGER, BOOLEAN, ENUM, DATE, PERIOD, QUANTITY, CURVE, DISTRIBUTION, SERIES, REFERENCE);
- dimension/unit/currencyPolicy/timeSemantics;
- constraints (min/max, inclusive flags, validCodes, crossFieldPredicates);
- requiredWhen (variant, business rule, effective date);
- originPolicy (FROZEN_FACTSET, SIGNED_CONFIG, USER_EXPLICIT, QUALIFIED_SOURCE);
- defaultPolicy (NONE до независимого review);
- overrideAuthority, effectiveFrom/To, sourceRevisionSha, parameterContractSha, policyApprovalId.

**Обязательные группы (по модели, не по всему семейству):**
- SET: obligation events, asOf, legal allocation/cutoff; optional только согласованные grace, buckets, cost policy.
- ECL: PD term, LGD, EAD, cash shortfall timing, discount policy; optional сценарные overlays только с весами и доказательствами.
- LOAN: contract revision, principal, rates, payment dates, dayCount; optional grace/prepay/fees по утверждённым правилам.
- CASH: bank cashflow/position, period, currency, completeness; optional scenario/horizon/contingency.
- DCF: signed dated/period cashflows, currency, discount basis; optional reviewed timing, terminal, sensitivity policy.
- ACC: accounting basis, opening balances, legal entity, cutoff; optional consolidation/OCI/tax rules if applicable.
- STOCK: ordered lots, quantities, costs, units; optional stock/return policy.
- ASSET: cost, salvage, useful life, serviceDate, component; optional dated estimate/impairment revisions.
- COST: product mix, cost pools, volume, pricing driver; optional objective and constraints.
- PLAN: historical series, scenario dates, limits; optional stochastic confidence and solver options.
- RISK: risk factor samples/models, horizon, confidence, sign; optional correlation/seed/calibration.
- CAP/CREDIT/CUST/ALM/FTP/PF/PRICE/HEDGE/INS: must supply exact approved curves/bases, contract, cohort, market and regulatory revisions under their specialized method applicability.

**Необязательный параметр без разрешённого default остаётся отсутствующим — не подставлять 0, 365, 1.0 или значение предыдущей версии.** У текущих 732 записей requiredness/domain largely pending independent review; они не становятся пригодными для исполнения только от наличия logicalType.

## 5. Пространство вариантов

Generation contract:
1. Из опубликованного ModelDescriptor выбрать зарегистрированный MethodologyRevision по applicability.
2. Методика объявляет конечные методологические оси: algorithmSelector, timeBasis, measurementBasis, settlementRule и т. п.
3. Комбинация осей проверяется conditional requiredWhen, cross-field guard, source availability, sector constraints; несовместимые наборы запрещены.
4. Materialize normalized *resolved* config (включая ссылочные ревизии, source fingerprints, нулевые/отсутствующие значения).
5. SHA = hash(canonical(methodRevision, formulaRevision, schemaRevisions, config, precisionPolicy, scope, effectiveDate, sourceManifest, buildManifest, admissionRevision)).
6. Создать immutable VariantInstance/CalcPlanBinding. Изменение любого параметра порождает **новую ревизию**, исторические CalcRun не мутируются.

Типовое несовместимое сочетание: ACC revaluation по методике cost model; FCFF с cost of equity вместо WACC; loan annuity со способом амортизации основного средства; льготный grace без реального изменённого cashflow. Совместимые оси: scenarioSet + discountRate + explicit rounding policy, если методика их разрешает.

**Текущие 222 строки — draft registry, не доказательство 222 автоматически генерируемых approved combinations.** До миграции R4 они сохраняются как уникальные кандидатные именованные template selector IDs, не 222 отдельные Python функции.

## 6. Конфигурация отраслевой применимости

| Family | Поддерживаемая область (candidate) | Дополнительные обязательные gates |
|---|---|---|
| CAP | Корпоративные финансы, оценка бизнеса | Risk-free tenor, CAPM/market basis, equity/debt weights |
| CREDIT | Кредиторы/банки | ECL model revision, funding curve, capital basis, pricing law |
| CUST | Ритейл, SaaS, сервис | Qualified cohort, retention and CAC attribution |
| ALM | Банки, казначейства | Behavioral deposit assumptions, curve revision, regulatory scope |
| FTP | Банковское внутреннее ценообразование | Currency/tenor matched FTP curve, internal allocation policy |
| PF | Проектное финансирование | CFADS definition, contractual waterfall, loan/project life |
| PRICE | Торговля/дистрибуция | Elasticity evidence, margin and inventory constraints |
| HEDGE | Банки, казначейства, промышленные риски | Quote orientation, instruments, collateral, designation evidence |
| INS | Страховщики | Product/claim group, actuarial triangle, IFRS17 basis or legal solvency revision |

**Никаких** if industry == bank внутри вычислительных примитивов. Selector eligibility находится в ApplicabilityRule(organizationType, sector, country, effectiveDate, accountingBasis, productPackRevision). Нормативные методики отдельно утверждаются по юрисдикции и дате.

## 7. Два различных графа и их валидация

### 7.1 Model dependency DAG

Python: fengine_hc/graphs.py — CandidateModelGraph строит ровно **116 узлов и 55 кандидатных рёбер** из upstreamCandidateRefs Wave 4/5, включая сокращённые суффиксы вида HC.LOAN.01/02/03; валидирует unknown node/cycle и выдаёт deterministic topological order.

Это **не** автоматически полный вычислительный граф: для многих W1–W3 отсутствуют доказанные межмодельные выходные bindings. Значение candidate edge = CANDIDATE_NO_TYPED_RESULT_BINDING. Не повышать в QUALIFIED по совпадению modelCode.

InMemoryCalculationPlan: каждое исполняемое ребро имеет sourceJob, sourceOutputField, targetInputField. Проверяет unknown job, duplicates, конфликт target input, циклы, отсутствие output; исполняет в топологическом порядке. Проверяемый пример: HC.CAP.01.costOfEquity → HC.CAP.02.costOfEquity. Это **in-memory reference**, без PostgreSQL транзакционной фиксации.

Для production дополнительно обязательны OutputSchema/InputSchema/MetricSemanticVersion, единицы и валюты, effective dates, tenant/FactSet scope, source hash, admission evidence SHA, optimistic locking, durability и idempotency.

### 7.2 Strategy decision graph

Отдельные StrategyState(ENTRY, DECISION, ACTION, TERMINAL; activeFamilySet) и StrategyTransition(source, target, modelCode, outputField, comparator, threshold). Структура валидирует номера моделей, типы правил, пороги, наличие состояний и отсутствие циклов без специального bounded-loop contract. Rule evaluation использует Decimal; произвольный Python/eval не выполняется.

Пример стратегии: вход → оценка стоимости капитала HC.CAP.02 → ветка инвестиционного рассмотрения при approved threshold → альтернативная ветка дополнительной проверки. **Этот граф не открывает финансовый допуск и не выдаёт автоматической инвестиционной рекомендации**. Для реальных стратегий требуется типизированный квалифицированный Finding, а не просто математическое условие.

## 8. Golden datasets и Rust parity

Каждый реализованный ModelVariant требует независимый golden JSON:
inputSnapshot, scope, method revision, exact configuration, numericPolicy, expected typed outputs, status, errorCodes, provenance and SHA. Для каждого из 116 — отдельная запись покрытия IMPLEMENTED/NOT_IMPLEMENTED, не синтетический PASS без исполнения.

Required cases:
- DCF.01: [-1000, 600, 600] при r=.10 -> NPV ≈ 41.32231404958678; 0/-100% rate and negative rate domain.
- DCF.02: XNPV 0 at 10% for -100 on 2026-01-01 and +110 on 2027-01-01; ACT/365 fixed explicitly required.
- CAP.01: RF=.04, beta=1.2, ERP=.06 -> Ke=.112.
- CAP.02: E=60,D=40, Ke=.12,Kd=.08,tax=.25 -> WACC=.096.
- ASSET.01: SL C=1200,S=200,n=5 -> 200/period; SYD C=1000,S=100,n=4 -> first 360, last 90; UOP C=1000,S=100, total=30000, actual=9000 -> 270.
- LOAN.02: dated ACT/365 schedules reconcile principal exactly, final balance=0; irregular periods and errors.
- STOCK: FIFO receipts 10×10,10×20, issue 12 -> COGS 140 / closing inventory 160; moving WAC -> COGS 180 / closing 120.
- SET.03: overdue boundaries non-overlap and no negative outstanding.
- PF.01: rate=0, debt=100, CFADS=[100,100,100], loanLife=2 -> LLCR=2, PLCR=3.
- Graph: CAPM → WACC exactly; cyclic job input dependencies rejected.

Python/Rust parity contract: identical normalized decimal inputs, dates, hashes, precision/rounding staging, outputs, structured errors and deterministic ordering. For monetary arithmetic compare exact canonical decimals **after the specified quantization stage**; never substitute binary float. For iterative numerical roots/Monte Carlo require explicit tolerance bound, iteration policy and seeded RNG algorithm version; compare decision statuses and failure reasons exactly. Historical results must keep original method revision and build SHA.

Current mathematical reference uses Python Decimal localcontext precision=40 and fingerprints. It is not yet a stable cross-language canonical wire protocol. Production requires formally frozen serialization and unit-specific money quantization; Python/Rust parity is NOT CLAIMED.

## 9. Реализация, тестирование и acceptance gates

Executable reference code:
- fengine_hc/reference.py: 10 financial model codes with real mathematical execution, no generic fallback zero, explicit reference_mode gate.
- fengine_hc/graphs.py: candidate 116-node graph, typed in-memory bound DAG, decision graph.
- tests/test_fengine_hc_reference.py, tests/test_fengine_hc_graphs.py: independent numerical examples plus blockers.
- geo_opt/ and tase/ remain separate reusable reference packages.

Known limitations:
1. 106/116 financial model codes have no executor; many model variants of the 10 covered codes remain explicitly unimplemented.
2. ROOT, probabilistic ECL, interest EIR, IFRS17, full PVM and constrained OPT are **not qualified**. Do not replace with a generic approximation.
3. Current R3 parameter requiredness, source and constraints not frozen; all S2 unapproved.
4. In-memory Result SHA and deep frozen projection are not durable immutable PostgreSQL records.
5. 55 candidate graph edges do not constitute reviewed output-schema bindings; industry applicability and full source authority not executed.
6. No Rust implementation, no complete parity and no performance qualification.

Exit gates for next stage:
- R0.2: classify all 732 ParameterBinding rows into globally typed semantic IDs and remove five type collisions without altering historical drafts; validate 222 method template selectors.
- R0.3: freeze first 10 qualified mathematical contracts with independent goldens, unit/currency/date rules, source/dimensions and precision.
- R0.4: implement and test ROOT (IRR/EIR), probabilistic losses and dynamic rate curves, refusing ambiguous/multiple-root results.
- R0.5: schema-driven typed cross-model CalcPlan, immutable PostgreSQL receipts, idempotency, fencing and recovery.
- R0.6: explicit sector applicability/finance S2; Rust shadow parity only after reproducible Python goldens and load measurements.

**Core decision:** no synthetic universal 'execute everything' function; missing calculators return MODEL_NOT_IMPLEMENTED / VARIANT_NOT_IMPLEMENTED. The most important measure is the number of independently verified real calculations, not catalogue row counts.
