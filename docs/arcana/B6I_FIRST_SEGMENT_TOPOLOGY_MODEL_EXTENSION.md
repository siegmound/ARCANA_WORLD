# R6 B6I — minimal first-segment topology model extension

## Qualified revision and authorial scope

Qualified source is the current B6I checkout recorded in `B6I_RESULT.json`. B6I freezes `FIRST_SEGMENT_TOPOLOGY_PROCESS_SCOPE`: initial topology is the governed T0 graph; `RIFT_PROCESS_ACTIVATION` is the only enabled topology-changing process; other independent non-rift topology changes are explicitly out of scope for this MVP segment. The rift activation may lead to a topology transition, but B6I does not implement that transition. The segment terminates at the enabled event for later explicit transition handling.

Out of scope means only that this first-segment model does not generate those processes. It does not mean physically impossible, absent in general, or removed from future ARCANA. Registry entries distinguish rift activation (`ENABLED`), the conditional rift-linked transition (`DERIVED_FROM_ENABLED_EVENT`), and independent boundary/interface/junction/plate-support changes (`OUT_OF_SCOPE_FOR_FIRST_SEGMENT_MODEL`). An unregistered event class raises a fail-closed error.

## Topology hold and qualified model-relative bound

The frozen rule is `FIRST_SEGMENT_TOPOLOGY_HOLD_UNTIL_ENABLED_EVENT`: preserve T0 semantic topology between T0 and the first enabled event while governed plate-local Euler kinematics apply. The inherited qualified rift guard gives a first-segment positive topology validity bound of **27,123.405156307464 years**, limited by candidate pair **1:3**. Its predicate, conditional applicability, authority, threshold, opening rate, and stop-before/capture semantics are retained from B6A/B6H and the horizon is counted once.

This bound is complete only for the frozen MVP first-segment process scope. It is not a claim that other processes are physically absent, and it is not a selected `dt`. The valid hold interval is open at the horizon. No topology mutation, rift transition, candidate T1, or forward evolution is run; transition handling requires an explicit successor stage.

## Query scope and future extension

Queries distinguish an evaluated enabled event that did not occur (`EVENT_DID_NOT_OCCUR`) from an event class outside this model (`MODEL_SCOPE_LIMITATION`). An enabled but unevaluated event remains `UNKNOWN`; an unregistered class fails closed. These statuses prevent model scope from being reported as historical fact.

Promotion of an out-of-scope process requires an explicit model addition, event predicate, authority/provenance, detector/horizon qualification where required, regression against existing history semantics, and query/replay compatibility. No future event model is implemented here.

## First-dt prerequisites and safety

B6A/B6B positive-duration kinematics and B6G rigid-interior, interface, junction, state-transfer, and SYSTEM_MEMORY closures are reused. With the B6I first-segment topology bound, readiness is `READY_FOR_FIRST_DT_ADJUDICATION`. This authorizes only a later dt *adjudication*, not timestep selection or evolution.

No ShellSet or OrbData mechanics ran. Mechanics authorization, forward evolution authorization, `dt_selected`, `t1_created`, canonical state change, node motion, topology mutation, and rift transition execution remain false. Runtime authorization remains limited to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`.

## Validation

The focused B6I suite passed 9 tests; the B5–B6H regression passed 59; the complete active R6 suite passed 401 tests in 157.09 seconds. The 9-test increase over the 392-test baseline is the B6I module. `py_compile`, `compileall`, JSON validation, artifact manifest/hash checks, portable-path checks, and `git diff --check` are recorded in the retained B6I evidence package.
