# ARCANA R6 — FAIR NEW02 1000-year permanently noncanonical thermal study receipt

**Date:** 2026-11-22
**Evidence status:** `FAIR_OPERATOR_TERMINAL_REPORTED_PASS__DIRECT_LOG_BYTES_NOT_INDEPENDENTLY_IMPORTED`
**Tested source Git commit:** `5ee1c320ae44a14d7e9cb9c1a23f7850bf3f6cc6`
**Branch at execution:** `r6/experimental-thermal-column-1000y-noncanonical-20261122`
**Original experiment 100-year R6 integration ancestor:** `b3f2891b2d98523f419c5e7dfc0e13d0b3f0409a`.
**Study specification:** `docs/arcana/R6_EXPERIMENTAL_NONCANONICAL_THERMAL_1000Y_STUDY_20261122.md`

## 1. Exact operator-provided FAIR execution

The FAIR operator supplied their checkout/runner stdout; the output identifies exactly:

```text
Previous HEAD position was b19d2bc9 ...
HEAD is now at 5ee1c320 ...
EXPERIMENTAL_1000Y_SOURCE_HEAD=5ee1c320ae44a14d7e9cb9c1a23f7850bf3f6cc6
EXPERIMENTAL_1000Y_AUTHORITY=EXPERIMENTAL_NONCANONICAL_ONLY
Targeted new 1000y tests: 30 passed in 1.87s
Selected R6 regression: 368 passed in 3.16s
FAIR_1000Y_NUMERICAL_STUDY=PASS
FAIR_1000Y_REFERENCE_SENSITIVITY_CASES=8
FAIR_1000Y_PERMANENT_NONCANONICAL=TRUE
CANONICAL_PHYSICAL_T1=NULL
FAIR_1000Y_TARGET_30=PASS
FAIR_1000Y_SELECTED_368=PASS
FAIR_1000Y_EXPERIMENTAL_STUDY=PASS
```

The **368 selected** suite includes the 30 new targeted cases and the earlier 338; do not add these to claim 398 independently run tests. This is not a repository-wide `pytest` claim.

The run script first verifies pinned original T0 materials, source manifests and model anchor through the unchanged 100-year pilot called in-memory; the actual second experiment advances the explicitly synthetic heat equation for 1000 Julian years. The 100-year source experiment, policy and its original FAIR evidence remain immutable.

## 2. Numerical results from the exact operator stdout

Source-authenticated original **T0 model** parent `R6G1D-R089-C359`, plate 8. Actual numerical column is **1000 m synthetic depth**, not a real original crustal thermal profile. Reference bulk ocean crust properties are authorial specialist values, not cellwise observations. Constant parameters nominal: `rho=2890 kg/m3`, `Cp=1000 J/(kg K)`, `k=2.2 W/(m K)`, `Q=3e-7 W/m3`.

Three grids: 50/100/200 cells, time steps 1/0.25/0.0625 Julian year, total 1000/4000/16000 explicit finite-volume steps.

| FV cells | Insulated cosine exact error [K] | Fixed-temperature manufactured exact error [K] |
|---:|---:|---:|
| 50 | 0.0005902039906686696 | 0.0003150850501469904 |
| 100 | 0.00014759446935386222 | 0.00007879403989363709 |
| 200 | 0.000036901334851791034 | 0.00001969993144257387 |

Error refinement ratios insulated: `3.9988218613641786`, `3.999705429265755`. Fixed-temperature: `3.9988437015327434`, `3.999711375814938`. These are consistent with the expected observed ~second-order error trend for this *particular* co-refinement (halving spatial step, quartering the time step); this is **not** a full independent order study over arbitrary steps.

Eight one-factor authored/reference parameter-endpoint sensitivity runs passed.

For the matched initial synthetic cosine profile, the **maximum absolute difference at five sampled cell centres** between fixed-temperature and insulated 1000y cases was `3.1144334887656555 K`. Do not report this as a max over all cells or a natural geological temperature prediction.

The fail-closed FAIR report verification also printed PASS for conservation, provenance and governance assertions. The standalone stdout does **not** include every numerical residual, manifest hash or the eight detailed sensitivity outputs; those are stored in the external source report/manifest and have **not been independently read or byte-hash-verified in this authoring environment**.

## 3. Original failed NEW01 evidence preserved

At previously tested `b19d2bc90982f2172322efed933f3db38efb7d21`, FAIR showed **29/30 targeted** and `TypeError: Object of type bool is not JSON serializable` during strict JSON serialization of the Dirichlet report. The numerical method was not changed in the repair: the module now converts NumPy-origin report scalars to Python `float` and `bool`, with strict nested JSON roundtrip regressions. Do not overwrite or reclassify this first failed attempt.

The new FAIR runner uses `NEW02` non-overwrite destinations outside the repository:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_EXP_THERMAL_1000Y_TARGET_30_NEW02.log
  R6_EXP_THERMAL_1000Y_FULL_368_NEW02.log
  R6_EXP_THERMAL_1000Y_NONCANONICAL_NEW_02/
    REPORT.json
    MANIFEST.json
```

These paths are reported from the committed runner, **not a claim of direct shell access to FAIR or an imported source SHA manifest**.

## 4. Acceptance and strict scope

```text
EXPERIMENTAL_1000Y_NUMERICAL_VALIDATION = FAIR_OPERATOR_REPORTED_PASS
SELECTED_R6_REGRESSION = 368/368 FAIR_OPERATOR_REPORTED_PASS
TARGETED_TESTS = 30/30 FAIR_OPERATOR_REPORTED_PASS
SYNTHETIC_1000Y_SOURCE_ANCHORED_STUDY = PASS_OPERATOR_REPORTED
EXPERIMENTAL_NONCANONICAL_ONLY = TRUE
CANONICAL_HISTORY_CREATED = FALSE
HISTORYSTORE_MUTATIONS = 0
NATURAL_ARCANA_T0_THERMAL_PROFILE_QUALIFIED = FALSE
PHYSICAL_T1 = NULL
D_024 = ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED = FALSE
```

The new 1000-year tested code is eligible for **software-only integration** into the R6 integration branch after an exact Git ancestry/unchanged-code review. The receipt and later ledger updates are documentation changes **after** the tested commit; they do not change tested numerical code. A successful original-geometry/source readback and synthetic numerical PDE benchmark are not physical G2/G3 force/material closure, historical resources/Deep, or real WORLD_HISTORY.

## 5. Next actual science objective

Per the permanent D-024 startup strategy, avoid automatically extending synthetic years as if they add new physical authority. The meaningful next track is qualifying a **real, minimal regional T0 to T1 physical case**, with:
- source-authenticated natural/authorially selected initial thermal stratification and material properties with valid ranges;
- the complete G2 rheology/poromechanics/fault state and constitutive applicability;
- physically supported G3 basal/cut traction, pressure, GPE and boundary histories;
- a finite qualified time interval with stability, conservation, material/energy and restart accounting.

If any required law or source is absent, keep regional/physical `T1` **blocked**, retain UNKNOWN and continue independent numerical research in a separate noncanonical lane. Canonical WORLD_HISTORY requires a newly qualified and expressly author-ratified production run; experimental records are permanently noncanonical.
