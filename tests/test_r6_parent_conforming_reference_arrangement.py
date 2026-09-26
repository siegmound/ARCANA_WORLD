"""Numerical fixtures for canonical-parent ownership and local refinement."""
from __future__ import annotations

import math

import numpy as np
import pytest

from arcana_worldsim.r6.physical.reference_arrangement import (
    ParentFace, build_parent_conforming_reference_arrangement,
    CanonicalBoundarySpatialIndex, build_canonical_junction_bases,
    canonical_parent_faces, junction_geography, spherical_rect_area_m2,
    validate_parent_conforming_arrangement, certify_parent_region,
    classify_canonical_parent_cell, split_parent_face,
)


def _all_parents():
    rows, cols = np.indices((180, 360))
    # Deliberately shuffle input order: stable face identity is grid-derived.
    order = np.arange(64_800)[::-1]
    return canonical_parent_faces(rows.ravel()[order], cols.ravel()[order],
                                  np.zeros(64_800, dtype=np.int16))


def test_canonical_parent_ownership_is_inherited_and_sphere_area_closes():
    parents = _all_parents()
    assert len(parents) == 64_800
    assert parents[0].parent_face_id == "R6PARENT:000:000"
    assert parents[-1].parent_face_id == "R6PARENT:179:359"
    area = math.fsum(spherical_rect_area_m2(p.south_deg, p.north_deg,
                                             p.west_deg, p.east_deg) for p in parents)
    assert abs(area - 4 * math.pi * 6_371_000.0**2) / area < 1e-12


def test_local_refinement_preserves_parent_plate_and_reduces_terminal_ambiguity():
    plate_ids = np.zeros(64_800, dtype=np.int16)
    plate_ids[89 * 360 + 180] = 7
    parents = canonical_parent_faces(np.repeat(np.arange(180), 360),
                                     np.tile(np.arange(360), 180), plate_ids)
    parent_id = "R6PARENT:089:180"
    def cert(cell, _rho):
        # A meridional transition crosses just the selected parent face.
        if cell.parent_face_id == parent_id and cell.west_deg < 0.3 < cell.east_deg:
            return None, None, False
        return "RIGID_CORE", f"PLATE:{cell.plate_id}", True
    l0 = build_parent_conforming_reference_arrangement(parents, cert, 100_000, 1)
    l1 = build_parent_conforming_reference_arrangement(parents, cert, 100_000, 2)
    assert l0["refined_parent_face_count"] == l1["refined_parent_face_count"] == 1
    assert l0["ambiguous_area_m2"] > l1["ambiguous_area_m2"] > 0
    assert all(c.parent_plate_id == 7 for c in l1["cells"] if c.parent_face_id == parent_id)
    check = validate_parent_conforming_arrangement(l1)
    assert check["sphere_closure_pass"] and check["area_accounting_pass"]
    assert check["parent_face_count"] == 64_800


def test_parent_grid_rejects_duplicate_or_missing_faces():
    rows = np.zeros(64_800, dtype=np.uint8)
    cols = np.zeros(64_800, dtype=np.uint16)
    plates = np.zeros(64_800, dtype=np.int16)
    with pytest.raises(ValueError, match="complete 180x360"):
        canonical_parent_faces(rows, cols, plates)


def test_area_rejects_invalid_latitude_or_longitude_span():
    with pytest.raises(ValueError):
        spherical_rect_area_m2(-91, -90, 0, 1)
    with pytest.raises(ValueError):
        spherical_rect_area_m2(0, 1, 1, 1)


def test_lipschitz_certificates_inherit_core_and_localize_ambiguous_band():
    pairs = {"B0": (2, 7), "B1": (7, 9)}
    incident = {"J0": ("B0", "B1")}
    assert certify_parent_region(7, {"B0": 200_000, "B1": 250_000}, pairs,
                                 {"J0": 300_000}, incident, 50_000, 10_000) == (
                                     "RIGID_CORE", "PLATE:7", True)
    assert certify_parent_region(7, {"B0": 30_000, "B1": 250_000}, pairs,
                                 {"J0": 300_000}, incident, 50_000, 10_000) == (
                                     "BOUNDARY_ZONE", "B0", True)
    category, _, proven = certify_parent_region(7, {"B0": 55_000, "B1": 250_000}, pairs,
                                                 {"J0": 300_000}, incident, 50_000, 10_000)
    assert category == "MIXED_REQUIRES_REFINEMENT" and not proven


