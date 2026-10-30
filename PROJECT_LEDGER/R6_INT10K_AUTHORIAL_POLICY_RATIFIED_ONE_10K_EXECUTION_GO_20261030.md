# ARCANA R6 INT10K — authorial configuration ratified; ONE synthetic 10k numerical execution GO

**Decision 2026-10-30.** User's explicit request following the R2-L1 PASS and question confirming `compact_query`, CP/B0 every 250Y and journal fsync every 10Y: **"Salta i controlli di memoria ti dico io che è libero solo assicura i parametri e fa partire il test 10k"**. This is (a) authorial ratification of the proposed L1 run policy, (b) user authorization for **one** first synthetic 10,000-model-year experiment, and (c) instruction to **omit the discretionary free-memory preflight gate**, based on the user's assurance. It does **not** mean a run has been executed by the GitHub-documentation session, which has no access to the user's FAIR shell.

**State:** `R2_10K_EXECUTION=USER_AUTHORIZED__PENDING_FAIR_OPERATOR_LAUNCH`, not PASS. The earlier preflight `BLOCKED_SERVICE_AND_CHECKPOINT_CADENCE_NOT_RATIFIED` is historically correct; its *authorial* missing choice is now resolved. The bounded L1 launcher is already qualified on 242 tests/9 SIGKILL; perform exact-identity operational preflight, not another design cycle. Only actual source/config/site incompatibility blocks starting. Do not make memory availability checks an extra condition.

## Ratified exact experiment contract

```yaml
scope: NONCANONICAL_SYNTHETIC_3X3_C028_C029_R6_ENGINEERING
planned_years: 10000
physical_annual_advance_years: 1
advanced_segment_years: 10000
output_service: compact_query
retain_all_complete_causal_records: true
legacy_full_History_Index_eager_export: false
journal_commit_interval_years: 250
paired_native_checkpoint_B0_interval_years: 250
staged_journal_fsync_interval_years: 10
staged_fsync_is_recoverable_commit: false
selected_query_years: [100,250,500,750,1000,2500,5000,7500,10000]
uplift_support_C028_annual_m_per_year: 0.0001
uplift_support_C029_annual_m_per_year: 0.0
uplift_support_C028_derived_10k_total_m: 1.0
uplift_support_C029_derived_10k_total_m: 0.0
opening_m_per_year: 0.01
hydrology_step_seconds: 31557600
use_existing_E0_provider_input_manifest_pins: true
numerical_solver_and_deep_rules_changes: false
full_10k_numerical_executions_authorized: 1
full_100k_numerical_executions_authorized: 0
read_only_memory_telemetry_during_execution: true
memory_free_capacity_preflight_gate_required: false
automatic_retry_after_failure: false
auto_commit_or_push: false
production_or_science_authority: false
```

The chosen query years are **engineering-selected sampling** of exact state reconstruction, not lossy archival retention. All annual events/deltas, materials, hydrology, Unified/Deep, provenance, source NULL timestamps and history reconstruction recipes **must** be retained for every year. If the prebuilt proposed CP250/fsync10 contract SHA `163a4557c3956baf133c25ae039da37c91a362a1388eab55b829eff78f2ebcc5` has different query-year selection, do **not** misrepresent that existing SHA as this new user-approved contract. Create a fresh exclusive L1 `prepare` contract with selected years and verify its new SHA; never rewrite the frozen proposed contract.

The 250Y schedule makes at most 249 completed model-years rework after the last paired committed checkpoint for an eligible recovery; before the first committed pair, a run may have no restart point and must not silently fall back to T0. Periodic fsync every 10Y only stages journal bytes, never authorizes a resume point. Exact final stage Y10000 must be paired and B0 committed.

## Before launch — narrow preflight ONLY

1. Inspect the **actual** FAIR local worktree under `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`, local branch `r6/runtime-copy-r1-fair`, baseline commit `2c71370eb9a959c78121ce1c88ec8e9e37187787`. R1/R2/REC1/L1 changes are intentionally dirty/uncommitted; do not `git pull`, reset, checkout old source, merge or push. Verify source/test SHA and original 1000Y and REC1/L1 evidence pins from reports. The L1 launcher reported SHA256 `7844b40dd68d879850de4500370aa6418009496747e3d04634556880836b6dd9` and REC1 runtime `44a203700871c2893f691fe0f304d7447deae714774c653ff61b9c043d8d6444`; verify actual available bytes and frozen exact contract identity, not just names.
2. Use the qualified L1 `scripts/r6_runtime_r2_launcher.py --help` to derive **real CLI flag names**; do not invent a run command or modify module APIs. Use `prepare` to produce a fresh immutable versioned V1 contract binding exact R6 module hashes, unchanged original E0 input root/pins, chosen uplifts and total, 10000 planned horizon, above compact-query service, query years, 250/250 B0/checkpoint and 10-year staged fsync. Rehash the finalized contract and verify intended values *before running*. If a CLI parameter or fixed service contract cannot express the declared settings without changing qualified source, STOP with `BLOCKED_CONTRACT_NOT_EXPRESSIBLE`; do not silently alter user choice or patch-stack.
3. Preserve all prior FAIR evidence. Create **new exclusive** results/evidence output roots with existence/no-symlink check. Bind exact source/forcing identities and record actual worktree diff. Verify E0 input and source manifests, root/storage writability, server session/compute context and **actual applicable FAIR site/scheduler policy**. User approves running the job on their account and confirms free memory. This eliminates the former **discretionary memory-headroom / available-memory preflight gate**; do not block on unknown `memory.max`, free memory or speculation about RAM. **Do not bypass actual site allocation restrictions, quota, disk write permissions, OS errors or numerical fail-closed guards**. Record resource limits if they exist; do not impose invented application time/RAM/output/thread caps.
4. No need to re-run a full 1000Y simulation or a prolonged preflight. The L1 bounded suite already PASS (242 tests) on the pinned source; if source SHA drift or required manifest mismatch, fail closed and report. Do not claim site policy verified unless actual evidence supports it.

