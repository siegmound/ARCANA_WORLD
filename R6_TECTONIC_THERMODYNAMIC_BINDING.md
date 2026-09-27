# R6 Tectonic Thermodynamic Binding and Density-State Reconciliation

**Decision:** `R6_TECTONIC_THERMODYNAMIC_BINDING_PARTIAL__PRESSURE_COUPLING_REMAINS`

**Scope:** specialist capability and authority reconciliation only. No scientific engine was installed or run; no physical values, canonical T0 state, future state, or custom thermodynamics were created. ShellSet runtime qualification and first-interval design remain unauthorized.

## Decision summary

ShellSet does not document a need for an independent ARCANA-authored density raster. Its documented FEG carries nodal surface elevation, heat flow, crust thickness, and mantle-lithosphere thickness. OrbData/SHELLS derives thermal density response from depth, heat flow, layer heat production and transient-geotherm inputs; OrbData can add/adjust a chemical-origin density anomaly under its isostatic workflow. A mean crust/mantle density relationship is also part of model configuration/validation. The exact pinned parser and density crosswalk still need source-level binding.

Perple_X can determine stable phase assemblages and aggregate density from bulk composition at prescribed P–T using selected thermodynamic data and solution models. BurnMan can evaluate density and thermoelastic properties for specified minerals, solutions and composites. BurnMan's `Planet` iterates pressure, density and gravity for a completely specified **radial layered planet**. Its `Layer` solves pressure within one spherical layer only when top pressure and bottom gravity are supplied. Neither is documented as a self-consistent solver for ARCANA's laterally varying lithospheric shell. Perple_X does not solve pressure or gravity.

Therefore the remaining principal blocker is assigning an existing specialist to the lateral P–ρ–g/material state without inventing a custom ARCANA iteration or silently treating independent vertical columns as globally self-consistent. The available specialists are capable for their defined domains; their applicability to ARCANA's lateral shell and ShellSet's density semantics is not closed.

## Parent result preserved

The parent decision is `R6_TECTONIC_UPSTREAM_CLASSIFICATION_PARTIAL__THERMODYNAMIC_BINDING_REMAINS`, with exactly these gaps: `CRUSTAL_TYPE_AUTHORITY_GAP`, `TECTONIC_PROCESS_CLASSIFICATION_GAP`, and `THERMAL_DENSITY_MAPPING_GAP`.

This stage preserves the parent conclusions: global tectonic-process classification and GWB are not mandatory for the minimum ShellSet continuum path; OrbData may conditionally derive layer thickness; physical material/composition semantics remain required; ocean elevation and rheology remain separate unresolved matters; no custom ARCANA mechanics is justified.

Canonical invariants remain T0 210 Ma; 12 plates; 64,800 parent faces; 1,983 boundaries; 30 adjacent plate pairs; 20 degree-3 junctions; 30 branches and sections; 1,091 convergent and 892 divergent kinematic-demand edges. Historical bootstrap identity remains `27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf`.

## What ShellSet consumes

The ShellSet v1.1 paper says the lithosphere structure before mechanics consists of surface elevation, crust and mantle-lithosphere thicknesses, densities, and parameters defining internal temperature, specified at FEG nodes. The SHELLS archive describes the nodal FEG fields as elevation, heat flow, crust thickness, and mantle-lithosphere thickness. The author response clarifies that local temperature depends on depth/topography, heat flow, each layer's radioactive heat production, and a non-steady geotherm component; OrbData computes heat flow and non-steady components and adds a chemical-origin density anomaly for local isostatic adjustment. ShellSet also checks that mean crust density is less than mean mantle density.

This does **not** establish a mandatory pressure raster, gravity raster, mineral phase raster, or elastic-modulus field in the FEG. Nor does it establish that absolute EOS density can be substituted directly for OrbData's chemical density anomaly. Thermoelastic outputs beyond density are not needed by the reviewed ShellSet input description and are excluded from the minimum candidate chain.

## Minimum authorial primitives

### Material

