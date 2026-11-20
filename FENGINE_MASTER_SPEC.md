# FEngine — единая спецификация финансово-экономического аналитического ядра

Версия документа: 0.5 (83 model contracts, 81 typed dataset DTO candidates, Python-first hub requirements)
Дата: 2026-11-20
Репозиторий: https://github.com/alimbetov/FEngine
Статус: DRAFT / синхронизация знаний с FIN на 2026-11-20; архитектурное задание; не является свидетельством реализованных расчётов.
Правило текущего этапа: хранить канонический реестр/обзор в ЭТОМ MASTER ФАЙЛЕ; по прямому решению пользователя детальные ТЗ ведутся отдельными приложениями в docs. Не создавать Python/Rust исходный код, сервисы, схемы БД или миграции до отдельного согласования.

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


---

## 17. FEngine HPC-R0 — Python-first Mathematical Reference → Rust High-Performance Calculation Engine (предлагаемая архитектура)

**Решение/статус:** DESIGN_PROPOSAL / NOT_IMPLEMENTED / NOT_BENCHMARKED / NOT_FINANCIALLY_APPROVED.
**Дата:** 2026-11-20.
**Текущий этап:** дополнение ТОЛЬКО к единому FENGINE_MASTER_SPEC.md. Самостоятельных исходных файлов Python/Rust, Crate, микросервиса, стенда и performance test в FEngine пока нет.
**Scope:** FEngine как самостоятельный проект; FIN Analyzer — один из возможных квалифицированных источников контрактов/FactSet через version-pinned adapter. Не заменять текущие FIN Java/SQL-механизмы без подтверждённого parity и performance gate.

### 17.1. Цель, гипотеза и ограничения

Цель: принимать типизированные **пакеты массивов фактов/входных параметров**
и набор допущенных вычислительных заданий, эффективно исполнять связанные
формулы и модели, возвращать **массивы результатов с состояниями ошибок и
lineage** для различных Java, Python и других сервисов.

Гипотеза ускорения: CPU-bound расчетные ядра со значительными пакетами и
повторяющимися операциями могут выиграть от Rust (компиляция, контроль
аллокатора, параллелизм, колонное исполнение). Ускорение НЕ гарантировано:
небольшие scalar calls, JDBC pushdown, сетевые serialization и бизнес-логика
Spring могут быть быстрее/дешевле без нового сетевого hop.
Нужно отдельно измерять compute-only и full end-to-end.

Rust — **data-plane / numerical execution**.
Java/Spring Boot — control-plane (authn/authz, tenant, source admission, immutable
CalcPlan, input resolving, orchestration, job, transaction, audit, result publication).
PostgreSQL — source of truth и эффективные set-based operations (filter/joins/
aggregation/win functions); pushdown может оказаться выгоднее Rust.
Python — независимый reference-oracle / исследовательский и тестовый контур,
НЕ обязательный production inference/finance dependency.

Управление графами: четыре графа FEngine из раздела 4 остаются
семантической/методологической системой; Rust исполняет **только
компилированный, заранее разрешённый, acyclic Calculation DAG**, не
навигационный и не reasoning graph, которые могут содержать бизнес-ветки.
Стратегический граф разрешает метод/вариант и условия входа до отправки
задания; узлы результата/finding формируются поверх точных вычислений.

### 17.2. Строгая последовательность Python → Rust, но по вертикалям

Вместо «сначала реализовать на Python сразу все 154 формы, потом переписать»
ввести repeatable **помодельный квалификационный конвейер**:

P0. Автор выбирает одну финансовую/экономическую модель и её применимость
   (метрика, входы, период, валюта, единица, policy, формула, варианты).
P1. Математическое определение + source evidence + independently worked golden
   examples, подписанные/проверенные ответственным методологом.
P2. Python reference implementation: decimal.Decimal и явный Context,
   либо Fraction/integers там, где математически применимо;
   собственные правила rounding/missing/overflow/IRR root selection.
P3. Python deterministic test suite: normal, boundary, negative,
   fuzz/property/metamorphic tests и large-shape tests.
P4. Опубликованный **golden corpus**: входы, ожидаемые выходы/состояния,
   алгоритм, версия формулы/параметров, source provenance, SHA-256,
   policy и expected calculation precision.
P5. Rust implementation **той же версии** с тем же typed contract,
   positive/negative tests и golden corpus; никакой автоматической
   трансляции случайного Python кода в production Rust.
P6. Differential tests Python ↔ Rust ↔ Java/SQL (когда там существует
   такая же методика) + cross-language serialization + replay.
P7. Benchmark CPU+memory+end-to-end (Rust vs Java/SQL) на одинаковых
   input snapshots; если выигрыш недоказан — сохранять действующий маршрут.
P8. Методологическое review и отдельный financial S2 gate для
   production admission; математическое совпадение НЕ заменяет S2.

Важно: Python тоже может содержать ошибки. Эталонность возникает из
независимых контрольных примеров, property invariants и ревью, а не
только потому, что вычисления написаны на Python.

Категории сравнения:
- EXACT: fixed decimal arithmetic, balances/ratios по полному
  контракту, status и currency/unit/period совпадают буквально
  после явного normalized scale/quantization.
- NUMERICAL_APPROXIMATION: EIR/IRR/NPV root solving, оптимизация,
  сценарные численные методы; проверять root count/policy, остаточную
  ошибку уравнения, заранее утверждённые absolute/relative tolerances,
  детерминированность и одинаковую семантику округления на выходе.
- NONDETERMINISTIC_MODELS (future): вероятностные/ML модели,
  отдельная статистическая acceptance policy, никогда не применять
  «точность ±ε» к денежным проводкам автоматически.

В golden корпусе должны быть также zero denominator, decimal overflow,
negative/credit balances, signed flows, currency mismatch, missing/null,
NOT_APPLICABLE, AS_OF vs INTERVAL, leap year, day-count, duplicate keys,
revoked source, stale plan, aggregation grain, cross-form and cases
for multiple/no IRR roots.

### 17.3. Предлагаемая архитектура Rust ядра

