# INT-2C-C3 — Supervised Linux replay launcher preparation

Date: 2026-10-14. Entry branch `r6/si1-bandwidth-f2av`, HEAD
`7ebbccfa136056b2467ece43fbb7fde51748c531`; tracked worktree/index clean.

**Decision: `INT2C_C3_SUPERVISED_LAUNCHER_READY__REAL_REPLAY_PENDING`.**
This is code readiness with offline tests, not a Linux supervisor runtime PASS,
real B0 replay, numerical equivalence or execution authorization. No Fair command
or real R4 kernel was executed in this preparation.

## Implementation and unchanged contracts

`scripts/r6_int2c_replay_launcher.py` supplies one CLI and a standard-library
Linux supervisor, reusing `attest_r4()`, `HistoryStore`,
`validate_replay_inputs()`, `execute_replay()` and `DeterministicKernelAdapter`.
The adapter, attestor, B0 core, physical kernel, original R4 bundle, expected
identities and numerical configuration are unchanged.

Default mode is **preflight only**. The future numerical mode additionally
requires `--execute-authorized`, an operator acknowledgement that cannot issue
authorization. There is no retry or fallback. Direct `--child` is an internal
supervisor interface requiring a START handshake; it is not an execution command
for the operator.

The parent checks fresh/external output paths, missing inputs, symlink ancestry,
canonical-path exclusion, exact clean source commit and loaded module bytes
against that commit. Twelve relevant launcher/adapter/attestor/B0/kernel source
files are recorded with byte and normalized-text hashes. R4's pinned nine-file
manifest, provenance and historical kernel are reauthenticated by the existing
attestor. Python 3.12.10 and NumPy 2.3.5 must load from the exact isolated prefix
`/home/jlpfritas/miniforge3/envs/arcana-r6-replay-r4-py31210`; external NumPy or
another interpreter is rejected even with matching version labels. Recorded
NumPy module hash is not a complete historical library-binary attestation.

### Protecting the existing C2 store

Source: `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/INT2C_C2_ljWdyPsq/isolated_history_store`.
HistoryStore construction can initialize lock/view metadata or recover pending
transactions. To preserve C2, the child verifies its reported 16-file/78,945-byte
inventory and makes an exact byte copy at `<new evidence>/store_read_copy`.
Current HistoryStore opens that copy; no append/publication API is called.
Source hashes are rechecked after copying and after processing. Every one of the
eleven original/prepared/technically attested typed records must match the newly
authenticated preparation before `validate_replay_inputs()` succeeds. The new
checkpoint and recipe must also match the fixed Windows C1 identities.

This is a verified working read copy of the existing C2 store, not a new source
of authority or republication of C2. Only the copy can undergo constructor
recovery. No read-only replacement store framework or B0 contract change was
introduced. Source inventory hashes observed now do not independently prove
historical C2 bytes: C1/C2 historical results remain OPERATOR_REPORTED as recorded
in `docs/arcana/INT2C_C1_C2_FAIR_EVIDENCE_RECONCILIATION.md`.

### Genuine execution and acceptance, when separately authorized

The numerical child passes the real adapter to current `execute_replay()`.
A transparent wrapper records the returned object and returns that same object
unchanged to B0. It never inserts expected values into the prediction. The child
writes `COMPUTED_STATE.json` and `REPLAY_RESULT.json`, including the complete
state ID, both historical pretty-JSON/LF per-support digests, B0 verification,
source/runtime/configuration and C2 inventory. A mismatch exits 2 and retains
the computed state and metrics. An exception is reported as FAILED; partial
files, stderr and supervision survive. No mismatch normalization is implemented.

Fixed targets:

- State: `r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a`.
- Each support: `2b4836954e688d7aac6d9e26ccb61aa02fa94e9e40550c395922b30fa1b45d7b`.
- Checkpoint: `r6checkpoint_45ccc437cbe2d5d8d40febbbbc3d7d6d5b5a1a42e7060ca40027048524b71158`.
- Recipe: `r6recipe_46e4b555cd4f996cd58020b840819c6ff468cb4640254fb3bb4efb6e887a4c92`.
- Two 73-node R4 states, duration 1,000 engineering years, fraction 0.0005,
  original source-bound frozen forcing. Expected output remains an oracle only.

## Supervision contract and limitations

The parent launches `sys.executable` explicitly in a new Linux process session,
captures stdout/stderr to fresh files, verifies `/proc/<pid>/exe` and start ticks,
and samples the actual root and descendants before sending START. Both launch
contexts remove invalid Git object-directory variables; PATH, PYTHONPATH and
ARCANA_EXTERNAL_ROOT are preserved. User-site imports are disabled.

Thresholds: 900 seconds from subprocess launch, summed sampled process-tree RSS
2 GiB, cumulative evidence-directory bytes 512 MiB. Samples are taken on a
0.1-second loop, with scan costs additional. Linux RSS is the working-set proxy;
shared pages may be double counted across processes. Supervisor RSS is excluded.
These are monitored thresholds, not cgroup/OS quotas or guaranteed peak bounds.
Overshoot and finalization time are explicit. Final size after evidence sealing
and manifest SHA are emitted to the parent console; SUPERVISION.json's byte
observation precedes its own sealing metadata.

On a threshold, monitoring error or interruption, termination uses process-group
SIGTERM then SIGKILL and identity-checked observed descendants, with bounded
wait. Natural child exit code is preserved. Signal exits are separately classified as
CHILD_SIGNAL_EXIT; the actual negative child code is retained and the CLI uses
128+signal. Controlled threshold/supervisor stops use CLI exit 124. No automatic retry or cleanup.
SUPERVISION.json records PID/start ticks/executable, command, observed process
identities, elapsed time, sampled peak RSS, output observation, actual child exit
code, stop reason, thresholds and overshoot. ARTIFACT_MANIFEST.json covers all
existing output files except itself, using streamed SHA256.