Keep two role-specific references: crust and mantle lithosphere. Each resolves to an ARCANA material-family ID and a pinned specialist representation. They may refer to the same material record only if a later authorial decision says they do; this report assumes neither shared nor different composition.

The least prescriptive candidate is a bulk chemical composition expressed on a component basis supported by a chosen Perple_X thermodynamic dataset. A stable ARCANA family ID should point to the component definition, dataset, solution model, version and hashes instead of copying large specialist models into ARCANA. A rock-type label or mechanical class alone is insufficient. Authoring mineral/endmember fractions is more detailed and is only needed if the author intends to prescribe an assemblage instead of computing equilibrium.

### Thermal

Use one T0 thermal initialization model/profile primitive with layer-scoped inputs. The actual values remain undecided. BurnMan requires temperatures at the layer samples in user-defined mode, or an adiabatic/perturbed-adiabatic model with an anchor state. Literature geotherms are reference models, not silently transferable ARCANA defaults. Perple_X evaluates supplied P–T conditions; it does not establish a synthetic world's thermal initial state.

ShellSet's own thermal initialization path uses heat flow, layer heat production, depth and geotherm curvature through OrbData/SHELLS. Pinning that path could derive fields and avoid separate hand-authored temperature and heat-flow rasters, but its exact ARCANA input/parser contract has not been verified here.

## Specialist capability matrix

| Capability | BurnMan 2.1 stable / current 3.0 docs | Perple_X 7.2.6 documentation |
|---|---|---|
| Main role | Mineral physics / thermoelastic property evaluation | Phase-equilibrium petrology from bulk composition |
| Material input | Mineral/endmember, solid solution, combined mineral, composite; EOS/dataset | Bulk composition components, thermodynamic data, solution models and phase constraints |
| Phase equilibrium | `equilibrate` tools exist for configured systems; not presumed necessary | VERTEX phase-equilibrium calculations produce stable phase assemblage/proportions |
| EOS and density | Multiple EOS and density, volume, expansivity, moduli, heat capacity at P–T | Selected data/EOS supports density and bulk properties at P–T; phase-specific extra properties depend on database content |
| Pressure/gravity | `Layer`: local pressure given top pressure and bottom gravity. `Planet`: self-consistent global radial P–ρ–g for layered planet | Uses prescribed P–T; no self-consistent gravity/pressure solver documented |
| Temperature | User profile, adiabatic or perturbed adiabatic layer profiles; published geotherms include literature/Earth references | Supplied T or P–T section/grid; no ARCANA geotherm authority |
| Database | Literature mineral datasets, e.g. HP and SLB families; choose and pin one | Release bundles thermodynamic data and solution-model files; select and pin explicitly |
| API/batch | Python API; suitable for point/profile batches. Dependencies and exact release must be pinned | Fortran CLI suite with project/configuration files and batch-friendly tables; no official Python API found |
| License | BurnMan software GPL v2 or later; data sources need separate attribution/terms review | Copyright identified; reviewed official materials did not establish an OSI/SPDX license grant; verify release terms before integration |
| ARCANA limitation | Radial `Planet` is not lateral-shell gravity; Layer needs externally supplied boundary gravity/pressure | No P–ρ–g closure; requires supplied P–T, and no direct ShellSet adapter |

BurnMan's `PerplexMaterial` (documented in 2.1) reads a 2-D WERAMI P–T tab property table and interpolates properties such as density. The official BurnMan tutorial demonstrates a Perple_X table used as a BurnMan `Layer` material in a Planet example. This is a **format/property-table adapter** for the tabulated properties. It does not automatically map every Perple_X phase identity or phase fraction into BurnMan mineral objects. It also does not solve ARCANA's lateral ShellSet mapping.

## Pipeline adjudication