**Core (без network и без DB):**
- typed canonical batch: columnar arrays with schema, values and value-state bitmap;
- immutable compiled plan (ops, typed dependencies, version/policy SHA);
- policy-driven decimal execution: ADD/SUBTRACT/RATIO,
  SUM_FLOW/LAST_AS_OF, GROUP_BY, PERIOD_COMPARE, ROLL_FORWARD,
  RATIO_OF_SUMS, RECONCILE; domain operators добавлять только по доказанной
  методике;
- graph execution: validation, topological ordering, dependency closure,
  skip/propagate/partial statuses, intermediate results and lineage;
- batch scheduling: limit concurrency, memory usage and time;
- deterministic reduction: explicit ordered fold or proved
  associative/exact accumulator, stable grouping, safe overflow policy;
- checked arithmetic and explicit rounding stages; forbid f32/f64 for
  monetary/covenant/accounting results;
- no SQL execution, networking, filesystem or dynamic plugin loading inside core;
  no eval of user-authored expressions.

**Transport adapter:**
- phase 1: single long-lived Rust worker service with gRPC/Protobuf
  typed request/response and internal unary batch calls; Rust core is
  separately testable library and can run embedded in tests;
- phase 2 (only if benchmarks justify): Apache Arrow IPC / Arrow Flight
  for large columnar RecordBatch transfer and streaming; define
  schema evolution and decimal compatibility first;
- streaming execution for huge datasets with bounded memory and backpressure;
- maintain service/connection pools; avoid 1 RPC per scalar metric.

**Storage and authority:**
- Java coordinator creates/validates exact CalcPlan and authorized source set,
  passes validated resolved values or protected immutable batch handles;
- Rust service must independently validate immutable plan schema/version,
  worker admission class, allowed operation IDs, scope, batch fingerprints,
  resource bounds and exact source plan references;
- rust executor returns result buffers + hashes; Java commits
  under trusted transaction/admission and idempotency;
- no network-available endpoint permitted to approve financial S2;
- short-lived, scope-bound service credentials, mTLS and quotas for
  actual remote execution; never trust tenant/org from free-form payload;
- no bulk logging of financial raw data and no Python in production critical path.

### 17.4. Finance-safe numeric representation and interoperability

Do not store financial money as JSON float/double.
Wire representation for initial small batches:
- decimal values as exact unscaled integer + scale, or canonical decimal
  **string** with protocol-level precision/scale and unit metadata;
- input data state separately: PRESENT, MISSING, NULL, NOT_APPLICABLE,
  INVALID; zeros are normal PRESENT values;
- per-column/per-row unit, currency policy, time basis and grain contract.
All payloads are versioned and bounded.

Rust numeric candidates to benchmark / select:
- checked i128 scaled integers for homogeneous fixed-scale cases;
- rust_decimal for bounded conventional decimal arithmetic, **not arbitrary
  Java BigDecimal replacement** (96-bit coefficient; max scale 28);
- Arrow Decimal128 for columnar exchange (up to 38-digit precision)
  and Decimal256 for larger interchange; **the existence of Arrow
  Decimal256 data type does not itself guarantee identical math operator
  coverage or overflow behavior**;
- arbitrary precision BigDecimal/BigInt/Rational where finance policy,
  numerical guardrails and performance comparison require it.

Python decimal.Context and Java BigDecimal differ by default in precision/
rounding/exception behavior; every algorithm must specify precision,
intermediate rounding, scale and overflow. Round *after* aggregation unless
method policy explicitly requires per-item rounding. Beware rate/balance
calculations with repeated multiplication and iterative solvers; a single
global fixed scale is not enough for every application.

### 17.5. Batch Request / Result — целевой пример контракта (DESIGN ONLY)

Do not allow caller-supplied SQL, arbitrary AST, Python code or formula strings.
Caller supplies server-known IDs and pinned revisions/plan hashes.

Request shape (illustrative, NOT an active API):
{
  "contractVersion": "FENGINE-BATCH-V1",
  "tenantScopeId": "pinned-scope-ref",
  "calcPlanId": "immutable-plan-ref",
  "calcPlanSha256": "<64 hex digest>",
  "requestId": "stable-idempotency-key",
  "batch": {
    "rowIds": ["r1", "r2"],
    "columns": [
      {"metricCode":"F02.netRevenue","type":"DECIMAL","scale":2,"values":["200.00","300.00"]},
      {"metricCode":"F02.cogs","type":"DECIMAL","scale":2,"values":["100.00","180.00"]},
      {"metricCode":"F02.operatingExpenses","type":"DECIMAL","scale":2,"values":["50.00","70.00"]}
    ],
    "valueStates": "typed state arrays aligned by rowId",
    "reportingCurrency":"KZT",
    "periodKind":"INTERVAL",
    "periodCode":"PINNED_MONTH"
  },
  "tasks":[
    {"taskId":"gross","methodRevisionRef":"pinned-F02-gross-profit"},
    {"taskId":"margin","methodRevisionRef":"pinned-F02-gross-margin"},
    {"taskId":"operating","methodRevisionRef":"pinned-F02-operating-result"}
  ]
}

Response shape (illustrative):
{
  "contractVersion":"FENGINE-BATCH-V1",
  "requestId":"stable-idempotency-key",
  "calcPlanSha256":"<64 hex digest>",
  "rowIds":["r1","r2"],
  "results":[
    {"taskId":"gross","metricCode":"F02.grossProfit",
     "unit":"KZT","values":["100.00","120.00"],"states":["COMPLETE","COMPLETE"]},
    {"taskId":"margin","metricCode":"F02.grossMargin",
     "unit":"RATIO","values":["0.5","0.4"],"states":["COMPLETE","COMPLETE"]},
    {"taskId":"operating","metricCode":"F02.operatingResult",
     "unit":"KZT","values":["50.00","50.00"],"states":["COMPLETE","COMPLETE"]}
  ],
  "resultSha256":"<64 hex digest>",
  "lineageRef":"immutable-output-manifest-ref",
  "warnings":[]
}

При разных task groups возможны row-wise, grouped и aggregate outputs;
**нельзя обещать 1:1 число выходных строк для GROUP_BY**. Требуется typed
ResultShape: ROW_ALIGNED, GROUPED, AGGREGATE, SERIES, SCENARIO_TREE.
Массивы в строковых JSON — только учебный DTO. Для массового runtime
выбирать protocol-specific binary/columnar data, если тесты доказали смысл.
Поля "<64 hex digest>" — placeholders и не выдаются за реальные SHA.

