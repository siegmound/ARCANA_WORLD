from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import inspect
import json
from collections import Counter

import numpy as np

STAGE = "v0.6D1-R4.39"

PARENT_COMPLETE = (
    "PASS_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_"
    "CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_"
    "CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_"
    "AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT"
)

COMPLETE = (
    "PASS_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_"
    "AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_"
    "AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R439_RUNTIME_TIME_MAPPING_CARRIER_DYNAMICS_OR_DYNAMIC_LAYER_"
    "CHANGE_PREFLIGHT_FAILURE"
)
NEXT = (
    "BUILD_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
    "AND_EXECUTION_QUEUE_PREFLIGHT"
)

OUT = Path("outputs/v0_6D1_R4_39")
SEAL = Path("outputs/v0_6D1_R4_39_SEAL/R4_39_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r439_geonomics_runtime_time_mapping_nonliteral_carrier_"
    "dynamics_dynamic_layer_change_preflight_v0_6D1_R4_39.json"
)

R438_AUDIT = Path("outputs/v0_6D1_R4_38/R4_38_INTEGRATED_AUDIT.json")
R438_SEAL = Path("outputs/v0_6D1_R4_38_SEAL/R4_38_FINAL_SEAL_AUDIT.json")
R436_NATIVE = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
)
R436_J21_MANIFEST = Path(
    "outputs/v0_6D1_R4_36/geonomics_canonical_payload/"
    "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS/INITIAL_LAYER_PAYLOAD_MANIFEST.json"
)

R430_J14 = Path(
    "outputs/v0_6D1_R4_30/authority/"
    "R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz"
)
R328 = Path(
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz"
)
R333 = Path(
    "outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz"
)
R334 = Path(
    "outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"
)

EXPECTED_SOURCE_HASHES = {
    R430_J14.as_posix():
        "eed2d1e350783f1d2dc31c5b7e697330ccbfcf63024062bc9f4ed2f8905f4756",
    R328.as_posix():
        "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a",
    R333.as_posix():
        "5fd7b11df5051245551aa2d23ce334b0a540f171e85ac8a451c603eb63f685b9",
    R334.as_posix():
        "31f5954b846be3cb4a6bb14afb2ae19e7cccafd47c90719a1434e9058bc35d86",
}

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

R437_STATIC_SIDECAR_NAMES = {
    "temperature_anomaly_c",
    "sea_level_anomaly_m",
}

R439_DYNAMIC_SIDECAR_NAMES = {
    "temperature_anomaly_c",
    "precipitation_factor",
    "npp_factor",
    "sea_level_anomaly_m",
}

