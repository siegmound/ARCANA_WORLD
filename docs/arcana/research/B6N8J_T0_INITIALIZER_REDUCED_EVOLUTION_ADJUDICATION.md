# R6 B6N8-J — T0 initializer and reduced evolution adjudication

**Baseline:** branch r6/b6n8j-t0-initializer-reduced-evolution-adjudication, commit 5196b89d8f24cce528a84a9cf6f01c93457a8a24 (B6N8-I attestation commit).

**Verdict:** PASS_B6N8J_MODEL_FAMILY_SELECTED_T0_INITIALIZER_CONDITIONALLY_READY_T0_TO_T1_EVOLUTION_AUTHORITY_REMAINS

B6N8-J resolves one model-form gap: the later R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING.json is distinct from the rejected steady column. It is selected for a **noncanonical, replayable T0 reference profile**, conditional on explicit native-support/material-role binding and provider validation. It is not selected as a T0-to-T1 integrator and publishes no physical state.

## Authority and candidate reconciliation

B6N8-I remains authoritative for its stage: no initializer was selected there; material applicability and T0-to-T1 evolution remained open. B6N8-J evaluates the existing transient-coupling contract, whose decision is R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING_CLOSED__CONFIG_V1_AND_IMPLEMENTATION_READY. It defines:

- a transient HWR-2 ocean/ridge profile and Hermite layer projection;
- a separate fixed-geometry continental transient-rate profile;
- model-specific surface/base rules, deterministic tolerances, fail-closed policy, and static profile/sensitivity checks.

This later recipe repairs the steady-column representation incompatibility; it does not contradict the finding that the steady piecewise column failed. The transient recipe is adopted only as a specialist reduced-model reference initializer. Its material tuples are not observed lithology, canonical material identity, or newly selected parameters. A role-to-native-support join remains necessary.

| Candidate | Adjudication |
|---|---|
| Direct prescribed T0 profile | Unavailable |
| Prescribed analytic or steady column | Rejected; no direct profile authority and the existing steady candidate failed |
| Existing transient ARCANA coupling | Selected for reduced T0 reference-profile construction only |
| External profile or new authorial numeric T0 primitive | Not selected or created |

For continents, the existing recipe retains authored q, TSurf, cellwise crust thickness, and authored total thickness H. It solves the effective column Tdot closure for T_LAB=T_ad(H), then derives a continuous Moho profile. Tdot is an instantaneous closure, expressly not a temporal-history primitive. Positive-age ocean uses the existing HWR-2 age solution. Ridge age zero uses the source-defined effective-age inversion without changing authored age. The model's constant-per-layer k/rho/Cp and radiogenic A remain specialist configuration; kappa is derived as k/(rho Cp). No composition is inferred from crust-domain ID or thermal class.

**T0 readiness:** conditionally constructible as a replayable reduced-model profile after exact support/material-role joins and provider validation. No T0 profile or state was generated here. The profile is not asserted to be an observed or fully resolved planetary geotherm.

The selected scope is one reduced column per supported native T0 source cell, preserving explicit validity/UNKNOWN masks. There is no interpolation, extrapolation, or resolution promotion; mapping those columns to a Buck section remains B6N8-F work.

## Boundaries, LAB, and circularity

