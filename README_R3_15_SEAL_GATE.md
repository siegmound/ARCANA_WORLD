# R3.15 local seal gate

Apply this patch over the current R3.15 canonical-run tree.

Run:

```powershell
.\verify_v0_6D1_R3_15_seal_gate_patch.ps1
.\run_v0_6D1_R3_15_sealed_checks.ps1
```

The sealed checks run the focused R3.15/R3.14/R3.13 regression with local pytest basetemp, then independently audit the canonical 250 ka checkpoint and revalidate the actual materialized R3.14 C1->C2/B1/B2/v0.6.1 authority.

No scientific runtime or parameter is changed by this seal gate.
