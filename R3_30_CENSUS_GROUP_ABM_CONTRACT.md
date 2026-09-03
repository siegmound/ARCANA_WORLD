# ARCANA WorldSim — v0.6D1-R3.30
## Census-Equivalent Calibration, Weighted Group ABM & Late-Pleistocene Community History

### Purpose
R3.30 converts the sealed R3.27 effective-population anchor and the sealed R3.28/R3.29 relative demographic/community trajectories into an uncertainty-aware **census-equivalent posterior ensemble** and a computationally bounded **weighted residential-group ABM** for the two retained HUMAN_0KA lineages.

### Canonical restrictions
- Parent R3.29 must be SEALED and unchanged.
- R3.28, R3.27 and R3.23 remain immutable authorities.
- Deep biological coupling remains OFF.
- No unique human identity is assigned.
- No language, religion, agriculture, city/state, ethnicity or named culture is materialized.
- Census values are calibrated posterior equivalents, not archaeological observations.
- R3.28 relative population trajectories are preserved; R3.30 does not rerun biological demography.

### Census semantics
R3.27 state variable `effective_population` supplies the 200 ka effective-size anchor. R3.28 begins from that anchor (with its documented restart floor) and supplies the relative population trajectory. R3.30 samples an uncertainty prior for `Ne/N_total` and converts the 200 ka anchor into a total census-equivalent value, then propagates only the sealed R3.28 relative trajectory.

The `Ne/N_total` prior is deliberately broad. It is not tuned to either candidate and is not interpreted as a universal human constant.

### Group ABM semantics
The ABM is a **weighted group-agent model**. A stored agent represents one or more equivalent residential camps. It is not a person-level simulation. At the eleven sealed R3.29 spatial anchors, agents retain:
- represented people;
- represented camp count;
- mean camp size;
- deme/grid anchor;
- mobility/settlement mode;
- network access;
- cultural-precondition stock;
- resource stress;
- inter-lineage exchange opportunity;
- CHA-2 disruption pressure.

Fission/fusion and settlement changes are derived from changes in calibrated group counts and sealed community state. They are diagnostics of community reorganization, not literal archaeologically observed events.

### Evidence calibration envelope
- Hunter-gatherer camp sizes commonly average roughly 25–35 individuals, with substantial seasonal and ecological variation.
- Cross-cultural dispersed residential groups can be ~14 individuals and aggregated groups ~40 individuals on average/median scales; larger active/periodic networks are nested above camps.
- `Ne/N` is definition- and history-dependent; empirical syntheses show broad uncertainty. R3.30 therefore uses an ensemble prior rather than a fixed conversion.

### Outputs
R3.30 produces census-equivalent trajectories, weighted group-agent anchors, community-history summaries, CHA-2 group-exposure diagnostics, sensitivity analysis, an integrated audit and one final seal.
