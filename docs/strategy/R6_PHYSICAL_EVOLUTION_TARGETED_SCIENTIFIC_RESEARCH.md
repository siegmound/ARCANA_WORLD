# R6 Physical Evolution — Targeted Scientific Research

**Research date:** 2026-09-24
**Repository baseline inspected:** `main`, `592b1651b405363373590092e133bd25569d99a5` (`origin/main` matched)
**Scope:** architecture/tool/literature adjudication only; no installation, provider acquisition, or simulation.

## Executive conclusion

R6 does **not** need a full mantle-convection solver as a prerequisite for a useful 1° global physical history. It does need more than rigid plate kinematics if the target history is to include causal breakup, collision, crust/domain transitions, macro-relief, and shorelines. A layered **hybrid process-constrained architecture** is the best-fit architecture class:

1. ARCANA owns the physical-state schema, causality, event records, stochastic seed lineage, uncertainty, forcing, checkpoints, validation and canonical-history policy.
2. An ARCANA-owned reduced-order tectonic law must generate/authorize rotations, boundary changes and vertical-motion fields. It may use Earth literature as parameter priors, not copy Earth/A1 trajectories.
3. pyGPlates can be evaluated as a deterministic spherical geometry/topology resolver for ARCANA-supplied plate rotations and topological features. It is not a motion-physics generator.
4. A landscape-evolution model (FastScape or Badlands/eSCAPE) is downstream of tectonic uplift/subsidence and climate/base-level inputs. It is a regional refinement candidate first, not the global plate solver.
5. Preserve the global 1° history, with plate boundaries and events stored as vector/topological state independent of that raster; regional high-resolution replay receives those boundary conditions and retains its own physical provenance.

The research **supports this architecture class**, but it does not authorize the missing reduced-order laws or any replay. The next contract can freeze layer interfaces and fail-closed prerequisites; actual implementation/execution must wait for ARCANA's explicit plate-motion, breakup/boundary, orogeny/topographic, sea-level and uncertainty authorities. Full 3-D mantle dynamics remain an optional future model, not a default requirement.

**Decision state:** `RESEARCH_SUPPORTS_R6_PHYSICAL_EVOLUTION_ARCHITECTURE`
**Verdict:** `HYBRID_LAYERED_ARCHITECTURE_SUPPORTED__CAUSAL_LAWS_STILL_REQUIRE_AUTHORITY`
**Ready to write architecture/physical-evolution contract:** yes.
**Ready to implement/run a physical interval:** no.

## Scientific requirements and boundary

The initial state is a newly designed synthetic Earth-scale world at 210 Ma, with 1°/180×360 global base grid, materialized and validated. It is Pangaea-inspired, not a claim about observed Earth at 210 Ma. The R6 specification explicitly marks plate motion, numeric bathymetry, Deep, climate, and hydrology as unknown/unbound and marks A1 as reference/design evidence, not numeric R6 authority.

R6 should proceed only forward from this t0. Historical Earth models may inform plausible ranges, rates, mechanisms and validation envelopes. They may not prescribe R6's continent paths, event chronology, or map states. In particular, `R6 state(t) = A1 state(t)` and generic interpolation of A1 frames are forbidden absent later quantity-specific promotion.

The research does not license an arbitrary seeded random walk. Seeded randomness provides reproducibility, not scientific causality. Any stochastic event needs a governed state/driver-conditioned law, a declared prior or authorial constraint, a seed lineage, and uncertainty reporting.

## Repository capability boundary

The repository audit for the prior R6 adjudication found:

- `R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json` and its paired files bind a synthetic t0 design, not a geodynamic law; plate motion is unknown and bathymetry is not materialized.
- R6 generator/topography modules generate initial relief/province patterns. They do not simulate tectonic uplift, erosion, plate motion, or shoreline history.
- R6 latent geometry/refinement is useful for deterministic procedural regional geometry. It does not increase geological authority or provide a time-dependent state.
- `references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz` is a precomputed 210→0 Ma reference trajectory (SHA256 `9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f`). It is not an R6 history.
- `src/arcana_worldsim/post_cha1/paleogeographic_history.py` and `src/arcana_worldsim/late_cenozoic/paleogeography.py` implement A1 endpoint/event-constrained land-support reconstruction, not a physical driver for the synthetic R6 planet.
- `src/arcana_worldsim/scientific_engines/r310_cha1_highres_bridge.py` freezes tectonics across the short CHA-1 bridge. R3.11/14/18/20 and R3.27/28 are ecological, exposure, climate-clock, hazard, human replay, or downstream boundary machinery; none supplies a 210 Ma geodynamic law. R3.14 itself says its adaptive clock is a scheduler, not physics.
- R4.0 supplies engine inventory/orchestration governance. ARCANA stays sole canonical-state owner; engine outputs are bounded evidence.
- Deep contracts bind biological/energy/genetic semantics and historical replay dependencies, not Deep→mantle causality. For R6 geodynamics this remains unknown/optional-model coupling, not canon.
- The prior local candidate scan found no governed R6 engine-suitability decision for FastScape, ASPECT, Underworld, GPlates, or Badlands. This task is the research comparison, not provider acquisition or engine validation.

