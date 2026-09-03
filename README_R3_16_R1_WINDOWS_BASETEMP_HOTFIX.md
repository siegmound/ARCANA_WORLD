# v0.6D1-R3.16-R1 — Windows pytest basetemp bootstrap hotfix

Scope: operational/test-runner only.

Root cause: `run_v0_6D1_R3_16_checks.ps1` supplied nested `--basetemp` paths under `.pytest_tmp_r316_checks`, but did not create that parent directory first. On a clean Windows checkout pytest attempted a non-recursive mkdir for the child basetemp and failed with WinError 3 during `tmp_path` fixture setup.

Repair: create `.pytest_tmp_r316_checks` explicitly before invoking pytest.

Scientific parameter changes: NONE.
Biology changes: NONE.
R3.15 seal changes: NONE.
R3.16 solver/test changes: NONE.

Post-repair verification in the development tree:
- R3.16 tests: 9/9 PASS
- R3.15 tests: 12/12 PASS
- R3.14 tests: 13/13 PASS
- focused regression: 34/34 PASS
- formal candidate audit: 310/310 PASS