### 17.6. Кандидатные библиотеки и доказательства выбора

Python:
- decimal.Decimal + Context — reference exact-decimal implementation.
- pytest + hypothesis — deterministic golden and property-based tests.
- pandas/Polars/numpy — только подходящие vector/data operations;
  проверять dtype, не подменять Decimal float64 в финансовых формулах.
- pyarrow для Decimal128/256 и межъязыковой проверки Arrow schema.
- PyO3/maturin — опциональное локальное Python↔Rust FFI для parity и
  compute-only benchmark; не подменяет проверку remote gRPC.
Rust:
- crate с чистым ядром + rayon (data parallelism там, где это корректно).
- checked decimal backend (i128/rust_decimal/BigDecimal по спецификации).
- tonic + prost для gRPC.
- arrow / arrow-flight только как optional batch transport optimization.
- criterion для compute-only benchmark; интеграционные нагрузочные
  тесты — отдельный внешний клиент и реальный Java/Rust/PG сетевой путь.
- Polars/Rust columnar expressions рассматриваются для проекций/
  агрегаций, но нельзя объявлять их эквивалентом подписанных финансовых
  формул или использовать float dtypes для денежных расчётов.

Официальные документы для tech due diligence (перепроверять версии при коде):
https://docs.python.org/3/library/decimal.html
https://hypothesis.readthedocs.io/
https://pyo3.rs/main/
https://arrow.apache.org/rust/arrow/datatypes/enum.DataType.html
https://docs.rs/rust_decimal/latest/rust_decimal/
https://docs.rs/rayon/latest/rayon/
https://criterion-rs.github.io/book/
https://github.com/apache/arrow-rs/tree/main/arrow-flight

### 17.7. Бенчмарки без искусственных обещаний ускорения

Сравнить:
(1) Java 21 BigDecimal локально и/or существующий FIN kernel,
(2) PostgreSQL 16 set-based SQL/JDBC,
(3) Python Decimal reference,
(4) Rust core in-process,
(5) Rust gRPC over same host and over representative internal network,
(6) Arrow Flight only after core baseline,
(7) при необходимости SQL aggregation → Rust final hybrid.

Фиксированные размеры: 1, 10, 1_000, 10_000, 100_000, 1_000_000 rows;
операторные группы: arithmetic, SUM, GROUP_BY, RATIO_OF_SUMS,
multi-step DAG, debt amortization, dates/day-count, DCF/IRR, scenario tree.
Для смешанных реализаций сравнивать **одинаковые input hashes,
calc policy, output shape и materialization**.

Измерять: p50/p95/p99 end-to-end latency, compute CPU time,
serialization/deserialization, network hop, GC/allocation pressure,
RSS/peak memory, bytes transmitted, throughput, contention, errors,
cold/warm start, concurrency (1/8/32/64), output SHA mismatch count.
GPU/SIMD/Polars/Arrow имеют смысл только после профиля узкого места.

Предлагаемые **пороговые цели проекта**, не измеренные достижения:
- correctness: 0 mismatches в утверждённых EXACT golden кейсах;
- numerical models: 0 violations принятой tolerance/root policy;
- safety: 0 unintended production admissions / cross-tenant escapes;
- performance: для выбранного Rust batch-кандидата >=2.0×
  compute-only throughput relative to matched Java baseline при
  равной точности, **и** отсутствие ухудшения p95 full-path; пороги
  пересматриваются после измерения на целевом оборудовании;
- ресурсные ограничения и OOM handling — обязательные, memory caps per request.
Отчёт должен указывать процессор, число ядер, Rust/JDK/Python/PG версии,
reproducible fixture, branch SHA, CI run и доверительные интервалы.
Если на малом batch размер Rust проигрывает Java или PG, выбрать
LOCAL_JAVA / SQL_PUSHDOWN, не вынуждать лишний network hop.

### 17.8. Встраивание в существующую модель FEngine/FIN

Рассматривать execution modes:
- SQL_PUSHDOWN — фильтры, агрегаты, temporal/group joins в PostgreSQL;
- JAVA_LOCAL — small batches, legacy parity/backward compatibility;
- RUST_REMOTE_BATCH — CPU-heavy, large arrays, independent compiled plans;
- RUST_EMBEDDED_TEST_ONLY — прототип/локальная parity без IPC;
- SQL_PLUS_RUST — только после измеренного выигрыша гибридной стратегии.

Выбор стратегии фиксируется в immutable CalcPlan
(executorKind, version, capability manifest SHA, exact numeric policy).
В FIN нельзя обойти существующие S2/admission/FactSet checks новым
Rust endpoint. Future FIN adapter должен сначала использовать
существующие версии и команды; FEngine не становится третьим writer.
На случай ошибки/недоступности Rust — fail-closed или разрешённый
версионированный fallback, только если результаты гарантированно
эквивалентны и не обходятся доказательства финансового допуска.

### 17.9. Первые модельные вертикали (не 154 сразу)

HPC-PY-01: F02 Python oracle:
netRevenue - COGS → grossProfit; grossProfit/netRevenue → grossMargin RATIO;
grossProfit - operatingExpenses → operatingResult; zero/missing/negative
scopes only as explicitly allowed. Сопоставить с точными FIN codes,
ratio scale и существующим FIN synthetic golden.

HPC-PY-02: C01/C02 snapshot as-of:
SUM_AS_OF(gross) - allowance, declared overdue subset, outstanding,
non-overlapping same-currency asOf; источник событий A01 пока отсутствует.
Проверить duplicate obligation key vs row id, invalid allowance/overdue.

HPC-PY-03: F01/F03 control math:
assets - liabilities - equity reconciliation, opening cash +
signed CFO/CFI/CFF +/- separately modeled FX bridge - closing cash;
все политики и исключения независимо согласовать.

HPC-PY-04: ROWSET C07/P06:
GROUP_BY, RATIO_OF_SUMS, DSO/DIO/DPO и CCC только с совместимыми
дневными периодами, кредитными продажами и закупками,
не подставлять COGS автоматически для DPO.

