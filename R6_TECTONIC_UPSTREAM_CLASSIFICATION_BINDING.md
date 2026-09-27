# R6 Tectonic Upstream Classification and Material-Property Binding

**Decision:** `R6_TECTONIC_UPSTREAM_CLASSIFICATION_PARTIAL__THERMODYNAMIC_BINDING_REMAINS`

**Scope:** capability and authority reconciliation only. No canonical state, bootstrap, or future state was changed. No numeric physical value was selected. No scientific engine was run. Runtime qualification and the first interval remain unauthorized.

## Executive finding

The parent adjudication named three upstream gaps. Global tectonic process classification is not a prerequisite for the minimum connected-continuum ShellSet mechanics path reviewed here. It is deferred unless a specific optional GWB, fault, or slab workflow later requires a narrowly scoped feature meaning. GPlates/pyGPlates can represent typed features but does not infer their ARCANA meaning.

Material semantics remain necessary: ARCANA must eventually define physical bulk composition/material families and their spatial scope. Density and other P/T-dependent properties need not be authored as independent rasters: BurnMan can evaluate a specified mineral assemblage, while Perple_X can perform phase-equilibrium calculations from bulk composition with selected databases/models. The provider, material representation, P/T inputs, and pressure closure are not bound, so the thermodynamic gap remains open.

## Parent-gap coverage

| Gap | Required by minimum path? | Reduction | Remaining blocker |
|---|---|---|---|
| `CRUSTAL_TYPE_AUTHORITY_GAP` | Yes, as physical material semantics when material-aware generation is used; not as a pre-existing land/ocean classification | Reduce to an authorial bulk composition/material family and spatial scope; let a selected specialist derive properties | No family, composition representation, or specialist binding is authorized |
| `TECTONIC_PROCESS_CLASSIFICATION_GAP` | No, not globally for connected-continuum ShellSet mechanics | Remove as a minimum upstream requirement; defer feature labels for optional GWB/fault/slab workflows | No blocker for minimum path; optional feature semantics must be supplied if that path is selected |
| `THERMAL_DENSITY_MAPPING_GAP` | Yes where material density/thermal properties are required | Existing specialist capabilities can derive density/properties conditionally; density need not be a separately authored field | Composition, P/T, pressure workflow, specialist/database/EOS and adapter remain unbound |

Counts: **3** parent gaps; **1** eliminated as unnecessary for the minimum path; **0** completely closed by a bound specialist; **1** reduced to smaller authorial primitives; **1** irreducible material semantic; **1** remaining provider/workflow gap; **1** remaining classification gap (physical material semantics). Process-feature labels are deferred, not inferred.

## Minimum required semantics

- **Crustal material:** an explicit physical bulk composition/material family and its spatial scope. A geographic land/ocean class, plate identity, convergence, or province label alone is insufficient. No particular classes or compositions are selected.
- **Thermal initialization:** eventually select a thermal model family and its minimal boundary/material inputs. No values or model are selected here.
- **Elevation:** complete surface elevation support remains an independent world-geometry primitive. Existing canonical land elevation is retained; ocean support is unresolved. No unique deeper-structure-to-topography transformation was established.
- **Tectonic processes:** no global ridge/subduction/collision/transform labels are required for the minimum continuum path. Optional workflows may require local, explicit semantics.
- **Rheology:** remains a separate specialist model configuration, not automatically WORLD_HISTORY state. Material classes may later inform grouping but do not determine rheology.

## Material properties and specialist roles

The intended authority direction is:

```text
authorial/canonical composition + bound P/T
                    ↓
           thermodynamic specialist
                    ↓
      model-derived density/properties
                    ↓
          ShellSet/OrbData adapter
```

**Perple_X** is the relevant capability if phase-equilibrium petrology is needed: it operates on bulk composition expressed through selected database components, thermodynamic data, solution models, and P–T conditions. It can calculate phase assemblages and aggregate properties such as volume/density. It is a Fortran program suite with file/configuration-oriented workflows; no official Python API was identified in the reviewed material. Current release license/use terms must be verified; source availability does not establish an open-source license. Not executed.

**BurnMan** is relevant if ARCANA can authoritatively specify the mineral/endmember/solution assemblage and only needs its P/T-dependent density and thermoelastic properties. It is a Python library with EOS and material datasets/models; its documented project license is GPL-2.0-or-later. Phase equilibrium is possible when a phase/reaction system is configured, but BurnMan does not uniquely infer a mineral assemblage from an unspecified crust bulk composition. Not executed.

No winner is selected. Perple_X is better matched to bulk-composition phase-equilibrium questions; BurnMan may be sufficient for property evaluation of a specified assemblage. ARCANA has not yet established that phase-equilibrium petrology is required.

### Pressure dependency

Both routes can depend on pressure and temperature. A lithostatic pressure calculated from depth and overlying density can create density → pressure → density coupling. No pressure initialization or iteration path is bound, and no custom ARCANA solver is proposed. A documented specialist workflow must close this input before execution; ShellSet/OrbData closure has not been verified.

## Tectonic process classification and GPlates

The reviewed ShellSet mechanics path is a connected continuum finite-element problem; boundary process names are not a universal prerequisite. Fault elements and their details are refinements when explicitly selected. Location/geometry and conditional dip/friction/polarity data may matter for a selected fault/slab workflow, but those are not global mandatory labels. Velocity, strain, and slip are solver predictions, not upstream classifications.

