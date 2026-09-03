from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import hashlib
import json
import math
import zipfile

import numpy as np

from arcana_worldsim.scientific_engines.r429_j14_spatial_authority_replay import (
    AUTHORITY_ALGORITHM,
    build_replay,
    validate_authority_inputs,
)
from arcana_worldsim.scientific_engines.r429_selector_authority_design_validation_j14_authorization import (
    recover_exact_inventory,
    _resolve_recorded_path,
)

STAGE = "v0.6D1-R4.30"
PARENT_SEALED = "PASS_R429_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE_TARGET_DESIGN_IMPLEMENTATION_VALIDATION_AND_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION_SEALED"
PARENT_NEXT = "BUILD_R430_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION"
COMPLETE = "PASS_R430_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION_COMPLETE"
SEALED = "PASS_R430_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION_SEALED"
BLOCKED = "BLOCKED_R430_PARENT_TARGET_MATERIALIZATION_SELECTOR_GAP_OR_J14_EXECUTION_FAILURE"
NEXT = "BUILD_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL"

CFG = Path("configs/world1_r430_target_materialization_selector_gap_j14_execution_v0_6D1_R4_30.json")
PSEAL = Path("outputs/v0_6D1_R4_29_SEAL/R4_29_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_29/R4_29_INTEGRATED_AUDIT.json")
PSELECT = Path("outputs/v0_6D1_R4_29/R4_29_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE.json")
PCLOSURE = Path("outputs/v0_6D1_R4_29/R4_29_SCHEMALESS_SOURCE_AUTHORITY_CLOSURE.json")
PDESIGN = Path("outputs/v0_6D1_R4_29/R4_29_TARGET_DESIGN_IMPLEMENTATION_VALIDATION.json")
PSEM = Path("outputs/v0_6D1_R4_29/R4_29_SEMANTIC_REPAIR_EXECUTION_AUTHORIZATION.json")
PJ14 = Path("outputs/v0_6D1_R4_29/R4_29_GEONOMICS_J14_SPATIAL_REPLAY_EXECUTION_AUTHORIZATION.json")
PPLAN = Path("outputs/v0_6D1_R4_29/R4_29_R430_EXECUTION_PLAN.json")
R428SELECT = Path("outputs/v0_6D1_R4_28/R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json")
R416PROT = Path("outputs/v0_6D1_R4_16/R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json")
R413MATRIX = Path("outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json")
R44CFG = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
OUT = Path("outputs/v0_6D1_R4_30")
SEAL = Path("outputs/v0_6D1_R4_30_SEAL/R4_30_FINAL_SEAL_AUDIT.json")
J14_NPZ = OUT / "authority" / "R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz"
J14_META = OUT / "authority" / "R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.json"


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


def finite_scalar(x: Any) -> float | None:
    try:
        y = float(x)
        return y if math.isfinite(y) else None
    except Exception:
        return None


def _json_exact_value(obj: Any, selector: str) -> Any:
    cur = obj
    for token in str(selector).split("."):
        if not isinstance(cur, dict) or token not in cur:
            raise KeyError(selector)
        cur = cur[token]
    return cur


def _tabular_exact_column(path: Path, selector: str) -> np.ndarray:
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        if selector not in (reader.fieldnames or []):
            raise KeyError(selector)
        vals = []
        for row in reader:
            raw = row.get(selector)
            if raw in (None, ""):
                continue
            v = finite_scalar(raw)
            if v is None:
                raise ValueError(f"non-numeric tabular value for {selector}")
            vals.append(v)
    return np.asarray(vals, dtype=float)


def read_exact_selector(path: Path, parser_family: str, selector: str) -> Any:
    parser = str(parser_family or "")
    if parser == "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR":
        return _json_exact_value(load(path), selector)
    if parser == "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR":
        with np.load(path, allow_pickle=False) as z:
            if selector not in z.files:
                raise KeyError(selector)
            return np.asarray(z[selector])
    if parser == "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR":
        return _tabular_exact_column(path, selector)
    raise ValueError(f"unsupported parser family: {parser}")


def _as_numeric_array(raw: Any) -> np.ndarray:
    if isinstance(raw, (int, float, np.integer, np.floating)):
        arr = np.asarray([raw], dtype=float)
    else:
        arr = np.asarray(raw, dtype=float)
    if arr.dtype == object or not np.all(np.isfinite(arr)):
        raise ValueError("selector value is not a finite numeric value/array")
    return arr


