from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STAGE = "v0.6D1-R4.22"
PARENT_SEALED = "PASS_R421_P2_ADAPTER_IMPLEMENTATION_STATIC_VALIDATION_AND_SYMMETRIC_REEXECUTION_AUTHORIZATION_SEALED"
COMPLETE = "PASS_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION_COMPLETE"
SEALED = "PASS_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION_SEALED"
BLOCKED = "BLOCKED_R422_AUTHORIZED_EXECUTION_OR_DEFERRED_COMPLETION_FAILURE"

CFG = Path("configs/world1_r422_authorized_p2_reexecution_v0_6D1_R4_22.json")
PSEAL = Path("outputs/v0_6D1_R4_21_SEAL/R4_21_FINAL_SEAL_AUDIT.json")
AUTH = Path("outputs/v0_6D1_R4_21/R4_21_SYMMETRIC_REEXECUTION_AUTHORIZATION.json")
P2VAL = Path("outputs/v0_6D1_R4_21/R4_21_P2_STATIC_VALIDATION.json")
R42 = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
OUT = Path("outputs/v0_6D1_R4_22")
SEAL = Path("outputs/v0_6D1_R4_22_SEAL/R4_22_FINAL_SEAL_AUDIT.json")

ADAPTER_PATHS = {
    "NEMO": Path("benchmarks/r421/nemo_r421.py"),
    "SLiM": Path("benchmarks/r421/slim_r421.py"),
    "CDMetaPOP": Path("benchmarks/r421/cdmetapop_r421_matched.py"),
    "Geonomics": Path("benchmarks/r421/geonomics_r421.py"),
}

GEONOMICS_JOBS = {
    "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS": {
        "window": "SAPIENT_3MA_TO_200KA",
        "sources": [
            ("outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz", ["age_ma", "state", "candidate_ids"]),
            ("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz", ["snapshot_deme_state", "snapshot_active", "snapshot_age_ka", "state_variable_names"]),
        ],
        "required_status": "DEFERRED_WINDOW_START_SPATIAL_BINDING_INCOMPLETE",
    },
    "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS": {
        "window": "SAPIENT_200KA_TO_0",
        "sources": [
            ("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz", ["snapshot_deme_state", "snapshot_active", "snapshot_age_ka", "state_variable_names"]),
        ],
        "required_status": "CANONICAL_SPATIAL_SOURCE_AVAILABLE_PARAMETER_TRANSLATION_REQUIRED",
    },
    "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS": {
        "window": "PRODUCER_20KA_TO_0",
        "sources": [
            ("outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz", ["anchor_age_ka", "environment_fields", "environment_variable_names"]),
            ("outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz", ["anchor_age_ka", "producer_landscape", "landscape_variable_names"]),
        ],
        "required_status": "CANONICAL_SPATIAL_SOURCE_AVAILABLE_PARAMETER_TRANSLATION_REQUIRED",
    },
}

