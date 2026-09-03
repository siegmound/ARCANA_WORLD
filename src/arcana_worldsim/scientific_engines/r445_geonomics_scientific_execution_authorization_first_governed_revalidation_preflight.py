from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

STAGE = "v0.6D1-R4.45"

PARENT_COMPLETE = (
    "PASS_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
    "VALIDATION_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
    "VALIDATION_SEALED"
)
PARENT_NEXT = (
    "BUILD_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
    "GOVERNED_REVALIDATION_RUN_PREFLIGHT"
)

COMPLETE = (
    "PASS_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
    "GOVERNED_REVALIDATION_RUN_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
    "GOVERNED_REVALIDATION_RUN_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R445_SCIENTIFIC_EXECUTION_AUTHORIZATION_OR_FIRST_GOVERNED_"
    "REVALIDATION_RUN_PREFLIGHT_FAILURE"
)
NEXT = (
    "BUILD_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
    "AND_EVIDENCE_CAPTURE"
)

OUT = Path("outputs/v0_6D1_R4_45")
SEAL = Path("outputs/v0_6D1_R4_45_SEAL/R4_45_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r445_geonomics_scientific_execution_authorization_"
    "first_governed_revalidation_run_preflight_v0_6D1_R4_45.json"
)

R444 = Path("outputs/v0_6D1_R4_44/R4_44_INTEGRATED_AUDIT.json")
R444_SEAL = Path("outputs/v0_6D1_R4_44_SEAL/R4_44_FINAL_SEAL_AUDIT.json")
R443_REGISTRY = Path(
    "outputs/v0_6D1_R4_43/R4_43_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY.json"
)
R443_EXTRACTION = Path(
    "outputs/v0_6D1_R4_43/R4_43_METRIC_EXTRACTION_SCHEMA.json"
)
R443_ADJUDICATION = Path(
    "outputs/v0_6D1_R4_43/R4_43_ADJUDICATION_SCHEMA.json"
)
R436_NATIVE = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
)

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

FROZEN_SEEDS = {
    J14: [310746493, 1894477382, 1291996560, 1554786554],
    J18: [999124684, 1705133798, 1085091276, 555097754],
    J21: [1617603515, 1207292893, 1138693833, 989125497],
}

