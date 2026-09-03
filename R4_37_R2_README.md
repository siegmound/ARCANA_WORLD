# ARCANA WorldSim v0.6D1-R4.37-R2
## Native Representability + Geonomics 1.4.9 Public-API Compatibility Repair

Live R4.37-R1 established two exact root causes.

### J21

Exactly two hash-valid canonical physical-unit environment fields are outside
Geonomics `Layer.rast`'s `[0,1]` domain:

- `temperature_anomaly_c`
- `sea_level_anomaly_m`

R4.37-R2 does **not** normalize, clip, or derive a transform from live values.

Instead:
- 149 already-native `[0,1]` payloads remain exact identity Geonomics Layers;
- 2 physical-unit payloads remain exact hash-bound canonical sidecars;
- all 151 canonical payloads are preserved unchanged;
- exact native bindings required: `149 × 4 = 596`.

This is a representability partition, not target tuning.

### J14 / J18

Geonomics 1.4.9 `Model.add_individuals()` contains an upstream public-wrapper
bug: when `source_spp` is supplied it evaluates `isinstance(source_spp, species)`
although `species` is not defined in `geonomics.sim.model`.

For the disposable mechanical dry-run only, R4.37-R2 temporarily binds the
missing module-global symbol to the actual Species class, calls the unchanged
public `Model.add_individuals()`, then restores the module state.

No installed Geonomics file is modified. ARCANA still never calls
`_add_individuals()` or `_remove_individuals()` directly.

### Still not authorized

- scientific exact initial-state installation;
- construction-probe elimination;
- Geonomics execution;
- run/walk/default-model;
- result-selected transforms;
- target numeric execution;
- readjudication;
- canonical-state writes.

Run:

```powershell
.\run_v0_6D1_R4_37_R2_targeted_repair_and_reseal.ps1
```
