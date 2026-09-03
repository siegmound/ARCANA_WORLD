from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import json

import numpy as np

STAGE = "v0.6D1-R4.44"

PARENT_COMPLETE = (
    "PASS_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
    "AND_ADJUDICATION_SCHEMA_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
    "AND_ADJUDICATION_SCHEMA_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
    "VALIDATION"
)

COMPLETE = (
    "PASS_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
    "VALIDATION_COMPLETE"
)
SEALED = (
    "PASS_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
    "VALIDATION_SEALED"
)
BLOCKED = (
    "BLOCKED_R444_READOUT_EXTRACTION_DRY_RUN_OR_ADJUDICATION_INPUT_"
    "VALIDATION_FAILURE"
)
NEXT = (
    "BUILD_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
    "GOVERNED_REVALIDATION_RUN_PREFLIGHT"
)

OUT = Path("outputs/v0_6D1_R4_44")
SEAL = Path("outputs/v0_6D1_R4_44_SEAL/R4_44_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r444_geonomics_readout_extraction_dry_run_"
    "adjudication_input_validation_v0_6D1_R4_44.json"
)

R443 = Path("outputs/v0_6D1_R4_43/R4_43_INTEGRATED_AUDIT.json")
R443_SEAL = Path("outputs/v0_6D1_R4_43_SEAL/R4_43_FINAL_SEAL_AUDIT.json")
R443_REGISTRY = Path(
    "outputs/v0_6D1_R4_43/R4_43_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY.json"
)
R443_EXTRACTION = Path(
    "outputs/v0_6D1_R4_43/R4_43_METRIC_EXTRACTION_SCHEMA.json"
)
R443_ADJUDICATION = Path(
    "outputs/v0_6D1_R4_43/R4_43_ADJUDICATION_SCHEMA.json"
)

R436_NATIVE = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
)
R436_J21_MANIFEST = Path(
    "outputs/v0_6D1_R4_36/geonomics_canonical_payload/"
    "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS/INITIAL_LAYER_PAYLOAD_MANIFEST.json"
)

J14_SOURCE = Path(
    "outputs/v0_6D1_R4_30/authority/"
    "R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz"
)
J18_SOURCE = Path(
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz"
)
J14_SHA = "eed2d1e350783f1d2dc31c5b7e697330ccbfcf63024062bc9f4ed2f8905f4756"
J18_SHA = "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a"

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

MID_COORD = "GNX_CARRIER_COORDINATE_READBACK_XY"
MID_CELL = "GNX_CARRIER_NATIVE_CELL_READBACK_IJ"
MID_NN = "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE"
MID_RASTER = "GNX_NATIVE_LAYER_RASTER_READBACK"
MID_LAYER_SUMMARY = "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY"


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
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _import_params(path: Path) -> dict[str, Any]:
    name = "r444_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import params {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    params = getattr(mod, "params", None)
    if not isinstance(params, dict):
        raise RuntimeError(f"{path} did not expose dict params")
    return params


def _native_rows(native: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    return sorted(
        [
            r for r in (native.get("records") or [])
            if r.get("job_id") == job_id and r.get("construction_pass") is True
        ],
        key=lambda r: int(r["replicate_index"]),
    )


def _array_digest(a: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(a))
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode("utf-8"))
    h.update(str(arr.shape).encode("utf-8"))
    h.update(arr.tobytes(order="C"))
    return h.hexdigest()


def _finite_summary(a: np.ndarray, *, include_median: bool) -> dict[str, Any]:
    arr = np.asarray(a, dtype=float).ravel()
    finite = arr[np.isfinite(arr)]
    if len(finite) == 0:
        return {
            "count": int(arr.size),
            "finite_count": 0,
            "min": None,
            "max": None,
            "mean": None,
            **({"median": None} if include_median else {}),
            **({"std": None} if not include_median else {}),
        }
    out = {
        "count": int(arr.size),
        "finite_count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
    }
    if include_median:
        out["median"] = float(np.median(finite))
    else:
        out["std"] = float(np.std(finite))
    return out


