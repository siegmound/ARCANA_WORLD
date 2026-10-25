"""Canon-guided, explicitly synthetic two-cell Deep reservoir pilot.

The canon supplies separations and conservation constraints, not a closed
macroscopic geological transport law. All constitutive coefficients below
are therefore declared experimental inputs, never inferred from ordinary
thermal conductivity or presented as production physics.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any

import numpy as np

from .functional_development import ReducedState, pure_shear_thermal_step

SECONDS_PER_YEAR = 31_557_600.0


@dataclass(frozen=True)
class ModalMaterial:
    """Measured material properties plus synthetic Deep-mode parameters."""

    material_id: str
    density_kg_m3: float
    heat_capacity_j_kg_k: float
    thermal_conductivity_w_m_k: float
    modal_coupling: float
    modal_detuning: float
    modal_loss: float
    modal_parameter_authority: str = "SYNTHETIC_ENGINEERING_PARAMETER"

    def validate(self) -> None:
        if not self.material_id.strip():
            raise ValueError("MATERIAL_ID_REQUIRED")
        if self.modal_parameter_authority != "SYNTHETIC_ENGINEERING_PARAMETER":
            raise ValueError("UNQUALIFIED_MODAL_AUTHORITY")
        vals = (self.density_kg_m3, self.heat_capacity_j_kg_k,
                self.thermal_conductivity_w_m_k, self.modal_coupling,
                self.modal_detuning, self.modal_loss)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("MATERIAL_PARAMETER_NONFINITE")
        if min(vals[:3]) <= 0 or self.modal_coupling < 0 or self.modal_loss < 0:
            raise ValueError("MATERIAL_PARAMETER_OUT_OF_RANGE")

    def modal_response(self) -> float:
        """Bounded synthetic response inspired by mode-coupling structure.

        This is not the canon's coupled-mode evolution equation or a fitted
        geological law. The formula only makes sensitivity testable.
        """
        self.validate()
        g2 = self.modal_coupling * self.modal_coupling
        denominator = g2 + self.modal_detuning * self.modal_detuning + self.modal_loss
        return 0.0 if denominator == 0.0 else g2 / denominator


@dataclass(frozen=True)
class GeologyState:
    cell_id: str
    material: ModalMaterial
    strain: float
    thermal_state: str

    def validate(self) -> None:
        self.material.validate()
        if not self.cell_id.strip() or not math.isfinite(self.strain) or self.strain < 0:
            raise ValueError("GEOLOGY_STATE_INVALID")
        if not self.thermal_state.strip():
            raise ValueError("THERMAL_STATE_ID_REQUIRED")


@dataclass(frozen=True)
class DeepCell:
    cell_id: str
    free_inventory_j: float
    equilibrium_inventory_j: float
    accessibility_zeta: float
    geological_accessibility_a_x: float
    geological_source_w: float = 0.0
    loss_rate_per_year: float = 0.0

    def validate(self) -> None:
        vals = (self.free_inventory_j, self.equilibrium_inventory_j,
                self.accessibility_zeta, self.geological_accessibility_a_x,
                self.geological_source_w, self.loss_rate_per_year)
        if not self.cell_id.strip() or not all(math.isfinite(v) for v in vals):
            raise ValueError("DEEP_CELL_NONFINITE_OR_UNNAMED")
        if min(self.free_inventory_j, self.equilibrium_inventory_j,
               self.geological_source_w, self.loss_rate_per_year) < 0:
            raise ValueError("DEEP_CELL_NEGATIVE_STOCK_OR_RATE")
        if not 0 <= self.accessibility_zeta <= 1 or not 0 <= self.geological_accessibility_a_x <= 1:
            raise ValueError("DEEP_ACCESSIBILITY_OUT_OF_RANGE")

    @property
    def accessible_free_inventory_j(self) -> float:
        self.validate()
        return self.accessibility_zeta * max(
            self.free_inventory_j - self.equilibrium_inventory_j, 0.0
        )


@dataclass(frozen=True)
class RoleModalParameters:
    """Synthetic modal closure kept separate from ReducedState geology."""

    role_id: str
    coupling: float
    detuning: float
    loss: float

    def validate(self) -> None:
        if not self.role_id.strip() or not all(math.isfinite(v) for v in
                (self.coupling, self.detuning, self.loss)):
            raise ValueError("SYNTHETIC_MODAL_ROLE_PARAMETERS_INVALID")
        if self.coupling < 0 or self.loss < 0:
            raise ValueError("SYNTHETIC_MODAL_ROLE_PARAMETERS_INVALID")


@dataclass(frozen=True)
class ReducedStateNodeMapping:
    """Persistent support/trajectory/node binding for the two pilot volumes."""

    support_id: str
    trajectory_id: str
    sequence: int
    state_payload_sha256: str
    mapping_id: str
    node_indices: tuple[int, int]
    strike_length_m: float = 1.0

    def validate(self, node_count: int) -> None:
        if not self.support_id or not self.trajectory_id or not self.mapping_id:
            raise ValueError("MATERIAL_NODE_MAPPING_IDENTITY_MISSING")
        if isinstance(self.sequence, bool) or self.sequence < 0:
            raise ValueError("MATERIAL_NODE_MAPPING_SEQUENCE_INVALID")
        if not re.fullmatch(r"[0-9a-f]{64}", self.state_payload_sha256):
            raise ValueError("MATERIAL_NODE_MAPPING_STATE_DIGEST_INVALID")
        a, b = self.node_indices
        if isinstance(a, bool) or isinstance(b, bool) or b <= a or a < 1 or b >= node_count - 1:
            raise ValueError("MATERIAL_NODE_MAPPING_REQUIRES_ORDERED_INTERIOR_NODES")
        if not math.isfinite(self.strike_length_m) or self.strike_length_m <= 0:
            raise ValueError("MATERIAL_NODE_MAPPING_STRIKE_LENGTH_INVALID")


@dataclass(frozen=True)
class MappedReducedStatePair:
    geology: tuple[GeologyState, GeologyState]
    cell_ids: tuple[str, str]
    mapping_payload: dict[str, Any]
    interface_thermal_diagnostics: dict[str, Any]

    def deep_cells(
        self, *, inventory_j: tuple[float, float], zeta: tuple[float, float],
        a_x: tuple[float, float],
    ) -> tuple[DeepCell, DeepCell]:
        if any(len(v) != 2 for v in (inventory_j, zeta, a_x)):
            raise ValueError("MAPPED_PAIR_INPUTS_REQUIRE_TWO_CELLS")
        return tuple(DeepCell(self.cell_ids[i], inventory_j[i], 0.0, zeta[i], a_x[i])
                     for i in range(2))  # type: ignore[return-value]


def map_reduced_state_material_nodes(
    state: ReducedState,
    *,
    identity: ReducedStateNodeMapping,
    modal_parameters_by_role: tuple[RoleModalParameters, ...],
) -> MappedReducedStatePair:
    """Bind two adjacent ReducedState nodes without inferring lithology.

    The Fourier flux is a conventional thermal diagnostic over the selected
    adjacent nodes. It is never passed to the Deep inventory operator.
    """
    identity.validate(len(state.materials))
    if len(state.temperature_k) != len(state.material_coordinate) or len(state.materials) != len(state.temperature_k):
        raise ValueError("REDUCED_STATE_MATERIAL_MAPPING_CARDINALITY_INVALID")
    params: dict[str, RoleModalParameters] = {}
    for item in modal_parameters_by_role:
        item.validate()
        if item.role_id in params:
            raise ValueError("DUPLICATE_SYNTHETIC_MODAL_ROLE_CONFIGURATION")
        params[item.role_id] = item
    i, j = identity.node_indices
    samples = []
    geology = []
    cell_ids = []
    for index in (i, j):
        mat = state.materials[index]
        if mat.role_id not in params:
            raise ValueError(f"SYNTHETIC_MODAL_PARAMETERS_MISSING_FOR_ROLE:{mat.role_id}")
        p = params[mat.role_id]
        z_m = state.material_coordinate[index] * state.lithosphere_m
        cell_id = f"{identity.support_id}:{identity.trajectory_id}:NODE{index:03d}"
        z_all = [x * state.lithosphere_m for x in state.material_coordinate]
        left = z_all[0] if index == 0 else 0.5 * (z_all[index - 1] + z_all[index])
        right = z_all[-1] if index == len(z_all) - 1 else 0.5 * (z_all[index] + z_all[index + 1])
        cell_ids.append(cell_id)
        samples.append({
            "support_id": identity.support_id,
            "trajectory_id": identity.trajectory_id,
            "sequence": identity.sequence,
            "state_payload_sha256": identity.state_payload_sha256,
            "node_index_zero_based": index,
            "cell_id": cell_id,
            "material_role_id": mat.role_id,
            "rho_kg_m3": mat.rho_kg_m3,
            "cp_j_kg_k": mat.cp_j_kg_k,
            "k_w_m_k": mat.k_w_m_k,
            "radiogenic_w_m3": mat.radiogenic_w_m3,
            "temperature_k": state.temperature_k[index],
            "material_coordinate_xi": state.material_coordinate[index],
            "coordinate_z_m": z_m,
            "control_volume_bounds_z_m": [left, right],
            "control_volume_thickness_m": right - left,
        })
        geology.append(GeologyState(
            cell_id=cell_id,
            material=ModalMaterial(mat.role_id, mat.rho_kg_m3, mat.cp_j_kg_k,
                                   mat.k_w_m_k, p.coupling, p.detuning, p.loss),
            strain=state.accumulated_strain,
            thermal_state=identity.state_payload_sha256,
        ))
    a, b = samples
    dz = b["coordinate_z_m"] - a["coordinate_z_m"]
    if not math.isfinite(dz) or dz <= 0:
        raise ValueError("MAPPED_NODE_COORDINATES_NOT_INCREASING")
    area_m2 = state.width_m * identity.strike_length_m
    gradient = (b["temperature_k"] - a["temperature_k"]) / dz
    crosses_moho = (a["material_role_id"] != b["material_role_id"]
                    and a["coordinate_z_m"] <= state.crust_m <= b["coordinate_z_m"])
    if a["material_role_id"] != b["material_role_id"] and not crosses_moho:
        raise ValueError("MATERIAL_INTERFACE_NOT_BRACKETED_BY_SELECTED_NODES")
    if crosses_moho:
        d_crust = state.crust_m - a["coordinate_z_m"]
        d_mantle = b["coordinate_z_m"] - state.crust_m
        if d_crust <= 0 or d_mantle <= 0:
            raise ValueError("MATERIAL_INTERFACE_SAMPLE_MUST_BRACKET_INTERFACE")
        resistance_area = d_crust / a["k_w_m_k"] + d_mantle / b["k_w_m_k"]
        k_face = dz / resistance_area
        flux_0_to_1_w = -area_m2 * (b["temperature_k"] - a["temperature_k"]) / resistance_area
        mapped_face_z_m = state.crust_m
        flux_method = "PIECEWISE_SERIES_RESISTANCE_THROUGH_CRUST_MANTLE_INTERFACE"
    else:
        k_face = 2.0 * a["k_w_m_k"] * b["k_w_m_k"] / (a["k_w_m_k"] + b["k_w_m_k"])
        flux_0_to_1_w = -k_face * area_m2 * gradient
        mapped_face_z_m = 0.5 * (a["coordinate_z_m"] + b["coordinate_z_m"])
        resistance_area = None
        flux_method = "ADJACENT_SAMPLE_HARMONIC_CONDUCTIVITY_DIAGNOSTIC"
    if not all(math.isfinite(v) for v in (k_face, area_m2, gradient, flux_0_to_1_w)):
        raise ValueError("THERMAL_INTERFACE_DIAGNOSTIC_NONFINITE")
    digest_payload = {
        "mapping_id": identity.mapping_id,
        "support_id": identity.support_id,
        "trajectory_id": identity.trajectory_id,
        "sequence": identity.sequence,
        "state_payload_sha256": identity.state_payload_sha256,
        "node_indices": list(identity.node_indices),
        "strike_length_m": identity.strike_length_m,
    }
    mapping_payload = {
        **digest_payload,
        "mapping_sha256": hashlib.sha256(json.dumps(digest_payload, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest(),
        "support_identity_semantics": "R6_SUPPORT_ID_FROM_ARCHIVED_STATE_PROVENANCE",
        "material_identity_semantics": "NODE_ROLE_ID_FROM_REDUCED_STATE; NOT_LITHOLOGY",
        "numerical_state_identity_semantics": "STATE_PAYLOAD_SHA256_FROM_ARCHIVE_RECORD",
        "volume_semantics": "MAPPED_NODE_DUAL_CONTROL_VOLUME_SAMPLES; NOT_GLOBAL_CELLS",
        "samples": samples,
        "modal_configuration_authority": "SEPARATE_SYNTHETIC_ROLE_PARAMETER_TABLE",
        "synthetic_modal_parameters_by_role": [vars(x) for x in modal_parameters_by_role],
    }
    return MappedReducedStatePair(
        tuple(geology), tuple(cell_ids), mapping_payload, {
            "diagnostic": "ORDINARY_FOURIER_FLUX_ONLY_NOT_A_DEEP_SOURCE",
            "direction": "CELL_0_TO_CELL_1; POSITIVE_DOWNWARD_IN_INCREASING_Z",
            "node_indices_zero_based": [i, j],
            "node_spacing_m": dz,
            "mapped_face_z_m": mapped_face_z_m,
            "material_boundary_z_m": state.crust_m if a["material_role_id"] != b["material_role_id"] else None,
            "flux_method": flux_method,
            "temperature_gradient_k_m": gradient,
            "effective_face_conductivity_w_m_k": k_face,
            "series_resistance_area_k_m2_w": resistance_area,
            "cross_section_area_m2": area_m2,
            "conductive_flux_0_to_1_w": flux_0_to_1_w,
            "radiogenic_thermal_power_w_by_node_volume": [
                a["radiogenic_w_m3"] * area_m2 * a["control_volume_thickness_m"],
                b["radiogenic_w_m3"] * area_m2 * b["control_volume_thickness_m"],
            ],
            "radiogenic_power_is_deep_source": False,
        },
    )


@dataclass(frozen=True)
class PilotConfig:
    duration_years: float = 3.0
    step_years: float = 1.0
    mobility_per_year: float = 0.08
    extension_velocity_m_per_year: float = 0.11467052868814648
    solar_candidate_share: float = 0.05
    solar_source_enabled: bool = False
    solar_flux_w: float | None = None

    def validate(self) -> int:
        if not all(math.isfinite(v) for v in (self.duration_years, self.step_years,
                                               self.mobility_per_year,
                                               self.extension_velocity_m_per_year,
                                               self.solar_candidate_share)):
            raise ValueError("CONFIG_NONFINITE")
        if self.duration_years <= 0 or self.step_years <= 0 or self.mobility_per_year < 0:
            raise ValueError("CONFIG_RANGE_INVALID")
        if self.extension_velocity_m_per_year < 0 or not 0 <= self.solar_candidate_share <= 1:
            raise ValueError("CONFIG_RANGE_INVALID")
        ratio = self.duration_years / self.step_years
        steps = round(ratio)
        if not math.isclose(ratio, steps, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("DURATION_MUST_BE_INTEGER_STEPS")
        if self.solar_source_enabled:
            if self.solar_flux_w is None or not math.isfinite(self.solar_flux_w) or self.solar_flux_w < 0:
                raise ValueError("SOLAR_SOURCE_REQUIRES_EXPLICIT_NONNEGATIVE_FLUX")
        elif self.solar_flux_w is not None:
            raise ValueError("SOLAR_FLUX_MUST_NOT_BE_SILENTLY_IGNORED")
        return steps


def _structural_accessibility(base: float, strain: float) -> float:
    """Synthetic monotone access response; changes no stored energy."""
    return min(1.0, max(0.0, base * (1.0 + strain)))


def _advance_reservoirs(
    cells: tuple[DeepCell, DeepCell], geology: tuple[GeologyState, GeologyState],
    *, dt_years: float, mobility_per_year: float, solar_source_w: float = 0.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    for c, g in zip(cells, geology):
        c.validate(); g.validate()
        if c.cell_id != g.cell_id:
            raise ValueError("CELL_ID_BINDING_MISMATCH")
    responses = tuple(g.material.modal_response() for g in geology)
    line_response = min(responses)
    coefficient = mobility_per_year * line_response
    transfer_fraction = dt_years * coefficient
    if not math.isfinite(transfer_fraction) or transfer_fraction > 0.5:
        raise ValueError("EXPLICIT_TRANSPORT_STEP_UNSTABLE")
    before = np.asarray([c.free_inventory_j for c in cells], dtype=np.float64)
    geology_sources = np.asarray([c.geological_source_w * dt_years * SECONDS_PER_YEAR for c in cells])
    solar_total = solar_source_w * dt_years * SECONDS_PER_YEAR
    solar_sources = np.asarray((solar_total * 0.5, solar_total * 0.5), dtype=np.float64)
    sources = geology_sources + solar_sources
    # First-order explicit sink; rates are synthetic and bounded per step.
    losses = np.asarray([c.loss_rate_per_year * dt_years for c in cells]) * before
    if np.any(losses > before):
        raise ValueError("LOSS_EXCEEDS_AVAILABLE_STOCK")
    post_local = before - losses + sources
    flux = transfer_fraction * (post_local[0] - post_local[1])
    after = np.asarray((post_local[0] - flux, post_local[1] + flux), dtype=np.float64)
    if not np.isfinite(after).all() or np.any(after < 0):
        raise ValueError("DEEP_RESERVOIR_UPDATE_INVALID")
    residual = float(after.sum() - before.sum() - sources.sum() + losses.sum())
    return after, {
        "modal_response_by_cell": list(responses),
        "synthetic_line_response": line_response,
        "synthetic_transport_coefficient_per_year": coefficient,
        "synthetic_two_cell_relaxation_time_years": (
            None if coefficient == 0.0 else 1.0 / (2.0 * coefficient)
        ),
        "transport_fraction_this_step": transfer_fraction,
        "transport_flux_0_to_1_j": float(flux),
        "geological_source_j_by_cell": sources.tolist(),
        "geological_source_only_j_by_cell": geology_sources.tolist(),
        "solar_candidate_source_j_by_cell": solar_sources.tolist(),
        "loss_j_by_cell": losses.tolist(),
        "energy_balance_residual_j": residual,
    }


def run_canon_guided_pilot(
    initial_thermal_state: ReducedState,
    *,
    geology: tuple[GeologyState, GeologyState],
    deep_cells: tuple[DeepCell, DeepCell],
    config: PilotConfig = PilotConfig(),
    structure_access_scale: float = 0.01,
    structure_accessibility_perturbation: tuple[float, float] = (0.0, 0.0),
    material_mapping: ReducedStateNodeMapping | None = None,
    modal_parameters_by_role: tuple[RoleModalParameters, ...] = (),
) -> dict[str, Any]:
    """Advance the reduced thermal kernel and a separate synthetic Deep ledger.

    Thermal evolution does not inject energy into Deep. Geometry/strain only
    affects the synthetic accessibility diagnostic, not energy stock.
    """
    steps = config.validate()
    if not math.isfinite(structure_access_scale) or structure_access_scale < 0:
        raise ValueError("STRUCTURE_ACCESS_SCALE_INVALID")
    if len(structure_accessibility_perturbation) != 2 or not all(
            math.isfinite(v) for v in structure_accessibility_perturbation):
        raise ValueError("STRUCTURAL_ACCESSIBILITY_PERTURBATION_INVALID")
    if tuple(c.cell_id for c in deep_cells) != tuple(g.cell_id for g in geology):
        raise ValueError("CELL_ID_BINDING_MISMATCH")
    for c in deep_cells: c.validate()
    initial_mapping = None
    if material_mapping is not None:
        initial_mapping = map_reduced_state_material_nodes(
            initial_thermal_state, identity=material_mapping,
            modal_parameters_by_role=modal_parameters_by_role,
        )
        if tuple(c.cell_id for c in deep_cells) != initial_mapping.cell_ids:
            raise ValueError("MATERIAL_MAPPING_DEEP_CELL_ID_MISMATCH")
    state = initial_thermal_state
    stocks = np.asarray([c.free_inventory_j for c in deep_cells], dtype=np.float64)
    records: list[dict[str, Any]] = []
    mapping_records: list[dict[str, Any]] = []
    if initial_mapping is not None:
        mapping_records.append(initial_mapping.mapping_payload)
    for step in range(steps):
        next_state, thermal_diag = pure_shear_thermal_step(
            state, duration_s=config.step_years * SECONDS_PER_YEAR,
            extension_velocity_m_s=config.extension_velocity_m_per_year / SECONDS_PER_YEAR,
        )
        current_geo = tuple(GeologyState(
            cell_id=g.cell_id, material=g.material,
            strain=g.strain + structure_access_scale * (next_state.accumulated_strain - initial_thermal_state.accumulated_strain),
            thermal_state=f"REDUCED_THERMAL_STATE_STEP_{step + 1}",
        ) for g in geology)
        mapped_pair = None
        if material_mapping is not None:
            import dataclasses
            state_bytes = json.dumps(next_state.payload(), sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode("utf-8")
            next_identity = dataclasses.replace(
                material_mapping,
                sequence=material_mapping.sequence + step + 1,
                state_payload_sha256=hashlib.sha256(state_bytes).hexdigest(),
            )
            mapped_pair = map_reduced_state_material_nodes(
                next_state, identity=next_identity,
                modal_parameters_by_role=modal_parameters_by_role,
            )
            current_geo = mapped_pair.geology
            mapping_records.append(mapped_pair.mapping_payload)
        current_cells = tuple(DeepCell(
            cell_id=c.cell_id, free_inventory_j=float(stocks[i]),
            equilibrium_inventory_j=c.equilibrium_inventory_j,
            accessibility_zeta=c.accessibility_zeta,
            geological_accessibility_a_x=c.geological_accessibility_a_x,
            geological_source_w=c.geological_source_w,
            loss_rate_per_year=c.loss_rate_per_year,
        ) for i, c in enumerate(deep_cells))
        stocks, ledger = _advance_reservoirs(
            current_cells, current_geo, dt_years=config.step_years,
            mobility_per_year=config.mobility_per_year,
            solar_source_w=(config.solar_flux_w * config.solar_candidate_share
                            if config.solar_source_enabled else 0.0),
        )
        zeta = [_structural_accessibility(c.accessibility_zeta, g.strain)
                for c, g in zip(current_cells, current_geo)]
        zeta = [min(1.0, max(0.0, zeta[i] + structure_accessibility_perturbation[i]))
                for i in range(2)]
        accessible = [zeta[i] * max(stocks[i] - current_cells[i].equilibrium_inventory_j, 0.0)
                      for i in range(2)]
        records.append({
            "step": step + 1,
            "elapsed_years": (step + 1) * config.step_years,
            "thermal_kernel_substeps": thermal_diag.substeps,
            "thermal_state_time_s": next_state.time_s,
            "width_m": next_state.width_m,
            "strain": next_state.accumulated_strain,
            "deep_inventory_j_by_cell": stocks.tolist(),
            "accessibility_zeta_by_cell": zeta,
            "structure_accessibility_perturbation_by_cell": list(structure_accessibility_perturbation),
            "accessible_free_inventory_diagnostic_j_by_cell": accessible,
            **ledger,
            **({"material_mapping_sha256": mapped_pair.mapping_payload["mapping_sha256"],
               "mapped_material_samples": mapped_pair.mapping_payload["samples"],
               "interface_thermal_diagnostics": mapped_pair.interface_thermal_diagnostics}
              if mapped_pair is not None else {}),
        })
        state = next_state
    total_geology_source = sum(sum(r["geological_source_only_j_by_cell"]) for r in records)
    total_solar = sum(sum(r["solar_candidate_source_j_by_cell"]) for r in records)
    total_source = total_geology_source + total_solar
    total_loss = sum(sum(r["loss_j_by_cell"]) for r in records)
    total_transport = sum(r["transport_flux_0_to_1_j"] for r in records)
    solar = total_solar
    return {
        "schema": "ARCANA_CANON_GUIDED_DEEP_GEOPHYSICS_PILOT_V1",
        "scope": "TWO_CELL_SYNTHETIC_MACROSCOPIC_CLOSURE_NOT_CANONICAL_PHYSICS",
        "canon_basis": {
            "chapter_12": "Deep stock is nonuniform, multimodal; accessible free energy is zeta times positive excess; sources and transport are separate.",
            "chapter_13": "Material/geology/temperature can modify mode spectrum and overlap; macroscopic response remains unclosed.",
            "chapter_17": "Ordinary thermal diffusion uses k/(rho cp); no identification with Deep transport is made.",
            "chapter_21": "Materials alter modes/coupling and do not create Deep energy; recharge requires an actual source.",
            "chapter_25": "Cross-domain energy and source attribution must close; accessibility change is not energy transfer.",
            "canon_zip_sha256": "RECORDED_BY_CALLER_NOT_RECALCULATED",
        },
        "synthetic_closure": {
            "modal_response": "g^2/(g^2+detuning^2+loss)",
            "line_transport": "dt*mobility*min(response_left,response_right)*(E_left-E_right), equal/opposite flux",
            "accessibility": "clip(zeta_base*(1+strain_scale*strain),0,1); affects diagnostic accessible inventory only",
            "limits": "synthetic parameters; not derived/canonical rates; no thermal-to-Deep source",
        },
        "energy_ledgers": {
            "geological_inventory_dfeu": None,
            "geological_inventory_authority": "UNKNOWN_NO_GEOLOGICAL_DFEU_PROVIDER_BOUND",
            "deep_joule_inventory_authority": "SYNTHETIC_TEST_INITIAL_CONDITION_AND_EXPLICIT_SOURCE_INPUTS",
            "initial_inventory_j_by_cell": [c.free_inventory_j for c in deep_cells],
            "final_inventory_j_by_cell": stocks.tolist(),
            "geological_accessibility_a_x_by_cell": [c.geological_accessibility_a_x for c in deep_cells],
            "energy_accessibility_zeta_base_by_cell": [c.accessibility_zeta for c in deep_cells],
            "geological_source_j": total_geology_source,
            "material_to_deep_conversion_j": 0.0,
            "solar_candidate_share": config.solar_candidate_share,
            "solar_source_enabled": config.solar_source_enabled,
            "solar_flux_w": config.solar_flux_w,
            "solar_energy_j": solar,
            "solar_authority": "NO_SOLAR_PROVIDER; DISABLED_UNLESS_EXPLICIT_SYNTHETIC_FLUX_GIVEN",
            "losses_j": total_loss,
            "net_transport_left_to_right_j": total_transport,
            "transport_is_internal_and_conservative": True,
            "balance_residual_j": float(stocks.sum() - sum(c.free_inventory_j for c in deep_cells) - total_source + total_loss),
            "accessibility_does_not_change_inventory": True,
            "accessible_free_inventory_j_by_cell": records[-1]["accessible_free_inventory_diagnostic_j_by_cell"],
        },
        "thermal": {
            "time_start_s": initial_thermal_state.time_s,
            "time_end_s": state.time_s,
            "width_start_m": initial_thermal_state.width_m,
            "width_end_m": state.width_m,
            "temperature_start_k": [initial_thermal_state.temperature_k[0], initial_thermal_state.temperature_k[-1]],
            "temperature_end_k": [state.temperature_k[0], state.temperature_k[-1]],
            "temperature_linf_change_k": max(abs(a - b) for a, b in zip(
                initial_thermal_state.temperature_k, state.temperature_k
            )),
            "coupling_to_deep": "NONE; THERMAL_RESULTS_AFFECT_ONLY_SYNTHETIC_ACCESSIBILITY_DIAGNOSTIC",
        },
        "geology": [{"cell_id": g.cell_id, "material_id": g.material.material_id,
                     "rho_kg_m3": g.material.density_kg_m3,
                     "cp_j_kg_k": g.material.heat_capacity_j_kg_k,
                     "thermal_conductivity_w_m_k_not_used_for_deep_transport": g.material.thermal_conductivity_w_m_k,
                     "modal_coupling": g.material.modal_coupling,
                     "modal_detuning": g.material.modal_detuning,
                     "modal_loss": g.material.modal_loss,
                     "modal_parameter_authority": g.material.modal_parameter_authority}
                    for g in geology],
        "records": records,
        "reduced_state_material_mappings": mapping_records,
        "claim_limit": "NO_GEOLOGICAL_DFEU_PROVIDER_NO_PHYSICAL_MODAL_PARAMETERS_NO_VALIDATED_DEEP_TRANSPORT_OR_SOLAR_SOURCE",
    }
