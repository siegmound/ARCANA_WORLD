# R5.17-B7-A3F2-P7Q-PRE5C

## Static source-binding prototype

The two official archives were re-hashed successfully. Their 0.5-degree ASCII products are not exactly congruent: GLiM is 720×360 with `yllcorner=-90`, while GUM is 720×347 with `yllcorner=-89.985256795408`. Therefore no cell-wise merge is scientifically authorized.

The runner creates only a deterministic, external provider-grid diagnostic payload. It does not create canonical ARCANA parent material, physical soil, temporal states, depth, texture, profiles, abundance, or any K(x,t) state. No resampling, reprojection, nearest-neighbor mapping, or invented land-state crosswalk is used.

Grid-cell diagnostics: GLiM total 259,200; valid 87,098; nodata/ND 172,102. GUM total 249,840; valid 59,233; nodata 190,607. Cross-provider cell counts are explicitly not computed because the grids are incongruent; these are grid-cell counts, not area fractions.

GUM codes are retained losslessly and ambiguously because the payload exposes encoded abbreviations (`XX` etc.) without a decoded genetic semantic sufficient for exact ARCANA branch mapping. GUM absence remains `OUTSIDE_SOURCE_COVERAGE`; GLiM-only evidence is not direct parent-material support.

Verdict: `BLOCKED_P7Q_PRE5C_STATIC_SOURCE_BINDING_PROTOTYPE_INSUFFICIENT`.

Decision: `REQUIRE_P7Q_PRE5C_GRID_ALIGNMENT_GATE`.
