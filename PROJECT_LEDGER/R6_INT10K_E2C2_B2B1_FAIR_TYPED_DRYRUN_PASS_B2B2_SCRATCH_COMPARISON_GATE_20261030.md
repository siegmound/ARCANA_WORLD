# ARCANA R6 E2-C2-B2-B1 FAIR typed record dry-run PASS; E2-C2-B2-B2 scratch comparison prepared

**Date:** 2026-10-30. FAIR operator stdout, checksum-pinned script. `E2C2_B2B1=PASS_TYPED_SOURCE_ENVELOPE_DRYRUN_SAMPLED_YEARS`. Strict scope: sampled, synthetic 3×3 1000Y historical input; no B0 HistoryStore opened, no persistent history written and no new scientific authority.

## B2-B1 actual FAIR provenance

- FAIR script SHA256 confirmed: `539e18d5e8403e1f61525749afa6e0ab1c3b082efc1d94c5664e54d4667ce2ab` (`arcana_e2c2_b2b1_typed_dryrun_no_store.py`). `E2C2_B2B1_PURE_NEGATIVE_SELFTEST=PASS` (printed twice because self-test and full run), `E2C2_B2B1_TYPED_ROUNDTRIP_SELFTEST=PASS`, source original INDEX PINNED SHA256 PASS.
- Sampled years `1,2,10`: 58 original and 58 typed standalone events each, 8 source `time_year=null` each, original source `sequence` EXACT_PASS. Total **174 EventRecord, 4 DomainStateEnvelope, 9 HistoricalSnapshot typed records**, 24 null timestamps unchanged. Typed serializer roundtrips and source SHA checked, no `HistoryStore()` constructor, no disk writes.
- Real typed encoded byte lengths from operator: `events=221819`, `states=31960`, `temporal=362839`, `bundle_candidate=78978`. The latter represents an **alternative** annual event bundle, not an additional mandatory record to be persisted together with all individual events; the bytes cannot simply be added as a single model total without a mapping.
- Operator states `ALTERNATIVES=PER_EVENT_VS_ANNUAL_BUNDLE__UNDECIDED`. No native event_at source ordering was asserted; ordered adapter must use original indexed `sequence`, not `EventRecord.record_id`. The 8 null events/year are explicitly preserved without fabricated time.

**Adjudication:** `E2C2_B2B1_QUALIFIED_SAMPLED_TYPED_ROUNDTRIP=PASS`, not a store persistence, runtime atomics or complete 61,001-row proof. A3 append-only deposits, B1 1,001 exact regional snapshots, B2-A full original 1.916GB HISTORY SHA/58k events/1000 Deep, B2-B0 pinned B0 API are independently PASS.

## B2-B2 scratch comparison artifact (PREPARED_NOT_EXECUTED_FAIR)

- Script: `arcana_e2c2_b2b2_scratch_store_compare.py` SHA256 `70ba607096e2477faff4f879f6471a1e252900944f4f47f0c270072168d3c9ba`; ZIP `ARCANA_E2C2_B2B2_FAIR_PACKAGE.zip` SHA256 `fa1ccf709e74f08a5c0916ce93c77bb9d0d6a542cb5a448c68c386de944f53c8`; README SHA256 `a370294c72fa2799f756ba36242abbd277f1b5df0e81e1c9e9f9c4e04fec5a88`. These are conversation artifacts, not FAIR source files. Python compile, pure delta positive/negative selftest, ZIP integrity PASS in chat runtime; **actual B0 transaction runtime NOT tested here, not run FAIR**.
- Dependencies in same FAIR operator directory, strictly SHA-pinned: B2-A `arcana_e2c2_b2a_full_history_event_unified_audit.py` SHA `ac53f0d004bcda04dae6c78bb8aaa4c9e771759ba9c781a140e85684a09293dd`; B2-B1 `arcana_e2c2_b2b1_typed_dryrun_no_store.py` SHA `539e18d5e8403e1f61525749afa6e0ab1c3b082efc1d94c5664e54d4667ce2ab`, and exact source git child commit `2c71370e...` and seven module SHAs as recorded by B2-B0. No checkout modification.
- B2-B2 reads first 10 years via original SHA-pinned INDEX/record envelopes, checks all original snapshot/year/Unified/events hashes, and runs **four isolated temporary stores**: 3Y-A, 3Y-B, 10Y-A, 10Y-B. Variant A stores 58 `EventRecord` per year and two typed temporal record envelopes per year with yearly delta `DomainStateEnvelope`; variant B stores one `HistoricalSnapshot` annual bundle of ordered source events + full annual and Unified data, plus yearly delta `DomainStateEnvelope`. Both use year0 anchor.
- Per year actual B0 `HistoryStore.append_transaction(expected_parent_view_id=...)`; test pinned old view cannot see new state before release and new view can see it; test stale parent rejection. Re-open store, reconstruct 4/11 snapshot annual payloads from **stored** anchor+deltas and compare original canonical payload/sha; validate year/Deep and source event sequence, 8 null/year, 58 source event payload hashes. Measure all file bytes, view metadata, number of files, total write seconds and reopen/read seconds, then automatic `TemporaryDirectory` cleanup.
- **No physical solver run, original archive write, WORLD_HISTORY canon promotion, repo git commit/push or persistent prototype ingest**. Results will be output-only from `/tmp` scratch that is auto-deleted. The B2-B2 result is a 3Y/10Y benchmark, cannot establish 100/1000Y overhead or filesystem power-loss recovery; subsequent stage must explicitly test fault injection, 100Y size/runtime, event/query semantics before choosing persisted shape.
- Expected marker *only after FAIR execution*: `E2C2_B2B2=PASS_3Y10Y_ATOMIC_SCRATCH_STORE_COMPARISON`. On any failure inspect exact traceback before runner patch; do not patch WorldSim for test harness errors.

## Operator command

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate arcana-r6-linux
cd ~/HPC-POMDP/Arcana
sha256sum arcana_e2c2_b2b2_scratch_store_compare.py
python -B arcana_e2c2_b2b2_scratch_store_compare.py --self-test
python -B arcana_e2c2_b2b2_scratch_store_compare.py
```

**Permissions:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
