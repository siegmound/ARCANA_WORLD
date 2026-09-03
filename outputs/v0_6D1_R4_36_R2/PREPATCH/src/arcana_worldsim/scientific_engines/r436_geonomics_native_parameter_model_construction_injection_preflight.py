from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import inspect
import json
import pprint
import re
import tempfile

import numpy as np

STAGE = "v0.6D1-R4.36"

PARENT_COMPLETE = (
    "PASS_R435_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
    "AND_SEED_AUTHORITY_CLOSURE_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R435_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_"
    "AND_SEED_AUTHORITY_CLOSURE_SEALED"
)
PARENT_NEXT = (
    "BUILD_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_"
    "CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT"
)

COMPLETE = (
    "PASS_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_"
    "CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_"
    "CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R436_NATIVE_PARAMETER_MODEL_CONSTRUCTION_OR_EXACT_STATE_"
    "INJECTION_PREFLIGHT_FAILURE"
)

NEXT = (
    "BUILD_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_"
    "INJECTION_DRY_RUN_VALIDATION"
)

CFG = Path(
    "configs/world1_r436_geonomics_native_parameter_materialization_model_"
    "construction_exact_state_injection_preflight_v0_6D1_R4_36.json"
)
PSEAL = Path("outputs/v0_6D1_R4_35_SEAL/R4_35_FINAL_SEAL_AUDIT.json")
PAUDIT = Path("outputs/v0_6D1_R4_35/R4_35_INTEGRATED_AUDIT.json")
PCLOSURE = Path(
    "outputs/v0_6D1_R4_35/"
    "R4_35_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_SEED_AUTHORITY_CLOSURE.json"
)
PPLAN = Path("outputs/v0_6D1_R4_35/R4_35_R436_EXECUTION_PLAN.json")

J14_SRC = Path(
    "outputs/v0_6D1_R4_30/authority/"
    "R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz"
)
J18_SRC = Path(
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz"
)
J21_ENV = Path(
    "outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz"
)
J21_PROD = Path(
    "outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"
)

OUT = Path("outputs/v0_6D1_R4_36")
SEAL = Path("outputs/v0_6D1_R4_36_SEAL/R4_36_FINAL_SEAL_AUDIT.json")

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
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def _gap_index(closure: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (r.get("job_id"), r.get("gap")): r
        for r in closure.get("records") or []
    }


def _geometry(closure: dict[str, Any], job_id: str) -> dict[str, Any]:
    r = _gap_index(closure).get((job_id, "LANDSCAPE_GEOMETRY_DIM_RES_ULC_PRJ")) or {}
    a = r.get("authority") or {}
    if not r.get("terminally_closed"):
        return {}
    return a


