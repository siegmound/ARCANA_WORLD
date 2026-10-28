# R6-INT10K E0 — FAIR host/runtime and source-input diagnostic (2026-10-28)

**Status:** `R6_INT10K_E0_FAIR_HOST_RESOURCES_OBSERVED__INPUT_PATH_UNRESOLVED__SOURCE_CHECKOUT_STALE`. **Evidence level:** `OPERATOR_REPORTED_DIAGNOSTIC`, from terminal output supplied in conversation; this report has not accessed FAIR or verified full original files. **No simulation executed, no solver invoked.**

## Observed FAIR commands and values

- Checkout: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV`.
- Actual FAIR `git rev-parse HEAD`: `ec79bf8954a4922f84249fbe23e2657bc5beee23`. This is an **older engineering baseline**, not the current integration source.
- Remote branch `r6/multiphysics-integration-20261026` was independently observed at `2c8a087e5544678ae5f66b6ad693e901a6d97301` on GitHub at the time of this documentation update. Current remote HEAD must be rechecked on FAIR; do not assume that the local checkout is at this revision.
- The **exact one checked default directory** `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV/outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03` returned `NOT_FOUND` for `RESULT.json`, `MANIFEST.json` and `RESULT.json.sha256`.
- The output does **not** show those files are absent from alternative FAIR roots, evidence directories or the original Windows workspace.
- Python `3.12.14` (GCC `15.3.0`), NumPy `2.5.3`, pytest `9.1.1` from `arcana-r6-linux`.
- `free -h`: Mem total `1.0 TiB`, used `34 GiB`, free `21 GiB`, cache/buffers `961 GiB`, **available `972 GiB`**; swap `8.0 GiB` total, `1.0 GiB` used.
- `df -h` for the project mount `/home`: `22 TiB` total, `5.9 TiB` used, `15 TiB` available (`29%` used).
- These values are **node / mounted-filesystem observations**, not proof of Slurm/job cgroup quota, accessible allocation, personal disk quota, or permission for a large multi-year run.
- The `git status --short -uno` command printed no tracked modifications in the supplied output, but untracked/ignored results were not included in that check.

## Adjudication

**Do not classify as `INPUTS_LOST` or `ENGINE_FAILURE`.** Current blocker: `SOURCE_INPUT_PATH_UNRESOLVED`, plus `FAIR_CHECKOUT_STALE`. The repository does not store the required result bundle at the default path, and nothing supports synthesizing replacement inputs while claiming the historic T0 source identities.

The correct next operation is **read-only discovery** of directories named `MATERIAL_RHEOLOGY_PROVIDER_*` under the relevant FAIR project/evidence paths; capture the actual absolute directory, three-file SHA256/size, manifest/sidecar and hash-bound two-support identity. Check the Windows originating source if no suitable FAIR copy exists. **No copying/re-creating/rewriting source evidence without a separately recorded provenance-preserving transfer.**

Separately `git fetch --no-tags origin r6/multiphysics-integration-20261026` can acquire the remote object into the local object database **without moving HEAD/index/worktree**; require exact `2c8a087e5544678ae5f66b6ad693e901a6d97301` (or explicitly re-adjudicate newer HEAD), and pin reviewed source to exact commit via `git archive` in a new external evidence directory for later preflight. Do **not** reset/rebase/checkout the old worktree automatically; do not use `PYTHONPATH` from the stale source tree while claiming new-source parity.

Actual host/job memory quota, output/inode/personal quota, available CPUs, scheduler/supervisor permissions and proposed resource ceilings remain **UNKNOWN**. Design/short-run cost measurements are still prerequisites before any long integration test.

## Next bounded decision

`R6_INT10K_E0_INPUT_DISCOVERY_AND_EXACT_SOURCE_PIN` — read-only path and identity scan, then isolated exact-source verification. If candidate absent: `BLOCKED_INPUT_NOT_LOCATED` (not `INPUTS_LOST`). If candidate found but SHA/loader fails: preserve failure and stop without automatically correcting it. New streaming runner/short-run phases remain pending until provenance and runtime are bound. Earlier ENG10K success and GEODYN-3C FAIR archive PASS are not the same engine.

**Gates unchanged:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`. This report is documentation only, not a physical-forward authorization.
