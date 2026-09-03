# R3.16-R1 Windows basetemp repair audit

Classification: INFRASTRUCTURE / TEST HARNESS PORTABILITY REPAIR.

Observed Windows failure:
`FileNotFoundError [WinError 3]` while pytest created the `tmp_path` fixture beneath `.pytest_tmp_r316_checks\\r316`.

Cause: parent `.pytest_tmp_r316_checks` was not materialized before nested `--basetemp` was supplied.

Fix: one PowerShell statement:
`New-Item -ItemType Directory -Force -Path $bt | Out-Null`

No scientific engine, config, test semantics, provider, cadence, checkpoint, or sealed authority was modified.
