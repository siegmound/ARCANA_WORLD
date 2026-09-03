# v0.6D1-R0 — Historical Artifact Recovery Audit

## Verdict

`PASS_RECOVERY_AUDIT_WITH_PARTIAL_RAW_SURVIVAL_AND_EXECUTABLE_HISTORY_STILL_MISSING`

`FULL_210_TO_0_MA_HX = NOT_AUTHORIZED`

## Purpose

R0 is an evidence/recovery stage only. It determines which original D1/D2/D2.2 artifacts still exist, which facts can be verified from surviving RAW outputs, and which state would be unsafe to reconstruct. It does not re-simulate or infer missing historical state.

## Canonical historical chain

`D1 @ 210 Ma -> D2 pre-CHA1 -> D2.2 CHA-1 -> D3 post-CHA1`

The old D2 CHA-1 bottleneck is not survivor authority; D2.2 remains preferred for the CHA-1 event.

## Locked historical package hashes

- v0.6.3D1: `75a8bd4e90103e20ff308ef052871289eb3a608a558288abf1622c36a3b7fb1c`
- v0.6.3D2.T: `3b236d3a0a3a048b300d1fcd818006bedc93130c6a17abf9378635f0b6d76aa8`
- v0.6.3D2.1: `e751668c7a8232cf67b791b93312ad89050d8a7b2fd8cd4f9da4422fc0bc8828`
- v0.6.3D2.1.1: `918b5693efb0db81628efaba3f7f63b6365c1f975aba36d123401c2aede52905`
- v0.6.3D2.2: `42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8`

No trustworthy original v0.6.3D2 package hash was recovered from the surviving records inspected in R0. A filename-only D2 match therefore remains a candidate, not authority.

## Mounted ZIP audit

Three later WorldSim packages were inspected:

1. `ARCANA_WorldSim_v0_6_3D3_3B2_LONG_HORIZON_WINDOWS_RUNPACK(1).zip`
2. `ARCANA_WorldSim_v0_6_4D_Late_Cenozoic_Environmental_Provider_Closure_Audit_Production_Replay_Seal_Candidate(1).zip`
3. `ARCANA_WorldSim_v0_6_5B_R2_NATURAL_CONTROL_30Ma_0_WINDOWS_RUNPACK(1).zip`

Result:

- exact historical package hash matches: `0/5`;
- D1 `species_metadata.json`: FOUND in later packages;
- D3.0A `post_cha1_spatial_bridge_state.npz`: FOUND;
- D3.0A `spatial_bridge_diagnostics.json`: FOUND;
- `arcana_rawfirst.sqlite`: NOT FOUND;
- `physical_reference_cube.nc`: NOT FOUND;
- D2 frozen species raster NPZ: NOT FOUND;
- D2.2 `cha1_highres_state.npz`: NOT FOUND;
- pre-CHA1 D1/D2 solver Python: NOT FOUND.

The later packages therefore preserve identity and downstream boundary evidence, not the original historical solver/state archive.

## Surviving RAW-FIRST evidence

Project records prove that D2.T originally materialized:

- `outputs/raw/physical_reference_cube.nc`;
- a frozen D2 species raster NPZ;
- `outputs/stores/arcana_rawfirst.sqlite`.

The recorded store scale is:

- 121 species objects;
- 1331 global population-state rows;
- 5653 species×plate deme rows;
- 211 event rows.

These byte artifacts were not found in the current mounted files/File Library search.

D2.2 originally materialized 12 major RAW products. R0 found File-Library references for four of them:

- `species_population_timeseries.csv`;
- `physical_foodweb_timeseries.csv`;
- `CHA1_survivor_registry.json`;
- `species_diagnostics.json`.

The other major D2.2 RAW products remain documented but byte-unrecovered in this audit.

## What is recoverable without simulation

Safe/grounded:

- exact D1 120-species identity/metadata surface from later runpacks;
- D2 aggregate history: 120 initial species, 121 species objects ever, one ordinary extinction, one speciation;
- real D2 topology `HSG_003 -> HSG_025` and recorded gate metrics;
- D2.2 high-resolution event outcome and surviving RAW trajectories where bytes survive;
- D2.2 preferred survivor identities;
- real D2.2 -> D3.0A 31-survivor -> 115-deme-seed boundary.

## What is NOT safe to reconstruct

R0 explicitly forbids reconstructing from prose, survivor lists, or downstream geometry:

- D1 210 Ma population raster/state;
- D2 210->66 Ma cell/species population and trait trajectory;
- D2.2 continuous-hazard solver implementation;
- historical HSG_025 Deep sidecar from the D3.0A HSG_003 proxy;
- a bit-identical original H0 from post-CHA1 D3 state.

These would create false precision and violate RAW-FIRST.

## Recovery decision tree

### A — exact historical packages found

Bind them with hash verification, then run v0.6D1 Deep-OFF parity before any HX.

### B — RAW store/state found but solver packages missing

Recover state and schemas exactly, inspect whether executable/runtime source is embedded or referenced, and use the RAW history as an H0 oracle. Do not claim an original executable replay until the dynamics can reproduce the RAW history under Deep-OFF.

### C — only partial RAW outputs survive

Keep them as validation oracles. They are insufficient to produce the historical Deep-ON 210->66 Ma trajectory.

### D — original runtime cannot be recovered

The allowed fallback is a new explicitly rebased paired history, e.g. `H0-R / HX-R`, regenerated from the earliest authoritative reconstructible state with both controls using exactly the same new runtime. It must never be labeled bit-identical original D2 history.

## Next stage

`v0.6D1-R1 — Local Archive Recovery Scanner & Source Rehydration Gate`

Use `scan_v0_6D1_R0_windows.ps1` recursively over the Arcana project folders, Downloads, backup/archive folders, and any external drive containing old runpacks.
