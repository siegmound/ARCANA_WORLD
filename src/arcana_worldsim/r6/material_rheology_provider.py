"""Documented rheology benchmark adapter for reduced R6 material columns.

This module evaluates a dry-olivine dislocation-creep benchmark, not a
constitutive law identified for the R6 crust/mantle role labels. R6 supplies
temperature, density and material coordinates; the benchmark supplies creep
parameters and elastic constants. Hydrostatic pressure is an explicitly
derived overburden proxy (rho*g*z), not a measured R6 pressure field.

The flow-law form and parameter conventions follow ASPECT's
DiffusionDislocation material model documentation:
https://aspect-documentation.readthedocs.io/en/latest/parameters/Material_20model.html
ASPECT documents the dry-olivine dislocation parameters A=1.1e-16 Pa^-n s^-1,
n=3.5, E=530 kJ/mol, V=14e-6 m^3/mol, following Hirth & Kohlstedt (2003).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping

from .functional_development import ReducedState

R_GAS_J_MOL_K = 8.31446261815324
GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True)
class DislocationCreepBenchmark:
    benchmark_id: str = "DRY_OLIVINE_DISLOCATION_HIRTH_KOHLSTEDT_2003_ASPECT_CONVENTION"
    prefactor_pa_n_s: float = 1.1e-16
    stress_exponent: float = 3.5
    activation_energy_j_mol: float = 530_000.0
    activation_volume_m3_mol: float = 14.0e-6
    shear_modulus_pa: float = 30.0e9
    poisson_ratio: float = 0.25
    provenance: str = "LITERATURE_BENCHMARK; NOT_ASSIGNED_TO_R6_MATERIAL_ROLES"


DEFAULT_BENCHMARK = DislocationCreepBenchmark()


def evaluate_dislocation_creep(
    *, temperature_k: float, strain_rate_s: float, pressure_pa: float,
    benchmark: DislocationCreepBenchmark = DEFAULT_BENCHMARK,
) -> dict[str, Any]:
    """Return benchmark shear viscosity and derived 1-D Maxwell properties.

    ASPECT-style effective viscosity:
      eta = 1/2 A^(-1/n) epsdot^((1-n)/n)
           exp((E + P*V)/(n*R*T))
    The mechanical microdomain evolves a uniaxial Young-modulus bar. To retain
    the same Maxwell time, eta_1d = E/G * eta_shear, giving tau=eta_shear/G.
    This mapping is an explicit reduced-model convention, not a tensor
    constitutive integration.
    """
    values = (temperature_k, strain_rate_s, pressure_pa,
              benchmark.prefactor_pa_n_s, benchmark.stress_exponent,
              benchmark.activation_energy_j_mol, benchmark.activation_volume_m3_mol,
              benchmark.shear_modulus_pa, benchmark.poisson_ratio)
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("RHEOLOGY_INPUT_NONFINITE")
    if (temperature_k <= 0 or strain_rate_s <= 0 or pressure_pa < 0
            or benchmark.prefactor_pa_n_s <= 0 or benchmark.stress_exponent <= 0
            or benchmark.activation_energy_j_mol < 0 or benchmark.activation_volume_m3_mol < 0
            or benchmark.shear_modulus_pa <= 0 or not -1.0 < benchmark.poisson_ratio < 0.5):
        raise ValueError("RHEOLOGY_INPUT_OUT_OF_DOMAIN")
    n = benchmark.stress_exponent
    log_eta = (math.log(0.5) - math.log(benchmark.prefactor_pa_n_s) / n
               + ((1.0 - n) / n) * math.log(strain_rate_s)
               + (benchmark.activation_energy_j_mol
                  + pressure_pa * benchmark.activation_volume_m3_mol)
               / (n * R_GAS_J_MOL_K * temperature_k))
    if log_eta > math.log(float.fromhex("0x1.fffffffffffffp+1023")):
        raise ValueError("RHEOLOGY_VISCOSITY_OVERFLOW")
    eta_shear = math.exp(log_eta)
    shear = benchmark.shear_modulus_pa
    young = 2.0 * shear * (1.0 + benchmark.poisson_ratio)
    eta_1d = eta_shear * young / shear
    tau = eta_shear / shear
    if any(not math.isfinite(value) or value <= 0 for value in (eta_shear, young, eta_1d, tau)):
        raise ValueError("RHEOLOGY_OUTPUT_INVALID")
    return {
        "temperature_k": float(temperature_k), "pressure_pa": float(pressure_pa),
        "strain_rate_s": float(strain_rate_s), "young_modulus_pa": young,
        "shear_modulus_pa": shear, "effective_shear_viscosity_pa_s": eta_shear,
        "equivalent_1d_maxwell_viscosity_pa_s": eta_1d,
        "maxwell_relaxation_time_s": tau,
        "maxwell_relaxation_time_years": tau / (365.25 * 24.0 * 3600.0),
        "pressure_authority": "EXPLICIT_PRESSURE_INPUT_TO_BENCHMARK_LAW",
        "benchmark": asdict(benchmark),
    }


def evaluate_reduced_state_column(
    state: ReducedState, cells: list[Mapping[str, Any]], *, support_id: str,
    strain_rate_s: float, temperature_offset_k: float = 0.0,
    benchmark: DislocationCreepBenchmark = DEFAULT_BENCHMARK,
) -> dict[str, Any]:
    """Bind R6 per-node T/rho/z to the explicit benchmark; no role→mineral mapping."""
    if not math.isfinite(temperature_offset_k):
        raise ValueError("RHEOLOGY_TEMPERATURE_OFFSET_INVALID")
    if len(cells) != len(state.materials) or len(cells) != len(state.temperature_k):
        raise ValueError("RHEOLOGY_COLUMN_CARDINALITY_MISMATCH")
    nodes: list[dict[str, Any]] = []
    young_by_cell: dict[str, float] = {}
    eta_1d_by_cell: dict[str, float] = {}
    for index, (cell, material, temperature, xi) in enumerate(zip(
            cells, state.materials, state.temperature_k, state.material_coordinate)):
        if (cell.get("support_id") != support_id or cell.get("node_index_zero_based") != index
                or cell.get("material_role_id") != material.role_id):
            raise ValueError("RHEOLOGY_CELL_TO_R6_MATERIAL_BINDING_MISMATCH")
        depth = float(xi) * state.lithosphere_m
        pressure = float(material.rho_kg_m3) * GRAVITY_M_S2 * depth
        result = evaluate_dislocation_creep(
            temperature_k=float(temperature) + temperature_offset_k,
            strain_rate_s=strain_rate_s, pressure_pa=pressure, benchmark=benchmark)
        cell_id = str(cell["cell_id"])
        young_by_cell[cell_id] = result["young_modulus_pa"]
        eta_1d_by_cell[cell_id] = result["equivalent_1d_maxwell_viscosity_pa_s"]
        nodes.append({"cell_id": cell_id, "support_id": support_id,
            "node_index_zero_based": index, "material_role_id": material.role_id,
            "r6_density_kg_m3": float(material.rho_kg_m3),
            "r6_temperature_k": float(temperature),
            "constitutive_temperature_k": result["temperature_k"],
            "material_coordinate_xi": float(xi), "depth_proxy_m": depth,
            "pressure_proxy_pa": pressure, **result})
    return {
        "schema": "ARCANA_R6_MATERIAL_RHEOLOGY_BENCHMARK_ADAPTER_V1",
        "scope": "NONCANONICAL_BENCHMARK_EVALUATION_ON_R6_NODE_T_RHO_COORDINATES",
        "support_id": support_id, "node_count": len(nodes),
        "temperature_offset_k": temperature_offset_k,
        "strain_rate_s": strain_rate_s,
        "material_role_to_mineralogy": "UNKNOWN; NO MINERALOGY IN REDUCEDSTATE",
        "pressure_method": "rho_kg_m3 * 9.80665_m_s2 * material_coordinate_xi * lithosphere_m",
        "young_modulus_method": "E=2*G*(1+nu); benchmark G and nu, not R6-measured",
        "viscosity_method": "ASPECT_STYLE_DRY_OLIVINE_DISLOCATION_CREEP; benchmark only",
        "nodes": nodes, "young_modulus_pa_by_cell": young_by_cell,
        "eta_1d_pa_s_by_cell": eta_1d_by_cell,
    }
