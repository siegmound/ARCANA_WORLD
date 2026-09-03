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
R423_J18_PROFILE = Path(
    "outputs/v0_6D1_R4_23/geonomics_profiles/"
    "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS/LANDSCAPE_PROFILE.json"
)
R328_AUTHORITY = Path(
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json"
)

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
    """Recover the exact R4.3 ordered replicate-seed vectors.

    Live R4.35-R1 proved the frozen R4.3 ledger contains 23 jobs and exactly
    4 replicate seeds per job. The authority is the ordered vector, never a
    scalar selected from it.
    """
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
    jobs = ledger.get("jobs") if isinstance(ledger, dict) else None
    if not isinstance(jobs, list):
        return {
            "status": "BLOCKED_R435_R43_SEED_LEDGER_SCHEMA_MISMATCH",
            "ledger_path": R43SEEDS.as_posix(),
            "ledger_present": True,
            "ledger_sha256": sha256(p),
            "job_seed_count": 0,
            "records": [],
        }

    by_job: dict[str, list[int]] = {}
    schema_ok = True
    for row in jobs:
        if not isinstance(row, dict):
            schema_ok = False
            continue
        jid = row.get("job_id")
        reps = row.get("replicates")
        if not isinstance(jid, str) or not jid.startswith("R42_J") or not isinstance(reps, list):
            schema_ok = False
            continue
        ordered: list[int] = []
        for rep in reps:
            if not isinstance(rep, dict):
                schema_ok = False
                continue
            s = _as_int_seed(rep.get("seed"))
            if s is None:
                schema_ok = False
                continue
            ordered.append(s)
        by_job[jid] = ordered

    exact_23 = (
        schema_ok
        and len(jobs) == 23
        and len(by_job) == 23
        and all(len(v) == 4 for v in by_job.values())
    )
    all_92 = [s for jid in sorted(by_job) for s in by_job[jid]]
    unique_92 = exact_23 and len(all_92) == 92 and len(set(all_92)) == 92

    selected = []
    for jid in JOBS:
        vals = by_job.get(jid, [])
        selected.append({
            "job_id": jid,
            "replicate_seed_vector": vals,
            "replicate_count": len(vals),
            "exact_four_frozen_replicate_seeds": len(vals) == 4,
            "replicate_bindings": [
                {
                    "replicate_index": i,
                    "seed": s,
                    "model_seed_binding_target": "params.model.seed.num",
                }
                for i, s in enumerate(vals)
            ],
            "scalar_seed_selection_performed": False,
        })

    three_exact = all(r["exact_four_frozen_replicate_seeds"] for r in selected)

    return {
        "status":
            "R435_R43_FROZEN_REPLICATE_SEED_AUTHORITY_RECOVERED"
            if exact_23 and unique_92 and three_exact
            else "BLOCKED_R435_R43_REPLICATE_SEED_LEDGER_NOT_EXACT",
        "ledger_path": R43SEEDS.as_posix(),
        "ledger_present": True,
        "ledger_sha256": sha256(p),
        "job_seed_count": len(by_job),
        "replicates_per_job_expected": 4,
        "total_frozen_seed_count": len(all_92),
        "global_unique_seed_count": len(set(all_92)),
        "exact_23_job_seed_ledger": exact_23,
        "no_duplicate_seeds_global": unique_92,
        "geonomics_three_exact": three_exact,
        "exact_23_job_replicate_seed_vectors": exact_23,
        "all_92_replicate_seeds_globally_unique": unique_92,
        "geonomics_three_exact_replicate_seed_vectors": three_exact,
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
    matches: list[tuple[Path, np.ndarray]] = []
    for p in _npz_source_paths(root, package):
        try:
            with np.load(p, allow_pickle=False) as z:
                if key in z.files:
                    vals = np.asarray(z[key], dtype=np.float64).reshape(-1)
                    matches.append((p, vals))
        except Exception:
            continue

    if not matches:
        return {
            "status": "BLOCKED_EXACT_TIME_AXIS_NOT_RESOLVED",
            "key": key,
            "match_count": 0,
        }

    vals = matches[0][1]
    equivalent = all(
        other.shape == vals.shape and np.array_equal(other, vals)
        for _, other in matches[1:]
    )
    if not equivalent:
        return {
            "status": "BLOCKED_MULTIPLE_CANONICAL_TIME_AXES_NOT_EXACTLY_EQUIVALENT",
            "key": key,
            "match_count": len(matches),
            "sources": [p.relative_to(root).as_posix() for p, _ in matches],
        }

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
        "source_paths": [p.relative_to(root).as_posix() for p, _ in matches],
        "source_sha256": [sha256(p) for p, _ in matches],
        "canonical_axis_copy_count": len(matches),
        "all_canonical_axis_copies_exactly_equal": equivalent,
        "key": key,
        "axis_count": int(vals.size),
        "monotonic": monotonic,
        "mapping_rule":
            "model_step=i <-> exact canonical age axis element i; "
            "equivalent canonical copies retained without source selection; "
            "no equal-duration assumption; physical duration retained per edge",
        "interpolation_performed": False,
        "extrapolation_performed": False,
        "steps": steps,
    }


