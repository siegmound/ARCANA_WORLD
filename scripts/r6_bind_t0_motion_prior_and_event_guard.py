"""Bind one t0-only synthetic R6 plate-motion realization and event guard.

No geometry is regenerated and no time evolution is performed.  All writes
are repository-scoped and fail closed against unexpected pre-existing files.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    resolve_external_payload_path, verify_protected_staged_blobs)
HEAD = "592b1651b405363373590092e133bd25569d99a5"
RADIUS_M = 6_371_000.0
EXPECTED_T0_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
EXPECTED_VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
EXPECTED_INDEX = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
PREIMAGE = {
    "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json": "4faf581f6807786daf779b481d92ae5f1dadb6f765fcdbb3dbe242d98bb3aad9",
    "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.md": "474901d2d3017bbe27047743534cff87e40d586fba7ef58726205732613a7a92",
    "R6_T0_INITIAL_KINEMATICS_MANIFEST.json": "a2e5757a43a072f5b8b4b0ef4c5e6e5aaf564faec5b652ddbcad95df126145e5",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS.json": "828c0fb1694d6e72e8b4debad7781df85be7e8888a874449139d2f4ead82af41",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS.md": "0d9be0d52e9a79fc813036db78bbca2965e2cdaf75254505c18589ef1fb03f7c",
    "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.json": "be6315eb50b619d36e61d01276c41925f53081d69744470080e7141983341e79",
    "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.md": "fa04780bfe9f064b560eaec5768325e48a4edb4f6a6e6af5d0be557cb0ebe5c9",
}
POSTIMAGE = {
    "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json": "77788494f62331ec4cf9dce9a2bc027335dd4e38db838610b8d9bb198e2cefb6",
    "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.md": "87d6dcfcca448e127f71cdbbb750f935c20b5cf67999125dd47ed517dcdea1f1",
    "R6_T0_INITIAL_KINEMATICS_MANIFEST.json": "039583b4416bc70ff7d87ea0da72b3547165b8febb68d594069096fa790eb27d",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS.json": "c8231e7cea815f250d3f3e77e1cef68ddbb82f958ae125231ed85e2fa290867f",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS.md": "961334a25cd05e018d0b3652be0bba22127ac3617e642611d02e025a8bd61866",
    "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.json": "607d957ac86ceaffd3eba8d072cd416319083daedda42bc25ae5c5e3f96c04aa",
    "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.md": "e6cf596b73c508dd5fd361c2f688b9f6c5667f0e27d94a2c3cd340eaf68f15fa",
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_repo() -> None:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    verify_protected_staged_blobs(ROOT, EXPECTED_INDEX)
    observed = {name: digest((ROOT / name).read_bytes()) if (ROOT / name).is_file() else None for name in PREIMAGE}
    if observed != PREIMAGE and observed != POSTIMAGE:
        raise RuntimeError("fail-closed: task parent artifacts are neither the governed pre-run nor this task's exact post-run set")


def write_new(name: str, obj: object) -> None:
    path = ROOT / name
    data = canonical(obj)
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f"refusing to overwrite non-identical output: {path}")
        return
    path.write_bytes(data)


def write_new_text(name: str, text: str) -> None:
    path = ROOT / name
    data = text.encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError(f"refusing to overwrite non-identical output: {path}")
        return
    path.write_bytes(data)


def replace_json(name: str, obj: object) -> None:
    (ROOT / name).write_bytes(canonical(obj))


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n <= 0 or not math.isfinite(n):
        raise RuntimeError("invalid zero/nonfinite spherical vector")
    return v / n


def cell_geometry(row: np.ndarray, col: np.ndarray, nlon: int) -> tuple[np.ndarray, np.ndarray]:
    lat = np.deg2rad(-90.0 + row.astype(np.float64) + 0.5)
    lon = np.deg2rad(-180.0 + col.astype(np.float64) + 0.5)
    r = np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))
    north = np.column_stack((-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)))
    return r, north


def main() -> None:
    verify_repo()
    contract = read_json("R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json")
    if contract.get("status") != "PRECOMMITTED_BEFORE_CANONICAL_DRAW":
        raise RuntimeError("prior contract is not precommitted")
    if contract["parent"]["vector_payload_sha256"] != EXPECTED_VECTOR_SHA or contract["parent"]["canonical_t0_sha256"] != EXPECTED_T0_SHA:
        raise RuntimeError("contract parent identity mismatch")
    if (contract["seed_lineage"]["acceptance_attempt_index"] != 1
            or contract["seed_lineage"]["maximum_attempts"] != 1
            or "Exactly one deterministic draw" not in contract["seed_lineage"]["candidate_sequence"]):
        raise RuntimeError("canonical realization selection rule mismatch")

    partition = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    if partition["canonical_parent_sha256"] != EXPECTED_T0_SHA or partition["payload"]["sha256"] != EXPECTED_VECTOR_SHA:
        raise RuntimeError("vector manifest parent identity mismatch")
    vector_path = resolve_external_payload_path(ROOT, partition["payload"]["path"])
    if not vector_path.is_file() or vector_path.stat().st_size != partition["payload"]["bytes"] or digest(vector_path.read_bytes()) != EXPECTED_VECTOR_SHA:
        raise RuntimeError("external vector payload missing or hash/size mismatch")
    parent = read_json("R6_CANONICAL_INITIAL_STATE_PACKAGE.json")
    parent_path = resolve_external_payload_path(ROOT, parent["materialized_payload"]["relative_path"])
    if parent["materialized_payload"]["sha256"] != EXPECTED_T0_SHA or not parent_path.is_file() or digest(parent_path.read_bytes()) != EXPECTED_T0_SHA:
        raise RuntimeError("canonical t0 payload missing or changed")

    with np.load(vector_path, allow_pickle=False) as z:
        rows = z["face_row"].astype(np.int64)
        cols = z["face_col"].astype(np.int64)
        plate_cells = z["face_plate_id"].astype(np.int64)
        erow = z["boundary_edge_row"].astype(np.int64)
        ecol = z["boundary_edge_col"].astype(np.int64)
        axis = z["boundary_edge_axis"].astype(np.int64)
        pa = z["boundary_plate_a"].astype(np.int64)
        pb = z["boundary_plate_b"].astype(np.int64)
        edge_len = z["boundary_length_m"].astype(np.float64)

    plate_ids = sorted(map(int, np.unique(plate_cells)))
    if plate_ids != list(range(12)) or len(erow) != 1983 or not (len(erow) == len(ecol) == len(axis) == len(pa) == len(pb) == len(edge_len)):
        raise RuntimeError("vector payload topology/count mismatch")
    nr, nc = map(int, partition["parent_grid"]["shape"])
    lookup = np.full((nr, nc), -1, dtype=np.int16)
    lookup[rows, cols] = plate_cells.astype(np.int16)
    if np.any(lookup < 0):
        raise RuntimeError("parent face-to-cell coverage incomplete")
    pair_length: dict[tuple[int, int], float] = defaultdict(float)
    pair_edges: dict[tuple[int, int], int] = defaultdict(int)
    for a, b, length in zip(pa, pb, edge_len):
        pair = (int(a), int(b))
        pair_length[pair] += float(length)
        pair_edges[pair] += 1
    manifest_pairs = {(int(g["plate_a"]), int(g["plate_b"])): g for g in partition["adjacency_groups"]}
    if set(pair_length) != set(manifest_pairs) or len(pair_length) != 30:
        raise RuntimeError("payload adjacency does not match manifest")
    for pair, group in manifest_pairs.items():
        if pair_edges[pair] != group["edge_count"] or not math.isclose(pair_length[pair], group["length_m"], abs_tol=0.002, rel_tol=0):
            raise RuntimeError(f"boundary pair mismatch: {pair}")

    # Cell areas on the exact canonical 1-degree spherical grid.
    sin_edges = np.sin(np.deg2rad(-90.0 + np.arange(nr + 1, dtype=np.float64)))
    per_row_area = RADIUS_M**2 * (2.0 * math.pi / nc) * (sin_edges[1:] - sin_edges[:-1])
    cell_area = per_row_area[rows]
    areas = np.bincount(plate_cells, weights=cell_area, minlength=12)
    if np.any(areas <= 0) or not math.isclose(float(areas.sum()), 4 * math.pi * RADIUS_M**2, rel_tol=1e-12):
        raise RuntimeError("plate area partition invalid")

    # Precommitted graph-covariance draw; ordering is part of this runner contract.
    n = len(plate_ids)
    adjacency = np.zeros((n, n), dtype=np.float64)
    for (a, b), length in pair_length.items():
        adjacency[a, b] = adjacency[b, a] = length
    degree = adjacency.sum(axis=1)
    if np.any(degree <= 0):
        raise RuntimeError("isolated plate in adjacency graph")
    w = adjacency / np.sqrt(np.outer(degree, degree))
    lap = np.eye(n) - w
    covariance = np.linalg.inv(np.eye(n) + lap)
    covariance = (covariance + covariance.T) / 2
    chol = np.linalg.cholesky(covariance)
    seed_meta = contract["seed_lineage"]
    seed_material = bytes.fromhex(seed_meta["root_digest_sha256"]) + b"\0" + seed_meta["generator_version"].encode() + b"\0" + seed_meta["semantic_stream_name"].encode()
    seed_digest = sha256(seed_material).digest()
    seed = int.from_bytes(seed_digest[:16], "big", signed=False)
    if f"{seed:032x}" != "" and seed != int(seed_meta.get("seed_uint128_hex", f"0x{seed:032x}"), 16):
        raise RuntimeError("derived seed mismatch")
    rng = np.random.Generator(np.random.PCG64(seed))
    raw = chol @ rng.standard_normal((n, 3))

    # Fit and remove the common rigid spin in the contracted surface-velocity LS sense.
    r, _ = cell_geometry(rows, cols, nc)
    proj = np.eye(3)[None, :, :] - r[:, :, None] * r[:, None, :]
    weighted_proj = proj * cell_area[:, None, None]
    matrix = weighted_proj.sum(axis=0)
    raw_cell_omega = raw[plate_cells]
    rhs = np.einsum("nij,nj->i", weighted_proj, raw_cell_omega)
    common = np.linalg.solve(matrix, rhs)
    gauged = raw - common[None, :]
    gauge_residual = np.linalg.solve(matrix, np.einsum("nij,nj->i", weighted_proj, gauged[plate_cells]))
    speed_before_scale = np.cross(gauged[plate_cells], r) * RADIUS_M
    rms_m_per_year = math.sqrt(float(np.sum(cell_area * np.sum(speed_before_scale**2, axis=1)) / cell_area.sum()))
    target_cm_year = float(rng.uniform(2.0, 10.0))
    scale = (target_cm_year / 100.0) / rms_m_per_year
    omega = gauged * scale
    speed_m_per_year = np.cross(omega[plate_cells], r) * RADIUS_M
    speed_cm_year = np.linalg.norm(speed_m_per_year, axis=1) * 100.0
    final_rms = math.sqrt(float(np.sum(cell_area * (speed_cm_year**2)) / cell_area.sum()))
    if not np.isfinite(omega).all() or not 2.0 <= final_rms <= 10.0 or abs(final_rms-target_cm_year) > 1e-10:
        raise RuntimeError("predeclared kinematic validity constraint failed")
    if np.linalg.norm(gauge_residual) > max(1e-15, 1e-12 * np.linalg.norm(gauged)):
        raise RuntimeError("NNR-like gauge residual exceeds predeclared tolerance")

    # Face-area-weighted representative point and per-plate surface RMS diagnostics.
    plate_records = []
    centroids = []
    for pid in plate_ids:
        mask = plate_cells == pid
        centroid = unit(np.sum(r[mask] * cell_area[mask, None], axis=0))
        centroids.append(centroid)
        v = np.cross(omega[pid], centroid) * RADIUS_M
        axis_norm = float(np.linalg.norm(omega[pid]))
        plate_speed = math.sqrt(float(np.sum(cell_area[mask] * np.sum(speed_m_per_year[mask]**2, axis=1)) / areas[pid])) * 100
        plate_records.append({
            "plate_id": pid,
            "euler_vector_rad_per_year": [float(x) for x in omega[pid]],
            "euler_vector_deg_per_myr": [float(x * 180 / math.pi * 1e6) for x in omega[pid]],
            "angular_speed_rad_per_year": axis_norm,
            "angular_speed_deg_per_myr": axis_norm * 180 / math.pi * 1e6,
            "euler_pole_unit_xyz": [float(x) for x in (omega[pid] / axis_norm if axis_norm else np.zeros(3))],
            "representative_surface_velocity_m_per_year_xyz": [float(x) for x in v],
            "plate_surface_rms_speed_cm_per_year": plate_speed,
            "area_m2": float(areas[pid]),
        })

    # Boundary-normal diagnostics are descriptive only; no boundary type or event is assigned.
    accum: dict[tuple[int, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row, col, ax, a, b, length in zip(erow, ecol, axis, pa, pb, edge_len):
        lat = math.radians(-90.0 + row + (0.5 if ax == 0 else 1.0))
        lon = math.radians(-180.0 + col + (1.0 if ax == 0 else 0.5))
        rr = np.array([math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat)])
        if ax == 0:
            normal = np.array([-math.sin(lon), math.cos(lon), 0.0])
            # payload's west/current cell is (row,col); east neighbor wraps longitude.
            west_pid = int(lookup[row, col])
            if west_pid != int(a) and west_pid != int(b):
                raise RuntimeError("east edge plate identity mismatch")
            if west_pid != int(a):
                normal = -normal
        elif ax == 1:
            normal = np.array([-math.sin(lat)*math.cos(lon), -math.sin(lat)*math.sin(lon), math.cos(lat)])
            south_pid = int(lookup[row, col])
            if south_pid != int(a) and south_pid != int(b):
                raise RuntimeError("north edge plate identity mismatch")
            if south_pid != int(a):
                normal = -normal
        else:
            raise RuntimeError("unknown boundary axis")
        relative = (np.cross(omega[int(b)], rr) - np.cross(omega[int(a)], rr)) * RADIUS_M * 100.0
        normal_rate = float(np.dot(relative, normal))
        tangential = math.sqrt(max(0.0, float(np.dot(relative, relative)) - normal_rate**2))
        q = accum[(int(a), int(b))]
        q["length"] += float(length)
        q["signed_normal_weighted"] += normal_rate * float(length)
        q["tangential_weighted"] += tangential * float(length)
        q["relative_speed_weighted"] += float(np.linalg.norm(relative)) * float(length)
    pair_records = []
    for (a, b), q in sorted(accum.items()):
        length = q["length"]
        signed = q["signed_normal_weighted"] / length
        pair_records.append({
            "plate_a": a, "plate_b": b, "boundary_length_m": length,
            "signed_normal_relative_speed_cm_per_year": signed,
            "opening_cm_per_year": max(0.0, signed),
            "convergence_cm_per_year": max(0.0, -signed),
            "tangential_relative_speed_cm_per_year": q["tangential_weighted"] / length,
            "relative_speed_cm_per_year": q["relative_speed_weighted"] / length,
            "eligibility": "UNKNOWN",
            "weak_zone_state": "UNKNOWN",
            "initial_process_state": "RIFT_QUIESCENT_AT_EXACT_T0",
            "event_guard_status": "BLOCKED_NO_GOVERNED_POSITIVE_LEAD_TIME_OR_TRIGGER_LAW",
        })
    if len(pair_records) != 30:
        raise RuntimeError("did not produce diagnostics for all 30 adjacent pairs")

    kin = {
        "artifact": "R6_T0_CANONICAL_PLATE_KINEMATICS",
        "schema": "R6_T0_CANONICAL_PLATE_KINEMATICS_V1",
        "time_ma": 210.0,
        "authority_class": "STOCHASTIC_CANONICAL_MODEL_REALIZATION",
        "not_empirical_or_earth_reconstruction": True,
        "runtime_identity": {"python": sys.version.split()[0], "numpy": np.__version__, "platform": platform.platform()},
        "prior_contract": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
        "prior_family": "A_GRAPH_CORRELATED_EULER_PRIOR",
        "prior_covariance_sha256": digest(np.ascontiguousarray(covariance).tobytes()),
        "seed_lineage": {**seed_meta, "seed_uint128_hex": f"0x{seed:032x}", "derivation_sha256": seed_digest.hex(), "attempt_index": 1},
        "canonical_realization_rule": "FIRST_DETERMINISTIC_SEEDED_REALIZATION_PASSING_PREDECLARED_HARD_CONSTRAINTS; exactly one draw and no rejection/resampling; attempt 1",
        "raw_generated_euler_vectors_rad_per_year": {str(i): [float(x) for x in raw[i]] for i in plate_ids},
        "gauge": {
            "name": "SYNTHETIC_AREA_WEIGHTED_LEAST_SQUARES_NO_NET_ROTATION_GAUGE",
            "common_spin_removed_rad_per_year": [float(x) for x in common],
            "post_gauge_residual_rad_per_year": [float(x) for x in gauge_residual],
            "post_gauge_scale_factor": float(scale),
            "target_global_surface_weighted_rms_cm_per_year": target_cm_year,
            "realized_global_surface_weighted_rms_cm_per_year": final_rms,
            "interpretation": "kinematic gauge only; not mantle frame or torque balance",
        },
        "plates": plate_records,
        "uncertainty": {
            "class": "MODEL_UNCERTAINTY; ONE_CANONICAL_MEMBER_OF_EXPLICIT_SYNTHETIC_PRIOR",
            "graph_correlation_and_scale_distribution_are_model_assumptions": True,
            "sensitivity_ensemble_executed": False,
            "future_outcome_used_for_selection": False,
        },
        "parent_vector_partition_sha256": EXPECTED_VECTOR_SHA,
        "parent_canonical_t0_sha256": EXPECTED_T0_SHA,
        "forward_evolution_executed": False,
        "topology_changed": False,
    }
    kin["payload_identity_sha256"] = digest(canonical(kin))
    write_new("R6_T0_CANONICAL_PLATE_KINEMATICS.json", kin)

    census_old = read_json("R6_T0_EVENT_ELIGIBILITY_CENSUS.json")
    old_by_pair = {(int(x["plate_a"]), int(x["plate_b"])): x for x in census_old["candidates"]}
    enriched = []
    for rec in pair_records:
        old = old_by_pair.get((rec["plate_a"], rec["plate_b"]))
        if old is None:
            raise RuntimeError("event census pair set mismatch")
        enriched.append({**old, **rec,
            "kinematic_driver": {
                "status": "COMPUTED_DIAGNOSTIC_ONLY",
                "signed_normal_relative_speed_cm_per_year": rec["signed_normal_relative_speed_cm_per_year"],
                "opening_cm_per_year": rec["opening_cm_per_year"],
                "convergence_cm_per_year": rec["convergence_cm_per_year"],
                "tangential_relative_speed_cm_per_year": rec["tangential_relative_speed_cm_per_year"],
                "relative_speed_cm_per_year": rec["relative_speed_cm_per_year"],
                "not_stress_strain_or_boundary_class_authority": True,
            },
            "missing_inputs": ["MECHANICALLY_AUTHORIZED_WEAK_ZONE_STATE", "RIFT_INITIATION_AND_SPLIT_LAWS", "POSITIVE_EVENT_LEAD_TIME"]})
    counts = {label: sum(row["eligibility"] == label for row in enriched) for label in ("UNKNOWN", "ELIGIBLE", "INELIGIBLE", "ACTIVE")}
    census = {**census_old, "candidate_pair_count": 30, "candidates": enriched, "counts": counts,
        "kinematics_manifest": "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "kinematics_sha256": kin["payload_identity_sha256"],
        "census_semantics": "Kinematic relative velocities are descriptive; eligibility stays tri-state UNKNOWN because weakness and initiation law remain unbound.",
        "time_evolution_executed": False}
    replace_json("R6_T0_EVENT_ELIGIBILITY_CENSUS.json", census)
    md = ("# R6 t0 event eligibility census\n\nAt 210 Ma, 30 positive-length adjacent plate-pair aggregates have kinematic diagnostics.\n\n"
          f"- UNKNOWN: {counts['UNKNOWN']}\n- ELIGIBLE: {counts['ELIGIBLE']}\n- INELIGIBLE: {counts['INELIGIBLE']}\n- ACTIVE: {counts['ACTIVE']}\n\n"
          "Opening, convergence, tangential and relative speeds are descriptive only. Eligibility remains UNKNOWN because mechanically supported weakness and rift initiation/split laws are not bound. No event or evolution was executed.\n")
    (ROOT / "R6_T0_EVENT_ELIGIBILITY_CENSUS.md").write_text(md, encoding="utf-8")

    guard = {
        "artifact": "R6_T0_FIRST_INTERVAL_EVENT_GUARD", "schema": "R6_T0_FIRST_INTERVAL_EVENT_GUARD_V1", "time_ma": 210.0,
        "initial_rift_state": "RIFT_QUIESCENT_AT_EXACT_T0",
        "assumption_scope": "synthetic ARCANA initial condition only; not a claim about Earth at 210 Ma",
        "active_candidate_set": [], "eligible_candidate_set": [],
        "unknown_candidate_set": [f"{x['plate_a']}:{x['plate_b']}" for x in enriched if x["eligibility"] == "UNKNOWN"],
        "unknown_candidate_count": counts["UNKNOWN"], "ineligible_candidate_count": counts["INELIGIBLE"], "active_candidate_count": counts["ACTIVE"],
        "weak_zone_or_susceptibility": "UNKNOWN; no province/suture-to-weakness inference",
        "positive_event_lead_time_lower_bound_ma": None,
        "earliest_possible_unresolved_transition_ma": None,
        "guard_horizon_ma": None,
        "decision": "BLOCK_FIRST_INTERVAL__NO_GOVERNED_POSITIVE_EVENT_LEAD_TIME",
        "blocking_authorities": ["P05_WEAK_ZONE_STATE", "P07_RIFT_ELIGIBILITY", "P08_RIFT_INITIATION_TRIGGER", "P09_PLATE_SPLIT_TOPOLOGY", "P11_NUMERICAL_STEP_LIMITS"],
        "quiescent_at_exact_t0_does_not_imply_positive_post_t0_delay": True,
        "kinematics_manifest": "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "event_census": "R6_T0_EVENT_ELIGIBILITY_CENSUS.json",
        "forward_evolution_executed": False, "event_created": False, "boundary_types_assigned": False,
    }
    write_new("R6_T0_FIRST_INTERVAL_EVENT_GUARD.json", guard)
    write_new_text("R6_T0_FIRST_INTERVAL_EVENT_GUARD.md",
        "# R6 t0 first-interval event guard\n\n"
        "At exact synthetic t0 (210 Ma), the initial process state is quiescent: no topology-changing rift is active at that instant. This is not a claim about Earth at 210 Ma and does not prohibit future rifting.\n\n"
        "All 30 adjacent-pair candidates remain UNKNOWN because mechanical weakness/susceptibility and rift eligibility/trigger/split laws are unbound. Exact-t0 quiescence does not imply a positive post-t0 delay. Earliest unresolved transition and guard horizon are therefore UNKNOWN/UNBOUND, and this guard blocks the first interval.\n\n"
        "No event, boundary classification, topology change, or time evolution occurred.\n")

    kin_manifest = {
        "schema": "R6_T0_INITIAL_KINEMATICS_MANIFEST_V2", "time_ma": 210.0,
        "status": "CANONICAL_SYNTHETIC_MODEL_REALIZATION_MATERIALIZED__FIRST_INTERVAL_BLOCKED",
        "authority_class": "STOCHASTIC_CANONICAL_MODEL_REALIZATION", "canonical_realization_materialized": True,
        "prior_contract": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
        "kinematics_artifact": "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "kinematics_sha256": kin["payload_identity_sha256"],
        "plate_count": 12, "reference_frame": contract["reference_frame"]["name"],
        "selection_rule": kin["canonical_realization_rule"], "gauge_validation": "PASS_AREA_WEIGHTED_SURFACE_VELOCITY_LEAST_SQUARES",
        "global_surface_weighted_rms_cm_per_year": final_rms,
        "uncertainty": kin["uncertainty"], "a1_or_earth_trajectory_fit": False,
        "first_segment_motion_change": "NOT_EXERCISED_INSIDE_FIRST_SEGMENT; segment renewal law remains unbound",
        "forward_evolution_executed": False,
    }
    replace_json("R6_T0_INITIAL_KINEMATICS_MANIFEST.json", kin_manifest)

    readiness = read_json("R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.json")
    readiness.update({
        "decision": "BLOCKED_FIRST_INTERVAL_EVENT_GUARD_AND_NUMERICAL_LIMITS_UNBOUND",
        "candidate_event_state": "UNKNOWN",
        "kinematics_bound": True,
        "kinematics_manifest": "R6_T0_INITIAL_KINEMATICS_MANIFEST.json",
        "unknown_event_guard": "BLOCKED_NO_GOVERNED_STRICTLY_POSITIVE_EVENT_TIME_LOWER_BOUND",
        "strictly_positive_event_time_lower_bound_ma": None,
        "motion_validity_horizon_ma": None,
        "displacement_or_error_tolerance": None,
        "active_constraints": [], "first_dt_ma": None,
        "first_interval_contract_created": False, "first_interval_executable": False,
        "forward_evolution_executed": False,
        "P03_motion_change_law": "NOT_EXERCISED_INSIDE_FIRST_SEGMENT; RENEWAL_LAW_UNBOUND",
        "P08_rift_initiation_law": "UNBOUND; UNKNOWN_CANDIDATES_CANNOT_BE_CROSSED",
        "P09_plate_split_law": "UNBOUND; NO_EVENT_GUARD_HORIZON",
        "blocker_family": "R6_FIRST_INTERVAL_EVENT_GUARD_AND_NUMERICAL_LIMITS",
    })
    replace_json("R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.json", readiness)
    (ROOT / "R6_FIRST_PHYSICAL_INTERVAL_NUMERICAL_READINESS.md").write_text(
        "# R6 first physical interval numerical readiness\n\nDecision: `BLOCKED_FIRST_INTERVAL_EVENT_GUARD_AND_NUMERICAL_LIMITS_UNBOUND`.\n\n"
        "A deterministic t0 Euler realization is bound, but the first interval remains blocked. Rift eligibility is UNKNOWN for all 30 adjacent pairs, the initiation/split laws provide no strictly positive event-time lower bound, and displacement/error tolerances and motion-validity horizon remain unbound. No dt is assigned and no evolution occurred.\n", encoding="utf-8")

    state = read_json("R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json")
    state.update({
        "decision": "T0_MOTION_PRIOR_CANONICALIZED__FIRST_INTERVAL_BLOCKED_UNKNOWN_RIFT_ELIGIBILITY_AND_UNBOUND_DT",
        "verdict": "PASS_T0_CANONICAL_SYNTHETIC_KINEMATICS_AND_EVENT_GUARD__FIRST_INTERVAL_BLOCKED",
        "initial_motion": "CANONICAL_SYNTHETIC_MODEL_REALIZATION",
        "initial_motion_authority": "STOCHASTIC_CANONICAL_MODEL_REALIZATION",
        "motion_prior_contract": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
        "kinematics_manifest": "R6_T0_INITIAL_KINEMATICS_MANIFEST.json",
        "event_guard": "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json",
        "first_interval_contract_created": False, "first_interval_scientifically_executable": False,
        "first_legal_dt_determinable": False, "first_legal_dt_ma": None,
        "no_bulk_rotation_validation": "PASS_AREA_WEIGHTED_SURFACE_VELOCITY_LEAST_SQUARES_GAUGE",
        "extensional_forcing_at_t0": "KINEMATIC_RELATIVE_VELOCITY_DIAGNOSTIC_ONLY; weak-zone and rift law remain UNKNOWN",
        "rift_eligibility_census": "30_UNKNOWN_PRESERVED_WITH_KINEMATIC_DIAGNOSTICS",
        "rift_unknown": 30, "rift_eligible": 0, "rift_ineligible": 0, "rift_active": 0,
        "weak_zone_state": "UNKNOWN", "initial_rift_state": "RIFT_QUIESCENT_AT_EXACT_T0",
        "scientific_evolution_executed": False,
        "requirements_P01_P12": {
            "P01": "BOUND_STOCHASTIC_CANONICAL_MODEL_REALIZATION; NOT_EMPIRICAL",
            "P02": "INITIAL_STATE_BOUND; TEMPORAL_SEGMENT_VALIDITY_UNBOUND",
            "P03": "NOT_EXERCISED_INSIDE_FIRST_SEGMENT; RENEWAL_LAW_UNBOUND",
            "P04": "MATERIALIZED_AND_VALIDATED",
            "P05": "EXPLICIT_UNKNOWN_RETAINED",
            "P06": "RELATIVE_KINEMATIC_DIAGNOSTICS_COMPUTED; NOT_FORCE_OR_STRESS",
            "P07": "UNKNOWN_PRESERVED_FOR_ALL_30_PAIRS",
            "P08": "UNBOUND; FIRST_INTERVAL_GUARD_BLOCKS",
            "P09": "UNBOUND; FIRST_INTERVAL_GUARD_BLOCKS",
            "P10": "RERUN_WITH_KINEMATICS; UNKNOWN_PRESERVED",
            "P11": "BLOCKED_NO_EVENT_HORIZON_OR_NUMERICAL_LIMITS",
            "P12": "MODEL_UNCERTAINTY_AND_SINGLE_CANONICAL_MEMBER_RECORDED"
        },
        "remaining_blocker": "FIRST_INTERVAL_EVENT_GUARD_AND_NUMERICAL_LIMITS_UNBOUND",
        "next_action": "BIND_RIFT_TRIGGER_OR_POSITIVE_EVENT_GUARD_AND_NUMERICAL_STEP_LIMITS_BEFORE_FIRST_INTERVAL",
        "outputs": list(dict.fromkeys(state["outputs"] + [
            "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json", "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.md",
            "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json", "R6_T0_FIRST_INTERVAL_EVENT_GUARD.md",
            "R6_T0_MOTION_PRIOR_ADJUDICATION.json", "R6_T0_MOTION_PRIOR_ADJUDICATION.md",
            "scripts/r6_bind_t0_motion_prior_and_event_guard.py"
        ])),
    })
    replace_json("R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json", state)
    (ROOT / "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.md").write_text(
        "# R6 t0 synthetic tectonic-state canonicalization\n\n"
        f"Decision: `{state['decision']}`\n\nVerdict: `{state['verdict']}`\n\n"
        "A seeded graph-correlated Euler prior now defines one canonical synthetic t0 motion realization under an explicit area-weighted no-net-rotation kinematic gauge. It is model-derived, outcome-blind, and not an empirical Earth reconstruction. Relative motions are diagnostics only.\n\n"
        "The synthetic initial state is rift-quiescent at the exact t0 instant; inherited weakness remains UNKNOWN. Quiescence does not imply a positive event lead time. All 30 event candidates remain UNKNOWN, so the first interval has no governed event horizon or legal dt. No time evolution, event, topology change, or canonical t0 payload mutation occurred.\n", encoding="utf-8")

    adjudication = {
        "artifact": "R6_T0_MOTION_PRIOR_ADJUDICATION", "schema": "R6_T0_MOTION_PRIOR_ADJUDICATION_V1",
        "decision": "CANONICALIZE_STOCHASTIC_SYNTHETIC_T0_MOTION__KEEP_FIRST_INTERVAL_BLOCKED",
        "verdict": "PASS_CANONICAL_T0_MOTION_REALIZATION__BLOCKED_NO_POSITIVE_RIFT_EVENT_GUARD",
        "selected_family": "A_GRAPH_CORRELATED_EULER_PRIOR", "rejected_families": ["B_SMOOTH_TANGENTIAL_FIELD_RIGID_FIT", "C_REDUCED_FORCE_TORQUE"],
        "kinematics": "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "event_guard": "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json",
        "first_interval_execution_contract_created": False, "first_dt_ma": None,
        "forward_evolution_executed": False, "earth_history_reconstruction": False,
        "canonical_t0_payload_changed": False, "vector_partition_changed": False,
        "scientific_authority_register_mutated": False, "protected_execution_indexes_mutated": False,
        "provider_acquisition": False, "P7Q_reopened": False, "physical_soil_created": False,
    }
    write_new("R6_T0_MOTION_PRIOR_ADJUDICATION.json", adjudication)
    write_new_text("R6_T0_MOTION_PRIOR_ADJUDICATION.md",
        "# R6 t0 motion-prior and event-guard adjudication\n\n"
        f"Decision: `{adjudication['decision']}`\n\nVerdict: `{adjudication['verdict']}`\n\n"
        "A seeded graph-correlated Euler prior provides a transparent canonical realization for the synthetic world. Earth evidence is limited to broad plausibility context; this is not observed paleogeology, a force-balance solution, or an empirically identified ARCANA velocity field.\n\n"
        "The initial condition is rift-quiescent at exact t0, but weak-zone support and initiation/split laws remain unknown. No scientifically justified positive event lead-time bound is available. The first interval is blocked; no dt, event, topology change, or time evolution is produced.\n\n"
        f"Next action: `{state['next_action']}`\n")
    print(json.dumps({"status": "PASS_T0_MOTION_BOUND__INTERVAL_BLOCKED", "seed": f"0x{seed:032x}", "global_rms_cm_year": final_rms, "pairs": len(pair_records), "unknown": counts["UNKNOWN"]}, indent=2))


if __name__ == "__main__":
    main()
