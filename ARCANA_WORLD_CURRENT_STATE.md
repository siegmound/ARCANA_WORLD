# ARCANA WorldSim — Current State Authority

> Compact continuation ledger. Use this file and its repository pointers as the default bootstrap. Historical R3/R4/R5 material is archive/provenance unless a targeted audit requires it.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
BASELINE_IMPORT_COMMIT: 15ef285e554658125744056ec9266d9b0ed4c0ba
RECOVERY_LEDGER: R5_15_R5_17_RECOVERY_LEDGER.md

LAST_SEAL_ARTIFACT: R5_16_FINAL_SEAL_AUDIT.json
LAST_SEAL_COMMIT: d96235d8425c0f0fb9322ea01213cccb0c6e02f2
POST_R5_16_OBJECTIVE: ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md
SCIENTIFIC_ENGINE_SUITABILITY_GATE: SCIENTIFIC_ENGINE_SUITABILITY_GATE.md
R5_17_CONTRACT: R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md

R5_17_B6_DESIGN: R5_17_B6_FRESHWATER_PHYSICAL_INPUT_BINDING_DESIGN.md
R5_17_B6_H0_SEMANTIC_INSPECTOR: R5_17_B6_INSPECT_PALEOCLIMATE_SEMANTICS.py
R5_17_B6_H1_NATIVE_HYDROLOGY_INSPECTOR: R5_17_B6_H1_LOCATE_AND_INSPECT_NATIVE_HYDROLOGY.py
R5_17_B6_H2_PROVENANCE_AUDITOR: R5_17_B6_H2_AUDIT_NATIVE_HYDROLOGY_PROVENANCE.py
R5_17_B6_H3_GENERATOR_SEMANTIC_AUDITOR: R5_17_B6_H3_AUDIT_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.py
R5_17_B6_H4_EXPORT_PHYSICAL_EVIDENCE_AUDITOR: R5_17_B6_H4_ADJUDICATE_V055I_EXPORT_AND_PHYSICAL_SUFFICIENCY.py
R5_17_B6_D1_REPLAY_CONTRACT_EXTRACTOR: R5_17_B6_D1_EXTRACT_CANONICAL_HYDROLOGY_REPLAY_CONTRACT.py
R5_17_B6_D2_INPUT_BINDING_PREFLIGHT: R5_17_B6_D2_BIND_CANONICAL_PALEOHYDROLOGY_INPUTS.py
R5_17_B6_D2R_SEASONAL_BASELINE_RECOVERY: R5_17_B6_D2R_RECOVER_SEASONAL_CLIMATE_BASELINE.py
R5_17_B6_D2A_IDENTITY_ADJUDICATION: R5_17_B6_D2A_ADJUDICATE_SEASONAL_BASELINE_IDENTITY.py
R5_17_B6_D2B_PROMOTION_AUTHORITY: R5_17_B6_D2B_AUDIT_V055I_SEASONAL_PROMOTION_AUTHORITY.py
R5_17_B6_D2C_RECONSTRUCTION_PREFLIGHT: R5_17_B6_D2C_PREPARE_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION.py
R5_17_B6_D2C1_SHORELINE_ADAPTER: R5_17_B6_D2C1_ADJUDICATE_SHORELINE_LAND_MASK_ADAPTER.py
R5_17_B6_D2D_REPLAY_RECONSTRUCTION: R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I.py
R5_17_B6_D2D1_RUNTIME_BINDING: R5_17_B6_D2D1_RESOLVE_EXACT_SEASONAL_GENERATOR_RUNTIME_BINDING.py
R5_17_B6_D2D2_NONEXACT_DIAGNOSTICS: R5_17_B6_D2D2_DIAGNOSE_F_REPLAY_NONEXACTNESS.py
R5_17_B6_D2D3_SERIALIZED_REPLAY: R5_17_B6_D2D3_VALIDATE_SERIALIZED_MARGIN_REPLAY_AND_RECONSTRUCT_I.py
R5_17_B6_D2D4_ULP_GATE: R5_17_B6_D2D4_FLOAT32_ULP_EQUIVALENCE_AND_I_RECONSTRUCTION.py
R5_17_B6_D2D5_FULL_CHAIN_REPLAY: R5_17_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY_AND_I_RECONSTRUCTION.py
R5_17_B6_D3_PALEOHYDROLOGY_REPLAY: R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.py
R5_17_B6_COMPLETION_REGISTER: R5_17_B6_COMPLETION_REGISTER.md
R5_17_B6_EVIDENCE_MANIFEST: R5_17_B6_EVIDENCE_MANIFEST.json
R5_17_B6_D4_FRESHWATER_RESULT: R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json
R5_17_B7_CONTRACT: R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md
R5_17_B7_A1_PREFLIGHT: R5_17_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_PREFLIGHT.json
EXECUTION_REFERENCE_INDEX_MD: ARCANA_EXECUTION_REFERENCE_INDEX.md
EXECUTION_REFERENCE_INDEX_JSON: ARCANA_EXECUTION_REFERENCE_INDEX.json

