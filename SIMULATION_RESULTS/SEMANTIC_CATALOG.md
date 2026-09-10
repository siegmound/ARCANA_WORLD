# ARCANA WorldSim — Semantic Catalog

## Status and scope

This file is the semantic companion to `SIMULATION_RESULTS/README.md` and the machine-readable `MANIFEST.csv` / `MANIFEST.json` catalogues.

Its purpose is not to duplicate every historical audit. It records, in one stable place, what scientifically relevant payloads actually contain, what their authoritative semantics are, and what they must **not** be interpreted as.

This first cataloguing pass is intentionally bounded to the four payloads currently most relevant to the WorldSim → human-support bridge:

1. R3.18 recent environmental exposure integrals
2. R3.20 CHA2 hydrological hazard fields
3. R3.33 Holocene environmental/resource landscape
4. R5.1 cradle opportunity atlas

The catalogue will be extended incrementally as later work needs additional payloads.

### Evidence rule

Every entry separates three evidence classes:

- **Observed payload schema** — array names, shapes, dtypes and axis values inspected directly from the consolidated `.npz` file.
- **Repository authority** — semantics, status and governance explicitly established by stage manifests, audits, final seals or `ARCANA_WORLD_CURRENT_STATE.md`.
- **Interpretive restriction** — meanings that are explicitly forbidden or remain unsupported.

Presence in `SIMULATION_RESULTS/` alone does not create scientific authority.

---

# Authority summary

| Stage | Primary payload | SHA256 | Authority status | Audit / seal result |
|---|---|---|---|---|
| R3.18 | `R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz` | `54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70` | SEALED CORE AUTHORITY | 172/172 PASS |
| R3.20 | `R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz` | `4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14` | SEALED CORE AUTHORITY | 108/108 PASS |
| R3.33 | `R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz` | `5fd7b11df5051245551aa2d23ce334b0a540f171e85ac8a451c603eb63f685b9` | SEALED SCIENTIFIC REPLAY AUTHORITY | 33/33 PASS |
| R5.1 | `R5_1_CRADLE_OPPORTUNITY_ATLAS.npz` | `9d4a70780785bdda7d1a51549d3b842450d6b563cab44684229157f073707caa` | SEALED DERIVED SCIENTIFIC AUTHORITY | 51/51 PASS |

Important status nuance:

- some pre-seal output manifests retain a historical `CANDIDATE` status;
- later final-seal evidence supersedes that stage-local candidate label for the sealed artifacts listed above;
- the sealed status does **not** change the intended semantics or turn diagnostic indices into new physical quantities.

---

# R3.18 — Recent environmental exposure integrals

## Primary artifact

`SIMULATION_RESULTS/01_CORE_WORLD_HISTORY/local_runs/v0_6D1_R3_18/R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz`

SHA256:

`54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70`

## Authority

Stage: `v0.6D1-R3.18`

Final sealed verdict:

`PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED`

Audit closure: **172/172 PASS**.

Repository authority states that the payload contains environmental **integrals / accumulated exposures**, not point-in-time environmental states.

The biology state remains at 125 ka while the physical environment is integrated to 0 ka. R3.18 itself does not advance biology.

## Temporal structure

Observed scalar axes:

| Field | Value | Meaning |
|---|---:|---|
| `biology_state_age_ma` | 0.125 | retained biology state age = 125 ka |
| `physical_end_age_ma` | 0.0 | environmental integration reaches present |
| `transport_boundary_age_ma` | 0.0625 | transport phase boundary = 62.5 ka |

Authoritative integration windows:

- inherited R3.17 exposure: 125–120 ka = 5,000 years
- recent R3.18 exposure: 120–0 ka = 120,000 years
- full environmental macrostep: 125–0 ka = 125,000 years
- transport phase 1: 125–62.5 ka = 62,500 years
- transport phase 2: 62.5–0 ka = 62,500 years

## Spatial grid

All spatial exposure fields use the native World1 grid:

`90 × 180`

`reference_population` arrays add a leading six-member axis:

`6 × 90 × 180`

## Observed payload schema

The payload contains **31 arrays**.

### Scalar age / boundary arrays

