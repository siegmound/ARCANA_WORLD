# ARCANA WorldSim v0.6D1-R4.38
## Geonomics Exact Initialization Adapter & Construction Probe Elimination Preflight

Parent: authoritative R4.37 SEALED (40/40 integrated, 28/28 final seal, R3 17/17).

For each frozen replicate, one governed R4.36 model is constructed. Every canonical J14/J18 branch is then installed sequentially into that still-unrun disposable model by a narrow adapter that replaces the nongenomic construction probe with exactly one nonliteral carrier per active canonical deme.

The adapter preserves exact `x=grid_col`, `y=grid_row`; never consumes `population_proxy` as count or biology; rebuilds Geonomics coords/cells, KD-tree, density/N and environment caches; writes the adapted community into `orig_comm`; and verifies K, landscape rasters, RNG state and model counters remain unchanged.

Scope: J14 192 branches / 854 carriers × 4 seeds; J18 64 branches / 319 carriers × 4 seeds. Only 8 `make_model()` constructions are needed because branches are validated sequentially before each disposable model is discarded.

This is adapter validation, not scientific engine execution. `geonomics_execution_ready=false` remains mandatory.

Run:
```powershell
.\run_v0_6D1_R4_38.ps1
```

Next if SEALED:
`BUILD_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT`