GPlates feature models can store typed features such as mid-ocean ridges and subduction zones, plus faults and topological boundaries. Feature authoring documentation places feature type and geometry with the user. Representation does not classify an ARCANA convergent boundary as subduction, nor a divergent edge as a ridge. Do not infer process types from kinematics alone.

GWB remains optional. Its oceanic half-space cooling and subducting-plate features need their respective pre-existing geometries, velocities/polarity and model parameters. GWB consumes those meanings; it does not authorize them. It is not required for the minimum ShellSet path on current evidence.

## Thermal, elevation, and OrbData reductions

- Surface heat flow can follow Fourier conduction from a temperature gradient and conductivity, or be an input in a selected initialization workflow. ARCANA has no complete T0 temperature field or conductivity path bound, so this relation does not close the gap by itself.
- OrbData5 can derive crustal and mantle-lithosphere thickness using a selected local-isostasy/steady-state-geotherm workflow or accept seismic thickness constraints. The local-isostasy route depends on elevation, thermal/heat-flow inputs, material/density assumptions and selected mode. These are specialist outputs, not universal identities. Synthetic inputs may be algorithmically usable, but the ARCANA inputs and adapter are not bound.
- Existing land elevation is canonical. Ocean elevation/bathymetry is still missing/unknown. The reviewed tools do not establish a unique topography derivation from deeper structure.

## Revised minimum upstream state

1. `SURFACE_ELEVATION_SUPPORT` — partially canonical, with ocean support unresolved.
2. `CRUSTAL_MATERIAL_COMPOSITION_FAMILY` — authorial physical semantics and spatial scope, not yet specified.
3. `THERMAL_INITIALIZATION_MODEL_AND_BOUNDARY_INPUTS` — model family and minimal inputs, not yet selected or parameterized.
4. `RHEOLOGY_MODEL_CONFIGURATION` — separate later ShellSet specialist configuration, not world-history state.

Thickness, density, temperature, heat flow, and phase state should be generated by selected specialists where their input contracts permit. This report does not claim that all required transforms are currently bound. The `.bcs` interface, FEG adapter, and connected-domain/junction qualification remain separate unresolved work.

## Authority graph

| Upstream authority | Specialist/transformation | Derived product | Required controls |
|---|---|---|---|
| Canonical land elevation + authorized ocean support | Explicit support completion and FEG mapping | Complete elevation field | Datum, source provenance, uncertainty, mesh projection |
| Material family/composition + P/T + database/EOS | BurnMan for specified assemblage properties or Perple_X for phase equilibrium | Density and material properties | Material model, P/T/pressure route, pinned data/version, uncertainty |
| Elevation + thermal/geotherm/material inputs or seismic constraints | Selected OrbData5 route | Crust and mantle-lithosphere thickness | Mode and assumptions, source hashes, uncertainty, node mapping |
| Thermal primitives and any explicitly authorized feature semantics | Selected OrbData/GWB/thermal specialist; Fourier relation where applicable | Temperature/composition/heat-flow fields | Boundary conditions, conductivity, model provenance, support mapping |
| Connected continuum mesh + generated fields + separate rheology config | ShellSet/SHELLS | Velocity, strain, mechanical response | Later interface and solver qualification; not authorized by this stage |

## Remaining gaps and next stage

The targeted next stage is thermodynamic binding: decide whether the required question is phase equilibrium or properties of a specified assemblage; define the minimal material semantics; identify an established P/T/pressure workflow; pin data/license/runtime terms; and describe the adapter/provenance contract. Keep process labels deferred unless an explicitly selected optional workflow requires them. Do not run scientific engines, qualify runtime, or begin a first interval in this stage.

No custom ARCANA petrology, EOS, density law, phase-equilibrium model, boundary classifier, thermal model, or isostasy was implemented. No numeric physical values were selected. Runtime qualification is not authorized; the first interval remains unauthorized.

## Sources

- [ShellSet/SHELLS paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html) and [source archive](https://datadryad.org/dataset/doi:10.5061/dryad.cnp5hqcjb).
- [Perple_X official site](https://perplex.ethz.ch/), [documentation](https://perplex.ethz.ch/perplex_documentation.html), [thermodynamic data requirements](https://www.perplex.ethz.ch/perplex_thermodynamic_data_file_body.html), [data-file contents](https://www.perplex.ethz.ch/perplex_thermodynamic_data_file_contents.html), and [installation/release workflow](https://www.perplex.ethz.ch/perple_x_installation/perple_x_installation.html).
- [BurnMan repository and license](https://github.com/geodynamics/burnman), [thermodynamic background](https://burnman.readthedocs.io/en/stable/background.html), [composition API](https://burnman.readthedocs.io/en/latest/api_compositions.html), and [equation-of-state API](https://burnman.readthedocs.io/en/latest/autogenerated/api_eos.html).
- [GPlates feature model](https://www.gplates.org/docs/gpgim/), [feature creation responsibility](https://www-old.gplates.org/user-manual/Creating_Features.html), and [pyGPlates common feature query example](https://www.gplates.org/docs/pygplates/sample-code/pygplates_query_common_feature_types).

## Validation record

Parent decision/gaps were checked against `R6_TECTONIC_AUTHORIAL_INITIAL_STATE_ADJUDICATION.json`. No canonical T0 or historical bootstrap change, new future state, engine execution, or physical numeric selection was made. JSON parsing and `git diff --check` are to be recorded after validation.
