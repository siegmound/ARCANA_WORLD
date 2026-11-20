# ARCANA R6 — Regional robustness sweep and global sparse-scale gate

**Date:** 2026-11-20.
**Parent:** `5337d7a94ee3b787dc3530ea7e09f6237dd6ce78`.
**Decision:** `AUTHORIZE_ENGINEERING_ONLY_ROBUSTNESS_AND_GLOBAL_SPARSE_TOPOLOGY_PROBE__NOT_GLOBAL_PHYSICAL_T1`.

## Why this test

Previous FAIR source-keyed **G1↔G2 manufactured** solver passed
39/39 with 8×8, 16×16 source regions at 100/1000 years; fixed
synthetic viscosities and welded plate contact. This verifies the
particular constructed equations, not their parameter robustness,
mesh convergence, global computation, or geophysics.

Two independent objectives now:

1. **Regional parameter sensitivity on authentic T0 source meshes**:
   check parameter dependence, source immutability and manufactured
   energy/force/area gates at 100 and 1000 model years.
2. **Global 12-plate numerical scaling**:
   exercise real 64,442-node / 128,880-triangle source topology
   through sparse plate-local assembly and one *artificial graph*
   conjugate-gradient solve. This is **not** global P1
   viscoelasticity or 1000-year nonlinear geodynamics.

## Regional scenario matrix — source-identical geometry

New runner:
`experiments/plate58_deforming_explore_v1/g1_g2_robustness_global_sparse_probe.py`.

The existing source-bound region runner is reused unchanged in
geometry/physics, with one **necessary compatibility fix**:
`evolve_modes(..., tau_years=TAU_YEARS)` is now passed explicitly
for the full and 500+500 restart flows. Before this change the
Python default argument captured 200 years at import time and
would NOT have respected a changed `TAU_YEARS` global. The default
200-year baseline remains mathematically the same.

This wrapper runs one case per **exclusive new evidence subdirectory**,
in a single process, with a temporary lexical patch of the four
manufactured scalar constants; originals are always restored and no
real T0 PRE/kinematics or prior FAIR evidence is changed:

| Case | Crosta viscosity | Mantle viscosity | Relaxation | Dashpot ratio |
|---|---:|---:|---:|---:|
| baseline | 1e20 Pa s | 1e21 Pa s | 200 y | 0.5 |
| uniform_viscosity_x10 | 1e21 | 1e22 | 200 | 0.5 |
| crust_viscosity_x10 | 1e21 | 1e21 | 200 | 0.5 |
| mantle_viscosity_x10 | 1e20 | 1e22 | 200 | 0.5 |
| relaxation_half | 1e20 | 1e21 | 100 | 0.5 |
| relaxation_double | 1e20 | 1e21 | 400 | 0.5 |
| drive_dashpot_half | 1e20 | 1e21 | 200 | 0.25 |
| drive_dashpot_double | 1e20 | 1e21 | 200 | 1.0 |

All cases reuse exact 8×8/16×16 source records, preserve manifest
SHA and run the same **1/5/10-year time-step, 100/1000-year
checkpoints and 500+500 restart gates**. Failure of any
existing force/work/area numerical acceptance stops the sweep
without hiding a failed case or changing acceptance tolerances.

**Critical structural non-identifiability:** since
`K = eta_crust*Kc + eta_mantle*Km` and
`C = ratio * mean(diag(K)) * I`, multiplying both
viscosities by ten multiplies K and C equally. The
**kinematic response must remain unchanged**. The runner
fails if the resulting maximum displacement differs from the
baseline by `>= 1e-7 m`. This proves that absolute
viscosity cannot be calibrated from this synthetic test. It
is a model-design diagnostic, not proof that nature has
scale invariance.

## Sub-year time accuracy — independent analytical solution

A separate exactly solvable **two-mode, constant-drive** equation
with eigenvalues 0.2 and 2.0 and tau 200 years is integrated
at dt 1, 0.5 and 0.25 years over 100 years.
The analytical exact displacement is

```text
u(t) = (g * tau / lambda) * (1 - exp[-lambda*t/(tau*(1+lambda))])
```

