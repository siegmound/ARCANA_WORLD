#!/usr/bin/env python3
"""Qualify read-only ingestion of governed R6 T0 into WORLD_HISTORY."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import time
from typing import Any

from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.storage import account_storage, history_store_scope
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.t0_world_history_adapter import (
    T0AuthorityError, authority_inventory, build_records, source_snapshot,
)


def _portable_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in inventory.items()
            if key not in {"_repository_root", "source_paths_internal"}}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                                allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def qualify(root: Path, output_dir: Path, work_root: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    work_root = (work_root or output_dir.parent / ".b3_work").resolve()
    if output_dir == root or root not in output_dir.parents:
        raise T0AuthorityError("qualification outputs must be inside this repository")
    if work_root == root or root not in work_root.parents:
        raise T0AuthorityError("temporary store must be inside this repository")

    # Authority verification precedes store creation and any output write.
    inventory = authority_inventory(root)
    before = source_snapshot(inventory)
    states, provenance, state_info = build_records(root, inventory)
    repeated_states, repeated_provenance, _ = build_records(root, inventory)
    identity_material = sorted(str(state.state_id) for state in states)
    identity_material.append(str(provenance.record_id))
    identity_hash = sha256("\n".join(identity_material).encode("utf-8")).hexdigest()
    if ([str(state.state_id) for state in states] != [str(state.state_id) for state in repeated_states]
            or str(provenance.record_id) != str(repeated_provenance.record_id)):
        raise T0AuthorityError("B3 adapter record identities are not deterministic")
    state_info["repeatability"] = {"status": "PASS",
        "semantic_record_identity_sha256": identity_hash,
        "repeated_build_state_ids_match": True,
        "repeated_build_provenance_id_matches": True}
    if len(states) != 14:
        raise T0AuthorityError(f"unexpected B3 semantic state count: {len(states)}")
    domains = {state.domain: state for state in states}
    expected_domains = {
        "physical_geography", "land_ocean", "province_state", "topography",
        "tectonic_plate_partition", "plate_kinematics", "bathymetry",
        "tectonic_kinematics_grid", "boundary_classification", "deep", "climate", "hydrology",
        "weak_zone_state", "junction_physical_semantics",
    }
    if set(domains) != expected_domains:
        raise T0AuthorityError("B3 adapter domain inventory differs from its declared scope")

    work_root.mkdir(parents=True, exist_ok=True)
    query_result: dict[str, Any]
    with tempfile.TemporaryDirectory(prefix="b3-t0-history-", dir=work_root) as temp:
        store_path = Path(temp) / "store"
        started = time.perf_counter()
        store = HistoryStore(store_path)
        published = store.append_transaction((*states, provenance))
        publish_seconds = time.perf_counter() - started
        manifest_before_close = store._read("metadata", "store_manifest")
        expected_ids = sorted(str(s.state_id) for s in states)
        del store
        gc.collect()

        started = time.perf_counter()
        reopened = HistoryStore(store_path)
        reopen_seconds = time.perf_counter() - started
        persisted = [reopened.read_state(state_id) for state_id in expected_ids]
        persisted_provenance = reopened.read_provenance(str(provenance.record_id))
        if sorted(str(s.state_id) for s in persisted) != expected_ids:
            raise T0AuthorityError("state identities changed after store reopen")
        if persisted_provenance != provenance.to_dict():
            raise T0AuthorityError("provenance record changed after store reopen")
        query = HistoryQueryService(reopened)
        history_id, branch_id = state_info["history_id"], state_info["branch_id"]
        supported = query.state_at(history_id=history_id, branch_id=branch_id,
                                   domain="physical_geography", time_key="210Ma")
        unknown = query.state_at(history_id=history_id, branch_id=branch_id,
                                 domain="bathymetry", time_key="210Ma")
        missing_domain = query.state_at(history_id=history_id, branch_id=branch_id,
                                        domain="not_governed", time_key="210Ma")
        missing_time = query.state_at(history_id=history_id, branch_id=branch_id,
                                      domain="physical_geography", time_key="209Ma")
        grid_cell = query.state_at(history_id=history_id, branch_id=branch_id,
                                   domain="physical_geography", time_key="210Ma",
                                   cell_id="R6G1D-R000-C000")
        listed = query.history_result(history_id=history_id, branch_id=branch_id)
        why = query.why(str(domains["physical_geography"].state_id))
        same_state_difference = query.difference(str(domains["physical_geography"].state_id),
                                                  str(domains["physical_geography"].state_id))
        query_result = {
            "supported_state": supported.status,
            "unknown_state": unknown.status,
            "missing_domain": missing_domain.status,
            "missing_time": missing_time.status,
            "grid_cell_query": grid_cell.status,
            "grid_cell_query_limitation": (grid_cell.provenance or {}).get("reason"),
            "history_state_count": len(listed.states),
            "history_ordering": listed.ordering,
            "why_state_lineage_count": len(why.state_lineage),
            "why_provenance_count": len(why.provenance_records),
            "why_external_references": list(why.external_references),
            "why_unresolved_references": list(why.unresolved_references),
            "same_state_difference_status": same_state_difference.status.value,
            "same_state_difference_equal": same_state_difference.equal,
            "no_temporal_difference_constructed": True,
        }
        if (supported.status != "FOUND" or unknown.status != "UNKNOWN"
                or missing_domain.status != "MISSING_DOMAIN"
                or missing_time.status != "MISSING_TIMESTAMP"
                or grid_cell.status != "SUPPORT_MISMATCH"
                or len(listed.states) != len(states)
                or not why.provenance_records
                or same_state_difference.status.value != "COMPARABLE"
                or same_state_difference.equal is not True):
            raise T0AuthorityError("WORLD_HISTORY reopen/query/WHY qualification failed")

        accounting = account_storage(history_store_scope(reopened)).to_dict()
        for entry in accounting["files"]:
            absolute_path = Path(entry["path"])
            try:
                relative_path = absolute_path.relative_to(store_path).as_posix()
            except ValueError as exc:
                raise T0AuthorityError("WORLD_HISTORY accounting escaped qualification store") from exc
            entry["path"] = f"qualification_store/{relative_path}"
        manifest_after_reopen = reopened._read("metadata", "store_manifest")
        if manifest_before_close != manifest_after_reopen:
            raise T0AuthorityError("store manifest changed across reopen")
        del reopened
        gc.collect()

    after = source_snapshot(inventory)
    immutability = {
        "status": "PASS" if before == after else "FAIL",
        "comparison": {key: {"before_sha256": before[key][0], "after_sha256": after[key][0],
            "before_bytes": before[key][1], "after_bytes": after[key][1],
            "before_mtime_ns": before[key][2], "after_mtime_ns": after[key][2],
            "unchanged": before[key] == after[key]} for key in sorted(before)},
        "mtime_is_evidence_only": True,
    }
    if before != after:
        raise T0AuthorityError("source artifact bytes or metadata changed during B3")

    # Count only physical payloads actually referenced by ingested states.
    references = {
        "canonical_initial_world": inventory["source_paths_internal"]["canonical_initial_world"],
        "vector_partition": inventory["source_paths_internal"]["vector_partition"],
        "kinematics": inventory["source_paths_internal"]["kinematics"],
    }
    payload_rows = []
    seen: set[str] = set()
    for role, path in references.items():
        digest = before[role][0]
        if digest in seen:
            continue
        seen.add(digest)
        payload_rows.append({"role": role, "identity": f"sha256:{digest}",
                             "byte_size": before[role][1],
                             "ownership": ("REFERENCED_EXTERNAL_GOVERNED_PAYLOAD"
                                 if role in {"canonical_initial_world", "vector_partition"}
                                 else "REFERENCED_TRACKED_GOVERNED_ARTIFACT")})
    external_bytes = sum(row["byte_size"] for row in payload_rows
                         if row["ownership"] == "REFERENCED_EXTERNAL_GOVERNED_PAYLOAD")
    tracked_reference_bytes = sum(row["byte_size"] for row in payload_rows
                                  if row["ownership"] == "REFERENCED_TRACKED_GOVERNED_ARTIFACT")
    accounting["referenced_external_governed_payloads"] = payload_rows
    accounting["referenced_external_governed_payload_bytes"] = external_bytes
    accounting["referenced_tracked_governed_artifact_bytes"] = tracked_reference_bytes
    accounting["world_history_owned_canonical_payload_bytes"] = 0
    accounting["hard_cap_includes_referenced_external_bytes"] = False

    output_dir.mkdir(parents=True, exist_ok=True)
    portable = _portable_inventory(inventory)
    _write_json(output_dir / "B3_T0_AUTHORITY_INVENTORY.json", portable)
    _write_json(output_dir / "B3_T0_STATE_INVENTORY.json", state_info)
    retention = {
        "status": "REVIEW_REQUIRED_FOR_SCIENTIFIC_MINIMALITY",
        "adapter_boundary": "REFERENCE_ONLY; no governed field arrays copied",
        "items": [
            {"item": "initial-world supported fields", "action": "MATERIALIZE",
             "role": "SYSTEM_MEMORY", "reference": f"payload://sha256/{inventory['payload_artifacts'][0]['actual_sha256']}",
             "reason": "current governed T0 support; semantic envelopes retain references only"},
            {"item": "vector partition", "action": "STATIC",
             "role": "SYSTEM_MEMORY", "reference": "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
             "reason": "governed topology dependency for future domain adapters"},
            {"item": "plate kinematics", "action": "STATIC",
             "role": "SYSTEM_MEMORY", "reference": "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
             "reason": "current canonical synthetic T0 model realization; no interval law selected"},
            {"item": "FEG and ShellSet runtime package", "action": "DISCARD",
             "role": "DERIVED_QUERY_OR_RUNTIME_PRODUCT", "reference": "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json; R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json",
             "reason": "excluded from WORLD_HISTORY physical-state ingest; source artifacts remain untouched"},
            {"item": "B-PANGAEA V2 field package", "action": "REVIEW_REQUIRED",
             "role": "CANDIDATE_T0", "reason": "manifest remains CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION"},
            {"item": "unknown-domain masks", "action": "STATIC",
             "role": "SUPPORT_EVIDENCE", "reference": "field refs in R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json",
             "reason": "referenced by UNKNOWN state metadata; not numeric state"},
        ],
        "system_memory_vs_derived_products": "T0 geography/topology/plate kinematics are represented as current inputs; FEG/runtime products remain derived support.",
    }
    _write_json(output_dir / "B3_T0_RETENTION_MAP.json", retention)
    _write_json(output_dir / "B3_T0_ACCOUNTING.json", accounting)
    _write_json(output_dir / "B3_SOURCE_IMMUTABILITY.json", immutability)
    result = {
        "schema": "ARCANA_R6_B3_T0_READ_ONLY_INGEST_RESULT_V1",
        "decision": "PASS_B3_GOVERNED_T0_READ_ONLY_INGEST",
        "qualified_source_commit": inventory["head"],
        "qualification_scope": "READ_ONLY_REFERENCE_INGEST_AND_QUERY; no evolution or mechanics",
        "authority_artifact_count": len({item["logical_path"] for item in
            inventory["tracked_authority_documents"] + inventory["payload_artifacts"]}),
        "authority_payload_count": len(inventory["payload_artifacts"]),
        "ingested_unique_payload_identity_count": len({
            state.payload_reference.identity.digest for state in states
            if state.payload_reference is not None and state.payload_reference.identity is not None}),
        "t0_semantic_state_count": len(states), "t0_state_domains": state_info["domains"],
        "semantic_identity_repeatability": state_info["repeatability"],
        "publication": {"status": "PASS_ATOMIC_TRANSACTION", "record_count": len(published),
                         "transaction_record_ids": list(published), "elapsed_seconds": publish_seconds},
        "reopen": {"status": "PASS_NEW_STORE_INSTANCE", "state_identity_count": len(persisted),
                   "elapsed_seconds": reopen_seconds, "manifest_stable": True},
        "queries": query_result,
        "accounting": {"canonical_persistent_bytes": accounting["canonical_persistent_bytes"],
                       "hard_cap_bytes": accounting["hard_cap_bytes"],
                       "within_hard_cap": accounting["within_hard_cap"],
                       "external_governed_payload_bytes_referenced": external_bytes,
                       "tracked_governed_artifact_bytes_referenced": tracked_reference_bytes},
        "source_immutability": immutability["status"],
        "scientific_side_effects": {"payloads_modified": False, "payloads_regenerated": False,
            "provider_access": False, "mechanics_executed": False, "shellset_executed": False,
            "orbdata_mechanics_executed": False, "dt_selected": False, "t1_created": False,
            "canonical_state_advanced": False, "authority_promoted": False},
        "source_document_gate_snapshot": inventory["governance"],
        "authorization_boundary": {"runtime_authorized": True,
            "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
            "mechanics_authorized": False, "forward_evolution_authorized": False,
            "dt_selected": False, "t1_created": False, "canonical_state_changed": False,
            "runtime_scope_used_by_b3": False},
        "next_stage_readiness": "READY_FOR_B4_WITH_GAPS",
        "recommended_first_temporal_adapter": "PLATE_KINEMATICS_ADAPTER_DESIGN; qualify a governed rotation/interval law before any execution or dt choice",
        "next_stage_authorization": "AUTHORIZE_B4_FIRST_TEMPORAL_ADAPTER_DESIGN_AND_QUALIFICATION",
        "environment_evidence_only": {"platform": __import__("platform").platform(),
            "python": __import__("platform").python_version(),
            "completed_utc": datetime.now(timezone.utc).isoformat()},
    }
    _write_json(output_dir / "B3_T0_INGEST_RESULT.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args()
    try:
        result = qualify(args.repository_root, args.output_dir, args.work_root)
    except Exception as exc:
        print(f"BLOCKED_B3_GOVERNED_T0_INGEST: {exc}")
        return 1
    print(json.dumps({"decision": result["decision"],
                      "states": result["t0_semantic_state_count"],
                      "source_immutability": result["source_immutability"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
