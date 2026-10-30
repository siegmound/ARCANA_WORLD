# R6-INT10K 1000Y FAIR — performance, persistence, implementation and new-chat handoff

**Recorded:** 2026-10-30 (Europe/Rome; dates of FAIR runs 2026-10-30). **Authority:** operator-provided FAIR stdout / audit outputs, corroborated by reading published R6 source at baseline `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839`; evidence files themselves were **not fetched from FAIR** in this ledger-writing session. This is a **DOCUMENTED_ENGINEERING_RESULT**, not a new science seal, WORLD_HISTORY production authorization, or claim of current GitHub publication of FAIR-only code. This file is the detailed continuation anchor for E2-C/E2-D; consult `STATUS.md`, `NEXT_ACTION.md`, `EVIDENCE_INDEX.md` and `PROCEDURE.md` first.

## 0. Mission and irreversible boundaries

ARCANA WorldSim aims to generate causal, geographically/time-queryable, reconstructible world history from ~210 Ma to 0 ka: tectonics, geology, climate, hydrology, material/natural resources, Deep, flora, fauna, lineages, peoples and social history. It must support a precise query about location, time, quantity, material provenance, uncertainty, and selectively higher-resolution regional/time replay. Not a population-only simulator. R3/R4/R5 are historical/legacy experiments, **not scientific outputs to force R6 to reproduce**. No single arbitrary global persistent timestep; provider internal timesteps and retained significant states are distinct.

