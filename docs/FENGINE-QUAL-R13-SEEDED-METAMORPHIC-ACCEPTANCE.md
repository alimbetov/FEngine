# FEngine QUAL-R1.3 — Seeded property-based & metamorphic reference qualification

**Scope:** repository `alimbetov/FEngine`, branch `main`. Synthetic, bounded, deterministic Python 3.11 / 3.13 reference execution only. **No FIN integration; no Redis Runtime; no Rust; financial S2 closed.**

## Acceptance rationale

R1.2 introduced one separately authored numerical golden and one domain-specific rejection for **each of 48 executable HC variants across 27 model codes**. R1.3 expands coverage with **1,348 explicitly counted generated cases** over several high-risk model families and the shared temporal engine. **This does not mean 1,348 unittest methods or randomized full coverage of all 48 variants.** Cases are constructed deterministically from fixed `random.Random` seeds and bounded integer-to-Decimal conversions, with no binary float, network, dependency on FIN, ephemeral real customer facts or nonrepeatable randomness.

The numerical oracles are written outside the production models. Examples include discounted principal equations, closed-form IRR roots, survival recursions and original component totals. A matching SHA alone cannot satisfy an oracle.

| Family / pattern | Generated cases | Seed / source |
|---|---:|---|
| Four ACT/365 Fixed dated loan variants, **nonzero rates**, variable terms and payment dates | 64 × 4 = **256** | `SEED_LOAN = 0xA0513001` |
| Metamorphic linearity of loan principal across four variants | 16 × 4 = **64** | same loan seed |
| 12-month default-event ECL and lifetime conditional-survival ECL, independently discounted | 100 × 2 = **200** | `SEED_ECL = 0xEC113002` |
| ECL exposure-scale and discount-rate monotonicity | 12 × 2 = **24** | same ECL seeds |
| IRR: known unique root, both registered variants | 80 × 2 = **160** | `SEED_ROOT = 0x1AA13003` |
| IRR: polynomial with two independently planted algebraic real roots | **56** | derived independent cashflow polynomial |
| IRR: tangent/double root is reported only once | **16** | independent repeated-root polynomial |
| EIR: irregular ACT/365 Fixed dates (31, 93, 181, 365, 366, 400, 730 days) | **80** | independent zero-XNPV relation |
| VaR and Expected Shortfall discrete sample-quantile / tail-integral | 80 × 2 = **160** | `SEED_RISK = 0xAB131304` |
| Temporal monthly→quarterly→annual SUM across three branches | 40 × 3 = **120** | `SEED_TEMP = 0x7A531305` |
| Ratio of sums recomputed from aligned original source components at 3 grains | 30 × 3 = **90** | independent numerator/denominator totals |
| Daily EVENT_AT sources with 29-day leap February, daily and monthly output (LOGISTICS contract) | **50** | only allowed product/grain semantics |
| V1.1 full-window NPV re-execution and V1.2 exposure-weighted CAPM total | 24 × 2 = **48** | original cashflows, betas and weights |
| V1.2 dated XNPV with ACT/365 Fixed fractional exponents | **24** | independent origin-fixed discounting |
| **Total** | **1,348** | Fixed, versioned scenario budgets |

In addition to the generated cases, each file executes explicit negative contract controls: invalid loan payment order, marginal first-year PD sum over one, nonconventional EIR, and disappearance of a branch in a complete interval series.

## Financial and technical correctness boundaries

