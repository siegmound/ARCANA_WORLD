# R6 Physical Domain T0 Authority Reconciliation and Binding

**Decision:** `R6_PHYSICAL_DOMAIN_T0_BOUND__FIRST_INTERVAL_BLOCKED`

T0 is bound as a historical state at 210 Ma. Forward evolution remains unauthorized.

## Canonical T0 and validation

- Parent payload: `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c` (1,169,900 bytes; read-only hash verified)
- Vector partition: `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab` (5,681,184 bytes; read-only hash verified)
- Kinematics: `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4` (canonical JSON identity recomputed)
- Inventory: 12 plates, 64,800 parent faces, 1,983 boundary segments, 30 pairs, 20 junctions.
- Boundary support remains coarse support on the 1-degree parent grid.
- Unknown bathymetry, deep, climate, hydrology, weak-zone state, boundary class, and junction semantics are preserved.

## Authority lineage

The old Simulation1 recovery binding and V1 event census/guard are historical. The materialized synthetic T0 is the current authority; the V3 census supersedes V1 for the precommitted minimal event guard. Diagnostic continuum and pyGPlates artifacts do not acquire scientific authority.

| Artifact | Classification | Status | Commit |
|---|---|---|---|
| `R6_SIMULATION1_PHYSICAL_GEOGRAPHY_T0_BINDING.json` | HISTORICAL_SUPERSEDED | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json` | CURRENT_SUPPORTING_EVIDENCE | AUTHORIAL_DESIGN_SPECIFICATION__NOT_MATERIALIZED | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json` | CURRENT_AUTHORITY | MATERIALIZED_AND_VALIDATED | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json` | CURRENT_AUTHORITY | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json` | CURRENT_AUTHORITY | PRECOMMITTED_BEFORE_CANONICAL_DRAW | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_INITIAL_KINEMATICS_MANIFEST.json` | CURRENT_AUTHORITY | CANONICAL_SYNTHETIC_MODEL_REALIZATION_MATERIALIZED__FIRST_INTERVAL_BLOCKED | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_CANONICAL_PLATE_KINEMATICS.json` | CURRENT_AUTHORITY | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json` | CURRENT_SUPPORTING_EVIDENCE | T0_MOTION_PRIOR_CANONICALIZED__FIRST_INTERVAL_BLOCKED_UNKNOWN_RIFT_ELIGIBILITY_AND_UNBOUND_DT | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json` | CURRENT_SUPPORTING_EVIDENCE | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_EVENT_ELIGIBILITY_CENSUS.json` | HISTORICAL_SUPERSEDED | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json` | CURRENT_AUTHORITY | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_FIRST_INTERVAL_EVENT_GUARD.json` | HISTORICAL_SUPERSEDED | BLOCK_FIRST_INTERVAL__NO_GOVERNED_POSITIVE_EVENT_LEAD_TIME | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json` | CURRENT_SUPPORTING_EVIDENCE | PRECOMMITTED_BEFORE_T0_CENSUS_V3 | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_CONTINUUM_DEFORMATION_GUARD.json` | CURRENT_SUPPORTING_EVIDENCE | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST.json` | DIAGNOSTIC_ONLY | NOT_MATERIALIZED__GEOMETRIC_FEASIBILITY_UNDETERMINED | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_BOUNDARY_ZONE_REFERENCE_VALIDATION.json` | DIAGNOSTIC_ONLY | FAIL_CLOSED_REFERENCE_GEOMETRY_NOT_MATERIALIZED | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_T0_CONTINUUM_REFERENCE_VALIDATION.json` | DIAGNOSTIC_ONLY | REFERENCE_MAP_MATERIALIZATION_BLOCKED | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION.json` | DIAGNOSTIC_ONLY | SYNTHETIC_TRACE_FIXTURE_PASS__CANONICAL_GLOBAL_FIELD_NOT_RUN | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json` | BLOCKER | NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_TOPOLOGY_CONTACT_GUARD.json` | BLOCKER | BLOCKED_PHYSICAL_BOUNDARY_ACCOMMODATION_AND_JUNCTION_RULES_UNBOUND | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_JUNCTION_COMPATIBILITY_CONTRACT.json` | BLOCKER | BLOCKED_T0_INCIDENCE_ONLY | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json` | BLOCKER | not-recorded | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json` | BLOCKER | BLOCKED_TOPOLOGY_CONTACT_AND_PARTITION_EVOLUTION_SEMANTICS | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json` | BLOCKER | OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json` | BLOCKER | OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json` | BLOCKER | OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE | `caf37cfc790f702c0cafc00c53e079236b7e294c` |
| `R6_PYGPLATES_CANONICAL_MAPPING_REPORT.json` | CURRENT_SUPPORTING_EVIDENCE | FAIL | `c17f1194bd948f4961da57fd5a57d4f6150caddd` |
| `R6_PYGPLATES_TOPOLOGY_ASSEMBLY_REPORT.json` | DIAGNOSTIC_ONLY | FAIL | `8987f8669d51e81ddbc0824295b98bb065c90f2a` |
| `R6_PYGPLATES_STATIC_TOPOLOGY_RESOLUTION_REPORT.json` | DIAGNOSTIC_ONLY | PARTIAL | `948d322c85830e9c188870ca26d71e0b342d1677` |

## P01–P12

| ID | Requirement | Current status | Before T0 | Before first interval | Later topology event only |
|---|---|---|---:|---:|---:|
| P01 | Initial plate kinematics | `BOUND_FOR_CANONICAL_SYNTHETIC_T0_REALIZATION` | True | True | False |
| P02 | Motion segment validity | `BOUND_ONLY_FOR_T0_SNAPSHOT` | True | False | False |
| P03 | Motion renewal/change law | `UNBOUND` | False | False | False |
| P04 | Master plate geometry | `MATERIALIZED_AND_VALIDATED` | True | True | False |
| P05 | Weak-zone state/strength | `UNKNOWN_PRESERVED` | False | False | False |
| P06 | Extensional forcing | `KINEMATIC_DIAGNOSTIC_BOUND` | True | True | False |
| P07 | Rift eligibility | `BOUND_FOR_MINIMAL_GUARD_AT_T0` | True | True | False |
| P08 | Rift initiation trigger | `BOUNDED_MODEL_GUARD__NO_EVENT_CREATED` | True | True | False |
| P09 | Plate split topology | `DEFERRED_UNTIL_RIFT_EVENT` | True | False | True |
| P10 | Initial eligibility census | `CURRENT_CENSUS_COMPLETE` | True | True | False |
| P11 | Numerical acceptance and step limits | `BLOCKED` | False | True | False |
| P12 | Uncertainty | `BOUND_FOR_SINGLE_T0_REALIZATION` | True | True | False |

## World History binding

- T0, HistoryStore, and physical-domain registry bound: **True / True / True**.
- State ID: `r6state_1d36fb90cd23443407ce6c63611a65b74c5a9157bd89b1c6cec449d9b927f2d9`; provenance ID: `r6prov_89cec59543ee455ab120ebb523ece11c3d0b44d45944daa400bfbf655eaa3392`.
- Temporal roles: AUTHORITY_ANCHOR, HISTORICAL_SNAPSHOT, REFINEMENT_ANCHOR. Checkpoint roles are unassigned because no restart bundle or consumer exists.
- `STATE_AT(210 Ma, physical_world)`: global state `FOUND`; lineage has 0 missing parents.
- Available resolution: ['1-degree nominal parent grid; vector edges COARSE_SUPPORT_ON_FINE_GRID']; no interpolation or finer support inferred.
- Scientific execution: false.

## pyGPlates role

`BOUNDED_SOLVER_CANDIDATE`; ARCANA remains the scientific authority. Static geometry/topology and synthetic deforming network are qualified as sufficient; canonical dynamic deformation is not yet validated. The tracked Windows runtime report remains `PYGPLATES_RUNTIME_UNAVAILABLE`; Fair evidence is external and its hashes/result identity are not bound in repository artifacts.

## First interval readiness

- T0 bound: **yes**.
- First interval executable/authorized: **no / no**.
- `dt_first_years`: `None`; no dt, t1, or W_model selected.
- Conditional event horizon is not legal dt: **True**.
- Exact next scientific blocker: Define and govern a physically defensible positive shared-boundary accommodation/deformation law that is junction-compatible; separately, the current patch operator must be redefined from canonical branch cross-sections and pure-plate anchors before a positive topology-preserving horizon can be computed.

### Recorded blockers

- **SCIENTIFIC_LAW** (`R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json`): No governed law maps relative boundary displacement into shared interface/material geometry with junction-compatible state.
- **TOPOLOGY_AND_NUMERICS** (`R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json`): No positive partition-preserving topology/contact transition horizon; dt_first_years remains null.
- **CONTINUUM_DISCRETIZATION** (`R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json`): JUNCTION_PATCH_REDEFINITION_FROM_CANONICAL_BRANCH_CROSS_SECTIONS_AND_PURE_PLATE_ANCHORS
- **JUNCTION_COMPATIBILITY** (`R6_JUNCTION_COMPATIBILITY_CONTRACT.json`): 20 degree-3 junction velocities and residual allocation semantics remain unbound.

No forward state was created and no canonical payload was modified.
