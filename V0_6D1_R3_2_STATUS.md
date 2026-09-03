# v0.6D1-R3.2 Status

**Verdict:** `PASS_BARRIER_COUPLED_TRANSPORT_GENE_FLOW_AND_VARIANCE_CLOSURE_CANDIDATE__LONG_210_150_RERUN_PENDING`

R3.2 closes the architectural mismatch found in R3.1 by reusing the same D3.2B permeability authority for migration, gene-flow/contact, and vicariance/fission. The D3.3A variance ordering/cap repair from R3.1 remains active.

Validated short history:
- 210→206 Ma: 120 species, 148 components, 15 fissions, 0 speciation, 0 ordinary extinction;
- 210→205 Ma: 120 species, 151 components, 18 fissions, 0 speciation, 0 ordinary extinction;
- qmax at 205 Ma ~0.01575; 0 reservoirs ≥0.0495;
- gene-flow first/second moment closure ~2.18e-11 / 2.33e-10.

R3.1 210→150 Ma remains diagnostic only. R3.2 must rerun 210→150 Ma from the common R1 210 Ma state before 150 Ma can become a continuation checkpoint.

## Verification closure
- included pytest suite: **83/83 PASS**;
- R3.2 formal audit: **31/31 PASS**;
- short validation outputs and state files are included in `outputs/v0_6D1_R3_2/`.
