# R4.14

Run from the ARCANA WorldSim root:

```powershell
.\run_v0_6D1_R4_14.ps1
```

No external engine is executed. The stage reads the SEALED R4.13 matrix, R4.3 mappings/runtime work, R4.1 authority matrix and frozen R4.2 registry, then emits a 71-cell evidence-gap census and a pre-result closure plan.

Expected outputs:

- `outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json`
- `outputs/v0_6D1_R4_14/R4_14_RETAINED_EVIDENCE_CAPABILITY_AUDIT.json`
- `outputs/v0_6D1_R4_14/R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json`
- `outputs/v0_6D1_R4_14/R4_14_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_14_SEAL/R4_14_FINAL_SEAL_AUDIT.json`

R4.14 never changes ARCANA canonical state, never authorizes replay/recalibration, never mutates the exact R4.2 23-job freeze and never promotes proxy-only evidence.