For this initializer only, the model-specific thermal base is authored continental H with T(H)=T_ad(H), or the ocean HWR profile/adiabat crossing (with the source's finite-plate endpoint rule). This does not select a universal physical LAB or equate thermal, mechanical, rheological, seismic, compositional, and numerical-domain boundaries. A later Buck/mechanical provider still needs its own section geometry and thickness authority.

The T0 upper boundary uses existing specialist TSurf=280 K and the governed domain-specific heat-flow rule. It is not a global 210 Ma climate field. The initializer does not provide complete ARCANA-world boundary histories over T0-to-T1; no constant-world-boundary assumption is made.

The initializer dependency graph is acyclic: independent geometry and material references plus the HWR adiabat feed profile construction; the thermal base is imposed or diagnosed afterward. There is no LAB iteration or rheology feedback.



## Temporal and causal correction

B6N1 governs the event at T1, not at T0 and not within the open T0-to-T1 interval. The sequence is T0 → pre-event interval evolution → T1 PRE_EVENT → B6N1 activation → T1 POST_EVENT. The event and the B6N2 kinematic authority do not provide forcing inside T0-to-T1. This corrects the earlier task-prompt premise; event placement is no longer listed as a residual blocker.

The correction does not establish conduction-only sufficiency. J10 remains unresolved because pre-event boundary histories, material applicability, geometry/support/configuration evolution, and the sufficiency of the reduced conduction model remain open. Structural geometry remains EVOLUTION_UNKNOWN. A frozen geometry in a future prototype is only MODEL_CONFIGURATION_APPROXIMATION. Generic pre-event advection/upwelling and other omitted processes remain unknown unless independently bounded; post-activation extension and post-activation mechanical-work heating are excluded from the open interval.

Activation is a causal transition, not authority for a thermal jump. No reset, pulse, geotherm change, or material-property jump is introduced. A future T1 PRE_EVENT thermal payload may be reused as T1 POST_EVENT thermal payload only if no separate instantaneous thermal transition is authorized; no such state is generated now.

## T0-to-T1 is not executable

The candidate equation rho Cp dT/dt = div(k grad T) + A is not selected as a complete physical evolution model. The continental Tdot closure is not an integration recipe. HWR is a function of its ocean-age coordinate, but ARCANA has not bound age/support/new-crust evolution over this world interval. Boundary histories, structural configuration evolution, and omitted-process sufficiency remain open.

| Omitted process | Status |
|---|---|
| Post-activation extension-related vertical motion from B6N1/B6N2 | Not applicable within open T0-to-T1; event/kinematics begin at endpoint T1 |
| Other/background advection or vertical motion independent of post-event kinematics | Unknown; no source-backed bound established |
| Material-boundary or geometry motion | EVOLUTION_UNKNOWN; no invariance inferred |
| Lower-crust flow | Not required by T0 conductive initialization; physical absence not established |
| Mantle upwelling | Unknown; no independent pre-T1 authority or bound identified; not sourced from B6N2 post-event kinematics |
| Post-activation mechanical-work heating | Not applicable within open T0-to-T1; activation is at endpoint T1 |
| Other pre-event thermal/mechanical work | Unknown; not part of initializer and not bounded |
| Radiogenic heating | Existing source term is included in initializer; temporal history not separately bound |

## 27 kyr diagnostic

For 27,123.40515632 years (8.5594957056e11 s), the characteristic length sqrt(kappa*t) is 0.67–1.09 km over existing crust-reference k/(rho Cp) range corners and 0.78–1.00 km over the existing mantle kappa range. Using 2 sqrt(kappa*t) as the error-function e-fold scale gives 1.33–2.18 km (crust) and 1.55–2.00 km (mantle). These use prior specialist ranges only as a diagnostic; target-material applicability remains conditional. They do not prove steady state, constant boundaries, frozen geometry, or negligible advection/other processes.

## Gate result and remaining closure

The separate J1–J14 outcomes are recorded in [the readiness overlay](B6N8J_B6N8I_READINESS_OVERLAY.json). The initializer family, model-specific thermal base, T0 surface boundary, and constant-per-reference-layer properties are selected for T0 reference-profile construction. T0 profile generation is conditional; conduction sufficiency and T0-to-T1 evolution remain unresolved; T1 thermal state and first Buck thermal readiness remain false. J14 is ready only for the T0 initializer component, not the full interval provider.

Exact residuals:

1. Bind native physical domains/support to reference-material roles without asserting composition.
2. Confirm whether the effective continental Tdot snapshot closure applies to the intended T0 profile; it is not an integration law.
3. Define pre-event surface/basal/q and ocean-age/support histories over T0-to-T1.
4. Determine the treatment/authority for pre-T1 geometry, support, and configuration evolution; preserve STRUCTURAL_GEOMETRY_T0_TO_T1=EVOLUTION_UNKNOWN. If later frozen for a prototype, label it MODEL_CONFIGURATION_APPROXIMATION.
5. Establish whether conduction-only pre-event evolution is sufficient or independently authorized physical coupling is required.
6. Bind uncertainty and validity and map the result to the eventual B6N8-F section support.

**Pre-T0:** the selected formula can produce a model-defined T0 profile without numerical stepping before T0, if authorized and fully bound. This does not establish that pre-T0 physical history is unnecessary: PRE_T0_HISTORY_REQUIRED=NOT_DEMONSTRATED; PRE_T0_HISTORY_PROVEN_UNNECESSARY=false.

**WORLD_HISTORY:** not accessed or changed; no inventory comparison. No canonical T0/T1 publication, provider, evolution, mechanics, forcing, dt2, or T2 was produced. No external research was needed for this authority adjudication; scale inputs came from existing ARCANA references.

## Validation

Static-only validation: source gate and B6N8-I/H lineage, transient-versus-steady contract reconciliation, temporal arithmetic, JSON/cross-file consistency, DAG acyclicity, UTF-8/LF, local links, portable paths, and whitespace. No runtime execution or production state generation.

## Non-actions

No new physical parameter; no T0/T1 state generation or publication; no T0-to-T1 evolution; no provider implementation; no Buck rheology/section/Ux/Xe/XL/strain-rate/forcing; no mechanics; no second dt/T2; no canonical forward propagation; no WORLD_HISTORY change.
