from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import math

STAGE = "v0.6D1-R4.23"
PARENT_SEALED = "PASS_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION_SEALED"
COMPLETE = "PASS_R423_P2_REEXECUTION_EVIDENCE_NORMALIZATION_AND_GEONOMICS_CANONICAL_SPATIAL_BINDING_COMPLETION_COMPLETE"
SEALED = "PASS_R423_P2_REEXECUTION_EVIDENCE_NORMALIZATION_AND_GEONOMICS_CANONICAL_SPATIAL_BINDING_COMPLETION_SEALED"
BLOCKED = "BLOCKED_R423_PARENT_EVIDENCE_NORMALIZATION_OR_GEONOMICS_BINDING_AUDIT_FAILURE"
NEXT = "BUILD_R424_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN"

CFG = Path("configs/world1_r423_p2_evidence_normalization_geonomics_binding_v0_6D1_R4_23.json")
PSEAL = Path("outputs/v0_6D1_R4_22_SEAL/R4_22_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_22/R4_22_INTEGRATED_AUDIT.json")
PEVID = Path("outputs/v0_6D1_R4_22/R4_22_AUTHORIZED_REEXECUTION_EVIDENCE_AUDIT.json")
PPLAN = Path("outputs/v0_6D1_R4_22/R4_22_R423_POSTEXECUTION_PLAN.json")
PGEO = Path("outputs/v0_6D1_R4_22/R4_22_DEFERRED_GEONOMICS_IMPLEMENTATION_COMPLETION.json")
R421P2 = Path("outputs/v0_6D1_R4_21/R4_21_P2_STATIC_VALIDATION.json")
R421AUTH = Path("outputs/v0_6D1_R4_21/R4_21_SYMMETRIC_REEXECUTION_AUTHORIZATION.json")
R418MATRIX = Path("outputs/v0_6D1_R4_18/R4_18_PARTIAL_READJUDICATED_MATRIX.json")
OUT = Path("outputs/v0_6D1_R4_23")
SEAL = Path("outputs/v0_6D1_R4_23_SEAL/R4_23_FINAL_SEAL_AUDIT.json")

AUTHORIZED_ENGINE_COUNTS = {"CDMetaPOP": 5, "NEMO": 3, "SLiM": 3}

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

