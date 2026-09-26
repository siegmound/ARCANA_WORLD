# R6 rift-initiation and event-guard law binding

Status: **precommitted before V3 t0 evaluation**. Scope is the minimum synthetic global-base rift-progress/event guard only. This is not a rift simulation, full lithospheric model, or plate-splitting law.

## Selected state: cumulative normal extension

Use `E` in metres: `dE/dt = max(0, (vB - vA) · nAB)`, with velocity in m/year and positive sign denoting opening. E starts at zero as an explicit ARCANA synthetic t0 initial condition. No effective width is needed, so this is extension displacement—not strain, beta, fault slip, or damage. Non-opening motion stalls progress; no healing/reset rule is introduced.

Strain is not selected because R6 has no governed deforming-zone width. Stretching factor beta is not selected because initial lithospheric/crustal thickness and a spatially coherent stretching model are unavailable. Damage/maturity is not selected because rheology and weakening parameters are unbound.

The operational `RIFT_INITIATION` transition occurs when accumulated E reaches threshold `theta` under opening. The bounded ARCANA model envelope is **5–30 km**, with no probability distribution and no canonical threshold draw. This is an explicit authorial model assumption, not a literature-derived universal threshold. Earth studies document diverse extension amounts and show strong setting/rheology dependence; those observations are context only, not a transferable onset criterion ([Buck 1991](https://doi.org/10.1029/91JB01485), [Brune et al. 2023](https://doi.org/10.1038/s43017-023-00391-3), [Boone et al. 2018](https://doi.org/10.1002/2017TC004575)). The minimum 5 km is the model's declared earliest activation criterion. It does not claim that natural faults cannot initiate at less extension.

Weak-zone susceptibility stays UNKNOWN and is not numerically assigned. This minimal event envelope does not require an explicit weakness field; threshold uncertainty stands in for unresolved aggregate resistance solely for this coarse event guard. The guard uses the most event-permissive threshold, 5 km. A future weakness/rheology modifier requires separate authority.

## Event guard and remaining limit

For the constant initial Euler segment, calculate the fastest positive local edge-opening rate in the 30-pair boundary graph. The earliest modeled activation bound is `theta_min / u_open,max`. This is a model-bound event horizon, not a natural lower bound. If the candidate threshold is approached, a solver must analytically bracket/localize the crossing and must not step over it. The initiation event does not itself authorize a plate split.

The scientific guard can be computed, but the first numerical `dt` remains unbound: no solver/runtime is pinned and no verified vertex-displacement, rotation, topology, event-localization, or restart-equivalence tolerance exists. Therefore no first-interval execution contract is created and no evolution runs. P09 split/lineage is deferred until before any topology-changing realization; P03 motion renewal is not exercised within the conditional first segment.
