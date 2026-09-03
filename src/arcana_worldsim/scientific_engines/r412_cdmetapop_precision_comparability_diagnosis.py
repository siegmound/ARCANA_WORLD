from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import math
import re

import numpy as np

STAGE = "v0.6D1-R4.12"
R411_SEALED = "PASS_R411_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION_SEALED"
R411_UNCERTAIN = "R411_CORRECTED_MATCHED_CONTROL_EFFECT_UNCERTAIN"
COMPLETE = "PASS_R412_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_COMPARABILITY_DIAGNOSIS_COMPLETE"
SEALED = "PASS_R412_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_COMPARABILITY_DIAGNOSIS_SEALED"
BLOCKED = "BLOCKED_R412_PARENT_PRECISION_OR_COMPARABILITY_DIAGNOSIS_FAILURE"
FINDING = "R412_CDMETAPOP_ABSOLUTE_POPULATION_RESPONSE_NEUTRAL_INVARIANCE_FAILURE_CONFIRMED"
NEXT_DOWNGRADE = "BUILD_R413_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_READJUDICATION"
NEXT_PRECISION = "BUILD_R413_CDMETAPOP_PRECISION_AND_ALTERNATE_EVIDENCE_CLOSURE_WITHOUT_AUTOMATIC_REPLICATE_ESCALATION"
NEXT_MECHANISM = "BUILD_R413_R311_CDMETAPOP_MECHANISM_DECOMPOSITION_AFTER_METRIC_REPAIR"

CFG_REL = Path("configs/world1_r412_cdmetapop_precision_comparability_v0_6D1_R4_12.json")
R411_SEAL_REL = Path("outputs/v0_6D1_R4_11_SEAL/R4_11_FINAL_SEAL_AUDIT.json")
R411_SUMMARY_REL = Path("outputs/v0_6D1_R4_11/R4_11_EXECUTION_SUMMARY.json")
R411_PAIR_REL = Path("outputs/v0_6D1_R4_11/R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json")
R411_MATRIX_REL = Path("outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json")
R44_CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R43_MAP_REL = Path("outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json")
R43_J09_CONTRACT_REL = Path("outputs/v0_6D1_R4_3/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/JOB_CONTRACT.json")
R47_ADAPTER_REL = Path("benchmarks/r47/cdmetapop_r47.py")
R48_ADAPTER_REL = Path("benchmarks/r48/cdmetapop_r48_neutral.py")
R49D_ADAPTER_REL = Path("benchmarks/r49/cdmetapop_r49_dynamic.py")
R49N_ADAPTER_REL = Path("benchmarks/r49/cdmetapop_r49_neutral.py")
OUT_REL = Path("outputs/v0_6D1_R4_12")
SEAL_REL = Path("outputs/v0_6D1_R4_12_SEAL/R4_12_FINAL_SEAL_AUDIT.json")

