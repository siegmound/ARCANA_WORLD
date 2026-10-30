# ARCANA R6 E2-C2-A2 FAIR authenticated samples PASS; A3 exhaustive append-only proof prepared

**Date:** 2026-10-30. Evidence: FAIR operator-pasted stdout, matching the earlier SHA-pinned E2-C2-A2 script. **A2 result** `E2C2_A2=PASS_AUTHENTICATED_TARGETED_HISTORY_SAMPLES`. **A3:** local mock/safety tests PASS, **NOT YET RUN on FAIR**. No 1000Y solver rerun, source commit, archive mutation or scientific authorization.

## A2 verified original archive identity and sample coverage

- Original script SHA256 verified by FAIR: `b4a16a1fb52038d74444cadec8034410444dcc174446cbe65005bf57d3b64141`.
- `E2C2_A2_MANIFEST_INDEX=SHA256_AND_OFFSETS_PASS`; full `INDEX.jsonl` SHA256, 61,001 rows, all indexed offsets, expected kinds and original `HISTORY.jsonl` length 1,916,080,917 bytes verified. **No full 1.916GB HISTORY digest recomputation** by A2.
- Read and checked exact payload SHA256 and canonical bytes of **40** record envelopes at selected years `[0,1,2,99,100,101,499,500,501,749,750,751,999,1000]`. All 9 ordered stable cell IDs `SYNTHETIC_BASIN_3X3:C00..C08`. Snapshot has keys `cells,time_year`; cell fieldset of 25 keys pinned by A2. Source classification synthetic/noncanonical.

## Deposit field identities and sampled growth

Nine deposit fields (all present in examined deposits): `density_kg_m3,deposition_time_year,destination_cell_id,erosion_time_year,event_id,mass_kg,material_id,source_cell_id,transport_time_year`. No duplicated `event_id` or wrong fieldsets in the selected anchor snapshots.

| Archived year | Snapshot bytes | Number of deposits | Per-cell deposit counts |
|---:|---:|---:|---|
| 0 | 7,908 | 0 | 0,0,0,0,0,0,0,0,0 |
| 1 | 13,081 | 11 | 0,1,1,0,1,2,0,2,4 |
| 100 | 358,420 | 1,100 | 0,100,100,0,100,200,0,200,400 |
| 500 | 1,772,536 | 5,500 | 0,500,500,0,500,1000,0,1000,2000 |
| 750 | 2,656,326 | 8,250 | 0,750,750,0,750,1500,0,1500,3000 |
| 1000 | 3,540,152 | 11,000 | 0,1000,1000,0,1000,2000,0,2000,4000 |

All **nine sampled adjacent transitions** `0→1,1→2,99→100,100→101,499→500,500→501,749→750,750→751,999→1000`: `DEPOSIT_PREFIX_UNCHANGED=True`, `NEW_DEPOSITS=11`. These are positive *samples*, not proof for unobserved 991 adjacent transitions. Non-deposit changing fields include bedrock and surface elevation, cumulative eroded/exported/deposited mass, substrate and its thickness, mobile/suspended material, per-cell flow accounting; these must remain in historical state projection.

## Other historical fields and a significant temporal-index caveat

- Sampled `UNIFIED_STEP` includes `deep, elapsed_years, material_flows, material_volumes, mechanics, step, surface_hydrology, thermal, time_end_s, time_start_s`; Deep contains inventory, geological source, loss, transport, modal response and fluxes. These must not be discarded or treated as inferred physics.
- Sampled `REGIONAL_YEAR_RECORD` contains water/solid balances, drainage, geologic load, depression storage, `events` and time_year. **Nested events=58** in each sampled annual record, whereas A2's index per-year count filtered to `REGIONAL_EVENT` rows **with a non-null time_year** is **50** per sampled year. This does **not prove 8 events absent**; in this writer some event payloads are undated at the external envelope level. A3 will inventory index null-time vs dated events; future typed archival adapter must bind those events to the appropriate annual/causal context without silently assigning invented time semantics, losing ordering or double-counting the nested and externally emitted representations.
- DEPOSITION events do **not** include all 9 full deposit fields and cannot alone reconstruct the deposit objects; maintain exact supplemental deposit deltas and per-cell append ordinal. UNKNOWN statuses must be retained, not changed into fabricated data.

## A3 read-only exhaustive validation — prepared, not executed on FAIR

- Python `arcana_e2c2_a3_all_year_deposit_proof.py`, SHA256 **`388d1731a8891bc9c2d17df05a172e825c3947c6c2ef6c8d642dcb8c210faeb0`**. ZIP `ARCANA_E2C2_A3_READONLY_FAIR_PACKAGE.zip`, SHA256 `af4483a922da708e3b90d9ee274ec64115a886e916fef8cbdc7289c546234e6e`. Both in conversation attachment container only; **not uploaded to FAIR or repository**. README included.
- Python syntax and positive/negative data-model selftests PASS. A mock end-to-end execution on separately generated **synthetic 61,001-index-row, 1001-snapshot 12.1MB archive** PASS, including 8,000 external index null-time events. These local tests do not certify FAIR original.
- FAIR operator checks script SHA, optionally runs `--self-test`, then default execution. Script reads pinned original MANIFEST, rehashes INDEX, checks all offsets and coverage, **reads and verifies canonical bytes + payload SHA of all 1,001 REGIONAL_SNAPSHOT and all 1,000 REGIONAL_YEAR_RECORD**. For each of 1,000 annual transitions it checks 9 cell order, exact prefix equality of old deposits, unique event_id, 9-key schema, cell/time references, and exact multiset match of newly appended deposits with nested annual DEPOSITION events for overlapping event fields. Prints changing non-deposit field counts and dated-vs-undated external event index census. Fail-closed on any mismatch.
- A3 is intentionally a ~1.8GB snapshot read/JSON re-encode + annual record scan; not a full HISTORY SHA check and **does not** independently SHA-rehash 58,000 standalone REGIONAL_EVENT or 1,000 UNIFIED_STEP records. It never writes an archive, creates a HistoryStore or runs WorldSim physics. New result only when actual FAIR command returns `E2C2_A3=PASS_EXHAUSTIVE_DEPOSIT_APPEND_ONLY_AND_EVENT_PARITY`. On BLOCKED diagnose; no patch stacking.
- After A3 PASS, freeze only the *synthetic* deposit invariant. Next E2-C2-B must define typed B0 HistoryStore lossless append deltas plus non-deposit state projections, UNIFIED_STEP/Deep/temporal provenance, exact by-year reconstruction and no silent UNKNOWN inference. Query and scientific/production permissions remain closed.

**Authority flags:** `E2C1_QUALIFIED_SYNTHETIC_SCOPE=PASS`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
