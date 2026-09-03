from __future__ import annotations

from pathlib import Path
from typing import Any
import collections
import copy
import hashlib
import json
import re

STAGE = "v0.6D1-R4.52"

PARENT_COMPLETE = (
    "PASS_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
    "GAP_CENSUS_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
    "GAP_CENSUS_SEALED"
)
PARENT_NEXT = (
    "BUILD_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
    "AND_EXECUTION_PLAN"
)

COMPLETE = (
    "PASS_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
    "AND_EXECUTION_PLAN_COMPLETE"
)
SEALED = (
    "PASS_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
    "AND_EXECUTION_PLAN_SEALED"
)
BLOCKED = "BLOCKED_R452_NON_GEONOMICS_EXECUTION_PLAN_FAILURE"
NEXT = (
    "BUILD_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
    "AND_READOUT_AUTHORITY_PREFLIGHT"
)

OUT = Path("outputs/v0_6D1_R4_52")
SEAL = Path("outputs/v0_6D1_R4_52_SEAL/R4_52_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r452_non_geonomics_job_specific_evidence_adjudication_"
    "execution_plan_v0_6D1_R4_52.json"
)

R451 = Path("outputs/v0_6D1_R4_51/R4_51_INTEGRATED_AUDIT.json")
R451_SEAL = Path("outputs/v0_6D1_R4_51_SEAL/R4_51_FINAL_SEAL_AUDIT.json")
R451_CENSUS = Path("outputs/v0_6D1_R4_51/R4_51_23_JOB_REVALIDATION_GAP_CENSUS.json")
R42_MATRIX = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")

