# ARCANA R6 — FAIR G2/G3 rate-state normalized mechanical stability 166/166 and 66 published fit rows

**Date:** 2026-11-21. **FAIR-tested exact source SHA:** `3c02bd0365fd0a399cd21ec957ef2187d2410ea0`.
**Decision:** `G2_G3_RSF_SOURCE_NORMALIZED_STABILITY_66_REAL_FITS_FAIR_PASS__NO_PLANETARY_FAULT_PREDICTION`.

## 1. Exact terminal evidence supplied by FAIR operator

```text
HEAD is now at 3c02bd03 docs(r6): record normalized RSF stability dev science; FAIR physical replay pending
................... [100%]
19 passed in 0.11s
TARGET_EXIT_CODE=0
...
166 passed in 0.76s
FULL_REGRESSION_EXIT_CODE=0
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/pangaea_921284.tab: OK
{
  "decision": "EARTH_LAB_NORMALIZED_QUASISTATIC_STABILITY__NO_ARCANA_FAULT_BINDING",
  "summary": {
    "fitted_model_rows": 66,
    "source_row_qualification_counts": {
      "CRITICAL_STIFFNESS_ONE_STATE_EXACT": 13,
      "CRITICAL_STIFFNESS_TWO_STATE_ROUTH_HURWITZ": 5,
      "EXCLUDED_NONPOSITIVE_DIRECT_EFFECT_OR_NEGATIVE_STATE_WEIGHT": 11,
      "EXCLUDED_SOURCE_ROUNDED_ZERO_A_MINUS_B": 3,
      "EXCLUDED_TWO_STATE_RH_THRESHOLD_NOT_IDENTIFIABLE": 1,
      "STABLE_FOR_ANY_POSITIVE_NORMALIZED_STIFFNESS_IN_SURROGATE": 33
    },
    "positive_critical_ratio_rows": 18,
    "min_positive_critical_K_over_sigma_m_inv": 0.6352322759421543,
    "max_positive_critical_K_over_sigma_m_inv": 298.85057471264366,
    "pressure_values_assigned": 0,
    "arcana_faults_assigned": 0,
    "independent_experimental_trials_inferred": null
  },
  "physical_T1": null,
  "mechanical_solve_authorized": false
}
SCIENTIFIC_ANALYSIS_EXIT_CODE=0
```

These results are supplied in the operator's pasted FAIR terminal. The authoring environment has **not** independently run FAIR commands or received the original FAIR evidence bytes; it therefore attests the *operator-reported* results, not an independent raw-data audit.

