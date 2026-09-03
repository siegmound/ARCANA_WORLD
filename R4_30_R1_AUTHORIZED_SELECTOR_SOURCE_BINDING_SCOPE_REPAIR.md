# R4.30-R1 — Authorized Selector Source-Binding Scope Repair

## Finding
The initial R4.30 target materialization gate treated every R4.28 parent `source_packet` as a conjunctive integrity dependency. This was broader than the authority actually frozen in R4.29: R4.29 froze an exact selector/transform authority, but did not freeze every candidate source packet as mandatory evidence.

Observed initial run: 5 authorized attempts -> 0 materialized, 4 semantic/transform deferrals, 1 source-integrity block, while J14 executed and validated successfully.

## Repair
For each R4.29-authorized selector, R4.30-R1 reconstructs the binding from the frozen R4.28 source packets and requires exactly one source that is simultaneously:

- present;
- SHA256-equal to its frozen parent hash;
- compatible with the frozen parser;
- contains the exact frozen selector.

A missing/hash-drifted *non-binding alternative candidate packet* is recorded but no longer vetoes a unique valid exact binding.

Fail-closed behavior remains:

- zero exact valid bindings + any drift -> BLOCKED;
- zero exact valid bindings with all packets intact -> BLOCKED;
- multiple exact valid bindings -> DEFERRED ambiguity;
- selector/transform changes are forbidden.

No numeric target is promoted adjudicatively in R4.30-R1. J14, Geonomics, R4.2, canonical parameters and Deep biological coupling governance are unchanged.
