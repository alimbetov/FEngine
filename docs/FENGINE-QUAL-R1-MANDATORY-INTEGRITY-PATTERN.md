# FEngine QUAL-R1 — mandatory semantic integrity / adversarial testing pattern

**Adopted:** 2026-11-20 · **Branch:** main · **Mode:** synthetic Python/Decimal mathematical reference only, **not financial S2**.

## Why this gate exists

A numeric result may be internally consistent and look credible while combining facts from **different dimensions, populations, periods, revisions or valuation bases**. Traditional successful-case golden vectors do not detect this defect class.

The mandatory rule is:

**Never accept a mathematical success-only golden as sufficient. For every new executable model/variant or new temporal capability, pair an independent numeric oracle with a suite of deliberately inconsistent source transformations, and assert that they either produce the precisely justified changed result or fail closed with the expected stable error code.**

The pattern is applied in two complementary layers:

1. **Common-kernel executable tests:** assertions for source cohort preservation, atomic component identity and time-window alignment, nonoverlap, event/exposure pair matching, scope isolation, a reproducible Decimal numeric oracle and deterministic receipt under permutation. These are real tests of TASE, not inventory-text checks.
2. **Every registered executable HC variant:** explicit requirement metadata and a named existing model test file. The CI gate requires that **all 48** entries across **27** model codes have the core plus family-specific risk pattern declarations and a test fixture referencing that variant. Unlisted or newly added variants require an explicit inventory/test review rather than silently entering the "tested" column.

**Important qualification distinction:** an inventory risk pattern entry is an **obligation**, not proof of an independently executed adversarial scenario for that exact variant. The common-kernel tests enforce kernel integrity; model-specific independent goldens/negative paths must still be inspected before financial approval. This rollout does **not** certify all 48 variants as independently S2-qualified.

## Mandatory test transformations

| Pattern | Positive control | Adversarial mutation | Required result |
|---|---|---|---|
| Independent Decimal oracle | Independently recomputed value | Change amount, precision or input basis | Correct changed value or exact error; never a copied engine oracle |
| Atomic dimension alignment | Same date, branch, SKU, account for all ratio components | Profit from A, revenue from B | `COMPONENT_ALIGNMENT` |
| Complete cohort | Each reported branch/cost centre exists in every complete bucket | Remove B from February; retain A | `PARTIAL_COHORT_COVERAGE`, not a plausible diminished total |
| Nonoverlapping source | One canonical source interval per leaf | Overlap Jan–Feb 15 and Feb–Mar, even in partial mode | `SOURCE_OVERLAP` |
| Weighted pair identity | Rate and exposure have identical date+full dimensions | Pair rate in A with exposure in B or wrong date | `PAIR_ALIGNMENT` |
| Stock snapshot comparability | Compatible snapshots for every required leaf | Remove one branch in middle period | `PARTIAL_COHORT_COVERAGE` rather than silent carry-forward or drop |
| Scope isolation | Same authorized synthetic test scope | Change one input to another project/scope | `CROSS_SCOPE_DATASET` |
| Grand-total algebra | Full-window result recomputed from atomic inputs | Change grouping or bucket size | Conservation/independent-oracle agreement, never sum percentages |
| Deterministic replay | Identical facts, different input order | Permute observations | Same result SHA and values |
| Content/revision binding | One immutable source revision | Change value while keeping source identity | Different output receipt or deterministic rejection |
| Financial admission | Explicit reference flag only | Omit reference flag or request unreviewed method | Fail closed; no silent production S2 promotion |

For **nonlinear** models (NPV/XNPV/IRR/ES) add full-window re-execution and valuation basis validation; for **balances** add opening+movement=closing; for **ratios** add component alignment; for **weighted** outputs add weight/date/dimension correspondence. This does not license applying a SUM aggregation to every numeric variant.

## Real defects found and addressed

- **P0 — cross-business-universe ratio contamination:** RATIO_OF_SUMS previously accepted numerator from branch A and denominator from branch B when each series was individually complete. Fixed by validating exact atomic **(all dimensions, start, end)** identity of both component sets and rejecting duplicated component keys. Tests include valid cross-branch rollups as a positive oracle.
- **P0 — source overlap during partial coverage:** an interval operation with `require_full_coverage=False` previously skipped overlap detection and could count overlapping source facts twice. Now overlap is checked per leaf regardless of whether completeness is attested, while missing periods can still be marked partial.
- **P0 — disappearing leaf cohort:** a complete cross-branch monthly rollup could silently lose branch B or one cost centre in February while still reporting a plausible SUM or LAST_AS_OF. The complete-cohort guard checks stable leaf membership across all populated requested buckets for `SUM`, `RATIO_OF_SUMS` and `LAST_AS_OF` on eligible interval/snapshot metrics. Totally absent buckets retain their own explicit missing-source diagnostic.

**Business limitation:** stable cohort membership is intentionally strict for complete comparable series. Legitimate openings, closures and reorganizations need **a separately reviewed effective-dated cohort-change contract**. Until such a policy exists, silent source population changes are blocked, not guessed. EVENT_AT and RATE_FIXING streams are outside this fixed-cohort rule.

## Enforced files and CI

- Shared reusable testing helpers: [`tests/qualification_integrity_patterns.py`](../tests/qualification_integrity_patterns.py)
- Executable semantic integrity gate: [`tests/test_fengine_integrity_pattern_gate.py`](../tests/test_fengine_integrity_pattern_gate.py)
- Per-model variant requirement matrix: [`catalog/hc_reference_execution_inventory_r1.tsv`](../catalog/hc_reference_execution_inventory_r1.tsv)
- Other independent qualification coverage: [`tests/test_fengine_qualification_r1_temporal.py`](../tests/test_fengine_qualification_r1_temporal.py)
- The corrected source-of-truth TASE kernel: [`tase/reference.py`](../tase/reference.py)
- [GitHub Actions reference checks](../.github/workflows/reference-checks.yml) runs the mandatory integrity gate first, followed by the **entire** existing suite, both on Python 3.11 and 3.13.

To reproduce:

```bash
python -m unittest discover -s tests -p 'test_fengine_integrity_pattern_gate.py' -v
python -m unittest discover -s tests -v
```

The first step verifies compulsory registry coverage and runs adversarial cases; the second guarantees no regression in the existing model/temporal/golden tests. A new executable variant must update its independent model fixtures, explicit risk patterns and the inventory; otherwise this gate should fail or the variant must remain unqualified.

CI status alone does not imply that a GitHub branch-protection required-status check has been configured; repository settings must separately enforce that policy if desired.

## Boundaries

- No FIN integration, no real fact inputs, no operational Redis Runtime, no Rust.
- All synthetic inputs and reference results remain in-process. Future production Redis retention must remain **absolute <=10,800 seconds, never sliding, and atomically cleared after confirmed authenticated consumption ACK**.
- No general guarantee that externally supplied source SHA/content hash is a trusted FIN signature. No financial S2 approval, production valuation policy, KZT rounding qualification, or nonlinear method admission is implied.
- The manifest currently records required risk patterns and test file references; complete independent adversarial *per-variant* qualification is further work. A test passing with insufficient fixture scope must not be called "financially certified".
