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
R5_17_CONTRACT: R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md
R5_17_CONTRACT_COMMIT: 2b733d308d01e18991f9ec16f2781a5f88f004e9
R5_17_INPUT_CAPABILITY_CENSUS: R5_17_INPUT_CAPABILITY_CENSUS.json
R5_17_INPUT_CAPABILITY_CENSUS_COMMIT: b211c5acb8fcaf7cd977d63dc2ba2671700251ea
R5_17_B_SOURCE_BINDING: R5_17_B_SOURCE_BINDING.json
R5_17_B_SOURCE_BINDING_COMMIT: 01cb913daed22cf0c6207700b97e199a7ca3b7de
R5_17_B_LOCAL_INSPECTION_TOOL: R5_17_B_INSPECT_CANONICAL_INPUTS.py
R5_17_B_LOCAL_INSPECTION_TOOL_COMMIT: b88595a0f8ef45e0b811b863dc8d05eaa57d0335
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.17-B1
LATEST_STATUS: PASS
LATEST_VERDICT: PASS_R517_B1_ENVIRONMENTAL_HYDROLOGICAL_SOURCE_BINDING
ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION
ACTIVE_SUBPHASE: R5.17-B2
ACTIVE_SUBPHASE_STATUS: READY_FOR_LOCAL_CANONICAL_PAYLOAD_INSPECTION
ACTIVE_SUBPHASE_SCOPE: LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION
NEXT_PHASE_OBJECTIVE: SIMULATION_DERIVED_MACROHISTORICAL_REFERENCE_TO_YEAR_0
```

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
  -> v0.6D1-R5.16   SEALED integrated end-of-legacy closure
  -> v0.6D1-R5.17   AUTHORIZED_IN_PROGRESS post-legacy human-support bridge
       -> R5.17-A   PASS input/capability census
       -> R5.17-B1  PASS environmental/hydrological source binding
       -> R5.17-B2  READY_FOR_LOCAL_CANONICAL_PAYLOAD_INSPECTION
```

R5.16 explicitly seals the integrated R5.8–R5.15 continuation reconciled against the SEALED legacy authorities R3.34–R3.39. Earlier candidate labels remain historical stage statuses; they are contained in the explicit integrated R5.16 seal and must not be independently promoted or rewritten.

R5.17 is the first authorized post-R5.16 scientific implementation stage. It is not a civilization, polity or warfare simulation. It builds the bridge from SEALED WorldSim state to explicit human-support layers and baseline carrying-capacity semantics.

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

R5.15 completed the bulk reconciliation with six Class-A exact sealed-artifact reuses and zero repair requirement. Because no repair block was required, numbering compressed and R5.16 became the integrated end-of-legacy seal review. R5.16 has completed that objective and is explicitly SEALED.

## Fixed post-R5.16 scientific objective

The post-R5.16 WorldSim program has a repository-fixed objective charter:

`ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md`

The long-term target is a simulation-derived macrohistorical reference to narrative Year 0, not a prewritten exact history. Population, settlement geography, trade networks, civilization/polity structure, warfare, collapse and recovery are intended to emerge from WorldSim geography, climate, hydrology, ecology, resources, human state and Deep.

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

## R5.17 bridge objective

R5.17 is governed by:

`R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md`

Its purpose is to translate existing SEALED WorldSim evidence into independent civilization-facing support layers and ultimately a baseline `K(x,t)` or bounded capacity proxy. R5.17 must not tune the world to a desired population or civilization outcome.

### R5.17-A result

`R5_17_INPUT_CAPABILITY_CENSUS.json` records:

```yaml
STATUS: PASS_R517_A_INPUT_CAPABILITY_CENSUS
NEW_HISTORICAL_SIMULATION_REQUIRED_NOW: false
EXTERNAL_ENGINE_EXECUTION_REQUIRED_NOW: false
PRIMARY_BLOCKER: no calibrated human-support/carrying-capacity bridge currently exists
```

### R5.17-B1 result

`R5_17_B_SOURCE_BINDING.json` binds the exact SEALED authorities for the first bridge calculation.

The important new finding is that R3.18 already provides a directly relevant environmental integral bundle with four temporal groups and these validated fields:

```text
aridity_index
browse_forage
land_support
low_forage
reference_population
temperature_c
wetland_forage
```

Its canonical NPZ SHA256 is:

`54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70`

R3.19 provides the exact present biological/support boundary; its checkpoint NPZ SHA256 is:

`f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406`

R3.20 provides the 15–11 ka / 50-year hydrological-hazard payload; its NPZ SHA256 is:

`4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14`

The SEALED audits and hashes are repository-resident, but these canonical binary payloads are intentionally/local historically stored rather than committed to Git. This is not a provenance failure, but numeric derivation must not proceed until the local payloads are revalidated against those hashes.

## Active work rule — R5.17-B2

`R5_17_B_INSPECT_CANONICAL_INPUTS.py` is the repository-tracked fail-closed inspection tool.

R5.17-B2 must:

1. locate the three canonical NPZ payloads on the user's local WorldSim tree;
2. verify their SHA256 values exactly against SEALED authority;
3. load with `allow_pickle=False`;
4. record every array key, shape, dtype, finite/nonfinite count and numeric range;
5. write `R5_17_B_LOCAL_CANONICAL_PAYLOAD_INSPECTION.json`;
6. import that manifest back into the repository before R5.17-B3 derives any human-support variable.

The inspection is not a simulation and should be cheap. A hash mismatch fails closed and must not be bypassed by choosing a similar file.

R5.17-B must not yet:

- calibrate a desired global population;
- materialize agriculture/cities/states;
- infer trade networks or polities;
- use an external engine merely because it is available;
- generalize the R3.20 15–11 ka hazard evidence beyond its supported window without explicit derivation;
- treat R3.18 `reference_population` as physical human population or carrying capacity;
- call a relative support proxy physical carrying capacity before calibration.

If native ARCANA layers are sufficient, no external runtime is needed for R5.17-B. If a later subquestion genuinely needs Geonomics, SLiM, NEMO, RangeShiftR or CDMetaPOP, long local execution remains explicitly permitted under repository-tracked configuration and evidence.

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
