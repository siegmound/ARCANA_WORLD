"""T0 B5 boundary binding and short experimental two-column mechanics pilot.

Topology and T0 relative motion are loaded from the existing B4/B5 authority.
There is no positive-time boundary law. The opening trajectory, spring
stiffnesses, Deep stocks/mobility, and optional cross-boundary Deep conductance
are explicit synthetic engineering inputs and are never scientific authority.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tracemalloc
from time import perf_counter
from typing import Any, Iterator, Mapping

import numpy as np

from .deep_geological_physics_pilot import ModalMaterial
from .functional_development import ReducedState, pure_shear_thermal_step
from .functional_spatial_support import (
    GRID_COLUMNS,
    GRID_ROWS,
    audit_pair_5_11,
    exact_face_plate_lookup,
    incident_cells,
    local_edge_frame,
)
from .integrated_geological_microdomain import (
    ARCHIVE_SHA256,
    ROLE_MODAL_PARAMETERS,
    SUPPORT_RECORDS,
    _column_geometry,
    _deep_transport_step,
    _modal_response_by_role,
    _sha256_json,
    _state_digest,
    load_microdomain_inputs,
)
from .plate_support_adapter import load_b5_sources, _grid_vertex_node
from .plate_kinematics_adapter import load_governed_source, _tracked_identity
from .plate_support_adapter import B5_TRACKED
from .tectonic_deep_pilot import SECONDS_PER_YEAR, conservative_two_cell_transport

DEFAULT_BOUNDARY_EDGE = {"row": 91, "column": 28, "axis": "EAST"}
DEFAULT_ENGINEERING_CONFIG = {
    "steps": 3,
    "step_years": 1.0,
    "synthetic_total_opening_m": 0.03,
    "column_stiffness_a_n_per_m": 2_000_000.0,
    "interface_stiffness_n_per_m": 1_000_000.0,
    "column_stiffness_b_n_per_m": 2_000_000.0,
    "strike_length_m": 1.0,
    "deep_vertical_mobility_per_year": 0.01,
    "deep_initial_density_j_m3_by_role": {
        "CONTINENTAL_CRUST_REFERENCE": 1.0,
        "LITHOSPHERIC_MANTLE_REFERENCE": 0.25,
    },
    "synthetic_support_b_deep_stock_multiplier": 1.10,
    "lateral_deep_base_fraction_per_step": 0.05,
    "lateral_deep_gap_gain_per_m": 10.0,
}
CACHE_IMPLEMENTATION_PATHS = (
    "src/arcana_worldsim/r6/plate_support_adapter.py",
    "src/arcana_worldsim/r6/plate_kinematics_adapter.py",
    "src/arcana_worldsim/r6/functional_spatial_support.py",
    "src/arcana_worldsim/r6/tectonic_boundary_microdomain.py",
    "src/arcana_worldsim/r6/integrated_geological_microdomain.py",
    "src/arcana_worldsim/r6/functional_development.py",
    "src/arcana_worldsim/r6/tectonic_deep_pilot.py",
)


@contextmanager
def _external_root_scope(path: str | Path) -> Iterator[None]:
    key = "ARCANA_EXTERNAL_ROOT"
    previous = os.environ.get(key)
    os.environ[key] = str(Path(path).resolve())
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


def _raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cached_view_source_identity(repository_root: Path, external_root: Path,
                                 expected_branch: str) -> tuple[str, str, str, list[dict[str, Any]]]:
    """Verify source closure cheaply, without rebuilding global B5 mesh topology.

    The governed B4 loader rechecks its tracked authorities and payload digests.
    B5's tracked members are checked against the current Git tree. The full
    global mesh and 1,983-edge audit are intentionally not reconstructed here.
    """
    root = repository_root.resolve()
    branch = subprocess.run(["git", "-C", str(root), "branch", "--show-current"],
                            check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if branch != expected_branch:
        raise ValueError("B5_VIEW_CACHE_BRANCH_MISMATCH")
    with _external_root_scope(external_root):
        kinematics, inventory = load_governed_source(root, expected_branch=expected_branch)
        tracked = [_tracked_identity(root, path) for path in B5_TRACKED]
        # Hash each governed source member directly. This uses the source
        # inventory but avoids B5's global-mesh reconstruction and pair audit.
        files: list[dict[str, Any]] = []
        for row in inventory["tracked_authority_documents"]:
            path = root / str(row["logical_path"])
            digest, size, _ = _file_sha_size(path)
            files.append({"logical_path": str(row["logical_path"]), "path_kind": "REPOSITORY",
                          "path": str(path.resolve()), "sha256": digest, "byte_size": size})
        for row in inventory["payload_artifacts"]:
            logical = str(row["logical_path"])
            path = inventory["_payload_paths_internal"].get(logical)
            if path is None:
                path = root / logical
            path = Path(path).resolve()
            digest, size, _ = _file_sha_size(path)
            files.append({"logical_path": logical,
                          "path_kind": "EXTERNAL" if logical.startswith("external://") else "REPOSITORY",
                          "path": str(path), "sha256": digest, "byte_size": size})
        for row in tracked:
            path = root / str(row["logical_path"])
            digest, size, _ = _file_sha_size(path)
            files.append({"logical_path": str(row["logical_path"]), "path_kind": "REPOSITORY",
                          "path": str(path.resolve()), "sha256": digest, "byte_size": size})
        for logical in CACHE_IMPLEMENTATION_PATHS:
            path = root / logical
            digest, size, _ = _file_sha_size(path)
            files.append({"logical_path": logical, "path_kind": "IMPLEMENTATION",
                          "path": str(path.resolve()), "sha256": digest, "byte_size": size})
    # Same identity equation as load_b5_sources(), using verified manifests.
    source_identity = _sha256_json({
        "head": head,
        "tracked_sources": [{"path": row["logical_path"], "sha256": row["sha256"]}
                            for row in sorted((*inventory["tracked_authority_documents"], *tracked),
                                              key=lambda value: value["logical_path"])],
        "payloads": [{"path": row["logical_path"], "sha256": row["sha256"]}
                     for row in inventory["payload_artifacts"]],
    })
    if kinematics.head != head:
        raise ValueError("B5_VIEW_CACHE_HEAD_CHANGED_DURING_VERIFICATION")
    return branch, head, source_identity, files


def _file_sha_size(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size, path.stat().st_mtime_ns


def boundary_view_cache_default_path(repository_root: str | Path) -> Path:
    """Return an immutable cache name bound to HEAD and the view implementation."""
    root = Path(repository_root).resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()
    digest = hashlib.sha256()
    for logical_path in CACHE_IMPLEMENTATION_PATHS:
        digest.update(logical_path.encode("utf-8"))
        digest.update((root / logical_path).read_bytes())
    return root / "outputs/r6_experimental_multiphysics/_cache" / (
        f"B5_T0_EDGE_VIEW_{head}_{digest.hexdigest()[:16]}.json")


def _view_digest(binding: Mapping[str, Any]) -> str:
    payload = json.dumps(binding, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_cached_edge_content(binding: Mapping[str, Any], root: Path,
                                  current_files: list[dict[str, Any]]) -> None:
    """Cross-check cached local edge fields against the small governed inputs."""
    files = {(row["logical_path"], row["path_kind"]): Path(row["path"])
             for row in current_files}
    vector_logical = "external://r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz"
    vector_path = files[(vector_logical, "EXTERNAL")]
    with np.load(vector_path, allow_pickle=False) as vector:
        lookup = exact_face_plate_lookup(vector["face_row"], vector["face_col"],
            vector["face_plate_id"], rows=GRID_ROWS, columns=GRID_COLUMNS)
    expected_cells = []
    for cell, support in (((91, 28), "R6G1D-R091-C028"),
                          ((91, 29), "R6G1D-R091-C029")):
        expected_cells.append({"support_id": support, "grid_cell": list(cell),
                               "plate_id": int(lookup[cell])})
    if binding.get("support_cells") != expected_cells or {x["plate_id"] for x in expected_cells} != {5, 11}:
        raise ValueError("B5_VIEW_CACHE_LOCAL_CELL_PLATE_BINDING_MISMATCH")
    edge = binding.get("boundary", {})
    census_path = files[("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json", "REPOSITORY")]
    state_path = files[("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json", "REPOSITORY")]
    census = json.loads(census_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    matches = [row for row in census.get("segments", [])
               if row.get("parent_grid_edge") == DEFAULT_BOUNDARY_EDGE]
    if len(matches) != 1:
        raise ValueError("B5_VIEW_CACHE_EDGE_SOURCE_ROW_NOT_UNIQUE")
    source_row = matches[0]
    boundary_id = source_row.get("boundary_id")
    state_matches = [row for row in state.get("segments", [])
                     if row.get("boundary_id") == boundary_id]
    if len(state_matches) != 1:
        raise ValueError("B5_VIEW_CACHE_EDGE_STATE_ROW_NOT_UNIQUE")
    state_row = state_matches[0]
    if (edge.get("boundary_id") != boundary_id
            or edge.get("ordered_plate_pair") != [5, 11]
            or edge.get("parent_grid_edge") != DEFAULT_BOUNDARY_EDGE
            or tuple(sorted(int(x) for x in source_row.get("ordered_plate_pair", ()))) != (5, 11)
            or float(edge.get("length_m", -1.0)) != float(source_row.get("length_m", -2.0))
            or edge.get("support") != source_row.get("support")
            or source_row.get("endpoint_vertex_ids") != state_row.get("endpoint_vertex_ids")
            or edge.get("endpoint_node_ids") != sorted(_grid_vertex_node(str(value))
                                                          for value in source_row["endpoint_vertex_ids"])):
        raise ValueError("B5_VIEW_CACHE_EDGE_GEOMETRY_BINDING_MISMATCH")
    radial, forward, tangent = local_edge_frame(91, 28, "EAST", 6_371_000.0)
    plate_5_is_first = expected_cells[0]["plate_id"] == 5
    normal = forward if plate_5_is_first else -forward
    for key, expected in (("grid_forward_unit_vector", forward),
                          ("plate_5_to_plate_11_normal_unit_vector", normal),
                          ("radial_unit_vector_at_edge_midpoint", radial),
                          ("positive_tangent_unit_vector", tangent)):
        if not np.allclose(np.asarray(edge.get(key), dtype=float), expected, rtol=0.0, atol=1e-15):
            raise ValueError(f"B5_VIEW_CACHE_ORIENTATION_MISMATCH:{key}")
    if (edge.get("positive_duration_validity") != "UNKNOWN"
            or edge.get("t0_velocity_used_as_positive_time_forcing") is not False
            or binding.get("time_scope") != "T0_INSTANT_ONLY_NO_POSITIVE_DURATION_VALIDITY"):
        raise ValueError("B5_VIEW_CACHE_TEMPORAL_SCOPE_WIDENED")
    audit = binding.get("pair_5_11_audit", {})
    if (audit.get("section_eligibility") != "ELIGIBLE"
            or audit.get("material_admissibility") != "PASS_B6N8N_ADMITTED"):
        raise ValueError("B5_VIEW_CACHE_AUDIT_STATUS_INVALID")


def load_cached_t0_boundary_view(cache_path: str | Path, repository_root: str | Path,
                                 external_root: str | Path, *,
                                 expected_branch: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load a previously full-audited edge view after source-hash revalidation."""
    path = Path(cache_path).resolve()
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema") != "ARCANA_B5_T0_EDGE_VIEW_CACHE_V1":
        raise ValueError("B5_VIEW_CACHE_SCHEMA_INVALID")
    binding = record.get("binding")
    if not isinstance(binding, dict) or _view_digest(binding) != record.get("binding_sha256"):
        raise ValueError("B5_VIEW_CACHE_BINDING_DIGEST_MISMATCH")
    branch, head, source_identity, current_files = _cached_view_source_identity(
        Path(repository_root), Path(external_root), expected_branch)
    if (branch != record.get("source_branch") or head != record.get("source_head")
            or source_identity != record.get("source_identity_sha256")
            or binding.get("source_identity_sha256") != source_identity):
        raise ValueError("B5_VIEW_CACHE_SOURCE_IDENTITY_MISMATCH")
    expected_files = record.get("source_files")
    if not isinstance(expected_files, list):
        raise ValueError("B5_VIEW_CACHE_SOURCE_FILE_CLOSURE_MISSING")
    current_by_key = {(row["logical_path"], row["path_kind"]): row for row in current_files}
    if {(row.get("logical_path"), row.get("path_kind")) for row in expected_files} != set(current_by_key):
        raise ValueError("B5_VIEW_CACHE_SOURCE_FILE_MEMBERSHIP_MISMATCH")
    for row in expected_files:
        current = current_by_key[(row["logical_path"], row["path_kind"])]
        if (row.get("sha256") != current["sha256"] or row.get("byte_size") != current["byte_size"]
                or Path(row.get("path", "")).resolve() != Path(current["path"]).resolve()):
            raise ValueError(f"B5_VIEW_CACHE_SOURCE_FILE_CHANGED:{row['logical_path']}")
    _validate_cached_edge_content(binding, Path(repository_root).resolve(), current_files)
    if binding.get("boundary", {}).get("boundary_id") != "R6BND-T0-3eb57747e6f0a3f3305f":
        raise ValueError("B5_VIEW_CACHE_WRONG_BOUNDARY")
    if [row.get("support_id") for row in binding.get("support_cells", [])] != [
            "R6G1D-R091-C028", "R6G1D-R091-C029"]:
        raise ValueError("B5_VIEW_CACHE_SUPPORTS_INVALID")
    return binding, {"mode": "VERIFIED_CACHE_REUSE_NO_GLOBAL_TOPOLOGY_REBUILD",
                     "source_file_count": len(current_files), "source_identity_sha256": source_identity}


