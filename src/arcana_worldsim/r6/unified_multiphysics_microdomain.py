"""Short, shared-clock noncanonical R6 multiphysics microdomain.

The runner composes existing thermal, benchmark rheology, continuum mechanics,
surface/hydrology, and Deep reservoir operators. Couplings are limited to
explicit state handoffs; all non-R6 closures and forcings are labeled synthetic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Callable, Mapping

from .constitutive_mechanics_microdomain import solve_layered_interface_increment
from .deep_geological_physics_pilot import (
    DeepCell, GeologyState, ModalMaterial, _advance_reservoirs,
    _structural_accessibility,
)
from .functional_development import NodeMaterial, ReducedState, pure_shear_thermal_step
from .geological_surface_microdomain import (
    SUPPORTS, SurfaceConfig, SurfaceMicrodomainError, _surface_grid_geometry,
)
from .hydrology_surface_coupling import HydroConfig, run_hydrology_scenario
from .integrated_geological_microdomain import _column_geometry, _state_digest
from .material_rheology_provider import evaluate_reduced_state_column
from .tectonic_deep_pilot import SECONDS_PER_YEAR


@dataclass(frozen=True)
class UnifiedConfig:
    duration_years: float = 3.0
    external_step_years: float = 1.0
    hydrology_dt_seconds: float = 3600.0
    opening_rate_m_year: float = 0.01
    prescribed_uplift_total_m_by_support: tuple[float, float] = (0.25, 0.0)
    surface_initial_relief_m_by_support: tuple[float, float] = (20.0, 0.0)
    surface_initial_cover_m_by_support: tuple[float, float] = (5.0, 5.0)
    sediment_density_kg_m3: float = 1800.0
    substrate_initial_thickness_m_by_support: tuple[float, float] = (100.0, 100.0)
    substrate_density_kg_m3_by_support: tuple[float, float] = (2700.0, 2700.0)
    substrate_material_id_by_support: tuple[str, str] = (
        "SYNTHETIC_SUBSTRATE_BENCHMARK:C028", "SYNTHETIC_SUBSTRATE_BENCHMARK:C029")
    substrate_erosion_enabled: bool = False
    substrate_critical_shear_pa: float = 0.0
    substrate_detachment_kg_pa_s: float = 0.0
    precipitation_m_year_by_support: tuple[float, float] = (0.40, 0.20)
    evapotranspiration_m_year_by_support: tuple[float, float] = (0.08, 0.08)
    infiltration_capacity_m_year_by_support: tuple[float, float] = (0.12, 0.12)
    outlet_open: bool = True
    sediment_transport_enabled: bool = True
    mechanical_model: str = "MAXWELL"
    strike_length_m: float = 1.0
    interface_stiffness_pa_per_m: float = 1.0e12
    deep_initial_inventory_j_by_support: tuple[float, float] = (1.0e12, 0.6e12)
    deep_zeta_by_support: tuple[float, float] = (0.4, 0.55)
    deep_mobility_per_year: float = 0.02

    def validate(self) -> int:
        vals = (self.duration_years, self.external_step_years, self.hydrology_dt_seconds,
                self.opening_rate_m_year, self.strike_length_m,
                self.interface_stiffness_pa_per_m, self.deep_mobility_per_year,
                self.sediment_density_kg_m3,
                *self.prescribed_uplift_total_m_by_support,
                *self.surface_initial_relief_m_by_support, *self.surface_initial_cover_m_by_support,
                *self.precipitation_m_year_by_support,
                *self.evapotranspiration_m_year_by_support,
                *self.infiltration_capacity_m_year_by_support,
                *self.substrate_initial_thickness_m_by_support,
                *self.substrate_density_kg_m3_by_support,
                self.substrate_critical_shear_pa, self.substrate_detachment_kg_pa_s,
                *self.deep_initial_inventory_j_by_support, *self.deep_zeta_by_support)
        if any(not math.isfinite(float(x)) for x in vals):
            raise SurfaceMicrodomainError("UNIFIED_CONFIG_NONFINITE")
        if (self.duration_years <= 0 or self.external_step_years <= 0
                or self.hydrology_dt_seconds <= 0 or self.hydrology_dt_seconds > SECONDS_PER_YEAR
                or self.opening_rate_m_year < 0 or self.strike_length_m <= 0
                or self.interface_stiffness_pa_per_m <= 0 or self.deep_mobility_per_year < 0
                or self.sediment_density_kg_m3 <= 0
                or any(x < 0 for x in self.substrate_initial_thickness_m_by_support)
                or any(x <= 0 for x in self.substrate_density_kg_m3_by_support)
                or self.substrate_critical_shear_pa < 0 or self.substrate_detachment_kg_pa_s < 0
                or len(self.substrate_material_id_by_support) != 2
                or any(not x for x in self.substrate_material_id_by_support)
                or self.mechanical_model not in {"ELASTIC", "MAXWELL"}):
            raise SurfaceMicrodomainError("UNIFIED_CONFIG_OUT_OF_RANGE")
        steps = round(self.duration_years / self.external_step_years)
        if not math.isclose(self.duration_years / self.external_step_years, steps,
                            rel_tol=0.0, abs_tol=1e-12):
            raise SurfaceMicrodomainError("UNIFIED_EXTERNAL_STEPS_NOT_INTEGRAL")
        hydro_steps = self.external_step_years * SECONDS_PER_YEAR / self.hydrology_dt_seconds
        if not math.isclose(hydro_steps, round(hydro_steps), rel_tol=0.0, abs_tol=1e-8):
            raise SurfaceMicrodomainError("UNIFIED_HYDRO_SUBSTEPS_NOT_INTEGRAL")
        if any(x < 0 for x in (*self.prescribed_uplift_total_m_by_support,
                               *self.surface_initial_cover_m_by_support,
                               *self.precipitation_m_year_by_support,
                               *self.evapotranspiration_m_year_by_support,
                               *self.infiltration_capacity_m_year_by_support,
                               *self.deep_initial_inventory_j_by_support)):
            raise SurfaceMicrodomainError("UNIFIED_NEGATIVE_INPUT")
        if any(not 0 <= x <= 1 for x in self.deep_zeta_by_support):
            raise SurfaceMicrodomainError("UNIFIED_ZETA_OUT_OF_RANGE")
        return steps


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


CHECKPOINT_SCHEMA = "ARCANA_R6_UNIFIED_MULTIPHYSICS_CHECKPOINT_V1"
CHECKPOINT_SCHEMA_HISTORY_INDEPENDENT = "ARCANA_R6_UNIFIED_MULTIPHYSICS_CHECKPOINT_V2"


def _empty_history_accumulators(initial_deep: tuple[float, ...] | list[float]) -> dict[str, Any]:
    return {
        "material_flows": {
            "bedrock_detachment_kg_by_material_id": {},
            "outlet_export_kg_by_material_id": {},
            "deposition_kg_by_material_id": {},
            "internal_transfer_kg_by_material_id": {},
            "mobile_cover_erosion_kg_by_material_id": {},
        },
        "mechanical": {"external_work_j": 0.0, "viscous_dissipation_j": 0.0,
                       "algorithmic_energy_increment_j": 0.0},
        "deep": {"gross_internal_transport_j": 0.0, "net_transport_0_to_1_j": 0.0,
                 "minimum_reservoir_stock_j": min(float(x) for x in initial_deep)},
    }


def _accumulate_history_record(accumulators: dict[str, Any], row: Mapping[str, Any]) -> None:
    flows = row.get("material_flows", {})
    for name in accumulators["material_flows"]:
        target = accumulators["material_flows"][name]
        for material_id, value in flows.get(name, {}).items():
            target[material_id] = target.get(material_id, 0.0) + float(value)
    mechanics = row["mechanics"]
    for source, target in (("external_work_increment_j", "external_work_j"),
                           ("viscous_dissipation_increment_j", "viscous_dissipation_j"),
                           ("algorithmic_energy_increment_j", "algorithmic_energy_increment_j")):
        accumulators["mechanical"][target] += float(mechanics[source])
    deep = row["deep"]
    transport = float(deep.get("transport_flux_0_to_1_j", 0.0))
    accumulators["deep"]["gross_internal_transport_j"] += abs(transport)
    accumulators["deep"]["net_transport_0_to_1_j"] += transport
    stocks = deep.get("inventory_j_by_material_volume", {}).values()
    if stocks:
        accumulators["deep"]["minimum_reservoir_stock_j"] = min(
            accumulators["deep"]["minimum_reservoir_stock_j"],
            *(float(value) for value in stocks))


def _validate_history_accumulators(value: Any) -> None:
    expected = {
        "material_flows": {"bedrock_detachment_kg_by_material_id", "outlet_export_kg_by_material_id",
                           "deposition_kg_by_material_id", "internal_transfer_kg_by_material_id",
                           "mobile_cover_erosion_kg_by_material_id"},
        "mechanical": {"external_work_j", "viscous_dissipation_j", "algorithmic_energy_increment_j"},
        "deep": {"gross_internal_transport_j", "net_transport_0_to_1_j", "minimum_reservoir_stock_j"},
    }
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise SurfaceMicrodomainError("UNIFIED_FRONTIER_ACCUMULATORS_INVALID")
    for group, keys in expected.items():
        row = value[group]
        if not isinstance(row, Mapping) or set(row) != keys:
            raise SurfaceMicrodomainError("UNIFIED_FRONTIER_ACCUMULATORS_INVALID")
        for item in row.values():
            values = item.values() if isinstance(item, Mapping) else (item,)
            for number in values:
                if (not isinstance(number, (int, float)) or isinstance(number, bool)
                        or not math.isfinite(float(number))):
                    raise SurfaceMicrodomainError("UNIFIED_FRONTIER_ACCUMULATORS_NONFINITE")


def seal_unified_checkpoint(state: Mapping[str, Any]) -> dict[str, Any]:
    """Add corruption detection to a portable JSON checkpoint (not authentication)."""
    body = json.loads(json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False))
    schema = (CHECKPOINT_SCHEMA_HISTORY_INDEPENDENT
              if body.get("history_independent_continuation") is True else CHECKPOINT_SCHEMA)
    envelope = {"schema": schema, "state": body}
    envelope["state_sha256"] = _canonical_sha(envelope)
    return envelope


def verify_unified_checkpoint(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    if checkpoint.get("schema") not in {CHECKPOINT_SCHEMA, CHECKPOINT_SCHEMA_HISTORY_INDEPENDENT} or not isinstance(checkpoint.get("state"), Mapping):
        raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_SCHEMA_INVALID")
    expected = checkpoint.get("state_sha256")
    unsigned = {"schema": checkpoint["schema"], "state": checkpoint["state"]}
    if not isinstance(expected, str) or _canonical_sha(unsigned) != expected:
        raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_DIGEST_MISMATCH")
    state = json.loads(json.dumps(checkpoint["state"], sort_keys=True, allow_nan=False))
    if checkpoint["schema"] == CHECKPOINT_SCHEMA_HISTORY_INDEPENDENT:
        if state.get("history_independent_continuation") is not True or "records" in state:
            raise SurfaceMicrodomainError("UNIFIED_FRONTIER_HISTORY_INVALID")
        _validate_history_accumulators(state.get("history_accumulators"))
    return state


def serialize_unified_checkpoint(checkpoint: Mapping[str, Any]) -> bytes:
    verify_unified_checkpoint(checkpoint)
    return json.dumps(checkpoint, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def parse_unified_checkpoint(payload: bytes | str) -> dict[str, Any]:
    try:
        checkpoint = json.loads(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_JSON_INVALID") from exc
    if not isinstance(checkpoint, dict):
        raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_JSON_INVALID")
    verify_unified_checkpoint(checkpoint)
    return checkpoint


def _state_from_payload(payload: Mapping[str, Any]) -> ReducedState:
    return ReducedState(
        time_s=float(payload["time_s"]), initial_width_m=float(payload["initial_width_m"]),
        width_m=float(payload["width_m"]), initial_crust_m=float(payload["initial_crust_m"]),
        initial_lithosphere_m=float(payload["initial_lithosphere_m"]), crust_m=float(payload["crust_m"]),
        lithosphere_m=float(payload["lithosphere_m"]), beta=float(payload["beta"]),
        accumulated_strain=float(payload["accumulated_strain"]), crust_fraction=float(payload["crust_fraction"]),
        material_coordinate=tuple(float(x) for x in payload["material_coordinate"]),
        temperature_k=tuple(float(x) for x in payload["temperature_k"]),
        materials=tuple(NodeMaterial(**row) for row in payload["materials"]),
        surface_temperature_k=float(payload["surface_temperature_k"]),
        base_temperature_k=float(payload["base_temperature_k"]))


def unified_states_from_checkpoint(checkpoint: Mapping[str, Any]) -> dict[str, ReducedState]:
    state = verify_unified_checkpoint(checkpoint)
    return {support: _state_from_payload(payload)
            for support, payload in state["thermal_states_by_support"].items()}


def _role_parameter_maps(states: Mapping[str, ReducedState]) -> tuple[dict[str, float], dict[str, float]]:
    roles = {material.role_id for state in states.values() for material in state.materials}
    young = {
        "CONTINENTAL_CRUST_REFERENCE": 30.0e9,
        "LITHOSPHERIC_MANTLE_REFERENCE": 70.0e9,
    }
    eta = {
        "CONTINENTAL_CRUST_REFERENCE": 2.0e19,
        "LITHOSPHERIC_MANTLE_REFERENCE": 4.0e19,
    }
    if roles - set(young):
        raise SurfaceMicrodomainError("UNIFIED_UNKNOWN_MATERIAL_ROLE:" + ",".join(sorted(roles - set(young))))
    return young, eta


def _new_hydrology_state(states: Mapping[str, ReducedState], source_identity: Mapping[str, Any],
                         config: UnifiedConfig, surface_prior: Mapping[str, Any] | None,
                         *, precipitation: tuple[float, float], uplift: tuple[float, float],
                         external_step_years: float) -> dict[str, Any]:
    if surface_prior is None:
        bedrock = config.surface_initial_relief_m_by_support
        cover = config.surface_initial_cover_m_by_support
        water = (0.0, 0.0)
        suspended = (0.0, 0.0)
        mobile_material = None
        suspended_material = None
        geometry, _, _ = _surface_grid_geometry(source_identity)
        substrate_mass = tuple(config.substrate_initial_thickness_m_by_support[i]
                               * geometry[support][2] * config.substrate_density_kg_m3_by_support[i]
                               for i, support in enumerate(SUPPORTS))
    else:
        by_support = {cell["support_id"]: cell for cell in surface_prior["cells"]}
        bedrock = tuple(float(by_support[s]["bedrock_elevation_m"]) for s in SUPPORTS)
        cover = tuple(float(by_support[s]["mobile_cover_thickness_m"]) for s in SUPPORTS)
        water = tuple(float(by_support[s]["water_storage_m3"]) for s in SUPPORTS)
        suspended = tuple(float(by_support[s]["suspended_sediment_kg"]) for s in SUPPORTS)
        mobile_material = tuple(dict(by_support[s]["mobile_material_mass_kg_by_id"]) for s in SUPPORTS)
        suspended_material = tuple(dict(by_support[s]["suspended_material_mass_kg_by_id"]) for s in SUPPORTS)
        substrate_mass = tuple(float(by_support[s]["substrate_mass_kg"]) for s in SUPPORTS)
    surface = SurfaceConfig(
        duration_years=external_step_years,
        dt_years=external_step_years,
        initial_relief_m=bedrock,
        initial_cover_m=cover,
        prescribed_uplift_m=uplift,
        sediment_density_kg_m3=config.sediment_density_kg_m3,
        enable_surface_transport=False,
    )
    hydro = HydroConfig(
        duration_years=external_step_years,
        hydrology_dt_seconds=config.hydrology_dt_seconds,
        precipitation_m_year_by_support=precipitation,
        evapotranspiration_m_year_by_support=config.evapotranspiration_m_year_by_support,
        infiltration_capacity_m_year_by_support=config.infiltration_capacity_m_year_by_support,
        initial_water_storage_m3_by_support=water,
        initial_suspended_sediment_kg_by_support=suspended,
        initial_mobile_material_kg_by_support=mobile_material,
        initial_suspended_material_kg_by_support=suspended_material,
        initial_substrate_mass_kg_by_support=substrate_mass,
        substrate_material_id_by_support=config.substrate_material_id_by_support,
        substrate_density_kg_m3_by_support=config.substrate_density_kg_m3_by_support,
        substrate_erosion_enabled=config.substrate_erosion_enabled,
        substrate_critical_shear_pa=config.substrate_critical_shear_pa,
        substrate_detachment_kg_pa_s=config.substrate_detachment_kg_pa_s,
        outlet_open=config.outlet_open,
        sediment_transport_enabled=config.sediment_transport_enabled,
        surface_config=surface,
    )
    return run_hydrology_scenario(
        {support: states[support].payload() for support in SUPPORTS}, source_identity, config=hydro)


def run_unified_microdomain(
    initial_states_by_support: Mapping[str, ReducedState],
    source_identity: Mapping[str, Any],
    *,
    config: UnifiedConfig = UnifiedConfig(),
    deep_mode: str = "ACTIVE_SYNTHETIC_TRANSPORT",
    precipitation_m_year_by_support: tuple[float, float] | None = None,
    uplift_scale: float = 1.0,
    checkpoint: Mapping[str, Any] | None = None,
    segment_years: float | None = None,
    history_independent_continuation: bool = False,
    history_consumer: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Advance all included domains on one external clock and report each handoff."""
    if history_independent_continuation and history_consumer is None:
        raise SurfaceMicrodomainError("UNIFIED_HISTORY_CONSUMER_REQUIRED")
    planned_steps = config.validate()
    if set(initial_states_by_support) != set(SUPPORTS):
        raise SurfaceMicrodomainError("UNIFIED_SUPPORT_SET_MISMATCH")
    if deep_mode not in {"ACTIVE_SYNTHETIC_TRANSPORT", "PASSIVE"}:
        raise SurfaceMicrodomainError("UNIFIED_DEEP_MODE_INVALID")
    if not math.isfinite(uplift_scale) or uplift_scale < 0:
        raise SurfaceMicrodomainError("UNIFIED_UPLIFT_SCALE_INVALID")
    states = dict(initial_states_by_support)
    start_times = {state.time_s for state in states.values()}
    if len(start_times) != 1:
        raise SurfaceMicrodomainError("UNIFIED_SUPPORT_TIME_MISMATCH")
    if not all(math.isfinite(value) and value >= 0 for value in start_times):
        raise SurfaceMicrodomainError("UNIFIED_SUPPORT_TIME_INVALID")
    precipitation = precipitation_m_year_by_support or config.precipitation_m_year_by_support
    if len(precipitation) != 2 or any(not math.isfinite(x) or x < 0 for x in precipitation):
        raise SurfaceMicrodomainError("UNIFIED_PRECIPITATION_INVALID")
    if segment_years is None:
        run_steps = planned_steps
    else:
        if not math.isfinite(segment_years) or segment_years <= 0:
            raise SurfaceMicrodomainError("UNIFIED_SEGMENT_DURATION_INVALID")
        ratio = segment_years / config.external_step_years
        run_steps = round(ratio)
        if not math.isclose(ratio, run_steps, rel_tol=0.0, abs_tol=1e-12):
            raise SurfaceMicrodomainError("UNIFIED_SEGMENT_DURATION_INVALID")
    if run_steps <= 0:
        raise SurfaceMicrodomainError("UNIFIED_SEGMENT_DURATION_INVALID")
    run_identity = {
        "source_identity": dict(source_identity), "source_sha256": _canonical_sha(source_identity),
        "config": asdict(config), "config_sha256": _canonical_sha(asdict(config)),
        "deep_mode": deep_mode, "precipitation": list(precipitation), "uplift_scale": uplift_scale,
    }
    identity_sha = _canonical_sha(run_identity)
    offset = 0
    if checkpoint is None:
        initial_payloads = {support: state.payload() for support, state in states.items()}
        initial_digests = {support: _state_digest(state) for support, state in states.items()}
        young_by_role, eta_by_role = _role_parameter_maps(states)
        mechanical_reference_cells = {support: _column_geometry(state, support, config.strike_length_m)
                                      for support, state in states.items()}
        viscous_history = {row["cell_id"]: 0.0 for support in SUPPORTS
                           for row in mechanical_reference_cells[support]}
        total_strain_history = dict(viscous_history)
        opening_total = 0.0
        previous_disp = {support: 0.0 for support in SUPPORTS}
        previous_gap = previous_energy = 0.0
        surface_state: dict[str, Any] | None = None
        deep_stocks = list(config.deep_initial_inventory_j_by_support)
        initial_deep = sum(deep_stocks)
        deep_material_ids = [f"{support}:DEEP:RESERVOIR:00" for support in SUPPORTS]
        zeta = list(config.deep_zeta_by_support)
        modal_params_by_role = {role: (0.4 + 0.1 * i, 0.2, 0.1)
                                for i, role in enumerate(sorted({m.role_id for state in states.values()
                                                                  for m in state.materials}))}
        initial_geometry, _, _ = _surface_grid_geometry(source_identity)
        initial_surface_snapshot = {
            support: {"surface_cell_id": f"{support}:SURFACE:PATCH00",
                      "bedrock_elevation_m": config.surface_initial_relief_m_by_support[i],
                      "cover_mass_kg": (config.surface_initial_cover_m_by_support[i]
                                        * initial_geometry[support][2] * config.sediment_density_kg_m3),
                      "surface_elevation_m": (config.surface_initial_relief_m_by_support[i]
                                              + config.surface_initial_cover_m_by_support[i])}
            for i, support in enumerate(SUPPORTS)}
        initial_cover_mass = sum(row["cover_mass_kg"] for row in initial_surface_snapshot.values())
        initial_water = 0.0
        initial_suspended = 0.0
        initial_substrate_mass = sum(config.substrate_initial_thickness_m_by_support[i]
                                     * initial_geometry[support][2]
                                     * config.substrate_density_kg_m3_by_support[i]
                                     for i, support in enumerate(SUPPORTS))
        initial_material_inventory = {
            support: {
                "substrate": {"material_id": config.substrate_material_id_by_support[i],
                              "mass_kg": config.substrate_initial_thickness_m_by_support[i]
                                        * initial_geometry[support][2]
                                        * config.substrate_density_kg_m3_by_support[i],
                              "composition": "UNKNOWN_NOT_INFERRED_FROM_ROLE",
                              "provenance": "SYNTHETIC_BULK_BENCHMARK"},
                "mobile_cover": {"material_id": f"SYNTHETIC_INITIAL_COVER:{support}",
                                 "mass_kg": initial_surface_snapshot[support]["cover_mass_kg"],
                                 "composition": "UNKNOWN_NOT_INFERRED_FROM_ROLE",
                                 "provenance": "SYNTHETIC_INITIAL_COVER"},
                "suspended": [],
            } for i, support in enumerate(SUPPORTS)}
        total_water = {key: 0.0 for key in ("precipitation_input_m3", "evapotranspiration_sink_m3",
                                            "infiltration_sink_m3", "internal_transfer_m3", "outlet_export_m3")}
        total_sediment = {key: 0.0 for key in ("erosion_from_cover_kg", "internal_suspended_transfer_kg",
                                               "deposition_to_cover_kg", "outlet_sediment_export_kg")}
        total_substrate_erosion = 0.0
        water_roundoff_tolerance = sediment_roundoff_tolerance = geometry_roundoff_tolerance = 0.0
        records: list[dict[str, Any]] = []
        history_accumulators = _empty_history_accumulators(deep_stocks)
    else:
        saved = verify_unified_checkpoint(checkpoint)
        if (saved.get("run_identity_sha256") != identity_sha
                or _canonical_sha(saved.get("run_identity")) != identity_sha
                or saved.get("planned_external_steps") != planned_steps):
            raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_RUN_IDENTITY_MISMATCH")
        if saved.get("thermal_states_by_support") != {k: v.payload() for k, v in states.items()}:
            raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_THERMAL_STATE_MISMATCH")
        offset_value = saved.get("elapsed_external_steps")
        if (not isinstance(offset_value, int) or isinstance(offset_value, bool)
                or offset_value <= 0 or offset_value > planned_steps):
            raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_STEP_COUNT_INVALID")
        offset = offset_value
        initial_payloads, initial_digests = saved["initial_thermal_states"], saved["initial_state_sha256_by_support"]
        mechanical_reference_cells = saved["mechanical_reference_cells"]
        young_by_role, eta_by_role = _role_parameter_maps(
            {support: _state_from_payload(payload) for support, payload in initial_payloads.items()})
        viscous_history, total_strain_history = saved["viscous_strain"], saved["total_strain"]
        opening_total, previous_disp = float(saved["opening_total_m"]), saved["previous_displacement_m_by_support"]
        previous_gap, previous_energy = float(saved["previous_interface_gap_m"]), float(saved["previous_stored_energy_j"])
        surface_state = saved["surface_state"]
        deep_stocks, initial_deep = saved["deep_inventory_j_by_support"], float(saved["initial_deep_inventory_j"])
        if (len(deep_stocks) != 2 or any(not math.isfinite(float(x)) or float(x) < 0 for x in deep_stocks)):
            raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_DEEP_STATE_INVALID")
        deep_stocks = [float(x) for x in deep_stocks]
        deep_material_ids, zeta = saved["deep_volume_ids"], saved["deep_zeta_by_support"]
        modal_params_by_role = {key: tuple(value) for key, value in saved["synthetic_modal_parameters_by_role"].items()}
        initial_geometry = saved["initial_geometry_area_m2_by_support"]
        initial_surface_snapshot = saved["initial_surface_snapshot"]
        initial_cover_mass, initial_water = float(saved["initial_cover_mass_kg"]), float(saved["initial_water_storage_m3"])
        initial_suspended = float(saved["initial_suspended_sediment_kg"])
        initial_substrate_mass = float(saved["initial_substrate_mass_kg"])
        initial_material_inventory = saved["initial_material_inventory"]
        total_water, total_sediment = saved["cumulative_water"], saved["cumulative_sediment"]
        total_substrate_erosion = float(saved["cumulative_substrate_erosion_kg"])
        water_roundoff_tolerance, sediment_roundoff_tolerance = (
            float(saved["water_roundoff_tolerance_m3"]), float(saved["sediment_roundoff_tolerance_kg"]))
        geometry_roundoff_tolerance = float(saved["geometry_roundoff_tolerance_m3"])
        is_history_free = saved.get("history_independent_continuation") is True
        if history_independent_continuation and not is_history_free:
            raise SurfaceMicrodomainError("UNIFIED_HISTORY_INDEPENDENT_FRONTIER_REQUIRED")
        if is_history_free:
            if "records" in saved or not isinstance(saved.get("history_accumulators"), Mapping):
                raise SurfaceMicrodomainError("UNIFIED_FRONTIER_HISTORY_OR_ACCUMULATORS_INVALID")
            records = []
            history_accumulators = json.loads(json.dumps(saved["history_accumulators"], allow_nan=False))
        else:
            records = list(saved["records"])
            history_accumulators = json.loads(json.dumps(
                saved.get("history_accumulators", _empty_history_accumulators(config.deep_initial_inventory_j_by_support)),
                allow_nan=False))
            if "history_accumulators" not in saved:
                for old_record in records:
                    _accumulate_history_record(history_accumulators, old_record)
        if offset + run_steps > planned_steps:
            raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_EXCEEDS_PLANNED_DURATION")

    # Uplift is a run-level rate; it does not change when the same run is split.
    uplift_per_step = tuple(x * uplift_scale / planned_steps
                            for x in config.prescribed_uplift_total_m_by_support)

    for local_step_index in range(run_steps):
        step_index = offset + local_step_index
        t0 = next(iter(states.values())).time_s
        dt_s = config.external_step_years * SECONDS_PER_YEAR
        opening_increment = config.opening_rate_m_year * config.external_step_years
        opening_total += opening_increment
        cells = {support: _column_geometry(states[support], support, config.strike_length_m)
                 for support in SUPPORTS}
        strain_rate = opening_increment / max(
            0.5 * (states[SUPPORTS[0]].width_m + states[SUPPORTS[1]].width_m) * dt_s, 1e-30)
        rheology_profiles = {
            support: evaluate_reduced_state_column(
                states[support], cells[support], support_id=support,
                strain_rate_s=strain_rate, temperature_offset_k=0.0)
            for support in SUPPORTS
        }
        young_by_cell = {k: v for profile in rheology_profiles.values()
                         for k, v in profile["young_modulus_pa_by_cell"].items()}
        eta_by_cell = {k: v for profile in rheology_profiles.values()
                       for k, v in profile["eta_1d_pa_s_by_cell"].items()}
        mech = solve_layered_interface_increment(
            mechanical_reference_cells[SUPPORTS[0]], mechanical_reference_cells[SUPPORTS[1]],
            reference_width_a_m=states[SUPPORTS[0]].initial_width_m,
            reference_width_b_m=states[SUPPORTS[1]].initial_width_m,
            lithosphere_a_m=states[SUPPORTS[0]].initial_lithosphere_m,
            lithosphere_b_m=states[SUPPORTS[1]].initial_lithosphere_m,
            strike_length_m=config.strike_length_m,
            interface_stiffness_pa_per_m=config.interface_stiffness_pa_per_m,
            opening_total_m=opening_total, opening_increment_m=opening_increment,
            dt_s=dt_s, young_by_role=young_by_role, eta_by_role=eta_by_role,
            model=config.mechanical_model, viscous_strain=viscous_history,
            previous_total_strain=total_strain_history,
            previous_displacement_a_m=previous_disp[SUPPORTS[0]],
            previous_displacement_b_m=previous_disp[SUPPORTS[1]],
            previous_interface_gap_m=previous_gap, previous_stored_energy_j=previous_energy,
            young_by_cell=young_by_cell, eta_by_cell=eta_by_cell,
        )
        viscous_history = dict(mech["updated_viscous_strain"])
        total_strain_history = dict(mech["updated_total_strain"])
        previous_gap = mech["interface_gap_total_m"]
        previous_energy = mech["stored_energy_j"]
        extension_by_support = {
            SUPPORTS[0]: mech["column_a_displacement_increment_m"],
            SUPPORTS[1]: mech["column_b_displacement_increment_m"],
        }
        if any(value < -1e-12 for value in extension_by_support.values()):
            raise SurfaceMicrodomainError("UNIFIED_THERMAL_KERNEL_DOES_NOT_SUPPORT_COMPRESSION")
        next_states: dict[str, ReducedState] = {}
        thermal_diag: dict[str, Any] = {}
        for support in SUPPORTS:
            next_states[support], diag = pure_shear_thermal_step(
                states[support], duration_s=dt_s,
                extension_velocity_m_s=max(0.0, extension_by_support[support]) / dt_s)
            thermal_diag[support] = {
                "substeps": diag.substeps,
                "area_relative_error": diag.area_relative_error,
                "min_temperature_k": diag.min_temperature_k,
                "max_temperature_k": diag.max_temperature_k,
                "state_sha256": _state_digest(next_states[support]),
            }
            previous_disp[support] += extension_by_support[support]
        states = next_states

        hydrology = _new_hydrology_state(
            states, source_identity, config, surface_state,
            precipitation=precipitation, uplift=uplift_per_step,
            external_step_years=config.external_step_years)
        wb, sb = hydrology["water_balance"], hydrology["sediment_balance"]
        water_roundoff_tolerance += wb["roundoff_tolerance_m3"]
        sediment_roundoff_tolerance += sb["roundoff_tolerance_kg"]
        geometry_roundoff_tolerance += hydrology["geometry_balance"]["roundoff_tolerance_m3"]
        for key in total_water:
            total_water[key] += wb[key]
        for key in total_sediment:
            total_sediment[key] += sb[key]
        total_substrate_erosion += float(sb["bedrock_erosion_kg"])

        deep_ledger: dict[str, Any]
        if deep_mode == "ACTIVE_SYNTHETIC_TRANSPORT":
            geology_rows = []
            deep_cells = []
            for i, support in enumerate(SUPPORTS):
                material = states[support].materials[0]
                role = material.role_id
                coupling, detuning, modal_loss = modal_params_by_role[role]
                modal = ModalMaterial(
                    role, material.rho_kg_m3, material.cp_j_kg_k, material.k_w_m_k,
                    modal_coupling=coupling, modal_detuning=detuning, modal_loss=modal_loss,
                )
                geology_rows.append(GeologyState(
                    cell_id=deep_material_ids[i], material=modal,
                    strain=max(0.0, states[support].accumulated_strain),
                    thermal_state=_state_digest(states[support]),
                ))
                deep_cells.append(DeepCell(
                    cell_id=deep_material_ids[i], free_inventory_j=deep_stocks[i],
                    equilibrium_inventory_j=0.0, accessibility_zeta=zeta[i],
                    geological_accessibility_a_x=0.0,
                ))
            updated, deep_step = _advance_reservoirs(
                tuple(deep_cells), tuple(geology_rows),
                dt_years=config.external_step_years,
                mobility_per_year=config.deep_mobility_per_year,
            )
            deep_stocks = [float(x) for x in updated]
            zeta = [_structural_accessibility(config.deep_zeta_by_support[i],
                                               max(0.0, states[support].accumulated_strain))
                    for i, support in enumerate(SUPPORTS)]
            deep_ledger = {
                **deep_step,
                "mode": deep_mode,
                "inventory_before_j": sum(deep_cells[i].free_inventory_j for i in range(2)),
                "inventory_after_j": sum(deep_stocks),
                "inventory_residual_j": sum(deep_stocks) - sum(c.free_inventory_j for c in deep_cells),
                "inventory_j_by_material_volume": dict(zip(deep_material_ids, deep_stocks)),
                "zeta_by_material_volume": dict(zip(deep_material_ids, zeta)),
                "accessible_inventory_diagnostic_j_by_material_volume": {
                    deep_material_ids[i]: zeta[i] * deep_stocks[i] for i in range(2)},
                "thermal_energy_transfer_j": 0.0,
                "mechanical_work_transfer_j": 0.0,
            }
        else:
            deep_ledger = {
                "mode": deep_mode, "inventory_before_j": sum(deep_stocks),
                "inventory_after_j": sum(deep_stocks), "inventory_residual_j": 0.0,
                "inventory_j_by_material_volume": dict(zip(deep_material_ids, deep_stocks)),
                "zeta_by_material_volume": dict(zip(deep_material_ids, zeta)),
                "accessible_inventory_diagnostic_j_by_material_volume": {
                    deep_material_ids[i]: zeta[i] * deep_stocks[i] for i in range(2)},
                "thermal_energy_transfer_j": 0.0, "mechanical_work_transfer_j": 0.0,
            }
        surface_state = hydrology
        record = {
            "step": step_index + 1,
            "time_start_s": t0,
            "time_end_s": next(iter(states.values())).time_s,
            "elapsed_years": (step_index + 1) * config.external_step_years,
            "material_volumes": {
                support: [{"material_volume_id": row["cell_id"],
                           "material_role_id": row["material_role_id"],
                           "volume_m3": row["volume_m3"],
                           "temperature_k": row["temperature_k"]}
                          for row in _column_geometry(states[support], support, config.strike_length_m)]
                for support in SUPPORTS
            },
            "mechanics": {
                "model": config.mechanical_model,
                "interface_force_n": mech["interface_force_n"],
                "interface_stress_pa": mech["interface_stress_pa"],
                "interface_area_m2": mech["interface_area_m2"],
                "displacement_increment_m_by_support": extension_by_support,
                "strain_by_support": mech["strain_by_support"],
                "stored_energy_j": mech["stored_energy_j"],
                "external_work_increment_j": mech["external_work_increment_j"],
                "viscous_dissipation_increment_j": mech["viscous_dissipation_increment_j"],
                "algorithmic_energy_increment_j": mech["algorithmic_energy_increment_j"],
                "energy_balance_residual_j": mech["energy_balance_residual_j"],
                "rheology_authority": "ASPECT_STYLE_DRY_OLIVINE_BENCHMARK_ON_R6_T_RHO_DEPTH_PROXY_NOT_MATERIAL_CALIBRATION",
                "rheology_provider_nodes": {
                    support: [{key: node[key] for key in (
                        "cell_id", "material_role_id", "r6_temperature_k", "depth_proxy_m",
                        "pressure_proxy_pa", "young_modulus_pa", "equivalent_1d_maxwell_viscosity_pa_s")}
                              for node in rheology_profiles[support]["nodes"]]
                    for support in SUPPORTS
                },
                "total_strain_by_material_volume": dict(total_strain_history),
                "viscous_strain_by_material_volume": dict(viscous_history),
            },
            "thermal": thermal_diag,
            "surface_hydrology": {
                "surface_cells": [{"surface_cell_id": cell["surface_cell_id"],
                                   "support_id": cell["support_id"],
                                   "elevation_m": cell["surface_elevation_m"],
                                   "bedrock_elevation_m": cell["bedrock_elevation_m"],
                                   "mobile_cover_mass_kg": cell["mobile_cover_mass_kg"],
                                   "water_storage_m3": cell["water_storage_m3"],
                                   "suspended_sediment_kg": cell["suspended_sediment_kg"],
                                   "mobile_material_mass_kg_by_id": cell["mobile_material_mass_kg_by_id"],
                                   "suspended_material_mass_kg_by_id": cell["suspended_material_mass_kg_by_id"],
                                   "substrate_material_id": cell["substrate_material_id"],
                                   "substrate_mass_kg": cell["substrate_mass_kg"],
                                   "bedrock_erosion_kg": cell["bedrock_erosion_kg"]}
                                  for cell in hydrology["cells"]],
                "water_balance_step": wb,
                "sediment_balance_step": sb,
                "geometry_balance_step": hydrology["geometry_balance"],
                "hydraulic_diagnostics": hydrology["hydraulic_diagnostics"],
                "hydraulic_connectivity": hydrology["configuration"]["hydraulic_interface_status"],
            },
            "material_flows": {
                "time_start_s": t0, "time_end_s": next(iter(states.values())).time_s,
                "erosion_type": "PHYSICAL_HYDRAULIC_DETACHMENT" if config.substrate_erosion_enabled else "NONE",
                "bedrock_detachment_kg_by_material_id": sb["bedrock_erosion_kg_by_material_id"],
                "mobile_cover_erosion_kg_by_material_id": sb["erosion_from_mobile_by_material_id"],
                "internal_transfer_kg_by_material_id": sb["internal_transfer_kg_by_material_id"],
                "internal_transport_kg_by_route_and_material": sb["internal_transport_kg_by_route_and_material"],
                "deposition_kg_by_material_id": sb["deposition_kg_by_material_id"],
                "deposition_kg_by_surface_cell_and_material": sb["deposition_kg_by_surface_cell_and_material"],
                "outlet_export_kg_by_material_id": sb["outlet_export_kg_by_material_id"],
                "outlet_export_kg_by_surface_cell_and_material": sb["outlet_export_kg_by_surface_cell_and_material"],
                "chemical_weathering": "NOT_MODELED",
                "lithification": "NOT_MODELED",
            },
            "deep": deep_ledger,
        }
        _accumulate_history_record(history_accumulators, record)
        records.append(record)
        if history_consumer is not None:
            history_consumer("UNIFIED_STEP", record)

    final_states = {support: state.payload() for support, state in states.items()}
    final_surface = {cell["support_id"]: cell for cell in surface_state["cells"]}
    final_cover_mass = sum(cell["mobile_cover_mass_kg"] for cell in final_surface.values())
    final_suspended = sum(cell["suspended_sediment_kg"] for cell in final_surface.values())
    final_water = sum(cell["water_storage_m3"] for cell in final_surface.values())
    water_residual = (initial_water + total_water["precipitation_input_m3"]
                      - total_water["evapotranspiration_sink_m3"]
                      - total_water["infiltration_sink_m3"] - total_water["outlet_export_m3"]
                      - final_water)
    sediment_residual = (initial_cover_mass + initial_suspended + total_substrate_erosion
                         - final_cover_mass - final_suspended
                         - total_sediment["outlet_sediment_export_kg"])
    final_substrate_mass = sum(cell["substrate_mass_kg"] for cell in final_surface.values())
    substrate_residual = initial_substrate_mass - final_substrate_mass - total_substrate_erosion
    final_surface_volume = sum(cell["surface_elevation_m"] * cell["surface_area_m2"]
                               for cell in final_surface.values())
    initial_surface_volume = sum(
        row["surface_elevation_m"] * initial_geometry[support][2]
        for support, row in initial_surface_snapshot.items())
    prescribed_uplift_volume = sum(
        config.prescribed_uplift_total_m_by_support[i] * uplift_scale * ((offset + run_steps) / planned_steps)
        * initial_geometry[support][2] for i, support in enumerate(SUPPORTS))
    sediment_export_volume = total_sediment["outlet_sediment_export_kg"] / config.sediment_density_kg_m3
    final_suspension_volume = final_suspended / config.sediment_density_kg_m3
    flow_accumulators = history_accumulators["material_flows"]
    eroded_by_material = flow_accumulators["bedrock_detachment_kg_by_material_id"]
    exported_by_material = flow_accumulators["outlet_export_kg_by_material_id"]
    deposited_by_material = flow_accumulators["deposition_kg_by_material_id"]
    internal_by_material = flow_accumulators["internal_transfer_kg_by_material_id"]
    mobile_erosion_by_material = flow_accumulators["mobile_cover_erosion_kg_by_material_id"]
    substrate_bulk_expansion = sum(
        eroded_by_material.get(config.substrate_material_id_by_support[i], 0.0)
        * (1.0 / config.sediment_density_kg_m3 - 1.0 / config.substrate_density_kg_m3_by_support[i])
        for i in range(2))
    geometry_residual = (final_surface_volume - initial_surface_volume - prescribed_uplift_volume
                         + sediment_export_volume + final_suspension_volume - substrate_bulk_expansion)
    deep_residual = sum(deep_stocks) - initial_deep
    mechanical_work = history_accumulators["mechanical"]["external_work_j"]
    mechanical_stored = previous_energy
    mechanical_viscous = history_accumulators["mechanical"]["viscous_dissipation_j"]
    mechanical_algorithmic = history_accumulators["mechanical"]["algorithmic_energy_increment_j"]
    mechanical_energy_residual = (mechanical_work - mechanical_stored
                                  - mechanical_viscous - mechanical_algorithmic)
    substrate_roundoff_tolerance = max(1e-6, 256.0 * math.ulp(max(initial_substrate_mass, 1.0)))
    if any(not math.isfinite(x) for x in (water_residual, sediment_residual, deep_residual, substrate_residual)):
        raise SurfaceMicrodomainError("UNIFIED_FINAL_LEDGER_NONFINITE")
    if abs(deep_residual) > max(1e-5, initial_deep * 1e-12):
        raise SurfaceMicrodomainError("UNIFIED_DEEP_LEDGER_FAILED")
    if abs(water_residual) > water_roundoff_tolerance:
        raise SurfaceMicrodomainError("UNIFIED_WATER_LEDGER_FAILED")
    if abs(sediment_residual) > sediment_roundoff_tolerance:
        raise SurfaceMicrodomainError("UNIFIED_SEDIMENT_LEDGER_FAILED")
    if abs(substrate_residual) > substrate_roundoff_tolerance:
        raise SurfaceMicrodomainError("UNIFIED_SUBSTRATE_LEDGER_FAILED")
    if abs(geometry_residual) > geometry_roundoff_tolerance:
        raise SurfaceMicrodomainError("UNIFIED_GEOMETRY_LEDGER_FAILED")
    if any(not math.isfinite(value) for state in states.values()
           for value in (*state.temperature_k, state.width_m, state.crust_m, state.lithosphere_m)):
        raise SurfaceMicrodomainError("UNIFIED_THERMAL_STATE_NONFINITE")
    checkpoint_state = {
        "run_identity": run_identity,
        "run_identity_sha256": identity_sha,
        "source_identity": dict(source_identity),
        "thermal_states_by_support": {support: state.payload() for support, state in states.items()},
        "initial_thermal_states": initial_payloads,
        "initial_state_sha256_by_support": initial_digests,
        "elapsed_external_steps": offset + run_steps,
        "planned_external_steps": planned_steps,
        "mechanical_reference_cells": mechanical_reference_cells,
        "viscous_strain": viscous_history,
        "total_strain": total_strain_history,
        "opening_total_m": opening_total,
        "previous_displacement_m_by_support": previous_disp,
        "previous_interface_gap_m": previous_gap,
        "previous_stored_energy_j": previous_energy,
        "surface_state": {"cells": surface_state["cells"]},
        "deep_inventory_j_by_support": deep_stocks,
        "initial_deep_inventory_j": initial_deep,
        "deep_volume_ids": deep_material_ids,
        "deep_zeta_by_support": zeta,
        "synthetic_modal_parameters_by_role": modal_params_by_role,
        "initial_geometry_area_m2_by_support": {key: list(value) for key, value in initial_geometry.items()},
        "initial_surface_snapshot": initial_surface_snapshot,
        "initial_cover_mass_kg": initial_cover_mass,
        "initial_water_storage_m3": initial_water,
        "initial_suspended_sediment_kg": initial_suspended,
        "initial_substrate_mass_kg": initial_substrate_mass,
        "initial_material_inventory": initial_material_inventory,
        "cumulative_water": total_water,
        "cumulative_sediment": total_sediment,
        "cumulative_substrate_erosion_kg": total_substrate_erosion,
        "water_roundoff_tolerance_m3": water_roundoff_tolerance,
        "sediment_roundoff_tolerance_kg": sediment_roundoff_tolerance,
        "geometry_roundoff_tolerance_m3": geometry_roundoff_tolerance,
    }
    if history_independent_continuation:
        checkpoint_state["history_independent_continuation"] = True
        checkpoint_state["history_accumulators"] = history_accumulators
    else:
        checkpoint_state["records"] = records
    checkpoint_result = seal_unified_checkpoint(checkpoint_state)
    return {
        "schema": "ARCANA_R6_UNIFIED_MULTIPHYSICS_MICRODOMAIN_V1",
        "scope": "NONCANONICAL_SYNTHETICALLY_FORCED_SHARED_TIME_WINDOW",
        "source_identity": dict(source_identity),
        "configuration": {
            "duration_years": config.duration_years,
            "external_step_years": config.external_step_years,
            "planned_external_step_count": planned_steps,
            "segment_external_step_count": run_steps,
            "elapsed_external_step_count": offset + run_steps,
            "hydrology_dt_seconds": config.hydrology_dt_seconds,
            "mechanical_model": config.mechanical_model,
            "opening_rate_m_year": config.opening_rate_m_year,
            "interface_stiffness_pa_per_m": config.interface_stiffness_pa_per_m,
            "strike_length_m": config.strike_length_m,
            "deep_mode": deep_mode,
            "deep_initial_inventory_j_by_support": dict(zip(
                SUPPORTS, config.deep_initial_inventory_j_by_support)),
            "deep_initial_zeta_by_support": dict(zip(SUPPORTS, config.deep_zeta_by_support)),
            "deep_mobility_per_year": config.deep_mobility_per_year,
            "synthetic_modal_parameters_by_role": {
                role: {"coupling": values[0], "detuning": values[1], "loss": values[2],
                       "authority": "SYNTHETIC_ENGINEERING_PARAMETER"}
                for role, values in modal_params_by_role.items()},
            "precipitation_m_year_by_support": dict(zip(SUPPORTS, precipitation)),
            "evapotranspiration_m_year_by_support": dict(zip(
                SUPPORTS, config.evapotranspiration_m_year_by_support)),
            "infiltration_capacity_m_year_by_support": dict(zip(
                SUPPORTS, config.infiltration_capacity_m_year_by_support)),
            "outlet_open": config.outlet_open,
            "sediment_transport_enabled": config.sediment_transport_enabled,
            "prescribed_uplift_total_m_by_support": dict(zip(
                SUPPORTS, (x * uplift_scale for x in config.prescribed_uplift_total_m_by_support))),
            "surface_initial_relief_m_by_support": dict(zip(
                SUPPORTS, config.surface_initial_relief_m_by_support)),
            "surface_initial_cover_m_by_support": dict(zip(
                SUPPORTS, config.surface_initial_cover_m_by_support)),
            "sediment_density_kg_m3": config.sediment_density_kg_m3,
            "substrate_initial_thickness_m_by_support": dict(zip(SUPPORTS, config.substrate_initial_thickness_m_by_support)),
            "substrate_density_kg_m3_by_support": dict(zip(SUPPORTS, config.substrate_density_kg_m3_by_support)),
            "substrate_material_id_by_support": dict(zip(SUPPORTS, config.substrate_material_id_by_support)),
            "substrate_erosion_enabled": config.substrate_erosion_enabled,
            "substrate_critical_shear_pa": config.substrate_critical_shear_pa,
            "substrate_detachment_kg_pa_s": config.substrate_detachment_kg_pa_s,
            "substrate_erosion_law": "m_dot=k_d*max(tau_b-tau_c,0); tau_b=rho_w*g*R_h*S" if config.substrate_erosion_enabled else "DISABLED",
            "operator_order": ["MAXWELL_MECHANICS", "THERMAL_PURE_SHEAR", "PRESCRIBED_UPLIFT_AND_SURFACE_GEOMETRY",
                               "HYDROLOGY_SEDIMENT", "DEEP_SYNTHETIC_RESERVOIR"],
            "physical_feedbacks": {
                "mechanics_to_thermal_geometry": "MECHANICAL_DISPLACEMENT_INCREMENT_APPLIED_ONCE_AS_PURE_SHEAR_EXTENSION",
                "uplift_to_hydrology": "PRESCRIBED_UPLIFT_CHANGES_SURFACE_HEAD_BEFORE_RUNOFF",
                "water_to_sediment": "CAPACITY_LIMITED_MOBILE_COVER_EROSION_AND_ROUTING",
                "sediment_to_surface": "COVER_MASS_CHANGES_SURFACE_ELEVATION",
                "thermal_to_deep_energy": "NONE",
                "mechanical_work_to_deep_energy": "NONE",
                "deep_to_other_domains": "NONE",
            },
        },
        "identity_semantics": {
            "material_volumes": "SUPPORT:COLUMN:NODE; REDUCEDSTATE MATERIAL ROLE, NOT LITHOLOGY",
            "surface_cells": "SUPPORT:SURFACE:PATCH00; SEPARATE FROM MATERIAL VOLUME IDS",
            "deep_volumes": deep_material_ids,
            "state_input_sha256": initial_digests,
            "run_identity_sha256": identity_sha,
            "surface_initial_state": initial_surface_snapshot,
            "initial_thermal_states": initial_payloads,
            "surface_topography": "SYNTHETIC_PRESCRIBED_RELIEF; GOVERNED T0 ELEVATION UNAVAILABLE",
        },
        "initial": {
            "time_s_by_support": {support: float(payload["time_s"]) for support, payload in initial_payloads.items()},
            "thermal_state_sha256_by_support": initial_digests,
            "deep_inventory_j": initial_deep,
            "deep_inventory_j_by_volume": dict(zip(deep_material_ids, config.deep_initial_inventory_j_by_support)),
            "water_storage_m3": initial_water,
            "mobile_cover_mass_kg": initial_cover_mass,
            "substrate_mass_kg": initial_substrate_mass,
            "suspended_sediment_kg": initial_suspended,
            "material_inventory_by_support": initial_material_inventory,
        },
        "steps": records,
        **({"history_output_coverage": {
            "mode": "EXTERNAL_CONSUMER", "step_ordinals": [row["step"] for row in records],
        }} if history_independent_continuation else {}),
        "final": {
            "time_s_by_support": {support: state.time_s for support, state in states.items()},
            "thermal_states": final_states,
            "thermal_state_sha256_by_support": {support: _state_digest(state) for support, state in states.items()},
            "surface_hydrology_cells": list(final_surface.values()),
            "deep_inventory_j": sum(deep_stocks),
            "deep_inventory_j_by_volume": dict(zip(deep_material_ids, deep_stocks)),
            "deep_zeta_by_volume": dict(zip(deep_material_ids, zeta)),
            "substrate_mass_kg": final_substrate_mass,
            "material_inventory_by_support": {
                support: {
                    "substrate": {"material_id": cell["substrate_material_id"],
                                  "mass_kg": cell["substrate_mass_kg"],
                                  "composition": cell["substrate_material_composition"],
                                  "provenance": cell["substrate_material_provenance"]},
                    "mobile_material_mass_kg_by_id": dict(cell["mobile_material_mass_kg_by_id"]),
                    "suspended_material_mass_kg_by_id": dict(cell["suspended_material_mass_kg_by_id"]),
                } for support, cell in final_surface.items()},
        },
        "integrated_balances": {
            "water": {**total_water, "initial_storage_m3": initial_water,
                      "final_storage_m3": final_water, "residual_m3": water_residual,
                      "roundoff_tolerance_m3": water_roundoff_tolerance,
                      "classification": "CLOSED_WITH_PRECIPITATION_ET_INFILTRATION_OUTLET_AND_STORAGE"},
            "sediment": {**total_sediment, "initial_mobile_cover_kg": initial_cover_mass,
                         "final_mobile_cover_kg": final_cover_mass,
                         "final_suspended_kg": final_suspended,
                         "bedrock_erosion_kg": total_substrate_erosion,
                         "initial_substrate_mass_kg": initial_substrate_mass,
                         "final_substrate_mass_kg": final_substrate_mass,
                         "substrate_residual_kg": substrate_residual,
                          "outlet_export_kg_by_material_id": exported_by_material,
                          "deposition_kg_by_material_id": deposited_by_material,
                          "internal_transfer_kg_by_material_id": internal_by_material,
                          "mobile_cover_erosion_kg_by_material_id": mobile_erosion_by_material,
                         "outlet_sediment_export_kg": total_sediment["outlet_sediment_export_kg"],
                         "residual_kg": sediment_residual,
                         "roundoff_tolerance_kg": sediment_roundoff_tolerance,
                         "bedrock_erosion_kg": total_substrate_erosion},
            "geometry": {"initial_surface_volume_m3": initial_surface_volume,
                         "final_surface_volume_m3": final_surface_volume,
                         "prescribed_uplift_volume_m3": prescribed_uplift_volume,
                         "sediment_export_volume_m3": sediment_export_volume,
                         "suspended_equivalent_volume_m3": final_suspension_volume,
                         "residual_m3": geometry_residual,
                         "roundoff_tolerance_m3": geometry_roundoff_tolerance},
            "deep": {"initial_inventory_j": initial_deep,
                     "final_inventory_j": sum(deep_stocks), "residual_j": deep_residual,
                      "gross_internal_transport_j": history_accumulators["deep"]["gross_internal_transport_j"],
                      "net_transport_0_to_1_j": history_accumulators["deep"]["net_transport_0_to_1_j"],
                      "minimum_reservoir_stock_j": history_accumulators["deep"]["minimum_reservoir_stock_j"],
                     "source_j": 0.0, "loss_j": 0.0,
                     "thermal_transfer_j": 0.0, "mechanical_work_transfer_j": 0.0},
            "mechanical": {
                "external_work_j": mechanical_work,
                "initial_stored_energy_j": 0.0,
                "final_stored_energy_j": mechanical_stored,
                "viscous_dissipation_j": mechanical_viscous,
                "algorithmic_energy_increment_j": mechanical_algorithmic,
                "residual_j": mechanical_energy_residual,
                "per_step_residuals_j": [r["mechanics"]["energy_balance_residual_j"] for r in records],
            },
        },
        "continuation": checkpoint_result,
        "authority_and_limits": [
            "R6 T0 states and B5 support geometry are source-bound; positive-time B5 kinematics are not inferred.",
            "Mechanical coefficients are evaluated from a dry-olivine literature benchmark on R6 T/rho/depth proxies; no R6 mineralogy calibration.",
            "Hydrology, channel geometry, rainfall, ET, infiltration, uplift, initial relief/cover, Deep stocks and modal parameters are synthetic.",
            "Manning runoff is a rectangular-channel approximation; sediment capacity is an uncalibrated empirical closure.",
            "Infiltration is an unresolved sink; no aquifer is modeled. Chemical weathering and lithification are absent; enabled bedrock detachment is a synthetic threshold law.",
            "Checkpoint SHA256 detects accidental corruption but is not an authenticated provenance signature.",
            "Deep inventory and accessibility are diagnostic synthetic reservoirs; Deep does not feed back into other domains.",
        ],
    }


