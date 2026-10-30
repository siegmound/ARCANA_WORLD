# ARCANA R6 — REC1 bounded PASS, 10k launcher/services/cadence remain BLOCKED

**Recorded 2026-10-30.** Evidence authority **FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE as reported by user and supplied REC1 Markdown**, not independently accessed/rehashed from FAIR in this GitHub documentation update. Original local FAIR result `docs/arcana/R6_REC1_FAIR_20261030.md`; separate refreshed preflight `docs/arcana/R6_RUNTIME_R2_10K_PREFLIGHT_REC1_FAIR_20261030.md` was named by the user, but its full contents are **not present in this documentation session**. Do not fabricate its machine marker or missing metadata. This GitHub file is a new handoff and proposed bounded gate, **not a simulation or source patch**.

## 1. Verified status as reported

`R2_REC1_BOUNDED=PASS_ATOMIC_COMMITTED_HISTORY_AND_EXPLICIT_UPLIFT_CONFIG`.

- 228 PASS tests (previous 168 R1/R2, 22 REC1, 38 B0), 9 supervised process SIGKILL, post-crash recovery of **both** committed numerical frontier and complete causal history with B0 read-view/atomic publication. Direct/split 3Y (1+2), 10Y (5+5) with source oracle for original 1000-plan; bounded 10000-planned 3/10 steps exact same-plan direct/split, anchors y101/y501/y751 exact. Original NULL source event time semantics intact; no full REC1 1000Y/10k run.
- `AnnualUpliftPlan V1`: RATIFIED yearly uplift `R6G1D-R091-C028` plate 11 **0.0001 m/year**, `R6G1D-R091-C029` plate 5 **0**. Derived 1000Y total `(0.1,0)` m and 10000Y total `(1.0,0)` m. Config/horizon/support checks fail closed; original constructor defaults and original 1000Y checkpoint bytes preserved.
- B0-coupled `RecoveryController` opt-in: durable chunk fsync and content identity, matching full native coupled checkpoint fsync, then one atomic B0 read-view publication via `append_transaction` / expected parent; stale parent rejected. Recovery only from verified committed lineage, with global ordinal and stream parent binding, fail-closed corruption/truncation and retained orphan evidence. This is **bounded current-filesystem process-crash qualification**, not production storage failover or hardware power-loss qualification.
- Reported 10Y under planned 10000 horizon: advance 0.304578 s; commit 0.094671 s; query/reconstruction 0.093464 s; split recovery 0.040159 s; 1,843,419 logical archive B. These are short single samples; do not extrapolate them as steady-state 10k commit overhead.
- Source pins reported: `int10k_runtime_compact.py` SHA256 `44a203700871c2893f691fe0f304d7447deae714774c653ff61b9c043d8d6444`; `runtime_run_plan.py` `0c55932157de25c5746a73a952e506cef0a9564a59f788954d653a8d4d0c14c2`; `runtime_recovery.py` `f91e78030fc13323ee9cbe6f88857a0998b52e23fc3b02a854d5d8c8a310fc32`; `test_r6_rec1.py` `906aba73992410635526c98657bd18a041f3da4a5d4595f01a8be7247b34c163`. Regional operator SHA `bc119751559d4d74c8e76292dcc92fcabeade31defb59a9f65cc4d7d60a047db`.
- FAIR worktree remains intentionally dirty, branch `r6/runtime-copy-r1-fair` based at `2c71370eb9a959c78121ce1c88ec8e9e37187787`; unchanged original E0/R1/R2 evidence. No commit/push/reset or long simulation executed.
- User reports refreshed 10k preflight **BLOCKED on launcher integration and service/cadence policy**. Old two-block marker from pre-REC1 is HISTORICAL and must NOT be reported as the present unresolved state. The authorial uplift choice and bounded crash integrity are now resolved. No 10k authorization or production authority follows.

## 2. Core service contract proposed for authorial review (NOT YET RATIFIED)

The primary ARCANA goal is a queryable, causally coherent scientific WORLD_HISTORY, not an expensive eager full-JSON snapshot on every simulated year. Recommend **COMPACT_FULL_CAUSAL_HISTORY** as standard engineering 10k output:
1. Store **all** complete numerical/causal compact frames (each native simulation year), material/region/event/provenance data, hydrology, synthetic Deep/unified records, explicit NULL source timestamps and all relevant source/forcing, with no lossy pruning, invented coverage, silent downsampling or changed solver cadence.
2. B0 committed checkpoints and source/config/clock-bound read views for exact restart and verified query. Reconstruct complete legacy regional snapshot at **any retained exact source year on demand**; prove values/hash against existing oracle where available. Preserve optional legacy materialization as a **distinct, explicitly selected and separately measured** compatibility service; do not automatically generate 10k physical legacy JSONL (earlier conditional forecast 140–220 GB) or report compact-only vs full legacy as same-service speedup.
3. The engine remains a **synthetic 3×3 region + C028/C029 model** with existing reduced thermal/mechanics/hydrology and diagnostic Deep. Do not claim biology/climate/populations or production history created in the 10k test. Separate numerical step = 1 year from archival sampling/checkpoint cadence; no change to annual forcing.
4. For operational monitoring, record annual and 100Y time series, p50/p95/max, CPU user/system/core-equivalent, RSS/cgroup, allocated/logical disk/file counts by journal/B0/checkpoint, reconstruct/query/restart cost, events/deposits and five O(D) scans. Use actual site allocation and quotas; no artificial resource caps.

