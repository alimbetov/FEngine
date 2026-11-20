# FEngine — единая спецификация финансово-экономического аналитического ядра

Версия документа: 0.7 (83 model contracts + OPT-R0 universal planning + GEO-OPT-R0 weighted spatial graphs)
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

---

## 19. FEngine OPT-R0 — Universal Mathematical Modeling, Resource Planning & Optimization

**Дата решения:** 2026-11-20. **Статус:** APPROVED_CONCEPT / DESIGN_ONLY / NOT_IMPLEMENTED / NOT_BENCHMARKED / NOT_PRODUCTION_ADMITTED.
**Цель:** сделать FEngine универсальной, отраслево расширяемой системой математического моделирования, планирования ресурсов и обоснования управленческих решений. «На все случаи жизни» означает единый расширяемый формализм и реестр solver capabilities, а НЕ обещание, что один алгоритм подходит всем задачам или что все перечисленные модели уже работают.

**Ограничение текущего этапа:** канонический обзор расширения фиксируется в FENGINE_MASTER_SPEC.md; детальные приложения в docs допускаются только по отдельному прямому решению пользователя. Никаких новых исходников, Python/Rust сервисов, миграций, внешних зависимостей и фактических solver-тестов без отдельного разрешения. Прежде чем реализовывать, необходимо закрыть модельные контракты и независимые worked examples. Этот раздел не меняет автоматически статус 83 показателей, 166 форм FIN, 42 аналитических моделей и существующих кандидатных HC.*.

### 19.1. Функциональная граница и бизнес-ценность

FEngine отвечает на три разных вопроса:
1. **Descriptive:** что произошло? Надёжные факты, показатели, формулы, анализ.
2. **Predictive:** что может произойти? Прогнозы, сценарии, распределения, интервалы неопределённости.
3. **Prescriptive:** что делать? Решения (decision variables), допустимые ограничения и математически оптимальные/приближённые варианты.

Виды сущностей не смешиваются: FACT ≠ ASSUMPTION ≠ DECISION ≠ SOLVER_RESULT ≠ BUSINESS_APPROVAL. Результат оптимизатора является предложением плана, но не новой финансовой проводкой/фактом и не автоматически утверждённой стратегией. Финансовые показатели из Metric Graph могут задавать коэффициенты, цели или ограничения; обратная связь план → прогноз формирует отдельный scenario output, а не меняет исходный FactSet.

Основные отраслевые шаблоны: производство/BOM, мощность оборудования, персонал и смены, закупки/запасы, транспорт/склады/маршруты, бюджет и cashflow, CAPEX-портфель, энергетика и накопители, стройка/проектная сетка, торговый ассортимент и цены, банковский капитал/ликвидность, агро/земля/вода, healthcare/сервисные расписания, госбюджет/социальная инфраструктура. Шаблон — набор типизированных параметров и правил, не отдельный движок. Разрешено подключать новые отрасли без изменения core DSL.

### 19.2. Универсальная модель OPT

Канонический OptimizationModelRevision включает:
- modelCode, modelRevision, schemaRevision, modelClass, domainTags, descriptive purpose, ownerScope, tenantRef, applicable profiles, approval status, effective dates, immutable modelSha256;
- decisionVariables[]: code, domain (CONTINUOUS/INTEGER/BINARY/SEMICONTINUOUS при поддержке solver), indexed dimensions, bounds, unit/currency, time basis, integrality and optional initial guess;
- parameters[]: typed sources (FactSet revision/Metric revision/assumption revision), values, units, scenario overrides, provenance, missing/null/NA semantics;
- objectiveTerms[]: MIN/MAX, scalar expression, multiple weighted/lexicographic/Pareto objectives with fully pinned priority and weights; optimisationDirection;
- constraints[]: linear rows, equalities, upper/lower bounds, indicator constraints, piecewise constraints, network/precedence/cumulative constraints only for declared solver capability; hard/soft, penalty, name, business explanation and numeric tolerance policy;
- coefficientTensor: dense or sparse COO/CSR, dimension names/keys (product/site/period/etc.), row/column alignment, declared precision, canonical coordinate ordering, immutable tensor content SHA;
- timeHorizon: periodStart/periodEnd, calendar/timezone and bucket policy, initial conditions, terminal policy; event-time vs period-time not interchangeable;
- uncertaintyModel: deterministic/scenario-tree/distribution/uncertainty sets, scenario probabilities, correlation and seed provenance, nonanticipativity by information stage;
- solverPolicyRevision: algorithm class, candidate backends, required capabilities, time/memory/node budgets, mipGap/optimality/feasibility tolerances, deterministic settings, parallelism and stop conditions;
- outputContractRevision: required result shape, decision rows, resource utilization, objective values, feasibility diagnostics, scenario comparison and reporting units;
- compilation references: dependency graph / model AST version / source SHA / scenario SHA / numeric policy SHA / solver artifact and library versions.

**Нет произвольного eval/exec, SQL или пользовательских Python-скриптов внутри модели.** Только безопасный, типизированный DSL/AST с валидацией и белым списком операторов. Символьные expression/constraint AST независимы от Python, Rust и конкретного solver. Сложные nonlinear/custom models не считаются допустимыми, пока их конкретная capability не реализована и не прошла gate.

Типовые условные семейства выражений: CONST, REF, ADD, SUB, MUL_CONSTANT, SUM, DOT, MATMUL, MIN/MAX_REFORMULATION при проверенной линейной редукции, ABS_LINEARIZATION, IF/THEN только для поддерживаемых indicator constraints, TIME_SHIFT, BALANCE, INDEX_FILTER, GROUP_SUM. Нелинейное произведение двух decision variables запрещено в LP и требует QP/NLP capability. Величины без совместимых единиц, валют, периода и scope отклоняются компилятором; FX/единицы требуют версионированную операцию приведения.

### 19.3. Классы математических задач, а не отдельные сервисы

