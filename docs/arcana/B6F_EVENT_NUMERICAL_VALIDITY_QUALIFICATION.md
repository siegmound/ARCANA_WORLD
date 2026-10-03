# R6 B6F — event and numerical validity qualification

## A. Qualified revision and scope

Qualified source baseline: `83061d1a3ecba3455be7bada00a13c8c8a7d16e2`, branch `r6/b6f-event-numerical-validity-qualification`. This is a read-only qualification of the frozen B6D/B6E MVP: constant-T0 plate Euler kinematics, event-driven topology hold, plate-local rigid support, explicit discontinuous interfaces, and set-valued junctions. The diagnostic uses the governed T0 mesh and forcing; it does not persist or authorize a candidate future state.

The canonical adapter reproduced 64,442 nodes, 128,880 triangles, 193,320 unique edges, and mesh identity `6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad`. The governed representation retains 62,469 interior representatives, 3,966 boundary sides, 1,983 interfaces, 60 junction sides, and 20 junction relations. No node ownership or motion was assigned.

## B. Event and kinematic validity

The conditional constant-T0 Euler rule defines a model segment but supplies no governed numeric segment duration or renewal law. The only positive event horizon is the B6A conditional rift-process activation horizon of 27,123.405156307464 years for eligible support under fixed T0 rates and the 5 km activation threshold. It is not a plate split, generic topology bound, or `dt`.

The relevant unsupported transitions include plate split/merge/creation/termination, boundary/interface birth/death/split/merge, adjacency change, junction birth/death/reassignment, and plate-support split/merge. Missing detectors do not establish event absence. Therefore no positive topology-validity interval is qualified.

## C. Geometry and numerical diagnostics

`rotate_vector_constant_euler` uses an exact finite quaternion action. It has no ODE small-step stability restriction; B6F invents no angular threshold. On the complete plate-local triangle support, hypothetical elapsed-time samples from 0 through the conditional rift horizon remained finite and preserved positive oriented spherical areas to floating-point roundoff. This establishes rigid interior shape invariance for this diagnostic, not cross-plate interface compatibility or a topology interval.

The mesh has 193,320 unique edges; edge lengths range from 1,940.594 m to 157,249.381 m (median 111,194.927 m). At the conditional rift horizon, the diagnostic maximum plate angle is 0.000658124 rad, maximum point path is 4,192.906 m, and maximum path/minimum incident-edge ratio is 0.825518. These are measurements at a conditional model horizon, not allowed thresholds. The hypothetical interface side separation reaches 6,032.152 m and the maximum junction incident-position spread reaches 4,885.702 m there. These values demonstrate that independently moved plate-local copies diverge; no interface closure or junction response law defines whether/how to accommodate that divergence. No arbitrary safety factor, gap tolerance, displacement fraction, or remesh threshold was selected.

## D. H1–H? validity inventory and transfer

The machine-readable inventory covers kinematic duration, event coverage, exact rigid rotation, displacement, local edge scale, interface validity, junction compatibility, mesh geometry, state-transfer applicability, SYSTEM_MEMORY, remesh, and solver stability. Remesh and solver stability are not applicable to this no-mechanics MVP. Interior rigid geometry is preserved; boundary/junction behavior and state transfers remain unresolved.

B6E transfer declarations remain authoritative. Initial-world physical geography and several material/domain families remain `MODEL_REQUIRED` or `UNKNOWN`; plate kinematics is historical/conditional forcing, and FEG/ShellSet outputs must be recomputed. SYSTEM_MEMORY is retained. No field-specific future transfer was executed or fabricated.

## E. Result and limits

One event-specific conditional positive bound is retained, with restricted scope. No common comparable bound is available as a global candidate minimum. First-dt adjudication remains blocked by topology-event coverage, interface/junction model and acceptance semantics, field-specific state transfer, SYSTEM_MEMORY update rules, and unqualified local-scale thresholds. Readiness is `NOT_READY_FOR_FIRST_DT_ADJUDICATION`; next recommendation is `AUTHORIZE_TARGETED_VALIDITY_GAP_CLOSURE`. Ubuntu qualification is not required for this bounded diagnostic.

## F. Scientific safety

`mechanics_authorized=false`, `forward_evolution_authorized=false`, `dt_selected=false`, `t1_created=false`, and `canonical_state_changed=false`. No ShellSet or OrbData mechanics ran. No canonical node motion, topology mutation, or future state was created. Runtime authority remains limited to loading and consuming the governed ARCANA T0 runtime package.

See `outputs/r6_b6f_event_numerical_validity/` for the machine-readable result, constraint/event matrices, full-mesh diagnostic sweep, unresolved prerequisites, and SHA256 artifact manifest.

## G. Validation

On Windows, the B6F-focused suite passed 6 tests; combined B5–B6F regression passed 72 tests; the B5–B6E subset passed 66 tests; and the complete active R6 suite passed 378 tests (150.46 s). `compileall`, B6F `py_compile`, JSON parsing, artifact hash/size validation, portable-path checks, and whitespace checks passed. These are source/data qualification checks; no ShellSet or OrbData runtime qualification is claimed.
