from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import json
import math

STAGE = "v0.6D1-R4.54"

PARENT_COMPLETE = (
    "PASS_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
    "AND_READOUT_AUTHORITY_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
    "AND_READOUT_AUTHORITY_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R454_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_"
    "DRY_RUN_AND_SCHEMA_VALIDATION"
)

EXPECTED_R452_PLAN_SHA256 = (
    "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
)
EXPECTED_R453_REGISTRY_SHA256 = (
    "f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"
)

COMPLETE = (
    "PASS_R454_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_"
    "DRY_RUN_SCHEMA_VALIDATION_AND_SCIENTIFIC_EXECUTION_AUTHORIZATION_COMPLETE"
)
SEALED = (
    "PASS_R454_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_"
    "DRY_RUN_SCHEMA_VALIDATION_AND_SCIENTIFIC_EXECUTION_AUTHORIZATION_SEALED"
)
BLOCKED = (
    "BLOCKED_R454_SEED_INJECTION_READOUT_EXTRACTION_OR_AUTHORIZATION_FAILURE"
)
NEXT = (
    "BUILD_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_"
    "AND_EVIDENCE_CAPTURE"
)

OUT = Path("outputs/v0_6D1_R4_54")
SEAL = Path("outputs/v0_6D1_R4_54_SEAL/R4_54_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r454_non_geonomics_exact_seed_injection_readout_"
    "extraction_dry_run_schema_validation_authorization_v0_6D1_R4_54.json"
)

R453 = Path("outputs/v0_6D1_R4_53/R4_53_INTEGRATED_AUDIT.json")
R453_SEAL = Path("outputs/v0_6D1_R4_53_SEAL/R4_53_FINAL_SEAL_AUDIT.json")
R453_REGISTRY = Path(
    "outputs/v0_6D1_R4_53/"
    "R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json"
)
R452_PLAN = Path("outputs/v0_6D1_R4_52/R4_52_NON_GEONOMICS_EXECUTION_PLAN.json")
HOST_EVIDENCE = Path(
    "outputs/v0_6D1_R4_54/R4_54_HOST_DRY_RUN_EVIDENCE.json"
)
RUNTIME_EVIDENCE = Path(
    "outputs/v0_6D1_R4_54/R4_54_RUNTIME_IDENTITY_EVIDENCE.json"
)

ENGINE_ORDER = ["Madingley", "RangeShifter", "CDMetaPOP", "NEMO", "SLiM"]

EXPECTED_VERSIONS = {
    "Madingley": "MadingleyR-1.0.6__CPP-2.02",
    "RangeShifter": "3.0.1",
    "CDMetaPOP": "3.08",
    "NEMO": "2.4.2",
    "SLiM": "5.2",
}

EXPECTED_METRICS = {
    "Madingley": {
        "MADINGLEY_COHORT_COUNT_TRAJECTORY",
        "MADINGLEY_STOCK_COUNT_TRAJECTORY",
    },
    "RangeShifter": {
        "RANGESHIFTER_ABUNDANCE_TRAJECTORY",
        "RANGESHIFTER_OCCUPIED_CELL_TRAJECTORY",
    },
    "CDMetaPOP": {
        "CDMETAPOP_POPULATION_STATE_TRAJECTORY",
        "CDMETAPOP_GENETIC_DIVERSITY_TRAJECTORY",
    },
    "NEMO": {
        "NEMO_ALLELE_FREQUENCY_TRAJECTORY",
        "NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY",
    },
    "SLiM": {
        "SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY",
        "SLIM_ANCESTRY_GENE_FLOW_SUMMARY",
    },
}