**INT10K 1000Y is a 3×3 synthetic regional engineering experiment** coupled to two hash-verified E0 subsurface source columns C028/C029 (and synthetic surface/hydrology/Deep settings). It is not a real 1000-year ARCANA planet history. All of `WORLD_HISTORY_PRODUCTION_AUTHORIZED`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED`, `F2B_SOLVER_EXECUTION_AUTHORIZED`, `ARCANA_SI1_MECHANICS_QUALIFIED` remain **false**, as do general scientific permission for these synthetic experiments. A one-off operator-authorized FAIR interactive benchmark is **not** blanket authorization to run costly jobs on shared infrastructure.

## 1. FAIR source, Git, working directories — do not destroy

Repository: `https://github.com/siegmound/ARCANA_WORLD`.
- Published baseline R6 code branch `r6/multiphysics-integration-20261026` baseline HEAD `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839`; earlier E2-B2-R1 Linux qualification pinned there.
- Geometry ULP correction and test **FAIR_LOCAL_COMMIT**, branch `r6/geometry-ulp-r1-fair`, full SHA **`9dce77b5d65d4301d2145f9ad527b8efee0fe96d`**, parent `9d9a2512...`. A successful `git commit` on FAIR was shown. **No push of this SHA to GitHub was shown**: do not claim remote publication. Git identity was supplied per-command for this commit; no persistent config is required.
- Reuse existing FAIR worktree `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`. It is a linked Git worktree of the unchanged, detached source checkout at `.../ARCANA_WORLD_EVIDENCE/R6/INT10K_1000Y_OBSERVE_sNc82fLw/source`. Do **not** create another clone or change historical F2AV worktree. For source work: check `git rev-parse HEAD`, `git branch --show-current`, `git status --short`, and remote before mutation.
- This PROJECT_LEDGER is currently maintained on separate GitHub branch `docs/r6-project-ledger-20261010` (not assured present on the FAIR R6 code branch); before bringing docs into FAIR, inspect divergence and merge explicitly, never overwrite existing worktrees.
- Linux conda `arcana-r6-linux`, Python 3.12.14, NumPy 2.5.3 (E2-B2 qualification); original E0 files: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E1_R2_I6OODuU9/original_inputs`. Keep all input/result/manifest SHA constraints and source locks.

### Preserved FAIR evidence roots

All paths below share `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/`:
1. `INT10K_E2_A1_FAIR_kjB2nxDO`: original immutable 3Y/10Y oracle evidence; do not overwrite.
2. `INT10K_E2_B2_R1_FAIR_YhQ4gPTE`: 79/79 Linux tests, exact source qualification, 3Y 1+2 and 10Y 5+5 oracle parity, as earlier operator-reported.
3. `INT10K_1000Y_OBSERVE_sNc82fLw`: **original failed 1000Y first-year run**, `SURFACE_GEOMETRY_VOLUME_BALANCE_FAILED`. Leave FAIL unchanged.
4. `INT10K_1000Y_GEOMETRY_DIAG_Ewx1utQY`: read-only geometry numerical audit, PASS diagnostic only.
5. `INT10K_1000Y_GEOMETRY_R1_YJBeAKT4`: **completed 1000Y** `PASS_1000Y_ENGINEERING_EXECUTION_COMPLETE`; immutable source of 1000Y results.
6. `INT10K_1000Y_COST_ANALYSIS_Kaw8pV2x`: derived cost audit, `COST_ANALYSIS=PASS`; read-only new directory, not an original source seal.
7. `INT10K_1000Y_RECORD_AUDIT_AyVB7iSW`: index kind/100-year audit, `RECORD_KIND_COST_AUDIT=PASS`; derived.
Do not treat a local path recorded here as proof that a new chat has access; require operator read/manifest SHA validation.

## 2. The first-year bug and validated bounded fix

Original 1000-year configuration uses total synthetic uplift 0.1 m on C028 divided over 1000 steps: `0.0001 m` per year. The surface volume check subtracted two O(3.7e11 m³) floating-point values and used too-small absolute tolerance:
- observed delta `1235991.7892456055 m³`, expected `1235991.7892347989 m³`;
- signed residual `1.0806601494550705e-05 m³`;
- legacy `isclose` tolerance `1.2359917892456055e-06 m³`, FAIL;
- measured initial+final ULP budget `0.0001220703125 m³`.
Correction in `src/arcana_worldsim/r6/geological_surface_microdomain.py`: retain physical balance and relative tolerance `1e-12`, compute dynamic absolute tolerance `max(1e-6, fsum(ulp(v) for v in (initial_surface_volume,final_surface_volume,uplift_volume)))`. No physical operator/uplift/transport was modified. Add `tests/test_r6_int10k_surface_small_uplift_precision.py` with valid fixture `t0_boundary_id`. First version of fixture failed only on missing ID (85 pass/1 fail); then fixed and committed. **First full engine year at planned 1000Y PASS**, `ACTIVE_SOURCE` confirmed FAIR corrected worktree. A 24-test subset PASS before fixing fixture; the later 86-test/parity log was not independently included in this ledger session: retrieve/verify logs before claiming exact requalification. Exact `9dce77b5` commit comprises 2 files, 79 insertions/1 deletion.

The revised control tolerates representation roundoff of the computed volumes; do not weaken arbitrary invariants to hide future failures. A separate scientific precision audit may still be necessary for very small surface changes or large accumulated error.

## 3. 1000Y performance, output integrity and timestamps

FAIR completed under SHA `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`, `RUN_EXIT=0`, `1000Y_EXECUTION=PASS`. Exact completed evidence manifest SHA256:
`e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.
- `completed_years=1000`, `wall_seconds=244.78096017614007` for 1000Y loop including progressive writing/checkpoint work; `process_cpu_seconds=242.02050732600003`; `max_rss_bytes_os=103260160` (~98.48 MiB).
- `HISTORY.jsonl=1916080917 bytes` (~1.916 GB decimal / 1.784 GiB). `INDEX.jsonl` + `YEAR_METRICS.jsonl`, checkpoint outputs, samples and report in `1000y/`.
- From timestamps (not a dedicated full-pipeline timer): `YEAR_METRICS_END 2026-10-30T00:38:47`; `REPORT_CREATED 00:39:12`; `MANIFEST_CREATED 00:39:13`; `FINAL_STATUS 00:39:13`. Post-loop ~25.731 s, audit ~24.401 s, manifest ~1.286 s; **estimated wall end-to-end ~270.512 s**, excludes separate preflight and user-perceived waiting.
- `YEAR_METRICS.jsonl` contained 1000 years; sum `wall_step_s=231.733 s`, remaining loop time ~13.048 s **not attributed** to annual steps. Those annual steps include motor work, state copies, JSON/hashes, checkpoint work—not pure physics.
- OS resource samples `237`, peak RSS ~98.5 MiB. Runner is **single-process, predominantly single-core**. Loop CPU / wall ~98.87% overall; per-100y CPU/wall 95.39–100.14%, likely one fully occupied CPU-equivalent with no strong evidence of sustained loop I/O stalls. Per-process >100% over some windows is possible due to timing granularity. Post-loop CPU fraction *not measured*; do not assert this phase was CPU- or I/O-bound without profiling.
- The JSONL writer is a diagnostic non-transactional archive; a successful audit does not establish crash-consistent production persistence. E2-C/D still pending.

