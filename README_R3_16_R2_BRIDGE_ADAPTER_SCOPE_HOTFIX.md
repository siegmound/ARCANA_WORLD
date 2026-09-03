# ARCANA World1 v0.6D1-R3.16-R2 bridge adapter scope hotfix

Overlay this ZIP on the existing R3.16-R1 candidate tree.

This repair fixes only an R3.16 environment-adapter scope mismatch. It does not change scientific parameters or biology.

After overlay:

```powershell
.\verify_v0_6D1_R3_16_R2_hotfix.ps1
.\run_v0_6D1_R3_16_checks.ps1
.\run_v0_6D1_R3_16_c2_bridge_fixed_biology.ps1
```

Expected focused regression after the overlay:
- R3.16: 10 passed
- R3.15: 12 passed
- R3.14: 13 passed
- formal audit: 314/314 PASS
