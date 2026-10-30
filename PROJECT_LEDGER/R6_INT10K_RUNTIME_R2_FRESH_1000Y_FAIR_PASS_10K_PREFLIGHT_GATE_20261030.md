# ARCANA R6 — R2 fresh 1000Y PASS; integrated synthetic 10k preflight next

Date: 2026-10-30. Status: **USER/OPERATOR-REPORTED FAIR RESULT**, not independently fetched/rehashed from the FAIR evidence volume in this documentation-only GitHub session. User-supplied local source report: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK/docs/arcana/R6_RUNTIME_R2_1000Y_FAIR_20261030.md`. The exact report SHA, run manifest SHA, source snapshot digest, individual 100Y window measurements and actual allocated disk bytes were not supplied in this conversation; obtain from FAIR report and manifest before sealing or any further execution. Do not invent them.

## Completed result — fresh R2 1000Y numerical trajectory

The previously authorized **one** new synthetic 1000Y R2 numerical trajectory reportedly completed with a continuously alive single R2 frontier, generating a compact history and later reconstructing legacy outputs. This is **not** an offline re-encoding of an old 1000Y run.

- **PASS** exact reconstructed 61,001 ordered payloads, including 1,001 REGIONAL_SNAPSHOT, 1,000 REGIONAL_YEAR_RECORD, 1,000 UNIFIED_STEP / Deep and 58,000 events; 8,000 source event timestamps remain NULL.
- Reconstructed full `HISTORY` and `INDEX` byte-identical to original oracle; five milestone checkpoints also **byte-identical** (operator reports same full compatible envelope), numerical restart, material/water/solid balances and historical queries PASS; relevant 168 R2/R1 tests PASS.
- New 1000Y hot advancement+compact ingest wall **37.45 seconds**; hot loop with checkpoints/observation **40.24 seconds**.
- Complete legacy reconstruction **43.33 seconds**; counted loop + full reconstruction service **83.57 seconds**; full process launch-to-exit including all checks **110.02 seconds**.
- Complete new compact archive **175.66 MB** (unit/allocated-byte breakdown not separately provided); entire process peak RSS **355.60 MiB**; loop effective CPU cores **0.97**.
- No retry, new 10k/100k, commit/push or modification of original evidence.

R1 previous **fresh** 1000Y loop was 214.125572 s with original full `HISTORY` 1,916,080,917 B. R2's compact loop `40.24 s` is **not the same output service** as R1's loop. The 83.57s R2 loop+reconstruction is more informative but still not a controlled, repeated same-provenance and fully identical observation-cost comparison. The 110.02s full process contains additional verification not necessarily comparable with R1 recorded loop. Do not declare a statistically controlled overall speedup from these historical aggregate figures.

R2 compact archive 175.66 MB is a new solver-generated archive, unlike earlier offline compact 162.037MB; it is about 91% less than the original legacy `HISTORY` alone as a **descriptive, different-format comparison**, not evidence that all original data/durability semantics have been qualified under canonical B0. Exact logical oracle reconstruction is demonstrated by the operator report. A full legacy materialization still costs time and bytes when requested.

## Remaining engineering constraints

- Five deposit-dependent numerical scans remain O(D(y)) in dynamic age, plus cold imports, full snapshot queries, checkpoint seal/hash verification, and all-year legacy compatibility output. An R2 live journal resides in RAM and may grow with simulation age. R2 1000Y **355.60 MiB peak RSS**, substantially above R1's differently instrumented 1000Y ~122.37 MiB; do not claim RAM savings.
- Effective utilization **0.97 CPU cores**; 128 visible threads/CPUs are not evidence of parallel work. No uncontrolled multiprocessing, threading or novel NUMA changes without source and performance justification.
- R2 scratch compact codec/readback does NOT yet qualify full B0 production atomic publication/crash recovery or domain-adaptive state selection. Per-domain and region adaptive retention with shared causal index is future architecture, not production implementation.
- Keep all scientific/production flags false. A synthetic 3x3/C028/C029 1000Y engineering result does not qualify physical real-world WorldSim or ungoverned long-horizon geodynamics.

## Next objective — PREPARE integrated 10,000 model-year benchmark; NOT YET AUTHORIZED TO RUN

**Do not start the 10k on this document.** First a read-only and bounded engineering preflight using the exact R2 source/diff/manifest anchored on the FAIR local dirty branch, original input identities and delivered 1000Y output. Identify actual FAIR scheduler/session/node authorization and site resource policy; no arbitrary application duration/memory/size caps and no substitution of unrestricted cgroup observation for site permission.

Preflight must establish:
1. **Source/archive closure**: current dirty R2 code and all tests/source SHA; the new 1000Y report/manifest SHA and output members; recovered original 61,001 kind/order/hash evidence; checkpoint/restart evidence; no regressions; preserve original directories. No forced clean checkout, reset, pull, auto-commit or push.
2. **Planned horizon and forcing**: one yearly external step, regional `duration_years=10000`, unified planned horizon 10000 where relevant, 3x3 synthetic region + C028/C029 same qualified providers. Inspect exact 1000Y `0.1m` run-level prescribed uplift total and derive the 10k *annual forcing* explicitly; extending planned horizon with the same total changes per-year uplift and thus physics. Decide and document whether target is same annual forcing (with consistent adjusted total) or a different declared 10k scenario; neither is silently inferred. Check provider/model validity at 10k for synthetic engineering scope.
3. **Runtime scaling risk**: journal residency and potential RAM/disk/file counts, number/size growth of immutable deposit rows and compact frames, any all-history list exposed on each step, existing five O(D) deposit passes and O(D) checkpoint/reconstruction/queries. Instrument actual 1000Y per-100-year windows, sampled RSS, cumulative events, journal bytes and checkpoint growth before making any 10k forecast. Do not extrapolate linear from 40.24s or 175.66MB without qualifying memory and residual O(D).
4. **Checkpoint/restart strategy**: plan explicit sparse milestone checkpoints and exact coupled continuation, without reconstructing a full legacy snapshot each simulated year. Distinguish numerical restart checkpoint from sparse adaptive historical sampling. Check journal writer flush, failure recovery and ability to resume without retaining 10k full history in Python memory; if journal RAM makes this impractical or correctness cannot be ensured, produce `BLOCKED_10K_MEMORY_OR_RESTART_DESIGN` and propose minimal tested change before any long run.
5. **Observability and fair metric**: 10k wall end-to-end and annual/window curves, user/system CPU and effective cores, sample RSS and process tree, physical/logical disk bytes and file count by compact frames/events/Deep/checkpoints, full reconstruction only as a separately timed optional compatibility service with source-oracle checks where an oracle exists, selected queries and restart timings; checkpoint compression cannot be substituted for source values. Full original 10k oracle does **not** exist, so define internal consistency and independent overlap/restart tests, deterministic reruns of selected windows, hashing of selected source events/balances, and 1000Y overlap comparability only when forcing and planned horizon are truly equivalent.
6. **FAIR site policy**: actual compute allocation/job/session and permissions, quotas and output destination, and stop/failure protocol; no invisible retries, no made-up safety limits.

### Required preflight output

`R2_10K_PREFLIGHT=READY_FOR_EXPLICIT_10K_EXECUTION_AUTHORIZATION` only if all P0 source/science-scope/site/memory/journal/restart/observability checks are closed, including the selected uplift semantics. Otherwise report `R2_10K_PREFLIGHT=BLOCKED_<specific_reason>` and evidence. **No 10k job is authorized by this report or preflight.**

### Gate state

```yaml
R2_BOUNDED: PASS_FAIR_OPERATOR_REPORTED
R2_FRESH_1000Y: PASS_EXACT_RECONSTRUCTION_FAIR_OPERATOR_REPORTED
R2_1000Y_NUMERICAL_RETRY: NOT_REQUESTED
R2_10K_PREFLIGHT: NEXT
R2_10K_EXECUTION_AUTHORIZED: false
R2_10K_EXECUTED: false
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

Refs: `PROJECT_LEDGER/R6_INT10K_RUNTIME_R2_1000Y_EXECUTION_AUTHORIZED_GATE_20261030.md`, `PROJECT_LEDGER/R6_INT10K_RUNTIME_R2_BOUNDED_PASS_1000Y_RUN_GATE_20261030.md`, `PROJECT_LEDGER/ARCHITECTURE.md`, FAIR reports `docs/arcana/R6_RUNTIME_R2_1000Y_FAIR_20261030.md` / `docs/arcana/R6_RUNTIME_R2_STRUCTURAL_FAIR_20261030.md`.
