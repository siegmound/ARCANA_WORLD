# ARCANA WorldSim v0.6D1-R4.35-R1
## Live Seed Ledger & Spatial Schema Diagnostic

Diagnostic-only overlay for the live R4.35 BLOCKED result.

It does not modify R4.35 source, R4.3, R4.23, R4.30, R4.31, any canonical
artifact, any target, any selector, or any engine configuration.

It reports only the exact live schemas needed for a targeted repair:

1. `outputs/v0_6D1_R4_3/R4_3_SEED_LEDGER.json`
   - top-level schema
   - all scalar fields whose key contains `seed`
   - per-job seed fields, especially J14/J18/J21
2. the nine non-terminal R4.35 authority-gap records
3. J14/J18 R4.33 runtime binding packages
4. exact source NPZ array names/shapes/dtypes and small axis/name values
5. R4.30/R4.31 J14 authority metadata
6. R4.23 J18 frozen LANDSCAPE_PROFILE translation
7. R3.28 high-resolution spatial authority metadata
8. J21 duplicate `anchor_age_ka` equality check

Governance:
- no external engine execution
- no target numeric execution
- no readjudication
- no canonical state change
- no gate weakening
- failed R4.35 evidence preserved

Run:
    .\run_v0_6D1_R4_35_R1_live_schema_diagnostic.ps1

Report:
    outputs\v0_6D1_R4_35_R1\
      R4_35_R1_LIVE_SEED_AND_SPATIAL_SCHEMA_DIAGNOSTIC.json
