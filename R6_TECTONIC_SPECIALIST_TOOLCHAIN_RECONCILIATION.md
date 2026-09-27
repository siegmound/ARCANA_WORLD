# R6 Tectonic Specialist Toolchain Reconciliation

**Decision:** `R6_TECTONIC_TOOLCHAIN_COVERAGE_PARTIAL__INPUT_BINDING_GAPS_REMAIN`

**Scope:** capability research and input/interface reconciliation only. No engine was installed or run. No mechanics, physical parameters, `dt`, `t1`, deformation width, future state, or first interval was selected or authorized.

## Finding

ARCANA already owns a canonical 210 Ma T0 with 12 plates, 64,800 parent faces, 1,983 shared boundary segments, 30 adjacent plate pairs and 20 degree-three junctions. The boundary parent resolved kinematic demand on all 1,983 segments (1,091 convergent and 892 divergent); these are kinematic descriptors, not event labels. The parent decision remains `R6_BOUNDARY_ACCOMMODATION_NOT_ESTABLISHED__RESEARCH_REQUIRED`.

Mature specialists cover the missing calculation classes. pyGPlates resolves supplied rotations/topologies and evaluates velocities; ShellSet/SHELLS provides global/regional spherical thin-shell mechanical modeling; ASPECT, Underworld3 and LaMEM provide configurable continuum thermo-mechanics; GWB materializes temperature/composition from explicitly described features. The blocker is that ARCANA has not bound the mechanical T0, authorized its constitutive/process inputs, or defined how Shells' force-balanced velocities relate to ARCANA's prescribed rigid-plate kinematics. There is therefore no end-to-end toolchain ready for runtime qualification.

The minimum *candidate* composition is ARCANA T0 + pyGPlates for geometry and plate-side kinematic derivation + one selected mechanics solver, with ShellSet/SHELLS the closest global thin-shell candidate and ASPECT the leading high-fidelity regional comparator. GWB is optional: it can populate authored temperature/composition features, but it cannot establish their scientific authority. This is a candidate architecture, not a selected or executable engine contract.

## Parent, authority, and invariant checks

| Item | Verified value |
|---|---|
| Branch / HEAD at authoring start | `r6/tectonic-specialist-toolchain` / `a8d7f8543f79698fe1de3ea4046999334c93b634` |
| Required parent | `f327a317bc8650df3abcfe5a5e9924eebafbe427`, verified ancestor of HEAD |
| Boundary parent decision | `R6_BOUNDARY_ACCOMMODATION_NOT_ESTABLISHED__RESEARCH_REQUIRED` |
| T0 | `r6state_1d36fb90cd23443407ce6c63611a65b74c5a9157bd89b1c6cec449d9b927f2d9` at 210 Ma |
| Parent physical payload SHA-256 | `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c` |
| Vector partition SHA-256 | `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab` |
| Kinematics SHA-256 | `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4` |
| Historical bootstrap identity | `27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf` |

The existing engine decision order is already explicit in `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md` and the R6 architecture documents: canonical evidence first, then an already validated specialist, then an audited new specialist, then minimum custom implementation. The architecture freeze already assigns ARCANA authority/orchestration/provenance and limits an external engine to a bounded, separately validated computation. No new policy or architecture layer was added. The requested `R6_EXISTING_CAPABILITY_RECONCILIATION_AND_CORE_INTERFACE_SPEC.md` exists at `docs/strategy/R6_EXISTING_CAPABILITY_RECONCILIATION_AND_CORE_INTERFACE_SPEC.md` and agrees with this order.

## Anchor result: kinematic state does not need a spatial sample cell

**Q1 — Yes, for plate-side kinematics.** Given the canonical rotation model, pyGPlates can calculate the rigid velocity of each adjacent plate at the same point on a canonical boundary section. Thus `0 / 60` failed pure-plate spatial anchors do not block obtaining the instantaneous kinematic side state: `SPATIAL_ANCHOR_REQUIREMENT_NOT_NEEDED_FOR_KINEMATIC_BOUNDARY_STATE`.

