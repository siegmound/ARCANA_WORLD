# Handoff v0.6D1-R1 → v0.6D1-R2

Continue from `v0.6D1-R1 — World 1 210 Ma Canonical Biological Rebaseline & Paired H0/HX Replay Initialization`, verdict `PASS_210MA_CANONICAL_REBASELINE_AND_PAIRED_H0_HX_INITIALIZATION_CANDIDATE`.

The old lost D1/D2 trajectory is no longer the production baseline. R1 created a new deterministic 210 Ma species-level state from the exact surviving 120 D1 species metadata and the A1 210 Ma guild population/carrying-capacity rasters. The allocation is cellwise-conservative: each guild's species sum exactly equals the A1 population and K in every cell. Common-state semantic SHA-256 is `f0b15dc9dd3df479df1f48e286a64e28dc29c62674acc9792c4297049e600452`.

Deep hereditary initialization is `Z_X=0`, `V_A^X=0.045`, where 0.045 is exactly `sqrt(0.002 / 0.9876543209876544)` from the final D3.3A zero-selection variance homeostasis. Physiology starts at zero. Physical Deep exists in both H0 and HX. Photo-Deep is additive 5% on E/th and zero on p/I/N. Initial 210 Ma exposure remains entirely negligible; there are no pre-labelled Deep-adapted species.

H0 and HX reference the same common state, same physical environment and same base seed `917231`; the only allowed branch difference is Deep biological coupling OFF vs ON (plus branch labels). Future stochastic execution must use event-keyed common random numbers, not sequential draw-order parity.

## Exact next stage

`v0.6D1-R2 — Rebased Natural-Control Deep-Time Runtime & 210→180 Ma Pilot`

### R2 objectives

1. Build a production deep-time runtime operating on the 120-species raster representation rather than inventing a D3-at-210Ma state.
2. Use the modern validated causal components where representation-compatible: environmental provider, mutation/VA homeostasis, migration/contact, gene flow, RI/speciation authority, ordinary turnover, adaptive clock and checkpointing.
3. Run **H0 only first** from 210→180 Ma with Deep biological coupling OFF.
4. Preserve RAW-FIRST products: species state, spatial populations, event ledger, contact/gene-flow diagnostics, trait/VA state and fingerprints.
5. Use event-keyed deterministic RNG rooted at seed `917231`.
6. Compare the H0 pilot with old D2 outputs only as a plausibility/reference envelope; do not force the old HSG_003→HSG_025 event or any old survivor identity.
7. Check timestep convergence before HX.
8. If H0 passes, R3/HX starts from the exact same R1 common state and uses the same keyed stochastic stream.

### Do not

- reconstruct lost D2 events;
- force HSG_025 to appear;
- force 31 future CHA-1 survivors;
- introduce global speciation/extinction rates;
- let Deep directly alter RI/speciation;
- use `reference_population` as K or physical N;
- use D3 drift-equivalent individual counts as an energy conversion;
- change the R1 common initial state separately for H0 and HX.
