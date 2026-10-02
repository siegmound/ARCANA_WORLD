# ARCANA WORLD — C0-F3 Semantic Duplicate Adjudication

**Mode:** read-only adjudication; no payload changes, cleanup, regeneration, commit, or push.
**Decision:** `PASS_C0_F3_SEMANTIC_DUPLICATE_ADJUDICATION_READY_FOR_F4` — with an empty deletion set.

## A. Baseline

| Measure | Current evidence |
|---|---:|
| Branch | `r6/pre-b0-data-consolidation` |
| HEAD | `d05769b259d55b00eaa01617da891473b1122d77` |
| HEAD summary | `chore: remove verified duplicate simulation artifacts` |
| Worktree before this report | clean |
| Tracked files present | 48,282 |
| Logical tracked bytes present | 2,758,633,130 |
| R6-focused regression | C0-F2 recorded 252 passed |

The duplicate census was recomputed from present tracked files under
`outputs/`, `local_runs/`, `SIMULATION_RESULTS/`, `references/`,
`reference_results/`, `benchmarks/`, `repairs/`, and `external/`, using file
size prefiltering followed by SHA256. It found **3,682 groups**, **32,473
participating files**, **1,524,228,578 logical bytes**, and **907,229,236
theoretical one-copy savings**. These are different measures: the savings
retain one physical copy per hash group; they do not authorize removal.

The census scope contains 46,411 files / 2,232,718,792 bytes. Of these,
13,938 files / 708,490,214 bytes are singletons in this scope. “Singleton” is
only a hash observation; authority is not implied. All other files, including
every duplicate participant, remain on hold unless individually adjudicated.

## B. Duplicate taxonomy

Each hash group is assigned one primary **triage** class using explicit path
context (failure/attempt labels, source snapshot components, run tokens, time or
stage tokens, and artifact names). The class metrics below are exact for that
classification. Path cues do not prove semantic equivalence, payload
reproducibility, or delete eligibility. In particular, `A` and `E` are zero
because no remaining group was proven to have the same governed semantic
identity or a complete deterministic producer/input chain.

| Primary class | Groups | Files | Logical bytes | Potential one-copy savings | Evidence / limitation |
|---|---:|---:|---:|---:|---|
| A. `SAME_PAYLOAD_SAME_SEMANTIC_IDENTITY` | 0 | 0 | 0 | 0 | No group had independent authority/manifest evidence proving same record identity. |
| B. `SAME_PAYLOAD_DISTINCT_RUN_IDENTITY` | 20 | 159 | 1,181,052 | 1,071,943 | Explicit simulation, replicate, job, run, or attempt identifiers differ. |
| C. `SAME_PAYLOAD_DISTINCT_TEMPORAL_STATE` | 50 | 143 | 37,226,751 | 18,962,469 | Stage/time tokens differ; the state lineage is not thereby interchangeable. |
| D. `SAME_PAYLOAD_DISTINCT_AUTHORITY_RECORD` | 37 | 102 | 27,929,928 | 13,970,950 | Authority/evidence/registry/checkpoint/manifest naming indicates separate records; per-record IDs still need review. |
| E. `GENERATED_REPRODUCIBLE` | 0 | 0 | 0 | 0 | No remaining duplicate group passed producer + complete-input + deterministic-output proof. |
| F. `EXTERNAL_ENGINE_UNIQUE_CONTEXT` | 1,094 | 5,562 | 357,448,978 | 252,383,004 | Engine/work-tree paths or engine-specific run layouts; repeated bytes retain scenario/run context. |
| G. `REJECTED_OR_DIAGNOSTIC_RUN` | 2,366 | 26,229 | 1,094,219,505 | 617,641,925 | Paths contain blocked/rejected/failed/diagnostic/attempt context. This is evidence to preserve, not a deletion rule. |
| H. `SOURCE_TEST_SNAPSHOT` | 25 | 50 | 554,294 | 277,147 | Exact `PREPATCH`, `PREPATCH_SOURCE`, `tests`, or `replacement` path components. |
| I. `UNKNOWN` | 90 | 228 | 5,668,070 | 2,921,798 | No reliable path/record cue sufficient for a stronger triage label. |
| **Total** | **3,682** | **32,473** | **1,524,228,578** | **907,229,236** | |