HPC-PY-05: A05 loan schedules:
dated annuity/equal principal/custom cash schedule, fees, day-count;
отдельные номинальная ставка, IFRS9 EIR, KZ_GESV; plan-fact с A01
после источников платежей; проценты и rounding на каждой стадии.

HPC-PY-06: A06 investments:
NPV, FCFF/WACC vs FCFE/Ke, IRR multiple roots, XIRR/date semantics,
DCF terminal assumptions, scenarios; нет универсального «единственного IRR».

Реализовывать Rust-прототип для уже квалифицированной Python-модели
последовательно, не ожидая окончания всего каталога; это снижает
риск массового переписывания неверных assumptions.
FEngine Python stage не означает, что FIN 154 форм уже завершены.

### 17.10. Этапы, выходы и критерии GO

HPC-R0.0 — **предлагаемая архитектура (этот раздел)**, без кода.
HPC-R0.1 — Data/Decimal/Graph/Batch contract review:
typed schema, memory caps, status taxonomy, batch result shapes, exact API
transport; выбрать protocol и test matrix до реализации.
HPC-R0.2 — Python math reference и golden corpus для первых 3
семейств F02/C01/C02, с independent human-confirmed expected examples;
конкретные source policies ограничены pilot.
HPC-R0.3 — Rust pure core, checked decimals, DAG evaluator и batch test
для уже подтверждённых Python контрактов.
HPC-R0.4 — Differential/property/fuzz/serialization tests;
exact results vs policy tolerance; verify third-party Rust lib behavior.
HPC-R0.5 — Microbenchmark + SQL/Java/Rust end-to-end benchmark;
выбрать per-form/per-task execution routing с доказуемыми границами.
HPC-R0.6 — Rust gRPC worker service, quotas, versioned request,
admission, idempotency, deadlines, cancellation and metrics.
HPC-R0.7 — Operational integration through trusted orchestrator,
leases/fencing/source revocation, result commit, observability,
financial S2 policy and release qualification.
HPC-R0.8 — Domain expansion A01–A06, затем methodologically
reviewed remaining source and calculated outputs по coverage matrix.

**Блокирующее условие:** прежде чем запускать performance claims,
должны быть одинаковые numerics, versioned inputs, exact source evidence
и независимые golden examples. Rust ≠ автоматическая финансовая валидация.
**Главный acceptance:** для одного exact qualified CalcPlan из одного
исходного FactSet получить одинаковые допустимые результаты и состояния
на Python reference / Rust / Java-SQL где применимо,
доказать lineage и измерить full microservice roundtrip.

---

## 18. FEngine HC-CATALOG-R0 — реестр показателей, требующих глубоких вычислений (требования, без реализации)

**Дата:** 2026-11-20. **Статус:** REQUIREMENTS_COLLECTION / CANDIDATE_UNQUALIFIED.
**Область:** FEngine как универсальное финансово-экономическое ядро; связь с FIN Analyzer по точным form/model codes, только как кандидатные upstream references.
**FIN source snapshot:** alimbetov/fin-analyzer, ветка feat/fin-form-library-standalone, HEAD 5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b. Ссылки на изначальные 166 форм, 42 описательные модели, 46 кодов analytic outputs и 23 operator families — справочные, не свидетельствуют об их фактическом исполнении или финансовом S2.
**Область запрета:** НЕ создавать Python/Rust файлы, микросервисы, таблицы и миграции. Это только формализация будущих расчетов в ранее согласованном едином файле.

### 18.1. Что означает «глубокое вычисление»

Глубоким считать **не любое арифметическое отношение**, а показатель, для которого есть как минимум один:
- E: последовательная реконструкция на основе финансовых событий, частичных оплат, поправок, исторических версий и удержаний, где порядок событий влияет на результат.
- T: межформенная/многопериодная сверка, временные интервалы, stocks vs flows, валютная трансляция, средние остатки и дополнительные слои reconciliation.
- N: нелинейная численная процедура (EIR, IRR, XIRR, DCF roots, value-in-use), требующая устойчивого solver, проверки числа корней и допустимых ошибок.
- O: оптимизация, ограниченные ресурсы, расписания или поиск допустимого решения.
- M: многосценарная, стохастическая, когортная, матричная или вероятностная модель с зафиксированными источниками допущений.

**Не путать финансовую/логическую сложность и CPU-нагрузку.** E и T зачастую выгоднее делать в PostgreSQL с version-pinned SQL/JDBC; N, M и O — кандидаты для ускоренного Rust batch ядра, но решение только после бенчмарков. Простые netRevenue-cogs, обычные ratios и GROUP_BY без специальных зависимостей не являются самостоятельным оправданием Rust микросервиса.

**Прочтение реестра:** HC.* — новые **предлагаемые коды FEngine**, НЕ существующие имена метрик FIN; «FIN/источник» — только потенциальный источник/связь, не утвержденный source-to-metric binding. Priority P0/P1/P2 — порядок методологического исследования, не состояние разработки, не обещание S2.

### 18.2. Полный кандидатный реестр

В таблицах: Тип E/T/N/O/M по определениям выше; P0 — первая волна Python-reference требований, P1 — следующая волна, P2 — дальнейшее исследование. Названия и варианты расчетов черновые. Для каждого output обязательна отдельная проверка source, method, period, dimensions, value-state, financial example и golden tests до реализации.


#### Обязательства, оплаты и просрочка — 7 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.SET.01 | Остаток дебиторского обязательства из событий | event replay; allocation; effective-date | C01;C11;DF-CSH-02/04;A01 | E | P0 |
| HC.SET.02 | Остаток кредиторского обязательства из событий | event replay; allocation; corrections | C02;C11;DF-CSH-02/05;A01 | E | P0 |
| HC.SET.03 | Aging bucket и сумма просрочки по обязательству | asOf matching; payment waterfall; buckets | C01;C02;DF-CSH;A01 | E | P0 |
| HC.SET.04 | Взвешенный срок просрочки портфеля | event-weighted cohort; business key; date | C01;C02;A01 | T | P1 |
| HC.SET.05 | Сверенная чистая позиция по контрагенту | legal set-off qualification; net/gross bridge | C01;C02;C11 | T | P1 |
| HC.SET.06 | Остаток после частичных оплат и сторно | replay-safe settlement matching | A01;DF-CSH-02/04/05 | E | P0 |
| HC.SET.07 | DSO/DPO по верифицированным потокам | cohort joins; avg stock; credit sales/purchases | C01;C02;P06;C07 | T | P1 |