| Candidate | Phase equilibrium | Density | Pressure/gravity owner | Disposition |
|---|---|---|---|---|
| Bulk composition → Perple_X | Perple_X | Perple_X at prescribed P–T | No owner for lateral ARCANA P–ρ–g; BurnMan radial reference is only a possible future input | Least-prescriptive material route; not closed |
| Specified assemblage → BurnMan | Author specifies; optional BurnMan equilibration is not selected | BurnMan at prescribed P–T | Layer only conditional on boundary P/g; Planet only for whole radial structure | Alternate if ARCANA chooses to prescribe phases; not the minimum if Perple_X provides required density |
| Perple_X table → BurnMan `PerplexMaterial` → BurnMan Planet | Perple_X table | BurnMan Planet using table-interpolated properties | BurnMan closes global radial P–ρ–g | A radial reference chain exists, but current ARCANA state lacks full radial interior authority and the chain does not solve lateral variations |

Do not require both specialists automatically. Perple_X alone can provide the phase equilibrium and density property at defined P–T for the bulk-composition path. BurnMan is useful as a property evaluator for a prescribed assemblage or as a complete radial reference solver. Combining them is documented for radial planet models but does not cure lateral-shell applicability.

## Pressure, density and gravity

The coupling is real: material density depends on pressure and temperature; pressure depends on gravity and overlying density; gravity depends on density. BurnMan `Planet` owns iteration for a layered radial model when the full sequence of radial layers/radii, material models, thermal modes/profiles and boundary conventions are supplied. BurnMan `Layer` can compute pressure within its spherical layer if the user supplies pressure at the top and gravity at the bottom. It does not determine global gravity. Perple_X supplies density at imposed P–T and does not close either pressure or gravity.

The global `Planet` model is a `GLOBAL_RADIAL_REFERENCE`, not a `LATERALLY_VARIABLE_CRUSTAL_COLUMN` solution. Running a separate radial model per ARCANA region would not couple gravity across regions. Assuming a globally radial profile can stand in for lateral P–ρ–g needs an explicit model decision and validation; none is made here. No ARCANA fixed-point, pressure integration, gravity integration, density law or phase solver is proposed.

ShellSet does not document pressure/gravity rasters as direct FEG inputs. Pressure is nevertheless needed for a mineral EOS calculation if composition-derived density is chosen. This keeps the pressure question distinct from ShellSet's direct field requirements.

## Temperature, heat flow, and material data

BurnMan can use a supplied profile or its adiabatic/perturbed-adiabatic modes. Generic adiabatic physics still needs an anchor and material properties. Named geotherms are literature-derived reference curves, not a universal synthetic-world default. The least presumptive ARCANA input remains a chosen T0 thermal model/profile with explicit layer-scoped parameters.

Perple_X consumes P–T; it does not generate a heat-flow field for the ShellSet surface. OrbData/SHELLS can compute heat flow and thermal profiles through its geotherm path given its required input parameters, while the ShellSet paper also permits supplied nodal heat-flow datasets. Therefore heat flow should be specialist-derived if the selected pinned OrbData path generates it; otherwise it remains an explicit input. No ARCANA Fourier implementation is warranted.

Thermodynamic database choice is a physical model choice. Record dataset/solution-model names, exact versions and hashes, component basis, EOS/averaging method, P–T support, options, and citations. BurnMan's software license is GPL v2 or later; dataset citations/terms remain separate. Perple_X release packages bundle data/option files, but the release/data license terms need verification before use or redistribution.

## ShellSet adapter and support

The conceptual flow is:

```text
two ARCANA layer material references + T0 thermal model/profile
                         ↓
              Perple_X at supplied P-T
              [or BurnMan for a specified assemblage]
                         ↓
           phase state / density property table
                         ↓
    pressure and gravity reference if radial Planet is authorized
                         ↓
    OrbData/SHELLS density and geotherm semantic crosswalk
                         ↓
         FEG layer and nodal support adapter
```

No integration was built. Before one is, the adapter contract must define pressure units (BurnMan Pa; Perple_X interfaces/tables may use bar), temperature units (K), density units (kg m⁻³), depth/radius datum and direction, layer boundaries, sampling, interpolation limits, phase/mixture and layer averaging semantics, lateral material support, and how absolute specialist density maps to ShellSet reference means and OrbData chemical-origin anomaly. Record input/output hashes, software/database versions, uncertainty, and projection error.

