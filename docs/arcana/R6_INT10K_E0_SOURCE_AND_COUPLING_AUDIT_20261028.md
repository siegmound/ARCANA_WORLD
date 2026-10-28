# R6-INT10K E0 — Source/coupling/retention preflight (2026-10-28)

**Decision:** `R6_INT10K_E0_STATIC_SOURCE_AUDIT_PASS__FAIR_INPUT_RUNTIME_PENDING__NO_EXECUTION`.  
**Reviewed Git commit:** `d3bb38756d71f39d0e4756c19040068dfa1d5673`. **Method:** read-only exact-revision source inspection; **no code execution, no FAIR or original input inspection, no new timing/RSS/disk measurements**.

## 1. What actually runs

Primary candidate call graph:
`scripts/r6_regional_geological_evolution.py:43-75` → `load_verified_r6_initial_columns` + `run_regional_segment` (`regional_geological_evolution.py:705-764`) → `run_unified_microdomain` / `continue_unified_microdomain` AND `advance_region`.

The unified path `unified_multiphysics_microdomain.py:390-521` calls `evaluate_reduced_state_column` (benchmark dry-olivine rheology), `solve_layered_interface_increment` (MAXWELL mechanics), `pure_shear_thermal_step` (reduced 1D thermal, adaptive stability-limited internal steps), `run_hydrology_scenario` (two-column auxiliary surface/hydrology), and `_advance_reservoirs` (synthetic Deep stores). The regional **3×3** path separately executes annual runoff, routing, erosion/deposition and material bookkeeping in `advance_region`.

The regional wrapper passes **zero precipitation to unified hydrology** (`regional_geological_evolution.py:723-732`); regional rainfall is handled in the distinct 3×3 surface domain. No 3×3 erosion or surface loads are coupled back into the unified subsurface PDE. No Deep→thermal/mechanics, thermal→Deep energy or mechanics→Deep energy transfer exists (`unified_multiphysics_microdomain.py:751-759`). Regional cross-boundary hydraulic connectivity is experimental, mechanical continuity UNKNOWN and Deep interfacial exchange DISABLED (`regional_geological_evolution.py:170-186`). This is partial same-clock numerical co-execution, **not full closed-loop multiphysics**.

ASPECT, gFlex, Fastscapelib, ShellSet and other previously tested external solvers are **not called** in the inspected regional→unified runtime path. Their separate benchmark results must not be counted as active providers in INT10K.

## 2. Source input: identified interface, host availability UNKNOWN

`geological_surface_microdomain.py:19-22,38-131` requires `RESULT.json`, `MANIFEST.json`, `RESULT.json.sha256` in the selected input directory; it validates hashes, `UNCoupled_reference`, T0 73-node columns `R6G1D-R091-C028` and `R6G1D-R091-C029`, cells [91,28]/[91,29], plate-pair [5,11], shared-interface boundary ID/length and original payload source identities.

CLI default `outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03` was not present as a GitHub repository directory at the reviewed revision. **This does not show it is absent on FAIR or Windows.** The actual path/sha256/provenance of the three files, runtime package versions, FAIR job quota and output filesystem remain **UNKNOWN** and cannot be guessed.

Host read-only acceptance: verify exact source commit and each SHA256, invoke the reviewed `load_verified_r6_initial_columns` without writing the inputs, record source/support identities and Python/dependency versions, inspect true host/job memory/disk limits, and bind a separate new external evidence root. Missing file/source identity ⇒ `BLOCKED_INPUT_UNAVAILABLE`.

## 3. Source-backed engineering blockers

| Finding | Source | Consequence |
|---|---|---|
| Regional CLI `--years` sets both total plan and segment | `scripts/r6_regional_geological_evolution.py:43-74` | Cannot safely plan 10k and resume smaller segments through the current CLI without configuration-identity mismatch |
| Unified CLI uses default `UnifiedConfig(duration_years=3)` | `scripts/r6_unified_multiphysics_microdomain.py:47-76` | `--segment-years 10000` is not a valid 10k plan |
| Unified default hourly hydrology vs regional wrapper yearly | `unified_multiphysics_microdomain.py:31-35`; `regional_geological_evolution.py:723-732` | Hourly for 10k would entail 87,660,000 hydrology ticks per case; yearly is a different explicit approximation, not equivalent numerical convergence |
| Regional `advance_region` copies whole prior state and appends yearly record + full nine-cell snapshot | `regional_geological_evolution.py:357-375,610-630` | 10k years retain 10k copies in history; multi-segment copy/serialization can grow superlinearly |
| Checkpoint embeds full regional history + unified checkpoint | `regional_geological_evolution.py:633-648` | Checkpoints are not compact frontier snapshots |
| Unified resume copies `saved["records"]`; cumulative metrics rescan all records | `unified_multiphysics_microdomain.py:343-383,625-668,782-850` | Long-running and repeated resume modes need streamed history and cumulative sufficient statistics, not full recursive archives |
| Regional runner writes whole result and checkpoint JSON at completion | `scripts/r6_regional_geological_evolution.py:80-103` | Need bounded, atomic per-segment output and recoverable incomplete status |

The adaptive thermal kernel chooses internal substep based on `_diffusion_stability_limit` and geometry (`functional_development.py:289-368`). Do not claim thermal substeps, walltime, memory or 10k viability before measuring actual input/runtime behavior.

## 4. Implementation contract for next step

Use **new opt-in** runner, not edits to closed `r6_int3_eng10k.py` or GEODYN-3C. Keep a fixed planned duration independent of segment duration. Introduce a versioned **frontier-only continuation checkpoint** with current states, mechanical viscous state, current surface+water+sediment inventory, Deep reservoirs, cumulative exact balances, source/config/implementation identities, monotonic time, and previous segment digest. Retain old full-history format and readers for 3y/10y regression, not silent reinterpretation. Stream immutable per-year/per-segment state/flux/event records in external evidence, not in each checkpoint. Preserve exact-query support without interpolation and retain material/support IDs, event causes, anomalies, source provenance and per-domain numerical decisions.

Regressions **before any long execution**: old vs new on 3y and 10y direct and segmented, exact/tolerance-declared terminal state/balances, same event sequence/time, runtime source and config mismatch rejection, payload corruption/deletion, index/path traversal/collision checks, partial-run recovery, source+checkout immutability. Explicitly label absent bidirectional feedback `NOT_COUPLED` and annual hydrology `SYNTHETIC_ANNUAL_MODEL`.

Resource/timeout/output ceilings must come from host facts and E1–E3 samples, never fabricated universal thresholds. Only after separately authorized 10-, 100- and 1000-year results may a 10k controlled benchmark be considered; no automatic replay on failure. Compare real per-domain CPU/RSS/output scaling, conservation residuals with formula-backed tolerances, thermal stability and Deep stock drift.

**Verdict scope:** `R6_INT10K_E0_STATIC_SOURCE_AUDIT_PASS__FAIR_INPUT_RUNTIME_PENDING__NO_EXECUTION`; E0 source analysis done, host identity/runtime blocked, numerical E1–E4 **NOT_EXECUTED**. Scientific gap matrix remains parallel. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
