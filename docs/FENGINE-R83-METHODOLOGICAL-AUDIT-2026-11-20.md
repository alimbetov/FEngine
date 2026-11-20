# FEngine — методологический, математический и технический аудит 83 моделей

**Audit:** FENGINE-R83-AUDIT-R0.1; **дата:** 2026-11-20; **ветка:** main.  
**Статус:** REVIEWED_AS_DRAFT / CONTRACT_FREEZE_BLOCKED / FINANCIAL_S2_HOLD.  
**Граница:** 83 финансово-экономических спецификации, 81 проектный Dataset DTO, 235 исходных фактов, отдельная Python GEO-OPT reference-вертикаль. Новая реализация расчётного Python Hub и финансовых моделей не создавалась.

## 1. Доказанные результаты, без подмены понятий

| Проверка | Результат | Уровень доказательства |
|---|---|---|
| Все HC-коды и уникальные task codes | 83/83, P0=14, P1=42, P2=27 | Статический аудит трёх ТЗ |
| Поля Input, Parameters, Method, Output, Golden, Negative, DAG | 83/83 формально присутствуют | Документная полнота; не executable IDL |
| Типы входных наборов D01–D81 | 81/81 | Транспортные кандидаты, не реальные FIN table bindings |
| Каталог исходных фактов | 235 уникальных, 235 DRAFT | catalog/facts.tsv |
| Независимый арифметический банк | 83/83 PASS | Внешний локальный Python Decimal, не импортирует модели FEngine |
| Дополнительные пограничные математические примеры | 34/34 PASS | Отдельные математические проверки, не FEngine runtime |
| Реальный Python GEO-OPT, Python 3.11 | 38/38 PASS | GitHub Actions |
| Реальный Python GEO-OPT, Python 3.13 | 38/38 PASS | GitHub Actions |
| HC 83-model execution, DTO/session/outbox integration | NOT IMPLEMENTED / NOT TESTABLE | В коде нет финансового Python Calculation Hub |
| ECL calibration, VaR/ES out-of-sample, regulatory GESV, optimizer optimality | NOT QUALIFIED | Нет исторических валидационных данных, регуляторных golden или исполнителей |

**Надёжное свидетельство GEO-OPT:** https://github.com/alimbetov/FEngine/actions/runs/44699098351. Каждый из двух CI job логи подтверждают Ran 38 tests. Не переносить этот PASS на 83 финансовых модели.

**Арифметические банки:** fengine_spec_oracle_bank_83.py, fengine_83_oracle_bank_results.json, fengine_adversarial_math_bank.py и fengine_adversarial_math_results.json. Созданы/исполнены в аудиторской среде; отчёт и исходные скрипты могут быть отдельно выгружены. Не приписывать их существующему CI, пока они не интегрированы.

## 2. Обобщенная оценка качества по 11 семействам

Оценка относится к полноте математической **концепции**, а не проверенной точности работающего кода: B = разумная заготовка, требующая детализации; C = высокие методологические неопределенности; D = известная смысловая неполнота.

| Семейство | Кол-во | Уровень | Что необходимо до заморозки |
|---|---:|---|---|
| SET | 7 | B | Порядок погашений, сторно, допустимость взаимозачёта, DSO/DPO |
| ECL | 7 | C | SICR/Stage, PD/LGD/EAD, термины дефолта и взыскания, независимая калибровка |
| LOAN | 8 | B/C | Day count, плавающая ставка, нерегулярный график, EIR/ГЭСВ |
| CASH | 8 | B | Actual/forecast, FX, банковская сверка, CFO direct/indirect |
| DCF | 9 | B/C | Discount basis, IRR root isolation, terminal growth, реальная/номинальная ставка |
| ACC | 7 | C | OCI/NCI, консолидация, налог, аренда, правило S2 |
| STOCK | 7 | B | Возвраты, FIFO layers, WAC variant, NRV, единицы |
| ASSET | 7 | C | Компоненты, переоценка, IAS36 impairment, CGU |
| COST | 8 | B/D | PVM не выделяет MIX; ABC drivers; EVM baseline; BoQ |
| PLAN | 8 | C | Интегрированный forecast DAG, датировки, целочисленная оптимизация |
| RISK | 7 | C | Корреляции, VaR/ES дискретные хвосты, PRNG и статистические бэктесты |

**Приоритизация** — 22 CRITICAL, 37 HIGH, 24 MEDIUM. Это экспертная предварительная классификация **методических рисков/пропусков**, не статистически измеренная вероятность финансовой ошибки. Для каждого из 83 кодов есть индивидуальная строка в приложении: docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv.

