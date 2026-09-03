# R3.20-R1 seal-count hotfix

Scope: audit plumbing only.

- Changes the R3.20 candidate formal-audit expectation in `run_v0_6D1_R3_20_sealed_checks.ps1` from stale `51/51` to authoritative `57/57`.
- Updates `R320_SEAL_GATE_PATCH_MANIFEST.json` with the new runner SHA256.
- No scientific parameters, CHA-2/C1 code, hazard equations, R3.19 biology, or sealed-audit logic are changed.

After overlay, rerun:

```powershell
.\verify_v0_6D1_R3_20_seal_gate_patch.ps1
.\run_v0_6D1_R3_20_sealed_checks.ps1
```
