# INT3-ENG10K-F2 — Decision Preparation

Date: 2026-10-24
Source branch / HEAD: `r6/si1-bandwidth-f2av` / `1bf06ef0e624723c3722a351496ae3b7c2544f40`
F1 report: `docs/arcana/INT3_ENG10K_F1_FAIR_RESOURCE_PREFLIGHT_CLOSURE.md`

## Decision boundary

Decision: `INT3F_ENGINEERING_AUTHORIZATION_PROPOSAL_READY__EXECUTION_NOT_AUTHORIZED`.

Recommendation: **GO-PROPOSAL for option B only**, for a separate, explicit,
single-attempt, noncanonical engineering authorization that accepts residual risk
from sampled resource monitoring. This report does not grant that authorization.
Current gate remains `INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

The prior decision `INT3F_ENGINEERING_AUTHORIZATION_BLOCKED__REQUIREMENTS_UNRESOLVED`
is preserved as the result of its earlier evidence set. F1 adds a reported
read-only provider/runtime/resource snapshot; it does not rewrite that history or
qualify the ENG10K run.

## Decision matrix

| Requirement | Status | Evidence | Risk / condition for any future proposal |
|---|---|---|---|
| Provider, R4, runtime identity | GO for exact F1 source only | Fair operator reports preflight exit 0, R4/provider match, Python 3.12.10 / NumPy 2.3.5 and source composite `ab19e887113a045ebfa2db3ba30c724d6685e828e6e8eb20b76476ae3f9fa9ef` at HEAD `1bf06ef…` | Recompute all HEAD-bound identities on the exact authorized commit; imported evidence is still absent on Windows |
| Candidate code continuity | GO, bounded | `cb9bd837…` to `1bf06ef…` has no diff in supervisor, runner, or engineering-case configuration | Exact execution source must be rechecked at authorization time |
| Current host capacity | OBSERVED, not reserved | Reported MemAvailable ~1.03e9 kB; `/home` free ~16.55e12 bytes | Single-session values do not establish future allocation or personal quota |
| 2 GiB OS enforcement | UNKNOWN / unresolved | Visible cgroup `memory.max` and `memory.high` report `max`; scheduler allocation/enforcement absent from session evidence | Option A (verified scheduler/cgroup isolation) is not established and must not be presumed available or authorized |
| Sampled 2 GiB process-tree RSS stop | CONDITIONAL GO-PROPOSAL | INT3-E synthetic Linux supervisor suite reported 43/43 PASS; F1 resources audit was read-only | Accept as sampled monitoring only, with polling/termination overshoot and no hard memory protection |
| 512 MiB output stop | CONDITIONAL GO-PROPOSAL | Static projected output 66,715,648 bytes (63.625 MiB) in prior F review | Projection is not a quota; verify fresh attempt-root capacity and monitor candidate plus logs |
| 900 s wall threshold | CONDITIONAL GO-PROPOSAL | Supervisor implements stop threshold; no ENG10K timing evidence | It is not an estimate or completion guarantee; timeout means preserve partial evidence and stop |
| Per-user storage quota / exact workload RSS | UNKNOWN | Quota unavailable; no workload was run | A proposal must state these remain unknown and preserve fail-closed behavior on output/resource monitor errors |
| Direct/restart numerical acceptance | NO-GO for binary acceptance | No governed comparison tolerance | Keep comparisons descriptive; `THRESHOLD_UNJUSTIFIED` |
| Scientific/canonical promotion | NO-GO | Existing gates deny it | No geology, mechanics, Solver, or WORLD_HISTORY promotion |

## Options

**A — verified enforced isolation.** Prefer this only if the authorized Fair
operator can demonstrate, before execution, an applicable scheduler or cgroup
limit on the actual child process tree, with the requested limits and observable
failure behavior. F1 does not show such a facility: the visible cgroup limits were
`max`, and no scheduler allocation was evidenced. Do not configure systemd,
cgroups, or scheduler policy as part of this preparation.

**B — explicit residual-risk acceptance.** This is the only presently supportable
proposal route: one future noncanonical attempt under the already tested sampled
supervisor, with a separate authorization that explicitly accepts no hard 2 GiB
or 512 MiB OS quota and no runtime guarantee. The operator may stop/terminate on
observed thresholds; sampling and termination have latency, and a system-wide
resource failure may occur before a sample. This is a proposal, not a GO to run.

## Conditions for a separate authorization decision

Before asking for or acting on authorization, bind the request to the exact
candidate commit and recompute the provider/source-composite identities. Require
a fresh no-evolution check of Python/NumPy, R4 manifest/checkpoint, provider
hashes, the exact configuration, and new absent candidate/supervision directories
under the authorized evidence root. Recheck available memory, disk and any
observable quota/enforcement facts; record unknowns rather than infer them.

If option B is proposed, the authorization itself must explicitly acknowledge:

- 900 seconds is a monitored stop threshold, not predicted runtime.
- 2 GiB process-tree RSS and 512 MiB cumulative-output limits are sampled
  supervisor thresholds, not OS-enforced quotas.
- Actual ENG10K peak RSS, actual thermal substep count, wall time and personal
  filesystem quota remain UNKNOWN until an attempt; host MemAvailable is not a
  reservation.
- One attempt only, no automatic retry, immutable fresh evidence path, capture of
  stdout/stderr and stop reason, preservation of partial output, and no canonical
  writes.
- Numerical direct/restart and resolution comparisons are reported descriptively;
  no acceptance tolerance is justified (`THRESHOLD_UNJUSTIFIED`).

After a complete attempt, verify sealed manifest membership and hashes, output
continuity, finiteness/invariants, full endpoint fields, direct/restart and
resolution comparisons, replay/restart records, resource observations and
canonical non-mutation. A missing or incomplete seal, stop, monitor error, identity
mismatch or nonzero exit is a preserved failed/incomplete attempt; no retry is
implied.

## Next decision and gates

Next action: a human/operator may decide whether to issue a distinct, exact-commit
authorization using option B's explicit risk acceptance, or require option A and
leave execution blocked. No automatic transition occurs. No execution command is
authorized by F1/F2 documentation.

Preserve `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`,
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`.