The adapter maps `BOUNDARY_POINT + LEFT_PLATE_ID + RIGHT_PLATE_ID + CANONICAL_ROTATION_MODEL` to both side velocities, then projects them into ARCANA's oriented normal/tangent basis. It must preserve the exact boundary and plate identities and validate side ordering, units, interval convention and vector frame. This does not establish material support away from a boundary, strain-zone width, mechanical boundary conditions or physical accommodation. The pyGPlates calculation remains derived kinematic evidence under ARCANA's rotation authority.

## Tool comparison

| Tool | Scientific role and formulation | Geometry and domain | State and outputs | Runtime / role / blocker |
|---|---|---|---|---|
| GPlates / pyGPlates 2.5 / 1.0.0 | Rotation and topology reconstruction; spherical kinematics and deformation diagnostics, not force-balance mechanics | Global/regional spherical features and supplied topological plates/networks | Takes authored rotations, plate IDs, feature geometries/lifetimes; returns reconstructed geometries, velocities, boundary statistics and kinematic strain | GPL-2.0; Windows/Linux/macOS packages. Existing R6 evidence is diagnostic/bounded; adapter is needed and canonical dynamic mechanics are not validated. |
| ShellSet / SHELLS v1.1.0 | Quasi-static creeping-flow thin-shell finite elements, lithosphere force balance, velocity, strain, fault slip | Explicit 2-D spherical global/regional FE grid | Needs solver grid and mechanical lithosphere state; outputs surface velocity, strain/rate, slip/heave/throw, stress azimuth and spreading predictions | Linux/WSL2; Intel Fortran, MKL, MPI; hybrid model-run MPI + within-solve threaded MKL. GPL-3.0 per source/article. Strong global candidate, but no direct ARCANA topology/rotation ingestion or accepted kinematics-to-mechanics coupling. |
| ASPECT 3.1.0 | Parallel thermo-mechanical FEM; configurable rheology, free surface and coupled fields | Regional and global 3-D spherical shell | Initial conditions/material model/BC; outputs velocity, pressure, temperature/composition and derived mechanics | GPL-2.0-or-later; MPI and deal.II/Trilinos/p4est. High-fidelity regional candidate; global cost and R6 input binding unqualified. It documents a GPlates prescribed-velocity model. |
| GWB 1.1.0 | Initial-condition feature geometry; query pointwise temperature/composition | Cartesian and spherical domains | Needs explicit feature descriptions, profiles and composition labels; produces temperature/composition values/fields | C++14/CMake with C/Fortran wrappers; LGPL-2.1. Initial-condition provider only; no mechanics or authority to classify ARCANA features. |
| Underworld3 3.1.0 docs | Python/SymPy finite elements, particle-in-cell, PETSc and configurable viscoelastic/plastic/anisotropic constitutive models | Curved coordinate systems and regional examples; global R6 production not demonstrated | User supplies equations, material state and BC; solver returns configured PDE fields | LGPL-3.0 source; Python/PETSc/MPI. Flexible regional validator, but no unique R6 coverage beyond ASPECT and high model-verification burden. |
| LaMEM 3.0.0 family | 3-D thermo-mechanical marker-in-cell, staggered finite differences, PETSc; visco-elasto-plastic | Regional 3-D is a strong fit; global spherical R6 production not established | Requires geometry/material phases, temperature/density/gravity as selected, rheology and BC; outputs mechanics and evolution | MIT; PETSc/MPI, Linux/WSL and Windows bash documented. Regional validator candidate; no unique needed capability beyond other 3-D solvers evidenced. |

Versions are the latest releases/docs recovered from the official project sources on 2026-09-27; no claim is made that an untagged development branch is a stable release. ShellSet paper describes SHELLS as last updated/released in 2019; maintenance and compatible current build need qualification.

### ShellSet inputs: mandatory state vs Earth observations

**Solver/model state described by the ShellSet paper:** an FE grid representing the spherical surface and its node/element/fault topology; node-wise surface elevation; crust and mantle-lithosphere thickness; density structure; temperature/geotherm parameters; continuum friction and crust/mantle dislocation-creep parameters; plus fault friction where fault elements are modeled. Some structure can be prepared by OrbData from published datasets and stated local-isostasy/geotherm assumptions. OrbData is optional when a suitable populated grid already exists; that does not make the required state optional.

