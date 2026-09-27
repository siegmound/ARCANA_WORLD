# R6 tectonic authorial primitive constraints

**Decision:** `R6_TECTONIC_AUTHORIAL_PRIMITIVES_CONSTRAINED__READY_FOR_T0_MATERIALIZATION_DESIGN`

**Scope:** source and contract review of physical T0 authorial primitives. No ShellSet, OrbData, SHELLS, GWB or other scientific engine was run. No final T0 field or numeric world parameter was selected. Runtime qualification and forward evolution remain unauthorized.

## Parent authority and preserved T0

I read [the parent closure report](R6_SHELLSET_PRERUNTIME_INPUT_CLOSURE.md) and its JSON directly. Its required decision is `R6_SHELLSET_PRERUNTIME_INPUTS_PARTIAL__AUTHORIAL_PRIMITIVES_REMAIN`. The parent lists four candidate primitive families: ocean elevation/bathymetry support; physical crust-domain/thickness template; oceanic lithosphere age or ridge/formation history; and continental thermal/structural initialization.

The parent’s eight ShellSet input families are surface elevation, crust thickness, mantle-lithosphere structure, heat-flow/thermal state, reference material/density, rheology, FEG mesh, and BC/fault interface. Its six blockers are ocean bathymetry, crust domains/thickness, ocean age plus continental thermal state, reference material/thermal configuration, rheology configuration, and mesh/BC/fault interface.

Canonical T0 remains 210 Ma, with 12 plates, 64,800 parent faces, 1,983 shared boundary segments, 30 adjacent plate pairs, 20 degree-3 junctions, 30 branches/sections, 1,091 convergent-demand edges and 892 divergent-demand edges. Parent hashes are retained: physical geography `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`; vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; kinematics `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`; historical bootstrap `27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf`.

The canonical geography has land elevation support and an ocean unknown mask, but no ocean depths, crust thickness, age, heat flow or temperature. Crust and province categories are design labels, not physical material or thickness semantics. The historical blockers for external pressure/EOS/P-rho-g, mandatory BurnMan/Perple_X, global process taxonomy, arbitrary plate anchors and custom ARCANA mechanics remain superseded.

## Reduction result

The minimum independent authorial vector remains **four families**. No complete family can be removed by derivation with the currently bound state and provider chain. Oceanic age can generate several related fields, and can generate a thermal/isostatic component of bathymetry, but it does not determine all ocean relief. A direct age field is the lower-complexity choice; ridge chronology is an optional way to produce it, not a fifth input.

| Primitive | Minimum authorial representation | Main constraints and uncertainty | Downstream specialist fields |
|---|---|---|---|
| Ocean surface support | Datum-aware, long-wavelength basin/domain residual or low-resolution correlated support, combined with any separately selected cooling/isostatic component | Explicit ocean support and datum; coherent basin scales; no cellwise noise or invented detail. Range-constrained; ensemble recommended. | Complete ocean elevation after explicit component assembly |
| Physical crust-domain/thickness template | Small physical domain ontology (oceanic, continental, and transitional/mixed only where supported) with domain-level thickness ranges | Positive thickness, ordered interfaces, material consistency, domain coherence. Range-constrained; ensemble required until selected. | Crust thickness grid/FEG field through support-aware mapping |
| Oceanic lithosphere age | T0 age field on declared oceanic-lithosphere support; use sparse ridge/source chronology only if separately authorized | Nonnegative, explicit T0 convention and support, coherent age gradients, compatible with any source chronology and selected thermal-model regime. Distribution-constrained; ensemble recommended. | Oceanic thermal profile, heat flow, thermal mantle-lithosphere thickness, and thermal/isostatic depth component |
| Continental thermal/structural domains | Domain-wise structural support and compact 1D geotherm/thermal-state family; include heat-production family only when the chosen model needs it | Explicit surface/basal conditions, consistent heat flux and conductivity, positive thermal thickness under the selected definition, coherent domains. Class-constrained; ensemble recommended. | Continental temperature/geotherm, heat flow and thermal thickness |

The spatial representations deliberately avoid full-resolution authoring. The parent grid’s 1-degree support is not upgraded by interpolation. The physical masks do not license `land == continental crust` or `ocean == oceanic crust`.

## Bathymetry independence test

Published plate-cooling and age-depth models establish that oceanic age, thermal evolution and isostatic subsidence are related. The relationship depends on the selected model and material/boundary parameters; the literature also documents the limitations of simple half-space cooling for older seafloor. This makes a thermal/isostatic component **derivable**, not total bathymetry.

Total ocean-floor elevation can also contain dynamic/tectonic relief, trenches, ridge morphology, intraplate volcanism, sediment loading and basin-specific residual structure. These are not determined by age alone, and current ARCANA kinematic-demand labels do not authorize ridge or trench semantics. The current project has no validated provider that assembles a complete synthetic ARCANA bathymetry from the existing T0 state. Therefore the ocean surface support remains one of the four authorial families. Its first materialization should cover long wavelengths needed by a bounded mechanical input, with optional sparse features only when their authority and model are explicit.

## Crust, ocean age, and continental thermal state

**Crust:** The parent source audit found OrbData `Assign` consumes an upstream crust-thickness grid. It does not infer thickness from the present R6 topology or isostasy. GWB can materialize configured feature properties but cannot choose ARCANA thickness authority. Keep crust thickness as a compact authorial domain template and map it to solver support. Do not infer physical crust domains from current surface or province design labels.

