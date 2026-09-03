# v0.6D1-R3.7C — Selection Participation Calibration Contract

R3.7A introduced the minimum-distance mapping

`dh = dz / sqrt(2 K_eff)`

without authorizing `K_eff`. R3.7C measures the missing dynamic quantity with a genetically explicit external oracle.

## Allowed inference
The selected-vs-neutral excess divergence may be used to estimate candidate participation:

`K_eff = Delta z_adapt^2 / (2 Delta S_adapt)`.

The analysis must report:
- all per-chain estimates;
- dependence on `N`;
- dependence on trait axis;
- dependence on `selection_variance`;
- dispersion/CV rather than only a grand mean;
- adaptive-S retention after reconnection.

## Forbidden shortcuts
R3.7C may not:
- set `K_eff=64` merely because the oracle uses 64 QTL;
- promote the previous static median ~59.62 without dynamic evidence;
- fit a scalar to make ARCANA reproduce ARCANA;
- alter `mu`, `b`, `q*`, VA ceiling, migration, RI/speciation, fission/coalescence or paleogeography;
- write any NEMO result directly into canonical WorldSim state.

## Promotion rule
The raw NEMO run may only move the stage to `...K_EFF_RULE_REVIEW_REQUIRED`. A subsequent evidence-closure stage decides whether:
1. a scalar participation number is supported;
2. trait-specific participation is needed;
3. selection-strength/state-dependent participation is required.

Production binding remains fail-closed until that review is complete.