**This proposal is a recommendation, not an implementation or authority change.**

## 3. Checkpoint/commit cadence decision — do not confuse the two

REC1 shows the cost of one 10Y commit but does not establish ideal cadence at later years. The initial legacy proposal y100/250/500/750/1000 and then every 1000Y permits up to **999 model-years rework** after a crash; this recovery point can be unacceptable despite sparse bytes.

For decision support, define at least candidate **max checkpoint gaps** at 250, 500 and 1000 model-years (theoretical max uncompensated recomputation **249, 499, 999** respectively for aligned integer-year checkpoints), plus a candidate incremental **durable journal/B0 visibility cadence** measured separately. Finer durable publication than full solver checkpoints can preserve a committed event prefix but does NOT automatically allow resumption from that prefix without a compatible checkpoint or deterministic numerical replay recipe; conversely full checkpoints without committed causal history are ineligible. Only expose resume from B0 committed paired identities.

**Next bounded test** should instrument checkpoint seal/replay verification, B0 transaction/commit fsync, recovery and memory at source anchors y101/y501/y751 and existing 1000Y evidence where possible, then show cost-versus-max-recomputation tradeoffs. Do not impose 250/500/1000 as a ratified choice or claim constant per-checkpoint cost. Ask authorial decision only after presenting grounded costs or a safety-oriented recommendation with disclosed assumptions.

## 4. Next proposal — R2-L1 launcher integration and bounded acceptance (not executed, requires separate developer permission if code changes requested)

1. Inspect the actual refreshed FAIR preflight document and source/test/evidence hashes; reproduce its exact remaining BLOCKED decision, no guesswork. Confirm R1/R2/REC1 dirty source/patch identity against immutable evidence. No destructive git operation or changes to archived originals.
2. Implement a distinct **opt-in** R2-REC1 integrated long-horizon launcher/controller, using existing B0 `RecoveryController`, `AnnualUpliftPlan V1` and existing physical operators without modifications. Explicit planned duration 10000, annual advance one year, durable committed chunk+checkpoint, ability to stop, validate and resume from committed prefix. Do not rename as E1/ENG10K. **No new 1000Y, 10k or 100k numerical trajectory during bounded qualification.**
3. Define CLI/config explicitly: `planned_years`, `advanced_segment_years`, `source/input digests`, `output_root`, selected archive service `compact + query` or explicit `legacy_full`, journal chunk/publish interval, coupled native checkpoint interval, read-view/restart path and source/forcing identity. Reject unsafe path reuse and mismatched planned horizon. Avoid arbitrary fixed memory/runtime/output application caps; allow actual site scheduler rules.
4. Validate 3Y/10Y direct-vs-split with planned horizon 10000 under both single uninterrupted run and B0 committed save/exit/reopen/continue; negative SIGKILL pre/post visibility, partial/chunk corruption, source/config/horizon mismatches and stale parent; exact local stream record order/global ordinals, original 1000-planned oracle parity, checkpoints for Deep, thermal, regional source/forcings, NULL timestamps and balances. Refresh the full 228 tests and document evidence with separate source SHA.
5. Make the durability/observability service explicit in tests. Never claim B0 production archive qualification based on fixture-only adapter; fail closed on missing atomic visibility/commit chain, noncommitted historical suffix, or unavailable full-context resumed query.
6. Evaluate candidate durable publish and checkpoint cadence tradeoffs using existing anchor-based bounded replay and measured cost curves. Include memory of committed chain/recovery that REC1 says grows O(total compact history + sum checkpoint sizes), rather than treating disk-only output bytes as upper bound. If this memory threat is not supportable at 10k, return BLOCKED with one minimal scoped follow-up, not silent pruning.
7. Produce a final decision: `R2_L1_BOUNDED=PASS_LAUNCHER_SOURCE_AND_RESUME_PARITY` or `BLOCKED_<reason>`. Separately state whether service and cadence policy can be authorially ratified and whether the 10k preflight is READY; do not auto-authorize the 10k.

## 5. Stage authority

```yaml
R2_REC1_BOUNDED: PASS_ATOMIC_COMMITTED_HISTORY_AND_EXPLICIT_UPLIFT_CONFIG_FAIR_OPERATOR_REPORTED
R2_10K_UPLIFT: RATIFIED_ANNUAL_C028_0_0001M_C029_0_TOTAL_C028_1_0M
R2_10K_PREFLIGHT: BLOCKED_LAUNCHER_AND_SERVICE_CADENCE_POLICY_USER_REPORTED
R2_L1_IMPLEMENTATION_AND_TESTS: PROPOSED_NOT_EXECUTED
R2_10K_LONG_RUN_AUTHORIZED: false
R2_100K_LONG_RUN_AUTHORIZED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

References: local FAIR `docs/arcana/R6_REC1_FAIR_20261030.md` and `docs/arcana/R6_RUNTIME_R2_10K_PREFLIGHT_REC1_FAIR_20261030.md` (refreshed text not available to GitHub documentation author); earlier `PROJECT_LEDGER/R6_INT10K_AUTHORIAL_UPLIFT_RATIFIED_REC1_NEXT_GATE_20261030.md` and `PROJECT_LEDGER/R6_INT10K_R2_PREFLIGHT_BLOCKED_UPLIFT_AND_ATOMIC_RECOVERY_GATE_20261030.md`.
