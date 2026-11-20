# FEngine — единая спецификация финансово-экономического аналитического ядра

Версия документа: 0.2 (концепция + сверка с FIN Analyzer)
Дата: 2026-11-20
Репозиторий: https://github.com/alimbetov/FEngine
Статус: DRAFT / синхронизация знаний с FIN на 2026-11-20; архитектурное задание; не является свидетельством реализованных расчётов.
Правило текущего этапа: хранить концепцию, реестры-направления, проектные контракты, графы и план работ В ОДНОМ ЭТОМ ТЕКСТОВОМ ФАЙЛЕ. Не создавать дополнительные файлы, сервисы, схемы БД или исходный код до отдельного согласования.

## 1. Цель

Построить универсальный, расширяемый движок финансового и экономического анализа предприятий, организаций, проектов и бизнес-единиц, применимый к разным отраслям и моделям деятельности.

Основная цепочка:
Показатель → Формула → Методика → Вид анализа → Результат → Заключение → Стратегия действий.

Принципы:
1. Единый канонический каталог показателей, а не независимые справочники по каждому виду анализа.
2. Одну и ту же формулу допускается применять в нескольких методиках при совпадении её входного, временного и размерностного контрактов.
3. Один показатель может участвовать в произвольном количестве формул, графов и стратегий.
4. Отраслевые различия описывать применимостью, параметрами и методиками, а не копированием расчётного движка.
5. Никаких вымышленных формул: определения, условия применимости, примеры и источники методологического решения обязательны.
6. Проверенный вычислительный результат не равен автоматически финансово утверждённой интерпретации.
7. Воспроизводимость: точные версии данных, формул, параметров, стратегии и вычислительного плана.

## 2. Онтология и модель показателя

Виды показателей:
- RAW_METRIC — исходный факт, вводимый или импортируемый без вычислительной формулы.
- DERIVED_METRIC — вычисляемый показатель со строго определённым выражением.
- MODEL_OUTPUT — результат алгоритмической аналитической модели или прогноза.
- METRIC_GROUP — смысловая группа, не используемая как числовой факт.
- DIMENSION — измерение/ось аналитики (организация, валюта, период, подразделение, продукт и т. д.).

Не путать:
- Показатель (определение) с наблюдением/значением показателя.
- Формулу (функция и контракт) с методикой (область применимости, интерпретация, параметры).
- Вид анализа (пользовательская цель) со стратегией (ветвящийся маршрут применения методик).
- Результат вычислений (математический факт) с выводом, оценкой риска и рекомендацией.

Канонические поля определения показателя:
metric_code, metric_revision, name_ru/name_kk/name_en (расширяемо), description,
metric_kind, metric_group, numeric_type, unit, currency_policy, time_semantics,
aggregation_policy, dimensions, data_source_constraints, availability, domain,
entity_types, accounting_basis, evidence, approval_status, effective_date,
content_sha256.

Временная семантика:
- INSTANT: баланс/остаток на дату.
- FLOW: поток за период.
- PERIOD_AVERAGE: средний остаток/средняя величина за период.
- RATIO: производный коэффициент с собственным периодным контрактом.
- EVENT / FORECAST: событие или прогнозное значение.

Запретить сложение показателей несовместимых временных периодов, валют и размерностей без явной операции преобразования. Конверсия валюты требует источника курса, даты и метода конвертации. Нулевое значение, отсутствие значения и неприменимость — разные состояния.

## 3. Единый каталог видов анализа

Универсальные финансовые направления:
FIN-01 Активы, обязательства и собственный капитал.
FIN-02 Доходы, расходы, финансовые результаты.
FIN-03 Ликвидность.
FIN-04 Платёжеспособность.
FIN-05 Финансовая устойчивость.
FIN-06 Рентабельность.
FIN-07 Оборачиваемость активов и капитала.
FIN-08 Денежные потоки.
FIN-09 Оборотный капитал.
FIN-10 Долговая нагрузка и обслуживание долга.
FIN-11 Горизонтальный, вертикальный и трендовый анализ.
FIN-12 Качество прибыли и денежных потоков.
FIN-13 Дивидендная политика и капитализация.
FIN-14 Финансовая диагностика и раннее предупреждение.

Экономические направления:
ECO-01 Производительность труда.
ECO-02 Себестоимость и структура затрат.
ECO-03 Экономическая эффективность ресурсов.
ECO-04 Факторный анализ.
ECO-05 План-факт и бюджетные отклонения.
ECO-06 Маржинальный анализ, CVP, безубыточность.
ECO-07 Ценообразование и unit economics.
ECO-08 Использование основных средств и мощностей.
ECO-09 Запасы, закупки, логистика.
ECO-10 Организационная и операционная эффективность.
ECO-11 Конкурентоспособность и рыночная позиция.
ECO-12 Клиентская экономика и удержание.

Инвестиционные направления:
INV-01 Инвестиционная эффективность.
INV-02 NPV, IRR, PI, окупаемость.
INV-03 Оценка бизнеса и стоимости капитала.
INV-04 Проектное финансирование и инвестиционные риски.
INV-05 Портфельное сравнение проектов.

Риски, прогнозирование, стратегия:
RISK-01 Финансовые риски.
RISK-02 Кредитные риски.
RISK-03 Сценарный и стресс-анализ.
RISK-04 Рыночные, валютные, процентные риски.
RISK-05 Операционные и концентрационные риски.
STR-01 Стратегическая эффективность.
STR-02 Прогнозирование финансовых и экономических показателей.
STR-03 Анализ чувствительности.
STR-04 Сравнение альтернативных стратегий.
STR-05 Ранжирование рисков и мероприятий.

Секторальные методики (надстройки, не отдельные вычислительные ядра):
SEC-01 Промышленность.
SEC-02 Торговля и дистрибуция.
SEC-03 Строительство.
SEC-04 Логистика и транспорт.
SEC-05 Сельское хозяйство.
SEC-06 Услуги.
SEC-07 Банки, кредитные организации, лизинг.
SEC-08 Страхование.
SEC-09 Некоммерческие организации.
SEC-10 Государственные и бюджетные организации.
SEC-11 Образование и здравоохранение.
SEC-12 Недвижимость и девелопмент.
SEC-13 IT/SaaS и платформенный бизнес.
SEC-14 Энергетика и коммунальное хозяйство.

Каждая методика должна декларировать применимые сектора, типы организаций, модели отчётности, юрисдикцию/нормативный контекст, доступность исходных данных, период и ограничения. Нельзя механически применять универсальные коэффициенты к банкам или бюджетным организациям без отраслевой адаптации.

## 4. Четыре взаимосвязанных графа

A. METRIC KNOWLEDGE GRAPH — смысловая сеть показателей.
Узлы: RAW_METRIC, DERIVED_METRIC, MODEL_OUTPUT, METRIC_GROUP, DIMENSION.
Связи: BELONGS_TO, IS_COMPONENT_OF, ALIAS_OF, APPLICABLE_TO, REQUIRES_DIMENSION, RELATED_TO.
Назначение: поиск, классификация, повторное использование, объяснимость.