BurnMan radial and Perple_X P–T support do not resolve ShellSet FEG lateral support by themselves. A vertical discretization adapter and lateral mapping remain open. Do not assign per-plate material uniformity without authority.

## Density authority and counts

Density is `SPECIALIST_DERIVED_PHYSICAL_STATE`, not an independent authorial density raster. Its lineage includes material-family/composition, thermal state, pressure state, thermodynamic database, specialist version/configuration, phase/mixture assumptions, support/averaging, and uncertainty. At present the direct ShellSet mapping remains unverified.

Counts in the JSON use these definitions: **2** role-scoped material references (crust and mantle lithosphere), potentially pointing to **1 or 2** future unique material records; **1** thermal model/profile primitive with per-layer parameter slots; **4** candidate specialist-derived field families (equilibrium assemblage/fractions, density, pressure, gravity, with pressure/gravity only radially closed by BurnMan Planet); **0** fully-authorized ShellSet thermodynamic/material families covered end-to-end; **3** required families still uncovered (density/anomaly crosswalk, thermal/geotherm input binding, lateral pressure-consistent material density); **1** selected database lineage required per chosen path (or separate provenance for a combined path); **2** adapter gaps (density semantics and vertical/lateral FEG mapping); **0** custom scientific physics needed.

## Deferred boundaries and next stage

- `DEFERRED_BLOCKER_OCEAN_ELEVATION`: separate required surface geometry support; not a dependency of the EOS P–ρ–g API itself.
- `DEFERRED_SPECIALIST_CONFIGURATION_RHEOLOGY`: no rheology family or value selected; not WORLD_HISTORY state.
- No global tectonic process classification has been reintroduced; GWB remains optional.
- Runtime qualification and first-interval design remain unauthorized.

Next, resolve only whether a full radial BurnMan reference can be legitimately authorized for the laterally varying ARCANA ShellSet state, or whether an established specialist provides a better lateral P–ρ–g closure; pin the exact OrbData/SHELLS density contract in parallel. Do not implement an ARCANA pressure solver.

## Sources

- [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html); [author response clarifying OrbData heat-flow, thermal density and chemical anomaly](https://egusphere.copernicus.org/preprints/2023/egusphere-2023-1164/); [SHELLS/OrbData archive and FEG fields](https://datadryad.org/dataset/doi:10.5061/dryad.cnp5hqcjb).
- [BurnMan 2.1 stable docs](https://burnman.readthedocs.io/en/stable/), [materials](https://burnman.readthedocs.io/en/stable/materials.html), [Layer/Planet docs](https://burnman.readthedocs.io/en/stable/planets.html), [self-consistent Planet example](https://burnman.readthedocs.io/en/v2.1/examples.html), [Perple_X table integration tutorial](https://burnman.readthedocs.io/en/stable/tutorial_03_layers_and_planets.html), [PerplexMaterial implementation](https://burnman.readthedocs.io/en/v2.1/_modules/burnman/classes/perplex.html), and [BurnMan source/license](https://github.com/geodynamics/burnman).
- [Perple_X release/installation and bundled files](https://www.perplex.ethz.ch/perple_x_installation/perple_x_installation.html), [datafile repository note](https://www.perplex.ethz.ch/perplex/datafiles/), [P–T pseudosections and bulk density](https://www.perplex.ethz.ch/perplex_pseudosection.html), and [WERAMI tables](https://www.perplex.ethz.ch/perplex_66.html).

## Validation

The parent decision and exact gap IDs were read from the committed parent artifact; canonical invariants and bootstrap hash match. JSON parsing passed and `git diff --check` passed for tracked changes; both new untracked files were directly checked for trailing whitespace (none). Git staging was blocked because the linked-worktree index lock could not be created (`Permission denied`). Per the brief, the staging attempt was not repeated; no commit was created and no push was performed.
