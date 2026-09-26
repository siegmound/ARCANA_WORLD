# R6 Canonical Initial State Package — 210 Ma

**Status:** `CANONICAL_R6_INITIAL_PHYSICAL_STATE__UNKNOWN_DOMAINS_PRESERVED`

**Package content SHA-256:** `9c9a6ced1ecd530061872217b79499bdd479a1260867b99a6afe75ec0d6abf5f`
**Historical Simulation1 t0 recovered:** `false`

## Identity

- Run: `r6run_85af40f36fcb86c23a3571744817780a28e22740f6eaa04ae432bfe7d21f7f65`
- History: `r6hist_7de542d9a9c5030e01eba667e9c6f1e7fcbc4fcd913e2a1e6479fd729841ad63`
- GLOBAL_BASE branch: `r6branch_75a2a5ffe921187b585ce4f04db98c515bffa54e355f13c7e841fffa0b301454`
- Grid: `R6_GLOBAL_GEOGRAPHY_1DEG_V1` — 180×360, 1° nominal support
- Payload: `../_ARCANA_EXTERNAL_SOURCES/r6/initial_world/r6run_85af40f36fcb86c23a3571744817780a28e22740f6eaa04ae432bfe7d21f7f65/R6_INITIAL_PHYSICAL_GEOGRAPHY.npz`
- Payload SHA-256: `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c` (1169900 bytes)

## Registered domains

- `physical_geography` — `DERIVED_SUPPORTED` / `DERIVED_AUTHORITY`; state `r6state_d2e959c596bb1741d652c9d5f1d733b0d365cc9dbe362975048bc5ee3d3dca78`
- `land_ocean` — `DERIVED_SUPPORTED` / `DERIVED_AUTHORITY`; state `r6state_10c7ea803f6235662234d761b93b8047a35cf2cb8dcd2cd92b04ea4fba6f165a`
- `province_state` — `DERIVED_SUPPORTED` / `DERIVED_AUTHORITY`; state `r6state_4f09a4416a8972b985201056ac6bedff2da3c02677faffc48bf98f4605bace24`
- `topography` — `DERIVED_SUPPORTED` / `DERIVED_AUTHORITY`; state `r6state_6c1ad5e787aa3f26dba9c1fb8518c3f8da12184ef94025bf91de3bf85849691a`
- `bathymetry` — `UNKNOWN` / `NONE`; state `r6state_4275d09a648888b68bfbe16248f27742dab48defc2d3484cc3c8b9efb55b2ebb`
- `tectonic_kinematics` — `UNKNOWN` / `NONE`; state `r6state_6855b3953d3cfec7d82ca71332d459683c51ee66090d34a520ed7467cd295410`
- `deep` — `UNKNOWN` / `NONE`; state `r6state_6b89e1981a03a46067b835049ef333c76fbbabd561ac407f4c25c12e49b2628c`
- `climate` — `UNKNOWN` / `NONE`; state `r6state_0c54287c3b34e88045d99542716c468a930411ecb9e2f522ec4e91cb62a3a1ec`
- `hydrology` — `UNKNOWN` / `NONE`; state `r6state_74291206df1a7aeb43c1656a232a395b19f9ccb0cd4757803fe4be94dc5c58d4`

UNKNOWN is preserved for bathymetry, plate motion, Deep, climate and hydrology. No numeric placeholders are materialized for those domains.

## First post-t0 consumer

Selected earliest causal domain: `PHYSICAL_WORLD_EVOLUTION`. It is **blocked and not executed** pending:

- `governed_plate_motion_or_geodynamic_law`
- `dated_physical_forcings_and_event_schedule`
- `R6_Deep_initializer_and_laws_if_required_by_coupling`
- `bound_runtime_and_coupling_solver`

## Dependency/governance flags

- R5 runtime dependency: `false`
- A1 runtime dependency: `false`
- Simulation1 trajectory dependency: `false`
- Forward scientific simulation executed: `false`
- Provider acquisition executed: `false`
- P7Q reopened / physical soil created: `false` / `false`