## 3. Блокирующие дефекты и важные математические границы

### P0-A: Price-Volume-Mix — конкретная смысловая проблема

HC.COST.03 сегодня называет расчет Price-Volume-Mix, но formula вариант рассчитывает price и «volume» без отдельного mix term. Контрпример: SKU-A (20 KZT, объем 5→8) и SKU-B (10 KZT, объем 5→2); суммарно 10 единиц до и после; цены неизменны. Выручка +30 KZT исключительно из-за MIX, тогда как текущий «volume» выдаёт +30. **Требование:** явный вариант decomposition PRICE + TOTAL_VOLUME + MIX (+ interaction согласно утвержденной методике) и контроль нулевого total-volume effect на этом кейсе. Заблокировать переименование существующего двучленного эффекта в истинный PVM.

### P0-B: ECL и PD

12-month ECL означает lifetime cash shortfalls, возникающие из дефолтных событий, возможных в первые 12 месяцев, а не только денежные потери, полученные до конца этих 12 месяцев. Для Lifetime ECL условная PD по периоду должна переходить в marginal PD через survival. Пример q1=0.10,q2=0.20: survival2=0.72, cumulative PD2=0.28, marginal PD2=0.18. Утверждение q1+q2=0.30 как cumulative PD ошибочно.

**До freeze:** defaultEventDefinitionRef, creditStageSicrPolicyRef, conditionalHazardPolicy, originalEIRBasis, cashShortfallRecoveryHorizon, scenarioWeightTolerance, forecastScenarioCalibrationRef, EAD effective-date, LGD recovery-date discount, POCI and post-model adjustment policy. Для ECL исключить автоматическое принятие формулы EAD×PD×LGD без ограничений по временному горизонту и расчетной политике. Нужен независимый ECL reviewer.

### P0-C: кредиты и ставки

Разделить четыре типа: договорная nominal annual ставка, начисление за период по day-count, бухгалтерская IFRS EIR и нормативная ГЭСВ РК. Для графика с нерегулярными датами нельзя безоговорочно применять формулу аннуитета для равных периодов. Для EIR необходима classification eligibility of fees/initial carrying, approved cash direction, original vs revised rate, day count, convergence residual and multi-root handling.

**ГЭСВ РК:** правовая редакция постановления АРРФР 03.04.2026 №44; требуются пункты 11 (формула), 12–14 (комиссии и применимость по сторонам), 22 (итерационный метод), 23 (округление до сотых процента), дата вступления и тип договора/организации. Арифметика 110/98−1 не равна государственной квалификации ГЭСВ. https://old.adilet.zan.kz/rus/docs/V2600038333

### P0-D: DCF, IRR, XIRR, terminal value

Для FCFF применим WACC, для FCFE стоимость собственного капитала Ke; смешение требует блокировки. Для GORDON TV выполняется WACC>g. Нужны currency/inflation/period compatibility, midyear or end-year cash timing, valuation date, day-count, bounded domain, exact precision/rounding.

**Нетривиальная проверка:** CF=[−100,+200,−100] при t=0,1,2 имеет двойной корень IRR=0. NPV с обеих сторон корня отрицателен, поэтому простой поиск смены знака может его пропустить. До freeze — rootIsolationAlgorithmRevision + rootCompletenessStatus, no-root, multiple-root, tangent-root tests. XIRR требует собственный алгоритм датированных потоков.

### P0-E: статистический риск

VaR зависит от потерь/знака, горизонта, квантильной политики и обработки весов. Expected Shortfall определяется интегралом по хвостовым квантилям, включая долю вероятности на точке VaR. Пример дискретных убытков [0,10,20,20,100], равные веса, α=0.75: nearest-rank VaR=20, quantile-integral ES=84. Наивный E[L | L>VaR]=100 неверен. Нужны tail-mass rule и отдельный статистический контроль.

Monte Carlo: frozen seed, PRNG build SHA, joint factor distribution and PSD correlation, sample size, convergence/MC standard error, time-independent replay. Ни четыре сгенерированных примера, ни простое совпадение математического ожидания не доказывают калибровку 99% VaR/ES.

### P0-F: оптимизация

Любая модель планирования требует явной objective direction, integrality, constraints/units, feasible-set, time budget, bound gap, solver version, tie-breaker and infeasibility diagnostics. Недопустимо возвращать feasible heuristic как globally optimal. При расчетах с дробными проектами в CAPEX / MOQ запретить несанкционированную замену целочисленного решения непрерывным.

