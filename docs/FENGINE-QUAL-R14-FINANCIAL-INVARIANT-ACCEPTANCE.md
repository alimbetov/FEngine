# FEngine QUAL-R1.4 — Financial invariants, source-pool isolation, and ledger conservation

**Branch:** main. **Mode:** Python 3.11/3.13 reference arithmetic on synthetic, seeded fixtures only. **FIN:** disconnected. **Redis Runtime:** deferred. **Rust:** not started. **Financial S2:** CLOSED.

## Why this phase was required

QUAL-R1.2 furnished at least one independently derived expected result and an exact domain-denial test for **each of the 48 executable variants across 27 implemented HC model codes**. QUAL-R1.3 then added 1,348 bounded synthetic rate, ECL, risk and TASE temporal scenario executions. QUAL-R1.4 tests **financial conservation** and **typed source-pool isolation**, not merely output SHA mutation.

## 1,560 additional independent generated scenarios

| Family | Generated scenarios | Independent statement checked |
|---|---:|---|
| PVM three factors, 96 new three-SKU source sets × 3 variants | **288** | Baseline cost, actual cost, exact price/mix/volume bridge, permutation invariance, three factors sum to actual-minus-baseline |
| FIFO, moving WAC and periodic WAC, 80 unique lots × 3 variants | **240** | Original purchase spend = COGS + remaining inventory; remaining quantity and per-method cost independently derived; replay event order independence |
| Asset amortization, 72 independent schedules × 5 variants | **360** | Original asset cost = cumulative depreciation + residual; per-period closing rollforward; independent SYD, straight-line, declining, DDB and units-of-production reference |
| WACC, 120 independent capital scenarios × 2 reviewed variants | **240** | Exact after-tax weighted capital cost; proportional capital scaling invariance; nonincreasing WACC when tax increases with nonnegative debt cost |
| Posted vs reclassified direct CFO, 72 synthetic ledgers × 2 variants | **144** | Class cash conservation and all-postings closing balance; internal transfer exclusion; explicit documented reclassification |
| Indirect CFO, FCFF and both FCFE variants, 72 sets × 4 variants | **288** | Cash from NI+noncash−ΔNWC, EBIT after tax, capex and debt cashflows, discounted FCFE and two-method agreement |
| **Total generated scenario executions** | **1,560** | **Nine** model codes, **19** distinct variant codes |

The new tests also run **targeted negative controls** for cross-period source SHA swaps, noncanonical SKU/currency use, nonmatching PVM cost-vintage and volume-baseline digests, unbalanced or forged posted cash closing balances, reclassification integrity and mismatched FCFE reconciliations.

These are **1,560 generated case executions, not 1,560 Python unittest methods**, not exhaustive proof and not additional implemented catalog models.

## P0/P1 defects found by adversarial qualification

**Confirmed defect 1: Duplicate event IDs across different stock dates.**

- Previously stock replay rejected duplicate **(date, event_id)** pairs only. The same source posting replayed on a different date was therefore accepted again and could inflate purchased quantity or issue cost.
- A negative case (same source event ID on two days) was observed failing on **all three** inventory variants before the fix.
- Corrected `fengine_hc/reference.py` to enforce uniqueness of **event_id across the entire synthetic cost-pool replay**. The same exact `DUPLICATE_STOCK_EVENT_ID` refusal now applies to FIFO, moving WAC and periodic WAC.

**Confirmed defect 2: Stock events silently ignored untyped foreign business dimensions.**

- Before correction, the parser extracted only date, ID, quantity and positive purchase unit cost. An extra `sku`, `currency`, `location`, or an unauthorized sale `unitCost` was **ignored**. This permitted a plausible COGS calculation from a mixed-identity feed rather than a fail-closed refusal.
- The reference currently supports **one externally identified cost pool only**; it cannot independently group multiple SKU/currency/location populations.
- The event parser now enforces an exact typed schema: purchase `{date,id,quantity,unitCost}`, issue `{date,id,quantity}`. Unsupported attributes or missing purchase cost yield `STOCK_EVENT_SCHEMA`. A supplied issue price cannot override the selected FIFO/WAC method.
- **Limitation:** a source actor removing SKU labels before ingestion cannot be detected by this mathematical model. Authenticated external single-pool provenance and a future typed multi-SKU source contract are separate unimplemented admission work, not implied by input SHA.

The 116-model catalogue remains non-executable except for the 27 previously inventoried mathematical implementations, and the 18 reviewed temporal output bindings remain separate.

## Files and mandatory CI

- [PVM and inventory property vectors](../tests/test_fengine_qual_r14_pvm_stock_properties.py)
- [Depreciation and capital structure oracles](../tests/test_fengine_qual_r14_asset_wacc_properties.py)
- [Posted/indirect CFO, FCFF and both FCFE variants](../tests/test_fengine_qual_r14_cashflow_properties.py)
- [Patched stock reference input and global event-ID invariant](../fengine_hc/reference.py)
- [Mandatory Python 3.11/3.13 quality gate](../.github/workflows/reference-checks.yml)

~~~bash
python -m unittest discover -s tests -p 'test_fengine_qual_r14_pvm_stock_properties.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r14_asset_wacc_properties.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r14_cashflow_properties.py' -v
python -m unittest discover -s tests -v
~~~

The three independent R1.4 test steps execute **before** the complete regression, alongside previous R1–R1.3 gates. Verify the exact final `main` HEAD in **both** reference-check and methodology-bank GitHub Actions, not a previous green revision.

## Remaining uncertainty and qualification barriers

- Existing WACC inputs contain no authenticated currency, company, period, valuation basis or common revision contract. A mathematically correct weighted mean cannot prove that two capital values came from the same valuation context.
- Indirect CFO/FCFF use a syntactically valid `sourceRevisionSha256` but this does not independently certify the externally supplied financial data. The FCFE method-reconciliation function compares compatible currency/date/rate/period and output values; it does not prove common signed upstream source lineage between two method-specific revisions.
- PVM evidence hashes prove self-consistency of **provided** baseline/actual rows; not external source authorization, genuine industry standard costs, or reviewed change of SKU universe.
- No per-currency rounding policy, tax eligibility opinion, accounting standard S2 or financially approved multi-SKU inventory scope is asserted.
- No real `user_id/project_id` FIN facts, Redis TTL/ACK implementation or Rust parity work. The deferred Redis rule remains **absolute TTL ≤ 10,800 seconds**, and an authenticated consumer ACK must trigger atomic session deletion.
