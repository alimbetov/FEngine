# FEngine QUAL-R1.2 — Independent Mathematical Verification & Negative Testing

**Implementation:** 2026-11-20, branch main, synthetic Python/Decimal reference mode. **No financial S2**, FIN integration, Redis runtime or Rust implementation.

## Goal and evidence

The prior QUAL-R1.1 gate proved 48 named HC model variants executed and rejected generic configuration, SHA and type tampering. That did **not** prove that the actual numeric values were correct. This new gate adds explicit *independent* mathematical answers for all **48/48** executable variants across **27/116** model codes, plus a deliberately invalid **domain-specific case per variant**. The 222 registered candidates are not treated as executable or financially approved.

| Evidence type | Artifact | Exact scope |
|---|---|---|
| 48 typed synthetic inputs and hand-authored mathematical expected outputs | [qualification_r12_goldens.py](../tests/qualification_r12_goldens.py) | 48 model+variant cases, each with formula explanation and Decimal comparison tolerance |
| Executable independent numerical assertions | [test_fengine_qual_r12_independent_math.py](../tests/test_fengine_qual_r12_independent_math.py) | **Every** inventoried variant must have a matching golden and the output must equal the manually expected numeric field(s) |
| Domain-meaningful exact rejection case per variant | [test_fengine_qual_r12_domain_denials.py](../tests/test_fengine_qual_r12_domain_denials.py) | 48 carefully selected invalid cases, asserting exact CalculationError.code, not vague exception |
| Model-to-evidence exact join and reference status | [hc_reference_execution_inventory_r1.tsv](../catalog/hc_reference_execution_inventory_r1.tsv) | The required two evidence path columns and qualification state explicitly refuse production S2 |
| Mandatory CI, Python 3.11 and Python 3.13 | [reference-checks.yml](../.github/workflows/reference-checks.yml) | Shared-source gate → 48-variant real executor gate → QUAL-R1.2 numeric → QUAL-R1.2 domain denial → isolated decimal goldens → full reference regression |

### Numerical oracle principle

Expected outputs are **not obtained by calling FEngine, reusing its output hash, or simply checking that a value changes when its SHA changes**. The reference values are explicit, separately authored decimal numbers plus their mathematical derivations. For signed-source contracts (Direct CFO, FCFE and PVM), fixture builders may construct correctly pinned source revision SHA-256 values; they **do not** generate the independent expected answers.

The independent vector table explicitly checks the output *meaning* of each variant: depreciation methods, CAPM/WACC, runway, direct/indirect CFO, single/product-mix break-even, cost escalation, both EVM EAC forecasts, three PVM factors, period-end/midperiod NPV, dated XNPV, multi/unique IRR, FCFF, both FCFE methods, Gordon terminal valuation, EV-to-equity bridge, 12-month/lifetime ECL, four dated loans, EIR, LLCR/PLCR, VaR/Expected Shortfall, settlement ageing and FIFO/moving/periodic WAC.

Examples that would **fail if mathematical implementation were replaced by a plausible wrong formula**:

| Variant | Source | Independent expected |
|---|---|---|
| CAPM_BASE | rf=4%, β=1.2, market premium=6% | **11.2%**, not sum of three parameters |
| MARKET_VALUE_WACC | Equity=60, debt=40, Ke=12%, Kd=8%, tax=25% | **9.6%** |
| EVM_BAC_CPI | EV=60, AC=75, BAC=120 | CPI **0.8**; EAC **150** |
| EVM_EAC_FORECAST | Same source but different forecast formula | CPI **0.8**; EAC **135** |
| PRICE_VARIANCE | Fixed baseline costs, two SKUs | **−70**; total three-factor change **+230** |
| QUANTITY_VARIANCE | Same source | **+140** |
| MIX_VARIANCE | Same source | **+160** |
| FCFE_LEVERED | CFO=110, capex=50, drawn debt=40, repayment=15 | **85** |
| EXACT_DATE_XNPV | −100 initially, +121 exactly 365 days later, 10% annual | **10** |
| ALL_REAL_IRR_ROOTS | −100, +230, −132 periodic | Both real roots **10% and 20%** |
| QUANTILE_INTEGRAL_ES | losses 1,2,3,4,5; alpha=.7 | **14/3** |
| FIFO_LOT_REPLAY | Purchases 10@10 and 10@20, issue 12 | COGS **140**, inventory **160** |
| MOVING_WAC / PERIODIC_WAC | Same purchase/issue events | COGS **180**, inventory **120** |

### Independent metamorphic checks

Beyond the 48 numerical vectors, R1.2 checks named economic relations: changing CAPM β by +0.3 must increase Ke by exactly **1.8 percentage points** at a 6% premium; changing the initial undiscounted NPV cashflow by +100 must raise either NPV convention by exactly +100; the depreciation balance must reconcile to the acquisition cost; PVM's price+mix+volume must equal final actual cost less baseline cost; negative working-capital changes must release FCFF; ambiguous single-IRR must not guess a root; reconciling CFO cannot silently accept inconsistent direct CFO; and every loan schedule must conserve original principal/payment components. These are **test data transformations with financially specified results**, not hash-only probes.

### Domain-specific fail-closed cases

The domain-denial table blocks, among others: residual value above asset cost, zero total capital weights, duplicated cashflow dates/scenario IDs, stale direct-CFO source digest, false direct/indirect CFO reconciliation, nonpositive contribution margin, invalid growth/escalation rate, zero EVM cost denominator, PVM cost vintage/source mutation, incompatible NPV rate/daycount, nonexistent or ambiguous IRR roots, invalid FCFF tax, FCFE cash-source tampering, Gordon growth equal to WACC, mismatched equity valuation cutoff, out-of-range conditional PD, reversed loan dates, nonconventional EIR cashflow signs, debt life beyond project length, illegal VaR/ES alpha, overlapping aging ranges and stock issue beyond on-hand inventory.

The precise code is asserted. A test that merely raises *some* exception is not accepted.

### Replay commands

~~~bash
python -m unittest discover -s tests -p 'test_fengine_integrity_pattern_gate.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r11_per_variant_adversarial.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r12_independent_math.py' -v
python -m unittest discover -s tests -p 'test_fengine_qual_r12_domain_denials.py' -v
python -m unittest discover -s tests -v
~~~

The **final GitHub Actions SHA** must pass both Python versions and the R95/R1 methodology bank before claiming the R1.2 reference milestone complete.

## Explicit limitations

- **48 bounded synthetic cases ≠ exhaustive mathematics**, full property-based testing, legal/regulatory approval, a methodology-specific S2 adjudication, or stable behavior over every possible parameter and date. Some minimal examples (notably zero-interest dated loans) prove only one well-defined case; existing positive-rate reference tests supplement but do not remove the need for more independent nonzero-rate dated goldens.
- PVM and other SHA-bound inputs use existing pinned-fixture helpers solely for provenance construction. A cryptographic hash by itself does not prove a trusted FIN source.
- Precision policy remains Decimal and test-specific explicit tolerances. Per-currency legal rounding, source provenance, equity valuation methods, actuarial reporting and production source completeness are **not** independently approved.
- **FIN is disconnected** and receives no modifications. **Redis Runtime is not implemented**: the architectural obligation remains an absolute TTL no longer than 10,800 seconds and atomic deletion after an authenticated successful ACK. **Rust is deferred.**
- Next mathematical qualification wave: stronger nonzero-rate dated-loan vectors, randomized bounded metamorphic/property tests using independently specified invariants, per-method model-specific error lineage and validation of cross-dimensional/temporal reaggregation at source boundaries. Financial S2 remains closed.
