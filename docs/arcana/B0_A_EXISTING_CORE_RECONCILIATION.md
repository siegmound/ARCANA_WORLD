# B0-A — Existing WORLD_HISTORY Core Reconciliation

**Scope:** read-only reconciliation of the existing R6 history core against WH0-G and WH0-H. This report makes no application or scientific changes.

## A. BASELINE

- Branch: `r6/b0-world-history-core`
- HEAD: `ceb4fbd1e610f1e67807eb7d268dfbbc8274f351`
- Worktree before this report: clean.
- Current R6-focused pytest baseline supplied by the task: 252 collected, 252 passed, 0 collection errors. This audit did not rerun it.
- No commit or push.

## B. EXISTING MODULE MAP

| Module | Purpose and public surface | Persistence / consumers | Tests and present limits |
|---|---|---|---|
| `identity.py` | Canonical JSON bytes/hash, immutable JSON helpers, path rejection, deterministic typed IDs for run/history/branch/state/checkpoint/event/provider/provenance (lines 15–109). | In-memory; used throughout envelopes, bootstrap, records. | `test_identity_is_deterministic_versioned_and_path_independent` and bootstrap identity test in `tests/test_r6_bootstrap_core_wave1.py:64-89`. No distinct payload-ID type; content hashing is a primitive, not proof that payload identity equals semantic record identity. |
| `state.py` | `SupportClass`, `AuthorityClass`, `TimeSupport`, `SpatialSupport`, `DomainStateEnvelope`; identity-checked V1 and legacy V0 serialization (lines 11–227). | In-memory record; written/read through HistoryStore; consumed by query, adapters, T0 binding and initial-world materializer. | Round-trip, authority/value distinction, and unknown/NA/outside tests. `payload_ref` is a string; no payload resolver or payload verification. |
| `temporal.py` | Generic typed temporal record plus authority/provider/checkpoint/snapshot/event/refinement-anchor/consumer-checkpoint roles; EventRecord exposes cause, trigger, before/after states and dependencies (lines 14–172). | In-memory, optionally persisted through store/temporal registry. | Event metadata round-trip. No explicit forcing record or replay recipe. |
| `checkpoint.py` | Checkpoint identity, restart/retained state references, runtime/config/seed/dependency identity, compatibility check; refinement-branch metadata and identity (lines 15–231). | In-memory metadata; store persists checkpoint and branch envelopes. | Compatibility and serialization tested. It does not execute a restart or prove replay equivalence; refinement metadata does not enforce write isolation. |
| `provenance.py` | Immutable provenance record with activity, input/source refs, parents, outputs and attributes (lines 11–57). | In-memory and JSON-store persisted; traversed by store. | Graph traversal and dangling-reference failure tests. Does not itself validate referenced payload bytes or integrate every event/runtime action. |
| `store.py` | File-backed `HistoryStore`; append/read/list for state, provenance, event, checkpoint, provider binding, temporal record and refinement branch; exact state filters and provenance traversal (lines 22–166). | One canonical JSON file per record under record buckets. Reopen by constructing another HistoryStore on the same root. | Reopen, conflict/tamper-on-reappend, and traversal tests. No explicit close, manifest/schema negotiation, multi-record transaction, payload store, storage accounting, or general typed integrity checks on raw dict reads. |
| `query.py` | `state_at`, history listing, metadata/value search, state lineage, available resolution and refinement candidates (lines 13–146). | In-memory service over HistoryStore. | Exact state lookup and conflict handling tested. No difference or explicit `why` API; no interpolation. |
| `registry.py`, `planning.py` | Provider and temporal-authority registries; domain/engine/retention/dependency registries and causal-cone planning (registry lines 16–108; planning lines 10–314). | Registry state is in memory; temporal records can be persisted. | Deterministic registry/planning behavior tested. These do not provide storage quotas/accounting or execute a workflow. |
| `consumer.py` | Typed state request and checks for support/authority availability (lines 12–82). | In-memory validation. | Matching-input and authority-floor tests; it is not a consumer executor. |
| `bootstrap.py` | Validates bootstrap inputs and builds deterministic run/history/branch manifest, explicitly unbound from scientific execution (lines 11–44). | In-memory manifest only. | Deterministic identity and unbound execution test. No persistent history-root manifest lifecycle. |
| `physical_domain_t0.py` | Binds current physical T0 authority into a state, store, query and registry validation (`bind_physical_t0`, lines 148–330). | Writes an R6 state to HistoryStore; active physical-domain binding consumer. | Narrow binding checks exist in associated R6 tests; this is authority binding, not world evolution. |
| `initial_world/materialize.py` | Builds deterministic synthetic initial-world payload, field inventory and state/provenance/anchor envelopes (`_field_inventory` lines 242–263; `_make_states` lines 291–376; materialization lines 376–626). | Writes payload artifacts and World History records; payload is external to HistoryStore. Multiple state records reference a shared payload hash. | Initial-world tests cover determinism, package constraints and store reopen. This is a specific producer, not a generic raw-output/minimal-state extraction framework. |
| `initial_world/refinement.py` | Deterministic regional/tile refinement and parent-conservative generation (`materialize_region`, line 171 onward). | Produces in-memory refinement outputs and provenance descriptors; not itself a persisted HISTORY refinement branch executor. | Regional reconstruction, order/tile independence and preservation tests in `tests/test_r6_initial_world.py:213-370`. |

