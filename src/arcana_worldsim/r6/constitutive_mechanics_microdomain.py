"""Short layered-continuum mechanics experiment on the verified C028/C029 T0 pair.

The constitutive law and interface stiffness are synthetic. The two columns are
1-D layered bars in the boundary-normal direction; this is not a 2-D/3-D
geological contact solver and does not establish positive-time B5 kinematics.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import threading
from time import perf_counter, sleep
import tracemalloc
from typing import Any, Mapping

import numpy as np

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class _ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    _KERNEL32 = ctypes.windll.kernel32
    _PSAPI = ctypes.windll.psapi
    _KERNEL32.GetCurrentProcess.restype = wintypes.HANDLE
    _PSAPI.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters), wintypes.DWORD)
    _PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL

from .functional_development import ReducedState, pure_shear_thermal_step
from .integrated_geological_microdomain import (
    ARCHIVE_SHA256, _column_geometry, _deep_transport_step, _modal_response_by_role,
    _state_digest, load_microdomain_inputs,
)
from .material_rheology_provider import evaluate_reduced_state_column
from .tectonic_boundary_microdomain import build_t0_boundary_binding
from .tectonic_deep_pilot import SECONDS_PER_YEAR, conservative_two_cell_transport

DEFAULT_CONSTITUTIVE_CONFIG: dict[str, Any] = {
    "load_increments_m": [0.01, 0.01, 0.01],
    "step_years": 1.0,
    "strike_length_m": 1.0,
    "young_modulus_pa_by_role": {
        "CONTINENTAL_CRUST_REFERENCE": 30.0e9,
        "LITHOSPHERIC_MANTLE_REFERENCE": 70.0e9,
    },
    "maxwell_viscosity_pa_s_by_role": {
        "CONTINENTAL_CRUST_REFERENCE": 2.0e19,
        "LITHOSPHERIC_MANTLE_REFERENCE": 4.0e19,
    },
    "interface_normal_stiffness_pa_per_m": 1.0e12,
    "deep_vertical_mobility_per_year": 0.01,
    "deep_initial_density_j_m3_by_role": {
        "CONTINENTAL_CRUST_REFERENCE": 1.0,
        "LITHOSPHERIC_MANTLE_REFERENCE": 0.25,
    },
    "support_b_deep_stock_multiplier": 1.10,
    "lateral_deep_base_fraction_per_step": 0.05,
    "lateral_deep_gap_gain_per_m": 10.0,
}


def _read_process_rss_bytes() -> int | None:
    """Best-effort current RSS on Windows/Linux without requiring psutil."""
    if os.name == "nt":
        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        try:
            process = _KERNEL32.GetCurrentProcess()
            if _PSAPI.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        except OSError:
            return None
        return None
    if os.name == "posix":
        try:
            for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
        except (OSError, ValueError, IndexError):
            return None
    return None


class _RssSampler:
    def __init__(self, interval_s: float = 0.1):
        self.interval_s = interval_s
        self.samples: list[int] = []
        self.errors = 0
        self.error_types: list[str] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self._stop.is_set():
            try:
                value = _read_process_rss_bytes()
            except Exception as exc:
                self.errors += 1
                self.error_types.append(type(exc).__name__)
            else:
                if value is None:
                    self.errors += 1
                    self.error_types.append("RSS_UNAVAILABLE")
                else:
                    self.samples.append(value)
            self._stop.wait(self.interval_s)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_exc):
        self._stop.set()
        self._thread.join()

    def summary(self) -> dict[str, Any]:
        return {"method": "SAMPLED_CURRENT_PROCESS_RSS", "sample_interval_seconds": self.interval_s,
                "sample_count": len(self.samples), "sample_errors": self.errors,
                "sample_error_types": list(self.error_types),
                "initial_rss_bytes": self.samples[0] if self.samples else None,
                "peak_sampled_rss_bytes": max(self.samples) if self.samples else None,
                "final_rss_bytes": self.samples[-1] if self.samples else None,
                "is_process_tree_or_os_hard_limit": False}


def _effective_column(cells: list[dict[str, Any]], *, strike_length_m: float, dt_s: float, model: str,
                      young_by_role: Mapping[str, float], eta_by_role: Mapping[str, float],
                      viscous_strain: Mapping[str, float],
                      young_by_cell: Mapping[str, float] | None = None,
                      eta_by_cell: Mapping[str, float] | None = None) -> tuple[float, float, dict[str, float], dict[str, float]]:
    stiffness = 0.0
    history_force = 0.0
    areas: dict[str, float] = {}
    effective_modulus: dict[str, float] = {}
    for cell in cells:
        cell_id, role = cell["cell_id"], cell["material_role_id"]
        area = cell["control_volume_thickness_m"] * strike_length_m
        young = float((young_by_cell or {}).get(cell_id, young_by_role[role]))
        if not math.isfinite(young) or young <= 0:
            raise ValueError("SYNTHETIC_YOUNG_MODULUS_INVALID")
        if model == "ELASTIC":
            eff = young
            old_ev = 0.0
        elif model == "MAXWELL":
            eta = float((eta_by_cell or {}).get(cell_id, eta_by_role[role]))
            if not math.isfinite(eta) or eta <= 0:
                raise ValueError("SYNTHETIC_VISCOSITY_INVALID")
            eff = young / (1.0 + young * dt_s / eta)
            old_ev = float(viscous_strain.get(cell_id, 0.0))
        else:
            raise ValueError("CONSTITUTIVE_MODEL_UNKNOWN")
        stiffness += eff * area
        history_force += eff * old_ev * area
        areas[cell_id] = area
        effective_modulus[cell_id] = eff
    if not math.isfinite(stiffness) or stiffness <= 0:
        raise ValueError("CONTINUUM_COLUMN_STIFFNESS_INVALID")
    return stiffness, history_force, areas, effective_modulus


def solve_layered_interface_increment(
    cells_a: list[dict[str, Any]], cells_b: list[dict[str, Any]], *,
    reference_width_a_m: float, reference_width_b_m: float,
    lithosphere_a_m: float, lithosphere_b_m: float,
    strike_length_m: float, interface_stiffness_pa_per_m: float,
    opening_total_m: float, opening_increment_m: float, dt_s: float,
    young_by_role: Mapping[str, float], eta_by_role: Mapping[str, float],
    model: str, viscous_strain: dict[str, float],
    previous_total_strain: Mapping[str, float],
    previous_displacement_a_m: float, previous_displacement_b_m: float,
    previous_interface_gap_m: float, previous_stored_energy_j: float,
    young_by_cell: Mapping[str, float] | None = None,
    eta_by_cell: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Solve quasi-static 1-D layered bars plus a linear bonded interface.

    Nodal control volumes act in parallel across the column section. Maxwell
    material updates use backward Euler; the resulting algorithmic energy term
    is reported separately from viscous dissipation.
    """
    scalar_inputs = (reference_width_a_m, reference_width_b_m, lithosphere_a_m,
                     lithosphere_b_m, strike_length_m, interface_stiffness_pa_per_m,
                     opening_total_m, opening_increment_m, dt_s)
    if any(not math.isfinite(x) for x in scalar_inputs) or min(
            reference_width_a_m, reference_width_b_m, lithosphere_a_m,
            lithosphere_b_m, strike_length_m, interface_stiffness_pa_per_m, dt_s) <= 0:
        raise ValueError("CONTINUUM_MECHANICS_INPUT_INVALID")
    if any(not math.isfinite(x) for x in (previous_displacement_a_m, previous_displacement_b_m,
                                          previous_interface_gap_m, previous_stored_energy_j)):
        raise ValueError("CONTINUUM_MECHANICS_HISTORY_INVALID")
    if set(young_by_role) != set(eta_by_role) or any(
            not math.isfinite(float(v)) or float(v) <= 0 for v in (*young_by_role.values(), *eta_by_role.values())):
        raise ValueError("CONTINUUM_MATERIAL_PARAMETER_MAP_INVALID")
    dt_by_seconds = dt_s
    ka, ha, areas_a, e_eff_a = _effective_column(
        cells_a, strike_length_m=strike_length_m,
        dt_s=dt_by_seconds, model=model, young_by_role=young_by_role,
        eta_by_role=eta_by_role, viscous_strain=viscous_strain,
        young_by_cell=young_by_cell, eta_by_cell=eta_by_cell,
    )
    kb, hb, areas_b, e_eff_b = _effective_column(
        cells_b, strike_length_m=strike_length_m,
        dt_s=dt_by_seconds, model=model, young_by_role=young_by_role,
        eta_by_role=eta_by_role, viscous_strain=viscous_strain,
        young_by_cell=young_by_cell, eta_by_cell=eta_by_cell,
    )
    interface_area = min(lithosphere_a_m, lithosphere_b_m) * strike_length_m
    interface_k = interface_stiffness_pa_per_m * interface_area
    compliance_a, compliance_b = reference_width_a_m / ka, reference_width_b_m / kb
    offset_a, offset_b = reference_width_a_m * ha / ka, reference_width_b_m * hb / kb
    force = (opening_total_m - offset_a - offset_b) / (compliance_a + compliance_b + 1.0 / interface_k)
    strain_a, strain_b = (force + ha) / ka, (force + hb) / kb
    displacement_a, displacement_b = reference_width_a_m * strain_a, reference_width_b_m * strain_b
    gap = force / interface_k
    stresses: dict[str, float] = {}
    new_viscous = dict(viscous_strain)
    elastic_energy = 0.0
    viscous_dissipation = 0.0
    algorithmic_dissipation = 0.0
    force_a = force_b = 0.0
    for cells, areas, effective, strain, width, which in (
            (cells_a, areas_a, e_eff_a, strain_a, reference_width_a_m, "a"),
            (cells_b, areas_b, e_eff_b, strain_b, reference_width_b_m, "b")):
        for cell in cells:
            cid, role = cell["cell_id"], cell["material_role_id"]
            area = areas[cid]
            young = float((young_by_cell or {}).get(cid, young_by_role[role]))
            old_ev = float(viscous_strain.get(cid, 0.0)) if model == "MAXWELL" else 0.0
            stress = effective[cid] * (strain - old_ev)
            if model == "MAXWELL":
                eta = float((eta_by_cell or {}).get(cid, eta_by_role[role]))
                new_ev = old_ev + stress * dt_s / eta
                new_viscous[cid] = new_ev
                viscous_dissipation += eta * ((new_ev - old_ev) / dt_s) ** 2 * area * width * dt_s
            else:
                new_ev = 0.0
            old_elastic = float(previous_total_strain.get(cid, 0.0)) - old_ev
            new_elastic = strain - new_ev
            volume_ref = area * width
            elastic_energy += 0.5 * young * new_elastic ** 2 * volume_ref
            algorithmic_dissipation += 0.5 * young * (new_elastic - old_elastic) ** 2 * volume_ref
            stresses[cid] = stress
            if which == "a":
                force_a += stress * area
            else:
                force_b += stress * area
    interface_energy = 0.5 * interface_k * gap * gap
    algorithmic_dissipation += 0.5 * interface_k * (gap - previous_interface_gap_m) ** 2
    # Mechanical work uses the endpoint-force convention; its exact discrete
    # balance includes the explicitly reported algorithmic dissipation above.
    work_increment = force * opening_increment_m
    stored_energy = elastic_energy + interface_energy
    delta_energy = stored_energy - previous_stored_energy_j
    residual = work_increment - delta_energy - viscous_dissipation - algorithmic_dissipation
    if not math.isfinite(residual) or abs(residual) > max(1e-5, abs(work_increment) * 1e-9):
        raise ValueError("CONTINUUM_MECHANICAL_ENERGY_BALANCE_FAILED")
    return {
        "model": model, "opening_total_m": opening_total_m,
        "opening_increment_m": opening_increment_m,
        "column_a_displacement_total_m": displacement_a,
        "column_b_displacement_total_m": displacement_b,
        "column_a_displacement_increment_m": displacement_a - previous_displacement_a_m,
        "column_b_displacement_increment_m": displacement_b - previous_displacement_b_m,
        "interface_gap_total_m": gap,
        "interface_gap_increment_m": gap - previous_interface_gap_m,
        "interface_force_n": force,
        "interface_stress_pa": force / interface_area,
        "interface_area_m2": interface_area,
        "interface_traction_law": "SYNTHETIC_LINEAR_BONDED_NORMAL_TRACTION_SEPARATION_NO_FRICTION_OR_DAMAGE",
        "column_a_force_balance_residual_n": force_a - force,
        "column_b_force_balance_residual_n": force_b - force,
        "stress_pa_by_material_cell": stresses,
        "strain_by_support": {"R6G1D-R091-C028": strain_a, "R6G1D-R091-C029": strain_b},
        "updated_total_strain": {cid: strain_a for cid in areas_a} | {cid: strain_b for cid in areas_b},
        "elastic_energy_j": elastic_energy,
        "interface_energy_j": interface_energy,
        "stored_energy_j": stored_energy,
        "stored_energy_change_j": delta_energy,
        "viscous_dissipation_increment_j": viscous_dissipation,
        "algorithmic_energy_increment_j": algorithmic_dissipation,
        "external_work_increment_j": work_increment,
        "energy_balance_residual_j": residual,
        "updated_viscous_strain": new_viscous,
    }