### Legacy ARCANA engine inventory (preserve; downstream)

The following current R4 roles are retained. None is a direct geodynamic engine. “Keep” means preserve the integration in its intended R6 domain, not invoke it in this task.

| Engine | Actual prior ARCANA use / current R6 domain | Direct geodynamics? | Potential downstream R6 role | Keep existing integration? |
|---|---|---:|---|---:|
| NEMO | Quantitative-genetics reference/sensitivity oracle | No | Genetics validation | Yes |
| SLiM | Individual-based genetics, ancestry, selection | No | Detailed genomic/evolutionary replay | Yes |
| tskit | Tree-sequence storage/analysis | No | Ancestry data model/tooling | Yes |
| msprime | Population-genetic simulation/coalescent tools | No | Ancestry/genetic inference | Yes |
| pyslim | SLiM tree-sequence interoperability | No | SLiM provenance and analysis | Yes |
| Geonomics | Spatial individual/genomic regional backend | No | Regional ecology/demogenetics after habitat fields exist | Yes |
| CDMetaPOP | Spatial demography/dispersal/genetics oracle | No | Secondary demogenetic validation | Yes |
| RangeShiftR | Species range/dispersal specialist | No | Later range dynamics | Yes |
| Madingley | Ecosystem/trophic opportunity provider | No | Later ecosystem support | Yes |
| BIOME4 | Vegetation/ecological-opportunity provider | No | Later vegetation/habitat boundary conditions | Yes |

These are not discarded, but all are downstream of physical geography and remain untouched here.

## Candidate/tool inventory

Status and versions below were checked against official documentation/repositories on 2026-09-24. Capabilities are software capabilities; none alone establishes R6's physical laws.

