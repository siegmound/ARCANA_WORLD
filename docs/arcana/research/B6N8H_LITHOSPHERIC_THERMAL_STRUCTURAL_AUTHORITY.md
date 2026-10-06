# B6N8-H — Minimum Lithospheric Thermal-Structural State Authority

## Decision

**PASS_B6N8H_MINIMUM_PHYSICAL_STATE_CONTRACT_DEFINED_BINDINGS_AND_T0_TO_T1_EVOLUTION_REMAIN**

This closes a requirements definition, not the physical-state authority. ARCANA cannot currently construct a defensible T1 POST_EVENT lithospheric thermal-structural state. B6N8-G remains unchanged: FIRST_BUCK_PROCESS_EVALUATION_READY = false.

## Baseline and temporal target

- Branch: r6/b6n8h-lithospheric-thermal-structural-authority
- B6N8-G attestation baseline: 4731a376ce4ee87353747d7c4282bd9779125009
- B6N8-G qualified source: 8b263cc4d59a0bf3d01dc65dcedfe928b79e7130
- B6N8-E qualified source: f9904136e90b4463ab31013373d77810639748f3; attestation 1e4f4fee1ce95fabc32c9eb62b783314660afa78
- B6N8-D qualified source: 88298ef948b6dc17a14961f6a43154cca4915d05

T0 = 210.0 Ma; T1 = 209.97287659484368 Ma; elapsed = **27,123.40515632 years** (0.02712340515632 Ma). The required endpoint selector is exactly POST_EVENT; age alone is insufficient.

B6N8-E remains authoritative for the prehistory distinction: PRE_T0_HISTORY_REQUIRED = NOT_DEMONSTRATED; PRE_T0_HISTORY_PROVEN_UNNECESSARY = false. A T0 initializer could summarize earlier assumptions, so no pre-210 Ma simulation is demonstrated necessary; neither is its irrelevance proven.

## Existing authority

The canonical initial package covers physical geography, land/ocean, province and topography. Bathymetry, tectonic kinematics and deep state are unknown; there is no lithospheric thermal state. The initial-world specification says lithology/regolith/soil are not materialized and treats 210 Ma as a new R6 design time, not recovered Simulation1 history.

B-Pangaea-like v2 is ratified for T0 materialization and supplies authored cellwise crust/domain, continental thermal-class reference thickness and continental heat-flow fields. The realization manifest still says candidate pending materialization validation, while B6N8-E found no complete canonical Buck-support binding. These are authored candidates, not a complete verified canonical T0 lithosphere. Domain/province/thermal classes do not identify composition.

Some specialist references are selected, but their scope must remain intact: gravity 9.82 m s-2 is the fixed Earth-scale analogue baseline; A0.6D TSurf is 280 K (250-300 sensitivity); mantle conductivity 3.3 W m-1 K-1 (3.0-4.1), density 3300 kg m-3 (3200-3400), Cp 1200 J kg-1 K-1 (1100-1250), and alpha 3.0e-5 K-1 (2.5-3.5e-5). HWR Tb=1680 K (1523-1737) and zp=100 km (80-140) are finite-plate references, not automatically TADIAB, LAB or mechanical thickness. Continental q references are 0.045/0.060/0.085 W m-2 on their producing support; ridge q=0.3 W m-2 is separate. No scalar flux specifies T(z).

Still unbound are crust material/composition and crust k/rho/Cp/alpha/heat production; mantle production/decay; asthenosphere density/profile; TADIAB-to-LAB mapping; and a complete density(z) law. Diffusivity follows k/(rho Cp) only after a complete coherent tuple is bound. Zero heat production is not implicit.

## Minimum state and initialization

The minimum candidate state is: (1) crust thickness/Moho with explicit datum; (2) physical lithosphere base/LAB depth and thickness with explicit criterion; (3) authorized T(z) or a representation proven sufficient to reconstruct and evolve it; (4) material/compositional layer references; and (5) per-quantity support, provenance, uncertainty and validity. Density(z), interface temperatures and flux may be derived under a pinned model. Rheology is configuration; lower-crust flow stays conditional on selected Buck scope.

