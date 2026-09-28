# R6 T0 FAIR ShellSet runtime binding and input readjudication

**Decision:** `R6_T0_SPECIALIST_RUNTIME_QUALIFIED_FOR_EXAMPLES_AND_ARCANA_CAPACITY__INPUTS_REMAIN_OPEN`

- FAIR evidence: `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json`; committed SHA256 `ab29de4577c4c4b007d41a7ac5567d7b287c7fed5dee3107aeb69dc35df1a350`.
- Evidence identity: `8265b998a8ddb8e3fdfd7371c9bfe076e6697fbbd7fcb922d77a37317ef59afe`.
- Runtime: upstream `e4a6fbd5997b6c4978924649dff1abab0c96ca57`, qualified `09a06ecd061f00b80a52af86e31d609ff5545a8b`, executable SHA256 `03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349`.
- Historical Windows observation: `PRESERVED_HISTORICAL_OBSERVATION; not current FAIR qualification`; preserved unchanged.
- Upstream examples qualified: **true**; ARCANA mesh capacity qualified: **true**.
- T0 input transformation authorization: **false**; T0 mechanics authorization: **false**.
- Cross-backend Intel/NVIDIA tolerance: `NOT_ADJUDICATED`.

## OrbData5 field behavior and ARCANA readiness

Pinned-source semantics are recorded from OrbData5.f90 and MOD_Data.f90 at the qualified upstream commit. PRE_ORBDATA nodal inputs, auxiliary grids, recomputed outputs, and final FEG fields are distinct contracts.

### PRE_ORBDATA FEG node inputs

Longitude/latitude, elevation, and heat flow. Any elevation exactly 0.0 sets `needE` and selects the stock ETOPO20 grid fallback; that Earth fallback is prohibited for ARCANA and an exact-zero physical elevation is ambiguous. Any heat flow exactly 0.0 sets `needQ`; only those nodes take the qArray/age-law fill branch. Nonzero heat flow is not globally overridden by age.

### OrbData auxiliary grid inputs

`aArray` and `cArray` are always read. `sArray` is used for the age >=200 Ma continental/unknown mantle path. `eArray` and `qArray` are conditional on exact-zero elevation/heat flow. The >=200 age value is an interface classification marker derived from governed land/ocean identity, never a physical continental age. Because bilinear age interpolation precedes classification, coastal category leakage remains an adapter qualification blocker.

### OrbData-derived output fields

OrbData ignores input FEG crustal thickness, mantle-lithosphere thickness, chemical_delta_rho, and cooling_curvature, then recomputes all four. Crust thickness comes from cArray; ocean mantle thickness uses the age model; continental/unknown mantle thickness uses stock sArray. Chemical density anomaly and cooling curvature are derived under model/material/thermal configuration, including delta_rho_limit.

### SHELLS_READY final FEG fields

Elevation, heat flow, crustal thickness, mantle-lithosphere thickness, chemical_delta_rho, and cooling_curvature must all be present in the final FEG.

| Field | Source behavior | Sentinel / route | ARCANA disposition |
|---|---|---|---|
| `elevation` | FEG nodal input. Any exact 0.0 sets needE and requests an elevation grid; stock copies Earth INPUT/ETOPO20.grd. | 0.0 IS SOURCE-DEFINED NEED_E GRID SENTINEL; genuine zero is ambiguous; Node value is used; zero invokes the auxiliary elevation-grid path. No bathymetry from age; complete elevation remains independent ARCANA physical state. | Complete governed ocean elevation and an ARCANA grid/adapter or qualified interface change are still required. |
| `heat_flow` | FEG nodal input. Any exact 0.0 sets needQ. Only zero-valued nodes enter qArray then conditional age-law fill; nonzero values skip that branch. | 0.0 IS SOURCE-DEFINED NEED_Q GRID SENTINEL; For heatFl==0: interpolate qArray; age<200 overrides with pinned ocean law; age<=0 uses qLim1; then apply heat-flow limits. Nonzero heat flow does not get age-overridden. Conditional zero-node fill only; age is not a global override. | A governed global heat-flow policy must ensure intended zero routing and provide ARCANA qArray whenever any node is zero. |
| `crustal_thickness` | Not a required PRE_ORBDATA nodal input; Assign always reads cArray and ignores the input FEG value. | Not applicable to FEG input; cArray is mandatory; Recomputed/interpolated from cArray each run. Output from governed ARCANA cArray input. | Governed crustal_thickness_m exists on cell support and can be exported deterministically without cell-to-FEG projection. |
| `mantle_lithosphere_thickness` | Not a required PRE_ORBDATA nodal input; Assign ignores input FEG value. Interpolated age selects the method. | Not applicable to FEG input; auxiliary age and continental path inputs govern; Age<200 Ma uses pinned ocean model; age>=200 Ma uses stock continental/unknown S-wave anomaly sArray path. Ocean thickness from age; continental stock path requires sArray, not prescribed ARCANA thickness. | Governed continental_reference_lithosphere_thickness_m is not consumed by stock OrbData. Require a qualified source generalization, governed equivalent producer, or retain blocker; no synthetic delta_ts inversion. |
| `chemical_delta_rho` | Not a PRE_ORBDATA sentinel/input. Assign initializes then derives/limits final value internally. | Not a PRE_ORBDATA sentinel; Derived/limited from structural/isostatic calculation and delta_rho_limit. Yes; ORBDATA_DERIVED_FROM_GOVERNED_INPUT + MODEL_CONFIGURATION_REQUIRED. | No independent raster required absent another governed contract; configure delta_rho_limit and material parameters. |
| `cooling_curvature` | Not a PRE_ORBDATA sentinel/input. Assign computes curvature from thermal/geotherm state. | Not a PRE_ORBDATA sentinel; Derived thermally and may modify mantle thickness while enforcing profile conditions. Yes; ORBDATA_DERIVED_FROM_GOVERNED_INPUT + MODEL_CONFIGURATION_REQUIRED. | No independent raster required absent another governed contract; thermal model and limits remain unselected. |

