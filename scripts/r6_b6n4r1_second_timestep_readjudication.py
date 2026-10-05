"""Deterministically readjudicate the B6N4 second-segment gate.

This is a read-only decision aid. It reads frozen ARCANA contracts and the
qualified B6N4-A evidence bundle; it never opens or writes WORLD_HISTORY.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


EXPECTED_BRANCH = "r6/b6n4r1-second-timestep-readjudication"
EXPECTED_HEAD = "d3128fca0f6bd812298544768dbac0ef74dcca75"
EXPECTED_B6N4A_SOURCE = "5430d09dfd6f3cc5f1ad5d6db36b8fece6b30ab3"
EXPECTED_B6N4A_MANIFEST_SHA256 = "f4368256653979f77adaedae99829fb53bdb5c354d35ae4385855708579f9e47"
EXPECTED_PRE_STATE = "r6state_3e484d59d985ba93ec8c58d5a9a82ca4369f7aaa2d6725339479e68a7559810c"
EXPECTED_POST_STATE = "r6state_86b55139388fd6d01cb0ff640f9580e1e1331f2469fb5c4f296c6cf2578fc630"
EXPECTED_PAYLOAD_SHA256 = "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a"
EXPECTED_AGE_MA = 209.97287659484368


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True,
        text=True, encoding="utf-8",
    ).stdout.strip()


def _verify_manifest(bundle: Path) -> None:
    manifest = bundle / "EVIDENCE_CONTENT_SHA256.txt"
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != EXPECTED_B6N4A_MANIFEST_SHA256:
        raise ValueError("B6N4-A evidence manifest digest does not match the attested digest")
    seen: set[str] = set()
    entry_count = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64 or relative in seen:
            raise ValueError("malformed or duplicate B6N4-A manifest entry")
        seen.add(relative)
        path = (bundle / relative).resolve()
        if bundle.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"invalid B6N4-A evidence manifest path: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"B6N4-A evidence hash mismatch: {relative}")
        entry_count += 1
    if entry_count != 9:
        raise ValueError(f"expected 9 B6N4-A manifest entries, found {entry_count}")


def evaluate_dependency_closure(
    dependencies: list[dict[str, Any]], model_scope_limit_years: float,
    limiter_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Fail closed on a required dependency without authority/bound/isolation.

    Non-applicable and explicitly non-limiting rows are retained in the
    decision record but cannot be promoted to blockers by an UNKNOWN value.
    """
    blockers: list[dict[str, str]] = []
    if model_scope_limit_years <= 0:
        raise ValueError("model-scope limit must be a positive duration")
    for row in dependencies:
        if row["scope_role"] != "REQUIRED_FOR_REQUESTED_OUTPUT":
            continue
        if row["authority_status"] != "AUTHORIZED":
            blockers.append({"dependency": row["id"], "reason": "AUTHORITY_NOT_AUTHORIZED"})
        elif row["impact_bound_status"] not in {"BOUNDED", "NOT_APPLICABLE"}:
            blockers.append({"dependency": row["id"], "reason": "IMPACT_BOUND_UNRESOLVED"})
        elif row["dependency_status"] not in {"CLOSED", "ISOLATION_PROVEN"}:
            blockers.append({"dependency": row["id"], "reason": "DEPENDENCY_CLOSURE_NOT_PROVEN"})
        elif row.get("positive_validity_years", model_scope_limit_years) <= 0:
            blockers.append({"dependency": row["id"], "reason": "NO_POSITIVE_VALIDITY_INTERVAL"})

    authorized = not blockers
    limiter = select_nearest_positive_limiter(limiter_candidates or []) if authorized else None
    if authorized and limiter is None:
        blockers.append({"dependency": "LIMITER_SET", "reason": "NO_AUTHORIZED_POSITIVE_LIMITER"})
        authorized = False
    return {
        "status": "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED" if blockers else "AUTHORIZED_POSITIVE_PROPAGATION",
        "positive_propagation_established": authorized,
        "blocking_dependencies": blockers,
        "model_scope_limit_years": model_scope_limit_years,
        "model_scope_limit_is_event_free_proof": False,
        "nearest_authorized_limiter": limiter,
        "SECOND_DT_SELECTED": False,
        "dt2_years": None,
        "target_age_ma": None,
        "T2_CREATED": False,
    }


