"""Canonical topology checks for the static ShellSet mesh adapter."""
from pathlib import Path
import math
import hashlib
import json
from dataclasses import replace

import numpy as np

from arcana_worldsim.r6.shellset_mesh import (
    ElementRecord, FEGModel, FaultRecord, NodeRecord, PhysicalFieldBinding,
    fixture_roundtrip_evidence, load_canonical_mesh, model_from_mesh,
    normalized_feg_sha256, parse_feg, write_feg,
)
from arcana_worldsim.r6.shellset_mesh.branches import build_branch_registry
from arcana_worldsim.r6.shellset_mesh.geometry import (
    EARTH_RADIUS_M, edge_geometry_metrics, small_circle_geodesic_midpoint_deviation,
    unit_vector,
)
from arcana_worldsim.r6.repository_context import resolve_external_payload_path


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_grid_mesh_is_a_closed_sphere_with_stable_lineage():
    first = load_canonical_mesh(ROOT)
    second = load_canonical_mesh(ROOT)
    third = load_canonical_mesh(ROOT)

    assert first.audit["face_arity_distribution"] == {"3": 720, "4": 64080}
    assert first.audit["node_count"] == 64_442
    assert first.audit["triangle_count"] == 128_880
    assert first.audit["edge_count"] == 193_320
    assert first.audit["edge_incidence_distribution"] == {"2": 193_320}
    assert first.audit["euler_characteristic"] == 2
    assert first.audit["connected_components"] == 1
    assert first.audit["boundary_direct_feg_edges"] == 1_983
    assert first.audit["adjacency_support_count"] == 30
    assert set(first.audit["adjacency_support_components"].values()) == {1}
    assert first.audit["zero_area_triangles"] == 0
    assert first.audit["minimum_spherical_triangle_area_sr"] > 0
    assert math.isclose(first.audit["spherical_area_sum_sr"], 4 * math.pi, abs_tol=1e-10)
    assert first.audit["orientation_corrections"] == 0
    assert len(first.boundary_ids) == len(set(first.boundary_ids)) == 1_983
    assert len(first.junction_node_ids) == 20
    assert len(first.plate_triangle_ids) == 12
    assert len(first.adjacency_supports) == 30
    assert first.normalized_sha256 == second.normalized_sha256 == third.normalized_sha256


def test_poles_dateline_and_face_provenance_are_normalized_without_new_geography():
    mesh = load_canonical_mesh(ROOT)
    assert tuple(mesh.vertices_lat_lon[0]) == (-90.0, 0.0)
    assert tuple(mesh.vertices_lat_lon[1]) == (90.0, 0.0)
    assert mesh.vertices_lat_lon[:, 1].min() >= -180.0
    assert mesh.vertices_lat_lon[:, 1].max() < 180.0
    assert len(mesh.parent_face_triangles) == 64_800
    assert sum(map(len, mesh.parent_face_triangles)) == 128_880
    assert set(mesh.triangle_plate_id.tolist()) == set(range(12))


