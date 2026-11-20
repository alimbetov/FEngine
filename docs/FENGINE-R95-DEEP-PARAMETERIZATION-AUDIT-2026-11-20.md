# FEngine — повторный аудит параметризации всех 95 моделей (PARAM-R2)

**Дата:** 2026-11-20. **Статус:** SUBSTANTIVE_AUDIT_DRAFT / NOT_IMPLEMENTED / CONTRACT_FREEZE_BLOCKED / FINANCIAL_S2_HOLD.

## 1. Ключевая проблема предыдущего прохода

Формальная проверка «95/95 моделей имеют параметры» не была проверкой вариативности финансового метода. Реестр R1 содержал **83 заглушки BASE_METHOD_REVIEW из 95 моделей**. Первые 310 предложенных параметров не были превращены в полноценные обязательные/условные контракты, а большинство вариантов расчёта не имело отдельной method-revision политики.

В новом индивидуальном аудите:

| Результат | Количество | Статус |
|---|---:|---|
| HC-коды, имеющие отдельное решение по вариантам и параметрам | 95 | 95 строк, черновой методологический review |
| Предметные варианты расчётных методов | 201 | METHOD_CANDIDATE; не исполнены |
| Варианты с отдельными формульными описаниями R1 | 13 | черновые, включая ещё не завершённые описания SINKING_FUND и CUSTOM |
| Варианты, ожидающие формулу, Golden, применимость, рецензента | 188 | METHOD_FORMULA_REVIEW_REQUIRED |
| Typed parameter candidates в объединённом проектном реестре | 625 | 310 R1 + 36 variant-specific + 279 новых уникальных R2 |
| Повторяющиеся предложения, не продублированные при объединении | 7 | совпавшие ключи modelCode/parameterCode |
| Финансовые модели с production admission или независимым S2 | 0 | FINANCIAL_S2_HOLD |
| Подтверждённые финансовые HC-модули runtime | 0 | NOT_IMPLEMENTED |

R2-оценки рисков параметризации: **38 CRITICAL, 50 HIGH, 7 MEDIUM**. Это новая тематическая классификация **требуемого ревью**, а не перечень подтверждённых ошибок работающего кода. Предыдущие 28/42/25 имели другое основание — риск методологического описания.

## 2. Артефакты предметной ревизии

- **docs/FENGINE-R95-DEEP-PARAMETERIZATION-REVIEW.tsv**: 95 индивидуальных строк; существующий вариант, рекомендуемые альтернативы, конкретные поля (например, ENUM/REFERENCE/RATE/DATE/PERIOD), несовместимые настройки и blocker.
- **catalog/model_variant_profiles_r2.tsv**: 95 содержательных профилей, ни одной BASE_METHOD_REVIEW заглушки, все кандидаты из индивидуальной матрицы.
- **catalog/method_variant_definitions_r2.tsv**: 201 отдельный код варианта; qualification state и отсутствие действующего production method SHA.
- **catalog/method_parameter_candidates_r2.tsv**: 625 уникальных параметров; source class, logical type, requiredWhen, defaultPolicy=NONE, финансовый review pending, approval withheld.
- **docs/FENGINE-FLEX-METHOD-R1-METHOD-VARIANTS-TZ.md**: архитектура MethodVariant + ConfigRevision и детальное разделение амортизации имущества/кредита.

Никакой из R2 реестров не является подписанным машинным CalculationPlan или финальной версией TypeScript/Java/Python IDL.

## 3. Семейства и варианты — что нужно завершить до immutable freeze

| Семейство | Шт. | Предметные варианты и параметры | Главный блокер |
|---|---:|---|---|
| SET | 7 | posted/reversed, allocation order, due aging, legal netting, DSO/DPO basis | enforceable setoff и неизменяемое event replay |
| ECL | 7 | ageing/lifetime, default 12m vs recovery life, conditional PD/marginal, LGD paths, CCF EAD, stage policies | SICR/POCI, калибровка, EIR, default/recovery horizon |
| LOAN | 8 | fixed/floating, dated annuity/equal principal/bullet/custom, orig/revised EIR, local ГЭСВ | day-count, комиссии, кредитный договор, правила закона и статус solver |
| CASH | 8 | direct/indirect CFO, liquidity buckets, runway/scenarios, bank reconcile, FX | различие actual/forecast, restricted cash, валютные датировки |
| DCF | 9 | regular/dated NPV/IRR, FCFF/WACC и FCFE/Ke, TV Gordon vs multiple, sensitivity | multiple/tangent roots, terminal growth, currency/real-nominal |
| ACC | 7 | 3-statement, group elimination, FX translation, deferred tax, leases, OCI | учетный стандарт/обязательства/NCI/консолидация/ДТА |
| STOCK | 7 | FIFO, moving/periodic WAC, serial tracking, NRV, stock optimizer | не смешивать методы WAC/FIFO и корректировки/возвраты |
| ASSET | 7 | straight-line, units, declining, double-declining, cumulative SYD, annuity management, sinking fund, custom | IAS16/IAS36 basis, начало/конец, переоценка, life/residual |
| COST | 8 | ABC/direct, standard/actual cost, настоящий 3-factor PVM, cost escalation, BoQ, EVM | MIX отдельно от объёма, базы затрат и нормы |
| PLAN | 8 | rolling forecast, seasonal demand, safety-stock, LP/MILP, CPM/PERT, payroll, CAPEX | integer solver feasibility/optimality, budget, time-split |
| RISK | 7 | Monte Carlo/scenario, historical/parametric VaR, weighted ES, macro shocks | tail probability atom, covariance PSD, calibration, backtests |
| CAP | 2 | CAPM base/relevering, WACC market/target weights | beta/tenor/currency, tax shield |
| CREDIT | 2 | minimum viable rate and cashflow pricing, origination/portfolio RAROC | EL/funding double counting, capital denominator |
| CUST | 2 | per-customer/cohort CLV, discrete/interpolated payback | cohort retention and attribution, no-payback state |
| PF | 2 | LLCR/PLCR horizons, senior waterfall and DSRA | CFADS definition, priority, restricted reserve |
| ALM | 2 | contractual/behavioural repricing GAP, ΔEVE shocks | curve vintage, behavioral deposits, jurisdiction |
| FTP | 1 | matched-maturity or amortizing funding curve | rate interpolation/tenor/FX |
| PRICE | 1 | continuous price and discrete price-tick optimization | causal elasticity, stockout censoring, solver bounds |

