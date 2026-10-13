# NEXT - INT-1 empirical state-retention and reconstruction analysis

Current decision (2026-10-13): INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED. The authorized fourth R4 attempt completed and its output bundle was verified; see docs/arcana/INT0B_R4_EXECUTION_REPORT.md. Earlier _01-_03 failures remain immutable. No fifth INT-0B attempt is authorized or needed.

## Current action

Perform bounded, offline empirical retention/reconstruction analysis using the verified candidate trajectory at outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/. Recheck its manifest and hashes, then keep the source bundle read-only. Compare full-state retention, endpoints plus selected diagnostics, and deterministic reconstruction from checkpoints/forcing only where the existing contract supports it. Measure retained bytes, reconstructed-field differences, replay behavior, and information lost under each policy. Keep B0 replay DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE; do not claim HistoryStore registration or canonical retention.

Write analysis outputs only under a new isolated outputs/r6_functional_development/INT1_RETENTION_20261013/ directory; do not overwrite INT-0B-R4 evidence. This is analysis of the existing noncanonical engineering trajectory, not a new evolution, scientific promotion, or canonical retention decision. No Fair, MPI, ShellSet, Solver, B6 post-rift evolution, or WORLD_HISTORY access/publication.

Preserved gates: BLOCKED_F2AV_QUALIFICATION, OPERATOR_CLASS_UNVERIFIED, THRESHOLD_UNJUSTIFIED, RESOURCE_2GB_SCOPE_UNRESOLVED, F2B_SOLVER_EXECUTION_AUTHORIZED=false, ARCANA_SI1_MECHANICS_QUALIFIED=false, WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.

---

The remaining NEXT_ACTION content below is an archived snapshot from earlier gates. Its no-retry/INT-1-blocked statements describe those past checkpoints; the active action is the INT-1 analysis above.

## Historical checkpoint — INT-0B-R1 second attempt failed; no third execution was then authorized

**Current decision (2026-10-13):** INT0B_R1_SECOND_ATTEMPT_FAILED_PRE_OUTPUT_VALIDATION_GIT_OBJECT_ENV_REINSERTED. The single authorized second attempt on HEAD 4cc7a78d95ee7e529394173933817a7266db251d exited before candidate output creation because the supervisor child inherited Git object-store variables from r6-env.ps1. Full record: docs/arcana/INT0B_R1_SECOND_ATTEMPT_FAILURE.md.

## Current action

Preserve the failure record and stop. Do not retry INT-0B under this authorization; no third execution is permitted here. INT-1 remains blocked because no validated trajectory exists. No further scientific execution is authorized by this checkpoint.

The reproducible environment issue is that r6-env.ps1 sets GIT_OBJECT_DIRECTORY and GIT_ALTERNATE_OBJECT_DIRECTORIES. Any later, separately authorized operational task would need to clear both in the final process environment after loading that bootstrap and verify the repository Git query in the same child context before any run. This is a diagnosis, not authorization to execute again.

## Attempt evidence

- HEAD: 4cc7a78d95ee7e529394173933817a7266db251d; parent e95c7dbf281ede5312512654262b9925fa87eb02.
- Provider-backed audit passed directly on final HEAD with source identity SHA256 c30510e3b743954fd10385f02a6c282448843247db69e1da26de5ae22ac7a25d. The nested execution environment differed because it reloaded r6-env.ps1 without clearing the Git object variables.
- Runner SHA256 2b5ab1af081fae9ad2a0681a4ba9b95dfca032839caba52cdc440525cf77fc1c; sample test SHA256 87b3f5dae80cd27d356e28b75c94bdc4d31e83f29691b18aa26b7d6b0ee0f843. Python 3.12.10, NumPy 2.3.5.
- Candidate destination _02 remained absent; exit 1; 0.951220 s; 7 samples; peak sampled process-tree working set 48,848,896 bytes; output 0 bytes. These are monitored measurements, not OS-enforced quotas.
- No numerical samples, final state, resolution comparison, replay/restart, output manifest, or INT-1 evidence exists. No evidence of WORLD_HISTORY access or mutation. Prior _01 remains untouched.

## Publication

The failed-attempt and correction commits remain subject to normal fast-forward publication. Do not force-push or rewrite history. Any documentation consolidation must stage explicit report/ledger paths and exclude outputs.

## Preserved gates

BLOCKED_F2AV_QUALIFICATION; OPERATOR_CLASS_UNVERIFIED; THRESHOLD_UNJUSTIFIED; RESOURCE_2GB_SCOPE_UNRESOLVED; F2B_SOLVER_EXECUTION_AUTHORIZED=false; ARCANA_SI1_MECHANICS_QUALIFIED=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.