def _infer_raster_shape_from_state(path: Path) -> dict[str, Any]:
    """J14-only discrete-grid inference retained from the original R4.35."""
    with np.load(path, allow_pickle=False) as z:
        if "grid_row" in z.files and "grid_col" in z.files:
            rr = np.asarray(z["grid_row"], dtype=float).reshape(-1)
            cc = np.asarray(z["grid_col"], dtype=float).reshape(-1)
            finite = np.isfinite(rr) & np.isfinite(cc)
            if finite.any():
                return _shape_from_coords(rr[finite], cc[finite], "direct_grid_row_grid_col_arrays")

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
        "coordinate_semantics": "CANONICAL_DISCRETE_GRID_INDEX",
        "physical_distance_or_area_claim_authorized": False,
    }


def _r328_grid_authority(root: Path) -> dict[str, Any]:
    p = root / R328_AUTHORITY
    if not p.exists():
        return {"status": "BLOCKED_R328_SPATIAL_AUTHORITY_MISSING"}
    d = load(p)
    raw = str(d.get("spatial_state") or "")
    m = re.fullmatch(r"MAX_(\d+)_DEMES_PER_LINEAGE_ON_(\d+)x(\d+)_GRID", raw)
    if not m:
        return {
            "status": "BLOCKED_R328_GRID_AUTHORITY_UNPARSEABLE",
            "spatial_state": raw,
        }
    max_demes, rows, cols = map(int, m.groups())
    return {
        "status": "CLOSED_R328_EXPLICIT_GRID_AUTHORITY",
        "source_path": R328_AUTHORITY.as_posix(),
        "source_sha256": sha256(p),
        "spatial_state": raw,
        "max_demes_per_lineage": max_demes,
        "rows": rows,
        "cols": cols,
        "geonomics_landscape_dim_xy": [cols, rows],
        "geonomics_res_xy": [1, 1],
        "geonomics_ulc_xy": [0, 0],
        "geonomics_prj": None,
        "coordinate_semantics": "CONTINUOUS_COORDINATES_IN_CANONICAL_90x180_GRID_SPACE",
        "physical_distance_or_area_claim_authorized": False,
    }