100-year bins from operator `COST_BY_100Y.csv` / `YEAR_METRICS.jsonl`:

| Years | wall_s | avg ms/year | new HISTORY MB | HISTORY cum GB | final checkpoint MB | peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|
| 1-100 | 6.81 | 68.13 | 32.70 | 0.033 | 0.526 | 46.7 |
| 101-200 | 10.18 | 101.78 | 67.84 | 0.101 | 0.880 | 51.7 |
| 201-300 | 14.47 | 144.70 | 103.21 | 0.204 | 1.234 | 56.7 |
| 301-400 | 17.40 | 173.97 | 138.56 | 0.342 | 1.587 | 64.0 |
| 401-500 | 22.17 | 221.70 | 173.92 | 0.516 | 1.941 | 70.1 |
| 501-600 | 24.75 | 247.45 | 209.27 | 0.725 | 2.294 | 76.3 |
| 601-700 | 28.25 | 282.48 | 244.62 | 0.970 | 2.648 | 81.1 |
| 701-800 | 32.80 | 327.99 | 279.97 | 1.250 | 3.001 | 86.9 |
| 801-900 | 35.45 | 354.52 | 315.32 | 1.565 | 3.355 | 94.3 |
| 901-1000 | 39.46 | 394.62 | 350.67 | 1.916 | 3.708 | 98.5 |

Mean step grew 68.13→394.62 ms (~5.79×), history per century 32.70→350.67 MB (~10.72×), checkpoint ~0.526→3.708 MB. Annual time-history growth correlation `0.8904569561505411` and time-checkpoint size correlation `0.8904584673011295` are **not causal attribution**: both reflect increasing simulation time / deposit count.

## 4. Historic record composition — measured root of quadratic growth

`INDEX.jsonl` validated, offsets reconciled to all `1916080917` HISTORY bytes, `61001` indexed envelopes. `REGIONAL_SNAPSHOT` dominates history ~92.6% (~1.774 GB). Per-century sizes:
- `REGIONAL_SNAPSHOT`: 18.557 MB (1–100), 53.694, 89.047, 124.400, 159.754, 195.105, 230.455, 265.808, 301.161, **336.514 MB** (901–1000), **18.134×** first/last.
- `REGIONAL_YEAR_RECORD`: 2.812→2.822 MB, ~constant.
- `UNIFIED_STEP`: 9.215→9.212 MB, ~constant.
- `REGIONAL_EVENT`: 1.793→1.810 MB for dated rows, ~constant. **UNKNOWN temporal group** ~3.126 MB of REGIONAL_EVENT records lacking indexed `time_year` — investigate whether events instead use `detected_at_year` / other timestamp semantics; preserve exact temporal semantics rather than inventing times.
- Direct indexed snapshot reads (original HISTORY, three specific years): at year 100, snapshot 0.358 MB, 1100 deposits, deposits 0.349 MB = **97.31%**. Year 500, 1.773 MB, 5500 deposits, 1.763 MB = **99.46%**. Year 1000, 3.540 MB, 11000 deposits, 3.531 MB = **99.73%**.
- Published source at baseline: `regional_geological_evolution.py`, `advance_region()` clones whole state via `json.loads(_canonical(dict(state)))`, appends new `cell["deposits"]` with material, mass, density, source/destination, erosion/transport/deposition years and event ID, then constructs `snapshot={"time_year":year,"cells":json.loads(_canonical(cells))}` each year and passes it to history consumer. `run_regional_segment()` clones/checkpoints the growing state each segment and performs checked history-independent frontier sealing. This **directly explains duplicate historical deposit payload in each full snapshot** and strong O(year²) history-size growth on this observed case.
- Despite big output, per-step history is externalized, avoiding storing all snapshots in process RAM; peak RSS stays modest. Causally distinguish duplicated storage volume (established), CPU cost attributable to each JSON copy/validation/solver (requires new phase profiling).