GEO-OPT существует как референсный **отдельный модуль**: directed edges, Decimal nonnegative costs, hierarchy tree, Dijkstra/A*/Yen top-3. Динамические веса, дороги/PostGIS, независимые альтернативы, Optimization Solver и Calculation Hub интеграция **не реализованы**. Не считать GEO одним из 83 HC кодов.

## 4. Контракты и настроечные параметры: жесткое правило до FREEZE

**Рабочий перечень по всем 83:** docs/FENGINE-R83-CONTRACT-HARDENING-MATRIX-2026-11-20.tsv. Таблица содержит (код, P0/P1/P2, семейство, риск, 1–5 обязательных дополнительных параметров с типами, 1 критический отрицательный тест, ML relevance и фактический runtime/source/S2 status).

Все параметры в MethodParameterContractV2 обязаны иметь: parameterCode, parameterRevision, logicalType, unitCode/currency/period, REQUIRED/CONDITIONAL/OPTIONAL, explicit conditional expression, min/max, enum allowlist, default origin and source, effectiveFrom/to, financialApplicability, overridePermission, ownerApproval, resolvedSha256, cross-parameter constraints. CODE не может быть «временно свободной строкой» внутри immutable published method; вариант методики меняет собственную immutable revision.

**Обязательные глобальные поля:** methodRevision, input/outputSchemaRevision, signed NumericPolicy (precision/scale/rounding stage/FX), reportingBasis, asOf/period, unit/currency, source FactSet sha, plan sha, output/algorithm artifact sha, tenant/scope, scenario, source lineage, admission evidence and resourceBudget. Не все поля передавать от клиента; resolved values обязаны быть доказуемо включены в immutable binding.

**Reason taxonomy:** JobState, CalculationState и ValueState являются разными enums. BLOCKED_SOURCE, NOT_COMPARABLE, FINANCE_S2_HOLD, INFEASIBLE, CALIBRATION_REQUIRED, TIME_LIMIT являются reasonCode для базовых состояний; не менять трактовку существующих enum без новой OutputSchemaRevision. Для distribution/scenario/optimization result shapes требуется новая согласованная версия DTO.

**Решение:** **НЕ замораживать пока** Method/Parameter/Input/Output contracts. Новые параметры сначала согласовать в таблице и привести существующие W1/W2/W3 draft к однозначным строгим схемам, затем проводить freeze точных ревизий.

## 5. Банк тестов: границы PASS и обязательные новые кейсы

Пройдено локально: 83 независимых синтетических арифметических контрольных проверки и 34 дополнительных пограничных/invariant проверки. Эти тесты **не импортировали** финансовые модели FEngine (таких исполняемых модулей нет). Случаи для 34 included: 12m vs lifetime PD, LGD recovery date, leap year day-count, PVM mix, double IRR root, ES tie mass, WAC/FIFO roll-forward, discounted cash, optimized 0/1 CAPEX, scenario weights/PSD, first-passage cash.

Пройдено в GitHub Actions: GEO-OPT 38/38 на Python 3.11 и 38/38 на Python 3.13, workflow reference-checks.yml commit a362bf50f7c3b9641b81dccf85816d4eb3a31d09. Не заявлять 159 «реальных» финансовых модельных тестов: 83+34 независимы от FEngine runtime.

**Для каждого из 83 до Method FREEZE:** минимум два независимых финансово проверенных golden вектора, один boundary case, missing-vs-zero, negative sign/denominator, currency/unit/date mismatch, stale method/source/approval, duplicate idempotency key and source-authorization checks; plus family-specific stress. Каждая машина-читаемая TestCaseDTO должна иметь inputSha, parametersSha, methodSha, expected status/reason, expected exact values with type/tolerance, reviewer, financial basis, source revisions and testClass.

**Разделить классы PASS:** SPEC_COVERAGE, INDEPENDENT_ARITHMETIC, PROPERTY_INVARIANT, REGULATORY_CONFORMANCE, STATISTICAL_BACKTEST, PYTHON_RUNTIME_UNIT, PYTHON_RUNTIME_E2E, SQL_CROSSCHECK, RUST_PARITY, OPERATIONAL_CRASH, PERFORMANCE. Любая ячейка может PASS только после собственного evidence.

## 6. Помощь ML: где дает полезный прирост, а где запрещена

Для планирования в отдельных строках 83-model matrix: ML-assistance candidate YES=34, OPTIONAL=2, NO=47. Эти 34 **возможности** не равны моделям ML, которые уже созданы или прошли проверку. В первую очередь смотреть:

