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
R5_17_B3_DESIGN: R5_17_B3_HUMAN_ENVIRONMENTAL_WATER_SUPPORT_DESIGN.md
R5_17_B3_RUNNER: R5_17_B3_DERIVE_ENVIRONMENTAL_SUPPORT.py
R5_17_B3_MANIFEST: R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_MANIFEST.json
R5_17_B4_FRESHWATER_SOURCE_AUDIT: R5_17_B4_FRESHWATER_SOURCE_AUDIT.json
R5_17_B5_INSPECTION_TOOL: R5_17_B5_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py
R5_17_B5_LOCATOR: R5_17_B5_LOCATE_AND_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py
R5_17_B5_RESULT_SUMMARY: R5_17_B5_SEALED_PALEOCLIMATE_PAYLOAD_INSPECTION_SUMMARY.json
R5_17_B6_DESIGN: R5_17_B6_FRESHWATER_PHYSICAL_INPUT_BINDING_DESIGN.md
R5_17_B6_SEMANTIC_INSPECTOR: R5_17_B6_INSPECT_PALEOCLIMATE_SEMANTICS.py
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.17-B5
LATEST_STATUS: PASS
LATEST_VERDICT: PASS_R517_B5_SEALED_PALEOCLIMATE_PAYLOAD_HASH_AND_SCHEMA_INSPECTION

ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION

ACTIVE_SUBPHASE: R5.17-B6
ACTIVE_SUBPHASE_STATUS: READY_FOR_LOCAL_PALEOCLIMATE_SEMANTIC_INSPECTION
ACTIVE_SUBPHASE_SCOPE: FRESHWATER_PHYSICAL_INPUT_SEMANTIC_BINDING_AND_MINIMUM_HYDROLOGY_DESIGN
NEXT_ACTION: RUN_B6_EXACT_SOURCE_SEMANTIC_INSPECTOR_AND_ADJUDICATE_MINIMUM_NATIVE_HYDROLOGY
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
       -> B6  READY physical-input semantic binding / minimum hydrology design
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

## Bound recent authorities

```yaml
R3_18_ENVIRONMENT_INTEGRAL_BUNDLE_SHA256: 54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70
R3_19_0KA_CHECKPOINT_SHA256: f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406
R3_20_HYDROLOGICAL_HAZARD_SHA256: 4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14
```

R3.18 `reference_population` is not physical human population and not carrying capacity. R3.18 environmental fields are integrated exposures. R3.20 hazard indices are diagnostic/ranking fields, not flood depths, guaranteed inundation, freshwater supply or an automatic human-support penalty.

## R5.17-B2 result

```yaml
STATUS: PASS_R517_B2_LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION
ALL_SHA256_MATCH: true
R3_18_ARRAY_COUNT: 31
R3_19_ARRAY_COUNT: 12
R3_20_ARRAY_COUNT: 10
ALL_INSPECTED_ARRAYS_FINITE: true
NEW_HISTORICAL_SIMULATION: false
EXTERNAL_ENGINE_EXECUTION: false
CANONICAL_MUTATION: false
```

Native recent grid is 90 × 180. R3.19 exact 0-ka accessible cells = 4130. R3.20 contains 80 states at exact 50-year cadence from -14950 to -11000 years before book.

## R5.17-B3 result

```yaml
STATUS: PASS_R517_B3_NATIVE_ENVIRONMENTAL_SUPPORT_EXPOSURE_DERIVATION
ALL_INPUT_SHA256_MATCH: true
DERIVED_ARRAY_COUNT: 44
INTEGRAL_CLOSURE: PASS_ROUNDOFF_SCALE
FRESHWATER_SUPPORT_MATERIALIZED: false
K_X_T_MATERIALIZED: false
```

B3 duration-normalized the governed R3.18 integrals, derived transparent phase deltas, preserved the exact R3.19 0-ka accessibility endpoint, and copied the R3.20 hazard arrays unchanged within their original 15–11 ka scope.

## R5.17-B4 result