Classes B–D and F–H are not clearance decisions. Their numeric totals group
the remaining exact SHA matches; the required scientific/record-level review
has not been completed for every member. No `SAME_PAYLOAD` classification
means “safe to deduplicate.”

## C. Run identity analysis

**Payload identity** is exact byte equality. **Record identity** additionally
includes the run/stage/replicate, seed, parent, time, authority status, and
producer context. Existing stage manifests, run IDs and output paths often
carry the latter even when payload bytes match.

- A concrete collision in the rejected R5.2 RangeShiftR tree is a 10,353,246
  byte `Land1_Pop.txt` payload repeated under `Batch520011_Sim111`,
  `Batch520011_Sim112`, `Batch520023_Sim231`, and `Batch520023_Sim232`.
  Matching bytes do not erase those distinct simulation IDs, batches, or
  replicate contexts. The enclosing attempt is explicitly rejected for
  `InitType=0` free initialization despite a source-distribution file being
  supplied. Keep the files and their rejection/run evidence.
- Repeated R3 states, R4 repair/validation records, and R5 attempts can carry
  stage/time/parent identifiers in names and manifests. Equal serialized arrays
  or logs do not establish the same temporal state or accepted authority.
- `SIMULATION_RESULTS/MANIFEST.json/.csv` still retain all 863 source and
  historical consolidation records after C0-F2. The 863 original payload paths
  remain physical. Its `ConsolidatedPath` now describes copy-time history, not
  a currently present file. No new pointer system was introduced.
- Two governed metadata records pointing to one content-addressed payload is
  architecturally possible if record IDs, run provenance, parent relations and
  authority remain independent. Current manifests demonstrate some necessary
  source/hash metadata, but current consumers still expect paths and there is
  no repository-wide payload resolver. It is not implemented here.

## D. `outputs/`

Counts below cover present tracked files. Duplicate columns count all files in
remaining SHA groups under that family, not potential savings. R4 and R5
subtrees include distinct work, validation, run and attempt evidence; an
aggregate row does not make its members semantically uniform.

| Stage family | Files | Bytes | Duplicate participants / bytes | Authority and replay role | Builder/inputs/external dependencies; current R6 use | Recommended action |
|---|---:|---:|---:|---|---|---|
| R1 | 15 | 13,782,022 | 3 / 13,745,245 | Rebaseline state and metadata; some values are hard-anchor candidates. R6 bootstrap recovery cites the R1 common state as a candidate biological state, not the original physical bootstrap. | Stage records and some producer lineage exist; exact end-to-end regeneration is not established. No general R6 runtime path was found for the subtree. | `KEEP_PHYSICAL` for anchor candidates; audit each artifact. |
| R2 / R2.1 | 27 | 28,005,843 | 0 / 0 | Resolution/convergence and topology experiments. | Historical state files and stage metadata remain; no present runtime consumer found. | `KEEP_PHYSICAL`; distinct resolution products are not duplicate candidates. |
| R3 | 562 | 183,890,512 | 114 / 7,868,451 | World-history continuation, replay, event, checkpoint, and derived ecology/biology evidence; several checkpoints are anchors. | Python stage code and manifests exist for portions; upstream/external inputs vary. Current R6 docs cite bounded ancestry/metadata, not a blanket runtime dependency on this tree. | `KEEP_PHYSICAL`; preserve hard anchors and replay lineage. |
| R4 | 28,611 | 501,490,322 | 23,210 / 331,995,526 | Cross-engine validation, target binding, failures, repair snapshots and job evidence. | Stage-specific builders exist unevenly; engine versions, executable availability and full inputs are not closed. No broad R6 runtime consumer found. | `REVIEW_UNKNOWN`; no bulk dedup. |
| R5 | 15,138 | 1,282,358,271 | 7,993 / 1,119,414,185 | Later external-engine, ecological, population and scenario work, including accepted candidates and rejected attempts. | Inputs and external runtime availability are mixed; no R6 binding in the provider registry for NEMO, Geonomics, CDMetaPOP, SLiM, or RangeShiftR. | Preserve run/seed identity; adjudicate by stage and job. |
| Other top-level output records | 21 | 18,057 | 0 / 0 | Parent audits, extraction and smoke records. | No single producer chain inferred from names alone. | `REVIEW_UNKNOWN`; no deletion. |

