"""Read-only parent-cell, continental support and T0 section mapping for T-F2B.

The reader binds exact parent-cell identities to the verified vector partition
and B6N8-N field package. It is a noncanonical engineering adapter: it neither
publishes WORLD_HISTORY records nor assigns a geological boundary process.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .functional_development import materialize_admitted_continental_t0
from .plate_support_adapter import load_b5_sources
from .pre_orbdata_t0_initializer import preflight_admitted_bindings
from .repository_context import resolve_external_payload_path

GRID_ROWS = 180
GRID_COLUMNS = 360
CONTINENTAL_DOMAIN_IDS = frozenset((2, 3, 4, 5, 6))
CONTINENTAL_CLASS_BY_ID = {1: "CONTINENTAL_COLD_STABLE",
                           2: "CONTINENTAL_NORMAL",
                           3: "CONTINENTAL_HOT_EXTENDED"}
PLATE_PAIR = (5, 11)


class SpatialSupportError(ValueError):
    """Governed source identity or exact support mapping is invalid."""


@dataclass(frozen=True)
class EdgeCells:
    first: tuple[int, int]
    second: tuple[int, int]


def exact_face_plate_lookup(face_rows: Sequence[int], face_columns: Sequence[int],
                            face_plate_ids: Sequence[int], *,
                            rows: int = GRID_ROWS,
                            columns: int = GRID_COLUMNS) -> dict[tuple[int, int], int]:
    """Build a unique, complete zero-based parent-cell to plate-ID join."""
    if rows <= 0 or columns <= 0 or not (len(face_rows) == len(face_columns) == len(face_plate_ids)):
        raise SpatialSupportError("FACE_PARTITION_CARDINALITY_INVALID")
    result: dict[tuple[int, int], int] = {}
    for row_value, column_value, plate_value in zip(face_rows, face_columns, face_plate_ids):
        row, column, plate = int(row_value), int(column_value), int(plate_value)
        if not (0 <= row < rows and 0 <= column < columns) or plate < 0:
            raise SpatialSupportError("FACE_PARTITION_ID_OUTSIDE_GOVERNED_DOMAIN")
        key = (row, column)
        if key in result:
            raise SpatialSupportError("FACE_PARTITION_DUPLICATE_CELL_ID")
        result[key] = plate
    if len(result) != rows * columns:
        raise SpatialSupportError("FACE_PARTITION_INCOMPLETE")
    return result


def incident_cells(row: int, column: int, axis: str, *,
                   rows: int = GRID_ROWS,
                   columns: int = GRID_COLUMNS) -> EdgeCells:
    """Return the canonical cells on either side of EAST/NORTH grid edge."""
    if not (0 <= row < rows and 0 <= column < columns):
        raise SpatialSupportError("BOUNDARY_EDGE_OUTSIDE_PARENT_GRID")
    if axis == "EAST":
        return EdgeCells((row, column), (row, (column + 1) % columns))
    if axis == "NORTH" and row + 1 < rows:
        return EdgeCells((row, column), (row + 1, column))
    raise SpatialSupportError("BOUNDARY_EDGE_AXIS_OR_POLAR_ADJACENCY_INVALID")


def local_edge_frame(row: int, column: int, axis: str, radius_m: float
                     ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return unit position, grid-forward normal, and positive tangent at edge midpoint."""
    if not math.isfinite(radius_m) or radius_m <= 0:
        raise SpatialSupportError("PLANETARY_RADIUS_INVALID")
    if axis == "EAST":
        latitude = math.radians(-90.0 + row + 0.5)
        longitude = math.radians(-180.0 + column + 1.0)
    elif axis == "NORTH":
        latitude = math.radians(-90.0 + row + 1.0)
        longitude = math.radians(-180.0 + column + 0.5)
    else:
        raise SpatialSupportError("BOUNDARY_EDGE_AXIS_INVALID")
    radial = np.array((math.cos(latitude) * math.cos(longitude),
                       math.cos(latitude) * math.sin(longitude), math.sin(latitude)))
    east = np.array((-math.sin(longitude), math.cos(longitude), 0.0))
    north = np.array((-math.sin(latitude) * math.cos(longitude),
                      -math.sin(latitude) * math.sin(longitude), math.cos(latitude)))
    return radial, (east if axis == "EAST" else north), (north if axis == "EAST" else east)


