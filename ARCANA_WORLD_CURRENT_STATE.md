# ARCANA WorldSim — Current State Authority

> Compact repository-resident continuation ledger. Historical R3/R4/R5 artifacts are provenance/archive unless specifically required. This file, together with the pointed repository artifacts, is the default bootstrap for new ARCANA WorldSim chats.

## Repository

```yaml
PROJECT: ARCANA WorldSim
REPOSITORY: siegmound/ARCANA_WORLD
BRANCH: main
BASELINE_IMPORT_COMMIT: 15ef285e554658125744056ec9266d9b0ed4c0ba
RECOVERY_LEDGER: R5_15_R5_17_RECOVERY_LEDGER.md

R5_16_FINAL_SEAL_MANIFEST: R5_16_FINAL_SEAL_MANIFEST.json
R5_16_FINAL_SEAL_AUDIT: R5_16_FINAL_SEAL_AUDIT.json
R5_16_FINAL_SEAL_AUDIT_COMMIT: d96235d8425c0f0fb9322ea01213cccb0c6e02f2

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
R5_17_B_LOCAL_INSPECTION_MANIFEST: R5_17_B_LOCAL_CANONICAL_PAYLOAD_INSPECTION.json
R5_17_B_LOCAL_INSPECTION_MANIFEST_COMMIT: 8b31046b38f6cebe10a97f07e5757dee6a16c278
R5_17_B3_DESIGN: R5_17_B3_HUMAN_ENVIRONMENTAL_WATER_SUPPORT_DESIGN.md
R5_17_B3_DESIGN_COMMIT: eeddb3961b8543d5886730b76718e5b8d5585ba6
```

## Authoritative continuation state

```yaml
LAST_EXPLICITLY_CONFIRMED_SEALED: v0.6D1-R5.16
LATEST_COMPLETED: v0.6D1-R5.17-B2
LATEST_STATUS: PASS
LATEST_VERDICT: PASS_R517_B2_LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION

ACTIVE_STAGE: v0.6D1-R5.17
ACTIVE_STAGE_STATUS: AUTHORIZED_IN_PROGRESS
ACTIVE_STAGE_SCOPE: HUMAN_SUPPORT_CAPACITY_AND_CIVILIZATION_GEOGRAPHY_FOUNDATION

ACTIVE_SUBPHASE: R5.17-B3
ACTIVE_SUBPHASE_STATUS: DESIGN_READY
ACTIVE_SUBPHASE_SCOPE: HUMAN_ENVIRONMENTAL_AND_WATER_SUPPORT_DERIVATION
NEXT_ACTION: IMPLEMENT_SMALLEST_NATIVE_ARCANA_B3_NUMERIC_DERIVATION

NEXT_PHASE_OBJECTIVE: SIMULATION_DERIVED_MACROHISTORICAL_REFERENCE_TO_YEAR_0
```

## Continuation chain

```text
v0.6D1-R5.7   SEALED
  -> R5.8–R5.15 completed candidate continuation
  -> v0.6D1-R5.16   SEALED integrated end-of-legacy closure
  -> v0.6D1-R5.17   AUTHORIZED_IN_PROGRESS post-legacy human-support bridge
       -> R5.17-A   PASS input/capability census
       -> R5.17-B1  PASS environmental/hydrological source binding
       -> R5.17-B2  PASS local canonical payload hash/schema inspection
       -> R5.17-B3  DESIGN_READY environmental/water support derivation
```

R5.16 explicitly seals the integrated R5.8–R5.15 continuation reconciled against the SEALED legacy authorities. Earlier individual candidate labels remain historical statuses and must not be rewritten.

R5.17 is the first post-R5.16 scientific implementation stage. It is not yet a civilization, polity, trade or warfare simulation. It builds the bridge from SEALED WorldSim evidence to explicit human-support layers and, later in R5.17, baseline carrying-capacity semantics.

## R5.16 fixed parent state

```yaml
STAGE: v0.6D1-R5.16
STATUS: SEALED
FINAL_STATUS: PASS_R516_END_OF_LEGACY_INTEGRATED_RECONCILIATION_SEALED
FINAL_SEAL_CHECKS: 16/16 PASS
OPEN_SCIENTIFIC_GAPS: 0
OPEN_PROVENANCE_GAPS: 0
RETAINED_LINEAGES:
  - RPT_010_D02
  - RPT_009_D02
DEEP_BIOLOGICAL_COUPLING: false
UNIQUE_HUMAN_IDENTITY_MATERIALIZED: false
```

The seal does not itself materialize agriculture, cities, states, named cultures, religions, languages, ethnicities, trade systems, or a unique human identity.

## Fixed post-R5.16 objective

`ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md` fixes the long-term target as a **simulation-derived macrohistorical reference to narrative Year 0**, not a prewritten exact history.

Population, settlement geography, resource access, trade, polity structure, warfare, collapse and recovery are intended to emerge from WorldSim geography, climate, hydrology, ecology, resources, human state and Deep. Year-0 population must remain emergent rather than a calibration target. External runtimes remain evidence providers only and are used only when a defined subquestion benefits from them.

## R5.17 bridge objective

`R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md` requires independent, inspectable civilization-facing axes before any baseline `K(x,t)` or bounded support-capacity proxy is created.

Important governance rules:

- no target global/regional population;
- no target civilization or settlement outcome;
- no single opaque civilization score as primary authority;
- no invented missing hydrology/resources/Deep variables;
- no blind proxy-to-`K` conversion;
- no external runtime merely because it is installed;
- uncertainty and original proxy semantics must be preserved;
- a relative/bounded support proxy may precede physical persons/cell calibration if clearly labeled.

