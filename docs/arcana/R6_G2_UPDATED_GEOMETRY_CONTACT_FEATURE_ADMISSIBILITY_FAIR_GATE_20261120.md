# ARCANA R6 — updated-geometry source contact feature admissibility gate

**Date:** 2026-11-20  
**Previous FAIR geometry PASS:** source commit `28bc02c49d86b15dc9dae3388b66202ae4d8beb4`, operator-reported driver exit 0, `REPORT.json` SHA256 `f8747af7f62df89039c7ec641b8c64917cf7c52cb30001058b17d6fed89a2a04`. Full FAIR report was not independently fetched.

## Goal and authority

This is **ENGINEERING_ONLY FEATURE-ELIGIBILITY AND WITNESS CLASSIFICATION**, not an updated 3D physical KKT solver.

Original source-controlled topology is mandatory: authentic 8×8 original plate pair 5:8 (12 edges, 13 pair-node links) and 16×16 original 5:8:11 region (36 edges, 39 links, triple parent node 34587). Only FEG/PRE and existing named R6BND-T0 edges; no invented neighboring faces, faults, loads or geological material laws.

The new driver is `experiments/plate58_deforming_explore_v1/g2_contact_feature_admissibility.py`; new source-free suite `tests/test_r6_g2_contact_feature_admissibility.py`.

## Mathematical witness contract

The two original paired finite 3D source-edge segments are `a→b` (plate p) and `c→d` (plate q), with directions `e=b-a`, `f=d-c`. Compute a bounded nearest-feature witness `(s,t)` and independent unsigned closest-segment distance using the previously stabilized source algorithm. The dimensionless transversality condition is `||e×f||²/(||e||²||f||²) >= 1e-8`. For **engineering eligibility only**, require `0.001 < s,t < 0.999` and magnitude of the cross-product normal's alignment to the previously source-derived current edge normal at least 0.5.

On this strictly interior, nondegenerate witness branch, define a co-rotating, oriented **mathematical line-line gap** `g = ((closest_q - closest_p)·n)`, with `n = ±(e×f)/||e×f||` oriented toward the declared reference normal. Analytic discrete derivative is `∇_{a,b,c,d}g = (-(1-s)n, -sn, (1-t)n, tn)`. Validate this **same** g and its gradient by central differences and finite SO(3) rotation. With a purely normalized manufactured multiplier, verify zero net discrete force, moment balance, and virtual-work consistency.

The numerical cutoffs above are conservative **engineering abstention rules**, not measured geological collision thresholds. For genuinely parallel/nearly-parallel cases, endpoint cases, reference-normal inconsistency or feature-switching, return `AMBIGUOUS` or `NOT_QUALIFIED` with `signed_gap_m=null`. At T0 the twin original source edges coincide and must not be promoted to a signed contact gap by inventing a normal.

**Important:** even for an eligible skew-edge witness, finite line-line distance and orientation alone **cannot prove separating rock faces or volume non-penetration**. All records keep `physical_surface_contact_qualified=false`, and the driver does not run KKT or create physical T1.

## Genuine-source gate

Read-only SHA-verified source FEG/PRE and prior passed KKT/moving3D evidence must replay exactly. Additionally require current `G2_T0_NORMAL_SEGMENT_JACOBIAN_NEW_01` REPORT/MANIFEST matching its SHA and scientific status, check prior source pins, and compare every original source feature distance and signed projected diagnostic against that previous FAIR report within `1e-7 m`.

For 0,100,500,1000 model years, emit per R6BND-T0 source edge:
- plate pair, original parent-node IDs, s/t, dimensionless transversality ratio and unsigned distance;
- witness classification and a reason if ambiguous;
- signed *engineering* edge-edge gap and 4×3 gradient **only** if eligible;
- otherwise null signed gap and zero physical authorization;
- for eligible features, two-sided FD audit, SO(3), virtual work and normalized force/torque;
- classification transitions between checkpoints, including triple node coupling by source parent ID.

Full source FAIR run is **PENDING**. A source inventory can be numerically PASS even if most real features are AMBIGUOUS. That is an important negative result that prevents an unjustified full KKT claim.

## FAIR execution on clean checkout

```bash
set -euo pipefail
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
test -z "$(git status --porcelain)"
git fetch origin r6/multiphysics-integration-20261026
git switch --detach FETCH_HEAD
git rev-parse HEAD

source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_contact_feature_admissibility.py \
  tests/test_r6_g2_t0_normal_segment_jacobian.py \
  tests/test_r6_g2_moving_3d_contact_parallel.py \
  tests/test_r6_g2_regional_unilateral_contact_time.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -f "$BASE/G2_T0_NORMAL_SEGMENT_JACOBIAN_NEW_01/MANIFEST.json"
test ! -e "$BASE/G2_CONTACT_FEATURE_ADMISSIBILITY_NEW_01"

python -m experiments.plate58_deforming_explore_v1.g2_contact_feature_admissibility \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --prior-moving-3d "$BASE/G2_MOVING_3D_CONTACT_PARALLEL_NEW_01" \
  --prior-normal-jacobian "$BASE/G2_T0_NORMAL_SEGMENT_JACOBIAN_NEW_01" \
  --output "$BASE/G2_CONTACT_FEATURE_ADMISSIBILITY_NEW_01"
```

All output goes to exclusive `REPORT.json`/`MANIFEST.json` with SHA256. No rerun into an existing evidence directory. If pytest/source replay fails, diagnose and fix with a new commit; do not relax the prior 1e-7m SO(3) threshold or mutate earlier evidence.

## Post-gate scientific decision

If the source inventory is overwhelmingly parallel, endpoint or normal-ambiguous, **do not force an updated-geometry KKT**. The following research step is a signed *oriented surface-feature* gap contract using authentic plate-owned adjacent triangles/solid thickness and contact topology, with physically justified normals, coupled triple-junction handling and force/moment transfer. Only after an objective, differentiable, verified geometric gap exists may an **ENGINEERING_ONLY** manufactured updated-geometry Signorini solver be attempted.

`D-024=ACTIVE`, `physical_T1=null`, no canon/HistoryStore mutation, no natural G2/G3/G4 traction, and serial execution for these small regions.
