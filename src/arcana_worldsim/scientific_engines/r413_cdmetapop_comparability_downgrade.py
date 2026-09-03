from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import copy
import json

from arcana_worldsim.scientific_engines import r44_discordance_adjudication as r44
from arcana_worldsim.scientific_engines import r47_cdmetapop_forcing_parity as r47

STAGE = "v0.6D1-R4.13"
R412_SEALED = "PASS_R412_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_COMPARABILITY_DIAGNOSIS_SEALED"
R412_FINDING = "R412_CDMETAPOP_ABSOLUTE_POPULATION_RESPONSE_NEUTRAL_INVARIANCE_FAILURE_CONFIRMED"
R413_PLAN = "R413_COMPARABILITY_DOWNGRADE_PLAN_FROZEN"
COMPLETE = "PASS_R413_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_READJUDICATION_COMPLETE"
SEALED = "PASS_R413_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_READJUDICATION_SEALED"
BLOCKED = "BLOCKED_R413_PARENT_COMPARABILITY_OVERRIDE_OR_READJUDICATION_FAILURE"
NEXT_STRUCTURAL = "BUILD_R414_REMAINING_STRUCTURAL_CAUSAL_DIAGNOSIS_AFTER_CDMETAPOP_COMPARABILITY_DOWNGRADE"
NEXT_GAPS = "BUILD_R414_MULTI_ENGINE_EVIDENCE_GAP_CLOSURE_AND_TARGETED_ADAPTER_ENHANCEMENT"
NEXT_OFFSETS = "BUILD_R414_TARGETED_CALIBRATION_REVIEW_WITHOUT_AUTOMATIC_CANONICAL_CHANGE"
NEXT_CLOSURE = "BUILD_R414_REVALIDATION_CLOSURE_AND_BASELINE_PROMOTION_GATE"

CFG_REL = Path("configs/world1_r413_cdmetapop_comparability_downgrade_v0_6D1_R4_13.json")
R412_SEAL_REL = Path("outputs/v0_6D1_R4_12_SEAL/R4_12_FINAL_SEAL_AUDIT.json")
R412_DIAG_REL = Path("outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json")
R412_PLAN_REL = Path("outputs/v0_6D1_R4_12/R4_12_R413_COMPARABILITY_PLAN.json")
R411_MATRIX_REL = Path("outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json")
R44_CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
OUT_REL = Path("outputs/v0_6D1_R4_13")
SEAL_REL = Path("outputs/v0_6D1_R4_13_SEAL/R4_13_FINAL_SEAL_AUDIT.json")

AFFECTED = [
    "R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP",
    "R42_J06_H0_PRE_CHA1_CDMETAPOP",
    "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
    "R42_J15_SAPIENT_3MA_TO_200KA_CDMETAPOP",
    "R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP",
]
METRIC = "population_agent_response_ratio"
CLASSES = ["CONCORDANT", "CALIBRATION_OFFSET", "STRUCTURAL_DISAGREEMENT", "SEMANTICALLY_NONCOMPARABLE", "INSUFFICIENT_EVIDENCE"]
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


def _metric_name(row: dict[str, Any]) -> str | None:
    metric = row.get("metric")
    return metric.get("name") if isinstance(metric, dict) else None


def _is_downgrade_target(row: dict[str, Any]) -> bool:
    return (
        row.get("engine") == "CDMetaPOP"
        and row.get("job_id") in AFFECTED
        and _metric_name(row) == METRIC
    )


