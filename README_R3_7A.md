# v0.6D1-R3.7A

`Segregation-Potential Initialization, Evolution & Deme-Lifecycle Calibration`

This cumulative candidate closes the analytic/reduced-order lifecycle of the R3.7 genetic state and prepares an independent NEMO 2.4.2 B2 isolation→fragmentation→reconnection chain.

Current verdict:
`PASS_LIFECYCLE_ANALYTIC_AND_PARENT_NEMO_DRIFT_CLOSURE__NEMO_B2_CHAIN_CALIBRATION_PENDING`

Run local checks:

```powershell
.\run_v0_6D1_R3_7A_checks.ps1
```

Run the external NEMO B2 pilot:

```powershell
.\run_v0_6D1_R3_7A_nemo_b2_wsl.ps1 `
  -Replicates 2 -PopulationSizes 500,2000 -LociPerTrait 64 -ParallelChains 4
```

No production runtime binding or automatic calibration is authorized in R3.7A.
