# FEngine — единая спецификация финансово-экономического аналитического ядра

Версия документа: 0.1 (первичная концепция)
Дата: 2026-11-20
Репозиторий: https://github.com/alimbetov/FEngine
Статус: DRAFT / архитектурное задание; не является свидетельством реализованных расчётов.
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