**Ocean age versus ridge history:** Age is the more direct T0 state for cooling. A ridge/formation chronology could causally generate age, but requires explicit source geometry, creation times and spreading history. No such history can be reconstructed from plate IDs or instantaneous rotations, and divergent kinematic demand does not declare a ridge. Ridge history is therefore optional, not mandatory. If selected, keep the minimum semantics to formation source, age/time reference and spreading chronology; do not create a global process taxonomy.

**Continents:** A full authored 3D temperature field is unnecessary if a domain-wise 1D profile family is sufficient for the global thin-shell state. Continental structural domains, thermal family/boundary state and (when required) heat production are still independent because the current craton/suture/orogenic tags do not encode thermal age or seismic structure. A documented geotherm model can expand them into nodal fields after its exact version and input/output contract are selected.

## Derived field graph and configuration boundary

```text
oceanic age field
  -> selected plate-cooling model + versioned thermal/material inputs
  -> ocean temperature/geotherm, heat flow, thermal mantle-lithosphere thickness
  -> thermal/isostatic ocean-depth component

ocean residual basin/domain support + explicitly selected derived component
  -> provenance-aware surface assembly
  -> complete ocean elevation support

physical crust-domain/thickness templates
  -> support-aware domain-to-grid/FEG mapper
  -> crust-thickness field

continental structural/thermal domains
  -> selected documented continental geotherm model + heat production/material config
  -> temperature profile, heat flow and thermal lithosphere thickness

all authored and generated fields + numerical mesh policy
  -> versioned OrbData/SHELLS adapters
  -> FEG-ready input state (not runtime-qualified here)
```

Reference densities (`rhoBar`, `rhoAst`, applicable water term), thermal coefficients, heat production, rheology, numerical controls and mesh/BC policy remain specialist/model configuration, not WORLD_HISTORY rasters. Their values are not selected. Keep the parent constraints: mean mantle density must exceed mean crust density; applicable fault friction is below continuum friction. Map the already-authorized R6 gravity baseline to `gMean` only after checking the exact ShellSet convention. Material families constrain crust structure and thermal models; thermal coefficients condition age/geotherm materialization.

The specialist assignment is a **design candidate**, not a qualification: GWB feature cooling or another pinned plate-cooling implementation for oceanic fields; a pinned OrbData age route only if its exact contract supports the selected age source; a documented continental geotherm model for continental profiles; and a support-aware adapter for crust templates. No one has been selected or executed. Exact versions, units, mesh sampling and adapters belong to the next integrated design stage.

## Counts and readiness

- Parent primitive families: **4**.
- Eliminated as complete families by scientific derivation: **0**.
- Final independent authorial primitive families: **4**.
- Specialist-generated downstream field families: **5** (ocean thermal profile, ocean heat flow, ocean mantle-lithosphere thickness, thermal/isostatic bathymetry component, and continental profile/heat-flow/thickness family). Crust grid projection is a materialization adapter, not an inferred science field.
- Range-constrained primitive families: **4**.
- Ensemble-recommended primitive families: **4**.
- Direct full-field authorial primitives: **0**.
- Remaining provider gaps: **2** (total ocean surface assembly including nonthermal residual relief; pinned continental specialist/provider adapter).
- Remaining scientific transformation gaps: **2** (validated treatment of nonthermal ocean relief; selected and parameterized crust/geotherm transforms for ARCANA domain families).

This passes the requested constraint gate because each remaining family now has explicit physical meaning, a lower-dimensional spatial representation, constraint types, uncertainty treatment, and a stated materialization route or an explicit authorial residual where science cannot generate it. It does **not** close the parent’s six ShellSet runtime blockers or claim runtime readiness.

## Next stage and validation boundary

Proceed to one integrated **T0 materialization + ShellSet configuration + adapter design** stage. That stage should define domain schemas and constrained ranges/ensembles, choose and pin cooling/geotherm specialists, specify total ocean surface composition and provenance, define crust-template projection, bind configuration ranges, finalize mesh/BC invariants, and prepare the runtime manifest. It may not be interpreted as numerical T0 selection, engine execution, ShellSet runtime qualification or first-interval authorization.

Validation for this report: parent decision/counts and canonical identities were read directly; this JSON is required to parse; `git diff --check` is required before commit; bootstrap identity is checked against the parent hash. No canonical payload is changed. Source review only; no scientific engine or test suite is claimed as run.

## Scientific sources

- [Holdt et al., *Revised Oceanic Plate Cooling Models* (2025)](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JB029890) — joint age-depth/heat-flow constraints and plate-model dependence.
- [Parsons & Sclater, *A model for the global variation in oceanic depth and heat flow with lithospheric age*](https://www.nature.com/articles/359123a0) — established age-dependent depth and heat-flow model family.
- [Sclater et al., *The relationship between depth, age and gravity in the oceans*](https://academic.oup.com/gji/article/166/2/553/562527) — cooling/subsidence basis and limitations of simple half-space behavior for old floor.
- [Hasterok & Chapman, *Heat production and geotherms for the continental lithosphere*](https://www.sciencedirect.com/science/article/pii/S0012821X11002500) — material- and domain-conditioned continental geotherm model family.
- [Official GWB Oceanic Plate documentation](https://gwb.readthedocs.io/en/latest/user_manual/parameter_documentation/features/oceanic_plate.html) and [GWB methods paper](https://se.copernicus.org/articles/10/1785/2019/) — configured feature/property materialization, not primitive authority.
- [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html) — downstream ShellSet and OrbData input/model roles carried from the parent audit.

Earth results in these sources constrain plausible physics and model choice only; none is imported as ARCANA observational data or a selected value.