B. CALCULATION DEPENDENCY GRAPH — строго типизированный DAG вычислений.
Узлы: FACT_INPUT, FORMULA_REVISION, TRANSFORM, MODEL_EXECUTION, RESULT.
Связи: USES_INPUT, PRODUCES, DEPENDS_ON, TRANSFORMS.
Требования: проверка циклов, топологическая сортировка, missing inputs, единицы,
периоды, кеширование по идентичному immutable input fingerprint, инкрементальные
пересчёты, происхождение результата и детерминированное исполнение.
План DAG фиксируется до исполнения; опубликованный план нельзя тихо менять.

Пример:
Revenue - CostOfSales → GrossProfit
GrossProfit / Revenue → GrossMargin
CurrentAssets / CurrentLiabilities → CurrentRatio
Потребности графа: прямые зависимости, обратные зависимые узлы (impact analysis),
причины блокировок, downstream invalidation, версия каждого узла и ребра.

C. ANALYTICAL STRATEGY GRAPH — условные ветки анализа.
Типы узлов: ENTRY, CONDITION, ANALYSIS, METHODOLOGY, DECISION,
SCENARIO, BRANCH, TERMINAL.
Связи: NEXT, TRUE_BRANCH, FALSE_BRANCH, ON_MISSING_DATA,
ON_NOT_APPLICABLE, ON_FAILURE, USES_METHODOLOGY.
Правила переходов версионируются вместе с параметрами; пороги не захардкожены.
Путь анализа определяется целью, отраслью, типом организации, фактической
доступностью данных, настройками риск-профиля и выбранным сценарием.

Пример:
FinancialHealth → LiquidityAnalysis → CurrentRatio
  ├─ ниже согласованного порога → CashFlow → DebtService → Finding
  ├─ порог выполнен → Profitability → OperatingEfficiency → Finding
  └─ данных недостаточно → DataGapReport → REQUEST_DATA.
Порог иллюстративный; не устанавливается универсальный норматив автоматически.

Ветвление — не цикл расчётов. Для итеративного моделирования нужен
отдельный контролируемый алгоритм с лимитом итераций и критерием сходимости.

D. FINDINGS & REASONING GRAPH — доказательная сеть выводов.
Узлы: CALC_RESULT, FINDING, RISK, OPPORTUNITY, RECOMMENDATION, ACTION.
Связи: SUPPORTED_BY, INTERPRETED_AS, EXPOSES_RISK, SUGGESTS, DERIVED_FROM.
Каждый вывод привязан к исходным фактам, версии вычислений, периоду,
версии стратегии, нормативному/экспертному порогу и тексту обоснования.
Выводы должны иметь confidence/qualification и явный тип:
MEASURED_FACT, RULE_BASED_FINDING, EXPERT_JUDGEMENT, RECOMMENDATION.

Связь между графами через стабильные ID, версии и typed references.
Graph API — проекция доменной модели, не источник вычислительной истины.

## 5. Стартовые формулы для наполнения каталога (не полный каталог)

Обозначения:
Rev — выручка; COGS — себестоимость продаж; Opex — операционные расходы;
CA — оборотные активы; CL — краткосрочные обязательства; Cash — денежные средства;
STI — краткосрочные ликвидные инвестиции; AR — дебиторская задолженность;
Inventory — запасы; TA — активы; TL — обязательства; Equity — собственный капитал;
EBIT — прибыль до процентов и налогов; D&A — амортизация;
NI — чистая прибыль; CFO — денежный поток от операционной деятельности;
Capex — капитальные затраты; Avg(X) — средний X за сопоставимый период.
Все значения должны использовать единый согласованный период и контекст отчётности.

Финансовый результат:
F001 GrossProfit = Rev - COGS.
F002 GrossMarginPct = GrossProfit / Rev × 100.
F003 OperatingProfit = Rev - COGS - Opex (при условии, что Opex исключает COGS).
F004 OperatingMarginPct = OperatingProfit / Rev × 100.
F005 NetMarginPct = NI / Rev × 100.
F006 EBITDA = EBIT + D&A (только если EBIT и D&A сопоставимы по охвату).
F007 EBITDA_MarginPct = EBITDA / Rev × 100.
F008 ROA = NI / Avg(TA) × 100 (период прибыли согласован с периодом усреднения).
F009 ROE = NI / Avg(Equity) × 100 (отрицательный Equity требует особой интерпретации).

Ликвидность и финансовая устойчивость:
F010 CurrentRatio = CA / CL.
F011 QuickRatio = (Cash + STI + AR_Eligible) / CL; состав AR_Eligible задаётся методикой.
F012 CashRatio = (Cash + STI_CashEquivalent) / CL.
F013 WorkingCapital = CA - CL.
F014 DebtToEquity = InterestBearingDebt / Equity.
F015 LiabilitiesToAssets = TL / TA.
F016 EquityRatio = Equity / TA.
F017 NetDebt = InterestBearingDebt - CashAndCashEquivalents (согласовать определение restricted cash).
F018 NetDebtToEBITDA = NetDebt / EBITDA (с оговорками при EBITDA <= 0).
F019 InterestCoverage = EBIT / InterestExpense; финансовые расходы типизируются.
F020 DSCR = CashAvailableForDebtService / ScheduledDebtService (денежная база определяется конкретной методикой).

Оборачиваемость и оборотный капитал:
F021 AssetTurnover = Rev / Avg(TA).
F022 InventoryTurnover = COGS / Avg(Inventory).
F023 ReceivablesTurnover = CreditSales / Avg(AR_Trade).
F024 DSO = DaysInPeriod × Avg(AR_Trade) / CreditSales.
F025 DIO = DaysInPeriod × Avg(Inventory) / COGS.
F026 DPO = DaysInPeriod × Avg(AP_Trade) / CreditPurchases (допустимый суррогат COGS требует отдельного варианта методики).
F027 CashConversionCycleDays = DSO + DIO - DPO.

Cash flow:
F028 FreeCashFlowSimple = CFO - CapexCashOutflow (CapexCashOutflow задан положительным расходом).
F029 CFO_to_NetIncome = CFO / NI (при NI <= 0 смысл меняется).
F030 CFO_to_CurrentLiabilities = CFO / Avg(CL) (flow vs stock требует согласованного периода).

Экономика, производство и план-факт:
F031 LaborProductivity = OutputVolume / LaborHours; единица выхода обязательна.
F032 RevenuePerEmployee = Rev / Avg(FTE).
F033 UnitCost = EligibleProductionCost / OutputUnits.
F034 ContributionMargin = Rev - VariableCosts.
F035 ContributionMarginRatio = ContributionMargin / Rev.
F036 BreakEvenUnits = FixedCosts / (UnitPrice - VariableCostPerUnit); применимо к модели одного продукта либо эквивалентной продуктовой корзины.
F037 PlanFactAbsolute = Actual - Plan.
F038 PlanFactRelativePct = (Actual - Plan) / Abs(Plan) × 100; знак и интерпретация должны быть согласованы в методике.
F039 CapacityUtilizationPct = ActualOutput / AvailableCapacity × 100 при совместимых единицах и периодах.

