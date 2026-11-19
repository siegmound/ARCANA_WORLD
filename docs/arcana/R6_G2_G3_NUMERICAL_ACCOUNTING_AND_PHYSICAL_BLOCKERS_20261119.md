# ARCANA R6 — G2/G3 numerical accounting and remaining physical blockers

Date: 2026-11-19. Parent before new change: 8874170af3d666b8c160c024e6bbd7530c4a3818.
**Status: CODE_CANDIDATE — integrated FAIR verification pending. D-024 active.**

## G2 scientific change: laboratory validity is a continuous-depth requirement

The T0 PRE thermal law on each layer is cubic in local depth,
T(x)=c0+c1*x+c2*x²+c3*x³. Merely checking numerical integration Gauss points
does not certify every depth is inside a laboratory creep-law temperature
interval. New g2_exact_thermal_validity.py evaluates **both endpoints and
interior stationary points** of the PRE polynomial analytically, rejecting an
unsupported layer before g2_viscoplastic_explore integrates it.

The known T0 crust range 280..1051.558 K falls below the 1173.15..1373.15 K
GT95 high-temperature quartzite experimental window. No quartzite creep
calibration is promoted. Mineralogical identity, water fugacity, effective pore
pressure and brittle/ductile transitions are still authorially/scientifically
unqualified. The smooth harmonic cap remains an engineering approximation, not
a complete return-mapped Drucker-Prager / damage / fault law. The legacy 2P
ASPECT ViscoPlastic and modern 6P Rheology::DruckerPrager conventions remain
separate hypotheses, not an ARCANA material ratification.

Sources: https://doi.org/10.1002/2016JB013798
https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html
https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1Rheology_1_1DruckerPrager.html

## G3 A scientific change: exactly one candidate GPE force channel

g3_gpe_force_accounting.py combines already explicitly supplied P1 outer-cut
line loads, basal tangential loads, and one GPE candidate vector, preserving
the **same original parent-node East/North DOF order**. The function
rejects hidden channels, GPE double-count, mismatched source DOFs and any
attempt to promote a synthetic calculation to a physical solver state.

Outputs contain total and per-component global Cartesian resultant (N),
torque (N m), and optionally virtual power (W) for explicitly supplied
velocities. This is a mathematical/engineering identity check; it does not
prove equilibrium. The source GPE report now carries its external-only
owner and no-solve flags per scale for later source-verified composition.

Canonical R6 gravity is 9.82 m/s². The hydrostatic compensation plane -200km
and FEG derived elevation are **not** qualified by that canonical gravity.
They still lack geological/vertical pressure closure. GPE and horizontal basal
traction must not be counted again in original SHELLS Squeez/Fixed.

The thin-sheet literature requires GPE gradients, outer-boundary interactions,
basal tractions, and vertical support to be reconciled before equilibrium:
https://doi.org/10.1111/j.1365-246X.2007.03274.x

## Test scope and hard stops

New standalone synthetic tests: **7 G2 + 8 G3 = 15 local PASS**.
A new existing-G2 integration regression checks that a cubic 850 K interior
maximum cannot pass a 849.5 K laboratory upper bound merely because Gauss
nodes miss the maximum. Rerun **all four** focused test files in the isolated
FAIR checkout; do not report FAIR PASS until operator terminal evidence exists.

With a clean checkout at this commit:

    export PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1
    export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
    python -m pytest -q \
      tests/test_r6_g2_exact_thermal_validity.py \
      tests/test_r6_g3_gpe_force_accounting.py \
      tests/test_r6_g2_viscoplastic_explore.py \
      tests/test_r6_g3_gpe_hydrostatic.py

**Next substantive physical closure** requires real T0 material/mineral and
water/poroelastic law with P/T/rate applicability, plus 5:8:11 north/south
and other cut boundary tractions, deep-mantle basal shear and normal pressure,
consistent reference GPE owner, complete force/torque/virtual-work and rank
checks, and explicitly chosen original SHELLS or fully tested separate
two-exponent experimental solver. One common SHELLS eCreep affects Diamnd,
Mohr and OneBar; do not silently insert two exponents.

G2_material_ratified=false
G3_real_boundary_and_basal_physics_ratified=false
GPE_vertical_isostasy_qualified=false
SHELLS_two_exponent_solver_parity=false
mechanical_solve_authorized=false
solver_runs=0
physical_T1=null
D-024=ACTIVE
