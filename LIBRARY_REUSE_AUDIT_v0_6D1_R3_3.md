# Library / Provider Reuse Audit — v0.6D1-R3.3

## Decision
**Reuse SciPy + existing ARCANA D3 operators. Do not introduce a new population-genetics simulator for this stage.**

### Reused
- `scipy.sparse.csgraph.connected_components`: mature sparse-graph connected-component analysis; used for transitive reconnection groups.
- Existing `scipy.ndimage` raster connectivity from the parent runtime.
- ARCANA D3.2B migration/permeability/contact implementation, source-hash locked.
- ARCANA D3.3A additive-variance / gene-flow moment implementation.
- ARCANA D3.0C speciation/RI gates.

### Evaluated but not adopted
- **tskit**: excellent compact representation and analysis of explicit genetic genealogies / ARGs, but R3.3 has no sequence-level or tree-sequence state. Adopting it here would change model ontology rather than replace a low-level algorithm.
- **msprime**: backward-time ancestry / genome simulation; useful for future explicit genomic zooms, not for coalescing current WorldSim raster demes while preserving existing quantitative-genetic moments.
- **NetworkX**: capable of graph connected components, but SciPy sparse graph routines are already installed, lower-overhead for numeric arrays, and used elsewhere in the runtime.

## Environment used for closure
- NumPy 2.3.5
- SciPy 1.17.0

No new runtime dependency is required by R3.3.
