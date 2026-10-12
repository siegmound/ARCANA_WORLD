# NEXT — INT-0B noncanonical execution, pending explicit authorization

**Current result (2026-10-13):** `INT0B_PROVIDER_INPUTS_VERIFIED__EXECUTION_PENDING_AUTHORIZATION`. The provider-backed audit for pair 5:11 passed read-only on source HEAD `dde79ebe4d26ab7b21eff08245fc83330239c0bc`. Input inventory and hashes, sampling bounds, exact proposed command, unique output destination, and stop budget are in `docs/arcana/INT0B_PROVIDER_PREFLIGHT.md`.

## Authorized scope if and only if the user explicitly approves

- Existing T-F2B engineering runner `scripts/r6_functional_development_t_f2b.py`; ordered pair 5:11; T0=210 Ma; exact support cells `R6G1D-R091-C029` and `R6G1D-R091-C028`; admitted existing profiles; frozen instantaneous Euler forcing; 1,000 engineering years; resolution factors 0.001, 0.0005, 0.00025.
- Local Windows CPU/Python only; one process, no MPI, Fair, ShellSet, Solver or factorization. Python 3.12.10 and NumPy 2.3.5 were available at preflight. The runner rechecks branch and provider identities at execution time.
- Proposed unique output: `outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01`; it was absent when checked. Never overwrite or clean an existing destination. Preserve any partial output as failed/non-authoritative.
- Proposed stop budget: 15 minutes wall time; 2 GiB process working-set monitoring threshold; 512 MiB output directory cap. These are run-specific operator-monitored limits, not OS-enforced quotas or measured candidate resource use. The diagnostic samples are bounded to 10,001 records/support and 73 profile nodes; the schema-based sampled JSON size estimate is ≤350,000,000 bytes. If active monitoring cannot be provided, do not run.
- Exact command sequence from repository root:

```powershell
$env:ARCANA_EXTERNAL_ROOT = 'F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES'
$env:PYTHONPATH = 'C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src'
python --version
python -c "import numpy; print(numpy.__version__)"
python scripts/r6_functional_development_t_f2b.py --repository-root . --expected-branch r6/si1-bandwidth-f2av --output-relative outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01
```

Do not execute this command until explicit user authorization. Approval must be for this exact noncanonical engineering run and its input access, output path, process/time/memory/output limits, and stop behavior; it does not authorize any scientific or canonical promotion.

## Stop conditions and validation

Stop on branch/HEAD or input digest mismatch; missing/unexpected support or profile identity; nonfinite output; sample/node cap breach; invariant or replay/restart failure; wall time ≥15 minutes; monitored working set ≥2 GiB; output >512 MiB; or any canonical publication attempt. After explicit authorization and successful run, verify all manifest-listed files and hashes, finite values, numerical invariants, replay/restart, sample continuity/endpoints, and no canonical mutation. Report execution duration and observed resources without upgrading engineering-model behavior to scientific authority.

## Gates and prohibitions

Preserve `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. No run before authorization; no Fair, MPI, ShellSet, Solver, DGBSV, factorization, rift pair 1:3, canonical event/T1/T2, or WORLD_HISTORY access/write.
