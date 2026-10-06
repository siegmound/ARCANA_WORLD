# B6N8-E — Initialization / Prehistory Authority Audit

## Decision

**PASS_B6N8E_AUTHORITY_AUDIT__NO_PRE_T0_HISTORY_REQUIREMENT_PROVEN__T0_INITIALIZATION_AND_T0_T1_EVOLUTION_GAPS_REMAIN**

Initialization-specific implementability: **NO_CURRENTLY_DEFENSIBLE_INITIALIZATION**. Authority audit only; no implementation or simulation.

## Baseline and time frame

- Branch: r6/b6n8e-initialization-prehistory-authority
- Audited commit: 771b8d3ea9706eb0d45903e72354b304e6979e69 (B6N8-D attestation commit)
- B6N8-D qualified research source: 88298ef948b6dc17a14961f6a43154cca4915d05
- T0 = 210.0 Ma; T1 = 209.97287659484368 Ma. Elapsed = 0.02712340515632 Ma = 27,123.40515632 years.

The proposed split is supported: missing T1 state does not imply a multi-million-year reconstruction before T0. Current authority neither proves pre-T0 history is required nor authorizes a T0 equilibrium geotherm. An authorized T0 initialization could avoid explicit pre-210 Ma simulation; material/boundary assumptions, validity and uncertainty must first be bound.

## T0 authority

WORLD_HISTORY retains T0 geography, land/ocean, province, topography, tectonic partition/geometry and plate kinematics. Relevant UNKNOWN domains remain explicit. No complete canonical T(z), Moho/LAB thermal state, density profile, composition-to-rheology binding or lower-crust flow state was found. Read-only inventory: 46 files, 1,275,143 bytes; same-method per-path signature: 5a84ed6928f252d163c18864e62f9458b6873f98f5e628a074ba7a4701846d1c.

B_PANGAEA_LIKE_V2 has authored candidate fields for crust domain/thickness, continental reference lithosphere thickness, continental reference heat flow, oceanic age and geography. Materialization remains CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION. Continental q is ratified only on its producing class/cell support; it is a boundary scalar, not T(z). Oceanic age is an input, not a flux law.

## Thermal and material authority

The transient thermal-coupling artifact supplies a candidate analytical recipe and calls its configuration stage ready to construct. It is not proof of a qualified canonical T0 profile or physical T0-to-T1 transition: PRE_ORBDATA/runtime gates remain false and implementation, support and qualification work remains. Thermal reference-column and OrbData closures retain material/column compatibility blockers. A0.6D/G references exist, but material authority says values selected while compatibility remains blocked. These are specialist inputs, not canonical spatial material/rheology state.

Thus flux, one temperature reference or selected mantle properties do not establish a Buck initial state. Full profile, material mapping, coupled boundaries, density structure, brittle/ductile laws and lower-crust closure remain unbound or unqualified. Buck steady geotherm is model authority, not ARCANA T0 authority. Buck Table 2/3 values are not portable ARCANA parameters without separate justification.

## T0 to T1 evolution

No qualified physical thermal/structural evolution driver for this 27,123-year interval was found. Plate kinematics alone does not evolve temperature, thickness, density, composition or rheology. Symbolic conductive length is Ldiff approximately sqrt(kappa times delta_t); applicable diffusivity and geometry/support are not jointly qualified, so duration alone cannot prove negligible change. Structural change needs an authorized physical law.

Minimum chain: accepted T0 geometry/material map plus authorized T0 profile initialization, followed by finite-interval reduced evolution, producing T1 state and uncertainty. B6N8-F independently owns B6N2-to-Buck section/forcing mapping. No dt2, T2, propagation or mechanics was performed.

## Minimum upstream scope

The smallest plausible scope is a LITHOSPHERIC_THERMAL_STRUCTURAL_STATE T0 contract and derivation recipe, not a broad geodynamics model or duplicate per-node primitive by default. Bind geometry/support, material identity separately from rheology, whether T(z) is authored or derived, boundaries/production, constitutive laws, uncertainty and validity. Keep deterministic profiles replayable; persist causal endpoints if path-dependent; do not checkpoint every numerical step.

Authorial decisions: permit/reject steady T0 initialization; map ARCANA domains to material families; bind thermal/rheology laws and uncertainty; govern what evolves T0-to-T1; decide lower-crust flow/weakness only where selected model requires it.

## Artifacts and evidence

- [Initial-state gap matrix](B6N8E_BUCK_INITIAL_STATE_GAP_MATRIX.json)
- [T0-to-T1 evolution requirements](B6N8E_T0_T1_EVOLUTION_REQUIREMENTS.json)
- [Upstream physical-state requirements](B6N8E_UPSTREAM_PHYSICAL_STATE_REQUIREMENTS.json)
- [B6N8-D attestation](../qualifications/R6_B6N8D_ATTESTATION.json)
- [Canonical initial-state package](../../../R6_CANONICAL_INITIAL_STATE_PACKAGE.json)
- [Material-reference authority](../../../R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_AUTHORITY.json)
- [Thermal reference-column contract](../../../R6_PRE_ORBDATA_THERMAL_REFERENCE_COLUMN_CONTRACT.json)
- [Transient thermal coupling](../../../R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING.json)
- [Continental heat-flow ratification](../../../R6_PRE_ORBDATA_CONTINENTAL_HEAT_FLOW_AUTHORIAL_RATIFICATION.json)
- [T0 materialization report](../../../R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json)

## Gates

WORLD_HISTORY remained read-only. No parameter/profile/prototype/mechanics was executed and B6N8-F remains open. Preserved gates: PRE_ORBDATA_ready=false; t0_orbdata_executed=false; shellset_mechanics_authorized=false; dt_selected=false; no T1 thermal profile was created by this stage; forward_evolution_authorized=false; physical_rift_model_selected=false; physical_rift_model_qualified=false; prototype_implemented=false; new_physical_parameter_selected=false; SECOND_DT_SELECTED=false; dt2_years=null; T2_CREATED=false; B6O_authorized=false; mechanics_executed=false; canonical_forward_propagation_executed=false; topology_transition_executed=false; support_remapping_executed=false; WORLD_HISTORY_changed=false; B6N8-F remains open.
