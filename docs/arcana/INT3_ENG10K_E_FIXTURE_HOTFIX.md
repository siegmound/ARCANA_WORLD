# INT3-ENG10K-E — descendant fixture interpolation hotfix

Date: 2026-10-15
Repository: `siegmound/ARCANA_WORLD`
Branch / starting HEAD: `r6/si1-bandwidth-f2av` / `5ea8f6604bc4583a01b600f12f68eff3f9cd14f2`

## Decision

`INT3_ENG10K_E_FIXTURE_HOTFIX_READY__FAIR_RETEST_PENDING`

This change fixes only the Linux synthetic descendant fixture and adds a
cross-platform source-construction regression. It does not change the production
supervisor, ENG10K runner, numerical configuration, or authorize an ENG10K run.

## Fair failure preserved

The latest operator-reported Fair INT3-E suite collected 42 tests: 41 passed,
one failed, zero skipped. The failing test was
`test_linux_supervise_waits_for_live_descendant_after_leader_exits`; it failed
while constructing the child source, before calling `supervisor.supervise()`, with
`NameError: name 'os' is not defined` at test line 704. No log digest was supplied
for this 42-test retest. This result remains a suite FAIL, not a supervisor
regression result or PASS. The log is operator-reported and was not
transferred/rehashed here.

Preserved earlier observations remain distinct: INT3-C 30 PASS / 1 FAIL;
INT3-D 40 PASS / 1 FAIL; INT3-E first attempt collection error, exit 2; and the
earlier INT3-E test attempt 41 PASS / 1 FAIL, reported log SHA256
`f33b3c9d49b230c782018941b198e0bda4e951623c7f13aa316a6356f3194b1f`. None is
reclassified by this fixture correction.

## Minimal correction and regression

The outer test f-strings had evaluated `{os.getpid()}` in the pytest process while
building child code; `os` is imported only inside that child code. The fixture now
comes from `_live_descendant_fixture_source()`. Doubled braces preserve
`{os.getpid()}` and `{os.getpgrp()}` as expressions in the child program, where
`import os` makes them evaluable. Both the ready and finished marker writes use
the helper. A platform-independent test checks both expressions, the child import,
and Python syntax with `compile()` without starting the supervisor.

The original Linux test still waits for the child's `READY` handshake, checks the
recorded PID/process-group binding against the supervisor's group, then verifies
the completion marker and natural-exit wait. The Windows syntax check alone does
not verify Linux process-group behavior.

## Windows verification and blocker

The focused pytest command was attempted with the default available Python, but
collection stopped before tests because importing the test module requires NumPy
and that interpreter has no NumPy installed (`ModuleNotFoundError: No module named
'numpy'`). No tests were collected by pytest; no packages were installed. Thus the
new pytest regression and the full suite have no pytest PASS/skip result on this
Windows environment. Separately, `py_compile` passed; an AST-isolated invocation of
the actual helper confirmed both child expressions and compiled the generated
program; the prior interpolation form reproduced `NameError`; and `git diff
--check` passed. When dependencies permit collection, three Linux process tests are
expected to skip on Windows; they require actual execution on Fair.

## Fair test-only handoff

After review and publication, run the focused module on the reviewed full commit in
the existing approved `arcana-r6-linux` Conda environment, in a new absent evidence
directory. Do not reuse any INT3-C/D/E evidence path. This is a test-only command;
it does not invoke the production supervisor CLI or ENG10K kernel:

```bash
(
  source "$HOME/miniforge3/etc/profile.d/conda.sh"
  conda activate arcana-r6-linux
  export PYTHONNOUSERSITE=1
  if [[ "$(git branch --show-current)" != 'r6/si1-bandwidth-f2av' || \
        "$(git rev-parse HEAD)" != '<REVIEWED_FULL_SHA>' || \
        -n "$(git status --porcelain)" ]]; then
    echo "branch/HEAD/worktree precondition failed" >&2
    exit 2
  fi
  EVIDENCE="$HOME/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_E_FIXTURE_HOTFIX/<NEW_UNIQUE_ID>"
  if [[ -e "$EVIDENCE" ]]; then
    echo "evidence path already exists" >&2
    exit 2
  fi
  mkdir -m 700 "$EVIDENCE" || exit 2
  env -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
    python -m pytest -q -rs tests/test_r6_int3_eng10k.py \
    --basetemp "$EVIDENCE/pytest-tmp" 2>&1 | tee "$EVIDENCE/pytest.log"
  pytest_exit=${PIPESTATUS[0]}
  sha256sum "$EVIDENCE/pytest.log"
  exit "$pytest_exit"
)
```

Require zero failures and zero skips for the three Linux process tests: natural
single-child exit, leader exit with a live descendant, and process-group timeout.
Record the exact commit, runtime, collected/pass/fail/skip totals, exit code, log
SHA256 and evidence path. Any failed run remains immutable and is not reclassified.

## Preserved boundaries

No Fair retest or ENG10K evolution ran for this hotfix. Kernel, forcing, R4 bundle,
provider inputs, numerical settings, WORLD_HISTORY and scientific authorization
gates are unchanged.
