from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

STAGE = "v0.6D1-R4.28"
PARENT_SEALED = "PASS_R427_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_TARGET_DESIGN_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION_SEALED"
PARENT_NEXT = "BUILD_R428_TARGET_SELECTOR_AND_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT"
COMPLETE = "PASS_R428_TARGET_SELECTOR_AND_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT_COMPLETE"
SEALED = "PASS_R428_TARGET_SELECTOR_AND_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT_SEALED"
BLOCKED = "BLOCKED_R428_PARENT_SELECTOR_DESIGN_OR_J14_PREFLIGHT_FAILURE"
NEXT = "BUILD_R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_AND_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION"

CFG = Path("configs/world1_r428_target_selector_design_authority_j14_preflight_v0_6D1_R4_28.json")
PSEAL = Path("outputs/v0_6D1_R4_27_SEAL/R4_27_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_27/R4_27_INTEGRATED_AUDIT.json")
PSTATIC = Path("outputs/v0_6D1_R4_27/R4_27_TARGET_EXTRACTOR_STATIC_VALIDATION_REGISTRY.json")
PTARGET = Path("outputs/v0_6D1_R4_27/R4_27_TARGET_DESIGN_AUTHORITY_ADJUDICATION.json")
PJ14 = Path("outputs/v0_6D1_R4_27/R4_27_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION.json")
PPLAN = Path("outputs/v0_6D1_R4_27/R4_27_R428_EXECUTION_PLAN.json")
R416 = Path("outputs/v0_6D1_R4_16/R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json")
R426DESIGN = Path("outputs/v0_6D1_R4_26/R4_26_TARGET_DESIGN_AUTHORITY_REQUEST_REGISTRY.json")
R426J14 = Path("outputs/v0_6D1_R4_26/R4_26_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST.json")
R423GEO = Path("outputs/v0_6D1_R4_23/R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json")
OUT = Path("outputs/v0_6D1_R4_28")
SEAL = Path("outputs/v0_6D1_R4_28_SEAL/R4_28_FINAL_SEAL_AUDIT.json")

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

def _schema_inventory(binding: dict[str, Any]) -> list[str]:
    schema = binding.get("schema") or {}
    parser = str(binding.get("parser_family") or "")
    if parser == "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR":
        return sorted({str(x) for x in schema.get("schema_paths") or []})
    if parser == "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR":
        return sorted({str(x.get("selector")) for x in schema.get("arrays") or [] if x.get("selector")})
    if parser == "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR":
        return sorted({str(x) for x in schema.get("header_candidates") or []})
    return []

