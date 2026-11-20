# ARCANA R6 — FAIR one-model-year shell opening event refinement (SHA verified by operator)

**Date:** 2026-11-20. **Tested source:** `1bd6332fef2ed9ba5e326dc43e33645fdce589fd`. `118 passed in 0.84s`, `PYTEST_EXIT_CODE=0`, `DRIVER_EXIT_CODE=0`. Source report from `G2_SOURCE_SHELL_EVENT_1Y_REFINEMENT_NEW_01` status `PASS_SOURCE_SHELL_1Y_EVENT_BRACKET_REFINEMENT__PHYSICAL_SOLID_CONTACT_OPEN`. Operator ran `sha256sum REPORT.json`: `3a122e0ddccd0944b2478dda41abf452e00ec6f230edcb9313c0e8d3961b220c`, **exactly matching MANIFEST `REPORT.json` SHA**. Previous SHA-verified 25-year original shell diagnostic replay: `max_abs_error=0.0m`. Raw report bytes not independently retrieved by assistant.

## Source R6BND one-year sign brackets (not exact geophysical contact dates)

| Original source boundary | Original 25y bracket | 1y observed bracket | Modeled matched shell midpoint opening |
| --- | --- | --- | --- |
| `R6BND-T0-f679f4c97f1e7445d8d9` | 175–200 | **197–198** | NEGATIVE→POSITIVE |
| `R6BND-T0-4d168aac7492e7c418de` | 475–500 | **477–478** | POSITIVE→NEGATIVE |
| `R6BND-T0-1569360d5844c75db0d3` | 625–650 | **642–643** | NEGATIVE→POSITIVE |
| `R6BND-T0-16d7dc72630ecb414c04` | 875–900 | **892–893** | NEGATIVE→POSITIVE |

All four brackets have a definite sign reversal between consecutive integer model years, with **no sampled near-zero integer** in the windows. This does **not** prove a particular zero-crossing year or exclude additional sub-year crossings.

## Temporal numerical consistency

Original fixed-T0 KKT time-stepping and the identical matched edge/face gap definition were used; no new KKT solve on the updated g. Max observed |centered 1-year trajectory rate minus instantaneous kinematic geometric gdot| by bracket ranges: `3.672569e-6`, `4.964610e-6`, `3.110524e-6`, `2.861215e-6` m/model-year. Max `4.964610e-6 m/model-year` (~0.004965mm/model-year). **No qualifying tolerance for dynamic rate compatibility was set in the prior gate**, so the result is a measured discrepancy, not a validated time-discretization convergence order.

The 4 transitions are mathematical signs of the **material-matched original 2D shell boundary midpoint opening**; they are not rocks colliding/interpenetrating or full edge-face/solid Signorini constraints. `D-024=ACTIVE`, `physical_T1=null`, no new physical solver, canon or HistoryStore edits.

## Next gate: bounded timestep convergence — then stop diagnostic loop and adjudicate source authority

Design `R6_G2_SHELL_SOURCE_DT_CONVERGENCE_GATE`: compare the **same old fixed-T0 manufactured KKT trajectory** at dt=1,0.5,0.25 model years, using exactly authentic FEG/PRE, plate 5/8/11 material views and original R6BND IDs. Replay dt=1 SHA-pinned 25y checkpoints from previous receipt, compare g and rate at identical physical model times, give separate g=0 brackets at .5 and .25 within four previously verified one-year source intervals, report deviations of crossing brackets and temporal derivative discrepancies. The time step must only change a **previously existing engineered solver**; no new physical contact law or KKT. No scientific PASS of convergence should be implied by successful execution alone: report measured changes and indicate insufficiency if monotonic convergence fails.

After this bounded check, refocus on authentic source-provider physical 3D plate volume or explicitly authorized shell-contact dynamics; do not continue endlessly refining numeric midpoint proxy without source contact authority.