AUTHORIZED_METRICS = {
    J14: [
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
    ],
    J18: [
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
    ],
    J21: [
        "GNX_NATIVE_LAYER_RASTER_READBACK",
        "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY",
    ],
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


def _native_seed_rows(native: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    rows = [
        r for r in (native.get("records") or [])
        if r.get("job_id") == job_id and r.get("construction_pass") is True
    ]
    return sorted(rows, key=lambda r: int(r["replicate_index"]))


def _freeze_run_plan(
    registry: dict[str, Any],
    extraction: dict[str, Any],
    adjudication: dict[str, Any],
    native: dict[str, Any],
) -> dict[str, Any]:
    jobs = {}

    for job_id in (J14, J18, J21):
        rows = _native_seed_rows(native, job_id)
        observed_seeds = [int(r["frozen_seed"]) for r in rows]
        if observed_seeds != FROZEN_SEEDS[job_id]:
            raise RuntimeError(
                f"{job_id} frozen seed mismatch: {observed_seeds}"
            )

        registry_metrics = list(registry["jobs"][job_id]["authorized_metrics"])
        if registry_metrics != AUTHORIZED_METRICS[job_id]:
            raise RuntimeError(
                f"{job_id} R4.43 metric authority mismatch"
            )

        if job_id == J14:
            jobs[job_id] = {
                "scope_class": "FIRST_GOVERNED_SCIENTIFIC_COHORT",
                "branch_selector":
                    "member_index_0_candidate_index_0_FROZEN_ORDER",
                "branch_count": 1,
                "canonical_state_count": 141,
                "transition_count": 140,
                "replicate_count": 4,
                "frozen_seeds": observed_seeds,
                "metric_ids": registry_metrics,
                "expected_metric_records":
                    141 * 4 * 3,
                "expected_integrity_records":
                    141 * 4 * 2,
                "expected_descriptive_records":
                    141 * 4 * 1,
                "claim_scope":
                    "DESCRIPTIVE_SPATIAL_CONNECTIVITY_OF_MODEL_DERIVED_"
                    "CANONICAL_DEME_SUPPORTS_FOR_THIS_FROZEN_COHORT_ONLY",
                "observed_history_claim": False,
                "full_job_revalidation_claim": False,
            }
        elif job_id == J18:
            jobs[job_id] = {
                "scope_class": "FIRST_GOVERNED_SCIENTIFIC_COHORT",
                "branch_selector":
                    "member_index_0_candidate_index_0_FROZEN_ORDER",
                "branch_count": 1,
                "canonical_state_count": 15,
                "transition_count": 14,
                "replicate_count": 4,
                "frozen_seeds": observed_seeds,
                "metric_ids": registry_metrics,
                "expected_metric_records":
                    15 * 4 * 3,
                "expected_integrity_records":
                    15 * 4 * 2,
                "expected_descriptive_records":
                    15 * 4 * 1,
                "claim_scope":
                    "DESCRIPTIVE_SPATIAL_CONNECTIVITY_OF_CANONICAL_"
                    "SNAPSHOT_DEME_SUPPORTS_FOR_THIS_FROZEN_COHORT_ONLY",
                "observed_history_claim": False,
                "full_job_revalidation_claim": False,
            }
        else:
            jobs[job_id] = {
                "scope_class": "FIRST_GOVERNED_SCIENTIFIC_COHORT",
                "branch_selector":
                    "FULL_FROZEN_J21_LAYER_SEQUENCE",
                "branch_count": 1,
                "canonical_state_count": 9,
                "transition_count": 8,
                "native_dynamic_layer_count": 147,
                "dynamic_sidecar_count": 4,
                "replicate_count": 4,
                "frozen_seeds": observed_seeds,
                "metric_ids": registry_metrics,
                "expected_metric_records":
                    9 * 4 * 147 * 2,
                "expected_integrity_records":
                    9 * 4 * 147,
                "expected_descriptive_records":
                    9 * 4 * 147,
                "claim_scope":
                    "DESCRIPTIVE_NATIVE_LAYER_STATE_EVIDENCE_FOR_147_"
                    "AUTHORIZED_LAYERS_ONLY",
                "observed_history_claim": False,
                "full_job_revalidation_claim": True,
            }

    total_metric = sum(x["expected_metric_records"] for x in jobs.values())
    total_integrity = sum(
        x["expected_integrity_records"] for x in jobs.values()
    )
    total_descriptive = sum(
        x["expected_descriptive_records"] for x in jobs.values()
    )

    plan = {
        "stage": STAGE,
        "status": "R445_FIRST_GOVERNED_REVALIDATION_RUN_PLAN_FROZEN",
        "execution_engine": "Geonomics 1.4.9",
        "execution_queue": "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "default_geonomics_queue_authorized": False,
        "jobs": jobs,
        "expected_metric_record_count": total_metric,
        "expected_integrity_record_count": total_integrity,
        "expected_descriptive_record_count": total_descriptive,
        "expected_replicate_stream_count": 12,
        "authorized_metric_definition_count": 5,
        "adjudicative_numeric_threshold_count":
            int(adjudication["adjudicative_numeric_threshold_count"]),
        "raw_nn_vector_preserved":
            extraction["carrier_nn_distance_schema"]["raw_vector_preserved"],
        "j21_four_sidecars_excluded":
            extraction["layer_summary_schema"]["four_sidecars_excluded"],
        "scientific_claim_language": {
            "allowed":
                "Geonomics-native descriptive readouts were recorded for the "
                "predeclared frozen cohort under exact ARCANA replay authority.",
            "forbidden": [
                "Geonomics predicted ARCANA historical locations",
                "Geonomics independently generated ARCANA demographic history",
                "descriptive metric value passed or failed a numeric target",
                "external engine result defines or rewrites canonical state",
                "first J14/J18 cohort constitutes full-job revalidation",
            ],
        },
        "failure_semantics": {
            "integrity_mismatch":
                "ADAPTER_OR_RUNTIME_INTEGRITY_FAILURE_FAIL_CLOSED",
            "forbidden_metric_emission":
                "SCIENTIFIC_EVIDENCE_SCHEMA_FAILURE_FAIL_CLOSED",
            "nonfinite_descriptive_metric":
                "READOUT_EXTRACTION_FAILURE_FAIL_CLOSED",
            "descriptive_numeric_value":
                "RECORDED_WITHOUT_AUTOMATIC_PASS_FAIL",
        },
        "result_selected_branch_choice": False,
        "result_selected_metric_choice": False,
        "result_selected_threshold": False,
        "majority_vote_authorized": False,
        "engine_output_defines_arcana_target": False,
        "canonical_rewrite_authorized": False,
    }
    plan["plan_sha256"] = _sha_json(plan)
    return plan


def _execution_authorization(plan: dict[str, Any]) -> dict[str, Any]:
    exact_counts = (
        plan["expected_metric_record_count"] == 12456
        and plan["expected_integrity_record_count"] == 6540
        and plan["expected_descriptive_record_count"] == 5916
        and plan["expected_replicate_stream_count"] == 12
    )
    ok = all([
        plan["execution_queue"]
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        plan["default_geonomics_queue_authorized"] is False,
        exact_counts,
        plan["adjudicative_numeric_threshold_count"] == 0,
        plan["result_selected_branch_choice"] is False,
        plan["result_selected_metric_choice"] is False,
        plan["result_selected_threshold"] is False,
        plan["majority_vote_authorized"] is False,
        plan["engine_output_defines_arcana_target"] is False,
        plan["canonical_rewrite_authorized"] is False,
    ])
    return {
        "stage": STAGE,
        "status":
            "R445_SCIENTIFIC_EXECUTION_AUTHORIZED_FOR_FROZEN_FIRST_COHORT"
            if ok else BLOCKED,
        "authorization_scope":
            "FIRST_GOVERNED_REVALIDATION_COHORT_ONLY",
        "scientific_execution_authorized": bool(ok),
        "geonomics_execution_ready": bool(ok),
        "first_governed_revalidation_run_authorized": bool(ok),
        "first_governed_revalidation_run_executed": False,
        "scientific_engine_execution_performed": False,
        "authorized_plan_sha256": plan["plan_sha256"] if ok else None,
        "production_queue":
            "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "readout_authority":
            "R4.43_SEALED_FIVE_METRIC_DEFINITIONS",
        "adjudication_authority":
            "R4.43_SEALED_ZERO_NUMERIC_THRESHOLD_SCHEMA",
        "scientific_result_can_change_canonical_state": False,
        "scientific_result_can_define_arcana_target": False,
        "scientific_result_automatic_pass_fail": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R444)
    parent_seal = load(root / R444_SEAL)
    registry = load(root / R443_REGISTRY)
    extraction = load(root / R443_EXTRACTION)
    adjudication = load(root / R443_ADJUDICATION)
    native = load(root / R436_NATIVE)

    plan = _freeze_run_plan(registry, extraction, adjudication, native)
    auth = _execution_authorization(plan)

    write(root / OUT / "R4_45_FIRST_GOVERNED_REVALIDATION_RUN_PLAN.json", plan)
    write(root / OUT / "R4_45_SCIENTIFIC_EXECUTION_AUTHORIZATION.json", auth)

    checks = {
        "parent_r444_complete_38_38":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 38
            and parent.get("checks_failed") == 0,
        "parent_r444_sealed_23_23":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 23
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r445":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R445_AUTHORIZE_ONLY_PREDECLARED_FIRST_SCIENTIFIC_COHORT",
        "production_queue_authorized":
            parent.get("production_execution_queue_authorized") is True
            and parent.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "readout_authority_closed":
            parent.get("scientific_readout_authority_closed") is True,
        "metric_extraction_dry_run_validated":
            parent.get("metric_extraction_dry_run_validated") is True,
        "adjudication_input_closed":
            parent.get("adjudication_input_validation_closed") is True,
        "r444_2400_transport_records_validated":
            parent.get("metric_record_count") == 2400
            and parent.get("integrity_record_count") == 1208
            and parent.get("descriptive_record_count") == 1192,
        "five_metric_definitions_preserved":
            plan.get("authorized_metric_definition_count") == 5,
        "frozen_seed_vectors_exact":
            all(
                plan["jobs"][jid]["frozen_seeds"] == FROZEN_SEEDS[jid]
                for jid in (J14, J18, J21)
            ),
        "j14_first_branch_frozen":
            plan["jobs"][J14]["branch_selector"]
            == "member_index_0_candidate_index_0_FROZEN_ORDER",
        "j18_first_branch_frozen":
            plan["jobs"][J18]["branch_selector"]
            == "member_index_0_candidate_index_0_FROZEN_ORDER",
        "j21_full_layer_sequence_frozen":
            plan["jobs"][J21]["branch_selector"]
            == "FULL_FROZEN_J21_LAYER_SEQUENCE",
        "j14_not_full_job_claim":
            plan["jobs"][J14]["full_job_revalidation_claim"] is False,
        "j18_not_full_job_claim":
            plan["jobs"][J18]["full_job_revalidation_claim"] is False,
        "j21_full_job_claim_limited_to_layer_job":
            plan["jobs"][J21]["full_job_revalidation_claim"] is True,
        "observed_history_claim_off_all_jobs":
            all(
                plan["jobs"][jid]["observed_history_claim"] is False
                for jid in (J14, J18, J21)
            ),
        "expected_12456_metric_records":
            plan.get("expected_metric_record_count") == 12456,
        "expected_6540_integrity_records":
            plan.get("expected_integrity_record_count") == 6540,
        "expected_5916_descriptive_records":
            plan.get("expected_descriptive_record_count") == 5916,
        "expected_12_replicate_streams":
            plan.get("expected_replicate_stream_count") == 12,
        "zero_numeric_thresholds":
            plan.get("adjudicative_numeric_threshold_count") == 0,
        "raw_nn_vector_preserved":
            plan.get("raw_nn_vector_preserved") is True,
        "j21_sidecars_excluded":
            plan.get("j21_four_sidecars_excluded") is True,
        "no_result_selected_branch":
            plan.get("result_selected_branch_choice") is False,
        "no_result_selected_metric":
            plan.get("result_selected_metric_choice") is False,
        "no_result_selected_threshold":
            plan.get("result_selected_threshold") is False,
        "no_majority_vote":
            plan.get("majority_vote_authorized") is False,
        "engine_cannot_define_arcana_target":
            plan.get("engine_output_defines_arcana_target") is False,
        "canonical_rewrite_forbidden":
            plan.get("canonical_rewrite_authorized") is False,
        "scientific_execution_authorized":
            auth.get("scientific_execution_authorized") is True,
        "geonomics_execution_ready":
            auth.get("geonomics_execution_ready") is True,
        "first_governed_run_authorized":
            auth.get("first_governed_revalidation_run_authorized") is True,
        "first_governed_run_not_executed":
            auth.get("first_governed_revalidation_run_executed") is False,
        "no_scientific_execution_yet":
            auth.get("scientific_engine_execution_performed") is False,
        "authorization_plan_hash_exact":
            auth.get("authorized_plan_sha256") == plan.get("plan_sha256"),
        "scientific_result_cannot_change_canon":
            auth.get("scientific_result_can_change_canonical_state") is False,
        "scientific_result_cannot_define_target":
            auth.get("scientific_result_can_define_arcana_target") is False,
        "scientific_result_no_automatic_pass_fail":
            auth.get("scientific_result_automatic_pass_fail") is False,
        "target_numeric_not_executed":
            cfg.get("target_numeric_execution_performed") is False,
        "readjudication_not_performed":
            cfg.get("readjudication_performed") is False,
        "canonical_state_unchanged":
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
        "geonomics_version": "1.4.9",
        "production_execution_queue_authorized": True,
        "authorized_queue": "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "scientific_readout_authority_closed": True,
        "metric_extraction_dry_run_validated": True,
        "adjudication_input_validation_closed": True,
        "first_governed_revalidation_run_plan_sha256":
            plan.get("plan_sha256"),
        "first_governed_revalidation_scope":
            "DETERMINISTIC_FROZEN_COHORT",
        "expected_metric_record_count":
            plan.get("expected_metric_record_count"),
        "expected_integrity_record_count":
            plan.get("expected_integrity_record_count"),
        "expected_descriptive_record_count":
            plan.get("expected_descriptive_record_count"),
        "expected_replicate_stream_count":
            plan.get("expected_replicate_stream_count"),
        "scientific_execution_authorized": bool(ok),
        "geonomics_execution_ready": bool(ok),
        "first_governed_revalidation_run_authorized": bool(ok),
        "first_governed_revalidation_run_executed": False,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R445_SCIENTIFIC_EXECUTION_AUTHORIZATION",
    }
    write(root / OUT / "R4_45_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_45_INTEGRATED_AUDIT.json")
    plan = load(root / OUT / "R4_45_FIRST_GOVERNED_REVALIDATION_RUN_PLAN.json")
    auth = load(root / OUT / "R4_45_SCIENTIFIC_EXECUTION_AUTHORIZATION.json")

    checks = {
        "r445_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "production_queue_authorized":
            a.get("production_execution_queue_authorized") is True,
        "readout_authority_closed":
            a.get("scientific_readout_authority_closed") is True,
        "metric_dry_run_validated":
            a.get("metric_extraction_dry_run_validated") is True,
        "adjudication_input_closed":
            a.get("adjudication_input_validation_closed") is True,
        "plan_hash_exact":
            a.get("first_governed_revalidation_run_plan_sha256")
            == plan.get("plan_sha256")
            == auth.get("authorized_plan_sha256"),
        "expected_12456_records":
            a.get("expected_metric_record_count") == 12456,
        "expected_6540_integrity":
            a.get("expected_integrity_record_count") == 6540,
        "expected_5916_descriptive":
            a.get("expected_descriptive_record_count") == 5916,
        "expected_12_streams":
            a.get("expected_replicate_stream_count") == 12,
        "zero_numeric_thresholds":
            plan.get("adjudicative_numeric_threshold_count") == 0,
        "no_majority_vote":
            plan.get("majority_vote_authorized") is False,
        "no_result_selected_branch":
            plan.get("result_selected_branch_choice") is False,
        "no_result_selected_metric":
            plan.get("result_selected_metric_choice") is False,
        "no_result_selected_threshold":
            plan.get("result_selected_threshold") is False,
        "engine_target_definition_forbidden":
            plan.get("engine_output_defines_arcana_target") is False,
        "canonical_rewrite_forbidden":
            plan.get("canonical_rewrite_authorized") is False,
        "scientific_execution_authorized":
            a.get("scientific_execution_authorized") is True,
        "execution_ready":
            a.get("geonomics_execution_ready") is True,
        "first_governed_run_authorized":
            a.get("first_governed_revalidation_run_authorized") is True,
        "first_run_not_yet_executed":
            a.get("first_governed_revalidation_run_executed") is False,
        "no_scientific_execution_yet":
            a.get("scientific_engine_execution_performed") is False,
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
        "next_r446":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())
    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
            "GOVERNED_REVALIDATION_RUN_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "production_execution_queue_authorized": True,
            "scientific_readout_authority_closed": True,
            "metric_extraction_dry_run_validated": True,
            "adjudication_input_validation_closed": True,
            "first_governed_revalidation_run_plan_sha256":
                a.get("first_governed_revalidation_run_plan_sha256"),
            "expected_metric_record_count":
                a.get("expected_metric_record_count"),
            "scientific_execution_authorized":
                a.get("scientific_execution_authorized"),
            "geonomics_execution_ready":
                a.get("geonomics_execution_ready"),
            "first_governed_revalidation_run_authorized":
                a.get("first_governed_revalidation_run_authorized"),
            "first_governed_revalidation_run_executed": False,
            "scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
