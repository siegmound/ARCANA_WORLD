# Next-stage handoff after v0.6D1-R3.6D

## Current gate

R3.6D implements the complete executable NEMO 2.4.2 reference path but does not claim engine evidence that was not run.

## Immediate action

On the user's Windows/WSL machine:

1. `setup_nemo_242_wsl.ps1`
2. `run_v0_6D1_R3_6D_nemo_wsl.ps1 -Replicates 2 -PopulationSizes 500,2000 -LociPerTrait 64 -ParallelJobs 6`
3. archive/upload `local_runs/v0_6D1_R3_6D`.

## Review questions after execution

For B1 and C3, per axis:

- Is NEMO paired `Delta V_A` closer to ARCANA 1x125k or ARCANA 5x25k?
- Is the sign/magnitude stable across N?
- Does finite-N drift dominate the uncertainty?
- Does NEMO support substantial admixture-created standing variance, or is ARCANA moment mixing systematically excessive?

## Next governed stage

If engine evidence is complete, proceed to:

`v0.6D1-R3.6E — NEMO Evidence Closure & Quantitative-Genetics Causal Inference Gate`

R3.6E should close the actual three-way evidence and decide which hypothesis is supported. It must **not** automatically modify D3.

Only if a model correction is supported should a later R3.7 calibration stage test cadence, moment mixing, homeostasis timescale or ceiling policy.
