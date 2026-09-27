# R6 Tectonic Authorial Initial State Adjudication

**Decision:** `R6_TECTONIC_AUTHORIAL_STATE_PARTIAL__UPSTREAM_CLASSIFICATION_GAPS_REMAIN`
**Branch:** `r6/tectonic-authorial-initial-state`
**Parent:** `10a1c5bbff4c13e99d2387d6f633e87c0337e5bf`

## Result

Reading the parent ledger yields six physical input families: `elevation`, `surface_heat_flow`, `crust_thickness`, `mantle_lithosphere_thickness`, `thermal_density_structure`, and `continuum_rheology`. The `.bcs` velocity constraints and numerical/model controls are outside this six-family reduction: the parent classifies them as interface/configuration obligations, not independent physical initial-state families.

The parent JSON has a metadata inconsistency: its `authorial_required` flag is also true for `.bcs` and model/numerical controls, although its physical-state count is six and those two are separately identified as interface/configuration inputs. I preserve the six physical families identified by the parent count/narrative, and do not promote the two flags into WORLD_HISTORY physical state.

The six reduce to **three independent authorial physical primitive families**, plus **one separate rheology model-parameter family** that is not WORLD_HISTORY state:

1. **`SURFACE_ELEVATION_SUPPORT`** — complete topographic support. ARCANA already has its synthetic land elevation; ocean bathymetry remains unknown. Elevation does not follow uniquely from plate IDs, rotations, or other present T0 fields. GWB can assign configured feature topography, but a uniform/depth-surface assignment is not a physical derivation of realistic bathymetry.
2. **`CRUSTAL_MATERIAL_CLASS_AND_PROPERTIES`** — physical crust/lithosphere class semantics and associated material properties. This is independent of elevation and temperature. It needs explicit class meaning and material mapping; no values are set.
3. **`THERMAL_INITIALIZATION_MODEL_AND_FEATURE_INPUTS`** — the selected thermal model family and its driving conditions/features. A full temperature or heat-flow grid need not be hand-authored if an authorized specialist can generate it, but model, feature semantics and required physical parameters must first be specified.

**Separate constitutive choice:** SHELLS rheology remains an authorial physical-model parameter family. It is not an initial-state field and must not be stored as WORLD_HISTORY state. SHELLS supplies its frictional-plastic and dislocation-creep law implementations; ARCANA would bind an authorized law and parameter set, not implement one.

This is a **reduced candidate vector**, not an exact fully closed initializer: physical crust/material classes and any ridge/slab feature semantics remain unresolved. The selected principal decision therefore records the upstream classification gap rather than claiming readiness for parameter constraint adjudication.

## What can be derived