| Candidate | Current status/version and license | Class / useful capabilities | Custom synthetic R6 fit and limits | Cost / role for R6 |
|---|---|---|---|---|
| **GPlates** | Public release 2.5; GPL-2.0 | Desktop GIS/reconstruction application; GPML feature collections, plate IDs, rotation models, topological lines/polygons/networks, raster/vector I/O | Custom features/plate IDs/rotation models can be authored. Topological plates/networks support time-varying boundaries and deformation when supplied. Splits/merges/appearance/disappearance are represented by changes in time-dependent features/rotation topology. It reconstructs/resolves a supplied model; it does not derive the force law, decide where to rift, or produce an independently physical synthetic trajectory. GUI + headless/programmatic pyGPlates possible. | Promising geometry layer; adapter/install and deterministic replay evidence still needed. Global geometry is queryable; high-res regional geometry remains possible. |
| **pyGPlates** | 1.0.0 release; GPL-2.0 | Python API to GPlates rotation, reconstruction, topologies, deformation, velocities/strain, features and file I/O | Can accept custom feature collections, plate IDs and rotation/topology inputs. It can be ARCANA's geometry/topology solver **only in the bounded sense of resolving supplied kinematics/topologies**. ARCANA must determine motion, feature lifetimes, split/merge semantics, boundaries, event laws, vertical response and validation. API is deterministic for fixed binary/version/inputs in principle; strict reproducibility must be proven by adapter tests. | Likely practical for geometry calculations on consumer hardware; build/runtime identity must be pinned. Not a causal solver by itself. |
| **GPlately** | 2.0.0 (2025-07-14); GPL-2.0 | Higher-level Python analysis/reconstruction wrapper around pyGPlates; model management, velocity/subduction/spreading analysis, raster reconstruction and parallel-safe analysis | Same custom-model caveat as pyGPlates; simplifies interrogating supplied models, does not infer synthetic R6 motion physics. It is not a different dynamics engine. | Candidate convenience/API layer; useful after model format is selected, not mandatory in the core. |
| **Fastscape / Fastscapelib** | Fastscape Python v0.1.0 is latest tagged release found; BSD-3-Clause. C++ Fastscapelib is active; GPL-3.0. Fortran Fastscapelib is mature but slower-moving; GPL-3.0. Check exact components/licenses at binding. | Modular landscape evolution: drainage/flow routing, stream-power incision, hillslope diffusion and related surface-process components; tectonic uplift/subsidence is an input/coupling, not a plate solution. FastScapeLib Fortran is O(n), implicit for specified stream-power/sediment processes and designed to couple with a tectonic model. | Suitable downstream of an ARCANA tectonic displacement field. Existing documented grid APIs emphasize rectilinear/raster/planar domains; do not presume a globally conservative spherical 1° mesh. Regional projected/local domains are a natural fit; global use needs spherical metrics, seam/pole and boundary validation. | Local/regional landscape replay likely feasible; runtime depends on grid/process/forcing. Do not assert global feasibility without benchmarks. Best role: regional refinement or validated surface post-process; global only after spherical adaptation tests. |
| **Badlands / pyBadlands; eSCAPE** | Current `badlands` source branch reports 2.3.1; LGPL/GPL license metadata differs across repository generations/components, so exact distribution must be pinned. Legacy pyBadlands v2.0.0 is DOI-archived (2018). eSCAPE paper/software is 2018–19 generation; verify maintained branch before use. | TIN/unstructured landscape/basin evolution, hillslope and fluvial incision, sediment transport/deposition, spatial/temporal horizontal+vertical tectonics, climate and sea-level boundary forcing; eSCAPE uses Python/Fortran and PETSc/MPI, published as regional-to-global-scale LEM. | Can take externally defined tectonic forcing; it does not generate plate kinematics or independently decide breakup. Broad physical/surface feature set is attractive, but its mesh/domain semantics, global sphere/dateline/poles, restart fidelity and current exact license/runtime need a pinned audit. | Regional to large-domain LEM; HPC/parallel options exist. Potentially more capable than FastScape for sedimentary basin/source-to-sink questions, but greater input and runtime burden. Do not name it the global tectonic solver. |
| **ASPECT** | Current release 3.1.0 dated 2026-09-19; GPL-2.0-or-later | Parallel FEM planetary/geodynamic solver: mantle convection, lithosphere rheology, spherical shells, free-surface options and coupled FastScape mesh deformation; checkpoint/restart documented | Can model coupled physical processes when material laws, initial conditions and boundary conditions are specified. A custom Pangaea-like geometry could be an initial/boundary feature, but a usable model needs a full thermal/rheological/force state not present in R6. It does not automatically provide validated synthetic-world initial physics. | HPC preferred/likely required for useful 3D global long-duration runs; 6-core/32-GB local practicality not demonstrated. Highest physical closure, also highest parameter, initialization and validation burden. Not justified as minimum. |
| **Underworld3** | Current release 3.0.0; LGPL-3.0 module, docs/examples CC-BY-4.0 | Python-friendly, symbolic finite-element geodynamics using PETSc; Stokes/convection, 2D/3D, composable constitutive models; spherical/annulus examples and HPC/cloud targeting | Can express custom synthetic constitutive/boundary models, but user must implement laws and initial temperature/composition/material state. No automatic surface plate breakup law is supplied by the framework. | Desktop test models possible; production 3D global 210 Myr trajectory is HPC-preferred and unbenchmarked for ARCANA. Very flexible, meaning high verification/implementation burden. |
| **TERRA-NG** | 2026 preprint/research software; GPU-scale solver; not a mature consumer-PC candidate | Extreme-scale GPU mantle convection | Full geodynamics, not a reduced synthetic plate kinematics framework. | HPC/exascale research direction only; not R6 candidate for local global history. |

### Direct answers: GPlates

**Can GPlates operate on a completely synthetic ARCANA planet?** Yes, in the data/model sense: its feature model accepts user-defined geometries, plate IDs, finite rotations and topology features. Its geometry is spherical. A synthetic world does not need to be an Earth reconstruction dataset.

**Can ARCANA define its own kinematics and use pyGPlates?** Yes, as a geometry/topology resolver for ARCANA-authored rotation and topology history. GPlates can resolve rotations, topological plate polygons and deforming networks, and compute velocities/strain from that supplied history. It cannot infer plate-driving forces or scientifically choose the rotation histories. Thus it is a viable *kinematic execution layer*, not a *kinematic law authority*.

