from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

STAGE = "v0.6D1-R4.47"

PARENT_COMPLETE = (
    "PASS_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
    "AND_EVIDENCE_CAPTURE_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
    "AND_EVIDENCE_CAPTURE_SEALED"
)
PARENT_R1 = (
    "PASS_R446_R1_EVIDENCE_MANIFEST_ORDER_REPAIR_AND_R446_RESEAL_VERIFIED"
)
PARENT_NEXT = (
    "BUILD_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_COHORT_ADJUDICATION_CLOSURE"
)
EXPECTED_PLAN_SHA = (
    "9a33a40c178a816526ca8aec053aae5a393086d7a18b9a3122bd453a4f592ec0"
)

COMPLETE = (
    "PASS_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_COHORT_ADJUDICATION_CLOSURE_COMPLETE"
)
SEALED = (
    "PASS_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_COHORT_ADJUDICATION_CLOSURE_SEALED"
)
BLOCKED = (
    "BLOCKED_R447_EVIDENCE_REVIEW_OR_COHORT_ADJUDICATION_CLOSURE_FAILURE"
)
NEXT = (
    "BUILD_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_PREFLIGHT"
)

OUT = Path("outputs/v0_6D1_R4_47")
SEAL = Path("outputs/v0_6D1_R4_47_SEAL/R4_47_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r447_geonomics_first_governed_revalidation_evidence_"
    "review_cohort_adjudication_closure_v0_6D1_R4_47.json"
)

R446 = Path("outputs/v0_6D1_R4_46/R4_46_INTEGRATED_AUDIT.json")
R446_SEAL = Path("outputs/v0_6D1_R4_46_SEAL/R4_46_FINAL_SEAL_AUDIT.json")
R446_R1 = Path(
    "outputs/v0_6D1_R4_46_R1/R4_46_R1_POSTREPAIR_RESEAL_AUDIT.json"
)
R446_MANIFEST = Path("outputs/v0_6D1_R4_46/R4_46_EVIDENCE_MANIFEST.json")
R446_J14 = Path("outputs/v0_6D1_R4_46/R4_46_J14_SCIENTIFIC_EVIDENCE.json")
R446_J18 = Path("outputs/v0_6D1_R4_46/R4_46_J18_SCIENTIFIC_EVIDENCE.json")
R446_J21 = Path("outputs/v0_6D1_R4_46/R4_46_J21_SCIENTIFIC_EVIDENCE.json")
R445_PLAN = Path(
    "outputs/v0_6D1_R4_45/R4_45_FIRST_GOVERNED_REVALIDATION_RUN_PLAN.json"
)

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

