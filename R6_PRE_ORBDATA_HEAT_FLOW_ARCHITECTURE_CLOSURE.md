# R6 PRE_ORBDATA A0.5C — Heat-flow architecture closure

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_ARCHITECTURE_CLOSED__HYBRID_DOMAIN_AWARE__PARAMETERIZATION_PENDING`

**Selected architecture:** `HYBRID_DOMAIN_AWARE_HEAT_FLOW`

This closes only the architecture choice. It does not select numerical thermal parameters or a final ocean model/version, run OrbData/SHELLS, modify ShellSet, promote the B-v2 candidate to global canonical state, or authorize PRE_ORBDATA.

## Authority basis

A0.5R ratified `continental_reference_surface_heat_flow_w_m2` as `GOVERNED_AUTHORED_CONTINENTAL_T0_REFERENCE_BOUNDARY_FIELD`. It is an authored B-v2 T0 parent field with limited native continental support, no Earth observational authority, and no values derived merely from crustal thickness. Its normalized hash remains `234d2c34f4bc98f72cbaa0e1b322ba781bc95fab9e7b69795fb2b3e7a03b7e2f`.

`oceanic_lithosphere_age_ma` is the governed T0 ocean-age parent field (normalized hash `aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2`). `physical_crust_domain_id` is the categorical routing parent (normalized hash `814acfdde0285bf6bd549ae8c06e853da5855acb9e78187359a5230fe47cdfd1`). These remain within a ratified B-v2 realization whose current canonical status is `CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION`; this closure does not promote it.

## Architecture contract

```text
CONTINENTAL
  ratified continental_reference_surface_heat_flow_w_m2
       -> deterministic support-aware FEG projection
       -> continental nodal reference heat flow

OCEANIC
  governed oceanic_lithosphere_age_ma
  + versioned finite-plate-family cooling model
  + explicit young/rift applicability policy
       -> derived oceanic heat flow

physical_crust_domain_id (categorical)
       -> domain-aware join with lineage and uncertainty
       -> global DERIVED_REPLAYABLE_T0_STATE
       -> 64,442-node FEG serialization
       -> NUMERICAL_RUNTIME_INPUT_ONLY for OrbData
