# v0.6D1-R4.20-R1 — Windows Pytest Basetemp Permission Repair

The first local R4.20 attempt stopped during regression setup before any R4.20 scientific audit or external-engine activity. Pytest attempted to enumerate its default per-user temporary root (`%LOCALAPPDATA%\\Temp\\pytest-of-<user>`) and Windows returned `WinError 5 / Access denied` while creating the `tmp_path` fixture.

This is a host test-runtime filesystem issue, not a scientific-model, adapter, target-protocol, or evidence failure.

R4.20-R1 changes only the PowerShell runner so the R4.20 regression suite uses an explicit project-local pytest basetemp under `outputs\\v0_6D1_R4_20\\pytest_tmp`. The test itself, scientific implementation, frozen R4.19 parent evidence, six-cell P2 scope, 57 target-repair records, R4.2 frozen job registry, and all R4.20 governance rules remain unchanged.

The local basetemp is regression scratch space only and is not scientific evidence. R4.20-R1 still performs no external-engine execution and authorizes no canonical replay or parameter change.
