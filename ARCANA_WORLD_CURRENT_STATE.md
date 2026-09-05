# ARCANA WorldSim — Current State Authority

> Compact repository-resident continuation ledger. Historical R3/R4/R5 material is provenance/archive unless specifically required.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
BASELINE_IMPORT_COMMIT: 15ef285e554658125744056ec9266d9b0ed4c0ba
RECOVERY_LEDGER: R5_15_R5_17_RECOVERY_LEDGER.md
R5_15_CONTRACT: R5_15_BULK_LEGACY_RECONCILIATION_CONTRACT.md
R5_15_FINAL_AUDIT_PASS2: R5_15_FINAL_AUDIT_PASS2.json
R5_15_FINAL_AUDIT_COMMIT: fba2b90142cd3895ad2ef982d3fb19df22150d8a
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.7
LATEST_COMPLETED: v0.6D1-R5.15
LATEST_STATUS: CANDIDATE
LATEST_VERDICT: PASS_R515_R334_TO_R339_BULK_LEGACY_RECONCILIATION_CANDIDATE
NEXT_STAGE: v0.6D1-R5.16
NEXT_STAGE_SCOPE: R5.8-to-R3.39 integrated end-of-legacy reconciliation and seal review
```

## Recovery and discovery correction

A targeted recovery on 2026-09-05 established that R5.14 was the last completed stage in the contemporaneous handoff and that R5.15 was the unfinished R3.34–R3.39 bulk legacy reconciliation.

R5.15 pass 1 initially reported provenance gaps because GitHub code search was not indexed. Direct repository Contents API inspection then found complete artifact directories and final-seal directories for every stage R3.34 through R3.39. Pass 2 therefore supersedes the pass-1 discovery result while preserving pass 1 as audit history.

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
  -> v0.6D1-R5.15   CANDIDATE completed
  -> v0.6D1-R5.16   NEXT / NOT COMPLETED
```

## R5.15 completed result

```yaml
STAGE: v0.6D1-R5.15
STATUS: CANDIDATE
SCOPE: R3.34-R3.39 BULK LEGACY RECONCILIATION
REUSE_CLASSIFICATION:
  A: 6
  B: 0
  C: 0
  D: 0
REMAINING_PROVENANCE_GAPS: 0
SCIENTIFIC_INCOMPATIBILITIES: 0
NEW_SIMULATION_REQUIRED: false
EXTERNAL_RUNTIME_REQUIRED: false
REPAIR_BLOCK_REQUIRED: false
AUTO_SEAL_PERFORMED: false
```

Class A means exact reuse of immutable repository-resident SEALED artifacts and their manifest/hash-bound semantics; it does not require a fresh scientific rerun.

Repository-verified internal legacy chain:

```text
R3.34 -> R3.35 -> R3.36 -> R3.37 -> R3.38 -> R3.39
```

The final-seal audits verify exact parent/hash bindings across the chain, output-manifest closure, exact keys/axes/geometries where applicable, preservation of negative outcomes, Deep coupling OFF, and no forced unique human identity.

## R5.16 direction

Because R5.15 found no class-D gap, a targeted repair stage is not justified. The next non-empty identifier is therefore R5.16, used for an integrated end-of-legacy reconciliation and explicit seal review over the R5.8-to-R5.15 continuation and the reconciled sealed legacy authority through R3.39.

R5.16 must not auto-seal. It must either:

- explicitly PASS and produce a separately audited integrated seal, or
- remain blocked/CANDIDATE with the exact failing dependency recorded.

## Repository tracking rule

Every scientific, implementation, governance, calibration, replay, audit or continuation change must be represented in this repository.

1. Commit relevant contract/source/artifact/result.
2. Update this state ledger in the same change or immediately following bookkeeping commit.
3. Record parent, status, seal status and next stage.
4. Never infer `SEALED` from PASS alone.
5. Never let chat-only metadata override repository evidence or stronger contemporaneous handoffs.
6. Retrieve large historical artifacts only for targeted provenance/audit work.
7. Do not introduce an external runtime unless the scientific question shows it is useful.

---

Updated: 2026-09-05 (Europe/Rome project date).
