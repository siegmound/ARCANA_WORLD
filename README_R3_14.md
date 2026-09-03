# ARCANA World 1 — v0.6D1-R3.14

R3.14 binds the already-existing late-Cenozoic environmental stack to the SEALED R3.13 30 Ma boundary and rebuilds the production C2 adaptive clock. It is intentionally **not** a 30→0 biological run.

## First

```powershell
.\run_v0_6D1_R3_14_checks.ps1
```

Expected candidate regression: `18 passed`.

## Bind/recover

```powershell
.\run_v0_6D1_R3_14_late_cenozoic_binding.ps1
```

By default the runner searches the current package folder plus its parent ArcanaWorld/Arcana folders. It can inspect historical ZIPs without extracting them first.

If your archive is elsewhere:

```powershell
.\run_v0_6D1_R3_14_late_cenozoic_binding.ps1 -SearchRoot "F:\path\to\archive"
```

### Successful outcome

`PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__BIOLOGY_REPLAY_NOT_STARTED`

Artifacts are written under:

`local_bindings\v0_6D1_R3_14\`

including the rehydrated minimal v0.6.1 root, B1/B2 materialized boundaries, adaptive-clock JSON, and binding summary.

### Blocked outcome

`BLOCKED_R314_EXACT_V061_SEALED_PAYLOAD_NOT_FOUND`

This does not invalidate R3.13. It means only that the exact historical environmental bytes were not found in the scanned locations. See:

`local_bindings\v0_6D1_R3_14\R3_14_BINDING_BLOCKER_REPORT.json`

Do not replace the missing payload with a proxy.
