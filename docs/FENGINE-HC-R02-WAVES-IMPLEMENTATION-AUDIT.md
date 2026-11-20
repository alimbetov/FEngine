# FEngine HC-R0.2 — wave implementation audit and Python-first qualification

**2026-11-20 · main · Status: MATHEMATICAL_PYTHON_REFERENCE_PARTIAL / FINANCIAL_S2_HOLD**

## Truth table: catalogue versus executable coverage

| Topic | Status |
|---|---|
| Model candidates | 116 (20 families), unchanged |
| Model-parameter binding candidates | 732 |
| Unique textual parameter names | 704 |
| Candidate typed names | 709 |
| Name/type collisions | 5: calendarPolicy, taxShieldEligibility, horizon, dayCount, capitalBudget |
| Method variant templates | 222 candidate rows, unchanged |
| Mathematical Python reference model codes executable | 16/116 |
| Mathematically executable named variants (bounded subset) | 29/222 |
| Full auto-generated variants | NOT IMPLEMENTED / NOT QUALIFIED |
| Financial S2 qualified models/variants | 0 |
| PostgreSQL durable CalcPlan, issuer/tenant permissions, Rust parity | NOT IMPLEMENTED |

All historical R3 catalogues remain untouched. 732 are **occurrences**, not independently reviewed global semantic definitions. 709 grouped (name,type) keys are still *candidate* identities; identical name+type does not prove equal financial meaning.

## R0.2A — parameter semantics

- \`fengine_hc/semantics.py\`: actual 732-row scanner, consistent global candidate identities, exact five-collision baseline, per-model bindings, logical types and fail-closed variant resolver.
- Canonical \`CAND.<type>.<parameterName>\` is not a financially approved SemanticParameterId.
- Bounded explicit variant rules for DCF.01/.02/.03, LOAN.03, RISK.02/.03, ECL.02/.03; all unreviewed rules reject with \`VARIANT_RULE_NOT_IMPLEMENTED\`.
- All resolved configs carry deterministic SHA and immutable top-level config; \`reference_mode=True\` required.
- The 222 named templates are **not derivable from the current R3 fields alone**: missing reviewed full predicate DSL, financial applicability, conditional requiredness, source bindings and some enums. Do not claim automatically generated 222 combinations.

## R0.2B — genuinely computed math

\`fengine_hc/r02_math.py\`, \`ReferenceEngine.calculate\` and the portable golden bank:
- \`HC.DCF.03\`: polynomial cashflow IRR in the **explicit finite rate interval** via derivative critical points and monotonic bisection. Two-root, tangent-root and no-root tests; degree above 3 rejected until certified solver. No global/all-real-roots claim outside bounds. Only true numerical roots returned.
- \`HC.LOAN.03\`: dated cashflow root for one initial negative outflow and positive future receipts; ACT/365 fixed, explicit origin and fixed bounded search. Contractual fee eligibility, original/modified IFRS EIR and Kazakhstan GESV NOT reviewed.
- \`HC.RISK.02\`: exact nearest-rank empirical VaR of positive loss samples; no unqualified normal approximation or return/P&L sign conversion.
- \`HC.RISK.03\`: empirical quantile-integral Expected Shortfall; fractional mass on tied/terminal quantile handled. Weighted ES remains not implemented.
- \`HC.ECL.02\`: probability-weighted discounted losses from eligible first-year *default events*, including later loss settlement.
- \`HC.ECL.03\`: survival recursion from conditional period PD; no summing conditional default probabilities directly.
- Every unsupported model/variant is rejected. No “return 0”, “pass” or synthetic numerical admission.
- Real mathematical ECL is NOT automatically IFRS 9 ECL: need stage/SICR, scenario macro calibration, PD/EAD/LGD source checks, multiple recoveries, original EIR, credit-impaired/POCI and full cash shortfall definition.

Golden input/output JSON: \`tests/golden/hc_r02_reference_vectors.json\`. The independent checks in \`tests/test_fengine_hc_r02_math.py\` and \`tests/test_fengine_hc_r02_portable_golden.py\` compare Decimal values and error reasons. Baseline for future Rust, **not Rust parity PASS**.

## R0.2C — typed cross-model executable plan

- \`fengine_hc/graphs.py\`: model-level candidate DAG remains 116 nodes and 55 unqualified candidate edges.
- InMemoryCalculationPlan now deep-snapshots inputs/config, pins an immutable \`plan_sha256\`, rejects cycles, unknown graph jobs, input collisions and *unreviewed cross-model field bindings*.
- First explicit typed port-edge allowlist: \`HC.CAP.01.costOfEquity (DECIMAL_RATE, PER_ANNUAL) → HC.CAP.02.costOfEquity (DECIMAL_RATE, PER_ANNUAL)\`; runtime bound values must be canonical Decimal strings. The test runs both executors end-to-end.
- The other 54 candidate edges are **not executable by implication**. Future model port contracts must include unit, currency, period, scope, schema revision, as-of, type and source lineage to become qualified.
- This plan is **in-process and immutable-in-memory**, not persisted. Its SHA is not a signed immutable PostgreSQL transaction receipt; job retries, fencing and outbox still absent.

## 9 reusable primitive families and 20-family coverage matrix

The full design matrix is retained in [HC-R0.1 meta-model and primitive matrix](FENGINE-HC-R01-METAMODEL-PRIMITIVE-MATRIX-AND-EXECUTION.md):
PV, ROOT, SCHED, AGG, PROB, FX, EVENT, OPT, NUM. Numerically implemented coverage is *partial*. TASE's 13 operators remain independent.

## Exit gates and next wave priorities

1. **R0.3A — precision/qualification hardening:** freeze wire IDL, decimal scale/rounding stage, cashflow direction, day count, monetary units, all root-domain completeness semantics, independent high-degree solver. No S2 implied.
2. **R0.3B — economic and statistical methods:** dated forward/reset curves, multi-scenario loss paths, portfolio correlation, multiple recovery schedules, statutory fees only after method qualification.
3. **R0.3C — verified planner:** typed schema ports beyond CAPM→WACC, currency/unit/time/tenant verification, qualified dependencies for priority W1/W2 models; immutable plan storage in PostgreSQL with fencing.
4. **R0.3D — model coverage:** extend only with independent numerical golden, boundary and negative tests, no generic “execute all 116”.
5. **Rust** follows frozen Python numerical semantics, cross-engine goldens and representative performance tests; no performance claim yet.

### Required verification

\`\`\`bash
python -m unittest discover -s tests -v
\`\`\`

Run Python 3.11 and 3.13. Claim PASS counts only from the current HEAD's completed GitHub Action, not from historical results. Financial production remains blocked until independent S2 with exact artefact bindings.
