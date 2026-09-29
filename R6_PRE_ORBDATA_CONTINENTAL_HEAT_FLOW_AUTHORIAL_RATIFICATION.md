# R6 PRE_ORBDATA A0.5R — Continental heat-flow authorial semantic ratification

**Decision:** `R6_PRE_ORBDATA_CONTINENTAL_HEAT_FLOW_REFERENCE_BOUNDARY_AUTHORITY_RATIFIED__GLOBAL_HEAT_FLOW_ARCHITECTURE_OPEN`

**Ratified field:** `continental_reference_surface_heat_flow_w_m2`
**Authority class:** `AUTHORIAL_T0_PRIMITIVE`
**Semantic:** `GOVERNED_AUTHORED_CONTINENTAL_T0_REFERENCE_BOUNDARY_FIELD`

This ratification is authorized by the user's A0.5R instruction, which directs preparation of this semantic declaration unless existing authority contradicts it. The audit found no such contradiction. This closes the semantic question for the existing continental field only; it does not select architecture C or authorize PRE_ORBDATA.

## Producer lineage

The field is authored in the B-v2 realization by `src/arcana_worldsim/r6/t0_materialization/b_pangaea_v2.py` and materialized into `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz`.

1. `R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json` explicitly lists `reference_surface_heat_flow_mW_m2` within `CONTINENTAL_THERMAL_STRUCTURAL_DOMAINS`, with three classes, reference values, companion reference lithosphere thicknesses, and soft target area fractions. The realization is `RATIFIED_FOR_T0_MATERIALIZATION`.
2. The producer loads and identity-checks canonical geography, partition, and kinematics. The land/ocean mask and canonical boundary edge row/column/axis establish land support and adjacency. Relative normal velocity and segment length form continental extension/convergence support scores. The coastline mask is used later for physical-crust transition classes, not for thermal-class assignment.
3. A deterministic spatial ranking assigns coherent land cells to `HOT_EXTENDED`, `COLD_STABLE`, and the `NORMAL` remainder using the ratified soft area shares (hot and cold targets), support rankings, spherical cell area, and stable cell-ID tie breaks. Ocean thermal class is zero. This is not driven by crustal thickness, coastline mask, or imported Earth province tags.
4. `HEAT_FLOW_MW_M2` maps the three thermal IDs to the already ratified reference values. For each class, the producer writes `q * 1e-3` on `land & (thermal_id == class_id)`, yielding W m⁻²; the array is initialized to NaN elsewhere.
5. The B-v2 manifest records thermal IDs, area fractions, class reference heat flow and thickness, parent identities and normalized field hashes. The materialization/runtime reports carry the field hash and explicitly report continental-only support, missing ocean/global fields, and missing nodal lineage.

The exact class values remain as already ratified in the source artifacts; this semantic ratification changes no numbers.

## Value provenance and semantic authority

**Value provenance:** these are synthetic authored T0 reference values, assigned deterministically by thermal class. The producer does not use a heat-flow observation grid or thermal inversion to generate them. No Earth observational authority is implied. Their support ranking uses the governed T0 geography and canonical kinematic/boundary support; the values themselves are selected authorial class parameters.

**Semantic authority:** “reference” does not prohibit a prescribed T0 boundary/reference role. The B-v2 ratification explicitly selects reference surface heat-flow values as part of continental thermal structural domains. The producer writes them as a T0 field, and the specialist report separately leaves “model-derived heat flow beyond ratified references” pending. These are affirmative support for a prescribed reference field while retaining its limited meaning; they are not evidence of a complete continental geotherm or a global heat-flow solution.

The existing `derived_fields` manifest grouping describes generated/materialized package products. It does not override the upstream authorial selection that supplies the class values. The specialist report's global heat-flow status, the lack of FEG projection, and the absence of an oceanic field constrain completeness and runtime readiness; they do not contradict the continental boundary/reference authority.

### Existing descriptions and consumers

The repository-wide source/document search found the field or its dedicated reference metadata in:

- `R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json` — explicit authorial per-class reference surface heat-flow selection.
- `src/arcana_worldsim/r6/t0_materialization/b_pangaea_v2.py` — deterministic class/value producer, support assignment, field packaging, and manifest metadata.
- `R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json` and `R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json` — materialized class references and normalized hash.
- `R6_T0_B_PANGAEA_LIKE_V2_SPECIALIST_MATERIALIZATION.json` — reference class map, global/ocean fields missing, lineage/projection incomplete; “model-derived heat flow beyond ratified references” remains pending.
- `src/arcana_worldsim/r6/t0_materialization/specialist_runtime.py` — verifies/carries the upstream field identity and reports its reference values; does not calculate a new heat-flow value from it.
- `R6_T0_B_PANGAEA_LIKE_V2_RUNTIME_BINDING_AND_INPUT_READJUDICATION.json` — records it among upstream materialized fields; no FEG heat-flow projection or runtime consumption is implemented.
- `R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE.json` — carries its unchanged parent hash; ocean surface closure does not transform the heat-flow field.
- `R6_PRE_ORBDATA_HEAT_FLOW_SCIENTIFIC_REQUIREMENTS.{json,md}`, `R6_PRE_ORBDATA_HEAT_FLOW_LITERATURE_RESEARCH.{json,md}`, and the prior A0.5 adjudication — document its partial support and previously open exact role.

