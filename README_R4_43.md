# ARCANA WorldSim v0.6D1-R4.43
## Geonomics Scientific Readout Authority, Metric Extraction & Adjudication Schema Preflight

Parent:
- R4.42 integrated 26/26 PASS
- R4.42 final seal 21/21 SEALED
- R4.42-R1 reseal verification 16/16 PASS
- production queue: `ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE`

R4.43 freezes what Geonomics is allowed to report as scientific evidence
**before** any scientific execution.

## J14 / J18 authorized readouts

### Integrity only
1. exact continuous carrier coordinates `(x,y)`
2. exact native cell assignment from floor(coords)

A mismatch is an adapter/runtime integrity failure, never "scientific
divergence".

### Scientific descriptive
3. nearest-neighbor distance from the native Geonomics `_KDTree`

The raw nearest-neighbor vector is preserved. Summaries may include:

- count
- finite_count
- min
- median
- mean
- max

There is **no acceptance threshold**. For one-carrier states, the metric is
`NOT_APPLICABLE_SINGLE_CARRIER_NO_FAILURE`.

This readout describes connectivity of ARCANA canonical deme supports. It does
not turn carriers into biological individuals and does not claim Geonomics
predicted historical locations.

## J21 authorized readouts

### Integrity only
1. exact `Layer.rast` readback for the 147 native dynamic layers

### Scientific descriptive
2. per-layer:
- finite_count
- min
- max
- mean
- std

The four dynamic sidecars remain excluded.

## Explicitly forbidden scientific interpretations

- `Species.N` or `_calc_density()` as biological population density
- `Species.Nt` as historical population size
- births/deaths as historical demography
- age-stage as physical time
- K as adjudicative carrying capacity
- fitness/genetic/heterozygosity metrics on nongenomic carriers
- movement/dispersal history
- the four sidecars as Geonomics-native layer metrics

## Adjudication schema

R4.43 freezes three allowed roles:

- `EXACT_INTEGRITY_ONLY`
- `SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY`
- `SCIENTIFIC_DESCRIPTIVE_LAYER_STATE`

and one forbidden class:

- `FORBIDDEN_NONLITERAL_BIOLOGY`

No descriptive value can automatically PASS/FAIL ARCANA.

Frozen global rules:

- numeric acceptance thresholds: 0
- majority vote: forbidden
- result-selected threshold: forbidden
- result-selected metric: forbidden
- external engine output defining ARCANA target: forbidden
- canonical rewrite: forbidden

R4.43 does not yet extract live readouts.

Expected end state:

- production execution queue authorized: true
- scientific readout authority closed: true
- metric extraction dry run validated: false
- scientific execution authorized: false
- Geonomics execution ready: false

Run:

```powershell
.\run_v0_6D1_R4_43.ps1
```

Next if SEALED:

`BUILD_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_VALIDATION`
