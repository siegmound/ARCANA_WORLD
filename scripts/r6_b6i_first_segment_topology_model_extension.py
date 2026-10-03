#!/usr/bin/env python3
"""Materialize and qualify the authorial B6I topology-process scope."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from arcana_worldsim.r6.topology_process_registry import (
    EventQueryStatus,
    FirstSegmentStatus,
    FIRST_SEGMENT_REGISTRY,
    RIFT_ACTIVATION_HORIZON_YEARS,
    registry_as_dict,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r6_b6i_first_segment_topology_model_extension"
REPORT = ROOT / "docs/arcana/B6I_FIRST_SEGMENT_TOPOLOGY_MODEL_EXTENSION.md"
STAGES = {
    "B5": ("outputs/r6_b5_plate_support_topology_qualification", "B5_ARTIFACT_MANIFEST.json"),
    "B6A": ("outputs/r6_b6a_positive_duration_authority", "B6A_ARTIFACT_MANIFEST.json"),
    "B6D": ("outputs/r6_b6d_authorial_mvp_model_freeze", "B6D_ARTIFACT_MANIFEST.json"),
    "B6E": ("outputs/r6_b6e_minimal_mvp_model_implementation", "B6E_ARTIFACT_MANIFEST.json"),
    "B6F": ("outputs/r6_b6f_event_numerical_validity", "B6F_ARTIFACT_MANIFEST.json"),
    "B6G": ("outputs/r6_b6g_targeted_validity_gap_closure", "B6G_ARTIFACT_MANIFEST.json"),
    "B6H": ("outputs/r6_b6h_topology_event_coverage_closure", "B6H_ARTIFACT_MANIFEST.json"),
}


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _verify_manifest(root: Path, rel: str, filename: str) -> dict[str, str]:
    base = root / rel
    manifest = _read(base / filename)
    result: dict[str, str] = {}
    for row in manifest["artifacts"]:
        path = (base / row["relative_path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"input manifest path escapes repository: {row['relative_path']}")
        if (not path.is_file() or path.stat().st_size != row["byte_size"]
                or _sha(path) != row["sha256"]):
            raise ValueError(f"input evidence hash mismatch: {rel}/{row['relative_path']}")
        result[path.relative_to(root.resolve()).as_posix()] = _sha(path)
    return result


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    verified: dict[str, str] = {}
    counts: dict[str, int] = {}
    for stage, (rel, manifest) in STAGES.items():
        inputs = _verify_manifest(root, rel, manifest)
        verified.update(inputs)
        counts[stage] = len(inputs)
    b6g = _read(root / STAGES["B6G"][0] / "B6G_RESULT.json")
    b6h = _read(root / STAGES["B6H"][0] / "B6H_RESULT.json")
    bound = _read(root / STAGES["B6H"][0] / "B6H_RIFT_HORIZON_INTEGRATION.json")
    b6a = _read(root / STAGES["B6A"][0] / "B6A_TOPOLOGY_TEMPORAL_BOUND.json")
    prereq_old = _read(root / STAGES["B6G"][0] / "B6G_FIRST_DT_READINESS.json")
    if b6g.get("qualification_verdict") != "PASS_B6G_TARGETED_VALIDITY_GAP_CLOSURE":
        raise ValueError("B6G closure evidence is not passing")
    if b6h.get("qualification_verdict") != "PASS_B6H_TOPOLOGY_EVENT_COVERAGE_CLOSURE":
        raise ValueError("B6H closure evidence is not passing")
    if (bound.get("event_class") != "RIFT_PROCESS_ACTIVATION"
            or bound.get("value_years") != RIFT_ACTIVATION_HORIZON_YEARS
            or bound.get("limiting_pair_id") != "1:3"
            or bound.get("integration_count") != 1
            or bound.get("topology_window_closed") is not False
            or bound.get("not_a_dt") is not True):
        raise ValueError("B6H rift horizon provenance/identity does not match B6I authority")
    if (b6a["positive_conditional_rift_activation_bound"]["elapsed_years"] != RIFT_ACTIVATION_HORIZON_YEARS
            or "plate split" not in b6a["positive_conditional_rift_activation_bound"]["does_not_bound"]):
        raise ValueError("B6A qualified rift evidence conflicts with the retained B6H bound")
    if prereq_old.get("readiness") != "NOT_READY_FOR_FIRST_DT_ADJUDICATION":
        raise ValueError("B6G historical readiness changed unexpectedly")

    registry = registry_as_dict(FIRST_SEGMENT_REGISTRY)
    enabled = [row["event_class"] for row in registry["processes"]
               if row["first_segment_status"] == FirstSegmentStatus.ENABLED.value]
    derived = [row["event_class"] for row in registry["processes"]
               if row["first_segment_status"] == FirstSegmentStatus.DERIVED_FROM_ENABLED_EVENT.value]
    out_scope = [row["event_class"] for row in registry["processes"]
                 if row["first_segment_status"] == FirstSegmentStatus.OUT_OF_SCOPE_FOR_FIRST_SEGMENT_MODEL.value]
    if enabled != ["RIFT_PROCESS_ACTIVATION"] or len(derived) != 1 or not out_scope:
        raise ValueError("B6I topology process registry failed closed scope invariants")
    if any("UNKNOWN" in row["event_class"] and row["first_segment_status"] == "ENABLED"
           for row in registry["processes"]):
        raise ValueError("unknown event class was marked enabled")

    topology_bound = {
        "status": "FIRST_SEGMENT_POSITIVE_TOPOLOGY_BOUND_QUALIFIED",
        "value": RIFT_ACTIVATION_HORIZON_YEARS,
        "unit": "year",
        "limiting_enabled_event": "RIFT_PROCESS_ACTIVATION",
        "limiting_entity_pair": "1:3",
        "authority": "B6A Census V3 governed rift guard; B6D D1; B6I authorial first-segment process scope",
        "predicate": bound["predicate"],
        "strictness": "validity interval is open at the event horizon; stop before or capture event; no accepted segment crosses it",
        "applicability": bound["applicability"],
        "model_scope_limitation": "complete only for the frozen MVP first-segment model, which generates rift activation and no independent non-rift topology mutation; not a claim of physical impossibility or general absence",
        "not_a_dt": True,
        "transition_executed": False,
    }
    prerequisites = {
        "schema": "R6_B6I_FIRST_DT_PREREQUISITES_V1",
        "positive_duration_kinematics": {"status": "CLOSED_BY_B6A_B6B", "blocking": False},
        "rigid_interior_numerical_validity": {"status": "CLOSED_BY_B6G_EXACT_RIGID_TRANSFORM", "blocking": False},
        "interface_relational_validity": {"status": b6g["interface_validity_status"], "blocking": False},
        "junction_relational_validity": {"status": b6g["junction_validity_status"], "blocking": False},
        "state_transfer_applicability": {"status": b6g["state_transfer_blocking_status"], "blocking": False},
        "system_memory_applicability": {"status": b6g["system_memory_blocking_status"], "blocking": False},
        "first_segment_topology_validity": {"status": topology_bound["status"], "blocking": False},
        "readiness": "READY_FOR_FIRST_DT_ADJUDICATION",
        "dt_selected": False,
    }
    result = {
        "schema": "R6_B6I_RESULT_V1",
        "qualification_verdict": "PASS_B6I_FIRST_SEGMENT_TOPOLOGY_MODEL_EXTENSION",
        "qualified_source_commit": head,
        "branch": branch,
        "authorial_topology_extension_status": "FROZEN_FIRST_SEGMENT_TOPOLOGY_PROCESS_SCOPE",
        "first_segment_enabled_event_classes": enabled,
        "first_segment_derived_event_classes": derived,
        "first_segment_out_of_scope_event_classes": out_scope,
        "topology_process_registry_status": "PASS_DETERMINISTIC_FAIL_CLOSED",
        "rift_event_status": "ENABLED__TOPOLOGY_TRANSITION_NOT_EXECUTED",
        "rift_event_bound_years": RIFT_ACTIVATION_HORIZON_YEARS,
        "first_segment_topology_validity_status": topology_bound["status"],
        "first_segment_topology_positive_bound_years": RIFT_ACTIVATION_HORIZON_YEARS,
        "limiting_event": "RIFT_PROCESS_ACTIVATION",
        "limiting_entity": "pair 1:3",
        "model_scope_query_semantics_status": "PASS_DISTINGUISHES_EVENT_DID_NOT_OCCUR_FROM_MODEL_SCOPE_LIMITATION",
        "future_extension_contract_status": "PASS_EXPLICIT_PROMOTION_GATES_DEFINED",
        "first_dt_prerequisite_status": "ALL_CURRENT_MVP_PREREQUISITES_CLOSED_WITHIN_FIRST_SEGMENT_SCOPE",
        "first_dt_readiness": prerequisites["readiness"],
        "next_stage_recommendation": "AUTHORIZE_FIRST_DT_ADJUDICATION",
        "production_source_changes": True,
        "execution_target": "WINDOWS",
        "ubuntu_work_required": False,
        "input_provenance": {"verified_stage_artifact_counts": counts,
                              "verified_input_artifact_count": len(verified),
                              "B6H_qualified_source_commit": b6h["qualified_source_commit"],
                              "B6H_event_horizon_integration_count": bound["integration_count"]},
        "scientific_side_effect_check": {
            "mechanics_authorized": False, "forward_evolution_authorized": False,
            "dt_selected": False, "t1_created": False, "canonical_state_changed": False,
            "canonical_node_motion_executed": False, "canonical_topology_mutated": False,
            "rift_transition_executed": False, "shellset_executed": False,
            "orbdata_mechanics_executed": False,
            "runtime_authorized": True,
            "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
        },
    }
    return {"result": result, "registry": registry, "bound": bound,
            "topology_bound": topology_bound, "prerequisites": prerequisites,
            "verified_inputs": dict(sorted(verified.items())),
            "query_semantics": {
                "schema": "R6_MODEL_SCOPE_QUERY_SEMANTICS_V1",
                "statuses": [status.value for status in EventQueryStatus],
                "rules": [
                    {"case": "enabled or derived event evaluated and absent within qualified scope", "status": "EVENT_DID_NOT_OCCUR", "claim_scope": "only the evaluated model interval"},
                    {"case": "known event class outside first-segment model scope", "status": "MODEL_SCOPE_LIMITATION", "claim_scope": "does not assert physical impossibility or historical absence"},
                    {"case": "enabled event class has not been evaluated or observation is unavailable", "status": "UNKNOWN", "claim_scope": "no occurrence/absence claim"},
                    {"case": "unregistered/new event class", "status": "FAIL_CLOSED_ERROR", "claim_scope": "explicit model registration and qualification required"},
                ],
            },
            "extension_contract": {
                "schema": "R6_TOPOLOGY_PROCESS_EXTENSION_CONTRACT_V1",
                "promotion_requires": ["explicit model addition", "event predicate", "authority/provenance",
                                       "detector/horizon qualification where required", "regression against existing history semantics",
                                       "query/replay compatibility"],
                "no_implicit_promotion": True,
            },
            "scope_limitation": "OUT_OF_SCOPE_FOR_FIRST_SEGMENT_MODEL does not mean physically impossible, proven absent in general, or removed from future ARCANA",
            "source_commit": head,
            "verified_inputs": dict(sorted(verified.items()))}


def write(data: dict[str, Any], out: Path = OUT, report: Path = REPORT,
          test_results: dict[str, Any] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payloads = {
        "B6I_RESULT.json": data["result"],
        "B6I_AUTHORIAL_TOPOLOGY_SCOPE.json": {"model_scope": "FIRST_SEGMENT_TOPOLOGY_PROCESS_SCOPE", "initial_topology": "GOVERNED_T0_TOPOLOGY", "enabled_processes": data["result"]["first_segment_enabled_event_classes"], "derived_processes": data["result"]["first_segment_derived_event_classes"], "out_of_scope_processes": data["result"]["first_segment_out_of_scope_event_classes"], "out_of_scope_interpretation": data["scope_limitation"], "topology_hold_rule": data["registry"]["topology_hold_rule"], "authority": "B6I authorial direction at qualified source baseline"},
        "B6I_TOPOLOGY_PROCESS_REGISTRY.json": data["registry"],
        "B6I_RIFT_INTEGRATION.json": {**data["bound"], "first_segment_status": "ENABLED", "transition_executed": False, "horizon_integrated_once": True},
        "B6I_TOPOLOGY_VALIDITY_BOUND.json": data["topology_bound"],
        "B6I_MODEL_SCOPE_QUERY_SEMANTICS.json": data["query_semantics"],
        "B6I_FUTURE_EXTENSION_CONTRACT.json": data["extension_contract"],
        "B6I_FIRST_DT_PREREQUISITES.json": data["prerequisites"],
        "B6I_SOURCE_MANIFEST.json": {"source_commit": data["source_commit"], "verified_inputs": data["verified_inputs"]},
        "B6I_TEST_RESULTS.json": test_results or {"status": "NOT_RECORDED", "source_commit": data["source_commit"]},
    }
    for name, payload in payloads.items():
        (out / name).write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (out / "README.md").write_text("# B6I first-segment topology model extension\n\nThis package materializes the authorial MVP process scope: governed T0 topology is held fixed except for the already-qualified conditional rift-activation process. Non-rift topology processes are explicitly out of scope for this model segment; this is not a claim about physical impossibility or general absence. The model-relative topology validity bound is 27,123.405156307464 years for rift activation at pair 1:3. The rift transition itself, dt selection, T1, and forward evolution are not executed.\n", encoding="utf-8", newline="\n")
    artifacts = []
    for path in sorted(out.iterdir()):
        if path.name == "B6I_ARTIFACT_MANIFEST.json" or not path.is_file():
            continue
        artifacts.append({"relative_path": path.name, "byte_size": path.stat().st_size, "sha256": _sha(path), "role": "B6I qualification evidence"})
    if report.is_file():
        artifacts.append({"relative_path": "../../docs/arcana/B6I_FIRST_SEGMENT_TOPOLOGY_MODEL_EXTENSION.md", "byte_size": report.stat().st_size, "sha256": _sha(report), "role": "human closure report"})
    artifacts.sort(key=lambda item: item["relative_path"])
    (out / "B6I_ARTIFACT_MANIFEST.json").write_text(json.dumps({"schema": "R6_B6I_ARTIFACT_MANIFEST_V1", "manifest_self_hash": "OMITTED_BY_POLICY", "artifacts": artifacts}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    data = evaluate(args.root)
    write(data, args.output, args.report)
    print(json.dumps(data["result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