| Array | Shape | dtype |
|---|---:|---|
| `biology_state_age_ma` | `(1,)` | float64 |
| `physical_end_age_ma` | `(1,)` | float64 |
| `transport_boundary_age_ma` | `(1,)` | float64 |

### `recent_120_to_0` group

| Array | Shape | dtype |
|---|---:|---|
| `recent_120_to_0__land_support` | `(90,180)` | float64 |
| `recent_120_to_0__temperature_c` | `(90,180)` | float64 |
| `recent_120_to_0__aridity_index` | `(90,180)` | float64 |
| `recent_120_to_0__browse_forage` | `(90,180)` | float64 |
| `recent_120_to_0__low_forage` | `(90,180)` | float64 |
| `recent_120_to_0__wetland_forage` | `(90,180)` | float64 |
| `recent_120_to_0__reference_population` | `(6,90,180)` | float64 |

### `full_125_to_0` group

Same seven variables, prefixed with `full_125_to_0__`.

### `transport_phase1_125_to_62p5` group

Same seven variables, prefixed with `transport_phase1_125_to_62p5__`.

### `transport_phase2_62p5_to_0` group

Same seven variables, prefixed with `transport_phase2_62p5_to_0__`.

## Semantic meaning

These fields are accumulated environmental exposure terms over their named windows.

Consequently:

- `temperature_c` in this raw R3.18 bundle is an integrated temperature exposure term; it is **not** a point temperature in °C despite the inherited variable suffix;
- forage fields are accumulated forage exposure terms;
- `land_support` is accumulated land-access/support exposure;
- `reference_population` is the governed simulation reference-population exposure carried through the bundle.

`reference_population` is explicitly **not physical human population** and **not carrying capacity**.

R5.17-B3 later duration-normalizes these governed integrals and derives transparent phase deltas without changing the sealed R3.18 source payload.

## Allowed downstream use

Suitable for:

- reconstructing long-window recent environmental exposure;
- comparing 125–62.5 ka and 62.5–0 ka forcing regimes;
- deriving duration-normalized environmental support variables when an explicit derivation contract is used;
- enforcing the recent environmental history used by later replay stages.

## Forbidden / unsupported interpretation

Do not:

- read the integrated `temperature_c` arrays as instantaneous temperature maps;
- interpret `reference_population` as human population;
- interpret `reference_population` as `K(x,t)`;
- relabel `wetland_forage` as freshwater availability;
- infer physical freshwater supply from `aridity_index` without an explicit physical model.

## Main support evidence

- `90_SUPPORT_CORE/.../R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json`
- `90_SUPPORT_CORE/.../R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json`
- `93_SUPPORT_VALIDATION/.../FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json`
- `ARCANA_WORLD_CURRENT_STATE.md`

---

# R3.20 — CHA2 hydrological hazard fields

## Primary artifact

`SIMULATION_RESULTS/01_CORE_WORLD_HISTORY/local_runs/v0_6D1_R3_20/R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz`

SHA256:

`4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14`

## Authority

Stage: `v0.6D1-R3.20`

Final sealed verdict:

`PASS_R320_CHA2_YOUNGER_DRYAS_CLASS_MAGNITUDE_AND_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_LAYER_SEALED`

Audit closure: **108/108 PASS**.

The stage confirms a Younger-Dryas-class CHA2 event magnitude and seals a derived 15–11 ka hydrological-hazard layer without cultural targeting.

## Temporal structure

Observed:

- `years_before_book`: 80 states
- encoded range: `-14950` to `-11000`
- exact cadence: 50 years

Spatial hazard arrays therefore have shape:

`80 × 90 × 180`

## Observed payload schema

The payload contains **10 arrays**.

| Array | Shape | dtype | Semantic class |
|---|---:|---|---|
| `years_before_book` | `(80,)` | int32 | temporal axis |
| `severe_flood_candidate_fraction` | `(80,)` | float64 | global/aggregate diagnostic fraction |
| `pluvial_flood_potential_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `coastal_inundation_potential_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `compound_flood_hazard_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `drying_hazard_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `ecosystem_hydrological_shock_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `hydrological_disruption_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `meltwater_system_pressure_index` | `(80,90,180)` | float32 | diagnostic hazard ranking |
| `raw_support_loss_fraction` | `(80,90,180)` | float32 | derived support-loss diagnostic |

