from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

STAGE = "v0.6D1-R4.35-R1"

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"
JOBS = (J14, J18, J21)

SEED_LEDGER = Path("outputs/v0_6D1_R4_3/R4_3_SEED_LEDGER.json")
R435_CLOSURE = Path(
    "outputs/v0_6D1_R4_35/"
    "R4_35_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_SEED_AUTHORITY_CLOSURE.json"
)
R433_RUNTIME = Path(
    "outputs/v0_6D1_R4_33/"
    "R4_33_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT.json"
)
R434_SELECTOR = Path(
    "outputs/v0_6D1_R4_34/"
    "R4_34_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE.json"
)
R423_J18_PROFILE = Path(
    "outputs/v0_6D1_R4_23/geonomics_profiles/"
    "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS/LANDSCAPE_PROFILE.json"
)
R328_AUTHORITY = Path(
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json"
)
R431_J14_SEAL = Path(
    "outputs/v0_6D1_R4_31/authority/R4_31_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL.json"
)
R430_AUTHORITY_DIR = Path("outputs/v0_6D1_R4_30/authority")
OUT = Path("outputs/v0_6D1_R4_35_R1")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return str(path)


def walk(obj: Any, path: str = "$"):
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def scalar(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def seed_ledger_schema(root: Path) -> dict[str, Any]:
    p = root / SEED_LEDGER
    if not p.exists():
        return {"present": False, "path": SEED_LEDGER.as_posix()}

    data = load(p)
    all_seed_scalars = []
    for loc, obj in walk(data):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if "seed" in str(k).lower() and scalar(v):
                    all_seed_scalars.append(
                        {"json_path": f"{loc}.{k}", "key": str(k), "value": v}
                    )

    job_objects: list[tuple[str, str, dict[str, Any]]] = []
    for loc, obj in walk(data):
        if not isinstance(obj, dict):
            continue
        jid = None
        for k in ("job_id", "frozen_job_id", "job"):
            v = obj.get(k)
            if isinstance(v, str) and v.startswith("R42_J"):
                jid = v
                break
        if jid:
            job_objects.append((jid, loc, obj))

    # If the ledger is a JOB_ID -> record mapping, capture that too.
    for loc, obj in walk(data):
        if not isinstance(obj, dict):
            continue
        for k, v in obj.items():
            if isinstance(k, str) and k.startswith("R42_J") and isinstance(v, dict):
                job_objects.append((k, f"{loc}.{k}", v))

    dedup = {}
    for jid, loc, obj in job_objects:
        dedup[(jid, loc)] = obj

    per_job = defaultdict(list)
    field_signature_counter = Counter()
    for (jid, loc), obj in dedup.items():
        seed_fields = []
        for subloc, subobj in walk(obj, loc):
            if isinstance(subobj, dict):
                for k, v in subobj.items():
                    if "seed" in str(k).lower() and scalar(v):
                        path = f"{subloc}.{k}"
                        seed_fields.append({"json_path": path, "key": str(k), "value": v})
                        # Signature ignores list indices and the record's absolute location.
                        sig = str(k)
                        field_signature_counter[sig] += 1
        per_job[jid].append(
            {
                "object_path": loc,
                "top_level_keys": list(obj.keys()),
                "seed_scalar_fields": seed_fields,
            }
        )

    # Direct top-level record summaries are useful even if no job_id parser matches.
    top = {
        "type": type(data).__name__,
        "keys": list(data.keys()) if isinstance(data, dict) else None,
        "length": len(data) if isinstance(data, (dict, list)) else None,
    }

    return {
        "present": True,
        "path": SEED_LEDGER.as_posix(),
        "sha256": sha256(p),
        "top_level": top,
        "all_seed_scalar_count": len(all_seed_scalars),
        "all_seed_scalars": all_seed_scalars,
        "job_object_count": len(dedup),
        "distinct_job_ids_found": sorted(per_job.keys()),
        "distinct_job_id_count": len(per_job),
        "seed_key_frequency_across_job_objects": dict(field_signature_counter),
        "per_job": dict(per_job),
        "geonomics_jobs": {jid: per_job.get(jid, []) for jid in JOBS},
    }


def small_values(arr: np.ndarray, max_n: int = 300):
    if arr.ndim != 1 or arr.size > max_n:
        return None
    if arr.dtype.kind not in "biufUS":
        return None
    vals = arr.tolist()
    out = []
    for v in vals:
        if isinstance(v, bytes):
            out.append(v.decode("utf-8", errors="replace"))
        elif isinstance(v, np.generic):
            out.append(v.item())
        else:
            out.append(v)
    return out


def numeric_summary(arr: np.ndarray) -> dict[str, Any] | None:
    if arr.size == 0 or arr.dtype.kind not in "biuf":
        return None
    a = np.asarray(arr, dtype=float)
    finite = a[np.isfinite(a)]
    if not finite.size:
        return {"finite_count": 0}
    return {
        "finite_count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
    }


def npz_inventory(path: Path, root: Path) -> dict[str, Any]:
    out = {
        "path": rel(path, root),
        "exists": path.exists(),
    }
    if not path.exists():
        return out
    out["sha256"] = sha256(path)
    rows = []
    try:
        with np.load(path, allow_pickle=False) as z:
            for key in z.files:
                a = np.asarray(z[key])
                row = {
                    "key": key,
                    "shape": list(a.shape),
                    "dtype": str(a.dtype),
                }
                vals = small_values(a)
                if vals is not None:
                    row["values_if_small"] = vals
                ns = numeric_summary(a)
                if ns is not None and (
                    any(t in key.lower() for t in ("row", "col", "age", "time"))
                    or a.ndim == 1
                ):
                    row["numeric_summary"] = ns
                rows.append(row)
    except Exception as exc:
        out["load_error"] = repr(exc)
        return out
    out["array_count"] = len(rows)
    out["arrays"] = rows
    return out


def runtime_packages(root: Path) -> dict[str, Any]:
    p = root / R433_RUNTIME
    if not p.exists():
        return {"present": False, "path": R433_RUNTIME.as_posix()}

    reg = load(p)
    by = {r.get("job_id"): r for r in reg.get("records") or []}
    out = {}
    for jid in JOBS:
        r = by.get(jid) or {}
        relp = r.get("runtime_parameter_binding_package_file")
        pp = root / str(relp or "")
        pkg = load(pp) if relp and pp.exists() else {}
        inv = []
        for src in pkg.get("canonical_sources") or []:
            sp = root / str(src.get("path") or "")
            inv.append(npz_inventory(sp, root))
        out[jid] = {
            "registry_record": r,
            "package_path": relp,
            "package_exists": pp.exists(),
            "package_sha256_actual": sha256(pp) if pp.exists() else None,
            "package_top_level_keys": list(pkg.keys()) if isinstance(pkg, dict) else None,
            "selector_authority": pkg.get("selector_authority"),
            "mapping_fields": pkg.get("mapping_fields"),
            "canonical_sources": pkg.get("canonical_sources"),
            "canonical_source_inventories_from_r433": pkg.get("canonical_source_inventories"),
            "live_npz_inventories": inv,
        }
    return {
        "present": True,
        "path": R433_RUNTIME.as_posix(),
        "registry_record_count": reg.get("record_count"),
        "jobs": out,
    }


def blocked_gap_records(root: Path) -> dict[str, Any]:
    p = root / R435_CLOSURE
    if not p.exists():
        return {"present": False, "path": R435_CLOSURE.as_posix()}
    data = load(p)
    rows = []
    for r in data.get("records") or []:
        if not r.get("terminally_closed", False):
            rows.append(
                {
                    "job_id": r.get("job_id"),
                    "gap": r.get("gap"),
                    "disposition": r.get("disposition"),
                    "authority_status": (r.get("authority") or {}).get("status"),
                    "authority": r.get("authority"),
                }
            )
    return {
        "present": True,
        "path": R435_CLOSURE.as_posix(),
        "record_count": data.get("record_count"),
        "terminally_closed_gap_count": data.get("terminally_closed_gap_count"),
        "blocked_gap_count": data.get("blocked_gap_count"),
        "blocked_records": rows,
        "seed_authority_summary": data.get("seed_authority"),
        "job_summaries": data.get("job_summaries"),
    }


def json_if_present(root: Path, path: Path):
    p = root / path
    if not p.exists():
        return {"present": False, "path": path.as_posix()}
    try:
        data = load(p)
    except Exception as exc:
        return {
            "present": True,
            "path": path.as_posix(),
            "sha256": sha256(p),
            "parse_error": repr(exc),
        }
    return {
        "present": True,
        "path": path.as_posix(),
        "sha256": sha256(p),
        "data": data,
    }


def j14_authority_metadata(root: Path) -> dict[str, Any]:
    out = {
        "r431_seal": json_if_present(root, R431_J14_SEAL),
        "r430_authority_files": [],
    }
    d = root / R430_AUTHORITY_DIR
    if d.exists():
        for p in sorted(d.glob("*J14*")):
            if p.suffix.lower() == ".json":
                try:
                    data = load(p)
                except Exception as exc:
                    data = {"parse_error": repr(exc)}
                out["r430_authority_files"].append(
                    {
                        "path": rel(p, root),
                        "sha256": sha256(p),
                        "data": data,
                    }
                )
            elif p.suffix.lower() == ".npz":
                out["r430_authority_files"].append(npz_inventory(p, root))
    return out


def compare_j21_axes(runtime: dict[str, Any]) -> dict[str, Any]:
    job = runtime.get("jobs", {}).get(J21, {})
    axes = []
    for inv in job.get("live_npz_inventories") or []:
        for arr in inv.get("arrays") or []:
            if arr.get("key") == "anchor_age_ka":
                axes.append(
                    {
                        "source": inv.get("path"),
                        "values": arr.get("values_if_small"),
                        "shape": arr.get("shape"),
                        "dtype": arr.get("dtype"),
                    }
                )
    equal = False
    if len(axes) >= 2:
        first = axes[0].get("values")
        equal = first is not None and all(a.get("values") == first for a in axes[1:])
    return {
        "axis_copy_count": len(axes),
        "all_anchor_age_axes_exactly_equal_by_value": equal,
        "axes": axes,
    }


def main() -> int:
    root = Path(os.environ.get("ARCANA_PROJECT_ROOT", Path.cwd())).resolve()
    outdir = root / OUT
    outdir.mkdir(parents=True, exist_ok=True)

    seeds = seed_ledger_schema(root)
    runtime = runtime_packages(root)
    blocked = blocked_gap_records(root)
    j14meta = j14_authority_metadata(root)
    j18profile = json_if_present(root, R423_J18_PROFILE)
    r328auth = json_if_present(root, R328_AUTHORITY)
    j21axis = compare_j21_axes(runtime)

    report = {
        "stage": STAGE,
        "status": "DIAGNOSTIC_COMPLETE",
        "project_root": str(root),
        "seed_ledger_schema": seeds,
        "blocked_gap_records": blocked,
        "runtime_packages_and_live_npz_schema": runtime,
        "j14_authority_metadata": j14meta,
        "j18_r423_frozen_profile": j18profile,
        "r328_spatial_authority": r328auth,
        "j21_shared_time_axis_check": j21axis,
        "governance": {
            "external_engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
            "failed_r435_evidence_preserved": True,
            "gate_weakening_performed": False,
            "diagnostic_only": True,
        },
    }
    report_path = outdir / "R4_35_R1_LIVE_SEED_AND_SPATIAL_SCHEMA_DIAGNOSTIC.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    def compact_job_inventory(jid: str):
        j = runtime.get("jobs", {}).get(jid, {})
        return {
            "package_path": j.get("package_path"),
            "selector_authority": j.get("selector_authority"),
            "canonical_sources": j.get("canonical_sources"),
            "arrays": [
                {
                    "source": inv.get("path"),
                    "arrays": inv.get("arrays"),
                    "load_error": inv.get("load_error"),
                }
                for inv in j.get("live_npz_inventories") or []
            ],
        }

    console = {
        "stage": STAGE,
        "status": "DIAGNOSTIC_COMPLETE",
        "seed_ledger_schema": {
            "top_level": seeds.get("top_level"),
            "distinct_job_id_count": seeds.get("distinct_job_id_count"),
            "seed_key_frequency_across_job_objects":
                seeds.get("seed_key_frequency_across_job_objects"),
            "geonomics_jobs": seeds.get("geonomics_jobs"),
        },
        "blocked_gap_records": blocked.get("blocked_records"),
        "J14_runtime_inventory": compact_job_inventory(J14),
        "J18_runtime_inventory": compact_job_inventory(J18),
        "J21_shared_time_axis_check": j21axis,
        "J14_authority_metadata": j14meta,
        "J18_profile_translation": (
            (j18profile.get("data") or {}).get("translation")
            if j18profile.get("present") else None
        ),
        "R328_spatial_authority_core": {
            "status": (r328auth.get("data") or {}).get("status")
                if r328auth.get("present") else None,
            "spatial_state": (r328auth.get("data") or {}).get("spatial_state")
                if r328auth.get("present") else None,
            "source_path": r328auth.get("path"),
        },
        "report": rel(report_path, root),
        "governance": report["governance"],
    }

    print("=== R4.35-R1 live seed + spatial schema diagnostic ===")
    print(json.dumps(console, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
