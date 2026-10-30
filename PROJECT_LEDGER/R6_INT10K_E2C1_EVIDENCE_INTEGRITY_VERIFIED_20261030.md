# E2-C1 — FAIR evidence integrity independently checked by operator (2026-10-30)

**Operator terminal stdout (source of this update)**:

```text
PYTHON_IMPORT=PASS
E2C1_EVIDENCE_INTEGRITY=PASS
E2C1_PARITY_REPORT=PASS
E2C1_MANIFEST_MEMBERS= 10
 M src/arcana_worldsim/r6/regional_geological_evolution.py
?? tests/test_r6_int10k_e2c1_frontier_projection.py
```

The post-gate check ran within activated `arcana-r6-linux` with `PYTHONPATH=$PWD/src` from existing FAIR worktree, then confirmed all ten entries in `INT10K_E2C1_FRONTIER_PROJECTION_qLSPnKHS/FILE_MANIFEST.json` by SHA256 and exact byte length, and `PARITY_RESULT.json` reported `PASS_E2C1_EXACT_FRONTIER_PROJECTION`. The prior 76-test gate and 3×7 61-record/year exact oracle parity remain operator-reported PASS. No source commit, and original 1000Y evidence remains immutable. Both modified/untracked files were intentionally left uncommitted.

**Next exact task:** E2-C1-R2 fail-closed negative test on a 1-year resumed synthetic run using a history_consumer that mutates a just-emitted `REGIONAL_SNAPSHOT` by adding a nonfinite property. The earlier projection `json.loads(_canonical(region))` rejected malformed historical data before stripping it; new selective projection might omit validation of this excluded payload. Demonstrate or disprove with same source and single synthetic replay, without writing source/evidence, and review a bounded solution that maintains strict validation and avoids full JSON snapshot duplication. The already tested happy-path SHA parity is necessary but not sufficient to promote general input semantics.

**Authority:** E2-C1 `PASS_PARITY_SOURCE_UNCOMMITTED`; pending additional fail-closed contract; noncanonical synthetic engineering only. FAIR local source branch `r6/e2c1-frontier-projection-r1-fair`, pre-optimization base `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`; GitHub documentation branch separate. No full 1000Y rerun, no canonical/solver/forward authorization.

Previous detailed report: `PROJECT_LEDGER/R6_INT10K_E2C1_FAIR_GATE_OPERATOR_RESULT_20261030.md`.