AFFECTED = [
    "R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP",
    "R42_J06_H0_PRE_CHA1_CDMETAPOP",
    "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
    "R42_J15_SAPIENT_3MA_TO_200KA_CDMETAPOP",
    "R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP",
]
J09 = "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP"

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def finite(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def summary(vals: list[float]) -> dict[str, Any]:
    a = np.asarray(vals, dtype=float)
    if a.size == 0:
        return {"n": 0, "median": None, "q10": None, "q90": None, "min": None, "max": None, "mean": None}
    return {
        "n": int(a.size), "median": float(np.median(a)), "q10": float(np.quantile(a, .1)),
        "q90": float(np.quantile(a, .9)), "min": float(a.min()), "max": float(a.max()), "mean": float(a.mean())
    }


def _vals(rows: list[dict[str, Any]], key: str) -> list[float]:
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        v = finite(r.get(key))
        if v is not None:
            out.append(v)
    return out


def _bootstrap_median_ci(vals: list[float], draws: int, seed: int) -> dict[str, Any]:
    if not vals:
        return {"draws": draws, "rng_seed": seed, "median_ci95": [None, None]}
    a = np.asarray(vals, dtype=float)
    rng = np.random.default_rng(seed)
    # Fixed pre-result diagnostic only; it never changes the frozen R4.4 adjudication thresholds.
    idx = rng.integers(0, a.size, size=(draws, a.size))
    meds = np.median(a[idx], axis=1)
    return {
        "draws": int(draws), "rng_seed": int(seed),
        "median_ci95": [float(np.quantile(meds, .025)), float(np.quantile(meds, .975))],
        "adjudicative": False,
    }


def _adapter_source_audit(root: Path) -> dict[str, Any]:
    rels = [R47_ADAPTER_REL, R48_ADAPTER_REL, R49D_ADAPTER_REL, R49N_ADAPTER_REL]
    files = {}
    all_half_k = True
    for rel in rels:
        p = root / rel
        text = p.read_text(encoding="utf-8-sig", errors="replace") if p.exists() else ""
        half = re.search(r"k0\s*\*\s*0\.5", text) is not None
        target_in_n0 = "arcana_start_population_descriptor" in text
        files[str(rel)] = {
            "present": p.exists(),
            "n0_half_k_initialization_detected": half,
            "arcana_start_population_descriptor_referenced_in_adapter": target_in_n0,
        }
        all_half_k = all_half_k and p.exists() and half
    contract = load_json(root / R43_J09_CONTRACT_REL) if (root / R43_J09_CONTRACT_REL).exists() else {}
    drivers = ((contract.get("engine_input") or {}).get("drivers") or {})
    arc_start = finite(drivers.get("arcana_start_population_descriptor"))
    return {
        "files": files,
        "common_half_k_start_initialization": all_half_k,
        "j09_arcana_start_population_descriptor_present": arc_start is not None,
        "j09_arcana_start_population_descriptor": arc_start,
        "adapter_n0_not_initialized_from_arcana_population_descriptor": all(not x["arcana_start_population_descriptor_referenced_in_adapter"] for x in files.values()),
        "interpretation": "The R4.7-R4.9 CDMetaPOP experiment initializes N0 from approximately 0.5*K_start rather than mapping the ARCANA start population descriptor. Absolute final/initial population response therefore contains start-state relaxation unless neutral-control invariance is demonstrated.",
    }


def _selected_population_metric_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for r in matrix.get("evidence_rows", []):
        if not isinstance(r, dict) or r.get("engine") != "CDMetaPOP":
            continue
        metric = r.get("metric") or {}
        if metric.get("name") == "population_agent_response_ratio":
            out.append({
                "window_id": r.get("window_id"), "job_id": r.get("job_id"), "domain": r.get("domain"),
                "authority_role": r.get("authority_role"), "mapping_comparability": r.get("mapping_comparability"),
                "discordance_class": r.get("discordance_class"), "reason": r.get("reason"),
            })
    return out


def diagnose(root: Path) -> tuple[dict[str, Any], list[Check]]:
    cfg = load_json(root / CFG_REL)
    parent = load_json(root / R411_SEAL_REL) if (root / R411_SEAL_REL).exists() else {}
    psummary = load_json(root / R411_SUMMARY_REL) if (root / R411_SUMMARY_REL).exists() else {}
    pair = load_json(root / R411_PAIR_REL) if (root / R411_PAIR_REL).exists() else {}
    matrix = load_json(root / R411_MATRIX_REL) if (root / R411_MATRIX_REL).exists() else {}
    r44cfg = load_json(root / R44_CFG_REL) if (root / R44_CFG_REL).exists() else {}
    rows = list(pair.get("paired_replicates") or [])
    neutral_factor = finite((r44cfg.get("effect_policy") or {}).get("ratio_neutral_factor"))
    pair_neutral = finite(pair.get("neutral_factor"))
    low = 1.0 / neutral_factor if neutral_factor and neutral_factor > 0 else None
    high = neutral_factor
    neutral_vals = _vals(rows, "neutral_absolute_ratio")
    dynamic_vals = _vals(rows, "dynamic_absolute_ratio")
    paired_vals = _vals(rows, "paired_forcing_effect_ratio")
    neutral_stats = summary(neutral_vals); dynamic_stats = summary(dynamic_vals); paired_stats = summary(paired_vals)
    source_audit = _adapter_source_audit(root)

    if low is not None and high is not None and neutral_stats["q10"] is not None:
        if neutral_stats["q10"] > high:
            neutral_class = "NEUTRAL_CONTROL_ROBUST_UPWARD_RELAXATION"
        elif neutral_stats["q90"] < low:
            neutral_class = "NEUTRAL_CONTROL_ROBUST_DOWNWARD_RELAXATION"
        elif neutral_stats["q10"] >= low and neutral_stats["q90"] <= high:
            neutral_class = "NEUTRAL_CONTROL_STABLE_WITHIN_FROZEN_BAND"
        else:
            neutral_class = "NEUTRAL_CONTROL_RELAXATION_UNCERTAIN"
    else:
        neutral_class = "NEUTRAL_CONTROL_RELAXATION_UNRESOLVED"
    invariance_failure = neutral_class in ("NEUTRAL_CONTROL_ROBUST_UPWARD_RELAXATION", "NEUTRAL_CONTROL_ROBUST_DOWNWARD_RELAXATION")

    arc = finite(pair.get("arcana_causal_forcing_effect_ratio"))
    med = paired_stats.get("median")
    median_abs_delta = abs(med - arc) if med is not None and arc is not None else None
    median_relative_delta = median_abs_delta / abs(arc) if median_abs_delta is not None and arc not in (None, 0.0) else None
    pair_counts = {"below_lower_neutral_band": 0, "inside_neutral_band": 0, "above_upper_neutral_band": 0, "below_one": 0, "at_or_above_one": 0}
    if low is not None and high is not None:
        for v in paired_vals:
            if v < low: pair_counts["below_lower_neutral_band"] += 1
            elif v > high: pair_counts["above_upper_neutral_band"] += 1
            else: pair_counts["inside_neutral_band"] += 1
            if v < 1.0: pair_counts["below_one"] += 1
            else: pair_counts["at_or_above_one"] += 1
    boot = _bootstrap_median_ci(paired_vals, int(cfg["precision_policy"]["bootstrap_median_draws"]), int(cfg["precision_policy"]["bootstrap_rng_seed"]))

    selected_rows = _selected_population_metric_rows(matrix)
    j09_rows = [r for r in selected_rows if r.get("job_id") == J09 and r.get("domain") == "population_persistence" and r.get("authority_role") == "PRIMARY"]
    mapping = load_json(root / R43_MAP_REL) if (root / R43_MAP_REL).exists() else {}
    mapped_jobs = {m.get("job_id") for m in mapping.get("mappings", []) if isinstance(m, dict) and m.get("job_id") in AFFECTED}

    if invariance_failure:
        finding = FINDING
        comparability = "PROXY_ONLY_PENDING_MATCHED_CONTROL_SEMANTIC_PROTOCOL"
        next_action = NEXT_DOWNGRADE
    elif neutral_class == "NEUTRAL_CONTROL_STABLE_WITHIN_FROZEN_BAND" and pair.get("diagnosis_class") == "R411_CORRECTED_MATCHED_CONTROL_OPPOSITE_DIRECTION_ROBUST":
        finding = "R412_ABSOLUTE_RESPONSE_NEUTRAL_INVARIANCE_PASSED_BUT_MODEL_RESPONSE_DISAGREEMENT_REMAINS"
        comparability = "NORMALIZABLE_NOT_INVALIDATED_BY_NEUTRAL_CONTROL"
        next_action = NEXT_MECHANISM
    else:
        finding = "R412_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_REMAINS_UNRESOLVED"
        comparability = "NORMALIZABLE_NOT_CONFIRMED"
        next_action = NEXT_PRECISION

    checks = [
        Check("parent_r411_seal_present", (root / R411_SEAL_REL).exists(), str(R411_SEAL_REL)),
        Check("parent_r411_sealed", parent.get("status") == R411_SEALED, parent.get("status")),
        Check("parent_next_action_matches_r412", parent.get("next_action") == cfg["required_parent_next_action"], parent.get("next_action")),
        Check("parent_corrected_matrix_75_cells", matrix.get("cell_count") == 75, matrix.get("cell_count")),
        Check("parent_structural_cell_still_one", psummary.get("structural_disagreement_count_after_metric_repair") == 1, psummary.get("structural_disagreement_count_after_metric_repair")),
        Check("parent_j09_population_persistence_structural", psummary.get("j09_population_persistence_class_after_metric_repair") == "STRUCTURAL_DISAGREEMENT", psummary.get("j09_population_persistence_class_after_metric_repair")),
        Check("parent_corrected_matched_control_uncertain", pair.get("diagnosis_class") == R411_UNCERTAIN, pair.get("diagnosis_class")),
        Check("exact_20_corrected_pairs", len(rows) == 20 and len(neutral_vals) == 20 and len(dynamic_vals) == 20 and len(paired_vals) == 20, {"rows": len(rows), "neutral": len(neutral_vals), "dynamic": len(dynamic_vals), "paired": len(paired_vals)}),
        Check("frozen_r44_neutral_factor_reused", neutral_factor is not None and pair_neutral is not None and math.isclose(neutral_factor, pair_neutral, rel_tol=0, abs_tol=1e-12), {"r44": neutral_factor, "r411": pair_neutral}),
        Check("common_adapter_half_k_initialization_confirmed", source_audit["common_half_k_start_initialization"], source_audit["files"]),
        Check("arcana_start_descriptor_not_used_for_adapter_n0", source_audit["j09_arcana_start_population_descriptor_present"] and source_audit["adapter_n0_not_initialized_from_arcana_population_descriptor"], {"arcana_start_population_descriptor": source_audit["j09_arcana_start_population_descriptor"]}),
        Check("all_five_symmetric_cdmetapop_jobs_mapped", mapped_jobs == set(AFFECTED), sorted(mapped_jobs)),
        Check("j09_corrected_primary_population_row_resolved", len(j09_rows) == 1, j09_rows),
        Check("r412_does_not_reclassify_parent_matrix", cfg["precision_policy"]["preserve_r411_readjudication_without_posthoc_reclassification"] is True),
        Check("automatic_more_engine_replicates_forbidden", cfg["precision_policy"]["automatic_additional_engine_replicates_forbidden"] is True),
        Check("matched_control_global_promotion_forbidden_in_r412", cfg["comparability_policy"]["global_matched_control_metric_promotion_in_r412"] is False),
        Check("canonical_state_unchanged", cfg["canonical_state_changed"] is False),
        Check("canonical_replay_not_authorized", cfg["canonical_replay_authorized"] is False),
        Check("canonical_parameter_change_not_authorized", cfg["canonical_parameter_change_authorized"] is False),
        Check("deep_off", cfg["deep_biological_coupling"] is False),
        Check("majority_vote_forbidden", cfg["majority_vote"] is False),
        Check("engine_execution_not_performed", cfg["engine_execution_performed"] is False),
    ]
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED

    precision = {
        "stage": STAGE, "status": status, "parent_diagnosis_preserved": pair.get("diagnosis_class"),
        "arcana_causal_forcing_effect_ratio": arc,
        "corrected_paired_effect_summary": paired_stats,
        "paired_median_abs_delta_from_arcana": median_abs_delta,
        "paired_median_relative_delta_from_arcana": median_relative_delta,
        "descriptive_pair_counts": pair_counts,
        "bootstrap_median": boot,
        "frozen_neutral_factor": neutral_factor,
        "frozen_neutral_band": [low, high] if low is not None else None,
        "precision_reclassification_authorized": False,
        "automatic_additional_engine_replicates_authorized": False,
    }
    comparability_diag = {
        "stage": STAGE, "status": status, "finding": finding,
        "neutral_absolute_response_summary": neutral_stats,
        "dynamic_absolute_response_summary": dynamic_stats,
        "neutral_control_class": neutral_class,
        "neutral_invariance_failure": invariance_failure,
        "absolute_population_response_comparability": comparability,
        "source_initialization_audit": source_audit,
        "selected_cdmetapop_population_response_rows": selected_rows,
        "selected_row_count": len(selected_rows),
        "parent_r411_matrix_preserved": True,
        "parent_r411_structural_finding_actionable_for_canonical_replay": False if invariance_failure else None,
        "matched_control_metric_global_promotion_authorized": False,
        "canonical_change_authorized": False,
        "next_action": next_action,
    }
    plan = {
        "stage": STAGE,
        "status": "R413_COMPARABILITY_DOWNGRADE_PLAN_FROZEN" if invariance_failure else "R413_FOLLOWUP_PLAN_FROZEN",
        "trigger_finding": finding,
        "actions": ([
            "PRESERVE_R411_MATRIX_AND_ALL_HISTORICAL_EVIDENCE",
            "CREATE_NEW_R413_EVIDENCE_NAMESPACE_ONLY",
            "DOWNGRADE_population_agent_response_ratio_FROM_NORMALIZABLE_TO_PROXY_ONLY_FOR_ALL_FIVE_FROZEN_CDMETAPOP_JOBS_WHERE_SELECTED",
            "READJUDICATE_ALL_75_CELLS_WITH_FROZEN_R44_POLICY_WITHOUT_MAJORITY_VOTE",
            "DO_NOT_PROMOTE_J09_MATCHED_CONTROL_AS_GLOBAL_METRIC_WITHOUT_WINDOW_SPECIFIC_ARCANA_CAUSAL_TARGETS",
            "DO_NOT_EXECUTE_ENGINES_IN_COMPARABILITY_DOWNGRADE_STAGE",
        ] if invariance_failure else [
            "PRESERVE_R411_MATRIX_AND_ALL_HISTORICAL_EVIDENCE",
            "DO_NOT_AUTOMATICALLY_ADD_ENGINE_REPLICATES",
            "BUILD_SEPARATE_PRECISION_OR_MECHANISM_EVIDENCE_STAGE",
        ]),
        "symmetric_job_scope": AFFECTED,
        "metric_scope": "population_agent_response_ratio",
        "parent_matrix_rewrite": False,
        "new_engine_execution_authorized": False,
        "canonical_state_changed": False,
        "canonical_replay_authorized": False,
        "canonical_parameter_change_authorized": False,
        "next_action": next_action,
    }
    audit = {
        "stage": STAGE, "status": status,
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks], "finding": finding,
        "neutral_control_class": neutral_class, "absolute_population_response_comparability": comparability,
        "canonical_state_changed": False, "next_action": next_action,
    }
    write_json(root / OUT_REL / "R4_12_METRIC_REPAIRED_PRECISION_AUDIT.json", precision)
    write_json(root / OUT_REL / "R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json", comparability_diag)
    write_json(root / OUT_REL / "R4_12_R413_COMPARABILITY_PLAN.json", plan)
    write_json(root / OUT_REL / "R4_12_INTEGRATED_AUDIT.json", audit)
    return audit, checks


