#!/usr/bin/env python3
"""Read-only B4 qualification for the governed T0 plate-rate adapter."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.identity import content_hash
from arcana_worldsim.r6.plate_kinematics_adapter import (
    B4_BRANCH, build_t0_records, load_governed_source,
    require_interval_coverage, source_snapshot,
)
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.storage import account_storage, history_store_scope
from arcana_worldsim.r6.store import HistoryStore


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _implementation_hashes() -> list[dict[str, str]]:
    paths = ("src/arcana_worldsim/r6/plate_kinematics_adapter.py",
             "scripts/r6_plate_kinematics_b4_qualification.py",
             "tests/test_r6_plate_kinematics_adapter_b4.py")
    return [{"relative_path": name, "sha256": _sha(ROOT / name)} for name in paths]


def _public_inventory(inventory: dict) -> dict:
    return {key: value for key, value in inventory.items() if not key.startswith("_")}


def _write_artifact_manifest(output_dir: Path) -> None:
    report = ROOT / "docs/arcana/B4_PLATE_KINEMATICS_TEMPORAL_ADAPTER_QUALIFICATION.md"
    artifacts = []
    candidates = [(path, path.relative_to(ROOT).as_posix())
                  for path in output_dir.iterdir() if path.is_file()
                  and path.name != "B4_ARTIFACT_MANIFEST.json"]
    if report.is_file():
        candidates.append((report, report.relative_to(ROOT).as_posix()))
    for path, relative in sorted(candidates, key=lambda item: item[1]):
        role = ("HUMAN_CLOSURE_REPORT" if path == report else
                "MACHINE_READABLE_QUALIFICATION_RESULT" if path.name == "B4_RESULT.json" else
                "HOW_TO_RERUN_AND_ARTIFACT_GUIDE" if path.name == "README.md" else
                "TEST_AND_STATIC_VALIDATION_EVIDENCE" if path.name == "B4_TEST_RESULTS.json" else
                "QUALIFICATION_EVIDENCE")
        artifacts.append({"relative_path": relative, "byte_size": path.stat().st_size,
                          "sha256": _sha(path), "role": role})
    _write_json(output_dir / "B4_ARTIFACT_MANIFEST.json", {
        "schema": "ARCANA_R6_B4_ARTIFACT_MANIFEST_V1",
        "hash_algorithm": "SHA256", "manifest_excludes_itself": True,
        "artifacts": artifacts})


def qualify(repository_root: Path, output_dir: Path, work_root: Path) -> dict:
    source, inventory = load_governed_source(repository_root)
    before = source_snapshot(inventory)
    records_a = build_t0_records(source)
    records_b = build_t0_records(source)
    deterministic = {
        "forcing_id_equal": records_a.forcing.forcing_id == records_b.forcing.forcing_id,
        "driver_payload_identity_equal": records_a.driver_payload_identity_sha256 == records_b.driver_payload_identity_sha256,
        "source_provenance_id_equal": records_a.source_provenance.record_id == records_b.source_provenance.record_id,
        "adapter_provenance_id_equal": records_a.adapter_provenance.record_id == records_b.adapter_provenance.record_id,
        "index_state_id_equal": records_a.index_state.state_id == records_b.index_state.state_id,
    }
    if not all(deterministic.values()):
        raise RuntimeError("deterministic adapter identities differ")

    work_root.mkdir(parents=True, exist_ok=True)
    store_path = work_root / "world-history-store"
    started = time.perf_counter()
    store = HistoryStore(store_path)
    published = store.append_transaction((records_a.source_provenance,
        records_a.forcing, records_a.adapter_provenance, records_a.index_state))
    publish_seconds = time.perf_counter() - started
    del store
    gc.collect()
    started = time.perf_counter()
    reopened = HistoryStore(store_path)
    reopen_seconds = time.perf_counter() - started
    forcing_loaded = reopened.read_forcing(str(records_a.forcing.forcing_id))
    state_loaded = reopened.read_state(str(records_a.index_state.state_id))
    why = HistoryQueryService(reopened).why(str(state_loaded.state_id))
    why_forcing_ids = sorted(str(record.forcing_id) for record in why.forcings)
    if (str(records_a.forcing.forcing_id) not in why_forcing_ids
            or why.unresolved_references):
        raise RuntimeError("WHY traversal did not resolve the adapter forcing")
    external_paths = [inventory["_payload_paths_internal"][row["logical_path"]]
                      for row in inventory["payload_artifacts"]
                      if row["logical_path"].startswith("external://")]
    accounting = account_storage(history_store_scope(reopened,
        external_payloads=external_paths)).to_dict()
    after = source_snapshot(inventory)
    if before != after:
        raise RuntimeError("governed source changed during read-only qualification")

    # The governed source has only an instantaneous T0 anchor.  The interval
    # request is expected to fail closed and contributes no forcing record.
    interval_rejected = False
    try:
        require_interval_coverage(source, 210.0, 205.0)
    except ValueError:
        interval_rejected = True
    if not interval_rejected:
        raise RuntimeError("positive-duration request unexpectedly received coverage")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = [{"logical_path": path, "sha256": digest, "byte_size": size,
                    "mtime_ns_before": mtime_before, "mtime_ns_after": after[path][2],
                    "unchanged": before[path] == after[path]}
                   for path, (digest, size, mtime_before) in sorted(before.items())]
    authority_inventory = _public_inventory(inventory)
    authority_inventory["real_adapter_output"] = {
        "forcing_id": str(records_a.forcing.forcing_id),
        "authority_class": records_a.forcing.authority_class.value,
        "support_class": records_a.forcing.support_class.value,
        "time_support": records_a.forcing.time_support.to_dict(),
        "domain": records_a.forcing.domain,
        "plate_ids": list(source.plate_ids),
        "quantity": "PER_PLATE_EULER_ANGULAR_VELOCITY_VECTOR",
        "units": "rad/year", "reference_frame": source.reference_frame,
        "driver_payload_identity_sha256": records_a.driver_payload_identity_sha256,
        "vector_count": len(source.plates), "canonical_state_changed": False,
    }
    temporal = {
        "hard_anchors_ma": [source.time_ma], "anchor_support": "INSTANT_ONLY",
        "positive_duration_intervals": [], "positive_duration_request_rejected": interval_rejected,
        "interval_validity": "UNKNOWN", "global_dt_selected": False,
        "discontinuities_supported": [], "event_lead_time_lower_bound_ma": None,
        "candidate_event_pairs_unknown": 30,
        "reason": "motion segment validity is UNBOUND and renewal/change law is BLOCKED",
    }
    forcing_inventory = {"records": [records_a.forcing.to_dict()],
        "source_provenance_id": str(records_a.source_provenance.record_id),
        "adapter_provenance_id": str(records_a.adapter_provenance.record_id),
        "qualification_index_state_id": str(records_a.index_state.state_id),
        "persisted_transaction_ids": list(published), "reopened_forcing_sha256": content_hash(forcing_loaded),
        "reopened_state_id": str(state_loaded.state_id),
        "why": {"forcing_ids": why_forcing_ids,
            "provenance_ids": sorted(str(row.record_id) for row in why.provenance_records),
            "unresolved_references": list(why.unresolved_references),
            "external_reference_count": len(why.external_references)}}
    dependency_gaps = {
        "available_now": ["T0 plate IDs", "per-plate T0 Euler angular-rate vectors in rad/year",
            "synthetic no-net-rotation gauge identity", "coarse face plate IDs and topology identity"],
        "derivable_governed": [],
        "candidate_only": ["pyGPlates processing; not production-authorized or validated for R6"],
        "missing": ["positive-duration motion validity/change law", "governed plate-to-grid-node mapping",
            "boundary type/accommodation and contact laws", "topology transition/event schedule",
            "authorized physical interval and dt constraints"],
        "not_required_for_B4": ["geometry movement", "mechanics", "T1"],
        "shellset_input_readiness": "BLOCKED; no node support mapping or governed interval law",
        "recommended_next_domain": "SPATIAL_PLATE_SUPPORT_AND_BOUNDARY_TOPOLOGY_TRANSITION_CONTRACT",
    }
    immutability = {"status": "PASS", "source_artifacts": source_rows,
        "all_unchanged": all(row["unchanged"] for row in source_rows),
        "source_mutation_performed": False}
    result = {
        "schema": "ARCANA_R6_B4_PLATE_KINEMATICS_QUALIFICATION_V1",
        "decision": "PASS_B4_PLATE_KINEMATICS_TEMPORAL_ADAPTER_QUALIFICATION",
        "qualified_source_commit": source.head, "branch": B4_BRANCH,
        "qualification_implementation": {"repository_commit": source.head,
            "worktree_changes_present": True, "source_hashes": _implementation_hashes()},
        "qualification_scope": "READ_ONLY_T0_INSTANT_ADAPTER_BINDING_AND_SYNTHETIC_INTERVAL_FIXTURES; NO_EVOLUTION",
        "source_authority": source.authority_class,
        "source_semantic_identity_sha256": source.canonical_identity_sha256,
        "source_artifact_sha256": source.artifact_sha256,
        "tool_status": {"pygplates": "CANDIDATE_PROCESSOR_NOT_SCIENTIFIC_AUTHORITY",
            "production_authorized": False, "runtime_invoked": False},
        "adapter": {"type": "READ_ONLY_T0_INSTANT_PLATE_EULER_RATE_BINDING",
            "output_quantity": "PER_PLATE_EULER_ANGULAR_VELOCITY_VECTOR",
            "units": "rad/year", "plate_count": len(source.plate_ids),
            "plate_ids": list(source.plate_ids), "face_count": source.face_count,
            "boundary_count": source.boundary_count,
            "plate_to_grid_node_mapping": "UNAVAILABLE"},
        "persistence": {"status": "PASS_CLOSE_REOPEN_TYPED_READ_AND_WHY",
            "append_transaction_seconds": publish_seconds, "reopen_seconds": reopen_seconds,
            "record_count": 4, "forcing_id": str(records_a.forcing.forcing_id),
            "why_forcing_resolved": str(records_a.forcing.forcing_id) in why_forcing_ids,
            "why_unresolved_references": list(why.unresolved_references)},
        "determinism": {"status": "PASS" if all(deterministic.values()) else "FAIL", **deterministic},
        "synthetic_edge_cases": {"fixture_only": True,
            "qualification": "exercised by focused tests; no synthetic values treated as authority"},
        "temporal_support": temporal,
        "dependency_gaps": dependency_gaps,
        "source_immutability": "PASS" if immutability["all_unchanged"] else "FAIL",
        "storage_accounting": {key: value for key, value in accounting.items() if key != "files"},
        "scientific_side_effects": {"canonical_state_changed": False,
            "t0_payload_modified": False, "dt_selected": False, "t1_created": False,
            "mechanics_authorized": False, "forward_evolution_authorized": False,
            "shellset_executed": False, "orbdata_mechanics_executed": False,
            "provider_authority_promoted": False},
        "b5_readiness": "READY_FOR_B5_WITH_KINEMATIC_GAPS",
        "next_stage_authorization": "AUTHORIZE_B5_MULTI_DOMAIN_TEMPORAL_INTEGRATION_DESIGN_AND_QUALIFICATION",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output_dir / "B4_AUTHORITY_INVENTORY.json", authority_inventory)
    _write_json(output_dir / "B4_TEMPORAL_SUPPORT.json", temporal)
    _write_json(output_dir / "B4_FORCING_INVENTORY.json", forcing_inventory)
    _write_json(output_dir / "B4_DEPENDENCY_GAPS.json", dependency_gaps)
    _write_json(output_dir / "B4_SOURCE_IMMUTABILITY.json", immutability)
    _write_json(output_dir / "B4_ACCOUNTING.json", accounting)
    _write_json(output_dir / "B4_RESULT.json", result)
    _write_artifact_manifest(output_dir)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path,
        default=ROOT / "outputs/r6_b4_plate_kinematics_qualification")
    parser.add_argument("--work-root", type=Path, default=None,
        help="temporary WORLD_HISTORY location; defaults to an automatically removed temp directory")
    args = parser.parse_args()
    if args.work_root is None:
        with tempfile.TemporaryDirectory(prefix="arcana-r6-b4-") as temporary:
            result = qualify(args.repository_root.resolve(), args.output_dir.resolve(), Path(temporary))
    else:
        result = qualify(args.repository_root.resolve(), args.output_dir.resolve(), args.work_root.resolve())
    print(f"B4_DECISION={result['decision']}")
    print(f"B4_SOURCE_COMMIT={result['qualified_source_commit']}")
    print(f"B4_FORCING_ID={result['persistence']['forcing_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
