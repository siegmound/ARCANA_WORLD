from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import collections
import json
import re

STAGE = "v0.6D1-R4.51"

PARENT_COMPLETE = (
    "PASS_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_FINAL_GEONOMICS_CLOSURE_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_FINAL_GEONOMICS_CLOSURE_SEALED"
)
PARENT_NEXT = (
    "BUILD_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
    "GAP_CENSUS"
)

COMPLETE = (
    "PASS_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
    "GAP_CENSUS_COMPLETE"
)
SEALED = (
    "PASS_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
    "GAP_CENSUS_SEALED"
)
BLOCKED = "BLOCKED_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_OR_GAP_CENSUS_FAILURE"
NEXT = (
    "BUILD_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
    "AND_EXECUTION_PLAN"
)

OUT = Path("outputs/v0_6D1_R4_51")
SEAL = Path("outputs/v0_6D1_R4_51_SEAL/R4_51_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r451_multi_engine_23_job_reconciliation_revalidation_"
    "gap_census_v0_6D1_R4_51.json"
)

R42_MATRIX = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R42_SEAL = Path("outputs/v0_6D1_R4_2_SEAL/R4_2_FINAL_SEAL_AUDIT.json")
R450 = Path("outputs/v0_6D1_R4_50/R4_50_INTEGRATED_AUDIT.json")
R450_SEAL = Path("outputs/v0_6D1_R4_50_SEAL/R4_50_FINAL_SEAL_AUDIT.json")
R450_CLOSURE = Path(
    "outputs/v0_6D1_R4_50/R4_50_FINAL_GEONOMICS_REVALIDATION_CLOSURE.json"
)

EXPECTED_JOBS = [
    ("R42_J01_H0_DEEP_TIME_BACKGROUND_MADINGLEY", "Madingley", "H0_DEEP_TIME_BACKGROUND"),
    ("R42_J02_H0_DEEP_TIME_BACKGROUND_RANGESHIFTER", "RangeShifter", "H0_DEEP_TIME_BACKGROUND"),
    ("R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP", "CDMetaPOP", "H0_DEEP_TIME_BACKGROUND"),
    ("R42_J04_H0_PRE_CHA1_MADINGLEY", "Madingley", "H0_PRE_CHA1"),
    ("R42_J05_H0_PRE_CHA1_RANGESHIFTER", "RangeShifter", "H0_PRE_CHA1"),
    ("R42_J06_H0_PRE_CHA1_CDMETAPOP", "CDMetaPOP", "H0_PRE_CHA1"),
    ("R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY", "Madingley", "H0_POST_CHA1_RECOVERY"),
    ("R42_J08_H0_POST_CHA1_RECOVERY_RANGESHIFTER", "RangeShifter", "H0_POST_CHA1_RECOVERY"),
    ("R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP", "CDMetaPOP", "H0_POST_CHA1_RECOVERY"),
    ("R42_J10_H0_POST_CHA1_RECOVERY_NEMO", "NEMO", "H0_POST_CHA1_RECOVERY"),
    ("R42_J11_H0_LATE_CENOZOIC_MADINGLEY", "Madingley", "H0_LATE_CENOZOIC"),
    ("R42_J12_H0_LATE_CENOZOIC_RANGESHIFTER", "RangeShifter", "H0_LATE_CENOZOIC"),
    ("R42_J13_H0_LATE_CENOZOIC_NEMO", "NEMO", "H0_LATE_CENOZOIC"),
    ("R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS", "Geonomics", "SAPIENT_3MA_TO_200KA"),
    ("R42_J15_SAPIENT_3MA_TO_200KA_CDMETAPOP", "CDMetaPOP", "SAPIENT_3MA_TO_200KA"),
    ("R42_J16_SAPIENT_3MA_TO_200KA_SLIM", "SLiM", "SAPIENT_3MA_TO_200KA"),
    ("R42_J17_SAPIENT_3MA_TO_200KA_NEMO", "NEMO", "SAPIENT_3MA_TO_200KA"),
    ("R42_J18_SAPIENT_200KA_TO_0_GEONOMICS", "Geonomics", "SAPIENT_200KA_TO_0"),
    ("R42_J19_SAPIENT_200KA_TO_0_SLIM", "SLiM", "SAPIENT_200KA_TO_0"),
    ("R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP", "CDMetaPOP", "SAPIENT_200KA_TO_0"),
    ("R42_J21_PRODUCER_20KA_TO_0_GEONOMICS", "Geonomics", "PRODUCER_20KA_TO_0"),
    ("R42_J22_PRODUCER_20KA_TO_0_SLIM", "SLiM", "PRODUCER_20KA_TO_0"),
    ("R42_J23_PRODUCER_20KA_TO_0_RANGESHIFTER", "RangeShifter", "PRODUCER_20KA_TO_0"),
]

