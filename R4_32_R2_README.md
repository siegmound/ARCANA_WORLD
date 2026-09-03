# ARCANA WorldSim v0.6D1-R4.32-R2
## R4.23 Profile-Indirection Repair + R4.32 Reseal

Root cause proven by R4.32-R1C:
- R4.23 registry records for J18/J21 are intentionally summaries.
- Their detailed frozen source bindings live in the JSON file referenced by `profile_path`.
- R4.32 incorrectly attempted to read `canonical_spatial_source(s)` and
  `binding_translation_materialized` directly from the summary record.
- This yielded J18 `path=null / sha256=null / hash_match=false` and an empty J21
  source list, even though R4.23 had already materialized both bindings.

Repair:
- preserve R4.23 byte-for-byte;
- dereference each frozen R4.23 `profile_path`;
- verify profile job identity;
- use the R4.23 summary's `binding_materialized == true` as the terminal
  materialization authority;
- hash-check the canonical source path(s) found in the frozen profile;
- do not change any target numeric value, mapping class, canonical state,
  execution authorization, or external-engine state.

The repair tool also backs up the prepatch R4.32 producer and source manifest
under `outputs/v0_6D1_R4_32_R2/`, updates only the producer hash entry in the
R4.32 source-authority manifest, runs a dedicated regression, then invokes the
full original R4.32 runner and a postrepair reseal audit.

Run:
    .\run_v0_6D1_R4_32_R2_repair_and_reseal.ps1

Expected closure:
- R4.32 source authority PASS
- original R4.32 regression PASS
- `geonomics_parameter_manifest_static_valid_count = 3`
- integrated R4.32 `29/29 PASS`
- final R4.32 seal `SEALED`
- runtime compilation remains 0
- Geonomics execution remains not ready/not authorized
- next action becomes R4.33 runtime-parameter compilation preflight
