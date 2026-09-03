from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

STAGE = "v0.6D1-R4.24"
PARENT_SEALED = "PASS_R423_P2_REEXECUTION_EVIDENCE_NORMALIZATION_AND_GEONOMICS_CANONICAL_SPATIAL_BINDING_COMPLETION_SEALED"
COMPLETE = "PASS_R424_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_COMPLETE"
SEALED = "PASS_R424_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_SEALED"
BLOCKED = "BLOCKED_R424_PARENT_SEMANTIC_GATE_OR_GEONOMICS_AUTHORITY_PLAN_FAILURE"
NEXT = "BUILD_R425_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY"

CFG = Path("configs/world1_r424_p2_semantic_gate_geonomics_j14_authority_v0_6D1_R4_24.json")
PSEAL = Path("outputs/v0_6D1_R4_23_SEAL/R4_23_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_23/R4_23_INTEGRATED_AUDIT.json")
PCELLS = Path("outputs/v0_6D1_R4_23/R4_23_P2_CELL_EVIDENCE_CANDIDATE_REGISTRY.json")
PGEO = Path("outputs/v0_6D1_R4_23/R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json")
PPLAN = Path("outputs/v0_6D1_R4_23/R4_23_R424_EXECUTION_PLAN.json")
OUT = Path("outputs/v0_6D1_R4_24")
SEAL = Path("outputs/v0_6D1_R4_24_SEAL/R4_24_FINAL_SEAL_AUDIT.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"


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


def _check_detail(audit: dict[str, Any], name: str) -> Any:
    for c in audit.get("checks") or []:
        if c.get("name") == name:
            return c.get("detail")
    return None


def _terminal_disposition(rec: dict[str, Any]) -> tuple[str, str]:
    disp = str(rec.get("disposition") or "")
    reason = str(rec.get("reason") or "")
    if disp == "CONTEXT_ONLY_SEMANTIC_MISMATCH":
        return "TERMINAL_NONADJUDICATIVE_SEMANTIC_MISMATCH", reason or "DOMAIN_METRIC_IDENTITY_MISMATCH"
    if disp == "NO_AUTHORIZED_DOMAIN_METRIC_FROM_R422_NORMALIZATION":
        return "TERMINAL_NONADJUDICATIVE_NO_DOMAIN_IDENTITY_TRANSFORM", reason or "NO_EXPLICIT_DOMAIN_IDENTITY_TRANSFORM_FROZEN"
    if disp == "R424_SEMANTIC_PROMOTION_GATE_CANDIDATE":
        return "UNEXPECTED_PARENT_PROMOTION_CANDIDATE_REQUIRES_EXPLICIT_R424_VALIDATION", "PARENT_CANDIDATE_COUNT_MUST_MATCH_FROZEN_R423_PLAN"
    return "TERMINAL_NONADJUDICATIVE_UNCLASSIFIED_PARENT_DISPOSITION", "UNKNOWN_PARENT_DISPOSITION_FAIL_CLOSED"


def build_semantic_gate(parent_cells: dict[str, Any]) -> dict[str, Any]:
    records = []
    for r in parent_cells.get("records") or []:
        terminal, reason = _terminal_disposition(r)
        records.append({
            "window_id": r.get("window_id"),
            "domain": r.get("domain"),
            "engine": r.get("engine"),
            "source_stage": r.get("source_stage"),
            "normalized_job_id": r.get("normalized_job_id"),
            "metric_name": r.get("metric_name"),
            "parent_disposition": r.get("disposition"),
            "parent_reason": r.get("reason"),
            "r424_terminal_disposition": terminal,
            "r424_terminal_reason": reason,
            "adjudicative_promotion_authorized": False,
            "readjudication_authorized": False,
            "canonical_change_authorized": False,
            "numeric_reinterpretation_authorized": False,
        })
    candidate_count = sum(r.get("parent_disposition") == "R424_SEMANTIC_PROMOTION_GATE_CANDIDATE" for r in records)
    all_terminal_nonadj = all(str(r.get("r424_terminal_disposition", "")).startswith("TERMINAL_NONADJUDICATIVE_") for r in records)
    return {
        "stage": STAGE,
        "status": "R424_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_CLOSED" if candidate_count == 0 and all_terminal_nonadj else BLOCKED,
        "record_count": len(records),
        "parent_semantic_promotion_candidate_count": candidate_count,
        "adjudicative_promotion_count": 0,
        "terminal_nonadjudicative_closure_count": sum(str(r.get("r424_terminal_disposition", "")).startswith("TERMINAL_NONADJUDICATIVE_") for r in records),
        "records": records,
        "readjudication_performed": False,
        "canonical_state_changed": False,
    }


def build_geonomics_authority_plan(parent_geo: dict[str, Any]) -> dict[str, Any]:
    by = {r.get("job_id"): r for r in parent_geo.get("records") or []}
    j14 = by.get(J14) or {}
    j18 = by.get(J18) or {}
    j21 = by.get(J21) or {}
    routes = [
        {
            "priority": 1,
            "route": "EXISTING_SEALED_EXPLICIT_3MA_SPATIAL_AUTHORITY_DISCOVERY",
            "execution_authorized_in_r424": False,
            "acceptance": [
                "source belongs to sealed canonical R3 evidence, not external-engine output",
                "explicit spatial coordinates or grid indices are stored, not inferred from scalar deme_count",
                "explicit time authority reaches the 3 Ma J14 window start or an exact 3 Ma checkpoint",
                "population/habitat support needed by the Geonomics binding is present",
                "source provenance and hash are frozen before any Geonomics result exists",
            ],
        },
        {
            "priority": 2,
            "route": "NEW_CANONICAL_SPATIAL_REPLAY_AUTHORITY_REQUEST",
            "execution_authorized_in_r424": False,
            "acceptance": [
                "used only if no existing sealed 3 Ma spatial authority exists",
                "requires separate explicit authorization before replay/materialization",
                "must be engine-independent and may not tune toward Geonomics outputs",
                "does not retroactively rewrite R3 parent evidence",
            ],
        },
        {
            "priority": 3,
            "route": "NEW_NAMESPACE_GEONOMICS_EXTENSION_FROM_EARLIEST_VALID_SPATIAL_ANCHOR",
            "execution_authorized_in_r424": False,
            "acceptance": [
                "new namespace only; frozen R4.2 J14 is not mutated",
                "cannot substitute for the original J14 3 Ma to 200 ka evidence cell",
                "may be used only as additional diagnostic/extension evidence after explicit authorization",
            ],
        },
    ]
    forbidden = [
        "SYNTHESIZE_3MA_SPATIAL_COORDINATES_FROM_R3_27_SCALAR_MACRO_STATE",
        "INTERPOLATE_BACKWARD_FROM_R3_15_250KA_OR_R3_28_200KA_TO_3MA_WITHOUT_EXPLICIT_AUTHORITY",
        "USE_GEONOMICS_DEFAULT_MODEL_AS_ADJUDICATIVE_EVIDENCE",
        "MUTATE_R4_2_J14_WINDOW_OR_JOB_ID",
        "EXECUTE_ONLY_J18_J21_AS_IF_FULL_R4_2_GEONOMICS_SHARED_ADAPTER_SCOPE_WERE_SATISFIED",
        "USE_EXTERNAL_ENGINE_RESULTS_TO_DEFINE_CANONICAL_SPATIAL_BINDING",
    ]
    parent_gap = parent_geo.get("j14_pre_200ka_spatial_authority_gap_confirmed") is True and j14.get("binding_materialized") is False
    preserved = bool(j18.get("binding_materialized")) and bool(j21.get("binding_materialized"))
    return {
        "stage": STAGE,
        "status": "R424_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_FROZEN" if parent_gap and preserved else BLOCKED,
        "j14_job_id": J14,
        "j14_window_id": "SAPIENT_3MA_TO_200KA",
        "j14_parent_gap_confirmed": parent_gap,
        "j18_binding_translation_preserved": bool(j18.get("binding_materialized")),
        "j21_binding_translation_preserved": bool(j21.get("binding_materialized")),
        "current_geonomics_family_execution_ready": False,
        "geonomics_execution_authorized_in_r424": False,
        "canonical_replay_authorized_in_r424": False,
        "r42_registry_mutation_authorized": False,
        "closure_routes_in_priority_order": routes,
        "forbidden_shortcuts": forbidden,
        "r425_required_operation": "READ_ONLY_DISCOVERY_OF_EXISTING_SEALED_3MA_SPATIAL_AUTHORITY_BEFORE_ANY_REPLAY_OR_EXTENSION_AUTHORITY",
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    pc = load(root / PCELLS) if (root / PCELLS).exists() else {}
    pg = load(root / PGEO) if (root / PGEO).exists() else {}
    pp = load(root / PPLAN) if (root / PPLAN).exists() else {}

    deferred_p2 = _check_detail(pa, "parent_r421_deferred_p2_cells_two")
    checks: list[Check] = [
        Check("parent_r423_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r423_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r424", pseal.get("next_action") == "BUILD_R424_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN", pseal.get("next_action")),
        Check("parent_exact_11_normalized_jobs", pa.get("normalized_authorized_job_count") == 11, pa.get("normalized_authorized_job_count")),
        Check("parent_exact_four_p2_normalized_dispositions", pa.get("authorized_p2_cell_normalized_disposition_count") == 4 and pc.get("cell_count") == 4, {"audit": pa.get("authorized_p2_cell_normalized_disposition_count"), "registry": pc.get("cell_count")}),
        Check("parent_zero_semantic_promotion_candidates", pa.get("semantic_promotion_gate_candidate_count") == 0 and pc.get("semantic_promotion_gate_candidate_count") == 0, {"audit": pa.get("semantic_promotion_gate_candidate_count"), "registry": pc.get("semantic_promotion_gate_candidate_count")}),
        Check("parent_geonomics_two_bindings_one_gap", pa.get("geonomics_binding_translation_materialized_count") == 2 and pa.get("geonomics_binding_deferred_count") == 1, {"materialized": pa.get("geonomics_binding_translation_materialized_count"), "deferred": pa.get("geonomics_binding_deferred_count")}),
        Check("parent_geonomics_not_execution_ready", pa.get("geonomics_family_ready_for_execution") is False),
        Check("parent_active_target_repairs_57", pa.get("active_target_protocol_repair_count") == 57, pa.get("active_target_protocol_repair_count")),
        Check("parent_proxy_context_two", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("parent_p3_backlog_six", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("parent_r424_plan_frozen", pp.get("status") == "R423_R424_SEMANTIC_PROMOTION_AND_GEONOMICS_AUTHORITY_PLAN_FROZEN", pp.get("status")),
        Check("parent_deferred_p2_cells_two_preserved", deferred_p2 == 2, deferred_p2),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_PRE_P2_SEMANTIC_CLOSURE_AND_J14_AUTHORITY_DISCOVERY"),
        Check("engine_execution_forbidden_in_r424", cfg.get("engine_execution_performed") is False),
        Check("readjudication_forbidden_in_r424", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
    ]
    if not all(c.passed for c in checks):
        out = {"stage": STAGE, "status": BLOCKED, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks], "next_action": "REPAIR_R424_PARENT_OR_POLICY_INPUTS"}
        write(root / OUT / "R4_24_INTEGRATED_AUDIT.json", out)
        return out

    gate = build_semantic_gate(pc)
    geo = build_geonomics_authority_plan(pg)
    checks += [
        Check("semantic_gate_exact_four_records", gate.get("record_count") == 4, gate.get("record_count")),
        Check("semantic_gate_parent_candidate_count_zero", gate.get("parent_semantic_promotion_candidate_count") == 0, gate.get("parent_semantic_promotion_candidate_count")),
        Check("semantic_gate_zero_adjudicative_promotions", gate.get("adjudicative_promotion_count") == 0, gate.get("adjudicative_promotion_count")),
        Check("semantic_gate_all_four_terminally_nonadjudicative", gate.get("terminal_nonadjudicative_closure_count") == 4, gate.get("terminal_nonadjudicative_closure_count")),
        Check("semantic_gate_no_numeric_reinterpretation", all(r.get("numeric_reinterpretation_authorized") is False for r in gate.get("records") or [])),
        Check("semantic_gate_no_readjudication", gate.get("readjudication_performed") is False),
        Check("active_p2_after_semantic_closure_exact_two_geonomics", deferred_p2 == 2, deferred_p2),
        Check("geonomics_j14_parent_gap_preserved", geo.get("j14_parent_gap_confirmed") is True),
        Check("geonomics_j18_j21_bindings_preserved", geo.get("j18_binding_translation_preserved") is True and geo.get("j21_binding_translation_preserved") is True),
        Check("geonomics_three_authority_routes_frozen", len(geo.get("closure_routes_in_priority_order") or []) == 3, len(geo.get("closure_routes_in_priority_order") or [])),
        Check("geonomics_shortcuts_explicitly_forbidden", len(geo.get("forbidden_shortcuts") or []) >= 6, geo.get("forbidden_shortcuts")),
        Check("geonomics_execution_not_authorized", geo.get("geonomics_execution_authorized_in_r424") is False),
        Check("r42_registry_mutation_not_authorized", geo.get("r42_registry_mutation_authorized") is False),
        Check("target_repair_backlog_preserved_57", pa.get("active_target_protocol_repair_count") == 57),
        Check("proxy_context_only_preserved_two", pa.get("proxy_context_only_count") == 2),
        Check("p3_backlog_preserved_six", pa.get("p3_backlog_cell_count") == 6),
        Check("no_engine_execution_in_r424", cfg.get("engine_execution_performed") is False),
        Check("no_readjudication_in_r424", cfg.get("readjudication_performed") is False),
        Check("canonical_state_still_unchanged", cfg.get("canonical_state_changed") is False),
    ]
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED
    next_action = NEXT if status == COMPLETE else "REPAIR_R424_SEMANTIC_GATE_OR_GEONOMICS_AUTHORITY_PLAN"
    plan = {
        "stage": STAGE,
        "status": "R424_P2_SEMANTIC_CLOSURE_AND_J14_AUTHORITY_PLAN_FROZEN" if status == COMPLETE else BLOCKED,
        "p2_semantically_closed_nonadjudicative_count": gate.get("terminal_nonadjudicative_closure_count"),
        "p2_adjudicative_promotion_count": gate.get("adjudicative_promotion_count"),
        "active_deferred_p2_cell_count": 2,
        "active_deferred_p2_engine_families": ["Geonomics"],
        "geonomics_j14_authority_discovery_required": True,
        "geonomics_execution_authorized_in_r425_by_r424": False,
        "target_protocol_repair_preflight_count": 57,
        "target_numeric_promotion_authorized_in_r425_by_r424": False,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_authorized_in_r425_by_r424": False,
        "canonical_replay_authorized": False,
        "canonical_parameter_change_authorized": False,
        "next_action": next_action,
    }
    out = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "p2_semantically_closed_nonadjudicative_count": gate.get("terminal_nonadjudicative_closure_count"),
        "p2_adjudicative_promotion_count": gate.get("adjudicative_promotion_count"),
        "active_deferred_p2_cell_count": 2,
        "active_deferred_p2_engine_families": ["Geonomics"],
        "geonomics_j14_spatial_authority_gap_open": True,
        "geonomics_j18_j21_binding_translation_count": 2,
        "geonomics_family_ready_for_execution": False,
        "active_target_protocol_repair_count": 57,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "next_action": next_action,
    }
    write(root / OUT / "R4_24_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE.json", gate)
    write(root / OUT / "R4_24_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN.json", geo)
    write(root / OUT / "R4_24_R425_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_24_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_24_INTEGRATED_AUDIT.json") if (root / OUT / "R4_24_INTEGRATED_AUDIT.json").exists() else {}
    g = load(root / OUT / "R4_24_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE.json") if (root / OUT / "R4_24_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE.json").exists() else {}
    geo = load(root / OUT / "R4_24_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN.json") if (root / OUT / "R4_24_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN.json").exists() else {}
    plan = load(root / OUT / "R4_24_R425_EXECUTION_PLAN.json") if (root / OUT / "R4_24_R425_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r423_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r424_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r424_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("four_p2_cells_terminally_nonadjudicative", g.get("terminal_nonadjudicative_closure_count") == 4, g.get("terminal_nonadjudicative_closure_count")),
        Check("zero_p2_adjudicative_promotions", g.get("adjudicative_promotion_count") == 0, g.get("adjudicative_promotion_count")),
        Check("active_deferred_p2_exact_two", a.get("active_deferred_p2_cell_count") == 2, a.get("active_deferred_p2_cell_count")),
        Check("geonomics_j14_authority_plan_frozen", geo.get("status") == "R424_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_FROZEN", geo.get("status")),
        Check("geonomics_execution_not_authorized", geo.get("geonomics_execution_authorized_in_r424") is False),
        Check("target_repairs_57_preserved", a.get("active_target_protocol_repair_count") == 57, a.get("active_target_protocol_repair_count")),
        Check("p3_backlog_six_preserved", a.get("p3_backlog_cell_count") == 6, a.get("p3_backlog_cell_count")),
        Check("r425_plan_frozen", plan.get("status") == "R424_P2_SEMANTIC_CLOSURE_AND_J14_AUTHORITY_PLAN_FROZEN", plan.get("status")),
        Check("no_engine_execution", a.get("engine_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("next_action_present", a.get("next_action") == NEXT, a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "p2_semantically_closed_nonadjudicative_count": a.get("p2_semantically_closed_nonadjudicative_count"),
            "p2_adjudicative_promotion_count": a.get("p2_adjudicative_promotion_count"),
            "active_deferred_p2_cell_count": a.get("active_deferred_p2_cell_count"),
            "active_deferred_p2_engine_families": a.get("active_deferred_p2_engine_families"),
            "geonomics_j14_spatial_authority_gap_open": a.get("geonomics_j14_spatial_authority_gap_open"),
            "geonomics_j18_j21_binding_translation_count": a.get("geonomics_j18_j21_binding_translation_count"),
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