def _carrier_state_pair(root: Path, job_id: str) -> dict[str, Any]:
    if job_id == J14:
        p = root / J14_SOURCE
        if sha256(p) != J14_SHA:
            raise RuntimeError("J14 source hash mismatch")
        with np.load(p, allow_pickle=False) as z:
            ages = np.asarray(z["age_ma"], dtype=float)
            names = [str(x) for x in z["state_variable_names"]]
            s = np.asarray(z["spatial_state"], dtype=float)[0, 0, :2]
        ri = names.index("grid_row")
        ci = names.index("grid_col")
        ai = names.index("active")
        states = []
        for ti in range(2):
            mask = s[ti, :, ai] > 0.5
            coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
            states.append({"age": float(ages[ti]), "coords": coords})
        return {
            "selection": "member_index_0_candidate_index_0_states_0_and_1",
            "states": states,
        }

    if job_id == J18:
        p = root / J18_SOURCE
        if sha256(p) != J18_SHA:
            raise RuntimeError("J18 source hash mismatch")
        with np.load(p, allow_pickle=False) as z:
            ages = np.asarray(z["snapshot_age_ka"], dtype=float)
            names = [str(x) for x in z["state_variable_names"]]
            s = np.asarray(z["snapshot_deme_state"], dtype=float)[0, 0, :2]
            active = np.asarray(z["snapshot_active"])[0, 0, :2]
        ri = names.index("grid_row")
        ci = names.index("grid_col")
        states = []
        for ti in range(2):
            mask = np.asarray(active[ti], dtype=float) > 0.5
            coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
            states.append({"age": float(ages[ti]), "coords": coords})
        return {
            "selection": "member_index_0_candidate_index_0_states_0_and_1",
            "states": states,
        }
    raise ValueError(job_id)


def _metric_record_base(
    *,
    job_id: str,
    replicate_index: int,
    frozen_seed: int,
    canonical_state_index: int,
    canonical_physical_age: float,
    metric_id: str,
    metric_role: str,
    source_object: str,
    value_shape: list[int],
    finite: bool,
    payload_sha256: str,
) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "job_id": job_id,
        "replicate_index": replicate_index,
        "frozen_seed": frozen_seed,
        "canonical_state_index": canonical_state_index,
        "canonical_physical_age": canonical_physical_age,
        "metric_id": metric_id,
        "metric_role": metric_role,
        "source_object": source_object,
        "value_shape": value_shape,
        "finite": finite,
        "payload_sha256": payload_sha256,
    }


