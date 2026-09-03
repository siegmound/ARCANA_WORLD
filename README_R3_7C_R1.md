# ARCANA WorldSim v0.6D1-R3.7C-R1

**NEMO Composite Selection Lifecycle Repair**

R3.7C-R1 fixes the external directional-selection oracle after the locally executed parent R3.7C suite produced 32/32 byte-identical selected-vs-neutral qfreq checkpoint pairs.

Key changes:

- selected branch now uses NEMO `breed_selection_disperse`;
- Gaussian selection uses absolute fitness;
- matched neutral branch remains `breed_disperse`;
- new fail-closed selected-vs-neutral efficacy gate;
- parent R3.7C source/test restored to their sealed hashes;
- previous invalid results retained as diagnostic evidence, not calibration authority.

Run the smoke first:

```powershell
.\run_v0_6D1_R3_7C_R1_nemo_selection_wsl.ps1 `
  -Replicates 1 `
  -PopulationSizes 500 `
  -SelectionVariances 1 `
  -LociPerTrait 64 `
  -OptimumAmplitude 0.6 `
  -ParallelChains 2
```

Expected smoke surface:

```text
chain_count: 2
complete_chain_count: 2
selection_efficacy_pass_count: 2
nemo_run_count_expected: 10
status: NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED
```

Only after this passes should the full 16-chain / 80-run oracle be executed.
