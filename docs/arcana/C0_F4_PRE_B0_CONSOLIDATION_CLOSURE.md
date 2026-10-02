# ARCANA WORLD — C0-F4 PRE-B0 Consolidation Closure

**Status:** repository health and navigation closure; no scientific authority,
state, or payload changes authorized or performed.

## A. Final repository metrics

Metrics are measured from the current worktree against the C0 scientific
parent `2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`. File counts and logical
bytes refer to currently tracked, present files; untracked work is separate.

| Measure | Final value |
|---|---:|
| Branch / HEAD | `r6/pre-b0-data-consolidation` / `ca58c8a08b775cc490504f80e98b61b636a4ac46` |
| Tracked files present | 48,285 |
| Logical tracked bytes | 2,758,167,461 |
| Root tracked files present | 754 |
| Cumulative tracked deletions since scientific parent | 1,867 |
| Cumulative root-file deletions | 822 |
| Intended new untracked files | `pytest.ini`; this closure report |
| Unexpected untracked files | 0 |

## B–D. Cleanup chronology and payload disposition

C0-E/E3 removed 822 root files in cumulative cleanup chronology (414 in E3).
C0-F2 removed 863 verified catalog copies and 182 pytest scratch files. F3
adjudicated the remaining duplicate surface and found no safe deletion set.
F4 performed no payload deletion or relocation. Current F3 census remains
32,473 duplicate participants / 1,524,228,578 logical bytes; its 90
`REVIEW_UNKNOWN` groups comprise 228 files / 5,668,070 bytes. These historical
payloads remain intentionally retained because byte equality does not establish
semantic record identity or reproducibility.

## E. Pytest discovery policy and results

The default gate is the active R6 test surface: `tests/test_r6_*.py`, with
`pythonpath=src`. Snapshot trees under `outputs/`, `repairs/`,
`SIMULATION_RESULTS/`, and run evidence are not default test roots. R1–R5
stage-specific suites remain in `tests/` and can be invoked explicitly, for
example `python -m pytest -o python_files='test_*.py' tests/test_r52_final_seal.py`.

The initial unrestricted discovery found 1,613 tests and 27 collection errors:
15 snapshot/import issues outside the active test surface, one import-path
issue, four legacy import/API drift issues, and seven R3 closure tests missing
historical output manifests. A broad legacy run after collection isolation
completed 1,461 passed / 152 failed; failures were in R1–R5 historical
contracts, runner/source snapshots, or unavailable external evidence. One R6
test also failed in that broad run but passed in the isolated R6 suite and
final default run; its cross-suite interaction was not independently isolated.
This is not the release gate, but remains a recorded test-order risk.

With the final `pytest.ini` boundary, collection contains 252 R6 tests with
zero collection errors. Both the R6-focused run and the default `pytest`
command passed **252 tests** (default duration: 124.85 s). No historical test
source was edited or deleted.

## F–G. Execution index and WORLD_HISTORY lesson

The checked-in builder `tools/build_arcana_execution_reference_index.py` was
used to regenerate both root index representations from tracked current paths.
It produced 4,320 records in JSON and Markdown, including all 89 current
root-level R6 contract/manifest/authority surfaces in the audited filename
families. Each indexed path exists;
the two representations have matching record counts; no C0-E/F2 deleted root
path is present; no absolute machine path was introduced. The builder excludes
its own outputs and uses tracked paths, so Git-history-only files are not
current entries. It labels the index as navigational evidence only; presence
does not promote scientific authority. Its timestamp means the output is
ordered/reproducible enough for navigation, not byte-identical across runs.

The 14 retained R6 staged-blob guard files (13 scripts and one materializer)
were left unchanged. They pin the prior
index Git blobs while a candidate replacement is staged; they are not
scientific authority. They are intentionally not rewritten to the generated
index because the index itself catalogs the hashes of those guard-bearing
files, which would create a self-referential hash pin.

WORLD_HISTORY must distinguish payload identity from semantic record identity:
separate record IDs, branch/run IDs, authority, provenance, temporal support,
and causal links may refer to one shared payload hash. Content-addressed
storage remains a B0 design requirement only and is not implemented here.

## H. Protected authority and gates

R6 T0, PRE_ORBDATA, FEG/runtime package, S1B evidence, governed ShellSet source
and patch, and both R5 authority CSVs remain present. Historical
pre-execution records are not rewritten. Current authorization remains:

```text
runtime_authorized=true
scope=LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE
mechanics_authorized=false
forward_evolution_authorized=false
dt_selected=false
t1_created=false
canonical_state_changed=false
```

## I. Remaining unknowns

The 90 F3 `REVIEW_UNKNOWN` duplicate groups remain unresolved. Historical R1–R5
test failures and missing evidence remain outside the default R6 gate; they
must be invoked and adjudicated by stage before any legacy suite is used as a
release gate. No remaining payload was deemed safe to delete.

## J–K. B0 readiness and validation

Repository consolidation is ready for review/commit; this does not authorize
B0 implementation or alter R6 runtime/mechanics gates. Validation performed:

- R6 focused suite: **252 passed**.
- Default pytest discovery boundary: **252 collected, 0 collection errors**.
- Full historical sweep: **1,461 passed, 152 failed**, classified above.
- Execution index: **4,320 records**, JSON/Markdown counts consistent; zero
  missing current paths, stale deleted-root entries, or machine-specific paths.
- Documentation local links: **15 checked, 0 broken**.
- `git diff --check`: **PASS** (Git reported only line-ending normalization
  notices for the regenerated index).

No commit or push was performed.
