# R3.7A — NEMO 2.4.2 B2 Isolation → Divergence → Reconnection Protocol

## Goal
Independently calibrate the lifecycle of segregation potential `S` under fragmentation and reconnection, rather than fitting ARCANA to itself.

## Reference phases
1. `CONNECTED_BURNIN`: 250 generations, four-patch symmetric chain, edge exchange 0.03/generation.
2. `FRAGMENTED`: 400 generations, central edge removed; two connected pairs remain.
3. `RECONNECTED`: 550 generations, original chain restored.

The benchmark is generation-scale and is not a World-1 125-kyr migration schedule.

## State chaining
Each phase is run in NEMO 2.4.2. Final allele frequencies from `.qfreq` initialize the next phase. Phase boundaries therefore preserve allele-frequency state but reset Hardy-Weinberg/LD state. Only allele-frequency-derived segregation potential `S` is authoritative across boundaries.

## Primary comparison
For each pair and phase compute

`S_ij = 2 sum_l a_l^2 (p_il-p_jl)^2`.

Compare NEMO with the reduced-order R3.7A trajectory under the same migration geometry and with the D3.3A-derived drift transfer.

## Default pilot
- population sizes: 500, 2000;
- replicates: 2;
- loci per trait: 64;
- two trait axes;
- independent chains: 8;
- three sequential phases per chain: 24 NEMO executions.

## Fail-closed rules
- exact NEMO executable `nemo2.4.2` required;
- no mutation or selection parameter is invented for this B2 drift/migration calibration;
- results are evidence only;
- no canonical state or production parameter is written automatically.
