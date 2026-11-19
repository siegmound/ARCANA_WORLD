# ARCANA R6 — Plate 5:8: post-FAIR G2 adjudication and authorial physical experiment choice

**Date:** 2026-11-19  
**Authority:** `PROPOSED_EXPERIMENTAL_ONLY__NOT_RATIFIED`  
**Branch:** `r6/multiphysics-integration-20261026`  
**Target:** first genuine source-bound *mechanically deforming* ARCANA T1, NOT another prescribed-Euler geometry-only T1.
**No solver run, no new T1, no canon mutation.** D-024 applies.

## 1. What FAIR has actually established

The operator reported, against published GitHub commit `cee4e84f63c17ca0ee63814aff1c8366febdc131`:

```
tests/test_r6_plate58_wet_quartz_screen.py: 14/14 PASS
PASS_G2_ALTERNATE_WET_QUARTZ_PT_SCREEN__WATER_UNRESOLVED
source crust: 9 PRE parent nodes, 9 depths each = 81 samples
T min/max 280.0 / 1051.5581968311126 K
18/81 in the 2019 wet-quartz experiment temperature range [973.15,1473.15] K
63/81 outside this temperature range
9/81 cross-study screening intersection with 2021 pressure grouping
54/81 P <560 MPa, 18/81 P in [560,700) MPa,
9/81 P in [700,1600] MPa
water_or_fugacity_known=false
G2_effective_constitutive_closure=null
mechanical_solve_authorized=false
solver_runs=0
```

The 9 joint-screen points are **not** nine independently validated physical samples: the thermal samples are reconstructed from nine source-identified PRE node profiles and fixed-depth quadrature-like positions, not new field observations. The `cross_study_overlap` flag combines **different laboratory aggregations** and is *not* a domain where a single calibrated constitutive law has been demonstrated.

The preceding FAIR passes remain:
- G3 16-cell source diagnostic **9/9**, 25 nodes, 32 triangles, six contact segments, north owners [8,5,5,5], south [8,8,8,5].
- G3 exit-node audit **6/6**, two shared-nodal Euler incompatibilities at parent nodes 36744 (north) and 35306 (south); velocities from different plates cannot be simultaneously imposed on one continuous FEG DOF.
- G2 original benchmark **12/12**, 0/81 crust temperatures in GT95 900–1100°C; slope-only common eCreep maximum deviation 4.197428237611889%, **not** full integrated strength or geologic uncertainty.

All FAIR evidence folders remain **external** to GitHub; this document records the user's terminal reports and does not claim new hash verification of FAIR files.

## 2. Scientific decision from these results

**Rejected as a *physical* material promotion:** assigning a uniform GT95 Black Hills quartzite law to the whole hot-extended ARCANA continental crust just because an algebraic fit yields a finite stress. The nine-source-column proxy shows its calibration-temperature mismatch at every evaluated sample. The nominal 405/98 MPa at 10 km from the earlier FAIR decision is a laboratory-formulation sensitivity, not a selected actual constitutive strength.

**Not established:** that the 2019/2021 wet-quartz studies supply a field-correct law across the entire 28 km crust. Even the broader temperature screen covers only 18/81 sampling positions; fugacity/water, pressure convention, activation law, brittle transition and the cooler part remain unknown. The dry-olivine material adapter is a benchmark, not automatically the mantle mineralogy of ARCANA.

**Retained for bounded numerical exploration only:** use separate physically stated candidate branches for cold(er) brittle/frictional and deep ductile response, and an explicit mantle benchmark, but only after a user-authored water/effective-pressure/strength-law hypothesis with units, source, admissibility range and sensitivity. Do not infer a phase boundary from the screen counts: a 9-point-per-column grid is a diagnostic sampling, not a lithological zoning law.

## 3. One integrated proposed experiment (not yet authorized)

**Model family (proposed):** `R6_PLATE58_NONCANONICAL_CONTINUUM_MASS_CONSERVING_V1`.

