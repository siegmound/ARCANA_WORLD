# ARCANA R6 INT10K — Runtime Copy R1 1000Y exact FAIR result; quadratic cost remains

**Recorded:** 2026-10-30 Europe/Rome. **Authority:** user-supplied Codex/FAIR report text from local FAIR document `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK/docs/arcana/R6_RUNTIME_COPY_R1_FAIR_20261030.md`. The FAIR evidence directory and manifests were not fetched, rehashed or independently executed from this GitHub documentation session. This is a **reported synthetic engineering qualification**, not scientific/production authorization. Distinguish this updated outcome from earlier R1 bounded gate which was pending a full 1000Y candidate execution.

## Outcome

`R6_INT10K_RUNTIME_R1=PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP`. One-off authorized candidate 1000-year evolution completed naturally with exit 0. No application time/RAM/output/thread limit was introduced, and no extra solver, 10k run, engine commit/push or code change occurred after the candidate was selected. The optimization is **opt-in**, default disabled; on FAIR local branch `r6/runtime-copy-r1-fair`, based on `2c71370eb9a959c78121ce1c88ec8e9e37187787`, engine changes **uncommitted and unpublished** as of the user report.

The new runner `scripts/r6_int10k_runtime_r1_1000y.py` uses original source/input/oracle pins and annual segments with constant planned 1000 years. Every produced index/payload compared to original oracle in order, annual balances and frontier checked, original checkpoint schedule used. Original E0 inputs, source and archived 1000Y manifest unchanged.

Reported exact proofs:
- **61,001 ordered payload envelopes:** 1,001 REGIONAL_SNAPSHOT, 1,000 REGIONAL_YEAR_RECORD, 1,000 UNIFIED_STEP, 58,000 REGIONAL_EVENT.
- Whole `HISTORY` **1,916,080,917 B** and `INDEX` **10,685,396 B** are byte-identical in length and SHA to the prior original.
- Checkpoints at years **100/250/500/750/1000** byte-identical; water/solid/Deep, material identity, provenance and ordering exact; 8,000 event-source null timestamps preserved.
- Previous 141 focused tests and controlled seven-repetition y101/y501/y751 anchors pinned to unchanged measured source hashes.
- Evidence in FAIR `ARCANA_WORLD_EVIDENCE/R6/RUNTIME_R1_CANDIDATE_1000Y_20261030_01`: 82 manifest members; REPORT SHA256 `76dc09d0bf40e76540e9a5dc9f571b3ec946f370def3b6358b92aa7f19e3eef8`, MANIFEST SHA256 `3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b`. FAIR acceptance JSON SHA256 `1ea36053d25095e3a9897cb52ef30c88a8d05f58d674178e37231bfd16070313`.

## Performance reported

| Metric | Historical 1000Y original | R1 new 1000Y |
| --- | ---: | ---: |
| Loop wall seconds | 244.780960 | 214.125572 |
| Indicative relative wall reduction | — | 12.52% (1.143x faster) |
| CPU user / system seconds | — | 207.380428 / 2.500732 |
| Equivalent utilized CPU cores | approximately 1 | 0.98018 |
| Peak RSS | ~98.5 MiB (old reported sampling) | 125304 KiB, 122.37 MiB (VmHWM) |
| HISTORY logical bytes | 1916080917 | 1916080917 |
| INDEX bytes | see oracle | 10685396 |
| Final checkpoint | ~3.708 MB | 3708267 B |

R1 full output 1,938,809,781 logical B / 1,938,997,248 allocated B / 83 files. Pre-manifest wall 217.144785 s; final manifest generation and independent audit additional. Loop annual median/p95/max 0.208915/0.354151/2.008016 s. First 100-year window 6.744983 s versus last 100-year window 36.419843 s, confirming age-correlated growth. Detailed phase wall: engine including consumer 165.688599 s, additional outer checkpoint verification 30.671669 s, checkpoint byte encoding observation 12.284822 s; DO NOT sum overlapping stage/writer timers. Writer subcomponents: encoding payload 12.239689 s; payload SHA 1.015197 s; envelope/index encoding 13.339210 s; write+stream hash 1.921383 s; flush/fsync 4.434599 s. 128 NumPy threads observed + sampling thread, but effectively one CPU core utilized; no multi-core speedup claim.

