# ARCANA WorldSim v0.6D1-R4.36
## Geonomics Native Parameter Materialization, Model Construction & Exact-State Injection Preflight

**Status:** CANDIDATE OVERLAY — run only on the authoritative live root.

### Required parent

R4.35 must be SEALED with:
- 19/19 native-schema/initial-state/seed authority gaps terminally closed;
- 23 jobs × 4 frozen replicate seeds, all 92 globally unique;
- exact J14/J18 nonliteral population semantics;
- exact spatial-injection authority;
- J21 provenance-separated layer-role authority;
- native params still 0 and no `make_model()` yet.

### R4.36 is the first stage allowed to construct Geonomics Models

Geonomics 1.4.9 is required.

R4.36:
1. asks the installed Geonomics 1.4.9 runtime to generate a one-defined-layer,
   one-nongenomic-species schema probe;
2. converts that installed schema into 12 explicit construction-only native
   parameter modules: J14/J18/J21 × four frozen replicate seeds;
3. binds the exact frozen seed to `model.seed.num`;
4. imports each materialized parameter module;
5. creates a Geonomics `ParametersDict`;
6. calls `gnx.make_model()` exactly for construction validation;
7. verifies every constructed model is still unrun (`t=burn_t=it=-1`);
8. verifies the exact-state injection API exposes `n` and `coords`.

No `run`, `walk`, or `run_default_model` is called.

### Construction-probe semantics

The one probe individual and one support layer exist only because the native
Geonomics constructor requires a Community and carrying-capacity scaffold.

They are **not scientific state** and can never be used as ARCANA evidence.
All dynamics values retained from the installed template are likewise
construction-only and do not authorize a simulation.

### Exact initial-state preflight

R4.36 does not mutate the constructed Model yet.

Instead it materializes the complete injection payload:

- J14: all 96 storage-axis-0 members × 2 candidate IDs = 192 initial branches;
- J18: all 32 frozen parent members × 2 candidate IDs = 64 initial branches;
- every active deme's exact coordinates are retained;
- `population_proxy` remains a sidecar weight, never a literal individual count;
- J18 coordinates remain `x=grid_col`, `y=grid_row` with no `+0.5` shift;
- J14 remains explicitly model-derived authority, not observed location history.

A future exact injection must first remove/replace the construction probe
without allowing it to contaminate the scientific state.

### J21 canonical payload

R4.36 materializes the initial 20 ka identity-value payloads:
- 7 environment layers;
- 36 producer taxa × 4 producer-support variables = 144 layers;
- total 151 `.npy` payloads.

No automatic scaling, clipping, cross-layer fusion, or producer-agent synthesis
is performed.

The 151 canonical payloads are deliberately **not yet bound into the constructed
Model**. R4.37 will validate that binding together with exact state injection.

### Expected live result

- 12 native parameter modules materialized;
- 12/12 `make_model()` constructions PASS;
- 12/12 exact frozen replicate seeds match `Model.seed`;
- all models remain unrun;
- J14 branches = 192;
- J18 branches = 64;
- J21 initial payload layers = 151;
- exact-state injection performed = 0;
- model runs = 0;
- scientific execution = false.

### Next stage

`BUILD_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_INJECTION_DRY_RUN_VALIDATION`

### Run

```powershell
.\run_v0_6D1_R4_36.ps1
```
