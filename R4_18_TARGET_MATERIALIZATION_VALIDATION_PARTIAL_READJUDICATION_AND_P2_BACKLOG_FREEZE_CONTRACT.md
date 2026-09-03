# v0.6D1-R4.18 — Target Materialization Validation, Partial Readjudication & P2 Backlog Freeze

R4.18 is a fail-closed semantic validation stage. It consumes the SEALED R4.17 outputs and the immutable R4.13 75-cell matrix. It does not execute any external engine and cannot modify canonical state.

## Frozen scope

R4.17 produced three materialized ARCANA target candidates: exactly one DIRECT/NORMALIZABLE candidate requiring R4.18 validation and two PROXY_ONLY targets that remain contextual. R4.18 may alter evidence rows only in a cell whose non-proxy candidate passes all semantic and provenance gates.

## Validation gates

A candidate is not selected by numerical agreement. It must have the R4.16 domain protocol, explicit unit/time/space/transform/provenance fields, recognized candidate comparability, safe pre-result provenance, and at least one PRIMARY R4.13 evidence row with a frozen DIRECT/NORMALIZABLE mapping and a normalized metric already authorized for that engine/domain by R4.4. R4.3 descriptor-bridge targets additionally require the selected canonical artifact hash to remain present and matching.

Only after these gates pass is candidate comparability converted from `DIRECT_CANDIDATE`/`NORMALIZABLE_CANDIDATE` to `DIRECT`/`NORMALIZABLE`, and R4.4 `classify_pair` is reused without changing thresholds.

## Partial readjudication

The immutable R4.13 matrix is copied into the R4.18 namespace. Only eligible PRIMARY rows of validated candidate cells can receive the validated target and be reclassified. Secondary-only promotion, majority vote, target leakage, result-selected transforms, canonical writes, replay and parameter changes are forbidden.

If a newly validated cell becomes STRUCTURAL_DISAGREEMENT, R4.18 routes to a new causal diagnosis rather than to adapter execution.

## P2 freeze

R4.18 freezes, but does not execute, the six-cell P2 backlog accumulated from R4.14 P2 cells, R4.15-R1 exhausted retained-runtime candidates and R4.17 nonpromotable recovered metrics. P3 remains six frozen extension jobs.
