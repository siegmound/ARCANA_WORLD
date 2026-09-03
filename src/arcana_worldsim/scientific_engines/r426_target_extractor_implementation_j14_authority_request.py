from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import hashlib
import json

import numpy as np

STAGE = "v0.6D1-R4.26"
PARENT_SEALED = "PASS_R425_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY_SEALED"
PARENT_NEXT = "BUILD_R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FREEZE"
COMPLETE = "PASS_R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FREEZE_COMPLETE"
SEALED = "PASS_R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FREEZE_SEALED"
BLOCKED = "BLOCKED_R426_PARENT_SOURCE_INTEGRITY_OR_AUTHORITY_REQUEST_FREEZE_FAILURE"

CFG = Path("configs/world1_r426_target_extractor_implementation_j14_authority_request_v0_6D1_R4_26.json")
PSEAL = Path("outputs/v0_6D1_R4_25_SEAL/R4_25_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_25/R4_25_INTEGRATED_AUDIT.json")
PPREFLIGHT = Path("outputs/v0_6D1_R4_25/R4_25_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT.json")
PDISC = Path("outputs/v0_6D1_R4_25/R4_25_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY.json")
PPLAN = Path("outputs/v0_6D1_R4_25/R4_25_R426_EXECUTION_PLAN.json")
OUT = Path("outputs/v0_6D1_R4_26")
SEAL = Path("outputs/v0_6D1_R4_26_SEAL/R4_26_FINAL_SEAL_AUDIT.json")

CANONICAL_READY = "READY_FOR_READ_ONLY_CANONICAL_EXTRACTOR_IMPLEMENTATION"
SEMANTIC_READY = "READY_FOR_REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT"
DESIGN_REQUIRED = "DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED"
PROXY = "CONTEXT_ONLY_PROXY_PRESERVED"

NEXT_ACTION = "BUILD_R427_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_TARGET_DESIGN_GEONOMICS_J14_AUTHORITY_REQUEST_ADJUDICATION"


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


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


# Generic exact-selector readers are implemented here but are NOT invoked on ARCANA targets in R4.26.
# They deliberately have no fuzzy matching, no domain synonyms and no fallback selector discovery.
def extract_exact_json(path: Path, selector: str) -> Any:
    obj = load(path)
    cur: Any = obj
    for token in selector.split("."):
        if not isinstance(cur, dict) or token not in cur:
            raise KeyError(selector)
        cur = cur[token]
    return cur


def extract_exact_npz(path: Path, selector: str) -> np.ndarray:
    with np.load(path, allow_pickle=False) as z:
        if selector not in z.files:
            raise KeyError(selector)
        return np.asarray(z[selector])


def extract_exact_tabular(path: Path, selector: str, delimiter: str) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames or selector not in reader.fieldnames:
            raise KeyError(selector)
        return [row[selector] for row in reader]


def extract_exact(path: Path, parser_family: str, selector: str) -> Any:
    if parser_family == "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR":
        return extract_exact_json(path, selector)
    if parser_family == "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR":
        return extract_exact_npz(path, selector)
    if parser_family == "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR":
        return extract_exact_tabular(path, selector, "\t" if path.suffix.lower() == ".tsv" else ",")
    raise ValueError(f"unsupported parser family: {parser_family}")