| Family | Solver semantics / пример | Первый статус |
|---|---|---|
| LA | матрицы, разложение, системы линейных уравнений и балансы | CANDIDATE |
| LP | simplex/dual simplex/interior point, оптимальный ресурсный план | PILOT_TARGET |
| MILP | бинарный выбор, партии, смены, проектный портфель | CANDIDATE |
| QP/MIQP | квадратичные затраты/риски с проверенной выпуклостью | RESEARCH |
| NLP/MINLP | нелинейные функции, локальные/глобальные решения с явными гарантиями | RESEARCH |
| NETWORK | min-cost flow, assignment, matching, многоскладские перевозки | CANDIDATE |
| CP/SCHEDULE | технологические зависимости, календари, расписания и мощности | CANDIDATE |
| DYNAMIC | multi-period balances, rolling horizon, stock/flow propagation | PILOT_TARGET |
| STOCHASTIC | scenario tree, expected value, chance constraints, CVaR | RESEARCH |
| ROBUST | worst-case planning, uncertainty sets, bounds | RESEARCH |
| SIMULATION | Monte Carlo/discrete events/queue simulation для оценки политик | RESEARCH |
| MULTIOBJECTIVE | weighted/lexicographic, Pareto frontier and trade-offs | CANDIDATE |
| INPUT_OUTPUT | межотраслевой баланс, матрица Леонтьева (I-A)x=d, устойчивость и проверка невырожденности | CANDIDATE |
| HEURISTIC | маршрутизация/большие сложные задачи, явный gap/unknown guarantee | RESEARCH |

Каждый solver plugin публикует версионированный CapabilityDescriptor: supported variable types, expressions, constraint classes, objective modes, batch sizes, max dimensions, feasible/optimality guarantees, license/deployment, precision and output diagnostics. Preflight отклоняет неподдерживаемую модель с UNSUPPORTED_CAPABILITY; **никаких тихих замен MILP → LP или nonlinear → linear**, и «решение найдено» не эквивалентно «оптимальность доказана».

Рекомендуемый будущий стек: Python reference — NumPy/SciPy/HiGHS для LA/LP/MILP, OR-Tools для некоторых routing/CP-SAT/assignment (раздельные адаптеры); алгоритмы и API закрепляются по версиям. Rust — только для подтверждённо выгодных numerical kernels, не обязательный rewrite независимого solver. Сложные mixed-integer solver могут оставаться специализированной библиотекой под единым Python Calculation Hub. Окончательный выбор зависит от capability review, лицензий и E2E benchmarking. Пока никакая зависимость не установлена.

### 19.4. Связь с существующим Calculation Hub, Metric Graph и FIN

Использовать один существующий control/data protocol из разделов 17–18 и документа FENGINE-PY-R0:
- InputContractDTO / DatasetManifestDTO / immutable SessionRevision → typed coefficient/constraint/parameter datasets;
- CalculationPlanDTO → точные methodRevisionRef, paramsRevisionRef, solverPolicyRevision, dataset and model SHA, artifact SHA, taskCode, result shape, admission class;
- CalculationResponseDTO остаётся тем же root: results[] → CalculationResultSetDTO.rows[] → CalculatedRowDTO.values[]. Новые **типизированные result shapes** включают DECISION_VECTOR, RESOURCE_SLACKS, OBJECTIVE_BREAKDOWN, OPTIMIZATION_DIAGNOSTICS, SENSITIVITY_MATRIX, SCENARIO_COMPARISON, TIME_SERIES_PLAN; исключения и статусы — отдельные документированные поля существующих status/value-state contracts либо следующей их версией, но не второй response envelope.
- ScenarioRevision ссылается на неизменяемую base Session и только permitted overrides. Изменение любого оптимизируемого параметра означает новый execution binding и новый job/idempotency identity; base dataset chunks могут повторно использоваться по SHA.
- Result lineage связывает solution rows → variable/constraint/source metric revisions, scenario, solver policy, actual solver+library+build artifact, logs and validation certificate.
- FIN fin_intake/fin_fact остаются в своём trusted bounded context. FEngine не пишет туда напрямую. Экспорт финального плана/прогноза — отдельный reviewed adapter/approval workflow. Производственный уровень допуска требует отдельного финансового S2, где применимо.

OptimizationPlan не обязан быть частью финансового DAG на уровне внутренних переменных: **один оптимизационный solver-узел** является атомарным исполняемым узлом DAG, а зависимость между периодами и переменными решается внутри его формальной модели. Это предотвращает ошибочное представление круговых ограничений как недопустимых циклов Metric Graph.

### 19.5. Кандидатные taskCode и reuse существующих HC.*

| taskCode | Семейство | Результат | Связь |
|---|---|---|---|
| OPT.MATRIX.BALANCE.V1 | LA / input-output | MATRIX_RESULT | ECO-03, HC.COST.02 |
| OPT.LP.RESOURCE.V1 | LP | OPTIMIZATION_PLAN | HC.PLAN.04, HC.COST.04 |
| OPT.LP.TRANSPORT.V1 | NETWORK/LP | OPTIMIZATION_PLAN | ECO-09 |
| OPT.MILP.CAPACITY.V1 | MILP | OPTIMIZATION_PLAN | HC.PLAN.04 |
| OPT.MILP.SHIFT.V1 | MILP/CP | SCHEDULE_PLAN | HC.PLAN.06 |
| OPT.MILP.CAPEX.V1 | MILP | PROJECT_PORTFOLIO | HC.PLAN.08 |
| OPT.DYNAMIC.INVENTORY.V1 | DYNAMIC | TIME_SERIES_PLAN | HC.PLAN.03 |
| OPT.DYNAMIC.CASH.V1 | DYNAMIC/LP | CASH_PLAN | HC.PLAN.01/07 |
| OPT.SCENARIO.SENSITIVITY.V1 | SCENARIO | SENSITIVITY_MATRIX | HC.DCF.09 |
| OPT.STOCHASTIC.PORTFOLIO.V1 | STOCHASTIC | SCENARIO_COMPARISON | HC.RISK.01/03 |
| OPT.NETWORK.ROUTE.V1 | NETWORK/HEURISTIC | ROUTE_PLAN | ECO-09 |
| OPT.CP.PROJECT.V1 | CP/SCHEDULE | SCHEDULE_PLAN | HC.PLAN.05 |

