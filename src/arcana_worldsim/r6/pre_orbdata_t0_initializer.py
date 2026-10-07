"""Synthetic-only execution adapter for the qualified R6 T0 column initializer.

The numerical equations remain in :mod:`pre_orbdata_thermal_column`.  This
module validates B6N8-N bindings, builds a metadata-only plan for admitted
production support, and exposes numerical evaluation only for explicitly
non-canonical test fixtures.  It has no WORLD_HISTORY or filesystem write API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

import numpy as np

from .pre_orbdata_heat_flow import HWR2
from .pre_orbdata_thermal_column import (
    Column,
    LayerMaterial,
    continental_column,
    ocean_column,
)
from .repository_context import canonical_text_sha256

INITIALIZER_FAMILY = "R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING"
INITIALIZER_RECIPE = "R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING_V1"
T0_WORLD_AGE_MA = 210.0
N_ATTESTATION_VERDICT = (
    "PASS_B6N8N_ADMITTED_SUPPORT_BINDINGS_CLOSED_READY_FOR_T0_INITIALIZER_IMPLEMENTATION"
)
NATIVE_ID = re.compile(r"^R6G1D-R[0-9]{3}-C[0-9]{3}$")
FIXTURE_ID = re.compile(r"^TEST_[A-Z0-9_]+$")

REQUIRED_UNITS = {
    "depth": "m",
    "temperature": "K",
    "heat_flow": "W m-2",
    "conductivity": "W m-1 K-1",
    "density": "kg m-3",
    "heat_capacity": "J kg-1 K-1",
    "diffusivity": "m2 s-1",
    "radiogenic_source": "W m-3",
    "age": "Ma",
    "gravity": "m s-2",
    "thermal_expansion": "K-1",
}


class FailureCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    UNAUTHORIZED_SUPPORT = "UNAUTHORIZED_SUPPORT"
    MISSING_BINDING = "MISSING_BINDING"
    UNSUPPORTED_CONFIGURATION = "UNSUPPORTED_CONFIGURATION"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"


class InitializerError(ValueError):
    def __init__(self, code: FailureCode, message: str):
        self.code = code
        super().__init__(f"{code.value}:{message}")


@dataclass(frozen=True)
class LayerPropertyBinding:
    role_id: str
    tuple_reference: str
    source_term_reference: str
    material: LayerMaterial
    alpha_k_1: float | None
    kappa_reference_m2_s: float
    bounds: Mapping[str, tuple[float, float]]
    authority_reference: str
    uncertainty: Mapping[str, Any]


@dataclass(frozen=True)
class ColumnBinding:
    support_id: str
    support_class: str
    geometry_reference: str
    surface_datum: str
    crust_depth_m: float
    model_base_depth_m: float
    model_base_semantics: str
    physical_lab_depth_m: float | None
    material_role_sequence: tuple[str, str]
    crust: LayerPropertyBinding
    mantle: LayerPropertyBinding
    t0_world_age_ma: float
    surface_temperature_k: float
    surface_heat_flow_w_m2: float | None
    physical_ocean_age_ma: float | None
    hwr_model: HWR2
    gravity_m_s2: float
    initializer_family: str
    boundary_scenario_id: str
    configuration_identities: Mapping[str, str]
    support_lineage: Mapping[str, str]
    uncertainty: Mapping[str, Any]
    binding_status: str
    units: Mapping[str, str]


@dataclass(frozen=True)
class InitializerPlan:
    binding: ColumnBinding
    crust_kappa_m2_s: float
    mantle_kappa_m2_s: float
    plan_identity_sha256: str


@dataclass(frozen=True)
class SyntheticColumnFixture:
    non_canonical_test_fixture: bool
    fixture_name: str
    binding: ColumnBinding


@dataclass(frozen=True)
class ProfileSegment:
    z0_m: float
    z1_m: float
    basis: str
    coefficients: tuple[float, ...]
    material_role: str


@dataclass(frozen=True)
class InitializerResult:
    support_id: str
    surface_datum: str
    world_age_ma: float
    physical_ocean_age_ma: float | None
    initializer_family: str
    scenario_id: str
    geometry_reference: str
    model_base_semantics: str
    model_base_depth_m: float
    crust_depth_m: float
    thermal_lab_depth_m: float
    thermal_lab_temperature_k: float
    moho_temperature_k: float
    surface_heat_flow_w_m2: float
    effective_column_rate_k_s: float | None
    layer_roles: tuple[str, str]
    property_tuple_references: tuple[str, str]
    source_term_references: tuple[str, str]
    derived_kappa_m2_s: tuple[float, float]
    configuration_identities: tuple[tuple[str, str], ...]
    numerical_configuration: Mapping[str, Any]
    support_lineage: tuple[tuple[str, str], ...]
    uncertainty: Mapping[str, Any]
    provenance: Mapping[str, Any]
    segments: tuple[ProfileSegment, ...]
    validation_status: str
    result_sha256: str
    _layer_materials: tuple[LayerPropertyBinding, LayerPropertyBinding]

    def temperature_at(self, depth_m: float) -> float:
        if not math.isfinite(depth_m) or depth_m < 0 or depth_m > self.thermal_lab_depth_m:
            raise InitializerError(FailureCode.INVALID_INPUT, "DEPTH_OUTSIDE_PROFILE_DOMAIN")
        if not math.isfinite(depth_m) or depth_m < 0 or depth_m > self.thermal_lab_depth_m:
            raise InitializerError(FailureCode.INVALID_INPUT, "DEPTH_OUTSIDE_PROFILE_DOMAIN")
        segment = self._segment_at(depth_m)
        x = depth_m - segment.z0_m
        if segment.basis == "LOCAL_QUADRATIC_C2_C1_C0":
            c2, c1, c0 = segment.coefficients
            return (c2 * x + c1) * x + c0
        if segment.basis == "NORMALIZED_CUBIC_HERMITE_A_B_C_D":
            a, b, c, d = segment.coefficients
            s = x / (segment.z1_m - segment.z0_m)
            return ((a * s + b) * s + c) * s + d
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "PROFILE_BASIS_UNKNOWN")

    def flux_at(self, depth_m: float) -> float:
        if not math.isfinite(depth_m) or depth_m < 0 or depth_m > self.thermal_lab_depth_m:
            raise InitializerError(FailureCode.INVALID_INPUT, "DEPTH_OUTSIDE_PROFILE_DOMAIN")
        segment = self._segment_at(depth_m)
        material = self._material_for_role(segment.material_role)
        x = depth_m - segment.z0_m
        if segment.basis == "LOCAL_QUADRATIC_C2_C1_C0":
            c2, c1, _ = segment.coefficients
            gradient = 2.0 * c2 * x + c1
        else:
            a, b, c, _ = segment.coefficients
            s = x / (segment.z1_m - segment.z0_m)
            gradient = (3.0 * a * s * s + 2.0 * b * s + c) / (segment.z1_m - segment.z0_m)
        return material.material.k * gradient

    def equation_residual_rate_k_s(self, depth_m: float) -> float:
        """Return the profile-implied local residual rate; this is diagnostic only."""
        if not math.isfinite(depth_m) or depth_m < 0 or depth_m > self.thermal_lab_depth_m:
            raise InitializerError(FailureCode.INVALID_INPUT, "DEPTH_OUTSIDE_PROFILE_DOMAIN")
        segment = self._segment_at(depth_m)
        material_binding = self._material_for_role(segment.material_role)
        x = depth_m - segment.z0_m
        if segment.basis == "LOCAL_QUADRATIC_C2_C1_C0":
            c2, _, _ = segment.coefficients
            second = 2.0 * c2
        else:
            a, b, _, _ = segment.coefficients
            s = x / (segment.z1_m - segment.z0_m)
            second = (6.0 * a * s + 2.0 * b) / (segment.z1_m - segment.z0_m) ** 2
        mat = material_binding.material
        return (mat.k * second + mat.radiogenic_w_m3) / (mat.rho * mat.cp)

    def serialize(self) -> bytes:
        """Canonical JSON bytes for candidate output; this method performs no I/O."""
        payload = _result_payload(self)
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    def _segment_at(self, depth_m: float) -> ProfileSegment:
        for index, segment in enumerate(self.segments):
            if segment.z0_m <= depth_m < segment.z1_m:
                return segment
            if depth_m == segment.z1_m and index == len(self.segments) - 1:
                return segment
        raise InitializerError(FailureCode.INVALID_INPUT, "DEPTH_NOT_COVERED_BY_PROFILE")

    def _material_for_role(self, role: str) -> LayerPropertyBinding:
        for material in self._layer_materials:
            if material.role_id == role:
                return material
        raise InitializerError(FailureCode.MISSING_BINDING, "PROFILE_MATERIAL_ROLE_MISSING")


@dataclass(frozen=True)
class PreflightResult:
    native_support_count: int
    admitted_count: int
    continental_count: int
    positive_age_ocean_count: int
    unresolved_positive_age_ocean_excluded: int
    zero_age_ridge_excluded: int
    other_out_of_scope: int
    admitted_unresolved: int
    admitted_ambiguous: int
    candidate_boundary_segments: int
    adjacent_oceanic_cells: int
    ridge_overlap_cells: int
    deterministic_plan_sha256: str
    temperature_profiles_evaluated: bool
    production_execution_authorized: bool


def role_binding_from_registry(
    registry: Mapping[str, Any], role_id: str, *,
    overrides: Mapping[str, float] | None = None,
) -> LayerPropertyBinding:
    """Build one tuple directly from the qualified B6N8-N registry."""
    try:
        role = registry["roles"][role_id]
        props = role["properties"]
        override = dict(overrides or {})
        if set(override) - set(props):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"UNAUTHORIZED_PROPERTY_OVERRIDE:{role_id}")
        def value(name: str) -> float:
            return float(override.get(name, props[name]["nominal"]))
        bounds: dict[str, tuple[float, float]] = {}
        for key in ("k", "rho", "Cp", "A_C", "A_M", "alpha"):
            if key not in props:
                continue
            entry = props[key]
            interval = entry.get("sensitivity_range", entry.get("range"))
            if not isinstance(interval, list) or len(interval) != 2:
                raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"BOUNDS_MISSING:{role_id}:{key}")
            bounds[key] = (float(interval[0]), float(interval[1]))
        source_key = "A_C" if role_id.endswith("CRUST_REFERENCE") else "A_M"
        alpha = value("alpha") if "alpha" in props else None
        source_bounds = bounds.get(source_key)
        if source_bounds is None:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"SOURCE_TERM_BOUNDS_MISSING:{role_id}")
        expected_kappa = float(role["kappa_nominal_m2_s"])
        computed_kappa = value("k") / (value("rho") * value("Cp"))
        if not math.isclose(computed_kappa, expected_kappa, rel_tol=1e-14, abs_tol=0.0) and not overrides:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"KAPPA_REGISTRY_MISMATCH:{role_id}")
        return LayerPropertyBinding(
            role_id=role_id,
            tuple_reference=_registry_role_identity(registry, role_id),
            source_term_reference=source_key,
            material=LayerMaterial(value("k"), value("rho"), value("Cp"), value(source_key)),
            alpha_k_1=alpha,
            kappa_reference_m2_s=computed_kappa,
            bounds=bounds,
            authority_reference="B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json",
            uncertainty={"authority": "QUALIFIED_SOURCE_RANGE_OR_SCENARIO; NOT_A_PROBABILITY_DISTRIBUTION"},
        )
    except InitializerError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise InitializerError(FailureCode.MISSING_BINDING, f"PROPERTY_TUPLE:{role_id}") from exc


def build_initializer_plan(binding: ColumnBinding) -> InitializerPlan:
    """Validate an initializer input and produce a non-generative plan."""
    _validate_binding(binding)
    crust_kappa = _derive_kappa(binding.crust)
    mantle_kappa = _derive_kappa(binding.mantle)
    identity = {
        "support_id": binding.support_id,
        "support_class": binding.support_class,
        "geometry_reference": binding.geometry_reference,
        "interfaces_m": [0.0, binding.crust_depth_m, binding.model_base_depth_m],
        "material_roles": list(binding.material_role_sequence),
        "tuple_refs": [binding.crust.tuple_reference, binding.mantle.tuple_reference],
        "property_values": [_layer_property_payload(binding.crust), _layer_property_payload(binding.mantle)],
        "kappa": [crust_kappa, mantle_kappa],
        "source_terms": [binding.crust.source_term_reference, binding.mantle.source_term_reference],
        "world_age_ma": binding.t0_world_age_ma,
        "surface_temperature_k": binding.surface_temperature_k,
        "surface_heat_flow_w_m2": binding.surface_heat_flow_w_m2,
        "physical_ocean_age_ma": binding.physical_ocean_age_ma,
        "gravity_m_s2": binding.gravity_m_s2,
        "hwr_model": asdict(binding.hwr_model),
        "units": dict(sorted(binding.units.items())),
        "uncertainty": binding.uncertainty,
        "family": binding.initializer_family,
        "scenario": binding.boundary_scenario_id,
        "config": dict(sorted(binding.configuration_identities.items())),
        "lineage": dict(sorted(binding.support_lineage.items())),
    }
    digest = hashlib.sha256(_canonical_json(identity)).hexdigest()
    return InitializerPlan(binding, crust_kappa, mantle_kappa, digest)


def validate_column_binding(binding: ColumnBinding) -> None:
    """Public input-contract validator; performs no numerical initialization."""
    _validate_binding(binding)


def evaluate_synthetic_fixture(fixture: SyntheticColumnFixture) -> InitializerResult:
    """Evaluate a synthetic fixture only; no public production execution API exists."""
    if not isinstance(fixture, SyntheticColumnFixture) or fixture.non_canonical_test_fixture is not True:
        raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "SYNTHETIC_FIXTURE_MARKER_REQUIRED")
    if not FIXTURE_ID.fullmatch(fixture.binding.support_id) or not fixture.fixture_name.startswith("NON_CANONICAL_"):
        raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "SYNTHETIC_FIXTURE_ID_REQUIRED")
    plan = build_initializer_plan(fixture.binding)
    binding = plan.binding
    try:
        if binding.support_class.startswith("CONTINENTAL_"):
            column = continental_column(
                q_surface=float(binding.surface_heat_flow_w_m2),
                crust_m=binding.crust_depth_m,
                total_lithosphere_m=binding.model_base_depth_m,
                crust=binding.crust.material,
                mantle=binding.mantle.material,
                model=binding.hwr_model,
                mantle_alpha_k_1=float(binding.mantle.alpha_k_1),
                gravity_m_s2=binding.gravity_m_s2,
            )
        else:
            column = ocean_column(
                age_ma=float(binding.physical_ocean_age_ma),
                crust_m=binding.crust_depth_m,
                q_surface=binding.surface_heat_flow_w_m2,
                model=binding.hwr_model,
                ridge=False,
                crust=binding.crust.material,
                mantle_alpha_k_1=float(binding.mantle.alpha_k_1),
                gravity_m_s2=binding.gravity_m_s2,
            )
        return _make_result(plan, column)
    except InitializerError:
        raise
    except (ArithmeticError, ValueError, OverflowError) as exc:
        raise InitializerError(FailureCode.NUMERICAL_FAILURE, str(exc)) from exc


def preflight_admitted_bindings(repository_root: str | Path) -> PreflightResult:
    """Replay and validate admitted support metadata without evaluating T(z,T0)."""
    root = Path(repository_root).resolve()
    try:
        n_attestation = _read_json(root / "docs/arcana/qualifications/R6_B6N8N_ATTESTATION.json")
        if (
            n_attestation.get("qualified_source_commit") != "9d94170ae4a35267cbccd087e112841b4215d07e"
            or n_attestation.get("qualification_status") != "PASS"
            or n_attestation.get("verdict") != N_ATTESTATION_VERDICT
        ):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "B6N8N_ATTESTATION_NOT_QUALIFIED")
        index = _read_json(root / "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json")
        registry = _read_json(root / "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json")
        ledger = _read_json(root / "docs/arcana/research/B6N8N_BINDING_EXCEPTION_LEDGER.json")
        realization = _read_json(root / "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json")
        boundary_manifest = _read_json(root / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
        heat_config = _read_json(root / "R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json")
        package = root / index["field_package"]["path"]
        if _sha256(package) != index["field_package"]["sha256"]:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "FIELD_PACKAGE_HASH_MISMATCH")
        for authority in index["authorities"]:
            path = root / authority["path"]
            if canonical_text_sha256(path) != authority["canonical_text_sha256"]:
                raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"AUTHORITY_HASH_MISMATCH:{authority['path']}")
        for role_id in registry["required_roles"]:
            _validate_registry_role(registry, role_id)
        with np.load(package, allow_pickle=False) as fields:
            domain = fields["physical_crust_domain_id"]
            thermal_class = fields["continental_thermal_domain_id"]
            ocean_age = fields["oceanic_lithosphere_age_ma"]
            crust_depth = fields["crustal_thickness_m"]
            continental_base = fields["continental_reference_lithosphere_thickness_m"]
            continental_q = fields["continental_reference_surface_heat_flow_w_m2"]
        shape = tuple(index["grid"]["shape"])
        if any(tuple(array.shape) != shape for array in (domain, thermal_class, ocean_age, crust_depth, continental_base, continental_q)):
            raise InitializerError(FailureCode.INVALID_INPUT, "FIELD_PACKAGE_SHAPE_MISMATCH")
        if shape != (180, 360):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "UNEXPECTED_NATIVE_GRID")
        selected_ids = set(realization["derived_fields"]["oceanic_age"]["selected_source_boundary_ids"])
        excluded, touching, candidate_segments = _reconstruct_ocean_exclusions(
            domain, ocean_age, boundary_manifest["segments"], selected_ids,
        )
        ridge = {
            _cell_id(row, column)
            for row in range(shape[0]) for column in range(shape[1])
            if domain[row, column] == 1 and ocean_age[row, column] == 0
        }
        native_count = shape[0] * shape[1]
        plan_digest = hashlib.sha256()
        admitted_count = continental_count = ocean_count = invalid_count = 0
        thermal_id_to_class = {1: "CONTINENTAL_COLD_STABLE", 2: "CONTINENTAL_NORMAL", 3: "CONTINENTAL_HOT_EXTENDED"}
        q_by_class = registry["boundary_refs"]["continental_q_existing_by_thermal_class"]["class_values_w_m2"]
        q_name_by_id = {1: "COLD_STABLE", 2: "NORMAL", 3: "HOT_EXTENDED"}
        zp = _hwr_value(registry, "zp")
        hwr = _hwr_from_authority(heat_config)
        hwr_field_bindings = {
            "k": hwr.k_w_m_k,
            "rho_m": hwr.rho_kg_m3,
            "Cp": hwr.cp_j_kg_k,
            "Tb": hwr.tb_k,
            "T0": hwr.t0_k,
            "zp": hwr.zp_m,
        }
        if any(value != _hwr_value(registry, name) for name, value in hwr_field_bindings.items()):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "HWR_CONFIGURATION_REGISTRY_MISMATCH")
        mantle_alpha = registry["roles"]["LITHOSPHERIC_MANTLE_REFERENCE"]["properties"]["alpha"]["nominal"]
        if float(mantle_alpha) != _hwr_value(registry, "alpha"):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "MANTLE_ALPHA_HWR_REGISTRY_MISMATCH")
        if (heat_config["hwr2"]["series_N"] != hwr.n_modes
                or heat_config["hwr2"]["relative_tolerance"] != hwr.convergence_tolerance):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "HWR_NUMERICAL_CONTROLS_MISMATCH")
        if registry["boundary_refs"]["gravity"] != "Existing canonical R6 9.82 m s-2.":
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "GRAVITY_BINDING_NOT_RECOGNIZED")
        class_members: dict[str, set[str]] = {item["class"]: set() for item in index["support_classes"]}
        for row in range(shape[0]):
            for column in range(shape[1]):
                ident = _cell_id(row, column)
                dom = int(domain[row, column])
                age = float(ocean_age[row, column])
                if dom in (2, 3, 4, 5, 6):
                    tid = int(thermal_class[row, column])
                    if tid not in thermal_id_to_class or not math.isfinite(float(continental_base[row, column])):
                        invalid_count += 1
                        continue
                    role_class = thermal_id_to_class[tid]
                    h = float(continental_base[row, column])
                    hc = float(crust_depth[row, column])
                    q = float(continental_q[row, column])
                    qref = float(q_by_class[q_name_by_id[tid]])
                    if not (math.isfinite(hc) and math.isfinite(h) and h > hc > 0 and math.isfinite(q) and abs(q-qref) <= 1e-12):
                        invalid_count += 1
                        continue
                    roles = ("CONTINENTAL_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE")
                    geometry_ref, base_semantics = "CONTINENTAL_AUTHORED_REFERENCE_GEOMETRY", "AUTHORED_TOTAL_THERMAL_THICKNESS_NOT_PHYSICAL_LAB"
                    member_class = role_class
                    extra = {"surface_boundary": "AUTHORED_CONTINENTAL_HEAT_FLOW_AND_T0_REFERENCE", "q_surface_w_m2": q}
                    continental_count += 1
                elif dom == 1 and math.isfinite(age) and age > 0 and ident not in excluded:
                    hc = float(crust_depth[row, column])
                    if not (math.isfinite(hc) and 0 < hc < zp and 1.1491667412337465 <= age <= 160.0):
                        invalid_count += 1
                        continue
                    roles = ("OCEANIC_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE")
                    geometry_ref, base_semantics = "POSITIVE_AGE_HWR2_GEOMETRY", "HWR_FINITE_PLATE_BASE_NOT_PHYSICAL_LAB"
                    h = zp
                    member_class = "OCEAN_POSITIVE_AGE_ADMITTED"
                    extra = {"surface_boundary": "HWR2_POSITIVE_AGE_MODEL_FLUX", "oceanic_age_ma": age}
                    ocean_count += 1
                elif dom == 1 and math.isfinite(age) and age > 0 and ident in excluded:
                    class_members["UNRESOLVED_POSITIVE_AGE_OCEAN"].add(ident)
                    continue
                elif dom == 1 and math.isfinite(age) and age == 0:
                    class_members["ZERO_AGE_RIDGE"].add(ident)
                    continue
                else:
                    invalid_count += 1
                    continue
                if member_class not in class_members:
                    invalid_count += 1
                    continue
                class_members[member_class].add(ident)
                bindings = [_registry_role_identity(registry, role) for role in roles]
                record = {
                    "support_id": ident,
                    "support_class": member_class,
                    "geometry_reference": geometry_ref,
                    "interfaces_m": [0.0, hc, h],
                    "base_semantics": base_semantics,
                    "roles": list(roles),
                    "tuple_refs": bindings,
                    "derived_kappa_m2_s": [
                        _role_kappa(registry, roles[0]), _role_kappa(registry, roles[1]),
                    ],
                    "source_terms": ["A_C", "A_M"],
                    "initializer_family": INITIALIZER_FAMILY,
                    "scenario_id": extra,
                }
                plan_digest.update(_canonical_json(record) + b"\n")
                admitted_count += 1
        if invalid_count:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"ADMITTED_METADATA_INVALID:{invalid_count}")
        if sum(map(len, class_members.values())) != native_count:
            raise InitializerError(FailureCode.INVALID_INPUT, "SUPPORT_PARTITION_INCOMPLETE_OR_OVERLAPPING")
        _verify_support_membership_hashes(index, class_members)
        if len(excluded) != 1072 or len(ridge) != 108 or candidate_segments != 634 or len(touching) != 1075 or len(touching & ridge) != 3:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "B6N8N_BOUNDARY_EXCLUSION_REPLAY_MISMATCH")
        support_counts = {name: len(ids) for name, ids in class_members.items()}
        if (native_count, admitted_count, continental_count, ocean_count) != (64800, 63620, 14258, 49362):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "B6N8N_SUPPORT_CARDINALITY_MISMATCH")
        if support_counts != {
            "CONTINENTAL_COLD_STABLE": 7834,
            "CONTINENTAL_NORMAL": 5143,
            "CONTINENTAL_HOT_EXTENDED": 1281,
            "OCEAN_POSITIVE_AGE_ADMITTED": 49362,
            "UNRESOLVED_POSITIVE_AGE_OCEAN": 1072,
            "ZERO_AGE_RIDGE": 108,
        }:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "B6N8N_CLASS_COUNTS_MISMATCH")
        if ledger["cardinality"]["exactly_one"] != admitted_count or any(
            ledger["cardinality"][key] != 0 for key in ("zero", "duplicate_ids", "multiple_conflicting", "multiple_equivalent", "unknown", "overlap")
        ):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "B6N8N_BINDING_CARDINALITY_MISMATCH")
        return PreflightResult(
            native_count, admitted_count, continental_count, ocean_count,
            len(excluded), len(ridge), 0, 0, 0, candidate_segments,
            len(touching), len(touching & ridge), plan_digest.hexdigest(), False, False,
        )
    except InitializerError:
        raise
    except (OSError, KeyError, TypeError, ValueError, IndexError) as exc:
        raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"PREFLIGHT_INPUT_INVALID:{exc}") from exc


def _validate_binding(binding: ColumnBinding) -> None:
    if not isinstance(binding, ColumnBinding):
        raise InitializerError(FailureCode.INVALID_INPUT, "COLUMN_BINDING_TYPE_INVALID")
    if binding.support_class in ("UNRESOLVED_POSITIVE_AGE_OCEAN", "ZERO_AGE_RIDGE"):
        raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "EXCLUDED_SUPPORT_NOT_INITIALIZABLE")
    admitted = binding.support_class.startswith("CONTINENTAL_") or binding.support_class == "OCEAN_POSITIVE_AGE_ADMITTED"
    if not admitted:
        raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "SUPPORT_CLASS_UNKNOWN")
    if not binding.support_id or not (NATIVE_ID.fullmatch(binding.support_id) or FIXTURE_ID.fullmatch(binding.support_id)):
        raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "SUPPORT_ID_NOT_IN_ADMITTED_OR_FIXTURE_NAMESPACE")
    if binding.initializer_family != INITIALIZER_FAMILY:
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "INITIALIZER_FAMILY_NOT_AUTHORIZED")
    if binding.binding_status != "EXACTLY_ONE_INITIALIZER_BINDING":
        raise InitializerError(FailureCode.MISSING_BINDING, "BINDING_STATUS_NOT_EXACT")
    if not binding.geometry_reference or not binding.surface_datum or not binding.boundary_scenario_id:
        raise InitializerError(FailureCode.MISSING_BINDING, "GEOMETRY_DATUM_OR_SCENARIO_MISSING")
    if binding.surface_datum != "LOCAL_MODEL_SURFACE_Z0":
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "VERTICAL_DATUM_NOT_AUTHORIZED")
    if binding.physical_lab_depth_m is not None:
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "PHYSICAL_LAB_MUST_NOT_BE_INFERRED")
    if not (math.isfinite(binding.crust_depth_m) and math.isfinite(binding.model_base_depth_m)
            and 0 < binding.crust_depth_m < binding.model_base_depth_m):
        raise InitializerError(FailureCode.INVALID_INPUT, "GEOMETRY_ORDER_OR_LAYER_THICKNESS_INVALID")
    if not math.isfinite(binding.t0_world_age_ma) or binding.t0_world_age_ma != T0_WORLD_AGE_MA:
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "WORLD_TIME_MUST_BE_GOVERNED_T0")
    if not math.isfinite(binding.gravity_m_s2) or binding.gravity_m_s2 != 9.82:
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "GRAVITY_NOT_GOVERNED_VALUE")
    if not math.isfinite(binding.surface_temperature_k) or binding.surface_temperature_k != binding.hwr_model.t0_k:
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "SURFACE_TEMPERATURE_AUTHORITY_MISMATCH")
    if dict(binding.units) != REQUIRED_UNITS:
        raise InitializerError(FailureCode.INVALID_INPUT, "UNIT_CONTRACT_MISMATCH")
    if len(binding.material_role_sequence) != 2:
        raise InitializerError(FailureCode.MISSING_BINDING, "MATERIAL_ROLE_SEQUENCE_INVALID")
    expected_roles = (
        ("CONTINENTAL_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE")
        if binding.support_class.startswith("CONTINENTAL_") else
        ("OCEANIC_CRUST_REFERENCE", "LITHOSPHERIC_MANTLE_REFERENCE")
    )
    if binding.material_role_sequence != expected_roles or (binding.crust.role_id, binding.mantle.role_id) != expected_roles:
        raise InitializerError(FailureCode.MISSING_BINDING, "DISCRETE_MATERIAL_ROLE_BINDING_MISMATCH")
    if binding.support_class.startswith("CONTINENTAL_"):
        if binding.model_base_semantics != "AUTHORED_TOTAL_THERMAL_THICKNESS_NOT_PHYSICAL_LAB":
            raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "CONTINENTAL_BASE_SEMANTICS_INVALID")
        if binding.physical_ocean_age_ma is not None or binding.surface_heat_flow_w_m2 is None:
            raise InitializerError(FailureCode.MISSING_BINDING, "CONTINENTAL_BOUNDARY_BINDING_MISSING")
        if binding.boundary_scenario_id != "CONTINENTAL_AUTHORED_Q_AND_T0_REFERENCE_V1":
            raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "CONTINENTAL_SCENARIO_UNSUPPORTED")
    else:
        if binding.model_base_semantics != "HWR_FINITE_PLATE_BASE_NOT_PHYSICAL_LAB":
            raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "OCEAN_BASE_SEMANTICS_INVALID")
        if binding.physical_ocean_age_ma is None or not math.isfinite(binding.physical_ocean_age_ma) or binding.physical_ocean_age_ma <= 0:
            raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "POSITIVE_AGE_OCEAN_SUPPORT_REQUIRED")
        if not 1.1491667412337465 <= binding.physical_ocean_age_ma <= 160.0:
            raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "OCEAN_AGE_OUTSIDE_GOVERNED_DOMAIN")
        if binding.boundary_scenario_id != "HWR2_POSITIVE_AGE_BOUNDARY_V1":
            raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "OCEAN_SCENARIO_UNSUPPORTED")
        if not math.isclose(binding.model_base_depth_m, binding.hwr_model.zp_m, rel_tol=0.0, abs_tol=1e-9):
            raise InitializerError(FailureCode.MISSING_BINDING, "HWR_BASE_ZP_PAIR_MISMATCH")
    if binding.crust.source_term_reference != "A_C" or binding.mantle.source_term_reference != "A_M":
        raise InitializerError(FailureCode.MISSING_BINDING, "SOURCE_TERM_ROLE_BINDING_MISMATCH")
    if binding.mantle.alpha_k_1 is None or "alpha" not in binding.mantle.bounds:
        raise InitializerError(FailureCode.MISSING_BINDING, "MANTLE_ALPHA_BINDING_MISSING")
    if binding.mantle.material.k != binding.hwr_model.k_w_m_k or binding.mantle.material.rho != binding.hwr_model.rho_kg_m3 or binding.mantle.material.cp != binding.hwr_model.cp_j_kg_k:
        raise InitializerError(FailureCode.MISSING_BINDING, "HWR_MANTLE_TUPLE_COHERENCE_MISMATCH")
    binding.hwr_model.validate()
    _validate_layer_binding(binding.crust)
    _validate_layer_binding(binding.mantle)
    for label, mapping in (("CONFIGURATION_IDENTITIES", binding.configuration_identities), ("SUPPORT_LINEAGE", binding.support_lineage), ("UNCERTAINTY", binding.uncertainty)):
        if not mapping or any(not isinstance(k, str) or not k or v is None for k, v in mapping.items()):
            raise InitializerError(FailureCode.MISSING_BINDING, f"{label}_MISSING")
        try:
            _canonical_json(dict(mapping))
        except (TypeError, ValueError) as exc:
            raise InitializerError(FailureCode.INVALID_INPUT, f"{label}_NOT_SERIALIZABLE") from exc
    for key, value in binding.configuration_identities.items():
        if key.endswith("sha256") and (not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)):
            raise InitializerError(FailureCode.INVALID_INPUT, "CONFIGURATION_HASH_INVALID")
    if binding.support_class.startswith("CONTINENTAL_"):
        if not math.isfinite(float(binding.surface_heat_flow_w_m2)) or float(binding.surface_heat_flow_w_m2) <= 0:
            raise InitializerError(FailureCode.INVALID_INPUT, "CONTINENTAL_SURFACE_FLUX_INVALID")
    elif binding.surface_heat_flow_w_m2 is not None:
        expected_q = binding.hwr_model.flux(binding.physical_ocean_age_ma)
        if not math.isclose(float(binding.surface_heat_flow_w_m2), expected_q, rel_tol=0.0, abs_tol=1e-12):
            raise InitializerError(FailureCode.INVALID_INPUT, "OCEAN_FLUX_DOES_NOT_MATCH_HWR2")


def _validate_layer_binding(layer: LayerPropertyBinding) -> None:
    if not layer.tuple_reference or not layer.authority_reference or not layer.source_term_reference:
        raise InitializerError(FailureCode.MISSING_BINDING, "PROPERTY_TUPLE_REFERENCE_MISSING")
    try:
        layer.material.validate()
    except ValueError as exc:
        raise InitializerError(FailureCode.INVALID_INPUT, str(exc)) from exc
    if layer.alpha_k_1 is None and "alpha" in layer.bounds:
        raise InitializerError(FailureCode.MISSING_BINDING, "PROPERTY_VALUE_MISSING:alpha")
    values = {
        "k": layer.material.k, "rho": layer.material.rho,
        "Cp": layer.material.cp, "A_C" if layer.source_term_reference == "A_C" else "A_M": layer.material.radiogenic_w_m3,
    }
    if layer.alpha_k_1 is not None:
        values["alpha"] = layer.alpha_k_1
    for key, value in values.items():
        if not math.isfinite(value):
            raise InitializerError(FailureCode.INVALID_INPUT, f"PROPERTY_NONFINITE:{key}")
        if key in layer.bounds:
            low, high = layer.bounds[key]
            if not (math.isfinite(low) and math.isfinite(high) and low <= value <= high):
                raise InitializerError(FailureCode.INVALID_INPUT, f"PROPERTY_OUTSIDE_AUTHORITY:{key}")
        else:
            raise InitializerError(FailureCode.MISSING_BINDING, f"PROPERTY_BOUNDS_MISSING:{key}")
    if layer.source_term_reference not in ("A_C", "A_M"):
        raise InitializerError(FailureCode.MISSING_BINDING, "SOURCE_TERM_REFERENCE_UNKNOWN")
    derived = _derive_kappa(layer)
    if not math.isfinite(layer.kappa_reference_m2_s) or not math.isclose(
        derived, layer.kappa_reference_m2_s, rel_tol=1e-14, abs_tol=0.0,
    ):
        raise InitializerError(FailureCode.MISSING_BINDING, "KAPPA_NOT_DERIVED_FROM_SAME_TUPLE")


def _derive_kappa(layer: LayerPropertyBinding) -> float:
    layer.material.validate()
    return layer.material.k / (layer.material.rho * layer.material.cp)


def _make_result(plan: InitializerPlan, column: Column) -> InitializerResult:
    binding = plan.binding
    segments: list[ProfileSegment] = []
    if column.kind == "CONTINENT":
        for layer, role in zip(column.profile_coefficients, binding.material_role_sequence):
            z0, z1, c2, c1, c0 = map(float, layer)
            segments.append(ProfileSegment(z0, z1, "LOCAL_QUADRATIC_C2_C1_C0", (c2, c1, c0), role))
    else:
        for layer, role in zip(column.profile_coefficients, binding.material_role_sequence):
            z0, z1, a, b, c, d = map(float, layer)
            segments.append(ProfileSegment(z0, z1, "NORMALIZED_CUBIC_HERMITE_A_B_C_D", (a, b, c, d), role))
    provenance = {
        "recipe": INITIALIZER_RECIPE,
        "plan_identity_sha256": plan.plan_identity_sha256,
        "authority_references": [binding.crust.authority_reference, binding.mantle.authority_reference],
    }
    result = InitializerResult(
        support_id=binding.support_id,
        surface_datum=binding.surface_datum,
        world_age_ma=binding.t0_world_age_ma,
        physical_ocean_age_ma=binding.physical_ocean_age_ma,
        initializer_family=binding.initializer_family,
        scenario_id=binding.boundary_scenario_id,
        geometry_reference=binding.geometry_reference,
        model_base_semantics=binding.model_base_semantics,
        model_base_depth_m=binding.model_base_depth_m,
        crust_depth_m=binding.crust_depth_m,
        thermal_lab_depth_m=column.lab_m,
        thermal_lab_temperature_k=column.lab_temperature_k,
        moho_temperature_k=column.moho_temperature_k,
        surface_heat_flow_w_m2=column.q_surface_w_m2,
        effective_column_rate_k_s=column.transient_rate_k_s,
        layer_roles=binding.material_role_sequence,
        property_tuple_references=(binding.crust.tuple_reference, binding.mantle.tuple_reference),
        source_term_references=(binding.crust.source_term_reference, binding.mantle.source_term_reference),
        derived_kappa_m2_s=(plan.crust_kappa_m2_s, plan.mantle_kappa_m2_s),
        configuration_identities=tuple(sorted(binding.configuration_identities.items())),
        numerical_configuration={
            "surface_temperature_k": binding.surface_temperature_k,
            "gravity_m_s2": binding.gravity_m_s2,
            "hwr2": asdict(binding.hwr_model),
        },
        support_lineage=tuple(sorted(binding.support_lineage.items())),
        uncertainty=binding.uncertainty,
        provenance=provenance,
        segments=tuple(segments),
        validation_status="SYNTHETIC_FIXTURE_NUMERICALLY_VALIDATED",
        result_sha256="",
        _layer_materials=(binding.crust, binding.mantle),
    )
    digest = hashlib.sha256(result.serialize()).hexdigest()
    result = replace(result, result_sha256=digest)
    validate_initializer_result(result)
    return result


def validate_initializer_result(result: InitializerResult) -> None:
    """Validate candidate output structure and its canonical-byte identity."""
    if not isinstance(result, InitializerResult):
        raise InitializerError(FailureCode.INVALID_INPUT, "INITIALIZER_RESULT_TYPE_INVALID")
    if not FIXTURE_ID.fullmatch(result.support_id):
        raise InitializerError(FailureCode.UNAUTHORIZED_SUPPORT, "RESULT_SUPPORT_NOT_SYNTHETIC")
    if (result.initializer_family != INITIALIZER_FAMILY or result.world_age_ma != T0_WORLD_AGE_MA
            or result.surface_datum != "LOCAL_MODEL_SURFACE_Z0"):
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "RESULT_IDENTITY_OR_TIME_INVALID")
    if result.validation_status != "SYNTHETIC_FIXTURE_NUMERICALLY_VALIDATED":
        raise InitializerError(FailureCode.INVALID_INPUT, "RESULT_VALIDATION_STATUS_INVALID")
    if (result.model_base_semantics == "PHYSICAL_LAB"
            or ("PHYSICAL_LAB" in result.model_base_semantics
                and not result.model_base_semantics.endswith("NOT_PHYSICAL_LAB"))):
        raise InitializerError(FailureCode.UNSUPPORTED_CONFIGURATION, "MODEL_BASE_MISLABELED_AS_PHYSICAL_LAB")
    if len(result.segments) != 2 or len(result.layer_roles) != 2:
        raise InitializerError(FailureCode.INVALID_INPUT, "RESULT_LAYER_COUNT_INVALID")
    first, second = result.segments
    if (first.z0_m != 0.0 or first.z1_m != result.crust_depth_m
            or second.z0_m != result.crust_depth_m or second.z1_m != result.thermal_lab_depth_m
            or not result.crust_depth_m < result.thermal_lab_depth_m):
        raise InitializerError(FailureCode.INVALID_INPUT, "RESULT_GEOMETRY_INVALID")
    if (first.material_role, second.material_role) != result.layer_roles:
        raise InitializerError(FailureCode.MISSING_BINDING, "RESULT_DISCRETE_ROLE_BINDING_INVALID")
    values = (
        result.world_age_ma, result.model_base_depth_m, result.crust_depth_m,
        result.thermal_lab_depth_m, result.thermal_lab_temperature_k,
        result.moho_temperature_k, result.surface_heat_flow_w_m2,
        *result.derived_kappa_m2_s,
        *(coefficient for segment in result.segments for coefficient in segment.coefficients),
    )
    if not all(math.isfinite(value) for value in values):
        raise InitializerError(FailureCode.NUMERICAL_FAILURE, "RESULT_NONFINITE")
    if result.effective_column_rate_k_s is not None and not math.isfinite(result.effective_column_rate_k_s):
        raise InitializerError(FailureCode.NUMERICAL_FAILURE, "RESULT_RATE_NONFINITE")
    if len(result.property_tuple_references) != 2 or any(not ref for ref in result.property_tuple_references):
        raise InitializerError(FailureCode.MISSING_BINDING, "RESULT_TUPLE_PROVENANCE_MISSING")
    if not result.provenance or not result.uncertainty:
        raise InitializerError(FailureCode.MISSING_BINDING, "RESULT_PROVENANCE_OR_UNCERTAINTY_MISSING")
    if hashlib.sha256(result.serialize()).hexdigest() != result.result_sha256:
        raise InitializerError(FailureCode.INVALID_INPUT, "RESULT_IDENTITY_HASH_MISMATCH")


def _result_payload(result: InitializerResult) -> dict[str, Any]:
    return {
        "schema": "ARCANA_R6_T0_THERMAL_INITIALIZER_CANDIDATE_V1",
        "support_id": result.support_id,
        "time": {"selector": "T0", "world_age_ma": result.world_age_ma,
                 "physical_ocean_age_ma": result.physical_ocean_age_ma},
        "initializer_family": result.initializer_family,
        "scenario_id": result.scenario_id,
        "geometry_reference": result.geometry_reference,
        "model_base_semantics": result.model_base_semantics,
        "model_base_depth_m": result.model_base_depth_m,
        "crust_depth_m": result.crust_depth_m,
        "thermal_lab_depth_m": result.thermal_lab_depth_m,
        "thermal_lab_temperature_k": result.thermal_lab_temperature_k,
        "moho_temperature_k": result.moho_temperature_k,
        "surface_heat_flow_w_m2": result.surface_heat_flow_w_m2,
        "effective_column_rate_k_s": result.effective_column_rate_k_s,
        "vertical_coordinate": {
            "datum": result.surface_datum, "positive_direction": "DOWNWARD",
            "units": "m", "representation": "ANALYTIC_PIECEWISE_SEGMENTS_NO_SELECTED_PRODUCTION_GRID",
        },
        "segments": [asdict(segment) for segment in result.segments],
        "material_roles": list(result.layer_roles),
        "property_tuple_references": list(result.property_tuple_references),
        "material_property_bindings": [
            _layer_property_payload(layer) for layer in result._layer_materials
        ],
        "derived_kappa_m2_s": list(result.derived_kappa_m2_s),
        "source_term_references": list(result.source_term_references),
        "configuration_identities": dict(result.configuration_identities),
        "numerical_configuration": result.numerical_configuration,
        "support_lineage": dict(result.support_lineage),
        "uncertainty": result.uncertainty,
        "provenance": result.provenance,
        "validation_status": result.validation_status,
        "canonical_publication": False,
    }


def _layer_property_payload(layer: LayerPropertyBinding) -> dict[str, Any]:
    return {
        "role_id": layer.role_id,
        "tuple_reference": layer.tuple_reference,
        "source_term_reference": layer.source_term_reference,
        "k_w_m_k": layer.material.k,
        "rho_kg_m3": layer.material.rho,
        "Cp_j_kg_k": layer.material.cp,
        "source_w_m3": layer.material.radiogenic_w_m3,
        "alpha_k_1": layer.alpha_k_1,
        "derived_kappa_m2_s": _derive_kappa(layer),
        "authority_reference": layer.authority_reference,
        "uncertainty": layer.uncertainty,
    }


def _reconstruct_ocean_exclusions(domain, age, segments, selected_ids):
    excluded: set[str] = set()
    touching: set[str] = set()
    candidates = 0
    rows, columns = domain.shape
    for segment in segments:
        edge = segment["parent_grid_edge"]
        row, column, axis = int(edge["row"]), int(edge["column"]), edge["axis"]
        if axis == "EAST":
            adjacent = ((row, column), (row, (column + 1) % columns))
        elif axis == "NORTH":
            adjacent = ((row, column), (row + 1, column))
        else:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "BOUNDARY_EDGE_AXIS_UNKNOWN")
        (r0, c0), (r1, c1) = adjacent
        if not (0 <= r0 < rows and 0 <= r1 < rows and 0 <= c0 < columns and 0 <= c1 < columns):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, "BOUNDARY_EDGE_OUTSIDE_GRID")
        if (int(domain[r0, c0]) == 1 and int(domain[r1, c1]) == 1
                and float(segment["relative_normal_velocity_m_per_year"]) > 0
                and segment["boundary_id"] not in selected_ids):
            candidates += 1
            for r, c in adjacent:
                ident = _cell_id(r, c)
                if float(age[r, c]) > 0:
                    excluded.add(ident)
                    touching.add(ident)
                elif float(age[r, c]) == 0:
                    touching.add(ident)
    return excluded, touching, candidates


def _verify_support_membership_hashes(index, memberships):
    for entry in index["support_classes"]:
        ids = memberships[entry["class"]]
        digest = hashlib.sha256("".join(value + "\n" for value in sorted(ids)).encode("utf-8")).hexdigest()
        if len(ids) != entry["count"] or digest != entry["support_id_sha256"]:
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"SUPPORT_MEMBERSHIP_MISMATCH:{entry['class']}")


def _validate_registry_role(registry, role_id):
    role = registry["roles"][role_id]
    props = role["properties"]
    for name in ("k", "rho", "Cp"):
        entry = props[name]
        nominal = float(entry["nominal"])
        bounds = entry.get("sensitivity_range", entry.get("range"))
        if not math.isfinite(nominal) or not bounds or not float(bounds[0]) <= nominal <= float(bounds[1]):
            raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"TUPLE_PROPERTY_INVALID:{role_id}:{name}")
    expected = float(props["k"]["nominal"]) / (float(props["rho"]["nominal"]) * float(props["Cp"]["nominal"]))
    if not math.isclose(expected, float(role["kappa_nominal_m2_s"]), rel_tol=1e-14, abs_tol=0.0):
        raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"KAPPA_TUPLE_INCOHERENT:{role_id}")
    expected_source = "A_C" if role_id.endswith("CRUST_REFERENCE") else "A_M"
    if expected_source not in props:
        raise InitializerError(FailureCode.UNKNOWN_AUTHORITY, f"SOURCE_TERM_TUPLE_MISSING:{role_id}")


def _registry_role_identity(registry, role_id):
    return f"B6N8N_PROPERTY_TUPLE:{role_id}:{_sha256_bytes(_canonical_json(registry['roles'][role_id]))}"


def _role_kappa(registry, role_id):
    role = registry["roles"][role_id]
    props = role["properties"]
    return float(props["k"]["nominal"]) / (float(props["rho"]["nominal"]) * float(props["Cp"]["nominal"]))


def _hwr_from_authority(config):
    hwr = config["hwr2"]
    values = {entry["name"]: float(entry["value"]) for entry in hwr["parameters"]}
    controls = config["thermal_numerical_controls"]
    model = HWR2(
        k_w_m_k=values["k"], rho_kg_m3=values["rho_m"], cp_j_kg_k=values["Cp"],
        tb_k=values["Tb"], t0_k=values["T0"], zp_m=values["zp"],
        n_modes=int(controls["fourier_modes"]),
        convergence_tolerance=float(controls["fourier_relative_tolerance"]),
    )
    model.validate()
    return model


def _hwr_value(registry, name):
    return float(registry["boundary_refs"]["ocean_HWR_existing_boundary_parameters"][name]["value"])


def _cell_id(row, column):
    return f"R6G1D-R{row:03d}-C{column:03d}"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")
