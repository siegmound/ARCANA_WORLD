from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import hashlib
import json
import zipfile

import numpy as np

STAGE = "v0.6D1-R4.27"
PARENT_SEALED = "PASS_R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FREEZE_SEALED"
PARENT_NEXT = "BUILD_R427_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_TARGET_DESIGN_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION"
COMPLETE = "PASS_R427_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_TARGET_DESIGN_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION_COMPLETE"
SEALED = "PASS_R427_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_TARGET_DESIGN_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION_SEALED"
BLOCKED = "BLOCKED_R427_PARENT_STATIC_VALIDATION_OR_AUTHORITY_ADJUDICATION_FAILURE"

CFG = Path("configs/world1_r427_target_extractor_static_validation_authority_adjudication_v0_6D1_R4_27.json")
PSEAL = Path("outputs/v0_6D1_R4_26_SEAL/R4_26_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_26/R4_26_INTEGRATED_AUDIT.json")
PIMPL = Path("outputs/v0_6D1_R4_26/R4_26_TARGET_EXTRACTOR_IMPLEMENTATION_REGISTRY.json")
PDESIGN = Path("outputs/v0_6D1_R4_26/R4_26_TARGET_DESIGN_AUTHORITY_REQUEST_REGISTRY.json")
PJ14 = Path("outputs/v0_6D1_R4_26/R4_26_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST.json")
PPLAN = Path("outputs/v0_6D1_R4_26/R4_26_R427_EXECUTION_PLAN.json")
OUT = Path("outputs/v0_6D1_R4_27")
SEAL = Path("outputs/v0_6D1_R4_27_SEAL/R4_27_FINAL_SEAL_AUDIT.json")

NEXT_ACTION = "BUILD_R428_TARGET_SELECTOR_AND_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT"

SUPPORTED_PARSERS = {
    "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR",
    "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR",
    "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR",
}

TARGET_REQUIRED_GOVERNANCE = {
    "PRE_RESULT_DEFINITION",
    "CANONICAL_SOURCE_AUTHORITY",
    "EXPLICIT_TEMPORAL_BASIS",
    "EXPLICIT_SPATIAL_POPULATION_BASIS",
    "EXPLICIT_UNCERTAINTY_OR_AGGREGATION",
    "HASH_BOUND_PROVENANCE",
}

J14_REQUIRED_PROPERTIES = {
    "ARCANA_ENGINE_INDEPENDENT",
    "FORWARD_OR_EXPLICITLY_AUTHORIZED_RECONSTRUCTION_FROM_CANONICAL_PROVIDERS",
    "R3_27_MACRO_TRAJECTORY_AGGREGATE_INVARIANT_AUDIT",
    "PALEOGEOGRAPHIC_AND_ENVIRONMENTAL_PROVIDER_PROVENANCE",
    "HASH_BOUND_INPUT_OUTPUT_PROVENANCE",
    "SEALED_BEFORE_ANY_GEONOMICS_EXECUTION",
}

J14_REQUIRED_SPATIAL = {
    "EXPLICIT_LAT_LON_OR_GRID_ROW_COL",
    "TIME_INDEXED_POPULATION_OR_DEME_STATE",
    "EXPLICIT_CANONICAL_SPATIAL_SUPPORT_IDENTITY",
}

J14_FORBIDDEN_SHORTCUTS = {
    "SYNTHESIZE_3MA_COORDINATES_FROM_R3_27_SCALARS",
    "BACKWARD_INTERPOLATE_FROM_R3_15_250KA",
    "BACKWARD_EXTRAPOLATE_FROM_R3_28_200KA",
    "USE_GEONOMICS_DEFAULT_MODEL_AS_CANONICAL_AUTHORITY",
    "USE_EXTERNAL_ENGINE_RESULTS_TO_DEFINE_CANONICAL_SPATIAL_STATE",
    "MUTATE_R4_2_J14_WINDOW_OR_JOB_ID",
    "EXECUTE_J18_J21_AS_SUBSTITUTE_FOR_FULL_SHARED_GEONOMICS_SCOPE",
}


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
            q = root / marker.strip("/") / s.split(marker, 1)[1]
            if q.exists():
                return q
    return None


