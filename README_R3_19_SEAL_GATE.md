# v0.6D1-R3.19 Seal Gate

This delta seals the canonical R3.19 H0 present-day biology checkpoint produced after the R3.19-R2 exact endpoint-support reconciliation repair.

Canonical checkpoint SHA-256:
- JSON: `658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71`
- NPZ: `f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406`

Canonical boundary:
- biology age: 0 ka
- species: 134
- components: 295
- population: 1217.2506240828814
- exactly one 125 kyr biology macrostep
- exactly two 62.5 kyr transport substeps with phase-specific forcing
- one exact endpoint support-reconciliation remap event
- exact 0 ka inaccessible population mass: 0
- q peak: 0.047601695825828454 < 0.08
- Deep biological coupling: OFF

The seal gate rehydrates R3.18 SEALED, independently reruns the full 125 ka -> 0 ka R3.19 macrostep with exact 0 ka topology, and requires the replayed runtime state to be bit-exact with the canonical checkpoint. The R3.8 constant-forcing equivalence gate is rerun and must remain bit-exact.

No scientific parameter, biology cadence, transport cadence, gene-flow cadence, lifecycle cadence, or Deep coupling change is introduced by this seal patch.

Run:

```powershell
.\verify_v0_6D1_R3_19_seal_gate_patch.ps1
.\run_v0_6D1_R3_19_sealed_checks.ps1
```

Expected verdict:

`PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED`
