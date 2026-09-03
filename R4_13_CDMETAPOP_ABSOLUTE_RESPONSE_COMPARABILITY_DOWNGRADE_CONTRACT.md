# v0.6D1-R4.13 — CDMetaPOP Absolute-Response Comparability Downgrade & Symmetric Readjudication

## Trigger
R4.12 SEALED confirmed that `population_agent_response_ratio` fails neutral invariance under the matched CDMetaPOP control because the benchmark starts from an artificial ~0.5 K state and exhibits robust upward relaxation even without historical forcing.

## Authorized action
R4.13 creates a new evidence namespace and downgrades only CDMetaPOP evidence rows whose selected metric is exactly `population_agent_response_ratio` from `DIRECT/NORMALIZABLE` to `PROXY_ONLY` across all five frozen CDMetaPOP jobs. Parent R4.3 mappings and the R4.11 matrix remain immutable historical evidence.

## Scientific meaning
`PROXY_ONLY` retains directional/context evidence but is not eligible as a primary adjudicative row and cannot by itself establish `STRUCTURAL_DISAGREEMENT` or a promoted global agreement. R4.13 does **not** promote the J09 matched-control ratio into a global replacement metric because equivalent ARCANA causal targets have not been defined for every CDMetaPOP window.

## Readjudication
All 75 frozen window×domain cells are recomputed with the unchanged R4.4 policy, five frozen discordance classes, domain authority precedence, and no majority vote.

## Prohibitions
No engine execution. No canonical write. No R3 replay. No parameter change. Deep biological coupling remains OFF.
