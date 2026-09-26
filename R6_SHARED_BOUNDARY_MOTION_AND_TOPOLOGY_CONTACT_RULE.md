# R6 shared-boundary motion and topology/contact rule

## Adjudication

Adopt one shared-boundary network as the canonical interface representation, retaining rigid plate interiors. This is a state representation, not authorization to evolve it. Keep the parent finite-volume cell faces as the immutable t0 source; derive per-plate polygons from the shared network only after a governed resolver exists.

## Source-grounded geometric mechanisms

GPlates topological polygons reference shared boundary sections, and its resolver reports the subsegments actually shared among resolved topologies. Its deforming topological networks add a triangulated deforming region and optional rigid blocks. These mechanisms establish that shared topological boundaries/networks are a viable representation; they do not choose ARCANA's physical laws. Half-stage reconstruction is documented for ridge/tectonic sections and is not a universal boundary law.

## ARCANA t0 interface

Each edge has a payload/grid-keyed ID, ordered plate IDs, A-to-B normal, deterministic tangent direction, support, endpoint/junction incidence, and t0 relative velocity components. No independent side copies are allowed. Existing rift progress remains the only opening-progress source; no duplicate opening accumulator is made. Shortening and slip accumulators are not created because their process semantics are unbound.

## Positive-time law: blocked

No universal average/half-stage boundary velocity is adopted. One-sided attachment requires boundary-type evidence. A zero-width shared line cannot store finite opening as a gap-free physical deformation, while rigidly moving convergent interiors can overlap. There is no authorized finite-width boundary zone, convergence/contact capacity, or multi-plate junction velocity rule. Topology software cannot supply these missing causal semantics.

So the shared-network representation is bound at t0, but the transition law is not. No positive dt, topology guard horizon, forward checkpoint, or interval execution contract is authorized.

## Sources

- [GPlates User Manual: Topology and Crustal Deformation](https://www.gplates.org/docs/user-manual/)
- [pyGPlates Primer: topological reconstruction and deforming networks](https://www.gplates.org/docs/pygplates/pygplates_primer)
- [pyGPlates TopologicalSnapshot API](https://www.gplates.org/docs/pygplates/generated/pygplates.topologicalsnapshot)
- [pyGPlates shared topological subsegments API](https://www.gplates.org/docs/pygplates/generated/pygplates.resolvedtopologicalsharedsubsegment)
- [pyGPlates common feature example: half-stage ridge reconstruction](https://www.gplates.org/docs/pygplates/sample-code/pygplates_create_common_feature_types)
