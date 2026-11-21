# ARCANA R6 — FAIR 183/183 source-original contact-side thermal applicability (T0)

Date: 2026-11-21. **Exact FAIR-tested code commit:** `3b9908a6abefca61e1080d607f55535b8d36a448`.
Decision: `T0_SOURCE_FEG_PRE_CONTACT_THERMAL_DIAGNOSTIC_FAIR_PASS__MINERALOGY_AND_REAL_SLIP_UNBOUND`.

## Operator-provided FAIR execution

```text
HEAD 3b9908a6 refactor(r6): label triple-junction field by three-plate incidence rather than node existence
17 passed in 0.36s
TARGET_EXIT_CODE=0
183 passed in 1.00s
FULL_REGRESSION_EXIT_CODE=0
{
  "status": "SOURCE_T0_FAULT_CONTACT_THERMAL_APPLICABILITY_AUDITED__GEOLOGY_AND_SLIP_OPEN",
  "regions": [
    {"extent":8,"contact_edges":12,"contact_both_sides_thermal_isotherm":12,
     "source_plate_pairs":[[5,8]]},
    {"extent":16,"contact_edges":36,"contact_both_sides_thermal_isotherm":36,
     "source_plate_pairs":[[5,8],[5,11],[8,11]]}
  ],
  "lab_fitted_rows_compatible_in_mechanical_physics":0,
  "source_gouge_mineralogy_bound":false,
  "physical_T1":null,
  "mechanical_solve_authorized":false
}
SOURCE_ANALYSIS_EXIT_CODE=0
```

Evidence: FAIR operator terminal transcript pasted into chat. The authoring environment did **not** independently fetch the FAIR log bytes or report manifest SHA; the checked-out git hash and results are operator-reported. Recorded log locations:
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_CONTACT_TARGET_17.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_CONTACT_FULL_183.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_CONTACT_REAL_SOURCE.log`

New immutable report expected at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_T0_CONTACT_THERMAL_MATERIAL_NEW_01/REPORT.json`, with manifest and source digests.

## Verified scope and scientific interpretation

The checked source contract (original FEG/PRE and G2 nodal/RSF SHA chain) examines:
- **8×8:** 81 original parent nodes, 128 original triangular facets, 12 original contact edges on plate pair 5:8, each contact has two source-owned facets.
- **16×16:** 289 original parent nodes, 512 original triangular facets, 36 original contact edges involving 5:8, 5:11 and 8:11; authentic 3-plate junction is defined by three incident plate owners at parent node 34587 rather than by node presence alone.
- **12/12 and 36/36** source contacts met the *necessary mathematical vertex-column reachability condition*: all three vertices of each of the two owner faces have some depth in their respective original crustal thermal profile at **293.15 K**.
- The two nested regions must not be summed as 48 statistically/geologically independent faults. The thermal roots may exist at different depths, and the source original shared parent node PRE values are not independent sides or a physically defined fault plane.
- This does **not** show actual fault temperature at a common depth, a real gouge existing anywhere, lithological clay fraction, hydration, water-fugacity or pore fluid pressure, true Earth-lab-to-ARCANA mineral composition correspondence, strain/slip-rate applicability or physical effective normal stress.
- Previous PANGAEA 921284 Earth laboratory dataset SHA256 `b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d` contains 66 inverse-model fitted parameter rows; here **0 of 66** are assigned to an actual ARCANA source contact or qualified as physically compatible with its actual fault stress/lithology.
- **17 new targeted tests** and **183 total defined G2/G3+RSF+contact-material tests** passed at exact `3b9908a6abefca61e1080d607f55535b8d36a448`, not an all-repository suite claim.

## Scientific follow-on: physical geology before source-constrained fault friction

The top next priorities are (1) define and qualify T0 **actual rock mineralogy/composition and hydration** at original plate5:8:11 contact sides, distinguishing global crust reference roles from natural gouge lithology; (2) independently close source fault surface/depth/slip-sidedness, including physically motivated thickness/split DOFs without changing original owner IDs or triple node semantics; (3) source actual effective normal pressure, absolute mu_ref, equivalent physical stiffness and valid P/T/slip-rate envelope, including comparison with Earth lab fitted parameters; (4) qualify external 5:8:11 force/cut/mantle basal normal+tangential and one-owner GPE, then compatible mechanical evolution.

The preceding step only reports availability of the 20°C isotherm in six *separate nodal columns* per contact. Because 293.15K may be a shallow commonly-crossed isotherm, this result cannot be interpreted as evidence that most source fault materials share the Earth experiment's tectonic setting. No actual T0 physical plate solve, tectonic geological history, Deep mineral inventory or HistoryStore should be generated from these conditional checks.

```text
R6_T0_CONTACT_THERMAL_TARGETED_FAIR=17_OF_17_PASS
R6_G2_G3_CONTACT_EXTENDED_FAIR=183_OF_183_PASS
T0_SOURCE_8X8_29315K_VERTEX_CONDITION=12_OF_12
T0_SOURCE_16X16_29315K_VERTEX_CONDITION=36_OF_36
RSF_EARTH_LAB_T0_FAULT_PHYSICAL_ASSIGNMENT_COUNT=0
T0_FAULT_GOUGE_MINERALOGY=null
T0_FAULT_HYDRATION=null
T0_FAULT_PORE_PRESSURE=null
T0_FAULT_NORMAL_STRESS=null
T0_FAULT_TRUE_DEPTH_AND_SLIP_SURFACE=null
T0_FAULT_MU_REF=null
T0_FAULT_ELASTIC_STIFFNESS=null
G3_PHYSICAL_MANTLE_CUT_AND_GPE_FORCES=null
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
HISTORYSTORE_PRODUCTION_AUTHORIZED=false
```
