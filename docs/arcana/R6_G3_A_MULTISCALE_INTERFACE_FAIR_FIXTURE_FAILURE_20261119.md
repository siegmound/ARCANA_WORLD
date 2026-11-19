# ARCANA R6 — FAIR test failure: G3 A multiscale mechanical interface

**Date:** 2026-11-19. **Authority:** operator-pasted FAIR traceback only; new code not yet retested on FAIR.

Checkout and source:
`a6cc6603b0a909c733035d4546ea0651d12ddf0b`.
Command `python -m pytest -q tests/test_r6_g3_multiscale_mechanical_interface.py` resulted in **5 failed in 0.20s**.

All 5 failures terminate in `toy_region()` → `continuation_A.summarize_region()` before reaching `derive_external_interface()`:
```text
ValueError: G3_A_PARENT_NODE_COUNT_INVALID
reg=summarize_region(width,list(range(1,n*n)),tris,plates,mesh,source)
```

## Root cause and second latent bug
1. The purely synthetic fixture has `n=width+1` gridline vertices per side. `range(1,n*n)` omits the last node (8x8: 80 rather than 81; 16x16: 288 rather than 289). The source geometry legitimately enforces `len(nodes)==(width+1)**2`. Fix `range(1,n*n+1)`.
2. Once the count is fixed, `core_ids` contains a separate **variable-shadowing bug**: `interface=sorted(n for n in nodes if n != 1+center*n+center)`. The comprehension's `n` is the parent node ID, rather than outer `n=width+1`, so the center is not removed (9 interface IDs instead of the eight real perimeter IDs). Fix by evaluating `center_id=1+center*n+center` before the comprehension and using `parent_id!=center_id`. Added a regression test with exact 8+1 core partition for both extents.

**Classification:** test fixture defects; no evidence that the canonical T0 source continuation, 8x8/16x16 FAIR-generated FEG/PRE, or the G3 source integration is invalid. Equally, **the new multiscale mechanical interface is not yet PASS**, because those five tests did not exercise it. No production code change or authorial source/physical law correction is justified by this traceback.

## Corrected verification path (FAIR only)

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# If clean, fetch the new fixed HEAD from branch:
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
```

**Only after test PASS**, run the *already existing* original SHA-bound source data command from `docs/arcana/R6_G3_A_MULTISCALE_FAIR_PASS_INTERFACE_CONTRACT_20261119.md` with exclusive new output folder. Preserve existing `PLATE58_G3_A_OUTER_MULTISCALE_NEW_01` and `PLATE58_G2_G3_A_COUPLING_NEW_01` unchanged.

```text
G3_MULTISCALE_SOURCE_8X8_16X16=PRIOR_FAIR_PASS
G3_MULTISCALE_MECHANICAL_INTERFACE_TESTS=FAIR_FAIL_5_OF_5_AT_OLD_SHA
G3_MULTISCALE_MECHANICAL_INTERFACE_FIXED_CODE=COMMITTED__FAIR_RETEST_PENDING
G2_RHEOLOGY=UNRESOLVED
G3_EXTERNAL_K_AND_F=UNRESOLVED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_T1=null
```
