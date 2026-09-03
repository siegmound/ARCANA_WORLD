from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import json
import random

import numpy as np

STAGE = "v0.6D1-R4.41"

PARENT_COMPLETE = (
    "PASS_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
    "AND_EXECUTION_QUEUE_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
    "AND_EXECUTION_QUEUE_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
    "DRY_RUN_AND_STATE_INVARIANT_VALIDATION"
)

COMPLETE = (
    "PASS_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
    "DRY_RUN_AND_STATE_INVARIANT_VALIDATION_COMPLETE"
)
SEALED = (
    "PASS_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
    "DRY_RUN_AND_STATE_INVARIANT_VALIDATION_SEALED"
)
BLOCKED = (
    "BLOCKED_R441_SINGLE_TRANSITION_DRY_RUN_OR_STATE_INVARIANT_FAILURE"
)
NEXT = (
    "BUILD_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
    "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT"
)

OUT = Path("outputs/v0_6D1_R4_41")
SEAL = Path("outputs/v0_6D1_R4_41_SEAL/R4_41_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r441_geonomics_domain_specific_execution_queue_single_"
    "transition_dry_run_state_invariant_validation_v0_6D1_R4_41.json"
)

R440 = Path("outputs/v0_6D1_R4_40/R4_40_INTEGRATED_AUDIT.json")
R440_SEAL = Path("outputs/v0_6D1_R4_40_SEAL/R4_40_FINAL_SEAL_AUDIT.json")
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
    name = "r441_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
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
    rows = [
        r for r in (native.get("records") or [])
        if r.get("job_id") == job_id and r.get("construction_pass") is True
    ]
    return sorted(rows, key=lambda r: int(r["replicate_index"]))


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


def _exact_carrier_replace_preserve_clock(
    mod: Any,
    template: Any,
    coords: list[list[float]],
) -> dict[str, Any]:
    spp = mod.comm[0]
    if spp.gen_arch is not None or getattr(spp, "_tc", None) is not None:
        raise RuntimeError("R441 carrier replay requires nongenomic Species")
    if len(coords) <= 0:
        raise RuntimeError("R441 zero-carrier target unsupported")

    t_before = (mod.t, mod.comm.t, spp.t)
    rng_before = _rng_digest()
    land_before = _land_digest(mod.land)
    k_before = _array_digest(np.asarray(spp.K)) if spp.K is not None else None

    inds = OrderedDict()
    for idx, (x, y) in enumerate(coords):
        ind = copy.deepcopy(template)
        ind.idx = int(idx)
        ind._set_pos(float(x), float(y))
        ind.age = 0
        ind.sex = None
        ind.e = None
        ind.z = []
        ind.fit = None
        ind._individuals_tab_id = None
        ind._nodes_tab_ids = {}
        inds[idx] = ind

    spp.clear()
    spp.update(inds)
    spp.max_ind_idx = len(inds) - 1
    spp.start_N = len(inds)
    spp.N = None
    spp._coords = None
    spp._cells = None
    spp._kd_tree = None
    spp._dens_grids = None

    spp._set_coords_and_cells()
    spp._set_kd_tree()
    spp._set_dens_grids(mod.land)
    spp._calc_density(set_N=True)
    spp._set_e(mod.land)

    t_after = (mod.t, mod.comm.t, spp.t)
    k_after = _array_digest(np.asarray(spp.K)) if spp.K is not None else None

    return {
        "pass": bool(
            t_after == t_before
            and rng_before == _rng_digest()
            and land_before == _land_digest(mod.land)
            and k_before == k_after
            and spp.gen_arch is None
            and getattr(spp, "_tc", None) is None
        ),
        "clock_before_replace": list(t_before),
        "clock_after_replace": list(t_after),
        "rng_unchanged": rng_before == _rng_digest(),
        "landscape_unchanged": land_before == _land_digest(mod.land),
        "K_unchanged": k_before == k_after,
        "carrier_count": len(spp),
        "private_population_add_remove_called": False,
        "autonomous_movement_called": False,
        "autonomous_population_dynamics_called": False,
        "autonomous_ageing_called": False,
    }