Это **кандидатные taskCode**, не заявленные реализации, не новая серия финансовых форм и не дубликаты HC.PLAN.01–08. Одна математическая модель может применяться несколькими отраслевыми taskCode при одинаковом exact typed contract; каждый taskCode должен иметь методику, golden fixture, capability preflight и допустимый result shape. До qualification все — DESIGN_ONLY.

### 19.6. Базовая формальная постановка

Для детерминированной LP:
  maximize/minimize c^T x + c0;
  subject to L <= A x <= U; l <= x <= u.
Скалярная цель, типы x, единицы c и A, размерности [m×n], порядок индексов, совместимость валют и политика округления фиксируются. Нельзя приводить MONEY/DECIMAL к float64 как бухгалтерскую истину: для численного solver допустимо контролируемое scaling → numerical solve → high-precision residual/postsolve verification against original decimal inputs. При выходе за допуски — NUMERICAL_INVALID, не тихий SUCCESS. Не обещать битовой идентичности решений разных версий и алгоритмов при равных оптимумах; поддерживать canonical tie-breaker только когда явно задан.

Многопериодные инварианты:
  inventory[t] = inventory[t-1] + arrivals[t] + production[t] - demand[t] - scrap[t];
  cash[t] = cash[t-1] + inflows[t] - outflows[t];
  capacityUse[resource,t] <= capacityAvailable[resource,t].
Учитывать lead time, перенос остатков, дискретность закупок, отсутствие будущей информации при решениях прошлого периода (nonanticipativity), праздники/календари, границы горизонта, единицы измерения и отрицательные запасы только если явно разрешены моделью.

Для multiobjective: лексикографический приоритет, target constraints или нормированные веса; выбор и нормировка зафиксированы в modelRevision. Для сценариев: baseline, optimist/pessimist/stress — пользовательские метки, а не факты; сравнение требует одинаковой финансовой и временной базы. Для stochastic: нормированные вероятности, источник распределения/корреляций, seed, confidence interval и ограничения информации по стадиям.

### 19.7. Результаты и объяснимость

Минимальный OptimizationResultDTO (логическая схема внутри CalculationResponseDTO):
- executionId, taskCode, modelRevisionRef, scenarioRevisionRef, resultSchemaRevision, immutableResultSha, exact input lineage;
- solverStatus: OPTIMAL / FEASIBLE_NOT_PROVEN / INFEASIBLE / UNBOUNDED / TIME_LIMIT_NO_FEASIBLE / NUMERICAL_INVALID / UNSUPPORTED_CAPABILITY / CANCELLED / SYSTEM_ERROR;
- certifiedObjectiveValue (если валиден), objectiveBound (если solver вернул), abs/relative optimality gap, feasibility tolerance and max constraint residual, runtime, solver library/build/version/options, deterministic seed when used;
- variableValues[]: variableCode + full dimension keys + value/unit; constraintDiagnostics[]: constraintCode, LHS, bound, slack/violation/unit, binding state;
- dualValues/reducedCosts **только для поддерживаемой непрерывной LP и valid solver basis**, не для произвольного MILP/CP; basis/sensitivity ranges только при доказанной solver support;
- warnings, limitation/assumption refs, expected vs actual guarantees, reproducibility receipt;
- decision alternatives, scenario comparisons and mathematical sensitivity with explicit uncertainty.
Ни INFEASIBLE, ни UNBOUNDED не должны давать fabricated zero plan. Время исполнения и наличие feasible solution не гарантируют proof of global optimum.

### 19.8. Форматы данных, безопасность и экономика исполнения

Tensor input хранит dimension IDs, stable sort order, unit, exact source revision и content hash; поддерживает sparse storage для больших моделей. Наличие отсутствующих coefficients запрещено интерпретировать как 0 без явной sparse-zero policy. Validation: shape, unique axis keys, finite numerical range, dimension-conformity, empty sets, over/under-determined constraints, duplicates, bound contradictions, negative prices/quantities where forbidden, and independent feasibility checks.

Runtime constraints per tenant and request: max model vars/constraints/nonzero entries/bytes, solver CPU seconds and wall timeout, memory cap, parallel solve quota, session permissions, cancellation, bounded logs and safe cleanup. Solver plugin executes without arbitrary network/filesystem/system calls from user expressions, with restricted inputs and reviewed artifact versions. Admission logic fail-closed; idempotent replay binds exact model+scenario+solverPolicy+dataset hashes; stale result forbidden. Independent recheck of all hard constraints after solver, no overwrite of immutable result.

Caching: reuse compiled model only when structure+axis schema+solver version+numeric policy match; reuse numerical solution only when **all** coefficient data/objectives/bounds/scenario/permissions and solver policy hashes match. Warm-start is advisory, never proof of correctness. One Calculation Session may run multiple what-if jobs; each run gets a distinct key when its binding differs.

### 19.9. Planning Studio (future UI)

Excel-like model grid with typed dimensions, copy/paste/CSV import, pivot and sparse-matrix preview; custom variables/objectives/constraints with validation hints; resource capacity bars, time-series charts, Gantt-like schedule, bottleneck map, dual-price table where supported. Editable DRAFT scenario → server-side validation → sealed immutable revision → async solve → readonly result + downloadable proof/lineage + scenario comparison. Scenario editor never rewrites FactSet. Show OPTIMAL vs FEASIBLE_NOT_PROVEN prominently; surface INFEASIBLE with constraint conflict hints and model assumptions. Visual parameters cannot bypass schema/unit/S2/security gates.

### 19.10. Независимые контрольные примеры (обязательные перед кодом)

