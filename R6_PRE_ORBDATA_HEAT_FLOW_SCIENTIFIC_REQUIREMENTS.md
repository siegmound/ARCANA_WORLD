# R6 PRE_ORBDATA heat-flow scientific requirements

**Decision:** R6_PRE_ORBDATA_HEAT_FLOW_REQUIREMENTS_DECOMPOSED__ARCHITECTURE_UNSELECTED

This is A0.3 decomposition only. It selects neither values nor a heat-flow architecture and does not promote PRE_ORBDATA.

## Current T0 authority and later field correction

The semantic adjudication remains R6_PRE_ORBDATA_HEAT_FLOW_SEMANTICS_PARTIALLY_ADJUDICATED__SOURCE_AMBIGUITY_REMAINS. The current v2 realization reports RATIFIED_FOR_T0_MATERIALIZATION, while canonical_status remains CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION.

Later v2 artifacts supersede the older blanket statement that no heat-flow-related T0 field exists: continental_reference_surface_heat_flow_w_m2 and continental_thermal_domain_id are materialized on cell support. This is a partial continental reference, not complete global ocean-plus-continent flux and not a complete FEG nodal field. The specialist-materialization report says global heat flow is missing, ocean heat flow is missing, lineage per node is not assembled, and status is INCOMPLETE_CONTINENTAL_SUPPORT_ONLY (R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.json: global_heat_flow; Markdown lines 19, 63). PRE_ORBDATA remains blocked.

The selected GDH1 configuration is for the ocean water-loaded age-depth/elevation component. It does not automatically select an oceanic heat-flow law. Ocean thermal profile and age-derived heat flow remain pending (R6_T0_B_PANGAEA_LIKE_V2_GDH1_MODEL_CONFIGURATION.json; R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.json: oceanic_thermal_state).

## Existing T0 fields and their limits

| Field | Can constrain | Cannot establish by itself |
|---|---|---|
| physical_crust_domain_id | Ocean/continent routing masks | Flux magnitude or physical flux law |
| oceanic_lithosphere_age_ma | Input and provenance for a selected ocean age-dependent model | Law, coefficients, age-zero meaning, continental flux |
| crustal_thickness_m | Layer geometry for a selected coupled geotherm model | Surface flux magnitude |
| continental_reference_lithosphere_thickness_m | Continental profile geometry where a model uses it | Flux; stock sArray does not consume this field |
| continental_reference_surface_heat_flow_w_m2 | Partial continental reference targets, if governed as such | Ocean flux, global nodal field, spatial variability |
| continental_thermal_domain_id | Lookup support for continental reference values | Within-domain variation or a flux law |
| Elevation/bathymetry | Surface geometry and the elevation input to ShellSet's q-limit rule; depth only in models that explicitly use it | Flux magnitude or age-to-flux relation |
| Plate topology/kinematics | Provenance/support for authored age and future history-model inputs | Ridge classification, spreading history, or flux law without an authorized model |

The v2 age generator is a monotone distance transform from selected divergent-source boundaries and makes no constant spreading-rate claim. Existing age is a useful physical primitive for a selected model, not a determined flux field (R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json: derived_fields.oceanic_age).

## Required scientific decisions

The machine-readable companion assigns one or more requested classifications to each item.

1. **T0 physical heat-flow representation** — Decide whether the governed quantity is a complete explicit field, partial reference constraints, or specialist-derived state. Specify support, masks, units, provenance, unknown handling, and whether continental reference flux is actual input, calibration target, or validation-only. Classifications: NEW_ARCANA_PHYSICAL_MODEL_REQUIRED, ARCANA_EXISTING_FIELD_CAN_CONSTRAIN, UNRESOLVED.
2. **Oceanic derivation** — Decide whether flux is explicit or derived from existing age, select/version any cooling model, establish its age range, and distinguish it from GDH1 bathymetry unless evidence establishes coupling. Classifications: LITERATURE_CONSTRAINT_REQUIRED, ARCANA_EXISTING_FIELD_CAN_CONSTRAIN, NEW_ARCANA_PHYSICAL_MODEL_REQUIRED, DEFER_TO_MATERIAL_THERMAL_STAGE, UNRESOLVED.
3. **Continental derivation** — Decide whether the existing domain-reference flux is final T0 flux or constrains a separately selected geotherm model. Define domain transitions and variability. Classifications: ARCANA_EXISTING_FIELD_CAN_CONSTRAIN, NEW_ARCANA_PHYSICAL_MODEL_REQUIRED, LITERATURE_CONSTRAINT_REQUIRED, DEFER_TO_MATERIAL_THERMAL_STAGE, UNRESOLVED.
4. **Age zero** — Give 0 Ma an authorial meaning and govern model behavior at that boundary. Qualified ShellSet assigns qLim1 for age <= 0 when the ocean route runs; that is implementation behavior, not proof of physical meaning. Classifications: NEW_ARCANA_PHYSICAL_MODEL_REQUIRED, LITERATURE_CONSTRAINT_REQUIRED, ARCANA_EXISTING_FIELD_CAN_CONSTRAIN, UNRESOLVED.
5. **Material properties** — Constrain material-specific conductivity, expansion, heat production, surface/reference temperature, temperature limits, adiabat parameters, and correlations. Domains and thicknesses organize this work but do not provide the properties. Classifications: LITERATURE_CONSTRAINT_REQUIRED, DEFER_TO_MATERIAL_THERMAL_STAGE, UNRESOLVED.
6. **q-limit governance** — Decide whether qLim0, dQL_dE, qLim1 are retained, bounded, or replaced as qualified ShellSet controls. They affect flux, and qLim1 also supplies the age-zero branch. Classifications: SHELLSET_MODEL_CONFIGURATION_ONLY, NUMERICAL_SENSITIVITY_REQUIRED, UNRESOLVED.
7. **Geothermal corrections** — After the thermal law and parameters are governed, decide whether ShellSet's heat-flow correction to meet its adiabat target belongs in T0 derived state or conflicts with explicit input. Measure correction size and stability. Classifications: DEFER_TO_MATERIAL_THERMAL_STAGE, SHELLSET_MODEL_CONFIGURATION_ONLY, NUMERICAL_SENSITIVITY_REQUIRED, UNRESOLVED.
8. **Uncertainty and sensitivity** — Separate input, material-parameter, and model-form uncertainty. Define deterministic sensitivity/ensemble ranges, correlations, diagnostics, and selective-replay behavior. Classifications: NUMERICAL_SENSITIVITY_REQUIRED, LITERATURE_CONSTRAINT_REQUIRED, ARCANA_EXISTING_FIELD_CAN_CONSTRAIN, UNRESOLVED.

