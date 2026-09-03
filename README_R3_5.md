# ARCANA World 1 — v0.6D1-R3.5

**Time-Resolved VA Headroom Instrumentation & Dynamic Ceiling Sensitivity**

R3.5 is an instrumentation/sensitivity runpack built on R3.4. It does not replace the scientific runtime. Its purpose is to observe normalized additive-variance headroom every 125 kyr and compare matched q-ceiling 0.08 vs 0.10 histories from 210 to 150 Ma.

## Important
This package does **not** yet authorize 150 Ma. The full paired long replay must be executed locally.

## Recommended command

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_v0_6D1_R3_5_sensitivity_windows.ps1 -EndAgeMa 150 -Threads 12
```

See:
- `TIME_RESOLVED_VA_HEADROOM_CONTRACT_v0_6D1_R3_5.md`
- `DYNAMIC_CEILING_SENSITIVITY_PROTOCOL_v0_6D1_R3_5.md`
- `V0_6D1_R3_5_STATUS.md`
- `NEXT_STAGE_HANDOFF_v0_6D1_R3_5.md`