SIMULATION_RESULTS_ROOT: SIMULATION_RESULTS
SIMULATION_RESULTS_SEMANTIC_CATALOG: SIMULATION_RESULTS/SEMANTIC_CATALOG.md
SIMULATION_RESULTS_MANIFEST_JSON: SIMULATION_RESULTS/MANIFEST.json
SIMULATION_RESULTS_MANIFEST_CSV: SIMULATION_RESULTS/MANIFEST.csv
SIMULATION_RESULTS_CATALOGUE_COMMIT: 1fe30b5bd6e5d5410860710db479720485a89094
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.17-B6
LATEST_STATUS: PASS
LATEST_VERDICT: PASS_R517_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_MATERIALIZED

LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A1
LATEST_INTERNAL_VERDICT: PASS_R517_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT

ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION

ACTIVE_SUBPHASE: R5.17-B7
ACTIVE_SUBPHASE_STATUS: A1_PREFLIGHT_COMPLETE__A2_READY
ACTIVE_SUBPHASE_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT
NEXT_ACTION: RUN_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION
```

## Continuation chain

`	ext
R5.7 SEALED
  -> R5.8-R5.15 completed candidate continuation
  -> R5.16 SEALED integrated end-of-legacy closure
  -> R5.17 AUTHORIZED_IN_PROGRESS
       -> A-B5 PASS
       -> B6 COMPLETED, NOT SEALED
            -> canonical hydrology/paleohydrology replay completed
            -> freshwater support materialized
            -> hydrological reliability materialized
            -> heavy reconstructed payloads hash-registered, not committed
            -> K(x,t) not materialized
       -> B7 ACTIVE
            -> A1 PASS source/schema/coverage preflight
            -> A2 NEXT semantic binding + temporal coverage adjudication
`

R5.16 remains the latest explicit seal.
R5.17-B6 is the latest completed substantive subphase and remains intentionally unsealed.
R5.17-B7 is active; B7-A1 is complete and B7-A2 is authorized next.
## Fixed parent/governance state

```yaml
R5_16_STATUS: SEALED
R5_16_FINAL: PASS_R516_END_OF_LEGACY_INTEGRATED_RECONCILIATION_SEALED
RETAINED_LINEAGES:
  - RPT_010_D02
  - RPT_009_D02
DEEP_BIOLOGICAL_COUPLING: false
UNIQUE_HUMAN_IDENTITY_MATERIALIZED: false
```

R5.17 is a WorldSim -> human-support bridge, not yet a civilization/polity/trade/war simulation. It must not tune to a target population or desired civilization outcome, invent missing resource/water variables, or convert opaque proxies directly to `K(x,t)`.

## Bound recent authorities

```yaml
R3_18_ENVIRONMENT_INTEGRAL_BUNDLE_SHA256: 54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70
R3_19_0KA_CHECKPOINT_SHA256: f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406
R3_20_HYDROLOGICAL_HAZARD_SHA256: 4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14

