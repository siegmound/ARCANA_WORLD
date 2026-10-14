# INT3-ENG10K-C — Fair preflight closure and Linux supervisor qualification plan

Date: 2026-10-15
Repository: `siegmound/ARCANA_WORLD`
Branch / Fair-tested source commit: `r6/si1-bandwidth-f2av` / `f072c46c77ee73e45b4ad5d7230451b19f35a692`

## Decision

`INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`

This is a Fair operator-reported result. No Fair result JSON, command transcript,
pytest log, or imported hash-bearing evidence was supplied to or independently
rehashed by this Windows task. The result must therefore be read as reported by
the operator, not as a Windows-side artifact verification.

## Reported Fair checks

- Preflight marker: `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`; exit code 0.
- Focused Linux suite at tested commit: 29 passed, 0 failed, 0 skipped.
- Runtime: Python 3.12.10 / NumPy 2.3.5.
- R4 candidate manifest SHA256: `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.
- Current source-composite SHA256: `0737c2922b6ba694d432c1bc21b0a6895f44e66be0096c6566573734d7a9eb63`.
- The reported provider identities matched the R4 references. No numerical evolution,
  supervisor execute mode, Solver work, or canonical publication occurred.
- The reported evidence root is `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE`.

The provider/input result and runtime are tied to the exact commit above. This report
contains no claim that Windows independently re-ran the provider audit or checked
those external bytes.

## Worktree and Git LFS notes

The Fair operator reports reusing the existing worktree
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV`, after a verified fast-forward;
historical evidence and the R4 bundle were preserved. This differs from the new
clone path prescribed in the ENG10K-B handoff and is recorded as an operational
exception, not a change to the general G3 procedure. Windows did not inspect the
Fair worktree or its Git reflog, so the fast-forward and preservation remain
operator-reported.

A Git LFS warning was reported, but its exact text and triggering file were not
provided. No `.gitattributes`, Git LFS filter, remote, or repository setting was
changed. The local `.gitattributes` has no LFS filter rule for the ENG10K report,
preflight, or test. Local `git lfs status` did not complete: Git LFS returned
`Not in a Git repository` and an access-denied error resolving `.git`, although
ordinary Git commands worked. This local tooling result does not explain or
adjudicate the Fair warning. Preserve the raw warning from Fair before any later
LFS-specific diagnosis; do not change configuration merely to suppress it.

## Test scope and remaining Linux runtime gap

The 29 reported tests cover R4 manifest/member integrity and tamper rejection,
source/configuration identities, authorization binding, external destination path
safety, sampled-runner calculations and fixture parsing. Supervisor-specific tests
in the original suite cover `/proc/stat` parsing, process-group RSS aggregation from
synthetic `/proc` fixtures, and a mocked TERM/KILL helper. They do not call the
actual `supervise()` launch/monitor loop with a real Linux child process.

The current Windows suite now adds two Linux-only tests using the real
`supervisor.supervise()` monitor loop and fixed synthetic Python children:

1. A harmless child exits naturally; the test checks natural exit classification,
   PID/RSS sampling, captured stdout, and the supervision record.
2. A harmless parent and descendant sleep; a shortened test-only wall limit must
   stop the process group, return a nonzero child status, and leave no surviving
   descendant marker.

The test harness replaces only the supervisor's strict command allowlist with a
closure that accepts the exact fixed `python -c` fixture command. The production
CLI, authorization validator, runner, and supervisor source are not patched at
runtime in Fair. Neither probe imports or launches `r6_int3_eng10k.py`; no ENG10K
kernel, provider, R4 bundle, or scientific input is accessed. This demonstrates
only Linux process-supervision behavior for the synthetic child, not production
authorization, a Fair job, hard resource enforcement, or numerical execution.

Local Windows verification on Python 3.12.10 with the already available NumPy
2.3.5 and pytest 8.4.2: **28 passed, 3 skipped, 0 failed**. One pre-existing
symlink fixture and both `/proc`/process-group tests were skipped for Windows
platform/policy reasons. This is not the reported Fair Python 3.12.10 / NumPy 2.3.5
runtime result. `compile()` syntax checks passed for the runner, supervisor,
library, and tests. `py_compile` could not write bytecode to the sandbox-protected
temporary directory; no successful py_compile claim is made. `git diff --check`
passed after the documentation and test changes.

Still unverified: Linux execution of the new two tests; supervisor behavior on
actual Fair `/proc`; OS-level enforcement (the limits are sampled); polling
overshoot under load; behavior for descendants that detach into another session;
real execution stdout/stderr volume handling; and forced monitoring-failure
termination. No Fair supervisor execute invocation has been run.

## Fair synthetic-test handoff

After the reviewed changes have been manually committed and published, the operator
may fetch that exact commit through the normal verified workflow. In a clean active
checkout, set `EXPECTED_HEAD` to the published full commit SHA and run only:

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate arcana-r6-linux
export PYTHONNOUSERSITE=1
export EXPECTED_HEAD='<full reviewed published commit SHA>'
test "$(git branch --show-current)" = 'r6/si1-bandwidth-f2av'
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD"
test -z "$(git status --porcelain)"
python --version
python -c 'import numpy,sys; print(sys.executable); print(numpy.__version__)'
env -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES   python -m pytest -q -rs tests/test_r6_int3_eng10k.py
```

Do not run `scripts/r6_int3_eng10k.py --mode execute`,
`scripts/r6_int3_eng10k_supervisor.py`, or any numerical runner. The pytest command
runs fixture tests; the two new probes create their evidence root only under
pytest's temporary directory and launch only the fixed synthetic child commands.

### Acceptance

- **PASS for this bounded supervisor test:** both new Linux tests execute (not
  skip), the natural child reports `NATURAL_EXIT` with code 0 and captured output,
  the timeout child reports `WALL_TIME_LIMIT`, the child process group has no live
  descendant after return, and there are no failures or artifacts outside pytest
  temporary storage. Record the actual full-suite pass/skip counts and logs as
  operator-reported until their bytes are imported and verified.
- **FAIL / stop:** either new test fails, skips on the intended Linux runtime,
  misclassifies a natural exit/timeout, leaves a live process, writes outside its
  temporary directory, or any runner/kernel command appears in the executed child.
  Preserve the log and do not proceed to an ENG10K execution request.

Passing this synthetic check closes only the Linux monitor-mechanics gap exercised
by the two probes. It does not authorize or qualify an ENG10K numerical run.

## Gates

No numerical evolution or canonical publication was performed in the reported
preflight. Preserve `F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`, and
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; INT-2C remains closed. ENG10K numerical
execution remains unauthorized pending a separate decision.