def signed_boundary_velocity(*, row: int, column: int, axis: str,
                             first_plate: int, second_plate: int,
                             plate_a: int, plate_b: int,
                             euler_rad_per_year: Mapping[int, Sequence[float]],
                             radius_m: float) -> dict[str, Any]:
    """Compute v_b-v_a at the canonical edge midpoint and project into its frame."""
    if {first_plate, second_plate} != {plate_a, plate_b} or plate_a == plate_b:
        raise SpatialSupportError("PLATE_SIDE_ASSIGNMENT_MISMATCH")
    if plate_a not in euler_rad_per_year or plate_b not in euler_rad_per_year:
        raise SpatialSupportError("EULER_PLATE_RATE_UNKNOWN")
    radial, forward, tangent = local_edge_frame(row, column, axis, radius_m)
    # Grid-forward points from the first incident cell to the second.
    normal_ab = forward if first_plate == plate_a else -forward
    omega_a = np.asarray(euler_rad_per_year[plate_a], dtype=np.float64)
    omega_b = np.asarray(euler_rad_per_year[plate_b], dtype=np.float64)
    if omega_a.shape != (3,) or omega_b.shape != (3,) or not np.isfinite(omega_a).all() or not np.isfinite(omega_b).all():
        raise SpatialSupportError("EULER_VECTOR_INVALID")
    position_m = radial * radius_m
    velocity_a = np.cross(omega_a, position_m)
    velocity_b = np.cross(omega_b, position_m)
    relative = velocity_b - velocity_a
    signed = float(relative @ normal_ab)
    tangential = float(relative @ tangent)
    if not (math.isfinite(signed) and math.isfinite(tangential)):
        raise SpatialSupportError("RELATIVE_VELOCITY_NONFINITE")
    return {"velocity_a_xyz_m_per_year": velocity_a.tolist(),
            "velocity_b_xyz_m_per_year": velocity_b.tolist(),
            "relative_velocity_xyz_m_per_year": relative.tolist(),
            "normal_ab_xyz": normal_ab.tolist(), "tangent_xyz": tangent.tolist(),
            "signed_opening_m_per_year": signed,
            "signed_tangential_m_per_year": tangential}


