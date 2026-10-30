# ARCANA R6 E2-C2-B2-B — proposed typed lossless HistoryStore ingestion, order and atomicity contract

**Date:** 2026-10-30. **Decision state:** `DRAFT_DESIGN__NO_PERSISTENT_INGESTION_AUTHORIZED`. B2-A has PASS on the original 61,001-event history SHA; A3 and B1 have PASS on 1,001 regional snapshots and virtual deltas. This file sets technical acceptance criteria; it does NOT claim B2-B has been implemented, benchmarked, committed or run.

## Goal

Build a persistent, immutable, queryable, space-efficient ARCANA history preserving all represented time/space/resource/geological/Deep/environmental/historical events, provenance and uncertainty. Never collapse ARCANA WorldSim into a population-only archive. Original noncanonical 3×3 history is qualification fixture; absence of flora, fauna, culture or human migration in the fixture must be represented as absent/UNKNOWN, not invented.

## Source code API constraints (inspected read-only)

Repository source at published geometry parent `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839` (the FAIR-only E2-C1-R3 child changes regional frontier projection and tests, not these B0 modules).

| Existing API | Concrete verified behavior | Required B2-B boundary |
|---|---|---|
| `HistoryStore.append_transaction(records, expected_parent_view_id=...)` | Writes only typed objects (DomainStateEnvelope, ProvenanceRecord, EventRecord, CheckpointEnvelope, RefinementBranchEnvelope, ForcingRecord, ReplayRecipe, RefinementReconstructionRecipe, TemporalRecord); validates content IDs; immutable records; publishes committed read-view atomically via CURRENT.json | No arbitrary dict as transaction member. One complete annual *logical* bundle per committed visibility version, with explicit parent view identity and rollback/recovery negative tests |
| `HistoryStore.read_view()` | Pinned immutable read membership for a complete logical query | Read never mixes partially published annual material, Deep, event or delta records |
| `HistoryStore._view_material` and `_write_view_manifest` | Regenerates sorted **full record-membership lists** in a content-hashed view manifest at every transaction | Incremental per-event ingest may amplify metadata and wall time. Benchmark explicit per-year bundle count and O(N) view serialization; avoid claiming B1 99.49% savings for the persistent store |
| `TemporalRecord.create` | Content ID with history_id, branch_id, time_key, domain_ids/state_ids, authority_refs, provenance_refs, details | Candidate carrier for opaque year bundle and parent/source manifest metadata (subject to exact size query tests) |
| `EventRecord.create` | Adds causal support and event_contract, and receives its own typed record_id | If materialized for native `events()`/event_at, retain `source_sequence`, `source_time_year` (possibly null) and `source_payload_sha256` separately; typed ID is not source ID |
| `DomainStateEnvelope.create` | Requires explicit TimeSupport, SpatialSupport, SupportClass and AuthorityClass; UNKNOWN / OUTSIDE_SCOPE / NOT_APPLICABLE cannot carry value | SOURCE-FIXTURE-only authority, no inferred human/biology or new physical time for null-timed event |
| `HistoryQueryService.event_at` | Filters by history_id/branch_id/time_key and causal_phase=EVENT, **sorts by record_id string**, not original `sequence` | Do not represent its result as original chronological event order. A new sequence-aware retrieval adapter is required (or rigorously reviewed B0 API change) |
| `PayloadReference` / `verify_payload` | Can verify SHA256-backed content refs | Bind exact *source* payload hash and reconstructed payload canonical hash; reference must resolve to committed accessible material, not a noncommitted external orphan |
| `MinimalStateContract` and `HistoryQueryService.state_at` | Retention classification and support statuses are enforced | No SYSTEM_MEMORY DISCARD; DERIVE must resolve dependencies; unknown remains UNKNOWN and missing/outside statuses never upgraded silently |

## Complete source representation: no semantic loss

The original INDEX is a 61,001-row global order authority: keys `kind,length,offset,payload_sha256,sequence,time_year`, with 1,001 REGIONAL_SNAPSHOT, 1,000 REGIONAL_YEAR_RECORD, 1,000 UNIFIED_STEP and 58,000 REGIONAL_EVENT. History member raw SHA256 passed B2-A. Source envelope keys `kind,payload,payload_sha256,sequence,time_year`. All representations must retain source `sequence` exactly, independently of B0-assigned record IDs.

For every Y>0:
- Initial **Y0 snapshot** retained once with nine complete cells, static fields and explicit UNKNOWN statuses; authentic original hash.
- **Regional yearly delta**: `cell_id`, cell-order index, `set` of *full original values* for **all** non-deposit changes (never numerical rounded differences), `append_deposits` with all nine keys, order, event_id, mass/density and source/destination/times. Store `parent_snapshot_sha256`, `target_snapshot_sha256`, `source_original_sequence`, `year`, `history_id/branch_id`, parent delta ID/hash. Do not drop a non-deposit field because it is not in current example fixture.
- **REGIONAL_YEAR_RECORD**: full other fields, including water/solid balances, geologic loads, routing targets and all 58 nested annual event payloads OR a verified reversible event-list reconstruction recipe with precise ordinal position and source SHA. No duplicate counting; exact reconstitution of original annual record.
- **UNIFIED_STEP** full originally authenticated Deep inventories, thermal/mechanics/material flows/hydrology fields (cannot infer omitted numeric precision or units).
- **REGIONAL_EVENT** all 58 original externally indexed payloads per year, each original `sequence`, source external time_year (50 dated +8 **null** per year), source canonical bytes hash and original emission context. For 8k HYDRAULIC_DIAGNOSTIC, `source_time_year: null` stays null. If using storage/lookup `time_key` that encodes sequence or emission year, explicitly label it as a **storage ordinal/context**, never measured historical event timestamp.
- No action may omit UNKNOWN_NOT_INFERRED rock or plate status, material catalog authority or historical geographic support. Future nonfixture environment/biology/populations must gain explicit domain-specific retention contracts, not ghost data extrapolated from 3×3.

