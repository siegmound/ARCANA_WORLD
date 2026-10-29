# R6-INT10K E2-B2 — History-independent numerical continuation

**Local verdict:** `INT10K_E2_B2_HISTORY_INDEPENDENT_CONTINUATION_LOCAL_PASS__FAIR_PENDING`

**Base source:** `4910c2c4e4b1a00f2999b95937f07cea233a006c` on
`r6/multiphysics-integration-20261026`. The local numerical captures used this
base plus uncommitted E2-B2 files; they are not a qualification of a committed
or Linux-tested source revision. See each generated report for the exact source
file SHA256 values.

## Dependency audit

The audit traced the calls through `run_regional_segment`, `advance_region`,
`run_unified_microdomain`, and `continue_unified_microdomain`.

| Data | Prior use | E2-B2 treatment |
|---|---|---|
| Unified `records` / `steps` | Resume copied all previous rows, then final material-flow, mechanics and Deep summaries scanned the list. Per-step mechanical residuals are exposed as a diagnostic result. | HI checkpoint has no `records`; bounded accumulators are carried in its state and updated in original step order. Per-step rows are emitted to the consumer and remain available for the current invocation's result. |
| Regional `records` | Annual water/solid balances, event history, and query/provenance APIs use the recorded rows. Advancement itself uses current cells, routing, cumulative ledgers and current time. | HI resume starts with empty result-history lists. Every newly produced year record is emitted to the consumer. No prior record is reconstructed from the frontier. |
| Regional `snapshots` | Historical material lookup and exact-time queries use snapshots. | Year-zero initial snapshot is emitted on direct start; subsequent snapshots are emitted per year. Resume emits only new snapshots; the split-boundary snapshot remains in the separate prefix history. |
| Regional/unified events | Events are retained with annual/step records; routing and initial-condition event lists are also historical query data. | Events are emitted separately with their original event objects and remain embedded in their parent records. The frontier contains no event arrays. |
| Cumulative summaries | Existing totals and tolerances are needed for subsequent balances. | Existing dynamic totals remain in the checkpoint. New accumulators preserve material flow totals by material ID, mechanical work/dissipation totals, and Deep transport/minimum-stock summaries. No whole-history list is scanned in HI restore. |
| Dynamic state | Current columns, Maxwell memory, surface cells/deposits, water, materials, Deep inventory, routing and configuration are required to continue. | These remain in the nested engine checkpoint. Stratified deposits are physical state and can grow with the evolving model; their storage is not a duplicated history prefix. |

Legacy query helpers still operate on a supplied result/history object. The new
`HistoryReader` is a separate exact-row reader; it reports missing times and
does not interpolate. The numerical resume does not call historical queries.
E2-B2 does **not** implement an on-disk archive, transaction/commit chain,
atomic append, crash recovery, or bounded-memory streaming. The collector used
for parity is a lossless in-memory test consumer, and each engine call still
returns the records generated during that call for legacy API compatibility.

## Frontier/checkpoint behavior

`ARCANA_R6_INT10K_HISTORY_INDEPENDENT_CHECKPOINT_V1` wraps the regional and
unified engine checkpoints. It binds current year/high-water mark, next record
ordinals, source identity and SHA256, effective configuration and SHA256,
classification, and a checkpoint digest. The chain-head field explicitly says
`NOT_IMPLEMENTED_NO_APPEND_ONLY_CHAIN`; it is not a transaction or commit ID.

The regional frontier checkpoint and unified V2 checkpoint reject history
arrays. Restore verifies the outer and nested digests, source/config identities,
time agreement, schema, accumulator keys and finite values. The runner requires
history-independent mode and an external record consumer; it will not silently
load a legacy V1 full-history checkpoint in this mode. Legacy V1 behavior stays
available unchanged for the prior oracle path.

The HI mode replaces historical scans with accumulators. The accumulator is
validated against a reduction of the E1 step records in the qualification
harness. Numerical operators, forcing, timestep, coefficients, E0 inputs,
E1 tolerances, and output history contents are unchanged.

## Local validation

Environment: Windows Python 3.12.10, NumPy 2.5.1. E0 triplet SHA256 was checked
before and after each run using the pinned loader. The E2-A1 Windows oracle
bundles were reopened, their manifest members rehashed, and the oracle
integrity validator passed. Local oracle bundle manifest SHA256s: 3Y
`9485fa81ef6d88e63edb7d96a1a25661199bc3e712650316bd15864b8aed08c1`; 10Y
`a7f2bce9b4e725a9d0227ee76c5c6e88823a62a6d073afd94f713c0620099a0f`. FAIR
E2-A1 artifacts remain operator-reported and were not transferred or
independently rehashed here.