def _canonical_boundary_inputs():
    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    payload = resolve_external_payload_path(ROOT, manifest["payload"]["path"])
    with np.load(payload, allow_pickle=False) as archive:
        arrays = {key: archive[key].copy() for key in archive.files}
    boundary_state = json.loads((ROOT / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text())
    return arrays, boundary_state


def test_small_circle_approximation_uses_spherical_geometry_and_all_edge_metrics():
    mesh = load_canonical_mesh(ROOT)
    arrays, _ = _canonical_boundary_inputs()
    metrics = edge_geometry_metrics(mesh, arrays)
    expected = small_circle_geodesic_midpoint_deviation(45.0, 1.0)
    a, b, q = unit_vector(45, -0.5), unit_vector(45, 0.5), unit_vector(45, 0)
    normal = np.cross(a, b)
    normal /= np.linalg.norm(normal)
    spherical_cross_track = math.asin(abs(float(np.dot(q, normal))))
    assert math.isclose(expected, spherical_cross_track, abs_tol=1e-14)
    assert metrics["edge_count"] == 1983
    assert metrics["great_circle_canonical_edges"] == 702
    assert metrics["small_circle_edges"] == 1281
    assert metrics["endpoint_error_m"] == {"minimum": 0, "maximum": 0, "mean": 0, "p95": 0, "p99": 0}
    assert metrics["affected_edge_count"] == 1276
    assert metrics["maximum_cross_track_hausdorff_deviation_m"]["maximum"] < 124
    assert math.isclose(metrics["maximum_cross_track_hausdorff_deviation_m"]["maximum"],
                        EARTH_RADIUS_M * metrics["maximum_cross_track_hausdorff_deviation_rad"]["maximum"])
    assert metrics["deviation_relative_to_local_cell_scale"]["maximum"] < 0.0022
    assert len(metrics["per_edge_metrics"]) == 1983
    assert all(item["endpoint_error_m"] == 0 for item in metrics["per_edge_metrics"])
    assert all(not item["crosses_nonincident_boundary"] and item["contained_in_incident_cell"]
               for item in metrics["per_edge_metrics"])
    assert metrics["subdivision_required"] is False
    assert metrics["classification"] == "NUMERICAL_GEODESIC_APPROXIMATION_WITHIN_CANONICAL_SUPPORT"


def test_derived_branch_registry_assigns_each_boundary_once_and_chains_are_contiguous():
    mesh = load_canonical_mesh(ROOT)
    arrays, boundary_state = _canonical_boundary_inputs()
    metrics = edge_geometry_metrics(mesh, arrays)
    registry = build_branch_registry(boundary_state, mesh, metrics)
    assert registry["branch_count"] == 30
    assert registry["boundary_segment_count"] == 1983
    assert registry["junction_count"] == 20
    assert registry["plate_pair_adjacency_count"] == 30
    assert registry["unassigned_boundary_segments"] == []
    assert registry["duplicated_segment_ownership"] == []
    for branch in registry["branches"]:
        assert branch["id_authority"] == "DERIVED_CANONICAL_TOPOLOGY_REGISTRY_ID"
        chain = branch["ordered_feg_edge_chain"]
        assert len(chain) == len(branch["ordered_canonical_boundary_segment_ids"])
        assert all(left[1] == right[0] for left, right in zip(chain, chain[1:]))
    first = json.dumps(registry, sort_keys=True, separators=(",", ":"))
    second = json.dumps(build_branch_registry(boundary_state, mesh, metrics),
                        sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(first.encode()).digest() == hashlib.sha256(second.encode()).digest()


def test_feg_provenance_recovers_canonical_faces_boundaries_junctions_and_plates():
    mesh = load_canonical_mesh(ROOT)
    assert len(mesh.parent_face_triangles) == 64_800
    assert len(mesh.triangle_parent_face) == 128_880
    assert sum(map(len, mesh.parent_face_triangles)) == 128_880
    for face_index, triangle_ids in enumerate(mesh.parent_face_triangles):
        assert all(mesh.triangle_parent_face[triangle_id - 1] == face_index
                   for triangle_id in triangle_ids)
    assert set(mesh.triangle_plate_id.tolist()) == {plate for plate, _ in mesh.plate_triangle_ids}
    assert len({junction_id for junction_id, _ in mesh.junction_node_ids}) == 20
    assert len({node_id for _, node_id in mesh.junction_node_ids}) == 20
    assert len(mesh.boundary_edge_nodes) == len(mesh.boundary_ids) == 1983
    assert len({pair for _, pair in zip(mesh.boundary_ids, mesh.boundary_edge_nodes)}) == 1983
    arrays, boundary_state = _canonical_boundary_inputs()
    registry = build_branch_registry(boundary_state, mesh, edge_geometry_metrics(mesh, arrays))
    owned = [segment_id for branch in registry["branches"]
             for segment_id in branch["ordered_canonical_boundary_segment_ids"]]
    assert set(owned) == set(mesh.boundary_ids)
    assert len(owned) == len(set(owned)) == 1983


FIXTURE_FLAGS = ("TEST_FIXTURE_ONLY", "NOT_CANONICAL", "NOT_WORLD_HISTORY",
                 "NOT_PRODUCTION_INPUT")


def _feg_fixture():
    return FEGModel(
        "ARCANA TEST FIXTURE ONLY", "SHELLS_READY",
        tuple(NodeRecord(i, *coords, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0)
              for i, coords in enumerate(((0.0, 0.0), (1.0, 0.0),
                                          (1.0, 1.0), (0.0, 1.0)), 1)),
        (ElementRecord(1, (1, 2, 3), 7), ElementRecord(2, (1, 3, 4))),
        (FaultRecord(1, (1, 2, 3, 4), 30.0, 35.0, 0.0, 2),),
        fixture_status=FIXTURE_FLAGS,
    )


def test_feg_writer_parser_round_trip_hash_and_fortran_token_variants():
    model = _feg_fixture()
    text = write_feg(model)
    parsed = parse_feg(text, mode="SHELLS_READY", fixture_status=FIXTURE_FLAGS)
    assert normalized_feg_sha256(model) == normalized_feg_sha256(parsed)
    assert write_feg(parse_feg(write_feg(parsed), mode="SHELLS_READY",
                               fixture_status=FIXTURE_FLAGS)) == text
    assert normalized_feg_sha256(replace(model, title="different display title")) == normalized_feg_sha256(model)
    comma_text = text.replace(" ", ", ").replace("30 ", "3D1 ")
    comma_parsed = parse_feg(comma_text, mode="SHELLS_READY", fixture_status=FIXTURE_FLAGS)
    assert normalized_feg_sha256(comma_parsed) == normalized_feg_sha256(model)
    evidence = fixture_roundtrip_evidence()
    assert evidence["semantic_equality"] is True
    assert evidence["normalized_serialization_stable"] is True
    assert evidence["fixture_authority"].startswith("TEST_FIXTURE_ONLY")


def test_pre_orbdata_mode_omits_unbound_fields_without_zero_substitution():
    class Mesh:
        vertices_lat_lon = np.asarray(((0.0, 0.0), (0.0, 1.0), (1.0, 0.0)))
        triangles = np.asarray(((1, 2, 3),))

    binding = PhysicalFieldBinding({i: (12.0, 0.05) for i in (1, 2, 3)},
                                   "TEST_FIXTURE_ONLY")
    model = model_from_mesh(Mesh(), binding, title="PRE ORBDATA TEST",
                            mode="PRE_ORBDATA", fixture_status=FIXTURE_FLAGS)
    output = write_feg(model)
    parsed = parse_feg(output, mode="PRE_ORBDATA", fixture_status=FIXTURE_FLAGS)
    assert all(node.crustal_thickness_m is None for node in parsed.nodes)
    assert all(node.elevation_m == 12.0 and node.heat_flow_w_m2 == 0.05 for node in parsed.nodes)
    assert len(parsed.faults) == 0


def test_full_topology_feg_round_trip_uses_explicit_test_only_field_binding():
    mesh = load_canonical_mesh(ROOT)
    fixture_values = {node_id: (10.0, 0.03, 25_000.0, 80_000.0, -15.0, 1e-4)
                      for node_id in range(1, len(mesh.vertices_lat_lon) + 1)}
    binding = PhysicalFieldBinding(fixture_values, "TEST_FIXTURE_ONLY")
    model = model_from_mesh(mesh, binding, title="FULL GRID TEST FIXTURE",
                            fixture_status=FIXTURE_FLAGS)
    encoded = write_feg(model)
    decoded = parse_feg(encoded, mode="SHELLS_READY", fixture_status=FIXTURE_FLAGS)
    assert len(decoded.nodes) == 64_442
    assert len(decoded.elements) == 128_880
    assert len(decoded.faults) == 0
    assert normalized_feg_sha256(decoded) == normalized_feg_sha256(model)
    assert write_feg(decoded) == encoded
    assert "NOT_PRODUCTION_INPUT" in decoded.fixture_status
