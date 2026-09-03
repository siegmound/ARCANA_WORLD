from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import json
import pprint
import warnings

import numpy as np

STAGE = "v0.6D1-R4.37"

PARENT_COMPLETE = (
    "PASS_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_"
    "CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_"
    "CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT_SEALED"
)
PARENT_CHAIN_CLOSED = (
    "PASS_R436_R3_REPAIR_CHAIN_CLOSED_R436_AUTHORITATIVE_SEAL_PRESERVED"
)
PARENT_NEXT = (
    "BUILD_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_"
    "INJECTION_DRY_RUN_VALIDATION"
)

COMPLETE = (
    "PASS_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_"
    "INJECTION_DRY_RUN_VALIDATION_COMPLETE"
)
SEALED = (
    "PASS_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_"
    "INJECTION_DRY_RUN_VALIDATION_SEALED"
)
BLOCKED = (
    "BLOCKED_R437_CANONICAL_LAYER_BINDING_OR_EXACT_STATE_INJECTION_"
    "DRY_RUN_VALIDATION_FAILURE"
)
NEXT = (
    "BUILD_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_"
    "PROBE_ELIMINATION_PREFLIGHT"
)

CFG = Path(
    "configs/world1_r437_geonomics_canonical_layer_binding_exact_state_"
    "injection_dry_run_validation_v0_6D1_R4_37.json"
)

R436_AUDIT = Path("outputs/v0_6D1_R4_36/R4_36_INTEGRATED_AUDIT.json")
R436_SEAL = Path("outputs/v0_6D1_R4_36_SEAL/R4_36_FINAL_SEAL_AUDIT.json")
R436_CHAIN = Path(
    "outputs/v0_6D1_R4_36_R3/R4_36_R3_REPAIR_CHAIN_CLOSURE_AUDIT.json"
)
R436_NATIVE = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
)
R436_PAYLOAD = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json"
)

OUT = Path("outputs/v0_6D1_R4_37")
SEAL = Path("outputs/v0_6D1_R4_37_SEAL/R4_37_FINAL_SEAL_AUDIT.json")

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"
JOBS = (J14, J18, J21)

J14_INJECTION = Path(
    "outputs/v0_6D1_R4_36/exact_state_injection/"
    f"{J14}/INITIAL_STATE_INJECTION_PREFLIGHT.json"
)
J18_INJECTION = Path(
    "outputs/v0_6D1_R4_36/exact_state_injection/"
    f"{J18}/INITIAL_STATE_INJECTION_PREFLIGHT.json"
)
J21_PAYLOAD = Path(
    "outputs/v0_6D1_R4_36/geonomics_canonical_payload/"
    f"{J21}/INITIAL_LAYER_PAYLOAD_MANIFEST.json"
)


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


def _import_params_module(path: Path) -> dict[str, Any]:
    name = "r437_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import parameter module {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    params = getattr(mod, "params", None)
    if not isinstance(params, dict):
        raise TypeError(f"{path} did not expose dict `params`")
    return params


