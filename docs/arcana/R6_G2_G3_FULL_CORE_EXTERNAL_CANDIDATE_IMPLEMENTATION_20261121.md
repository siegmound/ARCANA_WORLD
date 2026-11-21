# R6 — Full source core+exterior G3 external-channel implementation (candidate-only)

Date: 2026-11-21. Parent: `85a6ba7e4d5dfdde0de2eb0ca716d3670472fbef`. Development branch: `r6/g2g3-core-external-complete-candidate-20261121`.
Status: **SOURCE IMPLEMENTED — FAIR PENDING. NO PHYSICAL SOLVE.**

## Substantive intervention

The previous source-original G2/G3 stitch genuinely assembled internal forces over all original 81/289 parent nodes and 128/512 triangles, but the external known inventory stopped at the 120/504 exterior basal facets and exterior GPE. This intervention adds an optional **source-original core basal/GPE channel** to that existing runner:

- Requires one explicitly source-keyed P1 tangential traction in Pa for **each of the eight original source core triangles**, exact unchanged original parent triangle IDs and connectivity; no zeros inserted.
- Requires a source-identified East/North nodal GPE **increment attributable only to those eight core triangles**, for all 9 core parent nodes (8 shared interface and 1 core-only). Never aliases the original exterior GPE.
- Reuses existing `g3_force_budget.assemble_explicit_g3_loads` (P1 quadrature, dimensions, source tangency, force/torque computations) on original **all** basal triangles and on exterior only; verifies the exterior reconstruction exactly agrees with the previously tested `integrate_coupled_candidate` load vector.
- Reuses existing source FEG/PRE/force chain and 81/289 original parent DOF order; sums full load once per original parent EN DOF. Does not invent a third slip DOF at original triple parent 34587.
- Leaves original `known_PARTIAL_residual_N_NOT_EQUILIBRIUM` unchanged and adds separately named `candidate_FULL_CHANNEL_residual_N_NOT_EQUILIBRIUM` when and only when both new core channels are explicit; calculates each force partition, torque, and virtual power.
- The source runner remains backward compatible in its **partial** mode. A one-channel-only submission must fail closed, not silently set the other to zero. No values are auto-generated and no source evidence is modified.

### Source dimensions

| Region | Source parent nodes | EN DOFs | Core basal facets | Exterior basal facets | Total required basal facets | Exterior cut edges |
|---|---:|---:|---:|---:|---:|---:|
| 8x8 | 81 | 162 | 8 | 120 | 128 | 32 |
| 16x16 | 289 | 578 | 8 | 504 | 512 | 64 |

The full source-referenced **inventory** does not create physical traction values. Core normal pressure is **not** resolved by a tangential shear input; deep mantle velocities/traction law, mechanical LAB, GPE physical vertical reference, low-T materials and fault transmission law remain absent. Material chemistry and water state are not inferred from PRE thermal configuration codes. A continuous shared-DOF shell has **no independent jump/slip mechanism** across the interface.

## Runtime contract and evidence semantics

Optional candidate input keys added to `G2_G3_EXPLICIT_FULL_PARENT_ENGINEERING_INPUT_TEMPLATE_V1.json`:
- `core_basal_tractions_by_triangle` keyed by the eight source original parent triangle IDs, each carrying the existing G3 `parent_triangle_id`, `parent_node_ids`, `force_channel=BASAL_TANGENTIAL`, `authority=ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED`, a specific `source_reference`, and three vertex vectors `nodal_xyz_N_per_m2` (tangent in the original R6 source frame).
- `core_gpe_increment_by_parent_node` keyed by all nine source core parent node IDs; each carrying `force_en_N`, `force_channel=CORE_TRIANGLE_GPE_INCREMENT_ONLY`, same engineering authority, `GPE_force_owner=EXPERIMENTAL_EXTERNAL_GPE_ONLY__ORIGINAL_SHELLS_GPE_NOT_COMBINED`, and specific provenance.

When these two objects are omitted or null, only the old *known partial* inventory is returned; when exactly one is populated, the scenario is rejected. A fixture may use explicit zero-valued rows only as a plainly marked synthetic benchmark; they do not become legitimate ARCANA free boundaries.

The new `candidate_complete_external_channels` key in `REPORT.json` indicates **explicit candidate channel completeness** and never physical equilibrium. The source runner still requires explicit 81/289 node material/velocity data, all real exterior source inventories and noncanonical authority flags. The original JSON template remains intentionally not runnable.

## Test plan

Run under the existing FAIR `arcana-r6-linux` isolated checkout after fetching this branch. Execute:
```bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python -m pytest -q \
  tests/test_r6_g2_g3_full_external_candidate.py \
  tests/test_r6_g2_g3_core_exterior_source_runner.py \
  tests/test_r6_g2_g3_source_core_exterior_stitch.py
```
Then run the existing **full G2/G3 regression command** used for the `7002f3a8` 120-test PASS. Do not assert FAIR results prior to actual execution. Only on PASS plus source/manifest audit should this development branch be integrated.

## Physical gate and next required original evidence

No rocks, water state, real creep law, mantle traction or fault friction are calibrated in this task. The physical G2/G3/FAULT solve still requires one authorially selected regional scenario with data-valid lithology/rheology, effective pressure, **core+exterior** basal normal and tangential source, outer-cut traction, global GPE ownership, and a genuinely discontinuous fault/triple law. Reject a full physical T1 until that separate coupled scenario is ratified and validated.

**`D-024=ACTIVE`; `MECHANICAL_SOLVE_AUTHORIZED=false`; `physical_T1=null`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.**