**Does GPlates supply plate splitting/merging?** It supplies topological representations and reconstruction operations whose time-varying features can encode boundaries and changing plate topology. ARCANA must author valid temporal lifetimes, plate identity succession and causal split/merge rules. It does not automatically generate a new plate because a supercontinent should break up.

### Full geodynamics: adversarial conclusion

ASPECT and Underworld solve the physical PDE systems they are given; their sophistication is not evidence that R6 has the inputs to configure them. R6 presently has no 210 Ma mantle temperature/composition/thermal anomaly, lithosphere thickness/rheology, slab/subduction state, energy/force law, or geodynamic boundary conditions. Initializing these synthetically would itself be a large new model authority. A credible global 3-D 210 Myr ensemble is not evidenced as consumer-PC work; exact runtime depends on discretization, timestep, rheology and convergence. Full geodynamics is therefore **not required**, but is **not locally justified as the first R6 engine**. It may later serve sensitivity/method validation if a Deep/thermal initializer and computational case are separately authorized.

### Landscape models: adversarial conclusion

FastScape and Badlands/eSCAPE evolve surfaces under supplied uplift/subsidence and climate/sea-level forcing; they do not solve the plate/mantle cause. FastScape is simpler/modular and its efficient algorithms suit repeated regional experiments. Badlands/eSCAPE offers richer sediment/basin and tectonic-displacement input, with additional TIN/PETSc/MPI/mesh complexity. Neither should be given fabricated 210 Ma bathymetry or precipitation. Neither should be called high-resolution global evidence solely because it can rasterize a dense output.

## Architecture options (no aggregate score)

| Option | Scientific defensibility | What it solves / does not solve | R6 tradeoff and disposition |
|---|---|---|---|
| **A. Custom ARCANA kinematic model** | High transparency only if laws and constraints are explicit; pure arbitrary rotations/events are not causal science. | ARCANA controls whole causal/event/checkpoint schema; must implement spherical geometry, topology validity, velocities, split/merge, validation itself. No mantle or landscape physics unless added. | Maximal governance fit, high custom burden. Do not implement as unconstrained random walk. Suitable only if narrow model research defines it. |
| **B. GPlates/pyGPlates kinematic core + ARCANA rules** | Strong geometric representation for supplied rotations/topologies; physical validity resides in ARCANA rules, not GPlates. | Spherical rigid rotations, continuously closing plate topology/deforming networks, feature lifetimes, derived velocities/strain. Does not derive forces, rift location/timing, subduction or orogeny. | Best candidate for the geometry execution layer; custom-world compatible. Pin adapter/runtime and prove restart determinism before use. |
| **C. pyGPlates + ARCANA process rules + FastScape-like LEM** | Best functional coverage for global macro tectonic history plus regional surface response, conditional on law binding. | Adds causal state transition/event rules and erosion/sediment response; LEM needs physical tectonic forcing and climate/base levels. | Preferred target architecture class. Global plate state remains vector/topological and coarse; LEM starts regional. Most balanced but not yet executable. |
| **D. Full ASPECT geodynamics** | Strongest direct continuum geodynamics when initial/boundary/rheology models are defensible. | Mantle, lithosphere and surface coupling; not automatic R6 initial physics, deterministic narrative history, or low-cost ensembles. | Too much unbound initialization and compute for minimum R6. HPC required/preferred. Retain as future optional comparator. |
| **E. Full Underworld3 geodynamics** | High physical flexibility and mathematical expressiveness; results depend on user constitutive model choices. | Stokes/thermal/material process models; does not supply a canonical planet model or ready-made R6 plate regime. | Research-grade, high coupling/build/verification burden. HPC preferred for global 3D. Not first R6 implementation. |
| **F. Badlands/eSCAPE as coupled tectonic-landscape system** | Strong surface-system representation under externally prescribed tectonic forcing; not full geodynamics. | Landscape/basin/sediment plus imposed horizontal/vertical tectonics. No endogenous global plate law. | Viable alternative to FastScape for large domains/source-to-sink studies; regional-first, with global spherical compatibility unresolved. |

No weighted score is used: causal law authority and initialization are gating criteria, not compensable scores.

## Decision matrix

Legend: **Strong** = native intended capability; **Conditional** = requires supplied laws/adapter; **Weak** = possible only through substantial custom work; **No** = not its role.

