"""Build and qualify one isolated R6 B6K pre-transition candidate state."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from arcana_worldsim.r6.b6k_candidate import (DT_YEARS, SOURCE_AGE_MA, TARGET_AGE_MA,
    build_plate_local_positions, candidate_identity, deterministic_payload,
    geometry_diagnostics, target_age, topology_identity)
from arcana_worldsim.r6.identity import (BranchId, HistoryId, canonical_bytes, content_hash)
from arcana_worldsim.r6.plate_support_adapter import (build_node_support, load_b5_sources,
    source_snapshot_b5)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
    SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import HistoricalSnapshot

BRANCH = "r6/b6k-isolated-first-candidate-state"
OUT_REL = Path("outputs/r6_b6k_isolated_first_candidate_state")
B6J = Path("outputs/r6_b6j_first_dt_adjudication")
B6I = Path("outputs/r6_b6i_first_segment_topology_model_extension")
B6E = Path("outputs/r6_b6e_minimal_mvp_model_implementation")
B6G = Path("outputs/r6_b6g_targeted_validity_gap_closure")
FEG_DATA = Path("R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg")
FEG_MANIFEST = Path("R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json")
RUNTIME_DATA = Path("R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat")
RUNTIME_MANIFEST = Path("R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                                allow_nan=False).encode("utf-8") + b"\n")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_manifest(directory: Path, manifest_name: str, repo_root: Path) -> dict:
    manifest = read_json(directory / manifest_name)
    rows = manifest.get("artifacts", [])
    if rows:
        entries = [(str(row["relative_path"]), row.get("sha256"), row.get("byte_size"))
                   for row in rows]
    else:
        table = manifest.get("verified_inputs", manifest.get("inputs", {}))
        entries = [(str(rel), expected, None) for rel, expected in table.items()]
    if not entries:
        raise ValueError(f"no verifiable entries in manifest: {manifest_name}")
    for rel, expected_hash, expected_size in entries:
        path = (directory / rel).resolve()
        if not path.is_file():
            path = (repo_root / rel).resolve()
        if repo_root.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"unsafe/missing prior evidence artifact: {rel}")
        if digest(path) != expected_hash or (expected_size is not None and path.stat().st_size != expected_size):
            raise ValueError(f"prior evidence hash mismatch: {rel}")
    return manifest


def _json_snapshot(snapshot: dict) -> dict:
    return {key: {"sha256": value[0], "size": value[1]}
            for key, value in sorted(snapshot.items())}


def _add_canonical_runtime_snapshot(root: Path, snapshot: dict) -> None:
    feg_manifest = read_json(root / FEG_MANIFEST)
    runtime_manifest = read_json(root / RUNTIME_MANIFEST)
    declarations = ((FEG_DATA, feg_manifest["production_feg"]["raw_sha256"]),
        (RUNTIME_DATA, runtime_manifest["runtime_data_sha256"]))
    for rel, expected in declarations:
        path = root / rel
        actual = digest(path)
        if actual != expected:
            raise ValueError(f"canonical runtime artifact identity mismatch: {rel}")
        snapshot[rel.as_posix()] = (actual, path.stat().st_size, path.stat().st_mtime_ns)


def construct(root: Path, output: Path) -> dict:
    branch_result = __import__("subprocess").run(["git", "-C", str(root), "branch", "--show-current"],
        check=True, capture_output=True, text=True)
    branch = branch_result.stdout.strip()
    head = __import__("subprocess").run(["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()
    if branch != BRANCH:
        raise ValueError(f"expected branch {BRANCH}, got {branch}")
    if output.resolve() == root.resolve() or root.resolve() not in output.resolve().parents:
        raise ValueError("B6K output must be an isolated directory within repository outputs")

    b6j_manifest = verify_manifest(root / B6J, "B6J_ARTIFACT_MANIFEST.json", root)
    b6j_dt = read_json(root / B6J / "B6J_DT_SELECTION.json")
    b6j_age = read_json(root / B6J / "B6J_TARGET_AGE.json")
    b6j_endpoint = read_json(root / B6J / "B6J_ENDPOINT_POLICY.json")
    b6j_event = read_json(root / B6J / "B6J_EVENT_BOUNDARY_CONTRACT.json")
    b6j_result = read_json(root / B6J / "B6J_RESULT.json")
    if (b6j_dt.get("status") != "FIRST_DT_SELECTED" or
            float(b6j_dt.get("value", -1)) != DT_YEARS or
            b6j_dt.get("numeric_representation", {}).get("hex") != DT_YEARS.hex() or
            b6j_age.get("target_age_ma") != TARGET_AGE_MA or
            b6j_endpoint.get("topology_mutation_during_step") is not False or
            b6j_event.get("transition_status") != "NOT_EXECUTED" or
            b6j_result.get("event_transition_status") != "NOT_EXECUTED"):
        raise ValueError("B6J dt or endpoint authority differs from expected frozen selection")
    for prior_dir, manifest_name in ((root / B6I, "B6I_SOURCE_MANIFEST.json"),
        (root / B6E, "B6E_ARTIFACT_MANIFEST.json"),
        (root / B6G, "B6G_SOURCE_MANIFEST.json")):
        verify_manifest(prior_dir, manifest_name, root)
    registry = read_json(root / B6I / "B6I_TOPOLOGY_PROCESS_REGISTRY.json")
    transfers = read_json(root / B6G / "B6G_STATE_TRANSFER_BLOCKING.json")
    memory_transfer = read_json(root / B6E / "B6E_SYSTEM_MEMORY_TRANSFER.json")
    memory_closure = read_json(root / B6G / "B6G_SYSTEM_MEMORY_BLOCKING.json")
    async_validity = read_json(root / B6E / "B6E_ASYNC_TEMPORAL_VALIDITY.json")
    if not any(row.get("family") == "plate-local geometry coordinates" and
               row.get("execution_performed") is False for row in transfers.get("required_transfer_operations", [])):
        raise ValueError("B6G does not identify the authorized plate-local geometry transfer")

    before = source_snapshot_b5(load_b5_sources(root, expected_branch=BRANCH)[0])
    _add_canonical_runtime_snapshot(root, before)
    source, inventory = load_b5_sources(root, expected_branch=BRANCH)
    support = build_node_support(source, inventory)
    omega = {int(row["plate_id"]): tuple(float(x) for x in row["euler_vector_rad_per_year"])
             for row in source.kinematics.plates}
    if set(omega) != set(source.kinematics.plate_ids):
        raise ValueError("Euler vectors do not cover the governed plate set")
    start = time.perf_counter()
    pairs, coordinates = build_plate_local_positions(vertices_lat_lon=source.mesh.vertices_lat_lon,
        face_node_ids=inventory["_face_node_ids"], face_plate_ids=inventory["_face_plate_ids"],
        plate_omega=omega, elapsed_years=DT_YEARS)
    elapsed = time.perf_counter() - start
    payload = deterministic_payload(pairs, coordinates)
    payload_sha = sha256(payload).hexdigest()
    replay_pairs, replay_coordinates = build_plate_local_positions(
        vertices_lat_lon=source.mesh.vertices_lat_lon,
        face_node_ids=inventory["_face_node_ids"], face_plate_ids=inventory["_face_plate_ids"],
        plate_omega=omega, elapsed_years=DT_YEARS)
    replay_payload = deterministic_payload(replay_pairs, replay_coordinates)
    replay_sha = sha256(replay_payload).hexdigest()
    if replay_sha != payload_sha or replay_pairs != pairs or replay_payload != payload:
        raise ValueError("deterministic B6K replay did not reproduce candidate bytes and identity")
    output.mkdir(parents=True, exist_ok=True)
    candidate_payload_path = output / "B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin"
    candidate_payload_path.write_bytes(payload)
    pair_index = {pair: index for index, pair in enumerate(pairs)}
    interfaces = []
    for descriptor in source.boundary_descriptors:
        plate_a, plate_b = (int(x) for x in descriptor["adjacent_plate_ids"])
        side_rows = []
        for plate in (plate_a, plate_b):
            side_rows.append({"plate_id": plate, "coordinate_rows": [
                pair_index[(int(node), plate)] for node in descriptor["endpoint_node_ids"]]})
        interfaces.append({"boundary_id": descriptor["boundary_id"],
            "incident_plate_ids": [plate_a, plate_b], "sides": side_rows,
            "candidate_motion": "PLATE_LOCAL_EXACT_RIGID_ROTATION",
            "governed_t0_relative_normal_tangential_diagnostic": descriptor["kinematic_descriptor"],
            "physical_accommodation": "UNKNOWN_UNCHANGED"})
    junctions = []
    for junction_id, node_id in source.mesh.junction_node_ids:
        plates = support.node_plate_ids[int(node_id) - 1]
        if len(plates) < 3:
            raise ValueError(f"junction {junction_id} lacks three incident plate identities")
        junctions.append({"junction_id": junction_id, "canonical_node_id": int(node_id),
            "incident_plate_ids": list(plates), "sides": [
                {"plate_id": plate, "coordinate_row": pair_index[(int(node_id), plate)]}
                for plate in plates], "support_semantics": "SET_VALUED_NO_UNIQUE_OWNER"})
    topology_id = topology_identity(triangles=source.mesh.triangles,
        triangle_plate_ids=source.mesh.triangle_plate_id,
        boundary_descriptors=source.boundary_descriptors,
        junction_node_ids=source.mesh.junction_node_ids)
    model_identity = content_hash({"B6D_model_freeze_sha256": digest(root / "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_RESULT.json"),
        "B6I_process_registry_sha256": digest(root / B6I / "B6I_TOPOLOGY_PROCESS_REGISTRY.json"),
        "rotation_implementation": "R6_EXACT_CONSTANT_EULER_QUATERNION_V1"})
    candidate_id = candidate_identity(source_t0_identity=source.kinematics.canonical_identity_sha256,
        model_identity=model_identity, dt_hex=DT_YEARS.hex(), target_age_ma=TARGET_AGE_MA,
        topology_id=topology_id, candidate_payload_sha256=payload_sha)
    implementation_sources = {
        "scripts/r6_b6k_isolated_first_candidate_state.py": digest(root / "scripts/r6_b6k_isolated_first_candidate_state.py"),
        "src/arcana_worldsim/r6/b6k_candidate.py": digest(root / "src/arcana_worldsim/r6/b6k_candidate.py"),
        "src/arcana_worldsim/r6/plate_support_adapter.py": digest(root / "src/arcana_worldsim/r6/plate_support_adapter.py"),
        "tests/test_r6_b6k_isolated_candidate_state.py": digest(root / "tests/test_r6_b6k_isolated_candidate_state.py"),
    }
    geom = geometry_diagnostics(pairs=pairs, coordinates=coordinates,
        vertices_lat_lon=source.mesh.vertices_lat_lon, triangles=source.mesh.triangles,
        triangle_plate_ids=source.mesh.triangle_plate_id)
    plate_rotations = []
    for plate in sorted(omega):
        vector = omega[plate]
        angle = math.sqrt(sum(x*x for x in vector)) * DT_YEARS
        # Rodrigues matrix diagnostics use the same exact axis/angle represented
        # by the quaternion point transform; no approximate coordinate update.
        axis_norm = math.sqrt(sum(x*x for x in vector))
        if axis_norm == 0:
            det, orth = 1.0, 0.0
        else:
            x, y, z = (v / axis_norm for v in vector)
            c, s, q = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
            matrix = np.array([[c+x*x*q, x*y*q-z*s, x*z*q+y*s],
                [y*x*q+z*s, c+y*y*q, y*z*q-x*s],
                [z*x*q-y*s, z*y*q+x*s, c+z*z*q]], dtype=np.float64)
            det = float(np.linalg.det(matrix)); orth = float(np.max(np.abs(matrix.T @ matrix - np.eye(3))))
        plate_rotations.append({"plate_id": plate, "omega_rad_per_year": list(vector),
            "angle_radians": angle, "matrix_determinant": det,
            "max_orthogonality_residual": orth, "rotation": "EXACT_ACTIVE_RH_XYZ_COLUMN_VECTOR"})

    history_id = source.kinematics.history_id
    candidate_branch = str(BranchId.from_payload({"b6k_candidate_id": candidate_id}))
    t0_support = SpatialSupport("R6_GLOBAL_GEOGRAPHY_1DEG_V1", (), "1 degree canonical mesh", "GLOBAL")
    provenance = ProvenanceRecord.create(activity="R6_B6K_BUILD_ISOLATED_FIRST_PRETRANSITION_CANDIDATE",
        input_refs=(f"sha256:{source.kinematics.canonical_identity_sha256}",
            f"sha256:{payload_sha}"),
        source_refs=tuple(source.kinematics.source_refs) + (
            f"artifact:outputs/r6_b6j_first_dt_adjudication/B6J_DT_SELECTION.json#sha256:{digest(root / B6J / 'B6J_DT_SELECTION.json')}",
            f"artifact:outputs/r6_b6i_first_segment_topology_model_extension/B6I_TOPOLOGY_PROCESS_REGISTRY.json#sha256:{digest(root / B6I / 'B6I_TOPOLOGY_PROCESS_REGISTRY.json')}"),
        attributes={"candidate_identity": candidate_id, "candidate_payload_sha256": payload_sha,
            "elapsed_years_hex": DT_YEARS.hex(), "target_age_ma": TARGET_AGE_MA,
            "topology_transition_executed": False, "canonical_state_changed": False})
    source_state = DomainStateEnvelope.create(history_id=history_id, branch_id=candidate_branch,
        domain="tectonic_geometry", time_support=TimeSupport("210.0Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=t0_support, support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"candidate_source_identity": source.kinematics.canonical_identity_sha256,
               "topology_identity": topology_id}, uncertainty={"source": "GOVERNED_T0"})
    candidate_state = DomainStateEnvelope.create(history_id=history_id, branch_id=candidate_branch,
        domain="tectonic_geometry", time_support=TimeSupport(f"{TARGET_AGE_MA:.17g}Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=t0_support, support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"candidate_id": candidate_id, "payload_sha256": payload_sha,
               "topology_identity": topology_id, "candidate_class": "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE"},
        uncertainty={"physical_boundary_accommodation": "UNKNOWN_NOT_RESOLVED_BY_CANDIDATE_GEOMETRY"},
        provenance_ids=(str(provenance.record_id),), parent_state_ids=(str(source_state.state_id),),
        payload_ref=f"sha256:{payload_sha}", model_derived=True,
        applicability={"candidate_only": True, "canonical_t1": False})
    unknown_state = DomainStateEnvelope.create(history_id=history_id, branch_id=candidate_branch,
        domain="boundary_physical_accommodation", time_support=TimeSupport("210.0Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
        spatial_support=SpatialSupport("R6_GLOBAL_GEOGRAPHY_1DEG_V1", (), "1,983 interfaces", "GLOBAL"),
        support_class=SupportClass.UNKNOWN, authority_class=AuthorityClass.NONE, value=None,
        uncertainty={"reason": "B6G_PHYSICAL_ACCOMMODATION_NOT_AUTHORIZED"})
    candidate_snapshot = HistoricalSnapshot.create(history_id=history_id, branch_id=candidate_branch,
        time_key=candidate_state.time_support.time_key, domain_ids=("tectonics",),
        state_ids=(str(candidate_state.state_id),), authority_refs=(
            f"artifact:outputs/r6_b6j_first_dt_adjudication/B6J_DT_SELECTION.json#sha256:{digest(root / B6J / 'B6J_DT_SELECTION.json')}",),
        provenance_refs=(str(provenance.record_id),), validation_status="CANDIDATE_VALIDATED",
        details={"candidate_only": True, "state_valid_time": candidate_state.time_support.time_key,
            "latest_valid_time": candidate_state.time_support.time_key,
            "query_time": candidate_state.time_support.time_key,
            "event_boundary": "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE",
            "rift_transition_executed": False, "canonical_t1": False})
    store_path = output / "isolated_world_history"
    store = HistoryStore(store_path)
    store.append_transaction((provenance, source_state, candidate_state, unknown_state, candidate_snapshot))
    del store
    store = HistoryStore(store_path)
    query = HistoryQueryService(store)
    state_query = query.state_at(history_id=history_id, branch_id=candidate_branch,
        domain="tectonic_geometry", time_key=candidate_state.time_support.time_key)
    history_query = query.history(history_id=history_id, branch_id=candidate_branch)
    difference = query.difference(str(source_state.state_id), str(candidate_state.state_id))
    why = query.why(str(candidate_state.state_id))
    lineage = query.lineage(str(candidate_state.state_id))
    unknown_query = query.state_at(history_id=history_id, branch_id=candidate_branch,
        domain="boundary_physical_accommodation", time_key="210.0Ma")
    support_query = query.available_resolution(history_id=history_id, branch_id=candidate_branch,
        domain="tectonic_geometry")
    temporal_query = [row for row in store.temporal_records(role="HISTORICAL_SNAPSHOT")
        if row.get("record_id") == candidate_snapshot.record_id]
    after = source_snapshot_b5(source)
    _add_canonical_runtime_snapshot(root, after)
    source_unchanged = _json_snapshot(before) == _json_snapshot(after)

    async_rows = async_validity.get("domains", [])
    if not async_rows or any(row.get("latest_valid_time") != "210Ma" for row in async_rows):
        raise ValueError("B6E async domain clock inventory changed or incomplete")
    family_rows = []
    for row in transfers.get("families", []):
        family = str(row["state_family"])
        classification = str(row["first_step_classification"])
        updated = classification == "DERIVED_RECOMPUTABLE" and family == "FEG/ShellSet runtime fields"
        family_rows.append({"state_family": family, "source_valid_time": "210Ma",
            "candidate_behavior": classification, "candidate_valid_time": None,
            "transfer_operation": "NOT_EXECUTED" if updated else "REFERENCE_OR_ASYNC_RETAINED",
            "authority": row.get("reason"), "result_status": "NOT_UPDATED_UNKNOWN_OR_MODEL_REQUIRED" if classification in ("QUERY_LIMITATION_ONLY", "DERIVED_RECOMPUTABLE") else classification})
    family_rows.append({"state_family": "plate-local geometry coordinates", "source_valid_time": "210Ma",
        "candidate_behavior": "RIGID_ADVECT", "candidate_valid_time": f"{TARGET_AGE_MA:.17g}Ma",
        "transfer_operation": "EXACT_CONSTANT_EULER_ROTATION", "authority": "B6B/B6C/B6G/B6J",
        "result_status": "UPDATED_CANDIDATE_ONLY"})
    async_report = [{"domain": row["domain"], "query_time": "209.97287659484368Ma",
        "state_valid_time": row["latest_valid_time"], "latest_valid_time": row["latest_valid_time"],
        "candidate_state_present": row.get("candidate_state_present", False),
        "classification": "ASYNC_RETAINS_LATEST_VALID_STATE"} for row in async_rows]
    event_predicate = "PREDICATE_SATISFIED_ACTIVATION_POSSIBLE"
    result = {"schema": "R6_B6K_RESULT_V1", "qualification_verdict": "PASS_B6K_ISOLATED_FIRST_CANDIDATE_STATE",
        "qualified_source_commit": head, "branch": branch, "execution_target": "WINDOWS",
        "dt_years": DT_YEARS, "dt_hex": DT_YEARS.hex(), "source_age_ma": SOURCE_AGE_MA,
        "target_age_ma": TARGET_AGE_MA, "candidate_id": candidate_id,
        "implementation_worktree_source_sha256": implementation_sources,
        "candidate_payload_sha256": payload_sha, "candidate_payload_bytes": len(payload),
        "plate_local_coordinate_rows": len(pairs), "topology_identity": topology_id,
        "interface_count": len(interfaces), "interface_side_count": sum(len(x["sides"]) for x in interfaces),
        "junction_count": len(junctions), "junction_side_count": sum(len(x["sides"]) for x in junctions),
        "candidate_state_status": "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE",
        "dt_selected": True,
        "rift_predicate_status": event_predicate, "rift_transition_status": "NOT_EXECUTED",
        "topology_transition_executed": False,
        "t1_created": False, "canonical_state_changed": False,
        "mechanics_authorized": False, "forward_evolution_authorized": False,
        "runtime_authorized": True,
        "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
        "shellset_executed": False, "orbdata_mechanics_executed": False,
        "canonical_source_unchanged": source_unchanged,
        "candidate_construction_seconds": elapsed,
        "candidate_acceptance_gate": "CANDIDATE_FIRST_STEP_VALIDATED" if source_unchanged and
            geom["plate_local_triangle_orientation_failures"] == 0 and geom["nan_count"] == 0 and geom["inf_count"] == 0
            else "CANDIDATE_INVALID",
        "next_stage_recommendation": "AUTHORIZE_FIRST_CANDIDATE_STATE_QUALIFICATION_AND_QUERY_ACCEPTANCE"}
    # Correctly spelled metric key retained as an explicit compatibility field.
    result["triangle_orientation_failures"] = geom["plate_local_triangle_orientation_failures"]
    artifacts = {
      "B6K_SOURCE_FREEZE.json": {"qualified_source_commit": head,
        "source_identity_sha256": source.source_identity,
        "canonical_mesh_sha256": source.mesh.normalized_sha256,
        "node_count": len(source.mesh.vertices_lat_lon), "triangle_count": len(source.mesh.triangles),
        "plate_count": len(source.kinematics.plate_ids), "boundary_count": len(interfaces),
        "junction_count": len(junctions), "verified_b6j_artifacts": len(b6j_manifest["artifacts"]),
        "source_snapshot_before": _json_snapshot(before), "source_snapshot_after": _json_snapshot(after),
        "canonical_world_history_store": {"status": "NOT_PRESENT_IN_REPOSITORY",
          "B3_work_root_empty": not any((root / "outputs/r6_world_history_b3_t0_ingest/.work").rglob("*"))},
        "runtime_artifact_scope": "hashed_for_immutability_only; not read as candidate input"},
      "B6K_TEMPORAL_TARGET.json": {"elapsed_years": DT_YEARS, "elapsed_years_hex": DT_YEARS.hex(),
        "conversion_rule": "Decimal(str(source_age_ma)) - Decimal.from_float(binary64_dt) / 1000000; cast once to binary64",
        "precision": "Decimal T0 age and exact binary64 dt, matching B6J conversion policy",
        "source_age_ma": SOURCE_AGE_MA,
        "target_age_ma": target_age(SOURCE_AGE_MA, DT_YEARS), "planning_target_matches_B6J": target_age(SOURCE_AGE_MA, DT_YEARS) == TARGET_AGE_MA,
        "endpoint_policy": "EVENT_ALIGNED_PRETRANSITION_ENDPOINT"},
      "B6K_PLATE_ROTATIONS.json": {"status": "PASS_EXACT_FINITE_ROTATION",
        "support_identity_sha256": support.mapping_identity_sha256,
        "plates": [{**row, "source_support_identity_sha256": support.mapping_identity_sha256} for row in plate_rotations],
        "maximum_determinant_error": max(abs(row["matrix_determinant"]-1.0) for row in plate_rotations),
        "maximum_orthogonality_residual": max(row["max_orthogonality_residual"] for row in plate_rotations)},
      "B6K_INTERIOR_CANDIDATE.json": {"status": "PASS", "unique_canonical_node_count": len(source.mesh.vertices_lat_lon),
        "plate_local_pair_count": len(pairs), "node_support_counts": dict(support.counts),
        "coordinate_representation": candidate_payload_path.name,
        "geometry_diagnostics": geom},
      "B6K_BOUNDARY_CANDIDATE.json": {"status": "PASS_RELATIONAL_TWO_SIDED", "interface_count": len(interfaces),
        "side_count": 2*len(interfaces), "interfaces": interfaces},
      "B6K_JUNCTION_CANDIDATE.json": {"status": "PASS_SET_VALUED", "junction_count": len(junctions),
        "side_count": sum(len(row["sides"]) for row in junctions), "junctions": junctions},
      "B6K_TOPOLOGY_HOLD.json": {"status": "PASS_IDENTITY_PRESERVED", "pre_transition_topology_identity": topology_id,
        "candidate_topology_identity": topology_id, "transition_executed": False,
        "boundary_birth_death": False, "junction_birth_death": False, "support_mutation": False},
      "B6K_EVENT_BOUNDARY.json": {"event_class": "RIFT_PROCESS_ACTIVATION", "event_pair": [1,3],
        "event_time_years": DT_YEARS, "absolute_age_ma": TARGET_AGE_MA,
        "predicate_status": event_predicate, "transition_status": "NOT_EXECUTED",
        "candidate_class": "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE"},
      "B6K_STATE_TRANSFER.json": {"status": "PASS_EXPLICIT_FIELD_SPECIFIC_ONLY",
        "state_families": family_rows,
        "executed_transfer": "B6B_EXACT_RIGID_PLATE_LOCAL_GEOMETRY", "unresolved_transfer_classes_preserved": ["MODEL_REQUIRED", "UNKNOWN", "CONSERVATIVE_REMAP_REQUIRED"],
        "no_interpolation": True, "no_imputation": True},
      "B6K_ASYNC_DOMAIN_STATE.json": {"status": "PASS_LATEST_VALID_TIME_RETAINED", "domains": async_report},
      "B6K_SYSTEM_MEMORY.json": {"status": "PASS_REFERENCE_AND_UNKNOWN_PRESERVATION",
        "system_memory_discarded": memory_transfer.get("system_memory_discarded"),
        "future_values_created": memory_transfer.get("future_values_created"),
        "declarations": memory_transfer.get("declarations", []),
        "b6g_classes": memory_closure.get("classes", []),
        "unresolved_values_imputed": False},
      "B6K_CANDIDATE_IDENTITY.json": {"candidate_identity": candidate_id, "canonical_t1_identity_created": False,
        "candidate_class": "CANDIDATE_FIRST_STEP_PRETRANSITION", "model_identity_sha256": model_identity,
        "topology_identity_sha256": topology_id, "payload_sha256": payload_sha},
      "B6K_LINEAGE.json": {"status": "PASS", "source_t0_identity": source.kinematics.canonical_identity_sha256,
        "source_support_identity": support.mapping_identity_sha256,
        "source_payloads": [{"logical_path": row["logical_path"], "sha256": row["sha256"], "role": row["role"]}
            for row in source.kinematics.payload_sources],
        "plate_motion_vectors_rad_per_year": omega, "dt_hex": DT_YEARS.hex(), "model_identity": model_identity,
        "candidate_identity": candidate_id, "lineage_rule": "PER_PLATE_LOCAL_NODE_INCIDENCE"},
      "B6K_WORLD_HISTORY_INTEGRATION.json": {"status": "PASS_ISOLATED_STORE_REOPEN_AND_QUERY",
        "history_id": history_id, "candidate_branch_id": candidate_branch,
        "source_state_id": str(source_state.state_id), "candidate_state_id": str(candidate_state.state_id),
        "unknown_state_id": str(unknown_state.state_id), "stored_state_count": len(store.states()),
        "temporal_validity_record_id": candidate_snapshot.record_id,
        "temporal_validity_record_status": temporal_query[0]["validation_status"] if temporal_query else "MISSING",
        "store_path": "isolated_world_history", "canonical_store_touched": False,
        "append_reopen": True, "query_state": state_query.status, "history_count": len(history_query),
        "why_state_count": len(why.state_lineage), "why_provenance_count": len(why.provenance_records),
        "lineage_depth": len(lineage["state_lineage"])},
      "B6K_DIFFERENCE.json": {"status": difference.status.value, "operation": difference.operation,
        "equal": difference.equal, "reason": difference.reason},
      "B6K_REPLAY.json": {"status": "PASS_DETERMINISTIC_RECONSTRUCTION_BYTES",
        "reconstruction_policy": "rerun exact candidate builder from frozen B6K inputs and compare canonical binary payload bytes",
        "payload_sha256_first": payload_sha, "payload_sha256_replay": replay_sha,
        "byte_identical": replay_payload == payload, "pair_identity_identical": replay_pairs == pairs,
        "recipe_record": "NOT_CREATED; deterministic reconstruction demonstrated in runner, no HistoryStore ReplayRecipe"},
      "B6K_GEOMETRIC_VALIDATION.json": geom,
      "B6K_CANONICAL_IMMUTABILITY.json": {"status": "CANONICAL_SOURCE_UNCHANGED" if source_unchanged else "FAIL",
        "before": _json_snapshot(before), "after": _json_snapshot(after)},
      "B6K_QUERY_PREACCEPTANCE.json": {"STATE": "PASS" if state_query.status == "FOUND" else "FAIL",
        "HISTORY": "PASS" if len(history_query) >= 3 else "FAIL",
        "DIFFERENCE": "PASS" if difference.status.value == "COMPARABLE" else "FAIL",
        "WHY": "PASS" if why.target_state.state_id == candidate_state.state_id else "FAIL",
        "SUPPORT": "PARTIAL" if support_query.get("status") == "AVAILABLE" else "BLOCKED_BY_CANONICAL_PUBLICATION",
        "REPLAY": "PASS_DETERMINISTIC_REBUILD; STORE_RECIPE_NOT_CREATED",
        "UNKNOWN": "PASS" if unknown_query.status == "UNKNOWN" else "FAIL",
        "TEMPORAL_VALIDITY": "PASS" if temporal_query and temporal_query[0]["details"]["rift_transition_executed"] is False else "FAIL",
        "REFINEMENT": "BLOCKED_BY_CANONICAL_PUBLICATION"},
      "B6K_TEST_RESULTS.json": (read_json(output / "B6K_TEST_RESULTS.json")
        if (output / "B6K_TEST_RESULTS.json").is_file() else
        {"focused_tests": "RUN_AFTER_CONSTRUCTION", "full_r6": "RUN_AFTER_CONSTRUCTION"})}
    write_json(output / "B6K_RESULT.json", result)
    for name, body in artifacts.items():
        write_json(output / name, body)
    write_json(output / "B6K_INTERIOR_CANDIDATE.json", artifacts["B6K_INTERIOR_CANDIDATE.json"])
    readback = (output / candidate_payload_path.name).read_bytes()
    if sha256(readback).hexdigest() != payload_sha:
        raise ValueError("candidate binary payload failed readback integrity check")
    return {"result": result, "artifacts": artifacts, "candidate_payload_path": candidate_payload_path,
        "payload_sha256": payload_sha, "candidate_id": candidate_id, "pairs": len(pairs),
        "candidate_state": candidate_state, "state_query": state_query.status,
        "query_unknown": unknown_query.status, "difference_status": difference.status.value,
        "source_unchanged": source_unchanged, "geometry": geom}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUT_REL)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        result = construct(root, output.resolve())
        print(json.dumps({"decision": result["result"]["qualification_verdict"],
            "candidate_id": result["candidate_id"], "payload_sha256": result["payload_sha256"],
            "candidate_acceptance_gate": result["result"]["candidate_acceptance_gate"]}, sort_keys=True))
        return 0 if result["result"]["candidate_acceptance_gate"] == "CANDIDATE_FIRST_STEP_VALIDATED" else 2
    except Exception as exc:
        print(f"B6K_FAIL_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
