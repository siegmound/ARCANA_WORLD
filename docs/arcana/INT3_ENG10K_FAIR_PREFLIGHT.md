# INT3-ENG10K-B — Fair integration preflight handoff

**Scope:** read-only Fair integration/preflight only. This document does not authorize
the ENG10K evolution, the supervisor's numerical execution mode, Solver work, or
canonical publication. The current gate is
`INT3_ENG10K_FAIR_INTEGRATION_CODE_READY__FAIR_RUNTIME_PREFLIGHT_PENDING`.

## Pinned inputs and required operator values

- Code branch: `r6/si1-bandwidth-f2av`; use the full reviewed commit SHA published
  by the operator as `EXPECTED_HEAD`. The runner rejects any other branch or HEAD.
- R4 read-only bundle manifest SHA256:
  `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.
- Existing governed provider root: set `ARCANA_EXTERNAL_ROOT` to the existing,
  authorized directory on Fair; its name must end in `_ARCANA_EXTERNAL_SOURCES`.
  Do not create or substitute a provider root.
- Existing external evidence root, created and governed by the operator before
  this gate: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE`. It must
  already exist, be accessible, be outside the checkout and WORLD_HISTORY, and
  have no symlinked/junction components. Neither preflight nor this handoff
  creates it.
- R4 bundle: set `R4_BUNDLE` to the absolute path of an already-existing
  read-only copy. No default repository `outputs/` path is presumed to exist on
  Fair. Stop if the authenticated manifest is unavailable or differs.
- Runtime: inspect existing environments only. The candidate isolated prefix is
  `$HOME/miniforge3/envs/arcana-r6-replay-r4-py31210`; verify Python 3.12.10 and
  NumPy 2.3.5 from that exact interpreter. Also inspect `arcana-r6-linux` if
  useful, but do not assume it matches. No package installation, environment
  creation or interpreter fallback is allowed.

## Safe active-branch checkout exception (ENG10K lane only)

The provider audit requires the real active branch name, so the historical G3
detached-HEAD recipe is not suitable for this lane. Use a **new clone directory**;
do not repurpose the existing Fair worktree. Substitute the repository's known
GitHub URL and a fresh checkout path selected by the operator:

```bash
git clone --single-branch --branch r6/si1-bandwidth-f2av \
  https://github.com/siegmound/ARCANA_WORLD.git "$NEW_CHECKOUT"
git -C "$NEW_CHECKOUT" status --short
git -C "$NEW_CHECKOUT" branch --show-current
git -C "$NEW_CHECKOUT" rev-parse HEAD
git -C "$NEW_CHECKOUT" fetch origin r6/si1-bandwidth-f2av
git -C "$NEW_CHECKOUT" log --oneline --decorate -5
git -C "$NEW_CHECKOUT" status --short
```

Inspect the fetched commits and require `origin/r6/si1-bandwidth-f2av` to equal
the independently reviewed/published full `EXPECTED_HEAD`. If this fresh clone's
local branch is behind that verified remote-tracking ref, fast-forward only in
this new clone after confirming the clean status and ancestry:

```bash
git -C "$NEW_CHECKOUT" merge-base --is-ancestor HEAD origin/r6/si1-bandwidth-f2av
git -C "$NEW_CHECKOUT" merge --ff-only origin/r6/si1-bandwidth-f2av
git -C "$NEW_CHECKOUT" switch r6/si1-bandwidth-f2av
git -C "$NEW_CHECKOUT" status --short
git -C "$NEW_CHECKOUT" branch --show-current
git -C "$NEW_CHECKOUT" rev-parse HEAD
```

Require an empty tracked/untracked status, branch exactly
`r6/si1-bandwidth-f2av`, and HEAD exactly `EXPECTED_HEAD`. Do not use reset, clean,
forced updates, automatic merges or deletion. If the branch/HEAD relation is not
the expected fast-forward, stop and reconcile outside this preflight.

This is a lane-specific G3 exception, not a relaxation: the branch is checked by
the provider audit and the full exact HEAD is required by the runner.

## Read-only Fair checks

Run from the verified checkout. The variables below must be set to actual existing
paths; these commands intentionally do not create any directories:

