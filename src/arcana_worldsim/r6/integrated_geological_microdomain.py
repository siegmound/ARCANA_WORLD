"""Two-column ENG10K material/thermal/Deep microdomain engineering pilot.

The thermal kernel and archived ReducedState records are real R6 inputs. The
Deep inventory, modal response, access proxy, mobility, and vertical transfer
law are explicitly synthetic. B4/B5 do not bind these R6G1D supports to a
plate-face topology or define a material-contact law, so no lateral interface
is created between the columns.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
import tracemalloc
from time import perf_counter
from typing import Any

from .deep_geological_physics_pilot import ModalMaterial, RoleModalParameters
from .functional_development import ReducedState, pure_shear_thermal_step
from .tectonic_deep_pilot import (
    DEFAULT_SOURCE_ARCHIVE_MEMBER,
    SECONDS_PER_YEAR,
    _control_volume_widths,
    load_archived_state_jsonl,
)

ARCHIVE_SHA256 = "7dda60c8fa1f535d9e257eb2d04fdfde4643a92765eca8631bd766058240d8cb"
SUPPORT_RECORDS = (
    ("R6G1D-R091-C028", "DIRECT-f0.001-R6G1D-R091-C028", 12),
    ("R6G1D-R091-C029", "DIRECT-f0.001-R6G1D-R091-C029", 0),
)
ROLE_MODAL_PARAMETERS = (
    RoleModalParameters("CONTINENTAL_CRUST_REFERENCE", 0.6, 0.3, 0.05),
    RoleModalParameters("LITHOSPHERIC_MANTLE_REFERENCE", 0.8, 0.2, 0.08),
)
DEFAULT_SYNTHETIC_DEEP_DENSITY_BY_ROLE = {
    "CONTINENTAL_CRUST_REFERENCE": 1.0,
    "LITHOSPHERIC_MANTLE_REFERENCE": 0.25,
}
SCOPE = "NONCANONICAL_TWO_COLUMN_ENGINEERING_MICRODOMAIN"


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _state_digest(state: ReducedState) -> str:
    return _sha256_json(state.payload())


def load_microdomain_inputs(archive_path: str) -> tuple[list[tuple[ReducedState, dict[str, Any]]], str]:
    """Load exactly the two declared time-zero archive records, without extraction."""
    loaded = []
    for support_id, trajectory_id, sequence in SUPPORT_RECORDS:
        state, meta = load_archived_state_jsonl(
            archive_path, member=DEFAULT_SOURCE_ARCHIVE_MEMBER,
            trajectory_id=trajectory_id, sequence=sequence,
        )
        if meta["support_id"] != support_id or meta["time_s"] != 0.0:
            raise ValueError("MICRODOMAIN_ARCHIVE_SUPPORT_OR_TIME_MISMATCH")
        if len(state.temperature_k) != 73:
            raise ValueError("MICRODOMAIN_REQUIRES_73_NODE_ARCHIVED_COLUMNS")
        loaded.append((state, meta))
    digests = {meta["archive_sha256"] for _, meta in loaded}
    if len(digests) != 1:
        raise ValueError("MICRODOMAIN_ARCHIVE_IDENTITY_MISMATCH")
    archive_digest = digests.pop()
    if archive_digest != ARCHIVE_SHA256:
        raise ValueError("MICRODOMAIN_ARCHIVE_SHA256_MISMATCH")
    return loaded, archive_digest


def _modal_response_by_role() -> dict[str, float]:
    params = {row.role_id: row for row in ROLE_MODAL_PARAMETERS}
    responses = {}
    for role, row in params.items():
        material = ModalMaterial(role, 1.0, 1.0, 1.0,
                                 row.coupling, row.detuning, row.loss,
                                 row.modal_parameter_authority if hasattr(row, "modal_parameter_authority")
                                 else "SYNTHETIC_ENGINEERING_PARAMETER")
        responses[role] = material.modal_response()
    return responses


def _column_geometry(state: ReducedState, support_id: str, strike_length_m: float) -> list[dict[str, Any]]:
    if not math.isfinite(strike_length_m) or strike_length_m <= 0:
        raise ValueError("MICRODOMAIN_STRIKE_LENGTH_INVALID")
    n = len(state.temperature_k)
    if n != 73 or len(state.materials) != n or len(state.material_coordinate) != n:
        raise ValueError("MICRODOMAIN_COLUMN_CARDINALITY_INVALID")
    dz = _control_volume_widths(state)
    if any(not math.isfinite(value) or value <= 0 for value in dz):
        raise ValueError("MICRODOMAIN_CONTROL_VOLUME_INVALID")
    cells = []
    for index, (thickness, material, temperature, xi) in enumerate(zip(
            dz, state.materials, state.temperature_k, state.material_coordinate)):
        volume = state.width_m * strike_length_m * thickness
        if not math.isfinite(volume) or volume <= 0:
            raise ValueError("MICRODOMAIN_CELL_VOLUME_INVALID")
        cells.append({
            "cell_id": f"{support_id}:COLUMN:NODE{index:03d}",
            "support_id": support_id,
            "material_id": None,
            "material_id_status": "UNKNOWN_ARCHIVE_BINDS_ROLE_ID_NOT_SEPARATE_MATERIAL_ID",
            "material_role_id": material.role_id,
            "node_index_zero_based": index,
            "material_coordinate_xi": xi,
            "coordinate_z_m": xi * state.lithosphere_m,
            "control_volume_thickness_m": thickness,
            "cross_section_area_m2": state.width_m * strike_length_m,
            "volume_m3": volume,
            "rho_kg_m3": material.rho_kg_m3,
            "cp_j_kg_k": material.cp_j_kg_k,
            "k_w_m_k": material.k_w_m_k,
            "radiogenic_w_m3": material.radiogenic_w_m3,
            "temperature_k": temperature,
        })
    return cells


def _vertical_interfaces(cells_by_support: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    edges = []
    for support_id, cells in cells_by_support.items():
        for index, (left, right) in enumerate(zip(cells, cells[1:])):
            if right["coordinate_z_m"] <= left["coordinate_z_m"]:
                raise ValueError("MICRODOMAIN_VERTICAL_COORDINATE_ORDER_INVALID")
            edges.append({
                "interface_id": f"{support_id}:VERTICAL:{index:03d}-{index + 1:03d}",
                "support_id": support_id,
                "cell_a": left["cell_id"],
                "cell_b": right["cell_id"],
                "kind": "ADJACENT_NODAL_CONTROL_VOLUME_INTERFACE",
                "deep_transport_law": "SYNTHETIC_MODAL_RESPONSE_WEIGHTED_DENSITY_EXCHANGE",
                "thermal_flux_role": "DIAGNOSTIC_ONLY",
            })
    return edges


def _thermal_diagnostics(state: ReducedState, cells: list[dict[str, Any]], strike_length_m: float) -> dict[str, Any]:
    fluxes = []
    radiogenic = []
    for i, (a, b) in enumerate(zip(cells, cells[1:])):
        dz = b["coordinate_z_m"] - a["coordinate_z_m"]
        k_face = 2.0 * a["k_w_m_k"] * b["k_w_m_k"] / (a["k_w_m_k"] + b["k_w_m_k"])
        area = state.width_m * strike_length_m
        q = -k_face * area * (b["temperature_k"] - a["temperature_k"]) / dz
        fluxes.append({
            "interface_id": f"{a['support_id']}:VERTICAL:{i:03d}-{i + 1:03d}",
            "conductive_flux_a_to_b_w": q,
            "effective_conductivity_w_m_k": k_face,
            "gradient_k_m": (b["temperature_k"] - a["temperature_k"]) / dz,
            "is_deep_energy_transfer": False,
            "method": "R6_KERNEL_ADJACENT_SAMPLE_HARMONIC_CONDUCTIVITY_DIAGNOSTIC",
        })
    for cell in cells:
        power = cell["radiogenic_w_m3"] * cell["volume_m3"]
        radiogenic.append({"cell_id": cell["cell_id"], "ordinary_thermal_power_w": power,
                           "is_deep_source": False})
    sensible = sum(cell["rho_kg_m3"] * cell["cp_j_kg_k"] * cell["temperature_k"] * cell["volume_m3"]
                   for cell in cells)
    return {"sensible_energy_reference_0_k_j": sensible,
            "conductive_interfaces": fluxes,
            "radiogenic_power_by_volume": radiogenic,
            "deep_energy_source_from_thermal": 0.0}


def _deep_transport_step(
    cells_by_support: dict[str, list[dict[str, Any]]],
    stocks_j_by_id: dict[str, float],
    *,
    dt_years: float,
    mobility_per_year: float,
    response_by_role: dict[str, float],
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    if not math.isfinite(dt_years) or dt_years <= 0 or not math.isfinite(mobility_per_year) or mobility_per_year < 0:
        raise ValueError("MICRODOMAIN_DEEP_STEP_CONFIG_INVALID")
    transfers = []
    delta = {cell_id: 0.0 for cell_id in stocks_j_by_id}
    requested_fraction_by_cell = {cell_id: 0.0 for cell_id in stocks_j_by_id}
    for support_id, cells in cells_by_support.items():
        for left, right in zip(cells, cells[1:]):
            a_id, b_id = left["cell_id"], right["cell_id"]
            volume_a, volume_b = left["volume_m3"], right["volume_m3"]
            response = min(response_by_role[left["material_role_id"]],
                           response_by_role[right["material_role_id"]])
            fraction = dt_years * mobility_per_year * response
            harmonic_volume = 2.0 * volume_a * volume_b / (volume_a + volume_b)
            density_a = stocks_j_by_id[a_id] / volume_a
            density_b = stocks_j_by_id[b_id] / volume_b
            transfer = fraction * harmonic_volume * (density_a - density_b)
            delta[a_id] -= transfer
            delta[b_id] += transfer
            requested_fraction_by_cell[a_id] += fraction * harmonic_volume / volume_a
            requested_fraction_by_cell[b_id] += fraction * harmonic_volume / volume_b
            transfers.append({
                "interface_id": f"{support_id}:VERTICAL:{left['node_index_zero_based']:03d}-{right['node_index_zero_based']:03d}",
                "cell_a": a_id, "cell_b": b_id,
                "transfer_a_to_b_j": transfer,
                "synthetic_modal_response_face": response,
                "effective_exchange_fraction": fraction,
            })
    if max(requested_fraction_by_cell.values(), default=0.0) > 1.0:
        raise ValueError("MICRODOMAIN_DEEP_EXPLICIT_STEP_UNSTABLE")
    result = {cell_id: stock + delta[cell_id] for cell_id, stock in stocks_j_by_id.items()}
    if any(not math.isfinite(value) or value < -1e-10 for value in result.values()):
        raise ValueError("MICRODOMAIN_DEEP_STOCK_INVALID")
    result = {cell_id: max(0.0, value) for cell_id, value in result.items()}
    residual = sum(result.values()) - sum(stocks_j_by_id.values())
    if not math.isclose(residual, 0.0, rel_tol=1e-13, abs_tol=1e-8):
        raise ValueError("MICRODOMAIN_DEEP_TRANSPORT_NOT_CONSERVATIVE")
    return result, transfers


def run_integrated_microdomain(
    archive_path: str,
    *,
    duration_years: float = 3.0,
    step_years: float = 1.0,
    strike_length_m: float = 1.0,
    synthetic_deep_density_by_role_j_m3: dict[str, float] | None = None,
    synthetic_mobility_per_year: float = 0.01,
) -> dict[str, Any]:
    """Run a bounded two-column thermal advance and synthetic Deep exchange."""
    density_by_role = dict(DEFAULT_SYNTHETIC_DEEP_DENSITY_BY_ROLE if synthetic_deep_density_by_role_j_m3 is None
                           else synthetic_deep_density_by_role_j_m3)
    if not all(math.isfinite(v) for v in (duration_years, step_years, strike_length_m,
                                           synthetic_mobility_per_year, *density_by_role.values())):
        raise ValueError("MICRODOMAIN_CONFIG_NONFINITE")
    if (duration_years <= 0 or step_years <= 0 or strike_length_m <= 0
            or synthetic_mobility_per_year < 0 or any(v < 0 for v in density_by_role.values())):
        raise ValueError("MICRODOMAIN_CONFIG_RANGE_INVALID")
    ratio = duration_years / step_years
    steps = round(ratio)
    if not math.isclose(ratio, steps, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("MICRODOMAIN_DURATION_NOT_INTEGER_STEPS")

    started = perf_counter()
    loaded, archive_digest = load_microdomain_inputs(archive_path)
    metadata = {meta["support_id"]: meta for _, meta in loaded}
    states = {meta["support_id"]: state for state, meta in loaded}
    initial_states = dict(states)
    original_hashes = {support: _state_digest(state) for support, state in states.items()}
    if any(original_hashes[support] != metadata[support]["state_payload_sha256"] for support in states):
        raise ValueError("MICRODOMAIN_INITIAL_STATE_IDENTITY_MISMATCH")
    forcing_values = {meta["frozen_euler_extension_m_per_year"] for _, meta in loaded}
    if len(forcing_values) != 1 or next(iter(forcing_values)) is None:
        raise ValueError("MICRODOMAIN_SHARED_FORCING_UNKNOWN_OR_MISMATCHED")
    extension_velocity = float(next(iter(forcing_values)))
    cells_by_support = {
        support: _column_geometry(state, support, strike_length_m)
        for support, state in states.items()
    }
    initial_cells = {cell["cell_id"]: cell for cells in cells_by_support.values() for cell in cells}
    initial_volumes = {cell_id: cell["volume_m3"] for cell_id, cell in initial_cells.items()}
    if set(density_by_role) != {cell["material_role_id"] for cell in initial_cells.values()}:
        raise ValueError("MICRODOMAIN_SYNTHETIC_DEEP_DENSITY_ROLE_SET_MISMATCH")
    response_by_role = _modal_response_by_role()
    stability_by_cell = {cell_id: 0.0 for cell_id in initial_cells}
    for cells in cells_by_support.values():
        for left, right in zip(cells, cells[1:]):
            fraction = step_years * synthetic_mobility_per_year * min(
                response_by_role[left["material_role_id"]],
                response_by_role[right["material_role_id"]],
            )
            harmonic_volume = 2.0 * left["volume_m3"] * right["volume_m3"] / (
                left["volume_m3"] + right["volume_m3"]
            )
            stability_by_cell[left["cell_id"]] += fraction * harmonic_volume / left["volume_m3"]
            stability_by_cell[right["cell_id"]] += fraction * harmonic_volume / right["volume_m3"]
    if max(stability_by_cell.values(), default=0.0) > 1.0:
        raise ValueError("MICRODOMAIN_DEEP_EXPLICIT_STEP_UNSTABLE")
    tracemalloc.start()
    stocks = {cell_id: density_by_role[cell["material_role_id"]] * cell["volume_m3"]
              for cell_id, cell in initial_cells.items()}
    initial_stocks = dict(stocks)
    initial_thermal = {support: _thermal_diagnostics(states[support], cells, strike_length_m)
                       for support, cells in cells_by_support.items()}
    step_records = []

    for step_index in range(steps):
        step_states = {}
        step_support_records = {}
        for support, prior in states.items():
            next_state, kernel_diag = pure_shear_thermal_step(
                prior,
                duration_s=step_years * SECONDS_PER_YEAR,
                extension_velocity_m_s=extension_velocity / SECONDS_PER_YEAR,
            )
            next_cells = _column_geometry(next_state, support, strike_length_m)
            before_diag = _thermal_diagnostics(prior, cells_by_support[support], strike_length_m)
            after_diag = _thermal_diagnostics(next_state, next_cells, strike_length_m)
            step_support_records[support] = {
                "time_start_s": prior.time_s,
                "time_end_s": next_state.time_s,
                "width_start_m": prior.width_m,
                "width_end_m": next_state.width_m,
                "crust_start_m": prior.crust_m,
                "crust_end_m": next_state.crust_m,
                "lithosphere_start_m": prior.lithosphere_m,
                "lithosphere_end_m": next_state.lithosphere_m,
                "beta_start": prior.beta,
                "beta_end": next_state.beta,
                "strain_start": prior.accumulated_strain,
                "strain_end": next_state.accumulated_strain,
                "temperature_linf_change_k": max(abs(a - b) for a, b in zip(prior.temperature_k, next_state.temperature_k)),
                "temperature_min_start_k": min(prior.temperature_k),
                "temperature_min_end_k": min(next_state.temperature_k),
                "temperature_max_start_k": max(prior.temperature_k),
                "temperature_max_end_k": max(next_state.temperature_k),
                "thermal_sensible_energy_start_j": before_diag["sensible_energy_reference_0_k_j"],
                "thermal_sensible_energy_end_j": after_diag["sensible_energy_reference_0_k_j"],
                "thermal_kernel_substeps": kernel_diag.substeps,
                "area_relative_error": kernel_diag.area_relative_error,
                "state_payload_sha256_start": _state_digest(prior),
                "state_payload_sha256_end": _state_digest(next_state),
            }
            step_states[support] = next_state
            cells_by_support[support] = next_cells
        stocks, edge_transfers = _deep_transport_step(
            cells_by_support, stocks, dt_years=step_years,
            mobility_per_year=synthetic_mobility_per_year,
            response_by_role=response_by_role,
        )
        current_volumes = {cell["cell_id"]: cell["volume_m3"]
                           for cells in cells_by_support.values() for cell in cells}
        step_records.append({
            "step": step_index + 1,
            "supports": step_support_records,
            "deep": {
                "inventory_before_j": sum(initial_stocks.values()) if step_index == 0 else step_records[-1]["deep"]["inventory_after_j"],
                "inventory_after_j": sum(stocks.values()),
                "inventory_change_j": sum(stocks.values()) - (sum(initial_stocks.values()) if step_index == 0 else step_records[-1]["deep"]["inventory_after_j"]),
                "edge_transfer_count": len(edge_transfers),
                "transferred_energy_abs_sum_j": sum(abs(edge["transfer_a_to_b_j"]) for edge in edge_transfers),
                "transfers": edge_transfers,
                "source_j": 0.0,
                "loss_j": 0.0,
                "thermal_to_deep_transfer_j": 0.0,
                "volume_change_max_abs_m3": max(abs(current_volumes[k] - initial_volumes[k]) for k in initial_volumes),
            },
        })
        states = step_states

    final = {}
    for support, state in states.items():
        cells = cells_by_support[support]
        rows = []
        for cell in cells:
            cell_id = cell["cell_id"]
            stock = stocks[cell_id]
            source_cell = initial_cells[cell_id]
            zeta_base = 0.35 if cell["material_role_id"] == "CONTINENTAL_CRUST_REFERENCE" else 0.20
            zeta_initial = min(1.0, zeta_base * (1.0 + 0.1 * max(0.0, initial_states[support].accumulated_strain)))
            zeta = min(1.0, zeta_base * (1.0 + 0.1 * max(0.0, state.accumulated_strain)))
            rows.append({
                **cell,
                "initial_deep_inventory_j": initial_stocks[cell_id],
                "initial_deep_energy_density_j_m3": initial_stocks[cell_id] / source_cell["volume_m3"],
                "deep_inventory_j": stock,
                "deep_energy_density_j_m3": stock / cell["volume_m3"],
                "deep_equilibrium_density_j_m3": 0.0,
                "geological_inventory_dfeu": None,
                "geological_inventory_status": "UNKNOWN_NO_DFEU_PROVIDER",
                "synthetic_zeta_accessibility": zeta,
                "initial_synthetic_zeta_accessibility": zeta_initial,
                "synthetic_accessible_energy_proxy_j": zeta * stock,
                "initial_synthetic_accessible_energy_proxy_j": zeta_initial * initial_stocks[cell_id],
                "accessibility_authority": "SYNTHETIC_ROLE_BASE_AND_STRAIN_PROXY_NOT_GEOLOGICAL_DATA",
                "modal_response": response_by_role[cell["material_role_id"]],
            })
        final[support] = {
            "source_record": metadata[support],
            "state_payload_sha256_initial": original_hashes[support],
            "state_payload_sha256_final": _state_digest(state),
            "initial_state": initial_states[support].payload(),
            "final_state": state.payload(),
            "initial_thermal_diagnostics": initial_thermal[support],
            "final_thermal_diagnostics": _thermal_diagnostics(state, cells, strike_length_m),
            "initial_material_volumes": [initial_cells[cell["cell_id"]] for cell in _column_geometry(
                initial_states[support], support, strike_length_m
            )],
            "material_volumes": rows,
            "column_volume_sum_m3_initial": sum(initial_volumes[c["cell_id"]] for c in _column_geometry(initial_states[support], support, strike_length_m)),
            "column_volume_sum_m3_final": sum(c["volume_m3"] for c in cells),
        }
        source_state = initial_states[support]
        final[support]["initial"] = {
            "time_s": source_state.time_s,
            "width_m": source_state.width_m,
            "crust_m": source_state.crust_m,
            "lithosphere_m": source_state.lithosphere_m,
            "beta": source_state.beta,
            "accumulated_strain": source_state.accumulated_strain,
            "temperature_min_k": min(source_state.temperature_k),
            "temperature_max_k": max(source_state.temperature_k),
            "thermal_sensible_energy_j": initial_thermal[support]["sensible_energy_reference_0_k_j"],
        }
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = perf_counter() - started
    initial_total = sum(initial_stocks.values())
    final_total = sum(stocks.values())
    return {
        "schema": "ARCANA_INTEGRATED_GEOLOGICAL_MICRODOMAIN_V1",
        "scope": SCOPE,
        "source_archive": {"sha256": archive_digest, "state_member": DEFAULT_SOURCE_ARCHIVE_MEMBER},
        "topology": {
            "B4_B5_reference": "T0 plate support/topology contracts",
            "support_grid_locators": ["R091-C028", "R091-C029"],
            "R6G1D_to_B5_face_or_node_binding": "UNKNOWN_NOT_PROVIDED_BY_CURRENT_B4_B5_EVIDENCE",
            "between_support_geological_contact": "UNKNOWN_NO_BOUNDARY_CLASS_OR_ACCOMMODATION_LAW",
            "lateral_interface_count": 0,
            "lateral_deep_transport": "DISABLED_NO_INFERRED_CONTINUITY",
            "vertical_interface_count": sum(len(cells) - 1 for cells in cells_by_support.values()),
            "vertical_interface_semantics": "ADJACENT_R6_COLUMN_CONTROL_VOLUMES; NOT_TECTONIC_BOUNDARY",
        },
        "configuration": {
            "duration_years": duration_years,
            "step_years": step_years,
            "steps": steps,
            "strike_length_m": strike_length_m,
            "extension_velocity_m_per_year": extension_velocity,
            "forcing_authority": "REUSED_FROZEN_ENGINEERING_CASE_VALUE_FOR_BOUNDED_DEVELOPMENT_ONLY",
            "deep_initial_density_j_m3_by_role": density_by_role,
            "deep_initial_inventory_authority": "SYNTHETIC_INITIAL_CONDITION_NOT_ENG10K_OR_GEOPHYSICAL_DATA",
            "deep_mobility_per_year": synthetic_mobility_per_year,
            "deep_mobility_authority": "SYNTHETIC_EXPERIMENTAL_CLOSURE_NOT_THERMAL_CONDUCTIVITY",
            "role_modal_parameters": [asdict(row) for row in ROLE_MODAL_PARAMETERS],
            "solar_source_w": 0.0,
            "geological_source_w": 0.0,
            "loss_rate_per_year": 0.0,
            "thermal_to_deep_transfer_j": 0.0,
            "accessibility_model": "SYNTHETIC_ROLE_BASE_TIMES_STRAIN_PROXY; CHANGES NO_STOCK",
        },
        "interfaces": _vertical_interfaces(cells_by_support),
        "steps": step_records,
        "supports": final,
        "deep_ledger": {
            "initial_inventory_j": initial_total,
            "final_inventory_j": final_total,
            "source_j": 0.0,
            "loss_j": 0.0,
            "thermal_to_deep_transfer_j": 0.0,
            "conservation_residual_j": final_total - initial_total,
            "inventory_density_semantics": "SYNTHETIC_J_PER_M3_TIMES_CURRENT_CONTROL_VOLUME",
        },
        "measurements": {
            "elapsed_seconds_including_archive_read": elapsed,
            "python_tracemalloc_peak_bytes": peak_python_bytes,
            "tracemalloc_is_not_process_rss": True,
            "recorded_cell_count": sum(len(rows["material_volumes"]) for rows in final.values()),
            "vertical_transport_interface_count_per_step": sum(len(cells) - 1 for cells in cells_by_support.values()),
            "step_count": steps,
        },
        "claim_limit": "NO_TECTONIC_LATERAL_CONTINUITY_DEEP_GEOLOGICAL_INVENTORY_OR_PHYSICAL_QUALIFICATION",
    }