High-volume R4/R5 examples (these rows are subsets of the R4/R5 totals above):

| Subtree | Files / bytes | Duplicate participants / bytes | Finding |
|---|---:|---:|---|
| `R4_22` | 4,259 / 85,967,362 | 4,218 / 83,980,113 | Extremely high duplicate participation; retain stage/job identity until its manifest and producer semantics are mapped. |
| `R4_3` | 7,234 / 59,339,415 | 5,160 / 44,923,051 | Job/runtime evidence; same payload can belong to distinct jobs. |
| `R4_55` | 9,265 / 101,199,191 | 7,258 / 86,664,596 | Large job outputs; no global reproducibility proof. |
| `R4_7` | 2,106 / 41,879,346 | 2,080 / 41,662,908 | Keep input/output pairing and qualification context. |
| `R4_9` | 3,336 / 64,417,707 | 3,088 / 31,465,690 | Includes additional dynamic runtime work; run identity remains relevant. |
| `R5_2` | 3,266 / 149,282,742 | 3,131 / 145,807,300 | RangeShiftR runs; exact executable/input replay not closed. |
| `R5_2_BLOCKED_PRE_R1_FREE_INIT` | 3,257 / 945,429,341 | 3,129 / 942,021,096 | Explicitly rejected attempt. Preserve the failed initialization evidence and raw outputs. |
| `R5_3` | 6,417 / 170,020,140 | 387 / 25,778,827 | CDMetaPOP work/results; stage manifest exists, but full regeneration was not proven. |

“Builder exists” is not equivalent to “complete deterministic replay proven.”
Input availability, engine version, seed, execution settings and authority
status must be closed per stage. The rows above are not `F4` deletion families.

## E. `local_runs/`

| Measure | Current result |
|---|---:|
| Files / bytes | 1,814 / 113,105,603 |
| Duplicate participants / their logical bytes | 1,101 / 22,650,966 |

The tree mixes at least three roles: (1) canonical/continuation checkpoint and
replay state families (`R3_10`–`R3_20` paths include multi-megabyte states),
(2) engine suite and qualification work (`R3_6D`, `R3_7A`, `R3_7C`), and
(3) smoke/debug attempts and their logs. Some files are results that matter;
other files are working trees or intermediate inputs whose pairing is needed to
interpret a result. A raw working-directory label does not distinguish them.

The F1 audit notes checkpoint candidates and links to stage evidence, but its
own limitation stands: no complete semantic census of all 1,814 files or
end-to-end producer/input/executable proof exists. Current R6 consumer checks
found no general `local_runs/` runtime binding; explicit historical R1
provenance citations are not live runtime consumers. Keep the tree physically
until stage-level result-versus-working-directory adjudication exists.

## F. Historical engine families

Counts cover name-matched files under result/evidence trees after C0-F2; they
are discovery counts, not guaranteed complete producer attribution. Duplicate
bytes count the logical bytes of participating files, not one-copy savings.