with positive lambda and constant dimensionless modal drag.
Compare absolute numerical errors and compute effective
first-order estimates from successive halving, accepting
0.85 < observed order < 1.15. This is independent
mathematical code verification; it is **not the source-region
dt<1-year convergence test**. That remains a separate next
scientific/engineering gate if the global probe passes.

## First global-scale sparse experiment

The existing full-world G1 benchmark contains:
- **64,442 distinct parent nodes**
- **128,880 triangles**, **12 Euler plates**
- **66,435 plate-local material views** (separate DOF copies
  at contacts), or **132,870 tangential East/North DOFs**

A global dense symmetric 132,870×132,870 `float64` array
would require ~**131.54 GiB** just for values, excluding
factorizations and extra arrays. Directly applying the
regional dense eigendecomposition is therefore inadmissible.

New global probe reads `source_inputs` and `build_views`
with their original SHA-validated T0 sources, builds a
**sparse plate-local graph Laplacian** from original plate-
owned triangles (no accidental welded graph link between
different plate-local views), then solves one deterministic
manufactured SPD equation `(I+0.05L)x=b` using
`scipy.sparse.linalg.cg` with relative tolerance 1e-9
and at most 500 iterations. Reports CSR nnz/bytes, measured
CG residual and peak process memory. Fails if source count,
geometry, solver convergence or residual mismatches.

The sparse graph **does not represent** the G2 3D
viscoplastic membrane operator, real Euler forcing,
boundary tractions, slip/opening contacts, full Earth
mantle coupling, or global 1000-year G1↔G2 evolution.
This stage closes only the **sparse topology/solver-size
feasibility**; it cannot authorize a real global G2
mechanical solve. Any ensuing full-global prototype should
use **sparse assembled P1 tangent or matrix-free action**,
with physical contact choices and separately measurable
basal/exterior loads, and must prove total error,
memory, force/energy, restart and cost.

## FAIR commands

The following test source is new and FAIR execution is
**pending**. Run on a clean isolated checkout; do not
overwrite prior source evidence or tests:

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
python -c 'import scipy; print("SciPy",scipy.__version__)'

python -m pytest -q \
  tests/test_r6_g1_g2_robustness_global_sparse_probe.py \
  tests/test_r6_g1_g2_manufactured_feedback.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
python -m experiments.plate58_deforming_explore_v1.g1_g2_robustness_global_sparse_probe \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --g1-audit "$BASE/G1_G2_PASSIVE_100_1000Y_NEW_01" \
  --output "$BASE/G1_G2_ROBUSTNESS_GLOBAL_SPARSE_NEW_01"
```

If an input evidence path does not exist on FAIR, stop
and identify its original sealed name; do not fabricate
previously sealed artifacts. The output folder must not exist;
failure may leave an incomplete *new* evidence directory
for debugging and must not be relabeled PASS.

Check original `MANIFEST.json` hashes and return
the final JSON summary, including baseline vs all
parameter variants and the exact global sparse residual.
The global read-only sparse graph is a controlled operation;
it has zero physical solve runs.

## Next gates after this test

1. At fixed physical extent, interpolate the original source
   geometry into a *numerically manufactured* finer mesh,
   preserving plate boundaries and independent contact owner
   identity. Compare common material DOFs and force/work
   at matched scale; do not interpret 8×8/16×16 different
   extents as mesh convergence.
2. Add independent synthetic **contact slide/open alternatives**
   to the single weighted welded mechanical node.
3. Upgrade global matrix-free/sparse graph feasibility to
   a true synthetic **global P1 constitutive tangent and
   time integration**, with 100/1000-year checkpoints,
   honest step count/memory benchmark and G1 Euler geometry.
   Keep all physical material laws and G3 tractions null.
4. Separately qualify authorially accepted rock chemistry,
   water, strain regime, G3 external/basal forces and
   G4 mass/heat transport before any real physical world
   or HistoryStore state is advanced.

```text
REGIONAL_G1_G2_MANUFACTURED_FAIR_BASELINE=PASS_39_39
ROBUSTNESS_SWEEP_FAIR=PENDING
GLOBAL_SPARSE_SOURCE_PROBE_FAIR=PENDING
GLOBAL_G2_PHYSICAL_MECHANICAL_T1=NOT_AUTHORIZED
D_024=ACTIVE
physical_T1=null
```
