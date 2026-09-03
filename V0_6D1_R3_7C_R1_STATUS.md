# v0.6D1-R3.7C-R1 Status

Verdict before external rerun:

`PASS_COMPOSITE_SELECTION_REPAIR_AND_FAIL_CLOSED_EFFICACY_GATE__EXTERNAL_NEMO_SMOKE_PENDING`

Closed:

- parent R3.7C local evidence diagnosed as invalid for selection calibration;
- parent R3.7C source/test restored to sealed hashes;
- NEMO selected lifecycle repaired with `breed_selection_disperse`;
- Gaussian fitness bound as absolute;
- selected-vs-neutral numerical efficacy gate implemented fail-closed;
- no production/canonical authorization introduced.

Pending:

1. external NEMO 2.4.2 smoke (N=500, one replicate, one selection variance, two axes);
2. if efficacy gate passes, full 16-chain / 80-run R3.7C-R1 suite;
3. evidence review and `K_eff` inference in the next stage.

Validation at candidate build:

- Parent + R1 focused tests: 17/17 PASS.
- Parent R3.7C formal audit: 44/44 PASS after byte-for-byte restoration.
- R3.7C-R1 formal audit: 62/62 PASS.
- Scientific-engine regression R3.6A→R3.7C-R1: 80/80 PASS with clean exit.
- A separate full cumulative pytest attempt reached 36% with no displayed failures before the 120 s environment timeout; no full-suite PASS is claimed from that attempt.
