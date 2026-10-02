# B3 governed T0 read-only ingest evidence

Decision: `PASS_B3_GOVERNED_T0_READ_ONLY_INGEST`.

This package records the real T0 reference-only ingest qualification. The
runner validated source identities, published 14 semantic state records plus
one provenance record atomically, destroyed and reopened the temporary store,
ran exact state/history/WHY and support-boundary queries, accounted only the
WORLD_HISTORY store, and compared all source hashes before and after.

Run from the repository root on a checkout with the governed external payloads
available:

```powershell
$env:PYTHONPATH = 'src'
python scripts/r6_world_history_b3_t0_read_only_ingest.py `
  --repository-root . `
  --output-dir outputs/r6_world_history_b3_t0_ingest `
  --work-root outputs/r6_world_history_b3_t0_ingest/.work
```

`B3_T0_AUTHORITY_INVENTORY.json` lists exact source artifacts, their roles and
verified hashes. `B3_T0_STATE_INVENTORY.json` records state IDs, authority,
support and payload references. `B3_T0_RETENTION_MAP.json` preserves the
explicit review-required items. `B3_T0_ACCOUNTING.json` separates store-owned
metadata from external payload references. `B3_SOURCE_IMMUTABILITY.json`
contains per-source before/after SHA-256 evidence. No governed source payload
is copied into this directory.

This is a read-only integration qualification. It does not authorize dt, T1,
mechanics, forward evolution or authority promotion. The next stage is B4
first temporal adapter design and qualification only.
