# Handoff — v0.6D1-R3.3 → Long-run promotion audit

## Current authority
Use the R3.3 package and common R1 210 Ma initial state. Do not continue from R3/R3.1/R3.2 150 Ma checkpoints.

## Next execution
On Windows:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_v0_6D1_R3_3_windows.ps1 -EndAgeMa 150 -Threads 12
```

Upload `local_runs\v0_6D1_R3_3` after completion.

## Promotion gates at 150 Ma
1. `q > 0.05` count = 0.
2. VA reservoirs ≥99% ceiling must no longer show the R3.1/R3.2 ~13% long-horizon attractor.
3. Component ledger must close: `initial + fissions - coalescences - extinct components = endpoint`.
4. Coalescences must be same-current-species only.
5. Population and first/second moments must close for every coalescence.
6. Speciation events remain governed by D3.0C + D3.2B and are not undone by coalescence.
7. Ordinary extinctions remain deterministic and unforced.
8. If passed, promote the 150 Ma H0 checkpoint and proceed 150→90 Ma.
