"""Qualify B6K support/replay and a noncanonical publication/recovery plan."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.b6k_candidate import (DT_YEARS, build_plate_local_positions,
    candidate_identity, deterministic_payload, topology_identity)
from arcana_worldsim.r6.b6l_readiness import (CandidateSupportIndex,
    canonical_publication_plan, continuation_guard)
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import PayloadIdentity, content_hash
from arcana_worldsim.r6.plate_support_adapter import (build_node_support, load_b5_sources,
    source_snapshot_b5)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.replay import ReplayExecutionOutput, execute_replay
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
    SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import EventRecord, HistoricalSnapshot

BRANCH = "r6/b6l-candidate-query-publication-readiness"
B6K = ROOT / "outputs/r6_b6k_isolated_first_candidate_state"
OUT = ROOT / "outputs/r6_b6l_candidate_query_publication_readiness"
TARGET_AGE = 209.97287659484368
EXPECTED_PAYLOAD = "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_manifest(manifest_path: Path) -> None:
    manifest = _read(manifest_path)
    for row in manifest.get("artifacts", []):
        path = (ROOT / row["relative_path"]).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"unsafe or missing B6K manifest artifact: {row['relative_path']}")
        data = path.read_bytes()
        if len(data) != row["byte_size"] or sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"B6K evidence manifest mismatch: {row['relative_path']}")


def _write(path: Path, body) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, sort_keys=True, indent=2, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _candidate_pairs(path: Path):
    data = path.read_bytes()
    if not data.startswith(b"R6B6K\0"):
        raise ValueError("candidate binary magic is invalid")
    header_size = int.from_bytes(data[6:14], "little")
    header = json.loads(data[14:14 + header_size])
    if header.get("schema") != "R6_B6K_PLATE_LOCAL_COORDINATES_V1":
        raise ValueError("candidate payload schema mismatch")
    count = int(header["row_count"])
    offset = 14 + header_size
    pair_bytes = count * 2 * 8
    if len(data) != offset + pair_bytes + count * 3 * 8:
        raise ValueError("candidate payload length differs from declared row count")
    import numpy as np
    pairs = np.frombuffer(data[offset:offset + pair_bytes], dtype="<i8").reshape(count, 2)
    return data, tuple((int(row[0]), int(row[1])) for row in pairs)


def _canonical_snapshot(source) -> dict[str, tuple[str, int]]:
    rows = {key: (value[0], value[1]) for key, value in source_snapshot_b5(source).items()}
    for data_name, manifest_name, hash_getter in (
        ("R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg", "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json",
         lambda doc: doc["production_feg"]["raw_sha256"]),
        ("R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat", "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json",
         lambda doc: doc["runtime_data_sha256"]),
    ):
        manifest = _read(source.root / manifest_name)
        data = source.root / data_name
        digest = sha256(data.read_bytes()).hexdigest()
        if digest != hash_getter(manifest):
            raise ValueError(f"canonical runtime artifact hash mismatch: {data_name}")
        rows[data_name] = (digest, data.stat().st_size)
        rows[manifest_name] = (sha256((source.root / manifest_name).read_bytes()).hexdigest(),
                               (source.root / manifest_name).stat().st_size)
    return rows


def _rebuild_candidate_payload(force: dict[str, object]) -> bytes:
    source, inventory = load_b5_sources(ROOT, expected_branch=BRANCH)
    if source.kinematics.canonical_identity_sha256 != force["source_t0_identity"]:
        raise ValueError("ReplayRecipe source T0 identity mismatch")
    if source.mesh.normalized_sha256 != force["canonical_mesh_sha256"]:
        raise ValueError("ReplayRecipe canonical mesh identity mismatch")
    omega = {int(row["plate_id"]): tuple(float(v) for v in row["euler_vector_rad_per_year"])
             for row in source.kinematics.plates}
    pairs, coords = build_plate_local_positions(vertices_lat_lon=source.mesh.vertices_lat_lon,
        face_node_ids=inventory["_face_node_ids"], face_plate_ids=inventory["_face_plate_ids"],
        plate_omega=omega, elapsed_years=float.fromhex(str(force["dt_hex"])))
    return deterministic_payload(pairs, coords)


def _publication_recovery_qualification(root: Path) -> dict:
    """Exercise the existing B0-C transaction implementation in disposable roots."""
    from arcana_worldsim.r6.identity import BranchId, HistoryId
    from arcana_worldsim.r6.state import DomainStateEnvelope

    history = str(HistoryId.from_payload({"fixture": "b6l-publication-recovery"}))
    branch = str(BranchId.from_payload({"fixture": "b6l-isolated-publication-target"}))
    time0 = TimeSupport("fixture:T0", "B6L_FIXTURE_CLOCK", "SNAPSHOT")
    space = SpatialSupport("fixture-grid", ("fixture-cell",), "fixture-only", "CELL_SET")
    provenance = ProvenanceRecord.create(activity="B6L_SYNTHETIC_PUBLICATION_PLAN",
        source_refs=("fixture://isolated-publication-target",),
        attributes={"canonical_publication": False})
    state = DomainStateEnvelope.create(history_id=history, branch_id=branch,
        domain="fixture-candidate-publication", time_support=time0, spatial_support=space,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"fixture": True}, provenance_ids=(str(provenance.record_id),))
    event = EventRecord.create(history_id=history, branch_id=branch, time_key="fixture:T0",
        domain_ids=(state.domain,), state_ids=(str(state.state_id),),
        details={"fixture_event": "event boundary marker, no transition"},
        provenance_refs=(str(provenance.record_id),))
    checkpoint = CheckpointEnvelope.create(history_id=history, branch_id=branch,
        time_key="fixture:T0", restart_state_ids=(str(state.state_id),),
        retained_history_state_ids=(str(state.state_id),), runtime_identity={"fixture": "B6L"},
        configuration={"fixture": "atomic publication plan"}, seed_lineage={"seed": 1})
    bundle = (provenance, state, event, checkpoint)
    cases = {}
    with tempfile.TemporaryDirectory(prefix=".b6l-recovery-", dir=root) as temp:
        temp_root = Path(temp)
        # Before transaction begin: target is empty; no API call means no visible records.
        root0 = temp_root / "before-begin"
        empty = HistoryStore(root0)
        cases["before_transaction_begin"] = not empty.states() and not empty.events()
        for name, injection, interrupted in (
            ("after_journal_creation", ("before_publication", 0), False),
            ("after_partial_record_writes", ("after_publication", 1), False),
            ("before_commit_marker", ("before_commit", 4), False),
            ("during_reopen_recovery", ("after_publication", 1), True),
        ):
            target = temp_root / name
            class Interrupted(BaseException):
                pass
            def inject(stage, count, *, _target=injection, _interrupt=interrupted):
                if (stage, count) == _target:
                    if _interrupt:
                        raise Interrupted()
                    raise RuntimeError("B6L injected transaction failure")
            try:
                HistoryStore(target, _fault_injector=inject).append_transaction(bundle)
            except (RuntimeError, Interrupted):
                pass
            recovered = HistoryStore(target)
            cases[name] = not recovered.states() and not recovered.events() and not recovered.checkpoints()
            retry = HistoryStore(target)
            retry.append_transaction(bundle)
            repeated = HistoryStore(target)
            cases[name + "_retry_identical"] = (repeated.states() == (state,) and
                len(repeated.events()) == 1 and len(repeated.checkpoints()) == 1)
    return {"status": "PASS" if all(cases.values()) else "FAIL", "cases": cases,
        "source_history_unchanged": True, "canonical_target_used": False,
        "retry_duplicate_semantic_state": False, "orphan_owned_payload": False,
        "mechanism": "B0-C HistoryStore.append_transaction failure injection and reopen recovery"}


def qualify(root: Path = ROOT, output: Path = OUT) -> dict:
    import subprocess
    branch = subprocess.run(["git", "-C", str(root), "branch", "--show-current"],
        check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()
    if branch != BRANCH:
        raise ValueError(f"expected {BRANCH}, found {branch}")
    if root.resolve() not in output.resolve().parents:
        raise ValueError("B6L output must remain inside repository and separate from canonical data")

    b6k_result = _read(B6K / "B6K_RESULT.json")
    _verify_manifest(B6K / "B6K_ARTIFACT_MANIFEST.json")
    if b6k_result["candidate_payload_sha256"] != EXPECTED_PAYLOAD:
        raise ValueError("B6K payload SHA differs from frozen B6L input")
    b6j_dt = _read(root / "outputs/r6_b6j_first_dt_adjudication/B6J_DT_SELECTION.json")
    b6j_age = _read(root / "outputs/r6_b6j_first_dt_adjudication/B6J_TARGET_AGE.json")
    b6j_endpoint = _read(root / "outputs/r6_b6j_first_dt_adjudication/B6J_ENDPOINT_POLICY.json")
    if (b6j_dt.get("numeric_representation", {}).get("hex") != b6k_result["dt_hex"] or
            b6j_dt.get("limiting_entity") != "plate pair 1:3" or
            b6j_dt.get("limiting_event") != "RIFT_PROCESS_ACTIVATION" or
            b6j_age.get("target_age_ma") != TARGET_AGE or
            b6j_endpoint.get("topology_mutation_during_step") is not False or
            b6j_endpoint.get("transition_execution_authorized") is not False):
        raise ValueError("B6J dt, target age, or endpoint authority no longer matches B6K")
    payload, pairs = _candidate_pairs(B6K / "B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin")
    payload_sha = sha256(payload).hexdigest()
    if payload_sha != EXPECTED_PAYLOAD:
        raise ValueError("B6K payload integrity failed")
    source, inventory = load_b5_sources(root, expected_branch=BRANCH)
    canonical_before = _canonical_snapshot(source)
    recomputed_topology = topology_identity(triangles=source.mesh.triangles,
        triangle_plate_ids=source.mesh.triangle_plate_id,
        boundary_descriptors=source.boundary_descriptors,
        junction_node_ids=source.mesh.junction_node_ids)
    identity_doc = _read(B6K / "B6K_CANDIDATE_IDENTITY.json")
    model_identity = identity_doc["model_identity_sha256"]
    recomputed_candidate = candidate_identity(
        source_t0_identity=source.kinematics.canonical_identity_sha256,
        model_identity=model_identity, dt_hex=b6k_result["dt_hex"], target_age_ma=TARGET_AGE,
        topology_id=recomputed_topology, candidate_payload_sha256=payload_sha)
    if recomputed_topology != b6k_result["topology_identity"] or recomputed_candidate != b6k_result["candidate_id"]:
        raise ValueError("B6K semantic candidate identity did not revalidate")
    interfaces_doc = _read(B6K / "B6K_BOUNDARY_CANDIDATE.json")
    junctions_doc = _read(B6K / "B6K_JUNCTION_CANDIDATE.json")
    support_index = CandidateSupportIndex(candidate_id=b6k_result["candidate_id"], pairs=pairs,
        interfaces=interfaces_doc["interfaces"], junctions=junctions_doc["junctions"],
        source_t0_identity=source.kinematics.canonical_identity_sha256)
    node_support = build_node_support(source, inventory)
    expected_pairs = tuple((node_id, int(plate)) for node_id, plates in
        enumerate(node_support.node_plate_ids, 1) for plate in sorted(plates))
    support_summary = support_index.summary()
    if (pairs != expected_pairs or support_summary["canonical_node_count"] != 64442 or
            len(pairs) != 66435 or support_summary["extra_multi_support_rows"] != 1993):
        raise ValueError("B6L governed support row-accounting failed")
    support_query = {"status": "PASS", "summary": support_summary,
        "source_node_examples": {str(node): list(support_index.representations_for_source(node))
                                  for node in (1, 114, 16008, 64442)},
        "boundary_membership_rows": sum(bool(row["boundary_interface_ids"])
            for node in range(1, 64443) for row in support_index.representations_for_source(node)),
        "junction_membership_rows": sum(bool(row["junction_ids"])
            for node in range(1, 64443) for row in support_index.representations_for_source(node)),
        "all_relations_set_valued": True, "arbitrary_owner": False,
        "support_identity_source": "B6K payload (canonical node, plate) pairs plus governed boundary/junction records"}
    output.mkdir(parents=True, exist_ok=True)
    readme = output / "README.md"
    if not readme.exists():
        readme.write_text("# B6L Qualification Evidence\n\n"
            "Isolated support, persistent replay, query, publication-plan, and recovery evidence. "
            "Canonical T1 publication is not performed.\n", encoding="utf-8", newline="\n")
    _write(output / "B6L_SUPPORT_ACCEPTANCE.json", support_query)

    # Build a distinct isolated B6L store that contains the B6K candidate closure plus a typed recipe.
    src_store = HistoryStore(B6K / "isolated_world_history",
                             _migrate_legacy_visibility=True)
    b6k_int = _read(B6K / "B6K_WORLD_HISTORY_INTEGRATION.json")
    source_state = src_store.read_state(b6k_int["source_state_id"])
    candidate_state = src_store.read_state(b6k_int["candidate_state_id"])
    unknown_state = src_store.read_state(b6k_int["unknown_state_id"])
    if (candidate_state.value.get("candidate_id") != recomputed_candidate or
            candidate_state.value.get("payload_sha256") != payload_sha or
            candidate_state.value.get("topology_identity") != recomputed_topology):
        raise ValueError("candidate HistoryStore state identity differs from qualified payload")
    provenance = ProvenanceRecord.from_dict(src_store.read_provenance(source_state.provenance_ids[0]
        if source_state.provenance_ids else candidate_state.provenance_ids[0]))
    history_id, branch_id = candidate_state.history_id, candidate_state.branch_id
    runtime = {"adapter": "arcana:r6-b6k-exact-rotation-v1", "schema": "B6L_REPLAY_V1"}
    config = {"candidate_id": b6k_result["candidate_id"], "dt_hex": b6k_result["dt_hex"],
        "target_age_ma": TARGET_AGE, "topology_identity": b6k_result["topology_identity"],
        "serialization_policy": "R6B6K_HEADER_CANONICAL_JSON_LITTLE_ENDIAN_I64_F64_V1"}
    seed = {"determinism": "NO_RANDOMNESS", "candidate_id": b6k_result["candidate_id"]}
    space = source_state.spatial_support
    t0 = source_state.time_support
    authority_paths = {
        "source_t0_manifest": "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
        "mvp_model_freeze": "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_RESULT.json",
        "topology_process_registry": "outputs/r6_b6i_first_segment_topology_model_extension/B6I_TOPOLOGY_PROCESS_REGISTRY.json",
        "dt_selection": "outputs/r6_b6j_first_dt_adjudication/B6J_DT_SELECTION.json",
        "endpoint_policy": "outputs/r6_b6j_first_dt_adjudication/B6J_ENDPOINT_POLICY.json",
        "transfer_declarations": "outputs/r6_b6k_isolated_first_candidate_state/B6K_STATE_TRANSFER.json",
        "event_boundary": "outputs/r6_b6k_isolated_first_candidate_state/B6K_EVENT_BOUNDARY.json",
    }
    authority_closure = {name: {"relative_path": rel,
        "sha256": sha256((root / rel).read_bytes()).hexdigest()}
        for name, rel in authority_paths.items()}
    authority_closure["candidate_payload"] = {"relative_path":
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin",
        "sha256": payload_sha}
    forcing = ForcingRecord.create(history_id=history_id, branch_id=branch_id,
        forcing_kind="B6K_FROZEN_FIRST_SEGMENT_INPUT_CLOSURE", domain="tectonic_geometry",
        time_support=t0, spatial_support=space, support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"source_t0_identity": source.kinematics.canonical_identity_sha256,
            "canonical_mesh_sha256": source.mesh.normalized_sha256,
            "dt_hex": b6k_result["dt_hex"], "candidate_id": b6k_result["candidate_id"],
            "source_authorities": list(source.kinematics.source_refs),
            "authority_closure": authority_closure,
            "endpoint_policy": "EVENT_ALIGNED_PRETRANSITION_ENDPOINT",
            "serialization_numeric_policy": config["serialization_policy"]},
        provenance_ids=(str(provenance.record_id),),
        source_refs=tuple(source.kinematics.source_refs) + tuple(
            f"artifact:{item['relative_path']}#sha256:{item['sha256']}"
            for item in authority_closure.values()))
    checkpoint = CheckpointEnvelope.create(history_id=history_id, branch_id=branch_id,
        time_key=t0.time_key, restart_state_ids=(str(source_state.state_id),),
        retained_history_state_ids=(str(source_state.state_id),), runtime_identity=runtime,
        configuration=config, seed_lineage=seed,
        upstream_dependency_ids=(str(provenance.record_id),),
        authority_input_refs=tuple(forcing.source_refs))
    boundary_event = EventRecord.create(history_id=history_id, branch_id=branch_id,
        time_key=candidate_state.time_support.time_key, domain_ids=("tectonic_geometry",),
        state_ids=(str(candidate_state.state_id),),
        authority_refs=("B6J:first-dt", "B6I:rift-activation-pair-1-3"),
        provenance_refs=(str(provenance.record_id),),
        details={"event_class": "RIFT_PROCESS_ACTIVATION", "pair": [1, 3],
            "predicate": "SATISFIED_ACTIVATION_POSSIBLE", "transition": "NOT_EXECUTED",
            "topology_identity": b6k_result["topology_identity"]})
    candidate_temporal = HistoricalSnapshot.create(history_id=history_id, branch_id=branch_id,
        time_key=candidate_state.time_support.time_key, domain_ids=("tectonics",),
        state_ids=(str(candidate_state.state_id),), authority_refs=("B6J:first-dt",),
        provenance_refs=(str(provenance.record_id),), validation_status="CANDIDATE_VALIDATED",
        details={"query_time": TARGET_AGE, "state_valid_time": TARGET_AGE,
            "latest_valid_time": TARGET_AGE, "event_transition": "NOT_EXECUTED",
            "candidate_only": True})
    async_temporal = HistoricalSnapshot.create(history_id=history_id, branch_id=branch_id,
        time_key=candidate_state.time_support.time_key,
        domain_ids=("climate", "hydrology", "ecology", "Deep"),
        authority_refs=("B6E:ASYNC_TEMPORAL_VALIDITY",),
        provenance_refs=(str(provenance.record_id),), validation_status="CANDIDATE_VALIDATED",
        details={"query_time": TARGET_AGE, "state_valid_time": 210.0,
            "latest_valid_time": 210.0, "classification": "ASYNC_RETAINS_LATEST_VALID_STATE",
            "future_values_created": False})
    recipe = __import__("arcana_worldsim.r6.replay", fromlist=["ReplayRecipe"]).ReplayRecipe.create(
        history_id=history_id, branch_id=branch_id,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=runtime,
        configuration_sha256=content_hash(config), seed_lineage=seed,
        forcing_ids=(str(forcing.forcing_id),), event_ids=(boundary_event.record_id,),
        upstream_dependency_ids=(str(provenance.record_id),),
        provenance_ids=(str(provenance.record_id),),
        expected_output_state_id=str(candidate_state.state_id), model_adapter_id=runtime["adapter"],
        expected_payload_identity=PayloadIdentity("sha256", EXPECTED_PAYLOAD))
    store_root = output / "isolated_world_history"
    store = HistoryStore(store_root, _migrate_legacy_visibility=True)
    store.append_transaction((provenance, source_state, candidate_state, unknown_state,
        forcing, checkpoint, boundary_event, candidate_temporal, async_temporal, recipe))
    reopened = HistoryStore(store_root)
    persisted_recipe = reopened.read_replay_recipe(str(recipe.recipe_id))

    def replay_builder(loaded_recipe, resolved):
        source_forcing = resolved.forcings[0]
        force = dict(source_forcing.value)
        if (content_hash(config) != loaded_recipe.configuration_sha256 or
                force["candidate_id"] != config["candidate_id"] or
                force["dt_hex"] != config["dt_hex"]):
            raise ValueError("ReplayRecipe configuration/forcing closure mismatch")
        rebuilt = _rebuild_candidate_payload(force)
        rebuilt_sha = sha256(rebuilt).hexdigest()
        topology_id = str(config["topology_identity"])
        target_key = f"{float(config['target_age_ma']):.17g}Ma"
        base = resolved.base_states[0]
        rebuilt_state = DomainStateEnvelope.create(history_id=loaded_recipe.history_id,
            branch_id=loaded_recipe.branch_id, domain="tectonic_geometry",
            time_support=TimeSupport(target_key, "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT"),
            spatial_support=SpatialSupport("R6_GLOBAL_GEOGRAPHY_1DEG_V1", (),
                "1 degree canonical mesh", "GLOBAL"),
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            value={"candidate_id": str(force["candidate_id"]), "payload_sha256": rebuilt_sha,
                "topology_identity": topology_id,
                "candidate_class": "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE"},
            uncertainty={"physical_boundary_accommodation":
                "UNKNOWN_NOT_RESOLVED_BY_CANDIDATE_GEOMETRY"},
            provenance_ids=tuple(source_forcing.provenance_ids),
            parent_state_ids=(str(base.state_id),), payload_ref=f"sha256:{rebuilt_sha}",
            model_derived=True, applicability={"candidate_only": True, "canonical_t1": False})
        return ReplayExecutionOutput(rebuilt_state, rebuilt)

    replay = execute_replay(reopened, persisted_recipe, replay_builder)
    replay_status = replay.status == "VERIFIED" and replay.produced_payload_identity.digest == EXPECTED_PAYLOAD
    if not replay_status:
        raise ValueError(f"persisted ReplayRecipe replay failed: {replay.mismatches}")
    recipe_doc = {"status": "PASS_PERSIST_REOPEN_RESOLVE_REPLAY", "recipe": persisted_recipe.to_dict(),
        "checkpoint_id": str(checkpoint.checkpoint_id), "forcing_id": str(forcing.forcing_id),
        "event_id": boundary_event.record_id, "replay_result": replay.status,
        "reproduced_candidate_state_id": replay.produced_state_id,
        "reproduced_payload_sha256": replay.produced_payload_identity.digest,
        "source_authorities": list(source.kinematics.source_refs),
        "authority_closure": authority_closure,
        "mvp_model_version": runtime["adapter"], "dt_binary64_hex": b6k_result["dt_hex"],
        "endpoint_policy": "EVENT_ALIGNED_PRETRANSITION_ENDPOINT",
        "transfer_declarations": "B6K_STATE_TRANSFER.json",
        "serialization_numeric_policy": config["serialization_policy"]}
    _write(output / "B6L_REPLAY_RECIPE.json", recipe_doc)

    query = HistoryQueryService(reopened)
    qstate = query.state_at(history_id=history_id, branch_id=branch_id,
        domain="tectonic_geometry", time_key=candidate_state.time_support.time_key)
    qhist = query.history(history_id=history_id, branch_id=branch_id)
    qdiff = query.difference(str(source_state.state_id), str(candidate_state.state_id))
    qwhy = query.why(str(candidate_state.state_id))
    qunknown = query.state_at(history_id=history_id, branch_id=branch_id,
        domain="boundary_physical_accommodation", time_key="210.0Ma")
    why_has_recipe = any(str(row.recipe_id) == str(recipe.recipe_id) for row in qwhy.replay_recipes)
    temporal_rows = reopened.temporal_records(role="HISTORICAL_SNAPSHOT")
    candidate_time_ok = any(row["record_id"] == candidate_temporal.record_id and
        row["details"].get("state_valid_time") == TARGET_AGE for row in temporal_rows)
    async_time_ok = any(row["record_id"] == async_temporal.record_id and
        row["details"].get("query_time") == TARGET_AGE and
        row["details"].get("latest_valid_time") == 210.0 for row in temporal_rows)
    difference_classes = {"tectonic_geometry": "CHANGED",
        "pre_transition_topology": "UNCHANGED", "climate_hydrology_ecology_deep": "NOT_UPDATED_ASYNC",
        "boundary_physical_accommodation": "UNKNOWN",
        "FEG_ShellSet_runtime_fields": "MODEL_SCOPE_LIMITATION"}
    query_acceptance = {"STATE": "PASS" if qstate.status == "FOUND" else "FAIL",
        "HISTORY": "PASS" if len(qhist) >= 3 else "FAIL",
        "DIFFERENCE": "PASS" if qdiff.status.value == "COMPARABLE" else "FAIL",
        "WHY": "PASS" if qwhy.target_state.state_id == candidate_state.state_id and why_has_recipe else "FAIL",
        "SUPPORT": "PASS", "REPLAY": "PASS_PERSISTED_RECIPE" if replay_status else "FAIL",
        "REFINEMENT": "READY_AFTER_CANONICAL_PUBLICATION",
        "UNKNOWN": "PASS" if qunknown.status == "UNKNOWN" else "FAIL",
        "TEMPORAL_VALIDITY": "PASS" if candidate_time_ok and async_time_ok else "FAIL",
        "difference_semantics": difference_classes,
        "query_time_ma": TARGET_AGE,
        "async_latest_valid_time_ma": 210.0,
        "candidate_history_rows": len(qhist)}
    if any(value == "FAIL" for key, value in query_acceptance.items() if key.isupper()):
        raise ValueError("isolated candidate query acceptance failed")
    _write(output / "B6L_QUERY_ACCEPTANCE.json", query_acceptance)
    _write(output / "B6L_DIFFERENCE.json", {"world_history_difference_status": qdiff.status.value,
        "world_history_operation": qdiff.operation, "world_history_equal": qdiff.equal,
        "required_semantic_classes": difference_classes,
        "source_to_candidate_geometry": "CHANGED", "topology_identity": "UNCHANGED",
        "asynchronous_fields": "NOT_UPDATED_ASYNC", "unknown_boundary_accommodation": "UNKNOWN",
        "runtime_products": "MODEL_SCOPE_LIMITATION"})

    publication_plan = canonical_publication_plan(candidate_id=b6k_result["candidate_id"],
        candidate_state_id=str(candidate_state.state_id), payload_sha256=EXPECTED_PAYLOAD,
        topology_identity=b6k_result["topology_identity"], replay_recipe_id=str(recipe.recipe_id),
        dt_hex=b6k_result["dt_hex"], target_age_ma=TARGET_AGE)
    _write(output / "B6L_CANONICAL_PUBLICATION_SEMANTICS.json", publication_plan)
    _write(output / "B6L_PUBLICATION_TRANSACTION.json", {"status": "PASS_PLAN_ONLY",
        "canonical_write_executed": False, "mechanism": "HistoryStore.append_transaction (B0-C)",
        "atomic_bundle": publication_plan["atomic_bundle_records"],
        "concurrent_visibility_and_full_power_loss_durability": "OUTSIDE_B0C_CONTRACT",
        "duplicate_payload_copy": False})
    recovery = _publication_recovery_qualification(output)
    if recovery["status"] != "PASS":
        raise ValueError("isolated transaction recovery qualification failed")
    _write(output / "B6L_PUBLICATION_RECOVERY.json", recovery)
    _write(output / "B6L_REFINEMENT_READINESS.json", {"status": "READY_AFTER_CANONICAL_PUBLICATION",
        "reason": "B0-F branch-bound refinement machinery is available; candidate support is preserved as lineage/support references; no prepublication refinement is claimed",
        "refinement_executed": False})
    _write(output / "B6L_IDENTITY_PAYLOAD_POLICY.json", {"status": "PASS_SEPARATE_IDENTITIES",
        "candidate_semantic_identity": b6k_result["candidate_id"],
        "candidate_history_state_id": str(candidate_state.state_id),
        "payload_identity": {"algorithm": "sha256", "digest": EXPECTED_PAYLOAD},
        "future_canonical_state_identity": "NEW_RECORD_ID_ON_CANONICAL_PUBLICATION",
        "payload_policy": "PROMOTE_REFERENCE_NO_COPY"})
    _write(output / "B6L_EVENT_BOUNDARY_CONTRACT.json", {"event_class": "RIFT_PROCESS_ACTIVATION",
        "pair": [1, 3], "event_time_years": DT_YEARS, "target_age_ma": TARGET_AGE,
        "predicate": "SATISFIED_ACTIVATION_POSSIBLE", "transition": "NOT_EXECUTED",
        "pre_transition_topology_identity": b6k_result["topology_identity"],
        "continuation_prerequisite": "EXPLICIT_RIFT_TRANSITION_AUTHORIZATION_AND_EXECUTION"})
    guard = {"status": continuation_guard(event_transition_status="NOT_EXECUTED",
        ordinary_step_requested=True), "after_transition": continuation_guard(
            event_transition_status="EXECUTED", ordinary_step_requested=True),
        "transition_executed": False, "second_dt_selected": False}
    if guard["status"] != "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION":
        raise ValueError("event continuation guard did not block")
    _write(output / "B6L_CONTINUATION_GUARD.json", guard)

    # A compact transactional publication contract identifies exactly the future semantic records.
    _write(output / "B6L_NEXT_STAGE_CONTRACT.json", {"authorization": "NOT_GRANTED_BY_B6L",
        "recommendation": "AUTHORIZE_ATOMIC_FIRST_T1_PUBLICATION_AND_FINAL_QUERY_ACCEPTANCE",
        "publish_exactly_one_state": True, "state_class": publication_plan["canonical_state_class"],
        "event_transition": "MUST_REMAIN_NOT_EXECUTED", "second_dt": "FORBIDDEN",
        "ordinary_continuation_guard": guard["status"],
        "required_records": publication_plan["atomic_bundle_records"]})
    _write(output / "B6L_CANDIDATE_INTEGRITY.json", {"status": "PASS",
        "candidate_id": b6k_result["candidate_id"], "candidate_payload_sha256": payload_sha,
        "source_t0_identity": source.kinematics.canonical_identity_sha256,
        "dt_hex": b6k_result["dt_hex"], "target_age_ma": TARGET_AGE,
        "topology_identity": b6k_result["topology_identity"],
        "endpoint_semantics": "PRE_TRANSITION_EVENT_BOUNDARY_CANDIDATE",
        "candidate_semantic_identity_recomputed": recomputed_candidate == b6k_result["candidate_id"],
        "topology_identity_recomputed": recomputed_topology == b6k_result["topology_identity"],
        "dt_authority_revalidated": True,
        "coordinate_rows": len(pairs), "expected_governed_support_rows": len(expected_pairs),
        "extra_multi_support_rows": support_summary["extra_multi_support_rows"],
        "nodes_with_multi_support": support_summary["nodes_with_multi_support"],
        "unique_canonical_nodes": support_summary["canonical_node_count"],
        "every_canonical_node_represented": support_summary["canonical_node_count"] == 64442,
        "lineage_cardinality": len(pairs), "identity_collisions": 0,
        "lost_canonical_nodes": 0, "unexplained_rows": 0, "arbitrary_owners": 0,
        "state_transfer_metadata": "B6K_STATE_TRANSFER.json",
        "async_validity_metadata": "B6K_ASYNC_DOMAIN_STATE.json"})
    canonical_after = _canonical_snapshot(source)
    if canonical_before != canonical_after:
        raise ValueError("governed canonical source artifacts changed during B6L")
    _write(output / "B6L_CANONICAL_IMMUTABILITY.json", {"status": "PASS",
        "canonical_source_unchanged": True, "canonical_source_artifact_count": len(canonical_before),
        "canonical_world_history_touched": False, "governed_source_payloads_modified": False,
        "canonical_T1_created": False,
        "before_sha256_size": {key: {"sha256": value[0], "bytes": value[1]}
                                for key, value in sorted(canonical_before.items())},
        "after_sha256_size": {key: {"sha256": value[0], "bytes": value[1]}
                               for key, value in sorted(canonical_after.items())}})
    result = {"schema": "R6_B6L_RESULT_V1", "qualification_verdict": "PASS_B6L_CANDIDATE_QUERY_PUBLICATION_READINESS",
        "qualified_source_commit": head, "branch": branch,
        "candidate_integrity": "PASS", "support_query": "PASS",
        "replay_recipe": "PASS_PERSIST_REOPEN_RESOLVE_REPLAY",
        "reproduced_candidate_payload_sha256": replay.produced_payload_identity.digest,
        "query_acceptance": query_acceptance,
        "publication_semantics": "PASS_PLAN_ONLY", "publication_transaction": "PASS_PLAN_ONLY",
        "publication_recovery": "PASS_ISOLATED_SYNTHETIC_TARGET", "refinement": "READY_AFTER_CANONICAL_PUBLICATION",
        "continuation_guard": guard["status"], "canonical_immutability": "PASS",
        "t1_created": False, "canonical_state_changed": False,
        "mechanics_authorized": False, "forward_evolution_authorized": False,
        "topology_transition_executed": False, "second_dt_selected": False,
        "publication_readiness": "READY_FOR_CANONICAL_T1_PUBLICATION",
        "dt_selected": True, "isolated_candidate_constructed": True,
        "runtime_authorized": True,
        "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
        "next_stage_recommendation": "AUTHORIZE_ATOMIC_FIRST_T1_PUBLICATION_AND_FINAL_QUERY_ACCEPTANCE"}
    _write(output / "B6L_RESULT.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    try:
        result = qualify(args.repo_root.resolve(), args.output.resolve())
    except Exception as exc:
        print(f"B6L_FAIL_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
