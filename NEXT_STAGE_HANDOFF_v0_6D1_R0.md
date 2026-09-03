# Next Stage Handoff — v0.6D1-R0 -> v0.6D1-R1

## Current state

`PASS_RECOVERY_AUDIT_WITH_PARTIAL_RAW_SURVIVAL_AND_EXECUTABLE_HISTORY_STILL_MISSING`

The original historical solver/state bytes have not yet been recovered. Later runpacks retain D1 metadata and the real D2.2->D3.0A boundary; File Library retains at least four D2.2 RAW outputs; D2.T core SQLite/NetCDF/frozen NPZ and executable D1/D2/D2.2 packages remain missing.

## Exact next stage

`v0.6D1-R1 — Local Archive Recovery Scanner & Source Rehydration Gate`

1. Run the R0 scanner over all likely local archive roots.
2. Promote packages only on exact recorded SHA-256.
3. If `arcana_rawfirst.sqlite` / frozen D2 NPZ / physical cube are found, inspect schema and establish an immutable RAW H0 oracle.
4. If D1/D2/D2.2 source packages are found, bind them and rerun Deep-OFF parity.
5. If only D2.2 RAW outputs are found, keep them as validation evidence; do not infer the 210->66 Ma trajectory.
6. If original D2 runtime is irrecoverable, prepare an explicitly rebased paired baseline `H0-R/HX-R`; never call it the original D2 replay.

## Hashes to search

- D1: `75a8bd4e90103e20ff308ef052871289eb3a608a558288abf1622c36a3b7fb1c`
- D2.T: `3b236d3a0a3a048b300d1fcd818006bedc93130c6a17abf9378635f0b6d76aa8`
- D2.1: `e751668c7a8232cf67b791b93312ad89050d8a7b2fd8cd4f9da4422fc0bc8828`
- D2.1.1: `918b5693efb0db81628efaba3f7f63b6365c1f975aba36d123401c2aede52905`
- D2.2: `42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8`
