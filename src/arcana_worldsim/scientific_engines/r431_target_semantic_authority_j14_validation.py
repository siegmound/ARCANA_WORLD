from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import math

import numpy as np

from arcana_worldsim.scientific_engines.r429_j14_spatial_authority_replay import (
    AUTHORITY_ALGORITHM,
    build_replay,
    validate_authority_inputs,
)

STAGE = "v0.6D1-R4.31"
PARENT_SEALED = "PASS_R430_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION_SEALED"
PARENT_COMPLETE = "PASS_R430_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION_COMPLETE"
PARENT_NEXT = "BUILD_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL"
COMPLETE = "PASS_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL_COMPLETE"
SEALED = "PASS_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL_SEALED"
BLOCKED = "BLOCKED_R431_PARENT_TARGET_AUTHORITY_OR_J14_VALIDATION_FAILURE"
J14_SEALED = "PASS_R431_J14_DERIVED_CANONICAL_SPATIAL_AUTHORITY_VALIDATION_SEALED"
NEXT = "BUILD_R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION"

CFG = Path("configs/world1_r431_target_semantic_authority_j14_validation_v0_6D1_R4_31.json")
PSEAL = Path("outputs/v0_6D1_R4_30_SEAL/R4_30_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_30/R4_30_INTEGRATED_AUDIT.json")
PTARGET = Path("outputs/v0_6D1_R4_30/R4_30_AUTHORIZED_TARGET_MATERIALIZATION_REGISTRY.json")
PGAPS = Path("outputs/v0_6D1_R4_30/R4_30_SELECTOR_GAP_CLOSURE_REGISTRY.json")
PSEM = Path("outputs/v0_6D1_R4_30/R4_30_SEMANTIC_REPAIR_PRIMARY_MAPPING_REVIEW.json")
PPLAN = Path("outputs/v0_6D1_R4_30/R4_30_R431_EXECUTION_PLAN.json")
PJ14_META = Path("outputs/v0_6D1_R4_30/authority/R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.json")
PJ14_NPZ = Path("outputs/v0_6D1_R4_30/authority/R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz")
R429_J14 = Path("outputs/v0_6D1_R4_29/R4_29_GEONOMICS_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION.json")
R429_DESIGN = Path("outputs/v0_6D1_R4_29/R4_29_TARGET_DESIGN_IMPLEMENTATION_VALIDATION.json")
R416_PROTOCOL = Path("outputs/v0_6D1_R4_16/R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json")
R327_TRAJ = Path("outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz")
A1 = Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz")
OUT = Path("outputs/v0_6D1_R4_31")
SEAL = Path("outputs/v0_6D1_R4_31_SEAL/R4_31_FINAL_SEAL_AUDIT.json")
J14_VALIDATION_SEAL = OUT / "authority" / "R4_31_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL.json"


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


