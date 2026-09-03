# ARCANA WorldSim v0.6D1-R4.48
## Geonomics J14/J18 Full-Job Revalidation Coverage Expansion Preflight

Parent:
- R4.47 integrated 34/34 PASS
- R4.47 final seal 23/23 SEALED

Current scientific coverage:
- J14: 1/192
- J18: 1/64
- J21: 1/1 CLOSED

R4.48 performs no scientific engine execution. It freezes every remaining
J14/J18 branch before R4.49.

## Remaining coverage

J14:
- 192 total frozen branches
- M000_C00 already scientifically executed and closed
- 191 remaining
- 764 new streams (191 x 4 seeds)

J18:
- 64 total frozen branches
- M000_C00 already scientifically executed and closed
- 63 remaining
- 252 new streams (63 x 4 seeds)

Combined:
- 254 remaining branches
- 1,016 new streams

## Representability gate

Every canonical state of every frozen branch is inspected before authorization.

R4.48 requires:
- at least one active carrier at every canonical state;
- all x/y coordinates finite;
- 0 <= x < 180;
- 0 <= y < 90;
- unique branch identities.

No branch may be silently dropped based on its scientific values.

## Deterministic sharding

R4.48 freezes contiguous branch shards in canonical order:

`member index major -> candidate index minor`

Maximum 8 branches per shard.

Expected:
- J14: 24 shards
- J18: 8 shards
- total: 32 shards

Each branch always carries all four frozen seeds.

Shard membership is scientific plan authority. Execution concurrency is only an
operational property and does not alter scientific evidence identity. This
allows R4.49 to resume at whole-shard granularity without changing the plan.

## New evidence expected in R4.49

J14 remaining:
- 323,172 metric records
- 215,448 integrity
- 107,724 descriptive

J18 remaining:
- 11,340 metric records
- 7,560 integrity
- 3,780 descriptive

Combined expansion:
- 334,512 metric records
- 223,008 integrity
- 111,504 descriptive

After combining the new expansion evidence with the already SEALED first cohort
and J21 evidence, full Geonomics coverage would contain:

- 346,968 metric records
- 229,548 integrity records
- 117,420 descriptive records

## No reruns of closed evidence

R4.48 explicitly forbids R4.49 from rerunning:
- J14 M000_C00;
- J18 M000_C00;
- J21.

The full-coverage result must be assembled from existing SEALED evidence plus
the 254 predeclared missing branches.

## Governance remains frozen

- zero numeric acceptance thresholds
- no majority vote
- no result-selected branch
- no result-selected metric
- no external-engine target definition
- no canonical rewrite
- Deep OFF

Run:

```powershell
.\run_v0_6D1_R4_48.ps1
```

Next if SEALED:

`BUILD_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE`