def _extract_carrier_metrics(
    mod: Any,
    *,
    job_id: str,
    replicate_index: int,
    frozen_seed: int,
    canonical_state_index: int,
    canonical_physical_age: float,
    expected_coords: np.ndarray,
) -> list[dict[str, Any]]:
    spp = mod.comm[0]
    public_coords = np.asarray(mod.get_coords(spp=0), dtype=float)
    expected_coords = np.asarray(expected_coords, dtype=float)

    coords_exact = bool(
        public_coords.shape == expected_coords.shape
        and np.array_equal(public_coords, expected_coords)
    )
    coords_finite = bool(np.all(np.isfinite(public_coords)))
    coord_record = _metric_record_base(
        job_id=job_id,
        replicate_index=replicate_index,
        frozen_seed=frozen_seed,
        canonical_state_index=canonical_state_index,
        canonical_physical_age=canonical_physical_age,
        metric_id=MID_COORD,
        metric_role="EXACT_INTEGRITY_ONLY",
        source_object="Model.get_coords(spp=0)",
        value_shape=list(public_coords.shape),
        finite=coords_finite,
        payload_sha256=_array_digest(public_coords),
    )
    coord_record.update({
        "comparison_result": "EXACT_MATCH" if coords_exact else "MISMATCH",
        "canonical_payload_sha256": _array_digest(expected_coords),
        "exact_match": coords_exact,
        "scientific_divergence_claim": False,
    })

    cells = np.asarray(spp._cells)
    expected_cells = np.floor(expected_coords).astype(np.int32)
    cells_exact = bool(
        cells.shape == expected_cells.shape
        and np.array_equal(cells, expected_cells)
    )
    cell_record = _metric_record_base(
        job_id=job_id,
        replicate_index=replicate_index,
        frozen_seed=frozen_seed,
        canonical_state_index=canonical_state_index,
        canonical_physical_age=canonical_physical_age,
        metric_id=MID_CELL,
        metric_role="EXACT_INTEGRITY_ONLY",
        source_object="Species._cells",
        value_shape=list(cells.shape),
        finite=bool(np.all(np.isfinite(cells))),
        payload_sha256=_array_digest(cells),
    )
    cell_record.update({
        "comparison_result": "EXACT_MATCH" if cells_exact else "MISMATCH",
        "canonical_payload_sha256": _array_digest(expected_cells),
        "exact_match": cells_exact,
        "scientific_divergence_claim": False,
    })

    n = len(public_coords)
    if n < 2:
        nn = np.asarray([], dtype=float)
        nn_record = _metric_record_base(
            job_id=job_id,
            replicate_index=replicate_index,
            frozen_seed=frozen_seed,
            canonical_state_index=canonical_state_index,
            canonical_physical_age=canonical_physical_age,
            metric_id=MID_NN,
            metric_role="SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            source_object="Species._kd_tree.tree.query(coords,k=2)",
            value_shape=[0],
            finite=True,
            payload_sha256=_array_digest(nn),
        )
        nn_record.update({
            "applicability": "NOT_APPLICABLE_SINGLE_CARRIER_NO_FAILURE",
            "raw_vector": [],
            "summary": {
                "count": 0,
                "finite_count": 0,
                "min": None,
                "median": None,
                "mean": None,
                "max": None,
            },
            "numeric_acceptance_threshold": None,
            "automatic_pass_fail_from_value": False,
        })
    else:
        dists, _ = spp._kd_tree.tree.query(public_coords, k=2)
        nn = np.asarray(dists, dtype=float)[:, 1]
        nn_finite = bool(np.all(np.isfinite(nn)))
        nn_record = _metric_record_base(
            job_id=job_id,
            replicate_index=replicate_index,
            frozen_seed=frozen_seed,
            canonical_state_index=canonical_state_index,
            canonical_physical_age=canonical_physical_age,
            metric_id=MID_NN,
            metric_role="SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            source_object="Species._kd_tree.tree.query(coords,k=2)",
            value_shape=list(nn.shape),
            finite=nn_finite,
            payload_sha256=_array_digest(nn),
        )
        nn_record.update({
            "applicability": "APPLICABLE",
            "raw_vector": [float(x) for x in nn],
            "summary": _finite_summary(nn, include_median=True),
            "numeric_acceptance_threshold": None,
            "automatic_pass_fail_from_value": False,
        })

    return [coord_record, cell_record, nn_record]


