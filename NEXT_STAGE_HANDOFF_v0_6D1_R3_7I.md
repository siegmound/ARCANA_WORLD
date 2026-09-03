# Next-stage handoff after sealed R3.7I

R3.7 is closed for the legacy whole-trait admixture/coalescence variance failure mode. The segregation-aware closed-loop runtime is now the canonical World-1 production authority.

## Next natural stage
`v0.6D1-R3.8 — Canonical 150 Ma Continuation Checkpoint & Post-Promotion Long-Horizon Replay Handoff`.

The next stage should materialize a restartable 150 Ma checkpoint containing the **full** reduced genetic state (`VA_within`, ancestry/LD covariance, neutral segregation-potential matrix, adaptive coordinate) together with all demographic/speciation/lifecycle state required by the runtime. The current R3.7H JSONs intentionally expose summaries and canonical arrays but do not serialize the complete reduced-state matrices required for an exact restart.

After checkpoint equivalence is demonstrated against a direct 210→150 sealed replay, continue H0 beyond 150 Ma using the promoted runtime. LOW/HIGH remain validation sentinels at release gates; they are not separate canonical worlds.