- **Crust and mantle-lithosphere thickness:** OrbData5 can calculate these jointly under its documented local-isostasy/geotherm workflow, or use seismic layer-thickness inputs. This can eliminate two independent full-grid authoring burdens, but only after input elevation, thermal/material assumptions or source fields are governed. It is not an assumption-free derivation. [ShellSet paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html)
- **Heat flow:** Fourier conduction, `q = -k ∇T`, provides an established relation from a temperature gradient and conductivity. Neither is fully available in R6 T0. The output requires a documented adapter and authorized material/thermal inputs; interpolation alone does not confer authority.
- **Temperature and composition:** GWB can materialize these from a structured feature description and selected models/parameters. For oceanic half-space cooling its tutorial requires ridge coordinates, spreading velocity and depth support. A subducting-plate feature requires explicit trench coordinates, dip-side definition and slab segment properties plus thermal/composition models. GWB cannot decide that ARCANA contains a ridge or subduction zone. [GWB oceanic plate tutorial](https://gwb.readthedocs.io/en/latest/user_manual/basic_starter_tutorial/06_oceanic_plate_temperature.html), [subducting plate tutorial](https://gwb.readthedocs.io/en/v1.0.0/user_manual/basic_starter_tutorial/10_adding_basic_subducting_plate.html)
- **Density:** GWB composition labels are not density. A density field needs an authorized material/property relation or specialist parameterization. No equation of state or mapping is selected here.
- **Elevation:** GWB has feature topography assignment models, including uniform/depth-surface modes. These assign a configured value; they do not derive the missing R6 ocean floor from canonical topology. [GWB feature parameter listing](https://gwb.readthedocs.io/en/latest/GWB_parameter_listings/world_builder_file/index.html)
- **pyGPlates/GPlates:** can produce plate-side kinematics from authorized rotations/topology, but none of the six physical families is derivable from kinematics alone. [GPlately reconstruction API](https://gplates.github.io/gplately/latest/sphinx/html/generated/gplately.PlateReconstruction.html)

## Crust type and tectonic semantics

The tracked R6 generator/validator assigns `crust_class` from land/ocean support (land interior, ocean, coast). That is a design-level category and does not establish physical crust type, composition, age, thickness, density or mechanical properties. The required **`CRUSTAL_TYPE_AUTHORITY_GAP`** remains; do not infer mechanical class solely from land/ocean.

Likewise, the 1,091 convergent and 892 divergent boundary demands remain kinematic descriptors. They do not identify ridge, subduction, collision, rift, transform or distributed-deformation features. Those classes become upstream inputs only if a selected initializer needs them. No class is assigned here.

## Minimum spatial authoring

Avoid 64,800 independent values. The candidate scope is:

- retain the canonical land-elevation field and explicitly resolve whether/how ocean elevation is represented;
- describe material properties per physically authorized material/crust class, not automatically per plate or cell;
- describe thermal initialization per authorized material/tectonic feature and let GWB/OrbData generate supported fields;
- let OrbData generate the two thickness fields under an explicitly selected documented method, retaining method/source/uncertainty provenance;
- configure SHELLS rheology globally or by justified material/element group. Per-plate or per-cell rheology is not currently justified.

The parent authorial synthetic land field is already fixed in canonical T0, so no ensemble is recommended for changing that state. Later ensembles are recommended for unresolved material-property, thermal-initialization, and rheology alternatives, after semantic classes and scientifically defensible ranges are agreed. No ensemble is generated now.

## Interface and remaining limits

The parent `pyGPlates → ShellSet` status remains `SUPPORTED_ONLY_WITH_MODEL_ASSUMPTIONS`. This stage does not determine `.bcs` frame, constrained nodes, precedence, or mesh mapping. Material and temperature fields still need projection to FEG nodes/layers. If explicit slab/fault constraints are chosen, process classes affect node selection; that is a dependency, not a solved interface.

Junction mechanics remain `UNKNOWN`. No junction law is added. The custom patch operator remains conditionally unnecessary if a future specialist proof establishes connected-domain mechanics; its former failure remains diagnostic evidence. No custom ARCANA scientific physics is required by this adjudication.

## Counts

The parent six-family list reduces to **3 candidate independent physical primitive families + 1 separate constitutive parameter family**. One parent family (`elevation`) is partially available in canonical state. One family (`surface_heat_flow`) has an established derivation relation, conditional on authorized temperature and conductivity. Three parent families have specialist materialization paths (`crust_thickness`, `mantle_lithosphere_thickness`, `thermal_density_structure`), with different dependencies and adapters. One family (`elevation`) still requires completion of unsupported ocean surface data or an authorized generation method. Three upstream classification/material-mapping gaps are registered. Three primitive/parameter families are ensemble candidates.

Full mappings and dependency edges are in [the machine-readable adjudication](R6_TECTONIC_AUTHORIAL_INITIAL_STATE_ADJUDICATION.json).

No numeric physical values were selected. No Earth fields were imported. No engine was run; no future state was created. Canonical hashes and the historical bootstrap identity are preserved.

## Sources

- [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html)
- [SHELLS tools/results archive index](https://datadryad.org/dataset/doi:10.5061/dryad.cnp5hqcjb)
- [GWB oceanic plate temperature tutorial](https://gwb.readthedocs.io/en/latest/user_manual/basic_starter_tutorial/06_oceanic_plate_temperature.html)
- [GWB subducting plate tutorial](https://gwb.readthedocs.io/en/v1.0.0/user_manual/basic_starter_tutorial/10_adding_basic_subducting_plate.html)
- [GWB subducting plate temperature models](https://gwb.readthedocs.io/en/v1.0.0/user_manual/basic_starter_tutorial/12_subducting_plate_temperatures.html)
- [GWB feature parameter listing](https://gwb.readthedocs.io/en/latest/GWB_parameter_listings/world_builder_file/index.html)
- [GPlately reconstruction API](https://gplates.github.io/gplately/latest/sphinx/html/generated/gplately.PlateReconstruction.html)
- [Local isostasy and lithosphere thermal structure](https://doi.org/10.1016/S0040-1951(06)00353-2)