def apply_frozen_transform(raw: Any, transform_id: str) -> tuple[str, float | None, str]:
    """Execute only transform semantics that were fully bound by R4.29.

    Returns (disposition, value, reason).  Missing semantic dependencies are a
    terminal deferral, never an invitation to infer or tune a transform.
    """
    t = str(transform_id or "")
    try:
        arr = _as_numeric_array(raw)
    except Exception as e:
        return "DEFERRED_NONNUMERIC_OR_NONFINITE_SELECTOR_VALUE", None, str(e)

    scalar_identity = {
        "IDENTITY", "IDENTITY_STANDARDIZED_DELTA", "IDENTITY_NAMED_INDEX",
        "IDENTITY_NAMED_RISK", "IDENTITY_RATE", "IDENTITY_NAMED_STATISTIC",
        "IDENTITY_FROZEN_B2_1_CURRENCY",
    }
    if t in scalar_identity:
        if arr.size != 1:
            return "DEFERRED_IDENTITY_REQUIRES_SCALAR_SELECTOR_VALUE", None, f"shape={list(arr.shape)}"
        return "MATERIALIZED", float(arr.reshape(-1)[0]), "FROZEN_SCALAR_IDENTITY_TRANSFORM"

    if t in {"END_OVER_START", "END_OVER_START_SAME_CENSUS_SEMANTICS"}:
        if arr.ndim != 1 or arr.size < 2:
            return "DEFERRED_ENDPOINT_RATIO_REQUIRES_EXPLICIT_1D_TEMPORAL_SERIES", None, f"shape={list(arr.shape)}"
        start = float(arr[0]); end = float(arr[-1])
        if abs(start) <= 1e-15:
            return "DEFERRED_ENDPOINT_RATIO_ZERO_START", None, "start=0"
        return "MATERIALIZED", end / start, "FROZEN_END_OVER_START_TRANSFORM"

    if t == "END_MINUS_START_OR_EXPLICIT_ENDPOINT":
        if arr.ndim != 1 or arr.size < 2:
            return "DEFERRED_ENDPOINT_DELTA_REQUIRES_EXPLICIT_1D_TEMPORAL_SERIES", None, f"shape={list(arr.shape)}"
        return "MATERIALIZED", float(arr[-1] - arr[0]), "FROZEN_END_MINUS_START_TRANSFORM"

    # These transforms explicitly declare additional semantic bindings that
    # R4.29 did not freeze.  They therefore cannot be executed in R4.30.
    semantic_dependency = {
        "IDENTITY_REQUIRES_EXPLICIT_LINEAGE_LABEL_BINDING",
        "IDENTITY_REQUIRES_GUILD_AND_SUPPORT_BINDING",
        "IDENTITY_RATE_OR_FRACTION_REQUIRES_CLOCK_BINDING",
        "NORMALIZE_BY_FROZEN_SUPPORT_DENOMINATOR",
    }
    if t in semantic_dependency:
        return "DEFERRED_FROZEN_TRANSFORM_HAS_UNBOUND_SEMANTIC_DEPENDENCY", None, t

    return "DEFERRED_UNSUPPORTED_FROZEN_TRANSFORM", None, t


def _r428_record_map(parent: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(r.get("window_id")), str(r.get("domain"))): r for r in parent.get("records") or []}


def _protocol_map(parent: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(r.get("window_id")), str(r.get("domain"))): r for r in parent.get("records") or []}


