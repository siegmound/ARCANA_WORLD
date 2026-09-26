# R6 spherical boundary-zone footprint contract

Decision: `REFERENCE_MAP_MATERIALIZATION_BLOCKED`.

The immutable t0 parents bind 12 plates, 1,983 shared boundary segments and 20 degree-3 junctions. The edge geometry is inherited from the coarse 1-degree spherical finite-volume partition: meridian edges and latitude-parallel (small-circle) edges. Support remains `COARSE_SUPPORT_ON_FINE_GRID`.

The width envelope remains the prior authorial design envelope, 100–1,000 km, with no distribution and no canonical realization. `W_model` means full cross-zone width; `W_model/2` is only a possible symmetric geometric half-width convention, not an adopted physical allocation. Predeclared geometry test values are 100, 250, 500 and 1,000 km; no footprint algorithm has yet produced valid measurements at those widths.

The preferred next implementation candidate is a global spherical network-distance partition coupled to a constrained local mesh/arrangement. It is not selected as canonical until it passes continuous coverage, non-overlap, core-preservation, junction-connectivity and partition-of-unity checks. Per-edge buffers, raster dilation, arbitrary clipping, nearest-cell repair and implicit local width capping are not authorized.

No width was selected; no zones, rigid cores, patches, reference coordinates, weights or payload were materialized. No forward evolution or parent mutation occurred. The precise blocker is the absence of an implemented and fixture-validated continuous spherical arrangement handling both great-circle meridians and small-circle parallels while preserving global ownership and resolving all 20 junction patches.