The current software-readiness report describes infrastructure readiness only; it does not authorize physical execution or supersede these implementation limits.

## C. WH0-G OBJECT COVERAGE

| Logical object | Status | Current evidence / limit |
|---|---|---|
| WORLD_HISTORY | PARTIAL | Records can share a history ID and persist, but bootstrap manifest is in memory; no durable history-root/catalog lifecycle. |
| Branch | PARTIAL | Deterministic BranchId and refinement-branch envelope exist. No generic branch creation/merge lifecycle or isolation enforcement. |
| SpatialSupport | IMPLEMENTED | Grid/cell/native-resolution/selectors are explicit in `state.py:51-69`; geometry validity and general support containment remain limited. |
| TemporalSupport | IMPLEMENTED | Instant/interval/snapshot-style typed temporal support and temporal records exist; no first-class forcing timeline. |
| DomainState | IMPLEMENTED | Versioned, identity-checked envelope with authority, support, uncertainty, provenance, parents, events and payload reference. |
| Checkpoint | PARTIAL | Restart identity/inputs and compatibility metadata exist; no restart executor or replay-equivalence proof. |
| Event | IMPLEMENTED | Typed event and causal links exist; not all state changes/actions are required to produce linked events. |
| Forcing | MISSING | No first-class forcing object/record or forcing query/storage contract found in the R6 core. |
| Authority | IMPLEMENTED | Authority class plus authority-anchor/registry representations exist; not a complete durable authority-catalog lifecycle. |
| Uncertainty | IMPLEMENTED | Structured uncertainty mapping survives state serialization; no common uncertainty ontology or required schema. |
| Provenance | IMPLEMENTED | Records and recursive parent traversal exist; external payload verification and complete runtime integration are absent. |
| ReplayRecipe | MISSING | Checkpoint captures restart metadata but there is no explicit recipe type or replay executor. |
| Entity/Lineage | PARTIAL | Parent-state links, event references and provenance traversal support record lineage; no first-class evolving entity identity/lineage model. |
| RefinementBranch | PARTIAL | Persistable deterministic metadata and candidate query exist; isolation, parent immutability and reconstruction linkage are not enforced end-to-end. |
| Payload reference | PARTIAL | States can carry opaque string references and producers share a hashed payload; core has no payload identity contract, resolver, byte verification or lifecycle. |

No legacy equivalent was necessary to classify as an adapter in this generic-core audit.

