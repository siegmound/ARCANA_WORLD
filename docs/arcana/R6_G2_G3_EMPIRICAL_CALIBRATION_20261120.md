# ARCANA R6 — G2/G3 empirical calibration: identifiability analysis

Date: 2026-11-20. Parent commit: dd769427440316201acbef0b0dbaff30328e9427.

Decision: CALIBRATION_MATH_IMPLEMENTED_AND_SYNTHETICALLY_TESTED__ARCANA_PHYSICAL_PARAMETERS_NOT_IDENTIFIABLE.

## Scientific result

This step implements actual parameter-regression algorithms for independent
laboratory creep and observed basal shear, with independent held-out groups
and matrix-identifiability checks. Synthetic manufactured datasets confirm
recovery of known inputs. **No actual ARCANA rock law or basal-drag coefficient
has been empirically calibrated.** The T0 PRE and Euler geometry contain
thermal, density and kinematic priors, not independently measured stress or
mantle traction. Resulting physical parameter fields must remain null.

## G2 — independent laboratory stress/strain fitting

Module: experiments/plate58_deforming_explore_v1/g2_g3_empirical_calibration.py
Function: fit_g2_dislocation_laboratory

Mathematical fit, under explicitly LAB TRIAXIAL differential stress
convention, in Pa and s^-1:

    log(epsdot) = log(A) + n*log(sigma_differential/Pa)
                  - E/(R*T) - P*V/(R*T)
                  + r*log(fH2O/fH2O_ref) [if measured]

Needs unique source-referenced laboratory stress/rate/temperature/pressure
measurements and separate experimental groups for training and holdout.
A water-sensitive model requires measured fugacity and a reference.
Rank-deficient and ill-conditioned fits fail closed. Outputs include
train and holdout log-rate residuals and laboratory support intervals.
The fitted activation volume may have either sign and requires source
review. A fit alone does NOT verify original measurements, ARCANA mineral
identity, fault fabric, pore state, or any temperature extrapolation.
The stress invariant has not been converted to original SHELLS/ASPECT.

Source screen: the T0 5:8 crust ranges 280–1051.558 K, while GT95
quartzite experiments cover about 1173.15–1373.15 K (0/81 source
samples in the reported calibration interval). The broader wet-quartz
cross-study screen yields 18/81 in one study's T range and 9/81
in an intersection of different study windows; this does NOT
establish a valid single wet-quartz flow-law calibration.
The Hirth–Kohlstedt dry-olivine reference remains an Earth analogue,
not the R6 mantle mineralogy.

## G3 — basal drag parameter

Function: fit_g3_linear_basal_drag

Candidate equation: tau_b = beta * (v_deep_mantle - v_lithosphere).
Beta units: Pa s/m. All vector measurements in the same local East/North
frame, with observed traction in Pa and independent train/holdout groups.
The estimator rejects non-identifiable zero relative motion and
nonpositive beta. The result does not calibrate basal NORMAL pressure,
the mechanical LAB or external N/S tractions.

The source 5:8 Euler opening is only 0.1575 m/year. For unobserved
hypothetical accommodation widths 10, 100 and 300 km, the
nominal strain-rate proxy is 4.99087e-13, 4.99087e-14 and
1.66362e-14 s^-1. These values are valid sensitivity drivers, not
observed strain or inferred stress. No independent deep-mantle
velocity / basal traction provider has been qualified. Beta therefore
remains NULL. Thermal LAB is not the mechanical LAB.

## Verification and continuation

Local synthetic tests: 10 passed in 0.05 s. They cover
fit recoverability with and without water, P/T collinearity,
absent water, train/holdout leakage, missing observations,
synthetic basal drag recovery, missing deep-mantle velocity,
zero relative motion, and current T0 no-fit assessment.
FAIR environment verification has NOT yet run. After checking out
the exact published commit in the clean isolated FAIR checkout:

    PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
      python -m pytest -q tests/test_r6_g2_g3_empirical_calibration.py

Next scientific requirement: recover individual traceable laboratory
stress/rate measurements in a valid domain relevant to R6 lithology,
then demonstrate applicability to the full T0 column or stop.
Separately obtain physically founded mantle reference flow and
basal traction, or maintain G3 as unidentifiable. Do not set unknown
water to dry, fit unknown tractions to force-balance zero, or
promote an isolated good fit to ARCANA physical history.

Cited existing ARCANA repository sources:
- docs/arcana/R6_FIRST_DEFORMATION_MODEL_DECISION_FAIR_20261118.md
- docs/arcana/R6_PLATE58_G2_G3_AUTHORIAL_EXPERIMENT_DECISION_20261119.md
- docs/arcana/R6_G2_G3_PAIRED_PHYSICAL_SCENARIO_DECISION_20261119.md
- experiments/plate58_deforming_explore_v1/rheology_envelope.py
- experiments/plate58_deforming_explore_v1/wet_quartz_screen.py
- docs/arcana/research/B6N8J_LAB_BASAL_BOUNDARY_DECISION.json

Public literature:
- GT95: https://doi.org/10.1016/0040-1951(95)00011-B
- Olivine activation volume: https://doi.org/10.1029/2018JB015853
- ASPECT rheology: https://aspect-documentation.readthedocs.io/en/stable/parameters/Material_20model.html
- Bird et al. basal forces: https://doi.org/10.1029/2007JB005460

MECHANICAL_SOLVE_AUTHORIZED=false
SOLVER_RUNS=0
PHYSICAL_T1=null
D_024=ACTIVE