def test_junction_certificate_supersedes_its_three_incident_corridors():
    boundaries = {f"B{i}": 0.0 for i in range(3)}
    pairs = {"B0": (1, 2), "B1": (2, 3), "B2": (1, 3)}
    result = certify_parent_region(2, boundaries, pairs, {"J": 10.0},
                                   {"J": ("B0", "B1", "B2")}, 100.0, 5.0)
    assert result == ("JUNCTION_PATCH", "J", True)


def test_canonical_style_spatial_index_keeps_boundary_identity_at_dateline():
    segments = [
        {"boundary_id": "B0", "ordered_plate_pair": [1, 2],
         "endpoint_vertex_ids": ["GRID_VERTEX:90:359", "GRID_VERTEX:90:360"]},
        {"boundary_id": "B1", "ordered_plate_pair": [1, 2],
         "endpoint_vertex_ids": ["GRID_VERTEX:90:0", "GRID_VERTEX:90:1"]},
    ]
    index = CanonicalBoundarySpatialIndex(segments)
    assert len(index.records) == 2
    assert index.records[0].component_id == index.records[1].component_id
    hits = index.query(0.0, 179.5, 100.0)
    assert hits and hits[0][0].boundary_id == "B0"
    assert hits[0][1] == pytest.approx(0.0, abs=1e-7)


def test_dateline_crossing_source_segment_midpoint_is_indexed_from_either_endpoint_order():
    segments = [
        {"boundary_id": "WRAPPED", "ordered_plate_pair": [1, 2],
         "endpoint_vertex_ids": ["GRID_VERTEX:90:0", "GRID_VERTEX:90:359"]},
    ]
    index = CanonicalBoundarySpatialIndex(segments)
    record = index.records[0]
    assert abs(abs(record.mid_lon_deg) - 179.5) < 1e-12
    assert index.query(0.0, record.mid_lon_deg, 0.01)[0][0].boundary_id == "WRAPPED"


def test_realistic_t_junction_is_reported_blocked_not_bent_into_convex_p1_patch():
    node = "GRID_VERTEX:90:180"
    segments = [
        {"boundary_id": "E", "ordered_plate_pair": [1, 2],
         "endpoint_vertex_ids": [node, "GRID_VERTEX:90:181"]},
        {"boundary_id": "W", "ordered_plate_pair": [1, 3],
         "endpoint_vertex_ids": ["GRID_VERTEX:90:179", node]},
        {"boundary_id": "S", "ordered_plate_pair": [2, 3],
         "endpoint_vertex_ids": ["GRID_VERTEX:89:180", node]},
    ]
    junctions = [{"junction_id": "J-T", "vertex_id": node, "degree": 3,
                  "incident_boundary_ids": ["E", "W", "S"]}]
    index = CanonicalBoundarySpatialIndex(segments)
    patch, = build_canonical_junction_bases(junctions, index, 2.0)
    assert patch["status"] == "BLOCKED"
    assert "nondegenerate convex three-side P1 patch" in patch["reason"]


def test_real_canonical_style_parent_cell_classifier_certifies_corridor_and_core():
    segments = [{"boundary_id": "B", "ordered_plate_pair": [1, 2],
                 "endpoint_vertex_ids": ["GRID_VERTEX:90:10", "GRID_VERTEX:90:11"]}]
    index = CanonicalBoundarySpatialIndex(segments)
    south = ParentFace("R6PARENT:089:010", 1, 89, 10, -1, 0, -170, -169)
    near = south
    for _ in range(4):
        near = split_parent_face(near)[2]  # deterministic north-west child
    result = classify_canonical_parent_cell(near, index, (), width_m=100_000)
    assert result["category"] == "BOUNDARY_ZONE"
    assert result["canonical_boundary_ids"] == ("B",)
    assert result["certified"] is True

    far = ParentFace("R6PARENT:089:010", 1, 89, 10, -1, 0, -170, -169)
    far_result = classify_canonical_parent_cell(far, index, (), width_m=100_000)
    assert far_result["category"] == "MIXED_REQUIRES_REFINEMENT"
    # A sufficiently distant canonical parent face inherits its parent owner.
    distant = ParentFace("R6PARENT:120:100", 1, 120, 100, 30, 31, -80, -79)
    core = classify_canonical_parent_cell(distant, index, (), width_m=100_000)
    assert core["category"] == "RIGID_CORE" and core["certified"] is True
