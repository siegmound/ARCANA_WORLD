"""Noncanonical engineering T0/profile and pure-shear thermal development.

This module deliberately does not call the B6N8-Q execution adapter and does
not alter any qualified initializer, kinematics, or WORLD_HISTORY interface.
It binds one already-admitted native column, calls the shared column equation,
and provides a separate material-coordinate finite-volume development kernel.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .pre_orbdata_heat_flow import HWR2
from .pre_orbdata_t0_initializer import (
    INITIALIZER_FAMILY,
    REQUIRED_UNITS,
    T0_WORLD_AGE_MA,
    ColumnBinding,
    LayerPropertyBinding,
    build_initializer_plan,
    continental_column,
    preflight_admitted_bindings,
    role_binding_from_registry,
    _cell_id,
    _hwr_from_authority,
)
from .repository_context import canonical_text_sha256

ENGINEERING_SCENARIO = "REFERENCE_ENGINEERING_SCENARIO"
SECONDS_PER_YEAR = 31_557_600.0
T1_PRE_EVENT_MA = 209.97287659484368
T0_TO_T1_SECONDS = (210.0 - T1_PRE_EVENT_MA) * 1_000_000.0 * SECONDS_PER_YEAR


@dataclass(frozen=True)
class NodeMaterial:
    role_id: str
    k_w_m_k: float
    rho_kg_m3: float
    cp_j_kg_k: float
    radiogenic_w_m3: float


@dataclass(frozen=True)
class T0Profile:
    support_id: str
    support_class: str
    scenario_id: str
    crust_m: float
    model_base_m: float
    surface_temperature_k: float
    base_temperature_k: float
    surface_heat_flow_w_m2: float
    z_m: tuple[float, ...]
    temperature_k: tuple[float, ...]
    materials: tuple[NodeMaterial, ...]
    material_roles: tuple[str, str]
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class ReducedState:
    time_s: float
    initial_width_m: float
    width_m: float
    initial_crust_m: float
    initial_lithosphere_m: float
    crust_m: float
    lithosphere_m: float
    beta: float
    accumulated_strain: float
    crust_fraction: float
    material_coordinate: tuple[float, ...]
    temperature_k: tuple[float, ...]
    materials: tuple[NodeMaterial, ...]
    surface_temperature_k: float
    base_temperature_k: float

    def payload(self) -> dict[str, Any]:
        return {
            "schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_REDUCED_STATE_V1",
            "scope": ["NON_CANONICAL", "ENGINEERING_REFERENCE", "MODEL_DEPENDENT", "NOT_RECONSTRUCTED_HISTORY"],
            "time_s": self.time_s,
            "initial_width_m": self.initial_width_m,
            "width_m": self.width_m,
            "initial_crust_m": self.initial_crust_m,
            "initial_lithosphere_m": self.initial_lithosphere_m,
            "crust_m": self.crust_m,
            "lithosphere_m": self.lithosphere_m,
            "beta": self.beta,
            "accumulated_strain": self.accumulated_strain,
            "area_m2": self.width_m * self.lithosphere_m,
            "crust_fraction": self.crust_fraction,
            "material_coordinate": list(self.material_coordinate),
            "z_m": [x * self.lithosphere_m for x in self.material_coordinate],
            "temperature_k": list(self.temperature_k),
            "materials": [asdict(x) for x in self.materials],
            "surface_temperature_k": self.surface_temperature_k,
            "base_temperature_k": self.base_temperature_k,
        }


@dataclass(frozen=True)
class StepDiagnostics:
    duration_s: float
    substeps: int
    min_stability_limit_s: float
    max_stability_ratio: float
    area_before_m2: float
    area_after_m2: float
    area_relative_error: float
    min_temperature_k: float
    max_temperature_k: float


@dataclass(frozen=True)
class ThermalEvolutionDiagnostics:
    duration_s: float
    substeps: int
    min_stability_limit_s: float
    max_stability_ratio: float
    temperature_change_linf_k: float


def materialize_admitted_continental_t0(
    repository_root: str | Path,
    support_id: str | None = None,
    *,
    crust_intervals: int = 24,
    mantle_intervals: int = 48,
) -> tuple[T0Profile, dict[str, Any]]:
    """Evaluate one exact continental support from B6N8-N bindings.

    This is a development-only path. It verifies the qualified N binding
    authority and native package, but does not invoke or modify B6N8-Q.
    """
    root = Path(repository_root).resolve()
    if crust_intervals < 2 or mantle_intervals < 2:
        raise ValueError("PROFILE_RESOLUTION_TOO_LOW")
    index = _read_json(root / "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json")
    registry = _read_json(root / "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json")
    attestation = _read_json(root / "docs/arcana/qualifications/R6_B6N8N_ATTESTATION.json")
    if (attestation.get("qualification_status") != "PASS"
            or attestation.get("verdict") != "PASS_B6N8N_ADMITTED_SUPPORT_BINDINGS_CLOSED_READY_FOR_T0_INITIALIZER_IMPLEMENTATION"):
        raise ValueError("B6N8N_BINDING_AUTHORITY_NOT_QUALIFIED")
    for authority in index["authorities"]:
        path = root / authority["path"]
        if canonical_text_sha256(path) != authority["canonical_text_sha256"]:
            raise ValueError(f"B6N8N_AUTHORITY_HASH_MISMATCH:{authority['path']}")
    package_path = (root / index["field_package"]["path"]).resolve()
    if root not in package_path.parents or _sha256(package_path) != index["field_package"]["sha256"]:
        raise ValueError("B6N8N_FIELD_PACKAGE_IDENTITY_MISMATCH")
    preflight = preflight_admitted_bindings(root)
    if preflight.admitted_count != 63_620 or preflight.production_execution_authorized:
        raise ValueError("B6N8N_ADMITTED_SUPPORT_PREFLIGHT_MISMATCH")

    with np.load(package_path, allow_pickle=False) as arrays:
        domain = arrays["physical_crust_domain_id"]
        thermal = arrays["continental_thermal_domain_id"]
        if support_id is None:
            matches = np.argwhere(
                np.isin(domain, (2, 3, 4, 5, 6)) & np.isin(thermal, (1, 2, 3))
            )
            if not len(matches):
                raise ValueError("NO_ADMITTED_CONTINENTAL_SUPPORT")
            row, column = map(int, matches[0])
            support_id = _cell_id(row, column)
        match = __import__("re").fullmatch(r"R6G1D-R([0-9]{3})-C([0-9]{3})", support_id)
        if not match:
            raise ValueError("NATIVE_SUPPORT_ID_REQUIRED")
        row, column = map(int, match.groups())
        if not (0 <= row < domain.shape[0] and 0 <= column < domain.shape[1]):
            raise ValueError("SUPPORT_ID_OUTSIDE_NATIVE_GRID")
        domain_id, thermal_id = int(domain[row, column]), int(thermal[row, column])
        class_by_id = {1: "CONTINENTAL_COLD_STABLE", 2: "CONTINENTAL_NORMAL", 3: "CONTINENTAL_HOT_EXTENDED"}
        if domain_id not in (2, 3, 4, 5, 6) or thermal_id not in class_by_id:
            raise ValueError("SUPPORT_NOT_ADMITTED_CONTINENTAL_BINDING")
        support_class = class_by_id[thermal_id]
        crust_m = float(arrays["crustal_thickness_m"][row, column])
        base_m = float(arrays["continental_reference_lithosphere_thickness_m"][row, column])
        q_surface = float(arrays["continental_reference_surface_heat_flow_w_m2"][row, column])

    heat_config_path = root / "R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json"
    material_config_path = root / "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json"
    heat_config = _read_json(heat_config_path)
    material_config = _read_json(material_config_path)
    hwr = _hwr_from_authority(heat_config)
    crust_binding = role_binding_from_registry(registry, "CONTINENTAL_CRUST_REFERENCE")
    mantle_binding = role_binding_from_registry(registry, "LITHOSPHERIC_MANTLE_REFERENCE")
    binding = ColumnBinding(
        support_id=support_id, support_class=support_class,
        geometry_reference="CONTINENTAL_AUTHORED_REFERENCE_GEOMETRY",
        surface_datum="LOCAL_MODEL_SURFACE_Z0", crust_depth_m=crust_m,
        model_base_depth_m=base_m,
        model_base_semantics="AUTHORED_TOTAL_THERMAL_THICKNESS_NOT_PHYSICAL_LAB",
        physical_lab_depth_m=None,
        material_role_sequence=(crust_binding.role_id, mantle_binding.role_id),
        crust=crust_binding, mantle=mantle_binding,
        t0_world_age_ma=T0_WORLD_AGE_MA, surface_temperature_k=hwr.t0_k,
        surface_heat_flow_w_m2=q_surface, physical_ocean_age_ma=None,
        hwr_model=hwr, gravity_m_s2=9.82, initializer_family=INITIALIZER_FAMILY,
        boundary_scenario_id="CONTINENTAL_AUTHORED_Q_AND_T0_REFERENCE_V1",
        configuration_identities={
            "heat_flow_config_canonical_text_sha256": canonical_text_sha256(heat_config_path),
            "material_reference_config_canonical_text_sha256": canonical_text_sha256(material_config_path),
            "b6n8n_index_canonical_text_sha256": canonical_text_sha256(root / "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json"),
            "field_package_sha256": index["field_package"]["sha256"],
        },
        support_lineage={"grid_id": index["grid"]["grid_id"], "native_row": str(row),
                         "native_column": str(column), "field_package": index["field_package"]["path"]},
        uncertainty={"classification": "REFERENCE_RANGE_AND_MODEL_FORM; NOT_A_PROBABILITY_DISTRIBUTION",
                     "scenario_scope": ENGINEERING_SCENARIO},
        binding_status="EXACTLY_ONE_INITIALIZER_BINDING", units=REQUIRED_UNITS,
    )
    plan = build_initializer_plan(binding)
    column = continental_column(
        q_surface=q_surface, crust_m=crust_m, total_lithosphere_m=base_m,
        crust=crust_binding.material, mantle=mantle_binding.material, model=hwr,
        mantle_alpha_k_1=float(mantle_binding.alpha_k_1), gravity_m_s2=9.82,
    )
    z_crust = np.linspace(0.0, crust_m, crust_intervals + 1)
    z_mantle = np.linspace(crust_m, base_m, mantle_intervals + 1)[1:]
    z = np.concatenate((z_crust, z_mantle))
    temperature = np.asarray([_profile_temperature(column, float(value)) for value in z], dtype=np.float64)
    materials = tuple(
        _node_material(crust_binding if value <= crust_m else mantle_binding)
        for value in z
    )
    if (len(z) != len(temperature) or len(z) != len(materials)
            or not np.isfinite(z).all() or not np.isfinite(temperature).all()
            or np.any(np.diff(z) <= 0)):
        raise ValueError("T0_PROFILE_GRID_OR_VALUE_INVALID")
    profile = T0Profile(
        support_id=support_id, support_class=support_class,
        scenario_id=ENGINEERING_SCENARIO, crust_m=crust_m, model_base_m=base_m,
        surface_temperature_k=hwr.t0_k, base_temperature_k=column.lab_temperature_k,
        surface_heat_flow_w_m2=q_surface, z_m=tuple(map(float, z)),
        temperature_k=tuple(map(float, temperature)), materials=materials,
        material_roles=(crust_binding.role_id, mantle_binding.role_id),
        provenance={
            "initializer_family": INITIALIZER_FAMILY,
            "initializer_plan_identity_sha256": plan.plan_identity_sha256,
            "b6n8n_binding_status": "EXACTLY_ONE_INITIALIZER_BINDING",
            "profile_kernel": "pre_orbdata_thermal_column.continental_column",
            "support_fields": {"physical_crust_domain_id": domain_id,
                               "continental_thermal_domain_id": thermal_id,
                               "crustal_thickness_m": crust_m,
                               "continental_reference_lithosphere_thickness_m": base_m,
                               "continental_reference_surface_heat_flow_w_m2": q_surface},
            "piecewise_profile_coefficients": [list(row) for row in column.profile_coefficients],
            "moho_temperature_k": column.moho_temperature_k,
            "moho_heat_flux_w_m2": column.moho_flux_w_m2,
            "model_base_temperature_k": column.lab_temperature_k,
            "material_tuple_references": [crust_binding.tuple_reference, mantle_binding.tuple_reference],
            "thermal_reference_config_canonical_text_sha256": canonical_text_sha256(heat_config_path),
            "material_reference_config_canonical_text_sha256": canonical_text_sha256(material_config_path),
            "scenario_roster_status": "ONE_LOCAL_ENGINEERING_CASE; NOT_B6N8R_EXECUTION_ROSTER",
            "canonical_state": False,
        },
    )
    _validate_profile(profile)
    return profile, {"admitted_count": preflight.admitted_count,
                     "continental_admitted_count": preflight.continental_count,
                     "plan_identity_sha256": plan.plan_identity_sha256,
                     "source_commit": _git(root, "rev-parse", "HEAD")}


def initial_reduced_state(profile: T0Profile, *, initial_width_m: float) -> ReducedState:
    if not math.isfinite(initial_width_m) or initial_width_m <= 0:
        raise ValueError("INITIAL_WIDTH_MUST_BE_POSITIVE")
    xi = tuple(z / profile.model_base_m for z in profile.z_m)
    return ReducedState(
        time_s=0.0, initial_width_m=initial_width_m, width_m=initial_width_m,
        initial_crust_m=profile.crust_m, initial_lithosphere_m=profile.model_base_m,
        crust_m=profile.crust_m, lithosphere_m=profile.model_base_m, beta=1.0,
        accumulated_strain=0.0, crust_fraction=profile.crust_m / profile.model_base_m,
        material_coordinate=xi, temperature_k=profile.temperature_k,
        materials=profile.materials, surface_temperature_k=profile.surface_temperature_k,
        base_temperature_k=profile.base_temperature_k,
    )


def pure_shear_thermal_step(
    state: ReducedState,
    *,
    duration_s: float,
    extension_velocity_m_s: float,
    maximum_kinematic_fraction_per_substep: float = 0.01,
) -> tuple[ReducedState, StepDiagnostics]:
    """Advance an engineering 1-D section using Lagrangian pure shear + heat.

    In physical z, w(z)=-epsilon_dot*z and
    dT/dt + w*dT/dz = div(k grad(T))/(rho Cp) + A/(rho Cp).
    The material-coordinate mesh moves with w, so the advective transport is
    represented by vertical mesh contraction; conduction/source are integrated
    explicitly on that updated mesh. Surface and model-base temperatures are
    held fixed as declared engineering boundary conditions.
    """
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("FINITE_POSITIVE_DURATION_REQUIRED")
    if not math.isfinite(extension_velocity_m_s):
        raise ValueError("EXTENSION_VELOCITY_NONFINITE")
    if extension_velocity_m_s < 0:
        raise ValueError("COMPRESSION_NOT_ADMISSIBLE_TO_EXTENSION_ONLY_V0")
    if not 0 < maximum_kinematic_fraction_per_substep <= 0.05:
        raise ValueError("KINEMATIC_SUBSTEP_LIMIT_OUTSIDE_NUMERICAL_POLICY")
    if len(state.temperature_k) != len(state.material_coordinate) or len(state.materials) != len(state.temperature_k):
        raise ValueError("REDUCED_STATE_CARDINALITY_MISMATCH")
    remaining = duration_s
    current = state
    substeps = 0
    min_limit = math.inf
    max_ratio = 0.0
    area_before = state.width_m * state.lithosphere_m
    while remaining > max(1e-9, duration_s * 1e-15):
        z = tuple(x * current.lithosphere_m for x in current.material_coordinate)
        stability = _diffusion_stability_limit(z, current.materials)
        min_limit = min(min_limit, stability)
        dt = min(remaining, 0.8 * stability)
        if extension_velocity_m_s > 0:
            dt = min(dt, maximum_kinematic_fraction_per_substep * current.width_m / extension_velocity_m_s)
        # The moving material grid shortens its diffusion spacing during this
        # substep. Tighten dt against the updated geometry before evaluating.
        for _ in range(8):
            beta_increment = 1.0 + extension_velocity_m_s * dt / current.width_m
            trial_h = current.lithosphere_m / beta_increment
            trial_z = tuple(x * trial_h for x in current.material_coordinate)
            updated_limit = _diffusion_stability_limit(trial_z, current.materials)
            min_limit = min(min_limit, updated_limit)
            if dt <= 0.8 * updated_limit:
                break
            dt = 0.8 * updated_limit
        else:
            raise ValueError("MOVING_GRID_STABILITY_LIMIT_DID_NOT_CONVERGE")
        beta_increment = 1.0 + extension_velocity_m_s * dt / current.width_m
        if not math.isfinite(beta_increment) or beta_increment < 1.0:
            raise ValueError("PURE_SHEAR_STRETCH_FACTOR_INVALID")
        new_width = current.width_m * beta_increment
        new_lithosphere = current.lithosphere_m / beta_increment
        new_crust = current.crust_m / beta_increment
        new_z = tuple(x * new_lithosphere for x in current.material_coordinate)
        next_temperature = _explicit_thermal_update(
            current.temperature_k, new_z, current.materials, dt,
            current.surface_temperature_k, current.base_temperature_k,
        )
        ratio = dt / updated_limit
        max_ratio = max(max_ratio, ratio)
        elapsed = current.time_s + dt
        beta_total = new_width / current.initial_width_m
        current = ReducedState(
            time_s=elapsed, initial_width_m=current.initial_width_m, width_m=new_width,
            initial_crust_m=current.initial_crust_m,
            initial_lithosphere_m=current.initial_lithosphere_m,
            crust_m=new_crust, lithosphere_m=new_lithosphere, beta=beta_total,
            accumulated_strain=math.log(beta_total), crust_fraction=current.crust_fraction,
            material_coordinate=current.material_coordinate, temperature_k=next_temperature,
            materials=current.materials, surface_temperature_k=current.surface_temperature_k,
            base_temperature_k=current.base_temperature_k,
        )
        remaining -= dt
        substeps += 1
        if substeps > 1_000_000:
            raise ValueError("THERMAL_KERNEL_SUBSTEP_LIMIT_EXCEEDED")
    _validate_reduced_state(current)
    area_after = current.width_m * current.lithosphere_m
    area_error = abs(area_after - area_before) / area_before
    diagnostics = StepDiagnostics(
        duration_s=duration_s, substeps=substeps, min_stability_limit_s=min_limit,
        max_stability_ratio=max_ratio, area_before_m2=area_before,
        area_after_m2=area_after, area_relative_error=area_error,
        min_temperature_k=min(current.temperature_k), max_temperature_k=max(current.temperature_k),
    )
    return current, diagnostics


def evolve_fixed_geometry_thermal_profile(
    profile: T0Profile,
    *,
    duration_s: float,
    maximum_substep_s: float | None = None,
) -> tuple[tuple[float, ...], ThermalEvolutionDiagnostics]:
    """Engineering pre-event thermal evolution with geometry held fixed.

    This is intentionally distinct from post-activation pure-shear forcing.
    Surface and model-base temperatures are held at the declared reference
    values; the supplied material roles and radiogenic sources are retained.
    """
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("FINITE_POSITIVE_DURATION_REQUIRED")
    if maximum_substep_s is not None and (not math.isfinite(maximum_substep_s) or maximum_substep_s <= 0):
        raise ValueError("MAXIMUM_SUBSTEP_MUST_BE_POSITIVE")
    start = tuple(profile.temperature_k)
    values = start
    remaining = duration_s
    min_limit = math.inf
    max_ratio = 0.0
    substeps = 0
    while remaining > max(1e-9, duration_s * 1e-15):
        limit = _diffusion_stability_limit(profile.z_m, profile.materials)
        min_limit = min(min_limit, limit)
        dt = min(remaining, 0.8 * limit)
        if maximum_substep_s is not None:
            dt = min(dt, maximum_substep_s)
        values = _explicit_thermal_update(
            values, profile.z_m, profile.materials, dt,
            profile.surface_temperature_k, profile.base_temperature_k,
        )
        max_ratio = max(max_ratio, dt / limit)
        remaining -= dt
        substeps += 1
        if substeps > 1_000_000:
            raise ValueError("THERMAL_KERNEL_SUBSTEP_LIMIT_EXCEEDED")
    return values, ThermalEvolutionDiagnostics(
        duration_s=duration_s, substeps=substeps, min_stability_limit_s=min_limit,
        max_stability_ratio=max_ratio,
        temperature_change_linf_k=max(abs(a - b) for a, b in zip(values, start)),
    )


def state_from_payload(payload: Mapping[str, Any]) -> ReducedState:
    if payload.get("schema") != "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_REDUCED_STATE_V1":
        raise ValueError("CHECKPOINT_SCHEMA_INVALID")
    materials = tuple(NodeMaterial(**row) for row in payload["materials"])
    state = ReducedState(
        time_s=float(payload["time_s"]), initial_width_m=float(payload["initial_width_m"]),
        width_m=float(payload["width_m"]), initial_crust_m=float(payload["initial_crust_m"]),
        initial_lithosphere_m=float(payload["initial_lithosphere_m"]), crust_m=float(payload["crust_m"]),
        lithosphere_m=float(payload["lithosphere_m"]), beta=float(payload["beta"]),
        accumulated_strain=float(payload["accumulated_strain"]),
        crust_fraction=float(payload["crust_fraction"]),
        material_coordinate=tuple(map(float, payload["material_coordinate"])),
        temperature_k=tuple(map(float, payload["temperature_k"])), materials=materials,
        surface_temperature_k=float(payload["surface_temperature_k"]),
        base_temperature_k=float(payload["base_temperature_k"]),
    )
    _validate_reduced_state(state)
    return state


def select_pair_13_interior_segment(repository_root: str | Path) -> dict[str, Any]:
    """Return geometry-only middle interior edge and its exact T0 field sides.

    B6N8-N excludes all 1:3 edge-adjacent ocean cells. The result therefore
    intentionally reports a mapping blocker and does not bind either side to
    the continental profile or execute a rift step.
    """
    root = Path(repository_root).resolve()
    manifest = _read_json(root / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
    pair = [row for row in manifest["segments"] if row["ordered_plate_pair"] == [1, 3]]
    if len(pair) != 71:
        raise ValueError("PAIR_1_3_SEGMENT_COUNT_CHANGED")
    degrees: dict[str, int] = {}
    for row in pair:
        for vertex in row["endpoint_vertex_ids"]:
            degrees[vertex] = degrees.get(vertex, 0) + 1
    interior = [row for row in pair if all(degrees[v] == 2 for v in row["endpoint_vertex_ids"])]
    if len(interior) != 69:
        raise ValueError("PAIR_1_3_INTERIOR_ENDPOINT_AUDIT_CHANGED")
    segment = sorted(interior, key=lambda row: row["boundary_id"])[len(interior) // 2]
    edge = segment["parent_grid_edge"]
    row, column = int(edge["row"]), int(edge["column"])
    if edge["axis"] == "NORTH":
        cells = ((row, column), (row + 1, column))
    elif edge["axis"] == "EAST":
        cells = ((row, column), (row, (column + 1) % 360))
    else:
        raise ValueError("BOUNDARY_EDGE_AXIS_UNSUPPORTED")
    index = _read_json(root / "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json")
    realization = _read_json(root / "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json")
    selected = set(realization["derived_fields"]["oceanic_age"]["selected_source_boundary_ids"])
    boundary_rows = manifest["segments"]
    with np.load(root / index["field_package"]["path"], allow_pickle=False) as arrays:
        domain, age = arrays["physical_crust_domain_id"], arrays["oceanic_lithosphere_age_ma"]
        from .pre_orbdata_t0_initializer import _reconstruct_ocean_exclusions
        excluded, _, _ = _reconstruct_ocean_exclusions(domain, age, boundary_rows, selected)
        side_rows = []
        for r, c in cells:
            ident = _cell_id(r, c)
            dom, age_value = int(domain[r, c]), float(age[r, c])
            admitted = bool((dom in (2, 3, 4, 5, 6)) or (dom == 1 and math.isfinite(age_value) and age_value > 0 and ident not in excluded))
            side_rows.append({"support_id": ident, "row": r, "column": c,
                              "physical_crust_domain_id": dom, "oceanic_age_ma": age_value,
                              "B6N8N_admitted": admitted,
                              "plate_membership": "UNKNOWN_NOT_IN_T0_FIELD_PACKAGE"})
    return {
        "plate_pair": [1, 3], "boundary_id": segment["boundary_id"],
        "selection_rule": "LEXICAL_MIDDLE_OF_INTERIOR_EDGES_FOR_DEVELOPMENT_PROBE_ONLY",
        "physical_section_selected": False,
        "ordered_plate_pair": segment["ordered_plate_pair"],
        "endpoint_vertex_ids": segment["endpoint_vertex_ids"],
        "endpoint_degrees": [degrees[v] for v in segment["endpoint_vertex_ids"]],
        "parent_grid_edge": edge, "length_m": segment["length_m"],
        "normal_convention": segment["normal_convention"],
        "boundary_process_class": segment["boundary_process_class"],
        "relative_normal_velocity_m_per_year": segment["relative_normal_velocity_m_per_year"],
        "relative_tangential_velocity_m_per_year": segment["relative_tangential_velocity_m_per_year"],
        "velocity_role": "T0_BOUNDARY_MANIFEST_DIAGNOSTIC_ONLY_NOT_B6N2_POST_EVENT_FORCING",
        "adjacent_supports": side_rows,
        "material_mapping_status": "BLOCKED_B6N8N_SUPPORT_EXCLUSION_AND_CELL_TO_PLATE_MEMBERSHIP_UNKNOWN",
        "rift_step_executed": False,
    }


def _profile_temperature(column: Any, z_m: float) -> float:
    if z_m <= column.crust_m:
        _, _, c2, c1, c0 = column.profile_coefficients[0]
        x = z_m
        return (c2 * x + c1) * x + c0
    z0, _, c2, c1, c0 = column.profile_coefficients[1]
    x = z_m - z0
    return (c2 * x + c1) * x + c0


def _node_material(binding: LayerPropertyBinding) -> NodeMaterial:
    material = binding.material
    return NodeMaterial(binding.role_id, material.k, material.rho, material.cp, material.radiogenic_w_m3)


def _diffusion_stability_limit(z: Sequence[float], materials: Sequence[NodeMaterial]) -> float:
    if len(z) != len(materials) or len(z) < 3:
        raise ValueError("THERMAL_GRID_CARDINALITY_INVALID")
    limits = []
    for i in range(1, len(z) - 1):
        dl, dr = z[i] - z[i - 1], z[i + 1] - z[i]
        if dl <= 0 or dr <= 0:
            raise ValueError("THERMAL_GRID_NOT_STRICTLY_INCREASING")
        gl = 1.0 / (0.5 * dl / materials[i - 1].k_w_m_k + 0.5 * dl / materials[i].k_w_m_k)
        gr = 1.0 / (0.5 * dr / materials[i].k_w_m_k + 0.5 * dr / materials[i + 1].k_w_m_k)
        capacity = materials[i].rho_kg_m3 * materials[i].cp_j_kg_k * 0.5 * (dl + dr)
        limits.append(capacity / (gl + gr))
    limit = min(limits)
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError("THERMAL_EXPLICIT_STABILITY_LIMIT_INVALID")
    return limit


def _explicit_thermal_update(
    temperatures: Sequence[float], z: Sequence[float], materials: Sequence[NodeMaterial],
    dt_s: float, surface_k: float, base_k: float,
) -> tuple[float, ...]:
    output = list(map(float, temperatures))
    for i in range(1, len(output) - 1):
        dl, dr = z[i] - z[i - 1], z[i + 1] - z[i]
        mat = materials[i]
        gl = 1.0 / (0.5 * dl / materials[i - 1].k_w_m_k + 0.5 * dl / mat.k_w_m_k)
        gr = 1.0 / (0.5 * dr / mat.k_w_m_k + 0.5 * dr / materials[i + 1].k_w_m_k)
        cv = 0.5 * (dl + dr)
        capacity = mat.rho_kg_m3 * mat.cp_j_kg_k * cv
        net = gr * (temperatures[i + 1] - temperatures[i]) - gl * (temperatures[i] - temperatures[i - 1])
        output[i] = temperatures[i] + dt_s * (net + mat.radiogenic_w_m3 * cv) / capacity
    output[0], output[-1] = surface_k, base_k
    if not all(math.isfinite(value) and value > 0 for value in output):
        raise ValueError("THERMAL_UPDATE_NONFINITE_OR_NONPOSITIVE")
    return tuple(output)


def _validate_profile(profile: T0Profile) -> None:
    if not (0 < profile.crust_m < profile.model_base_m):
        raise ValueError("T0_PROFILE_GEOMETRY_INVALID")
    if not (len(profile.z_m) == len(profile.temperature_k) == len(profile.materials)):
        raise ValueError("T0_PROFILE_CARDINALITY_INVALID")
    if profile.z_m[0] != 0.0 or not math.isclose(profile.z_m[-1], profile.model_base_m, abs_tol=1e-8):
        raise ValueError("T0_PROFILE_ENDPOINTS_INVALID")
    if min(profile.temperature_k) <= 0 or not all(math.isfinite(x) for x in profile.temperature_k):
        raise ValueError("T0_PROFILE_TEMPERATURE_INVALID")
    if profile.material_roles != ("CONTINENTAL_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE"):
        raise ValueError("T0_PROFILE_DISCRETE_MATERIAL_SEQUENCE_INVALID")
    i = min(range(len(profile.z_m)), key=lambda j: abs(profile.z_m[j] - profile.crust_m))
    if profile.z_m[i] != profile.crust_m or profile.materials[i].role_id != profile.material_roles[0]:
        raise ValueError("T0_PROFILE_MOHO_GRID_OR_PHASE_INVALID")
    if profile.materials[i + 1].role_id != profile.material_roles[1]:
        raise ValueError("T0_PROFILE_MANTLE_PHASE_NOT_SELECTED_AFTER_MOHO")


def _validate_reduced_state(state: ReducedState) -> None:
    n = len(state.material_coordinate)
    if n < 3 or len(state.temperature_k) != n or len(state.materials) != n:
        raise ValueError("REDUCED_STATE_CARDINALITY_INVALID")
    numeric = (state.time_s, state.initial_width_m, state.width_m, state.initial_crust_m,
               state.initial_lithosphere_m, state.crust_m, state.lithosphere_m,
               state.beta, state.accumulated_strain, state.crust_fraction,
               state.surface_temperature_k, state.base_temperature_k, *state.temperature_k)
    if not all(math.isfinite(x) for x in numeric) or min(state.temperature_k) <= 0:
        raise ValueError("REDUCED_STATE_NONFINITE_OR_NONPOSITIVE")
    if not (state.width_m > 0 and state.lithosphere_m > 0 and 0 < state.crust_m < state.lithosphere_m):
        raise ValueError("REDUCED_STATE_GEOMETRY_INVALID")
    if any(b <= a for a, b in zip(state.material_coordinate, state.material_coordinate[1:])):
        raise ValueError("MATERIAL_COORDINATE_NOT_MONOTONE")
    if not math.isclose(state.crust_m / state.lithosphere_m, state.crust_fraction, rel_tol=1e-12, abs_tol=1e-14):
        raise ValueError("PURE_SHEAR_INTERFACE_FRACTION_CHANGED")
    if not math.isclose(state.width_m * state.lithosphere_m,
                        state.initial_width_m * state.initial_lithosphere_m, rel_tol=2e-14, abs_tol=1e-6):
        raise ValueError("PURE_SHEAR_AREA_NOT_CONSERVED")
    if len(state.materials) != len(state.temperature_k):
        raise ValueError("DISCRETE_MATERIAL_ID_INTERPOLATION_PROHIBITED")


def _read_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"AUTHORITY_JSON_NOT_OBJECT:{path.name}")
    return result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    import subprocess
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"GIT_IDENTITY_QUERY_FAILED:{' '.join(args)}")
    return result.stdout.strip()