#### Кредитный риск и резервы — 7 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.ECL.01 | Резерв ECL по допустимой матрице просрочки | cohort; forward-looking scenarios | C01;A02;DF-CSH-04 | M | P1 |
| HC.ECL.02 | 12-month ECL портфеля | PD term; EAD; LGD; discounting | C01;C05;A02 | M | P1 |
| HC.ECL.03 | Lifetime ECL портфеля | multi-period hazard; discounted loss paths | C01;C05;A02 | M | P1 |
| HC.ECL.04 | Срочная структура PD | survival/hazard curves; calibration | A02;SF-K01 | N | P2 |
| HC.ECL.05 | LGD по сценариям взыскания | recoveries; costs; discounted paths | A02;C05;SF-K01 | M | P2 |
| HC.ECL.06 | EAD с будущими выборками и выплатами | contract cash schedule; credit exposure path | A02;C05;A05 | T | P2 |
| HC.ECL.07 | Миграция стадий риска и резервов | transition matrix; roll-forward; attribution | A02;C01;F01 | M | P2 |

#### Кредиты, EIR и графики — 8 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.LOAN.01 | График договорных процентов | day-count; rates history; dated accruals | C05;P04;A05 | E | P0 |
| HC.LOAN.02 | График погашения основного долга | annuity/equal principal/custom; cash waterfall | C05;P04;A05 | E | P0 |
| HC.LOAN.03 | Эффективная ставка IFRS EIR | discounted root; fee classification | C05;F01/F02;A05 | N | P0 |
| HC.LOAN.04 | Амортизированная стоимость долга | EIR interest; dated principal; remeasurement | C05;F01;A05 | E | P1 |
| HC.LOAN.05 | Результат модификации/пересмотра долга | cashflow revision; discounted modification | C05;F01/F02;A05 | N | P1 |
| HC.LOAN.06 | Эффект досрочного погашения | rescheduled cashflows; fees; interest difference | C05;P04;A05;A01 | E | P1 |
| HC.LOAN.07 | Договорный DSCR и covenant assessment | CFADS from contract; schedule; thresholds | P09;P04;C05;A05 | T | P1 |
| HC.LOAN.08 | ГЭСВ РК по применимой редакции правил | jurisdiction/date-dependent cashflow rate root | C05;A05 | N | P2 |

#### Казначейство и денежные потоки — 8 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.CASH.01 | Прогноз ликвидности на 13 недель | time-phased receipts/payments; scenarios | DF-CSH-01/02/03;P03;CFO-02 | T | P0 |
| HC.CASH.02 | Разрывы ликвидности по временным корзинам | bucketed obligations; matched cash sources | P03;P10;C01/C02 | T | P1 |
| HC.CASH.03 | Cash runway по динамическим сценариям | cash path; threshold/first-passage | P03;P08 | M | P1 |
| HC.CASH.04 | CFO прямым методом | cash classification; reconciliation | F03;C06;C07;A01 | T | P0 |
| HC.CASH.05 | CFO косвенным методом | net profit; noncash and working capital bridges | F02;F03;P06 | T | P0 |
| HC.CASH.06 | Сверка банковских проводок | event matching; value/posting dates; dedup | C06;F03;ACC-03 | E | P1 |
| HC.CASH.07 | Курсовой мост денежных средств | multi-currency FX historical vs closing; noncash | F03;C06 | T | P1 |
| HC.CASH.08 | Потребность во внешнем финансировании | rolling deficits; financing constraints | P10;P03;INV-08 | O | P1 |

#### Инвестиции и оценка — 9 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.DCF.01 | NPV регулярных денежных потоков | discounted series; agreed periodic rate | P07;P03;P05;INV-05 | N | P0 |
| HC.DCF.02 | NPV потоков с фактическими датами | actual-day discount; day-count conventions | P07;A06 | N | P1 |
| HC.DCF.03 | Все допустимые IRR roots и неоднозначность | multi-root discovery; domain restrictions | P07;INV-05;A06 | N | P0 |
| HC.DCF.04 | XIRR по календарным датам | numerical roots; irregular periods | P07;A06 | N | P1 |
| HC.DCF.05 | FCFF по полной экономической схеме | cashflow bridge; CAPEX; working capital | P07;P03;P05;INV-02 | T | P1 |
| HC.DCF.06 | FCFE по полной схеме долга | equity CF bridge; debt flows | P07;P04;INV-03 | T | P1 |
| HC.DCF.07 | Стоимость предприятия DCF и terminal value | FCFF/WACC; TV; discount convention | P07;INV-06;A06 | N | P1 |
| HC.DCF.08 | Стоимость капитала и EV-to-equity bridge | FCFE/Ke; EV-net debt + adjustments | P07;INV-04;A06 | T | P1 |
| HC.DCF.09 | Матрица чувствительности стоимости проекта | vectorized scenario grid; dependency DAG | P08;P07;INV-07 | M | P1 |

#### Учёт и консолидация — 7 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.ACC.01 | Интегрированная модель трёх отчётов | F01/F02/F03; cash/balance reconciliation; graph | F01/F02/F03;P01/P02/P03;CFO-01 | T | P1 |
| HC.ACC.02 | Элиминация внутригрупповых операций | intercompany matching; consolidation rules | F08;C14;ACC-07 | E | P1 |
| HC.ACC.03 | Валютная трансляция консолидации | rate types; CTA; position-level translation | F08;F01/F02;C14 | T | P2 |
| HC.ACC.04 | Межфирменная сверка дебета/кредита | pair matching; entity-level netting; exceptions | F06;C14;C11 | E | P1 |
| HC.ACC.05 | Отложенные налоги и временные разницы | tax basis; reversals; time profiles | F01;F02;F05 | T | P2 |
| HC.ACC.06 | PV и roll-forward обязательства по аренде | dated discounted rentals; modification | C13;C05;ACC-06 | N | P1 |
| HC.ACC.07 | Мост движения капитала и результата | OCI/distributions; roll-forward proof | F04;F01;F02 | T | P2 |

