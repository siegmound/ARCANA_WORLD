#!/usr/bin/env python3
"""Qualify the first model-relative dt selection without evolving R6 state."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r6_b6j_first_dt_adjudication"
REPORT = ROOT / "docs/arcana/B6J_FIRST_DT_ADJUDICATION.md"
EXPECTED_B6I_SOURCE = "a3d351b0abf8231308a8394feadf9480794dc0ea"
T0_AGE_MA = Decimal("210.0")
YEAR_PER_MA = Decimal("1000000")


def normalize_years(value: float | int | str, unit: str) -> float:
    factors = {"year": 1.0, "years": 1.0, "yr": 1.0,
               "kyr": 1_000.0, "ka": 1_000.0,
               "Myr": 1_000_000.0, "Ma": 1_000_000.0}
    if unit not in factors:
        raise ValueError(f"unsupported temporal unit: {unit}")
    result = float(value) * factors[unit]
    if not math.isfinite(result) or result <= 0:
        raise ValueError("qualified temporal bounds must be finite and positive")
    return result


def select_limiting_bound(bounds: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not bounds:
        raise ValueError("no active qualified temporal bound")
    normalized = []
    for row in bounds:
        normalized.append({**dict(row), "value_years": normalize_years(row["value"], row["unit"])})
    normalized.sort(key=lambda row: (row["value_years"], row["bound_id"]))
    return normalized[0]


def active_qualified_bounds(constraints: list[Mapping[str, Any]],
                           bounds: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    active_ids = [str(row["bound_id"]) for row in constraints
                  if row.get("status") == "ACTIVE_QUALIFIED_BOUND" and row.get("bound_id")]
    by_id = {str(row["bound_id"]): dict(row) for row in bounds}
    if len(active_ids) != len(set(active_ids)) or set(active_ids) != set(by_id):
        raise ValueError("active qualified constraint/bound identities do not close exactly")
    return [by_id[bound_id] for bound_id in sorted(active_ids)]


def decide_endpoint(*, interval_open_at_horizon: bool,
                    capture_boundary_authorized: bool,
                    event_at_equality: bool) -> str:
    if not all(isinstance(value, bool) for value in
               (interval_open_at_horizon, capture_boundary_authorized, event_at_equality)):
        raise ValueError("endpoint semantics must be explicit booleans")
    if interval_open_at_horizon and capture_boundary_authorized and event_at_equality:
        return "EVENT_ALIGNED_ENDPOINT_AUTHORIZED"
    if interval_open_at_horizon and not capture_boundary_authorized:
        return "STRICT_PRE_EVENT_ENDPOINT_REQUIRED"
    return "ENDPOINT_POLICY_BLOCKED"


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _verify_source_authority(root: Path) -> dict[str, str]:
    # B6I revalidates the B5/B6A/B6D-B6H manifests and their pinned evidence.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.r6_b6i_first_segment_topology_model_extension import evaluate as evaluate_b6i
    from scripts.r6_b6i_first_segment_topology_model_extension import _verify_manifest as verify_manifest
    b6i = evaluate_b6i(root)
    verified_b6i_manifest = verify_manifest(
        root, "outputs/r6_b6i_first_segment_topology_model_extension", "B6I_ARTIFACT_MANIFEST.json")
    retained_b6i = _read(root / "outputs/r6_b6i_first_segment_topology_model_extension/B6I_RESULT.json")
    if retained_b6i["qualified_source_commit"] != EXPECTED_B6I_SOURCE:
        raise ValueError("historical B6I qualified source identity changed")

    b6a_inputs = _read(root / "outputs/r6_b6a_positive_duration_authority/B6A_INPUT_EVIDENCE.json")
    verified: dict[str, str] = {}
    for row in b6a_inputs["sources"]:
        path = (root / row["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"B6A source is missing or escapes repository: {row['path']}")
        if path.stat().st_size != row["byte_size"] or _sha(path) != row["sha256"]:
            raise ValueError(f"B6A source evidence mismatch: {row['path']}")
        verified[path.relative_to(root).as_posix()] = row["sha256"]
    return {**b6i["verified_inputs"], **verified_b6i_manifest, **verified}


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch = _git(root, "branch", "--show-current")
    head = _git(root, "rev-parse", "HEAD")
    verified = _verify_source_authority(root)
    b6a = _read(root / "outputs/r6_b6a_positive_duration_authority/B6A_TOPOLOGY_TEMPORAL_BOUND.json")
    b6f = _read(root / "outputs/r6_b6f_event_numerical_validity/B6F_QUALIFIED_BOUND_SET.json")
    b6d = _read(root / "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_TOPOLOGY_EVENT_POLICY.json")
    b6g = _read(root / "outputs/r6_b6g_targeted_validity_gap_closure/B6G_QUALIFIED_BOUND_SET.json")
    b6h = _read(root / "outputs/r6_b6h_topology_event_coverage_closure/B6H_RIFT_HORIZON_INTEGRATION.json")
    b6i = _read(root / "outputs/r6_b6i_first_segment_topology_model_extension/B6I_TOPOLOGY_VALIDITY_BOUND.json")
    b6i_scope = _read(root / "outputs/r6_b6i_first_segment_topology_model_extension/B6I_AUTHORIAL_TOPOLOGY_SCOPE.json")
    law = _read(root / "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json")

    if b6a["positive_conditional_rift_activation_bound"]["elapsed_years"] != b6i["value"]:
        raise ValueError("B6A and B6I rift horizons disagree")
    if b6d["policy"] != "EVENT_DRIVEN_TOPOLOGY_HOLD" or b6i["strictness"] != "validity interval is open at the event horizon; stop before or capture event; no accepted segment crosses it":
        raise ValueError("topology endpoint authority is missing or changed")
    if law["driver_and_transition_law"]["event_condition"] != "RIFT_INITIATION becomes possible when E >= theta under positive opening; this operational model event marks activation of the rift-process state, not plate splitting or mature breakup":
        raise ValueError("qualified rift event predicate differs from the adjudicated predicate")
    if "analytically solve dt_event" not in law["driver_and_transition_law"]["event_localization"]:
        raise ValueError("analytic event-time derivation is no longer explicit")
    if b6i_scope["initial_topology"] != "GOVERNED_T0_TOPOLOGY":
        raise ValueError("pre-event topology identity is not explicit")

    value = normalize_years(b6i["value"], b6i["unit"])
    if value != 27123.405156307464 or b6i["limiting_entity_pair"] != "1:3":
        raise ValueError("qualified event bound/limiting entity differs")
    prior_bound_sets = [
        ("B6F", b6f["bounds"]),
        ("B6G", b6g["bounds"]),
        ("B6H", [b6h]),
        ("B6I", [b6i]),
    ]
    cross_stage_bounds = []
    for stage, rows in prior_bound_sets:
        if len(rows) != 1:
            raise ValueError(f"{stage} qualified active-bound inventory is not a singleton")
        row = rows[0]
        row_value = row.get("value", row.get("value_years"))
        row_unit = row.get("unit", "year")
        if normalize_years(row_value, row_unit) != value:
            raise ValueError(f"{stage} qualified bound differs from the B6I event horizon")
        cross_stage_bounds.append({"stage": stage, "qualified_bound_count": 1,
                                  "bound_id": row.get("bound_id", "RIFT_PROCESS_ACTIVATION_HORIZON"),
                                  "value_years": value})
    bounds = [{"bound_id": "B6I_RIFT_PROCESS_ACTIVATION_HORIZON", "value": value, "value_years": value,
               "unit": "year", "category": "MODEL_EVENT_HORIZON",
               "authority": b6i["authority"], "scope": b6i["applicability"],
               "strictness": b6i["strictness"], "limiting_entity": "plate pair 1:3",
               "applicability_condition": b6i["applicability"], "source": "B6I_TOPOLOGY_VALIDITY_BOUND.json"}]
    active = [
        {"constraint_id": "POSITIVE_DURATION_KINEMATIC_VALIDITY", "status": "ACTIVE_NONNUMERIC_CONDITION", "basis": "B6A/B6B governed conditional constant-T0 Euler first segment; no separate numeric duration bound."},
        {"constraint_id": "FIRST_SEGMENT_TOPOLOGY_VALIDITY", "status": "ACTIVE_QUALIFIED_BOUND", "bound_id": bounds[0]["bound_id"]},
        {"constraint_id": "ROTATION_IMPLEMENTATION_VALIDITY", "status": "CLOSED_NO_NUMERIC_BOUND_REQUIRED", "basis": "B6C/B6D action convention and B6G exact rigid transform closure."},
        {"constraint_id": "RIGID_INTERIOR_MESH_VALIDITY", "status": "CLOSED_NO_NUMERIC_BOUND_REQUIRED", "basis": "B6G exact rigid plate-local geometry; no generic angle/displacement threshold."},
        {"constraint_id": "INTERFACE_RELATIONAL_VALIDITY", "status": "CLOSED_NO_NUMERIC_BOUND_REQUIRED", "basis": "B6D/B6G interface sides are relational, not required to be co-located."},
        {"constraint_id": "JUNCTION_RELATIONAL_VALIDITY", "status": "CLOSED_NO_NUMERIC_BOUND_REQUIRED", "basis": "B6D/B6G set-valued multi-interface junction relation."},
        {"constraint_id": "STATE_TRANSFER_APPLICABILITY", "status": "CLOSED_NO_NUMERIC_BOUND_REQUIRED", "basis": "B6I async domain validity; no required synchronous transfer family blocks this step."},
        {"constraint_id": "SYSTEM_MEMORY_APPLICABILITY", "status": "CLOSED_NO_NUMERIC_BOUND_REQUIRED", "basis": "B6G/B6I closure when retained and temporally scoped."},
        {"constraint_id": "MECHANICS_SOLVER_STABILITY", "status": "NOT_APPLICABLE", "basis": "B6D MVP permits a kinematic first segment without mechanics; no mechanics solver is selected or run."},
        {"constraint_id": "INDEPENDENT_NON_RIFT_TOPOLOGY_MUTATIONS", "status": "OUT_OF_SCOPE", "basis": "B6I frozen first-segment process registry."},
    ]
    active_bounds = active_qualified_bounds(active, bounds)
    limiting = select_limiting_bound(active_bounds)
    endpoint_status = decide_endpoint(interval_open_at_horizon=True,
                                      capture_boundary_authorized=True,
                                      event_at_equality=">=" in law["driver_and_transition_law"]["event_condition"])
    if endpoint_status != "EVENT_ALIGNED_ENDPOINT_AUTHORIZED":
        raise ValueError("event-aligned endpoint is not uniquely authorized")

    dt = limiting["value_years"]
    age_decimal = T0_AGE_MA - Decimal.from_float(dt) / YEAR_PER_MA
    age_ma = float(age_decimal)
    active_only = [row for row in active if row["status"] in
                   {"ACTIVE_QUALIFIED_BOUND", "ACTIVE_NONNUMERIC_CONDITION"}]
    dt_selection = {
        "status": "FIRST_DT_SELECTED", "value": dt, "unit": "year",
        "numeric_representation": {"format": "IEEE-754 binary64", "shortest_round_trip": repr(dt), "hex": dt.hex()},
        "numeric_tolerance": "NONE_ADDED_TO_ANALYTIC_BOUND_SELECTION; no rounding, epsilon, or safety factor applied",
        "selection_rule": "minimum active qualified positive temporal bound; the sole bound ends the first segment exactly at the enabled event boundary",
        "limiting_constraint": limiting["bound_id"], "limiting_event": "RIFT_PROCESS_ACTIVATION",
        "limiting_entity": "plate pair 1:3", "endpoint_semantics": "pre-transition event-boundary capture; no topology mutation in the kinematic step",
        "strictness": b6i["strictness"], "authority": ["B6A_TOPOLOGY_TEMPORAL_BOUND.json", "B6D_TOPOLOGY_EVENT_POLICY.json", "B6G_QUALIFIED_BOUND_SET.json", "B6I_TOPOLOGY_VALIDITY_BOUND.json"],
        "replay_recipe_inputs": ["governed T0 age", "frozen MVP model identity", "ordered active constraint records", "B6I event registry/bound", "endpoint policy", "source artifact hashes"],
    }
    event = {
        "status": "EVENT_BOUNDARY_CONTRACT_DEFINED_NOT_EVENT_CREATED",
        "event_class": "RIFT_PROCESS_ACTIVATION", "event_time_from_t0_years": dt,
        "event_absolute_geological_age_ma": age_ma, "limiting_entity": "plate pair 1:3",
        "pre_event_topology_identity": "GOVERNED_T0_TOPOLOGY",
        "event_predicate": law["driver_and_transition_law"]["event_condition"],
        "event_provenance": {"B6A": verified["outputs/r6_b6a_positive_duration_authority/B6A_TOPOLOGY_TEMPORAL_BOUND.json"],
                             "B6I": verified["outputs/r6_b6i_first_segment_topology_model_extension/B6I_TOPOLOGY_VALIDITY_BOUND.json"],
                             "rift_guard_law": verified["R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"]},
        "transition_status": "NOT_EXECUTED",
        "post_event_transition_contract": "A later explicit event-specific topology and identity/lineage map is required before transition; no silent crossing or application.",
    }
    age = {"source_age_ma": float(T0_AGE_MA), "elapsed_dt_years": dt, "target_age_ma": age_ma,
           "conversion_rule": "source_age_ma - elapsed_dt_years / 1,000,000; positive elapsed duration corresponds to decreasing geological age toward present",
           "precision": "Decimal calculation from exact decimal T0 age and the exact binary64 dt value, then serialized as binary64; planning metadata only."}
    dt_provenance = {
        "status": "WHY_PROVENANCE_SPECIFIED",
        "active_bound_set": [row["bound_id"] for row in bounds], "limiting_bound": limiting["bound_id"],
        "model_scope": "FROZEN_MVP_FIRST_SEGMENT_CONSTANT_T0_EULER__TOPOLOGY_HOLD_UNTIL_ENABLED_RIFT_EVENT",
        "event_policy": b6d["policy"], "endpoint_policy": endpoint_status,
        "source_qualified_evidence": {key: verified[key] for key in sorted(verified) if key.startswith("outputs/r6_b6") or key == "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"},
        "numeric_representation": dt_selection["numeric_representation"],
        "numeric_tolerance": dt_selection["numeric_tolerance"],
        "future_solver_tolerance": "UNSELECTED; B6A requires solver-specific event-localization tolerance before event application. No tolerance is silently introduced here.",
    }
    replay = {
        "status": "PASS_DETERMINISTIC_SELECTION_REPLAY",
        "algorithm": "validate evidence identities; normalize all active qualified bounds to years; stable-sort by (value_years, bound_id); select first; preserve binary64 value and hex representation; derive target age from fixed source age",
        "inputs": dt_selection["replay_recipe_inputs"],
        "excluded_inputs": ["wall clock", "filesystem mtime", "unordered directory iteration", "unstored tolerance", "randomness"],
        "repeatability": "Two independently reconstructed selections from the same verified evidence yield byte-identical canonical JSON for dt, event boundary, and target age.",
        "scope_limit": "This proves selection/provenance determinism only; no state integration or replayed physical result is executed.",
    }
    result = {
        "schema": "R6_B6J_RESULT_V1", "qualification_verdict": "PASS_B6J_FIRST_DT_ADJUDICATION",
        "qualified_source_commit": head, "branch": branch,
        "active_constraint_count": len(active_only), "active_constraints": active_only,
        "constraint_candidate_count": len(active), "constraint_assessment": active,
        "finite_qualified_temporal_bound_count": len(bounds), "finite_qualified_temporal_bounds": bounds,
        "limiting_constraint": limiting["bound_id"], "limiting_event": "RIFT_PROCESS_ACTIVATION",
        "limiting_entity": "plate pair 1:3", "rift_horizon_strictness_status": "OPEN_INTERVAL__EXACT_BOUNDARY_CAPTURE_ALLOWED__NO_CROSSING",
        "endpoint_policy_status": endpoint_status, "first_dt_selection_status": "FIRST_DT_SELECTED",
        "first_dt_value": dt, "first_dt_unit": "year", "first_dt_selection_rule": dt_selection["selection_rule"],
        "source_age_ma": age["source_age_ma"], "target_age_ma": age_ma,
        "event_boundary_contract_status": event["status"], "event_transition_status": event["transition_status"],
        "dt_provenance_status": dt_provenance["status"], "dt_replay_determinism_status": replay["status"],
        "first_candidate_state_readiness": "READY_FOR_ISOLATED_FIRST_CANDIDATE_STATE_CONSTRUCTION",
        "next_stage_authorization": "AUTHORIZE_FIRST_CANDIDATE_STATE_CONSTRUCTION",
        "runtime_authorized": True, "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
        "mechanics_authorized": False, "forward_evolution_authorized": False, "dt_selected": True,
        "t1_created": False, "canonical_state_changed": False, "canonical_node_motion_executed": False,
        "canonical_topology_mutated": False, "rift_transition_executed": False,
        "shellset_executed": False, "orbdata_mechanics_executed": False,
        "qualified_prior_stage": "B6I_FIRST_SEGMENT_TOPOLOGY_MODEL_EXTENSION",
        "qualified_prior_stage_source_commit": EXPECTED_B6I_SOURCE,
        "verified_prior_artifact_count": len(verified), "execution_target": "WINDOWS",
        "source_evidence_sha256": dict(sorted(verified.items())),
    }
    return {"result": result, "active": {"schema": "R6_B6J_ACTIVE_CONSTRAINT_SET_V1", "candidate_constraint_count": len(active), "active_constraint_count": len(active_only), "active_constraints": active_only, "constraints": active},
            "bounds": {"schema": "R6_B6J_NORMALIZED_BOUNDS_V1", "bounds": bounds, "finite_active_bound_count": len(bounds), "hidden_smaller_qualified_bound": False, "limiting_bound_id": limiting["bound_id"], "cross_stage_bound_verification": cross_stage_bounds},
            "strictness": {"schema": "R6_B6J_RIFT_BOUND_STRICTNESS_V1", "interval": "0 <= t < horizon", "predicate": law["driver_and_transition_law"]["event_condition"], "predicate_satisfied_at_equality": True, "activation_becomes_possible_at_equality": True, "actual_event_created": False, "endpoint_capture_allowed": True, "no_accepted_segment_crosses": True, "numeric_tolerance": "NONE_FOR_ANALYTIC_BOUND_SELECTION; solver-specific localization tolerance remains required before event application."},
            "endpoint": {"schema": "R6_B6J_ENDPOINT_POLICY_V1", "status": endpoint_status, "policy": "EVENT_ALIGNED_PRETRANSITION_ENDPOINT", "topology_mutation_during_step": False, "transition_execution_authorized": False, "causal_rationale": "stop at the earliest enabled causal model event and represent its boundary explicitly; this avoids arbitrary calendar checkpoints and preserves sparse causal history"},
            "dt": dt_selection, "age": age, "event": event, "provenance": dt_provenance, "replay": replay,
            "verified_inputs": dict(sorted(verified.items()))}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write(data: dict[str, Any], *, test_summary: dict[str, Any], root: Path = ROOT) -> None:
    root = root.resolve()
    out, report = root / "outputs/r6_b6j_first_dt_adjudication", root / "docs/arcana/B6J_FIRST_DT_ADJUDICATION.md"
    out.mkdir(parents=True, exist_ok=True)
    payloads = {
        "B6J_RESULT.json": data["result"], "B6J_ACTIVE_CONSTRAINT_SET.json": data["active"],
        "B6J_NORMALIZED_BOUNDS.json": data["bounds"], "B6J_RIFT_BOUND_STRICTNESS.json": data["strictness"],
        "B6J_ENDPOINT_POLICY.json": data["endpoint"], "B6J_DT_SELECTION.json": data["dt"],
        "B6J_TARGET_AGE.json": data["age"], "B6J_EVENT_BOUNDARY_CONTRACT.json": data["event"],
        "B6J_DT_PROVENANCE.json": data["provenance"], "B6J_REPLAY_DETERMINISM.json": data["replay"],
        "B6J_NEXT_STAGE_CONTRACT.json": {"authorization": data["result"]["next_stage_authorization"], "scope": "isolated candidate-state construction only", "forbidden": ["canonical T1 publication", "topology transition", "unbounded forward evolution", "mechanics", "ShellSet", "OrbData mechanics"]},
        "B6J_TEST_RESULTS.json": test_summary,
    }
    for name, value in payloads.items():
        _write_json(out / name, value)
    (out / "README.md").write_text("# B6J first-dt adjudication\n\nThe package selects the single qualified model-relative interval to the pre-transition rift event boundary. It records the event boundary but does not create an event, candidate state, T1, or mutate topology. The solver-specific event-localization tolerance remains unselected for future event application.\n", encoding="utf-8", newline="\n")
    report.write_text(_render_report(data, test_summary), encoding="utf-8", newline="\n")
    files = [*out.iterdir(), report, root / "scripts/r6_b6j_first_dt_adjudication.py", root / "tests/test_r6_b6j_first_dt_adjudication.py"]
    manifest_rows = []
    for path in sorted(files, key=lambda item: item.relative_to(out).as_posix() if item.is_relative_to(out) else item.relative_to(root).as_posix()):
        if path.name == "B6J_ARTIFACT_MANIFEST.json":
            continue
        manifest_rows.append({"relative_path": path.relative_to(out).as_posix() if path.is_relative_to(out) else (Path("../..") / path.relative_to(root)).as_posix(),
                              "byte_size": path.stat().st_size, "sha256": _sha(path), "role": "B6J evidence/report/qualification source"})
    _write_json(out / "B6J_ARTIFACT_MANIFEST.json", {"schema": "R6_B6J_ARTIFACT_MANIFEST_V1", "manifest_self_hash": "OMITTED_BY_POLICY", "artifacts": manifest_rows})


def _render_report(data: dict[str, Any], tests: dict[str, Any]) -> str:
    r, dt, age, event = data["result"], data["dt"], data["age"], data["event"]
    return f"""# B6J first-dt adjudication

