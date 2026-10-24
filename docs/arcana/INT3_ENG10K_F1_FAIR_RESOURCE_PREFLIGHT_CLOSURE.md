# INT3-ENG10K-F1 — Fair Read-Only Resource Preflight Closure

Date: 2026-10-24
Repository: `siegmound/ARCANA_WORLD`
Branch / source HEAD: `r6/si1-bandwidth-f2av` / `1bf06ef0e624723c3722a351496ae3b7c2544f40`

## Decision and scope

`INT3F1_FAIR_READ_ONLY_RECON_COMPLETE`

This closes the requested **read-only** identity/provider and current-session resource
reconnaissance. It is not an ENG10K execution, kernel benchmark, resource guarantee,
or execution authorization. The original INT3-F decision
`INT3F_ENGINEERING_AUTHORIZATION_BLOCKED__REQUIREMENTS_UNRESOLVED` remains a valid
historical decision for the evidence available to that review; this new evidence
supports a separate F2 decision proposal, not an implicit authorization.

No ENG10K evolution, supervisor production invocation, benchmark, Fair job, or
canonical operation was performed in this closure.

## FAIR-reported evidence and authority

The operator reports that the read-only commands on Fair returned
`PREFLIGHT_EXIT_CODE=0`, `RESOURCE_AUDIT_EXIT_CODE=0`, and
`INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`. Reported source-composite
SHA256: `ab19e887113a045ebfa2db3ba30c724d6685e828e6e8eb20b76476ae3f9fa9ef`.
The report states that R4 and governed provider identities match, with Python
3.12.10 / NumPy 2.3.5.

Fair evidence locator:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT3F1_RESOURCE_PREFLIGHT/1bf06ef0_20261024_01`

Operator-reported member identities:

| File | Reported SHA256 | Windows status |
|---|---|---|
| `preflight.log` | `db5c15a0555c00753711007342362cc91d3eb7e48c9f46895573a51f9d67c0e8` | Original not imported or rehashed |
| `resources.log` | `cd960de86593eb38241981d67f07b26df71dfc37e2d12754132486c375c3eaf5` | Original not imported or rehashed |
| Four other control files | Individual hashes not supplied here | Fair procedure reports checksum OK; files not imported or rehashed |

Accordingly, the Fair commands, outputs, and checksums are **operator-reported**.
Windows has not independently authenticated the original Fair files. The
source-composite is reported for exactly HEAD `1bf06ef…`; it must be recomputed
for any later execution candidate because its identity is HEAD-bound.

The scoped Git comparison from the FAIR-tested INT3-E code commit
`cb9bd8373eeb028b83c8bc1abb376624e3553adb` to `1bf06ef0e624723c3722a351496ae3b7c2544f40`
shows no changes to the ENG10K supervisor, runner, or engineering-case
configuration. The later commits in that interval are documentation/ledger
changes; this does not make the new HEAD a FAIR-tested commit.

## Current-session resource observations

At `2026-10-24T21:26:09Z`, Fair reportedly observed:

| Observation | Value | Interpretation limit |
|---|---:|---|
| Host | `fair` | Session host only |
| `MemTotal` | 1,056,486,536 kB | Host-visible capacity; not a job allocation |
| `MemAvailable` | 1,030,996,348 kB | One-time current-session observation; not a future-run reservation |
| `/home` available | 16,550,992,183,296 bytes | Filesystem free-space observation; personal quota remains unknown |
| Free inodes | 361,730,941 | Current observation only |
| Cgroup v2 | `/user.slice/user-1006.slice/session-56997.scope` | Current session path |
| Visible `memory.max` / `memory.high` | `max` in session and inspected ancestors | No effective 2 GiB OS-enforced limit demonstrated |
| Scheduler variables | Slurm/PBS/LSF/SGE variables unset | Does not prove no scheduler or no allocation |
| Personal quota | UNKNOWN; `quota` unavailable | No quota authority established |

These data distinguish host capacity from enforcement: abundant host-visible
memory and filesystem space do not prove resources are reserved for ENG10K. No
future process RSS, cgroup ceiling, scheduler allocation, filesystem quota, or
hard output cap was demonstrated. The supervisor's 2 GiB RSS and 512 MiB output
thresholds remain sampled monitoring thresholds; 900 seconds remains a stop
threshold, not a runtime estimate.

## INT3-F1 closure matrix

| Requirement | Result | Evidence class | Remaining limit |
|---|---|---|---|
| Exact source/provider/runtime preflight | PASS as reported | `OPERATOR_REPORTED` | Original files not imported/rehashed on Windows |
| R4 and provider identity match | PASS as reported | `OPERATOR_REPORTED` | Applies to this exact Fair preflight and HEAD only |
| Host memory/filesystem snapshot | Observed as reported | `OPERATOR_REPORTED` | No reservation, quota, or future job equivalence |
| Effective 2 GiB OS limit | NOT ATTESTED | Reported cgroup values are `max` | Scheduler/job-level enforcement not demonstrated |
| Future workload RSS / duration | UNKNOWN | No workload execution or benchmark | Must not infer from machine totals or synthetic tests |
| Personal filesystem quota | UNKNOWN | `quota` unavailable | Actual attempt-root capacity not guaranteed |
| Numerical acceptance | UNCHANGED | Existing code invariants only | `THRESHOLD_UNJUSTIFIED` remains |

## Preserved gates

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`;
`THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`;
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`;
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`.