def continue_unified_microdomain(
    checkpoint: Mapping[str, Any], source_identity: Mapping[str, Any], *,
    config: UnifiedConfig, segment_years: float,
    deep_mode: str = "ACTIVE_SYNTHETIC_TRANSPORT",
    precipitation_m_year_by_support: tuple[float, float] | None = None,
    uplift_scale: float = 1.0,
    history_independent_continuation: bool = False,
    history_consumer: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Continue a sealed noncanonical checkpoint under its original run identity."""
    state = verify_unified_checkpoint(checkpoint)
    if _canonical_sha(source_identity) != _canonical_sha(state["source_identity"]):
        raise SurfaceMicrodomainError("UNIFIED_CHECKPOINT_SOURCE_IDENTITY_MISMATCH")
    return run_unified_microdomain(
        unified_states_from_checkpoint(checkpoint), source_identity, config=config,
        deep_mode=deep_mode, precipitation_m_year_by_support=precipitation_m_year_by_support,
        uplift_scale=uplift_scale, checkpoint=checkpoint, segment_years=segment_years,
        history_independent_continuation=history_independent_continuation,
        history_consumer=history_consumer)


def run_experiment_matrix(
    states_by_support: Mapping[str, ReducedState], source_identity: Mapping[str, Any],
    *, config: UnifiedConfig = UnifiedConfig(),
) -> dict[str, Any]:
    """Run baseline, no-rain, altered-uplift, and passive-Deep contrasts."""
    return {
        "BASELINE": run_unified_microdomain(states_by_support, source_identity, config=config),
        "NO_PRECIPITATION": run_unified_microdomain(
            states_by_support, source_identity, config=config,
            precipitation_m_year_by_support=(0.0, 0.0)),
        "ALTERED_UPLIFT": run_unified_microdomain(
            states_by_support, source_identity, config=config, uplift_scale=2.0),
        "DEEP_PASSIVE": run_unified_microdomain(
            states_by_support, source_identity, config=config, deep_mode="PASSIVE"),
    }


def query_unified_result(result: Mapping[str, Any], *, case_id: str, elapsed_years: float,
                         support_id: str, domain: str,
                         material_id: str | None = None) -> dict[str, Any]:
    """Exact-time local reader; no interpolation or synthesized states."""
    if (support_id not in SUPPORTS or not math.isfinite(elapsed_years) or elapsed_years < 0
            or (material_id is not None and (not isinstance(material_id, str) or not material_id))):
        raise SurfaceMicrodomainError("UNIFIED_QUERY_COORDINATE_INVALID")
    if material_id is not None and domain != "MATERIAL":
        raise SurfaceMicrodomainError("UNIFIED_QUERY_MATERIAL_FILTER_REQUIRES_MATERIAL_DOMAIN")
    case = result.get("cases", {}).get(case_id)
    if not isinstance(case, Mapping):
        raise SurfaceMicrodomainError("UNIFIED_QUERY_CASE_UNKNOWN")
    if elapsed_years == 0.0:
        if domain == "THERMAL":
            value = case["initial"]["thermal_states"][support_id]
        elif domain == "SURFACE_HYDROLOGY":
            value = case["identity_semantics"]["surface_initial_state"][support_id]
        elif domain == "DEEP":
            volume_id = next(x for x in case["final"]["deep_inventory_j_by_volume"]
                             if x.startswith(support_id + ":"))
            value = {"volume_id": volume_id,
                     "inventory_j": case["initial"]["deep_inventory_j_by_volume"][volume_id]}
        elif domain == "MATERIAL":
            value = case["initial"]["material_inventory_by_support"][support_id]
            if material_id is not None:
                value = {
                    "substrate": (value["substrate"] if value["substrate"]["material_id"] == material_id
                                  else None),
                    "mobile_cover": (value["mobile_cover"]
                                     if value["mobile_cover"]["material_id"] == material_id else None),
                    "suspended": [row for row in value["suspended"]
                                  if row["material_id"] == material_id],
                }
        else:
            raise SurfaceMicrodomainError("UNIFIED_QUERY_DOMAIN_UNKNOWN")
        return {"case_id": case_id, "elapsed_years": 0.0,
                "support_id": support_id, "domain": domain, "value": value}
    matches = [step for step in case.get("steps", [])
               if math.isclose(float(step["elapsed_years"]), elapsed_years,
                               rel_tol=0.0, abs_tol=1e-12)]
    if len(matches) != 1:
        raise SurfaceMicrodomainError("UNIFIED_QUERY_TIME_NOT_EXACTLY_STORED")
    step = matches[0]
    if domain == "THERMAL":
        value = step["material_volumes"][support_id]
    elif domain == "MECHANICS":
        value = step["mechanics"]
    elif domain == "SURFACE_HYDROLOGY":
        value = next(row for row in step["surface_hydrology"]["surface_cells"]
                     if row["support_id"] == support_id)
    elif domain == "DEEP":
        volume_id = f"{support_id}:DEEP:RESERVOIR:00"
        value = {
            "volume_id": volume_id,
            "inventory_j": step["deep"]["inventory_j_by_material_volume"][volume_id],
            "zeta": step["deep"]["zeta_by_material_volume"][volume_id],
        }
    elif domain == "MATERIAL":
        surface_state = next(row for row in step["surface_hydrology"]["surface_cells"]
                             if row["support_id"] == support_id)
        flows = step["material_flows"]
        if material_id is not None:
            surface_state = dict(surface_state)
            surface_state["substrate"] = (
                {"material_id": surface_state["substrate_material_id"],
                 "mass_kg": surface_state["substrate_mass_kg"]}
                if surface_state["substrate_material_id"] == material_id else None)
            surface_state["mobile_material_mass_kg_by_id"] = {
                material_id: surface_state["mobile_material_mass_kg_by_id"][material_id]
            } if material_id in surface_state["mobile_material_mass_kg_by_id"] else {}
            surface_state["suspended_material_mass_kg_by_id"] = {
                material_id: surface_state["suspended_material_mass_kg_by_id"][material_id]
            } if material_id in surface_state["suspended_material_mass_kg_by_id"] else {}
            flows = {
                "time_start_s": flows["time_start_s"], "time_end_s": flows["time_end_s"],
                "erosion_type": flows["erosion_type"],
                "bedrock_detachment_kg_by_material_id": {
                    material_id: flows["bedrock_detachment_kg_by_material_id"][material_id]
                } if material_id in flows["bedrock_detachment_kg_by_material_id"] else {},
                "mobile_cover_erosion_kg_by_material_id": {
                    material_id: flows["mobile_cover_erosion_kg_by_material_id"][material_id]
                } if material_id in flows["mobile_cover_erosion_kg_by_material_id"] else {},
                "internal_transfer_kg_by_material_id": {
                    material_id: flows["internal_transfer_kg_by_material_id"][material_id]
                } if material_id in flows["internal_transfer_kg_by_material_id"] else {},
                "internal_transport_kg_by_route_and_material": {
                    key: amount for key, amount in flows["internal_transport_kg_by_route_and_material"].items()
                    if key.endswith("|" + material_id)},
                "deposition_kg_by_material_id": {
                    material_id: flows["deposition_kg_by_material_id"][material_id]
                } if material_id in flows["deposition_kg_by_material_id"] else {},
                "deposition_kg_by_surface_cell_and_material": {
                    cell_id: {material_id: value[material_id]}
                    for cell_id, value in flows["deposition_kg_by_surface_cell_and_material"].items()
                    if material_id in value},
                "outlet_export_kg_by_material_id": {
                    material_id: flows["outlet_export_kg_by_material_id"][material_id]
                } if material_id in flows["outlet_export_kg_by_material_id"] else {},
                "outlet_export_kg_by_surface_cell_and_material": {
                    cell_id: {material_id: value[material_id]}
                    for cell_id, value in flows["outlet_export_kg_by_surface_cell_and_material"].items()
                    if material_id in value},
                "chemical_weathering": flows["chemical_weathering"],
                "lithification": flows["lithification"],
            }
        value = {
            "surface_state": surface_state,
            "flows": flows,
        }
    else:
        raise SurfaceMicrodomainError("UNIFIED_QUERY_DOMAIN_UNKNOWN")
    return {"case_id": case_id, "elapsed_years": elapsed_years,
            "support_id": support_id, "domain": domain, "value": value}
