# GEODYN-3A — Experimental trajectory archive contract

**Date:** 2026-10-27
**Branch:** `r6/multiphysics-integration-20261026`
**Baseline:** `8c7cda39a5da4a3b98621af168fe69b61537667a`
**Decision:** `GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT_RATIFIED__GEODYN_3B_MVP_AUTHORIZED`

## 1. Purpose and authority boundary

Define an experimental, solver-neutral archive for numerical trajectories. This ratifies the contract and authorizes only the bounded GEODYN-3B MVP described in §8. This document does not implement an archive writer/storage backend, create canonical records, remap data, execute a solver or import payloads. The contract describes ASPECT output while leaving future solvers free to supply the same concepts through adapters.

Every archive has a mandatory classification. The GEODYN-2A-R1 rigid-shear fixture is `SYNTHETIC_ENGINEERING_ONLY`. Its FAIR test and numeric-comparison results are operator-reported in [the R1 closure](GEODYN_2A_R1_FAIR_QUALIFICATION_CLOSURE.md); the Linux runner, comparison report and original VTU bytes were not transferred or independently rehashed on Windows. This classification and provenance status must not be upgraded because file hashes match. Hashes establish byte consistency relative to a trusted digest, not scientific authority or who produced the evidence.

No archived model time is an ARCANA geological age. No archive record is a `DomainStateEnvelope` or World History state. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` remains in force.

## 2. Reuse review of current R6 interfaces

| Component | Available behavior | Reuse decision / concrete gap |
|---|---|---|
| `r6/identity.py` | Canonical JSON bytes, content hashes, path-independent deterministic IDs, `PayloadIdentity`, `PayloadReference`, and `verify_payload`. Identity construction rejects absolute machine paths. | Reuse canonicalization and SHA-256 primitives. Add no solver-specific IDs to canonical state classes. The current payload reference accepts opaque locators; GEODYN-3 must constrain them to archive-relative paths or a declared external evidence URI and resolve under a trusted root. |
| `r6/segment_archive.py` | Incremental JSONL output, expected-trajectory completion, an `INCOMPLETE` marker, stream/manifest hashes and validation. It explicitly marks observations `NOT_QUALIFIED_AS_RESTARTABLE`. | Reuse completion and fail-closed design patterns only. Its schema is for `ReducedState`, assumes one grid identity per trajectory, and does not represent solver completion vs last snapshot, changing meshes, field catalogs, or immutable external binary payloads. Do not force VTU data into it. |
| `r6/retention.py` | `MinimalStateContract` classifies retained/derived/static/forcing/discarded information and checks reconstruction references. | Reuse the separation principle, not its envelope contract. Its extraction materializes `DomainStateEnvelope`; it does not prove an ASPECT snapshot is reconstructible or restartable. An experimental archive needs explicit observation/reconstruction/restart capability labels and evidence. |
| `r6/storage.py` | Logical byte/file accounting, categories, reparse/symlink checks and canonical HistoryStore scope. | Reuse accounting concepts and path-safety review. It is explicitly WORLD_HISTORY accounting, includes a canonical hard cap, and has no experimental-run/payload retention policy. Do not classify an experiment as canonical or apply the canonical hard-cap semantics by implication. |
| `r6/query.py` | Exact-time/domain/support queries, provenance explanation, ambiguity and missing-support statuses, and differences between retained states without interpolation. | Reuse explicit statuses and exact-query behavior as design guidance. `HistoryQueryService` reads `HistoryStore` and `DomainStateEnvelope`, not solver snapshot indexes or external VTU payloads. No canonical query route is added. |
| `r6/adapters/aspect_snapshot_reader.py` | Bounded read-only PVD/PVTU/VTU parsing; native time value/unit; mesh and schema audit; source-file hashes, typed numeric hashes, invariant/dynamic/duplicate observations; safe-root checks; explicit in-memory numerical arrays. | Reuse as the ASPECT ingestion adapter and numerical source for a later archive builder. It currently materializes arrays and reports metadata; it does not externalize immutable payloads, finalize a trajectory archive, expose an archive query service, authenticate operator provenance, or qualify checkpoints. |

**Conclusion:** R6 already supplies identity, hash verification, a reduced-state streaming archive, generic retention concepts, canonical storage accounting and canonical historical queries. No current component supplies the requested solver-neutral experimental trajectory archive. A small independent schema/index and payload-reference layer is justified; changing `HistoryStore`, `DomainStateEnvelope`, or the W1 archive is not justified by this contract.

## 3. Proposed archive layout and versioned manifest

An archive is rooted at a newly allocated experimental run directory. A manifest/index stores metadata and references only; numerical arrays remain in immutable payload objects. The storage backend may be a local evidence directory or an external immutable evidence store. Backend locator and logical content identity are separate so copying between Windows and FAIR does not change run, snapshot, mesh, field or payload IDs.

Suggested logical layout (not an implementation requirement):

```text
manifest.json                 # sealed run/index metadata, no bulk arrays
manifest.sha256               # digest of exact manifest bytes
payloads/sha256/<digest>       # optional content-addressed local payloads
```

Example manifest fragment for the reference trajectory:

```json
{
  "schema": "ARCANA_GEODYN_EXPERIMENTAL_TRAJECTORY_V1",
  "classification": "SYNTHETIC_ENGINEERING_ONLY",
  "authority": "OPERATOR_REPORTED_UNAUTHENTICATED",
  "run_id": "geodyn3run_<sha256-of-path-independent-run-identity>",
  "attempt_id": "attempt-<unique-execution-token>",
  "solver": {
    "name": "ASPECT",
    "version": "3.2.0-pre",
    "source_commit": "30eb77ee5da186137d436dbad35c6cb3cab64b69",
    "build_identity": "UNKNOWN",
    "configuration_sha256": "<sha256>"
  },
  "source_execution": {
    "repository_commit": "1fd5e8d8f21e28876da9ef89423755615efc6162",
    "adapter_commit": "1fd5e8d8f21e28876da9ef89423755615efc6162",
    "input_identities": ["<content-id>"]
  },
  "time": {
    "basis": "SOLVER_NATIVE",
    "unit": "s",
    "solver_completed_time": 1.098612289,
    "last_archived_snapshot_time": 1.0142299266,
    "coverage": "SNAPSHOT_SERIES_ENDS_BEFORE_SOLVER_COMPLETION",
    "unobserved_intervals": "NOT_INFERRED_WITHOUT_DECLARED_OUTPUT_SCHEDULE"
  },
  "completion": {
    "solver_status": "NATURAL_COMPLETION_REPORTED",
    "archive_status": "COMPLETE",
    "snapshot_count": 11
  },
  "mesh_catalog": [],
  "field_catalog": [],
  "snapshots": [],
  "payload_catalog": []
}
```

Angle-bracket placeholders above are explanatory, not valid digests. The real manifest must contain valid values or explicit `UNKNOWN` with an authority/source explanation; a placeholder cannot pass validation.

### Deterministic identity rules

Use versioned canonical JSON with UTF-8, sorted keys, compact separators, finite numbers only, and explicitly defined numeric encodings. Hash formulas are domain-separated so IDs from different record kinds cannot collide semantically:

- `run_id = "geodyn3run_" + SHA256(canonical({schema, solver/build identity, source identity, configuration digest, input content identities, classification, native time basis}))`. Missing authority is represented as explicit `UNKNOWN` plus its source status; it is not silently omitted. This identity excludes machine paths, hostnames and output-directory names.
- `attempt_id` is a unique execution token assigned at launch (or preserved from the source evidence); it distinguishes reruns of the same `run_id`. It is not asserted to be content-deterministic, and it cannot prove owner authority.
- `field_id = "geodyn3field_" + SHA256(canonical({schema, source field key/name, association, dtype, byte order, components, units declaration, semantic provenance}))`. A source label alone is insufficient.
- `mesh_id = "geodyn3mesh_" + SHA256(canonical({mesh algorithm/version, coordinate system, coordinate dtype/order and typed numeric values, connectivity, offsets, cell types, association/order}))`. Keep raw-file hashes separately. The same numeric mesh does not prove the same physical support.
- `snapshot_id = "geodyn3snapshot_" + SHA256(canonical({run_id, attempt_id, source ordinal, original time token, parsed native time/unit, mesh_id, ordered field IDs and payload identities}))`. Do not round, convert units or reorder source records before ID calculation.
- Payload identity is `sha256:<lowercase digest of exact payload bytes>` and is independent of its locator. Record raw VTU/PVTU file SHA separately from typed numeric field/mesh hashes and from any archive payload hash; each digest must name its byte representation and canonicalization version.
- `archive_id = "geodyn3archive_" + SHA256(canonical({schema version, run_id, attempt_id, normalized snapshot/mesh/field/payload-reference index, completion metadata}))`. Exclude `archive_id`, the manifest seal, and machine-specific locators to avoid recursion/path dependence. Resolve external locator identity through a logical namespace plus relative object key; do not hash absolute local paths.
- The seal is `manifest_sha256 = SHA256(exact serialized manifest bytes)` and is not the archive ID. A sidecar stored beside the manifest is only a consistency check; authenticity requires an independently held digest/signature or owner evidence.

R6 `identity.py` provides canonical JSON and path-independent content-ID primitives. Its current `PayloadReference` can retain arbitrary opaque locator strings, and `verify_payload` reads a whole file/stream into memory; GEODYN-3B must validate locators against an explicit trusted root and use bounded streaming hashing for original files. Do not change the shared identity contract for this adapter.

### Time and coverage

Store native solver time exactly as supplied, including source lexical token where available, parsed finite value, unit, unit source, and comparator/representation version. Keep source ordinal and never sort away source order. Version 1 requires finite nondecreasing times; a decreasing source sequence fails qualification as `INVALID_TIME_ORDER`. Equal times remain distinct records keyed by ordinal and make time-only exact queries `AMBIGUOUS`. Interval queries are inclusive at both endpoints and return records sorted by `(native_time_value, source_ordinal)` while retaining original source ordinal.

Exact lookup compares the schema-defined parsed numeric representation for the same run and same native unit; there is no epsilon matching. If callers provide a different unit/time basis, return `INCOMPATIBLE_TIME_BASIS`; no seconds conversion, geological-age conversion, interpolation, extrapolation or inferred event is permitted. Keep `solver_completed_time`, `last_archived_snapshot_time`, and coverage gaps as separate fields. In the fixture, the last of 11 reported snapshots is at 1.0142299266 s and solver completion is reported at 1.098612289 s; do not invent a final snapshot. A missing interval may be asserted only where an expected output schedule or explicit coverage rule defines it; otherwise record coverage as unknown/unobserved.

### Meshes and fields

Each snapshot references its own `mesh_id`, allowing mesh identity to change over time. Mesh records identify coordinates, topology, coordinate system, point/cell counts, cell types and payload references. The fixture has 1152 points and 512 VTK quadrilaterals and is reported numerically mesh-stable; that does not require future runs to use a static mesh.

Field metadata records source name, stable key, point/cell association, VTK/numeric dtype, byte order, component count, tuple count, units and semantic provenance. Units and physical meaning may be `UNKNOWN`. State validity is per snapshot/field (`PRESENT_VALIDATED`, `MISSING`, `INVALID`, `UNKNOWN`). Invariant/dynamic classification and numeric duplicate relationships are archive-level observations over the indexed series, with algorithm and comparison basis; they are not universal field properties. Names such as `density` do not establish scientific meaning. For this fixture, `density` and `density_comp` are reported numerically identical, while `T=0` is reported invariant and its discrepancy from the initial expression is unresolved.

## 4. Retention capability is not restart capability

Every snapshot and payload must state a retention role independently from capability:

| Label | Meaning | Minimum claim |
|---|---|---|
| `VISUALIZATION_ONLY` | Payload can be rendered or inspected. | No claim that it preserves all numeric fields. |
| `OBSERVATION_COMPLETE` | Source snapshot arrays/topology needed to reproduce that stored observation are retained and hash-verified. | Does not imply regeneration of the trajectory. |
| `RECONSTRUCTION_INPUT` | A declared input/dependency needed by a specific reconstruction recipe. | Recipe execution and equivalence must be separately tested. |
| `RESTART_CANDIDATE` | Solver output advertises restart data. | Candidate only; no restart qualification yet. |
| `RESTART_QUALIFIED` | Solver can resume from the saved checkpoint under pinned runtime/config/dependencies and passes a declared continuation-equivalence test. | Exact test scope, solver/build and tolerance must be bound. |

Availability is a separate per-payload property: `AVAILABLE_LOCAL`, `AVAILABLE_EXTERNAL`, `UNAVAILABLE`, `EXPIRED`, or `UNKNOWN`, with check time and resolver namespace where applicable. A payload can be retained by policy but temporarily unavailable, or available without being sufficient to reconstruct a run. Expired/unavailable payloads remain indexed with their identities and status; do not delete metadata silently. Reconstruction is separately `NOT_CLAIMED`, `INPUTS_DECLARED_NOT_EXECUTED`, or `RECONSTRUCTION_VALIDATED` with recipe/runtime/output evidence. The R1 fixture has no qualified restart data and is `RESTART_NOT_AVAILABLE`.

The R1 snapshots are observations, not qualified restart checkpoints. No restart data or checkpoint capability is evidenced. A complete observation archive can still be non-restartable. “Replayable” is not a capability inferred from stored fields; it requires a pinned executable, all inputs and forcing, an explicit recipe, and independently verified output equivalence. The existing `segment_archive.py` explicitly says its reduced observations are `NOT_QUALIFIED_AS_RESTARTABLE`; preserve that distinction.

## 5. Query API proposal and result model

Proposed API is conceptual for a future GEODYN-3B implementation, not a claim about current R6 methods:

```python
archive = ExperimentalTrajectoryArchive.open(manifest_ref, trusted_root=...)
archive.run(run_id)
archive.snapshots(run_id, start_time=0.0, end_time=1.0142299266,
                  time_unit="s")
