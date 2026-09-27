# R6 ShellSet Pre-runtime Input Closure

**Decision:** `R6_SHELLSET_PRERUNTIME_INPUTS_PARTIAL__AUTHORIAL_PRIMITIVES_REMAIN`
**Branch / HEAD at authoring:** `r6/shellset-preruntime-input-closure` / `1d35adb55c8eb83f36ba2fc299d8d6bd10f43886`
**Scope:** integrated T0 input authority and interface adjudication. No scientific engine or forward evolution was run.

## Finding

The minimum OrbData5 → SHELLS contract is now reduced enough to plan a bounded runtime proof, but the necessary R6 physical inputs and interfaces are not ready. The existing R6 T0 has canonical plate geometry, topology, rotations/kinematics and a validated land-elevation payload. It has no physical crust thickness, lithosphere age/thickness, heat flow, geotherm, material-property mapping, rheology, bathymetry, FEG mesh or `.bcs` interface.

The historical parent blocker for external absolute pressure, EOS density and P–ρ–g coupling is superseded. OrbData/SHELLS uses reference densities, thermal correction and `chemical_delta_rho`; it constructs its pressure/stress column internally. BurnMan and Perple_X are optional refinement/validation tools, not mandatory global production engines. No bulk mineralogical state or global tectonic-process labels are needed for the minimum path.

The best shared generative input is a **T0 oceanic lithosphere-age/thermal-feature state**. In an explicitly configured model, OrbData can use the age route for oceanic mantle-lithosphere thickness/heat flow, while GWB can generate temperature from explicit age or ridge geometry and spreading velocity. Age is not derivable from `plate_id` or the instantaneous rotation field; divergent kinematic demand does not authorize a ridge classification. Continents still need their own thermal/structural initialization. The age route does not by itself create ARCANA-authorized bathymetry or crustal thickness.

Thus the reduced world-definition burden is **four independent primitive families**: (1) ocean elevation/bathymetry support; (2) a compact physical crustal-domain/thickness template; (3) oceanic lithosphere age or explicit ridge/spreading-history state; and (4) continental thermal/structural initialization. The remaining physical constants and rheology belong to constrained, versioned specialist configuration, not WORLD_HISTORY rasters. No values are selected here.

## Repository archaeology and canonical status

The current reports and payload manifest show the R6 initial geography is at T0 = 210 Ma on `R6_GLOBAL_GEOGRAPHY_1DEG_V1`, shape 180×360. Its validated physical-geography payload hash is `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`. It contains:

- `land_ocean_mask` and `coastline_mask`;
- `land_surface_elevation_m`, supported on land only, relative to the authorial R6 zero datum;
- `bathymetry_unknown_mask`, true on ocean, with no depth values;
- `crust_class` and `province_class` design categories;
- `plate_id`, but its manifest explicitly says identity is not motion.

The separate canonical tectonic state provides 12 plates, 64,800 parent faces, 1,983 shared boundaries, 20 degree-3 junctions, the plate partition and canonical kinematics. It is not a ShellSet FEG and contains no lithosphere-age field. The R6 design is synthetic, Earth-scale and Pangaea-inspired; A1 and Earth products are reference evidence only. The original source support stays 1-degree cell support; interpolation onto FEG nodes is numerical projection, not new scientific resolution.

| ShellSet family | ARCANA availability | Classification |
|---|---|---|
| Land elevation | Validated authorial synthetic field, land support only | `PARTIAL_CANONICAL_SUPPORT` |
| Ocean elevation/bathymetry | Unknown mask only; no numeric depth | `NOT_AVAILABLE` |
| Crust type/province | Design categories, not thickness or material laws | `CANONICAL_T0_AVAILABLE_AS_DESIGN_CATEGORY` |
| Crust thickness | No physical field | `NOT_AVAILABLE` |
| Mantle-lithosphere thickness | No thickness or age field | `NOT_AVAILABLE` |
| Heat flow / temperature / geotherm | No field | `NOT_AVAILABLE` |
| Reference material / density parameters | No ShellSet configuration | `NOT_AVAILABLE` except canonical planetary radius/gravity baseline |
| Rheology | No law or values | `NOT_AVAILABLE` |
| FEG / `.bcs` | No exported mesh or boundary file | `NOT_AVAILABLE` |

No A1 values, modern Earth grids, Earth5 example fields or interpolation products were promoted to ARCANA state.

## Integrated input closure

### Elevation and bathymetry

