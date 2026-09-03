from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import math
import re

import numpy as np

STAGE = "v0.6D1-R4.35"

PARENT_COMPLETE = (
    "PASS_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
    "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_"
    "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R435_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
    "AND_SEED_AUTHORITY_CLOSURE"
)

COMPLETE = (
    "PASS_R435_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
    "AND_SEED_AUTHORITY_CLOSURE_COMPLETE"
)
SEALED = (
    "PASS_R435_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
    "AND_SEED_AUTHORITY_CLOSURE_SEALED"
)
BLOCKED = (
    "BLOCKED_R435_PARENT_NATIVE_SCHEMA_INITIAL_STATE_OR_SEED_"
    "AUTHORITY_CLOSURE_FAILURE"
)

NEXT = (
    "BUILD_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_"
    "CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT"
)

CFG = Path(
    "configs/world1_r435_geonomics_native_schema_mapping_initial_state_"
    "adapter_seed_authority_closure_v0_6D1_R4_35.json"
)
PSEAL = Path("outputs/v0_6D1_R4_34_SEAL/R4_34_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_34/R4_34_INTEGRATED_AUDIT.json")
PSEL = Path(
    "outputs/v0_6D1_R4_34/"
    "R4_34_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE.json"
)
PPREFLIGHT = Path(
    "outputs/v0_6D1_R4_34/"
    "R4_34_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT.json"
)
PPLAN = Path("outputs/v0_6D1_R4_34/R4_34_R435_EXECUTION_PLAN.json")
R43SEEDS = Path("outputs/v0_6D1_R4_3/R4_3_SEED_LEDGER.json")

OUT = Path("outputs/v0_6D1_R4_35")
SEAL = Path("outputs/v0_6D1_R4_35_SEAL/R4_35_FINAL_SEAL_AUDIT.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"
JOBS = (J14, J18, J21)

TIME_KEYS = {
    J14: ("age_ma", "ma", 1_000_000.0),
    J18: ("snapshot_age_ka", "ka", 1_000.0),
    J21: ("anchor_age_ka", "ka", 1_000.0),
}

COMMON_GAPS = (
    "LANDSCAPE_GEOMETRY_DIM_RES_ULC_PRJ",
    "MODEL_PHYSICAL_TIME_TO_INTEGER_TIMESTEP_MAPPING",
    "MODEL_RANDOM_SEED_LEDGER_BINDING",
    "LAYER_VALUE_SCALING_NORMALIZATION",
)
SAPIENT_GAPS = (
    "SPECIES_INIT_N_FROM_CANONICAL_POPULATION",
    "EXACT_SPATIAL_INITIAL_STATE_INJECTION",
    "SPECIES_K_LAYER_AND_K_FACTOR_SEMANTIC_BINDING",
)
J21_GAPS = (
    "PRODUCER_RESOURCE_TO_GEONOMICS_LAYER_ROLE_BINDING",
)


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


def _as_int_seed(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, np.integer)):
        v = int(value)
        return v if v >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


def _collect_seed_candidates(
    obj: Any,
    current_job: str | None = None,
    out: dict[str, set[int]] | None = None,
) -> dict[str, set[int]]:
    """Schema-tolerant read of the historical R4.3 frozen seed ledger.

    Supports:
    - rows with job_id + seed/random_seed/model_seed/base_seed;
    - dict mappings JOB_ID -> integer seed;
    - nested per-job dicts.
    Does not synthesize missing values.
    """
    if out is None:
        out = {}

    if isinstance(obj, dict):
        jid = current_job
        for k in ("job_id", "frozen_job_id", "job"):
            v = obj.get(k)
            if isinstance(v, str) and v.startswith("R42_J"):
                jid = v
                break

        if jid:
            for k in ("seed", "random_seed", "model_seed", "base_seed"):
                s = _as_int_seed(obj.get(k))
                if s is not None:
                    out.setdefault(jid, set()).add(s)

        for k, v in obj.items():
            next_job = jid
            if isinstance(k, str) and k.startswith("R42_J"):
                next_job = k
                s = _as_int_seed(v)
                if s is not None:
                    out.setdefault(k, set()).add(s)
                    continue
            _collect_seed_candidates(v, next_job, out)

    elif isinstance(obj, list):
        for v in obj:
            _collect_seed_candidates(v, current_job, out)

    return out


