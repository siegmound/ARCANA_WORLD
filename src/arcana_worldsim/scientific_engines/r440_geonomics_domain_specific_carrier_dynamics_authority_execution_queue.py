from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import inspect
import json

import numpy as np

STAGE = "v0.6D1-R4.40"

PARENT_COMPLETE = (
    "PASS_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_"
    "AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_"
    "AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT_SEALED"
)
PARENT_R5 = "PASS_R439_R5_BOUNDED_PREFLIGHT_AND_R439_RESEAL_VERIFIED"
PARENT_NEXT = (
    "BUILD_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
    "AND_EXECUTION_QUEUE_PREFLIGHT"
)

COMPLETE = (
    "PASS_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
    "AND_EXECUTION_QUEUE_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
    "AND_EXECUTION_QUEUE_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R440_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_OR_EXECUTION_"
    "QUEUE_PREFLIGHT_FAILURE"
)
NEXT = (
    "BUILD_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
    "DRY_RUN_AND_STATE_INVARIANT_VALIDATION"
)

OUT = Path("outputs/v0_6D1_R4_40")
SEAL = Path("outputs/v0_6D1_R4_40_SEAL/R4_40_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r440_geonomics_domain_specific_carrier_dynamics_"
    "authority_execution_queue_preflight_v0_6D1_R4_40.json"
)

