# GEODYN-3B — Experimental trajectory archive MVP

**Date:** 2026-10-27
**Branch:** `r6/multiphysics-integration-20261026`
**Implementation baseline:** `0256458553f5ee856739cd0abff7561d90ad1198`
**Decision:** `GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP_LOCAL_PASS__FAIR_QUALIFICATION_PENDING`

## Scope and outcome

Implemented a small, solver-independent metadata index and read-only query API for an existing ASPECT PVD/PVTU/VTU series. The implementation follows the ratified [GEODYN-3A contract](GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT.md) and reuses the qualified `AspectSnapshotSeries` reader plus canonical identity/hash primitives. It does not modify `HistoryStore`, `HistoryQueryService`, `DomainStateEnvelope`, or `segment_archive.py`.

The archive is explicitly `SYNTHETIC_ENGINEERING_ONLY`; caller-provided run/build/source claims remain `OPERATOR_REPORTED_UNAUTHENTICATED`. The indexer independently measures original file lengths and SHA256 values and compares them with the caller's expected inventory. A matching digest verifies bytes against that supplied inventory; it does not authenticate who produced the source or establish scientific authority.

## Implemented API

In `src/arcana_worldsim/r6/experimental_trajectory_archive.py`:

- `index_existing_aspect_series(*, trusted_source_root, pvd_relative_ref, run_identity, expected_source_inventory, output_index_root, limits=None)` creates a new index directory exclusively. The parent must already exist. It writes an incomplete marker first, audits and hashes the existing source files incrementally, then writes `manifest.json` and `manifest.sha256`. It never copies VTU/PVTU/PVD payloads. Failure leaves the destination and incomplete marker for inspection; no durability or atomicity guarantee is claimed.
- `ExperimentalTrajectoryArchive.open(index_ref, *, trusted_index_root, trusted_source_roots=None, limits=None)` opens a sealed index and optional trusted external source roots. Metadata remains queryable when source files are unavailable; numeric reads then return an explicit missing-payload status.
- Metadata operations: `get_run`, `query_snapshots` (inclusive interval in the declared native time basis), `get_snapshot_at` (exact time, ambiguity reported), `list_meshes`, `get_mesh`, and `list_fields`.
- Numeric operations: `get_snapshot` and `get_field` read from the original source on demand and check raw-file and typed-array identities. The existing reader materializes all arrays of the requested snapshot; this is not a streaming field decoder.
- `verify_integrity()` validates the manifest seal and references and rehashes the external source inventory when its trusted root is supplied.

Results use explicit statuses such as `FOUND`, `MISSING_RUN`, `MISSING_SNAPSHOT`, `MISSING_FIELD`, `MISSING_PAYLOAD`, `AMBIGUOUS`, `INCOMPATIBLE_TIME_BASIS`, `ARCHIVE_INCOMPLETE`, `CORRUPT_MANIFEST`, and `CORRUPT_PAYLOAD`. There is no nearest-time lookup, interpolation, extrapolation, remapping, or restart claim. Path traversal and symlink/reparse references are rejected. The implementation supports only formats accepted by the qualified ASPECT snapshot reader (single rank/single Piece and its documented inline encodings).

## Archive contents and identities

Schema: `ARCANA_GEODYN_EXPERIMENTAL_TRAJECTORY_V1`. The deterministic logical IDs bind solver/source/configuration/input declarations, attempt identity, native time tokens, mesh/field identities, and payload digests. Absolute machine paths and availability-check timestamps are excluded from logical identity. Relative source references and current availability are recorded separately. The archive contains metadata and references only; its expected finalized membership is `manifest.json` and its SHA256 sidecar. A self-contained sidecar is a consistency check, not an independent signature.

The manifest distinguishes solver completion time from last stored snapshot time and records the reader's observed mesh/schema stability, invariant/dynamic fields, numeric duplicate fields, and time coverage observations without assigning physical meaning based on names. Mesh identity is attached to each snapshot, so changing meshes are represented. Reconstruction is `NOT_CLAIMED`; restart is `NOT_AVAILABLE`.

Example usage:

```python
result = index_existing_aspect_series(
    trusted_source_root=source_root,
    pvd_relative_ref="solution/solution.pvd",
    run_identity=claim,
    expected_source_inventory=expected_files,
    output_index_root=new_index_directory,
)
archive = ExperimentalTrajectoryArchive.open(
    result.index_ref,
    trusted_index_root=new_index_directory,
    trusted_source_roots={"source": source_root},
)
snapshots = archive.query_snapshots(run_id, start=NativeTime(0.0, "s", basis_id))
```

The caller must supply the values and source inventory shown above; they are not inferred as authoritative by the archive.

## Local verification

Windows Python 3.12.10, focused command:

```text
python -m pytest -q -rs --basetemp=.pytest_geodyn3b_final_20261027 tests/test_r6_experimental_trajectory_archive.py tests/test_r6_aspect_snapshot_reader.py
42 passed, 2 skipped
```

Both skips are Windows symlink-creation tests skipped because the current account lacks the required privilege (`WinError 1314`): one new archive source-path test and one existing reader path-safety regression. These cases remain for execution on Linux. `py_compile` passed for the new module and tests. No ASPECT process or FAIR command was run.

The tests cover deterministic index bytes and IDs under source relocation; exact/inclusive time queries and duplicate-time ambiguity; variable mesh identities; on-demand readback and source immutability; missing and mutated payloads; wrong source inventory; interrupted finalization; path traversal and output collision; and reader-format/path regressions. No authentic R1 FAIR payloads were present in the Windows validation inputs, so this result does not qualify the 11-snapshot series.

## GEODYN-3C handoff

On the exact reviewed implementation commit, use the original FAIR R1 files read-only and a new, previously absent evidence/index directory outside the source series. Provide the expected relative-path/length/SHA256 inventory from an independently preserved source manifest, run the indexer, then reopen and verify the index and each source reference. Compare the resulting 11 native times, point/cell counts, field schema, typed numeric digests, invariant/dynamic/duplicate observations, and coverage against the independent `NUMERIC_AUDIT.json`. Confirm the final archived snapshot remains at the reported 1.0142299266 s while solver completion is 1.098612289 s; do not create a terminal snapshot. Preserve the earlier real-format probe failure and the operator-reported R1 qualification as historical records. No ASPECT solve is part of GEODYN-3C.

Until that check is completed, FAIR qualification is pending. All scientific and canonical gates remain unchanged, including `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false` and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
