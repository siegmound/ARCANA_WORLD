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

SIMULATION_RESULTS_ROOT: SIMULATION_RESULTS
SIMULATION_RESULTS_SEMANTIC_CATALOG: SIMULATION_RESULTS/SEMANTIC_CATALOG.md
SIMULATION_RESULTS_MANIFEST_JSON: SIMULATION_RESULTS/MANIFEST.json
SIMULATION_RESULTS_MANIFEST_CSV: SIMULATION_RESULTS/MANIFEST.csv
SIMULATION_RESULTS_CATALOGUE_COMMIT: 1fe30b5bd6e5d5410860710db479720485a89094
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.17-B5
LATEST_STATUS: PASS
LATEST_VERDICT: PASS_R517_B5_SEALED_PALEOCLIMATE_PAYLOAD_HASH_AND_SCHEMA_INSPECTION

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

```text
R5.7 SEALED
  -> R5.8–R5.15 completed candidate continuation
  -> R5.16 SEALED integrated end-of-legacy closure
  -> R5.17 AUTHORIZED_IN_PROGRESS
       -> A   PASS input/capability census
       -> B1  PASS environmental/hydrological source binding
       -> B2  PASS exact local payload hash/schema inspection
       -> B3  PASS native environmental exposure derivation
       -> B4  PASS direct-bound freshwater source-gap audit
       -> B5  PASS exact sealed paleoclimate payload inspection
       -> B6  IN_PROGRESS
            -> H0   PASS exact paleoclimate semantic evidence
            -> H1   BLOCKED local channel-hydrology payload absent
            -> H1R  BLOCKED payload absent across local ArcanaWorld tree
            -> H2   PASS native hydrology provenance/generator candidates recovered
            -> H3   PASS native hydrology generator semantics recovered
            -> H4   PASS exact v0.5.5I export lineage + physical sufficiency
                     decision = REUSE_CANONICAL_ARCANA
                     external hydrology provider = NOT AUTHORIZED
            -> D1   PASS canonical hydrology replay contract captured
            -> D2   PASS binding evidence; seasonal_climate_state_I originally absent
            -> D2R  recovered two surviving F-era seasonal baselines, not historical I
            -> D2A  identity lineage inspected; exact historical I identity not recoverable
            -> D2B  PASS no exact promotion authority recovered
                     decision = reconstruct with preserved provenance gap
            -> D2C  exact seasonal generator + exact shoreline I bound
            -> D2C1 PASS interface-only adapter authorized:
                     coast_state.elevation_m <- shoreline.elevation_m
                     coast_state.land_mask   <- shoreline.effective_land_mask
            -> D2D/D2D1 runtime/import path resolved
            -> D2D2/D2D3/D2D4 diagnosed apparent non-exactness caused by serialized reload path
            -> D2D5 PASS exact full in-memory F chain replay
                     margin replay exact = true
                     seasonal replay exact = true
                     hydrology replay exact = true
                     tolerance promotion = false
                     reconstructed seasonal I materialized = true
            -> D3   READY canonical book-era + snapshot paleohydrology replay
```

R5.16 remains the latest explicit seal. B6 is not sealed or complete yet.

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

## R5.17-B6 native hydrology authority

R3.14 consumes `inputs/v0_5_5I_SEALED/channel_hydrology_state_I.npz` with at least:

```text
mean_discharge_m3_s
drainage_area_km2
receiver_flat
lake_candidate_mask
depression_depth_m
```

The historical I payload itself is no longer materialized locally. H2/H3/H4 recovered and adjudicated the governed source lineage:

```yaml
src/arcana_worldsim/surface/hydrology.py:
  sha256: 34584d0e8a8696b26e4026aad28f362850b7e9b98bb7754cc5cab8e4d282ff42
src/arcana_worldsim/regional/hydrology.py:
  sha256: e32d766e3e700dd2da22adda3c09b0327e503d1ab9df663eb1c23e6730832b87
src/arcana_worldsim/climate/water_balance.py:
  sha256: 23090416ef8234d43689171241d80d8ca2609882455bd30761de30301e5bfb61
src/arcana_worldsim/finalization/hydrology.py:
  sha256: 29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351
src/arcana_worldsim/finalization/seasonal.py:
  sha256: 3ec12145617ae63e6ce9d9bd123c159525f83925f9257f1138f3490bb3e70de2
src/arcana_worldsim/morphogenesis/margins.py:
  sha256: f8998f2213938eb80a2b414300c2acc6dc298bc5327a6fb081951fde136d7d52
```

