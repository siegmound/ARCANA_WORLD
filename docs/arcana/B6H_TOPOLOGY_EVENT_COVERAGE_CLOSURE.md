# R6 B6H — topology event coverage closure

## Qualified revision and scope

B6H source baseline is recorded from the current checkout in `B6H_RESULT.json`. This is a read-only qualification of the frozen B6D first-segment model and the B5/B6E T0 relation graph. The runner re-derives the graph and verifies the retained B5, B6A, B6D, B6E, B6F, and B6G artifact manifests. It does not create future geometry or mutate canonical state.

The actual governed inventory is 64,442 nodes, 128,880 triangles, 12 plate supports, 1,983 interface identities, 3,966 distinct plate-local interface sides, 3,966 boundary-endpoint references over 1,973 unique endpoint nodes, 30 adjacent plate pairs, and 20 set-valued junction relations with 60 junction sides. The 20 junctions retain their explicit incident plate/interface sets in the inventory evidence. The T0 mesh SHA256 remains `6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad`.

## Minimal event classes and predicates

The minimal relevant classes are: (1) conditional rift-process activation; (2) boundary identity-set birth/death; (3) interface relation decomposition split/merge; (4) junction identity/incidence change; (5) plate-support component/plate identity change; and (6) other unenumerated topology transitions. Boundary birth is not inferred from rift activation. Split/merge directions are grouped under the same relation-set change. A frozen-MVP relation-degeneracy class is not independently relevant: exact plate-local rigid transforms preserve local geometry, while D2/D3 do not require cross-side co-location; any identity/incidence change is already represented by the listed relation-change classes.

For non-rift classes, a difference in boundary/interface/junction/plate identity or incidence is a testable *retrospective* state predicate. Current authority provides no pre-event trigger, continuous-time law, transition map, or conservative timing bound. Synthetic graph-delta tests verify deterministic detection after a fixture changes; they are not evidence that a corresponding event occurs in ARCANA or a predictor for its time. No geometric root search is supportable without the missing event semantics.

## Qualified rift horizon and topology coverage

The B6A/B6D conditional rift activation horizon is integrated exactly once: 27,123.405156307464 years, limiting candidate pair `1:3`, under the qualified fixed-T0 Euler assumptions. Its event predicate is `RIFT_INITIATION` when governed extension reaches its activation threshold under positive opening. This is a process-activation event, not a boundary birth, plate split, or generic topology bound. Its strictness is to stop before or capture the event; it is not `dt`.

The remaining plate-support, boundary, interface, junction, and unenumerated transitions have neither qualified first-event detectors nor positive interval exclusion proofs. Absence of a detector is not absence of an event. Therefore coverage remains `PARTIAL_EVENT_COVERAGE_ONLY`; no composite positive topology window is computed. Readiness is `TOPOLOGY_MODEL_EXTENSION_REQUIRED` and first-dt adjudication remains blocked.

## Decision, limits, and scientific safety

The exact residual authority needed is a governed first-segment event vocabulary with eligibility predicates, event-specific transition/identity semantics, and conservative first-event timing/stop rules (or a qualified positive interval proof that excludes the unsupported classes). This is a targeted topology model extension, not another broad numerical audit. No Ubuntu workload is justified: current governed data are small, and the missing information is model authority rather than compute capacity.

No production source changed. Mechanics, forward evolution, `dt`, T1, canonical node movement/topology mutation, ShellSet, and OrbData mechanics remain unauthorized/not executed. Runtime authorization remains limited to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`. Test evidence and artifact hashes are in `outputs/r6_b6h_topology_event_coverage_closure/`.

## Validation

The focused B6H module passed 7 tests; the B5–B6G regression passed 52 tests; the complete active R6 suite passed 392 tests in 190.22 seconds. The 7-test increase over the 385-test baseline is the B6H module. Python compilation, JSON parsing, manifest/hash verification, portable-path checks, and `git diff --check` are recorded in the retained validation evidence.