## Projection and FEG gates

- Projection: `OPTIONAL_FOR_ORBDATA_GRIDS; not a PRE_ORBDATA dependency` using existing shellset_mesh adapter project_cell_field_to_nodes; class `NUMERICAL_DERIVED_SUPPORT`.
- Cell-to-node projection is not required before OrbData for age or crust thickness when exported as auxiliary grids; the missing partition NPZ no longer blocks these inputs.
- PRE_ORBDATA ready/materialized: **false / false**.
- Auxiliary inputs ready: **false**; OrbData transformation ready: **false**.
- SHELLS_READY ready: **false**; mechanics authorized: **false**.

## Scientific blockers

- Author complete T0 ocean elevation/bathymetry with datum, support and uncertainty; OrbData age does not establish bathymetry generation.
- Resolve aArray coastal category-leakage qualification and governed ocean heat-flow/thickness parameters; age >=200 may only encode interface classification, not physical continental age.
- Constrain all nine reference material/thermal configuration families and numeric continuum rheology; no Earth defaults/OrbScore optimum.
- Resolve stock continental sArray incompatibility: governed ARCANA continental_reference_lithosphere_thickness_m is not consumed; choose qualified source generalization/equivalent producer or retain blocker.
- Close delta_rho_limit, material parameters, and thermal/geotherm controls for derived chemical_delta_rho and cooling_curvature outputs.

## Physical configuration

- Canonical values: `gMean=9.82 m/s²`, `radius=6371000 m`.
- Unresolved reference families: rhoBar_crust, rhoBar_mantle, rhoAst, rhoH2O, alphaT_crust_mantle, conductivity_crust_mantle, radiogenic_heat_production_crust_mantle, surface_temperature_and_temperature_limits, TADIAB_GRADIE_ZBASTH.
- Rheology: CFRIC, FFRIC, BIOT, BYERLY, ACREEP(1), ACREEP(2), BCREEP(1), BCREEP(2), CCREEP(1), CCREEP(2), DCREEP(1), DCREEP(2), ECREEP; `nFl=0`, FFRIC and BYERLY inactive; no numeric baseline selected.
- No Earth defaults or Earth OrbScore optimum were used.

## Implementation blockers

- Implement and qualify deterministic OrbData-compatible aArray/cArray exporters with source support and lineage; no resolution increase.
- Qualify age-grid coast classification strategy because bilinear aArray interpolation precedes the 200 Ma branch.
- Select ARCANA eArray/qArray adapter path if any FEG node uses exact-zero elevation/heat flow.
- After required scientific fields close, materialize PRE_ORBDATA and execute the prepared FAIR OrbData validation; do not run ShellSet mechanics here.
- Global sphere uniqueness/reference-frame and rigid-rotation nullspace qualification remains open.

**FAIR validation command after input gates close:** `bash scripts/r6_t0_fair_validate_orbdata_result.sh`.
Required result manifest: `R6_T0_ORBDATA_FAIR_RESULT_MANIFEST.json (not yet present; PRE_ORBDATA is not ready)`.

**Next action:** Resolve the authorial T0 ocean elevation/bathymetry and thermal-model configuration first. When a complete governed PRE_ORBDATA manifest exists, run the prepared FAIR identity/input validation script; mechanics remain separately unauthorized.

No OrbData or mechanics execution, forward evolution, `dt`, or `t1` was performed or created.
