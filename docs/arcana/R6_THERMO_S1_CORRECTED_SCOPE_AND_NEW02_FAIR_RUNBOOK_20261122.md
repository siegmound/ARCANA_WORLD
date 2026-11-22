# R6 THERMO S1 — corrected Julia scope, dedicated NEW02 FAIR gate (2026-11-22)

**Status: CODE_PUBLISHED_ON_ISOLATED_BRANCH; FAIR tests / NEW02 engines PENDING.**

Source branch: `r6/thermo-s1-scopefix-real-gate-v2-20261122`.
Original source/software-only preflight checkout: `393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2` (35 targeted + 640 selected); preserve it and the original evidence.
Earlier real standalone tests ran at this ORIGINAL checkout with a DIAGNOSTIC-ONLY Julia `global data` patch; no original source commit changed. Their 17-file write-once archive is:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_S1_STANDALONE_DIAGNOSTICS_NEW01`,
manifest SHA256 `3a4559c2397ea3a1a56a3cc5cba95077bd48511f7fd7f7188c84e68ae2548298` (operator-reported, not independently downloaded/rehashed through GitHub).

## Why change the code

The historical Julia script fails at line 36 with `UndefVarError: data` caused by soft scope in top-level `try`. V2 splits two fixtures into properly scoped functions with `finally` cleanup. Besides previous report fields it emits `G_system`, both phase weight/molar fractions, KLB1 upstream `G` and `s_cp[1]` reference deltas, and CUSTOM_IG density closure. A separate V2 Python report validator fails closed on reference drift and improper cross-solver promotion. Previous Python pilot and `run_perplex_official` are unchanged.

FAIR standalone facts: MAGEMin_C.jl v2.4.5, MAGEMin_jll v2.1.0+0, official portable Julia 1.10.4. KLB1 energy difference `5.614328983938321e-7`, cp difference `0.6511044569438127` (<2), CUSTOM_IG density closure zero. Perple_X source SHA `950d882bb6a9325a627109aa7154f7b526aa3087`, release tar SHA256 `ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7`, real upstream BL691 MEEMUM test PASS. CUSTOM_IG README mass fractions / G / rho do NOT agree precisely with observed current backend outputs; this remains `PENDING_QUANTITATIVE_RECONCILIATION`. Do not label these suites independent experimental validation or compare the different provider chemistries.

## Next FAIR action: only source checkout and targeted regression tests

Never pull, reset, or branch-switch inside the old detached worktree. Use separate clean worktree:

```bash
OLD=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
NEW=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_THERMO_S1_V2_VERIFY
BRANCH=r6/thermo-s1-scopefix-real-gate-v2-20261122
cd "$OLD"
git fetch origin "$BRANCH:refs/remotes/origin/$BRANCH"
test ! -e "$NEW" && git worktree add --detach "$NEW" "refs/remotes/origin/$BRANCH"
cd "$NEW"
git status --short
git rev-parse HEAD
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q -ra --tb=short \
  tests/test_r6_thermo_provider_pilot.py tests/test_r6_thermo_s1_v2.py
```

**Stop and report the exact SHA, pytest counts and errors before running NEW02 gates.** No fresh evidentiary directory is consumed by the above read-only code checks. The new source has NOT been run on FAIR and has NOT passed real-provider tests yet.

## Separate write-once NEW02 gates, only after review

Preflight script: `scripts/r6_thermo_s1_corrected_preflight_fair.sh`; outputs `R6_THERMO_S1_SCOPEFIX_PREFLIGHT_NEW02/{PYTEST.log,MANIFEST.json}` (software-only). Must match original preflight SHA and current tracked clean source; do not repeat the original preflight.

External script: `scripts/r6_thermo_s1_corrected_run_official_fair.sh` (run only after NEW02 preflight PASS, from new clean checkout, Python `arcana-r6-linux`). Set the pinned external tool paths from earlier working `arcana-thermo-compat` conda prefix, with Julia official binary and its isolated `JULIA_DEPOT_PATH`, Perple_X pinned source/release/meemum, then invoke `bash scripts/r6_thermo_s1_corrected_run_official_fair.sh`. Outputs `R6_THERMO_EXTERNAL_OFFICIAL_NEW02` with both real MAGEMin samples, source-reference Perple_X MEEMUM, validation logs and SHA256 manifest. This code-head is cryptographically checked against NEW02 preflight, not the historical `393ee8c1`.

All NEW02 outputs are **write-once**. On failure preserve them and design NEW03, never delete/overwrite failed evidence. Run scripts with `bash`, not `source`, so internal `set -euo pipefail` cannot close the user's interactive SSH shell.

## Scientific authority

No T0 native phase/rock/fluid identity selected; `D-024=ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. No cross-model ranking until common P/T units, independent full oxide chemistry, redox and H2O, model/database crosswalk and component-wise mass closure. After genuine NEW02 success: S2 >=5 independent repeat-process checks and S3 5x5 P/T, under resource limits/site policy (start with one thread).