## Semantic meaning

The authority explicitly defines these arrays as **diagnostic/ranking hazard indices**, not direct physical measurements.

The event-level freshwater forcing used in the CHA2 climate mechanism is not equivalent to local terrestrial freshwater supply.

The sealed audit also establishes that:

- human population was not used;
- settlement targets were not used;
- religion/flood-myth targets were not used;
- biology was not modified;
- R3.19 H0 state was not modified.

## Allowed downstream use

Suitable for:

- identifying relative hydrological disruption/hazard during CHA2;
- applying an explicitly governed hazard penalty or risk term in later replay;
- temporal comparison at 50-year resolution within the sealed interval;
- locating candidate flood/drying/disruption stress zones.

## Forbidden / unsupported interpretation

Do not interpret these arrays as:

- flood depth;
- guaranteed inundation extent;
- river discharge;
- local rainfall amount;
- freshwater supply;
- persistent water access;
- navigability;
- human carrying capacity.

`meltwater_system_pressure_index > 1` is possible in the observed payload and must not be silently clipped or redefined unless a downstream contract explicitly requires a transformation.

## Main support evidence

- `90_SUPPORT_CORE/.../R3_20_CHA2_YD_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_SUMMARY.json`
- `93_SUPPORT_VALIDATION/.../FORMAL_AUDIT_SEALED_v0_6D1_R3_20.json`
- `ARCANA_WORLD_CURRENT_STATE.md`

---

# R3.33 — Holocene environmental/resource landscape

## Primary artifact

`SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz`

SHA256:

`5fd7b11df5051245551aa2d23ce334b0a540f171e85ac8a451c603eb63f685b9`

## Authority

Stage: `v0.6D1-R3.33`

Final sealed verdict:

`PASS_R333_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE_ANIMAL_ECOLOGICAL_PARTNERS_DOMESTICATION_TRAJECTORIES_AND_FOOD_PRODUCTION_EMERGENCE_SEALED`

Final seal: **33/33 PASS, 0 failed**.

The earlier output manifest records the stage as a candidate; the later final seal closes the stage and validates this payload as part of the sealed R3.33 artifact set.

## Environmental authority

Repository authority defines the environmental semantics as:

`DIRECT_SEALED_PALEOCLIMATE_PROVIDER_DOWNSAMPLED_TO_WORLD1_90X180_AND_INTERPOLATED_ONLY_BETWEEN_PROVIDER_SNAPSHOTS`

The authority binds the sealed paleoclimate provider by SHA256 and states that the environmental landscape consumes spatial temperature, precipitation, NPP and land-mask information from that provider.

## Temporal structure

Observed `anchor_age_ka`:

`[20, 15, 14, 13, 12, 11, 10, 5, 0]`

Nine environmental anchor states.

## Spatial grid

World1 grid:

`90 × 180`

## Observed payload schema

The payload contains **3 arrays**:

| Array | Shape | dtype |
|---|---:|---|
| `anchor_age_ka` | `(9,)` | float64 |
| `environment_variable_names` | `(7,)` | Unicode string |
| `environment_fields` | `(9,90,180,7)` | float64 |

Observed variable order in the final axis:

1. `temperature_anomaly_c`
2. `precipitation_factor`
3. `npp_factor`
4. `land_fraction`
5. `hydroclimate_resource_index`
6. `coastal_edge_index`
7. `sea_level_anomaly_m`

## Semantic meaning

This is a compact Holocene environmental/resource representation derived from the sealed paleoclimate authority and used by the existing scientific replay chain.

The resource layer was used as environmental context for ecological-partner/domestication work.

The R3.33 authority explicitly states:

`plant_resource_semantics = NPP_AND_PRECIPITATION_RESOURCE_FIELD_ONLY_NOT_EXPLICIT_PLANT_SPECIES`

and:

`plant_species_registry_available = false`

Therefore this stage does not itself create explicit plant species or agriculture.

## Allowed downstream use

Suitable for:

