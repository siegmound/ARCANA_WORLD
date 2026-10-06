# B6N8-M — Conduction sufficiency prerequisite and identifiability audit

## Baseline and authority

- Branch: r6/b6n8m-conduction-sufficiency-identifiability; governing B6N8-L R1 attestation commit: 725974b2c5b2635f94b61de7342132e54fdb7f92.
- B6N8-L qualified source: c0584aff534e328b4c0f682c26e2690e45efe202; verdict remains PASS_B6N8L_BOUNDARY_SCENARIOS_AUTHORIZED_SUPPORT_APPLICABILITY_REMAINS.
- B6N8-K qualified source: de9e1f5e7aeed9de426d0e570c1d19fb4af3b739; candidate operator: rho*Cp*dT/dt = div(k grad T) + A.
- T0 = 210.0 Ma; T1 PRE_EVENT = 209.97287659484368 Ma; interval = 27123.40515632 years (855949570561.084 s). B6N2 is post-event; no B6N2 forcing applies during T0→T1.
- The required input T0_thermal_initial_condition is a support-aware T(z,T0) at 210 Ma, but its value is unavailable and provider is not executable.

## Sufficiency meanings and observables

Model-form sufficiency asks whether the conduction operator represents relevant physical processes. Thermal-state accuracy asks whether T1 observables meet an authorized error rule. Downstream Buck relevance asks whether thermal error compromises Buck force/rheology/buoyancy on the selected section. Support-coverage sufficiency asks whether the intended supports have valid joined inputs or explicit exclusions. These are separate claims.

B6N8-L names temperature differences at authorized depths, a profile-difference norm on common vertical support, and a later Buck thermal-force contribution after B6N8-F selects support. B6N8-D ties T(z) to the Buck Eq. 1; the profile affects integrated yield strength (ENV), Moho gradient/lower-crust closure (Eq. 10), density-moment buoyancy (Eq. 11), thermal buoyancy (A3–A4), and signed force changes (DF). Target depths, section, norm/weighting, and tolerance are still unselected. A force-sign criterion is not a thermal error tolerance. The qualified source says the tolerance is unresolved; an authorial model acceptance rule is needed after the target is specified.

## Profile-independent results

For two runs with the same unknown initial profile and the same linear operator, material tuple, geometry/support and source, subtracting their solutions cancels the common initial-condition term. Boundary-scenario differences then solve a zero-initial-data equation forced by boundary differences. Source-only contrasts obey rho Cp d(theta)/dt = div(k grad(theta)) + delta_A; for bounded delta_A, identical coefficients/initial data and compatible fixed difference boundaries, a maximum-principle bound is ||theta||∞ <= delta_t sup|delta_A/(rho Cp)|. These identify conditional model-scenario sensitivities only; they do not recover physical histories or absolute T1 state. If coefficients, geometry, interfaces or support differ, operator-difference terms act on unknown T0 gradients and cancellation is no longer profile-independent.

The existing B6N8-K diagnostic, using existing specialist diffusivity corners, reports sqrt(kappa t) = 665.4–1090.4 m for crust and 777.3–998.5 m for mantle; 2 sqrt(kappa t) = 1330.8–2180.7 m and 1554.6–1997.0 m. Its idealized 30 K surface step diagnostic gives maximum |deltaT| 15.499 K at 1 km, 5.838 K at 2 km, 0.03553 K at 5 km. These are conditional half-space diagnostics, not physical temporal variation authority or an absolute bound at a Buck target. Diffusion length alone proves neither full-profile retention nor erasure; broad/low-wavenumber components may retain memory and exact attenuation depends on profile spectrum, domain, layers and boundaries.

## Absolute state and omitted processes

The absolute T1 solution contains the propagated initial profile term. Without a T0 value or qualified profile class/range, absolute T1 temperature, gradient and interface values cannot be determined or bounded. Temperature-dependent Buck strength, flow, and thermal buoyancy also need the actual profile and target/material binding.

B6N8-K permits frozen T0 geometry only as a reduced configuration; physical STRUCTURAL_GEOMETRY_T0_TO_T1 remains EVOLUTION_UNKNOWN. No zero geometry error follows. Background advection/vertical motion, geometry/interface migration, mantle upwelling and lower-crust flow are not bounded. The initializer omits some processes, but their physical absence is not established. B6N1/B6N2 post-event processes cannot be imported backward. Pe = U L/kappa is not physically evaluable: pre-event U and relevant target L are not authorized; absence of U authority is not U=0.

## Support and next provider trigger

B6N8-L counts 14,258 continental thermal cells; 49,362 conditionally eligible positive-age ocean cells; 1,072 unresolved positive-age ocean cells; and 108 age-zero ridge cells. Eligibility still requires exact per-column role/support joins. The unresolved and age-zero groups remain outside the admitted path; this does not prevent a restricted analysis on joined eligible columns but prevents global coverage claims.

