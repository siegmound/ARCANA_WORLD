# R3.19-R1 Windows/local canonical runner hotfix

Overlay this patch on top of the already verified R3.19 candidate.

Run:

```powershell
.\verify_v0_6D1_R3_19_R1_hotfix.ps1
.\run_v0_6D1_R3_19_checks.ps1
.\run_v0_6D1_R3_19_phase_aware_transport_closure.ps1
```

Expected updated candidate checks:

- R3.19: 11 passed
- R3.18: 10 passed
- R3.17: 9 passed
- R3.16: 11 passed
- R3.15: 12 passed
- R3.14: 13 passed
- formal audit: 209/209

The hotfix changes no science or cadence. It only repairs a stale q-ceiling config attribute name in the canonical runner.