| Engine | Files / bytes | Duplicate participants / bytes | R6 binding and evidence role | Inputs / executable / reproducibility | Minimum to retain; action |
|---|---:|---:|---|---|---|
| NEMO | 2,179 / 9,595,204 | 1,154 / 3,454,317 | Not bound in R6; R3/R5 benchmark/reference evidence. | Wrappers and some inputs remain; exact 2.4.2 executable/environment and full run replay are unverified. | Keep templates, input/QTL evidence, suite logs and per-run outputs; `KEEP_REFERENCE`. |
| Geonomics | 366 / 21,820,256 | 34 / 511,186 | No R6 binding; R4 native schema, parameter, seed and layer-binding qualification/repair evidence. | Contracts and snapshots exist; no complete installed engine/version replay closure. | Keep frozen inputs/seeds, source snapshots, manifests and validation results; `KEEP_UNIQUE_EVIDENCE`. |
| CDMetaPOP | 23,756 / 509,376,005 | 17,366 / 328,685,795 | Not bound in R6; R4/R5 population and demographic bridge/evidence. | Large work trees and inputs exist, but exact external runtime/configuration and complete replay are not proven. | Preserve replicate IDs, inputs, manifests, `indSample`/outputs and validation; `REVIEW_UNKNOWN`. |
| SLiM | 208 / 7,882,660 | 97 / 80,523 | Not bound in R6; R5.6 genetics/population evidence. | Seed/scenario-specific results are present; executable/version reproducibility unverified. | Preserve `.trees`, seeds, scenarios and validation together; `KEEP_REFERENCE`. |
| RangeShiftR | 6,883 / 1,097,280,609 | 6,596 / 1,090,880,619 | Not bound in R6; R5.2/R5.3 distribution scenarios and a specifically rejected R5.2 attempt. | Runtime/executable and input closure incomplete; blocked attempt is not an accepted result. | Keep run/replicate IDs, initialization inputs, manifests and raw outputs; `KEEP_UNIQUE_EVIDENCE` / `REVIEW_UNKNOWN`. |
| Madingley | 10,394 / 28,357,316 | 6,219 / 2,712,623 | No R6 binding; historical ecosystem-model/reconciliation work. | Work snapshots and repeated timestamped `input/C.csv` are present; exact runtime/scenario replay is not proven. | Keep timestamp/config/result association; `REVIEW_UNKNOWN`. |
| BIOME4 | 0 name-matched result files | 0 / 0 | Provider registry freezes an interface but records input gaps and production unauthorized. | No name-matched results; inputs and executable not closed. | Keep interface/design/provenance, do not infer disposable status from absent results. |
| pyGPlates | 0 name-matched result-tree files | 0 / 0 | Diagnostic feasibility candidate only; not a canonical R6 dynamic solver. | Feasibility code/report artifacts are elsewhere; no result family found by engine-name scan. | Keep current R6 contracts/tests/reports; no engine output cleanup candidate. |
| ShellSet | 61 / 44,449,564 vendored files | 7 / 7,344 | S1B FAIR evidence qualifies the bounded ARCANA package-load boundary only; full mechanics is not qualified/authorized. | Vendored source and reference inputs remain; the qualified executable is represented by external qualification identity/evidence, not a generally reproducible binary in this tree. | Keep source/license/patch/input files, R6 package and qualification logs; `KEEP_AUTHORITY` / `KEEP_REUSABLE`. |

“Not bound” is a statement about current R6 wiring, not a deletion argument.
No external-engine family is proposed for removal.

## G. Rejected, PREPATCH, failed, and diagnostic runs

| Family | Evidenced value | Classification | Keep/delete decision |
|---|---|---|---|
| R5.2 `BLOCKED_PRE_R1_FREE_INIT` | Documents why a source-distribution input was not used (`InitType=0` selected free initialization); includes raw engine outputs and run identities. | Scientific execution/rejection evidence plus debugging history; not an accepted scientific candidate. | Keep physical and label rejected. Inputs/runtime closure remains incomplete. |
| R4 `PREPATCH` / `PREPATCH_SOURCE` | Captures exact source/test state before a repair or qualification transition. Several same-named tests differ byte-for-byte from current root tests. | Regression evidence and debugging/repair provenance. | Keep snapshots; do not collapse by basename/hash without commit/manifest mapping. |
| `repairs/**/replacement/tests` | Captures replacement test/source payloads; paths map to individual repair events. | Regression and repair evidence. | Keep until a governed archive map preserves the event and source path. |
| R5.3 `attempt_*` and R4 diagnostic/qualification records | Preserve attempts and diagnostic outputs under attempt/job/stage labels. | Evidence of bounded runs; some may be debugging-only, but no compact ledger currently proves complete recovery. | Keep; no `F4C` selection. |