def final_seal(root: Path) -> tuple[dict[str, Any], list[Check]]:
    parent = load_json(root / R411_SEAL_REL) if (root / R411_SEAL_REL).exists() else {}
    audit = load_json(root / OUT_REL / "R4_12_INTEGRATED_AUDIT.json") if (root / OUT_REL / "R4_12_INTEGRATED_AUDIT.json").exists() else {}
    precision = load_json(root / OUT_REL / "R4_12_METRIC_REPAIRED_PRECISION_AUDIT.json") if (root / OUT_REL / "R4_12_METRIC_REPAIRED_PRECISION_AUDIT.json").exists() else {}
    comp = load_json(root / OUT_REL / "R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json") if (root / OUT_REL / "R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json").exists() else {}
    plan = load_json(root / OUT_REL / "R4_12_R413_COMPARABILITY_PLAN.json") if (root / OUT_REL / "R4_12_R413_COMPARABILITY_PLAN.json").exists() else {}
    cfg = load_json(root / CFG_REL)
    checks = [
        Check("parent_r411_sealed", parent.get("status") == R411_SEALED, parent.get("status")),
        Check("r412_diagnosis_complete", audit.get("status") == COMPLETE, audit.get("status")),
        Check("r412_zero_process_failures", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("precision_preserves_r411_classification", precision.get("precision_reclassification_authorized") is False),
        Check("comparability_diagnosis_present", bool(comp.get("finding")), comp.get("finding")),
        Check("r413_plan_present", bool(plan.get("status")), plan.get("status")),
        Check("no_engine_execution", plan.get("new_engine_execution_authorized") is False),
        Check("canonical_state_unchanged", plan.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", plan.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", plan.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("next_action_present", bool(audit.get("next_action")), audit.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks],
        "summary": {
            "finding": comp.get("finding"),
            "neutral_control_class": comp.get("neutral_control_class"),
            "absolute_population_response_comparability": comp.get("absolute_population_response_comparability"),
            "corrected_paired_effect_summary": precision.get("corrected_paired_effect_summary"),
            "arcana_causal_forcing_effect_ratio": precision.get("arcana_causal_forcing_effect_ratio"),
            "canonical_state_changed": False,
            "canonical_replay_authorized": False,
            "canonical_parameter_change_authorized": False,
            "deep_biological_coupling": False,
            "next_action": audit.get("next_action"),
        },
        "next_action": audit.get("next_action"),
    }
    write_json(root / SEAL_REL, out)
    return out, checks