Инвестиции:
F040 NPV = сумма по t от 0 до N: CF_t / (1+r)^t; в договорённом периоде дисконтирования.
F041 ProfitabilityIndex = PV(FutureInflows) / PV(InitialOutflows) для строго заданной схемы потоков.
F042 IRR = ставка r, при которой NPV(r) = 0; могут существовать несколько корней либо ни одного.
F043 PaybackPeriod = первый момент, когда накопленный недисконтированный CF становится неотрицательным (с правилом интерполяции внутри периода).
F044 DiscountedPayback = тот же критерий по дисконтированному CF.
F045 WACC = We×Ke + Wd×Kd×(1-T), если применима классическая налоговая модель; веса, ставка и налоговая база — версионируемые входы.

Тренды и факторные показатели:
F046 YoYGrowthPct = (Current - Previous) / Abs(Previous) × 100; не заменяет экономическую трактовку изменения знака.
F047 StructureSharePct = Component / Total × 100.
F048 CAGR = (EndValue / StartValue)^(1/Years) - 1; только для допустимых положительных значений и Years > 0.

Перечень F001–F048 — НАЧАЛЬНЫЕ ПРИМЕРЫ ДЛЯ МЕТОДОЛОГИЧЕСКОЙ ПРОВЕРКИ, НЕ ФИНАНСОВО УТВЕРЖДЁННЫЕ КОНТРАКТЫ.
Для каждой формулы нужны исходные определения из конкретной отчётной политики,
валюта, единица, период, denominator policy, округление, null semantics,
контрольный пример и решение ответственного методолога.
Не считать приведённые 48 формул автоматически реализованными или проверенными.

## 6. Типизированный Formula Engine

Рекомендуемый целевой backend:
Java 21; Spring Boot; PostgreSQL; Flyway; JPA для каталога;
JDBC/SQL для массовых расчётов; JUnit 5; Testcontainers.
Это рекомендация для дальнейшей реализации, не обязательство разворачивать стек сейчас.

Формулы — ограниченный типизированный AST/DSL, а не произвольный код пользователя.
Операторы: +, -, *, /, min/max, sum, avg, case/if,
comparison, date_shift, period_aggregate, discount, ratio, safe_divide.
Расширять набор операторов только под утверждённые методологические потребности.
Детерминированный numeric policy (BigDecimal/MathContext), precision/scale и rounding.
Обработка ZERO_DENOMINATOR, MISSING_INPUT, NOT_APPLICABLE, UNIT_MISMATCH,
PERIOD_MISMATCH, CURRENCY_MISMATCH, REVOKED_REVISION, STALE_PLAN.
Нельзя молча преобразовывать ошибки в нули.

Пример контракта формулы:
formula_code: FIN.GROSS_MARGIN.PCT
revision: 1
inputs: [FIN.GROSS_PROFIT (FLOW, MONEY), FIN.REVENUE (FLOW, MONEY)]
output: PERCENT
expression: grossProfit / revenue * 100
preconditions: same_period, same_currency, revenue != 0
rounding: methodology_defined
status: DRAFT
test_case: grossProfit=30, revenue=120 -> 25%.

## 7. Планирование и выполнение вычислений

Вход: immutable FactSet/snapshot, entity profile, analytic goal,
methodology revisions, parameter revisions, strategy revision и scenario overrides.

Конвейер:
1. Validate application context и доступные данные.
2. Resolve applicable methodologies; для неподходящих зафиксировать причины.
3. Resolve metric definitions and formula revisions.
4. Построить и валидировать DAG; вычислить недостающие источники.
5. Сформировать canonical immutable CalcPlan + fingerprints/SHA-256.
6. Выполнить в топологическом порядке с идемпотентностью и изоляцией.
7. Записать immutable results + input lineage, runtime metadata.
8. Пройти strategy branch conditions; фиксировать выбранный маршрут.
9. Создать findings по правилам интерпретации и доказательной цепочке.
10. Построить report/graph projections (без расхождения с расчётными данными).

Инкрементальный пересчёт — только после доказуемой идентификации изменившихся
входных фактов, dependency closure и неизменных остальных контрактов.
Нельзя возвращать кешированный результат при несовпадении версий или измерений.

## 8. Версионирование, квалификация, доступ

Сущности: MetricRevision, FormulaRevision, MethodologyRevision,
ParameterRevision, StrategyRevision, CalculationPlan, ResultRevision.

Статусы:
DRAFT → VALIDATED → TECHNICALLY_VERIFIED → FINANCIALLY_APPROVED → ACTIVE.
Дополнительные исходы: DEPRECATED / REVOKED.
Предусмотреть явный запрет production admission до требуемой независимой
финансовой квалификации; технический GREEN сам по себе её не заменяет.

В SHA-256 canonical manifest включать: код, ревизию, AST формулы,
типизированные входы/выходы, нормативные параметры, единицы, временную
семантику, округление, dependency references и применимые ограничения.
Execution manifest включает исходный FactSet fingerprint, версии всех зависимостей,
build/artifact fingerprint и runtime policy.
Изменение значимого параметра — новая immutable revision, а не изменение
опубликованной строки.
Исторические результаты воспроизводятся на версиях своего времени.
Разграничить роли автора, технического валидатора, финансового утверждающего
и пользователя расчёта.

## 9. Предлагаемая реляционная модель (будущая)

Каталог:
metric_definition, metric_revision, metric_dimension, metric_relationship,
formula_definition, formula_revision, formula_input,
methodology_definition, methodology_revision, methodology_parameter,
analysis_type, analysis_metric_binding, entity_type, sector_applicability.

Графы:
strategy_definition, strategy_revision, strategy_node, strategy_edge,
metric_graph_edge, calculation_dependency_edge, finding_graph_edge.

Вычисления и результат:
calculation_plan, calculation_plan_node, calculation_execution,
calculation_result, result_lineage, fact_snapshot_reference,
scenario_definition, scenario_override, finding_definition, finding_result.

Управление:
methodology_approval, artifact_manifest, audit_event, registry_coverage.

Нужны первичные/внешние ключи, уникальность по (code, revision),
ограничения ссылочной целостности, publication immutability,
идемпотентность исполнения и транзакционное утверждение.
PostgreSQL — источник истины. Отдельная графовая БД не требуется на R0:
графы представляются typed nodes/edges и строятся из реляционного каталога.

## 10. API-контракты (будущая реализация)