EXPECTED_ENGINE_COUNTS = {
    "Madingley": 4,
    "RangeShifter": 5,
    "CDMetaPOP": 5,
    "NEMO": 3,
    "Geonomics": 3,
    "SLiM": 3,
}

GEONOMICS_CLOSED = {
    "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
    "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS",
    "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS",
}

EVIDENCE_CLASSES = {
    "SCIENTIFIC_VALID",
    "SCIENTIFIC_FAILED_OR_INVALID",
    "PROCESS_EXECUTION_SUCCESS_ONLY",
    "PREFLIGHT_OR_GOVERNANCE",
    "BLOCKED_OR_INVALID",
    "UNCLASSIFIED_REFERENCE",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stage_number(path: Path) -> tuple[int, int, str]:
    s = str(path).replace("\\", "/")
    m = re.search(r"v0_6D1_R4_(\d+)(?:_R(\d+))?", s)
    if not m:
        return (-1, -1, s)
    return (int(m.group(1)), int(m.group(2) or 0), s)


def _json_files(root: Path) -> Iterable[Path]:
    outputs = root / "outputs"
    if not outputs.exists():
        return []
    paths = []
    for p in outputs.rglob("*.json"):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if "outputs/v0_6D1_R4_51" in rel:
            continue
        if "failed_or_partial_shards" in rel:
            # Preserve these historically, but they are not authoritative
            # candidates for current job scientific closure.
            continue
        if re.search(r"outputs/v0_6D1_R4_(\d+)", rel):
            paths.append(p)
    return sorted(paths, key=_stage_number)


def _strings(obj: Any, depth: int = 0) -> list[str]:
    if depth > 4:
        return []
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(_strings(v, depth + 1))
    elif isinstance(obj, list):
        for v in obj[:5000]:
            out.extend(_strings(v, depth + 1))
    return out


def _bool_signal(obj: Any, names: set[str]) -> bool | None:
    if not isinstance(obj, dict):
        return None
    found = []
    stack = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > 3 or not isinstance(cur, dict):
            continue
        for k, v in cur.items():
            nk = str(k).lower()
            if nk in names and isinstance(v, bool):
                found.append(v)
            if isinstance(v, dict):
                stack.append((v, depth + 1))
    if any(found):
        return True
    if found and not any(found):
        return False
    return None


def _numeric_signal(obj: Any, names: set[str]) -> list[float]:
    vals = []
    if not isinstance(obj, dict):
        return vals
    stack = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > 3 or not isinstance(cur, dict):
            continue
        for k, v in cur.items():
            nk = str(k).lower()
            if nk in names and isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.append(float(v))
            if isinstance(v, dict):
                stack.append((v, depth + 1))
    return vals


def _classify_local_object(obj: Any, path: Path) -> tuple[str, dict[str, Any]]:
    strings = [s.upper() for s in _strings(obj)]
    text = " ".join(strings)

    sci_exec = _bool_signal(obj, {
        "scientific_engine_execution_performed",
        "scientific_execution_performed",
        "scientific_engine_execution",
    })
    sci_valid = _bool_signal(obj, {
        "scientific_evidence_capture_valid",
        "scientific_evidence_valid",
        "evidence_capture_valid",
        "scientific_validation_pass",
    })
    full_closed = _bool_signal(obj, {
        "full_job_revalidation_closed",
        "geonomics_full_job_revalidation_closed",
        "scientific_revalidation_closed",
    })

    returncodes = _numeric_signal(obj, {
        "returncode", "return_code", "process_returncode", "exit_code"
    })
    process_success = any(v == 0 for v in returncodes)

    blocked = any(tok in text for tok in (
        "BLOCKED_", "ADAPTER_FAILURE", "INVALID_EVIDENCE",
        "SCIENTIFIC_EVIDENCE_SCHEMA_FAILURE", "FAIL_CLOSED"
    ))
    passish = any(tok in text for tok in (
        "PASS_", "EVIDENCE_CAPTURED", "REVALIDATED", "SEALED"
    ))
    preflight = any(tok in text for tok in (
        "PREFLIGHT", "AUTHORITY", "MAPPING", "SELECTOR", "TARGET_DESIGN",
        "RUNTIME_READY", "RUNTIME EVIDENCE", "SCHEMA", "PROTOCOL",
        "MATERIALIZATION", "ADAPTER", "CONSTRUCTION", "DRY_RUN", "DRY RUN",
    ))

    if sci_exec is True and sci_valid is True and passish and not blocked:
        cls = "SCIENTIFIC_VALID"
    elif sci_exec is True and (sci_valid is False or blocked):
        cls = "SCIENTIFIC_FAILED_OR_INVALID"
    elif process_success and sci_valid is not True:
        cls = "PROCESS_EXECUTION_SUCCESS_ONLY"
    elif blocked:
        cls = "BLOCKED_OR_INVALID"
    elif preflight:
        cls = "PREFLIGHT_OR_GOVERNANCE"
    else:
        cls = "UNCLASSIFIED_REFERENCE"

    signals = {
        "scientific_execution": sci_exec,
        "scientific_evidence_valid": sci_valid,
        "full_job_revalidation_closed_signal": full_closed,
        "process_returncode_zero": process_success,
        "blocked_signal": blocked,
        "pass_signal": passish,
        "preflight_signal": preflight,
    }
    return cls, signals


def _collect_job_objects(
    obj: Any,
    known_jobs: set[str],
    json_path: str = "$",
) -> list[tuple[str, Any, str]]:
    out = []
    if isinstance(obj, dict):
        jid = obj.get("job_id")
        if isinstance(jid, str) and jid in known_jobs:
            out.append((jid, obj, json_path))
        for k, v in obj.items():
            if isinstance(k, str) and k in known_jobs:
                out.append((k, v, f"{json_path}.{k}"))
            if isinstance(v, (dict, list)):
                out.extend(_collect_job_objects(v, known_jobs, f"{json_path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                out.extend(_collect_job_objects(v, known_jobs, f"{json_path}[{i}]"))
    return out


def _scan_evidence(root: Path, jobs: list[dict[str, Any]]) -> dict[str, Any]:
    known = {j["job_id"] for j in jobs}
    by_job: dict[str, list[dict[str, Any]]] = {jid: [] for jid in known}
    file_count = 0
    parse_failures = []
    skipped_large = []

    for p in _json_files(root):
        try:
            size = p.stat().st_size
            # Summary/audit files are expected to be small. Very large JSON
            # evidence bodies are already represented by their sealed manifests.
            if size > 64 * 1024 * 1024:
                skipped_large.append({
                    "path": str(p.relative_to(root)).replace("\\", "/"),
                    "bytes": size,
                })
                continue
            obj = load(p)
            file_count += 1
        except Exception as exc:
            parse_failures.append({
                "path": str(p.relative_to(root)).replace("\\", "/"),
                "error": repr(exc),
            })
            continue

        rel = str(p.relative_to(root)).replace("\\", "/")
        for jid, local, jpath in _collect_job_objects(obj, known):
            cls, signals = _classify_local_object(local, p)
            by_job[jid].append({
                "path": rel,
                "json_path": jpath,
                "stage_sort": list(_stage_number(p)[:2]),
                "evidence_class": cls,
                "signals": signals,
            })

    for jid in by_job:
        seen = set()
        deduped = []
        for rec in sorted(
            by_job[jid],
            key=lambda r: (
                int(r["stage_sort"][0]),
                int(r["stage_sort"][1]),
                r["path"],
                r["json_path"],
            ),
        ):
            key = (
                rec["path"], rec["json_path"], rec["evidence_class"],
                json.dumps(rec["signals"], sort_keys=True)
            )
            if key not in seen:
                seen.add(key)
                deduped.append(rec)
        by_job[jid] = deduped

    return {
        "scanned_json_file_count": file_count,
        "parse_failure_count": len(parse_failures),
        "parse_failures": parse_failures,
        "skipped_large_json_count": len(skipped_large),
        "skipped_large_json": skipped_large,
        "job_evidence_candidates": by_job,
    }


def _classify_job(
    job: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    jid = job["job_id"]
    classes = collections.Counter(c["evidence_class"] for c in candidates)

    if jid in GEONOMICS_CLOSED:
        status = "FULLY_REVALIDATED_CLOSED_R450"
        closure_gap = False
        execution_decision = "NO_NEW_EXECUTION_REQUIRED"
        promotion_candidate = False
    elif classes["SCIENTIFIC_VALID"] > 0:
        status = "SCIENTIFIC_EVIDENCE_PRESENT_CLOSURE_NOT_PROVEN"
        closure_gap = True
        execution_decision = "PENDING_R452_EVIDENCE_ADJUDICATION_BEFORE_RERUN"
        promotion_candidate = True
    elif classes["PROCESS_EXECUTION_SUCCESS_ONLY"] > 0:
        status = "PROCESS_EXECUTION_EVIDENCE_ONLY"
        closure_gap = True
        execution_decision = "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
        promotion_candidate = False
    elif (
        classes["SCIENTIFIC_FAILED_OR_INVALID"] > 0
        or classes["BLOCKED_OR_INVALID"] > 0
    ):
        status = "FAILED_OR_INVALID_EVIDENCE_ONLY"
        closure_gap = True
        execution_decision = "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
        promotion_candidate = False
    elif classes["PREFLIGHT_OR_GOVERNANCE"] > 0:
        status = "PREFLIGHT_OR_GOVERNANCE_ONLY"
        closure_gap = True
        execution_decision = "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
        promotion_candidate = False
    else:
        status = "NO_JOB_SPECIFIC_SCIENTIFIC_EVIDENCE_FOUND"
        closure_gap = True
        execution_decision = "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
        promotion_candidate = False

    latest = candidates[-1] if candidates else None
    return {
        "job_id": jid,
        "engine": job["engine"],
        "window_id": job["window_id"],
        "earliest_replay_boundary": job.get("earliest_replay_boundary"),
        "r42_execution_status": job.get("execution_status"),
        "classification": status,
        "full_job_closure_gap": closure_gap,
        "new_scientific_execution_decision": execution_decision,
        "scientific_evidence_promotion_candidate": promotion_candidate,
        "evidence_candidate_count": len(candidates),
        "evidence_class_counts": dict(sorted(classes.items())),
        "latest_evidence_candidate": latest,
        "evidence_candidates": candidates,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    matrix = load(root / R42_MATRIX)
    r42_seal = load(root / R42_SEAL)
    parent = load(root / R450)
    parent_seal = load(root / R450_SEAL)
    geonomics = load(root / R450_CLOSURE)

    jobs = list(matrix.get("jobs") or [])
    expected_map = {
        jid: (engine, window)
        for jid, engine, window in EXPECTED_JOBS
    }
    observed_ids = [str(j.get("job_id")) for j in jobs]
    expected_ids = [x[0] for x in EXPECTED_JOBS]

    registry_checks = {
        "r42_exact_23_jobs": matrix.get("job_count") == 23 and len(jobs) == 23,
        "r42_job_order_and_ids_exact": observed_ids == expected_ids,
        "r42_engine_window_identity_exact": all(
            (
                str(j.get("engine")),
                str(j.get("window_id")),
            ) == expected_map[str(j.get("job_id"))]
            for j in jobs
        ),
        "r42_all_canonical_write_false":
            all(j.get("canonical_write") is False for j in jobs),
        "r42_all_result_selected_false":
            all(j.get("result_selected") is False for j in jobs),
        "r42_all_frozen_not_executed_in_r42":
            all(
                j.get("execution_status") == "FROZEN_NOT_EXECUTED_IN_R42"
                for j in jobs
            ),
    }

    engine_counts = collections.Counter(str(j["engine"]) for j in jobs)
    registry_checks["r42_engine_distribution_exact"] = (
        dict(engine_counts) == EXPECTED_ENGINE_COUNTS
    )

    scan = _scan_evidence(root, jobs)
    classified = [
        _classify_job(
            j, scan["job_evidence_candidates"][j["job_id"]]
        )
        for j in jobs
    ]

    class_counts = collections.Counter(j["classification"] for j in classified)
    engine_summary = {}
    for engine in EXPECTED_ENGINE_COUNTS:
        rows = [j for j in classified if j["engine"] == engine]
        engine_summary[engine] = {
            "job_count": len(rows),
            "fully_revalidated_closed_count": sum(
                j["classification"] == "FULLY_REVALIDATED_CLOSED_R450"
                for j in rows
            ),
            "full_job_closure_gap_count": sum(
                j["full_job_closure_gap"] for j in rows
            ),
            "scientific_evidence_promotion_candidate_count": sum(
                j["scientific_evidence_promotion_candidate"] for j in rows
            ),
            "jobs": [j["job_id"] for j in rows],
        }

    closed = [j for j in classified if not j["full_job_closure_gap"]]
    gaps = [j for j in classified if j["full_job_closure_gap"]]
    promotion = [
        j for j in classified
        if j["scientific_evidence_promotion_candidate"]
    ]
    execution_required = [
        j for j in classified
        if j["new_scientific_execution_decision"]
        == "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
    ]

    census = {
        "stage": STAGE,
        "status": "R451_23_JOB_REVALIDATION_GAP_CENSUS_FROZEN",
        "job_count": len(classified),
        "fully_revalidated_closed_job_count": len(closed),
        "full_job_closure_gap_count": len(gaps),
        "scientific_evidence_promotion_candidate_count": len(promotion),
        "scientific_revalidation_execution_required_count":
            len(execution_required),
        "classification_counts": dict(sorted(class_counts.items())),
        "engine_summary": engine_summary,
        "jobs": classified,
        "scanner": {
            "scanned_json_file_count": scan["scanned_json_file_count"],
            "parse_failure_count": scan["parse_failure_count"],
            "parse_failures": scan["parse_failures"],
            "skipped_large_json_count": scan["skipped_large_json_count"],
            "skipped_large_json": scan["skipped_large_json"],
        },
        "promotion_candidate_job_ids": [j["job_id"] for j in promotion],
        "scientific_execution_required_job_ids": [
            j["job_id"] for j in execution_required
        ],
        "fully_revalidated_closed_job_ids": [j["job_id"] for j in closed],
        "full_job_closure_gap_job_ids": [j["job_id"] for j in gaps],
        "automatic_prior_evidence_promotion_performed": False,
        "new_scientific_engine_execution_performed": False,
        "canonical_state_changed": False,
    }
    write(root / OUT / "R4_51_23_JOB_REVALIDATION_GAP_CENSUS.json", census)

    evidence_index = {
        "stage": STAGE,
        "status": "R451_JOB_SPECIFIC_EVIDENCE_CANDIDATE_INDEX_FROZEN",
        **scan,
    }
    write(root / OUT / "R4_51_JOB_SPECIFIC_EVIDENCE_CANDIDATE_INDEX.json", evidence_index)

    checks = {
        "parent_r450_complete_50_50":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 50
            and parent.get("checks_failed") == 0,
        "parent_r450_sealed_25_25":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 25
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r451":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R451_CONSERVATIVE_23_JOB_EVIDENCE_RECONCILIATION_NO_AUTOMATIC_PROMOTION",
        "r42_registry_seal_present":
            str(r42_seal.get("verdict", "")).upper() == "SEALED"
            or str(r42_seal.get("status", "")).startswith("PASS_"),
        "r42_registry_exact":
            all(registry_checks.values()),
        "exact_23_jobs_classified":
            census["job_count"] == 23,
        "exact_3_geonomics_jobs_closed":
            census["fully_revalidated_closed_job_count"] == 3
            and set(census["fully_revalidated_closed_job_ids"])
            == GEONOMICS_CLOSED,
        "exact_20_non_geonomics_closure_gaps":
            census["full_job_closure_gap_count"] == 20,
        "geonomics_r450_closure_exact":
            geonomics.get("geonomics_full_job_revalidation_closed") is True
            and geonomics.get("coverage", {}).get(
                "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
            ) == "192/192"
            and geonomics.get("coverage", {}).get(
                "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
            ) == "64/64"
            and geonomics.get("coverage", {}).get(
                "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"
            ) == "1/1",
        "all_jobs_have_one_known_classification":
            all(
                j["classification"] in {
                    "FULLY_REVALIDATED_CLOSED_R450",
                    "SCIENTIFIC_EVIDENCE_PRESENT_CLOSURE_NOT_PROVEN",
                    "PROCESS_EXECUTION_EVIDENCE_ONLY",
                    "FAILED_OR_INVALID_EVIDENCE_ONLY",
                    "PREFLIGHT_OR_GOVERNANCE_ONLY",
                    "NO_JOB_SPECIFIC_SCIENTIFIC_EVIDENCE_FOUND",
                }
                for j in classified
            ),
        "no_non_geonomics_auto_closed":
            all(
                j["full_job_closure_gap"] is True
                for j in classified
                if j["engine"] != "Geonomics"
            ),
        "no_automatic_prior_evidence_promotion":
            census["automatic_prior_evidence_promotion_performed"] is False,
        "scientific_valid_candidates_deferred_to_r452":
            all(
                j["new_scientific_execution_decision"]
                == "PENDING_R452_EVIDENCE_ADJUDICATION_BEFORE_RERUN"
                for j in promotion
            ),
        "nonpromotion_gaps_require_scientific_execution":
            all(
                j["new_scientific_execution_decision"]
                == "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
                for j in execution_required
            ),
        "scanner_parse_failures_zero":
            scan["parse_failure_count"] == 0,
        "no_new_scientific_execution":
            cfg.get("new_scientific_engine_execution_performed") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False,
        "deep_off":
            cfg.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            parent.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            parent.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            parent.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "frozen_r42_job_count": 23,
        "fully_revalidated_closed_job_count":
            census["fully_revalidated_closed_job_count"],
        "full_job_closure_gap_count":
            census["full_job_closure_gap_count"],
        "scientific_evidence_promotion_candidate_count":
            census["scientific_evidence_promotion_candidate_count"],
        "scientific_revalidation_execution_required_count":
            census["scientific_revalidation_execution_required_count"],
        "fully_revalidated_closed_job_ids":
            census["fully_revalidated_closed_job_ids"],
        "promotion_candidate_job_ids":
            census["promotion_candidate_job_ids"],
        "scientific_execution_required_job_ids":
            census["scientific_execution_required_job_ids"],
        "engine_summary": census["engine_summary"],
        "multi_engine_full_revalidation_closed": False,
        "automatic_prior_evidence_promotion_performed": False,
        "new_scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R451_RECONCILIATION_OR_GAP_CENSUS",
    }
    write(root / OUT / "R4_51_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_51_INTEGRATED_AUDIT.json")
    c = load(root / OUT / "R4_51_23_JOB_REVALIDATION_GAP_CENSUS.json")

    checks = {
        "r451_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "exact_23_frozen_jobs":
            a.get("frozen_r42_job_count") == 23,
        "exact_3_closed":
            a.get("fully_revalidated_closed_job_count") == 3,
        "exact_20_closure_gaps":
            a.get("full_job_closure_gap_count") == 20,
        "closed_jobs_exactly_geonomics":
            set(a.get("fully_revalidated_closed_job_ids") or [])
            == GEONOMICS_CLOSED,
        "every_gap_classified":
            len(c.get("full_job_closure_gap_job_ids") or []) == 20,
        "promotion_candidates_explicit":
            a.get("scientific_evidence_promotion_candidate_count")
            == len(a.get("promotion_candidate_job_ids") or []),
        "execution_required_explicit":
            a.get("scientific_revalidation_execution_required_count")
            == len(a.get("scientific_execution_required_job_ids") or []),
        "no_automatic_prior_evidence_promotion":
            a.get("automatic_prior_evidence_promotion_performed") is False,
        "multi_engine_not_yet_closed":
            a.get("multi_engine_full_revalidation_closed") is False,
        "no_new_scientific_execution":
            a.get("new_scientific_engine_execution_performed") is False,
        "no_target_numeric":
            a.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            a.get("readjudication_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r452":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_GAP_CENSUS",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "frozen_r42_job_count": 23,
            "fully_revalidated_closed_job_count":
                a.get("fully_revalidated_closed_job_count"),
            "full_job_closure_gap_count":
                a.get("full_job_closure_gap_count"),
            "scientific_evidence_promotion_candidate_count":
                a.get("scientific_evidence_promotion_candidate_count"),
            "scientific_revalidation_execution_required_count":
                a.get("scientific_revalidation_execution_required_count"),
            "geonomics_jobs_closed": sorted(GEONOMICS_CLOSED),
            "multi_engine_full_revalidation_closed": False,
            "automatic_prior_evidence_promotion_performed": False,
            "new_scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
