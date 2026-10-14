# INT3-ENG10K-D — Linux process-state reconciliation

Date: 2026-10-15
Repository: `siegmound/ARCANA_WORLD`
Branch / baseline: `r6/si1-bandwidth-f2av` / `ba81c8cfc18b750358f174d1504d89b275ef7647`

## Decision

`INT3_ENG10K_D_WINDOWS_FIX_READY__FAIR_RETEST_PENDING`

## Fair failure: conservative interpretation

The Fair test outcome below is operator-reported; the original log remains at
`ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_C_SUPERVISOR_TESTS/ba81c8cf_20261015/`
and was not imported or rehashed in this Windows worktree:

- 31 collected; 30 passed and 1 failed.
- Natural-exit fixture: child exit 0 after 0.26849564909935 seconds, root PID
  1632066, but supervisor classified
  `MONITORING_FAILURE:PROC_RESOURCE_SNAPSHOT_UNVERIFIABLE:1632066`.
- Sampled process-group RSS was 9,437,184 bytes.
- The distinct timeout test with a real synthetic descendant passed.

The natural-exit result is **not** a supervisor PASS: resource state could not be
verified and fail-closed behavior was correct. A terminal process disappearing or
being observed as a zombie without `VmRSS` is a plausible race consistent with the
reported signature, but Fair's `/proc` state/status bytes were not supplied, so the
root cause is not independently established. The timeout pass does not remedy the
natural-exit failure.

## Minimal correction

`scripts/r6_int3_eng10k_supervisor.py` now parses and validates the state field in
`/proc/PID/stat` while retaining the robust last-`)` boundary for command names
containing parentheses. A snapshot excludes `Z`, `X`, and `x` terminal processes.
If status/RSS is missing or malformed, it rereads `stat`: a vanished or now-terminal
PID is skipped; a still-live PID with unverifiable RSS continues to fail closed.
For live members, a second `stat` read binds the RSS sample to the same start ticks
and process group; detected PID reuse fails closed. The known leader's start ticks
are checked whenever its PID is observed again. Natural exit still requires the
child leader to have exited and the snapshot to contain no live process-group
members, so a zombie does not mask a live descendant.

This narrows `/proc` race handling only. It does not suppress generic errors,
establish kernel-level resource enforcement, or prove behavior on Fair.

## Offline regressions

`tests/test_r6_int3_eng10k.py` now covers terminal `Z`/`X`/`x` without `VmRSS`,
live processes with absent or malformed `VmRSS`, disappearance between `/proc`
reads, PID reuse, invalid state parsing, and a zombie leader with a live descendant.
The existing Linux-only real-supervisor natural-exit and timeout-group tests remain;
a further Linux-only fixture verifies that the supervisor waits while a descendant
remains alive after its leader exits. Existing authorization, RSS/output limit,
path, and command-binding tests remain in the focused suite.

Windows result after the PID-reuse regression: **37 passed, 4 skipped, 0 failed**.
The skips are one platform-dependent symlink test and three Linux `/proc`/process-group tests.
Windows fixtures validate parsing and race decisions, not Linux kernel semantics.

## Fair-only handoff

After review and manual publication, use a **new immutable evidence directory**;
do not reuse or alter the preserved failing Fair log. On the existing approved
Fair Conda runtime, verify the exact published HEAD and clean active branch, then
run only:

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate arcana-r6-linux
export PYTHONNOUSERSITE=1
test "$(git branch --show-current)" = 'r6/si1-bandwidth-f2av'
test "$(git rev-parse HEAD)" = '<exact reviewed published commit SHA>'
test -z "$(git status --porcelain)"
mkdir -m 700 "$HOME/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_D_SUPERVISOR_TESTS/<new-unique-id>"
EVIDENCE="$HOME/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_D_SUPERVISOR_TESTS/<new-unique-id>"
env -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
  python -m pytest -q -rs tests/test_r6_int3_eng10k.py \
  --basetemp "$EVIDENCE/pytest-tmp" 2>&1 | tee "$EVIDENCE/pytest.log"
pytest_exit=${PIPESTATUS[0]}
sha256sum "$EVIDENCE/pytest.log"
test "$pytest_exit" -eq 0
```

First check `test ! -e "$HOME/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_D_SUPERVISOR_TESTS/<new-unique-id>"`;
the identifier must be new, otherwise choose another and preserve the existing
directory. Record the exact command, commit, runtime, collected/pass/fail/skip
counts, exit code and log SHA256. Do not run supervisor CLI, `--mode execute`, the
ENG10K runner, or numerical evolution. PASS requires the natural-exit,
leader-plus-live-descendant, and timeout tests to execute (not skip) and pass, plus
the full focused suite with no failure.
Any monitoring failure, unexpected skip, survivor, or test failure remains FAIL and
must be preserved without retrying ENG10K.

## Scope and gates

No Fair access, Linux runtime test, supervisor production invocation, ENG10K
evolution, provider audit, R4 modification, or WORLD_HISTORY operation was made
in this correction. The Fair process-state fix remains runtime-pending. Preserve
the reported no-evolution preflight as operator-reported and all prior gate
decisions; this change authorizes neither supervisor execution nor ENG10K evolution.
