# ARCANA WorldSim v0.6D1-R0 — Historical Artifact Recovery Audit

Status: `PASS_RECOVERY_AUDIT_WITH_PARTIAL_RAW_SURVIVAL_AND_EXECUTABLE_HISTORY_STILL_MISSING`

This package extends v0.6D1 with an evidence-preserving recovery audit and a local archive scanner. It does **not** reconstruct D1/D2/D2.2 from summaries and does not authorize the 210->0 Ma Deep-coupled replay.

Key files:

- `HISTORICAL_ARTIFACT_RECOVERY_AUDIT_v0_6D1_R0.md`
- `RECOVERY_MATRIX_v0_6D1_R0.json`
- `V0_6D1_R0_STATUS.md`
- `scripts/scan_arcana_historical_artifacts.py`
- `scan_v0_6D1_R0_windows.ps1`
- `outputs/CURRENT_SESSION_RECOVERY_SCAN_v0_6D1_R0.json`
- `NEXT_STAGE_HANDOFF_v0_6D1_R0.md`

Example Windows scan:

```powershell
.\scan_v0_6D1_R0_windows.ps1 -Roots `
  "F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld", `
  "$HOME\Downloads"
```

Only exact SHA-256 matches restore package identity. A RAW or filename match is never silently promoted to executable authority.