ShellSet needs node elevation for the modeled surface structure. Land elevation is already present, but the ocean is explicitly unsupported. The land/ocean mask does not specify ocean depth. Neither GWB's feature topography inputs nor the candidate landscape-evolution tools infer a physically authoritative synthetic basin depth from current R6 state. FastScape/Badlands are surface-evolution tools with required forcing, not a source of initial bathymetry. An age-depth/cooling model is a possible later physical model only after its thermal assumptions and structural use are authorized; no such model is currently selected.

**Minimum primitive:** a low-dimensional authorial ocean-basin/domain elevation field with datum, uncertainty, support and provenance. The current land field remains untouched. This does not require 64,800 independently authored depths. No depth values are chosen.

### Crustal thickness and material domains

The current OrbData5 `Assign` path reads crustal thickness from an upstream grid; it does not solve crustal thickness from isostasy. `crust_class` values (oceanic, continental, transitional) and craton/suture/orogenic design labels do not imply thickness, physical lithology or density. GWB can materialize feature-configured structures, but does not supply authority for a feature's thickness.

**Minimum primitive:** an authorial physical crustal-domain template with a small set of thickness parameters or constrained ranges assigned to explicitly defined domains. An adapter can map this template to the OrbData input grid. Preserve uncertainty as ranges/scenarios. A specialist can materialize the field after this authority exists; no selected specialist derives it from current T0 without those assumptions.

### Mantle-lithosphere structure, age and thermal state

OrbData's Earth-oriented alternatives use oceanic seafloor age or continental vertical S-wave travel-time anomaly. Neither observational field is available or transferable here. The current T0 rotation/plate identity does not encode geological age.