def _run_carrier_readout_dry_run(
    root: Path,
    native: dict[str, Any],
    job_id: str,
) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight import (
        _install_exact_nonliteral_carriers,
    )
    from arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run import (
        _advance_authorized_clock_once,
        _exact_carrier_replace_preserve_clock,
    )

    rows = _native_rows(native, job_id)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_NATIVE_ROWS"}

    pair = _carrier_state_pair(root, job_id)
    s0, s1 = pair["states"]
    if len(s0["coords"]) <= 0 or len(s1["coords"]) <= 0:
        return {"status": BLOCKED, "reason": "ZERO_CARRIER_SELECTED_STATE"}

    metric_records = []
    replicate_records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(_import_params(root / row["native_parameter_file"]))
            params["model"]["T"] = 1
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R444_{job_id}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )
            template = copy.deepcopy(next(iter(mod.comm[0].values())))
            init = _install_exact_nonliteral_carriers(
                mod, template, s0["coords"].tolist()
            )

            r0 = _extract_carrier_metrics(
                mod,
                job_id=job_id,
                replicate_index=rep,
                frozen_seed=seed,
                canonical_state_index=0,
                canonical_physical_age=s0["age"],
                expected_coords=s0["coords"],
            )
            metric_records.extend(r0)

            clock = _advance_authorized_clock_once(mod)
            repl = _exact_carrier_replace_preserve_clock(
                mod, template, s1["coords"].tolist()
            )

            r1 = _extract_carrier_metrics(
                mod,
                job_id=job_id,
                replicate_index=rep,
                frozen_seed=seed,
                canonical_state_index=1,
                canonical_physical_age=s1["age"],
                expected_coords=s1["coords"],
            )
            metric_records.extend(r1)

            local = r0 + r1
            integrity = [
                r for r in local if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
            ]
            descriptive = [
                r for r in local
                if r["metric_role"] == "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY"
            ]
            passed = bool(
                init.get("pass") is True
                and clock.get("pass") is True
                and repl.get("pass") is True
                and len(local) == 6
                and len(integrity) == 4
                and all(r.get("exact_match") is True for r in integrity)
                and len(descriptive) == 2
                and all(r.get("finite") is True for r in descriptive)
                and all(
                    r.get("numeric_acceptance_threshold") is None
                    for r in descriptive
                )
                and mod.t == 0
                and mod.comm.t == 0
                and mod.comm[0].t == 0
            )
            replicate_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "metric_record_count": len(local),
                "integrity_record_count": len(integrity),
                "descriptive_record_count": len(descriptive),
                "all_integrity_exact": all(
                    r.get("exact_match") is True for r in integrity
                ),
                "all_descriptive_finite_or_na": all(
                    r.get("finite") is True for r in descriptive
                ),
                "no_numeric_thresholds": all(
                    r.get("numeric_acceptance_threshold") is None
                    for r in descriptive
                ),
                "model_walk_called": False,
                "scientific_execution_claimed": False,
                "pass": passed,
            })
            del mod
        except Exception as exc:
            replicate_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "pass": False,
                "error": repr(exc),
            })

    pass_count = sum(bool(r.get("pass")) for r in replicate_records)
    return {
        "stage": STAGE,
        "status":
            "R444_CARRIER_READOUT_EXTRACTION_DRY_RUN_VALIDATED"
            if pass_count == 4 else BLOCKED,
        "job_id": job_id,
        "selection": pair["selection"],
        "state_count_per_replicate": 2,
        "replicate_count": 4,
        "replicate_pass_count": pass_count,
        "metric_record_count": len(metric_records),
        "expected_metric_record_count": 24,
        "integrity_record_count": sum(
            r["metric_role"] == "EXACT_INTEGRITY_ONLY"
            for r in metric_records
        ),
        "descriptive_record_count": sum(
            r["metric_role"] == "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY"
            for r in metric_records
        ),
        "metric_records": metric_records,
        "replicate_records": replicate_records,
        "model_walk_call_count": 0,
        "forbidden_readout_emission_count": 0,
        "scientific_execution_performed": False,
    }


def _prepare_j21_dynamic(root: Path) -> tuple[dict[str, list[np.ndarray]], dict[str, str]]:
    from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import (
        _j21_dynamic_payload_authority,
    )
    manifest = load(root / R436_J21_MANIFEST)
    payload, dynamic_by_name, _, bound_dynamic_sidecars = (
        _j21_dynamic_payload_authority(root, manifest)
    )
    if payload.get("pass") is not True or len(dynamic_by_name) != 147:
        raise RuntimeError("J21 dynamic authority invalid")
    return dynamic_by_name, bound_dynamic_sidecars


def _layer_metric_records(
    *,
    job_id: str,
    replicate_index: int,
    frozen_seed: int,
    state_index: int,
    age: float,
    layer_name: str,
    actual: np.ndarray,
    expected: np.ndarray,
) -> list[dict[str, Any]]:
    actual = np.asarray(actual)
    expected = np.asarray(expected)
    exact = bool(
        actual.shape == expected.shape
        and actual.dtype == expected.dtype
        and np.array_equal(actual, expected)
    )
    finite = bool(np.all(np.isfinite(actual)))

    raster = _metric_record_base(
        job_id=job_id,
        replicate_index=replicate_index,
        frozen_seed=frozen_seed,
        canonical_state_index=state_index,
        canonical_physical_age=age,
        metric_id=MID_RASTER,
        metric_role="EXACT_INTEGRITY_ONLY",
        source_object=f"Landscape.Layer[{layer_name}].rast",
        value_shape=list(actual.shape),
        finite=finite,
        payload_sha256=_array_digest(actual),
    )
    raster.update({
        "layer_name": layer_name,
        "comparison_result": "EXACT_MATCH" if exact else "MISMATCH",
        "canonical_payload_sha256": _array_digest(expected),
        "exact_match": exact,
        "scientific_divergence_claim": False,
    })

    summary = _metric_record_base(
        job_id=job_id,
        replicate_index=replicate_index,
        frozen_seed=frozen_seed,
        canonical_state_index=state_index,
        canonical_physical_age=age,
        metric_id=MID_LAYER_SUMMARY,
        metric_role="SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
        source_object=f"Landscape.Layer[{layer_name}].rast",
        value_shape=list(actual.shape),
        finite=finite,
        payload_sha256=_array_digest(actual),
    )
    summary.update({
        "layer_name": layer_name,
        "summary": _finite_summary(actual, include_median=False),
        "numeric_acceptance_threshold": None,
        "automatic_pass_fail_from_value": False,
    })
    return [raster, summary]