ENGINE_ORDER = ["Madingley", "RangeShifter", "CDMetaPOP", "NEMO", "SLiM"]
EXPECTED_COUNTS = {
    "Madingley": 4,
    "RangeShifter": 5,
    "CDMetaPOP": 5,
    "NEMO": 3,
    "SLiM": 3,
}
GEONOMICS_JOBS = {
    "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
    "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS",
    "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha_json(obj: Any) -> str:
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _seed_json_files(root: Path) -> list[Path]:
    paths = []
    out = root / "outputs"
    for p in out.rglob("*.json"):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if (
            "v0_6D1_R4_35" in rel
            or "v0_6D1_R4_3/" in rel
            or "v0_6D1_R4_3_" in rel
        ):
            paths.append(p)
    return sorted(set(paths))


def _collect_job_seed_records(
    obj: Any,
    known_jobs: set[str],
    inherited_job: str | None = None,
    path: str = "$",
) -> list[dict[str, Any]]:
    out = []
    if isinstance(obj, dict):
        local_job = inherited_job
        jid = obj.get("job_id")
        if isinstance(jid, str) and jid in known_jobs:
            local_job = jid

        for k, v in obj.items():
            if isinstance(k, str) and k in known_jobs:
                out.extend(
                    _collect_job_seed_records(v, known_jobs, k, f"{path}.{k}")
                )

        if local_job is not None:
            seed_values = []
            for k, v in obj.items():
                if "seed" not in str(k).lower():
                    continue
                if isinstance(v, int) and not isinstance(v, bool):
                    seed_values.append(int(v))
                elif isinstance(v, list):
                    seed_values.extend(
                        int(x)
                        for x in v
                        if isinstance(x, int) and not isinstance(x, bool)
                    )
            if seed_values:
                out.append({
                    "job_id": local_job,
                    "json_path": path,
                    "seed_values": seed_values,
                })

        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out.extend(
                    _collect_job_seed_records(
                        v, known_jobs, local_job, f"{path}.{k}"
                    )
                )

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                out.extend(
                    _collect_job_seed_records(
                        v, known_jobs, inherited_job, f"{path}[{i}]"
                    )
                )
    return out


def _discover_frozen_seeds(
    root: Path, known_jobs: set[str]
) -> dict[str, Any]:
    by_job = {jid: set() for jid in known_jobs}
    sources = {jid: [] for jid in known_jobs}
    parse_failures = []

    for p in _seed_json_files(root):
        try:
            obj = load(p)
        except Exception as exc:
            parse_failures.append({
                "path": str(p.relative_to(root)).replace("\\", "/"),
                "error": repr(exc),
            })
            continue

        rel = str(p.relative_to(root)).replace("\\", "/")
        for rec in _collect_job_seed_records(obj, known_jobs):
            jid = rec["job_id"]
            before = set(by_job[jid])
            by_job[jid].update(rec["seed_values"])
            if set(by_job[jid]) != before:
                sources[jid].append({
                    "path": rel,
                    "json_path": rec["json_path"],
                    "seed_values": rec["seed_values"],
                })

    result = {}
    for jid in sorted(known_jobs):
        values = sorted(by_job[jid])
        result[jid] = {
            "frozen_seeds": values,
            "seed_count": len(values),
            "source_records": sources[jid],
        }

    return {
        "status": "R452_R43_R435_SEED_AUTHORITY_DISCOVERY_COMPLETE",
        "parse_failure_count": len(parse_failures),
        "parse_failures": parse_failures,
        "jobs": result,
    }


def _job_record_hash(job: dict[str, Any]) -> str:
    return _sha_json(job)


def _freeze_plan(
    matrix: dict[str, Any],
    census: dict[str, Any],
    seed_discovery: dict[str, Any],
) -> dict[str, Any]:
    census_rows = {j["job_id"]: j for j in census["jobs"]}
    jobs = []

    for job in matrix["jobs"]:
        jid = str(job["job_id"])
        if jid in GEONOMICS_JOBS:
            continue

        row = census_rows[jid]
        seed = seed_discovery["jobs"][jid]
        jobs.append({
            "job_id": jid,
            "engine": str(job["engine"]),
            "window_id": str(job["window_id"]),
            "r42_job_record_sha256": _job_record_hash(job),
            "r42_execution_status": job.get("execution_status"),
            "r451_classification": row["classification"],
            "r451_execution_decision":
                row["new_scientific_execution_decision"],
            "promotion_candidate": False,
            "new_scientific_execution_required": True,
            "frozen_seeds": seed["frozen_seeds"],
            "frozen_seed_count": seed["seed_count"],
            "seed_authority_sources": seed["source_records"],
            "expected_scientific_stream_count": seed["seed_count"],
            "readout_authority_state":
                "ENGINE_SPECIFIC_READOUT_AUTHORITY_REQUIRED_R453",
            "execution_interface_state":
                "ENGINE_SPECIFIC_SCIENTIFIC_INTERFACE_REQUIRED_R453",
            "scientific_execution_authorized_in_r452": False,
            "result_selected": False,
            "canonical_write": False,
        })

    jobs = sorted(
        jobs,
        key=lambda x: int(re.search(r"_J(\d+)_", x["job_id"]).group(1))
    )

    batches = []
    for batch_index, engine in enumerate(ENGINE_ORDER):
        engine_jobs = [j for j in jobs if j["engine"] == engine]
        batches.append({
            "batch_index": batch_index,
            "engine": engine,
            "job_count": len(engine_jobs),
            "job_ids": [j["job_id"] for j in engine_jobs],
            "scientific_stream_count": sum(
                j["expected_scientific_stream_count"] for j in engine_jobs
            ),
            "batch_order_is_scientific_authority": False,
            "job_membership_is_scientific_authority": True,
            "parallelism_is_scientific_authority": False,
        })

    plan = {
        "stage": STAGE,
        "status": "R452_NON_GEONOMICS_EXECUTION_PLAN_FROZEN",
        "promotion_candidate_count": 0,
        "execution_required_job_count": len(jobs),
        "engine_count": len(ENGINE_ORDER),
        "expected_engine_job_counts": EXPECTED_COUNTS,
        "jobs": jobs,
        "engine_batches": batches,
        "expected_scientific_stream_count": sum(
            j["expected_scientific_stream_count"] for j in jobs
        ),
        "seed_authority_policy":
            "EXACT_FROZEN_R43_R435_SEEDS_NO_RESEEDING",
        "scientific_interface_policy":
            "FREEZE_ENGINE_SPECIFIC_EXECUTION_AND_READOUT_AUTHORITY_IN_R453_BEFORE_RUN",
        "automatic_evidence_promotion_performed": False,
        "scientific_execution_authorized": False,
        "scientific_engine_execution_performed": False,
        "result_selected_job_choice": False,
        "majority_vote_authorized": False,
        "engine_output_defines_arcana_target": False,
        "canonical_rewrite_authorized": False,
    }
    plan["plan_sha256"] = _sha_json(plan)
    return plan


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R451)
    parent_seal = load(root / R451_SEAL)
    census = load(root / R451_CENSUS)
    matrix = load(root / R42_MATRIX)

    known_jobs = {str(j["job_id"]) for j in matrix["jobs"]}
    seed_discovery = _discover_frozen_seeds(root, known_jobs)
    plan = _freeze_plan(matrix, census, seed_discovery)

    write(root / OUT / "R4_52_FROZEN_SEED_AUTHORITY_DISCOVERY.json", seed_discovery)
    write(root / OUT / "R4_52_NON_GEONOMICS_EXECUTION_PLAN.json", plan)

    non_gnx = [j for j in plan["jobs"]]
    counts = collections.Counter(j["engine"] for j in non_gnx)
    seed_counts = {j["job_id"]: j["frozen_seed_count"] for j in non_gnx}
    all_seed_values = [
        seed
        for j in non_gnx
        for seed in j["frozen_seeds"]
    ]

    checks = {
        "parent_r451_complete_24_24":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 24
            and parent.get("checks_failed") == 0,
        "parent_r451_sealed_18_18":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 18
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r452":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R452_FREEZE_EXACT_20_JOB_NON_GEONOMICS_EXECUTION_PLAN_WITHOUT_RUNNING",
        "r451_exact_zero_promotion_candidates":
            parent.get("scientific_evidence_promotion_candidate_count") == 0
            and census.get("scientific_evidence_promotion_candidate_count") == 0,
        "r451_exact_20_execution_required":
            parent.get("scientific_revalidation_execution_required_count") == 20
            and census.get("scientific_revalidation_execution_required_count") == 20,
        "exact_20_plan_jobs":
            plan["execution_required_job_count"] == 20
            and len(non_gnx) == 20,
        "geonomics_excluded_from_plan":
            all(j["job_id"] not in GEONOMICS_JOBS for j in non_gnx),
        "engine_distribution_exact":
            dict(counts) == EXPECTED_COUNTS,
        "exact_five_engine_batches":
            len(plan["engine_batches"]) == 5,
        "all_jobs_frozen_execution_required":
            all(j["new_scientific_execution_required"] is True for j in non_gnx),
        "all_jobs_not_promotion_candidates":
            all(j["promotion_candidate"] is False for j in non_gnx),
        "all_r451_decisions_execution_required":
            all(
                j["r451_execution_decision"]
                == "SCIENTIFIC_REVALIDATION_EXECUTION_REQUIRED"
                for j in non_gnx
            ),
        "seed_scan_parse_failures_zero":
            seed_discovery["parse_failure_count"] == 0,
        "all_20_jobs_have_exact_four_frozen_seeds":
            all(v == 4 for v in seed_counts.values()),
        "exact_80_planned_scientific_streams":
            plan["expected_scientific_stream_count"] == 80,
        "all_80_non_geonomics_seeds_unique":
            len(all_seed_values) == 80
            and len(set(all_seed_values)) == 80,
        "all_jobs_seed_authority_sourced":
            all(len(j["seed_authority_sources"]) >= 1 for j in non_gnx),
        "all_jobs_bound_to_exact_r42_record_hash":
            all(len(j["r42_job_record_sha256"]) == 64 for j in non_gnx),
        "all_jobs_require_r453_readout_authority":
            all(
                j["readout_authority_state"]
                == "ENGINE_SPECIFIC_READOUT_AUTHORITY_REQUIRED_R453"
                for j in non_gnx
            ),
        "all_jobs_require_r453_execution_interface":
            all(
                j["execution_interface_state"]
                == "ENGINE_SPECIFIC_SCIENTIFIC_INTERFACE_REQUIRED_R453"
                for j in non_gnx
            ),
        "scientific_execution_not_authorized_yet":
            plan["scientific_execution_authorized"] is False,
        "no_scientific_execution_in_r452":
            plan["scientific_engine_execution_performed"] is False,
        "no_result_selected_jobs":
            plan["result_selected_job_choice"] is False,
        "no_majority_vote":
            plan["majority_vote_authorized"] is False,
        "engine_cannot_define_target":
            plan["engine_output_defines_arcana_target"] is False,
        "canonical_rewrite_forbidden":
            plan["canonical_rewrite_authorized"] is False,
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
        "promotion_candidate_count": 0,
        "execution_required_job_count": 20,
        "engine_count": 5,
        "engine_job_counts": dict(counts),
        "planned_scientific_stream_count":
            plan["expected_scientific_stream_count"],
        "execution_plan_sha256": plan.get("plan_sha256"),
        "scientific_execution_authorized": False,
        "scientific_engine_execution_performed": False,
        "multi_engine_full_revalidation_closed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R452_NON_GEONOMICS_EXECUTION_PLAN",
    }
    write(root / OUT / "R4_52_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_52_INTEGRATED_AUDIT.json")
    plan = load(root / OUT / "R4_52_NON_GEONOMICS_EXECUTION_PLAN.json")

    checks = {
        "r452_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "zero_promotion_candidates":
            a.get("promotion_candidate_count") == 0,
        "exact_20_execution_jobs":
            a.get("execution_required_job_count") == 20,
        "exact_five_engines":
            a.get("engine_count") == 5,
        "engine_distribution_exact":
            a.get("engine_job_counts") == EXPECTED_COUNTS,
        "exact_80_planned_streams":
            a.get("planned_scientific_stream_count") == 80,
        "plan_hash_exact":
            a.get("execution_plan_sha256") == plan.get("plan_sha256"),
        "scientific_execution_not_authorized_yet":
            a.get("scientific_execution_authorized") is False,
        "no_scientific_execution":
            a.get("scientific_engine_execution_performed") is False,
        "multi_engine_not_closed":
            a.get("multi_engine_full_revalidation_closed") is False,
        "no_result_selected_job_choice":
            plan.get("result_selected_job_choice") is False,
        "no_majority_vote":
            plan.get("majority_vote_authorized") is False,
        "engine_cannot_define_target":
            plan.get("engine_output_defines_arcana_target") is False,
        "canonical_rewrite_forbidden":
            plan.get("canonical_rewrite_authorized") is False,
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
        "next_r453":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
            "AND_EXECUTION_PLAN",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "promotion_candidate_count": 0,
            "execution_required_job_count": 20,
            "engine_count": 5,
            "engine_job_counts": a.get("engine_job_counts"),
            "planned_scientific_stream_count":
                a.get("planned_scientific_stream_count"),
            "execution_plan_sha256":
                a.get("execution_plan_sha256"),
            "scientific_execution_authorized": False,
            "scientific_engine_execution_performed": False,
            "multi_engine_full_revalidation_closed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
