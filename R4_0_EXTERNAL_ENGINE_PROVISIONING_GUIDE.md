# R4.0 External Engine Provisioning Guide — governed WSL2 path

R4.0 remains fail-closed. External engines are evidence providers only; ARCANA remains the canonical state owner.

## Why the first inventory reported every engine as MISSING
The original R4.0 probe only searched the direct process PATH for several tools. In particular, the already-used NEMO runtime from R3.6D lives in the WSL Conda environment `arcana-nemo242` and was invoked historically with `conda run -n arcana-nemo242 nemo2.4.2`. The revised probe checks governed WSL Conda environments directly.

## WSL discovery hardening
The provisioning runner does not assume that `conda` is exported by a non-interactive login shell. It checks the login PATH, common Miniforge/Miniconda/Anaconda locations, then performs a bounded search under `$HOME`, `/opt`, and `/usr/local`. Empty WSL stdout is handled as an empty result rather than calling `.Trim()` on `$null`. The ARCANA root is converted to `/mnt/<drive>/...` directly, so provisioning no longer depends on `wslpath` output either.

## Governed environment layout
The provisioning script creates/reuses isolated WSL2 Conda environments:

- `arcana-nemo242` — NEMO 2.4.2
- `arcana-geonomics-149` — Python 3.11 + Geonomics 1.4.9
- `arcana-r40-r` — R 4.5 + MadingleyR 1.0.6 / C++ 2.02 + RangeShiftR 3.0.1
- `arcana-cdmetapop-308` — Python 3.8 + NumPy/SciPy for CDMetaPOP 3.08
- `arcana-slim52` — SLiM 5.2 + tskit/msprime/pyslim

This avoids contaminating the ARCANA project Python environment.

## Exact upstream identities
- NEMO: 2.4.2.
- Geonomics: 1.4.9.
- MadingleyR: 1.0.6 with Madingley C++ 2.02.
- RangeShiftR: package version 3.0.1; frozen to official commit `d01f1b6` (23 July 2026 parameter-check bugfix) and checked after installation.
- CDMetaPOP: 3.08 source pinned to commit `3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118` (`v3.08 clean`, 2025-09-18) plus Python 3.8 runtime.
- SLiM: 5.2 with tskit >=1.0.2, msprime >=1.4.1, pyslim >=1.1.1.

## Provisioning command
From the ARCANA root in PowerShell:

```powershell
.\provision_v0_6D1_R4_0_engines.ps1
```

The script provisions all six runtimes, writes `set_r40_engine_env.local.ps1`, then reruns `run_v0_6D1_R4_0.ps1` automatically.

To rebuild every governed environment from scratch:

```powershell
.\provision_v0_6D1_R4_0_engines.ps1 -ForceReinstall
```

## Fast inventory-only check
After provisioning:

```powershell
.\check_v0_6D1_R4_0_engine_provisioning.ps1
```

## Expected R4.0 semantics
A successful runtime seal means only that the exact engine identities are available and the seven comparison windows remain frozen before result inspection. It does **not** claim that external engines agree with ARCANA. Scientific cross-engine runs are the next operation within R4.0.

### Governed local runtime bindings
The provisioner writes `set_r40_engine_env.local.ps1` with explicit `ARCANA_WSL_EXE`, `ARCANA_WSL_CONDA`, and engine-environment bindings. `run_v0_6D1_R4_0.ps1` auto-loads this local file before inventory so Python runtime discovery cannot silently diverge from the PowerShell provisioning path.

### Fresh runtime identity evidence
Normal `run_v0_6D1_R4_0.ps1` runs no installer. It now executes `capture_v0_6D1_R4_0_runtime_evidence.ps1` first so Windows PowerShell owns the WSL process boundary known to work on the local host. The generated JSON is runtime evidence only and is regenerated before inventory; exact R4.0 version pins are revalidated by Python.