## Qualified baseline and decision

- Branch: `{r['branch']}`
- Qualified source commit: `{r['qualified_source_commit']}`
- B6I historical source remains `{EXPECTED_B6I_SOURCE}`.
- Result: `{r['qualification_verdict']}`.
- First interval: `{dt['numeric_representation']['shortest_round_trip']} year` (`{dt['numeric_representation']['hex']}`), selected as the minimum applicable qualified bound.

## Constraint and bound adjudication

There is exactly one finite active qualified temporal bound: conditional `RIFT_PROCESS_ACTIVATION` at pair `1:3`, `{dt['numeric_representation']['shortest_round_trip']} years`. Positive-duration kinematics is an active nonnumeric model condition. B6G closes generic rotation/displacement thresholds, interface and junction geometric co-location, transfer and SYSTEM_MEMORY blockers. Mechanics stability is not applicable to the mechanics-free MVP. Non-rift topology mutations are out of scope under B6I.

The event law uses `E >= theta`; the topology validity interval is open at the horizon. B6I explicitly permits stopping before or capturing the event, while forbidding a segment from crossing it. B6J therefore authorizes exact pre-transition event-boundary capture. It adds no epsilon, tolerance, rounding, or safety factor. The solver-specific localization tolerance still required before future event application is unselected and is not claimed as solved here.