**Earth-specific calibration/scoring datasets, not simply execution inputs:** geodetic benchmark velocities, stress directions, SKS fast-polarization, seafloor-spreading rates, observed fault-slip rates and seismicity catalogs are used by OrbScore to score model predictions. They are useful validation evidence, not mandatory merely to execute Shells. Earth5-049 and the associated Earth grids/data are example inputs, not universal solver requirements.

The exact minimum parser-level configuration for every SHELLS option has not been qualified against a pinned source/manual build. The fields above are the model state the published workflow says must be defined; no synthetic defaults are supplied here. ShellSet's model predicts force-balanced velocities. Sources inspected do not establish that arbitrary pyGPlates/ARCANA boundary velocities are a native Shells solve input. Whether to use them as a boundary constraint, compare them with Shells predictions, or treat them as different model states remains a key interface and authority decision.

## Capability coverage matrix (summary)

The JSON artifact provides all required columns for each row: capability, ARCANA status, candidate and role, required/available/missing inputs, provider, adapter, custom-physics requirement, authority class, coverage status and notes.

| Capability group | ARCANA now | Candidate / status |
|---|---|---|
| Plate geometry, topology, rotations, velocities, boundary-side velocities | Canonical T0 has geometry/topology/rotation authority; demand resolved; 0/60 spatial sample anchors | pyGPlates can provide reconstruction and side kinematics; adapter and side-frame proof remain. No mechanics authority. |
| Boundary normal/tangent and demand | Kinematic demand on all segments; local frame available in diagnostics; demand is not event classification | Coordinate/unit/orientation normalization needed; no custom physics. |
| Boundary class, fault state, weak zones | Not authorized; no ridge/transform/subduction/collision/rift/fault assignment | Input-authority gap. Convergence/divergence cannot classify these. GWB can materialize a declared class, not select it. |
| Crust/lithosphere, temperature, composition, density | No solver-ready mechanical field bound | GWB/OrbData or approved data may provide/materialize fields after model authority. Synthetic structures/profiles remain authorial inputs if no provider is adopted. |
| Rheology, equilibrium, stress, strain/rate, slip | No canonical mechanical law or solved outputs | ShellSet, ASPECT, Underworld3, LaMEM provide native solver capabilities, conditional on authorized inputs. ARCANA must not implement replacement mechanics. |
| Triple-junction kinematics/mechanics | 20 identity records; no junction velocity or mechanical closure authority | pyGPlates can compute incident rigid velocities; a coupled solver can solve a connected domain, but three-arm closure needs qualification. |
| Topology trigger and surface response | No event trigger or mechanical free-surface response law bound | Requires separate event/BC and coupling contracts. Not closed by kinematic demand or solver availability. |
| Checkpoint, normalization and HistoryStore | T0 history binding exists; no mechanical restart bundle or output schema | ARCANA architecture owns wrappers, provenance, normalization and checkpoint orchestration; solver-specific mappings are not implemented. |

## Pipeline comparison

| Pipeline | Coverage | Mandatory missing inputs / adapter | Runtime profile | Verdict |
|---|---|---|---|---|
| A: ARCANA → pyGPlates → ShellSet/SHELLS → ARCANA | Kinematics plus global/regional thin-shell mechanics | FE grid/fault topology, lithosphere/thermal/density/rheology state; identity/frame adapter; unresolved whether canonical plate velocities constrain or only compare against SHELLS | Spherical 2-D FE; Linux/WSL2; MKL threads and MPI across model runs | Closest global candidate, not yet an adapter-only path; input and interface gaps remain. |
| B: ARCANA → pyGPlates → GWB → ASPECT → ARCANA | Kinematics, authored T/composition, 3-D thermo-mechanics | Mesh, materials/rheology, BC/load authority, GWB feature definitions; mesh/field/velocity/output adapters | MPI FEM; global shell possible, regional use more tractable | Viable high-fidelity path; larger state/compute burden. |
| C: ARCANA → pyGPlates → Underworld3 → ARCANA | Kinematics and configurable regional continuum physics | Mesh/equations/constitutive state/BC plus Python/PETSc adapter | PETSc/MPI; global feasibility unproven | No unique closure over ASPECT; flexible regional alternative. |
| D: ARCANA → pyGPlates → LaMEM → ARCANA | Kinematics and regional 3-D lithosphere mechanics | 3-D grid/material/rheology/thermal/BC mapping | PETSc/MPI; WSL/Linux available | Strong regional alternative; global spherical suitability unestablished. |
| M: global ShellSet + targeted 3-D validation | Potentially tractable global shell plus selected high-fidelity regions | All A inputs plus compatible extraction, regional BC, same source state, uncertainty and output comparison contracts | Cheap global candidate plus selective higher-cost runs | Architecturally plausible; cross-solver compatibility is unproven. |