R333_SOURCE = Path(
    "src/arcana_worldsim/scientific_engines/"
    "r333_holocene_environment_domestication.py"
)
R333_SOURCE_SHA256 = (
    "c32d78efcffccf60dd0a70870dc6d9555a9eed823ec4fa5e7fb3c2e61705fc40"
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
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _import_params_module(path: Path) -> dict[str, Any]:
    name = "r439_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import parameter module {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    params = getattr(mod, "params", None)
    if not isinstance(params, dict):
        raise TypeError(f"{path} did not expose dict `params`")
    return params


def _source_hash_audit(root: Path) -> dict[str, Any]:
    rows = []
    for rel, expected in EXPECTED_SOURCE_HASHES.items():
        p = root / rel
        actual = sha256(p) if p.exists() else None
        rows.append({
            "path": rel,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "hash_match": actual == expected,
        })
    return {
        "record_count": len(rows),
        "all_hashes_match": all(r["hash_match"] for r in rows),
        "records": rows,
    }


def _time_mapping(
    axis: np.ndarray,
    *,
    job_id: str,
    physical_unit: str,
    years_multiplier: float,
) -> dict[str, Any]:
    axis = np.asarray(axis, dtype=float).reshape(-1)
    finite = bool(np.all(np.isfinite(axis)))
    strictly_descending = bool(
        finite and len(axis) >= 2 and np.all(np.diff(axis) < 0.0)
    )

    transitions = []
    for state_index in range(1, len(axis)):
        model_t = state_index - 1
        interval = float(axis[state_index - 1] - axis[state_index])
        transitions.append({
            "from_state_index": state_index - 1,
            "to_state_index": state_index,
            "geonomics_timestep": model_t,
            "from_physical_age": float(axis[state_index - 1]),
            "to_physical_age": float(axis[state_index]),
            "physical_age_unit": physical_unit,
            "interval_years": float(interval * years_multiplier),
        })

    timesteps = [r["geonomics_timestep"] for r in transitions]
    intervals = [r["interval_years"] for r in transitions]
    collision_free = len(timesteps) == len(set(timesteps))
    monotone_t = timesteps == list(range(len(transitions)))
    positive_intervals = bool(all(x > 0.0 for x in intervals))
    uniform_physical_intervals = bool(
        len(intervals) <= 1
        or np.allclose(intervals, intervals[0], rtol=0.0, atol=1e-6)
    )
    T = len(axis) - 1

    return {
        "job_id": job_id,
        "mapping_semantics":
            "CANONICAL_STATE_0_IS_UNRUN_MODEL_T_MINUS_1_EACH_FUTURE_CANONICAL_"
            "STATE_I_MAPS_TO_MAIN_TIMESTEP_I_MINUS_1",
        "canonical_state_count": len(axis),
        "transition_count": T,
        "geonomics_T": T,
        "initial_model_t": -1,
        "final_model_t_after_T_steps": T - 1,
        "physical_age_unit": physical_unit,
        "axis_values": [float(x) for x in axis],
        "finite": finite,
        "strictly_descending_physical_age": strictly_descending,
        "integer_timestep_collision_free": collision_free,
        "integer_timestep_monotone_zero_based": monotone_t,
        "all_physical_intervals_positive": positive_intervals,
        "uniform_physical_interval": uniform_physical_intervals,
        "single_fixed_years_per_timestep_claim":
            float(intervals[0]) if uniform_physical_intervals and intervals else None,
        "variable_duration_ordinal_transition_mapping":
            not uniform_physical_intervals,
        "physical_rate_mapping_authority_created": False,
        "interpolation_performed": False,
        "transitions": transitions,
        "pass": bool(
            finite
            and strictly_descending
            and collision_free
            and monotone_t
            and positive_intervals
            and T >= 1
        ),
    }


def _build_time_authority(root: Path) -> dict[str, Any]:
    with np.load(root / R430_J14, allow_pickle=False) as z:
        j14_axis = np.asarray(z["age_ma"], dtype=float)

    with np.load(root / R328, allow_pickle=False) as z:
        j18_axis = np.asarray(z["snapshot_age_ka"], dtype=float)

    with np.load(root / R333, allow_pickle=False) as z33:
        j21_a = np.asarray(z33["anchor_age_ka"], dtype=float)
    with np.load(root / R334, allow_pickle=False) as z34:
        j21_b = np.asarray(z34["anchor_age_ka"], dtype=float)

    j21_axes_equal = bool(np.array_equal(j21_a, j21_b))

    j14 = _time_mapping(
        j14_axis, job_id=J14, physical_unit="Ma", years_multiplier=1_000_000.0
    )
    j18 = _time_mapping(
        j18_axis, job_id=J18, physical_unit="ka", years_multiplier=1_000.0
    )
    j21 = _time_mapping(
        j21_a, job_id=J21, physical_unit="ka", years_multiplier=1_000.0
    )

    exact_expected = (
        j14["canonical_state_count"] == 141
        and j14["geonomics_T"] == 140
        and np.isclose(j14_axis[0], 3.0)
        and np.isclose(j14_axis[-1], 0.2)
        and j18["canonical_state_count"] == 15
        and j18["geonomics_T"] == 14
        and np.array_equal(
            j18_axis,
            np.asarray(
                [200, 125, 100, 75, 50, 30, 20, 15, 14, 13, 12, 11, 10, 5, 0],
                dtype=float,
            ),
        )
        and j21["canonical_state_count"] == 9
        and j21["geonomics_T"] == 8
        and np.array_equal(
            j21_a, np.asarray([20, 15, 14, 13, 12, 11, 10, 5, 0], dtype=float)
        )
    )

    return {
        "stage": STAGE,
        "status":
            "R439_EXACT_ORDINAL_TIME_MAPPING_VALIDATED"
            if j21_axes_equal and exact_expected
            and j14["pass"] and j18["pass"] and j21["pass"]
            else BLOCKED,
        "j21_r333_r334_anchor_axes_exact_equal": j21_axes_equal,
        "exact_expected_canonical_axes": bool(exact_expected),
        "jobs": {J14: j14, J18: j18, J21: j21},
        "no_interpolation": True,
        "no_generation_time_invention": True,
        "physical_rate_mapping_authority_created": False,
    }


def _j21_record_array(
    rec: dict[str, Any],
    anchor_index: int,
    *,
    env_names: list[str],
    env_fields: np.ndarray,
    producer_taxa: list[str],
    producer_vars: list[str],
    producer_landscape: np.ndarray,
) -> np.ndarray:
    family = rec.get("layer_family")
    name = str(rec.get("name"))
    if family == "environment":
        vi = env_names.index(name)
        return np.asarray(env_fields[anchor_index, :, :, vi])

    taxon = str(rec.get("taxon_id"))
    ti = producer_taxa.index(taxon)
    vi = producer_vars.index(name)
    return np.asarray(producer_landscape[ti, anchor_index, :, :, vi])


def _array_hash(a: np.ndarray) -> str:
    a = np.asarray(a)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode("utf-8"))
    h.update(str(a.shape).encode("utf-8"))
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def _r333_dynamic_representability_semantic_authority(root: Path) -> dict[str, Any]:
    """Freeze dynamic sidecar authority from SEALED R3.33 source semantics.

    This is intentionally independent of the live 0 ka out-of-range value.
    R3.33 copies/interpolates precipitation_factor and npp_factor into canonical
    fields without clipping them to [0,1]. Only the derived hydroclimate index
    applies broader clips (P to 1.5, N to 1.2).
    """
    p = root / R333_SOURCE
    actual = sha256(p) if p.exists() else None
    txt = p.read_text(encoding="utf-8") if p.exists() else ""

    required = {
        "exact_source_sha256": actual == R333_SOURCE_SHA256,
        "precip_provider_relative_book":
            "precipitation_factor_relative_book" in txt,
        "npp_provider_relative_book":
            "npp_factor_relative_book" in txt,
        "precip_interpolated_without_output_clip":
            "P=(1-w)*dp[lo]+w*dp[hi]" in txt,
        "npp_interpolated_without_output_clip":
            "N=(1-w)*dn[lo]+w*dn[hi]" in txt,
        "precip_written_directly_to_canonical_field":
            "fields[ai,...,1]=P" in txt,
        "npp_written_directly_to_canonical_field":
            "fields[ai,...,2]=N" in txt,
        "hydro_uses_broader_precip_clip_1p5":
            "np.clip(P,0,1.5)" in txt,
        "hydro_uses_broader_npp_clip_1p2":
            "np.clip(N,0,1.2)" in txt,
    }
    ok = all(required.values())
    return {
        "stage": STAGE,
        "status":
            "R439_R333_SOURCE_SEMANTIC_DYNAMIC_REPRESENTABILITY_AUTHORITY_VALIDATED"
            if ok else BLOCKED,
        "source_path": R333_SOURCE.as_posix(),
        "expected_sha256": R333_SOURCE_SHA256,
        "actual_sha256": actual,
        "checks": required,
        "checks_passed": sum(required.values()),
        "checks_total": len(required),
        "dynamic_sidecar_variables": sorted(R439_DYNAMIC_SIDECAR_NAMES),
        "r437_static_initial_sidecar_variables":
            sorted(R437_STATIC_SIDECAR_NAMES),
        "semantic_conclusion":
            "PRECIPITATION_AND_NPP_RELATIVE_FACTORS_HAVE_NO_SEALED_R3_33_0_1_"
            "CANONICAL_BOUND_AND_MUST_NOT_BE_GEONOMICS_DYNAMIC_LAYER_RAST",
        "live_minmax_used_to_define_transform": False,
        "automatic_rescaling_authorized": False,
        "clipping_authorized": False,
        "result_selected_transform_authorized": False,
        "pass": ok,
    }



