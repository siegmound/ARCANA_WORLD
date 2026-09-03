# R3.9 — Canonical 150→66 Ma H0 Continuation

Run from the R3.8 SEALED checkpoint using:

```powershell
.\run_v0_6D1_R3_9_precha1_continuation.ps1
```

The run performs exactly 672 ordinary 125 kyr biology steps and materializes the complete 66.0 Ma **PRE_CHA1** restartable state. It does not execute the CHA-1 pulse and does not continue to ages younger than 66.0 Ma.

The full result becomes authoritative only after the runner reports the governed PASS verdict and the resulting JSON+NPZ pair is audited/sealed.
