"""B6M-R1D T1 refinement-source checkpoint and child-support qualification."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORLD_ROOT = ROOT.parent
EXPECTED_BRANCH = "r6/b6m-r1d-refinement-checkpoint-child-cells"
EXPECTED_STORE_ID = "r6canonical_18bab1f51f02b62f6b78e893b24c9fd81f8d48b8ed30d513c6d19141ebf3e4a0"
EXPECTED_T1_ID = "r6state_3e484d59d985ba93ec8c58d5a9a82ca4369f7aaa2d6725339479e68a7559810c"
EXPECTED_T1_AGE = 209.97287659484368
EXPECTED_T1_PAYLOAD = "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a"
EXPECTED_T0_CHECKPOINT_ID = "r6checkpoint_d6b138a164345e46390a6e9be70dca574dab761102f88030ea5e144a2c3f7c92"
EXPECTED_MAPPING_SHA = "63a111d9be7485bc97bd3cc51c54ced72fcdc19619c476399fb7bf2b9b8c7c5e"
EXPECTED_MAPPING_GZIP_SHA = "9a7eecf625298faf8f1d6e9588bab9e76c7566d6a43d036b9ae33a69a0141dd4"
EXPECTED_SOURCE_T0_ID = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
EXPECTED_B6M1C_HEAD = "8e6a09eb39956d316091a3d8ff8c1fa4fe908876"
MAPPING_EVIDENCE_KEY = f"B6MR1C/{EXPECTED_B6M1C_HEAD}"
MAPPING_PATH = WORLD_ROOT / "ARCANA_WORLD_QUALIFICATION_EVIDENCE" / MAPPING_EVIDENCE_KEY / "B6MR1C_SUPPORT_MAPPING.json.gz"
MAPPING_MANIFEST = MAPPING_PATH.parent / "EVIDENCE_CONTENT_SHA256.txt"
ATTESTATION_PATH = ROOT / "docs/arcana/qualifications/R6_B6MR1C_ATTESTATION.json"
CONTRACT_PATH = ROOT / "contracts/R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1.json"
PAYLOAD_PATH = ROOT / "outputs/r6_b6k_isolated_first_candidate_state/B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin"
EXPECTED_WORKTREE_PATHS = {
    "contracts/R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1.json",
    "src/arcana_worldsim/r6/hierarchical_refinement.py",
    "scripts/r6_b6m_r1d_refinement_checkpoint_child_cells.py",
    "tests/test_r6_b6m_r1d_refinement_checkpoint_child_cells.py",
    "tests/_git_test_env.py",
    "tests/test_r6_repository_context.py",
    "tests/test_r6_b6b_accommodation_state_transfer.py",
    "tests/test_r6_b6c_targeted_model_decision.py",
    "tests/test_r6_plate_kinematics_adapter_b4.py",
    "tests/test_r6_pre_orbdata_heat_flow_source_audit.py",
}


class QualificationError(RuntimeError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _plain_json_value(value: Any) -> Any:
    """Normalize frozen record tuples/mappings against JSON request values."""
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): _plain_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json_value(item) for item in value]
    return value


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=False,
                            capture_output=True, text=True)
    if result.returncode:
        raise QualificationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _unrelated_worktree_paths(status: str) -> list[str]:
    unrelated = []
    for line in status.splitlines():
        if not line:
            continue
        path = line[3:]
        if path not in EXPECTED_WORKTREE_PATHS:
            unrelated.append(path)
    return sorted(unrelated)


def source_gate() -> dict[str, Any]:
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "--verify", "HEAD")
    object_type = _git("cat-file", "-t", "HEAD")
    if branch != EXPECTED_BRANCH or object_type != "commit":
        raise QualificationError("source branch or HEAD object type is not qualified for B6M-R1D")
    status_result = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, check=False, capture_output=True, text=True)
    if status_result.returncode:
        raise QualificationError("git status failed: " + status_result.stderr.strip())
    status = status_result.stdout.rstrip("\r\n")
    staged = _git("diff", "--cached", "--name-only")
    if staged:
        raise QualificationError("B6M-R1D requires an unstaged source worktree")
    unrelated = _unrelated_worktree_paths(status)
    if unrelated:
        raise QualificationError("unrelated worktree paths: " + ", ".join(sorted(unrelated)))
    store_root = os.environ.get("ARCANA_WORLD_HISTORY_ROOT")
    required_env = {
        "GIT_OBJECT_DIRECTORY": r"C:\Users\jose_\AppData\Local\ARCANA\git-objects\r6",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": (
            r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD1_v0_6D1_R3_11_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CANDIDATE\.git\objects"),
        "ARCANA_WORLD_HISTORY_ROOT": r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD_HISTORY_R6_CANONICAL",
    }
    mismatches = {key: {"expected": value, "actual": os.environ.get(key)}
                  for key, value in required_env.items()
                  if os.environ.get(key) != value}
    if mismatches or not store_root:
        raise QualificationError("repository/store environment differs: " +
                                 json.dumps(mismatches, sort_keys=True))
    return {"branch": branch, "head": head, "object_type": object_type,
            "worktree_unrelated_paths": [], "staged_paths": [],
            "canonical_store_id": EXPECTED_STORE_ID,
            "environment_contract": "PASS; absolute roots omitted from portable evidence"}


def _mapping_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not MAPPING_PATH.is_file() or not MAPPING_MANIFEST.is_file():
        raise QualificationError("retained B6MR1C mapping evidence is unavailable")
    compressed = MAPPING_PATH.read_bytes()
    gzip_sha = _sha(compressed)
    manifest_rows = {}
    for line in MAPPING_MANIFEST.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match:
            manifest_rows[match.group(2)] = match.group(1)
    if (gzip_sha != EXPECTED_MAPPING_GZIP_SHA or
            manifest_rows.get(MAPPING_PATH.name) != EXPECTED_MAPPING_GZIP_SHA):
        raise QualificationError("retained mapping gzip hash differs from qualified B6MR1C evidence")
    for relative, expected_sha in manifest_rows.items():
        retained = MAPPING_PATH.parent / relative
        if not retained.is_file() or _sha(retained.read_bytes()) != expected_sha:
            raise QualificationError(f"B6MR1C evidence manifest mismatch: {relative}")
    with gzip.open(MAPPING_PATH, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    attestation = _json(ATTESTATION_PATH)
    coverage_path = MAPPING_PATH.parent / "B6MR1C_MAPPING_COVERAGE.json"
    coverage = _json(coverage_path)
    if (attestation["qualified_source_commit"] != EXPECTED_B6M1C_HEAD or
            attestation["parent_support"]["mapping_sha256"] != EXPECTED_MAPPING_SHA or
            coverage["mapping_sha256"] != EXPECTED_MAPPING_SHA or
            coverage["mapping_rows_sha256_gzip"] != EXPECTED_MAPPING_GZIP_SHA):
        raise QualificationError("B6MR1C mapping attestation does not match its retained payload")
    if (len(rows) != 66435 or len({row["representation_id"] for row in rows}) != 66435 or
            len({row["source_canonical_node_id"] for row in rows}) != 64442):
        raise QualificationError("retained B6MR1C mapping cardinality/identity check failed")
    if any(row.get("lineage", {}).get("source_t0_identity") != EXPECTED_SOURCE_T0_ID or
           row.get("lineage", {}).get("candidate_payload_sha256") != EXPECTED_T1_PAYLOAD
           for row in rows):
        raise QualificationError("mapping lineage differs from canonical T1 candidate inputs")
    from arcana_worldsim.r6.hierarchical_refinement import canonical_parent_order
    cell_union: set[str] = set()
    single = multi = boundary_multi = 0
    for row in rows:
        cells = row.get("parent_region_cell_ids", [])
        ordered = canonical_parent_order(cells)
        if not ordered:
            raise QualificationError("mapping row has no parent-cell support")
        if ordered != tuple(cells):
            raise QualificationError("mapping row parent-cell order is not canonical")
        cell_union.update(cells)
        single += len(cells) == 1
        multi += len(cells) > 1
        boundary_multi += bool(row.get("boundary_interface_ids")) and len(cells) > 1
    if (len(cell_union), single, multi) != (64800, 1028, 65407) or not boundary_multi:
        raise QualificationError("retained mapping support coverage differs from B6MR1C")
    if coverage.get("support_cell_union_count") != len(cell_union):
        raise QualificationError("B6MR1C reported parent support union differs from retained rows")
    return rows, {"authority": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
        "mapping_sha256": EXPECTED_MAPPING_SHA, "mapping_rows_sha256_gzip": gzip_sha,
        "attested_source_commit": EXPECTED_B6M1C_HEAD,
        "representation_count": len(rows), "single_cell_mappings": single,
        "multi_cell_mappings": multi, "boundary_multicell_representation_count": boundary_multi,
        "unknown": 0, "unmapped": 0, "ambiguous": 0,
        "parent_cell_count": len(cell_union), "parent_cell_ids": list(canonical_parent_order(cell_union)),
        "status": "PASS_RETAINED_AUTHORITY_AND_ROW_COVERAGE_VERIFIED"}


def _minimum_boundary_request(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in rows if row.get("boundary_interface_ids") and
                  len(row.get("parent_region_cell_ids", [])) > 1]
    selected = min(candidates, key=lambda row:(len(row["parent_region_cell_ids"]),
                                                row["representation_id"]))
    parents = selected["parent_region_cell_ids"]
    from arcana_worldsim.r6.hierarchical_refinement import refinement_request_id, subdivide_parent_cells
    scope = "B6MR1D_MINIMUM_BOUNDARY_SUPPORT_QUALIFICATION_REQUEST"
    request_id = refinement_request_id(parent_cell_ids=parents,
        subdivision_factor=2, request_scope=scope)
    cells = subdivide_parent_cells(parent_cell_ids=parents, subdivision_factor=2,
                                   request_scope=scope)
    return {"request_id": request_id, "request_scope": scope,
        "selected_mapping_representation_id": selected["representation_id"],
        "selected_boundary_interface_ids": selected["boundary_interface_ids"],
        "selection_rule": "FEWEST_PARENT_CELLS_THEN_REPRESENTATION_ID_AMONG_BOUNDARY_MULTICELL_ROWS",
        "selection_is_physical_region_authority": False,
        "parent_cell_ids": list(parents), "subdivision_factor": 2,
        "child_cells": [cell.to_dict() for cell in cells],
        "child_cell_ids": [cell.cell_id for cell in cells],
        "child_cell_count": len(cells)}


def _assert_no_active_transactions(root: Path) -> None:
    tx = root / ".history_transactions"
    if tx.exists() and any(item.name != ".retired" for item in tx.iterdir()):
        raise QualificationError("canonical store has a pending transaction")


def _file_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): _sha(path.read_bytes())
            for path in root.rglob("*") if path.is_file() and ".history_visibility" not in path.parts and
            ".history_transactions" not in path.parts}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                                allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _child_states(inputs, request: dict[str, Any], support_state, provenance_id):
    from arcana_worldsim.r6.hierarchical_refinement import subdivide_parent_cells
    from arcana_worldsim.r6.state import AuthorityClass, DomainStateEnvelope, SupportClass
    bound = support_state.value.get("minimum_qualification_request", {})
    for key in ("request_id", "request_scope", "parent_cell_ids", "subdivision_factor", "child_cell_ids"):
        if _plain_json_value(bound.get(key)) != _plain_json_value(request.get(key)):
            raise QualificationError("child geometry request differs from checkpoint-bound support")
    cells = subdivide_parent_cells(parent_cell_ids=bound["parent_cell_ids"],
        subdivision_factor=bound["subdivision_factor"], request_scope=bound["request_scope"])
    if [cell.cell_id for cell in cells] != request["child_cell_ids"]:
        raise QualificationError("child grid reconstruction differs from declared request")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for cell in cells:
        grouped.setdefault(cell.parent_cell_id, []).append(cell.to_dict())
    results = []
    for parent_cell in request["parent_cell_ids"]:
        rows = grouped[parent_cell]
        child_ids = tuple(row["cell_id"] for row in rows)
        state = DomainStateEnvelope.create(history_id=support_state.history_id,
            branch_id=str(inputs.branch.branch_id), domain="tectonic_geometry_refinement_support",
            time_support=support_state.time_support,
            spatial_support=__import__("arcana_worldsim.r6.state", fromlist=["SpatialSupport"]).SpatialSupport(
                "R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1", child_ids,
                f"{request['subdivision_factor']}x request-scoped derived support", "CELL_SET"),
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            value={"schema": "R6_DERIVED_CHILD_GRID_SUPPORT_V1",
                   "model": "R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1",
                   "request_id": request["request_id"], "support_only": True,
                   "scientific_field_values_created": False,
                   "child_cells": rows},
            uncertainty={"scientific_child_fields": "NOT_CREATED"},
            provenance_ids=(provenance_id,),
            parent_state_ids=(str(support_state.state_id), *support_state.parent_state_ids),
            model_derived=True,
            applicability={"canonical_t1": False, "derived_refinement_support": True},
            refinement_lineage={"request_id": request["request_id"],
                "parent_cell_ids": [parent_cell], "child_cell_ids": list(child_ids),
                "physical_resolution_promotion": False})
        results.append((parent_cell, rows, state))
    return tuple(results)


def _replay_query(store, query, t1):
    recipes = store.replay_recipes()
    matches = [recipe for recipe in recipes if recipe.expected_output_state_id == str(t1.state_id)]
    why = query.why(str(t1.state_id))
    if len(matches) != 1 or not any(str(item.recipe_id) == str(matches[0].recipe_id)
                                    for item in why.replay_recipes):
        raise QualificationError("canonical T1 does not resolve one persisted replay recipe")
    if (matches[0].expected_payload_identity is None or
            matches[0].expected_payload_identity.digest != EXPECTED_T1_PAYLOAD):
        raise QualificationError("canonical T1 replay payload identity mismatch")
    return {"status": "PASS_REPLAY_RECIPE_RESOLVES_TO_CANONICAL_T1",
        "replay_recipe_id": str(matches[0].recipe_id),
        "expected_state_id": matches[0].expected_output_state_id,
        "expected_payload_sha256": matches[0].expected_payload_identity.digest,
        "replay_execution": "NOT_RERUN; existing B6M canonical replay evidence preserved"}


def qualify() -> dict[str, Any]:
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    from arcana_worldsim.r6.checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
    from arcana_worldsim.r6.identity import content_hash
    from arcana_worldsim.r6.provenance import ProvenanceRecord
    from arcana_worldsim.r6.query import DifferenceStatus, HistoryQueryService
    from arcana_worldsim.r6.refinement import (RefinementExecutionOutput,
        RefinementOutputManifestEntry, RefinementReconstructionRecipe,
        execute_refinement)
    from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope,
        SpatialSupport, SupportClass)
    from arcana_worldsim.r6.store import HistoryStore

    source = source_gate()
    root = Path(os.environ["ARCANA_WORLD_HISTORY_ROOT"])
    descriptor = _json(root / "arcana_canonical_store.json")
    if descriptor.get("store_identity") != EXPECTED_STORE_ID:
        raise QualificationError("canonical WORLD_HISTORY store identity mismatch")
    initial_hashes = _file_hashes(root)
    store = HistoryStore(root)
    _assert_no_active_transactions(root)
    with store.read_view() as initial_view:
        before_view_id = initial_view.view_id
        states_before = store.states()
        state_count_before = len(states_before)
        t1 = store.read_state(EXPECTED_T1_ID)
        temporal_before = store.temporal_records()
        checkpoints_before = store.checkpoints()
        branches_before = store.refinement_branches()
        recipes_before = store.refinement_recipes()
        events_before = store.events()
    preflight_counts = (state_count_before, len(checkpoints_before),
                        len(branches_before), len(recipes_before))
    if (preflight_counts not in ((16, 1, 0, 0), (17, 2, 0, 0), (19, 2, 1, 1)) or
            len(temporal_before) != 2 or len(events_before) != 1):
        raise QualificationError("canonical T1 baseline counts differ from authorized B6M status or exact B6MR1D resume state")
    refinement_preexisting = preflight_counts == (19, 2, 1, 1)
    base_checkpoint = next((checkpoint for checkpoint in checkpoints_before
                            if str(checkpoint.checkpoint_id) == EXPECTED_T0_CHECKPOINT_ID), None)
    if base_checkpoint is None:
        raise QualificationError("canonical T0 parent checkpoint identity mismatch")
    if (t1.time_support.time_key != f"{EXPECTED_T1_AGE}Ma" or
            t1.value.get("payload_sha256") != EXPECTED_T1_PAYLOAD or
            t1.value.get("topology_identity") is None or
            t1.branch_id != descriptor.get("branch_id") or
            t1.payload_reference is None or t1.payload_reference.identity.digest != EXPECTED_T1_PAYLOAD):
        raise QualificationError("canonical T1 identity, age, topology, or payload binding mismatch")
    payload_hash = _sha(PAYLOAD_PATH.read_bytes())
    if payload_hash != EXPECTED_T1_PAYLOAD:
        raise QualificationError("retained candidate payload bytes differ from canonical T1 SHA256")
    t1_path = root / "states" / f"{EXPECTED_T1_ID}.json"
    t1_bytes_before = t1_path.read_bytes()
    t1_parent = store.read_state(t1.parent_state_ids[0])
    source_t0_identity = t1_parent.value.get("candidate_source_identity")
    if source_t0_identity != EXPECTED_SOURCE_T0_ID:
        raise QualificationError("T1 parent state does not attest the retained mapping source identity")
    rows, mapping = _mapping_rows()
    if any(row["lineage"].get("source_t0_identity") != source_t0_identity for row in rows):
        raise QualificationError("retained parent mapping does not trace to the canonical T1 parent")
    mapping["source_t0_identity"] = source_t0_identity
    request = _minimum_boundary_request(rows)

    existing_event = events_before[0].to_dict()
    event_value = existing_event.get("details", {})
    if (event_value.get("event_class") != "RIFT_PROCESS_ACTIVATION" or
            event_value.get("pair") != [1, 3] or
            event_value.get("transition") != "NOT_EXECUTED" or
            event_value.get("topology_identity") != t1.value["topology_identity"]):
        raise QualificationError("canonical T1 event boundary differs from the frozen rift stop")
    t1_snapshot = next((row for row in temporal_before
                        if EXPECTED_T1_ID in row.get("state_ids", ())), None)
    if (t1_snapshot is None or t1_snapshot.get("time_key") != t1.time_support.time_key or
            t1_snapshot.get("details", {}).get("rift_transition") != "NOT_EXECUTED" or
            t1_snapshot.get("details", {}).get("topology") != "PRE_TRANSITION"):
        raise QualificationError("canonical T1 temporal/event boundary snapshot mismatch")
    system_memory_ref = t1_snapshot.get("details", {}).get("system_memory_reference")
    if not system_memory_ref:
        raise QualificationError("canonical T1 temporal snapshot lacks SYSTEM_MEMORY provenance")

    # Explicit support metadata binds all set-valued parent cells to the existing T1.
    from arcana_worldsim.r6.hierarchical_refinement import CHILD_GRID_MODEL
    binding_provenance = ProvenanceRecord.create(
        activity="B6MR1D_BIND_CANONICAL_T1_PARENT_SUPPORT",
        input_refs=(str(t1.state_id), f"sha256:{EXPECTED_T1_PAYLOAD}", system_memory_ref,
                    f"sha256:{EXPECTED_MAPPING_SHA}", f"sha256:{EXPECTED_MAPPING_GZIP_SHA}"),
        source_refs=("authority:R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            f"qualification-evidence:{MAPPING_EVIDENCE_KEY}/B6MR1C_SUPPORT_MAPPING.json.gz",
            f"artifact:docs/arcana/qualifications/R6_B6MR1C_ATTESTATION.json#sha256:{_sha(ATTESTATION_PATH.read_bytes())}"),
        parent_provenance_ids=t1.provenance_ids,
        attributes={"canonical_t1_is_referenced_not_rewritten": True,
            "mapping_sha256": EXPECTED_MAPPING_SHA, "mapping_rows_sha256_gzip": EXPECTED_MAPPING_GZIP_SHA,
            "parent_grid_authority": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            "support_semantics": "SET_VALUED_NO_UNIQUE_OWNER",
            "parent_cell_count": 64800, "child_grid_model": CHILD_GRID_MODEL})
    request_record = {key: value for key, value in request.items() if key != "child_cells"}
    support_state = DomainStateEnvelope.create(
        history_id=t1.history_id, branch_id=t1.branch_id,
        domain="tectonic_geometry_refinement_support", time_support=t1.time_support,
        spatial_support=SpatialSupport("R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            tuple(mapping["parent_cell_ids"]), "1-degree nominal parent grid", "CELL_SET"),
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"schema": "R6_B6MR1D_T1_REFINEMENT_PARENT_SUPPORT_V1",
            "role": "REFINEMENT_SOURCE_SUPPORT_VIEW_NOT_NEW_SCIENTIFIC_STATE",
            "canonical_t1_state_id": str(t1.state_id), "canonical_t1_payload_sha256": EXPECTED_T1_PAYLOAD,
            "canonical_t1_age_ma": EXPECTED_T1_AGE,
            "system_memory_reference": system_memory_ref,
            "topology_identity": t1.value["topology_identity"],
            "event_boundary_status": "PRE_TRANSITION; RIFT_PROCESS_ACTIVATION 1:3 NOT_EXECUTED",
            "source_t0_identity": source_t0_identity,
            "parent_mapping_authority": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            "parent_mapping_sha256": EXPECTED_MAPPING_SHA,
            "parent_mapping_gzip_sha256": EXPECTED_MAPPING_GZIP_SHA,
            "parent_mapping_evidence_key": MAPPING_EVIDENCE_KEY,
            "representation_count": mapping["representation_count"],
            "set_valued_support_preserved": True,
            "multi_cell_mapping_count": mapping["multi_cell_mappings"],
            "parent_cell_count": len(mapping["parent_cell_ids"]),
            "minimum_qualification_request": request_record,
            "scientific_field_values_created": False},
        uncertainty={"support_mapping": "RETAINED_B6MR1C_QUALIFIED_MAPPING"},
        provenance_ids=(str(binding_provenance.record_id),),
        parent_state_ids=(str(t1.state_id),), model_derived=True,
        applicability={"canonical_t1": True, "mechanics_restart": False,
                       "refinement_support_view": True})
    source_checkpoint = CheckpointEnvelope.create(
        history_id=t1.history_id, branch_id=t1.branch_id, time_key=t1.time_support.time_key,
        restart_state_ids=(str(t1.state_id), str(support_state.state_id)),
        retained_history_state_ids=(str(t1.state_id), str(support_state.state_id)),
        runtime_identity={"consumer": "B0-F refinement reconstruction contract",
            "role": "REFINEMENT_SOURCE_VIEW_ONLY", "model_adapter": "R6_B6MR1D"},
        configuration={"purpose": "canonical_t1_refinement_source_view",
            "child_grid_model": CHILD_GRID_MODEL,
            "parent_mapping_sha256": EXPECTED_MAPPING_SHA},
        seed_lineage={"determinism": "NO_RANDOMNESS", "source": "canonical_t1_and_qualified_parent_mapping"},
        upstream_dependency_ids=(str(binding_provenance.record_id), *t1.provenance_ids),
        validation_status="VALIDATED",
        restart_compatibility={"b0_f_refinement_source": True,
            "mechanics_restart": False, "shellset_restart": False,
            "creates_temporal_epoch": False, "canonical_t1_rewritten": False},
        parent_checkpoint_id=str(base_checkpoint.checkpoint_id),
        authority_input_refs=(str(t1.state_id), f"sha256:{EXPECTED_T1_PAYLOAD}", system_memory_ref,
            f"sha256:{EXPECTED_MAPPING_SHA}", t1.value["topology_identity"]),
        provider_manifest_refs=(f"qualification-evidence:{MAPPING_EVIDENCE_KEY}/B6MR1C_MAPPING_COVERAGE.json",),
        engine_versions={"adapter": "R6_B6MR1D_SUPPORT_ONLY_V1"},
        output_manifest={"checkpoint_role": "REFINEMENT_SOURCE_VIEW_ONLY",
            "support_state_id": str(support_state.state_id), "temporal_epoch_created": False})
    before_epochs = len(temporal_before)
    existing_support = next((state for state in states_before
                             if str(state.state_id) == str(support_state.state_id)), None)
    existing_checkpoint = next((checkpoint for checkpoint in checkpoints_before
                                if str(checkpoint.checkpoint_id) == str(source_checkpoint.checkpoint_id)), None)
    published_now = False
    if existing_support is None and existing_checkpoint is None:
        if state_count_before != 16 or len(checkpoints_before) != 1:
            raise QualificationError("unexpected records present; refusing non-idempotent checkpoint publication")
        store.append_transaction((binding_provenance, support_state, source_checkpoint))
        published_now = True
    elif (existing_support != support_state or existing_checkpoint is None or
          _plain_json_value(existing_checkpoint.to_dict()) !=
          _plain_json_value(source_checkpoint.to_dict())):
        checkpoint_differences = []
        if existing_checkpoint is not None:
            old_checkpoint = existing_checkpoint.to_dict()
            new_checkpoint = source_checkpoint.to_dict()
            checkpoint_differences = [key for key in sorted(set(old_checkpoint) | set(new_checkpoint))
                                      if _plain_json_value(old_checkpoint.get(key)) !=
                                         _plain_json_value(new_checkpoint.get(key))]
        raise QualificationError(
            "existing B6MR1D checkpoint/support records differ from deterministic reconstruction "
            f"(support_equal={existing_support == support_state}, "
            f"checkpoint_equal={existing_checkpoint is not None and _plain_json_value(existing_checkpoint.to_dict()) == _plain_json_value(source_checkpoint.to_dict())}, "
            f"checkpoint_differing_fields={checkpoint_differences})")
    del store

    store = HistoryStore(root)
    _assert_no_active_transactions(root)
    with store.read_view() as support_view:
        support = store.read_state(str(support_state.state_id))
        checkpoint = CheckpointEnvelope.from_dict(store.read_checkpoint(str(source_checkpoint.checkpoint_id)))
        t1_reopened = store.read_state(EXPECTED_T1_ID)
        temporal_after_support = store.temporal_records()
    if ((published_now and support_view.view_id == before_view_id) or support != support_state or
            _plain_json_value(checkpoint.to_dict()) != _plain_json_value(source_checkpoint.to_dict()) or
            t1_reopened != t1 or
            len(temporal_after_support) != before_epochs):
        raise QualificationError("atomic T1 checkpoint/support publication or reopen failed")
    if t1_path.read_bytes() != t1_bytes_before:
        raise QualificationError("canonical T1 record bytes changed during support publication")

    # Request-scoped boundary sample contains multiple parent cells and no field values.
    from arcana_worldsim.r6.hierarchical_refinement import subdivide_parent_cells
    grid_cells = subdivide_parent_cells(parent_cell_ids=request["parent_cell_ids"],
        subdivision_factor=request["subdivision_factor"], request_scope=request["request_scope"])
    branch = RefinementBranchEnvelope.create(history_id=t1.history_id,
        parent_branch_id=t1.branch_id, base_history_id=t1.history_id,
        refinement_anchor_id=f"B6MR1D:T1:{source_checkpoint.checkpoint_id}",
        region_id=request["request_id"],
        time_interval=(t1.time_support.time_key, t1.time_support.time_key),
        requested_domains=("tectonic_geometry_refinement_support",),
        requested_resolution=f"{request['subdivision_factor']}x request-scoped derived support",
        parent_boundary_conditions={"purpose": "refinement request identity only",
            "scientific_boundary_conditions": "NOT_APPLICABLE",
            "mapping_sha256": EXPECTED_MAPPING_SHA,
            "request_id": request["request_id"]},
        provenance_refs=(str(binding_provenance.record_id),), validation_status="VALIDATED")
    # The runtime runner receives authoritative parent support/state through B0-F.
    def run_child_adapter(inputs):
        parent_support = next(state for state in inputs.parent_states
                              if state.domain == "tectonic_geometry_refinement_support")
        built = _child_states(inputs, request, parent_support,
                              str(binding_provenance.record_id))
        return tuple(RefinementExecutionOutput(state) for _, _, state in built)

    # Build output identity declarations from the exact support-only adapter.
    built_states = []
    for parent_cell in request["parent_cell_ids"]:
        subset = tuple(cell for cell in grid_cells if cell.parent_cell_id == parent_cell)
        from arcana_worldsim.r6.state import TimeSupport
        state = DomainStateEnvelope.create(history_id=t1.history_id,
            branch_id=str(branch.branch_id), domain="tectonic_geometry_refinement_support",
            time_support=t1.time_support,
            spatial_support=SpatialSupport(CHILD_GRID_MODEL,
                tuple(cell.cell_id for cell in subset),
                f"{request['subdivision_factor']}x request-scoped derived support", "CELL_SET"),
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            value={"schema": "R6_DERIVED_CHILD_GRID_SUPPORT_V1", "model": CHILD_GRID_MODEL,
                "request_id": request["request_id"], "support_only": True,
                "scientific_field_values_created": False,
                "child_cells": [cell.to_dict() for cell in subset]},
            uncertainty={"scientific_child_fields": "NOT_CREATED"},
            provenance_ids=(str(binding_provenance.record_id),),
            parent_state_ids=(str(support_state.state_id), str(t1.state_id)),
            model_derived=True, applicability={"canonical_t1": False,
                "derived_refinement_support": True},
            refinement_lineage={"request_id": request["request_id"],
                "parent_cell_ids": [parent_cell],
                "child_cell_ids": [cell.cell_id for cell in subset],
                "physical_resolution_promotion": False})
        built_states.append((parent_cell, subset, state))
    entries = tuple(RefinementOutputManifestEntry(str(state.state_id), (parent_cell,),
        tuple(cell.cell_id for cell in subset), None)
        for parent_cell, subset, state in built_states)
    branch_recipe = RefinementReconstructionRecipe.create(branch=branch,
        base_checkpoint_id=str(source_checkpoint.checkpoint_id),
        parent_state_ids=(str(t1.state_id), str(support_state.state_id)),
        parent_region_cell_ids=tuple(request["parent_cell_ids"]),
        runtime_identity={"adapter": "R6_B6MR1D_CHILD_GEOMETRY_V1",
            "model": CHILD_GRID_MODEL},
        configuration_sha256=content_hash({"contract_sha256": _sha(CONTRACT_PATH.read_bytes()),
            "request_id": request["request_id"], "subdivision_factor": 2}),
        seed_lineage={"determinism": "NO_RANDOMNESS", "request_id": request["request_id"]},
        model_adapter_id="R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1",
        output_manifest=entries, materialization_status="DECLARED")
    accepted = execute_refinement(store, branch, branch_recipe, run_child_adapter)
    if accepted.status != "VERIFIED":
        raise QualificationError("B0-F child-grid acceptance failed: " + ";".join(accepted.mismatches))
    materialized = RefinementReconstructionRecipe.create(branch=branch,
        base_checkpoint_id=str(source_checkpoint.checkpoint_id),
        parent_state_ids=branch_recipe.parent_state_ids,
        parent_region_cell_ids=branch_recipe.parent_region_cell_ids,
        runtime_identity=dict(branch_recipe.runtime_identity),
        configuration_sha256=branch_recipe.configuration_sha256,
        seed_lineage=dict(branch_recipe.seed_lineage), model_adapter_id=branch_recipe.model_adapter_id,
        output_manifest=branch_recipe.output_manifest, materialization_status="MATERIALIZED")
    if refinement_preexisting:
        existing_branch = next((item for item in branches_before
                                if str(item.branch_id) == str(branch.branch_id)), None)
        existing_recipe = next((item for item in recipes_before
                               if str(item.recipe_id) == str(materialized.recipe_id)), None)
        if (existing_branch is None or existing_recipe is None or
                _plain_json_value(existing_branch.to_dict()) != _plain_json_value(branch.to_dict()) or
                _plain_json_value(existing_recipe.to_dict()) != _plain_json_value(materialized.to_dict())):
            raise QualificationError("existing B6MR1D refinement records differ from deterministic reconstruction")
    else:
        store.append_refinement_transaction(branch, materialized,
            (binding_provenance, *(state for _, _, state in built_states)))
    del store

    # Close/reopen and exercise canonical, support, replay, unknown, and refinement queries.
    store = HistoryStore(root)
    _assert_no_active_transactions(root)
    query = HistoryQueryService(store)
    with store.read_view() as final_view:
        t1 = store.read_state(EXPECTED_T1_ID)
        t1_query = query.state_at(history_id=t1.history_id, branch_id=t1.branch_id,
            domain=t1.domain, time_key=t1.time_support.time_key)
        history = query.history_result(history_id=t1.history_id, branch_id=t1.branch_id)
        canonical_branch_state_count = sum(
            state.branch_id == t1.branch_id for state in store.states())
        difference = query.difference(EXPECTED_T1_ID, EXPECTED_T1_ID)
        child = store.read_state(str(built_states[0][2].state_id))
        why = query.why(str(child.state_id))
        support_query = query.available_resolution(history_id=t1.history_id,
            branch_id=t1.branch_id, domain=support_state.domain,
            time_key=t1.time_support.time_key,
            region_cell_ids=tuple(request["parent_cell_ids"]))
        replay_query = _replay_query(store, query, t1)
        refinement_rows = query.refinement_candidates(history_id=t1.history_id,
            branch_id=t1.branch_id, domain=branch.requested_domains[0], region_id=branch.region_id)
        replayed_refinement = execute_refinement(store,
            store.read_refinement_branch(str(branch.branch_id)),
            store.read_refinement_recipe(str(materialized.recipe_id)), run_child_adapter)
        unknown_state = next(state for state in store.states()
            if state.support_class is SupportClass.UNKNOWN)
        unknown_query = query.state_at(history_id=unknown_state.history_id,
            branch_id=unknown_state.branch_id, domain=unknown_state.domain,
            time_key=unknown_state.time_support.time_key)
        async_snapshot = next(row for row in temporal_after_support
            if row.get("details", {}).get("classification") ==
               "CANONICAL_FIRST_STEP_PRETRANSITION_EVENT_BOUNDARY")
        temporal_state = query.state_at(history_id=t1.history_id, branch_id=t1.branch_id,
            domain="climate", time_key=t1.time_support.time_key)
        final_temporal = store.temporal_records()
        final_epoch_count = len(final_temporal)
        final_states = store.states()
        final_events = store.events()
    if t1_query.status != "FOUND" or len(history.states) < canonical_branch_state_count:
        raise QualificationError(
            f"canonical T1 STATE/HISTORY query failed (state_status={t1_query.status}, "
            f"history_state_count={len(history.states)}, canonical_branch_state_count={canonical_branch_state_count})")
    if support_query["status"] != "AVAILABLE" or support_query["cell_count"] != 64800:
        raise QualificationError("governed parent support query failed")
    if unknown_query.status != "UNKNOWN":
        raise QualificationError("UNKNOWN preservation query failed")
    if (not any(item.checkpoint_id == source_checkpoint.checkpoint_id for item in why.checkpoints) or
            not any(item.recipe_id == materialized.recipe_id for item in why.refinement_recipes) or
            not any(item.branch_id == branch.branch_id for item in why.refinement_branches) or
            str(t1.state_id) not in {str(item.state_id) for item in why.state_lineage} or
            why.unresolved_references):
        raise QualificationError("WHY query did not resolve checkpoint/refinement/T1 provenance closure")
    if not refinement_rows or not replay_query["replay_recipe_id"]:
        raise QualificationError("REFINEMENT or REPLAY query did not resolve")
    async_climate = next((row for row in async_snapshot.get("details", {}).get(
        "asynchronous_latest_valid_states", ()) if row.get("domain") == "climate"), None)
    if (temporal_state.status != "MISSING_TIMESTAMP" or async_climate is None or
            async_climate.get("state_valid_time") != "210Ma"):
        raise QualificationError("asynchronous temporal validity was not preserved")
    if (replayed_refinement.status != "VERIFIED" or
            replayed_refinement.produced_state_ids != accepted.produced_state_ids or
            replayed_refinement.expected_state_ids != accepted.expected_state_ids):
        raise QualificationError("repeated B0-F refinement was not identical after durable reopen")
    if difference.status not in {DifferenceStatus.COMPARABLE, DifferenceStatus.TYPE_OR_SHAPE_MISMATCH}:
        raise QualificationError(f"DIFFERENCE query returned unexpected status {difference.status}")
    if final_epoch_count != before_epochs or store.read_state(EXPECTED_T1_ID) != t1:
        raise QualificationError("refinement changed canonical epoch count or T1 state")
    if t1_path.read_bytes() != t1_bytes_before or _sha(PAYLOAD_PATH.read_bytes()) != EXPECTED_T1_PAYLOAD:
        raise QualificationError("canonical T1 record or payload bytes changed")
    if len(final_events) != 1 or final_events[0].to_dict().get("details", {}).get("transition") != "NOT_EXECUTED":
        raise QualificationError("rift event boundary changed")
    _assert_no_active_transactions(root)
    final_hashes = _file_hashes(root)
    for rel, digest in initial_hashes.items():
        if final_hashes.get(rel) != digest:
            raise QualificationError(f"pre-existing canonical store file changed: {rel}")
    final_epochs = len(store.temporal_records())
    store_id = descriptor["store_identity"]
    support_summary = {"checkpoint_id": str(source_checkpoint.checkpoint_id),
        "support_state_id": str(support_state.state_id), "view_before": before_view_id,
        "view_after": final_view.view_id, "epochs_before": before_epochs,
        "epochs_after": final_epochs, "epoch_count_unchanged": final_epochs == before_epochs}
    from arcana_worldsim.r6.identity import canonical_bytes
    output_structure_sha = _sha(canonical_bytes([state.to_dict() for _, _, state in built_states]))
    from arcana_worldsim.r6.b6l_readiness import continuation_guard
    continuation = continuation_guard(event_transition_status=event_value["transition"],
                                      ordinary_step_requested=True)
    if continuation != "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION":
        raise QualificationError("ordinary continuation was not blocked at the rift event")
    return {"source": source, "canonical_store_id": store_id,
        "canonical_t1": {"state_id": EXPECTED_T1_ID, "payload_sha256": payload_hash,
            "age_ma": EXPECTED_T1_AGE, "topology_identity": t1.value["topology_identity"],
            "epoch_count_before": before_epochs, "epoch_count_after": final_epochs,
            "state_bytes_unchanged": True, "payload_bytes_unchanged": True},
        "checkpoint": {**support_summary, "record": checkpoint.to_dict(),
            "system_memory_reference": system_memory_ref}, "mapping": mapping, "request": request,
        "refinement": {"status": accepted.status, "branch_id": str(branch.branch_id),
            "recipe_id": str(materialized.recipe_id), "output_state_ids": list(accepted.produced_state_ids),
            "child_cell_count": sum(len(subset) for _, subset, _ in built_states),
            "output_structure_sha256": output_structure_sha,
            "reopened_replay_status": replayed_refinement.status,
            "replay_identical": True, "isolation": "PASS_CANONICAL_T1_AND_EPOCHS_UNCHANGED"},
        "queries": {"state": t1_query.status, "history": "PASS", "history_state_count": len(history.states),
            "difference": difference.status.value, "why": "PASS_NO_UNRESOLVED_REFERENCES",
            "support": support_query, "replay": replay_query,
            "refinement": [{"record_id": item["record_id"], "validation_status": item["validation_status"]
                           } for item in refinement_rows],
            "unknown": unknown_query.status,
            "temporal_validity": {"t1_time_key": t1.time_support.time_key,
                "asynchronous_climate_status_at_t1": temporal_state.status,
                "climate_latest_valid_time_ma": async_climate["state_valid_time"],
                "fake_synchronization": False}},
        "event_boundary": {"event_class": event_value["event_class"], "pair": event_value["pair"],
            "age_ma": EXPECTED_T1_AGE, "transition": event_value["transition"],
            "topology": "PRE_TRANSITION", "second_dt_selected": False,
            "t2_created": False, "continuation": continuation},
        "scientific_gates": {"runtime_authorized": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
            "mechanics_authorized": False, "forward_evolution_authorized": False,
            "dt2_selected": False, "t2_created": False, "rift_transition_executed": False,
            "canonical_t1_republished": False, "canonical_state_changed": False}}


def _portable(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _portable(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _portable(item)
    elif isinstance(value, str) and ("C:\\Users\\" in value or "F:\\" in value or
            value.startswith("/home/") or value.startswith("/tmp/")):
        raise QualificationError("portable evidence contains an absolute machine path")


def write_evidence(result: dict[str, Any], test_results: dict[str, Any]) -> Path:
    head = result["source"]["head"]
    output = WORLD_ROOT / "ARCANA_WORLD_QUALIFICATION_EVIDENCE" / "B6MR1D" / head
    output.mkdir(parents=True, exist_ok=True)
    mapping = result["mapping"]
    request = result["request"]
    checkpoint = result["checkpoint"]
    refinement = result["refinement"]
    query = result["queries"]
    files = {
        "B6MR1D_SOURCE_GATE.json": result["source"],
        "B6MR1D_T1_CHECKPOINT_CONTRACT.json": {
            "contract_id": "B0F_CHECKPOINT_CONTRACT_V1_AUDIT",
            "checkpoint_schema": "ARCANA_R6_CHECKPOINT_V1",
            "requirements": {"checkpoint_validated": True,
                "history_branch_time_match": True,
                "parent_states_in_restart_or_retained_closure": True,
                "parent_region_is_subset_of_parent_state_cell_support": True,
                "child_state_domain_and_time_match_branch": True,
                "child_support_equals_manifest_child_cell_ids": True,
                "output_parent_cells_subset_of_region": True,
                "payload_identity_matches_manifest": True,
                "provenance_references_resolve": True,
                "child_geometry_is_not_scientific_field_value": True},
            "source_modules": ["src/arcana_worldsim/r6/checkpoint.py",
                "src/arcana_worldsim/r6/refinement.py", "src/arcana_worldsim/r6/store.py",
                "tests/test_r6_world_history_b0_f.py"],
            "B0F_requires_scientific_child_values": False},
        "B6MR1D_T1_CHECKPOINT.json": {"status": "PASS", **checkpoint,
            "role": "REFINEMENT_SOURCE_VIEW_NOT_MECHANICS_RESTART",
            "temporal_record_created": False},
        "B6MR1D_PARENT_SUPPORT_BINDING.json": mapping,
        "B6MR1D_CHILD_CELL_AUTHORITY.json": _json(CONTRACT_PATH),
        "B6MR1D_CHILD_CELL_IDENTITY.json": {"model": "R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1",
            "identity_rule": ["parent_cell_id", "subdivision_factor", "child_row",
                "child_column", "request_id"], "ordering": request["selection_rule"],
            "request_id": request["request_id"], "child_ids": request["child_cell_ids"]},
        "B6MR1D_MINIMUM_REFINEMENT_REQUEST.json": request,
        "B6MR1D_REFINEMENT_ACCEPTANCE.json": refinement,
        "B6MR1D_REFINEMENT_REPLAY.json": {"status": "PASS_DETERMINISTIC_RECONSTRUCTION",
            "request_id": request["request_id"], "child_ids_match": True,
            "bounds_match": True, "parent_child_lineage_match": True,
            "structural_output_sha256": refinement["output_structure_sha256"],
            "reopened_replay_status": refinement["reopened_replay_status"]},
        "B6MR1D_REFINEMENT_ISOLATION.json": {"status": refinement["isolation"],
            "canonical_epoch_count_before": result["canonical_t1"]["epoch_count_before"],
            "canonical_epoch_count_after": result["canonical_t1"]["epoch_count_after"],
            "t1_state_id_unchanged": True, "t1_payload_sha256_unchanged": True,
            "scientific_child_values_created": False},
        "B6MR1D_QUERY_ACCEPTANCE.json": query,
        "B6MR1D_EVENT_BOUNDARY_SAFETY.json": result["event_boundary"],
        "B6MR1D_TEST_RESULTS.json": test_results,
        "B6MR1D_VERTICAL_SLICE_ACCEPTANCE.json": {
            "status": "FIRST_WORLD_HISTORY_VERTICAL_SLICE_ACCEPTED",
            "path": ["governed T0", "qualified first interval", "candidate", "replay",
                "canonical T1", "atomic visibility", "canonical queries",
                "governed refinement entry", "derived child-grid output",
                "rift event-boundary stop"],
            "next_stage": "AUTHORIZE_FIRST_RIFT_TRANSITION_MODEL_AND_APPLICATION_DESIGN"},
    }
    _portable(files)
    for name, body in files.items():
        _write_json(output / name, body)
    evidence_result = {"schema": "ARCANA_R6_B6MR1D_RESULT_V1",
        "verdict": "PASS_B6MR1D_T1_REFINEMENT_CHECKPOINT_CHILD_AUTHORITY_AND_VERTICAL_SLICE_CLOSURE",
        "qualified_source_commit": head, "execution_target": "WINDOWS",
        "ubuntu_work_required": False, "canonical_store_id": result["canonical_store_id"],
        "canonical_t1": result["canonical_t1"], "checkpoint": checkpoint,
        "mapping": {key: value for key, value in mapping.items() if key != "parent_cell_ids"},
        "request": {key: value for key, value in request.items() if key != "child_cells"},
        "refinement": refinement, "queries": query,
        "event_boundary": result["event_boundary"], "scientific_gates": result["scientific_gates"],
        "vertical_slice_acceptance": "FIRST_WORLD_HISTORY_VERTICAL_SLICE_ACCEPTED",
        "next_stage_recommendation": "AUTHORIZE_FIRST_RIFT_TRANSITION_MODEL_AND_APPLICATION_DESIGN"}
    _write_json(output / "B6MR1D_RESULT.json", evidence_result)
    _portable(evidence_result)
    summary = (f"verdict={evidence_result['verdict']}\n"
        f"qualified_source_commit={head}\n" 
        f"canonical_t1_state_id={EXPECTED_T1_ID}\n"
        f"canonical_t1_payload_sha256={EXPECTED_T1_PAYLOAD}\n"
        f"parent_mapping_sha256={EXPECTED_MAPPING_SHA}\n"
        f"child_grid_model=R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1\n"
        f"subdivision_factor_used=2 (request scoped only)\n"
        f"refinement_status={refinement['status']}\n"
        f"child_cell_count={refinement['child_cell_count']}\n"
        f"canonical_epoch_count_before={checkpoint['epochs_before']}\n"
        f"canonical_epoch_count_after={checkpoint['epochs_after']}\n"
        "second_dt_selected=false\nt2_created=false\nrift_transition_executed=false\n")
    (output / "QUALIFICATION_SUMMARY.txt").write_text(summary, encoding="utf-8", newline="\n")
    artifacts = [f"{_sha(path.read_bytes())}  {path.name}"
                 for path in sorted(output.iterdir())
                 if path.is_file() and path.name != "EVIDENCE_CONTENT_SHA256.txt"]
    manifest = "\n".join(artifacts) + "\n"
    manifest_path = output / "EVIDENCE_CONTENT_SHA256.txt"
    manifest_path.write_text(manifest, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true",
                        help="run canonical gates and queries without writing evidence")
    parser.add_argument("--test-results", type=Path,
                        help="portable JSON summary of completed required test/compile checks")
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        if not args.validate_only and (args.test_results is None or not args.test_results.is_file()):
            raise QualificationError("successful evidence publication requires --test-results JSON")
        test_results = {} if args.test_results is None else _json(args.test_results)
        _portable(test_results)
        result = qualify()
        evidence_root = None if args.validate_only else write_evidence(result, test_results)
        manifest_sha = (None if evidence_root is None else
                        _sha((evidence_root / "EVIDENCE_CONTENT_SHA256.txt").read_bytes()))
        print(json.dumps({"verdict": "PASS_B6MR1D_T1_REFINEMENT_CHECKPOINT_CHILD_AUTHORITY_AND_VERTICAL_SLICE_CLOSURE",
            "qualified_source_commit": result["source"]["head"],
            "checkpoint_id": result["checkpoint"]["checkpoint_id"],
            "request_id": result["request"]["request_id"],
            "child_cell_count": result["refinement"]["child_cell_count"],
            "canonical_epochs": [result["checkpoint"]["epochs_before"],
                                 result["checkpoint"]["epochs_after"]],
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "external_evidence_root": None if evidence_root is None else str(evidence_root),
            "external_evidence_manifest_sha256": manifest_sha},
            sort_keys=True, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"verdict": "BLOCKED_B6MR1D_QUALIFICATION", "reason": str(exc)},
                         sort_keys=True, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
