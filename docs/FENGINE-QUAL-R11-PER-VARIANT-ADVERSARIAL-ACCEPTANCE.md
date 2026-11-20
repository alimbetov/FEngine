# FEngine QUAL-R1.1 — executable per-variant adversarial evidence

**Branch:** `main` · **Mode:** synthetic, Python 3.11/3.13, reference-only · **Financial S2:** closed.

## Problem corrected

The QUAL-R1 catalogue previously relied on a model variant's **name appearing in an existing test file**. This is weaker than execution evidence: a variant mentioned in a negative test can appear covered even though it never completes a successful calculation. The new acceptance mechanism verifies actual successful invocations.

Initial qualification run captured successful calculations for **47/48** declared variants. The missing case was `HC.DCF.03 / SINGLE_IF_UNAMBIGUOUS`: its previous tests rejected multiple IRR roots, but did not execute that variant successfully. A model-specific positive golden was added: `[-100, 110]` gives a unique IRR near `0.10`, and `[-100,121]` gives `0.21`. The mutation must produce a different immutable input and result fingerprint.

## Permanent model qualification pattern

`tests/test_fengine_qual_r11_per_variant_adversarial.py` executes the **seven existing independent HC model reference suites** under an instrumented `ReferenceEngine.calculate` call boundary. Only **real successful**, reference-mode calculations are admitted as evidence. It compares the observed exact set of `(modelCode, variantCode)` with the versioned inventory, failing for **either missing declared executions or undeclared new successful variants**.

For each captured real model sample, the gate independently performs:

| Pattern | Required evidence |
|---|---|
| Positive, real math invocation | A successful existing model calculation, not string matching |
| Deterministic replay | Same immutable output/input/config SHA after an independent replay |
| Financial admission | `FINANCIAL_S2_REQUIRED` when explicit reference mode is omitted |
| Unexpected configuration | Typed `UNKNOWN_PARAMETER` refusal |
| Unexpected input | Typed refusal rather than silent consumption or ignoring |
| Known numeric source mutation | Fail closed, or produce new input SHA **and** new result SHA |
| Binary-float injection | Exact `BINARY_FLOAT_FORBIDDEN` refusal |
| Immutable fixture handling | Deep-copy accepted nested mapping/sequence structures without mutating original fixtures |

The established `tests/test_fengine_integrity_pattern_gate.py` additionally checks actual cross-dimension ratio sources, cohort loss, partial overlap, weight pairing and month/day grand totals. **Both tests are explicit mandatory GitHub Actions steps before the full suite**.

## Reproduction and required gate

```bash
python -m unittest discover -s tests -p 'test_fengine_integrity_pattern_gate.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r11_per_variant_adversarial.py' -v
python -m unittest discover -s tests -v
```

GitHub Actions: `.github/workflows/reference-checks.yml`, Python 3.11 and Python 3.13. The actual final SHA and run logs, not an earlier commit, decide acceptance.

## Boundaries and future work

This is stronger evidence of **executable per-variant contract integrity** but is **not** independent financial methodology qualification. Specifically, comparing fingerprints after a numeric mutation establishes binding of a change to a different result identity; it does **not** prove that the **numeric output changed in the financially correct way**. Independent per-variant mathematical goldens, multiple parameter boundaries, model-specific domain metamorphic relations and negative provenance cases must still be added and tracked for financial S2. A successful run of the model test suites does not prove FIN source trust.

No FIN integration, Redis Runtime or Rust. The future ephemeral runtime rule remains Redis absolute TTL ≤ 10,800 seconds and atomic purge after authenticated durable consumer ACK. Customer data must not be persisted in FEngine.
