# R6 B6B First-Step Accommodation and State Transfer

Decision: **PASS_B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER**

## A. Baseline and authority

Qualified source commit `66ff83a8cf8b86b483c60a75b12d1da9594d1740`. This is a read-only adjudication. T0 is 210 Ma; B5 supplies 64,800 plate faces, 64,442 node supports (62,469 interior, 1,953 boundary-shared, 20 junction-shared), 1,983 boundaries and 20 degree-three junctions.

## B. Rigid interiors

A strictly single-plate interior point/face admits a rigid-transfer rule, applying one transform by plate ID and preserving face identity/connectivity. No mechanics solver or interpolation is needed for that limited geometric operation. It remains conditional: B5 says Cartesian axis handedness is not separately declared, so the mapping from Euler-vector axes to coordinate rotation action must be made explicit before applying it. No ARCANA coordinates were transformed.

## C. Shared boundaries and junctions

The B5 node support is set-valued and assigns no owner. B5 and the finite-step census report nonzero relative motion on all 1,983 boundaries; current fail-closed policy blocks all of them. A single shared coordinate cannot follow distinct plate transforms without a governed interface/deformation response. Do not average, snap, select a side, or duplicate nodes as an implicit fault.

All 20 degree-three junctions are blocked, have no canonical velocity, and lack boundary types or a residual allocation rule. A common junction coordinate requires a compatible multi-boundary model. Incidence alone does not define it.

Geological type and polarity remain UNKNOWN; relative motion is only a kinematic diagnostic. Those unknowns can remain only if an explicitly selected response law proves type-agnostic. No such law is currently selected, so type-dependent model selection is blocked.

## D. Topology hold

An explicit topology-invariance/event model is required. It must state which plate IDs, faces, edges, junctions and identities stay fixed over the authorized interval, and guard split, merge, creation/termination, boundary birth/death, adjacency change and junction reassignment. B6A's 27,123.405-year census bound concerns conditional rift activation only; it is not a topology bound or dt.

## E. Mesh and fields

The T0 FEG manifest identifies 64,442 nodes and 128,880 triangles (fault_count=0); B5's 64,800 entries are plate-cell faces, not triangles. Connectivity/support are valid T0 references, but there is no next-state topology hold, shared-node geometry, field transport, remap or remesh lineage contract. Nearest-neighbor, barycentric, conservative remap, snapping and arbitrary grid interpolation are not authorized.

The FEG/runtime package is derived runtime support and is excluded from B3's canonical WORLD_HISTORY minimal-state ingest. The B3 inventory has 14 state domains. Existing retention declares initial supported fields as SYSTEM_MEMORY, T0 partition and kinematics STATIC system memory, unknown masks as support evidence, and FEG/runtime product as derived/discarded. B0-G requires any future-dependent SYSTEM_MEMORY to survive; producer adapter policy remains review-required and field-specific transfer is incomplete.

## F. Numerical validity

No governed angular rotation, node displacement, edge-fraction, inversion/Jacobian, remesh, or topology validity threshold exists. Solver stability and event-localization tolerance are solver-dependent. The rift horizon is only an event boundary to respect if that model is used; it supplies none of these numerical limits.

## G. ShellSet and B7

A physical boundary/junction response is required before a physically valid next state, but the evidence does not establish that ShellSet or any numerical solver is necessary. The model family and required outputs are not yet selectable. B7 is therefore not ready to qualify; if a native solver is later selected for expensive qualification, use Ubuntu after defining its narrow I/O/acceptance contract.

## H. Candidate state contract and blockers

The machine-readable candidate-state contract lists required source IDs, support, selected forcing/law, per-field memory transfer, uncertainty, event/provenance, checkpoint and replay recipe. No state was produced.

- `positive-duration kinematics` — **PARTIALLY_CLOSED**: conditional constant-T0 first segment exists; not executable and has no renewal law/numerical validity
- `topology/event bound` — **BLOCKING**: rift horizon is not topology bound; no invariance interval or topology-event calendar
- `boundary/junction accommodation` — **BLOCKING**: all 1,983 segments and 20 junctions fail closed under unbound physical response
- `mesh/state transfer` — **BLOCKING**: only single-plate interior rigid transform is specified; shared support and fields lack transfer rules
- `numerical/model validity` — **BLOCKING**: no displacement, rotation, mesh-validity or solver-specific thresholds

First dt remains **NOT_READY_FOR_FIRST_DT**. Next authorization: `AUTHORIZE_TARGETED_MODEL_DECISION`. All safety gates remain closed.

Validation verdict: **PASS_B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER**. Focused B6B: 6 passed. Full `test_r6_*.py`: 350 passed, 0 setup errors. py_compile PASS; JSON/manifest/path PASS; diff check PASS.
