# R6-INT10K E2 — Frontier and Historical Stream Contract

**Status:** `E2_A1_FULL_HISTORY_ORACLE_WINDOWS_PASS__STREAMING_AND_LINUX_FAIR_PENDING`
**Scaling policy:** `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS`
**Prepared:** 2026-10-29
**Reference:** E1 short-reference source commit `5faf619875af86caa2ee824dff4b0a833f4227f1`; reported 3- and 10-year FAIR outcomes were not imported or independently hashed on Windows.

## 1. Purpose and boundary

E2 separates bounded continuation state from queryable history so retained execution memory need not grow with elapsed history. This is a storage/continuation contract, not a new physical model. Existing kernels, forcing, parameters, annual regional step, unified external timestep, E0 source identity and input bytes remain unchanged. This document prepares design and implementation only; it does not authorize numerical runs, scientific promotion, or canonical writes.

Scaling measurements are observational. E2 code MUST NOT impose arbitrary wall-time, RAM, output-size, checkpoint-size, record-count, or history-truncation caps on benchmarks. It records actual scaling and allows the process to complete naturally unless an actual FAIR administrator, scheduler, OS allocation, or site policy acts. This does not declare unknown allocations unlimited, bypass site rules, or relax fail-closed numerical, integrity, and state invariants. The execution configuration must state `OBSERVE_ONLY` and identify actual environment allocations/policies as known or `UNKNOWN`; legacy budget fields cannot silently imply enforcement or be reused without an explicit mode.

All artifacts remain `NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY`. Hashes establish byte integrity and linkage, not producer authenticity or scientific authority.

## 2. Source-grounded consumers

Existing histories have live consumers and cannot be discarded until those consumers use the archive API.

| Source/API | Current dependency found in source | E2 preservation requirement |
|---|---|---|
| `regional_geological_evolution.py:create_initial_state`, `run_regional_segment` | Initial `snapshots` contains year 0; each annual advance appends a full cell snapshot and one record. Records include events, routing before/after geomorphology, depression storage, geologic loads, and global/per-cell water and solid balances. | Persist snapshots for 0..N and records for 1..N, with every currently emitted field and stable cell/material identity. |
| `query_materials_at_time` | Exact snapshot lookup; absent time raises `TIME_NOT_ARCHIVED`; returns substrate, cover, suspended sediment and deposits. | Preserve exact-time queries and missing-time result; never interpolate. |
| `query_material_provenance` | Scans events in all regional records. | Keep event identity, material, origin, transfer, destination, time and parent-record reference queryable. |
| `query_deep_inventory` | Reads unified checkpoint records at exact elapsed year; year 0 comes from run configuration; absent time raises `TIME_NOT_ARCHIVED`. | Archive time-indexed Deep inventory records; frontier alone cannot answer historical queries. |
| `seal_regional_checkpoint` / `verify_regional_checkpoint` | Hashes canonicalized regional state, including records and snapshots, and unified checkpoint; verification detects changes and checks source identity, but is not an authenticated signature. | Replace embedded histories with a bounded frontier plus committed archive high-water mark; retain identity/config checks and corruption detection. |
| Regional resume | `run_regional_segment` checks source identity/configuration and restores regional plus unified state. | Resume only from a complete transaction whose frontier, chain, source, config and coverage agree. |
| `unified_multiphysics_microdomain.py` resume/result | Resume copies `saved["records"]`; each external step appends thermal, mechanics, surface, hydrology, material-flow, Deep and balance diagnostics. Checkpoint embeds records; result exposes them as `steps`. | Stream each existing step record unchanged; keep only dynamic state and bounded online accumulators in the frontier. |
| Unified summary consumers | Aggregations scan history for Deep transport/minimum stock, mechanical residuals/work, flows and diagnostics. | Replace scans with online accumulators only after their update rules reproduce legacy summaries exactly. Retain queryable source records. |
| `int10k_short_reference.run_short_reference` | Compares full regional state, unified final state and domain balances; numerical tolerance `abs=1e-8`, `rel=2e-14`; metadata/events exact. | Extend parity to all unified step records, checkpoint frontiers, accumulators and historical query results. |

