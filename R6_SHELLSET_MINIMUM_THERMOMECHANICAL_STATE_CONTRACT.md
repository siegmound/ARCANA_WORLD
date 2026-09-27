# R6 ShellSet Minimum Thermomechanical State Contract

**Decision:** `R6_SHELLSET_MINIMUM_STATE_CONTRACT_PARTIAL__REFERENCE_MATERIAL_PARAMETERS_REMAIN`
**Parent decision reassessed:** `R6_TECTONIC_THERMODYNAMIC_BINDING_PARTIAL__PRESSURE_COUPLING_REMAINS`
**Branch / HEAD at authoring:** `r6/shellset-minimum-state-contract` / `a4021ef39e3fd109d85b1fa979f6a05755ae006d`

## Adjudication

The earlier uncertainty about the minimum specialist path is resolved by the source findings for `OrbData5`, `MOD_Data`, `SHELLS_v5.0`, `MOD_ShellSet` and the standard parameter file, reconciled with the ShellSet paper and author response. **External P–ρ–g coupling, an absolute pressure field, and EOS-generated absolute density are not required by the minimum OrbData5 → SHELLS path.** The pressure-coupling blocker from the parent thermodynamic report is superseded as a branch-specific blocker. This does not close the missing ARCANA physical inputs or authorize a runtime.

The density implementation is ShellSet's reduced model: crust/mantle reference density is thermally corrected using local temperature/geotherm state and `alphaT`, then the node-wise `chemical_delta_rho` correction is applied. Conceptually:

```text
rho_local = rho_reference * thermal_correction(T, alphaT, depth/geotherm) + chemical_delta_rho
```

This is a description of terms and roles, not a replacement equation or generic EOS law. `chemical_delta_rho` is an effective lithosphere-property correction of chemical origin, used/adjusted as a degree of freedom in OrbData's structural/isostatic construction and subject to a configured bound. It is not absolute `rho(P,T,composition)`, nor does it require an authored phase assemblage. `rhoBar` crust/mantle and `rhoAst` are reference/mean material densities under model reference conditions. They are global specialist physical-model parameters, not WORLD_HISTORY density rasters.

`Squeez` constructs a vertical reference-pressure column internally from reference density, surface gravity and depth increments. It integrates the vertical standardized stress anomaly through the plate and returns `tauZZ` and `sigZZB`; `Assign` checks basal anomaly against the isostatic consistency condition. This separates internal reference pressure/stress from any external absolute pressure field and from fault effective-pressure/friction parameters. `gMean` is a global scalar planetary surface-gravity model parameter. No laterally varying gravity field or gravity solver is part of this minimum input contract.

