# ARCANA WorldSim v0.6D1-R4.41
## Geonomics Domain-Specific Execution Queue Single-Transition Dry Run & State Invariant Validation

Parent:
- R4.40 integrated 38/38 PASS
- R4.40 final seal 25/25 SEALED

R4.41 performs the first disposable domain-specific transition dry run.

It does **not** call `Model.walk()`, `Model.run()`, or `run_default_model()`.

## Clock queue

The only Geonomics clock primitives called are the source-audited:

- `Model._set_t()`
- `Model._set_comm_t()`
- `Model._set_spp_t()`

They advance:

`model/community/species t: -1 -> 0`

No age-stage, movement, population-dynamics, or landscape-changer function is
called.

## J14/J18

For each of four frozen seeds:

1. construct the governed model;
2. deterministically choose the first branch in frozen canonical order;
3. install canonical state 0 exactly;
4. preserve that state in `orig_comm`;
5. advance the ordinal clocks once;
6. replace `comm` exactly with canonical state 1;
7. rebuild only spatial/density/environment caches;
8. validate invariants.

Required invariants:

- exact target `x=grid_col`, `y=grid_row`;
- target carrier count equals active canonical deme count;
- `population_proxy` is not consumed as count;
- `orig_comm` remains the initial anchor;
- births/deaths remain empty;
- carrier ages remain zero;
- RNG unchanged across the transition;
- landscape unchanged;
- K unchanged;
- no interpolation.

## J21

For each frozen seed:

1. construct the 147-native-layer static model with 4 sidecars absent;
2. validate all 147 initial native rasters;
3. advance ordinal clocks once;
4. directly replace all 147 rasters with the next canonical anchor;
5. validate all 147 targets exactly.

Invariants:

- construction support unchanged;
- carrier coordinates unchanged;
- K unchanged;
- births/deaths empty;
- ages unchanged;
- RNG unchanged;
- no `LandscapeChanger` exists or executes.

## Evidence status

R4.41 dry-runs are mechanical validation only:

- scientific evidence: false
- production execution queue authorized: false
- geonomics execution ready: false
- canonical state changed: false

Expected dry-run count if complete:

- J14: 4
- J18: 4
- J21: 4
- total: 12

Run:

```powershell
.\run_v0_6D1_R4_41.ps1
```

Next if SEALED:

`BUILD_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT`
