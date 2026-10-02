# C0-E Safe Repository Cleanup Ledger

**Branch:** `r6/pre-b0-repository-consolidation`
**Parent scientific HEAD:** `2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`
**Commit/push:** none; explicitly out of scope.

## A. Baseline

At start of C0-E, the checkout was at the expected branch and parent with one
pre-existing untracked C0-B audit report. Baseline inventory: **50,140** tracked
paths, **1,576** tracked root-level files and **3,134,912,039 bytes** (about
2.92 GiB) of logical tracked content.

## B. Documentation created/updated

- Replaced the obsolete R3.6B/NEMO root `README.md` with the R6 World History
  entrypoint.
- Replaced the stale root `ARCANA_WORLD_CURRENT_STATE.md` with a compatibility
  pointer to the maintained R6 state document.
- Added `ARCANA_BOOTSTRAP.md`, `ARCANA_CURRENT_STATE.md`,
  `WORLD_HISTORY_ARCHITECTURE.md`, `DATA_AUTHORITY_MAP.md`,
  `PROVIDER_REGISTRY.md`, `LEGACY_ARCHIVE_MAP.md` and `CLEANUP_POLICY.md` under
  `docs/arcana/`.
- This ledger records exact removals, preserved exceptions and validation.

## C. Deleted file families

Removal was limited to root-level, tracked, stage-specific files matching the
families below. Candidate basenames were checked against tracked source, scripts,
tests, current `R6_*` JSON/Markdown authority/report files, and the current
authority register. The first broad scan retained 82 candidates because of
legacy R3/R4/R5 references; a later R6-only scan found no R6 references to
those candidates, so they were removed in the second root-level pass.
No removed path was referenced by the searched active source/test/builder or
current R6 authority surface. Historical bytes are recoverable from Git history.

| Family | Count removed | Reason / evidence | Historical role and recovery |
|---|---:|---|---|
| `README_R3_*`, `README_R4_*`, `README_R5_*` | 136 | Superseded stage entrypoints; no searched active R6 source, test, builder or current authority reference to those exact files. Referenced exceptions retained. | Stage setup, validation and handoff context; recover from Git history. |
| `NEXT_STAGE_HANDOFF_*` | 26 | Historical continuation prompts; no searched active R6 source, test, builder or current authority reference to those exact files. Referenced exceptions retained. | Human handoffs between old stages; recover from Git history. |
| Root stage runner/check/recovery PowerShell (`run_v0_6D1_R*`, selected `run_v0_6D_R*`, `capture/check/provision_v0_6D1_R*`, `run_r455_*`) | 161 | One-shot stage launch/verification wrappers; unreferenced by searched source, tests, scripts/builders and current R6 authority files. R5.17 authority-recovery tools and referenced runners were not candidates. | Historical stage orchestration; implementation/evidence remains in Git history and corresponding retained artifacts. |
| `APPLY_R52_FINAL_SEAL_HOTFIX_V2.ps1` | 1 | Obsolete one-time seal hotfix application wrapper; no searched active consumer. | Historical repair workflow; recover from Git history. |
| `README_PARENT_v0_6D1*.md` | 2 | Superseded R0/R1 parent-stage entrypoints; no exact R6 source/test/builder/authority reference. | Historical project entrypoints; recover from Git history. |

The first pass conservatively retained candidates referenced only by R3/R4/R5
tests/scripts. A second root-level pass applied the R6-only dependency boundary
and removed those additional README/handoff/runner candidates too.
Total removed: **408 tracked files**. No files under `src/`, `tests/`,
`scripts/`, `external/`, `outputs/`, `local_runs/` or `SIMULATION_RESULTS/`
were removed.

## D. Individual exceptions retained

- The 28 root R3/R4/R5 stage documents directly cited by the R6 source/contract
  scan remain. These include exact contracts and R5 authority records used by
  current R6 reuse maps, bootstrap artifacts and provider contracts.
