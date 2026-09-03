# R4.13 candidate

Purpose: apply the R4.12-authorized comparability downgrade for CDMetaPOP absolute population response and readjudicate the existing 75-cell matrix without new simulations.

Run from the WorldSim root:

```powershell
.\run_v0_6D1_R4_13.ps1
```

Main outputs:
- `outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json`
- `outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json`
- `outputs/v0_6D1_R4_13/R4_13_READJUDICATION_DELTA.json`
- `outputs/v0_6D1_R4_13/R4_13_EXECUTION_SUMMARY.json`
- `outputs/v0_6D1_R4_13/R4_13_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_13_SEAL/R4_13_FINAL_SEAL_AUDIT.json`

R4.13 never rewrites R4.11 or the frozen R4.3 unit mapping.
