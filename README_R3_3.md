# ARCANA WorldSim v0.6D1-R3.3

Persistent Deme Reconnection / Coalescence & Long-Horizon Fragmentation Homeostasis candidate.

This stage repairs the asymmetric deme lifecycle exposed by the R3.2 long run. R3.2 had a fission operator but no reverse demographic coalescence, so component count followed `initial + all fissions` exactly. R3.3 adds a governed same-species-only remerger after persistent secondary contact, without adding a random merge rate or de-speciation mechanism.

Key files:
- `src/rebased_natural_control_runtime_v0_6D1_R3_3.py`
- `DEME_RECONNECTION_COALESCENCE_CONTRACT_v0_6D1_R3_3.md`
- `LIBRARY_REUSE_AUDIT_v0_6D1_R3_3.md`
- `V0_6D1_R3_3_STATUS.md`
- `NEXT_STAGE_HANDOFF_v0_6D1_R3_3.md`
- `tests/test_r3_3_deme_reconnection_coalescence.py`
- `scripts/audit_v0_6D1_R3_3.py`
- `scripts/run_v0_6D1_R3_3_local.py`
- `run_v0_6D1_R3_3_windows.ps1`