def _uncoupled_mechanics(opening_increment_m: float, previous_a: float, previous_b: float) -> dict[str, Any]:
    da = db = opening_increment_m / 2.0
    return {"model": "NO_MECHANICAL_COUPLING_PRESCRIBED_HALF_OPENING",
            "opening_increment_m": opening_increment_m,
            "column_a_displacement_increment_m": da,
            "column_b_displacement_increment_m": db,
            "column_a_displacement_total_m": previous_a + da,
            "column_b_displacement_total_m": previous_b + db,
            "interface_force_n": None, "interface_stress_pa": None,
            "elastic_energy_j": 0.0, "interface_energy_j": 0.0,
            "viscous_dissipation_increment_j": 0.0, "algorithmic_energy_increment_j": 0.0,
            "external_work_increment_j": None, "energy_balance_residual_j": None,
            "strain_by_support": None}


def _run_variant(loaded, binding, config, model: str, lateral: bool, timings: dict[str, float],
                 *, case_id: str | None = None,
                 young_by_cell: Mapping[str, float] | None = None,
                 eta_by_cell: Mapping[str, float] | None = None):
    supports = [meta["support_id"] for _, meta in loaded]
    states = {meta["support_id"]: state for state, meta in loaded}
    initial = dict(states)
    start = perf_counter()
    cells = {support: _column_geometry(state, support, config["strike_length_m"])
             for support, state in states.items()}
    mechanical_reference_cells = cells
    timings["microdomain_creation_seconds"] += perf_counter() - start
    stocks = {cell["cell_id"]: config["deep_initial_density_j_m3_by_role"][cell["material_role_id"]]
              * cell["volume_m3"] * (config["support_b_deep_stock_multiplier"] if cell["support_id"] == supports[1] else 1.0)
              for rows in cells.values() for cell in rows}
    inventory_initial = sum(stocks.values())
    history = {cell_id: 0.0 for cell_id in stocks}
    strain_history = {cell_id: 0.0 for cell_id in stocks}
    cumulative_opening = 0.0
    displacement = {support: 0.0 for support in supports}
    gap = 0.0
    stored_energy = 0.0
    records = []
    for index, opening_increment in enumerate(config["load_increments_m"], start=1):
        cumulative_opening += opening_increment
        mechanical_start = perf_counter()
        if model == "UNCOUPLED":
            mech = _uncoupled_mechanics(opening_increment, displacement[supports[0]], displacement[supports[1]])
        else:
            mech = solve_layered_interface_increment(
                mechanical_reference_cells[supports[0]], mechanical_reference_cells[supports[1]],
                reference_width_a_m=initial[supports[0]].initial_width_m,
                reference_width_b_m=initial[supports[1]].initial_width_m,
                lithosphere_a_m=initial[supports[0]].initial_lithosphere_m,
                lithosphere_b_m=initial[supports[1]].initial_lithosphere_m,
                strike_length_m=config["strike_length_m"],
                interface_stiffness_pa_per_m=config["interface_normal_stiffness_pa_per_m"],
                opening_total_m=cumulative_opening, opening_increment_m=opening_increment,
                dt_s=config["step_years"] * SECONDS_PER_YEAR,
                young_by_role=config["young_modulus_pa_by_role"],
                eta_by_role=config["maxwell_viscosity_pa_s_by_role"], model=model,
                viscous_strain=history,
                previous_total_strain=strain_history,
                previous_displacement_a_m=displacement[supports[0]],
                previous_displacement_b_m=displacement[supports[1]],
                previous_interface_gap_m=gap,
                previous_stored_energy_j=stored_energy,
                young_by_cell=young_by_cell, eta_by_cell=eta_by_cell,
            )
            history = mech.pop("updated_viscous_strain")
            strain_history = mech.pop("updated_total_strain")
            gap = mech["interface_gap_total_m"]
            stored_energy = mech["stored_energy_j"]
        timings["mechanics_seconds"] += perf_counter() - mechanical_start
        next_states = {}
        thermal_start = perf_counter()
        for support, key in ((supports[0], "column_a_displacement_increment_m"),
                              (supports[1], "column_b_displacement_increment_m")):
            extension_m = float(mech[key])
            if extension_m < -1e-12:
                raise ValueError("THERMAL_KERNEL_COMPRESSION_UNSUPPORTED; mechanical unload remains separately testable")
            step_state, _diag = pure_shear_thermal_step(
                states[support], duration_s=config["step_years"] * SECONDS_PER_YEAR,
                extension_velocity_m_s=max(0.0, extension_m) / (config["step_years"] * SECONDS_PER_YEAR),
            )
            next_states[support] = step_state
            displacement[support] = step_state.width_m - initial[support].initial_width_m
        timings["thermal_seconds"] += perf_counter() - thermal_start
        states = next_states
        start_deep = perf_counter()
        cells = {support: _column_geometry(state, support, config["strike_length_m"])
                 for support, state in states.items()}
        before_deep = sum(stocks.values())
        stocks, vertical = _deep_transport_step(
            cells, stocks, dt_years=config["step_years"],
            mobility_per_year=config["deep_vertical_mobility_per_year"],
            response_by_role=_modal_response_by_role(),
        )
        lateral_records = []
        if lateral:
            for left, right in zip(cells[supports[0]], cells[supports[1]]):
                if left["node_index_zero_based"] != right["node_index_zero_based"]:
                    raise ValueError("EXPERIMENTAL_LATERAL_NODE_MAPPING_INVALID")
                fraction = config["lateral_deep_base_fraction_per_step"] * (
                    1.0 + config["lateral_deep_gap_gain_per_m"] * abs(gap))
                pair = (left["cell_id"], right["cell_id"])
                updated, transfer = conservative_two_cell_transport(
                    np.asarray((stocks[pair[0]], stocks[pair[1]])), fraction)
                stocks[pair[0]], stocks[pair[1]] = map(float, updated)
                lateral_records.append({"cell_a": pair[0], "cell_b": pair[1],
                                        "transfer_a_to_b_j": transfer, "fraction": fraction})
        timings["deep_seconds"] += perf_counter() - start_deep
        after_deep = sum(stocks.values())
        if any(not math.isfinite(v) or v < 0 for v in stocks.values()) or not math.isclose(
                before_deep, after_deep, rel_tol=1e-13, abs_tol=1e-7):
            raise ValueError("DEEP_INVENTORY_CONSERVATION_FAILED")
        records.append({"step": index, "time_years": index * config["step_years"],
                        "mechanics": mech,
                        "mechanical_state_after": {
                            "total_strain_by_cell": dict(strain_history) if model != "UNCOUPLED" else None,
                            "viscous_strain_by_cell": dict(history) if model == "MAXWELL" else None,
                            "constitutive_state_status": ("SYNTHETIC_MAXWELL_INTERNAL_STATE" if model == "MAXWELL"
                                                           else "SYNTHETIC_ELASTIC_NO_INTERNAL_MEMORY" if model == "ELASTIC"
                                                           else "NO_COUPLED_CONSTITUTIVE_STATE"),
                        },
                        "thermal_final_state_sha256": {sid: _state_digest(s) for sid, s in states.items()},
                        "thermal_width_m": {sid: s.width_m for sid, s in states.items()},
                        "thermal_strain_delta": {sid: s.accumulated_strain - initial[sid].accumulated_strain for sid, s in states.items()},
                        "deep": {"inventory_before_j": before_deep, "inventory_after_j": after_deep,
                                 "conservation_residual_j": after_deep - before_deep,
                                 "vertical_interfaces": len(vertical),
                                 "lateral_interfaces": len(lateral_records),
                                 "lateral_transfers": lateral_records,
                                 "thermal_to_deep_j": 0.0, "mechanical_work_to_deep_j": 0.0}})
    return {"case_id": case_id or model,
            "model": model, "lateral_deep_mode": "SYNTHETIC_STRUCTURE_MODULATED" if lateral else "BLOCKED",
            "steps": records, "initial_inventory_j": inventory_initial,
            "final_inventory_j": sum(stocks.values()),
            "deep_conservation_residual_j": sum(stocks.values()) - inventory_initial,
            "state_initial": {sid: s.payload() for sid, s in initial.items()},
            "state_final": {sid: s.payload() for sid, s in states.items()},
            "state_initial_sha256": {sid: _state_digest(s) for sid, s in initial.items()},
            "state_final_sha256": {sid: _state_digest(s) for sid, s in states.items()},
            "material_role_ids_preserved": {sid: [m.role_id for m in initial[sid].materials]
                                            == [m.role_id for m in states[sid].materials] for sid in supports},
            "binding_boundary_id": binding["boundary"]["boundary_id"]}


