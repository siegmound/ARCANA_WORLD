# ARCANA R6 — HR1-MRES: multiresolution 1000Y resource and metadata benchmarks

**Date:** 2026-10-30. **Decision:** user requests evaluating multiple cell counts — 480, 720, HD, 2K and lower — instead of only one 2K configuration. This **amends and supersedes the single-size experimental matrix**, not the original distinction between metadata workload and real qualified planetary physics in `PROJECT_LEDGER/R6_HR1_2K_1000Y_WORKLOAD_AND_REAL_PHYSICS_GATE_20261030.md`. **NOT EXECUTED.**

## Comparable global-grid resolution ladder

Use **the same 2:1 longitude×latitude global raster** for all tiers, with proper spherical area per cell and polar/periodic-longitude handling; labels `480/720/Full HD` are *geo-grid equivalents*, **not literal 16:9 video resolutions**. Source radius/area and row/column layout must be declared, and the same field schema, compression, tile, cadence, precision and provenance rules used for comparisons.

| Label | W×H | Number of cells | Cell-years if actually advanced 1000Y |
| --- | --- | ---: | ---: |
| Preview | 256×128 | 32768 | 32768000 |
| SD | 512×256 | 131072 | 131072000 |
| 480-equivalent | 854×427 | 364658 | 364658000 |
| 720-equivalent | 1280×640 | 819200 | 819200000 |
| Full HD-equivalent | 1920×960 | 1843200 | 1843200000 |
| 2K | 2048×1024 | 2097152 | 2097152000 |

At the 2K tier, one uncompressed 8-byte scalar per cell per 1000 annual records is **16.777 GB decimal** and 64-byte payload per cell-year is **134.218 GB decimal**. These are arithmetic work-size illustrations, not measurements or a disk limit.

## Scope and execution stages

- **HR1-MRES-A read-only capability audit:** inspect local FAIR dirty R1/R2/REC1/L1 source SHA, POST10K-A0 and synthetic 10k evidence, actual approved providers. Existing nine-cell unlocated regional 1 km² basin and C028/C029 1° support columns with 73 nodes each are NOT a genuine 2K global numerical solver. Do not upsample/copy these as if independent source states; missing physical climate, chemistry, species/populations and Deep global fields are UNKNOWN.
- **HR1-MRES-B actual measured metadata and array workload on each of all six tiers:** use the same deterministic, explicitly SYNTHETIC_WORKLOAD_ONLY data generator; tiled numeric arrays, actual geometries, typed fields/masks/units and source provenance, lossless compact journal, sparse events and NULL, content hashes, index, atomic B0 paired checkpoint, exact queries/reopen. Never allocate billions of Python dictionaries. Include **common baseline payload profile 64 bytes/cell-year**, plus separate sensitivities 256/1024 bytes and explicitly declared changed-cell/event sparsity where useful. Test actual 1-year, 10-year, 100-year windows, and progress to full 1000Y metadata workload at each resolution where qualified and permissible. **A 1000Y estimate is not a measured 1000Y test**. No fake PASS for unexecuted horizons.
- **HR1-MRES-C conditional real 1000Y planetary-grid physics:** only if an independently qualified spatial numerical provider, compatible georeferenced inputs/forcing, conservative global boundaries/fluxes, stability and recovery exist. The prior owner request is to attempt one true high-resolution 1000Y target if these are established. Otherwise explicitly `HR1_MRES_PHYSICS_1000Y=BLOCKED_TRUE_GLOBAL_GRID_PHYSICS_OR_INPUTS_UNAVAILABLE`; a synthetic writer is not planetary physics. No unreviewed operator-law changes, long 10k/100k, or automatic retry.
- Record source/test SHA and new exclusive evidence roots; preserve original FAIR dirty source and all previous archives without reset/pull/merge/auto-commit/push.

## Required measured comparison

Per tier x actual years x payload/event profile: wall launch-to-exit; CPU user/system/effective cores; process-tree RSS; logical/allocated disk B and file counts; timing for numerical-array work vs serialization/compression/hash/index/B0 paired checkpoint/fsync; exact cold/warm query and restart; per-cell-year update/write/query throughput; compression ratios and byte cost per field/tile/cell-year/event/source metadata; volume/area conservation if relevant. Report cold vs warmed query separately and do not double-count nested costs. Compute scaling only from **actually measured** windows with assumptions and residuals; distinguish real measurements from conditional 1000Y scenarios, especially for higher tiers. All original source values and causal IDs must remain intact. No fabricated natural resource/climate/Deep values.

**Full operational instructions** delivered to the user as `ARCANA_R6_HR1_MULTIRES_1000Y_BENCHMARK_GATE_20261030.md`, with matrix, profiles, staged runs, fields and gates.

```yaml
HR1_MRES_POLICY: USER_REQUESTED_SIX_LEVEL_RESOLUTION_LADDER
HR1_MRES_WORKLOAD: NOT_EXECUTED
HR1_MRES_PHYSICS_1000Y: CONDITIONALLY_AUTHORIZED_IF_GENUINE_QUALIFIED_PROVIDER_EXISTS
ORIGINAL_10K_AND_A0_EVIDENCE: IMMUTABLE
AUTO_COMMIT_OR_PUSH: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
```
