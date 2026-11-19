# R2-L1 — opt-in REC1 launcher, bounded qualification

2026-10-30. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`R2_L1_BOUNDED=PASS_LAUNCHER_SOURCE_AND_RESUME_PARITY`

The launcher is qualified for the bounded scope below. No new 1000Y/10k/100k
numerical trajectory, commit, push, merge, reset or original archive mutation.
The 10k benchmark is not authorized. Scientific/production flags remain false.

## Identity and implementation

Worktree `ARCANA_WORLD_R6_GEOMETRY_R1_WORK`, branch `r6/runtime-copy-r1-fair`, HEAD
`2c71370eb9a959c78121ce1c88ec8e9e37187787`. All 22 pre-existing dirty/untracked
files were copied before L1 and verified unchanged before the ledger update.
All REC1 source pins remain unchanged, including the numerical engine, compact
runtime, explicit uplift plan, B0 store and recovery controller. L1 adds only:

| File | SHA256 |
| --- | --- |
| scripts/r6_runtime_r2_launcher.py | 7844b40dd68d879850de4500370aa6418009496747e3d04634556880836b6dd9 |
| tests/test_r6_runtime_r2_launcher.py | 9eac97317bdd84889f0b5cecd894706971cd02cb884112ec718a07bfe0ed814d |

