"""Small noncanonical one-way coupling between the R6 thermal kernel and Deep.

This is an engineering adapter, not a qualified physical coupling. A 1-D
thermal column is sampled into two explicitly mapped cells; their sensible
heat in joules is used as a prescribed Deep thermal-mode inventory. DFEU,
geological accessibility, and solar forcing are not inferred from temperature.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

import numpy as np

from deep_d3_coupling_v0_6A import (
    MODES,
    PassiveUptakeConfig,
    additive_photo_equilibrium_energy,
    analytic_decaying_component_step,
    local_passive_uptake_rate_per_year,
)

from .functional_development import ReducedState, pure_shear_thermal_step, state_from_payload

SECONDS_PER_YEAR = 31_557_600.0
PILOT_SCHEMA = "ARCANA_TECTONIC_DEEP_ENGINEERING_PILOT_V1"
DEFAULT_SOURCE_ARCHIVE_MEMBER = (
    "ENG10K_ARCHIVE_ec79bf89_01/candidate/SEGMENT_ARCHIVE_V1/STATES.jsonl"
)
DEFAULT_TRAJECTORY_ID = "DIRECT-f0.001-R6G1D-R091-C029"


@dataclass(frozen=True)
class PilotGrid:
    """A 1x2 sample grid; cells are column control volumes, not world cells."""

    grid_id: str
    cell_ids: tuple[str, str]
    node_indices: tuple[int, int]
    geological_accessibility_a_x: tuple[float, float]
    exposure_zeta: tuple[float, float]
    capacity_c_car: tuple[float, float]
    demand_saturation: tuple[float, float]
    strike_length_m: float = 1.0

    def validate(self, node_count: int) -> None:
        if not self.grid_id.strip() or len(set(self.cell_ids)) != 2:
            raise ValueError("PILOT_GRID_ID_OR_CELL_IDS_INVALID")
        if len(set(self.node_indices)) != 2 or any(i < 1 or i >= node_count - 1 for i in self.node_indices):
            raise ValueError("PILOT_GRID_NODE_MAPPING_INVALID")
        if not math.isfinite(self.strike_length_m) or self.strike_length_m <= 0:
            raise ValueError("PILOT_GRID_STRIKE_LENGTH_INVALID")
        for values in (self.geological_accessibility_a_x, self.exposure_zeta,
                       self.capacity_c_car, self.demand_saturation):
            if len(values) != 2 or any(not math.isfinite(v) or not 0.0 <= v <= 1.0 for v in values):
                raise ValueError("PILOT_GRID_FRACTION_INVALID")

    def identity_sha256(self) -> str:
        body = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()


DEFAULT_GRID = PilotGrid(
    grid_id="C029_TWO_THERMAL_CONTROL_VOLUME_EXPERIMENT_NOT_GLOBAL",
    cell_ids=("C029_THERMAL_SAMPLE_INDEX_024_ZERO_BASED", "C029_THERMAL_SAMPLE_INDEX_025_ZERO_BASED"),
    node_indices=(24, 25),
    geological_accessibility_a_x=(0.5, 0.8),
    exposure_zeta=(0.4, 0.7),
    capacity_c_car=(0.6, 0.8),
    demand_saturation=(0.2, 0.35),
)


def load_archived_state_jsonl(
    archive_path: str,
    *,
    member: str = DEFAULT_SOURCE_ARCHIVE_MEMBER,
    trajectory_id: str = DEFAULT_TRAJECTORY_ID,
    sequence: int = 0,
) -> tuple[ReducedState, dict[str, Any]]:
    """Load one preserved state record from a tar.gz without extracting files."""
    import tarfile

    digest = hashlib.sha256()
    with open(archive_path, "rb") as raw:
        for block in iter(lambda: raw.read(1024 * 1024), b""):
            digest.update(block)
    found: dict[str, Any] | None = None
    with tarfile.open(archive_path, "r:gz") as tar:
        entry = tar.getmember(member)
        stream = tar.extractfile(entry)
        if stream is None:
            raise ValueError("ARCHIVE_STATE_MEMBER_NOT_READABLE")
        for line in stream:
            row = json.loads(line)
            if row.get("trajectory_id") == trajectory_id and row.get("sequence") == sequence:
                if found is not None:
                    raise ValueError("ARCHIVE_STATE_RECORD_NOT_UNIQUE")
                found = row
        case = json.load(tar.extractfile(
            "ENG10K_ARCHIVE_ec79bf89_01/candidate/engineering_case.json"
        ))
    if found is None:
        raise ValueError("ARCHIVE_STATE_RECORD_NOT_FOUND")
    canonical = json.dumps(found["state"], sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")
    state_hash = hashlib.sha256(canonical).hexdigest()
    if found.get("state_payload_sha256") != state_hash:
        raise ValueError("ARCHIVE_STATE_PAYLOAD_HASH_MISMATCH")
    if found.get("state_class") != "DIAGNOSTIC_OBSERVATION":
        raise ValueError("ARCHIVE_STATE_CLASS_UNEXPECTED")
    if case.get("experiment_id") != "R6-INT3-ENG10K-A" or case.get("scope") != "NONCANONICAL_ENGINEERING_STRESS_TEST":
        raise ValueError("ARCHIVE_ENGINEERING_CASE_IDENTITY_UNEXPECTED")
    state = state_from_payload(found["state"])
    return state, {
        "archive_path": archive_path,
        "archive_sha256": digest.hexdigest(),
        "member": member,
        "trajectory_id": trajectory_id,
        "sequence": sequence,
        "support_id": found.get("support_id"),
        "time_s": found.get("time_s"),
        "state_payload_sha256": state_hash,
        "state_class": found.get("state_class"),
        "checkpoint_capability": found.get("checkpoint_capability"),
        "frozen_euler_extension_m_per_year": case.get("frozen_euler_extension_m_per_year"),
        "historical_case_identity": "READ_FROM_PRESERVED_ENG10K_ARCHIVE_NOT_REQUALIFIED_HERE",
    }


def _control_volume_widths(state: ReducedState) -> tuple[float, ...]:
    z = tuple(x * state.lithosphere_m for x in state.material_coordinate)
    bounds = [z[0]]
    bounds.extend((z[i - 1] + z[i]) * 0.5 for i in range(1, len(z)))
    bounds.append(z[-1])
    return tuple(bounds[i + 1] - bounds[i] for i in range(len(z)))


def mapped_sensible_energy_j(state: ReducedState, grid: PilotGrid) -> np.ndarray:
    """Compute mapped-node rho*cp*T*volume for a 1 m strike-length slice."""
    grid.validate(len(state.temperature_k))
    dz = _control_volume_widths(state)
    result = []
    for index in grid.node_indices:
        material = state.materials[index]
        volume = state.width_m * grid.strike_length_m * dz[index]
        energy = material.rho_kg_m3 * material.cp_j_kg_k * state.temperature_k[index] * volume
        if not math.isfinite(energy) or energy < 0:
            raise ValueError("THERMAL_SENSIBLE_ENERGY_INVALID")
        result.append(energy)
    return np.asarray(result, dtype=np.float64)


def run_tiny_coupling(
    initial_state: ReducedState,
    *,
    duration_years: float = 1.0,
    extension_velocity_m_per_year: float = 0.11467052868814648,
    grid: PilotGrid = DEFAULT_GRID,
    photo_share: float = 0.05,
    passive_config: PassiveUptakeConfig = PassiveUptakeConfig(),
) -> dict[str, Any]:
    """Advance actual kernel, transfer mapped heat J, then run Deep v0.6A ledger.

    The heat-to-Deep mapping, 1x2 attributes and frozen velocity are explicit
    engineering forcing. This does not feed Deep back into tectonics.
    """
    if not math.isfinite(duration_years) or duration_years <= 0:
        raise ValueError("PILOT_DURATION_MUST_BE_POSITIVE")
    if not math.isfinite(extension_velocity_m_per_year) or extension_velocity_m_per_year < 0:
        raise ValueError("PILOT_EXTENSION_VELOCITY_INVALID")
    grid.validate(len(initial_state.temperature_k))
    import tracemalloc
    from time import perf_counter

    before = mapped_sensible_energy_j(initial_state, grid)
    start = perf_counter()
    tracemalloc.start()
    final_state, thermal_diagnostics = pure_shear_thermal_step(
        initial_state,
        duration_s=duration_years * SECONDS_PER_YEAR,
        extension_velocity_m_s=extension_velocity_m_per_year / SECONDS_PER_YEAR,
    )
    after = mapped_sensible_energy_j(final_state, grid)

    # Deep v0.6A expects J-valued energy reservoirs. Use the post-tectonic
    # sensible energy as a declared synthetic thermal-mode inventory.
    shape = (len(MODES), 1, len(grid.cell_ids))
    background = np.zeros(shape, dtype=np.float64)
    background[MODES.index("th"), 0, :] = after
    photo = additive_photo_equilibrium_energy(background, photo_share, ("th",))

    restore_time = np.asarray((80.0, 120.0, 100.0, 250.0, 500.0), dtype=np.float64)
    saturation = np.zeros(shape, dtype=np.float64)
    c_car = np.zeros(shape, dtype=np.float64)
    zeta = np.zeros(shape, dtype=np.float64)
    saturation[MODES.index("th"), 0, :] = grid.demand_saturation
    c_car[MODES.index("th"), 0, :] = grid.capacity_c_car
    zeta[MODES.index("th"), 0, :] = grid.exposure_zeta
    lam = local_passive_uptake_rate_per_year(saturation, c_car, zeta, restore_time, passive_config)
    tau_th = restore_time[MODES.index("th")]
    dt = float(duration_years)
    background_step = analytic_decaying_component_step(
        background, tau_th, lam, dt,
        return_flow_fraction=0.50,
    )
    photo_step = analytic_decaying_component_step(
        photo, tau_th, lam, dt,
        return_flow_fraction=0.50,
    )
    elapsed_s = perf_counter() - start
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    bg_after = background_step["surface_energy_after_j"]
    ph_after = photo_step["surface_energy_after_j"]
    bg_th = bg_after[MODES.index("th"), 0, :]
    ph_th = ph_after[MODES.index("th"), 0, :]
    access_proxy = np.asarray(grid.geological_accessibility_a_x) * np.asarray(grid.exposure_zeta)
    # A_X/zeta are dimensionless and deliberately remain separate; DFEU is
    # unavailable here, so no accessible DFEU or canonical opportunity is made.
    deep_bg = background_step
    deep_photo = photo_step
    closure = np.concatenate((deep_bg["closure_error_j"].ravel(), deep_photo["closure_error_j"].ravel()))
    all_values = np.concatenate((bg_th, ph_th, background_step["gross_uptake_j"][MODES.index("th"), 0],
                                 photo_step["gross_uptake_j"][MODES.index("th"), 0]))
    if not np.isfinite(all_values).all() or np.any(all_values < 0):
        raise ValueError("DEEP_LEDGER_NONFINITE_OR_NEGATIVE")

    return {
        "schema": PILOT_SCHEMA,
        "scope": "NONCANONICAL_SHORT_ENGINEERING_COUPLING_NOT_PHYSICAL_QUALIFICATION",
        "coupling_direction": "TECTONIC_THERMAL_STATE_TO_DEEP_THERMAL_MODE_ONLY",
        "grid": {
            "grid_id": grid.grid_id,
            "grid_identity_sha256": grid.identity_sha256(),
            "grid_shape": [1, len(grid.cell_ids)],
            "cell_ids": list(grid.cell_ids),
            "mapped_zero_based_node_indices": list(grid.node_indices),
            "mapping_semantics": "TWO_DISJOINT_C029_VERTICAL_CONTROL_VOLUME_SAMPLES_NOT_GLOBAL_CELLS",
            "strike_length_m": grid.strike_length_m,
        },
        "forcing": {
            "duration_years": duration_years,
            "extension_velocity_m_per_year": extension_velocity_m_per_year,
            "velocity_authority": "PRESCRIBED_FROM_EXISTING_ENG10K_ENGINEERING_CASE_FOR_SHORT_PROTOTYPE_ONLY",
            "thermal_to_deep_transfer": "ONE_TO_ONE_SENSIBLE_HEAT_J_TO_SYNTHETIC_DEEP_TH_INVENTORY_J",
        },
        "thermal": {
            "time_before_s": initial_state.time_s,
            "time_after_s": final_state.time_s,
            "width_before_m": initial_state.width_m,
            "width_after_m": final_state.width_m,
            "temperature_min_before_k": min(initial_state.temperature_k),
            "temperature_min_after_k": min(final_state.temperature_k),
            "temperature_max_before_k": max(initial_state.temperature_k),
            "temperature_max_after_k": max(final_state.temperature_k),
            "temperature_change_linf_k": max(abs(a - b) for a, b in zip(final_state.temperature_k, initial_state.temperature_k)),
            "energy_reference_temperature_k": 0.0,
            "mapped_sensible_energy_before_j": before.tolist(),
            "mapped_sensible_energy_after_j": after.tolist(),
            "mapped_sensible_energy_delta_j": (after - before).tolist(),
            "kernel_substeps": thermal_diagnostics.substeps,
            "area_relative_error": thermal_diagnostics.area_relative_error,
        },
        "deep": {
            "geological_inventory_dfeu": None,
            "geological_inventory_status": "UNKNOWN_NO_DFEU_FIELD_BOUND_TO_C029",
            "background_thermal_inventory_at_deep_step_start_j": background[MODES.index("th"), 0].tolist(),
            "background_thermal_inventory_after_j": bg_th.tolist(),
            "photo_share_candidate": photo_share,
            "photo_share_source": "EXISTING_DEEP_V06C_CANDIDATE_CONFIGURATION",
            "photo_contribution_inventory_before_j": photo[MODES.index("th"), 0].tolist(),
            "photo_contribution_inventory_after_j": ph_th.tolist(),
            "solar_flux_or_spatial_irradiance": None,
            "solar_flux_status": "UNKNOWN_NOT_MODELED; PHOTO_TERM_IS_ONLY_THE_EXISTING_ADDITIVE_CANDIDATE_SHARE",
            "geological_accessibility_A_X": list(grid.geological_accessibility_a_x),
            "exposure_zeta": list(grid.exposure_zeta),
            "synthetic_accessibility_proxy_A_X_times_zeta": access_proxy.tolist(),
            "accessibility_authority": "SYNTHETIC_FIXTURE_INPUT; NOT_A_GEOLOGICAL_PROVIDER",
            "remaining_background_inventory_j_after": bg_th.tolist(),
            "remaining_photo_inventory_j_after": ph_th.tolist(),
            "available_energy_j": None,
            "available_energy_status": "UNKNOWN_DISTINCT_FROM_REMAINING_INVENTORY; NO_C029_DFEU_TO_JOULE_BINDING",
            "accessible_dfeu": None,
            "accessible_dfeu_status": "UNKNOWN_NO_DFEU_TO_APPLY_A_X_AND_ZETA_WITH_CANONICAL_SEMANTICS",
            "gross_uptake_j": background_step["gross_uptake_j"][MODES.index("th"), 0].tolist(),
            "returned_energy_j": background_step["return_flow_j"][MODES.index("th"), 0].tolist(),
            "net_biological_sink_j": background_step["net_biological_sink_j"][MODES.index("th"), 0].tolist(),
            "decay_dissipation_j": background_step["physical_decay_dissipation_j"][MODES.index("th"), 0].tolist(),
            "photo_gross_uptake_j": photo_step["gross_uptake_j"][MODES.index("th"), 0].tolist(),
            "photo_returned_energy_j": photo_step["return_flow_j"][MODES.index("th"), 0].tolist(),
            "photo_net_biological_sink_j": photo_step["net_biological_sink_j"][MODES.index("th"), 0].tolist(),
            "photo_decay_dissipation_j": photo_step["physical_decay_dissipation_j"][MODES.index("th"), 0].tolist(),
            "energy_closure_max_abs_j": float(np.max(np.abs(closure))),
            "energy_closure_relative_to_max_inventory": float(
                np.max(np.abs(closure)) / max(float(np.max(background)), float(np.max(photo)), 1.0)
            ),
        },
        "measurements": {
            "elapsed_seconds": elapsed_s,
            "tracemalloc_peak_bytes": peak_python_bytes,
            "tracemalloc_scope": "PYTHON_ALLOCATIONS_ONLY_NOT_PROCESS_RSS",
            "output_bytes": None,
        },
        "claim_limit": "ENGINEERING_DATAFLOW_AND_OPERATOR_SMOKE_ONLY_NO_BIDIRECTIONAL_OR_GEOLOGICAL_VALIDATION",
    }


def conservative_two_cell_transport(values_j: np.ndarray, fraction: float) -> tuple[np.ndarray, float]:
    """Exchange a bounded fraction of the two-cell difference; positive is 0->1."""
    values = np.asarray(values_j, dtype=np.float64)
    if values.shape != (2,) or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("TRANSPORT_REQUIRES_TWO_FINITE_NONNEGATIVE_RESERVOIRS")
    if not math.isfinite(fraction) or not 0.0 <= fraction <= 0.5:
        raise ValueError("TRANSPORT_FRACTION_OUTSIDE_CONSERVATIVE_BOUNDS")
    transfer = float(fraction * (values[0] - values[1]))
    result = np.asarray((values[0] - transfer, values[1] + transfer), dtype=np.float64)
    if not np.isfinite(result).all() or np.any(result < 0):
        raise ValueError("TRANSPORT_RESULT_INVALID")
    return result, transfer


def _run_multistep_branch(
    initial_state: ReducedState,
    *,
    steps: int,
    step_years: float,
    extension_velocity_m_per_year: float,
    grid: PilotGrid,
    transport_enabled: bool,
    transport_fraction: float,
    photo_share: float,
    passive_config: PassiveUptakeConfig,
) -> dict[str, Any]:
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("MULTISTEP_COUNT_MUST_BE_POSITIVE_INTEGER")
    if not math.isfinite(step_years) or step_years <= 0:
        raise ValueError("MULTISTEP_DURATION_MUST_BE_POSITIVE")
    grid.validate(len(initial_state.temperature_k))
    if not 0.0 <= transport_fraction <= 0.5:
        raise ValueError("TRANSPORT_FRACTION_OUTSIDE_CONSERVATIVE_BOUNDS")

    background = np.zeros((len(MODES), 1, 2), dtype=np.float64)
    background[MODES.index("th"), 0, :] = mapped_sensible_energy_j(initial_state, grid)
    photo = additive_photo_equilibrium_energy(background, photo_share, ("th",))
    initial_photo = photo.copy()
    restores = np.asarray((80.0, 120.0, 100.0, 250.0, 500.0), dtype=np.float64)
    saturation = np.zeros_like(background)
    c_car = np.zeros_like(background)
    zeta = np.zeros_like(background)
    mode_th = MODES.index("th")
    saturation[mode_th, 0, :] = grid.demand_saturation
    c_car[mode_th, 0, :] = grid.capacity_c_car
    zeta[mode_th, 0, :] = grid.exposure_zeta
    lam = local_passive_uptake_rate_per_year(saturation, c_car, zeta, restores, passive_config)
    state = initial_state
    records: list[dict[str, Any]] = []
    for index in range(steps):
        thermal_before = mapped_sensible_energy_j(state, grid)
        next_state, thermal_diag = pure_shear_thermal_step(
            state,
            duration_s=step_years * SECONDS_PER_YEAR,
            extension_velocity_m_s=extension_velocity_m_per_year / SECONDS_PER_YEAR,
        )
        thermal_after = mapped_sensible_energy_j(next_state, grid)
        thermal_delta = thermal_after - thermal_before

        bg_before_operator = background.copy()
        bg_before_operator[mode_th, 0, :] += thermal_delta
        if np.any(bg_before_operator < 0) or not np.isfinite(bg_before_operator).all():
            raise ValueError("THERMAL_FIXTURE_SOURCE_EXHAUSTED_DEEP_INVENTORY")
        bg_op = analytic_decaying_component_step(
            bg_before_operator, restores[mode_th], lam, step_years,
            return_flow_fraction=0.50,
        )
        photo_op = analytic_decaying_component_step(
            photo, restores[mode_th], lam, step_years,
            return_flow_fraction=0.50,
        )
        background = bg_op["surface_energy_after_j"]
        photo = photo_op["surface_energy_after_j"]

        bg_after_operator = background[mode_th, 0, :].copy()
        photo_after_operator = photo[mode_th, 0, :].copy()
        if transport_enabled:
            bg_transported, bg_flux = conservative_two_cell_transport(bg_after_operator, transport_fraction)
            photo_transported, photo_flux = conservative_two_cell_transport(photo_after_operator, transport_fraction)
            background[mode_th, 0, :] = bg_transported
            photo[mode_th, 0, :] = photo_transported
        else:
            bg_flux = photo_flux = 0.0

        bg_final = background[mode_th, 0, :].copy()
        photo_final = photo[mode_th, 0, :].copy()
        bg_energy_closure = (
            bg_before_operator[mode_th, 0, :]
            + bg_op["return_flow_j"][mode_th, 0, :]
            - bg_op["gross_uptake_j"][mode_th, 0, :]
            - bg_op["physical_decay_dissipation_j"][mode_th, 0, :]
            - bg_after_operator
        )
        photo_energy_closure = (
            photo_op["surface_energy_before_j"][mode_th, 0, :]
            + photo_op["return_flow_j"][mode_th, 0, :]
            - photo_op["gross_uptake_j"][mode_th, 0, :]
            - photo_op["physical_decay_dissipation_j"][mode_th, 0, :]
            - photo_after_operator
        )
        bg_transport_residual = float(np.sum(bg_final) - np.sum(bg_after_operator))
        photo_transport_residual = float(np.sum(photo_final) - np.sum(photo_after_operator))
        closure_values = np.concatenate((bg_energy_closure, photo_energy_closure,
                                         np.asarray((bg_transport_residual, photo_transport_residual))))
        if not np.isfinite(closure_values).all() or np.any(bg_final < 0) or np.any(photo_final < 0):
            raise ValueError("MULTISTEP_DEEP_LEDGER_INVALID")
        scale = max(float(np.max(bg_before_operator)), float(np.max(photo_op["surface_energy_before_j"])), 1.0)
        records.append({
            "step": index + 1,
            "thermal_time_start_s": state.time_s,
            "thermal_time_end_s": next_state.time_s,
            "thermal_substeps": thermal_diag.substeps,
            "thermal_energy_before_j": thermal_before.tolist(),
            "thermal_energy_after_j": thermal_after.tolist(),
            "thermal_delta_applied_to_deep_j": thermal_delta.tolist(),
            "deep_background_input_j": bg_before_operator[mode_th, 0, :].tolist(),
            "deep_background_after_operator_j": bg_after_operator.tolist(),
            "deep_photo_input_j": photo_op["surface_energy_before_j"][mode_th, 0, :].tolist(),
            "deep_photo_after_operator_j": photo_after_operator.tolist(),
            "background_transport_0_to_1_j": bg_flux,
            "photo_transport_0_to_1_j": photo_flux,
            "background_transport_sum_residual_j": bg_transport_residual,
            "photo_transport_sum_residual_j": photo_transport_residual,
            "background_gross_uptake_j": bg_op["gross_uptake_j"][mode_th, 0, :].tolist(),
            "background_return_flow_j": bg_op["return_flow_j"][mode_th, 0, :].tolist(),
            "background_dissipation_j": bg_op["physical_decay_dissipation_j"][mode_th, 0, :].tolist(),
            "photo_gross_uptake_j": photo_op["gross_uptake_j"][mode_th, 0, :].tolist(),
            "photo_return_flow_j": photo_op["return_flow_j"][mode_th, 0, :].tolist(),
            "photo_dissipation_j": photo_op["physical_decay_dissipation_j"][mode_th, 0, :].tolist(),
            "energy_balance_residual_max_abs_j": float(np.max(np.abs(closure_values))),
            "energy_balance_residual_relative": float(np.max(np.abs(closure_values)) / scale),
            "deep_total_energy_before_transport_j": float(np.sum(bg_after_operator + photo_after_operator)),
            "deep_total_energy_after_transport_j": float(np.sum(bg_final + photo_final)),
        })
        state = next_state

    available = background[mode_th, 0, :] + photo[mode_th, 0, :]
    return {
        "transport_enabled": transport_enabled,
        "transport_fraction": transport_fraction if transport_enabled else 0.0,
        "final_thermal_state": state,
        "final_background_j": background[mode_th, 0, :].copy(),
        "final_photo_j": photo[mode_th, 0, :].copy(),
        "final_available_energy_j": available.copy(),
        "initial_photo_j": initial_photo[mode_th, 0, :].copy(),
        "records": records,
    }


def run_multistep_transport_comparison(
    initial_state: ReducedState,
    *,
    steps: int = 3,
    step_years: float = 1.0,
    extension_velocity_m_per_year: float = 0.11467052868814648,
    grid: PilotGrid = DEFAULT_GRID,
    transport_fraction: float = 0.2,
    photo_share: float = 0.05,
    passive_config: PassiveUptakeConfig = PassiveUptakeConfig(),
) -> dict[str, Any]:
    """Compare identical short tectonic/Deep runs with transport disabled/enabled."""
    import tracemalloc
    from time import perf_counter

    tracemalloc.start()
    started = perf_counter()
    off = _run_multistep_branch(
        initial_state, steps=steps, step_years=step_years,
        extension_velocity_m_per_year=extension_velocity_m_per_year,
        grid=grid, transport_enabled=False, transport_fraction=transport_fraction,
        photo_share=photo_share, passive_config=passive_config,
    )
    on = _run_multistep_branch(
        initial_state, steps=steps, step_years=step_years,
        extension_velocity_m_per_year=extension_velocity_m_per_year,
        grid=grid, transport_enabled=True, transport_fraction=transport_fraction,
        photo_share=photo_share, passive_config=passive_config,
    )
    elapsed = perf_counter() - started
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    off_distribution = off["final_available_energy_j"]
    on_distribution = on["final_available_energy_j"]
    thermal_difference = max(abs(a - b) for a, b in zip(
        off["final_thermal_state"].temperature_k, on["final_thermal_state"].temperature_k
    ))
    return {
        "schema": "ARCANA_TECTONIC_DEEP_MULTISTEP_TRANSPORT_PILOT_V1",
        "scope": "NONCANONICAL_SYNTHETIC_TRANSPORT_AND_MULTI_STEP_DATAFLOW_ONLY",
        "steps": steps,
        "step_years": step_years,
        "total_engineering_years": steps * step_years,
        "extension_velocity_m_per_year": extension_velocity_m_per_year,
        "grid": {
            "grid_id": grid.grid_id,
            "grid_identity_sha256": grid.identity_sha256(),
            "shape": [1, 2],
            "cell_ids": list(grid.cell_ids),
            "node_indices_zero_based": list(grid.node_indices),
            "mapped_node_depth_m": [
                initial_state.material_coordinate[i] * initial_state.lithosphere_m
                for i in grid.node_indices
            ],
            "mapped_material_role_ids": [initial_state.materials[i].role_id for i in grid.node_indices],
            "mapped_material_properties": [
                {
                    "rho_kg_m3": initial_state.materials[i].rho_kg_m3,
                    "cp_j_kg_k": initial_state.materials[i].cp_j_kg_k,
                    "k_w_m_k": initial_state.materials[i].k_w_m_k,
                }
                for i in grid.node_indices
            ],
            "geological_accessibility_A_X": list(grid.geological_accessibility_a_x),
            "accessibility_authority": "SYNTHETIC_FIXTURE_INPUT_NOT_GEOLOGICAL_PROVIDER",
            "exposure_zeta": list(grid.exposure_zeta),
            "capacity_C_car": list(grid.capacity_c_car),
            "demand_saturation": list(grid.demand_saturation),
        },
        "energy_semantics": {
            "geological_inventory_dfeu": None,
            "geological_inventory_status": "UNKNOWN_NO_DEEP_GEOLOGICAL_PROVIDER_BOUND_TO_C029",
            "deep_energy_available_j": "SYNTHETIC_REMAINING_BACKGROUND_PLUS_PHOTO_RESERVOIR",
            "available_energy_scope": "JOULE_INVENTORY_AFTER_DEEP_OPERATOR_NOT_CANONICAL_ACCESSIBLE_DFEU",
            "accessible_dfeu": None,
            "accessibility_zeta": list(grid.exposure_zeta),
            "zeta_used_in": "EXISTING_LOCAL_PASSIVE_UPTAKE_RATE_OPERATOR",
            "A_X_used_in": "REPORTED_SEPARATELY; NO_DFEU_TO_APPLY_EFFECTIVE_MODE_OPPORTUNITY",
            "solar_contribution": "EXISTING_5_PERCENT_ADDITIVE_PHOTO_CANDIDATE_ON_TH_MODE_ONLY",
            "solar_flux": None,
            "solar_flux_status": "UNKNOWN_NOT_MODELED",
            "thermal_transfer": "SIGNED_CELLWISE_SENSIBLE_HEAT_DELTA_ADDED_TO_DEEP_TH_J_AS_EXPLICIT_FIXTURE_SOURCE",
            "thermal_transfer_is_physical_law": False,
            "deep_operator": "DEEP_V06A_ANALYTIC_DECAYING_COMPONENT_PLUS_LOCAL_PASSIVE_UPTAKE",
            "decay_time_years": 120.0,
            "return_flow_fraction": 0.5,
        },
        "transport_law": {
            "formula": "flux_0_to_1 = fraction * (E0 - E1); E0 -= flux; E1 += flux",
            "fraction_per_step": transport_fraction,
            "max_fraction_for_nonnegative_two_cell_update": 0.5,
            "implementation_scope": "SYNTHETIC_CONSERVATIVE_EXCHANGE_NOT_PRODUCTION_TRANSPORT",
        },
        "without_transport": {
            "background_energy_j_by_cell": off["final_background_j"].tolist(),
            "photo_energy_j_by_cell": off["final_photo_j"].tolist(),
            "available_energy_j_by_cell": off_distribution.tolist(),
            "step_records": off["records"],
        },
        "with_transport": {
            "background_energy_j_by_cell": on["final_background_j"].tolist(),
            "photo_energy_j_by_cell": on["final_photo_j"].tolist(),
            "available_energy_j_by_cell": on_distribution.tolist(),
            "step_records": on["records"],
        },
        "comparison": {
            "max_abs_final_cell_distribution_difference_j": float(np.max(np.abs(on_distribution - off_distribution))),
            "final_total_available_energy_without_transport_j": float(np.sum(off_distribution)),
            "final_total_available_energy_with_transport_j": float(np.sum(on_distribution)),
            "final_temperature_linf_difference_k": thermal_difference,
            "transport_changes_spatial_distribution": bool(np.any(on_distribution != off_distribution)),
            "interpretation": "THERMAL_PATHS_MATCH; DEEP_DISTRIBUTION_DIFFERS; TOTAL MAY DIFFER DUE CELLWISE UPTAKE",
        },
        "measurements": {
            "elapsed_seconds_both_branches": elapsed,
            "tracemalloc_peak_bytes": peak_python_bytes,
            "tracemalloc_scope": "PYTHON_ALLOCATIONS_ONLY_NOT_PROCESS_RSS",
            "steps_per_branch": steps,
            "records_total": len(off["records"]) + len(on["records"]),
            "output_bytes": None,
        },
        "claim_limit": "NO_GEOLOGICAL_DFEU_SOLAR_FLUX_POPULATION_OR_BIDIRECTIONAL_PHYSICAL_COUPLING_QUALIFIED",
    }
