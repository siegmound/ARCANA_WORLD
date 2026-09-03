# ARCANA WorldSim v0.6D1-R4.47
## Geonomics First Governed Revalidation Evidence Review & Cohort Adjudication Closure

Parent authority:
- R4.46 integrated 39/39 PASS
- R4.46 final seal 22/22 SEALED
- R4.46-R1 reseal verification 16/16 PASS

R4.47 performs **no new Geonomics execution**. It reviews the already-captured
scientific evidence and closes the first-cohort adjudication.

## What can be adjudicated

### Exact-integrity evidence

Coordinate, cell, and native-raster replay records have an objective frozen
criterion:

`exact_match == true`

Therefore integrity may be adjudicated:

`PASS_EXACT_INTEGRITY`

Any mismatch remains a fail-closed adapter/runtime integrity failure.

### Scientific-descriptive evidence

Nearest-neighbor and native-layer descriptive records have **no frozen numeric
acceptance threshold**.

R4.47 therefore does not manufacture one after seeing the results. Valid
finite descriptive evidence is classified:

`REVIEWED_VALID_DESCRIPTIVE_EVIDENCE_NO_THRESHOLD`

This is an evidence-quality/governance adjudication, not a numeric
corroboration claim.

Expected overall cohort verdict:

`VALID_GOVERNED_COHORT_EVIDENCE_WITH_EXACT_INTEGRITY_AND_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM`

## Coverage closure

### J14

The first scientific cohort executed only:

`member0 / candidate0`

of 192 frozen branches.

Coverage:

`1 / 192 = 0.520833...%`

Therefore:
- first-cohort evidence closure: allowed
- full-job revalidation claim: forbidden

### J18

Coverage:

`1 / 64 = 1.5625%`

Therefore:
- first-cohort evidence closure: allowed
- full-job revalidation claim: forbidden

### J21

The predeclared layer job has one full canonical sequence and it was executed
for all four frozen seeds.

Coverage:

`1 / 1 = 100%`

Therefore full coverage of the predeclared J21 layer job may close.

## Frozen evidence totals

- 12 replicate streams
- 12,456 metric records
- 6,540 exact-integrity records
- 5,916 scientific-descriptive records

R4.47 does not change those files. It records their SHA256 identities in the
review outputs.

## Still forbidden

- retroactive numeric thresholds
- automatic scientific PASS/FAIL from descriptive values
- majority vote
- result-selected metric or branch
- engine-defined ARCANA target
- canonical rewrite
- calling J14/J18 full-job revalidated

Run:

```powershell
.\run_v0_6D1_R4_47.ps1
```

Next if SEALED:

`BUILD_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_EXPANSION_PREFLIGHT`
