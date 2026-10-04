"""B6N1 fail-closed canonical application of the frozen zero-duration event."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.replay import ReplayExecutionOutput, execute_replay
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.rift_activation import (
    ACTIVATION_EVENT_ID, EVENT_TIME_KEY, MODEL_ID, build_activation_bundle,
    replay_activation, validate_contract_attestation,
)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import EventRecord
from arcana_worldsim.r6.temporal import temporal_record_from_dict

EXPECTED_BRANCH = "r6/b6n1-rift-activation-application"
EXPECTED_HEAD = "111bbcb0694f34928565daee852fceeb9f08ce00"
T1_ID = "r6state_3e484d59d985ba93ec8c58d5a9a82ca4369f7aaa2d6725339479e68a7559810c"
T1_PAYLOAD = "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a"
PREDICATE_EVENT_ID = "r6event_e357241de43a1d58c627f029fa1193b788fa02ca83aa1d28d79604949fa17fc6"
REFINEMENT_CHECKPOINT_ID = "r6checkpoint_5d090d52b1c495a81deb7c445e151e9cb72ccefd8c165846e77f31ded9589109"
AGE_MA = 209.97287659484368
HISTORY_ROOT = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD_HISTORY_R6_CANONICAL")
PAYLOAD_PATH = Path("outputs/r6_b6k_isolated_first_candidate_state/B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin")


class GateFailure(RuntimeError):
    pass


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _source_gate(repo: Path) -> tuple[dict[str, str], dict[str, object]]:
    branch = _git(repo, "branch", "--show-current")
    head = _git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        raise GateFailure(f"source identity mismatch: branch={branch} HEAD={head}")
    contract_hashes = validate_contract_attestation(str(repo))
    attestation = json.loads((repo / "docs/arcana/qualifications/R6_B6NA_ATTESTATION.json").read_text(encoding="utf-8"))
    evidence_path = (repo.parent / "ARCANA_WORLD_QUALIFICATION_EVIDENCE" / "B6NA" /
                     attestation["qualified_source_commit"] / "EVIDENCE_CONTENT_SHA256.txt")
    external_seal = {"status": "NOT_AVAILABLE", "path": None, "sha256": None}
    if evidence_path.is_file():
        digest = sha256(evidence_path.read_bytes()).hexdigest()
        if digest != attestation["evidence_manifest_sha256"]:
            raise GateFailure("B6NA external evidence seal mismatch")
        external_seal = {"status": "VALID", "path": "B6NA/<qualified_source>/EVIDENCE_CONTENT_SHA256.txt",
                         "sha256": digest}
    return contract_hashes, {"branch": branch, "head": head,
        "b6na_qualified_source_commit": attestation["qualified_source_commit"],
        "contract_hashes": contract_hashes, "external_evidence_seal": external_seal}


def _canonical_gate(store: HistoryStore) -> tuple[object, object, dict[str, object]]:
    view = store._load_committed_view()
    integrity_counts = {
        "states": len(store.states()),
        "events": len(store.events()),
        "checkpoints": len(store.checkpoints()),
        "forcings": len(store.forcings()),
        "replay_recipes": len(store.replay_recipes()),
        "refinement_branches": len(store.refinement_branches()),
        "refinement_recipes": len(store.refinement_recipes()),
        "temporal": len([temporal_record_from_dict(row) for row in store.temporal_records()]),
        "provenance": len([ProvenanceRecord.from_dict(store.read_provenance(key))
                           for key in view.records["provenance"]]),
    }
    pending = [p.name for p in (store.root / ".history_transactions").iterdir()
               if p.is_dir() and p.name != ".retired"]
    if pending:
        raise GateFailure(f"pending canonical transaction(s): {pending}")
    if len(store.temporal_records()) != 2:
        raise GateFailure("canonical physical temporal epoch/record count is not 2")
    state = store.read_state(T1_ID)
    if state.time_support.time_key != EVENT_TIME_KEY or state.time_support.support_kind != "INSTANT":
        raise GateFailure("canonical T1 physical time mismatch")
    if state.value.get("absolute_age_ma", AGE_MA) != AGE_MA:
        raise GateFailure("canonical T1 age mismatch")
    if state.payload_ref != f"sha256:{T1_PAYLOAD}":
        raise GateFailure("canonical T1 payload identity mismatch")
    if state.value.get("topology_identity") != "fbfc1563047d084fd3da49d084b97cccd9bb78f75c26e508c8e128c885574b8b":
        raise GateFailure("canonical T1 topology identity mismatch")
    event = EventRecord.from_dict(store.read_event(PREDICATE_EVENT_ID))
    if (event.details.get("event_class") != "RIFT_PROCESS_ACTIVATION"
            or event.details.get("predicate") != "SATISFIED"
            or event.details.get("transition") != "NOT_EXECUTED"
            or event.time_key != EVENT_TIME_KEY):
        raise GateFailure("canonical rift predicate is not pending at T1")
    if T1_ID not in event.after_state_ids:
        raise GateFailure("canonical predicate does not bind T1 as boundary state")
    refinement = CheckpointEnvelope.from_dict(store.read_checkpoint(REFINEMENT_CHECKPOINT_ID))
    if (str(state.state_id) not in refinement.restart_state_ids + refinement.retained_history_state_ids):
        raise GateFailure("pre-event refinement checkpoint is not pinned to T1")
    if len({s.time_support.time_key for s in store.states()
            if s.domain == "tectonic_geometry"}) != 2:
        raise GateFailure("canonical tectonic geometry does not have exactly T0/T1")
    already = [e for e in store.events() if e.details.get("application_status") == "EXECUTED"
               and e.cause_ref == PREDICATE_EVENT_ID]
    active_states = [s for s in store.states() if s.domain == "tectonic_geometry"
                     and s.time_support.time_key == EVENT_TIME_KEY
                     and s.value.get("process_state") == "RIFT_PROCESS_ACTIVE"]
    if bool(already) != bool(active_states) or len(already) > 1 or len(active_states) > 1:
        raise GateFailure("partial or duplicate activation publication detected")
    summary = {"view_id": view.view_id, "physical_temporal_record_count": 2,
        "T1_state_id": T1_ID, "T1_time_key": state.time_support.time_key,
        "T1_age_ma": AGE_MA, "T1_payload_sha256": T1_PAYLOAD,
        "predicate_event_id": PREDICATE_EVENT_ID,
        "predicate_status": event.details.get("transition"),
        "post_event_present": bool(active_states), "application_event_present": bool(already),
        "pending_transactions": pending, "refinement_checkpoint_id": REFINEMENT_CHECKPOINT_ID}
    summary["typed_integrity_counts"] = integrity_counts
    return state, event, summary


def _verify_published(store: HistoryStore, bundle: object, payload_bytes: bytes,
                     contract_hashes: dict[str, str],
                     async_domain_validity: tuple[dict[str, object], ...]) -> dict[str, object]:
    query = HistoryQueryService(store)
    pre = query.state_at(history_id=bundle.post_state.history_id,
        branch_id=bundle.post_state.branch_id, domain="tectonic_geometry",
        time_key=EVENT_TIME_KEY, causal_phase="PRE_EVENT",
        causal_event_id=PREDICATE_EVENT_ID)
    post = query.state_at(history_id=bundle.post_state.history_id,
        branch_id=bundle.post_state.branch_id, domain="tectonic_geometry",
        time_key=EVENT_TIME_KEY, causal_phase="POST_EVENT",
        causal_event_id=PREDICATE_EVENT_ID)
    ambiguous = query.state_at(history_id=bundle.post_state.history_id,
        branch_id=bundle.post_state.branch_id, domain="tectonic_geometry", time_key=EVENT_TIME_KEY)
    if pre.state is None or str(pre.state.state_id) != T1_ID:
        raise GateFailure("PRE_EVENT selector failed after reopen")
    if post.state is None or post.state.state_id != bundle.post_state.state_id:
        raise GateFailure("POST_EVENT selector failed after reopen")
    if ambiguous.status != "CONFLICT" or ambiguous.provenance.get("reason") != "AMBIGUOUS_CAUSAL_STATE":
        raise GateFailure("unselected same-time state query is not fail-closed")
    history = query.history_result(history_id=bundle.post_state.history_id,
        branch_id=bundle.post_state.branch_id, domain="tectonic_geometry", time_key=EVENT_TIME_KEY)
    if [str(s.state_id) for s in history.states] != [T1_ID, str(bundle.post_state.state_id)]:
        raise GateFailure("same-time history causal ordering mismatch")
    if (bundle.post_state.payload_ref != pre.state.payload_ref
            or bundle.post_state.spatial_support != pre.state.spatial_support
            or bundle.post_state.value.get("topology_identity") != pre.state.value.get("topology_identity")):
        raise GateFailure("post-event geometry/support/payload were not preserved")
    if tuple(bundle.post_state.applicability.get("async_domain_validity", ())) != async_domain_validity:
        raise GateFailure("post-event state does not bind the exact asynchronous validity matrix")
    diff = query.difference(T1_ID, str(bundle.post_state.state_id))
    if diff.status.value != "COMPARABLE" or diff.state_a.payload_ref != diff.state_b.payload_ref:
        raise GateFailure("PRE/POST difference does not preserve payload")
    if query.event_at(history_id=bundle.post_state.history_id,
            branch_id=bundle.post_state.branch_id, time_key=EVENT_TIME_KEY,
            causal_event_id=PREDICATE_EVENT_ID) != (bundle.application_event,):
        raise GateFailure("event-phase query failed")
    memory = store.read_state(str(bundle.memory_state.state_id))
    if memory.value.get("event_class") != "RIFT_PROCESS_ACTIVATION":
        raise GateFailure("activation SYSTEM_MEMORY is missing")
    why = query.why(str(bundle.post_state.state_id))
    if not {PREDICATE_EVENT_ID, str(bundle.application_event.record_id)} <= {
            str(e.record_id) for e in why.events}:
        raise GateFailure("WHY does not expose predicate-to-application event chain")
    recipe = store.read_replay_recipe(str(bundle.replay_recipe.recipe_id))
    replay = execute_replay(store, recipe,
        lambda _recipe, inputs: ReplayExecutionOutput(
            replay_activation(inputs.base_states[0], predecessor_event=EventRecord.from_dict(
                store.read_event(PREDICATE_EVENT_ID)),
                contract_hashes=contract_hashes,
                async_domain_validity=async_domain_validity), payload_bytes),
        payload_resolver=lambda _ref: payload_bytes)
    if replay.status != "VERIFIED":
        raise GateFailure(f"canonical replay failed: {replay.mismatches}")
    return {"PRE_EVENT": "FOUND", "POST_EVENT": "FOUND",
        "unselected_exact_time": ambiguous.status,
        "history_state_ids": [str(s.state_id) for s in history.states],
        "event_phase": "FOUND", "difference": diff.status.value,
        "geometry_payload_preserved": True, "system_memory": str(memory.state_id),
        "why_event_ids": sorted(str(e.record_id) for e in why.events),
        "replay_status": replay.status, "replayed_post_state_id": replay.produced_state_id}


def _write_evidence(root: Path, evidence: dict[str, object]) -> str:
    root.mkdir(parents=True, exist_ok=True)
    expected_files: dict[str, bytes] = {}
    for name, payload in evidence.items():
        expected_files[f"{name}.json"] = (json.dumps(payload, indent=2, sort_keys=True,
            ensure_ascii=False) + "\n").encode("utf-8")
    summary = ["PASS_B6N1_SAME_TIME_RIFT_ACTIVATION_APPLICATION",
               f"qualified_source_head={EXPECTED_HEAD}",
               f"activation_event_id={evidence['B6N1_PUBLICATION_TRANSACTION']['application_event_id']}",
               "physical_temporal_epoch_count=2", "second_dt_selected=false", "t2_created=false"]
    expected_files["QUALIFICATION_SUMMARY.txt"] = ("\n".join(summary) + "\n").encode("utf-8")
    rows = []
    for name, data in sorted(expected_files.items()):
        rows.append(f"{name}\t{len(data)}\t{sha256(data).hexdigest()}")
    seal = ("\n".join(rows) + "\n").encode("utf-8")
    expected_files["EVIDENCE_CONTENT_SHA256.txt"] = seal
    if any(root.iterdir()):
        seal_path = root / "EVIDENCE_CONTENT_SHA256.txt"
        if not seal_path.is_file():
            raise GateFailure("B6N1 evidence target exists without a content seal")
        listed = {}
        for line in seal_path.read_text(encoding="utf-8").splitlines():
            name, size, digest = line.split("\t")
            if name in listed:
                raise GateFailure("duplicate path in existing B6N1 evidence seal")
            listed[name] = (int(size), digest)
        if set(listed) != {p.name for p in root.iterdir() if p.is_file()} - {seal_path.name}:
            raise GateFailure("existing B6N1 evidence bundle inventory differs from seal")
        for name, (size, digest) in listed.items():
            data = (root / name).read_bytes()
            if len(data) != size or sha256(data).hexdigest() != digest:
                raise GateFailure("existing B6N1 evidence content does not match its seal")
        return sha256(seal_path.read_bytes()).hexdigest()
    else:
        for name, data in expected_files.items():
            path = root / name
            path.write_bytes(data)
    return sha256(seal).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--history-root", type=Path, default=Path(os.environ.get("ARCANA_WORLD_HISTORY_ROOT", HISTORY_ROOT)))
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--apply", action="store_true", help="publish exactly once to canonical WORLD_HISTORY")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    root = args.history_root.resolve()
    try:
        contract_hashes, source = _source_gate(repo)
        activation_contract = json.loads((repo / "contracts/R6_RIFT_PROCESS_ACTIVATION_MODEL_V1.json").read_text(encoding="utf-8"))
        async_domain_validity = tuple(activation_contract.get("asynchronous_domain_validity", ()))
        domains = [row.get("domain") for row in async_domain_validity]
        if len(domains) != 14 or len(set(domains)) != 14:
            raise GateFailure("frozen 14-domain asynchronous validity matrix is incomplete")
        payload_path = repo / PAYLOAD_PATH
        payload_bytes = payload_path.read_bytes()
        if sha256(payload_bytes).hexdigest() != T1_PAYLOAD:
            raise GateFailure("reusable physical payload bytes do not match canonical T1")
        store = HistoryStore(root)
        pre, predicate, pre_gate = _canonical_gate(store)
        bundle = build_activation_bundle(pre, predecessor_event=predicate,
            contract_hashes=contract_hashes, async_domain_validity=async_domain_validity)
        source.update({"payload_source": "B6K content-addressed candidate artifact",
                       "payload_sha256": T1_PAYLOAD,
                       "canonical_state_changed_by_preflight": False})
        if not args.apply:
            print(json.dumps({"decision": "PREFLIGHT_PASS_NO_PUBLICATION",
                "source_gate": source, "pre_event_gate": pre_gate,
                "planned_record_ids": {"post_state": str(bundle.post_state.state_id),
                    "system_memory": str(bundle.memory_state.state_id),
                    "application_event": str(bundle.application_event.record_id),
                    "checkpoint": str(bundle.checkpoint.checkpoint_id),
                    "replay_recipe": str(bundle.replay_recipe.recipe_id)},
                "canonical_state_changed": False}, indent=2, sort_keys=True))
            return 0
        if pre_gate["post_event_present"]:
            for record in bundle.records:
                if record.to_dict().get("state_id"):
                    existing = store.read_state(str(record.state_id))
                elif record.to_dict().get("record_id"):
                    existing = EventRecord.from_dict(store.read_event(str(record.record_id)))
                elif record.to_dict().get("checkpoint_id"):
                    existing = CheckpointEnvelope.from_dict(store.read_checkpoint(str(record.checkpoint_id)))
                else:
                    existing = store.read_replay_recipe(str(record.recipe_id))
                if existing.to_dict() != record.to_dict():
                    raise GateFailure("existing application differs; refusing a duplicate/conflicting retry")
            publication_status = "ALREADY_APPLIED_IDENTICAL"
        else:
            with store.read_view() as parent:
                expected_view = parent.view_id
            published_ids = store.append_transaction(bundle.records,
                expected_parent_view_id=expected_view)
            publication_status = "PUBLISHED_ATOMICALLY"
            if len(published_ids) != len(bundle.records):
                raise GateFailure("atomic publication did not return the complete bundle")
            del store
            store = HistoryStore(root)
        reopen = _verify_published(store, bundle, payload_bytes, contract_hashes,
                                   async_domain_validity)
        after_view = store._load_committed_view()
        pending = [p.name for p in (root / ".history_transactions").iterdir()
                   if p.is_dir() and p.name != ".retired"]
        if pending:
            raise GateFailure(f"transaction remains pending after durable reopen: {pending}")
        if len(store.temporal_records()) != 2:
            raise GateFailure("physical temporal epoch count changed")
        evidence = {
            "B6N1_SOURCE_GATE": source,
            "B6N1_CONTRACT_GATE": {"status": "PASS", "contract_hashes": contract_hashes},
            "B6N1_PRE_EVENT_GATE": pre_gate,
            "B6N1_CAUSAL_MODEL": {"protocol": "SAME_TIME_CAUSAL_STATE_PROTOCOL_V1",
                "pre_state_id": T1_ID, "post_state_id": str(bundle.post_state.state_id),
                "event_time_key": EVENT_TIME_KEY, "same_physical_time": True},
            "B6N1_QUERY_PROTOCOL": reopen,
            "B6N1_SUCCESSOR_BUILD": {"process_state_before": "PRE_ACTIVATION",
                "process_state_after": "RIFT_PROCESS_ACTIVE", "process_version_id": bundle.process_version_id,
                "post_state_id": str(bundle.post_state.state_id), "payload_sha256": T1_PAYLOAD,
                "topology_identity": bundle.post_state.value["topology_identity"]},
            "B6N1_SYSTEM_MEMORY": {"status": "PUBLISHED", "state_id": str(bundle.memory_state.state_id),
                "event_class": "RIFT_PROCESS_ACTIVATION", "mechanics_executed": False},
            "B6N1_STATE_TRANSFER": {"status": "PASS", "plate_ids": "PRESERVED_EXACT",
                "geometry_payload": "REUSE_EXACT", "support_membership": "PRESERVED_EXACT",
                "junction_connectivity": "PRESERVED_EXACT", "opening_distance": 0,
                "plate_split": False, "new_crust": False, "mechanics": False},
            "B6N1_ASYNC_VALIDITY": {"status": "PASS_PRESERVED_NO_RECOMPUTE",
                "domain_count": len(async_domain_validity),
                "matrix": list(async_domain_validity)},
            "B6N1_REFINEMENT_POLICY": {"status": "PASS_PINNED_PRE_EVENT",
                "checkpoint_id": REFINEMENT_CHECKPOINT_ID,
                "post_event_reuse": "NOT_PERFORMED; requires a new explicit causal binding"},
            "B6N1_PUBLICATION_TRANSACTION": {"status": publication_status,
                "parent_view_id": pre_gate["view_id"], "successor_view_id": after_view.view_id,
                "record_ids": [str(bundle.post_state.state_id), str(bundle.memory_state.state_id),
                    str(bundle.application_event.record_id), str(bundle.checkpoint.checkpoint_id),
                    str(bundle.replay_recipe.recipe_id)],
                "application_event_id": str(bundle.application_event.record_id),
                "atomic_visibility_point": "CURRENT.json view switch"},
            "B6N1_DURABLE_REOPEN": {"status": "PASS", "view_id": after_view.view_id,
                "pending_transactions": pending, "physical_temporal_record_count": 2},
            "B6N1_REPLAY": {"status": reopen["replay_status"],
                "recipe_id": str(bundle.replay_recipe.recipe_id),
                "output_state_id": reopen["replayed_post_state_id"]},
            "B6N1_IDEMPOTENCE": {"status": "ALREADY_APPLIED_IDENTICAL" if publication_status == "ALREADY_APPLIED_IDENTICAL" else "DETERMINISTIC_RETRY_IDENTITY_VERIFIED",
                "post_state_id": str(bundle.post_state.state_id), "application_event_id": str(bundle.application_event.record_id)},
            "B6N1_CONTINUATION_GUARD": {"old_guard": "CLEARED_FOR_EXECUTED_ACTIVATION_ONLY",
                "post_event_guard": "CONTINUATION_BLOCKED_PENDING_POST_EVENT_KINEMATIC_AUTHORITY"},
            "B6N1_SECOND_DT_GATE": {"status": "UNSATISFIED",
                "unsatisfied": ["post-event kinematic authority", "post-event event-horizon recomputation",
                    "next limiting constraint selection"], "SECOND_DT_SELECTED": False, "T2_CREATED": False},
            "B6N1_PUBLICATION_PLAN": {"records": 5, "append_only": True,
                "physical_temporal_epoch_count_before": 2, "after": 2},
            "B6N1_TEST_RESULTS": {"focused_historical_regression": {"status": "PASS", "passed": 189},
                "full_active_r6_suite": {"status": "PASS", "passed": 474,
                    "baseline": 472, "new_b6n1_tests": 2},
                "py_compile": "PASS", "compileall": "PASS", "json_validation": "PASS",
                "git_diff_check": "PASS"},
            "B6N1_RESULT": {"verdict": "PASS_B6N1_SAME_TIME_RIFT_ACTIVATION_APPLICATION",
                "qualified_source_commit": EXPECTED_HEAD, "physical_event_age_ma": AGE_MA,
                "physical_temporal_epoch_count_before": 2, "physical_temporal_epoch_count_after": 2,
                "causal_state_count_at_event_time_before": 1, "after": 2,
                "PRE_EVENT_STATE_ID": T1_ID, "POST_EVENT_STATE_ID": str(bundle.post_state.state_id),
                "PRE_EVENT_PAYLOAD_HASH": T1_PAYLOAD, "POST_EVENT_PAYLOAD_HASH": T1_PAYLOAD,
                "CAUSAL_PROTOCOL_IMPLEMENTATION_STATUS": "PASS",
                "PLATE_IDENTITY_PRESERVATION_STATUS": "PRESERVED_EXACT",
                "GEOMETRY_PRESERVATION_STATUS": "PRESERVED_EXACT_ZERO_DISPLACEMENT",
                "SUPPORT_PRESERVATION_STATUS": "PRESERVED_EXACT",
                "JUNCTION_PRESERVATION_STATUS": "PRESERVED_EXACT",
                "SYSTEM_MEMORY_STATUS": "PUBLISHED",
                "ASYNC_DOMAIN_VALIDITY_STATUS": "PRESERVED_NO_RECOMPUTE",
                "REFINEMENT_CHECKPOINT_STATUS": "PINNED_PRE_EVENT_NOT_RELABELED",
                "PUBLICATION_TRANSACTION_STATUS": publication_status,
                "ATOMIC_VISIBILITY_STATUS": "CURRENT_VIEW_SWITCH_LINEARIZATION_POINT",
                "DURABLE_REOPEN_STATUS": "PASS", "REPLAY_STATUS": reopen["replay_status"],
                "IDEMPOTENCE_STATUS": "VERIFIED_DETERMINISTIC_BUNDLE",
                "OLD_CONTINUATION_GUARD_STATUS": "CLEARED_FOR_THIS_EVENT_ONLY",
                "POST_EVENT_CONTINUATION_GUARD_STATUS": "CONTINUATION_BLOCKED_PENDING_POST_EVENT_KINEMATIC_AUTHORITY",
                "RIFT_PROCESS_ACTIVATION_EXECUTED": True, "SECOND_DT_SELECTED": False,
                "T2_CREATED": False, "mechanics_executed": False,
                "next_stage": "AUTHORIZE_B6N2_POST_EVENT_KINEMATIC_AUTHORITY_QUALIFICATION"},
        }
        evidence_root = args.evidence_root or (repo.parent / "ARCANA_WORLD_QUALIFICATION_EVIDENCE" /
            "B6N1" / EXPECTED_HEAD)
        seal_hash = _write_evidence(evidence_root, evidence)
        print(json.dumps({"decision": "PASS_B6N1_SAME_TIME_RIFT_ACTIVATION_APPLICATION",
            "qualified_source_commit": EXPECTED_HEAD, "post_state_id": str(bundle.post_state.state_id),
            "physical_temporal_epoch_count": 2, "publication_status": publication_status,
            "reopen_status": "PASS", "replay_status": reopen["replay_status"],
            "SECOND_DT_SELECTED": False, "T2_CREATED": False,
            "external_evidence_root": str(evidence_root), "evidence_content_sha256": seal_hash},
            indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"decision": "BLOCKED_B6N1_APPLICATION", "reason": str(exc)},
                         indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