Across the candidates, custom ARCANA scientific mechanics is not justified. The ARCANA work is the bridge: canonical identity and geometry mapping, coordinate/unit/support conversion, engine manifests and wrappers, output normalization, uncertainty/provenance, cross-engine comparison, checkpoint/restart and HistoryStore binding.

## Required questions

1. **Can pyGPlates remove spatial pure-plate anchors?** Yes, for boundary-side kinematic state only. It evaluates both adjacent rigid velocities at the same point. It does not resolve physical accommodation or sampling away from the boundary.
2. **Can ShellSet consume ARCANA topology/kinematics through adapters alone?** No evidence. It expects its own spherical FE grid and mechanical lithosphere state, and predicts force-balanced velocities. Both the state and kinematics-to-mechanics interpretation are unresolved.
3. **Which ShellSet inputs are mandatory vs Earth calibration?** Mechanical FE model state is required (grid, elevation/structure, density/thermal parameters, rheology and fault state when faults are modeled). Earth geodesy/stress/SKS/spreading/fault-slip/seismicity are scoring datasets, not baseline solver inputs. Exact parser-minimal configurations need later source qualification.
4. **Can GWB supply missing initial state?** It can generate/query temperature and composition from explicit feature geometry/profiles in spherical or Cartesian domains. It cannot authorize feature classification or select values.
5. **Can ASPECT take GPlates velocity and GWB state?** In principle, yes: ASPECT documents GPlates boundary-velocity input and supports initial temperature/composition. Adapters and compatible geometry are required; this is not yet a qualified or lightweight global R6 path.
6. **Does Underworld3 close a unique gap?** No unique gap shown. It offers flexible Python/PETSc FEM and constitutive models for regional work, with additional authoring/verification responsibility.
7. **Does LaMEM close a unique gap?** No unique gap shown. It is a capable regional 3-D visco-elasto-plastic solver; global spherical use was not established.
8. **Can the custom patch operator be retired?** Yes, conditionally: a selected specialist's native discretization may handle connected continuum/fault mechanics. Retain the old `OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE` result as diagnostic evidence. A domain/mesh adapter may still be required.
9. **What must be added before mechanics?** There is no universal field list independent of formulation. At minimum: solver geometry/mesh, governing equations, constitutive relation and parameters, material state, and boundary conditions/loads with support/units/time. Thermo-mechanical variants additionally need temperature and relevant composition/density/layering. Fault accommodation needs authorized fault/process class, geometry and law.
10. **Can providers produce required fields?** pyGPlates derives kinematics; GWB materializes authored T/composition; OrbData derives Shells structure from data and assumptions; mechanics solvers calculate stress/strain/slip after setup. None supplies input authority automatically.
11. **What requires authorial initialization if no observation source is chosen?** Synthetic crust/lithosphere structure, thermal profiles, material/composition and density relations, rheology and parameter ranges, boundary/fault/process classification, weak zones, accepted load/BC interpretation, and event-transition rules.
12. **Minimum viable toolchain?** Candidate ARCANA + pyGPlates + one mechanical solver. ShellSet/SHELLS is the closest global thin-shell candidate; ASPECT is the leading regional high-fidelity comparison; GWB is optional for explicitly authored initialization. Do not select or execute until state authority and ShellSet/kinematics interface are bound.

## Junctions, topology, patch operator, and width

