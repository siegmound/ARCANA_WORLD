# B6J first-dt adjudication

## Qualified baseline and decision

- Branch: `r6/b6j-first-dt-adjudication`
- Qualified source commit: `4fd62dd272b9f671b7dc8ffffde7592c78a38a38`
- B6I historical source remains `a3d351b0abf8231308a8394feadf9480794dc0ea`.
- Result: `PASS_B6J_FIRST_DT_ADJUDICATION`.
- First interval: `27123.405156307464 year` (`0x1.a7cd9ee14b895p+14`), selected as the minimum applicable qualified bound.

## Constraint and bound adjudication

There is exactly one finite active qualified temporal bound: conditional `RIFT_PROCESS_ACTIVATION` at pair `1:3`, `27123.405156307464 years`. Positive-duration kinematics is an active nonnumeric model condition. B6G closes generic rotation/displacement thresholds, interface and junction geometric co-location, transfer and SYSTEM_MEMORY blockers. Mechanics stability is not applicable to the mechanics-free MVP. Non-rift topology mutations are out of scope under B6I.

The event law uses `E >= theta`; the topology validity interval is open at the horizon. B6I explicitly permits stopping before or capturing the event, while forbidding a segment from crossing it. B6J therefore authorizes exact pre-transition event-boundary capture. It adds no epsilon, tolerance, rounding, or safety factor. The solver-specific localization tolerance still required before future event application is unselected and is not claimed as solved here.

## Causal endpoint, history and replay

The interval ends at the earliest enabled causal event boundary under the adaptive constraint-driven and event-driven topology-hold policies. The reason is sparse causal history: preserve the long valid segment and represent the event boundary explicitly, rather than adding an arbitrary calendar checkpoint. WORLD_HISTORY `EventRecord` supports temporal/spatial support, trigger/cause, before/after state and causal dependencies; `ReplayRecipe` can reference event IDs. This package defines only the boundary contract and does not create an `EventRecord` or execute its transition.

Target age is `209.97287659484368 Ma` from source age `210.0` Ma using positive elapsed years and decreasing geological age. It is planning metadata only; no state at that age is materialized.

## Event and authorization boundary

- Event boundary contract: `EVENT_BOUNDARY_CONTRACT_DEFINED_NOT_EVENT_CREATED`.
- Transition status: `NOT_EXECUTED`.
- Maximum next authorization: `AUTHORIZE_FIRST_CANDIDATE_STATE_CONSTRUCTION`.
- `dt_selected=true`; mechanics, forward evolution, T1, canonical state mutation, node motion, topology mutation, ShellSet and OrbData mechanics remain false/not executed.
- Runtime authorization remains limited to loading and consuming the governed ARCANA T0 runtime package.

## Determinism and validation

Bound normalization converts supported temporal units to years, then sorts by `(value_years, bound_id)`. Numeric representation and hexadecimal binary64 value are retained. Replay selection excludes wall-clock, filesystem ordering, random inputs and unstored tolerances. This is selection determinism, not physical simulation replay.

Recorded tests: `{"focused_b6j_passed": 12, "full_r6_passed": 413, "related_b5_b6i_passed": 61, "status": "PASS"}`.

The retained artifact manifest covers this report, evidence JSON, runner and focused tests; the manifest omits its own hash. No production scientific/runtime source was changed.
