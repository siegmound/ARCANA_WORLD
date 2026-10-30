# ARCANA R6 INT10K E2-C1-R4 — FAIR 3Y/10Y history-independent oracle PASS

2026-10-30. **Evidence level:** operator-provided stdout of existing checksum-pinned runner; source artifact FAIR output has not been fetched by GitHub documentation writer nor independently post-audited in this turn. **Status:** `E2C1_R4_GATE=PASS_EXACT_3Y10Y_HISTORY_INDEPENDENT_ORACLE`; source commit locally sealed but not remotely pushed; archival/production authority not changed.

## Exact source and evidence

- Runner V2 SHA256 as checked on FAIR: `f0a1aa14f1908841154ed7da9e36c975de28077dbe4ef58f0cafe8554e268ec2`.
- Local source commit `2c71370eb9a959c78121ce1c88ec8e9e37187787` on FAIR `r6/e2c1-frontier-projection-r1-fair`; parent `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`. Commit modified exactly the regional frontier-projection code and two dedicated R1/R3 tests (125 insertions, 4 deletions); **no GitHub source push**.
- Success evidence directory `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_R4_3Y10Y_tqei5685`.
- Original untouched 1000Y reference `INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y`, pinned `MANIFEST.json` SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`; runner V2 preflight also verifies `INDEX.jsonl` declared byte_length and SHA256 in list-shaped manifest `members`.
- Previously blocked roots `INT10K_E2C1_R4_3Y10Y_mhtk8c0p` (Git identity/commit missing) and `INT10K_E2C1_R4_3Y10Y_lpvnnze4` (V1 runner list-vs-map error) remain preserved, not overwritten.

## FAIR output (operator, verbatim main markers)

```
E2C1_R4_SOURCE_AND_R3_EVIDENCE=PINNED
104 passed in 1.59s
E2C1_R4_YEAR=3 SPLIT=1+2 ORACLE_BY_KIND=EXACT_PASS FRONTIER=EXACT_PASS BALANCES=EXACT_PASS RECORDS=184
E2C1_R4_YEAR=10 SPLIT=5+5 ORACLE_BY_KIND=EXACT_PASS FRONTIER=EXACT_PASS BALANCES=EXACT_PASS RECORDS=611
E2C1_R4_EVIDENCE_MANIFEST=PASS
E2C1_R4_GATE=PASS_EXACT_3Y10Y_HISTORY_INDEPENDENT_ORACLE
```

## Scope of proof

The actual R4 V2 runner, reviewed in chat, evaluates the **history-independent** execution, not merely the existing legacy short-reference tests. For `(years, split_at)=(3,1),(10,5)`, it checks exact per-kind ordered payload SHA256 streams against 1000Y archive index prefix for both direct and segmented 1+2 / 5+5 runs; exact terminal checkpoint dictionary equality, subsurface-by-support dictionaries and integrated mass/Deep balances; source SHAs, clean one-child commit, pinned R3 manifest, original 1000Y manifest and `INDEX.jsonl` integrity; 104 targeted pytest cases. Count includes initial `REGIONAL_SNAPSHOT` and record/event kinds, thus 184 at 3Y and 611 at 10Y.

**Important nuance:** R4 checks event SHA order **within each kind**, NOT global cross-kind stream interleaving: original 1000Y advanced yearly while 3Y/10Y direct calls group phases differently. No evidence here that cross-kind global interleaving is byte-identical, nor that physical laws/coupling beyond the synthetic 3×3 fixture are qualified.

**Next gate:** read-only *independent* rehash of all `FILE_MANIFEST_R4.json` members (list `members` with `name`, `bytes`, `sha256`), validate `PARITY_R4.json` status `PASS_3Y_10Y_EXACT_ORACLE_AND_SEGMENT_RESTART`, expected two cases and counts, source commit matches `2c71370e...`, immutable 1000Y manifest remains identical. Do not rerun 1000Y or source tests if current checks suffice. If audit passes, mark E2-C1 qualified for the bounded synthetic engineering scope; then start **E2-C2 archival design** using B0 `HistoryStore`, retention/replay/query with exact all-year snapshot/material/Deep/provenance reconstruction and no loss of UNKNOWN.

**Authority unchanged:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
