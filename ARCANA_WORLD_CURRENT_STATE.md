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
R5_17_B6_H0_SEMANTIC_LOCATOR: R5_17_B6_LOCATE_AND_INSPECT_PALEOCLIMATE_SEMANTICS.py
R5_17_B6_H1_NATIVE_HYDROLOGY_INSPECTOR: R5_17_B6_H1_LOCATE_AND_INSPECT_NATIVE_HYDROLOGY.py
R5_17_B6_H2_PROVENANCE_AUDITOR: R5_17_B6_H2_AUDIT_NATIVE_HYDROLOGY_PROVENANCE.py
R5_17_B6_H3_GENERATOR_SEMANTIC_AUDITOR: R5_17_B6_H3_AUDIT_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.py
R5_17_B6_H4_EXPORT_PHYSICAL_EVIDENCE_AUDITOR: R5_17_B6_H4_ADJUDICATE_V055I_EXPORT_AND_PHYSICAL_SUFFICIENCY.py
R5_17_B6_D1_REPLAY_CONTRACT_EXTRACTOR: R5_17_B6_D1_EXTRACT_CANONICAL_HYDROLOGY_REPLAY_CONTRACT.py
R5_17_B6_D2_INPUT_BINDING_PREFLIGHT: R5_17_B6_D2_BIND_CANONICAL_PALEOHYDROLOGY_INPUTS.py

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
LATEST_COMPLETED_INTERNAL_STEP: R5.17-B6-D1
LATEST_INTERNAL_VERDICT: PASS_R517_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT_CAPTURED

ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION

ACTIVE_SUBPHASE: R5.17-B6
ACTIVE_SUBPHASE_STATUS: H4_REUSE_CANONICAL_ARCANA_PASS__D1_REPLAY_CONTRACT_PASS__D2_READY
ACTIVE_SUBPHASE_SCOPE: FRESHWATER_PHYSICAL_DERIVATION_BINDING_AND_REPLAY_PREPARATION
NEXT_ACTION: RUN_B6_D2_CANONICAL_PALEOHYDROLOGY_INPUT_BINDING_PREFLIGHT
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
            -> H0  PASS exact paleoclimate semantic evidence
            -> H1  BLOCKED local channel-hydrology payload absent
            -> H1R BLOCKED payload absent across local ArcanaWorld tree
            -> H2  PASS native hydrology provenance/generator candidates recovered
            -> H3  PASS native hydrology generator semantics recovered
            -> H4  PASS exact v0.5.5I export lineage + physical sufficiency
                    decision = REUSE_CANONICAL_ARCANA
                    external provider = NOT AUTHORIZED
            -> D1  PASS canonical hydrology replay contract captured
            -> D2  READY exact replay-input binding preflight
            -> D3  pending canonical paleohydrology replay implementation
```

R5.16 explicitly seals the integrated R5.8–R5.15 continuation. Earlier individual candidate labels remain historical stage statuses and are not independently rewritten. B6 is not sealed or complete yet.

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

R5.17 is a WorldSim → human-support bridge, not yet a civilization/polity/trade/war simulation. It must not tune to a target population or desired civilization outcome, invent missing resource/water variables, or convert opaque proxies directly to `K(x,t)`.

## Bound recent authorities

```yaml
R3_18_ENVIRONMENT_INTEGRAL_BUNDLE_SHA256: 54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70
R3_19_0KA_CHECKPOINT_SHA256: f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406
R3_20_HYDROLOGICAL_HAZARD_SHA256: 4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14
```

R3.18 `reference_population` is not physical human population and not carrying capacity. R3.18 environmental fields are integrated exposures. R3.20 hazard indices are diagnostic/ranking fields, not flood depths, guaranteed inundation, freshwater supply or an automatic human-support penalty.

## R5.17-B4/B5 established result

B4 established that no directly bound freshwater-supply/reliability/persistent-access/navigation field exists and that a new derivation is required, but did not authorize an external provider.

B5 hash-validated the R3.14 frozen paleoclimate payloads:

```yaml
recent_paleoclimate_history.npz:
  sha256: be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1
paleoclimate_spatial_snapshots.npz:
  sha256: a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd
shoreline_state_I.npz:
  sha256: f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85
ALL_SHA256_MATCH: true
```

`precipitation_factor_relative_book[5,720,1440]` is a relative paleoprecipitation field, not physical freshwater volume. Ocean freshwater forcings in the climate history are not terrestrial freshwater supply.

## Active work — R5.17-B6

### H0/H1/H2/H3 — native hydrology recovery

The R3.14 frozen paleoclimate source consumes `inputs/v0_5_5I_SEALED/channel_hydrology_state_I.npz` with at least `mean_discharge_m3_s`, `drainage_area_km2`, `receiver_flat`, `lake_candidate_mask`, and `depression_depth_m`.

The payload itself is no longer materialized locally, but H2/H3 recovered a stable composed native source lineage:

```yaml
src/arcana_worldsim/surface/hydrology.py:
  sha256: 34584d0e8a8696b26e4026aad28f362850b7e9b98bb7754cc5cab8e4d282ff42
src/arcana_worldsim/regional/hydrology.py:
  sha256: e32d766e3e700dd2da22adda3c09b0327e503d1ab9df663eb1c23e6730832b87
