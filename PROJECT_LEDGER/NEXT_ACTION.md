# NEXT — INT-2 query, refinement and reconstruction on existing candidate evidence

INT-1D is complete within its authorized scope. The new pair-5:11 normal-continental trajectory and the preserved INT-0B-R4 hot-extended trajectory have both passed their applicable bundle/provenance checks; the INT-1A evaluator has measured actual-time full/fixed/retrospective retention for each. These are two case-specific engineering trajectories, not a general retention qualification.

## Current action

Perform a bounded offline INT-2 evaluation using the existing R4 and INT-1D bundles: verify the candidate query/refinement/reconstruction path against their manifests and state/time supports, record which operations are already executable, and identify any missing binding needed for repeatable candidate retrieval. Reuse existing code and tests. Do not run another evolution, infer geological events, create canonical state, or treat retrospective selection as an online policy. Any additional numerical execution requires separate authorization. B0 `HistoryStore` executable registration/query/replay remains distinct and currently descriptor-only.

## Inputs and constraints

- R4 bundle: `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/`, manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.
- INT-1D bundle: `outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02/`, manifest SHA256 `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`.
- Comparison report: `docs/arcana/INT1D_EXECUTION_REPORT.md`.
- Preserve all previous failures and output directories. No Fair, MPI, ShellSet, Solver, DGBSV, post-rift evolution, or WORLD_HISTORY modification. Preserve `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

## Archived proposal — INT-1B before INT-1C implementation

Current decision (2026-10-13): `INT1B_NEXT_EVIDENCE_EXPERIMENT_DEFINED__EXECUTION_NOT_AUTHORIZED`. Report: `docs/arcana/INT1B_EVIDENCE_DENSITY_AND_DISTINCT_REGIME_DESIGN.md`. INT-1A remains the empirical baseline: `INT1A_RETENTION_EMPIRICAL_BASELINE_EVIDENCED__GENERAL_POLICY_NOT_QUALIFIED`.

## Historical action (archived)

The minimum next evidence run is defined but not authorized. Do not execute provider-backed evolution until a separate authorization and preflight. Proposal: pair 5:11, audited boundary `R6BND-T0-27e4d497530e681071fb`, its two admitted normal continental supports, T0=210 Ma, 1,000 engineering years, existing frozen Euler/kernel and unchanged boundary conditions; preserve factors 0.001/0.0005/0.00025 and add 0.000125, capturing every substep only at the finest rung. A runner boundary selector must accept only one verified eligible ID and retain all current provider checks. Re-materialize/verify both complete profiles and material tuple, hashes, environment and output paths immediately before any future authorized run. No second case, alternate physics, parameter change, retry, or canonical write.

The comparison target is R4's hot-extended boundary `R6BND-T0-3eb57747e6f0a3f3305f` at common factor 0.00025; code for the reduced kernel/step path is unchanged since the R4 commit. Edge-specific forcing and thermal/geometric class vary together, so this contrast cannot establish a physical cause. The 0.000125 substep count, actual sample density, run costs, and general online/event retention remain `UNKNOWN`. B0 replay remains `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`; executable registration/query/replay binding remains a separate prerequisite for restart-cost claims.

The reviewed output is `outputs/r6_functional_development/INT1_RETENTION_20261013/FINAL/`. Provisional first-pass outputs created during this same audit are preserved at the parent directory and `_R1` sibling; only `FINAL/` passed the completed cross-artifact review.

No provider-backed evolution, Fair, MPI, ShellSet, Solver, B6 post-rift evolution, or WORLD_HISTORY access/publication was performed in INT-1B.

Preserved gates: BLOCKED_F2AV_QUALIFICATION, OPERATOR_CLASS_UNVERIFIED, THRESHOLD_UNJUSTIFIED, RESOURCE_2GB_SCOPE_UNRESOLVED, F2B_SOLVER_EXECUTION_AUTHORIZED=false, ARCANA_SI1_MECHANICS_QUALIFIED=false, WORLD_HISTORY_PRODUCTION_AUTHORIZED=false.

---

The remaining NEXT_ACTION content below is an archived snapshot from earlier gates. Its no-retry/INT-1-blocked statements describe those past checkpoints; the active action is the INT-1 analysis above.

## Historical checkpoint — INT-0B-R1 second attempt failed; no third execution was then authorized

**Current decision (2026-10-13):** INT0B_R1_SECOND_ATTEMPT_FAILED_PRE_OUTPUT_VALIDATION_GIT_OBJECT_ENV_REINSERTED. The single authorized second attempt on HEAD 4cc7a78d95ee7e529394173933817a7266db251d exited before candidate output creation because the supervisor child inherited Git object-store variables from r6-env.ps1. Full record: docs/arcana/INT0B_R1_SECOND_ATTEMPT_FAILURE.md.

## Historical action (archived)

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
