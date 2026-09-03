# ARCANA WorldSim v0.6D1-R3.1

Repair release for the first rebased 210→150 Ma Natural-Control long run.

The previous R3 run completed but must not be continued from 150 Ma. Audit found that the rebased runtime applied Riccati VA homeostasis before gene-flow moment mixing and used a simplified gene-flow mixer. This differed from D3.3A, where gene flow is followed by the final homeostasis step and aggregate exchange per deme is capped.

R3.1 does not invent a new implementation. It vendors the already-tested D3.3A `additive_variance.py` unchanged and adapts only the root-species indexing needed by the rebased raster runtime.

## Windows rerun

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_v0_6D1_R3_1_windows.ps1 -EndAgeMa 150 -Threads 12
```

Do not resume from the old 150 Ma NPZ. R3.1 must restart at the R1 210 Ma common state embedded in the package.