EXPECTED_SEED_MODES = {
    "Madingley": "R_SET_SEED_BEFORE_MADINGLEY_INIT_AND_RUN",
    "RangeShifter": "RANGESHIFTR_RSSIM_SEED_ARGUMENT",
    "CDMetaPOP": "PYTHON_AND_NUMPY_PROCESS_RNG_SEED_BEFORE_RUNPY",
    "NEMO": "NEMO_RANDOM_SEED_INI_PARAMETER",
    "SLiM": "SLIM_COMMAND_LINE_MINUS_S_SEED",
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
    raw = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_hashed_object(obj: dict[str, Any], key: str, expected: str) -> bool:
    embedded = str(obj.get(key, ""))
    bare = copy.deepcopy(obj)
    bare.pop(key, None)
    return embedded == expected == _sha_json(bare)


def _first_probe_jobs(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for engine in ENGINE_ORDER:
        rows = [j for j in plan["jobs"] if j["engine"] == engine]
        if not rows:
            continue
        out[engine] = rows[0]
    return out


def _finite_tree(obj: Any) -> bool:
    if obj is None or isinstance(obj, (str, bool)):
        return True
    if isinstance(obj, (int, float)):
        return math.isfinite(float(obj))
    if isinstance(obj, list):
        return all(_finite_tree(x) for x in obj)
    if isinstance(obj, dict):
        return all(_finite_tree(v) for v in obj.values())
    return False


def _validate_metric(metric: dict[str, Any], authorized_ids: set[str]) -> bool:
    if str(metric.get("metric_id")) not in authorized_ids:
        return False
    if metric.get("numeric_acceptance_threshold") is not None:
        return False
    if metric.get("automatic_pass_fail_from_value") is not False:
        return False
    if metric.get("finite") is not True:
        return False
    payload = metric.get("payload")
    return _finite_tree(payload)


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R453)
    parent_seal = load(root / R453_SEAL)
    registry = load(root / R453_REGISTRY)
    plan = load(root / R452_PLAN)
    host = load(root / HOST_EVIDENCE)
    runtime = load(root / RUNTIME_EVIDENCE)

    probes = _first_probe_jobs(plan)
    rows = {
        str(x["engine"]): x
        for x in (host.get("dry_runs") or [])
        if isinstance(x, dict)
    }

    per_engine = {}
    all_metric_ids = []
    for engine in ENGINE_ORDER:
        probe = probes[engine]
        row = rows.get(engine, {})
        expected_seed = int(probe["frozen_seeds"][0])
        authorized_ids = EXPECTED_METRICS[engine]
        metrics = row.get("metrics") or []
        metric_ids = {str(m.get("metric_id")) for m in metrics if isinstance(m, dict)}
        metric_schema_pass = (
            len(metrics) == 2
            and metric_ids == authorized_ids
            and all(
                isinstance(m, dict) and _validate_metric(m, authorized_ids)
                for m in metrics
            )
        )
        all_metric_ids.extend(sorted(metric_ids))

        checks = {
            "row_present": bool(row),
            "status_pass": row.get("status") == "PASS",
            "returncode_zero": row.get("returncode") == 0,
            "confirmed_version_exact":
                str(row.get("confirmed_version")) == EXPECTED_VERSIONS[engine],
            "probe_job_id_exact":
                row.get("probe_job_id") == probe["job_id"],
            "probe_seed_exact":
                int(row.get("frozen_seed", -1)) == expected_seed,
            "seed_injection_mode_exact":
                row.get("seed_injection_mode") == EXPECTED_SEED_MODES[engine],
            "seed_binding_verified":
                row.get("seed_binding_verified") is True,
            "dry_run_true":
                row.get("dry_run") is True,
            "scientific_evidence_false":
                row.get("scientific_evidence") is False,
            "metric_schema_exact":
                metric_schema_pass,
            "unauthorized_metric_count_zero":
                row.get("unauthorized_metric_count") == 0,
            "numeric_threshold_count_zero":
                row.get("numeric_acceptance_threshold_count") == 0,
            "automatic_pass_fail_count_zero":
                row.get("automatic_scientific_pass_fail_count") == 0,
            "artifact_hashes_present":
                isinstance(row.get("artifact_hashes"), dict)
                and len(row.get("artifact_hashes")) >= 1
                and all(
                    isinstance(v, str) and len(v) == 64
                    for v in row.get("artifact_hashes", {}).values()
                ),
            "canonical_unchanged":
                row.get("canonical_state_changed") is False,
        }
        per_engine[engine] = {
            "pass": all(checks.values()),
            "checks": checks,
            "probe_job_id": probe["job_id"],
            "frozen_seed": expected_seed,
            "metric_ids": sorted(metric_ids),
        }

    runtime_rows = {
        str(x["engine"]): x for x in runtime.get("engines", [])
        if isinstance(x, dict)
    }

    checks = {
        "parent_r453_complete_39_39":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 39
            and parent.get("checks_failed") == 0,
        "parent_r453_sealed_23_23":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 23
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r454":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R454_REAL_FIVE_ENGINE_DISPOSABLE_DRY_RUN_THEN_AUTHORIZE_FROZEN_80_STREAM_PLAN",
        "r452_plan_hash_exact":
            _verify_hashed_object(
                plan, "plan_sha256", EXPECTED_R452_PLAN_SHA256
            ),
        "r453_registry_hash_exact":
            _verify_hashed_object(
                registry, "registry_sha256", EXPECTED_R453_REGISTRY_SHA256
            ),
        "runtime_identity_all_six_ready":
            runtime.get("all_required_engines_ready") is True
            and len(runtime.get("ready_engines") or []) == 6,
        "five_non_geonomics_runtime_versions_exact":
            all(
                e in runtime_rows
                and runtime_rows[e].get("status") == "READY"
                and str(runtime_rows[e].get("confirmed_version"))
                    == EXPECTED_VERSIONS[e]
                for e in ENGINE_ORDER
            ),
        "host_evidence_type_exact":
            host.get("evidence_type")
            == "NON_SCIENTIFIC_FIVE_ENGINE_SEED_AND_READOUT_DRY_RUN_EVIDENCE",
        "host_parent_plan_hash_exact":
            host.get("parent_execution_plan_sha256")
            == EXPECTED_R452_PLAN_SHA256,
        "host_parent_registry_hash_exact":
            host.get("parent_readout_registry_sha256")
            == EXPECTED_R453_REGISTRY_SHA256,
        "exact_five_dry_runs":
            host.get("dry_run_count") == 5 and len(rows) == 5,
        "all_five_dry_runs_pass":
            all(per_engine[e]["pass"] for e in ENGINE_ORDER),
        "exact_ten_authorized_metric_ids":
            len(all_metric_ids) == 10
            and len(set(all_metric_ids)) == 10
            and set(all_metric_ids)
                == set().union(*EXPECTED_METRICS.values()),
        "all_80_plan_seeds_positive_int":
            len([
                s for j in plan["jobs"] for s in j["frozen_seeds"]
            ]) == 80
            and all(
                isinstance(s, int) and not isinstance(s, bool) and 0 < s < 2**31
                for j in plan["jobs"]
                for s in j["frozen_seeds"]
            ),
        "all_80_plan_seeds_unique":
            len({
                s for j in plan["jobs"] for s in j["frozen_seeds"]
            }) == 80,
        "no_historical_job_execution_in_dry_run":
            host.get("historical_job_execution_performed") is False,
        "dry_runs_not_scientific_evidence":
            host.get("scientific_engine_execution_performed") is False
            and host.get("scientific_evidence_claimed") is False,
        "zero_numeric_thresholds":
            host.get("numeric_acceptance_threshold_count") == 0,
        "zero_automatic_pass_fail":
            host.get("automatic_scientific_pass_fail_count") == 0,
        "no_majority_vote":
            registry.get("majority_vote_authorized") is False,
        "no_result_selected_metric":
            registry.get("result_selected_metric_authorized") is False,
        "no_result_selected_threshold":
            registry.get("result_selected_threshold_authorized") is False,
        "engine_cannot_define_target":
            registry.get("engine_output_defines_arcana_target") is False,
        "canonical_rewrite_forbidden":
            registry.get("canonical_rewrite_authorized") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False
            and host.get("canonical_state_changed") is False,
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

    authorization = {
        "stage": STAGE,
        "status":
            "R454_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AUTHORIZED"
            if ok else BLOCKED,
        "parent_execution_plan_sha256": EXPECTED_R452_PLAN_SHA256,
        "parent_readout_registry_sha256": EXPECTED_R453_REGISTRY_SHA256,
        "authorized_job_count": 20 if ok else 0,
        "authorized_scientific_stream_count": 80 if ok else 0,
        "scientific_execution_authorized": bool(ok),
        "authorization_scope":
            "EXACT_R452_20_JOBS_X_EXACT_FOUR_FROZEN_SEEDS"
            if ok else None,
        "readout_authority":
            "EXACT_R453_TEN_METRIC_DEFINITIONS"
            if ok else None,
        "dry_run_evidence_is_scientific_evidence": False,
        "historical_execution_performed_in_r454": False,
        "automatic_scientific_pass_fail_count": 0,
        "numeric_acceptance_threshold_count": 0,
        "canonical_state_changed": False,
    }
    write(root / OUT / "R4_54_SCIENTIFIC_EXECUTION_AUTHORIZATION.json", authorization)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "engine_dry_run_results": per_engine,
        "engine_count": 5,
        "job_count": 20,
        "planned_scientific_stream_count": 80,
        "authorized_metric_definition_count": 10,
        "exact_seed_injection_dry_run_validated": bool(ok),
        "readout_extraction_dry_run_validated": bool(ok),
        "scientific_execution_authorized": bool(ok),
        "scientific_engine_execution_performed": False,
        "dry_run_is_scientific_evidence": False,
        "multi_engine_full_revalidation_closed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R454_SEED_OR_READOUT_DRY_RUN",
    }
    write(root / OUT / "R4_54_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_54_INTEGRATED_AUDIT.json")
    auth = load(root / OUT / "R4_54_SCIENTIFIC_EXECUTION_AUTHORIZATION.json")

    checks = {
        "r454_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "five_engine_dry_runs_pass":
            all(
                x.get("pass") is True
                for x in a.get("engine_dry_run_results", {}).values()
            )
            and len(a.get("engine_dry_run_results", {})) == 5,
        "seed_injection_validated":
            a.get("exact_seed_injection_dry_run_validated") is True,
        "readout_extraction_validated":
            a.get("readout_extraction_dry_run_validated") is True,
        "exact_20_jobs":
            a.get("job_count") == 20,
        "exact_80_streams":
            a.get("planned_scientific_stream_count") == 80,
        "exact_10_metrics":
            a.get("authorized_metric_definition_count") == 10,
        "scientific_execution_authorized":
            a.get("scientific_execution_authorized") is True
            and auth.get("scientific_execution_authorized") is True,
        "authorization_exact_80":
            auth.get("authorized_scientific_stream_count") == 80,
        "dry_run_not_scientific_evidence":
            a.get("dry_run_is_scientific_evidence") is False
            and auth.get("dry_run_evidence_is_scientific_evidence") is False,
        "no_historical_execution_yet":
            a.get("scientific_engine_execution_performed") is False
            and auth.get("historical_execution_performed_in_r454") is False,
        "zero_numeric_thresholds":
            auth.get("numeric_acceptance_threshold_count") == 0,
        "zero_automatic_pass_fail":
            auth.get("automatic_scientific_pass_fail_count") == 0,
        "multi_engine_not_closed":
            a.get("multi_engine_full_revalidation_closed") is False,
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
        "next_r455":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_"
            "DRY_RUN_SCHEMA_VALIDATION_AND_SCIENTIFIC_EXECUTION_AUTHORIZATION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "engine_count": 5,
            "job_count": 20,
            "planned_scientific_stream_count": 80,
            "authorized_metric_definition_count": 10,
            "exact_seed_injection_dry_run_validated":
                a.get("exact_seed_injection_dry_run_validated"),
            "readout_extraction_dry_run_validated":
                a.get("readout_extraction_dry_run_validated"),
            "scientific_execution_authorized":
                a.get("scientific_execution_authorized"),
            "scientific_engine_execution_performed": False,
            "dry_run_is_scientific_evidence": False,
            "multi_engine_full_revalidation_closed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
