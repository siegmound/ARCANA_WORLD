# Runtime R2 — structural fast path, bounded FAIR qualification

2026-10-30. `R2_BOUNDED=PASS_BOUNDED_EXACT_RECONSTRUCTION_AND_STRUCTURAL_ELIMINATION`.
Scope: opt-in private frontier, scratch compact codec, exact bounded generation
and reconstruction. **No new R2 1000Y or 10k numerical trajectory was executed.**
Those remain separate authorization gates. Scientific/production flags are false.

The improvement is conditional on requested services. R2 removes old-deposit
copying and full snapshot construction from annual advancement, and regional
checkpoint processing from years without a requested checkpoint. It does not
make deposit-dependent numerical reductions constant-time. A fresh isolated
one-year run with all compatibility outputs is slower than R1. A five-year
persistent session with the same full requested outputs is measurably faster.

## Source identity and preservation

Actual branch stays `r6/runtime-copy-r1-fair`, HEAD
`2c71370eb9a959c78121ce1c88ec8e9e37187787`. Intentional R1 modifications were
verified against the passed R1 evidence before editing. No reset, checkout,
pull, merge, commit or push occurred. The original R1 report and FAIR archives
remain unchanged.

Evidence root:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/RUNTIME_R2_STRUCTURAL_20261030_01`.

- `r1_backup/` contains all ten pre-R2 modified/untracked R1 files.
- `R1_BACKUP_MANIFEST.json` pins their exact SHA256 and original git status.
- `R1_TRACKED.patch` SHA256:
  `1c868b243da5375bb5c948d3bbc9c57290828a5cb367a35e08b117ab35467c67`.
- `R2_AGAINST_PRESERVED_R1.patch` SHA256:
  `965f463559a618e100af85950513f97832714608169ef682e9c5103163371c9a`.
- `qualification/SOURCE_SHA256.json` pins all measured R6 modules, R2 tests
  and runner; unchanged after qualification. Original E0 inputs and all original
  1000Y manifest members were rehashed unchanged at the final gate.
- Original manifest remains
  `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.

The R2 task and live R1 report supply operational authority; the two named
task-specific remote ledger additions are absent from this local checkout.
No historical evidence was substituted or rewritten. The user's no-commit rule
keeps this gate's code and ledger edits uncommitted.

## Design, fields and ownership

`DESIGN_BEFORE_PATCH.md` and `FIELD_INVENTORY.json` were captured before source
edits. The inventory includes all 18 regional frontier fields, 25 cell fields
and nine deposit fields. Snapshots retain exact cell order and all nondeposit
values; deposits retain material/event IDs, density, mass, source/destination,
and erosion/transport/deposition years. Nondeposit field addition/removal and
cell addition/removal/reordering are covered by the general codec.

There is one new implementation module, `int10k_runtime_compact.py`:

- `CompactRuntime(..., runtime_compact_history=True)` is a separate explicit
  R2 API. It imports and verifies a complete restart checkpoint once, detaches
  mutable state, and owns it privately. Legacy/R1 APIs retain their defaults.
- `_DepositLog` freezes each full appended row recursively using immutable
  mappings/tuples. The numerical operator can append and iterate; it cannot
  overwrite, remove or mutate old rows. General codec splices separately support
  append, replacement and removal. Unexpected runtime mutation fails rather
  than silently switching representations.
- The same existing `advance_region` numerical body is used. Only a private
  owner capability bypasses its entry copy and annual snapshot creation.
  The entire numerical body between cell selection and snapshot emission is
  text-identical to the preserved R1 source. No formula, constants, timestep,
  forcing, precision, material arithmetic or reduction algorithm changed.
- Nondeposit mappings are sorted in place at each annual boundary, reproducing
  the reference JSON roundtrip's iteration order without traversing old deposit
  rows. All original material sums and geologic-load scans remain intact.
- A runtime frame contains complete nondeposit values and ordered new deposit
  rows. It occupies the original snapshot's position in the event stream.
  Unified, Deep, annual and event payloads retain their full source values.
