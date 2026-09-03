# ARCANA WorldSim v0.6D1-R4.10

Purpose: close the R4.9 uncertainty branch without endless replicate escalation. R4.10 audits precision and alternate evidence, and performs a source/output-integrity audit of CDMetaPOP population metrics.

Expected finding on the current R4.3–R4.9 source line:
`R43_R49_CDMETAPOP_POPULATION_METRIC_FILENAME_SELECTOR_COLLISION_CONFIRMED`.

This stage is intentionally fast: it does not launch WSL engines.

Run:
```powershell
.\run_v0_6D1_R4_10.ps1
```

Expected next action after a successful seal:
`BUILD_R411_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION`.
