# R6 Wave 3A — Physical Geography t0 Binding

## Decision

`R6_PHYSICAL_T0 = BLOCKED`; `R6_GLOBAL_T0 = 210 Ma` is **not frozen**. The 210 Ma A1 frame is `REFERENCE_ONLY`. No initial field is promoted to R6 state by this audit.

The bundle `references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz` (SHA256 `9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f`) contains 11 frames from 210 to 0 Ma on a 90×180, 2° center grid. At 210 Ma, its binary land mask has 3,616 ones and 12,584 zeros; plate codes contain values 0–10 in that frame, with no codebook recovered. Across the entire trajectory plate codes span 0–11. All floating arrays were finite (zero NaNs); this does not make zero a missing-value code or confer semantic authority.

| Physical property | Wave-3A classification | Finding |
|---|---|---|
| Land mask | `REFERENCE_ONLY` | Binary array present; Sim1 input role and ocean semantics unbound |
| Plate code | `REFERENCE_ONLY` | Categorical carrier only; no names, rotations, polygons, topology, or motion law |
| Topography/elevation | `UNKNOWN_REQUIREMENT_AND_MISSING_FROM_A1` | Absent; original consumer is missing, so cannot decide whether generated at bootstrap or not required |
| Coastline | `REFERENCE_ONLY_DERIVABLE_NOT_BOUND` | Could derive a raster boundary from land mask; no governed coastline representation |
| Basins/lithology | `UNKNOWN_NOT_ESTABLISHED_AS_T0_REQUIREMENT` | Not present in A1; original requirement unresolved |
| Crustal/tectonic state | `REFERENCE_ONLY_PARTIAL_CARRIER` | Plate IDs do not encode a verified evolving tectonic model |
| Sea level | `UNKNOWN` | No value/datum or bootstrap binding recovered |
| Ocean mask | `DERIVED_FROM_REFERENCE_ONLY` | Complementing land mask is a representation, not independent authority |

The repository cannot distinguish terrestrial Pangaea reconstruction, transformed Earth paleogeography, or synthetic ARCANA supercontinent geometry. Use only `ARCANA A1 supercontinent-like reference` until the pre-import authority is recovered. Later R2/R3 code uses precomputed A1 boundary frames and endpoint-derived transition rules; that does not establish the original Simulation-1 evolution process. Full array shapes/ranges and planetary-assumption classifications are in the JSON artifact.

No climate or hydrology run, provider acquisition, simulation, or file promotion occurred.