### E1 reference coverage gap

The serialized E1 reference includes the full regional state, unified final state and aggregate domain balances for direct and split paths. It does not serialize unified per-step `steps` or the internal checkpoint/frontier at the split boundary. Therefore the reported endpoint/direct-split PASS is not full-history parity. Before E2 claims full parity, obtain a bounded reference containing those missing objects, or compare against a deterministic rerun with the same source/config/input identity under separate authorization. This is an evidence requirement, not permission for longer runs.

### Required E1 oracle extension

Extend the reference artifact to a versioned oracle bundle without changing E1's numerical configuration or source pins. For each direct and split case, record: exact run/source/config/input identities; all unified step records in execution order; all regional snapshots, annual records, events and per-cell/global balances; final states and cumulative summaries; and the complete restart checkpoint/frontier immediately after year 1 (3-year split) or year 5 (10-year split). Store payloads with explicit schemas, units, sizes and hashes; a compact index may point to immutable payload files. The direct run has no artificial split checkpoint; record that absence explicitly. Verify exact temporal coverage and query results. The checkpoint oracle must be captured from the genuine E1 implementation, not reconstructed from the final state. Keep the original E1 outputs immutable; this is a separate bounded reference capture requiring its own execution authorization if existing FAIR evidence does not already contain these objects.

The E2 comparison consumes this oracle symmetrically for continuous and resumed runs. Compare record types/order/counts, each field with the declared E1 numeric policy where already applicable, exact metadata/event/material IDs, checkpoint restoration inputs, final accumulators, water/solid/geometry/Deep/mechanical balances, and exact-time/range/spatial query responses. A final-state-only digest is insufficient.

## 3. Logical products and records

Keep these products distinct:

1. **Continuation frontier:** bounded current dynamic state, independent of history length.
2. **Append-only history:** immutable snapshots, annual/step records, events, material flows and balances indexed by sequence and native time.
3. **Checkpoint envelope:** versioned restorable frontier bound to a committed-history high-water mark and chain root.
4. **Commit envelope:** atomic visibility point for a history chunk and its matching checkpoint.
5. **Derived indexes:** rebuildable sequence/time/cell/support/event/material indexes; indexes never outrank immutable payloads.

Proposed schema IDs, not yet implemented:

```text
ARCANA_R6_INT10K_FRONTIER_V2
ARCANA_R6_INT10K_HISTORY_SEGMENT_V1
ARCANA_R6_INT10K_CHECKPOINT_V2
ARCANA_R6_INT10K_SEGMENT_COMMIT_V1
```

Each object binds run/attempt IDs, exact source identity, E0 input identities, canonical numerical-configuration identity, schema/algorithm versions, native time convention/unit, step plan and expected duration. Logical identities exclude absolute paths; paths are locators only.

### 3.1 Continuation frontier

The frontier contains only data required to continue without hidden reinitialization. “Bounded” means independent of prior history length, not subject to an arbitrary byte limit:

- Run/attempt, source/config/input identities and schema versions.
- Current time, external-step ordinal, planned-step count and next regional/unified record sequences.
- Current thermal `ReducedState` payloads per support; initial-state digests remain bound for validation.
- Maxwell reference geometry, viscous/total strain memory, opening, prior displacement/interface gap and stored elastic energy.
- Current surface-cell state: topography, water/depression storage, cover, suspended material, stratified deposits, material identities and provenance.
- Deep inventories, accessibility and volume IDs; material changes do not create Deep energy.
- Initial inventories/configuration required for existing cumulative ledgers and tolerances.
- Bounded cumulative accumulators for water, sediment, substrate, geometry, Deep transfer/residual, mechanical work/energy/dissipation and existing summaries, each with a specified update rule and reduction order.
- Last committed history sequence/time and commit-chain digest.

