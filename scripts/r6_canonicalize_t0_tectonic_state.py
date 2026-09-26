"""Canonicalize the supported R6 210 Ma plate-face topology and census.

This is a t0-only materialization.  It never assigns plate motion, promotes
design labels to rheology, or advances the world in time.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (
    external_root, require_repository_context, repository_provenance,
    verify_protected_staged_blobs,
)
EXPECTED_HEAD = "592b1651b405363373590092e133bd25569d99a5"
EXPECTED_T0_SHA256 = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
EXPECTED_T0_BYTES = 1_169_900
EXPECTED_LATENT_SHA256 = "ab24a80cda7bda035589b4473fa4af51d63ad92560ed96f368061319caa3231a"
EXPECTED_INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
RADIUS_M = 6_371_000.0
SHAPE = (180, 360)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f"immutable output differs: {path}")
        return
    fd, temp_name = tempfile.mkstemp(prefix=".r6-t0-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _verify_repository() -> None:
    require_repository_context(ROOT, required_ancestor=EXPECTED_HEAD)
    verify_protected_staged_blobs(ROOT, EXPECTED_INDEX_BLOBS)


def _deterministic_npz(arrays: dict[str, np.ndarray]) -> bytes:
    from io import BytesIO

    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(arrays):
            buf = BytesIO()
            np.lib.format.write_array(buf, np.ascontiguousarray(arrays[name]), version=(2, 0), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o600 << 16
            archive.writestr(info, buf.getvalue())
    return stream.getvalue()


def _verify_latent(parent_hash: str) -> dict:
    path = ROOT / "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY.json"
    manifest_path = ROOT / "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY_MANIFEST.json"
    raw = path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if _sha(raw) != EXPECTED_LATENT_SHA256 or manifest["latent_artifact"]["sha256"] != EXPECTED_LATENT_SHA256:
        raise RuntimeError("fail-closed: latent geometry identity mismatch")
    latent = json.loads(raw)
    if latent.get("parent_payload_sha256") != parent_hash or manifest.get("parent_payload_sha256") != parent_hash:
        raise RuntimeError("fail-closed: latent geometry does not bind canonical t0")
    return latent


def _verify_nuclei_support(fields, nuclei: list[list[float]]) -> None:
    lat = np.deg2rad(fields.grid.lat_centers_deg)[:, None]
    lon = np.deg2rad(fields.grid.lon_centers_deg)[None, :]
    best = np.full(SHAPE, -2.0, dtype=np.float64)
    ids = np.zeros(SHAPE, dtype=np.int16)
    for plate_id, (plat, plon) in enumerate(nuclei):
        plat_r, plon_r = math.radians(plat), math.radians(plon)
        dot = np.sin(lat) * math.sin(plat_r) + np.cos(lat) * math.cos(plat_r) * np.cos(lon - plon_r)
        take = dot > best
        ids[take] = plate_id
        best[take] = dot[take]
    if not np.array_equal(ids, fields.plate_id):
        raise RuntimeError("R6_T0_VECTOR_PARTITION_CANONICAL_COMPATIBILITY_CONFLICT: latent nuclei do not reproduce parent support")


def _build_mesh(fields) -> tuple[dict[str, np.ndarray], list[dict], dict]:
    nlat, nlon = SHAPE
    plate = fields.plate_id
    if plate.shape != SHAPE or set(map(int, np.unique(plate))) != set(range(fields.plate_count)):
        raise RuntimeError("canonical plate support has unexpected shape or IDs")

    # Every cell is one closed spherical face.  Its exact latitude/longitude
    # bounds and its small-circle/meridian edge semantics are in the manifest.
    face_rows = np.repeat(np.arange(nlat, dtype=np.uint8), nlon)
    face_cols = np.tile(np.arange(nlon, dtype=np.uint16), nlat)
    south = -90.0 + np.arange(nlat, dtype=np.float64)
    west = -180.0 + np.arange(nlon, dtype=np.float64)
    face_south = np.repeat(south, nlon)
    face_north = face_south + 1.0
    face_west = np.tile(west, nlat)
    face_east = face_west + 1.0
    face_vertices = np.stack((
        np.stack((face_south, face_west), axis=1),
        np.stack((face_south, face_east), axis=1),
        np.stack((face_north, face_east), axis=1),
        np.stack((face_north, face_west), axis=1),
        np.stack((face_south, face_west), axis=1),
    ), axis=1)
    face_plate = plate.reshape(-1).astype(np.int16, copy=True)
    face_crust = fields.crust_class.reshape(-1).astype(np.int8, copy=True)
    face_boundary_support = fields.boundary_class.reshape(-1).astype(np.int8, copy=True)
    if len(np.unique(face_rows.astype(np.uint32) * nlon + face_cols)) != nlat * nlon:
        raise RuntimeError("face IDs are not unique")
    if not np.array_equal(face_vertices[:, 0, :], face_vertices[:, -1, :]):
        raise RuntimeError("spherical face rings are not closed")
    row_areas = [RADIUS_M**2 * (2.0 * math.pi / nlon) *
                 (math.sin(math.radians(-89.0 + row)) - math.sin(math.radians(-90.0 + row)))
                 for row in range(nlat)]
    total_area = math.fsum([area * nlon for area in row_areas])
    sphere_area = 4.0 * math.pi * RADIUS_M**2
    if abs(total_area - sphere_area) / sphere_area > 1e-12:
        raise RuntimeError("spherical faces do not cover the declared sphere area")

    # Enumerate each positive-length shared interface once: east and north.
    # edge_axis 0 = east/west meridian; 1 = north/south parallel.
    edge_rows: list[tuple[int, int, int, int, int, float, int, int, int, int]] = []
    group: dict[tuple[int, int], dict] = {}
    dlat = math.pi / nlat
    dlon = 2.0 * math.pi / nlon
    for row in range(nlat):
        lat_center = -90.0 + (row + 0.5) * 180.0 / nlat
        meridian_length = RADIUS_M * dlat
        parallel_length = RADIUS_M * math.cos(math.radians(lat_center + 0.5)) * dlon
        for col in range(nlon):
            east_col = (col + 1) % nlon
            for rr, cc, axis, length in ((row, east_col, 0, meridian_length),
                                         (row + 1, col, 1, parallel_length) if row + 1 < nlat else (-1, -1, 1, 0.0)):
                if rr < 0 or length <= 0.0:
                    continue
                a, b = int(plate[row, col]), int(plate[rr, cc])
                if a == b:
                    continue
                pair = (min(a, b), max(a, b))
                side_a_crust = int(fields.crust_class[row, col]) if a == pair[0] else int(fields.crust_class[rr, cc])
                side_b_crust = int(fields.crust_class[rr, cc]) if a == pair[0] else int(fields.crust_class[row, col])
                side_a_boundary = int(fields.boundary_class[row, col]) if a == pair[0] else int(fields.boundary_class[rr, cc])
                side_b_boundary = int(fields.boundary_class[rr, cc]) if a == pair[0] else int(fields.boundary_class[row, col])
                rec = group.setdefault(pair, {"plate_a": pair[0], "plate_b": pair[1], "length_m": 0.0,
                    "edge_count": 0, "crust_pair_counts": defaultdict(int), "unknown_boundary_edge_count": 0})
                rec["length_m"] += length
                rec["edge_count"] += 1
                rec["crust_pair_counts"][f"{side_a_crust}:{side_b_crust}"] += 1
                rec["unknown_boundary_edge_count"] += int(side_a_boundary == 0 or side_b_boundary == 0)
                edge_rows.append((row, col, axis, pair[0], pair[1], length,
                                  side_a_crust, side_b_crust, side_a_boundary, side_b_boundary))

    # At each pole, all terminal-row faces meet at a point (contracted grid
    # topology).  Record point adjacency, never a positive-length boundary or
    # an event candidate.
    polar_pairs = set()
    for row in (0, nlat - 1):
        ids = sorted(set(map(int, plate[row, :])))
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                polar_pairs.add((a, b))
    groups = []
    for pair, rec in sorted(group.items()):
        groups.append({**rec, "length_m": round(float(rec["length_m"]), 6),
                       "crust_pair_counts": dict(sorted(rec["crust_pair_counts"].items())),
                       "boundary_support": "COARSE_SUPPORT_ON_FINE_GRID",
                       "geometric_semantics": "UNION_OF_CANONICAL_SPHERICAL_CELL_FACES; boundary follows parent grid edges"})
    arrays = {
        "face_row": face_rows,
        "face_col": face_cols,
        "face_vertex_latlon_deg": face_vertices,
        "face_plate_id": face_plate,
        "face_crust_class": face_crust,
        "face_boundary_class": face_boundary_support,
        "boundary_edge_row": np.asarray([r[0] for r in edge_rows], dtype=np.uint8),
        "boundary_edge_col": np.asarray([r[1] for r in edge_rows], dtype=np.uint16),
        "boundary_edge_axis": np.asarray([r[2] for r in edge_rows], dtype=np.uint8),
        "boundary_plate_a": np.asarray([r[3] for r in edge_rows], dtype=np.int16),
        "boundary_plate_b": np.asarray([r[4] for r in edge_rows], dtype=np.int16),
        "boundary_length_m": np.asarray([r[5] for r in edge_rows], dtype=np.float64),
        "boundary_crust_a": np.asarray([r[6] for r in edge_rows], dtype=np.int8),
        "boundary_crust_b": np.asarray([r[7] for r in edge_rows], dtype=np.int8),
        "boundary_support_a": np.asarray([r[8] for r in edge_rows], dtype=np.int8),
        "boundary_support_b": np.asarray([r[9] for r in edge_rows], dtype=np.int8),
    }
    topo = {"face_count": int(len(face_plate)), "plate_count": int(fields.plate_count),
        "positive_length_adjacency_pair_count": len(groups), "positive_length_boundary_edge_count": len(edge_rows),
        "polar_point_only_adjacency_pair_count": len(polar_pairs),
        "polar_point_only_pairs": [list(p) for p in sorted(polar_pairs)],
        "groups": groups,
        "partition_proof": {"one_face_per_parent_cell": True, "unique_parent_cell_ids": True,
            "face_bounds_tile_declared_global_grid": True, "surface_area_m2": sphere_area,
            "computed_face_area_sum_m2": total_area,
            "overlap_or_gap_test": "EXACT_INDEX_PARTITION; canonical lat/lon finite-volume faces are disjoint in interiors and cover sphere, poles identified as shared points"}}
    return arrays, edge_rows, topo


def _write_outputs(outdir: Path, payload_path: Path, manifest: dict, kinematics: dict,
                   census: dict, readiness: dict, adjudication: dict) -> None:
    from arcana_worldsim.r6.initial_world.materialize import _deterministic_npz as canonical_npz

    arrays = manifest.pop("_arrays")
    data = canonical_npz(arrays)
    payload_root = external_root(ROOT).resolve()
    logical_payload_path = payload_path.resolve().relative_to(payload_root).as_posix()
    manifest["payload"] = {"path": logical_payload_path,
        "root_environment_variable": "ARCANA_EXTERNAL_ROOT", "bytes": len(data), "sha256": _sha(data),
                            "format": "deterministic NPZ/NPY v2 ZIP_STORED"}
    outputs = {
        "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json": manifest,
        "R6_T0_INITIAL_KINEMATICS_MANIFEST.json": kinematics,
        "R6_T0_EVENT_ELIGIBILITY_CENSUS.json": census,
        "R6_T0_EVENT_ELIGIBILITY_CENSUS.md": _census_md(census),
        "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.json": readiness,
        "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.md": _readiness_md(readiness),
        "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json": adjudication,
        "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.md": _adjudication_md(adjudication),
    }
    serialized = {}
    for name, obj in outputs.items():
        serialized[outdir / name] = obj.encode("utf-8") if isinstance(obj, str) else _json_bytes(obj)
    if payload_path.exists() and _sha(payload_path.read_bytes()) != _sha(data):
        raise FileExistsError(f"refusing to overwrite differing external payload: {payload_path}")
    for path, expected in serialized.items():
        if path.exists() and path.read_bytes() != expected:
            raise FileExistsError(f"refusing to overwrite differing output: {path}")
    if not payload_path.exists():
        _atomic_write(payload_path, data)
    for path, expected in serialized.items():
        _atomic_write(path, expected)


def _census_md(obj: dict) -> str:
    return ("# R6 t0 event eligibility census\n\n"
        f"At 210 Ma, {obj['candidate_pair_count']} positive-length plate-pair boundary aggregates were evaluated.\n\n"
        f"- UNKNOWN: {obj['counts']['UNKNOWN']}\n- ELIGIBLE: {obj['counts']['ELIGIBLE']}\n"
        f"- INELIGIBLE: {obj['counts']['INELIGIBLE']}\n- ACTIVE: {obj['counts']['ACTIVE']}\n\n"
        "All candidates remain UNKNOWN because plate-relative velocity and mechanically authorized weak-zone support are absent. "
        "This is a t0 census, not rift evolution.\n")


def _readiness_md(obj: dict) -> str:
    return ("# R6 first physical interval numerical readiness\n\n"
        f"Decision: `{obj['decision']}`.\n\n"
        f"The first dt is **not determinable**. Motion is unknown; event candidates are unresolved; no positive event-time lower bound, "
        "motion validity horizon, displacement tolerance, or numerical error tolerance is authorized.\n")


def _adjudication_md(obj: dict) -> str:
    return ("# R6 t0 synthetic tectonic-state canonicalization\n\n"
        f"Decision: `{obj['decision']}`\n\nVerdict: `{obj['verdict']}`\n\n"
        "The 210 Ma spherical cell-face plate partition and topological adjacency census are materialized and validated against the "
        "canonical parent support. Initial plate motion and mechanical weak-zone state remain UNKNOWN; therefore t0 opening rates, "
        "rift eligibility beyond UNKNOWN, and a legal first dt are not established. No time evolution occurred.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    parser.add_argument("--payload-path", type=Path,
        default=external_root(ROOT) / "r6" / "tectonic_t0" / "R6_T0_VECTOR_PLATE_PARTITION.npz")
    args = parser.parse_args()
    _verify_repository()
    sys.path.insert(0, str(ROOT / "src"))
    from arcana_worldsim.r6.initial_world.generator import generate_initial_world

    package = json.loads((ROOT / "R6_CANONICAL_INITIAL_STATE_PACKAGE.json").read_text(encoding="utf-8"))
    materialization = json.loads((ROOT / "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json").read_text(encoding="utf-8"))
    latent = _verify_latent(EXPECTED_T0_SHA256)
    fields = generate_initial_world()
    canonical = _deterministic_npz(fields.arrays())
    if len(canonical) != EXPECTED_T0_BYTES or _sha(canonical) != EXPECTED_T0_SHA256:
        raise RuntimeError("canonical t0 regeneration does not match immutable registered payload")
    _verify_nuclei_support(fields, latent["plate_nuclei_lat_lon_deg"])
    mesh_arrays, edge_rows, topology = _build_mesh(fields)
    if topology["face_count"] != 64_800 or topology["positive_length_boundary_edge_count"] != len(edge_rows):
        raise RuntimeError("spherical mesh cardinality check failed")

    output_dir = args.output_dir.resolve()
    payload_path = args.payload_path.resolve()
    # The payload is deliberately outside ordinary Git; preflight all targets
    # before creating any output, so a permission failure cannot leave a partial ledger.
    if output_dir != ROOT.resolve():
        raise RuntimeError("output-dir must be the active repository root")
    expected_external_root = external_root(ROOT)
    if expected_external_root not in payload_path.parents:
        raise RuntimeError("payload-path must remain under the designated external source root")
    if not expected_external_root.exists() or (not payload_path.exists() and not os.access(expected_external_root, os.W_OK)):
        raise PermissionError(f"external payload root is not writable: {expected_external_root}")

    groups = topology.pop("groups")
    candidates = [{"candidate_id": f"R6T0-BOUNDARY-{i:04d}", "plate_a": g["plate_a"], "plate_b": g["plate_b"],
        "boundary_edge_count": g["edge_count"], "boundary_length_m": g["length_m"],
        "support": g["boundary_support"], "kinematic_driver": None,
        "weak_zone_state": "UNKNOWN", "eligibility": "UNKNOWN",
        "missing_inputs": ["INITIAL_RELATIVE_PLATE_VELOCITY", "MECHANICALLY_AUTHORIZED_WEAK_ZONE_STATE", "RIFT_INITIATION_LAW"],
        "reason": "UNKNOWN_IS_NOT_INELIGIBLE; no authorized inputs permit an eligibility decision"} for i, g in enumerate(groups)]
    census = {"schema": "R6_T0_EVENT_ELIGIBILITY_CENSUS_V1", "time_ma": 210.0,
        "census_executed": True, "candidate_unit": "ADJACENT_PLATE_PAIR_POSITIVE_LENGTH_BOUNDARY_AGGREGATE",
        "candidate_pair_count": len(candidates), "counts": {"UNKNOWN": len(candidates), "ELIGIBLE": 0, "INELIGIBLE": 0, "ACTIVE": 0},
        "candidates": candidates, "rift_evolution_executed": False,
        "source_authority": "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
        "weak_zone_policy": "UNKNOWN_REMAINS_FIRST_CLASS; province design classes are not rheology"}
    vector_manifest = {"schema": "R6_T0_VECTOR_PLATE_PARTITION_V1", "time_ma": 210.0,
        "authority_class": "MODEL_DERIVED_FROM_CANONICAL_T0",
        "canonical_parent_sha256": EXPECTED_T0_SHA256, "canonical_parent_bytes": EXPECTED_T0_BYTES,
        "canonical_parent_state_id": package["states"][0]["state_id"],
        "generator_id": package["generator"]["id"], "generator_identity_sha256": package["generator"]["identity_sha256"],
        "latent_source_sha256": EXPECTED_LATENT_SHA256,
        "representation": "ONE_CLOSED_SPHERICAL_FINITE_VOLUME_CELL_FACE_PER_CANONICAL_PARENT_CELL_GROUPED_BY_PLATE_ID",
        "edge_semantics": {"meridians": "GREAT_CIRCLE_ARCS", "latitude_edges": "SMALL_CIRCLE_ARCS", "face_rings_closed": True,
            "no_smoothing_or_subcell_inference": True, "support": "COARSE_SUPPORT_ON_FINE_GRID"},
        "parent_grid": {"grid_id": "R6_GLOBAL_GEOGRAPHY_1DEG_V1", "shape": list(SHAPE), "radius_m": RADIUS_M,
            "latitude_bounds_deg": [-90, 90], "longitude_bounds_deg": [-180, 180], "row_order": "SOUTH_TO_NORTH",
            "periodic_longitude": True, "pole_policy": "terminal latitude-row faces meet at shared polar point"},
        "parent_consistency": {"validation": "PASS_EXACT_PLATE_ID_AND_CRUST_CLASS_PER_PARENT_FACE",
            "face_count": topology["face_count"], "all_64800_parent_cells_once": True,
            "latent_nuclei_reproduced_plate_support": True},
        "topology": topology, "adjacency_groups": groups,
        "boundary_uncertainty": "NO_FINER_THAN_SOURCE_CELL_SUPPORT; parent boundary class retains UNKNOWN",
        "_arrays": mesh_arrays}
    kinematics = {"schema": "R6_T0_INITIAL_KINEMATICS_MANIFEST_V1", "time_ma": 210.0,
        "status": "BLOCKED_INITIAL_MOTION_NOT_IDENTIFIED_BY_AUTHORIZED_PRIOR",
        "authority_class": "LITERATURE_PRIOR_ONLY_FOR_AGGREGATE_EARTH_PLAUSIBILITY",
        "canonical_realization_materialized": False, "plate_motion_values": None,
        "reference_frame": "SYNTHETIC_AREA_WEIGHTED_LEAST_SQUARES_NO_NET_ROTATION_GAUGE__NOT_MANTLE_FRAME",
        "selection_rule": None,
        "blocker": "available Earth aggregate speed statistics do not specify an R6 joint per-plate speed/direction distribution; no evidence-based geometry-conditioned coupling law or predeclared acceptance prior is bound",
        "gauge_validation": "NOT_APPLICABLE_NO_VELOCITY_FIELD",
        "uncertainty": "MODEL_UNCERTAINTY_RETAINED; numeric joint prior absent",
        "a1_or_earth_trajectory_fit": False}
    readiness = {"schema": "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS_V1", "start_time_ma": 210.0,
        "decision": "BLOCKED_T0_MOTION_AND_EVENT_GUARD_UNRESOLVED", "first_interval_executable": False,
        "first_dt_ma": None, "first_interval_contract_created": False,
        "candidate_event_state": "UNKNOWN", "unknown_event_guard": "BLOCK_IF_NO_SOURCED_STRICTLY_POSITIVE_ACTIVATION_TIME_LOWER_BOUND",
        "strictly_positive_event_time_lower_bound_ma": None, "motion_validity_horizon_ma": None,
        "displacement_or_error_tolerance": None, "active_constraints": [],
        "blocker_family": "R6_T0_INITIAL_MOTION_AND_EVENT_GUARD_AUTHORITY_BINDING",
        "P03_motion_change_law": "REQUIRED_BEFORE_SEGMENT_RENEWAL; first segment cannot be established while t0 motion is unbound",
        "P08_rift_initiation_law": "REQUIRED_BEFORE_FIRST_INTERVAL_WHILE_CANDIDATE_ELIGIBILITY_IS_UNKNOWN",
        "P09_plate_split_law": "REQUIRED_BEFORE_FIRST_INTERVAL_WHILE_UNKNOWN_EVENT_CANNOT_BE_GUARDED",
        "forward_evolution_executed": False}
    req = {
        "P01": "BLOCKED_NO_CANONICAL_MOTION_DISTRIBUTION", "P02": "BOUNDED_PRIOR_NOT_BOUND_FOR_SEGMENT",
        "P03": "BLOCKED", "P04": "MATERIALIZED_AND_VALIDATED", "P05": "EXPLICIT_UNKNOWN_RETAINED",
        "P06": "SEMANTICS_BOUND_VALUE_NOT_COMPUTABLE_WITHOUT_MOTION", "P07": "EVALUATED_UNKNOWN_AT_T0",
        "P08": "REQUIRED_BEFORE_FIRST_INTERVAL", "P09": "REQUIRED_BEFORE_FIRST_INTERVAL",
        "P10": "EXECUTED_AT_T0_UNKNOWN_PRESERVED", "P11": "BLOCKED_NO_DT_CONSTRAINTS", "P12": "EXPLICIT_UNKNOWN_NO_NUMERIC_JOINT_PRIOR"}
    adjudication = {"schema": "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION_V1", "repository": "siegmound/ARCANA_WORLD",
        "repository_context": repository_provenance(ROOT),
        "decision": "T0_VECTOR_PARTITION_MATERIALIZED__FIRST_INTERVAL_BLOCKED_UNKNOWN_MOTION_AND_RIFT_ELIGIBILITY",
        "verdict": "PASS_T0_VECTOR_TOPOLOGY_AND_EVENT_CENSUS__MOTION_AND_FIRST_DT_UNBOUND",
        "next_action": "R6_T0_INITIAL_MOTION_AND_EVENT_GUARD_AUTHORITY_BINDING",
        "canonical_t0_changed": False, "global_grid_changed": False,
        "vector_partition": "MATERIALIZED_AND_VALIDATED", "spherical_coverage": "PASS_EXACT_SPHERICAL_CELL_FACE_PARTITION",
        "parent_support_consistency": "PASS_EXACT_1DEG_PARENT_CLASS_REPRODUCTION",
        "plate_adjacency_graph": "MATERIALIZED", "initial_motion": "BLOCKED", "initial_motion_authority": "LITERATURE_PRIOR_ONLY",
        "reference_frame": kinematics["reference_frame"], "no_bulk_rotation_validation": "NOT_APPLICABLE_MOTION_UNKNOWN",
        "weak_zone_state": "UNKNOWN", "extensional_forcing_at_t0": "BLOCKED_MOTION_UNKNOWN",
        "rift_eligibility_census": "EXECUTED_UNKNOWN_PRESERVED", "rift_candidate_pairs": len(candidates),
        "rift_eligible": 0, "rift_ineligible": 0, "rift_unknown": len(candidates), "rift_active": 0,
        "first_legal_dt_determinable": False, "first_legal_dt_ma": None, "first_interval_scientifically_executable": False,
        "first_interval_contract_created": False, "requirements_P01_P12": req,
        "remaining_blocker": readiness["blocker_family"], "scientific_evolution_executed": False,
        "a1_used_as_trajectory_authority": False, "earth_trajectory_copied": False,
        "deep_required": False, "bathymetry_generated": False, "climate_required": False,
        "canonical_t0_payload_replaced": False, "physical_soil_created": False, "scientific_authority_register_mutated": False,
        "execution_indexes_mutated": False, "P7Q_reopened": False,
        "research_basis": [{"source": "Zahirovic et al. 2015, EPSL 418, 40-52", "doi": "10.1016/j.epsl.2015.02.037",
            "use": "broad Earth aggregate plausibility prior; does not identify a joint R6 per-plate motion realization"},
            {"source": "Brune et al. 2023, Nature Reviews Earth & Environment 4, 235-253", "doi": "10.1038/s43017-023-00391-3",
            "use": "inherited weakness affects rift localization in interaction with driving/resisting/weakening processes; does not justify mapping design-only ARCANA suture labels to mechanical weakness"}],
        "outputs": ["R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json", "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.md",
            "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json", "R6_T0_INITIAL_KINEMATICS_MANIFEST.json",
            "R6_T0_EVENT_ELIGIBILITY_CENSUS.json", "R6_T0_EVENT_ELIGIBILITY_CENSUS.md",
            "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.json", "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.md"],
        "protected_index_blobs": EXPECTED_INDEX_BLOBS,
        "non_goals": {"forward_simulation": False, "canonical_payload_overwrite": False, "provider_acquisition": False,
            "staging": False, "commit": False, "push": False}}
    _write_outputs(output_dir, payload_path, vector_manifest, kinematics, census, readiness, adjudication)
    print(json.dumps({"decision": adjudication["decision"], "verdict": adjudication["verdict"],
        "payload": payload_path.resolve().relative_to(external_root(ROOT).resolve()).as_posix(),
        "payload_root_environment_variable": "ARCANA_EXTERNAL_ROOT",
        "payload_bytes": payload_path.stat().st_size,
        "payload_sha256": _sha(payload_path.read_bytes()), "boundary_pairs": len(candidates),
        "boundary_edges": len(edge_rows), "index_blobs": EXPECTED_INDEX_BLOBS}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