H4 decision remains:

```yaml
REUSE_CANONICAL_ARCANA: true
EXTERNAL_PROVIDER_AUTHORIZED: false
STRUCTURAL_SEMANTICS_SUFFICIENT: true
PHYSICAL_WATER_BALANCE_SUFFICIENT: true
DISCHARGE_SEMANTICS_SUFFICIENT: true
```

Recovered physical semantics include precipitation, evapotranspiration, infiltration, groundwater return, storage, cryo-storage, runoff, network routing, receiver topology, drainage area, depressions, lakes, runoff depth/volume and `mean_discharge_m3_s`.

## D2 reconstruction closure

The original historical `seasonal_climate_state_I.npz` was not recovered. D2B established that neither surviving F baseline can honestly be promoted as the lost I payload. The provenance gap remains explicit.

D2C1 authorized only an interface adapter; it does not alter grid cells:

```yaml
coast_state.elevation_m: shoreline_state_I.elevation_m
coast_state.land_mask: shoreline_state_I.effective_land_mask
```

D2D5 then reproduced the explicit recovered F runner chain fully in memory:

```text
build_margin_morphogenesis(root, 917231)
  -> build_seasonal_climate(root, margin)
  -> build_channel_hydrology(root, margin, seasonal)
```

All three native serialized F outputs were array-for-array exact against their historical payloads:

```yaml
MARGIN_REPLAY_EXACT: true
SEASONAL_REPLAY_EXACT: true
HYDROLOGY_REPLAY_EXACT: true
MAX_ABS_DIFFERENCE: 0.0
ABSOLUTE_OR_RELATIVE_TOLERANCE_AUTHORIZED: false
ULP_TOLERANCE_AUTHORIZED: false
```

This proves that the earlier D2D3/D2D4 discrepancies came from an artificial serialize/reload boundary that did not exist in the historical runner, not from a generator/runtime divergence.

The governed reconstructed I seasonal payload is:

```yaml
PATH: R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz
SHA256: bd25948db09ecc50409a7d18df1fc6d08350820fd2f0f1d06aeb5a2b98de98a7
HYDROLOGY_FIELDS_PRESENT: true
HISTORICAL_PAYLOAD_IDENTITY_CLAIMED: false
CANONICAL_MUTATION: false
```

It is a new governed reconstructed artifact, not the original lost `seasonal_climate_state_I.npz`.

## D3 authorized implementation

`R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.py` is authorized to:

1. verify the D2D5 exact-chain gate and the reconstructed I seasonal artifact;
2. regenerate seasonal I in memory from the exact shoreline I and verify array equality with the reconstructed seasonal payload;
3. materialize a reconstructed book-era I channel-hydrology payload through exact `build_channel_hydrology(...)`;
4. replay the five exact R3.14 paleoclimate snapshots using:
   - `temperature_anomaly_c`;
   - `precipitation_factor_relative_book`;
   - `paleo_land_mask`;
   - sea-level anomaly bound from exact recent paleoclimate history;
5. reuse the exact ARCANA seasonal PET temperature-response law for snapshot PET composition;
6. require the R3.14-consumed hydrology fields and basic physical/structural validity in every output;
7. preserve `historical_payload_identity_claimed: false` and `freshwater_support_materialized: false`.

D3 must not materialize `K(x,t)`, silently call physical discharge human support, or introduce another hydrology provider.

## B6 scientific rule

Do not approximate paleodischarge by multiplying book-era `mean_discharge_m3_s` by `precipitation_factor_relative_book`. The adjudicated canonical model contains ET, infiltration, groundwater return, storage, cryo-storage, runoff and routing. D3 therefore reruns the governed hydrology consumer with time-specific climate and coast inputs.

Explicit unresolved human-facing quantities remain:

```yaml
FRESHWATER_SUPPORT: MISSING_NEEDS_NEW_DERIVATION
HYDROLOGICAL_RELIABILITY: PARTIAL_NEEDS_NEW_DERIVATION
NAVIGABLE_WATER_OPPORTUNITY: NOT_MATERIALIZED
HUMAN_EDIBLE_PRODUCTIVITY: NOT_MATERIALIZED
PHYSICAL_PERSONS_PER_CELL_K: NOT_MATERIALIZED
```

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
