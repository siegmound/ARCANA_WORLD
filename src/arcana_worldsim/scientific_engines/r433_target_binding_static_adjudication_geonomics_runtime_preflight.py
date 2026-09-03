from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json

import numpy as np

STAGE = "v0.6D1-R4.33"

PARENT_COMPLETE = (
    "PASS_R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_"
    "CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_"
    "CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION_SEALED"
)
PARENT_NEXT = (
    "BUILD_R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_"
    "GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT"
)

COMPLETE = (
    "PASS_R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_"
    "GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_"
    "GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R433_PARENT_BINDING_ADJUDICATION_OR_GEONOMICS_"
    "RUNTIME_PARAMETER_COMPILATION_PREFLIGHT_FAILURE"
)

NEXT = (
    "BUILD_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
    "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT"
)

CFG = Path(
    "configs/world1_r433_target_binding_static_adjudication_"
    "geonomics_runtime_parameter_compilation_preflight_v0_6D1_R4_33.json"
)
PSEAL = Path("outputs/v0_6D1_R4_32_SEAL/R4_32_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_32/R4_32_INTEGRATED_AUDIT.json")
PTB = Path(
    "outputs/v0_6D1_R4_32/"
    "R4_32_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_REGISTRY.json"
)
PGEO = Path(
    "outputs/v0_6D1_R4_32/"
    "R4_32_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_REGISTRY.json"
)
PPLAN = Path("outputs/v0_6D1_R4_32/R4_32_R433_EXECUTION_PLAN.json")

