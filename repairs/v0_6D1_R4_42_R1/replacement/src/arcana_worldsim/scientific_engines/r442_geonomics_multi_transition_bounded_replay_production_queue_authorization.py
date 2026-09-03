from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import json
import random

import numpy as np

STAGE = "v0.6D1-R4.42"

PARENT_COMPLETE = (
    "PASS_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
    "DRY_RUN_AND_STATE_INVARIANT_VALIDATION_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
    "DRY_RUN_AND_STATE_INVARIANT_VALIDATION_SEALED"
)
PARENT_NEXT = (
    "BUILD_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
    "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT"
)

COMPLETE = (
    "PASS_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
    "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
    "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R442_MULTI_TRANSITION_REPLAY_OR_PRODUCTION_QUEUE_AUTHORIZATION_"
    "PREFLIGHT_FAILURE"
)
NEXT = (
    "BUILD_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
    "AND_ADJUDICATION_SCHEMA_PREFLIGHT"
)

OUT = Path("outputs/v0_6D1_R4_42")
SEAL = Path("outputs/v0_6D1_R4_42_SEAL/R4_42_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r442_geonomics_multi_transition_bounded_replay_"
    "production_execution_queue_authorization_preflight_v0_6D1_R4_42.json"
)

R441 = Path("outputs/v0_6D1_R4_41/R4_41_INTEGRATED_AUDIT.json")
R441_SEAL = Path("outputs/v0_6D1_R4_41_SEAL/R4_41_FINAL_SEAL_AUDIT.json")
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
    name = "r442_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
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


def _rng_digest() -> dict[str, str]:
    py = hashlib.sha256(repr(random.getstate()).encode()).hexdigest()
    st = np.random.get_state()
    blob = (
        str(st[0]).encode()
        + st[1].tobytes()
        + str(st[2]).encode()
        + str(st[3]).encode()
        + repr(float(st[4])).encode()
    )
    return {
        "python_random": py,
        "numpy_random": hashlib.sha256(blob).hexdigest(),
    }


def _array_digest(a: np.ndarray) -> str:
    a = np.asarray(a)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def _land_digest(land: Any) -> str:
    h = hashlib.sha256()
    for k, lyr in land.items():
        h.update(str(k).encode())
        h.update(str(lyr.name).encode())
        h.update(_array_digest(np.asarray(lyr.rast)).encode())
    return h.hexdigest()


def _coords_from_spp(spp: Any) -> np.ndarray:
    return np.asarray(
        [[float(ind.x), float(ind.y)] for ind in spp.values()],
        dtype=float,
    )


def _coords_exact(a: np.ndarray, b: np.ndarray) -> bool:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return a.shape == b.shape and np.array_equal(a, b)


def _j14_first_branch_full(root: Path) -> dict[str, Any]:
    p = root / J14_SOURCE
    if sha256(p) != J14_SHA:
        raise RuntimeError("J14 source hash mismatch")
    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        s = np.asarray(z["spatial_state"], dtype=float)[0, 0]
    pi = names.index("population_proxy")
    ri = names.index("grid_row")
    ci = names.index("grid_col")
    ai = names.index("active")
    states = []
    for ti, age in enumerate(ages):
        mask = s[ti, :, ai] > 0.5
        coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
        if len(coords) <= 0:
            raise RuntimeError(f"J14 first branch zero carriers at index {ti}")
        states.append({
            "age": float(age),
            "coords": coords,
            "population_proxy": s[ti, mask, pi],
        })
    return {
        "selection": "member_index_0_candidate_index_0_full_sequence",
        "states": states,
    }


