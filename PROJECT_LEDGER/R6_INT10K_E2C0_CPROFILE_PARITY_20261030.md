# INT10K E2-C0 — FAIR single-year cProfile, 2026-10-30

Authority: operator-reported FAIR logs, not an independent fetch of the FAIR .pstats files. Scope: NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY, source FAIR-local geometry commit 9dce77b5d65d4301d2145f9ad527b8efee0fe96d; no World History production/seal.

FAIR profile directory: /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C0_PROFILE_Piy2PjHo. Files reported: PROFILE_YEAR_101.txt/.pstats, PROFILE_YEAR_501.txt/.pstats, PROFILE_YEAR_751.txt/.pstats, PROFILE_REPORT.json. Confirm existence and hashes from FAIR when needed.
Original 1000Y oracle: /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y; MANIFEST SHA256 e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a.

Status: ORIGINAL_EVIDENCE_INTEGRITY=PASS; E2_C0_REFERENCE_PARITY=PASS. Replay one year each from sealed frontier checkpoint y100, y500, y750, and compare 61 record-kind + canonical-payload SHA256 pairs in exact order to original history for years 101,501,751; all three PASS. The integrity/unchanged-source checks also PASS per user log.

| replay year | wall s | process CPU s | consumer SHA s | records | json.dumps cumulative s | json.loads cumulative s | approximate JSON share |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 101 | 0.080281 | 0.080271 | 0.004160 | 61 | 0.051 | 0.012 | 78.8% |
| 501 | 0.202521 | 0.202520 | 0.013361 | 61 | 0.134 | 0.040 | 86.1% |
| 751 | 0.279157 | 0.279148 | 0.019238 | 61 | 0.187 | 0.055 | 87.1% |

Key observation: json.dumps exactly 110 calls/year, json.loads exactly 12/year in all three profiles. Increasing time therefore comes predominantly from larger serialized state, not increasing call count. json.encoder.iterencode ~0.050/0.133/0.186 s and decoder.raw_decode ~0.012/0.039/0.054 s. SHA256 C/OpenSSL exclusive ~0.002/0.007/0.009 s. The hash-only no-write consumer time ~0.004/0.013/0.019 s is a minority of cost.
Nested/overlapping inclusive cProfile timings: advance_region ~0.013/0.058/0.084 s (includes JSON clone); verify_regional_checkpoint ~0.016/0.034/0.046 s; verify_history_independent_checkpoint ~0.012/0.031/0.042 s; seal_history_independent_checkpoint ~0.004/0.013/0.019 s. Unified numerical run_unified_microdomain ~0.021/0.020/0.020 s (stable). Do not add the listed overlapping parent times. 56,844 to 106,894 function calls, reflecting larger deposit collections.
Source parent inspection: regional_geological_evolution.advance_region clones state with json.loads(_canonical(dict(state))); each annual snapshot performs json.loads(_canonical(cells)); checkpoint seal/verify also serializes growing frontier. Older index proof: at y100/500/1000 snapshots have 1100/5500/11000 deposits, comprising 97.31/99.46/99.73% of snapshot bytes; 92.6% of 1.916 GB history is snapshot copies. The snapshot duplication is proven; precise phase-exclusive timing still requires direct caller analysis.

Measurement limits: cProfile adds overhead; the callback only computes hashes, does not write the same JSONL bytes; values must not be substituted for unprofiled 1000-year wall. CPU/wall ~100% means one busy CPU equivalent, not the entire 64-core FAIR host. Host has 2x Xeon Gold 6530 (64 physical,128 SMT), 4 NUMA nodes, 1TiB RAM, 2x RTX 5090; no GPU involved. Permission on shared host remains separate.

NEXT: E2-C0-B read-only direct caller attribution using saved PROFILE_YEAR_{101,501,751}.pstats via pstats.Stats(...).print_callers('dumps') and print_callers('loads'), and source path mapping; no new engine run. Identify incremental savings for regional clone vs snapshot clone vs frontier hashes, checkpoints, unified step and callback. Audit existing R6 B0 HistoryStore (store.py), retention.py, checkpoint.py, replay.py, query.py, transaction/recovery/read views. Design deterministic event/delta plus sparse sufficient checkpoint, preserve material identities, deposit ordering, mass/provenance/Deep/UNKNOWN; oracle-reconstruct all years 0..1000/all 9 cells, and 3Y/10Y parity before changing runtime. Do not clone/re-run 1000Y or replace existing B0 infrastructure.

Git reconciliation caution: GitHub docs branch/active branch commit is separate from FAIR-local 9dce77b5 branch. Source locks, original FAIL and PASS evidence remain immutable; all canonical forward/science authorization flags stay false.