## Execution — authorized one run

Once exact parameters, source/input, immutable contract and permitted FAIR execution context verify, **launch one new real R2-L1/REC1 synthetic 10k numerical trajectory** with exactly 10000 annual physical advances, one live frontier, distinct source-pinned evidence/output root, paired durable CP+B0 commit each 250 years and staged fsync each 10. L1 `run` must receive explicit `--runtime-r2-rec1`, contract path plus its **actual byte SHA**, output root and `--advanced-segment-years 10000`; do not use `--resume` for a fresh run. If the actual CLI requires options different from these documented concepts, use `--help` and the validated contract as the source of truth.

Do not assume a constant 11 deposits or 58 events per year or exactly 610001 records on the 10k: count actual emitted causal data. No independent 10k oracle exists. Observe all numeric/physical balances, provenance, Deep/coupled annual records, full material identity, clock/support continuity and NULL source-time semantics. Do not fabricate missing climate/biosphere/population sources or claim R6 is full planetary WorldSim scientific production.

**No silent retry, second full run, automatic physics edits or source patches if the run fails.** Preserve partial/orphan diagnostics and last eligible committed B0 prefix; report `BLOCKED_<reason>`. Do not relabel a truncated job PASS, and do not automatically rerun/continue after failure without an explicit decision. A requested read-only verification of committed history is part of the same run's acceptance.

## Telemetry, post-run acceptance

Collect observed per-year and 100Y-wall windows, CPU user/system/effective core use, wall by region/unified/scan/compact/journal/B0 CP/fsync/checkpoint/query, p50/p95/max, process and process-tree RSS and cgroup peak (observation only; distinguish shared metrics), exact events/deposits and B0 high-water numbers, logical/allocated bytes and files per compact stream/metadata/CP/B0/query, source/config and manifest hashes, cold exact-year query/witness at selected years, full causal ordered digest/clock/Deep/solid-water accounting and verified final native coupled checkpoint at Y10000.

No automatic full legacy `HISTORY`/`INDEX` materialization at 10k (may be immense); future optional legacy export separately qualified/authorized. Where sample 1000Y oracle exists, compare only if identical **actual numerical forcing/horizon**; changing plan changes config identity, so no ungrounded bit-exact 1000Y prefix claim. No science or production authority follows.

Completion marker `R2_10K=PASS_FRESH_10000Y_COMMITTED_HISTORY_AND_MEASURED_RESOURCES` only with full actual Y10000 closure, commit-chain integrity, source/forcing matches, no missing causal years, numerical balances and selected historic queries verified, and truthful all-inclusive costs. Otherwise `R2_10K=BLOCKED_<SPECIFIC_REASON>` with immutable evidence.

```yaml
R2_L1_BOUNDED: PASS_LAUNCHER_SOURCE_AND_RESUME_PARITY_OPERATOR_REPORTED
R2_10K_SERVICE_POLICY: AUTHORIAL_RATIFIED_COMPACT_QUERY_CP250_FSYNC10
R2_10K_MEMORY_FREE_PREFLIGHT: WAIVED_BY_USER
R2_10K_SOURCE_AND_SITE_PREFLIGHT: REQUIRED
R2_10K_FRESH_EXECUTION: USER_AUTHORIZED_ONE_RUN_PENDING_FAIR_OPERATOR_ACTION
R2_10K_EXECUTED: false
R2_100K_EXECUTION_AUTHORIZED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

Related: `PROJECT_LEDGER/R6_INT10K_L1_BOUNDED_PASS_POLICY_RATIFICATION_PENDING_20261030.md`, actual local FAIR `docs/arcana/R6_RUNTIME_R2_L1_FAIR_20261030.md` and `qualified/PROPOSED_OPTIONS.json` in evidence root `R2_L1_20261030_01`.
