# v0.6D1-R3.4 Status

**Verdict:** `PASS_ADMIXTURE_VARIANCE_HEADROOM_AND_SPECIES_BOUND_GENE_FLOW_CANDIDATE__LONG_210_TO_150_RERUN_PENDING`

## Closed
- Candidate normalized VA safety ceiling: **0.08**.
- `mu = 0.002 q/Myr`: unchanged.
- nonlinear homeostasis `b = 0.9876543209876544 / Myr / q`: unchanged.
- no-flow equilibrium `q*=0.045`: unchanged.
- Gene flow/contact/RI pair-state identity is **current species**, matching D3 dynamic-deme semantics.
- Root species remains immutable provenance/metadata authority.
- Frozen 150 Ma headroom audit: 0.08 and 0.10 give the same natural max `q=0.07435062666931849`; 0.08 has 0% reservoirs at >=99% of cap.
- Smoke 210→209 Ma: 120 species, 133 components, zero events.
- Full package tests: **96/96 PASS**.
- Formal R3.4 audit: **21/21 PASS**.

## Pending
The full 210→150 Ma Natural-Control replay must be rerun from the R1 common state. The old R3.3 endpoint is diagnostic evidence only and is not a continuation checkpoint.

## Package verification
- Full tests: **96/96 PASS**.
- Formal audit: **21/21 PASS**.
- Fresh extraction manifest verification: **PASS**.
- Fresh extraction tests: **96/96 PASS**.
- Fresh extraction formal audit: **21/21 PASS**.
