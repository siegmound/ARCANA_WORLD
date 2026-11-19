# Runtime Copy R1 — FAIR exact oracle and measured speedup

## Current outcome — authorized candidate 1000Y completed, 2026-10-30

The user explicitly authorized the proposed one-off 1000Y gate with
“non imporre limiti ma fa partire la simulazione”. The run completed naturally
with exit 0 and no added application duration, memory, thread or output caps.
No extra solver, 10k run, commit, push or change to the engine patch was made.

**Engineering marker:**
`R6_INT10K_RUNTIME_R1=PASS_EXACT_ORACLE_AND_MEASURED_SPEEDUP`.
Scope: the opt-in detached-copy candidate, with exact unchanged public output
and controlled anchor speedups. This does not qualify scientific/production
authority, solve quadratic scaling or enable the optimization by default.

New runner `scripts/r6_int10k_runtime_r1_1000y.py` binds the previously measured
source hashes, original E0 pins and oracle manifest. It advances exactly 1000
annual segments with constant planned duration 1000, verifies every emitted
index/payload against the original in order, checks balances and frontier at
every step, fsyncs the original milestone schedule and saves full-value output.
Resource sampling is observational. All measured sources, inputs and original
manifest members were independently rehashed after completion, unchanged.

Command (already executed; output directory must never be reused):

```bash
PYTHONPATH=src PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python \
scripts/r6_int10k_runtime_r1_1000y.py \
--output /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/RUNTIME_R1_CANDIDATE_1000Y_20261030_01
```

Validation:

- **61,001 ordered payloads exact:** 1001 snapshots, 1000 regional annual
  records, 1000 unified steps and 58,000 events. This is a newly generated
  candidate trajectory, closing the previous archived-snapshot-only limitation.
- **Entire HISTORY and INDEX byte-identical** to the original archive: equal
  SHA256 and lengths, including NULL times, order, provenance and material IDs.
- **Five checkpoints byte-exact** at years 100, 250, 500, 750 and 1000, proving
  regional/unified frontier, Deep and full restart state equality.
- All annual water/solid balances and checkpoint integrity checks passed.
  8000 source event timestamps remain NULL. Original scientific gates stay false.
- Prior 141 focused regressions, short split parity and seven-repeat anchor
  evidence remain applicable: their measured engine/test hashes are unchanged.

| Measurement | Candidate 1000Y |
| --- | ---: |
| Loop wall, including writer, checkpoint verification and telemetry | 214.125572 s |
| CPU user / system | 207.380428 / 2.500732 s |
| Equivalent utilized cores | 0.98018 |
| Engine calls including consumer | 165.688599 s |
| Additional outer checkpoint verification | 30.671669 s |
| Checkpoint byte encoding for observation | 12.284822 s |
| Annual wall median / p95 / maximum | 0.208915 / 0.354151 / 2.008016 s |
| Peak RSS, `/proc/self/status` VmHWM | 125,304 KiB (122.37 MiB) |
| HISTORY | 1,916,080,917 B |
| INDEX | 10,685,396 B |
| Final checkpoint | 3,708,267 B |
| Complete output, including source snapshot and manifest | 1,938,809,781 logical B; 1,938,997,248 allocated B; 83 files |

The measured pre-manifest end-to-end wall is 217.144785 s; final manifest
construction and subsequent independent audit are additional work. The first
100-year window took 6.744983 s and the final window 36.419843 s, confirming
the continuing growth in annual cost. Full window telemetry is in REPORT.json.
128 NumPy threads were present (129 including the sampling thread), but measured
CPU/wall corresponds to about one utilized core. No thread limit was imposed.

Writer components include 12.239689 s payload encoding, 1.015197 s payload SHA,
13.339210 s envelope/index encoding, 1.921383 s writes plus stream hashing,
4.434599 s flush/fsync, and 0.036883 s online oracle comparison. These are
subcomponents of the engine/loop measurements, not additional totals to add.

Historical baseline loop: 244.780960 s; candidate: 214.125572 s, an indicative
12.52% reduction (1.143×). This is one new full run against a historical run
with differing provenance and observation overhead; it is not a controlled
repeated full-run comparison. The matched seven-repeat anchors remain the
controlled speedup evidence (1.084×, 1.175×, 1.192×). No storage or memory
reduction is claimed; preloaded oracle indices and telemetry affect RSS.

Evidence (FAIR_EXTERNAL_EVIDENCE):

