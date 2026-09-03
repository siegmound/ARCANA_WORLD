# ARCANA WorldSim v0.6D1-R4.51
## Multi-Engine 23-Job Reconciliation & Revalidation Gap Census

Parent:
- R4.50 integrated 50/50 PASS
- R4.50 final seal 25/25 SEALED
- Geonomics 1.4.9 fully revalidated:
  - J14 192/192
  - J18 64/64
  - J21 1/1

R4.51 returns to the immutable R4.2 23-job registry.

It performs **no engine execution**.

## Exact frozen R4.2 registry

The registry contains 23 jobs:

- Madingley: 4
- RangeShifter: 5
- CDMetaPOP: 5
- NEMO: 3
- Geonomics: 3
- SLiM: 3

R4.51 checks exact job order, IDs, engines, windows, and the frozen
`canonical_write=false`, `result_selected=false`,
`FROZEN_NOT_EXECUTED_IN_R42` semantics.

## Conservative evidence reconciliation

R4.51 scans locally preserved R4 JSON evidence and extracts job-scoped records.

Evidence is kept separate as:

1. `SCIENTIFIC_VALID`
   - scientific execution explicitly performed;
   - scientific evidence explicitly valid;
   - PASS/evidence-captured semantics;
   - no local blocked signal.

2. `SCIENTIFIC_FAILED_OR_INVALID`

3. `PROCESS_EXECUTION_SUCCESS_ONLY`
   - for example a return code of zero without scientific-evidence validity.

4. `PREFLIGHT_OR_GOVERNANCE`
   - mapping, target, selector, runtime, adapter, schema, construction, dry-run,
     or authority records without valid scientific execution.

5. `BLOCKED_OR_INVALID`

6. `UNCLASSIFIED_REFERENCE`

## No automatic promotion

Only the three explicit R4.50 Geonomics closures are automatically classified:

`FULLY_REVALIDATED_CLOSED_R450`

All 20 non-Geonomics jobs remain full-job closure gaps in R4.51.

If a non-Geonomics job already has strong scientific evidence, R4.51 marks:

`SCIENTIFIC_EVIDENCE_PRESENT_CLOSURE_NOT_PROVEN`

and:

`PENDING_R452_EVIDENCE_ADJUDICATION_BEFORE_RERUN`

This prevents an unnecessary rerun while also preventing evidence from being
promoted merely because a process returned successfully.

If no promotable scientific evidence is found, the job is marked:

`SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED`

## Important consequence

A SEALED R4.51 does **not** mean the 23-job multi-engine revalidation is closed.

Expected present state:

- 3 jobs fully closed (Geonomics)
- 20 full-job closure gaps
- exact promotion-candidate count determined from local historical evidence
- exact execution-required count determined from local historical evidence

R4.52 will adjudicate every promotion candidate and then freeze the precise
execution plan for the jobs that genuinely need new scientific runs.

## Run

```powershell
.\run_v0_6D1_R4_51.ps1
```

Next if SEALED:

`BUILD_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_AND_EXECUTION_PLAN`
