# ARCANA WorldSim v0.6D1-R3.6D

**NEMO 2.4.2 Executable Reference Binding & Ensemble Run Evidence**

This candidate turns the R3.6B/R3.6C NEMO reference design into an executable, provenance-tracked WSL runpack.

Key properties:

- exact `nemo2.4.2` executable pin;
- source-bound NEMO quantitative-trait initialization;
- exact ARCANA `a(g-1)` -> NEMO alleles `±a/2` mapping;
- hermaphrodite `patch_nbfem=N`, `patch_nbmal=0` population mapping;
- `breed_disperse + mating_isWrightFisher` controlled reference lifecycle;
- symmetric/doubly-stochastic cadence-normalized migration only;
- matched FLOW/no-flow common QTL + common RNG seed;
- mutation=0, no selection in the primary reference;
- qfreq parser -> `ScientificEvidenceBundle`;
- automated N sensitivity and three-way review table;
- no canonical writes and no automatic calibration.

Run package checks:

```powershell
.\run_v0_6D1_R3_6D_checks.ps1
```

Install NEMO in WSL:

```powershell
.\setup_nemo_242_wsl.ps1
```

Run the default pilot:

```powershell
.\run_v0_6D1_R3_6D_nemo_wsl.ps1 -Replicates 2 -PopulationSizes 500,2000 -LociPerTrait 64 -ParallelJobs 6
```

## R2 technical repair — qfreq finalization
After the first real WSL2 smoke completed 10/10 NEMO 2.4.2 jobs with rc=0 but emitted no `.qfreq`, the binding was corrected to schedule `quanti_freq_logtime` on the final NEMO generation. See `NEMO_QFREQ_FINALIZATION_REPAIR_v0_6D1_R3_6D_R2.md`. No scientific parameters changed.
