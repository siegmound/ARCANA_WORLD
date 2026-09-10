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
R5_17_B6_SEMANTIC_LOCATOR: R5_17_B6_LOCATE_AND_INSPECT_PALEOCLIMATE_SEMANTICS.py
R5_17_B6_H1_NATIVE_HYDROLOGY_INSPECTOR: R5_17_B6_H1_LOCATE_AND_INSPECT_NATIVE_HYDROLOGY.py

SIMULATION_RESULTS_ROOT: SIMULATION_RESULTS
SIMULATION_RESULTS_README: SIMULATION_RESULTS/README.md
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

ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION

ACTIVE_SUBPHASE: R5.17-B6
ACTIVE_SUBPHASE_STATUS: H0_LOCAL_SEMANTIC_PASS__H1_NATIVE_HYDROLOGY_AUDIT_READY
ACTIVE_SUBPHASE_SCOPE: FRESHWATER_PHYSICAL_INPUT_SEMANTIC_BINDING_AND_MINIMUM_HYDROLOGY_DESIGN
NEXT_ACTION: RUN_B6_H1_NATIVE_HYDROLOGY_DISCOVERY_THEN_AUDIT_AUTHORITY_LINEAGE_AND_GENERATOR
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
            -> H0 local exact paleoclimate semantic evidence captured
            -> H1 READY native channel-hydrology discovery/inspection
            -> H2 pending authority-lineage/generator semantic audit
            -> suitability adjudication pending
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

B6 H0 verifies the exact R3.14-frozen source:

```yaml
src/arcana_worldsim/paleoclimate/model.py:
  sha256: de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f
```

Local H0 evidence reported exact source/payload hash matches, five precipitation snapshots at `[-21000, -14000, -12900, -12000, 0]`, and no materialization of freshwater support, runoff, hydrological reliability or K.

Critically, the inspected paleoclimate source loads:

```text
inputs/v0_5_5I_SEALED/channel_hydrology_state_I.npz
```

and consumes at least:

```text
mean_discharge_m3_s
drainage_area_km2
receiver_flat
lake_candidate_mask
depression_depth_m
```

The paleoclimate source itself does not expose a complete water-balance chain: lexical H0 evidence does not establish runoff, evapotranspiration, infiltration, recharge or storage semantics. This absence cannot be interpreted as absence of ARCANA hydrology because the model explicitly consumes the separate v0.5.5I channel-hydrology state.

Therefore H1 must discover and structurally inspect all local/archive `channel_hydrology_state_I.npz` candidates before provider selection. H1 does not assume an authority SHA in advance and cannot adjudicate canonical identity merely from filename/path coincidence.

After H1, H2 must recover the governed payload lineage and generator semantics, including the physical meaning of `mean_discharge_m3_s`, routing/topology construction and temporal applicability.

B6 semantic rule:

- relative precipitation + geometry may support a later relative hydroclimatic/drainage opportunity calculation;
- existing native discharge/drainage evidence must be audited before any replacement or duplication;
- physical freshwater supply requires defensible water-balance semantics (absolute precipitation or calibrated baseline, evapotranspiration, infiltration/recharge, storage/routing/reliability as applicable);
- only after H2 may the Scientific Engine Suitability Gate choose reuse, specialist derivation, dedicated hydrology provider or minimum custom ARCANA computation.

Explicit unresolved quantities remain:

```yaml
FRESHWATER_SUPPORT: MISSING_NEEDS_NEW_DERIVATION
HYDROLOGICAL_RELIABILITY: PARTIAL_NEEDS_NEW_DERIVATION
NAVIGABLE_WATER_OPPORTUNITY: NOT_MATERIALIZED
HUMAN_EDIBLE_PRODUCTIVITY: NOT_MATERIALIZED
PHYSICAL_PERSONS_PER_CELL_K: NOT_MATERIALIZED
```

## Default simulation result catalogue