| ML задача | Где помогает | Как доказывать пригодность |
|---|---|---|
| PD survival/credit scoring | ECL.01–.04, RISK.05 | temporal calibration, Brier/logloss, stability, overrides, out-of-time validation |
| LGD and EAD forecasting | ECL.05–.06 | censored recovery, coverage and bias, segment drift |
| cash, demand and seasonal forecasts | CASH.01/.03, PLAN.01/.02/.03, STOCK.07 | rolling-origin backtest, censored sales, benchmark to seasonal naive |
| anomaly assisted classification | CASH.06, ACC.04, COST.02/.06 | human-review false-positive control, no automatic accounting posting |
| factor scenarios and Monte Carlo proposals | RISK.01/.02/.03/.07, DCF.09 | backtested tail, PSD covariance, calibration and reproducibility |
| operational maintenance and capacity | ASSET.06, PLAN.04 | temporal holdout, hard feasibility maintained in deterministic solver |

Prefer transparent baseline before gradient boosting. Candidate Python models for research: logistic/hazard and survival models, generalized additive models, LightGBM/CatBoost where appropriate, calibrated quantile regression and time-series forecasting. Data source and stable event history prerequisites; no training on synthetic golden examples.

**No replacement of deterministic computations by ML:** loan ledger arithmetic, accounting recognition, statutory GESV, contractual EIR eligibility, FIFO, settlement idempotency, IRR root definition, legal offset, optimization feasibility and business policy are deterministic/legal rules. ML may propose forecasts, features or suggested classifications, **not silently alter a financial result**.

**Proposed MLModelRevisionDTO:** modelArtifactSha, featureSchemaSha, trainDataSha, labelDefinitionRevision, featureAvailabilityCutoff, trainValidationTestTimeSplitSha, calibrationEvidenceSha, inferenceNumericPolicy, effective dates, monitoring/driftPolicy, humanApproval and rollback. Inference outputs must have lineage and distinct status, consumed by financial formula only with approved policy; ML and Python/Rust calculation execution remain separate logical boundaries.

**External governance benchmark:** US Federal Reserve SR 26-2 issued 2026-04-17 supersedes earlier SR 11-7; applies in relevant US supervisory scope, **not automatically Kazakhstan regulation**. https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm . IFRS9 ECL quality benchmark: https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/pap/20

## 7. Python/Rust optimization recommendation

Optimization of runtime is **not** first priority before semantics/goldens. Baseline comparison required on one same immutable dataset and same financial policy:
1. Pure Python Decimal reference and method-level golden bank.
2. PostgreSQL/JDBC grouping and reconciliation for set-based finance data.
3. Calculation Session immutable batch reuse and optionally bounded local/Redis cache.
4. Rust typed batch hot paths, only when Python vs SQL vs Rust full-path benchmark and parity justify migration.
5. Heavy optimization separate LP/MILP/constraint solver with bounded resource and residual/optimality proof. ML is a forecast input, not the optimizer correctness proof.

Report ingestion, serialization, memory, queue wait, compute, archive commit, p95/p99, recovery, and exact-money parity. No universal claim that Rust/Redis speeds all 83 operations.

## 8. Required acceptance work and release decision

| Stage | Mandatory outcome | Gate |
|---|---|---|
| AUD-R0.1 | Resolve 83-row proposed params and semantic defects, including true PVM, ECL, KZ GESV, ES, root isolation | Mathematical and finance review |
| AUD-R0.2 | Map exact FIN fields/source revisions to D01–D81 and freeze asOf/units/dimensions; 235 DRAFT facts cannot be auto-qualified | Source validation |
| AUD-R0.3 | Two or more independent finance-reviewed goldens/model, negative/property bank, scenario/calibration tests | Independent reviewer |
| AUD-R0.4 | Formal versioned Method/Input/Output/Parameter IDL and canonical SHAs, reasonCode/ResultShape compatibility | CONTRACT_FREEZE_CANDIDATE |
| PY-R0 next | Implement actual Python Decimal math/worker, registry/session/PG/inbox/outbox; run E2E and CI | Separate implementation approval |
| ML-R0 next | Only opt-in shadow models using legal historical data, time split/calibration and sign-off | No silent financial override |
| RUST-R0 future | Rust hot-path parity and benchmarks against Python/JDBC | Proven advantage only |

**Final verdict:** 83/83 have usable **draft design skeletons** and arithmetic smoke vectors. **0/83 have confirmed executable financial model E2E**, **0/83 have independent financial S2**, so **freeze is blocked**. GEO-OPT is the only verified working Python reference slice, outside the 83 scope.