## Candidate architectures; no selection

| Dimension | A. Explicit governed T0 heat-flow field | B. Derive from governed primitives/model |
|---|---|---|
| Required data | Complete global flux on canonical support or validated FEG projection; ocean/continent masks; units, lineage, uncertainty; exact-zero-safe interface | Domain masks; ocean age/history; continental structure/reference; material properties, heat production, boundaries; versioned model and projection |
| Existing T0 reuse | Continental reference flux can constrain or seed continental coverage only if governance promotes its role; ocean flux is absent | Can use domain, age, crust thickness, continental domain/reference flux, lithosphere thickness and elevation in justified roles; none alone yields global flux |
| Assumptions | Supplied flux is authoritative T0 state or named upstream model output; precedence needed if recomputed for checking | Selected laws map primitives and specialist configuration to flux; ocean and continent may need separate branches |
| Provenance | Per-region/node lineage to authored field, reference, model, and projection | Model/config version and complete input identities; flux is derived state |
| Uncertainty | Spatial field uncertainty/covariance plus model uncertainty | Propagate primitive, parameter, and model-form uncertainty/correlation |
| Selective replay | Supports regional updates with stable tiles and lineage; opaque raster makes invalidation harder | Supports deterministic dependency-aware recomputation and affected-region invalidation |
| T0 to T1 | Provides initial state but no temporal evolution law | Supports recomputation only when temporal laws and forcing/history are defined |
| Duplicate-state risk | High if authoritative flux is also independently recomputed; give each stored field one role | Lower if flux is only a derived cache; keep continental reference flux distinct as constraint/reference |

Both require complete support, category-safe routing, provenance, uncertainty, a zero-sentinel-safe adapter, deterministic projection, and explicit T0-to-T1 semantics before evolution. Selection criteria are physical authority, consistency with continental references, ocean model and age-zero evidence, material-property support, uncertainty propagation, replay behavior, and state-versus-derived clarity.

## Research questions for literature/web phase

Hand these questions to research without asking it to select ARCANA values:

1. Which published ocean plate-cooling formulations defensibly derive surface heat flow over ARCANA's governed age range? Provide primary citations, equations, units, assumptions, limits, alternatives, and parameter uncertainty.
2. Does the selected GDH1 water-loaded age-depth configuration imply/share a heat-flow law, or are they independent? Compare primary equations and conventions.
3. What physical meaning and limiting behavior are supported at ocean age 0 Ma, and how can valid new lithosphere be distinguished from ridge/interface sentinels?
4. Which continental geotherm/heat-flow models suit the authored thermal domains, and what inputs turn reference fluxes into spatial fields?
5. What material-specific evidence constrains conductivity, volumetric expansion, radiogenic production, and thermal-profile parameters, including temperature/depth dependence and covariance?
6. What source rationale supports qLim0, dQL_dE, qLim1 as safeguards versus consequential model bounds, especially qLim1 as the age<=0 output?
7. How sensitive are flux/geotherm outputs to model form, age uncertainty, material properties, q limits, and consistency corrections?
8. What methods map cell heat-flow fields to the 64,442-node sphere without false resolution, category smearing, or lineage loss?
9. What evidence distinguishes continental reference flux as direct T0 state, calibration target, or validation-only constraint?
10. Which thermal variables must update from T0 to T1 under either architecture, and what temporal laws, forcing, and selective-replay invalidation rules are required?

## Preserved gates

PRE_ORBDATA_ready=false; t0_orbdata_executed=false; shellset_mechanics_authorized=false; dt_selected=false; t1_created=false; forward_evolution_authorized=false.

No values or architecture were selected. OrbData/SHELLS were not run and ShellSet was not modified. No commit or push was made.
