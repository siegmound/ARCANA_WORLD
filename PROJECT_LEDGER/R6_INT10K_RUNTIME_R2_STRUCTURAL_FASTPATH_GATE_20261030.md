# ARCANA R6 INT10K — Runtime R2 structural fast-path gate and Codex implementation brief

**Decision date:** 2026-10-30. **User decision:** proceed with the next **R2 design, implementation and bounded qualification** after R1 PASS. This document is a technical engineering work order, not evidence of a source patch, tests already run, any 1000Y/10k R2 simulation or scientific qualification.

**Required source:** FAIR existing worktree `~/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`, reported branch `r6/runtime-copy-r1-fair`, git HEAD parent `2c71370eb9a959c78121ce1c88ec8e9e37187787` with an **uncommitted** opt-in R1 optimization. **Do not require an empty git status**; the reported R1 patch is intentionally dirty. Inspect live source and capture exact R1 file SHA/diff before creating new R2 edits. Never run `git reset --hard`, destructive checkout, pull or merge over this worktree. GitHub docs branch is **not** the FAIR local code branch. Do not automatically commit or push.

## 0. Authoritative references, do not overwrite

- `docs/arcana/R6_RUNTIME_COPY_R1_FAIR_20261030.md` on FAIR, previously supplied by user (operator evidence). It records `R6_INT10K_RUNTIME_R1=PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP`: new R1 1000Y loop 214.125572 s vs historical 244.780960 s, 61,001 payloads and full HISTORY/INDEX byte exact, five checkpoint bytes exact, 8,000 event NULL year values preserved; R1 opt-in by default. Historical comparison -12.52% indicative, 7-repeat anchored y101/y501/y751 1.084x/1.175x/1.192x controlled speedup. 1000Y HISTORY still 1,916,080,917 bytes. R1 did not eliminate O(Y²).
- Ledger: `PROJECT_LEDGER/R6_INT10K_RUNTIME_R1_FAIR_1000Y_PASS_AND_NEXT_GATE_20261030.md`; `PROJECT_LEDGER/R6_INT10K_B2B3S_PASS_DOMAIN_RETENTION_RUNTIME_FIRST_20261030.md`.
- Original 1000Y immutable archive at FAIR: `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y`. Original MANIFEST SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.
- R1 new evidence `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/RUNTIME_R1_CANDIDATE_1000Y_20261030_01`; manifest SHA256 `3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b`. R1 code patch is **not** committed/pushed; do not reconstruct its exact bytes from stale published remote code.
- Previous E2-C2-B1 offline exact virtual delta reconstruction of 1001 regional snapshots, and E2-C2-B2B3S bounded B annual bundle 100Y PASS, supply **reference techniques**, not direct R2 qualification.
- Contracts: `docs/arcana/B6N4A_EVENT_IMPACT_AND_STATE_SIGNIFICANCE.md`, `docs/arcana/B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE.md`, and `contracts/R6_SIGNIFICANT_STATE_EXTRACTION_RECONSTRUCTION_V1.json`. Per-domain adaptive retention comes **later**, not in R2.

## 1. Primary performance objective — remove per-year work proportional to ALL prior history

R1 changed JSON encode/decode to detached Python copies while retaining O(D(y)) repeated cloning, annual full snapshot construction, deposit sums, and verification of growing frontiers. With ~11 deposit rows added annually and D(y)=O(y), legacy complete yearly full snapshots require O(Y²) total output. **R2 changes the representation and the loop**, not only the serializer:

- Maintain a **mutable minimal current solver frontier** with exact original physical state values and memory, and immutable/stable older material/deposit objects where proven safe.
- Record **append/replace/remove** operations as full-value, ordered **regional/material deltas** plus event metadata, capturing nondeposit changes, cell order, exact source provenance and SHA identities. Existing toy fixture may only append, but verify; fail closed on unexpected in-place edits.
- In the R2 compact runtime path, do **not** build a new full historical `REGIONAL_SNAPSHOT` each year or recursively serialize/copy all earlier deposits solely to append history. Emit history events/deltas + exact yearly and UNIFIED/Deep records, preserving their source semantics.
- Generate legacy logical snapshot **on-demand for queries, sampled oracle validation and requested replay**, using checkpoint + ordered deltas. A full legacy archive materialization is an optional, separately timed compatibility phase, not part of optimized streaming loop. The original source full HISTORY and INDEX are **not** expected to be byte-identical as physical files in compact mode; equivalence is **logical reconstructed payload SHA** for all original indexed records, with source order and NULL timestamp semantics. Do not claim an absent full HIST file is byte-equal.
- Eliminate or amortize repeated deposit scans in per-cell solid mass, geologic load, and checkpoint processing only if the exact order/float results and all negative/invalid-input behavior remain qualified. Numeric reduction order can change floating results; test each affected field before using a cached accumulator.
- Reader and writer must not mutate shared solver state. Explicit ownership, defensive isolation/immutable references, alias tests and fail-closed boundary; avoid silently sharing mutable public dicts with consumers.
- Keep old R1 and legacy modes runnable unchanged as exact oracles.

**Success criterion**: demonstrate via instrumentation that hot-path CPU and bytes copied per year no longer scale with cumulative historical deposits *for the operations actually replaced*, while measured end-to-end wall and storage improve on equivalent requested output service levels. Do not claim global O(Y) physics or O(1) memory: living current-state material layers may genuinely grow and some physical operations may need O(D). Checkpoint frequency, reconstruction/query latency and resource requirements must be reported separately; no hidden shift of O(Y²) cost from solver to writer.

## 2. Mandatory phased work

### R2-A — read-only exact baseline and design

1. Inspect actual FAIR code, source identity, git diff of R1, R1 report and evidence integrity. Check source/source E0 checksums/original oracle manifest; capture immutable local R1 patch and file SHA in a **new R2 evidence root**, without modifying the old report or original evidence. Verify actual last passed test suite and source hashes before change.
2. Call-graph/complexity and per-phase profiler, from saved y101/y501/y751 restart cases. Attribute duplicate copies in `advance_region`, regional snapshot emission, checkpoint hash/validation, history consumer and deposit scans. Isolate numerical engine vs output costs. Record exact `current_state` mutable ownership and all consumers requiring legacy snapshots; include effects on E1/E2 tests and source hash.
3. Produce a strict field inventory and invariants matrix before changing the code: initial state; all nondeposit cell fields; each deposit key and order; source/original event sequence/time/null; annual and unified Deep; physical balances; dynamic memory; source/config/forcing and exact hash boundaries.
4. Choose **one minimal opt-in architecture** with versioned schema/adapter; explain expected O(·) runtime, checkpoint and query complexity and fallback/rollback. Do not build a new uncoordinated second B0 store.

### R2-B — implement test-first bounded candidate

1. Create independently testable **compact year-delta + reconstruction** codec; persist full-field values where needed, parent/target canonical snapshot hash and identity. Do not infer missing fields from `DEPOSITION` events; events alone lacked density, stable deposit event id and full historical metadata. Preserve original records/source sequence and original `NULL` timestamp.
2. Create opt-in `runtime_compact_history=True` or equivalent distinct flag; keep R1 opt-in separate and legacy defaults unchanged. No change to numerical laws, timestep, forcing, thermal/hydrology/Deep outputs or float precision.
3. Avoid copying accumulated full deposit rows in each year. Use immutable-with-ownership/structural sharing or equivalent safe bounded copy, and append-only material journal with a *separate* exact reconstructed view. Parent and new states must be detached with respect to mutation where public API guarantees require it.
4. If numerical running cost is still dominated by repeated balance scans/hash on growing live state, measure explicitly; fix only if exact/sufficiently authorized numeric parity can be demonstrated. Do not turn exact regression tolerances into broad loose tolerance.
5. Use existing B0 checkpoint, retention, replay, journal/source identity and atomicity contracts for any persistent integration. Prefer a bounded scratch adapter and testing first; defer production HistoryStore optimization B2B4.

### R2-C — bounded qualification (authorized scope here: implementation + small tests only)

