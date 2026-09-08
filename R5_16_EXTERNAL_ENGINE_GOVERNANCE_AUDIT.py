from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path("R5_16_EXTERNAL_ENGINE_GOVERNANCE_AUDIT.json")
PREREQUISITE_PATH = Path("R5_16_NEGATIVE_RESULT_PRESERVATION.json")
R515_PATH = Path("R5_15_FINAL_AUDIT_PASS2.json")

EXPECTED_BRANCH = "main"
EXPECTED_SOURCE_COMMIT = "3f9c7d4428fc94daa6a70a87da6cb7524fc46a80"

INTEGRATED = {
    8: Path("outputs/v0_6D1_R5_8/R5_8_INTEGRATED_RECONCILIATION.json"),
    9: Path("outputs/v0_6D1_R5_9/R5_9_INTEGRATED_RECONCILIATION.json"),
    10: Path("outputs/v0_6D1_R5_10/R5_10_INTEGRATED_RECONCILIATION.json"),
    11: Path("outputs/v0_6D1_R5_11/R5_11_INTEGRATED_RECONCILIATION.json"),
    12: Path("outputs/v0_6D1_R5_12/R5_12_INTEGRATED_RECONCILIATION.json"),
    13: Path("outputs/v0_6D1_R5_13/R5_13_INTEGRATED_RECONCILIATION.json"),
    14: Path("outputs/v0_6D1_R5_14/R5_14_INTEGRATED_RECONCILIATION.json"),
}

RUNTIME = {
    9: Path("outputs/v0_6D1_R5_9/R5_9_RUNTIME_UTILITY_REVIEW.json"),
    10: Path("outputs/v0_6D1_R5_10/R5_10_RUNTIME_UTILITY_REVIEW.json"),
    11: Path("outputs/v0_6D1_R5_11/R5_11_RUNTIME_UTILITY_REVIEW.json"),
    12: Path("outputs/v0_6D1_R5_12/R5_12_RUNTIME_UTILITY_REVIEW.json"),
    13: Path("outputs/v0_6D1_R5_13/R5_13_RUNTIME_UTILITY_REVIEW.json"),
    14: Path("outputs/v0_6D1_R5_14/R5_14_RUNTIME_UTILITY_REVIEW.json"),
}

EXPECTED_RUNTIME_STATUS = {
    9: "PASS_R59_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED",
    10: "PASS_R510_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED",
    11: "PASS_R511_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED",
    12: "PASS_R512_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED",
    13: "PASS_R513_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED",
    14: "NO_NEW_EXTERNAL_ENGINE_REQUIRED",
}

NUMERICAL_CHECKS = {
    8: [
        "r327_age_axis_exact_3ma_to_200ka_141_states",
        "r55_age_axis_exactly_matches_r327",
        "r56_schedule_class_recomputed_exact",
        "direct_events_align_to_r327_macrostep_axis",
    ],
    9: [
        "r328_age_axis_exact",
        "r328_state_variable_names_exact",
        "r328_summary_geometry_exact",
        "r58_handoff_boundary_exact",
    ],
    10: [
        "r329_age_axis_exact_r328_subset_50ka_to_0",
        "r329_anchor_age_axis_exact_r328_snapshots",
        "r329_anchor_geometry_exact",
        "r329_candidate_order_exact",
    ],
    11: [
        "r330_age_axis_exact_r329",
        "r330_full_census_group_series_recomputed_exact",
        "r330_history_census_matches_timeseries",
        "r330_history_group_count_matches_timeseries",
    ],
    12: [
        "r331_deterministic_domain_stock_replay_exact",
        "r331_deterministic_ecology_replay_exact",
        "r331_deterministic_group_anchor_replay_exact",
        "r331_frozen_dynamics_exact",
    ],
    13: [
        "r332_deterministic_ecology_replay_exact",
        "r332_deterministic_regional_anchor_replay_exact",
        "r332_deterministic_stock_replay_exact",
        "r332_deterministic_transition_pockets_exact",
        "r332_frozen_dynamics_exact",
    ],
    14: [
        "align::checkpoint_recomputed_exact",
        "align::environment_replay_exact",
        "align::outcomes_recomputed_exact",
        "align::sensitivity_recomputed_exact",
        "align::stage_replay_exact",
        "align::trajectory_replay_within_one_float64_epsilon",
    ],
}


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed ({proc.returncode}):\n{proc.stderr}"
        )
    return proc


def git_text(*args: str) -> str:
    return run_git(*args).stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot parse JSON {path}: {exc}") from exc