- The R5.17 authority recovery PowerShell tools were outside the removal family
  and remain.
- Three root R4.32 `.txt` readmes remain as historical source evidence: current
  `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY` introspection outputs name them.
- Other R3/R4/R5 contracts, authority reports, manifests, JSON, tests and source
  were not removed by prefix.
- `C0_B_AUTHORITY_DEPENDENCY_AUDIT.md` was already untracked before C0-E and was
  preserved.
- `outputs/`, `local_runs/`, `SIMULATION_RESULTS/`, all hard anchors, current R6
  payloads, and qualification evidence remain untouched.

## E. REVIEW_UNKNOWN

- Root R3/R4/R5 contracts and reports outside the removed README/handoff
  patterns; some are direct R6 authority/reuse dependencies.
- Other root PowerShell helpers not in the reviewed family, including any
  mechanism whose reuse status has not been adjudicated.
- All JSON, data and generated-result families, including duplicate copies in
  `SIMULATION_RESULTS/`; these require a separate hash/consumer audit.
- The execution reference index remains stale and may contain historical paths;
  it is navigational, not an authority source. Regeneration is a separate
  metadata task.
- The supplied FAIR S1B runtime-load handoff reports a successful bounded load,
  while the tracked pre-execution compatibility closure still records
  `runtime_authorized=false` and
  `runtime_or_mechanics_qualification_claimed=false`. Keep the scope bounded and
  reconcile the evidence metadata in a separately governed step.

## F. Post-cleanup metrics

Measured from tracked paths still present in the working tree (the Git index
still lists unstaged deletions until a later authorized commit):

- Tracked paths present: **49,732** (50,140 baseline minus 408 removals).
- Tracked paths still in index: **50,140**.
- Tracked root-level files present: **1,168** (1,576 baseline minus 408).
- Logical size of remaining tracked files: **3,134,310,156 bytes** (~2.9191 GiB).
- Logical size reduction: **601,883 bytes** (~0.00056 GiB); the benefit is lower
  root/context clutter, not material disk-space reduction.
- New untracked files are not included in these tracked metrics.

## G. Validation

- Branch and parent: verified before and after cleanup: `r6/pre-b0-repository-consolidation`
  at `2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`.
- Protected-path check: passed; the 408 deletions are all root-level files in
  the four listed families; no R6 source, R6 test, R6 builder, current R6
  payload, ShellSet source or protected data path was deleted.
- R6-focused tests after the second root-level pass: **252 passed** across 32 test modules (131.70 s).
- Full repository suite was attempted before the second root-level pass, but collection stopped with 26 legacy
  collection/import errors in 100.99 s. Reported causes include duplicate
  test-module basenames under archived `outputs/`/`repairs/` trees and legacy
  imports of `ENGINE_REGISTRY`. No error reported a removed cleanup path; the
  full suite is not a usable gate until its collection layout/import baseline is
  repaired.
- Current R6 reference scan: zero exact references to the removed README,
  handoff and stage-runner candidates. The 28 other R6-cited root stage docs
  were retained. The two parent README paths had no R6 references.
- Markdown links: **9 current README/docs files checked; zero broken local links**.
- Authorization-boundary agreement: **passed**; current state lists all required
  false gates and bootstrap says not to infer mechanics/evolution permission.
- `git diff --check`: **passed**. New untracked documentation whitespace check:
  **passed** (zero trailing whitespace).

## H. Risks

Legacy stage tests/tools that are outside R6 may have depended on files removed
here even though no selected active R6 source/test/builder/current-authority
consumer referenced them. The R6-focused regression is the release gate for this
wave. Historical documentation and scripts can be recovered from Git history;
the separately retained results and manifests were not altered.

## I. C0-E3 ROOT SURFACE FINAL REDUCTION

This section records the final root-only reduction. It does not rewrite the
earlier C0-E deletion history above. Branch and parent remained
`r6/pre-b0-repository-consolidation` and
`2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`.

