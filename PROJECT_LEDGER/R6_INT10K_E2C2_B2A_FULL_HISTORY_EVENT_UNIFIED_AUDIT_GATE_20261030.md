# ARCANA R6 — E2-C2-B2-A full original HISTORY and event/Unified authentication gate

Date: 2026-10-30. Status: **PREPARED_NOT_RUN_FAIR**. Follows operator-proven E2-C2-B1 V2 exact virtual reconstruction PASS, detailed in `PROJECT_LEDGER/R6_INT10K_E2C2_B1_V2_FAIR_EXACT_VIRTUAL_DELTA_PASS_20261030.md`.

## Why a new gate is necessary

B1 proves 1001 year-by-year regional snapshots reconstruct byte-exact from 9,055,299 bytes of virtual initial anchor and append-deposit/full-value deltas (original canonical snapshot payloads 1,774,346,125 bytes, ratio 0.005103). B1 did **not** authenticate all original standalone events or all Unified Deep steps, did not compute full HISTORY file hash, did not write persisted storage or integrate typed B0 HistoryStore. Original history has 58,000 standalone REGIONAL_EVENT and 1000 UNIFIED_STEP; 8000 standalone events have **null external time_year**. We must close archive provenance and representation gaps prior to B2-B schema design.

## Prepared B2-A artifact; verify before use

- Script: `arcana_e2c2_b2a_full_history_event_unified_audit.py`, SHA256 **`ac53f0d004bcda04dae6c78bb8aaa4c9e771759ba9c781a140e85684a09293dd`**.
- ZIP: `ARCANA_E2C2_B2A_READONLY_FAIR_PACKAGE.zip`, SHA256 `fa74af4d8745dbf70388eedb56bd227e7d76b96cbec94cae9d798e075f8db7a1`. README SHA256 `efd098919f39d539d26acd99eeb218d59bb9a3d8a7f115e44d3bf52b3c1a83ce`. These are attached chat artifacts, not in GitHub source tree and **not yet run on FAIR**.
- Python syntax compile PASS; standalone selftests PASS on locally created *small artificial archive* (two years, six events) including rejecting corrupted original history, a disagreement between nested and standalone event payloads, and a falsified event time in the index/envelope. Does **not** assume that the synthetic fixture predicts the actual FAIR result.

## Full FAIR verification design

1. Pinned original 1000Y MANIFEST SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`, list-shaped members; INDEX file SHA256, HISTORY byte length, all 61001 index identities and contiguous offsets with original count checks.
2. Sequentially read all 1,916,080,917 bytes of original HISTORY once, hash entire byte stream and compare to original manifest member SHA256. This is *not* a new solver run or storage rewrite. Bound memory to max JSONL row (late snapshot ~3.5MB), rather than holding 1.9GB.
3. Parse and reserialize canonically each 58000 standalone REGIONAL_EVENT, 1000 UNIFIED_STEP, and 1000 REGIONAL_YEAR_RECORD; verify envelope equality with index (sequence/kind/time/payload_sha), JSON canonical bytes and payload SHA256. For 1001 large REGIONAL_SNAPSHOT rows, rely on independently verified A3/B1 per-payload SHA and authenticated full-file raw hash in B2-A; no second decode of 1.77GB snapshots.
4. Group events by original annual emission interval for *context only* (not their intrinsic time). For each of 1000 years, verify exact multiset of standalone events vs `REGIONAL_YEAR_RECORD.events` nested values, so payloads cannot be omitted or silently doubled. Check ordered per-record global sequence in INDEX. Count standalone kinds, 50000 dated events and 8000 index-null-time events. Verify original writer's index time extraction: `event.get('time_year', event.get('detected_at_year'))`, **never derive missing time_year from context as fact**. The code permits route-change external events before the annual regional record but after Unified step (source-compatible).
5. On verified FAIR PASS print `E2C2_B2A=PASS_FULL_HISTORY_SHA_AND_EVENT_UNIFIED_COVERAGE`. Otherwise BLOCKED with exact reason; do not patch source or original archive to pass.

## Exact operator command

```bash
cd ~/HPC-POMDP/Arcana
sha256sum arcana_e2c2_b2a_full_history_event_unified_audit.py
python arcana_e2c2_b2a_full_history_event_unified_audit.py --self-test
python arcana_e2c2_b2a_full_history_event_unified_audit.py
```

## Next architecture gate, after *actual* PASS

B2-B must design **typed** B0 HistoryStore append transactions for immutable per-year envelopes and deltas: stage parent/checkpoint/time and space support; preserve all nine deposit fields incl exact event IDs, ordered append offsets, original historical source and SHA lineage; changed nondeposit fields with exact float values; retain separate `REGIONAL_YEAR_RECORD`, standalone event stream, `UNIFIED_STEP` Deep/mechanics/thermal/hydrology, unknown and no-date semantics. Introduce no unapproved new data/authority in synthetic archive; never persist fabricated biological or human history. Query/reconstruction from authenticated anchor plus sequential deltas and snapshots must match all 1001 original payload hashes; trust B0 committed-view transaction rather than writing arbitrary dicts directly.

**Authority:** scoped noncanonical synthetic engineering only. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
