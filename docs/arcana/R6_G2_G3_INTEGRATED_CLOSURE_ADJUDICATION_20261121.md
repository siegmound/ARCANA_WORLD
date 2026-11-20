# ARCANA R6 — G2/G3 integrated closure adjudication after FAIR core/exterior PASS
Date: 2026-11-21. Source branch: `r6/multiphysics-integration-20261026`.
Exact tested source SHA: `7002f3a8373f629cf7d59245f42af221a56aaa2d`.

**Decision: `G2_G3_SOURCE_INTERNAL_SOFTWARE_CLOSURE_FAIR_PASS__PHYSICAL_SOLVE_BLOCKED_SOURCE_AUTHORITY_GAPS`.**
This closes the *software-engineering internal-operator integration milestone*, NOT the real-world force balance, rock law, fault mechanics, geological prediction or T0→T1 physics. No canonical/HistoryStore mutation and no physical solve is authorized.

## 1. FAIR terminal receipt, exact qualification scope

The operator pasted the clean detached checkout and command outcomes:

```text
HEAD 7002f3a8 feat(r6): stitch authentic G2 core and G3 exterior internal forces over shared parent DOFs
CORE + EXTERIOR TESTS: 24 passed in 0.20s; TARGET_EXIT_CODE=0
FULL G2/G3 REGRESSION: 120 passed in 0.61s; REGRESSION_EXIT_CODE=0
```

The full regression includes the 24 targeted tests. It is **120 total**, not 120+24 independent tests. These are terminal results supplied by the FAIR operator; no independent transfer, hash authentication of FAIR logs or execution from this authoring environment is claimed. The earlier FAIR exterior-only gate was 19/19 + 96/96 at `72168a5e...`. This receipt supersedes the *FAIR PENDING* indication in the new-step design document, but does not rewrite its historical provenance.

Source-original 8×8: 81 parent nodes / 162 East-North DOFs, core 8 triangles with 9 nodes, exterior 120 triangles with 80 nodes, shared interface 8 parent nodes/16 EN DOFs, original total 128 triangles.
Source-original 16×16: 289 parent nodes / 578 EN DOFs, same 8 core triangles, exterior 504 triangles with 288 nodes, original total 512 triangles. The original plate triple parent 34587 is not silently split into three mechanical states.

The stitched operator assembles source-backed *candidate internal* G2+G3 forces, tangents and work from both regions. It transports only the **known exterior** load/GPE contributions, retaining `known_PARTIAL_residual_N_NOT_EQUILIBRIUM`. The eight original core basal facets, core external forces and core GPE/vertical closure remain missing. Do not label the known-channel residual global equilibrium.

## 2. Physical input findings (all must be addressed as one coupled scenario)

### G2 — materials and constitutive law

Available: source original 51-field PRE nodal thermal/geometry/density metadata, thicknesses, material configuration codes and original FEG topology; experimental candidate two-layer pressure-aware viscoplastic potential with independent crust/mantle exponents; source-binding and manufactured constitutive tests.

Missing: **authorially selected** rock/mineral/phase distributions for actual T0 crust and mantle; measured/source-backed hydration, fugacity, pore/effective pressure and Biot state; legitimate low-T brittle/friction and ductile mechanisms with laboratory stress and rate conventions, `A,n,E,V` where applicable; coverage of each used P/T/rate/material domain; validated material assignment and averaging rules; fault damage/weakening law.

Already examined Zenodo 8304793: 39 curves / 555 digitized stress–strain records from quartz/granulite high-temperature laboratory studies. They are neither 555 independent stress–strain-rate observations nor valid calibration of the source cold crust (280–1051.558 K, while cited high-temperature experiments start at ~1173 K). Never feed individual trace points straight to the stationary creep regressor; never use the quartzite law as the cold full-column ARCANA crust. Treat Earth analogues only as proposed EXPLORE material inputs, never canonical rock identity.

### G3 — genuine external and basal force closure

Available: source 32/64 exterior cut-edge inventory and 120/504 exterior basal triangle inventory; correct original core/exterior topology and current exclusive external-GPE bookkeeping prototype.

Missing: physically supported traction values and source units `N/m` on the exterior cut, shear tractions `N/m²` and vertical/normal support on **all 128/512 original basal triangles** including the eight core triangles, independent deep-mantle reference flow and coupling depth/law, validated pressure/topography datum and GPE source support/owner. The existing thermal LAB must not stand in for mechanical/rheological LAB. Euler velocities do not determine basal `beta` nor global traction balance. Missing does **not** mean zero.

### Fault/interface and solver route

**Selected engineering development direction (NOT a new physical ratification):** retain the source-aligned spherical **thin-lithosphere / fault-transmission** model family and qualify a physically meaningful explicit fault element/slip law before a regional mechanical solve. Original source FEG contains a 2D sheet, not closed 3D rock volumes. Therefore an automatically extruded solid, arbitrary sidewalls or 3D nonpenetration KKT is prohibited. An alternative 3D solid interface requires its own approved physical geometry, mesh and BCs; it is not a silent fallback.

The existing eight shared parent EN DOFs are correct for the current *continuous* internal test. They **cannot** by themselves represent independent displacement jumps across an active fault. A physical slip formulation must explicitly define sidedness, permitted independent traces, state ownership, traction action/reaction, rate/state or friction-cohesion response, effective-normal-stress support, and triple-junction treatment (parent 34587). Never invent source fault DOFs or equate a shell signed-gap diagnostic with validated solid contact.

