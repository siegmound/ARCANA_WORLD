# v0.6D1-R3.7B — World-Interval Neutral Shadow Binding Contract

R3.7B adds a non-canonical bridge for the existing WorldSim interval semantics.

`advance_neutral_world_interval_shadow(...)`:
1. consumes an already-derived finite-step migration transition;
2. applies the R3.7 exact genic segregation mixture;
3. reuses D3.3A exponential drift retention over the WorldSim interval;
4. transfers that expected drift loss into pairwise neutral `S`;
5. never writes canonical state.

This is deliberately different from the generation-scale NEMO B2 recursion. B2 uses migration and drift every generation; WorldSim currently applies a finite interval migration operator followed by its D3.3A non-flow operator. R3.7B preserves that existing operator order rather than silently changing cadence semantics.

## Selection gate
The shadow bridge does **not** move the adaptive latent coordinate under directional selection because dynamic `K_eff` is not yet externally calibrated.

Any short World-1 replay containing non-zero selected trait response remains diagnostic-only until the selection calibration gate is closed.

## Authority
- canonical write: forbidden
- R3.5 replacement: forbidden
- mean migration semantics: unchanged
- D3.3A drift authority: reused
- selection latent displacement: intentionally absent/pending