#### Запасы и себестоимость — 7 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.STOCK.01 | Себестоимость FIFO по партиям | ordered lot consumption; returns; corrections | C03;DF-STK-02/03;A03 | E | P0 |
| HC.STOCK.02 | Средневзвешенная стоимость партий | perpetual/periodic moving weighted avg | C03;DF-STK-02/03;A03 | E | P0 |
| HC.STOCK.03 | Себестоимость по идентифицированным единицам | item trace; quantity lineage | C03;DF-STK-01/02/03;A03 | E | P1 |
| HC.STOCK.04 | Уценка запасов до NRV | item-level recoverable NRV; provisions | C03;A03 | T | P1 |
| HC.STOCK.05 | Старение и риск обесценения запасов | stock cohorts; return histories; policy | C03;DF-STK-04;A03 | M | P2 |
| HC.STOCK.06 | Сверка движения и конечного остатка | receipt/consumption/adjustment roll-forward | C03;DF-STK-01/02/03 | T | P1 |
| HC.STOCK.07 | Потребность пополнения с ограничениями | safety stock; demand uncertainty; optimization | DF-STK-05;MGT-03 | O | P2 |

#### Основные средства — 7 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.ASSET.01 | Покомпонентная амортизация | partial periods; changing useful life; policy | C04;DF-AST-01;A04 | E | P1 |
| HC.ASSET.02 | Изменение стоимости и переоценка ОС | events; impairment; reversal; OCI rules | C04;F01;A04 | E | P1 |
| HC.ASSET.03 | Value-in-use и impairment по CGU | discounted forecast; recoverable value | C04;F05;A04 | N | P2 |
| HC.ASSET.04 | Балансовая стоимость на дату среза | component cost-depreciation-impairment roll | C04;A04 | T | P1 |
| HC.ASSET.05 | Результат выбытия ОС | proceeds; disposal costs; carrying amount | C04;DF-AST-03;A04 | T | P2 |
| HC.ASSET.06 | Прогноз ремонтов и жизненного цикла ОС | component wear; time/usage scheduling | C04;P05;DF-AST-01 | M | P2 |
| HC.ASSET.07 | График CAPEX и вводов в эксплуатацию | time-phased commitments; capitalization events | P05;C04;INV-01 | T | P1 |

#### Затраты и строительство — 8 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.COST.01 | ABC распределение косвенных расходов | drivers; multi-stage allocation; residuals | C08;F07;DF-CST-03;CFO-07 | E | P1 |
| HC.COST.02 | Себестоимость единицы по ресурсам | BOM/resources; conversion units; work item | SF-F02;DF-OPS-02;CST-04 | E | P1 |
| HC.COST.03 | Price-volume-mix bridge прибыли | factor decomposition; reconciliation | C07;C08;C09;CFO-04 | T | P1 |
| HC.COST.04 | Точка безубыточности для продуктового микса | contribution margins; optimization constraints | C07;C08;P02 | O | P2 |
| HC.COST.05 | Эскалация стоимости проекта и contingency | time index; risk scenarios | SF-F02;P08;CST-10 | M | P2 |
| HC.COST.06 | BoQ и стоимость строительных работ | quantity takeoff; rate mapping; material-labor | SF-F01/SF-F02;CST-01/04 | E | P1 |
| HC.COST.07 | Освоенный объём EVM (CPI/SPI/EAC) | earned value; time-phased progress forecast | SF-F01/SF-F02;CST-09 | T | P1 |
| HC.COST.08 | План-факт затрат по драйверам | flex budgets; drivers; multi-period bridge | C08;P02;CFO-03 | T | P1 |

#### Планирование и оптимизация — 8 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.PLAN.01 | Скользящий финансовый прогноз | rolling multi-statement scenario DAG | P01/P02/P03;MGT-05 | M | P1 |
| HC.PLAN.02 | Прогноз спроса с сезонностью | time-series; hierarchical cohorts; error intervals | DF-SAL-01;C07;P02 | M | P2 |
| HC.PLAN.03 | Оптимальные страховые запасы | service levels; probabilistic demand/lead time | DF-STK-05;MGT-03 | O | P2 |
| HC.PLAN.04 | Планирование мощностей и загрузки | resource calendars; capacity constraints | DF-OPS-01/02;MGT-02 | O | P2 |
| HC.PLAN.05 | Критический путь проекта и задержки | precedence DAG; scheduling/critical path | DF-PRJ-06;MGT-08 | O | P2 |
| HC.PLAN.06 | План ФОТ и численности | headcount events; temporal payroll policies | DF-HR-01/03;MGT-04 | T | P2 |
| HC.PLAN.07 | Согласованный P&L/BS/CF для сценариев | cross-statement financial propagation | P01/P02/P03;CFO-01 | M | P1 |
| HC.PLAN.08 | Оптимальное распределение CAPEX | portfolio budget constraints; NPV optimization | P05/P07/P08;INV-09 | O | P2 |

#### Риск и стресс-моделирование — 7 кандидатов

| FEngine-код | Показатель-кандидат | Почему сложный / семейство | Связь с FIN (кандидат) | Тип | Очерёдность |
|---|---|---|---|:---:|:---:|
| HC.RISK.01 | Monte Carlo распределение NPV | stochastic inputs; correlated draws; distribution | P07/P08;A06 | M | P2 |
| HC.RISK.02 | Value at Risk денежного результата | loss distribution; quantile estimation | P08;MGT-07 | M | P2 |
| HC.RISK.03 | Conditional Value at Risk (Expected Shortfall) | tail conditional loss; backtesting | P08;MGT-07 | M | P2 |
| HC.RISK.04 | Многопериодный стресс ликвидности | scenario cashflow shock and constraints | P03;P08;CFO-02 | M | P1 |
| HC.RISK.05 | Чувствительность ECL к макрофакторам | forward macro paths; credit loss recalibration | A02;C01;P08 | M | P2 |
| HC.RISK.06 | Вероятность кассового разрыва | stochastic first-passage on cash paths | P03;P08;CFO-02 | M | P2 |
| HC.RISK.07 | Совместный сценарий ставок, FX и CAPEX | correlated shocks; cross-form propagation | P07/P08;C05;A06 | M | P2 |


