# ARCANA WorldSim v0.6D1-R3.6A

This candidate adds a governed scientific-engine integration layer **without modifying the R3.5 simulation behavior**.

Primary entrypoints:

- `src/arcana_worldsim/scientific_engines/`
- `SCIENTIFIC_ENGINE_INTEGRATION_CONTRACT_v0_6D1_R3_6A.md`
- `EXTERNAL_SCIENTIFIC_ENGINE_REUSE_AUDIT_v0_6D1_R3_6A.md`
- `scripts/prepare_nemo_reference_v0_6D1_R3_6A.py`
- `run_v0_6D1_R3_6A_checks.ps1`

The NEMO adapter is intentionally in **preparation-only** mode until R3.6B binds an official NEMO 2.4.2-validated `.ini` template and a governed QTL/genotype ensemble mapping. This avoids silently guessing simulator semantics.

`150 Ma` remains diagnostic, not an authorized canonical continuation checkpoint.