It MUST NOT contain previous `records`, `snapshots`, `steps`, event arrays, or any duration-growing list. It may hold immutable input references/digests, not duplicated trajectories.

### 3.2 Append-only history

Preserve all current externally observable records:

- `REGIONAL_SNAPSHOT`: year 0 through N, complete cell state and stable cell/material identities.
- `REGIONAL_YEAR_RECORD`: year 1 through N, events, routing before/after, depression storage, loads, and current per-cell/global water and solid balances.
- `UNIFIED_STEP_RECORD`: every completed external step, preserving existing `steps` content and exact support/time associations.
- `EVENT`: material/routing/connectivity event linked to its parent record.
- `BALANCE_RECORD`: existing component/global values, residuals and configured tolerances.

Each record carries monotonic sequence, record schema/type, native time and interval, support/cell/material identities, source/config identity and payload SHA256. Coverage metadata must be queryable without loading all record bodies.

The archive is intended to support a reconstructible WorldSim history across geology, hydrology, natural resources, Deep, materials, fauna, flora and later civilizations. These are domain categories for future records, not a claim that current E1/E2 inputs or kernels provide them. Each domain declares spatial/temporal coverage, resolution, units, provenance, authority, and `UNKNOWN`/unavailable fields. No domain is fabricated to fill a gap.

Lossless compression is permitted only when decoding reproduces the exact logical bytes/typed values required by the declared representation. Record both the uncompressed logical payload digest and stored-object digest, codec/version/parameters, and uncompressed/stored byte counts. Lossy compression, silent downsampling, omitted reconstruction state, or implicit interpolation is prohibited. A query must disclose whether data are full-resolution, compressed losslessly, unavailable, or covered only at a coarser declared resolution.

## 4. Checkpoint and atomic commit

A checkpoint is restorable only when its version is supported, digest verifies, source/config/input/run identities match, dynamic-state invariants pass, and its high-water mark names a complete valid commit-chain prefix. A snapshot is not automatically a restart point.

For each transaction:

1. Write history chunk and frontier/checkpoint to unique temporary names; never overwrite a committed object.
2. Close and flush files; where supported, sync file data and containing directory. Hash closed bytes and validate record counts, sequence/time continuity and existing ledger invariants.
3. Write a commit envelope naming the prior commit digest, chunk/checkpoint digests, first/last sequences and times, record counts, source/config identity and cumulative coverage. Publish it atomically (same-filesystem atomic rename or an explicitly documented equivalent). This is the visibility point.
4. Update convenience manifest/index atomically from the committed chain. It can be rebuilt; it cannot include uncommitted data.

Interrupted pre-commit objects remain uncommitted and ignored, preserved for diagnosis. If commit publication succeeds but index refresh does not, rebuild the index from the chain. Missing/corrupt chunk or checkpoint invalidates that commit; resume only from the last complete valid transaction, otherwise stop with recovery required. Never truncate or overwrite committed history. If a chunk and matching frontier cannot be exposed atomically through the commit envelope, fail closed.

Hashes detect accidental corruption and inconsistency, not producer identity. Owner-authenticated signatures are outside E2.

## 5. Query and replay contract

Proposed APIs (names are design proposals, not existing interfaces):

```python
archive.coverage() -> Coverage
archive.query_snapshot(time_year, *, cell_id=None) -> SnapshotResult
archive.query_records(start_sequence, end_sequence, *, record_type=None) -> Iterator[HistoryRecord]
archive.query_time_range(start_time, end_time, *, record_type=None) -> Iterator[HistoryRecord]
archive.query_spatial_time(start_time, end_time, *, support_ids=None, cell_ids=None, domain=None) -> Iterator[HistoryRecord]
archive.query_events(start_time, end_time, *, material_id=None) -> Iterator[Event]
archive.audit_integrity() -> IntegrityReport
archive.load_checkpoint(checkpoint_id, *, expected_source, expected_config) -> ContinuationFrontier
```

