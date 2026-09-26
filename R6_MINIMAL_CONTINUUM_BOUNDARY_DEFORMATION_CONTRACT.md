# R6 minimal continuum boundary-deformation contract

Decision: **CONTINUUM_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_UNBOUND**

PASS_TARGETED_CONTINUUM_MODEL_ADJUDICATION__FIRST_INTERVAL_BLOCKED. No forward evolution is authorized.

## Adjudication

Finite-width zones and triangulated deforming networks are scientifically useful representation families, but ARCANA has not defined the zone footprint, width, core ownership, material-coordinate map, strain law, or junction constraints. The zero-width ledger does not establish where material resides. The current fail-closed policy therefore remains.

Diffuse-boundary dimensions vary by tectonic setting; reported Earth examples cannot be promoted to a universal width for untyped synthetic boundaries. The 1-degree cell scale and edge length are not substitutes. No t0 zone state is created and initial strain is not assumed zero.

Opening continues to use the existing rift-progress state as its sole source of truth (not advanced). Shortening and shear remain unmaterialized and are not interpreted as subduction, orogeny, or fault slip. No continuous velocity field, finite strain, Jacobian guard, or junction velocity is selected.

## Sources

- [Gordon (1998), The plate tectonic approximation: Plate nonrigidity, diffuse plate boundaries, and global plate reconstructions](https://doi.org/10.1146/annurev.earth.26.1.615): Diffuse zones vary strongly in scale; some exceed 1000 km across and reported relative rates/strain vary. This demonstrates non-universality, not an ARCANA width prior.
- [Gurnis et al. (2018), Global tectonic reconstructions with continuously deforming and evolving rigid plates](https://doi.org/10.1016/j.cageo.2018.04.007): A deforming network uses finite network geometry and triangular tessellation with strain tracking; it is an implementation representation requiring specified domain and constraints, not a universal constitutive law.
- [Bird (2003), An updated digital model of plate boundaries](https://doi.org/10.1029/2001GC000252): Boundary classes combine kinematics with geological evidence; relative motion alone does not determine process type.
- [McKenzie & Morgan (1969), Evolution of triple junctions](https://doi.org/10.1038/224125a0): Junction stability depends on boundary configuration and motion; incidence degree alone is insufficient.
- [Cronin (1992), Types and kinematic stability of triple junctions](https://doi.org/10.1016/0040-1951(92)90391-I): Kinematic compatibility/stability depends on boundary types and evolving motions, unavailable for the synthetic t0 graph.
- [pyGPlates Primer, Deformation and topological networks](https://www.gplates.org/docs/pygplates/pygplates_primer): The technical model represents finite network polygons, optional rigid blocks, deforming points, triangulation, and strain; it does not select ARCANA physics or parameters.
