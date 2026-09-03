# R4.19
Run:

```powershell
.\run_v0_6D1_R4_19.ps1
```

Expected outputs:
- `outputs/v0_6D1_R4_19/R4_19_P2_ADAPTER_EXECUTION_PLAN.json`
- `outputs/v0_6D1_R4_19/R4_19_TARGET_DESIGN_BACKLOG_PLAN.json`
- `outputs/v0_6D1_R4_19/R4_19_R420_EXECUTION_AUTHORIZATION_PLAN.json`
- `outputs/v0_6D1_R4_19/R4_19_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_19_SEAL/R4_19_FINAL_SEAL_AUDIT.json`

No external engine is run in R4.19. The next authorized stage after a successful seal is R4.20 implementation/preflight, not engine reexecution.