| Dimension | ARCANA custom kinematics | pyGPlates + ARCANA | pyGPlates + ARCANA + LEM | ASPECT | Underworld3 | Badlands/eSCAPE |
|---|---|---|---|---|---|---|
| Custom synthetic world | Strong | Strong | Strong | Conditional | Conditional | Conditional |
| Causal plate motion | Conditional | Conditional | Conditional | Strong if physical IC/laws bound | Strong if physical IC/laws bound | No (takes forcing) |
| Spherical plate topology | Weak/custom | Strong | Strong | Spherical physical domain, not a plate reconstruction model | Spherical/annulus physical domain, not plate model | Weak/adapter required |
| Breakup and splitting | Custom law required | ARCANA law + topology encoding | ARCANA law + topology encoding | Emerges only if configured physics resolves it | Emerges only if configured physics resolves it | Forced tectonic displacement only |
| Collision/orogeny | Custom law required | ARCANA law + boundary state | ARCANA law + relief coupling | Physical process possible; configuration required | Physical process possible; configuration required | Imposed vertical/horizontal tectonics |
| Macro-topography | Custom | ARCANA surface law | ARCANA + LEM response | Coupled options, but high cost | Coupled custom model | Surface solver |
| Erosion/sedimentation | Custom | No native LEM | Strong via selected LEM | FastScape coupling available | Must couple/build surface response | Strong |
| 210 Myr execution | Computationally possible but scientific rates unbound | Same | Same; landscape workload scales with mesh/process | HPC and large model setup | HPC/model dependent | Long LEM horizons are within intended scope, forcing-dependent |
| Global 1° base | Yes, but sparse vector data needed | Strong geometry; raster only output | Conditional spherical raster/metric adapter | Global 3D, not equivalent to 1° surface physics | Global 3D possible with HPC | Published global-scale LEM but spherical R6 compatibility unproven |
| Regional refinement | Strong if implemented | Strong geometry | Strong candidate | Regional 3D possible but heavy | Regional model possible | Strong unstructured-domain candidate |
| Reproducibility/checkpoint | ARCANA must build | Inputs/version pin; adapter tests | Combined restart testing required | Native restart, solver/runtime exactness still needed | Checkpoint/runtime validation required | Need adapter-specific restart validation |
| Consumer PC feasibility | Likely for vector kinematics (benchmark required) | Likely for geometry; benchmark required | Regional LEM likely; global proof required | Not demonstrated; HPC preferred | Small demos yes; global 3D no evidence | Small/regional possible; large parallel runs may need HPC |
| ARCANA implementation cost | High | Medium-high | Medium-high | Very high | Very high | Medium-high |

## Recommended R6 architecture

### Global base physical history

1. **Canonical ARCANA state is vector/topological first.** Keep plate polygons/boundaries, feature time intervals, plate IDs, crust/domain support, kinematic state, event records, macro-elevation and uncertainty as separate typed components. The 1° land/ocean/elevation rasters are derived views, never the sole truth.
2. **ARCANA tectonic law layer.** A future governed law owns plate-motion generation, boundary transition, rift/collision event conditions, IDs/lifetimes, vertical surface response, event uncertainty and causal dependency graph. Prefer finite spherical rotations for rigid plate interiors; represent deforming/rifting networks explicitly rather than smearing categorical plate IDs. Motions must be driven by declared state/forces/priors, not unconstrained time-correlated noise.
3. **pyGPlates geometry adapter candidate.** Resolve ARCANA-authored rotations and topologies, validate closure/gaps/overlaps and export vector fields. It is not allowed to invent rotations or events. ARCANA retains normalized canonical state and writes immutable solver evidence/checkpoints.
4. **Macro-topography/land-sea.** Apply governed uplift/subsidence and crust/domain changes to macro topography; derive a land mask against a declared sea-level datum. Keep tectonic vertical motion separate from eustatic/climate sea-level effects. Use unknown bathymetry until an ocean/basin process requires it.
5. **Adaptive physical stepping.** Bound accepted integration steps by event boundaries, topological changes, angular/displacement limits and solver stability/error diagnostics. Numbers require a specified law and convergence tests. Checkpoints are restart-complete solver state; historical snapshots are normalized query products and are not substitutes for checkpoints.

### Regional high-resolution replay

Use the validated R6 latent geometry/refinement contract to obtain region-specific starting support without raster upsampling. Pass explicit global plate/topology, macro-topographic, event, vertical-motion and sea-level boundary conditions. A regional LEM (FastScape or Badlands/eSCAPE) is a candidate after native-grid/geodesy and restart tests; output keeps provider resolution, process assumptions and uncertainty. It cannot promote coarse global plate/province categories to high-resolution geological evidence.

