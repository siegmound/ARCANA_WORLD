# ARCANA R6 — G2 PRE binding FAIR PASS, G3 A explicit load mechanics and force ledger

Date 2026-11-19. Operator-reported FAIR terminal:
```text
commit 791adc2e478388484c431546abea2744d919aa53
tests/test_r6_g2_nodal_source_bridge.py: 7 passed in 0.10s
PASS_G2_SOURCE_NODAL_ELEMENT_BINDING__CONSTITUTIVE_AND_G3_FORCING_OPEN
8x8: 81 PRE source nodes, 120 exterior triangles, 0 mixed material configuration code triangles
16x16: 289 PRE source nodes, 504 exterior triangles, 0 mixed material configuration code triangles
triple source node ID 34587
mechanical_solve_authorized=false, solver_runs=0, physical_T1=null
```

The number **zero mixed material-code triangles** means no triangle has different vertex values of `material_configuration_code`. It does NOT establish homogeneous mineralogy, hydrated status, unique material type across plates 5/8/11, or the physical absence of shear zones or faults. All 51 PRE source fields are bound, but none is a validated fault-traction or water-fugacity provider.

## New G3 A numerical implementation — explicit noncanonical external and basal force weak form

`g3_force_budget.py` implements a mathematically consistent **P1 faceted-surface traction integral** with true source parent nodes and per-node E/N tangent DOF. Inputs are ONLY explicit engineering scenarios:
- an exhaustive source cut-edge catalog, including side and adjacent source plate;
- a traction **3D ECEF vector in N/m for both endpoints of every cut edge**, source reference/authority and channel `EXTERIOR_BOUNDARY`; the field must be tangential at each endpoint;
- an explicit **basal tangential shear force density in N/m² at each triangle vertex**, source ID and authority, on every exterior parent triangle;
- an explicit `SYNTHETIC_NO_GPE__NOT_A_PHYSICAL_GPE_CLOSURE` decision. This module does NOT add gravitational-potential driving, nor certify GPE ownership.

Endpoint line loads use length of embedded spherical **faceted chord** L and P1 consistent quadrature:
```text
F_a_xyz_preprojection = L*(2*t_a + t_b)/6
F_b_xyz_preprojection = L*(t_a + 2*t_b)/6
```
Each load is projected into its original node's E/N DOF. Each triangle basal force uses faceted element area A and:
```text
F_i_xyz_preprojection = A*(2*b_i + b_j + b_k)/12.
```
The force vector is not a mechanical equilibrium solution. The code reports net 3D nodal force, global torque `sum(r_i × F_i)`, and virtual power when nodal E/N velocities are explicitly passed, plus facet chord-vs-arc discrepancy. It does **not** cancel nonzero resultant or torque through invented reactions. Normal basal support must be developed separately from the tangential 2D DOFs.

The **same 5/8/11 parent node always has one 2-DOF mechanical state** irrespective of how many contact edges meet there. No duplicate Euler Dirichlet constraints are generated.

`source_force_requirements()` authenticates the FAIR multiscale, interface and nodal G2 source files by SHA, then lists all required external-cut and basal inputs for 8x8 and 16x16. Expect 32/64 true exterior cut edges and 120/504 basal parent triangles (8x8 /16x16 respectively). All physical source loads remain `null`. It records the three-plate node 34587 and the source contact-pair graph. The audit is NOT a force computation.

Unit tests of the engineering load assembler validate line P1 quadrature, basal area traction, explicit missing-force refusal, radial-force rejection, source plate owner check, virtual power/torque equality and no duplicated DOF at a synthetic triple node. Tests on FAIR and authentic requirement audit are PENDING.

## Scientific reason for strict input separation

Studies of SHELLS describe a thin-shell 2D horizontal velocity field with depth-integrated 3D density and strength, and their use of consistent nodal forces to assess net plate torque. This makes actual external traction, GPE and basal force accounting essential; simply inserting Euler velocities at a shared boundary node or assuming zero shear would be physically unjustified. Cite Bird et al., *Stresses that drive plates from below*, JGR 2008 DOI 10.1029/2007JB005460, and Bird (1999) *Thin-plate and thin-shell finite-element programs...* doi 10.1016/S0098-3004(98)00142-3.

Empirical quartzite creep can be strongly sensitive to water fugacity, e.g. Hirth, Teyssier and Dunlap (2001), doi 10.1007/s005310000152. Lab brittle/friction envelopes require explicit effective stress and pore-pressure assumptions: Brace & Kohlstedt (1980), doi 10.1029/JB085iB11p06248. Those are candidate scientific references, not a direct assignment to fantasy ARCANA T0.

## FAIR next verification

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# stop if dirty:
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
python -m pytest -q tests/test_r6_g3_force_budget.py

MULTISCALE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01
MECHANICAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01
NODAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_FORCE_REQUIREMENTS_NEW_01
python -m experiments.plate58_deforming_explore_v1.g3_force_budget "$MULTISCALE" "$MECHANICAL" "$NODAL" "$OUTPUT"
```

This inventories source force providers but does not create physical loads or run ShellSet. D-024 and no canonical T1 remain.

## Remaining G2/G3 physical closure

1. G2 full-depth brittle+ductile, actual T/P validity, effective stress / pore pressure, water fugacity and mineralogy selection (including n=4 and n=3.5 separate layer behaviors), with robust constraints and authorial scope.
2. G3 A basal normal support, lateral GPE owner/balance, source-supported N/S far-field loads including plate11 and true triple node, physical forcing plus boundary/gauge treatment.
3. Solve validation: net torque/work balance, convergence in spatial extent and resolution, tensor parity to actual ShellSet and bounded noncanonical first physical advance; no auto-promotion to T1.
