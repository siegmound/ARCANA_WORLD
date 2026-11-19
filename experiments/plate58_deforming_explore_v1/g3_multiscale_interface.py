"""G3 A: source-exact multiscale exterior Schur interface, plate-11-aware.

Turns the verified 8x8/16x16 T0 FEG source domains into interface/node/DOF
partitions usable by an eventually *physically supplied* exterior mechanical
tangent. Reports actual contact pair graph and triple-plate junction IDs;
three plates in a domain does not by itself prove a triple junction.
No constitutive matrix, boundary load, mechanics solve, or canonical T1.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.prepare import _json, require, sha
from experiments.plate58_deforming_explore_v1.continuation_A import (
    SCHEMA as PARENT_SCHEMA, STATUS as PARENT_STATUS,
)
from experiments.plate58_deforming_explore_v1.coupling_A import (
    EXPECTED_APPROVAL, STATUS as COUPLING_STATUS,
)

STATUS = "PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED"
SCHEMA = "ARCANA_R6_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH_V1"
SIDES = ("north", "south", "west", "east")
SIZES = (8, 16)


def _edges(triangle):
    a, b, c = map(int, triangle)
    require(len({a, b, c}) == 3, "G3_A_DEGENERATE_SOURCE_TRIANGLE")
    return (tuple(sorted((a, b))), tuple(sorted((b, c))),
            tuple(sorted((c, a))))


def derive_external_interface(region: dict, feg, core_triangles,
                              core_perimeter_edges, core_interface_nodes,
                              core_only_nodes):
    """Contract from original parent IDs; accepts 3+ plate ownership.

    Exact-interface DOFs appear first, followed by all exterior-only nodes.
    The core center is excluded from the exterior Schur stiffness.
    """
    width = int(region["cell_extent_per_side"])
    require(width in SIZES, "G3_A_UNSUPPORTED_EXTENT")
    nodes = [int(n) for n in region["parent_node_ids"]]
    triangles = [int(t) for t in region["parent_triangle_ids"]]
    plates = [int(p) for p in region["parent_triangle_plate_ids"]]
    require(len(nodes) == (width+1)**2 and len(set(nodes)) == len(nodes)
            and len(triangles) == len(plates) == 2*width**2
            and len(set(triangles)) == len(triangles)
            and len(feg.nodes) == len(nodes) and len(feg.elements) == len(triangles)
            and not feg.faults, "G3_A_MULTISCALE_SOURCE_INVENTORY_INVALID")
    require([int(n.node_id) for n in feg.nodes] == list(range(1,len(nodes)+1)),
            "G3_A_LOCAL_NODE_ORDER_CHANGED")
    source_faces = {}
    incidence = defaultdict(list)
    node_owner = defaultdict(set)
    for tid, plate, element in zip(triangles, plates, feg.elements, strict=True):
        local_ids = [int(n) for n in element.node_ids]
        require(all(1<=n<=len(nodes) for n in local_ids),
                "G3_A_PARENT_NODE_INDEX_INVALID")
        parent_nodes = tuple(nodes[n-1] for n in local_ids)
        require(tid not in source_faces, "G3_A_DUPLICATED_PARENT_TRIANGLE")
        source_faces[tid] = parent_nodes
        for n in parent_nodes:
            node_owner[n].add(plate)
        for edge in _edges(parent_nodes):
            incidence[edge].append((tid,plate))
    require(all(1<=len(rows)<=2 for rows in incidence.values()) and
            set(node_owner)==set(nodes), "G3_A_NONMANIFOLD_OR_UNUSED_PARENT_NODE")

    core=set(map(int,core_triangles))
    interface=set(map(int,core_interface_nodes))
    center=set(map(int,core_only_nodes))
    core_edges={tuple(sorted(map(int,edge))) for edge in core_perimeter_edges}
    require(len(core)==8 and len(interface)==8 and len(center)==1
            and len(core_edges)==8 and core.issubset(source_faces)
            and interface.isdisjoint(center)
            and interface.union(center).issubset(nodes),
            "G3_A_SOURCE_CORE_BINDING_CHANGED")
    cfaces={tid:face for tid,face in source_faces.items() if tid in core}
    assert len(cfaces)==8
    counts=Counter(edge for face in cfaces.values() for edge in _edges(face))
    actual_core_edges={edge for edge,count in counts.items() if count==1}
    require(actual_core_edges==core_edges and
            {n for edge in actual_core_edges for n in edge}==interface,
            "G3_A_CORE_CONTACT_PERIMETER_MISMATCH")
    external={tid:face for tid,face in source_faces.items() if tid not in core}
    require(len(external)==2*width**2-8, "G3_A_EXTERIOR_TRIANGLE_COUNT_INVALID")
    exterior_edge_uses=Counter(edge for face in external.values()
                               for edge in _edges(face))
    require(all(exterior_edge_uses[edge]==1 for edge in core_edges)
            and all(len(incidence[edge])==2 for edge in core_edges),
            "G3_A_OUTER_NOT_CONNECTED_TO_CORE")
    outer_nodes={n for face in external.values() for n in face}
    require(outer_nodes==set(nodes)-center and interface.issubset(outer_nodes),
            "G3_A_EXTERIOR_NODE_COVERAGE_INVALID")
    exterior_only=sorted(outer_nodes-interface)
    order=sorted(interface)+exterior_only
    require(len(order)==len(nodes)-1 and len(exterior_only)==len(nodes)-9
            and len(set(order))==len(order),
            "G3_A_INTERFACE_EXTERIOR_ORDER_INVALID")

    contacts={}
    for edge,rows in incidence.items():
        if len(rows)==2 and rows[0][1]!=rows[1][1]:
            contacts[edge]=tuple(sorted({int(p) for _,p in rows}))
    written={}
    for row in region["source_contact_edges"]:
        edge=tuple(sorted(map(int,row["source_edge_node_ids"])))
        pair=tuple(sorted(map(int,row["plate_pair"])))
        ident=row["source_boundary_id"]
        require(edge not in written and isinstance(ident,str)
                and ident.startswith("R6BND-T0-"),
                "G3_A_CONTACT_BOUNDARY_PROVENANCE_INVALID")
        written[edge]=(pair,ident)
    require(len(contacts)==len(written)==region["source_contact_count"]
            and all(edge in written and pair==written[edge][0]
                    for edge,pair in contacts.items()),
            "G3_A_CONTACT_PAIR_GRAPH_CHANGED")
    contact_counts=Counter(contacts.values())
    node_junctions=[
        {"parent_node_id":n,"incident_plates":sorted(owners)}
        for n,owners in sorted(node_owner.items()) if len(owners)>=3]
    # A plate's inclusion alone is not proof of an exact triple junction.
    if width==16:
        require(11 in set(plates), "G3_A_PLATE_11_MISSING_IN_16X16")
    for side in SIDES:
        entries=region["outer_cut_edges"][side]
        require(len(entries)==width, "G3_A_CUT_EDGE_INVENTORY_CHANGED")
        for row in entries:
            edge=tuple(sorted(map(int,row["source_parent_node_ids"])))
            require(edge in incidence and len(incidence[edge])==1
                    and int(row["single_adjacent_plate_id"])==incidence[edge][0][1]
                    and row["prescribed_velocity"] is None
                    and row["physical_traction"] is None,
                    "G3_A_UNAUTHORIZED_OR_MISMATCHED_EXTERNAL_CUT")
        expected={
            n for row in entries for n in map(int,row["source_parent_node_ids"])
            if len(node_owner[n])>1}
        actual={int(item["parent_node_id"]) for item
                in region["ambiguous_outer_cut_nodes"][side]}
        require(expected==actual and all(
            sorted(map(int,item["incident_plate_ids"]))==
            sorted(node_owner[int(item["parent_node_id"])])
            for item in region["ambiguous_outer_cut_nodes"][side]),
            "G3_A_AMBIGUOUS_CUT_OWNER_MISMATCH")
    pair_rows=[
        {"plate_pair":list(pair),"source_contact_edge_count":count}
        for pair,count in sorted(contact_counts.items())]
    require(sum(row["source_contact_edge_count"] for row in pair_rows)
            ==region["source_contact_count"], "G3_A_CONTACT_TOTAL_NOT_CONSERVED")
    require([5,8] in [x["plate_pair"] for x in pair_rows],
            "G3_A_ORIGINAL_PLATE_CONTACT_LOST")
    return {
        "extent_cells_per_side":width,
        "plate_ids_present":sorted(set(plates)),
        "triangles_total":len(triangles),
        "triangles_exterior":len(external),
        "source_interface_node_ids":sorted(interface),
        "source_core_only_node_ids":sorted(center),
        "source_exterior_only_node_ids":exterior_only,
        "source_exterior_triangles":sorted(external),
        "source_interface_edges":[list(edge) for edge in sorted(core_edges)],
        "mechanical_node_order_interface_first":order,
        "velocity_dof_count":2*len(order),
        "interface_dof_indices":list(range(2*len(interface))),
        "external_dof_indices":list(range(2*len(interface),2*len(order))),
        "contact_graph_by_plate_pair":pair_rows,
        "actual_3plus_plate_junctions":node_junctions,
        "triple_plate_junction_exists":any(
            len(item["incident_plates"])>=3 for item in node_junctions),
        "outer_cut_kinematic_ambiguities":{
            side:region["ambiguous_outer_cut_nodes"][side] for side in SIDES},
        "physical_mechanical_tangent":None,
        "physical_mechanical_force":None,
        "far_field_kinematics_are_only_priors":True,
        "g3_11_boundary_provider":None,
        "source_geometry_is_not_physical_mesh_convergence":True,
        "no_shared_node_duplicated_as_physical_DOF":True,
        "G2_effective_material":None,"GPE_basal_force_balance":None,
        "mechanical_solve_authorized":False,
        "physical_T1":None,
    }


def build(multiscale_dir:Path,coupling_dir:Path,output:Path):
    require(not output.exists(),"G3_A_OUTPUT_ALREADY_EXISTS")
    prior=json.loads((multiscale_dir/"MANIFEST.json").read_text())
    context=json.loads((multiscale_dir/"CONTINUATION_A.json").read_text())
    require(prior["status"]==context["status"]==PARENT_STATUS
            and context["schema"]==PARENT_SCHEMA
            and prior["no_solver_run"] and prior["no_T1"]
            and prior["no_canonical_promotion"],
            "G3_A_PARENT_CONTINUATION_NOT_QUALIFIED")
    require("CONTINUATION_A.json" in prior["files"]
            and all(sha(multiscale_dir/name)==digest
                    for name,digest in prior["files"].items()),
            "G3_A_PARENT_CONTINUATION_MEMBER_HASH_MISMATCH")
    require(context["source_coupling_manifest_sha256"]==
            sha(coupling_dir/"MANIFEST.json")
            and context["G3_A_physically_calibrated_tangent"] is None
            and not context["mechanical_solve_authorized"],
            "G3_A_PARENT_COUPLING_OR_SOLVE_CHANGED")
    cm=json.loads((coupling_dir/"MANIFEST.json").read_text())
    require(cm["status"]==COUPLING_STATUS and
            cm["no_solver_run"] and cm["no_T1"] and
            cm["no_canonical_promotion"] and
            all(sha(coupling_dir/name)==digest for name,digest in cm["files"].items()),
            "G3_A_COUPLING_MANIFEST_FAILED")
    geometry=json.loads((coupling_dir/"GEOMETRY.json").read_text())
    coupling=json.loads((coupling_dir/"G3_A_TRANSFER_CONTRACT.json").read_text())
    require(geometry["source_mesh_identity_sha256"]==
            context["source_mesh_sha256"] and
            coupling["architecture"]==EXPECTED_APPROVAL and
            coupling["actual_interface_tangent"] is None and
            coupling["actual_effective_load"] is None and
            coupling["mechanical_solve_authorized"] is False,
            "G3_A_TRANSFER_PROVENANCE_OR_AUTHORITY_CHANGED")
    core=geometry["geometry"]
    reports=[]
    expected_files=set()
    for region in context["topological_comparative_extents"]:
        size=int(region["cell_extent_per_side"])
        require(size in SIZES and size not in {r["extent_cells_per_side"]
                                               for r in reports},
                "G3_A_EXTENT_DUPLICATION_OR_UNEXPECTED")
        p=multiscale_dir/f"OUTER_A_{size:02d}x{size:02d}.feg"
        pre=multiscale_dir/f"OUTER_A_{size:02d}x{size:02d}_PRE_T0_PASSIVE.dat"
        require(p.is_file() and pre.is_file() and
                sha(p)==region["output_FEG_sha256"] and
                sha(pre)==region["output_PRE_sha256"],
                "G3_A_FEG_PRE_ARTIFACTS_SOURCE_MISMATCH")
        expected_files.update((p.name,pre.name))
        mesh=parse_feg(p.read_text(),mode="SHELLS_READY")
        item=derive_external_interface(
            region,mesh,core["source_core_parent_triangle_ids"],
            core["interface_parent_edges"],
            core["parent_interface_nodes"],
            core["parent_core_only_nodes"])
        reports.append(item)
    require(set(item["extent_cells_per_side"] for item in reports)==set(SIZES)
            and set(prior["files"])==expected_files|{"CONTINUATION_A.json"},
            "G3_A_NESTED_DOMAIN_INVENTORY_INCOMPLETE")
    assert reports[0]["source_interface_node_ids"]==reports[1]["source_interface_node_ids"]
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_multiscale_manifest_sha256":sha(multiscale_dir/"MANIFEST.json"),
        "source_coupling_manifest_sha256":sha(coupling_dir/"MANIFEST.json"),
        "source_mesh_sha256":context["source_mesh_sha256"],
        "source_PRE_sha256":context["source_PRE_sha256"],
        "source_vector_partition_sha256":context["source_vector_partition_sha256"],
        "architecture":"EXTERIOR_CONTINUUM_MECHANICAL_TRANSFER_A",
        "one_mechanical_source_node_per_interface_DOF":True,
        "scales":reports,
        "material_model_G2":None,
        "physically_assembled_tangent_by_scale":None,
        "physically_assembled_load_by_scale":None,
        "G3_A_normal_basal_balance":None,
        "G3_A_tangential_basal_balance":None,
        "GPE_nonduplicated":None,
        "source_scope":"PRE_T0_GEOMETRY_AND_CONTACT_TOPOLOGY_ONLY",
        "physical_mesh_or_domain_convergence_qualified":False,
        "mechanical_solve_authorized":False,"solver_runs":0,
        "physical_T1":None}
    output.mkdir(parents=True,exist_ok=False)
    (output/"MULTISCALE_INTERFACE.json").write_bytes(_json(report))
    (output/"MANIFEST.json").write_bytes(_json({
        "schema":"ARCANA_R6_G3_A_MULTISCALE_MECHANICAL_INTERFACE_MANIFEST_V1",
        "status":STATUS,
        "source_multiscale_manifest_sha256":report["source_multiscale_manifest_sha256"],
        "source_coupling_manifest_sha256":report["source_coupling_manifest_sha256"],
        "files":{"MULTISCALE_INTERFACE.json":sha(output/"MULTISCALE_INTERFACE.json")},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True}))
    return {"status":STATUS,"scales":[{
        "extent":r["extent_cells_per_side"],
        "plate_ids":r["plate_ids_present"],
        "dof_count":r["velocity_dof_count"],
        "contact_graph":r["contact_graph_by_plate_pair"],
        "actual_3plus_plate_junction_count":len(r["actual_3plus_plate_junctions"]),
        "source_interface_nodes":len(r["source_interface_node_ids"])}
        for r in reports],
        "physical_tangent":None,
        "mechanical_solve_authorized":False,"solver_runs":0,"physical_T1":None}


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("multiscale",type=Path)
    ap.add_argument("coupling",type=Path)
    ap.add_argument("output",type=Path)
    a=ap.parse_args()
    print(json.dumps(build(a.multiscale,a.coupling,a.output),indent=2))
