# R4.4

Run after the final SEALED R4.3 result is present in `outputs/v0_6D1_R4_3*`.

```powershell
.\run_v0_6D1_R4_4.ps1
```

R4.4 is an adjudication-only stage. It does not rerun NEMO, Geonomics, Madingley, RangeShiftR, CDMetaPOP or SLiM, and it never writes canonical ARCANA state.

Primary outputs:
- `outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json`
- `outputs/v0_6D1_R4_4/R4_4_ADJUDICATION_SUMMARY.json`
- `outputs/v0_6D1_R4_4/R4_4_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_4_SEAL/R4_4_FINAL_SEAL_AUDIT.json`
