# v0.6D1-R5.16 — Integrated End-of-Legacy Reconciliation & Seal Review Contract

## Status

```yaml
STAGE: v0.6D1-R5.16
STATUS: AUTHORIZED_NOT_COMPLETED
PARENT: v0.6D1-R5.15 CANDIDATE
LAST_EXPLICIT_R5_SEAL: v0.6D1-R5.7
SCOPE:
  R5_CONTINUATION: v0.6D1-R5.8 through v0.6D1-R5.15
  RECONCILED_LEGACY: v0.6D1-R3.34 through v0.6D1-R3.39
PURPOSE: integrated end-of-legacy reconciliation and explicit seal review
AUTO_SEAL: forbidden
```

## Scientific/governance question

Does the complete R5.8→R5.15 continuation form one internally coherent, repository-proven, non-mutating scientific chain when reconciled against the SEALED R3.34→R3.39 legacy authorities, such that the block may be explicitly promoted to a new integrated SEALED milestone?

R5.16 is a **review and integration stage**, not a new historical simulation and not a repair stage.

## Preconditions already established

R5.15 pass 2 established:

```yaml
R3_34_TO_R3_39_REUSE:
  class_A: 6
  class_B: 0
  class_C: 0
  class_D: 0
remaining_provenance_gaps: 0
scientific_incompatibilities: 0
new_simulation_required: false
external_runtime_required: false
repair_block_required: false
```

Therefore R5.16 must not invent a repair merely to justify its existence.

## Required integrated audit domains

### 1. Repository provenance

For every stage R5.8–R5.15 identify and bind:

- stage contract/config/source authority;
- parent stage and immutable parent evidence;
- produced outputs and manifests;
- regression/audit evidence;
- completion verdict;
- explicit CANDIDATE/SEALED status;
- any external-engine evidence and its governed role.

A missing repository-bound stage artifact is a blocking provenance failure, not permission to reconstruct from chat memory.

### 2. Parent-chain integrity

Verify the full continuation order and parent compatibility:

```text
R5.7 SEALED
 -> R5.8
 -> R5.9
 -> R5.10
 -> R5.11
 -> R5.12
 -> R5.13
 -> R5.14
 -> R5.15
```

Where a stage uses a legacy R3 authority rather than only its immediate R5 parent, that authority must be explicitly represented as an additional dependency rather than silently flattened into the chain.

### 3. Legacy reconciliation integrity

Verify that the R5 continuation preserves the SEALED meaning of:

```text
R3.34 producer operational taxa
R3.35 producer quantitative genetics
R3.36 producer selection ecology / managed-forager pathway
R3.37 managed-forager economy
R3.38 regional technological traditions / reticulate genealogy
R3.39 symbolic memory / language-divergence preconditions / identity dynamics
```

R5.15 class-A reuse evidence must remain valid.

### 4. Negative-result preservation

The integrated block must not silently materialize any state previously absent unless a later repository-tracked stage explicitly and validly did so.

At minimum audit:

- agriculture;
- reproductive-control domestication;
- materialized plant domesticates;
- village/city/state;
- class hierarchy;
- currency/market;
- named culture;
- named language;
- named religion/myth;
- ethnicity;
- unique human identity;
- Deep/noetic biological coupling.

### 5. Human-lineage identity governance

Preserve the retained lineages:

```text
RPT_010_D02
RPT_009_D02
```

Do not reinterpret legacy `human/hominin` naming as proof of a unique human species identity. Identity remains an emergent/materialization question, not a label shortcut.

### 6. Numerical/replay integrity

Where stages claim exact replay/reconciliation, verify exact hashes/keys/shapes/axes or the stage's explicitly declared numerical tolerance.

Do not upgrade tolerance-based compatibility to exact equality.

### 7. External-engine governance

Any NEMO, Geonomics, RangeShiftR, CDMetaPOP, SLiM, Madingley or other runtime evidence must remain evidence/provider output only unless a stage explicitly promoted an ARCANA-owned result.

No majority vote and no engine may become canonical writer by implication.

### 8. Canonical-mutation audit

Determine whether any R5.8–R5.15 stage:

- changed an earlier SEALED scientific law;
- changed thresholds merely to force an outcome;
- reran/mutated an earlier sealed stage;
- introduced an untracked canonical rewrite.

Any such event blocks the integrated seal unless already authorized, traced to earliest affected authority, and fully replayed/revalidated.

## Required outputs

```text
R5_16_SOURCE_AUTHORITY.json
R5_16_PARENT_CHAIN_AUDIT.json
R5_16_LEGACY_RECONCILIATION_AUDIT.json
R5_16_NEGATIVE_RESULT_PRESERVATION.json
R5_16_EXTERNAL_ENGINE_GOVERNANCE_AUDIT.json
R5_16_INTEGRATED_AUDIT.json
```

If all integrated gates pass, a separate explicit seal artifact may then be created:

```text
R5_16_FINAL_SEAL_AUDIT.json
R5_16_FINAL_SEAL_MANIFEST.json
```

The integrated audit passing is not itself the seal.

## Seal gate

R5.16 may become SEALED only if all of the following are true:

```yaml
repository_provenance_complete: true
parent_chain_integrity: true
legacy_reconciliation_integrity: true
negative_results_preserved: true
human_lineage_governance_preserved: true
numerical_replay_claims_supported: true
external_engine_governance_preserved: true
unauthorized_canonical_mutation: false
open_scientific_gap_count: 0
open_provenance_gap_count: 0
explicit_final_seal_audit: PASS
```

Otherwise R5.16 remains CANDIDATE/BLOCKED and records the earliest exact failing dependency.

## Non-goals

R5.16 does not:

- invent new historical outcomes;
- add a new simulation merely for freshness;
- rerun R3.34–R3.39 after R5.15 proved exact artifact reuse sufficient;
- force agriculture/civilization/language/religion/state formation;
- create a named human identity;
- enable Deep biological coupling;
- automatically start the next historical phase.

## Downstream rule

Only after the explicit R5.16 seal decision may the next scientific phase be numbered and authorized. Its scope must be chosen from the state actually established by the integrated review, not from old chat roadmap labels.

---

Authorized from completed v0.6D1-R5.15 CANDIDATE on 2026-09-05.
