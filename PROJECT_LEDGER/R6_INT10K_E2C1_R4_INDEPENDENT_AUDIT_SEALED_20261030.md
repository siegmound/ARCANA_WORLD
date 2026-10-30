# ARCANA R6 — E2-C1 R4 independent audit and bounded synthetic qualification SEALED

Date 2026-10-30. Independent operator-executed FAIR read-only verification after E2-C1 R4 V2 numerical qualification.

```text
E2C1_R4_INDEPENDENT_EVIDENCE_AUDIT=PASS
E2C1_R4_MANIFEST_MEMBERS= 4
E2C1_R4_3Y10Y_ORACLE=EXACT_PASS
E2C1_R4_SOURCE_COMMIT=VERIFIED
E2C1_R4_ORIGINAL_ORACLE=UNCHANGED
```

Evidence root (already known): `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_R4_3Y10Y_tqei5685`; exact four manifest members were `PARITY_R4.json`, `PYTEST_R4.log`, `SOURCE_COMMIT.txt`, and `SOURCE_SHA256.json`. The operator script read each `FILE_MANIFEST_R4.json` member, checked byte lengths and SHA256; validated `PARITY_R4.json` status `PASS_3Y_10Y_EXACT_ORACLE_AND_SEGMENT_RESTART`, 3Y 1+2 /184 records, 10Y 5+5 /611 records, exact within-kind oracle, terminal frontier and balances, local source commit match, clean worktree, and unchanged original 1000Y archive `MANIFEST.json` SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.

**Source qualification anchor:** local FAIR source Git commit `2c71370eb9a959c78121ce1c88ec8e9e37187787` on branch `r6/e2c1-frontier-projection-r1-fair`, parent `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`. This is *local to FAIR and not confirmed pushed to GitHub*. GitHub `PROJECT_LEDGER` branch is a separate docs-only lineage. Do not infer public availability of engine patch from this document.

**Closed gates:** E2-C0/B/C profiling; E2-C1-R1 valid-input oracle/parity benchmark; E2-C1-R2 negative mutation diagnostic (a genuine validation regression found); E2-C1-R3 remediation of excluded-history fail-closed semantics (104 tests, 3×7 one-year checkpoints and 61-record/year stream hash parity, net 3.84/3.45/5.98% lower median wall than original at Y101/501/751); E2-C1-R4 dedicated history-independent 3Y direct vs 1+2 and 10Y direct vs 5+5 against immutable original by-kind per-record SHA256 and exact checkpoints, balances. 104 tests PASS and independent R4 four-member SHA/size audit PASS. The original E2-C1 R2 bug is fixed for the tested excluded-history invalid-JSON cases, not formally proven for arbitrary custom Python object semantics.

**Decision:** `E2C1_QUALIFIED_SYNTHETIC_SCOPE=PASS`. No need for further E2-C1 reruns; preserve original evidence, all failure roots, R3 and R4 results. Explicit limitations: 3×3 noncanonical synthetic fixture, original 1000Y *used as oracle not regenerated*, per-kind rather than global cross-kind event interleaving, hash-only consumer not full 1.916GB JSONL write, no planetary science or broad query correctness proof. Speedup not extrapolated to a world simulation. E2-C1 closes **only this engineering scope**.

**Next active gate:** E2-C2-A READ-ONLY inventory of `REGIONAL_SNAPSHOT`, `REGIONAL_YEAR_RECORD`, `REGIONAL_EVENT`, `UNIFIED_STEP` historical source fields, material deposit IDs/ordering/uncertainty, original index structure and query/retention/HistoryStore mapping. Design full-field delta & authenticated anchor materialization without discarding Deep/environmental/biological/civilizational historical data when supported. See `PROJECT_LEDGER/R6_INT10K_E2C2_LOSSLESS_ARCHIVAL_DESIGN_GATE_20261030.md`.

**All authority gates unchanged:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
