# Next-stage handoff — after R3.7C-R1 external evidence

Do not advance on engine return codes alone.

Required smoke status:

`NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED`

with:

- `chain_count = 2`
- `complete_chain_count = 2`
- `selection_efficacy_pass_count = 2`
- `nemo_run_count_expected = 10`

Then run the full suite:

```powershell
.\run_v0_6D1_R3_7C_R1_nemo_selection_wsl.ps1 `
  -Replicates 2 `
  -PopulationSizes 500,2000 `
  -SelectionVariances 1,4 `
  -LociPerTrait 64 `
  -OptimumAmplitude 0.6 `
  -ParallelChains 4
```

Expected full dimensions: 16 chains, 80 NEMO phase runs, 16 efficacy passes.

Next stage after valid evidence:

**v0.6D1-R3.7D — Directional-Selection Evidence Closure & Adaptive Shadow Runtime Binding**.

R3.7D must determine from real NEMO evidence whether `K_eff` is scalar, trait-specific, selection-strength-dependent, population-size-dependent, or otherwise state-dependent. No scalar `K_eff` is authorized by R3.7C-R1 itself.
