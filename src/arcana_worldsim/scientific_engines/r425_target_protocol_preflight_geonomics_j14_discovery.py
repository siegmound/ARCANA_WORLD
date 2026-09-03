from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math
import re

import numpy as np

STAGE = "v0.6D1-R4.25"
PARENT_SEALED = "PASS_R424_P2_NORMALIZED_EVIDENCE_SEMANTIC_PROMOTION_GATE_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_SEALED"
COMPLETE = "PASS_R425_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY_COMPLETE"
SEALED = "PASS_R425_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY_SEALED"
BLOCKED = "BLOCKED_R425_PARENT_TARGET_PREFLIGHT_OR_SPATIAL_AUTHORITY_DISCOVERY_FAILURE"

CFG = Path("configs/world1_r425_target_protocol_preflight_geonomics_j14_discovery_v0_6D1_R4_25.json")
PSEAL = Path("outputs/v0_6D1_R4_24_SEAL/R4_24_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_24/R4_24_INTEGRATED_AUDIT.json")
PPLAN = Path("outputs/v0_6D1_R4_24/R4_24_R425_EXECUTION_PLAN.json")
PGEO = Path("outputs/v0_6D1_R4_24/R4_24_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN.json")
R420_TARGET = Path("outputs/v0_6D1_R4_20/R4_20_TARGET_DESIGN_PROTOCOL_REPAIR.json")
R417_TARGET = Path("outputs/v0_6D1_R4_17/R4_17_ARCANA_TARGET_EXTRACTOR_RESULTS.json")
R423_GEO = Path("outputs/v0_6D1_R4_23/R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json")
OUT = Path("outputs/v0_6D1_R4_25")
SEAL = Path("outputs/v0_6D1_R4_25_SEAL/R4_25_FINAL_SEAL_AUDIT.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"


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
    if p.exists():
        return p
    s = str(raw).replace("\\", "/")
    for marker in ("/outputs/", "/local_runs/", "/references/"):
        if marker in s:
            rel = s.split(marker, 1)[1]
            q = root / marker.strip("/") / rel
            if q.exists():
                return q
    q = root / s
    return q if q.exists() else None


def _canonical_source_eligible(root: Path, path: Path) -> tuple[bool, str]:
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix().lower()
    except Exception:
        rel = path.as_posix().lower()
    if not (rel.startswith("outputs/v0_6d1_r3") or rel.startswith("local_runs/v0_6d1_r3") or rel.startswith("references/")):
        return False, "OUTSIDE_CANONICAL_R3_OR_REFERENCE_SURFACE"
    engine_tokens = ("nemo", "slim", "cdmetapop", "geonomics", "rangeshift", "madingley")
    if any(t in rel for t in engine_tokens):
        return False, "EXTERNAL_ENGINE_DERIVED_SOURCE_CANNOT_DEFINE_ARCANA_TARGET"
    if "/v0_6d1_r4_" in rel or rel.startswith("outputs/v0_6d1_r4"):
        return False, "R4_EXTERNAL_REVALIDATION_OUTPUT_CANNOT_DEFINE_ARCANA_TARGET"
    return True, "ELIGIBLE_CANONICAL_SOURCE_SURFACE"


def _parser_family(path: Path) -> str | None:
    s = path.suffix.lower()
    return {
        ".json": "READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR",
        ".npz": "READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR",
        ".csv": "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR",
        ".tsv": "READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR",
    }.get(s)


def build_target_preflight(root: Path, r420: dict[str, Any], r417: dict[str, Any]) -> dict[str, Any]:
    old_by = {(r.get("window_id"), r.get("domain")): r for r in (r417.get("records") or [])}
    records: list[dict[str, Any]] = []
    for rec in r420.get("records") or []:
        key = (rec.get("window_id"), rec.get("domain"))
        cls = str(rec.get("backlog_class") or "")
        out: dict[str, Any] = {
            "window_id": rec.get("window_id"),
            "domain": rec.get("domain"),
            "backlog_class": cls,
            "r420_repair_disposition": rec.get("repair_disposition"),
            "required_fields": rec.get("required_fields"),
            "external_result_may_define_target": False,
            "numeric_target_materialization_authorized_in_r425": False,
            "adjudicative_promotion_authorized_in_r425": False,
            "result_selected_transform_authorized": False,
        }
        if cls == "CONTEXT_ONLY_PROXY_PRESERVE":
            out.update({
                "active_repair": False,
                "preflight_disposition": "CONTEXT_ONLY_PROXY_PRESERVED",
                "implementation_ready": False,
                "next_priority": "P4_PRESERVE_NONADJUDICATIVE",
            })
        elif cls == "NEW_CANONICAL_TARGET_DESIGN_REQUIRED":
            out.update({
                "active_repair": True,
                "preflight_disposition": "DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED",
                "implementation_ready": False,
                "next_priority": "R426_TARGET_DESIGN_AUTHORITY_FREEZE",
                "source_authority_required": True,
            })
        elif cls == "MATERIALIZED_TARGET_OR_PRIMARY_METRIC_SEMANTIC_REPAIR_REQUIRED":
            failed = list(rec.get("failed_validation_keys") or [])
            out.update({
                "active_repair": True,
                "preflight_disposition": "READY_FOR_REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT" if failed else "DEFERRED_MISSING_REJECTION_CAUSE",
                "implementation_ready": bool(failed),
                "next_priority": "R426_REPAIR_ONLY_FAILED_SEMANTIC_OR_PRIMARY_METRIC_GATES",
                "failed_validation_keys": failed,
                "failed_validation_fields": rec.get("failed_validation_fields"),
                "numeric_value_change_authorized": False,
            })
        elif cls == "CANONICAL_TARGET_EXTRACTOR_OR_EXPLICIT_DESCRIPTOR_REQUIRED":
            old = old_by.get(key) or {}
            candidates = []
            for src in old.get("candidate_sources_inspected") or []:
                rp = _resolve_recorded_path(root, src.get("source"))
                if rp is None or not rp.exists():
                    candidates.append({"source": src.get("source"), "present": False, "eligible": False, "reason": "SOURCE_NOT_PRESENT_AT_PREFLIGHT"})
                    continue
                eligible, reason = _canonical_source_eligible(root, rp)
                parser = _parser_family(rp)
                if parser is None and eligible:
                    eligible, reason = False, "UNSUPPORTED_READ_ONLY_EXTRACTOR_FORMAT"
                try:
                    rel = rp.resolve().relative_to(root.resolve()).as_posix()
                except Exception:
                    rel = rp.as_posix()
                candidates.append({
                    "source": rel,
                    "present": True,
                    "eligible": bool(eligible and parser),
                    "reason": reason if parser else (reason if not eligible else "UNSUPPORTED_READ_ONLY_EXTRACTOR_FORMAT"),
                    "parser_family": parser,
                    "sha256": sha256(rp) if eligible and parser else None,
                    "bytes": rp.stat().st_size,
                })
            eligible_candidates = [c for c in candidates if c.get("eligible")]
            out.update({
                "active_repair": True,
                "preflight_disposition": "READY_FOR_READ_ONLY_CANONICAL_EXTRACTOR_IMPLEMENTATION" if eligible_candidates else "DEFERRED_NO_ELIGIBLE_CANONICAL_SOURCE_AFTER_AUTHORITY_SCREEN",
                "implementation_ready": bool(eligible_candidates),
                "next_priority": "R426_CANONICAL_TARGET_EXTRACTOR_IMPLEMENTATION" if eligible_candidates else "R426_TARGET_DESIGN_AUTHORITY_OR_SOURCE_DISCOVERY",
                "candidate_source_count_from_r417": old.get("candidate_source_count", 0),
                "eligible_canonical_source_count": len(eligible_candidates),
                "candidate_sources": candidates,
            })
        else:
            out.update({
                "active_repair": True,
                "preflight_disposition": "DEFERRED_UNKNOWN_BACKLOG_CLASS_FAIL_CLOSED",
                "implementation_ready": False,
                "next_priority": "REPAIR_R425_UNKNOWN_TARGET_BACKLOG_CLASS",
            })
        records.append(out)

    active = [r for r in records if r.get("active_repair")]
    ready = [r for r in active if r.get("implementation_ready")]
    design = [r for r in active if r.get("preflight_disposition") == "DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED"]
    source_deferred = [r for r in active if r.get("preflight_disposition") == "DEFERRED_NO_ELIGIBLE_CANONICAL_SOURCE_AFTER_AUTHORITY_SCREEN"]
    semantic_ready = [r for r in active if r.get("preflight_disposition") == "READY_FOR_REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT"]
    proxy = [r for r in records if not r.get("active_repair")]
    unknown = [r for r in active if r.get("preflight_disposition") == "DEFERRED_UNKNOWN_BACKLOG_CLASS_FAIL_CLOSED"]
    return {
        "stage": STAGE,
        "status": "R425_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_COMPLETE" if len(records) == 59 and len(active) == 57 and len(proxy) == 2 and not unknown else BLOCKED,
        "record_count": len(records),
        "active_repair_count": len(active),
        "context_only_proxy_count": len(proxy),
        "implementation_ready_count": len(ready),
        "canonical_extractor_ready_count": sum(r.get("preflight_disposition") == "READY_FOR_READ_ONLY_CANONICAL_EXTRACTOR_IMPLEMENTATION" for r in active),
        "semantic_repair_audit_ready_count": len(semantic_ready),
        "new_target_design_authority_required_count": len(design),
        "source_or_authority_deferred_count": len(source_deferred),
        "unknown_backlog_class_count": len(unknown),
        "numeric_target_materialization_authorized": False,
        "target_execution_performed": False,
        "records": records,
    }


def _load_small_numeric(npz: Any, key: str, max_items: int = 100_000) -> np.ndarray | None:
    try:
        arr = np.asarray(npz[key])
        if arr.size > max_items or arr.dtype.kind not in "fiu":
            return None
        return arr.astype(float, copy=False).ravel()
    except Exception:
        return None


def _npz_spatial_exact3(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"format": "npz", "inspectable": False, "spatial_basis_present": False, "exact_3ma_time_present": False, "time_indexed_spatial_support": False}
    try:
        with np.load(path, allow_pickle=False) as z:
            keys = list(z.files)
            low = {k.lower(): k for k in keys}
            spatial_pair = (("lat" in low and "lon" in low) or ("grid_row" in low and "grid_col" in low) or ("x" in low and "y" in low))
            state_vars: list[str] = []
            for vk in ("state_variable_names", "variable_names", "landscape_variable_names"):
                if vk in low:
                    try:
                        state_vars.extend(str(x).lower() for x in np.asarray(z[low[vk]]).ravel().tolist())
                    except Exception:
                        pass
            embedded_grid = "grid_row" in state_vars and "grid_col" in state_vars
            spatial_basis = spatial_pair or embedded_grid
            exact = False
            time_key = None
            time_count = None
            for k in keys:
                kl = k.lower()
                factor = None
                if kl in {"age_ma", "snapshot_age_ma", "anchor_age_ma", "time_ma"}:
                    factor = 1.0
                    target = 3.0
                elif kl in {"age_ka", "snapshot_age_ka", "anchor_age_ka", "time_ka"}:
                    factor = 1.0
                    target = 3000.0
                else:
                    continue
                arr = _load_small_numeric(z, k)
                if arr is None:
                    continue
                if np.any(np.isfinite(arr) & np.isclose(arr, target, rtol=0.0, atol=1e-9)):
                    exact = True; time_key = k; time_count = int(arr.size); break
            time_indexed = False
            if spatial_basis and exact and time_count:
                for k in keys:
                    try:
                        shape = z[k].shape
                    except Exception:
                        continue
                    if time_count in shape and len(shape) >= 2 and k != time_key:
                        if any(tok in k.lower() for tok in ("state", "population", "deme", "landscape", "field", "snapshot")):
                            time_indexed = True; break
                # Embedded grid in a time-indexed state tensor is sufficient.
                if embedded_grid:
                    for k in keys:
                        if "state" in k.lower():
                            try:
                                if time_count in z[k].shape and len(z[k].shape) >= 3:
                                    time_indexed = True; break
                            except Exception:
                                pass
            out.update({
                "inspectable": True,
                "keys": keys,
                "spatial_basis_present": spatial_basis,
                "spatial_basis_kind": "DIRECT_COORDINATE_ARRAYS" if spatial_pair else ("EMBEDDED_GRID_VARIABLES" if embedded_grid else None),
                "exact_3ma_time_present": exact,
                "time_key": time_key,
                "time_indexed_spatial_support": bool(time_indexed),
            })
    except Exception as e:
        out["inspection_error"] = type(e).__name__
    return out


def _json_collect_keys(obj: Any, keys: set[str], nums: list[float], depth: int = 0) -> None:
    if depth > 6:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(str(k).lower())
            if isinstance(v, (int, float)) and math.isfinite(float(v)):
                nums.append(float(v))
            _json_collect_keys(v, keys, nums, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:5000]:
            if isinstance(v, (int, float)) and math.isfinite(float(v)):
                nums.append(float(v))
            elif isinstance(v, (dict, list)):
                _json_collect_keys(v, keys, nums, depth + 1)


def _json_spatial_exact3(path: Path) -> dict[str, Any]:
    out = {"format": "json", "inspectable": False, "spatial_basis_present": False, "exact_3ma_time_present": False, "time_indexed_spatial_support": False}
    try:
        if path.stat().st_size > 20 * 1024 * 1024:
            out["inspection_error"] = "JSON_TOO_LARGE_FOR_BOUNDED_DISCOVERY"
            return out
        obj = load(path)
        keys: set[str] = set(); nums: list[float] = []
        _json_collect_keys(obj, keys, nums)
        spatial = (("lat" in keys and "lon" in keys) or ("latitude" in keys and "longitude" in keys) or ("grid_row" in keys and "grid_col" in keys) or ("x" in keys and "y" in keys))
        time_keys = any(k in keys for k in ("age_ma", "snapshot_age_ma", "anchor_age_ma", "time_ma", "age_ka", "snapshot_age_ka", "anchor_age_ka", "time_ka"))
        exact = time_keys and (any(abs(x - 3.0) <= 1e-9 for x in nums) or any(abs(x - 3000.0) <= 1e-9 for x in nums))
        stateish = any(any(t in k for t in ("state", "population", "deme", "landscape", "field", "snapshot")) for k in keys)
        out.update({"inspectable": True, "spatial_basis_present": spatial, "exact_3ma_time_present": exact, "time_indexed_spatial_support": bool(spatial and exact and stateish), "key_sample": sorted(keys)[:120]})
    except Exception as e:
        out["inspection_error"] = type(e).__name__
    return out


def _stage_dir_from_path(root: Path, path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except Exception:
        return None
    parts = rel.parts
    if len(parts) >= 2 and parts[0].lower() in {"outputs", "local_runs"} and parts[1].lower().startswith("v0_6d1_r3"):
        return parts[1]
    return None


def _seal_provenance(root: Path, path: Path) -> dict[str, Any]:
    stage_dir = _stage_dir_from_path(root, path)
    if not stage_dir:
        return {"verified": False, "reason": "NO_R3_STAGE_DIRECTORY_IDENTITY"}
    candidates: list[Path] = []
    seal_dir = root / "outputs" / f"{stage_dir}_SEAL"
    if seal_dir.exists():
        candidates.extend(seal_dir.rglob("*.json"))
    stage_out = root / "outputs" / stage_dir
    if stage_out.exists():
        candidates.extend(p for p in stage_out.rglob("*.json") if "seal" in p.name.lower())
    for p in candidates[:100]:
        try:
            d = load(p)
        except Exception:
            continue
        status = str(d.get("status") or "")
        verdict = str(d.get("verdict") or "")
        if verdict.upper() == "SEALED" or (status.startswith("PASS_") and "SEALED" in status.upper()):
            try: rel = p.resolve().relative_to(root.resolve()).as_posix()
            except Exception: rel = p.as_posix()
            return {"verified": True, "seal_path": rel, "seal_status": status, "seal_verdict": verdict}
    return {"verified": False, "reason": "NO_EXPLICIT_SEALED_PROVENANCE_FOUND_FOR_STAGE", "stage_dir": stage_dir}


def _discovery_candidates(root: Path, parent_geo: dict[str, Any], max_additional: int = 400) -> list[Path]:
    found: dict[str, Path] = {}
    # Always re-audit the exact sources already named by R4.23 for J14.
    for rec in parent_geo.get("records") or []:
        if rec.get("job_id") != J14:
            continue
        for src in rec.get("canonical_spatial_sources_audited") or []:
            p = _resolve_recorded_path(root, src.get("path"))
            if p and p.exists(): found[str(p.resolve())] = p
    tokens = ("spatial", "population", "deme", "replay", "checkpoint", "landscape", "bridge", "state", "grid", "geo")
    for base_name in ("outputs", "local_runs", "references"):
        base = root / base_name
        if not base.exists():
            continue
        search_roots = [base] if base_name == "references" else [d for d in base.iterdir() if d.is_dir() and d.name.lower().startswith("v0_6d1_r3")]
        for search_root in search_roots:
            for suffix in ("*.npz", "*.json"):
                for p in search_root.rglob(suffix):
                    rel = p.as_posix().lower()
                    if not any(t in p.name.lower() or t in rel for t in tokens):
                        continue
                    found.setdefault(str(p.resolve()), p)
                    if len(found) >= max_additional:
                        break
                if len(found) >= max_additional:
                    break
            if len(found) >= max_additional:
                break
        if len(found) >= max_additional:
            break
    return sorted(found.values(), key=lambda p: p.as_posix())


def discover_j14_spatial_authority(root: Path, parent_geo: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for p in _discovery_candidates(root, parent_geo):
        eligible, reason = _canonical_source_eligible(root, p)
        if not eligible:
            # For spatial authority, local canonical R3 artifacts may contain engine names in unrelated filenames;
            # external-engine results remain excluded, but retain the audit row.
            authority_surface = False
        else:
            authority_surface = True
        info = _npz_spatial_exact3(p) if p.suffix.lower() == ".npz" else _json_spatial_exact3(p)
        seal = _seal_provenance(root, p) if authority_surface else {"verified": False, "reason": reason}
        exact_candidate = bool(authority_surface and info.get("spatial_basis_present") and info.get("exact_3ma_time_present") and info.get("time_indexed_spatial_support"))
        accepted = bool(exact_candidate and seal.get("verified"))
        try: rel = p.resolve().relative_to(root.resolve()).as_posix()
        except Exception: rel = p.as_posix()
        records.append({
            "path": rel,
            "sha256": sha256(p),
            "bytes": p.stat().st_size,
            "authority_surface_eligible": authority_surface,
            "authority_surface_reason": reason,
            **info,
            "exact_3ma_spatial_authority_candidate": exact_candidate,
            "seal_provenance": seal,
            "accepted_existing_sealed_authority_candidate": accepted,
        })
    exact = [r for r in records if r.get("exact_3ma_spatial_authority_candidate")]
    accepted = [r for r in records if r.get("accepted_existing_sealed_authority_candidate")]
    status = "R425_EXISTING_SEALED_3MA_SPATIAL_AUTHORITY_DISCOVERY_COMPLETE"
    return {
        "stage": STAGE,
        "status": status,
        "candidate_file_count": len(records),
        "exact_3ma_spatial_candidate_count": len(exact),
        "sealed_existing_authority_candidate_count": len(accepted),
        "existing_sealed_authority_found": bool(accepted),
        "j14_spatial_authority_gap_open_after_discovery": not bool(accepted),
        "geonomics_execution_authorized_in_r425": False,
        "canonical_replay_authorized_in_r425": False,
        "r42_j14_mutation_authorized": False,
        "records": records,
        "accepted_candidates": accepted,
        "if_none_found_next_route": "NEW_CANONICAL_SPATIAL_REPLAY_AUTHORITY_REQUEST_FREEZE",
        "if_found_next_route": "EXISTING_AUTHORITY_BINDING_VALIDATION_BEFORE_GEONOMICS_EXECUTION",
    }


def build(root: Path) -> dict[str, Any]:
    cfg = load(root / CFG) if (root / CFG).exists() else {}
    pseal = load(root / PSEAL) if (root / PSEAL).exists() else {}
    pa = load(root / PAUDIT) if (root / PAUDIT).exists() else {}
    pp = load(root / PPLAN) if (root / PPLAN).exists() else {}
    pg = load(root / PGEO) if (root / PGEO).exists() else {}
    r420 = load(root / R420_TARGET) if (root / R420_TARGET).exists() else {}
    r417 = load(root / R417_TARGET) if (root / R417_TARGET).exists() else {}
    r423geo = load(root / R423_GEO) if (root / R423_GEO).exists() else {}

    checks: list[Check] = [
        Check("parent_r424_seal_present", (root / PSEAL).exists(), str(PSEAL)),
        Check("parent_r424_sealed", pseal.get("status") == PARENT_SEALED, pseal.get("status")),
        Check("parent_next_action_matches_r425", pseal.get("next_action") == "BUILD_R425_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY", pseal.get("next_action")),
        Check("parent_four_p2_terminal_nonadjudicative", pa.get("p2_semantically_closed_nonadjudicative_count") == 4, pa.get("p2_semantically_closed_nonadjudicative_count")),
        Check("parent_zero_p2_promotions", pa.get("p2_adjudicative_promotion_count") == 0, pa.get("p2_adjudicative_promotion_count")),
        Check("parent_two_deferred_geonomics_p2", pa.get("active_deferred_p2_cell_count") == 2 and pa.get("active_deferred_p2_engine_families") == ["Geonomics"], {"count": pa.get("active_deferred_p2_cell_count"), "families": pa.get("active_deferred_p2_engine_families")}),
        Check("parent_j14_gap_open", pa.get("geonomics_j14_spatial_authority_gap_open") is True),
        Check("parent_j18_j21_bindings_two", pa.get("geonomics_j18_j21_binding_translation_count") == 2, pa.get("geonomics_j18_j21_binding_translation_count")),
        Check("parent_target_repairs_57", pa.get("active_target_protocol_repair_count") == 57, pa.get("active_target_protocol_repair_count")),
        Check("parent_proxy_two", pa.get("proxy_context_only_count") == 2, pa.get("proxy_context_only_count")),
        Check("parent_p3_six", pa.get("p3_backlog_cell_count") == 6, pa.get("p3_backlog_cell_count")),
        Check("parent_r425_plan_frozen", pp.get("status") == "R424_P2_SEMANTIC_CLOSURE_AND_J14_AUTHORITY_PLAN_FROZEN", pp.get("status")),
        Check("parent_geonomics_authority_plan_frozen", pg.get("status") == "R424_GEONOMICS_J14_SPATIAL_AUTHORITY_CLOSURE_PLAN_FROZEN", pg.get("status")),
        Check("r420_target_repair_registry_59", r420.get("record_count") == 59 and len(r420.get("records") or []) == 59, {"declared": r420.get("record_count"), "loaded": len(r420.get("records") or [])}),
        Check("r420_active_target_repairs_57", r420.get("active_repair_count") == 57, r420.get("active_repair_count")),
        Check("r417_target_registry_59", r417.get("p1_cell_count") == 59 and len(r417.get("records") or []) == 59, {"declared": r417.get("p1_cell_count"), "loaded": len(r417.get("records") or [])}),
        Check("r423_geonomics_registry_three", r423geo.get("record_count") == 3, r423geo.get("record_count")),
        Check("policy_frozen", cfg.get("policy_freeze") == "FROZEN_PRE_TARGET_REPAIR_EXECUTION_AND_J14_SPATIAL_AUTHORITY_DISCOVERY"),
        Check("engine_execution_forbidden", cfg.get("engine_execution_performed") is False),
        Check("target_numeric_execution_forbidden", cfg.get("target_numeric_execution_performed") is False),
        Check("readjudication_forbidden", cfg.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", cfg.get("canonical_replay_authorized") is False),
        Check("deep_off", cfg.get("deep_biological_coupling") is False),
    ]
    if not all(c.passed for c in checks):
        out = {"stage": STAGE, "status": BLOCKED, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.d() for c in checks], "next_action": "REPAIR_R425_PARENT_OR_POLICY_INPUTS"}
        write(root / OUT / "R4_25_INTEGRATED_AUDIT.json", out)
        return out

    target = build_target_preflight(root, r420, r417)
    spatial = discover_j14_spatial_authority(root, r423geo)
    next_action = (
        "BUILD_R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_EXISTING_AUTHORITY_BINDING_VALIDATION"
        if spatial.get("existing_sealed_authority_found")
        else "BUILD_R426_TARGET_EXTRACTOR_IMPLEMENTATION_AND_GEONOMICS_J14_NEW_SPATIAL_AUTHORITY_REQUEST_FREEZE"
    )
    checks += [
        Check("target_preflight_exact_59_records", target.get("record_count") == 59, target.get("record_count")),
        Check("target_preflight_active_exact_57", target.get("active_repair_count") == 57, target.get("active_repair_count")),
        Check("target_preflight_proxy_exact_two", target.get("context_only_proxy_count") == 2, target.get("context_only_proxy_count")),
        Check("target_preflight_all_active_terminally_disposed", target.get("implementation_ready_count", 0) + target.get("new_target_design_authority_required_count", 0) + target.get("source_or_authority_deferred_count", 0) == 57, {"ready": target.get("implementation_ready_count"), "design": target.get("new_target_design_authority_required_count"), "source_deferred": target.get("source_or_authority_deferred_count")}),
        Check("target_preflight_unknown_class_zero", target.get("unknown_backlog_class_count") == 0, target.get("unknown_backlog_class_count")),
        Check("target_no_numeric_materialization", target.get("numeric_target_materialization_authorized") is False),
        Check("target_external_results_never_define_target", all(r.get("external_result_may_define_target") is False for r in target.get("records") or [])),
        Check("target_no_adjudicative_promotion", all(r.get("adjudicative_promotion_authorized_in_r425") is False for r in target.get("records") or [])),
        Check("j14_discovery_completed", spatial.get("status") == "R425_EXISTING_SEALED_3MA_SPATIAL_AUTHORITY_DISCOVERY_COMPLETE", spatial.get("status")),
        Check("j14_discovery_records_hash_bound", all(bool(r.get("sha256")) for r in spatial.get("records") or [])),
        Check("j14_acceptance_requires_exact_3ma_spatial_and_seal", all((not r.get("accepted_existing_sealed_authority_candidate")) or (r.get("exact_3ma_spatial_authority_candidate") and (r.get("seal_provenance") or {}).get("verified")) for r in spatial.get("records") or [])),
        Check("geonomics_execution_not_authorized", spatial.get("geonomics_execution_authorized_in_r425") is False),
        Check("canonical_replay_not_authorized_by_discovery", spatial.get("canonical_replay_authorized_in_r425") is False),
        Check("r42_j14_mutation_not_authorized", spatial.get("r42_j14_mutation_authorized") is False),
        Check("p3_backlog_preserved_six", pa.get("p3_backlog_cell_count") == 6),
        Check("no_engine_execution", cfg.get("engine_execution_performed") is False),
        Check("no_readjudication", cfg.get("readjudication_performed") is False),
        Check("canonical_state_still_unchanged", cfg.get("canonical_state_changed") is False),
    ]
    ok = all(c.passed for c in checks)
    status = COMPLETE if ok else BLOCKED
    plan = {
        "stage": STAGE,
        "status": "R425_TARGET_PREFLIGHT_AND_J14_AUTHORITY_DISCOVERY_FROZEN" if ok else BLOCKED,
        "target_active_repair_count": 57,
        "target_implementation_ready_count": target.get("implementation_ready_count"),
        "target_canonical_extractor_ready_count": target.get("canonical_extractor_ready_count"),
        "target_semantic_repair_audit_ready_count": target.get("semantic_repair_audit_ready_count"),
        "target_new_design_authority_required_count": target.get("new_target_design_authority_required_count"),
        "target_source_or_authority_deferred_count": target.get("source_or_authority_deferred_count"),
        "target_numeric_execution_authorized_in_r426_by_r425": False,
        "j14_existing_sealed_authority_found": spatial.get("existing_sealed_authority_found"),
        "j14_existing_sealed_authority_candidate_count": spatial.get("sealed_existing_authority_candidate_count"),
        "j14_spatial_authority_gap_open_after_discovery": spatial.get("j14_spatial_authority_gap_open_after_discovery"),
        "geonomics_execution_authorized_in_r426_by_r425": False,
        "canonical_replay_authorized": False,
        "p3_backlog_cell_count": 6,
        "next_action": next_action if ok else "REPAIR_R425_TARGET_PREFLIGHT_OR_SPATIAL_DISCOVERY",
    }
    out = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "target_active_repair_count": 57,
        "target_implementation_ready_count": target.get("implementation_ready_count"),
        "target_canonical_extractor_ready_count": target.get("canonical_extractor_ready_count"),
        "target_semantic_repair_audit_ready_count": target.get("semantic_repair_audit_ready_count"),
        "target_new_design_authority_required_count": target.get("new_target_design_authority_required_count"),
        "target_source_or_authority_deferred_count": target.get("source_or_authority_deferred_count"),
        "proxy_context_only_count": 2,
        "j14_discovery_candidate_file_count": spatial.get("candidate_file_count"),
        "j14_exact_3ma_spatial_candidate_count": spatial.get("exact_3ma_spatial_candidate_count"),
        "j14_existing_sealed_authority_candidate_count": spatial.get("sealed_existing_authority_candidate_count"),
        "j14_existing_sealed_authority_found": spatial.get("existing_sealed_authority_found"),
        "j14_spatial_authority_gap_open_after_discovery": spatial.get("j14_spatial_authority_gap_open_after_discovery"),
        "active_deferred_p2_cell_count": 2,
        "p3_backlog_cell_count": 6,
        "engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_25_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT.json", target)
    write(root / OUT / "R4_25_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY.json", spatial)
    write(root / OUT / "R4_25_R426_EXECUTION_PLAN.json", plan)
    write(root / OUT / "R4_25_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    p = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_25_INTEGRATED_AUDIT.json") if (root / OUT / "R4_25_INTEGRATED_AUDIT.json").exists() else {}
    t = load(root / OUT / "R4_25_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT.json") if (root / OUT / "R4_25_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT.json").exists() else {}
    g = load(root / OUT / "R4_25_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY.json") if (root / OUT / "R4_25_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY.json").exists() else {}
    plan = load(root / OUT / "R4_25_R426_EXECUTION_PLAN.json") if (root / OUT / "R4_25_R426_EXECUTION_PLAN.json").exists() else {}
    checks = [
        Check("parent_r424_sealed", p.get("status") == PARENT_SEALED, p.get("status")),
        Check("r425_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r425_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check("target_preflight_59_records", t.get("record_count") == 59, t.get("record_count")),
        Check("target_active_57", t.get("active_repair_count") == 57, t.get("active_repair_count")),
        Check("target_proxy_two", t.get("context_only_proxy_count") == 2, t.get("context_only_proxy_count")),
        Check("target_no_numeric_execution", t.get("target_execution_performed") is False),
        Check("j14_discovery_complete", g.get("status") == "R425_EXISTING_SEALED_3MA_SPATIAL_AUTHORITY_DISCOVERY_COMPLETE", g.get("status")),
        Check("geonomics_not_executed", g.get("geonomics_execution_authorized_in_r425") is False),
        Check("r426_plan_frozen", plan.get("status") == "R425_TARGET_PREFLIGHT_AND_J14_AUTHORITY_DISCOVERY_FROZEN", plan.get("status")),
        Check("p3_backlog_six", a.get("p3_backlog_cell_count") == 6, a.get("p3_backlog_cell_count")),
        Check("no_engine_execution", a.get("engine_execution_performed") is False),
        Check("no_readjudication", a.get("readjudication_performed") is False),
        Check("canonical_state_unchanged", a.get("canonical_state_changed") is False),
        Check("next_action_present", str(a.get("next_action") or "").startswith("BUILD_R426_"), a.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {
        "stage": STAGE,
        "audit": "FINAL_TARGET_PROTOCOL_REPAIR_EXECUTION_PREFLIGHT_AND_GEONOMICS_J14_SPATIAL_AUTHORITY_DISCOVERY",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "target_active_repair_count": a.get("target_active_repair_count"),
            "target_implementation_ready_count": a.get("target_implementation_ready_count"),
            "target_canonical_extractor_ready_count": a.get("target_canonical_extractor_ready_count"),
            "target_semantic_repair_audit_ready_count": a.get("target_semantic_repair_audit_ready_count"),
            "target_new_design_authority_required_count": a.get("target_new_design_authority_required_count"),
            "target_source_or_authority_deferred_count": a.get("target_source_or_authority_deferred_count"),
            "proxy_context_only_count": a.get("proxy_context_only_count"),
            "j14_existing_sealed_authority_candidate_count": a.get("j14_existing_sealed_authority_candidate_count"),
            "j14_existing_sealed_authority_found": a.get("j14_existing_sealed_authority_found"),
            "j14_spatial_authority_gap_open_after_discovery": a.get("j14_spatial_authority_gap_open_after_discovery"),
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
