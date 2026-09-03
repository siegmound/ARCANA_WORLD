# v0.6D1-R4.28

Target Selector & Design Authority Implementation Preflight + Geonomics J14 Spatial Replay Authority Preflight.

Run:

```powershell
.\run_v0_6D1_R4_28.ps1
```

This stage is read-only with respect to canonical state. It performs no external-engine run, no numeric target extraction, no canonical spatial replay, and no readjudication.

R4.28-R1 repairs the initial over-strong 44/44 selector-ready gate. Sources with no exact named selector inventory are explicitly deferred to R4.29 rather than treated as process failures or assigned invented selectors.
