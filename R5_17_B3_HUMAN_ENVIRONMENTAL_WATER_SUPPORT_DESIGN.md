# v0.6D1-R5.17-B3 — Human Environmental & Water Support Derivation Design

## Authority

```yaml
STAGE: v0.6D1-R5.17
SUBPHASE: R5.17-B3
PARENT: PASS_R517_B2_LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION
ROLE: HUMAN_ENVIRONMENTAL_AND_WATER_SUPPORT_DERIVATION_DESIGN
STATUS: DESIGN_READY
SEAL_ACTION: false
CANONICAL_MUTATION: false
NEW_HISTORICAL_SIMULATION: false
EXTERNAL_ENGINE_REQUIRED: false
```

This design translates the exact, hash-validated R3.18/R3.19/R3.20 payloads into transparent human-facing environmental support components. It does **not** define physical human carrying capacity `K(x,t)`, does not target a population, and does not materialize settlements or civilizations.

## Bound inputs

### R3.18 — environmental exposure integrals

Canonical payload:

`R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz`

SHA256:

`54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70`

R3.18 SEALED authority explicitly defines this payload as an **integral bundle**. The four supported windows are:

| group | duration |
|---|---:|
| `full_125_to_0` | 125000 y |
| `recent_120_to_0` | 120000 y |
| `transport_phase1_125_to_62p5` | 62500 y |
| `transport_phase2_62p5_to_0` | 62500 y |

For each window, the payload contains:

- `aridity_index`
- `browse_forage`
- `land_support`
- `low_forage`
- `reference_population`
- `temperature_c`
- `wetland_forage`

The apparently very large temperature/aridity/support values are therefore not instantaneous environmental snapshots. They must retain integral/exposure semantics.

### R3.19 — exact present support geometry / biology boundary

Canonical payload:

`WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.npz`

SHA256:

`f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406`

Relevant arrays:

- `lat[90]`
- `lon[180]`
- `current_accessible[90,180]`
- `population[295,90,180]`
- component-level biological metadata

`current_accessible` is an exact 0-ka boundary. It must not be silently projected backward over the entire R3.18 time span.

### R3.20 — high-resolution hydrological hazard evidence

Canonical payload:

`R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz`

SHA256:

`4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14`

Supported interval: 15–11 ka, 50-year cadence, 80 states.

The hazard arrays remain diagnostic/ranking quantities, not flood depths, guaranteed inundation or a direct freshwater-supply model.

## B2 inspection evidence

```yaml
ALL_SHA256_MATCH: true
R3_18_ARRAY_COUNT: 31
R3_19_ARRAY_COUNT: 12
R3_20_ARRAY_COUNT: 10
NONFINITE_VALUES_FOUND: false
FILENAME_MISMATCH_FOUND: false
```

## Spatial semantics

Native working grid:

```yaml
LAT_CELLS: 90
LON_CELLS: 180
GRID_SHAPE: [90, 180]
LAT_CENTERS: -89..89 degrees
LON_CENTERS: -179..179 degrees
```

All B3 2-D layers should remain on this grid unless an explicit later resampling contract is created.

## Temporal semantics

B3 must preserve three distinct temporal forms:

1. **R3.18 interval exposure/integral fields** over fixed long windows.
2. **R3.19 exact 0-ka endpoint fields**.
3. **R3.20 50-year hazard states** only inside the supported 15–11 ka interval.

No interpolation across these different semantics is implicit.

### Duration-normalized exposure

For an R3.18 field `I_f,w(x)` that is explicitly stored as a time integral over window `w`, B3 may derive:

```text
E_f,w(x) = I_f,w(x) / Δt_w
```

where `Δt_w` is the SEALED window duration in years.

`E_f,w` must initially be named and documented as **duration-normalized exposure**. It may only be promoted to a physical temporal mean when the underlying field/unit convention supports that interpretation.

This rule prevents, for example, an integrated `temperature_c` value from being interpreted directly as degrees Celsius.

## Independent B3 axes

### 1. LAND_SUPPORT_EXPOSURE

Source:

`R3.18 land_support`

Derived quantity:

```text
LAND_SUPPORT_EXPOSURE_w(x) = land_support_integral_w(x) / Δt_w
```

Interpretation: fraction-like/time-normalized support exposure where justified by the R3.18 source semantics. It is **not** human carrying capacity.

At 0 ka, `R3.19 current_accessible` remains the exact endpoint accessibility mask.

### 2. CLIMATE_EXPOSURE

Sources:

- duration-normalized `temperature_c`
- duration-normalized `aridity_index`

Keep as two independent continuous fields:

```text
TEMPERATURE_EXPOSURE_w(x)
ARIDITY_EXPOSURE_w(x)
```

B3 must not yet impose human optimum temperatures, aridity thresholds or a combined climate-suitability curve unless separately calibrated and repository-documented.

### 3. FORAGE_SUPPORT_VECTOR

Sources:

- duration-normalized `low_forage`
- duration-normalized `browse_forage`
- duration-normalized `wetland_forage`

Output remains a vector:

```yaml
FORAGE_SUPPORT_VECTOR:
  LOW_FORAGE_EXPOSURE
  BROWSE_FORAGE_EXPOSURE
  WETLAND_FORAGE_EXPOSURE
```

The three channels must not be blindly summed. No direct conversion to human-edible calories, persons/cell or `K` is authorized in B3.

### 4. BIOLOGICAL_SUPPORT_DIAGNOSTICS

R3.19 biological population may be used to validate spatial biological presence/absence and endpoint support relationships.

R3.18 `reference_population[6,90,180]` is **not** physical human population and **not** `K`. Until the six channel semantics are bound explicitly, it remains diagnostic-only and must not enter a human-support equation.

### 5. HYDROLOGICAL_HAZARD_VECTOR

For each R3.20 state `t` inside 15–11 ka, preserve independently:

```yaml
HYDROLOGICAL_HAZARD_VECTOR:
  PLUVIAL_FLOOD_POTENTIAL
  COASTAL_INUNDATION_POTENTIAL
  COMPOUND_FLOOD_HAZARD
  DRYING_HAZARD
  ECOSYSTEM_HYDROLOGICAL_SHOCK
  MELTWATER_SYSTEM_PRESSURE
  RAW_SUPPORT_LOSS
```

`severe_flood_candidate_fraction[t]` remains a state-level diagnostic summary.

No component is converted automatically into water availability, mortality, settlement loss, or a generic hazard penalty.

### 6. FRESHWATER_SUPPORT

Status in B3:

```yaml
STATUS: MISSING_NEEDS_NEW_DERIVATION
```

Existing R3.20 evidence measures hazard/disruption, not persistent freshwater availability. Therefore B3 must not fabricate `FRESHWATER_SUPPORT` from low flood hazard or low drying hazard.

Minimum next source/compute requirement:

- bind repository-proven hydrological/geographic variables capable of representing persistent freshwater access or availability;
- derive a transparent water-access field on the native grid;
- separately derive reliability/variability if supported;
- preserve flood/drying hazard as independent axes.

### 7. HYDROLOGICAL_RELIABILITY

Status in B3:

```yaml
STATUS: PARTIAL_NEEDS_NEW_DERIVATION
```

R3.20 can inform disruption during 15–11 ka but cannot define long-term reliability outside that window. Any reliability product must expose its temporal coverage and must not extrapolate the 15–11 ka event diagnostics to 125–0 ka or Year 0.

### 8. ENVIRONMENTAL_STABILITY

Status in B3:

```yaml
STATUS: DERIVABLE_AS_DIAGNOSTICS_NOT_YET_SINGLE_SCORE
```

Allowed transparent diagnostics include differences between independently duration-normalized R3.18 phase exposures, e.g.:

```text
ΔE_f(x) = E_f,phase2(x) - E_f,phase1(x)
```

and within-window R3.20 temporal variability for hazard components during 15–11 ka.

A single `ENVIRONMENTAL_STABILITY` score is deferred until component scales and interpretation are calibrated.

## Explicitly unavailable in B3

The following must remain absent rather than inferred:

```text
absolute human freshwater supply
persistent river discharge
navigable-water opportunity
human-edible calorie productivity
marine food productivity
persons-per-cell carrying capacity
settlement density
city/state/civilization probability
trade or polity networks
```

## Proposed machine-readable B3 output

A later implementation runner should create an NPZ plus manifest containing at minimum:

```text
lat
lon
window_duration_years
land_support_exposure
aridity_exposure
temperature_exposure
low_forage_exposure
browse_forage_exposure
wetland_forage_exposure
phase_delta_* diagnostics
current_accessible_0ka
R3.20 hazard arrays preserved by component
R3.20 years_before_book
coverage/availability masks and metadata
```

No scalar `K` field is produced by B3.

## Validation gates before B3 numeric implementation

```yaml
R3_18_INTEGRAL_SEMANTICS_PRESERVED: required
WINDOW_DURATIONS_EXPLICIT: required
R3_19_0KA_MASK_NOT_BACKPROJECTED: required
R3_20_TIME_WINDOW_NOT_EXTRAPOLATED: required
REFERENCE_POPULATION_NOT_USED_AS_HUMAN_K: required
HAZARD_NOT_RELABELED_AS_FRESHWATER_SUPPORT: required
FORAGE_CHANNELS_NOT_BLINDLY_SUMMED: required
POPULATION_TARGET_IMPOSED: false
CIVILIZATION_TARGET_IMPOSED: false
EXTERNAL_ENGINE_REQUIRED: false
```

## Smallest next computation

The smallest defensible B3 computation is:

1. load the already hash-validated R3.18/R3.19/R3.20 payloads;
2. derive duration-normalized R3.18 exposure fields for the four authorized windows;
3. derive transparent phase-difference diagnostics;
4. retain the exact R3.19 0-ka accessibility mask as an endpoint boundary;
5. preserve R3.20 hydrological hazards unchanged by component and temporal coverage;
6. write a repository-importable numeric manifest/output;
7. leave `FRESHWATER_SUPPORT` and long-term `HYDROLOGICAL_RELIABILITY` explicitly unresolved until a source-supported water-access derivation is bound.

That computation uses native ARCANA evidence only and requires no external runtime.