def _protocol_map(protocol_registry: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out = {}
    for r in protocol_registry.get("records") or []:
        out[(str(r.get("window_id")), str(r.get("domain")))] = r
    return out

def build_selector_preflight(static: dict[str, Any], protocols: dict[str, Any]) -> dict[str, Any]:
    pmap = _protocol_map(protocols)
    records = []
    for r in static.get("records") or []:
        key = (str(r.get("window_id")), str(r.get("domain")))
        proto_rec = pmap.get(key) or {}
        exact_inventory = []
        source_packets = []
        for b in r.get("source_bindings") or []:
            valid = bool(b.get("hash_match") and b.get("parser_supported") and b.get("static_schema_valid"))
            inv = _schema_inventory(b) if valid else []
            exact_inventory.extend(inv)
            source_packets.append({
                "source": b.get("source"),
                "parser_family": b.get("parser_family"),
                "expected_sha256": b.get("expected_sha256"),
                "observed_sha256": b.get("observed_sha256"),
                "hash_match": b.get("hash_match"),
                "static_schema_valid": b.get("static_schema_valid"),
                "exact_schema_inventory": inv,
            })
        exact_inventory = sorted(set(exact_inventory))
        protocol = proto_rec.get("protocol")
        source_integrity_ready = bool(r.get("static_implementation_valid") and source_packets)
        protocol_ready = bool(protocol)
        inventory_ready = bool(exact_inventory)
        ready = bool(source_integrity_ready and protocol_ready and inventory_ready)
        if ready:
            disposition = "READY_EXACT_SCHEMA_INVENTORY_AND_PROTOCOL"
            next_priority = "R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE"
        elif source_integrity_ready and protocol_ready and not inventory_ready:
            # R4.28-R1: an empty exact inventory is a scientifically explicit deferral,
            # not a process failure. We must not synthesize column names/selectors.
            disposition = "DEFERRED_NO_EXACT_SCHEMA_SELECTOR_INVENTORY"
            next_priority = "R429_SCHEMALESS_SOURCE_AUTHORITY_OR_ALTERNATE_CANONICAL_SOURCE_CLOSURE"
        elif source_integrity_ready and not protocol_ready:
            disposition = "BLOCKED_DOMAIN_PROTOCOL_MISSING"
            next_priority = "REPAIR_R428_PROTOCOL_REGISTRY_INTEGRITY"
        else:
            disposition = "BLOCKED_SOURCE_OR_STATIC_IMPLEMENTATION_INTEGRITY"
            next_priority = "REPAIR_R428_SELECTOR_PREFLIGHT_SOURCE_INTEGRITY"
        records.append({
            "window_id": r.get("window_id"),
            "domain": r.get("domain"),
            "authority_class": "PRE_RESULT_EXACT_SELECTOR_AND_TRANSFORM_AUTHORITY",
            "parent_static_implementation_valid": r.get("static_implementation_valid"),
            "parent_selector_authorized": r.get("selector_execution_authorized_in_r427"),
            "source_packets": source_packets,
            "exact_schema_inventory": exact_inventory,
            "domain_protocol": protocol,
            "selector_authority_preflight_ready": ready,
            "selector_authority_preflight_disposition": disposition,
            "source_integrity_ready": source_integrity_ready,
            "domain_protocol_ready": protocol_ready,
            "exact_schema_inventory_ready": inventory_ready,
            "selector_selection_policy": "EXPLICIT_EXACT_FIELD_FREEZE_ONLY",
            "selector_must_be_member_of_exact_schema_inventory": True,
            "transform_policy": "IDENTITY_OR_EXPLICIT_PRE_RESULT_DOMAIN_TRANSFORM_ONLY",
            "fuzzy_matching_authorized": False,
            "synonym_fallback_authorized": False,
            "external_result_comparison_authorized_for_selector_choice": False,
            "result_selected_selector_authorized": False,
            "selector_authorized_in_r428": False,
            "numeric_target_execution_authorized_in_r428": False,
            "next_priority": next_priority,
        })
    ready_count = sum(bool(r.get("selector_authority_preflight_ready")) for r in records)
    deferred = [r for r in records if r.get("selector_authority_preflight_disposition") == "DEFERRED_NO_EXACT_SCHEMA_SELECTOR_INVENTORY"]
    blocked = [r for r in records if str(r.get("selector_authority_preflight_disposition", "")).startswith("BLOCKED_")]
    terminal_count = ready_count + len(deferred)
    return {
        "stage": STAGE,
        "repair_revision": "R4.28-R1",
        "repair_finding": "R428_INITIAL_GATE_INCORRECTLY_REQUIRED_EXACT_SELECTOR_INVENTORY_FROM_ALL_HASH_VALID_SOURCES",
        "status": "R428_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT_COMPLETE" if len(records) == 44 and terminal_count == 44 and not blocked else BLOCKED,
        "record_count": len(records),
        "selector_authority_preflight_ready_count": ready_count,
        "selector_authority_preflight_deferred_no_exact_inventory_count": len(deferred),
        "selector_authority_preflight_terminal_count": terminal_count,
        "selector_authority_preflight_blocked_count": len(blocked),
        "selector_authorized_count": 0,
        "numeric_target_execution_authorized_count": 0,
        "records": records,
    }

def implement_target_design_authorities(adj: dict[str, Any], requests: dict[str, Any]) -> dict[str, Any]:
    amap = {(str(r.get("window_id")), str(r.get("domain"))): r for r in adj.get("records") or []}
    records = []
    for req in requests.get("requests") or []:
        key = (str(req.get("window_id")), str(req.get("domain")))
        a = amap.get(key) or {}
        approved = a.get("authority_definition_implementation_authorized_in_r428") is True
        implemented = bool(approved and req.get("scientific_construct") and req.get("required_canonical_observables") and req.get("permitted_unit_families"))
        records.append({
            "window_id": req.get("window_id"),
            "domain": req.get("domain"),
            "authority_definition_id": f"R428_TARGET_AUTHORITY_{req.get('window_id')}_{req.get('domain')}",
            "scientific_construct": req.get("scientific_construct"),
            "required_canonical_observables": req.get("required_canonical_observables"),
            "permitted_unit_families": req.get("permitted_unit_families"),
            "required_governance": req.get("required_governance"),
            "forbidden_shortcuts": req.get("forbidden_shortcuts"),
            "external_engine_result_may_define_target": False,
            "result_selected_transform_authorized": False,
            "implementation_status": "PRE_RESULT_AUTHORITY_DEFINITION_IMPLEMENTED_NONNUMERIC" if implemented else "DEFERRED_AUTHORITY_IMPLEMENTATION_SPEC_FAILURE",
            "authority_definition_implemented": implemented,
            "numeric_target_definition_authorized_in_r428": False,
            "numeric_target_materialization_authorized_in_r428": False,
            "next_priority": "R429_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_VALIDATION" if implemented else "REPAIR_R428_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION",
        })
    implemented_count = sum(bool(r.get("authority_definition_implemented")) for r in records)
    return {
        "stage": STAGE,
        "status": "R428_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_COMPLETE" if len(records) == 12 and implemented_count == 12 else BLOCKED,
        "record_count": len(records),
        "authority_definition_implemented_count": implemented_count,
        "numeric_target_materialization_authorized_count": 0,
        "records": records,
    }

def build_semantic_repair_preflight(static: dict[str, Any]) -> dict[str, Any]:
    records = []
    for r in static.get("semantic_repair_records") or []:
        ready = bool(r.get("static_validation_pass") and r.get("failed_validation_keys_frozen") == ["eligible_primary_row_count"])
        records.append({
            "window_id": r.get("window_id"),
            "domain": r.get("domain"),
            "frozen_review_scope": r.get("failed_validation_keys_frozen"),
            "review_preflight_ready": ready,
            "allowed_operation": "PRIMARY_MAPPING_ELIGIBILITY_REVIEW_ONLY",
            "numeric_value_change_authorized": False,
            "mapping_class_upgrade_authorized": False,
            "readjudication_authorized_in_r428": False,
            "next_priority": "R429_PRIMARY_MAPPING_ELIGIBILITY_REVIEW" if ready else "REPAIR_R428_SEMANTIC_REPAIR_PREFLIGHT",
        })
    return {
        "stage": STAGE,
        "status": "R428_SEMANTIC_REPAIR_IMPLEMENTATION_PREFLIGHT_COMPLETE" if len(records) == 1 and records[0].get("review_preflight_ready") else BLOCKED,
        "record_count": len(records),
        "review_preflight_ready_count": sum(bool(r.get("review_preflight_ready")) for r in records),
        "records": records,
    }

def build_j14_preflight(adj: dict[str, Any], req: dict[str, Any], geo: dict[str, Any]) -> dict[str, Any]:
    parent_approved = adj.get("spatial_authority_implementation_preflight_authorized_in_r428") is True
    j14_parent = next((r for r in geo.get("records") or [] if r.get("job_id") == "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"), {})
    audited_sources = j14_parent.get("canonical_spatial_sources_audited") or []
    checks = {
        "r427_preflight_authorized": parent_approved,
        "request_kind_engine_independent": req.get("request_kind") == "NEW_ENGINE_INDEPENDENT_CANONICAL_SPATIAL_REPLAY_AUTHORITY",
        "new_namespace_required": req.get("new_namespace_required_if_authority_is_later_approved") is True,
        "temporal_support_exact_3ma_to_200ka": (req.get("required_temporal_support") or {}).get("start_age_ma") == 3.0 and (req.get("required_temporal_support") or {}).get("end_age_ka") == 200.0,
        "canonical_source_audit_context_present": len(audited_sources) >= 2,
        "r327_macro_state_explicitly_nonspatial": j14_parent.get("r327_macro_state_is_spatial") is False,
        "window_start_spatial_state_absent_confirmed": j14_parent.get("window_start_3000ka_explicit_spatial_state_present") is False,
        "r42_job_mutation_forbidden": req.get("r42_j14_mutation_authorized") is False,
    }
    ready = all(checks.values())
    return {
        "stage": STAGE,
        "status": "R428_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT_COMPLETE" if ready else BLOCKED,
        "job_id": req.get("job_id"),
        "window_id": req.get("window_id"),
        "authority_namespace": "R429_PLUS_NEW_ENGINE_INDEPENDENT_CANONICAL_SPATIAL_REPLAY_AUTHORITY",
        "authority_kind": req.get("request_kind"),
        "required_temporal_support": req.get("required_temporal_support"),
        "required_spatial_support": req.get("required_spatial_support"),
        "required_authority_properties": req.get("required_authority_properties"),
        "aggregate_invariants_to_preserve_or_explain": req.get("aggregate_invariants_to_preserve_or_explain"),
        "forbidden_shortcuts": req.get("forbidden_shortcuts"),
        "parent_canonical_source_audit_context": audited_sources,
        "checks": checks,
        "implementation_preflight_ready": ready,
        "canonical_spatial_replay_execution_authorized_in_r428": False,
        "geonomics_execution_authorized_in_r428": False,
        "r42_j14_mutation_authorized": False,
        "active_deferred_p2_cell_count": 2,
        "next_priority": "R429_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION_GATE" if ready else "REPAIR_R428_J14_SPATIAL_REPLAY_PREFLIGHT",
    }

def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    static = load(root / PSTATIC) if (root / PSTATIC).exists() else {}
    target_adj = load(root / PTARGET) if (root / PTARGET).exists() else {}
    j14_adj = load(root / PJ14) if (root / PJ14).exists() else {}
    pplan = load(root / PPLAN) if (root / PPLAN).exists() else {}
    protocols = load(root / R416) if (root / R416).exists() else {}
    design_req = load(root / R426DESIGN) if (root / R426DESIGN).exists() else {}
    j14_req = load(root / R426J14) if (root / R426J14).exists() else {}
    geo = load(root / R423GEO) if (root / R423GEO).exists() else {}

    selector = build_selector_preflight(static, protocols)
    design = implement_target_design_authorities(target_adj, design_req)
    semantic = build_semantic_repair_preflight(static)
    j14 = build_j14_preflight(j14_adj, j14_req, geo)

    checks = [
        Check("parent_r427_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r427_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r428", pa.get("next_action") == PARENT_NEXT, pa.get("next_action")),
        Check("parent_44_extractors_static_valid", pa.get("canonical_extractor_static_valid_count") == 44, pa.get("canonical_extractor_static_valid_count")),
        Check("parent_zero_selectors_authorized", pa.get("canonical_extractor_selector_authorized_count") == 0, pa.get("canonical_extractor_selector_authorized_count")),
        Check("parent_44_selectors_deferred", pa.get("canonical_extractor_selector_deferred_count") == 44, pa.get("canonical_extractor_selector_deferred_count")),
        Check("parent_one_semantic_repair_authorized", pa.get("semantic_repair_review_authorized_count") == 1, pa.get("semantic_repair_review_authorized_count")),
        Check("parent_12_target_authorities_approved", pa.get("target_design_authority_approved_count") == 12, pa.get("target_design_authority_approved_count")),
        Check("parent_j14_preflight_authorized", pa.get("j14_spatial_authority_implementation_preflight_authorized") is True, pa.get("j14_spatial_authority_implementation_preflight_authorized")),
        Check("parent_r428_plan_frozen", pplan.get("status") == "R427_STATIC_VALIDATION_AND_AUTHORITY_ADJUDICATION_FROZEN", pplan.get("status")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_PRE_EXPLICIT_SELECTOR_AUTHORITY_FREEZE_TARGET_NUMERIC_EXECUTION_AND_J14_SPATIAL_REPLAY_EXECUTION", cfg.get("policy_freeze")),
        Check("selector_preflight_exact_44", selector.get("record_count") == 44, selector.get("record_count")),
        Check("all_44_selector_authority_preflights_terminally_disposed", selector.get("selector_authority_preflight_terminal_count") == 44 and selector.get("selector_authority_preflight_blocked_count") == 0, {"ready": selector.get("selector_authority_preflight_ready_count"), "deferred_no_exact_inventory": selector.get("selector_authority_preflight_deferred_no_exact_inventory_count"), "blocked": selector.get("selector_authority_preflight_blocked_count"), "total": selector.get("record_count")}),
        Check("zero_selectors_auto_authorized", selector.get("selector_authorized_count") == 0, selector.get("selector_authorized_count")),
        Check("selector_inventory_exact_only", all(r.get("selector_selection_policy") == "EXPLICIT_EXACT_FIELD_FREEZE_ONLY" and r.get("fuzzy_matching_authorized") is False for r in selector.get("records") or [])),
        Check("selector_external_result_choice_forbidden", all(r.get("external_result_comparison_authorized_for_selector_choice") is False for r in selector.get("records") or [])),
        Check("target_design_definition_exact_12", design.get("record_count") == 12, design.get("record_count")),
        Check("all_12_target_design_definitions_implemented_nonnumeric", design.get("authority_definition_implemented_count") == 12, design.get("authority_definition_implemented_count")),
        Check("target_design_numeric_materialization_zero", design.get("numeric_target_materialization_authorized_count") == 0),
        Check("semantic_repair_preflight_exact_one_ready", semantic.get("record_count") == 1 and semantic.get("review_preflight_ready_count") == 1, {"records": semantic.get("record_count"), "ready": semantic.get("review_preflight_ready_count")}),
        Check("semantic_repair_scope_immutable", all(r.get("numeric_value_change_authorized") is False and r.get("mapping_class_upgrade_authorized") is False for r in semantic.get("records") or [])),
        Check("j14_spatial_replay_authority_preflight_ready", j14.get("implementation_preflight_ready") is True, j14.get("checks")),
        Check("j14_replay_execution_not_authorized", j14.get("canonical_spatial_replay_execution_authorized_in_r428") is False),
        Check("geonomics_execution_not_authorized", j14.get("geonomics_execution_authorized_in_r428") is False),
        Check("r42_j14_mutation_forbidden", j14.get("r42_j14_mutation_authorized") is False),
        Check("active_deferred_p2_two_preserved", pa.get("active_deferred_p2_cell_count") == 2, pa.get("active_deferred_p2_cell_count")),
        Check("proxy_context_only_two_preserved", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("p3_backlog_six_preserved", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("no_engine_execution", cfg.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", cfg.get("target_numeric_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_spatial_replay_not_authorized", cfg.get("canonical_spatial_replay_execution_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
    ]
    ok = all(c.passed for c in checks)
    plan = {
        "stage": STAGE,
        "status": "R428_SELECTOR_DESIGN_AND_J14_PREFLIGHT_FROZEN" if ok else BLOCKED,
        "repair_revision": "R4.28-R1",
        "repair_finding": "R428_INITIAL_GATE_INCORRECTLY_REQUIRED_EXACT_SELECTOR_INVENTORY_FROM_ALL_HASH_VALID_SOURCES",
        "selector_authority_preflight_ready_count": selector.get("selector_authority_preflight_ready_count"),
        "selector_authority_preflight_deferred_no_exact_inventory_count": selector.get("selector_authority_preflight_deferred_no_exact_inventory_count"),
        "selector_authority_preflight_terminal_count": selector.get("selector_authority_preflight_terminal_count"),
        "selector_authorized_count": 0,
        "target_design_authority_definition_implemented_count": design.get("authority_definition_implemented_count"),
        "semantic_repair_preflight_ready_count": semantic.get("review_preflight_ready_count"),
        "j14_spatial_replay_authority_preflight_ready": j14.get("implementation_preflight_ready"),
        "target_numeric_execution_authorized_in_r429_by_r428": False,
        "canonical_spatial_replay_execution_authorized_in_r429_by_r428": False,
        "geonomics_execution_authorized_in_r429_by_r428": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R428_SELECTOR_DESIGN_OR_J14_PREFLIGHT",
    }
    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "repair_revision": "R4.28-R1",
        "repair_finding": "R428_INITIAL_GATE_INCORRECTLY_REQUIRED_EXACT_SELECTOR_INVENTORY_FROM_ALL_HASH_VALID_SOURCES",
        "selector_authority_preflight_ready_count": selector.get("selector_authority_preflight_ready_count"),
        "selector_authority_preflight_deferred_no_exact_inventory_count": selector.get("selector_authority_preflight_deferred_no_exact_inventory_count"),
        "selector_authority_preflight_terminal_count": selector.get("selector_authority_preflight_terminal_count"),
        "selector_authorized_count": 0,
        "target_design_authority_definition_implemented_count": design.get("authority_definition_implemented_count"),
        "semantic_repair_preflight_ready_count": semantic.get("review_preflight_ready_count"),
        "j14_spatial_replay_authority_preflight_ready": j14.get("implementation_preflight_ready"),
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "canonical_spatial_replay_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json", selector)
    write(root / OUT / "R4_28_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_REGISTRY.json", design)
    write(root / OUT / "R4_28_SEMANTIC_REPAIR_IMPLEMENTATION_PREFLIGHT.json", semantic)
    write(root / OUT / "R4_28_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT.json", j14)
    write(root / OUT / "R4_28_R429_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_28_INTEGRATED_AUDIT.json", out)
    return out

def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_28_INTEGRATED_AUDIT.json") if (root / OUT / "R4_28_INTEGRATED_AUDIT.json").exists() else {}
    s = load(root / OUT / "R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json") if (root / OUT / "R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json").exists() else {}
    d = load(root / OUT / "R4_28_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_REGISTRY.json") if (root / OUT / "R4_28_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_REGISTRY.json").exists() else {}
    sem = load(root / OUT / "R4_28_SEMANTIC_REPAIR_IMPLEMENTATION_PREFLIGHT.json") if (root / OUT / "R4_28_SEMANTIC_REPAIR_IMPLEMENTATION_PREFLIGHT.json").exists() else {}
    j14 = load(root / OUT / "R4_28_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT.json") if (root / OUT / "R4_28_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT.json").exists() else {}
    plan = load(root / OUT / "R4_28_R429_EXECUTION_PLAN.json") if (root / OUT / "R4_28_R429_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r427_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r428_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r428_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("selector_preflight_44_terminally_disposed", s.get("selector_authority_preflight_terminal_count") == 44 and s.get("selector_authority_preflight_blocked_count") == 0, {"ready": s.get("selector_authority_preflight_ready_count"), "deferred_no_exact_inventory": s.get("selector_authority_preflight_deferred_no_exact_inventory_count"), "blocked": s.get("selector_authority_preflight_blocked_count")}),
        Check("zero_selector_auto_authorizations", s.get("selector_authorized_count") == 0, s.get("selector_authorized_count")),
        Check("target_design_12_definitions_implemented", d.get("authority_definition_implemented_count") == 12, d.get("authority_definition_implemented_count")),
        Check("zero_numeric_target_authorizations", d.get("numeric_target_materialization_authorized_count") == 0),
        Check("semantic_repair_one_preflight_ready", sem.get("review_preflight_ready_count") == 1, sem.get("review_preflight_ready_count")),
        Check("j14_spatial_replay_preflight_ready", j14.get("implementation_preflight_ready") is True, j14.get("implementation_preflight_ready")),
        Check("j14_no_replay_or_geonomics_execution_authorized", j14.get("canonical_spatial_replay_execution_authorized_in_r428") is False and j14.get("geonomics_execution_authorized_in_r428") is False),
        Check("r429_plan_frozen", plan.get("status") == "R428_SELECTOR_DESIGN_AND_J14_PREFLIGHT_FROZEN", plan.get("status")),
        Check("deferred_p2_two", a.get("active_deferred_p2_cell_count") == 2, a.get("active_deferred_p2_cell_count")),
        Check("p3_backlog_six", a.get("p3_backlog_cell_count") == 6, a.get("p3_backlog_cell_count")),
        Check("no_engine_execution", a.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", a.get("target_numeric_execution_performed") is False),
        Check("no_canonical_spatial_replay_execution", a.get("canonical_spatial_replay_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("next_action_present", a.get("next_action") == NEXT, a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "repair_revision": "R4.28-R1",
        "repair_finding": "R428_INITIAL_GATE_INCORRECTLY_REQUIRED_EXACT_SELECTOR_INVENTORY_FROM_ALL_HASH_VALID_SOURCES",
        "audit": "FINAL_TARGET_SELECTOR_AND_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "selector_authority_preflight_ready_count": a.get("selector_authority_preflight_ready_count"),
            "selector_authority_preflight_deferred_no_exact_inventory_count": a.get("selector_authority_preflight_deferred_no_exact_inventory_count"),
            "selector_authority_preflight_terminal_count": a.get("selector_authority_preflight_terminal_count"),
            "selector_authorized_count": 0,
            "target_design_authority_definition_implemented_count": a.get("target_design_authority_definition_implemented_count"),
            "semantic_repair_preflight_ready_count": a.get("semantic_repair_preflight_ready_count"),
            "j14_spatial_replay_authority_preflight_ready": a.get("j14_spatial_replay_authority_preflight_ready"),
            "active_deferred_p2_cell_count": a.get("active_deferred_p2_cell_count"),
            "proxy_context_only_count": a.get("proxy_context_only_count"),
            "p3_backlog_cell_count": a.get("p3_backlog_cell_count"),
            "engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "canonical_spatial_replay_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
            "canonical_replay_execution_authorized": False,
            "canonical_parameter_change_authorized": False,
            "deep_biological_coupling": False,
            "next_action": a.get("next_action"),
        },
        "next_action": a.get("next_action"),
    }
    write(root / SEAL, out)
    return out