T0 profile routes remain open: author a profile primitive; authorize a layered steady conductive initializer; or retain complete primitives with a pinned replay recipe. None is currently authorized as ARCANA T0 geotherm. Buck's experimental steady-state setup is not ARCANA initialization authority. A steady layered conductor is possible as an explicit model assumption with validity limits, but its current authority result is UNKNOWN. Surface heat flux alone cannot determine it.

## T0 to T1

S_T1 = EVOLVE(S_T0, governed_pre_activation_processes, elapsed_interval). No complete reduced thermal law or boundary history is bound. Geometry evolution is EVOLUTION_UNKNOWN: absence of an authorized structural driver does not prove unchanged geometry, and silence does not authorize deformation. Do not apply B6N2 POST_EVENT rift forcing before the activation boundary.

B6N1 has distinct PRE_EVENT and POST_EVENT causal records at activation with the same published physical-payload SHA. This supports no instantaneous change in that existing payload. It does not provide or validate the missing thermal profile, nor settle future evolution.

For diffusion, L=sqrt(kappa*dt), and kappa_critical=L^2/dt. Over about 8.56e11 seconds, thresholds for diffusion lengths of illustrative 1, 10 and 30 km are approximately 1.17e-6, 1.17e-4 and 1.05e-3 m2 s-1. These are dimensional thresholds, not selected ARCANA diffusivities or physical layer boundaries. Without a full kappa tuple and boundary/source history, 27 kyr cannot be declared negligible or significant for ARCANA. SHORT_INTERVAL does not imply CONSTANT_STATE.

## Provider, overlay and gates

The conceptual LITHOSPHERIC_THERMAL_STRUCTURAL_STATE_PROVIDER_V0 requirements are in [B6N8H_PHYSICAL_STATE_PROVIDER_REQUIREMENTS.json](B6N8H_PHYSICAL_STATE_PROVIDER_REQUIREMENTS.json). The contract requires exact time/causal identity, native support, geometry, thermal state, material references, boundary history, uncertainty, validity, provenance, and replay recipe when applicable. It fails closed on missing support, datum, properties, evolution or unauthorized resampling.

The 20-input B6N8-G overlay is [B6N8H_B6N8G_INPUT_STATUS_OVERLAY.json](B6N8H_B6N8G_INPUT_STATUS_OVERLAY.json). It preserves age, candidate plate identities, restricted B6N2 kinematics, and leaves section/Ux/Xe/XL and finite-forcing work to the owning stages. It updates physical-state inputs with explicit remaining blockers. B6N8-G itself is not modified.

| Gate | Result |
|---|---|
| H1 T0 geometry authority | Partial authored candidate; canonical Buck-support binding incomplete |
| H2 T0 thermal state | Blocked: no profile or authorized initializer |
| H3 thermal properties | Partial references; material tuples incomplete |
| H4 T0-to-T1 evolution | Blocked: no governed reduced evolution |
| H5 T1 geometry | Blocked |
| H6 T1 thermal state | Blocked |
| H7 T1 POST_EVENT binding | Partial: selector and existing-payload rule known; state absent |
| H8 uncertainty/validity | Blocked |
| H9 provider contract | Pass at requirements-only scope; not implemented |
| H10 ready for Buck adapter | Not ready |

## Exact blockers and next closure

1. Validate/bind existing T0 geometry candidates and datum on native support.
2. Choose an authored T0 profile or authorize a reduced initializer.
3. Complete crust/material and basal/LAB bindings.
4. Govern thermal boundary history and evolution over 27,123 years.
5. Decide structural evolution or explicitly authorize a no-change model; neither follows from silence.
6. Bind uncertainty, support, validity and deterministic replay.

A layered 1-D conductive/transient column on native support is the smallest new model candidate if ARCANA chooses derivation rather than an authored T0 profile. Requirements only: not selected or implemented. Rheology/lower-crust flow and B6N8-F section/forcing remain separate.

## Validation and safety

Reviewed the G attestation/source, 20-input inventory, E immutable gap/evolution records, D minimum-state audit, T0 manifests, material/thermal contracts, and B6N1 activation attestation. G's FIRST_BUCK_PROCESS_EVALUATION_READY=false is preserved. WORLD_HISTORY was not accessed.

No T0/T1 state, provider, Buck section, Ux, Xe, XL, strain or forcing was generated; no parameters selected; no dt2/T2, mechanics or forward propagation; WORLD_HISTORY_changed=false.