GET  /api/v1/metrics
GET  /api/v1/metrics/{code}
GET  /api/v1/metrics/{code}/dependencies
GET  /api/v1/formulas
GET  /api/v1/analysis-types
GET  /api/v1/methodologies
GET  /api/v1/graphs/metrics
GET  /api/v1/graphs/calculations
GET  /api/v1/graphs/strategies/{id}
GET  /api/v1/graphs/results/{executionId}
POST /api/v1/calculation-plans/preview
POST /api/v1/calculations
POST /api/v1/scenarios
POST /api/v1/scenarios/compare

Узлы и рёбра API должны содержать stable ID, type, revision,
status, labels, dependency metadata, reason codes и graph provenance.
React Flow можно подключить впоследствии; React-интерфейс не является
предпосылкой для корректного расчетного ядра.

## 11. Объекты анализа и сценарии

Поддержать: предприятие, юридическое лицо, группа, филиал,
подразделение, проект, бизнес-единица, продукт и допустимые измерения.
Контур применения: sector, business_model, jurisdiction, accounting_standard,
financial_reporting_basis, currency, reporting_period, consolidation_scope.

Сценарии: BASE, CONSERVATIVE, OPTIMISTIC, STRESS, CUSTOM.
Сценарий = базовый immutable snapshot + собственные versioned overrides;
никогда не переписывать исходные факты.
Пороговые значения и стратегия разветвления — только версионируемая
конфигурация с обоснованием и контекстом применения.

## 12. Полнота реестра и поэтапное наполнение

Для каждого направления поддерживать coverage matrix:
AnalysisType × Metric × Formula × Methodology × EntityType × Sector × Evidence.

Состояния покрытия:
NOT_SPECIFIED, DRAFT, VALIDATED, IMPLEMENTED, TESTED,
FINANCIALLY_APPROVED, PRODUCTION_ADMITTED, BLOCKED.

Стартовые целевые ориентиры, НЕ текущий статус реализации:
- не менее 200 описанных показателей;
- не менее 100 методологически проверенных формул;
- не менее 20 методик;
- не менее 10 аналитических стратегий;
- не менее 4 сквозных графов.

Цифры не являются потолком. Главная цель — систематическое покрытие
всех релевантных отраслей, методов и типов организаций без дублирования.
Реестр должен позволять масштабироваться существенно дальше.
Запрещено увеличивать счётчики фиктивными записями.

Обязательны поля каждой строки будущего полного каталога:
code; name; definition; metric_kind; source_requirements;
formula_ref; methodology_refs; unit; time_semantics;
dimensions; sector; entity_type; accounting_basis;
params; applicability; exceptions; worked_example;
financial_source_or_decision; revision; sha256; validation_status.

## 13. План дальнейшего развития (только план, не выполненные работы)

R0.1 Repository Foundation — утверждение единого файла-спецификации,
затем структурирование и отдельная рабочая ветка после разрешения на код.
R0.2 Metric Registry — миграции, каталог, контракты и валидаторы.
R0.3 Formula Registry + Calculation DAG — типизированный AST,
планировщик, первый end-to-end расчёт.
R0.4 Strategy Graph — условия, ветки, применимость, сценарии.
R0.5 Result + Findings Graph — неизменяемые результаты и lineage.
R0.6 Catalog Expansion — массовое наполнение и coverage matrix.
R0.7 Graph API Qualification — API и сквозная приёмка.

Первый вычислительный E2E:
Financial Facts → CalcPlan → Liquidity/Profitability Ratios →
Analytical Branch → Immutable Result → Lineage/Findings.

Следующее действие ПОСЛЕ отдельного разрешения пользователя:
спроектировать machine-readable Metric/Formula Registry на базе
согласованной спецификации, затем реализовать минимальную вертикаль.

## 14. Критерии приёмки будущего кода

- Уникальные стабильные коды и неизменяемые опубликованные ревизии.
- Отсутствие циклов и висячих зависимостей Calculation DAG.
- Корректная топологическая сортировка и invalidation.
- Учет единиц, времени, валюты, допустимости деления.
- Контрольные примеры с финансово определённой ожидаемой величиной.
- Явные missing / zero / not-applicable / blocked состояния.
- Immutable plan, проверяемые SHA-256 и lineage.
- Идемпотентность и корректность при конкурентном исполнении.
- Запрет отозванных методик и stale plans.
- Изоляция сценариев.
- Доказуемые branch decisions с причинами перехода.
- PostgreSQL-интеграционные и отрицательные тесты.
- Фактический отчёт PASS/FAIL/SKIP; без выдуманных тестовых результатов.

## 15. Инструкция Codex для продолжения

Работать только с https://github.com/alimbetov/FEngine.
Считать этот файл единственным master-spec документом текущего этапа.
Пока пользователь не разрешил программную реализацию:
1. Не создавать дополнительные документы/файлы и исходный код.
2. Все уточнения к показателям, формулам, методикам и четырём графам
   вносить как версии/дополнения ЭТОГО файла.
3. Не заявлять, что целевое количество формул и методик уже реализовано.
4. Не смешивать техническую валидацию, методологическую проверку и
   независимое финансовое утверждение.
5. Сначала выявлять противоречия в определениях, размерностях,
   периодах и применимости, потом предлагать исправления.
6. Отдельно отмечать финансовые вопросы, требующие решения методолога.
7. При переходе к коду начать с проверяемого R0.2–R0.3, а не с UI.

Итог: FEngine — единый версионируемый семантический каталог и четыре
взаимосвязанных графа, из которых воспроизводимо строятся расчёты,
аналитические маршруты, выводы и стратегии действий.


---

## 16. Сверка знаний с FIN Analyzer: snapshot 2026-11-20 (FEngine v0.2)

**Источник:** alimbetov/fin-analyzer, строго ветка feat/fin-form-library-standalone.
**Зафиксированный исходный HEAD:** c8cbb40e773c6d38dc4032149b0c91f7f27acfcd (2026-11-20).
**Назначение:** заимствовать проверяемые понятия, инвентарь, связи и инженерные ограничения из реального FIN, не выдавая кандидатов за утверждённые расчёты.
**Статус синхронизации:** DOCUMENTATION_KNOWLEDGE_SYNC; никакой код FIN в FEngine не скопирован, база данных не перенесена, тесты FEngine не запускались.
**Сохранено пользовательское ограничение:** пока весь FEngine в одном FENGINE_MASTER_SPEC.md. Не создавать другие файлы и приложения до следующего решения.
**Проверка полноты:** это аудированный архитектурно-методологический снимок ключевых реестров и реализаций, а НЕ построчный импорт всех 840 метрик, 877 полей или каждой формы.

### 16.1. Реальный инвентарь и статус достоверности

