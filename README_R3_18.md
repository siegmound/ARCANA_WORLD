# R3.18

**Stage:** `v0.6D1-R3.18 — Recent H0 Exposure Completion & Transport-Phase Readiness`

Parent: R3.17 SEALED 120 ka environmental restart / 125 ka biology state.

Run order:

```powershell
.\verify_v0_6D1_R3_18_patch.ps1
.\run_v0_6D1_R3_18_checks.ps1
.\run_v0_6D1_R3_18_recent_exposure_transport_readiness.ps1
```

R3.18 does not advance biology. It completes the 125 ka -> 0 environmental forcing integral and separates the two 62.5-kyr transport phases. The resulting diagnostics determine the exact operator required in R3.19.
