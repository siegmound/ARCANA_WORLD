# ARCANA R6 — HR1-MRES completed: measured six-tier workload, global physics blocked

Recorded 2026-10-31. Source: user-supplied FAIR report `docs/arcana/R6_HR1_MRES_FAIR_20261030.md` and actual `COMPARISON.csv` delivered to this chat. FAIR operator reported and internally verified: **54 infrastructure cases, 61 tests, four controlled SIGKILL, 31,690 manifest members**. This connected GitHub documentation entry does not independently access or rehash FAIR.

## Actual results

`HR1_MRES_WORKLOAD=PASS_MEASURED_SIX_TIER_METADATA_ARRAY_AND_RESTART`

`HR1_MRES_PHYSICS_1000Y=BLOCKED_TRUE_GLOBAL_GRID_PHYSICS_OR_INPUTS_UNAVAILABLE`

The six 2:1 grids have verified spherical geometry, periodic longitude/seam and pole area closure. Synthetic workload stores 8 dimensionless binary64 counters (64 B per cell) + separately accounted 1-byte mask. ALL fields and ALL cells change each model year, deterministic dyadic increments, byte-shuffle + zlib1 compressed, 128×128 tiles, exact SHA chain and B0 paired array-reference checkpoints. No regional/Unified/thermal/Deep numerical operators were imported. None of the absent domains may be interpreted as zero-valued physically.

**One real 1000-synthetic-year case per grid at 64 B/cell**, with 1/10/100Y cases at all grids. Additional 256B/1024B cases measured only 1Y/10Y, and denser event profile only 10Y. Do not label sensitivities as observed 1000Y.

| Raster | Cells | Wall s | Writer RSS MiB | Logical archive MB |
| --- | ---: | ---: | ---: | ---: |
| 256x128 | 32768 | 28.080 | 45.00 | 32.770 |
| 512x256 | 131072 | 36.347 | 51.41 | 105.865 |
| 854x427 | 364658 | 84.221 | 65.99 | 560.996 |
| 1280x640 | 819200 | 162.392 | 94.50 | 785.277 |
| 1920x960 | 1843200 | 352.681 | 158.99 | 1807.093 |
| 2048x1024 | 2097152 | 391.744 | 175.43 | 1393.953 |

The 2K 1000Y case performed 2,097,152,000 synthetic cell-year updates. Its 391.279 s measured child service includes **183.295 s compression**, **94.517 s shuffle/serialize**, **71.363 s raw SHA**, **21.726 s synthetic arithmetic**, 8.484 s journal fsync and 3.292 s B0 publication. Compression + shuffle + raw hash comprise **89.24%** of that child service; the cheap synthetic array update only **5.55%**. This is an I/O/codec workload, not an estimate of computationally realistic physics.

The 2K archive being ~22.86% smaller than the FullHD archive despite ~13.78% more cells is a data-entropy, shuffle and tile-alignment artifact; observed compression ratio 104.686x vs 69.531x. Do not infer that increasing physical resolution reduces natural-data storage. 2K 10Y at 256B/1024B has measured 28.132/89.926 s child service and 55.964/219.073 MB archive; these do not establish 1000Y costs.

**Recovery qualification boundary:** B0 visibility and restored array continuation are checked, including four SIGKILL phases. A journal tail previously durably written but not B0 committed remains orphaned; same-directory crash continuation can collide with those filenames, thus tail quarantine/linked continuation is NOT production-qualified. The array-reference checkpoint is NOT an R2 coupled numerical checkpoint.

**Global physics blockers:** global base `GlobalGrid1Degree` accepts 180x360; R2 synthetic regional operator fixed 3x3; Unified only C028/C029. No qualified global physics operator/forcing, pole/seam flux law, source-bound initial conditions, mesh/time convergence, conservative coupling or full solver restart at these six meshes. Do not upscale nine cells, copy two 1-degree supports or reinterpret synthetic array values as physically simulated global data.

Evidence and provenance: FAIR root `ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01`; `COMPARISON.csv`, `SCALABILITY.pdf`, `PHASE_COSTS.pdf`, `FINALIZATION.json`. New workload SHA `d1a590b7195bcf033a01abc6077c6281c8fe225543e4b01199bc9440c2414fc2`; new focused test SHA `2bad5858bae5aa3a3869574ca4fbfba24084b5145c1b823cc74016914bad3e30`. Original engine and archives protected; no auto commits/push.

## Proposed next gates — not automatically authorized

**HR1-MRES-P1: representativeness and crash tail qualification.** Research or model physically labeled but explicitly synthetic heterogeneous/spatially correlated values with independently controlled entropy, sparse/partial cell changes, nonuniform event density, metadata and missingness; use compatible source snapshots only when actually available and declared. Measure codec, hash, disk, RAM and indexing sensitivity with repeat controls, and qualify torn/uncommitted tail quarantine and same-directory restart. Do NOT silently change the existing passed fixture or claim a 1000Y physical trajectory. No new long test authorized by this result.

**HR2-PHYS: minimum honest globally coupled numerical provider.** Identify one scientifically defined and source-authenticated field (e.g. surface water or terrain evolution) with conservative spherical-grid fluxes, latitudinal area, periodic seam and pole rules, explicit units/time forcing, a verified small-grid oracle, convergence and restart; begin at bounded meshes/steps before considering 1000Y six-tier physics. Missing mineralogy, Deep, climate, fauna/flora, populations remain UNAVAILABLE, never invented.

**Data architecture:** The ultimate ARCANA goal remains full queryable multi-domain time/space history with zoomable time resolution, not an HD screenshot or pseudo-global clone of the nine-cell basin. Keep physics resolution, historical archive resolution, and visualization resolution separate.

```yaml
HR1_MRES_WORKLOAD: PASS_MEASURED_SIX_TIER_METADATA_ARRAY_AND_RESTART_OPERATOR_REPORTED
HR1_MRES_PHYSICS_1000Y: BLOCKED_TRUE_GLOBAL_GRID_PHYSICS_OR_INPUTS_UNAVAILABLE
HR1_MRES_NEXT_RUN: NOT_AUTHORIZED_BY_THIS_REPORT
HR2_GLOBAL_PHYSICS_IMPLEMENTED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
```
