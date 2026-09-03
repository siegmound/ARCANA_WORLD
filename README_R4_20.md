# R4.20

## R4.20-R1 Windows regression-runtime repair

The first Windows attempt stopped in pytest fixture setup with `WinError 5` while pytest tried to enumerate its default user temp root. R4.20-R1 routes pytest scratch state to the project-local directory:

`outputs\\v0_6D1_R4_20\\pytest_tmp`

This changes no R4.20 scientific logic, P2 scope, target-repair semantics, frozen evidence, or authorization state.

Run:

```powershell
.\run_v0_6D1_R4_20.ps1
```

Expected outputs:
- `outputs/v0_6D1_R4_20/R4_20_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT.json`
- `outputs/v0_6D1_R4_20/R4_20_TARGET_DESIGN_PROTOCOL_REPAIR.json`
- `outputs/v0_6D1_R4_20/R4_20_R421_STATIC_VALIDATION_AND_REEXECUTION_AUTHORIZATION_PLAN.json`
- `outputs/v0_6D1_R4_20/R4_20_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_20_SEAL/R4_20_FINAL_SEAL_AUDIT.json`

No external engine is executed in R4.20. Successful completion routes to R4.21 static validation of the new-namespace adapter implementation and a separate symmetric-reexecution authorization gate.
