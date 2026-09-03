# v0.6D1-R4.0 — ARCANA Multi-Engine Scientific Revalidation & Orchestrator Consolidation

R4.0 preserves R3.19–R3.39 as `ARCANA_REDUCED_ORDER_BASELINE_A`, consolidates external-engine governance under ARCANA, freezes seven revalidation windows before seeing results, and fail-closes until every required runtime identity is available.

After the initial inventory, use `provision_v0_6D1_R4_0_engines.ps1`. The governed default is WSL2 + isolated Conda environments; native overrides remain supported.

### Governed local runtime bindings
The provisioner writes `set_r40_engine_env.local.ps1` with explicit `ARCANA_WSL_EXE`, `ARCANA_WSL_CONDA`, and engine-environment bindings. `run_v0_6D1_R4_0.ps1` auto-loads this local file before inventory so Python runtime discovery cannot silently diverge from the PowerShell provisioning path.

Windows/WSL runtime readiness is bridged through fresh PowerShell-owned host evidence before Python inventory, avoiding false `MISSING` results caused by Python-side `wsl.exe` discovery/execution differences.