## 5. FAIR host hardware and actual execution

Operator `lscpu`: **2× Intel Xeon Gold 6530**, 32 physical cores/socket, **64 physical cores / 128 SMT logical CPUs**, 4 NUMA nodes; node CPU lists: N0 `0-15,64-79`, N1 `16-31,80-95`, N2 `32-47,96-111`, N3 `48-63,112-127`. NUMA distance matrix diagonal 10, within socket 12, cross socket 21. `os.cpu_count()=128`, `sched_getaffinity` allows all 128 logical CPUs. RAM `1.0 TiB`; `available ~979 GiB`, large file cache (~977 GiB), `free ~7.7 GiB` is not actual allocatable limit. Swap 8 GiB, 1 GiB used. **2× NVIDIA RTX 5090** with 32607 MiB reported VRAM per GPU (CUDA sm_120 per prior hardware characterization), neither involved in current Python loop.
`/proc/self/cgroup`: `0::/user.slice/user-1006.slice/session-58509.scope`. Reading `/sys/fs/cgroup/cpu.max` and `/sys/fs/cgroup/memory.max` returned "not available"; **this is root-path probing, not proof of unlimited cgroup quota**. Query effective cgroup path under `/sys/fs/cgroup/user.slice/user-1006.slice/session-58509.scope/` and its ancestors; validate job policy/usage rules. No `squeue`/`qstat` command was found in operator check. FAIR's shared-compute authorization remains external; do not schedule 64-core load just because all CPUs are visible.

The 1000Y run's near-100% CPU/wall is ~one fully utilized CPU-equivalent or ~1.6% of 64 *installed* physical cores, not ~100% workstation utilization. Do **not** assume linear 64× speedup; 1000 annual steps are causally dependent and 3×3 cells provide insufficient spatial work. Parallelize independent spatial tiles/domains after deterministic causal/halo contract; asynchronous writer/hash processes only after parity/replay preservation is demonstrated. NUMA pinning first-touch/memory locality; GPU only for sufficiently large vectorized numerical kernels with transfer/sync accounting.

## 6. Approved architectural direction — MATERIALIZE / DERIVE / REFINE

Codex is **design-time auditor/implementer and optionally read-only analyst**, *not* free-running AI deciding what to discard independently at every timestep. The simulation applies a **deterministic, versioned, governed retention policy**. It must preserve all non-derivable causal information and exact provenance; any inability to reconstruct or prove the tolerance must force retention or fail-closed. A possible historical storage budget (prior discussion: ~250 GB target / ~500 GB ceiling) is at most a **planning hypothesis**, not an authorization to drop evidence nor a benchmark resource cutoff.

**MATERIALIZE**: source/provider hashes, versions, schemas, domain applicability, grid IDs/geography, initial/forced boundary states, config, seeds/random state, solver tolerances, numeric precision, external forcing schedules, adaptive step decisions, event brackets and actual event times if known, immutable material/deposit identities and provenance, material changes (create, transport, deposit, transform, split, merge, consume, export), exact mass/energy ledgers and uncertainties, sparse recovery checkpoints and significance-selected state anchors. Retain original ordered layer/deposit semantics and all needed floating-point state values, not merely rounded/aggregated summaries.

