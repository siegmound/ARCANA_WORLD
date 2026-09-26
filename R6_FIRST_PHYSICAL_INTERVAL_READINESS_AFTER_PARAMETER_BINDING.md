# R6 first physical interval readiness after parameter binding

**T0:** 210 Ma. **Evaluation:** static only; no evolution was executed.\
**Decision:** `T0_VECTOR_PARTITION_AND_EVENT_ELIGIBILITY_BINDING_REQUIRED_BEFORE_REPLAY`\
**Verdict:** `EARTH_PRIORS_BOUNDED__INITIAL_MOTION_AND_RIFT_CENSUS_REMAIN_UNBOUND`

## Readiness checks

| Check | Result | Evidence |
|---|---|---|
| Initial plate motions fully specified | No | Earth aggregate RMS prior does not specify per-plate angular vectors or a canonical draw. |
| Reference frame specified | Yes, as a gauge only | Least-squares removal of common rigid rotation from area-weighted surface velocities; it is not mantle-fixed physics or torque balance. |
| Motion segment initializable | No | No per-plate rates, valid horizon or causal rate-change law. |
| Adaptive scheduler can determine first legal dt | No | No solver precision, displacement, topology, event-localization or error tolerances. |
| t0 event census executable | No | Support-preserving vector partition is not materialized; kinematics, weakness and extension state are unavailable. |
| Rift eligible at t0 | Unknown / not evaluated | Unknown weakness cannot be treated as eligible or ineligible. |
| If no rift eligible, can restricted interval proceed? | Not established | There is no executable census proving absence of an immediately possible event. |
| Trigger/split bound if eligible | No | No transferable initiation trigger, split topology or lineage consequence. |
| Checkpoint schema can be created | Yes | Architecture contract binds restart fields and identifiers. |
| Deterministic replay guaranteed | No | No law parameters or pinned/validated R6 kinematics adapter. |

The canonical t0 payload remains registered as `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`. The 1° grid and coarse plate labels are not upgraded to exact geology. The vector method is a deterministic union of source cells with parent-cell provenance and inherited coarse uncertainty; actual materialization is a separate implementation prerequisite.

## Exact blocking set

1. Select no per-plate motion until a governed vector partition, adjacency and initial relative-motion law exist; the published RMS values remain comparator priors only.
2. Bind a causal motion segment/update rule and its validity limits.
3. Materialize and validate the support-preserving t0 vector partition.
4. Keep weak-zone support UNKNOWN unless independently supported; bind the extension-based tri-state eligibility inputs and evaluate the census.
5. If eligibility is ELIGIBLE or cannot be excluded, bind initiation and split/lineage rules before the interval.
6. Pin/validate the geometry adapter and derive its precision/error tolerances for largest-safe-step and event localization.
7. Precommit the parameter uncertainty and canonical-realization policy without choosing by map appearance or downstream outcome.

No execution contract was created. Full 210 Myr evolution remains unauthorized. Climate is not required for initial plate kinematics; bathymetry remains UNKNOWN and is not a first-interval prerequisite; Deep remains optional and unbound. A1 was not used as authority. No provider was acquired.

**Next action:** `R6_T0_VECTOR_PARTITION_AND_FIRST_INTERVAL_EVENT_ELIGIBILITY_BINDING`. Do not run a replay until the t0 census resolves the rift gate and the motion/step law is executable.
