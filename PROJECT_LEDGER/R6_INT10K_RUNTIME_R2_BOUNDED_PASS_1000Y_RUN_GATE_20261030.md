# ARCANA R6 INT10K — R2 bounded FAIR PASS; NEW 1000Y R2 trajectory gate PENDING

Recorded 2026-10-30. Operator/user-supplied results from FAIR local report `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK/docs/arcana/R6_RUNTIME_R2_STRUCTURAL_FAIR_20261030.md`. The report and FAIR worktree are not available to the connected GitHub documentation session; **the exact R2 source hash, manifest and experiment source artifacts have not been independently inspected here**. Record these as OPERATOR_REPORTED, pending direct source/evidence intake. This document is a ledger and proposed next gate, not a new scientific/production approval.

## New R2 bounded result — PASS

R2 opt-in candidate preserves R1 and the same numerical body. Private dynamic frontier, older deposits frozen under controlled ownership, complete event/delta record rather than annual complete snapshot clone. **168 tests PASS** (negative, ownership/isolation, corruption, 3Y / 10Y direct/split). Readback of new history format and offline reconstruction matched **61,001 ordered historical payloads and 1,001 full regional snapshots**, including original 8,000 NULL event timestamps. Original output logical schema preserved on reconstruction. These tests are *not* a new R2 1000Y numerical trajectory.

| Benchmark | R1 | R2 | ratio R1/R2 |
| --- | ---: | ---: | ---: |
| Y101 hot step with ingest | 59.66 ms | 26.49 ms | 2.252x |
| Y501 hot step with ingest | 137.59 ms | 29.08 ms | 4.732x |
| Y751 hot step with ingest | 187.45 ms | 31.10 ms | 6.027x |
| Bounded Y751–755 combined query, full reconstruction and final checkpoint | 1.190 s | 0.844 s | 1.410x; -29.1% |

**Tradeoff**: a single-year restart plus complete reconstruction/output is **41–55% slower** on R2; this is not hidden or averaged into the fast hot-step measurement. Five remaining O(D) scans, import/query/checkpoint O(D) and complete canonical SHA calculation remain, explicitly deferred out of R2's hot path. R2 offline compact history representation ~162 MB versus original ~1916 MB, an **indicative ~91.5% reduction in the bounded offline representation**, not a new 1000Y live-run size comparison. R1 itself was full new 1000Y: 214.125572s loop, original history 1,916,080,917 B, 61,001 original items and five exact checkpoints. R2 has not repeated this full trajectory.

## Requested next operational gate — *new R2 1000Y* (not yet authorized)

User's latest message reports R2 bounded PASS and identifies a separate authorization prerequisite for the 1000Y numerical trajectory. **No new run was requested by explicit executable approval in that message.** Obtain explicit user approval and confirm FAIR site/job policy before launching. No scientific/canonical promotion.

### Preparation (read-only, allowed within R2 bounded implementation work)

1. Check actual FAIR branch, tracked/untracked changes, R1 and R2 source SHA/diffs and the 168-test source pins. Existing R1 and R2 changes are uncommitted; do not `git pull` code, overwrite, reset or auto-commit/push. Freeze R2 candidate by immutable source manifest and patch bundle under a **new** evidence directory and checksum, without modifying originals. R1 candidate 1000Y manifest SHA256 `3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b`; original 1000Y manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.
2. Review R2 current code/runner API and exact source/input pins. Prepare runner that uses **1-year external physical step** and **1000-year planned duration**, preserves exact original forcing/uplift/source config and numerical operators, keeps R2 frontier **alive across years**, and does not do full import/reseal/restart at every step. Include logical annual events/full-value deltas, regional annual records and unified Deep steps. If actual R2 API cannot preserve the frontier across segments without rebuilding all history, report BLOCKED before running.
3. Before any heavy execution, run short smoke parity and controlled y101/y501/y751 anchors; independently validate source hashes, root output path freshness, artifact quotas and FAIR actual scheduler/cgroup permissions, failure/cleanup behavior, exact 1000Y run config and numerical validity for that bounded **synthetic engineering** scope. No invented RAM/duration/output caps; honor actual site limits. A 1000Y validation may consume substantial CPU/writes even in compact mode; site quota is relevant.
4. Predeclare original oracle mapping: all 61,001 ordered kind/record digests; every year's REGIONAL_SNAPSHOT reconstructed from compact stream and exact canonical logical payload hash (all 1,001 including t0); all 1,000 REGIONAL_YEAR_RECORD, 1,000 UNIFIED_STEP (Deep), and 58,000 REGIONAL_EVENT including original 8,000 NULL source times; complete ordering and provenance; 5 milestones at y100/250/500/750/1000 with equivalent **logical coupled frontier/restart state**, not necessarily byte-identical physical R2 checkpoint envelope as R1, given legitimate format change. Verify water/solid/material balances and continuity each year and exact expected cumulative material deposit state. Reject missing history/UNKNOWN coercion.
5. Require isolated new candidate output directory, no modifications to baseline/original artifacts, immutable manifest with own REPORT, hash and error evidence. If later authorized, run once; do not auto-rerun on failure.

