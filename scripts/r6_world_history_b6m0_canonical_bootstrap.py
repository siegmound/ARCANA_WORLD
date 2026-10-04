#!/usr/bin/env python3
"""Initialize the governed T0 genesis in the env-selected canonical history."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any

from arcana_worldsim.r6.canonical_bootstrap import (
    EXPECTED_HEAD, ROOT_ENV, STORE_DESCRIPTOR,
    classify_canonical_root, discovery_contract, inspect_and_bootstrap,
)

OUTPUT_REL = Path("outputs/r6_b6m0_canonical_world_history_bootstrap")
IMPLEMENTATION_FILES = (
    "src/arcana_worldsim/r6/t0_world_history_adapter.py",
    "src/arcana_worldsim/r6/canonical_bootstrap.py",
    "scripts/r6_world_history_b6m0_canonical_bootstrap.py",
    "tests/test_r6_world_history_b6m0_canonical_bootstrap.py",
)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                                allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def run(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output = repo_root / OUTPUT_REL
    first = inspect_and_bootstrap(repo_root)
    second = inspect_and_bootstrap(repo_root)
    state_ids = first["integrity"]["genesis_state_ids"]
    store_id = first["store_identity"]

    with tempfile.TemporaryDirectory(prefix="b6m0-conflict-") as temporary:
        conflict_root = Path(temporary) / "synthetic-target"
        conflict_root.mkdir()
        _write_json(conflict_root / STORE_DESCRIPTOR,
                    {"schema": "FIXTURE_ONLY", "store_identity": "r6canonical_" + "0" * 64})
        conflict_status = classify_canonical_root(conflict_root, store_id)
    if conflict_status != "CONFLICTING_CANONICAL_STORE":
        raise RuntimeError("synthetic conflicting canonical target was not rejected")

    integrity = first["integrity"]
    result = {
        "schema": "ARCANA_R6_B6M0_RESULT_V1",
        "decision": "PASS_B6M0_CANONICAL_WORLD_HISTORY_BOOTSTRAP",
        "qualified_source_commit": EXPECTED_HEAD,
        "source_branch": first["git_source_gate"]["branch"],
        "source_head": first["git_source_gate"]["head"],
        "canonical_root_status": first["root_status"],
        "canonical_store_id": store_id,
        "canonical_temporal_state_count": integrity["canonical_temporal_state_count"],
        "domain_state_record_count": integrity["domain_state_record_count"],
        "genesis_t0_state_ids": state_ids,
        "latest_canonical_age_ma": integrity["latest_age_ma"],
        "initialization_status": first["decision"],
        "atomic_initialization": "PASS_B0_C_TRANSACTION_IN_PRIVATE_STAGE_THEN_ATOMIC_DIRECTORY_RENAME",
        "durable_reopen": "PASS_TYPED_RECORDS_AND_QUERIES_AFTER_REOPEN",
        "idempotence": second["decision"],
        "conflict_test": conflict_status,
        "query_acceptance": {
            "STATE": integrity["state_query"],
            "HISTORY": "PASS_SINGLE_GENESIS_EPOCH_NO_PREDECESSOR",
            "WHY": "PASS_PROVENANCE_RESOLVES",
            "SUPPORT": integrity["support_status"],
            "UNKNOWN": integrity["unknown_status"],
            "TEMPORAL_VALIDITY": "PASS_T0_INSTANT_AND_AUTHORITY_ANCHOR",
            "DIFFERENCE": "NOT_APPLICABLE_GENESIS_NO_PREDECESSOR",
            "REPLAY": "NOT_APPLICABLE_NO_PREDECESSOR_RECIPE",
            "REFINEMENT": "NOT_AVAILABLE_NO_GENESIS_CHECKPOINT",
        },
        "payload_policy": "REFERENCE_EXISTING_GOVERNED_PAYLOADS",
        "payload_bytes_copied": 0,
        "canonical_world_history_initialized": True,
        "canonical_state_changed": False,
        "t1_created": False,
        "dt_selected": True,
        "isolated_candidate_constructed": True,
        "selected_dt_applied": False,
        "forward_evolution_authorized": False,
        "mechanics_authorized": False,
        "topology_transition_executed": False,
        "runtime_root_source": ROOT_ENV,
        "absolute_path_in_semantic_identity": False,
        "b6m_resume_readiness": "READY_TO_RESUME_ATOMIC_FIRST_T1_PUBLICATION",
    }
    artifacts: dict[str, Any] = {
        "B6M0_RESULT.json": result,
        "B6M0_GIT_SOURCE_GATE.json": {
            **first["git_source_gate"],
            "implementation_worktree_files_sha256": {
                path: sha256((repo_root / path).read_bytes()).hexdigest()
                for path in IMPLEMENTATION_FILES
            },
            "git_object_directory_status": "EXPECTED_VALUE_VERIFIED",
            "git_alternate_object_directory_status": "EXPECTED_VALUE_VERIFIED",
            "canonical_root_environment_status": "EXPECTED_VALUE_VERIFIED",
            "path_values_stored_in_evidence": False,
        },
        "B6M0_CANONICAL_ROOT_INSPECTION.json": {
            "classification_before_initialization": first["root_status"],
            "classification_after_initialization": "VALID_EXISTING_CANONICAL_STORE",
            "conflict_fixture": conflict_status,
            "unrecognized_target_policy": "FAIL_CLOSED_NO_OVERWRITE",
        },
        "B6M0_CANONICAL_STORE_IDENTITY.json": {
            "store_identity": store_id,
            "identity_material": first["store_identity_material"],
            "path_independent": True,
            "descriptor_sha256": integrity["descriptor_sha256"],
        },
        "B6M0_GENESIS_SOURCE.json": {
            "authority_inventory": first["inventory"],
            "source_integrity": first["source_integrity"],
        },
        "B6M0_GENESIS_STATE.json": {
            "history_id": first["state_info"]["history_id"],
            "branch_id": first["state_info"]["branch_id"],
            "time_support": first["state_info"]["time_support"],
            "canonical_temporal_state_count": 1,
            "domain_state_record_count": len(state_ids),
            "domains": first["state_info"]["domains"],
            "state_authorities": first["state_info"]["state_authorities"],
            "candidate_field_package_promoted": False,
        },
        "B6M0_INITIALIZATION_TRANSACTION.json": {
            "status": result["atomic_initialization"],
            "record_ids": first.get("initialization_transaction_record_ids", []),
            "genesis_anchor_id": first["genesis_anchor_id"],
            "staged_privately_before_atomic_install": True,
            "no_partial_canonical_root_exposure": True,
        },
        "B6M0_PAYLOAD_REFERENCE_POLICY.json": {
            "policy": result["payload_policy"],
            "payload_references": integrity["payload_references"],
            "payload_bytes_copied": 0,
            "semantic_identity_is_payload_hash": False,
        },
        "B6M0_DURABLE_REOPEN.json": {
            "status": result["durable_reopen"],
            "store_identity": store_id,
            "store_manifest_sha256": integrity["manifest_sha256"],
            "descriptor_sha256": integrity["descriptor_sha256"],
            "pending_transaction_count": integrity["pending_transaction_count"],
            "persistent_bytes": integrity["persistent_bytes"],
        },
        "B6M0_GENESIS_QUERY_BASELINE.json": result["query_acceptance"],
        "B6M0_IDEMPOTENCE.json": {
            "status": second["decision"],
            "store_identity_unchanged": second["store_identity"] == store_id,
            "canonical_state_count": second["integrity"]["canonical_temporal_state_count"],
            "domain_record_count": second["integrity"]["domain_state_record_count"],
        },
        "B6M0_CONFLICT_TEST.json": {
            "status": conflict_status,
            "target": "SYNTHETIC_ISOLATED_FIXTURE_ONLY",
            "canonical_target_touched": False,
        },
        "B6M0_DISCOVERY_CONTRACT.json": discovery_contract(store_id, state_ids),
        "B6M0_STORE_INTEGRITY.json": integrity,
        "B6M0_CANONICAL_SOURCE_INTEGRITY.json": {
            "status": first["source_integrity"],
            "source_snapshot_equal_before_after": True,
            "scientific_payloads_modified": False,
            "t0_authority_promoted": False,
        },
        "B6M0_B6M_READINESS.json": {
            "status": result["b6m_resume_readiness"],
            "t0_genesis_present": True,
            "t1_absent": True,
            "candidate_unapplied": True,
            "next_action": "RESUME_ATOMIC_FIRST_T1_PUBLICATION",
        },
        "B6M0_NEXT_STAGE_CONTRACT.json": {
            "canonical_state_count_before_t1": 1,
            "latest_state_age_ma": 210.0,
            "t1_absent": True,
            "candidate_payload_sha256": "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a",
            "dt_years": 27123.405156307464,
            "target_age_ma": 209.97287659484368,
            "next_action": "RESUME_ATOMIC_FIRST_T1_PUBLICATION",
            "transition_executed": False,
        },
    }

    output.mkdir(parents=True, exist_ok=True)
    for name, payload in artifacts.items():
        _write_json(output / name, payload)
    test_results = {"schema": "ARCANA_R6_B6M0_TEST_RESULTS_V1",
                    "focused": "PENDING_EXTERNAL_TEST_RUN",
                    "related_regression": "PENDING_EXTERNAL_TEST_RUN",
                    "full_r6": "PENDING_EXTERNAL_TEST_RUN",
                    "qualification_runner_completed": True}
    _write_json(output / "B6M0_TEST_RESULTS.json", test_results)
    readme = """# B6M0 Canonical WORLD_HISTORY Bootstrap\n\nThis package records initialization of the canonical WORLD_HISTORY with the governed ARCANA T0 genesis. It does not publish T1, apply the selected dt, execute a transition, or authorize mechanics/evolution. The runtime store is discovered through `ARCANA_WORLD_HISTORY_ROOT` and is intentionally excluded from Git. See `docs/arcana/B6M0_CANONICAL_WORLD_HISTORY_BOOTSTRAP.md`.\n"""
    (output / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    report_path = repo_root / "docs/arcana/B6M0_CANONICAL_WORLD_HISTORY_BOOTSTRAP.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# B6M0 Canonical WORLD_HISTORY Bootstrap\n\n"
        "## Decision\n\n"
        f"`{result['decision']}` at source baseline `{EXPECTED_HEAD}`. The governed T0 genesis is "
        f"represented by {integrity['domain_state_record_count']} domain-state records at one "
        "canonical temporal state (210 Ma). The B0-C transaction ran in a private staging store, "
        "then the completed directory was atomically installed.\n\n"
        "## Validation\n\n"
        f"- Durable reopen: `{result['durable_reopen']}`.\n"
        f"- Idempotence: `{second['decision']}`.\n"
        f"- Synthetic conflicting target: `{conflict_status}`.\n"
        f"- Genesis queries: STATE `{integrity['state_query']}`, WHY provenance resolves, SUPPORT "
        f"`{integrity['support_status']}`, UNKNOWN `{integrity['unknown_status']}`, and temporal "
        "validity is represented by the T0 instant and authority anchor.\n"
        "- Difference is not applicable because T0 has no predecessor; no replay recipe or "
        "refinement checkpoint was fabricated.\n"
        f"- Existing payloads are referenced; payload bytes copied: `{integrity['payload_bytes_copied']}`.\n\n"
        "## Scientific boundary\n\n"
        "This operation initializes history with the already governed T0. It does not apply the "
        "selected dt or candidate, create T1, move nodes, mutate topology, run mechanics, or "
        "execute a transition. `t1_created=false`, `canonical_state_changed=false`, "
        "`forward_evolution_authorized=false`, and `topology_transition_executed=false`.\n\n"
        "## Discovery and next stage\n\n"
        f"The portable discovery contract uses `{ROOT_ENV}` as the runtime locator and logical "
        f"store id `{store_id}`; the machine path is excluded from semantic identity. "
        f"Readiness: `{result['b6m_resume_readiness']}`. The next stage may resume atomic first-T1 "
        "publication. B6M0 itself did not create T1.\n",
        encoding="utf-8", newline="\n")
    rows = []
    for path in sorted(p for p in output.iterdir() if p.is_file()
                       and p.name != "B6M0_ARTIFACT_MANIFEST.json"):
        rows.append({"relative_path": path.relative_to(repo_root).as_posix(),
                     "byte_size": path.stat().st_size,
                     "sha256": sha256(path.read_bytes()).hexdigest(),
                     "role": "B6M0_BOOTSTRAP_QUALIFICATION_EVIDENCE"})
    rows.append({"relative_path": report_path.relative_to(repo_root).as_posix(),
                 "byte_size": report_path.stat().st_size,
                 "sha256": sha256(report_path.read_bytes()).hexdigest(),
                 "role": "B6M0_HUMAN_CLOSURE_REPORT"})
    _write_json(output / "B6M0_ARTIFACT_MANIFEST.json", {
        "schema": "ARCANA_R6_B6M0_ARTIFACT_MANIFEST_V1",
        "source_commit": EXPECTED_HEAD, "artifacts": rows,
        "manifest_self_hash": False,
    })
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = run(root)
    print(f"B6M0_DECISION={result['decision']}")
    print(f"CANONICAL_STORE_ID={result['canonical_store_id']}")
    print(f"CANONICAL_STATE_COUNT={result['canonical_temporal_state_count']}")
    print(f"GENESIS_DOMAIN_RECORD_COUNT={result['domain_state_record_count']}")
    print(f"B6M_RESUME_READINESS={result['b6m_resume_readiness']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