## R5.17-A result

```yaml
STATUS: PASS_R517_A_INPUT_CAPABILITY_CENSUS
NEW_HISTORICAL_SIMULATION_REQUIRED_NOW: false
EXTERNAL_ENGINE_EXECUTION_REQUIRED_NOW: false
PRIMARY_BLOCKER: no calibrated human-support/carrying-capacity bridge currently exists
```

The census established that base geometry and lineage state are reusable, while climate/environment, hydrology, food support, hazards and Deep require explicit civilization-facing derivations. Freshwater support/reliability and navigable-water opportunity are not already materialized.

## R5.17-B1 source binding

Three exact SEALED authorities are bound for the first bridge work:

```yaml
R3_18_ENVIRONMENT_INTEGRAL_BUNDLE_SHA256: 54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70
R3_19_0KA_CHECKPOINT_SHA256: f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406
R3_20_HYDROLOGICAL_HAZARD_SHA256: 4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14
```

R3.18 provides four temporal groups with `aridity_index`, `browse_forage`, `land_support`, `low_forage`, `reference_population`, `temperature_c`, and `wetland_forage`.

R3.18 `reference_population` is not physical human population and not `K`. R3.20 diagnostic hazard fields are not flood depths, guaranteed inundation, freshwater support, or a direct reliability penalty.

## R5.17-B2 completed result

The user's local canonical payloads were inspected by the repository-tracked fail-closed tool and the resulting manifest was imported into the repository.

```yaml
STATUS: PASS_R517_B2_LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION
ALL_SHA256_MATCH: true
R3_18_ARRAY_COUNT: 31
R3_19_ARRAY_COUNT: 12
R3_20_ARRAY_COUNT: 10
NONFINITE_VALUES_FOUND: false
FILENAME_MISMATCH_FOUND: false
NEW_HISTORICAL_SIMULATION: false
EXTERNAL_ENGINE_EXECUTION: false
CANONICAL_MUTATION: false
```

Important structural evidence:

- native spatial grid is 90 × 180;
- R3.19 supplies exact `lat`, `lon`, and 0-ka `current_accessible` with 4130 accessible cells;
- R3.20 supplies 80 hazard states at 50-year cadence from 14,950 to 11,000 years before book;
- all inspected arrays are finite.

### Critical R3.18 semantic clarification

The R3.18 SEALED audit explicitly defines the canonical NPZ as an **integral bundle** and the decision as recent exposure plus two 62.5-kyr transport-phase integrals. Therefore its large `temperature_c`, `aridity_index`, forage and land-support values are cumulative exposure/integral quantities, not instantaneous snapshots.

R5.17 must preserve that meaning. Duration-normalized quantities may be derived transparently using the SEALED window durations, but must initially remain labelled duration-normalized exposures unless the source unit convention supports promotion to a physical temporal mean.

## Active work — R5.17-B3

Design authority:

`R5_17_B3_HUMAN_ENVIRONMENTAL_WATER_SUPPORT_DESIGN.md`

B3 keeps independent axes for:

```text
LAND_SUPPORT_EXPOSURE
TEMPERATURE_EXPOSURE
ARIDITY_EXPOSURE
LOW_FORAGE_EXPOSURE
BROWSE_FORAGE_EXPOSURE
WETLAND_FORAGE_EXPOSURE
BIOLOGICAL_SUPPORT_DIAGNOSTICS
HYDROLOGICAL_HAZARD_VECTOR
ENVIRONMENTAL_STABILITY_DIAGNOSTICS
```

The first numeric B3 computation may:

1. load the already validated R3.18/R3.19/R3.20 payloads;
2. divide R3.18 integral fields by their explicit window durations to create duration-normalized exposure fields;
3. compute transparent phase-difference diagnostics;
4. retain R3.19 `current_accessible` only as the exact 0-ka endpoint boundary;
5. preserve R3.20 hazards unchanged by component and supported 15–11 ka coverage;
6. write a repository-importable output/manifest.

It must **not** yet:

- generate `K`;
- convert forage directly to human calories/persons;
- sum forage channels blindly;
- treat `reference_population` as humans;
- back-project the 0-ka accessibility mask across 125 kyr;
- extrapolate R3.20 hazards outside 15–11 ka;
- infer freshwater availability from low hazard;
- materialize settlements/cities/states/trade/polities.

### Explicit unresolved B3 quantities

```yaml
FRESHWATER_SUPPORT: MISSING_NEEDS_NEW_DERIVATION
HYDROLOGICAL_RELIABILITY: PARTIAL_NEEDS_NEW_DERIVATION
NAVIGABLE_WATER_OPPORTUNITY: NOT_MATERIALIZED
HUMAN_EDIBLE_PRODUCTIVITY: NOT_MATERIALIZED
PHYSICAL_PERSONS_PER_CELL_K: NOT_MATERIALIZED
```

These must remain explicit gaps until source-supported derivations are bound.

## Repository tracking rule

Every scientific, implementation, governance, calibration, replay, audit or continuation change must be represented in this repository. Commit the artifact/result, update this ledger, preserve parent/status/seal distinctions, and never infer `SEALED` from PASS alone.

Large historical R3/R4/R5 artifacts should be retrieved only for targeted provenance or semantic questions. Do not bootstrap new chats from old uploaded package names when this ledger and current repository evidence are available.

---

Updated: 2026-09-09 (Europe/Rome project date).