- `RUNTIME_R1_CANDIDATE_1000Y_20261030_01`: 82 manifest members verified.
  REPORT SHA256 `76dc09d0bf40e76540e9a5dc9f571b3ec946f370def3b6358b92aa7f19e3eef8`;
  MANIFEST SHA256 `3142804095c065f46c740a7ab0a21ff32160ac00b73053f8eaf78d6a2db1840b`.
- `RUNTIME_R1_ACCEPTANCE_20261030_01/ACCEPTANCE.json`: SHA256
  `1ea36053d25095e3a9897cb52ef30c88a8d05f58d674178e37231bfd16070313`.

Next: review the qualified opt-in candidate and the separate 10k execution
contract below. The 1000Y permission does not authorize a 10k run. Actual FAIR
allocation/site limits, reviewed source identity and the run-level uplift
configuration remain explicit prerequisites. No further optimization is applied
in this gate; all scientific and production authority flags remain false.

---

## Previous bounded audit record — before the 1000Y authorization

2026-10-30. Authority: FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE. Uncommitted
candidate on `r6/runtime-copy-r1-fair`, based on
`2c71370eb9a959c78121ce1c88ec8e9e37187787`. No commit, push, merge or 10k run.

**Outcome: CODE_READY_BOUNDED_EXACT_PARITY; full R1 acceptance remains BLOCKED.**
This is a measured constant-factor improvement, not elimination of growing-state
cost or qualification of a 10k run. The candidate remains opt-in and disabled by
default. No second optimization is stacked on the pending acceptance gate.

## Preconditions and scope

The starting branch `r6/e2c1-frontier-projection-r1-fair`, exact HEAD and clean
worktree matched the assignment. R3 source/test SHA pins and all three original
E0 input pins matched. Runtime: FAIR, arcana-r6-linux, Python 3.12.14,
NumPy 2.5.3, pytest 9.1.1. All original 1000Y manifest member lengths and hashes
were independently checked before the bounded audit. Manifest SHA remains
`e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.

The supplied Runtime R1 task and ledger supersede the older E2-B2 priority in
the committed project ledger. The user's explicit FAIR implementation request
provides the exception to the historical Windows-only authoring workflow.
The user's no-commit instruction takes precedence over the ledger's normal
same-commit documentation rule; these handoff edits remain uncommitted.

## Diagnosis and complexity

Let D(y) be accumulated deposits at year y, H the historical payload retained in
the current invocation, and C the nine cells. The authentic oracle ends with
11,000 deposit rows. With approximately linear deposit growth:

| Operation | Existing cost | R1 candidate |
| --- | --- | --- |
| `advance_region` entry copy | JSON encode + decode, O(D + H), transient bytes and detached objects | Exact detached recursive copy, O(D + H), no temporary JSON for ordinary values |
| Annual full snapshot | Encode + decode all cells/deposits, O(D) | Exact detached copy, still O(D) |
| Frontier projection | Encode excluded history; encode + decode retained frontier | Excluded validation unchanged; retained frontier copied directly |
| Seal/verify regional, outer and unified checkpoints | Repeated full canonical encoding, hashing; unified also detaches by JSON | Unchanged |
| Solid/cell balances, `_geologic_load` inventory/thickness/provenance | Several ordered deposit scans, O(D) | Unchanged |
| `HistoryCollector.emit/export` | Additional validation, JSON roundtrip and complete history copies | Unchanged |
| SHA consumer / full-value writer | O(D) encoding/hashing/output per year | Equivalent work measured explicitly |

The annual copies and scans still accumulate O(Y²) time when D(y)=O(y).
Persistent full snapshots still require O(Y²) bytes; history-free frontier is
O(Y), not bounded in deposit age. A multi-year invocation retaining snapshots
also has O(Y²) historical memory. There is no claim of asymptotic improvement.

Append-only deposits are created in `advance_region`; the inspected operator
does not edit older rows. Exploiting that property safely requires an explicit
immutable ownership/COW boundary and a compatible logical snapshot adapter.
Mutable public dicts and consumer mutation preclude simply sharing those rows.
An incremental material total must also reproduce each separate floating-point
reduction order, including per-material interleaving, mass/density thickness
and provenance ordering. R1 does not substitute rounded or reordered counters.

## Minimal implementation

Only `src/arcana_worldsim/r6/regional_geological_evolution.py` changes engine
behavior. `_clone_canonical_json` handles exact built-in JSON types, sorting
string dictionary keys to preserve the reference roundtrip's iteration order.
It copies every mutable container and every repeated occurrence independently.
Finite floats, negative zero, strings and small integers retain their values.
Non-ordinary values, non-string keys, large integers, deep nesting and cycles
fall back to the original roundtrip, preserving normalization and rejection.
UTF-8 surrogate rejection is retained.

`runtime_copy_optimization=True` selects this copy in `advance_region` (entry
state and annual snapshots), `_project_validated_history_free_frontier` and
`run_regional_segment`. The default remains the reference path. No numerical
formula, timestep, forcing, authority flag, output schema or checkpoint hash
algorithm changes. Excluded-history canonical validation remains mandatory.

New files:

- `tests/test_r6_runtime_copy_r1.py`: reference equivalence, detachment, Unicode,
  large-integer/tuple/key normalization, cycles, NaN/Inf/object rejection,
  randomized JSON, deep fallback, annual 10Y parity and history-free frontier.
- `scripts/r6_int10k_runtime_r1.py`: bounded exact oracle benchmark and offline
  all-snapshot copy proof. This runner cannot start a 1000Y or 10k evolution.

## Validation

Test-first collection initially failed because the copier did not exist.
After implementation and final fallback/negative tests: **141 passed in 1.64s**,
zero failure/skip. Command: arcana-r6-linux `python -m pytest -q -p no:cacheprovider`
with `PYTHONPATH=src`, `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`, covering
the new runtime tests, both E2-C1 projection suites, history-independent,
regional, frontier-checkpoint, full-history-oracle, short-reference,
source-provenance, uplift-precision and unified suites.

- Each y101/y501/y751 replay: exact ordered kind/payload SHA equality for all
  61 envelopes, in baseline and candidate, warm-up and seven repetitions.
- Entire baseline/candidate result canonical SHA identical at each anchor:
  includes checkpoints, frontiers, hydrology, Deep, material/water/solid
  balances, events and history coverage. Output and checkpoint byte sizes match.
- 3Y direct vs 1+2: 184 original oracle items exact by kind; checkpoint,
  balances and subsurface state byte-exact. Complete direct candidate result
  also equals the reference path.
- 10Y direct vs 5+5: same proof for 611 original items.
- NULL event timestamps, IDs, material provenance and event order are inside
  the exact payload hashes; no new timestamp is inferred.
- All 1,001 authentic snapshots at years 0..1000, nine cells each, copied by
  the candidate helper: exact original canonical SHA. Final count 11,000 deposits.
  **This validates the copier on archived snapshots. It is not a candidate
  1000Y trajectory, new delta representation or new writer reconstruction proof.**

## Measurements

Final evidence directory:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/RUNTIME_R1_COPY_AUDIT_20261030_03`.
`REPORT.json` contains samples, user/system CPU, writer timings, checkpoint/output
bytes, peak process RSS, and separate instrumented phase wall / exclusive CPU.
`SOURCE_SHA256.json` pins all R6 modules, runner and new tests; unchanged at end.
`SOURCE_DIFF.patch` captures the engine diff; `FILE_MANIFEST.json` hashes outputs.