`SIMULATION_RESULTS/` is the default repository catalogue for locating consolidated WorldSim scientific/replay results before searching historical stage trees or archival packages.

```yaml
CATALOGUE_RECORDS: 863
SEMANTICALLY_VERIFIED_RECORDS: 4
SEMANTICALLY_PENDING_RECORDS: 859
MANIFEST_JSON: SIMULATION_RESULTS/MANIFEST.json
MANIFEST_CSV: SIMULATION_RESULTS/MANIFEST.csv
HUMAN_SEMANTIC_CATALOG: SIMULATION_RESULTS/SEMANTIC_CATALOG.md
CATALOGUE_AUTHORITY_COMMIT: 1fe30b5bd6e5d5410860710db479720485a89094
```

The four currently verified semantic payload authorities are:

```text
R3.18  environmental exposure integrals
R3.20  hydrological hazard diagnostic rankings
R3.33  Holocene environmental/resource landscape
R5.1   model-derived cradle opportunity atlas
```

Their machine-readable manifest records include temporal coverage, spatial grid, semantic class, primary use, forbidden interpretations, authority evidence, and seal checks.

Absence of verified semantic metadata on the remaining 859 records means **not yet semantically catalogued**. It must not be interpreted as invalid, non-authoritative, or scientifically rejected.

The result catalogue improves discovery and semantic routing only. It does not rewrite the original stage authority, promote candidate stages, alter payload SHA256 identities, or change scientific meaning.

For new work, prefer this lookup order:

1. `SIMULATION_RESULTS/MANIFEST.json` for machine-readable discovery;
2. `SIMULATION_RESULTS/SEMANTIC_CATALOG.md` for human semantic guidance;
3. the referenced original/seal authority artifacts for adjudication;
4. historical repository trees only when targeted provenance requires them.

This catalogue registration does not complete R5.17-B6. B5 remains the latest completed R5.17 subphase until B6 H0/H1/H2 evidence and suitability adjudication are repository-reviewed and committed as a completed result.

## Scientific provider / engine selection policy

Before designing any new material scientific computation, apply `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md`.

Standing decision order:

```text
1. reuse scientifically sufficient governed ARCANA authority;
2. otherwise reuse a suitable already validated specialist provider;
3. otherwise audit and introduce a justified specialist provider;
4. only otherwise implement the minimum custom ARCANA computation.
```

The scientific question chooses the tool. Existing engines such as NEMO, Geonomics, SLiM, CDMetaPOP and RangeShiftR/RangeShifter are routed by domain and assumptions rather than used indiscriminately. Other specialist engines/libraries may be introduced only after a suitability audit and reproducible runtime/version binding.

External engines remain evidence/providers under ARCANA orchestration; they do not become implicit canonical writers and no majority vote between engines defines ARCANA history. A PASS provider run still requires explicit scientific adjudication before canonical promotion.

For hydrology specifically, inspect the exact governed ARCANA channel/topography/hydrology authority and its generator before authorizing a new hydrological model. Do not duplicate or replace native hydrology until its semantics have been shown insufficient.

This policy is persistent governance and does not itself advance R5.17-B6 or authorize any new provider execution.

## Forbidden shortcuts

- do not relabel `wetland_forage` as freshwater;
- do not invert `aridity_index` and call it freshwater without a physical model;
- do not interpret R3.20 hazards as water supply;
- do not treat ocean-circulation freshwater forcing as local terrestrial supply;
- do not assume `mean_discharge_m3_s` is a valid persistent-human-water field before generator semantics and temporal support are verified;
- do not extrapolate sparse snapshots or static channel state into continuous physical water history without an explicit contract;
- do not collapse these layers into `K` yet.

## Repository tracking rule

Commit every scientific/implementation/governance result and update this ledger. Never infer `SEALED` from PASS alone. Do not bootstrap from old uploaded package names when this repository authority is available; retrieve historical artifacts only for targeted provenance or semantic work.

---

Updated: 2026-09-11 (Europe/Rome project date).
