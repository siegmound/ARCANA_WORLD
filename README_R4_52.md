# ARCANA WorldSim v0.6D1-R4.52
## Non-Geonomics Job-Specific Evidence Adjudication & Execution Plan

R4.51 established an exact result:

- frozen R4.2 jobs: 23
- Geonomics fully closed: 3
- non-Geonomics closure gaps: 20
- prior scientific promotion candidates: **0**
- jobs requiring new scientific execution: **20**

Therefore R4.52 has no historical evidence to promote.

It freezes the exact scientific execution plan for those 20 jobs.

## Engine distribution

- Madingley: 4 jobs
- RangeShifter: 5 jobs
- CDMetaPOP: 5 jobs
- NEMO: 3 jobs
- SLiM: 3 jobs

Total: 20 jobs.

## Frozen seed authority

The existing R4.3/R4.35 governance established four frozen seeds per R4.2 job.

R4.52 recovers those values from locally preserved JSON authority. It requires:

- exactly four seeds for every non-Geonomics job;
- 80 seeds total;
- all 80 seeds unique;
- at least one concrete local authority source per job.

No seed may be invented or regenerated.

The 20 Geonomics-independent job records are also bound to SHA256 hashes of
their exact immutable R4.2 job records.

## Planned scientific streams

20 jobs × 4 frozen seeds = 80 planned scientific streams.

R4.52 groups them into five deterministic engine batches:

1. Madingley
2. RangeShifter
3. CDMetaPOP
4. NEMO
5. SLiM

Batch membership is frozen. Operational execution order and parallelism do not
constitute scientific authority.

## Why R4.52 does not execute them yet

Unlike Geonomics, the five remaining engines do not yet have an R4.43-style
scientific readout authority frozen for these exact jobs.

Therefore every job is explicitly marked:

`ENGINE_SPECIFIC_SCIENTIFIC_INTERFACE_REQUIRED_R453`

and:

`ENGINE_SPECIFIC_READOUT_AUTHORITY_REQUIRED_R453`

R4.52 keeps:

- `scientific_execution_authorized = false`
- `scientific_engine_execution_performed = false`

R4.53 will close execution/readout interfaces for all five engines before any
of the 80 new streams are launched.

## Run

```powershell
.\run_v0_6D1_R4_52.ps1
```

Next if SEALED:

`BUILD_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_AND_READOUT_AUTHORITY_PREFLIGHT`