### Layer-specific conclusions

| Question | Finding |
|---|---|
| Full geodynamics required? | **No** for a bounded global macro-history, if ARCANA binds and validates a reduced-order process-constrained plate model. Full mantle dynamics may be optional research/ensemble evidence. |
| Is plate kinematics sufficient? | **No** for the requested complete physical history: kinematics move geometry but do not govern breakup, ocean-crust creation, convergence response, uplift/subsidence, erosion or sea-level shoreline effects. It can suffice only for an explicitly narrower geometry-motion phase. |
| Physics beyond kinematics | State-conditioned rift/boundary rules, split/merge lineage, convergent/subduction/collision semantics, vertical tectonic response and mass/area/topology accounting. Add erosion/sedimentation only at the scope requiring it. |
| Can pyGPlates be the custom kinematics layer? | **Yes, bounded:** geometry/topology resolution for ARCANA-defined finite rotations and time-dependent features. It cannot derive the motion law. |
| What ARCANA must supply for GPlates | Initial geometries and plate identities; rotation/event generation; time-dependent feature validity; split/merge/appearance semantics; physical cause and priors; crust/ocean production accounting; uplift/subsidence; seed/uncertainty; invariant and restart contract. |
| FastScape role | Prefer **regional refinement/topography post-process** initially. Global 1° is unproven due spherical/seam/polar and support assumptions; an adapter/benchmark could later qualify it. |
| ASPECT/Underworld justification | Not justified as minimum; full PDE initialization and HPC-scale validation outweigh incremental benefit before physical priors exist. |
| Minimum breakup model | No scientifically safe numeric law can be frozen from software research alone. Require weak-zone/province state plus an explicit extensional driving/weakening process and split/oceanic-domain lifecycle; use seeded draws only from governed priors. Weak zones/localization and multiple causal drivers matter; “split at seed-chosen longitude” is not defensible. |
| Minimum collision/orogeny | Convergence/boundary type and crust/domain properties feed a declared shortening/thickening/uplift/subsidence response with mass/area bookkeeping and bounded topographic output; numerical constitutive coefficients remain to be studied. |
| Plate velocity representation | Rigid plates use spherical finite rotations/Euler poles; moving/deforming boundaries require topological networks or explicit deforming fields. Earth measurements provide priors (typical cm/year and documented temporal changes), not a fixed R6 speed schedule. Avoid arbitrary independent per-step vector random walks. |
| Bathymetry before first replay? | **No** for a narrowly bounded continental kinematic/topographic phase that leaves ocean depth unknown. **Yes before** basin-depth evolution, bathymetry-dependent shoreline/shelves, ocean circulation, or ocean/climate coupling. |
| Deep before first replay? | **No current canonical requirement established.** Keep a potential interface only. If later selected, require Deep physical initialization and an explicit Deep-geodynamic coupling contract. |
| Preserve uncertainty | Initial partition, weak-zone/thermal assumptions, rate priors, boundary changes, subduction polarity, vertical response, sea-level forcing, and LEM parameters; separate seeded realization from ensemble variation and structural/model uncertainty. |
| Physical checkpoint | Plate/topology geometry and lifetimes; rotations/velocity state; boundary/process state; crust/domain and macro-relief; forcing/event queue and RNG lineage; optional sea-level/Deep coupling state; solver and dependency versions; mass/area/topology diagnostics; restart-required internals and parent hashes. |
| Temporal strategy | Event-adaptive: explicit breakup/boundary/collision/forcing boundaries plus max angular displacement, local process time scales and numerical error/stability limits; do not prescribe one global step before solver choice. |
| Best global / regional tools | Global: ARCANA-owned canonical plate/event state + pyGPlates as a bounded topology/kinematics geometry adapter. Regional: ARCANA boundary conditions + selected FastScape or Badlands/eSCAPE LEM after suitability benchmark. |

## Earth as parameter prior, not history copy

Earth literature documents broad plate-motion ranges and changes tied to plate-boundary forces; it also shows that rift localization depends on inherited lithospheric weaknesses and can involve plume/mantle processes. These sources support parameter priors and a requirement that breakup be state/force-conditioned. They do not identify ARCANA's weak zones, choose its split location, set its event chronology, or authorize its Deep coupling. The R6 realization must stay synthetic and be selected against prespecified broad physical/authorial constraints, never by visual resemblance to Earth, A1 agreement, or narrative outcome.