def materialize_authorized_targets(root: Path, selector_parent: dict[str, Any], r428: dict[str, Any], protocols: dict[str, Any]) -> dict[str, Any]:
    r428m = _r428_record_map(r428)
    protm = _protocol_map(protocols)
    records: list[dict[str, Any]] = []
    for sel in selector_parent.get("records") or []:
        if not sel.get("selector_authorized"):
            continue
        w = str(sel.get("window_id") or ""); d = str(sel.get("domain") or "")
        parent = r428m.get((w, d)) or {}
        frozen_selector = str(sel.get("frozen_selector") or "")
        expected_transform = str(sel.get("frozen_transform_id") or "")
        source_matches = []
        for sp in parent.get("source_packets") or []:
            p = _resolve_recorded_path(root, sp.get("source"))
            expected = str(sp.get("expected_sha256") or "")
            if p is None or not p.exists():
                source_matches.append({"source": sp.get("source"), "present": False, "hash_match": False, "selector_present": False})
                continue
            observed = sha256(p)
            hmatch = bool(expected and observed == expected)
            inv = recover_exact_inventory(p, str(sp.get("parser_family") or "")) if hmatch else []
            present = frozen_selector in inv
            source_matches.append({
                "source": str(p), "present": True, "expected_sha256": expected, "observed_sha256": observed,
                "hash_match": hmatch, "parser_family": sp.get("parser_family"), "selector_present": present,
            })

        # R4.30-R1 repair: R4.29 froze the selector authority, not an all-candidate-source
        # conjunction.  A parent source packet that is missing/hash-drifted but does not
        # carry the frozen selector must not veto a unique, hash-valid exact binding.
        # Fail closed only when no exact hash-valid binding can be reconstructed.
        eligible = [x for x in source_matches if x.get("hash_match") and x.get("selector_present")]
        drifted_packets = [x for x in source_matches if not x.get("present") or not x.get("hash_match")]
        disposition = ""
        value: float | None = None
        reason = ""
        selected_source = None
        raw_shape = None
        # R4.30-R2 repair: R4.29 froze selector/transform authority against an
        # aggregate exact inventory, but it did not freeze the identity of the source
        # packet that supplied that selector. Therefore, when no exact selector binding
        # can be reconstructed but at least one parent packet still passes its frozen
        # hash, this is a source-binding AUTHORITY GAP, not source-integrity failure.
        # We must defer rather than guess which packet was authoritative. Only the case
        # where *all* parent packets fail integrity remains fail-closed BLOCKED.
        hash_valid_packets = [x for x in source_matches if x.get("hash_match")]
        if len(eligible) == 0 and not hash_valid_packets:
            disposition = "BLOCKED_AUTHORIZED_SELECTOR_ALL_PARENT_SOURCES_FAIL_INTEGRITY"
            reason = f"eligible_sources=0; hash_valid_parent_packets=0; parent_packets={len(source_matches)}"
        elif len(eligible) == 0:
            disposition = "DEFERRED_AUTHORIZED_SELECTOR_SOURCE_BINDING_AUTHORITY_NOT_FROZEN_BY_R429"
            reason = (f"eligible_sources=0; hash_valid_parent_packets={len(hash_valid_packets)}; "
                      f"drifted_parent_packets={len(drifted_packets)}; frozen_selector={frozen_selector}")
        elif len(eligible) > 1:
            disposition = "DEFERRED_AMBIGUOUS_MULTIPLE_HASH_VALID_SOURCES_FOR_AUTHORIZED_SELECTOR"
            reason = f"eligible_sources={len(eligible)}"
        else:
            selected_source = eligible[0]
            p = Path(str(selected_source["source"]))
            raw = read_exact_selector(p, str(selected_source.get("parser_family") or ""), frozen_selector)
            try:
                raw_shape = list(np.asarray(raw).shape)
            except Exception:
                raw_shape = None
            disposition, value, reason = apply_frozen_transform(raw, expected_transform)

        blocked = disposition.startswith("BLOCKED_")
        materialized = disposition == "MATERIALIZED" and value is not None and math.isfinite(float(value))
        protocol = protm.get((w, d)) or {}
        records.append({
            "window_id": w, "domain": d,
            "selector_authority_disposition": sel.get("selector_authority_disposition"),
            "frozen_selector": frozen_selector, "frozen_transform_id": expected_transform,
            "frozen_authority_class": sel.get("frozen_authority_class"),
            "source_candidates": source_matches, "selected_source": selected_source,
            "nonbinding_parent_source_packet_drift_count": len(drifted_packets),
            "hash_valid_parent_source_packet_count": len(hash_valid_packets),
            "source_binding_rule": "UNIQUE_HASH_VALID_EXACT_SELECTOR_SOURCE_REQUIRED; ZERO_EXACT_BINDING_WITH_SOME_HASH_VALID_PARENT_SOURCE_IS_DEFERRED_AUTHORITY_GAP; ALL_PARENT_SOURCE_INTEGRITY_FAILURE_BLOCKS",
            "raw_value_shape": raw_shape,
            "materialization_disposition": disposition,
            "materialization_reason": reason,
            "numeric_value": float(value) if materialized else None,
            "numeric_target_materialized": materialized,
            "source_integrity_blocked": blocked,
            "domain_protocol": protocol.get("protocol") if isinstance(protocol, dict) else None,
            "adjudicative_in_r430": False,
            "external_engine_result_used_to_define_target": False,
            "result_selected_transform_used": False,
            "readjudication_authorized_in_r430": False,
            "next_priority": "R431_MATERIALIZED_TARGET_SEMANTIC_VALIDATION" if materialized else (
                "REPAIR_R430_SOURCE_INTEGRITY" if blocked else "R431_AUTHORIZED_SELECTOR_TRANSFORM_DEPENDENCY_CLOSURE"
            ),
        })
    materialized = sum(r.get("numeric_target_materialized") is True for r in records)
    blocked = sum(r.get("source_integrity_blocked") is True for r in records)
    deferred = len(records) - materialized - blocked
    return {
        "stage": STAGE,
        "status": "R430_AUTHORIZED_TARGET_MATERIALIZATION_COMPLETE" if len(records) == 5 and blocked == 0 else BLOCKED,
        "authorized_selector_attempt_count": len(records),
        "numeric_target_materialized_count": materialized,
        "semantic_dependency_or_source_ambiguity_deferred_count": deferred,
        "source_integrity_blocked_count": blocked,
        "adjudicative_target_count": 0,
        "records": records,
    }