```bash
export EXPECTED_HEAD='<full reviewed and published commit SHA>'
export ARCANA_EVIDENCE_ROOT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE
export ARCANA_EXTERNAL_ROOT='<existing governed provider root ending _ARCANA_EXTERNAL_SOURCES>'
export R4_BUNDLE='<absolute path to existing read-only R4 bundle copy>'
export RUNTIME="$HOME/miniforge3/envs/arcana-r6-replay-r4-py31210"
test -d "$ARCANA_EVIDENCE_ROOT" && test -w "$ARCANA_EVIDENCE_ROOT" && test -x "$ARCANA_EVIDENCE_ROOT"
test -d "$ARCANA_EXTERNAL_ROOT"
test -d "$R4_BUNDLE"
test -x "$RUNTIME/bin/python"
"$RUNTIME/bin/python" --version
"$RUNTIME/bin/python" -c 'import sys, numpy; print(sys.executable); print(numpy.__version__); print(numpy.__file__)'
df -h "$ARCANA_EVIDENCE_ROOT"
quota -s 2>/dev/null || true
```

Require Python `3.12.10` and NumPy `2.3.5` from this interpreter. `df`/quota
observations are informational; they do not attest future resource sufficiency.
Confirm that the R4 manifest hashes to the pinned digest without changing the
bundle:

```bash
sha256sum "$R4_BUNDLE/CANDIDATE_MANIFEST.json"
```

The two reserved targets are relative to the evidence root and must both be
absent before preflight:

```bash
test ! -e "$ARCANA_EVIDENCE_ROOT/R6/INT3_ENG10K/INT3_ENG10K_5_11_DIRECT_RESTART_20261014_01"
```

Use a sanitized child environment. Do not rely on values exported in another
terminal. From the checkout root:

```bash
cd "$NEW_CHECKOUT"
env -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
  ARCANA_EXTERNAL_ROOT="$ARCANA_EXTERNAL_ROOT" \
  ARCANA_EVIDENCE_ROOT="$ARCANA_EVIDENCE_ROOT" \
  ARCANA_EXPECTED_SOURCE_HEAD="$EXPECTED_HEAD" \
  "$RUNTIME/bin/python" scripts/r6_int3_eng10k.py \
    --mode preflight \
    --expected-head "$EXPECTED_HEAD" \
    --evidence-root "$ARCANA_EVIDENCE_ROOT" \
    --r4-bundle "$R4_BUNDLE"
```

The child independently checks exact Python/NumPy versions, sanitized Git object
environment, active branch/full HEAD, clean execution sources, the pinned
execution contract/configuration, governed provider audit and component bindings,
historical R4 manifest/source/kernel identities, and both target paths. Expected
marker: `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`. It must report absolute
root/output/supervision/R4 paths and create no root, attempt directory or file.
Capture the terminal output in the operator's pre-existing handoff record; do not
redirect into either reserved target. Record the exact command, exit code and
SHA256 of any separately retained transcript. No transcript is represented as
historical evidence unless actually acquired and hashed.

Run only the focused offline test module in the exact runtime:

```bash
env -u GIT_OBJECT_DIRECTORY -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
  "$RUNTIME/bin/python" -m pytest -q tests/test_r6_int3_eng10k.py
```

These tests must remain fixture-only. Do not run the runner's `execute` mode or
the supervisor against ENG10K. A synthetic Linux supervisor test is only a
monitoring test; it is not execution authorization.

## External output and authorization boundary

Future attempt payloads and supervision records are siblings under
`ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K/<attempt_id>/candidate` and
`.../<attempt_id>/supervision`. The root must preexist; the runner validates
absolute root identity, containment, no symlink/junction path components,
non-overlap with the checkout, WORLD_HISTORY and R4, safe relative paths, same
attempt ID, and collision-free destinations. Preflight is read-only. Only the
supervisor, after a distinct valid execution authorization, creates the unique
attempt/supervision directories. That authorization must bind full source HEAD,
configuration SHA256, absolute evidence root, and both relative and absolute
candidate/supervision paths. No authorization is issued here.

The Linux supervisor uses a new process group, samples `/proc` process membership
and RSS, accumulates candidate plus captured-stream bytes, and can send TERM then
KILL on monitored limit or monitoring failure. Limits (900 seconds, 2 GiB sampled
process-group RSS, 512 MiB cumulative output) are sampled thresholds, not kernel
quotas; polling overshoot and detached descendants remain limitations. No
production execution is in scope for this preflight.

## Gate status

Windows implementation/tests do not establish Fair runtime, Linux `/proc`
supervisor behavior, provider availability on Fair, free space/quota enforcement,
resource sufficiency, or physical validity of a 10,000-year extrapolation. This
gate stops after read-only Fair preflight and its evidence acquisition. Any later
numerical run requires its own explicit authorization bound to the final commit,
configuration, provider/R4 identities, new output attempt and supervisor budget.
