# ARCANA WorldSim v0.6D1-R3.21 — Final Seal Audit

This is a read-only final audit overlay for the already-materialized R3.21 outputs.
It does not execute biology and does not modify H0 or CHA-2.

Run from the WorldSim root after R3.21 REV4 has produced `outputs/v0_6D1_R3_21`:

```powershell
.\run_v0_6D1_R3_21_seal.ps1
```

The audit fails closed unless it finds the exact SEALED R3.19 checkpoint hashes and verifies:

- 134 present species;
- 295 present components;
- 348 historical registry species;
- 2925 historical events and the exact event histogram;
- exact population closure;
- parent-complete, acyclic ancestry;
- no extinct species resurrected at 0 ka;
- generic functional-phenotype fork still unmaterialized;
- Deep OFF / no human target / no biology advancement / no H0-CHA2 mutation declarations;
- output-manifest hash/size closure;
- bit-exact preservation of all four R3.19 reduced genetic-state arrays;
- canonical reduced-state geometry `(295,3)`, `(295,3)`, `(295,295,3)`, `(295,3)`.

On success it writes `outputs/v0_6D1_R3_21_SEAL/` and prints the SEALED verdict.