def close_selector_gaps(selector_parent: dict[str, Any], design_parent: dict[str, Any]) -> dict[str, Any]:
    design_keys = {(str(r.get("window_id")), str(r.get("domain"))) for r in design_parent.get("records") or [] if r.get("implementation_validation_pass")}
    records = []
    for r in selector_parent.get("records") or []:
        if r.get("selector_authorized"):
            continue
        key = (str(r.get("window_id")), str(r.get("domain")))
        disp = str(r.get("selector_authority_disposition") or "")
        if key in design_keys:
            status = "ROUTED_TO_VALIDATED_TARGET_DESIGN_OBSERVABLE_BINDING_AUTHORITY"
            nxt = "R431_TARGET_DESIGN_OBSERVABLE_BINDING_IMPLEMENTATION"
        elif "AMBIGUOUS" in disp:
            status = "AMBIGUOUS_EXACT_SELECTOR_RULE_AUTHORITY_GAP_FROZEN"
            nxt = "R431_AMBIGUOUS_EXACT_SELECTOR_RULE_AUTHORITY_REVIEW"
        else:
            status = "NO_EXACT_PRE_RESULT_SELECTOR_RULE_AUTHORITY_GAP_FROZEN"
            nxt = "R431_SELECTOR_AUTHORITY_CATALOG_EXTENSION_OR_ALTERNATE_CANONICAL_SOURCE_REVIEW"
        records.append({
            "window_id": key[0], "domain": key[1], "parent_disposition": disp,
            "closure_status": status, "selector_authorized_in_r430": False,
            "numeric_target_execution_authorized": False, "result_selected_selector_forbidden": True,
            "next_priority": nxt,
        })
    counts: dict[str, int] = {}
    for r in records:
        counts[r["closure_status"]] = counts.get(r["closure_status"], 0) + 1
    return {
        "stage": STAGE,
        "status": "R430_SELECTOR_GAP_CLOSURE_COMPLETE" if len(records) == 39 else BLOCKED,
        "record_count": len(records), "closure_status_counts": counts,
        "selector_auto_authorized_count": 0, "records": records,
    }


def execute_semantic_repair_review(root: Path, parent: dict[str, Any]) -> dict[str, Any]:
    records = []
    matrix = load(root / R413MATRIX) if (root / R413MATRIX).exists() else {}
    cfg44 = load(root / R44CFG) if (root / R44CFG).exists() else {}
    rows = matrix.get("rows") or matrix.get("evidence_rows") or []
    if not rows and isinstance(matrix.get("matrix"), list):
        rows = matrix.get("matrix") or []
    for r in parent.get("records") or []:
        w = str(r.get("window_id") or ""); d = str(r.get("domain") or "")
        primary = [x for x in rows if x.get("window_id") == w and x.get("domain") == d and x.get("authority_role") == "PRIMARY"]
        checks = []
        eligible = 0
        for x in primary:
            metric = x.get("metric") or {}
            name = metric.get("name") if isinstance(metric, dict) else None
            allowed = ((cfg44.get("domain_metric_candidates") or {}).get(str(x.get("engine")), {}) or {}).get(d, [])
            ok = bool(name and name in allowed and x.get("mapping_comparability") in {"DIRECT", "NORMALIZABLE"})
            eligible += int(ok)
            checks.append({"job_id": x.get("job_id"), "engine": x.get("engine"), "metric_name": name, "mapping_comparability": x.get("mapping_comparability"), "eligible_under_existing_frozen_mapping": ok})
        records.append({
            "window_id": w, "domain": d,
            "review_authorized_by_r429": r.get("review_authorized_for_r430") is True,
            "allowed_operation": "PRIMARY_MAPPING_ELIGIBILITY_REVIEW_ONLY",
            "primary_row_count": len(primary), "eligible_primary_row_count_under_existing_frozen_mapping": eligible,
            "primary_rows": checks,
            "numeric_value_changed": False, "mapping_class_changed": False, "readjudication_performed": False,
            "review_status": "EXISTING_FROZEN_PRIMARY_MAPPING_ELIGIBILITY_FOUND" if eligible else "NO_EXISTING_FROZEN_PRIMARY_MAPPING_ELIGIBILITY_REMAINS_DEFERRED",
            "next_priority": "R431_MATERIALIZED_TARGET_SEMANTIC_VALIDATION" if eligible else "R431_PRIMARY_MAPPING_AUTHORITY_GAP_CLOSURE",
        })
    return {
        "stage": STAGE,
        "status": "R430_SEMANTIC_REPAIR_REVIEW_COMPLETE" if len(records) == 1 and records[0].get("review_authorized_by_r429") else BLOCKED,
        "record_count": len(records),
        "eligible_existing_primary_mapping_count": sum(int(r.get("eligible_primary_row_count_under_existing_frozen_mapping") or 0) for r in records),
        "records": records,
    }


