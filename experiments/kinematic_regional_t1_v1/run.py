"""Source-bound, prescribed rigid regional transport using R6 history."""

from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import numpy as np

from arcana_worldsim.r6 import finite_rotation
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import BranchId, HistoryId, thaw_json
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh import coordinates, feg
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import HistoricalSnapshot, SimulationCheckpoint


ROOT = Path(__file__).resolve().parents[2]
REGION = ROOT.parent / "ARCANA_WORLD_EVIDENCE/R6/SHELLSET_REGIONAL_CASE_20261118_01"
B6J = ROOT / "outputs/r6_b6j_first_dt_adjudication"
LABEL = "PRESCRIBED_KINEMATIC_ONLY"
DOMAIN = "REGIONAL_PLATE_KINEMATICS"
CLOCK = "MODEL_YEARS_SINCE_ARCANA_T0"
RADIUS = 6_371_000.0
TARGET = 10
MIDPOINT = 5
EULER = "R6_T0_CANONICAL_PLATE_KINEMATICS.json"
LAW = "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"
B6I = "outputs/r6_b6i_first_segment_topology_model_extension/"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, payload):
    with path.open("x") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")


def relative(path):
    return str(path.relative_to(ROOT.parent))


def load_inputs():
    pins = {}

    def pin(path, expected=None):
        actual = digest(path)
        require(expected is None or actual == expected, f"SHA mismatch: {path}")
        pins[relative(path)] = actual
        return path

    regional = read(pin(REGION / "MANIFEST.json",
                        "39072160dc78ef280bd423c04fd510754e1a9a775ac9f002ab6f4a182d7cfd90"))
    for name, expected in regional["files"].items():
        pin(REGION / name, expected)
    case = read(REGION / "CASE.json")
    for name, expected in case["source_sha256"].items():
        pin(ROOT / name, expected)

    manifest = read(pin(B6J / "B6J_ARTIFACT_MANIFEST.json",
                        "b6f8780c91a64cfac74b0617845f6145059fd10fecee1131131c7dc42d8cc700"))
    entries = {row["relative_path"]: row["sha256"] for row in manifest["artifacts"]}
    for name in ("B6J_DT_SELECTION.json", "B6J_DT_PROVENANCE.json",
                 "B6J_ACTIVE_CONSTRAINT_SET.json", "B6J_ENDPOINT_POLICY.json",
                 "B6J_TARGET_AGE.json"):
        pin(B6J / name, entries[name])
    evidence = read(B6J / "B6J_DT_PROVENANCE.json")["source_qualified_evidence"]
    bound = read(pin(ROOT / (B6I + "B6I_TOPOLOGY_VALIDITY_BOUND.json"),
                     evidence[B6I + "B6I_TOPOLOGY_VALIDITY_BOUND.json"]))
    registry = read(pin(ROOT / (B6I + "B6I_TOPOLOGY_PROCESS_REGISTRY.json"),
                        evidence[B6I + "B6I_TOPOLOGY_PROCESS_REGISTRY.json"]))
    pin(ROOT / LAW, evidence[LAW])
    require(read(ROOT / LAW)["first_segment_policy"]["motion"].startswith(
        "Hold the canonical t0 Euler state constant only through the first segment"),
        "fixed Euler interval policy missing")
    enabled = [p["event_class"] for p in registry["processes"]
               if p["first_segment_status"] == "ENABLED"]
    require(registry["topology_hold_rule"] == "FIRST_SEGMENT_TOPOLOGY_HOLD_UNTIL_ENABLED_EVENT"
            and enabled == ["RIFT_PROCESS_ACTIVATION"]
            and registry["unknown_event_policy"].startswith("FAIL_CLOSED")
            and bound["status"] == "FIRST_SEGMENT_POSITIVE_TOPOLOGY_BOUND_QUALIFIED"
            and bound["limiting_enabled_event"] == enabled[0]
            and bound["unit"] == "year"
            and bound["value"] == read(B6J / "B6J_DT_SELECTION.json")["value"],
            "unsupported first-segment event calendar")
    require(0 < MIDPOINT < TARGET < bound["value"], "target reaches event horizon")

    freeze = read(pin(ROOT / "outputs/r6_b6k_isolated_first_candidate_state/B6K_SOURCE_FREEZE.json",
                      "c543cf0f66f201ac7a0a57eeb9d7266b31f6b10a87f7fcbdfd01a2c28e09cd9a"))
    euler = read(ROOT / EULER)
    require(any(isinstance(table, dict)
                and table.get(EULER, {}).get("sha256") == case["source_sha256"][EULER]
                and any(isinstance(row, dict) and row.get("sha256") ==
                        euler["parent_canonical_t0_sha256"] for row in table.values())
                for table in freeze.values()), "incompatible T0 realization")
    require(case["time_age_ma"] == 210 and case["plate_id"] == 5
            and euler["time_ma"] == read(B6J / "B6J_TARGET_AGE.json")["source_age_ma"] == 210
            and sorted(p["plate_id"] for p in euler["plates"]) == list(range(12)),
            "incompatible regional domain or Euler inventory")
    pre = read(ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json")
    lineage = pre["projection_source_lineage"]
    require(lineage["kinematics_sha256"] == euler["payload_identity_sha256"]
            and lineage["physical_geography_sha256"] == euler["parent_canonical_t0_sha256"]
            and lineage["vector_partition_sha256"] == euler["parent_vector_partition_sha256"],
            "PRE and Euler describe different T0 realizations")
    partition = read(ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    pin(resolve_external_payload_path(ROOT, partition["payload"]["path"]),
        euler["parent_vector_partition_sha256"])
    geography = ROOT.parent / (
        "_ARCANA_EXTERNAL_SOURCES/r6/initial_world/"
        "r6run_2688234592b36fcdfe43428725d1369927c7f7625929c9ee1aad7f123ac9ba2b/"
        "R6_INITIAL_PHYSICAL_GEOGRAPHY.npz")
    pin(geography, euler["parent_canonical_t0_sha256"])
    omega = next(p["euler_vector_rad_per_year"] for p in euler["plates"] if p["plate_id"] == 5)
    require(len(omega) == 3 and all(map(math.isfinite, omega)) and math.hypot(*omega) > 0,
            "invalid Euler rate")
    for source in (__file__, finite_rotation.__file__, coordinates.__file__, feg.__file__,
                   sys.modules[HistoryStore.__module__].__file__,
                   sys.modules[DomainStateEnvelope.__module__].__file__,
                   sys.modules[HistoricalSnapshot.__module__].__file__,
                   sys.modules[ForcingRecord.__module__].__file__,
                   sys.modules[ProvenanceRecord.__module__].__file__,
                   sys.modules[HistoryId.__module__].__file__):
        pin(Path(source).resolve())

    forcing = {
        "label": LABEL, "plate_id": 5, "euler_rad_per_year": omega,
        "gauge": euler["gauge"]["name"],
        "euler_payload_sha256": euler["payload_identity_sha256"],
        "parent_canonical_t0_sha256": euler["parent_canonical_t0_sha256"],
        "age_t0_ma": case["time_age_ma"], "analysis_end_year": TARGET,
        "event_horizon_year_open": bound["value"], "limiting_pair": bound["limiting_entity_pair"],
        "enabled_events": enabled, "events_in_experiment": [],
        "event_scope": registry["model_scope"],
        "coordinate_frame": "ARCANA_T0_CANONICAL_XYZ",
    }
    return case, pins, forcing


def initial_state(case):
    mesh = feg.parse_feg((REGION / "regional.feg").read_text(), mode="SHELLS_READY")
    require(len(mesh.nodes) == 9 and len(mesh.elements) == 8 and not mesh.faults,
            "unexpected regional mesh")
    nodes = [{"local_id": n["local_id"], "parent_id": n["parent_id"], "pre_t0": n["PRE"],
              "canonical_lat_lon_t0_deg": n["canonical_lat_lon_deg"],
              "boundary_tag_t0": n["boundary_tag"]} for n in case["nodes"]]
    for node, wire in zip(nodes, mesh.nodes, strict=True):
        require(node["local_id"] == wire.node_id and node["parent_id"] == node["pre_t0"]["node_id"],
                "incompatible PRE or FEG node identity")
        require(node["pre_t0"]["crust_thickness_m"] == wire.crustal_thickness_m and
                node["pre_t0"]["mantle_lithosphere_thickness_m"] ==
                wire.mantle_lithosphere_thickness_m, "incompatible layer thickness")
    elements = []
    for row, face in zip(case["elements"], mesh.elements, strict=True):
        require(row["local_id"] == face.element_id, "incompatible element identity")
        elements.append({**row, "local_node_ids": list(face.node_ids),
                         "parent_node_ids": [nodes[i - 1]["parent_id"] for i in face.node_ids]})
    xyz = coordinates._unit_vectors([n["canonical_lat_lon_t0_deg"] for n in nodes])
    forward, _ = coordinates.rotation_matrices()
    runtime = coordinates._unit_vectors([[n.latitude_deg, n.longitude_deg] for n in mesh.nodes])
    error = float(np.max(np.abs(xyz @ forward.T - runtime)))
    require(error <= 2e-14, "source frame mismatch")
    static = {"nodes": nodes, "triangles": elements, "radius_m": RADIUS, "plate_id": 5,
              "parent_cells_t0": case["cells"], "pre_validity_model_year": 0,
              "reference_frame_at_t0": coordinates.RUNTIME_FRAME_ID}
    return {"year": 0, "age_ma": 210.0, "canonical_xyz": xyz.tolist(),
            "label": LABEL, "static": static}, error


def advance(state, forcing, end):
    old = state["year"]
    require(0 <= old < end <= forcing["analysis_end_year"] < forcing["event_horizon_year_open"],
            "step outside the scoped positive interval")
    require(state["age_ma"] == forcing["age_t0_ma"] - old / 1e6
            and state["static"]["plate_id"] == forcing["plate_id"] and state["label"] == LABEL,
            "incompatible restart state")
    positions = finite_rotation.rotate_points_constant_euler(
        state["canonical_xyz"], forcing["euler_rad_per_year"], end - old)
    return {**state, "year": end, "age_ma": forcing["age_t0_ma"] - end / 1e6,
            "canonical_xyz": [list(p) for p in positions]}


def signed_areas(xyz, faces):
    a, b, c = np.moveaxis(xyz[faces], 1, 0)
    dot = lambda x, y: np.einsum("ij,ij->i", x, y)
    return 2 * np.arctan2(dot(a, np.cross(b, c)), 1 + dot(a, b) + dot(b, c) + dot(c, a))


def geometry_checks(t0, t1, forcing):
    require(t0["static"] == t1["static"], "passive support or material properties changed")
    static = t0["static"]
    x, y = (np.asarray(state["canonical_xyz"]) for state in (t0, t1))
    faces = np.array([row["local_node_ids"] for row in static["triangles"]]) - 1
    a0, a1 = signed_areas(x, faces), signed_areas(y, faces)
    archive_area = np.array([row["area_m2"] for row in static["triangles"]])
    require(np.all(np.sign(a0) == np.sign(a1)) and np.all(a0 != 0)
            and np.max(np.abs(np.abs(a0) * RADIUS**2 / archive_area - 1)) < 2e-12,
            "orientation or sealed T0 area discrepancy")
    area_error = np.abs(a1 - a0) / np.abs(a0)
    i, j = np.array(list(combinations(range(len(x)), 2))).T

    def arc(left, right):
        return RADIUS * np.arctan2(np.linalg.norm(np.cross(left, right), axis=1),
                                   np.einsum("ij,ij->i", left, right))

    distance_error = float(np.max(np.abs(arc(x[i], x[j]) - arc(y[i], y[j]))))
    norm_error = float(np.max(np.abs(np.linalg.norm(y, axis=1) - 1)))
    require(np.max(area_error) < 2e-12 and distance_error < 1e-7 and norm_error < 2e-15,
            "rigid transport geometry invariant failed")

    # A lumped reference mass from the spherical layers and PRE nodal densities.
    def sector_per_sr(top, thickness, density):
        bottom = top - thickness
        return density * thickness * (top * top + top * bottom + bottom * bottom) / 3

    crust = []
    mantle = []
    for node in static["nodes"]:
        pre = node["pre_t0"]
        h = pre["crust_thickness_m"]
        crust.append(sector_per_sr(RADIUS, h, pre["crust_density_kg_m3"]))
        mantle.append(sector_per_sr(RADIUS - h, pre["mantle_lithosphere_thickness_m"],
                                    pre["mantle_density_kg_m3"]))
    masses = {}
    for layer, values in (("crust", crust), ("mantle_lithosphere", mantle)):
        per_sr = np.mean(np.array(values)[faces], axis=1)
        m0, m1 = np.dot(np.abs(a0), per_sr), np.dot(np.abs(a1), per_sr)
        relative_error = abs(m1 - m0) / m0
        require(relative_error < 2e-12, f"rigid reference mass failed: {layer}")
        masses[layer] = {"t0_kg": float(m0), "t1_kg": float(m1),
                         "relative_difference": float(relative_error)}

    omega = np.asarray(forcing["euler_rad_per_year"])
    wx, wy, wz = omega
    gradient = np.array([[0, -wz, wy], [wz, 0, -wx], [-wy, wx, 0]])
    tangent = np.eye(3) - y[:, :, None] * y[:, None, :]
    projected = tangent @ gradient @ tangent
    symmetric = (projected + projected.transpose(0, 2, 1)) / 2
    symmetric_error = float(np.max(np.abs(symmetric)))
    # Independent Rodrigues evaluation uses the same model but a different formula.
    axis = omega / np.linalg.norm(omega)
    angle = np.linalg.norm(omega) * (t1["year"] - t0["year"])
    oracle = (x * np.cos(angle) + np.cross(axis, x) * np.sin(angle)
              + (x @ axis)[:, None] * axis * (2 * np.sin(angle / 2)**2))
    oracle_error = float(np.max(np.abs(oracle - y)))
    displacement = arc(x, y)
    require(symmetric_error < 1e-22 and oracle_error < 2e-15 and np.min(displacement) > 0,
            "Euler transport oracle failed")
    return {
        "pair_count": len(i), "max_pair_distance_change_m": distance_error,
        "triangle_orientation_preserved": True, "max_unit_norm_error": norm_error,
        "max_area_relative_change": float(np.max(area_error)),
        "max_area_change_m2": float(np.max(np.abs(a1 - a0)) * RADIUS**2),
        "surface_area_t0_m2": float(np.sum(np.abs(a0)) * RADIUS**2),
        "min_node_displacement_m": float(np.min(displacement)),
        "max_node_displacement_m": float(np.max(displacement)),
        "rotation_angle_rad": float(angle), "reference_layer_mass": masses,
        "thickness_and_material_payloads_identical": True,
        "ambient_symmetric_gradient_per_year": float(np.max(np.abs((gradient + gradient.T) / 2))),
        "max_tangential_symmetric_gradient_per_year": symmetric_error,
        "rodrigues_xyz_max_abs_difference": oracle_error,
    }


def publish(path, t0, endpoint, law, pins, branch_name):
    history = str(HistoryId.from_payload({"sources": pins, "law": law, "scope": LABEL}))
    branch = str(BranchId.from_payload({"history": history, "name": branch_name}))
    support = SpatialSupport("ARCANA_T0_FEG_PARENT_CELLS",
                             tuple(f"R{r:03}C{c:03}" for r, c in t0["static"]["parent_cells_t0"]),
                             "T0 parent IDs; coordinates of transported triangles in state payload")
    refs = tuple("sha256:" + value for value in sorted(set(pins.values())))
    provenance = ProvenanceRecord.create(activity=LABEL, source_refs=refs,
                                         attributes={"branch": branch_name, "physical_mechanics": False})
    forcing = ForcingRecord.create(
        history_id=history, branch_id=branch, forcing_kind="FIXED_CANONICAL_T0_EULER",
        domain=DOMAIN, time_support=TimeSupport(f"0/{TARGET}", CLOCK, "INTERVAL"),
        spatial_support=support, support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY, value=law, source_refs=refs,
        provenance_ids=(str(provenance.record_id),))
    store = HistoryStore(path)
    parent = ()
    results = {}
    for index, state in enumerate((t0, endpoint)):
        year = str(state["year"])
        record = DomainStateEnvelope.create(
            history_id=history, branch_id=branch, domain=DOMAIN,
            time_support=TimeSupport(year, CLOCK, "SNAPSHOT"), spatial_support=support,
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            parent_state_ids=parent, provenance_ids=(str(provenance.record_id),),
            value={**state, "forcing_id": str(forcing.forcing_id)}, model_derived=True,
            applicability={"scope": LABEL, "canonical": False, "material_reference": "PRE_T0_PASSIVE"})
        args = dict(history_id=history, branch_id=branch, time_key=year,
                    domain_ids=(DOMAIN,), state_ids=(str(record.state_id),),
                    provenance_refs=(str(provenance.record_id),),
                    validation_status=LABEL,
                    details={"forcing_id": str(forcing.forcing_id), "age_ma": state["age_ma"],
                             "event_count": 0, "experiment_elapsed_year": state["year"]})
        snapshot, checkpoint = HistoricalSnapshot.create(**args), SimulationCheckpoint.create(**args)
        store.append_transaction(([provenance, forcing] if index == 0 else []) +
                                 [record, snapshot, checkpoint])
        require(store.read_state(str(record.state_id)).to_dict() == record.to_dict(),
                "R6 state readback differs")
        parent = (str(record.state_id),)
        results[year] = {"state_id": parent[0], "snapshot_id": snapshot.record_id,
                         "checkpoint_id": checkpoint.record_id}
    return {"history_id": history, "branch_id": branch,
            "forcing_id": str(forcing.forcing_id), "states": results}


def resume(path, ids):
    store = HistoryStore(path)
    row = ids["states"][str(MIDPOINT)]
    record = store.read_state(row["state_id"])
    checkpoints = store.temporal_records(role=SimulationCheckpoint.ROLE)
    require(any(cp["record_id"] == row["checkpoint_id"] and cp["time_key"] == str(MIDPOINT)
                and cp["state_ids"] == [row["state_id"]] for cp in checkpoints)
            and record.parent_state_ids == (ids["states"]["0"]["state_id"],)
            and record.history_id == ids["history_id"] and record.branch_id == ids["branch_id"]
            and record.time_support == TimeSupport(str(MIDPOINT), CLOCK, "SNAPSHOT"),
            "checkpoint identity or causal order mismatch")
    current = thaw_json(record.value)
    require(current.pop("forcing_id") == ids["forcing_id"], "checkpoint forcing mismatch")
    law = store.read_forcing(ids["forcing_id"])
    require(law["history_id"] == record.history_id and law["branch_id"] == record.branch_id
            and law["spatial_support"] == record.spatial_support.to_dict()
            and law["value"]["label"] == LABEL, "forcing identity or support mismatch")
    return advance(current, law["value"], TARGET)


def run(output):
    started = perf_counter()
    case, pins, law = load_inputs()
    t0, frame_error = initial_state(case)
    t1 = advance(t0, law, TARGET)
    diagnostics = geometry_checks(t0, t1, law)
    output.mkdir()
    write(output / "INPUT_SHA256.json", pins)
    write(output / "FORCING.json", law)
    split = publish(output / "restart_history", t0, advance(t0, law, MIDPOINT), law, pins, "split")
    write(output / "RESTART_IDS.json", split)
    child_start = perf_counter()
    subprocess.run([sys.executable, __file__, str(output), "--resume"], check=True)
    child_wall = perf_counter() - child_start
    restarted = read(output / "RESUMED_T1.json")
    restarted_xyz = restarted.pop("canonical_xyz")
    require(restarted == {k: v for k, v in t1.items() if k != "canonical_xyz"},
            "non-geometric restart state differs")
    error = float(np.max(np.abs(np.asarray(restarted_xyz) - t1["canonical_xyz"])))
    require(error <= 2e-15, "restart differs beyond binary64 roundoff")
    primary = publish(output / "history", t0, t1, law, pins, "regional-10-year")
    store = HistoryStore(output / "history")
    restored = thaw_json(store.read_state(primary["states"]["0"]["state_id"]).value)
    require(restored.pop("forcing_id") == primary["forcing_id"]
            and advance(restored, store.read_forcing(primary["forcing_id"])["value"], TARGET) == t1,
            "same-schedule direct replay differs")
    write(output / "T1_GEOMETRY.json", {
        "frame": law["coordinate_frame"],
        "nodes": [{"parent_id": n["parent_id"], "lat_lon_t0_deg": n["canonical_lat_lon_t0_deg"],
                   "lat_lon_t1_deg": ll, "canonical_xyz_t1": xyz}
                  for n, ll, xyz in zip(t1["static"]["nodes"],
                                        coordinates._lat_lon(np.asarray(t1["canonical_xyz"])).tolist(),
                                        t1["canonical_xyz"], strict=True)],
    })
    require(all(digest(ROOT.parent / path) == expected for path, expected in pins.items()),
            "source changed during experiment")
    write(output / "RESULT.json", {
        "status": "PASS_PRESCRIBED_KINEMATIC_ONLY", "scope": LABEL,
        "physical_deforming_t1": "BLOCKED_EXACT_G2_G3_INPUTS", "event_count": 0,
        "target_year": TARGET, "target_age_ma": t1["age_ma"], "archive": primary,
        "diagnostics": diagnostics, "t0_frame_max_xyz_error": frame_error,
        "restart": {"separate_process": True, "midpoint_year": MIDPOINT,
                    "max_xyz_abs_difference": error, "all_other_payload_fields_equal": True,
                    "same_schedule_t0_replay_exact": True, "child_wall_s": child_wall},
        "internal_wall_s": perf_counter() - started,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--resume", action="store_true")
    options = parser.parse_args()
    if options.resume:
        write(options.output / "RESUMED_T1.json",
              resume(options.output / "restart_history", read(options.output / "RESTART_IDS.json")))
    else:
        run(options.output)
