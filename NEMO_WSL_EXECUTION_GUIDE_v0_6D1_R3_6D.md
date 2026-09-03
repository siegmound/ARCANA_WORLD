# NEMO 2.4.2 WSL execution guide — v0.6D1-R3.6D

## 1. Install/check the pinned engine

From PowerShell in the extracted runpack:

```powershell
.\setup_nemo_242_wsl.ps1
```

This requires WSL with `conda` already available and creates environment `arcana-nemo242` from the upstream conda channels.

## 2. Run the governed pilot

```powershell
.\run_v0_6D1_R3_6D_nemo_wsl.ps1 `
  -Replicates 2 `
  -PopulationSizes 500,2000 `
  -LociPerTrait 64 `
  -MacroIntervals 1 `
  -ParallelJobs 6
```

The PowerShell runner:

1. prepares QTL ensembles and matched controls;
2. converts paths into WSL paths;
3. runs only exact `nemo2.4.2` jobs;
4. records return code/stdout/stderr per job;
5. parses qfreq output;
6. emits the cross-engine evidence summary.

Each NEMO process is constrained to one BLAS/OpenMP thread; independent jobs are parallelized instead.

## 3. Result to preserve/upload

Archive:

`local_runs/v0_6D1_R3_6D/`

Most important file:

`R3_6D_NEMO_EVIDENCE_SUMMARY.json`

Also preserve all `evidence/`, `*.qfreq`, `engine.stdout.txt`, `engine.stderr.txt`, `engine.returncode.txt`, INI files and job manifests.

## Fail-closed behavior

The stage must stop rather than silently continue when:

- `nemo2.4.2` is absent;
- a job returns non-zero;
- qfreq output is missing;
- the migration matrix is not symmetric/doubly stochastic;
- QTL moments fail their R3.6B mapping audit.