| Объект | Количество/состояние в FIN | Правильная интерпретация для FEngine |
|---|---:|---|
| Формы | 166 | Идентичности и редакции форм уже существуют; не создавать 167-ю ради аналитических приложений |
| FINANCE / PLANNING / LEDGERS / DETAIL / SECTOR / EVIDENCE | 8 / 10 / 14 / 59 / 63 / 12 | Взаимоисключающие каталожные семейства, а не отдельные расчётные движки |
| Числовые формы | 154 = 3 SINGLE_RECORD + 151 ROWSET | Единый расчётный контур с разными source adapters |
| EVIDENCE-формы | 12 | Документальные доказательства и поля метаданных, не обязательные numeric outputs |
| Числовые формы с прямым числовым источником | 145 | Остальные 9 числовых форм являются reference-only; не фабриковать источники |
| Физические поля | 877 = 793 source + 84 document metadata | Кандидатные физические контракты, не 877 финансовых метрик |
| Исторический каталог metric definition | 840 | 794 legacy SOURCE_FIELD + 46 ANALYTICAL_OUTPUT; не путать с 793 физическими source-binding |
| Исключение F02.netProfit | 1 | Исторически классифицирован SOURCE_FIELD, фактически unbound FORM_DERIVED_CANDIDATE; отдельный migration/semantic reconciliation |
| Выходные метрики аналитических моделей | 46 уникальных кодов | Существование кода не доказывает наличие формулы или выполненного результата |
| Модели-описания | 42 = 37 DESIGN_ONLY + 5 CALC_PILOT | Пилотный статус модели не означает 5 работающих E2E-движков |
| Пользовательские задачи | 7 CANDIDATE_NOT_S2 | Кандидатные навигационные сценарии, не финансово квалифицированные стратегии |
| Use case → form | 101 связей: 34 CORE / 46 SUPPORTING / 21 EVIDENCE | 53 уникальные формы по прямым связям |
| Формы-источники моделей | 47 уникальных | Совокупно с прямыми связями 71 уникальная форма; 95 форм пока вне связанного goal/model graph |
| Кандидатные formula revisions | 10 в 5 формах | Не равно 154 формам с определёнными финансовыми расчетами |
| Синтетические контрольные примеры | 12 по 10 кандидатным ревизиям | Математические векторы; не независимая финансовая проверка |
| E2E browser gate DC-R2.5 | F02, C01, C02; 3/3 PASS на SHA f5fee543ac8a865ff81e013ad5824e265024a1f6 | Только bounded MANAGEMENT/SYNTHETIC KZT, saved intake → UAT preview → explain/history; не FIN S2 |

Уточнение: 48 формул F001–F048 в разделе 5 FEngine — **наши универсальные иллюстративные кандидаты**. Они НЕ являются выгрузкой 10 кандидатных формул FIN и не могут засчитываться как успешно исполненные формулы FIN.

Ссылки на исходные контракты:
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/README.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/form-library/docs/FIN-R16-FIELD-METRIC-CONTRACT-COMPLETION.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-KPI-R0-INDICATOR-NAVIGATOR-TZ.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-CALC154-METHODOLOGY-COMPLETION-AND-CALC4D5-RUNBOOK.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/qa/FIN-DATA-CALC-R25-UNIFIED-BROWSER-ACCEPTANCE.md

### 16.2. Границы ответственности: FIN ↔ FEngine

FIN Analyzer (существующая реализация):
- **fin_lib**: версии форм, поля, определения метрик, локализация RU/KK/EN/ZH, схемы ввода, редакционные и частично вычислительные контракты.
- **fin_intake**: пользовательские значения и неизменяемые редакции сохранённых данных; существующие FormDraftService и ReportGridService имеют два разных контракта хранения, их нельзя незаметно объединять.
- **fin_fact**: квалифицированный контур точных FactSet со строгими допусками, исходными ревизиями, SHA, изоляцией и INGEST-2 rehash.
- **fin_calc**: candidate formula revisions, typed DAG, SQL/JDBC и Java BigDecimal; production calc_plan/calc_job/result ограничены независимыми воротами.
- **calc4d_uat_*:** отдельное синтетическое UAT-хранилище планов, заданий, receipt и immutable результатов, не аналог production admission.
- **frontend**: реальный React Form Studio, decision-tree навигация и ограниченный Calculate/Explain/History для F02/C01/C02.

FEngine (отдельный будущий продукт):
- Канонический **семантический слой** определений финансовых/экономических метрик, формул, стратегий и версионируемой их применимости к организациям.
- Четыре графа из раздела 4, включая cause/evidence edges и объяснимую трассу анализа.
- Не объявлять FEngine «источником пользовательских фактов» на основании FIN; факты могут поступать через проверяемый адаптер из FIN или другой системы.
- До отдельного ADR не решено, будет ли FEngine самостоятельным вычислительным сервисом, вынесенным совместно используемым Java-модулем или версионируемым knowledge-package поверх FIN. Нельзя порождать внутри FIN второй источник истинных метрик или второй параллельный калькулятор.
- Экспорт/импорт кандидатов из FIN должен быть **read-only / version-pinned** на этапе синхронизации; изменение источника не редактирует исторические записи FEngine.
- В FIN применяются Liquibase и PostgreSQL 16; в FEngine ранее предложен Flyway. Нельзя копировать миграции FIN в FEngine как есть. При интеграции выбрать один migration tool на физическую БД, утвердить схему и версию контракта.

### 16.3. Четыре графа FEngine — уточнение на основе реального FIN

**Graph A / Semantic Metric & Decision Knowledge**
Хранит canonical metric, source field binding, aliases, unit/time/dimension,
method output, accounting basis, sector scope, аудит происхождения, goal и
невычислительные прикладные отношения.

Строго различать три связи:
1. **REQUIRES_DATA** — доказуемая техническая входная зависимость.
2. **HELPS_DECISION** — показатель полезен для решения; не говорит о причинности.
3. **BUSINESS_IMPACT** — гипотеза о влиянии на бизнес, требующая направления влияния, assumptions и отдельной проверки; может быть NON_MONOTONIC/CONTEXT_DEPENDENT.

Не превращать «увеличение X способствует Y» в расчётную формулу без
самостоятельного финансового и причинного обоснования.

**Graph B / Typed Calculation DAG + Cross-Form Reconciliation**
Проверенные идеи FIN: Calc4DTypedDagCompiler компилирует explicit formula revision UUID,
проверяет типы, целостность revision/SHA, missing edges/cycles и топологический порядок.
Calc4DExactFactSetInputResolver привязывает вычисления к точным synthetic TEST_QUALIFIED
FactSet с rehash source revision. Опциональная SQL/JDBC+Java strategy разрешена
только по whitelist, с currency/period/dimension invariant и тестами parity.
Добавить к модели FEngine отдельные RECONCILES_WITH, DIFFERENCE, AS_OF_SNAPSHOT,
PERIOD_COMPARE edges, которые не считаются арифметическими зависимостями автоматически.

У результата сверки самостоятельные состояния:
PASS, DIFFERENCE, NOT_COMPARABLE, MISSING_SOURCE, BLOCKED.
Запрещены автоматический SUM по датам запасов AS_OF, скрытое смешивание IFRS и
MANAGEMENT и считывание «latest» вместо точной входной ревизии.

