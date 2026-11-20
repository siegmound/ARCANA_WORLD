# 2026-11-20 — R6 shell dt comparison: fractional restart checkpoint bug

**First FAIR source commit:** `5e2ef26bbaa595feb3ba037d2ef0c05da3b0626d`. `132 passed in 0.87s`; driver failure `DTC_SOURCE_LOCAL_RESTART_FAILED`; no DT convergence inventory produced. Terminal log `/tmp/arcana_r6_dt_v7lpEc.log`.

**Cause confirmed from connected GitHub source:** the existing old manufactured T0-KKT `integrate()` implementation casts `checkpoints=set(map(int,checkpoints))`, then records snapshots under `int(round(year))`. Requests for fractional local restart endpoints (e.g. 197.5) are cast to 197 before matching. The integrator returns its **actual endpoint displacement/gap** as `result["state"]` at every step regardless of snapshot selection. The experimental driver incorrectly demanded `len(result["snapshots"])==1` even for half/quarter-year steps.

**Correction:** source shell dt diagnostic now uses `advance_source_restart_state(...)` calling the unchanged original `integrate(..., dt, steps=1, initial=..., checkpoints=())`, requires `max_scaled_complementarity <1e-8` and finite valid source shapes, recovers endpoint material velocity by the exact original update identity `velocity = (u_next-u_previous)/dt`, and uses returned true next state for subsequent local substeps. It no longer asks original integrator to represent fractional snapshot keys. The original solver, parameters, scientific source inputs and existing FAIR evidence are untouched. New test coverage for `dt=.5`, `dt=.25`, and strict complementarity failure.

**Code commits:** `a7a2fd3d45043b4b42d87544e3581260e2ba8824` (driver), `870dafba7450d3c7c461e0c58430c61042be5289` (regression). **Full FAIR suite and source rerun PENDING.**

A successful rerun still indicates **engineering numeric comparison inventory only**, not physically authorized closed rock-solid nonpenetration or automatic DT convergence. `D-024=ACTIVE`, `physical_T1=null`, no new moving KKT, no canon/HistoryStore changes.
