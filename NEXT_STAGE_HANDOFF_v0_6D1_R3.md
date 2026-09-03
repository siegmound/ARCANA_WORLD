# NEXT STAGE HANDOFF — v0.6D1-R3 → v0.6D1-R3C

## Parent status
R3 has closed the barrier-history binding and re-enabled event-driven persistent-vicariance fission using the exact surviving D3.2C provider. Tests and formal audit pass. The 210→150 Ma production replay has not yet been run to completion.

## Next stage
**v0.6D1-R3C — Checkpoint/Resume Closure & H0 210→150 Ma Local Production Replay**

## Required work
1. Add production checkpoint serialization for the full R3 state: populations, traits, V_A, species/component identity, RI/contact clocks, founder/extinction/vicariance persistence state, registry, event ledger, and elapsed age.
2. Prove continuous vs checkpoint→restore execution parity over a short interval.
3. Keep external chunk size non-biological; preserve fixed internal biology/transport cadence.
4. Execute H0 210→150 Ma locally using `run_v0_6D1_R3_windows.ps1`.
5. Audit richness, fission/speciation/extinction ledgers, population/resource envelopes, V_A homeostasis, gene-flow moment closure, and event-history sensitivity.
6. Do not cross CHA-1 as an ordinary macrostep; later 70→60 Ma closure must splice to the high-resolution CHA-1 provider.

## Current recommended command
```powershell
.\run_v0_6D1_R3_windows.ps1 -EndAgeMa 150 -Threads 12
```

## Scope locks
- Deep biological coupling remains OFF for H0.
- fission is demographic, not speciation.
- no global/random speciation or extinction rates.
- D3.2C derived event clusters are not independent geological observations.
- initial 210 Ma fragmentation remains grandfathered.
