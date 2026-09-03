# R3.19 Phase-Aware Transport Promotion Audit

R3.18 measured a non-roundoff difference between the two 62.5 kyr transport forcing phases (`global max abs difference = 1.5816467428221057`). Reusing one environment for both transport substeps is therefore not authorized for the final recent macrostep.

R3.19 is deliberately implemented as a binding around SEALED R3.8 rather than a replacement runtime. Only two symbols are temporarily rebound during the one-step call:

1. `r38.bp.environment_at` supplies the R3.18 full-macro effective forcing to the unchanged non-transport R3.8 operators.
2. `r38.r34._migration_subcycled_r3` delegates sequentially to the original SEALED migration function once with phase-1 forcing and once with phase-2 forcing, each for exactly 62.5 kyr.

No demography, selection, gene-flow, variance, pair-clock, lifecycle, speciation, extinction, fission or coalescence implementation is replaced.

The mandatory promotion test uses a real restartable WorldSim state and proves that the generalized path is bit-exact to R3.8 when both transport forcings are identical. Production remains fail-closed on exact-present support consistency.


## R3.19-R2 endpoint-support repair

The phase-aware transport forcing remains time-integrated over two 62.5 kyr phases. Discrete `accessible` topology is now bound to the exact 0 ka provider endpoint. After phase 2, any population on cells that are accessible in the phase-average forcing but inaccessible at exactly 0 ka is conservatively reconciled with the existing SEALED `remap_to_land` operator. This is an operator-order/topology binding repair, not a parameter or cadence change. The constant-forcing case with identical endpoint support remains bit-exact to SEALED R3.8.
