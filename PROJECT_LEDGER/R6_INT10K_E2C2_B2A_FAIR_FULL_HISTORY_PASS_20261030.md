# ARCANA R6 — E2-C2-B2-A FAIR complete original history integrity and event/Unified coverage PASS

Date: 2026-10-30. **Source:** operator-pasted stdout from FAIR after executing the SHA-pinned B2-A verifier. **Decision:** `E2C2_B2A=PASS_FULL_HISTORY_SHA_AND_EVENT_UNIFIED_COVERAGE`, scoped to the immutable **noncanonical 3×3 synthetic 1000Y history**. This does not establish the correctness of physical models or authorize canon production.

## Exact binary identity and test provenance

- FAIR checked script SHA256 `ac53f0d004bcda04dae6c78bb8aaa4c9e771759ba9c781a140e85684a09293dd` for `arcana_e2c2_b2a_full_history_event_unified_audit.py`.
- `E2C2_B2A_SYNTHETIC_SELFTEST=PASS` on a separate 13-row mock fixture, with intentional negative corruption / event mismatch / temporal forgery tests handled as expected. Mock output prefixed `E2C2_B2A_TEST_` and `_TEST_NEG_` must **not** be mistaken for the real 61001-row result.
- Original `MANIFEST.json` SHA256 pin `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`; `E2C2_B2A_MANIFEST_INDEX=SHA256_AND_OFFSETS_PASS`; original 61,001 indexed rows and original `HISTORY.jsonl` entire raw SHA256 passed against its manifest member.
- Physical original history `HISTORY.jsonl` 1,916,080,917 bytes, used read-only. No source patch/commit, archive rewrite, WorldSim numerical rerun or separate persistent history created.

## FAIR actual output

```text
E2C2_B2A_INDEX_RECORDS= 61001
E2C2_B2A_MODE=FULL_ORIGINAL_HISTORY_STREAM_SHA_AND_TYPED_ENVELOPE_AUDIT
E2C2_B2A_ORIGINAL_HISTORY_FULL_SHA256=PASS
E2C2_B2A_UNIFIED_DEEP_ENVELOPES_SHA256=PASS 1000
E2C2_B2A_EXTERNAL_EVENT_ENVELOPES_SHA256=PASS 58000
E2C2_B2A_YEAR_RECORD_EXTERNAL_EVENT_MULTISET=EXACT_PASS 1000
E2C2_B2A_EVENT_TIME_FIELD_CENSUS= {'DATED_TIME_YEAR': 50000, 'NULL_TIME_YEAR': 8000}
E2C2_B2A_NULL_EVENT_KINDS= {'HYDRAULIC_DIAGNOSTIC': 8000}
E2C2_B2A_ALL_EVENT_KINDS= {'BEDROCK_EROSION': 8000, 'DEPOSITION': 11000, 'HYDRAULIC_DIAGNOSTIC': 8000, 'SEDIMENT_EXPORT': 8000, 'TRANSPORT': 14000, 'WATER_ROUTING': 9000}
E2C2_B2A_CONTEXT_DATED_COUNTS_UNIQUE= [50]
E2C2_B2A_CONTEXT_NULL_COUNTS_UNIQUE= [8]
E2C2_B2A_NULL_YEARS_RETAINED_AS_NULL=PASS
E2C2_B2A=PASS_FULL_HISTORY_SHA_AND_EVENT_UNIFIED_COVERAGE
```

All six event-kind counts total exactly 58,000, with 50 dated and 8 index-null-time event envelopes per annual emission interval in this fixture. **Important:** `time_year=null` is part of the original external envelope and is *not* a license to assign a physical year; `HYDRAULIC_DIAGNOSTIC` can retain an annual grouping as separate context only. Annual multiset checks prove per-year payload membership, **not** all internal event causal ordering by themselves. Use the original global index `sequence` and per-kind external ordering as authority.

## Combined A3 → B1 → B2-A engineering conclusion

- A3 proved `REGIONAL_SNAPSHOT` deposit lists append-only on every one of 1000 year transitions, and 11,000 inserted deposits match nested DEPOSITION events; all 1001 regional snapshots and 1000 regional year records per-payload hashes PASS.
- B1 V2 proved every one of 1001 regional snapshot JSON canonical payloads can be reproduced **byte-for-byte** from Y0 anchor + exact changed fields + 11k full nine-field appended deposit objects; virtual encoding 9,055,299 bytes vs original 1,774,346,125 bytes regional snapshot **payloads** only (0.005103 ratio, 99.4897% smaller snapshot-only virtual encoding). Not on-disk archive benchmark; no query/read-view overhead, no standalone event/Unified retention represented in this ratio.
- B2-A completed *original-source integrity* coverage: full HISTORY raw file SHA, all 1000 `UNIFIED_STEP` Deep/thermal/mechanics/hydrology envelopes and all 58k standalone events SHA, exact annual event multiset with 8k null timestamps preserved.
- These results **authorize B2-B schema and contract work**, **not a claim of a new persistent lossless history store**; no B0 archive written and no physical simulation run or scientific authority earned.

## Upcoming B2-B review invariants

- Preserve global `sequence` 0..61000 of original records; exact original kind, external `time_year` value including JSON null, payload SHA256, event kind, payload JSON and annual emission interval. Do not collapse event duplicates without reversible identity and position.
- `UNIFIED_STEP` carries actual Deep inventory and source/transfer/balance fields: preserve full JSON values and original SHA; do not fold it into water/geo-only deltas.
- B0 `HistoryStore.append_transaction` accepts only typed envelopes and atomically switches committed read views. Existing `HistoryQueryService.event_at` sorts by `record_id`, not original global `sequence`—a future adapter must explicitly provide order-by-original-sequence. Record parent-view growth and store-size overhead must be benchmarked; do not extrapolate the B1 99.49% snapshot ratio to the whole history.
- Proposed next phase: source-pinned nonwriting typed-record contract/preflight; then isolated scratch store + negative transaction and exact historical query proofs only after explicit design acceptance.

**Authority:** `E2C1_QUALIFIED_SYNTHETIC_SCOPE=PASS`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`. FAIR source commit `2c71370eb9a959c78121ce1c88ec8e9e37187787` remains local, not confirmed pushed. Docs GitHub branch separate.