The **12.52% full-loop comparison is indicative only**: one new full execution versus a historical run with differing measurement overhead. Controlled seven-repetition exact same-work y101/y501/y751 medians are 1.084x, 1.175x and 1.192x speedup (corresponding to 7.77%/14.91%/16.10% wall reduction). No memory or disk savings claimed.

## Fundamental remaining performance blocker

R1 `_clone_canonical_json` replaces JSON encode/decode with detached recursive copies for ordinary built-in JSON types, preserving fallback canonical behavior for exotic types, cycles, NaN and invalid historical payloads. It still **copies complete growing deposit state**, materializes full annual snapshots, serializes/verifies complete frontier, and traverses growing deposits for balances. Source and output remain byte-for-byte the original 1000Y legacy layout. With ~11 new deposits per year and D(y)=O(y), copies, scans and full snapshot output cost O(y) per year, O(Y²) cumulative. It is **impossible** to obtain asymptotically subquadratic full HISTORY output at fixed legacy canonical full snapshot cadence while requiring that same physical 1.916GB output for 1000Y; compact internal representation with reconstruction-on-demand is a separate unqualified candidate.

The B2-B3S 100Y alternative B annual bundle and earlier E2-C2-B1 exact virtual delta are useful **evidence for a future new logical representation**, not evidence that R1 now uses it, nor that B2B3S's input storage time is physical simulation time. The global R6 domain-independent adaptive retention direction is still design only.

## Next gate: R2 asymptotic runtime path, then integrated synthetic 10k

**Recommended engineering next step (proposal, NOT executed or authorized):** review an R2 opt-in hot path where immutable historical deposits and exact per-domain event/delta records are not repeatedly cloned or serialized in every computed annual step; maintain detached mutable frontier with safe ownership and exact reconstructible history. Full canonical regional snapshots must be generated **on-demand for oracle/query/restart validation**, not forcibly emitted/written at each time in the 10k experimental fast path. Preserve material IDs, old row ordering, mass/density, provenance, source timestamps including NULL, Deep, hydrology and model/source/config identities; retain all non-derivable numeric and coupled solver state. Incremental per-cell mass ledgers only when reduction order/precision can be proven equivalent; do not hide O(Y²) scans behind a writer or checkpoint. Test 3Y and 10Y direct/split, y101/501/751 anchored replay, complete original 1000Y reconstructed per-kind/source/hash against oracle with a changed candidate writer (not merely replay old data), 141+ negative tests including cyclic/NaN, crash/commit/query view integrity and measured wall/CPU/RSS/bytes. Keep an unchanged legacy mode for A/B comparison. If exact logical historical parity fails, preserve failure, do not patch-stack or claim speedup.

**User's requested next long-run target:** 10,000 synthetic integrated model-years, with observed end-to-end/loop wall, CPU user/system and utilized core equivalent, RSS peak, output logical and allocated bytes, file counts, checkpoint size/verification, domain event/stream counts and annual/100Y growth, genuine segmented restart, all source/input/authority guards. No global fixed application resource cap invented; FAIR actual site limits and authorization binding. 10k is **NOT authorized** by the previous 1000Y permission. Need exact reviewed configuration and planned duration, existing run-level uplift total 0.1m implies changed annual uplift when total duration changes, confirm domain validity and site job policy. Reusing the old full-snapshot format for a 10k run could imply order ~190GB HISTORY and hours of CPU under an unverified quadratic extrapolation, not a resource forecast or evidence to set a cap. Do not blindly launch.

Keep user's future priority: separate adaptive event/significance-driven sampling per domain and spatial scope after simulation, global causally consistent reconstruction and restart, plus exploratory 100k only after measuring 10k. Postpone B0 full-view manifest schema redesign until informed by measurements or needed to prove tested correctness.

## Authority / pending gates

```yaml
R6_INT10K_RUNTIME_R1: PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP_FAIR_OPERATOR_REPORTED
R6_INT10K_RUNTIME_R1_DEFAULT_ENABLED: false
R6_INT10K_RUNTIME_R1_ENGINE_COMMITTED: false
R6_INT10K_INTEGRATED_10K_EXECUTED: false
R6_INT10K_INTEGRATED_10K_AUTHORIZED: false
DOMAIN_INDEPENDENT_ADAPTIVE_RETENTION: ARCHITECTURE_ONLY
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```
