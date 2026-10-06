# B6N8-L — Boundary history, support, material applicability, and temporal adapter

## Decision

**PASS_B6N8L_BOUNDARY_SCENARIOS_AUTHORIZED_SUPPORT_APPLICABILITY_REMAINS**

B6N8-L closes a finite, deterministic *reduced-model scenario envelope* on explicitly eligible native columns. It does not establish physical boundary histories, natural cellwise composition, global support coverage, conduction sufficiency, or a Buck section. The exact gate/readiness records are in [the B6N8-K overlay](B6N8L_B6N8K_READINESS_OVERLAY.json), [the temporal adapter](B6N8L_BOUNDARY_TEMPORAL_ADAPTER.json), [the support/material matrix](B6N8L_SUPPORT_MATERIAL_BINDING_MATRIX.json), and [the provider input contract](B6N8L_THERMAL_PROVIDER_INPUT_CONTRACT.json).

## Baseline and inherited authority

- Branch: `r6/b6n8l-boundary-history-support-applicability`; B6N8-K attestation baseline: `c18fedb3f3396ea9ac04bc925e6391bad23767d1`.
- The attested B6N8-K source is `de9e1f5e7aeed9de426d0e570c1d19fb4af3b739`; its verdict remains `PASS_B6N8K_REDUCED_EVOLUTION_CONDITIONALLY_AUTHORIZED_BOUNDARY_HISTORY_BINDING_REMAINS`.
- T0 is 210.0 Ma; T1 is 209.97287659484368 Ma; elapsed interval is 27,123.40515632 years. Order remains T0 → reduced pre-event evolution → T1 PRE_EVENT → B6N1 activation → T1 POST_EVENT → B6N2 post-event kinematics. B6N2 provides no T0–T1 forcing.
- Frozen T0 geometry/configuration remains a reduced-model approximation. `STRUCTURAL_GEOMETRY_T0_TO_T1=EVOLUTION_UNKNOWN`; neither geometry nor material/support invariance is claimed as physical fact. The selected B6N8-J initializer family is preserved; no T0 profile exists.

## Support and role mapping

The support inventory is the B-v2 native 180×360 grid (64,800 cells). The current census identifies 14,258 continental thermal-class cells and 50,542 ocean cells. Of the ocean cells, 49,362 positive-age cells are admitted by the current HWR support audit; 1,072 positive-age cells remain unresolved; 108 selected ridge cells have authored age zero. These counts describe candidate inputs, not Buck-target selection.

For the reduced column model, categorical `physical_crust_domain_id=1` maps to an oceanic crust *reference role* and IDs 2–6 to a continental crust *reference role*. The layer below the crust may use the shared effective lithospheric-mantle reference role where the corresponding authored/HWR geometry has positive residual thickness. This is a `REDUCED_MODEL_ADAPTATION`, not an inferred per-cell mineral composition. `continental_thermal_domain_id` independently selects authored continental q and total reference thickness; it does not select composition. IDs remain categorical and are never interpolated.

The 34 transitional-margin cells in physical domain 2 can enter the continental reduced-model branch only where the required thermal class, geometry, and property joins are valid. This does not assert that those cells are physically continental throughout the interval. Missing or mixed categorical support fails closed. No interpolation, resampling, or resolution promotion is part of L.

## Properties and source terms

Role-scoped reference tuples already exist for `k`, `rho`, and `Cp`; `kappa` is derived only as `k/(rho*Cp)` from the same coherent tuple. Existing B6N8-I ranges remain sensitivity inputs, not probability distributions. Their applicability is conditional on the per-support role join and later provider validation; a reference value alone does not make a column executable.

`A_C` and `A_M` are authorial specialist *model source configuration* references, not canonical geochemical fields or reconstructed histories. A finite test may bind their existing values/ranges as explicit fixed-configuration scenario axes. That makes their model-input role executable for the scenario, but does not prove physical radiogenic production constant over 27 kyr. Zero is an explicit sensitivity endpoint where governed, never a default. Radiogenic production, surface heat flux, and geotherm remain distinct quantities.

## Boundary histories and adapters

**Surface.** No physical T0–T1 surface-temperature trajectory is present. Existing `TSurf=280 K` and 250–300 K bounds support deterministic `LOW/REFERENCE/HIGH` held-*model-boundary* scenarios. They do not assert constant physical surface temperature or a climate history. Continental q remains the authored T0 boundary on its exact thermal-class support (0.045/0.060/0.085 W m⁻²); holding it is a reduced-model scenario, not a physical q(t). The source gives no numeric q uncertainty interval. Ocean q is HWR-2 output only for valid positive model age and support.

**Lower/model base.** Continental initializer base uses authored total model thickness `H` and the existing adiabat relation to derive the model-boundary temperature from a coherent tuple. `H` and that boundary are not a selected physical LAB or its history. On eligible positive-age ocean columns, use the coupled HWR-2 `Tb/zp` base only as its model configuration requires; `zp` is not a universal LAB. Existing parameter-range endpoints may be exercised as separate deterministic sensitivity cases; no correlations or probabilities are invented.

**Ocean age.** For admitted positive-age material columns, the deterministic reduced adapter is `age_model(t)=age_T0+(210.0 Ma−t_age_Ma)` for times from T0 to T1. It is a model-coordinate rule for a frozen column, not a spreading-rate law, Eulerian age-field trajectory, or proof of stable physical support. HWR remains restricted to `t>0`. The 108 age-zero ridge cells are excluded from the T0–T1 adapter: their existing effective-age inversion is only a T0 profile index. The 1,072 unresolved cells also remain excluded; no inference from divergent-boundary adjacency is allowed.