- The external journal contains authenticated immutable bytes, not solver
  references. Callbacks receive detached JSON values. Snapshot/checkpoint/query
  results are detached. Reentry is rejected; a failed step poisons the session.
  A poisoned session cannot continue or serve physical state/checkpoint queries;
  its raw bytes remain diagnostic evidence, not an atomically published history.

The scratch adapter does not integrate a second B0 store, publish canonical
transactions, implement adaptive retention, or claim durable crash recovery.
The existing B6N4A/B6N6 reconstruction and event/UNKNOWN rules remain authoritative.

### Hash boundary: no substitution of identities

`make_delta` / `apply_delta` use `ARCANA_R6_RUNTIME_R2_DELTA_V1`: complete
parent/target canonical snapshot SHA, year/identity, full nondeposit fields,
ordered per-cell splice and delta SHA. They reject invalid JSON, duplicate
identities, stale parent, invalid splice, changed digest and target mismatch.

The annual hot frame is explicitly **unsealed**
(`ARCANA_R6_RUNTIME_R2_UNSEALED_FRAME_V1`). Its full canonical snapshot SHA
fields are NULL with `DEFERRED_UNTIL_MATERIALIZATION`; its ordered record chain
is a different identity. It is never labeled a full canonical snapshot SHA.
Requested snapshot reconstruction computes the original canonical value/hash;
sealed codec generation records both exact canonical hashes.

Computing the old complete canonical SHA every year still needs O(D) input
bytes. R2 does not pretend the hash chain removes that cost. A service requiring
all full canonical hashes immediately must pay explicit materialization/sealing
costs and cannot use the compact-only timing claim.

Example API (not an authorization to start a long run):

```python
runtime = CompactRuntime(initial_states, identity, config=regional_config,
                         checkpoint=verified_anchor,
                         runtime_compact_history=True)
runtime.advance(5)
snapshot = runtime.snapshot()       # explicit reconstruction
checkpoint = runtime.checkpoint()   # explicit full seal + verify
history = runtime.legacy_history()  # explicit full compatibility iterator
```

## Tests and exact oracle evidence

`FINAL_TESTS.log`: **168 passed in 2.97 s**, zero failure/skip. This includes the
existing 141 focused R1/E2 tests and 27 R2 cases. Test-first collection initially
failed because the R2 module did not exist; the first implemented pure codec
passed all 17 initial cases before numerical qualification.

Named cases cover append/replace/remove, empty cells, field addition/removal,
cell/deposit reorder, nonfinite/object/cycle rejection, duplicate cell/material
identities, stale parent, changed hashes, omitted operations, detached reads,
callback mutation, immutable old deposits, failed-consumer poisoning and stream
loss/duplication/reorder/corruption/truncation. All existing excluded-history
NaN/Inf/cyclic fail-closed tests continue to pass on R1.

Actual E0/oracle checks:

- 3Y direct versus 1+2 and 10Y direct versus 5+5: exact original payload SHA,
  material/water/solid/Deep balances and original-format regional/unified
  checkpoints. Separate full cross-kind ordering proof: 184 and 611 items.
- Y101/Y501/Y751: seven measured repetitions after one discarded warm-up,
  with exact ordered 61-item source payload SHA on every case. R2 and R1 compact
  files, legacy files, queried snapshots and exported checkpoints match exactly.
- Bounded persistent Y751..755: same proof across 305 ordered items; seven
  measured repetitions. This is five model-years from a saved Y750 anchor,
  not a new trajectory from zero through year 1000.
- Offline conversion uses the newly implemented R2 sealed codec over all
  61,001 original records: 1001 snapshots, nine cells, 11,000 final deposits,
  8000 NULL event times. Every reconstructed source payload SHA is exact.
- Independent **on-disk readback** checks the new compact chain, reconstructs
  every snapshot, and compares all 61,001 logical payloads in source order.
  `DISK_READBACK.json`: exact PASS, 62.957533 s. This proves the new codec/file;
  new R2 numerical generation is demonstrated only in the bounded cases above.

The offline adapter's file format is compact and is intentionally not byte-equal
to original HISTORY/INDEX. The proof is exact reconstructed logical payloads.
No new 1000Y or 10k numerical trajectory, production archive or B0 durability
qualification is claimed.