def _write_view_cache(cache_path: str | Path, binding: Mapping[str, Any], *,
                      source_files: list[dict[str, Any]]) -> None:
    path = Path(cache_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    branch = binding["source_branch"]
    head = binding["source_head"]
    record = {"schema": "ARCANA_B5_T0_EDGE_VIEW_CACHE_V1", "source_branch": branch,
        "source_head": head, "source_identity_sha256": binding["source_identity_sha256"],
        "source_files": source_files, "binding_sha256": _view_digest(binding),
        "binding": binding,
        "authority_limit": "REUSE_OF_PRIOR_FULL_B5_T0_AUDIT; T0_ONLY; NO_POSITIVE_TIME_MECHANICAL_AUTHORITY"}
    data = (json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _cache_source_files(root: Path, sources: Any, inventory: Mapping[str, Any]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for row in inventory["source_documents"]:
        logical = str(row["logical_path"])
        path = root / logical
        digest, size, _ = _file_sha_size(path)
        files.append({"logical_path": logical, "path_kind": "REPOSITORY",
                      "path": str(path.resolve()), "sha256": digest, "byte_size": size})
    for row in inventory["payload_artifacts"]:
        logical = str(row["logical_path"])
        path = sources.payload_paths.get(logical, root / logical)
        path = Path(path).resolve()
        digest, size, _ = _file_sha_size(path)
        files.append({"logical_path": logical,
                      "path_kind": "EXTERNAL" if logical.startswith("external://") else "REPOSITORY",
                      "path": str(path), "sha256": digest, "byte_size": size})
    for logical in CACHE_IMPLEMENTATION_PATHS:
        path = root / logical
        digest, size, _ = _file_sha_size(path)
        files.append({"logical_path": logical, "path_kind": "IMPLEMENTATION",
                      "path": str(path.resolve()), "sha256": digest, "byte_size": size})
    return files


def build_t0_boundary_binding(
    repository_root: str | Path,
    external_root: str | Path,
    archive_path: str | Path,
    *,
    loaded_inputs: list[tuple[ReducedState, dict[str, Any]]] | None = None,
    verified_archive_digest: str | None = None,
    cache_path: str | Path | None = None,
    cache_timings: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Bind the R091 C028/C029 edge to verified B5 T0 cell/plate topology."""
    root = Path(repository_root).resolve()
    archive = Path(archive_path).resolve()
    branch = os.environ.get("ARCANA_EXPECTED_BRANCH") or __import__("subprocess").run(
        ["git", "branch", "--show-current"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if loaded_inputs is None:
        loaded, archive_digest = load_microdomain_inputs(str(archive))
    else:
        loaded = loaded_inputs
        archive_digest = verified_archive_digest
        if not archive_digest:
            raise ValueError("PRELOADED_ARCHIVE_DIGEST_REQUIRED")
    if archive_digest != ARCHIVE_SHA256:
        raise ValueError("MICRODOMAIN_ARCHIVE_SHA256_MISMATCH")
    if cache_path is not None and Path(cache_path).is_file():
        t_cache = perf_counter()
        binding, cache_audit = load_cached_t0_boundary_view(
            cache_path, root, external_root, expected_branch=branch)
        if cache_timings is not None:
            cache_timings["verified_cache_load_seconds"] = perf_counter() - t_cache
            cache_timings["cache_validation_mode"] = cache_audit["mode"]
        expected_records = binding.get("eng10k_profile_binding_checks", {})
        by_support = {meta["support_id"]: (state, meta) for state, meta in loaded}
        if set(by_support) != {"R6G1D-R091-C028", "R6G1D-R091-C029"}:
            raise ValueError("CACHED_B5_VIEW_ARCHIVE_SUPPORTS_MISMATCH")
        if binding.get("archive_sha256") != archive_digest:
            raise ValueError("CACHED_B5_VIEW_ARCHIVE_DIGEST_MISMATCH")
        for support, row in expected_records.items():
            state, meta = by_support[support]
            if (meta["sequence"] != row["archive_sequence"]
                    or meta["state_payload_sha256"] != row["archive_state_sha256"]
                    or _state_digest(state) != row["archive_state_sha256"]):
                raise ValueError(f"CACHED_B5_VIEW_ARCHIVE_STATE_MISMATCH:{support}")
        if len(expected_records) != 2:
            raise ValueError("CACHED_B5_VIEW_PROFILE_CLOSURE_INCOMPLETE")
        return binding

    t_build = perf_counter()
    with _external_root_scope(external_root):
        sources, source_inventory = load_b5_sources(root, expected_branch=branch)
    if cache_timings is not None:
        cache_timings["full_b5_source_load_seconds"] = perf_counter() - t_build
    vector_key = "external://r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz"
    vector_path = sources.payload_paths[vector_key]
    with np.load(vector_path, allow_pickle=False) as vector:
        lookup = exact_face_plate_lookup(
            vector["face_row"], vector["face_col"], vector["face_plate_id"],
            rows=GRID_ROWS, columns=GRID_COLUMNS,
        )
    edge_cells = incident_cells(**DEFAULT_BOUNDARY_EDGE)
    first_cell, second_cell = edge_cells.first, edge_cells.second
    support_a = f"R6G1D-R{first_cell[0]:03d}-C{first_cell[1]:03d}"
    support_b = f"R6G1D-R{second_cell[0]:03d}-C{second_cell[1]:03d}"
    if (support_a, support_b) != ("R6G1D-R091-C028", "R6G1D-R091-C029"):
        raise ValueError("B5_PARENT_CELL_TO_ENG10K_SUPPORT_ID_BINDING_CHANGED")
    plate_a, plate_b = lookup[first_cell], lookup[second_cell]
    if {plate_a, plate_b} != {5, 11}:
        raise ValueError("ENG10K_SUPPORTS_ARE_NOT_THE_EXPECTED_B5_5_11_SHARED_EDGE")
    descriptors = [dict(row) for row in sources.boundary_descriptors
                   if row.get("parent_grid_edge") == DEFAULT_BOUNDARY_EDGE]
    if len(descriptors) != 1:
        raise ValueError("B5_SHARED_EDGE_DESCRIPTOR_NOT_UNIQUE")
    descriptor = descriptors[0]
    boundary_id = descriptor["boundary_id"]
    t_audit = perf_counter()
    with _external_root_scope(external_root):
        audited = audit_pair_5_11(
            root, expected_branch=branch, requested_boundary_id=boundary_id,
            verified_sources=sources,
        )
    if cache_timings is not None:
        cache_timings["pair_5_11_audit_seconds"] = perf_counter() - t_audit
    audit_row = next((row for row in audited["edge_matrix"]
                      if row.get("boundary_id") == boundary_id), None)
    if (audit_row is None or audited["selected_boundary_id"] != boundary_id
            or audit_row.get("SECTION_ELIGIBILITY") != "ELIGIBLE"
            or audit_row.get("MATERIAL_ADMISSIBILITY") != "PASS_B6N8N_ADMITTED"):
        raise ValueError("B5_PAIR_AUDIT_DID_NOT_ADMIT_THE_REQUESTED_EDGE")

    mesh_edge_index = sources.mesh.boundary_ids.index(boundary_id)
    mesh_node_ids = tuple(int(node_id) for node_id in sources.mesh.boundary_edge_nodes[mesh_edge_index])
    if tuple(sorted(mesh_node_ids)) != tuple(sorted(descriptor["endpoint_node_ids"])):
        raise ValueError("B5_CANONICAL_EDGE_ENDPOINTS_DISAGREE")
    vertices = np.asarray(sources.mesh.vertices_lat_lon, dtype=np.float64)
    endpoint_lat_lon = []
    for node_id in mesh_node_ids:
        if node_id < 1 or node_id > len(vertices):
            raise ValueError("B5_EDGE_NODE_ID_OUTSIDE_CANONICAL_MESH")
        lat, lon = vertices[node_id - 1]
        endpoint_lat_lon.append({"node_id": node_id, "latitude_deg": float(lat),
                                 "longitude_deg": float(lon)})
    radial, grid_forward, tangent = local_edge_frame(91, 28, "EAST", 6_371_000.0)
    pair_normal = grid_forward if plate_a == 5 else -grid_forward

    states = {meta["support_id"]: (state, meta) for state, meta in loaded}
    side_rows = {row["support_id"]: row for row in audit_row["sides_plate_a_then_plate_b"]}
    profile_checks = {}
    expected_plate_by_support = {support_a: int(plate_a), support_b: int(plate_b)}
    for support in (support_a, support_b):
        state, meta = states[support]
        side = side_rows[support]
        profile = side["t0_profile"]
        z_m = [xi * state.lithosphere_m for xi in state.material_coordinate]
        same = (
            side["plate_id"] == expected_plate_by_support[support]
            and profile["crust_m"] == state.crust_m
            and profile["model_base_m"] == state.lithosphere_m
            and len(profile["z_m"]) == len(z_m) == len(profile["temperature_k"]) == len(state.temperature_k)
            and all(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-9) for a, b in zip(profile["z_m"], z_m))
            and all(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)
                    for a, b in zip(profile["temperature_k"], state.temperature_k))
            and [x["role_id"] for x in profile["material_properties"]]
            == [x.role_id for x in state.materials]
        )
        if not same:
            raise ValueError(f"ARCHIVED_ENG10K_STATE_NOT_BOUND_TO_B5_T0_PROFILE:{support}")
        profile_checks[support] = {
            "match": True,
            "archive_sequence": meta["sequence"],
            "archive_state_sha256": meta["state_payload_sha256"],
            "profile_nodes": len(profile["z_m"]),
            "temperature_coordinate_match": True,
            "material_role_sequence_match": True,
        }

    source_files = {
        "vector_partition": vector_path,
        "boundary_state": root / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json",
        "kinematic_census": root / "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
        "canonical_kinematics": root / "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
    }
    binding = {
        "schema": "ARCANA_B5_T0_ENG10K_SUPPORT_BOUNDARY_BINDING_V1",
        "time_anchor_ma": 210.0,
        "time_scope": "T0_INSTANT_ONLY_NO_POSITIVE_DURATION_VALIDITY",
        "source_branch": sources.branch,
        "source_head": sources.head,
        "source_identity_sha256": sources.source_identity,
        "vector_partition_payload_sha256": sources.vector_manifest["payload"]["sha256"],
        "kinematics_semantic_identity_sha256": sources.kinematics.canonical_identity_sha256,
        "support_cells": [
            {"support_id": support_a, "grid_cell": list(first_cell), "plate_id": int(plate_a)},
            {"support_id": support_b, "grid_cell": list(second_cell), "plate_id": int(plate_b)},
        ],
        "boundary": {
            "boundary_id": boundary_id,
            "ordered_plate_pair": [5, 11],
            "parent_grid_edge": dict(descriptor["parent_grid_edge"]),
            "first_cell_to_second_cell_plate_order": [int(plate_a), int(plate_b)],
            "grid_forward_unit_vector": grid_forward.tolist(),
            "plate_5_to_plate_11_normal_unit_vector": pair_normal.tolist(),
            "radial_unit_vector_at_edge_midpoint": radial.tolist(),
            "positive_tangent_unit_vector": tangent.tolist(),
            "endpoint_node_ids": list(mesh_node_ids),
            "endpoint_lat_lon": endpoint_lat_lon,
            "length_m": descriptor["length_m"],
            "support": descriptor["support"],
            "boundary_kind": descriptor["boundary_kind"],
            "geological_boundary_type": descriptor["geological_boundary_type"],
            "mechanical_accommodation_authority": descriptor["mechanical_accommodation"],
            "positive_duration_validity": descriptor["positive_duration_validity"],
            "relative_normal_velocity_m_per_year_t0_diagnostic": descriptor[
                "kinematic_descriptor"]["relative_normal_velocity_m_per_year"],
            "relative_tangential_velocity_m_per_year_t0_diagnostic": descriptor[
                "kinematic_descriptor"]["relative_tangential_velocity_m_per_year"],
            "t0_velocity_used_as_positive_time_forcing": False,
        },
        "pair_5_11_audit": {
            "selected_boundary_id": audited["selected_boundary_id"],
            "selection_mode": audited["selection_mode"],
            "section_eligibility": audit_row["SECTION_ELIGIBILITY"],
            "material_admissibility": audit_row["MATERIAL_ADMISSIBILITY"],
            "blockers": list(audit_row["BLOCKER"]),
        },
        "eng10k_profile_binding_checks": profile_checks,
        "archive_sha256": archive_digest,
        "source_file_sha256": {name: _raw_sha256(path) for name, path in source_files.items()},
        "contact_law_claim": "NONE_FROM_B5_TOPOLOGY; EXPERIMENTAL_SPRING_LAW_IS_SEPARATE_SYNTHETIC_INPUT",
    }
    if cache_path is not None:
        if not Path(cache_path).exists():
            cache_files = _cache_source_files(root, sources, source_inventory)
            t_write = perf_counter()
            _write_view_cache(cache_path, binding, source_files=cache_files)
            if cache_timings is not None:
                cache_timings["cache_write_seconds"] = perf_counter() - t_write
        # Verify the just-written persistent view through the same warm path
        # used by later invocations. The cold binding remains the run's source.
        t_warm = perf_counter()
        cached_binding, cache_audit = load_cached_t0_boundary_view(
            cache_path, root, external_root, expected_branch=branch)
        if _view_digest(cached_binding) != _view_digest(binding):
            raise ValueError("B5_CACHED_VIEW_DIFFERS_FROM_FRESH_FULL_AUDIT")
        if cache_timings is not None:
            cache_timings["verified_cache_load_seconds"] = perf_counter() - t_warm
            cache_timings["cache_validation_mode"] = cache_audit["mode"]
    return binding


def _series_spring_partition(opening_m: float, stiffnesses_n_per_m: tuple[float, float, float],
                             strike_length_m: float) -> dict[str, float]:
    """Solve three linear springs in series; this is a declared fixture law."""
    if (not math.isfinite(opening_m) or opening_m < 0 or not math.isfinite(strike_length_m)
            or strike_length_m <= 0 or len(stiffnesses_n_per_m) != 3
            or any(not math.isfinite(k) or k <= 0 for k in stiffnesses_n_per_m)):
        raise ValueError("SYNTHETIC_CONTACT_CONFIGURATION_INVALID")
    compliance = sum(1.0 / k for k in stiffnesses_n_per_m)
    force_n = opening_m / compliance
    displacement = tuple(force_n / k for k in stiffnesses_n_per_m)
    closure = sum(displacement) - opening_m
    work_j = 0.5 * force_n * opening_m
    stored_j = sum(0.5 * k * u * u for k, u in zip(stiffnesses_n_per_m, displacement))
    if not math.isclose(closure, 0.0, rel_tol=1e-13, abs_tol=1e-14):
        raise ValueError("SYNTHETIC_CONTACT_DISPLACEMENT_CLOSURE_FAILED")
    if not math.isclose(stored_j, work_j, rel_tol=1e-13, abs_tol=1e-14):
        raise ValueError("SYNTHETIC_CONTACT_WORK_BALANCE_FAILED")
    return {
        "opening_m": opening_m,
        "column_a_displacement_m": displacement[0],
        "interface_gap_m": displacement[1],
        "column_b_displacement_m": displacement[2],
        "interface_force_n": force_n,
        "interface_line_force_n_per_m": force_n / strike_length_m,
        "displacement_closure_m": closure,
        "external_work_j": work_j,
        "spring_energy_j": stored_j,
        "work_balance_residual_j": stored_j - work_j,
    }


def _run_case(loaded: list[tuple[ReducedState, dict[str, Any]]], binding: Mapping[str, Any],
              *, config: Mapping[str, Any], coupled: bool, lateral_mode: str) -> dict[str, Any]:
    if lateral_mode not in {"BLOCKED", "SYNTHETIC_CONSTANT", "SYNTHETIC_STRUCTURE_MODULATED"}:
        raise ValueError("LATERAL_DEEP_MODE_INVALID")
    if not coupled and lateral_mode != "BLOCKED":
        raise ValueError("LATERAL_DEEP_REQUIRES_MECHANICAL_INTERFACE_CASE")
    ids = [meta["support_id"] for _, meta in loaded]
    if ids != ["R6G1D-R091-C028", "R6G1D-R091-C029"]:
        raise ValueError("BOUNDARY_MICRODOMAIN_SUPPORT_ORDER_INVALID")
    states = {meta["support_id"]: state for state, meta in loaded}
    initial_states = dict(states)
    support_cells = {support: _column_geometry(state, support, config["strike_length_m"])
                     for support, state in states.items()}
    all_cells = {cell["cell_id"]: cell for cells in support_cells.values() for cell in cells}
    role_ids = {cell["material_role_id"] for cell in all_cells.values()}
    density_by_role = config["deep_initial_density_j_m3_by_role"]
    if set(density_by_role) != role_ids:
        raise ValueError("SYNTHETIC_DEEP_ROLE_CONFIGURATION_MISMATCH")
    if any(not math.isfinite(v) or v < 0 for v in density_by_role.values()):
        raise ValueError("SYNTHETIC_DEEP_DENSITY_INVALID")
    if config["steps"] < 1 or config["step_years"] <= 0:
        raise ValueError("BOUNDARY_MICRODOMAIN_STEP_CONFIGURATION_INVALID")
    if lateral_mode != "BLOCKED" and not 0 <= config["lateral_deep_base_fraction_per_step"] <= 0.5:
        raise ValueError("LATERAL_DEEP_FRACTION_INVALID")

    cells_a, cells_b = (support_cells[support] for support in ids)
    records = []
    stocks = {cell_id: density_by_role[cell["material_role_id"]] * cell["volume_m3"]
              * (config["synthetic_support_b_deep_stock_multiplier"] if cell["support_id"] == ids[1] else 1.0)
              for cell_id, cell in all_cells.items()}
    initial_inventory = sum(stocks.values())
    contact_history = []
    for step in range(1, config["steps"] + 1):
        opening = config["synthetic_total_opening_m"] / config["steps"]
        if coupled:
            mech = _series_spring_partition(
                opening,
                (config["column_stiffness_a_n_per_m"], config["interface_stiffness_n_per_m"],
                 config["column_stiffness_b_n_per_m"]), config["strike_length_m"],
            )
        else:
            # Two uncoupled columns each receive half of the same imposed opening.
            ua = ub = opening / 2.0
            mech = {"opening_m": opening, "column_a_displacement_m": ua,
                    "interface_gap_m": None, "column_b_displacement_m": ub,
                    "interface_force_n": 0.0, "interface_line_force_n_per_m": 0.0,
                    "displacement_closure_m": ua + ub - opening,
                    "external_work_j": None, "spring_energy_j": None,
                    "work_balance_residual_j": None}
        contact_history.append(mech)

        next_states = {}
        for support, extension_m in ((ids[0], mech["column_a_displacement_m"]),
                                     (ids[1], mech["column_b_displacement_m"])):
            prior = states[support]
            next_state, diag = pure_shear_thermal_step(
                prior, duration_s=config["step_years"] * SECONDS_PER_YEAR,
                extension_velocity_m_s=extension_m / (config["step_years"] * SECONDS_PER_YEAR),
            )
            next_states[support] = next_state
        states = next_states
        support_cells = {support: _column_geometry(state, support, config["strike_length_m"])
                         for support, state in states.items()}

        before = sum(stocks.values())
        stocks, vertical_transfers = _deep_transport_step(
            support_cells, stocks, dt_years=config["step_years"],
            mobility_per_year=config["deep_vertical_mobility_per_year"],
            response_by_role=_modal_response_by_role(),
        )
        lateral_transfers = []
        if lateral_mode != "BLOCKED":
            # Explicit node-index correspondence is an experiment mapping, not geological continuity.
            gap = float(mech["interface_gap_m"] or 0.0)
            for left, right in zip(support_cells[ids[0]], support_cells[ids[1]]):
                if left["node_index_zero_based"] != right["node_index_zero_based"]:
                    raise ValueError("LATERAL_NODE_MAPPING_NOT_IDENTITY")
                fraction = float(config["lateral_deep_base_fraction_per_step"])
                if lateral_mode == "SYNTHETIC_STRUCTURE_MODULATED":
                    fraction *= 1.0 + config["lateral_deep_gap_gain_per_m"] * gap
                if fraction > 0.5:
                    raise ValueError("LATERAL_DEEP_EXPLICIT_STEP_UNSTABLE")
                pair_ids = (left["cell_id"], right["cell_id"])
                updated, transfer = conservative_two_cell_transport(
                    np.asarray([stocks[pair_ids[0]], stocks[pair_ids[1]]]), fraction,
                )
                stocks[pair_ids[0]], stocks[pair_ids[1]] = map(float, updated)
                lateral_transfers.append({"interface_id": f"{binding['boundary']['boundary_id']}:DEEP:N{left['node_index_zero_based']:03d}",
                                          "cell_a": pair_ids[0], "cell_b": pair_ids[1],
                                          "transfer_a_to_b_j": transfer,
                                          "fraction": fraction, "structural_gap_m": gap})
        after = sum(stocks.values())
        if any(not math.isfinite(v) or v < 0 for v in stocks.values()):
            raise ValueError("DEEP_STOCK_INVALID")
        if not math.isclose(after, before, rel_tol=1e-13, abs_tol=1e-8):
            raise ValueError("DEEP_TRANSFER_NOT_CONSERVATIVE")
        records.append({
            "step": step,
            "time_years": step * config["step_years"],
            "mechanics": mech,
            "interface_stress_pa": None,
            "interface_stress_status": "UNKNOWN_NO_AUTHORIZED_CONTACT_AREA_OR_3D_GEOMETRY",
            "mechanical_strain_by_support": {
                ids[0]: mech["column_a_displacement_m"] / initial_states[ids[0]].width_m,
                ids[1]: mech["column_b_displacement_m"] / initial_states[ids[1]].width_m,
            },
            "thermal_kernel_extension_velocity_is_synthetic_contact_displacement": True,
            "deep": {"inventory_before_j": before, "inventory_after_j": after,
                     "conservation_residual_j": after - before,
                     "vertical_interface_count": len(vertical_transfers),
                     "lateral_interface_count": len(lateral_transfers),
                     "vertical_transferred_abs_sum_j": sum(abs(x["transfer_a_to_b_j"]) for x in vertical_transfers),
                     "lateral_transfers": lateral_transfers,
                     "thermal_to_deep_j": 0.0, "mechanical_work_to_deep_j": 0.0},
        })
    final_volumes = {cell["cell_id"]: cell["volume_m3"]
                     for cells in support_cells.values() for cell in cells}
    initial_volumes = {cell_id: cell["volume_m3"] for cell_id, cell in all_cells.items()}
    return {
        "contact_state": "COUPLED_SYNTHETIC_SPRING" if coupled else "DISCONNECTED_COLUMNS",
        "lateral_deep_mode": lateral_mode,
        "synthetic_mechanics": {"law": "THREE_LINEAR_SPRINGS_IN_SERIES" if coupled else "INDEPENDENT_HALF_OPENING",
                                "parameters": {k: config[k] for k in ("column_stiffness_a_n_per_m",
                                    "interface_stiffness_n_per_m", "column_stiffness_b_n_per_m",
                                    "synthetic_total_opening_m", "strike_length_m")},
                                "per_step": contact_history},
        "steps": records,
        "initial_deep_inventory_j": initial_inventory,
        "final_deep_inventory_j": sum(stocks.values()),
        "deep_conservation_residual_j": sum(stocks.values()) - initial_inventory,
        "deep_cell_count": len(stocks),
        "support_material_roles": {support: [cell["material_role_id"] for cell in support_cells[support]]
                                   for support in ids},
        "state_initial_sha256": {support: _state_digest(state) for support, state in initial_states.items()},
        "state_final_sha256": {support: _state_digest(state) for support, state in states.items()},
        "state_initial": {support: state.payload() for support, state in initial_states.items()},
        "state_final": {support: state.payload() for support, state in states.items()},
        "column_volume_initial_m3": {support: sum(cell["volume_m3"] for cell in _column_geometry(initial_states[support], support, config["strike_length_m"])) for support in ids},
        "column_volume_final_m3": {support: sum(cell["volume_m3"] for cell in support_cells[support]) for support in ids},
        "deep_stocks_j_by_cell": stocks,
        "binding_boundary_id": binding["boundary"]["boundary_id"],
    }


def run_boundary_microdomain(repository_root: str | Path, external_root: str | Path,
                             archive_path: str | Path,
                             config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(DEFAULT_ENGINEERING_CONFIG if config is None else config)
    required = set(DEFAULT_ENGINEERING_CONFIG)
    if set(cfg) != required:
        raise ValueError("BOUNDARY_MICRODOMAIN_CONFIG_KEYS_INVALID")
    if isinstance(cfg["steps"], bool) or not isinstance(cfg["steps"], int) or cfg["steps"] < 1:
        raise ValueError("BOUNDARY_MICRODOMAIN_STEP_COUNT_INVALID")
    floats = [v for k, v in cfg.items() if k != "deep_initial_density_j_m3_by_role"]
    if any(not math.isfinite(v) for v in floats if isinstance(v, (int, float))):
        raise ValueError("BOUNDARY_MICRODOMAIN_NONFINITE_CONFIG")
    if any(v <= 0 for v in (cfg["step_years"], cfg["strike_length_m"],
                             cfg["column_stiffness_a_n_per_m"], cfg["interface_stiffness_n_per_m"],
                             cfg["column_stiffness_b_n_per_m"])):
        raise ValueError("BOUNDARY_MICRODOMAIN_POSITIVE_CONFIG_REQUIRED")
    if cfg["synthetic_total_opening_m"] < 0 or cfg["deep_vertical_mobility_per_year"] < 0:
        raise ValueError("BOUNDARY_MICRODOMAIN_NONNEGATIVE_CONFIG_REQUIRED")
    if (not math.isfinite(cfg["synthetic_support_b_deep_stock_multiplier"])
            or cfg["synthetic_support_b_deep_stock_multiplier"] <= 0
            or cfg["lateral_deep_base_fraction_per_step"] < 0
            or cfg["lateral_deep_base_fraction_per_step"] > 0.5
            or cfg["lateral_deep_gap_gain_per_m"] < 0):
        raise ValueError("BOUNDARY_MICRODOMAIN_DEEP_CONFIGURATION_INVALID")
    if cfg["steps"] * cfg["step_years"] > 100.0:
        raise ValueError("BOUNDARY_MICRODOMAIN_DURATION_OUTSIDE_SHORT_PILOT_SCOPE")
    started = perf_counter()
    tracemalloc.start()
    binding = build_t0_boundary_binding(repository_root, external_root, archive_path)
    loaded, archive_digest = load_microdomain_inputs(str(archive_path))
    if archive_digest != binding["archive_sha256"]:
        raise ValueError("ARCHIVE_CHANGED_AFTER_TOPOLOGY_BINDING")
    cases = [
        _run_case(loaded, binding, config=cfg, coupled=False, lateral_mode="BLOCKED"),
        _run_case(loaded, binding, config=cfg, coupled=True, lateral_mode="BLOCKED"),
        _run_case(loaded, binding, config=cfg, coupled=True, lateral_mode="SYNTHETIC_CONSTANT"),
        _run_case(loaded, binding, config=cfg, coupled=True, lateral_mode="SYNTHETIC_STRUCTURE_MODULATED"),
    ]
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        "schema": "ARCANA_TECTONIC_BOUNDARY_MECHANICAL_MICRODOMAIN_V1",
        "scope": "NONCANONICAL_SYNTHETIC_CONTACT_ENGINEERING_EXPERIMENT",
        "t0_boundary_binding": binding,
        "configuration": {**cfg, "mechanics_authority": "SYNTHETIC_LINEAR_SPRINGS_NOT_B5_OR_GEOLOGICAL_LAW",
                           "deep_vertical_authority": "SYNTHETIC_EXISTING_MICRODOMAIN_OPERATOR",
                           "deep_lateral_default": "BLOCKED",
                           "deep_lateral_enabled_cases": ["SYNTHETIC_CONSTANT", "SYNTHETIC_STRUCTURE_MODULATED"],
                           "ordinary_thermal_flux": "DIAGNOSTIC_ONLY",
                           "thermal_to_deep": 0.0, "mechanical_work_to_deep": 0.0},
        "cases": cases,
        "measurements": {"elapsed_seconds": perf_counter() - started,
                         "python_tracemalloc_peak_bytes": peak,
                         "tracemalloc_is_not_process_rss": True,
                         "case_count": len(cases), "step_count_per_case": cfg["steps"]},
        "claim_limit": "T0_TOPOLOGY_BINDING_AND_SYNTHETIC_MECHANICS_ONLY; NO_GEOLOGICAL_RESPONSE_QUALIFICATION",
    }
    return result
