# ARCANA R6 — FAIR PASS G3 A 8×8 / 16×16 and three-plate-aware exterior interface

**2026-11-19**. FAIR operator-reported terminal (raw filesystem artifacts not accessed in this GitHub update):

```text
git HEAD: 0d908e0870a7d05ecae1bb89338abf6522fe4ae7
tests/test_r6_g3_A_multiscale_source_continuation.py: 5 passed in 0.17s
status: PASS_G3_A_MULTISCALE_SOURCE_CONTINUATION__BC_AND_G2_UNRESOLVED
8x8:  81 source nodes, 128 triangles, plates [5,8],    12 contact edges,
      north cut ambiguous nodes 1, south cut ambiguous nodes 1
16x16: 289 source nodes, 512 triangles, plates [5,8,11], 36 contact edges,
      north cut ambiguous nodes 1, south cut ambiguous nodes 2
mechanical_solve_authorized: false
solver_runs: 0
physical_T1: null
```

Source output FAIR (operator path): `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01`.

## Interpretation for physical mechanics (D-024)

- **Third plate 11 is genuinely present** in the 16×16 original T0 source continuation. It cannot be silently discarded in a physical far-field mechanical model.
- **Do not infer a triple junction solely because three plates occur inside the regional domain**; the exact paired-boundary graph and the nodes with three incident plate owners must be computed from source mesh, not guessed.
- North/south ambiguous cut vertices persist and increase to two on the south for 16×16. Euler vectors remain kinematic priors, **not multiple Dirichlet constraints on one DOF**. Unknown G3 normal, tangential and basal conditions remain null.
- The 8×8 domain with only plates 5/8 is a smaller controlled experiment candidate; 16×16 gives a more complex three-plate sensitivity domain, NOT necessarily superior physical BC or convergence.
- Neither domain has demonstrated mechanical extent/mesh convergence or physical 100km accommodation. The nested domains are source-connected numerical surfaces, not a valid stress/force result.

## New executable component: external Schur transfer source partition for both extents

`experiments/plate58_deforming_explore_v1/g3_multiscale_interface.py` validates the previous multiscale and coupling evidence with SHA, replays original FEG triangles and global parent IDs, and partitions the **identical core eight perimeter nodes** from every exterior.

The operator excludes the single core center and eight core triangles, conserves all contact-pair edge counts, identifies actual three-plus-plate junction node IDs, audits every external cut and rejects any invented outer displacement or traction. It provides **mechanical DOF order** to any future real finite-element tangent and load provider:
- 8×8 exterior: 80 unique mechanical nodes, 160 tangent DOFs; 16 interface DOFs and 144 exterior-only DOFs; 120 exterior triangles.
- 16×16 exterior: 288 unique nodes, 576 tangent DOFs; 16 interface DOFs and 560 exterior-only DOFs; 504 exterior triangles.

The existing `coupling_A.condense_exterior_tangent` accepts an **already assembled physically closed** tangent/load using those interface DOF positions, once G2 and far-field/base G3 have been validated. It does not assemble a constitutive law or prescribe a plate 11 boundary velocity now. `K` and `f` remain `null`. These counts are indexed source topologies, not newly run mechanical systems.

The true graph contact pairs and 3+-plate junction counts will be visible in FAIR output; **no unsupported guess of which pair or junction exists** is made.

## FAIR single verification

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# STOP if dirty, else:
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
python -m pytest -q tests/test_r6_g3_multiscale_mechanical_interface.py

MULTISCALE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01
COUPLING=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_G3_A_COUPLING_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01
python -m experiments.plate58_deforming_explore_v1.g3_multiscale_interface "$MULTISCALE" "$COUPLING" "$OUTPUT"
```

Expected diagnostic status: `PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED`. No real G2 material, basin force, assembled K/f, ShellSet solver or T1 is authorized.

## Next physical step (no further geometry-only loops)

After this source graph/DOF validation, prioritise **actual G2 material scenario selection and tensor-consistent nonlinear SHELLS implementation** with explicitly source-supported water/P_eff/friction/slope and validity across T0; then **G3 A true mechanical tangent/load assembly and GPE/basal balance** with 5,8,11 included for 16x16. Matrix rank/gauge, force/work conservation and domain-size sensitivity are meaningful only with justified physical boundary providers. The original single-`eCreep` SHELLS code must not be silently patched to two exponents because it affects OneBar, Diamnd, Mohr and other nonlinear paths.
