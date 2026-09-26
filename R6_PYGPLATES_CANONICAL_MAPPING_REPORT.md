# R6 pyGPlates canonical mapping diagnostic

- Status: **FAIL**
- Decision: `PYGPLATES_RUNTIME_UNAVAILABLE`
- Classification: `NONCANONICAL_FEASIBILITY_DIAGNOSTIC`
- pyGPlates version: `UNAVAILABLE`
- Runtime detail: `PYGPLATES_RUNTIME_UNAVAILABLE`
- Canonical t0: 210.0 Ma; payload SHA-256 `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`

## Inventory and representability

- ARCANA plates: 12; canonical faces: 64800
- Boundary segments: 1983; boundary plate pairs: 30
- Junctions: 20
- Rigid polygon candidates: None; represented plate groups: None
- Rigid blocks supported: `None`
- Deforming-network API supported: `None`; canonical region assignment: `UNBOUND`
- Boundary support geometries: None; unresolved boundary semantics: 1983
- Junction point geometries: None; unresolved junction semantics: 20
- Exact curve semantics: `UNBOUND; no geometry loss tolerance specified`

The adapter constructs geometry candidates only. It does not resolve topologies or assign motion, boundary process, strain semantics, or junction behavior. A `PASS` means this diagnostic completed; it is not a solver-selection or scientific-authority decision.

Canonical state unchanged; forward evolution, dt authorization, W_model selection, and rift advancement remain false.
