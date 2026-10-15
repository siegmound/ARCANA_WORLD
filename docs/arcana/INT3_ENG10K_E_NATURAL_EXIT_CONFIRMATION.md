# INT3-ENG10K-E — Natural Exit Confirmation

Date: 2026-10-15
Repository: `siegmound/ARCANA_WORLD`
Branch / baseline: `r6/si1-bandwidth-f2av` / `84c04fddac0fe078958dc0fe2ccbbe9e7c2c23fd`

## Decision

`INT3_ENG10K_E_WINDOWS_CORRECTION_READY__FAIR_LINUX_RETEST_PENDING`

This is a bounded supervisor/test correction. It does not authorize the ENG10K
runner, numerical evolution, Fair production supervision, or canonical operations.

## Fair observation and evidentiary limit

The Fair result is operator-reported; the original `pytest.log` remains immutable
at the supplied Fair evidence location and was not transferred or independently
rehashed here. It reports 41 collected, 40 passed, one failed, no skips. The
single-child natural-exit and process-group timeout tests passed. The
leader-exited/live-descendant test returned `NATURAL_EXIT` after
`0.033428873866796494` seconds although its child fixture intended to run about
0.45 seconds; its minimum assertion was 0.35 seconds. The reported pytest log
SHA256 is `a9fa5713ab91799a1301619a617ba7b86165dda5719d498425f2eaeb3de377a1`.
The child PID, process-group membership, `/proc` samples, and exact ordering of
`poll()` versus snapshot were not captured in the supplied evidence. Therefore
the observation does not prove that the supervisor saw the descendant alive.
The earlier INT3-C/D failures and their original evidence remain unchanged.

## Code finding and correction

In `scripts/r6_int3_eng10k_supervisor.py`, the loop previously took
`_proc_group_snapshot()` and only then called `process.poll()`. An empty sample
could therefore predate the observed leader exit. If the leader exited between
those operations while a just-created child had not yet appeared in the scan (or
was in a `/proc` transition), that one sample plus the newly observed exit code
could be misclassified as `NATURAL_EXIT`. This is a code-level race path; it is a
plausible explanation of the reported result, not a proven reconstruction of the
historical Fair process state.

The loop now observes `poll()` before collecting the group snapshot. Once the
leader has exited, a live member keeps the supervisor sampling and resets the
empty-group timer. `NATURAL_EXIT` requires repeated empty snapshots spanning
`NATURAL_EXIT_CONFIRMATION_S = 0.5` seconds, with each sample taken after the
leader exit was observed. At the existing 0.1-second poll interval this ordinarily
requires multiple post-exit observations. Half a second is a bounded race-settling
window, longer than the reported 0.45-second child lifetime and the 0.35-second
test minimum; it is a supervisor race guard, not a general OS guarantee. The
existing wall-time check is evaluated before natural-exit acceptance, so the
confirmation cannot intentionally extend the 900-second monitoring limit.

PID/start-tick/process-group checks, terminal `Z`/`X`/`x` handling, fail-closed
RSS verification for live processes, output/RSS limits, and process-group timeout
termination are retained. No generic monitoring exception is suppressed.

## Deterministic regression fixture

The leader/descendant test now uses a startup handshake. The child writes its PID
and process-group ID to a readiness record and signals `READY`; only after the
parent receives that signal does the parent return immediately. The child then
remains alive for approximately 0.45 seconds and records completion. The test
checks that the recorded child group equals the monitored leader group, that the
child completed, that the supervisor waited, and that the supervisor captured the
readiness record. This distinguishes a fixture startup failure from supervisor
early exit. A platform-independent state-transition regression checks the bounded
empty-group timer, its reset for a live member, and that a running leader cannot
confirm natural exit.

## Windows verification

Focused command: `python -m pytest -q -rs tests/test_r6_int3_eng10k.py` with a
fresh writable `--basetemp` inside the checkout. Result: **38 passed, 4 skipped,
0 failed**. The skips are the Windows symlink-creation policy test and the three
Linux `/proc`/process-group tests. `py_compile` for the supervisor and test module
passed; `git diff --check` passed. The default Python lacked NumPy; the test run
used the existing pytest environment plus the already-installed workspace NumPy
2.3.5 path, without installing packages. Windows does not execute or validate
Linux `/proc` semantics; the Fair retest remains required.

## Fair Linux handoff — tests only

After the reviewed changes are published, the operator should use the existing
approved Conda runtime and a **new, absent evidence directory**. Replace
`<REVIEWED_FULL_SHA>` and `<NEW_UNIQUE_ID>` only after publication; never reuse the
preserved INT3-C/D evidence path. This runs the focused test module only, not the
supervisor CLI or ENG10K kernel:

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate arcana-r6-linux
export PYTHONNOUSERSITE=1
test "$(git branch --show-current)" = 'r6/si1-bandwidth-f2av'
test "$(git rev-parse HEAD)" = '<REVIEWED_FULL_SHA>'
test -z "$(git status --porcelain)"
EVIDENCE="$HOME/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_E_SUPERVISOR_TESTS/<NEW_UNIQUE_ID>"
test ! -e "$EVIDENCE" || { echo "evidence path already exists" >&2; exit 2; }
mkdir -m 700 "$EVIDENCE"
env -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
  python -m pytest -q -rs tests/test_r6_int3_eng10k.py \
  --basetemp "$EVIDENCE/pytest-tmp" 2>&1 | tee "$EVIDENCE/pytest.log"
pytest_exit=${PIPESTATUS[0]}
sha256sum "$EVIDENCE/pytest.log"
test "$pytest_exit" -eq 0
```

Record the exact commit, command, Python/NumPy/pytest versions, collected/pass/
fail/skip totals, exit code, log SHA256 and evidence path. The natural-exit,
leader-with-live-descendant and timeout tests must execute and pass, not skip;
the full suite must have zero failures. Any failure remains immutable and is not
reclassified. No Fair command has been run for INT3-E.

## Preserved boundaries

No kernel, forcing, numerical configuration, R4 checkpoint/bundle, source-locked
scientific code, WORLD_HISTORY or canonical data changed. No Fair runtime test,
production supervisor invocation, ENG10K evolution, MPI, Solver or replay ran.
Scientific, Solver, mechanics and WORLD_HISTORY gates remain unchanged.