| ID | Постановка / эталон | Проверки |
|---|---|---|
| OPT-G01 | max 40a+50b, a+2b<=100, 3a+b<=120, a,b>=0. Эталон: a=28, b=36, Z=2920 | Ax<=b, exact objective, LP optimality |
| OPT-G02 | dual G01: resource shadow prices 22/hour and 6/kg, dual objective 22*100+6*120=2920 | strong duality, dual feasibility/complementary slackness |
| OPT-G03 | MILP max 3x+4y, 2x+3y<=7, integer x,y>=0. Эталон x=2,y=1,Z=10; continuous optimum 10.5 | integrality, LP relaxation not substituted |
| OPT-G04 | x>=10 and x<=5 | INFEASIBLE, no fictitious solution |
| OPT-G05 | max x, x>=0, without finite upper bound | UNBOUNDED |
| OPT-G06 | inventory0=10, period1 production0/demand7→inventory1=3, period2 production9/demand11→inventory2=1 | time balance and boundary conditions |
| OPT-G07 | model money in KZT, consumption in kg, foreign USD input without pinned FX | reject dimensional/currency mismatch |
| OPT-G08 | same idempotency key with changed RHS of a constraint | conflict, not cached success |
| OPT-G09 | same objective with two equal optima | valid objective and feasibility; no forced identical basis without tie-breaker |
| OPT-G10 | timeout with valid incumbent but unclosed gap | FEASIBLE_NOT_PROVEN, bound/gap if available |
| OPT-G11 | scenario branch with decision depending on future unknown demand | reject nonanticipativity violation |
| OPT-G12 | solver returns violating rounded decision or NaN | NUMERICAL_INVALID/no admission |
| OPT-G13 | different tenants, same mathematical data/model | no cross-tenant reads or cache authorization bypass |
| OPT-G14 | unsupported nonlinear multiplication in LP | UNSUPPORTED_CAPABILITY at preflight |
| OPT-G15 | model changes while another execution is in flight | immutable old result, new revision/job, no stale commit |
| OPT-G16 | solver crash/worker lease expired/replay | at-least-once execution, one fenced committed outcome and archived receipt |

Test strategy: golden independent analytical solutions; property/metamorphic (row permutations, scaling with checked units, extra redundant constraints, increased nonbinding capacity cannot worsen valid maximization); LP primal/dual residuals, MILP integrality and gap; solver-version pinned regression; PostgreSQL crash/idempotency/tenant checks when implementation is authorized. Actual PASS status is NOT CLAIMED.

### 19.11. Delivery roadmap with explicit qualification gates

| Stage | Artifact | Gate |
|---|---|---|
| OPT-R0.0 | этот дизайн, coverage taxonomy, ownership boundaries | architecture review |
| OPT-R0.1 | typed OptimizationModel DSL/AST and solver CapabilityDescriptor, exact SHA canonicalization, DTO shapes | schema/negative tests |
| OPT-R0.2 | independent goldens G01–G16; Python reference LA + LP resource problem | math proof + numerical residual acceptance |
| OPT-R0.3 | MILP, min-cost flow, infeasible/unbounded explanations | integer/capability correctness |
| OPT-R0.4 | multi-period balances and scenario revision binding | temporal/information-set correctness |
| OPT-R0.5 | Planning Studio editable draft/immutable execution, diagrams, scenario comparison | end-to-end browser qualification |
| OPT-R0.6 | industry templates: manufacturing, logistics, CAPEX, personnel, energy | each scenario independently qualified |
| OPT-R1+ | specialized CP, QP, nonlinear, stochastic/robust, simulation where justified | capability-specific reviews, performance and mathematical validity |

**Первый E2E vertical slice после отдельного разрешения:** fact-backed source inputs → typed A,b,c model → immutable scenario → LP solve → numerical verification → single OPTIMIZATION_PLAN ResultSet → reliable archival/ACK and UI scenario comparison. No new central optimizer service; reuse Calculation Hub jobs, session, leases/fencing, admission and results. No unconditional Rust conversion.

### 19.12. Design decisions / открытые ADR

- OPT-ADR-01: exact serialization/canonicalization for sparse tensor, unit and dimension IDs.
- OPT-ADR-02: separate mathematical model immutability vs scenario overrides and rights.
- OPT-ADR-03: LP postsolve high-precision check and signed financial/solver numeric policy.
- OPT-ADR-04: licensed/OSS solver matrix and deterministic acceptable outcome guarantees.
- OPT-ADR-05: design of time-indexed graph and scenario-tree information sets.
- OPT-ADR-06: solver logs, sensitivity limits, infeasibility explanation and what may be audited.
- OPT-ADR-07: production approval of a plan vs execution of an optimization vs writeback to FIN.
- OPT-ADR-08: maximum instance sizes, synchronous previews vs async jobs and SLO benchmarks.
- OPT-ADR-09: how to integrate OPT outputs into dashboards/financial reports without creating fake financial facts.

**Release boundary:** DESIGN_ONLY. «Все случаи» достигаются расширяемыми моделями, capabilities и отраслевыми templates, а не универсальным непроверяемым algorithm switch. Начинаем с одной доказанной LP вертикали и расширяем по отдельным квалификационным gate.

---

## 20. FEngine GEO-OPT-R0 — Universal Weighted Spatial Graph Engine

**Решение:** расширить FEngine OPT пространственными взвешенными графами; единый пространственный слой служит маршрутизации, иерархической оптимизации, потокам, размещению ресурсов, территориальному покрытию и проектированию сетей.
**Дата:** 2026-11-20.
**Статус:** APPROVED_CONCEPT / DESIGN_ONLY / NOT_IMPLEMENTED / NOT_TESTED / NOT_PRODUCTION_ADMITTED.
**Связь:** OPT-R0 (§19), Metric Graph / CalcPlan / Calculation Session (§§4,7,17–19), существующие HC.PLAN.01–08 (§18); GEO-OPT не создаёт второй calculation engine, второй финансовый FactSet или новую FIN-форму.
**Scope:** сейчас дополнение к единому FENGINE_MASTER_SPEC.md. Договор на будущий исходный код, SQL/PostGIS-миграции, UI и рабочий solver требует отдельного согласования и приёмки.

### 20.1. Концептуальная модель: hierarchy != routing != flow

