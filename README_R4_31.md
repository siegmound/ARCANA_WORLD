# v0.6D1-R4.31

Run from the ARCANA WorldSim root:

```powershell
.\run_v0_6D1_R4_31.ps1
```

Expected outputs:

- `outputs/v0_6D1_R4_31/R4_31_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_REGISTRY.json`
- `outputs/v0_6D1_R4_31/R4_31_TARGET_AUTHORITY_CLOSURE_REGISTRY.json`
- `outputs/v0_6D1_R4_31/R4_31_SEMANTIC_REPAIR_AUTHORITY_CLOSURE.json`
- `outputs/v0_6D1_R4_31/authority/R4_31_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL.json`
- `outputs/v0_6D1_R4_31/R4_31_R432_EXECUTION_PLAN.json`
- `outputs/v0_6D1_R4_31/R4_31_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_31_SEAL/R4_31_FINAL_SEAL_AUDIT.json`

R4.31 does **not** run Geonomics or any other external engine. The only computational replay is an in-memory deterministic validation recomputation of the already-authorized R4.30 J14 algorithm; it produces no new spatial candidate and is used only to verify reproducibility before sealing the R4.30 candidate.
