from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import re

STAGE = "v0.6D1-R4.34"

PARENT_COMPLETE = (
    "PASS_R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_"
    "GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_"
    "GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
    "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT"
)

COMPLETE = (
    "PASS_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
    "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
    "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R434_PARENT_SELECTOR_AUTHORITY_OR_NATIVE_PARAMETER_"
    "MATERIALIZATION_PREFLIGHT_FAILURE"
)

NEXT = (
    "BUILD_R435_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
    "AND_SEED_AUTHORITY_CLOSURE"
)

CFG = Path(
    "configs/world1_r434_geonomics_runtime_selector_authority_freeze_"
    "native_parameter_materialization_preflight_v0_6D1_R4_34.json"
)
PSEAL = Path("outputs/v0_6D1_R4_33_SEAL/R4_33_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_33/R4_33_INTEGRATED_AUDIT.json")
PTARGET = Path(
    "outputs/v0_6D1_R4_33/"
    "R4_33_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION.json"
)
PRUNTIME = Path(
    "outputs/v0_6D1_R4_33/"
    "R4_33_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT.json"
)
PPLAN = Path("outputs/v0_6D1_R4_33/R4_33_R434_EXECUTION_PLAN.json")

OUT = Path("outputs/v0_6D1_R4_34")
SEAL = Path("outputs/v0_6D1_R4_34_SEAL/R4_34_FINAL_SEAL_AUDIT.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"
JOBS = (J14, J18, J21)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None

    def d(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _inventory_key_index(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for inv in package.get("canonical_source_inventories") or []:
        for arr in inv.get("arrays") or []:
            key = str(arr.get("key") or "")
            if key and key not in idx:
                idx[key] = arr
    return idx


def _axis_authority(key: str, arr: dict[str, Any] | None) -> dict[str, Any]:
    shape = list((arr or {}).get("shape") or [])
    cardinality = shape[0] if len(shape) == 1 and isinstance(shape[0], int) else None
    vals = (arr or {}).get("axis_values_if_small")
    return {
        "selector_dimension": key,
        "authority_status": "FROZEN_PRE_RESULT",
        "rule": "FULL_ORDERED_CANONICAL_AXIS_PRESERVATION",
        "selection_mode": "NO_SINGLE_VALUE_SELECTION",
        "enumeration_order": "CANONICAL_STORAGE_ORDER",
        "cardinality_if_known": cardinality,
        "values_if_small_and_already_frozen": vals,
        "ranking_performed": False,
        "averaging_performed": False,
        "comparison_result_used": False,
    }


def _member_authority(key: str, arr: dict[str, Any] | None) -> dict[str, Any]:
    shape = list((arr or {}).get("shape") or [])
    cardinality = shape[0] if len(shape) >= 1 and isinstance(shape[0], int) else None
    vals = (arr or {}).get("axis_values_if_small")
    return {
        "selector_dimension": key,
        "authority_status": "FROZEN_PRE_RESULT",
        "rule": "EXHAUSTIVE_ENUMERATION_ALL_HASH_BOUND_MEMBERS",
        "selection_mode": "ALL_MEMBERS_INDEPENDENT_NONADJUDICATIVE_BUNDLES",
        "enumeration_order": "CANONICAL_STORAGE_ORDER",
        "cardinality_if_known": cardinality,
        "values_if_small_and_already_frozen": vals,
        "ranking_performed": False,
        "averaging_performed": False,
        "majority_vote_performed": False,
        "comparison_result_used": False,
    }


def _layer_set_authority(
    key: str,
    index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidate_name_keys = (
        ("environment", ("environment_variable_names", "environment_fields")),
        ("producer", ("landscape_variable_names", "producer_landscape", "producer_taxon_ids")),
    )
    source = None
    for token, names in candidate_name_keys:
        if token in key.lower():
            for name in names:
                if name in index:
                    source = name
                    break
    vals = index.get(source or "", {}).get("axis_values_if_small") if source else None
    return {
        "selector_dimension": key,
        "authority_status": "FROZEN_PRE_RESULT",
        "rule": "PRESERVE_ALL_DECLARED_LAYERS_AS_PROVENANCE_SEPARATE_CHANNELS",
        "selection_mode": "NO_LAYER_DROPPING_NO_NUMERIC_FUSION",
        "source_name_axis_if_identified": source,
        "declared_names_if_small": vals,
        "ranking_performed": False,
        "averaging_performed": False,
        "cross_layer_numeric_mixing_performed": False,
        "comparison_result_used": False,
    }


def _combination_authority(key: str) -> dict[str, Any]:
    return {
        "selector_dimension": key,
        "authority_status": "FROZEN_PRE_RESULT",
        "rule": "PROVENANCE_SEPARATE_PARALLEL_LAYERS_ONLY",
        "selection_mode": "NO_CROSS_LAYER_NUMERIC_COMBINATION",
        "allowed_operations": [
            "retain_separate_layer_identity",
            "retain_separate_source_hash_and_role",
            "bind_later_to_engine_layer_roles_only_with_explicit_semantic_authority",
        ],
        "forbidden_operations": [
            "mean",
            "sum",
            "weighted_sum",
            "max",
            "min",
            "target_fitted_combination",
        ],
        "comparison_result_used": False,
    }


def _freeze_requirement(
    requirement: str,
    index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    low = requirement.lower()
    arr = index.get(requirement)

    if any(tok in low for tok in ("age", "time")) and requirement not in {
        "environment_layer_set", "producer_layer_set"
    }:
        return _axis_authority(requirement, arr)

    if any(tok in low for tok in ("candidate", "member", "forcing", "taxon")):
        return _member_authority(requirement, arr)

    if requirement in ("environment_layer_set", "producer_layer_set"):
        return _layer_set_authority(requirement, index)

    if requirement == "cross_layer_combination_policy":
        return _combination_authority(requirement)

    # A placeholder is not an authority. Fail closed rather than inventing a selector.
    return {
        "selector_dimension": requirement,
        "authority_status": "DEFERRED_UNRESOLVED_SELECTOR_DIMENSION_IDENTITY",
        "rule": None,
        "selection_mode": None,
        "comparison_result_used": False,
    }


def freeze_runtime_selector_authority(
    root: Path,
    runtime_registry: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blocked = 0

    for parent in runtime_registry.get("records") or []:
        jid = parent.get("job_id")
        if jid not in JOBS:
            continue

        rel = parent.get("runtime_parameter_binding_package_file")
        p = root / str(rel or "")
        expected = parent.get("runtime_parameter_binding_package_sha256")
        package_ok = bool(
            rel and p.exists() and expected and sha256(p) == expected
            and parent.get("package_compile_pass") is True
        )
        package = load(p) if package_ok else {}
        index = _inventory_key_index(package)
        requirements = (
            package.get("selector_authority", {}).get("selector_requirements") or []
        )

        authorities = [
            _freeze_requirement(str(req), index)
            for req in requirements
        ]
        all_frozen = bool(requirements) and all(
            a.get("authority_status") == "FROZEN_PRE_RESULT"
            for a in authorities
        )

        if not package_ok or not all_frozen:
            blocked += 1

        d = root / OUT / "geonomics_selector_authority" / str(jid)
        auth = {
            "stage": STAGE,
            "engine": "Geonomics",
            "job_id": jid,
            "window_id": parent.get("window_id"),
            "status":
                "R434_RUNTIME_SELECTOR_AUTHORITY_FROZEN_PRE_RESULT"
                if package_ok and all_frozen
                else "BLOCKED_RUNTIME_SELECTOR_AUTHORITY_FREEZE",
            "parent_runtime_binding_package_file": rel,
            "parent_runtime_binding_package_sha256": expected,
            "parent_runtime_binding_package_hash_match": package_ok,
            "selector_requirements": requirements,
            "selector_authorities": authorities,
            "exhaustive_enumeration_only": True,
            "single_best_member_selection_forbidden": True,
            "target_fit_ranking_forbidden": True,
            "majority_vote_forbidden": True,
            "default_selector_values_used": False,
            "comparison_result_used": False,
            "geonomics_execution_authorized_in_r434": False,
        }
        ap = d / "GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE.json"
        write(ap, auth)

        rows.append({
            "job_id": jid,
            "window_id": parent.get("window_id"),
            "selector_authority_file": ap.relative_to(root).as_posix(),
            "selector_authority_sha256": sha256(ap),
            "parent_runtime_binding_package_hash_match": package_ok,
            "selector_requirement_count": len(requirements),
            "selector_authority_frozen_count":
                sum(a.get("authority_status") == "FROZEN_PRE_RESULT" for a in authorities),
            "all_selector_authority_frozen": all_frozen,
            "selector_freeze_pass": package_ok and all_frozen,
        })

    passed = sum(bool(r["selector_freeze_pass"]) for r in rows)
    return {
        "stage": STAGE,
        "status":
            "R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_COMPLETE"
            if len(rows) == 3 and passed == 3 and blocked == 0 else BLOCKED,
        "record_count": len(rows),
        "selector_authority_frozen_job_count": passed,
        "selector_authority_blocked_job_count": blocked,
        "result_selected_selector_used": False,
        "majority_vote_performed": False,
        "geonomics_execution_authorized": False,
        "records": rows,
    }


def _schema_obligations(job_id: str) -> list[dict[str, Any]]:
    """Requirements that must be resolved before writing a run-capable GNX params file.

    These are intentionally not satisfied by arbitrary defaults. The Geonomics 1.4.9
    native schema requires landscape geometry/layers, species init/K semantics and model
    time/seed fields. ARCANA must bind each from frozen authority rather than use the
    package defaults.
    """
    common = [
        {
            "obligation": "LANDSCAPE_GEOMETRY_DIM_RES_ULC_PRJ",
            "status": "DEFERRED_EXPLICIT_GRID_GEOMETRY_AND_UNIT_AUTHORITY_REQUIRED",
            "reason": "grid indices/raster shape do not by themselves authorize physical resolution, upper-left coordinates, or projection",
        },
        {
            "obligation": "MODEL_PHYSICAL_TIME_TO_INTEGER_TIMESTEP_MAPPING",
            "status": "DEFERRED_EXPLICIT_TIME_DISCRETIZATION_AUTHORITY_REQUIRED",
            "reason": "canonical age axes must not be silently converted to Geonomics integer timesteps",
        },
        {
            "obligation": "MODEL_RANDOM_SEED_LEDGER_BINDING",
            "status": "DEFERRED_EXACT_FROZEN_JOB_SEED_AUTHORITY_BINDING_REQUIRED",
            "reason": "native model.num must be bound to the frozen historical job seed ledger, not generated ad hoc",
        },
        {
            "obligation": "LAYER_VALUE_SCALING_NORMALIZATION",
            "status": "DEFERRED_EXPLICIT_NO_LOSS_SCALING_AUTHORITY_REQUIRED",
            "reason": "no automatic [0,1] rescaling or clipping may change canonical layer semantics",
        },
    ]

    if job_id in (J14, J18):
        common += [
            {
                "obligation": "SPECIES_INIT_N_FROM_CANONICAL_POPULATION",
                "status": "DEFERRED_POPULATION_TO_INTEGER_INDIVIDUAL_REPRESENTATION_AUTHORITY_REQUIRED",
                "reason": "ARCANA effective/proxy population is not automatically literal Geonomics individual count",
            },
            {
                "obligation": "EXACT_SPATIAL_INITIAL_STATE_INJECTION",
                "status": "DEFERRED_DEME_TO_INDIVIDUAL_COORDINATE_ADAPTER_AUTHORITY_REQUIRED",
                "reason": "random initialization from a carrying-capacity surface would discard the frozen per-deme spatial state",
            },
            {
                "obligation": "SPECIES_K_LAYER_AND_K_FACTOR_SEMANTIC_BINDING",
                "status": "DEFERRED_CARRYING_CAPACITY_ROLE_AUTHORITY_REQUIRED",
                "reason": "no canonical source layer may be silently reinterpreted as K_layer/K_factor",
            },
        ]
    else:
        common += [
            {
                "obligation": "PRODUCER_RESOURCE_TO_GEONOMICS_LAYER_ROLE_BINDING",
                "status": "DEFERRED_RESOURCE_LAYER_ROLE_AUTHORITY_REQUIRED",
                "reason": "producer resource abundance/suitability is support evidence, not automatically a Geonomics population or K layer",
            },
            {
                "obligation": "ENVIRONMENT_PRODUCER_LAYER_ROLE_SEPARATION",
                "status": "READY_PROVENANCE_SEPARATION_FROZEN_BY_R434",
                "reason": "R4.34 freezes parallel provenance-separated layers and forbids numerical fusion",
            },
        ]
    return common


def native_parameter_materialization_preflight(
    root: Path,
    selector_registry: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    for sel in selector_registry.get("records") or []:
        jid = sel.get("job_id")
        auth_path = root / str(sel.get("selector_authority_file") or "")
        auth_ok = bool(
            auth_path.exists()
            and sel.get("selector_authority_sha256")
            and sha256(auth_path) == sel.get("selector_authority_sha256")
            and sel.get("all_selector_authority_frozen") is True
        )
        obligations = _schema_obligations(str(jid))
        unresolved = [o for o in obligations if str(o["status"]).startswith("DEFERRED_")]
        ready = [o for o in obligations if str(o["status"]).startswith("READY_")]

        d = root / OUT / "geonomics_native_parameter_preflight" / str(jid)
        pf = {
            "stage": STAGE,
            "engine": "Geonomics",
            "engine_version_required": "1.4.9",
            "job_id": jid,
            "window_id": sel.get("window_id"),
            "status":
                "R434_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT_COMPLETE_WITH_EXPLICIT_AUTHORITY_GAPS"
                if auth_ok else "BLOCKED_NATIVE_PARAMETER_PREFLIGHT_SELECTOR_AUTHORITY_INTEGRITY",
            "selector_authority_file": sel.get("selector_authority_file"),
            "selector_authority_sha256": sel.get("selector_authority_sha256"),
            "selector_authority_hash_match": auth_ok,
            "geonomics_native_schema_obligations": obligations,
            "unresolved_authority_gap_count": len(unresolved),
            "ready_obligation_count": len(ready),
            "all_authority_gaps_explicit": True,
            "native_geonomics_params_file": None,
            "native_geonomics_params_materialized_in_r434": False,
            "gnx_read_parameters_file_performed": False,
            "gnx_make_model_performed": False,
            "scientific_execution_performed": False,
            "default_parameter_values_used": False,
            "random_spatial_initialization_used": False,
            "automatic_layer_rescaling_used": False,
            "canonical_state_changed": False,
        }
        p = d / "GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT.json"
        write(p, pf)
        rows.append({
            "job_id": jid,
            "window_id": sel.get("window_id"),
            "preflight_file": p.relative_to(root).as_posix(),
            "preflight_sha256": sha256(p),
            "selector_authority_hash_match": auth_ok,
            "unresolved_authority_gap_count": len(unresolved),
            "ready_obligation_count": len(ready),
            "all_authority_gaps_explicit": True,
            "native_params_materialized": False,
            "preflight_pass": auth_ok,
        })

    passed = sum(bool(r["preflight_pass"]) for r in rows)
    gaps = sum(int(r["unresolved_authority_gap_count"]) for r in rows)
    return {
        "stage": STAGE,
        "status":
            "R434_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT_COMPLETE"
            if len(rows) == 3 and passed == 3 else BLOCKED,
        "record_count": len(rows),
        "preflight_pass_count": passed,
        "explicit_unresolved_authority_gap_count": gaps,
        "native_geonomics_params_materialized_count": 0,
        "gnx_read_parameters_file_performed_count": 0,
        "gnx_make_model_performed_count": 0,
        "geonomics_scientific_execution_performed": False,
        "default_parameter_values_used": False,
        "records": rows,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    ps = load(root / PSEAL)
    pa = load(root / PAUDIT)
    pt = load(root / PTARGET)
    pr = load(root / PRUNTIME)
    pp = load(root / PPLAN)

    sel = freeze_runtime_selector_authority(root, pr)
    write(root / OUT / "R4_34_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE.json", sel)

    pf = native_parameter_materialization_preflight(root, sel)
    write(root / OUT / "R4_34_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT.json", pf)

    checks = [
        Check(
            "parent_r433_sealed",
            ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED",
            ps.get("status"),
        ),
        Check(
            "parent_r433_complete",
            pa.get("status") == PARENT_COMPLETE and pa.get("checks_failed") == 0,
            pa.get("status"),
        ),
        Check(
            "parent_next_action_matches_r434",
            pa.get("next_action") == PARENT_NEXT and ps.get("next_action") == PARENT_NEXT,
            {"audit": pa.get("next_action"), "seal": ps.get("next_action")},
        ),
        Check(
            "parent_r434_plan_frozen",
            pp.get("status") == "R433_STATIC_ADJUDICATION_AND_RUNTIME_BINDING_PREFLIGHT_EVIDENCE_FROZEN",
            pp.get("status"),
        ),
        Check(
            "parent_target_accounting_57_preserved",
            pt.get("record_count") == 57 and pt.get("blocked_count") == 0,
            {"records": pt.get("record_count"), "blocked": pt.get("blocked_count")},
        ),
        Check(
            "parent_target_static_state_4_1_39_12_1_preserved",
            pt.get("exact_source_identity_future_numeric_execution_candidate_count") == 4
            and pt.get("source_identity_authority_gap_deferred_count") == 1
            and pt.get("catalog_extension_rule_selection_deferred_count") == 39
            and pt.get("observable_binding_exact_source_deferred_count") == 12
            and pt.get("primary_mapping_authority_frozen_count") == 1,
        ),
        Check(
            "parent_three_runtime_binding_packages_compiled",
            pr.get("record_count") == 3
            and pr.get("runtime_parameter_binding_package_compiled_count") == 3,
            pr.get("runtime_parameter_binding_package_compiled_count"),
        ),
        Check(
            "parent_no_native_params_or_make_model",
            pr.get("native_geonomics_params_materialized_count") == 0
            and pr.get("runtime_make_model_validation_performed_count") == 0,
        ),
        Check(
            "policy_frozen",
            cfg.get("policy")
            == "FROZEN_POST_R433_PRE_NATIVE_GEONOMICS_PARAMS_AND_PRE_MODEL_CONSTRUCTION",
            cfg.get("policy"),
        ),
        Check(
            "exact_three_selector_authority_records",
            sel.get("record_count") == 3,
            sel.get("record_count"),
        ),
        Check(
            "all_three_selector_authorities_frozen_pre_result",
            sel.get("selector_authority_frozen_job_count") == 3
            and sel.get("selector_authority_blocked_job_count") == 0,
            {
                "frozen": sel.get("selector_authority_frozen_job_count"),
                "blocked": sel.get("selector_authority_blocked_job_count"),
            },
        ),
        Check(
            "selector_parent_packages_hash_bound",
            all(
                r.get("parent_runtime_binding_package_hash_match") is True
                for r in sel.get("records") or []
            ),
        ),
        Check(
            "no_single_best_member_selection",
            cfg.get("single_best_member_selection_forbidden") is True
            and sel.get("result_selected_selector_used") is False,
        ),
        Check(
            "exhaustive_nonadjudicative_enumeration_authorized",
            all(
                load(root / r["selector_authority_file"]).get("exhaustive_enumeration_only") is True
                for r in sel.get("records") or []
            ),
        ),
        Check(
            "majority_vote_forbidden",
            cfg.get("majority_vote_forbidden") is True
            and sel.get("majority_vote_performed") is False,
        ),
        Check(
            "j21_cross_layer_numeric_fusion_forbidden",
            cfg.get("cross_layer_numeric_mixing_forbidden") is True,
        ),
        Check(
            "exact_three_native_materialization_preflights",
            pf.get("record_count") == 3,
            pf.get("record_count"),
        ),
        Check(
            "all_three_native_materialization_preflights_complete",
            pf.get("preflight_pass_count") == 3,
            pf.get("preflight_pass_count"),
        ),
        Check(
            "native_schema_authority_gaps_explicit_not_defaulted",
            pf.get("explicit_unresolved_authority_gap_count", 0) > 0
            and pf.get("default_parameter_values_used") is False,
            pf.get("explicit_unresolved_authority_gap_count"),
        ),
        Check(
            "native_params_not_materialized_before_schema_adapter_authority",
            pf.get("native_geonomics_params_materialized_count") == 0,
            pf.get("native_geonomics_params_materialized_count"),
        ),
        Check(
            "gnx_read_parameters_file_not_performed",
            pf.get("gnx_read_parameters_file_performed_count") == 0,
        ),
        Check(
            "gnx_make_model_not_performed",
            pf.get("gnx_make_model_performed_count") == 0,
        ),
        Check(
            "no_geonomics_scientific_execution",
            pf.get("geonomics_scientific_execution_performed") is False
            and cfg.get("geonomics_execution_performed") is False,
        ),
        Check(
            "no_target_numeric_execution",
            cfg.get("target_numeric_execution_performed") is False,
        ),
        Check(
            "no_readjudication",
            cfg.get("readjudication_performed") is False,
        ),
        Check(
            "canonical_state_unchanged",
            cfg.get("canonical_state_changed") is False,
        ),
        Check(
            "deep_off",
            cfg.get("deep_biological_coupling") is False,
        ),
        Check(
            "result_selected_transform_forbidden",
            cfg.get("result_selected_transform_forbidden") is True,
        ),
        Check(
            "random_spatial_initialization_forbidden",
            cfg.get("random_spatial_initialization_forbidden") is True,
        ),
        Check(
            "automatic_layer_rescaling_forbidden",
            cfg.get("automatic_layer_rescaling_forbidden") is True,
        ),
        Check(
            "deferred_p2_two_preserved",
            pa.get("active_deferred_p2_cell_count") == 2,
            pa.get("active_deferred_p2_cell_count"),
        ),
        Check(
            "proxy_context_two_preserved",
            pa.get("proxy_context_only_count") == 2,
            pa.get("proxy_context_only_count"),
        ),
        Check(
            "p3_backlog_six_preserved",
            pa.get("p3_backlog_cell_count") == 6,
            pa.get("p3_backlog_cell_count"),
        ),
    ]

    ok = all(c.passed for c in checks)

    plan = {
        "stage": STAGE,
        "status":
            "R434_SELECTOR_AUTHORITY_AND_NATIVE_PARAMETER_PREFLIGHT_EVIDENCE_FROZEN"
            if ok else BLOCKED,
        "geonomics_selector_authority_frozen_job_count":
            sel.get("selector_authority_frozen_job_count"),
        "geonomics_native_parameter_preflight_pass_count":
            pf.get("preflight_pass_count"),
        "geonomics_native_schema_explicit_authority_gap_count":
            pf.get("explicit_unresolved_authority_gap_count"),
        "native_geonomics_params_materialized_count": 0,
        "gnx_read_parameters_file_authorized_in_r434": False,
        "gnx_make_model_authorized_in_r434": False,
        "geonomics_execution_authorized_in_r434": False,
        "target_numeric_execution_authorized_in_r434": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R434_SELECTOR_AUTHORITY_OR_NATIVE_PARAMETER_PREFLIGHT",
    }
    write(root / OUT / "R4_34_R435_EXECUTION_PLAN.json", plan)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "target_authority_binding_record_count": 57,
        "geonomics_selector_authority_frozen_job_count":
            sel.get("selector_authority_frozen_job_count"),
        "geonomics_native_parameter_preflight_pass_count":
            pf.get("preflight_pass_count"),
        "geonomics_native_schema_explicit_authority_gap_count":
            pf.get("explicit_unresolved_authority_gap_count"),
        "native_geonomics_params_materialized_count": 0,
        "gnx_read_parameters_file_performed": False,
        "gnx_make_model_performed": False,
        "geonomics_execution_ready": False,
        "external_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_34_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    ps = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_34_INTEGRATED_AUDIT.json") if (
        root / OUT / "R4_34_INTEGRATED_AUDIT.json"
    ).exists() else {}
    sel = load(root / OUT / "R4_34_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE.json") if (
        root / OUT / "R4_34_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE.json"
    ).exists() else {}
    pf = load(root / OUT / "R4_34_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT.json") if (
        root / OUT / "R4_34_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT.json"
    ).exists() else {}
    plan = load(root / OUT / "R4_34_R435_EXECUTION_PLAN.json") if (
        root / OUT / "R4_34_R435_EXECUTION_PLAN.json"
    ).exists() else {}

    checks = [
        Check("parent_r433_sealed", ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED"),
        Check("r434_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r434_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check(
            "three_selector_authorities_frozen",
            sel.get("record_count") == 3
            and sel.get("selector_authority_frozen_job_count") == 3
            and sel.get("selector_authority_blocked_job_count") == 0,
        ),
        Check(
            "selector_authorities_hash_bound",
            all(r.get("parent_runtime_binding_package_hash_match") is True for r in sel.get("records") or []),
        ),
        Check("no_result_selected_selector", sel.get("result_selected_selector_used") is False),
        Check("no_majority_vote", sel.get("majority_vote_performed") is False),
        Check(
            "three_native_parameter_preflights_complete",
            pf.get("record_count") == 3 and pf.get("preflight_pass_count") == 3,
        ),
        Check(
            "native_schema_gaps_explicit",
            pf.get("explicit_unresolved_authority_gap_count", 0) > 0,
            pf.get("explicit_unresolved_authority_gap_count"),
        ),
        Check(
            "native_params_not_materialized",
            pf.get("native_geonomics_params_materialized_count") == 0,
        ),
        Check(
            "read_parameters_file_not_performed",
            pf.get("gnx_read_parameters_file_performed_count") == 0,
        ),
        Check("make_model_not_performed", pf.get("gnx_make_model_performed_count") == 0),
        Check(
            "geonomics_execution_not_performed",
            pf.get("geonomics_scientific_execution_performed") is False,
        ),
        Check(
            "r435_plan_frozen",
            plan.get("status") == "R434_SELECTOR_AUTHORITY_AND_NATIVE_PARAMETER_PREFLIGHT_EVIDENCE_FROZEN",
            plan.get("status"),
        ),
        Check(
            "geonomics_execution_not_authorized",
            plan.get("geonomics_execution_authorized_in_r434") is False,
        ),
        Check(
            "target_numeric_execution_not_authorized",
            plan.get("target_numeric_execution_authorized_in_r434") is False,
        ),
        Check("no_external_engine_execution", a.get("external_engine_execution_performed") is False),
        Check("no_target_numeric_execution", a.get("target_numeric_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("deferred_p2_two", a.get("active_deferred_p2_cell_count") == 2),
        Check("proxy_context_two", a.get("proxy_context_only_count") == 2),
        Check("p3_backlog_six", a.get("p3_backlog_cell_count") == 6),
        Check("next_action_present", a.get("next_action") == NEXT, a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
            "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "target_authority_binding_record_count": 57,
            "geonomics_selector_authority_frozen_job_count":
                sel.get("selector_authority_frozen_job_count"),
            "geonomics_native_parameter_preflight_pass_count":
                pf.get("preflight_pass_count"),
            "geonomics_native_schema_explicit_authority_gap_count":
                pf.get("explicit_unresolved_authority_gap_count"),
            "native_geonomics_params_materialized_count": 0,
            "gnx_read_parameters_file_performed": False,
            "gnx_make_model_performed": False,
            "geonomics_execution_authorized": False,
            "external_engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
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
