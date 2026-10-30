# Codex implementation brief — ARCANA R6 INT10K Runtime R1 (noncanonical test-first)

2026-10-30. This is an implementation assignment for Codex running **inside the existing FAIR worktree**, NOT evidence of completed implementation or an instruction to run a 10k simulation immediately. Parent ledger: `PROJECT_LEDGER/R6_INT10K_B2B3S_PASS_DOMAIN_RETENTION_RUNTIME_FIRST_20261030.md`.

## Goal

Remove redundant copies and escalating JSON serialization during simulated-year progression and checkpoint creation without changing the synthetic physical laws, step plan, source E0 inputs, state values, event identities/order, balances, explicit UNKNOWN/null semantics, and original 1000Y oracle. Target **end-to-end simulated years per wall second**, not only HistoryStore ingestion/query throughput.

## HARD prerequisites

- Work in pre-existing FAIR local R6 source worktree; actual relevant branch `r6/e2c1-frontier-projection-r1-fair`, expected local source HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787` (unpublished). Inspect `pwd`, `git rev-parse HEAD`, `git status --short`, source file SHA. If mismatch/dirty/unavailable -> **BLOCKED**, no unsafe reset/checkout/pull. Do not treat remote published geometry parent as a substitute.
- Original immutable 1000Y archive `~/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y`; original `MANIFEST.json` SHA `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`. All original evidence inputs must remain unchanged.
- Use `arcana-r6-linux`; obey FAIR administrator and job policy. Keep work on new named R1 test branch/worktree only when source and author/permission workflow allows. Do not auto-push, merge or rewrite older evidence. Do not run 10k yet.

## Stage 1 — inspect and profile WITHOUT source patch

Read current sources (not stale GitHub versions):
- `src/arcana_worldsim/r6/regional_geological_evolution.py`
- `src/arcana_worldsim/r6/unified_multiphysics_microdomain.py`
- `src/arcana_worldsim/r6/int10k_history_independent.py`
- `scripts/r6_int10k_*.py` relevant to 3Y/10Y/1000Y.
- B0 store/retention/checkpoint/replay/query modules only for interface compatibility.

Published-parent hotspots to confirm against FAIR actual source:
1. `advance_region`: `out = json.loads(_canonical(dict(state)))` on growing deposit data; determine call frequency and necessity.
2. Annual `snapshot = {"time_year": year, "cells": json.loads(_canonical(cells))}`; complete growing deposit list copied/serialized per year and history collector may serialize it again.
3. `seal_regional_checkpoint` / `verify_regional_checkpoint`, `seal_history_independent_checkpoint` and `verify_history_independent_checkpoint` reserialize large frontier; do not delete semantic validation to save time.
4. Mass inventory and per-cell balances repeatedly sum `deposits` each year (growing O(total layers)). Verify whether exact incremental counters can preserve float evaluation semantics and all mutation paths, otherwise retain original.
5. Unified step producer/writer phases and source history-independent `HistoricalCollector.emit/export`; avoid doubling or shifting work to a hidden decoder/writer.

Use existing y101/y501/y751 replay checkpoints and source SHA oracle and existing `.pstats`; collect baseline per-phase exclusive CPU and wall (numerical kernels vs regional copying/snapshot encoding vs ledger/balance recomputation vs checkpoint sealing/verification vs consumer/writer), RSS and bytes. Match 7 repeats per anchor with same environment. Do not use aggregate inclusive cProfile timings as additive components.

## Stage 2 — one minimal candidate at a time, test FIRST

Construct a **history-independent fast path** that preserves all original outputs by a verified adapter. Focus on:
- Build and validate a detached dynamic frontier without copying excluded historical collections, preserving original fail-closed JSON behavior for excluded invalid history (E2-C1 R3 bug-fix semantics).
- Replace full annual snapshot persistence with an exact append-only per-cell/full-value delta + ordered deposit log **in a candidate path**, then reconstruct original canonical full snapshot bytes for SHA oracle. B1 1001-snapshot virtual lossless proof exists. Do not drop original physical state or reconstruct historical deposits from incomplete DEPOSITION event alone.
- Avoid O(age) old deposit cloning/scanning in the hot loop where correctness is provable, e.g. immutable base+new delta layers, structural sharing with mutation safety; no O(age) hidden work at another yearly stage.
- Keep old legacy full-snapshot path intact for reference; never silently change permanent data representation or canonical public interface. Any lossless reconstruction must retain order, IDs, masses, densities, erosion/transport/deposition years, provenance, all non-deposit full-values, Deep/unified fields and source event timestamps including NULL.
- Apply independent per-domain retention **later**, not a redesign of per-domain database in this R1 task. Prefer minimal patch and strong tests over broad abstraction.
- No change to numerical method, physical constants, integration dt, precipitation, erosion/deposition, Deep coupling, available authority, floats or reduction order without exact parity proof. If speedup conflicts with correctness -> retain correctness, report BLOCKED.

## Stage 3 — acceptance proof on FAIR before any 10k

- Existing 104+ E2-C1 focused negative/parity regression tests, current exact source APIs and missing/NaN/Inf/cyclic historical payload fail-closed behavior PASS.
- New explicit test that after N simulated years the state dynamic frontier does not contain past snapshot/record/event arrays.
- Original y101/y501/y751 61 items per-year indexed kind/payload SHA exact; 3Y direct=1+2 and 10Y direct=5+5 with original per-kind history SHA, exact regional/unified frontier, Deep/material and water/solid balances. Source NULL event timestamps preserved.
- Offline reconstruction of `REGIONAL_SNAPSHOT` for all years 0..1000 and 9 cells, plus 11000 final deposits: exact source canonical SHA (can reuse verified B1 script for candidate archive, but do not count merely re-running B1 on untouched original as proof of new writer).
- Compare speed vs baseline with same workload/source/clock after code change. Record median/p95/max annual wall, CPU time, memory, byte counts and relative speedup; distinguish faster physics path from cheaper output.
- Fail state source hashes and evidence, no patch stacking and no implicit change to any authority flag.
- Emit machine-readable report with marker `R6_INT10K_RUNTIME_R1=PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP` ONLY if all parity conditions pass and measured speedup > noise on representative apples-to-apples benchmarks; otherwise `BLOCKED_...` with failures and source diff.

## Stage 4 — 10k performance benchmark (SEPARATE gate, not auto-run)

After review of R1 results: submit 10k execution contract on FAIR, check source exact commit and input SHAs, physics/coupling known support, planned_years distinct from segment_years, actual cgroup allocation/scheduler/site limits, output area, and 3Y/10Y parity. Compare original and candidate fairly using the same 10k physical/config assumptions where practically feasible; avoid an unjustified 10k baseline if memory/output blow-up is likely. Record loop/end-to-end wall, CPU user/system and equivalent utilized core count, per-domain numerical vs copying/serialization/checkpoint/writer wall, peak RSS, files/allocated disk bytes, events/deposits, hash and restart/query diagnostics, 100-year windows, annual scaling, failure reasons, run SHA and machine info. No claim that prior ENG10K is integrated multiphysics.

`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false` `F2B_SOLVER_EXECUTION_AUTHORIZED=false` `ARCANA_SI1_MECHANICS_QUALIFIED=false`
