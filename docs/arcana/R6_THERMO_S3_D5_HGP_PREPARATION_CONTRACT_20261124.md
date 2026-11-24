# S3-D5 — HGP preparation contract (source candidate)

2026-11-24. S3-D5 HGP preparation/readback candidate implemented, source-only, no engine launch path. Fixed BL691 phase-list replacement C1→HGP; isolated HGP alpha .555→.550 for B; conditional lAb for C. Pin D4 audit, S2 manifest/reference PRN, all four upstream fixture Git blobs, archive/executable and historical input parity. Runtime paths from authenticated S2 RUN_PROVENANCE; no write to S2 or external evidence. Phase-agnostic D3 parser and exact native-token comparison distinguish fresh repeats from model sensitivity. Resource observations only (disk/cgroup/scheduler); budgets not ratified. New targeted tests authored, not yet run on FAIR or locally. --phase run explicitly blocked; execution adapter still pending separate resource binding and authorization.

## Scope
A native HGP .555, B isolated paper-alpha .550, C HGP+low-albite conditional. Source bytes remain immutable. Four files exactly as in S1/S2; no extra option file injected. The preflight authenticates original S2 archived inputs against exact upstream blob IDs and checks release binary bytes against both the historical report and the tar archive. It reads only the one historic reference PRN, not a repeat of the five-process audit. All transformations happen in memory and emit per-case input hashes. No output directory created. No engine invocation. The later launcher must recreate and verify these bytes and ensure the original default-option behavior, preserve all native files, telemetry, failures and independent fresh processes. A change of phase set across different model configurations is an observation, not an automatic failure. No assumption that HGP or low-albite must appear.

## FAIR next
NEXT exact-commit FAIR isolated worktree: run new test module plus existing three S3 modules, then --phase preflight read-only. Return exact source SHA, pytest summary, JSON and exit; no MEEMUM. If PASS, bind actual allocation and implement bounded launch adapter, no repeated historical S2 audit. 4 initial fresh processes +2 conditional, no grid expansion. S2 SEALED, 50/50 UNKNOWN/NOT_APPROVED, S3 engines0, D-024 ACTIVE, physical_T1=null, mechanics/history false.

From a clean isolated source checkout, use arcana-r6-linux and PYTHONPATH=src:. with PYTHONDONTWRITEBYTECODE=1 and PYTHONNOUSERSITE=1. Run:

```bash
python -m pytest -q -ra --tb=short tests/test_r6_thermo_s3_d5_hgp_prepare_v1.py tests/test_r6_thermo_s3_design_v1.py tests/test_r6_thermo_s3_native_readback_v1.py tests/test_r6_thermo_s3_d4_numeric_screen_v1.py
python -m experiments.r6_thermo_provider_pilot_v1.s3_d5_hgp_prepare --phase preflight
```

The test and native preflight have not been executed by the GitHub author. The launch path is intentionally absent, and --phase run fails before any preflight or engine call. Report available resources as observations, not permission; no default NULL→unlimited. Exact database endmember parity and mineral model science remain UNKNOWN. Preserve failed evidence; no auto reset/clean or changes to the old source worktree.
