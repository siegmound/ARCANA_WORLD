# v0.6D1-R4.27 — Target Extractor Static Validation & Target-Design / Geonomics J14 Authority Request Adjudication

## Purpose
R4.27 consumes the SEALED R4.26 implementation/request registries and performs a result-independent authorization gate. It does not execute target numerics, external engines, readjudication, or canonical replay.

## Canonical extractor gate
All 44 R4.26 read-only extractor implementations are revalidated against the frozen source hashes and parser families. Static schema surfaces are inspected without emitting target numeric values. An exact selector can be authorized only if it was already frozen by the parent and is exactly present in the source schema. R4.27 MUST NOT invent a selector from field-name similarity, synonym matching, result agreement, or fallback search.

Because R4.26 intentionally froze the 44 implementations with `selector_binding_status=PENDING_EXPLICIT_R427_STATIC_SELECTOR_BINDING` and no result-selected selector authority, records lacking a parent-frozen exact selector remain `DEFERRED_EXPLICIT_SELECTOR_AND_TRANSFORM_AUTHORITY_REQUIRED`. This is a valid terminal static disposition, not a process failure.

## Semantic repair gate
The single R4.26 semantic-repair implementation may only review the frozen R4.18 rejection cause `eligible_primary_row_count`. Numeric target values and mapping classes are immutable in R4.27.

## Twelve new target-design authority requests
R4.27 adjudicates all 12 requests (5 `range_shift_rate`, 7 `founder_persistence`) against their pre-result construct, canonical-observable, unit-family, forbidden-shortcut, and governance requirements. Approval authorizes only authority-definition implementation preflight in R4.28. It does not authorize numeric target materialization or adjudicative promotion.

## Geonomics J14
R4.27 adjudicates the R4.26 request for a new engine-independent canonical spatial authority covering 3 Ma→200 ka. Approval authorizes only implementation preflight in a new namespace. Canonical spatial replay execution, Geonomics execution, backward interpolation/extrapolation, and R4.2/J14 mutation remain forbidden.

## Governance invariants
- frozen R4.2 registry immutable;
- no external-engine result may define an ARCANA canonical target or spatial state;
- no majority vote;
- no result-selected selector/transform;
- no numeric target execution;
- no engine execution;
- no readjudication;
- no canonical state/parameter change;
- Deep biological coupling OFF.
