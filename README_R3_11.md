# R3.11 — Post-CHA1 H0 Recovery & Adaptive-Radiation Restart

This stage restarts ordinary World-1 H0 biology from the exact R3.10 SEALED
checkpoint at 65.5 Ma and advances to 61.0 Ma (+5 Myr after CHA-1).

## Canonical local run

From PowerShell in the package root:

```powershell
.\run_v0_6D1_R3_11_postcha1_recovery.ps1
```

Expected workload:

```text
36 ordinary biology steps
65.5 -> 61.0 Ma
```

The runner prints the final verdict and writes:

```text
local_runs\v0_6D1_R3_11\R3_11_POST_CHA1_RECOVERY_SUMMARY.json
local_runs\v0_6D1_R3_11\WORLD1_H0_61Ma_POST_CHA1_5MY_RECOVERY_CHECKPOINT_v0_6D1_R3_11.json
local_runs\v0_6D1_R3_11\WORLD1_H0_61Ma_POST_CHA1_5MY_RECOVERY_CHECKPOINT_v0_6D1_R3_11.npz
```

## Optional smoke

```powershell
.\run_v0_6D1_R3_11_postcha1_recovery.ps1 -Smoke
```

This executes only 65.5→65.0 Ma (4 steps). A validated smoke is already included
in the candidate.

## Important governance

Do not:

- rerun CHA-1;
- use the historical D3.1 50-kyr solver as production authority;
- add a radiation/speciation multiplier;
- change mu, b, q ceiling, K semantics or speciation thresholds;
- select a branch based on desired richness.

The number of species at 61 Ma is an output.