No implemented consumer currently projects or passes this field to the FEG. It is carried and hash-checked by materialization/readiness reporting. The later FEG heat-flow field is still missing.

## Semantic options

| Option | Producer and contract fit | Numeric changes | New assumptions | PRE_ORBDATA consequence |
|---|---|---:|---|---|
| **A — prescribed T0 physical reference** | Best fit: class values are explicitly ratified in the T0 thermal-domain selection and materialized as a named T0 reference field. | None | Clarifies that the authored reference is the prescribed continental surface boundary/reference; it does not assert observational truth or a unique subsurface profile. | Supplies the continental branch on current support only. Ocean heat flow, projection, q-limit governance and runtime remain open. **Ratified.** |
| **B — calibration target** | Possible use of a reference, but no calibration model, observations, objective, or fitting process is specified. | None | Would add an unselected calibration procedure and demote the authored field to target status. | Continental flux would remain unavailable until calibration/model execution. Not selected. |
| **C — validation-only reference** | No authority says validation-only. This would demote explicit T0 class parameters without evidence. | None | Requires a separate continental physical model to become the sole flux authority. | Continental flux remains blocked pending that model. Not selected. |
| **D — other** | No source requires proxy-only or diagnostic-only status. | None | Unnecessary. | Not selected. |

## Ratification

`continental_reference_surface_heat_flow_w_m2` is hereby ratified as a **governed authored continental T0 reference boundary field** with these semantics:

- It is an authored synthetic T0 physical reference field and prescribed continental surface heat-flow boundary/reference state.
- Its authority is limited to the existing continental thermal-class/cell support. It is not a global field and supplies no ocean flux.
- It carries no Earth observational authority.
- It has no greater spatial resolution than its producing cell/class support. FEG projection is `NUMERICAL_DERIVED_SUPPORT` only and does not create new physical resolution.
- Its thermal-class identity, generating policy, input lineage, and uncertainty/provenance status remain attached. No numeric uncertainty interval is invented here.
- It is not derived merely from crustal thickness.
- Refinement or replacement requires an explicit higher-authority physical stage; no silent overwrite or relabeling is allowed.

This ratifies an authored reference boundary, not a full continental thermal solution, observation-backed truth, or model-derived geotherm. The existing uncertainty authority remains limited: class identity and provenance are governed, but a numerical uncertainty distribution is not.

## Values, support, and projection

**Effect on existing values:** none. No generator or payload is changed. The normalized field SHA256 remains `234d2c34f4bc98f72cbaa0e1b322ba781bc95fab9e7b69795fb2b3e7a03b7e2f`.

**Spatial authority:** the 180×360 cell-centered land support assigned a continental thermal class. Ocean and unsupported cells remain UNKNOWN. The values must not be spread to a higher resolution as a physical claim.

**FEG projection:** not yet implemented. When projected, only homogeneous incident continental class support may receive the reference value under a deterministic adapter; retain contributing source-cell IDs, method/weights, coverage, and class identity. Mixed ocean/continent or UNKNOWN support stays UNKNOWN until a separately governed interface rule resolves it. Projection is a numerical representation on the solver mesh, not new physical information.

**Uncertainty:** the authorial ratification makes authorial selections fixed choices rather than ensemble axes for ratification. The producer supplies no numeric uncertainty range for heat flow. Preserve the class/provenance metadata; do not derive an interval from modern Earth data. Any later model-derived thermal profile has separate parameter/model uncertainty.

## Global nodal payload authority

If a hybrid global architecture is selected later, do not create a duplicate independent canonical heat-flow field by default:

- The complete cell/node T0 flux product should be **`DERIVED_REPLAYABLE_T0_STATE`** when deterministically generated from governed continental references, ocean domain/age, pinned ocean model/configuration, and projection lineage. Retain its model/input hashes, uncertainty and support metadata in history.
- The serialized FEG nodal array/file should be **`NUMERICAL_RUNTIME_INPUT_ONLY`**, derived from that replayable field. It is not independent canonical physical state.
- **`CANONICAL_PHYSICAL_STATE`** is not preferred for the combined nodal field unless a later explicit ARCANA authorial stage chooses that field itself as a new immutable authored primitive.

## Downstream implications and remaining gates

The continental side is now authorized for a hybrid architecture candidate. This A0.5R report does **not** finalize architecture C. A remains incomplete without ocean flux and global support; B remains possible only if it explicitly preserves the ratified reference's role while defining any model-derived field separately. Still open: ocean model/version and parameters, age-zero treatment, `qLim0`/`dQL_dE`/`qLim1`, domain-boundary and UNKNOWN rules, global projection, and PRE_ORBDATA input qualification.

`authorial_decision_required` for this continental field is **false**: the user explicitly authorized this ratification if no contradiction existed, and the audit found none. Global architecture and remaining parameter decisions are still open.

**Gates preserved:** `PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`. Canonical state and ShellSet were not changed.