- Holocene environmental context at the nine sealed anchor ages;
- relative precipitation/productivity/resource opportunity;
- sea-level/coastal-edge context;
- interpolation only under the semantics inherited from the sealed provider/replay contract;
- environmental input to later food-production, settlement-opportunity, or support derivations when variable meaning is preserved.

## Forbidden / unsupported interpretation

Do not:

- treat `hydroclimate_resource_index` as physical freshwater supply;
- convert `precipitation_factor` directly into rainfall volume without a calibrated baseline;
- interpret `npp_factor` as human-edible productivity;
- infer explicit plant taxa from this landscape;
- infer agriculture from this environmental payload alone;
- extrapolate the sparse anchor system outside its governed temporal semantics without a new contract.

## Main support evidence

- `91_SUPPORT_SCIENTIFIC_REPLAY/.../R3_33_OUTPUT_MANIFEST.json`
- `91_SUPPORT_SCIENTIFIC_REPLAY/.../R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY.json`
- `91_SUPPORT_SCIENTIFIC_REPLAY/.../R3_33_INTEGRATED_AUDIT.json`
- `93_SUPPORT_VALIDATION/.../R3_33_FINAL_SEAL_AUDIT.json`

---

# R5.1 — Cradle opportunity atlas

## Primary artifact

`SIMULATION_RESULTS/03_DERIVED_REPLAY/outputs/v0_6D1_R5_1/R5_1_CRADLE_OPPORTUNITY_ATLAS.npz`

SHA256:

`9d4a70780785bdda7d1a51549d3b842450d6b563cab44684229157f073707caa`

## Authority

Stage: `v0.6D1-R5.1`

Final sealed status:

`PASS_R51_EMERGENT_HOMINID_CRADLE_AND_ECOLOGICAL_NICHE_DISCOVERY_SEALED`

Final scientific seal:

- `sealed = true`
- `scientific_seal = true`
- **51/51 checks PASS**

The earlier `R5_1_OUTPUT_MANIFEST.json` is a candidate-stage manifest. `R5_1_FINAL_SEAL.json` is the later authority for the sealed artifact set.

## Governing semantic restriction

The final seal explicitly defines cradle semantics as:

`MODEL_DERIVED_CRADLE_OPPORTUNITY_REGIONS_NOT_OBSERVED_LITERAL_BIRTHPLACE`

Therefore the atlas identifies model-derived regions of ecological/demographic opportunity. It does not claim an observed literal geographic birthplace.

## Temporal structure

Observed `age_ma`:

- oldest sample: 3.0 Ma
- youngest sample: 0.2 Ma
- sample count: 141
- observed step: 0.02 Ma = 20 kyr

The age axis is descending toward the present.

## Candidates

Observed `candidate_ids`:

- `RPT_010_D02`
- `RPT_009_D02`

These match the retained candidate cohort established by later WorldSim authority.

## Spatial grid

Observed axes:

- `lat`: 90 values from -89 to +89
- `lon`: 180 values from -179 to +179

Spatial fields use:

`90 × 180`

## Observed payload schema

The atlas contains **29 arrays**.

### Axes and identifiers

| Array | Shape | dtype |
|---|---:|---|
| `age_ma` | `(141,)` | float64 |
| `candidate_ids` | `(2,)` | Unicode string |
| `lat` | `(90,)` | float64 |
| `lon` | `(180,)` | float64 |

### Candidate spatial occupancy / support surfaces

| Array | Shape | dtype |
|---|---:|---|
| `population_mass_fraction` | `(2,90,180)` | float32 |
| `ensemble_time_presence_fraction` | `(2,90,180)` | float32 |
| `age_presence_fraction` | `(2,90,180)` | float32 |
| `member_coverage_fraction` | `(2,90,180)` | float32 |

### Environment / persistence surfaces

| Array | Shape | dtype |
|---|---:|---|
| `land_persistence_fraction` | `(90,180)` | float32 |
| `forage_q10` | `(90,180)` | float32 |
| `forage_median` | `(90,180)` | float32 |
| `wetland_forage_median` | `(90,180)` | float32 |
| `temperature_mean_c` | `(90,180)` | float32 |
| `temperature_std_c` | `(90,180)` | float32 |
| `aridity_mean` | `(90,180)` | float32 |
| `aridity_std` | `(90,180)` | float32 |

