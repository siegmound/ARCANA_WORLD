#!/usr/bin/env python3
"""Read-only R6 B6G relational validity and first-step gap qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r6_b6g_targeted_validity_gap_closure"
REPORT = ROOT / "docs/arcana/B6G_TARGETED_VALIDITY_GAP_CLOSURE.md"


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _verify_manifest(root: Path, relative: str, manifest_name: str) -> dict[str, str]:
    base = root / relative
    manifest = _read(base / manifest_name)
    verified = {}
    for row in manifest["artifacts"]:
        path = (base / row["relative_path"]).resolve()
        if not path.is_file() or path.stat().st_size != row["byte_size"] or _sha(path) != row["sha256"]:
            raise ValueError(f"upstream artifact manifest mismatch: {relative}/{row['relative_path']}")
        verified[path.relative_to(root).as_posix()] = _sha(path)
    return verified


def _relational_audit(representation, b5: dict[str, Any]) -> dict[str, Any]:
    descriptors = {str(row["boundary_id"]): row for row in b5["descriptors"]}
    interfaces = tuple(representation.interfaces)
    interface_ids = [row.interface_id for row in interfaces]
    source_ids = [row.source_boundary_id for row in interfaces]
    side_ids = [side.side_id for row in interfaces for side in (row.side_a, row.side_b)]
    interface_failures = []
    if len(interfaces) != 1983 or set(source_ids) != set(descriptors) or len(set(source_ids)) != 1983:
        interface_failures.append("interface/source-boundary identity inventory mismatch")
    if len(set(interface_ids)) != 1983 or len(set(side_ids)) != 3966:
        interface_failures.append("duplicate interface or plate-local side identity")
    for row in interfaces:
        desc = descriptors.get(row.source_boundary_id)
        if desc is None:
            interface_failures.append(f"unresolved source boundary {row.source_boundary_id}")
            continue
        pair = tuple(map(int, desc["adjacent_plate_ids"]))
        endpoints = tuple(map(int, desc["endpoint_node_ids"]))
        actual_pair = (row.side_a.plate_id, row.side_b.plate_id)
        actual_endpoints = tuple(row.side_a.source_endpoint_node_ids)
        if (row.side_a.side_id == row.side_b.side_id or actual_pair != pair
                or actual_endpoints != endpoints
                or tuple(row.side_b.source_endpoint_node_ids) != endpoints
                or row.side_a.source_boundary_id != row.source_boundary_id
                or row.side_b.source_boundary_id != row.source_boundary_id
                or row.topological_relation != "T0_SHARED_EDGE__PLATE_LOCAL_SIDES_DISTINCT"):
            interface_failures.append(f"relational side invariant failed: {row.source_boundary_id}")

    junctions = tuple(representation.junction_relations)
    junction_rows = {str(row["junction_id"]): row for row in b5["junctions"]}
    incidence_by_node: dict[int, set[str]] = {}
    for boundary_id, desc in descriptors.items():
        for node_id in map(int, desc["endpoint_node_ids"]):
            incidence_by_node.setdefault(node_id, set()).add(boundary_id)
    relation_ids = [row.relation_id for row in junctions]
    junction_source_ids = [row.source_junction_id for row in junctions]
    junction_nodes = [row.source_node_id for row in junctions]
    junction_failures = []
    if len(junctions) != 20 or len(set(relation_ids)) != 20 or len(set(junction_source_ids)) != 20 or len(set(junction_nodes)) != 20:
        junction_failures.append("junction/relation/node identity inventory mismatch")
    for row in junctions:
        source = junction_rows.get(row.source_junction_id)
        expected_interfaces = tuple(sorted(incidence_by_node.get(row.source_node_id, set())))
        expected_plates = tuple(sorted(map(int, source["incident_plate_ids"]))) if source else ()
        if (source is None or len(row.incident_plate_ids) != 3
                or row.incident_plate_ids != expected_plates
                or row.incident_interface_ids != expected_interfaces
                or len(row.incident_interface_ids) != 3
                or len(row.plate_local_side_ids) != 3
                or len(set(row.plate_local_side_ids)) != 3
                or row.unique_plate_owner is not None):
            junction_failures.append(f"set-valued incidence invariant failed: {row.source_junction_id}")

    return {
        "interface_count": len(interfaces), "unique_interface_id_count": len(set(interface_ids)),
        "unique_plate_local_side_id_count": len(set(side_ids)), "interface_identity_pairing_failures": interface_failures,
        "interface_structural_identity_pass": not interface_failures,
        "junction_relation_count": len(junctions), "unique_junction_identity_count": len(set(junction_source_ids)),
        "junction_incidence_failures": junction_failures, "junction_structural_incidence_pass": not junction_failures,
        "geometric_co_location_required": False,
        "physical_accommodation": "UNKNOWN_PRESERVED",
        "position_residual_or_velocity_allocation": "NOT_DEFINED_OR_REQUIRED_BY_FROZEN_RELATIONAL_SEMANTICS",
        "candidate_geometry_or_canonical_state_written": False,
    }


def _event_coverage() -> list[dict[str, Any]]:
    return [
        {"event_class": "conditional rift-process activation", "status": "QUALIFIED_DETECTOR", "can_be_relevant": True,
         "positive_horizon_years": 27123.405156307464, "can_be_excluded_until_horizon": True,
         "scope": "eligible rift support under fixed T0 Euler rates; activation is not boundary birth or plate split"},
        {"event_class": "plate split / merge / creation / termination", "status": "CANNOT_EXCLUDE", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "no governed event law, transition map, or detector"},
        {"event_class": "boundary birth / death", "status": "MODEL_REQUIRED", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "rift guard only detects process activation; no boundary transition semantics"},
        {"event_class": "interface split / merge", "status": "IMPLEMENTATION_REQUIRED", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "no relation-graph transition detector or transition authority"},
        {"event_class": "junction birth / death", "status": "CANNOT_EXCLUDE", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "no event law or junction identity transition detector"},
        {"event_class": "junction connectivity change / reassignment", "status": "CANNOT_EXCLUDE", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "current incidence is known; no future transition semantics or detector"},
        {"event_class": "plate support split / merge", "status": "CANNOT_EXCLUDE", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "rigid transform itself is bijective, but physical/topology transition law is absent"},
        {"event_class": "plate-local side geometric degeneration", "status": "DERIVABLE_DETECTOR", "can_be_relevant": False,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": True,
         "scope": "exact rigid rotation preserves each nonzero side length, endpoint distinction and orientation"},
        {"event_class": "cross-side gap / overlap / projected crossing", "status": "NOT_RELEVANT_TO_CURRENT_T0", "can_be_relevant": False,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": True,
         "scope": "not an invalidation of D2/D3 identity relations; physical interpretation remains outside MVP"},
        {"event_class": "other unenumerated topology transition", "status": "CANNOT_EXCLUDE", "can_be_relevant": True,
         "positive_horizon_years": None, "can_be_excluded_until_horizon": False,
         "scope": "D1 explicitly fails closed for unknown event classes"},
    ]


def _classify_state_transfers(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes = {
        "FEG/ShellSet runtime fields": ("DERIVED_RECOMPUTABLE", "No mechanics/runtime consumer is required by D7; recompute only if later selected."),
        "bathymetry": ("ASYNC_RETAINS_LATEST_VALID_STATE", "D6 independent domain clock; preserve its last valid T0 value."),
        "boundary_classification": ("QUERY_LIMITATION_ONLY", "UNKNOWN remains UNKNOWN; no boundary type is needed for kinematic relation identity."),
        "climate": ("ASYNC_RETAINS_LATEST_VALID_STATE", "D6 retains latest valid climate state; tectonic step does not advance climate."),
        "deep": ("ASYNC_RETAINS_LATEST_VALID_STATE", "D6 independent domain clock; no deep-domain execution in MVP."),
        "hydrology": ("ASYNC_RETAINS_LATEST_VALID_STATE", "D6 retains latest valid hydrology state."),
        "junction_physical_semantics": ("QUERY_LIMITATION_ONLY", "Physical accommodation remains UNKNOWN; structural junction incidence is retained."),
        "land_ocean": ("ASYNC_RETAINS_LATEST_VALID_STATE", "D6 independent domain clock; no land/ocean transition is authorized."),
        "physical_geography": ("ASYNC_RETAINS_LATEST_VALID_STATE", "B6E explicitly keeps tectonic-only clock at T0 absent a field model; D6 exposes age."),
        "plate_kinematics": ("REFERENCE_ONLY", "Retain governed Euler forcing identity; the vector itself is not a transferred state."),
        "province_state": ("ASYNC_RETAINS_LATEST_VALID_STATE", "D6 independent domain clock; preserve existing value and validity time."),
        "tectonic_kinematics_grid": ("QUERY_LIMITATION_ONLY", "No grid field is materialized; velocities remain derivable on supported plate-local geometry."),
        "tectonic_plate_partition": ("REFERENCE_ONLY", "D1 holds topology between events; retain identity/incidence with no reindex absent event."),
        "topography": ("ASYNC_RETAINS_LATEST_VALID_STATE", "B6E declares independent domain clock; do not fabricate an updated field."),
        "weak_zone_state": ("QUERY_LIMITATION_ONLY", "Support is absent and no mechanics consumes it in the frozen MVP."),
    }
    rows = []
    for item in declarations:
        family = item["state_family"]
        status, reason = classes[family]
        rows.append({"state_family": family, "declared_transfer_class": item["transfer_class"],
            "first_step_classification": status, "first_step_update_required": False,
            "latest_valid_state_retained": status == "ASYNC_RETAINS_LATEST_VALID_STATE",
            "existing_temporal_behavior": item["temporal_validity_behavior"], "reason": reason,
            "missing_authority_behavior": item["missing_authority_behavior"]})
    return rows


def _interface_kinematics(descriptors: list[dict[str, Any]]) -> dict[str, Any]:
    normal, tangent, missing = [], [], 0
    conventions = set()
    for row in descriptors:
        descriptor = row.get("kinematic_descriptor", {})
        conventions.add(descriptor.get("normal_convention", "UNKNOWN"))
        n = descriptor.get("relative_normal_velocity_m_per_year")
        t = descriptor.get("relative_tangential_velocity_m_per_year")
        if n is None or t is None:
            missing += 1
            continue
        normal.append(float(n))
        tangent.append(float(t))
    return {
        "interface_count": len(descriptors), "decomposed_count": len(normal), "missing_component_count": missing,
        "normal_velocity_units": "m/year", "tangential_velocity_units": "m/year",
        "normal_sign_convention": sorted(conventions),
        "normal_component_counts": {"opening_positive": sum(value > 0 for value in normal),
            "closing_negative": sum(value < 0 for value in normal), "exactly_zero": sum(value == 0 for value in normal)},
        "tangential_nonzero_count": sum(value != 0 for value in tangent),
        "maximum_absolute_normal_velocity_m_per_year": max(map(abs, normal), default=None),
        "maximum_absolute_tangential_velocity_m_per_year": max(map(abs, tangent), default=None),
        "interpretation": "KINEMATIC_DISCONTINUITY_ONLY__NO_SHARED_VELOCITY_OR_PHYSICAL_ACCOMMODATION",
        "normal_separation_semantics": "Separation does not erase relational interface identity under D2; physical gap response or a topology transition requires separate governed event/model authority.",
    }


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.r6_b6e_minimal_mvp_model_implementation import adjudicate as adjudicate_b6e
    b6e = adjudicate_b6e(root, mode="regression")
    b6e_result = _read(root / "outputs/r6_b6e_minimal_mvp_model_implementation/B6E_RESULT.json")
    b6f_dir = "outputs/r6_b6f_event_numerical_validity"
    manifests = {}
    for rel, name in [
        ("outputs/r6_b5_plate_support_topology_qualification", "B5_ARTIFACT_MANIFEST.json"),
        ("outputs/r6_b6d_authorial_mvp_model_freeze", "B6D_ARTIFACT_MANIFEST.json"),
        ("outputs/r6_b6e_minimal_mvp_model_implementation", "B6E_ARTIFACT_MANIFEST.json"),
        (b6f_dir, "B6F_ARTIFACT_MANIFEST.json")]:
        manifests.update(_verify_manifest(root, rel, name))
    b6f = _read(root / b6f_dir / "B6F_RESULT.json")
    if b6e_result.get("decision") != "PASS_B6E_MINIMAL_MVP_FIRST_STEP_MODEL_IMPLEMENTATION":
        raise ValueError("B6E input is not a passing governed materialization")
    if b6f.get("qualification_verdict") != "PASS_B6F_EVENT_NUMERICAL_VALIDITY_QUALIFICATION":
        raise ValueError("B6F historical qualification evidence is not passing")
    relation = _relational_audit(b6e["representation"], b6e["b5"])
    if not relation["interface_structural_identity_pass"] or not relation["junction_structural_incidence_pass"]:
        raise ValueError("governed interface/junction structural relation audit failed")
    state = _classify_state_transfers(_read(root / "outputs/r6_b6e_minimal_mvp_model_implementation/B6E_STATE_TRANSFER_DECLARATIONS.json")["declarations"])
    interface_motion = _interface_kinematics(b6e["b5"]["descriptors"])
    if interface_motion["decomposed_count"] != 1983 or interface_motion["missing_component_count"] != 0:
        raise ValueError("B5 governed interface normal/tangential kinematics are incomplete")
    memory_declarations = _read(root / "outputs/r6_b6e_minimal_mvp_model_implementation/B6E_SYSTEM_MEMORY_TRANSFER.json")["declarations"]
    memory = [
        {"memory_class": "FEG/ShellSet runtime products", "classification": "DERIVED_RECOMPUTABLE", "blocking_first_step": False, "basis": "D7 defers mechanics; B6E forbids treating runtime products as canonical memory."},
        {"memory_class": "initial-world supported fields", "classification": "NONBLOCKING_ASYNC", "blocking_first_step": False, "basis": "retain required SYSTEM_MEMORY at T0 and expose per-domain temporal validity under D6; no value discarded or promoted to T1."},
        {"memory_class": "plate kinematics", "classification": "REFERENCE_ONLY", "blocking_first_step": False, "basis": "retain forcing/replay identity; no change to the forcing record."},
        {"memory_class": "unknown-domain masks", "classification": "REFERENCE_ONLY", "blocking_first_step": False, "basis": "preserve UNKNOWN support evidence unchanged."},
        {"memory_class": "vector partition", "classification": "REFERENCE_ONLY", "blocking_first_step": False, "basis": "retain T0 identity; D1 prohibits reindex absent a governed event."},
    ]
    if len(state) != 15 or len(memory_declarations) != 5:
        raise ValueError("B6E state/memory inventory cardinality changed")
    required = [{"family": "plate-local geometry coordinates", "classification": "REQUIRED_SYNCHRONOUS_FIRST_STEP",
        "authorized_operation": "B6B conditional exact rigid transform x(t)=R(omega,t)x(T0), with B6C active RH XYZ column-vector action",
        "scope": "single-plate interiors / distinct plate-local side representatives only; only within an accepted event-free segment",
        "execution_performed": False}]
    events = _event_coverage()
    bounds = [{"bound_id": "B6G_CONDITIONAL_RIFT_ACTIVATION_HORIZON", "value": 27123.405156307464,
        "unit": "year", "scope": "eligible rift-process activation only", "authority": "B6A Census V3 guard / B6D D1 event policy",
        "derivation": "governed activation threshold and maximum positive opening rate with fixed T0 Euler forcing",
        "coverage": "does not bound plate split/merge, boundary birth/death, interface transition or junction transition",
        "limiting_condition": "rift process activation at eligible support; limiting pair 1:3",
        "strictness": "stop before/capture the event; no accepted interval crosses the unresolved event",
        "applicability": "conditional constant-T0 Euler segment", "not_a_dt": True}]
    blockers = [{"blocker_id": "D1_UNCOVERED_TOPOLOGY_TRANSITIONS", "status": "REQUIRED_AND_BLOCKING",
        "exact_gap": "No qualified detector or positive interval proof covers plate split/merge/create/terminate, boundary birth/death, interface split/merge, junction birth/death/connectivity reassignment, or unenumerated topology events.",
        "why_rift_bound_is_insufficient": "The 27,123.405-year guard detects rift-process activation only; B6A explicitly says it is not a topology transition or generic invariance bound.",
        "minimum_closure": "Govern either a complete conservative first-segment event vocabulary plus deterministic detector/stop rules, or an authoritative positive interval proof that excludes these transitions."}]
    result = {
        "schema": "R6_B6G_RESULT_V1", "qualification_verdict": "PASS_B6G_TARGETED_VALIDITY_GAP_CLOSURE",
        "qualified_source_commit": head, "branch": branch,
        "false_numerical_blockers_removed": ["generic maximum rotation angle", "absolute node displacement cap",
            "displacement/interior-edge ratio threshold", "interior triangle-quality/remesh threshold",
            "interface co-location/gap threshold", "junction single-coordinate/spread threshold", "mechanics solver stability limit"],
        "interface_validity_status": "INTERFACE_VALIDITY_IS_RELATIONAL_AND_POSITIVE",
        "interface_blocker": "None for D2 side identity, adjacency and support pairing within an unchanged topology segment; physical gap semantics remain UNKNOWN and do not impose co-location.",
        "interface_kinematic_summary": interface_motion,
        "junction_validity_status": "JUNCTION_VALIDITY_IS_RELATIONAL_AND_POSITIVE",
        "junction_blocker": "None for D3 identity/incidence preservation; one shared Euclidean point, residual velocity allocation and physical accommodation are not required. Physical accommodation remains UNKNOWN.",
        "topology_event_coverage_status": "PARTIAL_EVENT_COVERAGE_ONLY",
        "topology_positive_window_status": "PARTIAL_EVENT_COVERAGE_ONLY", "topology_positive_bound": None,
        "state_transfer_blocking_status": "NO_REQUIRED_SYNCHRONOUS_STATE_FAMILY_LACKS_AN_AUTHORIZED_OPERATION; D6_ASYNC_DOMAINS_RETAIN_LATEST_VALID_T0",
        "blocking_state_families": [], "system_memory_blocking_status": "NO_SYSTEM_MEMORY_CLASS_BLOCKS_FIRST_DT_ADJUDICATION_WHEN_RETAINED_AND_TEMPORALLY_SCOPED",
        "blocking_memory_classes": [], "qualified_bound_count": 1, "qualified_bounds": bounds,
        "current_smallest_qualified_bound_not_a_dt": {"value": 27123.405156307464, "unit": "year", "scope": "conditional rift activation only", "not_a_dt": True, "not_a_global_topology_bound": True},
        "minimal_remaining_blocking_set": blockers, "first_dt_readiness": "NOT_READY_FOR_FIRST_DT_ADJUDICATION",
        "production_source_changes": False, "implementation_changes": ["B6G read-only relational/topology evidence runner", "B6G tests and retained evidence"],
        "execution_target": "WINDOWS", "ubuntu_work_required": False,
        "scientific_side_effect_check": {"mechanics_authorized": False, "forward_evolution_authorized": False,
            "dt_selected": False, "t1_created": False, "canonical_state_changed": False,
            "canonical_node_motion_executed": False, "canonical_topology_mutated": False,
            "shellset_executed": False, "orbdata_mechanics_executed": False,
            "runtime_authorized": True, "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE"},
        "t0_counts": {"nodes": 64442, "triangles": 128880, "interfaces": relation["interface_count"],
            "interface_sides": relation["unique_plate_local_side_id_count"], "junction_relations": relation["junction_relation_count"],
            "junction_sides": b6e["representation"].summary()["junction_side_entities"],
            "canonical_mesh_sha256": b6e["b5"]["spatial"]["mesh"]["sha256"]},
        "input_provenance": {"B6F_historical_source_commit": b6f["qualified_source_commit"],
            "B6E_historical_source_commit": b6e_result["qualified_source_commit"],
            "verified_input_artifact_count": len(manifests)},
    }
    return {"result": result, "relations": relation, "interface_motion": interface_motion, "events": events, "state": state,
        "memory": memory, "required_transfers": required, "bounds": bounds,
        "blockers": blockers, "manifests": manifests,
        "input_hashes": {k: v for k, v in sorted(manifests.items())}}


def _write(data: dict[str, Any], out: Path, report: Path, test_results: dict[str, Any] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payloads = {
        "B6G_RESULT.json": data["result"],
        "B6G_FALSE_BLOCKER_REVIEW.json": {"removed_false_blockers": data["result"]["false_numerical_blockers_removed"], "reviewed_from": "B6D frozen MVP semantics + exact finite rotation"},
        "B6G_INTERFACE_VALIDITY.json": {"status": data["result"]["interface_validity_status"], "structural_audit": data["relations"], "kinematic_components": data["interface_motion"], "frozen_invariants": ["boundary/side IDs preserved", "two distinct plate-local sides", "adjacent plate pairing preserved", "endpoint identity/order preserved", "geometric co-location not required by D2"], "physical_accommodation": "UNKNOWN"},
        "B6G_JUNCTION_VALIDITY.json": {"status": data["result"]["junction_validity_status"], "structural_audit": data["relations"], "frozen_invariants": ["all 3 incident plate IDs retained", "all 3 incident interfaces retained", "3 distinct junction-side IDs retained", "no unique owner", "no shared Euclidean coordinate required"], "physical_accommodation": "UNKNOWN"},
        "B6G_EVENT_COVERAGE.json": {"status": data["result"]["topology_event_coverage_status"], "events": data["events"], "absence_of_detector_means_absence": False},
        "B6G_TOPOLOGY_WINDOW.json": {"status": data["result"]["topology_positive_window_status"], "positive_bound": None, "qualified_event_specific_bound_not_a_topology_window": data["bounds"][0], "coverage_gap": data["blockers"][0]},
        "B6G_STATE_TRANSFER_BLOCKING.json": {"state_family_count": len(data["state"]), "blocking_families": [], "required_transfer_operations": data["required_transfers"], "families": data["state"]},
        "B6G_SYSTEM_MEMORY_BLOCKING.json": {"memory_class_count": len(data["memory"]), "blocking_classes": [], "system_memory_discarded": False, "classes": data["memory"]},
        "B6G_IMPLEMENTATION_MAP.json": {"production_changes": False, "auditor": "scripts/r6_b6g_targeted_validity_gap_closure.py", "input_hashes": data["input_hashes"], "rederived_relation_counts": data["result"]["t0_counts"], "candidate_geometry_written": False},
        "B6G_QUALIFIED_BOUND_SET.json": {"bounds": data["bounds"], "current_smallest_qualified_bound_not_a_dt": data["result"]["current_smallest_qualified_bound_not_a_dt"]},
        "B6G_MINIMAL_BLOCKING_SET.json": data["blockers"],
        "B6G_FIRST_DT_READINESS.json": {"readiness": data["result"]["first_dt_readiness"], "blockers": data["blockers"], "dt_selected": False},
        "B6G_TEST_RESULTS.json": test_results or {"status": "NOT_RECORDED", "source_commit": data["result"]["qualified_source_commit"]},
        "B6G_SOURCE_MANIFEST.json": {"source_commit": data["result"]["qualified_source_commit"], "inputs": data["input_hashes"]},
    }
    for name, value in payloads.items():
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (out / "README.md").write_text("# B6G targeted validity gap closure\n\nRead-only qualification of the frozen B6D/B6E kinematic MVP. It closes false interior numerical and relational co-location blockers, but does not qualify a complete topology event window or select `dt`. No candidate geometry is written.\n", encoding="utf-8", newline="\n")
    artifacts = []
    for path in sorted(out.iterdir()):
        if path.name == "B6G_ARTIFACT_MANIFEST.json" or not path.is_file():
            continue
        artifacts.append({"relative_path": path.name, "byte_size": path.stat().st_size, "sha256": _sha(path), "role": "B6G qualification evidence"})
    if report.is_file():
        artifacts.append({"relative_path": "../../docs/arcana/B6G_TARGETED_VALIDITY_GAP_CLOSURE.md", "byte_size": report.stat().st_size, "sha256": _sha(report), "role": "human closure report"})
    artifacts.sort(key=lambda row: row["relative_path"])
    (out / "B6G_ARTIFACT_MANIFEST.json").write_text(json.dumps({"schema": "R6_B6G_ARTIFACT_MANIFEST_V1", "manifest_self_hash": "OMITTED_BY_POLICY", "artifacts": artifacts}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--test-results-json", type=Path)
    args = parser.parse_args()
    data = evaluate(args.root)
    tests = _read(args.test_results_json) if args.test_results_json else None
    _write(data, args.output, args.report, tests)
    print(json.dumps(data["result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