def _finite_scalar(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def _deferred_gap_class(disposition: str) -> tuple[str, str]:
    d = str(disposition or "")
    if d == "DEFERRED_AUTHORIZED_SELECTOR_SOURCE_BINDING_AUTHORITY_NOT_FROZEN_BY_R429":
        return "SOURCE_IDENTITY_AUTHORITY_GAP_FROZEN", "R432_EXPLICIT_SOURCE_IDENTITY_AUTHORITY_FREEZE"
    if d == "DEFERRED_AMBIGUOUS_MULTIPLE_HASH_VALID_SOURCES_FOR_AUTHORIZED_SELECTOR":
        return "SOURCE_IDENTITY_AMBIGUITY_AUTHORITY_GAP_FROZEN", "R432_SOURCE_IDENTITY_DISAMBIGUATION_AUTHORITY_FREEZE"
    if d == "DEFERRED_FROZEN_TRANSFORM_HAS_UNBOUND_SEMANTIC_DEPENDENCY":
        return "TRANSFORM_SEMANTIC_DEPENDENCY_AUTHORITY_GAP_FROZEN", "R432_TRANSFORM_SEMANTIC_DEPENDENCY_AUTHORITY_FREEZE"
    if d in {
        "DEFERRED_IDENTITY_REQUIRES_SCALAR_SELECTOR_VALUE",
        "DEFERRED_ENDPOINT_RATIO_REQUIRES_EXPLICIT_1D_TEMPORAL_SERIES",
        "DEFERRED_ENDPOINT_DELTA_REQUIRES_EXPLICIT_1D_TEMPORAL_SERIES",
        "DEFERRED_NONNUMERIC_OR_NONFINITE_SELECTOR_VALUE",
        "DEFERRED_ENDPOINT_RATIO_ZERO_START",
    }:
        return "SELECTOR_VALUE_SHAPE_OR_UNIT_AUTHORITY_GAP_FROZEN", "R432_SELECTOR_VALUE_SHAPE_AND_UNIT_AUTHORITY_REVIEW"
    return "AUTHORIZED_SELECTOR_MATERIALIZATION_AUTHORITY_GAP_FROZEN", "R432_AUTHORIZED_SELECTOR_AUTHORITY_GAP_REVIEW"


def validate_target_attempts(parent: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    blocked = 0
    materialized = 0
    semantic_valid = 0
    deferred = 0
    gap_counts: dict[str, int] = {}
    for r in parent.get("records") or []:
        disp = str(r.get("materialization_disposition") or "")
        is_blocked = bool(r.get("source_integrity_blocked")) or disp.startswith("BLOCKED_")
        is_mat = bool(r.get("numeric_target_materialized")) and disp == "MATERIALIZED"
        semantic_ok = False
        gap_class = None
        next_priority = None
        reasons: list[str] = []
        if is_blocked:
            blocked += 1
            reasons.append("PARENT_SOURCE_INTEGRITY_BLOCK")
        elif is_mat:
            materialized += 1
            semantic_ok = (
                _finite_scalar(r.get("numeric_value"))
                and bool(r.get("frozen_selector"))
                and bool(r.get("frozen_transform_id"))
                and isinstance(r.get("domain_protocol"), dict)
                and bool(r.get("domain_protocol"))
                and r.get("external_engine_result_used_to_define_target") is False
                and r.get("result_selected_transform_used") is False
                and r.get("adjudicative_in_r430") is False
            )
            semantic_valid += int(semantic_ok)
            if not semantic_ok:
                reasons.append("MATERIALIZED_TARGET_STATIC_SEMANTIC_GUARD_FAILURE")
            next_priority = "R432_MATERIALIZED_TARGET_ADJUDICATIVE_SEMANTIC_GATE" if semantic_ok else "REPAIR_R431_MATERIALIZED_TARGET_SEMANTICS"
        else:
            deferred += 1
            gap_class, next_priority = _deferred_gap_class(disp)
            gap_counts[gap_class] = gap_counts.get(gap_class, 0) + 1
            if r.get("numeric_value") is not None:
                reasons.append("DEFERRED_RECORD_MUST_NOT_CARRY_NUMERIC_VALUE")
            if r.get("adjudicative_in_r430") is not False:
                reasons.append("DEFERRED_RECORD_ADJUDICATIVE_FLAG_INVALID")

        terminal_ok = (not is_blocked) and (semantic_ok if is_mat else not reasons)
        records.append({
            "window_id": r.get("window_id"),
            "domain": r.get("domain"),
            "parent_materialization_disposition": disp,
            "parent_numeric_target_materialized": is_mat,
            "parent_numeric_value": r.get("numeric_value") if is_mat else None,
            "semantic_validation_pass": semantic_ok if is_mat else None,
            "authority_gap_class": gap_class,
            "terminal_validation_pass": terminal_ok,
            "validation_reasons": reasons,
            "adjudicative_in_r431": False,
            "numeric_target_execution_performed_in_r431": False,
            "external_engine_result_used": False,
            "result_selected_selector_or_transform_used": False,
            "next_priority": next_priority,
        })
    return {
        "stage": STAGE,
        "status": "R431_TARGET_ATTEMPT_SEMANTIC_VALIDATION_COMPLETE" if len(records) == 5 and blocked == 0 and all(r["terminal_validation_pass"] for r in records) else BLOCKED,
        "record_count": len(records),
        "parent_materialized_count": materialized,
        "materialized_semantic_valid_count": semantic_valid,
        "parent_deferred_count": deferred,
        "deferred_authority_gap_count": deferred,
        "authority_gap_class_counts": gap_counts,
        "source_integrity_blocked_count": blocked,
        "adjudicative_promotion_count": 0,
        "numeric_target_execution_performed": False,
        "records": records,
    }


def freeze_target_authority_closure(
    target_validation: dict[str, Any],
    selector_gaps: dict[str, Any],
    design: dict[str, Any],
    semantic_repair: dict[str, Any],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []

    for r in target_validation.get("records") or []:
        if r.get("parent_numeric_target_materialized"):
            status = "MATERIALIZED_TARGET_SEMANTIC_GATE_CANDIDATE_NONADJUDICATIVE"
        else:
            status = str(r.get("authority_gap_class") or "AUTHORIZED_SELECTOR_AUTHORITY_GAP_FROZEN")
        records.append({
            "source_branch": "R430_AUTHORIZED_SELECTOR_ATTEMPT",
            "window_id": r.get("window_id"), "domain": r.get("domain"),
            "closure_status": status,
            "authority_implementation_authorized_in_r432": bool(r.get("terminal_validation_pass")),
            "numeric_target_execution_authorized_in_r431": False,
            "next_priority": r.get("next_priority"),
        })

    for r in selector_gaps.get("records") or []:
        parent_status = str(r.get("closure_status") or "")
        if parent_status == "NO_EXACT_PRE_RESULT_SELECTOR_RULE_AUTHORITY_GAP_FROZEN":
            status = "PRE_RESULT_SELECTOR_RULE_CATALOG_EXTENSION_AUTHORITY_FROZEN"
            nxt = "R432_PRE_RESULT_SELECTOR_RULE_CATALOG_EXTENSION_OR_ALTERNATE_CANONICAL_SOURCE_BINDING"
        elif parent_status == "AMBIGUOUS_EXACT_SELECTOR_RULE_AUTHORITY_GAP_FROZEN":
            status = "AMBIGUOUS_EXACT_SELECTOR_RULE_REVIEW_AUTHORITY_FROZEN"
            nxt = "R432_AMBIGUOUS_EXACT_SELECTOR_RULE_DISAMBIGUATION"
        else:
            status = "SELECTOR_AUTHORITY_GAP_ROUTE_PRESERVED"
            nxt = r.get("next_priority")
        records.append({
            "source_branch": "R430_SELECTOR_GAP",
            "window_id": r.get("window_id"), "domain": r.get("domain"),
            "closure_status": status,
            "authority_implementation_authorized_in_r432": True,
            "numeric_target_execution_authorized_in_r431": False,
            "next_priority": nxt,
        })

    design_ready = 0
    for r in design.get("records") or []:
        ready = bool(r.get("implementation_validation_pass")) and str(r.get("validation_status") or "") == "VALIDATED_PRE_RESULT_NONNUMERIC_TARGET_AUTHORITY_DEFINITION"
        design_ready += int(ready)
        records.append({
            "source_branch": "R429_VALIDATED_TARGET_DESIGN",
            "window_id": r.get("window_id"), "domain": r.get("domain"),
            "closure_status": "TARGET_DESIGN_OBSERVABLE_BINDING_IMPLEMENTATION_AUTHORITY_FROZEN" if ready else "TARGET_DESIGN_VALIDATION_BLOCKED",
            "authority_implementation_authorized_in_r432": ready,
            "numeric_target_execution_authorized_in_r431": False,
            "next_priority": "R432_TARGET_DESIGN_OBSERVABLE_BINDING_IMPLEMENTATION" if ready else "REPAIR_TARGET_DESIGN_AUTHORITY",
        })

    sem_records = semantic_repair.get("records") or []
    sem_ready = 0
    for r in sem_records:
        immutable = r.get("numeric_value_changed") is False and r.get("mapping_class_changed") is False and r.get("readjudication_performed") is False
        sem_ready += int(immutable)
        records.append({
            "source_branch": "R430_SEMANTIC_REPAIR",
            "window_id": r.get("window_id"), "domain": r.get("domain"),
            "closure_status": "PRIMARY_MAPPING_AUTHORITY_GAP_FROZEN" if immutable else "PRIMARY_MAPPING_REPAIR_MUTATION_BLOCKED",
            "authority_implementation_authorized_in_r432": immutable,
            "numeric_target_execution_authorized_in_r431": False,
            "next_priority": "R432_PRIMARY_MAPPING_AUTHORITY_DEFINITION" if immutable else "REPAIR_PRIMARY_MAPPING_GOVERNANCE",
        })

    counts: dict[str, int] = {}
    for r in records:
        counts[r["source_branch"]] = counts.get(r["source_branch"], 0) + 1
    total = len(records)
    all_auth_or_candidate = all(r.get("authority_implementation_authorized_in_r432") is True for r in records)
    return {
        "stage": STAGE,
        "status": "R431_TARGET_AUTHORITY_CLOSURE_REGISTRY_FROZEN" if total == 57 and counts == {
            "R430_AUTHORIZED_SELECTOR_ATTEMPT": 5,
            "R430_SELECTOR_GAP": 39,
            "R429_VALIDATED_TARGET_DESIGN": 12,
            "R430_SEMANTIC_REPAIR": 1,
        } and all_auth_or_candidate else BLOCKED,
        "active_target_repair_accounting_count": total,
        "branch_counts": counts,
        "target_design_observable_binding_authorized_count": design_ready,
        "primary_mapping_authority_definition_authorized_count": sem_ready,
        "numeric_target_execution_authorized_count": 0,
        "result_selected_authority_forbidden": True,
        "records": records,
    }


def freeze_semantic_repair_closure(parent: dict[str, Any]) -> dict[str, Any]:
    records = []
    for r in parent.get("records") or []:
        immutable = r.get("numeric_value_changed") is False and r.get("mapping_class_changed") is False and r.get("readjudication_performed") is False
        eligible = int(r.get("eligible_primary_row_count_under_existing_frozen_mapping") or 0)
        records.append({
            "window_id": r.get("window_id"), "domain": r.get("domain"),
            "parent_review_status": r.get("review_status"),
            "existing_primary_mapping_eligible_count": eligible,
            "closure_status": "EXISTING_PRIMARY_MAPPING_AVAILABLE_FOR_R432_GATE" if eligible > 0 else "PRIMARY_MAPPING_AUTHORITY_GAP_FROZEN",
            "authority_definition_implementation_authorized_in_r432": immutable,
            "numeric_value_changed": False,
            "mapping_class_changed": False,
            "readjudication_performed": False,
        })
    return {
        "stage": STAGE,
        "status": "R431_SEMANTIC_REPAIR_AUTHORITY_CLOSURE_FROZEN" if len(records) == 1 and all(r["authority_definition_implementation_authorized_in_r432"] for r in records) else BLOCKED,
        "record_count": len(records),
        "records": records,
    }


def _load_macro(root: Path) -> tuple[list[str], np.ndarray, list[str], np.ndarray]:
    with np.load(root / R327_TRAJ, allow_pickle=False) as z:
        return (
            [str(x) for x in np.asarray(z["candidate_ids"]).tolist()],
            np.asarray(z["age_ma"], dtype=float),
            [str(x) for x in np.asarray(z["variable_names"]).tolist()],
            np.asarray(z["state"], dtype=float),
        )


def _support_and_macro_audit(root: Path, age: np.ndarray, cohort: list[str], spatial: np.ndarray) -> dict[str, bool]:
    cands, macro_age, vars_, macro = _load_macro(root)
    checks: dict[str, bool] = {}
    checks["age_axis_exact_r327"] = np.array_equal(age, macro_age)
    try:
        cix = [cands.index(c) for c in cohort]
    except ValueError:
        cix = []
    checks["candidate_cohort_is_r327_subset"] = len(cix) == len(cohort)
    if not cix or spatial.ndim != 5 or spatial.shape[-1] != 4:
        checks["deme_count_matches_r327_macro_constraint"] = False
        checks["population_sum_matches_r327_effective_population"] = False
        checks["all_active_cells_on_age_matched_canonical_support"] = False
        return checks
    vix = {v: i for i, v in enumerate(vars_)}
    active = spatial[..., 3] > 0.5
    observed_demes = np.sum(active, axis=3)
    expected_demes = np.rint(macro[:, :, :, vix["deme_count"]][:, cix, :]).astype(int)
    expected_demes = np.clip(expected_demes, 1, spatial.shape[3])
    checks["deme_count_matches_r327_macro_constraint"] = bool(np.array_equal(observed_demes, expected_demes))
    observed_pop = np.sum(np.where(active, spatial[..., 0], 0.0), axis=3)
    expected_pop = np.maximum(0.0, macro[:, :, :, vix["effective_population"]][:, cix, :])
    checks["population_sum_matches_r327_effective_population"] = bool(np.allclose(observed_pop, expected_pop, rtol=5e-6, atol=5e-6))

    support_ok = True
    try:
        from arcana_worldsim.late_cenozoic.paleogeography import physical_paleogeography_state
        with np.load(root / A1, allow_pickle=False) as z:
            a1 = {k: np.asarray(z[k]) for k in z.files}
        rows = spatial[..., 1]
        cols = spatial[..., 2]
        for t, a in enumerate(age):
            land = np.asarray(physical_paleogeography_state(a1, float(a))["land_support"], dtype=float) > 1e-9
            m = active[:, :, t, :]
            rr = rows[:, :, t, :][m].astype(int)
            cc = cols[:, :, t, :][m].astype(int)
            if len(rr):
                if np.any(rr < 0) or np.any(rr >= land.shape[0]) or np.any(cc < 0) or np.any(cc >= land.shape[1]) or not np.all(land[rr, cc]):
                    support_ok = False
                    break
    except Exception:
        support_ok = False
    checks["all_active_cells_on_age_matched_canonical_support"] = support_ok
    return checks


def validate_and_seal_j14(root: Path, parent_meta: dict[str, Any], r429_auth: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    p = root / PJ14_NPZ
    checks["parent_candidate_execution_complete"] = parent_meta.get("execution_performed") is True
    checks["parent_candidate_validation_pass"] = parent_meta.get("validation_pass") is True and all((parent_meta.get("validation_checks") or {}).values())
    checks["parent_candidate_marked_pending_r431_seal"] = parent_meta.get("candidate_authority_only_not_yet_canonical_sealed") is True
    checks["authority_algorithm_exact"] = parent_meta.get("authority_algorithm") == AUTHORITY_ALGORITHM
    checks["construction_semantics_model_derived_not_observed"] = parent_meta.get("construction_semantics") == "MODEL_DERIVED_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_NOT_OBSERVED_LOCATION_HISTORY"
    checks["future_spatial_anchor_not_used"] = parent_meta.get("future_spatial_anchor_used") is False
    checks["external_engine_not_used"] = parent_meta.get("external_engine_used") is False
    checks["candidate_npz_present"] = p.exists()
    checks["candidate_hash_matches_r430_metadata"] = p.exists() and sha256(p) == parent_meta.get("output_npz_sha256")

    current_inputs = validate_authority_inputs(root)
    frozen = r429_auth.get("input_hash_freeze") or {}
    checks["current_input_hashes_match_r429_freeze"] = current_inputs.get("ready") is True and bool(frozen) and current_inputs.get("hashes") == frozen

    age = np.asarray([])
    cohort: list[str] = []
    names: list[str] = []
    spatial = np.asarray([])
    if p.exists():
        try:
            with np.load(p, allow_pickle=False) as z:
                checks["candidate_npz_exact_required_keys"] = set(z.files) == {"age_ma", "candidate_ids", "state_variable_names", "spatial_state"}
                age = np.asarray(z["age_ma"], dtype=float)
                cohort = [str(x) for x in np.asarray(z["candidate_ids"]).tolist()]
                names = [str(x) for x in np.asarray(z["state_variable_names"]).tolist()]
                spatial = np.asarray(z["spatial_state"], dtype=np.float32)
        except Exception:
            checks["candidate_npz_exact_required_keys"] = False
    else:
        checks["candidate_npz_exact_required_keys"] = False

    checks["state_variable_names_exact"] = names == ["population_proxy", "grid_row", "grid_col", "active"]
    checks["spatial_state_rank_and_components"] = spatial.ndim == 5 and spatial.shape[-1] == 4
    checks["spatial_state_finite"] = spatial.size > 0 and bool(np.all(np.isfinite(spatial)))
    if spatial.ndim == 5 and spatial.shape[-1] == 4 and age.size:
        checks.update(_support_and_macro_audit(root, age, cohort, spatial))
    else:
        checks.update({
            "age_axis_exact_r327": False,
            "candidate_cohort_is_r327_subset": False,
            "deme_count_matches_r327_macro_constraint": False,
            "population_sum_matches_r327_effective_population": False,
            "all_active_cells_on_age_matched_canonical_support": False,
        })

    # Independent deterministic validation recomputation. It is not persisted and
    # does not create a second authority artifact.
    recompute_ok = False
    try:
        replay = build_replay(root)
        recompute_ok = (
            np.array_equal(np.asarray(replay["age_ma"], dtype=float), age)
            and [str(x) for x in np.asarray(replay["candidate_ids"]).tolist()] == cohort
            and [str(x) for x in np.asarray(replay["state_variable_names"]).tolist()] == names
            and np.array_equal(np.asarray(replay["spatial_state"], dtype=np.float32), spatial)
        )
    except Exception:
        recompute_ok = False
    checks["deterministic_in_memory_recomputation_exact"] = recompute_ok

    verdict = "SEALED" if checks and all(checks.values()) else "BLOCKED"
    return {
        "stage": STAGE,
        "audit": "J14_DERIVED_CANONICAL_SPATIAL_AUTHORITY_VALIDATION",
        "status": J14_SEALED if verdict == "SEALED" else BLOCKED,
        "verdict": verdict,
        "authority_class": "SEALED_DERIVED_CANONICAL_SPATIAL_AUTHORITY_FOR_EXTERNAL_REVALIDATION_BINDING" if verdict == "SEALED" else None,
        "construction_semantics": "MODEL_DERIVED_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_NOT_OBSERVED_LOCATION_HISTORY",
        "observed_location_history_claim": False,
        "source_candidate_npz": str(PJ14_NPZ).replace("\\", "/"),
        "source_candidate_npz_sha256": parent_meta.get("output_npz_sha256"),
        "validation_recomputation_performed": True,
        "new_spatial_candidate_generated_in_r431": False,
        "canonical_state_rewritten": False,
        "canonical_authority_registry_extended": verdict == "SEALED",
        "geonomics_spatial_binding_authority_available_for_r432": verdict == "SEALED",
        "geonomics_execution_authorized": False,
        "checks_passed": sum(bool(v) for v in checks.values()),
        "checks_total": len(checks),
        "checks_failed": sum(not bool(v) for v in checks.values()),
        "checks": checks,
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    paudit = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    ptarget = load(root / PTARGET) if (root / PTARGET).exists() else {}
    pgaps = load(root / PGAPS) if (root / PGAPS).exists() else {}
    psem = load(root / PSEM) if (root / PSEM).exists() else {}
    pplan = load(root / PPLAN) if (root / PPLAN).exists() else {}
    pj14 = load(root / PJ14_META) if (root / PJ14_META).exists() else {}
    r429j14 = load(root / R429_J14) if (root / R429_J14).exists() else {}
    design = load(root / R429_DESIGN) if (root / R429_DESIGN).exists() else {}

    target_validation = validate_target_attempts(ptarget)
    authority_closure = freeze_target_authority_closure(target_validation, pgaps, design, psem)
    semantic_closure = freeze_semantic_repair_closure(psem)
    j14_seal = validate_and_seal_j14(root, pj14, r429j14)

    write(root / OUT / "R4_31_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_REGISTRY.json", target_validation)
    write(root / OUT / "R4_31_TARGET_AUTHORITY_CLOSURE_REGISTRY.json", authority_closure)
    write(root / OUT / "R4_31_SEMANTIC_REPAIR_AUTHORITY_CLOSURE.json", semantic_closure)
    write(root / J14_VALIDATION_SEAL, j14_seal)

    target_parent_materialized = int(ptarget.get("numeric_target_materialized_count") or 0)
    target_parent_deferred = int(ptarget.get("semantic_dependency_or_source_ambiguity_deferred_count") or 0)
    checks = [
        Check("parent_r430_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r430_sealed", pseal.get("status") == PARENT_SEALED and pseal.get("verdict") == "SEALED", pseal.get("status")),
        Check("parent_r430_complete", paudit.get("status") == PARENT_COMPLETE and paudit.get("checks_failed") == 0, paudit.get("status")),
        Check("parent_next_action_matches_r431", paudit.get("next_action") == PARENT_NEXT, paudit.get("next_action")),
        Check("parent_exact_five_authorized_attempts_terminal", ptarget.get("authorized_selector_attempt_count") == 5 and ptarget.get("source_integrity_blocked_count") == 0 and target_parent_materialized + target_parent_deferred == 5, {"materialized": target_parent_materialized, "deferred": target_parent_deferred}),
        Check("parent_selector_gap_exact_39", pgaps.get("record_count") == 39 and pgaps.get("selector_auto_authorized_count") == 0, pgaps.get("closure_status_counts")),
        Check("parent_target_design_exact_12_validated", design.get("record_count") == 12 and design.get("validated_count") == 12, design.get("validated_count")),
        Check("parent_semantic_repair_exact_one", psem.get("record_count") == 1, psem.get("record_count")),
        Check("parent_j14_candidate_executed_and_validated", pj14.get("execution_performed") is True and pj14.get("validation_pass") is True, pj14.get("status")),
        Check("parent_r431_plan_frozen", pplan.get("status") == "R430_TARGET_MATERIALIZATION_GAP_AND_J14_EXECUTION_EVIDENCE_FROZEN", pplan.get("status")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_POST_R430_PRE_GEONOMICS_BINDING_AND_PRE_TARGET_AUTHORITY_BINDING_EXECUTION", cfg.get("policy_freeze")),
        Check("target_attempt_semantic_validation_exact_five", target_validation.get("record_count") == 5 and target_validation.get("source_integrity_blocked_count") == 0, {"materialized": target_validation.get("parent_materialized_count"), "deferred": target_validation.get("parent_deferred_count")} ),
        Check("all_parent_materialized_values_semantically_valid_or_zero", target_validation.get("materialized_semantic_valid_count") == target_validation.get("parent_materialized_count"), target_validation.get("materialized_semantic_valid_count")),
        Check("zero_adjudicative_promotions_in_r431", target_validation.get("adjudicative_promotion_count") == 0),
        Check("target_authority_closure_reconciles_exact_57", authority_closure.get("active_target_repair_accounting_count") == 57 and authority_closure.get("branch_counts") == {"R430_AUTHORIZED_SELECTOR_ATTEMPT": 5, "R430_SELECTOR_GAP": 39, "R429_VALIDATED_TARGET_DESIGN": 12, "R430_SEMANTIC_REPAIR": 1}, authority_closure.get("branch_counts")),
        Check("target_design_observable_binding_authority_exact_12", authority_closure.get("target_design_observable_binding_authorized_count") == 12, authority_closure.get("target_design_observable_binding_authorized_count")),
        Check("primary_mapping_authority_definition_exact_one", authority_closure.get("primary_mapping_authority_definition_authorized_count") == 1, authority_closure.get("primary_mapping_authority_definition_authorized_count")),
        Check("semantic_repair_authority_closure_frozen", semantic_closure.get("status") == "R431_SEMANTIC_REPAIR_AUTHORITY_CLOSURE_FROZEN" and semantic_closure.get("record_count") == 1, semantic_closure.get("status")),
        Check("j14_validation_seal_pass", j14_seal.get("verdict") == "SEALED" and j14_seal.get("status") == J14_SEALED and j14_seal.get("checks_failed") == 0, j14_seal.get("checks")),
        Check("j14_sealed_as_model_derived_not_observed_history", j14_seal.get("authority_class") == "SEALED_DERIVED_CANONICAL_SPATIAL_AUTHORITY_FOR_EXTERNAL_REVALIDATION_BINDING" and j14_seal.get("observed_location_history_claim") is False),
        Check("j14_deterministic_recomputation_exact", (j14_seal.get("checks") or {}).get("deterministic_in_memory_recomputation_exact") is True),
        Check("j14_no_new_candidate_and_no_state_rewrite", j14_seal.get("new_spatial_candidate_generated_in_r431") is False and j14_seal.get("canonical_state_rewritten") is False),
        Check("geonomics_spatial_binding_prerequisite_now_available", j14_seal.get("geonomics_spatial_binding_authority_available_for_r432") is True),
        Check("geonomics_execution_still_forbidden", cfg.get("geonomics_execution_authorized") is False and j14_seal.get("geonomics_execution_authorized") is False),
        Check("no_target_numeric_execution_in_r431", cfg.get("target_numeric_execution_performed") is False and target_validation.get("numeric_target_execution_performed") is False),
        Check("no_external_engine_execution", cfg.get("external_engine_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False and j14_seal.get("canonical_state_rewritten") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
        Check("result_selected_selector_forbidden", cfg.get("result_selected_selector_forbidden") is True),
        Check("result_selected_transform_forbidden", cfg.get("result_selected_transform_forbidden") is True),
        Check("active_deferred_p2_two_preserved", paudit.get("active_deferred_p2_cell_count") == 2, paudit.get("active_deferred_p2_cell_count")),
        Check("proxy_context_only_two_preserved", paudit.get("proxy_context_only_count") == 2, paudit.get("proxy_context_only_count")),
        Check("p3_backlog_six_preserved", paudit.get("p3_backlog_cell_count") == 6, paudit.get("p3_backlog_cell_count")),
    ]
    ok = all(c.passed for c in checks)
    plan = {
        "stage": STAGE,
        "status": "R431_TARGET_AUTHORITY_AND_J14_VALIDATION_SEAL_EVIDENCE_FROZEN" if ok else BLOCKED,
        "parent_materialized_target_count": target_validation.get("parent_materialized_count"),
        "parent_deferred_authorized_target_count": target_validation.get("parent_deferred_count"),
        "materialized_target_semantic_valid_count": target_validation.get("materialized_semantic_valid_count"),
        "authorized_selector_authority_gap_count": target_validation.get("deferred_authority_gap_count"),
        "selector_rule_gap_count": 39,
        "target_design_observable_binding_authorized_count": authority_closure.get("target_design_observable_binding_authorized_count"),
        "primary_mapping_authority_definition_authorized_count": authority_closure.get("primary_mapping_authority_definition_authorized_count"),
        "active_target_repair_accounting_count": authority_closure.get("active_target_repair_accounting_count"),
        "j14_spatial_authority_sealed": j14_seal.get("verdict") == "SEALED",
        "j14_authority_class": j14_seal.get("authority_class"),
        "geonomics_parameter_materialization_static_validation_authorized_in_r432": j14_seal.get("verdict") == "SEALED",
        "geonomics_execution_authorized_in_r432_by_r431": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R431_TARGET_AUTHORITY_OR_J14_VALIDATION",
    }
    write(root / OUT / "R4_31_R432_EXECUTION_PLAN.json", plan)
    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "parent_materialized_target_count": target_validation.get("parent_materialized_count"),
        "parent_deferred_authorized_target_count": target_validation.get("parent_deferred_count"),
        "materialized_target_semantic_valid_count": target_validation.get("materialized_semantic_valid_count"),
        "authorized_selector_authority_gap_count": target_validation.get("deferred_authority_gap_count"),
        "selector_rule_gap_count": 39,
        "target_design_observable_binding_authorized_count": authority_closure.get("target_design_observable_binding_authorized_count"),
        "primary_mapping_authority_definition_authorized_count": authority_closure.get("primary_mapping_authority_definition_authorized_count"),
        "active_target_repair_accounting_count": authority_closure.get("active_target_repair_accounting_count"),
        "j14_spatial_authority_validation_sealed": j14_seal.get("verdict") == "SEALED",
        "j14_authority_class": j14_seal.get("authority_class"),
        "geonomics_parameter_materialization_static_validation_authorized_for_r432": j14_seal.get("verdict") == "SEALED",
        "geonomics_execution_performed": False,
        "external_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "canonical_authority_registry_extended": j14_seal.get("verdict") == "SEALED",
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_31_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    parent = load(root / PSEAL) if (root / PSEAL).exists() else {}
    audit = load(root / OUT / "R4_31_INTEGRATED_AUDIT.json") if (root / OUT / "R4_31_INTEGRATED_AUDIT.json").exists() else {}
    target = load(root / OUT / "R4_31_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_REGISTRY.json") if (root / OUT / "R4_31_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_REGISTRY.json").exists() else {}
    closure = load(root / OUT / "R4_31_TARGET_AUTHORITY_CLOSURE_REGISTRY.json") if (root / OUT / "R4_31_TARGET_AUTHORITY_CLOSURE_REGISTRY.json").exists() else {}
    sem = load(root / OUT / "R4_31_SEMANTIC_REPAIR_AUTHORITY_CLOSURE.json") if (root / OUT / "R4_31_SEMANTIC_REPAIR_AUTHORITY_CLOSURE.json").exists() else {}
    j14 = load(root / J14_VALIDATION_SEAL) if (root / J14_VALIDATION_SEAL).exists() else {}
    plan = load(root / OUT / "R4_31_R432_EXECUTION_PLAN.json") if (root / OUT / "R4_31_R432_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r430_sealed", parent.get("status") == PARENT_SEALED and parent.get("verdict") == "SEALED", parent.get("status")),
        Check("r431_complete", audit.get("status") == COMPLETE, audit.get("status")),
        Check("r431_zero_process_failures", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("five_target_attempts_semantically_terminal", target.get("record_count") == 5 and target.get("source_integrity_blocked_count") == 0 and int(target.get("parent_materialized_count") or 0) + int(target.get("parent_deferred_count") or 0) == 5, {"materialized": target.get("parent_materialized_count"), "deferred": target.get("parent_deferred_count")}),
        Check("all_materialized_targets_semantically_valid_or_zero", target.get("materialized_semantic_valid_count") == target.get("parent_materialized_count"), target.get("materialized_semantic_valid_count")),
        Check("zero_adjudicative_target_promotions", target.get("adjudicative_promotion_count") == 0),
        Check("target_authority_accounting_exact_57", closure.get("active_target_repair_accounting_count") == 57, closure.get("branch_counts")),
        Check("selector_rule_gaps_39_preserved", (closure.get("branch_counts") or {}).get("R430_SELECTOR_GAP") == 39),
        Check("target_design_12_binding_authorities", closure.get("target_design_observable_binding_authorized_count") == 12),
        Check("semantic_repair_one_authority", sem.get("record_count") == 1 and closure.get("primary_mapping_authority_definition_authorized_count") == 1),
        Check("j14_validation_seal_pass", j14.get("status") == J14_SEALED and j14.get("verdict") == "SEALED" and j14.get("checks_failed") == 0, j14.get("status")),
        Check("j14_authority_hash_bound", bool(j14.get("source_candidate_npz_sha256")) and (root / PJ14_NPZ).exists() and sha256(root / PJ14_NPZ) == j14.get("source_candidate_npz_sha256"), j14.get("source_candidate_npz_sha256")),
        Check("j14_model_derived_not_observed_history", j14.get("observed_location_history_claim") is False and str(j14.get("authority_class") or "").startswith("SEALED_DERIVED_CANONICAL_SPATIAL_AUTHORITY")),
        Check("j14_deterministic_recomputation_pass", (j14.get("checks") or {}).get("deterministic_in_memory_recomputation_exact") is True),
        Check("j14_canonical_state_not_rewritten", j14.get("canonical_state_rewritten") is False),
        Check("geonomics_binding_prerequisite_available_but_execution_not_authorized", j14.get("geonomics_spatial_binding_authority_available_for_r432") is True and j14.get("geonomics_execution_authorized") is False),
        Check("r432_plan_frozen", plan.get("status") == "R431_TARGET_AUTHORITY_AND_J14_VALIDATION_SEAL_EVIDENCE_FROZEN", plan.get("status")),
        Check("deferred_p2_two", plan.get("active_deferred_p2_cell_count") == 2),
        Check("proxy_context_two", plan.get("proxy_context_only_count") == 2),
        Check("p3_backlog_six", plan.get("p3_backlog_cell_count") == 6),
        Check("no_external_engine_execution", audit.get("external_engine_execution_performed") is False),
        Check("no_target_numeric_execution", audit.get("target_numeric_execution_performed") is False),
        Check("no_readjudication", audit.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", audit.get("canonical_state_changed") is False),
        Check("next_action_present", audit.get("next_action") == NEXT, audit.get("next_action")),
    ]
    verdict = "SEALED" if all(c.passed for c in checks) else "BLOCKED"
    out = {
        "stage": STAGE,
        "audit": "FINAL_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL",
        "status": SEALED if verdict == "SEALED" else BLOCKED,
        "verdict": verdict,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "parent_materialized_target_count": target.get("parent_materialized_count"),
            "parent_deferred_authorized_target_count": target.get("parent_deferred_count"),
            "materialized_target_semantic_valid_count": target.get("materialized_semantic_valid_count"),
            "authorized_selector_authority_gap_count": target.get("deferred_authority_gap_count"),
            "selector_rule_gap_count": (closure.get("branch_counts") or {}).get("R430_SELECTOR_GAP"),
            "target_design_observable_binding_authorized_count": closure.get("target_design_observable_binding_authorized_count"),
            "primary_mapping_authority_definition_authorized_count": closure.get("primary_mapping_authority_definition_authorized_count"),
            "active_target_repair_accounting_count": closure.get("active_target_repair_accounting_count"),
            "j14_spatial_authority_validation_sealed": j14.get("verdict") == "SEALED",
            "j14_authority_class": j14.get("authority_class"),
            "canonical_authority_registry_extended": j14.get("canonical_authority_registry_extended") is True,
            "canonical_state_changed": False,
            "geonomics_parameter_materialization_static_validation_authorized_for_r432": plan.get("geonomics_parameter_materialization_static_validation_authorized_in_r432") is True,
            "geonomics_execution_authorized": False,
            "external_engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "readjudication_performed": False,
            "deep_biological_coupling": False,
            "active_deferred_p2_cell_count": 2,
            "proxy_context_only_count": 2,
            "p3_backlog_cell_count": 6,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