### Inventory and removals

Before E3, 1,168 tracked root files were present. The extension inventory was:

| Extension group | Before E3 | After E3 |
|---|---:|---:|
| `.md` | 442 | 146 |
| `.txt` | 3 | 0 |
| `.ps1` | 37 | 0 |
| `.patch` | 0 | 0 |
| `.diff` | 0 | 0 |
| `.py` | 78 | 0 |
| `.json` | 599 | 599 |
| `.yaml` / `.yml` | 1 | 1 |
| `.toml` | 0 | 0 |
| `.ini` / `.cfg` | 0 | 0 |
| `.csv` | 2 | 2 |
| `.dat` | 1 | 1 |
| other (`.feg`, `.npz`, `.gitattributes`, `.gitignore`) | 5 | 5 |
| **Total** | **1,168** | **754** |

E3 removed **414** root-level tracked files. Grouped by extension and governed
classification:

| Classification | Files | Rationale |
|---|---:|---|
| `DELETE_HISTORICAL` | 299 (`.md` 296, `.txt` 3) | Superseded R3/R4/R5 stage reports, contracts, status notes and old text readmes with no current R6 basename reference; history remains recoverable from Git. |
| `DELETE_ONE_SHOT` | 115 (`.py` 78, `.ps1` 37) | Root-level stage-specific audit, runner, recovery, setup and verification utilities with no current R6 caller or R6 basename reference; these are not active R6 builders. |
| Other deletion classes | 0 | No root patches/diffs or JSON files were removed. |

The reference scan covered `src/arcana_worldsim/r6/`, `scripts/r6_*`,
`tests/test_r6_*`, the Arcana docs other than this cleanup ledger, current root
`R6_*` text artifacts and the scientific authority register. It found **zero
E3-deleted basenames** in that active R6 surface. The execution reference index
was treated as navigational, as directed. Earlier C0-E notes reported 28
retained legacy documents from a broader scan; this E3 count is the narrowed
current-R6 exact-basename scan (9 Markdown and 15 JSON files), while the earlier
wave's recorded history is preserved above.

All 414 deleted paths were root-level. The 9 legacy Markdown files and 15
legacy JSON records with direct current R6 references were retained. All root
JSON was retained under the explicit no-broad-JSON-cleanup rule. No path under
`src/`, `tests/`, `scripts/`,
`external/`, `patches/`, `outputs/`, `local_runs/`, `SIMULATION_RESULTS/` or
`docs/` was deleted. The governed ShellSet patch and vendored ShellSet source
remain present and unmodified.

### Retained root map

| Retained family | Why it remains |
|---|---|
| 302 `R6_*` files | `KEEP_AUTHORITY`: current R6 authority, T0 state, provenance, replay, runtime package and qualification surface. |
| 9 directly R6-cited legacy Markdown and 15 directly R6-cited legacy JSON files | `KEEP_AUTHORITY`: explicit cross-stage reuse/provenance links found in the scoped scan. |
| 417 remaining root JSON files | `KEEP_REFERENCE`: retained under the explicit C0-E3 JSON default-retention rule for a later data/artifact wave; not asserted to be active runtime inputs. |
| `README.md` and `ARCANA_WORLD_CURRENT_STATE.md` (2) | `KEEP_CURRENT`: project entrypoint and compatibility pointer. |
| `ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.*` (2) | `KEEP_AUTHORITY`: current cross-cutting scientific authority register. |
| `ARCANA_EXECUTION_REFERENCE_INDEX.*` (2) | `KEEP_REFERENCE`: navigational legacy index; it does not protect historical files by itself. |
| `.gitignore`, `.gitattributes`, `environment-r6-linux.yml` (3) | `KEEP_LEGAL_CONFIG`: repository and R6 environment configuration. |
| Two root R5 snapshot CSVs | At E3 close these were `REVIEW_UNKNOWN`; E4 adjudication below resolves both to `KEEP_AUTHORITY` based on their producing scripts and R5 authority consumers. |
| `PATCH*`, `HOTFIX*`, `RECOVERY*`, `SEAL*` historical JSON manifests | Included in the 417 JSON holdouts and retained by the explicit no-broad-JSON rule; they are not the current ShellSet patch. The governed patch under `patches/shellset/` was protected. |