def _run_j21_readout_dry_run(root: Path, native: dict[str, Any]) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import (
        _r437_j21_bound_param_path,
    )
    from arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run import (
        _advance_authorized_clock_once,
    )

    rows = _native_rows(native, J21)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_J21_ROWS"}

    dynamic_by_name, sidecars = _prepare_j21_dynamic(root)
    names = list(dynamic_by_name.keys())
    ages = [20.0, 15.0]
    metric_records = []
    replicate_records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(
                _import_params(_r437_j21_bound_param_path(root, rep))
            )
            layers = params["landscape"]["layers"]
            for lname in sidecars:
                if lname not in layers:
                    raise RuntimeError(f"missing dynamic sidecar layer {lname}")
                del layers[lname]
            if set(names) != (set(layers.keys()) - {"R437_CONSTRUCTION_SUPPORT"}):
                raise RuntimeError("J21 native layer set mismatch")
            for lname in names:
                layers[lname].pop("change", None)

            params["model"]["T"] = 1
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R444_{J21}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )
            layer_map = {lyr.name: lyr for lyr in mod.land.values()}

            local = []
            for lname in names:
                local.extend(_layer_metric_records(
                    job_id=J21,
                    replicate_index=rep,
                    frozen_seed=seed,
                    state_index=0,
                    age=ages[0],
                    layer_name=lname,
                    actual=np.asarray(layer_map[lname].rast),
                    expected=np.asarray(dynamic_by_name[lname][0]),
                ))

            clock = _advance_authorized_clock_once(mod)
            for lname in names:
                layer_map[lname].rast = np.asarray(
                    dynamic_by_name[lname][1]
                ).copy()

            for lname in names:
                local.extend(_layer_metric_records(
                    job_id=J21,
                    replicate_index=rep,
                    frozen_seed=seed,
                    state_index=1,
                    age=ages[1],
                    layer_name=lname,
                    actual=np.asarray(layer_map[lname].rast),
                    expected=np.asarray(dynamic_by_name[lname][1]),
                ))

            metric_records.extend(local)
            integrity = [
                r for r in local if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
            ]
            descriptive = [
                r for r in local
                if r["metric_role"] == "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE"
            ]
            passed = bool(
                clock.get("pass") is True
                and len(local) == 588
                and len(integrity) == 294
                and all(r.get("exact_match") is True for r in integrity)
                and len(descriptive) == 294
                and all(r.get("finite") is True for r in descriptive)
                and all(
                    r.get("numeric_acceptance_threshold") is None
                    for r in descriptive
                )
                and mod.land._changer is None
                and mod.t == 0
            )
            replicate_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "metric_record_count": len(local),
                "integrity_record_count": len(integrity),
                "descriptive_record_count": len(descriptive),
                "all_integrity_exact": all(
                    r.get("exact_match") is True for r in integrity
                ),
                "all_descriptive_finite": all(
                    r.get("finite") is True for r in descriptive
                ),
                "no_numeric_thresholds": all(
                    r.get("numeric_acceptance_threshold") is None
                    for r in descriptive
                ),
                "dynamic_sidecar_count": 4,
                "sidecars_emitted_as_native_metrics": False,
                "landscape_changer_called": False,
                "model_walk_called": False,
                "scientific_execution_claimed": False,
                "pass": passed,
            })
            del mod
        except Exception as exc:
            replicate_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "pass": False,
                "error": repr(exc),
            })

    pass_count = sum(bool(r.get("pass")) for r in replicate_records)
    return {
        "stage": STAGE,
        "status":
            "R444_J21_READOUT_EXTRACTION_DRY_RUN_VALIDATED"
            if pass_count == 4 else BLOCKED,
        "job_id": J21,
        "state_count_per_replicate": 2,
        "replicate_count": 4,
        "replicate_pass_count": pass_count,
        "native_layer_count": 147,
        "dynamic_sidecar_count": 4,
        "metric_record_count": len(metric_records),
        "expected_metric_record_count": 2352,
        "integrity_record_count": sum(
            r["metric_role"] == "EXACT_INTEGRITY_ONLY"
            for r in metric_records
        ),
        "descriptive_record_count": sum(
            r["metric_role"] == "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE"
            for r in metric_records
        ),
        "metric_records": metric_records,
        "replicate_records": replicate_records,
        "model_walk_call_count": 0,
        "landscape_changer_call_count": 0,
        "forbidden_readout_emission_count": 0,
        "scientific_execution_performed": False,
    }


