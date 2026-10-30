# ARCANA R6 — 10k preflight BLOCKED: uplift decision + checkpoint–journal atomic recovery

**Logged:** 2026-10-30. **Provenance:** user/operator-provided FAIR report `docs/arcana/R6_RUNTIME_R2_10K_PREFLIGHT_FAIR_20261030.md`, also shared to this conversation as an uploaded Markdown copy. The connected GitHub-doc session does not have access to the local FAIR evidence bundle or test binaries; result below is *FAIR operator reported* and SHA are taken from that report, not independently rehashed in this doc-only workflow.

## Actual preflight decision

`R2_10K_PREFLIGHT=BLOCKED_UPLIFT_SCENARIO_NOT_AUTHORIZED_AND_CHECKPOINT_JOURNAL_RECOVERY_UNQUALIFIED`

Preflight completed without modifying any engine, physical contract, existing test, original archive, code commit or pushing source; **no 10k/100k execution**. There were two controlled supervised child interruption tests and bounded resume/corruption tests; a 10k-configured runtime was not advanced. Existing 168 exact suite passes remain source-hash-pinned.

R2 1000Y original full-result manifest: `1b1062eec6cbe1c13757fd06fd364a1ab30d808e2ed2dffe7018878ed94e3af3`; 1000Y report: `29ba4b36cc145acb7ec9b276dae8ca6a9bbd3a483145af8744024d288bb9a50f`. Sources in FAIR reported current worktree branch `r6/runtime-copy-r1-fair` based on `2c71370eb9a959c78121ce1c88ec8e9e37187787` with intended uncommitted R1/R2 changes; actual `CompactRuntime` source SHA `887d7b5b358069f7c4feba375d4410534e200984ceb978232e3baf9ab0d8c30a`, regional operator SHA `bc119751559d4d74c8e76292dcc92fcabeade31defb59a9f65cc4d7d60a047db`, 1000Y runner SHA `d4910c5f3f807db002adce50e73167acc833b6c348e3c2a50a4478b4db819d60`.

## Blocker A — authorial uplift selection OPEN

Existing code fixes unified total uplift `(0.1, 0.0)`. Under a 1000Y plan, uplift in affected support is 0.1m total, so yearly uplift = **0.0001 m/y**. Under a 10k plan there are two different experimental scenarios:
- `KEEP_TOTAL_UPLIFT_0_1M`: total 0.1m / 10000 y = 0.00001m/y; **changes annual forcing tenfold**.
- **Recommended for comparable annual physical forcing (not yet ratified)**: `KEEP_ANNUAL_UPLIFT_0_0001M_PER_Y`: yearly 0.0001m/y, 10000Y total **1.0m** on the same support, other support stays at existing zero total. This preserves annual forcing magnitude but is **not guaranteed to preserve trajectory** because total duration/model configuration and future geometry evolve. User must explicitly ratify before this scenario is considered authorized.

The R6 controller must expose a minimal versioned config interface for total uplift or (if authorial preference) explicit per-year uplift and derive total deterministically for planned duration; bind both plan, derived vector, support identity, source and forcing digest in checkpoints and manifest; reject stale cross-horizon imports and forbid silently using hardcoded 0.1m. The user has **not** yet ratified the 10k forcing choice; no 10k launch.

## Blocker B — recovery of checkpoint and journal OPEN

During a supervised 3Y kill before durable journal fsync, a **valid CP3** remained but its associated **184 logical records / 490782 logical bytes** had **zero journal bytes** persisted. The reader correctly rejects that prefix as incomplete. Numeric year-4 restart from CP3 matched direct CP4, **but the lost historical record chain was not recovered**. After fsync, numerical/record prefix matched only when using a test-specific external diagnostic head; native R2 runner metadata/atomic chain publication was absent. Corruption/truncation negatives rejected. Therefore numerical checkpoint sufficiency != causal historical resume authorization.

**Proposed minimal qualified fix (do not replace B0):**
1. Append source-ordered full-value delta/annual/unified/events to immutable journal chunks, calculate byte length, record count, first/last global sequence, native source time, chunk SHA and previous chain head; verify canonical null/event semantics.
2. Persist journal chunk and file/directory flush/fsync to meet documented durability boundary, then persist/seal the matching coupled checkpoint and its source/config/branch/duration/time/ordinal/high-water and journal chain head; do not make this checkpoint visible as a committed resume target yet.
3. Publish one last **atomic committed descriptor/read-view** using existing B0 transaction/visibility mechanism with both journal prefix identity and checkpoint identity. Crash before visibility switch resolves to previous committed pair; crash after resolves to fully verified new pair. Validate idempotence, stale parent and old-reader pinning. Do not assume independent file renames alone make two files atomic.
4. On reopen, load only the latest fully committed and hash-verified descriptor and reconstruct/rebind the complete global stream numbering across resumed segments; reject missing prefix, mismatched high-water, wrong source/config/horizon, missing event or truncated chunk. Preserve old committed prefixes and store incomplete files as quarantined evidence, do not silently delete/rewrite.
5. Test real R2 native runner with bounded 3Y/10Y direct vs split and subprocess SIGKILL at before/after chunk fsync, checkpoint durable, before/after atomic read-view switch, cleanup, with complete event/Deep/original NULL continuity. Genuine restart must recover **history and physics**; numeric endpoint alone is insufficient.