FAIR test logs:
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_RSF_STABILITY_TARGET_19.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_RSF_STABILITY_FULL_166.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_RSF_STABILITY_REAL_DATA.log`

Source and generated immutable report:
- PANGAEA raw TSV source (previously certified SHA256): `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/pangaea_921284.tab`; SHA256 `b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d`.
- Original corrected prior ingest `.../R6_G2_G3_PANGAEA921284_RAW_NEW_01/INGEST_NEW_02`.
- New pressure-normalized analysis `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_STABILITY_NEW_01/REPORT.json` and its `MANIFEST.json`.

## 2. What the experiment tells us

Of **66 published Earth laboratory inverse-model fitted rows**, processed with a one/two-state Dieterich aging and massless quasi-static spring-slider surrogate:

| Classification | Published fitted parameter rows |
|---|---:|
| Positive critical K/sigma: exact one-state relation | 13 |
| Positive critical K/sigma: two-state Routh-Hurwitz | 5 |
| Asymptotically stable at every strictly positive normalized stiffness **in surrogate** | 33 |
| Excluded: non-positive rate-direct term and/or negative state weights | 11 |
| Excluded: source-rounded `a-b=0` | 3 |
| Excluded: nonidentifiable two-state Routh-Hurwitz threshold | 1 |
| **Total** | **66** |

Of the **18** rows with an identifiable positive conditional stiffness threshold, the reported interval is `Kcrit/sigma_eff = [0.6352322759421543, 298.85057471264366] m^-1`. These are the extrema of **18 fitted rows** only; they are not confidence intervals, measured Earth-scale elastic stiffness, actual fault strengths or ARCANA geological properties. Row measurements and fitted parameters can be correlated; `independent_experimental_trials_inferred=null`. Excluded rows are retained for provenance.

The label `STABLE_FOR_ANY_POSITIVE_NORMALIZED_STIFFNESS_IN_SURROGATE` means mathematical linear stability under this **specific** aging-law, constant-normal-pressure, massless lumped slider with an assumed steady `v0` state; it does not prove earthquake immunity. In other 18 rows, a *potential critical elastic stiffness* exists under the same assumptions, but the physical stiffness `K` and per-experiment effective normal stress `sigma_eff` are unknown. A numerical threshold by itself does **not** diagnose an actually unstable fault or event probability.

## 3. Cross-component scientific authority boundary

Already established before this intervention: source original 81/289 parent nodes, 8 core+120/504 exterior triangles, full-channel external G3 **candidate** load bookkeeping, and lab-parametric RSF friction in isolation. This new analysis uses authentic Earth fit sources but **does not couple** this slider to ARCANA 5:8:11 contact geometry, deep mantle forces, crust/mantle mechanical properties or the global plate solver. Original 210 Ma regional FE mesh has single shared parent-node East/North DOF pairs, even at authentic triple node `34587`; actual slip-sided fault geometry and physical pressure/traction sources remain unresolved.

```text
LAB_RSF_SOURCE_PANGAEA921284_SHA256=b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d
LAB_RSF_SOURCE_MODEL_FIT_ROWS=66
R6_G2_G3_RSF_NORMALIZED_TARGETED_FAIR=19_OF_19_PASS
R6_G2_G3_RSF_NORMALIZED_EXTENDED_FAIR=166_OF_166_PASS
R6_G2_G3_RSF_REAL_SOURCED_STABILITY_ANALYSIS=PASS
R6_G2_G3_RSF_NORMALIZED_POSITIVE_CRITICAL_ROWS=18
R6_G2_G3_RSF_NORMALIZED_STABLE_SURROGATE_ROWS=33
R6_G2_G3_RSF_NORMALIZED_EXCLUDED_ROWS=15
R6_G2_G3_RSF_NORMALIZED_CRITICAL_RANGE_PER_M=[0.6352322759421543,298.85057471264366]
PUBLISHED_SOURCE_TEST_ROW_TO_T0_ARCANA_MATERIAL_MAP=null
PHYSICAL_PER_FAULT_EFFECTIVE_NORMAL_STRESS=null
PHYSICAL_FAULT_ELASTIC_STIFFNESS=null
PHYSICAL_FAULT_ABSOLUTE_REFERENCE_FRICTION=null
PHYSICAL_FAULT_SIDEDNESS=null
PHYSICAL_G3_MANTLE_AND_OUTER_CUT_LOADS=null
R6_PHYSICAL_MECHANICAL_SOLVE_AUTHORIZED=false
R6_PHYSICAL_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

## 4. Software integration and next scientific unit

The FAIR **166/166** gate on the exact source commit qualifies the code for engineering integration via **non-forced fast-forward** if the target R6 branch remains the source ancestor. This receipt and the top-of-ledger lines are documentation-only commits following the tested code; no new Python source/test changes. This suite is G2/G3+RSF-specific, not a claim of the entire repository global test suite passing.

The next substantive coupled-physics step is **not** more synthetic geometry or pretending the Earth lab fit covers ARCANA. Source-qualify or explicitly author-select:
1. Actual ARCANA T0 fault gouge and crust mineralogy, compositional proportions, hydration and fluid-pressure roles (PRE material configuration codes are not lithology);
2. Source contact surfaces/side DOFs and real fault slip law, while respecting original source 5:8:11 graph, triple-node ownership and conservation;
3. An appropriate effective normal stress and physical elastic stiffness `K`, or higher-resolution continuum stiffness transfer across an actual fault, plus absolute friction coefficient and applicability across in-situ pressure/T/rate;
4. Independent rock-specific G2 creep and brittle laws covering exact PRE source temperature/pressure and strain rate, and G3 mantle basal shear/normal, outer cut/GPE unique owner closure.

No mechanical T0→T1 or HistoryStore/Deep natural resource evolution until full physical source authorization.
