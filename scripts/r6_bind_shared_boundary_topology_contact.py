"""Build a t0-only shared-boundary census for the governed R6 partition.

This tool does not propose or execute a physical transition.  Its outputs are
an inspectable structural boundary graph and a diagnostic census at 210 Ma.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (
    external_root, require_repository_context, repository_provenance,
    resolve_external_payload_path,
    verify_protected_staged_blobs,
)
HEAD = "592b1651b405363373590092e133bd25569d99a5"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KIN_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
T0_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
VECTOR_PATH = external_root(ROOT) / "r6" / "tectonic_t0" / "R6_T0_VECTOR_PLATE_PARTITION.npz"
RADIUS_M = 6_371_000.0
ZERO_TOLERANCE_M_PER_YEAR = 1e-9  # diagnostic tolerance only; not a physical threshold


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write_new(name: str, obj: object) -> None:
    path = ROOT / name
    data = canonical(obj)
    if path.exists() and path.read_bytes() != data:
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            previous = {}
        same_authority = previous.get("artifact") == obj.get("artifact") and previous.get("parent_vector_partition_sha256") == VECTOR_SHA
        if not same_authority:
            raise FileExistsError(f"refusing to overwrite non-identical artifact outside this authority lineage: {path}")
    if not path.exists():
        path.write_bytes(data)
    elif path.read_bytes() != data:
        path.write_bytes(data)


def write_new_text(name: str, text: str) -> None:
    path = ROOT / name
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() != data:
        prior_title = path.read_text(encoding="utf-8").splitlines()[:1]
        if not prior_title or prior_title != text.splitlines()[:1]:
            raise FileExistsError(f"refusing to overwrite non-identical artifact outside this title lineage: {path}")
    if not path.exists():
        path.write_bytes(data)
    elif path.read_bytes() != data:
        path.write_bytes(data)


def verify_authorities() -> tuple[dict, dict, dict, dict]:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    for ref in ("origin/main",):
        actual = subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip()
        if actual != HEAD:
            raise RuntimeError(f"{ref} differs from governed baseline: {actual}")
    verify_protected_staged_blobs(ROOT, INDEX_BLOBS)
    part = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kin = read_json("R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    canonical_t0 = read_json("R6_CANONICAL_INITIAL_STATE_PACKAGE.json")
    rift = read_json("R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json")
    previous_readiness = read_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V4.json")
    previous_census = read_json("R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json")
    dt_register = read_json("R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json")
    if part["payload"]["sha256"] != VECTOR_SHA or part["canonical_parent_sha256"] != T0_SHA:
        raise RuntimeError("vector/t0 authority identity mismatch")
    if kin["payload_identity_sha256"] != KIN_SHA or kin["parent_vector_partition_sha256"] != VECTOR_SHA:
        raise RuntimeError("kinematics identity mismatch")
    if canonical_t0["materialized_payload"]["sha256"] != T0_SHA:
        raise RuntimeError("canonical physical t0 identity mismatch")
    physical_path = resolve_external_payload_path(ROOT, canonical_t0["materialized_payload"]["relative_path"])
    if not physical_path.is_file() or physical_path.stat().st_size != canonical_t0["materialized_payload"]["bytes"] or digest_file(physical_path) != T0_SHA:
        raise RuntimeError("canonical physical t0 payload missing or changed")
    if rift["initial_state"]["state"] != "RIFT_QUIESCENT_AT_EXACT_T0" or rift["initial_state"]["progress_m"] != 0.0:
        raise RuntimeError("rift initial state differs from governed t0")
    if rift["prohibitions"]["time_evolution_executed"] is not False:
        raise RuntimeError("rift authority already records time evolution")
    if previous_readiness["decision"] != "TOPOLOGY_CONTACT_GUARD_UNBOUND" or previous_readiness["forward_physical_evolution_executed"] is not False:
        raise RuntimeError("unexpected prior interval readiness/evolution state")
    if previous_census["time_evolution_executed"] is not False or len(previous_census["candidates"]) != 30:
        raise RuntimeError("unexpected prior event census state")
    if dt_register["derivation"]["dt_first_years"] is not None or dt_register["derivation"]["blocking_limit"] != "TOPOLOGY_CONTACT_GUARD":
        raise RuntimeError("unexpected pre-existing dt blocker")
    if not VECTOR_PATH.is_file() or VECTOR_PATH.stat().st_size != part["payload"]["bytes"] or digest_file(VECTOR_PATH) != VECTOR_SHA:
        raise RuntimeError("external vector partition payload identity mismatch")
    return part, kin, canonical_t0, rift


def xyz(lat_deg: float, lon_deg: float) -> np.ndarray:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)])


def vertex_key(row_v: int, col_v: int) -> str:
    if row_v == 0:
        return "SOUTH_POLE"
    if row_v == 180:
        return "NORTH_POLE"
    return f"GRID_VERTEX:{row_v}:{col_v % 360}"


def decompose_relative_velocity(delta_v: np.ndarray, normal_ab: np.ndarray, tangent: np.ndarray) -> tuple[float, float]:
    """Return signed A-to-B normal and oriented tangent components."""
    dv = np.asarray(delta_v, dtype=np.float64)
    n = np.asarray(normal_ab, dtype=np.float64)
    t = np.asarray(tangent, dtype=np.float64)
    if dv.shape != (3,) or n.shape != (3,) or t.shape != (3,) or not np.isfinite([*dv, *n, *t]).all():
        raise ValueError("relative velocity and unit directions must be finite 3-vectors")
    if not math.isclose(float(np.linalg.norm(n)), 1.0, abs_tol=1e-10) or not math.isclose(float(np.linalg.norm(t)), 1.0, abs_tol=1e-10):
        raise ValueError("normal and tangent must be unit vectors")
    if abs(float(np.dot(n, t))) > 1e-10:
        raise ValueError("normal and tangent must be orthogonal")
    return float(np.dot(dv, n)), float(np.dot(dv, t))


def main() -> None:
    part, kin, _, _ = verify_authorities()
    grid = part["parent_grid"]
    nrow, ncol = map(int, grid["shape"])
    face_lookup = np.full((nrow, ncol), -1, dtype=np.int16)
    plates = {int(x["plate_id"]): np.asarray(x["euler_vector_rad_per_year"], dtype=np.float64) for x in kin["plates"]}
    with np.load(VECTOR_PATH, allow_pickle=False) as z:
        face_lookup[z["face_row"].astype(int), z["face_col"].astype(int)] = z["face_plate_id"].astype(np.int16)
        rows, cols, axes = (z[k].astype(np.int64) for k in ("boundary_edge_row", "boundary_edge_col", "boundary_edge_axis"))
        pa, pb = (z[k].astype(np.int64) for k in ("boundary_plate_a", "boundary_plate_b"))
        lengths = z["boundary_length_m"].astype(np.float64)
    if np.any(face_lookup < 0) or len(rows) != 1983 or len(plates) != 12:
        raise RuntimeError("unexpected face/edge/plate cardinality")

    segments: list[dict] = []
    incidence: dict[str, list[str]] = defaultdict(list)
    class_lengths: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    normal_counts: Counter[str] = Counter()
    normal_lengths: Counter[str] = Counter()
    pair_acc: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for row, col, axis, a, b, length in zip(rows, cols, axes, pa, pb, lengths):
        row, col, axis, a, b = map(int, (row, col, axis, a, b))
        if not (0 <= row < nrow and 0 <= col < ncol and axis in (0, 1) and a < b and math.isfinite(float(length)) and length > 0):
            raise RuntimeError("invalid boundary record")
        side = int(face_lookup[row, col])
        if side not in (a, b):
            raise RuntimeError("canonical west/south side does not match plate pair")
        if axis == 0:  # meridian edge; canonical tangent is south -> north
            lat = -90.0 + row + 0.5
            lon = -180.0 + col + 1.0
            start, end = (row, (col + 1) % ncol), (row + 1, (col + 1) % ncol)
            tangent = np.array([-math.sin(math.radians(lat)) * math.cos(math.radians(lon)), -math.sin(math.radians(lat)) * math.sin(math.radians(lon)), math.cos(math.radians(lat))])
            normal = np.array([-math.sin(math.radians(lon)), math.cos(math.radians(lon)), 0.0])
        else:  # latitude edge; canonical tangent is west -> east
            lat = -90.0 + row + 1.0
            lon = -180.0 + col + 0.5
            start, end = (row + 1, col % ncol), (row + 1, (col + 1) % ncol)
            tangent = np.array([-math.sin(math.radians(lon)), math.cos(math.radians(lon)), 0.0])
            normal = np.array([-math.sin(math.radians(lat)) * math.cos(math.radians(lon)), -math.sin(math.radians(lat)) * math.sin(math.radians(lon)), math.cos(math.radians(lat))])
        if side != a:
            normal = -normal
        tangent /= np.linalg.norm(tangent)
        normal /= np.linalg.norm(normal)
        r = xyz(lat, lon)
        va = np.cross(plates[a], r) * RADIUS_M
        vb = np.cross(plates[b], r) * RADIUS_M
        dv = vb - va
        vn, vt = decompose_relative_velocity(dv, normal, tangent)
        if abs(vn) <= ZERO_TOLERANCE_M_PER_YEAR and abs(vt) <= ZERO_TOLERANCE_M_PER_YEAR:
            mode = "NEAR_ZERO"
        elif abs(vn) <= ZERO_TOLERANCE_M_PER_YEAR:
            mode = "SHEAR"
        elif abs(vt) <= ZERO_TOLERANCE_M_PER_YEAR:
            mode = "OPENING" if vn > 0 else "CLOSING"
        else:
            mode = "MIXED_OPENING_SHEAR" if vn > 0 else "MIXED_CLOSING_SHEAR"
        key = f"{row}:{col}:{axis}:{a}:{b}"
        bid = "R6BND-T0-" + sha256(f"{VECTOR_SHA}|{key}".encode()).hexdigest()[:20]
        id0, id1 = vertex_key(*start), vertex_key(*end)
        incidence[id0].append(bid)
        incidence[id1].append(bid)
        entry = {
            "boundary_id": bid, "parent_grid_edge": {"row": row, "column": col, "axis": "EAST" if axis == 0 else "NORTH"},
            "ordered_plate_pair": [a, b], "normal_convention": "n_AB points from plate_a to plate_b; positive signed normal relative velocity is opening",
            "tangent_convention": "increasing latitude for EAST edge; increasing longitude for NORTH edge",
            "endpoint_vertex_ids": [id0, id1], "support": "COARSE_SUPPORT_ON_FINE_GRID",
            "source_geometry": "CANONICAL_PARENT_CELL_FACE_EDGE; no smoothing or subcell inference",
            "length_m": float(length), "relative_normal_velocity_m_per_year": vn,
            "relative_tangential_velocity_m_per_year": vt, "local_kinematic_diagnostic": mode,
            "structural_state_only": True, "dynamic_boundary_accommodation_state": "NOT_MATERIALIZED",
            "boundary_process_class": "UNKNOWN_NOT_AUTHORIZED_BY_KINEMATICS_ALONE",
        }
        segments.append(entry)
        pair_acc[(a, b)].append(entry)
        class_counts[mode] += 1
        class_lengths[mode] += float(length)
        normal_class = "DIVERGENT" if vn > ZERO_TOLERANCE_M_PER_YEAR else "CONVERGENT" if vn < -ZERO_TOLERANCE_M_PER_YEAR else "NEAR_ZERO_NORMAL"
        normal_counts[normal_class] += 1
        normal_lengths[normal_class] += float(length)
    if len({x["boundary_id"] for x in segments}) != len(segments):
        raise RuntimeError("boundary ID collision")

    junctions = []
    for vid, edges in sorted(incidence.items()):
        unique = sorted(set(edges))
        if len(unique) >= 3:
            junctions.append({"junction_id": "R6JNT-T0-" + sha256(vid.encode()).hexdigest()[:16], "vertex_id": vid,
                              "incident_boundary_ids": unique, "degree": len(unique), "motion_rule": "UNBOUND", "status": "T0_INCIDENCE_ONLY"})
    pairs = []
    for (a, b), edge_set in sorted(pair_acc.items()):
        total = sum(x["length_m"] for x in edge_set)
        mean_n = sum(x["relative_normal_velocity_m_per_year"] * x["length_m"] for x in edge_set) / total
        mean_abs_t = sum(abs(x["relative_tangential_velocity_m_per_year"]) * x["length_m"] for x in edge_set) / total
        pairs.append({"pair_id": f"{a}:{b}", "edge_count": len(edge_set), "length_m": total,
                      "length_weighted_signed_normal_m_per_year": mean_n,
                      "length_weighted_absolute_tangential_m_per_year": mean_abs_t,
                      "local_mode_counts": dict(sorted(Counter(x["local_kinematic_diagnostic"] for x in edge_set).items()))})
    length_total = sum(x["length_m"] for x in segments)
    if len(segments) != 1983 or len(pairs) != 30 or not math.isclose(length_total, sum(float(x["length_m"]) for x in part["adjacency_groups"]), abs_tol=0.01, rel_tol=0):
        raise RuntimeError("boundary census does not reproduce parent manifest")

    manifest = {
        "artifact": "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST", "schema": "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST_V1",
        "time_ma": 210.0, "state_class": "STRUCTURAL_T0_INTERFACE_GRAPH_ONLY_NOT_A_DYNAMICAL_CHECKPOINT",
        "parent_vector_partition_sha256": VECTOR_SHA, "canonical_kinematics_sha256": KIN_SHA,
        "representation": "ONE_SHARED_RECORD_PER_CANONICAL_GRID_EDGE; adjacency polygons remain derived from the parent cell-face partition",
        "boundary_count": len(segments), "plate_pair_count": len(pairs), "junction_count_degree_ge_3": len(junctions),
        "support": "COARSE_SUPPORT_ON_FINE_GRID", "segments": segments, "junctions": junctions,
        "state_policy": {"opening_progress": "REFER_TO_EXISTING_RIFT_PROGRESS_LAW; not advanced; no duplicate accumulator created",
                         "shortening_accumulator": "NOT_CREATED; collision/contact law unbound", "tangential_slip_accumulator": "NOT_CREATED; fault/slip law unbound",
                         "boundary_width": "UNKNOWN_NOT_INFERRED", "process_classes": "UNKNOWN_NOT_ASSIGNED_FROM_MOTION"},
        "partition_at_t0": "INHERITED_VALIDATED_FROM_CANONICAL_PARENT; this manifest performs no polygon reconstruction or repair",
        "future_id_lineage": "IDs are stable for this exact parent grid/payload; remesh split/merge lineage must explicitly reference parent boundary IDs",
        "forward_evolution_executed": False,
    }
    census = {
        "artifact": "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS", "schema": "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS_V1",
        "time_ma": 210.0, "t0_only_diagnostic": True, "parent_vector_partition_sha256": VECTOR_SHA,
        "canonical_kinematics_sha256": KIN_SHA, "boundary_segment_count": len(segments), "adjacent_plate_pair_count": len(pairs),
        "total_boundary_length_m": length_total, "diagnostic_zero_tolerance_m_per_year": ZERO_TOLERANCE_M_PER_YEAR,
        "segment_class_counts": dict(sorted(class_counts.items())), "segment_class_length_m": dict(sorted(class_lengths.items())),
        "normal_sign_counts": dict(sorted(normal_counts.items())), "normal_sign_length_m": dict(sorted(normal_lengths.items())),
        "pairs": pairs, "segments": segments,
        "interpretation": "Relative kinematics only; classifications are local diagnostic signs/components, not geological boundary-type assignments or physical accommodation laws.",
        "time_evolution_executed": False,
    }

    active = [x for x in segments if x["local_kinematic_diagnostic"] not in ("NEAR_ZERO",)]
    convergent = [x for x in segments if x["relative_normal_velocity_m_per_year"] < -ZERO_TOLERANCE_M_PER_YEAR]
    divergent = [x for x in segments if x["relative_normal_velocity_m_per_year"] > ZERO_TOLERANCE_M_PER_YEAR]
    guard = {
        "artifact": "R6_TOPOLOGY_CONTACT_GUARD", "schema": "R6_TOPOLOGY_CONTACT_GUARD_V1", "time_ma": 210.0,
        "decision": "NO_POSITIVE_PARTITION_PRESERVING_TRANSITION_BOUND",
        "status": "BLOCKED_PHYSICAL_BOUNDARY_ACCOMMODATION_AND_JUNCTION_RULES_UNBOUND",
        "parent_vector_partition_sha256": VECTOR_SHA, "canonical_kinematics_sha256": KIN_SHA,
        "t0_predictive_geometry": "NOT_COMPUTED; no chosen shared-boundary motion or deformation-zone law exists",
        "segments_with_nonzero_relative_motion": len(active), "divergent_segments": len(divergent), "convergent_segments": len(convergent),
        "divergent_length_m": sum(x["length_m"] for x in divergent), "convergent_length_m": sum(x["length_m"] for x in convergent),
        "boundary_network_geometry": "A shared network avoids duplicate edge records at t0 but does not by itself absorb finite relative displacement.",
        "opening_before_rift_activation": "Existing rift progress is kinematic opening history, but no spatial deformation-zone width/geometry is authorized; cannot claim gap-free finite-time accommodation.",
        "convergence_before_collision_or_subduction": "No shortening/contact accommodation or collision/subduction law; any positive step has undefined physical response and may produce overlap under rigid interiors.",
        "transform_motion": "No authorized finite-width shear interface/remeshing law; signed relative tangential motion is diagnostic only.",
        "junction_guard": {"junction_count_degree_ge_3": len(junctions), "motion_rule": "UNBOUND", "status": "BLOCKING" if junctions else "NO_HIGHER_ORDER_JUNCTIONS"},
        "event_vs_numerical_failure": {"physical_event": "must be emitted only by a separately authorized process law and hand off at its event boundary",
                                       "numerical_failure": "self-intersection, invalid orientation, unresolved gap/overlap, or inconsistent junction from a proposed step; reject, do not snap/clip/fill"},
        "global_topology_guard_horizon_years": None, "first_positive_dt_authorized": False,
        "advance_allowed_segments": 0, "advance_allowed_with_accommodation_segments": 0,
        "event_guarded_segments": len(divergent), "blocked_physical_response_unbound_segments": len(convergent),
        "unknown_segments": sum(class_counts[k] for k in class_counts if k == "NEAR_ZERO"),
        "no_forward_evolution": True, "no_geometry_mutation": True,
    }

    readiness = {
        "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V5", "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V5",
        "repository": repository_provenance(ROOT), "t0_ma": 210.0,
        "decision": "CONVERGENT_BOUNDARY_PHYSICS_REQUIRED_BEFORE_FIRST_INTERVAL",
        "verdict": "PASS_T0_SHARED_BOUNDARY_CENSUS__BLOCKED_NO_AUTHORIZED_FINITE_TIME_ACCOMMODATION",
        "master_topology": "SHARED_BOUNDARY_NETWORK_IS_CANONICAL_INTERFACE_REPRESENTATION; parent cell-face partition remains immutable t0 geometry and polygons are derived views",
        "first_step": {"dt_first_years": None, "limiting_guard": "FINITE_TIME_SHARED_BOUNDARY_ACCOMMODATION_AND_TRIPLE_JUNCTION_MOTION_UNBOUND",
                       "rift_event_horizon_years": 27123.405156307464, "rift_horizon_is_legal_dt": False},
        "positive_interval": False, "forward_evolution_executed": False, "canonical_t0_changed": False,
        "canonical_kinematics_changed": False, "canonical_partition_changed": False,
        "next_action": "BIND_MINIMUM_SHARED_BOUNDARY_DEFORMATION_AND_JUNCTION_COMPATIBILITY_LAW_BEFORE_FIRST_INTERVAL",
    }

    rule = {
        "artifact": "R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE", "schema": "R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE_V1",
        "decision": "SHARED_BOUNDARY_NETWORK_BOUND_AS_MASTER_INTERFACE; TRANSITION_LAW_BLOCKED",
        "scope": "R6 synthetic t0 representation and positive-duration boundary semantics; no forward evolution",
        "parent_authorities": {"vector_partition_sha256": VECTOR_SHA, "canonical_kinematics_sha256": KIN_SHA,
                               "canonical_t0_sha256": T0_SHA, "rift_rule": "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"},
        "master_state_adjudication": {"selected": "SHARED_BOUNDARY_NETWORK", "rigid_interiors_retained": True,
            "independent_closed_polygon_rotation": "NOT_A_VALID_TRANSITION_RULE_WHEN_ADJACENT_PLATES_HAVE_DIFFERENT_ROTATIONS",
            "boundary_network_role": "one canonical shared geometric interface; polygons are derived from the network",
            "finite_width_deforming_zone": "NOT_BOUND; no width/support/state available", "backend_independent": True},
        "orientation": {"pair_order": "plate_a < plate_b, IDs from parent edge record", "normal": "unit tangent-plane normal from A toward B; positive (vB-vA) dot nAB means opening",
            "tangent": "increasing grid-coordinate direction along edge; signed shear diagnostic changes sign if tangent orientation reverses",
            "identity": "payload- and grid-keyed deterministic BOUNDARY_ID; no duplicate A/B copies"},
        "relative_motion": {"delta_v": "vB-vA", "normal_component": "dot(delta_v,nAB)", "tangential_component": "dot(delta_v,t_boundary)",
            "meaning": "diagnostic/process input only; not event typing or accommodation"},
        "boundary_motion_rule": "UNBOUND_FOR_POSITIVE_DT; symmetric half-stage is not adopted as a universal rule; one-sided attachment is not adopted without boundary-type authority; topology resolution alone does not define causal physical response",
        "process_semantics": {"divergent_pre_rift": "existing cumulative opening is the sole progress quantity; its geometric accommodation zone/width is undefined, so no physical partition-preserving transition is authorized",
            "convergent_pre_event": "no shortening/contact accommodation law; no overlap or silent crust removal permitted",
            "transform": "signed shear diagnostic only; no slip accumulator or fault mechanics authorized",
            "rift_split_spreading_subduction_collision_orogeny": "handoff to separately authorized event/process laws; no automatic continuation"},
        "junctions": {"identity": "canonical shared grid vertex; poles collapsed to one spherical point each", "t0_incidence_materialized": True,
            "positive_time_velocity_rule": "UNBOUND; pairwise means are not assumed compatible"},
        "topology_validation": ["closed loops", "complete spherical coverage within explicit area tolerance", "zero unintended overlap", "zero unintended gap", "valid junction incidence", "stable IDs and parent lineage"],
        "repair_prohibitions": ["nearest snapping", "nearest-plate gap filling", "arbitrary overlap clipping", "rasterize/vectorize repair"],
        "gplates_research_conclusion": "GPlates resolves shared topological sections and topological networks; deforming networks use a triangulated deforming region and rigid blocks. These are geometry/deformation reconstruction mechanisms, not ARCANA causal laws.",
        "pygplates_required": False, "pygplates_used": False, "half_stage_rotation": "documented in GPlates for tectonic sections such as spreading ridges; not generalized to stable, convergent, transform, or pre-rift boundaries",
        "no_forward_evolution": True,
    }

    write_new("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json", manifest)
    write_new("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json", census)
    write_new("R6_TOPOLOGY_CONTACT_GUARD.json", guard)
    write_new("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V5.json", readiness)
    write_new("R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE.json", rule)
    write_new_text("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.md", census_markdown(census))
    write_new_text("R6_TOPOLOGY_CONTACT_GUARD.md", guard_markdown(guard))
    write_new_text("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V5.md", readiness_markdown(readiness))
    write_new_text("R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE.md", rule_markdown(rule))
    print(json.dumps({"boundaries": len(segments), "pairs": len(pairs), "junctions": len(junctions),
                      "segment_class_counts": census["segment_class_counts"], "decision": readiness["decision"],
                      "dt_first_years": None}, sort_keys=True))


def census_markdown(x: dict) -> str:
    lines = ["# R6 shared-boundary t0 kinematic census", "", "Diagnostic evaluation at synthetic 210 Ma only. No geometry or process state advanced.",
             "", f"- Segments / plate pairs: {x['boundary_segment_count']} / {x['adjacent_plate_pair_count']}",
             f"- Total supported boundary length: {x['total_boundary_length_m']:.3f} m", f"- Local component classes: `{json.dumps(x['segment_class_counts'], sort_keys=True)}`",
             f"- Normal-sign counts/lengths (m): `{json.dumps(x['normal_sign_counts'], sort_keys=True)}` / `{json.dumps(x['normal_sign_length_m'], sort_keys=True)}`",
             f"- Length totals (m): `{json.dumps(x['segment_class_length_m'], sort_keys=True)}`", "", "## Plate-pair aggregates", "",
             "| Pair | Segments | Length (m) | Mean signed normal (m/y) | Mean absolute tangent (m/y) |", "|---|---:|---:|---:|---:|"]
    lines.extend(f"| {p['pair_id']} | {p['edge_count']} | {p['length_m']:.3f} | {p['length_weighted_signed_normal_m_per_year']:.8g} | {p['length_weighted_absolute_tangential_m_per_year']:.8g} |" for p in x["pairs"])
    lines += ["", "Local motion labels describe only the signed kinematic components; they do not assign ridge, trench, transform-fault, or other geological boundary classes.", ""]
    return "\n".join(lines)


def guard_markdown(x: dict) -> str:
    return ("# R6 topology/contact guard\n\n"
            f"Decision: **{x['decision']}**.\n\n"
            f"At t0, {x['divergent_segments']} segments diverge and {x['convergent_segments']} converge under the canonical relative-velocity diagnostic. A shared edge record prevents duplicated edge identity, but it is not a finite-time accommodation law. The divergent rift-progress variable has no authorized geometric width; convergence has no shortening/contact law; junction motion is unbound.\n\n"
            "Therefore there is no positive partition-validity horizon or legal dt. No predictive geometry was generated. Do not repair a trial transition by snapping, clipping, or raster fill.\n")


def readiness_markdown(x: dict) -> str:
    return ("# R6 first physical interval readiness V5\n\n"
            f"Decision: **{x['decision']}**\n\n{ x['verdict'] }.\n\n"
            "The t0 shared-boundary graph and kinematic census are materialized; positive-time boundary accommodation and junction compatibility are not. `dt_first_years = null`; no first-interval execution contract is authorized.\n")


def rule_markdown(x: dict) -> str:
    return ("# R6 shared-boundary motion and topology/contact rule\n\n"
            "## Adjudication\n\n"
            "Adopt one shared-boundary network as the canonical interface representation, retaining rigid plate interiors. This is a state representation, not authorization to evolve it. Keep the parent finite-volume cell faces as the immutable t0 source; derive per-plate polygons from the shared network only after a governed resolver exists.\n\n"
            "## Source-grounded geometric mechanisms\n\n"
            "GPlates topological polygons reference shared boundary sections, and its resolver reports the subsegments actually shared among resolved topologies. Its deforming topological networks add a triangulated deforming region and optional rigid blocks. These mechanisms establish that shared topological boundaries/networks are a viable representation; they do not choose ARCANA's physical laws. Half-stage reconstruction is documented for ridge/tectonic sections and is not a universal boundary law.\n\n"
            "## ARCANA t0 interface\n\n"
            "Each edge has a payload/grid-keyed ID, ordered plate IDs, A-to-B normal, deterministic tangent direction, support, endpoint/junction incidence, and t0 relative velocity components. No independent side copies are allowed. Existing rift progress remains the only opening-progress source; no duplicate opening accumulator is made. Shortening and slip accumulators are not created because their process semantics are unbound.\n\n"
            "## Positive-time law: blocked\n\n"
            "No universal average/half-stage boundary velocity is adopted. One-sided attachment requires boundary-type evidence. A zero-width shared line cannot store finite opening as a gap-free physical deformation, while rigidly moving convergent interiors can overlap. There is no authorized finite-width boundary zone, convergence/contact capacity, or multi-plate junction velocity rule. Topology software cannot supply these missing causal semantics.\n\n"
            "So the shared-network representation is bound at t0, but the transition law is not. No positive dt, topology guard horizon, forward checkpoint, or interval execution contract is authorized.\n\n"
            "## Sources\n\n"
            "- [GPlates User Manual: Topology and Crustal Deformation](https://www.gplates.org/docs/user-manual/)\n"
            "- [pyGPlates Primer: topological reconstruction and deforming networks](https://www.gplates.org/docs/pygplates/pygplates_primer)\n"
            "- [pyGPlates TopologicalSnapshot API](https://www.gplates.org/docs/pygplates/generated/pygplates.topologicalsnapshot)\n"
            "- [pyGPlates shared topological subsegments API](https://www.gplates.org/docs/pygplates/generated/pygplates.resolvedtopologicalsharedsubsegment)\n"
            "- [pyGPlates common feature example: half-stage ridge reconstruction](https://www.gplates.org/docs/pygplates/sample-code/pygplates_create_common_feature_types)\n")


if __name__ == "__main__":
    main()
