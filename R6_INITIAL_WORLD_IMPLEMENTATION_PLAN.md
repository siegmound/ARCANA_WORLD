# R6 Initial World Generator — Implementation Plan

**Next action:** `R6_INITIAL_WORLD_GENERATOR_IMPLEMENTATION_AND_210MA_MATERIALIZATION`
**Current status:** design contracts only; the generator has not been implemented or run.

## Work sequence

1. **Preflight:** verify `main`, exact contract/input hashes, protected index blobs, and external-result root. Fail closed on drift; preserve all existing dirty and untracked material.
2. **Implement pure deterministic primitives:** exact spherical grid/cell-area helpers; periodic/polar topology; independent SHA-256-derived PCG64 streams; canonical serialization and payload hashing. Unit-test seam, poles, area closure, stream independence, and reproducibility first.
3. **Implement the t0 geography generator:** spherical plate mosaic (12–18 plates), 4–8 clustered cratonic blocks, one dominant supercontinent, explicit categorical province/boundary fields, multiscale coastline, and bounded authorial land relief. Generate exactly one 210 Ma state on `R6_GLOBAL_GEOGRAPHY_1DEG_V1`.
4. **Keep unsupported state unknown:** emit UNKNOWN bathymetry and plate motion; no Deep, climate, hydrology, lithology, soil, biology, human, or resource outputs. Attach per-field uncertainty, support, authority and provenance.
5. **Validate before promotion:** implement the validation contract; run property/fixture tests, clean-process deterministic rerun, morphology and resolution audits, target-hardware time/RAM benchmark, and output-schema/hash checks.
6. **Materialize atomically outside Git:** write an isolated temporary package, verify all contracts and hashes, then promote to an immutable run-ID directory. Keep only compact evidence/manifests in ordinary Git if a later task explicitly requests integration.
7. **Stop at t0:** do not advance plates, evolve terrain, run Deep/climate/hydrology, acquire a provider, or enter downstream biology/resource work. Those require separately bound laws, drivers, and execution authorization.

## Architecture and module boundaries

Suggested package boundaries are `r6/physical/grid.py`, `r6/physical/seed.py`, `r6/physical/supercontinent.py`, `r6/physical/schema.py`, and a command runner. Keep generator functions pure where possible; the runner owns validation, manifests, temporary paths, hashing, and atomic promotion. Integrate through the R6 state/provenance envelopes; do not import R5 scripts as runtime dependencies. Chunk intermediate fields to bound memory; do not allocate time×domain cubes.

## Required engineering evidence before calling t0 materialized

- contract and dependency SHA-256 ledger;
- exact runtime/library/platform identity and seed-lineage manifest;
- land/ocean, plate, crust/province, and supported elevation field schema with UNKNOWN masks;
- grid and spherical cell-area audit;
- morphology diagnostics with area-weighted denominators;
- deterministic repeated-run hashes;
- memory and elapsed-time benchmark on the intended workstation class;
- external payload sizes/hashes and atomic-promotion record;
- validation report class (`PASS_WITH_UNKNOWN` is expected if required design checks pass while unsupported domains remain UNKNOWN).

## Explicitly out of scope

No physical forward evolution or trajectory, provider selection/acquisition, climate or hydrology, Deep, lithology/parent-material/soil/pedogenesis, vegetation/fauna/marine ecology, human history, resource/K(x,t), P7Q reopening, current-state update, authority-register/index mutation, staging, commit, or push. This plan creates no additional PRE5/HRAB micro-gates.
