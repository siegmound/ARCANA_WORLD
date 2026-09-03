# ARCANA WorldSim v0.6D1-R3.6C

Three-way quantitative-genetics cadence validation foundation.

Run internal checks:

```powershell
.\run_v0_6D1_R3_6C_checks.ps1
```

Generate internal prevalidation evidence:

```powershell
$env:PYTHONPATH = "$PWD\src"
python scripts\run_cross_engine_cadence_v0_6D1_R3_6C.py local_runs\R3_6C --macrosteps 40
```

Actual NEMO execution is deliberately pending until an upstream-valid NEMO 2.4.2 executable/configuration is bound. No external-engine result may write ARCANA canonical state.
