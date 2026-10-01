from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pytest

from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
from arcana_worldsim.r6.shellset_mesh import (
    RUNTIME_FRAME_ID, load_canonical_mesh, normalized_feg_sha256, parse_feg,
    prove_rigid_runtime_frame, runtime_coordinates_lat_lon, write_feg,
)
from arcana_worldsim.r6.shellset_mesh.materialization import (
    EXPECTED, N1000, TITLE, materialize_production_feg,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def materialized():
    first = materialize_production_feg(ROOT)
    second = materialize_production_feg(ROOT)
    return first, second


def test_production_feg_binds_existing_canonical_mesh_and_runtime_package(materialized):
    (text, manifest, evidence), (text_again, manifest_again, evidence_again) = materialized
    model = parse_feg(text, mode="SHELLS_READY")
    mesh = load_canonical_mesh(ROOT)
    assert mesh.normalized_sha256 == EXPECTED["mesh_sha256"]
    assert manifest["canonical_mesh"]["canonical_mesh_mutated"] is False
    assert len(model.nodes) == EXPECTED["node_count"] == 64_442
    assert len(model.elements) == EXPECTED["triangle_count"] == 128_880
    assert len(model.faults) == EXPECTED["fault_count"] == 0
    assert [n.node_id for n in model.nodes] == list(range(1, 64_443))
    assert [e.element_id for e in model.elements] == list(range(1, 128_881))
    assert [e.node_ids for e in model.elements] == [tuple(map(int, row)) for row in mesh.triangles]


def test_production_feg_header_marker_and_runtime_coordinate_frame(materialized):
    text, manifest, evidence = materialized[0]
    first, header = text.splitlines()[:2]
    values = header.split()
    model = parse_feg(text, mode="SHELLS_READY")
    assert first.startswith(TITLE)
    assert values[:4] == ["64442", "64442", "0", "100000"]
    assert values[4] == "T"
    assert model.brief is True and model.n1000 == 100_000
    latitudes = np.asarray([node.latitude_deg for node in model.nodes])
    assert np.max(np.abs(latitudes)) < 89.99
    assert manifest["runtime_coordinate_frame"]["frame_id"] == RUNTIME_FRAME_ID
    assert manifest["runtime_coordinate_frame"]["rotation_axis"] == "CARTESIAN_POSITIVE_X"
    assert manifest["runtime_coordinate_frame"]["rotation_degrees"] == 0.5


def test_rigid_transform_preserves_mesh_geometry_and_has_exact_inverse():
    mesh = load_canonical_mesh(ROOT)
    canonical = mesh.vertices_lat_lon.copy()
    runtime = runtime_coordinates_lat_lon(canonical)
    proof = prove_rigid_runtime_frame(canonical, runtime, mesh.triangles)
    assert proof["all_checks_pass"] is True
    assert proof["orthonormal"] is True
    assert proof["determinant"] == pytest.approx(1.0, abs=2e-15)
    assert proof["unique_mesh_edge_count"] == 193_320
    assert proof["triangle_count"] == 128_880
    assert proof["zero_area_triangles"] == 0
    assert proof["maximum_absolute_runtime_latitude_deg"] < 89.99
    assert np.array_equal(mesh.vertices_lat_lon, canonical)


def test_nodal_fields_are_owner_bound_and_exactly_match_runtime_authority(materialized):
    text, manifest, evidence = materialized[0]
    model = parse_feg(text, mode="SHELLS_READY")
    data = (ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat").read_text(encoding="ascii").splitlines()
    records = np.asarray([[float(v) for v in line.split()] for line in data[1:]], dtype=np.float64)
    positions = {name: FIELDS.index(name) for name in (
        "surface_heat_flow_w_m2", "crust_thickness_m", "mantle_lithosphere_thickness_m")}
    assert manifest["ownership"]["owner_reselected"] is False
    assert manifest["finite_coverage"]["elevation"] == 64_442
    for i, node in enumerate(model.nodes):
        assert node.heat_flow_w_m2 == records[i, positions["surface_heat_flow_w_m2"]]
        assert node.crustal_thickness_m == records[i, positions["crust_thickness_m"]]
        assert node.mantle_lithosphere_thickness_m == records[i, positions["mantle_lithosphere_thickness_m"]]
        assert node.chemical_density_anomaly_kg_m3 == 0.0
        assert node.cooling_curvature_k_m2 == 0.0
        assert np.isfinite((node.longitude_deg, node.latitude_deg, node.elevation_m,
                            node.heat_flow_w_m2, node.crustal_thickness_m,
                            node.mantle_lithosphere_thickness_m)).all()
    assert evidence["physical_field_equality"] == {
        "heat_flow_exact_to_runtime_package": True,
        "crust_thickness_exact_to_runtime_package": True,
        "mantle_lithosphere_thickness_exact_to_runtime_package": True,
    }
    assert manifest["nodal_fields"]["chemical_density_anomaly_kg_m3"]["authority"] == "NUMERICAL_RUNTIME_REFERENCE_COMPONENT"
    assert manifest["nodal_fields"]["chemical_density_anomaly_kg_m3"]["physical_authority"] == "NOT_CANONICAL_CHEMICAL_GEOLOGY"


def test_materialization_roundtrip_and_replay_are_byte_deterministic(materialized):
    (first, manifest, evidence), (second, manifest_again, evidence_again) = materialized
    text, parsed_manifest, parsed_evidence = first, manifest, evidence
    model = parse_feg(text, mode="SHELLS_READY")
    assert write_feg(model) == text
    assert normalized_feg_sha256(model) == parsed_manifest["production_feg"]["normalized_sha256"]
    assert text.encode("utf-8") == second.encode("utf-8")
    assert manifest == manifest_again
    assert evidence == evidence_again
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == evidence["raw_feg_sha256"]
    assert evidence["source_hashes_unchanged"] is True
    assert manifest["preserved_gates"] == {
        "runtime_authorized": False, "mechanics_authorized": False,
        "forward_evolution_authorized": False, "dt_selected": False,
        "t1_created": False, "canonical_state_changed": False,
    }


def test_feg_logical_parser_and_production_capacity_fail_closed():
    from dataclasses import replace
    from arcana_worldsim.r6.shellset_mesh import FEGModel, NodeRecord, write_feg

    nodes = tuple(NodeRecord(i, lon, lat, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0)
                  for i, (lat, lon) in enumerate(((0.0, 0.0), (0.0, 1.0), (1.0, 0.0)), 1))
    from arcana_worldsim.r6.shellset_mesh import ElementRecord
    model = FEGModel(TITLE, "SHELLS_READY", nodes, (ElementRecord(1, (1, 2, 3)),), (), n1000=N1000, brief=True)
    text = write_feg(model)
    assert parse_feg(text.replace(" 100000 T", " 100000 .TRUE."), mode="SHELLS_READY").brief is True
    assert parse_feg(text.replace(" 100000 T", " 100000 F"), mode="SHELLS_READY").brief is False
    assert parse_feg(text.replace(" 100000 T", " 100000 1"), mode="SHELLS_READY").brief is True
    with pytest.raises(ValueError, match="Fortran logical"):
        parse_feg(text.replace(" 100000 T", " 100000 2"), mode="SHELLS_READY")
    with pytest.raises(ValueError, match="n1000"):
        write_feg(replace(model, n1000=2))


def test_static_source_contract_prevents_legacy_header_and_pole_regressions():
    feg_source = (ROOT / "src/arcana_worldsim/r6/shellset_mesh/feg.py").read_text(encoding="utf-8")
    frame_source = (ROOT / "src/arcana_worldsim/r6/shellset_mesh/coordinates.py").read_text(encoding="utf-8")
    mesh_source = (ROOT / "src/arcana_worldsim/r6/shellset_mesh/adapter.py").read_text(encoding="utf-8")
    assert "len(ids) > model.n1000" in feg_source
    assert "_brief_token(model.brief)" in feg_source
    assert "{model.brief}" not in feg_source
    assert "RUNTIME_ROTATION_DEGREES = 0.5" in frame_source
    assert "runtime_coordinates_lat_lon" in frame_source
    assert "canonical_lat_lon" in frame_source
    assert not re.search(r"_vertex\([^\n]*\).*89\.99", mesh_source)
