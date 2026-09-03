# R3.19-R2 endpoint-support reconciliation repair

Apply this delta over the existing R3.19-R1 working tree after the fail-closed 0 ka endpoint-support diagnostic.

This repair does **not** relax the endpoint tolerance. It binds discrete support topology to the exact 0 ka provider state and uses the already-SEALED conservative support remap only when phase-aware transport leaves population on a cell closed at the endpoint.

Run:

```powershell
.\verify_v0_6D1_R3_19_R2_patch.ps1
.\run_v0_6D1_R3_19_checks.ps1
.\run_v0_6D1_R3_19_phase_aware_transport_closure.ps1
```

Expected checks: R3.19 13/13, inherited recent chain 55/55, total 68/68, formal audit 218/218.