@dataclass
class Check:
    name: str
    passed: bool
    detail: Any = None
    def d(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _contract_path(root: Path, job_id: str) -> Path:
    return root / "outputs" / "v0_6D1_R4_3" / "jobs" / job_id / "JOB_CONTRACT.json"


def _r47_profile_path(root: Path, job_id: str) -> Path:
    return root / "outputs" / "v0_6D1_R4_7" / "jobs" / job_id / "REPAIR_PROFILE.json"


def _contract_seed_ledger(contract: dict[str, Any]) -> list[dict[str, int]]:
    reps = contract.get("engine_input", {}).get("replicates") or []
    out = []
    for r in reps:
        out.append({"replicate_index": int(r["replicate_index"]), "seed": int(r["seed"])})
    return out


def _adapter_hash_registry(p2val: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in p2val.get("engine_families") or []:
        eng = rec.get("engine")
        cand = rec.get("candidate_adapter") or {}
        if eng:
            out[str(eng)] = cand
    return out


def _npz_key_audit(path: Path, required: list[str]) -> dict[str, Any]:
    rec: dict[str, Any] = {"path": path.as_posix(), "present": path.exists(), "required_keys": required}
    if not path.exists():
        rec.update({"sha256": None, "keys": [], "required_keys_present": False})
        return rec
    rec["sha256"] = sha256(path)
    try:
        import numpy as np
        with np.load(path, allow_pickle=False) as z:
            keys = list(z.files)
        rec["keys"] = keys
        rec["required_keys_present"] = all(k in keys for k in required)
    except Exception as exc:
        rec["keys"] = []
        rec["required_keys_present"] = False
        rec["error"] = repr(exc)
    return rec


def deferred_geonomics_completion_audit(root: Path) -> dict[str, Any]:
    records = []
    for job_id, spec in GEONOMICS_JOBS.items():
        sources = [_npz_key_audit(root / rel, req) for rel, req in spec["sources"]]
        all_sources = all(s.get("present") and s.get("required_keys_present") for s in sources)
        # R4.22 never synthesizes a raster from scalar descriptors. J14 remains the family blocker
        # because R3.27 is macro/non-spatial and R3.28 only starts at the 200 ka boundary.
        if job_id.endswith("J14_SAPIENT_3MA_TO_200KA_GEONOMICS"):
            status = "DEFERRED_WINDOW_START_SPATIAL_BINDING_INCOMPLETE" if all_sources else "DEFERRED_CANONICAL_SPATIAL_SOURCE_MISSING_OR_INCOMPLETE"
            parameter_translation_authorized = False
        else:
            status = "CANONICAL_SPATIAL_SOURCE_AVAILABLE_PARAMETER_TRANSLATION_REQUIRED" if all_sources else "DEFERRED_CANONICAL_SPATIAL_SOURCE_MISSING_OR_INCOMPLETE"
            parameter_translation_authorized = bool(all_sources)
        records.append({
            "job_id": job_id,
            "window_id": spec["window"],
            "status": status,
            "canonical_spatial_sources": sources,
            "scalar_descriptor_synthesis_forbidden": True,
            "default_geonomics_model_forbidden_for_adjudication": True,
            "parameter_translation_authorized_for_future_stage": parameter_translation_authorized,
            "engine_execution_authorized_in_r422": False,
        })
    family_ready = all(r["status"] == "CANONICAL_SPATIAL_BINDING_MATERIALIZED" for r in records)
    return {
        "stage": STAGE,
        "status": "R422_GEONOMICS_DEFERRED_IMPLEMENTATION_COMPLETION_AUDITED",
        "record_count": len(records),
        "records": records,
        "geonomics_family_ready_for_execution": family_ready,
        "geonomics_execution_authorized_in_r422": False,
        "blocking_reason": None if family_ready else "FULL_FROZEN_GEONOMICS_JOB_SET_LACKS_MATERIALIZED_CANONICAL_SPATIAL_BINDING",
        "next_required_work": "R423_CANONICAL_SPATIAL_BINDING_PARAMETER_TRANSLATION_AND_J14_PRE_200KA_SPATIAL_SOURCE_CLOSURE",
    }


def prepare(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    auth = load(root / AUTH) if (root / AUTH).exists() else {}
    p2val = load(root / P2VAL) if (root / P2VAL).exists() else {}
    r42 = load(root / R42) if (root / R42).exists() else {}
    checks: list[Check] = []
    checks += [
        Check("parent_r421_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r421_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r422", pseal.get("next_action") == "BUILD_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION", pseal.get("next_action")),
        Check("authorization_registry_frozen", auth.get("status") == "R421_SYMMETRIC_REEXECUTION_AUTHORIZATION_FROZEN", auth.get("status")),
        Check("authorized_job_count_exact_11", auth.get("authorized_job_count") == 11 and len(auth.get("authorized_job_ids") or []) == 11, auth.get("authorized_job_count")),
        Check("authorized_engine_families_exact", set(auth.get("authorized_engine_families") or []) == {"CDMetaPOP", "NEMO", "SLiM"}, auth.get("authorized_engine_families")),
        Check("geonomics_deferred", auth.get("deferred_engine_families") == ["Geonomics"], auth.get("deferred_engine_families")),
        Check("r42_frozen_registry_exact_23", r42.get("job_count") == 23 and len(r42.get("jobs") or []) == 23, r42.get("job_count")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_R421_AUTHORIZATION_ONLY_EXACT_11_JOBS", cfg.get("policy_freeze")),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
        Check("target_repair_execution_not_authorized", auth.get("target_repair_execution_authorized") is False),
        Check("p3_execution_not_authorized", auth.get("p3_execution_authorized") is False),
    ]
    if not all(c.passed for c in checks):
        out = {"stage": STAGE, "status": BLOCKED, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks], "next_action": "REPAIR_R422_PARENT_AUTHORIZATION_OR_POLICY_INPUTS"}
        write(root / OUT / "R4_22_PREEXECUTION_AUDIT.json", out)
        return out

    adapter_reg = _adapter_hash_registry(p2val)
    r42_ids = {j.get("job_id") for j in r42.get("jobs") or []}
    jobs = []
    for j in auth.get("authorized_jobs") or []:
        jid = str(j["job_id"]); engine = str(j["engine"])
        cp = _contract_path(root, jid)
        contract = load(cp) if cp.exists() else {}
        adapter = root / ADAPTER_PATHS[engine]
        reg = adapter_reg.get(engine) or {}
        row = {
            "job_id": jid,
            "engine": engine,
            "window_id": j.get("window_id"),
            "contract_path": cp.relative_to(root).as_posix() if cp.exists() else cp.as_posix(),
            "contract_present": cp.exists(),
            "contract_sha256": sha256(cp) if cp.exists() else None,
            "contract_job_match": contract.get("frozen_parent_job", {}).get("job_id") == jid,
            "seed_ledger": _contract_seed_ledger(contract) if contract else [],
            "adapter_path": ADAPTER_PATHS[engine].as_posix(),
            "adapter_present": adapter.exists(),
            "adapter_sha256": sha256(adapter) if adapter.exists() else None,
            "authorized_adapter_sha256": reg.get("sha256"),
            "adapter_hash_matches_r421_authorization": adapter.exists() and bool(reg.get("sha256")) and sha256(adapter) == reg.get("sha256"),
            "comparison_target_used": False,
            "canonical_write": False,
        }
        if engine == "CDMetaPOP":
            rp = _r47_profile_path(root, jid)
            prof = load(rp) if rp.exists() else {}
            row.update({
                "repair_profile_path": rp.relative_to(root).as_posix() if rp.exists() else rp.as_posix(),
                "repair_profile_present": rp.exists(),
                "repair_profile_sha256": sha256(rp) if rp.exists() else None,
                "repair_profile_job_match": prof.get("job_id") == jid,
                "repair_profile_no_target_leakage": prof.get("repair_profile", {}).get("comparison_target_used") is False,
            })
        jobs.append(row)

    all_jobs_ok = all(
        r["job_id"] in r42_ids and r["contract_present"] and r["contract_job_match"] and r["seed_ledger"] and r["adapter_present"] and r["adapter_hash_matches_r421_authorization"]
        and (r["engine"] != "CDMetaPOP" or (r.get("repair_profile_present") and r.get("repair_profile_job_match") and r.get("repair_profile_no_target_leakage")))
        for r in jobs
    )
    checks += [
        Check("exact_11_authorized_jobs_materialized", len(jobs) == 11, len(jobs)),
        Check("all_authorized_jobs_are_r42_subset", all(r["job_id"] in r42_ids for r in jobs), [r["job_id"] for r in jobs if r["job_id"] not in r42_ids]),
        Check("all_job_contracts_present_and_job_bound", all(r["contract_present"] and r["contract_job_match"] for r in jobs)),
        Check("all_seed_ledgers_nonempty", all(bool(r["seed_ledger"]) for r in jobs)),
        Check("all_executed_adapter_hashes_match_r421_authorization", all(r["adapter_hash_matches_r421_authorization"] for r in jobs)),
        Check("all_cdmetapop_jobs_have_valid_r47_profiles", all(r["engine"] != "CDMetaPOP" or (r.get("repair_profile_present") and r.get("repair_profile_job_match") and r.get("repair_profile_no_target_leakage")) for r in jobs)),
        Check("no_result_selected_job_expansion", len(jobs) == 11 and {r["job_id"] for r in jobs} == set(auth.get("authorized_job_ids") or [])),
    ]
    geo = deferred_geonomics_completion_audit(root)
    checks += [
        Check("geonomics_deferred_audit_exact_three_jobs", geo.get("record_count") == 3, geo.get("record_count")),
        Check("geonomics_execution_still_not_authorized", geo.get("geonomics_execution_authorized_in_r422") is False),
        Check("geonomics_scalar_descriptor_synthesis_forbidden", all(r.get("scalar_descriptor_synthesis_forbidden") for r in geo.get("records") or [])),
    ]
    status = "PASS_R422_PREEXECUTION_AUTHORIZATION_MATERIALIZED" if all(c.passed for c in checks) and all_jobs_ok else BLOCKED
    plan = {
        "stage": STAGE,
        "status": "R422_EXACT_AUTHORIZED_EXECUTION_PLAN_FROZEN" if status.startswith("PASS_") else BLOCKED,
        "authorized_job_count": len(jobs),
        "authorized_engine_families": auth.get("authorized_engine_families"),
        "authorized_job_ids": [r["job_id"] for r in jobs],
        "jobs": jobs,
        "execution_scope": "EXACT_R421_AUTHORIZED_11_JOBS_ONLY",
        "exact_seed_reuse_required": True,
        "adapter_revision": "R4.21_AUTHORIZED_SOURCE_HASH_EXACT",
        "target_repair_execution_authorized": False,
        "p3_execution_authorized": False,
        "geonomics_execution_authorized": False,
    }
    out = {"stage": STAGE, "status": status, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks], "authorized_job_count": len(jobs), "authorized_engine_families": auth.get("authorized_engine_families"), "geonomics_family_ready_for_execution": geo.get("geonomics_family_ready_for_execution"), "engine_execution_performed": False, "canonical_state_changed": False, "next_action": "EXECUTE_R422_AUTHORIZED_11_JOBS" if status.startswith("PASS_") else "REPAIR_R422_PREEXECUTION_INPUTS"}
    write(root / OUT / "R4_22_PREEXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_22_DEFERRED_GEONOMICS_IMPLEMENTATION_COMPLETION.json", geo)
    write(root / OUT / "R4_22_PREEXECUTION_AUDIT.json", out)
    return out


def _expected_seed_pairs(contract: dict[str, Any]) -> list[tuple[int, int]]:
    return [(int(r["replicate_index"]), int(r["seed"])) for r in contract.get("engine_input", {}).get("replicates") or []]


def _numeric_finite(v: Any) -> bool:
    return isinstance(v, (int, float)) and math.isfinite(float(v))


def _job_semantics_ok(engine: str, raw: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    reps = raw.get("replicates") or []
    if engine == "CDMetaPOP":
        if raw.get("absolute_population_response_comparability") != "PROXY_ONLY": errors.append("absolute_population_response_not_proxy_only")
        for r in reps:
            if not _numeric_finite(r.get("matched_control_population_effect_ratio")): errors.append("matched_control_effect_missing")
            if not _numeric_finite((r.get("dynamic") or {}).get("population_response_ratio")): errors.append("dynamic_ratio_missing")
            if not _numeric_finite((r.get("neutral") or {}).get("population_response_ratio")): errors.append("neutral_ratio_missing")
    elif engine == "NEMO":
        for r in reps:
            m = r.get("metrics") or {}; sem = m.get("metric_semantics") or {}
            if int(m.get("loci") or 0) <= 0: errors.append("qfreq_loci_missing")
            if sem.get("mean_expected_heterozygosity") != "RAW_EXPECTED_HETEROZYGOSITY_NOT_ADDITIVE_GENETIC_VARIANCE": errors.append("heterozygosity_semantic_guard_missing")
            if sem.get("mean_population_frequency_range") != "RAW_ALLELE_FREQUENCY_DIFFERENTIATION_NOT_GENE_FLOW_RATE": errors.append("frequency_gap_semantic_guard_missing")
    elif engine == "SLiM":
        for r in reps:
            m = r.get("metrics") or {}; sem = m.get("metric_semantics") or {}
            if int(m.get("current_sample_nodes") or 0) <= 0: errors.append("current_samples_missing")
            if sem.get("global_diversity_per_site") != "DIVERSITY_NOT_ANCESTRY_CONTRIBUTION": errors.append("diversity_semantic_guard_missing")
            if sem.get("fst_between_current_population_samples") != "DIFFERENTIATION_NOT_MIGRATION_RATE": errors.append("fst_semantic_guard_missing")
    else:
        errors.append("unauthorized_engine")
    return not errors, errors


def collect(root: Path) -> dict[str, Any]:
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    plan = load(root / OUT / "R4_22_PREEXECUTION_PLAN.json") if (root / OUT / "R4_22_PREEXECUTION_PLAN.json").exists() else {}
    geo = load(root / OUT / "R4_22_DEFERRED_GEONOMICS_IMPLEMENTATION_COMPLETION.json") if (root / OUT / "R4_22_DEFERRED_GEONOMICS_IMPLEMENTATION_COMPLETION.json").exists() else {}
    checks: list[Check] = [
        Check("parent_r421_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("preexecution_plan_frozen", plan.get("status") == "R422_EXACT_AUTHORIZED_EXECUTION_PLAN_FROZEN", plan.get("status")),
        Check("exact_11_planned_jobs", plan.get("authorized_job_count") == 11 and len(plan.get("jobs") or []) == 11, plan.get("authorized_job_count")),
        Check("geonomics_not_in_execution_plan", "Geonomics" not in set(plan.get("authorized_engine_families") or []), plan.get("authorized_engine_families")),
    ]
    audits = []
    for rec in plan.get("jobs") or []:
        jid = rec["job_id"]; engine = rec["engine"]
        rawp = root / OUT / "jobs" / jid / "RAW_EVIDENCE.json"
        raw = load(rawp) if rawp.exists() else {}
        contract = load(root / rec["contract_path"]) if (root / rec["contract_path"]).exists() else {}
        expected = sorted(_expected_seed_pairs(contract))
        observed = sorted((int(r.get("replicate_index", -999)), int(r.get("seed", -999))) for r in raw.get("replicates") or [])
        sem_ok, sem_errors = _job_semantics_ok(engine, raw) if raw else (False, ["raw_evidence_missing"])
        ok = (
            rawp.exists()
            and raw.get("adapter_status") == "PASS"
            and raw.get("job_id") == jid
            and raw.get("engine") == engine
            and raw.get("canonical_write") is False
            and raw.get("comparison_target_used") is False
            and expected == observed
            and len(expected) > 0
            and all(r.get("status") == "PASS" for r in raw.get("replicates") or [])
            and sem_ok
        )
        audit = {
            "job_id": jid,
            "engine": engine,
            "window_id": rec.get("window_id"),
            "raw_evidence_path": rawp.relative_to(root).as_posix(),
            "raw_evidence_present": rawp.exists(),
            "raw_evidence_sha256": sha256(rawp) if rawp.exists() else None,
            "adapter_status": raw.get("adapter_status"),
            "job_id_match": raw.get("job_id") == jid,
            "engine_match": raw.get("engine") == engine,
            "expected_seed_ledger": expected,
            "observed_seed_ledger": observed,
            "exact_seed_ledger_match": expected == observed and len(expected) > 0,
            "all_replicates_pass": bool(raw.get("replicates")) and all(r.get("status") == "PASS" for r in raw.get("replicates") or []),
            "comparison_target_used": raw.get("comparison_target_used"),
            "canonical_write": raw.get("canonical_write"),
            "semantic_validation_pass": sem_ok,
            "semantic_validation_errors": sem_errors,
            "job_audit_pass": ok,
        }
        audits.append(audit)
        write(root / OUT / "jobs" / jid / "JOB_AUDIT.json", audit)

    engine_counts: dict[str, int] = {}
    for a in audits: engine_counts[a["engine"]] = engine_counts.get(a["engine"], 0) + 1
    passed = sum(1 for a in audits if a["job_audit_pass"])
    checks += [
        Check("exact_11_job_audits", len(audits) == 11, len(audits)),
        Check("all_11_authorized_jobs_pass", passed == 11, {"pass": passed, "total": len(audits)}),
        Check("engine_execution_scope_exact_5_3_3", engine_counts == {"CDMetaPOP": 5, "NEMO": 3, "SLiM": 3}, engine_counts),
        Check("all_seed_ledgers_exactly_reused", all(a.get("exact_seed_ledger_match") for a in audits)),
        Check("all_results_target_independent", all(a.get("comparison_target_used") is False for a in audits)),
        Check("all_results_noncanonical", all(a.get("canonical_write") is False for a in audits)),
        Check("all_engine_specific_semantic_guards_pass", all(a.get("semantic_validation_pass") for a in audits)),
        Check("geonomics_deferred_completion_audit_preserved", geo.get("record_count") == 3 and geo.get("geonomics_execution_authorized_in_r422") is False, geo.get("status")),
        Check("no_readjudication_in_r422", True),
    ]
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED
    next_action = "BUILD_R423_P2_REEXECUTION_EVIDENCE_NORMALIZATION_AND_GEONOMICS_CANONICAL_SPATIAL_BINDING_COMPLETION" if status == COMPLETE else "REPAIR_R422_AUTHORIZED_ENGINE_EXECUTION_FAILURES"
    summary = {
        "stage": STAGE,
        "status": status,
        "authorized_job_count": 11,
        "successful_authorized_job_count": passed,
        "engine_job_counts": engine_counts,
        "authorized_engine_families": ["CDMetaPOP", "NEMO", "SLiM"],
        "deferred_engine_families": ["Geonomics"],
        "geonomics_family_ready_for_execution": geo.get("geonomics_family_ready_for_execution"),
        "readjudication_performed": False,
        "target_repair_execution_performed": False,
        "p3_execution_performed": False,
        "canonical_state_changed": False,
        "canonical_replay_authorized": False,
        "canonical_parameter_change_authorized": False,
        "deep_biological_coupling": False,
        "next_action": next_action,
    }
    out = {**summary, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks]}
    evidence_audit = {"stage": STAGE, "status": "R422_AUTHORIZED_REEXECUTION_EVIDENCE_AUDIT_COMPLETE" if passed == 11 else "R422_AUTHORIZED_REEXECUTION_EVIDENCE_AUDIT_BLOCKED", "job_count": len(audits), "passed_job_count": passed, "engine_job_counts": engine_counts, "jobs": audits}
    postplan = {
        "stage": STAGE,
        "status": "R422_R423_POSTEXECUTION_PLAN_FROZEN" if status == COMPLETE else BLOCKED,
        "authorized_reexecution_evidence_ready_for_normalization": status == COMPLETE,
        "normalization_scope_job_ids": [a["job_id"] for a in audits if a["job_audit_pass"]],
        "geonomics_deferred_binding_audit_status": geo.get("status"),
        "geonomics_execution_authorized": False,
        "target_repair_execution_authorized": False,
        "p3_execution_authorized": False,
        "readjudication_authorized_in_r422": False,
        "next_action": next_action,
    }
    write(root / OUT / "R4_22_AUTHORIZED_REEXECUTION_EVIDENCE_AUDIT.json", evidence_audit)
    write(root / OUT / "R4_22_EXECUTION_SUMMARY.json", summary)
    write(root / OUT / "R4_22_R423_POSTEXECUTION_PLAN.json", postplan)
    write(root / OUT / "R4_22_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_22_INTEGRATED_AUDIT.json") if (root / OUT / "R4_22_INTEGRATED_AUDIT.json").exists() else {}
    ev = load(root / OUT / "R4_22_AUTHORIZED_REEXECUTION_EVIDENCE_AUDIT.json") if (root / OUT / "R4_22_AUTHORIZED_REEXECUTION_EVIDENCE_AUDIT.json").exists() else {}
    geo = load(root / OUT / "R4_22_DEFERRED_GEONOMICS_IMPLEMENTATION_COMPLETION.json") if (root / OUT / "R4_22_DEFERRED_GEONOMICS_IMPLEMENTATION_COMPLETION.json").exists() else {}
    pp = load(root / OUT / "R4_22_R423_POSTEXECUTION_PLAN.json") if (root / OUT / "R4_22_R423_POSTEXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r421_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r422_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r422_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("exact_11_authorized_jobs_successful", ev.get("job_count") == 11 and ev.get("passed_job_count") == 11, {"jobs": ev.get("job_count"), "pass": ev.get("passed_job_count")}),
        Check("exact_engine_execution_scope", ev.get("engine_job_counts") == {"CDMetaPOP": 5, "NEMO": 3, "SLiM": 3}, ev.get("engine_job_counts")),
        Check("geonomics_remains_deferred", geo.get("record_count") == 3 and geo.get("geonomics_execution_authorized_in_r422") is False, geo.get("blocking_reason")),
        Check("r423_plan_frozen", pp.get("status") == "R422_R423_POSTEXECUTION_PLAN_FROZEN", pp.get("status")),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("no_target_repair_execution", a.get("target_repair_execution_performed") is False),
        Check("no_p3_execution", a.get("p3_execution_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", a.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", a.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", a.get("deep_biological_coupling") is False),
        Check("next_action_present", a.get("next_action") == pp.get("next_action") and bool(a.get("next_action")), a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "authorized_job_count": 11,
            "successful_authorized_job_count": a.get("successful_authorized_job_count"),
            "engine_job_counts": a.get("engine_job_counts"),
            "authorized_engine_families": a.get("authorized_engine_families"),
            "deferred_engine_families": a.get("deferred_engine_families"),
            "geonomics_family_ready_for_execution": a.get("geonomics_family_ready_for_execution"),
            "readjudication_performed": False,
            "target_repair_execution_performed": False,
            "p3_execution_performed": False,
            "canonical_state_changed": False,
            "canonical_replay_authorized": False,
            "canonical_parameter_change_authorized": False,
            "deep_biological_coupling": False,
            "next_action": a.get("next_action"),
        },
        "next_action": a.get("next_action"),
    }
    write(root / SEAL, out)
    return out
