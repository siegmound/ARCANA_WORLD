# R6 plate kinematics interface contract

**Status:** interface frozen; numerical and runtime binding pending.\
**Canonical owner:** ARCANA.

## Geometry and representation

The canonical master is spherical vector/topological plate features, not the 1° raster. The existing raster plate IDs are coarse support on a fine grid and do not establish exact boundary geometry. The representation is piecewise time-valid finite rotations with an explicit reference frame and reconstruction tree. Rotation values, reference assignments and validity intervals are not currently bound.

Kinematic representation answers how supplied motions are represented/resolved. The causal motion law answers why ARCANA changes them. These are distinct: pyGPlates or a substitute can resolve ARCANA-authored rotations, geometries and topology, but cannot select their physical law or event timing.

## Adapter boundary

Inputs are an explicitly directed interval, supported time-valid feature geometry and stable plate IDs, lineage/tree edges, ARCANA-authorized rotations/topology/event transitions, and uncertainty/support/provenance. Outputs are transformed spherical geometry, resolved topology where supplied inputs permit it, mathematically derived velocities where supported, diagnostics and deterministic run identity.

The adapter must not invent motion, split geometry, boundaries, collisions, rift triggers, subduction or vertical response. Exact spherical rotation composition may evaluate geometry inside a declared continuous rotation segment; no interpolation crosses a feature lifetime or rotation discontinuity. Solver-specific object types remain private to the adapter.

Splits and merges are ARCANA events. ARCANA records parent/child identities, time, geometry, pre/post state and boundaries; the solver only resolves the geometry. Historical identities remain queryable. Restart state binds rotation/frame/validity, topology, lineage, pending events, law/parameter identity, solver build/configuration, seeds if consumed, hashes and provenance.

Validation includes spherical/frame validity, partition checks where full coverage is expected, composition consistency, lineage at event boundaries, bounded motion under an authorized law, deterministic rerun, restart equivalence and substitutability. pyGPlates is only a candidate; no runtime is pinned and no R6 adapter has been validated. Execution is not authorized.