archive.snapshot_at(run_id, time_value=1.0142299266, time_unit="s")
archive.mesh(mesh_id)
archive.field(snapshot_id, field_id="point:T")
```

`run()` and `mesh()` return metadata and immutable payload refs, not eagerly embedded arrays. `field()` resolves a payload only on request and verifies byte length, raw SHA-256, dtype, byte order, component and tuple counts before returning a bounded typed view/stream. If an API provides in-memory numerical values, it must do so explicitly and enforce the same decoder limits as the ASPECT adapter.

- `snapshots()` filters only in the run's native time basis and declared unit. Cross-unit or cross-run range queries return `INCOMPATIBLE_TIME_BASIS` unless an explicit conversion policy is later separately specified; this contract specifies no conversion.
- `snapshot_at()` requires an exact stored time. If multiple records share that time, return `AMBIGUOUS` with candidate IDs; never choose nearest or interpolate.
- Mesh equality is an explicit identity comparison. A field query requiring a particular mesh returns `INCOMPATIBLE_MESH` when its snapshot references another mesh.
- Queries never resolve unknown field meaning by guessing from field names.

Proposed result statuses: `FOUND`, `MISSING_RUN`, `MISSING_SNAPSHOT`, `MISSING_FIELD`, `MISSING_PAYLOAD`, `ARCHIVE_INCOMPLETE`, `INVALID_TIME_ORDER`, `AMBIGUOUS`, `INCOMPATIBLE_TIME_BASIS`, `INCOMPATIBLE_MESH`, `CORRUPT_MANIFEST`, `CORRUPT_PAYLOAD`, `UNSUPPORTED_FORMAT`, and `UNKNOWN`. Status is explicit; no missing value is substituted. A decreasing source-time sequence fails index qualification with `INVALID_TIME_ORDER`; it is not repaired by sorting.

| Condition | Result |
|---|---|
| Run, exact snapshot/time, field or referenced payload absent | Corresponding `MISSING_*` status |
| Multiple snapshots match an exact-time query | `AMBIGUOUS`, with all candidate snapshot IDs |
| Query crosses declared time bases or requires an unbound mesh | `INCOMPATIBLE_TIME_BASIS` or `INCOMPATIBLE_MESH` |
| Required data belong to an unfinalized/partial attempt | `ARCHIVE_INCOMPLETE` |
| Manifest schema, seal or internal references inconsistent | `CORRUPT_MANIFEST` |
| Payload length, digest, typed shape or decoding disagrees | `CORRUPT_PAYLOAD` |
| File encoding or archive schema version not implemented | `UNSUPPORTED_FORMAT` |
| Requested scientific meaning/unit is not established | Metadata remains `UNKNOWN`; never infer from the field name |

## 6. Integrity, storage and immutability

- Manifest schema and canonical serialization are versioned. Seal exact manifest bytes with a sidecar digest or content identity. A manifest digest detects changes only when the expected digest is held independently; a self-written sidecar is not authentication.
- Finalization is allowed only after every declared snapshot, mesh, field, payload size and hash has been checked and all required snapshot references resolve. Before finalization, the attempt is `INCOMPLETE`; interrupted archives remain queryable only as explicitly partial evidence and cannot report `COMPLETE`.
- Reject absolute local paths in identity data; reject `..`, root escapes, symlinks/reparse points and references that resolve outside a declared root. Recheck resolved paths at open/read boundaries. External object stores require a declared resolver/namespace and immutable object-version or content-addressed semantics.
- Hash every payload on ingest and verify again on read, or rely on an independently verified immutable content-addressed backend with a documented integrity check. Record stored and logical byte counts by payload category. Do not copy the full VTU arrays into JSON manifests.
- Any post-seal manifest or payload mutation causes integrity failure. Do not claim atomicity, fsync durability, access control, tamper-proofing or write-once storage until implemented and tested on the selected backend.
- Experimental archive roots and identifiers are segregated from `WORLD_HISTORY`. No experimental size is charged to or promoted into canonical storage by default. Retention/deletion policy must be explicit and preserve externally governed evidence; content-addressed deduplication must not imply shared scientific authority.

### Incomplete attempts and recovery

- A process interrupted before a sealed manifest is written leaves `archive_status=INCOMPLETE`, with any known member references and validation errors recorded in a partial index/sidecar. Readers may list partial metadata only when explicitly asked; numerical queries return `ARCHIVE_INCOMPLETE` unless the caller explicitly requests partial inspection.
- Recovery never edits or deletes the partial attempt. A recovery tool creates a new archive generation/ID with `recovered_from_archive_id`, rescans the pinned source root, rehashes every declared source and payload, rebuilds the full index and seals only if all required references and counts validate. The original partial record remains immutable.
- If any required source file is absent, changed, unsafe, or mismatched, the recovered generation remains incomplete and reports the specific cause. Reusing an attempt token does not turn recovery into a new solver execution; no numerical continuation is implied.
- A sealed archive that later fails verification is `CORRUPT_*`; recovery creates a new generation and never rewrites the old seal. File-level atomicity, fsync durability and rollback are not claimed by the schema alone.

## 7. GEODYN-2A-R1 reference fixture and limits

Reference values are the operator-reported FAIR qualification, not independently imported Windows evidence:

| Property | Reported observation |
|---|---|
| Snapshots | 11, model time from 0 to 1.0142299266 s |
| Solver completion | 1.098612289 s; no matching terminal snapshot |
| Mesh | 1152 points, 512 VTK quadrilaterals, numerically stable across the series |
| Fields | Nine point fields; schema reported stable |
| Duplicates | `density` and `density_comp` numerically identical |
| Temperature | `T` observed constant at zero; discrepancy with initial expression unresolved |
| Restart | No qualified restart checkpoint |
| Classification | `SYNTHETIC_ENGINEERING_ONLY`; operator-reported provenance where not authenticated |

The adapter's currently qualified parser scope is limited to PVD part 0, one rank, one VTU Piece or one PVTU Piece source, inline ASCII or Base64 binary, uncompressed payloads or VTK zlib blocks, supported UInt32/UInt64 headers and declared byte order. Appended data, multipiece/multirank layouts and unsupported encodings/compressors remain rejected. Its current PVD parser requires strictly increasing snapshot times; the generic schema's equal-time ambiguity behavior is a broader contract and must be tested with non-ASPECT fixtures unless adapter support is separately qualified. Reader limits are software guardrails, not OS memory quotas. The adapter does not establish units or field semantics, authenticate operator provenance, create checkpoints, or establish ARCANA support correspondence.

## 8. GEODYN-3B MVP boundary and public API

GEODYN-3B is limited to a **read-only registration/index of the existing R1 ASPECT series**, not a new storage framework:

1. Accept an explicitly configured trusted source root and relative PVD reference; reject absolute, traversal, symlink/reparse and escaping references. Do not scan outside that root.
2. Use the qualified `AspectSnapshotSeries` reader to inspect and index the existing 11 snapshots. Stream-hash PVD/PVTU/VTU source bytes and store their root-relative references, sizes and hashes; do not copy the original VTU files or embed arrays in JSON. Fail if the source is unavailable or does not match the supplied R1 inventory; no fixture fallback.
3. Register exact native times, source ordinals, per-snapshot mesh/field identities, solver completion time separately from the last archived time, and the existing operator-reported authority/classification status. Record `density`/`density_comp` and invariant/dynamic observations only as measured comparison metadata; retain the unresolved `T=0` interpretation.
4. Expose metadata queries without reading arrays. Numeric field access is on demand for a requested snapshot/field and delegates to the already qualified adapter under its `ReaderLimits`. The current reader decodes/materializes all arrays for one requested snapshot before selecting the field; GEODYN-3B must state this memory behavior and must not claim field-selective disk decoding.
5. Verify the manifest seal, all referenced source-file sizes/hashes, path safety, payload identities and internal references on audit/open. Index data are written to a new experimental location; source files remain read-only. Do not use `HistoryStore`, `DomainStateEnvelope`, or `WORLD_HISTORY`.

Proposed public API (names/signatures for GEODYN-3B implementation; none exist yet):

```python
index_existing_aspect_series(
    *, trusted_source_root: Path,
    pvd_relative_ref: str,
    run_identity: RunIdentityClaim,
    expected_source_inventory: Mapping[str, SourceDigest],
    output_index_root: Path,
) -> IndexBuildResult

