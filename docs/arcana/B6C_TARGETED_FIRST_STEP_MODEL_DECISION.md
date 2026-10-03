# R6 B6C Targeted First-Step Model Decision

Decision: **PASS_B6C_TARGETED_FIRST_STEP_MODEL_DECISION**; qualified source `7b8f21bd6c1802df2a50a7eece70cfa36b2d9278`.

## Rotation action

The T0 realization convention is uniquely derivable, rather than an authorial gap: the producer computes `v = omega × r`; the Cartesian axes are +X at longitude 0° on the equator, +Y at +90°, +Z north, with the cross product fixing the right-handed orientation. `finite_rotation.py` applies the positive quaternion action to column XYZ vectors, whose infinitesimal derivative is `omega × x`. This yields an active right-hand rotation for constant omega in the internal synthetic NNR gauge. Angular units are rad/year, coordinates are unit-sphere XYZ, and the physical sphere radius is 6,371,000 m. This closes convention only; no interval or coordinate motion is authorized. B5's earlier statement that handedness was not separately declared is superseded by these directly inspected producer/code semantics.

## Topology, boundary and junction decisions

No candidate topology model is selected. The fixed-until-detector, explicit invariance-window, event-driven, external-provider and authorial-segment alternatives require different scientific authority and stopping/lineage behavior. The 27,123.405-year rift bound is only a conditional rift activation event, not a topology window.

The 1,983 boundaries have unresolved geological type and polarity, and all current finite steps remain blocked. Discontinuous slip, finite-width deformation and constraint-solved interfaces are distinct physical models; duplicated geometry is representation only. No evidence selects a type, polarity, rheology, fault law or solver. A unified law may handle boundaries and junctions only if it supplies explicit multi-interface compatibility for all 20 junctions without owner assignment.

## Mesh and state transfer

Same-connectivity rigid coordinate update fits single-plate interiors only. Duplication requires an authorized two-sided interface plus lineage; local remesh needs a selected zone/trigger/state map; global remesh is unsupported. No next-state mesh representation is selected. B3's 14 state families are inventoried in the machine package: supported geography fields require field-specific material/hold/recompute rules, plate support depends on topology policy, UNKNOWN domains remain UNKNOWN, and B0-G SYSTEM_MEMORY cannot be discarded. Remapping is not implemented or authorized.

## Numerical validity and first-dt closure

No value is selected for angular displacement, nodal displacement, edge-fraction, boundary gap/crossing, mesh quality, topology event lead, remesh trigger or solver stability. Their measurement variables and units are registered in JSON. The rift horizon remains a model event stop only.

Rotation convention is CLOSED. Conditional positive-duration kinematics remain MODEL_SELECTED_NOT_QUALIFIED. Topology, interface/junction physics, mesh/state transfer and numerical limits remain authorial/model blockers. ShellSet remains undecided until a physical model is selected; B7 execution is not authorized. First dt remains NOT_READY_FOR_FIRST_DT.

## Authorial decisions and next action

- **B6C-AD-01** — Which positive-duration topology policy governs the first interval?
- **B6C-AD-02** — How is relative normal/tangential motion physically accommodated at UNKNOWN boundaries?
- **B6C-AD-03** — What compatibility law closes multi-boundary motion at 20 shared junctions?
- **B6C-AD-04** — Which T0 fields are material-attached, held, recomputed, or replayed through the chosen geometry change?
- **B6C-AD-05** — Which geometric accuracy, topology and (if selected) solver limits bound the first dt?

Next recommendation: `AUTHORIZE_AUTHORIAL_MODEL_DECISION`. This does not authorize dt, T1, canonical motion, topology mutation or forward evolution. All scientific execution gates remain closed.

Validation: focused B6C 6 passed; full R6 suite 356 passed; py_compile PASS; JSON/manifest PASS; portability PASS; diff check PASS.
