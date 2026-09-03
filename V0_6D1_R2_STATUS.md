# ARCANA WorldSim — v0.6D1-R2 status

**Stage:** `v0.6D1-R2 — Rebased Natural-Control Deep-Time Runtime & 210→180 Ma Pilot`  
**Verdict:** `PASS_REBASED_NATURAL_CONTROL_210_180_MACROEVOLUTION_PILOT_CANDIDATE`  
**Qualification:** `SPECIES_LEVEL_MACROEVOLUTION_CONVERGED_FOR_PILOT; MICRO_RASTER_DISTRIBUTION_NOT_SEALED`

## Authoritative pilot result

- Initial richness: **120 species**.
- Final richness: **120 species**.
- Initial population: **1823.1595076876783** WorldSim units.
- Final population: **1843.0432915992033**.
- A1 180 Ma reference population: **1843.164794921875**.
- Relative global error vs A1: **6.592103050497578e-05** (~0.0066%).
- Demographic components at 180 Ma: **133**.
- Ordinary extinction events: **0**.
- Speciation births: **0**.
- Topology support events: **1**, at 195 Ma, conservatively remapping **234.44285927615562** population units.
- HSG_025 present: **false**.
- Candidate intra-lineage pairs checked at endpoint: **34**.
- Speciation-ready pairs: **0**.
- Max intrinsic RI: **0.0**.
- Max isolation clock: **8.2270829875e6 generations**.
- Max normalized trait distance: **0.2878514101**, below the required 1.0.
- Median normalized additive variance: **0.0404942584**.

## Scope lock

This is an H0 Natural-Control pilot. Deep physical references may exist in the package, but biological Deep coupling is **OFF**. There is no random/global speciation rate and no random/global extinction rate. The runtime advances demography, migration, ecological selection, long-horizon VA homeostasis, gene flow, isolation, RI and deterministic ordinary-extinction diagnostics.

The R2 source does **not** yet materialize speciation births. This does not alter this validated pilot because zero endpoint pairs satisfy the full speciation gate. A governed speciation-birth actuator is required before extending to intervals where a pair can become ready.

## Resolution qualification

250 kyr is accepted only as the **pilot macroevolution cadence**. Cell-level spatial diffusion/occupancy is not sealed at this resolution. See `RESOLUTION_AND_CONVERGENCE_REPORT_v0_6D1_R2.md`.
