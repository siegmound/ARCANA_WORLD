# R4.30-R2 — Selector Authority Source-Identity Freeze Gap Repair

## Finding
R4.29 froze an exact selector/transform authority against an aggregate exact schema inventory, but did not freeze the identity of the source packet that supplied that selector. R4.30-R1 correctly stopped unrelated candidate-packet drift from vetoing a unique reconstructed binding, but it still classified `zero exact reconstructed binding + any drifted packet` as a source-integrity failure. That is over-broad when one or more parent source packets still match their frozen hashes: source integrity survives, while source-binding authority is incomplete.

## Repair
- Exactly one hash-valid source containing the frozen selector: execute the frozen transform as before.
- Multiple exact hash-valid bindings: defer for ambiguity.
- Zero exact bindings but at least one hash-valid parent packet: defer as `DEFERRED_AUTHORIZED_SELECTOR_SOURCE_BINDING_AUTHORITY_NOT_FROZEN_BY_R429`.
- Zero exact bindings and zero hash-valid parent packets: remain fail-closed `BLOCKED_AUTHORIZED_SELECTOR_ALL_PARENT_SOURCES_FAIL_INTEGRITY`.

The repair does not choose a source, selector, transform, target value, or mapping based on external results. J14 authority execution, R4.2 immutability, Deep OFF, and all canonical governance remain unchanged.