Two-exponent G2 experimental potential is a separately versioned formulation; original SHELLS uses a common `eCreep`. It is not a justified direct replacement for the original SHELLS friction/OneBar/solver. If selecting original SHELLS, supply a common-exponent calibrated law plus approximation assessment. If selecting a new two-exponent EXPLORE solver, demonstrate nonlinear tangent/return or viscosity regularization/weak fault mechanism, gauge/rank and independent numerical equivalence limits. The smooth harmonic Drucker–Prager cap is not itself a physical fault return-mapping law.

## 3. Explicit source-to-solve acceptance conditions

All must pass before any **physical** regional 8×8 mechanical solve; the 16×16 extent is sensitivity, not automatic grid-convergence evidence:

1. **Source/authority:** exact SHA-pinned FEG/PRE provenance and all material, moisture, lithology, fault, mantle and force-provider identities; EXPLORE assumptions explicitly labeled and reviewed; no `null→0`.
2. **G2 coverage:** complete original 81/289 parent-node assignment, phase/lithology and hydration/poro-state provenance, source-specific laboratory domain support (temperature, pressure, stress, strain rate, fugacity), uncertainty and valid constitutive conventions; explicit outside-range rejection.
3. **G3 full inventory:** complete 32/64 cut lines, **128/512** basal facets inclusive of core eight, physically supported normal/tangential loads, force dimensions and consistent parent-frame transformation; core and exterior GPE accounting exactly once and no orphan/unowned load.
4. **Fault mechanics:** a true source-side trace or physically supported distinct interface state, explicit traction law, effective normal pressure, separation/slip orientation, action/reaction and triple junction; no automatic contact from old 1-year shell gap sign changes (not dt-robust).
5. **Solver closure:** declared nonlinear algorithm and discrete residual/tangent, identified constrained/gauge DOFs and rank, external/internal force and torque budget, consistent virtual-work/power partitions, bounded constitutive dissipation and perturbation/Jacobian checks.
6. **Numerical science:** restart parity, independent constitutive/force benchmarks, mesh sensitivity with comparable physical boundary data, timestep/event sensitivity and closed conservation/uncertainty accounting; no canonical T1 without a separately governed forward state-transfer G4.
7. **Governance:** issue an explicit bounded physical EXPLORE authorization on a complete scenario. No mechanical or world-history production inferred from this software milestone.

The companion JSON lists each missing **physical input**, allowed evidence route, source requirement and the strict NO-GO state. It is not a plausible numeric dataset or a ready-to-run input template.

## 4. Next implementation package, not an endless gate chain

A single *provider-backed* G2/G3/FAULT scenario should bind:
- material identity/phase/porosity/water with pressure and constitutive coverage per source parent node;
- original full-core-and-exterior physical tractions, full basal normal/shear/GPE budget and global-mantle source/boundary closure;
- the chosen thin-sheet fault transmission and pressure-effective law, plus a versioned nonlinear solver strategy.

Do **not** substitute another geometry-only test or manufactured shell KKT as closure. If ARCANA authors do not specify rock, water, mantle forcing or fault behavior, return `SOURCE_AUTHORITY_GAP`; an explicitly labeled **synthetic benchmark** may test code independently but must never produce `physical_T1`.

## 5. Fixed current state and citations

```text
G2_G3_SOURCE_INTERNAL_STITCH_SOFTWARE_FAIR=PASS_OPERATOR_REPORTED_120_OF_120
G2_MATERIAL_LAW_AUTHOR_RATIFIED=false
G3_FULL_DOMAIN_LOAD_PROVIDER_QUALIFIED=false
FAULT_PHYSICAL_TRANSMISSION_LAW_QUALIFIED=false
G2_G3_FULL_PHYSICAL_EQUILIBRIUM_AVAILABLE=false
MECHANICAL_SOLVE_AUTHORIZED=false
SOLVER_RUNS=0
D_024=ACTIVE
physical_T1=null
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

In-repository source basis:
- `R6_G2_G3_CORE_EXTERIOR_SOURCE_INTERNAL_STITCH_FAIR_GATE_20261120.md`
- `R6_G2_G3_CONTACT_COUPLED_SOURCE_AUTHORITY_GATE_20261120.md`
- `R6_G2_G3_PAIRED_PHYSICAL_SCENARIO_DECISION_20261119.md`
- `R6_G2_G3_EMPIRICAL_CALIBRATION_FAIR_PASS_20261120.md`
- `R6_ZENODO_8304793_FAIR_CURVES_SCIENTIFIC_ADJUDICATION_20261120.md`

Independent methodology (Earth analogues, not ARCANA boundary values):
- Bird & Kong (1995), SHELLS spherical continuum/fault elements: https://doi.org/10.1029/95JB02435
- Bird (1999), thin-plate/thin-shell modelling: https://doi.org/10.1016/S0098-3004(98)00142-3
- Masuti, Muto & Rybacki (2023) transient lab rheology: https://doi.org/10.1029/2023JB027762 ; source https://zenodo.org/records/8304793
- ASPECT viscoplastic material conventions: https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html
