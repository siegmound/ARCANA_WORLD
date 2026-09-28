# R6 T0 B-v2 ocean thermal-isostatic surface closure

**Decision:** `R6_T0_OCEAN_THERMAL_ISOSTATIC_SURFACE_MATERIALIZED__ORBDATA_INPUT_GAPS_REMAIN`

- Parent package: `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz` SHA256 `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`.
- New package: `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz` SHA256 `31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534`.
- Model: `GDH1_STEIN_STEIN_1992_WATER_LOADED_AGE_DEPTH_V1` (1.0.0); Stein, C.A. & Stein, S. (1992), Nature 359, 123-128, doi:10.1038/359123a0.
- Authority: GDH1 coefficients are a published Earth-analogue physical model configuration; derived thermal component is `SPECIALIST_DERIVED_T0`; authorial residual remains `AUTHORIAL_T0_PRIMITIVE`.
- No Earth observation, Earth bathymetry grid, OrbData output, or canonical geography was imported or changed.

## Component lineage

- Age input SHA256: `aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2` -> `aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2` (unchanged).
- Thermal component `ocean_thermal_isostatic_elevation_m` SHA256: `90ebdb63a981fde968a696a6844a51fb47be6a87e756f0651b947be10901d887`.
- Authorial residual SHA256: `315078fc021637823399a8a96272dcfc69d7746a3098064042119d7453755cfc` -> `315078fc021637823399a8a96272dcfc69d7746a3098064042119d7453755cfc` (unchanged).
- Canonical land elevation SHA256: `79b8a50159c5f74b94a0e0f4d856336a829c9e1d1cf9ee145ba0daac97f96c45` -> `79b8a50159c5f74b94a0e0f4d856336a829c9e1d1cf9ee145ba0daac97f96c45` (unchanged).
- Total surface `total_surface_elevation_m` SHA256: `b5cbbac4136b46f6352d2738552013995477b956ab31af9435b10b3d2ad4be70`.
- Ocean total is thermal elevation plus the unchanged authorial residual; land total copies the canonical land array exactly.

- All unchanged parent field hashes are retained under `component_lineage.unchanged_parent_field_hashes`; only the prior all-ocean unknown mask is replaced with the recomputed unknown-total mask.

## GDH1 configuration and model-form uncertainty

For age <20 Ma, depth is 2600 + 365√age m. For age ≥20 Ma, depth is 5651 − 2473 exp(−0.0278 age) m. Depth is positive downward; thermal elevation is its negative relative to the existing R6 zero datum.
At the 20 Ma branch, the young limit is 4232.329624 m and the old branch is 4232.738269 m; the specified piecewise law has a 0.408646 m old-minus-young step. No smoothing was applied.
Model-form axis: `OCEAN_PLATE_COOLING_MODEL_FORM`; primary `GDH1_COMPATIBLE_REFERENCE`; future comparator `REVISED_PLATE_MODEL_FAMILY`. No ensemble or second candidate world was generated. Reference: [Holdt et al. (2025)](https://doi.org/10.1029/2024JB029890).

## Ocean diagnostics

- Governed ocean cells: 50542; known elevation cells: 50542; unknown: 0; coverage: 1.000000000.
- Thermal elevation min/max: -5622.061 / -2600.000 m.
- Residual area-weighted mean / RMS / hard cap: -0.000000000 / 500.000000 / 1200.000 m.
- Total ocean elevation min/max: -6819.276 / -1400.000 m.
- Total ocean area-weighted mean / median: -5110.418 / -5165.141 m.
- Positive-down final ocean depth min/max: 1400.000 / 6819.276 m.
- GDH1 depth monotone over 0–160 Ma: True; ocean cells at/above zero datum: 0.

## PRE_ORBDATA

**Not ready.** Ocean surface is now complete on governed cell support, but PRE_ORBDATA still requires nodal inputs and closed auxiliary-grid/runtime interfaces.
- global heat-flow routing and qArray policy
- aArray export and coast-classification qualification
- cArray export
- continental mantle thickness sArray interoperability
- OrbData material/thermal configuration
- FEG nodal materialization and zero-elevation interface qualification

Age and residual were not regenerated. OrbData, SHELLS mechanics, forward evolution, `dt`, and `t1` were not run or created.
