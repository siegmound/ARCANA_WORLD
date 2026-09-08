# ARCANA WorldSim — Current State Authority

> Compact repository-resident continuation ledger. Historical R3/R4/R5 material is provenance/archive unless specifically required.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
BASELINE_IMPORT_COMMIT: 15ef285e554658125744056ec9266d9b0ed4c0ba
RECOVERY_LEDGER: R5_15_R5_17_RECOVERY_LEDGER.md
R5_16_CONTRACT: R5_16_INTEGRATED_END_OF_LEGACY_SEAL_REVIEW_CONTRACT.md
R5_16_FINAL_SEAL_MANIFEST: R5_16_FINAL_SEAL_MANIFEST.json
R5_16_FINAL_SEAL_MANIFEST_COMMIT: adab41b3d8385374a90a575c683ba16e49484945
R5_16_FINAL_SEAL_AUDIT: R5_16_FINAL_SEAL_AUDIT.json
R5_16_FINAL_SEAL_AUDIT_COMMIT: d96235d8425c0f0fb9322ea01213cccb0c6e02f2
R5_16_FINAL_SEAL_AUDIT_GIT_BLOB_SHA: 33555e64b741a19853c8ba190f956499a9dcb861
POST_R5_16_OBJECTIVE: ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md
POST_R5_16_OBJECTIVE_COMMIT: 692f44f2b2854db15e87424630122129c083b865
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.16
LATEST_STATUS: SEALED
LATEST_VERDICT: PASS_R516_END_OF_LEGACY_INTEGRATED_RECONCILIATION_SEALED
ACTIVE_STAGE: none
ACTIVE_STAGE_STATUS: NOT_AUTHORIZED
NEXT_PHASE: UNNUMBERED_OBJECTIVE_FIXED_NOT_YET_AUTHORIZED
NEXT_PHASE_OBJECTIVE: SIMULATION_DERIVED_MACROHISTORICAL_REFERENCE_TO_YEAR_0
```

## Continuation chain now sealed

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
  -> v0.6D1-R5.16   SEALED integrated end-of-legacy closure
```

R5.16 explicitly seals the integrated R5.8–R5.15 continuation reconciled against the SEALED legacy authorities R3.34–R3.39. Earlier candidate labels remain historical stage statuses; they are now contained in the explicit integrated R5.16 seal and must not be independently promoted or rewritten.

## R5.16 final result

```yaml
STAGE: v0.6D1-R5.16
STATUS: SEALED
FINAL_STATUS: PASS_R516_END_OF_LEGACY_INTEGRATED_RECONCILIATION_SEALED
FINAL_SEAL_CHECKS: 16/16 PASS

REPOSITORY_PROVENANCE_COMPLETE: true
PARENT_CHAIN_INTEGRITY: true
LEGACY_RECONCILIATION_INTEGRITY: true
NEGATIVE_RESULTS_PRESERVED: true
HUMAN_LINEAGE_GOVERNANCE_PRESERVED: true
NUMERICAL_REPLAY_CLAIMS_SUPPORTED: true
EXTERNAL_ENGINE_GOVERNANCE_PRESERVED: true
UNAUTHORIZED_CANONICAL_MUTATION: false
OPEN_SCIENTIFIC_GAPS: 0
OPEN_PROVENANCE_GAPS: 0
```

### Preserved scientific/governance state

```yaml
RETAINED_LINEAGES:
  - RPT_010_D02
  - RPT_009_D02

DEEP_BIOLOGICAL_COUPLING: false
UNIQUE_HUMAN_IDENTITY_MATERIALIZED: false
NEW_EXTERNAL_ENGINE_EXECUTION_IN_R5_16: false
FRESH_SCIENTIFIC_RERUN_IN_R5_16: false
```

The seal preserves the negative outcomes and identity-governance constraints established by the reconciled chain. It does not create agriculture, reproductive-control domestication, plant domesticates, village/city/state, class hierarchy, currency/market, named culture, named language, named religion/myth, ethnicity, or a unique human identity where those states were not validly materialized.

Numerical claims retain their original semantics. In particular, tolerance-based compatibility is not upgraded to exact equality; the R5.14 continuous domestication trajectories remain qualified as within one float64 epsilon while its explicitly exact replay/recomputation claims remain exact.

External-engine evidence remains provider/evidence output unless explicitly promoted by ARCANA-owned authority. No engine majority vote or implicit canonical writer is introduced by R5.16.

## End-of-legacy objective status

The recovered completion strategy targeted:

```text
bulk legacy reconciliation
-> repair only if real gaps exist
-> integrated end-of-legacy seal
```

R5.15 completed the bulk reconciliation with six Class-A exact sealed-artifact reuses and zero repair requirement. Because no repair block was required, numbering compressed and R5.16 became the integrated end-of-legacy seal review. R5.16 has now completed that objective and is explicitly SEALED.

## Fixed post-R5.16 scientific objective

The post-R5.16 WorldSim program now has a repository-fixed objective charter:

`ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md`

The long-term target is a simulation-derived macrohistorical reference to narrative Year 0, not a prewritten exact history. The simulation should allow population, settlement geography, trade networks, civilization/polity structure, warfare, collapse and recovery to emerge from WorldSim geography, climate, hydrology, ecology, resources, human state and Deep.

Key fixed principles are:

- Year-0 global and regional human population is an emergent result, not a preset target;
- carrying capacity changes through time with environment, resources, trade, technology, infrastructure, Deep, war, disaster and degradation/recovery;
- population may be represented computationally through weighted units, super-individuals, settlements or regional stocks rather than literal person-level agents;
- downscaled/local simulations and interpolation/scaling are allowed only with explicit scaling semantics and validation of important nonlinear effects;
- long or multi-seed simulations may be executed on local hardware and imported with repository-tracked configs, runtime identity, logs/manifests/hashes and adjudication;
- Geonomics, SLiM, NEMO, RangeShiftR, CDMetaPOP and other justified providers remain evidence providers rather than implicit canonical writers;
- macrohistory should support migration, trade, strategic settlement, civilization emergence, polity dynamics, war, collapse and successor states where later stages scientifically authorize those mechanisms;
- final Year-0 outputs should preferentially report uncertainty/ensemble distributions rather than false exactness;
- named cultures, religions, languages, ethnicities and detailed individual history are not required for objective completion unless separately materialized later.

The broader objective is complete when ARCANA can defensibly use the simulation to answer where large populations and civilizations are plausible, approximately how many people the world supports by Year 0, how major regions are connected by resources/trade/Deep, and what broad demographic/political history plausibly produced that state.

## Next work rule

There is currently no authorized post-R5.16 stage, but the scientific destination is now fixed by the post-R5.16 macrohistory objective charter.

Before assigning a new stage number:

1. choose the smallest scientifically useful unresolved component of the fixed macrohistorical objective;
2. inspect what sealed R5.16 and existing WorldSim layers already provide;
3. determine whether existing ARCANA outputs are sufficient or whether a new simulation/provider is justified;
4. design scaling/ensemble semantics before any downscaled demographic run is treated as a world-population result;
5. write a repository-tracked contract for that phase;
6. only then authorize and number the next stage.

No repair or rerun is required by the R5.16 seal itself. New computation is permitted when it materially advances the fixed macrohistorical objective.

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

Updated: 2026-09-08 (Europe/Rome project date).
