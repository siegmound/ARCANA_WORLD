# ARCANA R6 E2-C2-B1 V1 API mismatch (BLOCKED); V2 recovery script prepared

**Date** 2026-10-30. Provenance: FAIR operator terminal stdout, direct inspection of exact archived local A3/B1 scripts, and local verification of a V2 **test script, not a FAIR run**.

## Incident and adjudication

- Original B1 V1 SHA256 **`12a669a5193f5945c3174ede7a6d7ca5bdf9837a8121a1ab59c9fccce17dfbb9`** confirmed on FAIR.
- V1 `E2C2_B1_SYNTHETIC_SELFTEST=PASS` but full `verified_run()` aborted on line 98 at `a3.original_index()` with `TypeError: original_index() missing 1 required positional argument: 'root'`. Final marker `E2C2_B1=BLOCKED:TypeError:...`.
- The SHA-pinned A3 module defines `original_index(root: Path, pin: str=PIN)` and constants `ROOT`, `PIN`. V1 expected a zero-arg API. Execution failed before its historical index loader opened any original history; this is a **test runner API error**, not a failure of lossless delta reconstruction.
- A3 operator exhaustive PASS remains unchanged: all original 1001 snapshots and 1000 annual records authenticated; 1000 transitions retained deposit prefix and added 11000 new deposit objects matched to DEPOSITION annual events. No source or archive modifications are authorized.

## Corrected V2; content integrity

- **V2 script**: `arcana_e2c2_b1_virtual_delta_reconstruction_v2.py` SHA256 **`fc86a84c46339781c1e1f135728644261f7664b0223757e8a26aa0a8a56aaa1f`**.
- **ZIP package**: `ARCANA_E2C2_B1_V2_FAIR_PACKAGE.zip` SHA256 **`84c7b45ffde8cfde9aff7dbe9997816b86b19d81ea35fe3d82a3917412d742b5`**. README SHA256 `3ec9980ad11f7c357f406cb31c13f721b58e02ff218e1546dc902e9627b3592f`. Artifacts produced in chat file runtime, not transferred or run on FAIR.
- Source correction: `a3.original_index()` -> `a3.original_index(a3.ROOT, a3.PIN)`. Selftest additionally verifies via `inspect.signature(...).bind(a3.ROOT,a3.PIN)` and presence of actual required A3 functions. No changes to index record grammar, physics, delta construction, snapshot hash parity, 1001-year loop, 11000 deposit acceptance, original archive, A3 file or B0 HistoryStore.
- Local checks: V2 Python compile PASS; V2 `--self-test` PASS against actual SHA-pinned A3 source; bounded **3-year synthetic end-to-end** test PASS with real A3 canonical encoder, authenticated payload reader, inspect_transition and deposition-event matching, including explicit check original_index receives root and pin. The bounded synthetic test used a test-only in-memory copy with the 1001-year loop/counts reduced; those changes are **not included** in V2. ZIP member bytes and integrity validated.

## Next FAIR operator action

```bash
cd ~/HPC-POMDP/Arcana
sha256sum arcana_e2c2_b1_virtual_delta_reconstruction_v2.py
sha256sum arcana_e2c2_a3_all_year_deposit_proof.py
python arcana_e2c2_b1_virtual_delta_reconstruction_v2.py --self-test
python arcana_e2c2_b1_virtual_delta_reconstruction_v2.py
```

Expected SHA for A3 **unchanged**: `388d1731a8891bc9c2d17df05a172e825c3947c6c2ef6c8d642dcb8c210faeb0`. Keep B1 V1 for forensic provenance, no source patch, numerical rerun, push/merge or original evidence writes. The V2 full FAIR result is **PENDING**: no claim of `E2C2_B1=PASS_EXACT_VIRTUAL_REGIONAL_SNAPSHOT_DELTA_RECONSTRUCTION` until operator stdout supports it.

Any B1 success only qualifies **virtual regional snapshot lossless delta** and snapshot-only byte ratio for the original 3×3 synthetic 1000Y fixture; full 58000 external events, 1000 UNIFIED Deep steps, B0 typed HistoryStore, retention/query/replay/refinement and archival efficiency remain separate gates. The 8000 external null-time-year events must remain untouched and non-fabricated.

**Authority flags**: `E2C1_QUALIFIED_SYNTHETIC_SCOPE=PASS`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`.
