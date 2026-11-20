# ARCANA R6 — source T0 normal consistency, 3D closest-segment and gap Jacobian gate

**Date:** 2026-11-20. **Parent:** `250bab7f515a9b38b2acbe3f1c2477da373e4560`.
**Previous FAIR:** 40/40 PASS, source moving 3D paired-material-point geometry
plus exact serial/parallel SHA256 parity on 8×8 and 16×16.
**Next decision:** authorize an **ENGINEERING_ONLY**, **source-exact**
geometric CONTACT DIAGNOSTIC on original 5:8 and 5:8:11 plate
boundaries; no true moving-surface KKT or physical T1.

## The numerically observed unresolved geometry

Previous 16×16 test had four old fixed-T0-KKT-positive
normal reactions associated with **strictly positive** new
3D point-pair oriented gaps: smallest active-link gap
1.0739m at 100 model years, 5.4154m at 500 and 10.9089m at
1000. Maximum |new 3D point gap−old fixed T0 integrated
gap| was 22.3600m at 1000. This **violates geometric
complementarity if the old reactions are interpreted on
the new geometric gap**. It does NOT invalidate the
earlier algebraic fixed-T0 KKT test.

Current edge-derived normal differs from the transported
source centroid-derived normal by ~0.477rad (8×8),
~0.485rad (16×16), nearly independently of elapsed time.
Test the hypothesis that this mismatch existed **at T0**.
Do not attribute the angle exclusively to rotation-induced
mechanical strain without a t=0 audit.

## Source / geometry contracts

New driver:
`experiments/plate58_deforming_explore_v1/g2_t0_normal_segment_jacobian.py`

New test suite:
`tests/test_r6_g2_t0_normal_segment_jacobian.py`

The driver requires original SHA-verified source
`PLATE58_G3_A_OUTER_MULTISCALE_NEW_01`,
`PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01`,
the preceding **36/36 fixed-T0 KKT FAIR** evidence, and
the preceding **40/40 moving 3D FAIR** report and manifest.

The source original boundary IDs `R6BND-T0-...`, parent
node/edge IDs and original triangle plate owners are
reconstructed from read-only FEG/PRE.
8×8 must still have **13 contact pair-node links** and
16×16 **39**, including the authenticated triple node **34587**.

### Gate A: source normals at exactly t=0

For every ORIGINAL boundary **segment**, before movement:

- take 3D original source edge direction and local radial
  direction; construct outward signed edge-perpendicular
  tangent-plane normal;
- take original adjacent plate p/q triangle centroids,
  project p→q direction onto the same local tangent plane,
  and construct the centroid-derived contact normal;
- orient the edge normal consistently toward the centroid
  p→q normal; record per-segment angular difference,
  source edge length and boundary ID;
- separately record each original source pair-node normal
  mismatch with the edge-derived normal at T0.

This is a **definition consistency audit**, not an assumption
that these two geometrically different normal constructions
must be identical. No arbitrary threshold is imposed on the
normal mismatch. Exact T0 source twin material points and
source twin boundary segments must coincide.

### Gate B: independent feature distances at moving geometry

Reconstruct the previous exact Euler SO(3) + KKT residual
trajectory at model years **100,500,1000**, preserving
Euler double-counting avoidance. Recompute current
edge-normal and original point-pair signed 3D gap.

For each ORIGINAL source contact boundary edge, independently
compute the closest two points on the finite
**plate-paired 3D edge segments**, their bounded interpolation
parameters, unsigned 3D distance, signed separation
projected onto the *current edge-normal*, and tangential
offset. Check source edge and plate owner IDs.
No nearest-neighbor matching to invented adjacent
faces or non-source contacts is allowed.

**Limit:** a nearest-segment distance is a positive,
unsigned geometric metric. Its signed projection along a
chosen normal is NOT by itself a rigorous separating
surface distance, nor does it establish a physical
traction law, especially for disjoint endpoint features.
No general face–face shell collision is being solved.

The new 3D point-pair results must replicate the **prior
40/40 FAIR moving 3D** min signed gap and max
|new−T0 gap| to within 1e-7m at each checkpoint; compare
each original source link and plate pair.

