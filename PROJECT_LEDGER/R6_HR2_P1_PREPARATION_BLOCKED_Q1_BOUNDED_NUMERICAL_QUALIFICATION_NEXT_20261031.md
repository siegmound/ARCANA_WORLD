# ARCANA R6 — HR2-P1 prepared, numerical execution pending; HR2-P1-Q1 next gate

**Date:** 2026-10-31. **Authority:** User/operator-provided FAIR report `docs/arcana/R6_HR2_P1_PREPARATION_FAIR_20261031.md` and `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_PREP_20261031_01`, not independently rerun from GitHub. Worktree FAIR `r6/runtime-copy-r1-fair` at original HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`, intentionally dirty, not to be reset or committed automatically.

## Actual state

`HR2_P1_PREPARATION=PREPARED_SOURCE_TESTS_AND_FIXED_ACCEPTANCE_NOT_RUN`

`HR2_P1=BLOCKED_NUMERICAL_QUALIFICATION_NOT_EXECUTED`

The preparation authored **new isolated** `experiments/hr2_p1/model.py`, `manufactured.py`, `checkpoint.py`, `acceptance.json`, two `experiments/hr2_p1_checks/checks_*.py`, opt-in qualification and child-resume scripts, README and source contract. **17 statically identified functions** with parameterized cases: do **not** describe as 17 successful tests. Only AST, JSON, SHA and formatting checks executed. 336 prep manifest members checked. The new numerical method, stability, polar stencil, manufactured mode error order, and native/B0 restart have **no executed qualification evidence**. Original 10k/A0/HR1/HR2-P0/source preserved, no push/commit.

Exact prepared source contract SHA256:
`544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186`.
Read and compare actual local source-contract bytes before attempting qualification; do not reconstruct or replace SHA from this ledger.

## Proposed next bounded gate: HR2-P1-Q1 (not executed in this record)

**Objective:** run the frozen manufactured-method qualification only, using the already prepared isolated launcher and contract. A separate FAIR operator/user instruction should authorize Q1 numerical execution. **No** 1000Y/10k/100k, production global physics, new input downloads, engine source rewriting, additional manufactured coefficients, or automatic patching/retry.

1. Read preparation report, `experiments/hr2_p1/acceptance.json`, frozen `SOURCE_CONTRACT.json`, P0 `MINIMUM_PHYSICS_AND_VALIDATION.md`, original source hash evidence. Check input SHA and `--help`; source code, acceptance thresholds and SHA must match preparation. Preserve all old archives and choose a new exclusive `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/HR2_P1_Q1_...` output root.
2. Use predeclared launcher, with actual qualified environment, **only when Q1 is authorized**:
```bash
PYTHONPATH=src:experiments PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
scripts/r6_hr2_p1_qualification.py \
--output /NEW/EXCLUSIVE/HR2_P1_Q1_BOUNDED_OUTPUT \
--expected-contract-sha256 544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186 \
--execute-manufactured-method-tests
```
Do not run `checks_*.py` by relying on default `test_*.py` discovery; the opt-in runner explicitly selects two prepared test files.
3. Verify independent rational unequal-area **2×2 local patch** oracle; 16×8 real spherical constant/harmonic/positivity/volume/face uniqueness/antimeridian/polar checks; both axisymmetric and **non-axisymmetric** cell-average manufactured harmonic tests; spatial sequence 16×8→32×16→64×32→128×64→256×128 at frozen time, and temporal dt,dt/2,dt/4 at 16×8. Original limits: all refinement L1/L2/L∞ spatial observed order>=1.5 and <=5% half-dt continuum-error condition; temporal 0.9..1.2 against discrete same-mesh reference. No posthoc tolerance changes. Check CFL guard before mutation, exact accepted dt/substep histogram and conservation ledger.
4. Check native 3Y/10Y direct/split, separate-process child restart, pending-window state, complete native geometry/time/balances/initial field identity, source/config/mesh/B0 journal provenance, wrong/modified/stale/corrupt negative tests.
5. Capture test collection, JUnit, actual analytic-vs-numerical residuals per mesh/mode/step, global mass and positivity, wall/CPU/RSS/storage/query/restart, source pins before/after and original evidence immutable. All outputs/manifest under new exclusive Q1 root.
6. **Fail closed** if non-axisymmetric polar stencil, convergence, temporal order or restart fails. Emit `HR2_P1=BLOCKED_<specific_reason>` with retained stdout/stderr/JUnit/numerical arrays and separately proposed diagnosis gate. Do not modify acceptance and rerun in place; the existing prepared contract remains immutable.
7. Emit `HR2_P1=PASS_MANUFACTURED_SPHERICAL_DIFFUSION_CONSERVATION_AND_CONVERGENCE` **only** if the actual complete bounded suite and proof artifacts pass. Even then this is a manufactured numerical fixture, not a source-admitted geological operator, global Deep/climate/ecology or a qualified 2K×1000Y scientific trajectory.

## Authority boundary

```yaml
HR2_P0: PASS_GROUNDED_GLOBAL_PHYSICS_AND_ARCHIVAL_READINESS_MAP_OPERATOR_REPORTED
HR2_P1_PREPARATION: PREPARED_SOURCE_TESTS_AND_FIXED_ACCEPTANCE_NOT_RUN
HR2_P1: BLOCKED_NUMERICAL_QUALIFICATION_NOT_EXECUTED
HR2_P1_Q1: PROPOSED_BOUNDED_NUMERICAL_EXECUTION_NOT_YET_RUN
HR2_P1_GLOBAL_SCIENTIFIC_SOURCE_ADMISSION: false
GLOBAL_1000Y_EXECUTION_AUTHORIZED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
```
