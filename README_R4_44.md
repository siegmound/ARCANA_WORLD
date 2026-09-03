# ARCANA WorldSim v0.6D1-R4.44
## Geonomics Readout Extraction Dry Run & Adjudication Input Validation

Parent:
- R4.43 integrated 48/48 PASS
- R4.43 final seal 29/29 SEALED

R4.44 is the first live extraction of the five readout definitions frozen in
R4.43. It is still a **non-scientific dry run**.

## Scope

All four frozen seeds are used, but only two consecutive canonical states are
needed because R4.42 already validated full-sequence queue mechanics.

### J14
- first frozen branch
- states 0 and 1
- 4 seeds
- 3 metric IDs per state
- 24 metric records

### J18
- first frozen branch
- states 0 and 1
- 4 seeds
- 3 metric IDs per state
- 24 metric records

### J21
- 20 ka and 15 ka
- 4 seeds
- 147 native layers
- 2 metric IDs per layer/state
- 2352 metric records

Total:
- 2400 metric records
- 1208 exact-integrity records
- 1192 scientific-descriptive records

## Carrier extraction

R4.44 reads:

1. `Model.get_coords(spp=0)`
2. `Species._cells`
3. nearest-neighbor distances from
   `Species._kd_tree.tree.query(coords, k=2)`

Coordinates must exactly equal canonical x/y.

Cells must exactly equal:

`floor(canonical x/y)`

Nearest-neighbor distances preserve the raw vector and descriptive summary.
There is no numeric acceptance threshold.

## Layer extraction

For every one of the 147 J21 native layers, R4.44 records:

1. exact raster digest/readback
2. finite/min/max/mean/std descriptive summary

The four R4.39 sidecars remain excluded.

## Adjudication-input validation

Every emitted metric record must:

- use a metric ID already authorized by R4.43 for that job;
- contain all frozen common schema fields;
- classify integrity mismatches as runtime/adapter failures;
- record descriptive metrics without thresholds;
- never use majority vote;
- never allow engine output to define ARCANA's target;
- never rewrite canonical state.

R4.44 therefore tests the whole readout transport path without making any
scientific acceptance claim.

Expected end state if SEALED:

- production queue authorized = true
- scientific readout authority closed = true
- metric extraction dry run validated = true
- adjudication input validation closed = true
- scientific execution authorized = false
- Geonomics execution ready = false
- scientific execution performed = false

Run:

```powershell
.\run_v0_6D1_R4_44.ps1
```

Next if SEALED:

`BUILD_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_GOVERNED_REVALIDATION_RUN_PREFLIGHT`