def select_nearest_positive_limiter(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Choose the earliest positive, explicitly authorized finite limiter."""
    eligible = []
    for candidate in candidates:
        years = candidate.get("delta_time_years")
        if (candidate.get("authorized") is True and isinstance(years, (int, float))
                and math.isfinite(years) and years > 0):
            eligible.append(candidate)
    if not eligible:
        return None
    return min(eligible, key=lambda item: (item["delta_time_years"], item["horizon_id"]))


def inspect_canonical_read_only(root: Path) -> dict[str, Any]:
    """Hash the canonical store as bytes and inspect only indexed records."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("canonical WORLD_HISTORY root is missing")
    file_rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        file_rows.append((relative, len(payload), hashlib.sha256(payload).hexdigest()))
    tree = hashlib.sha256()
    for relative, size, digest in file_rows:
        tree.update(relative.encode("utf-8")); tree.update(b"\0")
        tree.update(str(size).encode("ascii")); tree.update(b"\0")
        tree.update(digest.encode("ascii")); tree.update(b"\n")

    current = _load_json(root / ".history_visibility/CURRENT.json")
    view_path = root / ".history_visibility/views" / f"{current['view_id']}.json"
    view = _load_json(view_path)
    temporal = len(view["records"]["temporal"])
    tectonic_states = []
    for state_id in view["records"]["states"]:
        state = _load_json(root / "states" / f"{state_id}.json")
        if state.get("domain") != "tectonic_geometry":
            continue
        value = state.get("value", {})
        time_support = state.get("time_support", {})
        tectonic_states.append({
            "state_id": state_id,
            "time_key": time_support.get("time_key"),
            "payload_ref": state.get("payload_ref"),
            "process_state": value.get("process_state"),
        })
    ages = sorted({row["time_key"] for row in tectonic_states if row["time_key"]})
    required = {row["state_id"]: row for row in tectonic_states}
    if temporal != 2 or len(ages) != 2:
        raise ValueError("canonical WORLD_HISTORY must retain exactly two temporal epochs")
    for state_id in (EXPECTED_PRE_STATE, EXPECTED_POST_STATE):
        if state_id not in required:
            raise ValueError(f"required canonical state is missing: {state_id}")
    if (required[EXPECTED_PRE_STATE]["time_key"] != "209.97287659484368Ma"
            or required[EXPECTED_POST_STATE]["time_key"] != "209.97287659484368Ma"
            or required[EXPECTED_PRE_STATE]["payload_ref"] != f"sha256:{EXPECTED_PAYLOAD_SHA256}"
            or required[EXPECTED_POST_STATE]["payload_ref"] != f"sha256:{EXPECTED_PAYLOAD_SHA256}"
            or required[EXPECTED_POST_STATE]["process_state"] != "RIFT_PROCESS_ACTIVE"):
        raise ValueError("canonical PRE/POST state identity, age, payload, or process state mismatch")
    if "210.0Ma" not in ages or "209.97287659484368Ma" not in ages:
        raise ValueError("canonical physical age set differs from the qualified T0/T1 ages")
    return {
        "read_only": True,
        "file_count": len(file_rows),
        "logical_bytes": sum(row[1] for row in file_rows),
        "tree_sha256": tree.hexdigest(),
        "view_id": view["view_id"],
        "view_sha256": hashlib.sha256(view_path.read_bytes()).hexdigest(),
        "canonical_temporal_record_count": temporal,
        "physical_epoch_count": len(ages),
        "physical_age_keys": ages,
        "pre_event_state_id": EXPECTED_PRE_STATE,
        "post_event_state_id": EXPECTED_POST_STATE,
        "payload_sha256": EXPECTED_PAYLOAD_SHA256,
        "t2_present": False,
    }


def build_decision(repo: Path, evidence_root: Path, canonical_root: Path) -> dict[str, Any]:
    branch = _git(repo, "branch", "--show-current")
    head = _git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        raise ValueError(f"source gate mismatch: branch={branch}; HEAD={head}")
    contracts = {
        "activation": _load_json(repo / "contracts/R6_RIFT_PROCESS_ACTIVATION_MODEL_V1.json"),
        "successor": _load_json(repo / "contracts/R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json"),
        "model_horizon": _load_json(repo / "contracts/R6_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1.json"),
        "second_dt_v1": _load_json(repo / "contracts/R6_SECOND_DT_AUTHORIZATION_AFTER_RIFT_V1.json"),
        "impact_policy": _load_json(repo / "contracts/R6_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY_V1.json"),
    }
    attestation = _load_json(repo / "docs/arcana/qualifications/R6_B6N4A_ATTESTATION.json")
    bundle = evidence_root / "B6N4A" / EXPECTED_B6N4A_SOURCE
    _verify_manifest(bundle)
    qualification = _load_json(bundle / "B6N4A_QUALIFICATION_RESULT.json")
    replay = _load_json(bundle / "B6N4A_SEVEN_UNKNOWN_ADJUDICATION.json")
    invariance = _load_json(bundle / "B6N4A_CANONICAL_INVARIANCE.json")
    if (attestation.get("qualified_source_commit") != EXPECTED_B6N4A_SOURCE
            or attestation.get("evidence_manifest_sha256") != EXPECTED_B6N4A_MANIFEST_SHA256
            or qualification.get("verdict") != "PASS_B6N4A_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY"
            or qualification.get("qualified_source_commit") != EXPECTED_B6N4A_SOURCE
            or replay.get("case_count") != 7 or not replay.get("repeatable")
            or not replay.get("semantic_results_match_development_prequalification")):
        raise ValueError("B6N4-A qualified evidence gate failed")
    expected_horizons = {
        "GENERIC_TOPOLOGY_EVENT_COVERAGE": ("INSUFFICIENT_IMPACT_BOUND", "UNKNOWN"),
        "JUNCTION_CONSISTENCY": ("INSUFFICIENT_IMPACT_BOUND", None),
        "MECHANICS_REQUIREMENT": ("NOT_APPLICABLE", None),
        "NEXT_RIFT_PROCESS_EVOLUTION": ("AUTHORITY_BLOCKED", "UNKNOWN"),
        "PLATE_INTERFACE_EVENT_PREDICATES": ("INSUFFICIENT_IMPACT_BOUND", "UNKNOWN"),
        "SOURCE_TEMPORAL_VALIDITY": ("AUTHORITY_BLOCKED", None),
        "SUPPORT_MEMBERSHIP_VALIDITY": ("INSUFFICIENT_IMPACT_BOUND", None),
    }
    actual_horizons = {
        row["assessment"]["subject_id"]: (
            row["significance_class"], row["assessment"]["event_occurrence"])
        for row in replay["adjudications"]
    }
    if actual_horizons != expected_horizons:
        raise ValueError("B6N4-A seven-horizon classification/occurrence mismatch")
    if (invariance.get("physical_epoch_count_before") != 2
            or invariance.get("physical_epoch_count_after") != 2
            or invariance.get("pre_event_state_id") != EXPECTED_PRE_STATE
            or invariance.get("post_event_state_id") != EXPECTED_POST_STATE
            or invariance.get("physical_payload_sha256") != EXPECTED_PAYLOAD_SHA256):
        raise ValueError("B6N4-A canonical invariance evidence mismatch")
    canonical = inspect_canonical_read_only(canonical_root)

    age = contracts["model_horizon"]["scope"]["physical_age_ma"]
    limit = contracts["model_horizon"]["derivation"]["horizon_delta_years"]
    if (age != EXPECTED_AGE_MA
            or contracts["model_horizon"]["scope"]["causal_origin_state_id"] != EXPECTED_POST_STATE
            or not contracts["model_horizon"]["b6n4_eligibility"]["limiting_eligible_for_dt_adjudication"]
            or contracts["successor"]["temporal_scope"]["source_temporal_support"] != "INSTANT_ONLY"
            or contracts["successor"]["second_dt_gate"]["SECOND_DT_SELECTED"] is not False):
        raise ValueError("post-event authority/horizon contract consistency check failed")
    if (contracts["second_dt_v1"].get("second_dt_authorized_by_this_contract") is not False
            or contracts["second_dt_v1"].get("t2_creation_authorized") is not False
            or "unknown" not in contracts["second_dt_v1"].get("failure_behavior", "").lower()
            or contracts["impact_policy"].get("current_policy_qualification", {}).get(
                "historical_B6N4_V1_authorization_changed") is not False):
        raise ValueError("frozen B6N4 V1 / B6N4-A policy gate consistency check failed")

    # UNKNOWN event occurrence is not automatically a blocker. These four
    # required dependencies block because impact/time bounds and isolation are
    # not governed for this complete plate-local geometry/kinematics output.
    dependencies = [
        {"id": "GENERIC_TOPOLOGY_EVENT_COVERAGE", "scope_role": "REQUIRED_FOR_REQUESTED_OUTPUT",
         "B6N4A_significance_class": "INSUFFICIENT_IMPACT_BOUND", "event_occurrence": "UNKNOWN",
         "applicability": "APPLICABLE", "authority_status": "AUTHORIZED",
         "impact_bound_status": "UNKNOWN", "dependency_status": "NOT_PROVEN",
         "required_invariant": "Plate geometry, identities, and represented topology remain within the frozen rigid scope.",
         "dependency_isolation": "NOT_PROVEN; B6N4-A policy therefore leaves the affected tectonic output scope global.",
         "positive_validity_interval": "UNKNOWN",
         "could_invalidate_before_model_scope_horizon": "UNKNOWN",
         "capability_governed": False,
         "evidence": "B6N4-A INSUFFICIENT_IMPACT_BOUND; topology/support events can change represented plate geometry and topology."},
        {"id": "JUNCTION_CONSISTENCY", "scope_role": "RELEVANT_NON_LIMITING_FOR_REQUESTED_OUTPUT",
         "B6N4A_significance_class": "INSUFFICIENT_IMPACT_BOUND", "event_occurrence": None,
         "applicability": "RELEVANT", "authority_status": "AUTHORIZED",
         "impact_bound_status": "UNKNOWN", "dependency_status": "NOT_PROVEN",
         "required_invariant": "Preserve the six set-valued junction identities and incidence; positional accommodation is outside requested outputs.",
         "dependency_isolation": "Not needed to authorize this output family because junction compatibility is not asserted or computed.",
         "positive_validity_interval": "NOT_APPLICABLE_TO_REQUESTED_OUTPUT",
         "could_invalidate_before_model_scope_horizon": "NO_FOR_CURRENT_RESTRICTED_RIGID_OUTPUT; physical compatibility remains UNKNOWN.",
         "capability_governed": "NOT_APPLICABLE_TO_CURRENT_REQUESTED_OUTPUT",
         "evidence": "B6N4-A states current restricted rigid kinematics alone is not invalidated; no junction accommodation/compatibility output is requested. Preserve set-valued incidence and UNKNOWN; do not assert geometric accommodation."},
        {"id": "MECHANICS_REQUIREMENT", "scope_role": "NOT_APPLICABLE_TO_REQUESTED_OUTPUT",
         "B6N4A_significance_class": "NOT_APPLICABLE", "event_occurrence": None,
         "applicability": "NOT_APPLICABLE", "authority_status": "NOT_REQUIRED",
         "impact_bound_status": "NOT_APPLICABLE", "dependency_status": "CLOSED",
         "required_invariant": "None; stress, strain, fault accommodation, and rheology are not requested.",
         "dependency_isolation": "NOT_APPLICABLE",
         "positive_validity_interval": "NOT_APPLICABLE",
         "could_invalidate_before_model_scope_horizon": "NO_WITHIN_DECLARED_OUTPUT_SCOPE",
         "capability_governed": "NOT_APPLICABLE",
         "evidence": "B6N2 restricts the requested output to rigid geometry/kinematics; mechanics is outside scope."},
        {"id": "NEXT_RIFT_PROCESS_EVOLUTION", "scope_role": "REQUIRED_FOR_REQUESTED_OUTPUT",
         "B6N4A_significance_class": "AUTHORITY_BLOCKED", "event_occurrence": "UNKNOWN",
         "applicability": "APPLICABLE", "authority_status": "NOT_AUTHORIZED",
         "impact_bound_status": "UNKNOWN", "dependency_status": "NOT_PROVEN",
         "required_invariant": "RIFT_PROCESS_ACTIVE remains the process context for the successor rigid kinematic model.",
         "dependency_isolation": "NOT_PROVEN; no governed predicate/time bound isolates process evolution from the requested geometry.",
         "positive_validity_interval": "UNKNOWN",
         "could_invalidate_before_model_scope_horizon": "UNKNOWN",
         "capability_governed": False,
         "evidence": "Activation V1 authorizes zero-duration activation only; no next predicate, threshold, opening law, or positive-time process isolation is governed."},
        {"id": "PLATE_INTERFACE_EVENT_PREDICATES", "scope_role": "REQUIRED_FOR_REQUESTED_OUTPUT",
         "B6N4A_significance_class": "INSUFFICIENT_IMPACT_BOUND", "event_occurrence": "UNKNOWN",
         "applicability": "APPLICABLE", "authority_status": "AUTHORIZED",
         "impact_bound_status": "UNKNOWN", "dependency_status": "NOT_PROVEN",
         "required_invariant": "The existing plate-interface identities and connectivity remain unchanged during the restricted candidate segment.",
         "dependency_isolation": "NOT_PROVEN; no enabled post-event detector proves unaffected interfaces independent.",
         "positive_validity_interval": "UNKNOWN",
         "could_invalidate_before_model_scope_horizon": "UNKNOWN",
         "capability_governed": False,
         "evidence": "B6N4-A INSUFFICIENT_IMPACT_BOUND; no post-event detector/bound for interface identity transitions."},
        {"id": "SOURCE_TEMPORAL_VALIDITY", "scope_role": "SOURCE_PROVENANCE_NOT_EXTENDED",
         "B6N4A_significance_class": "AUTHORITY_BLOCKED", "event_occurrence": None,
         "applicability": "RELEVANT_PROVENANCE_LIMIT", "authority_status": "UNKNOWN",
         "impact_bound_status": "UNKNOWN", "dependency_status": "CLOSED",
         "required_invariant": "Keep original 210 Ma Euler source validity instant-only; use only the separately authorized B6N2 successor model.",
         "dependency_isolation": "Source provenance is distinct from the successor model authority; no source interval is claimed.",
         "positive_validity_interval": "SOURCE_INTERVAL_UNKNOWN; SUCCESSOR_MODEL_SEPARATELY_AUTHORIZED_CONDITIONALLY",
         "could_invalidate_before_model_scope_horizon": "NOT_APPLICABLE_TO_SUCCESSOR_MODEL_AUTHORITY_AS_A_SEPARATE_SOURCE_CLAIM",
         "capability_governed": "NO_SOURCE_VALIDITY_EXTENSION",
         "evidence": "Original 210 Ma source remains INSTANT_ONLY/UNKNOWN beyond anchor; B6N2 independently authorizes a bounded successor model and does not extend source provenance."},
        {"id": "SUPPORT_MEMBERSHIP_VALIDITY", "scope_role": "REQUIRED_FOR_REQUESTED_OUTPUT",
         "B6N4A_significance_class": "INSUFFICIENT_IMPACT_BOUND", "event_occurrence": None,
         "applicability": "APPLICABLE", "authority_status": "AUTHORIZED",
         "impact_bound_status": "UNKNOWN", "dependency_status": "NOT_PROVEN",
         "required_invariant": "Support membership and plate-local representation identities remain exactly those of POST_EVENT.",
         "dependency_isolation": "NOT_PROVEN; support changes are tied to ungoverned topology/interface transitions.",
         "positive_validity_interval": "UNKNOWN",
         "could_invalidate_before_model_scope_horizon": "UNKNOWN",
         "capability_governed": False,
         "evidence": "B6N4-A INSUFFICIENT_IMPACT_BOUND; support validity is tied to ungoverned topology/interface events and no isolation is proven."},
        {"id": "SUCCESSOR_MODEL_SCOPE_REVALIDATION", "scope_role": "AUTHORIZED_FINITE_UPPER_BOUND_CANDIDATE",
         "applicability": "APPLICABLE", "authority_status": "AUTHORIZED",
         "impact_bound_status": "NOT_APPLICABLE", "dependency_status": "CLOSED",
         "positive_validity_years": limit,
         "required_invariant": "Renew/replace the successor model by the authored displacement-fraction model-scope limit.",
         "dependency_isolation": "This cap does not isolate physical events or process transitions.",
         "positive_validity_interval": limit,
         "could_invalidate_before_model_scope_horizon": "NOT_AN_EVENT_PREDICTION; it cannot bound earlier UNKNOWN event/process horizons.",
         "capability_governed": True,
         "evidence": "B6N3-A authorizes mandatory revalidation by this duration; it is not an event-free interval or resolution of the earlier unknowns."},
        {"id": "ASYNC_DOMAIN_VALIDITY", "scope_role": "NOT_APPLICABLE_TO_TECTONIC_KINEMATIC_OUTPUT",
         "applicability": "NOT_APPLICABLE", "authority_status": "NOT_REQUIRED",
         "impact_bound_status": "NOT_APPLICABLE", "dependency_status": "CLOSED",
         "required_invariant": "None; asynchronous domains are not consumed by this output.",
         "dependency_isolation": "NOT_APPLICABLE_BY_OUTPUT_DEPENDENCY_CLOSURE",
         "positive_validity_interval": "NOT_APPLICABLE",
         "could_invalidate_before_model_scope_horizon": "NO_FOR_CURRENT_REQUESTED_OUTPUT",
         "capability_governed": "NOT_APPLICABLE",
         "evidence": "B6N2 preserves asynchronous domains; no such domain is consumed by the restricted kinematic output."},
        {"id": "RIGID_ROTATION_NUMERICAL_STABILITY", "scope_role": "NOT_APPLICABLE_NO_GOVERNED_LIMIT",
         "applicability": "NOT_APPLICABLE", "authority_status": "NOT_REQUIRED",
         "impact_bound_status": "NOT_APPLICABLE", "dependency_status": "CLOSED",
         "required_invariant": "Use the frozen exact finite rigid-rotation action; no numerical solver stability output is requested.",
         "dependency_isolation": "NOT_APPLICABLE; B6F identifies no governed intrinsic ODE bound or angular accuracy threshold.",
         "positive_validity_interval": "NOT_APPLICABLE_AS_NUMERICAL_LIMIT",
         "could_invalidate_before_model_scope_horizon": "NO_GOVERNED_NUMERICAL_LIMIT_IDENTIFIED",
         "capability_governed": "NOT_APPLICABLE",
         "evidence": "B6F classifies exact rigid rotation as having no governed intrinsic ODE stability bound; no angular accuracy threshold is authored."},
    ]
    closure = evaluate_dependency_closure(dependencies, limit, [{
        "horizon_id": "FINITE_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1",
        "delta_time_years": limit,
        "authorized": True,
    }])
    result = {
        "schema": "ARCANA_R6_B6N4R1_SECOND_DT_READJUDICATION_V1",
        "stage": "B6N4-R1_SECOND_TIMESTEP_READJUDICATION",
        "baseline_branch": branch,
        "qualified_source_commit": head,
        "requested_output_family": "RESTRICTED_POST_EVENT_PLATE_LOCAL_RIGID_GEOMETRY_AND_KINEMATICS",
        "authority_inputs": {
            "B6N2_successor_model": "contracts/R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json",
            "B6N3A_model_scope_limit": "contracts/R6_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1.json",
            "B6N4A_policy": "contracts/R6_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY_V1.json",
            "B6N4A_attestation": "docs/arcana/qualifications/R6_B6N4A_ATTESTATION.json",
            "B6N4A_evidence_manifest_sha256": EXPECTED_B6N4A_MANIFEST_SHA256,
            "frozen_second_dt_contract_v1": "contracts/R6_SECOND_DT_AUTHORIZATION_AFTER_RIFT_V1.json",
        },
        "origin": {"state_id": EXPECTED_POST_STATE, "physical_age_ma": age,
                    "process_state": "RIFT_PROCESS_ACTIVE"},
        "canonical_state_read_only_snapshot": canonical,
        "dependency_closure": dependencies,
        "decision": closure,
        "limiting_horizon": {
            "candidate_id": "FINITE_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1",
            "candidate_delta_years": limit,
            "candidate_endpoint_age_ma": age - limit / 1_000_000,
            "role": "AUTHORIZED_MODEL_SCOPE_UPPER_BOUND_ONLY",
            "actual_nearest_limiter": closure["nearest_authorized_limiter"],
        },
        "authority_distinctions": {
            "source_temporal_validity": "UNKNOWN_BEYOND_INSTANT_ANCHOR; NOT_EXTENDED",
            "successor_model_authority": "INDEPENDENT_B6N2_AUTHORITY_WITH_B6N3A_REVALIDATION_CAP; DOES_NOT_RESOLVE_EARLIER_EVENT_OR_PROCESS_BOUNDARIES",
        },
        "v1_contract": {
            "path": "contracts/R6_SECOND_DT_AUTHORIZATION_AFTER_RIFT_V1.json",
            "preserved_unchanged": True,
            "decision": "NO_V2_REQUIRED_WHILE_NO_TIMESTEP_PERMISSION_IS_CHANGED; V1_FAIL_CLOSED_RULE_STILL_MATCHES_THIS_BLOCKED_RESULT",
        },
        "preserved_gates": {
            "SECOND_DT_SELECTED": False, "target_age_ma": None, "T2_CREATED": False,
            "canonical_physical_epochs": 2, "mechanics_executed": False,
            "forward_propagation_executed": False, "topology_transition_executed": False,
        },
        "verdict": "BLOCKED_B6N4R1_RELEVANT_AUTHORITY_UNRESOLVED",
        "next_stage": "STOP; B6O_NOT_AUTHORIZED",
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path,
                        default=Path(os.environ["ARCANA_WORLD_HISTORY_ROOT"])
                        if os.environ.get("ARCANA_WORLD_HISTORY_ROOT") else None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.canonical_root is None:
        parser.error("--canonical-root or ARCANA_WORLD_HISTORY_ROOT is required")
    try:
        result = build_decision(args.repo_root.resolve(), args.evidence_root.resolve(), args.canonical_root.resolve())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"B6N4-R1 FAIL CLOSED: {exc}", file=sys.stderr)
        return 2
    print(result["verdict"])
    print(f"positive_propagation_established={result['decision']['positive_propagation_established']}")
    print(f"SECOND_DT_SELECTED={result['decision']['SECOND_DT_SELECTED']}")
    print(f"T2_CREATED={result['decision']['T2_CREATED']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
