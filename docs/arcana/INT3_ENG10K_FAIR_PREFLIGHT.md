# INT3 ENG10K — FAIR non-numerical preflight handoff

This handoff authorizes no FAIR activity now and no numerical evolution. It describes only a later, separately scheduled **preflight without `--mode execute`**. Do not proceed if the source-composite mismatch below remains unresolved or if a separate authorization is absent.

## Required identities and data

Use the exact reviewed code commit after publication; verify its full SHA from GitHub and the FAIR checkout. Use the existing `arcana-r6-linux` Conda environment only after confirming its interpreter and NumPy identities; no install, environment recreation or fallback is permitted. Set `ARCANA_EXTERNAL_ROOT` to the already governed source directory available on that FAIR host. The R4 bundle must be an existing read-only copy whose manifest is `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; do not copy over or modify the historical bundle.

Do not assume the Windows R4 `outputs/` directory exists on FAIR. Before running the command below, verify that the standard bundle path exists and has the expected manifest, or stop and report the missing input. No placeholder path is an identity.

## Read-only command sequence

From the verified FAIR worktree, with Conda activated through the existing procedure:

```bash
git status --short
git rev-parse HEAD
python --version
python -c 'import numpy; print(numpy.__version__)'
test -n "$ARCANA_EXTERNAL_ROOT" && test -d "$ARCANA_EXTERNAL_ROOT"
test -f outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/CANDIDATE_MANIFEST.json
sha256sum outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/CANDIDATE_MANIFEST.json
python -m pytest -q tests/test_r6_int3_eng10k.py
python scripts/r6_int3_eng10k.py --mode preflight
```

`--mode preflight` does not call the numerical kernel. Expected success marker is `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`. The source-composite identity includes the audited current Git HEAD, so it is recorded separately from the authenticated historical R4 source composite. The preflight requires the current audit to bind to current HEAD and requires every non-source-set provider component identity to match the corresponding R4 forcing `source_refs`. It fails closed on any component mismatch; do not skip, override or rewrite this comparison.

The default candidate and supervision destinations are:

```text
outputs/r6_functional_development/INT3_ENG10K_5_11_DIRECT_RESTART_20261014_01
outputs/r6_functional_development/INT3_ENG10K_SUPERVISION_20261014_01
```

For preflight they must both remain absent. The preflight reports their status but creates neither. No `--authorization-json`, `--mode execute`, supervisor launch, or numeric runner is part of this gate.

## Fair-only verification boundary

Linux `/proc` sampling, actual process-group membership, captured streams, natural exit propagation, and SIGTERM/SIGKILL behavior cannot be proven by Windows fixture tests. Verify only through bounded synthetic supervisor tests in the existing Conda environment. These tests must not invoke ShellSet, MPI, the ENG10K execution mode, or the physical kernel. Descendants that deliberately detach into a separate session are outside the current process-group monitor and must remain an explicit limitation.

## If a later separate execution is proposed

Resolve the provider/source-composite discrepancy first; verify exact code commit, config SHA, R4 bundle, environment, new output and supervision paths, and Linux supervisor behavior. Then request a separate authorization binding the exact commit, configuration hash, paths, one attempt and monitored thresholds (900 s, 2 GiB sampled process-group RSS, 512 MiB output). These are sampled stop thresholds, not OS quotas. A preflight PASS alone is not permission to execute.
