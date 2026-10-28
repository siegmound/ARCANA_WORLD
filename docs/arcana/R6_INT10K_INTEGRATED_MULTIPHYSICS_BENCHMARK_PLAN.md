# R6-INT10K — Integrated multiphysics engineering benchmark preparation

**Date:** 2026-10-28  
**Decision:** `R6_INT10K_MULTIPHYSICS_ENGINEERING_BENCHMARK_PREPARATION`  
**Evidence level:** `DESIGN_ONLY__NOT_EXECUTED`  
**Base branch:** `r6/multiphysics-integration-20261026`  
**Reviewed source baseline:** `736bdd1e28f5d0b2d5611c4fb22ebb692f706724`  
**Production authority:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

## Why this is a new test, not a repeat of ENG10K

The older INT3-ENG10K was an actually executed 10,000-year *reduced thermal/tectonic* engineering slice (2 supports, 73 nodes, fixed Euler forcing), with 194 archived states across 8 trajectories and 186 substeps. It is **not** a 10,000-year qualification of the newer multiphysics engine.

Current source candidates:
- `src/arcana_worldsim/r6/unified_multiphysics_microdomain.py`: shared-clock mechanical Maxwell, reduced thermal pure-shear, rheology, surface/hydrology/sediment, and synthetic Deep reservoir calls. The default `UnifiedConfig` plans only 3 years (`external_step_years=1.0`, `hydrology_dt_seconds=3600`). `scripts/r6_unified_multiphysics_microdomain.py` hardcodes that default; `--segment-years 10000` alone is **not** a valid 10k run. A naive long full-cadence hydrology plan could schedule ~87.66 million hourly substeps per case over 10,000 years, prior to other operators and the four-case matrix.
- `src/arcana_worldsim/r6/regional_geological_evolution.py`: a **3x3 synthetic surface** and 2 R6 subsurface supports (`R6G1D-R091-C028/C029`); `run_regional_segment` advances the subsurface via the unified orchestrator using yearly external steps and `hydrology_dt_seconds=31557600`, with distinct regional annual precipitation/routing/erosion. It does **not** add bidirectional surface-to-thermal, sediment-to-Deep or climate feedback. Calling multiple subsystems is not proof that all are coupled.
- `scripts/r6_regional_geological_evolution.py`: `--years` currently sets both planned `RegionalConfig.duration_years=max(years,3)` and segment length. Its `--checkpoint-in` interface cannot safely implement 1k+9k with a fixed 10k plan without separating **planned duration** from **segment duration**, because config identity must match. Both unified/regional implementations retain detailed step/record histories in in-memory state and checkpoint; an unchecked 10k call risks RAM, serialization and quadratic growth across resumed segments.
- `scripts/r6_int3_eng10k.py` belongs to the old thermal benchmark and its own execution authorization contract. Do **not** reuse its success marker as evidence of the new integration. Fastscapelib/gFlex and ASPECT are **not** silently included: only count providers for which actual numerical calls and state handoffs are observed in this run.

**Input prerequisite:** `load_verified_r6_initial_columns` reads the preserved `MATERIAL_RHEOLOGY_PROVIDER_20261025_03` result, manifest and sidecar and checks two 73-node T0 initial columns and their boundary/source hashes. This output is not established as a Git-tracked input in the target branch. Determine the actual available path, bytes, identity and authority on the intended host before execution. Do not generate replacement data under an old verified identity.

## Target question and scope

Can the currently integrated **engineering** engine evolve for 10,000 *model* years with finite states, stable step decisions, intact domain ledger, exact time/support/material identities, bounded resource growth, reproducible checkpoint/resume, meaningful time-queryable history and no invented physical feedback? A successful 10k run establishes **software/numerical engineering evidence for the exact synthetic case**, not physical realism of 10k geological years.

Use the **regional 3x3 + unified 2-column path** as the primary test only after the input and execution contract are bound. Complement it with short high-cadence unified hydrology tests rather than assuming annual hydrology faithfully resolves hourly physics. No new unqualified ASPECT, MPI, pyGPlates, ShellSet, Fastscapelib or gFlex calls are included by implication.

## Required preparation before numerical execution