Regional time is the exact integer year; unified time is its existing numeric value with declared unit. No geological-age conversion is defined. Spatial queries require stable support/cell/mesh IDs and declared coordinate frames; no remapping is implied. Queries never interpolate/extrapolate and report actual temporal and spatial coverage, resolution, and missing spans. Explicit outcomes include `NOT_ARCHIVED`, `COVERAGE_GAP`, `FIELD_NOT_RECORDED`, `CORRUPT_PAYLOAD`, `INCOMPATIBLE_IDENTITY` and `CHECKPOINT_UNAVAILABLE`.

Replay means rerunning unchanged operators from an eligible checkpoint with exact bound source/config/input identity, then comparing emitted history and frontier. It cannot return archived expected values as computed output. Diagnostic snapshots are not implicitly restartable.

## 6. Invariants and fail-closed rules

- Regional records cover exactly years 1..N; snapshots cover 0..N; final regional time is N.
- Unified steps have unique monotonic ordinals and contiguous non-overlapping intervals matching the existing fixed step plan.
- A commit extends exactly one valid prior chain head without duplicate/skipped record sequences.
- Source, config, E0 inputs and run/attempt identity cannot change within a resumed run; a change starts a new run.
- Frontier time/ordinal/high-water mark agrees with latest committed records and checkpoint envelope.
- State and balance values are finite; material/water stocks obey existing invariants and residuals use existing configured tolerances. E2 adds no looser tolerance.
- Events reference valid records and stable identities; no query bridges a gap or creates a state.
- Missing/corrupt chunks, unsupported versions, ambiguous recovery, duplicate sequence, invalid digest or changed source/config means no success and no resume beyond the last valid commit.
- Failed/incomplete runs remain incomplete. A complete manifest is emitted only after every declared trajectory/step and final balance is committed and verified.

E1-R2 operator-reported 10-year diagnostics: water balance PASS; maximum absolute solid residual `0.00048828125 kg` within `0.03125 kg`; Deep total residual `0 J`; gross internal transport `38,795,203,049.11111 J`. These observations do not set new tolerances. Detailed 3-year residuals were not supplied.

## 7. Scaling observability policy

The benchmark policy is `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS`. The harness collects measurements and does not kill, truncate, or reject a run because an internally selected wall-time, RAM, output-byte, checkpoint-size, sample-count or record-count threshold was crossed. Natural completion, a solver/invariant failure, an observed system/site termination, and incomplete telemetry are distinct outcomes. Actual FAIR policy and allocated resources remain binding; absence of a reported quota is `UNKNOWN`, never “unlimited.” Before a future run, read-only preflight records what allocation/scheduler/cgroup/quota information is available and its scope. Do not install monitors or request privileged changes as part of E2.

Telemetry requirements:

| Metric | Collection and interpretation |
|---|---|
| Wall time | Monotonic start/end and per-phase durations; report process and internal kernel timings separately. |
| CPU time | Per-process user/system CPU and process-tree totals where available, keyed by PID plus process start identity; report collection gaps. |
| RSS/memory | Sample each second by default; save timestamp and process identity for each live process, per-process RSS and sampled summed process-tree RSS/peak. Summed RSS can double-count shared pages and is not unique physical memory. Record OS peak/available memory separately when supported. |
| Allocated memory | Optional Python `tracemalloc` current/peak and allocator/native-memory counters when available. Identify that NumPy/native allocations may not be visible to `tracemalloc`; record whether telemetry was enabled and its overhead. RSS remains the process observation, not a quota. |
| Process tree | PID, parent PID, process group/session, start ticks or platform identity, state and exit status. PID reuse must not join unrelated process samples. |
| I/O and storage | Sample process-tree read/write byte counters when exposed; record bytes/files written by transaction and final output-tree logical bytes. Record allocated filesystem blocks/free space/quota only if the system exposes them and scope is clear. |
| Checkpoint | Serialize and restore wall durations, payload bytes, component sizes, record high-water mark and hash-verification duration for each checkpoint. No size ceiling is imposed by this contract. |
| History/throughput | Per transaction and total counts of records, events, snapshots and years; bytes/sec, records/sec, events/sec, snapshots/sec, simulated years/sec, wall seconds per simulated year, and mean/median step cost. Preserve exact observed sample interval and missing-sample count. |
| Telemetry overhead | Record sampling cadence (initial default 1 s), monitoring thread/process CPU and bytes if measurable, and any dropped/error samples. Keep data collection lightweight; compare instrumented overhead in a bounded diagnostic check before interpreting small timing differences. |

