# ARCANA R6 — G2/G3 A nonlinear source-data binding after FAIR 11/11

2026-11-19 FAIR operator report:
```text
git HEAD ace05ffa5afd70425f0db042939707848588e557
python -m pytest -q tests/test_r6_g2_g3_nonlinear_layered.py
........... [100%] 11 passed in 0.16s
```

This establishes the **synthetic** depth-integrated nonlinear constitutive potential / gradient / exact tangent and spherical-facet G3 A source-keyed engineering assembly. It does not qualify a physically sourced ARCANA creep law or a mechanical solve.

## New substantive G2 source binding to G3 faceted triangles

The actual canonical PRE metadata `R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json` has **51 fields**, including explicit present flags, crust and mantle material-configuration codes, piecewise thermal polynomials and parent node IDs. Absent quantities are serialized as finite zero with a present flag, not inferred from their numeric value. In the previous FAIR G3 A multiscale step, the unmodified 64,442-node source PRE was copied into 81 and 289 original-parent-ID regional records. The previous 8x8 and 16x16 source geometry and spherical audits are already PASS.

`g2_nodal_source_bridge.py` now:
- reads the authentic unchanged PRE regional file under verified source SHA, schema, node IDs and field order without inventing missing field values;
- requires source thermal layer geometry and positive layer thickness/density for the **engineering potential's input scope**;
- binds each of the 120/504 exterior source triangles to its 3 **original parent nodes**, their PRE records and source material-configuration codes, tracking mixed-code triangles rather than homogenizing;
- cross-checks all 81 overlapping nodes between 8x8 and 16x16 for exact retained PRE numeric identity;
- preserves the true 5/8/11 triple source junction node **34587** and its PRE record without guessing the material's rheological coefficients;
- outputs one new SHA-manifested `SOURCE_NODAL_ELEMENT_G2.json`, with full node columns and triangle incidence; **G2 material, water, brittle law, G3 loads, basal/GPE and T1 stay null**.

The optional `vertex_quadrature_response()` calculates the arithmetic one-third weighted integral of three separately evaluated nodal G2 candidate responses (potential, stress, tangent) for a given element strain. This is **vertex-sampling quadrature for a future engineering experiment**, not a proven spatially convergent interpolation of heterogeneous nonlinear materials, nor an authorization to evaluate synthetic rheology on the actual 5/8/11 source. Each node's material scenario is required explicitly; no default law.

## Verification

The new focused tests include PRE schema, duplicate/missing IDs, 3-node element ownership, mixed source material configurations, missing candidate refusal and synthetic 1/3 response consistency. **Local 7/7 PASS**; FAIR run on actual PRE is pending.

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# if clean:
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
python -m pytest -q tests/test_r6_g2_nodal_source_bridge.py

MULTISCALE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01
MECHANICAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01
SPHERICAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_SPHERICAL_AUDIT_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01
python -m experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge "$MULTISCALE" "$MECHANICAL" "$SPHERICAL" "$OUTPUT"
```

The operator should inspect exact node counts, mixed material code counts and SHA evidence. If an authentic PRE source has a missing, absent or structurally incompatible thermal column, the correct result is fail-closed and explicit inspection, NOT replacing it with an arbitrary profile.

This code closes the SOURCE DATA wiring only. **Next scientifically substantial work** is selecting empirically defensible layer materials with bounds, Biot/pore-water and brittle law, and constructing G3 A external/basal force balance with GPE nonduplication. No further geometry-only expansion or unconstrained kinetic timelines. D-024 still blocks mechanics and T1.
