# R6 B6K Isolated Candidate Evidence

This package records one isolated first-step, pre-transition candidate built
from the governed T0 mesh, plate support, Euler vectors, frozen MVP model and
B6J-selected binary64 interval. It is not canonical T1 and does not contain an
applied rift transition.

`B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin` stores deterministic little-endian
`(node_id, plate_id)` support pairs followed by unit-sphere XYZ coordinates.
Boundary and junction relations refer to rows in this payload, so their
plate-local sides remain separate while canonical node and topology identities
are preserved.

`isolated_world_history/` is a disposable qualification store containing only
candidate/source references, the candidate state, one governed UNKNOWN state,
provenance, and a candidate temporal snapshot. It is not the canonical R6
WORLD_HISTORY store.

See `B6K_ARTIFACT_MANIFEST.json` for SHA256/size entries and
`docs/arcana/B6K_ISOLATED_FIRST_CANDIDATE_STATE.md` for the closure report.
