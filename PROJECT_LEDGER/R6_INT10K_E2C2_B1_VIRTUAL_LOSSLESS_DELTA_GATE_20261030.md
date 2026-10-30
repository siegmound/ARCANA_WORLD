# E2-C2-B1 — Virtual lossless regional snapshot delta representation; FAIR gate PREPARED

Date 2026-10-30. Based on read-only exhaustive E2-C2-A3 PASS. B1 **has not run on FAIR** and creates **no persistent archive**. It is an authenticated in-memory reconstruction test, not a new physical model or B0 HistoryStore implementation.

## Pinned source

- Test program `arcana_e2c2_b1_virtual_delta_reconstruction.py`, SHA256 `12a669a5193f5945c3174ede7a6d7ca5bdf9837a8121a1ab59c9fccce17dfbb9`; ZIP `ARCANA_E2C2_B1_READONLY_FAIR_PACKAGE.zip`, SHA256 `71a205f7b3fead9685a764349ffa71ec4aae18149f2e28b27fa11af917d0acdd`. Both prepared in current chat container, not on FAIR. Python syntax and locally run synthetic positive/negative selftests PASS; no FAIR benchmark claims.
- This runner imports SHA-pinned `arcana_e2c2_a3_all_year_deposit_proof.py` from same FAIR operator directory, SHA256 `388d1731a8891bc9c2d17df05a172e825c3947c6c2ef6c8d642dcb8c210faeb0` to reuse existing original-index verification, canonical encoding, exact authenticated payload reader and deposit/event invariants. Disables Python bytecode emission during import.
- On FAIR, user should transfer the B1 script to `~/HPC-POMDP/Arcana`, verify its SHA256, run `python arcana_e2c2_b1_virtual_delta_reconstruction.py --self-test` then `python arcana_e2c2_b1_virtual_delta_reconstruction.py`. This is standalone Python, no WorldSim Conda dependency, does not write to source checkout or original evidence.

## Exact experimental grammar (virtual, not yet accepted production schema)

- Year-0 full authenticated regional snapshot is the **anchor**; every year Y>0 has `{schema, time_year, parent_snapshot_sha256, snapshot_sha256, cells:[{cell_id,set:{changed-non-deposit-field:exact-new-value},append_deposits:[complete-9-field-deposit,...]},...]}`.
- Change detection compares all cell fields excluding `cell_id,deposits` and retains complete values (not rounded numeric differences); new deposit append lists preserve cell-local order and exact event_id/density/provenance and timestamps. The independently reconstructed year state maintains previous fields and appends full deposit objects. No original snapshot object is used as reconstructed future state after Y0.
- For *all 1001 years*, B1 checks canonical reconstructed payload bytes **and** SHA256 equal the original authenticated `REGIONAL_SNAPSHOT` payload. For all 1000 years >0, it reauthenticates `REGIONAL_YEAR_RECORD` and checks the complete new-deposit multiset matches nested annual `DEPOSITION` event shared fields. Required 11000 unique deposit IDs; nine unchanged ordered cells; existing deposit prefix append-only.
- The per-year delta is currently a *prototype JSON grammar*, NOT a validated B0 `TemporalRecord`, `DomainStateEnvelope` or transaction. Delta chain SHA is computed only in memory.
- B1 reports original snapshot envelope bytes, original canonical snapshot payload bytes, encoded year0 anchor+delta bytes (including parent/current SHA metadata), snapshot-only size ratio, per-field update frequency and delta hash chain; ratio **excludes** 58000 standalone events, 1000 unified steps, 1000 annual records, B0 store metadata, index, separate anchors and retention/replay overhead. No total archive compression/performance claim is allowed.

## Future explicit gaps

- All 8000 externally indexed events whose `time_year` is null must remain in exact sequence; preserve distinction between external envelope time and contextual grouping; no silent date assignment. Externally indexed event and Unified Deep payload SHA full census are not in scope for B1.
- Query/history and refinement require all geology, water, material, resource, deep state, input/provider provenance, UNKNOWN/NOT_APPLICABLE/OUTSIDE_SCOPE where known. The 3x3 fixture does not contain complete flora/fauna/human histories and must not be represented as though it does.
- After **actual FAIR B1 PASS**, independently review output and qualify only lossless snapshot grammar for this synthetic fixture. B2 must bind typed records to `HistoryStore.append_transaction`, committed `read_view`, `MinimalStateContract`, provenance and query/replay/refinement, negative corruption, and immutable source aliases. No push, source patch or production writing before independent contract acceptance.

Expected marker after execution only: `E2C2_B1=PASS_EXACT_VIRTUAL_REGIONAL_SNAPSHOT_DELTA_RECONSTRUCTION`. Failure requires diagnosing without patch stacking. All scientific and production authority gates remain false.
