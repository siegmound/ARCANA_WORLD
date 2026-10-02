# R6 B3 — Governed T0 Read-Only WORLD_HISTORY Ingest

## A. Qualified revision and scope

Source baseline: `33ab6f204e75d25dbaa1f0d27ef75203245f8df3`, branch
`r6/b3-governed-t0-read-only-ingest`. The B3 adapter and runner are authored
on this baseline. Qualification indexes existing T0 authority in a temporary
file-backed `HistoryStore`, closes it, opens a new store instance, and verifies
records, queries, provenance and accounting. Payload bytes are not copied into
WORLD_HISTORY.

## B–C. Authority set and identities

`outputs/r6_world_history_b3_t0_ingest/B3_T0_AUTHORITY_INVENTORY.json`
records 20 unique tracked-document/payload paths with roles, expected and
actual identities, byte sizes and read-only verification. The ingest uses the
canonical initial-world payload, its derived vector partition and the tracked
canonical plate-kinematics record. The inventory also audits the B-PANGAEA
candidate, closed-surface derivative, FEG, runtime package and FAIR evidence;
these are not promoted as physical state.

## D–E. Adapter and T0 state inventory

The adapter emits 14 deterministic semantic states: `physical_geography`,
`land_ocean`, `province_state`, `topography`, `tectonic_plate_partition`,
`plate_kinematics`, and eight explicit `UNKNOWN` domains (`bathymetry`,
`tectonic_kinematics_grid`, `boundary_classification`, `deep`, `climate`,
`hydrology`, `weak_zone_state`, `junction_physical_semantics`). Four
geography/province/topography views share the parent payload identity; semantic
state IDs remain distinct from payload identity. No numeric values are
synthesized for UNKNOWN domains.

## F–H. Retention and authority mapping

The adapter references supported initial-world fields and preserves UNKNOWN
as UNKNOWN. Grid-level tectonic motion remains UNKNOWN; separately governed
plate-level kinematics is a distinct state. The current materialization
manifest supplies a 180×360, 1-degree nominal grid. B3 does not claim per-cell
query membership. The B-PANGAEA v2 field package remains
`CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION`, so its system-memory sufficiency
classification remains `REVIEW_REQUIRED`. FEG and ShellSet runtime products
remain derived/runtime artifacts outside the physical-state mapping.

## I–K. Provenance, publication and query

All 14 states and one provenance record were published atomically. A newly
constructed `HistoryStore` reopened all 14 state records and provenance with
stable identities. Queries returned `FOUND`, `UNKNOWN`, `MISSING_DOMAIN`, and
`MISSING_TIMESTAMP`. A per-cell query against `GRID` returned
`SUPPORT_MISMATCH` with `CELL_MEMBERSHIP_CANNOT_BE_RESOLVED_FOR_DECLARED_SELECTOR`;
no cells were enumerated. `WHY` returned the state and its recorded
provenance/source references. The equal-state difference check was a contract
check only; no temporal difference was created.

Two independent adapter builds produced identical semantic state and
provenance IDs; their identity digest is recorded in the state inventory and
qualification result.

The focused adapter fixture test passed (1 test), and the complete active R6
suite passed (324 tests; one new adapter contract test over the 323-test B2
baseline). The explicit real-artifact integration runner also passed. These
results are summarized in `B3_TEST_RESULTS.json`.

## L. Storage accounting

The retained accounting JSON measures only the temporary WORLD_HISTORY store.
The store owns zero copies of governed payload bytes. The two external NPZ
payloads and the tracked kinematics artifact are separately reported as
references. The 500,000,000,000-byte hard cap applies to WORLD_HISTORY
canonical store accounting, not the repository or referenced source files.

## M. Source immutability

Before/after SHA-256 and byte-size snapshots cover every authority document
and inspected payload. Hashes and sizes matched. Modification timestamps are
secondary evidence only.

## N. Limitations

- `GRID` has no current direct cell-membership query contract.
- B-PANGAEA v2 remains a candidate and needs separate materialization
  validation before it can supply canonical physical state.
- B3 does not adjudicate minimal physical sufficiency or a temporal law.
- The B3 authorization boundary keeps runtime authorization limited to
  `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`; B3 did not use that
  capability. Mechanics, forward evolution, dt, T1 and canonical-state change
  remain unauthorized. Historical gate snapshots inside FEG/runtime manifests
  are recorded as source evidence and were not rewritten.

## O. Scientific safety

No T0 payload was modified or regenerated; no provider was contacted; no
OrbData/ShellSet mechanics, dt selection, T1, canonical advancement, or
authority promotion occurred. Only the authorized read-only WORLD_HISTORY
ingest was exercised.

## P. Next-stage readiness

Decision: `READY_FOR_B4_WITH_GAPS`. Plate kinematics is the best first temporal
adapter to design because its canonical T0 realization and partition parent
are already bound. B4 must first establish and qualify a rotation/interval
law. This recommendation authorizes design and qualification only; it does
not authorize a timestep, evolution, T1 or mechanics.

Machine-readable details and hashes are in
[`outputs/r6_world_history_b3_t0_ingest/README.md`](../../outputs/r6_world_history_b3_t0_ingest/README.md).