def _normalize(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): _normalize(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_normalize(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_normalize(x) for x in v)
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        raise TypeError("unexpected ndarray in R4.37 base params")
    return v


def _native_records(native: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    rows = [
        r for r in native.get("records") or []
        if r.get("job_id") == job_id and r.get("construction_pass") is True
    ]
    return sorted(rows, key=lambda r: int(r["replicate_index"]))


def _verify_manifest_hash(
    root: Path, parent_payload: dict[str, Any], key_path: str, key_hash: str
) -> dict[str, Any]:
    p = root / parent_payload[key_path]
    actual = sha256(p)
    expected = parent_payload[key_hash]
    return {
        "path": parent_payload[key_path],
        "expected_sha256": expected,
        "actual_sha256": actual,
        "hash_match": actual == expected,
    }


def _payload_range_audit(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Classify canonical payloads by native Geonomics Layer representability.

    R4.37-R2 NEVER derives a scaling transform from live min/max values.
    Canonical arrays already in [0,1] may be identity-bound as Geonomics
    Layer.rast. Canonical physical-unit arrays outside that domain remain
    hash-bound sidecars in their native units.
    """
    rows = []
    native_count = 0
    sidecar_count = 0
    allowed_sidecars = {
        "temperature_anomaly_c",
        "sea_level_anomaly_m",
    }

    for rec in manifest.get("records") or []:
        p = root / rec["payload_file"]
        hash_ok = p.exists() and sha256(p) == rec["payload_sha256"]
        if not hash_ok:
            rows.append({
                "payload_file": rec["payload_file"],
                "hash_match": False,
                "finite": False,
                "range_0_1": False,
                "binding_class": "BLOCKED_INTEGRITY",
            })
            continue

        a = np.load(p, allow_pickle=False)
        finite = bool(np.all(np.isfinite(a)))
        amin = float(np.min(a)) if a.size else None
        amax = float(np.max(a)) if a.size else None
        range_ok = bool(
            finite and a.size > 0 and amin is not None and amax is not None
            and amin >= 0.0 and amax <= 1.0
        )
        var_name = str(rec.get("name") or "")
        if range_ok:
            binding_class = "GEONOMICS_NATIVE_IDENTITY_LAYER"
            native_count += 1
        elif (
            finite
            and rec.get("layer_family") == "environment"
            and var_name in allowed_sidecars
        ):
            binding_class = "CANONICAL_PHYSICAL_UNIT_SIDECAR"
            sidecar_count += 1
        else:
            binding_class = "BLOCKED_UNAUTHORIZED_REPRESENTATION"

        rows.append({
            "payload_file": rec["payload_file"],
            "payload_sha256": rec["payload_sha256"],
            "hash_match": hash_ok,
            "finite": finite,
            "min": amin,
            "max": amax,
            "range_0_1": range_ok,
            "layer_family": rec.get("layer_family"),
            "variable_name": var_name,
            "binding_class": binding_class,
        })

    all_hash = all(r.get("hash_match") for r in rows)
    no_unauthorized = all(
        r.get("binding_class") in {
            "GEONOMICS_NATIVE_IDENTITY_LAYER",
            "CANONICAL_PHYSICAL_UNIT_SIDECAR",
        }
        for r in rows
    )
    return {
        "record_count": len(rows),
        "all_hashes_match": all_hash,
        "native_identity_layer_count": native_count,
        "canonical_physical_unit_sidecar_count": sidecar_count,
        "expected_native_identity_layer_count": 149,
        "expected_canonical_physical_unit_sidecar_count": 2,
        "exact_authorized_representability_partition": (
            all_hash and no_unauthorized
            and native_count == 149 and sidecar_count == 2
        ),
        "automatic_rescaling_performed": False,
        "result_selected_transform_performed": False,
        "canonical_values_modified": False,
        "records": rows,
    }


def _write_j21_bound_params(
    path: Path,
    base_params: dict[str, Any],
    payload_records: list[dict[str, Any]],
    *,
    rows: int,
    cols: int,
    seed: int,
    replicate_index: int,
) -> list[dict[str, Any]]:
    p = copy.deepcopy(base_params)
    p["landscape"]["main"]["dim"] = (cols, rows)
    p["landscape"]["main"]["res"] = (1, 1)
    p["landscape"]["main"]["ulc"] = (0, 0)
    p["landscape"]["main"]["prj"] = None
    p["landscape"]["layers"] = {}

    species = p["comm"]["species"]
    if len(species) != 1:
        raise ValueError("R4.37 requires one construction-probe species")
    sname = next(iter(species))
    species[sname]["init"]["N"] = 1
    species[sname]["init"]["K_layer"] = "R437_CONSTRUCTION_SUPPORT"
    species[sname]["init"]["K_factor"] = 1
    if "movement" in species[sname]:
        species[sname]["movement"]["move"] = False

    p["model"]["name"] = f"ARCANA_R437_{J21}_REP{replicate_index}_LAYER_BINDING"
    p["model"]["T"] = 0
    p["model"]["burn_T"] = 0
    p["model"]["seed"] = {"num": int(seed)}
    if "num" in p["model"]:
        p["model"]["num"] = int(seed)

    p = _normalize(p)
    base_txt = pprint.pformat(p, width=120, sort_dicts=False)

    specs = []
    mapping = []
    for i, rec in enumerate(payload_records):
        if rec.get("layer_family") == "environment":
            lname = f"R437_ENV_{i:03d}"
        else:
            lname = f"R437_PRD_{i:03d}"
        specs.append((lname, rec["payload_file"]))
        mapping.append({
            "native_layer_name": lname,
            "payload_file": rec["payload_file"],
            "payload_sha256": rec["payload_sha256"],
            "layer_family": rec.get("layer_family"),
            "taxon_id": rec.get("taxon_id"),
            "variable_name": rec.get("name"),
        })

    specs_txt = pprint.pformat(specs, width=120, sort_dicts=False)
    src = f"""# ARCANA R4.37 Geonomics 1.4.9 canonical-layer binding dry-run params
# 151 canonical identity-value payloads + 1 non-scientific construction support layer.
import numpy as np
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = None
for _anc in _HERE.parents:
    if _anc.name == "outputs":
        _ROOT = _anc.parent
        break
if _ROOT is None:
    raise RuntimeError("R4.37 cannot resolve ARCANA project root")

params = {base_txt}

params["landscape"]["layers"]["R437_CONSTRUCTION_SUPPORT"] = {{
    "init": {{
        "defined": {{
            "rast": np.ones(({rows}, {cols}), dtype=float),
            "pts": None,
            "vals": None,
            "interp_method": None,
        }}
    }}
}}

_PAYLOAD_SPECS = {specs_txt}
for _lname, _rel in _PAYLOAD_SPECS:
    params["landscape"]["layers"][_lname] = {{
        "init": {{
            "defined": {{
                "rast": np.load(_ROOT / _rel, allow_pickle=False),
                "pts": None,
                "vals": None,
                "interp_method": None,
            }}
        }}
}}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(src, encoding="utf-8")
    return mapping


def _j21_native_layer_binding(
    root: Path,
    native: dict[str, Any],
    payload_manifest: dict[str, Any],
) -> dict[str, Any]:
    try:
        import geonomics as gnx
    except Exception as exc:
        return {"status": "BLOCKED_R437_GEONOMICS_IMPORT", "error": repr(exc)}

    version = str(getattr(gnx, "__version__", "UNKNOWN"))
    if version != "1.4.9":
        return {
            "status": "BLOCKED_R437_GEONOMICS_VERSION",
            "geonomics_version": version,
        }

    range_audit = _payload_range_audit(root, payload_manifest)
    if not (
        range_audit["record_count"] == 151
        and range_audit["all_hashes_match"]
        and range_audit["exact_authorized_representability_partition"]
    ):
        return {
            "status": "BLOCKED_R437_J21_CANONICAL_REPRESENTABILITY_PARTITION",
            "geonomics_version": version,
            "range_audit": range_audit,
            "automatic_rescaling_performed": False,
            "result_selected_transform_performed": False,
        }

    base_rows = _native_records(native, J21)
    if len(base_rows) != 4:
        return {
            "status": "BLOCKED_R437_J21_R436_NATIVE_BASE_NOT_EXACT_4",
            "base_record_count": len(base_rows),
        }

    range_index = {
        r["payload_file"]: r
        for r in range_audit["records"]
    }
    payload_records = [
        r for r in payload_manifest["records"]
        if range_index[r["payload_file"]]["binding_class"]
        == "GEONOMICS_NATIVE_IDENTITY_LAYER"
    ]
    physical_sidecars = [
        r for r in payload_manifest["records"]
        if range_index[r["payload_file"]]["binding_class"]
        == "CANONICAL_PHYSICAL_UNIT_SIDECAR"
    ]
    records = []
    for base in base_rows:
        rep = int(base["replicate_index"])
        seed = int(base["frozen_seed"])
        base_file = root / base["native_parameter_file"]
        if sha256(base_file) != base["native_parameter_file_sha256"]:
            records.append({
                "replicate_index": rep,
                "pass": False,
                "error": "R436_NATIVE_PARAMETER_HASH_MISMATCH",
            })
            continue

        base_params = _import_params_module(base_file)
        out_file = (
            root / OUT / "geonomics_native" / J21 / f"replicate_{rep}"
            / "GNX_R437_CANONICAL_LAYER_BOUND_PARAMS.py"
        )
        mapping = _write_j21_bound_params(
            out_file,
            base_params,
            payload_records,
            rows=90,
            cols=180,
            seed=seed,
            replicate_index=rep,
        )

        try:
            params = _import_params_module(out_file)
            pdict = gnx.make_params_dict(params, model_name=params["model"]["name"])
            mod = gnx.make_model(parameters=pdict, verbose=False)

            layer_by_name = {lyr.name: lyr for lyr in mod.land.values()}
            exact = 0
            mismatches = []
            for m in mapping:
                lname = m["native_layer_name"]
                arr = np.load(root / m["payload_file"], allow_pickle=False)
                lyr = layer_by_name.get(lname)
                same = (
                    lyr is not None
                    and lyr.rast.shape == arr.shape
                    and np.array_equal(lyr.rast, arr)
                )
                exact += int(same)
                if not same:
                    mismatches.append(lname)

            support = layer_by_name.get("R437_CONSTRUCTION_SUPPORT")
            support_ok = (
                support is not None
                and support.rast.shape == (90, 180)
                and np.array_equal(support.rast, np.ones((90, 180)))
            )
            unrun = mod.t == -1 and mod.burn_t == -1 and mod.it == -1
            seed_ok = mod.seed == seed
            passed = (
                len(mod.land) == 150
                and exact == 149
                and not mismatches
                and support_ok
                and unrun
                and seed_ok
            )
            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "bound_parameter_file": out_file.relative_to(root).as_posix(),
                "bound_parameter_file_sha256": sha256(out_file),
                "native_landscape_layer_count": len(mod.land),
                "canonical_layer_count": 149,
                "canonical_physical_unit_sidecar_count": 2,
                "canonical_physical_unit_sidecars": [
                    {
                        "payload_file": s["payload_file"],
                        "payload_sha256": s["payload_sha256"],
                        "variable_name": s.get("name"),
                        "native_units_preserved": True,
                        "bound_as_geonomics_layer": False,
                    }
                    for s in physical_sidecars
                ],
                "canonical_layers_exact_identity_match_count": exact,
                "canonical_layer_mismatches": mismatches,
                "construction_support_layer_present": support_ok,
                "construction_support_layer_is_scientific_evidence": False,
                "model_seed_match": seed_ok,
                "model_unrun": unrun,
                "model_run_performed": False,
                "pass": passed,
            })
            del mod
        except Exception as exc:
            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "bound_parameter_file": out_file.relative_to(root).as_posix(),
                "bound_parameter_file_sha256": sha256(out_file),
                "pass": False,
                "error": repr(exc),
            })

    passed = sum(bool(r.get("pass")) for r in records)
    return {
        "status":
            "R437_J21_CANONICAL_NATIVE_LAYER_BINDING_VALIDATED"
            if len(records) == 4 and passed == 4
            else BLOCKED,
        "geonomics_version": version,
        "range_audit": range_audit,
        "replicate_count": len(records),
        "replicate_pass_count": passed,
        "canonical_payload_count": 151,
        "native_identity_payload_count": 149,
        "canonical_physical_unit_sidecar_count": 2,
        "canonical_layer_binding_count": 149 * passed,
        "physical_sidecar_binding_count": 2,
        "result_selected_transform_performed": False,
        "automatic_rescaling_performed": False,
        "cross_layer_numeric_fusion_performed": False,
        "model_run_performed_count": 0,
        "records": records,
    }