EXPECTED = {
    J14: {
        "streams": 4,
        "records": 1692,
        "integrity": 1128,
        "descriptive": 564,
        "executed_branches": 1,
        "total_branches": 192,
        "full_job": False,
    },
    J18: {
        "streams": 4,
        "records": 180,
        "integrity": 120,
        "descriptive": 60,
        "executed_branches": 1,
        "total_branches": 64,
        "full_job": False,
    },
    J21: {
        "streams": 4,
        "records": 10584,
        "integrity": 5292,
        "descriptive": 5292,
        "executed_branches": 1,
        "total_branches": 1,
        "full_job": True,
    },
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _review_job(
    *,
    job_id: str,
    evidence: dict[str, Any],
    plan_job: dict[str, Any],
    evidence_file_sha256: str,
) -> dict[str, Any]:
    exp = EXPECTED[job_id]
    records = evidence.get("metric_records") or []
    streams = evidence.get("stream_records") or []

    integrity = [
        r for r in records if r.get("metric_role") == "EXACT_INTEGRITY_ONLY"
    ]
    descriptive = [
        r for r in records
        if r.get("metric_role") in {
            "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
        }
    ]

    metric_ids = sorted({str(r.get("metric_id")) for r in records})
    plan_metric_ids = sorted(str(x) for x in plan_job["metric_ids"])

    integrity_exact = all(r.get("exact_match") is True for r in integrity)
    descriptive_finite = all(r.get("finite") is True for r in descriptive)
    no_thresholds = all(
        r.get("numeric_acceptance_threshold") is None for r in descriptive
    )
    no_auto_pass_fail = all(
        r.get("automatic_pass_fail_from_value") is False
        for r in descriptive
    )

    stream_claim_scope_exact = all(
        bool(r.get("full_job_revalidation_claim")) is exp["full_job"]
        for r in streams
    )
    observed_history_claim_off = all(
        r.get("observed_history_claim") is False for r in streams
    )
    all_streams_pass = (
        len(streams) == exp["streams"]
        and all(r.get("pass") is True for r in streams)
    )

    coverage_fraction = (
        float(exp["executed_branches"]) / float(exp["total_branches"])
    )

    checks = {
        "stream_count_exact": len(streams) == exp["streams"],
        "all_streams_pass": all_streams_pass,
        "metric_record_count_exact": len(records) == exp["records"],
        "integrity_record_count_exact": len(integrity) == exp["integrity"],
        "descriptive_record_count_exact":
            len(descriptive) == exp["descriptive"],
        "metric_ids_exactly_predeclared":
            metric_ids == plan_metric_ids,
        "all_integrity_exact": integrity_exact,
        "all_descriptive_finite": descriptive_finite,
        "zero_numeric_thresholds": no_thresholds,
        "zero_automatic_pass_fail": no_auto_pass_fail,
        "stream_claim_scope_exact": stream_claim_scope_exact,
        "observed_history_claim_off": observed_history_claim_off,
        "scientific_evidence_capture_valid":
            evidence.get("scientific_evidence_capture_valid") is True,
        "canonical_unchanged":
            evidence.get("canonical_state_changed") is False,
    }
    ok = all(checks.values())

    if exp["full_job"]:
        coverage_status = "FULL_JOB_COVERAGE_FOR_PREDECLARED_J21_LAYER_JOB"
        adjudication_scope = "FULL_JOB_GOVERNED_EVIDENCE_CLOSURE"
    else:
        coverage_status = "PARTIAL_FROZEN_COHORT_COVERAGE_ONLY"
        adjudication_scope = "FIRST_COHORT_GOVERNED_EVIDENCE_CLOSURE_ONLY"

    return {
        "stage": STAGE,
        "job_id": job_id,
        "status":
            "R447_JOB_EVIDENCE_REVIEW_CLOSED"
            if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "evidence_file_sha256": evidence_file_sha256,
        "replicate_stream_count": len(streams),
        "metric_record_count": len(records),
        "integrity_record_count": len(integrity),
        "descriptive_record_count": len(descriptive),
        "metric_ids": metric_ids,
        "integrity_adjudication":
            "PASS_EXACT_INTEGRITY"
            if integrity_exact else "FAIL_INTEGRITY",
        "descriptive_evidence_adjudication":
            "REVIEWED_VALID_DESCRIPTIVE_EVIDENCE_NO_THRESHOLD"
            if descriptive_finite and no_thresholds and no_auto_pass_fail
            else "INVALID_DESCRIPTIVE_EVIDENCE",
        "numeric_scientific_adjudication_of_descriptive_values_performed":
            False,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "executed_branch_count": exp["executed_branches"],
        "total_frozen_branch_count": exp["total_branches"],
        "branch_coverage_fraction": coverage_fraction,
        "branch_coverage_percent": coverage_fraction * 100.0,
        "coverage_status": coverage_status,
        "full_job_revalidation_claim": exp["full_job"],
        "adjudication_scope": adjudication_scope,
        "cohort_adjudication_closed": bool(ok),
        "canonical_state_changed": False,
    }


def _cohort_closure(
    *,
    parent_manifest: dict[str, Any],
    plan: dict[str, Any],
    reviews: list[dict[str, Any]],
    evidence_file_hashes: dict[str, str],
) -> dict[str, Any]:
    by_job = {r["job_id"]: r for r in reviews}

    exact_totals = {
        "streams": sum(r["replicate_stream_count"] for r in reviews),
        "records": sum(r["metric_record_count"] for r in reviews),
        "integrity": sum(r["integrity_record_count"] for r in reviews),
        "descriptive": sum(r["descriptive_record_count"] for r in reviews),
    }

    checks = {
        "parent_manifest_valid":
            parent_manifest.get("scientific_evidence_capture_valid") is True,
        "parent_plan_hash_exact":
            plan.get("plan_sha256") == EXPECTED_PLAN_SHA,
        "three_job_reviews_closed":
            all(r.get("cohort_adjudication_closed") is True for r in reviews),
        "exact_12_streams": exact_totals["streams"] == 12,
        "exact_12456_records": exact_totals["records"] == 12456,
        "exact_6540_integrity": exact_totals["integrity"] == 6540,
        "exact_5916_descriptive": exact_totals["descriptive"] == 5916,
        "j14_partial_scope_preserved":
            by_job[J14]["full_job_revalidation_claim"] is False
            and by_job[J14]["executed_branch_count"] == 1
            and by_job[J14]["total_frozen_branch_count"] == 192,
        "j18_partial_scope_preserved":
            by_job[J18]["full_job_revalidation_claim"] is False
            and by_job[J18]["executed_branch_count"] == 1
            and by_job[J18]["total_frozen_branch_count"] == 64,
        "j21_full_layer_job_scope_preserved":
            by_job[J21]["full_job_revalidation_claim"] is True
            and by_job[J21]["executed_branch_count"] == 1
            and by_job[J21]["total_frozen_branch_count"] == 1,
        "all_integrity_pass":
            all(
                r["integrity_adjudication"] == "PASS_EXACT_INTEGRITY"
                for r in reviews
            ),
        "all_descriptive_evidence_valid_no_threshold":
            all(
                r["descriptive_evidence_adjudication"]
                == "REVIEWED_VALID_DESCRIPTIVE_EVIDENCE_NO_THRESHOLD"
                for r in reviews
            ),
        "zero_numeric_value_adjudication":
            all(
                r[
                    "numeric_scientific_adjudication_of_descriptive_values_performed"
                ] is False
                for r in reviews
            ),
        "zero_automatic_scientific_pass_fail":
            all(
                r["automatic_scientific_pass_fail_count"] == 0
                for r in reviews
            ),
        "zero_scientific_divergence_claims":
            all(r["scientific_divergence_claim_count"] == 0 for r in reviews),
        "canonical_unchanged":
            all(r["canonical_state_changed"] is False for r in reviews),
        "evidence_hashes_present":
            set(evidence_file_hashes) == {J14, J18, J21},
    }
    ok = all(checks.values())

    return {
        "stage": STAGE,
        "status":
            "R447_FIRST_GOVERNED_REVALIDATION_COHORT_ADJUDICATION_CLOSED"
            if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "authorized_parent_plan_sha256": EXPECTED_PLAN_SHA,
        "evidence_file_hashes": evidence_file_hashes,
        "replicate_stream_count": exact_totals["streams"],
        "metric_record_count": exact_totals["records"],
        "integrity_record_count": exact_totals["integrity"],
        "descriptive_record_count": exact_totals["descriptive"],
        "integrity_adjudication_verdict":
            "PASS_ALL_EXACT_INTEGRITY"
            if ok else "BLOCKED",
        "descriptive_evidence_review_verdict":
            "ACCEPTED_AS_GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_THRESHOLD"
            if ok else "BLOCKED",
        "cohort_adjudication_verdict":
            (
                "VALID_GOVERNED_COHORT_EVIDENCE_WITH_EXACT_INTEGRITY_AND_"
                "DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
            ) if ok else "BLOCKED",
        "cohort_adjudication_closed": bool(ok),
        "numeric_scientific_adjudication_of_descriptive_values_performed":
            False,
        "automatic_scientific_pass_fail_count": 0,
        "majority_vote_performed": False,
        "result_selected_threshold_performed": False,
        "engine_output_defined_arcana_target": False,
        "canonical_state_changed": False,
        "coverage": {
            J14: {
                "executed_branches": 1,
                "total_frozen_branches": 192,
                "coverage_fraction": 1.0 / 192.0,
                "full_job_revalidation_closed": False,
            },
            J18: {
                "executed_branches": 1,
                "total_frozen_branches": 64,
                "coverage_fraction": 1.0 / 64.0,
                "full_job_revalidation_closed": False,
            },
            J21: {
                "executed_branches": 1,
                "total_frozen_branches": 1,
                "coverage_fraction": 1.0,
                "full_job_revalidation_closed": True,
            },
        },
        "next_action":
            NEXT if ok else "REPAIR_R447_EVIDENCE_REVIEW_OR_ADJUDICATION",
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R446)
    parent_seal = load(root / R446_SEAL)
    parent_r1 = load(root / R446_R1)
    parent_manifest = load(root / R446_MANIFEST)
    plan = load(root / R445_PLAN)

    evidence_paths = {
        J14: root / R446_J14,
        J18: root / R446_J18,
        J21: root / R446_J21,
    }
    evidence = {jid: load(p) for jid, p in evidence_paths.items()}
    hashes = {jid: sha256(p) for jid, p in evidence_paths.items()}

    reviews = []
    for jid in (J14, J18, J21):
        review = _review_job(
            job_id=jid,
            evidence=evidence[jid],
            plan_job=plan["jobs"][jid],
            evidence_file_sha256=hashes[jid],
        )
        reviews.append(review)
        write(
            root / OUT / f"R4_47_{jid}_EVIDENCE_REVIEW.json",
            review,
        )

    closure = _cohort_closure(
        parent_manifest=parent_manifest,
        plan=plan,
        reviews=reviews,
        evidence_file_hashes=hashes,
    )
    write(root / OUT / "R4_47_COHORT_ADJUDICATION_CLOSURE.json", closure)

    by_job = {r["job_id"]: r for r in reviews}

    checks = {
        "parent_r446_complete_39_39":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 39
            and parent.get("checks_failed") == 0,
        "parent_r446_sealed_22_22":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 22
            and parent_seal.get("checks_failed") == 0,
        "parent_r446_r1_verified_16_16":
            parent_r1.get("status") == PARENT_R1
            and parent_r1.get("checks_passed") == 16
            and parent_r1.get("checks_total") == 16,
        "parent_next_action_r447":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT
            and parent_r1.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R447_REVIEW_CAPTURED_EVIDENCE_WITHOUT_RETROACTIVE_NUMERIC_THRESHOLDS",
        "parent_plan_hash_exact":
            plan.get("plan_sha256") == EXPECTED_PLAN_SHA,
        "scientific_execution_recorded":
            parent.get("scientific_engine_execution_performed") is True,
        "parent_evidence_capture_valid":
            parent.get("scientific_evidence_capture_valid") is True,
        "j14_review_closed":
            by_job[J14].get("cohort_adjudication_closed") is True,
        "j18_review_closed":
            by_job[J18].get("cohort_adjudication_closed") is True,
        "j21_review_closed":
            by_job[J21].get("cohort_adjudication_closed") is True,
        "exact_12_streams":
            closure.get("replicate_stream_count") == 12,
        "exact_12456_records":
            closure.get("metric_record_count") == 12456,
        "exact_6540_integrity":
            closure.get("integrity_record_count") == 6540,
        "exact_5916_descriptive":
            closure.get("descriptive_record_count") == 5916,
        "all_integrity_adjudicated_exact_pass":
            closure.get("integrity_adjudication_verdict")
            == "PASS_ALL_EXACT_INTEGRITY",
        "descriptive_evidence_review_valid_no_threshold":
            closure.get("descriptive_evidence_review_verdict")
            == "ACCEPTED_AS_GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_THRESHOLD",
        "cohort_adjudication_closed":
            closure.get("cohort_adjudication_closed") is True,
        "numeric_value_adjudication_not_performed":
            closure.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "zero_automatic_pass_fail":
            closure.get("automatic_scientific_pass_fail_count") == 0,
        "no_majority_vote":
            closure.get("majority_vote_performed") is False,
        "no_result_selected_threshold":
            closure.get("result_selected_threshold_performed") is False,
        "engine_did_not_define_target":
            closure.get("engine_output_defined_arcana_target") is False,
        "j14_partial_1_of_192":
            closure["coverage"][J14]["executed_branches"] == 1
            and closure["coverage"][J14]["total_frozen_branches"] == 192
            and closure["coverage"][J14]["full_job_revalidation_closed"] is False,
        "j18_partial_1_of_64":
            closure["coverage"][J18]["executed_branches"] == 1
            and closure["coverage"][J18]["total_frozen_branches"] == 64
            and closure["coverage"][J18]["full_job_revalidation_closed"] is False,
        "j21_full_1_of_1":
            closure["coverage"][J21]["executed_branches"] == 1
            and closure["coverage"][J21]["total_frozen_branches"] == 1
            and closure["coverage"][J21]["full_job_revalidation_closed"] is True,
        "no_new_scientific_execution":
            cfg.get("new_scientific_engine_execution_performed") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            closure.get("canonical_state_changed") is False
            and cfg.get("canonical_state_changed") is False,
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
        "geonomics_version": "1.4.9",
        "authorized_parent_plan_sha256": EXPECTED_PLAN_SHA,
        "scientific_engine_execution_previously_performed": True,
        "new_scientific_engine_execution_performed": False,
        "scientific_evidence_review_performed": bool(ok),
        "cohort_adjudication_closed": bool(ok),
        "cohort_adjudication_verdict":
            closure.get("cohort_adjudication_verdict"),
        "metric_record_count": closure.get("metric_record_count"),
        "integrity_record_count": closure.get("integrity_record_count"),
        "descriptive_record_count": closure.get("descriptive_record_count"),
        "numeric_scientific_adjudication_of_descriptive_values_performed":
            False,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "j14_full_job_revalidation_closed": False,
        "j14_branch_coverage": "1/192",
        "j18_full_job_revalidation_closed": False,
        "j18_branch_coverage": "1/64",
        "j21_full_job_revalidation_closed": bool(ok),
        "j21_branch_coverage": "1/1",
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R447_EVIDENCE_REVIEW_OR_ADJUDICATION",
    }
    write(root / OUT / "R4_47_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_47_INTEGRATED_AUDIT.json")
    c = load(root / OUT / "R4_47_COHORT_ADJUDICATION_CLOSURE.json")

    checks = {
        "r447_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "scientific_evidence_review_performed":
            a.get("scientific_evidence_review_performed") is True,
        "cohort_adjudication_closed":
            a.get("cohort_adjudication_closed") is True,
        "cohort_verdict_exact":
            a.get("cohort_adjudication_verdict")
            == (
                "VALID_GOVERNED_COHORT_EVIDENCE_WITH_EXACT_INTEGRITY_AND_"
                "DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
            ),
        "exact_12456_records":
            a.get("metric_record_count") == 12456,
        "exact_6540_integrity":
            a.get("integrity_record_count") == 6540,
        "exact_5916_descriptive":
            a.get("descriptive_record_count") == 5916,
        "all_integrity_exact_pass":
            c.get("integrity_adjudication_verdict")
            == "PASS_ALL_EXACT_INTEGRITY",
        "descriptive_review_no_threshold":
            c.get("descriptive_evidence_review_verdict")
            == "ACCEPTED_AS_GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_THRESHOLD",
        "numeric_value_adjudication_not_performed":
            a.get(
                "numeric_scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "zero_automatic_pass_fail":
            a.get("automatic_scientific_pass_fail_count") == 0,
        "zero_divergence_claims":
            a.get("scientific_divergence_claim_count") == 0,
        "j14_not_full_job":
            a.get("j14_full_job_revalidation_closed") is False
            and a.get("j14_branch_coverage") == "1/192",
        "j18_not_full_job":
            a.get("j18_full_job_revalidation_closed") is False
            and a.get("j18_branch_coverage") == "1/64",
        "j21_full_layer_job":
            a.get("j21_full_job_revalidation_closed") is True
            and a.get("j21_branch_coverage") == "1/1",
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
        "next_r448":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
            "AND_COHORT_ADJUDICATION_CLOSURE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "scientific_evidence_review_performed":
                a.get("scientific_evidence_review_performed"),
            "cohort_adjudication_closed":
                a.get("cohort_adjudication_closed"),
            "cohort_adjudication_verdict":
                a.get("cohort_adjudication_verdict"),
            "metric_record_count": a.get("metric_record_count"),
            "integrity_record_count": a.get("integrity_record_count"),
            "descriptive_record_count": a.get("descriptive_record_count"),
            "j14_branch_coverage": "1/192",
            "j14_full_job_revalidation_closed": False,
            "j18_branch_coverage": "1/64",
            "j18_full_job_revalidation_closed": False,
            "j21_branch_coverage": "1/1",
            "j21_full_job_revalidation_closed": True,
            "numeric_scientific_adjudication_of_descriptive_values_performed":
                False,
            "automatic_scientific_pass_fail_count": 0,
            "new_scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