def _j21_dynamic_payload_authority(
    root: Path,
    initial_manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[np.ndarray]], list[dict[str, Any]]]:
    with np.load(root / R333, allow_pickle=False) as z:
        anchors33 = np.asarray(z["anchor_age_ka"], dtype=float)
        env_names = [str(x) for x in z["environment_variable_names"]]
        env_fields = np.asarray(z["environment_fields"])
    with np.load(root / R334, allow_pickle=False) as z:
        anchors34 = np.asarray(z["anchor_age_ka"], dtype=float)
        producer_taxa = [str(x) for x in z["producer_taxon_ids"]]
        producer_vars = [str(x) for x in z["landscape_variable_names"]]
        producer_landscape = np.asarray(z["producer_landscape"])

    if not np.array_equal(anchors33, anchors34):
        return ({
            "status": "BLOCKED_R439_J21_TIME_AXES_DIFFER",
            "pass": False,
        }, {}, [])

    records = initial_manifest.get("records") or []
    if len(records) != 151:
        return ({
            "status": "BLOCKED_R439_J21_INITIAL_MANIFEST_NOT_151",
            "record_count": len(records),
            "pass": False,
        }, {}, [])

    # Reconstruct the exact R4.37 static-initial native naming first.
    # This preserves the already-SEALED 20 ka naming even though R4.39 refines
    # dynamic representability for the full 20->0 ka trajectory.
    r437_static_native_records = [
        r for r in records
        if not (
            r.get("layer_family") == "environment"
            and str(r.get("name")) in R437_STATIC_SIDECAR_NAMES
        )
    ]
    r437_name_by_payload = {}
    for i, rec in enumerate(r437_static_native_records):
        lname = (
            f"R437_ENV_{i:03d}"
            if rec.get("layer_family") == "environment"
            else f"R437_PRD_{i:03d}"
        )
        r437_name_by_payload[rec["payload_file"]] = lname

    native_records = [
        r for r in records
        if not (
            r.get("layer_family") == "environment"
            and str(r.get("name")) in R439_DYNAMIC_SIDECAR_NAMES
        )
    ]
    sidecar_records = [
        r for r in records
        if r.get("layer_family") == "environment"
        and str(r.get("name")) in R439_DYNAMIC_SIDECAR_NAMES
    ]

    # Two dynamic sidecars (precip/NPP) were valid static R4.37 layers at 20 ka.
    # Record their frozen R4.37 names so R4.39 can remove them from dynamic
    # Geonomics params rather than normalize them.
    bound_dynamic_sidecars = {
        r437_name_by_payload[r["payload_file"]]: str(r.get("name"))
        for r in sidecar_records
        if r["payload_file"] in r437_name_by_payload
    }

    dynamic_by_name: dict[str, list[np.ndarray]] = {}
    identity_rows = []
    sidecar_rows = []
    all_native_ok = True
    all_sidecar_ok = True

    for rec in native_records:
        lname = r437_name_by_payload[rec["payload_file"]]
        states = []
        state_rows = []
        for ai in range(len(anchors33)):
            arr = _j21_record_array(
                rec,
                ai,
                env_names=env_names,
                env_fields=env_fields,
                producer_taxa=producer_taxa,
                producer_vars=producer_vars,
                producer_landscape=producer_landscape,
            )
            finite = bool(np.all(np.isfinite(arr)))
            amin = float(np.min(arr))
            amax = float(np.max(arr))
            native_range = finite and amin >= 0.0 and amax <= 1.0
            all_native_ok = all_native_ok and native_range
            states.append(arr)
            state_rows.append({
                "anchor_index": ai,
                "age_ka": float(anchors33[ai]),
                "sha256": _array_hash(arr),
                "finite": finite,
                "min": amin,
                "max": amax,
                "native_range_0_1": native_range,
            })
        dynamic_by_name[lname] = states
        identity_rows.append({
            "native_layer_name": lname,
            "layer_family": rec.get("layer_family"),
            "variable_name": rec.get("name"),
            "taxon_id": rec.get("taxon_id"),
            "anchor_state_count": len(states),
            "all_states_native_range_0_1": all(x["native_range_0_1"] for x in state_rows),
            "states": state_rows,
        })

    for rec in sidecar_records:
        state_rows = []
        for ai in range(len(anchors33)):
            arr = _j21_record_array(
                rec,
                ai,
                env_names=env_names,
                env_fields=env_fields,
                producer_taxa=producer_taxa,
                producer_vars=producer_vars,
                producer_landscape=producer_landscape,
            )
            finite = bool(np.all(np.isfinite(arr)))
            all_sidecar_ok = all_sidecar_ok and finite
            state_rows.append({
                "anchor_index": ai,
                "age_ka": float(anchors33[ai]),
                "sha256": _array_hash(arr),
                "finite": finite,
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "bound_as_geonomics_layer": False,
            })
        sidecar_rows.append({
            "variable_name": rec.get("name"),
            "canonical_sidecar_semantics":
                "R3_33_NATIVE_PHYSICAL_OR_RELATIVE_FACTOR_SEMANTICS_PRESERVED",
            "r437_static_bound_layer_name":
                r437_name_by_payload.get(rec["payload_file"]),
            "bound_as_r439_dynamic_geonomics_layer": False,
            "anchor_state_count": len(state_rows),
            "states": state_rows,
        })

    total_native_states = len(native_records) * len(anchors33)
    future_change_targets = len(native_records) * (len(anchors33) - 1)

    out = {
        "stage": STAGE,
        "status":
            "R439_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY_VALIDATED"
            if (
                len(native_records) == 147
                and len(sidecar_records) == 4
                and total_native_states == 1323
                and future_change_targets == 1176
                and all_native_ok
                and all_sidecar_ok
            )
            else BLOCKED,
        "anchor_age_ka": [float(x) for x in anchors33],
        "native_identity_layer_count": len(native_records),
        "canonical_dynamic_sidecar_count": len(sidecar_records),
        "r437_static_initial_native_layer_count": len(r437_static_native_records),
        "r437_static_initial_sidecar_count": 2,
        "r439_bound_dynamic_sidecar_layer_names": bound_dynamic_sidecars,
        "native_identity_anchor_state_count": total_native_states,
        "future_exact_change_target_count": future_change_targets,
        "all_native_states_finite_and_0_1": all_native_ok,
        "all_sidecars_finite": all_sidecar_ok,
        "sidecars_bound_into_geonomics_layers": False,
        "automatic_rescaling_performed": False,
        "clipping_performed": False,
        "cross_layer_numeric_fusion_performed": False,
        "result_selected_transform_performed": False,
        "canonical_values_modified": False,
        "native_identity_records": identity_rows,
        "physical_sidecars": sidecar_rows,
        "pass": bool(
            len(native_records) == 147
            and len(sidecar_records) == 4
            and total_native_states == 1323
            and future_change_targets == 1176
            and all_native_ok
            and all_sidecar_ok
        ),
    }
    return out, dynamic_by_name, native_records, bound_dynamic_sidecars


