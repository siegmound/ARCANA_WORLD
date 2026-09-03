# R3.20 — CHA-2 Younger-Dryas-Class Audit & Hydrological Hazard Layer

Parent: **R3.19 SEALED H0 Natural Control at 0 ka**.

Current audit revision: **R1_METRIC_AND_PARENT_SCHEMA_REPAIR**.

Run order on Windows PowerShell:

```powershell
.\verify_v0_6D1_R3_20_R1_audit_repair.ps1
.\run_v0_6D1_R3_20_checks.ps1
.\run_v0_6D1_R3_20_cha2_yd_hydrological_hazard.ps1
```

R1 changes only audit semantics and parent-schema parsing. `cha2_nested_50y.py`, CHA-2 physics and the hazard equations remain unchanged.

If the repaired magnitude audit fails, do not tune the hazard layer or human outcomes. Fail closed and inspect the remaining physical gate(s).