def _proxy_reclassify(row: dict[str, Any], cfg44: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(row)
    old_comp = out.get("mapping_comparability")
    old_class = out.get("discordance_class")
    out["stage"] = STAGE
    out["parent_stage"] = row.get("stage")
    out["parent_mapping_comparability"] = old_comp
    out["parent_discordance_class"] = old_class
    out["mapping_comparability"] = "PROXY_ONLY"
    out["comparability_override"] = {
        "status": "APPLIED",
        "finding": R412_FINDING,
        "metric": METRIC,
        "from": old_comp,
        "to": "PROXY_ONLY",
        "canonical_change": False,
    }
    metric = out.get("metric") or {}
    target = out.get("target")
    if isinstance(target, dict) and isinstance(metric, dict) and metric.get("name") == METRIC and isinstance(metric.get("summary"), dict):
        res = r44.classify_pair(target, METRIC, metric["summary"], "PROXY_ONLY", cfg44)
        # Replace only R4.4 adjudication fields, preserving evidence/provenance.
        for k in [
            "discordance_class", "reason", "combined_comparability", "target_direction", "external_direction",
            "target_value", "external_median", "external_q10", "external_q90", "magnitude_comparison_used"
        ]:
            out.pop(k, None)
        out.update(res)
    else:
        # If a row lacks a valid target/metric pair it remains non-adjudicative evidence.
        out["discordance_class"] = "INSUFFICIENT_EVIDENCE"
        out["reason"] = "R413_PROXY_OVERRIDE_ROW_LACKS_VALID_TARGET_METRIC_PAIR"
        out["combined_comparability"] = "PROXY_ONLY"
        out["magnitude_comparison_used"] = False
    return out


def _semantic_parent_fingerprint(row: dict[str, Any]) -> str:
    # Used only to prove non-target rows are copied without semantic mutation.
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def readjudicate(root: Path) -> tuple[dict[str, Any], list[Check]]:
    cfg = load_json(root / CFG_REL)
    seal = load_json(root / R412_SEAL_REL) if (root / R412_SEAL_REL).exists() else {}
    diag = load_json(root / R412_DIAG_REL) if (root / R412_DIAG_REL).exists() else {}
    plan = load_json(root / R412_PLAN_REL) if (root / R412_PLAN_REL).exists() else {}
    parent = load_json(root / R411_MATRIX_REL) if (root / R411_MATRIX_REL).exists() else {}
    cfg44 = load_json(root / R44_CFG_REL) if (root / R44_CFG_REL).exists() else {}
    parent_rows = list(parent.get("evidence_rows") or [])
    parent_cells = list(parent.get("cells") or [])

    target_rows = [r for r in parent_rows if isinstance(r, dict) and _is_downgrade_target(r)]
    target_job_ids = {r.get("job_id") for r in target_rows}
    target_bad_scope = [r.get("job_id") for r in target_rows if r.get("job_id") not in AFFECTED]
    target_old_comp = sorted({str(r.get("mapping_comparability")) for r in target_rows})

    checks = [
        Check("parent_r412_seal_present", (root / R412_SEAL_REL).exists(), str(R412_SEAL_REL)),
        Check("parent_r412_sealed", seal.get("status") == R412_SEALED, seal.get("status")),
        Check("parent_r412_finding_matches", diag.get("finding") == R412_FINDING, diag.get("finding")),
        Check("parent_r413_plan_frozen", plan.get("status") == R413_PLAN, plan.get("status")),
        Check("parent_absolute_response_proxy_only_pending", str(diag.get("absolute_population_response_comparability", "")).startswith("PROXY_ONLY"), diag.get("absolute_population_response_comparability")),
        Check("exact_five_symmetric_cdmetapop_jobs", list(cfg.get("affected_frozen_cdmetapop_jobs") or []) == AFFECTED, cfg.get("affected_frozen_cdmetapop_jobs")),
        Check("parent_matrix_exact_75_cells", parent.get("cell_count") == 75 and len(parent_cells) == 75, {"declared": parent.get("cell_count"), "loaded": len(parent_cells)}),
        Check("parent_matrix_has_evidence_rows", bool(parent_rows), len(parent_rows)),
        Check("downgrade_metric_exact", cfg.get("comparability_override", {}).get("metric_name") == METRIC, cfg.get("comparability_override", {}).get("metric_name")),
        Check("downgrade_scope_only_affected_jobs", not target_bad_scope, target_bad_scope),
        Check("at_least_one_population_response_row_selected", len(target_rows) > 0, len(target_rows)),
        Check("selected_rows_match_authorized_from_comparability", all(r.get("mapping_comparability") in tuple(cfg.get("comparability_override", {}).get("from", [])) for r in target_rows), target_old_comp),
        Check("matched_control_global_promotion_forbidden", cfg.get("comparability_override", {}).get("matched_control_global_metric_promotion") is False),
        Check("parent_mapping_files_not_modified_by_contract", cfg.get("comparability_override", {}).get("parent_r43_mapping_files_are_not_modified") is True),
        Check("parent_r411_matrix_not_modified_by_contract", cfg.get("comparability_override", {}).get("parent_r411_matrix_is_not_modified") is True),
        Check("engine_execution_forbidden", cfg.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
    ]
    if any(not c.passed for c in checks):
        out = {"stage": STAGE, "status": BLOCKED, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.to_dict() for c in checks], "canonical_state_changed": False}
        write_json(root / OUT_REL / "R4_13_INTEGRATED_AUDIT.json", out)
        return out, checks

    revised_rows: list[dict[str, Any]] = []
    overrides: list[dict[str, Any]] = []
    for r in parent_rows:
        if _is_downgrade_target(r):
            nr = _proxy_reclassify(r, cfg44)
            revised_rows.append(nr)
            overrides.append({
                "window_id": nr.get("window_id"), "job_id": nr.get("job_id"), "domain": nr.get("domain"),
                "authority_role": nr.get("authority_role"), "metric_name": METRIC,
                "from_comparability": r.get("mapping_comparability"), "to_comparability": "PROXY_ONLY",
                "parent_discordance_class": r.get("discordance_class"), "proxy_context_class": nr.get("discordance_class"),
                "reason": R412_FINDING,
            })
        else:
            revised_rows.append(copy.deepcopy(r))

    revised_cells = r47._recompute_cells(root, revised_rows)
    counts = {c: sum(1 for x in revised_cells if x.get("discordance_class") == c) for c in CLASSES}
    structural = counts["STRUCTURAL_DISAGREEMENT"]
    gaps = counts["INSUFFICIENT_EVIDENCE"] + counts["SEMANTICALLY_NONCOMPARABLE"]
    offsets = counts["CALIBRATION_OFFSET"]

    if structural:
        next_action = NEXT_STRUCTURAL
    elif gaps:
        next_action = NEXT_GAPS
    elif offsets:
        next_action = NEXT_OFFSETS
    else:
        next_action = NEXT_CLOSURE

    parent_non_targets = [_semantic_parent_fingerprint(r) for r in parent_rows if not _is_downgrade_target(r)]
    new_non_targets = [_semantic_parent_fingerprint(r) for r in revised_rows if not _is_downgrade_target(r)]
    downgraded_rows = [r for r in revised_rows if _is_downgrade_target(r)]
    downgraded_adjudicative = [r for r in downgraded_rows if r.get("mapping_comparability") in ("DIRECT", "NORMALIZABLE")]
    proxy_structural = [r for r in downgraded_rows if r.get("discordance_class") == "STRUCTURAL_DISAGREEMENT"]
    j09_rows = [r for r in revised_rows if r.get("job_id") == J09 and r.get("domain") == "population_persistence" and r.get("authority_role") == "PRIMARY"]

    old_by = {(x.get("window_id"), x.get("domain")): x for x in parent_cells}
    new_by = {(x.get("window_id"), x.get("domain")): x for x in revised_cells}
    changed = []
    for key, nr in new_by.items():
        orow = old_by.get(key, {})
        if orow.get("discordance_class") != nr.get("discordance_class"):
            changed.append({"window_id": key[0], "domain": key[1], "old_class": orow.get("discordance_class"), "new_class": nr.get("discordance_class")})

    checks += [
        Check("all_selected_rows_downgraded_to_proxy_only", len(downgraded_rows) == len(target_rows) and not downgraded_adjudicative, {"selected": len(target_rows), "downgraded": len(downgraded_rows)}),
        Check("proxy_rows_cannot_remain_structural", not proxy_structural, [{"job_id": r.get("job_id"), "domain": r.get("domain")} for r in proxy_structural]),
        Check("non_target_parent_rows_preserved_semantically", parent_non_targets == new_non_targets, {"parent": len(parent_non_targets), "new": len(new_non_targets)}),
        Check("all_five_jobs_covered_where_metric_selected", target_job_ids.issubset(set(AFFECTED)), sorted(target_job_ids)),
        Check("revised_matrix_exact_75_cells", len(revised_cells) == 75, len(revised_cells)),
        Check("five_class_accounting_complete", sum(counts.values()) == 75, counts),
        Check("all_downgraded_rows_are_nonadjudicative_by_frozen_mapping_class", all(r.get("mapping_comparability") == "PROXY_ONLY" for r in downgraded_rows), sorted({r.get("mapping_comparability") for r in downgraded_rows})),
        Check("no_secondary_only_promotion", all(not (x.get("discordance_class") in ("CONCORDANT", "CALIBRATION_OFFSET", "STRUCTURAL_DISAGREEMENT") and x.get("primary_adjudicative_rows") == 0) for x in revised_cells)),
        Check("no_majority_vote_anywhere", all(x.get("majority_vote") is False for x in revised_cells) and all(r.get("majority_vote") is False for r in revised_rows)),
        Check("engine_execution_not_performed", cfg.get("engine_execution_performed") is False),
        Check("canonical_state_still_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_still_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_still_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
    ]
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED

    registry = {
        "stage": STAGE, "status": status,
        "trigger_finding": R412_FINDING,
        "metric_name": METRIC,
        "new_comparability": "PROXY_ONLY",
        "override_count": len(overrides),
        "overrides": overrides,
        "symmetric_job_scope": AFFECTED,
        "parent_r43_mapping_files_modified": False,
        "parent_r411_matrix_modified": False,
        "matched_control_global_metric_promoted": False,
        "canonical_change_authorized": False,
    }
    matrix = {
        "stage": STAGE, "status": status, "cell_count": len(revised_cells), "class_counts": counts,
        "cells": revised_cells, "evidence_rows": revised_rows,
        "parent_matrix": str(R411_MATRIX_REL), "parent_matrix_preserved": True,
        "comparability_override_registry": "R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json",
        "engine_execution_performed": False, "canonical_state_changed": False,
        "scientific_agreement_claimed": False, "next_action": next_action,
    }
    summary = {
        "stage": STAGE, "status": status,
        "class_counts_after_comparability_downgrade": counts,
        "structural_disagreement_count_after_comparability_downgrade": structural,
        "calibration_offset_count_after_comparability_downgrade": offsets,
        "evidence_gap_count_after_comparability_downgrade": gaps,
        "downgraded_evidence_row_count": len(overrides),
        "downgraded_job_ids": sorted(target_job_ids),
        "j09_population_persistence_class_after_comparability_downgrade": j09_rows[0].get("discordance_class") if j09_rows else None,
        "j09_population_persistence_mapping_comparability": j09_rows[0].get("mapping_comparability") if j09_rows else None,
        "changed_cell_count": len(changed), "changed_cells": changed,
        "engine_execution_performed": False, "canonical_state_changed": False,
        "canonical_replay_authorized": False, "canonical_parameter_change_authorized": False,
        "deep_biological_coupling": False, "next_action": next_action,
    }
    audit = {
        "stage": STAGE, "status": status,
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks], "class_counts": counts,
        "canonical_state_changed": False, "next_action": next_action,
    }
    write_json(root / OUT_REL / "R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json", registry)
    write_json(root / OUT_REL / "R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json", matrix)
    write_json(root / OUT_REL / "R4_13_READJUDICATION_DELTA.json", {"stage": STAGE, "status": status, "changed_cell_count": len(changed), "changed_cells": changed, "parent_class_counts": parent.get("class_counts"), "new_class_counts": counts, "canonical_change_authorized": False, "next_action": next_action})
    write_json(root / OUT_REL / "R4_13_EXECUTION_SUMMARY.json", summary)
    write_json(root / OUT_REL / "R4_13_INTEGRATED_AUDIT.json", audit)
    return audit, checks


def final_seal(root: Path) -> tuple[dict[str, Any], list[Check]]:
    parent = load_json(root / R412_SEAL_REL) if (root / R412_SEAL_REL).exists() else {}
    audit = load_json(root / OUT_REL / "R4_13_INTEGRATED_AUDIT.json") if (root / OUT_REL / "R4_13_INTEGRATED_AUDIT.json").exists() else {}
    summary = load_json(root / OUT_REL / "R4_13_EXECUTION_SUMMARY.json") if (root / OUT_REL / "R4_13_EXECUTION_SUMMARY.json").exists() else {}
    matrix = load_json(root / OUT_REL / "R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json") if (root / OUT_REL / "R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json").exists() else {}
    registry = load_json(root / OUT_REL / "R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json") if (root / OUT_REL / "R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json").exists() else {}
    cfg = load_json(root / CFG_REL)
    checks = [
        Check("parent_r412_sealed", parent.get("status") == R412_SEALED, parent.get("status")),
        Check("r413_complete", audit.get("status") == COMPLETE, audit.get("status")),
        Check("r413_zero_process_failures", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("readjudicated_matrix_75_cells", matrix.get("cell_count") == 75, matrix.get("cell_count")),
        Check("class_accounting_complete", sum((matrix.get("class_counts") or {}).values()) == 75, matrix.get("class_counts")),
        Check("comparability_override_registry_present", registry.get("new_comparability") == "PROXY_ONLY" and registry.get("override_count", 0) > 0, {"override_count": registry.get("override_count"), "new": registry.get("new_comparability")}),
        Check("parent_matrix_preserved", matrix.get("parent_matrix_preserved") is True),
        Check("matched_control_not_globally_promoted", registry.get("matched_control_global_metric_promoted") is False),
        Check("no_engine_execution", summary.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged", summary.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", summary.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", summary.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", summary.get("deep_biological_coupling") is False),
        Check("next_action_present", bool(summary.get("next_action")), summary.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_SYMMETRIC_READJUDICATION",
        "status": SEALED if ok else BLOCKED, "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks],
        "summary": summary, "next_action": summary.get("next_action"),
    }
    write_json(root / SEAL_REL, out)
    return out, checks