### 18.3. Сводка и качество покрытия

Реестр кандидатов НЕ равен числу существующих или финансово квалифицированных показателей в FIN. Он нужен для фильтрации и декомпозиции на независимые вычислительные output contracts, а не для создания фиктивного покрытия форм.

Обязательные поля для каждого HC.*:
code; title; analysisGoal; sourceSystem; formVersion(s);
metric/inputRevision(s); input-grain; stableBusinessKey; value-state;
stock/flow/event/valuation-date semantics; expected result-shape;
output unit; currency & FX version; contract/parameter/method revision SHA;
math expression/iterative method; convergence criteria when applicable;
edge cases; independent examples with source evidence;
Python oracle revision; Rust capability candidate; SQL fallback;
privacy/security; numerical policy; publication and approval gate;
performance workload shape; idempotent async taskCode;
staged input SHA; result SHA; archive receipt and 3h temporary retention policy.

Пример ResultShape:
- ROW_ALIGNED: график событий по каждой строке/договору/парте;
- GROUPED: aging/cohorts/group-by;
- TIME_SERIES: 13-week cashflow, debt schedules, rolling forecasts;
- AGGREGATE: DSO/NPV/DSCR с единой единицей и scope;
- ROOT_SET: IRR/XIRR — возможны 0, 1, несколько корней;
- SCENARIO_MATRIX: stress, Monte Carlo, NPV sensitivity;
- OPTIMIZATION_PLAN: альтернативы, ограничения, objective + diagnostics.

Пример BATCH-выполнения: одна taskCode может возвращать несколько зависимых
outputs, но каждая output metric revision и ее typed status должна иметь собственную
semantic ID, lineage и методологический gate. Input data, taskCode, exact method,
numeric policy, resultShape фиксируются в **immutable execution binding**;
одноименный ключ идемпотентности с другой задачей или исходным массивом — conflict,
а не автоматическая повторная калькуляция.

### 18.4. Первые шесть эталонных пакетов Python (только будущие требования)

1. HC.SET.01/02/03/06: invoice+settlement events, due date amendment, reversal,
   duplicate business keys; stateful replay and aging; C01/C02/A01. В FIN
   пока нет универсального полного allocation ledger E2E для этих задач.
2. HC.LOAN.01/02/03: cash schedule, nominal rate, contract dates,
   fees, EIR root; C05/P04/A05. Не смешивать EIR с договорной ставкой и ГЭСВ.
3. HC.CASH.01/04/05: cash roll-forward, direct vs indirect CFO, 13-week
   liquidity, stock/flow reconciliation.
4. HC.STOCK.01/02: transaction-ordered FIFO vs weighted average and returns;
   C03/A03; invariant quantity and cost.
5. HC.DCF.01/03/09: periodic NPV, all IRR roots and sensitivity grid;
   P07/P08/A06, signed dated cashflows and FCFF/WACC vs FCFE/Ke gate.
6. HC.ECL.01/02/03: forward-looking ECL with segment definitions
   and eligibility; independent loss assumptions and financial policy.
   Не выдавать synthetic loss model за IFRS certification.

Для каждого пакета сначала: финансовое определение; независимые числовые
worked examples; Python Decimal (или при статистическом моделировании
явная точность/seed/tolerance); property/negative tests; immutable golden vectors;
лишь затем Rust parity, если модель и задача научно/методологически доказаны.

### 18.5. Как решать, переносить ли показатель в Rust

| Семейство вычислений | Предварительный исполнитель | Условие для Rust |
|---|---|---|
| Многомерные joins, WHERE/GROUP BY, простые SUM/ROLL_FORWARD | PostgreSQL SQL/JDBC | Только при подтверждённой экономии full-path latency |
| Платежные и товарные event waterfalls | SQL temporal + Python reference, затем Rust | Большой поток упорядоченных событий, устойчивый replay, batch throughput |
| EIR/IRR/XIRR/NPV solver, множество датированных графиков | Python Decimal reference, затем Rust compute | Numerical parity, root policy, batches и CPU bottleneck |
| Сценарии, Monte Carlo, чувствительность | Python model, затем Rust | Доказанный workload, reproducible seeds, statistical acceptance |
| Resource/capital optimization | Python OR reference, затем Rust или dedicated solver | Точный objective/constraints и качество результата |
| Простая маржа, процент, изменение за период | Java/SQL | Не выделять Rust лишь из-за названия показателя |

Требование FEngine ASYNC: сначала INPUT(contract + idempotency key + arrays),
затем EXECUTE(taskCode + same scoped key), затем GET status/result by key;
durable Inbox/Outbox, immutable result, acknowledgment при записи в основную
БД, purge временных payload **не ранее 3 часов после завершения и подтвержденной
архивации**. 3h payload TTL не равно периоду сохранения ключа или финансовых
audit receipts. До спецификации архивного подтверждения опасно считать очистку
безусловной.

### 18.6. Методологические блокеры для каталога

- Финансовые ставки: EIR / договорная номинальная / применимая ГЭСВ РК
  разные оси, не interchangeable versions.
- A02/ECL: PD, LGD, EAD и staging/forecast policy не заполняются автоматически.
  Случай allowance > gross в positive-stock pilot требует review, а не writeoff.
- Stock AS_OF: брать ровно одно надлежащее состояние на дату;
  суммирование состояний за несколько дат — ошибка.
- Valuation: FCFF дисконтируется WACC, FCFE — cost of equity при корректной
  методике; не смешивать денежные потоки и ставки.
- IRR: multiple/no root; XIRR and day-count/valuation date pinned.
- Ценообразование и risk: causal interpretation отдельна от correlation;
  forecast/error bounds and baseline must be explainable.
- Unit/currency/period mismatch, missing/zero/null/NA, negative balances,
  precision and rounding always explicit; no silent zero substitution.
- Monte Carlo/ML statistical floats may be appropriate within clearly
  versioned probabilistic kernels; денежные обязательства и бухгалтерские
  суммы — controlled Decimal with exact final money policy.