### Prefix inventory after E3

The root prefix-family counts are: `R3*` 27, `R4*` 1, `R5*` 231, `R6*` 302,
`README*` 1, `NEXT*` 0, `APPLY*` 0, `RUN*` 0, `CHECK*` 0, `BUILD*` 0,
`PATCH*` 11, `HOTFIX*` 2, `RECOVERY*` 1, `SEAL*` 2, `AUDIT*` 0,
`CONTRACT*` 0, `HANDOFF*` 0, and other 176. Prefix counts overlap no groups.

### E3 validation and metrics

| Measure | Before E3 | After E3 | E3 change |
|---|---:|---:|---:|
| Tracked-present files | 49,732 | 49,318 | -414 |
| Tracked-present root files | 1,168 | 754 | -414 |
| Logical bytes, all tracked-present files | 3,134,310,156 | 3,132,495,393 | -1,814,763 |
| Logical bytes, root files | 508,254,610 | 506,439,847 | -1,814,763 |

- R6-focused tests: **252 passed** across the existing `tests/test_r6_*.py`
  selection (135.79 s).
- `git diff --check`: passed after E3.
- Local Markdown links in the root README, current-state pointer and 8
  `docs/arcana/*.md` files: **15 checked, 0 broken**.
- Protected root `R6_*` files: **302 tracked, 0 missing**.
- Deleted paths outside repository root: **0**.
- Current R6 exact-basename reference check: **0 E3 deletions referenced**.
- Governed ShellSet patch exists; diff under `external/ShellSet-v1.1.0/` and
  `patches/`: **0 changed paths**.
- No commit or push was made.

### E3 residual review

- At E3 close, two retained root CSVs were `REVIEW_UNKNOWN` because no R6
  basename or SHA reference was found. C0-E4's cross-stage producer/consumer
  audit resolves both as `KEEP_AUTHORITY` below.
- The remaining 417 root JSON files are explicitly deferred by the no-broad-JSON
  rule; they are classified `KEEP_REFERENCE` pending the later data/artifact
  wave, not claimed as active runtime dependencies. The 9 legacy Markdown files
  and 15 legacy JSON records with direct R6 references are positively protected.
- The stale execution index may still list historical paths; it is retained for
  navigation and excluded from the active dependency test.

## J. C0-E4 FINAL ROOT CLOSURE

This section is the authoritative final status and metric set; the C0-E and
C0-E3 sections above remain per-wave chronology. No files were deleted in E4.

### CSV adjudication

| Path | Size | Worktree SHA256 | Producer-recorded SHA256 / semantics | Producer and role | Classification |
|---|---:|---|---|---|---|
| `R5_17_B7_A3F2_P7C_CO2_SNAPSHOT_BINDING.csv` | 2,738 bytes | `1ce62cfd132c9f6fa823383c7db71b12c68cd093c92302c7aae1a409312ce5b8` | `57be7841e334e7e4dea6541d81f77361f2b2bbb33e6945831fcbd9c661ae489e` for the producer's CRLF CSV output; converting the checked-in LF file to CRLF reproduces this hash. | Produced by the historical `R5_17_B7_A3F2_P7C_BIND_PALEO_CO2_AUTHORITY.py`; 12 age-indexed CO2 snapshot bindings, with source dataset and interpolation details also recorded in the P7C JSON. | `KEEP_AUTHORITY` |
| `R5_17_B7_A3F2_P7T_TEMPORAL_SNAPSHOT_REGISTRY.csv` | 5,931 bytes | `fdbf299df338bacddaface93e91237aa5eecabb34f5996334888088147443454` | `fda3bfaa162f0eac6f8739550d2eadee78112e6fcfbf457e5d4f024cfb780331` for the producer's CRLF CSV output; converting the checked-in LF file to CRLF reproduces this hash. | Produced by historical `R5_17_B7_A3F2_P7T_DEFINE_HUMAN_SUPPORT_TEMPORAL_SNAPSHOTS.py`; 12-row shared temporal snapshot authority covering 200 ka to 0 ka and recording readiness/semantics by domain. | `KEEP_AUTHORITY` |