src/arcana_worldsim/climate/water_balance.py:
  sha256: 23090416ef8234d43689171241d80d8ca2609882455bd30761de30301e5bfb61
src/arcana_worldsim/finalization/hydrology.py:
  sha256: 29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351
```

H3 V2 recovered drainage topology, drainage-area and lake materialization, water-balance semantics and finalized mean-discharge semantics.

### H4 — exact lineage + physical sufficiency PASS

Local H4 result:

```yaml
STATUS: PASS_R517_B6_H4_V055I_EXPORT_LINEAGE_AND_PHYSICAL_SUFFICIENCY_ADJUDICATED
DECISION: REUSE_CANONICAL_ARCANA
ALL_EXPECTED_GENERATOR_HASHES_RECOVERED: true
STRUCTURAL_SEMANTICS_SUFFICIENT: true
PHYSICAL_WATER_BALANCE_SUFFICIENT: true
DISCHARGE_SEMANTICS_SUFFICIENT: true
TARGET_PAYLOAD_LITERAL_REFERENCE_COUNT: 18
V055I_REFERENCE_COUNT: 81
DIRECT_V055I_PAYLOAD_BRIDGE_REFERENCE_COUNT: 17
EXACT_V0_5_5I_GENERATOR_IDENTITY_ADJUDICATED: true
REUSE_CANONICAL_ARCANA_AUTHORIZED: true
EXTERNAL_PROVIDER_AUTHORIZED: false
```

Recovered physical components include precipitation, evapotranspiration, infiltration, groundwater return, storage, cryo-storage, runoff, network routing, receiver network, drainage area, depressions, lakes, runoff depth/volume and `mean_discharge_m3_s`.

Scientific-engine selection for the hydrology core is therefore closed: reuse the governed ARCANA lineage. Do not introduce Wflow, PCR-GLOBWB, pyflwdir or another hydrology provider unless a later, new scientific requirement exceeds this adjudicated model.

### D1 — canonical replay contract PASS

Local D1 result:

```yaml
STATUS: PASS_R517_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT_CAPTURED
ALL_EXPECTED_GENERATOR_HASHES_RECOVERED: true
REPLAY_CONTRACT_READY_FOR_IMPLEMENTATION_DESIGN: true
REUSE_CANONICAL_ARCANA: true
EXTERNAL_PROVIDER_AUTHORIZED: false
SOURCE_EXECUTED: false
FRESHWATER_SUPPORT_MATERIALIZED: false
```

Key recovered callables include `build_climatic_hydrology(...)` and `build_channel_hydrology(project_root, coast_state, seasonal)`. D1 captures the callable/input/output contract only; it does not execute historical source.

### D2 — exact replay-input binding preflight READY

D2 must bind those exact callables to materialized baseline climate/coast inputs and the exact R3.14 paleoclimate snapshots before any replay. It must explicitly report unresolved inputs rather than synthesize replacements.

The D2 preflight is:

`R5_17_B6_D2_BIND_CANONICAL_PALEOHYDROLOGY_INPUTS.py`

A D2 PASS with `replay_execution_ready=true` authorizes design of D3 canonical paleohydrology replay. A D2 evidence PASS with unresolved inputs routes to bounded input recovery first.

### B6 scientific rule

Do not approximate paleodischarge by multiplying book-era `mean_discharge_m3_s` by `precipitation_factor_relative_book`. The adjudicated canonical model contains ET, infiltration, groundwater return, storage, cryo-storage, runoff and routing, so time-varying hydrology must preserve those semantics or explicitly document a narrower derived product.

Explicit unresolved quantities remain:

```yaml
FRESHWATER_SUPPORT: MISSING_NEEDS_NEW_DERIVATION
HYDROLOGICAL_RELIABILITY: PARTIAL_NEEDS_NEW_DERIVATION
NAVIGABLE_WATER_OPPORTUNITY: NOT_MATERIALIZED
HUMAN_EDIBLE_PRODUCTIVITY: NOT_MATERIALIZED
PHYSICAL_PERSONS_PER_CELL_K: NOT_MATERIALIZED
```

## Default simulation result catalogue

`SIMULATION_RESULTS/` is the default repository catalogue before historical tree search.

```yaml
CATALOGUE_RECORDS: 863
SEMANTICALLY_VERIFIED_RECORDS: 4
SEMANTICALLY_PENDING_RECORDS: 859
CATALOGUE_AUTHORITY_COMMIT: 1fe30b5bd6e5d5410860710db479720485a89094
```

Verified semantic payload authorities currently cover R3.18 environmental exposures, R3.20 hydrological hazard rankings, R3.33 Holocene environmental/resource landscape and R5.1 model-derived cradle opportunity atlas. Pending semantic metadata means not yet catalogued, not invalid or rejected.

## Scientific provider / engine selection policy

Before any new material scientific computation, apply `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md`:

```text
1. reuse scientifically sufficient governed ARCANA authority;
2. otherwise reuse a suitable already validated specialist provider;
3. otherwise audit and introduce a justified specialist provider;
4. only otherwise implement the minimum custom ARCANA computation.
```

For the R5.17-B6 hydrology core, H4 selected `REUSE_CANONICAL_ARCANA`. External hydrology-provider introduction is not authorized. The next task is input binding and time-varying replay preparation, not engine selection.