- Pure synthetic codec tests (append/replace/remove, empty cells, field addition/removal, cell ordering, nonfinite/invalid, duplicate/omitted/reordered material/event, hash tampering, cyclic/non-serializable values, alias mutation, stale parents). Reject uncovered states.
- Current R1/E2-C1 regressions (at least existing 141 focused tests plus new R2 cases) and original 3Y direct vs 1+2, 10Y direct vs 5+5 under same R1 source/config/inputs: exact causal event/yearly and unified Deep source payload hashes, frontier/state/checkpoint and balances. Null event timestamps remain null.
- Y101/Y501/Y751 single-year resumed anchor replay with 7 controlled repetitions, same measured output functionality between legacy R1 path and new compact path. Compare separately **engine-only**, compact sink, requested historical query materialization, and legacy output compatibility cost; do not misrepresent different output work as a matched wall speedup.
- **Read-only offline** check of the existing original 1001 snapshot oracle and 61,001 records against a newly generated candidate delta/reconstruction representation. Important: merely running B1's old converter against the old oracle is insufficient to establish that a new R2 engine writer is correct. Prove new generation for bounded years and authentic original field parity. Full new R2 1000Y trajectory **requires a separate explicit run gate**, so may remain PENDING.
- Consistent checkpoints and crash/failure/corruption evidence; if B0 scratch store used, verify old pinned view and atomic publication. A bounded in-memory codec test is NOT durability or full archive production validation.
- Baseline and candidate output bytes (logical/allocated), file count, wall/CPU by phase, peak RSS and year-window trajectories; read-only reports should include existing reference original `R1=214.125572s` but no new global 10k estimate from unvalidated extrapolation.
- On failure, stop and preserve evidence and diagnostics; no patch stacking, source reset, solver auto-retry or status promotion.

### R2-D — only after review, separately authorized scalability experiments

1. Request a controlled **new 1000Y compact candidate numerical replay** if needed to test new full-history generation, reconstruction at all 0..1000 years and source cross-kind sequence. Compare compact simulation wall, all domain reconstructed outputs, disk bytes and replay cost; do not automatically execute.
2. After exact 1000Y qualification, review and **separately authorize** a synthetic integrated **10,000 year** FAIR benchmark. One planned `RegionalConfig(duration_years=10000)`, one-year external steps, 3x3/C028/C029 existing physical constants, source/input hashes and real FAIR site/cgroup permissions; carefully account for prior run-level total uplift (0.1 m) being redistributed over longer duration. `INT3_ENG10K` is a different reduced benchmark and not relevant proof.
3. For 10k record: loop/end-to-end wall, CPU user/system and effective cores, wall by domain/copy/snapshot/query/writer/checkpoint, p50/p95/max annual times and each 100Y window, process-tree peak RSS, logical and allocated disk bytes, file count, events and deposit growth, checkpoint bytes/encode+verify time, corruption/recovery, source provenance and UNKNOWN coverage. All real FAIR site constraints apply; no invented programmatic time/RAM/output caps. A reference full snapshot at 10k would be an extremely large **separate cost**, not secretly included or silently omitted from measured totals.

## 3. Hard stop and output

**Do not run a new 1000Y or 10k R2 numerical trajectory under this acceptance.** Approval covers the next implementation and bounded verification stage, not a large job. Do not commit/push/merge or alter original evidence without separate instruction. Do not change source/physical authority flags.

Required Codex answer:
- Exact actual source status and separate R1 patch SHA; new R2 modified files and diff.
- Baseline hotspot evidence and O(·) analysis, including any remaining O(D) scans.
- Code design / ownership, per-event and per-domain preservation and exact reconstruction proof.
- Test suite, named negative/positive cases, 3Y/10Y and 7-repeat anchors.
- Comparable workload performance for solver-only, compact ingest, original-format reconstruction, and combined costs, plus peak RSS and bytes.
- Explicit decision `R2_BOUNDED=PASS_... / BLOCKED_...`; list new 1000Y R2 / 10k FAIR run gates still PENDING, no invented projection.

```yaml
R1: PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP_FAIR_OPERATOR_REPORTED
R2_DESIGN_IMPLEMENTATION_BOUNDED_TESTS: USER_AGREED_PROCEED
R2_1000Y_NUMERICAL_RUN: NOT_AUTHORIZED
R2_10000Y_NUMERICAL_RUN: NOT_AUTHORIZED
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```