```

The ocean model family is fixed as finite-thickness plate cooling, but its exact identity, version and parameters remain for A0.6. The joined global field is a deterministic derivative of governed parents/configuration, not a new independent canonical authority. ShellSet's exact-zero heat-flow sentinel and limit/correction behavior still require explicit configuration and qualification.

## Why A is not selected

`EXPLICIT_GLOBAL_HEAT_FLOW_FIELD` is not physically impossible. It is deferred for governance and replay reasons:

- A separate, independently authored global field would duplicate the ratified continental parent and the age/model-derived ocean branch unless it replaced and re-typed those authorities through a higher-authority authorial decision.
- No ocean values or complete global/node support currently exist, so A would require a new independent global materialization.
- A flat global field weakens causal and replay provenance by obscuring the age-to-model-to-ocean-flux dependency.
- No current contract requires a second complete authored field.

A can be reconsidered if ARCANA explicitly chooses a complete global field as the primary physical parent and resolves the branch-source authority without duplicate state.

## Why B is not selected

`FULLY_DERIVED_HEAT_FLOW` is not scientifically invalid in general. It is deferred for the current T0 because:

- Current crustal and lithosphere thickness alone cannot uniquely reconstruct continental surface heat flow.
- A derived continental branch would need new assumptions and governed inputs for radiogenic heat production, its vertical distribution, material properties and basal thermal conditions.
- ARCANA already has a ratified authored continental T0 reference field. Replacing it as branch authority requires an explicit higher-authority physical stage.
- A downstream continental geotherm or model-derived refinement remains possible, but it must retain the ratified reference's declared role and separate lineage.

## Domain and support behavior

- **Continental:** use the ratified field on existing support. `physical_crust_domain_id` codes 2–6 select the continental branch, subject to source-field support and FEG class-resolution checks.
- **Oceanic:** use derived finite-plate-family heat flow only where the ocean age and selected model's validity support are known.
- **Young/rift ocean:** until the special physical treatment and applicability range are selected, the heat-flow value remains UNKNOWN. Do not use `qLim1` as a substitute.
- **UNKNOWN:** remain UNKNOWN and fail closed unless an explicitly authorized producer supplies a value. Never encode UNKNOWN as exact zero.
- **FEG boundaries:** retain incident source-cell IDs and physical-domain/thermal-class IDs. Mixed ocean/continent support remains UNKNOWN; do not blend branch values. Mixed continental thermal classes also remain UNKNOWN until a categorical rule is governed. Projection is `NUMERICAL_DERIVED_SUPPORT`, does not create new physical resolution, and must report support/coverage and method.
- **ShellSet interface:** exact zero triggers `needQ`/qArray routing. Prevent accidental zero-sentinel activation; a valid physical zero needs its own authorized, qualified representation.

## State authority versus runtime payload

| Field/product | Authority class | Scope |
|---|---|---|
| `continental_reference_surface_heat_flow_w_m2` | `CANONICAL/GOVERNED_AUTHORED_T0_PARENT_FIELD`; `AUTHORIAL_T0_PRIMITIVE` in the B-v2 candidate lineage | Existing continental thermal-class cell support only; not a claim that the B-v2 candidate has been globally promoted |
| `oceanic_lithosphere_age_ma` | `GOVERNED_T0_PHYSICAL_PARENT_FIELD` | Existing governed ocean age support |
| Ocean heat flow from age + selected model | `DERIVED_REPLAYABLE_T0_STATE` | Recomputed from governed age, domain, model/configuration and source identities |
| Global joined T0 heat flow | `DERIVED_REPLAYABLE_T0_STATE` | Replayable branch join; no independent canonical authority |
| Serialized 64,442-node OrbData heat-flow payload | `NUMERICAL_RUNTIME_INPUT_ONLY` | Adapter representation of the joined replayable state; never becomes physical authority because it is serialized |
| Uncertainty/support/lineage | Derived-state metadata | Stored alongside the derived field, preserving distinct uncertainty axes and UNKNOWN |

## Replay identity

The replay identity includes and pins:

1. Continental reference-field hash.
2. Oceanic age-field hash.
3. `physical_crust_domain_id` hash and continental thermal-class hash.
4. Ocean model identity/version and its parameter configuration hash.
5. Young-ocean/age-zero policy identity/version.
6. Projection algorithm/version/configuration.
7. Uncertainty configuration/member identity.
8. Source package and canonical parent identities.
9. Derived producer implementation/version and environment identity.

Changing any item creates a different derived-state replay identity and requires recomputation/revalidation for affected support. Hash the ocean branch output, joined cell field, FEG nodal projection and serialized runtime file.

## Uncertainty contract

Keep these separate; do not collapse them into one scalar:

- **Continental authored/reference uncertainty:** retain thermal class and source provenance. No numerical interval is invented; the authored values have no generated ensemble in the ratification.
- **Ocean model structural uncertainty:** retain model-family alternatives and model-validity information separately from parameter uncertainty.
- **Ocean parameter uncertainty:** attach selected model parameter ranges/covariance and govern ensemble dimensions in A0.6.
- **Young-ocean applicability uncertainty:** retain separate validity flags and ridge/accretion/hydrothermal structural alternatives; unsupported values stay UNKNOWN.
- **FEG projection/support uncertainty:** retain incident source lineage, categorical agreement, coverage, method/weights and numerical projection diagnostics.

## A0.6 scope: remaining parameterization decisions

A0.6 receives architecture C as fixed and must not revisit A/B/C. It selects/configures only the remaining model and parameter details:

| Area | Remaining choices | Belongs to |
|---|---|---|
| Ocean heat-flow producer | Exact finite-plate model/version and transfer rationale; model thermal/basal/plate parameters; whether output is conductive flux or total heat loss | Ocean cooling specialist producer |
| Young/rift ocean | Applicability range; ridge/accretion treatment; hydrothermal scope; finite age-zero representation; corresponding uncertainty | Ocean heat-flow producer/interface |
| ShellSet heat-flow routing | `qLim0`, `dQL_dE`, `qLim1` roles and values/replacement semantics; decouple `qLim1` from physical age zero; accept/reject and diagnose later geotherm correction; avoid accidental exact-zero qArray fallback | OrbData/ShellSet specialist configuration and qualified adapter |
| Thermal/material configuration | Conductivity by material/domain; `alphaT`; `TSurf`; `TAsthK`; `temLim`; `TADIAB`/`GRADIE`/`ZBASTH` only where active in the pinned source | Downstream OrbData geotherm/material model |
| Uncertainty | Ocean model-form alternatives; parameter covariance/ranges; young-ocean validity alternatives; projection/support diagnostics and ensemble dimensions | Both, with separate identities per producer |

If the ocean cooling model and OrbData geotherm model both use conductivity or expansivity, those are separately versioned configurations; do not assume the parameter bindings are interchangeable. No numerical values are chosen here.

## Remaining blockers

**Scientific:** exact ocean plate model/version and parameters; young/rift and age-zero law; q-limit and correction governance; downstream material/geotherm configuration; uncertainty ensembles; mixed-boundary and physical-zero semantics.

**Implementation:** generate the ocean branch after model selection; implement lineage-preserving join; project to all 64,442 FEG nodes with categorical support checks and projection evidence; serialize a complete non-sentinel field; replay/hash validate all inputs and outputs; perform FAIR qualification before any OrbData execution. The canonical partition/mesh payload prerequisites remain those recorded in the materialization ledger.

**Gates preserved:** `PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`. No canonical promotion or ShellSet modification occurred.
