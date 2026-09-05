# v0.6D1-R5.15 — R3.34–R3.39 Bulk Legacy Reconciliation Contract

## Status

```yaml
STAGE: v0.6D1-R5.15
STATUS: AUTHORIZED_NOT_COMPLETED
PARENT: v0.6D1-R5.14 CANDIDATE
SEALED_ANCESTOR: v0.6D1-R5.7
SCOPE: R3.34 through R3.39 legacy reconciliation
CANONICAL_MUTATION: forbidden unless independently justified by direct evidence
AUTO_SEAL: forbidden
```

## Scientific question

Can the complete sealed legacy block R3.34–R3.39 be reused under the R5 continuation without silently changing its scientific meaning, and if not, what is the minimum repair actually required?

This is a **bulk census/reconciliation**, not six automatic micro-stages.

## Legacy authorities in scope

```yaml
R3_34:
  domain: Producer operational taxa
  established_summary: 36 operational producer taxa; 6 archetypes x 6 variants; zero domesticates
R3_35:
  domain: Producer genetics
  established_summary: 6 traits; additive variance; breeder response; wild gene flow; no baseline domesticates
R3_36:
  domain: Producer selection ecology
  established_summary: INTENSIVE_MANAGED_FORAGER_PATHWAY; agriculture=false
R3_37:
  domain: Managed forager economy
  established_summary: DISTRIBUTED_MANAGED_FORAGER_ECONOMY; no agriculture, village/city/state, class system, currency/market, named culture, language, religion, unique identity or Deep coupling
R3_38:
  domain: Regional technological traditions
  established_summary: REGIONAL_TECHNOLOGICAL_TRADITIONS_WITH_LIMITED_BORROWING; 12 opaque regional stems
  known_validation: 44/44 PASS
R3_39:
  domain: Cultural-symbolic memory and language-divergence preconditions / interlineage identity dynamics
  known_validation:
    source_manifest: 9/9 PASS
    regression: 22/22 PASS
    final_seal: 40/40 PASS
  known_verdict: PASS_R339_CULTURAL_SYMBOLIC_MEMORY_DIRECT_CHA2_EVENT_MEMORY_LANGUAGE_DIVERGENCE_PRECONDITIONS_AND_INTERLINEAGE_IDENTITY_DYNAMICS_SEALED
  known_artifact_sha256: e575cf85e15b069e6a0ebbc1e6d895fc6a9f9bb122af0ac02703ae59d50888a1
```

These summaries are discovery anchors only. The R5.15 audit must bind to actual repository artifacts before declaring reuse class.

## Census fields required for every stage

For each of R3.34–R3.39 record:

1. parent authority;
2. time interval / temporal support;
3. scientific question;
4. exact inputs;
5. source/config/runner/test artifacts;
6. scientific outputs and manifests;
7. deterministic or stochastic semantics;
8. external runtime dependency, if any;
9. sensitivity structure;
10. materialized claims;
11. explicitly forbidden interpretations;
12. downstream consumers;
13. compatibility with current R5 invariants;
14. exact replay or recomputation capability;
15. proposed reuse class and evidence.

## Reuse classification

Each stage must be assigned exactly one class:

```text
A — exact deterministic reuse
    Artifact semantics and values can be replayed/recomputed exactly under current authority.

B — deterministic reuse within strict numerical tolerance
    Same scientific semantics, with only explicitly bounded numerical tolerance.

C — semantically reusable but requires an R5 reconciliation wrapper
    Scientific result is preserved, but interpretation/provenance must be narrowed or rebound.

D — scientifically incompatible / missing evidence
    Existing evidence is insufficient or inconsistent; targeted repair/new execution is required.
```

Class D must identify the earliest broken dependency and the smallest justified repair boundary.

## Hard governance constraints

- Do not lower thresholds to force domestication, agriculture, settlements, named cultures, languages, religions, states or identities.
- Preserve negative results.
- `RPT_010_D02` and `RPT_009_D02` remain retained human-lineage candidates unless direct evidence changes that status.
- Unique human identity remains unmaterialized unless directly established downstream.
- Deep/noetic biological coupling remains OFF for this recovered human-history block.
- Opaque regional lineage/stem codes are not ethnicities, named cultures or languages.
- Functional technology domains are not named inventions unless separately materialized.
- Census-equivalent values are not literal archaeological headcounts.
- Readiness/transition pockets are not automatically realized transitions.
- External engines are evidence providers only and are executed only when the census shows a concrete scientific need.
- No majority-vote governance across engines.

## Expected R5.15 outputs

```text
R5_15_R3_34_TO_R3_39_CENSUS.json
R5_15_DEPENDENCY_GRAPH.json
R5_15_REUSE_CLASSIFICATION.json
R5_15_GAP_REGISTER.json
R5_15_FINAL_AUDIT.json
```

Optional human-readable companion:

```text
R5_15_RECONCILIATION_REPORT.md
```

## Completion gate

R5.15 may be marked completed only when:

- all six legacy stages have repository-bound evidence;
- every required census field is populated or explicitly marked unavailable;
- every stage has one justified A/B/C/D classification;
- all cross-stage dependencies needed by downstream history are represented;
- no legacy claim has been broadened during reconciliation;
- gap register is explicit;
- audit distinguishes exact reuse from semantic reuse;
- any proposed new execution is justified by a class-D gap rather than by convenience.

A PASS of R5.15 does **not** seal the entire R5.8+ human-history branch.

## Downstream decision

```yaml
IF_ANY_CLASS_D_GAP:
  NEXT: targeted repair block (provisionally R5.16)
IF_NO_CLASS_D_GAP:
  NEXT: integrated end-of-legacy reconciliation/seal stage using the next non-empty identifier
```

Do not create an empty R5.16 solely to preserve numbering.

---

Authorized from the recovered post-R5.14 workflow on 2026-09-05.