def _j21_grid_from_declared_axes(root: Path, package: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for p in _npz_source_paths(root, package):
        with np.load(p, allow_pickle=False) as z:
            if (
                "environment_fields" in z.files
                and "anchor_age_ka" in z.files
                and "environment_variable_names" in z.files
            ):
                a = np.asarray(z["environment_fields"])
                nt = int(np.asarray(z["anchor_age_ka"]).size)
                nv = int(np.asarray(z["environment_variable_names"]).size)
                ok = a.ndim == 4 and a.shape[0] == nt and a.shape[-1] == nv
                rows.append({
                    "source_path": p.relative_to(root).as_posix(),
                    "source_sha256": sha256(p),
                    "key": "environment_fields",
                    "shape": list(a.shape),
                    "axis_binding": ["time", "grid_row", "grid_col", "environment_variable"],
                    "rows": int(a.shape[1]) if ok else None,
                    "cols": int(a.shape[2]) if ok else None,
                    "schema_match": ok,
                })

            if (
                "producer_landscape" in z.files
                and "producer_taxon_ids" in z.files
                and "anchor_age_ka" in z.files
                and "landscape_variable_names" in z.files
            ):
                a = np.asarray(z["producer_landscape"])
                ns = int(np.asarray(z["producer_taxon_ids"]).size)
                nt = int(np.asarray(z["anchor_age_ka"]).size)
                nv = int(np.asarray(z["landscape_variable_names"]).size)
                ok = (
                    a.ndim == 5
                    and a.shape[0] == ns
                    and a.shape[1] == nt
                    and a.shape[-1] == nv
                )
                rows.append({
                    "source_path": p.relative_to(root).as_posix(),
                    "source_sha256": sha256(p),
                    "key": "producer_landscape",
                    "shape": list(a.shape),
                    "axis_binding": ["producer_taxon", "time", "grid_row", "grid_col", "landscape_variable"],
                    "rows": int(a.shape[2]) if ok else None,
                    "cols": int(a.shape[3]) if ok else None,
                    "schema_match": ok,
                })

    ok = (
        len(rows) == 2
        and all(r["schema_match"] for r in rows)
        and len({(r["rows"], r["cols"]) for r in rows}) == 1
    )
    if not ok:
        return {
            "status": "BLOCKED_J21_SHARED_RASTER_GRID_NOT_EXACT",
            "raster_shapes": rows,
        }
    nrows, ncols = rows[0]["rows"], rows[0]["cols"]
    return {
        "status": "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY",
        "sources": rows,
        "rows": nrows,
        "cols": ncols,
        "geonomics_landscape_dim_xy": [ncols, nrows],
        "geonomics_res_xy": [1, 1],
        "geonomics_ulc_xy": [0, 0],
        "geonomics_prj": None,
        "coordinate_semantics": "CANONICAL_RASTER_INDEX_GRID",
        "physical_distance_or_area_claim_authorized": False,
    }


def _geometry(root: Path, job_id: str, package: dict[str, Any]) -> dict[str, Any]:
    paths = _npz_source_paths(root, package)

    if job_id == J18:
        auth = _r328_grid_authority(root)
        if not str(auth.get("status", "")).startswith("CLOSED_"):
            return auth

        profile_path = root / R423_J18_PROFILE
        if not profile_path.exists() or len(paths) != 1:
            return {"status": "BLOCKED_J18_PROFILE_OR_SOURCE_MISSING"}
        profile = load(profile_path)
        tr = profile.get("translation") or {}
        if (
            tr.get("deme_state") != "snapshot_deme_state"
            or tr.get("active_mask") != "snapshot_active"
            or tr.get("coordinate_fields") != ["grid_row", "grid_col"]
        ):
            return {"status": "BLOCKED_J18_R423_TRANSLATION_DRIFT", "translation": tr}

        with np.load(paths[0], allow_pickle=False) as z:
            names = _decode_names(z["state_variable_names"])
            low = [n.lower() for n in names]
            if not {"grid_row", "grid_col"}.issubset(set(low)):
                return {"status": "BLOCKED_J18_COORDINATE_FIELDS_MISSING"}
            st = np.asarray(z["snapshot_deme_state"])
            active = np.asarray(z["snapshot_active"]).astype(bool)
            if st.shape[:-1] != active.shape:
                return {"status": "BLOCKED_J18_ACTIVE_MASK_SHAPE_MISMATCH"}
            rr = np.asarray(st[..., low.index("grid_row")], dtype=float)[active]
            cc = np.asarray(st[..., low.index("grid_col")], dtype=float)[active]

        finite = bool(rr.size > 0 and np.all(np.isfinite(rr)) and np.all(np.isfinite(cc)))
        within = bool(
            finite
            and np.min(rr) >= 0 and np.max(rr) < auth["rows"]
            and np.min(cc) >= 0 and np.max(cc) < auth["cols"]
        )
        if not within:
            return {
                "status": "BLOCKED_J18_CONTINUOUS_COORDINATES_OUTSIDE_R328_GRID",
                "grid_authority": auth,
            }
        auth.update({
            "status": "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY",
            "coordinate_validation_source": paths[0].relative_to(root).as_posix(),
            "coordinate_validation_source_sha256": sha256(paths[0]),
            "coordinate_validation_state_key": "snapshot_deme_state",
            "coordinate_validation_active_mask_key": "snapshot_active",
            "active_coordinate_count": int(rr.size),
            "grid_row_min": float(np.min(rr)),
            "grid_row_max": float(np.max(rr)),
            "grid_col_min": float(np.min(cc)),
            "grid_col_max": float(np.max(cc)),
            "coordinates_preserved_exactly_no_center_shift": True,
        })
        return auth

    if job_id == J21:
        return _j21_grid_from_declared_axes(root, package)

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


def _state_field_authority(root: Path, job_id: str, package: dict[str, Any]) -> dict[str, Any]:
    if job_id not in (J14, J18):
        return {
            "status": "NOT_APPLICABLE_LANDSCAPE_ONLY_RESOURCE_JOB",
            "job_scope": "PROVENANCE_SEPARATE_LANDSCAPE_LAYER_BINDING",
        }

    paths = _npz_source_paths(root, package)
    if len(paths) != 1:
        return {
            "status": "BLOCKED_SPATIAL_STATE_SOURCE_NOT_UNIQUE",
            "source_count": len(paths),
        }
    p = paths[0]

    if job_id == J18:
        profile_path = root / R423_J18_PROFILE
        if not profile_path.exists():
            return {"status": "BLOCKED_J18_R423_PROFILE_MISSING"}
        profile = load(profile_path)
        tr = profile.get("translation") or {}
        state_key = tr.get("deme_state")
        active_key = tr.get("active_mask")
        time_key = tr.get("time_axis")
        population_field = tr.get("population_support_field")
        coordinate_fields = tr.get("coordinate_fields")
        if (
            state_key != "snapshot_deme_state"
            or active_key != "snapshot_active"
            or time_key != "snapshot_age_ka"
            or population_field != "population_proxy"
            or coordinate_fields != ["grid_row", "grid_col"]
        ):
            return {"status": "BLOCKED_J18_R423_TRANSLATION_DRIFT", "translation": tr}

        with np.load(p, allow_pickle=False) as z:
            required = {state_key, active_key, time_key, "state_variable_names"}
            if not required.issubset(set(z.files)):
                return {
                    "status": "BLOCKED_J18_FROZEN_TRANSLATION_ARRAY_MISSING",
                    "required": sorted(required),
                    "available": sorted(z.files),
                }
            names = _decode_names(z["state_variable_names"])
            low = [n.lower() for n in names]
            for required_field in ("grid_row", "grid_col", population_field):
                if required_field.lower() not in low:
                    return {
                        "status": "BLOCKED_J18_FROZEN_TRANSLATION_FIELD_MISSING",
                        "field": required_field,
                    }
            st = np.asarray(z[state_key])
            active = np.asarray(z[active_key]).astype(bool)
            ages = np.asarray(z[time_key])
            shape_ok = (
                st.shape[:-1] == active.shape
                and st.shape[2] == ages.size
                and st.shape[-1] == len(names)
            )
            if not shape_ok:
                return {"status": "BLOCKED_J18_FROZEN_TRANSLATION_SHAPE_MISMATCH"}

        return {
            "status": "CLOSED_EXACT_DEME_STATE_FIELD_AUTHORITY",
            "source_path": p.relative_to(root).as_posix(),
            "source_sha256": sha256(p),
            "state_key": state_key,
            "active_mask_key": active_key,
            "time_axis_key": time_key,
            "names_key": "state_variable_names",
            "grid_row_field": names[low.index("grid_row")],
            "grid_col_field": names[low.index("grid_col")],
            "population_weight_field": names[low.index(population_field.lower())],
            "available_state_fields": names,
            "selection_authority_source": R423_J18_PROFILE.as_posix(),
            "selection_authority_source_sha256": sha256(profile_path),
            "population_semantics":
                "ARCANA_EFFECTIVE_OR_PROXY_WEIGHT_RETAINED_AS_SIDECAR_NOT_LITERAL_INDIVIDUAL_COUNT",
            "geonomics_carrier_semantics":
                "ONE_NONLITERAL_CONNECTIVITY_CARRIER_PER_ACTIVE_DEME",
            "carrier_coordinate_rule":
                "x=grid_col; y=grid_row; preserve exact continuous canonical grid-space coordinates",
            "coordinate_center_shift_performed": False,
            "random_initialization_authorized": False,
            "demographic_population_count_adjudication_authorized": False,
            "authorized_domain_scope": ["connectivity", "range_support_proxy"],
        }

    with np.load(p, allow_pickle=False) as z:
        if "state_variable_names" not in z.files or "spatial_state" not in z.files:
            return {"status": "BLOCKED_J14_SPATIAL_STATE_BUNDLE_MISSING"}
        names = _decode_names(z["state_variable_names"])
        low = [n.lower() for n in names]
        if not all(k in low for k in ("grid_row", "grid_col", "population_proxy", "active")):
            return {"status": "BLOCKED_J14_STATE_FIELDS_MISSING", "available": names}
        a = np.asarray(z["spatial_state"])
        if a.ndim < 2 or a.shape[-1] != len(names):
            return {"status": "BLOCKED_J14_SPATIAL_STATE_SHAPE_MISMATCH"}

    return {
        "status": "CLOSED_EXACT_DEME_STATE_FIELD_AUTHORITY",
        "source_path": p.relative_to(root).as_posix(),
        "source_sha256": sha256(p),
        "state_key": "spatial_state",
        "active_mask_key": "spatial_state.active_component",
        "names_key": "state_variable_names",
        "grid_row_field": names[low.index("grid_row")],
        "grid_col_field": names[low.index("grid_col")],
        "population_weight_field": names[low.index("population_proxy")],
        "active_field": names[low.index("active")],
        "available_state_fields": names,
        "population_semantics":
            "ARCANA_EFFECTIVE_OR_PROXY_WEIGHT_RETAINED_AS_SIDECAR_NOT_LITERAL_INDIVIDUAL_COUNT",
        "geonomics_carrier_semantics":
            "ONE_NONLITERAL_CONNECTIVITY_CARRIER_PER_ACTIVE_DEME",
        "carrier_coordinate_rule":
            "J14 frozen grid_row/grid_col interpreted by its SEALED R4.31 spatial authority; no stochastic relocation",
        "random_initialization_authorized": False,
        "demographic_population_count_adjudication_authorized": False,
        "authorized_domain_scope": ["connectivity", "range_support_proxy"],
    }


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
        seed_ok = seedrec.get("exact_four_frozen_replicate_seeds") is True

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
                "model_seed_binding_target": "params.model.seed.num per frozen replicate index",
                "replicate_seed_vector_preserved_in_order": True,
                "scalar_seed_selection_performed": False,
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
                        "x=grid_col; y=grid_row; exact active-deme order; no center shift",
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
            "r43_seed_ledger_exact_23_jobs_x4_replicates_recovered",
            closure.get("seed_authority", {}).get("exact_23_job_seed_ledger") is True,
            closure.get("seed_authority", {}).get("job_seed_count"),
        ),
        Check(
            "r43_all_92_replicate_seeds_globally_unique",
            closure.get("seed_authority", {}).get("no_duplicate_seeds_global") is True,
            closure.get("seed_authority", {}).get("global_unique_seed_count"),
        ),
        Check(
            "three_geonomics_exact_frozen_replicate_seed_vectors",
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
            "r43_exact_23_jobs_x4_replicate_seed_ledger_preserved",
            c.get("seed_authority", {}).get("exact_23_job_seed_ledger") is True
            and c.get("seed_authority", {}).get("no_duplicate_seeds_global") is True,
        ),
        Check(
            "three_geonomics_replicate_seed_vectors_exact",
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
