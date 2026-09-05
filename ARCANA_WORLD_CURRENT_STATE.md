# ARCANA WorldSim — Current State Authority

> Compact repository-resident continuation ledger. Historical R3/R4/R5 material is provenance/archive unless specifically required.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
BASELINE_IMPORT_COMMIT: 15ef285e554658125744056ec9266d9b0ed4c0ba
RECOVERY_LEDGER: R5_15_R5_17_RECOVERY_LEDGER.md
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.7
LATEST_COMPLETED: v0.6D1-R5.14
LATEST_STATUS: CANDIDATE
NEXT_STAGE: v0.6D1-R5.15
NEXT_STAGE_SCOPE: R3.34-R3.39 BULK LEGACY RECONCILIATION
```

### Why this supersedes the earlier R5.17 recovery claim

A targeted recovery on 2026-09-05 found a contemporaneous 2026-09-03 WorldSim handoff stating that:

- R5.14 was the last completed PASS CANDIDATE stage;
- the global R3.34–R3.39 census had been started but not completed;
- R5.15/R5.16/R5.17 were a proposed future layout, not completed stage artifacts.

No repository artifacts for R5.15, R5.16 or R5.17 were found. Later assistant-side summaries assigning unrelated scopes to those identifiers are treated as context drift.

Therefore the prior temporary ledger entry `LATEST_RECOVERED_COMPLETED_ID: R5.17` is withdrawn.

## Continuation chain

```text
v0.6D1-R5.7   SEALED
  -> v0.6D1-R5.8    CANDIDATE completed
  -> v0.6D1-R5.9    CANDIDATE completed
  -> v0.6D1-R5.10   CANDIDATE completed
  -> v0.6D1-R5.11   CANDIDATE completed
  -> v0.6D1-R5.12   CANDIDATE completed
  -> v0.6D1-R5.13   CANDIDATE completed
  -> v0.6D1-R5.14   CANDIDATE completed
  -> v0.6D1-R5.15   NEXT / NOT YET COMPLETED
```

## R5.14 summary

```yaml
STAGE: v0.6D1-R5.14
STATUS: CANDIDATE
SOURCE_AUTHORITY: 36/36 PASS
REGRESSION: 4/4 PASS
RECONCILIATION: 37/37 PASS
ECOLOGICAL_PARTNER_CANDIDATES: 24
ENSEMBLE_MEMBERS: 32
ENVIRONMENT_TRAJECTORY_ANCHORS: 9
MAX_DOMESTICATION_STAGE: 1
INCIPIENT_DOMESTICATED_SPECIES: 0
MATERIALIZED_DOMESTICATED_SPECIES: 0
ANIMAL_FOOD_PRODUCTION_EMERGENCE: false
PLANT_REGISTRY: absent
PLANT_DOMESTICATION: false
AGRICULTURE: false
SENSITIVITY_VARIANTS: 18
NON_EMERGENCE_ROBUST_ACROSS_ALL_VARIANTS: true
UNIQUE_HUMAN_IDENTITY: false
DEEP_COUPLING: OFF
```

## R5.15 contract direction

R5.15 is the first unfinished operation after R5.14:

`R3.34–R3.39 BULK LEGACY RECONCILIATION`

The work must census and classify R3.34–R3.39 together, rather than automatically mapping one R5 stage per legacy stage.

Required classification for each legacy stage:

```text
A — exact deterministic reuse
B — deterministic reuse within strict numerical tolerance
C — semantically reusable but requires R5 reconciliation wrapper
D — scientifically incompatible / missing evidence
```

Only class D justifies new simulation/repair.

R5.16 remains a conditional targeted gap/repair block if the census finds real problems. A later integrated end-of-legacy seal should use the next appropriate identifier without creating empty stages merely to preserve old numbering expectations.

## Repository tracking rule

From now on every scientific, implementation, governance, calibration, replay, audit or continuation change must be represented in this repository.

1. Commit the relevant contract/source/artifact/result.
2. Update this state ledger in the same change or immediately following bookkeeping commit.
3. Record parent, status, seal status and next stage.
4. Never infer `SEALED` from PASS alone.
5. Never let chat-only metadata override repository evidence or stronger contemporaneous handoffs.
6. Retrieve large historical artifacts only for targeted provenance/audit work.
7. Do not introduce an external runtime unless the scientific question shows it is useful.

---

Updated: 2026-09-05 (Europe/Rome project date).
