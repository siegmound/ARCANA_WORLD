# ARCANA WorldSim v0.6D1-R3.7C

This candidate prepares the independent NEMO 2.4.2 directional-selection oracle required by the R3.7B gate.

Default full suite:
- 2 population sizes: 500, 2000
- 2 replicates
- 2 trait axes
- 2 selection variances: 1, 4
- 16 matched chains
- 5 NEMO runs per chain (one shared burn-in, selected/control fragmented phase, selected/control reconnection)
- 80 NEMO executions total

Run from Windows PowerShell with the already installed `arcana-nemo242` WSL environment:

```powershell
.\run_v0_6D1_R3_7C_nemo_selection_wsl.ps1 `
  -Replicates 2 `
  -PopulationSizes 500,2000 `
  -SelectionVariances 1,4 `
  -LociPerTrait 64 `
  -OptimumAmplitude 0.6 `
  -ParallelChains 4
```

Expected engine-completion status:

`NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED`

Then zip `local_runs/v0_6D1_R3_7C_SELECTION` and return it for evidence closure.
