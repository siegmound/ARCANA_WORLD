"""Production T0 FEG assembly from governed ARCANA authorities."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from ..pre_orbdata_runtime_package import FIELDS, MODE
from ..repository_context import resolve_external_payload_path
from .adapter import load_canonical_mesh
from .coordinates import (RUNTIME_FRAME_ID, RUNTIME_ROTATION_DEGREES,
                          prove_rigid_runtime_frame, rotation_matrices,
                          runtime_coordinates_lat_lon)
from .feg import normalized_feg_sha256, parse_feg, write_feg
from .model import PhysicalFieldBinding, model_from_mesh

ROOT_NAMES = {
    "surface": "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz",
    "projection": "R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json",
    "runtime_data": "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
    "runtime_manifest": "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json",
}
EXPECTED = {
    "surface_sha256": "31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534",
    "runtime_data_sha256": "2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584",
    "mesh_sha256": "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad",
    "node_count": 64_442,
    "triangle_count": 128_880,
    "fault_count": 0,
}
TITLE = "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1"
N1000 = 100_000


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_runtime_records(data_path: Path, manifest: dict[str, Any]) -> np.ndarray:
    raw = data_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED["runtime_data_sha256"] or digest != manifest.get("runtime_data_sha256"):
        raise ValueError("RUNTIME_PACKAGE_SHA256_MISMATCH")
    lines = raw.decode("ascii").splitlines()
    if len(lines) != EXPECTED["node_count"] + 1:
        raise ValueError("RUNTIME_PACKAGE_RECORD_COUNT_MISMATCH")
    header = lines[0].split()
    if header != [MODE, manifest.get("schema"), str(EXPECTED["node_count"])]:
        raise ValueError("RUNTIME_PACKAGE_HEADER_MISMATCH")
    matrix = np.loadtxt(io.BytesIO(b"\n".join(line.encode("ascii") for line in lines[1:])), dtype=np.float64)
    if matrix.shape != (EXPECTED["node_count"], len(FIELDS)) or not np.all(np.isfinite(matrix)):
        raise ValueError("RUNTIME_PACKAGE_SHAPE_OR_FINITE_CHECK_FAILED")
    if not np.array_equal(matrix[:, 0], np.arange(1, EXPECTED["node_count"] + 1, dtype=np.float64)):
        raise ValueError("RUNTIME_PACKAGE_NODE_IDS_NOT_CANONICAL")
    return matrix


def _owner_cells(projection: dict[str, Any]) -> np.ndarray:
    lineage = projection.get("lineage")
    if not isinstance(lineage, list) or len(lineage) != EXPECTED["node_count"]:
        raise ValueError("HEAT_FLOW_OWNER_LINEAGE_COUNT_MISMATCH")
    owners = np.empty((EXPECTED["node_count"], 2), dtype=np.int64)
    for index, row in enumerate(lineage):
        if row.get("node_id") != index + 1:
            raise ValueError("HEAT_FLOW_OWNER_NODE_ID_MISMATCH")
        owner = row.get("numerical_owner_cell_row_col")
        if not isinstance(owner, list) or len(owner) != 2:
            raise ValueError(f"HEAT_FLOW_OWNER_MISSING:{index + 1}")
        owners[index] = owner
    return owners


def materialize_production_feg(root: str | Path) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Return deterministic FEG bytes plus manifest and qualification evidence."""
    root = Path(root).resolve()
    surface_path = root / ROOT_NAMES["surface"]
    projection_path = root / ROOT_NAMES["projection"]
    runtime_path = root / ROOT_NAMES["runtime_data"]
    runtime_manifest_path = root / ROOT_NAMES["runtime_manifest"]
    for path in (surface_path, projection_path, runtime_path, runtime_manifest_path):
        if not path.is_file():
            raise ValueError(f"REQUIRED_GOVERNED_INPUT_MISSING:{path.name}")
    partition_manifest = json.loads((root / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    partition_payload = resolve_external_payload_path(root, partition_manifest["payload"]["path"])
    source_paths = {"canonical_partition_payload": partition_payload,
                    "surface_closed_package": surface_path,
                    "heat_flow_projection": projection_path,
                    "runtime_package": runtime_path,
                    "runtime_package_manifest": runtime_manifest_path}
    source_hashes_before = {name: _sha(path) for name, path in source_paths.items()}
    if source_hashes_before["surface_closed_package"] != EXPECTED["surface_sha256"]:
        raise ValueError("SURFACE_CLOSED_PACKAGE_SHA256_MISMATCH")
    if source_hashes_before["runtime_package"] != EXPECTED["runtime_data_sha256"]:
        raise ValueError("RUNTIME_PACKAGE_SHA256_MISMATCH")

    mesh = load_canonical_mesh(root)
    if mesh.normalized_sha256 != EXPECTED["mesh_sha256"]:
        raise ValueError("CANONICAL_MESH_SHA256_MISMATCH")
    if (len(mesh.vertices_lat_lon) != EXPECTED["node_count"]
            or len(mesh.triangles) != EXPECTED["triangle_count"]):
        raise ValueError("CANONICAL_MESH_COUNT_MISMATCH")
    canonical_vertices = mesh.vertices_lat_lon.copy()
    canonical_triangles = mesh.triangles.copy()

    projection = json.loads(projection_path.read_text(encoding="utf-8"))
    claimed_replay = projection.pop("replay_sha256", None)
    actual_replay = hashlib.sha256(json.dumps(
        projection, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    if claimed_replay != actual_replay:
        raise ValueError("HEAT_FLOW_PROJECTION_REPLAY_HASH_MISMATCH")
    projection["replay_sha256"] = claimed_replay
    if (projection.get("mesh_sha256") != EXPECTED["mesh_sha256"]
            or projection.get("node_count") != EXPECTED["node_count"]
            or projection.get("node_unknown_count") != 0
            or projection.get("deterministic_numerical_owner_count") != EXPECTED["node_count"]
            or projection.get("projection_rule") != "LEXICOGRAPHIC_FIRST_INCIDENT_CELL"):
        raise ValueError("HEAT_FLOW_PROJECTION_AUTHORITY_MISMATCH")
    owners = _owner_cells(projection)

    runtime_manifest = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    runtime_matrix = _read_runtime_records(runtime_path, runtime_manifest)
    index = {name: FIELDS.index(name) for name in (
        "owner_row", "owner_column", "surface_heat_flow_w_m2",
        "crust_thickness_m", "mantle_lithosphere_thickness_m")}
    if not np.array_equal(runtime_matrix[:, index["owner_row"]:index["owner_column"] + 1], owners):
        raise ValueError("RUNTIME_PACKAGE_OWNER_DIFFERS_FROM_GOVERNED_PROJECTION")

    with np.load(surface_path, allow_pickle=False) as archive:
        surface_elevation = archive["total_surface_elevation_m"].copy()
    if surface_elevation.shape != (180, 360):
        raise ValueError("SURFACE_ELEVATION_SHAPE_MISMATCH")
    elevation = surface_elevation[owners[:, 0], owners[:, 1]]
    if not np.all(np.isfinite(elevation)):
        raise ValueError("SURFACE_ELEVATION_OWNER_COVERAGE_INCOMPLETE")
    heat_flow = runtime_matrix[:, index["surface_heat_flow_w_m2"]]
    crust = runtime_matrix[:, index["crust_thickness_m"]]
    mantle = runtime_matrix[:, index["mantle_lithosphere_thickness_m"]]
    if (not np.array_equal(heat_flow, np.asarray(projection["heat_flow_w_m2"], dtype=np.float64))
            or not np.all(np.isfinite(heat_flow)) or not np.all(np.isfinite(crust))
            or not np.all(np.isfinite(mantle))):
        raise ValueError("RUNTIME_PHYSICAL_FIELD_BINDING_INVALID")

    runtime_coordinates = runtime_coordinates_lat_lon(canonical_vertices)
    frame_proof = prove_rigid_runtime_frame(canonical_vertices, runtime_coordinates,
                                            canonical_triangles)
    node_values = {
        node_id: (float(elevation[node_id - 1]), float(heat_flow[node_id - 1]),
                  float(crust[node_id - 1]), float(mantle[node_id - 1]), 0.0, 0.0)
        for node_id in range(1, EXPECTED["node_count"] + 1)
    }
    binding = PhysicalFieldBinding(node_values, "GOVERNED_ARCANA_T0_RUNTIME_BINDING")
    model = model_from_mesh(mesh, binding, title=TITLE,
                            coordinates_lat_lon=runtime_coordinates)
    from dataclasses import replace
    model = replace(model, n1000=N1000, brief=True)
    if len(model.faults) != EXPECTED["fault_count"]:
        raise ValueError("PRODUCTION_FEG_FAULT_COUNT_MISMATCH")
    text = write_feg(model)
    parsed = parse_feg(text, mode="SHELLS_READY")
    roundtrip_text = write_feg(parsed)
    if roundtrip_text != text or normalized_feg_sha256(parsed) != normalized_feg_sha256(model):
        raise ValueError("PRODUCTION_FEG_PARSE_WRITE_ROUNDTRIP_FAILED")
    for node_id, record in enumerate(parsed.nodes, 1):
        expected = node_values[node_id]
        actual = (record.elevation_m, record.heat_flow_w_m2,
                  record.crustal_thickness_m, record.mantle_lithosphere_thickness_m,
                  record.chemical_density_anomaly_kg_m3, record.cooling_curvature_k_m2)
        if actual != expected:
            raise ValueError(f"PRODUCTION_FEG_FIELD_BINDING_MISMATCH:{node_id}")
    if not np.array_equal(mesh.vertices_lat_lon, canonical_vertices) or not np.array_equal(mesh.triangles, canonical_triangles):
        raise ValueError("CANONICAL_MESH_MUTATED_DURING_RUNTIME_FRAME_MATERIALIZATION")
    source_hashes_after = {name: _sha(path) for name, path in source_paths.items()}
    if source_hashes_before != source_hashes_after:
        raise ValueError("CANONICAL_INPUT_HASH_CHANGED_DURING_MATERIALIZATION")

    forward, inverse = rotation_matrices()
    normalized_sha = normalized_feg_sha256(parsed)
    raw = text.encode("utf-8")
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    manifest = {
        "schema": "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1",
        "source_git_commit": commit,
        "canonical_mesh": {"normalized_sha256": mesh.normalized_sha256,
            "node_count": len(mesh.vertices_lat_lon), "triangle_count": len(mesh.triangles),
            "fault_count": 0, "canonical_mesh_mutated": False},
        "runtime_coordinate_frame": {
            "frame_id": RUNTIME_FRAME_ID,
            "rotation_axis": "CARTESIAN_POSITIVE_X",
            "rotation_degrees": RUNTIME_ROTATION_DEGREES,
            "forward_rotation_matrix": forward.tolist(),
            "inverse_rotation_matrix": inverse.tolist(),
            "rationale": "Proper rigid rotation by half the native one-degree ARCANA grid spacing avoids ShellSet's exact-pole rejection; canonical coordinates and topology remain unchanged.",
            **frame_proof,
        },
        "source_authorities": {
            "surface_closed_package": {"path": ROOT_NAMES["surface"], "sha256": source_hashes_before["surface_closed_package"],
                "field": "total_surface_elevation_m", "authority": "GOVERNED_T0_FIELD_NUMERICAL_DERIVED_SUPPORT"},
            "heat_flow_projection": {"path": ROOT_NAMES["projection"], "sha256": source_hashes_before["heat_flow_projection"],
                "replay_sha256": claimed_replay, "owner_rule": "LEXICOGRAPHIC_FIRST_INCIDENT_CELL"},
            "runtime_package": {"path": ROOT_NAMES["runtime_data"], "sha256": source_hashes_before["runtime_package"],
                "manifest_path": ROOT_NAMES["runtime_manifest"], "manifest_sha256": source_hashes_before["runtime_package_manifest"],
                "authority": "NUMERICAL_RUNTIME_INPUT_ONLY"},
            "canonical_partition_payload_sha256": source_hashes_before["canonical_partition_payload"],
        },
        "production_feg": {"title_marker": TITLE, "mode": "SHELLS_READY",
            "header": {"numNod": EXPECTED["node_count"], "nRealN": EXPECTED["node_count"],
                "nFakeN": 0, "n1000": N1000, "brief": True, "serialized_brief_token": "T"},
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "normalized_sha256": normalized_sha,
            "roundtrip_semantically_identical": True,
            "roundtrip_raw_bytes_identical": True,
            "node_id_alignment_with_runtime_package": True,
            "max_absolute_runtime_latitude_deg": frame_proof["maximum_absolute_runtime_latitude_deg"],
        },
        "nodal_fields": {
            "elevation_m": {"source_field": "total_surface_elevation_m", "authority": "NUMERICAL_DERIVED_SUPPORT", "owner_bound": True},
            "heat_flow_w_m2": {"source_field": "surface_heat_flow_w_m2", "authority": "NUMERICAL_RUNTIME_INPUT_ONLY", "owner_bound": True},
            "crustal_thickness_m": {"source_field": "crust_thickness_m", "authority": "NUMERICAL_RUNTIME_INPUT_ONLY", "owner_bound": True},
            "mantle_lithosphere_thickness_m": {"source_field": "mantle_lithosphere_thickness_m", "authority": "NUMERICAL_RUNTIME_INPUT_ONLY", "owner_bound": True},
            "chemical_density_anomaly_kg_m3": {"value": 0.0, "authority": "NUMERICAL_RUNTIME_REFERENCE_COMPONENT", "physical_authority": "NOT_CANONICAL_CHEMICAL_GEOLOGY"},
            "cooling_curvature_k_m2": {"value": 0.0, "authority": "LEGACY_FEG_COMPATIBILITY_ONLY", "reason": "Explicit ARCANA runtime bypasses legacy cooling-curvature reconstruction; profile is supplied by owner-bound runtime package."},
        },
        "ownership": {"rule": "LEXICOGRAPHIC_FIRST_INCIDENT_CELL", "source": "R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json", "owner_reselected": False},
        "finite_coverage": {"elevation": EXPECTED["node_count"], "heat_flow": EXPECTED["node_count"],
            "crustal_thickness": EXPECTED["node_count"], "mantle_lithosphere_thickness": EXPECTED["node_count"],
            "chemical_density_zero": EXPECTED["node_count"], "cooling_curvature_zero": EXPECTED["node_count"], "nonfinite_values": 0},
        "physical_field_equality": {"heat_flow_exact_to_runtime_package": True,
            "crust_thickness_exact_to_runtime_package": True,
            "mantle_lithosphere_thickness_exact_to_runtime_package": True},
        "source_hashes_unchanged": source_hashes_before == source_hashes_after,
        "preserved_gates": {"runtime_authorized": False, "mechanics_authorized": False,
            "forward_evolution_authorized": False, "dt_selected": False,
            "t1_created": False, "canonical_state_changed": False},
    }
    evidence = {
        "node_count": EXPECTED["node_count"], "triangle_count": EXPECTED["triangle_count"],
        "fault_count": EXPECTED["fault_count"], "canonical_mesh_sha256": mesh.normalized_sha256,
        "runtime_coordinate_frame_id": RUNTIME_FRAME_ID,
        "max_absolute_runtime_latitude_deg": frame_proof["maximum_absolute_runtime_latitude_deg"],
        "raw_feg_sha256": manifest["production_feg"]["raw_sha256"],
        "normalized_feg_sha256": normalized_sha,
        "runtime_package_sha256": source_hashes_before["runtime_package"],
        "surface_package_sha256": source_hashes_before["surface_closed_package"],
        "heat_flow_projection_replay_sha256": claimed_replay,
        "frame_proof": frame_proof,
        "physical_field_equality": manifest["physical_field_equality"],
        "source_hashes_unchanged": source_hashes_before == source_hashes_after,
        "gates": manifest["preserved_gates"],
    }
    return text, manifest, evidence


def write_production_feg(root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    text, manifest, evidence = materialize_production_feg(root)
    (root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg").write_text(text, encoding="utf-8", newline="\n")
    manifest_path = root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n",
                             encoding="utf-8", newline="\n")
    closure = {
        "schema": "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE_V1",
        "decision": "PASS_R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_AND_MATERIALIZATION",
        "production_feg_manifest": manifest_path.name,
        "evidence": evidence,
        "preserved_gates": manifest["preserved_gates"],
        "runtime_or_mechanics_qualification_claimed": False,
    }
    (root / "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json").write_text(
        json.dumps(closure, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# R6 PRE_ORBDATA FEG Runtime Compatibility Closure", "",
        f"Decision: `{closure['decision']}`", "",
        "This materializes a production ShellSet FEG from governed T0/runtime inputs. It does not run ShellSet, OrbData, mechanics, or forward evolution.", "",
        "## Evidence", "",
    ]
    for key, value in evidence.items():
        lines.append(f"- `{key}`: `{json.dumps(value, sort_keys=True)}`")
    lines.extend(["", "## Preserved gates", ""])
    for key, value in manifest["preserved_gates"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}")
    lines.extend(["", "No runtime or mechanics qualification is claimed.", ""])
    (root / "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n")
    return closure
