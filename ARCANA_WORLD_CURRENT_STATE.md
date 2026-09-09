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
R5_17_CONTRACT: R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md

R5_17_A_CENSUS: R5_17_INPUT_CAPABILITY_CENSUS.json
R5_17_B1_BINDING: R5_17_B_SOURCE_BINDING.json
R5_17_B2_INSPECTION_TOOL: R5_17_B_INSPECT_CANONICAL_INPUTS.py
R5_17_B2_INSPECTION_MANIFEST: R5_17_B_LOCAL_CANONICAL_PAYLOAD_INSPECTION.json
R5_17_B2_MANIFEST_COMMIT: 8b31046b38f6cebe10a97f07e5757dee6a16c278
R5_17_B3_DESIGN: R5_17_B3_HUMAN_ENVIRONMENTAL_WATER_SUPPORT_DESIGN.md
R5_17_B3_DESIGN_COMMIT: eeddb3961b8543d5886730b76718e5b8d5585ba6
R5_17_B3_RUNNER: R5_17_B3_DERIVE_ENVIRONMENTAL_SUPPORT.py
R5_17_B3_RUNNER_COMMIT: bc01c577154ace91d85f2c185b3b9a58137c3895
R5_17_B3_MANIFEST: R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_MANIFEST.json
R5_17_B3_MANIFEST_COMMIT: 64e1921e2c9d3568193f11ed330b87d722bfa8d5
R5_17_B4_FRESHWATER_SOURCE_AUDIT: R5_17_B4_FRESHWATER_SOURCE_AUDIT.json
R5_17_B4_COMMIT: afc69cbd139448712330635563656758e781c163
R5_17_B5_INSPECTION_TOOL: R5_17_B5_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py
R5_17_B5_TOOL_COMMIT: c1729c667ae31dbdb5f48a22d7c93eb07f0e25a1
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.17-B4
LATEST_STATUS: PASS
LATEST_VERDICT: PASS_R517_B4_FRESHWATER_SOURCE_GAP_CONFIRMED

ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION

ACTIVE_SUBPHASE: R5.17-B5
ACTIVE_SUBPHASE_STATUS: READY_FOR_LOCAL_SEALED_PALEOCLIMATE_PAYLOAD_INSPECTION
ACTIVE_SUBPHASE_SCOPE: SEALED_PALEOCLIMATE_PAYLOAD_HASH_AND_SCHEMA_INSPECTION
NEXT_ACTION: LOCATE_R314_V061_PAYLOADS_RUN_B5_INSPECTOR_AND_IMPORT_MANIFEST
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
       -> B5  READY sealed paleoclimate payload inspection
