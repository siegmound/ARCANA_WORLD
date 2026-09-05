# ARCANA WorldSim — Current State Authority

> Compact repository-resident continuation ledger. This file is the default bootstrap for future ARCANA WorldSim work; historical R3/R4/R5 artifacts are archive/provenance material and should be opened only when specifically needed.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
LAST_REPOSITORY_BASELINE_BEFORE_CONTINUITY_SYNC: 15ef285e554658125744056ec9266d9b0ed4c0ba
RECOVERY_LEDGER: R5_15_R5_17_RECOVERY_LEDGER.md
```

## Current continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.7
LATEST_RECOVERED_COMPLETED_ID: v0.6D1-R5.17
LATEST_COMPLETION_SOURCE: project/chat continuity recovered 2026-09-05
R5_15_TO_R5_17_REPOSITORY_ARTIFACT_MIRROR: BLOCKED_PENDING_REAL_ARTIFACT_RECOVERY
R5_17_METADATA_CONFLICT: true
REPOSITORY_ARTIFACT_COMPLETENESS_THROUGH_R5_17: incomplete
NEXT_STAGE_ID: v0.6D1-R5.18
NEXT_STAGE_SCOPE: unresolved_pending_parent_recovery
NEXT_STAGE_STATUS: NOT_COMPLETED
```

### Recovered recent chain

```text
v0.6D1-R5.14  completed candidate (previous state authority)
  -> v0.6D1-R5.15  recovered as completed/verified; repository artifacts absent
  -> v0.6D1-R5.16  recovered as completed/verified; repository artifacts absent
  -> v0.6D1-R5.17  recovered as completed/verified; exact metadata conflicts across old chats
  -> v0.6D1-R5.18  next identifier; exact scientific scope not yet authorized/reconstructed
```

Do **not** promote R5.15–R5.17 to `SEALED` from chat summaries alone. `R5.7` remains the last explicitly confirmed seal in this compact repository authority until direct evidence establishes a later seal.

## Verified recovery findings

The 2026-09-05 targeted recovery audit established:

- no `R5_15`, `R5_16` or `R5_17` paths are present in the current repository tree;
- the current GitHub repository has only the `main` branch, so there is no alternate branch carrying those stage artifacts;
- targeted File Library recovery found no relevant ARCANA artifact for these stages;
- historical chat records disagree on R5.17/R5.18 titles and scientific scope;
- a prior-chat commit claim `3f2c0b7` does not resolve in the current GitHub repository.

See `R5_15_R5_17_RECOVERY_LEDGER.md` for the conservative recovery record.

## Repository tracking rule

From the continuity synchronization onward, **no WorldSim modification is authoritative only because it exists in chat**.

For every scientific, implementation, governance, calibration, replay, audit, or continuation change:

1. commit the relevant source/artifact/contract to this repository;
2. update this file in the same repository change, or in an immediately following bookkeeping commit when atomic inclusion is technically impossible;
3. record stage identifier, completion status, seal status, parent stage, and next stage;
4. preserve explicit `SEALED` versus `CANDIDATE`/unsealed distinctions;
5. never reconstruct the current head from old R3/R4/R5 chat history when this ledger and newer repository evidence are available;
6. retrieve historical large artifacts only for targeted provenance/audit needs rather than preloading them into chat context;
7. never convert conflicting old-chat metadata into canonical scientific evidence without direct provenance.

## R5.18 continuation gate

```yaml
NEXT_STAGE_ID: v0.6D1-R5.18
PARENT_CONTINUATION_ID: v0.6D1-R5.17
PARENT_METADATA_CONFIDENCE: partial
PARENT_ARTIFACT_PROVENANCE: incomplete
SPECIFICATION_WORK: allowed_with_explicit_provenance_gap
SCIENTIFIC_EXECUTION:
  allowed: only when required inputs are repository-supported or newly supplied as direct evidence
  blocked: when exact missing R5.17 artifacts are required
AUTO_SEAL: forbidden
```

Bookkeeping or recovery work does not consume the R5.18 stage number.

---

Updated: 2026-09-05 (Europe/Rome project date).
