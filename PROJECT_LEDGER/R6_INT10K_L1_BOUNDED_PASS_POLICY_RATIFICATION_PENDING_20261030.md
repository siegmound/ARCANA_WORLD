# ARCANA R6 — R2-L1 bounded PASS; 10k service/cadence authorial decision pending

**Recorded:** 2026-10-30. **Provenance:** user-supplied FAIR report `docs/arcana/R6_RUNTIME_R2_L1_FAIR_20261030.md` pasted into this conversation. The GitHub documentation session has **not** mounted or independently rehashed the complete FAIR worktree/evidence root. Statements below are **FAIR_OPERATOR_REPORTED**, not independent GitHub checkout tests or long-run evidence.

## Qualified outcome and immutable references

`R2_L1_BOUNDED=PASS_LAUNCHER_SOURCE_AND_RESUME_PARITY` — 242 tests PASS in 26.52 s, comprising 228 previous tests +14 launcher tests. Nine supervised SIGKILL hooks with exact pre/post B0 visibility recovery and independent-process continuation to Y10; 20 query snapshot witnesses, 3Y/10Y direct/split exact. For plan1000, original 184/611 logical record prefixes and complete `HISTORY`/`INDEX` bytes reproduced, including NULL event-source times. 10000-planned horizon short tests retained same-plan numerical and causal parity. No new 1000Y/10k/100k physical trajectory ran. Numerical R1/R2/REC1 source, original FAIR archives and prior manifests preserved; no commit, push, reset or merge.