def build_extractor_implementation_registry(root: Path, preflight: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for rec in preflight.get("records") or []:
        disp = str(rec.get("preflight_disposition") or "")
        base = {
            "window_id": rec.get("window_id"),
            "domain": rec.get("domain"),
            "parent_preflight_disposition": disp,
            "numeric_target_execution_authorized_in_r426": False,
            "adjudicative_promotion_authorized_in_r426": False,
            "result_selected_selector_authorized": False,
            "external_engine_result_may_define_target": False,
        }
        if disp == CANONICAL_READY:
            bindings: list[dict[str, Any]] = []
            for src in rec.get("candidate_sources") or []:
                if not src.get("eligible"):
                    continue
                p = _resolve_recorded_path(root, src.get("source"))
                expected = str(src.get("sha256") or "")
                if p is None or not p.exists():
                    bindings.append({
                        "source": src.get("source"), "present": False, "hash_match": False,
                        "expected_sha256": expected, "observed_sha256": None,
                        "parser_family": src.get("parser_family"), "binding_eligible": False,
                        "reason": "SOURCE_MISSING_AFTER_R425_FREEZE",
                    })
                    continue
                observed = sha256(p)
                bindings.append({
                    "source": _rel(root, p), "present": True, "hash_match": observed == expected,
                    "expected_sha256": expected, "observed_sha256": observed,
                    "parser_family": src.get("parser_family"),
                    "binding_eligible": bool(observed == expected and src.get("parser_family")),
                    "reason": "R425_HASH_BOUND_SOURCE_VERIFIED" if observed == expected else "SOURCE_HASH_DRIFT_AFTER_R425_FREEZE",
                })
            verified = [b for b in bindings if b.get("binding_eligible")]
            base.update({
                "implementation_class": "READ_ONLY_CANONICAL_TARGET_EXTRACTOR",
                "implementation_status": "IMPLEMENTED_PARSER_AND_PROVENANCE_BINDING_SELECTOR_PENDING_R427_STATIC_VALIDATION" if verified else "BLOCKED_NO_HASH_VERIFIED_R425_SOURCE_BINDING",
                "implementation_ready": bool(verified),
                "hash_verified_source_binding_count": len(verified),
                "source_bindings": bindings,
                "selector_binding_status": "PENDING_EXPLICIT_R427_STATIC_SELECTOR_BINDING",
                "selector_policy": "EXACT_SELECTOR_ONLY_NO_FUZZY_NO_FALLBACK",
                "allowed_parser_families": sorted({b.get("parser_family") for b in verified if b.get("parser_family")}),
                "numeric_materialization_performed": False,
                "next_priority": "R427_STATIC_SELECTOR_AND_SEMANTIC_VALIDATION",
            })
        elif disp == SEMANTIC_READY:
            failed = list(rec.get("failed_validation_keys") or [])
            base.update({
                "implementation_class": "REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT",
                "implementation_status": "IMPLEMENTED_FAILED_GATE_ONLY_AUDIT_SPEC" if failed else "BLOCKED_MISSING_FROZEN_REJECTION_CAUSE",
                "implementation_ready": bool(failed),
                "failed_validation_keys_frozen": failed,
                "failed_validation_fields_frozen": rec.get("failed_validation_fields"),
                "numeric_value_change_authorized": False,
                "mapping_class_upgrade_authorized": False,
                "allowed_repair_scope": failed,
                "next_priority": "R427_REJECTION_CAUSE_ONLY_STATIC_VALIDATION",
            })
        elif disp == DESIGN_REQUIRED:
            base.update({
                "implementation_class": "NEW_TARGET_DESIGN_AUTHORITY_REQUIRED",
                "implementation_status": "DEFERRED_TO_FROZEN_AUTHORITY_REQUEST",
                "implementation_ready": False,
                "next_priority": "R427_TARGET_DESIGN_AUTHORITY_REQUEST_ADJUDICATION",
            })
        elif disp == PROXY:
            base.update({
                "implementation_class": "CONTEXT_ONLY_PROXY",
                "implementation_status": "PRESERVED_NONADJUDICATIVE",
                "implementation_ready": False,
                "next_priority": "P4_PRESERVE_NONADJUDICATIVE",
            })
        else:
            base.update({
                "implementation_class": "UNKNOWN_FAIL_CLOSED",
                "implementation_status": "BLOCKED_UNKNOWN_PARENT_PREFLIGHT_DISPOSITION",
                "implementation_ready": False,
                "next_priority": "REPAIR_R426_UNKNOWN_PARENT_DISPOSITION",
            })
        records.append(base)

    canonical = [r for r in records if r.get("implementation_class") == "READ_ONLY_CANONICAL_TARGET_EXTRACTOR"]
    semantic = [r for r in records if r.get("implementation_class") == "REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT"]
    design = [r for r in records if r.get("implementation_class") == "NEW_TARGET_DESIGN_AUTHORITY_REQUIRED"]
    proxy = [r for r in records if r.get("implementation_class") == "CONTEXT_ONLY_PROXY"]
    unknown = [r for r in records if r.get("implementation_class") == "UNKNOWN_FAIL_CLOSED"]
    canonical_ready = [r for r in canonical if r.get("implementation_ready")]
    return {
        "stage": STAGE,
        "status": "R426_TARGET_EXTRACTOR_IMPLEMENTATION_REGISTRY_COMPLETE" if len(records) == 59 and len(canonical) == 44 and len(canonical_ready) == 44 and len(semantic) == 1 and len(design) == 12 and len(proxy) == 2 and not unknown else BLOCKED,
        "record_count": len(records),
        "canonical_extractor_implementation_count": len(canonical),
        "canonical_extractor_hash_verified_ready_count": len(canonical_ready),
        "semantic_repair_audit_implementation_count": len(semantic),
        "new_target_design_authority_deferred_count": len(design),
        "context_only_proxy_count": len(proxy),
        "unknown_count": len(unknown),
        "numeric_target_execution_performed": False,
        "records": records,
    }


TARGET_DESIGN_DEFINITIONS = {
    "range_shift_rate": {
        "scientific_construct": "TIME_RESOLVED_DISPLACEMENT_RATE_OF_CANONICAL_OCCUPIED_RANGE_SUPPORT",
        "required_canonical_observables": ["TIME_INDEXED_SPATIAL_OCCUPANCY_SUPPORT", "EXPLICIT_DISTANCE_OR_GRID_METRIC", "WINDOW_TIME_BASIS"],
        "permitted_unit_families": ["DISTANCE_PER_TIME", "GRID_DISTANCE_PER_TIME", "NORMALIZED_SUPPORT_DISPLACEMENT_PER_TIME"],
        "forbidden_shortcuts": ["INFER_FROM_SINGLE_SNAPSHOT", "DEFINE_FROM_EXTERNAL_ENGINE_OUTPUT", "RESULT_SELECTED_DISTANCE_METRIC"],
    },
    "founder_persistence": {
        "scientific_construct": "PERSISTENCE_OF_EXPLICITLY_IDENTIFIED_FOUNDER_DERIVED_LINEAGE_OR_POPULATION_SUPPORT_ACROSS_WINDOW",
        "required_canonical_observables": ["FOUNDER_IDENTITY_OR_COHORT_BINDING", "DESCENDANT_OR_SURVIVAL_SUPPORT", "WINDOW_START_END_OR_TIME_SERIES"],
        "permitted_unit_families": ["FRACTION", "PROBABILITY", "BINARY_WITH_EXPLICIT_AGGREGATION", "NORMALIZED_DESCENDANT_SUPPORT"],
        "forbidden_shortcuts": ["EQUATE_TOTAL_POPULATION_WITH_FOUNDER_PERSISTENCE", "DEFINE_FROM_EXTERNAL_ENGINE_OUTPUT", "RESULT_SELECTED_FOUNDER_LABEL"],
    },
}


def build_target_design_authority_requests(preflight: dict[str, Any]) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    for rec in preflight.get("records") or []:
        if rec.get("preflight_disposition") != DESIGN_REQUIRED:
            continue
        domain = str(rec.get("domain") or "")
        spec = TARGET_DESIGN_DEFINITIONS.get(domain)
        requests.append({
            "window_id": rec.get("window_id"),
            "domain": domain,
            "request_status": "FROZEN_PENDING_R427_AUTHORITY_ADJUDICATION" if spec else "BLOCKED_NO_DOMAIN_AUTHORITY_TEMPLATE",
            "authority_execution_authorized_in_r426": False,
            "numeric_target_definition_authorized_in_r426": False,
            "external_engine_result_may_define_target": False,
            "result_selected_transform_authorized": False,
            **(spec or {}),
            "required_governance": [
                "PRE_RESULT_DEFINITION",
                "CANONICAL_SOURCE_AUTHORITY",
                "EXPLICIT_TEMPORAL_BASIS",
                "EXPLICIT_SPATIAL_POPULATION_BASIS",
                "EXPLICIT_UNCERTAINTY_OR_AGGREGATION",
                "HASH_BOUND_PROVENANCE",
            ],
        })
    return {
        "stage": STAGE,
        "status": "R426_TARGET_DESIGN_AUTHORITY_REQUESTS_FROZEN" if len(requests) == 12 and all(r.get("request_status") == "FROZEN_PENDING_R427_AUTHORITY_ADJUDICATION" for r in requests) else BLOCKED,
        "request_count": len(requests),
        "authority_execution_performed": False,
        "numeric_target_definition_performed": False,
        "requests": requests,
    }


def build_j14_new_spatial_authority_request(discovery: dict[str, Any]) -> dict[str, Any]:
    gap = bool(discovery.get("j14_spatial_authority_gap_open_after_discovery"))
    none_found = not bool(discovery.get("existing_sealed_authority_found")) and int(discovery.get("sealed_existing_authority_candidate_count") or 0) == 0
    frozen = bool(gap and none_found)
    return {
        "stage": STAGE,
        "status": "R426_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FROZEN" if frozen else BLOCKED,
        "job_id": "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "window_id": "SAPIENT_3MA_TO_200KA",
        "request_kind": "NEW_ENGINE_INDEPENDENT_CANONICAL_SPATIAL_REPLAY_AUTHORITY",
        "parent_discovery_candidate_file_count": discovery.get("candidate_file_count"),
        "parent_exact_3ma_spatial_candidate_count": discovery.get("exact_3ma_spatial_candidate_count"),
        "parent_existing_sealed_authority_candidate_count": discovery.get("sealed_existing_authority_candidate_count"),
        "authority_request_frozen": frozen,
        "authority_execution_authorized_in_r426": False,
        "canonical_replay_authorized_in_r426": False,
        "geonomics_execution_authorized_in_r426": False,
        "r42_j14_mutation_authorized": False,
        "required_temporal_support": {"start_age_ma": 3.0, "end_age_ka": 200.0, "time_indexed": True},
        "required_spatial_support": [
            "EXPLICIT_LAT_LON_OR_GRID_ROW_COL",
            "TIME_INDEXED_POPULATION_OR_DEME_STATE",
            "EXPLICIT_CANONICAL_SPATIAL_SUPPORT_IDENTITY",
        ],
        "required_authority_properties": [
            "ARCANA_ENGINE_INDEPENDENT",
            "FORWARD_OR_EXPLICITLY_AUTHORIZED_RECONSTRUCTION_FROM_CANONICAL_PROVIDERS",
            "R3_27_MACRO_TRAJECTORY_AGGREGATE_INVARIANT_AUDIT",
            "PALEOGEOGRAPHIC_AND_ENVIRONMENTAL_PROVIDER_PROVENANCE",
            "HASH_BOUND_INPUT_OUTPUT_PROVENANCE",
            "SEALED_BEFORE_ANY_GEONOMICS_EXECUTION",
        ],
        "aggregate_invariants_to_preserve_or_explain": [
            "EFFECTIVE_POPULATION",
            "DEME_COUNT",
            "ECOLOGICAL_BREADTH",
            "DISPERSAL_CAPACITY",
        ],
        "forbidden_shortcuts": [
            "SYNTHESIZE_3MA_COORDINATES_FROM_R3_27_SCALARS",
            "BACKWARD_INTERPOLATE_FROM_R3_15_250KA",
            "BACKWARD_EXTRAPOLATE_FROM_R3_28_200KA",
            "USE_GEONOMICS_DEFAULT_MODEL_AS_CANONICAL_AUTHORITY",
            "USE_EXTERNAL_ENGINE_RESULTS_TO_DEFINE_CANONICAL_SPATIAL_STATE",
            "MUTATE_R4_2_J14_WINDOW_OR_JOB_ID",
            "EXECUTE_J18_J21_AS_SUBSTITUTE_FOR_FULL_SHARED_GEONOMICS_SCOPE",
        ],
        "new_namespace_required_if_authority_is_later_approved": True,
        "next_priority": "R427_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_ADJUDICATION",
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    ppref = load(root / PPREFLIGHT) if (root / PPREFLIGHT).exists() else {}
    pdisc = load(root / PDISC) if (root / PDISC).exists() else {}
    pplan = load(root / PPLAN) if (root / PPLAN).exists() else {}

    impl = build_extractor_implementation_registry(root, ppref)
    design = build_target_design_authority_requests(ppref)
    j14 = build_j14_new_spatial_authority_request(pdisc)

    impl_records = impl.get("records") or []
    canonical = [r for r in impl_records if r.get("implementation_class") == "READ_ONLY_CANONICAL_TARGET_EXTRACTOR"]
    semantic = [r for r in impl_records if r.get("implementation_class") == "REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT"]

    checks = [
        Check("parent_r425_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r425_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r426", pa.get("next_action") == PARENT_NEXT, pa.get("next_action")),
        Check("parent_target_active_57", pa.get("target_active_repair_count") == 57, pa.get("target_active_repair_count")),
        Check("parent_target_implementation_ready_45", pa.get("target_implementation_ready_count") == 45, pa.get("target_implementation_ready_count")),
        Check("parent_target_canonical_extractor_ready_44", pa.get("target_canonical_extractor_ready_count") == 44, pa.get("target_canonical_extractor_ready_count")),
        Check("parent_target_semantic_repair_ready_1", pa.get("target_semantic_repair_audit_ready_count") == 1, pa.get("target_semantic_repair_audit_ready_count")),
        Check("parent_target_new_design_12", pa.get("target_new_design_authority_required_count") == 12, pa.get("target_new_design_authority_required_count")),
        Check("parent_proxy_two", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("parent_zero_source_deferred", pa.get("target_source_or_authority_deferred_count") == 0, pa.get("target_source_or_authority_deferred_count")),
        Check("parent_j14_no_existing_authority", pa.get("j14_existing_sealed_authority_found") is False, pa.get("j14_existing_sealed_authority_found")),
        Check("parent_j14_gap_open", pa.get("j14_spatial_authority_gap_open_after_discovery") is True),
        Check("parent_plan_frozen", pplan.get("status") == "R425_TARGET_PREFLIGHT_AND_J14_AUTHORITY_DISCOVERY_FROZEN", pplan.get("status")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_PRE_TARGET_EXTRACTOR_STATIC_VALIDATION_AND_NEW_AUTHORITY_ADJUDICATION", cfg.get("policy_freeze")),
        Check("engine_execution_forbidden", cfg.get("engine_execution_performed") is False),
        Check("target_numeric_execution_forbidden", cfg.get("target_numeric_execution_performed") is False),
        Check("readjudication_forbidden", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
        Check("implementation_registry_exact_59", impl.get("record_count") == 59, impl.get("record_count")),
        Check("canonical_extractor_implementations_exact_44", impl.get("canonical_extractor_implementation_count") == 44, impl.get("canonical_extractor_implementation_count")),
        Check("all_44_canonical_extractors_have_hash_verified_source_binding", impl.get("canonical_extractor_hash_verified_ready_count") == 44, impl.get("canonical_extractor_hash_verified_ready_count")),
        Check("canonical_extractors_exact_selector_only", all(r.get("selector_policy") == "EXACT_SELECTOR_ONLY_NO_FUZZY_NO_FALLBACK" for r in canonical)),
        Check("canonical_extractors_no_selector_bound_or_executed", all(r.get("selector_binding_status") == "PENDING_EXPLICIT_R427_STATIC_SELECTOR_BINDING" and r.get("numeric_materialization_performed") is False for r in canonical)),
        Check("semantic_repair_implementation_exact_one", impl.get("semantic_repair_audit_implementation_count") == 1, impl.get("semantic_repair_audit_implementation_count")),
        Check("semantic_repair_only_frozen_failed_gate_and_numeric_immutable", len(semantic) == 1 and semantic[0].get("failed_validation_keys_frozen") == ["eligible_primary_row_count"] and semantic[0].get("numeric_value_change_authorized") is False),
        Check("target_design_authority_requests_exact_12", design.get("request_count") == 12, design.get("request_count")),
        Check("target_design_requests_known_domain_templates", all(r.get("domain") in TARGET_DESIGN_DEFINITIONS and r.get("request_status") == "FROZEN_PENDING_R427_AUTHORITY_ADJUDICATION" for r in design.get("requests") or [])),
        Check("target_design_requests_no_numeric_definition", design.get("numeric_target_definition_performed") is False),
        Check("j14_new_spatial_authority_request_frozen", j14.get("authority_request_frozen") is True, j14.get("status")),
        Check("j14_request_exact_3ma_to_200ka_time_support", (j14.get("required_temporal_support") or {}).get("start_age_ma") == 3.0 and (j14.get("required_temporal_support") or {}).get("end_age_ka") == 200.0),
        Check("j14_request_engine_independent_and_shortcuts_forbidden", "ARCANA_ENGINE_INDEPENDENT" in (j14.get("required_authority_properties") or []) and len(j14.get("forbidden_shortcuts") or []) >= 6),
        Check("geonomics_execution_not_authorized", j14.get("geonomics_execution_authorized_in_r426") is False),
        Check("r42_j14_mutation_not_authorized", j14.get("r42_j14_mutation_authorized") is False),
        Check("active_deferred_p2_two_preserved", pa.get("active_deferred_p2_cell_count") == 2, pa.get("active_deferred_p2_cell_count")),
        Check("p3_backlog_six_preserved", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("no_engine_execution", cfg.get("engine_execution_performed") is False),
        Check("no_target_numeric_execution", cfg.get("target_numeric_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_still_unchanged", cfg.get("canonical_state_changed") is False),
    ]
    ok = all(c.passed for c in checks)
    status = COMPLETE if ok else BLOCKED
    plan = {
        "stage": STAGE,
        "status": "R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_NEW_AUTHORITY_REQUESTS_FROZEN" if ok else BLOCKED,
        "canonical_extractor_implementation_count": impl.get("canonical_extractor_implementation_count"),
        "canonical_extractor_hash_verified_ready_count": impl.get("canonical_extractor_hash_verified_ready_count"),
        "semantic_repair_audit_implementation_count": impl.get("semantic_repair_audit_implementation_count"),
        "target_design_authority_request_count": design.get("request_count"),
        "proxy_context_only_count": impl.get("context_only_proxy_count"),
        "target_numeric_execution_authorized_in_r427_by_r426": False,
        "j14_new_spatial_authority_request_frozen": j14.get("authority_request_frozen"),
        "j14_spatial_authority_execution_authorized_in_r427_by_r426": False,
        "geonomics_execution_authorized_in_r427_by_r426": False,
        "active_deferred_p2_cell_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT_ACTION if ok else "REPAIR_R426_SOURCE_INTEGRITY_OR_AUTHORITY_REQUEST_FREEZE",
    }
    out = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "canonical_extractor_implementation_count": impl.get("canonical_extractor_implementation_count"),
        "canonical_extractor_hash_verified_ready_count": impl.get("canonical_extractor_hash_verified_ready_count"),
        "semantic_repair_audit_implementation_count": impl.get("semantic_repair_audit_implementation_count"),
        "target_design_authority_request_count": design.get("request_count"),
        "proxy_context_only_count": impl.get("context_only_proxy_count"),
        "j14_new_spatial_authority_request_frozen": j14.get("authority_request_frozen"),
        "j14_spatial_authority_gap_open": True,
        "active_deferred_p2_cell_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_26_TARGET_EXTRACTOR_IMPLEMENTATION_REGISTRY.json", impl)
    write(root / OUT / "R4_26_TARGET_DESIGN_AUTHORITY_REQUEST_REGISTRY.json", design)
    write(root / OUT / "R4_26_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST.json", j14)
    write(root / OUT / "R4_26_R427_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_26_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_26_INTEGRATED_AUDIT.json") if (root / OUT / "R4_26_INTEGRATED_AUDIT.json").exists() else {}
    impl = load(root / OUT / "R4_26_TARGET_EXTRACTOR_IMPLEMENTATION_REGISTRY.json") if (root / OUT / "R4_26_TARGET_EXTRACTOR_IMPLEMENTATION_REGISTRY.json").exists() else {}
    design = load(root / OUT / "R4_26_TARGET_DESIGN_AUTHORITY_REQUEST_REGISTRY.json") if (root / OUT / "R4_26_TARGET_DESIGN_AUTHORITY_REQUEST_REGISTRY.json").exists() else {}
    j14 = load(root / OUT / "R4_26_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST.json") if (root / OUT / "R4_26_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST.json").exists() else {}
    plan = load(root / OUT / "R4_26_R427_EXECUTION_PLAN.json") if (root / OUT / "R4_26_R427_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r425_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r426_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r426_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("canonical_extractors_44_implemented_and_hash_ready", impl.get("canonical_extractor_implementation_count") == 44 and impl.get("canonical_extractor_hash_verified_ready_count") == 44, {"implemented": impl.get("canonical_extractor_implementation_count"), "ready": impl.get("canonical_extractor_hash_verified_ready_count")}),
        Check("semantic_repair_one_implemented", impl.get("semantic_repair_audit_implementation_count") == 1, impl.get("semantic_repair_audit_implementation_count")),
        Check("target_design_authority_requests_12_frozen", design.get("request_count") == 12 and design.get("status") == "R426_TARGET_DESIGN_AUTHORITY_REQUESTS_FROZEN", design.get("request_count")),
        Check("j14_new_spatial_authority_request_frozen", j14.get("status") == "R426_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FROZEN", j14.get("status")),
        Check("no_numeric_target_execution", a.get("target_numeric_execution_performed") is False),
        Check("geonomics_not_executed_or_authorized", j14.get("geonomics_execution_authorized_in_r426") is False),
        Check("r427_plan_frozen", plan.get("status") == "R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_NEW_AUTHORITY_REQUESTS_FROZEN", plan.get("status")),
        Check("deferred_p2_two", a.get("active_deferred_p2_cell_count") == 2, a.get("active_deferred_p2_cell_count")),
        Check("p3_backlog_six", a.get("p3_backlog_cell_count") == 6, a.get("p3_backlog_cell_count")),
        Check("no_engine_execution", a.get("engine_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("next_action_present", a.get("next_action") == NEXT_ACTION, a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FREEZE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "canonical_extractor_implementation_count": a.get("canonical_extractor_implementation_count"),
            "canonical_extractor_hash_verified_ready_count": a.get("canonical_extractor_hash_verified_ready_count"),
            "semantic_repair_audit_implementation_count": a.get("semantic_repair_audit_implementation_count"),
            "target_design_authority_request_count": a.get("target_design_authority_request_count"),
            "proxy_context_only_count": a.get("proxy_context_only_count"),
            "j14_new_spatial_authority_request_frozen": a.get("j14_new_spatial_authority_request_frozen"),
            "j14_spatial_authority_gap_open": a.get("j14_spatial_authority_gap_open"),
            "active_deferred_p2_cell_count": a.get("active_deferred_p2_cell_count"),
            "p3_backlog_cell_count": a.get("p3_backlog_cell_count"),
            "engine_execution_performed": False,
            "target_numeric_execution_performed": False,
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
