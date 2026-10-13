# INT-0B-R1 second authorized attempt — pre-output failure

Date: 2026-10-13
Branch: r6/si1-bandwidth-f2av
Source HEAD: 4cc7a78d95ee7e529394173933817a7266db251d
Parent: e95c7dbf281ede5312512654262b9925fa87eb02

## Decision

INT0B_R1_SECOND_ATTEMPT_FAILED_PRE_OUTPUT_VALIDATION_GIT_OBJECT_ENV_REINSERTED

The single second-attempt authorization was used once. The runner exited before creating the candidate output directory or performing the numerical trajectory. No retry was performed; this authorization does not permit a third execution. INT-1 remains blocked because no validated trajectory exists.

## Final preflight

- Branch/HEAD/parent matched the authorized identity; tracked worktree and index were clean.
- Runner SHA256: 2b5ab1af081fae9ad2a0681a4ba9b95dfca032839caba52cdc440525cf77fc1c.
- Sample-validation test SHA256: 87b3f5dae80cd27d356e28b75c94bdc4d31e83f29691b18aa26b7d6b0ee0f843.
- Provider-backed audit passed directly on HEAD 4cc7a78d95ee7e529394173933817a7266db251d; its HEAD-bound source identity was c30510e3b743954fd10385f02a6c282448843247db69e1da26de5ae22ac7a25d. Governed provider hashes, pair 5:11, selected boundary/support and source lineage were checked. This direct audit used a clean Git-object environment.
- Python 3.12.10 and NumPy 2.3.5 were present.
- Candidate output _02 was absent before and after the attempt.
- The approved scientific arguments/configuration were retained, with the destination changed to _02. The supervisor invoked the same runner by its absolute path rather than the report's relative spelling; the runner bytes and CLI options were unchanged.

## Supervisor

The foreground PowerShell 7 supervisor used Windows Toolhelp process enumeration, sampled the Python root and descendants, summed their working sets, counted candidate-output bytes, polled every 100 ms, and used process-tree termination for threshold stops. Its synthetic checks exercised wall-time, working-set and output thresholds, descendant discovery/termination, and natural exit-code propagation. The limits were monitored, not OS-enforced.

Recorded attempt:

- Python PID/image: 31248 / python.exe; executable was the configured Python 3.12.10.
- Elapsed: 0.951220 s; 7 samples at 100 ms.
- Peak sampled process-tree working set: 48,848,896 bytes.
- Peak/final candidate-output bytes: 0.
- Termination: natural process exit, code 1; no resource threshold caused the stop.
- Trace and summary are retained under outputs/r6_functional_development/INT0B_R1_SUPERVISION_20261013/.

## Failure and reproduced cause

The runner traceback ended in plate_kinematics_adapter._tracked_identity() while executing:

git rev-parse HEAD:R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json

The supervisor process sourced r6-env.ps1 but did not clear the Git object-store variables that this bootstrap sets. The Python child therefore inherited:

- GIT_OBJECT_DIRECTORY=C:\Users\jose_\AppData\Local\ARCANA\git-objects\r6
- GIT_ALTERNATE_OBJECT_DIRECTORIES=F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD1_v0_6D1_R3_11_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CANDIDATE\.git\objects

A read-only reproduction returned exit 128 with those variables; after unsetting both, the same Git query succeeded and returned blob 47e623f83c2ee7bf8887bf823ac005f7e4fd15ff. This explains why the provider audit in the parent shell passed while the runner's nested process failed its source identity gate.

The execution did not create _02, write a trajectory/manifest/sample file, reach resolution comparisons or thermal/geometric evolution, or produce invariant/restart results. The supervisor's output counter remained zero. No evidence indicates access to or mutation of WORLD_HISTORY; the failure occurred during the pre-run Git source-identity check. The prior _01 attempt was not read, modified or cleaned.

## Required boundaries

All failures and previous evidence remain preserved. Do not start a third run under this authorization. Any later decision must be explicit and separate; there is currently no trajectory on which to begin INT-1.

Unchanged gates: BLOCKED_F2AV_QUALIFICATION; OPERATOR_CLASS_UNVERIFIED; THRESHOLD_UNJUSTIFIED; RESOURCE_2GB_SCOPE_UNRESOLVED; F2B_SOLVER_EXECUTION_AUTHORIZED=false; ARCANA_SI1_MECHANICS_QUALIFIED=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.
