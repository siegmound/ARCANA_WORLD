# ARCANA WorldSim v0.6D1-R4.45
## Geonomics Scientific Execution Authorization & First Governed Revalidation Run Preflight

Parent:
- R4.44 integrated 38/38 PASS
- R4.44 final seal 23/23 SEALED

R4.45 is the final pre-scientific gate. It does not run the engine scientifically.
Instead it freezes, hashes, and authorizes the exact first scientific cohort
before any scientific result exists.

## Frozen first cohort

### J14
- deterministic `member0/candidate0`
- all 141 canonical states
- 140 transitions
- all four frozen seeds
- 3 authorized metric IDs
- **not** a full-J14 revalidation claim

### J18
- deterministic `member0/candidate0`
- all 15 snapshot states
- 14 transitions
- all four frozen seeds
- 3 authorized metric IDs
- **not** a full-J18 revalidation claim

### J21
- full frozen 20 ka -> 0 ka sequence
- all 9 canonical states
- all 147 native layers
- 4 dynamic sidecars excluded
- all four frozen seeds
- 2 authorized metric IDs

## Frozen seed vectors

J14:
- 310746493
- 1894477382
- 1291996560
- 1554786554

J18:
- 999124684
- 1705133798
- 1085091276
- 555097754

J21:
- 1617603515
- 1207292893
- 1138693833
- 989125497

## Expected scientific evidence transport

The first cohort is expected to emit:

- 12,456 metric records
- 6,540 exact-integrity records
- 5,916 scientific-descriptive records
- 12 replicate streams

There are still **zero numeric acceptance thresholds**.

Descriptive metrics can be recorded, but cannot automatically PASS or FAIL
ARCANA.

## Authorization semantics

If SEALED, R4.45 sets:

- `scientific_execution_authorized = true`
- `geonomics_execution_ready = true`
- `first_governed_revalidation_run_authorized = true`

while still keeping:

- `first_governed_revalidation_run_executed = false`
- `scientific_engine_execution_performed = false`
- `canonical_state_changed = false`

The run plan receives a SHA256 digest. R4.46 must consume the exact sealed plan;
it may not silently change selectors, seeds, metrics, thresholds, or claim scope.

## Claim limits

R4.46 may say that Geonomics-native descriptive readouts were recorded under
the frozen ARCANA replay authority.

It may **not** say:

- Geonomics independently predicted ARCANA historical locations;
- J14/J18 first cohort is a full-job revalidation;
- a descriptive value passed or failed a retroactive threshold;
- an external-engine result defines the ARCANA target;
- scientific results rewrote canonical state.

Run:

```powershell
.\run_v0_6D1_R4_45.ps1
```

Next if SEALED:

`BUILD_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_AND_EVIDENCE_CAPTURE`