1. **Exact-code and actual-coupling inventory (read-only):** record branch/commit, upstream R6 source files and their SHA256, actual input directory and manifest hashes, runtime modules, support/material IDs, operator call graph, supported `dt`, source of forcing and source of every state/flux; label all synthetic/unknown semantics. Preserve previous ENG10K and GEODYN-3C evidence.
2. **Bounded streaming test harness (code/test preparation):** implement a distinct `r6_int10k` runner; explicitly configure `planned_years=10000` independently from `segment_years`, support exact checkpoint resumes at authorized boundaries, preserve the same configuration/source identity across segments, do not include full history recursively inside every new checkpoint, and stream immutable compact state/flux/event records plus an integrity manifest. Retention interval is **not** numerical step size. Preserve direct full-step continuity and evidence of per-step decisions; use event-driven plus periodic coarse retention, with higher resolution around anomalies.
3. **Regressions before FAIR run:** fixed-plan 3-year and 10-year continuity, segmented vs direct equivalence at agreed exact substep boundaries (declared numeric tolerances where not bit-identical), source/checkout immutability, initial identity mismatch rejection, missing/modified payload, checkpoint rehydration, incomplete recovery, manifest/hash check, absolute/relative path safety, no WORLD_HISTORY writes, and elapsed-time versus stored-time distinction.
4. **Resource and authority preflight:** determine actual host/interpreter/versions and dynamic resource constraints, input size, output budget, permitted evidence root, expected step counts and sampled CPU/RSS/output growth; no universal 2 GiB RAM assumption. Choose supervised time, memory/output/stop ceilings from measurements and operator/host constraints. Require a separate exact-commit review of these bounds before scheduling a long numerical run.

## Staged benchmark plan

| Stage | Model years | Mode | Evidence and advance condition |
|---|---:|---|---|
| E0 | 0 | Read-only input/coupling/runtime preflight | Exact source and input identities, actual operator call graph, budgets, stop and output policy bound |
| E1 | 10 | Fully integrated regional + unified, isolated output | All intended operators actually called; finite/nonnegative applicable stocks, no missing records, valid balances and authoritative labels |
| E2 | 100 | Same fixed plan, separate output | Source/flux/material/time identity; step-level and cumulative balance tolerances, thermal/mechanics and Deep monitoring; no runaway or unbounded I/O |
| E3 | 1000 | Segment/restart cross-check | Measured wall/RSS/output scaling and checkpoint integrity; direct/segmented comparison at valid boundaries; qualify larger-run cost estimate |
| E4 | 10000 | One **separately authorized** supervised synthetic engineering experiment | Only after E0–E3 evidence; terminal/natural stop, exact coverage, source immutability, balances, reproducibility, archive integrity and performance |
| E5 | bounded variants | Selected sensitivities/tuning | One parameter family at a time (annual step/retention where supported, mechanics/rheology, synthetic Deep mobility, sediment/routing) after baseline; distinguish numerical defects from scientifically unspecified laws |

**Do not silently change physical coefficients, units, grid resolution or material/Deep inventory between direct and restart comparisons.** The regional driver currently uses an annual coupling tick and distinct hydrology assumptions; do not report this as convergence relative to an hourly hydrology solve. A changed numerical step needs a distinct validated configuration and a defined comparison method.

## Mandatory metrics

- **Coverage & identity:** planned/completed model years, external/internal substeps by domain, snapshots/checkpoints/events, monotonic time, exact source SHA and support/material IDs, missing or extrapolated states.
- **Physical-accounting / engineering sanity:** per-domain min/max and finite values; thermal range, crust/lithosphere/volume/beta and mechanical work/elastic+viscous energy residual; water inputs, storage and exports; sediment/substrate erosion/deposition/export, inventory by material ID, mass closure; Deep reservoir stock/transport/accessibility, no accidental energy creation; track forcing as explicit sources/sinks.
- **Actual exchange graph:** for each edge, producer output, consumer input, conversion/mapping, time and support, units, per-step source identity, whether the link is genuine feedback or a diagnostic/no-coupling pathway.
- **Numerics & reproducibility:** exact or declared tolerance-checked direct-vs-restarted endpoint, anomaly/event timing, signed balance residual and numerical error budget (never assert zero in all cases by default), sensitivity of results to accepted time step.
- **Performance:** wall/CPU by provider, step count, peak **process-tree RSS measured** versus Python allocations, output byte counts by record type, hashing/serialization/checkpoint cost, scaling with simulated years and retained snapshots.

## Stop conditions and interpretation

Stop with a retained `BLOCKED`/FAIL evidence directory on nonfinite data, invalid/negative stock where forbidden, conservation residual outside a **documented domain-specific numerical tolerance**, missing source provenance, support/time mismatch, invalid checkpoint or manifest, unsupported coupling, resource budget breach or timeout. Do not modify original evidence or rerun a failed candidate automatically. Tolerances and resource ceilings are to be set from formulae, float precision and measured host budgets in E0–E3, not invented globally here.

**No claim of success for an unexecuted stage.** The next milestone is `R6_INT10K_E0_PREFLIGHT_AND_STREAMING_DESIGN`, not a 10k PASS. The already-closed GEODYN-3C experimental archive remains separate; it is not yet the 10k runtime segment writer nor a qualified geodynamic forward solver.

This experimental lane is compatible with prototype-first decision D-015/D-016. The `R6_PHYSICAL_ENVIRONMENTAL_PROVIDER_GAP_MATRIX` is retained as a **parallel, read-only scientific-readiness lane**, not silently completed or erased. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; existing engine-specific execution gates remain unchanged.
