# R6 Tectonic T0 materialization design

**Decision:** `R6_TECTONIC_T0_MATERIALIZATION_DESIGN_PARTIAL__FEG_BC_CONTRACT_REMAINS`

This report defines the integrated T0 field and ShellSet input design. It does not select a synthetic-world realization, run a scientific model, materialize fields, or qualify runtime. The design review found concrete gaps in the FEG producer/schema and the Shells velocity-boundary/reference-frame contract; those gaps prevent a runtime-ready design today.

## Parent chain and canonical state

I read the six requested parent artifacts directly, including the parent closure, minimum thermomechanical contract, upstream classification, mechanical input, specialist toolchain, and the primitive constraint report. The required parent decision is `R6_TECTONIC_AUTHORIAL_PRIMITIVES_CONSTRAINED__READY_FOR_T0_MATERIALIZATION_DESIGN`.

The canonical snapshot remains T0 = 210 Ma: 12 plates, 64,800 parent faces, 1,983 shared boundary segments, 30 adjacent pairs, 20 degree-3 junctions, 30 branches/sections, 1,091 convergent-demand edges and 892 divergent-demand edges. The physical-geography, vector-partition and kinematics hashes are respectively `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`, `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`, and `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`. Bootstrap identity remains `27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf`.

R6 already authorizes the spherical baseline `radius=6,371,000 m`, `surface gravity=9.82 m/s²`, and a `z=0` reference equipotential/sea-level datum. Gravity maps to Shells `gMean` only after source-convention verification; radius is used by a mesh only after FEG format verification. Surface temperature and ocean volume are not canonical. Do not invent them if the selected physical mode requires them.

The canonical plate motion frame is `SYNTHETIC_AREA_WEIGHTED_LEAST_SQUARES_NO_NET_ROTATION_GAUGE`, explicitly a kinematic gauge, not a mantle frame or torque balance. It must not be silently replaced with a Shells fixed reference plate. No bathymetry, crust thickness, age, geotherm, density anomaly, FEG or `.bcs` field is present in canonical R6.

## The four authorial primitive contracts

All four remain unselected by canonical authority. The machine-readable choice template gives each a `default: null`, support, constraints and dependent fields. `null` blocks the dependent materializer; it is not a zero/default field.

| Primitive | Contract and downstream products | Author choice still needed |
|---|---|---|
| Ocean surface support | Compose an optional model-derived thermal/isostatic depth component with an authorial low-frequency residual. Preserve `MODEL_DERIVED_THERMAL_DEPTH`, `AUTHORIAL_LOW_FREQUENCY_RESIDUAL`, and `UNKNOWN_FINE_SCALE_RELIEF` as separate authority masks. Project only after complete support is defined. | Basin/domain support, residual structure, whether to include thermal component and its model/configuration. No fine-scale relief is imputed. |
| Crust domain/thickness template | Define physical structural domains independently of plate IDs and land/ocean masks. Minimum families are oceanic, continental and transitional/mixed only when explicitly supported. Preferred candidate: OrbData local isostasy with steady-state geotherm derives thickness from selected structure and material inputs; use a bounded authorial thickness template only if that source-pinned route is unavailable or not selected. Never author thickness separately when the selected model generates it. | Domain boundaries, physical family, material/geotherm inputs and transition rule; thickness parameters only for the explicit template alternative. |
| Oceanic lithosphere age | Prefer a direct T0 age field or low-dimensional age surface. Formation/ridge chronology is an optional causal route to derive that field, not an additional required primitive or a full history simulator. | Age support/values or authorized source chronology, unknown support, and ensemble alternatives. |
| Continental thermal/structural domains | Represent explicit physical domains with compact domain-wise 1D thermal profiles/boundaries and required heat-production/material family. A selected geotherm specialist expands profiles onto mesh nodes. | Structural support, thermal family, boundary conditions and relevant heat-production family. No full authored 3D temperature field. |

Age values must be nonnegative, tied to T0, and spatially coherent with explicitly authorized formation sources. Published oceanic cooling models connect age to thermal profile, heat flow and first-order subsidence, with model uncertainty and limitations retained ([recent plate-cooling analysis](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JB029890)). Unknown chronology stays unknown. Continental support is not inferred from land, craton, suture or orogenic design labels. These constraints do not choose values.

## Materialization architecture

