"""Owner-bound, deterministic ShellSet input package for PRE_ORBDATA."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .pre_orbdata_heat_flow import HWR2
from .pre_orbdata_thermal_column import (
    Column, LayerMaterial, continental_column, ocean_column,
)
from .repository_context import canonical_text_sha256, resolve_external_payload_path
from .shellset_mesh.adapter import load_canonical_mesh

MODE = "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1"
SCHEMA = "arcana_worldsim.r6.shellset_owner_bound_runtime.v1"
DATA_NAME = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
MANIFEST_NAME = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"
BRANCH_CODES = {
    "CONTINENTAL_AUTHORED_REFERENCE": 1,
    "GOVERNED_RIDGE_BOUNDARY": 2,
    "AUTHORIZED_POSITIVE_AGE_OCEAN": 3,
}
BRANCH_NAMES = {value: key for key, value in BRANCH_CODES.items()}
MATERIAL_CODE = 1  # R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1
CRUST_CODES = {"CONTINENTAL_CRUST_REFERENCE": 1, "OCEANIC_CRUST_REFERENCE": 2}

# Each row is whitespace-delimited ASCII. Fields use a fixed order recorded in
# the manifest; nullable values have an explicit present flag and a finite 0.0
# storage value, never NaN/Inf or an overloaded physical sentinel.
FIELDS = [
    "node_id", "owner_row", "owner_column", "owner_domain_id", "incident_domain_mask",
    "mixed_support", "thermal_class_present", "owner_thermal_class_id", "runtime_branch_code",
    "physical_age_present", "physical_age_ma", "effective_age_present", "effective_age_ma",
    "surface_temperature_k", "surface_heat_flow_w_m2", "crust_thickness_m",
    "mantle_lithosphere_thickness_m", "lab_depth_m", "moho_temperature_k", "moho_flux_w_m2",
    "lab_temperature_k", "lab_flux_w_m2", "transient_rate_present", "transient_rate_k_s",
    "material_configuration_code", "crust_material_code", "mantle_material_code",
    "crust_density_kg_m3", "crust_conductivity_w_m_k", "crust_expansivity_k_1",
    "crust_heat_production_w_m3", "crust_cp_j_kg_k", "mantle_density_kg_m3",
    "mantle_conductivity_w_m_k", "mantle_expansivity_k_1", "mantle_heat_production_w_m3",
    "mantle_cp_j_kg_k", "rho_asthenosphere_kg_m3", "rho_water_kg_m3",
    "layer1_z0_m", "layer1_z1_m", "layer1_c3_k_m3", "layer1_c2_k_m2",
    "layer1_c1_k_m", "layer1_c0_k", "layer2_z0_m", "layer2_z1_m",
    "layer2_c3_k_m3", "layer2_c2_k_m2", "layer2_c1_k_m", "layer2_c0_k",
]
TOL_T = 2e-7
TOL_Q = 2e-12


@dataclass(frozen=True)
class RuntimeNode:
    values: tuple[float | int, ...]

    def line(self) -> str:
        if len(self.values) != len(FIELDS):
            raise ValueError("RUNTIME_RECORD_FIELD_COUNT_MISMATCH")
        out = [str(int(self.values[0]))]
        for value in self.values[1:]:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("RUNTIME_RECORD_NONFINITE_VALUE")
            out.append(format(number, ".17e"))
        return " ".join(out)


def _poly_from_column(column: Column) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if len(column.profile_coefficients) != 2:
        raise ValueError("RUNTIME_COLUMN_LAYER_COUNT_INVALID")
    converted = []
    for layer in column.profile_coefficients:
        if column.kind == "CONTINENT":
            if len(layer) != 5:
                raise ValueError("CONTINENT_PROFILE_COEFFICIENT_SHAPE_INVALID")
            z0, z1, c2, c1, c0 = map(float, layer)
            c3 = 0.0
        else:
            if len(layer) != 6:
                raise ValueError("OCEAN_PROFILE_COEFFICIENT_SHAPE_INVALID")
            z0, z1, a, b, c, d = map(float, layer)
            dx = z1 - z0
            if not math.isfinite(dx) or dx <= 0:
                raise ValueError("RUNTIME_PROFILE_LAYER_THICKNESS_INVALID")
            c3, c2, c1, c0 = a / dx**3, b / dx**2, c / dx, d
        vals = (z0, z1, c3, c2, c1, c0)
        if not all(math.isfinite(v) for v in vals) or z1 <= z0:
            raise ValueError("RUNTIME_PROFILE_COEFFICIENT_INVALID")
        converted.append(vals)
    return converted[0], converted[1]


def _temperature(poly: tuple[float, ...], z: float) -> float:
    z0, _z1, c3, c2, c1, c0 = poly
    x = z - z0
    return ((c3 * x + c2) * x + c1) * x + c0


def _flux(poly: tuple[float, ...], z: float, conductivity: float) -> float:
    z0, _z1, c3, c2, c1, _c0 = poly
    x = z - z0
    return conductivity * ((3.0 * c3 * x + 2.0 * c2) * x + c1)


def validate_column(column: Column, q_surface: float, surface_t: float,
                    crust_k: float, mantle_k: float) -> tuple[tuple[float, ...], tuple[float, ...]]:
    p1, p2 = _poly_from_column(column)
    hc, lab = column.crust_m, column.lab_m
    if not (math.isfinite(hc) and math.isfinite(lab) and 0 < hc < lab):
        raise ValueError("RUNTIME_COLUMN_GEOMETRY_INVALID")
    checks = (
        (p1[0], 0.0, 1e-10, "LAYER1_MUST_START_AT_SURFACE"),
        (p1[1], hc, 1e-8, "LAYER1_MUST_END_AT_MOHO"),
        (p2[0], hc, 1e-8, "LAYER2_MUST_START_AT_MOHO"),
        (p2[1], lab, 1e-8, "LAYER2_MUST_END_AT_LAB"),
    )
    for actual, expected, tol, error in checks:
        if abs(actual - expected) > tol:
            raise ValueError(error)
    boundary_checks = (
        (_temperature(p1, 0), surface_t, TOL_T, "SURFACE_TEMPERATURE_MISMATCH"),
        (_flux(p1, 0, crust_k), q_surface, TOL_Q, "SURFACE_FLUX_MISMATCH"),
        (_temperature(p1, hc), column.moho_temperature_k, TOL_T, "MOHO_T_CRUST_MISMATCH"),
        (_temperature(p2, hc), column.moho_temperature_k, TOL_T, "MOHO_T_MANTLE_MISMATCH"),
        (_flux(p1, hc, crust_k), column.moho_flux_w_m2, TOL_Q, "MOHO_FLUX_CRUST_MISMATCH"),
        (_flux(p2, hc, mantle_k), column.moho_flux_w_m2, TOL_Q, "MOHO_FLUX_MANTLE_MISMATCH"),
        (_temperature(p2, lab), column.lab_temperature_k, TOL_T, "LAB_TEMPERATURE_MISMATCH"),
        (_flux(p2, lab, mantle_k), column.lab_flux_w_m2, TOL_Q, "LAB_FLUX_MISMATCH"),
    )
    for actual, expected, tol, error in boundary_checks:
        if not math.isfinite(actual) or abs(actual - expected) > tol:
            raise ValueError(error)
    return p1, p2


def _material_config(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads((root / "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json").read_text(encoding="utf-8"))
    props = config["thermal_properties"]
    density = config["density"]
    radio = config["radiogenic_heat"]
    def nominal(section: dict, key: str) -> float:
        return float(section[key]["nominal"])
    crusts = {
        "CONTINENTAL_CRUST_REFERENCE": LayerMaterial(
            nominal(props["continental_crust"], "k"), density["continental_crust"]["nominal"],
            nominal(props["continental_crust"], "Cp"), radio["continental_crust"]["nominal"]),
        "OCEANIC_CRUST_REFERENCE": LayerMaterial(
            nominal(props["oceanic_crust"], "k"), density["oceanic_crust"]["nominal"],
            nominal(props["oceanic_crust"], "Cp"), radio["oceanic_crust"]["nominal"]),
    }
    mantle = LayerMaterial(nominal(props["mantle"], "k"), density["lithospheric_mantle"]["nominal"],
                           nominal(props["mantle"], "Cp"), radio["mantle_lithosphere"]["nominal"])
    refs = {"rho_ast": float(density["asthenosphere"]["nominal"]),
            "rho_water": float(density["seawater"]["nominal"]),
            "surface_temperature_k": float(props["surface_temperature"]["nominal"]),
            "crust_alpha": {"CONTINENTAL_CRUST_REFERENCE": nominal(props["continental_crust"], "alpha"),
                            "OCEANIC_CRUST_REFERENCE": nominal(props["oceanic_crust"], "alpha")},
            "mantle_alpha": nominal(props["mantle"], "alpha"),
            "material_identity": str(config["identity"])}
    heat_config = json.loads((root / "R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json").read_text(encoding="utf-8"))
    hwr_values = {p["name"]: float(p["value"]) for p in heat_config["hwr2"]["parameters"]}
    controls = heat_config["thermal_numerical_controls"]
    refs["hwr_model"] = HWR2(k_w_m_k=hwr_values["k"], rho_kg_m3=hwr_values["rho_m"],
        cp_j_kg_k=hwr_values["Cp"], tb_k=hwr_values["Tb"], t0_k=hwr_values["T0"],
        zp_m=hwr_values["zp"], n_modes=int(controls["fourier_modes"]),
        convergence_tolerance=float(controls["fourier_relative_tolerance"]))
    if abs(refs["surface_temperature_k"] - refs["hwr_model"].t0_k) > 1e-12:
        raise ValueError("RUNTIME_SURFACE_TEMPERATURE_AUTHORITY_MISMATCH")
    return {"config": config, "crusts": crusts, "mantle": mantle}, refs


def _number(value: Any, name: str) -> float:
    if value is None:
        raise ValueError(f"RUNTIME_REQUIRED_OWNER_VALUE_MISSING:{name}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"RUNTIME_OWNER_VALUE_NONFINITE:{name}")
    return result


def _node_values(node: dict[str, Any], projection: dict[str, Any], materials: dict[str, Any],
                 refs: dict[str, Any], age: np.ndarray, domain: np.ndarray,
                 crust: np.ndarray, cont_total: np.ndarray, thermal_class: np.ndarray,
                 branch: np.ndarray, qcell: np.ndarray) -> RuntimeNode:
    node_id = int(node["node_id"])
    owner = node["numerical_owner_cell_row_col"]
    if not isinstance(owner, list) or len(owner) != 2:
        raise ValueError(f"RUNTIME_OWNER_MISSING:{node_id}")
    row, col = map(int, owner)
    own_domain = int(domain[row, col])
    branch_name = str(node["numerical_owner_runtime_branch"])
    branch_code = BRANCH_CODES.get(branch_name)
    if branch_code is None or branch_code != int(branch[row, col]):
        raise ValueError(f"RUNTIME_OWNER_BRANCH_MISMATCH:{node_id}")
    if own_domain != int(node["numerical_owner_domain_id"]):
        raise ValueError(f"RUNTIME_OWNER_DOMAIN_MISMATCH:{node_id}")
    if _number(qcell[row, col], "heat_flow") != float(projection["heat_flow_w_m2"][node_id - 1]):
        raise ValueError(f"RUNTIME_OWNER_Q_MISMATCH:{node_id}")
    if (branch_code == 1 and own_domain == 1) or (branch_code in (2, 3) and own_domain != 1):
        raise ValueError(f"RUNTIME_OWNER_DOMAIN_BRANCH_CONFLICT:{node_id}")
    if node["numerical_owner_material_configuration_binding"] not in CRUST_CODES:
        raise ValueError(f"RUNTIME_MATERIAL_BINDING_MISSING:{node_id}")
    crust_name = node["numerical_owner_material_configuration_binding"]
    cm = materials["crusts"][crust_name]
    mm = materials["mantle"]
    h_crust = _number(crust[row, col], "crust_thickness_m")
    q = float(projection["heat_flow_w_m2"][node_id - 1])
    physical_age_present = branch_code in (2, 3)
    physical_age = _number(age[row, col], "physical_age_ma") if physical_age_present else 0.0
    effective_present = branch_code == 2
    if branch_code == 1:
        total = _number(cont_total[row, col], "continental_total_lithosphere_m")
        column = _cached_column(branch_code, physical_age, q, h_crust, total, cm, mm, refs["hwr_model"])
    elif branch_code == 2:
        if physical_age != 0.0 or q != 0.3:
            raise ValueError(f"RUNTIME_RIDGE_AUTHORITY_MISMATCH:{node_id}")
        column = _cached_column(branch_code, physical_age, q, h_crust, 0.0, cm, mm, refs["hwr_model"])
    else:
        if physical_age <= 0.0:
            raise ValueError(f"RUNTIME_OCEAN_AGE_INVALID:{node_id}")
        column = _cached_column(branch_code, physical_age, q, h_crust, 0.0, cm, mm, refs["hwr_model"])
    p1, p2 = validate_column(column, q, refs["surface_temperature_k"], cm.k, mm.k)
    age_eff = float(column.effective_age_ma) if effective_present else 0.0
    rate_present = column.transient_rate_k_s is not None
    rate = float(column.transient_rate_k_s) if rate_present else 0.0
    incidents = node["incident_physical_domain_ids"]
    mask = sum(1 << (int(v) - 1) for v in incidents)
    mixed = bool(node["mixed_physical_support"])
    if mixed != (len(incidents) > 1):
        raise ValueError(f"RUNTIME_MIXED_SUPPORT_INCONSISTENT:{node_id}")
    values: list[int | float] = [
        node_id, row, col, own_domain, mask, int(mixed), int(branch_code == 1),
        (int(_number(thermal_class[row, col], "thermal_class")) if branch_code == 1 else 0),
        branch_code, int(physical_age_present), physical_age, int(effective_present), age_eff,
        float(refs["surface_temperature_k"]), q, column.crust_m, column.mantle_m, column.lab_m,
        column.moho_temperature_k, column.moho_flux_w_m2, column.lab_temperature_k, column.lab_flux_w_m2,
        int(rate_present), rate, MATERIAL_CODE, CRUST_CODES[crust_name], 1,
        cm.rho, cm.k, float(refs["crust_alpha"][crust_name]), cm.radiogenic_w_m3, cm.cp,
        mm.rho, mm.k, float(refs["mantle_alpha"]), mm.radiogenic_w_m3, mm.cp,
        float(refs["rho_ast"]), float(refs["rho_water"]), *p1, *p2,
    ]
    if len(values) != len(FIELDS):
        raise ValueError("RUNTIME_RECORD_FIELD_COUNT_MISMATCH")
    return RuntimeNode(tuple(values))


@lru_cache(maxsize=50_000)
def _cached_column(branch: int, age: float, q: float, crust_m: float, total_m: float,
                   crust_material: LayerMaterial, mantle_material: LayerMaterial,
                   model: HWR2) -> Column:
    """Memoize identical owner-cell inputs; delegate all calculations to the governed solver."""
    if branch == 1:
        return continental_column(q_surface=q, crust_m=crust_m, total_lithosphere_m=total_m,
                                  crust=crust_material, mantle=mantle_material, model=model)
    if branch == 2:
        return ocean_column(age_ma=0.0, crust_m=crust_m, q_surface=q, ridge=True,
                            crust=crust_material, model=model)
    if branch == 3:
        return ocean_column(age_ma=age, crust_m=crust_m, q_surface=q, ridge=False,
                            crust=crust_material, model=model)
    raise ValueError("RUNTIME_BRANCH_CODE_UNSUPPORTED")


def materialize(root: Path) -> tuple[dict[str, Any], bytes]:
    root = root.resolve()
    projection = json.loads((root / "R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json").read_text(encoding="utf-8"))
    if projection.get("node_count") != 64_442 or projection.get("node_unknown_count") != 0:
        raise ValueError("FEG_PROJECTION_NOT_COMPLETE")
    if projection.get("deterministic_numerical_owner_count") != 64_442:
        raise ValueError("FEG_PROJECTION_OWNER_COUNT_INVALID")
    if projection.get("projection_rule") != "LEXICOGRAPHIC_FIRST_INCIDENT_CELL":
        raise ValueError("FEG_PROJECTION_RULE_MISMATCH")
    replay = dict(projection)
    claimed_replay = replay.pop("replay_sha256", None)
    actual_replay = hashlib.sha256(json.dumps(replay, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if claimed_replay != actual_replay:
        raise ValueError("FEG_PROJECTION_REPLAY_HASH_MISMATCH")

    fields = projection["cell_owner_source_fields"]
    domain = np.asarray(fields["physical_crust_domain_id"], dtype=np.int64)
    age = np.asarray(fields["oceanic_lithosphere_age_ma"], dtype=np.float64)
    crust = np.asarray(fields["crustal_thickness_m"], dtype=np.float64)
    cont_total = np.asarray(fields["continental_reference_lithosphere_thickness_m"], dtype=np.float64)
    thermal_class = np.asarray(fields["continental_thermal_domain_id"], dtype=np.float64)
    qcell = np.asarray(projection["cell_heat_flow_w_m2"], dtype=np.float64)
    branch = np.asarray(projection["cell_source_branch_code"], dtype=np.int64)
    validity = np.asarray(projection["cell_validity_mask"], dtype=bool)
    if any(a.shape != tuple(projection["field_shape"]) for a in
           (domain, age, crust, cont_total, thermal_class, qcell, branch, validity)):
        raise ValueError("RUNTIME_CELL_SOURCE_SHAPE_MISMATCH")
    if not np.all(validity):
        raise ValueError("RUNTIME_CELL_SOURCE_INVALID")
    materials, refs = _material_config(root)
    lineages = projection["lineage"]
    if len(lineages) != 64_442:
        raise ValueError("RUNTIME_PROJECTION_LINEAGE_COUNT_INVALID")

    mesh = load_canonical_mesh(root)
    manifest_path = root / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
    partition = json.loads(manifest_path.read_text(encoding="utf-8"))
    partition_payload = resolve_external_payload_path(root, partition["payload"]["path"])

    rows: list[str] = [f"{MODE} {SCHEMA} 64442"]
    branch_counts = {name: 0 for name in BRANCH_CODES}
    mixed_count = 0
    for index, node in enumerate(lineages, 1):
        if int(node["node_id"]) != index:
            raise ValueError("RUNTIME_NODE_ORDER_INVALID")
        owner = node["numerical_owner_cell_row_col"]
        if not isinstance(owner, list) or len(owner) != 2:
            raise ValueError(f"RUNTIME_NUMERICAL_OWNER_NOT_REUSED:{index}")
        record = _node_values(node, projection, materials, refs, age, domain,
                              crust, cont_total, thermal_class, branch, qcell)
        rows.append(record.line())
        branch_name = BRANCH_NAMES[int(record.values[8])]
        branch_counts[branch_name] += 1
        mixed_count += bool(record.values[5])
    data_bytes = ("\n".join(rows) + "\n").encode("ascii")

    package_path = root / "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz"
    source_hashes = {
        "heat_flow_config_sha256": canonical_text_sha256(root / "R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_V1.json"),
        "material_config_sha256": canonical_text_sha256(root / "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json"),
        "thermal_column_implementation_sha256": canonical_text_sha256(root / "src/arcana_worldsim/r6/pre_orbdata_thermal_column.py"),
        "projection_implementation_sha256": canonical_text_sha256(root / "src/arcana_worldsim/r6/pre_orbddata_projection.py") if (root / "src/arcana_worldsim/r6/pre_orbddata_projection.py").exists() else canonical_text_sha256(root / "src/arcana_worldsim/r6/pre_orbdata_projection.py"),
        "runtime_package_implementation_sha256": canonical_text_sha256(Path(__file__)),
        "runtime_package_producer_sha256": canonical_text_sha256(root / "scripts/r6_pre_orbdata_materialize_shellset_runtime_package.py"),
        "t0_physical_package_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "vector_partition_sha256": hashlib.sha256(partition_payload.read_bytes()).hexdigest(),
        "feg_mesh_sha256": mesh.normalized_sha256,
        "feg_projection_replay_sha256": str(claimed_replay),
    }
    units = {}
    for field in FIELDS:
        if field == "node_id": units[field] = "1"
        elif field in {"owner_row", "owner_column", "owner_domain_id", "incident_domain_mask", "mixed_support",
                       "thermal_class_present", "owner_thermal_class_id", "runtime_branch_code",
                       "physical_age_present", "effective_age_present", "transient_rate_present",
                       "material_configuration_code", "crust_material_code", "mantle_material_code"}: units[field] = "1"
        elif field.endswith("_age_ma"): units[field] = "Ma"
        elif field.endswith("_c1_k_m"): units[field] = "K m-1"
        elif field.endswith("_c2_k_m2"): units[field] = "K m-2"
        elif field.endswith("_c3_k_m3"): units[field] = "K m-3"
        elif field.endswith("_m"): units[field] = "m"
        elif field.endswith("_temperature_k") or field.endswith("_c0_k"): units[field] = "K"
        elif field.endswith("_flux_w_m2") or field == "surface_heat_flow_w_m2": units[field] = "W m-2"
        elif field.endswith("_rate_k_s"): units[field] = "K s-1"
        elif field.endswith("_kg_m3"): units[field] = "kg m-3"
        elif field.endswith("_conductivity_w_m_k"): units[field] = "W m-1 K-1"
        elif field.endswith("_expansivity_k_1"): units[field] = "K-1"
        elif field.endswith("_heat_production_w_m3"): units[field] = "W m-3"
        elif field.endswith("_cp_j_kg_k"): units[field] = "J kg-1 K-1"
        else: units[field] = "1"
    manifest = {
        "schema": SCHEMA,
        "decision": "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_COMPLETE__SHELLSET_CONSUMER_PATCH_READY",
        "explicit_arcana_runtime_mode": MODE,
        "algorithm_identity": "R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING_CLOSED__CONFIG_V1_AND_IMPLEMENTATION_READY",
        "node_count": len(lineages), "known_count": len(lineages), "invalid_count": 0,
        "mixed_physical_support_count": mixed_count, "branch_counts": branch_counts,
        "numerical_ownership_rule": "LEXICOGRAPHIC_FIRST_INCIDENT_CANONICAL_CELL",
        "numerical_owner_authority": "NUMERICAL_RUNTIME_SUPPORT_ONLY; NOT_CANONICAL_NODE_GEOLOGY",
        "material_configuration_identity": refs["material_identity"],
        "material_configuration_code": MATERIAL_CODE,
        "runtime_data_filename": DATA_NAME,
        "runtime_data_sha256": hashlib.sha256(data_bytes).hexdigest(),
        "header": {"magic": MODE, "schema": SCHEMA, "node_count": 64_442},
        "field_order": FIELDS,
        "units": units,
        "numeric_format": "17 significant decimal digits, lowercase scientific notation, ASCII, LF",
        "nullable_encoding": "explicit present flag; absent value serialized as finite 0.0; no sentinel inference",
        "incident_physical_domain_encoding": "incident_domain_mask bit (domain_id-1); owner domain is runtime binding only",
        "profile_polynomial": "T(x)=c3*x^3+c2*x^2+c1*x+c0; x=z-z0; local physical depth in metres",
        "profile_validation": {"nodes_validated": len(lineages), "invalid_nodes": 0,
            "temperature_abs_tolerance_k": TOL_T, "flux_abs_tolerance_w_m2": TOL_Q,
            "checks": ["surface temperature/flux", "Moho temperature/flux continuity", "LAB temperature/flux", "layer bounds", "finite coefficients"]},
        "projection_source_lineage": projection["source_lineage"],
        "source_lineage": source_hashes,
        "projection_rule": projection["projection_rule"],
        "projection_replay_sha256": claimed_replay,
        "fail_closed_policy": "reject incomplete, inconsistent, nonfinite or unsupported owner-bound node state",
        "physical_authority_disclaimer": "runtime serialization support only; numerical owner does not assert canonical node geology or promote resolution",
        "preserved_gates": {"PRE_ORBDATA_ready": False, "OrbData_authorized": False,
            "OrbData_executed": False, "SHELLS_ready": False, "mechanics_authorized": False,
            "dt_selected": False, "t1_created": False, "forward_evolution_authorized": False},
    }
    return manifest, data_bytes


def write_package(root: Path) -> dict[str, Any]:
    manifest, data_bytes = materialize(root)
    data_path = root / DATA_NAME
    manifest_path = root / MANIFEST_NAME
    data_path.write_bytes(data_bytes)
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n",
                             encoding="utf-8", newline="\n")
    return manifest