Checkpoint schedule initially 100/250/500/750/1000, then each 1000 years, with up to **999 simulated years of recomputation** after a failure if the schedule remains; user should ratify that recovery objective or opt for denser checkpoint intervals based on measured overhead. Do not confuse restart schedule with adaptive scientific retention.

## Quantitative 10k conditional planning (not observed run / not caps)

Source: actual R2 1000Y per-100Y windows. First 100 years hot 3.233686s, last 4.248704s. Planning only:
- Hot+compact ingest **630 / 885 / 1396 seconds** under slope sensitivity 0.5/1/2 = **10.5 / 14.8 / 23.3 minutes**. This excludes downstream reconstruction and unqualified pause/recovery costs.
- Resident journal/solver/transients illustrative **1.9–3.0 GiB**, not upper bound.
- Compact stream ~**1.619 GB** at unchanged cadence; archive w 14 draft checkpoints central **1.821 GB**, illustrative **1.6–2.2 GB**.
- Final checkpoint ~35.5 MB; stored checkpoints total ~202.5 MB under draft cadence.
- Optional entire legacy HISTORY ~178 GB (scenario ~140–220 GB); materialization costs could dominate, and full legacy should be **separately requested, measured and stored**, not silently included in compact-loop timing or generated by default.
- Five O(D) deposit scans remain, resident journal growth, old-record cold query O(D), no indexed query or B0 production durability qualification. Actual run at 10k is required for real measurements; projections are not bounds.

## FAIR and authority limits

Preflight used session-58727 with user-authorized bounded tests, no scheduler job evidence found; displayed cpuset 0..127 and cgroup max do not establish allocation. Site quota UNKNOWN. Actual free filesystem ~16.28TB decimal **is not quota**. For future separately authorized 10k, recheck session/job/site policy, output root and quotas; do not invent admin requirements absent actual rules. No 10k authorization or execution follows this entry.

## Proposed next engineering gate: R2-REC1 (NOT EXECUTED / NOT AUTHORIZED TO MUTATE CODE HERE)

A. User ratifies 10k annual uplift choice; **recommend same yearly 0.0001 m/y, total 1.0 m over 10000 years** for the first comparable 10k experiment. Don't claim ratification before explicit acceptance.

B. R2-REC1 code changes in isolated worktree with R1/R2 patch/hash backups (do not reset intentional dirty source), minimal explicit uplift configuration, B0-compatible journal+checkpoint committed pair and native replay/reopen controller; test first using current original 1000Y plan, no new 1000Y/10k run unless separately approved.

C. Bounded crash matrix covering all publication phases and real native controller, direct/split physical and full logical source history parity, existing 168 negatives/regressions; measure space/time writer+fsync+commit cost, memory and restart. Retain original experiment and source hashes, no automatic commit/push.

D. Refresh preflight, show independently supported `R2_10K_PREFLIGHT=READY_FOR_EXPLICIT_10K_EXECUTION_AUTHORIZATION` ONLY when both user uplift choice and recovery safety have qualified. Long 10k authorization remains distinct.

```yaml
R2_FRESH_1000Y: PASS_EXACT_ORACLE_FAIR_OPERATOR_REPORTED
R2_10K_PREFLIGHT: BLOCKED_UPLIFT_SCENARIO_NOT_AUTHORIZED_AND_CHECKPOINT_JOURNAL_RECOVERY_UNQUALIFIED
RECOMMENDED_UPLIFT: KEEP_ANNUAL_0_0001_M_PER_YEAR_TOTAL_1_0_M_NOT_YET_RATIFIED
R2_REC1_ENGINE_IMPLEMENTED: false
R2_REC1_ATOMIC_RECOVERY_QUALIFIED: false
R2_10K_EXECUTION_AUTHORIZED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

References: local FAIR preflight `docs/arcana/R6_RUNTIME_R2_10K_PREFLIGHT_FAIR_20261030.md`; GitHub `PROJECT_LEDGER/R6_INT10K_R2_10K_PREFLIGHT_EXECUTION_TASK_20261030.md`; existing R6 B0 HistoryStore, B6N4A/B6N6 and E2 frontier/history streaming contract.
