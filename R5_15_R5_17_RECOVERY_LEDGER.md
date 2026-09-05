# ARCANA WorldSim — R5.15–R5.17 Recovery Ledger

> Purpose: preserve the recovered continuation evidence without inventing repository provenance that is not present on the current `main` branch.

## Recovery audit — 2026-09-05

```yaml
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
AUDIT_SCOPE:
  - v0.6D1-R5.15
  - v0.6D1-R5.16
  - v0.6D1-R5.17
REPOSITORY_TREE_SEARCH:
  R5_15: no matching path found
  R5_16: no matching path found
  R5_17: no matching path found
FILE_LIBRARY_TARGETED_SEARCH: no relevant ARCANA artifact recovered
ARTIFACT_MIRROR_STATUS: BLOCKED_PENDING_REAL_ARTIFACT_RECOVERY
```

## What is repository-verified

The current repository contains the compact continuation authority `ARCANA_WORLD_CURRENT_STATE.md`, which records R5.17 as the latest recovered completed continuation head and R5.18 as the next stage. The current repository does **not** contain identifiable R5.15, R5.16 or R5.17 stage artifacts under those stage identifiers.

Therefore, repository provenance is currently incomplete for these three stages.

## Recovered project/chat continuity

The following information was recovered from prior ARCANA project conversations. It is retained as **recovered continuity evidence**, not as a substitute for missing source artifacts.

```yaml
R5_15:
  completion: recovered as completed/verified
  recovered_theme: Multi-Seed Coherence Ensemble
  seal_claim_in_prior_chat: present
  repository_seal_evidence: absent

R5_16:
  completion: recovered as completed/verified
  recovered_theme: Catastrophe Membrane / Dual-Law Hysteresis
  candidate_claim_in_prior_chat: present
  repository_stage_evidence: absent

R5_17:
  completion: recovered as completed/verified
  repository_stage_evidence: absent
  metadata_conflict: true
```

### R5.17 metadata conflict

Two incompatible R5.17 descriptions were recovered from earlier conversations:

1. `Stochastic Coherence Catastrophe Membrane, Dual-Law Hysteresis & Phase-Diagram Law-Transition Analysis`
2. `Ecological Carrying-Capacity & Latent-Pocket Stress Atlas`

A prior-chat claim also referenced commit `3f2c0b7` as R5.17 evidence. Direct lookup against the current GitHub repository did not resolve that commit. It must therefore **not** be treated as current repository provenance.

## Governance decision

Until real R5.15–R5.17 artifacts, hashes, logs, commits, or equivalent direct provenance are recovered:

- do not fabricate replacement artifacts;
- do not promote R5.15, R5.16 or R5.17 to `SEALED` from chat claims alone;
- preserve R5.17 as the recovered continuation head;
- preserve R5.7 as the last repository-authority seal currently established by the compact state ledger;
- treat R5.17 metadata/title as unresolved;
- do not allow a newly implemented R5.18 to silently overwrite or retroactively redefine R5.15–R5.17.

## R5.18 gate

R5.18 may be specified as a new repository-tracked continuation only if its contract explicitly acknowledges the provenance gap and uses only scientifically/repository-supported parent inputs. If R5.18 requires exact R5.17 numerical artifacts that are currently missing, execution must remain blocked until those artifacts are recovered.

```yaml
NEXT_STAGE: v0.6D1-R5.18
PARENT_CONTINUATION_ID: v0.6D1-R5.17
PARENT_METADATA_CONFIDENCE: partial
PARENT_ARTIFACT_PROVENANCE: incomplete
AUTO_SEAL: forbidden
```

---

This ledger is intentionally conservative: it records uncertainty rather than converting old chat summaries into canonical scientific evidence.