def check_snapshot_binding(paths: list[Path], gaps: list[str]) -> None:
    ancestor = run_git(
        "merge-base", "--is-ancestor", EXPECTED_SOURCE_COMMIT, "HEAD", check=False
    )
    if ancestor.returncode != 0:
        gaps.append("SOURCE_COMMIT_NOT_ANCESTOR_OF_HEAD")
        return
    for path in paths:
        proc = run_git(
            "diff", "--quiet", EXPECTED_SOURCE_COMMIT, "--", path.as_posix(), check=False
        )
        if proc.returncode != 0:
            gaps.append(f"INPUT_DRIFT_SINCE_SOURCE_COMMIT:{path.as_posix()}")


def main() -> None:
    root = Path(git_text("rev-parse", "--show-toplevel")).resolve()
    os.chdir(root)

    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    head = git_text("rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}")

    gaps: list[str] = []
    required_paths = [PREREQUISITE_PATH, R515_PATH, *INTEGRATED.values(), *RUNTIME.values()]
    for path in required_paths:
        if not path.is_file():
            gaps.append(f"MISSING_REQUIRED_INPUT:{path.as_posix()}")

    if not gaps:
        check_snapshot_binding(required_paths, gaps)

    prerequisite = load_json(PREREQUISITE_PATH) if PREREQUISITE_PATH.is_file() else {}
    prereq_ok = (
        prerequisite.get("stage") == "v0.6D1-R5.16"
        and prerequisite.get("subphase") == "R5.16-D"
        and prerequisite.get("status")
        == "PASS_R516_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT"
        and prerequisite.get("negative_results_preserved") is True
        and prerequisite.get("human_lineage_governance_preserved") is True
        and prerequisite.get("open_negative_or_governance_gap_count") == 0
    )
    if not prereq_ok:
        gaps.append("R516_D_PREREQUISITE_NOT_PASS")

    numerical: dict[str, Any] = {}
    external: dict[str, Any] = {}

    for n, path in INTEGRATED.items():
        if not path.is_file():
            continue
        obj = load_json(path)
        checks = obj.get("checks") if isinstance(obj.get("checks"), dict) else {}
        summary = obj.get("summary") if isinstance(obj.get("summary"), dict) else {}

        missing_numeric = [key for key in NUMERICAL_CHECKS[n] if checks.get(key) is not True]
        truth_scope_ok = summary.get("numeric_historical_truth_claimed") is False
        if missing_numeric:
            gaps.extend(f"R5.{n}:NUMERICAL_CHECK_FAILED:{key}" for key in missing_numeric)
        if not truth_scope_ok:
            gaps.append(f"R5.{n}:NUMERIC_TRUTH_SCOPE_NOT_PRESERVED")

        numerical[f"r5_{n}"] = {
            "required_checks": NUMERICAL_CHECKS[n],
            "all_required_checks_pass": not missing_numeric,
            "numeric_historical_truth_claimed": summary.get("numeric_historical_truth_claimed"),
            "truth_scope_preserved": truth_scope_ok,
        }

        new_engine_ok = checks.get("no_new_external_engine_execution") is True
        if not new_engine_ok:
            gaps.append(f"R5.{n}:NEW_EXTERNAL_ENGINE_EXECUTION_NOT_EXPLICITLY_FALSE")
        external[f"r5_{n}"] = {
            "no_new_external_engine_execution": new_engine_ok,
        }

    r58 = load_json(INTEGRATED[8]) if INTEGRATED[8].is_file() else {}
    r58_checks = r58.get("checks") if isinstance(r58.get("checks"), dict) else {}
    r58_governance = (
        r58_checks.get("derived_refinement_not_promoted") is True
        and r58_checks.get("slim_ancestry_not_realized_history") is True
        and r58_checks.get("contact_opportunity_not_realized_gene_flow") is True
    )
    if not r58_governance:
        gaps.append("R5.8:INHERITED_EXTERNAL_EVIDENCE_ROLE_NOT_PRESERVED")
    external["r5_8"].update(
        {
            "derived_refinement_not_promoted": r58_checks.get("derived_refinement_not_promoted"),
            "slim_ancestry_not_realized_history": r58_checks.get("slim_ancestry_not_realized_history"),
            "contact_opportunity_not_realized_gene_flow": r58_checks.get("contact_opportunity_not_realized_gene_flow"),
        }
    )

    for n, path in RUNTIME.items():
        if not path.is_file():
            continue
        obj = load_json(path)
        status_ok = obj.get("status") == EXPECTED_RUNTIME_STATUS[n]
        if n == 14:
            execution_ok = (
                obj.get("external_engines_rerun") == []
                and obj.get("artifact_mutation") is False
                and obj.get("r333_scientific_rerun") is False
            )
        else:
            execution_ok = obj.get("new_external_engine_execution_performed") is False
        if not status_ok:
            gaps.append(f"R5.{n}:RUNTIME_REVIEW_STATUS_MISMATCH")
        if not execution_ok:
            gaps.append(f"R5.{n}:RUNTIME_EXECUTION_GOVERNANCE_FAILED")
        external[f"r5_{n}"].update(
            {
                "runtime_review_status": obj.get("status"),
                "runtime_review_status_ok": status_ok,
                "runtime_execution_governance_ok": execution_ok,
            }
        )

    r515 = load_json(R515_PATH) if R515_PATH.is_file() else {}
    r515_checks = r515.get("checks") if isinstance(r515.get("checks"), dict) else {}
    r515_ok = (
        r515.get("status")
        == "PASS_R515_R334_TO_R339_BULK_LEGACY_RECONCILIATION_CANDIDATE"
        and r515_checks.get("parent_hash_exactness_preserved") is True
        and r515_checks.get("output_manifest_closure_preserved") is True
        and r515_checks.get("external_runtime_not_required") is True
        and r515_checks.get("new_simulation_not_required") is True
        and r515_checks.get("auto_seal_not_performed") is True
    )
    if not r515_ok:
        gaps.append("R5.15:SEALED_REUSE_OR_RUNTIME_GOVERNANCE_FAILED")
    numerical["r5_15"] = {
        "claim_mode": "EXACT_SEALED_ARTIFACT_REUSE_AND_HASH_BOUND_RECONCILIATION",
        "fresh_numerical_replay_claimed": False,
        "supported": r515_ok,
    }
    external["r5_15"] = {
        "external_runtime_not_required": r515_checks.get("external_runtime_not_required"),
        "new_simulation_not_required": r515_checks.get("new_simulation_not_required"),
    }

    r514_num = numerical.get("r5_14", {})
    r514_num["trajectory_claim_mode"] = "WITHIN_ONE_FLOAT64_EPSILON"
    r514_num["trajectory_tolerance_not_upgraded_to_exact"] = (
        "align::trajectory_replay_within_one_float64_epsilon"
        in r514_num.get("required_checks", [])
        and r514_num.get("all_required_checks_pass") is True
    )
    numerical["r5_14"] = r514_num

    numerical_supported = (
        all(item.get("all_required_checks_pass") is True and item.get("truth_scope_preserved") is True
            for key, item in numerical.items() if key != "r5_15")
        and numerical.get("r5_15", {}).get("supported") is True
        and numerical.get("r5_14", {}).get("trajectory_tolerance_not_upgraded_to_exact") is True
    )
    external_preserved = not any(
        "ENGINE" in gap or "RUNTIME" in gap or "EXTERNAL_EVIDENCE" in gap
        for gap in gaps
    ) and r58_governance and r515_ok

    output = {
        "schema": "ARCANA_R5_16_NUMERICAL_REPLAY_EXTERNAL_ENGINE_GOVERNANCE_AUDIT_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-E",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "execution_head": head,
        "prerequisite": {
            "path": PREREQUISITE_PATH.as_posix(),
            "status": prerequisite.get("status"),
            "negative_results_preserved": prerequisite.get("negative_results_preserved"),
            "human_lineage_governance_preserved": prerequisite.get("human_lineage_governance_preserved"),
            "pass": prereq_ok,
        },
        "method": {
            "integrated_completion_artifacts_checked": True,
            "r5_9_to_r5_14_runtime_utility_reviews_checked": True,
            "r5_15_pass2_governance_checked": True,
            "exact_and_tolerance_claims_separated": True,
            "fresh_scientific_rerun": False,
            "external_engine_execution": False,
            "automatic_repair": False,
            "canonical_mutation": False,
            "seal_action": False,
        },
        "numerical_replay": numerical,
        "numerical_replay_claims_supported": numerical_supported,
        "external_engine_governance": external,
        "external_engine_governance_preserved": external_preserved,
        "engine_as_canonical_writer_detected": False if external_preserved else None,
        "engine_majority_vote_detected": False if external_preserved else None,
        "open_numerical_or_engine_governance_gap_count": len(gaps),
        "open_numerical_or_engine_governance_gaps": gaps,
        "status": (
            "PASS_R516_NUMERICAL_REPLAY_AND_EXTERNAL_ENGINE_GOVERNANCE_AUDIT"
            if prereq_ok and numerical_supported and external_preserved and not gaps
            else "BLOCKED_R516_NUMERICAL_REPLAY_AND_EXTERNAL_ENGINE_GOVERNANCE_AUDIT"
        ),
        "next_if_pass": "R5.16-F_INTEGRATED_AUDIT",
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {EXPECTED_SOURCE_COMMIT}")
    print(f"EXECUTION_HEAD = {head}")
    print(f"NUMERICAL_REPLAY_CLAIMS_SUPPORTED = {numerical_supported}")
    print(f"EXTERNAL_ENGINE_GOVERNANCE_PRESERVED = {external_preserved}")
    print(f"OPEN_GAPS = {len(gaps)}")
    print(f"STATUS = {output['status']}")

    if output["status"].startswith("BLOCKED_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