**Graph C / Goal → Strategy → Method Variant → Required Form Fields**
Текущий FIN имеет 7 goal/use-case, 42 model candidates и граф навигации
«пользовательский вопрос → метрика → кандидатная модель → формы».
Это НЕ то же самое, что квалифицированный граф вычислений.
Целевой **MG-R0.1 read-only resolver**:
goal → output metric → method family/variant/revision → dependency DAG
→ exact physical input metric/field → required form revisions → data gaps.
Система обязана отображать reason codes:
METHOD_MISSING, FINANCIAL_S2_HOLD, MISSING_INPUT, REQUIREDNESS_UNREVIEWED,
POLICY_UNQUALIFIED, UNIT_MISMATCH, AS_OF_INTERVAL_MISMATCH, FX_MISSING,
REVISION_REVOKED, SCENARIO_INCOMPATIBLE.
Затем к нему добавлять стратегии и сценарии с условными переходами.

**Graph D / Evidence, Findings & Action Graph**
FIN подтверждает необходимость разделить редакционное решение,
научно-методический факт, математическую проверку, signed financial S2
и фактическую пригодность к production.
У каждого Finding сохранять lineage:
пользовательская цель → показатель → selected method → formula/parameter SHA
→ source FactSet/revisions → calc/result SHA → reconciliation state
→ интерпретационный rule/reviewer → рекомендация.
Запретить вывод «норматив выполнен» без version-pinned порога,
доказательства применимости и валидной сверки.

### 16.4. Контракты исходных данных: что зафиксировать заранее

Для InputObservation/FactSet:
organizationId; economicEntityId; businessScopeId; projectId; scenarioId;
accountingBasis (IFRS / MANAGEMENT раздельно); dataSpace; formCode/versionId;
fieldCode; metricCode/revisionId; sourceRevisionId; stableBusinessKey;
physicalRowKey; typed value/state; signed semantics; source amount currency;
functional/reporting currency; stock/flow kind; period start/end или exact asOf;
event/effective/posting dates; dimension grain; canonical source SHA; provenance.

Для Formula/Method/CalcPlan:
formulaRevision UUID; AST/allowlisted operation; typed input bindings;
operation and artifact version; parameters/config SHA; methodology selection SHA;
scope/policy/standard revision; source/FactSet SHA; exact units/currency/FX;
time calendar/interval/dimension; zero/missing/rounding policy; as-of and
cutoff; signer evidence; status и revocation epoch; reproducible plan fingerprint.

Для Output:
raw BigDecimal, display rounding separately, unit, status COMPLETE/PARTIAL/
UNDEFINED/MISSING/INVALID/BLOCKED, exact input lineage, reason codes,
execution strategy, UAT/prod admission class, immutable receipt and optional
cross-form reconciliation receipt.

Критические семантические отличия:
- F02.netProfit исторически SOURCE_FIELD, но концептуально derived candidate;
  не использовать исторический kind как единственное доказательство writable input.
- lib_form_field.required — обязательность **входного поля**, не обязательность
  вычисляемого выходного показателя.
- DATA form может легитимно иметь **ZERO_DERIVED_OUTPUTS**.
- 9 reference-only числовых форм нельзя объявлять пустыми/ошибочными
  без проверки межформенных зависимостей.
- 12 документальных форм — validation/evidence, а не forced numeric formula.
- 840 legacy metrics ≠ 840 вычисляемых финансовых показателей.

### 16.5. Области фактически работающих вычислений и их пределы

**FIN F02 synthetic test-only**:
source F02.netRevenue, F02.cogs, F02.operatingExpenses;
grossProfit = netRevenue - cogs;
grossMargin = grossProfit / netRevenue (в FIN output является RATIO: 0.5,
а не 50 как процентная шкала из общей формулы FEngine F002);
operatingResult = grossProfit - operatingExpenses.
При нулевой выручке grossMargin UNDEFINED/INVALID_ZERO_DENOMINATOR,
но остальные выходы могут остаться определёнными.
F02 kernel использует BigDecimal, строгие синтетические KZT/monthly условия.
Не переносить его test rounding как универсальную бухгалтерскую норму.

**FIN C01 synthetic trade receivables**:
C01 gross = непогашенный остаток на exact asOf ДО положительного allowance;
netReceivables = SUM_AS_OF(gross) - SUM_AS_OF(allowance).
Declared overdue входит в gross, не прибавляется отдельно.
overdueGrossShare = SUM_AS_OF(overdue)/SUM_AS_OF(gross), если сумма gross > 0
и overdue присутствует в каждой учтённой строке.
Credit balances/advance и allowance>gross — отдельные проблемы классификации /
review в ограниченном positive-stock UAT, не автоматическое write-off.

**FIN C02 synthetic trade payables**:
outstanding = непогашенная признанная обязанность на exact asOf;
totalOutstanding = SUM_AS_OF(outstanding).
overdue — подмножество outstanding, overdueOutstandingShare = overdue/outstanding;
авансы поставщика не зачитываются автоматически.
Частичные платежи и amendments должны быть подтверждены source events;
сейчас UAT читает уже предоставленный stock snapshot и сам не восстанавливает
allocation history.

**FIN UAT execution foundation**:
10 кандидатных formula revisions для 5 форм; GROUP_BY/RATIO_OF_SUMS и
предварительные typed арифметические операторы; 12 synthetic mathematical cases.
Calc4DUatPlanStore и Calc4DUatLeasedWorker реализуют изолированный
UAT-only план, leased job, fencing epoch, source revalidation,
атомарное сохранение immutable result и SUCCEEDED job.
FIN_CALC4D_UAT_EXECUTION_ENABLED=false по умолчанию; нет разрешённого
автономного production scheduler и нет независимого S2.
Не путать рабочий synthetic UAT queue с допущенным production executor.

**DC-R2.5 browser evidence**:
3 Chromium/Playwright tests PASS на отдельном exact SHA
f5fee543ac8a865ff81e013ad5824e265024a1f6,
real saved fin_intake → calculation preview → revision compare.
Это доказательство только конкретного тестового среза,
не автоматический GREEN нынешнего HEAD или финансовая приёмка.

Источники:
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-CALC-4D-EXECUTION-FOUNDATION-AND-METHODOLOGY-REGISTRATION.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-CALC154-C01-C02-EDITORIAL-POLICIES-V2-2026-11-20.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-DATA-CALC-R2-CROSS-FORM-CALCULATION-ROADMAP.md

### 16.6. Ветви финансовых приложений A01–A06: операционный DAG

Все приложения **поверх существующих 166 форм**, не новые report forms:
- **A01 / Obligations & Settlement Allocation**: C01/C02/C11 и DF-CSH,
  durable obligation ID, due-date amendments, payment allocation,
  overdue/aging; обязательный предок реального loan plan/fact.
- **A02 / ECL & Credit Risk**: cohorts, aging buckets, verified historical loss,
  recognized ECL, policy variants, forward-looking assumptions;
  write-off как самостоятельное подтверждённое событие, не арифметический shortcut.
