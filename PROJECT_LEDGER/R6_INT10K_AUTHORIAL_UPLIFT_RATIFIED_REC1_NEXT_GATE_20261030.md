# ARCANA R6 — 10k uplift authorial ratification; REC1 remains pending

**Date:** 2026-10-30. **Decision status:** AUTHORIAL_RATIFIED for 10k **synthetic engineering benchmark configuration only**. User expressly answered "si sono daccordo" to: "confermi la mia proposta di mantenere l'uplift annuale originale di 0,0001 m/anno, quindi 1,0 m totali nei 10.000 anni?" This document records that selected option without claiming any numerical simulation, program change or physical-science qualification.

## Authorial parameter fixed

```yaml
decision_id: R6_INT10K_KEEP_1000Y_ANNUAL_UPLIFT
decision: AUTHORIAL_RATIFIED
experiment_scope: NONCANONICAL_SYNTHETIC_REGIONAL_UNIFIED_10K_ENGINEERING_BENCHMARK
duration_years: 10000
external_step_years: 1
uplift_semantics: MAINTAIN_ANNUAL_FORCING_ACROSS_HORIZONS
uplift_m_per_year_by_support_order: [0.0001, 0.0]
total_uplift_m_by_support_order: [1.0, 0.0]
reference_1000Y_total_uplift_m_by_support_order: [0.1, 0.0]
reference_1000Y_duration_years: 1000
reference_1000Y_annual_uplift_m_per_year_by_support_order: [0.0001, 0.0]
physics_formula_change_authorized: false
long_10k_numerical_run_authorized: false
```

**Important:** do not infer support IDs solely from tuple position. Bind first and second entries to the actual validated C028/C029 mapping/source config after inspecting FAIR actual code and source identities. No non-zero uplift is introduced to the second original-zero support. Preserve the existing mechanical opening `0.01 m/year`, thermal and hydrology numerical rules, time stepping and all existing E0 identity as supported by the qualified 1000Y run.

**Deterministic configuration interface required:** the current R2/region-unified call path hardcodes total uplift `(0.1, 0.0)`. Introduce a minimal explicit versioned run configuration with either (preferred for this benchmark) *annual uplift by named support* and a derived *total uplift for the selected planned horizon*, or a declared total + horizon with explicit derived annual values. Distinguish 1000Y unchanged reference from 10000Y candidate in config/run identity and manifest; reject invalid/stale cross-horizon checkpoints and prevent silently applying the 1000Y hardcode to the longer planned run. The original 1000Y bit-exact oracle must stay intact in the reference code path. This parameter ratification does not establish scientific validity over 10000Y or identical trajectories: only the annual forcing magnitude matches.

## Updated blockers after authorial decision

Original FAIR preflight result (immutable historical fact):
`R2_10K_PREFLIGHT=BLOCKED_UPLIFT_SCENARIO_NOT_AUTHORIZED_AND_CHECKPOINT_JOURNAL_RECOVERY_UNQUALIFIED` — was correctly issued before this authorial ratification.

**Current decision state (post-ratification):**
- Uplift *authorial choice*: **RESOLVED**; selected 0.0001 m/year and 1.0 m in 10000 years.
- Uplift *explicit config implementation and bounded parity*: **PENDING**, not prequalified.
- Checkpoint/journal atomic publication and full causal recovery: **BLOCKED_UNQUALIFIED**. Supervised SIGKILL left a valid CP3 with a missing durable journal prefix (184 logical records / 490782 logical bytes), and native chain/commit binding is not implemented. Numerical restart alone is insufficient.
- 10k execution: **NOT AUTHORIZED / NOT RUN**.
- All WorldSim canon/production/scientific flags remain false.

## Next gate — R2-REC1 minimal configuration + atomic commit/recovery, bounded tests

On the **actual FAIR dirty R1/R2 worktree**, first pin source/status, the original preflight report and 1000Y output/test manifests, and the R1/R2 diff/backup. Do **not** pull/reset/checkout/merge over intentional local changes, auto-commit, push, alter original evidence or reuse output directories.

1. Implement the smallest explicit uplift configuration with fail-closed cross-horizon/source validation, while retaining unchanged 1000Y oracle parity. Test chosen 10k plan with **zero advance** for precise derived total/annual forcing, and only bounded short synthetic same-plan direct/split/restart probes where useful. A 10k *planned* configuration with 3 or 10 simulated steps is **not** a 10k run; label clearly.
2. Adapt R2 compact journal/checkpoint publication using the existing B0 transaction / committed read-view mechanism; do not create an uncoordinated independent canonical store. Journal append, seal, flush/fsync must precede checkpoint sealing, and atomic published descriptor must bind committed prefix high-water mark, first/last global sequence, byte length, chunk SHA/chain head, source, config/horizon, per-domain clocks, full coupled frontier and checkpoint digest. The latest visible pair is the only eligible resume target.
3. Bounded fault injection matrix: kill before/after durable journal, before/after checkpoint persistence, before/after atomic visibility switch and during cleanup; old view pinning, stale parent and idempotent recovery; partial/truncated/corrupted stream fail closed. A pre-commit interruption must recover the previous committed pair without losing previously committed history; post-commit interruption must recover the new verified pair; uncommitted tail can be quarantined. Validate **full causal history and numerical restart** with 3Y/10Y direct/split, Deep and 8,000 original NULL timestamp semantics where relevant; do not assume 184 records are all events.
4. Measure writer/flush/fsync/commit overhead and RAM growth separately from physical solver. Re-run existing 168 R2 tests plus focused negative/atomic tests and anchored source hashes; no new full 1000Y or 10k execution in this gate.
5. Record proposed recovery-point objective: draft checkpoint cadence after year 1000 is every 1000 years (up to 999 simulated years rework after failure). This is an **engineering proposal**, not ratified as optimal checkpoint policy or scientific adaptive retention; do not silently enforce it. Present observed overhead / alternatives when qualification evidence exists.

**Acceptance:** `R2_REC1_BOUNDED=PASS_ATOMIC_COMMITTED_HISTORY_AND_EXPLICIT_UPLIFT_CONFIG` only on actual source/test evidence; otherwise `BLOCKED_<REASON>`. Then refresh 10k preflight with source SHA, expected memory/journal metrics, site permissions and run-level config. Only a later separate user authorization may launch 10k.

```yaml
R2_INT10K_UPLIFT_DECISION: RATIFIED_KEEP_0_0001_M_PER_YEAR_TOTAL_1_0_M
R2_REC1_IMPLEMENTATION: NOT_EXECUTED_IN_THIS_GITHUB_DOC_UPDATE
R2_REC1_ATOMIC_RECOVERY_QUALIFIED: false
R2_10K_PREFLIGHT_UPDATED: PENDING_REC1_AND_REFRESH
R2_10K_NUMERICAL_RUN_AUTHORIZED: false
R2_10K_NUMERICAL_RUN_EXECUTED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

Sources: `PROJECT_LEDGER/R6_INT10K_R2_PREFLIGHT_BLOCKED_UPLIFT_AND_ATOMIC_RECOVERY_GATE_20261030.md`; FAIR `docs/arcana/R6_RUNTIME_R2_10K_PREFLIGHT_FAIR_20261030.md`; prior R2 1000Y report and source manifests. User's explicit authorial response ratifies the annual forcing choice above, not other simulation parameters.