```

R5.16 explicitly seals the integrated R5.8–R5.15 continuation. Earlier individual candidate labels remain historical stage statuses and are not independently rewritten.

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

The long-term post-R5.16 target remains a simulation-derived macrohistorical reference to narrative Year 0, with population and civilization geography emerging from the simulated world rather than being prescribed.

## R5.17-A/B1 result

The capability census found that base geometry and lineage state are reusable, while human-facing climate/environment, hydrology, food support, hazards, resources, Deep and carrying-capacity semantics require explicit derivation.

Three exact SEALED payloads are bound:

```yaml
R3_18_ENVIRONMENT_INTEGRAL_BUNDLE_SHA256: 54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70
R3_19_0KA_CHECKPOINT_SHA256: f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406
R3_20_HYDROLOGICAL_HAZARD_SHA256: 4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14
```

R3.18 `reference_population` is not physical human population and not carrying capacity. R3.20 hazard indices are diagnostic/ranking fields, not flood depths, guaranteed inundation, freshwater supply or an automatic human-support penalty.

## R5.17-B2 result

```yaml
STATUS: PASS_R517_B2_LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION
ALL_SHA256_MATCH: true
R3_18_ARRAY_COUNT: 31
R3_19_ARRAY_COUNT: 12
R3_20_ARRAY_COUNT: 10
ALL_INSPECTED_ARRAYS_FINITE: true
FILENAME_MISMATCH_FOUND: false
NEW_HISTORICAL_SIMULATION: false
EXTERNAL_ENGINE_EXECUTION: false
CANONICAL_MUTATION: false
```

Structural facts:

- native grid: 90 × 180;
- R3.19 `lat`, `lon`, exact 0-ka `current_accessible`; accessible cells = 4130;
- R3.20: 80 states, exact 50-year cadence, -14950 to -11000 years before book.

### Critical R3.18 semantics

The SEALED R3.18 audit explicitly defines the canonical payload as an **integral bundle** and its two transport windows as 62.5-kyr integrals. Therefore its large `temperature_c`, `aridity_index`, `land_support` and forage values are cumulative exposure/integral quantities, not instantaneous snapshots.

Authorized durations:

```yaml
full_125_to_0: 125000 years
recent_120_to_0: 120000 years
transport_phase1_125_to_62p5: 62500 years
transport_phase2_62p5_to_0: 62500 years
```

## R5.17-B3 completed result

```yaml
STATUS: PASS_R517_B3_NATIVE_ENVIRONMENTAL_SUPPORT_EXPOSURE_DERIVATION
ALL_INPUT_SHA256_MATCH: true
DERIVED_ARRAY_COUNT: 44
INTEGRAL_CLOSURE: PASS_ROUNDOFF_SCALE
FRESHWATER_SUPPORT_MATERIALIZED: false
K_X_T_MATERIALIZED: false
NEW_HISTORICAL_SIMULATION: false
EXTERNAL_ENGINE_EXECUTION: false
CANONICAL_MUTATION: false
```

B3 duration-normalized the governed R3.18 integrals, derived transparent phase deltas, preserved the exact R3.19 0-ka accessibility endpoint, and copied the R3.20 hazard arrays unchanged within their original 15–11 ka scope.

B3 does not authorize conversion of forage, aridity, wetland exposure or hazard values into physical human freshwater supply or carrying capacity.

## R5.17-B4 completed result

B4 asked whether the sources already bound to R5.17 contain a direct governed persistent freshwater availability/reliability field suitable for civilization-facing support.

```yaml
STATUS: PASS_R517_B4_FRESHWATER_SOURCE_GAP_CONFIRMED
DIRECT_BOUND_FRESHWATER_SUPPLY_FIELD: false
DIRECT_BOUND_FRESHWATER_RELIABILITY_FIELD: false
PERSISTENT_WATER_ACCESS_FIELD: false
NAVIGABLE_WATER_OPPORTUNITY_FIELD: false
NEW_COMPUTE_REQUIRED: true
EXTERNAL_PROVIDER_REQUIRED_AT_THIS_STAGE: false
```

This is a bounded source audit, not a claim that no freshwater-relevant raw quantity exists anywhere in historical artifacts. R3.14 binds exact historical v0.6.1 paleoclimate payloads which must be inspected before choosing the minimum native derivation.

Forbidden shortcuts remain:

- do not relabel `wetland_forage` as freshwater;
- do not invert `aridity_index` and call it freshwater without a physical model;
- do not interpret R3.20 hazards as water supply;
- do not extrapolate R3.20 outside 15–11 ka without explicit derivation;
- do not collapse these layers into `K` yet.

## Active work — R5.17-B5

Inspector: `R5_17_B5_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py`

R3.14 freezes the following historical v0.6.1 payload hashes:

```yaml
recent_paleoclimate_history.npz: be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1
paleoclimate_spatial_snapshots.npz: a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd
shoreline_state_I.npz: f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85
```

B5 must locate these exact local payloads, verify their SHA256 values, load with `allow_pickle=False`, inspect every array key/shape/dtype/range, and record only lexical hydrology candidate names before any semantic promotion.

B5 performs no freshwater derivation, no historical simulation and no `K` computation. If it passes, B6 may bind physically interpretable inputs and design the minimum freshwater-support computation.

Explicit unresolved quantities remain:

```yaml
FRESHWATER_SUPPORT: MISSING_NEEDS_NEW_DERIVATION
HYDROLOGICAL_RELIABILITY: PARTIAL_NEEDS_NEW_DERIVATION
NAVIGABLE_WATER_OPPORTUNITY: NOT_MATERIALIZED
HUMAN_EDIBLE_PRODUCTIVITY: NOT_MATERIALIZED
PHYSICAL_PERSONS_PER_CELL_K: NOT_MATERIALIZED
```

## Repository tracking rule

Commit every scientific/implementation/governance result and update this ledger. Never infer `SEALED` from PASS alone. Do not bootstrap from old uploaded package names when this repository authority is available; retrieve historical artifacts only for targeted provenance or semantic work.

---

Updated: 2026-09-09 (Europe/Rome project date).
