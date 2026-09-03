# ARCANA v0.6D1 — Executable Historical Binding

This package extends v0.6D with a strict executable-parent binder. It intentionally does **not** reconstruct D1/D2/D2.2 from exported summaries.

Current-session verdict: `PASS_EXECUTABLE_BINDER_AND_REFERENCE_PARITY_GATE_CANDIDATE__ACTUAL_HISTORICAL_HX_PILOT_BLOCKED_SOURCE_BYTES_NOT_MOUNTED`.

On Windows, once the canonical D2.2 ZIP is locally available:

```powershell
.\run_v0_6D1_windows.ps1 -D22Zip "C:\path\ARCANA_WorldSim_v0_6_3D2_2_CHA1_High_Resolution_Replay.zip"
```

A true historical Deep-ON pilot remains fail-closed until D1/D2 pre-CHA1 executable state is also available and inspected.