def _seed_authority(root: Path) -> dict[str, Any]:
    p = root / R43SEEDS
    if not p.exists():
        return {
            "status": "BLOCKED_R435_R43_SEED_LEDGER_MISSING",
            "ledger_path": R43SEEDS.as_posix(),
            "ledger_present": False,
            "job_seed_count": 0,
            "records": [],
        }

    ledger = load(p)
    cand = _collect_seed_candidates(ledger)
    all_job_seeds = {
        jid: sorted(vals)
        for jid, vals in cand.items()
        if jid.startswith("R42_J")
    }
    exact = {
        jid: vals[0]
        for jid, vals in all_job_seeds.items()
        if len(vals) == 1
    }
    selected = []
    for jid in JOBS:
        vals = all_job_seeds.get(jid, [])
        selected.append({
            "job_id": jid,
            "candidate_seed_values": vals,
            "exact_single_frozen_seed": len(vals) == 1,
            "seed": vals[0] if len(vals) == 1 else None,
        })

    all_exact_23 = len(exact) == 23 and len(all_job_seeds) == 23
    unique_global = all_exact_23 and len(set(exact.values())) == 23
    three_exact = all(r["exact_single_frozen_seed"] for r in selected)

    return {
        "status":
            "R435_R43_FROZEN_SEED_AUTHORITY_RECOVERED"
            if all_exact_23 and unique_global and three_exact
            else "BLOCKED_R435_R43_SEED_LEDGER_NOT_EXACT",
        "ledger_path": R43SEEDS.as_posix(),
        "ledger_present": True,
        "ledger_sha256": sha256(p),
        "job_seed_count": len(all_job_seeds),
        "exact_single_seed_job_count": len(exact),
        "global_unique_seed_count": len(set(exact.values())),
        "exact_23_job_seed_ledger": all_exact_23,
        "no_duplicate_seeds_global": unique_global,
        "geonomics_three_exact": three_exact,
        "records": selected,
    }


def _decode_names(arr: np.ndarray) -> list[str]:
    out: list[str] = []
    for v in np.asarray(arr).reshape(-1).tolist():
        if isinstance(v, bytes):
            out.append(v.decode("utf-8", errors="replace"))
        else:
            out.append(str(v))
    return out


def _npz_source_paths(root: Path, package: dict[str, Any]) -> list[Path]:
    paths = []
    for src in package.get("canonical_sources") or []:
        rel = src.get("path")
        if not rel:
            continue
        p = root / str(rel)
        if (
            p.exists()
            and p.suffix.lower() == ".npz"
            and src.get("hash_match") is True
        ):
            paths.append(p)
    return paths


