# R3.12 SEALED checks basetemp hotfix

Purpose: avoid Windows/Hermes pytest `tmp_path` failures caused by access denial under
`%LOCALAPPDATA%\\Temp\\pytest-of-<user>`.

Scientific effect: none.

The hotfix replaces only `run_v0_6D1_R3_12_sealed_checks.ps1` and passes an explicit
project-local `--basetemp` to pytest. No scientific source, checkpoint, authority,
parameter, manifest, or result is changed.

Apply this archive over the current R3.12 folder and rerun:

```powershell
.\verify_v0_6D1_R3_12_basetemp_hotfix.ps1
.\run_v0_6D1_R3_12_sealed_checks.ps1
```

Expected pytest result: `44 passed`.
Expected formal audit: `218/218` PASS.