**DERIVE**: historical snapshots and query views reconstructed deterministically by applying versioned event/delta streams to a known checkpoint, replaying the original provider only where provenance, deterministic numerics and a replay budget allow. Rehydrate the precise deposited layer ordering, IDs, masses, compositions, provenance and positions at arbitrary archived times. If floating operations would change canonical bytes due to associativity/order, retain the exact post-state value/delta representation rather than claim bit-exact equality from approximate recomputation.

**REFINE**: spawn separately identified higher-resolution temporal/spatial analysis from a governed anchor with provider/boundary inputs and causal context; must preserve lineage/uncertainty; is **not interpolation** and cannot manufacture UNKNOWN physical states or authorize future real-world simulation. Original coarser history remains immutable.

### Candidate E2-C/E2-D data model (DESIGN ONLY, not yet coded)
- Immutable `RUN_ID`/source lock + manifest with policies and `schema_version`.
- `CELL_STATIC` / IDs and geometry source; `INITIAL_STATE` (or anchor); append-only `MATERIAL_EVENT` & `CELL_DELTA` (signed/typed, deterministic order, event IDs, material provenance, deposit ordering and exact post-values); `DOMAIN_STEP` and balance summaries.
- `ANCHOR_CHECKPOINT` with minimal **sufficient** frontier state, domain clocks, random generator states, solver/provider state, outstanding flows/coupled-domain state, cumulative balances and provenance; checkpoints need not include every previously archived annual full snapshot. Checkpoints at 100/250/500/750/1000 in current experiment were *engineering schedule only*, not a universal retention interval.
- `REPLAY_INDEX` time/cell/material/event-to-segment offsets, byte sizes/hashes, coordinate grid/version, causal dependencies and `UNKNOWN` flags. Per-event stable ID (existing `event_id` candidate **requires uniqueness validation**; do not infer universally unique ID).
- `PREPARE`→write+fsync data/index+checkpoint→manifest hash chain→`COMMIT` atomically visible; on crash recover only fully committed intervals, detect partial tail, preserve old committed hash chain. Exact transaction protocol to be designed/tested: current runner **does not implement it**.
- Keep 1000Y original uncompressed canonical full-snapshot JSONL **as immutable oracle**. Develop converter in new evidence root; never rewrite original or alter source/source lock. Compression (e.g. chunked) can be separately evaluated after deterministic decoded byte equivalence, indexing and random access; not a replacement for lossless causal modeling.
- Query modes: `AS_RECORDED`, `RECONSTRUCTED_EXACT`, `DERIVED_WITH_TOLERANCE`, `UNKNOWN` visibly distinguished. WORLD_HISTORY claims cannot be promoted from INT10K.

### Exact equivalence / acceptance gates
1. Original 1000Y `MANIFEST.json` hash and each relevant member bytes/sha verified before read. Recheck after read. Source SHA for converter/reader fixed and clean; record Python/OS/library versions and input E0 SHA256. No in-place mutation.
2. Build event/delta mapping for all 1001 snapshots (0..1000), all 9 synthetic cells and material identities. Compare at 0, 1, 100, 250, 500, 750, 1000 AND exhaustive 0..1000 before parity PASS; verify canonical JSON payload hash where guaranteed, otherwise fieldwise typed exact identity + declared float tolerance **only after scientific approval**, never silently relax.
3. Prove counts/order of 11000 final deposits (and intermediate), layer ordering, unique identities, provenance/source/destination, times and mass/energy balances, exported material, Deep time series from `UNIFIED_STEP`; include negative/corruption/missing event tests.
4. Independent 3Y 1+2 and 10Y 5+5 parity against immutable FAIR E2-A1 oracle with the new reader and source exact pin; no shortcut claiming 1000Y PASS proves them. Historical first-year geometry correction regression remains mandatory.
5. Performance: compare real file sizes, index overhead, random historical query latency (year, cell, material), reconstruction CPU/RAM, time-window selective replay, write+fsync/transaction overhead, source/target NUMA affinity; include correctness under killed/interrupted writer. Avoid preselected pass thresholds that merely reward performance at expense of correctness.
6. Distinguish `CODE_READY`, `LOCAL_LINUX_TEST_PASS`, `FAIR_RUNTIME_EVIDENCED`, `EXACT_REPLAY_PASS`, `SCIENTIFIC_AUTHORITY`, `CANONICAL_PRODUCTION_AUTHORIZED`.