This is not hostile-process containment. A descendant that escapes the group
and disappears/reparents between observations may not be attributable; polling
cannot prove an unobserved instantaneous peak. The real adapter is a single
local numerical Python path, not an MPI/ShellSet job. Concurrent mutation of
source paths is not atomically prevented; byte comparisons fail on observed
changes. A complete OS-isolation claim is deliberately excluded.

## Offline verification

Combined launcher, INT-2C-A/B, INT-1A, INT-2A and INT-2B regressions:
**86 passed, 6 skipped, 1 deselected**. The six Linux runtime tests are NOT_TESTED
on Windows: natural exit propagation, wall-time termination, memory termination,
output termination, descendant termination and external signal classification. The deselected test is existing
Windows B0 atomic store publication; it was not attempted. py_compile passed.
Windows tests cover synthetic transparent capture and mismatch preservation,
complete typed readback, missing/corrupt checkpoint, altered forcing, exact pins,
runtime rejection before launch, source commit/dirty-tree rejection, CLI binding,
path collisions/overlap/missing/canonical paths, byte-exact store copy, /proc
field decoding, descendant/group accounting and PID-reuse filtering. Synthetic
kernel/storage doubles are confined to tests; no real R4 kernel was invoked.

Launcher SHA256: `bbc05c19795a2c2bb4630c6c429491b06b317d77ec2dd294a1301ab367c33e06`.
Test SHA256: `cbe13bdc0655e1d938591ff0fee2655b4a889fd3fda6bb56bb8b7ed4983e7e69`.

## Fair handoff — offline self-test first

Only an already authorized Fair operator should run these commands. The child
shell prevents a failed check from terminating the interactive SSH session.
Inspect untracked files printed by status before checkout; Git must not overwrite
them. The final launcher commit SHA is supplied by Windows publication; this
handoff additionally pins its direct parent and launcher/test bytes.

```bash
bash <<'SH'
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV || exit 1
git status --short
test -z "$(git status --porcelain --untracked-files=no)" || exit 1
git fetch origin r6/si1-bandwidth-f2av || exit 1
INT2C_COMMIT=$(git rev-parse FETCH_HEAD)
test "$(git rev-parse "$INT2C_COMMIT^")" = 7ebbccfa136056b2467ece43fbb7fde51748c531 || exit 1
git switch --detach "$INT2C_COMMIT" || exit 1
printf '%s  %s\n' \
  bbc05c19795a2c2bb4630c6c429491b06b317d77ec2dd294a1301ab367c33e06 scripts/r6_int2c_replay_launcher.py \
  cbe13bdc0655e1d938591ff0fee2655b4a889fd3fda6bb56bb8b7ed4983e7e69 tests/test_r6_int2c_replay_launcher.py | sha256sum --check || exit 1
export PYTHONPATH="$PWD/src:$PWD/scripts"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
INT2C_PYTHON=/home/jlpfritas/miniforge3/envs/arcana-r6-replay-r4-py31210/bin/python
test -x "$INT2C_PYTHON" || exit 1
"$INT2C_PYTHON" -c 'from pathlib import Path; import subprocess; import r6_int2c_replay_launcher as x; print(x.runtime_check()); print(x.source_check(Path.cwd(),subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()))' || exit 1
"$INT2C_PYTHON" -m pytest -q -rs tests/test_r6_int2c_replay_launcher.py || exit 1
SH
```

All six required Linux runtime supervision cases must PASS, not skip. The
Windows-only platform rejection case is expected to skip on Linux. No physical
kernel runs in that test module. Preserve stdout/test evidence with commit and
hashes according to PROCEDURE; an actual Fair self-test PASS has not been obtained
by Windows in this task.

### Final provider-free B0 preflight (no numerical execution)

After the self-test and source verification, use the exact isolated Python with
the environment above. The bundle path below is a proposed locator based on the
existing local layout; its presence on Fair must be checked, not assumed. If
missing, locate the verified unchanged R4 bundle before proceeding; no substitute.

```bash
INT2C_REPO=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV
INT2C_PYTHON=/home/jlpfritas/miniforge3/envs/arcana-r6-replay-r4-py31210/bin/python
INT2C_PREFLIGHT=/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/INT2C_C3_PREFLIGHT_20261014_01
test ! -e "$INT2C_PREFLIGHT" && \
"$INT2C_PYTHON" "$INT2C_REPO/scripts/r6_int2c_replay_launcher.py" \
  --repository "$INT2C_REPO" \
  --bundle "$INT2C_REPO/outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04" \
  --store /home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/INT2C_C2_ljWdyPsq/isolated_history_store \
  --output "$INT2C_PREFLIGHT" --source-commit "$(git -C "$INT2C_REPO" rev-parse HEAD)"
```

Require NATURAL_EXIT, child exit 0, PREFLIGHT_PASS_NO_NUMERICAL_EXECUTION,
unchanged original C2/R4 inputs and verified full output manifest. Then stop for
separate bounded authorization. The future execution uses the same CLI only with
`--execute-authorized` and a fresh, separately approved run directory, e.g.
`.../INT2C_C3_REPLAY_20261014_01`; that directory's absence is not yet checked on
Fair. No execution command has been run or authorized by this report.

## Unchanged gates

`BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`,
`RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`,
`ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
