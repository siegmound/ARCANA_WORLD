"""Small noncanonical surface-process experiment bound to archived R6 columns.

The subsurface role/thermal profiles are read from a hash-checked prior R6
microdomain result. Surface relief and mobile cover are explicit synthetic
inputs because the governed T0 surface payload is not locally available.
The only surface process is a conservative linear hillslope-diffusion flux;
it is an engineering candidate, not an ARCANA production erosion law.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


SUPPORTS = ("R6G1D-R091-C028", "R6G1D-R091-C029")
RESULT_FILENAME = "RESULT.json"
MANIFEST_FILENAME = "MANIFEST.json"
SIDECAR_FILENAME = "RESULT.json.sha256"


class SurfaceMicrodomainError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_verified_r6_initial_columns(result_dir: str | Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Read the prior pilot's actual T0 ReducedState payloads with hash checks."""
    root = Path(result_dir)
    result_path = root / RESULT_FILENAME
    manifest_path = root / MANIFEST_FILENAME
    sidecar_path = root / SIDECAR_FILENAME
    if not all(path.is_file() for path in (result_path, manifest_path, sidecar_path)):
        raise SurfaceMicrodomainError("SOURCE_RESULT_MANIFEST_OR_SIDECAR_MISSING")
    result_bytes = result_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    sidecar_bytes = sidecar_path.read_bytes()
    try:
        manifest = json.loads(manifest_bytes)
        result = json.loads(result_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SurfaceMicrodomainError("SOURCE_RESULT_JSON_INVALID") from exc
    if manifest.get("schema") != "ARCANA_CONSTITUTIVE_MECHANICS_MANIFEST_V1":
        raise SurfaceMicrodomainError("SOURCE_RESULT_MANIFEST_SCHEMA_MISMATCH")
    result_record = manifest.get("result", {})
    sidecar_record = manifest.get("sidecar", {})
    if (result_record.get("path") != RESULT_FILENAME
            or result_record.get("size_bytes") != len(result_bytes)
            or result_record.get("sha256") != _sha256(result_bytes)):
        raise SurfaceMicrodomainError("SOURCE_RESULT_MANIFEST_HASH_MISMATCH")
    if (sidecar_record.get("path") != SIDECAR_FILENAME
            or sidecar_record.get("size_bytes") != len(sidecar_bytes)
            or sidecar_record.get("sha256") != _sha256(sidecar_bytes)):
        raise SurfaceMicrodomainError("SOURCE_RESULT_SIDECAR_MANIFEST_MISMATCH")
    expected_sidecar = f"{_sha256(result_bytes)}  {RESULT_FILENAME}\n".encode("ascii")
    if sidecar_bytes != expected_sidecar:
        raise SurfaceMicrodomainError("SOURCE_RESULT_SIDECAR_CONTENT_MISMATCH")

    cases = result.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SurfaceMicrodomainError("SOURCE_RESULT_CASES_MISSING")
    initial: dict[str, dict[str, Any]] | None = None
    initial_hashes: dict[str, str] | None = None
    for case in cases:
        if case.get("case_id") == "UNCoupled_reference":
            initial = case.get("state_initial")
            initial_hashes = case.get("state_initial_sha256")
            break
    if not isinstance(initial, dict) or not isinstance(initial_hashes, dict):
        raise SurfaceMicrodomainError("SOURCE_R6_INITIAL_STATE_MISSING")
    states: dict[str, dict[str, Any]] = {}
    for support in SUPPORTS:
        payload = initial.get(support)
        if not isinstance(payload, dict) or not isinstance(initial_hashes.get(support), str):
            raise SurfaceMicrodomainError(f"SOURCE_R6_SUPPORT_MISSING:{support}")
        digest = _sha256(_canonical_bytes(payload))
        if digest != initial_hashes[support]:
            raise SurfaceMicrodomainError(f"SOURCE_R6_STATE_IDENTITY_MISMATCH:{support}")
        n = len(payload.get("temperature_k", []))
        if (payload.get("time_s") != 0.0 or n != 73
                or len(payload.get("materials", [])) != n
                or len(payload.get("z_m", [])) != n):
            raise SurfaceMicrodomainError(f"SOURCE_R6_T0_COLUMN_INVALID:{support}")
        for idx, (temp, z, material) in enumerate(zip(
                payload["temperature_k"], payload["z_m"], payload["materials"])):
            if (not math.isfinite(float(temp)) or not math.isfinite(float(z))
                    or not isinstance(material, dict)
                    or not material.get("role_id")
                    or not math.isfinite(float(material.get("rho_kg_m3", math.nan)))):
                raise SurfaceMicrodomainError(f"SOURCE_R6_NODE_INVALID:{support}:{idx}")
        states[support] = payload
    boundary_binding = result.get("t0_boundary_binding", {})
    support_cells = boundary_binding.get("support_cells", [])
    support_map = {row.get("support_id"): row.get("grid_cell")
                   for row in support_cells if isinstance(row, dict)}
    expected_map = {SUPPORTS[0]: [91, 28], SUPPORTS[1]: [91, 29]}
    boundary = boundary_binding.get("boundary", {})
    if (support_map != expected_map or boundary.get("boundary_kind") != "GEOMETRIC_SHARED_INTERFACE"
            or boundary.get("ordered_plate_pair") != [5, 11]
            or not isinstance(boundary.get("boundary_id"), str)):
        raise SurfaceMicrodomainError("SOURCE_T0_SURFACE_SUPPORT_BINDING_INVALID")
    boundary_length = float(boundary.get("length_m", math.nan))
    if not math.isfinite(boundary_length) or boundary_length <= 0:
        raise SurfaceMicrodomainError("SOURCE_T0_BOUNDARY_LENGTH_INVALID")
    identity = {
        "source_result_sha256": _sha256(result_bytes),
        "source_manifest_sha256": _sha256(manifest_bytes),
        "source_manifest_schema": manifest["schema"],
        "source_result_scope": result.get("scope"),
        "source_archive_sha256": boundary_binding.get("archive_sha256"),
        "source_branch": boundary_binding.get("source_branch"),
        "source_head": boundary_binding.get("source_head"),
        "source_identity_sha256": boundary_binding.get("source_identity_sha256"),
        "vector_partition_payload_sha256": boundary_binding.get("vector_partition_payload_sha256"),
        "t0_boundary_id": boundary["boundary_id"],
        "t0_boundary_length_m": boundary_length,
        "support_cells": support_cells,
        "support_state_sha256": dict(initial_hashes),
    }
    return states, identity


@dataclass(frozen=True)
class SurfaceConfig:
    duration_years: float = 3.0
    dt_years: float = 1.0
    initial_cover_m: tuple[float, float] = (5.0, 5.0)
    initial_relief_m: tuple[float, float] = (20.0, 0.0)
    prescribed_uplift_m: tuple[float, float] = (0.25, 0.0)
    sediment_density_kg_m3: float = 1800.0
    linear_diffusivity_m2_year: float = 1.0e6
    enable_surface_transport: bool = True

    def validate(self) -> None:
        scalars = (self.duration_years, self.dt_years,
                   self.sediment_density_kg_m3, self.linear_diffusivity_m2_year)
        if any(not math.isfinite(v) for v in scalars):
            raise SurfaceMicrodomainError("CONFIG_NONFINITE")
        if self.duration_years <= 0 or self.dt_years <= 0:
            raise SurfaceMicrodomainError("CONFIG_NONPOSITIVE_TIME_OR_LENGTH")
        if (self.sediment_density_kg_m3 <= 0 or self.linear_diffusivity_m2_year < 0
                or not math.isclose(self.duration_years / self.dt_years,
                                    round(self.duration_years / self.dt_years), abs_tol=1e-12)):
            raise SurfaceMicrodomainError("CONFIG_INVALID_RATE_OR_NONINTEGRAL_STEP_COUNT")
        for pair in (self.initial_cover_m, self.initial_relief_m, self.prescribed_uplift_m):
            if len(pair) != 2:
                raise SurfaceMicrodomainError("CONFIG_PAIR_INVALID")
            if any(not math.isfinite(float(v)) for v in pair):
                raise SurfaceMicrodomainError("CONFIG_PAIR_NONFINITE")
        if any(v < 0 for v in self.initial_cover_m):
            raise SurfaceMicrodomainError("INITIAL_COVER_NEGATIVE")


def _surface_grid_geometry(source_identity: Mapping[str, Any]) -> tuple[dict[str, tuple[int, int, float]], float, float]:
    """Derive areas, center distance, and shared edge length from the R6 1-degree grid."""
    supports = source_identity.get("support_cells", [])
    by_id = {row.get("support_id"): row.get("grid_cell") for row in supports if isinstance(row, dict)}
    if by_id != {SUPPORTS[0]: [91, 28], SUPPORTS[1]: [91, 29]}:
        raise SurfaceMicrodomainError("SURFACE_GRID_SUPPORTS_NOT_ADJACENT_EAST_WEST")
    radius = 6_371_000.0
    dlat = math.radians(1.0)
    dlon = math.radians(1.0)
    row = 91
    south = math.radians(-90.0 + row)
    north = math.radians(-90.0 + row + 1)
    center_lat = 0.5 * (south + north)
    areas: dict[str, tuple[int, int, float]] = {}
    for support in SUPPORTS:
        r, c = by_id[support]
        area = radius * radius * dlon * (math.sin(north) - math.sin(south))
        areas[support] = (r, c, area)
    delta_lon = math.radians(1.0)
    cos_angle = math.sin(center_lat) ** 2 + math.cos(center_lat) ** 2 * math.cos(delta_lon)
    center_distance = radius * math.acos(max(-1.0, min(1.0, cos_angle)))
    edge_length = radius * dlat
    declared_edge_length = float(source_identity.get("t0_boundary_length_m", math.nan))
    if not math.isclose(edge_length, declared_edge_length, rel_tol=1e-12, abs_tol=1e-6):
        raise SurfaceMicrodomainError("T0_SHARED_EDGE_GEOMETRY_MISMATCH")
    return areas, center_distance, edge_length


def run_surface_microdomain(
    states_by_support: Mapping[str, Mapping[str, Any]],
    source_identity: Mapping[str, Any],
    *,
    config: SurfaceConfig = SurfaceConfig(),
    interface_distance_m: float | None = None,
    deep_inventory_j_by_support: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Run a few conservative surface-cover diffusion steps on two R6 columns."""
    config.validate()
    if set(states_by_support) != set(SUPPORTS):
        raise SurfaceMicrodomainError("SURFACE_SUPPORT_SET_MISMATCH")
    surface_geometry, derived_center_distance, shared_edge_length = _surface_grid_geometry(source_identity)
    if interface_distance_m is None:
        interface_distance_m = derived_center_distance
    if not math.isfinite(interface_distance_m) or interface_distance_m <= 0:
        raise SurfaceMicrodomainError("SURFACE_INTERFACE_DISTANCE_INVALID")
    if not math.isclose(interface_distance_m, derived_center_distance, rel_tol=1e-12, abs_tol=1e-6):
        raise SurfaceMicrodomainError("SURFACE_CENTER_DISTANCE_NOT_BOUND_TO_GRID")
    cells: list[dict[str, Any]] = []
    for i, support in enumerate(SUPPORTS):
        state = states_by_support[support]
        materials = state["materials"]
        row, column, area = surface_geometry[support]
        top = materials[0]
        cells.append({
            "surface_cell_id": f"{support}:SURFACE:PATCH00",
            "support_id": support,
            "grid_row_col": [row, column],
            "grid_identity_status": "SOURCE_BOUND_R6_1DEGREE_SUPPORT_CELL; T0_ELEVATION_PAYLOAD_UNAVAILABLE",
            "subsurface_node_id": f"{support}:COLUMN:NODE000",
            "subsurface_role_id": top["role_id"],
            "subsurface_temperature_k": float(state["temperature_k"][0]),
            "subsurface_coordinate_z_m": float(state["z_m"][0]),
            "surface_area_m2": area,
            "bedrock_elevation_m": float(config.initial_relief_m[i]),
            "prescribed_uplift_m": float(config.prescribed_uplift_m[i]),
            # Initial topography includes the synthetic mobile-cover thickness.
            "surface_elevation_m": float(config.initial_relief_m[i] + config.initial_cover_m[i]),
            "cover_thickness_m": float(config.initial_cover_m[i]),
            "cover_mass_kg": float(config.initial_cover_m[i]) * area * config.sediment_density_kg_m3,
            "cover_material_class": "SYNTHETIC_MOBILE_REGOLITH; NOT A LITHOLOGY ASSIGNMENT",
            "cover_density_kg_m3": config.sediment_density_kg_m3,
        })
    initial_cover_mass = sum(cell["cover_mass_kg"] for cell in cells)
    initial_surface_volume = sum(cell["surface_elevation_m"] * cell["surface_area_m2"]
                                 for cell in cells)
    steps: list[dict[str, Any]] = []
    nsteps = round(config.duration_years / config.dt_years)
    for step_index in range(nsteps):
        # Prescribed displacement is a geometric boundary condition, not
        # inferred from the horizontal pure-shear kernel.
        if step_index == 0:
            for cell in cells:
                cell["bedrock_elevation_m"] += cell["prescribed_uplift_m"]
                cell["surface_elevation_m"] += cell["prescribed_uplift_m"]
        transfer_m3 = 0.0
        signed_slope = (cells[0]["surface_elevation_m"] - cells[1]["surface_elevation_m"]) / interface_distance_m
        if config.enable_surface_transport and signed_slope != 0.0:
            donor_index = 0 if signed_slope > 0 else 1
            receiver_index = 1 - donor_index
            donor, receiver = cells[donor_index], cells[receiver_index]
            area_d, area_r = donor["surface_area_m2"], receiver["surface_area_m2"]
            height_diff = donor["surface_elevation_m"] - receiver["surface_elevation_m"]
            requested = (config.linear_diffusivity_m2_year
                         * abs(signed_slope) * shared_edge_length * config.dt_years)
            # Explicit-step stability: no more than half the volume needed to
            # equalize the two cell surface heights in one step.
            equilibrium_volume = height_diff / (1.0 / area_d + 1.0 / area_r)
            available_volume = donor["cover_mass_kg"] / config.sediment_density_kg_m3
            transfer_m3 = min(requested, 0.5 * equilibrium_volume, available_volume)
            mass = transfer_m3 * config.sediment_density_kg_m3
            donor["cover_mass_kg"] -= mass
            receiver["cover_mass_kg"] += mass
            donor["cover_thickness_m"] = donor["cover_mass_kg"] / (
                config.sediment_density_kg_m3 * area_d)
            receiver["cover_thickness_m"] = receiver["cover_mass_kg"] / (
                config.sediment_density_kg_m3 * area_r)
            donor["surface_elevation_m"] -= transfer_m3 / area_d
            receiver["surface_elevation_m"] += transfer_m3 / area_r
        else:
            donor_index = receiver_index = None
        mass_end = sum(cell["cover_mass_kg"] for cell in cells)
        steps.append({
            "step": step_index + 1,
            "time_years": (step_index + 1) * config.dt_years,
            "prescribed_uplift_applied_m_by_support": (
                {support: float(config.prescribed_uplift_m[i]) if step_index == 0 else 0.0
                 for i, support in enumerate(SUPPORTS)}),
            "surface_transport": {
                "law": "SYNTHETIC_LINEAR_HILLSLOPE_DIFFUSION_Q_EQUALS_MINUS_K_GRADIENT",
                "enabled": config.enable_surface_transport,
                "signed_pretransport_slope": signed_slope,
                "donor_support": SUPPORTS[donor_index] if donor_index is not None else None,
                "receiver_support": SUPPORTS[receiver_index] if receiver_index is not None else None,
            "transferred_volume_m3": transfer_m3,
                "internal_mass_transfer_kg": transfer_m3 * config.sediment_density_kg_m3,
                "external_boundary_mass_flux_kg": 0.0,
            },
            "cover_mass_total_kg": mass_end,
            "mass_balance_residual_kg": mass_end - initial_cover_mass,
        })
    final_cover_mass = sum(cell["cover_mass_kg"] for cell in cells)
    final_surface_volume = sum(cell["surface_elevation_m"] * cell["surface_area_m2"]
                               for cell in cells)
    uplift_volume = sum(cell["prescribed_uplift_m"] * cell["surface_area_m2"]
                        for cell in cells)
    moved_volume_net = sum((cell["surface_elevation_m"] - cell["bedrock_elevation_m"]
                            - config.initial_cover_m[i]) * cell["surface_area_m2"]
                           for i, cell in enumerate(cells))
    if not math.isclose(final_cover_mass, initial_cover_mass, rel_tol=1e-13, abs_tol=1e-7):
        raise SurfaceMicrodomainError("SURFACE_MASS_NOT_CONSERVED")
    if any(cell["cover_mass_kg"] < 0 or cell["cover_thickness_m"] < 0 for cell in cells):
        raise SurfaceMicrodomainError("SURFACE_COVER_NEGATIVE")
    if not math.isclose(final_surface_volume - initial_surface_volume,
                        uplift_volume, rel_tol=1e-12, abs_tol=1e-6):
        raise SurfaceMicrodomainError("SURFACE_GEOMETRY_VOLUME_BALANCE_FAILED")

    deep_before = dict(deep_inventory_j_by_support or {})
    if deep_before and set(deep_before) != set(SUPPORTS):
        raise SurfaceMicrodomainError("DEEP_INVENTORY_SUPPORT_MISMATCH")
    if any(not math.isfinite(float(value)) or float(value) < 0 for value in deep_before.values()):
        raise SurfaceMicrodomainError("DEEP_INVENTORY_INVALID")
    return {
        "schema": "ARCANA_R6_GEOLOGICAL_SURFACE_MICRODOMAIN_V1",
        "scope": "NONCANONICAL_TWO_SUPPORT_SURFACE_PROCESS_EXPERIMENT",
        "source_identity": dict(source_identity),
        "input_authority": {
            "subsurface_profiles": "HASH_VERIFIED_PREVIOUS_R6_MICRODOMAIN_T0_REDUCED_STATES",
            "surface_elevation": "SYNTHETIC_PRESCRIBED_RELIEF; GOVERNED T0 SURFACE PAYLOAD UNAVAILABLE",
            "mobile_cover": "SYNTHETIC_REGOLITH_INITIAL_MASS",
            "uplift": "SYNTHETIC_PRESCRIBED_GEOMETRIC_BOUNDARY_VARIATION",
            "transport_coefficient": "SYNTHETIC_UNCALIBRATED_ENGINEERING_PARAMETER",
            "deep_coupling": "NONE; DEEP IS READ_ONLY AND UNCHANGED",
        },
        "configuration": {
            "duration_years": config.duration_years,
            "dt_years": config.dt_years,
            "initial_cover_m": list(config.initial_cover_m),
            "initial_relief_m": list(config.initial_relief_m),
            "prescribed_uplift_m": list(config.prescribed_uplift_m),
            "sediment_density_kg_m3": config.sediment_density_kg_m3,
            "linear_diffusivity_m2_year": config.linear_diffusivity_m2_year,
            "transport_enabled": config.enable_surface_transport,
            "cell_center_distance_m": interface_distance_m,
            "shared_edge_length_m": shared_edge_length,
            "cell_area_source": "R6_GLOBAL_GEOGRAPHY_1DEG_V1_SPHERICAL_CELL_AREA_FORMULA",
            "surface_elevation_source": "SYNTHETIC_NOT_T0_TOPOGRAPHY",
            "rheology_or_thermal_kernel_modified": False,
        },
        "grid": {
            "dimension": "2D_SURFACE_GRID; TWO_SOURCE_BOUND_ADJACENT_R6_1DEGREE_CELLS",
            "interface_id": source_identity["t0_boundary_id"],
            "interface_is_mechanically_qualified": False,
            "supports": list(SUPPORTS),
        },
        "initial_surface_volume_m3": initial_surface_volume,
        "final_surface_volume_m3": final_surface_volume,
        "prescribed_uplift_volume_m3": uplift_volume,
        "net_internal_cover_volume_change_m3": moved_volume_net,
        "initial_cover_mass_kg": initial_cover_mass,
        "final_cover_mass_kg": final_cover_mass,
        "mass_balance_residual_kg": final_cover_mass - initial_cover_mass,
        "boundary_mass_flux_kg": 0.0,
        "deep_inventory_before_j_by_support": deep_before,
        "deep_inventory_after_j_by_support": dict(deep_before),
        "deep_inventory_change_j": 0.0,
        "cells": cells,
        "steps": steps,
        "limits": [
            "No claim that synthetic relief represents T0 topography.",
            "No erosion from bedrock; conservative mobile-cover redistribution only.",
            "No mechanical continuity inferred from plate adjacency.",
            "No thermal/deep energy conversion or hydrology coupling.",
        ],
    }


def write_result(result: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Write a fresh result bundle; collision or partial output fails closed."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    result_bytes = _canonical_bytes(result)
    result_path = output / RESULT_FILENAME
    sidecar_path = output / SIDECAR_FILENAME
    manifest_path = output / MANIFEST_FILENAME
    result_path.write_bytes(result_bytes)
    sidecar = f"{_sha256(result_bytes)}  {RESULT_FILENAME}\n".encode("ascii")
    sidecar_path.write_bytes(sidecar)
    manifest = {
        "schema": "ARCANA_GEOLOGICAL_SURFACE_MICRODOMAIN_MANIFEST_V1",
        "manifest_self_hash": None,
        "result": {"path": RESULT_FILENAME, "size_bytes": len(result_bytes), "sha256": _sha256(result_bytes)},
        "sidecar": {"path": SIDECAR_FILENAME, "size_bytes": len(sidecar), "sha256": _sha256(sidecar)},
    }
    manifest_path.write_bytes(_canonical_bytes(manifest))
    return manifest
