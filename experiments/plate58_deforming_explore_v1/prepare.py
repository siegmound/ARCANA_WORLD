"""Source-bound plate 5:8 experimental continuum preparation; NEVER a mechanical solve.

Builds a small parent-indexed FEG/PRE case and an explicit fail-closed G2/G3
decision packet. All material/basal/NS unknowns remain unknown. No T1 is made.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.shellset_mesh.coordinates import (
    RUNTIME_FRAME_ID, _unit_vectors, rotation_matrices,
)
from arcana_worldsim.r6.shellset_mesh.feg import parse_feg, write_feg
from experiments.shellset_regional_explore_v1.build_case import (
    FEG, PRE, EULER, LAW, LOADER, ROOT, perimeter, sha, specialize_loader,
)

LABEL = "NONCANONICAL_PLATE58_CONTINUUM_HYPOTHESIS"
STATUS = "STAGED_G1_G3_DISTAL_ONLY__SOLVE_BLOCKED_G2_NS_BASAL"
CELLS = tuple((r, c) for r in (100, 101) for c in (21, 22))
ENVELOPE_CELLS = tuple((r, c) for r in range(99, 103) for c in range(20, 24))
SECONDS_YEAR = 31_557_600.0
RADIUS_M = 6_371_000.0
REFERENCE_BAND_KM = 100.0
WIDTHS_KM = (10.0, 100.0, 300.0)
SOURCE_CONTACT_IDS = (
    "R6BND-T0-10fc6a8d9eb6b36cb9a5",
    "R6BND-T0-61b58bd29612d49e4498",
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _emit(path, data):
    path.write_bytes(data)


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def interface_edges(elements, plates):
    """Return undirected edges incident to distinct plate IDs on both sides."""
    incidence = {}
    for element, plate in zip(elements, plates, strict=True):
        for a, b in ((element.node_ids[0], element.node_ids[1]),
                     (element.node_ids[1], element.node_ids[2]),
                     (element.node_ids[2], element.node_ids[0])):
            incidence.setdefault(tuple(sorted((int(a), int(b)))), []).append(int(plate))
    require(all(1 <= len(v) <= 2 for v in incidence.values()), "NONMANIFOLD_REGION_EDGE")
    return sorted(key for key, row in incidence.items() if len(row) == 2 and row[0] != row[1])


def strain_rate_scales(opening_m_year, widths_km=WIDTHS_KM):
    """Kinematic scale only: not a resolved strain rate or a constitutive law."""
    require(math.isfinite(opening_m_year) and opening_m_year > 0, "OPENING_INVALID")
    require(all(math.isfinite(w) and w > 0 for w in widths_km), "WIDTH_INVALID")
    return [{"width_km": float(w), "nominal_extension_rate_s_inv":
             opening_m_year / (1000.0 * w * SECONDS_YEAR)}
            for w in widths_km]


def readiness_gate(candidate):
    """A mechanical solve is not permitted merely because a fixture exists."""
    decisions = candidate["decisions"]
    missing = []
    g2 = decisions["G2_material"]
    for name in ("fit_a_b_c_d_by_layer", "effective_pressure_and_biot",
                 "brittle_friction", "water_model", "creep_fit_validation"):
        if g2[name] is None:
            missing.append("G2." + name)
    for name in ("physical_width_and_resolution", "time_validity"):
        if decisions["G3_accommodation"][name] is None:
            missing.append("G3_accommodation." + name)
    for name in ("north_cut", "south_cut", "basal_normal_support"):
        if decisions["G3_support"][name] is None:
            missing.append("G3_support." + name)
    return {"mechanical_solve_authorized": False, "missing": missing,
            "reason": "NO_AUTHORIAL_SOLVE_AUTHORITY_AND_INCOMPLETE_PHYSICAL_CLOSURE"}


def _selection(face_index, mesh, parent, cells):
    faces = [face_index[cell] for cell in cells]
    ids = sorted({int(t) for face in faces for t in mesh.parent_face_triangles[face]})
    require(len(ids) == 2 * len(cells), "UNEXPECTED_FACE_TRIANGLE_COUNT")
    elements = [parent.elements[t - 1] for t in ids]
    require(all(el.node_ids == tuple(map(int, mesh.triangles[t - 1]))
                for el, t in zip(elements, ids, strict=True)), "PARENT_FEG_TRIANGLE_BINDING_FAILED")
    nodes = sorted({int(n) for el in elements for n in el.node_ids})
    plates = [int(mesh.triangle_plate_id[t - 1]) for t in ids]
    return faces, ids, elements, nodes, plates


def _frame_velocity(omega, canonical_lat_lon):
    xyz = _unit_vectors(np.asarray(canonical_lat_lon, dtype=float))
    forward, _ = rotation_matrices()
    rt_xyz = xyz @ forward.T
    lat_lon = np.degrees(np.column_stack((np.arcsin(rt_xyz[:, 2]),
                                            np.arctan2(rt_xyz[:, 1], rt_xyz[:, 0]))))
    v = np.cross(np.asarray(omega, dtype=float), xyz) @ forward.T * RADIUS_M / SECONDS_YEAR
    phi, lam = np.deg2rad(lat_lon).T
    south = np.column_stack((np.sin(phi)*np.cos(lam), np.sin(phi)*np.sin(lam), -np.cos(phi)))
    east = np.column_stack((-np.sin(lam), np.cos(lam), np.zeros(len(phi))))
    return lat_lon, np.column_stack((np.einsum("ij,ij->i", v, south),
                                    np.einsum("ij,ij->i", v, east)))


def _relative_at_edge(mesh, a, b, omega_w, omega_e):
    xyz = _unit_vectors(mesh.vertices_lat_lon[[a - 1, b - 1]])
    midpoint = xyz.sum(axis=0)
    midpoint /= np.linalg.norm(midpoint)
    lat = math.asin(float(midpoint[2]))
    lon = math.atan2(float(midpoint[1]), float(midpoint[0]))
    east = np.asarray((-math.sin(lon), math.cos(lon), 0.0))
    north = np.asarray((-math.sin(lat)*math.cos(lon), -math.sin(lat)*math.sin(lon),
                        math.cos(lat)))
    relative = np.cross(np.asarray(omega_e) - np.asarray(omega_w), midpoint)
    relative *= RADIUS_M
    return {"parent_node_ids": [a, b],
            "opening_east_m_year": float(relative @ east),
            "tangential_north_m_year": float(relative @ north)}


def prepare(output):
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    meta = json.loads((ROOT / (PRE + ".json")).read_text())
    closure = json.loads((ROOT / "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json").read_text())
    euler = json.loads((ROOT / EULER).read_text())
    law = json.loads((ROOT / LAW).read_text())
    source_paths = (FEG, PRE + ".dat", PRE + ".json", EULER, LAW, LOADER,
                    "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json",
                    "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    pins = {name: sha(ROOT/name) for name in source_paths}
    require(pins[PRE + ".dat"] == meta["runtime_data_sha256"] and
            pins[FEG] == closure["evidence"]["raw_feg_sha256"] and
            euler["payload_identity_sha256"] == meta["projection_source_lineage"]["kinematics_sha256"],
            "T0_AUTHORITY_SHA_MISMATCH")
    require("first segment" in law["first_segment_policy"]["motion"].lower(),
            "FIRST_SEGMENT_KINEMATICS_NOT_BOUND")
    partition = json.loads((ROOT/"R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    part = resolve_external_payload_path(ROOT, partition["payload"]["path"])
    require(part.is_file() and sha(part) == partition["payload"]["sha256"]
            == euler["parent_vector_partition_sha256"], "EXTERNAL_PARTITION_SHA_MISMATCH")
    pins["external:vector_plate_partition"] = sha(part)
    mesh = load_canonical_mesh(ROOT)
    require(mesh.normalized_sha256 == closure["evidence"]["canonical_mesh_sha256"],
            "PARENT_MESH_IDENTITY_MISMATCH")
    parent = parse_feg((ROOT/FEG).read_text(), mode="SHELLS_READY")
    require(not parent.faults and len(parent.elements) == len(mesh.triangles),
            "PARENT_FAULT_OR_ELEMENT_INVENTORY_INVALID")
    with np.load(part, allow_pickle=False) as data:
        face_index = {(int(r), int(c)): i for i, (r, c) in enumerate(
            zip(data["face_row"], data["face_col"], strict=True))}
    require(len(face_index) == 180*360, "PARENT_FACE_MAPPING_NOT_BIJECTIVE")
    _, parent_ids, parent_elements, node_ids, plate_ids = _selection(
        face_index, mesh, parent, CELLS)
    require(len(parent_ids) == 8 and len(node_ids) == 9 and
            set(plate_ids) == {5, 8}, "PLATE58_SOURCE_TOPOLOGY_INVALID")
    local = {n: i for i, n in enumerate(node_ids, 1)}
    model_elements = tuple(replace(el, element_id=i,
                                   node_ids=tuple(local[n] for n in el.node_ids))
                           for i, el in enumerate(parent_elements, 1))
    model = replace(parent, title=LABEL, nodes=tuple(
        replace(parent.nodes[n-1], node_id=local[n]) for n in node_ids),
        elements=model_elements)
    serialized = write_feg(model)
    require(parse_feg(serialized, mode="SHELLS_READY") == model,
            "REGIONAL_FEG_ROUNDTRIP_FAILED")
    cycle = perimeter(model_elements)
    require(len(cycle) == 8 and len(set(local.values()) - set(cycle)) == 1,
            "REGIONAL_SQUARE_TOPOLOGY_INVALID")
    interface = interface_edges(model_elements, plate_ids)
    require(len(interface) == 2 and
            len({n for edge in interface for n in edge}) == 3,
            "PLATE58_TWO_SEGMENT_CONTACT_INVALID")
    canonical = mesh.vertices_lat_lon[np.asarray(node_ids, dtype=int)-1]
    lat_levels = sorted({round(float(x), 7) for x in canonical[:,0]})
    lon_levels = sorted({round(float(x), 7) for x in canonical[:,1]})
    require(len(lat_levels) == len(lon_levels) == 3, "NONRECTANGULAR_FEG_PATCH")
    west = [local[n] for n, ll in zip(node_ids, canonical, strict=True)
            if abs(ll[1] - lon_levels[0]) < 1e-6]
    east = [local[n] for n, ll in zip(node_ids, canonical, strict=True)
            if abs(ll[1] - lon_levels[-1]) < 1e-6]
    north = [local[n] for n, ll in zip(node_ids, canonical, strict=True)
             if abs(ll[0] - lat_levels[-1]) < 1e-6]
    south = [local[n] for n, ll in zip(node_ids, canonical, strict=True)
             if abs(ll[0] - lat_levels[0]) < 1e-6]
    require(all(len(row) == 3 for row in (west,east,north,south)),
            "DISTAL_CUT_NODE_INVENTORY_INVALID")
    euler_by_plate = {int(p["plate_id"]): p["euler_vector_rad_per_year"]
                      for p in euler["plates"]}
    require(set(euler_by_plate) == set(range(12)), "EULER_PLATE_INVENTORY_INVALID")
    runtime_pos, v_w = _frame_velocity(euler_by_plate[8], canonical)
    _, v_e = _frame_velocity(euler_by_plate[5], canonical)
    velocities = {}
    for side, plate, ids, field in (("west",8,west,v_w), ("east",5,east,v_e)):
        for lid in ids:
            velocities[lid] = {
                "parent_id": node_ids[lid-1], "plate_id": plate, "side": side,
                "south_east_m_s": [float(x) for x in field[lid-1]],
                "basis": RUNTIME_FRAME_ID, "proposal": "RIGID_DISTAL_EULER_DIRICHLET"}
    require(len(velocities) == 6, "DISTAL_NODE_BC_INVENTORY_INVALID")
    contact = [_relative_at_edge(mesh, node_ids[a-1], node_ids[b-1],
                                  euler_by_plate[8], euler_by_plate[5])
               for a,b in interface]
    require(all(0.15 < r["opening_east_m_year"] < 0.165 and
                0.004 < abs(r["tangential_north_m_year"]) < 0.01
                for r in contact), "SOURCE_PLATE58_RELATIVE_SPEED_MISMATCH")
    for name, edge in zip(SOURCE_CONTACT_IDS, contact, strict=True):
        edge["operator_source_segment_id"] = name
    opening = sum(row["opening_east_m_year"] for row in contact)/len(contact)
    with (ROOT/(PRE+".dat")).open() as stream:
        header = next(stream).split()
        pre_rows = [line.split() for line in stream]
    require(int(header[-1]) == len(parent.nodes) == len(pre_rows),
            "PARENT_PRE_NODE_COUNT_MISMATCH")
    pre_nodes = []
    pre_text = []
    for n in node_ids:
        row = pre_rows[n-1]
        require(len(row) == len(meta["field_order"]) and int(row[0]) == n
                and float(row[8]) == 1.0 and float(row[5]) == 0.0,
                "PLATE58_PRE_NOT_UNMIXED_CONTINENTAL")
        fields = dict(zip(meta["field_order"], map(float, row)))
        feg_node = parent.nodes[n-1]
        require(fields["crust_thickness_m"] == feg_node.crustal_thickness_m and
                fields["mantle_lithosphere_thickness_m"] == feg_node.mantle_lithosphere_thickness_m,
                "PARENT_PRE_FEG_LAYER_MISMATCH")
        pre_nodes.append({"local_id":local[n],"parent_id":n,"PRE":fields})
        pre_text.append(" ".join([str(local[n]), *row[1:]]))
    _, env_tri, env_el, env_nodes, env_plates = _selection(
        face_index, mesh, parent, ENVELOPE_CELLS)
    env_edges = interface_edges(env_el, env_plates)
    require(len(env_tri) == 32 and len(env_nodes) == 25 and {5,8}.issubset(set(env_plates)),
            "ENVELOPE_16_CELL_SOURCE_INVALID")
    decisions = {
        "authority": "USER_APPROVED_EXPLORE_HYPOTHESES_ONLY__NOT_CANON",
        "G2_material": {
            "proxy_roles": {"crust":"QUARTZITE_TWO_LAB_CANDIDATES",
                            "mantle":"DRY_OLIVINE_LAB_BENCHMARK"},
            "common_eCreep_FAIR_candidate": 0.267857,
            "common_eCreep_fit_error_FAIROperator_pct": 3.1,
            "stress_10km_pivot_MPa_FAIROperator": [405.0, 98.0],
            "fit_a_b_c_d_by_layer": None, "effective_pressure_and_biot": None,
            "brittle_friction": None, "water_model": None,
            "creep_fit_validation": None},
        "G3_accommodation": {
            "model": "DISTRIBUTED_CONTINUUM_NO_NEW_FAULT_ELEMENTS",
            "nominal_band_km_EXPLORE_only": REFERENCE_BAND_KM,
            "comparison_widths_km": list(WIDTHS_KM),
            "physical_width_and_resolution": None, "time_validity": None},
        "G3_support": {
            "west_east": "SOURCE_PLATE_8_WEST_AND_PLATE_5_EAST_RIGID_EULER",
            "north_cut": None, "south_cut": None,
            "basal_tangential_hypothesis": "NO_DRAG_FREE_SLIP_EXPLORE_ONLY",
            "basal_normal_support": None,
            "mechanical_reference": "CANONICAL_KINEMATIC_GAUGE_NOT_MANTLE_FRAME"},
    }
    staged = {
        "schema": "ARCANA_R6_PLATE58_DEFORMING_EXPLORE_STAGING_V1",
        "status": STATUS, "label":LABEL, "t0_age_ma":210,
        "source_sha256":pins,"parent_cells":[list(c) for c in CELLS],
        "parent_triangle_ids":parent_ids, "node_ids_parent":node_ids,
        "plate_by_parent_triangle":dict(zip(map(str,parent_ids),plate_ids)),
        "local_contact_edges":[list(x) for x in interface],
        "contact_diagnostics":contact, "mean_opening_m_year":opening,
        "continuum_cut_nodes":{"west":west,"east":east,"north":north,"south":south},
        "prescribed_distal_node_velocity":velocities,
        "parent_node_PRE":pre_nodes, "runtime_lat_lon_deg":runtime_pos.tolist(),
        "numerical_frame":RUNTIME_FRAME_ID,
        "envelope_16_parent_cells":[list(c) for c in ENVELOPE_CELLS],
        "envelope_parent_triangle_ids":env_tri,
        "envelope_node_count":len(env_nodes),
        "envelope_plates":sorted(set(env_plates)),
        "envelope_contact_edges_parent":[list(x) for x in env_edges],
        "diagnostic_width_rates":strain_rate_scales(opening),
        "resolution_warning":"100km band near parent 1-degree spacing; NOT demonstrated converged",
        "decisions":decisions, "physical_deforming_t1":None,
        "solver_output":None, "G4_material_transport":None}
    staged["readiness"] = readiness_gate(staged)
    require(not staged["readiness"]["mechanical_solve_authorized"] and
            staged["readiness"]["missing"], "PREMATURE_SOLVE_AUTHORITY")
    output.mkdir(parents=True)
    _emit(output/"CASE.json",_json(staged))
    _emit(output/"regional.feg", serialized.encode("utf-8"))
    _emit(output/"regional_PRE.dat",
          (f"ARCANA_R6_REGIONAL_PRE_EXPERIMENT_V1 "
           f"arcana_worldsim.r6.regional_owner_bound_experiment.v1 {len(node_ids)}\n"
           + "\n".join(pre_text) + "\n").encode("utf-8"))
    _emit(output/"MOD_ArcanaRuntime.regional.f90",
          specialize_loader((ROOT/LOADER).read_text(), len(node_ids)).encode("utf-8"))
    output_members = ("CASE.json","regional.feg","regional_PRE.dat",
                      "MOD_ArcanaRuntime.regional.f90")
    manifest = {"schema":"ARCANA_R6_PLATE58_EXPERIMENTAL_STAGE_MANIFEST_V1",
                "status":STATUS, "files":{p:sha(output/p) for p in output_members},
                "source_sha256":pins, "no_solver_run":True,
                "no_T1":True, "no_canonical_promotion":True}
    _emit(output/"MANIFEST.json",_json(manifest))
    return staged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path,help="New exclusive output directory")
    args = parser.parse_args()
    row = prepare(args.output)
    print(json.dumps({"status":row["status"], "source_parent_triangles":len(row["parent_triangle_ids"]),
                      "required_decisions":row["readiness"]["missing"],
                      "mean_opening_m_year":row["mean_opening_m_year"],
                      "no_solve":True},indent=2))