def run_constitutive_microdomain(repository_root: str | Path, external_root: str | Path,
                                 archive_path: str | Path,
                                 config: Mapping[str, Any] | None = None,
                                 *, boundary_view_cache_path: str | Path | None = None) -> dict[str, Any]:
    cfg = dict(DEFAULT_CONSTITUTIVE_CONFIG if config is None else config)
    if set(cfg) != set(DEFAULT_CONSTITUTIVE_CONFIG):
        raise ValueError("CONSTITUTIVE_CONFIG_KEYS_INVALID")
    increments = cfg["load_increments_m"]
    if not isinstance(increments, list) or not increments or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0
            for x in increments):
        raise ValueError("THERMAL_COUPLING_REQUIRES_NONNEGATIVE_FINITE_LOAD_INCREMENTS")
    if any(not math.isfinite(cfg[k]) or cfg[k] <= 0 for k in (
            "step_years", "strike_length_m", "interface_normal_stiffness_pa_per_m")):
        raise ValueError("CONSTITUTIVE_SCALAR_CONFIGURATION_INVALID")
    for name in ("young_modulus_pa_by_role", "maxwell_viscosity_pa_s_by_role"):
        mapping = cfg[name]
        if not isinstance(mapping, dict) or not mapping or any(
                not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(value) or value <= 0 for value in mapping.values()):
            raise ValueError("CONSTITUTIVE_MATERIAL_CONFIG_INVALID")
    density = cfg["deep_initial_density_j_m3_by_role"]
    if not isinstance(density, dict) or not density or any(
            not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value) or value < 0 for value in density.values()):
        raise ValueError("CONSTITUTIVE_DEEP_DENSITY_CONFIG_INVALID")
    if (not math.isfinite(cfg["deep_vertical_mobility_per_year"])
            or cfg["deep_vertical_mobility_per_year"] < 0
            or not math.isfinite(cfg["support_b_deep_stock_multiplier"])
            or cfg["support_b_deep_stock_multiplier"] <= 0
            or not 0 <= cfg["lateral_deep_base_fraction_per_step"] <= 0.5
            or not math.isfinite(cfg["lateral_deep_gap_gain_per_m"])
            or cfg["lateral_deep_gap_gain_per_m"] < 0):
        raise ValueError("CONSTITUTIVE_DEEP_CONFIG_INVALID")
    if len(increments) * cfg["step_years"] > 100:
        raise ValueError("CONSTITUTIVE_EXPERIMENT_EXCEEDS_SHORT_PILOT_SCOPE")
    timings = {key: 0.0 for key in ("archive_read_verify_seconds", "topology_binding_seconds",
                                    "microdomain_creation_seconds", "mechanics_seconds",
                                    "thermal_evolution_seconds", "deep_evolution_seconds")}
    boundary_cache_timings: dict[str, Any] = {}
    started = perf_counter()
    tracemalloc.start()
    sampler = _RssSampler()
    with sampler:
        t = perf_counter()
        loaded, archive_digest = load_microdomain_inputs(str(archive_path))
        timings["archive_read_verify_seconds"] = perf_counter() - t
        if archive_digest != ARCHIVE_SHA256:
            raise ValueError("ENG10K_ARCHIVE_IDENTITY_MISMATCH")
        t = perf_counter()
        binding = build_t0_boundary_binding(repository_root, external_root, archive_path,
                                            loaded_inputs=loaded,
                                            verified_archive_digest=archive_digest,
                                            cache_path=boundary_view_cache_path,
                                            cache_timings=boundary_cache_timings)
        timings["topology_binding_seconds"] = perf_counter() - t
        if len(loaded) != 2 or any(meta["time_s"] != 0.0 for _, meta in loaded):
            raise ValueError("EXPECTED_TWO_T0_SUPPORT_STATES")
        cases = []
        for case_id, model, lateral in (("UNCoupled_reference", "UNCOUPLED", False),
                                        ("ELASTIC_sensitivity", "ELASTIC", False),
                                        ("MAXWELL_constant_synthetic", "MAXWELL", False),
                                        ("MAXWELL_synthetic_lateral_deep_sensitivity", "MAXWELL", True)):
            case_timings = {"microdomain_creation_seconds": 0.0, "mechanics_seconds": 0.0,
                            "thermal_seconds": 0.0, "deep_seconds": 0.0}
            case = _run_variant(loaded, binding, cfg, model, lateral, case_timings, case_id=case_id)
            timings["microdomain_creation_seconds"] += case_timings["microdomain_creation_seconds"]
            timings["mechanics_seconds"] += case_timings["mechanics_seconds"]
            timings["thermal_evolution_seconds"] += case_timings["thermal_seconds"]
            timings["deep_evolution_seconds"] += case_timings["deep_seconds"]
            cases.append(case)

        initial_widths = {meta["support_id"]: state.initial_width_m for state, meta in loaded}
        mean_strain_rate_s = (sum(float(v) for v in cfg["load_increments_m"])
                              / sum(initial_widths.values())
                              / (len(cfg["load_increments_m"]) * cfg["step_years"] * SECONDS_PER_YEAR))
        provider_profiles: dict[str, dict[str, Any]] = {}
        provider_maps: dict[float, tuple[dict[str, float], dict[str, float]]] = {}
        for offset_k in (0.0, 100.0):
            young_by_cell: dict[str, float] = {}
            eta_by_cell: dict[str, float] = {}
            support_profiles = {}
            for state, meta in loaded:
                support = meta["support_id"]
                cells = _column_geometry(state, support, cfg["strike_length_m"])
                profile = evaluate_reduced_state_column(
                    state, cells, support_id=support,
                    strain_rate_s=mean_strain_rate_s, temperature_offset_k=offset_k)
                young_by_cell.update(profile["young_modulus_pa_by_cell"])
                eta_by_cell.update(profile["eta_1d_pa_s_by_cell"])
                support_profiles[support] = profile
            provider_profiles[f"temperature_offset_{offset_k:g}_k"] = support_profiles
            provider_maps[offset_k] = (young_by_cell, eta_by_cell)
        for offset_k in (0.0, 100.0):
            case_timings = {"microdomain_creation_seconds": 0.0, "mechanics_seconds": 0.0,
                            "thermal_seconds": 0.0, "deep_seconds": 0.0}
            young_by_cell, eta_by_cell = provider_maps[offset_k]
            case = _run_variant(
                loaded, binding, cfg, "MAXWELL", False, case_timings,
                case_id=("MAXWELL_dry_olivine_benchmark" if offset_k == 0.0
                         else "MAXWELL_dry_olivine_benchmark_T_plus_100K"),
                young_by_cell=young_by_cell, eta_by_cell=eta_by_cell)
            case["rheology_temperature_offset_k"] = offset_k
            case["rheology_authority"] = "LITERATURE_BENCHMARK_NOT_R6_MATERIAL_CALIBRATION"
            timings["microdomain_creation_seconds"] += case_timings["microdomain_creation_seconds"]
            timings["mechanics_seconds"] += case_timings["mechanics_seconds"]
            timings["thermal_evolution_seconds"] += case_timings["thermal_seconds"]
            timings["deep_evolution_seconds"] += case_timings["deep_seconds"]
            cases.append(case)
        _, peak_python = tracemalloc.get_traced_memory()
        rss = sampler.summary()
    tracemalloc.stop()
    return {"schema": "ARCANA_CONSTITUTIVE_MECHANICS_MICRODOMAIN_V1",
            "scope": "NONCANONICAL_SYNTHETIC_LAYERED_CONTINUUM_ENGINEERING_EXPERIMENT",
            "t0_boundary_binding": binding,
            "boundary_view_cache": {"path": str(Path(boundary_view_cache_path).resolve())
                                      if boundary_view_cache_path is not None else None,
                                      "timings": boundary_cache_timings,
                                      "rebuilds_global_b5_topology_on_verified_reuse": False},
            "rheology_provider": {
                "schema": "ARCANA_R6_MATERIAL_RHEOLOGY_BENCHMARK_ADAPTER_V1",
                "law": "ASPECT_STYLE_DRY_OLIVINE_DISLOCATION_CREEP",
                "benchmark_provenance": "Hirth_Kohlstedt_2003_parameters_as_documented_by_ASPECT",
                "inputs_from_r6": ["temperature_k", "rho_kg_m3", "material_coordinate_xi", "lithosphere_m"],
                "pressure": "DERIVED_LITHOSTATIC_PROXY_RHO_G_Z_NOT_AN_ARCHIVED_PRESSURE",
                "strain_rate_s": mean_strain_rate_s,
                "strain_rate_method": "TOTAL_PRESCRIBED_OPENING / SUM_INITIAL_COLUMN_WIDTHS / TOTAL_STEP_DURATION",
                "temperature_contrast_k": 100.0,
                "temperature_contrast_applies_to": "CONSTITUTIVE_EVALUATION_ONLY; THERMAL_STATE_AND_KERNEL_UNCHANGED",
                "material_role_to_mineralogy": "UNKNOWN; BENCHMARK_NOT_ASSIGNED_TO_C028_C029_LITHOLOGY",
                "profile_by_offset": provider_profiles,
            },
            "configuration": {**cfg,
                "young_modulus_authority": "SYNTHETIC_BY_ROLE; NOT_PRESENT_IN_ARCHIVE_MATERIAL_RECORDS",
                "viscosity_authority": "SYNTHETIC_MAXWELL_BY_ROLE",
                "interface_law": "SYNTHETIC_LINEAR_BONDED_TRACTION_SEPARATION_NO_UNILATERAL_CONTACT",
                "interface_area": "MINIMUM_CURRENT_LITHOSPHERE_THICKNESS_TIMES_DECLARED_STRIKE_LENGTH",
                "prescribed_opening": "ENGINEERING_DISPLACEMENT_SCHEDULE_NOT_EXTENDED_B5_KINEMATICS",
                "thermal_kernel_compression": "UNSUPPORTED; NEGATIVE_INCREMENT_REJECTED",
                "deep_lateral_default": "BLOCKED; ONE_EXPLICIT_MAXWELL_SENSITIVITY_CASE"},
            "cases": cases,
            "measurements": {"stage_timings_seconds": timings,
                "elapsed_seconds_before_output_serialization": perf_counter() - started,
                "python_tracemalloc_peak_bytes": peak_python,
                "process_memory": rss,
                "rss_is_sampled_not_hard_limit": True,
                "case_count": len(cases), "step_count_per_case": len(increments)},
            "claim_limit": "SYNTHETIC_LAYERED_CONTINUUM_AND_T0_TOPOLOGY_ONLY; NO_GEOLOGICAL_CONSTITUTIVE_QUALIFICATION"}
