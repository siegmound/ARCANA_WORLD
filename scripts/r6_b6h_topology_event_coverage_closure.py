#!/usr/bin/env python3
"""Read-only B6H topology event coverage closure for the frozen R6 MVP."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r6_b6h_topology_event_coverage_closure"
REPORT = ROOT / "docs/arcana/B6H_TOPOLOGY_EVENT_COVERAGE_CLOSURE.md"
RIFT_YEARS = 27123.405156307464
MESH_SHA = "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _verify_manifest(root: Path, rel: str, name: str) -> dict[str, str]:
    base = root / rel
    manifest = _read(base / name)
    result: dict[str, str] = {}
    for item in manifest["artifacts"]:
        path = (base / item["relative_path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"manifest path escapes repository: {item['relative_path']}")
        if (not path.is_file() or path.stat().st_size != item["byte_size"]
                or _sha(path) != item["sha256"]):
            raise ValueError(f"upstream artifact manifest mismatch: {rel}/{item['relative_path']}")
        result[path.relative_to(root.resolve()).as_posix()] = _sha(path)
    return result


def topology_delta(before: dict[str, Iterable[str]], after: dict[str, Iterable[str]]) -> dict[str, Any]:
    """Retrospective identity/incidence delta; it is not a time predictor."""
    rows = []
    for entity in sorted(set(before) | set(after)):
        old, new = set(before.get(entity, ())), set(after.get(entity, ()))
        rows.append({"entity": entity, "added": sorted(new - old), "removed": sorted(old - new)})
    return {"changed": any(row["added"] or row["removed"] for row in rows), "changes": rows}


def rift_bound_reached(elapsed_years: float, qualified_horizon_years: float = RIFT_YEARS) -> bool:
    """Compare an elapsed time with the already-qualified event-specific horizon."""
    return elapsed_years >= qualified_horizon_years


def _event_classes() -> list[dict[str, Any]]:
    return [
        {"event_class": "RIFT_PROCESS_ACTIVATION", "source_candidates": ["RIFT_ACTIVATION_BOUNDARY_BIRTH"],
         "classification": "RELEVANT_TO_CURRENT_T0", "reduction": "Rift-process activation is retained as its own event; it does not assert boundary birth.",
         "detector_status": "QUALIFIED_EXISTING_DETECTOR", "positive_horizon_status": "QUALIFIED_EVENT_SPECIFIC_BOUND"},
        {"event_class": "BOUNDARY_IDENTITY_SET_CHANGE", "source_candidates": ["BOUNDARY_DEATH", "RIFT_ACTIVATION_BOUNDARY_BIRTH"],
         "classification": "RELEVANT_TO_CURRENT_T0", "reduction": "Birth and death are the two directions of boundary identity-set change; rift activation is not equated with birth.",
         "detector_status": "CANNOT_BE_DEFINED_FROM_CURRENT_AUTHORITY", "positive_horizon_status": "UNKNOWN"},
        {"event_class": "INTERFACE_DECOMPOSITION_CHANGE", "source_candidates": ["INTERFACE_SPLIT", "INTERFACE_MERGE"],
         "classification": "RELEVANT_TO_CURRENT_T0", "reduction": "Split and merge are inverse changes to the interface relation decomposition.",
         "detector_status": "REQUIRES_EXTERNAL_MODEL", "positive_horizon_status": "UNKNOWN"},
        {"event_class": "JUNCTION_RELATION_CHANGE", "source_candidates": ["JUNCTION_BIRTH", "JUNCTION_DEATH", "JUNCTION_CONNECTIVITY_CHANGE"],
         "classification": "RELEVANT_TO_CURRENT_T0", "reduction": "Identity birth/death and incidence reassignment all alter the set-valued junction relation.",
         "detector_status": "REQUIRES_EXTERNAL_MODEL", "positive_horizon_status": "UNKNOWN"},
        {"event_class": "PLATE_SUPPORT_COMPONENT_CHANGE", "source_candidates": ["PLATE_SUPPORT_SPLIT", "PLATE_SUPPORT_MERGE"],
         "classification": "RELEVANT_TO_CURRENT_T0", "reduction": "Split/merge are support-component changes; plate creation/termination is a related identity-set change covered by the same missing transition authority.",
         "detector_status": "REQUIRES_EXTERNAL_MODEL", "positive_horizon_status": "UNKNOWN"},
        {"event_class": "RELATION_DEGENERACY_REQUIRING_TOPOLOGY_CHANGE", "source_candidates": ["RELATION_DEGENERACY_REQUIRING_TOPOLOGY_CHANGE"],
         "classification": "NOT_RELEVANT_WITHIN_FROZEN_FIRST_SEGMENT_MODEL", "reduction": "Exact plate-local rigid maps preserve internal geometry; D2/D3 relations do not require cross-side co-location. Identity/incidence changes are covered by the event classes above.",
         "detector_status": "QUALIFIED_BY_FROZEN_MVP_SEMANTICS", "positive_horizon_status": "NOT_APPLICABLE"},
        {"event_class": "OTHER_UNENUMERATED_TOPOLOGY_TRANSITION", "source_candidates": ["OTHER_GOVERNED_EVENT"],
         "classification": "INSUFFICIENT_AUTHORITY_TO_CLASSIFY", "reduction": "D1 explicitly fails closed for unknown event classes; no completeness proof exists.",
         "detector_status": "CANNOT_BE_DEFINED_FROM_CURRENT_AUTHORITY", "positive_horizon_status": "UNKNOWN"},
    ]


def _predicate_rows(classes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    descriptions = {
        "RIFT_PROCESS_ACTIVATION": ("eligible rift support and governed extension E(t)", "RIFT_INITIATION when E(t) >= theta under positive opening", "m", "Census V3 rift guard / B6A bound", True),
        "BOUNDARY_IDENTITY_SET_CHANGE": ("boundary identity set before/after", "a boundary identity is added or removed", "identity/count", "not governed", False),
        "INTERFACE_DECOMPOSITION_CHANGE": ("interface IDs and their side/incidence relations", "an interface relation is replaced by a split or merged relation set", "identity/incidence", "not governed", False),
        "JUNCTION_RELATION_CHANGE": ("junction IDs and incident plate/interface sets", "junction identity set or any governed incidence set changes", "identity/incidence", "not governed", False),
        "PLATE_SUPPORT_COMPONENT_CHANGE": ("plate identity and connected support components", "plate support component partition or plate identity set changes", "component/identity", "not governed", False),
        "RELATION_DEGENERACY_REQUIRING_TOPOLOGY_CHANGE": ("plate-local rigid geometry and D2/D3 relations", "no invalidating predicate under frozen MVP; exact rigid map preserves local geometry and cross-side coincidence is not required", "not applicable", "B6B-D3 frozen MVP", True),
        "OTHER_UNENUMERATED_TOPOLOGY_TRANSITION": ("not enumerable from current authority", "unknown D1 topology-changing transition occurs", "unknown", "D1 fail-closed policy", False),
    }
    out = []
    for row in classes:
        entities, predicate, units, authority, continuous = descriptions[row["event_class"]]
        out.append({"event_class": row["event_class"], "governed_entities": entities,
                    "input_geometry": "governed T0 topology identities/relations; no candidate future geometry materialized",
                    "input_kinematics": "B6B conditional fixed-T0 Euler rates only where a qualified guard consumes them",
                    "predicate": predicate, "units": units,
                    "event_semantics": row["reduction"], "authority": authority,
                    "continuous_in_time": continuous,
                    "first_event_horizon_computable": row["positive_horizon_status"] == "QUALIFIED_EVENT_SPECIFIC_BOUND",
                    "qualification_note": "For unsupported transitions this is only a semantic post-state delta predicate, not a pre-event detector or horizon."})
    return out


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.r6_b6e_minimal_mvp_model_implementation import adjudicate as adjudicate_b6e

    b6e = adjudicate_b6e(root, mode="regression")
    dirs = {
        "B5": ("outputs/r6_b5_plate_support_topology_qualification", "B5_ARTIFACT_MANIFEST.json"),
        "B6A": ("outputs/r6_b6a_positive_duration_authority", "B6A_ARTIFACT_MANIFEST.json"),
        "B6D": ("outputs/r6_b6d_authorial_mvp_model_freeze", "B6D_ARTIFACT_MANIFEST.json"),
        "B6E": ("outputs/r6_b6e_minimal_mvp_model_implementation", "B6E_ARTIFACT_MANIFEST.json"),
        "B6F": ("outputs/r6_b6f_event_numerical_validity", "B6F_ARTIFACT_MANIFEST.json"),
        "B6G": ("outputs/r6_b6g_targeted_validity_gap_closure", "B6G_ARTIFACT_MANIFEST.json"),
    }
    verified_inputs: dict[str, str] = {}
    input_counts = {}
    for stage, (rel, manifest) in dirs.items():
        hashes = _verify_manifest(root, rel, manifest)
        verified_inputs.update(hashes)
        input_counts[stage] = len(hashes)
    b5 = b6e["b5"]
    representation = b6e["representation"]
    b6g = _read(root / "outputs/r6_b6g_targeted_validity_gap_closure/B6G_RESULT.json")
    b6a_bound = _read(root / "outputs/r6_b6a_positive_duration_authority/B6A_TOPOLOGY_TEMPORAL_BOUND.json")
    policy = _read(root / "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_TOPOLOGY_EVENT_POLICY.json")
    mesh = b5["spatial"]["mesh"]
    interface_ids = sorted(item.interface_id for item in representation.interfaces)
    pairs = sorted({tuple(sorted((item.side_a.plate_id, item.side_b.plate_id))) for item in representation.interfaces})
    side_ids = sorted(side.side_id for item in representation.interfaces for side in (item.side_a, item.side_b))
    junctions = tuple(representation.junction_relations)
    endpoint_ids = sorted({int(node_id) for row in b5["descriptors"] for node_id in row["endpoint_node_ids"]})
    plate_ids = sorted({int(value) for values in b5["node_plates"] for value in values})
    inventory = {
        "schema": "R6_B6H_TOPOLOGY_STATE_INVENTORY_V1", "source_mesh_sha256": mesh["sha256"],
        "node_count": b6e["t0"]["node_count"], "triangle_count": b6e["t0"]["triangle_count"],
        "plate_support_count": len(plate_ids), "plate_ids": plate_ids,
        "interface_count": len(interface_ids), "unique_interface_identity_count": len(set(interface_ids)),
        "plate_local_interface_side_count": len(side_ids), "unique_plate_local_side_identity_count": len(set(side_ids)),
        "boundary_endpoint_references": sum(len(row["endpoint_node_ids"]) for row in b5["descriptors"]),
        "unique_boundary_endpoint_node_count": len(endpoint_ids),
        "distinct_adjacent_plate_pair_count": len(pairs), "adjacent_plate_pairs": [list(pair) for pair in pairs],
        "junction_relation_count": len(junctions), "junction_side_count": sum(len(item.plate_local_side_ids) for item in junctions),
        "junction_relations": [{"junction_id": item.source_junction_id,
                                "incident_plate_ids": sorted(item.incident_plate_ids),
                                "incident_interface_ids": sorted(item.incident_interface_ids),
                                "plate_local_side_count": len(item.plate_local_side_ids)}
                               for item in sorted(junctions, key=lambda value: value.source_junction_id)],
        "junction_incident_plate_degree_counts": {"3": sum(len(item.incident_plate_ids) == 3 for item in junctions)},
        "junction_incident_interface_degree_counts": {"3": sum(len(item.incident_interface_ids) == 3 for item in junctions)},
        "rift_candidates": b6a_bound["positive_conditional_rift_activation_bound"]["eligibility_counts"],
        "rift_limiting_pair": b6a_bound["positive_conditional_rift_activation_bound"]["limiting_pair_id"],
        "topology_scope": "current governed T0 identities and relations; inventory does not project future topology",
    }
    if (inventory["source_mesh_sha256"] != MESH_SHA or inventory["plate_support_count"] != 12
            or inventory["interface_count"] != 1983 or inventory["unique_interface_identity_count"] != 1983
            or inventory["plate_local_interface_side_count"] != 3966
            or inventory["unique_plate_local_side_identity_count"] != 3966
            or inventory["junction_relation_count"] != 20 or inventory["junction_side_count"] != 60
            or inventory["distinct_adjacent_plate_pair_count"] != 30):
        raise ValueError("governed B6E/B5 topology inventory does not match expected authority")
    classes = _event_classes()
    relevant = [row for row in classes if row["classification"] == "RELEVANT_TO_CURRENT_T0" or row["classification"] == "INSUFFICIENT_AUTHORITY_TO_CLASSIFY"]
    predicates = _predicate_rows(classes)
    rift = b6a_bound["positive_conditional_rift_activation_bound"]
    if (rift["status"] != "CONDITIONAL_BOUND_WITHIN_FIXED_T0_EULER_SEGMENT"
            or rift["elapsed_years"] != RIFT_YEARS or rift["limiting_pair_id"] != "1:3"
            or "plate split" not in rift["does_not_bound"] or policy["policy"] != "EVENT_DRIVEN_TOPOLOGY_HOLD"):
        raise ValueError("B6A/B6D rift or topology-hold authority changed unexpectedly")
    unsupported = [row["event_class"] for row in relevant if row["event_class"] != "RIFT_PROCESS_ACTIVATION"]
    coverage = []
    for row in classes:
        is_rift = row["event_class"] == "RIFT_PROCESS_ACTIVATION"
        excluded = row["classification"] == "NOT_RELEVANT_WITHIN_FROZEN_FIRST_SEGMENT_MODEL"
        coverage.append({"event_class": row["event_class"], "relevance": row["classification"],
                         "detector_status": row["detector_status"],
                         "positive_bound_status": row["positive_horizon_status"],
                         "positive_horizon_years": RIFT_YEARS if is_rift else None,
                         "coverage_scope": "eligible rift-process activation only" if is_rift else ("excluded by frozen MVP semantics" if excluded else "no predictive detector or interval proof"),
                         "remaining_unknown": None if is_rift or excluded else "event eligibility/transition rule and first-event horizon are not governed"})
    event_coverage = "PARTIAL_EVENT_COVERAGE_ONLY"
    readiness = "TOPOLOGY_MODEL_EXTENSION_REQUIRED"
    result = {
        "schema": "R6_B6H_RESULT_V1", "qualification_verdict": "PASS_B6H_TOPOLOGY_EVENT_COVERAGE_CLOSURE",
        "qualified_source_commit": head, "branch": branch,
        "topology_event_class_count": len(classes), "relevant_topology_event_classes": [row["event_class"] for row in relevant],
        "event_predicate_status": "EXPLICIT_FOR_RIFT_AND_RETROSPECTIVE_IDENTITY_DELTAS__NO_PREDICTIVE_PREDICATE_FOR_UNGOVERNED_TRANSITIONS",
        "event_detector_status": "RIFT_GUARD_QUALIFIED__OTHER_RELEVANT_TOPOLOGY_TRANSITIONS_REQUIRE_MODEL_AUTHORITY",
        "rift_event_bound_status": "QUALIFIED_EVENT_SPECIFIC_BOUND_NOT_TOPOLOGY_WINDOW",
        "rift_event_bound_years": RIFT_YEARS,
        "topology_event_coverage_status": event_coverage,
        "composite_topology_window_status": "NOT_COMPUTED_INCOMPLETE_EVENT_COVERAGE",
        "composite_topology_positive_bound_years": None, "limiting_topology_event": None, "limiting_entity": None,
        "remaining_topology_unknowns": unsupported,
        "first_dt_prerequisite_status": "BLOCKING_UNKNOWN_TOPOLOGY_EVENT_COVERAGE",
        "first_dt_readiness": readiness, "next_stage_recommendation": "AUTHORIZE_TARGETED_TOPOLOGY_MODEL_EXTENSION",
        "execution_target": "WINDOWS", "ubuntu_work_required": False,
        "production_source_changes": False,
        "scientific_side_effect_check": {"mechanics_authorized": False, "forward_evolution_authorized": False,
            "dt_selected": False, "t1_created": False, "canonical_state_changed": False,
            "canonical_node_motion_executed": False, "canonical_topology_mutated": False,
            "shellset_executed": False, "orbdata_mechanics_executed": False,
            "runtime_authorized": True, "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE"},
        "input_provenance": {"verified_stage_artifact_counts": input_counts, "verified_input_artifact_count": len(verified_inputs),
            "B6G_historical_source_commit": b6g["qualified_source_commit"],
            "canonical_mesh_sha256": inventory["source_mesh_sha256"]},
    }
    return {"result": result, "inventory": inventory, "classes": classes, "relevant": relevant,
            "predicates": predicates, "coverage": coverage, "rift": rift,
            "unknown": {"status": "MODEL_REQUIRED", "items": unsupported,
                        "minimum_missing_authority": "governed event eligibility, transition semantics/identity maps, and conservative first-event timing or positive interval exclusion for topology-changing classes"},
            "verified_inputs": dict(sorted(verified_inputs.items())),
            "event_delta_contract": "retrospective identity/incidence differences only; no future geometry or predictive horizon",
            "policy": policy, "b6g": b6g}


def write(data: dict[str, Any], out: Path = OUT, report: Path = REPORT,
          test_results: dict[str, Any] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    result = data["result"]
    payloads = {
        "B6H_RESULT.json": result,
        "B6H_TOPOLOGY_STATE_INVENTORY.json": data["inventory"],
        "B6H_EVENT_CLASS_MINIMIZATION.json": {"classes": data["classes"], "count": len(data["classes"]), "relevant_classes": result["relevant_topology_event_classes"]},
        "B6H_EVENT_PREDICATES.json": {"predicates": data["predicates"], "event_delta_contract": data["event_delta_contract"]},
        "B6H_DETECTOR_STATUS.json": {"classes": [{"event_class": row["event_class"], "detector_status": row["detector_status"]} for row in data["classes"]]},
        "B6H_EVENT_HORIZONS.json": {"event_specific_horizons": [{"event_class": "RIFT_PROCESS_ACTIVATION", "value": RIFT_YEARS, "unit": "year", "limiting_entity": "rift candidate pair 1:3", "strictness": "stop before/capture event; no accepted interval crosses it", "authority": "B6A Census V3 rift guard; B6D D1", "numeric_tolerance": "inherited from qualified B6A guard; B6H adds no threshold or tolerance", "uncertainty": "conditional on fixed-T0 Euler segment and eligible rift support; not re-estimated"}], "unsupported_class_horizons": "UNKNOWN"},
        "B6H_EVENT_COVERAGE_TABLE.json": {"status": result["topology_event_coverage_status"], "coverage": data["coverage"], "absence_of_detector_means_absence": False},
        "B6H_RIFT_HORIZON_INTEGRATION.json": {"integration_count": 1, "event_class": "RIFT_PROCESS_ACTIVATION", "value_years": RIFT_YEARS, "applicability": data["rift"]["validity_scope"], "scope": "eligible rift activation only; not boundary birth, plate split, or global topology bound", "predicate": data["rift"]["event_semantics"], "limiting_pair_id": data["rift"]["limiting_pair_id"], "threshold_lower_bound_m": data["rift"]["threshold_lower_bound_m"], "maximum_local_opening_velocity_m_per_year": data["rift"]["maximum_local_opening_velocity_m_per_year"], "strictness": "stop before/capture the event; no accepted interval crosses it", "authority": "B6A Census V3 guard / B6D D1", "topology_window_closed": False, "not_a_dt": True},
        "B6H_COMPOSITE_TOPOLOGY_WINDOW.json": {"status": result["composite_topology_window_status"], "value": None, "reason": "relevant event classes lack authority and positive interval proofs; no composite minimum is valid"},
        "B6H_REMAINING_UNKNOWN.json": data["unknown"],
        "B6H_FIRST_DT_PREREQUISITES.json": {"status": result["first_dt_prerequisite_status"], "readiness": result["first_dt_readiness"], "dt_selected": False, "blocking_classes": result["remaining_topology_unknowns"]},
        "B6H_EXECUTION_PLAN.json": {"execution_target": "WINDOWS", "ubuntu_work_required": False, "reason": "qualification uses existing small static topology evidence and a prequalified event-specific bound; no exhaustive supported detector calculation exists or can be justified without new authority"},
        "B6H_TEST_RESULTS.json": test_results or {"status": "NOT_RECORDED", "source_commit": result["qualified_source_commit"]},
        "B6H_SOURCE_MANIFEST.json": {"source_commit": result["qualified_source_commit"], "inputs": data["verified_inputs"]},
    }
    for filename, payload in payloads.items():
        (out / filename).write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (out / "README.md").write_text("# B6H topology event coverage closure\n\nB6H re-derives the governed T0 topology and closes the audit by minimizing event classes and recording the exact remaining authority gap. The conditional 27,123.405156-year rift activation horizon is integrated once and remains event-specific. Other topology-changing events are not predicted or excluded, so no composite topology window or dt is produced. No canonical state is modified.\n", encoding="utf-8", newline="\n")
    artifacts = []
    for path in sorted(out.iterdir()):
        if path.name == "B6H_ARTIFACT_MANIFEST.json" or not path.is_file():
            continue
        artifacts.append({"relative_path": path.name, "byte_size": path.stat().st_size, "sha256": _sha(path), "role": "B6H qualification evidence"})
    if report.is_file():
        artifacts.append({"relative_path": "../../docs/arcana/B6H_TOPOLOGY_EVENT_COVERAGE_CLOSURE.md", "byte_size": report.stat().st_size, "sha256": _sha(report), "role": "human closure report"})
    artifacts.sort(key=lambda row: row["relative_path"])
    (out / "B6H_ARTIFACT_MANIFEST.json").write_text(json.dumps({"schema": "R6_B6H_ARTIFACT_MANIFEST_V1", "manifest_self_hash": "OMITTED_BY_POLICY", "artifacts": artifacts}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


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