- 166 forms (154 data + 12 evidence) remain the FIN source catalogue.
  No invented 167th form, no equation for every numeric input,
  no automatic qualification of 42 models, 46 output codes or 10
  candidate formula revisions.
- Financial S2/production admission stays independent from Python/Rust
  code parity and algorithm verification.

### 18.7. Источники и актуальность

FIN Analyzer input sources (исходный snapshot):
https://github.com/alimbetov/fin-analyzer/blob/5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b/form-library/src/main/resources/catalog/analytics-model-catalog.tsv
https://github.com/alimbetov/fin-analyzer/blob/5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b/docs/FIN-CALC154-ALL166-FORMS-NAMES-METHODOLOGY-RESEARCH.tsv
https://github.com/alimbetov/fin-analyzer/blob/5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b/docs/FIN-CALC154-METHODOLOGY-OPERATION-GAPS.tsv
https://github.com/alimbetov/fin-analyzer/blob/5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b/docs/FIN-DATA-CALC-R2-CROSS-FORM-OUTPUT-MATRIX.tsv
https://github.com/alimbetov/fin-analyzer/blob/5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b/docs/FIN-CALC-APPS-R0-SIX-APPLICATION-CONTRACTS-AND-ROADMAP.md
https://github.com/alimbetov/fin-analyzer/blob/5d3be2d6b9856be1571ed6aa99d516e3c8b2af3b/docs/FIN-DATA-CALC-R2-CROSS-FORM-CALCULATION-ROADMAP.md

В новейшей ветке FIN MG-R0.1 read-only Metric Graph Resolver получил ограниченный
PG16 gate 5/5 PASS на тестируемом SHA d39af2e4...; это доказательство
чтения exact formula/physical field dependencies, НЕ 83 исполнимых
высокопроизводительных моделей.

**Итог требований:** сначала изучить типизированные outputs и exact source
evidence для P0, затем P1/P2 по бизнес-приоритету. До отдельного разрешения
разработка, нагрузочные тесты, новые SQL/Python/Rust файлы — STOP.



---

## 19. HPC Wave-2/Wave-3: все 83 показателя и Python-first комплексная спецификация (v0.5)

**Дата:** 2026-11-20. **Статус:** REQUIREMENTS_COLLECTION / METHOD_CANDIDATE / NOT_IMPLEMENTED / FINANCIAL_S2_HOLD.

Утверждённый пользователем рабочий охват FEngine (НЕ финансово утверждённые калькуляторы): один Python Memory Calculation Hub для всех 83 candidate methods, без выделения отдельных независимых сервисов или движков под каждую метрику. Сохранять этот master как canonical индекс и обзор; развёрнутые технические приложения по явному решению пользователя расположены в docs. Никаких исходных кодов, БД-миграций или runtime-сервисов на этапе requirements.

| Волна | Приоритет | Кодов FEngine | Typed Dataset DTO | Связанный подробный документ |
|---|---|---:|---|---|
| W1 | P0 | 14 | D01–D15 (15) | docs/FENGINE-HPC-WAVE1-14-CALCULATION-CONTRACTS-TZ.md v1.1 |
| W2 | P1 | 42 | D16–D54 (39) | docs/FENGINE-HPC-WAVE2-P1-42-METHOD-DTO-RESULT-TZ.md v1.0 |
| W3 | P2 | 27 | D55–D81 (27) | docs/FENGINE-HPC-WAVE3-P2-27-STATISTICAL-METHOD-DTO-TZ.md v1.0 |
| **Итого** | P0/P1/P2 | **83** | **81 types** | один логический InputBatchDTO / CalculationResponseDTO |

Сверка точных кодов по §18: P0 14/14, P1 42/42, P2 27/27; 83 уникальных кандидатных output definitions, без пропусков. Все 81 dataset schema — **проектные транспортные DTO**, не доказанные существующие FIN source tables/fields. Любой недостающий source binding остаётся BLOCKED_SOURCE до отдельной квалификации.

**Канонический путь:** versioned Contract → verified immutable DatasetRevision + SHA → sealed Calculation Session → TaskCode and immutable CalcPlan → Python Decimal Reference Worker → versioned CalculationResultSet arrays → durable PostgreSQL Result/Outbox → archive acknowledgment → eligible temporary purge. Rust alternative через тот же контракт — будущий этап после golden/benchmark.

**Типы ResultShape для полного охвата:** ROW_ALIGNED, GROUPED, TIME_SERIES, EVENT_SERIES, AGGREGATE, ROOT_SET, SCENARIO_MATRIX, DISTRIBUTION, OPTIMIZATION_PLAN. Последние три не должны появляться «втихую»: требуют отдельной версионируемой совместимой редакции OutputSchemaRevision.

**Логические типы, не закрытые Word DTO:** MONEY_PER_UNIT = MONEY / physical QUANTITY unit with exact currency, numerator and denominator; MATRIX/VECTOR/POINT_SERIES = LIST<typed values> with declared shape/dimensions and deterministic ordering; distribution sample weights must be RATE with correct normalization. Numeric policy Decimal money, statistical precision/PRNG and optimizer tolerances are different policy families. Universal auto-conversion without evidence prohibited.

**Состояния исследования:** REGISTERED → TYPED_METHOD_DRAFT → FINANCIAL_SOURCE_REVIEW → INDEPENDENT_MATH_GOLDEN_REVIEW → future PYTHON_PARITY → future RUST_PARITY → FINANCIAL_S2 (if applicable) → PRODUCTION_ADMISSION. На 2026-11-20 полнота спецификаций равна 83 кодам; математическая, нормативная и функциональная готовность **не доказана**.

**Нормативный источник KZ_GESV:** постановление Правления АРРФР от 3 апреля 2026 №44, зарегистрировано №38333: https://zakon.uchet.kz/rus/docs/V2600038333. Вступление в силу, дата договора, тип организации и историческая редакция закона должны быть проверены для каждого отдельного расчёта. KZ_GESV ≠ IFRS EIR.

**Приоритет дальнейшего design:** формализовать финансовую applicability, actual FIN source-to-field binding и независимые golden cases для P0, затем P1/P2; Python/Rust implementation остаётся STOP до отдельного явного распоряжения.
