# B6N7 — Minimum Evolvable Rift Model Requirements

## Decision

`PASS_B6N7_MINIMUM_EVOLVABLE_RIFT_MODEL_REQUIREMENTS_DEFINED` means that a researchable model interface and blocker traceability set are defined. It does not select or qualify a rift model, provide coefficients, authorize propagation, or close the B6N5 scientific blocker. The normative requirements are in `contracts/R6_MINIMUM_EVOLVABLE_RIFT_MODEL_REQUIREMENTS_V1.json`; the four-blocker mapping is `contracts/R6_MINIMUM_RIFT_MODEL_B6N4R1_BLOCKER_MATRIX_V1.json`.

## Governing facts and current authority

The current state is `RIFT_PROCESS_ACTIVE` for plate pair 1:3 at 209.97287659484368 Ma. Activation was instantaneous and preserved geometry, the 71-segment pair interface, junction incidence, set-valued support and plate identities; opening distance was zero, with no split, new plate, new crust or mechanics. B6N2 conditionally renews restricted plate-local rigid Euler kinematics. It explicitly does not classify individual interface segments as divergent or assert extension, opening, accommodation, or topology change. B6N5 therefore remains `BLOCKED_B6N5_INSUFFICIENT_STRUCTURAL_TRANSITION_AUTHORITY`, with `next_structural_transition_predicate=UNKNOWN_NOT_GOVERNED`.

## Minimum model interface and state

The interface must expose an immutable model/version and authority scope; initialize a model-defined minimum process-state vector from a named POST_EVENT checkpoint/support; advance that vector under an identified law and approved forcings; evaluate governed process, interface, topology and support predicates; report error/stability indicators, validity bounds and dimensioned uncertainty; and provide replay-complete identities.

The smallest state vector is model-dependent and cannot be physically named from current authority. Relative rigid displacement/velocity can be derived as a B6N2 kinematic diagnostic within scope, but is not extension, opening, segment type or response. Extension, accumulated opening, width, thinning and stretching ratio remain candidate quantities, not selected fields. The interface must expose support-resolved interface response semantics to close the interface blocker; it must not invent segment classes or assume uniform response. Topology/support eligibility are predicates, not automatic mutations.

## Four B6N4-R1 blockers

| Blocker | Runtime evidence needed | Predicate family | Remaining authority boundary |
| --- | --- | --- | --- |
| `NEXT_RIFT_PROCESS_EVOLUTION` | Evolved process state, law outputs/rates/error and validity | `NEXT_PROCESS_MODEL_VALIDITY_OR_REGIME_BOUNDARY` | Process law, state meaning and scope |
| `PLATE_INTERFACE_EVENT_PREDICATES` | Interface identities plus support-resolved response/regime, detector coverage and uncertainty | `INTERFACE_RESPONSE_REGIME_BOUNDARY` | Interface response semantics; kinematics alone is insufficient |
| `GENERIC_TOPOLOGY_EVENT_COVERAGE` | Topology invariants, covered event classes and conservative detector coverage | `TOPOLOGY_REEVALUATION_BOUNDARY` | Transition coverage and separate topology application authority |
| `SUPPORT_MEMBERSHIP_VALIDITY` | Support version, membership validity status and dependency/buffer closure | `SUPPORT_MEMBERSHIP_VALIDITY_BOUNDARY` | Explicit remapping authority; no silent reassignment |

The process state may feed multiple predicates, and topology/interface evidence may inform support validity. That shared dependency does not establish a common authority for all four blockers.

## Predicates, events and adaptive stepping

A predicate reports a governed condition, not an event application or transition result. The engine may bracket a supported predicate crossing, reduce `INTERNAL_DT`, refine the affected scope and emit an event candidate with an evidence-supported time interval. A predicate must never create a plate split, new boundary or support reassignment by itself. Persistent PRE/POST states are required only when an authorized causal transition is applied and significance rules require them; the event record may exist independently.

The model must expose local integration error/stability, state change rates or equivalent indicators, predicate proximity/change rate where meaningful, uncertainty growth, detector coverage, and model/authority validity bounds. B6N6 may use them to adapt stepping, but no timestep constants or thresholds are selected here.

## Scope, forcing, couplings and uncertainty

The first model scope can be the activated pair-1:3 interface plus its endpoint junctions and a proven dependency/buffer region. B6N2 rigid motion is the only currently identified kinematic-forcing candidate, but it is not executable for a current forward interval: no positive-duration interval is selected and B6N5/B6N4-R1 prerequisites remain unresolved. Thermal, lithospheric, mantle, loading or weakness forcings are conditional on the selected law and need their own authority and replay references. If dependency closure is not proven, the affected scope must expand or stop; local refinement does not imply whole-world high-resolution recomputation.

Tectonic geometry/topology monitoring is required for structural-event predicates. Topography/geography is required only after a governed structural transition changes those outputs. Volcanism is optional unless a chosen model includes it. Hydrology, climate, resources and ecology are downstream of governed environmental changes. Deep coupling remains unknown and is not presumed necessary.

Carry parameter, forcing, model-form, transition-criterion, spatial-localization, event-time, numerical and dependency uncertainty separately where supported; otherwise retain `UNKNOWN`. No single confidence score is substituted for missing authority.

## Tier decision

| Tier | Assessment |
| --- | --- |
| 0 — current rigid kinematics | Insufficient: motion diagnostics only; no process law, interface response, topology coverage or support-validity predicate. |
| 1 — pure kinematic extension | Insufficient alone: needs governed interface frame/sign and still cannot establish physical process/interface transitions or support validity. Adding those rules makes it a process model. |
| 2 — reduced-order rift-process model | **Lowest requirements tier to investigate.** It must evolve a model-defined process state and provide authorized interface outputs and conservative runtime predicates. It is not selected or scientifically qualified. |
| 3 — crustal/lithospheric extension | Needed only if thinning, crust, width or related outputs enter the required state authority. |
| 4 — full mechanical/geodynamic | Not proven necessary. Required only if the selected science requires stress/strain/force balance, fracture/localization or mechanical accommodation. |

Targeted external scientific research is required before model selection to establish physically meaningful state variables, evolution-law class, interface response semantics, transition criteria, uncertainty and whether a reduced-order/type-agnostic closure is defensible. B6N7 performs no provider selection or numerical calibration.

## B6N6 interface and replay

The conceptual interface operations are initialization, state advancement, predicate evaluation, error/stability estimation, authority-bound reporting and uncertainty reporting. They are requirements, not implemented functions. Replay must bind model/version and authority, parameters, initial state/support/checkpoint, forcing, predicate versions, numerical decisions, uncertainty configuration, stochastic seed where applicable, local scope/dependency proof, refinement decisions and expected outputs.

## Preserved gates

No rift propagation or mechanics was executed; no dt2, T2, B6O, topology transition or canonical WORLD_HISTORY mutation occurred. The contract defines requirements for a future research/model-selection stage only.