Вход: центральная точка ROOT и иерархические дочерние/внучатые узлы; ветви могут иметь 20–60 уровней (не путать с 20–60 узлами на одном уровне). Модели должны одинаково корректно описывать географическую сеть дорог и абстрактную инфраструктуру (электрические, кабельные, трубопроводные, логистические и внутренние инженерные сети).

Обязательное логическое разделение:
1. **HierarchyGraph:** parent-child, depth, subtree, branch ownership. Для строгого дерева один parent на узел и отсутствие циклов; опциональная DAG-hierarchy допускается только с явным контрактом множественных родителей и дедупликацией при агрегации.
2. **RoutingGraph:** разрешённые directed/undirected переходы между узлами; независимые межветвевые и обходные связи; географическая близость не создаёт физический переход автоматически.
3. **FlowNetwork:** ёмкости, баланс потоков, supply/demand и потери на рёбрах/узлах; маршрут движения и структура потоков необязательно совпадают.
4. **SpatialGeometry:** координаты точек, геометрия полилиний, полигоны/зоны и CRS; граф является топологией, геометрия не определяет право прохода.
5. **TemporalScenario:** immutable snapshot графа + применимые в конкретный момент веса/ограничения/доступность, без мутации historical revision.

Иерархические рёбра сами по себе НЕ ROUTABLE. Три альтернативы из чистого дерева по единственному пути невозможны; добавлять фиктивные маршруты запрещено. K=3 означает **до трёх реально существующих допустимых путей**.

### 20.2. Версионируемый доменный контракт

| Entity / DTO | Обязательная семантика |
|---|---|
| GeoGraphDefinition / GeoGraphRevision | tenant/scope, graphId, graphKind, graphRevision, schemaVersion, CRS policy, topologySha256, applicable dates, source provenance, state, immutable revision |
| GeoNode / GeoNodeRevision | stable nodeId, nodeType, coordinates (optional for abstract graph), geofenceRef, altitude/level if applicable, status, attributes with typed units, source revision |
| GeoHierarchyRelation | relationId, parentId, childId, relationKind, active version, optional branchId, depth semantics; no implicit routing edge |
| GeoEdge / GeoEdgeRevision | edgeId, fromId, toId, direction, edgeType, optional line geometry, network datasource, transition policy, capacity and closure state |
| GeoZone / GeoZoneRevision | polygon/multipolygon, CRS, access/coverage restrictions, effective window, allowed node/vehicle types |
| GeoWeightDefinition / GeoWeightProfileRevision | weightCode, subject NODE/EDGE/BRANCH/ZONE, semanticKind, unit, valueType, orderDirection, aggregationPolicy, timeSemantics, currency/basis, source and policy revision |
| GeoWeightValue / GeoWeightValueRevision | subjectId, weightDefinitionRef, typed value/valueState, unit, currency, validFrom/validTo, source dataset/metric/assumption reference, exact content hash |
| GeoRouteScenarioRevision | immutable graphRevision, source/targets/waypoints, time and horizon, transport/policy mode, allowed/blocked types, weight overrides and applied source SHA, solver policy |
| GeoRouteRequest / GeoRouteResult | taskCode, k, objectives/constraints, selection/distinctness policies, ordered reachable paths, results+diagnostics+lineage via common CalculationResponseDTO |
| GeoBranchAggregateRevision | aggregation of specifically declared additive or non-additive weights over descendant set, dedup policy, aggregate SHA, source versions |
| GeoNetworkOptimizationPlan | versioned location/flow/coverage/network design model for existing FEngine OPT model DSL, not an independent optimizer |

Stable IDs must be separate from coordinates, display labels, order in UI, and parent path. Deleting a node produces new graphRevision; old sealed revisions remain reproducible. Topology and source geometry may change independently but are resolved together into one exact execution binding.

**Coordinates:** for geographic input use WGS84 geographic SRID 4326, with explicit latitude [-90,90] / longitude [-180,180], precision, axis order and date/CRS provenance. Geodesic distance is not equal to planar length in degrees. Meter-based operations require geography geodesic model or an appropriate explicitly selected projection. Indoor/engineering local XYZ, floor/altitude, vertical datum, 3D and mixed CRS require explicit transform or UNSUPPORTED_CRS; no silent assumptions. Coordinates may be absent for valid logical graph nodes, but map routing requires a geometric data source. Edge's straight line is only visualization; it does not establish road/drone/pipe/cable feasibility. Road routes additionally require a verified road-network source and applicable permissions/vehicle policy.

### 20.3. Weight semantics — не один числовой score

Три базовые области: NODE_WEIGHT, EDGE_WEIGHT, BRANCH_AGGREGATE; дополнительно ZONE_WEIGHT and SCENARIO_WEIGHT_POLICY. Вес может быть положительной стоимостью, полезностью, ограничением, ёмкостью, demand, вектором риска, вероятностью, порядковым приоритетом или измеренным состоянием — **не всё является слагаемым суммарной стоимости**.

| Семейство | Кандидатные weightCode | Как использовать |
|---|---|---|
| DISTANCE/TIME | edge.length, edge.travelTime, node.serviceTime | стоимость перехода и обслуживания с учётом transportMode |
| COST | edge.moneyCost, node.serviceCost, branch.maintenanceCost | целевая стоимость после проверки валюты/даты |
| SUPPLY/DEMAND | node.supply, node.demand, branch.totalDemand | ограничения баланса и capacity |
| CAPACITY/LOAD | node.capacity, edge.capacity, node.currentLoad, edge.currentFlow | ограничения (не «плюс к стоимости») |
| PRIORITY/REWARD | node.priority, node.visitReward, node.mandatoryFlag | обязательное посещение, штраф за пропуск, prize collecting |
| RISK/RELIABILITY | edge.risk, node.failureProbability, branch.reliability | явно нормированная целевая функция или надежностное ограничение |
| ACCESS/TYPE | node.accessClass, edge.allowedNodeTypes, edge.allowedModes | жёсткая допустимость, не скалярный штраф по умолчанию |
| ENERGY/ENVIRONMENT | edge.energyConsumption, node.powerDemand, edge.emissions | ресурсы, суммарные бюджеты, ограничения |
| RESILIENCE/STATE | node.available, edge.closed, node.backupRole | маршрутизация/резервирование и scenario state |
| TEMPORAL | trafficWeight(t), demand(t), capacity(t), serviceWindow(t) | временно-зависимый поиск и оптимизация |
| SPATIAL/ZONE | altitude, slope, zone.penalty, zone.forbidden | геометрически обусловленные ограничения, только с доказуемой моделью |