One fresh subprocess per anchor/mode, one discarded warm-up plus seven measured
annual calls. Both modes hash every payload and write equivalent full-value
JSONL. Flush is included; fsync, durable store/index transactions and process
startup/input/oracle reads are excluded from annual wall. This benchmark is
distinct from the historical 244.78-second 1000Y loop and cannot replace it.

| Replay year | Baseline median ms | Candidate median ms | Speedup | Time reduction | Baseline/candidate p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| 101 | 65.867 | 60.752 | 1.084× | 7.77% | 69.291 / 60.837 |
| 501 | 175.898 | 149.675 | 1.175× | 14.91% | 178.366 / 153.280 |
| 751 | 247.157 | 207.357 | 1.192× | 16.10% | 255.036 / 212.154 |

The observed baseline/candidate sample ranges do not overlap at any anchor;
two preliminary batches showed the same direction. Seven samples are not a
robust distributional/tail estimate: nearest-rank p95 here equals the maximum.

| Year | Median user/system ms, baseline | Median user/system ms, candidate | Output bytes/year | Checkpoint bytes |
| --- | ---: | ---: | ---: | ---: |
| 101 | 65.881 / 0.000 | 60.769 / 0.000 | 496,361 | 529,942 |
| 501 | 173.988 / 1.999 | 147.986 / 1.999 | 1,910,670 | 1,944,172 |
| 751 | 243.083 / 4.004 | 204.616 / 2.998 | 2,794,299 | 2,827,818 |