Resource snapshots are observational, not active limits. A sampling error does not stop healthy numerical computation by an invented resource threshold, but the run's resource report becomes `OBSERVABILITY_INCOMPLETE` and cannot claim complete telemetry. A real scheduler/OS termination leaves an incomplete run with partial committed evidence preserved; no final-complete marker is written. Conservation, non-finite values, identity mismatch, data corruption and violated state invariants remain fail-closed regardless of resource policy.

Progression after archive and short-parity qualification is a sequence of separately reviewed measurements at 100, 1,000 and 10,000 years. At each scale, record actual resources and integrity; do not extrapolate completion, memory, output size, or scientific validity from the preceding scale. No such execution is part of this document task.

## 8. Acceptance criteria

No criterion here is claimed passed.

1. Run the existing 3-year direct/split 1+2 and 10-year 5+5 configurations with unchanged source, inputs, physics and timestep; compare final frontier, every regional snapshot/year record/event/balance, every unified step record, accumulators and query results. Use E1 `abs=1e-8`, `rel=2e-14` only for already-covered numeric fields; record ordering, identities, times, coverage and event metadata must match exactly. Keep existing physical-ledger tolerances.
2. Capture and verify each split-boundary checkpoint/frontier; restore it and show continuous/split equality without hidden reinitialization, loss or duplication.
3. Query every regional year including 0, material provenance chain, unified elapsed step/Deep inventory and balance; compare to reference. Missing times and gaps return explicit statuses.
4. Fault-inject interruption during chunk write, after chunk/checkpoint, during commit publication, and after commit before index refresh; corrupt/remove/truncate/reorder/duplicate objects. Only the last valid committed prefix is visible or resumable.
5. Reject changed E0/source/config/run identity, unsupported schema, frontier/high-water mismatch and resume from diagnostic-only snapshots. Keep historical E1 outputs readable.
6. Demonstrate frontier/checkpoint serialized size independent of history length up to bounded accumulators and stream/query history without loading every body into RAM. Record actual growth rather than enforcing an arbitrary resource ceiling.
7. Verify manifest inventory, byte counts, SHA256, coverage, counts and provenance; preserve E1 evidence unchanged.

Full-history parity is blocked until unified-step and split-checkpoint reference objects are preserved or regenerated under the same identity with separate bounded-run authorization.

## 9. Incremental roadmap

- **E2-A — this document:** source consumer audit and contract. Prepared; no code or simulation.
- **E2-B:** bounded typed frontier v2, canonical identity and versioned checkpoint serializer; fail-closed restore tests.
- **E2-C:** append-only regional snapshot/year/event/balance writer and exact query reader; preserve current query semantics and legacy compatibility.
- **E2-D:** stream unified step records and add online accumulators cross-checked against legacy summaries.
- **E2-E:** transaction/commit chain, atomic visibility, recovery and corruption fault injection.
- **E2-F:** join regional and unified streams under one run/source/config commit.
- **E2-G:** separately authorized 3/10-year parity and resource measurement. After qualification, plan and review distinct 100-, 1,000- and 10,000-year observe-only measurements; no automatic extrapolation or execution authorization.