def _r437_j21_bound_param_path(root: Path, replicate_index: int) -> Path:
    return (
        root
        / "outputs/v0_6D1_R4_37/geonomics_native"
        / J21
        / f"replicate_{replicate_index}"
        / "GNX_R437_CANONICAL_LAYER_BOUND_PARAMS.py"
    )


def _native_seed_rows(native: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    rows = [
        r for r in (native.get("records") or [])
        if r.get("job_id") == job_id and r.get("construction_pass") is True
    ]
    return sorted(rows, key=lambda r: int(r["replicate_index"]))


def _add_exact_j21_change_schedule(
    params: dict[str, Any],
    dynamic_by_name: dict[str, list[np.ndarray]],
    bound_dynamic_sidecars: dict[str, str],
    *,
    frozen_seed: int,
    replicate_index: int,
) -> dict[str, Any]:
    p = copy.deepcopy(params)
    layers = p["landscape"]["layers"]
    canonical_names = list(dynamic_by_name.keys())

    if "R437_CONSTRUCTION_SUPPORT" not in layers:
        raise RuntimeError("R439 expected R437_CONSTRUCTION_SUPPORT")

    if set(bound_dynamic_sidecars.values()) != {
        "precipitation_factor", "npp_factor"
    }:
        raise RuntimeError(
            "R439 expected exactly precipitation_factor and npp_factor as "
            "R4.37-bound but R4.39-dynamic-sidecar fields"
        )
    for lname in bound_dynamic_sidecars:
        if lname not in layers:
            raise RuntimeError(f"R439 missing R4.37 bound sidecar layer {lname}")
        del layers[lname]

    if set(canonical_names) != (set(layers.keys()) - {"R437_CONSTRUCTION_SUPPORT"}):
        raise RuntimeError(
            "R439 refined dynamic layer names do not match R4.37 params after "
            "source-semantic sidecar removal"
        )

    for lname in canonical_names:
        states = dynamic_by_name[lname]
        if len(states) != 9:
            raise RuntimeError("R439 expected 9 J21 anchor states")
        layers[lname]["change"] = {}
        for t in range(8):
            layers[lname]["change"][t] = {
                "change_rast": states[t + 1],
                "start_t": t,
                "end_t": t,
                "n_steps": 1,
            }

    p["model"]["T"] = 8
    p["model"]["burn_T"] = 0
    p["model"]["seed"] = {"num": int(frozen_seed)}
    if "num" in p["model"]:
        p["model"]["num"] = int(frozen_seed)
    p["model"]["name"] = f"ARCANA_R439_{J21}_REP{replicate_index}_DYNAMIC_PREFLIGHT"
    return p


def _inspect_compiled_j21_schedule(
    mod: Any,
    dynamic_by_name: dict[str, list[np.ndarray]],
) -> dict[str, Any]:
    changer = mod.land._changer
    if changer is None:
        return {"pass": False, "error": "NO_LANDSCAPE_CHANGER"}

    first = changer.next_change
    rest = list(changer.changes)
    schedule = ([] if first is None else [first]) + rest

    # Restore iterator state immediately; no change is executed.
    changer.next_change = first
    changer.changes = iter(rest)

    name_by_idx = {idx: lyr.name for idx, lyr in mod.land.items()}
    initial_exact = 0
    for lname, states in dynamic_by_name.items():
        lyr = next((lyr for lyr in mod.land.values() if lyr.name == lname), None)
        if lyr is not None and np.array_equal(np.asarray(lyr.rast), np.asarray(states[0])):
            initial_exact += 1

    times = []
    compiled_exact = 0
    bad = []
    for t, fn in schedule:
        times.append(int(t))
        defaults = getattr(fn, "__defaults__", None)
        if not defaults or len(defaults) < 2:
            bad.append({"t": int(t), "reason": "CHANGE_FN_DEFAULTS_MISSING"})
            continue
        lyr_num = int(defaults[-2])
        target = np.asarray(defaults[-1])
        lname = name_by_idx.get(lyr_num)
        if lname not in dynamic_by_name:
            bad.append({"t": int(t), "layer_num": lyr_num, "reason": "UNKNOWN_LAYER"})
            continue
        expected = np.asarray(dynamic_by_name[lname][int(t) + 1])
        same = target.shape == expected.shape and np.array_equal(target, expected)
        compiled_exact += int(same)
        if not same:
            bad.append({
                "t": int(t),
                "layer_num": lyr_num,
                "layer_name": lname,
                "reason": "COMPILED_TARGET_MISMATCH",
            })

    counts = Counter(times)
    per_t_exact = all(counts.get(t) == 147 for t in range(8))
    schedule_count = len(schedule)

    return {
        "pass": bool(
            initial_exact == 147
            and schedule_count == 1176
            and compiled_exact == 1176
            and per_t_exact
            and first is not None
            and int(first[0]) == 0
            and len(changer.change_info) == 147
        ),
        "initial_native_layers_exact_count": initial_exact,
        "compiled_change_count": schedule_count,
        "compiled_change_target_exact_count": compiled_exact,
        "compiled_change_mismatch_count": len(bad),
        "first_10_mismatches": bad[:10],
        "changes_per_timestep": {str(t): counts.get(t, 0) for t in range(8)},
        "exact_147_changes_per_timestep": per_t_exact,
        "next_change_timestep": None if first is None else int(first[0]),
        "landscape_change_info_layer_count": len(changer.change_info),
        "changer_make_change_called": False,
        "model_run_performed": False,
    }


def _j21_dynamic_model_preflight(
    root: Path,
    native: dict[str, Any],
    dynamic_by_name: dict[str, list[np.ndarray]],
    bound_dynamic_sidecars: dict[str, str],
) -> dict[str, Any]:
    import geonomics as gnx

    version = str(getattr(gnx, "__version__", "UNKNOWN"))
    if version != "1.4.9":
        return {"status": "BLOCKED_R439_GEONOMICS_VERSION", "geonomics_version": version}

    seed_rows = _native_seed_rows(native, J21)
    if len(seed_rows) != 4:
        return {"status": "BLOCKED_R439_J21_SEED_ROWS", "record_count": len(seed_rows)}

    records = []
    for row in seed_rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        bound_file = _r437_j21_bound_param_path(root, rep)
        try:
            base = _import_params_module(bound_file)
            dyn = _add_exact_j21_change_schedule(
                base,
                dynamic_by_name,
                bound_dynamic_sidecars,
                frozen_seed=seed,
                replicate_index=rep,
            )
            pdict = gnx.make_params_dict(dyn, model_name=dyn["model"]["name"])
            mod = gnx.make_model(parameters=pdict, verbose=False)

            seed_ok = mod.seed == seed
            unrun = mod.t == -1 and mod.burn_t == -1 and mod.it == -1
            T_ok = mod.T == 8
            movement_off = all(spp._move is False for spp in mod.comm.values())
            compiled = _inspect_compiled_j21_schedule(mod, dynamic_by_name)

            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "model_seed_match": seed_ok,
                "model_T": mod.T,
                "model_T_exact_8": T_ok,
                "model_unrun": unrun,
                "movement_disabled": movement_off,
                "removed_r437_static_bound_dynamic_sidecar_count":
                    len(bound_dynamic_sidecars),
                "removed_r437_static_bound_dynamic_sidecars":
                    bound_dynamic_sidecars,
                "compiled_schedule": compiled,
                "autonomous_population_dynamics_executed": False,
                "autonomous_movement_executed": False,
                "pass": bool(
                    seed_ok and unrun and T_ok and movement_off and compiled["pass"]
                ),
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
        "stage": STAGE,
        "status":
            "R439_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT_VALIDATED"
            if len(records) == 4 and pass_count == 4
            else BLOCKED,
        "geonomics_version": version,
        "replicate_count": len(records),
        "replicate_pass_count": pass_count,
        "native_dynamic_layer_count": 147,
        "anchor_state_count": 9,
        "compiled_exact_change_target_count_per_replicate": 1176,
        "compiled_exact_change_target_count_all_replicates": 1176 * pass_count,
        "dynamic_sidecars_in_changer": False,
        "dynamic_sidecar_count": 4,
        "r437_bound_layers_removed_before_dynamic_model_construction": 2,
        "intermediate_raster_interpolation_authorized": False,
        "each_event_n_steps": 1,
        "each_event_start_t_equals_end_t": True,
        "changer_make_change_called": False,
        "model_run_performed_count": 0,
        "records": records,
    }