def _seed_vectors(closure: dict[str, Any]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for r in closure.get("seed_authority", {}).get("records") or []:
        jid = r.get("job_id")
        vals = r.get("replicate_seed_vector")
        if jid in JOBS and isinstance(vals, list) and len(vals) == 4:
            out[jid] = [int(v) for v in vals]
    return out


def _import_params_module(path: Path) -> dict[str, Any]:
    name = "r436_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import parameter module {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    params = getattr(mod, "params", None)
    if not isinstance(params, dict):
        raise TypeError(f"{path} did not expose dict `params`")
    return params


def _normalize_for_repr(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): _normalize_for_repr(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_normalize_for_repr(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_normalize_for_repr(x) for x in v)
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        raise TypeError("unexpected ndarray in template after raster sentinel replacement")
    return v


def _write_params_module(path: Path, params: dict[str, Any], rows: int, cols: int) -> None:
    p = copy.deepcopy(params)
    layers = p["landscape"]["layers"]
    if len(layers) != 1:
        raise ValueError("R4.36 construction params require exactly one scaffold layer")
    lname = next(iter(layers))
    defined = layers[lname]["init"]["defined"]
    defined["rast"] = "__R436_CONSTRUCTION_SUPPORT_RASTER__"
    defined["pts"] = None
    defined["vals"] = None
    defined["interp_method"] = None

    p = _normalize_for_repr(p)
    txt = pprint.pformat(p, width=120, sort_dicts=False)
    sentinel = repr("__R436_CONSTRUCTION_SUPPORT_RASTER__")
    if sentinel not in txt:
        raise RuntimeError("construction raster sentinel missing")
    txt = txt.replace(
        sentinel,
        f"np.ones(({rows}, {cols}), dtype=float)",
        1,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# ARCANA R4.36 Geonomics 1.4.9 native construction-preflight params\n"
        "# CONSTRUCTION ONLY — NOT SCIENTIFIC EXECUTION PARAMETERS\n"
        "import numpy as np\n\n"
        f"params = {txt}\n",
        encoding="utf-8",
    )


def _patch_template(
    template: dict[str, Any],
    *,
    job_id: str,
    replicate_index: int,
    seed: int,
    rows: int,
    cols: int,
) -> dict[str, Any]:
    p = copy.deepcopy(template)

    main = p["landscape"]["main"]
    main["dim"] = (cols, rows)
    main["res"] = (1, 1)
    main["ulc"] = (0, 0)
    main["prj"] = None

    layers = p["landscape"]["layers"]
    if len(layers) != 1:
        raise ValueError("template must expose exactly one defined construction layer")
    lname = next(iter(layers))

    species = p["comm"]["species"]
    if len(species) != 1:
        raise ValueError("template must expose exactly one construction-probe species")
    sname = next(iter(species))
    spp = species[sname]
    spp["init"]["N"] = 1
    spp["init"]["K_layer"] = lname
    spp["init"]["K_factor"] = 1
    if "movement" in spp:
        spp["movement"]["move"] = False
    # No genomic interpretation in a construction probe.
    spp.pop("gen_arch", None)

    model = p["model"]
    model["name"] = (
        f"ARCANA_R436_{job_id}_REP{replicate_index}_CONSTRUCTION_PREFLIGHT"
    )
    model["T"] = 0
    model["burn_T"] = 0
    # Geonomics 1.4.9 Model.__init__ reads model.seed.num. Some shipped
    # templates also retain legacy model.num. Keep the latter as a mirror,
    # but scientific seed authority is the nested seed.num value.
    model["seed"] = {"num": int(seed)}
    if "num" in model:
        model["num"] = int(seed)
    if "its" in model:
        model["its"]["n_its"] = 1
        model["its"]["rand_landscape"] = False
        model["its"]["rand_comm"] = False
        model["its"]["repeat_burn"] = False
        if "rand_genarch" in model["its"]:
            model["its"]["rand_genarch"] = False
    return p


def _make_template(gnx: Any, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    td = root / OUT / "geonomics_native" / "_schema_probe"
    td.mkdir(parents=True, exist_ok=True)
    raw = td / "GNX_R436_SCHEMA_PROBE.py"
    if raw.exists():
        raw.unlink()

    gnx.make_parameters_file(
        filepath=str(raw),
        layers=[{"type": "defined"}],
        species=[{"genomes": False, "movement": False}],
        data=False,
        stats=False,
    )
    params = _import_params_module(raw)
    evidence = {
        "schema_probe_file": raw.relative_to(root).as_posix(),
        "schema_probe_sha256": sha256(raw),
        "landscape_main_keys": list(params.get("landscape", {}).get("main", {}).keys()),
        "layer_count": len(params.get("landscape", {}).get("layers", {})),
        "species_count": len(params.get("comm", {}).get("species", {})),
        "model_keys": list(params.get("model", {}).keys()),
        "scientific_evidence": False,
        "purpose": "installed-Geonomics-1.4.9 schema discovery only",
    }
    return params, evidence


def _model_api_evidence(mod: Any) -> dict[str, Any]:
    method = getattr(mod, "add_individuals", None)
    sig = inspect.signature(method) if callable(method) else None
    params = list(sig.parameters.keys()) if sig is not None else []
    return {
        "model_type": str(type(mod)),
        "model_seed": getattr(mod, "seed", None),
        "model_t": getattr(mod, "t", None),
        "model_burn_t": getattr(mod, "burn_t", None),
        "model_it": getattr(mod, "it", None),
        "add_individuals_present": callable(method),
        "add_individuals_signature": str(sig) if sig is not None else None,
        "add_individuals_has_n_and_coords": "n" in params and "coords" in params,
    }


def _materialize_and_construct_native_params(
    root: Path,
    closure: dict[str, Any],
) -> dict[str, Any]:
    try:
        import geonomics as gnx
    except Exception as exc:
        return {
            "stage": STAGE,
            "status": "BLOCKED_R436_GEONOMICS_IMPORT",
            "error": repr(exc),
            "records": [],
        }

    version = str(getattr(gnx, "__version__", "UNKNOWN"))
    if version != "1.4.9":
        return {
            "stage": STAGE,
            "status": "BLOCKED_R436_GEONOMICS_VERSION",
            "geonomics_version": version,
            "records": [],
        }

    seeds = _seed_vectors(closure)
    if set(seeds) != set(JOBS):
        return {
            "stage": STAGE,
            "status": "BLOCKED_R436_SEED_VECTOR_AUTHORITY",
            "seed_jobs": sorted(seeds),
            "records": [],
        }

    try:
        template, schema_evidence = _make_template(gnx, root)
    except Exception as exc:
        return {
            "stage": STAGE,
            "status": "BLOCKED_R436_GEONOMICS_SCHEMA_PROBE",
            "geonomics_version": version,
            "error": repr(exc),
            "records": [],
        }

    records: list[dict[str, Any]] = []
    blocked = 0

    for jid in JOBS:
        geom = _geometry(closure, jid)
        rows, cols = geom.get("rows"), geom.get("cols")
        if not isinstance(rows, int) or not isinstance(cols, int) or rows <= 0 or cols <= 0:
            blocked += 4
            for rep, seed in enumerate(seeds[jid]):
                records.append({
                    "job_id": jid,
                    "replicate_index": rep,
                    "seed": seed,
                    "construction_pass": False,
                    "error": "R435_GEOMETRY_AUTHORITY_NOT_RESOLVED",
                })
            continue

        for rep, seed in enumerate(seeds[jid]):
            d = root / OUT / "geonomics_native" / jid / f"replicate_{rep}"
            pf = d / "GNX_NATIVE_CONSTRUCTION_PREFLIGHT_PARAMS.py"
            params = _patch_template(
                template,
                job_id=jid,
                replicate_index=rep,
                seed=seed,
                rows=rows,
                cols=cols,
            )
            _write_params_module(pf, params, rows, cols)

            rec = {
                "job_id": jid,
                "replicate_index": rep,
                "frozen_seed": seed,
                "native_parameter_file": pf.relative_to(root).as_posix(),
                "native_parameter_file_sha256": sha256(pf),
                "geometry_rows": rows,
                "geometry_cols": cols,
                "construction_scaffold_layer":
                    "BINARY_OR_UNITY_CONSTRUCTION_SUPPORT_ONLY",
                "construction_probe_species_N": 1,
                "construction_probe_is_scientific_population": False,
                "dynamics_parameters_are_construction_scaffold_only": True,
                "scientific_execution_authorized": False,
                "model_run_performed": False,
                "exact_state_injection_performed": False,
            }
            try:
                file_params = _import_params_module(pf)
                pdict = gnx.make_params_dict(
                    file_params,
                    model_name=file_params.get("model", {}).get("name"),
                )
                mod = gnx.make_model(parameters=pdict, verbose=False)
                api = _model_api_evidence(mod)
                seed_ok = api["model_seed"] == seed
                unrun = (
                    api["model_t"] == -1
                    and api["model_burn_t"] == -1
                    and api["model_it"] == -1
                )
                api_ok = api["add_individuals_has_n_and_coords"] is True
                rec.update({
                    "parameter_module_import_pass": True,
                    "make_params_dict_pass": True,
                    "make_model_pass": True,
                    "model_seed_match": seed_ok,
                    "model_unrun_state_verified": unrun,
                    "exact_state_injection_api_preflight_pass": api_ok,
                    "model_api_evidence": api,
                    "construction_pass": bool(seed_ok and unrun and api_ok),
                })
                if not rec["construction_pass"]:
                    blocked += 1
                del mod
            except Exception as exc:
                rec.update({
                    "parameter_module_import_pass": False,
                    "make_params_dict_pass": False,
                    "make_model_pass": False,
                    "construction_pass": False,
                    "error": repr(exc),
                })
                blocked += 1

            records.append(rec)

    passed = sum(bool(r.get("construction_pass")) for r in records)
    return {
        "stage": STAGE,
        "status":
            "R436_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT_COMPLETE"
            if len(records) == 12 and passed == 12 and blocked == 0
            else BLOCKED,
        "geonomics_version": version,
        "schema_evidence": schema_evidence,
        "record_count": len(records),
        "native_parameter_materialized_count": len(records),
        "model_construction_pass_count": passed,
        "model_construction_blocked_count": blocked,
        "gnx_make_model_performed_count": passed,
        "gnx_read_parameters_file_performed_count": 0,
        "model_run_performed_count": 0,
        "scientific_execution_performed": False,
        "exact_state_injection_performed_count": 0,
        "records": records,
    }


def _names(z: Any, key: str) -> list[str]:
    return [str(v) for v in np.asarray(z[key]).reshape(-1).tolist()]


def _geom_bounds(closure: dict[str, Any], jid: str) -> tuple[int, int]:
    g = _geometry(closure, jid)
    return int(g["rows"]), int(g["cols"])


def _j14_injection_manifest(root: Path, closure: dict[str, Any]) -> dict[str, Any]:
    p = root / J14_SRC
    rows, cols = _geom_bounds(closure, J14)
    with np.load(p, allow_pickle=False) as z:
        names = _names(z, "state_variable_names")
        low = [n.lower() for n in names]
        s = np.asarray(z["spatial_state"], dtype=float)
        ages = np.asarray(z["age_ma"], dtype=float)
        cids = _names(z, "candidate_ids")
        pi = low.index("population_proxy")
        ri = low.index("grid_row")
        ci = low.index("grid_col")
        ai = low.index("active")

        if s.ndim != 5 or s.shape[2] != ages.size or s.shape[1] != len(cids):
            raise ValueError("J14 spatial_state schema drift")

        branches = []
        invalid = 0
        carriers = 0
        t = 0
        for a0 in range(s.shape[0]):
            for c in range(s.shape[1]):
                st = s[a0, c, t, :, :]
                active = np.isfinite(st[:, ai]) & (st[:, ai] > 0.5)
                rows_out = []
                for deme_i in np.flatnonzero(active).tolist():
                    pop = float(st[deme_i, pi])
                    gr = float(st[deme_i, ri])
                    gc = float(st[deme_i, ci])
                    ok = (
                        np.isfinite(pop) and pop >= 0
                        and np.isfinite(gr) and 0 <= gr < rows
                        and np.isfinite(gc) and 0 <= gc < cols
                    )
                    invalid += 0 if ok else 1
                    rows_out.append({
                        "deme_slot_index": deme_i,
                        "x_grid_col": gc,
                        "y_grid_row": gr,
                        "population_proxy_sidecar_weight": pop,
                        "coordinate_valid": bool(ok),
                    })
                    carriers += 1
                branches.append({
                    "authority_axis0_storage_index": a0,
                    "candidate_id": cids[c],
                    "canonical_start_age_ma": float(ages[t]),
                    "carrier_count": len(rows_out),
                    "carriers": rows_out,
                })

    return {
        "stage": STAGE,
        "job_id": J14,
        "source_path": J14_SRC.as_posix(),
        "source_sha256": sha256(p),
        "source_semantics":
            "R431_SEALED_MODEL_DERIVED_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_NOT_OBSERVED_LOCATION_HISTORY",
        "initial_time_rule": "FIRST_ELEMENT_OF_FROZEN_DESCENDING_CANONICAL_AGE_AXIS",
        "branch_enumeration_rule": "ALL_STORAGE_AXIS0_X_ALL_CANDIDATE_IDS",
        "branch_count": len(branches),
        "total_carrier_count": carriers,
        "invalid_carrier_count": invalid,
        "population_proxy_is_literal_census": False,
        "api_target": "Model.add_individuals(n, coords, ...)",
        "exact_state_injection_performed_in_r436": False,
        "construction_probe_removal_required_before_future_injection": True,
        "branches": branches,
        "preflight_pass": invalid == 0 and len(branches) > 0 and carriers > 0,
    }


def _j18_injection_manifest(root: Path, closure: dict[str, Any]) -> dict[str, Any]:
    p = root / J18_SRC
    rows, cols = _geom_bounds(closure, J18)
    with np.load(p, allow_pickle=False) as z:
        names = _names(z, "state_variable_names")
        low = [n.lower() for n in names]
        s = np.asarray(z["snapshot_deme_state"], dtype=float)
        active = np.asarray(z["snapshot_active"], dtype=bool)
        ages = np.asarray(z["snapshot_age_ka"], dtype=float)
        parents = np.asarray(z["parent_member_indices"]).reshape(-1).tolist()
        cids = _names(z, "candidate_ids")
        pi = low.index("population_proxy")
        ri = low.index("grid_row")
        ci = low.index("grid_col")

        if (
            s.ndim != 5
            or active.shape != s.shape[:-1]
            or s.shape[0] != len(parents)
            or s.shape[1] != len(cids)
            or s.shape[2] != ages.size
        ):
            raise ValueError("J18 snapshot schema drift")

        branches = []
        invalid = 0
        carriers = 0
        t = 0
        for m in range(s.shape[0]):
            for c in range(s.shape[1]):
                st = s[m, c, t, :, :]
                mask = active[m, c, t, :]
                rows_out = []
                for deme_i in np.flatnonzero(mask).tolist():
                    pop = float(st[deme_i, pi])
                    gr = float(st[deme_i, ri])
                    gc = float(st[deme_i, ci])
                    ok = (
                        np.isfinite(pop) and pop >= 0
                        and np.isfinite(gr) and 0 <= gr < rows
                        and np.isfinite(gc) and 0 <= gc < cols
                    )
                    invalid += 0 if ok else 1
                    rows_out.append({
                        "deme_slot_index": deme_i,
                        "x_grid_col": gc,
                        "y_grid_row": gr,
                        "population_proxy_sidecar_weight": pop,
                        "coordinate_valid": bool(ok),
                    })
                    carriers += 1
                branches.append({
                    "parent_member_index": int(parents[m]),
                    "candidate_id": cids[c],
                    "canonical_start_age_ka": float(ages[t]),
                    "carrier_count": len(rows_out),
                    "carriers": rows_out,
                })

    return {
        "stage": STAGE,
        "job_id": J18,
        "source_path": J18_SRC.as_posix(),
        "source_sha256": sha256(p),
        "state_key": "snapshot_deme_state",
        "active_mask_key": "snapshot_active",
        "initial_time_rule": "FIRST_ELEMENT_OF_FROZEN_SNAPSHOT_AGE_AXIS",
        "branch_enumeration_rule": "ALL_PARENT_MEMBERS_X_ALL_CANDIDATE_IDS",
        "branch_count": len(branches),
        "total_carrier_count": carriers,
        "invalid_carrier_count": invalid,
        "coordinate_rule": "x=grid_col; y=grid_row; no center shift",
        "population_proxy_is_literal_census": False,
        "api_target": "Model.add_individuals(n, coords, ...)",
        "exact_state_injection_performed_in_r436": False,
        "construction_probe_removal_required_before_future_injection": True,
        "branches": branches,
        "preflight_pass": invalid == 0 and len(branches) > 0 and carriers > 0,
    }


def _j21_payload_manifest(root: Path, closure: dict[str, Any]) -> dict[str, Any]:
    ep = root / J21_ENV
    pp = root / J21_PROD
    rows, cols = _geom_bounds(closure, J21)

    layer_dir = root / OUT / "geonomics_canonical_payload" / J21 / "initial_layers"
    layer_dir.mkdir(parents=True, exist_ok=True)
    records = []

    with np.load(ep, allow_pickle=False) as z:
        ages_e = np.asarray(z["anchor_age_ka"], dtype=float)
        env = np.asarray(z["environment_fields"])
        enames = _names(z, "environment_variable_names")
        if env.shape != (len(ages_e), rows, cols, len(enames)):
            raise ValueError("J21 environment schema drift")
        for i, name in enumerate(enames):
            arr = np.asarray(env[0, :, :, i])
            fp = layer_dir / f"ENV_{i:03d}_{re.sub(r'[^A-Za-z0-9_]+','_',name)}.npy"
            np.save(fp, arr, allow_pickle=False)
            records.append({
                "layer_family": "environment",
                "name": name,
                "source_path": J21_ENV.as_posix(),
                "source_sha256": sha256(ep),
                "source_array": "environment_fields",
                "source_indices": [0, ":", ":", i],
                "canonical_start_age_ka": float(ages_e[0]),
                "payload_file": fp.relative_to(root).as_posix(),
                "payload_sha256": sha256(fp),
                "shape": list(arr.shape),
                "dtype": str(arr.dtype),
                "identity_value_preservation": True,
            })

    with np.load(pp, allow_pickle=False) as z:
        ages_p = np.asarray(z["anchor_age_ka"], dtype=float)
        prod = np.asarray(z["producer_landscape"])
        taxa = _names(z, "producer_taxon_ids")
        pnames = _names(z, "landscape_variable_names")
        if prod.shape != (len(taxa), len(ages_p), rows, cols, len(pnames)):
            raise ValueError("J21 producer schema drift")
        if not np.array_equal(ages_e, ages_p):
            raise ValueError("J21 anchor age copies are not exact-equivalent")
        for ti, taxon in enumerate(taxa):
            for vi, name in enumerate(pnames):
                arr = np.asarray(prod[ti, 0, :, :, vi])
                fp = layer_dir / (
                    f"PRD_{ti:03d}_{re.sub(r'[^A-Za-z0-9_]+','_',taxon)}_"
                    f"{vi:02d}_{re.sub(r'[^A-Za-z0-9_]+','_',name)}.npy"
                )
                np.save(fp, arr, allow_pickle=False)
                records.append({
                    "layer_family": "producer_support",
                    "taxon_id": taxon,
                    "name": name,
                    "source_path": J21_PROD.as_posix(),
                    "source_sha256": sha256(pp),
                    "source_array": "producer_landscape",
                    "source_indices": [ti, 0, ":", ":", vi],
                    "canonical_start_age_ka": float(ages_p[0]),
                    "payload_file": fp.relative_to(root).as_posix(),
                    "payload_sha256": sha256(fp),
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                    "identity_value_preservation": True,
                })

    ok = (
        len(records) == 151
        and all(r["shape"] == [rows, cols] for r in records)
    )
    return {
        "stage": STAGE,
        "job_id": J21,
        "status":
            "R436_J21_INITIAL_CANONICAL_LAYER_PAYLOAD_MATERIALIZED"
            if ok else "BLOCKED_R436_J21_CANONICAL_LAYER_PAYLOAD",
        "canonical_start_age_ka": float(ages_e[0]),
        "environment_layer_count": len(enames),
        "producer_taxon_count": len(taxa),
        "producer_variable_count": len(pnames),
        "producer_support_layer_count": len(taxa) * len(pnames),
        "total_canonical_layer_payload_count": len(records),
        "cross_layer_numeric_fusion_performed": False,
        "automatic_rescaling_performed": False,
        "native_model_layer_binding_performed_in_r436": False,
        "scientific_execution_performed": False,
        "records": records,
        "preflight_pass": ok,
    }


def _exact_state_and_payload_preflight(root: Path, closure: dict[str, Any]) -> dict[str, Any]:
    try:
        j14 = _j14_injection_manifest(root, closure)
        j18 = _j18_injection_manifest(root, closure)
        j21 = _j21_payload_manifest(root, closure)
    except Exception as exc:
        return {
            "stage": STAGE,
            "status": "BLOCKED_R436_EXACT_STATE_OR_CANONICAL_PAYLOAD_PREFLIGHT",
            "error": repr(exc),
            "records": [],
        }

    j14p = root / OUT / "exact_state_injection" / J14 / "INITIAL_STATE_INJECTION_PREFLIGHT.json"
    j18p = root / OUT / "exact_state_injection" / J18 / "INITIAL_STATE_INJECTION_PREFLIGHT.json"
    j21p = root / OUT / "geonomics_canonical_payload" / J21 / "INITIAL_LAYER_PAYLOAD_MANIFEST.json"
    write(j14p, j14)
    write(j18p, j18)
    write(j21p, j21)

    ok = (
        j14.get("preflight_pass") is True
        and j18.get("preflight_pass") is True
        and j21.get("preflight_pass") is True
    )
    return {
        "stage": STAGE,
        "status":
            "R436_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT_COMPLETE"
            if ok else BLOCKED,
        "record_count": 3,
        "j14_injection_manifest": j14p.relative_to(root).as_posix(),
        "j14_injection_manifest_sha256": sha256(j14p),
        "j14_branch_count": j14.get("branch_count"),
        "j14_carrier_count": j14.get("total_carrier_count"),
        "j18_injection_manifest": j18p.relative_to(root).as_posix(),
        "j18_injection_manifest_sha256": sha256(j18p),
        "j18_branch_count": j18.get("branch_count"),
        "j18_carrier_count": j18.get("total_carrier_count"),
        "j21_payload_manifest": j21p.relative_to(root).as_posix(),
        "j21_payload_manifest_sha256": sha256(j21p),
        "j21_canonical_layer_payload_count": j21.get("total_canonical_layer_payload_count"),
        "exact_state_injection_performed_count": 0,
        "native_model_canonical_layer_binding_performed": False,
        "scientific_execution_performed": False,
        "preflight_pass": ok,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    ps = load(root / PSEAL)
    pa = load(root / PAUDIT)
    closure = load(root / PCLOSURE)
    pp = load(root / PPLAN)

    native = _materialize_and_construct_native_params(root, closure)
    write(
        root / OUT / "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json",
        native,
    )

    payload = _exact_state_and_payload_preflight(root, closure)
    write(
        root / OUT / "R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json",
        payload,
    )

    checks = [
        Check(
            "parent_r435_sealed",
            ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED",
            ps.get("status"),
        ),
        Check(
            "parent_r435_complete",
            pa.get("status") == PARENT_COMPLETE and pa.get("checks_failed") == 0,
            pa.get("status"),
        ),
        Check(
            "parent_next_action_matches_r436",
            pa.get("next_action") == PARENT_NEXT and ps.get("next_action") == PARENT_NEXT,
            {"audit": pa.get("next_action"), "seal": ps.get("next_action")},
        ),
        Check(
            "parent_r436_plan_frozen",
            pp.get("status")
            == "R435_NATIVE_SCHEMA_INITIAL_STATE_AND_SEED_AUTHORITY_EVIDENCE_FROZEN",
            pp.get("status"),
        ),
        Check(
            "parent_exact_19_authority_gaps_closed",
            closure.get("record_count") == 19
            and closure.get("terminally_closed_gap_count") == 19
            and closure.get("blocked_gap_count") == 0,
        ),
        Check(
            "parent_three_job_closures_pass",
            closure.get("job_closure_pass_count") == 3,
            closure.get("job_closure_pass_count"),
        ),
        Check(
            "parent_23x4_seed_vectors_preserved",
            closure.get("seed_authority", {}).get("exact_23_job_replicate_seed_vectors") is True
            and closure.get("seed_authority", {}).get("all_92_replicate_seeds_globally_unique") is True,
        ),
        Check(
            "policy_frozen",
            cfg.get("policy")
            == "FROZEN_POST_R435_MODEL_CONSTRUCTION_ALLOWED_SCIENTIFIC_EXECUTION_FORBIDDEN",
            cfg.get("policy"),
        ),
        Check(
            "geonomics_version_1_4_9",
            native.get("geonomics_version") == "1.4.9",
            native.get("geonomics_version"),
        ),
        Check(
            "native_parameter_files_exact_12",
            native.get("record_count") == 12
            and native.get("native_parameter_materialized_count") == 12,
            native.get("native_parameter_materialized_count"),
        ),
        Check(
            "all_12_model_constructions_pass",
            native.get("model_construction_pass_count") == 12
            and native.get("model_construction_blocked_count") == 0,
            native.get("model_construction_pass_count"),
        ),
        Check(
            "all_12_frozen_seeds_bound_exactly",
            all(r.get("model_seed_match") is True for r in native.get("records") or []),
        ),
        Check(
            "all_12_models_verified_unrun",
            all(r.get("model_unrun_state_verified") is True for r in native.get("records") or []),
        ),
        Check(
            "all_12_add_individuals_api_preflights_pass",
            all(
                r.get("exact_state_injection_api_preflight_pass") is True
                for r in native.get("records") or []
            ),
        ),
        Check(
            "schema_probe_not_scientific_evidence",
            native.get("schema_evidence", {}).get("scientific_evidence") is False,
        ),
        Check(
            "exact_state_and_payload_preflight_pass",
            payload.get("preflight_pass") is True,
            payload.get("status"),
        ),
        Check(
            "j14_all_initial_branches_enumerated",
            payload.get("j14_branch_count") == 192,
            payload.get("j14_branch_count"),
        ),
        Check(
            "j18_all_initial_branches_enumerated",
            payload.get("j18_branch_count") == 64,
            payload.get("j18_branch_count"),
        ),
        Check(
            "j14_j18_nonzero_carrier_payload",
            (payload.get("j14_carrier_count") or 0) > 0
            and (payload.get("j18_carrier_count") or 0) > 0,
            {
                "J14": payload.get("j14_carrier_count"),
                "J18": payload.get("j18_carrier_count"),
            },
        ),
        Check(
            "j21_exact_151_initial_payload_layers",
            payload.get("j21_canonical_layer_payload_count") == 151,
            payload.get("j21_canonical_layer_payload_count"),
        ),
        Check(
            "exact_state_injection_not_yet_performed",
            payload.get("exact_state_injection_performed_count") == 0,
        ),
        Check(
            "canonical_layers_not_yet_bound_into_model",
            payload.get("native_model_canonical_layer_binding_performed") is False,
        ),
        Check(
            "no_model_run",
            native.get("model_run_performed_count") == 0,
        ),
        Check(
            "no_scientific_execution",
            native.get("scientific_execution_performed") is False
            and payload.get("scientific_execution_performed") is False
            and cfg.get("scientific_engine_execution_performed") is False,
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
            "default_model_execution_forbidden",
            cfg.get("run_default_model_forbidden") is True,
        ),
        Check(
            "construction_probe_never_scientific_population",
            all(
                r.get("construction_probe_is_scientific_population") is False
                for r in native.get("records") or []
            ),
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
            "R436_NATIVE_PARAMS_MODEL_CONSTRUCTION_AND_INJECTION_PREFLIGHT_EVIDENCE_FROZEN"
            if ok else BLOCKED,
        "native_parameter_materialized_count": native.get("native_parameter_materialized_count"),
        "model_construction_pass_count": native.get("model_construction_pass_count"),
        "j14_initial_branch_count": payload.get("j14_branch_count"),
        "j18_initial_branch_count": payload.get("j18_branch_count"),
        "j21_initial_canonical_layer_payload_count":
            payload.get("j21_canonical_layer_payload_count"),
        "exact_state_injection_performed_count": 0,
        "canonical_layer_model_binding_performed": False,
        "geonomics_scientific_execution_authorized_in_r436": False,
        "target_numeric_execution_authorized_in_r436": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok
            else "REPAIR_R436_NATIVE_PARAMETER_MODEL_CONSTRUCTION_OR_INJECTION_PREFLIGHT",
    }
    write(root / OUT / "R4_36_R437_EXECUTION_PLAN.json", plan)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "native_parameter_materialized_count": native.get("native_parameter_materialized_count"),
        "gnx_make_model_performed_count": native.get("gnx_make_model_performed_count"),
        "model_construction_pass_count": native.get("model_construction_pass_count"),
        "j14_initial_branch_count": payload.get("j14_branch_count"),
        "j18_initial_branch_count": payload.get("j18_branch_count"),
        "j21_initial_canonical_layer_payload_count":
            payload.get("j21_canonical_layer_payload_count"),
        "exact_state_injection_performed_count": 0,
        "model_run_performed_count": 0,
        "geonomics_execution_ready": False,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_36_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    ps = load(root / PSEAL) if (root / PSEAL).exists() else {}
    a = load(root / OUT / "R4_36_INTEGRATED_AUDIT.json") if (
        root / OUT / "R4_36_INTEGRATED_AUDIT.json"
    ).exists() else {}
    n = load(
        root / OUT / "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
    ) if (
        root / OUT / "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
    ).exists() else {}
    p = load(
        root / OUT / "R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json"
    ) if (
        root / OUT / "R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json"
    ).exists() else {}
    plan = load(root / OUT / "R4_36_R437_EXECUTION_PLAN.json") if (
        root / OUT / "R4_36_R437_EXECUTION_PLAN.json"
    ).exists() else {}

    checks = [
        Check("parent_r435_sealed", ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED"),
        Check("r436_complete", a.get("status") == COMPLETE, a.get("status")),
        Check("r436_zero_process_failures", a.get("checks_failed") == 0, a.get("checks_failed")),
        Check(
            "native_params_exact_12",
            n.get("native_parameter_materialized_count") == 12,
        ),
        Check(
            "all_12_models_constructed",
            n.get("model_construction_pass_count") == 12
            and n.get("model_construction_blocked_count") == 0,
        ),
        Check(
            "all_12_models_unrun",
            all(r.get("model_unrun_state_verified") is True for r in n.get("records") or []),
        ),
        Check(
            "all_12_seed_bindings_exact",
            all(r.get("model_seed_match") is True for r in n.get("records") or []),
        ),
        Check(
            "add_individuals_api_available_all_models",
            all(
                r.get("exact_state_injection_api_preflight_pass") is True
                for r in n.get("records") or []
            ),
        ),
        Check("j14_all_192_initial_branches", p.get("j14_branch_count") == 192),
        Check("j18_all_64_initial_branches", p.get("j18_branch_count") == 64),
        Check("j21_151_initial_layer_payloads", p.get("j21_canonical_layer_payload_count") == 151),
        Check("exact_state_injection_not_performed", p.get("exact_state_injection_performed_count") == 0),
        Check("canonical_layer_model_binding_not_performed", p.get("native_model_canonical_layer_binding_performed") is False),
        Check("no_model_run", n.get("model_run_performed_count") == 0),
        Check("no_scientific_execution", n.get("scientific_execution_performed") is False),
        Check(
            "r437_plan_frozen",
            plan.get("status")
            == "R436_NATIVE_PARAMS_MODEL_CONSTRUCTION_AND_INJECTION_PREFLIGHT_EVIDENCE_FROZEN",
            plan.get("status"),
        ),
        Check(
            "scientific_execution_not_authorized",
            plan.get("geonomics_scientific_execution_authorized_in_r436") is False,
        ),
        Check(
            "target_numeric_execution_not_authorized",
            plan.get("target_numeric_execution_authorized_in_r436") is False,
        ),
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
            "FINAL_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_CONSTRUCTION_"
            "AND_EXACT_STATE_INJECTION_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.d() for c in checks],
        "summary": {
            "native_parameter_materialized_count": n.get("native_parameter_materialized_count"),
            "gnx_make_model_performed_count": n.get("gnx_make_model_performed_count"),
            "model_construction_pass_count": n.get("model_construction_pass_count"),
            "j14_initial_branch_count": p.get("j14_branch_count"),
            "j18_initial_branch_count": p.get("j18_branch_count"),
            "j21_initial_canonical_layer_payload_count": p.get("j21_canonical_layer_payload_count"),
            "exact_state_injection_performed_count": 0,
            "model_run_performed_count": 0,
            "geonomics_scientific_execution_authorized": False,
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