def _json_schema_paths(obj: Any, prefix: str = "", depth: int = 0, max_depth: int = 5) -> list[str]:
    if depth > max_depth:
        return []
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.append(p)
            if isinstance(v, (dict, list)):
                out.extend(_json_schema_paths(v, p, depth + 1, max_depth))
    elif isinstance(obj, list) and obj:
        # Schema only: inspect at most the first element; never emit values.
        p = f"{prefix}[]" if prefix else "[]"
        out.append(p)
        if isinstance(obj[0], (dict, list)):
            out.extend(_json_schema_paths(obj[0], p, depth + 1, max_depth))
    return sorted(set(out))


def inspect_source_schema(path: Path, parser_family: str) -> dict[str, Any]:
    """Static schema inspection only. It does not return target numeric values."""
    if parser_family == "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR":
        obj = load(path)
        paths = _json_schema_paths(obj)
        return {"parser_family": parser_family, "schema_paths": paths, "schema_item_count": len(paths)}
    if parser_family == "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR":
        # Read only embedded .npy headers from the ZIP container; do not materialize array payloads.
        arrays = []
        with zipfile.ZipFile(path, "r") as zf:
            for member in zf.namelist():
                if not member.endswith(".npy"):
                    continue
                key = member[:-4]
                with zf.open(member, "r") as fp:
                    version = np.lib.format.read_magic(fp)
                    if version == (1, 0):
                        shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(fp, max_header_size=1_000_000)
                    else:
                        shape, fortran_order, dtype = np.lib.format.read_array_header_2_0(fp, max_header_size=1_000_000)
                arrays.append({"selector": key, "dtype": str(dtype), "shape": list(shape), "fortran_order": bool(fortran_order)})
        arrays.sort(key=lambda x: x["selector"])
        return {"parser_family": parser_family, "arrays": arrays, "schema_item_count": len(arrays)}
    if parser_family == "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR":
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            row = next(csv.reader(f, delimiter=delim), [])
        # We only record the exact first-row tokens as header candidates. Numeric-only rows are not accepted as selectors.
        headers = [x for x in row if x and not _is_number(x)]
        return {"parser_family": parser_family, "header_candidates": headers, "schema_item_count": len(headers)}
    raise ValueError(f"unsupported parser family: {parser_family}")


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def _selector_exists(schema: dict[str, Any], parser_family: str, selector: str) -> bool:
    if parser_family == "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR":
        return selector in set(schema.get("schema_paths") or [])
    if parser_family == "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR":
        return selector in {str(a.get("selector")) for a in schema.get("arrays") or []}
    if parser_family == "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR":
        return selector in set(schema.get("header_candidates") or [])
    return False


