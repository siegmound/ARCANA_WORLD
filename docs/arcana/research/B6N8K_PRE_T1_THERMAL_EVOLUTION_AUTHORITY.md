# B6N8-K — Pre-T1 reduced thermal evolution authority

## Decision

**PASS_B6N8K_REDUCED_EVOLUTION_CONDITIONALLY_AUTHORIZED_BOUNDARY_HISTORY_BINDING_REMAINS**. ARCANA may use a frozen T0 configuration and held boundary values as explicit reduced-model scenarios for a pre-event thermal calculation. This is model-configuration authority only: it does not assert that physical geometry or boundaries were constant. Conduction-only sufficiency is **unresolved**, and no provider is ready to run.

## Governing frame and inherited authority

Qualified baseline: `f0ae6bca2ad443f66a38752452dc359ab00f983f`, the B6N8-J attestation commit. B6N8-J remains unchanged: `R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING` is the conditional replayable T0 reference-profile initializer, not a T0–T1 integrator or canonical geotherm. The interval is T0=210 Ma to T1 PRE_EVENT=209.97287659484368 Ma, exactly 27,123.40515632 years. Rift activation is at the endpoint; B6N2 post-event kinematics do not force this interval.

The evolution input interface is a provenance-bearing `T(z,T0)` on native-cell support, joined explicitly to material roles, geometry/base identity, boundaries, uncertainty and validity. No such profile/provider currently exists. The initializer and evolution must share support, layer interfaces, flux convention and source accounting; no steady-state replacement or duplicated radiogenic term is allowed.

## Configuration and boundary adjudication

T0 authored geometry is the chosen reference configuration for this reduced calculation. Holding it fixed is an explicit approximation; `STRUCTURAL_GEOMETRY_T0_TO_T1=EVOLUTION_UNKNOWN` and physical geometry invariance remains false. T1 data are not backcast into T0.

The 280 K specialist surface reference (250–300 K sensitivity) and authored continental q can define T0 model-boundary inputs on their governed support. Deterministic held-boundary scenarios are permissible as model configurations, not physical histories. The model-domain base may likewise be held only with the initializer-compatible base definition; HWR `zp` is not thereby a universal physical LAB. Existing parameter ranges are not temporal trajectories. Positive-age ocean HWR needs a world-time age/support adapter; age-zero ridge retains its separate rule.

Finite eligibility is limited to supported native cells with a valid material-role join, geometry, boundary and age/ridge rule. Unknown support or an ungoverned land/ocean/class change fails closed. No interpolation, extrapolation, support promotion or Buck-section inference is authorized.

## Conduction and sensitivity

The candidate is `rho Cp dT/dt = div(k grad T) + A`, using coherent `k,rho,Cp` and derived `kappa=k/(rho Cp)`. Existing specialist diffusivity corners imply `sqrt(kappa t)` of 0.665–1.090 km in crust and 0.777–0.999 km in mantle over this interval; `2 sqrt(kappa t)` is about 1.33–2.18 km and 1.55–2.00 km. A half-space step-boundary diagnostic shows a 30 K surface step could contribute up to about 5.84 K at 2 km but about 0.035 K at 5 km, conditional on those reference diffusivities and the idealized step model. This is not evidence that actual boundary history is constant, nor that an unselected Buck target is insensitive. Target/base sensitivity cannot be closed without target depth/support.

Thus conduction-only sufficiency is **UNRESOLVED, neither proved sufficient nor proved insufficient**. Radiogenic source applicability/temporal role, advection, interface migration, lower-crust flow, ocean support change and boundary-history adequacy require closure at intended support. Sensitivity cannot convert missing temporal authority into evidence. B6N1/B6N2 processes are excluded from the open interval.

## Readiness and causal output

The [reduced evolution contract](B6N8K_REDUCED_EVOLUTION_CONTRACT.json) defines only a prospective T1 PRE_EVENT interface: replayable profile identity, T0 geometry approximation flag, material/support identity, boundary/source provenance, uncertainty, validity and causal lineage. It does not create state. A future PRE_EVENT payload may be eligible for POST_EVENT reuse as the same payload under a distinct causal state only if separately governed instantaneous thermal physics is absent.

Provider readiness: **NO**. T0 materialization remains conditional on role/support binding and initializer-provider validation; T1 PRE_EVENT is not materialization-ready. B6N8-F thermal-to-section mapping remains separate. No physical LAB, Buck section, dt2, T2 or evolution was selected/executed. `PRE_T0_HISTORY_REQUIRED=NOT_DEMONSTRATED`; the selected reduced model does not require explicit pre-T0 integration, which does not prove physical pre-T0 history did not exist.

See the [boundary/support matrix](B6N8K_BOUNDARY_HISTORY_AND_SUPPORT_MATRIX.json), [conduction audit](B6N8K_CONDUCTION_SUFFICIENCY_AUDIT.json), and [B6N8J readiness overlay](B6N8K_B6N8J_READINESS_OVERLAY.json) for K1–K14 and exact remaining blockers.

WORLD_HISTORY was not accessed. No provider, physical state or canonical state was generated; no mechanics or propagation was run.
