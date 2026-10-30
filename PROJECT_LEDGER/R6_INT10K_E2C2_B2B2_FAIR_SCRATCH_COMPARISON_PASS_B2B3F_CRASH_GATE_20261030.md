# ARCANA R6 — B2-B2 FAIR 3Y/10Y real scratch HistoryStore comparison PASS; B2-B3F crash gate prepared

Date 2026-10-30. The figures below are from operator-pasted FAIR stdout, not hypothetical model projections. This gate qualifies an isolated synthetic engineering test only.

## Exact operator evidence

- Input executable `arcana_e2c2_b2b2_scratch_store_compare.py` SHA256 `70ba607096e2477faff4f879f6471a1e252900944f4f47f0c270072168d3c9ba`, independently checked by the FAIR operator.
- `E2C2_B2B2_PURE_SELFTEST=PASS`; B2B1 actual typed roundtrip self-test PASS; `E2C2_B2B2_SOURCE_INDEX=PINNED_AND_3Y10Y_PAYLOAD_SHA_PASS`.
- Each of four real, independent temporary stores (3Y-A per-event, 3Y-B yearly bundle, 10Y-A, 10Y-B) used `HistoryStore.append_transaction` with guarded expected parent view and tested old reader pinned view cannot see the later committed records. Stale parent rejected; reopened typed store was queried and all snapshot payload hashes reconstructed exactly; original annual and UNIFIED/Deep payloads exact; original event sequence exact; NULL source time preserved. Temporary stores deleted, engine and original archive unmodified.
- 3Y reconstructs 4 snapshots +174 external events, 24 source null years, 4 transactions and 4 old view checks. 10Y reconstructs 11 snapshots +580 external events, 80 null years, 11 transactions and 11 old view checks. All four measures explicitly report snapshot `EXACT_PASS`, yearly/Unified `EXACT_PASS`, source sequence `EXACT_PASS`, stale-parent negative `PASS`.

## Observed full-store measurements

| Test | Total store bytes | Files | Read-view bytes | Write total (s) | Reopen/query (s) | Temporal bytes | Standalone event bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3Y-A per event | 653145 | 192 | 29598 | 0.824694 | 0.184772 | 362484 | 220109 |
| 3Y-B annual bundle | 482394 | 15 | 2979 | 0.117323 | 0.040827 | 438461 | 0 |
| 10Y-A per event | 2316406 | 626 | 257672 | 2.700833 | 1.177530 | 1210855 | 734577 |
| 10Y-B annual bundle | 1591834 | 36 | 13647 | 0.404412 | 0.134998 | 1464885 | 0 |

On 10Y scratch B uses 31.280% fewer total store bytes (724572 bytes), 94.249% fewer files, 94.704% fewer view-metadata bytes, writes 6.678x faster and reopens/queries 8.723x faster. B's larger `temporal` bucket is **not** a regression hidden by reporting only event files; full-store totals include both buckets and read-view metadata. At 3Y, B uses 26.143% fewer total bytes. Wall times are single small-run observations; do not project speedups to 100Y/1000Y.

## Architectural decision

Decision: `E2C2_B2B2=PASS_3Y10Y_ATOMIC_SCRATCH_STORE_COMPARISON`; `B_ANNUAL_BUNDLE=LEADING_CANDIDATE_FOR_MORE_TESTS`, **not yet production selected**. Candidate B preserves externally indexed event source `sequence`, `payload_sha256`, exact `source_time_year` (8 null per year), source context and Deep via a typed `HistoricalSnapshot` bundle, as well as the regional delta/anchor states.

Important unresolved caveats: B does **not** populate native `HistoryStore.events()` and does not make native `HistoryQueryService.event_at()` equivalent to source order; a tested sequence-aware query adapter with time/place/material/Deep semantics is mandatory. The B0 read-view manifest stores full membership per committed transaction and must be benchmarked at 100Y; current 10Y results cannot establish 1000Y scaling. The 3Y/10Y tests did not inject interrupted-process crashes nor simulate power loss. No persistent world-history output was authored.

## Next B2-B3F (FAIR execution pending)

Read-only original source plus **ephemeral scratch writes only**. Prepare a Linux subprocess-crash fault injection at `before_publication`, `after_publication`(first record), `before_commit`, `before_visibility_switch`, `after_visibility_switch`, and `during_cleanup`. Each test starts an independent isolated 2Y annual bundle store with authenticated Y0/Y1; subprocess dies via `os._exit(79)` during Y2 transaction, with no Python unwinding. A new store instance reopens/recoveries journal, verifies pre-switch rollback vs post-switch commit, old reader visibility, idempotent retry, full Y0..Y2 regional source SHA and 116 event/year1+2 original order +16 NULL event times; no active journal afterwards. This is a **process crash** test, not real disk power loss.

- New conversation artifact `arcana_e2c2_b2b3f_crash_recovery_scratch.py` SHA256 `3596da70bb63b5e148335bc4f97bafb80700a0849c6974ef877cea9b744f0dbc`; ZIP `ARCANA_E2C2_B2B3F_FAIR_PACKAGE.zip` SHA256 `56c5c29b63bd18a9afb565ddd0d0d7d39fde5406cea932b4a2fb8209ff41b46d`; README SHA256 `f68f9feceaaf9c0f700cd2848050b8b1a9fc33da8743ba038991480288fbe3c0`.
- Requires the SHA-pinned original operator-proven B2A/B2B1/B2B2 helper scripts adjacent and FAIR source local child `2c71370eb9a959c78121ce1c88ec8e9e37187787` and original 1000Y MANIFEST SHA `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`. Python compile and pure `--self-test` passed in chat file runtime; **actual six-stage subprocess/runtime fault test has NOT run on FAIR**.
- Suggested FAIR invocation:
```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate arcana-r6-linux
cd ~/HPC-POMDP/Arcana
sha256sum arcana_e2c2_b2b3f_crash_recovery_scratch.py
python -B arcana_e2c2_b2b3f_crash_recovery_scratch.py --self-test
python -B arcana_e2c2_b2b3f_crash_recovery_scratch.py
```
- PASS marker after actual FAIR proof only: `E2C2_B2B3F=PASS_SUBPROCESS_CRASH_RECOVERY_AND_SOURCE_ORACLE_6_STAGES`. If blocked, preserve evidence and diagnose runner/API assumptions, no WorldSim source patch stacking.

## Future stage after B2-B3F

If crash-scope passes: a separately scoped B2-B3-100Y trial of annual bundle with complete provenance, **per-year full-view metadata scaling**, mixed event/Deep/material queries and exact oracle, then 1000Y staged all-kind reconstruction and true persisted bytes. Include a sequence-aware event adapter and time/place queries before any final architecture choice. Preserve UNKNOWN unsupported biology/human history and do not treat synthetic fixture as canonical planet.

**All authority gates remain closed**: `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
