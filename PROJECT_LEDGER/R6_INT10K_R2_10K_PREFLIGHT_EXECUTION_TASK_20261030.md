# ARCANA WorldSim R6 — R2 integrated 10k PREFLIGHT approved, no 10k execution

**Date:** 2026-10-30. **User decision:** "sono daccordo facciamo il prossimo passo", in response to **the 10k preflight** proposal following the first successful fresh R2 1000Y synthetic trajectory. This approves the bounded **preflight, source/data audit, analysis and necessary short qualification tests**, NOT the 10000-year computation, any 100k run, changes to scientific models, automatic commit/push, or mutation of immutable FAIR evidence.

**Result status in advance:** `R2_10K_PREFLIGHT=PENDING_EVIDENCE`. Never pre-label READY or PASS. Follow `PROJECT_LEDGER/R6_INT10K_RUNTIME_R2_FRESH_1000Y_FAIR_PASS_10K_PREFLIGHT_GATE_20261030.md`, existing R6 INT10K integrated multiphysics benchmark plan and E2 frontier/history streaming contract. This is a new instruction to run the preflight, not evidence that it ran.

## Grounded 1000Y inputs

User/operator-reported fresh R2 1000Y PASS: exact reconstructed 61,001 original indexed payloads (1,001 regional snapshots; 1,000 annual records; 1,000 unified/Deep steps; 58,000 events; 8,000 source NULL timestamps); byte-identical reconstructed HISTORY/INDEX and five checkpoints; restart, balances, historical queries, and 168 tests PASS. Advance + compact ingestion 37.45 s, observed loop with checkpoints 40.24 s, full legacy reconstruction 43.33 s, launch-to-exit all audits 110.02 s, compact complete archive 175.66 MB, full-process RSS 355.60 MiB, 0.97 CPU core equivalent. Five O(D) deposit scans and RAM-resident journal remain. FAIR local report path `docs/arcana/R6_RUNTIME_R2_1000Y_FAIR_20261030.md`; **GitHub remote documentation author has not fetched or independently verified the FAIR report/output/SHAs**, so Codex must obtain them from the actual local machine.

