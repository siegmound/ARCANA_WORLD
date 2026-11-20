# ARCANA R6 — Bounded source-shell dt-convergence inventory (dt 1 / .5 / .25)

**Date:** 2026-11-20. **New driver and tests published, FAIR PENDING.** An engineering-only numeric audit, no new physical contact response or 3D nonpenetration authority.

## Prior independently FAIR-SHA-verified evidence

Exactly original R6 `G2_SOURCE_SHELL_EVENT_1Y_REFINEMENT_NEW_01/REPORT.json` with digest `3a122e0ddccd0944b2478dda41abf452e00ec6f230edcb9313c0e8d3961b220c`: previous source commit `1bd6332fef2ed9ba5e326dc43e33645fdce589fd` produced 118/118 pytest and driver PASS with old manufactured fixed-T0 normal KKT replay perfect against 25y anchors (max gap drift 0m).

Four *original source* material-matched midpoint shell gap sign brackets at one-model-year cadence:
- `R6BND-T0-f679f4c97f1e7445d8d9` NEG→POS in 197–198
- `R6BND-T0-4d168aac7492e7c418de` POS→NEG in 477–478
- `R6BND-T0-1569360d5844c75db0d3` NEG→POS in 642–643
- `R6BND-T0-16d7dc72630ecb414c04` NEG→POS in 892–893

The observed time-centered gdot vs geometric instantaneous gdot residual reaches `4.9646104225e-6m/model-year`; this is measured, NOT a time convergence proof and NOT rock collision velocity.

## Scientific purpose

Before interpreting timing more precisely, test convergence and model-time step dependence of the **existing old fixed-T0 source manufactured QP/KKT** and mathematical original shell midpoint gap. This **does not** create an updated-geometry KKT, does not apply physical tectonic contact forces and does not define 3D solid-rock penetration.

**Experiment** `experiments/plate58_deforming_explore_v1/g2_source_shell_dt_convergence.py`. **Unit tests** `tests/test_r6_g2_source_shell_dt_convergence.py`.

1. Source 16×16 original plate 5/8/11, 36 original authentic R6BND-T0 edges, 39 source links, triple parent 34587, original FEG/PRE SHA-protected source nodes and plate-owned adjacent triangle faces.
2. Reintegrate **the same original fixed-T0-KKT equations** with time step `dt=0.5` (2000 steps) and `dt=0.25` (4000 steps) to model year 1000. The earlier independently verified `dt=1` report is the baseline. Run serial, do not change stiffness/drag/source inputs/physical laws. Retain all 41 prior 25-year checkpoint times plus all eight integer-year endpoints of the four source events.
3. At all original 41 time anchors, measure the SAME matched-edge source g for all 36 original edges and compare *by source ID* to the original dt=1 SHA-pinned report, measure maximum/mean deviations and sign disagreement counts. Compare `dt=1 vs .5` with `.5 vs .25` at IDENTICAL checkpoint times. Report if step differences contract, but do not silently claim asymptotic convergence order.
4. In each prior one-year window, resume the existing manufactured integrator from the dt-consistent original state at the earlier integer-year endpoint, taking separate short substeps (.5/.25) and testing parity of the computed ending gap with the uninterrupted dt-run, with the established `1e-7m` tolerance. Print sign bracket(s) within the one-year interval; if the dt change moves the sign reversal outside the prior interval, report `OUTSIDE_PRIOR_1Y_BRACKET_OR_SIGN_DRIFT`, NOT a fictitious event time or PASS of temporal convergence.
5. At T0,100,500,1000, repeat the original triple-parent 34587 three-copy vector-loop audit, which is only geometry indexing/kinematics and **NOT** a 3-body force balance.
6. All KKT normal reaction multipliers in these runs remain those of the **old T0 engineering surrogate**. Distances and sign reversals are not valid rock-volume contact complementarity tests.

The returned status `PASS_SOURCE_SHELL_ORIGINAL_DT_COMPARISON_INVENTORY__PHYSICAL_CONTACT_OPEN` means an inventory was produced with verified provenance. It **does not certify temporal convergence**: examine the difference-ratio, checkpoint sign drift, substep bracket status, and triple audit before scientific adjudication. Convergence can remain unqualified even with an exit code 0.

## FAIR command

Use clean detached checkout at the new exact commit, activate `arcana-r6-linux`, `PYTHONPATH=src:.`, `PYTHONDONTWRITEBYTECODE=1`, and `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`. Run new and all previous eight source shell/contact suites and advance to exclusive output only after pytest PASS:

```bash
BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6

python -m experiments.plate58_deforming_explore_v1.g2_source_shell_dt_convergence \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --prior-event "$BASE/G2_SOURCE_SHELL_EVENT_1Y_REFINEMENT_NEW_01" \
  --prior-differential "$BASE/G2_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_NEW_01" \
  --output "$BASE/G2_SOURCE_SHELL_DT_CONVERGENCE_NEW_01"
```

## Decision boundary

This is **the bounded last numerical refinement gate for this engineered shell proxy**. After the result: if variations are small and contract, record quantitative robustness without pretending mathematical convergence order from only 3 dt values. If not, record limitation and numeric inconsistency. In EITHER case, shift to validating the needed physically-authorized plate 3D solid boundary, or explicitly authorized natural source-shell contact law; avoid endless numerical polishing of a proxy that lacks physical signed-solid semantics.

Keep `D-024 = ACTIVE`, `physical_T1 = null`, `HistoryStore` unchanged, no geological G2/G3/G4 forces, no canon promotion.
