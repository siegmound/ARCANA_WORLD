# R6 B-Pangaea-like v2 specialist materialization

**Decision:** `R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_PARTIAL__MATERIALIZER_RUNTIME_BLOCKED`

## Parent state

- Realization: `B_PANGAEA_LIKE_LATE_TRIASSIC_v2` at T0 = 210 Ma; still a candidate.
- Geography `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`, partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`.
- Mesh `6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad`; upstream field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`.
- Canonical state was not modified.

## Exact pending-field ledger at entry

### ALREADY_MATERIALIZED

- `physical_crust_domain_id` — MATERIALIZED_UPSTREAM; SHA256 `814acfdde0285bf6bd549ae8c06e853da5855acb9e78187359a5230fe47cdfd1`.
- `crustal_thickness_m` — MATERIALIZED_UPSTREAM; SHA256 `d416e12cdc7ddc2e47dbfb5f67defe2651190ee3b30b04bdba083a00dda7bb3c`.
- `continental_thermal_domain_id` — MATERIALIZED_UPSTREAM; SHA256 `8dd631433acfe68ebb3312a20c904b313883596e8da63da10bbb50d854040d75`.
- `continental_reference_surface_heat_flow_w_m2` — MATERIALIZED_UPSTREAM; SHA256 `234d2c34f4bc98f72cbaa0e1b322ba781bc95fab9e7b69795fb2b3e7a03b7e2f`.
- `continental_reference_lithosphere_thickness_m` — MATERIALIZED_UPSTREAM; SHA256 `1e7db18c673c43c3048a863442e8182b9007d4cc292f60309583ce7b67d3e430`.
- `oceanic_lithosphere_age_ma` — MATERIALIZED_UPSTREAM; SHA256 `aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2`.
- `ocean_surface_authorial_residual_m` — MATERIALIZED_UPSTREAM; SHA256 `315078fc021637823399a8a96272dcfc69d7746a3098064042119d7453755cfc`.
- `canonical_land_surface_elevation_m` — CANONICAL_LAND_SUPPORT_ONLY; SHA256 `79b8a50159c5f74b94a0e0f4d856336a829c9e1d1cf9ee145ba0daac97f96c45`.
- `unknown_total_ocean_elevation_mask` — UNKNOWN_MASK_NOT_NUMERIC_ELEVATION; SHA256 `3c52af8ec1c5eb09557f5fda9a6c1153a1cc8bde1e94dff50026710456a21df7`.

### PENDING_SPECIALIST_RUNTIME

- ocean thermal profile and age-derived heat flow
- ocean thermal lithosphere thickness
- thermal/isostatic ocean bathymetry component and complete ocean surface
- continental geotherm profiles and model-derived heat flow beyond ratified references
- chemical density anomaly
- cooling curvature

### PENDING_MODEL_CONFIGURATION

- Reference parameters: rhoBar_crust, rhoBar_mantle, rhoAst, rhoH2O, alphaT_crust_mantle, conductivity_crust_mantle, radiogenic_heat_production_crust_mantle, surface_temperature_and_temperature_limits, TADIAB_GRADIE_ZBASTH.
- Rheology families: CFRIC, FFRIC, BIOT, BYERLY, ACREEP(1), ACREEP(2), BCREEP(1), BCREEP(2), CCREEP(1), CCREEP(2), DCREEP(1), DCREEP(2), ECREEP.

### PENDING_NUMERICAL_PROJECTION

- Project governed cell-domain crust/thermal fields to the 64,442-node FEG support with a validated interpolation/error policy.
- Project specialist-complete global elevation and heat-flow fields to FEG nodes with lineage per node.

### NOT_REQUIRED

- External absolute lithostatic pressure, EOS density, mineral phase fractions, and a 3-D gravity field; the parent minimum-state contract says SHELLS/OrbData derives or does not consume them.
- OrbData5 only if direct ARCANA/specialist producers supply every required physical field with equivalent governed provenance; that condition is not met in this report.
- Fault elements and fault-only mechanical values in Level 1 (nFl=0).
- Earth observational geography/grids and Earth OrbScore calibration.
- SHELLS mechanical solve, finite-time evolution, dt, and t1 at this stage.

### UNKNOWN

- Exact selected/version-pinned plate-cooling/isostatic engine and its local availability.
- Exact pinned ShellSet/SHELLS and OrbData source builds and parser conventions.
- Computational reference-frame behavior and global gauge; explicitly deferred to runtime qualification.
- Whether a validated OrbData-free producer can supply chemical_delta_rho and cooling_curvature without changing their contract semantics.

## Runtime and field result

- Specialist qualification: BLOCKED_NOT_RUN; smoke: BLOCKED_NOT_RUN.
- Ocean heat flow: MISSING; global heat flow: MISSING.
- Complete elevation: `INCOMPLETE_LAND_SUPPORT_PLUS_OCEAN_RESIDUAL_COMPONENT`.
- Mantle-lithosphere thickness: oceanic `PENDING_APPROVED_AGE_TO_THERMAL_SPECIALIST`; no global nodal field.
- `chemical_delta_rho`: PENDING_SPECIALIST_OR_VALID_EQUIVALENT; no zero placeholder.
- Cooling curvature: PENDING_ORBDATA_OR_VALID_EQUIVALENT; no arbitrary zero.
- FEGs: PRE_ORBDATA 0; SHELLS_READY 0.
- Runtime manifest remains incomplete and unauthorized.

## Configuration status

Reference configuration: INCOMPLETE__9_OF_11_FAMILIES_UNSELECTED. Two canonical constants are bound; nine other families remain open.
Rheology: NOT_SELECTED_OR_SOURCE_PINNED; no sensitivity members were generated.
Level 1 retains nFl=0; fault-only parameters are inactive.

## Why execution stopped

- No GWB, OrbData5, SHELLS, or ShellSet executable is available on PATH; specialist version/build smoke and T0 transformation cannot run here.
- The design does not select and version-pin the approved ocean plate-cooling/isostatic materializer.
- Ocean thermal state, ocean heat flow, ocean mantle-lithosphere thickness, and the thermal/isostatic elevation component remain unmaterialized.
- The current age field is an authoritative T0 input; its plate-cooling consequences require the approved specialist runtime and must not be regenerated.
- Global elevation, global heat flow, continental geotherm support, chemical_delta_rho, and cooling_curvature do not yet have complete governed FEG-node fields.
- Nine noncanonical reference-parameter families and the numerical ShellSet rheology baseline/sensitivity members remain unselected; ShellSet source/version semantics are not pinned locally.
- The runtime manifest remains incomplete and runtime_authorized=false; no scientific SHELLS_READY FEG can be written.

## Gate

ShellSet runtime readiness: `NOT_READY__SPECIALIST_FIELDS_CONFIGURATIONS_NODE_PROJECTION_AND_MANIFEST_INCOMPLETE`.
ShellSet mechanics, OrbData, forward evolution, dt, and t1 were not run or created. The B-v2 candidate was not promoted.