def classify_signed_extension(value_m_per_year: float,
                              zero_tolerance_m_per_year: float) -> str:
    if not math.isfinite(value_m_per_year) or not math.isfinite(zero_tolerance_m_per_year) or zero_tolerance_m_per_year < 0:
        raise SpatialSupportError("SIGNED_EXTENSION_INPUT_INVALID")
    if value_m_per_year > zero_tolerance_m_per_year:
        return "EXTENSION"
    if value_m_per_year < -zero_tolerance_m_per_year:
        return "COMPRESSION"
    return "ZERO_WITHIN_GOVERNED_TOLERANCE"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpatialSupportError(f"AUTHORITY_JSON_UNAVAILABLE:{path.name}") from exc
    if not isinstance(value, dict):
        raise SpatialSupportError(f"AUTHORITY_JSON_NOT_OBJECT:{path.name}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _support_id(row: int, column: int) -> str:
    return f"R6G1D-R{row:03d}-C{column:03d}"


def _continental_memberships(fields: Mapping[str, np.ndarray],
                             registry: Mapping[str, Any],
                             index: Mapping[str, Any]) -> dict[str, set[str]]:
    domain = fields["physical_crust_domain_id"]
    thermal = fields["continental_thermal_domain_id"]
    crust = fields["crustal_thickness_m"]
    base = fields["continental_reference_lithosphere_thickness_m"]
    q_surface = fields["continental_reference_surface_heat_flow_w_m2"]
    q_by_class = registry["boundary_refs"]["continental_q_existing_by_thermal_class"]["class_values_w_m2"]
    q_name = {1: "COLD_STABLE", 2: "NORMAL", 3: "HOT_EXTENDED"}
    entries = {row["class"]: row for row in index["support_classes"]}
    memberships = {name: set() for name in entries}
    for row in range(domain.shape[0]):
        for column in range(domain.shape[1]):
            domain_id, thermal_id = int(domain[row, column]), int(thermal[row, column])
            if domain_id not in CONTINENTAL_DOMAIN_IDS or thermal_id not in CONTINENTAL_CLASS_BY_ID:
                continue
            h_crust, h_base, q = float(crust[row, column]), float(base[row, column]), float(q_surface[row, column])
            expected_q = float(q_by_class[q_name[thermal_id]])
            if not (math.isfinite(h_crust) and math.isfinite(h_base) and math.isfinite(q)
                    and h_base > h_crust > 0 and q > 0 and abs(q - expected_q) <= 1e-12):
                continue
            class_name = CONTINENTAL_CLASS_BY_ID[thermal_id]
            memberships[class_name].add(_support_id(row, column))
    for class_name in CONTINENTAL_CLASS_BY_ID.values():
        entry = entries[class_name]
        serialized = "".join(f"{item}\n" for item in sorted(memberships[class_name])).encode("utf-8")
        if (len(memberships[class_name]) != int(entry["count"])
                or hashlib.sha256(serialized).hexdigest() != entry["support_id_sha256"]):
            raise SpatialSupportError(f"B6N8N_CONTINENTAL_MEMBERSHIP_HASH_MISMATCH:{class_name}")
    return memberships


def audit_pair_5_11(repository_root: str | Path, *,
                    expected_branch: str) -> dict[str, Any]:
    """Verify payloads, exact cell/plate join, two-sided B6N8-N support and T0 kinematics."""
    root = Path(repository_root).resolve()
    source, inventory = load_b5_sources(root, expected_branch=expected_branch)
    preflight = preflight_admitted_bindings(root)
    if (preflight.admitted_count != 63_620 or preflight.continental_count != 14_258
            or preflight.production_execution_authorized):
        raise SpatialSupportError("B6N8N_SUPPORT_PREFLIGHT_CHANGED")
    index_path = root / "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json"
    registry_path = root / "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json"
    index, registry = _read_json(index_path), _read_json(registry_path)
    field_path = (root / index["field_package"]["path"]).resolve()
    if root not in field_path.parents or _sha256(field_path) != index["field_package"]["sha256"]:
        raise SpatialSupportError("B6N8N_FIELD_PACKAGE_HASH_MISMATCH")
    vector_path = resolve_external_payload_path(root, source.vector_manifest["payload"]["path"])
    if _sha256(vector_path) != source.vector_manifest["payload"]["sha256"]:
        raise SpatialSupportError("VECTOR_PARTITION_PAYLOAD_HASH_MISMATCH")
    with np.load(vector_path, allow_pickle=False) as vector, np.load(field_path, allow_pickle=False) as fields:
        lookup = exact_face_plate_lookup(vector["face_row"], vector["face_col"], vector["face_plate_id"])
        crust_classes = exact_face_plate_lookup(vector["face_row"], vector["face_col"], vector["face_crust_class"])
        memberships = _continental_memberships(fields, registry, index)
        admitted = set().union(*memberships.values())
        field_values = {name: fields[name].copy() for name in (
            "physical_crust_domain_id", "continental_thermal_domain_id", "crustal_thickness_m",
            "continental_reference_lithosphere_thickness_m",
            "continental_reference_surface_heat_flow_w_m2")}
    census_by_id = {row["boundary_id"]: row for row in source.kinematic_census["segments"]}
    junction_vertices = {str(row["vertex_id"]) for row in source.boundary_state["junctions"]
                         if int(row.get("degree", 0)) >= 3}
    euler = {int(row["plate_id"]): tuple(float(x) for x in row["euler_vector_rad_per_year"])
             for row in source.kinematics.plates}
    radius = float(source.vector_manifest["parent_grid"]["radius_m"])
    event_census = _read_json(root / "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json")
    pair_event = next((row for row in event_census["candidates"] if row.get("pair_id") == "5:11"), None)
    if pair_event is None or pair_event.get("eligibility") != "ELIGIBLE_QUIESCENT":
        raise SpatialSupportError("PAIR_5_11_EVENT_CENSUS_IDENTITY_OR_STATUS_CHANGED")

    matrix: list[dict[str, Any]] = []
    rows = [row for row in source.boundary_descriptors if row["adjacent_plate_ids"] == list(PLATE_PAIR)]
    if len(rows) != 15:
        raise SpatialSupportError("PAIR_5_11_BOUNDARY_COUNT_CHANGED")
    for edge in rows:
        boundary_id = str(edge["boundary_id"])
        edge_def = edge["parent_grid_edge"]
        row, column, axis = int(edge_def["row"]), int(edge_def["column"]), str(edge_def["axis"])
        cells = incident_cells(row, column, axis)
        plate0, plate1 = lookup[cells.first], lookup[cells.second]
        face_crust0, face_crust1 = crust_classes[cells.first], crust_classes[cells.second]
        mapping_ok = (tuple(sorted((plate0, plate1))) == PLATE_PAIR
                      and tuple(sorted((face_crust0, face_crust1))) == (1, 1))
        sides = []
        for cell, plate_id in ((cells.first, plate0), (cells.second, plate1)):
            r, c = cell
            support_id = _support_id(r, c)
            domain_id = int(field_values["physical_crust_domain_id"][r, c])
            thermal_id = int(field_values["continental_thermal_domain_id"][r, c])
            crust_m = float(field_values["crustal_thickness_m"][r, c])
            base_m = float(field_values["continental_reference_lithosphere_thickness_m"][r, c])
            q_w_m2 = float(field_values["continental_reference_surface_heat_flow_w_m2"][r, c])
            sides.append({"support_id": support_id, "row": r, "column": c,
                "plate_id": plate_id, "physical_crust_domain_id": domain_id,
                "parent_crust_class": int(crust_classes[cell]),
                "parent_crust_class_semantics": {0: "OCEANIC", 1: "CONTINENTAL", 2: "TRANSITIONAL"}.get(int(crust_classes[cell]), "UNKNOWN"),
                "continental_thermal_domain_id": thermal_id,
                "support_class": CONTINENTAL_CLASS_BY_ID.get(thermal_id, "UNKNOWN"),
                "admitted_continental_binding": support_id in admitted,
                "crustal_thickness_m": crust_m, "reference_lithosphere_thickness_m": base_m,
                "surface_heat_flow_w_m2": q_w_m2})
        census = census_by_id.get(boundary_id)
        if census is None:
            raise SpatialSupportError(f"BOUNDARY_CENSUS_ROW_MISSING:{boundary_id}")
        kinematics = signed_boundary_velocity(row=row, column=column, axis=axis,
            first_plate=plate0, second_plate=plate1, plate_a=5, plate_b=11,
            euler_rad_per_year=euler, radius_m=radius)
        delta = abs(kinematics["signed_opening_m_per_year"]
                    - float(census["relative_normal_velocity_m_per_year"]))
        if delta > 1e-12:
            raise SpatialSupportError(f"EULER_CENSUS_CROSSCHECK_FAILED:{boundary_id}")
        junction_adjacent = any(str(vertex) in junction_vertices for vertex in census["endpoint_vertex_ids"])
        sign = classify_signed_extension(kinematics["signed_opening_m_per_year"],
                                         float(source.kinematic_census["diagnostic_zero_tolerance_m_per_year"]))
        blockers = []
        if not mapping_ok:
            blockers.append("PARENT_PARTITION_SIDE_PLATE_OR_CRUST_CLASS_MISMATCH")
        if not all(side["admitted_continental_binding"] for side in sides):
            blockers.append("ONE_OR_MORE_SIDES_NOT_ADMITTED_BY_B6N8N")
        if sign != "EXTENSION":
            blockers.append("NO_GOVERNED_POSITIVE_SIGNED_OPENING")
        if junction_adjacent:
            blockers.append("JUNCTION_ENDPOINT_TREATMENT_UNBOUND")
        matrix.append({"boundary_id": boundary_id, "ordered_plate_pair": [5, 11],
            "parent_grid_edge": edge_def, "endpoint_vertex_ids": census["endpoint_vertex_ids"],
            "edge_length_m": float(edge["length_m"]), "event_eligibility": pair_event["eligibility"],
            "sides_plate_a_then_plate_b": sorted(sides, key=lambda item: item["plate_id"]),
            "PLATE_MAPPING": "PASS_EXACT_PARTITION_JOIN" if mapping_ok else "FAIL",
            "MATERIAL_ADMISSIBILITY": "PASS_B6N8N_ADMITTED" if all(x["admitted_continental_binding"] for x in sides) else "BLOCKED",
            "THERMAL_AVAILABILITY": "PASS_AUTHORED_T0_CONTINENTAL_PROFILE_INPUTS" if all(x["admitted_continental_binding"] for x in sides) else "BLOCKED",
            "SECTION_ELIGIBILITY": "ELIGIBLE" if not blockers else "EXCLUDED",
            "junction_adjacent": junction_adjacent, "SIGNED_EXTENSION": sign,
            "signed_Ux_m_per_year": kinematics["signed_opening_m_per_year"],
            "tangential_relative_velocity_m_per_year": kinematics["signed_tangential_m_per_year"],
            "Euler_census_abs_difference_m_per_year": delta,
            "velocity_components": kinematics,
            "BLOCKER": blockers})
    eligible = [row for row in matrix if row["SECTION_ELIGIBILITY"] == "ELIGIBLE"]
    if not eligible:
        raise SpatialSupportError("NO_NONJUNCTION_TWO_SIDED_ADMITTED_EXTENSION_EDGE")
    eligible.sort(key=lambda item: (int(item["parent_grid_edge"]["row"]),
                                   int(item["parent_grid_edge"]["column"]),
                                   str(item["parent_grid_edge"]["axis"]), item["boundary_id"]))
    selected = eligible[(len(eligible) - 1) // 2]
    selected_sides = selected["sides_plate_a_then_plate_b"]
    for side in selected_sides:
        row, column = int(side["row"]), int(side["column"])
        side["t0_profile"], side["initializer_inventory"] = None, None
        profile, profile_inventory = materialize_admitted_continental_t0(
            root, side["support_id"])
        if profile.support_class != side["support_class"]:
            raise SpatialSupportError("MATERIALIZED_PROFILE_CLASS_DIFFERS_FROM_EXACT_SUPPORT_BINDING")
        side["t0_profile"] = {"z_m": list(profile.z_m), "temperature_k": list(profile.temperature_k),
            "scenario_id": profile.scenario_id,
            "material_roles": list(profile.material_roles), "material_properties": [vars(x) for x in profile.materials],
            "crust_m": profile.crust_m, "model_base_m": profile.model_base_m,
            "surface_temperature_k": profile.surface_temperature_k,
            "surface_heat_flow_w_m2": profile.surface_heat_flow_w_m2,
            "support_lineage": {"grid_id": index["grid"]["grid_id"],
                "support_id": side["support_id"], "native_row": str(row),
                "native_column": str(column), "field_package": index["field_package"]["path"],
                "profile_provenance": dict(profile.provenance)}}
        side["initializer_inventory"] = profile_inventory
    event_identity = hashlib.sha256((root / "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json").read_bytes()).hexdigest()
    return {"stage": "T-F2B", "scope": "T0_CONTINENTAL_ENGINEERING_EXTENSION_EXPERIMENT",
        "source_branch": source.branch, "source_head": source.head,
        "source_identity_sha256": source.source_identity,
        "kinematics_semantic_identity_sha256": source.kinematics.canonical_identity_sha256,
        "kinematics_artifact_sha256": source.kinematics.artifact_sha256,
        "kinematics_uncertainty": dict(source.kinematics.source_uncertainty),
        "source_grid_radius_m": radius,
        "plate_euler_vectors_rad_per_year": {str(pid): list(euler[pid]) for pid in PLATE_PAIR},
        "vector_partition_payload_sha256": source.vector_manifest["payload"]["sha256"],
        "b6n8n_field_package_sha256": index["field_package"]["sha256"],
        "b6n8n_index_sha256": _sha256(index_path), "event_eligibility_census_sha256": event_identity,
        "mapping_join": {"algorithm": "EXACT_UNIQUE_COMPLETE(face_row,face_col)->face_plate_id",
            "parent_crust_class_codes": {"0": "OCEANIC", "1": "CONTINENTAL", "2": "TRANSITIONAL"},
            "physical_crust_domain_id_is_separate": True, "parent_cells": len(lookup),
            "mapping_sha256": hashlib.sha256("".join(
                f"{r:03d},{c:03d},{lookup[(r,c)]}\n" for r in range(GRID_ROWS) for c in range(GRID_COLUMNS)
            ).encode("ascii")).hexdigest()},
        "pair_event_census": {"pair_id": "5:11", "eligibility": pair_event["eligibility"],
            "edge_count": pair_event["boundary_edge_count"],
            "positive_opening_edge_count": pair_event["positive_opening_edge_count"],
            "mean_opening_diagnostic_m_per_year": pair_event["pair_mean_opening_velocity_m_per_year"],
            "uncertainty": pair_event.get("uncertainty"),
            "scope_is_activation_authority": False},
        "b6n8n_support_counts": {"admitted_total": preflight.admitted_count,
            "admitted_continental": preflight.continental_count,
            "continental_support_membership_counts": {key: len(value) for key, value in memberships.items()}},
        "selection_rule": "FILTER_EXACT_TWO_SIDED_ADMITTED_CONTINENTAL_POSITIVE_EXTENSION_NONJUNCTION; SORT(row,column,axis,boundary_id); SELECT_LOWER_MEDIAN; NEVER_MAXIMIZE_OPENING",
        "selected_boundary_id": selected["boundary_id"], "selected_parent_grid_edge": selected["parent_grid_edge"],
        "selected_ordered_plate_pair": [5, 11], "edge_matrix": matrix,
        "all_15_edges_classified": len(matrix) == 15,
        "no_world_history_access_or_publication": True,
        "canonical_state_changed": False}
