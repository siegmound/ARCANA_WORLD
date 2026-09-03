# v0.6D1-R3.18 Seal Gate

This delta seals the canonical R3.18 readiness artifacts produced locally.

Canonical evidence SHA-256:
- readiness envelope: `45f42200faa315ad7fe69f4fa8bcb1019c8f0c8dcb90fc2a18488bd40a9df58a`
- integral bundle: `54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70`
- summary: `189007565f3f70c89b73e71bb4c23e9339bb392c550408a08b0d43c60f71317a`

The seal gate rehydrates the R3.17 SEALED parent and independently rebuilds the entire R3.18 exposure bundle. Every integral array must match the canonical bundle exactly. The 125 ka biology state must remain exactly unchanged.

No scientific parameters, biology cadence, transport cadence, gene-flow cadence, Deep coupling, or lifecycle rules are changed.

Run:

```powershell
.\verify_v0_6D1_R3_18_seal_gate_patch.ps1
.\run_v0_6D1_R3_18_sealed_checks.ps1
```

Expected sealed verdict:

`PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED`
