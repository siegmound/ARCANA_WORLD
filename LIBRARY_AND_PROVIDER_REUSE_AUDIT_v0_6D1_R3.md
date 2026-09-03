# v0.6D1-R3 — Scientific Library & Provider Reuse Audit

## Decision
R3 follows **reuse-first** engineering. No new general-purpose geospatial or graph algorithm is introduced where a mature scientific library or an existing ARCANA provider already covers the operation.

## Reused components

| Need | Selected authority/tool | Reason |
|---|---|---|
| Raster connected components | `scipy.ndimage.label` | Mature C-backed connected-component labeling for 2-D masks |
| Reproductive graph components | SciPy sparse graph connectivity | Avoids custom graph traversal and matches sparse pairwise connectivity |
| Nearest valid land remap | `scipy.spatial.cKDTree` | Mature nearest-neighbor implementation already used by the parent runtime |
| Array/state numerics | NumPy | Existing runtime authority |
| Paleogeographic event reconstruction | ARCANA D3.2C `paleogeographic_history.py` | Existing validated endpoint-constrained barrier-history provider; reused byte-for-byte |

## Evaluated but not selected

- **xESMF**: unnecessary because all A1 keyframes are already on the same 90×180 grid; R3 is not regridding between different grids.
- **Rasterio / Shapely**: useful for raster/vector GIS operations, but R3 stays in raster space and would gain complexity without additional physical authority.
- **NetworkX**: general and mature, but SciPy sparse connectivity is a closer fit for the numerical arrays already present and avoids graph-object overhead.
- **matrix-exponential/CTMC transport (`scipy.sparse.linalg.expm_multiply`)**: not selected because habitat/resource-dependent migration generators change with state; freezing a generator across long intervals would change model semantics.

## Custom code kept intentionally small
R3 custom code is limited to:
1. selecting the appropriate A1 bracket;
2. delegating each bracket to D3.2C;
3. adapting fractional land support into the rebased habitat/connectivity representation;
4. event-driven vicariance grandfathering;
5. binding the provider to the existing R2.1 runtime.

No new global speciation/extinction rate, stochastic radiation rate, or custom geospatial solver is introduced.
