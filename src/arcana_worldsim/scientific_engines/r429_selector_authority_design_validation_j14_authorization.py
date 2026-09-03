from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import hashlib
import json
import zipfile

from arcana_worldsim.scientific_engines.r429_j14_spatial_authority_replay import (
    AUTHORITY_ALGORITHM,
    validate_authority_inputs,
)

STAGE = "v0.6D1-R4.29"
PARENT_SEALED = "PASS_R428_TARGET_SELECTOR_AND_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT_SEALED"
PARENT_NEXT = "BUILD_R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_AND_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION"
COMPLETE = "PASS_R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_AND_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION_COMPLETE"
SEALED = "PASS_R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_AND_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION_SEALED"
BLOCKED = "BLOCKED_R429_PARENT_SELECTOR_AUTHORITY_DESIGN_VALIDATION_OR_J14_AUTHORIZATION_FAILURE"
NEXT = "BUILD_R430_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION"

CFG = Path("configs/world1_r429_selector_authority_design_validation_j14_execution_authorization_v0_6D1_R4_29.json")
PSEAL = Path("outputs/v0_6D1_R4_28_SEAL/R4_28_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_28/R4_28_INTEGRATED_AUDIT.json")
PSELECT = Path("outputs/v0_6D1_R4_28/R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json")
PDESIGN = Path("outputs/v0_6D1_R4_28/R4_28_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_REGISTRY.json")
PSEM = Path("outputs/v0_6D1_R4_28/R4_28_SEMANTIC_REPAIR_IMPLEMENTATION_PREFLIGHT.json")
PJ14 = Path("outputs/v0_6D1_R4_28/R4_28_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT.json")
PPLAN = Path("outputs/v0_6D1_R4_28/R4_28_R429_EXECUTION_PLAN.json")
R426DESIGN = Path("outputs/v0_6D1_R4_26/R4_26_TARGET_DESIGN_AUTHORITY_REQUEST_REGISTRY.json")
R427DESIGN = Path("outputs/v0_6D1_R4_27/R4_27_TARGET_DESIGN_AUTHORITY_ADJUDICATION.json")
OUT = Path("outputs/v0_6D1_R4_29")
SEAL = Path("outputs/v0_6D1_R4_29_SEAL/R4_29_FINAL_SEAL_AUDIT.json")


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_recorded_path(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    p = Path(str(raw))
    if p.is_absolute() and p.exists():
        return p
    s = str(raw).replace("\\", "/")
    q = root / s
    if q.exists():
        return q
    for marker in ("/outputs/", "/local_runs/", "/references/"):
        if marker in s:
            rel = s.split(marker, 1)[1]
            q = root / marker.strip("/") / rel
            if q.exists():
                return q
    return None


def _json_exact_dict_paths(obj: Any, prefix: str = "", depth: int = 0, limit: int = 4096) -> list[str]:
    # Only dict traversal is supported by the already-frozen R4.26 JSON exact extractor.
    if depth > 12 or limit <= 0 or not isinstance(obj, dict):
        return []
    out: list[str] = []
    for key in sorted(obj):
        if len(out) >= limit:
            break
        k = str(key)
        path = f"{prefix}.{k}" if prefix else k
        value = obj[key]
        if isinstance(value, dict):
            children = _json_exact_dict_paths(value, path, depth + 1, limit - len(out))
            if children:
                out.extend(children)
            else:
                out.append(path)
        else:
            out.append(path)
    return out[:limit]


def recover_exact_inventory(path: Path, parser_family: str) -> list[str]:
    parser = str(parser_family or "")
    suffix = path.suffix.lower()
    if parser == "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR":
        return sorted(set(_json_exact_dict_paths(load(path))))
    if parser == "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR":
        # NPZ inventory is read from ZIP member names only; arrays are not materialized.
        with zipfile.ZipFile(path, "r") as zf:
            names = [Path(n).name[:-4] for n in zf.namelist() if n.endswith(".npy")]
        return sorted(set(names))
    if parser == "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR":
        delim = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            row = next(csv.reader(f, delimiter=delim), [])
        return [str(x) for x in row if str(x)]
    return []


def build_schemaless_closure(root: Path, parent: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for rec in parent.get("records") or []:
        if rec.get("selector_authority_preflight_disposition") != "DEFERRED_NO_EXACT_SCHEMA_SELECTOR_INVENTORY":
            continue
        source_results = []
        recovered: list[str] = []
        for sp in rec.get("source_packets") or []:
            p = _resolve_recorded_path(root, sp.get("source"))
            expected = str(sp.get("expected_sha256") or "")
            if p is None or not p.exists():
                source_results.append({"source": sp.get("source"), "present": False, "hash_match": False, "recovered_inventory": []})
                continue
            observed = sha256(p)
            hmatch = bool(expected and observed == expected)
            inv = recover_exact_inventory(p, str(sp.get("parser_family") or "")) if hmatch else []
            recovered.extend(inv)
            source_results.append({
                "source": str(p), "present": True, "expected_sha256": expected, "observed_sha256": observed,
                "hash_match": hmatch, "parser_family": sp.get("parser_family"), "recovered_inventory": inv,
            })
        recovered = sorted(set(recovered))
        hash_valid_sources = [x for x in source_results if x.get("present") and x.get("hash_match")]
        source_integrity_pass = bool(hash_valid_sources)
        closed = bool(recovered) and source_integrity_pass
        if not source_integrity_pass:
            closure_status = "BLOCKED_SOURCE_INTEGRITY_DRIFT_AFTER_R428"
        elif closed:
            closure_status = "EXACT_SCHEMA_INVENTORY_RECOVERED_READ_ONLY"
        else:
            closure_status = "SCHEMALESS_SOURCE_AUTHORITY_GAP_FROZEN"
        records.append({
            "window_id": rec.get("window_id"), "domain": rec.get("domain"),
            "parent_disposition": rec.get("selector_authority_preflight_disposition"),
            "source_results": source_results,
            "recovered_exact_schema_inventory": recovered,
            "source_integrity_pass": source_integrity_pass,
            "closure_status": closure_status,
            "selector_synthesis_authorized": False,
            "fuzzy_or_synonym_discovery_authorized": False,
            "numeric_target_execution_authorized": False,
            "next_priority": "R429_EXPLICIT_SELECTOR_RULE_MATCH" if closed else "R430_SCHEMALESS_OR_ALTERNATE_CANONICAL_SOURCE_AUTHORITY_CLOSURE",
        })
    recovered_count = sum(r.get("closure_status") == "EXACT_SCHEMA_INVENTORY_RECOVERED_READ_ONLY" for r in records)
    gap_count = sum(r.get("closure_status") == "SCHEMALESS_SOURCE_AUTHORITY_GAP_FROZEN" for r in records)
    blocked_count = sum(str(r.get("closure_status", "")).startswith("BLOCKED_") for r in records)
    return {
        "stage": STAGE,
        "status": "R429_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_COMPLETE" if len(records) == 6 and blocked_count == 0 else BLOCKED,
        "record_count": len(records),
        "inventory_recovered_count": recovered_count,
        "authority_gap_frozen_count": gap_count,
        "source_integrity_blocked_count": blocked_count,
        "records": records,
    }


def _rule_matches(inventory: list[str], rule_selector: str) -> list[str]:
    # Exact full-selector or unique exact leaf-token binding only. No substring/synonym/fuzzy logic.
    full = [x for x in inventory if x == rule_selector]
    if full:
        return full
    leaf = [x for x in inventory if x.rsplit(".", 1)[-1] == rule_selector]
    return leaf


def freeze_selector_authorities(parent: dict[str, Any], closure: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    recovered_map = {(str(r.get("window_id")), str(r.get("domain"))): list(r.get("recovered_exact_schema_inventory") or []) for r in closure.get("records") or []}
    catalog = cfg.get("exact_selector_authority_catalog") or {}
    records = []
    for rec in parent.get("records") or []:
        key = (str(rec.get("window_id")), str(rec.get("domain")))
        inventory = sorted(set(list(rec.get("exact_schema_inventory") or []) + recovered_map.get(key, [])))
        rules = list(catalog.get(str(rec.get("domain"))) or [])
        matches: list[dict[str, Any]] = []
        for rule in rules:
            paths = _rule_matches(inventory, str(rule.get("selector") or ""))
            for path in paths:
                matches.append({**rule, "bound_selector": path})
        # De-duplicate exact rule/path duplicates.
        unique = []
        seen = set()
        for m in matches:
            k = (m.get("selector"), m.get("bound_selector"), m.get("transform_id"), m.get("authority_class"))
            if k not in seen:
                seen.add(k); unique.append(m)
        matches = unique
        authorized = len(matches) == 1
        if authorized:
            disp = "EXPLICIT_PRE_RESULT_SELECTOR_AUTHORITY_FROZEN"
            next_priority = "R430_AUTHORIZED_TARGET_NUMERIC_MATERIALIZATION"
        elif not inventory:
            disp = "DEFERRED_SCHEMALESS_SOURCE_AUTHORITY_GAP"
            next_priority = "R430_SCHEMALESS_OR_ALTERNATE_CANONICAL_SOURCE_AUTHORITY_CLOSURE"
        elif len(matches) == 0:
            disp = "DEFERRED_NO_EXACT_PRE_RESULT_SELECTOR_RULE_MATCH"
            next_priority = "R430_EXPLICIT_SELECTOR_RULE_OR_ALTERNATE_CANONICAL_SOURCE_AUTHORITY_CLOSURE"
        else:
            disp = "DEFERRED_AMBIGUOUS_MULTIPLE_EXACT_PRE_RESULT_SELECTOR_RULE_MATCHES"
            next_priority = "R430_AMBIGUOUS_SELECTOR_AUTHORITY_CLOSURE"
        frozen = matches[0] if authorized else None
        records.append({
            "window_id": rec.get("window_id"), "domain": rec.get("domain"),
            "parent_preflight_disposition": rec.get("selector_authority_preflight_disposition"),
            "exact_schema_inventory": inventory,
            "catalog_rule_count": len(rules),
            "exact_rule_matches": matches,
            "selector_authority_disposition": disp,
            "selector_authorized": authorized,
            "frozen_selector": frozen.get("bound_selector") if frozen else None,
            "frozen_rule_selector_token": frozen.get("selector") if frozen else None,
            "frozen_transform_id": frozen.get("transform_id") if frozen else None,
            "frozen_authority_class": frozen.get("authority_class") if frozen else None,
            "selector_choice_used_external_results": False,
            "fuzzy_matching_used": False,
            "synonym_fallback_used": False,
            "numeric_target_execution_performed": False,
            "numeric_target_materialization_authorized_in_r430": authorized,
            "next_priority": next_priority,
        })
    authorized = [r for r in records if r.get("selector_authorized")]
    deferred = [r for r in records if not r.get("selector_authorized")]
    return {
        "stage": STAGE,
        "status": "R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_COMPLETE" if len(records) == 44 else BLOCKED,
        "record_count": len(records),
        "selector_authorized_count": len(authorized),
        "selector_deferred_count": len(deferred),
        "numeric_target_materialization_authorized_for_r430_count": len(authorized),
        "numeric_target_execution_performed": False,
        "records": records,
    }


def validate_target_design_implementations(impl: dict[str, Any], requests: dict[str, Any], adj: dict[str, Any]) -> dict[str, Any]:
    reqmap = {(str(r.get("window_id")), str(r.get("domain"))): r for r in requests.get("requests") or []}
    amap = {(str(r.get("window_id")), str(r.get("domain"))): r for r in adj.get("records") or []}
    records = []
    for r in impl.get("records") or []:
        key = (str(r.get("window_id")), str(r.get("domain")))
        req = reqmap.get(key) or {}; a = amap.get(key) or {}
        checks = {
            "parent_implementation_nonnumeric": r.get("authority_definition_implemented") is True and r.get("numeric_target_materialization_authorized_in_r428") is False,
            "r427_definition_authorized": a.get("authority_definition_implementation_authorized_in_r428") is True,
            "scientific_construct_exact": r.get("scientific_construct") == req.get("scientific_construct") and bool(r.get("scientific_construct")),
            "canonical_observables_exact": list(r.get("required_canonical_observables") or []) == list(req.get("required_canonical_observables") or []),
            "unit_families_exact": list(r.get("permitted_unit_families") or []) == list(req.get("permitted_unit_families") or []),
            "governance_exact": list(r.get("required_governance") or []) == list(req.get("required_governance") or []),
            "forbidden_shortcuts_exact": list(r.get("forbidden_shortcuts") or []) == list(req.get("forbidden_shortcuts") or []),
            "external_engine_target_definition_forbidden": r.get("external_engine_result_may_define_target") is False,
            "result_selected_transform_forbidden": r.get("result_selected_transform_authorized") is False,
        }
        ok = all(checks.values())
        records.append({
            "window_id": r.get("window_id"), "domain": r.get("domain"), "checks": checks,
            "implementation_validation_pass": ok,
            "validation_status": "VALIDATED_PRE_RESULT_NONNUMERIC_TARGET_AUTHORITY_DEFINITION" if ok else "DEFERRED_TARGET_AUTHORITY_IMPLEMENTATION_VALIDATION_FAILURE",
            "numeric_target_materialization_authorized_in_r429": False,
            "next_priority": "R430_TARGET_DESIGN_OBSERVABLE_BINDING_IMPLEMENTATION" if ok else "REPAIR_R429_TARGET_DESIGN_IMPLEMENTATION",
        })
    passed = sum(bool(r.get("implementation_validation_pass")) for r in records)
    return {
        "stage": STAGE,
        "status": "R429_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_COMPLETE" if len(records) == 12 and passed == 12 else BLOCKED,
        "record_count": len(records), "validated_count": passed, "deferred_count": len(records) - passed,
        "numeric_target_materialization_authorized_count": 0, "records": records,
    }


def authorize_semantic_repair(parent: dict[str, Any]) -> dict[str, Any]:
    records = []
    for r in parent.get("records") or []:
        ready = bool(r.get("review_preflight_ready") and r.get("allowed_operation") == "PRIMARY_MAPPING_ELIGIBILITY_REVIEW_ONLY")
        records.append({
            "window_id": r.get("window_id"), "domain": r.get("domain"), "review_authorized_for_r430": ready,
            "allowed_operation": "PRIMARY_MAPPING_ELIGIBILITY_REVIEW_ONLY",
            "numeric_value_change_authorized": False, "mapping_class_upgrade_authorized": False,
            "readjudication_authorized_in_r429": False,
        })
    return {"stage": STAGE, "status": "R429_SEMANTIC_REPAIR_EXECUTION_AUTHORIZATION_COMPLETE" if len(records) == 1 and records[0].get("review_authorized_for_r430") else BLOCKED, "record_count": len(records), "review_authorized_count": sum(bool(r.get("review_authorized_for_r430")) for r in records), "records": records}


def authorize_j14(root: Path, parent: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    v = validate_authority_inputs(root)
    algo = cfg.get("j14_authority_algorithm") or {}
    required_algo = {
        "name": AUTHORITY_ALGORITHM,
        "initialization": "MAXIMUM_ENTROPY_OVER_AGE_MATCHED_CANONICAL_LAND_SUPPORT",
        "persistence": "KEEP_PRIOR_DEME_CELL_WHILE_CANONICALLY_ACCESSIBLE",
        "support_loss": "MINIMUM_GRID_DISTANCE_REMAP_TO_ACCESSIBLE_SUPPORT",
        "deme_fission": "DETERMINISTIC_FARTHEST_POINT_ADDITION_ON_ACCESSIBLE_SUPPORT",
        "deme_contraction": "DETERMINISTIC_LOWEST_SEPARATION_REMOVAL",
        "population_allocation": "MAXIMUM_ENTROPY_EQUAL_SHARE_OF_R327_EFFECTIVE_POPULATION",
        "future_spatial_anchor_usage": "FORBIDDEN_IN_CONSTRUCTION",
        "external_engine_usage": "FORBIDDEN",
    }
    checks = {
        "parent_preflight_ready": parent.get("implementation_preflight_ready") is True,
        "authority_inputs_static_valid": v.get("ready") is True,
        "algorithm_spec_exact_and_pre_result": all(algo.get(k) == val for k, val in required_algo.items()),
        "r42_j14_mutation_forbidden": parent.get("r42_j14_mutation_authorized") is False and cfg.get("r42_j14_mutation_forbidden") is True,
        "geonomics_not_authorized_in_r429": cfg.get("geonomics_execution_authorized") is False,
        "future_spatial_anchor_forbidden": cfg.get("j14_replay_construction_may_not_use_r315_or_r328_spatial_coordinates") is True,
    }
    authorized = all(checks.values())
    return {
        "stage": STAGE,
        "status": "R429_GEONOMICS_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION_COMPLETE" if authorized else BLOCKED,
        "job_id": "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "authority_algorithm": AUTHORITY_ALGORITHM,
        "checks": checks,
        "input_validation": v,
        "input_hash_freeze": v.get("hashes") or {},
        "canonical_spatial_replay_execution_authorized_in_r430": authorized,
        "canonical_spatial_replay_execution_performed_in_r429": False,
        "geonomics_execution_authorized_in_r429": False,
        "geonomics_execution_authorized_in_r430_by_r429": False,
        "r42_j14_mutation_authorized": False,
        "construction_may_use_r315_or_r328_coordinates": False,
        "construction_may_use_external_engine_results": False,
        "post_execution_r328_comparison_may_be_diagnostic_only": True,
        "next_priority": "R430_J14_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_EXECUTION" if authorized else "REPAIR_R429_J14_AUTHORITY_STATIC_INPUT_OR_ALGORITHM_SPEC",
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    ps = load(root / PSELECT) if (root / PSELECT).exists() else {}
    pd = load(root / PDESIGN) if (root / PDESIGN).exists() else {}
    psem = load(root / PSEM) if (root / PSEM).exists() else {}
    pj14 = load(root / PJ14) if (root / PJ14).exists() else {}
    pplan = load(root / PPLAN) if (root / PPLAN).exists() else {}
    r426d = load(root / R426DESIGN) if (root / R426DESIGN).exists() else {}
    r427d = load(root / R427DESIGN) if (root / R427DESIGN).exists() else {}

    closure = build_schemaless_closure(root, ps)
    selectors = freeze_selector_authorities(ps, closure, cfg)
    design = validate_target_design_implementations(pd, r426d, r427d)
    semantic = authorize_semantic_repair(psem)
    j14 = authorize_j14(root, pj14, cfg)

    checks = [
        Check("parent_r428_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r428_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_r428_r1_applied", pseal.get("repair_revision") == "R4.28-R1", pseal.get("repair_revision")),
        Check("parent_next_action_matches_r429", pa.get("next_action") == PARENT_NEXT, pa.get("next_action")),
        Check("parent_selector_terminal_44", pa.get("selector_authority_preflight_terminal_count") == 44, pa.get("selector_authority_preflight_terminal_count")),
        Check("parent_selector_ready_38", pa.get("selector_authority_preflight_ready_count") == 38, pa.get("selector_authority_preflight_ready_count")),
        Check("parent_selector_schemaless_deferred_6", pa.get("selector_authority_preflight_deferred_no_exact_inventory_count") == 6, pa.get("selector_authority_preflight_deferred_no_exact_inventory_count")),
        Check("parent_zero_selector_authorizations", pa.get("selector_authorized_count") == 0, pa.get("selector_authorized_count")),
        Check("parent_target_design_12", pa.get("target_design_authority_definition_implemented_count") == 12, pa.get("target_design_authority_definition_implemented_count")),
        Check("parent_semantic_repair_one", pa.get("semantic_repair_preflight_ready_count") == 1, pa.get("semantic_repair_preflight_ready_count")),
        Check("parent_j14_preflight_ready", pa.get("j14_spatial_replay_authority_preflight_ready") is True, pa.get("j14_spatial_replay_authority_preflight_ready")),
        Check("parent_plan_frozen", pplan.get("status") == "R428_SELECTOR_DESIGN_AND_J14_PREFLIGHT_FROZEN", pplan.get("status")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_PRE_TARGET_NUMERIC_MATERIALIZATION_AND_PRE_J14_SPATIAL_AUTHORITY_EXECUTION", cfg.get("policy_freeze")),
        Check("schemaless_exact_six_terminally_closed_or_gap_frozen", closure.get("record_count") == 6 and closure.get("source_integrity_blocked_count") == 0 and int(closure.get("inventory_recovered_count") or 0) + int(closure.get("authority_gap_frozen_count") or 0) == 6, {"recovered": closure.get("inventory_recovered_count"), "gap": closure.get("authority_gap_frozen_count"), "blocked": closure.get("source_integrity_blocked_count")}),
        Check("selector_freeze_exact_44_terminal", selectors.get("record_count") == 44 and int(selectors.get("selector_authorized_count") or 0) + int(selectors.get("selector_deferred_count") or 0) == 44, {"authorized": selectors.get("selector_authorized_count"), "deferred": selectors.get("selector_deferred_count")}),
        Check("selector_authorizations_pre_result_exact_only", all(r.get("selector_choice_used_external_results") is False and r.get("fuzzy_matching_used") is False and r.get("synonym_fallback_used") is False for r in selectors.get("records") or [])),
        Check("authorized_selectors_have_exact_frozen_rule", all((not r.get("selector_authorized")) or (r.get("frozen_selector") and r.get("frozen_transform_id") and r.get("frozen_authority_class") in {"DIRECT_CANDIDATE", "NORMALIZABLE_CANDIDATE"}) for r in selectors.get("records") or [])),
        Check("target_design_all_12_implementations_validated", design.get("record_count") == 12 and design.get("validated_count") == 12, {"records": design.get("record_count"), "validated": design.get("validated_count")}),
        Check("target_design_numeric_materialization_still_zero", design.get("numeric_target_materialization_authorized_count") == 0, design.get("numeric_target_materialization_authorized_count")),
        Check("semantic_repair_one_review_authorized_for_r430", semantic.get("record_count") == 1 and semantic.get("review_authorized_count") == 1, semantic.get("review_authorized_count")),
        Check("j14_spatial_authority_execution_authorized_for_r430", j14.get("canonical_spatial_replay_execution_authorized_in_r430") is True, j14.get("checks")),
        Check("j14_input_hash_freeze_nonempty", len(j14.get("input_hash_freeze") or {}) >= 7, sorted((j14.get("input_hash_freeze") or {}).keys())),
        Check("j14_geonomics_execution_still_not_authorized", j14.get("geonomics_execution_authorized_in_r429") is False and j14.get("geonomics_execution_authorized_in_r430_by_r429") is False),
        Check("j14_future_spatial_anchor_construction_forbidden", j14.get("construction_may_use_r315_or_r328_coordinates") is False),
        Check("active_deferred_p2_two_preserved", pa.get("active_deferred_p2_cell_count") == 2, pa.get("active_deferred_p2_cell_count")),
        Check("proxy_context_only_two_preserved", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("p3_backlog_six_preserved", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("no_engine_execution", cfg.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", cfg.get("target_numeric_execution_performed") is False),
        Check("no_canonical_spatial_replay_execution", cfg.get("canonical_spatial_replay_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
    ]
    ok = all(c.passed for c in checks)
    plan = {
        "stage": STAGE,
        "status": "R429_SELECTOR_DESIGN_AND_J14_EXECUTION_AUTHORIZATION_FROZEN" if ok else BLOCKED,
        "selector_numeric_materialization_authorized_cell_count": selectors.get("numeric_target_materialization_authorized_for_r430_count"),
        "selector_deferred_cell_count": selectors.get("selector_deferred_count"),
        "schemaless_inventory_recovered_count": closure.get("inventory_recovered_count"),
        "schemaless_authority_gap_frozen_count": closure.get("authority_gap_frozen_count"),
        "target_design_validated_count": design.get("validated_count"),
        "semantic_repair_review_authorized_count": semantic.get("review_authorized_count"),
        "j14_spatial_replay_execution_authorized_in_r430": j14.get("canonical_spatial_replay_execution_authorized_in_r430"),
        "geonomics_execution_authorized_in_r430": False,
        "r42_j14_mutation_authorized": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R429_SELECTOR_DESIGN_OR_J14_AUTHORIZATION",
    }
    out = {
        "stage": STAGE, "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks],
        "selector_authorized_count": selectors.get("selector_authorized_count"),
        "selector_deferred_count": selectors.get("selector_deferred_count"),
        "schemaless_inventory_recovered_count": closure.get("inventory_recovered_count"),
        "schemaless_authority_gap_frozen_count": closure.get("authority_gap_frozen_count"),
        "target_design_validated_count": design.get("validated_count"),
        "semantic_repair_review_authorized_count": semantic.get("review_authorized_count"),
        "j14_spatial_replay_execution_authorized_in_r430": j14.get("canonical_spatial_replay_execution_authorized_in_r430"),
        "active_deferred_p2_cell_count": 2, "proxy_context_only_count": 2, "p3_backlog_cell_count": 6,
        "engine_execution_performed": False, "target_numeric_execution_performed": False, "canonical_spatial_replay_execution_performed": False,
        "readjudication_performed": False, "canonical_state_changed": False,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_29_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE.json", closure)
    write(root / OUT / "R4_29_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE.json", selectors)
    write(root / OUT / "R4_29_TARGET_DESIGN_IMPLEMENTATION_VALIDATION.json", design)
    write(root / OUT / "R4_29_SEMANTIC_REPAIR_EXECUTION_AUTHORIZATION.json", semantic)
    write(root / OUT / "R4_29_GEONOMICS_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION.json", j14)
    write(root / OUT / "R4_29_R430_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_29_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    parent = load(root / PSEAL) if (root / PSEAL).exists() else {}
    audit = load(root / OUT / "R4_29_INTEGRATED_AUDIT.json") if (root / OUT / "R4_29_INTEGRATED_AUDIT.json").exists() else {}
    sel = load(root / OUT / "R4_29_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE.json") if (root / OUT / "R4_29_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE.json").exists() else {}
    clo = load(root / OUT / "R4_29_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE.json") if (root / OUT / "R4_29_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE.json").exists() else {}
    des = load(root / OUT / "R4_29_TARGET_DESIGN_IMPLEMENTATION_VALIDATION.json") if (root / OUT / "R4_29_TARGET_DESIGN_IMPLEMENTATION_VALIDATION.json").exists() else {}
    sem = load(root / OUT / "R4_29_SEMANTIC_REPAIR_EXECUTION_AUTHORIZATION.json") if (root / OUT / "R4_29_SEMANTIC_REPAIR_EXECUTION_AUTHORIZATION.json").exists() else {}
    j14 = load(root / OUT / "R4_29_GEONOMICS_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION.json") if (root / OUT / "R4_29_GEONOMICS_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION.json").exists() else {}
    plan = load(root / OUT / "R4_29_R430_EXECUTION_PLAN.json") if (root / OUT / "R4_29_R430_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r428_r1_sealed", parent.get("status") == PARENT_SEALED and parent.get("repair_revision") == "R4.28-R1", {"status": parent.get("status"), "revision": parent.get("repair_revision")}),
        Check("r429_complete", audit.get("status") == COMPLETE, audit.get("status")),
        Check("r429_zero_process_failures", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("selector_44_terminally_disposed", sel.get("record_count") == 44 and int(sel.get("selector_authorized_count") or 0) + int(sel.get("selector_deferred_count") or 0) == 44, {"authorized": sel.get("selector_authorized_count"), "deferred": sel.get("selector_deferred_count")}),
        Check("schemaless_six_terminally_closed_or_gap_frozen", clo.get("record_count") == 6 and clo.get("source_integrity_blocked_count") == 0 and int(clo.get("inventory_recovered_count") or 0) + int(clo.get("authority_gap_frozen_count") or 0) == 6, {"recovered": clo.get("inventory_recovered_count"), "gap": clo.get("authority_gap_frozen_count"), "blocked": clo.get("source_integrity_blocked_count")}),
        Check("target_design_12_validated", des.get("record_count") == 12 and des.get("validated_count") == 12, des.get("validated_count")),
        Check("semantic_repair_one_authorized", sem.get("record_count") == 1 and sem.get("review_authorized_count") == 1, sem.get("review_authorized_count")),
        Check("j14_spatial_replay_execution_authorized_for_r430", j14.get("canonical_spatial_replay_execution_authorized_in_r430") is True, j14.get("checks")),
        Check("geonomics_execution_still_not_authorized", j14.get("geonomics_execution_authorized_in_r429") is False and j14.get("geonomics_execution_authorized_in_r430_by_r429") is False),
        Check("r430_plan_frozen", plan.get("status") == "R429_SELECTOR_DESIGN_AND_J14_EXECUTION_AUTHORIZATION_FROZEN", plan.get("status")),
        Check("deferred_p2_two", plan.get("active_deferred_p2_cell_count") == 2, plan.get("active_deferred_p2_cell_count")),
        Check("proxy_context_two", plan.get("proxy_context_only_count") == 2, plan.get("proxy_context_only_count")),
        Check("p3_backlog_six", plan.get("p3_backlog_cell_count") == 6, plan.get("p3_backlog_cell_count")),
        Check("no_engine_execution", audit.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", audit.get("target_numeric_execution_performed") is False),
        Check("no_spatial_replay_execution", audit.get("canonical_spatial_replay_execution_performed") is False),
        Check("no_readjudication", audit.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", audit.get("canonical_state_changed") is False),
        Check("next_action_present", audit.get("next_action") == NEXT, audit.get("next_action")),
    ]
    verdict = "SEALED" if all(c.passed for c in checks) else "BLOCKED"
    out = {
        "stage": STAGE,
        "audit": "FINAL_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_AND_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION",
        "status": SEALED if verdict == "SEALED" else BLOCKED,
        "verdict": verdict,
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks],
        "summary": {
            "selector_authorized_count": sel.get("selector_authorized_count"), "selector_deferred_count": sel.get("selector_deferred_count"),
            "schemaless_inventory_recovered_count": clo.get("inventory_recovered_count"), "schemaless_authority_gap_frozen_count": clo.get("authority_gap_frozen_count"),
            "target_design_validated_count": des.get("validated_count"), "semantic_repair_review_authorized_count": sem.get("review_authorized_count"),
            "j14_spatial_replay_execution_authorized_in_r430": j14.get("canonical_spatial_replay_execution_authorized_in_r430"),
            "geonomics_execution_authorized": False, "active_deferred_p2_cell_count": 2, "proxy_context_only_count": 2, "p3_backlog_cell_count": 6,
            "engine_execution_performed": False, "target_numeric_execution_performed": False, "canonical_spatial_replay_execution_performed": False,
            "readjudication_performed": False, "canonical_state_changed": False, "canonical_parameter_change_authorized": False,
            "deep_biological_coupling": False, "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
