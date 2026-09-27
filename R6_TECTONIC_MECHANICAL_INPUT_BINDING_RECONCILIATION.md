# R6 Tectonic Mechanical Input Binding Reconciliation

**Decision:** `R6_TECTONIC_MECHANICAL_INPUT_BINDING_PARTIAL__AUTHORIAL_INITIALIZATION_REQUIRED`
**Branch / HEAD audited:** `r6/tectonic-mechanical-input-binding` / `2356e122f66d765c613d231edf72cf68b3aa9be6`
**Scope:** source and authority reconciliation only. No engine installation/execution, physical values, `W_model`, `dt`, future state, or canonical modification.

## Decision

ShellSet/SHELLS remains a credible global thin-shell mechanics candidate, but its physical inputs and its ARCANA interface are not bound. ARCANA T0 supplies canonical geometry, plate identities/topology, synthetic kinematics, and land elevation only. It does not supply an authorized full elevation field, heat flow, temperature/geotherm, crust or mantle-lithosphere thickness, density/composition, rheology, fault/process classes, an FE mesh, or SHELLS `.bcs` constraints.

The next stage is an **authorial physical initial-state contract**. It must name the authority and physical constraints for missing fields, without choosing values here. The `.bcs` frame/node policy and mesh mapping remain interface sub-gaps. Runtime qualification is not authorized; first-interval design remains unauthorized.

The input ledger, statuses, counts, and field-level evidence are in [the JSON report](R6_TECTONIC_MECHANICAL_INPUT_BINDING_RECONCILIATION.json).

## What each ShellSet component does

- **OrbData5** alters/populates nodal physical values in an existing finite-element grid. The published workflow derives crust and mantle-lithosphere thickness using local-isostasy/geotherm assumptions or seismic thickness data, and uses density-anomaly and geotherm-curvature parameters. It does not create/change FE topology or the included fault network. It is optional where the FEG already has the required values.
- **SHELLS v5** is the mechanics solver: a thin spherical finite-element model of quasi-static creeping flow that predicts velocity, strain and fault slip from lithosphere structure, rheology, mesh and selected forcing/boundary conditions.
- **OrbScore2** evaluates predictions against observation datasets; it does not provide the mechanical initial state.
- **OrbWin / FEG creation** is a separate mesh creation/editing responsibility. The resulting numerical mesh must remain subordinate to ARCANA's canonical geometry.

