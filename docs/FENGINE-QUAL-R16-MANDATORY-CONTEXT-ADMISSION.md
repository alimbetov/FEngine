# FEngine QUAL-R1.6 — Mandatory context admission (synthetic reference)

**Branch:** main. **FIN:** DISCONNECTED. **Rust/Redis Runtime:** NOT IMPLEMENTED. **Financial S2:** CLOSED.

## Contract

`QualifiedReferenceEngine.calculate(..., sources=..., payloads_by_role=..., reference_mode=True)` is the new **strict reference execution facade**. It fails closed before evaluating any numeric inputs if source admission is absent or incompatible. `ReferenceEngine.calculate` remains a legacy research-only entry point to preserve previous scientific golden tests, and **is not** an admitted/qualified computation API. No claim is made that Python process callers are technically prevented from directly importing the legacy class.

Explicit `POLICIES` contains the **27 existing executable HC model codes**. For 26 of these codes the present provisional input policy is `INPUT` (one payload exactly equal to the numerical input dictionary, with the model ID, scope, currency, period and immutable SHA bound). The stock models additionally require a **single SKU cost pool**; they cannot combine SKU identifiers. This provisional policy is not a claim of financially approved atomic per-component lineage. Every new model or multi-role contract must be explicitly reviewed and added to the allowlist; no default/fallback.

## PVM: BASELINE → ACTUAL

`HC.COST.08` has a dedicated `BASELINE` and `ACTUAL` source contract. Both source context envelopes must share user ID, project ID, currency, SKU universe, period granularity and complete methodology ID/version/SHA. The baseline source's closing date **must be strictly before** the actual source's opening date. This allows distinct non-overlapping periods; unlike R1.5 the periods are not required to be identical.

Each role must present a source-bound, digest-checked `{"rows": [{"sku", "quantity", "unitCost"}, ...]}` payload. The complete calculation rows are independently reconstructed from the two payloads, checked against the submitted inputs, and their baseline/actual revision digests and standard-cost/volume digests recomputed. Neither reversing roles nor changing a quantity/cost while keeping the original digest is allowed.

PVM numeric vectors and their allocation convention remain defined by R0.7; admission does **not** alter mathematical formulas or S2 status. Currency conversion, implicit period resampling, mergers of SKU populations and methodology migration are not supported.

## Failure semantics

- Missing context: `CONTEXT_ADMISSION_REQUIRED`
- Unknown policy: `CONTEXT_POLICY_NOT_APPROVED`
- Mixed scope/currency/period/SKU/methodology: `CROSS_SCOPE_DATASET`, `CROSS_CURRENCY_DATASET`, `CROSS_PERIOD_DATASET`, `CROSS_SKU_DATASET`, `CROSS_METHODOLOGY_DATASET`
- PVM date inversion/overlap: `PVM_PERIOD_ORDER_MISMATCH`
- PVM rows inconsistent with role payloads: `PVM_SOURCE_INPUT_MISMATCH`
- Role payload tampering: `SOURCE_PAYLOAD_DIGEST_MISMATCH`
- Single-SKU violation: `MULTI_SKU_POOL_UNSUPPORTED`
- Generic unapproved model or mismatched numerical inputs: `CONTEXT_POLICY_NOT_APPROVED`, `SOURCE_INPUT_MISMATCH`

Admission yields a separate deterministic `admission_sha256`, plus the original immutable calculation result. **The legacy numerical `output_sha256` does not incorporate admission context.** Callers needing full audit identity must use both values; a future release may bind them in one immutable execution receipt.

## Test commands

```bash
python -m unittest discover -s tests -p 'test_fengine_qual_r16_mandatory_admission.py' -v
python -m unittest discover -s tests -v
```

New cases: 450 seeded PVM context mismatches plus explicit positive PVM/WACC, fail-closed/missing-context, unauthorized multi-SKU inventory, role, schema, source corruption, input binding and metadata tests. CI executes this stage on Python 3.11 and 3.13.

## Next boundary

For QUAL-R1.7, independently test multi-model chains carrying `admission_sha256` and immutable typed outputs, as well as true role-specific source alignment for CAP/ECL/CASH/DCF. Require full model-family policies and prohibit legacy direct calculation in all new production-oriented entry points. Real FIN intake, signed source provenance, external authorization, Redis runtime/ACK, Rust parity and financial S2 remain outside this phase.
