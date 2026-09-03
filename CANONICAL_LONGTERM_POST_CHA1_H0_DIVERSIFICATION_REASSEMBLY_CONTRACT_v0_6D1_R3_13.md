# v0.6D1-R3.13 — Long-Term Post-CHA1 H0 Diversification & Ecological Reassembly Contract

## Purpose
Continue the sealed World-1 H0 state from **46.0 Ma** to the already-existing **30.0 Ma late-Cenozoic provider boundary** using the unchanged R3.7I/R3.8 ordinary production runtime.

R3.13 is an observation/continuation stage. It does not calibrate richness, guild composition, extinction, or diversification.

## Parent authority
The stage MUST load the local materialized R3.12 SEALED boundary:
- 46.0 Ma, `POST_CHA1_20MY_DIVERSITY_RECOVERY`;
- 104 species, 223 components;
- checkpoint JSON SHA-256 `6189f16fd3d7b390ad33afb57eaa36fef0bdbcf7f1498fa7396d3d1f81843269`;
- checkpoint NPZ SHA-256 `92b410ce3258c44ba0f4b911776628d880fbe5a5fe3be3b9b6fe13dc34973948`;
- CHA-1 completed exactly once;
- lifecycle thaw completed exactly once;
- Deep biological coupling OFF.

## Canonical window
`46.0 Ma -> 30.0 Ma`, 125 kyr biology cadence, **128 steps**.

The 30 Ma endpoint is not arbitrary: the inherited `arcana_worldsim.late_cenozoic` environmental stack is explicitly scoped to **30 Ma -> 0 Ma**.

## 30 Ma handoff gate
R3.13 remains on the current R3 barrier/environment provider through the final 30 Ma step. It MUST NOT activate the late-Cenozoic provider inside this stage.

At exactly 30 Ma, the current provider and `late_cenozoic_environment_state` must be exactly identical for:
- land support;
- temperature;
- aridity;
- browse, low, wetland and total edible forage.

This endpoint identity is a PASS gate for the canonical R3.13 run.

## Scientific authority unchanged
No changes are authorized to mutation supply, variance depletion, q ceiling, K_CENTER semantics, migration, gene flow, RI/speciation gates, founder/vicariance/reconnection persistence, ordinary extinction, paleogeography, biology cadence, or check cadences.

## No target-driven reassembly
PASS does not require rising richness, positive net diversification, recovery of any guild, a specific population, or an Earth-analogue endpoint.

## Guild-scope guard
The active R3.7I/R3.8 runtime stores a fixed guild per component and ordinary speciation inherits the parent's `guild_id`. R3.13 does **not** activate the separate historical trophic-mode/cross-guild operator. Therefore a guild already absent at 46 Ma is not expected to be recreated during R3.13. This is an inherited scope limitation, not a target or a narrative lock.

## Canonical endpoint
A successful run produces a restartable checkpoint at **30.0 Ma**, event side `POST_CHA1_36MY_LONG_TERM_REASSEMBLY`, ready for a separately governed late-Cenozoic provider/adaptive-clock binding stage.
