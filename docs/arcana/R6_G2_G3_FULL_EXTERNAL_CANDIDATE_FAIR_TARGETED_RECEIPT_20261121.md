# ARCANA R6 — G2/G3 full core/exterior external candidate: FAIR targeted receipt

Date: 2026-11-21. Source commit: `1f7af785d83f26c5e4853227b280e01dcceae9c6`.
Branch: `r6/g2g3-core-external-complete-candidate-20261121`.
Evidence provenance: **FAIR operator's terminal text pasted into the chat**. This authoring environment did not rerun pytest or read/hash the local FAIR log bytes.

## Observed FAIR result

```text
platform: linux
Python: 3.12.14
pytest: 9.1.1
venv: /home/jlpfritas/miniforge3/envs/arcana-r6-linux
checked-out commit: 1f7af785...
collected: 38
result: 38 passed in 0.28s
PYTEST_EXIT_CODE=0
log: /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/G2G3_DEBUG/targeted.log
```

Test files:
- `tests/test_r6_g2_g3_full_external_candidate.py` — 14 cases, all PASS, including explicit core+exterior P1 candidate force/channel partition and 11 negative cases plus paired channel and facet coverage.
- `tests/test_r6_g2_g3_core_exterior_source_runner.py` — 10 cases, all PASS.
- `tests/test_r6_g2_g3_source_core_exterior_stitch.py` — 14 cases, all PASS.

A previous synthetic-fixture node-coverage defect in the new intervention was fixed in commit `1f7af785d83f26c5e4853227b280e01dcceae9c6`. This receipt confirms that the *targeted regression* now passes on FAIR.

## Qualification, no promotion

```text
TARGETED_FAIR = PASS_OPERATOR_REPORTED_38_OF_38
FULL_G2_G3_REGRESSION_AT_1f7af785 = PENDING
CANDIDATE_LOAD_CHANNELS_FULLY_IMPLEMENTED = true
PHYSICAL_TRACTION_AND_LITHOLOGY_SOURCED = false
PHYSICAL_FAULT_LAW_RATIFIED = false
MECHANICAL_SOLVE_AUTHORIZED = false
physical_T1 = null
D_024 = ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```

The code's full-channel candidate residual is **not** physical equilibrium or a solved state. No actual original-FEG candidate scenario containing all physical external loads has been executed here. No canonical/HistoryStore promotion.

Next: test the existing G2/G3 regression suites **on the same development branch**, preserve shell stdout/stderr and exit code, and review any failing test before merging this intervention back into `r6/multiphysics-integration-20261026`.