OUT = Path("outputs/v0_6D1_R4_33")
SEAL = Path("outputs/v0_6D1_R4_33_SEAL/R4_33_FINAL_SEAL_AUDIT.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"
GEONOMICS_JOBS = (J14, J18, J21)

MAPPING_KEYS = (
    "time_mapping",
    "space_mapping",
    "population_mapping",
    "domain_mapping",
    "uncertainty_mapping",
)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None

    def d(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pass": bool(self.passed),
            "detail": self.detail,
        }


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


def _binding_kind_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for rec in records:
        k = str(rec.get("binding_kind") or "MISSING")
        out[k] = out.get(k, 0) + 1
    return out


def _static_adjudicate_target_bindings(parent: dict[str, Any]) -> dict[str, Any]:
    """Adjudicate authority state only; never create a target value or selector.

    R4.33 is intentionally conservative:
    - an already frozen exact-source identity may become an execution *candidate*,
      but execution remains unauthorized;
    - a pending source identity remains pending;
    - catalog extensions do not choose a rule;
    - target-design observable bindings do not bind an exact source;
    - the primary mapping authority does not change mapping class or numeric value.
    """
    rows: list[dict[str, Any]] = []
    blocked = 0
    exact_source_candidates = 0
    source_pending = 0
    catalog_deferred = 0
    design_deferred = 0
    primary_frozen = 0

    for src in parent.get("records") or []:
        rec = {
            "stage": STAGE,
            "window_id": src.get("window_id"),
            "domain": src.get("domain"),
            "binding_kind": src.get("binding_kind"),
            "parent_binding_disposition": src.get("binding_disposition"),
            "parent_implementation_ready": src.get("implementation_ready"),
            "numeric_target_execution_authorized_in_r433": False,
            "result_selected_selector_used": False,
            "result_selected_transform_used": False,
            "comparison_result_used_to_define_authority": False,
        }
        kind = str(src.get("binding_kind") or "")
        disp = str(src.get("binding_disposition") or "")
        ready = src.get("implementation_ready") is True

        if kind == "AUTHORIZED_SELECTOR_SOURCE_IDENTITY":
            if ready and "FROZEN" in disp and "PENDING" not in disp:
                rec.update({
                    "static_adjudication_disposition":
                        "EXACT_SOURCE_IDENTITY_AUTHORITY_STATIC_ADJUDICATED_"
                        "FUTURE_NUMERIC_EXECUTION_CANDIDATE_ONLY",
                    "future_numeric_execution_candidate": True,
                    "authority_gap_preserved": False,
                })
                exact_source_candidates += 1
            elif "PENDING" in disp or not ready:
                rec.update({
                    "static_adjudication_disposition":
                        "SOURCE_IDENTITY_AUTHORITY_GAP_STATIC_ADJUDICATED_DEFERRED",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                source_pending += 1
            else:
                rec.update({
                    "static_adjudication_disposition":
                        "BLOCKED_UNRECOGNIZED_SOURCE_IDENTITY_STATE",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                blocked += 1

        elif kind == "PRE_RESULT_SELECTOR_RULE_CATALOG_EXTENSION":
            ok = ready and src.get("selector_chosen_in_r432") in (None, False)
            if ok:
                rec.update({
                    "static_adjudication_disposition":
                        "CATALOG_EXTENSION_AUTHORITY_STATIC_ADJUDICATED_"
                        "RULE_SELECTION_STILL_PENDING",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                catalog_deferred += 1
            else:
                rec.update({
                    "static_adjudication_disposition":
                        "BLOCKED_CATALOG_EXTENSION_AUTHORITY_DRIFT_OR_SELECTOR_LEAKAGE",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                blocked += 1

        elif kind == "TARGET_DESIGN_OBSERVABLE_BINDING":
            if ready:
                rec.update({
                    "static_adjudication_disposition":
                        "OBSERVABLE_BINDING_CONTRACT_STATIC_ADJUDICATED_"
                        "EXACT_SOURCE_BINDING_PENDING",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                design_deferred += 1
            else:
                rec.update({
                    "static_adjudication_disposition":
                        "BLOCKED_TARGET_DESIGN_OBSERVABLE_BINDING_DRIFT",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                blocked += 1

        elif kind == "PRIMARY_MAPPING_AUTHORITY_DEFINITION":
            ok = (
                ready
                and src.get("mapping_class_change_authorized") is False
                and src.get("numeric_value_change_authorized") is False
            )
            if ok:
                rec.update({
                    "static_adjudication_disposition":
                        "PRIMARY_MAPPING_AUTHORITY_STATIC_ADJUDICATED_"
                        "MAPPING_CLASS_AND_NUMERIC_VALUE_FROZEN",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                primary_frozen += 1
            else:
                rec.update({
                    "static_adjudication_disposition":
                        "BLOCKED_PRIMARY_MAPPING_AUTHORITY_GOVERNANCE_DRIFT",
                    "future_numeric_execution_candidate": False,
                    "authority_gap_preserved": True,
                })
                blocked += 1
        else:
            rec.update({
                "static_adjudication_disposition":
                    "BLOCKED_UNKNOWN_R432_BINDING_KIND",
                "future_numeric_execution_candidate": False,
                "authority_gap_preserved": True,
            })
            blocked += 1

        rows.append(rec)

    return {
        "stage": STAGE,
        "status":
            "R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_COMPLETE"
            if len(rows) == 57 and blocked == 0 else BLOCKED,
        "record_count": len(rows),
        "blocked_count": blocked,
        "binding_kind_counts": _binding_kind_counts(rows),
        "exact_source_identity_future_numeric_execution_candidate_count":
            exact_source_candidates,
        "source_identity_authority_gap_deferred_count": source_pending,
        "catalog_extension_rule_selection_deferred_count": catalog_deferred,
        "observable_binding_exact_source_deferred_count": design_deferred,
        "primary_mapping_authority_frozen_count": primary_frozen,
        "numeric_target_execution_authorized_count": 0,
        "numeric_target_execution_performed": False,
        "readjudication_performed": False,
        "records": rows,
    }


def _safe_scalar_list(arr: np.ndarray) -> list[Any] | None:
    if arr.ndim != 1 or arr.size > 64:
        return None
    k = arr.dtype.kind
    if k not in "biufUS":
        return None
    vals = arr.tolist()
    out: list[Any] = []
    for v in vals:
        if isinstance(v, bytes):
            out.append(v.decode("utf-8", errors="replace"))
        elif isinstance(v, np.generic):
            out.append(v.item())
        else:
            out.append(v)
    return out


def _npz_inventory(path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with np.load(path, allow_pickle=False) as z:
        for key in sorted(z.files):
            arr = z[key]
            row = {
                "key": key,
                "shape": list(arr.shape),
                "dtype": str(arr.dtype),
            }
            vals = _safe_scalar_list(arr)
            if vals is not None:
                row["axis_values_if_small"] = vals
            rows.append(row)
    return {
        "path": path.as_posix(),
        "sha256": sha256(path),
        "array_count": len(rows),
        "arrays": rows,
    }


def _selector_requirements(job_id: str, inventories: list[dict[str, Any]]) -> dict[str, Any]:
    keyset = {
        a["key"]
        for inv in inventories
        for a in (inv.get("arrays") or [])
    }

    req: list[str] = []
    if job_id == J14:
        for key in sorted(keyset):
            low = key.lower()
            if any(tok in low for tok in ("candidate", "forcing", "member", "age")):
                req.append(key)
        if not req:
            req.append("R432_UNCERTAINTY_DIMENSION_SELECTOR_BUNDLE")
    elif job_id == J18:
        for key in ("parent_member_indices", "candidate_ids", "snapshot_age_ka"):
            if key in keyset:
                req.append(key)
        if not req:
            req.append("R432_REPLAY_CANDIDATE_SELECTOR_BUNDLE")
    elif job_id == J21:
        for key in ("anchor_age_ka", "producer_taxon_ids"):
            if key in keyset:
                req.append(key)
        req += [
            "environment_layer_set",
            "producer_layer_set",
            "cross_layer_combination_policy",
        ]

    # No default is ever generated from these requirements.
    return {
        "explicit_frozen_selector_bundle_required_before_native_params": True,
        "selector_requirements": req,
        "default_selector_values": None,
        "result_selected_selector_forbidden": True,
        "comparison_target_selected_selector_forbidden": True,
    }


def _compile_geonomics_runtime_packages(
    root: Path,
    parent: dict[str, Any],
) -> dict[str, Any]:
    parent_records = {
        r.get("job_id"): r
        for r in parent.get("records") or []
    }
    records: list[dict[str, Any]] = []
    blocked = 0

    for job_id in GEONOMICS_JOBS:
        src = parent_records.get(job_id) or {}
        mapping = src.get("required_mappings") or {}
        manifest_rel = src.get("canonical_parameter_manifest_file")
        manifest_path = root / str(manifest_rel or "")
        manifest_hash = src.get("canonical_parameter_manifest_sha256")

        manifest_ok = bool(
            src.get("static_parameter_manifest_valid") is True
            and manifest_rel
            and manifest_path.exists()
            and manifest_hash
            and sha256(manifest_path) == manifest_hash
        )

        source_rows: list[dict[str, Any]] = []
        inventories: list[dict[str, Any]] = []
        source_ok = True
        for s in src.get("sources") or []:
            rel = s.get("path")
            p = root / str(rel or "")
            expected = s.get("sha256")
            exists = bool(rel and p.exists())
            current = sha256(p) if exists else None
            ok = bool(exists and expected and current == expected)
            source_rows.append({
                "path": rel,
                "role": s.get("role"),
                "expected_sha256": expected,
                "current_sha256": current,
                "hash_match": ok,
            })
            source_ok = source_ok and ok
            if ok and p.suffix.lower() == ".npz":
                inv = _npz_inventory(p)
                inv["path"] = rel
                inventories.append(inv)

        mapping_ok = (
            set(mapping.keys()) == set(MAPPING_KEYS)
            and all(isinstance(mapping.get(k), str) and mapping.get(k).strip()
                    for k in MAPPING_KEYS)
        )

        selector = _selector_requirements(job_id, inventories)
        package = {
            "stage": STAGE,
            "engine": "Geonomics",
            "engine_version_required": "1.4.9",
            "job_id": job_id,
            "window_id": src.get("window_id"),
            "package_status":
                "RUNTIME_PARAMETER_BINDING_PACKAGE_COMPILED_"
                "SELECTOR_AUTHORITY_REQUIRED_BEFORE_NATIVE_PARAMS"
                if manifest_ok and source_ok and mapping_ok
                else "BLOCKED_RUNTIME_PARAMETER_BINDING_PACKAGE_INPUT_INTEGRITY",
            "parent_static_parameter_manifest_file": manifest_rel,
            "parent_static_parameter_manifest_sha256": manifest_hash,
            "parent_static_parameter_manifest_hash_match": manifest_ok,
            "source_authority_kind": src.get("source_authority_kind"),
            "canonical_sources": source_rows,
            "canonical_source_inventories": inventories,
            "mapping_fields": mapping,
            "selector_authority": selector,
            "native_geonomics_params_file": None,
            "native_geonomics_params_materialized_in_r433": False,
            "runtime_make_model_validation_performed": False,
            "runtime_make_model_authorized_in_r433": False,
            "geonomics_scientific_execution_authorized_in_r433": False,
            "geonomics_scientific_execution_performed": False,
            "default_model_used": False,
            "comparison_target_used": False,
            "canonical_write": False,
            "cross_layer_numeric_mixing_performed": False,
        }

        d = root / OUT / "geonomics_runtime" / job_id
        package_path = d / "GEONOMICS_RUNTIME_PARAMETER_BINDING_PACKAGE.json"
        write(package_path, package)
        ok = manifest_ok and source_ok and mapping_ok
        if not ok:
            blocked += 1

        records.append({
            "job_id": job_id,
            "window_id": src.get("window_id"),
            "runtime_parameter_binding_package_file":
                package_path.relative_to(root).as_posix(),
            "runtime_parameter_binding_package_sha256": sha256(package_path),
            "input_static_manifest_hash_match": manifest_ok,
            "all_canonical_source_hashes_match": source_ok,
            "five_mapping_classes_complete": mapping_ok,
            "explicit_selector_authority_required":
                selector["explicit_frozen_selector_bundle_required_before_native_params"],
            "native_geonomics_params_materialized": False,
            "runtime_make_model_validation_performed": False,
            "geonomics_execution_authorized": False,
            "package_compile_pass": ok,
        })

    passed = sum(bool(r["package_compile_pass"]) for r in records)
    return {
        "stage": STAGE,
        "status":
            "R433_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT_COMPLETE"
            if len(records) == 3 and passed == 3 and blocked == 0 else BLOCKED,
        "record_count": len(records),
        "runtime_parameter_binding_package_compiled_count": passed,
        "runtime_parameter_binding_package_blocked_count": blocked,
        "native_geonomics_params_materialized_count": 0,
        "runtime_selector_authority_required_count":
            sum(bool(r["explicit_selector_authority_required"]) for r in records),
        "runtime_make_model_validation_performed_count": 0,
        "geonomics_execution_authorized_count": 0,
        "geonomics_execution_performed": False,
        "default_model_used": False,
        "records": records,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    ps = load(root / PSEAL)
    pa = load(root / PAUDIT)
    ptb = load(root / PTB)
    pgeo = load(root / PGEO)
    pp = load(root / PPLAN)

    tb = _static_adjudicate_target_bindings(ptb)
    write(root / OUT / "R4_33_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION.json", tb)

    gp = _compile_geonomics_runtime_packages(root, pgeo)
    write(root / OUT / "R4_33_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT.json", gp)

    checks = [
        Check(
            "parent_r432_sealed",
            ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED",
            ps.get("status"),
        ),
        Check(
            "parent_r432_complete",
            pa.get("status") == PARENT_COMPLETE and pa.get("checks_failed") == 0,
            pa.get("status"),
        ),
        Check(
            "parent_next_action_matches_r433",
            pa.get("next_action") == PARENT_NEXT and ps.get("next_action") == PARENT_NEXT,
            {"audit": pa.get("next_action"), "seal": ps.get("next_action")},
        ),
        Check(
            "parent_r433_runtime_compilation_authorized",
            pp.get("geonomics_runtime_parameter_compilation_authorized_for_r433") is True,
            pp.get("geonomics_runtime_parameter_compilation_authorized_for_r433"),
        ),
        Check(
            "parent_target_binding_exact_57",
            ptb.get("record_count") == 57,
            ptb.get("record_count"),
        ),
        Check(
            "parent_geonomics_exact_three_static_valid",
            pgeo.get("record_count") == 3
            and pgeo.get("static_valid_count") == 3,
            {"records": pgeo.get("record_count"), "valid": pgeo.get("static_valid_count")},
        ),
        Check(
            "policy_frozen",
            cfg.get("policy")
            == "FROZEN_POST_R432_PRE_NUMERIC_TARGET_EXECUTION_PRE_NATIVE_GEONOMICS_PARAMETER_MATERIALIZATION",
            cfg.get("policy"),
        ),
        Check(
            "target_static_adjudication_exact_57",
            tb.get("record_count") == 57,
            tb.get("record_count"),
        ),
        Check(
            "target_static_adjudication_zero_blocks",
            tb.get("blocked_count") == 0,
            tb.get("blocked_count"),
        ),
        Check(
            "source_identity_four_exact_candidates_preserved",
            tb.get("exact_source_identity_future_numeric_execution_candidate_count") == 4,
            tb.get("exact_source_identity_future_numeric_execution_candidate_count"),
        ),
        Check(
            "source_identity_one_authority_gap_preserved",
            tb.get("source_identity_authority_gap_deferred_count") == 1,
            tb.get("source_identity_authority_gap_deferred_count"),
        ),
        Check(
            "catalog_extension_39_rule_selection_deferred",
            tb.get("catalog_extension_rule_selection_deferred_count") == 39,
            tb.get("catalog_extension_rule_selection_deferred_count"),
        ),
        Check(
            "observable_binding_12_exact_source_deferred",
            tb.get("observable_binding_exact_source_deferred_count") == 12,
            tb.get("observable_binding_exact_source_deferred_count"),
        ),
        Check(
            "primary_mapping_one_frozen",
            tb.get("primary_mapping_authority_frozen_count") == 1,
            tb.get("primary_mapping_authority_frozen_count"),
        ),
        Check(
            "target_numeric_execution_not_authorized",
            tb.get("numeric_target_execution_authorized_count") == 0,
            tb.get("numeric_target_execution_authorized_count"),
        ),
        Check(
            "geonomics_exact_three_runtime_binding_packages",
            gp.get("record_count") == 3,
            gp.get("record_count"),
        ),
        Check(
            "geonomics_all_three_runtime_binding_packages_compiled",
            gp.get("runtime_parameter_binding_package_compiled_count") == 3
            and gp.get("runtime_parameter_binding_package_blocked_count") == 0,
            gp.get("runtime_parameter_binding_package_compiled_count"),
        ),
        Check(
            "geonomics_all_package_inputs_hash_bound",
            all(
                r.get("input_static_manifest_hash_match") is True
                and r.get("all_canonical_source_hashes_match") is True
                for r in gp.get("records") or []
            ),
        ),
        Check(
            "geonomics_five_mapping_classes_preserved",
            all(r.get("five_mapping_classes_complete") is True for r in gp.get("records") or []),
        ),
        Check(
            "geonomics_selector_authority_required_for_all_three",
            gp.get("runtime_selector_authority_required_count") == 3,
            gp.get("runtime_selector_authority_required_count"),
        ),
        Check(
            "no_native_geonomics_params_materialized_without_selector_authority",
            gp.get("native_geonomics_params_materialized_count") == 0,
            gp.get("native_geonomics_params_materialized_count"),
        ),
        Check(
            "gnx_make_model_not_performed_or_authorized",
            gp.get("runtime_make_model_validation_performed_count") == 0
            and all(r.get("geonomics_execution_authorized") is False for r in gp.get("records") or []),
        ),
        Check(
            "no_external_engine_execution",
            cfg.get("external_engine_execution_performed") is False
            and cfg.get("geonomics_execution_performed") is False
            and gp.get("geonomics_execution_performed") is False,
        ),
        Check(
            "no_target_numeric_execution",
            cfg.get("target_numeric_execution_performed") is False
            and tb.get("numeric_target_execution_performed") is False,
        ),
        Check(
            "no_readjudication",
            cfg.get("readjudication_performed") is False
            and tb.get("readjudication_performed") is False,
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
            "majority_vote_forbidden",
            cfg.get("majority_vote_forbidden") is True,
        ),
        Check(
            "result_selected_selector_forbidden",
            cfg.get("result_selected_selector_forbidden") is True,
        ),
        Check(
            "result_selected_transform_forbidden",
            cfg.get("result_selected_transform_forbidden") is True,
        ),
        Check(
            "default_geonomics_model_forbidden",
            cfg.get("default_geonomics_model_forbidden") is True
            and gp.get("default_model_used") is False,
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
            "R433_STATIC_ADJUDICATION_AND_RUNTIME_BINDING_PREFLIGHT_EVIDENCE_FROZEN"
            if ok else BLOCKED,
        "target_authority_binding_record_count": tb.get("record_count"),
        "exact_source_identity_future_numeric_execution_candidate_count":
            tb.get("exact_source_identity_future_numeric_execution_candidate_count"),
        "source_identity_authority_gap_deferred_count":
            tb.get("source_identity_authority_gap_deferred_count"),
        "catalog_extension_rule_selection_deferred_count":
            tb.get("catalog_extension_rule_selection_deferred_count"),
        "observable_binding_exact_source_deferred_count":
            tb.get("observable_binding_exact_source_deferred_count"),
        "primary_mapping_authority_frozen_count":
            tb.get("primary_mapping_authority_frozen_count"),
        "target_numeric_execution_authorized_in_r433": False,
        "geonomics_runtime_parameter_binding_package_compiled_count":
            gp.get("runtime_parameter_binding_package_compiled_count"),
        "geonomics_native_params_materialized_count":
            gp.get("native_geonomics_params_materialized_count"),
        "geonomics_runtime_selector_authority_required_count":
            gp.get("runtime_selector_authority_required_count"),
        "gnx_make_model_authorized_in_r433": False,
        "geonomics_execution_authorized_in_r433": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R433_STATIC_ADJUDICATION_OR_RUNTIME_BINDING_PREFLIGHT",
    }
    write(root / OUT / "R4_33_R434_EXECUTION_PLAN.json", plan)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "target_authority_binding_record_count": tb.get("record_count"),
        "exact_source_identity_future_numeric_execution_candidate_count":
            tb.get("exact_source_identity_future_numeric_execution_candidate_count"),
        "source_identity_authority_gap_deferred_count":
            tb.get("source_identity_authority_gap_deferred_count"),
        "catalog_extension_rule_selection_deferred_count":
            tb.get("catalog_extension_rule_selection_deferred_count"),
        "observable_binding_exact_source_deferred_count":
            tb.get("observable_binding_exact_source_deferred_count"),
        "primary_mapping_authority_frozen_count":
            tb.get("primary_mapping_authority_frozen_count"),
        "geonomics_runtime_parameter_binding_package_compiled_count":
            gp.get("runtime_parameter_binding_package_compiled_count"),
        "geonomics_native_params_materialized_count":
            gp.get("native_geonomics_params_materialized_count"),
        "geonomics_runtime_selector_authority_required_count":
            gp.get("runtime_selector_authority_required_count"),
        "gnx_make_model_validation_performed": False,
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
    write(root / OUT / "R4_33_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    ps = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_33_INTEGRATED_AUDIT.json") if (
        root / OUT / "R4_33_INTEGRATED_AUDIT.json"
    ).exists() else {}
    tb = load(root / OUT / "R4_33_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION.json") if (
        root / OUT / "R4_33_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION.json"
    ).exists() else {}
    gp = load(root / OUT / "R4_33_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT.json") if (
        root / OUT / "R4_33_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT.json"
    ).exists() else {}
    plan = load(root / OUT / "R4_33_R434_EXECUTION_PLAN.json") if (
        root / OUT / "R4_33_R434_EXECUTION_PLAN.json"
    ).exists() else {}

    checks = [
        Check(
            "parent_r432_sealed",
            ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED",
        ),
        Check("r433_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r433_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check(
            "target_static_adjudication_exact_57_zero_blocks",
            tb.get("record_count") == 57 and tb.get("blocked_count") == 0,
            {"records": tb.get("record_count"), "blocked": tb.get("blocked_count")},
        ),
        Check(
            "source_identity_4_exact_plus_1_gap",
            tb.get("exact_source_identity_future_numeric_execution_candidate_count") == 4
            and tb.get("source_identity_authority_gap_deferred_count") == 1,
        ),
        Check(
            "catalog_extension_39_preserved",
            tb.get("catalog_extension_rule_selection_deferred_count") == 39,
        ),
        Check(
            "observable_binding_12_preserved",
            tb.get("observable_binding_exact_source_deferred_count") == 12,
        ),
        Check(
            "primary_mapping_one_preserved",
            tb.get("primary_mapping_authority_frozen_count") == 1,
        ),
        Check(
            "target_numeric_execution_still_not_authorized",
            tb.get("numeric_target_execution_authorized_count") == 0,
        ),
        Check(
            "geonomics_three_runtime_binding_packages_compiled",
            gp.get("record_count") == 3
            and gp.get("runtime_parameter_binding_package_compiled_count") == 3,
        ),
        Check(
            "geonomics_runtime_packages_hash_bound_to_parent_and_sources",
            all(
                r.get("input_static_manifest_hash_match") is True
                and r.get("all_canonical_source_hashes_match") is True
                for r in gp.get("records") or []
            ),
        ),
        Check(
            "geonomics_five_mapping_classes_preserved",
            all(r.get("five_mapping_classes_complete") is True for r in gp.get("records") or []),
        ),
        Check(
            "selector_authority_required_before_native_params",
            gp.get("runtime_selector_authority_required_count") == 3,
        ),
        Check(
            "native_params_not_materialized",
            gp.get("native_geonomics_params_materialized_count") == 0,
        ),
        Check(
            "make_model_not_performed",
            gp.get("runtime_make_model_validation_performed_count") == 0,
        ),
        Check(
            "geonomics_execution_not_authorized",
            gp.get("geonomics_execution_authorized_count") == 0
            and plan.get("geonomics_execution_authorized_in_r433") is False,
        ),
        Check(
            "r434_plan_frozen",
            plan.get("status")
            == "R433_STATIC_ADJUDICATION_AND_RUNTIME_BINDING_PREFLIGHT_EVIDENCE_FROZEN",
            plan.get("status"),
        ),
        Check(
            "no_external_engine_execution",
            a.get("external_engine_execution_performed") is False,
        ),
        Check(
            "no_target_numeric_execution",
            a.get("target_numeric_execution_performed") is False,
        ),
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
            "FINAL_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_"
            "GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "target_authority_binding_record_count": tb.get("record_count"),
            "exact_source_identity_future_numeric_execution_candidate_count":
                tb.get("exact_source_identity_future_numeric_execution_candidate_count"),
            "source_identity_authority_gap_deferred_count":
                tb.get("source_identity_authority_gap_deferred_count"),
            "catalog_extension_rule_selection_deferred_count":
                tb.get("catalog_extension_rule_selection_deferred_count"),
            "observable_binding_exact_source_deferred_count":
                tb.get("observable_binding_exact_source_deferred_count"),
            "primary_mapping_authority_frozen_count":
                tb.get("primary_mapping_authority_frozen_count"),
            "geonomics_runtime_parameter_binding_package_compiled_count":
                gp.get("runtime_parameter_binding_package_compiled_count"),
            "geonomics_native_params_materialized_count":
                gp.get("native_geonomics_params_materialized_count"),
            "geonomics_runtime_selector_authority_required_count":
                gp.get("runtime_selector_authority_required_count"),
            "gnx_make_model_validation_performed": False,
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
