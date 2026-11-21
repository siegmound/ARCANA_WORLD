# ARCANA R6 — FAIR G2/G3 + PANGAEA RSF complete software regression

**Date:** 2026-11-21.
**Exact FAIR-tested source commit:** `b2a9fc1140941881bdccb63f51a0f676fcd23fb3`.
**Decision:** `G2_G3_LAB_RSF_FAIR_147_147_PASS__SOURCE_ONLY_EARTH_ANALOGUE__PHYSICAL_T1_NO_GO`.

## Operator-provided FAIR receipt

The operator ran the full R6 G2/G3 suite including the corrected PANGAEA921284 rate-and-state laboratory adapter on the FAIR Linux workstation at the checked-out Git SHA `b2a9fc1140941881bdccb63f51a0f676fcd23fb3`:

```text
HEAD is now at b2a9fc11 docs(r6): attest FAIR corrected PANGAEA 66-row ingest and 13/13 test, full regression pending
........................................................................ [ 48%]
........................................................................ [ 97%]
...                                                                      [100%]
147 passed in 0.71s
FULL_REGRESSION_EXIT_CODE=0
LOG=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_RSF_FULL_147_b2a9.log
```

The log and source original data were retained on FAIR; this GitHub-side authoring environment only received the operator's terminal output, did **not** independently rerun tests or obtain the logged bytes. No evidence of other unrelated entire-repository tests being run: **147** is the defined G2/G3+RSF regression suite, not a global all-repository test claim.

**Earlier FAIR source ingestion** at `07b311c452ff0bc0bc85bdfee75f00b40da43075`:
- Corrected targeted RSF test: 13/13 PASS.
- PANGAEA `10.1594/PANGAEA.921284` raw official TSV SHA256: `b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d`.
- Original and second `INGEST_NEW_02` immutable reports: 66 fitted parameter rows, not 66 independent raw instrument observations or 66 ARCANA geological sites.
- 10 source event labels, 10 distinct sample labels, 23 source event+sample+experiment IDs, 57 one-state and 9 two-state fitted rows; 20 negative, 3 zero, 43 positive fitted `a-b` signs.
- **All 66** immediate and steady differential shear stress fields `null` because Table 2 per-test effective normal pressure is not independently bound; nominal study 10 MPa must not be assigned across all historical Tohoku cases (previously cited 7 MPa exception).
- Dimensionless `delta_mu` describes a conditional model response, with fitted parameter source and explicitly assumed steady initial state; this is not absolute frictional strength or physical fault traction.

## Engineering/software qualification

```text
R6_G2_G3_FULL_EXTERNAL_ENGINEERING_BASELINE=FAIR_134_134_PASS
R6_G2_G3_RSF_CORRECTED_FULL_REGRESSION=FAIR_147_147_PASS
R6_G2_G3_RSF_CORRECTED_FULL_REGRESSION_EXIT=0
PANGAEA921284_PUBLISHER_MODEL_FITS_IMPORTED=66
PANGAEA921284_SOURCE_SHA256=b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d
LAB_RELATIVE_FRICTION_MODEL=ENGINEERING_PASS_WITH_LAB_SUPPORT_LIMITS
RSF_PRESSURE_SCALED_DELTA_TAU=null
RSF_ABSOLUTE_TRACTION=null
RSF_FAULT_NODE_AND_SIDE_MAPPING=null
G2_PHYSICAL_MATERIAL_PT_HYDRATION_LAW=null
G3_BASAL_TANGENTIAL_AND_NORMAL_FULL_SOURCE=null
G3_OUTER_CUT_PHYSICAL_FORCE_SOURCE=null
G3_PHYSICAL_GPE_EQUILIBRIUM_AUTHORIZED=false
G3_FAULT_SLIP_SOLVER_COMPATIBILITY=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

## Integration decision / further work

Source regression 147/147 on the exact reviewed SHA warrants **engineering integration** via a non-force fast-forward into `r6/multiphysics-integration-20261026` only if main is still the tested ancestor and no history divergence exists. The documentation-only receipt commit after that SHA does not change Python source or the tests; it is not a new 147-test run at the receipt commit hash. Source data do **not** ratify a planetary fault material. The first scientific follow-up is source-binding actual T0 gouge/mineralogy/hydration, test-level effective normal stress and reference friction, authentic plate5/8/11 fault contact and slip-side configuration plus mantle/cut/pressure/GPE physical forcing, then nonlinear solver evaluation. No physical solve without independent joint authorization, and no HistoryStore/T1 production.
