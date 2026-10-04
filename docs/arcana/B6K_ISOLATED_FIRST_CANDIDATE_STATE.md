# B6K Isolated First Candidate State

## Decision

`PASS_B6K_ISOLATED_FIRST_CANDIDATE_STATE` at source HEAD
`c38de1c7ee59ebc49af070a9214cf7b3141e799b`.
The candidate gate is `CANDIDATE_FIRST_STEP_VALIDATED`. It is an isolated,
pre-transition candidate and is not canonical T1.

## Construction

The exact B6J binary64 interval is `27123.405156307464` years
(`0x1.a7cd9ee14b895p+14`), from 210 Ma to 209.97287659484368 Ma. The existing
exact constant-Euler quaternion transform was applied to each governed
`(canonical node, plate)` incidence. This keeps distinct plate-local coordinates
at boundaries and junctions without averaging or assigning a unique owner.

The candidate contains 66,435 plate-local coordinate rows for 64,442 canonical
node identities, 1,983 interfaces / 3,966 interface sides, and 20 junctions /
60 junction sides. The binary payload SHA256 is
`9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a`.
Candidate identity is
`c173852a93c702abfa8b61701c7fe4c001b71d86adf0b4fe893769105e380a58`.

Topology identity is held exactly. The rift activation predicate is satisfied
at the pre-transition endpoint, but transition status remains `NOT_EXECUTED`.
No event record was created. Per-interface output carries forward only the
governed B5 T0 relative-normal/tangential kinematic diagnostics.

## Validation

- Radius drift max: `2.220446049250313e-16` on unit-sphere coordinates.
- Plate-local edge-length drift max: `1.457167719820518e-16`.
- Plate-local triangle-area drift max: `3.0899761915836876e-18`.
- Triangle orientation failures: 0; NaN/Inf: 0.
- Replay rebuild matched candidate bytes, ordered support pairs, and SHA256.
- Isolated HistoryStore append/reopen, STATE, HISTORY, DIFFERENCE, WHY,
  UNKNOWN and candidate temporal snapshot checks passed.
- Support member query remains partial because the current store selector does
  not encode/query the per-node plate-local relation directly. Refinement stays
  blocked until canonical publication.
- The source snapshot, including external governed payload identities, was
  unchanged before and after construction. The production FEG and owner-bound
  runtime package were independently checked against their declared SHA256
  values and remained unchanged; they were not read as candidate inputs. The
  B3 qualification work directory contains no retained canonical store.

## State transfer and gates

Only B6G-authorized exact rigid plate-local geometry was advanced. B6E/B6G
field families remain reference-only, asynchronous at their latest T0 validity,
or unresolved as MODEL_REQUIRED/UNKNOWN; no values were imputed. The existing
SYSTEM_MEMORY declarations and B6G retention classifications were recorded.

`mechanics_authorized`, `forward_evolution_authorized`, `t1_created`,
`canonical_state_changed`, and `rift_transition_executed` remain false. No
ShellSet, OrbData mechanics, or second step ran.

## Tests and next stage

- B6K focused: 12 passed.
- B5–B6J regression: 118 passed.
- Active R6 suite: 425 passed (413 baseline plus 12 B6K tests).
- `compileall`, `py_compile`, JSON/binary/manifest/path checks and
  `git diff --check`: see retained `B6K_TEST_RESULTS.json` and
  `B6K_ARTIFACT_MANIFEST.json`.

Next authorization: `AUTHORIZE_FIRST_CANDIDATE_STATE_QUALIFICATION_AND_QUERY_ACCEPTANCE`.
Canonical T1 publication is not authorized.
