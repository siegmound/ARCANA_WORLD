# v0.6D1-R4.12 — CDMetaPOP Metric-Repaired Precision & Absolute-Response Comparability Diagnosis

## Purpose
R4.12 is a diagnostic-only stage after the R4.11 population-metric extraction repair. It does not rerun an engine, alter R4.11 classifications, change ARCANA, or authorize replay.

The stage tests whether CDMetaPOP's absolute `final_population / initial_population` response can legitimately remain `NORMALIZABLE` for historical population persistence when the experiment initializes population at approximately `0.5 * K_start` rather than mapping ARCANA's start population state.

## Frozen neutral-invariance rule
R4.12 reuses the R4.4 neutral factor `1.05`; no new numerical adjudication threshold is introduced.

A purportedly NORMALIZABLE absolute response fails neutral invariance when the matched neutral-forcing control has a robust non-neutral central distribution:

- robust upward relaxation: neutral-control q10 > 1.05;
- robust downward relaxation: neutral-control q90 < 1/1.05.

If this happens, the absolute population-response metric is not permitted to remain adjudicative merely because it produced a R4.11 structural disagreement. R4.12 only diagnoses and freezes a later comparability amendment; it does not rewrite R4.11.

## Precision
The 20 corrected paired dynamic/neutral effects are summarized with the existing q10/q90 policy and a fixed-seed bootstrap median interval. The bootstrap is descriptive only and cannot reclassify the parent result.

## Symmetry
If neutral invariance fails, the follow-up scope is all five frozen CDMetaPOP jobs and all evidence rows that select `population_agent_response_ratio`. The follow-up may downgrade that metric to `PROXY_ONLY` in a new evidence namespace and readjudicate the 75 cells. It may not silently modify the R4.3 mapping or historical R4.11 outputs.

## Prohibitions
- no engine execution;
- no automatic additional replicates;
- no matched-control metric global promotion;
- no majority vote;
- no canonical parameter changes;
- no canonical replay;
- Deep biological coupling remains OFF.