- **A03 / Inventory Accounting**: item/lot movements, FIFO/WAC/specific ID,
  NRV, C03→COGS/F02→P06 DIO; item granularity and returns.
- **A04 / Fixed Asset Accounting**: component/useful-life/residual/impairment
  policies, depreciation, C04/F01/F02/P05 roll-forward.
- **A05 / Loan Contract & Payment Schedule Studio**: C05, P04, P09, F01/F02/F03;
  договорные события, комиссии, dates/day-count, cash schedule,
  amortized-cost/EIR schedule и план-факт.
- **A06 / Investments & Scenarios**: dated FCFF→WACC→Enterprise Value,
  FCFE→Ke→Equity Value; NPV, ambiguity-aware IRR, terminal value,
  сценарии P01–P09; запрет FCFF+Ke и FCFE+WACC.

Строго разделить в A05:
1. NOMINAL_CONTRACT_RATE — начисление договорных процентов/cashflows.
2. IFRS9_EIR — амортизированная стоимость, при применимости стандарта и
   квалифицированных комиссиях/денежных потоках.
3. KZ_GESV — отдельно квалифицируемая регуляторная эффективная ставка РК,
   только для соответствующих договоров и актуальных НПА.
4. ANNUITY / EQUAL_PRINCIPAL / CUSTOM — погашение основного долга
   (отдельная ось от номинальная/EIR/ГЭСВ).

A05-R1 — только proposed specification, 38 acceptance checks не являются PASS.
Не создавать для него новый независимый источник договорных финансовых данных.
C05 сохраняет исходную контрактную identity/revision, P04/P09 — derived/read-only
проекции и сверки, не молчаливое перезаписывание существующих строк.

Исходники:
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-CALC-APPS-R0-SIX-APPLICATION-CONTRACTS-AND-ROADMAP.md
- https://github.com/alimbetov/fin-analyzer/blob/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd/docs/FIN-CALC-A05-R1-LOAN-CONTRACT-PAYMENT-SCHEDULE-STUDIO-TZ.md

### 16.7. Политики, операторы, ветвление, методология

FIN в каталоге выделяет 23 предварительных operator families на 154
формы (это не 23 финансово проверенных вычислительных реализации).
Предлагаемая частота по формам:
SUM 128; GROUP_BY 127; PERIOD_COMPARE 74; RATIO 25; ROLL_FORWARD 15.
Встречаются также AGING, ALLOCATION, AMORTIZATION, NPV, IRR,
SCENARIO и другие design-only потребности. Новую операцию добавлять
только после доказанного требования конкретного output contract.
Суммирование запасов AS_OF в разных датах без выбора effective snapshot
запрещено. Для совместимых интервалов и потоков использовать отдельно
согласованную агрегирующую операцию.

Референс FIN содержит 10 редакционных P0/P1 policy decisions:
9 EDITORIAL_ACCEPTED_WITH_GATES, 1 NUMERIC_PARAMS_NOT_APPROVED,
не финансовый S2. В FEngine каждое правило и threshold — versioned policy
с документированным scope и source authority. Scope resolution:
SYSTEM → ORGANIZATION → PROJECT → SCENARIO, по типизированным
ограничениям, без произвольной подмены финансовой нормы.
Алгоритм и параметры — отдельно версионируемые сущности.

Проверка достаточности:
FORMULA_VERIFIED → (methodology evidence + applicability qualification)
→ FINANCIAL_S2_APPROVED → PRODUCTION_ADMITTED.
Состояние AUTO_QUALIFIED не приравнивать к независимому S2.
Списки BLOCKED/MISSING/POLICY_INCOMPLETE/REVIEW_REQUIRED — явные
результаты валидатора, не скрытые исключения и не «ноль».

### 16.8. Целевые Cross-Form зависимости для FEngine

Видимый кроссформенный DAG следующего поколения:
1. A01 obligations/payments → C01/C02 amount, due/overdue and aging → P06 DSO/DPO.
2. A01 + credit classification → A02 ECL → C01 allowance/net and F01 assets.
3. Inventory source events → A03 → C03 balance → F02 COGS → P06 DIO.
4. Revenue C07 and recognized sales policy → F02 Revenue/Operating Result.
5. Asset component events → A04 → C04 book value/F01 assets/F02 depreciation.
6. C05 + loan events → A05 nominal cash schedule + IFRS9 EIR → P04/P09;
   cash projection to F03/P03, accounting carrying and interest to F01/F02.
7. F01/F02/F03 + P01–P06 + FX/basis/period controls → reconciled forecasts.
8. Reconciled dated flows → A06 P07/P08 DCF/scenario.
9. KPI views (CCC, DSCR, leverage, liquidity, cash runway, margin, NPV)
   consume qualified metric outputs; не генерируют недостающие исходные данные.

Каждому edge требуется: source type; target type; period mapping;
unit/currency policy; grain; ordering; variant revision; applicability;
reconciliation tolerance; lineage; BLOCKED reason; edge type
(CALCULATES, RECONCILES, EVIDENCES, HELPS_DECISION, BUSINESS_IMPACT).

Недостаток входного поля или метода блокирует конкретный downstream output,
но не должен уничтожать независимые уже корректно вычисленные outputs.

### 16.9. Стратегическая матрица с пользовательским входом

FIN уже описывает семь задач:
1. FINANCIAL_HEALTH — диагностика финансового состояния.
2. INVESTOR_READINESS — диагностика для инвестора.
3. BUSINESS_PLAN — подготовка бизнес-плана.
4. BANK_FINANCING — подготовка к кредитованию.
5. INVESTMENT_APPRAISAL — оценка инвестпроекта.
6. MANAGEMENT_CONTROL — бюджет/управленческий анализ.
7. GRANT_PROGRAM — грант и финансирование программы.

Их source model refs — кандидаты. Сохранять заявленную различимость:
- CORE form = главный источник для цели;
- SUPPORTING = полезное дополнение;
- EVIDENCE = подтверждающие документы;
- MODEL_INPUT = доказанный вход модели (только после методологического
  version-pinned контракта);
- MISSING_REQUIRED = отсутствующий квалифицированный вход;
- NOT_APPLICABLE = самостоятельное обоснованное состояние.

FEngine может расширять стратегические задачи для экономики предприятий,
банков, НКО и отраслей, но не считать все FIN 166 форм универсально
обязательными для любой цели.

### 16.10. Связка с правилами FEngine v0.1 и корректировка roadmap

**Не менять:** четыре графа, immutable/typed versions, ацикличность
вычислительного DAG, независимый S2, единый файл, FEngine как самостоятельная цель.

**Приоритет v0.2:**
- R0.K1 — подтверждённый каталог и инвентарь: сверить все 166 forms,
  877 fields, 840 legacy metric definitions, 46 analytic outputs,
  distinct source-role и DRAFT квалификацию; не допускать identity collision.
