# ARCANA WorldSim v0.6D1-R4.36-R2
## Geonomics Defined-Layer Schema-Probe Namespace Repair + R4.36 Reseal

### Exact root cause

R4.36-R1 successfully reached the already governed WSL Geonomics 1.4.9 runtime.
The run then stopped before native parameter materialization.

Geonomics 1.4.9's generated `defined` layer template contains:

`'rast': np.ones((20,20))`

but the generated parameter file does not necessarily include a self-contained
`import numpy as np`.

R4.36's non-scientific schema probe used a strict Python-module import, so the
probe failed on `NameError: np is not defined`.

### Narrow repair

Only the installed-runtime-generated **schema probe** is read with a minimal
controlled namespace containing `np`.

ARCANA's 12 materialized native parameter files remain on the strict,
self-contained import path and must themselves include all required imports.

This is not a scientific adapter and provides no new scientific authority.

### Unchanged

- R4.35 SEALED
- R4.36-R1 governed Windows→WSL runtime bridge
- Geonomics runtime and version
- 23×4 frozen seed authority
- intended 12 native parameter modules
- J14/J18 exact-state payloads
- J21 151 canonical payload layers
- no exact-state injection in R4.36
- no model run/walk/default-model execution
- no numeric target execution
- no readjudication
- no canonical-state change
- Deep OFF

### Run

```powershell
.\run_v0_6D1_R4_36_R2_schema_probe_repair_and_reseal.ps1
```
