# R3.7H
Closed-loop segregation-aware production-binding candidate.

Run a quick diagnostic:
```powershell
.\run_v0_6D1_R3_7H_smoke.ps1
```

Run the governed 210→150 three-branch validation:
```powershell
.\run_v0_6D1_R3_7H_closed_loop_validation.ps1
```

The PowerShell runner launches LOW/CENTER/HIGH as separate Python processes so each branch owns an independent full World-1 state and can use the available local CPU cores. Production promotion remains review-required after the run.
