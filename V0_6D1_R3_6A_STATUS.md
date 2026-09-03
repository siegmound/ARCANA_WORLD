# ARCANA WorldSim v0.6D1-R3.6A Status

**Stage:** `v0.6D1-R3.6A — Governed Scientific Engine Bridge Foundation`

**Status:** `CANDIDATE / IMPLEMENTED / TESTED`

## Implemented

- common immutable `ScientificExperiment` contract;
- deterministic semantic hashes and serialized experiment bundles;
- `ScientificEvidenceBundle` contract;
- `CalibrationCandidate` with mandatory `REVIEW_REQUIRED` state;
- hard direct-canonical-write denial;
- ARCANA R3/R3.5 state exporters;
- engine registry for NEMO, Madingley, Geonomics, CDMetaPOP and RangeShifter;
- NEMO 2.4.2 neutral bridge and preparation-only mode;
- generic isolated sidecar interfaces for the other four engines;
- formal integration audit and Windows check runner.

## Scientific behavior changed

**None.** R3.5 runtime and all parent authorities remain untouched.

## Gate

R3.6A does not authorize a new H0 150 Ma checkpoint and does not authorize 150→90 Ma continuation.

Next: `R3.6B — NEMO 2.4.2 Governed QTL-Ensemble Reference Benchmark`.
