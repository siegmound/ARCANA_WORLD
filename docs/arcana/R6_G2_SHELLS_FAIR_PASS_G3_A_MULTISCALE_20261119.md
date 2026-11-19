# ARCANA R6 — FAIR G2/SHELLS bridge PASS and G3 A multiscale exterior source continuation

**2026-11-19.** Independent operator reported on FAIR:
```text
commit: 214f31402f99f1f1ed50395b77bbdb04cfcd5570
python -m pytest -q tests/test_r6_shells_lr_creep_bridge.py
......... [100%]
9 passed in 0.10s
```
PASS proves the synthetic coefficient translation and source-convention guard. It does **not** establish ARCANA rheology or verify any G2 real-PRE scenario. The FAIR terminal report is operator-provided; no raw FAIR artifacts copied to GitHub.

## Important new source finding: shared eCreep is deeper than LR file formatting

`external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90` stores `LR_set_eCreep(0:LRn)`, one exponent per LR. In `MOD_Shells.f90` the shared exponent affects **multiple independent computational pathways**, not just `Diamnd`:
- `Diamnd` (around line 2348) computes `visInf = 0.5*aCreep*(2*sqrt(secInv))**(eCreep-1)`.
- `Mohr` (around lines 6138,6243,6247) uses `t_eCreep` for crust *and* mantle creep during fault-strength integration.
- `OneBar` (around lines 6510–6574) uses a common `ecini=-1/t_eCreep`, accumulates a depth integral of terms and finishes with `glue=1/v**t_eCreep`, i.e. the **same exponent factors the entire column**.
- Other constitutive calculations use the scalar LR exponent and nonlinear velocity powers; the scalar-to-pair change cannot be considered a valid local substitution.

This is an **architectural solver constraint**. A patch that simply widens `eCreep` to two elements could break the meaning of `glue`, fault traction and nonlinear tangent. No change to the original ShellSet source or authorial choice has been made. An EXPLORE-only dual-exponent solver must either replace the whole-column effective law with mathematically justified rate-dependent response and derivative, or demonstrate a calibrated bounded-error common-exponent representation. Physical rock laws, water, caps and friction remain unknown.

## Substantial G3 A step implemented: outer continuum extensions from authentic T0

New `experiments/plate58_deforming_explore_v1/continuation_A.py` reads SHA-bound T0 face partition, FEG and PRE and joins the prior FAIR stage, 16-cell halo and G2/G3 coupling. It generates **nested actual parent-cell meshes**:
- 8x8 cells: expected 81 source vertices, 128 original triangles;
- 16x16 cells: expected 289 vertices, 512 original triangles;
- Original core 2x2 and halo 4x4 remain embedded and source-ID aligned;
- All source contact edges are checked against canonical `R6BND-T0-...` identities. The outer cuts are represented as open, unprescribed boundaries; it reports each cut edge's adjacent plate and all multi-plate corner node ambiguities.
- Passive PRE projection is an **exact record selection** from the canonical 64,442-node package; no thermal material evolution is invented. New outputs carry parent triangle IDs, plate ownership, FEG roundtrip, original SHA manifest.

The additional extents are **domain-size probes**, not proven physically sufficient or spatially resolved. They do not implement a G3 constitutive tangent, force transfer, N/S reactions, basal support, convergence of physical deformation, or a T1. G3 A architecture ratification remains in force, D-024 unaffected.

## FAIR verification, isolated checkout only

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# If clean:
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
python -m pytest -q tests/test_r6_g3_A_multiscale_source_continuation.py

STAGE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
HALO=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_NEIGHBOR_16_NEW_01
COUPLING=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_G3_A_COUPLING_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01
python -m experiments.plate58_deforming_explore_v1.continuation_A "$STAGE" "$HALO" "$COUPLING" "$OUTPUT"
```
The output must be a **new exclusive** FAIR evidence directory. Existing verified inputs are never modified.

### Decision state
```text
G2_SHELLS_CREEP_BRIDGE_SYNTHETIC_TESTS=FAIR_PASS_9_OF_9
G3_A_MULTISCALE_SOURCE_CONTINUATION=CODE_PUBLISHED__FAIR_PENDING
G3_A_MATERIAL_TANGENT_AND_LOAD=UNRESOLVED
G3_A_NORTH_SOUTH_AND_BASAL_BC=UNRESOLVED
G2_AUTHOR_RATIFIED_FULL_COLUMN_MATERIAL=UNRESOLVED
SHELLS_DUAL_EXPONENT_FORK=NOT_AUTHORIZED_OR_IMPLEMENTED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_T1=null
```
Next work following FAIR geometry/source confirmation: choose a credible G2 material scenario including water/effective pressure and integrate its *tensor-consistent* nonlinear behavior into an experimentally isolated solver implementation; determine the G3 outer/basal physical forcing and test force/work balance. Do not silently promote source-correctness to physical closure.
