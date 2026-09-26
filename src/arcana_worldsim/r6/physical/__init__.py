"""Numerical physical-reference geometry for R6 (not canonical history)."""

from .boundary_geometry import (
    BoundaryFeature,
    Junction,
    RegionQuery,
    SphericalBoundaryArrangement,
    SphericalSegment,
    unit_xyz,
)
from .junction_basis import JunctionMeshTriangle, ThreePlateJunctionBasis
from .reference_mesh import (OwnershipSample, SphericalReferenceMesh, build_icosphere,
                             integrate_spherical_ownership, validate_spherical_mesh)
from .reference_arrangement import (ArrangementCell, ParentFace,
                                    build_parent_conforming_reference_arrangement,
                                    canonical_parent_faces, certify_parent_region,
                                    spherical_rect_area_m2,
                                    validate_parent_conforming_arrangement)

__all__ = ["BoundaryFeature", "Junction", "RegionQuery", "SphericalBoundaryArrangement",
           "SphericalSegment", "unit_xyz", "JunctionMeshTriangle", "ThreePlateJunctionBasis",
           "OwnershipSample", "SphericalReferenceMesh", "build_icosphere",
           "integrate_spherical_ownership", "validate_spherical_mesh", "ArrangementCell",
           "ParentFace", "build_parent_conforming_reference_arrangement",
           "canonical_parent_faces", "certify_parent_region", "spherical_rect_area_m2",
           "validate_parent_conforming_arrangement"]