### Gate C: diagnostic geometric gap Jacobian and SO(3)

Sample up to six original contact pair-node links in each
region, prioritizing all previous KKT-active links.
Perturb each of the two original plate material copies
along the current source edge-derived 3D contact normal
by ±1.0, ±0.5 and ±0.25m. Reproject perturbed
material points onto the original source sphere.
RECOMPUTE the current edge normal, thus including its
motion rather than freezing it during finite differences.

Compute central-difference directional derivatives of the
signed 3D point-pair gap for p and q. Demand the
difference between 0.5m and 0.25m derivatives <3e-4
and the derivative close enough to the nominal ±1
baseline (absolute mismatch <0.1). Report measured
mismatch from ±1 rather than claiming a closed-form
consistent full geometric contact Jacobian.

Subject all point-pair and nearest-segment gaps to a
separate arbitrary finite **SO(3)** rigid coordinate
rotation, transforming both material positions and local
basis/plate rotations. Differences must be <1e-7m.
Reject invalid original segments or zero normals.

This validates a numerical geometric gap derivative
DIAGNOSTIC in the current constructed configuration;
it does not implement an updated-geometry KKT solver,
full discrete virtual work or real rock physics.

### Parallelism / performance

FAIR measured two workers slower than one
(0.6903865s parallel vs 0.5073308s serial,
**speedup 0.7348503×**), despite exact SHA parity.
This new experiment runs both tiny independent regions
**serially** (workers=1). Parallelize larger global
source P1 element assembly later, with deterministic
sparse reductions and CPU/RSS benchmarks, rather
than introducing process-spawn overhead here.
Dependent yearly KKT steps remain sequential.

## FAIR execution — new code NOT YET SOURCE RUN

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

python -m pytest -q \
  tests/test_r6_g2_t0_normal_segment_jacobian.py \
  tests/test_r6_g2_moving_3d_contact_parallel.py \
  tests/test_r6_g2_regional_unilateral_contact_time.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -f "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01/MANIFEST.json"
test -f "$BASE/G2_MOVING_3D_CONTACT_PARALLEL_NEW_01/MANIFEST.json"

python -m experiments.plate58_deforming_explore_v1.g2_t0_normal_segment_jacobian \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --prior-moving-3d "$BASE/G2_MOVING_3D_CONTACT_PARALLEL_NEW_01" \
  --output "$BASE/G2_T0_NORMAL_SEGMENT_JACOBIAN_NEW_01"
```

All experimental outputs must go into an **exclusive new**
evidence folder. Fail closed if a source or previous manifest
SHA changes, a source border is not represented,
previous 40/40 3D trajectories are not reproduced, or
independent SO(3)/FD checks fail.

## Possible findings and next decision

- If mismatch angle is already present at T0, likely cause
  is the distinct geometric definitions
  (triangle-centroid vs boundary perpendicular) rather
  than growing numerical Euler drift; still report
  exact per-segment distribution before adopting that
  interpretation.
- If nearest-segment geometry reveals positive separation
  of old reaction-active KKT links, the old T0 constraint
  must **not** be promoted to moving 3D contact closure.
- If FD and SO(3) checks PASS, next create a
  **proper updated-geometry contact constraint** on a
  single consistently defined signed feature gap,
  with force Jacobian, multiplier sign and objectivity,
  and independently verify dynamic 100/500/1000-year
  contact activation, restart and energy/work.
- Only after regional mechanical geometry is qualified
  consider global moving-contact computational
  architecture, larger parallel source-element assembly,
  and ultimately separately sourced natural G2/G3/G4.

```text
SOURCE_MOVING_3D_DIAGNOSTIC_FAIR=PASS_40_40
T0_EDGE_CENTROID_NORMAL_AUDIT=CODE_PUBLISHED_FAIR_PENDING
SOURCE_EDGE_CLOSEST_SEGMENT_AND_GAP_JACOBIAN=FAIR_PENDING
FULL_MOVING_CONTACT_KKT=NOT_RUN
G2_G3_CALIBRATED_PHYSICS=NOT_QUALIFIED
physical_T1=null
D_024=ACTIVE
```