```text
canonical geometry, land support, plate IDs and kinematics (read-only)
  + four explicit authorial primitive selections
  + versioned physical/rheology configuration
       |
       +--> age/cooling specialist --> ocean thermal profile, heat flow,
       |                               mantle-lithosphere thickness,
       |                               thermal/isostatic depth component
       +--> crust domains + selected thickness route --> crust thickness
       +--> continental domains + geotherm specialist --> temperature,
       |                                                heat flow, thickness
       +--> ocean residual + thermal component --> complete ocean surface
       |
       v
ARCANA provenance-aware field assembly and support validation
       |
       +--> OrbData5 only for required transforms/derived node values
       +--> spherical FEG generator and field projection
       +--> pyGPlates kinematic evaluation / separately governed BC adapter
       |
       v
ShellSet/SHELLS T0 input package --> later authorized instantaneous T0 gate
       |
       v
ARCANA output normalization and immutable World History provenance
```

OrbData5 is optional in the ShellSet pipeline: the paper says it updates an input FEG and is unnecessary when required values are already supplied. Its documented route calculates crust and mantle-lithosphere thickness with local isostasy and either a steady-state geotherm or seismic layer estimates. The parent source review also identifies an `Assign` route that reads supplied crust-thickness grids. The design therefore makes the route explicit: prefer the verified OrbData isostasy/geotherm route if its pinned input contract satisfies the synthetic physical-domain schema; otherwise author a bounded thickness template and map it. Do not run both as competing authorities. Exact parser options and output fields must be checked against the pinned version before implementation.

Every derived output records the canonical input IDs/hashes, authorial realization ID, source support and unknown masks, material/model configuration, specialist/version, adapter/version, units, coordinate reference, uncertainty/ensemble member and output hash. OrbData chemical density anomaly and cooling curvature are specialist-derived only if OrbData is selected and required; they are not silently synthesized by ARCANA. The reported density-anomaly limit and other source constraints must be version-pinned, not copied as a chosen field.

## Reference physical parameters and planetary bindings

The parameter builder is versioned `MODEL_CONFIGURATION`. It may not inherit iEarth/Earth5 example values as ARCANA values. For each unbound parameter, the later selection record must point to a material/law source, allowed distribution, cross-parameter constraints and any ensemble member. No source-supported ARCANA-specific interval is selected in this design, so these remain a real configuration gate.

| Parameter family | Class | Contract |
|---|---|---|
| `rhoBar` crust | `AUTHORIAL_REFERENCE_PARAMETER` | Material-family distribution; positive and below mean mantle density under the documented ShellSet consistency check. |
| `rhoBar` mantle | `AUTHORIAL_REFERENCE_PARAMETER` | Material-family distribution greater than mean crust density. |
| `rhoAst` | `SHELLSET_MODEL_PARAMETER` | Reference-column consistency with selected mantle/asthenosphere family. |
| `rhoH2O` | `AUTHORIAL_REFERENCE_PARAMETER` if water-column terms are active | Requires explicit water-column decision; otherwise inactive. |
| `alphaT` crust/mantle | `PHYSICAL_PARAMETER` | Material/temperature-regime constraints and pinned units/sign convention. |
| Conductivity crust/mantle | `PHYSICAL_PARAMETER` | Positive and consistent with selected temperature/heat-flow model. |
| Radiogenic heat production crust/mantle | `AUTHORIAL_REFERENCE_PARAMETER` | Domain/material-conditioned; zero is a deliberate selection, not an implicit default. |
| Surface temperature and profile limits | `SHELLSET_MODEL_PARAMETER` | Bind to declared thermal boundaries and pinned parser conventions. |
| `TADIAB`, `GRADIE`, `ZBASTH` | `SHELLSET_MODEL_PARAMETER` | Mantle adiabat and asthenosphere-depth controls; source/version semantics required. |
| `gMean` | `ALREADY_CANONICAL` | R6 baseline `9.82 m/s²`, map only after convention check. |
| Spherical radius | `ALREADY_CANONICAL` | R6 `6,371,000 m`, mesh geometry only after file-format check. |

Rotation/obliquity are canonical design context, not substitutes for tectonic reference-frame authority. Surface temperature and water properties are absent. If required by the selected input mode, record `AUTHORIAL_PLANETARY_PARAMETER_REQUIRED` rather than filling a ShellSet default.

## Rheology configuration and uncertainty

