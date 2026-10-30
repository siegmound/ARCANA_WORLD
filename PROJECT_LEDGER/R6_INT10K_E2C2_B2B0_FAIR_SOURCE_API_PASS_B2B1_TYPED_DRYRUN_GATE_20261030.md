# ARCANA R6 — E2-C2-B2-B0 FAIR source API PASS, B2-B1 typed-record dry-run prepared

Date 2026-10-30. Source: actual FAIR operator stdout. **B2-B0=PASS**; B2-B1 **PREPARED_NOT_RUN_FAIR**.

## B2-B0 FAIR validated immutable source/contract

- Source script SHA256 operator verified `609aec03aa7c0c82ba2f56b21d3247089a7d44a1f3c102b4660ee337d8fa456b`; `E2C2_B2B0_SYNTHETIC_AST_SELFTEST=PASS`; `E2C2_B2B0_SOURCE_AND_ORACLE=PINNED_AND_UNCHANGED`, `E2C2_B2B0_STORE_WRITES=NOT_PERFORMED`, `E2C2_B2B0=PASS_READ_ONLY_TYPED_HISTORYSTORE_API_PREFLIGHT`.
- FAIR source HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`, parent `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`, clean local branch `r6/e2c1-frontier-projection-r1-fair`. Still **not confirmed pushed to GitHub**.
- Exact original 1000Y manifest `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`, unchanged.
- Accepted `HistoryStore.append_transaction` typed inputs verified statically: `CheckpointEnvelope,DomainStateEnvelope,EventRecord,ForcingRecord,ProvenanceRecord,RefinementBranchEnvelope,RefinementReconstructionRecipe,ReplayRecipe,TemporalRecord`.
- Verified `expected_parent_view_id` conflict check, atomic committed-read-view source API and explicit `DomainStateEnvelope` support/authority, `EventRecord` temporal/spatial/causal API. Native `HistoryQueryService.event_at` sorts by typed **record_id** rather than source `sequence`; event order adapter is mandatory. Full-member read-view manifest cost must be benchmarked, not assumed negligible.
- The API preflight is **source inspection**, not runtime transaction crash/visibility testing. It did not create HistoryStore or write any files.

### Pinned source-module sha256 (operator output)

```json
{
"checkpoint.py":"42e1de1ee05a471e05d1015337048e4f541f5e5814063c82897a8c6ac1302c4c",
"identity.py":"939df5f45717d60261df7b97ce9beef1a0904eedec5edde23bfb2f644ca50c18",
"query.py":"ee926a1e92945ffcf33ea860bfff760242210f62049c71637209ef1391540838",
"retention.py":"c9e67e39a5651f9e820e80c1db0773ac7164aa6d1772bddc4a55c0c164a3e0b6",
"state.py":"cc442d885db4728a999387d0c0125f00babd6bbb57a5fb7304e9c0276597b395",
"store.py":"d8da8fdd7e3444e787cf273f653aa2d85d2431ac3a20fb8f592aec378645505c",
"temporal.py":"60813102e9d5d55af8e71aad5e138110ee7d12fb10c63037dd7338372a3aa0f3"
}
```

## Important additional source constraint

`HistoryStore._transaction_record` accepts objects inheriting `TemporalRecord`, but the downstream `temporal_record_from_dict` dispatch table registers explicit subclasses such as `HistoricalSnapshot`, not the bare base `TemporalRecord` ROLE. Candidate typed annual bundles must use a **registered validated subclass** or undergo a deliberately separate API/schema review. B2-B1 uses `HistoricalSnapshot` for its experimental historical year/Unified/event-bundle carriers and never claims it is the final production schema.

## B2-B1 sampled typed dry-run prepared, not yet run on FAIR

- New script `arcana_e2c2_b2b1_typed_dryrun_no_store.py` SHA256 `539e18d5e8403e1f61525749afa6e0ab1c3b082efc1d94c5664e54d4667ce2ab`. README `ARCANA_E2C2_B2B1_README.md` SHA256 `3e4afaa145ba2c9b831c6596e9db3a04048382e420bc15b9a338fde0cda46ff6`. ZIP `ARCANA_E2C2_B2B1_FAIR_PACKAGE.zip` SHA256 `7193765d58bab00ca043d7e1052c86159b55fbeae9553418a2a31424da7760fe`.
- In this conversation runtime, `py_compile` PASS, pure negative tests PASS (NULL timestamp replaced, explicit date changed, duplicate/out-of-order global source sequence, removed deposit prefix), ZIP `testzip` PASS, script bytes verified. **Actual engine-typed constructors and original FAIR indexed records have not been tested in this session**, so no B2-B1 qualification is claimed.
- In FAIR full mode, pin local source Git and seven module SHAs; import actual B0 classes and SHA-pinned original B2-A indexed-envelope reader; run static `HistoryStore._transaction_record` on actual `EventRecord` (174 sampled standalone events, 58 each for years 1/2/10), on `HistoricalSnapshot` candidates containing original `UNIFIED_STEP` and `REGIONAL_YEAR_RECORD` payload, and on in-memory `DomainStateEnvelope` for year0 anchor, years1/2 exact changed-field+full deposit deltas and year10 source-hash reference only. For event bundles also test 3 annual ordered `HistoricalSnapshot` candidates; alternatives not additive requirements.
- Every source payload in the sampled years and y0 snapshot is independently checked against the pinned index by canonical JSON bytes, sequence, original time and `payload_sha256`. Null time of 8 `HYDRAULIC_DIAGNOSTIC` per sampled year remains null; source event order retained by `source_sequence`, not native `event_at`. B0 serializer IDs, hashes, reparse, no duplicate bucket/key, mutation negative checks. No `HistoryStore()` initialization, no disk writes, physical simulation or persistent archive.
- Execute on FAIR:
```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate arcana-r6-linux
cd ~/HPC-POMDP/Arcana
sha256sum arcana_e2c2_b2b1_typed_dryrun_no_store.py
sha256sum arcana_e2c2_b2a_full_history_event_unified_audit.py
python -B arcana_e2c2_b2b1_typed_dryrun_no_store.py --self-test
python -B arcana_e2c2_b2b1_typed_dryrun_no_store.py
```
- Expected only after actual run: `E2C2_B2B1=PASS_TYPED_SOURCE_ENVELOPE_DRYRUN_SAMPLED_YEARS`. If BLOCKED, diagnose first, do not patch scientific source or archive.
- B2-B1 is a bounded *sample type-schema* gate, not full 61k reingestion or real atomic writes. Following B2-B1 is separately reviewed scratch 3Y/10Y store and atomic-view/size benchmark; no production-store authority and no scientific/canon permissions.

Previous A3, B1 and B2-A PASS remain intact. Their noncanonical scope does not itself qualify biological/faunal/human histories, though later WorldSim history must retain such data wherever supported and maintain UNKNOWN elsewhere. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
