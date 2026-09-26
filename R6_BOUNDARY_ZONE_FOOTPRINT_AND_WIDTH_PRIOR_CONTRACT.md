# R6 boundary-zone footprint and width-prior contract

Decision: **BOUNDARY_FOOTPRINT_CONSTRUCTION_BLOCKED**

PASS_WIDTH_SCALE_PRIOR_ADJUDICATION__REFERENCE_MAP_NOT_CANONICALIZED. The bounded scale is an ARCANA design hypothesis, not an empirical universal width.

## Width concepts

`W_model` (physical-model domain scale), `W_numerical` (mesh spacing), and `W_support` (coarse inherited support) are separate. Proposed `W_model` envelope: 100–1,000 km, with no probability distribution. Both endpoints are authorial assumptions, informed only by broad literature scale context; they are not measured bounds. Fault-damage-zone widths are excluded.

No canonical realization is drawn until footprint and acceptance rules are frozen. The t0 geometry requires spherical vector corridors, non-overlapping core/zone ownership, shared degree-3 junction patches, and no silent clipping/capping. Those are not yet implemented or validated, so no map or t0 zone state exists.

If a reference mesh is later created, `F_R6(t0)=I` and accumulated post-t0 operator strain zero are definitions relative to that operator's start. Pre-t0 geological strain remains `UNKNOWN`; no claim of a geologically undeformed Earth is made.

Opening continues to use existing rift progress as its sole source of truth. Shortening is not subduction/orogeny; shear is not fault mechanics. No strain rates or Jacobian guard are computed without an instantiated field and mesh.

## Sources

- [Chen & Grimison (1989), Earthquakes associated with diffuse zones of deformation in the oceanic lithosphere: some examples](https://doi.org/10.1016/0040-1951(89)90209-6): up to several hundred kilometres wide; seismic/deformation-zone extent, not a universal mechanical corridor width; not transferable as a measured ARCANA parameter.
- [Gordon (1998), The plate tectonic approximation: Plate nonrigidity, diffuse plate boundaries, and global plate reconstructions](https://doi.org/10.1146/annurev.earth.26.1.615): some zones exceed 1000 km on a side; reported dimensions are not necessarily cross-boundary width; supports context dependence, not a numeric width bound.
- [Gurnis et al. (2018), Global tectonic reconstructions with continuously deforming and evolving rigid plates](https://doi.org/10.1016/j.cageo.2018.04.007): finite deforming network domains tessellated by triangular mesh; supports finite-domain/strain representation; does not prescribe universal width, partition, or ARCANA constitutive law.
- [Official pyGPlates Primer: Deformation and topological networks](https://www.gplates.org/docs/pygplates/pygplates_primer): network polygon, rigid blocks, deforming points, triangulation and strain; technical capabilities only; no ARCANA physical or width authority.
- [Babuška & Melenk (1997), The partition of unity method](https://doi.org/10.1002/%28SICI%291097-0207%2819970228%2940%3A4%3C727%3A%3AAID-NME86%3E3.0.CO%3B2-N): basis/regularity method, not a geological width; supports partition-of-unity as a numerical basis concept only; does not provide ARCANA zone geometry or tectonic law.
- [McKenzie & Morgan (1969), Evolution of triple junctions](https://doi.org/10.1038/224125a0): not a width study; junction stability depends on boundary configuration/motion, not incidence alone.
- [Cronin (1992), Types and kinematic stability of triple junctions](https://doi.org/10.1016/0040-1951(92)90391-I): not a width study; requires boundary classes and evolving kinematic constraints.
