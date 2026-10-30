# R6 INT10K E2-C1-R4 — manifest schema preflight bug; corrected V2 runner prepared

Date: 2026-10-30. Source: FAIR operator terminal output, source code inspection of the exact original 1000Y writer and preparation/test of the V2 script in current chat. **No actual R4 numerical qualification has run yet.**

## Local source commit

FAIR `r6/e2c1-frontier-projection-r1-fair` R3 source committed successfully as **`2c71370eb9a959c78121ce1c88ec8e9e37187787`**, with exactly 3 files (one modified R6 source, two new regression suites), 125 lines added and 4 removed. This is a FAIR-local commit, **not** pushed/published to GitHub; GitHub documentation branch remains separate. The historical geometry parent is `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`. Git author used explicit per-command identity (avoid global config on shared FAIR).

## Failed R4 first attempt after source commit

- The original R4 script SHA256 `eb9ed93973c9c61911b3f56b455396fa59fd595a0f02c8de211eba84f0a1a177` was pinned and executed.
- Output `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_R4_3Y10Y_lpvnnze4`.
- It raised `TypeError: list indices must be integers or slices, not str` in `check_preflight()`, `ix = oracle_manifest["members"]["INDEX.jsonl"]`, then `E2C1_R4_GATE=BLOCKED`. **This is an incorrectly authored runner; the source commit, E2-C1-R3 PASS and 1000Y evidence are not implicated. No 3Y/10Y simulation or results were obtained.**
- Prior earlier blocked attempt `INT10K_E2C1_R4_3Y10Y_mhtk8c0p` stopped before same numerical tests because Git author identity was unset; leave both blocked directories untouched.

## Root cause and corrected runner

The original 1000Y writer `arcana_int10k_1000y_fair_after_geometry_fix.sh`, inside its `run_1000y.py` heredoc, creates:

```python
members=[{'path':p.name,'byte_length':p.stat().st_size,'sha256':file_sha(p)}
         for p in sorted(OUTPUT.iterdir()) if p.is_file()]
manifest={'schema':'ARCANA_INT10K_1000Y_OBSERVE_MANIFEST_V1',
          'completion':'ALL_1000_YEARS_AUDITED','members':members,
          'classification':report['classification']}
```

Thus `members` is a **list**. R4 V1 incorrectly expected dict keyed by filename. R4 V2 selects exactly one list entry where `entry.get("path") == "INDEX.jsonl"`, rejects absent/duplicate names, then keeps the existing `byte_length` and SHA256 checks. No source/physics/record-index/oracle comparison changes.

New script artifact `arcana_e2c1_r4_3y10y_committed_gate_v2.py` SHA256 **`f0a1aa14f1908841154ed7da9e36c975de28077dbe4ef58f0cafe8554e268ec2`**, package `ARCANA_E2C1_R4_V2_FAIR_PACKAGE.zip` SHA256 `eebd3de38755f4e16e7f6e0cbc4b2c48a1580ae0efde6f5ac466d0e67a0f33a8`. Prepared and Python compiled in this conversation environment, with mocked check_preflight: valid original-list manifest PASS, missing INDEX REJECTED, duplicated INDEX REJECTED. **Not copied onto FAIR or executed on FAIR.** V2 differs by 5 added lines and exactly one replaced line.

## Next gate (operator)

1. Transfer V2 script to `~/HPC-POMDP/Arcana/` on FAIR, keep original v1 unchanged, check SHA256 `f0a1aa14...`.
2. Activate `arcana-r6-linux`, execute `python arcana_e2c1_r4_3y10y_committed_gate_v2.py` in that directory. Do NOT recommit, alter source, push, merge, repeat R1-R3 or 1000Y. The runner validates existing R3 manifest/source pins, original 1000Y oracle manifest/index, and clean child commit before running.
3. Expected **only if actual FAIR result**: `E2C1_R4_GATE=PASS_EXACT_3Y10Y_HISTORY_INDEPENDENT_ORACLE`; check `E2C1_R4_YEAR=3` and `E2C1_R4_YEAR=10` with `ORACLE_BY_KIND=EXACT_PASS`, `FRONTIER=EXACT_PASS`, `BALANCES=EXACT_PASS`. A BLOCKED result requires reviewing new isolated traceback, no patch stacking.
4. After a verified PASS, independently rehash the R4 manifest, review all source and original evidence integrity, then mark E2-C1 qualified **only for the synthetic scope**. E2-C2 remains separate: append-only deposit deltas + existing B0 HistoryStore, exact all-years material/provenance/Deep reconstruction.

No WORLD_HISTORY production authorization, GEODYN-2B forward authorization or F2-B solver/scientific promotion.
