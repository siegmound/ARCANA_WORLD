# R6 Wave 3 — Simulation 1 Initial Component Matrix

Audit baseline: `main` at `592b1651b405363373590092e133bd25569d99a5` (origin/main matched at inspection). No scientific execution or provider acquisition was performed.

## Determination

The authorial requirement is fixed as `SIMULATION1_PANGAEA_EARTH_LIKE`. Repository references strongly converge on a 210 Ma start: the A1 age coordinate begins at 210 Ma and the later R1–R3 configuration lineage starts there. However, the scoped audit did not locate the original Simulation-1 bootstrap contract/config that binds those artifacts to its actual initial world. Therefore **210 Ma is the supported candidate, not yet a frozen R6 canonical t0**.

`FULL_A1_REFERENCE_210_0Ma.npz` is classified as `SIMULATION1_PHYSICAL_REFERENCE_TRAJECTORY_WITH_INITIAL_FRAME__R6_REFERENCE_ONLY`: 11 ages from 210 to 0 Ma on a 90×180, 2-degree coordinate grid; land mask and plate codes are accompanied by climate, forage, population, and carrying-capacity fields. It is a mixed reference bundle, not a complete initializer or a validated rotation/topology model. The first frame is not promoted to R6 state, and the later trajectory is not reused.

| Component | Source / role | T0 requirement | R6 readiness / reuse | Gap |
|---|---|---:|---|---|
| Global t0/time | A1 age coordinate; R1–R3 later configs | Yes | **Partial** — 210 Ma candidate; contract only | Recover original Simulation-1 bootstrap boundary/time semantics |
| Planet parameters | R1 config’s `compatibility_radius_km=6371.0088` is a biological distance parameter | Yes | **Blocked** as canonical planet constants | Recover explicit radius, gravity, rotation/day, axial/orbital, atmosphere and sea-level assumptions, or record as unspecified |
| Pangaea geometry/plates | A1 210 Ma `land_mask`/`plate_code` | Yes | **Partial**, reference-only | Bind original frame identity, terminology, plate-code meaning and provenance; do not infer terrestrial Pangaea or rotations/topology |
| Grid | A1 lat/lon arrays, 90×180 at 2° centers | Yes | **Partial**; preserve native support | Bind R6 CRS, periodicity, cell support and cross-domain compatibility |
| Topography/shoreline | No qualified 210 Ma elevation/shoreline source located; a land mask is not elevation | Yes | **Blocked** | Recover source payload or authorized generation law and exact inputs |
| Climate | A1 temperature/aridity fields are mixed reference outputs; P7S support is bounded/incomplete | Yes, as boundary or governed generation | **Blocked** | Bind initialization semantics and validated climate boundary/generator |
| Hydrology | B6 D3 has no successful snapshots; B6 D1 is contract-only | Yes, field or justified generator | **Blocked** | Recover original initializer or validated geography/climate-to-hydrology law |
| Deep | 210 Ma Deep reference/calibration exists; later R1 builds a candidate state | Yes | **Partial**, contract/reference only | Bind fundamental Deep state/law/provenance; keep later accessibility/resource views distinct |
| Early biology | A1 includes population/capacity; R1 disclaims recovery of lost original species raster | Not assumed | **Partial**; domain activation unresolved | Recover original initialization/activation semantics; do not seed R6 from A1 derived populations |
| Physical/Deep laws | R1–R3 code/config and Deep calibration are later implementation lineage | Yes | **Blocked** as a complete R6 law bundle | Recover canonical laws/versions/parameters and adjudicate validated replacements |
| CHA-1 | Scoped R3.10 66.0–65.5 Ma event contract | No, later event | **Partial**, contract only | Bind applicability, uncertainty, effects and R6 scheduler adapter |
| CHA-2 | Scoped R3.20 Younger-Dryas-class hazard contract | No, later event | **Partial**, contract only | Bind applicability, uncertainty, effects and R6 scheduler adapter |
| Seed/ensemble | Later R1–R3 configs use seed 917231 | Yes for reproducibility | **Blocked** as Simulation-1/R6 lineage | Recover original RNG lineage/runtime or explicitly govern a new R6 ensemble |
| Later domain activation | R3–R5/P7 contracts and R6 architecture | No blanket activation at t0 | **Partial** | Bind domain-specific start times; preserve UNKNOWN/INACTIVE_BEFORE_DOMAIN_START |

Full evidence, individual hashes, field classification, reuse mode and blocker taxonomy are in [`R6_SIMULATION1_INITIAL_COMPONENT_MATRIX.json`](R6_SIMULATION1_INITIAL_COMPONENT_MATRIX.json).

## Outcome

No canonical package is emitted: topography/shoreline, physical planetary assumptions, the original Simulation-1 bootstrap binding, and a complete law/seed/event lineage are not closed. A targeted recovery record accompanies this matrix. No simulation, acquisition, state materialization, current-state edit, authority-register edit, or execution-index edit occurred.
