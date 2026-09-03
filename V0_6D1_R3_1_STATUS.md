# v0.6D1-R3.1 Status

**Status:** `PASS_VARIANCE_ORDER_AND_GENE_FLOW_REPAIR_CANDIDATE__210_TO_150_RERUN_REQUIRED`

## Closed

- exact D3.3A additive-variance source reused byte-for-byte;
- canonical operator order restored: pre-selection contact -> selection -> gene-flow moment mix -> Riccati homeostasis;
- D3 aggregate gene-flow exchange cap 0.45/deme restored;
- hard normalized q ceiling is again enforced by the final homeostasis operator;
- inherited R3 barrier-history/fission/speciation authorities unchanged;
- full package regression: 77/77 PASS;
- real 210→209 Ma repaired smoke: 120 species, 133 components, zero events, q_max ≈ 0.0219644.

## Rejected artifact

The previous R3 210→150 Ma output (137 species / 476 components / 343 fissions / 17 births) is **not a valid continuation checkpoint** because the repair changes upstream quantitative-genetic dynamics.

## Required next action

Rerun 210→150 Ma from the unchanged R1 210 Ma common state using this package. Then audit:

1. q <= 0.05 everywhere;
2. variance not ceiling-dominated;
3. fission identity/timing and component growth;
4. birth sensitivity, especially events near trait-distance threshold;
5. ordinary-extinction behavior;
6. population/A1 envelope.
