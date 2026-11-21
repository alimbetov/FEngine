# FEngine QUAL-R1.5 — Synthetic financial-context compatibility

**Branch:** main. **Scope:** Python reference admission gate, synthetic fixtures only. **FIN:** not connected. **Redis Runtime/Rust:** deferred. **S2:** CLOSED.

## Decision

Reject mixed financial source contexts **before calculation**, even if the mathematical engine could return a plausible number. No implicit currency translation, report-period resampling, SKU merge, methodology upgrade, or inconsistent revision fallback.

The synthetic source envelope binds `source_id`, unique `role`, `user_id`, `project_id`, ISO currency, exact inclusive `period_start/end`, `period_type`, canonical sorted SKU tuple, `methodology_id/version/sha256`, and SHA-256 of the exact role payload. The same user and project are mandatory for every role.

## Exact refusal classes

| Conflict | Error |
|---|---|
| Different scope (user/project) | `CROSS_SCOPE_DATASET` |
| Different currency | `CROSS_CURRENCY_DATASET` |
| Different exact period or period type | `CROSS_PERIOD_DATASET` |
| Different canonical SKU sets | `CROSS_SKU_DATASET` |
| Different methodology ID/version/SHA | `CROSS_METHODOLOGY_DATASET` |
| Invalid/noncanonical SKU | `NONCANONICAL_SKU_CONTEXT` |
| Multiple SKU in single-pool model | `MULTI_SKU_POOL_UNSUPPORTED` |
| Duplicate/missing source roles | `SOURCE_ROLE_MISMATCH` |
| Duplicate source ID | `DUPLICATE_SOURCE_ID` |
| Payload altered after digest assignment | `SOURCE_PAYLOAD_DIGEST_MISMATCH` |

Malformed currency, calendar, methodology SHA and role structure have separate stable schema errors. Ordering sources does not change the receipt. Changing any source/methodology version must change the receipt. No executor invocation is permitted when a context or payload check fails.

## Implemented reference surface

- `fengine_hc/source_context_r15.py`: `validate_contexts`, `execute_guarded`; pure synthetic Python gate, not a FIN integration layer.
- `tests/test_fengine_qual_r15_source_context.py`: 800 seeded single-axis incompatible cases plus scope, calendar, role, revision, digest, canonicality and positive controls.
- Test invocation: `python -m unittest discover -s tests -p 'test_fengine_qual_r15_source_context.py' -v`.

## Known limits / next qualification

- This is a **reference gate**, not yet mandatory for every `ReferenceEngine.calculate` entry point. Direct callers can bypass it. Before production architecture it must be a non-bypassable admission boundary with executable per-model source role/pool policies.
- SHA proves local bytes bind to the supplied synthetic envelope, **not** authorization, external lineage, cryptographic provenance, or financial approval. Malicious actors who replace both payload and its hash are outside this phase.
- Different periods, currencies, methodology versions or SKU universes are rejected even when a legitimate business conversion might exist. These require explicit reviewed policies and independent oracles, never silent coercion.
- No genuine FIN user/project identifiers or facts are read. Redis TTL/ACK and Rust parity remain unimplemented. Financial S2 remains closed.