FAIR branch reported `r6/runtime-copy-r1-fair`, git HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`, intentionally dirty local R1/R2/REC1. New L1 files:
- `scripts/r6_runtime_r2_launcher.py` SHA256 `7844b40dd68d879850de4500370aa6418009496747e3d04634556880836b6dd9`.
- `tests/test_r6_runtime_r2_launcher.py` SHA256 `9eac97317bdd84889f0b5cecd894706971cd02cb884112ec718a07bfe0ed814d`.
- Original REC1 manifest SHA256 `1bff4a390a702376e396425eb4e28e51d2975077c14f1f7de59777d210bda158`.
- New FAIR evidence root `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R2_L1_20261030_01`; authoritative final receipts in `qualified/`. The recommended prebuilt candidate contract SHA256 reported as `163a4557c3956baf133c25ae039da37c91a362a1388eab55b829eff78f2ebcc5`, but **no contract has been authorially selected or executed**.

The launcher has opt-in `prepare` (does not advance numerics) and `run` (needs explicit R2/REC1 flag, contract SHA, segment years, output path and resume). `compact_query` retains all ordered causal frames, event/material provenance, regional annual and Unified/Deep values and reconstructs full exact-year snapshots when requested; `legacy_full` additionally materializes full legacy `HISTORY` and `INDEX`. No 10k legacy materialization is permitted by default. `journal_commit_interval_years=checkpoint_interval_years` because the only qualified B0 visibility step commits a paired durable journal prefix and coupled numerical checkpoint. Periodic journal `fsync` (1/5/10 years) is staging only, NOT B0 publication or recovery eligibility.

## Reported quantitative bounded sample

Ten simulated years under **planned 10000Y**, with CP gap4 / fsync1, completed numerical advance+compact 0.303781 s, three paired commits 0.236686 s, snapshot/full legacy service 0.151927 s, total process launch-to-exit 1.020910 s. Individual isolated anchor CP sizes are y101 529,942 B; y501 1,944,172 B; y751 2,827,818 B; seal/validation costs increase with history age. This short sample does not provide controlled 10k speedup or tail/resource guarantee. Three staged-fsync configurations in short samples: 1-year extra fsync 0.027209s, 5-year 0.005785s, 10-year 0.003162s; stage fsync has no impact on qualified resume point. Five O(D) material/deposit scans and live encoded frames persist; REC1 chain loader eagerly retains decoded checkpoints.

## Checkpoint/cadence comparison (source report estimates, not actual 10k)

| Paired CP+B0 interval | Pure periodic CP count | Maximum rework after latest committed checkpoint | Estimated checkpoint disk | Estimated retained decoded checkpoints heap |
| --- | ---: | ---: | ---: | ---: |
| 250 model years | 40 | 249 model years | 731.69 MB | 1506.77 MB |
| 500 model years | 20 | 499 model years | 374.68 MB | 771.59 MB |
| 1000 model years | 10 | 999 model years | 196.18 MB | 403.99 MB |

**Important caveats:** source projections use an affine size fit and ~2.0593 Python heap / encoded checkpoint ratio; not site allocation, hard memory bound, 10k measurement, nor full-process RSS. During live journal and query these heaps can overlap live R2 journal, replay buffers and process instrumentation. No *committed T0 checkpoint pair* exists in L1; first-prefix interruption may require a fresh run in a new directory. Intervening staged fsync preserves bytes but grants no restart eligibility. Older conditional 10k hot estimates 10.5–23.3 minutes, 1.9–3.0 GiB live journal/solver, exclude checkpoint chain and full required services.

## User-facing recommendation / still NOT ratified

Recommended **candidate** for a first 10k *synthetic engineering* experiment:
- Historical service `compact_query`: complete compact lossless history + on-demand exact-year queries, no eager whole-history legacy export.
- Paired native checkpoint and B0 committed journal at years 250,500,...,10000, with coupling, clocks, source config SHA and committed prefix matched; recovery rework up to 249 years after a committed CP.
- Staged journal fsync every 10 model years (does not improve RPO; small measured isolated overhead in bounded trial).
- Define query years explicitly in selected run contract and decide on early checkpoint/T0 start exposure. Do not invent query years from previous 1000Y milestone schedule, and do not use default unrequested full legacy export.
- Condition: FAIR actual job/scheduler/site and storage quota, memory and process-tree RSS budget, 10k scenario forcing C028 0.0001m/y (total 1.0m) / C029 zero, checksum of real prebuilt contract, source/evidence integrity, and acceptance of checkpoint decoded-chain memory impact.

This is **NOT an implicit authorial ratification** of CP250/fsync10/service or chosen queried years. More conservative CP500/CP1000 reduce memory at cost of longer rework. If site memory allocation uncertain/insufficient, checkpoint cadence choice should remain BLOCKED or prefer CP500 with a newly reviewed contract. A new CP250/fsync10 authorial YES would settle the policy choice only, not automatically authorize executing 10k.

## Next verification after ratification, before explicit long-run authorization

1. User selects archive mode, paired CP/B0 interval, staged fsync interval, recovery rework goal and queried years; record parameter decision in new ledger entry and exact selected prepared contract bytes+SHA, fail closed on unknown.
2. Recheck live FAIR context, site policy, source/REC1/L1 SHA, original E0 pins and 242 tests, disk quota and workload allocation, and all source/contract identities. Confirm process memory headroom, especially CP250 decoded chain + live journal overlap. Do not assume cgroup unlimited means reserved resources.
3. Refresh `R2_10K_PREFLIGHT` to READY only if this service/cadence and actual operational context are verified and no further blocker discovered. No code patch if existing launcher sufficient.
4. **Separate user permission** for one 10k numerical trajectory. Only then launch in a new output/evidence directory without automatic retries; output CPU user/system, effective cores, RSS, full logical/allocated byte growth by domain, 100Y windows, checkpoints, B0 committed prefix, exact next-year segmented restart and query checks. Preserve original evidence, no push/commit.
5. No production, canonical or scientific authority promotion.

```yaml
R2_REC1_BOUNDED: PASS_FAIR_OPERATOR_REPORTED
R2_L1_BOUNDED: PASS_LAUNCHER_SOURCE_AND_RESUME_PARITY_FAIR_OPERATOR_REPORTED
R2_10K_UPLIFT: RATIFIED_C028_0_0001M_PER_YEAR_C029_ZERO
R2_10K_PREFLIGHT: BLOCKED_SERVICE_AND_CHECKPOINT_CADENCE_NOT_RATIFIED
R2_10K_POLICY: RECOMMENDED_COMPACT_QUERY_CP250_FSYNC10_NOT_RATIFIED
R2_10K_EXECUTION: NOT_AUTHORIZED_NOT_RUN
R2_100K_EXECUTION: NOT_AUTHORIZED_NOT_RUN
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```
