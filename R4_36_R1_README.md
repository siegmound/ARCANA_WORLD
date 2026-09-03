# ARCANA WorldSim v0.6D1-R4.36-R1
## Governed Geonomics WSL Host-Runtime Bridge Repair + R4.36 Reseal

### Exact live root cause

The initial R4.36 live run reached the Geonomics construction registry before
materializing any native params. `geonomics_version`,
`native_parameter_materialized_count`, and `model_construction_pass_count`
therefore remained null.

R4.0 already SEALED Geonomics 1.4.9 in the WSL conda environment:

`/home/jose/miniforge3/envs/arcana-geonomics-149`

The original R4.36 runner incorrectly executed the integrated build with the
project's Windows `python`, where the governed Geonomics runtime is not
installed.

### Repair

R4.36-R1 changes only the execution boundary:

- source-manifest check: Windows project Python
- regression: Windows project Python
- Geonomics version preflight: existing governed WSL Python
- R4.36 integrated build: existing governed WSL Python
- final seal: Windows project Python

No package is installed and no environment is created.

The WSL project root is resolved dynamically with `wslpath`; the R4.36 source,
R4.35 authorities and outputs remain the same files on the mounted Windows
project root.

### Explicitly unchanged

- R4.35 SEALED authority
- 19/19 authority closures
- 23×4 seed vectors
- 12 intended native parameter modules
- J14/J18 injection payloads
- J21 151 canonical payload layers
- construction semantics
- no `run`, `walk`, or `run_default_model`
- no scientific execution
- no numeric target execution
- no readjudication
- no canonical-state write
- Deep OFF

The initial BLOCKED R4.36 evidence is preserved.

### Run

```powershell
.\run_v0_6D1_R4_36_R1_host_runtime_repair_and_reseal.ps1
```