New evidence root:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R2_L1_20261030_01`.
The final qualified receipts are under `qualified/`; earlier candidates and
their source snapshots are retained separately. BEFORE.json/backup, SOURCE_SHA256,
PRESERVATION, L1_DELIVERY.tar, ARCHIVE_INTEGRITY and final MANIFEST bind evidence.
All original/R1/R2/REC1 manifest members were independently rehashed at closure:
10 + 82 + 98 + 415 members. Original manifest hashes are unchanged, including
REC1 `1bff4a390a702376e396425eb4e28e51d2975077c14f1f7de59777d210bda158`.

The opt-in CLI has two explicit operations. `prepare` creates an exclusive
versioned contract without constructing/advancing a numerical runtime. `run`
requires `--runtime-r2-rec1`, contract file and SHA, output root, positive
`--advanced-segment-years`, and explicit `--resume` for an existing run.
No default CI/CLI dispatch or long calculation is installed or executed.

Contract V1 binds all R6 module hashes, the launcher and E0-reader hashes,
the three original E0 input digests/root, planned horizon, annual step, named
uplift, output service, query years and both persistence intervals. Source drift,
wrong file SHA, invalid support/horizon/input, unsafe output reuse/symlink,
different resume contract or an active launcher writer fail closed. External
contract SHA hashes file bytes; internal run identity hashes canonical contract
content. These digest domains are recorded separately.

Annual forcing remains C028/plate11=0.0001 m/year and C029/plate5=0, deriving
1.0/0 m at planned 10000Y and 0.1/0 m at 1000Y. Original 1000Y defaults and
native checkpoint schema/content remain unchanged. Each numerical call advances
one year. Actual records/deposits are counted, not assumed permanently 61/11.

## Persistence and services

The launcher calls the unchanged REC1 controller. All compact causal frames,
events, material identity/provenance, annual region and Unified/Deep records are
retained. Periodic fsync is distinct from B0 publication. Current REC1 atomically
publishes a durable journal chunk with a complete coupled native checkpoint;
`journal_commit_interval_years` must equal `checkpoint_interval_years`.
Independent journal-only B0 publication is explicitly rejected as unqualified.

Journal fsync can run every 1/5/10 years independently. It preserves staged
bytes but grants no resume authority and does not reduce numerical rework.
A numerical checkpoint is published at absolute periodic years and always at
the requested segment end. Stopping early therefore adds a paired checkpoint.
Resume verifies the committed lineage and discards no original/committed data;
loose tails remain diagnostic orphans. No committed pair means no eligible
resume: a first-prefix failure requires an explicit fresh run in a new directory,
not automatic T0 fallback. Corrupt committed history stops; no silent rollback.

An exclusive process lock complements B0's stale-parent CAS. No extra solver is
spawned. Native checkpoint digests preserve full regional, thermal, mechanics,
Deep, clock and balance equality. Local chains after resume remain linked through
REC1 parent identities and global ordinals.

`compact_query` emits only explicitly requested exact-year snapshot files from
committed history. Its private synchronous serializer replays authenticated deltas
in one buffer, without detaching or serializing unrequested snapshots. Public
query files are complete serialized values; no mutable buffer escapes. Missing
future query years are explicitly deferred until their segment is committed.
`legacy_full` additionally emits complete HISTORY and INDEX in the original
envelope/index format, including original NULL time semantics. Full legacy
encoding remains quadratic in growing snapshot size and is an optional measured
service. Neither service changes physical state or archive cadence.

## Bounded results

Final `qualified/REGRESSION.xml/log`: **242 passed in 26.52 s**, zero skips/failures:
all 228 REC1/R1/R2/B0 regressions plus 14 launcher tests. CLI subprocess tests
cover 3Y/10Y direct versus 1+2 / 5+5 save/exit/reopen/continue under plans 1000
and 10000. Same-plan full native checkpoint and complete legacy history/index
are exact. Under plan1000, both files are byte-exact prefixes of the original
oracle: 184/611 payloads, 24/80 NULL event times, 174/580 events. Query Y3 is
also covered when the numerical checkpoint schedule does not include Y3.
Negative controls include source/input/contract/horizon drift, interval mismatch,
truncation, unavailable context, reused paths/symlinks and writer lock; unchanged
REC1 tests cover stale parent, pinned reader, corruption and incoherent checkpoint.

`qualified/LAUNCHER_SIGKILL.json`: nine real child kills at REC1 commit hooks
before/after journal sealing, checkpoint persistence, visibility and cleanup.
Pre-visibility cases recover Y1; post-visibility cases recover Y3. Every case
continues in a separate launcher process to Y10 with full native checkpoint and
all 611 payloads exact. Periodic launcher fsync can already have persisted a tail
before a REC1 hook: that durable but unconfirmed suffix correctly remains ineligible.
These are supervised fault experiments, not automatic numerical retries.

Final anchor component probes advance only Y100→101, Y500→501 and Y750→751,
61 exact original payloads each. No fabricated mid-history B0 root is published.
Single-sample milliseconds:

| Year | Advance + compact | CP seal | CP encode | CP file fsync | Pair validation | CP bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 101 | 32.938 | 26.271 | 3.773 | 3.564 | 24.638 | 529942 |
| 501 | 34.957 | 75.837 | 12.350 | 7.563 | 76.433 | 1944172 |
| 751 | 36.204 | 108.545 | 17.598 | 9.481 | 115.657 | 2827818 |

Journal fsync+SHA at those anchors: 4.137/2.381/3.101 ms. Pair validation covers
one newly advanced year here, not a 250/500/1000-year chunk. B0 publication costs
are measured by the real short launcher, not inferred from an invented anchor
history. Filesystem load and instrumentation affect timing; no controlled speedup
or distributional confidence is claimed.

Under plan10000, 10 advanced years, checkpoint interval4 and fsync1:
advance+compact **0.303781 s**, three coupled commits **0.236686 s**,
requested snapshots plus full legacy/INDEX **0.151927 s**. Wall before final
receipt **0.756405 s**; supervised process launch-to-exit **1.020910 s**.
CPU user/system **0.584729/0.009010 s**; equivalent cores on pre-receipt wall
about **0.785**. Own kernel VmHWM **47256 KiB**. Resume from Y5 takes
**0.049785 s**. These service choices differ from REC1's single-commit short run
and the old full1000Y results; no equal-service full-run speedup claim follows.

Pre-receipt category accounting: journal 1620470 logical B /1626112 allocated B,
3 chunks; native checkpoints 608798/614400 B, 3 files; B0 31829/65536 B,
13 files; invocation/service files 1893401/1900544 B, 7 files. Root contract/lock
and final receipt are separate. Raw telemetry records annual/window100 wall,
CPU, cores, exclusive operator/compact/writer phases, CP/validation/B0/fsync,
deposits/scans, own/process-tree RSS and separately shared cgroup current/peak,
and logical/allocated bytes/files. The short windows are explicitly incomplete;
their p50/p95/max are not 100Y measurements. Total timing includes observation;
phase subtotals must not be added twice. Operator phases include bookkeeping.

Three 10-step probes with the same CP interval4 compare staged fsync choices:

| Fsync interval | Extra fsync calls | Extra fsync total s | Pre-receipt whole-service s |
| --- | ---: | ---: | ---: |
| 1 | 10 | 0.027209 | 0.654457 |
| 5 | 2 | 0.005785 | 0.627641 |
| 10 | 1 | 0.003162 | 0.613557 |

These compact-only single samples include three paired checkpoint commits,
which fsync independently. Final native states are exact across all choices.
They illustrate redundant fsync overhead, not a universal I/O forecast.

## Memory and remaining scaling

The offline worker verifies the existing **161896378-byte** compact archive:
61001 chained records, 8000 NULL timestamps, five exact snapshot witnesses,
zero numerical advances. One-buffer replay takes **3.143962 s** and own RSS
grows **47612→60924 KiB** as deposits grow to11000. It does not retain all
encoded journal records. This is a component probe, not a full REC1 restart.

Separate processes load/verify 1/3/5 real previous checkpoints. Five encoded
files total **10056361 B**, retained unique Python objects **20709146 B**;
own RSS **46080→69632 KiB**. REC1 eagerly retains these decoded native states
in `_load_chain`; verification/query can overlap that chain with replay buffers
and the live runtime. Worker `ru_maxrss` inherited a parent's high-water value;
use the independently recorded `/proc/self/status` VmHWM/RSS above.

Refinement of the earlier coarse memory description: cold prefix verification
streams the journal; its retained memory grows with replay frontier and the sum
of decoded checkpoints, rather than all journal bytes. During live advancement,
R2 still retains its encoded entries/frames. During a query after a live run,
that resident journal can overlap the checkpoint chain. Five O(D) numerical
scans persist. L1 neither prunes history nor changes REC1's eager chain loader.

Full selected-year query work is prefix verification/replay plus encoding chosen
states. Full legacy output still encodes all growing states. No redundant full
state work is moved into the compact writer. Annual byte telemetry counts only
new encoded entries/frames rather than rescanning the retained journal.

## Cadence decision support — no automatic ratification

Pure periodic schedules over10000Y, with no extra early/forced commits:

| CP gap | CP count | Max rework years | Uniform-failure mean years | Conditional CP disk MB | Conditional retained CP heap MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 250 | 40 | 249 | 124.5 | 731.69 | 1506.77 |
| 500 | 20 | 499 | 249.5 | 374.68 | 771.59 |
| 1000 | 10 | 999 | 499.5 | 196.18 | 403.99 |

Disk uses an affine fit to the five authentic checkpoint sizes at100..1000;
heap uses their measured 2.0593× Python/encoded ratio. These are conditional
unchanged-growth scenarios, not 10k observations or memory bounds. CPU costs
also grow with state and chunk length: the anchor seal/validation curve must
not be replaced by constant 10Y commit cost. More frequent commits reduce
recomputation and repeated per-chunk validation span, while adding full-state
sealing/encoding and more retained checkpoints. Mean assumes uniformly placed
failures, not measured failure rates. The first interval has no committed T0 pair.

The old hot-loop 10k scenarios (~10.5–23.3min, illustrative1.9–3.0GiB live
state/journal) exclude L1's exact services. CP250's retained heap alone can add
about1.5GB during chain verification/query, plus transient copies/allocator and
observation. No total resource upper bound is qualified. Actual site allocation,
quota and later-state behavior must be checked before launch. No unsupported
memory optimization or independent journal publication was introduced.

Recommendation for authorial review: **compact_query**, selected snapshots,
**paired CP/B0 commit every250Y**, **staged journal fsync every10Y**, provided
the extra checkpoint memory and ≤249-year recovery objective are acceptable.
CP500 reduces chain memory at the cost of ≤499-year rework; CP1000 has the
lowest checkpoint overhead and the largest ≤999-year rework. Annual fsync is
an optional diagnostic durability choice, with no improved qualified resume
point. Independent journal commits with sparse numerical checkpoints need a
separate deterministic-replay implementation/qualification gate.

Four exclusive proposed contracts are prepared under `qualified/`: CP250/500/1000
with fsync1, and the recommended CP250/fsync10 variant. They are
**PREPARED_NOT_EXECUTED / NOT_AUTHORIALLY_SELECTED**. Recommended file SHA256:
`163a4557c3956baf133c25ae039da37c91a362a1388eab55b829eff78f2ebcc5`.
No option is silently installed as the benchmark policy. Extra early milestones,
different queries or legacy_full require an explicitly reviewed contract.

## Operational next gate

`R2_10K_PREFLIGHT=BLOCKED_SERVICE_AND_CHECKPOINT_CADENCE_NOT_RATIFIED`

Launcher integration and bounded REC1 source/resume parity are resolved.
Authorial service/query/fsync/checkpoint/RPO selection remains pending. Recheck
source/contract, actual FAIR resources/site rules/quota and runtime versions
before a separately authorized launch. Current context is FAIR session58727,
cpu.max=max100000, memory.max=max, CPUs0..127 visible; these are not reserved
128 cores or unlimited physical memory. Cgroup memory/peak include unrelated
session work and are not this process's RSS. No scheduler-only rule or scheduler
allocation was invented; account quota remains UNKNOWN. No application RAM,
time, output or thread cap was imposed. Observed128 NumPy threads do not imply
128 utilized cores. Existing Python3.12.14/NumPy2.5.3/pytest9.1.1 were used.

Only after the policy decision and refreshed launch checks can the technical
preflight become READY for an explicit 10k authorization. L1 PASS itself does
not grant it. No full 10k execution command is issued here.

## Reproduction and evidence scope

Explicit CLI help: arcana-r6-linux `python scripts/r6_runtime_r2_launcher.py --help`.
Preparation requires all duration/cadence/service/input/output arguments; the
actual prepare invocations/file SHAs are in qualified/PROPOSED_OPTIONS.json.
The final regression set and environment are in REGRESSION.xml and
RUNTIME_ENVIRONMENT.json. launcher_probe.py records each subprocess argv,
exit, stderr/stdout and launch-to-exit wall; cost_memory_probe.py retains
component, memory and fsync receipts. Re-entry into evidence directories is
rejected. Copy scripts into a fresh evidence directory for a newly authorized
reproduction. No automatic retries occur.

Earlier passing candidates used a simpler payload envelope, then the full
legacy INDEX format; final qualification additionally replaces unrequested
snapshot copies in queries with the private serializer buffer. Their sources
and receipts remain preserved, and only `qualified/` supplies the final marker.
This is current-filesystem process-crash engineering qualification, not storage
failover/power-loss, B0 production, science, canonical history or RNG authority.