## Computational feasibility and reproducibility

- **Consumer machine (6 cores/12 threads, 32 GB):** a compact vector-kinematic model and 64,800-cell output are plausibly practical, but must be benchmarked. Regional LEM may be local-practical at bounded mesh sizes. No evidence supports claiming global 210 Myr surface process runs or full 3D geodynamics practical without a benchmark.
- **HPC:** appropriate for 3D mantle convection, large-resolution ensembles, or large unstructured LEM domains. Do not choose it before physical initialization/parameter authority.
- Pin executable/package/source commit, compiler, Python and numerical libraries, grid/mesh, input hashes, units, tolerances, event/seed lineage and thread policy. Test restart equivalence and deterministic outputs; “deterministic” should mean bitwise or documented numerical tolerance, not assumed from a fixed random seed.
- Store canonical vector state and compact manifests in ARCANA; heavy checkpoints as hash-registered external payloads. A raster snapshot does not replace event/topology/restart state.

## Exact contracts still needed before implementation

The architecture contract can be written next, but an executable law contract must fail closed until the following are separately bound:

1. `R6_PLATE_KINEMATIC_STATE_AND_ROTATION_CONTRACT`: rigid/deforming plate semantics, coordinate/units, frame/anchor, rotation integration, identity/lifetime rules, topology validity and uncertainty.
2. `R6_BREAKUP_AND_BOUNDARY_TRANSITION_LAW`: state variables/weak zones and physical trigger; rift localization/propagation; creation and accounting of oceanic domain; seeded-event priors and bounds; boundary type transitions and merge/split lineages.
3. `R6_CONVERGENCE_OROGENY_AND_MACROTOPOGRAPHY_LAW`: subduction/collision scope, crustal thickening/vertical displacement, volcanic treatment (if any), basin development, conservation/accounting and elevation support.
4. `R6_SEA_LEVEL_AND_BATHYMETRY_DEPENDENCY_CONTRACT`: separation of tectonic vertical motion, eustatic/ice/climate forcing, datum, coastline semantics, and the gate that promotes numeric bathymetry from unknown.
5. `R6_TEMPORAL_INTEGRATION_CHECKPOINT_AND_UNCERTAINTY_CONTRACT`: adaptive controls, stable/restartable physical state, ensembles, canonical realization-selection criteria and validation tolerance.
6. If ARCANA elects Deep forcing: `R6_DEEP_PHYSICAL_INITIALIZER` and `R6_DEEP_GEODYNAMIC_COUPLING_CONTRACT`. Otherwise Deep remains off/unknown, not silently forced.
7. A separate engine-suitability/binding decision for the selected geometry adapter and regional LEM, including license, build/runtime, native grid/geodesy, I/O and restart tests.

These are contract packages for a single architecture path, not proposed extra micro-gates. No coefficients, event ages, stochastic distributions, solver timesteps or trajectories are authorized by this research document.

## Literature and current-source register

Accessed 2026-09-24. Project docs/repositories establish software capability/status/license; cited papers establish scientific methods or application examples, not R6-specific authority.

### Official software sources

