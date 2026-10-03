# R6 B6 Dependency and Temporal-Gap Adjudication

Decision: **PASS_B6_DEPENDENCY_TEMPORAL_GAP_ADJUDICATION**

## A. Baseline

Branch `r6/b6-dependency-temporal-gap-adjudication`, source commit `b0891494f58272aac5fb60811e77982e00fab80b`. The committed B5 source qualification `95d4bbe8d61e8796299e496822a95f7b8dac67cc` is an ancestor of this baseline; its implementation files and retained evidence were hash-checked against the current committed tree.

## B. First-step causal graph

T0, instantaneous forcing, and B5 spatial support are present. A positive-time candidate state requires a temporal segment, event bound, shared-boundary/junction accommodation, and geometry/state transfer policy. The dependency graph is machine-readable in `B6_FIRST_STEP_CAUSAL_GRAPH.json`.

## C. Current T0 domain requirements

B3 contains 14 semantic states. Plate partition is the state that must spatially transition; plate kinematics is a driver; B5 supplies derived grid/node support. Climate, hydrology, deep, and bathymetry remain UNKNOWN or separate-clock references only when not consumed. No domain is declared dynamically constant.

## D. Positive-duration kinematic authority

ABSENT. B4 qualifies only the 210 Ma instantaneous Euler anchor. The prior describes a constant first segment conditionally but explicitly says it was not exercised and has no validity/change horizon. No stage rotations, finite rotations, multiple anchors, or interpolation rule are governed.

## E. Reference-frame adjudication

The internal T0 computational axes are uniquely derivable from producer code: spherical `lat/lon` to XYZ and velocity `omega × r`, with +X at lon 0°, +Y at +90°, +Z north (right-handed by that cross-product convention). The gauge is synthetic NNR, not Earth-fixed/mantle/hotspot authority. No external-frame transform is authorized.

## F. Topology-time requirements

A full long-term event calendar is not required before the first interval, but a positive lower bound on the next relevant event—or explicit interval-specific no-event authority—is required. The 30 candidate plate pairs remain UNKNOWN and the current guard horizon is null.

## G. Mechanics necessity

A physical shared-boundary/junction accommodation response is required before any first physical step. Current governed policy is zero-capacity fail-closed; all 1,983 boundaries have nonzero relative motion, no segment may advance, and junction response is blocked. Whether that response needs a numerical solver is unresolved.

## H. ShellSet decision

**SHELLSET_REQUIREMENT_UNRESOLVED**. ShellSet is not required merely because it exists; no physical law or minimum solver-output contract has selected it. Legacy Earth5R BCS is not ARCANA authority.

## I. External/provider/model gaps

The minimum providers are a temporal kinematic model, event/topology bound, boundary/junction accommodation model, and mesh/state transfer validity rule. Provider research is targeted after authorial model-family selection; no provider search or installation occurred in B6.

## J. First-step state semantics

A future candidate needs plate geometry/partition, driver and support identities, shared boundary/junction response, support/state transfer, source provenance and uncertainty, and an event/forcing record. WORLD_HISTORY checkpoint/replay schema can retain those dependencies. No candidate state was created.

## K. Temporal constraints

Only the 210 Ma anchor is known. The existing 27,123.405-year rift guard is diagnostic and explicitly not a legal dt or positive horizon. No numerical threshold is supplied.

## L. Multi-domain clocks

WORLD_HISTORY supports distinct clocks. Climate and hydrology need not run on the tectonic clock if left UNKNOWN/passive and not consumed; no stale state may be represented as an updated simultaneous state.

## M. Minimum active domain set

Candidate set, not authorized: `tectonic_plate_partition`, `plate_kinematics`, and B5 `tectonic_kinematics_grid` support, plus boundary/junction accommodation and mesh transfer. Other domains enter only where the selected causal model consumes them.

## N. Authority floors

Positive-time motion, event bounds, and boundary accommodation need explicit hard authority. Deterministic support and the internal frame derivation may be derived from governed inputs. A qualified processor cannot substitute for scientific input authority.

## O. UNKNOWN policy

Deep, climate, hydrology and bathymetry may remain UNKNOWN only when outside the first transition's consumed inputs. Weak-zone/event eligibility and boundary/junction response cannot be treated as absent or zero under current guards.

## P. Provider research decisions

The next step is authorial decision and targeted model design, with narrowly scoped repository audits. External research is conditional on selecting a physical family. ShellSet/engine qualification follows only after its input/output contract is fixed.

## Q. Windows/Ubuntu execution plan

Windows: authority adjudication, model design, static adapter work and small tests. Ubuntu: later native solver/NVHPC qualification or genuinely heavy solver/reconstruction work only if selected and authorized. No heavy task is required now.

## R. B7 decision

**B7_DECISION_BLOCKED_BY_MISSING_TEMPORAL_AUTHORITY**. Mechanical boundary response is required, but solver necessity and exact outputs cannot be scoped before temporal and physical law authority exists.

## S. First-dt readiness

**NOT_READY_FOR_FIRST_DT**. B6 does not authorize dt, mechanics, T1 or evolution.

## T. Exact blocking set

- `B6_TEMPORAL_KINEMATIC_LAW` — positive-duration motion segment validity/change law for 12 plate Euler rates
- `B6_TOPOLOGY_EVENT_BOUND` — positive lower bound on next relevant rift/topology event or interval-specific no-event authority
- `B6_BOUNDARY_JUNCTION_ACCOMMODATION` — shared boundary and junction physical response to nonzero relative motion
- `B6_MESH_STATE_TRANSFER` — partition-preserving geometry update/remap criterion and support/material transfer for a candidate state
- `B6_NUMERICAL_VALIDITY_LIMITS` — precommitted displacement/rotation/topology/Jacobian limits and any selected solver stability bound

Scientific gates remain: runtime permission is limited to loading/consuming the governed ARCANA T0 runtime package; mechanics, dt, T1, canonical mutation and forward evolution remain false.

Validation: active R6 suite 340 passed; B6 focused tests 4 passed; py_compile PASS; JSON/manifest/path checks PASS; diff check PASS.