The report uses the source findings supplied in the source-level reconciliation and identifies the official source files for traceability. The published paper independently says OrbData computes the lithosphere structure, including nodal elevations, layer thicknesses, densities and temperature-defining parameters; its current documented paths use local isostasy with a steady-state geotherm or seismically determined layer thicknesses, and assign chemical density anomaly/geotherm curvature at nodes. The author response clarifies the heat-flow, depth, heat-production and non-steady geotherm roles. [ShellSet paper §§2.1–2.2](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html), [author response](https://egusphere.copernicus.org/preprints/2023/egusphere-2023-1164/), [official ShellSet repository](https://github.com/JonBMay/ShellSet).

## Component ownership and minimum nodal state

| Quantity | Owner/path | Classification and ARCANA status |
|---|---|---|
| Elevation | Input or OrbData fill from configured source data | WORLD_HISTORY geometry; canonical land coverage exists, ocean bathymetry remains incomplete. |
| Heat flow | Preserve non-zero FEG node value; otherwise configured data path; ocean path may use seafloor age | WORLD_HISTORY physical state or OrbData-derived field. No synthetic ARCANA heat-flow source is bound. |
| Crustal thickness | Current `OrbData5 Assign` reads it from a grid; it does not derive crust thickness from isostasy | True upstream authority gap. R6 currently records crust/province categories, not physical crust thickness. |
| Mantle-lithosphere thickness | Ocean path may use seafloor age; continental path may use vertical S-wave travel-time anomaly | Conditional OrbData result, dependent on upstream physical primitive/data. Earth grids are not transferable by default; no synthetic equivalent is bound. |
| `chemical_delta_rho` | OrbData node-wise effective correction/degree of freedom, constrained by its configured bound | Derived/adjusted node state; not EOS density or mineralogical composition. |
| Cooling/geotherm curvature | OrbData node-wise non-steady geotherm degree of freedom | Derived/adjusted node state, not a new ARCANA cooling law. |

These are node state written to the modified FEG and consumed in the OrbData/SHELLS chain. Separate from those fields are global Shells parameters such as `gMean`, `rhoBar`, `rhoAst`, thermal coefficients and rheology. OrbData does **not** create crustal-thickness authority in its current `Assign` path: it reads the upstream grid. The paper's statement that OrbData computes layer thickness must be read together with that actual path distinction: mantle-lithosphere thickness can be assigned through age/seismic inputs, while crust thickness remains prescribed by its grid in this path.

### Thermal classification

- **Nodal state or input:** surface heat flow; elevation/depth support; crust and mantle-lithosphere layer geometry; OrbData's cooling-curvature field.
- **Specialist parameters:** `alphaT`, thermal conductivity, layer radiogenic heat production, reference/surface temperatures, temperature limits and geotherm coefficients. Exact values/defaults are not selected here.
- **Internal calculation:** temperature varies with depth relative to topography, local heat flow, layer heat production and the configured non-steady geotherm. A standalone ARCANA temperature raster is not required by the described minimum path.
- **Heat-flow source gap:** OrbData can preserve an existing nonzero nodal field or populate from configured grids/data; its Earth workflow may use seafloor age for ocean heat flow. ARCANA must bind a synthetic field or authorized synthetic input primitive and provenance. Do not import Earth age products.

## Pressure, gravity and composition decisions

- **External absolute pressure field:** not required by the minimum path. The reference pressure/stress column is constructed internally by `Squeez`.
- **External EOS density `rho(P,T,composition)`:** `EXTERNAL_EOS_NOT_REQUIRED`. The reduced ShellSet density semantics use reference densities, thermal correction and `chemical_delta_rho`.
- **External P–ρ–g coupling:** `NOT_REQUIRED_FOR_MINIMUM_PATH`; no global radial BurnMan result or laterally varying pressure/gravity field is an input to the described path.
- **Gravity:** `gMean` is a global scalar planetary parameter for the reference column, not a lateral field. Its value remains unselected.
- **Reference density:** separate crust `rhoBar`, mantle `rhoBar`, and asthenosphere `rhoAst` model parameters. They need later scientific constraints but belong to versioned specialist configuration, not WORLD_HISTORY.
- **Chemical density anomaly:** node-wise, effective, chemical-origin density correction used by OrbData in the structural/isostatic fit; source-configured bound applies. Do not equate it with an absolute EOS density field.
- **Composition:** bulk chemistry, mineral assemblage and phase fractions are not required for this minimum ShellSet formulation. Do not add a categorical mineral ontology to the global path.

The previous parent result remains part of the audit history, but its external lateral P–ρ–g concern no longer controls sequencing. BurnMan is not mandatory; it may be an optional reference-structure tool, high-fidelity validator or targeted refinement. Perple_X is not mandatory; it may be optional petrological refinement or validation. Neither was run.

## Minimum ARCANA state versus model configuration

### WORLD_HISTORY physical state required upstream

1. Complete T0 elevation/bathymetry on the intended node support.
2. A physical crustal-thickness field/grid with authority and provenance.
3. An authorized mantle-lithosphere thickness source: a synthetic lithosphere-age/thermal-state primitive for the applicable age path, a prescribed thickness field, or another physically authorized equivalent.
4. Surface heat flow or an authorized synthetic producer/input path with provenance.

Current parent audits find none of the physical thickness, synthetic thermal/heat-flow or composition/material fields bound in R6 T0; canonical land elevation is retained but ocean elevation is unresolved. pyGPlates geometry/kinematics does not generate those thermomechanical state variables.

### Specialist model configuration

`gMean`; crust/mantle `rhoBar`; `rhoAst`; `alphaT`; conductivity; radiogenic heat production; reference/surface temperatures; temperature limits; geotherm coefficients; chemical-anomaly bound/isostasy controls; rheology and fault/friction law parameters; numerical solver controls. These are not selected. Earth example values/defaults are not promoted into ARCANA.

## Minimum global toolchain

Candidate only; runtime qualification remains unauthorized:

```text
ARCANA T0
  → pyGPlates (geometry, topology, plate-side kinematics)
  → ARCANA-to-OrbData adapter
  → OrbData5 (nodal thermo-structural preprocessing)
  → SHELLS (thin-shell mechanics)
  → ARCANA output normalization and provenance
```

Perple_X/BurnMan may appear only in a separate targeted refinement or validation branch if later justified and authorized. No custom ARCANA mechanics, thermodynamics, pressure solver, duplicate isostasy solver or density EOS is required by this adjudication. Glue remains necessary for mesh/boundary-condition mapping, state-to-OrbData input mapping, output normalization, authority and validation.

## True remaining blockers, in priority order

1. **Crustal-thickness authority:** a physical grid/provider is missing; current OrbData5 reads it and does not solve it from isostasy.
2. **Mantle-lithosphere thickness authority:** synthetic age/thermal-state primitive or authorized prescribed/equivalent field is missing. Earth seafloor-age and continental seismic data cannot be transplanted by default.
3. **Elevation/bathymetry support:** land elevation exists, ocean bathymetry is incomplete/unknown.
4. **Heat-flow/thermal source authority:** synthetic T0 heat flow or authorized synthetic OrbData source inputs are missing.
5. **Reference material and thermal parameter constraints:** crust/mantle `rhoBar`, `rhoAst`, thermal properties and initialization settings need authorial/scientific constraints; no values selected.
6. **Rheology and integration qualification:** rheology/fault parameters, fault/process semantics, pyGPlates-to-FEG/BC/reference-frame mapping, mesh mapping and eventual runtime qualification remain open.

### Superseded blockers

- **Lateral external P–ρ–g/EOS coupling:** superseded branch-specific blocker from `R6_TECTONIC_THERMODYNAMIC_BINDING_PARTIAL__PRESSURE_COUPLING_REMAINS`. The minimum path has reduced reference-density/thermal/anomaly semantics and internal reference pressure/stress.
- **Mandatory bulk composition/mineral-phase ontology:** not required for the minimum ShellSet path described here. It remains an optional high-fidelity branch input only if a later, separate use case requires it.

## Validation and limits

Preserved invariants: T0 = 210 Ma; 12 plates; 64,800 parent faces; 1,983 shared boundary segments; 30 adjacent pairs; 20 degree-3 junctions; 30 canonical branches and sections; 1,091 convergent and 892 divergent kinematic-demand edges. Bootstrap identity remains `27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf`.

No parameter values were selected; no ShellSet, OrbData, SHELLS, BurnMan, Perple_X, ASPECT or GWB engine was run. Canonical T0 was not modified. No future state, `dt`, `t1` or first-interval design was created. Runtime qualification and first-interval design remain unauthorized.

The source findings are tied to the named official code files and standard input file, and cross-checked against the published paper, author response and data archive. The Fortran sources are not vendored into this repository; implementation coefficients/defaults beyond the stated roles must be checked against the pinned release before adapter implementation or runtime qualification.

Validation to perform before commit: JSON parse and required-key assertions; `git diff --check`; compare the bootstrap manifest blob to HEAD; confirm only these two reports changed. No R6 simulation test is applicable to this documentation-only source adjudication.
