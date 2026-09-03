# R3.4 Long-Horizon Admixture-Variance Headroom Audit

The R3.3 long run ended with 183/1380 normalized variance reservoirs at >=99% of the old 0.05 cap. A frozen-state diagnostic was therefore used to distinguish a too-low safety cap from insufficient homeostatic depletion.

With `mu` and `b` unchanged, raising the diagnostic cap did **not** produce runaway growth. At 20 Myr frozen 150 Ma geometry, a 0.10 cap yielded max `q=0.07435062666931849`, median `0.044926105016421504`, P95 `0.050065805328403004`, and P99 `0.060505372139936286`. This demonstrates a finite admixture-supported tail rather than an unstable homeostasis law.

A 0.075 cap still had one reservoir at >=99% of cap. A 0.08 cap had zero and produced the exact same maximum as 0.10. Therefore 0.08 is the minimum tested rounded non-binding safety ceiling candidate.

The audit also found 131 positive geometric contacts between different current species sharing a root lineage in the R3.3 endpoint. This violates original D3 current-species gene-flow semantics. Their effective exchange was already strongly reduced by RI, so they do not explain the cap-attractor, but R3.4 repairs this semantic mismatch independently.

Verdict: `PASS_HEADROOM_SUPPORTS_0P08_NONBINDING_SAFETY_CEILING_CANDIDATE`.
