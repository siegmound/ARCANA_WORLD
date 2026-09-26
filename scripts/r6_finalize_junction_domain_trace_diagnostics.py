"""Finalize bounded domain/trace status reports from the existing t0 matrix.

This utility does not rerun geometry, evolve the world, or treat proposed
search radii as evaluated results. It corrects diagnostic semantics only.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from arcana_worldsim.r6.physical.junction_patch import (
    classify_trace_reach, deterministic_domain_radii,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    resolve_external_payload_path, verify_protected_staged_blobs)
EXPECTED_HEAD = "592b1651b405363373590092e133bd25569d99a5"
INDEX = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
PARENT_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write_json(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, sort_keys=True, indent=2,
                                        allow_nan=False) + "\n", encoding="utf-8",
                              newline="\n")


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()
    origin = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT,
                                     text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT,
                                     text=True).strip()
    context = require_repository_context(ROOT, required_ancestor=EXPECTED_HEAD,
                                         expected_refs={"origin/main": EXPECTED_HEAD})
    verify_protected_staged_blobs(ROOT, INDEX)
    parent = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    parent_path = resolve_external_payload_path(ROOT, parent["payload"]["path"])
    parent_hash = hashlib.sha256(parent_path.read_bytes()).hexdigest()
    if parent_hash != PARENT_SHA:
        raise RuntimeError("canonical vector parent hash mismatch")

    membership = read_json("R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.json")
    boundary = read_json("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
    known_junction_ids = {j["junction_id"] for j in boundary["junctions"]}
    rows = []
    width_stats = []
    for case in membership["width_cases"]:
        trace_counts = {key: 0 for key in ("TRACE_PASS", "TRACE_FAIL", "TRACE_NOT_REACHED")}
        attempted = []
        for row in case["junctions"]:
            stable = row.get("topology_status") == "PASS_THREE_PORT_TOPOLOGY"
            if not stable:
                trace_status, trace_class = "TRACE_NOT_REACHED", "TOPOLOGY_NOT_STABLE_THREE_PORT"
                did_attempt = False
            else:
                trace_status, trace_class = classify_trace_reach(
                    row.get("status", "INVALID"), row.get("reason"),
                    True if row.get("status") == "BOUND" and row.get("trace_pass") is True
                    else (False if "corridor trace tolerance unmet" in str(row.get("reason", "")).lower()
                          else None),
                )
                did_attempt = trace_status != "TRACE_NOT_REACHED"
            trace_counts[trace_status] += 1
            limits = [x.get("distance_m") for x in row.get("topological_limit_per_branch", [])]
            bounded = len(limits) == 3 and all(v is not None and math.isfinite(float(v)) and float(v) > 0
                                                 for v in limits)
            nearest = min(map(float, limits)) if bounded else None
            width = float(case["W_model_m"])
            if row.get("topology_status") == "LOCAL_DOMAIN_EXCEEDS_TOPOLOGICAL_LIMIT":
                domain_status = "INVALID_PRIOR_EVALUATION_BEYOND_TOPOLOGICAL_LIMIT"
            elif row.get("topology_status") == "LOCAL_DOMAIN_LIMIT_REACHED":
                domain_status = "DOMAIN_EXPANSION_REQUIRED"
            elif row.get("topology_status") == "TOPOLOGY_NOT_CONVERGED":
                domain_status = "BRANCH_SCAN_NOT_CONVERGED"
            elif row.get("topology_status") == "MULTIPLE_PORT_COMPONENTS":
                domain_status = "MULTIPLE_PORT_COMPONENTS_REQUIRES_REFINEMENT"
            else:
                domain_status = "INITIAL_DOMAIN_TOPOLOGY_STABLE_EXPANSION_NOT_REQUIRED_BY_PRIOR_RESULT"
            radii = (list(deterministic_domain_radii(width, nearest, max_level=4))
                     if bounded else [])
            row["trace_status"] = trace_status
            row["trace_classification"] = trace_class
            row["trace_attempted"] = did_attempt
            row["domain_reassessment"] = {
                "status": domain_status,
                "canonical_expansion_executed": False,
                "initial_search_radius_m": width,
                "next_junction_hard_limit_m": nearest,
                "bounded_dyadic_search_schedule_m": radii,
                "schedule_is_evaluated_evidence": False,
                "prior_evaluation_crossed_hard_limit":
                    row.get("topology_status") == "LOCAL_DOMAIN_EXCEEDS_TOPOLOGICAL_LIMIT",
            }
            trace_record = {
                "W_model_m": case["W_model_m"],
                "junction_id": row["junction_id"],
                "topology_status": row.get("topology_status"),
                "trace_status": trace_status,
                "trace_classification": trace_class,
                "trace_attempted": did_attempt,
                "reason": row.get("reason"),
                "maximum_error": None,
                "refinement_iterations": None,
                "endpoint_dirichlet_check": "NOT_REACHED" if not did_attempt else "FAILED_AT_TRACE_REFINEMENT",
                "same_physical_spherical_points": "NOT_REACHED",
                "port_orientation_invariance": "NOT_EVALUATED",
                "triangulation": "NOT_REACHED",
            }
            residual = re.search(r"residual=([0-9.eE+-]+)", str(row.get("reason", "")))
            edge_scale = re.search(r"smallest edge scale=([0-9.eE+-]+) m", str(row.get("reason", "")))
            depth = re.search(r"at depth ([0-9]+)", str(row.get("reason", "")))
            if residual:
                trace_record["maximum_error"] = float(residual.group(1))
                trace_record["refinement_iterations"] = int(depth.group(1)) if depth else None
                trace_record["minimum_edge_length_m"] = float(edge_scale.group(1)) if edge_scale else None
            rows.append(trace_record)
            if did_attempt:
                attempted.append(trace_record)
        case["trace_status_counts"] = trace_counts
        case["trace_attempted"] = trace_counts["TRACE_PASS"] + trace_counts["TRACE_FAIL"]
        case["trace_pass"] = trace_counts["TRACE_PASS"]
        case["trace_fail"] = trace_counts["TRACE_FAIL"]
        case["trace_not_reached"] = trace_counts["TRACE_NOT_REACHED"]
        case["triangulation_pass"] = sum(
            r.get("triangle_count", 0) > 0 and r.get("status") == "BOUND"
            for r in case["junctions"])
        case["domain_expansion_executed"] = False
        width_stats.append({
            "W_model_m": case["W_model_m"],
            "central_patch": sum(bool(r.get("central_patch_connected")) for r in case["junctions"]),
            "all_singleton_presence": sum(all((r.get("singleton_corridor_found") or {}).values())
                                           for r in case["junctions"]),
            "stable_three_port_topology": sum(r.get("topology_status") == "PASS_THREE_PORT_TOPOLOGY"
                                                for r in case["junctions"]),
            "trace_attempted": case["trace_attempted"],
            "trace_pass": case["trace_pass"],
            "trace_fail": case["trace_fail"],
            "trace_not_reached": case["trace_not_reached"],
            "triangulation_pass": case["triangulation_pass"],
            "local_velocity_pass": 0,
            "domain_expansion_executed": False,
            "global_L0_L1_executed": False,
        })

    membership.update({
        "schema": "R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS_V2",
        "decision": "CANONICAL_DOMAIN_EXPANSION_AND_TRACE_REASSESSMENT_REQUIRED",
        "domain_expansion_policy": {
            "schedule": "R0, 2R0, 4R0, 8R0, 16R0; R0=W",
            "max_level": 4,
            "hard_stop": "strictly_before_nearest_next_canonical_junction_on_each_of_three_branches",
            "schedule_values_are_evaluated": False,
            "canonical_expansion_executed": False,
        },
        "per_branch_topological_limit": "nearest graph distance to next governed junction; rows retain exact values",
        "legacy_over_limit_results": "INVALID_FOR_LOCAL_TOPOLOGY_EVIDENCE_AND_REQUIRE_BOUNDED_RERUN",
        "branch_outward_persistence_scan": "NOT_EXECUTED; no canonical per-arc mask samples are present in the prior matrix",
        "trace_status_semantics": "TRACE_NOT_REACHED is distinct from an evaluated TRACE_FAIL",
        "width_cases": membership["width_cases"],
        "canonical_width_selected": False,
        "canonical_reference_map_materialized": False,
        "forward_evolution": False,
    })
    write_json("R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.json", membership)
    by_artifact = {
        "R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS": {
            "artifact": "R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS",
            "schema": "R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS_V1",
            "repository": context.to_dict(),
            "parent_vector_payload_sha256": parent_hash,
            "trace_tolerance": 1e-4,
            "cases": rows,
            "attempted_trace_count": sum(r["trace_attempted"] for r in rows),
            "trace_pass_count": sum(r["trace_status"] == "TRACE_PASS" for r in rows),
            "trace_fail_count": sum(r["trace_status"] == "TRACE_FAIL" for r in rows),
            "trace_not_reached_count": sum(r["trace_status"] == "TRACE_NOT_REACHED" for r in rows),
            "interpretation": "Existing runner reaches corner compatibility and adaptive residual checks inside build_junction_patch; most stable topologies stop before trace evaluation. Only an explicit adaptive residual exceedance is recorded as TRACE_FAIL.",
            "all_attempted_trace_calls_represented": True,
            "triangulation_after_three_trace_passes": "NOT_REACHED_FOR_ANY_CASE",
            "static_velocity_validation": "NOT_REACHED",
            "forward_evolution": False,
        }
    }
    write_json("R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS.json",
               by_artifact["R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS"])
    trace = by_artifact["R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS"]
    (ROOT / "R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS.md").write_text(
        "# Canonical junction trace convergence diagnostics\n\n"
        f"Prior matrix rows classified: {len(rows)}. Trace attempted: {trace['attempted_trace_count']}; "
        f"pass: {trace['trace_pass_count']}; fail: {trace['trace_fail_count']}; "
        f"not reached: {trace['trace_not_reached_count']}.\n\n"
        "These are classifications of the existing t0 execution, not a new trace run. "
        "A corner Dirichlet conflict or invalid port association occurs before adaptive trace evaluation and is not mislabeled as TRACE_FAIL. No triangulation or velocity field is accepted.\n",
        encoding="utf-8", newline="\n")

    common_names = ["R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json",
                    "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS.json",
                    "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX.json"]
    for name in common_names:
        artifact = read_json(name)
        artifact["decision"] = "CANONICAL_DOMAIN_EXPANSION_AND_TRACE_REASSESSMENT_REQUIRED"
        artifact["domain_expansion"] = "IMPLEMENTED_SEARCH_POLICY__CANONICAL_EXPANSION_NOT_EXECUTED"
        artifact["trace_status_semantics"] = "TRACE_PASS_TRACE_FAIL_TRACE_NOT_REACHED"
        artifact["per_width_trace_pipeline"] = width_stats
        if "cases" in artifact:
            artifact["cases"] = membership["width_cases"]
        artifact["canonical_width_selected"] = False
        artifact["canonical_map_materialized"] = False
        artifact["forward_evolution"] = False
        write_json(name, artifact)
        md_name = name[:-5] + ".md"
        md_path = ROOT / md_name
        if md_path.exists():
            md_path.write_text(
                md_path.read_text(encoding="utf-8") +
                "\n\n## Domain and trace status correction\n\n"
                "The existing fixed-radius results have not been rerun under domain expansion. "
                "The dyadic search schedule is bounded by the next canonical junction and is recorded as a policy, not evaluated evidence. "
                "Trace outcomes distinguish actual residual failure from pre-trace construction blockers.\n",
                encoding="utf-8", newline="\n")

    readiness = {
        "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V18",
        "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V18",
        "decision": "JUNCTION_DOMAIN_EXPANSION_AND_TRACE_CONVERGENCE_NOT_ESTABLISHED",
        "verdict": "PASS_DIAGNOSTIC_RECLASSIFICATION__CANONICAL_DOMAIN_AND_TRACE_RERUN_REQUIRED",
        "repository": context.to_dict(),
        "parent_vector_payload_sha256": parent_hash,
        "membership_topology_reused": True,
        "normal_based_port_identity_retired": True,
        "domain_expansion_policy_bound": True,
        "domain_expansion_canonical_cases_executed": False,
        "topological_limits_enforced_in_new_evaluation": False,
        "branch_singleton_persistence_scans_executed": False,
        "trace_status_counts": {
            key: sum(r["trace_status"] == key for r in rows)
            for key in ("TRACE_PASS", "TRACE_FAIL", "TRACE_NOT_REACHED")
        },
        "per_width_pipeline": width_stats,
        "global_L0_L1_executed": False,
        "canonical_width_selected": False,
        "canonical_map_materialized": False,
        "forward_evolution": False,
        "first_dt_years": None,
        "next_action": "R6_JUNCTION_PATCH_BOUNDED_DOMAIN_EXPANSION_AND_CANONICAL_BRANCH_TRACE_RERUN",
        "protected_staged_blobs": INDEX,
    }
    write_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V18.json", readiness)
    (ROOT / "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V18.md").write_text(
        "# First physical interval readiness V18\n\n"
        "The current t0 diagnostic has been classified without claiming new geometric evaluations. "
        "Domain expansion policy and hard-limit semantics are now explicit, but canonical expansion, "
        "branch persistence, full trace convergence, triangulation, and static velocity gates remain unexecuted. "
        "First dt remains unbound; no world evolution occurred.\n",
        encoding="utf-8", newline="\n")
    md_lines = [
        "# Canonical junction membership topology diagnostics", "",
        f"Decision: `{membership['decision']}`. Matrix rows retained: {sum(len(c['junctions']) for c in membership['width_cases'])}.",
        "Normal-based port identity is retired; membership topology remains the source of port identity.",
        "The deterministic dyadic domain schedule is bounded strictly before the nearest next canonical junction. The listed schedule is not evaluated evidence; the old beyond-limit rows remain invalid pending bounded rerun.",
        "Branch-outward singleton persistence and canonical expanded-domain reevaluation were not executed in this handoff.",
        "",
    ]
    for stat in width_stats:
        md_lines.extend([
            f"## W = {stat['W_model_m']} m", "",
            f"Central patch {stat['central_patch']}/20; singleton presence {stat['all_singleton_presence']}/20; stable three-port topology {stat['stable_three_port_topology']}/20.",
            f"Trace attempted {stat['trace_attempted']}/20; pass {stat['trace_pass']}/20; fail {stat['trace_fail']}/20; not reached {stat['trace_not_reached']}/20; triangulation {stat['triangulation_pass']}/20.",
            "",
        ])
    (ROOT / "R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.md").write_text(
        "\n".join(md_lines), encoding="utf-8", newline="\n")
    print(json.dumps({"decision": readiness["decision"],
                      "trace_status_counts": readiness["trace_status_counts"],
                      "per_width": width_stats,
                      "parent_hash": parent_hash,
                      "protected_staged_blobs": INDEX}, indent=2))


if __name__ == "__main__":
    main()
