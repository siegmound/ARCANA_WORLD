# R6 B5 Plate Support, Topology and Temporal Integration

Decision: **PASS_B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION**

## A. Baseline

Qualified source `95d4bbe8d61e8796299e496822a95f7b8dac67cc` on `r6/b5-kinematic-support-topology-integration`; read-only T0 qualification.

## B. Governed spatial authority

The 210 Ma plate partition is model-derived from canonical T0 and covers 64,800 parent faces and 12 plates. It is not a hard anchor.

## C. Plate-face support

Face membership is direct in the governed vector-partition payload. Each parent face maps to one plate ID.

## D. Plate-node/grid support

Node membership is exactly derived as the set of plate IDs on incident parent faces through the canonical mesh incidence graph. It does not assign shared nodes to one plate.

Counts: 62,469 interior, 1,953 boundary-shared, 20 junction-shared, 0 unknown.

## E. Boundary semantics

The 1,983 segments define shared geometry, adjacent plate identities, ordered endpoints, lengths, and 20 junctions. Geological type, polarity, material continuity, fault/slip behavior and mechanical accommodation remain UNKNOWN.

## F. Instantaneous relative motion

Relative normal/tangential motion is a derived governed diagnostic at exactly 210 Ma. It is not a boundary mechanical response.

## G. Reference frame

The census binds the B4 T0 kinematics gauge `SYNTHETIC_AREA_WEIGHTED_LEAST_SQUARES_NO_NET_ROTATION_GAUGE` and 1-degree latitude/longitude grid; sphere radius is 6,371,000 m. Vector units are rad/year, boundary rates are m/year. Cartesian axis/handedness is not separately declared, no transform is inferred, and no Earth-fixed authority is claimed.

## H. Positive-duration motion law

**ANCHOR_ONLY_NO_POSITIVE_INTERVAL.** There is no governed validity interval, interpolation rule, or topology-event calendar. The instantaneous anchor cannot be extended to any positive duration.

## I. Topology transition contract

Existing EventRecord is sufficient for schema-only split, merge, boundary birth/death, and junction reassignment fixtures. No fixture claims an ARCANA historical event.

## J. Plate lineage

Plate IDs are anchored at 210 Ma only. Continuation, split, merge, creation and termination lineage are not governed.

## K. WORLD_HISTORY support integration

The forcing, support and boundary states plus provenance and fixture events were published transactionally, destroyed, reopened, queried and WHY-traced. Semantic IDs persisted. Parent T0 history was not mutated.

## L. Downstream requirements

Available: instantaneous plate motion. Derivable: face/node support and T0 relative boundary motion. Missing: positive-duration driver, event schedule, boundary accommodation and deformation response.

## M. ShellSet requirements

T0 FEG/package and plate support are available/derivable. ARCANA boundary conditions replacing Earth5R BCS, temporal law and boundary mechanics remain missing. Legacy Earth5R fault assumptions are not treated as ARCANA requirements.

## N. First-dt prerequisites

The qualified support map closes the spatial binding prerequisite. Positive-duration kinematic validity, topology calendar/lineage and frame adjudication must be resolved before dt. Mechanical accommodation and material/thermal response must be resolved before mechanics; none is selected here.

## O. Temporal constraint registry

Only the 210 Ma anchor is known. No positive-duration interval, event boundary, regime boundary or authority transition is registered.

## P. Source immutability

PASS_READ_ONLY_SOURCE_UNCHANGED; 28 source artifacts had unchanged content hashes and byte sizes.

## Q. Remaining gaps

No governed positive-time motion law, transition calendar, stable plate lineage, geological boundary classes/polarity, mechanical accommodation, or ARCANA ShellSet BCS replacement.

## R. B6 readiness

**READY_FOR_B6_WITH_UNRESOLVED_TEMPORAL_AUTHORITY.** Maximum next authorization: B6 dependency and temporal gap adjudication only. No dt, evolution, T1, mechanics, or forward evolution is authorized.

Scientific gates: runtime authorization remains limited to loading/consuming the governed ARCANA T0 runtime package; mechanics, dt, T1, canonical mutation, and forward evolution remain false.

Validation: focused B5 tests PASS; 7 focused tests; full active R6 suite PASS (336 tests, 129.92 s); py_compile PASS; diff check PASS.
