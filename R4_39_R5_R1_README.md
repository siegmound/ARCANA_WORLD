# ARCANA WorldSim v0.6D1-R4.39-R5-R1
## Runner newline packaging repair

The original R4.39-R5 overlay was packaged with literal `\n` sequences in:

- `run_v0_6D1_R4_39_R5_bounded_preflight_and_reseal.ps1`
- `tools/r4_39_r5_postrepair_reseal_audit.py`

This caused PowerShell to see the runner as one physical line and would also
have caused a later Python syntax failure in the post-reseal audit.

R5-R1 replaces only those two orchestration files with newline-correct versions.

It does not modify:
- the R4.39-R5 scientific module;
- configs;
- contracts;
- source authority manifest;
- canonical payloads;
- any R4.39 evidence.

Apply this overlay over the already-expanded R5 tree, then rerun:

```powershell
.\run_v0_6D1_R4_39_R5_bounded_preflight_and_reseal.ps1
```