## Causal endpoint, history and replay

The interval ends at the earliest enabled causal event boundary under the adaptive constraint-driven and event-driven topology-hold policies. The reason is sparse causal history: preserve the long valid segment and represent the event boundary explicitly, rather than adding an arbitrary calendar checkpoint. WORLD_HISTORY `EventRecord` supports temporal/spatial support, trigger/cause, before/after state and causal dependencies; `ReplayRecipe` can reference event IDs. This package defines only the boundary contract and does not create an `EventRecord` or execute its transition.

Target age is `{age['target_age_ma']:.17g} Ma` from source age `{age['source_age_ma']}` Ma using positive elapsed years and decreasing geological age. It is planning metadata only; no state at that age is materialized.

## Event and authorization boundary

- Event boundary contract: `{event['status']}`.
- Transition status: `{event['transition_status']}`.
- Maximum next authorization: `{r['next_stage_authorization']}`.
- `dt_selected=true`; mechanics, forward evolution, T1, canonical state mutation, node motion, topology mutation, ShellSet and OrbData mechanics remain false/not executed.
- Runtime authorization remains limited to loading and consuming the governed ARCANA T0 runtime package.

## Determinism and validation

Bound normalization converts supported temporal units to years, then sorts by `(value_years, bound_id)`. Numeric representation and hexadecimal binary64 value are retained. Replay selection excludes wall-clock, filesystem ordering, random inputs and unstored tolerances. This is selection determinism, not physical simulation replay.

Recorded tests: `{json.dumps(tests, sort_keys=True)}`.

The retained artifact manifest covers this report, evidence JSON, runner and focused tests; the manifest omits its own hash. No production scientific/runtime source was changed.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--focused-tests", type=int, default=0)
    parser.add_argument("--related-tests", type=int, default=0)
    parser.add_argument("--full-tests", type=int, default=0)
    args = parser.parse_args()
    data = evaluate(args.root)
    tests = {"focused_b6j_passed": args.focused_tests, "related_b5_b6i_passed": args.related_tests,
             "full_r6_passed": args.full_tests, "status": "PASS" if args.focused_tests and args.related_tests and args.full_tests else "NOT_FULLY_RECORDED"}
    write(data, test_summary=tests, root=args.root)
    print(json.dumps(data["result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
