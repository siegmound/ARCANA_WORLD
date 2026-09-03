# ARCANA WorldSim v0.6D1-R4.11 — CDMetaPOP Population-Metric Extraction Repair Contract

R4.11 repairs **evidence extraction only** after R4.10 confirmed the broad `"ind" in filename` selector collision.

## Frozen rules

- Parent: R4.10 SEALED with `R43_R49_CDMETAPOP_POPULATION_METRIC_FILENAME_SELECTOR_COLLISION_CONFIRMED`.
- No engine rerun in R4.11. Retained runtime outputs are re-extracted first.
- All five R4.7 CDMetaPOP jobs are repaired symmetrically: J03, J06, J09, J15, J20.
- R4.7/R4.8/R4.9 historical evidence is preserved and never overwritten.
- Population total is read from CDMetaPOP's native `summary_popAllTime.csv`.
- Start population = total component of first `N_Initial` row.
- Because pinned CDMetaPOP defines `GrowthRate[i]=N_Init[i+1]/N_Init[i]` and writes rows for i=0..T-1, final population = total component of the last written `N_Initial` row × its `GrowthRate`.
- The internal lifecycle chain is checked row-by-row.
- Extracted initial population must match the configured sum of PatchVars `N0` for each retained replicate.
- Legacy occupancy metrics derived from the broad filename selector are not promoted by R4.11.
- Frozen R4.4 adjudication policy and domain authority remain unchanged.
- The corrected 20-pair J09 dynamic/neutral matched-control metric is recomputed from retained R4.7/R4.8/R4.9 summaries.
- No majority vote, no canonical write, no R3 replay, no parameter change, Deep OFF.

If any retained summary is missing, malformed, or fails lifecycle/configured-N0 integrity, R4.11 blocks and identifies the missing runtime evidence; it does not silently rerun engines.

## R4.11-R1 clarification — engine-effective initial N0

The retained-runtime integrity comparison must use CDMetaPOP's **engine-effective** initial `N0`, not the raw sum written in `PatchVars.csv`. Pinned 3.08 selects the first `|` climate knot and then forces `N0=0` on every patch with `Natal Grounds == 0` before initialization. The raw configured sum, engine-effective sum, and amount removed by this rule must all be retained in audit evidence. This clarification does not alter any engine run or scientific parameter.