**Важно:** не каждое изменение числа создаёт новый MethodVariant. Изменение annualRate при той же математике создаёт новую ConfigRevision; изменение STRAIGHT_LINE на SUM_OF_YEARS_DIGITS создаёт новую MethodVariant/MethodRevision. FCFF/WACC и FCFE/Ke — не взаимозаменяемые значения одного свободного параметра.

## 4. Особая ошибка — амортизация и нормативная применимость

Первоначальный ASSET.01 содержал 3 номинальных метода; не были проработаны кумулятивная, удвоенного уменьшаемого остатка, экономическая аннуитетная и накопительная. Новая модель вариантов перечисляет 8 кандидатов с отдельными параметрами и audit gates.

- **STRAIGHT_LINE:** стоимость минус residual по сроку; отдельная pro-rata policy.
- **UNITS_OF_PRODUCTION:** стоимость минус residual по фактическому объёму и принятой единице измерения.
- **DECLINING_BALANCE / DOUBLE_DECLINING:** ставка снижения, переход к линейному и terminal true-up.
- **SUM_OF_YEARS_DIGITS:** числовые веса оставшегося срока (кумулятивный).
- **ANNUITY_CAPITAL_RECOVERY_MGMT:** экономическое распределение капитала, при r=0 — утверждённая предельная ветвь; management-only без отдельной учетной квалификации.
- **SINKING_FUND_MGMT / CUSTOM_APPROVED:** требуют квалификации полной формулы/артефакта и не готовы для production.

IAS16 требует, чтобы метод отражал потребление экономических выгод и пересматривался с оценками срока/остаточной стоимости; прямо упоминаются straight-line, diminishing balance, units of production. Нельзя автоматически утверждать, что финансовый аннуитет разрешён как IAS16 бухгалтерская амортизация. Международные нормы и налоговые правила РК — отдельные датированные политики. Источник: https://www.ifrs.org/issued-standards/list-of-standards/ias-16-property-plant-and-equipment/

**HC.LOAN.02:** пять отдельных вариантов погашения долга (dated annuity, equal principal, interest-only balloon, bullet, custom contract) и grace как modifier. Это не методы из HC.ASSET.01, хотя название «аннуитетный» встречается и там и там.

## 5. Обязательные общие настроечные контракты

**MethodVariant:** modelCode, variantCode, methodologyApplicability, effectiveFrom, methodRevisionSHA, parameterContractSHA, Input/OutputSchemaSHA, algorithm manifest SHA, approved accountingBasis/jurisdiction, finance S2.

**ParameterDefinition:** logicalType, unit/currency/period, REQUIRED/CONDITIONAL/OPTIONAL, requiredWhen, forbiddenWhen, enum allowlist revision, range, source, default policy, semantic/rule rev, override authority, validation expressions. No unchecked default rates or free-text variants.

**ConfigRevision:** approved resolved values, scenario, FactSet/source SHA, numeric policy precision/rounding, effective date, immutable version/hash, reviewer and approval reference. Preview evaluates cross-parameter conflicts and reports specific reasonCodes.

**Invariants:** no double counting of ECL, fees, netting, FX or accounting cashflows; no silent change of method; no float silently used for money; no INFEASIBLE → OPTIMAL; no undefined→0; no automatic IFRS/regulatory eligibility from an available formula. A method change never rewrites old results.

**UI:** выбрать модель → вариант → параметрическую форму с динамической conditional validation → предварительный расчёт/ошибки/версии → сравнение конфигураций → immutable commit. До десяти рекомендованных сочетаний — ограничение UX, не число возможных MethodVariants.

## 6. Квалификация по этапам

- **PARAM-R2.A** — устранить незакреплённые requiredness, semantic enum allowlist, диапазоны, unit/currency/date и conflicts для 625 candidate params. Начать с 38 CRITICAL.
- **PARAM-R2.B** — независимо финансово проверить/отвергнуть 201 возможный вариант; в том числе развернуть 188 формул-кандидатов в математические контракты с ≥2 finance-reviewed golden для *каждого реально принимаемого варианта*; не считать все 201 обязательными методами.
- **PARAM-R2.C** — immutable registry/validator/CalcPlan Preview и отрицательные тесты на пересечение допустимостей, без финансового production.
- **PARAM-R2.D** — Python/Java reference runtime для уже квалифицированных вариантов, а затем нагрузочные/SQL/Rust parity тесты.
- **PARAM-R2.E** — опциональный Rust CPU ML shadow: модель прогнозирует вход, а не меняет законодательные правила.

**Общее решение:** предметный аудит 95/95 подготовлен, содержательные пробелы отражены в машиночитаемых реестрах. **Financial S2 и заморозка по-прежнему BLOCKED**; 201 кандидатный вариант не означает 201 качественный действующий расчёт.
