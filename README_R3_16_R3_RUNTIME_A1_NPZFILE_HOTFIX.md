# R3.16-R3 Runtime A1 NpzFile Hotfix

This overlay fixes the canonical R3.16 runtime binding only. R3.14 reconstructs A1 as a provider-oriented dict, while sealed R3.8 inspects `a1.files`. R3.16 now reopens the same sealed `FULL_A1_REFERENCE_210_0Ma.npz` as an `NpzFile` for the R3.8 runtime call.

No scientific arrays, equations, biology parameters, cadence, C2 provider equations, or parent authority are changed.

After overlay:

```powershell
.\verify_v0_6D1_R3_16_R3_hotfix.ps1
.\run_v0_6D1_R3_16_checks.ps1
.\run_v0_6D1_R3_16_c2_bridge_fixed_biology.ps1
```

Expected focused regression: 11 + 12 + 13 = 36/36 PASS.
Expected formal audit: 318/318 PASS.
