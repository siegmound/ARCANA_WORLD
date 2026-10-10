# Next action — F2-B PREFLIGHT DESIGN only
2026-10-10: Code fix, project ledger and complete F2AV offline recovery are now published separately in GitHub. Evidence branch `evidence/r6-bw1-f2av-20261010` at `2b03fa558b02cb865c4f234e45f0386fab678822`.

## Start-up
1. On Windows check current branch `r6/si1-bandwidth-f2av`, HEAD, and `git status --short`; fetch origin and fast-forward only if safe, never use reset/force. Keep untracked `outputs/r6_si1_bandwidth_f2av_offline_recovery/` untouched.
2. Read `AGENTS.md`, `PROJECT_LEDGER/STATUS.md`, `PROJECT_LEDGER/F2B_PREFLIGHT_DESIGN.md`, `PROJECT_LEDGER/EVIDENCE_INDEX.md`, `docs/arcana/SI1_BW1_F2AV_DIAGNOSTIC.md`, source contracts, ShellSet Fortran solver/permutation path and `configs/r6_shells_si1/engineering_case.json`.
3. Evidence: LFS archive `F2AV_OFFLINE_RECOVERY_F2AV_WITH_F2A_REFERENCE_V1.tar.gz`, SHA256 `bdde8d4320b1fa6de577988bf911817918e910373bdbff9922c9d9c98f646562`; internal manifest SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`. Original historical `BLOCKED_F2AV_QUALIFICATION` and derived recovery `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION` remain distinct.

## Design-only technical workpack
- Trace exact DOF mapping from band global index through permutation to node/component/basis; retain `DOF_MAPPING_UNVERIFIED` if not fully supported by actual artifacts.
- Determine operator class and theoretical symmetry expectation from equations, boundary conditions and assembly source; explain whether the 10 asymmetric pairs require more diagnostics; never symmetrize without authority.
- Specify how to investigate possible rigid/nullspace modes in this global closed-sphere case with 0 prescribed velocity BC, without assigning gauge automatically.
- Calculate a realistic resource envelope for possible future solver: baseline 2,249,799,104 bytes for one band REAL*8 allocation, with factors, pivoting, copies, LAPACK workspaces, per-rank/aggregate memory and failure controls separated.
- Design validation: matrix/forcing/input hash identities, normalized residual and backward error criteria, convergence and engineering-only interpretation. Numeric thresholds must be justified by source/contract rather than invented.
- Define separate future NVHPC compile-only writer/IEEE probe; existing `139 passed, 2 skipped` do NOT resolve NVHPC, automatic positive E2E sealed test, or BW0/BW1/SciPy gaps.
- Produce a design document `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` and candidate fail-closed contract with requirements / evidence / UNKNOWN / gates, **without** building or running a solver. Update PROJECT_LEDGER at a significant decision gate.

## Decision boundary
Current operational disposition `GO_FOR_F2B_SOLVER_PREFLIGHT_DESIGN_ONLY`. Appropriate outcome design complete awaiting execution authority or blocked pending source/provenance. No scientific physics qualification implied.
Forbidden: new Fair/MPI runs, solve, factorization, gauge edit, source-locked ShellSet changes, forward evolution, canonical writes, re-running proven upstream ShellSet benchmarks.