def _j18_first_branch_full(root: Path) -> dict[str, Any]:
    p = root / J18_SOURCE
    if sha256(p) != J18_SHA:
        raise RuntimeError("J18 source hash mismatch")
    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["snapshot_age_ka"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        s = np.asarray(z["snapshot_deme_state"], dtype=float)[0, 0]
        active = np.asarray(z["snapshot_active"])[0, 0]
    pi = names.index("population_proxy")
    ri = names.index("grid_row")
    ci = names.index("grid_col")
    states = []
    for ti, age in enumerate(ages):
        mask = np.asarray(active[ti], dtype=float) > 0.5
        coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
        if len(coords) <= 0:
            raise RuntimeError(f"J18 first branch zero carriers at index {ti}")
        states.append({
            "age": float(age),
            "coords": coords,
            "population_proxy": s[ti, mask, pi],
        })
    return {
        "selection": "member_index_0_candidate_index_0_full_sequence",
        "states": states,
    }


def _advance_authorized_clock_expected(
    mod: Any,
    *,
    expected_before_t: int,
) -> dict[str, Any]:
    """Advance only the R4.40-authorized ordinal clock primitives.

    Unlike the R4.41 single-transition helper, this validator is explicitly
    multi-step: it accepts any expected current ordinal t and requires exactly
    t -> t+1 for model, community, and every species clock.
    """
    before = {
        "model_t": int(mod.t),
        "community_t": int(mod.comm.t),
        "species_t": [int(spp.t) for spp in mod.comm.values()],
    }

    before_exact = bool(
        before["model_t"] == expected_before_t
        and before["community_t"] == expected_before_t
        and all(t == expected_before_t for t in before["species_t"])
    )

    mod._set_t()
    mod._set_comm_t()
    for spp_idx in mod.comm.keys():
        mod._set_spp_t(spp_idx)

    expected_after_t = expected_before_t + 1
    after = {
        "model_t": int(mod.t),
        "community_t": int(mod.comm.t),
        "species_t": [int(spp.t) for spp in mod.comm.values()],
    }
    after_exact = bool(
        after["model_t"] == expected_after_t
        and after["community_t"] == expected_after_t
        and all(t == expected_after_t for t in after["species_t"])
    )

    return {
        "before": before,
        "after": after,
        "expected_before_t": expected_before_t,
        "expected_after_t": expected_after_t,
        "before_exact": before_exact,
        "after_exact": after_exact,
        "pass": bool(before_exact and after_exact),
        "model_set_t_called": 1,
        "community_set_t_called": 1,
        "species_set_t_call_count": len(mod.comm),
        "age_stage_called": False,
        "Nt_record_called": False,
        "movement_called": False,
        "population_dynamics_called": False,
        "land_changer_called": False,
    }



def _run_carrier_full_sequence(
    root: Path,
    native: dict[str, Any],
    job_id: str,
    branch: dict[str, Any],
) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight import (
        _install_exact_nonliteral_carriers,
    )
    from arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run import (
        _exact_carrier_replace_preserve_clock,
    )

    rows = _native_rows(native, job_id)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_NATIVE_ROWS"}

    states = branch["states"]
    transition_count = len(states) - 1
    records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(_import_params(root / row["native_parameter_file"]))
            params["model"]["T"] = transition_count
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R442_{job_id}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )
            spp = mod.comm[0]
            template = copy.deepcopy(next(iter(spp.values())))

            init = _install_exact_nonliteral_carriers(
                mod, template, states[0]["coords"].tolist()
            )
            initial_exact = _coords_exact(
                _coords_from_spp(mod.comm[0]), states[0]["coords"]
            )
            orig_initial_exact = _coords_exact(
                _coords_from_spp(mod.orig_comm[0]), states[0]["coords"]
            )

            seed_before = mod.seed
            rng_before = _rng_digest()
            land_before = _land_digest(mod.land)
            k_before = _array_digest(np.asarray(spp.K)) if spp.K is not None else None

            transition_rows = []
            for ti in range(transition_count):
                clock = _advance_authorized_clock_expected(
                    mod, expected_before_t=ti - 1
                )
                repl = _exact_carrier_replace_preserve_clock(
                    mod, template, states[ti + 1]["coords"].tolist()
                )
                target_exact = _coords_exact(
                    _coords_from_spp(mod.comm[0]), states[ti + 1]["coords"]
                )
                orig_still_initial = _coords_exact(
                    _coords_from_spp(mod.orig_comm[0]), states[0]["coords"]
                )
                births_empty = list(mod.comm[0].n_births) == []
                deaths_empty = list(mod.comm[0].n_deaths) == []
                ages_zero = all(int(ind.age) == 0 for ind in mod.comm[0].values())
                expected_clock = ti
                clock_exact = (
                    mod.t == expected_clock
                    and mod.comm.t == expected_clock
                    and mod.comm[0].t == expected_clock
                )
                transition_rows.append({
                    "transition_index": ti,
                    "source_age": states[ti]["age"],
                    "target_age": states[ti + 1]["age"],
                    "target_carrier_count": len(states[ti + 1]["coords"]),
                    "clock_exact": clock_exact,
                    "clock_helper_pass": clock.get("pass") is True,
                    "replacement_pass": repl.get("pass") is True,
                    "target_exact": target_exact,
                    "orig_comm_still_initial": orig_still_initial,
                    "births_empty": births_empty,
                    "deaths_empty": deaths_empty,
                    "ages_zero": ages_zero,
                    "pass": bool(
                        clock_exact
                        and clock.get("pass") is True
                        and repl.get("pass") is True
                        and target_exact
                        and orig_still_initial
                        and births_empty
                        and deaths_empty
                        and ages_zero
                    ),
                })

            k_after = _array_digest(np.asarray(mod.comm[0].K)) if mod.comm[0].K is not None else None
            final_exact = _coords_exact(
                _coords_from_spp(mod.comm[0]), states[-1]["coords"]
            )
            pass_count = sum(bool(x["pass"]) for x in transition_rows)
            passed = all([
                init.get("pass") is True,
                initial_exact,
                orig_initial_exact,
                mod.seed == seed_before == seed,
                pass_count == transition_count,
                final_exact,
                _coords_exact(
                    _coords_from_spp(mod.orig_comm[0]), states[0]["coords"]
                ),
                rng_before == _rng_digest(),
                land_before == _land_digest(mod.land),
                k_before == k_after,
                mod.t == transition_count - 1,
                mod.comm.t == transition_count - 1,
                mod.comm[0].t == transition_count - 1,
                list(mod.comm[0].n_births) == [],
                list(mod.comm[0].n_deaths) == [],
                all(int(ind.age) == 0 for ind in mod.comm[0].values()),
            ])

            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "canonical_state_count": len(states),
                "transition_count": transition_count,
                "transition_pass_count": pass_count,
                "initial_exact": initial_exact,
                "final_exact": final_exact,
                "orig_comm_initial_preserved": _coords_exact(
                    _coords_from_spp(mod.orig_comm[0]), states[0]["coords"]
                ),
                "rng_unchanged_full_sequence": rng_before == _rng_digest(),
                "landscape_unchanged_full_sequence": land_before == _land_digest(mod.land),
                "K_unchanged_full_sequence": k_before == k_after,
                "births_empty": list(mod.comm[0].n_births) == [],
                "deaths_empty": list(mod.comm[0].n_deaths) == [],
                "ages_zero": all(int(ind.age) == 0 for ind in mod.comm[0].values()),
                "model_walk_called": False,
                "autonomous_movement_called": False,
                "autonomous_population_dynamics_called": False,
                "autonomous_ageing_called": False,
                "population_proxy_consumed_as_count": False,
                "coordinate_interpolation_performed": False,
                "first_failed_transition": next(
                    (x for x in transition_rows if not x["pass"]), None
                ),
                "pass": bool(passed),
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
    total_transition_passes = sum(int(r.get("transition_pass_count", 0)) for r in records)
    expected_total = transition_count * 4
    return {
        "stage": STAGE,
        "status":
            "R442_CARRIER_FULL_SEQUENCE_BOUNDED_REPLAY_VALIDATED"
            if pass_count == 4 and total_transition_passes == expected_total
            else BLOCKED,
        "job_id": job_id,
        "branch_selection": branch["selection"],
        "replicate_count": 4,
        "replicate_pass_count": pass_count,
        "canonical_state_count_per_replicate": len(states),
        "transition_count_per_replicate": transition_count,
        "expected_transition_count_all_replicates": expected_total,
        "transition_pass_count_all_replicates": total_transition_passes,
        "model_walk_call_count": 0,
        "autonomous_movement_call_count": 0,
        "autonomous_population_dynamics_call_count": 0,
        "autonomous_ageing_call_count": 0,
        "records": records,
    }