def _carrier_dynamics_authority_gate(root: Path) -> dict[str, Any]:
    import geonomics as gnx

    # Inspect the live governed runtime, not a copied source file.
    model_src = inspect.getsource(gnx.Model._make_fn_queue)

    required_tokens = {
        "timestep_increment": "queue.append(self._set_t)" in model_src,
        "community_timestep_increment": "queue.append(self._set_comm_t)" in model_src,
        "species_timestep_increment": "_set_spp_t" in model_src,
        "movement_auto_queue": "_do_movement" in model_src,
        "population_dynamics_auto_queue": "_do_pop_dynamics" in model_src,
        "landscape_change_auto_queue": "_make_land_change" in model_src,
        "K_refresh_after_land_change": "_set_K" in model_src,
    }

    native = load(root / R436_NATIVE)
    param_rows = []
    for job_id in (J14, J18):
        for row in _native_seed_rows(native, job_id):
            pf = root / row["native_parameter_file"]
            params = _import_params_module(pf)
            species = params["comm"]["species"]
            move_values = [
                bool(s.get("movement", {}).get("move", False))
                for s in species.values()
            ]
            param_rows.append({
                "job_id": job_id,
                "replicate_index": int(row["replicate_index"]),
                "all_movement_flags_false": all(v is False for v in move_values),
                "species_count": len(species),
            })

    source_complete = all(required_tokens.values())
    all_movement_off = len(param_rows) == 8 and all(
        r["all_movement_flags_false"] for r in param_rows
    )

    return {
        "stage": STAGE,
        "status":
            "R439_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GAP_FROZEN"
            if source_complete and all_movement_off
            else BLOCKED,
        "live_geonomics_version": str(getattr(gnx, "__version__", "UNKNOWN")),
        "main_queue_source_requirements": required_tokens,
        "main_queue_source_requirements_pass": source_complete,
        "j14_j18_native_parameter_records_checked": len(param_rows),
        "all_j14_j18_movement_flags_false": all_movement_off,
        "parameter_records": param_rows,
        "carrier_semantics": "ONE_NONLITERAL_CONNECTIVITY_CARRIER_PER_ACTIVE_CANONICAL_DEME",
        "carrier_count_literal_population": False,
        "population_proxy_is_carrier_count": False,
        "physical_rate_mapping_authority_present": False,
        "autonomous_movement_authorized": False,
        "autonomous_population_dynamics_authorized": False,
        "autonomous_ageing_interpretation_authorized": False,
        "default_main_fn_queue_scientific_execution_authorized": False,
        "reason":
            "GEONOMICS_MAIN_QUEUE_AUTOMATICALLY_INCLUDES_POPULATION_DYNAMICS_AND_"
            "CAN_INCLUDE_MOVEMENT_BUT_NO_PRE_RESULT_AUTHORITY_MAPS_NONLITERAL_"
            "CARRIERS_OR_VARIABLE_PHYSICAL_INTERVALS_TO_THOSE_RATES",
        "execution_performed": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R438_AUDIT)
    parent_seal = load(root / R438_SEAL)
    native = load(root / R436_NATIVE)
    initial_manifest = load(root / R436_J21_MANIFEST)

    source_hashes = _source_hash_audit(root)
    time = _build_time_authority(root)
    write(root / OUT / "R4_39_EXACT_ORDINAL_TIME_MAPPING.json", time)

    r333_semantics = _r333_dynamic_representability_semantic_authority(root)
    write(
        root / OUT / "R4_39_R333_DYNAMIC_REPRESENTABILITY_SEMANTIC_AUTHORITY.json",
        r333_semantics,
    )

    j21_payload, dynamic_by_name, native_records, bound_dynamic_sidecars = (
        _j21_dynamic_payload_authority(root, initial_manifest)
        if r333_semantics.get("pass") is True
        else ({"status": BLOCKED, "pass": False}, {}, [], {})
    )
    write(
        root / OUT / "R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json",
        j21_payload,
    )

    j21_dynamic = (
        _j21_dynamic_model_preflight(
            root, native, dynamic_by_name, bound_dynamic_sidecars
        )
        if j21_payload.get("pass") is True
        else {"status": BLOCKED, "replicate_pass_count": 0}
    )
    write(
        root / OUT / "R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json",
        j21_dynamic,
    )

    dynamics = _carrier_dynamics_authority_gate(root)
    write(root / OUT / "R4_39_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GATE.json", dynamics)

    checks = {
        "parent_r438_complete_29_29":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 29
            and parent.get("checks_failed") == 0,
        "parent_r438_sealed_21_21":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 21
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r439":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R439_TIME_AND_LAYER_MACHINERY_PREFLIGHT_CARRIER_DYNAMICS_NOT_AUTHORIZED",
        "all_four_source_hashes_exact":
            source_hashes.get("all_hashes_match") is True,
        "time_mapping_complete":
            str(time.get("status", "")).startswith("R439_EXACT_ORDINAL_"),
        "j14_time_141_states_T140":
            time["jobs"][J14]["canonical_state_count"] == 141
            and time["jobs"][J14]["geonomics_T"] == 140,
        "j18_time_15_states_T14":
            time["jobs"][J18]["canonical_state_count"] == 15
            and time["jobs"][J18]["geonomics_T"] == 14,
        "j21_time_9_states_T8":
            time["jobs"][J21]["canonical_state_count"] == 9
            and time["jobs"][J21]["geonomics_T"] == 8,
        "j18_variable_duration_mapping_explicit":
            time["jobs"][J18]["variable_duration_ordinal_transition_mapping"] is True,
        "j21_variable_duration_mapping_explicit":
            time["jobs"][J21]["variable_duration_ordinal_transition_mapping"] is True,
        "no_physical_rate_authority_invented":
            time.get("physical_rate_mapping_authority_created") is False,
        "r333_dynamic_representability_source_semantics":
            r333_semantics.get("pass") is True
            and r333_semantics.get("actual_sha256") == R333_SOURCE_SHA256,
        "j21_147_native_4_dynamic_sidecars":
            j21_payload.get("native_identity_layer_count") == 147
            and j21_payload.get("canonical_dynamic_sidecar_count") == 4,
        "j21_r437_static_149_plus_2_history_preserved":
            j21_payload.get("r437_static_initial_native_layer_count") == 149
            and j21_payload.get("r437_static_initial_sidecar_count") == 2,
        "j21_exact_1323_native_anchor_states":
            j21_payload.get("native_identity_anchor_state_count") == 1323,
        "j21_exact_1176_future_change_targets":
            j21_payload.get("future_exact_change_target_count") == 1176,
        "j21_all_native_states_0_1":
            j21_payload.get("all_native_states_finite_and_0_1") is True,
        "j21_dynamic_sidecars_preserved_outside_changer":
            j21_payload.get("sidecars_bound_into_geonomics_layers") is False
            and j21_dynamic.get("dynamic_sidecars_in_changer") is False
            and j21_dynamic.get("dynamic_sidecar_count") == 4,
        "j21_two_r437_bound_relative_factor_layers_removed":
            j21_dynamic.get(
                "r437_bound_layers_removed_before_dynamic_model_construction"
            ) == 2,
        "j21_no_scaling_clipping_fusion":
            j21_payload.get("automatic_rescaling_performed") is False
            and j21_payload.get("clipping_performed") is False
            and j21_payload.get("cross_layer_numeric_fusion_performed") is False,
        "j21_four_dynamic_model_preflights":
            j21_dynamic.get("replicate_pass_count") == 4,
        "j21_4704_compiled_exact_targets":
            j21_dynamic.get("compiled_exact_change_target_count_all_replicates")
            == 4704,
        "j21_no_changer_execution":
            j21_dynamic.get("changer_make_change_called") is False
            and j21_dynamic.get("model_run_performed_count") == 0,
        "carrier_dynamics_gap_frozen":
            dynamics.get("status")
            == "R439_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GAP_FROZEN",
        "carrier_not_literal_population":
            dynamics.get("carrier_count_literal_population") is False
            and dynamics.get("population_proxy_is_carrier_count") is False,
        "movement_not_authorized":
            dynamics.get("autonomous_movement_authorized") is False,
        "population_dynamics_not_authorized":
            dynamics.get("autonomous_population_dynamics_authorized") is False,
        "ageing_not_authorized":
            dynamics.get("autonomous_ageing_interpretation_authorized") is False,
        "default_main_queue_not_scientifically_authorized":
            dynamics.get("default_main_fn_queue_scientific_execution_authorized") is False,
        "no_model_run":
            j21_dynamic.get("model_run_performed_count") == 0,
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
        "r438_adapter_preserved":
            parent.get("exact_initialization_adapter_validated") is True
            and parent.get("construction_probe_elimination_validated") is True,
        "r437_j21_596_preserved":
            parent.get("checks", {}).get("r437_j21_binding_preserved") is True,
        "deferred_p2_two":
            parent.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            parent.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            parent.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    plan = {
        "stage": STAGE,
        "status":
            "R439_TIME_LAYER_PREFLIGHT_COMPLETE_CARRIER_DYNAMICS_AUTHORITY_STILL_REQUIRED"
            if ok else BLOCKED,
        "exact_ordinal_time_mapping_validated": bool(ok),
        "j21_dynamic_layer_changer_construction_validated": bool(ok),
        "nonliteral_carrier_dynamics_authority_closed": False,
        "autonomous_population_dynamics_authorized": False,
        "autonomous_movement_authorized": False,
        "production_execution_queue_authorized": False,
        "geonomics_execution_ready": False,
        "next_action":
            NEXT if ok else "REPAIR_R439_TIME_LAYER_OR_DYNAMICS_AUTHORITY_PREFLIGHT",
    }
    write(root / OUT / "R4_39_R440_EXECUTION_PLAN.json", plan)

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "geonomics_version": j21_dynamic.get("geonomics_version", "1.4.9"),
        "j14_canonical_state_count": time["jobs"][J14]["canonical_state_count"],
        "j14_geonomics_T": time["jobs"][J14]["geonomics_T"],
        "j18_canonical_state_count": time["jobs"][J18]["canonical_state_count"],
        "j18_geonomics_T": time["jobs"][J18]["geonomics_T"],
        "j21_canonical_state_count": time["jobs"][J21]["canonical_state_count"],
        "j21_geonomics_T": time["jobs"][J21]["geonomics_T"],
        "j21_native_dynamic_layer_count": j21_dynamic.get("native_dynamic_layer_count"),
        "j21_native_anchor_state_count":
            j21_payload.get("native_identity_anchor_state_count"),
        "j21_future_change_target_count":
            j21_payload.get("future_exact_change_target_count"),
        "j21_dynamic_preflight_replicate_pass_count":
            j21_dynamic.get("replicate_pass_count"),
        "j21_compiled_exact_change_targets_all_replicates":
            j21_dynamic.get("compiled_exact_change_target_count_all_replicates"),
        "j21_dynamic_sidecar_count":
            j21_payload.get("canonical_dynamic_sidecar_count"),
        "j21_dynamic_sidecar_variables":
            sorted(R439_DYNAMIC_SIDECAR_NAMES),
        "nonliteral_carrier_dynamics_authority_closed": False,
        "autonomous_population_dynamics_authorized": False,
        "autonomous_movement_authorized": False,
        "autonomous_ageing_interpretation_authorized": False,
        "production_execution_queue_authorized": False,
        "geonomics_execution_ready": False,
        "model_run_performed_count": 0,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action": plan["next_action"],
    }
    write(root / OUT / "R4_39_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_39_INTEGRATED_AUDIT.json")
    t = load(root / OUT / "R4_39_EXACT_ORDINAL_TIME_MAPPING.json")
    sem = load(
        root / OUT / "R4_39_R333_DYNAMIC_REPRESENTABILITY_SEMANTIC_AUTHORITY.json"
    )
    p = load(root / OUT / "R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json")
    d = load(root / OUT / "R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json")
    c = load(root / OUT / "R4_39_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GATE.json")
    plan = load(root / OUT / "R4_39_R440_EXECUTION_PLAN.json")

    checks = {
        "r439_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "time_mapping_validated":
            t.get("status") == "R439_EXACT_ORDINAL_TIME_MAPPING_VALIDATED",
        "time_T_140_14_8":
            t["jobs"][J14]["geonomics_T"] == 140
            and t["jobs"][J18]["geonomics_T"] == 14
            and t["jobs"][J21]["geonomics_T"] == 8,
        "no_physical_rate_invention":
            t.get("physical_rate_mapping_authority_created") is False,
        "r333_source_semantics_validated":
            sem.get("pass") is True
            and sem.get("actual_sha256") == R333_SOURCE_SHA256,
        "j21_dynamic_147_plus_4":
            p.get("native_identity_layer_count") == 147
            and p.get("canonical_dynamic_sidecar_count") == 4,
        "j21_static_r437_history_149_plus_2_preserved":
            p.get("r437_static_initial_native_layer_count") == 149
            and p.get("r437_static_initial_sidecar_count") == 2,
        "j21_1323_anchor_states":
            p.get("native_identity_anchor_state_count") == 1323,
        "j21_1176_change_targets":
            p.get("future_exact_change_target_count") == 1176,
        "j21_4_dynamic_preflights":
            d.get("replicate_pass_count") == 4,
        "j21_4704_exact_compiled_targets":
            d.get("compiled_exact_change_target_count_all_replicates") == 4704,
        "j21_no_scaling_or_sidecar_binding":
            p.get("automatic_rescaling_performed") is False
            and p.get("sidecars_bound_into_geonomics_layers") is False,
        "carrier_dynamics_gap_frozen":
            c.get("status")
            == "R439_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GAP_FROZEN",
        "movement_not_authorized":
            c.get("autonomous_movement_authorized") is False,
        "population_dynamics_not_authorized":
            c.get("autonomous_population_dynamics_authorized") is False,
        "ageing_not_authorized":
            c.get("autonomous_ageing_interpretation_authorized") is False,
        "default_queue_not_authorized":
            c.get("default_main_fn_queue_scientific_execution_authorized") is False,
        "execution_queue_not_authorized":
            a.get("production_execution_queue_authorized") is False,
        "execution_not_ready":
            a.get("geonomics_execution_ready") is False,
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
        "r440_plan_frozen":
            plan.get("next_action") == NEXT
            and plan.get("nonliteral_carrier_dynamics_authority_closed") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r440":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_"
            "AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "j14_geonomics_T": a.get("j14_geonomics_T"),
            "j18_geonomics_T": a.get("j18_geonomics_T"),
            "j21_geonomics_T": a.get("j21_geonomics_T"),
            "j21_native_dynamic_layer_count":
                a.get("j21_native_dynamic_layer_count"),
            "j21_native_anchor_state_count":
                a.get("j21_native_anchor_state_count"),
            "j21_future_change_target_count":
                a.get("j21_future_change_target_count"),
            "j21_compiled_exact_change_targets_all_replicates":
                a.get("j21_compiled_exact_change_targets_all_replicates"),
            "j21_dynamic_sidecar_count":
                a.get("j21_dynamic_sidecar_count"),
            "j21_dynamic_sidecar_variables":
                a.get("j21_dynamic_sidecar_variables"),
            "nonliteral_carrier_dynamics_authority_closed": False,
            "autonomous_population_dynamics_authorized": False,
            "autonomous_movement_authorized": False,
            "production_execution_queue_authorized": False,
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