| Choice | Recommended path | Unresolved physically required input |
|---|---|---|
| Geometry | Source T0 continuous FEG with explicit 5:8 source IDs; no invented fault or node duplication | Physical accommodation width, numerically converged refinement, boundary-domain size |
| G2 crust | Two separate **candidate** effective strength profiles: dry/reference quartzite comparison and water-sensitive quartz alternative; brittle+ductile appropriate to region and unknown branch validity | Whole-profile effective strength including pore pressure, Biot, friction, fault-free continuum applicability, actual fugacity, time/rate domain and benchmark extrapolation |
| G2 mantle | Existing Hirth–Kohlstedt/ASPECT dry-olivine *benchmark* as sensitivity, not authorial mineralogy | Validate/exclude its use; pressure/rate/temperature and effective lithology, SHELLS two-layer fit |
| G2 SHELLS binding | Preserve single eCreep shared by the paired LR layers or distinct isolated LR variants, and compare integrated stress profiles | Actual a,b,c,d,e, caps and full-integral fit/acceptance; candidate 0.267857 not ratified |
| G3 exterior | **A preferred:** solve physically closed outer continuum and transfer correct traction/velocity relation to internal N/S cuts. West plate8/east plate5 Euler far field may drive distal edges if supported | Outer-domain loads, external continuation law, nonperiodic N/S closure, contact-exit compatibility; independence from halo size |
| G3 alternative | **B engineering sensitivity only:** SHELLS `free` N/S on progressively larger halos; cannot by itself validate ARCANA physical T1 | Exact modeled litostatic side load, convergence against halo/BC variations, external comparison to A |
| G3 basal | Preserve already-implemented PRE-derived GPE/vertical-integrated `Squeez`/`Fixed` terms; experimental tangential free-slip is merely a hypothesis | Confirm no duplicated normal pressure/vertical support, mantle reference and permitted tangential coupling; correct force/work budget |
| Time/G4 | Only after static force closure choose bounded small model timestep, conserve mass/layer area, heat and border flux; retain parent IDs | Valid Euler/event window, timestep error, material transport and thermal splitting, T0/T1 replay |

**Do not infer a G3 boundary condition from the near-constant 0.1575 m/year kinematic opening**. In particular, mixing two Euler solutions at the shared N/S contact node produces contradictory Dirichlet rows; averaging would destroy the model's contact physics. The external continuum must supply a unique compatible velocity at a continuous shared node (or an explicitly separately authorized discontinuity law and new DOFs).

**Important scope guard:** an engineering SHELLS run with a bounded example rheology under option B can be useful as an *unqualified numerical sensitivity*, but no such run or T1 is authorized by this proposal. A converged solver output alone is not a physically historical ARCANA state.

## 4. Required bundled authorial decision, not another chain of micro-gates

For a first **EXPLORE-only** solve authorization the author must explicitly select and define the *complete* three-part scenario:

1. **G2:** crust constitutive reference branch and water-sensitive alternative (or replacement), fugacity/pore-pressure assumption and Biot, friction/Byerly, brittle limit, mantle benchmark acceptability, rate/P/T window, numerical coefficients/units, robust integrated-stress validation including all cooler material.
2. **G3 external:** A with actual documented external model/provider, loads, domain and BC transfer; or B explicitly only as nonhistorical numerical sensitivity with source load semantics and size/BC convergence. Neither branch may silently prescribe two velocities at one DOF.
3. **G3 basal + geometry/time:** physically coherent support and tangential interaction in the code’s exact frame, a nonfabricated 100 km bandwidth hypothesis with resolution test, bounded time window and G4 mass/energy/flux/restart acceptance rules.

The three selections have **not** been made by the author. No magnitude is silently initialized to zero. Where required data cannot be justified, `null` is the correct authority value. No new "diagnostic shell" is needed before these choices: doing more PRE/lab overlap screens would not determine unknown water or exterior mechanics.

## 5. Go/no-go

```text
G2_GT95_WHOLE_CRUST_SOURCE_VALIDATED=false
G2_WET_QUARTZ_CROSS_STUDY_SCREEN=PASS_ONLY
G2_FIELD_WATER_FUGACITY=UNKNOWN
G2_BRITTLE_EFFECTIVE_STRENGTH=UNKNOWN
G2_FULL_COLUMN_LR_FIT=UNKNOWN
G3_NS_CONTINUATION=UNKNOWN
G3_BASAL_NORMAL_SUPPORT=UNKNOWN
G3_WIDTH_SPATIAL_CONVERGENCE=UNKNOWN
AUTHORIAL_EXPERIMENT_SCENARIO=NOT_RATIFIED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_DEFORMING_T1=BLOCKED
```

This is a **decision boundary**, not a code bug. Next actionable move: authorial scenario selection with defensible parameters, then create a real ShellSet experimental case, perform one short physically interpreted solve, and only after validation integrate G4/HistoryStore.

## References (existing repository)

- `experiments/plate58_deforming_explore_v1/wet_quartz_screen.py` and `README_WET_QUARTZ_SCREEN.md`
- `experiments/plate58_deforming_explore_v1/rheology_envelope.py` and `README_G2_ENVELOPE.md`
- `docs/arcana/R6_PLATE58_G2_G3_MECHANICAL_CLOSURE_DECISION_20261119.md`
- `docs/arcana/R6_FIRST_DEFORMATION_MODEL_DECISION_FAIR_20261118.md`
- `external/ShellSet-v1.1.0/src/MOD_Shells.f90` (`Fixed`, `Squeez`, `VBCs`, `Diamnd`)
- `external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90` (LR record)