- [pyGPlates 1.0 documentation](https://www.gplates.org/docs/pygplates/), [topology/reconstruction primer](https://www.gplates.org/docs/pygplates/pygplates_primer), [custom geometry/plate-ID import example](https://www.gplates.org/docs/pygplates/sample-code/pygplates_import_geometries_and_assign_plate_ids), [GPlates release page](https://github.com/GPlates/GPlates/releases), [GPlates source/license](https://github.com/GPlates/GPlates).
- [GPlately 2.0.0 release notes](https://github.com/GPlates/gplately/releases), [project README and license](https://github.com/GPlates/gplately).
- [ASPECT 3.1.0 official release/status](https://aspect.geodynamics.org/), [ASPECT 3.0 release notes (includes FastScape coupling)](https://github.com/geodynamics/aspect/releases), [ASPECT current changes/checkpoint and FastScape fixes](https://aspect.geodynamics.org/doc/doxygen/changes_between_3_80_80_and_3_81_80.html), [ASPECT project/license](https://github.com/geodynamics/aspect).
- [Underworld3 current repository/release/license](https://github.com/underworldcode/underworld3), [quick start and geometry examples](https://underworldcode.github.io/underworld3/development/_quickstart/index.html), [Underworld3 JOSS paper](https://doi.org/10.21105/joss.07831).
- [Fastscape model](https://github.com/fastscape-lem/fastscape), [Fastscapelib C++](https://github.com/fastscape-lem/fastscapelib), [FastScapeLib Fortran documentation](https://fastscape.org/fastscapelib-fortran/), [GFZ project page](https://www.gfz.de/en/section/earth-surface-process-modelling/projects/current-projects/fastscape-landscape-evolution-model-development).
- [Badlands current repository](https://github.com/badlands-model/badlands), [Badlands documentation](https://badlands.readthedocs.io/), [eSCAPE JOSS software article](https://doi.org/10.21105/joss.00964).
- [TERRA-NG 2026 preprint](https://arxiv.org/abs/2609.21633); treated as emerging extreme-scale research, not validated R6 or consumer hardware software.

### Representative primary/review literature

- Gurnis et al. (2012), [Plate tectonic reconstructions with continuously closing plates](https://doi.org/10.1016/j.cageo.2011.04.014), *Computers & Geosciences* 38, 35–42. Topological closure method; it takes plate rotations/topological data as model inputs.
- Müller et al. (2016), [Ocean Basin Evolution and Global-Scale Plate Reorganization Events Since Pangea Breakup](https://doi.org/10.1146/annurev-earth-060115-012211), *Annual Review of Earth and Planetary Sciences* 44, 107–138. Earth reconstruction and observed/reconstructed motion-rate changes; prior, not R6 history.
- Müller et al. (2018), [GPlates: Building a Virtual Earth Through Deep Time](https://doi.org/10.1029/2018GC007584), *Geochemistry, Geophysics, Geosystems*. GPlates, topological features and reconstruction uses.
- Yoshida (2014), [Effects of lithospheric yield stresses and mantle-heating modes on Pangea breakup](https://doi.org/10.1002/2014GL060023), *Geophysical Research Letters*. Demonstrates breakup sensitivity to physical assumptions; supports against arbitrary breakup placement.
- Brune et al. (2023), [Geodynamics of continental rift initiation and evolution](https://doi.org/10.1038/s43017-023-00391-3), *Nature Reviews Earth & Environment*. Rifting is transient and influenced by inherited weaknesses and force/thermal interactions.
- Braun & Willett (2013), [A very efficient O(n), implicit and parallel method to solve the stream power equation](https://doi.org/10.1016/j.geomorph.2012.10.008), *Geomorphology* 180–181, 170–179. Landscape algorithm, not tectonic driver.
- Salles (2018), [eSCAPE: parallel global-scale landscape evolution model](https://doi.org/10.21105/joss.00964), *JOSS* 3(30), 964; and Salles et al. (2019), [eSCAPE regional-to-global landscape evolution model](https://doi.org/10.5194/gmd-12-4165-2019), *Geoscientific Model Development* 12, 4165–4184. Surface model forced by external tectonic/climate/sea-level histories.
- Kronbichler et al. (2012), [Fast adaptive finite element Stokes solvers for geodynamic flows](https://doi.org/10.1137/100800037), *SIAM Journal on Scientific Computing*; and the [ASPECT spherical-shell benchmark comparison](https://doi.org/10.1093/gji/ggy528). Full geodynamics has substantial mesh/solver convergence requirements.
- Moresi et al. (2025), [Underworld3: Mathematically Self-Describing Modelling in Python](https://doi.org/10.21105/joss.07831), *JOSS* 10(112), 7831. Framework/software paper, not validation of a specific R6 model.
- Salles, Ding & Brocard (2018), [pyBadlands framework](https://doi.org/10.1371/journal.pone.0195557), *PLOS ONE* 13(4), e0195557. Landscape, sediment transport and basin stratigraphy under prescribed drivers.

## Governance and stop conditions

This research did not modify canonical t0, the 1° grid, A1, current-state ledger, protected execution indexes, or biological/genetic engine integrations. It did not run GPlates, pyGPlates, FastScape, Badlands, ASPECT, Underworld, climate, hydrology, Deep, ecology, provider acquisition, or a physical simulation. No files were staged; no commit or push occurred.

## Next action

`R6_PHYSICAL_EVOLUTION_ARCHITECTURE_AND_LAW_CONTRACT`

The next contract should freeze the ARCANA-owned state/event interfaces, pyGPlates geometry-adapter boundary, global-versus-regional solver roles, validation/checkpoint/uncertainty requirements, and fail-closed law prerequisites. It must not claim executable physical laws or authorize the first interval until each missing law and forcing is separately bound.