## D. H1-H18 ACCEPTANCE MATRIX

| Gate | Status | Existing evidence | Minimal remaining work |
|---|---|---|---|
| H1 write integrity | IMPLEMENTED_AND_TESTED | Canonical serialization, immutable create, conflict rejection; tampered state followed by attempted append is rejected (`store.py:31-55`; `test_r6_bootstrap_core_wave1.py:223-227)). | Add read-time record verification across all record types and failure-injection coverage. |
| H2 close/reopen identity | IMPLEMENTED_AND_TESTED | New HistoryStore instance reads persisted state/event/temporal/checkpoint (`test_r6_bootstrap_core_wave1.py:176-202)); initial-world producer repeats it (`test_r6_initial_world.py:92-117)). | Define/document lifecycle and compatibility for store schema changes. |
| H3 state query | IMPLEMENTED_AND_TESTED | Exact scoped state query and statuses (`query.py:23-51`; tests at `test_r6_bootstrap_core_wave1.py:230-264)). | Preserve current exact/no-interpolation behavior. |
| H4 history query | PARTIAL | History enumeration exists (`query.py:53-57)); current query-surface test covers a small fixture (`test_r6_world_history_core.py:88-108)). | Test ordered multi-time/multi-domain history and support metadata completeness. |
| H5 difference query | MISSING | No difference operation in HistoryQueryService. | Add explicit, support-aware difference result; never infer across incompatible/unknown support. |
| H6 WHY/provenance traversal | PARTIAL | State lineage + provenance DAG traversal and dangling-ref failure (`query.py:71-98`, `store.py:156-166`; tests at `test_r6_bootstrap_core_wave1.py:379-398)). | Join state, event, authority, provenance and dependency paths into one auditable explanation result. |
| H7 UNKNOWN preservation | IMPLEMENTED_AND_TESTED | UNKNOWN/NOT_APPLICABLE/OUTSIDE_SCOPE remain distinct null-valued states; parameterized round-trip and query-status tests (`state.py:92-116`; tests at `test_r6_bootstrap_core_wave1.py:155-162,230-264)). | Add explicit regression that known zero and false remain known values. |
| H8 replay integrity | PARTIAL | Checkpoint has runtime/config/seed/dependency identity and compatibility predicates (`checkpoint.py:15-94)); metadata compatibility tests at `test_r6_bootstrap_core_wave1.py:176-222). | Add ReplayRecipe, executor boundary, input closure, and deterministic restart equivalence fixture. |
| H9 append-only immutability | IMPLEMENTED_AND_TESTED | Existing identical write is idempotent; differing write conflicts (`store.py:31-55)); regression at `test_r6_bootstrap_core_wave1.py:223-227). | Ensure all record types and external payload references receive equivalent verification. |
| H10 refinement branch isolation | PARTIAL | Branch envelope persists and is queryable (`checkpoint.py:156-231`, `store.py:126-136)); metadata round-trip test `test_r6_world_history_core.py:54-86). | Test child writes cannot mutate parent records; enforce branch-scoped write rules. |
| H11 refinement reconstructability | PARTIAL | Initial-world regional refinement reconstructs deterministic terrain and tests it (`initial_world/refinement.py:171+`; `test_r6_initial_world.py:213-288)). | Bind reconstruction recipe, parent checkpoint/payload, boundaries and output to persisted refinement branch. |
| H12 storage accounting | MISSING | No byte accounting across store/payload/cache classes found. | Add generic measured counters for canonical persistent, metadata, payload, index, scratch, provider cache and refinement cache. |
| H13 payload integrity | PARTIAL | Initial-world payload is deterministically hashed and verified by producer (`initial_world/materialize.py:81-113,415-494)); state stores opaque ref (`state.py:84,131-162)). | Core-level payload identity/resolution/read verification; keep payload ID distinct from semantic state ID. |
| H14 support boundaries | PARTIAL | Explicit spatial/time support; exact cell selection and no interpolation (`state.py:34-69`, `query.py:23-51,100-113)). | Define and test coverage behavior for all selectors and distinguish unsupported from not-found consistently. |
| H15 authority preservation | IMPLEMENTED_AND_TESTED | Authority is explicit in state and validated by consumer; test ensures numeric value does not imply authority (`state.py:25-32,71-116`, `consumer.py:39-82`; `test_r6_bootstrap_core_wave1.py:135-162)). | Keep authority semantics separate from provider presence and numerical value. |
| H16 minimal-state extraction | PARTIAL | Initial-world producer has an explicit field inventory and emits selected state envelopes referencing shared payload (`initial_world/materialize.py:242-376)). | No general separation contract for raw engine output versus minimal persistent sufficient state, nor retention/selection validation. |
| H17 deterministic ordering | PARTIAL | Store enumeration and query output sort deterministically; registry ordering is deterministic (`store.py:63-67,114-136`, `query.py:53-69`, `registry.py:80-108)). | Test ordering under insertion permutations for queries, registries and reopened stores. |
| H18 failure atomicity | PARTIAL | A single record is staged, flushed/fsynced and hard-linked atomically (`store.py:31-55)). | No injected-failure tests, directory fsync, or atomic transaction across related state/provenance/event records. |