### Exact observations to capture if the 1000Y execution is later authorized

Report **simulation hot loop** (including real compact ingest), **checkpoint/verification wall**, **reconstruction/query wall**, and **full compatibility materialization wall** as *separate explicitly identified work*. Overall combined time must cover everything physically done; no double counting of nested timers. Compare R2 vs historical R1 214.125572s only with clear matching service level, unlike different writer outputs. Also report CPU user+system, equivalent utilized cores, per-year and 100-year-window p50/p95/max, peak process and process-tree RSS, allocated/logical disk bytes, all file counts, delta/deposit/event stream growth and hashes, resource sampling overhead, restart checkpoint size/time/validation and genuine segmented continuation from R2 checkpoint. Show data size including metadata, read views, event and Deep streams (not snapshots only). R2 single-year checkpoint/complete-output slowdown and O(D) residual costs must be separately measured, not concealed.

### Acceptance and next gate

- `R2_1000Y=PASS_EXACT_NEW_TRAJECTORY_AND_COMPACT_RECONSTRUCTION` only if the **new** R2 physical evolution emits the exact original logical history at 61,001 record granularity, every reconstructed regional snapshot and all 5 milestone restart states match the R1/original *semantically or canonical-field-exact as required*, all negative/checkpoint/corruption checks pass, and the measured hot loop and full-service costs are transparent.
- `R2_1000Y=BLOCKED_<REASON>` otherwise; preserve evidence and source diff. A speed gain alone is insufficient to pass.
- A verified R2 1000Y result can support a **separate** R6 integrated synthetic 10,000Y execution contract; no implicit 10k approval. Review source/input exact identity, planned horizon and run-level uplift (0.1 m total distributed over new duration), physical-model authority, FAIR scheduling/quotas and output performance; measure wall/CPU/RSS/file size and 100Y windows. Do not assume one busy CPU can profit from 128 visible threads without topology change.

## Governing authority

```yaml
R1_1000Y: PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP_OPERATOR_REPORTED
R2_BOUNDED: PASS_168_TESTS_AND_OFFLINE_61001_RECONSTRUCTION_OPERATOR_REPORTED
R2_1000Y_NUMERICAL_TRAJECTORY: PENDING_EXPLICIT_USER_AUTHORIZATION
R2_10K_NUMERICAL_TRAJECTORY: NOT_AUTHORIZED
DOMAIN_INDEPENDENT_ADAPTIVE_RETENTION: ARCHITECTURE_ONLY
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

References: `PROJECT_LEDGER/R6_INT10K_RUNTIME_R2_STRUCTURAL_FASTPATH_GATE_20261030.md`, `PROJECT_LEDGER/R6_INT10K_RUNTIME_R1_FAIR_1000Y_PASS_AND_NEXT_GATE_20261030.md`, source report on FAIR `docs/arcana/R6_RUNTIME_R2_STRUCTURAL_FAIR_20261030.md` (not fetched).
