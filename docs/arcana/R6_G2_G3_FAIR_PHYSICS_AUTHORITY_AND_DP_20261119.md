# ARCANA R6 — FAIR G2/G3 physics result, elevation lineage and DP convention correction

Date 2026-11-19. Physical experiment response to the author's agreement to close G2/G3. **G3 A architecture only is author-ratified; no material/fluid/mechanical T1 approval has been granted.**

## FAIR GPE + G2 numerical results received

The operator's isolated FAIR checkout at commit `1755f5abdf25b676cf3bac6aa870f643f9078c39` reported:
```text
tests/test_r6_g3_gpe_hydrostatic.py
tests/test_r6_g2_viscoplastic_explore.py
14 passed in 0.17s

CANDIDATE_G3_A_GPE_FROM_AUTHENTIC_T0_COLUMNS__VERTICAL_CLOSURE_UNRESOLVED
8x8:  nodes=81, ||F_GPE||=1.6809905549966784e18 N,
      h=935.9264526367188..1295.07177734375 m,
      relative basal normal pressure spread=0.018182512158444856
16x16: nodes=289, ||F_GPE||=5.146333093594666e18 N,
      h=-6086.268749480888..1304.8494873046875 m,
      relative basal normal pressure spread=0.022580510078730923
solver_runs=0, mechanical_solve_authorized=false, physical_T1=null
```
The raw FAIR evidence remains outside this GitHub authoring environment at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_GPE_HYDROSTATIC_HYPOTHESIS_NEW_01` and was **not imported or independently recomputed** here. Do not interpret 1.68e18 and 5.15e18 N as net vector-traction (these are vector **L2 norms over DOFs**, in differently sized discrete domains). No absolute force-balance or mechanical domain-convergence claim follows. Pressure spread is variation in modeled hydrostatic `W`, not measured or proven dynamical disequilibrium.

## Critical source-authority finding (not guessed)

`R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json` specifically says:
```text
nodal_fields.elevation_m.authority = "NUMERICAL_DERIVED_SUPPORT"
nodal_fields.elevation_m.source_field = "total_surface_elevation_m"
source_authorities.surface_closed_package.authority =
   "GOVERNED_T0_FIELD_NUMERICAL_DERIVED_SUPPORT"
```
The original parent field is `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz`, SHA `31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534`, linked in FEG metadata. Source derivation *is not* separate physical validation of historical topography, ocean bathymetry or isostasy. The FEG's zero chemical-density anomaly is an explicitly numerical reference component and **not a canonically proven lack of lateral compositional density anomalies**: `R6_PRE_ORBDATA_CHEMICAL_DENSITY_MECHANICS_AUTHORITY.json`.

`R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_AUTHORITY.json` identifies **canonical R6 gravity g=9.82 m/s²** under `existing_authority_audit.canonical_planet`. The previous hypothesis used `9.80665 m/s²` from `material_rheology_provider.DEFAULT_BENCHMARK`, correctly explicitly labeled Earth analogue, not canon gravity. The new scenario `G2_G3_ARCANA_GRAVITY_GPE_SENSITIVITY.json` reuses the **canonical gravity** with still **hypothetical** `z_ref=-200,000 m`; reference normal pressure and vertical support remain null and elevation remains `NUMERICAL_DERIVED_SUPPORT`. It does not overwrite the previous FAIR evidence. A dedicated source metadata check guards the canonical gravity and classification in `g3_gpe_hydrostatic.build` and records their SHA/labels.

### Deterministic, unverified prediction for gravity change only

Since both `W` and `U` are linear in `g` with the fixed other fields, the GPE nodal force norms would scale by `9.82/9.80665`, **provided the run succeeds with exact same inputs**. Predicted, not measured by FAIR:
```text
8x8   about 1.68327892298e18 N
16x16 about 5.15333890565e18 N
```
The basic relative pressure spread remains unchanged if *only* gravity scales. This numerical sensitivity does not solve basal normal force, mantle shear, real T0 water state or material rheology.

## Additional constitutive scientific issue: two ASPECT DP pressure coefficients

First-party ASPECT documentation carries two different 3D pressure factors:
- Legacy `MaterialModel::ViscoPlastic`: `(6 C cos(phi) + 2 P sin(phi))/(sqrt(3)(3+sin(phi)))` — https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html
- `MaterialModel::Rheology::DruckerPrager`: `(6 C cos(phi) + 6 P sin(phi))/(sqrt(3)(3+sin(phi)))` — https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1Rheology_1_1DruckerPrager.html

These **cannot be silently interchanged**. The initial source `g2_viscoplastic_explore.py` used the legacy `2P` form while referencing ASPECT generically, without an explicit input model convention. It now **requires** `brittle.drucker_prager_pressure_convention` with either `ASPECT_RHEOLOGY_DP_3D_6P` or `ASPECT_LEGACY_VISCOPLASTIC_3D_2P`. The synthetic fixture uses the documented rheology 6P variant. A regression demonstrates that, after subtracting the same cohesion contribution, the effective-pressure sensitivity is 3 times larger for 6P than for 2P; missing convention fails closed. This is a **constitutive assumption**, not yet a scientifically endorsed ARCANA continuum plasticity law. Also note the smooth harmonic cap is not classical nonassociated return-mapped DP friction.

## What remains for true physical closure

**G2:** select mineralogical identity, constitutive strain-rate/pressure/temperature/hydration domains that cover the *actual* T0 crust including 280 K, without extending quartzite GT95 beyond its 1173–1373 K experimental temperature basis. Author and source pore-water/biot and mantle material; choose full brittle+ductile law, not only its algebraic smooth-cap approximation. Prove SHELLS `Diamnd/Mohr/OneBar` equivalence or authorize an explicitly distinct experimental solver.

**G3:** select a physical basal reference pressure and deep mantle motion field, explicitly assign ownership of GPE when using `Squeez/Fixed` (NEVER double count external GPE), source realistic N/S far-field continuum transfer (5:8:11) and test full force/torque/virtual-work balance. Elevation/compensation depth and topographic physics require geological authority; the current 2.26% modeled basal normal-pressure spread does not automatically specify an upward reaction.

**Next test on FAIR** (new source not yet tested): focused G2 pressure variants and one **new** 8x8/16x16 GPE sensitivity with canonical gravity. Neither command solves mechanics or T1. Do not rerun previous 14/14 old commit unless needed for regression coverage in the combined file.