- R0.K2 — crosswalk from FIN:
  FIN form/field/metric/model/use-case/method code → FEngine canonical code
  + exact source repository/branch/commit/file/revision;
  mapping не равен финансовому утверждению.
- R0.K3 — Read-only **Metric Graph MG-R0.1** contract:
  goal → indicator → method variant → dependency → physical source fields,
  gaps/readiness; запрет второго calc engine в FIN.
- R0.K4 — Typed calculation DAG & reconciliation spec with
  AS_OF/INTERVAL/YTD, FX/accounting-basis and source SHA constraints.
- R0.K5 — Methodology completion backlog для всех 154 numeric forms:
  per-form SOURCE_ONLY/CALCULATED/MIXED/CROSS_FORM/NEEDS_RESEARCH,
  mandatory vs optional outputs, independent golden controls,
  explicit 9 reference-only decisions.
- R0.K6 — Outcome/Findings/Strategy graph:
  clear claim taxonomy, blocked paths and audit evidence.
- R0.K7 — Operational integration design AFTER separate approval:
  choose whether FEngine is library/service/knowledge-package;
  establish source-of-truth, ABI/API compatibility, independent migration
  strategy and governance. No code until explicit permission.

**Readiness evidence must be per output, not per form**:
REGISTERED → INPUT_CONTRACT_PINNED →
METHODOLOGY_VARIANT_AND_POLICY_PINNED → MATH_GOLDEN_GREEN →
SQL_JAVA_PARITY_GREEN (если нужно) → INTAKE_UAT_E2E_GREEN →
CROSS_FORM_RECONCILED (если нужно) →
FINANCIAL_S2_QUALIFIED → PRODUCTION_ADMITTED.

Управление статусами: машинно-проверяемый exact repository SHA,
test run ID, input fingerprints, verified expected/actual, policy/method
revision SHA, reviewer identity и timestamp. Результат тестов одного SHA
не переносится на HEAD автоматически.

**Разделение планов**: FIN roadmap DC-R2.6→R2.16 и A05-R1 следует
использовать как источник архитектурных зависимостей, но не как доказательство
того, что в FEngine создана реализация или импортированы базы.

### 16.11. Запрещённые упрощения и открытые решения

P0 — Не интерпретировать 840 definition как 840 работающих формул.
P0 — Не интерпретировать 42 model descriptors как 42 executable methods.
P0 — Не переводить 877 physical fields в 877 semantic facts без mapping.
P0 — Не объединять два FIN writer автоматически (FormDraft/ReportGrid).
P0 — Не считать редакционные C01/C02 IFRS/S2-certified.
P0 — Не изобретать SUM для каждой из 154 форм; SOURCE_ONLY допустим.
P0 — Не допускать ручных SQL/JavaScript expressions из каталоговых строк.
P0 — Не превращать hash verification в подпись независимого ревьюера.
P0 — Не усреднять и не суммировать stock AS_OF через несколько дат.
P0 — Не смешивать F02 margin RATIO=0.5 и FEngine PERCENT=50 без явной unit/scale conversion.
P0 — Не смешивать cash contractual debt service, EIR и KZ_GESV.
P0 — Не считать FIN UAT leased workers автоматически production-ready.
P1 — Уточнить у методологов semantics всех 46 analytic output metrics,
   затем требуемые исходные наборы и конкретные методики для 154 форм.
P1 — Принять отдельное ADR о режиме интеграции FEngine↔FIN.
P1 — Актуализировать snapshot при смене FIN HEAD, не стирая предыдущий.

### 16.12. Source register для дальнейших сверок

Главные документы и машиночитаемые реестры, закреплённые исходным HEAD:
- docs/FIN-CALC-R0-COVERAGE-166-BASELINE.tsv
- docs/FIN-CALC-R0-FIELD-COVERAGE-794-BASELINE.tsv
- docs/FIN-CALC154-METRIC-COVERAGE.tsv
- docs/FIN-CALC154-FORM-STATUS.tsv
- docs/FIN-CALC154-MODEL-OUTPUT-COVERAGE.tsv
- docs/FIN-CALC154-METHODOLOGY-OPERATION-GAPS.tsv
- docs/FIN-CALC4D-154-METHODOLOGY-AUTHORING-BACKLOG.tsv
- docs/FIN-DATA-CALC-R2-ALL154-FORM-READINESS.tsv
- docs/FIN-DATA-CALC-R2-CROSS-FORM-OUTPUT-MATRIX.tsv
- form-library/src/main/resources/catalog/analytics-model-catalog.tsv
- form-library/src/main/resources/catalog/use-case-catalog-r10.tsv
- form-library/src/main/resources/catalog/use-case-form-map-r10.tsv
- form-library/src/main/resources/catalog/calc154-formula-contracts-v1.tsv
- form-library/src/main/resources/catalog/calc154-mathematical-control-v1.tsv

Подтверждённые архитектурные источники:
- docs/FIN-CALC-166-SQL-JDBC-JAVA-HYBRID-TZ.md
- docs/FIN-CALC-R0-INCREMENTAL-CALCULATION-ARCHITECTURE-TZ.md
- docs/FIN-CALC-4D-EXECUTION-FOUNDATION-AND-METHODOLOGY-REGISTRATION.md
- docs/FIN-CALC154-METHODOLOGY-COMPLETION-AND-CALC4D5-RUNBOOK.md
- docs/FIN-KPI-R0-INDICATOR-NAVIGATOR-TZ.md
- docs/FIN-UX-R1-DECISION-TREE-IMPLEMENTATION.md
- docs/FIN-DATA-CALC-R2-CROSS-FORM-CALCULATION-ROADMAP.md
- docs/FIN-CALC-APPS-R0-SIX-APPLICATION-CONTRACTS-AND-ROADMAP.md
- docs/FIN-CALC-A05-R1-LOAN-CONTRACT-PAYMENT-SCHEDULE-STUDIO-TZ.md
- docs/FIN-CALC154-C01-C02-EDITORIAL-POLICIES-V2-2026-11-20.md
- docs/FIN-CALC154-AUTOQUAL-1-STANDARDS-BASED-QUALIFICATION-TZ.md
- form-library/docs/FIN-R16-FIELD-METRIC-CONTRACT-COMPLETION.md
- docs/qa/FIN-DATA-CALC-R25-UNIFIED-BROWSER-ACCEPTANCE.md

Все относительные пути выше относятся к:
https://github.com/alimbetov/fin-analyzer/tree/c8cbb40e773c6d38dc4032149b0c91f7f27acfcd

### 16.13. Gate для следующего Codex-шага

На текущем этапе обновлён ТОЛЬКО текстовый master spec FEngine.
Следующее содержательное задание: сделать READ-ONLY mapping inventory
из FIN кода и каталогов в одну утверждаемую таблицу внутри этого файла,
с учётом разницы 793 vs 794, 840 vs 46, 10 formula candidates vs 42 model descriptors.
Требуется полный построчный аудит перед заявлением 100% покрытия.
Никаких новых файлов и разработки до отдельного решения пользователя.