GeoWeightDefinition требует:
weightCode, semanticKind (COST/REWARD/CAPACITY/DEMAND/RISK/PRIORITY/FLAG/MEASURE), subjectKind, typed unit, currencyPolicy, timeSemantics (INSTANT/INTERVAL/FUNCTION), aggregationOperator (SUM/MIN/MAX/WEIGHTED_AVG/PRODUCT/CUSTOM_TYPED/NONE), direction/validRange, null/NA/zero policy, allowed source/override policy, modelRevision and immutable SHA.
Профиль может содержать много кодов, но не динамический untyped map. Изменение ставки/веса/периода = новая ревизия профиля или scenario override с SHA. Неизвестный вес/нормировка = explicit validation error, не молчаливое значение 0. Нормализация и коэффициенты целей фиксируются в objective policy. Приоритеты, запреты и минимальные гарантии должны по умолчанию быть ограничениями/лексикографическими правилами, а не спрятанными внутри суммы.

**Стоимость посещения узла:** модель явно задаёт chargePolicy = EACH_ENTRY / ONCE_PER_PATH / ONCE_PER_SERVICE / EXCLUDE_TERMINALS; стоимость входа и обслуживания нельзя посчитать дважды из node и edge без documented decomposition. Для маршрута P при аддитивной стоимости C(P)=sum(edgeCost(e) for traversed edges)+sum(nodeCost(v) for counted visits), где transit, service and start/end policies pinned. Если есть отрицательные награды, не превращать их в отрицательные Dijkstra/Yen edge costs: использовать capability для orienteering/prize-collecting или иной корректной постановки.

**Агрегация ветвей:** subtreeDemand(v)=localDemand(v)+sum(child subtreeDemand) только в строгом дереве и для SUM-совместимой величины. В DAG/графе дедуплицировать descendant node IDs по явно заданной области; cross-routing edges не являются descendants. Надёжность/риски требуют отдельной модели зависимости отказов; вероятность и priority нельзя просто суммировать. Для depth=60 и более — итеративный traversal с visited/stack, bounded memory и проверкой циклов; не генерировать весь набор возможных потомков как экспоненциальный декартов продукт.

### 20.4. Solver families, multi-route and quality rules

| GEO family / taskCode candidate | Задачи | Алгоритм/capability |
|---|---|---|
| GEO.GRAPH.REACHABILITY.V1 | достижимость с типами, запретами, глубиной | BFS/DFS + policy gate |
| GEO.GRAPH.SUBTREE_AGGREGATE.V1 | веса ветви, критическая нагрузка | tree/DAG aggregation with dedup |
| GEO.ROUTE.SHORTEST.V1 | один минимально затратный допустимый маршрут | Dijkstra/A* if nonnegative additive edge cost |
| GEO.ROUTE.TOP_K.V1 | до K loopless shortest путей, default K=3 | Yen K-shortest with nonnegative costs + deterministic tie rule |
| GEO.ROUTE.DIVERSE_TOP_K.V1 | до 3 существенно разных допустимых маршрутов | candidate generation + typed overlap/diversity constraints, feasibility and ranking |
| GEO.ROUTE.MULTIOBJECTIVE.V1 | маршрут по стоимости, времени и риску | pinned separate policy objectives / lexicographic / Pareto |
| GEO.ROUTE.TIME_DEPENDENT.V1 | трафик, временные окна, доступность | time-dependent routing with FIFO property validation or specialized time-expanded model |
| GEO.NETWORK.FLOW.V1 | материальные/энергетические потоки и bottlenecks | max-flow/min-cost-flow, typed flow conservation |
| GEO.NETWORK.DESIGN.V1 | сеть соединений между множеством узлов | MST/Steiner/MILP subject to network conditions |
| GEO.LOCATION.ALLOCATION.V1 | размещение складов/подстанций/филиалов | facility location, p-median/p-center, MILP |
| GEO.COVERAGE.V1 | покрытие, набор сервисных зон | set cover/max coverage, geofences and resource caps |
| GEO.VRP.SERVICE.V1 | многоточка, груз, смены, временные окна | VRP/OR-Tools specialized solver |
| GEO.NETWORK.RESILIENCE.V1 | резервные пути, критические мосты/узлы | bridges, articulation points, edge/node-disjoint routes |
| GEO.CLUSTER.TERRITORY.V1 | группировка, деление территории на районы | spatial clustering + balanced allocation |
| GEO.SIMULATION.WEIGHT_SHOCK.V1 | перегрузка/отказ/временное изменение весов | immutable scenario comparison / future simulation module |
| GEO.GRAPH.CENTRALITY.V1 | центральные, наиболее критичные узлы | typed centrality metrics with definition/policy |

Первые кандидаты к квалификации: REACHABILITY → SUBTREE_AGGREGATE → SHORTEST → TOP_K (K=3) → DIVERSE_TOP_K; остальные — DESIGN_ONLY / CAPABILITY_DEPENDENT.

**Три разных смысловых запроса, не смешивать:**
1. TOP_K по ОДНОЙ стоимости: первые K (обычно 3) допустимых простых путей с canonical tie-breaker.
2. DIVERSE_TOP_K: K кандидатов с ограничением сходства, например maxSharedEdgeRatio с явно зафиксированным знаменателем (по количеству или длине) и допустимостью.
3. MULTIOBJECTIVE: отдельные оптимумы по времени/стоимости/риску или Pareto alternatives; нельзя выдавать три весовые комбинации за доказанный глобальный Pareto frontier без проверки.