The source paper identifies elevation, heat flow, crust thickness, mantle-lithosphere thickness, density and parameters defining internal temperatures as physical lithosphere structure represented at grid nodes. The published `.feg` examples explicitly enumerate the first four nodal fields and per-fault dip angles. The published description of SHELLS rheology identifies low-temperature frictional rheology (four parameters, including the lower effective friction option for faults) and nine dislocation-creep flow-law parameters for crust and mantle lithosphere, with group-specific values selectable by FEG element IDs. Exact pinned-v5 parser requirements, parameter names/units/ranges/defaults were not fully inspected; the JSON labels this limitation rather than asserting a parser-level minimal contract. [ShellSet paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html), [official source archive index](https://datadryad.org/dataset/doi:10.5061/dryad.cnp5hqcjb)

No standalone mandatory GPE raster or initial velocity solution was established from the inspected sources. Topography and density/thermal structure contribute to physical state; whether extra traction/closure inputs are required depends on the selected formulation and remains unknown. Geometry/mesh and numerical solver controls are execution prerequisites, but they are not physical initial-state fields.

## Inputs that are not solver state

OrbScore's six documented scoring options are seafloor spreading rates, geodetic velocities, horizontal stress directions, SKS fast-polarization azimuths, smoothed seismicity, and fault-slip rates. They are observations against which a computed model may be scored, not compulsory SHELLS mechanical state. Earth example datasets such as CRUST2, ETOPO, PB2002, and NUVEL-1A are likewise not ARCANA inputs. In particular, Earth's observed fields, boundary classifications, and slab velocities are not transferred to the synthetic world. [ShellSet paper, §§2–3](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html)

## ARCANA T0 coverage

The tracked T0 manifests and binding reports agree on identity: 210 Ma, 12 plates, 64,800 parent faces, 1,983 shared boundary segments, 30 adjacent plate pairs, 20 degree-three junctions, and 30 junction-to-junction branches. The boundary kinematic counts (1,091 convergent, 892 divergent) are demands only; they do not define ridge/subduction/transform classes, fault dip, polarity, strength, or slip law.

The physical-geography manifest declares a 180×360 one-degree grid and a land elevation payload with 25–3309.49 m support. Ocean elevation/bathymetry is explicitly unknown. `crust_class` and `province_class` are design categories; they do not encode physical thickness, lithology, density, or rheology. T0 also contains synthetic plate rotations/kinematics, which are not equivalent to ShellSet fixed-node `.bcs` constraints. Canonical identity hashes are recorded in the JSON. Direct access to the external payload was denied by filesystem policy, so the audit used tracked manifests, their field inventory/support masks, validation report and payload hashes; no external data were modified.

## Specialist and authorial gaps

OrbData5 can interpolate or derive values only after data sources and assumptions have authority. It cannot supply that authority itself. GWB can materialize configured temperature/composition structures from a structured feature description and selected models/parameters; it cannot infer those definitions from plate outlines or kinematic convergence. A GWB handoff therefore still requires authorial feature semantics, material labels, thermal-model choices, depth support and parameters. [GWB manual](https://gwb.readthedocs.io/en/v1.0.0/), [official releases](https://github.com/GeodynamicWorldBuilder/WorldBuilder/releases)

Authorial contracts are needed for thermal/heat-flow state; crust and mantle-lithosphere thickness; composition/density/material family; and continuum rheology. If explicit faults or slab constraints are selected, physical boundary class, orientation/dip/polarity and node-selection semantics also need an authority decision. No values are proposed. ARCANA must bind accepted SHELLS laws and parameters; it must not implement a new constitutive model.

## Velocity boundary conditions and adapter

The source archive documents `.bcs` as **fixed-node** velocities: speed in m/s and azimuth in degrees clockwise from geographic north. Earth examples constrain nodes at subducting slabs. Earth iteration files also include fictitious anchors at a few interior nodes per plate; those anchors are released for the final iteration while slab velocities remain. These examples do not establish a generic prescription for every node on every ARCANA plate. Exact absolute/relative frame meaning, time dependence, component-wise constraints, precedence and production interior-node policy remain unknown. [Official source archive index](https://datadryad.org/dataset/doi:10.5061/dryad.cnp5hqcjb)

**ARCANA/pyGPlates → ShellSet status: `SUPPORTED_ONLY_WITH_MODEL_ASSUMPTIONS`.** There is no demonstrated direct ingestion. A future adapter would need an authorized reference frame and node-selection/constraint policy, a mesh-node-to-canonical mapping, pyGPlates velocity evaluation, spherical projection/interpolation with recorded error, conversion to `.bcs` units/azimuth, and preservation checks for plate, boundary, branch and junction identities. pyGPlates can derive kinematic values; it cannot decide which nodes SHELLS should constrain or make those constraints mechanically authoritative.

**Mesh ownership:** ARCANA remains authority for scientific geometry/topology. OrbWin or a validated, versioned mesh producer owns the numerical FEG. Record every projection and correspondence; mesh refinement/subdivision cannot replace canonical boundary identities.

## Faults, junctions and the old patch operator

The published FEG form includes triangular continuum elements and optional linear fault elements. Thus an explicit fault element is not shown as universally required, but a continuum-only setup is not yet proven adequate for ARCANA. When faults are represented, per-element dip is documented; optional lower effective fault friction is documented. The universal fault taxonomy and complete accepted fault parameter contract remain unknown. Do not classify boundaries using convergent/divergent kinematics alone.

**Triple-junction handling: `UNKNOWN`.** A connected FE continuum might couple adjacent elements, but inspected documentation does not establish ARCANA junction identity transfer or an explicit simultaneous triple-junction solution. Preserve canonical junction IDs and require a mapping proof; do not invent a junction law.

**Patch operator:** `ARCANA_CUSTOM_PATCH_OPERATOR_NOT_REQUIRED_FOR_PRODUCTION_CONDITIONALLY`; retain its prior failure as diagnostic evidence. This is conditional on a future proof that the chosen specialist handles the required continuum and any selected connected fault network. No custom ARCANA mechanics are required by this audit.

## Counts and validation

The machine-readable ledger counts **9 documented mandatory families** (6 physical-state and 3 mesh/BC/configuration), **6 optional/conditional families**, **6 scoring-only families**, and **3 Earth-example-only groups**. These are documented families, not parser fields. Zero mandatory families are already fully available in ARCANA; zero are derivable as a complete, authorized SHELLS input through pyGPlates; zero can be completed by another specialist without new input authority. Six physical-state families require authorial initialization. All nine mandatory families remain unresolved as executable bindings; eight interface-gap categories remain. The JSON explains this conservative count and distinguishes provider capability from authority.

Parent decision and canonical identities match the prior toolchain report; the required historical bootstrap identity remains `27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf`. No engine ran, no values were invented, and no future state was created. Validation commands/results will be recorded in the JSON and final response.

## Sources

- [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html)
- [Official ShellSet repository](https://github.com/JonBMay/ShellSet)
- [ShellSet supporting release](https://doi.org/10.5281/zenodo.7986808)
- [SHELLS tools/results archive index](https://datadryad.org/dataset/doi:10.5061/dryad.cnp5hqcjb)
- [Geodynamic World Builder manual](https://gwb.readthedocs.io/en/v1.0.0/)
- [Geodynamic World Builder releases](https://github.com/GeodynamicWorldBuilder/WorldBuilder/releases)
- [ASPECT velocity boundary comparator](https://aspect-documentation.readthedocs.io/en/v3.1.0/parameters/Boundary_20velocity_20model.html)