## HWR semantic crosswalk

The HWR-2 contract retains its finite-thickness plate-cooling meaning and versioned parameters. `k`, `rho_m`, `Cp`, `alpha`, `Tb`, and `zp` remain specialist model configuration/reference inputs with their governed units/ranges. `kappa` is derived coherently. `t` is positive HWR model age, not elapsed world time until the explicit material-column adapter maps it. HWR q is conductive model heat flux under its declared formulation, not an implicit total hydrothermal heat-loss field. `zp` is the finite-plate model base; the initializer’s LAB crossing is a derived thermal criterion and not a universal physical interface. Exact field-by-field status and lossiness are represented in the adapter artifact; original HWR authority is unchanged.

## Provider and Buck interfaces

The provider input **schema is complete** for the scoped envelope, but the required T0 initial-condition value is unavailable. Its contract now requires a support-indexed `T(z,T0)` profile (or the selected initializer's replayable profile output) at 210 Ma, produced under `R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING`; that profile is not materialized, and the initializer provider is not implemented or validated. Thus `INPUT_SCHEMA_COMPLETE` does not imply `INPUT_VALUES_AVAILABLE` or `PROVIDER_EXECUTABLE`; provider inputs are not yet complete for execution and T0→T1 evolution cannot run. Global inputs are additionally incomplete: the 1,072 cells and ridge temporal path are excluded, and per-cell applicability validation is not performed. No T1 profile or time integration has been generated or executed.

A future output must retain native cell IDs and lineage, categorical domain/class IDs, vertical datum and interfaces, per-layer material-role/config IDs, `T(z)` and units, scenario/recipe identity, uncertainty dimensions, validity, and UNKNOWN/exclusion status. It must not emit a canonical material ID at an integration point or claim new spatial resolution. Thermal-output support is not Buck-section authority. Extracting a profile for a section requires the separate B6N8-F section authority and, where supports differ, a governed aggregation/interpolation rule. No section, Ux, Xe, XL, or strain rate is selected here.

## L1–L14 closure

| Gate | Result | Scope |
|---|---|---|
| L1 Thermal support domain | PASS_SCOPED | Native support classes/counts defined; not global coverage. |
| L2 Support/material mapping | PASS_SCOPED_REDUCED_MODEL_ADAPTATION | Reference roles assigned categorically; no composition inference; joins still require validation. |
| L3 Property applicability | CONDITIONAL | References exist; per-support role applicability remains conditional. |
| L4 Radiogenic temporal role | CONDITIONAL_SCENARIO | Fixed model-source scenarios allowed; physical history UNKNOWN. |
| L5 Surface boundary temporal authority | PASS_SCOPED_MODEL_SCENARIOS | Finite held boundary scenarios, not physical histories. |
| L6 Lower boundary temporal authority | PASS_SCOPED_MODEL_SCENARIOS | Initializer-compatible model-base scenarios, not physical LAB history. |
| L7 HWR temporal adapter | PASS_SCOPED_POSITIVE_AGE_ONLY | Positive-age admitted material columns only. |
| L8 Ocean support eligibility | PARTIAL_FAIL_CLOSED | 49,362 conditionally eligible; 1,072 unresolved and 108 ridge cells excluded. |
| L9 Support temporal identity | PASS_SCOPED_MODEL_APPROXIMATION | Fixed model support only; physical invariance UNKNOWN. |
| L10 Boundary scenario envelope | PASS_SCOPED | Finite endpoints/reference cases from existing authorities, no invented bounds/probabilities. |
| L11 Temporal adapter contract | CONDITIONAL | Complete for the admitted scenario envelope only. |
| L12 Buck thermal-output interface | PASS_INTERFACE_ONLY | Native profile metadata defined; section mapping remains separate. |
| L13 Provider inputs complete | INPUT_SCHEMA_COMPLETE_VALUES_UNAVAILABLE | Required T0 initial condition is pending materialization and initializer-provider validation; no execution readiness. |
| L14 Ready for conduction-sufficiency adjudication | CONDITIONAL_T0_INITIAL_CONDITION_PENDING | The scenario envelope defines the next adjudication scope; computation consuming T0→T1 evolution waits for the initial profile and validation. |

## Handoff and remaining gaps

The next closure can test conduction sufficiency on eligible native columns using the declared finite material/property and boundary/source scenario axes. It must compare temperature differences at explicitly authorized depths and a declared profile norm on common vertical support; after B6N8-F chooses support, it may also compare the recovered Buck force-relevant thermal contribution. No numerical acceptance tolerance is selected here. Keep physical histories, missing support and parameter uncertainty as separate questions.

Still open: executable per-cell applicability joins/provider validation; physical surface and radiogenic histories (if required beyond model scenarios); temporal treatment of 1,072 ocean cells and 108 ridge cells; conduction-only sufficiency and its downstream tolerance; and the B6N8-F section/support extraction authority. The L result does not authorize state generation or production execution.

## Safety and non-actions

`WORLD_HISTORY_accessed=false`; no canonical state was read or changed. No new physical parameter, boundary value, acceptance tolerance, or thermal equation was selected. No T0/T1 state was generated; no provider or evolution was run; conduction was not declared sufficient; physical LAB and Buck section/mechanics were not selected/executed; no dt2, T2, or forward propagation was authorized. `B6N2_FORCING_DURING_T0_T1=false`.