Decision: the T0 profile is required for absolute state and final thermal-accuracy/Buck decision, but not for same-operator boundary/source sensitivity. This justifies implementing and validating the selected T0 initializer provider only conditionally after support/material binding. It does not authorize materialization, T0→T1 evolution, Buck execution or publication.

Minimum provider result: support-indexed T(z,T0), native vertical coordinates/layers, geometry identity, coherent k/rho/Cp references with derived kappa, uncertainty/validity/UNKNOWN mask, and deterministic initializer provenance. Validation must establish exact support/time contract, deterministic replay, equation/source/boundary consistency, no steady-state substitution, no support expansion or missing-to-zero mapping, and uncertainty/provenance propagation.

## Decision

**PARTIAL_IDENTIFIABILITY_PROFILE_REQUIRED_FOR_FINAL_DECISION.** Boundary and source contrasts have conditional profile-independent results. Absolute T1 state and Buck-relevant conduction adequacy do not. The finite scenario envelope is **INCONCLUSIVE** for robust sufficiency or insufficiency: T0 profile, target/section, acceptance rule, per-support joins, and omitted-process bounds remain open.

## M1–M14

| Gate | Status | Basis |
|---|---|---|
| M1_SUFFICIENCY_SEMANTICS_DEFINED | PASS_SCOPED | Four meanings defined; no sufficiency result claimed. |
| M2_DOWNSTREAM_OBSERVABLES_IDENTIFIED | PASS_SCOPED | Observable classes recovered; target depths and section remain unselected. |
| M3_ACCEPTANCE_CRITERION_AUTHORITY | BLOCKED_UNRESOLVED | No thermal tolerance; define authorially after target selection. |
| M4_PROFILE_INDEPENDENT_BOUNDARY_SENSITIVITY | PASS_CONDITIONAL | Same operator and initial profile required; scenario contrast only. |
| M5_PROFILE_INDEPENDENT_SOURCE_SENSITIVITY | PASS_CONDITIONAL | Same operator and initial profile required; model source contrast only. |
| M6_INITIAL_PROFILE_DEPENDENCE_CLASSIFIED | PASS | Absolute and differential dependencies separated. |
| M7_OMITTED_PROCESS_IDENTIFIABILITY | BLOCKED_AUTHORITY | Pre-event process/geometry bounds absent; no velocity-zero assumption. |
| M8_SUPPORT_RESTRICTED_IDENTIFIABILITY | PASS_SCOPED_WITH_BLOCKERS | Admitted joined support only; global support not qualified. |
| M9_BUCK_TARGET_DEPENDENCE | BLOCKED_TARGET_UNSELECTED | B6N8-F mapping remains open. |
| M10_ABSOLUTE_VS_DIFFERENTIAL_DECISIONS | PASS | Four result classes kept distinct. |
| M11_T0_PROFILE_NECESSITY | PARTIAL_IDENTIFIABILITY_PROFILE_REQUIRED_FOR_FINAL_DECISION | Required for absolute state/final accuracy, not same-operator sensitivity. |
| M12_INITIALIZER_IMPLEMENTATION_TRIGGER | CONDITIONALLY_AUTHORIZED_AFTER_SUPPORT_BINDING | Implementation/validation only after exact support join. |
| M13_MINIMUM_T0_OUTPUT_CONTRACT | PASS_REQUIREMENTS_DEFINED | Minimum provider output specified. |
| M14_READY_FOR_NEXT_EXECUTION_STAGE | CONDITIONAL_T0_INITIALIZER_PROVIDER_IMPLEMENTATION_AFTER_SUPPORT_BINDING | No runtime execution authorization. |

## Non-actions

No T0 profile/state or T1 state was generated. No provider/evolution was implemented or executed. Sufficiency was neither declared nor denied. No tolerance, physical parameter or boundary value was selected. No Buck section/mechanics, dt2 or T2. WORLD_HISTORY was not accessed or changed.

## Source references

- docs/arcana/qualifications/R6_B6N8L_ATTESTATION.json
- docs/arcana/research/B6N8L_THERMAL_PROVIDER_INPUT_CONTRACT.json
- docs/arcana/research/B6N8L_BOUNDARY_TEMPORAL_ADAPTER.json
- docs/arcana/research/B6N8L_SUPPORT_MATERIAL_BINDING_MATRIX.json
- docs/arcana/research/B6N8K_REDUCED_EVOLUTION_CONTRACT.json
- docs/arcana/research/B6N8K_CONDUCTION_SUFFICIENCY_AUDIT.json
- docs/arcana/research/B6N8D_BUCK_EQUATION_REGISTRY.json
- docs/arcana/research/B6N8D_BUCK_MINIMUM_STATE_AUDIT.json