## Quantitative comparison and eliminated work

FAIR `arcana-r6-linux`, Python 3.12.14, same E0 inputs and planned duration 1000.
One fresh worker per mode/case; seven repetitions and a discarded warm-up.
Baseline is the unchanged R1 path with a sink producing the **same** compact
service. Both modes additionally execute the same requested final query, full
legacy JSONL and full checkpoint file. Output byte lengths and hashes match.
Writer flush is included, fsync/B0 transactions are not. Input parsing happens
before measurement for both; all R2 initialization/import is separately counted.
No resource caps or thread environment changes were introduced.

Medians in milliseconds:

| Case | Hot advance + compact ingest, R1 / R2 | Import + compact output, R1 / R2 | Full requested service, R1 / R2 |
| --- | ---: | ---: | ---: |
| Y101, one year | 59.656 / 26.487 (2.25×) | 62.332 / 58.067 | 77.765 / 109.718 |
| Y501, one year | 137.594 / 29.084 (4.73×) | 150.238 / 140.784 | 206.722 / 310.459 |
| Y751, one year | 187.453 / 31.103 (6.03×) | 206.491 / 198.057 | 290.261 / 448.880 |
| Y751..755, five years | 941.914 / 152.853 (6.16×) | 960.008 / 315.769 (3.04×) | 1190.159 / 844.123 (1.41×) |

**Full service includes setup, advance, compact write, detached final query,
complete legacy materialization/write and final checkpoint export/write.**
For isolated one-year full compatibility, R2 is 41–55% slower. It should not be
selected on a claimed full-service speedup for that workload. Its initialization
cost is O(D), and requested full queries/checkpoints remain O(D).

Five-year full service improves **29.07%**, including all requested output and
reconstruction work. R1 observed range 1183.06–1210.13 ms, R2 834.00–852.50 ms:
the sample ranges do not overlap. Compact-only five-year total improves 67.11%.
This is a bounded amortization result, not a forecast for a full R2 1000Y/10k.

At Y751, the R2 cold import is 164.328 ms, final snapshot query 41.397 ms,
full legacy materialize/write 80.613 ms and checkpoint export/write 126.979 ms.
For the five-year case: 162.203 / 42.515 / 352.898 / 132.967 ms respectively.
These costs are included in the full service column; none are hidden in a writer.

Structural instrumentation per newly advanced year:

| Year | Deposit rows read by unchanged numerical scans | New rows frozen/exported | Full snapshots built in advance | Compact frame bytes including envelope |
| --- | ---: | ---: | ---: | ---: |
| 101 | 5555 | 11 / 11 | 0 | 13,772 |
| 501 | 27,555 | 11 / 11 | 0 | 13,783 |
| 751 | 41,305 | 11 / 11 | 0 | 13,778 |

There are five ordered full deposit passes (two stock reductions, plus material
inventory, surface-stock and thickness inside geologic load). No cached float
accumulator replaces them. The new log exports only 11 complete new rows per
year, not the historical prefix. Its append/freeze/export counters and readonly
rows corroborate the removed old-row copying. Regional full checkpoint calls
are absent from advance, occurring only at requested boundaries. Unified
checkpoint processing remains bounded by the two numerical columns.

`PHASE_WALL.json` contains a separate diagnostic with exclusive nested timers;
the `.pstats` files provide exclusive CPU, never inclusive totals added together.
At Y751 the named mechanics/thermal/hydrology/Deep kernels are 0.647 ms R1 and
0.661 ms R2; these are a **kernel subset**, excluding other rheology/orchestration.
Geologic-load scans are 2.097 / 4.061 ms: immutable mapping access and read
instrumentation add overhead. R1 copy-other is 47.177 ms, regional encoding
72.473 ms, outer checkpoint processing 38.299 ms. R2 regional encoding is
4.660 ms; delta-field work 0.068 ms, and additional compact ingest-other 0.147 ms.
All these phase times are diagnostic, separate from the uninstrumented medians.