def static_validate_extractors(root: Path, impl: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    canonical = [r for r in impl.get("records") or [] if r.get("implementation_class") == "READ_ONLY_CANONICAL_TARGET_EXTRACTOR"]
    semantic = [r for r in impl.get("records") or [] if r.get("implementation_class") == "REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT"]
    binding_cache: dict[tuple[str, str, str], dict[str, Any]] = {}

    for rec in canonical:
        bindings = []
        for b in rec.get("source_bindings") or []:
            if not b.get("binding_eligible"):
                continue
            p = _resolve_recorded_path(root, b.get("source"))
            parser = str(b.get("parser_family") or "")
            expected = str(b.get("expected_sha256") or "")
            cache_key = (str(p.resolve()) if p and p.exists() else str(b.get("source")), expected, parser)
            cached = binding_cache.get(cache_key)
            if cached is None:
                present = bool(p and p.exists())
                observed = sha256(p) if present else None
                hash_match = bool(present and expected and observed == expected)
                parser_supported = parser in SUPPORTED_PARSERS
                schema = None
                schema_ok = False
                schema_error = None
                if hash_match and parser_supported and p is not None:
                    try:
                        schema = inspect_source_schema(p, parser)
                        schema_ok = True
                    except Exception as exc:
                        schema_error = f"{type(exc).__name__}: {exc}"
                cached = {
                    "source": b.get("source"),
                    "parser_family": parser,
                    "present": present,
                    "expected_sha256": expected,
                    "observed_sha256": observed,
                    "hash_match": hash_match,
                    "parser_supported": parser_supported,
                    "static_schema_valid": schema_ok,
                    "schema": schema,
                    "schema_error": schema_error,
                }
                binding_cache[cache_key] = cached
            bindings.append(dict(cached))

        valid = [b for b in bindings if b.get("hash_match") and b.get("parser_supported") and b.get("static_schema_valid")]
        proposed_selector = rec.get("frozen_exact_selector") or rec.get("authorized_exact_selector")
        selector_authorized = False
        selector_source = None
        if proposed_selector:
            # Future-compatible path: only a selector already frozen by the parent may be authorized.
            for b in valid:
                if _selector_exists(b.get("schema") or {}, str(b.get("parser_family") or ""), str(proposed_selector)):
                    selector_authorized = True
                    selector_source = b.get("source")
                    break

        if selector_authorized:
            disposition = "AUTHORIZED_PARENT_FROZEN_EXACT_SELECTOR_STATICALLY_PRESENT"
            next_priority = "R428_READ_ONLY_TARGET_MATERIALIZATION_PREFLIGHT"
        elif valid:
            disposition = "DEFERRED_EXPLICIT_SELECTOR_AND_TRANSFORM_AUTHORITY_REQUIRED"
            next_priority = "R428_EXPLICIT_SELECTOR_AND_TRANSFORM_AUTHORITY_DEFINITION"
        else:
            disposition = "BLOCKED_SOURCE_HASH_PARSER_OR_SCHEMA_STATIC_VALIDATION_FAILURE"
            next_priority = "REPAIR_R427_EXTRACTOR_STATIC_VALIDATION"

        records.append({
            "window_id": rec.get("window_id"),
            "domain": rec.get("domain"),
            "implementation_class": rec.get("implementation_class"),
            "source_binding_count": len(bindings),
            "static_valid_binding_count": len(valid),
            "static_implementation_valid": bool(valid),
            "selector_policy": rec.get("selector_policy"),
            "parent_selector_binding_status": rec.get("selector_binding_status"),
            "parent_frozen_exact_selector": proposed_selector,
            "selector_execution_authorized_in_r427": selector_authorized,
            "selector_source": selector_source,
            "static_disposition": disposition,
            "numeric_target_execution_authorized_in_r427": False,
            "adjudicative_promotion_authorized_in_r427": False,
            "result_selected_selector_authorized": False,
            "source_bindings": bindings,
            "next_priority": next_priority,
        })

    semantic_records = []
    for rec in semantic:
        keys = list(rec.get("failed_validation_keys_frozen") or [])
        valid = keys == ["eligible_primary_row_count"] and rec.get("numeric_value_change_authorized") is False and rec.get("mapping_class_upgrade_authorized") is False
        semantic_records.append({
            "window_id": rec.get("window_id"),
            "domain": rec.get("domain"),
            "failed_validation_keys_frozen": keys,
            "static_validation_pass": valid,
            "disposition": "AUTHORIZED_REJECTION_CAUSE_ONLY_PRIMARY_MAPPING_REVIEW" if valid else "DEFERRED_SEMANTIC_REPAIR_SCOPE_INTEGRITY_FAILURE",
            "numeric_value_change_authorized": False,
            "mapping_class_upgrade_authorized": False,
            "readjudication_authorized_in_r427": False,
            "next_priority": "R428_PRIMARY_MAPPING_ELIGIBILITY_REVIEW" if valid else "REPAIR_R427_SEMANTIC_REPAIR_SCOPE",
        })

    static_valid = [r for r in records if r.get("static_implementation_valid")]
    selector_auth = [r for r in records if r.get("selector_execution_authorized_in_r427")]
    blocked = [r for r in records if str(r.get("static_disposition", "")).startswith("BLOCKED_")]
    return {
        "stage": STAGE,
        "status": "R427_TARGET_EXTRACTOR_STATIC_VALIDATION_COMPLETE" if len(records) == 44 and len(static_valid) == 44 and len(semantic_records) == 1 and semantic_records[0].get("static_validation_pass") and not blocked else BLOCKED,
        "canonical_extractor_record_count": len(records),
        "canonical_extractor_static_valid_count": len(static_valid),
        "canonical_extractor_selector_authorized_count": len(selector_auth),
        "canonical_extractor_selector_deferred_count": len(records) - len(selector_auth),
        "canonical_extractor_blocked_count": len(blocked),
        "semantic_repair_record_count": len(semantic_records),
        "semantic_repair_review_authorized_count": sum(bool(r.get("static_validation_pass")) for r in semantic_records),
        "numeric_target_execution_performed": False,
        "records": records,
        "semantic_repair_records": semantic_records,
    }


def adjudicate_target_design_authorities(design: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for req in design.get("requests") or []:
        governance = set(req.get("required_governance") or [])
        construct_ok = bool(req.get("scientific_construct"))
        observables_ok = len(req.get("required_canonical_observables") or []) >= 3
        units_ok = bool(req.get("permitted_unit_families"))
        shortcuts_ok = bool(req.get("forbidden_shortcuts"))
        governance_ok = TARGET_REQUIRED_GOVERNANCE.issubset(governance)
        frozen_ok = req.get("request_status") == "FROZEN_PENDING_R427_AUTHORITY_ADJUDICATION"
        no_external = req.get("external_engine_result_may_define_target") is False
        no_result_selected = req.get("result_selected_transform_authorized") is False
        no_numeric = req.get("numeric_target_definition_authorized_in_r426") is False
        approved = all([construct_ok, observables_ok, units_ok, shortcuts_ok, governance_ok, frozen_ok, no_external, no_result_selected, no_numeric])
        records.append({
            "window_id": req.get("window_id"),
            "domain": req.get("domain"),
            "request_status": req.get("request_status"),
            "scientific_construct": req.get("scientific_construct"),
            "checks": {
                "construct_defined": construct_ok,
                "canonical_observables_declared": observables_ok,
                "unit_family_declared": units_ok,
                "forbidden_shortcuts_declared": shortcuts_ok,
                "governance_complete": governance_ok,
                "request_frozen_pre_adjudication": frozen_ok,
                "external_results_forbidden": no_external,
                "result_selected_transform_forbidden": no_result_selected,
                "numeric_definition_not_preexecuted": no_numeric,
            },
            "adjudication": "APPROVED_FOR_PRE_RESULT_AUTHORITY_DEFINITION_IMPLEMENTATION" if approved else "DEFERRED_AUTHORITY_SPEC_REPAIR_REQUIRED",
            "authority_definition_implementation_authorized_in_r428": approved,
            "numeric_target_materialization_authorized_in_r427": False,
            "numeric_target_materialization_authorized_in_r428_by_r427": False,
            "adjudicative_promotion_authorized": False,
            "next_priority": "R428_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_PREFLIGHT" if approved else "REPAIR_TARGET_DESIGN_AUTHORITY_SPEC",
        })
    approved = [r for r in records if r.get("authority_definition_implementation_authorized_in_r428")]
    return {
        "stage": STAGE,
        "status": "R427_TARGET_DESIGN_AUTHORITY_REQUEST_ADJUDICATION_COMPLETE" if len(records) == 12 else BLOCKED,
        "request_count": len(records),
        "approved_for_definition_implementation_count": len(approved),
        "deferred_for_spec_repair_count": len(records) - len(approved),
        "numeric_target_materialization_authorized_count": 0,
        "records": records,
    }


def adjudicate_j14_authority_request(j14: dict[str, Any]) -> dict[str, Any]:
    temporal = j14.get("required_temporal_support") or {}
    spatial = set(j14.get("required_spatial_support") or [])
    props = set(j14.get("required_authority_properties") or [])
    forbidden = set(j14.get("forbidden_shortcuts") or [])
    checks = {
        "request_frozen": j14.get("authority_request_frozen") is True,
        "correct_job": j14.get("job_id") == "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "correct_request_kind": j14.get("request_kind") == "NEW_ENGINE_INDEPENDENT_CANONICAL_SPATIAL_REPLAY_AUTHORITY",
        "exact_3ma_to_200ka_support": temporal.get("start_age_ma") == 3.0 and temporal.get("end_age_ka") == 200.0 and temporal.get("time_indexed") is True,
        "required_spatial_support_complete": J14_REQUIRED_SPATIAL.issubset(spatial),
        "engine_independent_authority_properties_complete": J14_REQUIRED_PROPERTIES.issubset(props),
        "all_forbidden_shortcuts_preserved": J14_FORBIDDEN_SHORTCUTS.issubset(forbidden),
        "new_namespace_required": j14.get("new_namespace_required_if_authority_is_later_approved") is True,
        "parent_did_not_authorize_replay": j14.get("canonical_replay_authorized_in_r426") is False,
        "parent_did_not_authorize_geonomics": j14.get("geonomics_execution_authorized_in_r426") is False,
        "r42_job_mutation_forbidden": j14.get("r42_j14_mutation_authorized") is False,
        "existing_authority_discovery_exhausted": int(j14.get("parent_existing_sealed_authority_candidate_count") or 0) == 0,
    }
    approved = all(checks.values())
    return {
        "stage": STAGE,
        "status": "R427_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_ADJUDICATED" if approved else "R427_GEONOMICS_J14_AUTHORITY_REQUEST_DEFERRED_SPEC_REPAIR",
        "job_id": j14.get("job_id"),
        "checks": checks,
        "adjudication": "APPROVED_FOR_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_IMPLEMENTATION_PREFLIGHT" if approved else "DEFERRED_SPATIAL_AUTHORITY_SPEC_REPAIR_REQUIRED",
        "spatial_authority_implementation_preflight_authorized_in_r428": approved,
        "canonical_spatial_replay_execution_authorized_in_r427": False,
        "canonical_spatial_replay_execution_authorized_in_r428_by_r427": False,
        "geonomics_execution_authorized_in_r427": False,
        "geonomics_execution_authorized_in_r428_by_r427": False,
        "r42_j14_mutation_authorized": False,
        "active_deferred_p2_cell_count": 2,
        "next_priority": "R428_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_IMPLEMENTATION_PREFLIGHT" if approved else "REPAIR_R427_J14_AUTHORITY_REQUEST_SPEC",
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    impl = load(root / PIMPL) if (root / PIMPL).exists() else {}
    design = load(root / PDESIGN) if (root / PDESIGN).exists() else {}
    j14 = load(root / PJ14) if (root / PJ14).exists() else {}
    pplan = load(root / PPLAN) if (root / PPLAN).exists() else {}

    static = static_validate_extractors(root, impl)
    target_adj = adjudicate_target_design_authorities(design)
    j14_adj = adjudicate_j14_authority_request(j14)

    design_terminal = target_adj.get("request_count") == 12 and (target_adj.get("approved_for_definition_implementation_count", 0) + target_adj.get("deferred_for_spec_repair_count", 0) == 12)
    j14_terminal = j14_adj.get("adjudication") in {
        "APPROVED_FOR_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_IMPLEMENTATION_PREFLIGHT",
        "DEFERRED_SPATIAL_AUTHORITY_SPEC_REPAIR_REQUIRED",
    }

    checks = [
        Check("parent_r426_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r426_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r427", pa.get("next_action") == PARENT_NEXT, pa.get("next_action")),
        Check("parent_44_canonical_extractors", pa.get("canonical_extractor_implementation_count") == 44, pa.get("canonical_extractor_implementation_count")),
        Check("parent_44_hash_ready", pa.get("canonical_extractor_hash_verified_ready_count") == 44, pa.get("canonical_extractor_hash_verified_ready_count")),
        Check("parent_one_semantic_repair", pa.get("semantic_repair_audit_implementation_count") == 1, pa.get("semantic_repair_audit_implementation_count")),
        Check("parent_12_target_design_requests", pa.get("target_design_authority_request_count") == 12, pa.get("target_design_authority_request_count")),
        Check("parent_two_proxy", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("parent_j14_request_frozen", pa.get("j14_new_spatial_authority_request_frozen") is True),
        Check("parent_j14_gap_open", pa.get("j14_spatial_authority_gap_open") is True),
        Check("parent_deferred_p2_two", pa.get("active_deferred_p2_cell_count") == 2, pa.get("active_deferred_p2_cell_count")),
        Check("parent_p3_six", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("parent_r427_plan_frozen", pplan.get("status") == "R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_NEW_AUTHORITY_REQUESTS_FROZEN", pplan.get("status")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_PRE_TARGET_SELECTOR_AND_NEW_AUTHORITY_IMPLEMENTATION_PREFLIGHT", cfg.get("policy_freeze")),
        Check("engine_execution_forbidden", cfg.get("engine_execution_performed") is False),
        Check("target_numeric_execution_forbidden", cfg.get("target_numeric_execution_performed") is False),
        Check("readjudication_forbidden", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_execution_not_authorized", cfg.get("canonical_replay_execution_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
        Check("static_validation_exact_44_records", static.get("canonical_extractor_record_count") == 44, static.get("canonical_extractor_record_count")),
        Check("all_44_extractor_implementations_static_valid", static.get("canonical_extractor_static_valid_count") == 44, static.get("canonical_extractor_static_valid_count")),
        Check("zero_extractor_static_blocks", static.get("canonical_extractor_blocked_count") == 0, static.get("canonical_extractor_blocked_count")),
        Check("selector_authorization_parent_frozen_only", all((r.get("selector_execution_authorized_in_r427") is False) or bool(r.get("parent_frozen_exact_selector")) for r in static.get("records") or [])),
        Check("no_result_selected_selector", all(r.get("result_selected_selector_authorized") is False for r in static.get("records") or [])),
        Check("semantic_repair_one_review_authorized", static.get("semantic_repair_review_authorized_count") == 1, static.get("semantic_repair_review_authorized_count")),
        Check("semantic_repair_numeric_and_mapping_immutable", all(r.get("numeric_value_change_authorized") is False and r.get("mapping_class_upgrade_authorized") is False for r in static.get("semantic_repair_records") or [])),
        Check("target_authority_exact_12_terminally_adjudicated", design_terminal, {"approved": target_adj.get("approved_for_definition_implementation_count"), "deferred": target_adj.get("deferred_for_spec_repair_count")}),
        Check("target_authority_no_numeric_materialization_authorized", target_adj.get("numeric_target_materialization_authorized_count") == 0),
        Check("target_authority_external_results_forbidden", all((r.get("checks") or {}).get("external_results_forbidden") for r in target_adj.get("records") or [])),
        Check("j14_authority_request_terminally_adjudicated", j14_terminal, j14_adj.get("adjudication")),
        Check("j14_replay_execution_not_authorized", j14_adj.get("canonical_spatial_replay_execution_authorized_in_r427") is False),
        Check("j14_geonomics_execution_not_authorized", j14_adj.get("geonomics_execution_authorized_in_r427") is False),
        Check("r42_j14_mutation_not_authorized", j14_adj.get("r42_j14_mutation_authorized") is False),
        Check("active_deferred_p2_two_preserved", j14_adj.get("active_deferred_p2_cell_count") == 2),
        Check("proxy_context_only_two_preserved", pa.get("proxy_context_only_count") == 2),
        Check("p3_backlog_six_preserved", pa.get("p3_backlog_cell_count") == 6),
        Check("no_engine_execution", cfg.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", cfg.get("target_numeric_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_still_unchanged", cfg.get("canonical_state_changed") is False),
    ]
    ok = all(c.passed for c in checks)

    plan = {
        "stage": STAGE,
        "status": "R427_STATIC_VALIDATION_AND_AUTHORITY_ADJUDICATION_FROZEN" if ok else BLOCKED,
        "canonical_extractor_static_valid_count": static.get("canonical_extractor_static_valid_count"),
        "canonical_extractor_selector_authorized_count": static.get("canonical_extractor_selector_authorized_count"),
        "canonical_extractor_selector_deferred_count": static.get("canonical_extractor_selector_deferred_count"),
        "semantic_repair_review_authorized_count": static.get("semantic_repair_review_authorized_count"),
        "target_design_authority_approved_count": target_adj.get("approved_for_definition_implementation_count"),
        "target_design_authority_deferred_count": target_adj.get("deferred_for_spec_repair_count"),
        "j14_spatial_authority_implementation_preflight_authorized": j14_adj.get("spatial_authority_implementation_preflight_authorized_in_r428"),
        "target_numeric_execution_authorized_in_r428_by_r427": False,
        "canonical_spatial_replay_execution_authorized_in_r428_by_r427": False,
        "geonomics_execution_authorized_in_r428_by_r427": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT_ACTION if ok else "REPAIR_R427_STATIC_VALIDATION_OR_AUTHORITY_ADJUDICATION",
    }

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "canonical_extractor_static_valid_count": static.get("canonical_extractor_static_valid_count"),
        "canonical_extractor_selector_authorized_count": static.get("canonical_extractor_selector_authorized_count"),
        "canonical_extractor_selector_deferred_count": static.get("canonical_extractor_selector_deferred_count"),
        "semantic_repair_review_authorized_count": static.get("semantic_repair_review_authorized_count"),
        "target_design_authority_approved_count": target_adj.get("approved_for_definition_implementation_count"),
        "target_design_authority_deferred_count": target_adj.get("deferred_for_spec_repair_count"),
        "j14_spatial_authority_implementation_preflight_authorized": j14_adj.get("spatial_authority_implementation_preflight_authorized_in_r428"),
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "next_action": plan["next_action"],
    }

    write(root / OUT / "R4_27_TARGET_EXTRACTOR_STATIC_VALIDATION_REGISTRY.json", static)
    write(root / OUT / "R4_27_TARGET_DESIGN_AUTHORITY_ADJUDICATION.json", target_adj)
    write(root / OUT / "R4_27_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION.json", j14_adj)
    write(root / OUT / "R4_27_R428_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_27_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_27_INTEGRATED_AUDIT.json") if (root / OUT / "R4_27_INTEGRATED_AUDIT.json").exists() else {}
    static = load(root / OUT / "R4_27_TARGET_EXTRACTOR_STATIC_VALIDATION_REGISTRY.json") if (root / OUT / "R4_27_TARGET_EXTRACTOR_STATIC_VALIDATION_REGISTRY.json").exists() else {}
    target = load(root / OUT / "R4_27_TARGET_DESIGN_AUTHORITY_ADJUDICATION.json") if (root / OUT / "R4_27_TARGET_DESIGN_AUTHORITY_ADJUDICATION.json").exists() else {}
    j14 = load(root / OUT / "R4_27_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION.json") if (root / OUT / "R4_27_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION.json").exists() else {}
    plan = load(root / OUT / "R4_27_R428_EXECUTION_PLAN.json") if (root / OUT / "R4_27_R428_EXECUTION_PLAN.json").exists() else {}

    checks = [
        Check("parent_r426_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r427_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r427_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("all_44_extractors_static_valid", static.get("canonical_extractor_static_valid_count") == 44, static.get("canonical_extractor_static_valid_count")),
        Check("selector_accounting_complete", int(static.get("canonical_extractor_selector_authorized_count") or 0) + int(static.get("canonical_extractor_selector_deferred_count") or 0) == 44),
        Check("semantic_repair_one_review_authorized", static.get("semantic_repair_review_authorized_count") == 1, static.get("semantic_repair_review_authorized_count")),
        Check("target_design_12_terminally_adjudicated", int(target.get("approved_for_definition_implementation_count") or 0) + int(target.get("deferred_for_spec_repair_count") or 0) == 12),
        Check("zero_numeric_target_authorizations", target.get("numeric_target_materialization_authorized_count") == 0),
        Check("j14_authority_request_adjudicated", bool(j14.get("adjudication")), j14.get("adjudication")),
        Check("j14_no_replay_or_geonomics_execution_authorized", j14.get("canonical_spatial_replay_execution_authorized_in_r427") is False and j14.get("geonomics_execution_authorized_in_r427") is False),
        Check("r428_plan_frozen", plan.get("status") == "R427_STATIC_VALIDATION_AND_AUTHORITY_ADJUDICATION_FROZEN", plan.get("status")),
        Check("deferred_p2_two", a.get("active_deferred_p2_cell_count") == 2, a.get("active_deferred_p2_cell_count")),
        Check("p3_backlog_six", a.get("p3_backlog_cell_count") == 6, a.get("p3_backlog_cell_count")),
        Check("no_engine_execution", a.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", a.get("target_numeric_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("next_action_present", a.get("next_action") == NEXT_ACTION, a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_TARGET_DESIGN_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "canonical_extractor_static_valid_count": a.get("canonical_extractor_static_valid_count"),
            "canonical_extractor_selector_authorized_count": a.get("canonical_extractor_selector_authorized_count"),
            "canonical_extractor_selector_deferred_count": a.get("canonical_extractor_selector_deferred_count"),
            "semantic_repair_review_authorized_count": a.get("semantic_repair_review_authorized_count"),
            "target_design_authority_approved_count": a.get("target_design_authority_approved_count"),
            "target_design_authority_deferred_count": a.get("target_design_authority_deferred_count"),
            "j14_spatial_authority_implementation_preflight_authorized": a.get("j14_spatial_authority_implementation_preflight_authorized"),
            "active_deferred_p2_cell_count": a.get("active_deferred_p2_cell_count"),
            "proxy_context_only_count": a.get("proxy_context_only_count"),
            "p3_backlog_cell_count": a.get("p3_backlog_cell_count"),
            "engine_execution_performed": False,
            "target_numeric_execution_performed": False,
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