def _load_runtime_package(root: Path, selector_rec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    authp = root / str(selector_rec.get("selector_authority_file") or "")
    if not authp.exists():
        return {}, {"selector_authority_hash_match": False}
    auth = load(authp)
    auth_hash_ok = bool(
        selector_rec.get("selector_authority_sha256")
        and sha256(authp) == selector_rec.get("selector_authority_sha256")
    )
    rel = auth.get("parent_runtime_binding_package_file")
    pp = root / str(rel or "")
    package = load(pp) if rel and pp.exists() else {}
    package_hash_ok = bool(
        auth.get("parent_runtime_binding_package_sha256")
        and pp.exists()
        and sha256(pp) == auth.get("parent_runtime_binding_package_sha256")
    )
    return package, {
        "selector_authority_hash_match": auth_hash_ok,
        "runtime_binding_package_hash_match": package_hash_ok,
        "selector_authority_status": auth.get("status"),
    }


def _time_axis(root: Path, job_id: str, package: dict[str, Any]) -> dict[str, Any]:
    key, unit, years_per_unit = TIME_KEYS[job_id]
    matches = []
    for p in _npz_source_paths(root, package):
        try:
            with np.load(p, allow_pickle=False) as z:
                if key in z.files:
                    vals = np.asarray(z[key], dtype=np.float64).reshape(-1)
                    matches.append((p, vals))
        except Exception:
            continue
    if len(matches) != 1:
        return {
            "status": "BLOCKED_EXACT_TIME_AXIS_NOT_UNIQUELY_RESOLVED",
            "key": key,
            "match_count": len(matches),
        }

    p, vals = matches[0]
    finite = bool(vals.size >= 2 and np.all(np.isfinite(vals)))
    diffs = np.diff(vals)
    monotonic = bool(
        finite and (np.all(diffs <= 0) or np.all(diffs >= 0))
        and np.any(diffs != 0)
    )
    steps = []
    if finite and monotonic:
        for i, v in enumerate(vals.tolist()):
            row = {
                "model_step": i,
                "canonical_age": float(v),
                "canonical_age_unit": unit,
            }
            if i + 1 < vals.size:
                row["physical_duration_to_next_years"] = abs(
                    float(vals[i + 1] - vals[i]) * years_per_unit
                )
            else:
                row["physical_duration_to_next_years"] = None
            steps.append(row)

    return {
        "status":
            "CLOSED_EXACT_CANONICAL_AGE_TO_INTEGER_STEP_BIJECTION"
            if monotonic else "BLOCKED_TIME_AXIS_INVALID",
        "source_path": p.relative_to(root).as_posix(),
        "source_sha256": sha256(p),
        "key": key,
        "axis_count": int(vals.size),
        "monotonic": monotonic,
        "mapping_rule":
            "model_step=i <-> exact canonical age axis element i; "
            "no equal-duration assumption; physical duration retained per edge",
        "interpolation_performed": False,
        "extrapolation_performed": False,
        "steps": steps,
    }


def _infer_raster_shape_from_state(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as z:
        # Direct row/col arrays first.
        if "grid_row" in z.files and "grid_col" in z.files:
            rr = np.asarray(z["grid_row"], dtype=float).reshape(-1)
            cc = np.asarray(z["grid_col"], dtype=float).reshape(-1)
            finite = np.isfinite(rr) & np.isfinite(cc)
            if finite.any():
                return _shape_from_coords(rr[finite], cc[finite], "direct_grid_row_grid_col_arrays")

        # Discover a state table plus names axis.
        name_keys = [
            k for k in z.files
            if "variable_names" in k.lower() or "state_names" in k.lower()
        ]
        for nk in name_keys:
            try:
                names = _decode_names(z[nk])
            except Exception:
                continue
            low = [n.lower() for n in names]
            if "grid_row" not in low or "grid_col" not in low:
                continue
            ri, ci = low.index("grid_row"), low.index("grid_col")
            for sk in z.files:
                if "state" not in sk.lower():
                    continue
                a = np.asarray(z[sk])
                if a.ndim < 2 or a.shape[-1] != len(names):
                    continue
                rr = np.asarray(a[..., ri], dtype=float).reshape(-1)
                cc = np.asarray(a[..., ci], dtype=float).reshape(-1)
                finite = np.isfinite(rr) & np.isfinite(cc)
                if finite.any():
                    out = _shape_from_coords(rr[finite], cc[finite], f"{sk}+{nk}")
                    out["state_key"] = sk
                    out["names_key"] = nk
                    out["state_variable_names"] = names
                    return out
    return {"status": "BLOCKED_GRID_ROW_GRID_COL_NOT_DISCOVERED"}


def _shape_from_coords(rr: np.ndarray, cc: np.ndarray, provenance: str) -> dict[str, Any]:
    integerish = bool(
        np.all(np.abs(rr - np.round(rr)) < 1e-9)
        and np.all(np.abs(cc - np.round(cc)) < 1e-9)
    )
    nonnegative = bool(np.min(rr) >= 0 and np.min(cc) >= 0)
    if not (integerish and nonnegative):
        return {
            "status": "BLOCKED_GRID_INDICES_INVALID",
            "integerish": integerish,
            "nonnegative": nonnegative,
        }
    rows = int(np.max(np.round(rr))) + 1
    cols = int(np.max(np.round(cc))) + 1
    return {
        "status": "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY",
        "provenance": provenance,
        "rows": rows,
        "cols": cols,
        "geonomics_landscape_dim_xy": [cols, rows],
        "geonomics_res_xy": [1, 1],
        "geonomics_ulc_xy": [0, 0],
        "geonomics_prj": None,
        "coordinate_semantics": "CANONICAL_GRID_INDEX_ONLY",
        "physical_distance_or_area_claim_authorized": False,
    }


def _geometry(root: Path, job_id: str, package: dict[str, Any]) -> dict[str, Any]:
    paths = _npz_source_paths(root, package)
    if job_id in (J14, J18):
        hits = []
        for p in paths:
            try:
                r = _infer_raster_shape_from_state(p)
            except Exception:
                continue
            if r.get("status") == "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY":
                r["source_path"] = p.relative_to(root).as_posix()
                r["source_sha256"] = sha256(p)
                hits.append(r)
        if len(hits) != 1:
            return {
                "status": "BLOCKED_INDEX_GRID_GEOMETRY_NOT_UNIQUELY_RESOLVED",
                "candidate_count": len(hits),
                "candidates": hits,
            }
        return hits[0]

    # J21: require the two canonical raster families to agree on final y/x shape.
    shapes = []
    for p in paths:
        with np.load(p, allow_pickle=False) as z:
            for key in ("environment_fields", "producer_landscape"):
                if key in z.files:
                    a = np.asarray(z[key])
                    if a.ndim >= 2:
                        shapes.append({
                            "source_path": p.relative_to(root).as_posix(),
                            "source_sha256": sha256(p),
                            "key": key,
                            "rows": int(a.shape[-2]),
                            "cols": int(a.shape[-1]),
                        })
    if len(shapes) != 2 or len({(s["rows"], s["cols"]) for s in shapes}) != 1:
        return {
            "status": "BLOCKED_J21_SHARED_RASTER_GRID_NOT_EXACT",
            "raster_shapes": shapes,
        }
    rows, cols = shapes[0]["rows"], shapes[0]["cols"]
    return {
        "status": "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY",
        "sources": shapes,
        "rows": rows,
        "cols": cols,
        "geonomics_landscape_dim_xy": [cols, rows],
        "geonomics_res_xy": [1, 1],
        "geonomics_ulc_xy": [0, 0],
        "geonomics_prj": None,
        "coordinate_semantics": "CANONICAL_GRID_INDEX_ONLY",
        "physical_distance_or_area_claim_authorized": False,
    }


def _state_field_authority(root: Path, job_id: str, package: dict[str, Any]) -> dict[str, Any]:
    if job_id not in (J14, J18):
        return {
            "status": "NOT_APPLICABLE_LANDSCAPE_ONLY_RESOURCE_JOB",
            "job_scope": "PROVENANCE_SEPARATE_LANDSCAPE_LAYER_BINDING",
        }

    paths = _npz_source_paths(root, package)
    candidates = []
    for p in paths:
        with np.load(p, allow_pickle=False) as z:
            name_keys = [
                k for k in z.files
                if "variable_names" in k.lower() or "state_names" in k.lower()
            ]
            for nk in name_keys:
                try:
                    names = _decode_names(z[nk])
                except Exception:
                    continue
                low = [n.lower() for n in names]
                if "grid_row" not in low or "grid_col" not in low:
                    continue
                pop_name = next(
                    (n for n in names if n.lower() in (
                        "population", "population_proxy", "effective_population"
                    )),
                    None,
                )
                if pop_name is None:
                    continue
                state_keys = [
                    sk for sk in z.files
                    if "state" in sk.lower()
                    and np.asarray(z[sk]).ndim >= 2
                    and np.asarray(z[sk]).shape[-1] == len(names)
                ]
                for sk in state_keys:
                    candidates.append({
                        "source_path": p.relative_to(root).as_posix(),
                        "source_sha256": sha256(p),
                        "state_key": sk,
                        "names_key": nk,
                        "grid_row_field": names[low.index("grid_row")],
                        "grid_col_field": names[low.index("grid_col")],
                        "population_weight_field": pop_name,
                        "available_state_fields": names,
                    })
    # Deduplicate identical source/state/name triplets.
    uniq = {}
    for c in candidates:
        uniq[(c["source_path"], c["state_key"], c["names_key"])] = c
    candidates = list(uniq.values())

    if len(candidates) != 1:
        return {
            "status": "BLOCKED_SPATIAL_STATE_FIELDS_NOT_UNIQUELY_RESOLVED",
            "candidate_count": len(candidates),
            "candidates": candidates,
        }
    c = candidates[0]
    c.update({
        "status": "CLOSED_EXACT_DEME_STATE_FIELD_AUTHORITY",
        "population_semantics":
            "ARCANA_EFFECTIVE_OR_PROXY_WEIGHT_RETAINED_AS_SIDECAR_NOT_LITERAL_INDIVIDUAL_COUNT",
        "geonomics_carrier_semantics":
            "ONE_NONLITERAL_CONNECTIVITY_CARRIER_PER_ACTIVE_DEME",
        "carrier_coordinate_rule":
            "x=grid_col+0.5; y=grid_row+0.5 in canonical index-grid coordinates",
        "random_initialization_authorized": False,
        "demographic_population_count_adjudication_authorized": False,
        "authorized_domain_scope": ["connectivity", "range_support_proxy"],
    })
    return c


def _j21_layer_role_authority(root: Path, package: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for p in _npz_source_paths(root, package):
        with np.load(p, allow_pickle=False) as z:
            if "environment_fields" in z.files:
                names = _decode_names(z["environment_variable_names"]) if "environment_variable_names" in z.files else []
                rows.append({
                    "source_path": p.relative_to(root).as_posix(),
                    "source_sha256": sha256(p),
                    "array_key": "environment_fields",
                    "name_axis_key": "environment_variable_names" if names else None,
                    "declared_names": names,
                    "native_role": "GEONOMICS_DEFINED_LAYER_SET_ENVIRONMENT",
                })
            if "producer_landscape" in z.files:
                names = _decode_names(z["landscape_variable_names"]) if "landscape_variable_names" in z.files else []
                rows.append({
                    "source_path": p.relative_to(root).as_posix(),
                    "source_sha256": sha256(p),
                    "array_key": "producer_landscape",
                    "name_axis_key": "landscape_variable_names" if names else None,
                    "declared_names": names,
                    "native_role": "GEONOMICS_DEFINED_LAYER_SET_PRODUCER_SUPPORT",
                })
    kinds = {r["array_key"] for r in rows}
    ok = kinds == {"environment_fields", "producer_landscape"}
    return {
        "status":
            "CLOSED_J21_PROVENANCE_SEPARATE_NATIVE_LAYER_ROLE_AUTHORITY"
            if ok else "BLOCKED_J21_LAYER_ROLE_SOURCES_INCOMPLETE",
        "layers": rows,
        "identity_value_mapping": True,
        "automatic_rescaling_authorized": False,
        "cross_layer_numeric_fusion_authorized": False,
        "producer_values_interpreted_as_literal_agents": False,
        "environment_and_producer_provenance_kept_separate": True,
    }


def _closure_record(
    job_id: str,
    gap: str,
    disposition: str,
    authority: dict[str, Any],
) -> dict[str, Any]:
    terminal = disposition.startswith("CLOSED_")
    return {
        "stage": STAGE,
        "job_id": job_id,
        "gap": gap,
        "disposition": disposition,
        "terminally_closed": terminal,
        "authority": authority,
        "result_selected": False,
        "comparison_result_used": False,
        "canonical_state_changed": False,
    }


def build_authority_closure(
    root: Path,
    selector_registry: dict[str, Any],
    preflight_registry: dict[str, Any],
) -> dict[str, Any]:
    seed = _seed_authority(root)
    seed_by = {r["job_id"]: r for r in seed.get("records") or []}
    preflight_by = {
        r.get("job_id"): r
        for r in preflight_registry.get("records") or []
    }
    rows = []
    job_summaries = []
    blocked = 0

    for sel in selector_registry.get("records") or []:
        jid = sel.get("job_id")
        if jid not in JOBS:
            continue

        package, integrity = _load_runtime_package(root, sel)
        pfrow = preflight_by.get(jid) or {}
        pfp = root / str(pfrow.get("preflight_file") or "")
        pfhash_ok = bool(
            pfp.exists()
            and pfrow.get("preflight_sha256")
            and sha256(pfp) == pfrow.get("preflight_sha256")
        )

        geom = _geometry(root, jid, package) if integrity["runtime_binding_package_hash_match"] else {"status":"BLOCKED_PARENT_RUNTIME_PACKAGE_HASH"}
        time = _time_axis(root, jid, package) if integrity["runtime_binding_package_hash_match"] else {"status":"BLOCKED_PARENT_RUNTIME_PACKAGE_HASH"}
        state = _state_field_authority(root, jid, package) if integrity["runtime_binding_package_hash_match"] else {"status":"BLOCKED_PARENT_RUNTIME_PACKAGE_HASH"}
        j21_layers = _j21_layer_role_authority(root, package) if jid == J21 and integrity["runtime_binding_package_hash_match"] else None
        seedrec = seed_by.get(jid) or {}
        seed_ok = seedrec.get("exact_single_frozen_seed") is True

        # Common 4.
        rows.append(_closure_record(
            jid, "LANDSCAPE_GEOMETRY_DIM_RES_ULC_PRJ",
            "CLOSED_INDEX_GRID_NATIVE_GEOMETRY_AUTHORITY"
            if geom.get("status") == "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY"
            else "BLOCKED_INDEX_GRID_NATIVE_GEOMETRY_AUTHORITY",
            geom,
        ))
        rows.append(_closure_record(
            jid, "MODEL_PHYSICAL_TIME_TO_INTEGER_TIMESTEP_MAPPING",
            "CLOSED_EXACT_AGE_INDEX_TIMESTEP_AUTHORITY"
            if str(time.get("status","")).startswith("CLOSED_")
            else "BLOCKED_EXACT_AGE_INDEX_TIMESTEP_AUTHORITY",
            time,
        ))
        rows.append(_closure_record(
            jid, "MODEL_RANDOM_SEED_LEDGER_BINDING",
            "CLOSED_R43_FROZEN_JOB_SEED_AUTHORITY"
            if seed_ok else "BLOCKED_R43_FROZEN_JOB_SEED_AUTHORITY",
            {
                "seed_ledger_path": seed.get("ledger_path"),
                "seed_ledger_sha256": seed.get("ledger_sha256"),
                "job_seed_record": seedrec,
                "model_seed_binding_target": "params.model.seed.num",
                "new_seed_generation_authorized": False,
            },
        ))
        rows.append(_closure_record(
            jid, "LAYER_VALUE_SCALING_NORMALIZATION",
            "CLOSED_IDENTITY_VALUE_NO_RESCALING_AUTHORITY"
            if integrity["runtime_binding_package_hash_match"]
            else "BLOCKED_PARENT_RUNTIME_PACKAGE_HASH",
            {
                "rule": "IDENTITY_VALUE_PRESERVATION",
                "scale_min_val": None,
                "scale_max_val": None,
                "automatic_normalization_authorized": False,
                "automatic_clipping_authorized": False,
                "source_hash_bound": integrity["runtime_binding_package_hash_match"],
            },
        ))

        if jid in (J14, J18):
            state_ok = state.get("status") == "CLOSED_EXACT_DEME_STATE_FIELD_AUTHORITY"
            rows.append(_closure_record(
                jid, "SPECIES_INIT_N_FROM_CANONICAL_POPULATION",
                "CLOSED_BY_NONLITERAL_PROXY_CARRIER_SCOPE_RESTRICTION"
                if state_ok else "BLOCKED_PROXY_CARRIER_STATE_AUTHORITY",
                {
                    "rule": "ONE_CONNECTIVITY_CARRIER_PER_ACTIVE_DEME",
                    "population_weight_source_field": state.get("population_weight_field"),
                    "population_weight_semantics":
                        "SIDECAR_EFFECTIVE_OR_PROXY_WEIGHT_NOT_LITERAL_CENSUS",
                    "native_literal_N_from_population_weight_authorized": False,
                    "demographic_count_adjudication_authorized": False,
                    "authorized_domain_scope": ["connectivity", "range_support_proxy"],
                },
            ))
            rows.append(_closure_record(
                jid, "EXACT_SPATIAL_INITIAL_STATE_INJECTION",
                "CLOSED_EXACT_DEME_CENTER_ADD_INDIVIDUALS_ADAPTER_AUTHORITY"
                if state_ok else "BLOCKED_EXACT_SPATIAL_INITIAL_STATE_ADAPTER",
                {
                    "state_authority": state,
                    "engine_api_target": "Model.add_individuals(n, coords, ...)",
                    "coordinate_rule":
                        "x=grid_col+0.5; y=grid_row+0.5; exact active-deme order",
                    "random_initialization_authorized": False,
                    "jitter_authorized": False,
                    "future_state_interpolation_authorized": False,
                },
            ))
            rows.append(_closure_record(
                jid, "SPECIES_K_LAYER_AND_K_FACTOR_SEMANTIC_BINDING",
                "CLOSED_CONSTRUCTION_SCAFFOLD_ONLY_NO_CARRYING_CAPACITY_CLAIM"
                if state_ok and geom.get("status") == "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY"
                else "BLOCKED_K_LAYER_CONSTRUCTION_SCAFFOLD_AUTHORITY",
                {
                    "K_layer_rule":
                        "BINARY_CANONICAL_SUPPORT_SCAFFOLD_FOR_MODEL_CONSTRUCTION_ONLY",
                    "K_factor": 1,
                    "ARCANA_carrying_capacity_interpretation": False,
                    "population_persistence_adjudication_authorized": False,
                    "demographic_dynamics_authorized_by_this_binding": False,
                    "purpose": "permit exact connectivity-proxy initial-state construction only",
                },
            ))
        else:
            layer_ok = j21_layers and str(j21_layers.get("status","")).startswith("CLOSED_")
            rows.append(_closure_record(
                jid, "PRODUCER_RESOURCE_TO_GEONOMICS_LAYER_ROLE_BINDING",
                "CLOSED_J21_PROVENANCE_SEPARATE_DEFINED_LAYER_AUTHORITY"
                if layer_ok else "BLOCKED_J21_DEFINED_LAYER_ROLE_AUTHORITY",
                j21_layers or {},
            ))

        expected_gap_count = 7 if jid in (J14, J18) else 5
        job_rows = [r for r in rows if r["job_id"] == jid]
        terminal = sum(r["terminally_closed"] for r in job_rows)
        parent_ok = (
            integrity["selector_authority_hash_match"]
            and integrity["runtime_binding_package_hash_match"]
            and pfhash_ok
        )
        if not (parent_ok and terminal == expected_gap_count):
            blocked += 1
        job_summaries.append({
            "job_id": jid,
            "parent_selector_authority_hash_match": integrity["selector_authority_hash_match"],
            "parent_runtime_binding_package_hash_match": integrity["runtime_binding_package_hash_match"],
            "parent_r434_preflight_hash_match": pfhash_ok,
            "expected_gap_count": expected_gap_count,
            "terminally_closed_gap_count": terminal,
            "authority_closure_pass": parent_ok and terminal == expected_gap_count,
        })

    terminal = sum(r["terminally_closed"] for r in rows)
    return {
        "stage": STAGE,
        "status":
            "R435_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_AND_SEED_AUTHORITY_CLOSURE_COMPLETE"
            if len(rows) == 19 and terminal == 19 and blocked == 0
            and seed.get("exact_23_job_seed_ledger") is True
            and seed.get("no_duplicate_seeds_global") is True
            else BLOCKED,
        "record_count": len(rows),
        "terminally_closed_gap_count": terminal,
        "blocked_gap_count": len(rows) - terminal,
        "job_closure_pass_count": sum(r["authority_closure_pass"] for r in job_summaries),
        "seed_authority": seed,
        "job_summaries": job_summaries,
        "records": rows,
        "native_geonomics_params_materialized_count": 0,
        "gnx_make_model_performed": False,
        "geonomics_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    ps = load(root / PSEAL)
    pa = load(root / PAUDIT)
    sel = load(root / PSEL)
    pf = load(root / PPREFLIGHT)
    pp = load(root / PPLAN)

    closure = build_authority_closure(root, sel, pf)
    write(
        root / OUT / "R4_35_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_SEED_AUTHORITY_CLOSURE.json",
        closure,
    )

    checks = [
        Check(
            "parent_r434_sealed",
            ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED",
            ps.get("status"),
        ),
        Check(
            "parent_r434_complete",
            pa.get("status") == PARENT_COMPLETE and pa.get("checks_failed") == 0,
            pa.get("status"),
        ),
        Check(
            "parent_next_action_matches_r435",
            pa.get("next_action") == PARENT_NEXT and ps.get("next_action") == PARENT_NEXT,
            {"audit": pa.get("next_action"), "seal": ps.get("next_action")},
        ),
        Check(
            "parent_r435_plan_frozen",
            pp.get("status")
            == "R434_SELECTOR_AUTHORITY_AND_NATIVE_PARAMETER_PREFLIGHT_EVIDENCE_FROZEN",
            pp.get("status"),
        ),
        Check(
            "parent_three_selector_authorities_frozen",
            sel.get("record_count") == 3
            and sel.get("selector_authority_frozen_job_count") == 3,
            sel.get("selector_authority_frozen_job_count"),
        ),
        Check(
            "parent_three_native_preflights",
            pf.get("record_count") == 3 and pf.get("preflight_pass_count") == 3,
            pf.get("preflight_pass_count"),
        ),
        Check(
            "parent_explicit_gap_count_19",
            pf.get("explicit_unresolved_authority_gap_count") == 19,
            pf.get("explicit_unresolved_authority_gap_count"),
        ),
        Check(
            "policy_frozen",
            cfg.get("policy")
            == "FROZEN_POST_R434_PRE_NATIVE_PARAMETER_MATERIALIZATION_PRE_MODEL_CONSTRUCTION",
            cfg.get("policy"),
        ),
        Check(
            "r43_seed_ledger_exact_23_recovered",
            closure.get("seed_authority", {}).get("exact_23_job_seed_ledger") is True,
            closure.get("seed_authority", {}).get("job_seed_count"),
        ),
        Check(
            "r43_seed_ledger_no_duplicates",
            closure.get("seed_authority", {}).get("no_duplicate_seeds_global") is True,
            closure.get("seed_authority", {}).get("global_unique_seed_count"),
        ),
        Check(
            "three_geonomics_exact_frozen_seeds",
            closure.get("seed_authority", {}).get("geonomics_three_exact") is True,
        ),
        Check(
            "exact_19_authority_gaps_terminally_closed",
            closure.get("record_count") == 19
            and closure.get("terminally_closed_gap_count") == 19,
            {
                "records": closure.get("record_count"),
                "closed": closure.get("terminally_closed_gap_count"),
            },
        ),
        Check(
            "zero_authority_closure_blocks",
            closure.get("blocked_gap_count") == 0
            and closure.get("job_closure_pass_count") == 3,
            {
                "blocked": closure.get("blocked_gap_count"),
                "jobs": closure.get("job_closure_pass_count"),
            },
        ),
        Check(
            "three_index_grid_geometries_closed",
            sum(
                r["gap"] == "LANDSCAPE_GEOMETRY_DIM_RES_ULC_PRJ"
                and r["terminally_closed"]
                for r in closure.get("records") or []
            ) == 3,
        ),
        Check(
            "three_exact_age_index_time_mappings_closed",
            sum(
                r["gap"] == "MODEL_PHYSICAL_TIME_TO_INTEGER_TIMESTEP_MAPPING"
                and r["terminally_closed"]
                for r in closure.get("records") or []
            ) == 3,
        ),
        Check(
            "three_identity_no_rescaling_authorities_closed",
            sum(
                r["gap"] == "LAYER_VALUE_SCALING_NORMALIZATION"
                and r["terminally_closed"]
                for r in closure.get("records") or []
            ) == 3,
        ),
        Check(
            "j14_j18_nonliteral_population_semantics_preserved",
            sum(
                r["gap"] == "SPECIES_INIT_N_FROM_CANONICAL_POPULATION"
                and r["disposition"]
                    == "CLOSED_BY_NONLITERAL_PROXY_CARRIER_SCOPE_RESTRICTION"
                for r in closure.get("records") or []
            ) == 2,
        ),
        Check(
            "j14_j18_exact_spatial_injection_authority_closed",
            sum(
                r["gap"] == "EXACT_SPATIAL_INITIAL_STATE_INJECTION"
                and r["terminally_closed"]
                for r in closure.get("records") or []
            ) == 2,
        ),
        Check(
            "j14_j18_K_scaffold_not_claimed_as_arcana_carrying_capacity",
            sum(
                r["gap"] == "SPECIES_K_LAYER_AND_K_FACTOR_SEMANTIC_BINDING"
                and r["terminally_closed"]
                and r["authority"].get("ARCANA_carrying_capacity_interpretation") is False
                for r in closure.get("records") or []
            ) == 2,
        ),
        Check(
            "j21_provenance_separate_layer_role_closed",
            sum(
                r["gap"] == "PRODUCER_RESOURCE_TO_GEONOMICS_LAYER_ROLE_BINDING"
                and r["terminally_closed"]
                for r in closure.get("records") or []
            ) == 1,
        ),
        Check(
            "geonomics_authority_scope_domain_specific",
            cfg.get("geonomics_population_counts_never_literal_without_separate_authority") is True
            and cfg.get("connectivity_proxy_scope_authorized_for_j14_j18") is True,
        ),
        Check(
            "no_native_params_materialized",
            closure.get("native_geonomics_params_materialized_count") == 0,
        ),
        Check(
            "no_make_model",
            closure.get("gnx_make_model_performed") is False,
        ),
        Check(
            "no_external_engine_execution",
            closure.get("geonomics_execution_performed") is False
            and cfg.get("external_engine_execution_performed") is False,
        ),
        Check(
            "no_target_numeric_execution",
            closure.get("target_numeric_execution_performed") is False
            and cfg.get("target_numeric_execution_performed") is False,
        ),
        Check(
            "no_readjudication",
            closure.get("readjudication_performed") is False
            and cfg.get("readjudication_performed") is False,
        ),
        Check(
            "canonical_state_unchanged",
            closure.get("canonical_state_changed") is False
            and cfg.get("canonical_state_changed") is False,
        ),
        Check(
            "deep_off",
            cfg.get("deep_biological_coupling") is False,
        ),
        Check(
            "random_initialization_forbidden",
            cfg.get("random_spatial_initialization_forbidden") is True,
        ),
        Check(
            "result_selected_selector_forbidden",
            cfg.get("result_selected_selector_forbidden") is True,
        ),
        Check(
            "majority_vote_forbidden",
            cfg.get("majority_vote_forbidden") is True,
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
            "R435_NATIVE_SCHEMA_INITIAL_STATE_AND_SEED_AUTHORITY_EVIDENCE_FROZEN"
            if ok else BLOCKED,
        "authority_gap_record_count": closure.get("record_count"),
        "terminally_closed_authority_gap_count":
            closure.get("terminally_closed_gap_count"),
        "r43_seed_ledger_exact_23": closure.get("seed_authority", {}).get("exact_23_job_seed_ledger"),
        "geonomics_exact_frozen_seed_count": 3 if closure.get("seed_authority", {}).get("geonomics_three_exact") else 0,
        "native_geonomics_params_materialized_count": 0,
        "gnx_make_model_authorized_in_r435": False,
        "geonomics_execution_authorized_in_r435": False,
        "target_numeric_execution_authorized_in_r435": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok
            else "REPAIR_R435_NATIVE_SCHEMA_INITIAL_STATE_OR_SEED_AUTHORITY_CLOSURE",
    }
    write(root / OUT / "R4_35_R436_EXECUTION_PLAN.json", plan)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "target_authority_binding_record_count": 57,
        "geonomics_authority_gap_record_count": closure.get("record_count"),
        "geonomics_terminally_closed_authority_gap_count":
            closure.get("terminally_closed_gap_count"),
        "geonomics_seed_authority_exact_count":
            3 if closure.get("seed_authority", {}).get("geonomics_three_exact") else 0,
        "native_geonomics_params_materialized_count": 0,
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
    write(root / OUT / "R4_35_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    ps = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_35_INTEGRATED_AUDIT.json") if (
        root / OUT / "R4_35_INTEGRATED_AUDIT.json"
    ).exists() else {}
    c = load(
        root / OUT / "R4_35_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_SEED_AUTHORITY_CLOSURE.json"
    ) if (
        root / OUT / "R4_35_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_SEED_AUTHORITY_CLOSURE.json"
    ).exists() else {}
    plan = load(root / OUT / "R4_35_R436_EXECUTION_PLAN.json") if (
        root / OUT / "R4_35_R436_EXECUTION_PLAN.json"
    ).exists() else {}

    checks = [
        Check("parent_r434_sealed", ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED"),
        Check("r435_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r435_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check(
            "exact_19_authority_gaps_closed",
            c.get("record_count") == 19
            and c.get("terminally_closed_gap_count") == 19
            and c.get("blocked_gap_count") == 0,
        ),
        Check(
            "all_three_job_closures_pass",
            c.get("job_closure_pass_count") == 3,
            c.get("job_closure_pass_count"),
        ),
        Check(
            "r43_exact_23_seed_ledger_preserved",
            c.get("seed_authority", {}).get("exact_23_job_seed_ledger") is True
            and c.get("seed_authority", {}).get("no_duplicate_seeds_global") is True,
        ),
        Check(
            "three_geonomics_seeds_exact",
            c.get("seed_authority", {}).get("geonomics_three_exact") is True,
        ),
        Check(
            "population_semantics_nonliteral",
            sum(
                r.get("disposition") == "CLOSED_BY_NONLITERAL_PROXY_CARRIER_SCOPE_RESTRICTION"
                for r in c.get("records") or []
            ) == 2,
        ),
        Check(
            "exact_spatial_injection_adapter_authority",
            sum(
                r.get("gap") == "EXACT_SPATIAL_INITIAL_STATE_INJECTION"
                and r.get("terminally_closed") is True
                for r in c.get("records") or []
            ) == 2,
        ),
        Check(
            "j21_layer_role_authority",
            sum(
                r.get("gap") == "PRODUCER_RESOURCE_TO_GEONOMICS_LAYER_ROLE_BINDING"
                and r.get("terminally_closed") is True
                for r in c.get("records") or []
            ) == 1,
        ),
        Check(
            "native_params_not_materialized",
            c.get("native_geonomics_params_materialized_count") == 0,
        ),
        Check("make_model_not_performed", c.get("gnx_make_model_performed") is False),
        Check("geonomics_execution_not_performed", c.get("geonomics_execution_performed") is False),
        Check(
            "r436_plan_frozen",
            plan.get("status")
            == "R435_NATIVE_SCHEMA_INITIAL_STATE_AND_SEED_AUTHORITY_EVIDENCE_FROZEN",
            plan.get("status"),
        ),
        Check(
            "geonomics_execution_not_authorized",
            plan.get("geonomics_execution_authorized_in_r435") is False,
        ),
        Check(
            "target_numeric_execution_not_authorized",
            plan.get("target_numeric_execution_authorized_in_r435") is False,
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

    ok = all(ch.passed for ch in checks)
    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
            "AND_SEED_AUTHORITY_CLOSURE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(ch.passed for ch in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not ch.passed for ch in checks),
        "checks": [ch.d() for ch in checks],
        "summary": {
            "target_authority_binding_record_count": 57,
            "geonomics_authority_gap_record_count": c.get("record_count"),
            "geonomics_terminally_closed_authority_gap_count":
                c.get("terminally_closed_gap_count"),
            "geonomics_seed_authority_exact_count":
                3 if c.get("seed_authority", {}).get("geonomics_three_exact") else 0,
            "native_geonomics_params_materialized_count": 0,
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