FAIR worktree expected `~/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`; branch `r6/runtime-copy-r1-fair`, source base commit `2c71370eb9a959c78121ce1c88ec8e9e37187787`; **intentional uncommitted R1/R2 changes**. Do not `git pull`, `git reset --hard`, checkout dirty files, merge, create commits or push. Create a SHA-identified read-only inventory and a new noncolliding preflight evidence root. Historical 1000Y original manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`; R1 full candidate manifest SHA256 `3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b`; obtain actual R2 result manifest and measured file hashes rather than guessing them.

## Mandatory P0 audits

### P0.1 — Source, baseline and authority closure
- Inspect actual git status, code/diff hashes, `CompactRuntime`/stream codecs/runner API, source files and tests, E0 pinned manifest and source provider identities, R1 backup patch, R2 patch, R2 1000Y manifest member and test artifacts. Never convert user-reported exactness into independently sealed proof without rehashing source and result files.
- Inventory exact present numerical domains, grids/supports (synthetic 3×3, C028/C029), update cadence, actual Deep/thermal/surface/hydrology coupling and known gaps. Do not imply climate/ecology/geodynamics/more complete physics absent from current synthetic case.
- Preserve synthetic NONCANONICAL execution meaning and all authorization flags false.

### P0.2 — Time and uplift semantics (hard decision)
- Inspect the code that binds `RegionalConfig.duration_years`, unified `planned_years`, external `segment_years=1`, annual coupling, `hydrology_dt_seconds=31557600` and per-year uplift; independently derive and document 1000Y and proposed 10000Y effective per-year values.
- Prior run-level uplift **total 0.1 m across 1000Y** corresponds to 0.0001 m/year if distributed uniformly. Carrying **0.1 m total to 10000Y** implies 0.00001 m/year (10× smaller); carrying **same annual uplift** to 10000Y implies **1.0 m total**. These are *configuration alternatives*, not permission to change physics silently. State which variant preserves per-year forcing comparability, assess implications for source identity/checkpoint and identify authorial input if not settled by the existing contract.
- Do not mutate the original config for comparison or call 10k. Confirm no hidden high-cadence hydrology work (e.g. default 3600 s/hydrology step). Distinguish environmental/scientific source validity from engineering timesteps.

### P0.3 — Memory, journal streaming and asymptotic sustainability
- Analyze actual R2 1000Y `REPORT` windows and source instrumentation; extract per-100Y wall/user/system, RSS time samples, deposit rows per year, in-memory journal objects/bytes and compact file sizes by record type, checkpoint sizes. If missing, mark missing and propose the minimum bounded measurement. Do not infer 10k RAM from only final peak.
- Inspect all references retaining prior year frames/events in Python lists, `_DepositLog` older rows, previous full snapshots, checkpoint clones, query indexes and full-output materials. Quantify O(Y), O(Y²) components and whether append-only frames are flushed/closed/iterated without mandatory retention of every frame in RAM. Explicitly measure/assess five O(D) mass/provenance/deposit scans, and distinguish their unavoidable physics from avoidable copies.
- Propose **bounded, isolated changes only if required**, with a new approval gate for unqualified architecture modifications. No implicit pruning, lossy compaction, forcing changes, loss of order, sources, 8000 NULL timestamp preservation or renaming canonical identity without tests.
- Do NOT introduce arbitrary RAM/time/output caps; record actual FAIR allocation and job policy.

### P0.4 — Checkpoint/restart and failure semantics
- Examine checkpoint schedule and actual successful R2 1000Y restart evidence, including coupled frontier (not just the regional cells), ordered compact stream high-water mark, configuration/source identities, exact numerical memory, Deep, material balances, seed/forcing and all domain time boundaries.
- Verify what happens if a process ends between compact append/fsync and checkpoint publication; a scratch stream without production atomic B0 publication must not claim crash durable replay. Design a **bounded supervised checkpoint/resume test** that can run under a short synthetic horizon without destroying evidence, including byte/hashes/source/coupling continuity and fail-closed detection of incomplete segments.
- Explain whether one full checkpoint every 100/250/500/750/1000 and each subsequent 1000 years is defensible or needs a separately declared policy; no arbitrary global snapshot interval or conflation with post-hoc adaptive historical retention.

### P0.5 — FAIR execution, storage and observability
- Check actual current FAIR session/compute node vs login node, scheduler/job allocation identity, site policy, assigned cpuset, CPU quota, disk quota, accessible output root; **the user's permission to run under their account is explicit**, but does not override actual scheduler/site rules. No invented separate admin attestation if site rules don't require it.
- Forecast 10k candidate CPU, wall/RSS and disk using per-window growth and explicit residual O(D) cost with uncertainty bounds (scenario ranges, not fake hard caps); identify whether the output format is full legacy or compact. No implied linear projection from 1000Y.
- Design observational telemetry: actual numerical loop and per-100Y wall+CPU, kernel/copy/deposit scans/writer/checkpoint, p50/p95/max, process-tree RSS and high-water cgroup, event/deposit counts, compact stream logical/allocated bytes/file counts, source/config hashes, restart overhead, selected historic query latency and optional legacy materialization timed separately.
- Since no original 10k oracle exists, define independent validation: overlap with 1000Y only when *identical actual per-year forcing and planned-horizon semantics*; direct/split on a small identical-plan region; restart at selected year; source hashes and consistency (material/water/Deep and exact event ordering); after tests separate science from numeric engineering.

## Allowed execution under this authorization

READ-ONLY diagnostics and rehashing, no-source-change preflight, static call-graph, quantitative analysis of existing 1000Y evidence, and **short bounded tests necessary to verify the same-source schedule/restart mechanism**, as allowed by FAIR policy. Short tests must not be mislabeled as 10k. If source changes are necessary to achieve reliable 10k streaming/restart, **report BLOCKED with minimal change specification** rather than silently applying an unqualified change or launching an unbounded long run. Do not silently rerun 1000Y or execute a 10k/100k numerical trajectory.

Evidence output required under a unique preflight root: `R2_10K_PREFLIGHT_REPORT.md`, `R2_10K_PREFLIGHT_REPORT.json`, `SOURCE_IDENTITY.json`, measured resource and input references with SHA, `UPLIFT_SEMANTICS.md`, `JOURNAL_MEMORY_SCALING.md`, `CHECKPOINT_RESTART_PLAN.md`, `FAIR_EXECUTION_CONTEXT.md`, and immutable report manifest. No need to artificially generate empty files; when data are unavailable mark UNKNOWN and fail closed.

## Verdict

- Emit `R2_10K_PREFLIGHT=READY_FOR_EXPLICIT_10K_EXECUTION_AUTHORIZATION` **only** when exact source/input and numerical configuration, explicitly selected and comparable uplift semantics, journal memory/scaling/stream integrity, restart closure, valid FAIR compute context, output policy and telemetry are all verified. Mark remaining limitations precisely. READY is *not* 10k GO.
- Else `R2_10K_PREFLIGHT=BLOCKED_<EXPLICIT_REASON>`, record unresolved evidence and the minimal remedial next action.
- An expected `R2_10K_PREFLIGHT=BLOCKED_UPLIFT_SCENARIO_NOT_AUTHORIZED` is reasonable if annual/total uplift semantics cannot be derived from prior governing authorial decision; do not make the choice as an autonomous physical change.

```yaml
R2_FRESH_1000Y: PASS_FAIR_OPERATOR_REPORTED
R2_10K_PREFLIGHT: USER_AUTHORIZED_TO_PERFORM_NOW
R2_10K_NUMERICAL_EXECUTION: NOT_AUTHORIZED
R2_100K_NUMERICAL_EXECUTION: NOT_AUTHORIZED
AUTO_COMMIT_OR_PUSH: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```
