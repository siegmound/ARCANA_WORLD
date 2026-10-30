# ARCANA R6 — B2B3S FAIR PASS, adaptive domain retention decision, runtime-first INT10K recovery

Date: 2026-10-30. Repository: siegmound/ARCANA_WORLD. Document-only ledger addition. Status: AUTHORIAL_ARCHITECTURE_DIRECTION + ENGINEERING_EXECUTION_PLAN; no solver execution, code modification, canon promotion or source push in this entry. Latest user-supplied FAIR stdout is operator evidence, not independently downloaded FAIR artifacts.

## 1. Actual new FAIR gate — E2-C2-B2B3S

- Runner: `arcana_e2c2_b2b3s_100y_bundle_query_scale.py` SHA256 `cf58191d62fd41091ea1cc217dc45182509457bdc07886cc9e62352f33fa3324`, operator matched.
- `E2C2_B2B3S_PURE_SELFTEST=PASS`, B2B1 typed selftest PASS, original kinds hash pin PASS.
- `E2C2_B2B3S=PASS_100Y_BUNDLE_STORE_SOURCE_QUERY_AND_VIEW_GROWTH`; 101/101 authentic regional snapshot SHA; 100 annual and UNIFIED/Deep exact; 5,800 ordered/hash-authenticated events; 800 source NULL years unchanged; 101 typed transactions, 101 pinned old view checks, stale parent negative PASS.
- 16,600,429 total scratch store bytes; 306 files; 5.012019 seconds of recorded total writes; reopen + reconstruction + selected queries 3.837651 seconds; peak process RSS 152,216 KiB (reported Linux); 12 Deep material-volume checks, 14 cell-state SHA queries, 90 selected cell event matches, 100 annual bundles; experimental adapter not native B0 `event_at`.
- Read-view manifest at y100 16,590 bytes; cumulative all view manifests 857,491 bytes (about 5.17% of scratch store). Single manifest membership grows linearly (for selected y>=1, `390+162*y` bytes), cumulative stored membership is quadratic if all historic manifests remain. This needs a later engineering solution but **does not take precedence over runtime speed**.
- Original 1000Y manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a` unchanged; scratch store automatically removed; code unchanged. Candidate B annual bundle remains leading **only** for synthetic archival experiments; no persistent world-history schema ratified.

## 2. Authorial direction: independently sampled domain histories, shared causal consistency

Agreed objective: after simulation, select persistent state samples adaptively **per physical/scientific domain and spatial scope**, not a single global schedule or repeated global snapshots. Calmer/reconstructible intervals retain fewer samples; fast/intense changes, nonlinear transitions, discontinuities, uncertainty/support/model-validity boundaries, irreversible effects and PRE/POST event requirements retain more. No fixed global threshold or arbitrary retention ratio; follow existing `R6_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY_V1` and `R6_SIGNIFICANT_STATE_EXTRACTION_RECONSTRUCTION_V1`.

Candidate logical streams: geology/materials, hydrology, Deep/energy resources, climate, biosphere, populations/lineages, etc., each with its own ordered event/delta stream, domain-specific checkpoints, native clock, provenance, uncertainty and reconstructibility tests. Same tool/provider may feed multiple domains but does not gain canonical authority; logical stream separation does NOT imply mandatory separate database engines or independent uncoordinated transactions.

One global WORLD_HISTORY causal catalog / committed read-view binds run/branch IDs, domain version/high-water marks, provider/forcing identities, dependency edges, coupling and exchange records, and replay recipes. Cross-domain queries at location/time must select a **causally consistent vector** of domain views; if the requisite coupling states or histories cannot be reconstructed, report UNKNOWN/BLOCKED, never silently return unrelated last-known snapshots. Events may remain EVENT_ONLY. A domain does not rewrite geology just because Deep or hydrology changes, but **must** record a geology change when the cross-domain effect genuinely changes geological state. Use B0 typed records / retention / replay / checkpoint / refinement / atomic visibility rather than replacing them.

Distinguish (a) domain query reconstruction states and (b) sufficient global coupled solver restart frontier: a set of domain anchors plus outstanding fluxes, coupled-state memory, clocks/forcing, stochastic state and exact dependency closure. Sparse domain checkpoints need not all align on the same year; an eligible restart must have a complete consistent reconstructible frontier and validated replay, not just several unrelated snapshots.

This is a **design decision**, not an implemented or qualified per-domain multi-store or new science. Keep `WORLD_HISTORY_ARCHITECTURE.md` and `B6N6` contracts as authority; new alternative physical database layout / incremental view representation requires measured evaluation and tests.

## 3. PRIORITY SHIFT — runtime first, archival index optimization later

User-selected order:
1. Resolve repeated copying/serialization and optimize **numerical simulation wall time**, keeping exact computational/oracle semantics.
2. Re-run a separately authorized synthetic **10,000 model-year** integrated benchmark with wall/CPU/RSS/output measurements on FAIR, explicitly recording host/job limits and code/input SHA.
3. Once 10k scales and restarts reliably, assess separate 100k synthetic engineering experiment, then test retrospective adaptive domain-specific sampling on 0–10k/0–100k and independent reconstruction/restart.
4. Optimize B0 long-lived manifest/index/query layout informed by actual observed query and retention needs; B annual bundle remains a candidate, not selected production design.

**Known baseline:** 1000Y 3x3 synthetic FAIR loop wall `244.78096017614007 s`, full HISTORY `1,916,080,917 B`, 1000 annual records, 1001 regional snapshots, 61,001 indexed envelopes; original geometry-fixed source local FAIR `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`. At Y101/Y501/Y751 isolated cProfile JSON encode/decode roughly 79%/86%/87% of profiled time; stable unified numerical kernel ~20ms/year in those profiles. Dominant repeated serialized nested `deposits` and annual snapshots; sample Y1000 11000 deposits. Baseline is NOT a 10k measurement. E2-C1-R3 conservatively corrected history-free frontier projection preserving invalid-excluded-history fail-closed; FAIR committed `2c71370eb9a959c78121ce1c88ec8e9e37187787` locally unpushed; E2-C1-R4 3Y/10Y exact-oracle PASS. DO NOT regress its canonical validation to gain time.

## 4. Next technical work package: R6 INT10K RUNTIME-COPY-ELIMINATION R1 — TEST FIRST

Source on FAIR `r6/e2c1-frontier-projection-r1-fair`, `2c71370e...`, verify exact clean status; preserve all original E0 inputs/evidence and source lock. Avoid code edits using stale published remote R6 head as a substitute for FAIR local commit.

First independent audit of actual current `regional_geological_evolution.py`, `unified_multiphysics_microdomain.py`, history-independent adapter, caller profiling and existing tests. Candidate hotspots verified in published parent:
- `advance_region` clones full region with `json.loads(_canonical(dict(state)))` (including accumulated deposit layers).
- Each year `snapshot = {"time_year": year, "cells": json.loads(_canonical(cells))}` creates a growing complete snapshot, often only for history consumer; unbounded history-free execution still touches all previous deposits.
- `seal_regional_checkpoint` and repeated `verify_regional_checkpoint`, outer history-independent seal/verify, also re-encode growing frontier.
- per-year `sum(d["mass_kg"] for d in c["deposits"])` in solid/cell balances traverses all accumulated deposits; assess incremental exact accumulators while preserving numerical operation/reduction order or validated tolerances.
- writer vs solver timings must be separately measured. Do NOT simply remove hashing, safety validation, provenance, Deep, balances or events.

Candidate bounded optimization: explicitly validated detached frontier of only mutable dynamic state, keyed deposit append log / immutable structural sharing with copy-on-write on actual mutation, lazy *logical* full snapshot emission or compact field-exact delta, and cached verified additive ledgers only where original semantics preserved. Any runtime speed optimization must be tested with genuine equivalent output; do not pretend O(N) copying is removed merely by moving it to a writer.

Required tests before accepting: repeat 104 or latest current regression tests and explicit negative NaN/Inf/object/cyclic excluded-history guards; 3Y direct vs1+2 and 10Y direct vs5+5; independent original 1000Y per-kind SHA oracle, restart frontier and balances; y101/501/751 original 61-item per-year SHA, changed/duplicated/lost material events fail closed, source null event time preserved, no numerical constants/step/forcing changes. Record `PROFILING_BASELINE`, `PROFILING_CANDIDATE` for wall per-year and distinct phases; 7 repeated y101/501/751 anchored samples for comparable medians, CPU time, peak RSS, I/O/output bytes, checkpoint bytes and query-reconstruction availability. If changing on-disk representation, exact logical original snapshot reconstruction must be proven separately before any claim of losslessness. Do not patch-stack on a failed parity gate.

### 10k gate following optimization

Only after R1 PASS, design/approve a **new** 10,000-year synthetic integrated run using identical physical and external-step configuration/inputs for baseline-vs-candidate comparison. Confirm valid `planned_years=10000` separate from segment duration, effective FAIR allocation/scheduler/cgroup, and no unreviewed giant hydrology substeps; previous ENG10K was a distinct reduced thermal/tectonic benchmark and is not this experiment. Collect end-to-end and loop wall, CPU user+system, CPU/core-equivalent, per-domain kernel vs clone/serialization vs hashing/checkpoint vs writer, p50/p95/max annual cost and year-window trend, peak process-tree RSS, logical/disk bytes by domain/record type, file count, event/deposit growth, sample/checkpoint counts, stall/failed/unknown data, consumed cores/threads, exact source/input SHA, resume and hashes. Observability mode `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS` (subject to actual FAIR site resource policy). Do not launch 10k automatically, do not claim 64-core scaling on 9 cells, preserve complete evidence and stop on real invariant failure.

## 5. Explicit authority boundaries

```yaml
E2C2_B2B3S: PASS_FAIR_OPERATOR_REPORTED
DOMAIN_ADAPTIVE_RETENTION: AUTHORIAL_ARCHITECTURE_DIRECTION_NOT_IMPLEMENTED
NEXT_PRIORITY: RUNTIME_COPY_AND_SERIALIZATION_OPTIMIZATION_TEST_FIRST
NEXT_LONG_BENCHMARK: INT10K_REQUALIFIED_10000Y_AFTER_R1_AND_AUTHORIZATION
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

References: `docs/arcana/B6N4A_EVENT_IMPACT_AND_STATE_SIGNIFICANCE.md`; `docs/arcana/B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE.md`; `contracts/R6_SIGNIFICANT_STATE_EXTRACTION_RECONSTRUCTION_V1.json`; `PROJECT_LEDGER/R6_INT10K_1000Y_FAIR_PERFORMANCE_E2C_E2D_HANDOFF_20261030.md`; `PROJECT_LEDGER/R6_INT10K_E2C0_C_NESTED_CALLERS_20261030.md`; `PROJECT_LEDGER/R6_INT10K_E2C1_R4_INDEPENDENT_AUDIT_SEALED_20261030.md`; `PROJECT_LEDGER/R6_INT10K_E2C2_B2B3F_FAIR_SIX_STAGE_CRASH_PASS_B2B3S_100Y_GATE_20261030.md`.
