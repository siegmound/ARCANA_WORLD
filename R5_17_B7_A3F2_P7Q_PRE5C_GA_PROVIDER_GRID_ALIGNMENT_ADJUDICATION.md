# R5.17-B7-A3F2-P7Q-PRE5C-GA

## Provider grid alignment adjudication

The cached official GUM and GLiM archive hashes were reverified. Both use WGS84/EPSG:4326 and cellsize `0.5°`, but they are not the same grid. Recomputed offsets are `delta_x=+0.00001925036°` (`+0.00003850072` cells) and `delta_y=+0.014743204592°` (`+0.029486409184` cells).

Exact rectangular footprint intersection gives a deterministic same-index dominant-overlap crosswalk for all 249,840 GUM cells. The dominant footprint fraction is `0.9704762253439838` for minimum, mean, and maximum, above the explicit `0.95` guardrail; the largest secondary fraction is `0.0294852739360162`. There are 249,840 unique mappings and no ties.

ESRI ASCII rows are explicitly interpreted north-to-south and mapping uses geographic bounds. No resampling, reprojection, value modification, or canonical grid generation occurred. The GUM east edge exceeds GLiM's nominal xmax by `0.00001925036°`; this is recorded as 347 partial-outside cells with `NO_WRAP`, not silently clamped. The 13-row dimensional difference yields 12 fully GLiM-only northern rows (rows 348–359, latitude 84–90°) and one partially overlapping row 347.

This closes geometry only. GUM remains the primary material-support grid; GLiM remains a surface-lithology conditioner and future use requires `SPATIAL_REMAP_UNCERTAINTY`. GUM codes remain `AMBIGUOUS_RETAIN_UNKNOWN`, land state remains unbound, and no parent-material state is materialized.

Decision: `AUTHORIZE_P7Q_PRE5C_GUM_CLASS_SEMANTIC_DECODING_GATE_WITH_DOMINANT_OVERLAP_CROSSWALK`.

Verdict: `PASS_P7Q_PRE5C_PROVIDER_GRID_ALIGNMENT_ADJUDICATED`.