```yaml
STATUS: PASS_R517_B4_FRESHWATER_SOURCE_GAP_CONFIRMED
DIRECT_BOUND_FRESHWATER_SUPPLY_FIELD: false
DIRECT_BOUND_FRESHWATER_RELIABILITY_FIELD: false
PERSISTENT_WATER_ACCESS_FIELD: false
NAVIGABLE_WATER_OPPORTUNITY_FIELD: false
NEW_COMPUTE_REQUIRED: true
EXTERNAL_PROVIDER_REQUIRED_AT_THIS_STAGE: false
```

B4 is a bounded source audit. It required inspection of the exact historical R3.14-bound v0.6.1 paleoclimate payloads before choosing the minimum new hydrology computation.

## R5.17-B5 completed result

Exact R3.14-frozen payloads were found locally and hash-validated:

```yaml
recent_paleoclimate_history.npz:
  sha256: be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1
  arrays: 23
paleoclimate_spatial_snapshots.npz:
  sha256: a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd
  arrays: 11
shoreline_state_I.npz:
  sha256: f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85
  arrays: 17
ALL_SHA256_MATCH: true
BLOCKED_ALLOW_PICKLE_FALSE: none
```

Scientifically relevant B5 discoveries:

- `precipitation_factor_relative_book[5,720,1440]` exists and is the only direct lexical hydrology candidate in the spatial snapshot bundle; observed overall range is approximately 0.525904–1.000000.
- `snapshot_year_before_book[5]`, `paleo_land_mask[5,720,1440]`, `temperature_anomaly_c`, and `npp_factor_relative_book` provide related paleoclimate context.
- `shoreline_state_I` supplies 0.25-degree `elevation_m`, land/ocean geometry and a 0.125-degree subgrid mask.
- `canonical_freshwater_pulse_sv` and `freshwater_forcing_sv` exist in the 1201-step climate history but are freshwater/ocean-circulation forcings, not local terrestrial supply.

B5 does not promote any of these fields to freshwater support. The full generated B5 inspection manifest remains local evidence; the repository stores a compact result summary to avoid duplicating a large structural dump.

## Active work — R5.17-B6

B6 must verify the exact R3.14-frozen source:

```yaml
src/arcana_worldsim/paleoclimate/model.py:
  sha256: de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f
```

The local semantic inspector records exact snapshot years, per-snapshot precipitation statistics and bounded source evidence around precipitation/hydrology identifiers without executing the historical source.

B6 semantic rule:

- relative precipitation + geometry may support a later relative hydroclimatic/drainage opportunity calculation;
- physical freshwater supply requires defensible water-balance semantics (absolute precipitation or calibrated baseline, evapotranspiration, infiltration/recharge, storage/routing/reliability as applicable);
- if these semantics are absent, R5.17 must introduce the minimum explicit hydrology model/provider rather than fabricate them.

Explicit unresolved quantities remain:

```yaml
FRESHWATER_SUPPORT: MISSING_NEEDS_NEW_DERIVATION
HYDROLOGICAL_RELIABILITY: PARTIAL_NEEDS_NEW_DERIVATION
NAVIGABLE_WATER_OPPORTUNITY: NOT_MATERIALIZED
HUMAN_EDIBLE_PRODUCTIVITY: NOT_MATERIALIZED
PHYSICAL_PERSONS_PER_CELL_K: NOT_MATERIALIZED
```

## Forbidden shortcuts

- do not relabel `wetland_forage` as freshwater;
- do not invert `aridity_index` and call it freshwater without a physical model;
- do not interpret R3.20 hazards as water supply;
- do not treat ocean-circulation freshwater forcing as local terrestrial supply;
- do not extrapolate sparse snapshots into continuous physical water history without an explicit contract;
- do not collapse these layers into `K` yet.

## Repository tracking rule

Commit every scientific/implementation/governance result and update this ledger. Never infer `SEALED` from PASS alone. Do not bootstrap from old uploaded package names when this repository authority is available; retrieve historical artifacts only for targeted provenance or semantic work.

---

Updated: 2026-09-09 (Europe/Rome project date).
