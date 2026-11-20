# ARCANA R6 — Global genuine sparse P1 G2 static parity gate

**Date:** 2026-11-20. **Branch:** r6/multiphysics-integration-20261026.
**Input context:** FAIR operator-proven 39/39 regional manufactured G1↔G2
100/1000y and 20/20 robustness/global graph-scale experiments.
**Decision:** GO for source-preserving global **static** sparse *manufactured*
spherical P1 element test, only; physical geology remains NO-GO.

## What this step actually implements

New:
- `experiments/plate58_deforming_explore_v1/g2_global_sparse_p1_static.py`
- `tests/test_r6_g2_global_sparse_p1_static.py` (9 source-free test functions)

The earlier sparse **graph Laplacian** is *not* the real G2
membrane; this is a distinct bridge that assembles the
**actual existing `spherical_element_tangent` 6×6 P1 operator**
into a SciPy COO/CSR global matrix rather than allocating a
132,870² dense matrix.

### Gate A — regional exact-source dense/sparse parity

Read the previous FAIR SHA-verified 8×8 / 16×16 T0 FEG and 51-field
regional PRE binding. Reconstruct precisely the earlier synthetic
`eta_h = eta_crust * h_crust + eta_mantle * h_mantle`
and `lambda_h = eta_h`, where `eta_crust=1e20 Pa·s` and
`eta_mantle=1e21 Pa·s` are **manufactured hypotheses**.
Call the *same* P1 element function both through the old dense
`assemble_spherical_exterior` and the new sparse assembly.

Compare on authentic:
- **8×8** original region, 81 nodes, 128 triangles, 162 EN DOFs.
- **16×16** original *larger* region, 289 nodes, 512 triangles,
  578 EN DOFs, 5:8:11 triple source included.

Acceptance: relative `||K_sparse x - K_dense x||/||K_dense x||`,
relative largest entry error, and virtual-work symmetry
`|xᵀKy - yᵀKx|/(|xᵀKy|+|yᵀKx|)` all
**< 5×10⁻¹²**.
This is operator representation parity, **not spatial mesh
convergence** (regions have different geographic extents).

### Gate B — global P1 source assembly

Use `source_inputs(ROOT)` and `build_views(mesh)`
to load the genuine canonical 210 Ma T0 mesh and
first-segment Euler plate inputs: **64,442 global parent nodes**,
**128,880 source triangles**, **12 plates**.

The **66,435 plate-local material views** are independently stored
at shared parent-node locations; they yield **132,870 EN DOFs**.
No global welded-node mapping or arbitrary average of Euler
velocities is performed. The assembler *explicitly checks*
that **no nonzero matrix entry connects DOFs belonging to
different plate views**.

For each source triangle, evaluate the **original**
`spherical_element_tangent` on its source coordinates and use
the two original layer thicknesses from the **actual 51-field
source PRE**. Materials remain constructed / unratified;
mechanical LAB, fluids and real friction remain absent.

Report:
- Actual CSR nonzeros and storage bytes.
- Maximum matrix antisymmetry.
- Piecewise-facet vs geodesic source-area discrepancy.
- Whole-world source SHA/pins and after-run source immutability.
- Peak process memory and wall times for parity, global assembly
  and one static solve.

This is a true global **synthetic P1 membrane tangent**, unlike the
earlier graph operator. It is still **not a global physical T1 solver**.

### Gate C — global manufactured static response

Define `C=0.5*mean(diag(K)) I` and solve the normalized static
SPD system

```text
(I + K/C) v = g_test
```

with SciPy CG and diagonal Jacobi preconditioning (`rtol=1e-8`,
`maxiter=1200`), recording true residual and reciprocal-work
identity. The test target is **original source Euler tangential
velocity plus a small explicitly constructed nonrigid field**,
so the tangent's response is measurable. No G3 or GPE forces
are used.

The genuine Euler-only velocity field on independent plate
views must act as a **P1 membrane rigid rotation null mode**:
require small `||K v_Euler||/(max(diag(K))*||v_Euler||)<1e-9`.
An invented nonrigid source test must produce nonzero `Kx`,
and the solver's residual and work identity must each
be < 2e-8.

If global source triangles or contact frames reveal degeneracies,
a lack of balance, nonconvergence, or a numerical scaling
failure, **stop with the observed error and investigate**;
do not bypass material guards, alter source geometry, loosen
tolerances, or reinterpret the sparse graph as a pass.

**This one static solve is not a 100- or 1000-year global time
integration.** It intentionally precedes that larger task.

## FAIR commands

Use the existing checkout and original sealed evidence folders:

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
  tests/test_r6_g2_global_sparse_p1_static.py \
  tests/test_r6_g3_spherical_exterior.py \
  tests/test_r6_g1_g2_manufactured_feedback.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -d "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01"
test -d "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01"

python -m experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --output "$BASE/G2_GLOBAL_SPARSE_P1_STATIC_NEW_01"
```

Output is an **exclusive new** source-SHA-linked `REPORT.json`
and `MANIFEST.json`. The source is unchanged. If a previously
recorded evidence folder is unavailable at the quoted path,
inspect the original path; do not synthesize old evidence.

The report's global manufactured result must be read
**alongside** the source scope: 66,435 separate views,
no mechanical fault coupling. There may be nearly zero
correction to a perfect plate-rigid Euler field until a
genuine nonrigid/contact forcing or kinematic compatibility
constraint is introduced. This is expected rather than
evidence that the tangent is inert.

## After numerical PASS

Only after authentic global P1 static parity and measured
memory/convergence are accepted, design:
1. A contact law matrix with **explicitly different choices**
   (unwelded, synthetic welded, synthetic sliding/open) and
   a shared-DOF/constraint ownership registry.
2. Genuine global-engineering **100 and 1000 model years**
   of the constructed (not source-calibrated) law with
   restart, dt convergence, remeshing/area/energy checks.
3. Fixed geographic extent mesh refinement and
   independent virtual-work / frame rotation/objectivity tests.
4. Independently source/ratify G2 mineralogy, stress–rate–P/T–water
   flow laws, physical LAB and G3 mantle/exterior/basal
   forces before any physical global `T1` or WorldSim
   resource-history update.

```text
PREVIOUS_REGIONAL_ROBUSTNESS_FAIR=PASS_20_20
PREVIOUS_GLOBAL_SPARSE_GRAPH_FAIR=PASS
NEW_REAL_SPHERICAL_P1_SPARSE_PARITY_FAIR=PENDING
NEW_SOURCE_GLOBAL_STATIC_SPHERICAL_P1_FAIR=PENDING
GLOBAL_100_1000_ENGINEERING_TIME_INTEGRATION=NOT_RUN
PHYSICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
```
