# ARCANA WorldSim v0.6D1-R3.23

Large integrated functional-phenotype stage. This package intentionally replaces several micro-stages with one run:

`comparative calibration → ancestral prior ensemble → phylogenetic replay → present component conditioning → derived capabilities → audit`

## Run

Extract as an overlay on the current WorldSim root, then run only:

```powershell
.\run_v0_6D1_R3_23.ps1
```

The script runs the R3.23 regression tests and then the full local ensemble materialization.

Default ensemble: 3 rate regimes × 32 replicates = 96 histories.

Expected output directory:

`outputs\v0_6D1_R3_23`

No separate R3.23A/B/C/D versions are created. If the resulting local evidence is clean, R3.23 receives one final seal.