**Counts:** 6 IMPLEMENTED_AND_TESTED; 0 IMPLEMENTED_UNTESTED; 10 PARTIAL; 2 MISSING.

## E. PERSISTENCE MODEL

The core backend is filesystem JSON, not SQLite. Each record is a separate canonical JSON file. `HistoryStore.SCHEMA` names a V0 store schema but no store manifest is written or checked. State and checkpoint envelopes have V0/V1 schema compatibility; temporal/provenance/provider records have identity/role data but no common store migration protocol.

A new HistoryStore pointed at the same directory can read records; there is no explicit close API or long-lived handle to close. The current atomic write stages a temp file in the destination bucket, flushes/fsyncs it, then uses a hard link to install it without overwriting a conflicting record. That gives a useful single-file atomicity boundary. It does not make a set of related records transactional, and the parent directory is not explicitly fsynced.

Payload bytes live outside HistoryStore. `payload_ref` does not cause the store to load or validate them. Typed state/checkpoint reconstruction checks semantic record identity; raw dictionary reads for some other records do not uniformly reconstruct and verify typed identities.

**Smallest H1/H2/H13/H18 follow-up:** persist and validate a store schema manifest; make all reads verify record identities; define a payload reference/resolver interface with byte-hash validation while retaining backend neutrality; add failure-injection and multi-record atomicity tests. Do not choose a production database in this audit.

## F. IDENTITY MODEL

Typed semantic IDs exist for run, history, branch, state, checkpoint, event, provider binding and provenance. Their values are deterministic hashes over canonical semantic bodies; serialization reconstruction validates them. Refinement branches use BranchId. Authority, temporal support and replay recipe do not have dedicated IDs; temporal role records use deterministic role/body hashes. No ForcingId or PayloadId exists.

The producer demonstrates the needed sharing shape: distinct domain-state records can point to fields in the same deterministic payload (`initial_world/materialize.py:242-376`). However payload refs are strings and payload SHA is carried in producer metadata/provenance. There is no general enforced identity distinction between content-addressed payload and semantic record beyond the separate fields currently used. Future B0 work must formalize the distinction without collapsing record identity into a content hash.

## G. SUPPORT SEMANTICS

TimeSupport records a time key, coordinate system and instant/interval/snapshot kind; SpatialSupport records grid, cells, native resolution and selector kind. DomainState has separate support class and authority class. UNKNOWN, NOT_APPLICABLE and OUTSIDE_SCOPE are distinct enum states and require null values. A missing query result is separately represented by query statuses such as NOT_FOUND/MISSING_DOMAIN/MISSING_TIMESTAMP. Exact cell lookup does not interpolate, and available-resolution explicitly reports `interpolation_performed=false`.

