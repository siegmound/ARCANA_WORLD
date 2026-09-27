# R6 ShellSet global FEG and boundary-condition contract

## Decision

**`R6_SHELLSET_FEG_BC_CONTRACT_PARTIAL__MESH_TRIANGULATION_PROVIDER_REMAINS`**

The source-level FEG, fault-node, coincident-node, `Next` connectivity, `ReadBC`, and global-sphere semantics are reconciled against ShellSet v5.0. The previous `FAULT_NODE_SEMANTICS_REMAIN` decision is resolved: ShellSet's four-node fault convention and coincident endpoint handling provide a representable numerical structure. Exact ARCANA node-copy counts still depend on a selected mechanical fault set, which is unbound. The contract remains partial because no mature deterministic spherical triangulation provider/resolution policy has been selected or validated, and global solver uniqueness/frame handling still needs qualification.

No FEG/BC adapter or engine was implemented/run. No canonical payload, physical primitive, material, rheology, fault class, or first interval was selected.

## Source basis

The official public ShellSet source inspected is pinned to initial commit `8ab721312977cec1091d17c0e7854b2ee9adc554`: [MOD_Data.f90](https://github.com/JonBMay/ShellSet/blob/8ab721312977cec1091d17c0e7854b2ee9adc554/src/MOD_Data.f90), [MOD_Shells.f90](https://github.com/JonBMay/ShellSet/blob/8ab721312977cec1091d17c0e7854b2ee9adc554/src/MOD_Shells.f90), and [SHELLS_v5.0.f90](https://github.com/JonBMay/ShellSet/blob/8ab721312977cec1091d17c0e7854b2ee9adc554/src/SHELLS_v5.0.f90). The observed `main` head was `e4a6fbd5997b6c4978924649dff1abab0c96ca57`. The README labels `Earth5R-type4A.bcs` as having no plate-interior VBCs and lists `Earth5R-type4AplusA.bcs` separately.

The audit read `GetNet`, `PutNet`, `Next`, `Square`, `ReadBC`, `VBCs`, `EdgeVs`, `Euler`, and the global-sphere caller. No immutable local source archive or per-file checksums were added. No ShellSet/OrbData runtime was run.

## Exact FEG structure

`GetNet`/`PutNet` establish this sequence:

1. Title record (`A80`).
2. `numNod, nRealN, nFakeN, n1000, brief`.
3. One node record per node: ID, east longitude, north latitude, elevation, heat flow, crustal thickness, mantle-lithosphere thickness, chemical density anomaly, cooling curvature.
4. `numEl`, followed by triangular continuum records: element ID, three node IDs counterclockwise, optional `LR <integer>`.
5. `nFl`, followed by fault records: fault ID, `n1 n2 n3 n4`, two dips, nonnegative past offset, optional `LR <integer>`.

`GetNet` reads only the first five nodal values (ID, longitude, latitude, elevation, heat flow), because its OrbData input pass recomputes/populates the remaining state. `PutNet` writes all nine. Longitude/latitude are file degrees and become radians internally. Source variable names and calculations establish SI dimensional interpretation: elevation and thickness in m, heat flow in W m⁻², chemical density anomaly in kg m⁻³, and cooling curvature in K m⁻² in the quadratic geotherm. The writer has no complete adjacent units legend, so any future writer must include an explicit unit note.

`nFakeN`/`n1000` are legacy numbering fields. `GetNet` calls fake-node numbering outdated and unsupported. It maps external IDs above `nRealN` through `n1000` to internal contiguous node IDs; `PutNet` reverses that mapping. ARCANA duplication must use ordinary valid FEG node identities.

## Faults, physical points, and junctions

Each fault has four node IDs. `n1,n2` run left-to-right on the near side; `n3` is opposite `n2`; `n4` is opposite `n1`. Physical endpoint A is `n1 ↔ n4`; endpoint B is `n2 ↔ n3`. The record also stores `dip1`, `dip2`, past offset, and optional LR tag. `Next` searches across those pairs to locate adjacent continuum elements; `Square` detects fault edges and uses them when resolving connectivity/perimeter.

A canonical physical point is not synonymous with one FEG node. Multiple ordinary node IDs may share exactly the same coordinates while carrying independent mechanical DOFs on different sides. `Square` starts from the opposite-side endpoint pair, gathers connected nearby corner nodes, and averages positions if needed. ARCANA should emit exactly coincident coordinates and treat averaging as tolerance handling, not geometry repair.

For a selected fault set, the deterministic junction rule is: remove discontinuity edges from local continuum connectivity, identify the mechanically independent continuum sectors incident to each canonical junction, and allocate one coincident FEG node per sector/side incidence with provenance. Preserve canonical junction ID, physical coordinate, side/domain, incident branches, fault elements, and continuum domains. Do not hard-code copies to degree three or invent junction mechanics.

`OrbData5` sets `maxAtP=10` as its overlap-node capacity at a fault intersection. It is component/version specific; check each compiled component's actual limit. Exact ARCANA multiplicity is unbound because no boundary is selected as a mechanical fault. At Level 1 (`nFl=0`), one continuum node identity per physical junction suffices and fault-side expansion is deferred. Thus the prior fault-node blocker is resolved at the representation level; selecting faults and implementing expansion remain future adapter work.

## Two qualification levels

**Level 1: global continuum integration proof.** A bounded qualification fixture is feasible in principle with a closed spherical continuum FEG, `nFl=0`, and no topology-derived internal VBCs, provided it retains fields needed for that limited objective. It does not qualify fault mechanics or production physics; no runtime was performed here.

**Level 2: fault-aware qualification.** A later fixture may add synthetic test-only faults or an explicitly governed mechanical subset, with coincident side nodes, locally derived junction sectors, lineage, and static `Next`/`Square` checks. Do not turn all 1,983 kinematic boundary segments into fault elements by default.

## Global sphere and BC semantics

After `Square`, SHELLS sets `sphere=.TRUE.` when `nCond==0`; `Square` returns without tracing an ordinary perimeter. The global caller invokes `Downer`, which can add constraints for specific truncated thrust/slab-footwall geometry. A closed global ARCANA FEG has no ordinary external perimeter and should have no ordinary perimeter `.bcs` records. With `nFl=0`, there are no fault footwalls.

`ReadBC` documents and implements these codes:

| Code | Meaning | Constrained DOFs |
|---:|---|---:|
| -1 | No velocity constraint; ridge-adjacent label | 0 |
| 0 | No velocity constraint; weak/free-margin label | 0 |
| 1 | Fix velocity along specified direction; perpendicular component free | 1 |
| 2 | Fix specified direction and set perpendicular component to zero | 2 |
| 3 | One component supplied by PB2002 `EdgeVs` | 1 |
| 4 | Both components supplied by PB2002 `EdgeVs` | 2 |
| 5 | Both components from named-plate `Euler` relative to `iPVRef` | 2 |

For explicit types 1/2, magnitude is m/s and azimuth is degrees clockwise from geographic North. `ReadBC` stores `vBCArg=(180°-vAz)π/180`, counterclockwise from +South. Inverse: `vAz=180°-vBCArg·180/π` modulo 360.

Types 3/4 are prohibited for canonical ARCANA input: `EdgeVs` uses PB2002 boundary lines, names, Euler data, symbols and polarity. Types 1/2 are the generic explicit sparse forms eligible for a future authorized adapter. No type is selected, and full-field pyGPlates velocity BCs are not allowed.

Type 5's Euler calculation is general over `names`, `omega`, and `iPVRef`, but the current application supplies a fixed 52-plate Earth/PB2002 registry. That binding is not ARCANA authority. ARCANA type 5 would need a parameterized registry/omega adapter or source generalization and requalification. It is unnecessary for the Level 1 no-interior-VBC path.

## Interior constraints, frame, and uniqueness

The README's type4A example is explicitly the global case without plate-interior VBCs. The plusA path adds internal type-5 constraints. `Tract` describes a preceding torque run commonly using `trHMax=0` plus internal constraints on slabless plates to infer basal tractions. This is an Earth torque/basal-traction iteration, not a general ARCANA requirement.

The `ReadBC` check for at least three constrained DOFs applies only when `NOT sphere` and `trHMax<=0`; global sphere bypasses it. The guard sets no positive global minimum. It does **not** prove that the unconstrained global mechanical system is unique or that another solver mechanism removes rigid modes. Global nullspace/uniqueness remains open for qualification.

`pltRef` resolves to `iPVRef`; `Euler` subtracts the reference plate's rotation vector when computing relative type-5 velocities. This is a computational frame for those kinematic values. Inspected code does not establish that `iPVRef` alone removes the mechanical nullspace when no BCs exist. ARCANA's area-weighted NNR is only a kinematic gauge. Any future transform must be invertible and preserve relative plate velocities, boundary-relative motion and strain rates. A numerical reference plate must never silently become a physically fixed ARCANA plate. None is selected here.

## Provider and adapter status

The FEG schema is source-defined, but no mature deterministic spherical/constrained triangulation provider or resolution policy is selected. The 64,800 canonical faces have not been shown to satisfy ShellSet's triangular counterclockwise spherical FEG requirements, so they are not reused by assumption. FEG remains `NUMERICAL_DERIVED_SUPPORT`; ARCANA geometry and identity remain authoritative.

No adapter/parser/writer, junction expansion, frame transformer, or static topology validator was implemented. Remaining implementation gates are provider/resolution selection, canonical lineage, `Square`/`Next` fixture acceptance, and global uniqueness/frame qualification. Authorial material/rheology selection remains a separate governed stage.

## Governance and validation boundary

- Canonical T0 payload: unchanged.
- Physical primitives/material/rheology: no values selected or materialized.
- ShellSet/OrbData execution: not run.
- Runtime qualification: not authorized by this report.
- First interval / `dt`: not authorized.
- Regression and report validation: update the paired JSON after checks.

See [R6_SHELLSET_FEG_BC_CONTRACT.json](R6_SHELLSET_FEG_BC_CONTRACT.json) for machine-readable details. Git staging previously failed once because the linked-worktree `index.lock` could not be created (`Permission denied`). Staging was not retried; no commit or push was made.