Git history can retrieve tracked blobs at old commits, but this audit found no
authoritative compact ledger proving that every debugging-only output can be
reconstructed from history without losing path/run semantics. Therefore Git
history alone is not adopted as a deletion replacement in F3.

## H. Payload / metadata separation

The repository already has partial payload/record separation: manifests retain
run/stage/source paths, size, hash, copy verification and authority/semantic
statuses. F2 also established that the 863 catalog copies could be removed
while retaining their `OriginalRelativePath` payloads and copy-time records.
The remaining 3,682 groups show a much larger opportunity, especially repeated
RangeShiftR and CDMetaPOP bytes, but many correspond to distinct jobs,
replicates, attempts or temporal/authority records.

A future WORLD_HISTORY store could keep one immutable payload object addressed
by content hash while preserving one metadata record per governed run/output.
It would need explicit `record_id`, `run_id`, `stage_id`, parent/checkpoint,
producer/environment, seed, authority status, path history and payload digest;
readers/builders would resolve payload references without merging record
identity. Current consumers use filesystem paths and current manifests do not
provide a repository-wide resolver. No CAS, manifest rewrite or alias layer is
implemented or authorized here.

## I. Proposed F4 safe set

The exact candidate list is empty because no remaining family satisfies every
F4 criterion (proven duplicate/reproducibility, retained semantic identity,
no active consumer, replay preservation, no unavailable-source uniqueness, and
no hard-anchor loss):

| Proposed wave | Exact candidates | Files / bytes | Reason empty |
|---|---|---:|---|
| `F4A_EXACT_PHYSICAL_REDUNDANCY` | None | 0 / 0 | Exact byte matches remain associated with distinct or unresolved run, temporal, repair, authority, or engine context. |
| `F4B_REGENERABLE_WORKING_OUTPUT` | None | 0 / 0 | No remaining duplicate family has complete builder, input, environment and deterministic-output proof. C0-F2 already removed the proven pytest scratch set. |
| `F4C_DEBUG_ONLY_HISTORY` | None | 0 / 0 | No group has a compact recovery ledger proving Git history alone preserves its path/event/debug meaning. |

Thus F3 is ready for a later targeted F4 adjudication, but it recommends no
deletion now. The next useful work is per-manifest mapping for the highly
duplicated R4/R5 job families and a designed payload-reference contract, not a
bulk hash cleanup.

## J. Pytest collection diagnosis

The default root invocation without `PYTHONPATH=src` reproduced **1,613 tests
collected, 27 collection errors**. The 27 are:

| Cause class for this invocation | Count | Exact observed cause |
|---|---:|---|
| Archived source snapshot / accidental recursive discovery | 15 | `_r52_hotfix_payload/test_r52_final_seal.py` plus 7 `outputs/**/PREPATCH*/tests` and 7 `repairs/**/replacement/tests` modules fail to import `arcana_worldsim` when `src` is not on `PYTHONPATH`. These paths are historical source/repair snapshots, not default test roots. |
| Root import-path configuration | 1 | `tests/test_cross_engine_cadence_v0_6D1_R3_6C.py` also cannot import `arcana_worldsim` without `PYTHONPATH=src`. |
| Legacy import/API drift | 4 | `test_deep_production_runtime_v0_6C.py` imports missing `deep_production_runtime_v0_6C`; three R3.6 tests import missing public names `Nemo242R36BAdapter`, `NEMO_242`, and `ENGINE_REGISTRY` from `arcana_worldsim.scientific_engines`. |
| Historical artifact/manifest closure | 7 | `test_r333` through `test_r339` execute stage validation at module import and fail because required audit files removed in earlier root cleanup are absent: R3_32, R3_33, R3_34, R3_35, R3_30, R3_31 and R3_38 audit paths respectively. |
| Missing optional dependency | 0 | No such cause identified in this run. |
| Duplicate module basename | 0 in the default no-`PYTHONPATH` error set | The snapshot modules fail earlier on package import. With `PYTHONPATH=src`, duplicate basename/import-file-mismatch errors become visible for the nested output/repair tests. |

The seven root R333–R339 failures are not optional-dependency failures and are
not safely repaired by recreating old stage outputs. They expose tests that run
manifest-closure/replay work at import time and depend on historical artifacts
removed by a prior cleanup wave. No change was made to them.

