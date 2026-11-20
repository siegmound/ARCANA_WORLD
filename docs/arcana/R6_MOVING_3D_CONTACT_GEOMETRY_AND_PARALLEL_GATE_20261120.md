# ARCANA R6 — Objective moving 3D contact-geometry diagnostic and parallel source domains

**Date:** 2026-11-20.
**Prerequisite FAIR:** genuine source 5–8 and 5–8–11, fixed-T0-normal
**regional unilateral KKT time PASS 36/36** on
`4ec52f3a3e8815ccf495a8611b17bef994f6f592`,
recorded on GitHub in `ababe8eccec4af25d207cc35322efeb6a31e6bca`.

**DECISION:** authorize a **READ-ONLY, ENGINEERING_ONLY,
GEOMETRY DIAGNOSTIC** with serial/parallel parity. It MUST NOT
declare true 3D contact closure or actual physical T1 merely because
the earlier fixed-T0 gap is nonnegative. Only the geometry
reconstruction and numerical parity gates can PASS.

## Source scope

- Original regional **8×8** source parents: 81 nodes, 128
  triangles, **5:8**, 12 boundary source edges / 13 pair-node links.
- Original **16×16**: 289 nodes, 512 triangles, **5:8:11**,
  36 boundary source edges / 39 pair-node links, authentic
  triple source parent node **34587**.
- All contact edge IDs must originate in source
  `R6BND-T0-...` with authentic plate-pair owners and
  original T0 FEG, PRE and nodal binding.
- Require prior FAIR `G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01`
  `REPORT.json` and SHA `MANIFEST.json`.
  Recheck the original parent and source SHA metadata and
  exact prior KKT status. **No source mutation**.

## Avoid the most dangerous trajectory error: double Euler counting

The existing regional implicit KKT integrator's nodal displacement
`u(t)` already contains the Euler plate rigid velocity integrated
in the original T0 East/North reference frame. Therefore applying
an Euler finite rotation directly to `x0 + E0*u(t)` would count
the Euler component **twice**.

Instead separate the small residual in the original source frame:

```text
u_residual(t) = u_KKT(t) - t * g_Euler(T0)
v_residual(t) = v_KKT(t) - g_Euler(T0)

x_plate(t) = R_plate(t) * normalize_radius(x0 + E0*u_residual)
v_plate(t) = omega_plate cross x_plate(t)
             + R_plate(t) * derivative_of_radius_projection(E0*v_residual)
```

`R_plate(t)=exp([omega_plate]x*t)` uses exact source G1
Euler rotation, and transforms each **independent plate-local
material view** separately. The radial projection keeps the
spherical source radius; it is an explicitly constructed
trajectory, **not** a nonlinear shell constitutive update.
A zero residual exactly reproduces Euler-rigid rotation
in a manufactured test.

## Source-bound updated 3D contact geometry

For each legitimate pair-node link at years **100, 500 and 1000**:

1. Obtain actual moved 3D coordinates for both plate material
   copies of its parent node and both plate-owned
   copies of every incident source boundary edge.
2. Form the current edge tangent from the mean of the two
   deformed, plate-specific edge tangents and the local
   radial direction at the pair.
3. Construct current tangent-plane normal using the
   3D cross-product, and fix orientation by the original
   pairwise source-normal transported under each plate's
   original Euler SO(3) rotation. Reject degenerate
   edge tangents and ambiguous normal directions.
4. Compute **signed point-pair geometric gap**:
   `(x_q(t)-x_p(t)) dot n_current(t)`;
   also report point-to-point tangential slip, relative
   normal material velocity and the original integrated
   T0 `gap_KKT`.
5. Preserve original contact boundary IDs per pair-node
   in the full report and compare exactly with the
   original T0-normal KKT checkpoint minimum/maximum gaps,
   active link count, pair count, triple node.
6. Report the source-KKT geometric discrepancy per link
   and summarize the maximum absolute difference,
   **most negative signed geometric gap**, number of
   negative gaps below `-1e-6 m`, and the minimum
   gap among links with positive KKT reaction.

**Crucial distinction:** an oriented geometric **pair of
coincident-origin material points**, projected onto an
updated *edge-derived* normal, is more informative than
the time integral of a frozen T0 normal. It is **still not**
the full signed minimum distance between two deforming
edge/face surfaces, nor a real gap-conditioned contact
reaction solution. A negative geometric gap does not
invalidate the previous algebraic KKT proof, but it
**blocks** a statement that 3D nonpenetration is solved.