Current limits: general geographic containment and selector coverage are not implemented as a universal contract; support mismatch and absent records do not always have their own fully normalized result taxonomy. Add zero/false-known regressions to ensure ordinary values cannot be confused with unknown.

## H. QUERY MODEL

- `state(...)`: implemented as `state_at`, scoped by history, branch, domain, time and optional cell; reports found/unknown/not-applicable/outside/conflict/missing statuses with state/provenance where available.
- `history(...)`: returns scoped state records in deterministic order.
- `difference(...)`: absent.
- `why(...)`: no single API; `lineage` plus `trace_provenance` provides partial state-parent and provenance traversal.
- `search(...)`: exact metadata/value-path filters; not a generic query language.
- Resolution/refinement queries expose available native support and candidates without interpolation or execution.

## I. REPLAY / REFINEMENT

Checkpoint metadata records runtime identity, configuration hash, seed lineage, upstream dependencies, restart compatibility, parent checkpoint, authority/provider refs and output manifest. Compatibility is a predicate only. No ReplayRecipe or replay executor ties forcings, events, provider versions and outputs into an executable restart proof.

RefinementBranchEnvelope records parent branch/history, base history, anchor, region, interval, requested domains/resolution, boundary conditions, provenance, outputs and status. The store persists it and query returns candidates. It does not enforce branch isolation or prove parent immutability. The initial-world regional refinement algorithm is tested for deterministic reconstruction, but it is not the same as replaying a persisted WORLD_HISTORY refinement branch from a checkpoint.

## J. MINIMAL STATE

No generic raw-output-to-minimal-history extractor exists. The initial-world producer does define a field inventory and materializes selected state envelopes and payload references. This is a useful local example, not a system-wide minimal-sufficient-state contract, retention policy or validation that discarded raw outputs remain reconstructable where required.

## K. STORAGE ACCOUNTING

No core accounting was found for canonical persistent records, indexes, scratch, provider/cache, refinement cache, metadata or payload bytes. Existing retention classes express retention intent, not measured usage. The architecture’s hard cap remains canonical persistent WORLD_HISTORY below 500 GB; this audit does not derive quotas or a final backend.

## L. TEST ADEQUACY