Если доступно только 1–2 маршрута, вернуть actualPathCount=1/2, shortageReason=NO_ADDITIONAL_FEASIBLE_PATH; **не дорисовывать** третий путь. Если нет пути, status=UNREACHABLE with validated constraints and diagnostics. При disjoint-required, искать независимые пути подходящим max-flow/disjoint-path solver; если таких путей нет, не подменять их просто «разными» маршрутами. В чистом дереве маршруты root→leaf являются единственными по топологии.

Алгоритм указывается через GEO SolverCapabilityDescriptor: supported graph orientation, negative/nonnegative costs, node vs edge cost policies, time dependence, FIFO compliance, capacity, constraints, exactness, K/diversity, max graph size, CRS, numeric semantics and solver artifact versions. A* heuristic must be admissible (and consistency policy explicit for chosen implementation). Dijkstra/Yen запрещены при отрицательных приведённых стоимостях; негативные цены/награды требуют отдельного solver. Time-dependent FIFO assumption must be checked or explicitly unsupported; naive static weights with changing travel time prohibited. Graph route with direction violation, forbidden node or insufficient flow capacity is invalid even when shortest.

### 20.5. Data-plane, compilation and execution

Общая архитектура: Geo Inputs (points/edges/relations/zones) → type/CRS/topology/weight validation → immutable GeoGraphRevision + GeoWeightProfileRevision → GeoScenarioRevision → GEO-OPT compiler → OPT SolverCapabilityDescriptor → ONE standard Calculation Job → immutable GEO typed ResultSet → report/map projections.

- **Control plane:** existing CalculationPlanDTO/Calculation Session/InputContractDTO; GEO taskCode registered in shared dispatcher. Separate GeoGraphRevision and GeoWeightProfileRevision are referenced by exact content SHA.
- **Graph storage future option:** PostgreSQL + PostGIS spatial indexes and efficient spatial predicates, optionally pgRouting for road/network shortest paths; alternative in-memory adjacency lists for small abstract graphs; not a mandatory extra database/service.
- **Routing source:** explicit road/indoor/custom graph reference; no automatic promise of real road path or travel time merely from coordinates. If geodata includes provider/OSM licenses, trace source/license and allowable derivative storage/reuse.
- **Graph compiler:** validate stable IDs, duplicate edges/axes, missing endpoint, self-loop policy, graph orientation, hierarchy cycles, dimensionality, CRS, spatial accuracy, validFrom/validTo, disconnected components, forbidden types, null weight state, node/edge capacity, negative costs, and solver supported capability.
- **Shape:** immutable typed GeoGraphDatasetDTO (NODE_TABLE, EDGE_TABLE, HIERARCHY_TABLE, GEOMETRY_DATA, WEIGHT_TABLE, ZONE_TABLE, TIME_PROFILE) in versioned DatasetManifest; batch/chunk immutable manifests for large data. No unbounded embedded JSON graphs.
- **Execution binding:** graph SHA + geometry SHA + weightDefinition/profile SHA + scenario revision/SHA + source/target and constraint set + objective normalization/weight policy SHA + solver capability, numeric policy, solver artifact build and input dataset SHA, tenant/scope + idempotency. Changed weight/time/location must produce a new job/binding, while unchanged input batches can be shared with permission checks.
- **Results:** preserve standard CalculationResponseDTO root results[]; specific OutputSchemaRevision for GEO_ROUTE_PATH_SET/GEO_WEIGHT_AGGREGATE/GEO_NETWORK_FLOW/GEO_LOCATION_PLAN (candidates). Each path includes ordered nodeIds/edgeIds, measures by unit, objective component breakdown, travel/service time, type-policy feasibility, constraint residuals, overlap vs peer paths, optional trusted geometry ref and exact source lineage.
- **Execution:** durable jobs, lease/fencing, replay-safe result commit, rights isolation, archive/ACK and retention from Python Hub contract. No uncontrolled dynamic Python eval, JS eval, arbitrary user SQL or free-form solver plugin.
- **Postsolve verifier:** independently recompute path connectivity, direction, allowed node/edge types, all hard constraints, node-visit charging, resource sums, metric/currency/time semantics and claimed objective. Solver result that violates any becomes INVALID_RESULT / blocked admission.
- **No user-facing distance/time claims** until actual datasource and routing policy provide grounded metrics; geometric straight-line distance may be shown only as labeled estimate, not driving distance.

### 20.6. Performance, large hierarchy and dynamic weights

Performance is bounded by **actual V/E, graph sparsity, geometry complexity, candidate path count and solver class**, not just '60 levels'. Не разворачивать все возможные пути и комбинации: глубина 60 при branching factor 3 порождает потенциально экспоненциальное число потомков/путей. Использовать индексированные adjacency, lazy traversal, pruning, spatial index, bounded priority queues, maxPaths/maxCandidates/maxDepth/maxVisitedNodes/maxWorkUnits/maxRuntime/maxMemory and cancellation. Heavy tasks run asynchronously; prioritize common Hub tenant quotas and workload admissions, not unbounded per-request parallelism.

Dynamic values: eventTime / effectiveTime / observedAt / ingestedAt with source validity; traffic, capacity, shutdowns and demand are exact scenario snapshots (or versioned functions). Hot data cannot silently mutate an in-flight sealed execution. A later update invalidates derived cache via dependency closure / new scenario revision. Cache key includes all relevant source and algorithm revisions; cross-tenant cache retrieval always rechecks access. Route planning can use different model time (departAt, arriveBy, timetable), with declared timezone/calendar and time-dependent edge profiles.

No committed p95/p99, capacity claim or Rust speedup until benchmarked on realistic synthetic and permitted datasets. Dedicated Rust graph kernels, specialized routing database, OR-Tools, H3/other indexing may be evaluated after reference correctness and end-to-end measurement; they are NOT new mandatory services.

### 20.7. Golden fixtures and negative acceptance (design requirements only)

