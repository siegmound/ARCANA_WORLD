from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path("R5_16_LEGACY_RECONCILIATION_AUDIT.json")
PARENT_CHAIN_PATH = Path("R5_16_PARENT_CHAIN_AUDIT.json")

EXPECTED_BRANCH = "main"
EXPECTED_SOURCE_COMMIT = "adfbbf5ee8769b742475824782d69a3815387069"

CENSUS_PATH = Path("R5_15_R3_34_TO_R3_39_CENSUS_PASS2.json")
REUSE_PATH = Path("R5_15_REUSE_CLASSIFICATION_PASS2.json")
GAP_PATH = Path("R5_15_GAP_REGISTER_PASS2.json")
FINAL_AUDIT_PATH = Path("R5_15_FINAL_AUDIT_PASS2.json")

STAGES = tuple(range(34, 40))
EXPECTED_SCOPE = [f"R3.{n}" for n in STAGES]
EXPECTED_CHECK_COUNTS = {
    34: 25,
    35: 29,
    36: 32,
    37: 38,
    38: 44,
    39: 40,
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def repo_root() -> Path:
    return Path(git_text("rev-parse", "--show-toplevel")).resolve()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot parse JSON {path}: {exc}") from exc


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_pass_count(value: Any) -> tuple[int | None, int | None]:
    if not isinstance(value, str):
        return None, None
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s+PASS\s*", value)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def final_seal_path(stage_number: int) -> Path:
    return Path(
        f"outputs/v0_6D1_R3_{stage_number}_SEAL/"
        f"R3_{stage_number}_FINAL_SEAL_AUDIT.json"
    )


def write_blocked(branch: str, head: str, gaps: list[str]) -> None:
    result = {
        "schema": "ARCANA_R5_16_LEGACY_RECONCILIATION_AUDIT_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-C",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": head,
        "legacy_reconciliation_integrity": False,
        "open_legacy_reconciliation_gap_count": len(gaps),
        "open_legacy_reconciliation_gaps": gaps,
        "status": "BLOCKED_R516_LEGACY_RECONCILIATION_AUDIT",
        "next_if_pass": "R5.16-D_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT",
    }
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {head}")
    print(f"OPEN_LEGACY_RECONCILIATION_GAPS = {len(gaps)}")
    print(f"STATUS = {result['status']}")


def main() -> None:
    root = repo_root()
    os.chdir(root)

    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    head = git_text("rev-parse", "HEAD")

    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}")

    if head != EXPECTED_SOURCE_COMMIT:
        raise SystemExit(
            "R5.16-C is bound to the completed R5.16-B repository snapshot.\n"
            f"Expected HEAD: {EXPECTED_SOURCE_COMMIT}\n"
            f"Found HEAD:    {head}"
        )

    tracked_dirty = git_text("status", "--porcelain", "--untracked-files=no")
    if tracked_dirty:
        raise SystemExit(
            "Tracked working tree is not clean. Commit/stash tracked changes before R5.16-C:\n"
            + tracked_dirty
        )

    gaps: list[str] = []

    if not PARENT_CHAIN_PATH.is_file():
        raise SystemExit(f"Missing prerequisite {PARENT_CHAIN_PATH}")

    parent_chain = load_json(PARENT_CHAIN_PATH)
    parent_prerequisite_ok = (
        parent_chain.get("stage") == "v0.6D1-R5.16"
        and parent_chain.get("subphase") == "R5.16-B"
        and parent_chain.get("status") == "PASS_R516_PARENT_CHAIN_AUDIT"
        and parent_chain.get("parent_chain_integrity") is True
        and parent_chain.get("open_parent_chain_gap_count") == 0
        and parent_chain.get("continuation_edge_count_verified") == 8
        and parent_chain.get("legacy_dependencies_explicit") is True
    )
    if not parent_prerequisite_ok:
        gaps.append("PARENT_CHAIN_PREREQUISITE_NOT_PASS")

    required = {
        "census_pass2": CENSUS_PATH,
        "reuse_classification_pass2": REUSE_PATH,
        "gap_register_pass2": GAP_PATH,
        "final_audit_pass2": FINAL_AUDIT_PATH,
    }
    for label, path in required.items():
        if not path.is_file():
            gaps.append(f"MISSING_{label.upper()}:{path}")

    if gaps:
        write_blocked(branch, head, gaps)
        raise SystemExit(1)

    census = load_json(CENSUS_PATH)
    reuse = load_json(REUSE_PATH)
    gap = load_json(GAP_PATH)
    final_audit = load_json(FINAL_AUDIT_PATH)

    census_checks = {
        "stage_exact": census.get("stage") == "v0.6D1-R5.15",
        "pass_exact": census.get("pass") == "CENSUS_PASS_2",
        "status_exact":
            census.get("status") == "PASS_REPOSITORY_BOUND_PROVENANCE_RECOVERED",
        "scope_exact": census.get("scope") == EXPECTED_SCOPE,
        "scientific_incompatibilities_zero":
            census.get("scientific_incompatibilities") == 0,
        "new_simulation_not_required":
            census.get("new_simulation_required") is False,
        "external_engine_execution_not_required":
            census.get("external_engine_execution_required") is False,
    }
    if not all(census_checks.values()):
        gaps.append(
            "CENSUS_PASS2_FAILED:"
            + ",".join(k for k, v in census_checks.items() if not v)
        )

    reuse_checks = {
        "stage_exact": reuse.get("stage") == "v0.6D1-R5.15",
        "classification_pass_exact": reuse.get("classification_pass") == 2,
        "status_exact": reuse.get("status") == "PASS_EXACT_SEALED_ARTIFACT_REUSE",
        "counts_exact":
            reuse.get("counts") == {"A": 6, "B": 0, "C": 0, "D": 0},
        "scientific_incompatibility_zero":
            reuse.get("scientific_incompatibility_proven") == 0,
        "new_simulation_not_authorized":
            reuse.get("new_simulation_authorized") is False,
        "external_runtime_not_authorized":
            reuse.get("external_runtime_authorized") is False,
        "repair_block_not_required":
            reuse.get("repair_block_required") is False,
    }
    if not all(reuse_checks.values()):
        gaps.append(
            "REUSE_PASS2_FAILED:"
            + ",".join(k for k, v in reuse_checks.items() if not v)
        )

    gap_checks = {
        "stage_exact": gap.get("stage") == "v0.6D1-R5.15",
        "pass_exact": gap.get("pass") == "GAP_REGISTER_PASS_2",
        "status_closed": gap.get("status") == "CLOSED",
        "remaining_provenance_gaps_zero":
            gap.get("remaining_provenance_gaps") == [],
        "scientific_gaps_zero": gap.get("scientific_gaps_proven") == 0,
        "simulation_repair_not_needed":
            gap.get("simulation_repair_needed") is False,
        "external_engine_execution_not_needed":
            gap.get("external_engine_execution_needed") is False,
        "r516_repair_not_authorized":
            gap.get("r5_16_repair_block_authorized") is False,
    }
    if not all(gap_checks.values()):
        gaps.append(
            "GAP_REGISTER_PASS2_FAILED:"
            + ",".join(k for k, v in gap_checks.items() if not v)
        )

    final_checks_obj = final_audit.get("checks")
    final_all_checks_true = (
        isinstance(final_checks_obj, dict)
        and bool(final_checks_obj)
        and all(v is True for v in final_checks_obj.values())
    )
    final_audit_checks = {
        "stage_exact": final_audit.get("stage") == "v0.6D1-R5.15",
        "audit_exact":
            final_audit.get("audit") == "BULK_LEGACY_RECONCILIATION_PASS_2",
        "status_candidate":
            final_audit.get("status")
            == "PASS_R515_R334_TO_R339_BULK_LEGACY_RECONCILIATION_CANDIDATE",
        "all_checks_true": final_all_checks_true,
        "completed": final_audit.get("r5_15_completed") is True,
        "candidate_not_sealed":
            final_audit.get("r5_15_status") == "CANDIDATE"
            and final_audit.get("r5_15_sealed") is False,
        "repair_not_required":
            final_audit.get("repair_block_required") is False,
    }
    if not all(final_audit_checks.values()):
        gaps.append(
            "R515_FINAL_AUDIT_PASS2_FAILED:"
            + ",".join(k for k, v in final_audit_checks.items() if not v)
        )

    census_stages = census.get("stages")
    reuse_classes = reuse.get("classes")
    if not isinstance(census_stages, dict):
        census_stages = {}
        gaps.append("CENSUS_STAGE_MAP_MISSING")
    if not isinstance(reuse_classes, dict):
        reuse_classes = {}
        gaps.append("REUSE_CLASS_MAP_MISSING")

    stage_results: list[dict[str, Any]] = []

    for n in STAGES:
        stage_id = f"R3.{n}"
        stage_token = f"v0.6D1-R3.{n}"
        seal_path = final_seal_path(n)
        census_entry = census_stages.get(stage_id)
        reuse_entry = reuse_classes.get(stage_id)

        failures: list[str] = []
        result: dict[str, Any] = {
            "stage": stage_id,
            "final_seal_audit_path": seal_path.as_posix(),
            "status": "BLOCKED",
        }

        if not isinstance(census_entry, dict):
            failures.append("CENSUS_ENTRY_MISSING")
            census_entry = {}
        if not isinstance(reuse_entry, dict):
            failures.append("REUSE_ENTRY_MISSING")
            reuse_entry = {}

        expected_artifact_dir = Path(f"outputs/v0_6D1_R3_{n}")
        expected_seal_dir = Path(f"outputs/v0_6D1_R3_{n}_SEAL")

        artifact_dir_ok = expected_artifact_dir.is_dir()
        seal_dir_ok = expected_seal_dir.is_dir()
        seal_file_ok = seal_path.is_file()

        if not artifact_dir_ok:
            failures.append("ARTIFACT_DIRECTORY_MISSING")
        if not seal_dir_ok:
            failures.append("SEAL_DIRECTORY_MISSING")
        if not seal_file_ok:
            failures.append("FINAL_SEAL_AUDIT_MISSING")

        census_paths_exact = (
            census_entry.get("artifact_directory") == expected_artifact_dir.as_posix()
            and census_entry.get("seal_directory") == expected_seal_dir.as_posix()
            and census_entry.get("final_seal_audit") == seal_path.as_posix()
        )
        if not census_paths_exact:
            failures.append("CENSUS_PATH_BINDING_MISMATCH")

        class_a_exact = (
            reuse_entry.get("class") == "A"
            and reuse_entry.get("subtype") == "A_EXACT_SEALED_ARTIFACT_REUSE"
        )
        if not class_a_exact:
            failures.append("REUSE_CLASS_NOT_EXACT_A")

        if seal_file_ok:
            seal = load_json(seal_path)
            actual_digest = sha256(seal_path)
            checks = seal.get("checks")
            check_list_valid = isinstance(checks, list) and bool(checks)
            all_seal_checks_pass = (
                check_list_valid
                and all(
                    isinstance(item, dict) and item.get("pass") is True
                    for item in checks
                )
            )

            expected_count = EXPECTED_CHECK_COUNTS[n]
            reported_passed = seal.get("checks_passed")
            reported_total = seal.get("checks_total")
            reported_failed = seal.get("checks_failed")

            census_passed, census_total = parse_pass_count(
                census_entry.get("final_checks")
            )

            seal_stage_exact = seal.get("stage") == stage_token
            seal_status = seal.get("status")
            seal_status_matches_census = (
                seal_status == census_entry.get("final_seal_status")
            )
            explicit_sealed = (
                seal.get("verdict") == "SEALED"
                and isinstance(seal_status, str)
                and seal_status.endswith("_SEALED")
            )
            counts_exact = (
                reported_passed == expected_count
                and reported_total == expected_count
                and reported_failed == 0
                and census_passed == expected_count
                and census_total == expected_count
                and check_list_valid
                and len(checks) == expected_count
            )

            if not seal_stage_exact:
                failures.append("FINAL_SEAL_STAGE_MISMATCH")
            if not seal_status_matches_census:
                failures.append("FINAL_SEAL_STATUS_CENSUS_MISMATCH")
            if not explicit_sealed:
                failures.append("FINAL_SEAL_NOT_EXPLICIT")
            if not counts_exact:
                failures.append("FINAL_SEAL_CHECK_COUNT_MISMATCH")
            if not all_seal_checks_pass:
                failures.append("FINAL_SEAL_CHECK_FAILURE")

            result.update(
                {
                    "final_seal_sha256": actual_digest,
                    "sha256_well_formed": bool(HEX64.fullmatch(actual_digest)),
                    "final_seal_status": seal_status,
                    "verdict": seal.get("verdict"),
                    "checks_passed": reported_passed,
                    "checks_total": reported_total,
                    "checks_failed": reported_failed,
                    "all_final_seal_checks_pass": all_seal_checks_pass,
                    "census_final_checks": census_entry.get("final_checks"),
                    "census_final_seal_status":
                        census_entry.get("final_seal_status"),
                    "key_findings": census_entry.get("key_findings"),
                    "final_seal_summary": seal.get("summary"),
                }
            )

        result.update(
            {
                "artifact_directory_present": artifact_dir_ok,
                "seal_directory_present": seal_dir_ok,
                "census_paths_exact": census_paths_exact,
                "reuse_class": reuse_entry.get("class"),
                "reuse_subtype": reuse_entry.get("subtype"),
                "reuse_basis": reuse_entry.get("basis"),
                "failures": failures,
            }
        )

        if not failures:
            result["status"] = "PASS"
        else:
            gaps.extend(f"{stage_id}:{failure}" for failure in failures)

        stage_results.append(result)

    stages_verified = sum(1 for x in stage_results if x.get("status") == "PASS")

    legacy_reconciliation_integrity = (
        parent_prerequisite_ok
        and all(census_checks.values())
        and all(reuse_checks.values())
        and all(gap_checks.values())
        and all(final_audit_checks.values())
        and stages_verified == 6
        and not gaps
    )

    output = {
        "schema": "ARCANA_R5_16_LEGACY_RECONCILIATION_AUDIT_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-C",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": head,
        "prerequisite": {
            "path": PARENT_CHAIN_PATH.as_posix(),
            "status": parent_chain.get("status"),
            "parent_chain_integrity": parent_chain.get("parent_chain_integrity"),
            "open_parent_chain_gap_count":
                parent_chain.get("open_parent_chain_gap_count"),
            "continuation_edge_count_verified":
                parent_chain.get("continuation_edge_count_verified"),
            "legacy_dependencies_explicit":
                parent_chain.get("legacy_dependencies_explicit"),
            "pass": parent_prerequisite_ok,
        },
        "method": {
            "r515_pass2_cross_artifact_consistency_checked": True,
            "six_repository_final_seal_audits_directly_verified": True,
            "census_paths_bound_to_repository_layout": True,
            "final_seal_status_and_check_counts_cross_checked": True,
            "class_A_exact_sealed_artifact_reuse_required_for_all_six": True,
            "fresh_rerun_required": False,
            "external_engine_execution": False,
            "automatic_repair": False,
            "canonical_mutation": False,
            "seal_action": False,
            "negative_result_final_adjudication": False,
            "human_lineage_governance_final_adjudication": False,
            "negative_and_human_governance_deferred_to":
                "R5.16-D_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT",
            "numerical_replay_final_adjudication": False,
            "external_engine_governance_final_adjudication": False,
        },
        "r5_15_pass2": {
            "census": {
                "path": CENSUS_PATH.as_posix(),
                "sha256": sha256(CENSUS_PATH),
                "checks": census_checks,
            },
            "reuse_classification": {
                "path": REUSE_PATH.as_posix(),
                "sha256": sha256(REUSE_PATH),
                "checks": reuse_checks,
                "counts": reuse.get("counts"),
            },
            "gap_register": {
                "path": GAP_PATH.as_posix(),
                "sha256": sha256(GAP_PATH),
                "checks": gap_checks,
            },
            "final_audit": {
                "path": FINAL_AUDIT_PATH.as_posix(),
                "sha256": sha256(FINAL_AUDIT_PATH),
                "checks": final_audit_checks,
                "result_counts": final_audit.get("result_counts"),
            },
        },
        "scope": EXPECTED_SCOPE,
        "stages": stage_results,
        "stages_expected": 6,
        "stages_verified": stages_verified,
        "reuse_class_counts": reuse.get("counts"),
        "scientific_incompatibility_count":
            census.get("scientific_incompatibilities"),
        "new_simulation_required": census.get("new_simulation_required"),
        "external_engine_execution_required":
            census.get("external_engine_execution_required"),
        "repair_block_required": reuse.get("repair_block_required"),
        "legacy_reconciliation_integrity": legacy_reconciliation_integrity,
        "open_legacy_reconciliation_gap_count": len(gaps),
        "open_legacy_reconciliation_gaps": gaps,
        "status": (
            "PASS_R516_LEGACY_RECONCILIATION_AUDIT"
            if legacy_reconciliation_integrity
            else "BLOCKED_R516_LEGACY_RECONCILIATION_AUDIT"
        ),
        "next_if_pass": "R5.16-D_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT",
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {head}")
    for item in stage_results:
        print(
            f"{item['stage']}: {item['status']} "
            f"checks={item.get('checks_passed')}/{item.get('checks_total')} "
            f"class={item.get('reuse_class')}"
        )
    print(f"STAGES_VERIFIED = {stages_verified}/6")
    print(f"REUSE_CLASS_COUNTS = {reuse.get('counts')}")
    print(
        "SCIENTIFIC_INCOMPATIBILITIES = "
        f"{census.get('scientific_incompatibilities')}"
    )
    print(
        "NEW_SIMULATION_REQUIRED = "
        f"{census.get('new_simulation_required')}"
    )
    print(
        "EXTERNAL_ENGINE_EXECUTION_REQUIRED = "
        f"{census.get('external_engine_execution_required')}"
    )
    print(f"OPEN_LEGACY_RECONCILIATION_GAPS = {len(gaps)}")
    print(f"STATUS = {output['status']}")

    if not legacy_reconciliation_integrity:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
