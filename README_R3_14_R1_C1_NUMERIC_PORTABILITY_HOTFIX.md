# R3.14-R1 C1 numeric portability hotfix

Overlay this hotfix on the existing R3.14 candidate directory after the Windows C1 orbital-reconstruction byte-equality failure.

Then run:

```powershell
.\verify_v0_6D1_R3_14_R1_hotfix.ps1
.\run_v0_6D1_R3_14_checks.ps1
.\run_v0_6D1_R3_14_late_cenozoic_binding.ps1
```

Expected checks after overlay: `22 passed`.

The hotfix does not change the v0.6.1 sealed payload hashes or any scientific parameter. It changes only the portability semantics of derived floating-point replay checks while keeping sealed 100-year anchors authoritative.
