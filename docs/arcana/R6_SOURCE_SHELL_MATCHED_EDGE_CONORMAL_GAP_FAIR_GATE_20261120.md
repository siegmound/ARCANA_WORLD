# ARCANA R6 — Original plate-shell matched-edge co-normal signed opening diagnostic

**Date:** 2026-11-20. **New source FAIR run pending**. This is a mathematical ENGINEERING_ONLY surface-shell kinematic diagnostic, *not* proof of physical rock-volume nonpenetration or a 3D contact solver.

## Measured preceding gate (FAIR original face topology)

Source commit `d758a542fa207b6ad3a2f777e8d8151b869d75e2`, 74/74 pytest PASS, source FACE driver PASS, report SHA256 in manifest `3e42e1321cfb72f73bd72c82c32030969c908ec112ef5fb1255b9d7a767e4d07`. Per original source-edge face geometry at 0/100/500/1000 years, FAIR operator read-only output:
- region 8×8: 12 authentic R6BND-T0 edges, 13 pair-node links, 24 source face incidences at every checkpoint, 12/12 source p and 12/12 q faces radially outward, all paired interior co-normal dot products NEGATIVE, range near −0.999857 to −0.999848 (same order at all times).
- region 16×16: 36 original edges, 39 pair-node links, 72 source face incidences at every checkpoint, 36/36 p and q raw face windings radially outward, all interior co-normals opposite with dots approx −0.999863 to −0.999848; original triple parent node 34587.
- SO(3) absolute maximum paired boundary distance error <= 1.062787e-9 m (vs 1e-7 m criterion); worst relative facet area error <= 1.739e-14 and orientation dot error <= 5.551e-16. Qualified solid 3D contacts: ZERO BY AUTHORITY, not proof that plates never collide. All prior 48 source edge-edge closest-feature witnesses remain AMBIGUOUS at every checkpoint, so the unstable line-line nearest-point contact was correctly blocked.

## Next diagnostic principle

The edge-edge nearest-point method was ambiguous because authentic paired plate edges are quasi-parallel. However, original **source material parent IDs and their two adjacent original plate-owned triangles** supply a different *mathematically fixed witness*: corresponding material midpoints of the original boundary edge on plates p and q.

For each source edge `(a,b)`, construct inward face co-normals `m_p,m_q`: project the vector from edge midpoint to the face third vertex onto the plane perpendicular to that edge and normalize. Require `m_p·m_q <= -0.95`; this is an **engineering guard**, not a tectonic law. For passing features, define `n=(m_q-m_p)/||m_q-m_p||`, oriented toward the interior of source plate q. Define `g_shell = (mid_q-mid_p)·n`. Positive `g_shell` corresponds to *opening* when q moves toward its own original side; negative indicates *closure in the 2D surface-shell material-matched gap convention*, **NOT physically proven rock solid penetration**. At true T0 require |g_shell|<1e-8 m for original paired material nodes.

This is NOT an edge-edge closest-point minimum: no ill-conditioned s,t selection, and no invented additional vertices. At a triple junction, each authentic original source boundary ID/plate pair is evaluated separately; no independent force law is attached to the triple node.

## Driver and tests

New driver: `experiments/plate58_deforming_explore_v1/g2_source_shell_conormal_gap.py`. New source-free test: `tests/test_r6_g2_source_shell_conormal_gap.py`.

- Rebuild authentic FEG/PRE source plates (8×8 and 16×16), original pair-owned triangles and source Euler + source-preserving old KKT trajectory at T0 and years 100/500/1000; no new physical step.
- Pin SHA256 of full previous source face report to `3e42e1321cfb72f73bd72c82c32030969c908ec112ef5fb1255b9d7a767e4d07`, verify its manifest plus prior source SHA pins, and compare each source R6BND-T0 face co-normal dot / edge distance to its previous FAIR values.
- For eligible source material-matched edges, compute signed shell *diagnostic* gap, repeat under finite SO(3) rotation (<1e-7 m absolute difference) and two-sided numerical gradient with .5/.25 m perturbations, translation and manufactured virtual-work directional-derivative checks. This checks the functional, not a natural/calibrated contact force law.
- If side consistency fails, return `NOT_QUALIFIED` with `signed_shell_midpoint_gap_m=null`; never silently assign a physical contact sign.
- Preserve per-source IDs, 0/100/500/1000 signed opening ranges, number of negative shell gaps, co-normal orientations, and triple node. Never write canon or HistoryStore, never run updated-geometry KKT.

## FAIR command

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
  tests/test_r6_g2_source_shell_conormal_gap.py \
  tests/test_r6_g2_source_owned_face_topology.py \
  tests/test_r6_g2_contact_feature_admissibility.py \
  tests/test_r6_g2_t0_normal_segment_jacobian.py \
  tests/test_r6_g2_moving_3d_contact_parallel.py \
  tests/test_r6_g2_regional_unilateral_contact_time.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test ! -e "$BASE/G2_SOURCE_SHELL_CONORMAL_GAP_NEW_01"
python -m experiments.plate58_deforming_explore_v1.g2_source_shell_conormal_gap \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --prior-face "$BASE/G2_SOURCE_OWNED_FACE_TOPOLOGY_NEW_01" \
  --output "$BASE/G2_SOURCE_SHELL_CONORMAL_GAP_NEW_01"
```

## Decision boundary

A PASS of this new test demonstrates mathematical orientation and objective signed **material-matched shell boundary opening** *within this source kinematic representation*. It does NOT prove facet-facet solid collision, geological yielding/friction, fully constrained Signorini gap, natural G3/G4 traction or real T1. Additional source-authority review of solid surfaces or an explicitly scoped physically validated shell-contact constitutive law is required before any physical contact authorization.

`D-024=ACTIVE`, `physical_T1=null` and no canonical promotion regardless of engineering PASS.
