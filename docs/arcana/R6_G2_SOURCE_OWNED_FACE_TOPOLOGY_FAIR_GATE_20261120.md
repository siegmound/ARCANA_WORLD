# ARCANA R6 — Source-owned adjacent triangle/facet topology and orientation audit

**Date:** 2026-11-20  
**State:** NEW ENGINEERING_ONLY test and driver, source FAIR **PENDING**.  
**Grounded prerequisite:** full original-edge source FAIR `REPORT.json` SHA256 `e7b8f9c47bcd9f46a35f9edb06ee52ba641747f006482a1efc766f25b5b1fc21`. The 8×8 region has 12 and the 16×16 has 36 authentic source edges; **all remain AMBIGUOUS at T0/100/500/1000**, zero engineering and physical contacts. There are 8 changes in the ambiguity REASON at 16×16 (zero classification switches).

## Scope and scientific limit

Source-preserving next diagnostic: two **original adjacent plate-owned P1 surface triangles** for each authentic R6BND-T0 boundary edge, with no made-up faces. The purpose is to test whether the existing 2D shell source triangulation supplies a usable orientation and a local interface topology; this is **not** full 3D rock volume collision, and has no signed solid nonpenetration or KKT. Real PRE crust/lithosphere thickness scalars are not silently interpreted as extruded 3D volume facets. No new G3/G4 geological load or constitutive law.

The driver `experiments/plate58_deforming_explore_v1/g2_source_owned_face_topology.py` rebuilds original source FEG faces and plate owners, source original R6BND IDs, source PRE and plate-local P1 trajectory from authentic KKT/Euler inputs, with SHA validation and prior source-feature REPORT replay at T0/100/500/1000 model years. At every edge it demands exactly one source triangle from each original owning plate. Nonmanifold/missing owners, source SHA drift or replay differences fail closed.

Measurements per original edge and time: original source plate triangle node IDs and their face areas; raw FEG triangle winding (signed with respect to current radial direction, without silently changing winding); pair of source facet normal alignment; inward-to-face co-normal from the edge toward the third vertex of each plate-owned triangle; nearest original paired boundary-edge unsigned distance; SO(3) invariance of area, orientation inner products and distance. Report original triple parent node `34587` at 16×16. The source-edge pair nearest distance must reproduce the already SHA-verified feature FAIR report within `1e-7m`. No inferred rock volume, no signed solid gap, no action-reaction or KKT solver.

**Important:** a surface normal or opposing in-face co-normals only describes the source triangulated sheet orientation. It does **not** give a physically valid separating normal for 3D rock solids; even if all mathematical tests pass the scientific result is an audit with contact physics open.

## FAIR execution

Use a **clean detached checkout pinned to the exact upcoming branch commit**; never run from a dirty or unverified source SHA. Existing evidenced inputs are read-only.

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_source_owned_face_topology.py \
  tests/test_r6_g2_contact_feature_admissibility.py \
  tests/test_r6_g2_t0_normal_segment_jacobian.py \
  tests/test_r6_g2_moving_3d_contact_parallel.py \
  tests/test_r6_g2_regional_unilateral_contact_time.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test ! -e "$BASE/G2_SOURCE_OWNED_FACE_TOPOLOGY_NEW_01"

python -m experiments.plate58_deforming_explore_v1.g2_source_owned_face_topology \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --prior-feature "$BASE/G2_CONTACT_FEATURE_ADMISSIBILITY_NEW_01" \
  --output "$BASE/G2_SOURCE_OWNED_FACE_TOPOLOGY_NEW_01"
```

## Acceptance and stop conditions

- Per-region real source-edge source-owner face inventory must be 12/36 with no fabrication, and existing triple parent 34587 only for 16×16.
- Prior feature FAIR REPORT must exactly match pinned `e7b8f9c47bcd9f46a35f9edb06ee52ba641747f006482a1efc766f25b5b1fc21` and source file pins; each original source edge minimum unsigned distance must replay within `1e-7m`.
- Geometry SO(3) invariance: edge distance absolute error < `1e-7m`, face area relative error < `1e-9`, face/co-normal dot error < `1e-9`. These are **engineered diagnostic numerical tolerances**, not geological source measurements. Reject if fail, do not loosen gates silently.
- If the FEG original face winding differs, record both source signs instead of overriding data. If the source sheet does not carry a closed solid oriented interface, fail **qualification** explicitly (not necessarily the source topological inventory).
- `physical_T1=null`, `D-024=ACTIVE`, `HistoryStore_modified=false`, no KKT, no source world canon change.

**After FAIR PASS:** decide whether a genuinely justified **side-of-plate and solid-boundary geometry** can be built from already authorized FEG/PRE sources; if not, declare a missing source provider/authority for physical contact, rather than adding synthetic thickness extrusion.
