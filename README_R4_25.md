# R4.25 candidate overlay

Run from the ARCANA World root:

```powershell
.\run_v0_6D1_R4_25.ps1
```

Main outputs:
- `outputs/v0_6D1_R4_25/R4_25_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT.json`
- `outputs/v0_6D1_R4_25/R4_25_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY.json`
- `outputs/v0_6D1_R4_25/R4_25_R426_EXECUTION_PLAN.json`
- `outputs/v0_6D1_R4_25/R4_25_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_25_SEAL/R4_25_FINAL_SEAL_AUDIT.json`

This stage is read-only with respect to engines and canonical state. The J14 discovery branch is intentionally data-dependent: finding an existing SEALED exact-3 Ma spatial authority changes only the next plan; it does not authorize Geonomics execution in R4.25.
