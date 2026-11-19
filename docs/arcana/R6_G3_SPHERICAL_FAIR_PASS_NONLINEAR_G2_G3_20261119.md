# ARCANA R6 — FAIR spherical source PASS and first coupled nonlinear G2/G3 A engineering operator

**Operator report: 2026-11-19**. No independent direct access to the FAIR output files in this commit. The operator ran on FAIR at `2603c90984b3069ee655e9ec0c2517d7b6ec6e85`:

```text
tests/test_r6_g3_spherical_exterior.py: 8 passed in 0.16s
PASS_G3_A_SOURCE_SPHERICAL_FACET_AUDIT__G2_G3_PHYSICS_UNRESOLVED
8x8 exterior triangles=120
max_area_deficit=7.558776317639904e-05
total_relative_area_deficit=7.470915197782535e-05
max_rigid_rotation_strain_s_inv=4.0888805869167684e-29
triple_parent_node_ids=[]
16x16 exterior triangles=504
max_area_deficit=7.604907147884532e-05
total_relative_area_deficit=7.455190158156544e-05
max_rigid_rotation_strain_s_inv=4.0888805869167684e-29
triple_parent_node_ids=[34587]
mechanical_solve_authorized=false
solver_runs=0
physical_T1=null
```

The max facet vs geodesic triangle relative deficit is around 0.0076%; this is only an *area* comparison and cannot qualify all spherical covariant strain terms or the physical solution. The exact source node of the 5:8:11 triple plate junction is **34587**. Old source evidence was not modified.

## Substantial next software implementation: nonlinear 3D-incompressible layer G2 → spherical G3 A

New `nonlinear_layered_g3.py` is a **separate noncanonical engineering constitutive formulation** that supports different dislocation exponents in crust and mantle **without changing SHELLS source**. It is not an exact dual-`eCreep` patch of `Mohr`, `Diamnd` or `OneBar`, and is not authorized as an alternate planetary solver.

The new tensor calculation uses 2D in-plane rate vector `e=[eps_xx, eps_yy, gamma_xy]` and imposes 3D incompressible thickness strain `eps_zz=-(eps_xx+eps_yy)`. Thus `eps_II^2=e.T Q e`, with `Q=[[1,0.5,0],[0.5,1,0],[0,0,0.25]]`. For each layer and depth Gauss point, the rate-based dislocation candidate is `eps_II=A_eff*sigma_II^n exp(-(E+PV)/(RT))`, with all coefficients, P/T/rate validity, explicit gravity and optional water fugacity mandatory as applicable.

Write `alpha=1/n`, `C(z)=A_eff^(-alpha)*exp((E+PV)/(nRT))`, `r=sqrt(e.T Q e + eps_floor^2)`, with the **engineering regularization rate explicitly provided**. An analytical non-negative layer potential is:

```text
Phi_layer(e) = integral 2 C(z)/(alpha+1)
               [r^(alpha+1) - eps_floor^(alpha+1)] dz
N_layer(e) = dPhi/de = integral 2 C(z) r^(alpha-1) Q e dz
D_layer(e) = dN/de = integral 2 C(z) r^(alpha-1)
                [Q + (alpha-1)*(Qe)(Qe)^T/r^2] dz
```

This is a **convex dissipation potential** for n>=1, with exact analytic consistent Newton tangent. Each layer contributes separately, allowing alpha_crust=0.25, alpha_mantle=1/3.5 (used only in synthetic tests). For n=1 it recovers the earlier Newtonian membrane tensor with `eta=1/(2A)` and `lambda_h=2eta_h` under the specified incompressible closure. No rheology values are inferred from an ARCANA source PRE node.

The element binds the **existing spherical-facet strain B** to `f_int=A B.T N` and `K_consistent=A B.T D B`, and global assembly combines source parent triangle IDs and node DOFs. Unlike the earlier linear kernel this is a true nonlinear constitutive residual plus analytic Newton tangent. 11 local synthetic tests PASS, including finite-difference verification of the potential gradient, constitutive tangent, element tangent, global two-triangle coupling, three rigid rotations, missing water/P/T validity guards, and n=1 parity.

## Absolute boundaries

- No brittle/frictional fault yielding, damage, or plasticity; `brittle_failure_implemented=false`.
- No real-PRE-to-element interpolation provider yet; the global assembler accepts only a deliberately marked **synthetic** `PRE_projection_provenance=EXPLICIT_TEST_COLUMN_NOT_VALIDATED_FOR_REAL_T0`. It cannot silently transform 25 true PRE nodal columns into calibrated elements.
- All material laws are hypotheses `ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED`; dry/wet labels and material mix remain unselected. Input water fugacity **cannot** be inferred from PRE; stress convention uses a declared ASPECT-style invariant and is not proven equivalent to complete nonlinear SHELLS.
- No G3 A external/body force, far-boundary tractions, normal/tangential basal law, GPE nonduplication, mechanics solve or T1 is authorized.
- This is neither a globally qualified G2 rheology nor a materially calibrated 5:8:11 solution.

## FAIR follow-up

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
python -m pytest -q tests/test_r6_g2_g3_nonlinear_layered.py
```

No execution on actual ARCANA nodal PRE with fabricated materials or tractions is requested. Follow-up engineering work should now qualify empirical full-depth G2 ductile+brittle, water/P effective, a source-bound PRE-to-element projection and external/basal G3 A forces with plate11; only then permit an explicitly reviewed bounded EXPLORE physical solve. D-024 remains unchanged.