R3_14_RECENT_PALEOCLIMATE_HISTORY_SHA256: be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1
R3_14_PALEOCLIMATE_SPATIAL_SNAPSHOTS_SHA256: a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd
V055I_SHORELINE_STATE_SHA256: f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85
```

R3.18 `reference_population` is not physical human population and not carrying capacity. R3.18 environmental fields are integrated exposures. R3.20 hazard indices are diagnostic/ranking fields, not flood depths, guaranteed inundation, freshwater supply or an automatic human-support penalty.

## R5.17-B6 completion authority

R5.17-B6 is COMPLETED and intentionally NOT SEALED.

Primary completion pointers:

`yaml
COMPLETION_REGISTER: R5_17_B6_COMPLETION_REGISTER.md
EVIDENCE_MANIFEST: R5_17_B6_EVIDENCE_MANIFEST.json
D4_RESULT: R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json
EXECUTION_REFERENCE_INDEX: ARCANA_EXECUTION_REFERENCE_INDEX.md
`

Terminal B6 result:

`yaml
STATUS: PASS_R517_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_MATERIALIZED
FRESHWATER_SUPPORT_MATERIALIZED: true
HYDROLOGICAL_RELIABILITY_MATERIALIZED: true
K_X_T_MATERIALIZED: false
CANONICAL_MUTATION: false
`

The historical/native hydrology recovery, seasonal reconstruction, replay diagnostics,
D3/D3R paleohydrology replay and H1-H4 provenance evidence remain available through
the completion register, evidence manifest and execution/reference index. They are
not repeated in this compact continuation ledger.

Semantic guardrails remain:

`	ext
wetland_forage               != freshwater supply
aridity_index                 != freshwater supply
freshwater_forcing_sv         != local freshwater access
precipitation alone           != freshwater access
R3.20 hydrological hazard     != freshwater availability
`

B6 does not materialize human-edible biological food, persons/cell, settlement,
agriculture, civilization, or K(x,t). Those remain downstream.
## Default simulation result catalogue

`SIMULATION_RESULTS/` is the default repository catalogue before historical-tree search.

```yaml
CATALOGUE_RECORDS: 863
SEMANTICALLY_VERIFIED_RECORDS: 4
SEMANTICALLY_PENDING_RECORDS: 859
CATALOGUE_AUTHORITY_COMMIT: 1fe30b5bd6e5d5410860710db479720485a89094
```

Pending semantic metadata means not yet catalogued, not invalid or rejected.

## Scientific provider / engine selection policy

Before any new material scientific computation, apply `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md`:

```text
1. reuse scientifically sufficient governed ARCANA authority;
2. otherwise reuse a suitable already validated specialist provider;
3. otherwise audit and introduce a justified specialist provider;
4. only otherwise implement the minimum custom ARCANA computation.
```

For R5.17-B6 hydrology, H4 already selected `REUSE_CANONICAL_ARCANA`; external hydrology providers are not authorized. Geonomics, NEMO, SLiM/tskit/msprime/pyslim, CDMetaPOP and RangeShiftR remain available evidence providers for later spatial-population/genetic/connectivity subquestions when their scientific domains become relevant; availability alone does not authorize their use.

---

<!-- R517_B6_TO_B7_TRANSITION_BEGIN -->

## R5.17 authoritative subphase transition - B6 -> B7

This block supersedes earlier R5.17 subphase-status statements in this file.

STAGE: v0.6D1-R5.17
STAGE_STATUS: ACTIVE

R5_17_LATEST_COMPLETED_SUBPHASE: R5.17-B6
R5_17_B6_STATUS: COMPLETED
R5_17_B6_SEALED: false

FRESHWATER_SUPPORT_MATERIALIZED: true
HYDROLOGICAL_RELIABILITY_MATERIALIZED: true
K_X_T_MATERIALIZED: false

R5_17_ACTIVE_SUBPHASE: R5.17-B7
R5_17_ACTIVE_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT
R5_17_B7_STATUS: ACTIVE__A1_COMPLETE

NEXT_OPERATION:
  R5.17-B7-A2
  SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION

EXECUTION_REFERENCE_INDEX:
  ARCANA_EXECUTION_REFERENCE_INDEX.md
  ARCANA_EXECUTION_REFERENCE_INDEX.json
  tools/build_arcana_execution_reference_index.py

MICRO_SEAL_CREATED: false
CANONICAL_MUTATION: false

B7 must construct the natural biological-resource layer before any application
of human technology, processing, storage, management, domestication,
agriculture or civilization dynamics.

The inherited A1 forage vector is authorized only as a trophic-resource proxy.
Its original generator is not recoverable from available repository Git
history and it must not be relabelled as physical biomass, human calories or
carrying capacity.

<!-- R517_B6_TO_B7_TRANSITION_END -->
