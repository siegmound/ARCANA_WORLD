# ARCANA World 1 — v0.6D1-R3.15

R3.15 couples the R3.14 SEALED C2 late-Cenozoic environmental provider to the existing R3.7I/R3.8 H0 biology runtime without changing biological cadence.

Canonical run: **30.0 Ma -> 0.25 Ma**, 238 x 125 kyr biology steps.

The endpoint is deliberately 250 ka because the next nominal biology step would cross the C2 200–120 ka replay-safe environmental bridge. R3.15 does not enter that bridge.

Run:

```powershell
.\verify_v0_6D1_R3_15_patch.ps1
.\run_v0_6D1_R3_15_checks.ps1
.\run_v0_6D1_R3_15_secular_biology.ps1 -Smoke
.\run_v0_6D1_R3_15_secular_biology.ps1
```

No richness target, no radiation multiplier, no Deep biological coupling, no biology-cadence change.