Medians of user/system components need not sum to the median total. CPU/wall is
approximately one utilized core. No multi-core scaling claim is made.
Recorded process ru_maxrss is 113,740 KiB for every worker. This high-water mark
includes setup/profiling and may inherit the fork parent's prior maximum;
it does not establish a candidate-only peak or a memory improvement.

At y751, median payload encoding is 17.516/17.534 ms baseline/candidate,
consumer SHA 1.466/1.467 ms, and buffered writer/flush 1.528/1.159 ms.
The gain comes from the engine copy path; equivalent output encoding remains.
Total generated output and checkpoint sizes do not shrink.

Phase measurements use a separate instrumented cProfile call with a SHA-only
consumer. They are disjoint exclusive measurements, not inclusive totals added
together. Python recursion suffers larger profiling overhead than C JSON; these
phase numbers must not be used as the uninstrumented speedup estimate. Deep,
regional reductions and unwrapped bookkeeping remain within broader groups.

The first audit directory `_01` retains an interrupted audit: anchor/short
parity passed, but the offline reader used incorrect index field names and
raised `KeyError`. The reader was corrected to authentic `offset`/`length`.
`_02` is preliminary evidence. `_03` is the final pinned runner evidence.
No oracle or failed evidence directory was rewritten.

## Remaining gate and 10k execution contract

The requested R1 acceptance marker is deliberately absent. Machine marker:
`R6_INT10K_RUNTIME_R1=BLOCKED_FULL_CANDIDATE_1000Y_ORACLE_AND_AUTHORIZATION_PENDING`.
A separate user gate is pending for one candidate 1000Y trajectory using annual
calls and the original inputs/configuration, with all 61,001 original envelopes
and five original milestone checkpoints compared. Indicative output is about
2 GB and runtime several minutes; this estimate is not an execution guarantee.
The task explicitly requires a gate before heavy work. No answer to the gate
is treated as approval. No 1000Y/10k numerical run was launched.

After that gate and R1 review, a **separately authorized** 10k run must bind:

1. A reviewed exact candidate source snapshot/commit and measured-file SHA set,
   clean provenance or explicitly reviewed uncommitted-patch identity; all three
   E0 pins, configuration hash and original oracle manifest. No automatic commit.
2. `RegionalConfig(duration_years=10000)`, unified planned duration 10000,
   external step one year and `segment_years=1`; 3×3 cells, C028/C029 columns,
   existing constants, hydrology dt 31,557,600 s, opening 0.01 m/year, synthetic
   Deep and all existing balances. Run-level uplift total (0.1, 0.0) implies a
   different annual rate with the new planned duration: explicitly review this
   existing config behavior for both comparison arms before execution. Confirm
   provider/model support over the full horizon, not merely parser acceptance.
3. FAIR administrator/site permission and actual job allocation. This session
   sees CPUs 0..127 and session cgroup `cpu.max=max 100000`, `memory.max=max`;
   these are visibility readings, not reserved resources or proof of site
   permission. No scheduler job ID was observed. Resolve scheduler/site limits,
   effective cpuset/quota and output quota before launch. Host free disk about
   15 TiB is not a user quota. Do not claim 128-core utilization from visibility.
4. New external run directory, never an original archive. One process/no extra
   solver, record thread environment and libraries. Observe real scaling under
   actual site limits, without invented application RAM/time/output caps.
5. Per-year wall and CPU user/system; per-domain numerical, copy, serialize,
   hash/checkpoint and writer phases; sampled process-tree RSS/cgroup peaks;
   logical/allocated disk bytes, file counts, events/deposits and checkpoint
   bytes/times. Summarize p50/p95/max and each 100-year window. Preserve NULL
   timestamps, full causal records, integrity and failure evidence.
6. Full checkpoint persistence at years 100, 250, 500, 750, 1000 and each later
   1000-year milestone, plus final; verify before resume. Check selected exact
   next-year replay and genuine interrupted continuation, with same source and
   input identity. Stop on actual balance/hash/clock/source invariant failure.
7. An equivalent baseline arm only when independently justified and authorized.
   With unchanged full snapshots the old growth extrapolation suggests roughly
   100× the 1000Y HISTORY bytes (order 190 GB), not a safe resource forecast.
   Compare bounded equal-work anchors if a full 10k baseline is unreasonable;
   never compare different physics or hide reconstruction/writer work.

The current bounded runner is deliberately not a 10k launcher. A reviewed
long-run runner and exact launch command remain prerequisites, rather than an
executable command against an unqualified engine.

`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`
`GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`
`ARCANA_SI1_MECHANICS_QUALIFIED=false`
