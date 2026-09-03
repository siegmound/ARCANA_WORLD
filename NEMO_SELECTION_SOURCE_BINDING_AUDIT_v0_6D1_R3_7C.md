# v0.6D1-R3.7C — NEMO 2.4.2 Selection Source Binding Audit

Verified against the current NEMO 2.4.2 public source/documentation on 2026-08-28:

1. NEMO 2.4.2 is the current release and provides explicit quantitative-trait selection.
2. `LCE_Selection_base` registers the mandatory `selection_trait` and `selection_model` parameters and the optional `selection_fitness_model`, `selection_variance`, `selection_trait_dimension`, and `selection_local_optima` parameters.
3. The life-cycle event name used in init files is `viability_selection`.
4. The documented Gaussian model is stabilizing selection around local phenotypic optima; patch-specific optima and selection variance are supported.
5. `relative_local` is a documented fitness interpretation.

R3.7C intentionally uses the explicit `viability_selection` event instead of inventing a custom selection backend.

No NEMO output is treated as canonical authority automatically.
