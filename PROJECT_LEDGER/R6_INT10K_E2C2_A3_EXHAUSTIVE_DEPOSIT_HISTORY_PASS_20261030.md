# E2-C2-A3 — exhaustive 1001 snapshot deposit append-only audit PASS

2026-10-30. FAIR operator terminal result; script SHA256 exactly `388d1731a8891bc9c2d17df05a172e825c3947c6c2ef6c8d642dcb8c210faeb0`.

**Decision:** `E2C2_A3=PASS_EXHAUSTIVE_DEPOSIT_APPEND_ONLY_AND_EVENT_PARITY` within the **original noncanonical synthetic 3x3 1000-year archive**. This seals the append-only property for that archive, **not for future physical worlds or biological/civilizational histories**. No WorldSim solver rerun or source change.

## Independent provenance and completeness

- `E2C2_A3_SYNTHETIC_SELFTEST=PASS`; original manifest and INDEX SHA256 PASS.
- INDEX counts: REGIONAL_SNAPSHOT=1001, REGIONAL_YEAR_RECORD=1000, UNIFIED_STEP=1000, REGIONAL_EVENT=58000.
- External regional events: 50000 indexed `DATED_TIME_YEAR`, **8000** indexed `NULL_TIME_YEAR`. Null timestamp does not imply missing event and must not be filled with invented time.
- All **1001 snapshots** and **1000 regional annual records** read at authenticated offsets, canonical payload hash checked. All **1000 adjacent transitions** exhaustively checked across nine ordered cells: old deposit prefix byte-equivalent at JSON value level, no mutation/reorder/removal, **11000 new complete deposit objects** with unique event_id and nine required keys, exactly matched to 11000 **nested** annual DEPOSITION events via shared fields.
- At Y0/Y1/Y100/Y500/Y750/Y1000 deposit counts 0/11/1100/5500/8250/11000, respectively; per-cell final counts 0,1000,1000,0,1000,2000,0,2000,4000.
- `E2C2_A3_AUTHENTICATED_SNAPSHOT_BYTES=1774502989`; `E2C2_A3_AUTHENTICATED_YEAR_RECORD_BYTES=28217835`; source `HISTORY.jsonl` total 1916080917 bytes.
- The reported nondeposit-field changes across 1000 transitions: `bedrock_elevation_m=8000`, `cumulative_deposited_kg=6000`, `cumulative_eroded_kg=8000`, `cumulative_exported_kg=3000`, `elevation_m=9000`, `internal_material_in_kg=6000`, `internal_material_out_kg=8000`, `mobile_kg_by_material=8000`, `substrate=8000`, `substrate_thickness_m=8000`, `suspended_kg_by_material=6`. All must be preserved for lossless regional historical state.
- A3 explicitly printed `E2C2_A3_HISTORY_FULL_SHA_REHASH=NOT_PERFORMED` and `E2C2_A3_UNIFIED_AND_EVENT_ENVELOPES=NOT_FULLY_REHASHED`. Do NOT claim global 1.916GB history SHA or all-domain archive integrity from A3 alone.

## Authority and next gate

- Source on FAIR remains local branch `r6/e2c1-frontier-projection-r1-fair`, commit `2c71370eb9a959c78121ce1c88ec8e9e37187787` (not confirmed pushed), unrelated to docs branch.
- Original 1000Y MANIFEST pin `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`; original inputs/evidence must stay immutable.
- **E2-C2-B1** is a distinct, read-only *virtual delta + full regional snapshot reconstruction* proof. It must SHA-verify every derived Y0..1000 original snapshot from compact year0 anchor + appended deposits + exact changed nondeposit fields before any B0 HistoryStore integration. Even an exact B1 PASS is *not* an external-event, Unified Deep, or all-domain retention PASS.
- Then E2-C2-B2/C design typed annual `HistoryStore.append_transaction` envelopes with immutable committed views, historical queries, provenance and UNKNOWN semantics, and 8000 null-year events preserved in original sequence. No production write or solver run authorized.

Authorities stay false: `WORLD_HISTORY_PRODUCTION_AUTHORIZED`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED`, `F2B_SOLVER_EXECUTION_AUTHORIZED`, `ARCANA_SI1_MECHANICS_QUALIFIED`.