def _coords_digest(coords: list[list[float]]) -> str:
    payload = json.dumps(coords, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _exact_state_public_api_dry_run(
    root: Path,
    native: dict[str, Any],
    job_id: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Validate exact coordinate representability and freeze public-API incompatibility.

    Live R4.37 proved that Geonomics 1.4.9 Model.add_individuals() is not a
    valid fresh-model initializer for the intentionally nongenomic R4.36
    construction probe. R4.37-R3 therefore stops invoking that mutation path.

    This function constructs the same governed unrun models, verifies all
    canonical coordinates against the actual native Landscape bounds, and
    introspects the installed runtime source to prove the exact API mismatch.
    It does not mutate Individuals, Species, Landscape state, or burn flags.
    """
    try:
        import geonomics as gnx
        import inspect
    except Exception as exc:
        return {"status": "BLOCKED_R437_GEONOMICS_IMPORT", "error": repr(exc)}

    rows = _native_records(native, job_id)
    if len(rows) != 4:
        return {
            "status": "BLOCKED_R437_R436_NATIVE_BASE_NOT_EXACT_4",
            "job_id": job_id,
            "base_record_count": len(rows),
        }

    branches = manifest.get("branches") or []
    canonical_coords = [
        [float(c["x_grid_col"]), float(c["y_grid_row"])]
        for b in branches
        for c in (b.get("carriers") or [])
    ]
    expected_total = int(manifest.get("total_carrier_count") or -1)
    records = []

    for base in rows:
        rep = int(base["replicate_index"])
        seed = int(base["frozen_seed"])
        pf = root / base["native_parameter_file"]
        if sha256(pf) != base["native_parameter_file_sha256"]:
            records.append({
                "replicate_index": rep,
                "pass": False,
                "error": "R436_NATIVE_PARAMETER_HASH_MISMATCH",
            })
            continue

        try:
            params = _import_params_module(pf)
            pdict = gnx.make_params_dict(params, model_name=params["model"]["name"])
            mod = gnx.make_model(parameters=pdict, verbose=False)
            spp = mod.comm[0]

            seed_ok = mod.seed == seed
            unrun = mod.t == -1 and mod.burn_t == -1 and mod.it == -1
            dim = [float(mod.land.dim[0]), float(mod.land.dim[1])]
            probe_nongenomic = spp.gen_arch is None

            bad = []
            max_margin_violation = 0.0
            for i, coord in enumerate(canonical_coords):
                x, y = coord
                x_ok = bool(np.isfinite(x) and 0.0 <= x <= dim[0] - 0.001)
                y_ok = bool(np.isfinite(y) and 0.0 <= y <= dim[1] - 0.001)
                if not (x_ok and y_ok):
                    bad.append({"carrier_index": i, "x": x, "y": y})
                    max_margin_violation = max(
                        max_margin_violation,
                        max(0.0, x - (dim[0] - 0.001), -x),
                        max(0.0, y - (dim[1] - 0.001), -y),
                    )

            public_src = inspect.getsource(type(mod).add_individuals)
            private_src = inspect.getsource(type(spp)._add_individuals)
            model_module = inspect.getmodule(type(mod))

            undefined_species_reference = (
                "isinstance(source_spp, species)" in public_src
                and model_module is not None
                and "species" not in vars(model_module)
            )
            misspelled_isinstance_reference = "isinstnace(source_spp, str)" in public_src
            source_branch_requires_genarch = (
                "source_gen_arch.L" in private_src
                and "self.gen_arch.L" in private_src
            )
            source_branch_requires_tskit_union = (
                "_prep_tskit_tabcoll_for_gnx_spp_union" in private_src
                and "self._tc.union(" in private_src
            )

            exact_api_incompatibility = bool(
                probe_nongenomic
                and source_branch_requires_genarch
                and source_branch_requires_tskit_union
            )
            coordinate_ok = (
                len(canonical_coords) == expected_total
                and len(bad) == 0
            )

            passed = bool(
                seed_ok
                and unrun
                and coordinate_ok
                and exact_api_incompatibility
                and undefined_species_reference
                and misspelled_isinstance_reference
            )
            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "model_seed_match": seed_ok,
                "model_unrun": unrun,
                "native_landscape_dim_xy": dim,
                "construction_probe_genomic_architecture": None,
                "construction_probe_is_nongenomic": probe_nongenomic,
                "canonical_branch_count": len(branches),
                "canonical_carrier_count": len(canonical_coords),
                "canonical_coordinate_digest": _coords_digest(canonical_coords),
                "coordinate_native_bounds_pass": coordinate_ok,
                "coordinate_out_of_bounds_count": len(bad),
                "first_10_out_of_bounds": bad[:10],
                "max_margin_violation": max_margin_violation,
                "public_wrapper_undefined_species_reference_present":
                    undefined_species_reference,
                "public_wrapper_isinstnace_typo_present":
                    misspelled_isinstance_reference,
                "source_species_branch_requires_genomic_architecture":
                    source_branch_requires_genarch,
                "source_species_branch_requires_tskit_union":
                    source_branch_requires_tskit_union,
                "public_api_exact_state_injection_compatible": False,
                "public_api_incompatibility_reason":
                    "GEONOMICS_1_4_9_SOURCE_SPP_ADD_PATH_REQUIRES_GENOMIC_ARCHITECTURE_AND_TSKIT_WHILE_R436_PROBE_IS_NONGENOMIC",
                "public_model_add_individuals_called": False,
                "private_geonomics_mutation_api_called_by_arcana": False,
                "test_only_burn_guard_override_used": False,
                "installed_geonomics_file_modified": False,
                "model_run_performed": False,
                "scientific_exact_state_installed": False,
                "mechanical_dry_run_is_scientific_evidence": False,
                "pass": passed,
            })
            del mod
        except Exception as exc:
            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "pass": False,
                "error": repr(exc),
            })

    pass_count = sum(bool(r.get("pass")) for r in records)
    return {
        "status":
            "R437_PUBLIC_API_INCOMPATIBILITY_AND_COORDINATE_REPRESENTABILITY_VALIDATED"
            if len(records) == 4 and pass_count == 4
            else BLOCKED,
        "job_id": job_id,
        "replicate_count": len(records),
        "replicate_pass_count": pass_count,
        "canonical_branch_count": manifest.get("branch_count"),
        "canonical_carrier_count": manifest.get("total_carrier_count"),
        "all_coordinates_native_representable": (
            len(records) == 4
            and all(r.get("coordinate_native_bounds_pass") is True for r in records)
        ),
        "public_api_exact_state_injection_compatible": False,
        "public_api_incompatibility_frozen": (
            len(records) == 4
            and all(
                r.get("public_api_exact_state_injection_compatible") is False
                and r.get("source_species_branch_requires_genomic_architecture") is True
                and r.get("construction_probe_is_nongenomic") is True
                for r in records
            )
        ),
        "construction_probe_removed": False,
        "scientific_exact_state_installed": False,
        "public_api_final_initialization_authorized": False,
        "test_only_burn_guard_override_used": False,
        "mechanical_dry_run_is_scientific_evidence": False,
        "private_geonomics_mutation_api_called_by_arcana": False,
        "public_model_add_individuals_called_count": 0,
        "model_run_performed_count": 0,
        "records": records,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    pa = load(root / R436_AUDIT)
    ps = load(root / R436_SEAL)
    pc = load(root / R436_CHAIN)
    native = load(root / R436_NATIVE)
    parent_payload = load(root / R436_PAYLOAD)

    h14 = _verify_manifest_hash(
        root, parent_payload, "j14_injection_manifest", "j14_injection_manifest_sha256"
    )
    h18 = _verify_manifest_hash(
        root, parent_payload, "j18_injection_manifest", "j18_injection_manifest_sha256"
    )
    h21 = _verify_manifest_hash(
        root, parent_payload, "j21_payload_manifest", "j21_payload_manifest_sha256"
    )

    j14_manifest = load(root / J14_INJECTION) if h14["hash_match"] else {}
    j18_manifest = load(root / J18_INJECTION) if h18["hash_match"] else {}
    j21_manifest = load(root / J21_PAYLOAD) if h21["hash_match"] else {}

    j21 = _j21_native_layer_binding(root, native, j21_manifest)
    write(root / OUT / "R4_37_J21_CANONICAL_NATIVE_LAYER_BINDING_AUDIT.json", j21)

    j14 = _exact_state_public_api_dry_run(root, native, J14, j14_manifest)
    write(root / OUT / "R4_37_J14_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json", j14)

    j18 = _exact_state_public_api_dry_run(root, native, J18, j18_manifest)
    write(root / OUT / "R4_37_J18_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json", j18)

    checks = {
        "parent_r436_complete_33_33":
            pa.get("status") == PARENT_COMPLETE
            and pa.get("checks_passed") == 33
            and pa.get("checks_failed") == 0,
        "parent_r436_sealed_25_25":
            ps.get("status") == PARENT_SEALED
            and ps.get("verdict") == "SEALED"
            and ps.get("checks_passed") == 25
            and ps.get("checks_failed") == 0,
        "parent_repair_chain_closed":
            pc.get("status") == PARENT_CHAIN_CLOSED
            and pc.get("verdict") == "CLOSED"
            and pc.get("checks_passed") == 20,
        "parent_next_action_r437":
            pa.get("next_action") == PARENT_NEXT
            and ps.get("next_action") == PARENT_NEXT
            and pc.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R437_BIND_AND_MECHANICALLY_VALIDATE_WITHOUT_SCIENTIFIC_EXECUTION",
        "parent_native_12":
            native.get("native_parameter_materialized_count") == 12
            and native.get("model_construction_pass_count") == 12,
        "parent_manifest_hash_j14": h14["hash_match"],
        "parent_manifest_hash_j18": h18["hash_match"],
        "parent_manifest_hash_j21": h21["hash_match"],
        "j21_151_payload_manifest":
            j21_manifest.get("total_canonical_layer_payload_count") == 151,
        "j21_all_payload_hashes_match":
            j21.get("range_audit", {}).get("all_hashes_match") is True,
        "j21_exact_representability_partition_149_plus_2":
            j21.get("range_audit", {}).get(
                "exact_authorized_representability_partition"
            ) is True
            and j21.get("range_audit", {}).get("native_identity_layer_count") == 149
            and j21.get("range_audit", {}).get(
                "canonical_physical_unit_sidecar_count"
            ) == 2,
        "j21_four_native_bindings_pass":
            j21.get("replicate_count") == 4
            and j21.get("replicate_pass_count") == 4,
        "j21_596_exact_native_layer_bindings":
            j21.get("canonical_layer_binding_count") == 596,
        "j21_two_physical_unit_sidecars_preserved":
            j21.get("physical_sidecar_binding_count") == 2
            and j21.get("result_selected_transform_performed") is False,
        "j21_no_rescaling":
            j21.get("automatic_rescaling_performed") is False,
        "j21_no_cross_layer_fusion":
            j21.get("cross_layer_numeric_fusion_performed") is False,
        "j21_no_result_selected_transform":
            j21.get("result_selected_transform_performed") is False
            and j21.get("range_audit", {}).get(
                "result_selected_transform_performed"
            ) is False,
        "j14_four_coordinate_and_api_incompatibility_validations_pass":
            j14.get("replicate_count") == 4
            and j14.get("replicate_pass_count") == 4
            and j14.get("all_coordinates_native_representable") is True,
        "j18_four_coordinate_and_api_incompatibility_validations_pass":
            j18.get("replicate_count") == 4
            and j18.get("replicate_pass_count") == 4
            and j18.get("all_coordinates_native_representable") is True,
        "j14_exact_192_branches":
            j14.get("canonical_branch_count") == 192,
        "j18_exact_64_branches":
            j18.get("canonical_branch_count") == 64,
        "j14_exact_854_carriers":
            j14.get("canonical_carrier_count") == 854,
        "j18_exact_319_carriers":
            j18.get("canonical_carrier_count") == 319,
        "no_arcana_private_mutation_api":
            j14.get("private_geonomics_mutation_api_called_by_arcana") is False
            and j18.get("private_geonomics_mutation_api_called_by_arcana") is False,
        "public_api_incompatibility_frozen_without_shim":
            j14.get("public_api_incompatibility_frozen") is True
            and j18.get("public_api_incompatibility_frozen") is True
            and j14.get("public_model_add_individuals_called_count") == 0
            and j18.get("public_model_add_individuals_called_count") == 0,
        "dry_run_not_scientific_evidence":
            j14.get("mechanical_dry_run_is_scientific_evidence") is False
            and j18.get("mechanical_dry_run_is_scientific_evidence") is False,
        "construction_probe_not_removed":
            j14.get("construction_probe_removed") is False
            and j18.get("construction_probe_removed") is False,
        "scientific_exact_state_not_claimed":
            j14.get("scientific_exact_state_installed") is False
            and j18.get("scientific_exact_state_installed") is False,
        "final_initialization_not_yet_authorized":
            j14.get("public_api_final_initialization_authorized") is False
            and j18.get("public_api_final_initialization_authorized") is False,
        "no_test_only_burn_guard_override":
            j14.get("test_only_burn_guard_override_used") is False
            and j18.get("test_only_burn_guard_override_used") is False,
        "no_model_run":
            j14.get("model_run_performed_count") == 0
            and j18.get("model_run_performed_count") == 0
            and j21.get("model_run_performed_count") == 0,
        "no_scientific_execution":
            cfg.get("scientific_engine_execution_performed") is False,
        "no_target_numeric_execution":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False,
        "deep_off":
            cfg.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            pa.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            pa.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            pa.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    plan = {
        "stage": STAGE,
        "status":
            "R437_CANONICAL_LAYER_BINDING_AND_MECHANICAL_INJECTION_EVIDENCE_FROZEN"
            if ok else BLOCKED,
        "j21_canonical_native_layer_binding_validated": bool(ok),
        "j14_j18_public_api_mechanical_coordinate_injection_validated": bool(ok),
        "scientific_exact_initial_state_installed": False,
        "construction_probe_eliminated": False,
        "test_only_burn_guard_override_is_future_execution_path": False,
        "geonomics_execution_ready": False,
        "next_action":
            NEXT if ok else "REPAIR_R437_CANONICAL_LAYER_BINDING_OR_DRY_RUN",
    }
    write(root / OUT / "R4_37_R438_EXECUTION_PLAN.json", plan)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "geonomics_version": j21.get("geonomics_version"),
        "j21_native_binding_replicate_pass_count": j21.get("replicate_pass_count"),
        "j21_canonical_layer_binding_count": j21.get("canonical_layer_binding_count"),
        "j14_dry_run_replicate_pass_count": j14.get("replicate_pass_count"),
        "j18_dry_run_replicate_pass_count": j18.get("replicate_pass_count"),
        "j14_branch_count": j14.get("canonical_branch_count"),
        "j18_branch_count": j18.get("canonical_branch_count"),
        "j14_carrier_count": j14.get("canonical_carrier_count"),
        "j18_carrier_count": j18.get("canonical_carrier_count"),
        "j14_public_api_exact_state_injection_compatible":
            j14.get("public_api_exact_state_injection_compatible"),
        "j18_public_api_exact_state_injection_compatible":
            j18.get("public_api_exact_state_injection_compatible"),
        "j14_all_coordinates_native_representable":
            j14.get("all_coordinates_native_representable"),
        "j18_all_coordinates_native_representable":
            j18.get("all_coordinates_native_representable"),
        "scientific_exact_initial_state_installed": False,
        "construction_probe_eliminated": False,
        "private_geonomics_mutation_api_called_by_arcana": False,
        "test_only_burn_guard_override_is_scientific_evidence": False,
        "model_run_performed_count": 0,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "geonomics_execution_ready": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_37_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    ps = load(root / R436_SEAL)
    pc = load(root / R436_CHAIN)
    a = load(root / OUT / "R4_37_INTEGRATED_AUDIT.json")
    j21 = load(root / OUT / "R4_37_J21_CANONICAL_NATIVE_LAYER_BINDING_AUDIT.json")
    j14 = load(root / OUT / "R4_37_J14_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json")
    j18 = load(root / OUT / "R4_37_J18_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json")
    plan = load(root / OUT / "R4_37_R438_EXECUTION_PLAN.json")

    checks = {
        "parent_r436_sealed":
            ps.get("status") == PARENT_SEALED and ps.get("verdict") == "SEALED",
        "parent_r436_chain_closed":
            pc.get("status") == PARENT_CHAIN_CLOSED and pc.get("verdict") == "CLOSED",
        "r437_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "j21_four_bindings_pass":
            j21.get("replicate_pass_count") == 4,
        "j21_596_exact_identity_bindings":
            j21.get("canonical_layer_binding_count") == 596,
        "j21_149_native_plus_2_sidecar_partition":
            j21.get("native_identity_payload_count") == 149
            and j21.get("canonical_physical_unit_sidecar_count") == 2
            and j21.get("physical_sidecar_binding_count") == 2,
        "j21_no_rescale_or_fusion":
            j21.get("automatic_rescaling_performed") is False
            and j21.get("cross_layer_numeric_fusion_performed") is False,
        "j14_four_coordinate_api_validations_pass":
            j14.get("replicate_pass_count") == 4
            and j14.get("all_coordinates_native_representable") is True
            and j14.get("public_api_incompatibility_frozen") is True,
        "j18_four_coordinate_api_validations_pass":
            j18.get("replicate_pass_count") == 4
            and j18.get("all_coordinates_native_representable") is True
            and j18.get("public_api_incompatibility_frozen") is True,
        "j14_192_854":
            j14.get("canonical_branch_count") == 192
            and j14.get("canonical_carrier_count") == 854,
        "j18_64_319":
            j18.get("canonical_branch_count") == 64
            and j18.get("canonical_carrier_count") == 319,
        "public_api_mechanics_only":
            j14.get("mechanical_dry_run_is_scientific_evidence") is False
            and j18.get("mechanical_dry_run_is_scientific_evidence") is False,
        "no_private_arcana_mutation_api":
            j14.get("private_geonomics_mutation_api_called_by_arcana") is False
            and j18.get("private_geonomics_mutation_api_called_by_arcana") is False,
        "probe_not_eliminated":
            a.get("construction_probe_eliminated") is False,
        "scientific_exact_state_not_installed":
            a.get("scientific_exact_initial_state_installed") is False,
        "no_public_api_injection_or_burn_override":
            j14.get("public_model_add_individuals_called_count") == 0
            and j18.get("public_model_add_individuals_called_count") == 0
            and j14.get("test_only_burn_guard_override_used") is False
            and j18.get("test_only_burn_guard_override_used") is False,
        "no_model_run":
            a.get("model_run_performed_count") == 0,
        "no_scientific_execution":
            a.get("scientific_engine_execution_performed") is False,
        "no_target_numeric":
            a.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            a.get("readjudication_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "execution_not_ready":
            a.get("geonomics_execution_ready") is False,
        "r438_plan_frozen":
            plan.get("status")
            == "R437_CANONICAL_LAYER_BINDING_AND_MECHANICAL_INJECTION_EVIDENCE_FROZEN",
        "r438_exact_init_required":
            plan.get("scientific_exact_initial_state_installed") is False
            and plan.get("construction_probe_eliminated") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_action_r438":
            a.get("next_action") == NEXT and plan.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit": (
            "FINAL_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_"
            "INJECTION_DRY_RUN_VALIDATION"
        ),
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "j21_native_binding_replicates": j21.get("replicate_pass_count"),
            "j21_exact_identity_layer_bindings": j21.get("canonical_layer_binding_count"),
            "j21_native_identity_payload_count": j21.get("native_identity_payload_count"),
            "j21_canonical_physical_unit_sidecar_count":
                j21.get("canonical_physical_unit_sidecar_count"),
            "j14_coordinate_api_validation_replicates": j14.get("replicate_pass_count"),
            "j18_coordinate_api_validation_replicates": j18.get("replicate_pass_count"),
            "j14_public_api_exact_state_injection_compatible":
                j14.get("public_api_exact_state_injection_compatible"),
            "j18_public_api_exact_state_injection_compatible":
                j18.get("public_api_exact_state_injection_compatible"),
            "j14_branch_count": j14.get("canonical_branch_count"),
            "j18_branch_count": j18.get("canonical_branch_count"),
            "j14_carrier_count": j14.get("canonical_carrier_count"),
            "j18_carrier_count": j18.get("canonical_carrier_count"),
            "scientific_exact_initial_state_installed": False,
            "construction_probe_eliminated": False,
            "geonomics_execution_ready": False,
            "scientific_engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