The P7T producer is deterministic and pins ARCANA HEAD
`43731502aa210f0714473f0f71606eaf5f769375`; its R3.27/R3.28 replay NPZs and
checkpoint JSON inputs remain present. P7C is deterministic from the P7T
authority/registry and the NOAA/NCEI Antarctic ice-core CO2 input. That external
source file is not present in this worktree, although its dataset identifier,
URL, source hash and coverage are recorded in P7C authority JSON. Thus exact
CSV blobs are recoverable from Git, but Git history alone is not a complete
rebuild environment, especially for P7C.

Consumers/provenance references found in the tracked parent include the P7T,
P7C and P7S producer scripts, the P7T and P7C authority JSON, the P7S authority
JSON, and the historical root-index builder. The P7T registry is a direct P7C
and P7S input; the P7C CSV is the governed companion output consumed through
P7C's authority binding for later CO2 routing. The values are unique materialized
stage evidence (the P7T per-domain readiness columns are not represented by its
age list alone); the P7C JSON also embeds rows, but names the CSV and its
producer-output hash. Both files therefore remain current provenance inputs for
their R5 authority records. Their raw worktree SHA differs from the producer
hash solely because the producer emits CRLF and the Git checkout stores LF;
the content and recorded producer hashes reconcile exactly after line-ending
conversion. No CSV content or scientific values were changed.

### Current documentation authority gates

`docs/arcana/ARCANA_BOOTSTRAP.md` and
`docs/arcana/ARCANA_CURRENT_STATE.md` now agree:

- `runtime_authorized=true` only for
  `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`;
- `mechanics_authorized=false`;
- `forward_evolution_authorized=false`;
- `dt_selected=false`;
- `t1_created=false`;
- `canonical_state_changed=false`.

The historical pre-execution compatibility closure still contains its earlier
false runtime authorization and was not rewritten. `C0_B_AUTHORITY_DEPENDENCY_AUDIT.md`
remains intentionally preserved.

### Authoritative final metrics

These counts were computed from the current worktree after E4 documentation
updates. Untracked documents are counted separately from Git-tracked files.

| Metric | Final value |
|---|---:|
| Cumulative deleted tracked files | 822 |
| Cumulative deleted root files | 822 |
| Tracked-present root files | 754 |
| Tracked-present files, all paths | 49,318 |
| Logical bytes across tracked-present files | 3,132,495,393 |
| Intended untracked documents for a later commit | 9 |
| Unexpected untracked files | 0 |

The 9 intended untracked documents are `C0_B_AUTHORITY_DEPENDENCY_AUDIT.md`
and the 8 `docs/arcana/*.md` documents. No commit or push has occurred.

### Final regression

- Full R6-focused set: **252 passed**.
- `git diff --check`: **PASS**.
- Current README/Arcana documentation local-link check: **15 checked, 0 broken**.
- Exact R6 reference scan against cumulative root deletions: **0 active R6
  basename references**. The C0 cleanup ledger and stale execution index are
  excluded as audit/navigation metadata; neither is an active R6 consumer.
- All 302 root `R6_*` paths remain present; ShellSet integration source and the
  governed patch are present and unchanged.

**PASS_C0_E_ROOT_CLEANUP_CLOSED_READY_TO_COMMIT**
