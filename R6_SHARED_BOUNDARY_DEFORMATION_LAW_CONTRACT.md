# R6 shared-boundary deformation law contract

## Decision

**NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND.** Keep the shared network as the master interface representation, but do not authorize a finite-time transition. Current policy is zero-capacity/fail-closed.

## Candidate adjudication

| Family | Disposition | Reason |
|---|---|---|
| Zero-width centerline + residual | Algebraic diagnostic only | It can conserve relative velocity algebraically, but residual bookkeeping has no spatial support or physical map to keep rigid-core boundaries compatible. |
| Finite-width deforming zone | Not bound | Requires physical footprint/width, support, deformation mapping, and capacity/constitutive semantics absent from t0. The 1° cell is not a physical width. |
| Triangulated deforming network | Backend candidate only | GPlates-style networks resolve finite deforming regions and strain; the software does not provide ARCANA's causal law or event semantics. |
| Zero-capacity fail-closed | Selected current policy | Any nonzero unsupported relative motion blocks advancement. |

## State semantics

- Shared boundary network: one interface identity, never duplicated by side.
- Rigid cores remain a t0 kinematic abstraction; future topological domains may include deforming margins and must not be called rigid polygons.
- Existing cumulative local normal opening/rift progress is the sole opening-progress source. It is not advanced and does not itself define boundary geometry.
- Shortening and tangential slip are not materialized. If future operators use ledgers, they mean unresolved relative displacement only—not subduction, thickening, fault slip, or uplift.
- A future unresolved state may be restartable as an integrator checkpoint only; not a World History snapshot until physical response is consumed and partition checks pass.

The symmetric residual identity `vB-vA = (vB-v_boundary) - (vA-v_boundary)` is exact for any selected `v_boundary`; it does not select a physical boundary velocity. Midpoint/half-stage, one-sided attachment, or least-squares fitting is therefore not adopted.

## Why the step remains blocked

All 1,983 current segments have nonzero relative motion. Opening has no geometric zone, convergence lacks a shortening/contact response and transferable minimum capacity, shear lacks an interface state/remesh law, and all 20 multi-plate junctions lack typed kinematic constraints and residual allocation. No finite guard horizon or legal `dt` follows. The existing 27,123.405-year rift horizon remains conditional and is not a timestep.

## Research basis

Bird's PB2002 associates boundary types with geological evidence as well as relative velocity and explicitly excludes diffuse orogenic zones from rigid-plate accuracy. Gordon reviews diffuse boundaries as finite zones of distributed deformation. Gurnis et al. describe continuously deforming regions as polygons tessellated by meshes with strain tracked. McKenzie & Morgan and Cronin show junction stability depends on boundary configuration and plate motions. None supplies a universal shortening capacity for these untyped synthetic ARCANA boundaries.

Sources: [Bird 2003](https://doi.org/10.1029/2001GC000252); [Gordon 1998](https://doi.org/10.1146/annurev.earth.26.1.615); [Gurnis et al. 2018](https://doi.org/10.1016/j.cageo.2018.04.007); [McKenzie & Morgan 1969](https://doi.org/10.1038/224125a0); [Cronin 1992](https://doi.org/10.1016/0040-1951(92)90391-I); [pyGPlates primer](https://www.gplates.org/docs/pygplates/pygplates_primer).
