# INT3-ENG10K-B — Fair integration implementation report

Date: 2026-10-15
Repository: `siegmound/ARCANA_WORLD`
Branch/starting HEAD: `r6/si1-bandwidth-f2av` / `16e4fa94bab659879a871222bd96ec72c561dfc3`
Status: Windows worktree only; no commit or push performed.

## Decision

`INT3_ENG10K_FAIR_INTEGRATION_CODE_READY__FAIR_RUNTIME_PREFLIGHT_PENDING`

This is an implementation/test readiness decision only. No connection to Fair,
provider-backed preflight, supervisor run, numerical evolution or canonical data
operation was performed. No execution authorization was created.

## Implementation

ENG10K now takes a pre-existing external evidence root from `--evidence-root` or
`ARCANA_EVIDENCE_ROOT`, requires an absolute root named `ARCANA_WORLD_EVIDENCE`,
checks that it is accessible and outside the checkout and WORLD_HISTORY, and
accepts only relative destinations under `R6/INT3_ENG10K/<attempt>/`. Candidate
and supervision destinations must share one attempt ID, be distinct and be
collision-free. R4 bundle overlap, path traversal, absolute destination values,
symlink/junction components and existing candidate/attempt paths fail closed.
Preflight creates no root, attempt directory, candidate or supervision file.

The supervisor and child runner use the same root and relative destinations. The
separate authorization contract binds the absolute root, absolute and relative
candidate/supervision identities, exact source HEAD, configuration identity and
the existing bounded-attempt limits. The execution contract JSON is pinned by
SHA256 `6ce5e12de99f422827b66a530ac4590b3c7e40b788a7013b622edefc700b63f8` and
continues to set both execution and canonical publication authorization false.
The runner independently checks the active branch and exact full expected HEAD.

Fair's provider audit requires an active branch name, unlike the general detached
checkout recipe. For this lane only, [PROJECT_LEDGER/PROCEDURE.md](../../PROJECT_LEDGER/PROCEDURE.md)
and the Fair handoff specify a fresh clone, inspection, fetched-ref ancestry and
fast-forward-only update to the exact reviewed SHA. The provider branch check
and runner exact-HEAD check remain mandatory.

The external Fair evidence root is fixed in the contract and handoff as
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE`; preflight refuses to
create it. Future output layout is
`R6/INT3_ENG10K/<attempt_id>/{candidate,supervision}`. The R4 input must be passed
as an explicit existing read-only bundle path on Fair; the historical manifest
identity remains `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.

On restricted Windows, fixture-created paths may deny handle-based
`Path.resolve()`. The helper therefore uses normalized absolute paths only on
Windows after checking every path component for symlinks/junctions; POSIX retains
strict `resolve()`. This is not a race-free guarantee against concurrent path
replacement. Windows no-follow/reparse checks and Linux `/proc` supervision still
require platform-specific Fair/runtime verification.

## Verification

- Focused ENG10K tests: **28 passed, 1 skipped, 0 failed**. The skip is the
  symlink-creation case because Windows policy may deny link creation.
- `py_compile`: PASS for runner, supervisor, library and test module.
- Execution-contract JSON parsing and pinned SHA check: PASS.
- `git diff --check`: PASS.
- Added a focused failure-path regression: a candidate directory may receive an
  exclusive `INCOMPLETE.json` only while unsealed and paired with the expected
  supervision streams; a sealed manifest or collision is never overwritten.
- Test runtime was local Windows Python 3.12.10 / NumPy 2.5.1 / pytest 9.1.1;
  it is not the required Fair Python 3.12.10 / NumPy 2.3.5 environment.
- The first pytest invocation could not create its default temp directory; the
  rerun used a fresh explicit `--basetemp` under `outputs/`. It passed as above.
- No full preflight ran: the Windows bootstrap did not provide the Fair evidence
  root or Fair provider payloads, and the source files remain uncommitted/dirty.
  No Fair or external-provider identity is claimed here.

## Required Fair-only checks and blockers

After the user manually reviews, commits and publishes the exact source, an
authorized Fair operator must use a fresh active-branch clone, inspect the
published ancestry, bind `EXPECTED_HEAD`, choose the already existing exact
runtime and R4 bundle, validate root/quota/provider input identities, run the
focused Linux tests, then run only `--mode preflight`. The exact commands and
stop conditions are in [INT3_ENG10K_FAIR_PREFLIGHT.md](INT3_ENG10K_FAIR_PREFLIGHT.md).

Still pending: Fair checkout/runtime/toolchain observation, Linux supervisor
execution tests, Fair external-root access/quota, provider payload availability,
fresh source-composite identity, R4 bundle path and the no-write Fair preflight.
The 10,000-year evolution is outside this task and remains unauthorized pending
a separate decision. No scientific or canonical gate changed.

## Files intended for a later manual code commit

The user should review exact membership before staging. This task made no commit
or push. Candidate task files are:

- `configs/r6_int3_eng10k/INT3_ENG10K_EXECUTION_CONTRACT.json`
- `docs/arcana/INT3_ENG10K_FAIR_PREFLIGHT.md`
- `docs/arcana/INT3_ENG10K_FAIR_INTEGRATION_REPORT.md`
- `scripts/r6_int3_eng10k.py`
- `scripts/r6_int3_eng10k_supervisor.py`
- `src/arcana_worldsim/r6/int3_eng10k.py`
- `tests/test_r6_int3_eng10k.py`
- `PROJECT_LEDGER/PROCEDURE.md`
- `PROJECT_LEDGER/STATUS.md`
- `PROJECT_LEDGER/NEXT_ACTION.md`
- `PROJECT_LEDGER/EVIDENCE_INDEX.md`
- `PROJECT_LEDGER/LOG.md`
- `PROJECT_LEDGER/ROADMAP.md`
- `PROJECT_LEDGER/README.md`

Pre-existing dirty ledger edits and every untracked evidence/output path are
preserved and must not be swept into the later commit without individual review.