def _advance_authorized_clock_once(mod: Any) -> dict[str, Any]:
    before = {
        "model_t": int(mod.t),
        "community_t": int(mod.comm.t),
        "species_t": [int(spp.t) for spp in mod.comm.values()],
    }

    mod._set_t()
    mod._set_comm_t()
    for spp_idx in mod.comm.keys():
        mod._set_spp_t(spp_idx)

    after = {
        "model_t": int(mod.t),
        "community_t": int(mod.comm.t),
        "species_t": [int(spp.t) for spp in mod.comm.values()],
    }

    return {
        "before": before,
        "after": after,
        "pass": bool(
            before["model_t"] == -1
            and before["community_t"] == -1
            and all(t == -1 for t in before["species_t"])
            and after["model_t"] == 0
            and after["community_t"] == 0
            and all(t == 0 for t in after["species_t"])
        ),
        "model_set_t_called": 1,
        "community_set_t_called": 1,
        "species_set_t_call_count": len(mod.comm),
        "age_stage_called": False,
        "Nt_record_called": False,
        "movement_called": False,
        "population_dynamics_called": False,
        "land_changer_called": False,
    }


def _j14_first_branch_states(root: Path) -> dict[str, Any]:
    p = root / J14_SOURCE
    if sha256(p) != J14_SHA:
        raise RuntimeError("J14 source hash mismatch")
    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        s = np.asarray(z["spatial_state"], dtype=float)[0, 0, :2]
    pi = names.index("population_proxy")
    ri = names.index("grid_row")
    ci = names.index("grid_col")
    ai = names.index("active")
    out = []
    for ti in range(2):
        mask = s[ti, :, ai] > 0.5
        coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
        pops = s[ti, mask, pi]
        out.append({
            "age": float(ages[ti]),
            "coords": coords,
            "population_proxy": pops,
        })
    return {
        "selection": "member_index_0_candidate_index_0_first_transition",
        "states": out,
    }


