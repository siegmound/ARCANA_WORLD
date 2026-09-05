# ARCANA WorldSim — Current State Authority

> Compact repository-resident continuation ledger. This file is the default bootstrap for future ARCANA WorldSim work; historical R3/R4/R5 artifacts are archive/provenance material and should be opened only when specifically needed.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
LAST_REPOSITORY_BASELINE_BEFORE_CONTINUITY_SYNC: 15ef285e554658125744056ec9266d9b0ed4c0ba
```

## Current continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.7
LATEST_CONFIRMED_COMPLETED: v0.6D1-R5.17
LATEST_COMPLETION_SOURCE: project/chat continuity recovered 2026-09-05
R5_15_TO_R5_17_REPOSITORY_ARTIFACT_MIRROR: pending
NEXT_STAGE: v0.6D1-R5.18
NEXT_STAGE_STATUS: NOT_COMPLETED
```

### Recovered recent chain

```text
v0.6D1-R5.14  completed candidate (previous state file)
  -> v0.6D1-R5.15  completed / verified in project continuity
  -> v0.6D1-R5.16  completed / verified in project continuity
  -> v0.6D1-R5.17  completed / verified in project continuity
  -> v0.6D1-R5.18  next stage; prior chat showed integration starting, not sufficient evidence of completion
```

R5.15-R5.17 must **not** be promoted to SEALED merely because they were completed/verified. `R5.7` remains the last explicitly confirmed seal until repository evidence or an explicit later seal proves otherwise.

## Repository tracking rule

From this synchronization onward, **no WorldSim modification is authoritative only because it exists in chat**.

For every scientific, implementation, governance, calibration, replay, audit, or continuation change:

1. commit the relevant source/artifact/contract to this repository;
2. update this file in the same repository change, or in an immediately following bookkeeping commit when atomic inclusion is technically impossible;
3. record the stage identifier, completion status, seal status, parent stage, and next stage;
4. preserve explicit `SEALED` versus `CANDIDATE`/unsealed distinctions;
5. never reconstruct the current head from old R3/R4/R5 chat history when this ledger and newer repository evidence are available;
6. retrieve historical large artifacts only for targeted provenance/audit needs rather than preloading them into chat context.

## Provenance gap to close

The repository baseline at `15ef285e...` predates the recovered R5.15-R5.17 work. Therefore the immediate bookkeeping objective is to mirror/recover the actual R5.15, R5.16 and R5.17 artifacts/contracts/results into the repository when available, without fabricating missing scientific evidence.

Until that mirror is complete, use this distinction:

```yaml
CONTINUATION_HEAD: v0.6D1-R5.17
CONTINUATION_CONFIDENCE: confirmed by project/chat continuity
REPOSITORY_ARTIFACT_COMPLETENESS_THROUGH_R5_17: incomplete
```

## Next work

```yaml
NEXT_STAGE: v0.6D1-R5.18
PARENT_CONTINUATION_HEAD: v0.6D1-R5.17
RULE: define and implement R5.18 from the recovered R5.17 head; do not restart from R3/R4/R5.14 and do not auto-seal.
```

---

Updated: 2026-09-05 (Europe/Rome project date).
