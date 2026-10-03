# R6 B6G — targeted first-step validity gap closure

## Qualified revision and scope

Source baseline: `67d1bf249ce5a099ab8fa68a25bb85ac56f9528a` on `r6/b6g-targeted-validity-gap-closure`. B6G revalidated B5 support and B6E materialization from the full governed source, checked retained B6D/B6E/B6F evidence manifests, and re-derived the complete relational graph. Counts are 64,442 nodes, 128,880 triangles, 1,983 interfaces, 3,966 distinct interface sides, 20 junction relations, and 60 junction sides. The canonical mesh hash remains `6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad`.

This is a read-only adjudication of frozen D1–D8. It does not run or authorize mechanics, state evolution, topology mutation, `dt`, or T1.

## False numerical blockers removed

The MVP applies exact finite rigid rotation to plate-local geometry. An isometry preserves each plate-interior edge length, orientation, and triangle shape; therefore a generic maximum angle, absolute displacement cap, displacement/interior-edge ratio, or interior quality/remesh threshold is not required for numerical correctness of this rigid operation. No such numerical safety factor is selected. These quantities may matter to later resolution/query policy or a different deforming model.

## Interface and junction validity

All 1,983 interface identities were re-derived against B5 boundary IDs. Each has two distinct plate-local side identities with the governed adjacent plates and endpoint ordering. D2 represents relative motion as a discontinuity; geometric co-location and a gap tolerance are not required to preserve the relation. Physical gap contents/accommodation remain UNKNOWN.

The governed normal/tangential decomposition is present for all 1,983 interfaces: 892 have positive opening-normal velocity, 1,091 negative closing-normal velocity, and all 1,983 have nonzero tangential velocity. The normal convention is positive from plate A toward plate B. These instantaneous components describe the discontinuity only; they do not assign fault type, polarity, stress, slip, or a physical response.

All 20 junction relations preserve three incident plate IDs, three incident interface identities, three distinct junction-side identities, and no unique owner. D3 is set-valued and does not require one moving Euclidean point, a positional spread threshold, or residual velocity allocation. Physical accommodation remains UNKNOWN. Both relations remain valid relationally within an unchanged topology segment; this does not qualify topology transitions.

## Event coverage and positive window

The conditional rift-process activation guard is qualified at 27,123.405156307464 years for its eligible support under fixed T0 Euler forcing. It does not represent boundary birth or plate split. Rigid transformation itself cannot degenerate a plate-local side, and cross-side gap/overlap is not an invalidation of D2/D3 identity relations.

The D1 topology event set remains incomplete: plate split/merge/create/terminate, boundary birth/death, interface split/merge, junction birth/death/connectivity reassignment, and unenumerated events have no complete detector or positive interval proof. Missing event detection is not treated as event absence. Result: `PARTIAL_EVENT_COVERAGE_ONLY`; no positive topology window is qualified.

## State transfer and SYSTEM_MEMORY

All 15 B6E state families were classified. The existing B6B/B6C operation authorizes conditional rigid transfer of plate-local geometry inside an accepted event-free segment; it was not executed. Other domains retain their latest valid state under D6, while UNKNOWN boundary/junction/weak-zone semantics remain explicit query limitations. Plate forcing and partition identities remain references under topology hold. All five SYSTEM_MEMORY classes remain retained; no memory is discarded or assigned a fabricated future value. These items do not block first-dt adjudication for the kinematic/no-mechanics MVP when temporal validity is exposed.

## Exact remaining blocker and decision

The minimum blocker is D1 event coverage: no qualified detector or positive interval proof conservatively covers the topology transitions listed above. The rift horizon alone cannot bound them. Closure requires either a governed complete event vocabulary with deterministic detector/stop rules, or an authoritative positive interval proof excluding those transitions.

The only reported positive candidate bound is the conditional rift activation horizon. `CURRENT_SMALLEST_QUALIFIED_BOUND_NOT_A_DT` is 27,123.405156307464 years for that event only; it is not a global topology bound and is not a selected `dt`.

Readiness remains `NOT_READY_FOR_FIRST_DT_ADJUDICATION`. Next recommendation: `AUTHORIZE_CONTINUED_TARGETED_VALIDITY_CLOSURE`. Ubuntu work is not required for this static/derived qualification.

Safety gates remain false: `mechanics_authorized`, `forward_evolution_authorized`, `dt_selected`, `t1_created`, and `canonical_state_changed`. No ShellSet or OrbData mechanics ran; no candidate geometry was written.

Machine evidence and its hash manifest are under `outputs/r6_b6g_targeted_validity_gap_closure/`.

## Validation

On Windows, focused B6G tests passed 7 tests; the B5–B6F regression passed 72 tests; and the complete active R6 suite passed 385 tests (143.10 s). `compileall`, B6G `py_compile`, JSON checks, artifact manifest/hash checks, portable-path checks, and whitespace checks passed. No ShellSet or OrbData runtime qualification is claimed.