ShellSet v1.1.0 documents four low-temperature friction parameters and nine dislocation-creep parameters. The rheology configuration contract records the code-native families as `CFRIC`, `FFRIC`, `BIOT`, `BYERLY`, `ACREEP(1)`, `ACREEP(2)`, `BCREEP(1)`, `BCREEP(2)`, `CCREEP(1)`, `CCREEP(2)`, `DCREEP(1)`, `DCREEP(2)`, and shared `ECREEP`. The parameter-file generator must confirm these names and units against the exact pinned source before writing files ([ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html), [Shells parameter definitions](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2007JB005460)).

`CFRIC` represents continuum friction; `FFRIC` applies only to fault elements and must satisfy the source’s friction ordering where active. `BIOT` encodes effective-stress sensitivity to pore pressure; `BYERLY` is a master-fault strength reduction and is fault-only. Crust/mantle `ACREEP`, `BCREEP`, `CCREEP`, `DCREEP` and shared `ECREEP` describe their respective dislocation-creep laws. Creep coefficients must be paired to material/law families and source units. `TRHMAX`/`TAUMAX` are optional force/traction model controls, not extra rheology-family counts. `PLTREF`, `ICONVE`, `TADIAB`, `GRADIE`, and `ZBASTH` are separate model controls. No generic viscosity cap was added without a pinned-source requirement.

Use a bounded configuration ensemble after the law and material families are selected. Keep `AUTHORIAL_ALTERNATIVE` (different world choices) separate from `SCIENTIFIC_UNCERTAINTY_ENSEMBLE` (uncertain parameters/models). Retain all members. ShellSet model-list/grid-search is a sensitivity mechanism; Earth OrbScore observations cannot rank ARCANA members.

## FEG, faults and velocity boundary conditions

**FEG:** Canonical R6 geometry/topology remains scientific authority; the FEG is numerical support. ShellSet documents OrbWin as a separate FEG creator. A validated spherical mesher is an alternative only after its serialization is proven compatible. The FEG contract binds spherical longitude/latitude and R6 radius after confirming exact field order/units in the pinned format. Node/element IDs are generated identities, with explicit links to canonical plate, boundary branch/section and junction IDs.

The mesh policy starts with the coarsest mesh that preserves all required geometry and topology, then refines through a convergence sequence. No target node count is selected here. Production resolution is a separate later choice. Before a solver run, verify all 12 plate IDs, 30 adjacency pairs, all 30 branch/section connections, all 20 junction identities, no accidental adjacency, valid spherical connectivity, and field coverage/error. FEG node spacing cannot be reported as new physical resolution.

**Fault elements:** The first qualification should use continuum-only structure only if the pinned Shells source confirms a valid no-fault solve for the selected proof. The current sources say fault elements are optional in the FEG structure but do not establish continuum-only adequacy for ARCANA. Do not turn all 1,983 boundaries into faults. If any faults are required, separately authorize their geometry, semantics, dip/side-node representation and friction.

**pyGPlates to `.bcs`:** The adapter accepts canonical plate IDs/rotations, topology, FEG node coordinates, and a separately declared reference-frame policy. It can evaluate and export velocities only for authorized nodes/DOFs. pyGPlates velocity at every node must not be used as a prescribed Shells solution field. Nodes default to mechanically free; constrained gauge nodes require an explicit policy; shared boundaries/junctions remain multivalued or free until the pinned solver’s side-node semantics are known. A fault-side class exists only for explicitly mapped fault elements.

The canonical source frame is the R6 synthetic area-weighted no-net-rotation gauge. The target must be the source-confirmed Shells frame; `PLTREF` is a model reference-plate control and may not be silently equated to R6’s gauge. The adapter must transform tangent vectors, convert canonical velocity units to m/s, and encode the parent-described speed/azimuth convention (clockwise from geographic north) only after verifying parser sign/azimuth behavior. A validation invariant is preservation of all pairwise plate-relative velocities under a rigid frame transformation. Exact gauge nodes/DOFs, frame choice, duplicate fault nodes, junction behavior and parser round-trip remain open.

## Runtime manifest, replay and authority

[The manifest template](R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_TEMPLATE.json) holds canonical parent hashes, authorial realization/member IDs, derived-field artifacts, FEG and BC hashes, parameter/rheology config IDs, ShellSet/OrbData/SHELLS/mesh/pyGPlates versions, adapter versions, units, coordinate reference, seeds, uncertainty and validation states. Required null fields mean “incomplete; do not execute.”

