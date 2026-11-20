# ARCANA R6 — Global P1 manufactured 100/1000 model-year sparse time integration gate

**2026-11-20.** Previous FAIR static global P1 gate: **28/28 PASS**
at source HEAD `313b2f40ed7066cbd1b424b7237551d4d2b39d78`.
It was documented on GitHub under the later operator-receipt commit
`778c6ce9df55588534a6ffe206be4f47d39372a7`.

**Decision:** `ENGINEERING_ONLY_GLOBAL_100_1000Y_FIXED_SOURCE_T0_P1_TEST_ALLOWED__NO_PHYSICAL_T1`.
Do **not** interpret the next PASS as geological time evolution.

## Model and source restrictions

The new driver is
`experiments/plate58_deforming_explore_v1/g2_global_sparse_p1_time.py`.
It requires as input the earlier independently SHA-bound source
`G2_GLOBAL_SPARSE_P1_STATIC_NEW_01` report and manifest, and
checks original source SHA, reported `cg_info=0`, original
`132870` East/North DOFs, original P1 CSR nonzero count,
source mesh identity and `D_024=ACTIVE`.

It builds the same *actual implemented* spherical-facet P1 sparse
tangent `K` from **12 source plates, 66,435 plate-local views,
128,880 triangles** and the original T0 PRE thickness columns.
`K` is physically **unratified**: the two viscosity coefficients
were invented for the regional engineering test; no real G2
temperature-dependent viscosity, hydrology, friction or
mantle-exterior traction is available.

**Plate contact policy = UNWELDED / independent plate-local views.**
The genuine source plate-Euler target field `g_Euler` lies nearly
in the rigid null space of the P1 membrane; a small explicitly
synthetic nonrigid field is added to make a measurable response.
The target is constant in a fixed reference frame attached to the
original source material. This is a **linearized frozen-T0 tangent
approximation**, not a numerically exact Euler-rotating
nonlinear geometry: the geometry and stiffness are not recomputed
at every year. No nonphysical contact weld or averaged Euler
Dirichlet velocities are applied.

The manufacturing equation in velocity form, with
`L=K/C`, `C = 0.5 mean(diag(K)) I` and `tau=200 model years`, is:

```text
g = v + L (v + u_next/tau)
u_next = u_old + dt v

(I + (1 + dt/tau) L) v_new = g - L u_old/tau
```

Velocities are metres/model year and displacement is metres.
The time formulation and `C` scaling are **engineering-only**
not a calibrated global constitutive model or G3 forcing.
The meaning of the frame is fixed by the T0 source
node East/North basis; a real moving mesh needs an objective
corotational update, new geometry and contact laws.

## What FAIR must verify

Use **1-, 5- and 10-year** implicit steps, each integrated to
model year **1000**, with checkpoints at **100,500,1000**.
Re-run from the 500-year 1-year-step checkpoint to year 1000.
This is an explicit source-global engineering test; unlike the
preceding static P1 pass, it actually performs temporal updates.

For each step:
- conjugate gradient with diagonal Jacobi preconditioner,
  warm-start from the previous step, and full normalized equation
  residual `<2e-7`;
- numerical backward-Euler discrete energy/work identity
  (including nonnegative algorithmic dissipation term),
  `<2e-7`;
- all vectors finite, re-used same fixed K and genuine
  source T0 parent-node/plate view ownership.

At 100 and 1000 model years:
- compare maximum nodal EN displacement, RMS velocities and
  G1-vs-coupled feedback;
- compute **max per-component** dt5-vs-dt1 and dt10-vs-dt1
  displacement differences; demand dt5 error not exceed dt10
  (allow 1e-8m numerical slack), and dt10 error relative to
  max displacement below 2.5%;
- compute oriented spherical-triangle area ratios on **all
  original independent plate-local triangles** from perturbed
  material positions; reject negative triangles or >2% area drift;
- require 500+500 restart max displacement difference <1e-8m;
- report total CG iterations, max per-step iterations, peak
  relative residual, energy error, CSR bytes and full wall time.

Real G4 material/energy transport is NOT present: area ratio
audit is not mass conservation. Similarly this is not actual
global physical shell finite strain, dynamic tectonic contact
opening/slip or pressure/thermal fields.

For the original global plate-Euler rigid target alone, the
frozen source membrane gives **K g_Euler≈0**. Thus most large-scale
rigid motion remains unchanged: the manufactured feedback
chiefly affects the added nonrigid field. A small global
velocity correction is expected and cannot be interpreted as
weak tectonic coupling in the real world.

The new test file
`tests/test_r6_g2_global_sparse_p1_time.py` defines nine
source-free checks: zero stiffness parity with G1, nonrigid
work/feedback, 500+500 deterministic restart,
independent scalar analytical order using
dt=1,0.5,0.25y, rigid null response and invalid inputs.

## FAIR operator command — pending source execution

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
  tests/test_r6_g2_global_sparse_p1_time.py \
  tests/test_r6_g2_global_sparse_p1_static.py \
  tests/test_r6_g1_g2_manufactured_feedback.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -d "$BASE/G2_GLOBAL_SPARSE_P1_STATIC_NEW_01"

python -m experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_time \
  --static "$BASE/G2_GLOBAL_SPARSE_P1_STATIC_NEW_01" \
  --output "$BASE/G2_GLOBAL_SPARSE_P1_TIME_100_1000Y_NEW_01"
```

The source output path must be a **new exclusive** directory.
A failed time-step, source SHA mismatch, physical source mismatch,
work/area gate or CG nonconvergence must stop; do not automatically
relax tolerances or substitute a synthetic physical G3 force.

**Source status at publication:** code exists in repository;
new FAIR 100/1000-year full-global experiment and all tests are
PENDING, not claimed PASS.

## Next physics and engineering gates

If this source-engineering time integration passes, compare
contact representations (plate-local split, artificially
welded and independent synthetic slip/open) and objectively
update tangent/geometry in rotating material frames.
Then test fixed-geographic-extent mesh refinement and
measure step-size convergence. All T0 source material
properties, actual mechanical LAB, natural G3 mantle loads
and G4 heat/mass and event physics still need independently
authorized source providers before a true T1 can be built.

```text
GLOBAL_SPARSE_P1_STATIC=PASS_FAIR_28_OF_28
GLOBAL_MANUFACTURED_P1_100_1000Y=CODE_PUBLISHED_FAIR_PENDING
REAL_GLOBAL_FAULT_CONTACT=NOT_QUALIFIED
REAL_G2_G3_CONSTITUTIVE_AND_FORCE_PROVIDERS=NOT_QUALIFIED
D_024=ACTIVE
physical_T1=null
```
