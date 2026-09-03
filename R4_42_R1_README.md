# ARCANA WorldSim v0.6D1-R4.42-R1
## Multi-Step Clock Validation Repair

Live R4.42 produced exactly four passing transitions for each of J14, J18,
and J21: the first transition for each frozen seed.

This is the signature of reusing the R4.41 single-transition clock helper.
That helper intentionally validates only `-1 -> 0`.

R4.42-R1 keeps R4.41 SEALED and untouched. It introduces an R4.42-local clock
validator that requires, for transition `ti`:

- before clock: `ti-1`
- after clock:  `ti`

using only:
- `Model._set_t()`
- `Model._set_comm_t()`
- `Model._set_spp_t()`

No movement, demography, ageing, default walk, interpolation, canonical
modification, or gate weakening is introduced.

Run:
```powershell
.\run_v0_6D1_R4_42_R1_multistep_clock_repair_and_reseal.ps1
```
