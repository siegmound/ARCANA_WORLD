"""Read-only G3 neighborhood closure diagnostics for ARCANA plate 5:8.

This stage uses canonical T0 geometry, exact source boundary IDs and the
authored Euler vectors. It does NOT infer mechanical tractions, normal basal
support, a continuous external velocity field, or any deforming T1.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.shellset_mesh.coordinates import _unit_vectors
from arcana_worldsim.r6.shellset_mesh.feg import parse_feg, write_feg

from experiments.plate58_deforming_explore_v1.check import verify as verify_stage
from experiments.plate58_deforming_explore_v1.prepare import (
    ENVELOPE_CELLS, EULER, FEG, PRE, ROOT, SOURCE_CONTACT_IDS,
    _frame_velocity, _json, _selection, readiness_gate, require, sha,
)

STATUS = "PASS_16_CELL_G3_SOURCE_DIAGNOSTIC__NS_BASAL_UNRESOLVED"
SCHEMA = "ARCANA_R6_PLATE58_G3_NEIGHBOR_ENVELOPE_V1"
RADIUS_M = 6_371_000.0


def edge_incidence(elements, plates):
    """Map undirected FEG edges to incident (triangle ordinal, plate) pairs."""
    result = {}
    for index, (element, plate) in enumerate(zip(elements, plates, strict=True)):
        u, v, w = map(int, element.node_ids)
        require(len({u, v, w}) == 3, "DEGENERATE_ELEMENT")
        for a, b in ((u, v), (v, w), (w, u)):
            result.setdefault(tuple(sorted((a, b))), []).append((index, int(plate)))
    require(all(1 <= len(rows) <= 2 and
                (len(rows) == 1 or rows[0][0] != rows[1][0])
                for rows in result.values()), "NONMANIFOLD_OR_DUPLICATED_FACE")
    return result


def side_of_edge(lla, llb, bounds, tol=1e-7):
    """Classify only the FOUR straight exterior grid cuts, never diagonal edges."""
    south, north, west, east = bounds
    for side, axis, coordinate in (
        ("south", 0, south), ("north", 0, north),
        ("west", 1, west), ("east", 1, east),
    ):
        if abs(float(lla[axis])-coordinate) <= tol and abs(float(llb[axis])-coordinate) <= tol:
            return side
    raise ValueError("OUTER_EDGE_NOT_ON_RECTANGULAR_CUT")


def geodesic_length_km(a, b):
    values = _unit_vectors(np.asarray((a, b), dtype=float))
    return float(RADIUS_M / 1000 * math.atan2(
        float(np.linalg.norm(np.cross(values[0], values[1]))),
        float(np.dot(values[0], values[1]))))


def midpoint_lat_lon(a, b):
    values = _unit_vectors(np.asarray((a, b), dtype=float))
    midpoint = values[0] + values[1]
    norm = float(np.linalg.norm(midpoint))
    require(norm > 0, "ANTIPODAL_EDGE_UNSUPPORTED")
    midpoint /= norm
    return [math.degrees(math.asin(float(midpoint[2]))),
            math.degrees(math.atan2(float(midpoint[1]), float(midpoint[0])))]


def _angles(coords, edge):
    return [coords[edge[0]], coords[edge[1]]]


def _ring_coordinates(mesh, node_ids, edges):
    ll = {int(n): mesh.vertices_lat_lon[n-1].tolist() for n in node_ids}
    all_lat = [ll[n][0] for n in ll]
    all_lon = [ll[n][1] for n in ll]
    bounds = (min(all_lat), max(all_lat), min(all_lon), max(all_lon))
    outer = {side: [] for side in ("west", "east", "south", "north")}
    for edge, members in edges.items():
        if len(members) != 1:
            continue
        side = side_of_edge(ll[edge[0]], ll[edge[1]], bounds)
        outer[side].append((edge, members[0][1]))
    for side in outer:
        outer[side].sort(key=lambda item: (
            midpoint_lat_lon(*_angles(ll, item[0]))[1 if side in ("north", "south") else 0]))
    return ll, bounds, outer


def boundary_diagnostics(mesh, node_ids, elements, plates, eulers, boundary_index):
    """Produce source-indexed split-plate and outer-cut kinematic *observations*."""
    edges = edge_incidence(elements, plates)
    ll, bounds, outer = _ring_coordinates(mesh, node_ids, edges)
    require(all(len(rows) == 4 for rows in outer.values()),
            "SIXTEEN_CELL_RECTANGLE_NOT_FOUR_EDGES_PER_SIDE")
    contact = []
    for edge, members in sorted(edges.items()):
        if len(members) != 2 or members[0][1] == members[1][1]:
            continue
        participants = sorted({row[1] for row in members})
        require(participants == [5, 8], "UNEXPECTED_PLATE_PAIR_AT_CONTACT")
        require(edge in boundary_index, "CONTACT_EDGE_NOT_IN_T0_BOUNDARY_REGISTRY")
        contact.append({"parent_node_ids": list(edge),
                        "source_boundary_id": boundary_index[edge],
                        "parent_triangle_ordinals": [row[0] for row in members],
                        "plates": participants,
                        "length_km": geodesic_length_km(*_angles(ll, edge))})
    require(len({item["source_boundary_id"] for item in contact}) == len(contact),
            "DUPLICATED_CONTACT_SOURCE_ID")
    require(contact, "NO_SOURCE_PLATE58_CONTACT")
    rows_by_side = {}
    for side, rows in outer.items():
        result = []
        for edge, plate in rows:
            require(plate in (5, 8), "ADDITIONAL_PLATE_AT_REGION_CUT")
            center = midpoint_lat_lon(*_angles(ll, edge))
            _runtime_ll, speed = _frame_velocity(eulers[plate], [center])
            result.append({
                "side": side, "parent_node_ids": list(edge), "adjacent_plate_id": plate,
                "midpoint_canonical_lat_lon_deg": center,
                "euler_midpoint_south_east_m_s": [float(x) for x in speed[0]],
                "length_km": geodesic_length_km(*_angles(ll, edge)),
                "prescribed_velocity": None,
                "exterior_traction": None,
                "meaning": "SOURCE_KINEMATIC_SAMPLE_NOT_MECHANICAL_BOUNDARY_CLOSURE",
            })
        rows_by_side[side] = result
    interface_nodes = {n for row in contact for n in row["parent_node_ids"]}
    endpoints = {side: sorted(interface_nodes & {
        n for row in rows_by_side[side] for n in row["parent_node_ids"]})
        for side in ("north", "south", "west", "east")}
    return {
        "source_contact": contact,
        "source_contact_count": len(contact),
        "side_segments": rows_by_side,
        "side_plate_ownership": {side: [r["adjacent_plate_id"] for r in rows]
                                 for side, rows in rows_by_side.items()},
        "source_interface_meets_outer_cut_parent_nodes": endpoints,
        "north_south_extension_policy": None,
        "basal_normal_support_policy": None,
        "north_south_periodicity_supported": False,
        "reason_no_periodic": "BOUNDARY_CONTACT_STEPS_REQUIRE_EXTERIOR_CONTINUATION_LAW",
        "geometry_bounds_lat_lon": list(bounds),
    }


def _source_boundary_index(mesh):
    index = {}
    for edge, identity in zip(mesh.boundary_edge_nodes, mesh.boundary_ids, strict=True):
        key = tuple(sorted(map(int, edge)))
        require(key not in index and str(identity).startswith("R6BND-T0-"),
                "SOURCE_BOUNDARY_REGISTRY_ID_INVALID")
        index[key] = identity
    return index


def _copy_source_validation(stage, root=ROOT):
    for name, digest in stage["source_sha256"].items():
        if name.startswith("external:"):
            continue
        require(sha(root/name) == digest, "PREVIOUS_STAGE_SOURCE_CHANGED:" + name)
    manifest = json.loads((root/"R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    part = resolve_external_payload_path(root, manifest["payload"]["path"])
    require(sha(part) == manifest["payload"]["sha256"] ==
            stage["source_sha256"]["external:vector_plate_partition"],
            "EXTERNAL_VECTOR_SOURCE_CHANGED")
    return part


def prepare_envelope(previous_stage: Path, output: Path):
    """Create a NEW immutable-by-convention diagnostic, never modify the old stage."""
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    verify_stage(previous_stage)
    prior = json.loads((previous_stage/"CASE.json").read_text())
    require(prior["readiness"] == readiness_gate(prior) and
            prior["physical_deforming_t1"] is None, "PRIOR_SOURCE_STAGE_NOT_BLOCKED")
    part = _copy_source_validation(prior)
    mesh = load_canonical_mesh(ROOT)
    parent = parse_feg((ROOT/FEG).read_text(), mode="SHELLS_READY")
    require(not parent.faults and len(parent.elements) == len(mesh.triangles),
            "CANONICAL_FEG_SOURCE_UNEXPECTED")
    with np.load(part, allow_pickle=False) as data:
        face_index = {(int(r), int(c)): i for i, (r, c) in enumerate(
            zip(data["face_row"], data["face_col"], strict=True))}
    require(len(face_index) == 64_800, "FACE_MAPPING_INCOMPLETE")
    faces, ids, elements, nodes, plates = _selection(
        face_index, mesh, parent, ENVELOPE_CELLS)
    require(len(faces) == 16 and len(ids) == 32 and len(nodes) == 25 and
            set(plates) == {5, 8} and
            set(prior["parent_triangle_ids"]).issubset(set(ids)),
            "ENVELOPE_GEOMETRY_OR_PLATE_INVENTORY_CHANGED")
    euler = json.loads((ROOT/EULER).read_text())
    eulers = {int(row["plate_id"]): row["euler_vector_rad_per_year"]
              for row in euler["plates"]}
    require(set(eulers) == set(range(12)), "EULER_INVENTORY_INVALID")
    index = _source_boundary_index(mesh)
    boundary = boundary_diagnostics(mesh, nodes, elements, plates, eulers, index)
    former = []
    for edge in prior["local_contact_edges"]:
        parent_edge = tuple(sorted(prior["node_ids_parent"][int(n)-1] for n in edge))
        require(parent_edge in index, "FOUR_CELL_CONTACT_NOT_IN_SOURCE_REGISTRY")
        former.append(index[parent_edge])
    require(set(former) == set(SOURCE_CONTACT_IDS) and
            set(former).issubset({x["source_boundary_id"] for x in boundary["source_contact"]}),
            "SOURCE_CONTACT_SEGMENT_BINDING_MISMATCH")

    local = {n: i for i,n in enumerate(nodes, 1)}
    new_nodes = tuple(replace(parent.nodes[n-1], node_id=local[n]) for n in nodes)
    new_elements = tuple(replace(row, element_id=i,
                                 node_ids=tuple(local[n] for n in row.node_ids))
                         for i,row in enumerate(elements,1))
    model = replace(parent, title="ARCANA_PLATE58_16CELL_GEOMETRY_ONLY_NOT_SOLVER_READY",
                    nodes=new_nodes, elements=new_elements)
    raw = write_feg(model)
    require(parse_feg(raw, mode="SHELLS_READY") == model, "ENVELOPE_FEG_ROUNDTRIP_FAIL")
    # No PRE reader, mechanical parameters or ShellSet input are generated here.
    all_grid_edges = set()
    for row in elements:
        a,b,c = row.node_ids
        for u,v in ((a,b),(b,c),(c,a)):
            key = tuple(sorted((int(u),int(v))))
            l1,l2 = mesh.vertices_lat_lon[[key[0]-1,key[1]-1]]
            if abs(float(l1[0]-l2[0]))<1e-8 or abs(float(l1[1]-l2[1]))<1e-8:
                all_grid_edges.add(key)
    lengths = sorted(geodesic_length_km(mesh.vertices_lat_lon[u-1],
                                        mesh.vertices_lat_lon[v-1])
                     for u,v in all_grid_edges)
    require(len(lengths)>0 and lengths[0]>0, "ENVELOPE_GRID_SCALE_INVALID")
    middle = lengths[len(lengths)//2]
    report = {
        "schema": SCHEMA,
        "status": STATUS,
        "authority": "SOURCE_BOUND_DIAGNOSTIC__EXPERIMENT_ONLY__NOT_CANON",
        "parent_cells": [list(cell) for cell in ENVELOPE_CELLS],
        "parent_triangle_ids": ids,
        "parent_node_ids": nodes,
        "triangle_plate_ids": plates,
        "source_mesh_identity_sha256": mesh.normalized_sha256,
        "source_vector_partition_sha256": prior["source_sha256"]["external:vector_plate_partition"],
        "source_euler_sha256": prior["source_sha256"][EULER],
        "input_four_cell_sha256": sha(previous_stage/"CASE.json"),
        "source_contact_from_four_cell": sorted(former),
        "boundary_analysis":boundary,
        "mesh_orthogonal_edge_length_km": {
            "minimum":lengths[0], "middle":middle, "maximum":lengths[-1]},
        "reference_100km_band_per_median_source_grid_spacing":
            100.0/middle,
        "reference_100km_band_resolved":False,
        "why_band_unresolved": "No mesh refinement or spatial convergence demonstrated",
        "candidate_crustal_stresses_MPa_at_10km_before_brittle":{
            "FAIR_OPERATOR_FORMULATION_A":405.0,
            "FAIR_OPERATOR_FORMULATION_B":98.0,
            "ratio_A_over_B":405.0/98.0,
            "not_a_converged_reology_fit":True},
        "G2_material_coefficients":None,
        "G3_north_cut":None, "G3_south_cut":None,
        "G3_basal_normal_support":None,
        "mechanical_solve_authorized":False,
        "first_deforming_T1":None,
        "solver_runs":0,
        "requires_authorial_decision":[
            "G2 effective constitutive coefficients, water pressure, brittle cap",
            "G3 physically justified width/resolution and time window",
            "G3 external continuation or justified tractions across N/S cuts",
            "G3 physical basal normal support and tangential decoupling validity",
        ],
    }
    output.mkdir(parents=True)
    (output/"NEIGHBORHOOD.json").write_bytes(_json(report))
    (output/"REGIONAL_16.feg").write_text(raw)
    manifest = {
        "schema":"ARCANA_R6_PLATE58_G3_NEIGHBOR_MANIFEST_V1",
        "status":STATUS,
        "source_case_sha256":report["input_four_cell_sha256"],
        "files":{name:sha(output/name) for name in ("NEIGHBORHOOD.json","REGIONAL_16.feg")},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True,
    }
    (output/"MANIFEST.json").write_bytes(_json(manifest))
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous_stage",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    result=prepare_envelope(args.previous_stage,args.output)
    print(json.dumps({"status":result["status"],
                      "parent_triangles":len(result["parent_triangle_ids"]),
                      "source_contact_segments":result["boundary_analysis"]["source_contact_count"],
                      "north_owners":result["boundary_analysis"]["side_plate_ownership"]["north"],
                      "south_owners":result["boundary_analysis"]["side_plate_ownership"]["south"],
                      "mechanical_solve_authorized":False},indent=2))
