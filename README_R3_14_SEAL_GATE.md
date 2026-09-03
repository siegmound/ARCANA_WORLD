# R3.14 local seal gate

This overlay does **not** alter the R3.14 binding, late-Cenozoic physics, adaptive clock, v0.6.1 payloads, or biology.

It adds a local post-binding seal gate for the already-successful R3.14-R2 run. The gate:

- re-verifies the R3.13 SEALED 30 Ma parent;
- verifies final R3.14-R2 source hashes;
- verifies all five exact v0.6.1 payload hashes directly on disk;
- verifies B1/B2 materialized artifact hashes and finite state;
- reconstructs the real `C1 -> C2` provider chain and enforces the C2.parent type guard;
- rebuilds the adaptive clock and requires exact equality with its stored JSON;
- rechecks exact 30 Ma environmental identity;
- preserves `high_resolution_200ka_historical_paleoclimate_sealed=false` and `c2_bridge_is_historical_glacial_chronology=false`;
- confirms biology has not advanced beyond the R3.13 30 Ma state.

On PASS it writes `R3_14_SEAL_SUMMARY.json`, which is the authority R3.15 should consume.