The official [GWB oceanic-plate model documentation](https://gwb.readthedocs.io/en/latest/user_manual/parameter_documentation/features/oceanic_plate.html) describes temperature models including half-space cooling. Its dynamic route takes ridge coordinates and spreading velocity and computes age from ridge distance; those feature inputs are explicit assumptions. GWB can materialize configured temperature/composition fields, but it cannot infer a ridge, spreading history or material authority from ARCANA kinematics. OrbData may then produce heat-flow/thickness fields through its configured age/data path. For continents, use a separately governed thermal/structural primitive or prescribed thickness equivalent; do not infer thermal age from craton/suture labels.

**Minimum shared primitive:** either an authorial synthetic oceanic age support field or an explicit ridge/spreading-history feature state. Choose one later; do not encode both redundantly. For a general T0 with no authorized tectonic history, an age field is the more direct primitive. The continental thermal/structural initialization is an additional independent family.

### Thermal state and heat flow

OrbData can preserve an already non-zero nodal heat-flow value or read/populate it from a selected source; its ocean path may use age. The ShellSet source description makes temperature depend on depth relative to topography, local heat flow, layer heat production and a non-steady geotherm component. GWB supports configured oceanic plate cooling and continental thermal profiles. Heat flow can also be derived from a fully specified temperature gradient and conductivity using the established conductive flux relation, then mapped to the FEG with source support, sign convention and error recorded. This is an adapter operation, not an ARCANA heat-conduction solver.

Do not independently author both age-derived temperature and heat-flow fields unless a model explicitly requires them as independent conditions. Use the chosen specialist path to generate dependent fields and carry input/model uncertainty. Current R6 has none of these thermal fields or source primitives.

### Reference material parameters and constraints

These are model configuration, not spatial WORLD_HISTORY state:

- `gMean`: the R6 design already records a global surface-gravity value with its Earth-scale analogue provenance. It can map to ShellSet after checking the pinned parameter's convention. Keep the canonical design value and provenance; do not substitute an Earth example default.
- `rhoBar` crust and mantle, `rhoAst`, and applicable `rhoH2O`: unbound specialist reference parameters. Preserve the source consistency condition that mean mantle density exceed mean crust density. Constrain ranges only after physical material/domain and model convention are declared.
- `alphaT`, conductivity, layer heat production, reference/surface temperature and geotherm controls: thermal-model configuration. They must be dimensionally and mutually consistent with the chosen profiles. Values remain unset.

The parent records these as reference densities and an effective chemical-density anomaly, not EOS density. Avoid importing ranges from an unrelated planetary or Earth calibration without qualifying material and temperature regimes. Since no canonical material basis yet fixes a unique point, later constrained ranges/ensemble members are more honest than scalar defaults.

### Rheology and ShellSet parameter exploration

ShellSet/SHELLS already implements a low-temperature frictional/plastic law and crust/mantle dislocation-creep laws. The ShellSet paper describes four low-temperature frictional inputs (including an optional lower effective fault friction) and nine creep-law inputs. Element-group IDs can select alternate values, but per-plate variation is not justified by current R6 physical classes. The source paper gives consistency checks such as fault friction below continuum friction and mean mantle density above mean crust density. Exact parameter names, dimensional units, admissible ranges and defaults must be pinned to the exact SHELLS release before runtime.

Physical constraints can be stated without numeric choices: layer thicknesses must be positive and compatible with the selected layer profiles; oceanic age must be non-negative and tied to the declared T0/history or explicit ridge geometry; conductivity and thermal coefficients must have correct dimensions and match the chosen profile; reference densities must satisfy the ShellSet ordering check; and friction ordering applies where the relevant fault/continuum terms are used. More specific numeric intervals depend on material family and constitutive law, neither of which is authored in R6. Applying a broad Earth range to undefined ARCANA materials would create false precision, so those constraints remain governed ensemble/configuration work.

Rheology is a specialist physical-model configuration family, not WORLD_HISTORY state. Preserve uncertainty as governed ranges or an ensemble. ShellSet model-list/grid-search features can explore parameter families later, but the Earth OrbScore datasets are observational calibration for Earth and must not rank ARCANA models. A model-list ensemble retaining all outputs can support sensitivity analysis without inventing an ARCANA score.

### pyGPlates velocity boundary conditions

Published `.bcs` descriptions use fixed mesh nodes with speed in m/s and azimuth clockwise from geographic north. Earth examples prescribe selected slab nodes and use temporary fictitious interior anchors during iterations, then release those anchors. They do not justify constraining all ARCANA plate nodes or define a generic absolute/relative frame policy.

pyGPlates can evaluate a canonical plate velocity under the selected rotation/reference frame; an adapter still must choose which nodes (if any) are fixed, convert frame/units/azimuth, preserve plate and junction identities, and define constraint precedence and fault duplicate-node behavior. The mechanical solver's velocity field is an output; prescribing the whole field would erase the solution. Retain only model-required constraints. Kinematic divergence alone cannot declare a ridge, and no global fault/process taxonomy is introduced here.

Status: `ADAPTER_ONLY_PLUS_MODEL_AUTHORITY_GAP`; do not execute the mapping yet.

### Mesh ownership

ARCANA's spherical geometry/topology remains scientific authority. OrbWin or a separately validated spherical mesher owns the numerical FEG mesh. The mesh and its nodes are `NUMERICAL_DERIVED_SUPPORT`, never canonical geography. A later mesh adapter must preserve plate/boundary/branch/junction identities, retain source support and projection error, and test topology preservation and numerical convergence under mesh refinement. No FEG exists yet.

## Minimum production chain and authority graph

Candidate after the listed authorial definitions and adapters are governed:

```text
ARCANA canonical T0 geometry / plate identities / kinematics
  ├─ land elevation (canonical) + authorial ocean-elevation primitive
  ├─ authorial crust-domain thickness template
  ├─ oceanic age/feature primitive + continental thermal initialization
  └─ versioned material / thermal / rheology configuration
       ↓ support-aware adapters and numerical FEG mesh
pyGPlates (only selected kinematic values for authorized BC nodes)
       ↓
OrbData5 (configured node-state preprocessing when needed;
          may be skipped if the FEG already has the complete state)
       ↓
SHELLS (thin-shell mechanics)
       ↓
ARCANA normalized derived output + provenance
```

OrbData5/SHELLS own their physical transformations. ARCANA supplies the authored world primitives, versions specialist parameters, validates adapters and records results. No custom crust-formation, plate-cooling, heat-conduction, isostasy, rheology, mesh-mechanics or tectonic PDE implementation belongs in ARCANA.

Explicit fault elements are not shown to be universally required: they are needed when the selected model represents discrete faults. A continuum-only idealization is possible, but its adequacy for ARCANA has not been established. A bounded proof must state that model policy rather than silently assigning fault classes to every canonical boundary.

## Blocker reduction and counts

| Current item | Closure classification | Result |
|---|---|---|
| Canonical plate geometry, IDs and rotations | `CLOSED_BY_CANONICAL_STATE` | Available; not a FEG or age field. |
| Land elevation | `CLOSED_BY_CANONICAL_STATE` | Available on supported land cells only. |
| Ocean elevation/bathymetry | `REDUCED_TO_AUTHORIAL_PRIMITIVE` | Missing basin-depth support; no selected generator. |
| Crustal thickness | `REDUCED_TO_AUTHORIAL_PRIMITIVE` | Compact domain/thickness template; OrbData reads its grid. |
| Ocean mantle thickness/heat flow/temperature | `CLOSED_BY_SPECIALIST` after primitive | OrbData/GWB can materialize selected age/cooling path fields; age/feature input absent. |
| Continental thermal/structural state | `REDUCED_TO_AUTHORIAL_PRIMITIVE` | No seismic Earth field or synthetic thermal initialization in T0. |
| Reference material configuration | `REDUCED_TO_SPECIALIST_CONFIGURATION` | Ranges/constraints, no selected values. |
| Rheology | `REDUCED_TO_SPECIALIST_CONFIGURATION` | Built-in law; parameters/config not selected. |
| FEG mesh | `ADAPTER_ONLY` | Numerical mesh absent; canonical geometry remains authority. |
| pyGPlates to `.bcs` | `ADAPTER_ONLY` plus model authority | Frame/node/constraint policy unresolved. |
| External pressure, EOS, P–ρ–g, mandatory BurnMan/Perple_X | `DEFERRED_OPTIONAL_REFINEMENT` / superseded | Removed from mandatory chain. |
| Global process labels, arbitrary anchor distance, custom mechanics | `DEFERRED_OPTIONAL_REFINEMENT` / superseded | Not required by current minimum state contract. |

Counts, using **families** rather than individual parameter scalars or per-cell values:

- Required scientific input families: **8** (surface elevation, crust thickness, mantle-lithosphere structure, heat-flow/thermal state, reference density/material structure, rheology, FEG support, BC/fault interface).
- Already canonical complete: **1** (R6 planetary radius/gravity baseline for convention-checked `gMean`).
- Already canonical partial: **1** (land elevation; ocean absent). Canonical plate geometry/kinematics is available as upstream geometry, not counted as a ShellSet physical field.
- Specialist-generated candidate families: **4** (temperature/geotherm, heat flow, mantle-lithosphere thickness, OrbData density-anomaly/cooling-curvature fields), conditional on the authorial primitives and chosen specialist configuration.
- Independent authorial physical primitive families after reduction: **4** (ocean elevation/bathymetry; crustal physical-domain/thickness template; oceanic age/ridge-history; continental thermal/structural initialization).
- Specialist-model configuration families: **3** (reference material/density; thermal coefficients/initialization settings; rheology).
- Adapter-only gaps: **2** (canonical-to-FEG mesh/field mapping; pyGPlates-to-`.bcs` frame/node mapping).
- Optional high-fidelity items: **5** (GWB beyond the selected configured field path; ASPECT; BurnMan; Perple_X; Underworld3/LaMEM).
- True remaining blocker groups: **6**, listed below.

### True blockers, in priority order

1. Complete surface elevation support, especially the ocean/bathymetry primitive.
2. Physical crustal-domain semantics and crust-thickness template/range.
3. Oceanic age/feature state plus continental thermal/structural initialization.
4. Constrained reference material and thermal configuration ranges.
5. Constrained SHELLS rheology configuration/ensemble and pinned parameter inventory.
6. FEG mesh and pyGPlates/`.bcs`/fault/junction interface contract.

These are now one integrated pre-runtime readiness ledger. The smallest remaining independent world-definition burden is four primitive families; specialists materialize dependent fields after their authority and configuration are specified. Runtime readiness remains false.

## Sources and validation boundary

- [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html): OrbData/Shells/OrbScore roles, thermal and layer fields, thickness paths, rheology group parameterization, and ShellSet model-list/grid-search capability.
- [ShellSet source repository](https://github.com/JonBMay/ShellSet): official source and standard parameter/input files; source findings for current `Assign`, `Squeez`, `.bcs` and parameter semantics are carried forward from the parent source-level adjudication.
- [ShellSet author response](https://egusphere.copernicus.org/preprints/2023/egusphere-2023-1164/): heat-flow/geotherm, heat-production, depth and effective chemical density-anomaly semantics.
- [GWB oceanic plate documentation](https://gwb.readthedocs.io/en/latest/user_manual/parameter_documentation/features/oceanic_plate.html) and [GWB 2019 methods paper](https://se.copernicus.org/articles/10/1785/2019/): configured feature-based fields and cooling/temperature models; inputs remain authorial.
- [GWB manual](https://gwb.readthedocs.io/en/v1.0.0/): feature-oriented geodynamic initial-condition generator, not an authority generator.
- Repository inputs read directly: toolchain reconciliation; mechanical input reconciliation; authorial initial-state adjudication; upstream classification; thermodynamic binding; minimum ShellSet thermomechanical contract; initial-world physical specification and materialization manifest.

Validation performed before commit: verify the parent decision and branch/HEAD, canonical payload and bootstrap hashes, JSON structure/required sections, unchanged bootstrap blob, no numeric additions, no canonical or future state edits, and `git diff --check`. No engine/test execution is appropriate for this source/authority-only report. Runtime qualification and first-interval design remain unauthorized.