- Unit/serialization: state V1 and legacy V0 round-trip, event/checkpoint/refinement metadata round-trip (`tests/test_r6_world_history_core.py:32-86)).
- Persistence/reopen: tests construct a second HistoryStore on the same path and read records (`tests/test_r6_bootstrap_core_wave1.py:176-202`; `tests/test_r6_initial_world.py:92-117)); this is a real filesystem reopen, not an in-memory cache check.
- Integrity: state mutation is written directly to JSON then rejected on attempted same-ID append (`test_r6_bootstrap_core_wave1.py:223-227)); it does not test that a plain read detects tampering. Event raw-dict reads lack equivalent coverage.
- Query: scoped found/missing/unknown and conflict behavior tested (`test_r6_bootstrap_core_wave1.py:230-275)); history/difference/why coverage is absent or limited.
- Provenance: recursive provider-to-derived-record trace and dangling provenance failure tested (`test_r6_bootstrap_core_wave1.py:379-398)).
- Branching/refinement: metadata creation/serialization/candidate selection tested, but not parent immutability, cross-branch isolation or persisted-branch reconstruction.
- Failure behavior: conflict and dangling-reference errors exist; atomic-write fault injection and multi-record rollback are untested.
- Numerical domain state and scientific execution are not in scope of these generic infrastructure tests.

## M. GAP MATRIX

| Requirement | Existing implementation / test | Status | Minimum change | Risk |
|---|---|---|---|---|
| Record write/read integrity | Immutable per-file write; partial tamper test | Partial closure | Verify identities on every typed read and add corruption tests | Silent corrupt raw records |
| Reopen/schema | Filesystem reopen tests; no store manifest | Partial closure | Persist schema/version and reopen compatibility test | Incompatible stores appear readable |
| Payload identity/integrity | Opaque refs; producer hashes payload | Partial | Backend-neutral payload descriptor/resolver + verify bytes | Stale/wrong payload silently consumed |
| Support boundaries | Explicit exact support; no interpolation | Partial | Normalize outside/unavailable/mismatch results and test selector edges | Unsupported state mistaken for missing |
| Queries | state/history/search/lineage/resolution | Partial | Add difference and joined explanation only after result contract | Misleading comparisons/causal gaps |
| Replay | Checkpoint metadata only | Partial | ReplayRecipe and synthetic deterministic restart proof | Metadata mistaken for reproducible replay |
| Forcing | No typed record | Missing | Introduce neutral forcing envelope linked to support/provenance | Forcing semantics left untyped |
| Refinement branch | Envelope and candidate selection | Partial | Enforce branch-scoped writes and parent immutability tests | Child refinement mutates canonical parent |
| Minimal extraction | One producer inventory | Partial | Generic extraction boundary and retained/reconstructable output manifest | Persisting too much or dropping needed history |
| Storage accounting | Retention classes only | Missing | Measured category counters; no premature quotas | 500 GB ceiling cannot be demonstrated |
| Difference query | None | Missing | Exact-support comparison result with uncertainty/authority metadata | Invalid cross-support comparison |
| Failure atomicity | Atomic single file only | Partial | Inject faults and define small transaction boundary | Partial records after interruption |

## N. PROPOSED B0 IMPLEMENTATION WAVES

Order follows actual dependencies; these are proposals, not implementation.

1. **B0-B — record/store identity and support closure.** Add persisted store schema identity, validate all typed reads, formalize payload reference identity separately from semantic record IDs, and normalize support mismatch outcomes. Close H1/H2/H7/H9/H13/H14 gaps without selecting a payload backend. Files: `identity.py`, `state.py`, `store.py`, with focused identity/store/support tests.
2. **B0-C — persistence failure boundaries.** Specify the minimal record transaction boundary, atomic related-record append behavior, directory durability policy and fault-injection tests. Retain filesystem JSON provisionally. Closes remaining H1/H2/H18 evidence.
3. **B0-D — causal/replay inputs.** Add first-class forcing and ReplayRecipe records; bind checkpoint, authority, event/forcing, runtime/config/seed/dependency identity; synthetic replay equivalence only. Closes H8 and forcing coverage.
4. **B0-E — query completion.** Add support-aware difference and joined WHY/explanation results while retaining exact query semantics and no implicit interpolation. Closes H5 and H6; expands H4/H14 tests.
5. **B0-F — branch/refinement isolation.** Enforce branch scoped writes, parent immutability and persisted refinement reconstruction from declared checkpoint/boundaries. Closes H10/H11.
6. **B0-G — minimal-state and measured storage accounting.** Separate raw outputs from persistent minimal sufficient records; add measured category totals and reproducibility metadata without freezing quotas/backend. Closes H12/H16.
7. **B0-H — synthetic lifecycle fixture.** Bootstrap → records/provenance → close/reopen → query/explain/difference → replay/refinement branch, with corruption and injected-failure cases. This is an integration proof across the preceding gates, not a substitute for each gate’s unit test.

Each wave remains infrastructure-only. Keep the proposed exact files and tests small after B0-B confirms the final interfaces.

## O. PROTECTED SCIENTIFIC BOUNDARY

This reconciliation inspects infrastructure only. It does not reinterpret provider authority, alter canonical state, run ShellSet mechanics, create T1, select `dt`, or authorize forward evolution. Preserve the currently supplied gate values:

- `runtime_authorized=true` only for `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`
- `mechanics_authorized=false`
- `forward_evolution_authorized=false`
- `dt_selected=false`
- `t1_created=false`
- `canonical_state_changed=false`

No scientific execution is implied by any B0 capability described above.