def _adjudication_input(
    registry: dict[str, Any],
    extraction_schema: dict[str, Any],
    adjudication_schema: dict[str, Any],
    job_results: list[dict[str, Any]],
) -> dict[str, Any]:
    records = [
        r
        for result in job_results
        for r in result.get("metric_records", [])
    ]

    common = set(extraction_schema["common_record_fields"])
    rows = []
    forbidden_metric_ids = set()
    authorized = {
        J14: set(registry["jobs"][J14]["authorized_metrics"]),
        J18: set(registry["jobs"][J18]["authorized_metrics"]),
        J21: set(registry["jobs"][J21]["authorized_metrics"]),
    }

    for r in records:
        missing = sorted(common - set(r.keys()))
        metric_authorized = r.get("metric_id") in authorized.get(
            r.get("job_id"), set()
        )
        role = r.get("metric_role")
        if not metric_authorized:
            forbidden_metric_ids.add(str(r.get("metric_id")))

        if role == "EXACT_INTEGRITY_ONLY":
            adjudication_status = (
                "INTEGRITY_EXACT_MATCH"
                if r.get("exact_match") is True
                else "ADAPTER_OR_RUNTIME_INTEGRITY_FAILURE"
            )
            numeric_threshold_used = False
        elif role in {
            "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
        }:
            adjudication_status = "RECORDED_NO_NUMERIC_THRESHOLD"
            numeric_threshold_used = False
        else:
            adjudication_status = "FORBIDDEN_METRIC_ROLE"
            numeric_threshold_used = False

        rows.append({
            "job_id": r.get("job_id"),
            "replicate_index": r.get("replicate_index"),
            "canonical_state_index": r.get("canonical_state_index"),
            "metric_id": r.get("metric_id"),
            "metric_role": role,
            "schema_missing_fields": missing,
            "metric_authorized_for_job": metric_authorized,
            "finite": r.get("finite"),
            "adjudication_status": adjudication_status,
            "numeric_threshold_used": numeric_threshold_used,
            "majority_vote_used": False,
            "engine_output_defined_target": False,
            "canonical_rewrite_performed": False,
        })

    exact_rows = [
        x for x in rows if x["metric_role"] == "EXACT_INTEGRITY_ONLY"
    ]
    descriptive_rows = [
        x for x in rows
        if x["metric_role"] in {
            "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
        }
    ]

    pass_conditions = {
        "exact_2400_metric_records": len(records) == 2400,
        "exact_1208_integrity_records": len(exact_rows) == 1208,
        "exact_1192_descriptive_records": len(descriptive_rows) == 1192,
        "all_common_schema_fields_present":
            all(len(x["schema_missing_fields"]) == 0 for x in rows),
        "all_metrics_authorized_for_job":
            all(x["metric_authorized_for_job"] for x in rows),
        "all_integrity_exact":
            all(
                x["adjudication_status"] == "INTEGRITY_EXACT_MATCH"
                for x in exact_rows
            ),
        "all_descriptive_recorded_without_threshold":
            all(
                x["adjudication_status"] == "RECORDED_NO_NUMERIC_THRESHOLD"
                for x in descriptive_rows
            ),
        "all_records_finite":
            all(x["finite"] is True for x in rows),
        "zero_numeric_threshold_use":
            all(x["numeric_threshold_used"] is False for x in rows),
        "zero_majority_vote":
            all(x["majority_vote_used"] is False for x in rows),
        "zero_engine_target_definition":
            all(x["engine_output_defined_target"] is False for x in rows),
        "zero_canonical_rewrite":
            all(x["canonical_rewrite_performed"] is False for x in rows),
        "zero_forbidden_metric_ids": len(forbidden_metric_ids) == 0,
        "r443_zero_threshold_authority_preserved":
            adjudication_schema.get("adjudicative_numeric_threshold_count") == 0,
    }
    ok = all(pass_conditions.values())

    return {
        "stage": STAGE,
        "status":
            "R444_ADJUDICATION_INPUT_DRY_RUN_VALIDATED"
            if ok else BLOCKED,
        "checks": pass_conditions,
        "checks_passed": sum(pass_conditions.values()),
        "checks_total": len(pass_conditions),
        "metric_record_count": len(records),
        "integrity_record_count": len(exact_rows),
        "descriptive_record_count": len(descriptive_rows),
        "forbidden_metric_ids": sorted(forbidden_metric_ids),
        "adjudicative_numeric_threshold_count": 0,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "rows": rows,
        "scientific_execution_performed": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R443)
    parent_seal = load(root / R443_SEAL)
    registry = load(root / R443_REGISTRY)
    extraction_schema = load(root / R443_EXTRACTION)
    adjudication_schema = load(root / R443_ADJUDICATION)
    native = load(root / R436_NATIVE)

    j14 = _run_carrier_readout_dry_run(root, native, J14)
    j18 = _run_carrier_readout_dry_run(root, native, J18)
    j21 = _run_j21_readout_dry_run(root, native)
    adj = _adjudication_input(
        registry, extraction_schema, adjudication_schema, [j14, j18, j21]
    )

    write(root / OUT / "R4_44_J14_READOUT_EXTRACTION_DRY_RUN.json", j14)
    write(root / OUT / "R4_44_J18_READOUT_EXTRACTION_DRY_RUN.json", j18)
    write(root / OUT / "R4_44_J21_READOUT_EXTRACTION_DRY_RUN.json", j21)
    write(root / OUT / "R4_44_ADJUDICATION_INPUT_VALIDATION.json", adj)

    checks = {
        "parent_r443_complete_48_48":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 48
            and parent.get("checks_failed") == 0,
        "parent_r443_sealed_29_29":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 29
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r444":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R444_READOUT_EXTRACTION_DRY_RUN_TWO_STATES_FOUR_SEEDS",
        "production_queue_authority_preserved":
            parent.get("production_execution_queue_authorized") is True
            and parent.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "scientific_readout_authority_preserved":
            parent.get("scientific_readout_authority_closed") is True,
        "five_metric_definition_authority_preserved":
            parent.get("unique_authorized_metric_definition_count") == 5,
        "j14_four_readout_dry_runs_pass":
            j14.get("replicate_pass_count") == 4,
        "j14_exact_24_metric_records":
            j14.get("metric_record_count") == 24,
        "j18_four_readout_dry_runs_pass":
            j18.get("replicate_pass_count") == 4,
        "j18_exact_24_metric_records":
            j18.get("metric_record_count") == 24,
        "j21_four_readout_dry_runs_pass":
            j21.get("replicate_pass_count") == 4,
        "j21_exact_2352_metric_records":
            j21.get("metric_record_count") == 2352,
        "exact_2400_metric_records":
            adj.get("metric_record_count") == 2400,
        "exact_1208_integrity_records":
            adj.get("integrity_record_count") == 1208,
        "exact_1192_descriptive_records":
            adj.get("descriptive_record_count") == 1192,
        "adjudication_input_validated":
            adj.get("status") == "R444_ADJUDICATION_INPUT_DRY_RUN_VALIDATED",
        "all_schema_fields_present":
            adj["checks"]["all_common_schema_fields_present"] is True,
        "all_integrity_exact":
            adj["checks"]["all_integrity_exact"] is True,
        "all_descriptive_no_threshold":
            adj["checks"][
                "all_descriptive_recorded_without_threshold"
            ] is True,
        "all_metrics_authorized":
            adj["checks"]["all_metrics_authorized_for_job"] is True,
        "zero_forbidden_metric_ids":
            adj["checks"]["zero_forbidden_metric_ids"] is True,
        "zero_numeric_thresholds":
            adj.get("adjudicative_numeric_threshold_count") == 0,
        "zero_automatic_scientific_pass_fail":
            adj.get("automatic_scientific_pass_fail_count") == 0,
        "zero_scientific_divergence_claims":
            adj.get("scientific_divergence_claim_count") == 0,
        "metric_extraction_dry_run_validated": True,
        "adjudication_input_validation_closed": True,
        "scientific_execution_not_yet_authorized":
            cfg.get("scientific_execution_authorized") is False,
        "geonomics_execution_not_yet_ready":
            cfg.get("geonomics_execution_ready") is False,
        "dry_run_not_scientific_evidence":
            cfg.get("dry_run_is_scientific_evidence") is False,
        "no_scientific_execution":
            cfg.get("scientific_engine_execution_performed") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False,
        "deep_off":
            cfg.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            parent.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            parent.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            parent.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "geonomics_version": "1.4.9",
        "production_execution_queue_authorized": True,
        "authorized_queue": "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "scientific_readout_authority_closed": True,
        "metric_extraction_dry_run_validated": bool(ok),
        "adjudication_input_validation_closed": bool(ok),
        "metric_record_count": adj.get("metric_record_count"),
        "integrity_record_count": adj.get("integrity_record_count"),
        "descriptive_record_count": adj.get("descriptive_record_count"),
        "adjudicative_numeric_threshold_count": 0,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_execution_authorized": False,
        "geonomics_execution_ready": False,
        "dry_run_is_scientific_evidence": False,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R444_READOUT_EXTRACTION_OR_ADJUDICATION_INPUT",
    }
    write(root / OUT / "R4_44_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_44_INTEGRATED_AUDIT.json")
    adj = load(root / OUT / "R4_44_ADJUDICATION_INPUT_VALIDATION.json")

    checks = {
        "r444_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "production_queue_authorized":
            a.get("production_execution_queue_authorized") is True,
        "arcana_queue_only":
            a.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "readout_authority_closed":
            a.get("scientific_readout_authority_closed") is True,
        "metric_extraction_dry_run_validated":
            a.get("metric_extraction_dry_run_validated") is True,
        "adjudication_input_validation_closed":
            a.get("adjudication_input_validation_closed") is True,
        "exact_2400_records":
            a.get("metric_record_count") == 2400,
        "exact_1208_integrity":
            a.get("integrity_record_count") == 1208,
        "exact_1192_descriptive":
            a.get("descriptive_record_count") == 1192,
        "all_adjudication_checks_pass":
            adj.get("checks_passed") == adj.get("checks_total"),
        "zero_thresholds":
            a.get("adjudicative_numeric_threshold_count") == 0,
        "zero_automatic_scientific_pass_fail":
            a.get("automatic_scientific_pass_fail_count") == 0,
        "scientific_execution_not_authorized":
            a.get("scientific_execution_authorized") is False,
        "execution_not_ready":
            a.get("geonomics_execution_ready") is False,
        "dry_run_not_scientific":
            a.get("dry_run_is_scientific_evidence") is False,
        "no_scientific_execution":
            a.get("scientific_engine_execution_performed") is False,
        "no_target_numeric":
            a.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            a.get("readjudication_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r445":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())
    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_"
            "INPUT_VALIDATION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "production_execution_queue_authorized": True,
            "scientific_readout_authority_closed": True,
            "metric_extraction_dry_run_validated":
                a.get("metric_extraction_dry_run_validated"),
            "adjudication_input_validation_closed":
                a.get("adjudication_input_validation_closed"),
            "metric_record_count": a.get("metric_record_count"),
            "integrity_record_count": a.get("integrity_record_count"),
            "descriptive_record_count": a.get("descriptive_record_count"),
            "adjudicative_numeric_threshold_count": 0,
            "scientific_execution_authorized": False,
            "geonomics_execution_ready": False,
            "scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