archive = ExperimentalTrajectoryArchive.open(
    index_ref: str, *, trusted_index_root: Path,
    trusted_source_roots: Mapping[str, Path],
)
archive.verify_integrity() -> IntegrityReport
archive.get_run(run_id: str) -> RunMetadataResult
archive.query_snapshots(
    run_id: str, *, start: NativeTime | None = None,
    end: NativeTime | None = None,
) -> SnapshotListResult
archive.get_snapshot_at(run_id: str, time: NativeTime) -> SnapshotResult
archive.get_mesh(mesh_id: str) -> MeshMetadataResult
archive.get_field(snapshot_id: str, field_id: str) -> FieldReadResult
```

All return explicit status-bearing records. `NativeTime` includes numeric value, exact source token when available, unit and time-basis ID. `get_field` first verifies referenced source VTU hash and then uses `AspectSnapshotSeries.read_snapshot(ordinal)`; it returns the selected field values plus association/dtype/components/units/provenance and does not claim semantic interpretation. `SourceDigest` includes a relative source reference, byte length and raw SHA256. `IndexBuildResult` separates `COMPLETE`, `INCOMPLETE` and `FAILED`; only complete results expose ordinary exact queries.

GEODYN-3B acceptance tests:

- Path-independent, stable run/archive/mesh/snapshot/field IDs and exact payload digests across two different mount roots for the same source bytes; locator strings themselves differ but do not change IDs.
- Read-only registration of exactly 11 source snapshots, 0 through 1.0142299266 s; `solver_completed_time=1.098612289 s` is distinct and no terminal snapshot is synthesized. Source order is preserved and invalid order rejected.
- Exact-time hit, absent-time status, inclusive native-unit interval query, duplicate-time ambiguity, wrong-unit rejection, field lookup, mesh lookup, and changed-mesh handling.
- All original-file hashes and byte lengths match the supplied inventory; no VTU bytes copied into the index root. Query-time payload hash mismatch, missing file, changed file, corrupt index, incomplete archive and unsupported source format fail closed.
- Traversal, symlink/reparse escape, source-root substitution, and post-seal index mutation are rejected. Raw parser data are decoded only on requested snapshot access under reader limits.
- Exact field dtype/association/components/tuple count are returned. No `DomainStateEnvelope`, `HistoryStore`, geological-time conversion, interpolation, resource/Deep/surface output, restart or forward solver call occurs.

The 11-snapshot numeric comparison against the independent R1 audit remains a GEODYN-3C qualification gate. GEODYN-3B's synthetic tests are not a replacement for availability of the original FAIR source files.

## 9. Qualification gates and next bounded phases

### GEODYN-3A — contract ratified

Acceptance: six R6 interfaces audited; missing deterministic archive identity, time-order semantics, payload availability, recovery behavior and GEODYN-3B API/test scope are now specified. Ratification authorizes only the experimental, read-only GEODYN-3B MVP defined above; it is not canonical promotion or physical execution authorization.

### GEODYN-3B — minimal experimental index/reader implementation

Implement only the read-only ASPECT registration/index and query MVP in §8, reusing `identity.py` canonical bytes/content hashes and payload verification concepts where their semantics fit. Tests start synthetic but the registration path must verify the existing 11-file series when available. Store no arrays in manifests and do not copy original VTUs. Prove no code path constructs a `DomainStateEnvelope` or accesses `WORLD_HISTORY`. Do not claim reconstruction, restart or replay.

### GEODYN-3C — existing-trajectory qualification

Only after 3B review and an exact implementation revision, validate an archive/index view against the existing R1 trajectory and independent audit. Preserve raw evidence outside Git; record which payload bytes were actually available and independently hashed. Check all 11 snapshots, native times, per-snapshot mesh/schema, field associations/types/components and payload references, including the reported tail without a terminal snapshot. Keep `T=0` semantics unresolved and the rigid-shear dataset experimental. This is archive qualification, not an ARCANA forward run.

GEODYN-3B/3C do not authorize ASPECT execution, FAIR jobs, geological-time conversion, resource creation, remapping, surface/Deep coupling or canonical publication. The ARCANA forward problem remains blocked until initial conditions, constitutive laws, boundary conditions, spatial mapping and time-dependent forcing are established.
