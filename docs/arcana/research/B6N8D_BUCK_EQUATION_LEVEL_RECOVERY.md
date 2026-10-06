# B6N8-D — Buck equation recovery and minimum-state audit

**Baseline:** `6538951e441899013d616fec48a4f143afb0c6bf`\
**Decision:** `PASS_B6N8D_BUCK_MODEL_RECOVERED_PREHISTORY_AND_FORCING_AUTHORITY_REQUIRED`\
**Scope:** scientific recovery and state-authority analysis only. No model was selected or implemented.

## Source and transcription policy

Primary authority is W. R. Buck (1991), “Modes of Continental Lithospheric Extension,” *Journal of Geophysical Research* 96(B12), 20161–20178, [doi:10.1029/91JB01485](https://doi.org/10.1029/91JB01485). The supplied primary PDF `1991BuckMOLE.pdf` has SHA256 `0f545e0c045db989bd81ae62461cebfd5e52d72eeb6ed1d9b8c326374e8d5d26`. The specified page images were visually inspected; page images, not OCR, control mathematical transcription. The registry records exact page/equation references, verified forms, and both source-internal inconsistencies without silently normalizing it. No later rift model was substituted.

Authority tags used below: `BUCK_1991_PRIMARY_AUTHORITY`, `SECONDARY_CLARIFICATION`, `ARCANA_ADAPTATION`, `AUTHORIAL_DECISION`, and `UNKNOWN`. No secondary source was needed to replace or override Buck. An equation's standard dimensional interpretation is not itself ARCANA parameter authority.

## Geometry and support

Buck idealizes a two-dimensional cross-section with horizontal coordinate `x` and vertical coordinate `z`. Outside a central extension zone, properties are initially laterally uniform over width `X_L`; the symmetric section is considered from rift center `x=0` to `X_L/2`. A finite-width zone `|x|≤X_e/2` is extended by imposed pure shear. The velocity difference across it is `U_x`; its strain rate is `ε̇=U_x/X_e`, and the horizontal velocity varies linearly through the zone (Figure 2, p. 20164). Crust, Moho and mantle-lithosphere geometry provide vertical strength/thermal support. Buck's extension experiment acts at the center; it is not a network of separately evolving faults or segments.

For the full thermal calculation, only the temperature change at the center column is solved. Thermal transport is one-dimensional vertically; temperature in the non-extending region is held unchanged, and lateral conduction is omitted. Lower-crustal thickness redistribution is solved laterally on the symmetric half-domain with no-flow `∂h/∂x=0` at `x=0` and `X_L/2`; local thinning is imposed in `0≤x≤X_e/2` (pp. 20163–20167). These are part of the published reduction, not generic ARCANA geometry facts. The particular `X_e`, `X_L`, rates and finite strain used in figures are experiment choices, not universal validity limits.

## Equation inventory and causal meaning

The machine-readable [equation registry](B6N8D_BUCK_EQUATION_REGISTRY.json) records equation forms, dependencies, outputs, units, support and source image status. The [dependency graph](B6N8D_BUCK_DEPENDENCY_GRAPH.json) separates model dependencies from ARCANA authority gaps.

Verified coverage: `B91-EQ1`–`B91-EQ12`, `B91-DF`, `B91-A1`–`B91-A12`; the source page images were used for the equations enumerated below.

### Primary-image transcriptions

The following are literal mathematical forms recovered visually. `≈` and piecewise source qualifications are retained. These are Buck source equations, not selected ARCANA parameter values.

- **Eq. 1, p. 20163:** `∂T/∂t = κ ∂²T/∂z² − v ∂T/∂z + H`; Buck defines H in this equation as crustal heat production divided by density and specific heat (K s⁻¹), while Table 2 gives the underlying volumetric source (W m⁻³).
- **Eq. 2, p. 20164:** `σ_b = g B z`; B is Buck’s brittle-failure constant (kg m⁻³), and gB is the stress gradient.
- **Eq. 3, p. 20164:** `σ_d = (ε̇/A)^(1/n) exp(E/(n R T))`.
- **Eqs. 4–9, p. 20166:**
  - (4) `η(y) = η_0 exp(y/y_0)`.
  - (5) `u_f(y) = −(∂P/∂x)(y_0 y/η_0) exp(−y/y_0)`.
  - (6) `∂P/∂x = (g Δρ*) ∂h/∂x`, with `Δρ* = ρ_c(ρ_m−ρ_c)/ρ_m`.
  - (7) `∂h/∂t = κ_f ∂²h/∂x² − u ∂h/∂x − h ∂u/∂x`.
  - (8) `κ_f = g Δρ* y_0³/η_0`.
  - (9) `η_0 = C exp(E/(R T_M))`; adjacent text defines `C = A⁻¹(2 y_0 ∂P/∂x)^(1−n)`, where `2 y_0 ∂P/∂x` is the average base-of-crust deviatoric stress.
- **Eqs. 10–12, p. 20167:**
  - (10) `y_0 = R T_M²/[E (∂T/∂z)]`.
  - (11) `F_b = g ∫₀^{Z_L} δρ(z) z dz`; the printed equation has no additional horizontal-length factor.
  - (12) `F_cb ≈ g Δρ* h δh` for small thickness perturbations.
- **Appendix A, p. 20174:**
  - (A1) `F_ys = (g B/2)[Z_c² + (Z_m²−h²)]`; when `Z_m<h`, the `(Z_m²−h²)` term is set to zero.
  - (A2) `dF_ys = −[1−exp(−2ε)](g B/2)[Z_c²+Z_m²−h²]` under the stated rapid-extension approximation.
  - (A3) `δρ = 2α ρ_m(T_m−T_s)(1−z/(2Z_m))`.
  - (A4) `dF_tb = −[1−exp(−2ε)] gα ρ_m(T_m−T_s)Z_m²/6`.
  - (A5) `h(x,t)=h_0−(δh/2){erf[(X_e+2x)/(4√(κ_f δt))]+erf[(X_e−2x)/(4√(κ_f δt))]}`.
- **Appendix A, p. 20175:**
  - (A6) `dF_cb=[1−exp(−ε)](gΔρ*h²)F(κ_f,ε̇)`.
  - (A7) `F(κ_f,ε̇)=erf[X_e/(4√(κ_f ε/ε̇))]−(1/2)erf[(X_e+X_L)/(4√(κ_f ε/ε̇))]−(1/2)erf[(X_e−X_L)/(4√(κ_f ε/ε̇))]`.
  - (A8) `G_z=dF_cb/(−dF_ys)`.
  - (A9) `G_z=[Δρ*h²/{B(Z_c²+Z_m²−h²)}]F(κ_f,ε̇)`.
  - (A10) `F=1` when `√(κ_f ε/ε̇)≪X_e`; `F=X_e/[2√(κ_f ε/ε̇)]` when `√(κ_f ε/ε̇)≫X_e`.
  - (A11) `T_c=E/{nR ln[g B h(A/ε̇)^(1/n)]}`.
- **Appendix A, p. 20176:**
  - (A12) `κ_f=(gΔρ*/C)[hRT_M²/{E(T_M−T_s)}]³ exp[−E/(RT_M)]` for the stated linear-geotherm closure.

The p. 20165 prose literally gives `dF_ys=F_ys(initial)−F_ys(final)`, while Figure 4 says positive `dF_ys` means strengthening. Appendix A2 and the A8 explanation instead make rapid-extension weakening negative. This is recorded as `SOURCE_INTERNAL_SIGN_INCONSISTENCY`, not corrected in the source transcription. Table 1 p. 20164 also prints `Δρ*=ρ_c(ρ_c−ρ_m)/ρ_m`, opposite to the positive reduced contrast in Eq. 6 p. 20166. This second source inconsistency is retained separately; the extension-positive Appendix force reading follows the Eq. 6 definition and the text’s stated sign, without rewriting Table 1. For coherent signed component bookkeeping only, the registry labels the interpretation `ARCANA_ADAPTATION`: `dF_i=F_i(final)−F_i(initial)`, so weakening is negative. In the Appendix extension convention `dF_cb>0` and rapid-extension thermal `dF_tb<0`; `dF_total=dF_ys+dF_tb+dF_cb`. Buck p. 20168 states positive total change means the required force for continued local extension increases and assumes widening; negative total change favors localization. This remains a Buck diagnostic, never an ARCANA topology-transition predicate.

### `FULL_NUMERICAL_MODEL` versus `APPENDIX_ANALYTICAL_APPROXIMATION`

The full numerical calculation evolves center-column thermal structure, computes the state-dependent strength, solves the crustal thickness/flow equation on the symmetric lateral section, computes buoyancy terms and compares finite before/after force. Appendix A is explicitly analytical and approximate: it includes instantaneous/rapid-extension, negligible thermal-diffusion limits; idealized brittle-envelope integrals; an infinite-width error-function thinning/flow solution; small-strain Goetze-number expressions; and simplified temperature/flow closures. `G_z=ΔF_cb/(−ΔF_ys)` omits thermal buoyancy and is interpreted for rapid extension with `G_z>1` wide, `<1` localized. It is not the complete numerical criterion and cannot stand in for it without a scope-specific validity proof. Buck notes the Appendix infinite-width solution differs from the numerical finite no-flow boundary and is formally valid only when the thinning increment is of order `y_0` or less.

## Symbol and unit registry

The complete machine-readable registry is in `B6N8D_BUCK_EQUATION_REGISTRY.json`; the following is the causal subset. Paper units are retained where explicitly given; conversions to SI are marked as needed for implementation.

| Symbol | Meaning | Units | Role / variation |
|---|---|---|---|
| `x,z,y` | horizontal section; depth positive downward from surface; distance above Moho | m (paper often km) | source figures establish the respective coordinates |
| `T,T_M,T_s` | temperature, Moho temperature, surface temperature | K in constitutive law; paper plots °C | thermal state / initial or boundary condition |
| `κ, H, v` | thermal diffusivity; contextual radiogenic source term; vertical velocity | m²/s; K/s in Eq. 1, W/m³ as tabulated source; m/s | H is divided by density and specific heat in Eq. 1; notation is reused in Table 2 |
| `h,Z_L,X_L,X_e` | crust thickness, lithosphere base, uniform-region width, extension-zone width | m (table often km) | `h` evolves in x,t; other geometry fixed per experiment |
| `U_x, ε̇, ε` | imposed velocity difference, rate `U_x/X_e`, finite strain | m/s; s⁻¹; dimensionless | prescribed forcing |
| `σ_b,σ_d,σ_y` | brittle, ductile and selected yield stress | Pa | algebraic, depth/state dependent |
| `B,g,A,n,E,R` | brittle-failure constant; gravity; creep-law constants; gas constant | B kg/m³; g m/s²; A Pa⁻ⁿs⁻¹; n 1; E J/mol; R J/mol/K | `gB` is the brittle stress gradient |
| `F_ys,F_tb,F_cb,ΔF` | integrated strength; thermal/crust buoyancy; total finite force change | N/m | derived force diagnostics/regime input |
| `ρ_c,ρ_m,Δρ*,α,g` | densities, reduced density contrast, expansion and gravity | kg/m³; kg/m³; K⁻¹; m/s² | material/model parameters |
| `η_0,y_0,κ_f` | basal effective viscosity, viscosity scale length, flow diffusivity | Pa s; m; m²/s | closure quantities; `κ_f` varies with time, not space in Buck model |
| `Z_c,Z_m,T_c,T_m,G_z` | brittle/ductile transition depths/temperatures and approximate ratio | m; K; dimensionless | derived/Appendix diagnostic |

Symbols and subscripts are transcribed from the supplied page images. The source-internal `dF_ys` sign conflict is explicitly retained in the registry; notation is not silently normalized.

## Thermal, strength, thickness and flow state

The model's minimum causal content is not a heat-flow scalar. A complete initial `T(z)` profile, surface/base conditions, thermal properties/source, and the subsequent vertical advection-diffusion response are needed because temperature feeds both the ductile envelope and thermal buoyancy. Crustal thickness is a spatial state: imposed pure-shear extension thins it locally, while lower-crust flow redistributes the resulting anomaly. Mantle lithosphere thins kinematically with the prescribed pure-shear strain; it is allowed to move vertically in response to crustal thickness changes but does not flow laterally in response to pressure gradients. Lower-crust flow is not an optional decoration for full three-mode classification: it creates the broad lower-crust thinning central to core-complex behavior and modifies the crustal-buoyancy change.

The full model uses a strength envelope constrained jointly by frictional/brittle failure and temperature-/rate-dependent ductile flow. Constitutive laws and material compositions materially change `ΔF`; the paper's own examples show markedly different results for weak wet quartz and stronger pyroxene. No table value, “standard” law, or Earth calibration is selected for ARCANA here.

## Four state/dependency sets

### FULL_PUBLISHED_MODEL_STATE_AND_DEPENDENCIES

Section/layer geometry; initial lateral crust-thickness profile; initial temperature profile and thermal boundaries; imposed pure-shear velocity/rate, zone width and finite strain; heat production and thermal diffusivity; crust/mantle densities, expansion and gravity; brittle-failure gradient/effective-pressure assumption; crust and mantle rheology; evolving temperature and thickness; lower-crust viscosity/flow closure; initial/final buoyancy and yield-strength components; numerical domain/discretization and validity/uncertainty evidence.

### MINIMUM_CAUSALLY_REQUIRED_STATE_CANDIDATE

1. Section geometry and initial crust/lithosphere thickness profiles.
2. Initial/evolving thermal profile sufficient for strength and thermal buoyancy.
3. Discrete crust/mantle material and constitutive bindings.
4. Forcing in the Buck section frame, including finite amount/rate and zone support.
5. Lower-crust flow closure for any full Buck/core-complex claim.
6. Recomputable initial/final strength and buoyancy components, signed `ΔF`, uncertainty, and validity.

Force components are derived/replayable state, not independent canonical physical primitives by default.

### POSSIBLY_REDUCIBLE_DEPENDENCIES

- Temperature vector → reduced profile basis only after comparison against the full thermal and force-sign response over an authorized domain.
- Lower-crust PDE → effective `κ_f` closure only after verifying the non-Newtonian approximation and boundary/domain restrictions.
- Per-section calculations → aggregate diagnostic only after declaring coverage, buffer, weighting and junction/end treatment.
- Persisted force components → recompute from parent state/configuration and retain only as diagnostics if replay is deterministic.

### UNSAFE_TO_REMOVE_DEPENDENCIES

Thermal structure/evolution; thickness geometry and contrast; crust/mantle rheology and brittle failure; finite extension amount/rate and width; crust and thermal buoyancy in the full criterion; lower-crust flow when claiming core-complex/full three-mode behavior; uncertainty and validity of any reduction. Removing any changes the causal claim or restricts it to a separately justified domain.

## ARCANA authority, prehistory and gap matrix

B6N8-C is the current design authority: Track A is a preferred research direction, not a selected/qualified production model. It identifies canonical POST_EVENT pair/interface geometry and B6N2 plate-local Euler vectors, but explicitly says relative motion is not physical extension, opening, stress or accommodation. Existing T0 authorities expose crustal-thickness and continental reference heat-flow support and selected physical-domain fields. Those constrain parts of a model, but neither a surface heat-flow field nor T0 thickness uniquely supplies a T1 geotherm, mantle/lithosphere section, rheology or post-event history.

The R6 authorial initial-state/material and thermodynamic binding artifacts separately identify unresolved material-class, thermal/density mapping and parameter configuration. Current classification from B6N8-C is therefore retained: thermal profile at pair support is not currently bound; model-ready material composition/weakness and full thickness profiles are absent or only partially constrained; specialist constants and rheology have not been selected. This report makes no claim that each possible T0 field is globally absent; it distinguishes T0 availability from the missing T1, model-support and semantic binding.

**Prehistory rule:** the Buck equations require initial values. That does not authorize ARCANA to create those values at the B6N1 activation age `209.97287659484368 Ma`. Temperature, thickness/lithosphere geometry, material/density, and likely lower-crust structural state are prehistory-sensitive. Rheology/gravity/thermal laws are static model configuration, while force components and regime diagnostics are derived after forcing. No backcast or activation-time invention is authorized. See the row-level matrix in `B6N8D_BUCK_MINIMUM_STATE_AUDIT.json`.

| Required quantity | Current ARCANA status | Prehistory / blocker |
|---|---|---|
| POST_EVENT pair, interfaces, junction identities | `AVAILABLE_IN_CANONICAL_HISTORY` | Identities exist; no Buck section geometry/support mapping |
| B6N2 Euler vectors | `AVAILABLE_IN_CANONICAL_HISTORY_CONDITIONALLY` | Valid kinematics are not a model-frame extension rate; B6N8-F mapping required |
| T0 crust thickness/domain fields | Available on T0 source support | Must reconstruct/bind the T1 local section history; cannot assume unchanged |
| Continental reference heat flow | Available on existing continental support | Constrains thermal state only under a governed model; does not uniquely define T(z) |
| Complete T1 temperature profile and boundaries | `ABSENT_FROM_BOUND_RIFT_INITIALIZATION` | `NEEDS_PREHISTORY` |
| Complete T1 crust/lithosphere section and thickness profile | Partly constrained at T0, not bound at T1 | `NEEDS_PREHISTORY` and support mapping |
| Material families/density/thermal properties | Semantically partial, numeric/model binding unresolved | `NEEDS_AUTHORITY_BINDING` |
| Crust/mantle rheology and brittle law | Not selected for this model | `NEEDS_AUTHORIAL_PRIMITIVE_DECISION` |
| Radiogenic source/thermal properties on model support | Not fully bound | `NEEDS_AUTHORITY_BINDING` |
| Local section `U_x`, `ε̇`, `X_e`, finite interval | No physical mapping from B6N2 yet | `NEEDS_AUTHORIAL_PRIMITIVE_DECISION`; B6N8-F |
| `F_ys,F_tb,F_cb,ΔF` | Deterministically derivable after all prior closure | Not current state; never invent as independent input |

## B6N2 forcing and interface mapping

Buck's actual forcing is a prescribed horizontal velocity difference across a finite-width pure-shear zone, plus a finite strain/time increment. A spherical rigid-plate angular velocity is not that quantity. A future mapping must specify: local frame; tangent/normal basis; sign/polarity; relative surface velocity and authorized temporal horizon; extension/convergence classification; section support and `X_e/X_L`; aggregation/resampling; strain-rate and finite-strain calculation; and validity at segment endpoints/junctions. No part of this mapping is fixed here.

Buck's support is one symmetric cross-section, not automatically one of 71 ARCANA interface segments. Plausible future mappings include `PER_CROSS_SECTION`, `LOCAL_WINDOW`, or `PER_INTERFACE_AGGREGATE`; a segment-by-segment one-to-one mapping is unsupported without added scientific semantics. B6N8-F must determine section selection, buffers, diagnostic coverage, aggregate rule, and junction overlap before any model can consume the B6N2 driver.

## Uncertainty, validity and mechanics classification

Keep uncertainty dimensions separate: initial-state/prehistory; material/parameter; rheology; forcing; model form (including incomplete flow/thermal coupling); numerical discretization; force-sign/regime criterion near zero; and spatial section-to-interface mapping. Buck varies parameters/rheologies in experiments but does not prescribe ARCANA probability distributions. Do not invent distributions.

Validity is bounded by the symmetric 2-D section, thin-sheet forces, imposed pure shear, 1-D center-column thermal model with omitted lateral conduction, Newtonian-derived/non-Newtonian flow approximation, and incomplete thermal-flow coupling. The model is continental; its findings do not automatically define oceanic spreading or subduction. Buck notes that very high temperatures may melt or convect, processes not included. Where a limit can be made measurable later it should become a model validity/stop bound; until thresholds are authorized, retain documented limitation/unknown rather than inventing a threshold.

**Mechanics classification:** B6N8-C's `TIER2_PLUS_LIMITED_PHYSICAL_STATE_REQUIRED` is consistent in broad terms. Equation-level refinement is `TIER_2_PLUS_LIMITED_MECHANICAL_STATE`: reduced thin-sheet force balance, brittle/ductile constitutive strength and pressure-driven lower-crust flow are mechanical physics. The paper does not establish that a full finite-element/Stokes regional solve is necessary. Full-mechanics necessity remains unproven.

## Candidate minimum prototype state V0 (not a schema)

The candidate components are: (1) section geometry/material interfaces; (2) initial/evolved temperature profile; (3) crust/lithosphere thickness profiles; (4) discrete material/constitutive bindings; (5) forcing interval and model-frame mapping; (6) lower-crust flow closure; and (7) derived force/regime diagnostics with uncertainty. Units, support, temporal origin, initialization, law dependencies and ARCANA status for each are in the JSON audit. This is a conceptual candidate only, not a production contract or selected data model.

## Implementability and next stage

**Equation recovery:** CLOSED from the supplied primary page images, including the yield-strength sign conflict and the Table 1/Eq. 6 density-contrast conflict. **Implementability:** `NOT_IMPLEMENTABLE_FROM_CURRENT_ARCANA_AUTHORITY`. Independent blockers remain: (a) pre-T1 thermal history and crust/lithosphere structural state; (b) material/rheological/thermal authority binding and uncertainty; and (c) B6N2-to-Buck local-section physical extension, support and interval mapping.

B6N8-D equation recovery is closed. The next work is B6N8-E (prehistory/initial-state and material/thermal authority) and B6N8-F (B6N2-to-physical-section forcing/support mapping). Neither authorizes values or propagation. Do not create a prototype until those independent authority paths are closed.

## Preserved non-actions

`physical_rift_model_selected=false`; `physical_rift_model_qualified=false`; `prototype_implemented=false`; `physical_parameters_selected=false`; `SECOND_DT_SELECTED=false`; `dt2_years=null`; `T2_CREATED=false`; `B6O_authorized=false`; `mechanics_executed=false`; `canonical_forward_propagation_executed=false`; `topology_transition_executed=false`; `support_remapping_executed=false`; `WORLD_HISTORY_changed=false`.

## Validation/evidence notes

The qualification-stage baseline was clean at the requested commit. The recorded pre-authoring canonical WORLD_HISTORY snapshot contained 46 files / 1,275,143 bytes with prior manifest digest `7beea3258010ecb412dbf0d6ae69fe5c5f9f250245b6e7231851bb68a83a45c2`. A read-only post-authoring inventory again found 46 files / 1,275,143 bytes. This pass wrote only the four repository research artifacts and did not access WORLD_HISTORY for writing; because the prior digest serialization was not reproduced, this report makes no new digest-equivalence claim. Artifact JSON graph and equation IDs were cross-validated; no simulation/regression applies because no executable model was introduced.