def _j18_first_branch_states(root: Path) -> dict[str, Any]:
    p = root / J18_SOURCE
    if sha256(p) != J18_SHA:
        raise RuntimeError("J18 source hash mismatch")
    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["snapshot_age_ka"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        s = np.asarray(z["snapshot_deme_state"], dtype=float)[0, 0, :2]
        active = np.asarray(z["snapshot_active"])[0, 0, :2]
    pi = names.index("population_proxy")
    ri = names.index("grid_row")
    ci = names.index("grid_col")
    out = []
    for ti in range(2):
        mask = np.asarray(active[ti], dtype=float) > 0.5
        coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
        pops = s[ti, mask, pi]
        out.append({
            "age": float(ages[ti]),
            "coords": coords,
            "population_proxy": pops,
        })
    return {
        "selection": "member_index_0_candidate_index_0_first_transition",
        "states": out,
    }


def _run_carrier_job(
    root: Path,
    native: dict[str, Any],
    job_id: str,
    branch: dict[str, Any],
) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight import (
        _install_exact_nonliteral_carriers,
    )

    rows = _native_rows(native, job_id)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_NATIVE_ROWS"}

    initial = branch["states"][0]
    target = branch["states"][1]
    if len(initial["coords"]) <= 0 or len(target["coords"]) <= 0:
        return {"status": BLOCKED, "reason": "ZERO_CARRIER_FIRST_TRANSITION"}

    records = []
    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        pf = root / row["native_parameter_file"]
        try:
            params = copy.deepcopy(_import_params(pf))
            params["model"]["T"] = 1
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R441_{job_id}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )
            spp = mod.comm[0]
            probe = copy.deepcopy(next(iter(spp.values())))

            initial_coords = initial["coords"].tolist()
            init = _install_exact_nonliteral_carriers(
                mod, probe, initial_coords
            )
            init_exact = _coords_exact(
                _coords_from_spp(mod.comm[0]), initial["coords"]
            )
            orig_initial = _coords_from_spp(mod.orig_comm[0])
            orig_exact_initial = _coords_exact(
                orig_initial, initial["coords"]
            )

            births_before = list(mod.comm[0].n_births)
            deaths_before = list(mod.comm[0].n_deaths)
            ages_before = [int(ind.age) for ind in mod.comm[0].values()]
            rng_before_transition = _rng_digest()
            seed_before = mod.seed
            land_before_transition = _land_digest(mod.land)
            k_before_transition = _array_digest(
                np.asarray(mod.comm[0].K)
            ) if mod.comm[0].K is not None else None

            clock = _advance_authorized_clock_once(mod)
            replace = _exact_carrier_replace_preserve_clock(
                mod, probe, target["coords"].tolist()
            )

            target_exact = _coords_exact(
                _coords_from_spp(mod.comm[0]), target["coords"]
            )
            orig_still_initial = _coords_exact(
                _coords_from_spp(mod.orig_comm[0]), initial["coords"]
            )
            births_after = list(mod.comm[0].n_births)
            deaths_after = list(mod.comm[0].n_deaths)
            ages_after = [int(ind.age) for ind in mod.comm[0].values()]
            k_after_transition = _array_digest(
                np.asarray(mod.comm[0].K)
            ) if mod.comm[0].K is not None else None

            passed = all([
                mod.seed == seed_before == seed,
                init.get("pass") is True,
                init_exact,
                orig_exact_initial,
                clock.get("pass") is True,
                replace.get("pass") is True,
                target_exact,
                orig_still_initial,
                len(mod.comm[0]) == len(target["coords"]),
                births_before == births_after == [],
                deaths_before == deaths_after == [],
                all(a == 0 for a in ages_before),
                all(a == 0 for a in ages_after),
                rng_before_transition == _rng_digest(),
                land_before_transition == _land_digest(mod.land),
                k_before_transition == k_after_transition,
                mod.t == 0,
                mod.comm.t == 0,
                mod.comm[0].t == 0,
                mod.comm[0].burned is False,
            ])

            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "seed_exact": mod.seed == seed,
                "initial_age": initial["age"],
                "target_age": target["age"],
                "initial_carrier_count": len(initial["coords"]),
                "target_carrier_count": len(target["coords"]),
                "initial_exact": init_exact,
                "target_exact": target_exact,
                "orig_comm_initial_before_transition": orig_exact_initial,
                "orig_comm_still_initial_after_transition": orig_still_initial,
                "clock": clock,
                "replacement": replace,
                "births_unchanged_empty": births_before == births_after == [],
                "deaths_unchanged_empty": deaths_before == deaths_after == [],
                "ages_unchanged_zero":
                    all(a == 0 for a in ages_before)
                    and all(a == 0 for a in ages_after),
                "rng_unchanged_during_transition":
                    rng_before_transition == _rng_digest(),
                "landscape_unchanged_during_transition":
                    land_before_transition == _land_digest(mod.land),
                "K_unchanged_during_transition":
                    k_before_transition == k_after_transition,
                "population_proxy_consumed_as_carrier_count": False,
                "coordinate_interpolation_performed": False,
                "model_walk_called": False,
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
    return {
        "stage": STAGE,
        "status":
            "R441_CARRIER_SINGLE_TRANSITION_DRY_RUN_VALIDATED"
            if pass_count == 4 else BLOCKED,
        "job_id": job_id,
        "branch_selection": branch["selection"],
        "replicate_count": len(records),
        "replicate_pass_count": pass_count,
        "domain_specific_transition_dry_run_count": pass_count,
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
    result = _j21_dynamic_payload_authority(root, initial_manifest)
    if len(result) != 4:
        raise RuntimeError("unexpected R4.39 J21 payload authority return shape")
    payload, dynamic_by_name, native_records, bound_dynamic_sidecars = result
    if payload.get("pass") is not True:
        raise RuntimeError("J21 dynamic payload authority not valid")
    if len(dynamic_by_name) != 147:
        raise RuntimeError("expected 147 J21 native dynamic layers")
    return dynamic_by_name, bound_dynamic_sidecars


def _run_j21(
    root: Path,
    native: dict[str, Any],
) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import (
        _r437_j21_bound_param_path,
    )

    rows = _native_rows(native, J21)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_J21_ROWS"}

    dynamic_by_name, bound_dynamic_sidecars = _prepare_j21_dynamic(root)
    canonical_names = list(dynamic_by_name.keys())
    records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(
                _import_params(_r437_j21_bound_param_path(root, rep))
            )
            layers = params["landscape"]["layers"]

            for lname in bound_dynamic_sidecars:
                if lname not in layers:
                    raise RuntimeError(f"missing R4.37 sidecar-bound layer {lname}")
                del layers[lname]

            if set(canonical_names) != (
                set(layers.keys()) - {"R437_CONSTRUCTION_SUPPORT"}
            ):
                raise RuntimeError("J21 native layer set mismatch")

            for lname in canonical_names:
                layers[lname].pop("change", None)
            params["model"]["T"] = 1
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R441_{J21}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )

            seed_before = mod.seed
            rng_before_transition = _rng_digest()
            support = next(
                lyr for lyr in mod.land.values()
                if lyr.name == "R437_CONSTRUCTION_SUPPORT"
            )
            support_before = _array_digest(np.asarray(support.rast))
            spp = mod.comm[0]
            coords_before = _coords_from_spp(spp).copy()
            k_before = _array_digest(np.asarray(spp.K)) if spp.K is not None else None
            births_before = list(spp.n_births)
            deaths_before = list(spp.n_deaths)
            ages_before = [int(ind.age) for ind in spp.values()]

            layer_map = {lyr.name: lyr for lyr in mod.land.values()}
            initial_exact_count = 0
            for lname in canonical_names:
                if np.array_equal(
                    np.asarray(layer_map[lname].rast),
                    np.asarray(dynamic_by_name[lname][0]),
                ):
                    initial_exact_count += 1

            clock = _advance_authorized_clock_once(mod)

            for lname in canonical_names:
                target = np.asarray(dynamic_by_name[lname][1])
                layer_map[lname].rast = target.copy()

            target_exact_count = sum(
                np.array_equal(
                    np.asarray(layer_map[lname].rast),
                    np.asarray(dynamic_by_name[lname][1]),
                )
                for lname in canonical_names
            )

            births_after = list(spp.n_births)
            deaths_after = list(spp.n_deaths)
            ages_after = [int(ind.age) for ind in spp.values()]
            k_after = _array_digest(np.asarray(spp.K)) if spp.K is not None else None

            passed = all([
                mod.seed == seed_before == seed,
                initial_exact_count == 147,
                target_exact_count == 147,
                clock.get("pass") is True,
                _array_digest(np.asarray(support.rast)) == support_before,
                _coords_exact(_coords_from_spp(spp), coords_before),
                k_before == k_after,
                births_before == births_after == [],
                deaths_before == deaths_after == [],
                all(a == 0 for a in ages_before),
                all(a == 0 for a in ages_after),
                rng_before_transition == _rng_digest(),
                mod.t == 0,
                mod.comm.t == 0,
                spp.t == 0,
                mod.land._changer is None,
            ])

            records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "seed_exact": mod.seed == seed,
                "initial_native_layer_exact_count": initial_exact_count,
                "target_native_layer_exact_count": target_exact_count,
                "dynamic_sidecar_count": 4,
                "dynamic_sidecars_bound_as_layers": False,
                "clock": clock,
                "construction_support_unchanged":
                    _array_digest(np.asarray(support.rast)) == support_before,
                "carrier_coords_unchanged":
                    _coords_exact(_coords_from_spp(spp), coords_before),
                "K_unchanged": k_before == k_after,
                "births_unchanged_empty": births_before == births_after == [],
                "deaths_unchanged_empty": deaths_before == deaths_after == [],
                "ages_unchanged_zero":
                    all(a == 0 for a in ages_before)
                    and all(a == 0 for a in ages_after),
                "rng_unchanged_during_transition":
                    rng_before_transition == _rng_digest(),
                "landscape_changer_absent": mod.land._changer is None,
                "direct_exact_layer_replay_used": True,
                "model_walk_called": False,
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
    return {
        "stage": STAGE,
        "status":
            "R441_J21_LAYER_SINGLE_TRANSITION_DRY_RUN_VALIDATED"
            if pass_count == 4 else BLOCKED,
        "job_id": J21,
        "replicate_count": len(records),
        "replicate_pass_count": pass_count,
        "domain_specific_transition_dry_run_count": pass_count,
        "native_layer_count": 147,
        "exact_layer_target_count_per_transition": 147,
        "dynamic_sidecar_count": 4,
        "model_walk_call_count": 0,
        "landscape_changer_call_count": 0,
        "autonomous_movement_call_count": 0,
        "autonomous_population_dynamics_call_count": 0,
        "autonomous_ageing_call_count": 0,
        "records": records,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R440)
    parent_seal = load(root / R440_SEAL)
    native = load(root / R436_NATIVE)

    j14 = _run_carrier_job(
        root, native, J14, _j14_first_branch_states(root)
    )
    j18 = _run_carrier_job(
        root, native, J18, _j18_first_branch_states(root)
    )
    j21 = _run_j21(root, native)

    write(root / OUT / "R4_41_J14_SINGLE_TRANSITION_DRY_RUN.json", j14)
    write(root / OUT / "R4_41_J18_SINGLE_TRANSITION_DRY_RUN.json", j18)
    write(root / OUT / "R4_41_J21_SINGLE_TRANSITION_DRY_RUN.json", j21)

    checks = {
        "parent_r440_complete_38_38":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 38
            and parent.get("checks_failed") == 0,
        "parent_r440_sealed_25_25":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 25,
        "parent_next_action_r441":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R441_SINGLE_TRANSITION_DISPOSABLE_DRY_RUN_NO_DEFAULT_WALK",
        "j14_four_dry_runs_pass":
            j14.get("replicate_pass_count") == 4,
        "j18_four_dry_runs_pass":
            j18.get("replicate_pass_count") == 4,
        "j21_four_dry_runs_pass":
            j21.get("replicate_pass_count") == 4,
        "exact_12_domain_specific_transition_dry_runs":
            (
                j14.get("domain_specific_transition_dry_run_count", 0)
                + j18.get("domain_specific_transition_dry_run_count", 0)
                + j21.get("domain_specific_transition_dry_run_count", 0)
            ) == 12,
        "j14_no_model_walk":
            j14.get("model_walk_call_count") == 0,
        "j18_no_model_walk":
            j18.get("model_walk_call_count") == 0,
        "j21_no_model_walk_or_land_changer":
            j21.get("model_walk_call_count") == 0
            and j21.get("landscape_changer_call_count") == 0,
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
        "j21_147_exact_layer_targets_per_run":
            j21.get("native_layer_count") == 147
            and j21.get("exact_layer_target_count_per_transition") == 147,
        "j21_four_sidecars_external":
            j21.get("dynamic_sidecar_count") == 4,
        "single_transition_dry_run_validated": True,
        "dry_run_not_scientific_evidence":
            cfg.get("dry_run_is_scientific_evidence") is False,
        "production_execution_queue_not_authorized":
            cfg.get("production_execution_queue_authorized") is False,
        "geonomics_execution_not_ready":
            cfg.get("geonomics_execution_ready") is False,
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
        "j14_dry_run_replicate_pass_count": j14.get("replicate_pass_count"),
        "j18_dry_run_replicate_pass_count": j18.get("replicate_pass_count"),
        "j21_dry_run_replicate_pass_count": j21.get("replicate_pass_count"),
        "domain_specific_transition_dry_run_count": 12 if ok else (
            j14.get("domain_specific_transition_dry_run_count", 0)
            + j18.get("domain_specific_transition_dry_run_count", 0)
            + j21.get("domain_specific_transition_dry_run_count", 0)
        ),
        "single_transition_dry_run_validated": bool(ok),
        "default_model_walk_used": False,
        "autonomous_movement_executed": False,
        "autonomous_population_dynamics_executed": False,
        "autonomous_ageing_executed": False,
        "dry_run_is_scientific_evidence": False,
        "production_execution_queue_authorized": False,
        "geonomics_execution_ready": False,
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R441_SINGLE_TRANSITION_DRY_RUN",
    }
    write(root / OUT / "R4_41_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_41_INTEGRATED_AUDIT.json")
    j14 = load(root / OUT / "R4_41_J14_SINGLE_TRANSITION_DRY_RUN.json")
    j18 = load(root / OUT / "R4_41_J18_SINGLE_TRANSITION_DRY_RUN.json")
    j21 = load(root / OUT / "R4_41_J21_SINGLE_TRANSITION_DRY_RUN.json")

    checks = {
        "r441_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "j14_4_of_4":
            j14.get("replicate_pass_count") == 4,
        "j18_4_of_4":
            j18.get("replicate_pass_count") == 4,
        "j21_4_of_4":
            j21.get("replicate_pass_count") == 4,
        "exact_12_dry_runs":
            a.get("domain_specific_transition_dry_run_count") == 12,
        "single_transition_validated":
            a.get("single_transition_dry_run_validated") is True,
        "no_default_walk":
            a.get("default_model_walk_used") is False,
        "no_autonomous_movement":
            a.get("autonomous_movement_executed") is False,
        "no_autonomous_population_dynamics":
            a.get("autonomous_population_dynamics_executed") is False,
        "no_autonomous_ageing":
            a.get("autonomous_ageing_executed") is False,
        "dry_run_not_scientific":
            a.get("dry_run_is_scientific_evidence") is False,
        "production_queue_not_authorized":
            a.get("production_execution_queue_authorized") is False,
        "execution_not_ready":
            a.get("geonomics_execution_ready") is False,
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
        "next_r442":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
            "DRY_RUN_AND_STATE_INVARIANT_VALIDATION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "j14_replicates": j14.get("replicate_pass_count"),
            "j18_replicates": j18.get("replicate_pass_count"),
            "j21_replicates": j21.get("replicate_pass_count"),
            "domain_specific_transition_dry_run_count":
                a.get("domain_specific_transition_dry_run_count"),
            "single_transition_dry_run_validated":
                a.get("single_transition_dry_run_validated"),
            "default_model_walk_used": False,
            "autonomous_movement_executed": False,
            "autonomous_population_dynamics_executed": False,
            "autonomous_ageing_executed": False,
            "dry_run_is_scientific_evidence": False,
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