For a clean B0 command, the later test policy should explicitly add the `src`
import path and constrain recursive discovery to maintained test roots so
`outputs/`, `repairs/`, and `_r52_hotfix_payload/` are not collected as tests.
The root `tests/` directory still contains legacy API-drift and import-time
manifest-closure tests. Those require a deliberate choice among compatibility
repair, conversion to isolated fixtures/markers, or relocation into a mapped
legacy archive. Do not delete their evidence to make `pytest` appear clean.
The current supported R6 regression remains the explicit
`tests/test_r6_*.py` selection (252 passed in C0-F2).

## K. Execution index repair plan

`tools/build_arcana_execution_reference_index.py` confirms:

- `candidate_paths()` uses `git ls-files`, sorts the current tracked path set,
  and excludes only the two index outputs. It does not enumerate Git-history-
  only/deleted paths. A tracked path that is missing from the worktree before
  its deletion is staged/committed can still make record construction fail
  because it calls `stat()`.
- Records contain current file path/stage/category/size/Git blob OID/SHA256;
  the builder records current HEAD and `datetime.now(timezone.utc)`. Stable
  inputs yield stable record ordering/content apart from the timestamp and
  HEAD fields, so byte-for-byte deterministic regeneration is **not** claimed.
- The index is navigation/evidence discovery metadata, not scientific
  authority. The current JSON index still cites 501 of the removed catalogue
  paths; its stale state does not restore those payloads.
- Thirteen R6 scripts pin older JSON/Markdown index blob OIDs. The index must
  not be regenerated alone: stale guards and downstream tests would then
  reject the new blobs.

Regenerate only after the final cleanup set and its commit are fixed, the 13
R6 pin sites have an explicit coordinated update/retirement decision, and the
builder output has been reviewed for path/record completeness. Then update the
index and approved pins together, run the R6 regression and link/reference
checks, and record the resulting HEAD/time. Do not regenerate during F3.

## L. Protected

- All 32,473 duplicate-participating files remain held pending semantic review;
  singleton status does not grant authority, and no singleton was deleted.
- Current R6 code, tests, contracts, authority/manifests, T0/FEG/runtime
  packages and ShellSet integration remain protected.
- All 14 current `SIMULATION_RESULTS/` files remain. Ten are the R6 FAIR
  qualification evidence under
  `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs/v0_6D1_R6_T0_ORBDATA_ARCANA_QUALIFICATION/`
  (checksums, Assign/build/ListEx1/MPI/partial-domain/partial-lithosphere and
  qualification logs, patched/reference Models outputs). Four are the README,
  JSON/CSV manifests and semantic catalogue.
- R1/R2/R3 checkpoint/replay hard-anchor candidates, all distinct external
  engine run/seed/job identities, rejected R5.2 evidence, repair/PREPATCH
  snapshots, the two protected R5 authority CSVs, references and vendored
  upstream/tool source remain untouched.
- “Not bound in R6,” “no name-matched files,” “failed,” and “duplicate hash”
  are not deletion criteria.

## M. Review unknown

- The 90 `I_UNKNOWN` groups (228 files / 5,668,070 bytes) have no stronger
  path/record cue. All category-F external-engine groups and most G diagnostic
  groups still require stage/seed/job and authority review despite their path
  labels.
- Across all duplicate participants, authority status and replay relevance
  have not been exhaustively joined to every parent/child manifest.
- Input/executable availability and reproducibility remain incomplete for
  NEMO, Geonomics, CDMetaPOP, SLiM, RangeShiftR and Madingley. BIOME4 inputs
  remain open; pyGPlates remains diagnostic; ShellSet's full mechanics remains
  unqualified.
- The seven root R333–R339 tests have missing historical manifest-closure
  files; the full intended B0 pytest discovery policy is unresolved.
- The generated execution index and 13 R6 blob pins remain stale and require a
  coordinated post-cleanup repair.

No repository files other than this report were created or edited by C0-F3.
No payloads were deleted, moved, regenerated or executed. No commit or push was
performed.