## 7. Immediate recommended implementation and measurement sequence

**E2-C0 / diagnostic-first / read-only:** in the **existing FAIR worktree** (no new clone) and a **fresh evidence output directory**:
1. Verify `git status --short`, branch and SHA `9dce77b5...`; confirm original 1000Y evidence manifest hash and the 3Y/10Y parity logs before relying on those. Verify actual cgroup limits via resolved `/proc/self/cgroup` path + ancestors, operator permission and available CPU budget; do not spawn unrestricted 128-thread jobs.
2. Use `cProfile` or deterministic phase timers (in new profiling instrumentation branch; no modification of original evidence) to isolate `run_unified_microdomain`, `advance_region`, `_canonical` + JSON state clone, snapshot deep copy, archive `Writer.emit`, checkpoint `seal`+`verify`, SHA, and fsync/audit; gather wall and process CPU separately, `/proc/<pid>/io`, user/system CPU and contextual switching; repeat at early/late checkpoints, equivalent source and config. First choice: bounded replays of individual years from available checkpoints 100/250/500/750 under a new output root; confirm checkpoint source and identity constraints. Do not assume 1000Y original runner supports transactional resume.
3. Profile resident deposit list **and** exact payload duplication per record category. Investigate 3.126 MB `REGIONAL_EVENT` with unknown indexed year; preserve time semantics.
4. Decide design only after measured breakdown; no speculative MPI/GPU optimization or patch stacking. Establish pass/fail tests *before* transformation.

**E2-C1/C2:** trace/write exact new event/delta+anchor format, deterministic reader + reconstruction, 1000Y oracle parity in new evidence; retention policy version and index; prove zero loss of historical detail. Reuse existing R6 B0 HistoryStore/query/replay/retention if compatible after auditing its real API/contracts rather than constructing a competing store.

**E2-D1:** eliminate redundant state clones/whole-history JSON churn **within proven equivalence**; introduce efficient immutable/persistent deposit structures, copy-on-write or generational indexes, cached hashes where correct, bounded canonical serialization. Separate current simulation-state from archive representation; do not compromise checkpoint sealing or temporal identity.

**E2-D2:** only after E2-C1/C2 correctness, profile/experiment with independent region partitions and separate writer/analytics workers (processes avoiding Python GIL), NUMA-local scheduling and accelerator candidate kernels. No GPU obligation on nine-cell benchmark; use real resource-allocation limits and reproducible measurable speedup/efficiency, not workstation-usage targets.

**E2-E/F later:** transactional crash recovery, source/config locking, exact replay and scaling at higher spatial resolution; scientifically qualified provider coupling & future 210Ma→0ka remain separate gates.

### Next chat exact entrypoint
Read `PROJECT_LEDGER/NEW_CHAT.md`, `README.md`, `STATUS.md`, `NEXT_ACTION.md`, **this file**, `EVIDENCE_INDEX.md`, `DECISIONS.md`, `PROCEDURE.md`. This GitHub docs branch is separate from FAIR local source branch. Read actual FAIR evidence if accessible; operator must run/check commands otherwise. The next task is **E2-C0 read-only cost-phase profiling and audit of existing B0 retention/replay APIs**, then propose a tested E2-C1 schema. Do NOT re-run 1000 years or clone a repo merely to get a handoff. The source-geometry fix `9dce77b5...` is FAIR-local unless independently confirmed remote. Do not overwrite previous FAIL/PASS artifacts. Before any run on FAIR, follow site policy. **No canonical history production is authorized.**
