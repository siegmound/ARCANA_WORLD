"""Synthetic pyGPlates 1.0 deforming-network feasibility fixture.

This module intentionally imports pyGPlates only inside :func:`run_spike`.
It has no connection to canonical R6 state, geometry, or authority registers.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

FIXTURE_ID = "R6_SYNTHETIC_DEFORMING_NETWORK_V1"
RECONSTRUCTION_TIME_MA = 5.0
VELOCITY_DELTA_TIME_MA = 1.0
EARTH_RADIUS_KM = 6371.0


def _finite(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(v) for v in value)
    return True


def _vector(vector: Any) -> list[float] | None:
    if vector is None:
        return None
    return [float(vector.get_x()), float(vector.get_y()), float(vector.get_z())]


def _point(point: Any) -> list[float]:
    lat, lon = point.to_lat_lon()
    return [float(lat), float(lon)]


def _strain(strain: Any) -> dict[str, Any] | None:
    if strain is None:
        return None
    return {
        "total_strain_rate": float(strain.get_total_strain_rate()),
        "velocity_spatial_gradient": [float(x) for x in strain.get_velocity_spatial_gradient()],
    }


def _rotation_feature(pygplates: Any, plate_id: int, angle_degrees: float) -> Any:
    pole = pygplates.PointOnSphere(0.0, 90.0)
    finite_rotation = pygplates.FiniteRotation(pole, math.radians(angle_degrees))
    feature = pygplates.Feature.create_total_reconstruction_sequence(
        plate_id,
        0,
        [(0.0, pygplates.FiniteRotation.create_identity_rotation()),
         (10.0, finite_rotation)],
    )
    feature.set_name(f"{FIXTURE_ID}_ROTATION_PLATE_{plate_id}")
    return feature


def _regular_feature(pygplates: Any, geometry: Any, plate_id: int) -> Any:
    feature = pygplates.Feature(pygplates.FeatureType.gpml_unclassified_feature)
    feature.set_geometry(geometry)
    feature.set_reconstruction_plate_id(plate_id)
    feature.set_name(f"{FIXTURE_ID}_PLATE_{plate_id}")
    return feature


def _build_fixture(pygplates: Any) -> tuple[Any, list[Any]]:
    """Build a closed square network, a center node, and a control point."""
    corners = [(-10.0, -10.0), (-10.0, 10.0), (10.0, 10.0), (10.0, -10.0)]
    plate_ids = [101, 102, 103, 104]
    boundaries = [
        _regular_feature(
            pygplates,
            pygplates.PolylineOnSphere([corners[index], corners[(index + 1) % 4]]),
            plate_ids[index],
        )
        for index in range(4)
    ]
    # The point is an interior constraint for the deforming network.
    interior = _regular_feature(pygplates, pygplates.PointOnSphere(0.0, 0.0), 101)
    sections = [
        pygplates.GpmlTopologicalSection.create(feature, pygplates.GpmlTopologicalNetwork)
        for feature in boundaries
    ]
    network_geometry = pygplates.GpmlTopologicalNetwork(
        sections,
        [pygplates.GpmlTopologicalSection.create_network_interior(interior)],
    )
    network = pygplates.Feature.create_topological_network_feature(network_geometry)
    network.set_reconstruction_plate_id(101)
    network.set_name(f"{FIXTURE_ID}_NETWORK")

    # A second, explicitly identified plate rotation provides a distinct kinematic input.
    rotation_features = [
        _rotation_feature(pygplates, 101, 0.0),
        _rotation_feature(pygplates, 102, 1.0),
        _rotation_feature(pygplates, 103, 0.5),
        _rotation_feature(pygplates, 104, -0.5),
    ]
    model = pygplates.TopologicalModel(
        [*boundaries, interior, network],
        pygplates.RotationModel(rotation_features),
    )
    samples = [
        {"sample_id": "center", "lat_lon": [0.0, 0.0]},
        {"sample_id": "interior_north", "lat_lon": [5.0, 0.0]},
        {"sample_id": "outside_control", "lat_lon": [25.0, 0.0]},
    ]
    return model, samples


def _one_run(pygplates: Any) -> dict[str, Any]:
    model, samples = _build_fixture(pygplates)
    snapshot = model.topological_snapshot(RECONSTRUCTION_TIME_MA)
    networks = [
        topology for topology in snapshot.get_resolved_topologies()
        if isinstance(topology, pygplates.ResolvedTopologicalNetwork)
    ]
    network = networks[0] if networks else None
    resolved_boundary = network.get_resolved_boundary() if network else None
    boundary_geometry = resolved_boundary.get_resolved_geometry() if resolved_boundary else None
    boundary_count = len(boundary_geometry.get_points()) if boundary_geometry is not None else 0

    triangulation = network.get_network_triangulation() if network else None
    triangles = list(triangulation.get_triangles()) if triangulation is not None else []
    vertices = list(triangulation.get_vertices()) if triangulation is not None else []

    queried: list[dict[str, Any]] = []
    for sample in samples:
        lat, lon = sample["lat_lon"]
        point = pygplates.PointOnSphere(lat, lon)
        classified = bool(resolved_boundary and resolved_boundary.get_resolved_geometry().is_point_in_polygon(point))
        velocity = network.get_point_velocity(
            point,
            velocity_delta_time=VELOCITY_DELTA_TIME_MA,
            velocity_delta_time_type=pygplates.VelocityDeltaTimeType.t_plus_delta_t_to_t,
            velocity_units=pygplates.VelocityUnits.cms_per_yr,
            earth_radius_in_kms=EARTH_RADIUS_KM,
        ) if network else None
        strain = network.get_point_strain_rate(point) if network else None
        reconstructed = network.reconstruct_point(point, RECONSTRUCTION_TIME_MA + 1.0) if network else None
        queried.append({
            **sample,
            "inside_resolved_boundary": classified,
            "velocity": _vector(velocity),
            "strain_rate_diagnostic": _strain(strain),
            "reconstructed_position_lat_lon": _point(reconstructed) if reconstructed is not None else None,
        })

    return {
        "pygplates_version": str(pygplates.__version__),
        "fixture_id": FIXTURE_ID,
        "reconstruction_time_ma": RECONSTRUCTION_TIME_MA,
        "network_resolved": network is not None,
        "resolved_boundary_point_count": boundary_count,
        "triangulation_available": triangulation is not None,
        "triangulation_summary": {
            "vertex_count": len(vertices),
            "triangle_count": len(triangles),
        } if triangulation is not None else None,
        "triangulation_algorithm_interpretation": "NOT_ASSIGNED",
        "samples": queried,
        "velocity_convention": {
            "velocity_delta_time_ma": VELOCITY_DELTA_TIME_MA,
            "velocity_delta_time_type": "t_plus_delta_t_to_t",
            "velocity_units": "cms_per_yr",
            "earth_radius_km": EARTH_RADIUS_KM,
        },
        "strain_rate_convention": {
            "diagnostic_only": True,
            "pygplates_1_0_fixed_delta_time_ma": 1.0,
            "pygplates_1_0_earth_radius_km": float(pygplates.Earth.equatorial_radius_in_kms),
            "arcana_strain_semantics_bound": False,
        },
        "all_finite": False,
        "canonical_state_changed": False,
        "forward_evolution_executed": False,
    }


def run_spike() -> dict[str, Any]:
    """Run twice and return a deterministic, JSON-safe feasibility report."""
    try:
        import pygplates  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("PYGPLATES_RUNTIME_UNAVAILABLE") from exc

    first = _one_run(pygplates)
    second = _one_run(pygplates)
    first["all_finite"] = _finite(first)
    second["all_finite"] = _finite(second)
    first["repeatability"] = {
        "identical_json": json.dumps(first, sort_keys=True, separators=(",", ":"))
        == json.dumps(second, sort_keys=True, separators=(",", ":")),
        "first_run_sha256": hashlib.sha256(json.dumps(first, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "second_run_sha256": hashlib.sha256(json.dumps(second, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }
    first["artifact_classification"] = "NONCANONICAL_FEASIBILITY_DIAGNOSTIC"
    return first


def main() -> int:
    try:
        result = run_spike()
    except RuntimeError as exc:
        if str(exc) == "PYGPLATES_RUNTIME_UNAVAILABLE":
            print(json.dumps({"status": "PYGPLATES_RUNTIME_UNAVAILABLE"}, sort_keys=True))
            return 2
        raise
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
