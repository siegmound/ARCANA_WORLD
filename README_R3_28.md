# R3.28 — High-Resolution 200 ka → 0 Replay

Single-stage workflow: source authority → regression → high-resolution replay → robustness → final seal.

Run from the ARCANA WorldSim root:

```powershell
.\run_v0_6D1_R3_28.ps1
```

Required existing authorities:
- R3.27 SEALED outputs and seal
- R3.21 present lineage/component registry
- exact SEALED R3.18 exposure bundle
- exact SEALED R3.20 CHA-2 hazard bundle

The runner auto-discovers R3.18/R3.20 artifacts by exact SHA-256 under `local_runs`, `outputs`, or the project root.

R3.28 does not claim R3.18 is a direct high-resolution time series: it uses phase-constrained downscaling. CHA-2 14.95–11 ka is consumed directly from the 80 × 50-year R3.20 states.