Kinematic triple-junction analysis can evaluate each incident plate velocity at the shared junction point and check vector consistency. It is not a mechanical junction law. A connected continuum or thin-shell solve may impose simultaneous closure through its shared mesh, but this must be demonstrated with a bounded qualification test using authorized material and boundary inputs. No candidate decides whether an ARCANA junction should create a rift, subduction zone, collision, or other event.

The custom patch operator need not be repaired for production if the selected solver natively discretizes the relevant connected material domain and faults. Its existing failure remains useful historical evidence. Do not use `W_model`: element size is a numerical resolution choice, while a fault thickness or weak-zone width would be a distinct physical input only if the selected formulation requires one.

## Remaining gaps and next stage

| Gap type | Current item |
|---|---|
| `INPUT_AUTHORITY_GAP` | Rheology, thermal/lithosphere state, density/composition, fault/weak-zone state, process classes and physical BC/load interpretation |
| `INPUT_PROVIDER_GAP` / `INITIAL_STATE_GAP` | Solver-ready mechanical T0 fields; GWB/OrbData are possible providers only after inputs/assumptions are authorized |
| `INTEROPERABILITY_GAP` | ARCANA topology to ShellSet FE grid/fault network; relation between canonical rotations and Shells force balance; output/restart mapping |
| `COORDINATE_TRANSFORM_GAP` / `UNIT_SEMANTICS_GAP` | pyGPlates global vectors to local normal/tangent and solver conventions |
| `RESOLUTION_SUPPORT_GAP` | Coarse canonical vector support to solver mesh and regional refinement |
| `BOUNDARY_CLASSIFICATION_GAP` | No process/fault labels established from kinematic demand |
| `RUNTIME_QUALIFICATION_GAP` / `VALIDATION_GAP` | No selected solver installed/run; no cross-engine or three-arm closure evidence |

Next is targeted input-authority and ShellSet-versus-ASPECT interface binding. Runtime qualification follows only after the mechanical input contract is accepted. This report does not authorize first-interval design, `dt`, `t1`, forward evolution or canonical mechanics.

## Sources

- [pyGPlates primer](https://www.gplates.org/docs/pygplates/pygplates_primer), [velocity API](https://www.gplates.org/docs/pygplates/generated/pygplates.calculate_velocities), [GPlates releases](https://github.com/GPlates/GPlates/releases)
- [ShellSet v1.1.0 paper](https://gmd.copernicus.org/articles/17/6153/2024/gmd-17-6153-2024.html), [archived source](https://doi.org/10.5281/zenodo.7986808)
- [ASPECT project and releases](https://aspect.geodynamics.org/), [ASPECT 3.1 spherical-shell cookbook](https://aspect-documentation.readthedocs.io/en/v3.1.0/user/cookbooks/cookbooks/shell_simple_3d/doc/shell_simple_3d.html), [prescribed GPlates boundary velocity model](https://aspect-documentation.readthedocs.io/en/v3.1.0/parameters/Boundary_20velocity_20model.html)
- [GWB official repository and documentation links](https://github.com/GeodynamicWorldBuilder/WorldBuilder), [GWB 1.1.0 archive](https://doi.org/10.5281/zenodo.19222670)
- [Underworld3 3.1.0 documentation](https://underworld3.readthedocs.io/en/v3.1.0/), [official source repository](https://github.com/underworldcode/underworld3)
- [LaMEM official repository](https://github.com/UniMainzGeo/LaMEM), [installation/runtime documentation](https://unimainzgeo.github.io/LaMEM/dev/man/Quickstart/)

## Validation record

- Required branch, HEAD and parent ancestry verified before authoring; parent decision and T0 identities copied from checked-in reports.
- Bootstrap identity is unchanged and is present in the parent report.
- JSON parsing passed with `python -m json.tool`; `git diff --no-index --check` on each new artifact emitted no whitespace diagnostics.
- Tests and compilation are intentionally not run because this stage adds only report/documentation artifacts.
- No pyGPlates runtime is installed in this Windows environment; Fair runtime facts are treated as supplied/checked-in prior evidence and were not reproduced here.
- Staging and commit were blocked: `git add` could not create the linked worktree's shared `index.lock` (Permission denied). Both artifacts remain untracked; no retry, commit, or push was attempted.