| Reference | Captured path | Coverage | Frontier serialized bytes (split boundary / final) | Full history bytes | Sealed output bytes | Wall / CPU | Python heap peak | RSS samples (before / after) |
|---|---|---|---:|---:|---:|---:|---:|
| 3Y, 1+2 | `INT10K_E2_B2_WINDOWS_20261029_06/3y_1plus2` | 3 year records, 4 snapshots, 174 event records, 3 unified steps | 181,125 / 188,011 | 452,080 | 1,467,179 B | 3.1123 s / 3.0156 s | 8,980,160 B | 47,591,424 / 69,582,848 B |
| 10Y, 5+5 | `INT10K_E2_B2_WINDOWS_20261029_06/10y_5plus5` | 10 year records, 11 snapshots, 580 event records, 10 unified steps | 194,913 / 212,214 | 1,612,204 | 3,849,627 B | 8.5641 s / 8.1250 s | 25,625,235 B | 64,294,912 / 129,024,000 B |

RSS is a Windows process working-set observation at phase boundaries, not a
continuous peak or process-tree measurement. The frontier grows 6,886 bytes
from split to final at 3Y and 17,301 bytes at 10Y; it also differs between
ages (188,011 bytes at 3Y and 212,214 bytes at 10Y). This is observed growth,
not proof that all dynamic state is constant-size. In particular, material
deposit strata and bounded-by-material-ID cumulative maps can change with the
run. No size limit or resource cap was imposed.

The runs compared all direct and split-prefix/resumed year records, snapshots,
event payloads, unified steps, final dynamic state, component balances, and
split-boundary/final checkpoint state with the preserved Windows E2-A1 oracle.
The split resume received only the typed checkpoint and immutable source/config
binding: the prefix history collector was not passed. Direct and joined split
history matched exactly; numeric fields used the existing E1 tolerances
(`abs=1e-8`, `rel=2e-14`), while IDs, ordering, time, schemas and event metadata
were exact. The checkpoint accumulators matched an in-order reduction of the
full reference steps. Exact-time material/Deep queries passed; absent times
returned `TIME_NOT_ARCHIVED`.

Artifacts, all verified against their newly written manifests:

- 3Y manifest SHA256 `a24f46d051f2dea81f49183ed320f920c7d815ac68f9613542b5e4248df26fb4`.
- 10Y manifest SHA256 `e58e774623b3b0e53d488f36eb8667b7dfc074dd45c03f7222778308e7c59870`.
- Both bundles retain separate direct and split-joined history JSON plus direct,
  boundary and final frontier checkpoints. The direct/split history files have
  equal bytes and SHA256 within each bundle.
- The earlier `_05` captures are preserved as exploratory evidence; `_06` is
  the final recapture after event-stream reconciliation. All four manifest
  members in each `_06` bundle were independently rehashed and length-checked
  locally. The reported directory byte totals are the sums of the files present
  in each evidence directory; no output bundle was staged or committed.

Focused regressions: **67 passed, 0 failed, 0 skipped** across E2-B2, E2-B,
E2-A1, E1 short-reference, regional geology, and unified multiphysics tests.
The earlier E2-A1 result of 60/60 on Windows and the operator-reported FAIR
60/60 remain historical and unchanged. No FAIR execution of E2-B2 has occurred.

## Acceptance and remaining gates

| Criterion | Result |
|---|---|
| Resume without the prior history prefix | PASS locally for 3Y 1+2 and 10Y 5+5 |
| All output records preserved by an external consumer | PASS locally; in-memory collector, no durable archive |
| Parity with full E2-A1 direct and split histories/checkpoints | PASS locally for the preserved Windows oracle |
| No hidden dependency on prior history lists during continuation | PASS in HI checkpoint/restore path; current-call result rows are still returned explicitly |
| Checkpoint corruption, incompatible source/config/schema, missing or malformed accumulators, and ordinal gaps | PASS in focused tests |
| History-independent serialized size at arbitrary duration | NOT CLAIMED; dynamic physical state can grow, and only 3Y/10Y were measured |
| Append-only durable history, transactions, recovery, and on-disk queries | NOT IMPLEMENTED |
| Exact-commit Linux/FAIR qualification | PENDING |
| 100Y / 1,000Y / 10,000Y scaling runs | NOT RUN and not authorized by this task |

Next gate: commit this scoped implementation, then run the same E2-B2 tests and
3Y/10Y local-oracle parity harness on FAIR at the exact commit in a new external
evidence directory. Preserve the existing FAIR checkout, E0 files, E2-A1/E1
evidence and all failed exploratory outputs. E2-C/E2-D history persistence,
E2-E transaction/recovery and E2-F joined-domain commit semantics remain
separate implementation gates.

All runs are `NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY`. `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS`
remains active; actual FAIR allocation and site rules bind, and unknown quotas
remain UNKNOWN. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`,
`GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, and
`INT10K_LONG_RUN_AUTHORIZED=false`.