- **Loan schedules:** independently derive each period's interest from prior principal × annual nominal rate × exact ACT/365 Fixed day fraction; derive equal-payment level using discounted dated cashflows; check every opening, interest, principal, payment and closing balance. Both interest-only/balloon and bullet accumulation rules are tested. Principal, interest and cash-payment totals reconcile independently. Nonzero rates, date variation and proportionality to principal are mandatory.
- **ECL:** independently compute 12-month marginal default probabilities and lifetime `survival_previous × conditional_PD`, then separately discount expected losses by original settlement date. PD, LGD and EAD are bounded; invalid conditional event orders and PD mass must fail closed. Exposure scaling and increasing-rate discount reduction are checked.
- **IRR and EIR:** inputs are algebraically constructed from their known roots, including two-root and tangent-root polynomials. The engine must identify all real roots within the declared domain and reject ambiguous requests for a single root. EIR future receipts are constructed independently from a known annual rate and irregular calendar gaps, not by calling the numerical root solver.
- **Risk:** nearest-rank VaR and fractional upper-tail ES are independently computed from the original ordered loss sample. A separate edge case exercises tail mass below one sample. Never treat an empirical tail mean as a simple unweighted entire-sample mean.
- **Temporal:** exact original-source SUM and ratio of aligned components across months, quarters, years, multiple branches and leap February. Source population and strict calendar-grain contracts remain binding. V1.1/1.2 model-temporal totals are independently checked against original financial values rather than sums/averages of output bucket values.

## Precision and reproducibility

All data generators use private `random.Random` instances seeded by named constants. No `hypothesis` package, external API, network access or global random state is required. Decimal arithmetic is isolated with explicit `localcontext(prec=65)` where independently compounded rates and fractional exponents are involved.

The bounded numerical acceptance tolerances are encoded in the test files and are **reference arithmetic comparison tolerances**, not approved production currency-rounding or regulatory tolerances:

- Dated loan per-row and conservation: absolute ≤ `1e-25` units.
- ECL independent discounted outputs: absolute ≤ `1e-25` units.
- IRR / EIR roots: absolute ≤ `1e-20`, EIR ≤ `1e-18` for 31–730-day fractional exponents.
- Empirical ES: ≤ `1e-26`; VaR uses exact equality.
- Temporal sums and ratios / NPV / XNPV / CAPM: absolute ≤ `1e-28`.

A failed case names its versioned seed, index, variant, field, calendar or component. Preserve the smallest failing case as an additional permanent targeted golden if implementation corrections are needed; do not weaken a numerical tolerance merely to make CI green.

## Mandatory CI

[Python reference workflow](../.github/workflows/reference-checks.yml) runs the following three additional **independently executable** suites on both Python 3.11 and Python 3.13, before the full test discovery suite:

~~~bash
python -m unittest discover -s tests -p 'test_fengine_qual_r13_loan_ecl_properties.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r13_irr_eir_risk_properties.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r13_temporal_properties.py' -v
python -m unittest discover -s tests -v
~~~

The separate methodology reference-bank CI must also pass on the **same exact HEAD**. Executed scenario counts are kept as assertions within individual tests; passing full regression alone does not imply S2.

## Qualification findings during development

Early QUAL-R1.3 CI detected two *test-harness* defects, corrected without modifying financial production models:

1. **ES independent oracle: fractional upper tail < one observation.** A Python `ordered[-whole:]` slice with `whole=0` incorrectly included **all samples**, dramatically inflating the independent reference. Fixed with an explicit empty full-sample selection and a fractional highest-loss atom.
2. **Product/period-grain admission.** The FIN TASE product intentionally does not admit DAY output. The day-level test was moved to LOGISTICS `DISTANCE_KM EVENT_AT`, which explicitly admits DAY and MONTH. No unreviewed admission was granted.
3. **Quarterly population loss.** A missing June branch must fail at per-leaf `PARTIAL_COVERAGE` (the branch is still present during April/May), while MONTH output detects missing cohort as `PARTIAL_COHORT_COVERAGE`. Both are precise hard errors, not synthetic zeros.

The financial model implementations were not edited in this wave; no model bug may be claimed merely because a newly authored oracle failed.

## Still out of scope

- Financial production S2, upstream trust signatures and permitted real financial fact sources.
- Actual, authenticated user/project FIN source ingestion.
- Redis expiry, 10,800-second absolute TTL, ACK/purge protocol and Redis failure resilience (all deferred).
- Rust translation, performance parity or production service admission.
- Full exhaustive coverage or property testing of every one of 48 variants; the remaining families retain the earlier R1.2 independent numerical and domain-negative gates. Further campaign coverage requires a reviewed mathematical risk matrix and more boundary constraints.