Reuse R6 source/config identity and canonicalization primitives, Segment Archive V1 patterns when compatible, and existing query/error semantics. Do not create a second canonical `HistoryStore`, weaken checkpoint validation, or rewrite historical evidence.

## 10. Decision and gates

E1-R2 results are operator-reported at exact source commit `5faf619875af86caa2ee824dff4b0a833f4227f1`: 45/45 Linux regressions, E0 loader/input/source identity, and 3-/10-year references PASS. FAIR artifacts were not imported or independently hashed on Windows. The earlier E1 24-pass/2-fail attempt and prior R1 results remain unchanged. E2 is a contract only: no streaming implementation or numerical evolution was performed for it.

Next: close the reference-coverage gap, then implement E2-B onward in bounded steps. No 100-, 1,000- or 10,000-year run is authorized.

`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`

`GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`

`INT10K_LONG_RUN_AUTHORIZED=false`

## 11. E2-A1 full-history oracle implementation addendum (2026-10-29)

The separate `FULL_HISTORY_ORACLE_V1` implementation is recorded in
`docs/arcana/R6_INT10K_E2_A1_FULL_HISTORY_ORACLE_IMPLEMENTATION.md`. It captures
the complete raw direct result, actual split-prefix result/checkpoint, and
resumed full result from existing regional/unified operators. Its local 3-year
1+2 and 10-year 5+5 captures passed full direct/resumed comparison and manifest
verification on Python 3.12.10 / NumPy 2.5.1; FAIR E1 used reported NumPy 2.3.5,
and its serialized result was not imported for byte comparison. The oracle is
still an in-memory reference with duplicated histories: it is not an E2
streaming archive, bounded continuation frontier, or Linux-qualified runtime.
The synthetic adversarial and pertinent regressions passed locally. The exact
implementation commit still requires Linux qualification. E2-B through E2-G
and all resource progression gates remain pending; no long-run authorization
or scientific/canonical promotion follows.

## 12. E2-A1 FAIR report and E2-B frontier projection (2026-10-29)

The operator reports E2-A1 qualification on exact source commit
`57768923a4a8478381d9153c6f910fba811613d2`, with Python 3.12.14, NumPy 2.5.3,
pytest 9.1.1, 60/60 Linux tests, original 3Y and 10Y oracle/checkpoint/query
checks PASS and `FINAL_EXIT=0`. Reported FAIR oracle/manifest SHA256 pairs are
3Y `6052e8cd222141a41276bf1b041aeec89fd6a7aac52b8628a5d263867098eeb1` /
`a6ca3b7db7e9aa1d08569e79bb0215aa8679217de5523ebdc7caf15da9744040`, and 10Y
`7f060bd5d2b920abf18685a38d4eb25eb8792733fb50ac128775842014ca8798` /
`0ff8b1e4a8eec93960a3551fbc8b0145c5561e1740c723fdb2641b6ed54e9c02`. These are
operator-reported; FAIR files were not imported/rehashed on Windows. See the
E2-A1 report for provenance separation.

E2-B local projection work is recorded in
`docs/arcana/R6_INT10K_E2_B_FRONTIER_CHECKPOINT_IMPLEMENTATION.md`. It removes
duration-growing regional histories and unified step records from the v2
frontier/checkpoint envelope and records a high-water mark, E0/source/config
identities, SHA256 integrity and an explicit not-implemented commit-chain
reference. A compatibility restore must receive the complete separate history
prefix because the existing continuation runner consumes it. Actual local 3Y
and 10Y restored continuations matched the complete E2-A1 Windows reference.
Dynamic stratified deposits also grow and remain state-bearing frontier data;
the observed sizes are reported without claiming history-independent size.
No append-only transaction chain, streaming, recovery, indexed on-disk query,
or Linux qualification is implemented. E2-B remains partial until the engine
can resume from a frontier without loading the full prior history and that
change passes exact-commit Linux tests. Scientific, canonical and long-run
gates remain false.