def _prepare_j21_dynamic(root: Path) -> tuple[dict[str, list[np.ndarray]], dict[str, str]]:
    from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import (
        _j21_dynamic_payload_authority,
    )

    initial_manifest = load(root / R436_J21_MANIFEST)
    payload, dynamic_by_name, _, bound_dynamic_sidecars = (
        _j21_dynamic_payload_authority(root, initial_manifest)
    )
    if payload.get("pass") is not True or len(dynamic_by_name) != 147:
        raise RuntimeError("J21 dynamic authority invalid")
    return dynamic_by_name, bound_dynamic_sidecars


def _run_j21_full_sequence(root: Path, native: dict[str, Any]) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import (
        _r437_j21_bound_param_path,
    )
    rows = _native_rows(native, J21)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_J21_ROWS"}

    dynamic_by_name, bound_dynamic_sidecars = _prepare_j21_dynamic(root)
    names = list(dynamic_by_name.keys())
    transition_count = 8
    records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(_import_params(_r437_j21_bound_param_path(root, rep)))
            layers = params["landscape"]["layers"]
            for lname in bound_dynamic_sidecars:
                if lname not in layers:
                    raise RuntimeError(f"missing sidecar-bound layer {lname}")
                del layers[lname]
            if set(names) != (set(layers.keys()) - {"R437_CONSTRUCTION_SUPPORT"}):
                raise RuntimeError("J21 native layer set mismatch")
            for lname in names:
                layers[lname].pop("change", None)

            params["model"]["T"] = 8
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R442_{J21}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )
            spp = mod.comm[0]
            layer_map = {lyr.name: lyr for lyr in mod.land.values()}

            initial_exact = sum(
                np.array_equal(
                    np.asarray(layer_map[lname].rast),
                    np.asarray(dynamic_by_name[lname][0]),
                )
                for lname in names
            )
            seed_before = mod.seed
            rng_before = _rng_digest()
            support = next(
                lyr for lyr in mod.land.values()
                if lyr.name == "R437_CONSTRUCTION_SUPPORT"
            )
            support_before = _array_digest(np.asarray(support.rast))
            coords_before = _coords_from_spp(spp).copy()
            k_before = _array_digest(np.asarray(spp.K)) if spp.K is not None else None

            transition_rows = []
            for ti in range(transition_count):
                clock = _advance_authorized_clock_expected(
                    mod, expected_before_t=ti - 1
                )
                for lname in names:
                    layer_map[lname].rast = np.asarray(
                        dynamic_by_name[lname][ti + 1]
                    ).copy()
                exact_count = sum(
                    np.array_equal(
                        np.asarray(layer_map[lname].rast),
                        np.asarray(dynamic_by_name[lname][ti + 1]),
                    )
                    for lname in names
                )
                clock_exact = (
                    mod.t == ti and mod.comm.t == ti and spp.t == ti
                )
                invariant = all([
                    clock.get("pass") is True,
                    clock_exact,
                    exact_count == 147,
                    _array_digest(np.asarray(support.rast)) == support_before,
                    _coords_exact(_coords_from_spp(spp), coords_before),
                    (_array_digest(np.asarray(spp.K)) if spp.K is not None else None)
                        == k_before,
                    list(spp.n_births) == [],
                    list(spp.n_deaths) == [],
                    all(int(ind.age) == 0 for ind in spp.values()),
                    mod.land._changer is None,
                ])
                transition_rows.append({
                    "transition_index": ti,
                    "exact_native_layer_target_count": exact_count,
                    "clock_exact": clock_exact,
                    "invariants_exact": invariant,
                    "pass": bool(invariant),
                })

            final_exact = sum(
                np.array_equal(
                    np.asarray(layer_map[lname].rast),
                    np.asarray(dynamic_by_name[lname][-1]),
                )
                for lname in names
            )
            pass_count = sum(bool(x["pass"]) for x in transition_rows)
            passed = all([
                initial_exact == 147,
                pass_count == 8,
                final_exact == 147,
                mod.seed == seed_before == seed,
                rng_before == _rng_digest(),
                _array_digest(np.asarray(support.rast)) == support_before,
                _coords_exact(_coords_from_spp(spp), coords_before),
                (_array_digest(np.asarray(spp.K)) if spp.K is not None else None)
                    == k_before,
                list(spp.n_births) == [],
                list(spp.n_deaths) == [],
                all(int(ind.age) == 0 for ind in spp.values()),
                mod.t == 7 and mod.comm.t == 7 and spp.t == 7,
                mod.land._changer is None,
            ])

            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "canonical_state_count": 9,
                "transition_count": 8,
                "transition_pass_count": pass_count,
                "initial_exact_native_layer_count": initial_exact,
                "final_exact_native_layer_count": final_exact,
                "rng_unchanged_full_sequence": rng_before == _rng_digest(),
                "construction_support_unchanged":
                    _array_digest(np.asarray(support.rast)) == support_before,
                "carrier_coords_unchanged":
                    _coords_exact(_coords_from_spp(spp), coords_before),
                "K_unchanged":
                    (_array_digest(np.asarray(spp.K)) if spp.K is not None else None)
                    == k_before,
                "dynamic_sidecar_count": 4,
                "dynamic_sidecars_bound_as_layers": False,
                "landscape_changer_absent": mod.land._changer is None,
                "model_walk_called": False,
                "autonomous_movement_called": False,
                "autonomous_population_dynamics_called": False,
                "autonomous_ageing_called": False,
                "first_failed_transition": next(
                    (x for x in transition_rows if not x["pass"]), None
                ),
                "pass": bool(passed),
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
    total_transition_passes = sum(int(r.get("transition_pass_count", 0)) for r in records)
    return {
        "stage": STAGE,
        "status":
            "R442_J21_FULL_SEQUENCE_BOUNDED_LAYER_REPLAY_VALIDATED"
            if pass_count == 4 and total_transition_passes == 32
            else BLOCKED,
        "job_id": J21,
        "replicate_count": 4,
        "replicate_pass_count": pass_count,
        "canonical_state_count_per_replicate": 9,
        "transition_count_per_replicate": 8,
        "expected_transition_count_all_replicates": 32,
        "transition_pass_count_all_replicates": total_transition_passes,
        "native_layer_count": 147,
        "dynamic_sidecar_count": 4,
        "model_walk_call_count": 0,
        "landscape_changer_call_count": 0,
        "autonomous_movement_call_count": 0,
        "autonomous_population_dynamics_call_count": 0,
        "autonomous_ageing_call_count": 0,
        "records": records,
    }


