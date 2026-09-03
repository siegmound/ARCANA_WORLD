# R3.16 Seal Gate

This overlay seals the completed canonical R3.16 250 ka -> 125 ka run.

Canonical evidence expected locally:
- checkpoint JSON SHA-256: `aaf0bab510b4bcb5fbf77707ad66201515342cf8eb25b687e8f15952d2afca32`
- checkpoint NPZ SHA-256: `de0ef549d2fc74f1546e320b3fc3e0bc2f7ca7cbf5ebac464976494ad4055593`
- biology endpoint: 125 ka
- biology steps: 1 at inherited 125 kyr cadence
- C2 500-y exposure intervals consumed: 150
- C2 500-y intervals left to the exact 120 ka environmental restart: 10
- biology advanced to 120 ka: false

The sealed audit does not merely inspect the stored checkpoint. It revalidates the live R3.15/R3.14 authority chain, reconstructs the C2 exposure integral, independently replays the single 250->125 ka macrostep, and requires restart-state equivalence against the stored canonical checkpoint.

No scientific parameter, biology cadence, gene-flow cadence, lifecycle cadence, or Deep coupling is changed by this patch.

Run:

```powershell
.\verify_v0_6D1_R3_16_seal_gate_patch.ps1
.\run_v0_6D1_R3_16_sealed_checks.ps1
```

Successful seal verdict:

`PASS_R316_CANONICAL_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__125KA_PRE_120KA_RESTART_BOUNDARY_SEALED`

R3.16 deliberately does **not** claim a 120 ka biological state and does **not** promote the C2 bridge to historical high-resolution glacial chronology.
