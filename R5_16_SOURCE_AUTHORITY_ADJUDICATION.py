from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path("R5_16_SOURCE_AUTHORITY.json")
INVENTORY_PATH = Path("R5_16_SOURCE_AUTHORITY_INVENTORY.json")

EXPECTED_BRANCH = "main"
EXPECTED_A1_COMMIT = "7b25d57a599c513b8404c0aeaf5693cfc77ac3e8"
STAGES = tuple(range(8, 16))


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


def current_git_entries() -> dict[str, dict[str, Any]]:
    raw = subprocess.run(
        ["git", "ls-files", "-s", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if raw.returncode != 0:
        raise SystemExit(
            raw.stderr.decode("utf-8", errors="replace")
        )

    out: dict[str, dict[str, Any]] = {}
    for record in raw.stdout.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, oid, index_stage = meta.split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        out[path] = {
            "git_mode": mode.decode("ascii"),
            "git_blob_oid": oid.decode("ascii"),
            "git_index_stage": int(index_stage),
        }
    return out


def one_match(paths: list[str], predicate, label: str) -> tuple[str | None, list[str]]:
    matches = [p for p in paths if predicate(p)]
    if len(matches) == 1:
        return matches[0], []
    if not matches:
        return None, [f"MISSING_{label}"]
    return None, [f"AMBIGUOUS_{label}:{matches}"]


def exact_path(paths: list[str], expected: str, label: str) -> tuple[str | None, list[str]]:
    if expected in paths:
        return expected, []
    return None, [f"MISSING_{label}:{expected}"]


def checker_result(script_path: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, script_path, "--root", "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return {
        "script": script_path,
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout.strip().splitlines()[-20:],
        "stderr_tail": proc.stderr.strip().splitlines()[-20:],
    }


def runtime_review(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    data = load_json(path)
    return {
        "path": path.as_posix(),
        "stage": data.get("stage"),
        "status": data.get("status"),
        "decision": data.get("decision"),
        "considered": data.get("considered"),
        "new_external_engine_execution_performed": data.get(
            "new_external_engine_execution_performed"
        ),
        "role_adjudication": "DEFERRED_TO_R5_16_EXTERNAL_ENGINE_GOVERNANCE_AUDIT",
    }


def completion_evidence(stage_number: int, path: Path) -> tuple[dict[str, Any], list[str]]:
    data = load_json(path)
    failures: list[str] = []

    if stage_number < 15:
        if data.get("stage") != f"v0.6D1-R5.{stage_number}":
            failures.append("COMPLETION_STAGE_MISMATCH")
        if data.get("scientific_candidate_eligible") is not True:
            failures.append("SCIENTIFIC_CANDIDATE_NOT_ELIGIBLE")
        if data.get("failed") not in ([], None):
            failures.append(f"COMPLETION_FAILED_LIST_NONEMPTY:{data.get('failed')}")
        status = data.get("status")
        if not isinstance(status, str) or "CANDIDATE" not in status:
            failures.append(f"COMPLETION_STATUS_NOT_CANDIDATE:{status!r}")

        summary = {
            "path": path.as_posix(),
            "stage": data.get("stage"),
            "status": status,
            "scientific_candidate_eligible": data.get("scientific_candidate_eligible"),
            "checks_passed": data.get("checks_passed"),
            "checks_total": data.get("checks_total"),
            "failed": data.get("failed"),
        }
        return summary, failures

    # R5.15 is an audit/reconciliation stage and intentionally uses PASS2 artifacts.
    if data.get("stage") != "v0.6D1-R5.15":
        failures.append("R515_COMPLETION_STAGE_MISMATCH")
    if data.get("r5_15_completed") is not True:
        failures.append("R515_NOT_COMPLETED")
    if data.get("r5_15_status") != "CANDIDATE":
        failures.append(f"R515_STATUS_NOT_CANDIDATE:{data.get('r5_15_status')!r}")
    if data.get("r5_15_sealed") is not False:
        failures.append("R515_SEAL_STATE_INVALID")
    checks = data.get("checks")
    if not isinstance(checks, dict) or not checks:
        failures.append("R515_CHECKS_MISSING")
    else:
        failed_checks = [k for k, v in checks.items() if v is not True]
        if failed_checks:
            failures.append(f"R515_FAILED_CHECKS:{failed_checks}")

    summary = {
        "path": path.as_posix(),
        "stage": data.get("stage"),
        "status": data.get("status"),
        "r5_15_completed": data.get("r5_15_completed"),
        "r5_15_status": data.get("r5_15_status"),
        "r5_15_sealed": data.get("r5_15_sealed"),
        "result_counts": data.get("result_counts"),
        "repair_block_required": data.get("repair_block_required"),
    }
    return summary, failures


def main() -> None:
    root = repo_root()
    os.chdir(root)

    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    head = git_text("rev-parse", "HEAD")

    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}")

    # A2 is intentionally bound to the committed A1 inventory.
    if head != EXPECTED_A1_COMMIT:
        raise SystemExit(
            "R5.16-A2 must be run from the committed A1 authority snapshot.\n"
            f"Expected HEAD: {EXPECTED_A1_COMMIT}\n"
            f"Found HEAD:    {head}"
        )

    tracked_dirty = git_text("status", "--porcelain", "--untracked-files=no")
    if tracked_dirty:
        raise SystemExit(
            "Tracked working tree is not clean.\n"
            "Commit/stash tracked modifications before running A2:\n"
            + tracked_dirty
        )

    if not INVENTORY_PATH.exists():
        raise SystemExit(f"Missing {INVENTORY_PATH}")

    inventory = load_json(INVENTORY_PATH)
    if inventory.get("schema") != "ARCANA_R5_16_SOURCE_AUTHORITY_INVENTORY_V1":
        raise SystemExit("Unexpected A1 inventory schema")
    if inventory.get("status") != "INVENTORY_ONLY_NO_ADJUDICATION":
        raise SystemExit("Unexpected A1 inventory status")
    if inventory.get("scope", {}).get("stage_count") != 8:
        raise SystemExit("Unexpected A1 stage count")

    inventory_source_commit = inventory.get("source_commit")
    if not isinstance(inventory_source_commit, str):
        raise SystemExit("A1 inventory source_commit missing")

    ancestor = run_git(
        "merge-base",
        "--is-ancestor",
        inventory_source_commit,
        head,
        check=False,
    )
    if ancestor.returncode != 0:
        raise SystemExit(
            f"A1 source commit {inventory_source_commit} is not an ancestor of A2 HEAD {head}"
        )

    current_entries = current_git_entries()

    all_failures: list[str] = []
    stage_results: list[dict[str, Any]] = []

    stage_files_obj = inventory.get("stage_files")
    if not isinstance(stage_files_obj, dict):
        raise SystemExit("A1 inventory stage_files missing")

    for n in STAGES:
        stage = f"v0.6D1-R5.{n}"
        prefix = f"R5_{n}_"
        inventory_entries = stage_files_obj.get(stage)

        if not isinstance(inventory_entries, list):
            stage_results.append(
                {
                    "stage": stage,
                    "status": "BLOCKED",
                    "failures": ["A1_STAGE_INVENTORY_MISSING"],
                }
            )
            all_failures.append(f"{stage}:A1_STAGE_INVENTORY_MISSING")
            continue

        paths = [item["path"] for item in inventory_entries]
        failures: list[str] = []
        drift: list[dict[str, Any]] = []

        # Exact blob preservation from the A1 snapshot.
        for item in inventory_entries:
            path = item["path"]
            expected_oid = item["git_blob_oid"]
            current = current_entries.get(path)
            if current is None:
                drift.append(
                    {
                        "path": path,
                        "expected_git_blob_oid": expected_oid,
                        "current_git_blob_oid": None,
                        "reason": "MISSING_FROM_CURRENT_INDEX",
                    }
                )
            elif current["git_blob_oid"] != expected_oid:
                drift.append(
                    {
                        "path": path,
                        "expected_git_blob_oid": expected_oid,
                        "current_git_blob_oid": current["git_blob_oid"],
                        "reason": "GIT_BLOB_OID_CHANGED_SINCE_A1",
                    }
                )

        if drift:
            failures.append("A1_TO_A2_STAGE_BLOB_DRIFT")

        evidence: dict[str, Any] = {}

        contract, errs = one_match(
            paths,
            lambda p, pfx=prefix: Path(p).name.startswith(pfx)
            and Path(p).name.endswith("_CONTRACT.md"),
            "STAGE_CONTRACT",
        )
        failures.extend(errs)
        evidence["contract"] = contract

        if n < 15:
            authority, errs = exact_path(
                paths,
                f"R5_{n}_RECONCILIATION_AUTHORITY.json",
                "RECONCILIATION_AUTHORITY",
            )
            failures.extend(errs)
            evidence["reconciliation_authority"] = authority

            source_manifest, errs = exact_path(
                paths,
                f"SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_{n}.json",
                "SOURCE_AUTHORITY_MANIFEST",
            )
            failures.extend(errs)
            evidence["source_authority_manifest"] = source_manifest

            config, errs = one_match(
                paths,
                lambda p: p.startswith("configs/") and p.endswith(".json"),
                "STAGE_CONFIG",
            )
            failures.extend(errs)
            evidence["config"] = config

            parent_binding, errs = exact_path(
                paths,
                f"outputs/v0_6D1_R5_{n}/R5_{n}_PARENT_AUTHORITY_BINDING.json",
                "PARENT_AUTHORITY_BINDING",
            )
            failures.extend(errs)
            evidence["parent_authority_binding"] = parent_binding

            output_manifest, errs = exact_path(
                paths,
                f"outputs/v0_6D1_R5_{n}/R5_{n}_OUTPUT_MANIFEST.json",
                "OUTPUT_MANIFEST",
            )
            failures.extend(errs)
            evidence["output_manifest"] = output_manifest

            integrated, errs = exact_path(
                paths,
                f"outputs/v0_6D1_R5_{n}/R5_{n}_INTEGRATED_RECONCILIATION.json",
                "INTEGRATED_RECONCILIATION",
            )
            failures.extend(errs)
            evidence["completion_artifact"] = integrated

            checker_path = f"scripts/check_v0_6D1_R5_{n}_source_manifest.py"
            checker, errs = exact_path(paths, checker_path, "SOURCE_MANIFEST_CHECKER")
            failures.extend(errs)

            checker_info = None
            if checker is not None:
                checker_info = checker_result(checker)
                if not checker_info["passed"]:
                    failures.append("SOURCE_MANIFEST_CHECKER_FAILED")
            evidence["source_manifest_checker"] = checker_info

            if integrated is not None:
                completion, completion_failures = completion_evidence(
                    n, Path(integrated)
                )
                failures.extend(completion_failures)
            else:
                completion = None

            runtime_matches = [
                p for p in paths if Path(p).name == f"R5_{n}_RUNTIME_UTILITY_REVIEW.json"
            ]
            if len(runtime_matches) > 1:
                failures.append(f"AMBIGUOUS_RUNTIME_UTILITY_REVIEW:{runtime_matches}")
            runtime_path = Path(runtime_matches[0]) if len(runtime_matches) == 1 else None
            external_runtime = runtime_review(runtime_path)

        else:
            # R5.15 intentionally has a different, audit-only source-authority shape.
            r515_required = {
                "dependency_graph_pass2": "R5_15_DEPENDENCY_GRAPH_PASS2.json",
                "final_audit_pass2": "R5_15_FINAL_AUDIT_PASS2.json",
                "gap_register_pass2": "R5_15_GAP_REGISTER_PASS2.json",
                "legacy_census_pass2": "R5_15_R3_34_TO_R3_39_CENSUS_PASS2.json",
                "reuse_classification_pass2": "R5_15_REUSE_CLASSIFICATION_PASS2.json",
            }

            for key, expected in r515_required.items():
                path, errs = exact_path(paths, expected, key.upper())
                failures.extend(errs)
                evidence[key] = path

            completion_path = evidence.get("final_audit_pass2")
            if completion_path is not None:
                completion, completion_failures = completion_evidence(
                    15, Path(completion_path)
                )
                failures.extend(completion_failures)
            else:
                completion = None

            evidence["source_authority_manifest"] = None
            evidence["config"] = None
            evidence["parent_authority_binding"] = evidence.get(
                "dependency_graph_pass2"
            )
            evidence["output_manifest"] = None
            evidence["schema_note"] = (
                "R5.15 is an audit/reconciliation stage; PASS2 dependency/final-audit/"
                "census/reuse/gap artifacts are the required source-authority evidence."
            )
            external_runtime = {
                "path": "R5_15_FINAL_AUDIT_PASS2.json",
                "decision": "EXTERNAL_RUNTIME_NOT_REQUIRED",
                "new_external_engine_execution_performed": False,
                "role_adjudication": (
                    "DEFERRED_TO_R5_16_EXTERNAL_ENGINE_GOVERNANCE_AUDIT"
                ),
            }

        provenance_complete = not failures

        stage_result = {
            "stage": stage,
            "inventory_file_count": len(inventory_entries),
            "inventory_blob_drift_count": len(drift),
            "inventory_blob_drift": drift,
            "evidence": evidence,
            "completion": completion,
            "external_engine_evidence": external_runtime,
            "provenance_complete": provenance_complete,
            "failures": failures,
            "status": "PASS" if provenance_complete else "BLOCKED",
        }
        stage_results.append(stage_result)

        all_failures.extend(f"{stage}:{failure}" for failure in failures)

    stages_verified = sum(1 for x in stage_results if x["provenance_complete"])
    provenance_complete = stages_verified == len(STAGES) and not all_failures

    result = {
        "schema": "ARCANA_R5_16_SOURCE_AUTHORITY_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-A2",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": head,
        "a1_inventory": {
            "path": INVENTORY_PATH.as_posix(),
            "inventory_source_commit": inventory_source_commit,
            "a1_commit": EXPECTED_A1_COMMIT,
            "a1_source_is_ancestor_of_a2": True,
        },
        "scope": {
            "first_stage": "v0.6D1-R5.8",
            "last_stage": "v0.6D1-R5.15",
            "stage_count": len(STAGES),
        },
        "method": {
            "a1_git_blob_identity_rechecked": True,
            "existing_stage_sha256_checkers_executed_for_r5_8_to_r5_14": True,
            "r5_15_pass2_audit_shape_respected": True,
            "scientific_reinterpretation": False,
            "parent_chain_adjudication": False,
            "legacy_reconciliation_adjudication": False,
            "negative_result_adjudication": False,
            "external_engine_execution": False,
            "external_engine_governance_final_adjudication": False,
            "canonical_mutation": False,
            "automatic_repair": False,
            "seal_action": False,
        },
        "stages": stage_results,
        "stages_expected": len(STAGES),
        "stages_verified": stages_verified,
        "repository_provenance_complete": provenance_complete,
        "open_provenance_gap_count": len(all_failures),
        "open_provenance_gaps": all_failures,
        "status": (
            "PASS_R516_SOURCE_AUTHORITY"
            if provenance_complete
            else "BLOCKED_R516_SOURCE_AUTHORITY"
        ),
        "next_if_pass": "R5.16-B_PARENT_CHAIN_AUDIT",
    }

    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {head}")
    for stage_result in stage_results:
        print(
            f"{stage_result['stage']}: "
            f"{stage_result['status']} "
            f"files={stage_result['inventory_file_count']} "
            f"drift={stage_result['inventory_blob_drift_count']} "
            f"failures={len(stage_result['failures'])}"
        )
    print(f"STAGES_VERIFIED = {stages_verified}/{len(STAGES)}")
    print(f"OPEN_PROVENANCE_GAPS = {len(all_failures)}")
    print(f"STATUS = {result['status']}")

    if not provenance_complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