### Global temporal connectivity

| Array | Shape | dtype |
|---|---:|---|
| `corridor_connectivity_median_by_age` | `(141,)` | float32 |

### Candidate-specific temporal series

For each of `RPT_010_D02` and `RPT_009_D02`, the atlas contains one `(141,)` float32 series for each of:

- `effective_population_median_by_age`
- `deme_count_median_by_age`
- `ecological_breadth_median_by_age`
- `dispersal_capacity_median_by_age`
- `genetic_diversity_proxy_median_by_age`
- `adaptive_integration_median_by_age`

## Semantic meaning

The atlas combines model-derived spatial persistence/opportunity summaries with the two retained candidate lineages and their time-varying demographic/ecological descriptors.

The final seal records:

- 300 region records;
- 161 region families;
- 12 all-threshold robust families;
- no majority-vote authority mechanism;
- no new external engine used as target authority;
- canonical parent state unchanged;
- Deep biological coupling off.

The atlas is therefore a derived, sealed scientific product rather than a replacement for the underlying physical WorldSim state.

## Allowed downstream use

Suitable for:

- identifying persistent ecological opportunity regions for retained lineages;
- comparing candidate spatial support;
- examining land persistence, forage, wetland forage, temperature and aridity context over the modelled cradle window;
- using corridor connectivity and lineage-level temporal summaries in later geographically explicit replay;
- prioritizing regions for downstream support/corridor analysis.

## Forbidden / unsupported interpretation

Do not interpret the atlas as:

- an observed archaeological birthplace map;
- a literal historical settlement map;
- a physical freshwater-supply map;
- human carrying capacity;
- proof that the highest-scoring region must contain the unique origin of a lineage;
- authority to overwrite the underlying WorldSim environment.

`wetland_forage_median` remains a forage/environmental variable and must not be relabelled as persistent freshwater access.

## Main support evidence

- `92_SUPPORT_DERIVED_REPLAY/.../R5_1_OUTPUT_MANIFEST.json`
- `92_SUPPORT_DERIVED_REPLAY/.../R5_1_FINAL_SEAL.json`
- `92_SUPPORT_DERIVED_REPLAY/.../R5_1_INTEGRATED_AUDIT.json`
- `92_SUPPORT_DERIVED_REPLAY/.../R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json`

---

# Cross-payload relationship for R5.17

The four catalogued products serve different roles and must remain separated:

| Payload | What it supplies | What it does NOT supply |
|---|---|---|
| R3.18 | long-window integrated environmental exposure | instantaneous environment, freshwater supply, human population, K(x,t) |
| R3.20 | high-resolution CHA2 hydrological disruption/hazard | river flow, flood depth, freshwater availability, navigability |
| R3.33 | sealed Holocene environmental/resource anchors | calibrated terrestrial water balance, explicit plant species, agriculture |
| R5.1 | sealed lineage-specific cradle opportunity/persistence atlas | literal birthplace, settlement map, freshwater supply, carrying capacity |

### Immediate implication

Existing WorldSim results already provide substantial environmental, resource, persistence, hazard and lineage-geography information.

Therefore R5.17 should reuse these products before creating any new derived layer.

However none of the four catalogued products currently supplies an authoritative direct field for:

- physical terrestrial freshwater supply;
- hydrological reliability / persistent water access;
- navigable-water opportunity;
- human-edible productivity;
- physical persons-per-cell carrying capacity `K(x,t)`.

Those quantities remain separate derivation problems and must not be fabricated by renaming existing proxies.

---

# Catalog extension policy

When another payload becomes necessary, extend this document with the same structure:

1. exact consolidated path;
2. SHA256;
3. stage and final authority status;
4. observed array schema;
5. temporal coverage and cadence;
6. spatial grid;
7. authoritative semantic meaning;
8. allowed downstream uses;
9. forbidden / unsupported interpretations;
10. support/authority file pointers.

Do not perform a repository-wide rediscovery unless the consolidated catalogue is proven incomplete for the specific required quantity.

---

Updated: 2026-09-10