def _authorization(
    j14: dict[str, Any],
    j18: dict[str, Any],
    j21: dict[str, Any],
) -> dict[str, Any]:
    checks = {
        "j14_full_sequence_bounded_replay":
            j14.get("replicate_pass_count") == 4
            and j14.get("transition_pass_count_all_replicates") == 560,
        "j18_full_sequence_bounded_replay":
            j18.get("replicate_pass_count") == 4
            and j18.get("transition_pass_count_all_replicates") == 56,
        "j21_full_sequence_bounded_replay":
            j21.get("replicate_pass_count") == 4
            and j21.get("transition_pass_count_all_replicates") == 32,
        "no_default_walk":
            j14.get("model_walk_call_count") == 0
            and j18.get("model_walk_call_count") == 0
            and j21.get("model_walk_call_count") == 0,
        "zero_autonomous_movement":
            j14.get("autonomous_movement_call_count") == 0
            and j18.get("autonomous_movement_call_count") == 0
            and j21.get("autonomous_movement_call_count") == 0,
        "zero_autonomous_population_dynamics":
            j14.get("autonomous_population_dynamics_call_count") == 0
            and j18.get("autonomous_population_dynamics_call_count") == 0
            and j21.get("autonomous_population_dynamics_call_count") == 0,
        "zero_autonomous_ageing":
            j14.get("autonomous_ageing_call_count") == 0
            and j18.get("autonomous_ageing_call_count") == 0
            and j21.get("autonomous_ageing_call_count") == 0,
    }
    ok = all(checks.values())
    return {
        "stage": STAGE,
        "status":
            "R442_ARCANA_DOMAIN_SPECIFIC_PRODUCTION_EXECUTION_QUEUE_AUTHORIZED"
            if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "production_execution_queue_authorized": bool(ok),
        "authorized_queue":
            "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "default_geonomics_queue_authorized": False,
        "authorization_scope": {
            "J14": "exact anchor carrier replay; no autonomous dynamics",
            "J18": "exact anchor carrier replay; no autonomous dynamics",
            "J21": "exact native-layer anchor replay; four sidecars external",
        },
        "bounded_validation_scope": {
            "J14": "first frozen branch, all 140 transitions, four seeds",
            "J18": "first frozen branch, all 14 transitions, four seeds",
            "J21": "all 8 transitions, all 147 native layers, four seeds",
        },
        "scientific_readout_authority_closed": False,
        "scientific_execution_authorized": False,
        "geonomics_execution_ready": False,
        "reason_not_ready":
            "SCIENTIFIC_READOUT_METRICS_AND_ADJUDICATION_SCHEMA_NOT_YET_FROZEN",
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R441)
    parent_seal = load(root / R441_SEAL)
    native = load(root / R436_NATIVE)

    j14 = _run_carrier_full_sequence(
        root, native, J14, _j14_first_branch_full(root)
    )
    j18 = _run_carrier_full_sequence(
        root, native, J18, _j18_first_branch_full(root)
    )
    j21 = _run_j21_full_sequence(root, native)
    auth = _authorization(j14, j18, j21)

    write(root / OUT / "R4_42_J14_MULTI_TRANSITION_BOUNDED_REPLAY.json", j14)
    write(root / OUT / "R4_42_J18_MULTI_TRANSITION_BOUNDED_REPLAY.json", j18)
    write(root / OUT / "R4_42_J21_MULTI_TRANSITION_BOUNDED_REPLAY.json", j21)
    write(root / OUT / "R4_42_PRODUCTION_EXECUTION_QUEUE_AUTHORIZATION.json", auth)

    checks = {
        "parent_r441_complete_28_28":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 28
            and parent.get("checks_failed") == 0,
        "parent_r441_sealed_21_21":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 21,
        "parent_next_action_r442":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R442_BOUNDED_FULL_SEQUENCE_REPLAY_BEFORE_PRODUCTION_QUEUE_AUTHORIZATION",
        "j14_four_full_sequences_pass":
            j14.get("replicate_pass_count") == 4,
        "j14_exact_560_transitions":
            j14.get("transition_pass_count_all_replicates") == 560,
        "j18_four_full_sequences_pass":
            j18.get("replicate_pass_count") == 4,
        "j18_exact_56_transitions":
            j18.get("transition_pass_count_all_replicates") == 56,
        "j21_four_full_sequences_pass":
            j21.get("replicate_pass_count") == 4,
        "j21_exact_32_transitions":
            j21.get("transition_pass_count_all_replicates") == 32,
        "exact_648_bounded_transition_validations":
            (
                j14.get("transition_pass_count_all_replicates", 0)
                + j18.get("transition_pass_count_all_replicates", 0)
                + j21.get("transition_pass_count_all_replicates", 0)
            ) == 648,
        "production_execution_queue_authorized":
            auth.get("production_execution_queue_authorized") is True,
        "authorized_queue_is_arcana_exact_replay":
            auth.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "default_geonomics_queue_still_forbidden":
            auth.get("default_geonomics_queue_authorized") is False,
        "scientific_readout_authority_not_closed":
            auth.get("scientific_readout_authority_closed") is False,
        "scientific_execution_not_authorized":
            auth.get("scientific_execution_authorized") is False,
        "geonomics_execution_not_ready":
            auth.get("geonomics_execution_ready") is False,
        "bounded_replay_not_scientific_evidence":
            cfg.get("bounded_replay_is_scientific_evidence") is False,
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
        "j14_replicate_pass_count": j14.get("replicate_pass_count"),
        "j14_transition_pass_count": j14.get("transition_pass_count_all_replicates"),
        "j18_replicate_pass_count": j18.get("replicate_pass_count"),
        "j18_transition_pass_count": j18.get("transition_pass_count_all_replicates"),
        "j21_replicate_pass_count": j21.get("replicate_pass_count"),
        "j21_transition_pass_count": j21.get("transition_pass_count_all_replicates"),
        "bounded_transition_validation_count": 648 if ok else (
            j14.get("transition_pass_count_all_replicates", 0)
            + j18.get("transition_pass_count_all_replicates", 0)
            + j21.get("transition_pass_count_all_replicates", 0)
        ),
        "production_execution_queue_authorized": bool(ok),
        "authorized_queue":
            "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE" if ok else None,
        "default_geonomics_queue_authorized": False,
        "scientific_readout_authority_closed": False,
        "scientific_execution_authorized": False,
        "geonomics_execution_ready": False,
        "bounded_replay_is_scientific_evidence": False,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R442_MULTI_TRANSITION_REPLAY_OR_QUEUE_AUTHORIZATION",
    }
    write(root / OUT / "R4_42_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_42_INTEGRATED_AUDIT.json")
    auth = load(root / OUT / "R4_42_PRODUCTION_EXECUTION_QUEUE_AUTHORIZATION.json")

    checks = {
        "r442_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "j14_4_and_560":
            a.get("j14_replicate_pass_count") == 4
            and a.get("j14_transition_pass_count") == 560,
        "j18_4_and_56":
            a.get("j18_replicate_pass_count") == 4
            and a.get("j18_transition_pass_count") == 56,
        "j21_4_and_32":
            a.get("j21_replicate_pass_count") == 4
            and a.get("j21_transition_pass_count") == 32,
        "exact_648_bounded_transitions":
            a.get("bounded_transition_validation_count") == 648,
        "production_queue_authorized":
            a.get("production_execution_queue_authorized") is True,
        "arcana_queue_only":
            a.get("authorized_queue")
            == "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
        "default_queue_forbidden":
            a.get("default_geonomics_queue_authorized") is False,
        "readout_authority_pending":
            a.get("scientific_readout_authority_closed") is False,
        "scientific_execution_not_authorized":
            a.get("scientific_execution_authorized") is False,
        "execution_not_ready":
            a.get("geonomics_execution_ready") is False,
        "bounded_replay_not_scientific":
            a.get("bounded_replay_is_scientific_evidence") is False,
        "authorization_reason_exact":
            auth.get("reason_not_ready")
            == "SCIENTIFIC_READOUT_METRICS_AND_ADJUDICATION_SCHEMA_NOT_YET_FROZEN",
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
        "next_r443":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())
    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
            "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "j14_transition_validations": a.get("j14_transition_pass_count"),
            "j18_transition_validations": a.get("j18_transition_pass_count"),
            "j21_transition_validations": a.get("j21_transition_pass_count"),
            "bounded_transition_validation_count":
                a.get("bounded_transition_validation_count"),
            "production_execution_queue_authorized":
                a.get("production_execution_queue_authorized"),
            "authorized_queue": a.get("authorized_queue"),
            "default_geonomics_queue_authorized": False,
            "scientific_readout_authority_closed": False,
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