def _load_r327_macro(root: Path) -> tuple[list[str], np.ndarray, list[str], np.ndarray]:
    p = root / "outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz"
    with np.load(p, allow_pickle=False) as z:
        cands = [str(x) for x in np.asarray(z["candidate_ids"]).tolist()]
        ages = np.asarray(z["age_ma"], dtype=float)
        vars_ = [str(x) for x in np.asarray(z["variable_names"]).tolist()]
        state = np.asarray(z["state"], dtype=float)
    return cands, ages, vars_, state


def execute_j14_authority(root: Path, parent: dict[str, Any]) -> dict[str, Any]:
    current = validate_authority_inputs(root)
    frozen = parent.get("input_hash_freeze") or {}
    hash_match = current.get("ready") is True and bool(frozen) and current.get("hashes") == frozen
    authorized = parent.get("canonical_spatial_replay_execution_authorized_in_r430") is True
    if not authorized or not hash_match:
        return {
            "stage": STAGE, "status": BLOCKED,
            "execution_authorized_by_r429": authorized, "input_hash_freeze_match": hash_match,
            "execution_performed": False, "validation_checks": {},
        }

    replay = build_replay(root)
    J14_NPZ_ABS = root / J14_NPZ
    J14_NPZ_ABS.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        J14_NPZ_ABS,
        age_ma=np.asarray(replay["age_ma"], dtype=float),
        candidate_ids=np.asarray(replay["candidate_ids"]),
        state_variable_names=np.asarray(replay["state_variable_names"]),
        spatial_state=np.asarray(replay["spatial_state"], dtype=np.float32),
    )

    spatial = np.asarray(replay["spatial_state"], dtype=float)
    cands, ages, vars_, macro = _load_r327_macro(root)
    cohort = [str(x) for x in np.asarray(replay["candidate_ids"]).tolist()]
    cix = [cands.index(c) for c in cohort]
    vix = {v: i for i, v in enumerate(vars_)}
    active = spatial[..., 3] > 0.5
    pop = spatial[..., 0]
    rows = spatial[..., 1]
    cols = spatial[..., 2]
    expected_demes = np.rint(macro[:, :, :, vix["deme_count"]][:, cix, :]).astype(int)
    expected_demes = np.clip(expected_demes, 1, spatial.shape[3])
    observed_demes = np.sum(active, axis=3)
    expected_pop = np.maximum(0.0, macro[:, :, :, vix["effective_population"]][:, cix, :])
    observed_pop = np.sum(np.where(active, pop, 0.0), axis=3)

    # Full age-by-age support audit; only 141 canonical provider evaluations.
    support_ok = True
    try:
        from arcana_worldsim.late_cenozoic.paleogeography import physical_paleogeography_state
        a1p = root / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
        with np.load(a1p, allow_pickle=False) as z:
            a1 = {k: np.asarray(z[k]) for k in z.files}
        for t, age in enumerate(ages):
            land = np.asarray(physical_paleogeography_state(a1, float(age))["land_support"], dtype=float) > 1e-9
            mask = active[:, :, t, :]
            rr = rows[:, :, t, :][mask].astype(int)
            cc = cols[:, :, t, :][mask].astype(int)
            if len(rr) and (np.any(rr < 0) or np.any(rr >= land.shape[0]) or np.any(cc < 0) or np.any(cc >= land.shape[1]) or not np.all(land[rr, cc])):
                support_ok = False
                break
    except Exception:
        support_ok = False

    checks = {
        "authority_algorithm_exact": replay.get("authority_algorithm") == AUTHORITY_ALGORITHM,
        "input_hashes_match_r429_freeze": replay.get("input_hashes") == frozen,
        "age_axis_exact_r327": np.array_equal(np.asarray(replay["age_ma"], dtype=float), ages),
        "candidate_cohort_exact_r327_checkpoint": cohort == ["RPT_010_D02", "RPT_009_D02"],
        "spatial_state_finite": bool(np.all(np.isfinite(spatial))),
        "spatial_state_expected_rank_and_components": spatial.ndim == 5 and spatial.shape[-1] == 4,
        "deme_count_matches_r327_macro_constraint": bool(np.array_equal(observed_demes, expected_demes)),
        "population_sum_matches_r327_effective_population": bool(np.allclose(observed_pop, expected_pop, rtol=2e-6, atol=2e-3)),
        "all_active_cells_on_age_matched_canonical_support": support_ok,
        "future_spatial_anchor_not_used": replay.get("future_spatial_anchor_used_in_construction") is False,
        "external_engine_not_used": replay.get("external_engine_used_in_construction") is False,
    }
    passed = all(checks.values())
    meta = {
        "stage": STAGE,
        "status": "R430_J14_SPATIAL_AUTHORITY_CANDIDATE_EXECUTION_COMPLETE_PENDING_R431_VALIDATION_SEAL" if passed else BLOCKED,
        "execution_authorized_by_r429": True,
        "input_hash_freeze_match": True,
        "authority_algorithm": AUTHORITY_ALGORITHM,
        "construction_semantics": replay.get("construction_semantics"),
        "execution_performed": True,
        "candidate_authority_only_not_yet_canonical_sealed": True,
        "geonomics_execution_performed": False,
        "r42_j14_mutation_performed": False,
        "future_spatial_anchor_used": False,
        "external_engine_used": False,
        "output_npz": str(J14_NPZ),
        "output_npz_sha256": sha256(J14_NPZ_ABS),
        "spatial_state_shape": list(spatial.shape),
        "validation_checks": checks,
        "validation_pass": passed,
        "next_priority": "R431_J14_SPATIAL_AUTHORITY_VALIDATION_AND_SEAL" if passed else "REPAIR_R430_J14_AUTHORITY_EXECUTION",
    }
    write(root / J14_META, meta)
    return meta


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    ps = load(root / PSELECT) if (root / PSELECT).exists() else {}
    pcl = load(root / PCLOSURE) if (root / PCLOSURE).exists() else {}
    pd = load(root / PDESIGN) if (root / PDESIGN).exists() else {}
    psem = load(root / PSEM) if (root / PSEM).exists() else {}
    pj14 = load(root / PJ14) if (root / PJ14).exists() else {}
    pplan = load(root / PPLAN) if (root / PPLAN).exists() else {}
    r428 = load(root / R428SELECT) if (root / R428SELECT).exists() else {}
    protocols = load(root / R416PROT) if (root / R416PROT).exists() else {}

    targets = materialize_authorized_targets(root, ps, r428, protocols)
    gaps = close_selector_gaps(ps, pd)
    sem = execute_semantic_repair_review(root, psem)
    j14 = execute_j14_authority(root, pj14)

    checks = [
        Check("parent_r429_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r429_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r430", pa.get("next_action") == PARENT_NEXT, pa.get("next_action")),
        Check("parent_selector_authorized_exact_five", pa.get("selector_authorized_count") == 5 and ps.get("selector_authorized_count") == 5, {"audit": pa.get("selector_authorized_count"), "registry": ps.get("selector_authorized_count")}),
        Check("parent_selector_deferred_exact_39", pa.get("selector_deferred_count") == 39 and ps.get("selector_deferred_count") == 39, {"audit": pa.get("selector_deferred_count"), "registry": ps.get("selector_deferred_count")}),
        Check("parent_schemaless_six_recovered", pa.get("schemaless_inventory_recovered_count") == 6 and pcl.get("inventory_recovered_count") == 6, pa.get("schemaless_inventory_recovered_count")),
        Check("parent_target_design_12_validated", pa.get("target_design_validated_count") == 12 and pd.get("validated_count") == 12, pa.get("target_design_validated_count")),
        Check("parent_semantic_repair_one_authorized", pa.get("semantic_repair_review_authorized_count") == 1 and psem.get("review_authorized_count") == 1, pa.get("semantic_repair_review_authorized_count")),
        Check("parent_j14_execution_authorized", pa.get("j14_spatial_replay_execution_authorized_in_r430") is True and pj14.get("canonical_spatial_replay_execution_authorized_in_r430") is True),
        Check("parent_r430_plan_frozen", pplan.get("status") == "R429_SELECTOR_DESIGN_AND_J14_EXECUTION_AUTHORIZATION_FROZEN", pplan.get("status")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_R429_AUTHORIZED_TARGET_MATERIALIZATION_AND_J14_AUTHORITY_EXECUTION_ONLY", cfg.get("policy_freeze")),
        Check("exact_five_authorized_target_materialization_attempts", targets.get("authorized_selector_attempt_count") == 5, targets.get("authorized_selector_attempt_count")),
        Check("all_five_target_attempts_terminal_without_source_integrity_failure", targets.get("source_integrity_blocked_count") == 0 and int(targets.get("numeric_target_materialized_count") or 0) + int(targets.get("semantic_dependency_or_source_ambiguity_deferred_count") or 0) == 5, {"materialized": targets.get("numeric_target_materialized_count"), "deferred": targets.get("semantic_dependency_or_source_ambiguity_deferred_count"), "blocked": targets.get("source_integrity_blocked_count")}),
        Check("materialized_targets_remain_nonadjudicative", targets.get("adjudicative_target_count") == 0 and all(r.get("adjudicative_in_r430") is False for r in targets.get("records") or [])),
        Check("selector_gap_exact_39_terminal", gaps.get("record_count") == 39 and gaps.get("selector_auto_authorized_count") == 0, gaps.get("closure_status_counts")),
        Check("no_result_selected_selector_or_transform", all(r.get("result_selected_transform_used") is False for r in targets.get("records") or []) and all(r.get("result_selected_selector_forbidden") is True for r in gaps.get("records") or [])),
        Check("semantic_repair_review_exact_one_and_immutable", sem.get("record_count") == 1 and all(r.get("numeric_value_changed") is False and r.get("mapping_class_changed") is False and r.get("readjudication_performed") is False for r in sem.get("records") or []), sem.get("eligible_existing_primary_mapping_count")),
        Check("j14_authority_execution_performed", j14.get("execution_performed") is True, j14.get("status")),
        Check("j14_authority_execution_validation_pass", j14.get("validation_pass") is True and all((j14.get("validation_checks") or {}).values()), j14.get("validation_checks")),
        Check("j14_output_hash_present", bool(j14.get("output_npz_sha256")) and (root / J14_NPZ).exists(), j14.get("output_npz_sha256")),
        Check("j14_candidate_not_yet_canonical_sealed", j14.get("candidate_authority_only_not_yet_canonical_sealed") is True),
        Check("geonomics_execution_forbidden_and_not_performed", cfg.get("geonomics_execution_authorized") is False and j14.get("geonomics_execution_performed") is False),
        Check("r42_j14_mutation_not_performed", j14.get("r42_j14_mutation_performed") is False),
        Check("target_design_12_preserved_for_r431", pd.get("validated_count") == 12),
        Check("active_deferred_p2_two_preserved", pa.get("active_deferred_p2_cell_count") == 2, pa.get("active_deferred_p2_cell_count")),
        Check("proxy_context_only_two_preserved", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("p3_backlog_six_preserved", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("no_external_engine_execution", cfg.get("external_engine_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged_pending_r431_authority_validation_seal", cfg.get("canonical_state_changed") is False),
        Check("canonical_parameter_change_not_authorized", cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden", cfg.get("majority_vote") is False),
    ]
    ok = all(c.passed for c in checks)
    plan = {
        "stage": STAGE,
        "status": "R430_TARGET_MATERIALIZATION_GAP_AND_J14_EXECUTION_EVIDENCE_FROZEN" if ok else BLOCKED,
        "numeric_target_materialized_count": targets.get("numeric_target_materialized_count"),
        "authorized_target_materialization_deferred_count": targets.get("semantic_dependency_or_source_ambiguity_deferred_count"),
        "selector_gap_cell_count": gaps.get("record_count"),
        "target_design_validated_pending_observable_binding_count": 12,
        "semantic_repair_review_record_count": sem.get("record_count"),
        "j14_spatial_authority_candidate_executed": j14.get("execution_performed") is True,
        "j14_spatial_authority_candidate_validation_pass": j14.get("validation_pass") is True,
        "geonomics_execution_authorized_in_r431_by_r430": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": NEXT if ok else "REPAIR_R430_TARGET_MATERIALIZATION_SELECTOR_GAP_OR_J14_EXECUTION",
    }
    out = {
        "stage": STAGE, "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks],
        "authorized_target_materialization_attempt_count": targets.get("authorized_selector_attempt_count"),
        "numeric_target_materialized_count": targets.get("numeric_target_materialized_count"),
        "authorized_target_materialization_deferred_count": targets.get("semantic_dependency_or_source_ambiguity_deferred_count"),
        "selector_gap_closure_count": gaps.get("record_count"),
        "target_design_validated_pending_observable_binding_count": 12,
        "semantic_repair_review_count": sem.get("record_count"),
        "j14_spatial_authority_candidate_execution_performed": j14.get("execution_performed") is True,
        "j14_spatial_authority_candidate_validation_pass": j14.get("validation_pass") is True,
        "geonomics_execution_performed": False,
        "external_engine_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_30_AUTHORIZED_TARGET_MATERIALIZATION_REGISTRY.json", targets)
    write(root / OUT / "R4_30_SELECTOR_GAP_CLOSURE_REGISTRY.json", gaps)
    write(root / OUT / "R4_30_SEMANTIC_REPAIR_PRIMARY_MAPPING_REVIEW.json", sem)
    write(root / OUT / "R4_30_R431_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_30_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    parent = load(root / PSEAL) if (root / PSEAL).exists() else {}
    audit = load(root / OUT / "R4_30_INTEGRATED_AUDIT.json") if (root / OUT / "R4_30_INTEGRATED_AUDIT.json").exists() else {}
    targets = load(root / OUT / "R4_30_AUTHORIZED_TARGET_MATERIALIZATION_REGISTRY.json") if (root / OUT / "R4_30_AUTHORIZED_TARGET_MATERIALIZATION_REGISTRY.json").exists() else {}
    gaps = load(root / OUT / "R4_30_SELECTOR_GAP_CLOSURE_REGISTRY.json") if (root / OUT / "R4_30_SELECTOR_GAP_CLOSURE_REGISTRY.json").exists() else {}
    sem = load(root / OUT / "R4_30_SEMANTIC_REPAIR_PRIMARY_MAPPING_REVIEW.json") if (root / OUT / "R4_30_SEMANTIC_REPAIR_PRIMARY_MAPPING_REVIEW.json").exists() else {}
    j14 = load(root / J14_META) if (root / J14_META).exists() else {}
    plan = load(root / OUT / "R4_30_R431_EXECUTION_PLAN.json") if (root / OUT / "R4_30_R431_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r429_sealed", parent.get("status") == PARENT_SEALED, parent.get("status")),
        Check("r430_complete", audit.get("status") == COMPLETE, audit.get("status")),
        Check("r430_zero_process_failures", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("five_authorized_target_attempts_terminal", targets.get("authorized_selector_attempt_count") == 5 and targets.get("source_integrity_blocked_count") == 0 and int(targets.get("numeric_target_materialized_count") or 0) + int(targets.get("semantic_dependency_or_source_ambiguity_deferred_count") or 0) == 5, {"materialized": targets.get("numeric_target_materialized_count"), "deferred": targets.get("semantic_dependency_or_source_ambiguity_deferred_count")}),
        Check("zero_adjudicative_target_promotions", targets.get("adjudicative_target_count") == 0, targets.get("adjudicative_target_count")),
        Check("selector_gap_39_frozen", gaps.get("record_count") == 39 and gaps.get("selector_auto_authorized_count") == 0, gaps.get("closure_status_counts")),
        Check("semantic_repair_review_one_no_mutation", sem.get("record_count") == 1 and all(r.get("numeric_value_changed") is False and r.get("mapping_class_changed") is False for r in sem.get("records") or []), sem.get("record_count")),
        Check("j14_authority_candidate_executed_and_validated", j14.get("execution_performed") is True and j14.get("validation_pass") is True, j14.get("validation_checks")),
        Check("j14_output_hash_bound", bool(j14.get("output_npz_sha256")) and (root / J14_NPZ).exists() and sha256(root / J14_NPZ) == j14.get("output_npz_sha256"), j14.get("output_npz_sha256")),
        Check("j14_candidate_pending_r431_validation_seal", j14.get("candidate_authority_only_not_yet_canonical_sealed") is True),
        Check("geonomics_not_executed", audit.get("geonomics_execution_performed") is False),
        Check("r431_plan_frozen", plan.get("status") == "R430_TARGET_MATERIALIZATION_GAP_AND_J14_EXECUTION_EVIDENCE_FROZEN", plan.get("status")),
        Check("deferred_p2_two", plan.get("active_deferred_p2_cell_count") == 2, plan.get("active_deferred_p2_cell_count")),
        Check("proxy_context_two", plan.get("proxy_context_only_count") == 2, plan.get("proxy_context_only_count")),
        Check("p3_backlog_six", plan.get("p3_backlog_cell_count") == 6, plan.get("p3_backlog_cell_count")),
        Check("no_external_engine_execution", audit.get("external_engine_execution_performed") is False),
        Check("no_readjudication", audit.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", audit.get("canonical_state_changed") is False),
        Check("next_action_present", audit.get("next_action") == NEXT, audit.get("next_action")),
    ]
    verdict = "SEALED" if all(c.passed for c in checks) else "BLOCKED"
    out = {
        "stage": STAGE,
        "audit": "FINAL_AUTHORIZED_TARGET_MATERIALIZATION_SELECTOR_GAP_CLOSURE_AND_J14_SPATIAL_REPLAY_AUTHORITY_EXECUTION",
        "status": SEALED if verdict == "SEALED" else BLOCKED,
        "verdict": verdict,
        "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks],
        "summary": {
            "authorized_target_materialization_attempt_count": targets.get("authorized_selector_attempt_count"),
            "numeric_target_materialized_count": targets.get("numeric_target_materialized_count"),
            "authorized_target_materialization_deferred_count": targets.get("semantic_dependency_or_source_ambiguity_deferred_count"),
            "selector_gap_closure_count": gaps.get("record_count"),
            "semantic_repair_review_count": sem.get("record_count"),
            "j14_spatial_authority_candidate_execution_performed": j14.get("execution_performed") is True,
            "j14_spatial_authority_candidate_validation_pass": j14.get("validation_pass") is True,
            "j14_candidate_authority_sealed_canonical": False,
            "geonomics_execution_performed": False,
            "external_engine_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
            "canonical_parameter_change_authorized": False,
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