| Case | Input | Required outcome |
|---|---|---|
| GEO-G01 | directed ROOT→A(2)→T(3), ROOT→B(3)→T(4), ROOT→C(4)→T(5) | TOP_K(3) has paths A/B/C with objective costs 5,7,9 |
| GEO-G02 | GEO-G01 + disallow node B | exactly two paths A/C, costs 5/9, no invented third |
| GEO-G03 | strict hierarchy ROOT→A→A1, 60-deep parent chain, no cross-route edges | max depth=60, unique ancestor/path, bounded traversal |
| GEO-G04 | GEO-G01 add node A visit fee 4, EACH_ENTRY | A path cost 9, B path 7, C path 9; deterministic tie rule |
| GEO-G05 | branch A local demand 4 and child A1 demand 2 | additive subtreeDemand(A)=6; no route-edge double count |
| GEO-G06 | DAG two parents share one descendant of demand 5 | each eligible aggregate counts descendant once per declared scope |
| GEO-G07 | negative transformed routing edge cost under Dijkstra-only capability | unsupported/blocked, not success |
| GEO-G08 | disconnected target or forbidden path type | UNREACHABLE, no fake path |
| GEO-G09 | reverse-only directed edge | cannot traverse forward |
| GEO-G10 | node/edge capacity lower than demand | infeasible route/flow, explain bottleneck |
| GEO-G11 | WGS84 latitude 95 or CRS mixed without transform | invalid geographic input |
| GEO-G12 | first run graph A, then change edge weight in B | old immutable result stable, distinct new binding/cache key |
| GEO-G13 | same idempotency key but changed scenario RHS or weight | conflict, never return cached old result |
| GEO-G14 | two tenants identical graph content | tenant read/cached route isolation and ACL checks |
| GEO-G15 | stale worker after lease/fencing, crash/restart | at-most-one committed immutable outcome per scoped key |
| GEO-G16 | K=3 with disjoint-required but only 2 edge-disjoint routes | return 2 with shortage reason, no overlap fraud |
| GEO-G17 | dynamic route violates time-dependence/FIFO policy | unsupported or verified specialized solver, never static shortest misrepresentation |
| GEO-G18 | graph has cycle plus valid hierarchy/tree contract | invalid hierarchy (routing cycle independently allowed) |
| GEO-G19 | null demand versus explicit zero demand | different states, no silent zero substitution |
| GEO-G20 | 2D geographic edge in degrees treated as meter length | unit/CRS violation |
| GEO-G21 | two alternatives share all but trivial terminal edge, min-diversity ratio configured | filtered or reported, not called independent |
| GEO-G22 | concurrent hotspot weight updates during sealed job | exact snapshot consistency / immutable result and revised next job |

Independent reference examples, baseline path enumerator for small graphs, deterministic edge-order permutations, numeric objective re-evaluation and negative/property tests are mandatory before any status=TECHNICALLY_VERIFIED. Status PASS is **not claimed** by this document.

### 20.8. Product projection: Universal Weighted Spatial Graph Studio (future)

Two synchronized views on one sealed graph:
- hierarchical tree/branch panel: ROOT/children/descendants, depth 20–60 via virtualized lazy expansion, aggregated weights and branch bottlenecks;
- map/engineering canvas: GPS/indoor map, typed nodes, edges, restricted zones, route highlights and altitude/floor layers if supported.

Editor (DRAFT only) handles import CSV/GeoJSON/typed network datasets, manual placement, node/edge weight matrix, temporal overrides, dimension and unit validators. Users can request (a) Top 3 cheapest, (b) Top 3 diverse, (c) min time / min cost / min risk, (d) capacity allocation / coverage / flow. Sealing produces immutable graph/scenario revisions, job runs asynchronously and result becomes read-only; edits create new revisions. A path card must show objective, traversal edges, node charges, capacity and policy checks, overlap/difference and reproducibility hash. Map drawing does not qualify solver result.

### 20.9. Milestones and ADR

| Stage | Deliverable | Evidence gate |
|---|---|---|
| GEO-R0.0 | This design and OPT-R0 integration boundary | documented architecture, DESIGN_ONLY |
| GEO-R0.1 | Typed GeoNode, GeoEdge, HierarchyRelation, CRS and WeightDefinition/Profile, schema and hashing | formal DTO/negative schema cases |
| GEO-R0.2 | Graph compiler, hierarchy validation, subtree aggregate and reachability | golden fixtures, cycle, scale and reuse tests |
| GEO-R0.3 | Single shortest path with independent postsolve verifier | Dijkstra/A* gates, unit and type correctness |
| GEO-R0.4 | Top 3 loopless, diverse/disjoint route policies and diagnostics | G01–G22, no fake 3rd result |
| GEO-R0.5 | Calculation Hub job/session integration, graph snapshots, lease/tenant/idempotency | PostgreSQL + crash and isolation E2E |
| GEO-R0.6 | Multi-criteria, flow/capacity, coverage, location/allocation, time-dependent models | per-solver qualified examples |
| GEO-R0.7 | Graph Studio map/tree UI, scenario comparisons, 20–60 hierarchy virtualization | browser end-to-end, benchmark, UX |
| GEO-R1+ | VRP, project/utility network design, failure simulation, high scale | workload-specific benchmarks and independent approval |

Open ADR: GEO-ADR-01 hierarchy tree versus DAG contract; -02 coordinate/altitude CRS and local engineering transforms; -03 weight aggregation and missing states; -04 road data source/licensing and topology ownership; -05 negative costs / node reward formulation; -06 path diversity and tie policy; -07 temporal FIFO/non-FIFO capability; -08 data volume and solve SLO; -09 visibility/security of sensitive critical infrastructure; -10 integration with FIN project planning and production S2.

**First future executable vertical slice (only after separate authorization):** import 1 ROOT + 3 child branches + 1 target, 6 directed routing edges with weights; create sealed ScenarioRevision; run GEO.ROUTE.TOP_K.V1 (K=3) on existing Hub; independently verify costs 5/7/9; return immutable typed route result + evidence; then change one node weight to prove new revision and no stale cache. No new microservice or financial writer.