At noncoincident points, equal/opposite artificial
contact forces applied at separate material points
may yield nonzero torque. Record the corresponding
normalized couple rather than pretending a
zero global torque identity has been proven.
No reaction magnitudes are physical newtons.

## Parallelization policy

Numerical dependencies matter:

- **Parallelize by independent source region** (8×8, 16×16)
  with `ProcessPoolExecutor` and **spawn**, up to two
  workers, each reading the same sealed inputs but writing
  no files.
- **Do not parallelize sequential time steps** of one
  Kelvin–Voigt/KKT state evolution; each uses the
  previous step's displacement and gap.
- Source-topology lookup and boundary-point calculations
  are NumPy based; KKT uses a cached sparse LU/Schur
  factorization per regional timestep.
- For the first FAIR gate, use
  `--workers 2 --verify-serial-parity`.
  This executes two region jobs in parallel and
  separately re-executes them serially; checkpoint
  SHA256 hashes of displacement, KKT gap and geometric
  signed gap must be **byte-identical**.
- Measure parallel and serial elapsed wall time, per-worker
  peak RSS, and the actual **serial/parallel speedup**.
  Startup overhead or memory pressure may cause speedup
  `<1`. Never assert that two workers are faster without
  FAIR evidence.
- BLAS threads `OPENBLAS_NUM_THREADS=1`,
  `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`
  prevent nested oversubscription.
- If future global work needs acceleration, consider
  **independent plate-owned element/region assembly**
  distributed across CPU processes, with a deterministic
  sparse reduction before solving. A single global
  implicit time trajectory remains causal; heterogeneous
  CPU/GPU strategies require a benchmark, not assumptions.

## Validation and interpretation

The source-free unit suite covers:
- source-bound contact edge IDs and no invented contacts;
- zero displacement/coincident source pair;
- deliberately positive and negative signed geometric gaps;
- **no Euler double counting** at multiple time horizons;
- common finite SO(3) frame equivariance of material paths
  and signed point-pair gaps;
- exactly matching vs deliberately divergent
  serial/parallel checkpoint digest;
- reject degenerate vectors and missing regional scope.

**Fail closed** on source SHA mismatch, incorrect
previous checkpoint reproduction, source junction
mismatch, degenerate current geometry, nonfinite
coordinates, or nondeterministic serial-parallel output.
**Do not** mark 3D physical contact PASS based only
on numerical reconstruction.

### FAIR operator invocation — code PENDING

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
  tests/test_r6_g2_moving_3d_contact_parallel.py \
  tests/test_r6_g2_regional_unilateral_contact_time.py \
  tests/test_r6_g2_source_contact_objectivity.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -f "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01/MANIFEST.json"
test -f "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01/REPORT.json"

python -m experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --workers 2 \
  --verify-serial-parity \
  --output "$BASE/G2_MOVING_3D_CONTACT_PARALLEL_NEW_01"
```

Output: exclusively new directory, `REPORT.json` and
SHA `MANIFEST.json`; full per-contact details in the
report, compact diagnostic summary on stdout.

No FAIR source execution can be claimed until the
operator returns its actual results. A result marked
`PASS_SOURCE_MOVING_3D_CONTACT_GEOMETRY_DIAGNOSTIC`
only passes **geometry-reconstruction checks**;
`3D_geometric_no_penetration_proved` and
`current_3D_contact_law_reaction_enforced`
remain **false** even if no negative point gaps
are observed.

## Further work

If source and 3D diagnostic + parallel parity PASS,
prioritize an **updated-geometry KKT contact law** in
Cartesian frame with properly defined signed edge/face
gap, consistent normal derivative, contact point choice,
and pairwise force/torque balance. First regional
5–8/11, then 12-plate global. Require dt/restart,
fixed-geographic-extent mesh refinement and
independent force/energy tests.

Do not authorize geological production, HistoryStore
updates, mineral/resource evolution or physical T1
without actual G2 constitutive data, G3 load closure
and G4 transport providers.

```text
PREVIOUS_FIXED_T0_NORMAL_KKT_FAIR=PASS_36_36
NEW_MOVING_3D_GEOMETRY_SOURCE_RUN=PENDING
REGIONAL_PARALLEL_SERIAL_NUMERICAL_PARITY=PENDING
TRUE_MOVING_3D_SURFACE_CONTACT_COMPLEMENTARITY=OPEN
GLOBAL_PHYSICAL_T1=null
D_024=ACTIVE
```
