# ARCANA R6 — Regional source-keyed unilateral contact time gate

**Date:** 2026-11-20.
**Prior FAIR-tested source:** `2da20adf7637fc4a325bd2d3239143f41c6027ca`, 32/32 PASS contact source registry, synthetic STATIC penalty policies and 18 SO(3) local-element frame checks in each region.
**Registered receipt commit:** `6ab6bbf438d2073538d70f099721fdc108ccff3f`.

**Decision:** AUTHORIZE a NEW **ENGINEERING_ONLY manufactured discrete Signorini-like normal-contact test**, explicitly on **fixed T0 normals and fixed P1 tangent**. It does not qualify moving contact geometry, a natural G3 traction/pressure, true geodynamics or an ARCANA physical T1.

## Critical failure this experiment targets

The prior `CLOSING_NORMAL_ONLY` velocity-penalty test in 16×16 activated **4 closing links**, but **all 4 still had closing normal velocity signs after the solve**. Symmetric finite penalties do not guarantee nonpenetration. Instead require an actual constrained solve.

## Mathematics and source ownership

Use source-verified original `R6BND-T0-...` edges and plate pairs, 8×8 plate 5:8 and 16×16 plates 5:8:11, with actual triple source node `34587`. Every pair-node link has an **independent source-normal constraint** from the previous contact registry. NO derived contacts are allowed at other shared nodes.

Plate-local East/North mechanical DOFs and the original faceted P1 `spherical_element_tangent` are retained. T0 PRE thickness modulates **invented** `eta_crust=1e20 Pa s`, `eta_mantle=1e21 Pa s` with memory `tau=200 model years`. Normal relative displacement, `gap`, starts at zero at every T0 source-pair link and is updated **in the original T0 East/North reference normal**, not from current physical 3D surfaces.

Let `J` map plate-local nodal velocity to oriented source-normal relative pair velocity `Jv`, with positive sign for opening. On each implicit Euler time step

```text
A v = b + Jᵀ λ
A = I + (K/C) (1 + Δt/τ)
b = g_Euler - (K/C) u_old / τ
C = 0.5 mean(diag(K)) I

u_new = u_old + Δt v
gap_new = gap_old + Δt (Jv)
gap_new >= 0
λ >= 0
λ_i * gap_new_i = 0
```

A and b are **normalized** by the artificial drag coefficient so λ is an invented normalized force, not a physical Newton load.

The dual Schur problem is `S=J A⁻¹ Jᵀ` and `d=J A⁻¹ b + gap_old/Δt`; find `λ>=0` minimizing `½ λᵀSλ + dᵀλ`. The implementation uses a Cholesky-whitened nonnegative least-squares solution and checks the primal equation, nonnegative *final gap*, and complementarity at every step.

The full sparse A factorization and Schur matrix are reused for each chosen Δt; these are **small regional** experiments. A redundant source contact Jacobian should cause a **fail-closed** report rather than silently using an artificial spring. Closing is not determined from a frozen active-set chosen before the solve: it follows from constrained KKT optimization.

**Fundamental geometric limitation:** source normals are held at T0 and normal gap is the time integral of `Jv`. It is NOT verified physical minimum 3D distance between rotated triangle surfaces. Thus this gates the algebra of discrete unilateral complementarity, NOT a claim of true contact during a deforming Earth evolution. For full physical nonpenetration, co-rotating frames, moving normals, signed 3D point-to-face gaps and edge interactions must be added later.

## FAIR test matrix

- Original source domains **8×8 (13 contact pair-node links, 0 initial Euler closing)** and **16×16 (39 contact pair-node links, 4 initial Euler closing)**; verify source hashes, nodal source PRE/FEG binding, original contact provenance, and initial rate sign inventory.
- Iterate manufactured G1↔G2 P1 and contact reaction to years **100, 500, 1000**, with **Δt=1,5,10 model years**. Confirm gap and λ KKT at **every step**, report total activations and largest normalized reaction.
- Restart 500+500 with 1-year time step and compare final displacement **<1e-8m**.
- At 100 and 1000 model years compare dt5 and dt10 against dt1; require dt5 error not larger than dt10, within numerical slack, but do not interpret as analytical convergence order or fixed-domain spatial convergence.
- Save original source boundary IDs, parent nodes/plate pairs and initial source-normal rates in the **full FAIR report**; print a reduced operator summary. Never overwrite previously sealed evidence.

The source-free unit test suite checks a provably closing two-node example, opening with zero multiplier, existing gap permitting temporary closing, simultaneous pair links at a triple-node analogue, redundant constraints fail-closed, action/reaction, null input, restart, and rejected invalid state.

## FAIR command — pending source execution

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
  tests/test_r6_g2_regional_unilateral_contact_time.py \
  tests/test_r6_g2_source_contact_objectivity.py \
  tests/test_r6_g2_global_sparse_p1_static.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -f "$BASE/G2_SOURCE_CONTACT_OBJECTIVITY_NEW_01/MANIFEST.json"
test -f "$BASE/G2_SOURCE_CONTACT_OBJECTIVITY_NEW_01/REPORT.json"
test -d "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01"
test -d "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01"

python -m experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-contact "$BASE/G2_SOURCE_CONTACT_OBJECTIVITY_NEW_01" \
  --output "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01"
```

**This code has not yet been source-run on FAIR at publication**. A zero or failed KKT result should be investigated with the original provenance; no physical source or test threshold is to be silently changed. Source output must be a **new exclusive** folder.

## What remains blocked

Successful results would show that the **linear source-normal unilateral model** can evolve a nonnegative contact-gap variable while preserving KKT, restarts and work/residual identities. Still absent are real 3D moving geometry and updated normals, true traction directions and torque balances, slip friction, hydration/temperature-dependent G2 rheology, source-calibrated G3 lateral/basal loads and G4 layer thermal/mass transport. The 12-plate global manufactured 1000y baseline remains valid only for independent plate contacts.

```text
PRIOR_SOURCE_CONTACT_OBJECTIVITY_FAIR=PASS_32_OF_32
REGIONAL_UNILATERAL_GAP_COMPLEMENTARITY_FAIR=PENDING
MOVING_3D_NORMALS_AND_CONTACT_GAPS=NOT_IMPLEMENTED
REAL_G2_G3_MATERIAL_AND_FORCES=OPEN
D_024=ACTIVE
physical_T1=null
```