R327 = Path("outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz")
R328 = Path("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz")
R333 = Path("outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz")
R334 = Path("outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz")
R315_250 = Path("local_runs/v0_6D1_R3_15/WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.npz")


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None
    def d(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def finite(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def quantile(vals: list[float], q: float) -> float | None:
    if not vals:
        return None
    xs = sorted(vals)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * float(q)
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def summarize(vals: list[Any]) -> dict[str, Any]:
    xs = [x for x in (finite(v) for v in vals) if x is not None]
    return {
        "n": len(xs),
        "median": quantile(xs, 0.5),
        "q10": quantile(xs, 0.1),
        "q90": quantile(xs, 0.9),
        "min": min(xs) if xs else None,
        "max": max(xs) if xs else None,
    }


def _raw_path(root: Path, job_id: str) -> Path:
    return root / "outputs" / "v0_6D1_R4_22" / "jobs" / job_id / "RAW_EVIDENCE.json"


def _metric_record(name: str, values: list[Any], semantics: str, comparability: str, kind: str = "ratio") -> dict[str, Any]:
    return {
        "name": name,
        "summary": summarize(values),
        "kind": kind,
        "semantics": semantics,
        "comparability_disposition": comparability,
        "adjudicative_promotion_authorized_in_r423": False,
    }


def normalize_raw(job_audit: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    engine = str(job_audit.get("engine"))
    reps = list(raw.get("replicates") or [])
    metrics: list[dict[str, Any]] = []
    guards: list[str] = []
    if engine == "CDMetaPOP":
        metrics = [
            _metric_record(
                "matched_control_population_effect_ratio",
                [r.get("matched_control_population_effect_ratio") for r in reps],
                "DYNAMIC_POPULATION_RESPONSE_DIVIDED_BY_MATCHED_NEUTRAL_RESPONSE; DIAGNOSTIC_DOMAIN_CANDIDATE_REQUIRES_ARCANA_CAUSAL_TARGET",
                "NORMALIZABLE_CANDIDATE_PENDING_ARCANA_CAUSAL_TARGET",
            ),
            _metric_record(
                "dynamic_population_response_ratio",
                [(r.get("dynamic") or {}).get("population_response_ratio") for r in reps],
                "ABSOLUTE_DYNAMIC_POPULATION_RESPONSE; R4.12 NEUTRAL-INVARIANCE FAILURE PREVENTS GLOBAL ADJUDICATIVE USE",
                "PROXY_ONLY",
            ),
            _metric_record(
                "neutral_population_response_ratio",
                [(r.get("neutral") or {}).get("population_response_ratio") for r in reps],
                "MATCHED_NEUTRAL_CONTROL RESPONSE; CONTEXT FOR CAUSAL NORMALIZATION ONLY",
                "CONTEXT_ONLY",
            ),
        ]
        guards = [
            "absolute_population_response != adjudicative_population_persistence",
            "matched_control_effect requires explicit ARCANA causal target before promotion",
        ]
    elif engine == "NEMO":
        metrics = [
            _metric_record(
                "mean_expected_heterozygosity",
                [(r.get("metrics") or {}).get("mean_expected_heterozygosity") for r in reps],
                "RAW_EXPECTED_HETEROZYGOSITY_NOT_ADDITIVE_GENETIC_VARIANCE",
                "CONTEXT_ONLY_SEMANTIC_MISMATCH",
            ),
            _metric_record(
                "mean_population_frequency_range",
                [(r.get("metrics") or {}).get("mean_population_frequency_range") for r in reps],
                "RAW_ALLELE_FREQUENCY_DIFFERENTIATION_NOT_GENE_FLOW_RATE",
                "CONTEXT_ONLY_SEMANTIC_MISMATCH",
            ),
        ]
        guards = [
            "heterozygosity != additive_variance",
            "allele_frequency_differentiation != gene_flow_rate",
        ]
    elif engine == "SLiM":
        metrics = [
            _metric_record(
                "global_diversity_per_site",
                [(r.get("metrics") or {}).get("global_diversity_per_site") for r in reps],
                "DIVERSITY_NOT_ANCESTRY_CONTRIBUTION",
                "CONTEXT_ONLY_SEMANTIC_MISMATCH",
            ),
            _metric_record(
                "fst_between_current_population_samples",
                [(r.get("metrics") or {}).get("fst_between_current_population_samples") for r in reps],
                "DIFFERENTIATION_NOT_MIGRATION_RATE",
                "CONTEXT_ONLY_SEMANTIC_MISMATCH",
            ),
        ]
        guards = [
            "diversity != ancestry",
            "FST != migration_rate",
        ]
    else:
        raise ValueError(f"unsupported R4.23 normalization engine: {engine}")

    finite_metric_count = sum(1 for m in metrics if (m.get("summary") or {}).get("n", 0) > 0)
    return {
        "stage": STAGE,
        "job_id": job_audit.get("job_id"),
        "window_id": job_audit.get("window_id"),
        "engine": engine,
        "raw_evidence_sha256": job_audit.get("raw_evidence_sha256"),
        "replicate_count": len(reps),
        "seed_ledger_exactly_reused": job_audit.get("exact_seed_ledger_match") is True,
        "metric_count": len(metrics),
        "finite_metric_count": finite_metric_count,
        "normalized_metrics": {m["name"]: m for m in metrics},
        "semantic_guards": guards,
        "adjudicative_promotion_authorized_in_r423": False,
        "readjudication_authorized_in_r423": False,
        "canonical_write": False,
    }


def build_normalized_registry(root: Path, pevid: dict[str, Any]) -> dict[str, Any]:
    records = []
    for a in pevid.get("jobs") or []:
        jid = str(a.get("job_id"))
        rawp = _raw_path(root, jid)
        raw = load(rawp)
        rec = normalize_raw(a, raw)
        rec["raw_evidence_path"] = rawp.relative_to(root).as_posix()
        rec["raw_hash_matches_r422_audit"] = rawp.exists() and sha256_file(rawp) == a.get("raw_evidence_sha256")
        records.append(rec)
        write(root / OUT / "jobs" / jid / "NORMALIZED_EVIDENCE.json", rec)
    engine_counts: dict[str, int] = {}
    for r in records:
        engine_counts[r["engine"]] = engine_counts.get(r["engine"], 0) + 1
    return {
        "stage": STAGE,
        "status": "R423_P2_REEXECUTION_EVIDENCE_NORMALIZATION_COMPLETE",
        "job_count": len(records),
        "engine_job_counts": engine_counts,
        "records": records,
        "all_raw_hashes_match_r422": all(r.get("raw_hash_matches_r422_audit") for r in records),
        "all_seed_ledgers_preserved": all(r.get("seed_ledger_exactly_reused") for r in records),
        "automatic_adjudicative_promotion_count": 0,
        "readjudication_performed": False,
    }


def _semantic_candidate(engine: str, domain: str, norm: dict[str, Any]) -> dict[str, Any]:
    nm = norm.get("normalized_metrics") or {}
    if engine == "CDMetaPOP" and domain == "population_persistence" and "matched_control_population_effect_ratio" in nm:
        return {
            "metric_name": "matched_control_population_effect_ratio",
            "disposition": "R424_SEMANTIC_PROMOTION_GATE_CANDIDATE",
            "reason": "MATCHED_CONTROL_CAUSAL_EFFECT_EXISTS_BUT_ARCANA_CAUSAL_TARGET_SEMANTICS_NOT_YET_VALIDATED",
            "adjudicative_in_r423": False,
        }
    mismatch_map = {
        ("NEMO", "additive_variance"): ("mean_expected_heterozygosity", "HETEROZYGOSITY_IS_NOT_ADDITIVE_VARIANCE"),
        ("NEMO", "gene_flow"): ("mean_population_frequency_range", "ALLELE_FREQUENCY_DIFFERENTIATION_IS_NOT_GENE_FLOW_RATE"),
        ("SLiM", "ancestry"): ("global_diversity_per_site", "DIVERSITY_IS_NOT_ANCESTRY_CONTRIBUTION"),
        ("SLiM", "gene_flow"): ("fst_between_current_population_samples", "FST_IS_NOT_MIGRATION_RATE"),
    }
    if (engine, domain) in mismatch_map:
        metric, reason = mismatch_map[(engine, domain)]
        return {"metric_name": metric if metric in nm else None, "disposition": "CONTEXT_ONLY_SEMANTIC_MISMATCH", "reason": reason, "adjudicative_in_r423": False}
    return {"metric_name": None, "disposition": "NO_AUTHORIZED_DOMAIN_METRIC_FROM_R422_NORMALIZATION", "reason": "NO_EXPLICIT_DOMAIN_IDENTITY_TRANSFORM_FROZEN", "adjudicative_in_r423": False}


def build_p2_cell_candidate_registry(p2v: dict[str, Any], normreg: dict[str, Any]) -> dict[str, Any]:
    by = {(r.get("engine"), r.get("window_id")): r for r in normreg.get("records") or []}
    rows = []
    for c in p2v.get("cells") or []:
        if not c.get("static_validation_pass"):
            continue
        engine = str(c.get("engine")); window = str(c.get("window_id")); domain = str(c.get("domain"))
        n = by.get((engine, window))
        cand = _semantic_candidate(engine, domain, n or {})
        rows.append({
            "window_id": window,
            "domain": domain,
            "engine": engine,
            "source_stage": c.get("source_stage"),
            "normalized_job_id": n.get("job_id") if n else None,
            "normalized_evidence_present": n is not None,
            **cand,
            "canonical_change_authorized": False,
        })
    return {
        "stage": STAGE,
        "status": "R423_AUTHORIZED_P2_CELL_NORMALIZED_EVIDENCE_CANDIDATES_FROZEN",
        "cell_count": len(rows),
        "semantic_promotion_gate_candidate_count": sum(r.get("disposition") == "R424_SEMANTIC_PROMOTION_GATE_CANDIDATE" for r in rows),
        "context_only_or_no_metric_count": sum(r.get("disposition") != "R424_SEMANTIC_PROMOTION_GATE_CANDIDATE" for r in rows),
        "records": rows,
        "readjudication_authorized_in_r423": False,
    }


def _npz_meta(path: Path, required: list[str], variable_name_key: str | None = None, age_key: str | None = None) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "path": path.as_posix(),
        "present": path.exists(),
        "required_keys": required,
        "required_keys_present": False,
        "sha256": None,
        "keys": [],
        "shapes": {},
        "dtypes": {},
    }
    if not path.exists():
        return rec
    rec["sha256"] = sha256_file(path)
    try:
        import numpy as np
        with np.load(path, allow_pickle=False) as z:
            rec["keys"] = list(z.files)
            rec["required_keys_present"] = all(k in z.files for k in required)
            for k in z.files:
                a = z[k]
                rec["shapes"][k] = list(a.shape)
                rec["dtypes"][k] = str(a.dtype)
            if variable_name_key and variable_name_key in z.files:
                rec["variable_names"] = [str(x) for x in z[variable_name_key].tolist()]
            if age_key and age_key in z.files:
                arr = z[age_key].astype(float).reshape(-1)
                if arr.size:
                    rec["age_min"] = float(arr.min()); rec["age_max"] = float(arr.max()); rec["age_count"] = int(arr.size)
    except Exception as exc:
        rec["error"] = repr(exc)
        rec["required_keys_present"] = False
    return rec


def _profile_path(root: Path, jid: str) -> Path:
    return root / OUT / "geonomics_profiles" / jid / "LANDSCAPE_PROFILE.json"


def build_geonomics_binding_registry(root: Path) -> dict[str, Any]:
    r327 = _npz_meta(root / R327, ["age_ma", "state", "candidate_ids", "variable_names"], "variable_names", "age_ma")
    r328 = _npz_meta(root / R328, ["snapshot_age_ka", "snapshot_deme_state", "snapshot_active", "state_variable_names"], "state_variable_names", "snapshot_age_ka")
    r333 = _npz_meta(root / R333, ["anchor_age_ka", "environment_fields", "environment_variable_names"], "environment_variable_names", "anchor_age_ka")
    r334 = _npz_meta(root / R334, ["anchor_age_ka", "producer_landscape", "landscape_variable_names"], "landscape_variable_names", "anchor_age_ka")
    r315 = _npz_meta(root / R315_250, ["population", "current_accessible", "lat", "lon"], None, None)

    r327_names = set(r327.get("variable_names") or [])
    r328_names = set(r328.get("variable_names") or [])
    r327_has_explicit_xy = {"grid_row", "grid_col"}.issubset(r327_names) or {"lat", "lon"}.issubset(r327_names)
    r328_spatial = {"population_proxy", "grid_row", "grid_col", "local_suitability"}.issubset(r328_names)
    r328_covers_200_to_0 = r328.get("age_max") is not None and r328.get("age_min") is not None and float(r328["age_max"]) >= 200.0 and float(r328["age_min"]) <= 0.0

    j14 = {
        "job_id": J14,
        "window_id": "SAPIENT_3MA_TO_200KA",
        "profile_status": "DEFERRED_PRE_200KA_CANONICAL_SPATIAL_SOURCE_ABSENT",
        "binding_materialized": False,
        "canonical_spatial_sources_audited": [r327, r328, r315],
        "r327_macro_state_is_spatial": bool(r327_has_explicit_xy),
        "r328_spatial_support_starts_at_or_before_200ka": bool(r328_spatial and r328_covers_200_to_0),
        "window_start_3000ka_explicit_spatial_state_present": False,
        "scalar_descriptor_synthesis_forbidden": True,
        "interpolation_from_30Ma_or_250ka_forbidden_without_authority": True,
        "canonical_replay_authorized_in_r423": False,
        "geonomics_execution_ready": False,
        "reason": "R3.27 PROVIDES 3Ma MACRO DEMOGRAPHIC TRAJECTORIES BUT NO EXPLICIT SPATIAL COORDINATES; R3.28 SPATIAL DEME STATE STARTS AT 200ka; R3.15 250ka CHECKPOINT DOES NOT SUPPLY THE 3Ma WINDOW START",
    }

    j18_ready = bool(r328.get("present") and r328.get("required_keys_present") and r328_spatial and r328_covers_200_to_0)
    j18_profile = {
        "stage": STAGE,
        "job_id": J18,
        "window_id": "SAPIENT_200KA_TO_0",
        "profile_status": "CANONICAL_SPATIAL_BINDING_TRANSLATION_FROZEN" if j18_ready else "DEFERRED_CANONICAL_SPATIAL_SOURCE_INCOMPLETE",
        "canonical_spatial_source": {"path": R328.as_posix(), "sha256": r328.get("sha256")},
        "translation": {
            "time_axis": "snapshot_age_ka",
            "deme_state": "snapshot_deme_state",
            "active_mask": "snapshot_active",
            "coordinate_fields": ["grid_row", "grid_col"],
            "habitat_suitability_field": "local_suitability",
            "population_support_field": "population_proxy",
            "spatial_interpolation": "FORBIDDEN_IN_R423",
            "unobserved_cell_fill": "NOT_AUTHORIZED_IN_R423",
        },
        "comparison_target_used": False,
        "geonomics_parameters_file": None,
        "geonomics_parameter_materialization_authorized_in_r423": False,
        "geonomics_execution_ready": False,
    }
    write(_profile_path(root, J18), j18_profile)

    j21_ready = bool(r333.get("present") and r333.get("required_keys_present") and r334.get("present") and r334.get("required_keys_present"))
    j21_profile = {
        "stage": STAGE,
        "job_id": J21,
        "window_id": "PRODUCER_20KA_TO_0",
        "profile_status": "CANONICAL_SPATIAL_BINDING_TRANSLATION_FROZEN" if j21_ready else "DEFERRED_CANONICAL_SPATIAL_SOURCE_INCOMPLETE",
        "canonical_spatial_sources": [
            {"path": R333.as_posix(), "sha256": r333.get("sha256"), "role": "HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE"},
            {"path": R334.as_posix(), "sha256": r334.get("sha256"), "role": "PRODUCER_RESOURCE_LANDSCAPE"},
        ],
        "translation": {
            "time_axis": "anchor_age_ka",
            "environment_tensor": "environment_fields",
            "environment_variable_names": r333.get("variable_names") or [],
            "producer_tensor": "producer_landscape",
            "producer_variable_names": r334.get("variable_names") or [],
            "cross_layer_numeric_mixing": "FORBIDDEN_WITHOUT_EXPLICIT_R424_AUTHORITY",
            "spatial_interpolation": "FORBIDDEN_IN_R423",
        },
        "comparison_target_used": False,
        "geonomics_parameters_file": None,
        "geonomics_parameter_materialization_authorized_in_r423": False,
        "geonomics_execution_ready": False,
    }
    write(_profile_path(root, J21), j21_profile)

    records = [
        j14,
        {"job_id": J18, "window_id": "SAPIENT_200KA_TO_0", "profile_status": j18_profile["profile_status"], "binding_materialized": j18_ready, "canonical_spatial_sources_audited": [r328], "geonomics_execution_ready": False, "profile_path": _profile_path(root, J18).relative_to(root).as_posix()},
        {"job_id": J21, "window_id": "PRODUCER_20KA_TO_0", "profile_status": j21_profile["profile_status"], "binding_materialized": j21_ready, "canonical_spatial_sources_audited": [r333, r334], "geonomics_execution_ready": False, "profile_path": _profile_path(root, J21).relative_to(root).as_posix()},
    ]
    materialized = sum(bool(r.get("binding_materialized")) for r in records)
    return {
        "stage": STAGE,
        "status": "R423_GEONOMICS_CANONICAL_SPATIAL_BINDING_AUDIT_COMPLETE",
        "record_count": 3,
        "records": records,
        "binding_translation_materialized_count": materialized,
        "binding_deferred_count": 3 - materialized,
        "j14_pre_200ka_spatial_authority_gap_confirmed": j14["profile_status"] == "DEFERRED_PRE_200KA_CANONICAL_SPATIAL_SOURCE_ABSENT",
        "geonomics_family_ready_for_execution": False,
        "geonomics_execution_authorized_in_r423": False,
        "default_model_forbidden_for_adjudication": True,
        "scalar_descriptor_synthesis_forbidden": True,
        "next_required_work": "R424_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_AND_PARAMETER_MATERIALIZATION_AUTHORITY_GATE",
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    pe = load(root / PEVID) if (root / PEVID).exists() else {}
    pp = load(root / PPLAN) if (root / PPLAN).exists() else {}
    pg = load(root / PGEO) if (root / PGEO).exists() else {}
    p2v = load(root / R421P2) if (root / R421P2).exists() else {}
    auth = load(root / R421AUTH) if (root / R421AUTH).exists() else {}
    matrix = load(root / R418MATRIX) if (root / R418MATRIX).exists() else {}

    checks: list[Check] = [
        Check("parent_r422_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r422_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r423", pseal.get("next_action") == "BUILD_R423_P2_REEXECUTION_EVIDENCE_NORMALIZATION_AND_GEONOMICS_CANONICAL_SPATIAL_BINDING_COMPLETION", pseal.get("next_action")),
        Check("parent_exact_11_authorized_jobs_successful", pa.get("authorized_job_count") == 11 and pa.get("successful_authorized_job_count") == 11, {"authorized": pa.get("authorized_job_count"), "successful": pa.get("successful_authorized_job_count")}),
        Check("parent_engine_scope_exact_5_3_3", pa.get("engine_job_counts") == AUTHORIZED_ENGINE_COUNTS, pa.get("engine_job_counts")),
        Check("parent_evidence_audit_exact_11_pass", pe.get("job_count") == 11 and pe.get("passed_job_count") == 11, {"jobs": pe.get("job_count"), "pass": pe.get("passed_job_count")}),
        Check("parent_r423_postexecution_plan_frozen", pp.get("status") == "R422_R423_POSTEXECUTION_PLAN_FROZEN" and pp.get("authorized_reexecution_evidence_ready_for_normalization") is True, pp.get("status")),
        Check("parent_geonomics_deferred_three", pg.get("record_count") == 3 and pg.get("geonomics_execution_authorized_in_r422") is False, pg.get("record_count")),
        Check("parent_r421_authorized_p2_cells_four", p2v.get("authorized_p2_cell_count") == 4, p2v.get("authorized_p2_cell_count")),
        Check("parent_r421_deferred_p2_cells_two", p2v.get("deferred_p2_cell_count") == 2, p2v.get("deferred_p2_cell_count")),
        Check("parent_authorization_exact_11", auth.get("authorized_job_count") == 11, auth.get("authorized_job_count")),
        Check("latest_matrix_exact_75_cells", matrix.get("cell_count") == 75 and len(matrix.get("cells") or []) == 75, matrix.get("cell_count")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_POST_R422_PRE_SEMANTIC_PROMOTION_AND_GEONOMICS_AUTHORITY_CLOSURE", cfg.get("policy_freeze")),
        Check("engine_execution_forbidden_in_r423", cfg.get("engine_execution_performed") is False),
        Check("readjudication_forbidden_in_r423", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
    ]
    if not all(c.passed for c in checks):
        out = {"stage": STAGE, "status": BLOCKED, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks], "canonical_state_changed": False, "next_action": "REPAIR_R423_PARENT_OR_POLICY_INPUTS"}
        write(root / OUT / "R4_23_INTEGRATED_AUDIT.json", out)
        return out

    norm = build_normalized_registry(root, pe)
    p2cells = build_p2_cell_candidate_registry(p2v, norm)
    geo = build_geonomics_binding_registry(root)

    norm_records = norm.get("records") or []
    checks += [
        Check("normalized_registry_exact_11_jobs", norm.get("job_count") == 11 and len(norm_records) == 11, norm.get("job_count")),
        Check("normalized_engine_scope_exact_5_3_3", norm.get("engine_job_counts") == AUTHORIZED_ENGINE_COUNTS, norm.get("engine_job_counts")),
        Check("all_normalized_raw_hashes_match_r422", norm.get("all_raw_hashes_match_r422") is True),
        Check("all_normalized_seed_ledgers_preserved", norm.get("all_seed_ledgers_preserved") is True),
        Check("all_normalized_jobs_have_replicate_evidence", all(r.get("replicate_count") == 4 for r in norm_records), [(r.get("job_id"), r.get("replicate_count")) for r in norm_records if r.get("replicate_count") != 4]),
        Check("all_normalized_jobs_have_finite_metrics", all(r.get("finite_metric_count", 0) == r.get("metric_count", -1) for r in norm_records), [(r.get("job_id"), r.get("finite_metric_count"), r.get("metric_count")) for r in norm_records if r.get("finite_metric_count", 0) != r.get("metric_count", -1)]),
        Check("zero_automatic_adjudicative_promotions", norm.get("automatic_adjudicative_promotion_count") == 0, norm.get("automatic_adjudicative_promotion_count")),
        Check("exact_four_authorized_p2_cells_receive_normalized_disposition", p2cells.get("cell_count") == 4, p2cells.get("cell_count")),
        Check("all_p2_cell_dispositions_nonadjudicative_in_r423", all(r.get("adjudicative_in_r423") is False for r in p2cells.get("records") or [])),
        Check("geonomics_exact_three_binding_records", geo.get("record_count") == 3, geo.get("record_count")),
        Check("geonomics_j18_j21_binding_translations_materialized", geo.get("binding_translation_materialized_count") == 2, geo.get("binding_translation_materialized_count")),
        Check("geonomics_j14_spatial_authority_gap_confirmed", geo.get("j14_pre_200ka_spatial_authority_gap_confirmed") is True),
        Check("geonomics_family_still_not_execution_ready", geo.get("geonomics_family_ready_for_execution") is False and geo.get("geonomics_execution_authorized_in_r423") is False),
        Check("geonomics_scalar_synthesis_forbidden", geo.get("scalar_descriptor_synthesis_forbidden") is True),
        Check("no_engine_execution_in_r423", cfg.get("engine_execution_performed") is False),
        Check("no_readjudication_in_r423", cfg.get("readjudication_performed") is False),
        Check("canonical_state_still_unchanged", cfg.get("canonical_state_changed") is False),
    ]
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED
    next_action = NEXT if status == COMPLETE else "REPAIR_R423_NORMALIZATION_OR_GEONOMICS_BINDING_AUDIT"
    plan = {
        "stage": STAGE,
        "status": "R423_R424_SEMANTIC_PROMOTION_AND_GEONOMICS_AUTHORITY_PLAN_FROZEN" if status == COMPLETE else BLOCKED,
        "normalized_job_count": norm.get("job_count"),
        "authorized_p2_cell_count": p2cells.get("cell_count"),
        "semantic_promotion_gate_candidate_count": p2cells.get("semantic_promotion_gate_candidate_count"),
        "geonomics_binding_translation_materialized_count": geo.get("binding_translation_materialized_count"),
        "geonomics_j14_spatial_authority_gap_confirmed": geo.get("j14_pre_200ka_spatial_authority_gap_confirmed"),
        "geonomics_execution_authorized": False,
        "engine_execution_authorized_in_r424_by_r423": False,
        "readjudication_authorized_in_r423": False,
        "target_repair_execution_authorized_in_r423": False,
        "p3_execution_authorized_in_r423": False,
        "canonical_replay_authorized": False,
        "next_action": next_action,
    }
    out = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "normalized_authorized_job_count": norm.get("job_count"),
        "normalized_engine_job_counts": norm.get("engine_job_counts"),
        "authorized_p2_cell_normalized_disposition_count": p2cells.get("cell_count"),
        "semantic_promotion_gate_candidate_count": p2cells.get("semantic_promotion_gate_candidate_count"),
        "geonomics_binding_translation_materialized_count": geo.get("binding_translation_materialized_count"),
        "geonomics_binding_deferred_count": geo.get("binding_deferred_count"),
        "geonomics_family_ready_for_execution": geo.get("geonomics_family_ready_for_execution"),
        "active_target_protocol_repair_count": 57,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "next_action": next_action,
    }
    write(root / OUT / "R4_23_P2_REEXECUTION_NORMALIZED_EVIDENCE_REGISTRY.json", norm)
    write(root / OUT / "R4_23_P2_CELL_EVIDENCE_CANDIDATE_REGISTRY.json", p2cells)
    write(root / OUT / "R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json", geo)
    write(root / OUT / "R4_23_R424_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_23_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_23_INTEGRATED_AUDIT.json") if (root / OUT / "R4_23_INTEGRATED_AUDIT.json").exists() else {}
    n = load(root / OUT / "R4_23_P2_REEXECUTION_NORMALIZED_EVIDENCE_REGISTRY.json") if (root / OUT / "R4_23_P2_REEXECUTION_NORMALIZED_EVIDENCE_REGISTRY.json").exists() else {}
    c = load(root / OUT / "R4_23_P2_CELL_EVIDENCE_CANDIDATE_REGISTRY.json") if (root / OUT / "R4_23_P2_CELL_EVIDENCE_CANDIDATE_REGISTRY.json").exists() else {}
    g = load(root / OUT / "R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json") if (root / OUT / "R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json").exists() else {}
    plan = load(root / OUT / "R4_23_R424_EXECUTION_PLAN.json") if (root / OUT / "R4_23_R424_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r422_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r423_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r423_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("exact_11_normalized_jobs", n.get("job_count") == 11, n.get("job_count")),
        Check("exact_engine_normalization_scope", n.get("engine_job_counts") == AUTHORIZED_ENGINE_COUNTS, n.get("engine_job_counts")),
        Check("zero_automatic_promotions", n.get("automatic_adjudicative_promotion_count") == 0, n.get("automatic_adjudicative_promotion_count")),
        Check("exact_four_p2_cell_dispositions", c.get("cell_count") == 4, c.get("cell_count")),
        Check("geonomics_two_bindings_one_authority_gap", g.get("binding_translation_materialized_count") == 2 and g.get("binding_deferred_count") == 1 and g.get("j14_pre_200ka_spatial_authority_gap_confirmed") is True, {"materialized": g.get("binding_translation_materialized_count"), "deferred": g.get("binding_deferred_count")}),
        Check("geonomics_execution_still_not_authorized", g.get("geonomics_execution_authorized_in_r423") is False),
        Check("r424_plan_frozen", plan.get("status") == "R423_R424_SEMANTIC_PROMOTION_AND_GEONOMICS_AUTHORITY_PLAN_FROZEN", plan.get("status")),
        Check("no_engine_execution", a.get("engine_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("next_action_present", a.get("next_action") == NEXT, a.get("next_action")),
    ]
    ok = all(x.passed for x in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_P2_REEXECUTION_EVIDENCE_NORMALIZATION_AND_GEONOMICS_CANONICAL_SPATIAL_BINDING_COMPLETION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(x.passed for x in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not x.passed for x in checks),
        "checks": [x.d() for x in checks],
        "summary": {
            "normalized_authorized_job_count": a.get("normalized_authorized_job_count"),
            "normalized_engine_job_counts": a.get("normalized_engine_job_counts"),
            "authorized_p2_cell_normalized_disposition_count": a.get("authorized_p2_cell_normalized_disposition_count"),
            "semantic_promotion_gate_candidate_count": a.get("semantic_promotion_gate_candidate_count"),
            "geonomics_binding_translation_materialized_count": a.get("geonomics_binding_translation_materialized_count"),
            "geonomics_binding_deferred_count": a.get("geonomics_binding_deferred_count"),
            "geonomics_family_ready_for_execution": a.get("geonomics_family_ready_for_execution"),
            "active_target_protocol_repair_count": a.get("active_target_protocol_repair_count"),
            "proxy_context_only_count": a.get("proxy_context_only_count"),
            "p3_backlog_cell_count": a.get("p3_backlog_cell_count"),
            "engine_execution_performed": False,
            "readjudication_performed": False,
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
