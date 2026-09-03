# Next Stage Handoff — v0.6D1

Current status: binder/parity harness is ready and fail-closed. The first action when the historical source archives are mounted is to run:

```powershell
.\run_v0_6D1_windows.ps1 -D22Zip "<path>\ARCANA_WorldSim_v0_6_3D2_2_CHA1_High_Resolution_Replay.zip"
```

The verifier must report `PASS_D22_EXECUTABLE_PARENT_BINDING_AND_DEEP_OFF_RAW_REFERENCE_PARITY` before any Deep-ON run.

Then inspect the discovered runtime surfaces and implement the narrow adapter against the actual parent API. Do not infer the entrypoint from documentation alone.

Next authorization sequence:

1. D1/D2 executable parent identity + 210 Ma RAW state verified;
2. Deep-OFF D1/D2 parity including real HSG_003 -> HSG_025 event;
3. D2.2 Deep-OFF exact 89/31 parity;
4. short Deep-ON CHA-1 pilot with zero named protection;
5. actual D2.2 survivor Deep state -> D3.0A 115 seeds;
6. convergence/sensitivity comparison H0 vs HX;
7. only then authorize full 210 -> 0 Ma HX.
