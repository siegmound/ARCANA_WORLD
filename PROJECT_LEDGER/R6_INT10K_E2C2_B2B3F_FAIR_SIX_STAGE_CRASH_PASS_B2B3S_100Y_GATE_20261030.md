# ARCANA R6 — B2-B3F FAIR crash/recovery PASS; B2-B3S 100Y historical query and view-growth trial prepared

Date 2026-10-30. FAIR user-pasted stdout of exact SHA-pinned script. Synthetic fixture and isolated scratch stores only.

## B2-B3F actual FAIR decision

**`E2C2_B2B3F=PASS_SUBPROCESS_CRASH_RECOVERY_AND_SOURCE_ORACLE_6_STAGES`**.

- Script `arcana_e2c2_b2b3f_crash_recovery_scratch.py`, SHA256 operator verified `3596da70bb63b5e148335bc4f97bafb80700a0849c6974ef877cea9b744f0dbc`.
- Python pure selftest PASS; actual B2B1 typed roundtrip PASS; original source y0..y2 payloads SHA-pinned; isolated `HistoryStore` scratch root and six real separate child-process interruptions (exit code **79** each). Not a power-loss or filesystem durability test.
- `before_publication`, `after_publication`, `before_commit`, `before_visibility_switch`: all four **BEFORE** the CURRENT read-view switch. Fresh-open deterministic rollback validated. No uncommitted year2 state exposed to pinned old reader; safe retry gives complete oracle.
- `after_visibility_switch`, `during_cleanup`: both **AFTER** linearization/commit. Fresh-open deterministic completion validated; idempotent duplicate year2 append, no new duplicate historical state or event rows.
- All six stages: `crashed_process_exit=79`, `reopen_recovery=PASS`, `pinned_old_view=PASS`, `post_recovery_replay=EXACT_PASS_3_SNAPSHOTS_116_EVENTS`, `idempotence_or_retry=PASS`, `active_journals_after_recovery=0`. Each final scratch store 324,555 bytes and 12 files. No active journals, all scratch roots automatically removed.
- Measured child+recovery seconds (in stage order): 0.517437, 0.506688, 0.510104, 0.515247, 0.507842, 0.508382. Single-run timing only, not throughput proof.
- Original 1000Y archive and FAIR engine source left unchanged. This closes **process-crash** transaction boundary qualification on a two-year synthetic bundle; does NOT establish power-cut durability, long-history scaling, native event query, arbitrary corruption recovery or canonical world history production.

## Original source/canon constraints stay immutable

- FAIR source child HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787` (local, not confirmed pushed); original 1000Y manifest SHA `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.
- A3 exhaustively verified 1001 original regional snapshots/deposit append, B1 reconstructed 1001 snapshots SHA exact virtually, B2A full original 1.916GB HISTORY SHA plus 58000 events and 1000 UNIFIED Deep PASS; B2B0 source typed contract, B2B1 174 typed samples, B2B2 3Y10Y real transactional two-variant scratch PASS.
- At B2B2 10Y, B annual bundle occupies 1,591,834 bytes and 36 files vs A per-event 2,316,406 bytes and 626 files, with B scratch measured writes 0.404412s vs A 2.700833s. Thus B is **leading candidate for additional scale/query tests only**. No 100Y or full 1000Y persistent archive claims.

## New B2-B3S **100Y bundle/query/metadata-growth** gate: prepared, not executed on FAIR

- New script `arcana_e2c2_b2b3s_100y_bundle_query_scale.py`, SHA256 **`cf58191d62fd41091ea1cc217dc45182509457bdc07886cc9e62352f33fa3324`**.
- Zip `ARCANA_E2C2_B2B3S_100Y_FAIR_PACKAGE.zip` SHA256 **`4a574b828a6abb6998f596abcef636dd93904a7cec3e923bece5cca8d77f45c5`**, README SHA256 `05a53fafbf59faa485e560b78db779ada1d6b033286b76e265e8cb2b250ab8da`. Chat artifacts only, not FAIR yet.
- New script Python compile, pure negative query/selftest PASS; ZIP member CRC and content integrity PASS in chat runtime. These are not proofs of 100Y FAIR execution.
- Three unchanged helper modules required in FAIR directory: B2A SHA `ac53f0d004bcda04dae6c78bb8aaa4c9e771759ba9c781a140e85684a09293dd`, B2B1 SHA `539e18d5e8403e1f61525749afa6e0ab1c3b082efc1d94c5664e54d4667ce2ab`, B2B2 SHA `70ba607096e2477faff4f879f6471a1e252900944f4f47f0c270072168d3c9ba`. Source git and original manifest pinned by helpers.
- Reads original Y0..Y100 snapshots/yearrecords/UNIFIED/deep/external events with per-envelope SHA, writes **one isolated ephemeral /tmp B0 HistoryStore** with 101 annual parent-view-guarded commits for B bundle variant, then reopens and reconstructs original 101 regional snapshot SHA bytes and exact 100 annual/UNIFIED, 5800 external events, 800 source NULL timestamps. All original global sequences retained; no new source times inferred.
- Demonstrate a **prototype source-order-aware query** through typed `HistoricalSnapshot` bundle records (NOT native `HistoryQueryService.event_at`): query 100 annual bundles; selected years 0/1/10/25/50/75/100 by two cells; external event kinds, source/destination cell and literal explicit `time_year`; preserve 8 null/year diagnostics separately from contextual annual grouping. Retrieve exact Deep inventory per material volume and source SHA, do not invent missing biology, fauna, flora or populations; outside cell and outside time fail closed.
- Measure on-disk bytes across all buckets including read-view manifests, 101 view-visibility guards, write seconds by windows 0–10, 11–25, 26–50, 51–75, 76–100, full view-manifest byte growth, close/reopen query seconds and rough RSS. No sample can justify simple scaling to 1000Y (full-membership view files lead to quadratic cumulative membership metadata).
- Script **has not run on FAIR**. Expected marker ONLY after operator output `E2C2_B2B3S=PASS_100Y_BUNDLE_STORE_SOURCE_QUERY_AND_VIEW_GROWTH`. All scratch store files automatically removed. No physical simulation execution, source commit/push or persistent archive built.

## Next if B2-B3S actually succeeds

Adjudicate the *measured* 100Y read-view metadata growth; consider page/index strategy for long-lived B0 query without full view rewrite on each step; build independently reviewed sequence-aware typed query adapter and tests (including status UNKNOWN/MISSING_TIMESTAMP, material distribution, Deep, plus future biology/fauna/flora and humans where actual providers exist). Only afterward design staged whole-1000Y ingestion with separate scratch budget and independent complete source-envelope SHA oracle. NO canon production or scientific gate promotion.

**Authority flags unchanged:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
