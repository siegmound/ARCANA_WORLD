# v0.6D1-R2.1 — Library Reuse & Implementation Audit

## Decision

R2.1 follows **reuse-first** engineering. No custom graph traversal, nearest-neighbour search, or generic image/raster labeling algorithm is introduced when a mature SciPy implementation already exists.

## Reused production libraries

1. **`scipy.ndimage.label`** — 2-D raster connected-component labeling. ARCANA adds only the domain-specific longitude seam union needed for a periodic world grid.
2. **`scipy.sparse.csgraph.connected_components`** — reproductive-component graph partition after the D3.0C isolation predicates have determined which component pairs remain reproductively connected.
3. **`scipy.spatial.cKDTree`** — conservative nearest-land remapping when the discrete paleogeographic support changes.

The active environment used for R2.1 validation contains NumPy 2.3.5 and SciPy 1.17.0.

## Existing ARCANA code reused instead of reimplemented

- `speciation_gate.py` from SEALED D3.0C is copied byte-for-byte from the surviving user-supplied v0.6.4D package. SHA-256: `1927744f10e39c8c2af39b6e72799bef8b7b8466bea123d1aa28d38c812af028`.
- D3.2B founder-lineage viability thresholds and semantics are reused from `diversification_adequacy.py`.
- D3.2D persistent deterministic nonviability semantics are reused for ordinary extinction.
- R2 habitat, demographic target, selection, additive-variance, and conservative paleogeographic-remap functions are retained rather than rewritten.

## Evaluated and rejected for this stage

### NetworkX connected-components
Functionally valid, but unnecessary. The runtime already depends on SciPy and the reproductive graph is a small numerical sparse graph. Adding NetworkX would increase dependency surface without adding semantics.

### `scipy.sparse.linalg.expm_multiply` for migration
A matrix-exponential transport integrator is mature, but was rejected for R2.1 because the transition weights depend on habitat and predator/prey state. Freezing a single generator across a long macrostep would silently change ARCANA's biological model. R2.1 therefore uses deterministic fixed-cadence subcycling instead.

## Cadence architecture

- external macrostep/checkpoint chunk: 500 kyr candidate;
- biological cadence: 125 kyr;
- transport cadence: 62.5 kyr;
- speciation/extinction/fission checks: 500 kyr;
- output snapshot cadence: 1 Myr.

External chunking is not a biological parameter. A 250 kyr and a 500 kyr external macrostep produce bit-identical state when the same internal cadence is used.

## Persistent-vicariance fission qualification

The D3.2B fission actuator is implemented and tested, including the 2 Myr continuous-persistence gate. It remains **OFF in the R2.1 210→180 Ma production pilot** because the self-contained R2 reference has only two paleogeographic support keyframes (210 and 180 Ma). A diagnostic run with ecological connectivity alone produced 47 demographic fissions in the first 5 Myr; treating those as production authority without resolved barrier history would be underdetermined. R3 may enable this actuator when the full deep-time paleogeographic barrier-history provider is bound.
