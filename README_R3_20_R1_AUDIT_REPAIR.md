# R3.20-R1 Audit Repair

Apply over the existing R3.20 candidate after R3.19 SEALED.

This is an audit-only repair. CHA-2/C1 physics and the hydrological-hazard equations are unchanged.

Run on Windows PowerShell:

```powershell
.\verify_v0_6D1_R3_20_R1_audit_repair.ps1
.\run_v0_6D1_R3_20_checks.ps1
```

If the repaired magnitude audit passes, continue with:

```powershell
.\run_v0_6D1_R3_20_cha2_yd_hydrological_hazard.ps1
```

Do not recalibrate CHA-2 unless the repaired live physical gates still fail.
