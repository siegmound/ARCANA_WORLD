# ARCANA WorldSim v0.6D1-R4.37
## Geonomics Canonical Layer Binding & Exact-State Injection Dry-Run Validation

Parent requirement:
- R4.36 integrated 33/33 PASS;
- R4.36 final seal 25/25 SEALED;
- R4.36-R3 repair chain CLOSED 20/20.

R4.37 remains a **non-executing validation stage**.

## J21 — actual canonical native-layer binding

For each of the four frozen J21 replicates R4.37 constructs a new Geonomics 1.4.9 model with:

- 151 canonical R4.36 identity-value payload layers;
- one separate `R437_CONSTRUCTION_SUPPORT` layer used only by the one probe species;
- exact frozen replicate seed;
- `T=0`, `burn_T=0`.

Before construction every payload must:
- match its R4.36 SHA256;
- contain finite values;
- already lie in Geonomics' native `[0,1]` Layer domain.

If a canonical payload is outside `[0,1]`, R4.37 BLOCKS. It does not scale,
clip or normalize it.

After `make_model()` all 151 layer rasters are checked with `np.array_equal`.
Expected exact bindings: `151 × 4 = 604`.

## J14/J18 — public API mechanical coordinate dry run

Geonomics 1.4.9 `Model.add_individuals()` is not a fresh-model initializer:
it requires the recipient Species to be marked `burned` and requires a source
Species or msprime source.

R4.37 therefore does **not** claim to install final scientific state.

Instead, on disposable unrun models only:

1. preserve the original construction-probe Species;
2. clone its single probe Individual as a non-scientific source template;
3. set the recipient `burned=True` only as an explicitly test-only API guard
   override;
4. call the public `Model.add_individuals()` one carrier at a time;
5. compare every added Individual's public `x`/`y` values exactly with the
   canonical coordinate;
6. restore the `burned` flag;
7. discard the model.

ARCANA never calls `_remove_individuals()` or `_add_individuals()` directly.

All:
- J14 192 branches / 854 carriers;
- J18 64 branches / 319 carriers;
are validated independently under all four frozen replicate seeds.

This dry-run evidence is **mechanical, not scientific evidence**. The
construction probe remains present, so `geonomics_execution_ready=false`.

## Still forbidden

- `run()`
- `walk()`
- `run_default_model()`
- target numeric execution
- readjudication
- canonical-state writes
- Deep biological coupling
- treating the burn-guard override as a scientific initialization path

## Expected next step

`BUILD_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT`

R4.38 must solve the real fresh-model exact-initialization problem without
silently legitimizing the R4.37 test-only guard override.

## Run

```powershell
.\run_v0_6D1_R4_37.ps1
```


## R4.37-R2 targeted repair semantics

Live R4.37-R1 proved that exactly two J21 environment variables are not native
Geonomics `[0,1]` rasters:

- `temperature_anomaly_c` in canonical degrees Celsius anomaly;
- `sea_level_anomaly_m` in canonical metres anomaly.

R4.37-R2 does NOT derive a live min/max scaling transform. Instead:
- 149 already `[0,1]` payloads are identity-bound as Geonomics native Layers;
- the two physical-unit arrays remain hash-bound canonical sidecars;
- all 151 canonical payloads remain preserved unchanged;
- 149 × 4 = 596 exact native layer bindings are required.

Live R4.37-R1 also isolated an upstream Geonomics 1.4.9 public-wrapper defect:
`Model.add_individuals()` evaluates `isinstance(source_spp, species)` although
`species` is not defined in `geonomics.sim.model`.

For the disposable mechanical dry-run only, R4.37-R2 temporarily binds that
missing module-global symbol to the actual Species class, invokes the public
`Model.add_individuals()`, and restores the module state afterwards. No installed
Geonomics file is modified; ARCANA still never calls `_add_individuals()` or
`_remove_individuals()` directly.
