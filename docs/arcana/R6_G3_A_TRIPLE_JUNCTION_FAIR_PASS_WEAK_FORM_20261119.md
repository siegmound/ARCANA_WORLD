# ARCANA R6 — G3 A verified triple junction and first weak-form membrane kernel

**FAIR operator result: 2026-11-19, source checkout `ee4ada4953a2bdce76840483116c62335029bb65`**. The operator reports `7 passed in 0.15s` for `tests/test_r6_g3_multiscale_mechanical_interface.py` and:
```text
status=PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED
8x8: 160 tangential DOF, core interface 8 nodes,
     contact edges 5:8 = 12; 3+-plate junction count 0
16x16: 576 tangential DOF, core interface 8 nodes,
       contact edges 5:8 = 18; 5:11 = 7; 8:11 = 11;
       actual source nodes incident to >=3 plates = 1
physical_tangent=null
mechanical_solve_authorized=false
solver_runs=0
physical_T1=null
```
Raw result and source `MULTISCALE_INTERFACE.json` remain only on FAIR in `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01`. Only the operator's terminal report is visible here, not the actual triple-junction parent node ID. Do not invent that ID. The presence of a single source node incident to 5/8/11 DOES NOT imply an explicitly resolved fault or three separately imposed nodal velocities; the source remains a continuous mesh.

## First mechanical numerical kernel — NOT a G3 closure

New `experiments/plate58_deforming_explore_v1/exterior_variational.py` implements a **P1 planar tangential, linear Newtonian viscous membrane weak form** and a source-parent-triangle-ID assembly function requiring explicit *candidate* integrated viscosities for EVERY triangle. For a 2D velocity field and engineering shear strain rate, at each triangle:
```text
epsilon_dot = B * nodal_velocity
N = D * epsilon_dot
D (Pa s m) = [[lambda_h + 2 eta_h, lambda_h, 0],
              [lambda_h, lambda_h + 2 eta_h, 0],
              [0, 0, eta_h]]
K_element = integral B.T D B dA = A * B.T D B.
```
If `eta_h` and `lambda_h` are depth-integrated effective viscosities in Pa·s·m, `D` has units N·s/m and `K` maps nodal velocity m/s into force N (within the planar 2D continuum approximation). No fictitious G2 viscosity, elastic modulus, strain-rate or boundary loads is supplied by ARCANA. The function refuses absent per-element coefficient coverage, provenance or nonpositive viscosity. It does not compute a body/load vector or perform a mechanical solve.

The planar metric is **azimuthal-equidistant tangent approximation** to the spherical T0 source, *not* ShellSet's covariant surface-strain or complete rheology. Projection distortion on 8×8/16×16 is not yet quantified against true spherical element metrics. No claims of ShellSet tensor parity, real G2 material, 3-plate traction continuity, basal GPE or physical T1. This is a reusable variational operator kernel for eventual explicitly supplied physics, and its outputs MUST NOT be treated as a complete physical model.

Local independent numerical manufactured tests (container): **8 passed in 0.05s**, testing affine energy/virtual work, two translations and one rotation rigid modes (three expected gauge modes), symmetry/rank, depth-integrated coefficient positivity, source triangle material coverage, provenance guards, degenerate triangle rejection and tangent coordinate orientation. These are synthetic, not FAIR results.

## FAIR focused verification

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# STOP if dirty
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
python -m pytest -q tests/test_r6_g3_exterior_variational.py
```

No FAIR real material output expected because valid G2 source-dependent material response `D` and G3 load/basal boundary have NOT yet been supplied. Next genuine physical task: connect a source-supported G2 constitutive tangent with strain-rate, P/T/water and shell tensor conventions (shared eCreep is not yet resolved), then assemble a source-bound exterior G3 A operator and physically admissible force vector on 5/8/11, close far boundaries and basal GPE; only then attempt an explicitly authorized noncanonical experiment, never T1 by default.
