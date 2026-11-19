# R2 10k preflight refresh after REC1

2026-10-30. Prepared only after the bounded REC1 PASS.

`R2_10K_PREFLIGHT=BLOCKED_LONG_RUN_LAUNCHER_INTEGRATION_AND_SERVICE_CONTRACT_PENDING`

The former authorial-uplift and bounded coupled-recovery blockers are resolved
by [REC1](R6_REC1_FAIR_20261030.md). The earlier BLOCKED report is preserved as
history. This refresh does not execute or authorize 10k/100k or another 1000Y.
No scientific/production authority is promoted.

## Source and configuration contract

Same branch/head and intentionally dirty source set as REC1. Its
SOURCE_SHA256.json, REC1_DELIVERY.tar and REC1_AGAINST_R2.patch define the candidate;
future source edits invalidate this exact candidate identity until requalified.
All original/R1/R2 archive members were rehashed and unchanged.

Proposed explicit run plan:

```yaml
schema: ARCANA_R6_ANNUAL_UPLIFT_PLAN_REC1_V1
decision_id: R6_INT10K_KEEP_1000Y_ANNUAL_UPLIFT
planned_years: 10000
external_step_years: 1
external_steps: 10000
annual_uplift_m_by_support:
  R6G1D-R091-C028: 0.0001
  R6G1D-R091-C029: 0.0
derived_total_uplift_m_by_support:
  R6G1D-R091-C028: 1.0
  R6G1D-R091-C029: 0.0
opening_rate_m_year: 0.01
hydrology_dt_seconds: 31557600.0
regional_prescribed_uplift: 0.0
long_run_authorized: false
```

The initial E0 mapping binds C028/plate11 and C029/plate5. Preserve the original
nine-cell synthetic geology, two 73-node E0 columns, numerical rules, thermal,
Deep, water/solid balances and null event-time semantics. Config-derived annual
uplift matches the original magnitude; horizon-bound hashes and potentially
other horizon semantics differ. Cross-horizon native checkpoints are rejected.
The explicit plan was checked at zero advance and with 3/10-step direct/split
recovery. No 10000-year physical/model validity claim follows.

## What is now qualified

228 regressions PASS, exact original E0 3Y/10Y histories and 101/501/751 anchors,
and nine SIGKILL windows with full causal recovery followed by exact Y10
continuation. Existing B0 read-view publication is the sole commit authority;
source/config/clocks/native bytes/chunk chain/global high-water are bound.
REC1 supports repeated advance/commit/recover on one live frontier. It does not
change the old hardcoded-1000Y runner, which must not be used as a 10k launcher.

## Resource planning, not a new long-run forecast

The authentic 1000Y base remains hot 37.447499 s, observed loop 40.240046 s,
175661768 archive bytes and 355.60 MiB whole-service peak RSS. The prior ten
100-year windows and conditional nonlinear estimates remain evidence for the
old service: roughly 10.5–23.3 minutes hot/compact, 1.619 GB compact data,
illustrative 1.9–3.0 GiB resident state/journal, not upper bounds or reservations.
Five O(D) scans persist; integrating deposit growth is quadratic numerical work,
not ten times the measured 1000Y cost. Annual physical/event cadence can change.

REC1 adds writer encoding, fsync, typed B0 publication and verified prefix replay.
At 10 advanced years the explicit-plan commit costs 0.094671 s, including
0.009002 s journal persistence, 0.020239 s checkpoint seal/persist,
0.040612 s pair verification and 0.023528 s B0 publication. These small-state
costs cannot be projected unchanged to 10k. Runtime journal/frame bytes remain
resident; the adapter does not prune them. Cold recovery retains the selected
native-checkpoint chain and reads/replays the committed compact prefix.
Account for sum of checkpoint sizes and replay buffers in addition to the old
RSS scenario. Full history query/export creates detached snapshots on demand;
the prior optional ~178 GB legacy service remains a different output contract.

## Remaining integrated-launch gate

Prepare and qualify a separate controller-driven launcher before issuing an
executable 10k command. It must bind the reviewed source snapshot, original E0
pins, explicit named plan and full config/forcing identity; use a fresh external
run directory; maintain a live frontier; persist only compact causal data between
scheduled commits; and resume exclusively through REC1's verified B0 pair.
No original 10k oracle exists: same-plan direct/split and checkpoint replay,
balances, clocks, event/material/provenance closure remain the engineering tests.

Specify requested services: compact archive, chosen historical queries and
selected full states; select full legacy export explicitly if wanted and time
it separately. Include observed total service cost, not only hot advancement.
Review checkpoint cadence/recovery objective: Y100/250/500/750/1000 and each
later 1000 is a draft with up to 999 years recomputation, not an accepted policy.
More frequent commits add checkpoint/fsync/replay cost and reduce recovery loss.
Do not infer an optimal interval from a ten-step overhead measurement.

The integrated launcher must record annual/window100 wall and CPU user/system,
equivalent cores, p50/p95/max, numerical/compact/writer/commit/verification phase
costs, process-tree RSS and separately actual cgroup peaks, file counts and
logical/allocated bytes, event/deposit growth, committed ordinal/head, checkpoint
sizes/times and recovery/query/materialization costs. Preserve failure evidence;
no automatic blind retry. Test its bounded mode before any long-run request.

## FAIR context

Observed host FAIR, current cgroup `session-58727.scope`, matching the account
holder's existing interactive authorization. No scheduler commands srun/salloc/
sbatch/qsub/bsub were found; no new scheduler-only rule was identified. Effective
session `cpu.max=max 100000`, `memory.max=max`; affinity exposes 0..127. These are
visibility/quota observations, not reservation of 128 cores or unlimited RAM.
Free filesystem ~16.28 TB decimal; account quota UNKNOWN (no quota tool exposed).
FAIR_CONTEXT.json and FAIR_EFFECTIVE_SESSION.json retain raw readings. No
invented application time, RAM, output or thread caps were added.

Recheck site rules, actual allocation/quota and source identity at a separately
authorized launch. Unknown quota remains explicit; no administrator approval
requirement is fabricated. The next step is bounded launcher/service-contract
integration and a completed preflight review, followed by a separate explicit
10k execution authorization. REC1 PASS alone supplies no long-run permission.