## Two alternative typed storage shapes — benchmark, do not prematurely ratify

**Option A (1 EventRecord per standalone event, plus per-year Temporal/State records):** exposes native B0 event reads but at least 58k event record files; repeated full-view manifests can dominate persistent bytes and time; native event_at record ID sorting is NOT original event order. Explicit source-sequence adapter still needed.

**Option B (one/few TemporalRecord annual bundles containing ordered canonical original event/Unified/year material, plus state snapshots/deltas as typed records):** reduces B0 record fanout and full-view manifest copy, but native HistoryQueryService.event_at does not expose nested event records. Requires a named, tested sequence-aware adapter, query indexes and provenance contract; no silent fallback.

**Proposed experimental comparison:** on scratch *synthetic* staging only, measure both options at 3Y/10Y/100Y (not immediate 1000Y ingest), including directory item count, total bytes (records + view manifests + journals + delta blobs), fsync count/wall, peak RSS and specific time/place/Deep/source-order queries. Choose after evidence, not by arbitrary preference.

## Atomic persistence and off-store blob caution

HistoryStore does not currently transactionally publish arbitrary content-addressed external blob files. If B2-B uses separate compact binary/JSONL delta packs, B0 view publication alone cannot guarantee sidecar atomicity: stage and fsync blobs first, pin SHA in typed records, publish only when all blobs have been verified, and define crash recovery/garbage collection for unreferenced prepublished blobs. An orphan must not be query-visible; a committed view with missing blob must fail-closed. Until that is implemented/tested, **no production/persistent archive writes**.

## Explicit contract gates and negative tests

**B2-B0 (next):** read-only source/API preflight against exact FAIR local commit; pin accepted `append_transaction` record types, TimeSupport/SpatialSupport, EventRecord and query ordering, read-view publication and source sha. Outcome only authorizes drafting scratch implementation.

**B2-B1 (candidate record grammar):** create type-valid test envelopes *without store writes*, selftest canonical serialize/roundtrip, preserve null-year and full original global sequence, original snapshot/event/Unified payload SHA.

**B2-B2 (scratch store only after separate approval):** 3Y/10Y per-year atomic visibility and restart recovery fault-injection; fail on stale parent view, duplicate/missing record, missing committed blob, wrong source hash, event order inversion, null date replaced, NaN, UNKNOWN misclassification, broken delta parent and orphan event. Compare native vs adapter queries.

**B2-B3 (measurement and seal):** 100Y then full 1000Y complete material/Deep/geology and event provenance query oracle (including arbitrary historical year and cell/volume), all 61,001 source envelopes reconstruct exact payload hashes; byte counts **including store overhead**. Scientific/World History production remains unauthorised until separate physical, bio, geo and canon gates.

## Invariant public marker

`E2C2_B2B=DESIGN_DRAFT__STORAGE_AND_QUERY_SHAPE_UNSELECTED`; no guarantee of query correctness or disk compression is granted. Operators must not merge docs branch into FAIR source branch, upload/push engine source, rewrite historical reference, or rerun solver.

## Concrete B2-B0 non-writing FAIR preflight prepared (as of 2026-10-30)

A separate standard-library AST-only script has been created and local Python compiled/self-tested (but **not executed against FAIR source yet**):

- `arcana_e2c2_b2b0_readonly_api_preflight.py` SHA256 `609aec03aa7c0c82ba2f56b21d3247089a7d44a1f3c102b4660ee337d8fa456b`.
- Package `ARCANA_E2C2_B2B0_READONLY_FAIR_PACKAGE.zip` SHA256 `353b86fc47eca941ab1581c463014c769e61b2b8536d1734dc9d39467fd220e9`.
- README `ARCANA_E2C2_B2B0_README.md` SHA256 `4533f70f010e4f2e68b33dcc5cc2f30576918f366fb8d4088859b601a7fc0a89`.
- These are current chat sandbox artifacts only and are **not** source Git commits or remote FAIR files. Python compile and `--self-test` PASS locally; ZIP integrity PASS.
- Operator copies just the script beside other probes into `~/HPC-POMDP/Arcana`, checks its SHA, runs `python arcana_e2c2_b2b0_readonly_api_preflight.py --self-test` then `python arcana_e2c2_b2b0_readonly_api_preflight.py`.
- Script verifies FAIR exact child HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`, parent and source branch/clean status; pins original 1000Y manifest SHA; AST-inspects seven real B0 modules without importing/instantiating a store, verifies exact typed transaction acceptance, `expected_parent_view_id`, read-view and temporal/causal fields, and confirms native event ordering is by record_id rather than source sequence. Prints source module SHA256.
- Expected actual FAIR success marker, **not observed yet**: `E2C2_B2B0=PASS_READ_ONLY_TYPED_HISTORYSTORE_API_PREFLIGHT`.
- Script does not certify runtime transaction atomics or persistent size; B2-B1/B2 scratch store work remains unauthorized until this preflight and contract adjudication.