CPU user/system, median complete service: Y751 one-year R1 0.285006/0.005001 s,
R2 0.437010/0.009010 s; five-year R1 1.181715/0.007997 s,
R2 0.828214/0.015014 s. Work remains effectively single-core. Per-sample VmHWM
includes import and prior repetitions/queries (read before separate profiling).
Recorded Y751 peaks are 81,492 KiB R1 and 99,680 KiB R2; five-year peaks
98,132 / 106,848 KiB. **No RSS reduction is claimed.**

### Storage and full reconstruction cost

Y751 one-year compact output is 161,710 B versus 2,794,299 B full legacy JSONL;
both R1/R2 adapters produce identical files for each service. The five-year
outputs are 808,528 B compact and 14,006,595 B legacy. A complete compact yearly
bundle stays approximately 162 kB across the three anchors.

Offline original-HISTORY conversion produces one file of **162,037,378 logical B,
162,041,856 allocated B**, versus original HISTORY 1,916,080,917 B: 91.54% smaller.
This excludes additional anchors/checkpoints and is an offline representation
comparison, not measured new 1000Y solver output. The qualification directory
also retains repeated full compatibility files, so its total scratch usage is
larger than the single compact representation.

Offline conversion wall: **179.686505 s**. Explicit subphases: full canonical
sealed-delta generation 98.558677 s; reconstruction/validation 55.601444 s;
compact encode/hash/write 3.221302 s. Source reading/parsing/hashing and other
bookkeeping account for the remainder. Independent disk readback is another
62.957533 s. Full all-year hashing/reconstruction is still O(sum D), and these
numbers must not be described as incremental simulation time.

## Remaining history-dependent work and next gates

1. Five ordered physical ledger/load passes remain O(D), with O(D) temporary
   provenance lists before deduplication. Contrary to the initial design
   hypothesis, emitted provenance is `sorted(set(...))`; stored annual records
   are about 28 kB at all anchors, not growing deposit-length arrays.
2. Cold import/freezing and requested full checkpoint construction/seal/verify
   are O(D). Full snapshot query is O(D + intervening frames), with owned append
   reconstruction and a detached result. Historical frame traversal still
   grows with the number of frames; this is not an indexed B0 query store.
3. All-year legacy compatibility export and complete canonical snapshot hashes
   remain O(sum D). Requesting them each year restores that output complexity.
4. Living material/deposit state and compact journal grow with actual data.
   R2 does not claim constant memory, global O(Y) physics or 64/128-core scaling.
5. No production durability/atomic publication/recovery is qualified. Negative
   stream/callback tests prove fail-closed scratch behavior only. A failed
   standalone phase-helper launch from the parent directory had an import-path
   error; rerunning from the documented repository directory succeeded. There
   was no failed scientific parity gate, solver retry or patch stacking.

`QUALIFICATION_SUMMARY.json` binds final tests, source/diff identities, on-disk
proof, benchmark caveats and the bounded engineering marker. This is one
isolated R2 candidate; R1 remains available unchanged on its reference path.

**Next required numerical gate:** review and explicitly authorize a new R2
1000Y compact trajectory with fixed planned duration 1000, annual steps,
unchanged E0 inputs and exact source hashes. Measure compact loop/ingest,
sampled queries, explicit checkpoint cadence and separate full compatibility
reconstruction, and verify all 61,001 original logical payloads plus original
milestone checkpoints. No application time/RAM/output caps should be invented;
actual FAIR allocation/site rules apply. Do not run it under this bounded gate.

Only after exact full R2 1000Y qualification, review and separately authorize
10k, including the run-level uplift redistribution with planned duration,
provider validity, allocation and resource telemetry. No 10k extrapolation is
made from the bounded timings. R1's recorded 214.125572 s remains historical
reference, not an R2 full-run measurement.

`R2_1000Y_NUMERICAL_RUN=NOT_AUTHORIZED_NOT_RUN`
`R2_10000Y_NUMERICAL_RUN=NOT_AUTHORIZED_NOT_RUN`
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`
`GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`
`ARCANA_SI1_MECHANICS_QUALIFIED=false`
