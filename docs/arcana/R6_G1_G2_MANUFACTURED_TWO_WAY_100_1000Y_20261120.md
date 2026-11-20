# ARCANA R6 — G1 <-> G2 manufactured regional feedback test (100 and 1000 years)

Date: 2026-11-20. Parent source:
`3a9f1cd7346161b450aa3998e3823f31ff4abc82`.
Decision: `AUTHORIZE_BOUNDED_NONCANONICAL_MANUFACTURED_ENGINEERING_TEST_ONLY`.
**This is not a physical deformation simulation or geological forecast.**

## What changed relative to the FAIR G1 -> G2 passive PASS

The operator's last FAIR receipt confirmed G1->G2 source-only 32/32 PASS:
64,442/64,442 global PRE T0 columns and 66,435 original plate-local
material views, with max within-plate relative edge error
3.438e-13 (100y) and 3.127e-12 (1000y). G2 stresses were absent
in that audit.

Now run a **distinct synthetic, source-geometry-bound mechanical test**:
- Read and SHA-check the existing **G1->G2 PASS** source receipt,
  **G3 A 8×8 / 16×16 genuine T0 FEG** and **G2 nodal source binding**.
- For all original nodes/triangles, the existing `spherical_exterior`
  P1 tangent builds a manufactured linear viscous membrane. Only authentic
  **PRE layer thicknesses** modulate the operator geometrically:
  `eta_h = eta_crust * h_crust + eta_mantle * h_mantle`.
- **Invented** viscosity parameters:
  `eta_crust = 1e20 Pa s`,
  `eta_mantle = 1e21 Pa s`;
  `lambda_h = eta_h`. No real lithology, pore pressure or
  dry/wet condition is inferred; no cold-crust lab law is applied.
- Add invented Kelvin–Voigt elastic memory with
  `tau = 200 model years`, plus an explicit manufactured velocity
  drive/dashpot `C = 0.5 * mean(diag(K)) * I`.
- G1 supplies Euler angular velocities and the same source parent IDs.
  At shared 5:8:11 nodes, **one pair of EN mechanical DOFs** is used.
  In this engineering-only fixture, competing plate target velocities
  are **averaged by incident-triangle count**; this is not a physical
  fault/contact solution and must never be adopted as the real law.

The artificial implicit model in yearly velocity units is

```text
C (v_G1 - v) = K v + (K/tau) u_next
u_next = u + dt_years * v
```

K and C have units N s/m, v is in metres per model year,
u in metres; when interpreting forces in N, divide the velocity
and displacement/tau terms by seconds per year. This is a
manufactured mechanical damping/elastic-reaction problem.
The physical G3 *far-field/basal normal and shear* force provider
remains null. **Original G1 Euler inputs and PRE files stay immutable.**

## Comparisons and acceptance

- Two genuine nested domains:
  8×8 → **81 source nodes / 128 source triangles**;
  16×16 → **289 nodes / 512 triangles**, including real parent
  triple-junction node `34587`. Different extents do **not** alone
  establish mesh convergence.
- Integrate from **0 to 100 and 1000 model years**, with
  **1, 5, 10-year** numerical steps on the same static T0 source
  geometry. Report corrected vs G1 driving velocities, total displacement,
  and the 5y/10y vs 1y displacement deviation.
- Check manufactured internal/dashpot **force residual** (relative
  < 1e-9), scalar **backward-Euler energy / virtual-work identity**
  (< 1e-8), positive semidefinite tangent, and **500+500**
  restart deviation (< 1e-8 m modal).
- Construct perturbed positions `xyz + EN*u` and reject inverted
  triangles or excessive area Jacobian (>5% change).
- Quantify a **Lagrangian manufactured mass bookkeeping** rule
  `h_new = h_T0/J_area`, which preserves a mass proxy. It is not
  qualified G4 thermal/material advection or a real mass solve.
- Report actual numerical engineering steps. Separately keep
  `physical_solver_runs = 0`, `physical_T1 = null`,
  `mechanical_solve_authorized = false`.

## Verification scope

Pure mathematical synthetic cases cover nonzero elastic/viscous
feedback; zero G2 stiffness reproducing G1 drive; 500+500 restart;
coarser time steps; unique junction DOF owner; absent source
ownership; invalid and nonsymmetric tangent; nonfinite restart;
invalid dt; Euler target convention.

**The new source-region execution has NOT been performed on FAIR
in this publication. Do not claim full test PASS yet.**
Local preliminary manufactured kernel checks passed 5/5 in an
isolated Python environment. Those checks are not full FAIR source
tests.

## FAIR clean checkout and test commands

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
  tests/test_r6_g1_g2_manufactured_feedback.py \
  tests/test_r6_g1_g2_passive_100_1000y.py \
  tests/test_r6_g2_g3_nonlinear_layered.py \
  tests/test_r6_g3_spherical_exterior.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6

python -m experiments.plate58_deforming_explore_v1.g1_g2_manufactured_feedback \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --g1-audit "$BASE/G1_G2_PASSIVE_100_1000Y_NEW_01" \
  --output "$BASE/G1_G2_MANUFACTURED_FEEDBACK_100_1000Y_NEW_01"
```

The three input paths are the prior FAIR evidence names in project docs.
If any source evidence folder does not exist on FAIR, **stop and inspect
the actual previously sealed path**, never fabricate upstream receipts.
The output path is **exclusive** and must not exist.

Operator should return the HEAD, pytest summary, and source-run JSON:
both scales, errors at years 100/1000, 5y/10y refinement and
relative force/energy residuals. A failed numerical gate is a
diagnostic to investigate, **not** permission to relax thresholds
or assign arbitrary source rock properties.

## Hard safety/authority separation

This test gives a first **two-way mathematical response** of
manufactured G2 membrane stress to G1 Euler forcing and its own
displacement memory. It DOES NOT implement real constitutive
failure, fault opening/shear, nonlinear full-temperature creep,
real G3 outer/basal traction, planet pressure/isostasy, true G4
advection, or true local deforming Earth/ARCANA time advancement.
Using the fixed initial tangent over 1000y is a small-displacement
linearization, checked only against its diagnostic area Jacobian.

```text
G1_G2_PASSIVE_FAIR_100_1000=PASS_32_OF_32
G1_G2_MANUFACTURED_FEEDBACK_SOURCE_RUN=PENDING_FAIR
G2_TRUE_CREEP_AND_FRICTION_CALIBRATION=OPEN
G3_REAL_BOUNDARY_BASAL_AND_GPE=OPEN
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_T1=null
D_024=ACTIVE
```