R439 = Path("outputs/v0_6D1_R4_39/R4_39_INTEGRATED_AUDIT.json")
R439_SEAL = Path("outputs/v0_6D1_R4_39_SEAL/R4_39_FINAL_SEAL_AUDIT.json")
R439_R5 = Path(
    "outputs/v0_6D1_R4_39_R5/R4_39_R5_POSTREPAIR_RESEAL_AUDIT.json"
)
R439_TIME = Path("outputs/v0_6D1_R4_39/R4_39_EXACT_ORDINAL_TIME_MAPPING.json")
R439_DYNAMICS = Path(
    "outputs/v0_6D1_R4_39/R4_39_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GATE.json"
)
R439_J21 = Path(
    "outputs/v0_6D1_R4_39/R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json"
)
R439_J21_NATIVE = Path(
    "outputs/v0_6D1_R4_39/R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json"
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


def _state_digest(
    age: float,
    coords: np.ndarray,
    population_proxy: np.ndarray | None = None,
) -> str:
    h = hashlib.sha256()
    h.update(np.asarray([age], dtype=np.float64).tobytes())
    arr = np.asarray(coords, dtype=np.float64)
    h.update(str(arr.shape).encode("utf-8"))
    h.update(arr.tobytes(order="C"))
    if population_proxy is not None:
        p = np.asarray(population_proxy, dtype=np.float64)
        h.update(str(p.shape).encode("utf-8"))
        h.update(p.tobytes(order="C"))
    return h.hexdigest()


def _aggregate_digests(values: list[str]) -> str:
    h = hashlib.sha256()
    for value in values:
        h.update(value.encode("ascii"))
    return h.hexdigest()


def _j14_carrier_replay_authority(root: Path) -> dict[str, Any]:
    p = root / J14_SOURCE
    if sha256(p) != J14_SHA:
        return {"status": BLOCKED, "reason": "J14_SOURCE_HASH_MISMATCH"}

    with np.load(p, allow_pickle=False) as z:
        age = np.asarray(z["age_ma"], dtype=float)
        candidate_ids = [str(x) for x in z["candidate_ids"]]
        names = [str(x) for x in z["state_variable_names"]]
        state = np.asarray(z["spatial_state"], dtype=float)

    expected_names = ["population_proxy", "grid_row", "grid_col", "active"]
    if names != expected_names or state.shape != (96, 2, 141, 8, 4):
        return {
            "status": BLOCKED,
            "reason": "J14_SCHEMA_MISMATCH",
            "state_variable_names": names,
            "shape": list(state.shape),
        }

    pi = names.index("population_proxy")
    ri = names.index("grid_row")
    ci = names.index("grid_col")
    ai = names.index("active")

    branch_digests = []
    total_active_states = 0
    total_carrier_instances = 0
    bad_coords = 0
    nonbinary_active = 0

    for member in range(state.shape[0]):
        for cand in range(state.shape[1]):
            state_digests = []
            for ti, physical_age in enumerate(age):
                slab = state[member, cand, ti]
                active = slab[:, ai]
                binary = np.logical_or(
                    np.isclose(active, 0.0, rtol=0.0, atol=1e-12),
                    np.isclose(active, 1.0, rtol=0.0, atol=1e-12),
                )
                nonbinary_active += int(np.size(binary) - np.count_nonzero(binary))
                mask = active > 0.5
                coords = np.column_stack((slab[mask, ci], slab[mask, ri]))
                pops = slab[mask, pi]

                if len(coords):
                    valid = (
                        np.all(np.isfinite(coords))
                        and np.all(coords[:, 0] >= 0.0)
                        and np.all(coords[:, 0] < 180.0)
                        and np.all(coords[:, 1] >= 0.0)
                        and np.all(coords[:, 1] <= 89.0)
                    )
                    if not valid:
                        bad_coords += 1
                    total_active_states += 1
                    total_carrier_instances += int(len(coords))

                state_digests.append(
                    _state_digest(float(physical_age), coords, pops)
                )

            branch_digests.append(
                _aggregate_digests(state_digests)
            )

    branch_count = state.shape[0] * state.shape[1]
    transition_targets = branch_count * (len(age) - 1)
    ok = (
        len(age) == 141
        and branch_count == 192
        and transition_targets == 26880
        and bad_coords == 0
        and nonbinary_active == 0
        and len(candidate_ids) == 2
    )
    return {
        "stage": STAGE,
        "status":
            "R440_J14_CANONICAL_ANCHOR_CARRIER_REPLAY_AUTHORITY_VALIDATED"
            if ok else BLOCKED,
        "source_path": J14_SOURCE.as_posix(),
        "source_sha256": J14_SHA,
        "authority_semantics":
            "MODEL_DERIVED_CANONICAL_SPATIAL_AUTHORITY_NOT_OBSERVED_HISTORY",
        "observed_location_history_claim": False,
        "branch_count": branch_count,
        "canonical_state_count_per_branch": len(age),
        "transition_count_per_branch": len(age) - 1,
        "carrier_state_replacement_target_count": transition_targets,
        "total_active_state_count": total_active_states,
        "total_carrier_instances_across_all_states": total_carrier_instances,
        "bad_coordinate_state_count": bad_coords,
        "nonbinary_active_value_count": nonbinary_active,
        "exact_x_semantics": "x=grid_col",
        "exact_y_semantics": "y=grid_row",
        "coordinate_interpolation_authorized": False,
        "population_proxy_used_as_carrier_count": False,
        "autonomous_movement_authorized": False,
        "autonomous_population_dynamics_authorized": False,
        "autonomous_ageing_authorized": False,
        "branch_sequence_aggregate_sha256":
            _aggregate_digests(branch_digests),
        "pass": ok,
    }


def _j18_carrier_replay_authority(root: Path) -> dict[str, Any]:
    p = root / J18_SOURCE
    if sha256(p) != J18_SHA:
        return {"status": BLOCKED, "reason": "J18_SOURCE_HASH_MISMATCH"}

    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["snapshot_age_ka"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        states = np.asarray(z["snapshot_deme_state"], dtype=float)
        active = np.asarray(z["snapshot_active"])

    expected_ages = np.asarray(
        [200, 125, 100, 75, 50, 30, 20, 15, 14, 13, 12, 11, 10, 5, 0],
        dtype=float,
    )
    schema_ok = (
        states.shape == (32, 2, 15, 6, 7)
        and active.shape == (32, 2, 15, 6)
        and np.array_equal(ages, expected_ages)
        and "grid_row" in names
        and "grid_col" in names
        and "population_proxy" in names
    )
    if not schema_ok:
        return {
            "status": BLOCKED,
            "reason": "J18_SCHEMA_MISMATCH",
            "states_shape": list(states.shape),
            "active_shape": list(active.shape),
            "ages": ages.tolist(),
            "state_variable_names": names,
        }

    pi = names.index("population_proxy")
    ri = names.index("grid_row")
    ci = names.index("grid_col")

    branch_digests = []
    total_active_states = 0
    total_carrier_instances = 0
    bad_coords = 0
    nonbinary_active = 0

    for member in range(states.shape[0]):
        for cand in range(states.shape[1]):
            state_digests = []
            for ti, physical_age in enumerate(ages):
                slab = states[member, cand, ti]
                amask = np.asarray(active[member, cand, ti], dtype=float)
                binary = np.logical_or(
                    np.isclose(amask, 0.0, rtol=0.0, atol=1e-12),
                    np.isclose(amask, 1.0, rtol=0.0, atol=1e-12),
                )
                nonbinary_active += int(np.size(binary) - np.count_nonzero(binary))
                mask = amask > 0.5
                coords = np.column_stack((slab[mask, ci], slab[mask, ri]))
                pops = slab[mask, pi]

                if len(coords):
                    valid = (
                        np.all(np.isfinite(coords))
                        and np.all(coords[:, 0] >= 0.0)
                        and np.all(coords[:, 0] < 180.0)
                        and np.all(coords[:, 1] >= 0.0)
                        and np.all(coords[:, 1] <= 89.0)
                    )
                    if not valid:
                        bad_coords += 1
                    total_active_states += 1
                    total_carrier_instances += int(len(coords))

                state_digests.append(
                    _state_digest(float(physical_age), coords, pops)
                )

            branch_digests.append(_aggregate_digests(state_digests))

    branch_count = states.shape[0] * states.shape[1]
    transition_targets = branch_count * (len(ages) - 1)
    ok = (
        branch_count == 64
        and transition_targets == 896
        and bad_coords == 0
        and nonbinary_active == 0
    )
    return {
        "stage": STAGE,
        "status":
            "R440_J18_CANONICAL_ANCHOR_CARRIER_REPLAY_AUTHORITY_VALIDATED"
            if ok else BLOCKED,
        "source_path": J18_SOURCE.as_posix(),
        "source_sha256": J18_SHA,
        "authority_semantics":
            "R3_28_CANONICAL_SNAPSHOT_DEME_STATE_REPLAY",
        "branch_count": branch_count,
        "canonical_state_count_per_branch": len(ages),
        "transition_count_per_branch": len(ages) - 1,
        "carrier_state_replacement_target_count": transition_targets,
        "total_active_state_count": total_active_states,
        "total_carrier_instances_across_all_states": total_carrier_instances,
        "bad_coordinate_state_count": bad_coords,
        "nonbinary_active_value_count": nonbinary_active,
        "exact_x_semantics": "x=grid_col",
        "exact_y_semantics": "y=grid_row",
        "coordinate_interpolation_authorized": False,
        "population_proxy_used_as_carrier_count": False,
        "autonomous_movement_authorized": False,
        "autonomous_population_dynamics_authorized": False,
        "autonomous_ageing_authorized": False,
        "branch_sequence_aggregate_sha256":
            _aggregate_digests(branch_digests),
        "pass": ok,
    }


def _live_queue_source_audit() -> dict[str, Any]:
    import geonomics as gnx

    src = inspect.getsource(gnx.Model._make_fn_queue)
    checks = {
        "version_1_4_9": str(getattr(gnx, "__version__", "")) == "1.4.9",
        "default_queue_sets_model_time":
            "queue.append(self._set_t)" in src,
        "default_queue_sets_community_time":
            "queue.append(self._set_comm_t)" in src,
        "default_queue_sets_species_time":
            "_set_spp_t" in src,
        "default_queue_can_move":
            "_do_movement" in src,
        "default_queue_does_population_dynamics":
            "_do_pop_dynamics" in src,
        "default_queue_can_change_landscape":
            "_make_land_change" in src,
        "default_queue_can_refresh_K":
            "_set_K" in src,
    }
    return {
        "stage": STAGE,
        "status":
            "R440_GEONOMICS_DEFAULT_QUEUE_SOURCE_AUDITED"
            if all(checks.values()) else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "default_queue_authorized_for_arcana_nonliteral_carriers": False,
        "reason":
            "DEFAULT_QUEUE_CONTAINS_AUTONOMOUS_MOVEMENT_AND_POPULATION_DYNAMICS_"
            "THAT_HAVE_NO_ARCANA_AUTHORITY_FOR_NONLITERAL_CARRIERS",
    }


def _queue_contracts(
    j14: dict[str, Any],
    j18: dict[str, Any],
    parent: dict[str, Any],
) -> dict[str, Any]:
    j21_layer_count = int(parent["j21_native_dynamic_layer_count"])
    j21_transitions = int(parent["j21_geonomics_T"])
    j21_targets = int(parent["j21_future_change_target_count"])

    common_forbidden = [
        "GEONOMICS_DEFAULT_MODEL_WALK",
        "GEONOMICS_AUTONOMOUS_MOVEMENT",
        "GEONOMICS_AUTONOMOUS_POPULATION_DYNAMICS",
        "GEONOMICS_AUTONOMOUS_AGEING_AS_PHYSICAL_TIME",
        "POPULATION_PROXY_TO_INDIVIDUAL_COUNT_CAST",
        "COORDINATE_INTERPOLATION_BETWEEN_CANONICAL_ANCHORS",
        "RESULT_SELECTED_TRANSFORM",
    ]

    jobs = {
        J14: {
            "mode": "CANONICAL_ANCHOR_CARRIER_STATE_REPLAY",
            "branch_count": j14["branch_count"],
            "canonical_state_count_per_branch":
                j14["canonical_state_count_per_branch"],
            "transition_count_per_branch":
                j14["transition_count_per_branch"],
            "exact_carrier_replacement_target_count":
                j14["carrier_state_replacement_target_count"],
            "allowed_transition_operations": [
                "BIND_NEXT_ORDINAL_TIMESTEP_TO_CANONICAL_AGE",
                "ARCANA_EXACT_NONLITERAL_CARRIER_STATE_REPLACE_AT_ANCHOR",
                "REBUILD_GEONOMICS_DERIVED_SPATIAL_CACHES",
                "STATIC_CONNECTIVITY_READOUT_ONLY",
            ],
            "forbidden_operations": common_forbidden,
            "between_anchor_carrier_dynamics":
                "NONE_AUTHORIZED",
            "external_engine_may_invent_location_history": False,
        },
        J18: {
            "mode": "CANONICAL_ANCHOR_CARRIER_STATE_REPLAY",
            "branch_count": j18["branch_count"],
            "canonical_state_count_per_branch":
                j18["canonical_state_count_per_branch"],
            "transition_count_per_branch":
                j18["transition_count_per_branch"],
            "exact_carrier_replacement_target_count":
                j18["carrier_state_replacement_target_count"],
            "allowed_transition_operations": [
                "BIND_NEXT_ORDINAL_TIMESTEP_TO_CANONICAL_AGE",
                "ARCANA_EXACT_NONLITERAL_CARRIER_STATE_REPLACE_AT_ANCHOR",
                "REBUILD_GEONOMICS_DERIVED_SPATIAL_CACHES",
                "STATIC_CONNECTIVITY_READOUT_ONLY",
            ],
            "forbidden_operations": common_forbidden,
            "between_anchor_carrier_dynamics":
                "NONE_AUTHORIZED",
            "external_engine_may_invent_location_history": False,
        },
        J21: {
            "mode": "CANONICAL_ANCHOR_LAYER_REPLAY_ONLY",
            "branch_count": 1,
            "canonical_state_count_per_branch": j21_transitions + 1,
            "transition_count_per_branch": j21_transitions,
            "native_dynamic_layer_count": j21_layer_count,
            "exact_layer_target_count": j21_targets,
            "dynamic_sidecar_count": int(parent["j21_dynamic_sidecar_count"]),
            "allowed_transition_operations": [
                "BIND_NEXT_ORDINAL_TIMESTEP_TO_CANONICAL_AGE",
                "APPLY_EXACT_CANONICAL_NATIVE_LAYER_TARGETS",
                "REFRESH_LAYER_DERIVED_CACHES_ONLY_IF_SOURCE_REQUIRED",
                "STATIC_LAYER_OR_CONNECTIVITY_READOUT_ONLY",
            ],
            "forbidden_operations": common_forbidden + [
                "BIND_DYNAMIC_SIDECARS_AS_GEONOMICS_LAYER_RAST"
            ],
            "autonomous_carrier_dynamics":
                "NOT_APPLICABLE_AND_NOT_AUTHORIZED",
        },
    }

    return {
        "stage": STAGE,
        "status": "R440_DOMAIN_SPECIFIC_EXECUTION_QUEUE_CONTRACTS_COMPILED",
        "jobs": jobs,
        "default_geonomics_queue_used": False,
        "domain_specific_carrier_dynamics_authority_closed": True,
        "closure_semantics":
            "AUTHORITY_IS_EXACT_CANONICAL_ANCHOR_REPLAY_WITH_ZERO_AUTONOMOUS_"
            "CARRIER_DYNAMICS_NOT_PERMISSION_FOR_GEONOMICS_TO_INVENT_DYNAMICS",
        "production_execution_queue_authorized": False,
        "single_transition_dry_run_validated": False,
        "geonomics_execution_ready": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R439)
    parent_seal = load(root / R439_SEAL)
    parent_r5 = load(root / R439_R5)
    parent_time = load(root / R439_TIME)
    parent_dyn = load(root / R439_DYNAMICS)
    parent_j21 = load(root / R439_J21)
    parent_j21_native = load(root / R439_J21_NATIVE)

    j14 = _j14_carrier_replay_authority(root)
    j18 = _j18_carrier_replay_authority(root)
    source_queue = _live_queue_source_audit()
    queue = _queue_contracts(j14, j18, parent)

    write(root / OUT / "R4_40_J14_CANONICAL_CARRIER_REPLAY_AUTHORITY.json", j14)
    write(root / OUT / "R4_40_J18_CANONICAL_CARRIER_REPLAY_AUTHORITY.json", j18)
    write(root / OUT / "R4_40_GEONOMICS_DEFAULT_QUEUE_SOURCE_AUDIT.json", source_queue)
    write(root / OUT / "R4_40_DOMAIN_SPECIFIC_EXECUTION_QUEUE_CONTRACTS.json", queue)

    checks = {
        "parent_r439_complete_44_44":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 44
            and parent.get("checks_failed") == 0,
        "parent_r439_sealed_32_32":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 32
            and parent_seal.get("checks_failed") == 0,
        "parent_r439_r5_verified_16_16":
            parent_r5.get("status") == PARENT_R5
            and parent_r5.get("checks_passed") == 16
            and parent_r5.get("checks_total") == 16,
        "parent_next_action_r440":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT
            and parent_r5.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R440_EXACT_CANONICAL_ANCHOR_REPLAY_ZERO_AUTONOMOUS_CARRIER_DYNAMICS",
        "j14_source_hash_exact":
            j14.get("source_sha256") == J14_SHA,
        "j18_source_hash_exact":
            j18.get("source_sha256") == J18_SHA,
        "j14_authority_validated":
            j14.get("pass") is True,
        "j18_authority_validated":
            j18.get("pass") is True,
        "j14_192_branches_141_states_26880_targets":
            j14.get("branch_count") == 192
            and j14.get("canonical_state_count_per_branch") == 141
            and j14.get("carrier_state_replacement_target_count") == 26880,
        "j18_64_branches_15_states_896_targets":
            j18.get("branch_count") == 64
            and j18.get("canonical_state_count_per_branch") == 15
            and j18.get("carrier_state_replacement_target_count") == 896,
        "continuous_coords_preserved":
            j14.get("exact_x_semantics") == "x=grid_col"
            and j14.get("exact_y_semantics") == "y=grid_row"
            and j18.get("exact_x_semantics") == "x=grid_col"
            and j18.get("exact_y_semantics") == "y=grid_row",
        "no_coordinate_interpolation":
            j14.get("coordinate_interpolation_authorized") is False
            and j18.get("coordinate_interpolation_authorized") is False,
        "population_proxy_not_count":
            j14.get("population_proxy_used_as_carrier_count") is False
            and j18.get("population_proxy_used_as_carrier_count") is False,
        "live_default_queue_source_audited":
            source_queue.get("status")
            == "R440_GEONOMICS_DEFAULT_QUEUE_SOURCE_AUDITED",
        "default_queue_not_authorized":
            source_queue.get(
                "default_queue_authorized_for_arcana_nonliteral_carriers"
            ) is False,
        "domain_specific_queue_contracts_compiled":
            queue.get("status")
            == "R440_DOMAIN_SPECIFIC_EXECUTION_QUEUE_CONTRACTS_COMPILED",
        "carrier_dynamics_authority_closed_by_zero_autonomous_dynamics":
            queue.get("domain_specific_carrier_dynamics_authority_closed")
            is True,
        "j14_autonomous_dynamics_off":
            queue["jobs"][J14]["between_anchor_carrier_dynamics"]
            == "NONE_AUTHORIZED",
        "j18_autonomous_dynamics_off":
            queue["jobs"][J18]["between_anchor_carrier_dynamics"]
            == "NONE_AUTHORIZED",
        "j21_layer_only":
            queue["jobs"][J21]["mode"]
            == "CANONICAL_ANCHOR_LAYER_REPLAY_ONLY"
            and queue["jobs"][J21]["native_dynamic_layer_count"] == 147
            and queue["jobs"][J21]["exact_layer_target_count"] == 1176,
        "j21_four_sidecars_stay_external":
            queue["jobs"][J21]["dynamic_sidecar_count"] == 4,
        "r439_time_mapping_preserved":
            parent_time["jobs"][J14]["geonomics_T"] == 140
            and parent_time["jobs"][J18]["geonomics_T"] == 14
            and parent_time["jobs"][J21]["geonomics_T"] == 8,
        "r439_carrier_gap_was_frozen":
            parent_dyn.get("status")
            == "R439_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GAP_FROZEN",
        "r439_j21_147_plus_4_preserved":
            parent_j21.get("native_identity_layer_count") == 147
            and parent_j21.get("canonical_dynamic_sidecar_count") == 4,
        "r439_j21_bounded_validation_preserved":
            parent_j21_native.get("bounded_native_changer_probe_pass") is True
            and parent_j21_native.get(
                "full_direct_native_series_validation_pass_count"
            ) == 1176,
        "single_transition_dry_run_not_yet_validated":
            queue.get("single_transition_dry_run_validated") is False,
        "production_execution_queue_not_authorized":
            queue.get("production_execution_queue_authorized") is False,
        "execution_not_ready":
            queue.get("geonomics_execution_ready") is False,
        "no_model_run":
            cfg.get("model_run_performed_count") == 0,
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
        "geonomics_version": source_queue.get("checks", {}).get(
            "version_1_4_9"
        ) and "1.4.9" or "UNKNOWN",
        "j14_branch_count": j14.get("branch_count"),
        "j14_canonical_state_count": j14.get("canonical_state_count_per_branch"),
        "j14_exact_carrier_replacement_target_count":
            j14.get("carrier_state_replacement_target_count"),
        "j18_branch_count": j18.get("branch_count"),
        "j18_canonical_state_count": j18.get("canonical_state_count_per_branch"),
        "j18_exact_carrier_replacement_target_count":
            j18.get("carrier_state_replacement_target_count"),
        "j21_native_dynamic_layer_count": 147,
        "j21_exact_layer_target_count": 1176,
        "j21_dynamic_sidecar_count": 4,
        "domain_specific_carrier_dynamics_authority_closed": bool(ok),
        "carrier_dynamics_authority_semantics":
            "ZERO_AUTONOMOUS_DYNAMICS_PLUS_EXACT_CANONICAL_ANCHOR_REPLAY",
        "autonomous_movement_authorized": False,
        "autonomous_population_dynamics_authorized": False,
        "autonomous_ageing_authorized": False,
        "default_geonomics_queue_authorized": False,
        "single_transition_dry_run_validated": False,
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
        "next_action":
            NEXT if ok else "REPAIR_R440_DOMAIN_SPECIFIC_QUEUE_AUTHORITY",
    }
    write(root / OUT / "R4_40_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_40_INTEGRATED_AUDIT.json")
    j14 = load(root / OUT / "R4_40_J14_CANONICAL_CARRIER_REPLAY_AUTHORITY.json")
    j18 = load(root / OUT / "R4_40_J18_CANONICAL_CARRIER_REPLAY_AUTHORITY.json")
    src = load(root / OUT / "R4_40_GEONOMICS_DEFAULT_QUEUE_SOURCE_AUDIT.json")
    q = load(root / OUT / "R4_40_DOMAIN_SPECIFIC_EXECUTION_QUEUE_CONTRACTS.json")

    checks = {
        "r440_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "j14_replay_authority":
            j14.get("pass") is True
            and j14.get("carrier_state_replacement_target_count") == 26880,
        "j18_replay_authority":
            j18.get("pass") is True
            and j18.get("carrier_state_replacement_target_count") == 896,
        "continuous_coords_exact":
            j14.get("exact_x_semantics") == "x=grid_col"
            and j18.get("exact_x_semantics") == "x=grid_col",
        "no_coordinate_interpolation":
            j14.get("coordinate_interpolation_authorized") is False
            and j18.get("coordinate_interpolation_authorized") is False,
        "population_proxy_nonliteral":
            j14.get("population_proxy_used_as_carrier_count") is False
            and j18.get("population_proxy_used_as_carrier_count") is False,
        "default_queue_source_audited":
            src.get("status") == "R440_GEONOMICS_DEFAULT_QUEUE_SOURCE_AUDITED",
        "default_queue_forbidden":
            src.get("default_queue_authorized_for_arcana_nonliteral_carriers")
            is False,
        "domain_specific_authority_closed":
            q.get("domain_specific_carrier_dynamics_authority_closed") is True,
        "j14_zero_autonomous_dynamics":
            q["jobs"][J14]["between_anchor_carrier_dynamics"]
            == "NONE_AUTHORIZED",
        "j18_zero_autonomous_dynamics":
            q["jobs"][J18]["between_anchor_carrier_dynamics"]
            == "NONE_AUTHORIZED",
        "j21_layer_only_147_1176":
            q["jobs"][J21]["mode"] == "CANONICAL_ANCHOR_LAYER_REPLAY_ONLY"
            and q["jobs"][J21]["native_dynamic_layer_count"] == 147
            and q["jobs"][J21]["exact_layer_target_count"] == 1176,
        "j21_four_sidecars_external":
            q["jobs"][J21]["dynamic_sidecar_count"] == 4,
        "single_transition_dry_run_pending":
            a.get("single_transition_dry_run_validated") is False,
        "production_queue_not_authorized":
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
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r441":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())
    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_"
            "AND_EXECUTION_QUEUE_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "j14_exact_carrier_replacement_target_count":
                a.get("j14_exact_carrier_replacement_target_count"),
            "j18_exact_carrier_replacement_target_count":
                a.get("j18_exact_carrier_replacement_target_count"),
            "j21_exact_layer_target_count":
                a.get("j21_exact_layer_target_count"),
            "domain_specific_carrier_dynamics_authority_closed":
                a.get("domain_specific_carrier_dynamics_authority_closed"),
            "authority_semantics":
                a.get("carrier_dynamics_authority_semantics"),
            "autonomous_movement_authorized": False,
            "autonomous_population_dynamics_authorized": False,
            "autonomous_ageing_authorized": False,
            "default_geonomics_queue_authorized": False,
            "single_transition_dry_run_validated": False,
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