Replay identity is the tuple of canonical parent identities, authorial selection-manifest hash, specialist versions/configuration, adapter versions, deterministic seed where used, and environment/lockfile identity. Hash every derived field, FEG, BC and parameter file. Replay must be byte-identical after canonical serialization or state a numeric tolerance and show evidence. New T0 output is appended to World History with provenance; it cannot overwrite canonical parent data or become hard-canonical by default.

Use authority classes `AUTHORIAL_T0_PRIMITIVE`, `SPECIALIST_DERIVED_T0`, `NUMERICAL_DERIVED_SUPPORT`, `MODEL_CONFIGURATION`, `ENSEMBLE_MEMBER`, and `UNKNOWN`. Existing `ProvenanceRecord`, `HistoryStore`, `DomainStateEnvelope`, stable IDs and provider/version registry patterns in `src/arcana_worldsim/r6/` should be reused; do not create another orchestration framework.

## Remaining blockers and counts

- **Authorial:** all four primitive realizations remain `null` and require human choices.
- **Scientific/model configuration:** no ARCANA material family, thermal parameter distributions or rheology ensemble has been selected. Whether continuum-only FEG is a defensible proof also remains unestablished.
- **Provider/interface:** no selected FEG generator and pinned parser contract; no validated frame/gauge/BC node policy or fault/junction duplicate-node contract; no pinned materializer versions.
- **Pure implementation:** primitive manifest loader/materialization orchestrator; specialist adapters; FEG generator/exporter and topology audit; pyGPlates velocity/BC exporter; ShellSet/OrbData parameter and input/output adapters. These should reuse current identity, provenance and provider patterns.

| Count | Result |
|---|---:|
| Independent authorial primitive families | 4 |
| Concretely selected from canonical authority | 0 |
| Requiring authorial selection | 4 |
| Derived T0 field families | 10 |
| Reference physical parameter families | 11 (2 canonical bindings, 9 still unbound/configured) |
| Rheology parameter families | 13 (4 friction + 9 creep) |
| FEG/BC contracts closed at design level | 4 |
| Adapter contracts still open | 5 |
| True scientific/model blockers | 3 |
| Pure implementation blockers | 4 |

Counts are family/contract counts as listed in the JSON. The ten derived-field families cover age, ocean thermal profile, ocean heat flow, ocean mantle thickness, thermal bathymetry component, total ocean-surface assembly, crust thickness, continental thermal outputs, OrbData node-state outputs, and FEG-projected fields.

## Readiness and next stage

The requested design is **partial**, specifically at FEG/BC. The unresolved facts are not resolved by a schema: the official ShellSet paper identifies OrbWin as the FEG creator, while the actual mesh schema/provider and ARCANA topology-preserving conversion are not yet selected. The exact Shells frame, minimum gauge constraints, `.bcs` node semantics and fault/junction behavior also need a pinned-source contract and validation. The [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html) describes OrbData’s input-FEG transformations and optionality; the [official ShellSet repository](https://github.com/JonBMay/ShellSet) identifies the included inputs and software roles. The source-level parent audit independently records the current unresolved `.bcs` and FEG details.

Next, close those provider/source contracts and collect the four explicit human selections using [the selection template](R6_TECTONIC_T0_AUTHORIAL_SELECTION_TEMPLATE.json). Then pin specialist/config versions and fill the runtime manifest. This report authorizes **design only**: it does not authorize final T0 materialization, engine installation/build, official example execution, ARCANA input smoke, ShellSet qualification, or any first finite interval. No `dt`, `t1`, integration horizon or future physical state is selected. No custom ARCANA physical laws are required.

## Validation boundary

The report is grounded in the current parent JSON/Markdown artifacts, R6 initial-world specification, canonical kinematics frame metadata, and the official ShellSet paper/repository and cited parameter literature. JSON parsing, required-section/count checks, authored-file whitespace checks, and unchanged canonical/bootstrap tracked files passed. No scientific engine or tests were run because this change is documentation and JSON templates only. `git diff --check` emitted no tracked-file diagnostics; because the deliverables are untracked and Git excludes them from that command, an explicit whitespace scan was also run on all four files. The one authorized `git add` attempt failed with `Permission denied` creating linked-worktree `.git/worktrees/ARCANA_WORLD_R6_UBUNTU_PORT/index.lock`. Per the brief, no retry was made; no commit was created and no push was attempted.
