"""G3 A explicit external-cut and basal-shear force weak form (engineering only).

No real traction provider, GPE partition, basal law or material is supplied.
Finite-element *load* algebra can be tested before these authorities exist.

Consistent P1 endpoint/vertex traction interpolation uses faceted chord
edge length and faceted triangle area, matching spherical_exterior's discrete
membrane geometry. Nodal DOFs remain local East/North at original parent IDs.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian, spherical_triangle_geometry,
)
from experiments.plate58_deforming_explore_v1.prepare import _json, sha

SYNTHETIC_GPE_OWNER = "SYNTHETIC_NO_GPE__NOT_A_PHYSICAL_GPE_CLOSURE"
ENGINEERING_AUTHORITY = "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED"
STATUS = "PASS_G3_A_FORCE_SOURCE_INVENTORY__LOAD_PHYSICS_UNRESOLVED"


class ForceInputError(ValueError):
    pass


def require(cond, tag):
    if not cond:
        raise ForceInputError(tag)


def edge_key(nodes):
    seq = list(map(int, nodes))
    require(len(seq) == 2 and seq[0] != seq[1] and all(n>0 for n in seq),
            "G3_A_FORCE_EDGE_KEY_INVALID")
    return ":".join(map(str, sorted(seq)))


def _validated_traction(entry, node_unit, n_nodes, kind):
    require(isinstance(entry, dict)
            and entry.get("authority") == ENGINEERING_AUTHORITY
            and isinstance(entry.get("source_reference"), str)
            and len(entry["source_reference"].strip()) >= 10,
            "G3_A_FORCE_PHYSICAL_PROVENANCE_MISSING")
    if kind == "line":
        data=entry.get("nodal_xyz_N_per_m")
    else:
        data=entry.get("nodal_xyz_N_per_m2")
    require(data is not None, "G3_A_FORCE_MISSING_TRACTION_FIELD")
    try:
        tr=np.asarray(data,dtype=float)
    except (TypeError,ValueError) as exc:
        raise ForceInputError("G3_A_FORCE_INVALID_TRACTION_ARRAY") from exc
    require(tr.shape==(n_nodes,3) and np.all(np.isfinite(tr)),
            "G3_A_FORCE_INVALID_TRACTION_ARRAY")
    norms=np.linalg.norm(tr,axis=1)
    radial=np.abs(np.einsum("ij,ij->i",tr,node_unit))
    require(np.all(radial <= 1e-10*np.maximum(norms,1e-100)),
            "G3_A_FORCE_NON_TANGENTIAL_SHEAR_INPUT")
    return tr


def assemble_explicit_g3_loads(node_order, node_lat_lon,
                               source_cut_edges, line_tractions_by_edge,
                               exterior_triangles, basal_tractions_by_triangle,
                               *, gpe_ownership, velocity_en_by_node=None):
    """Consistent external and basal nodal loads, explicit source-ledger only.

    All edge and basal forces MUST be provided, even if a zero-valued synthetic
    test. Such zeros are NEVER default physical ARCANA far-field conditions.
    Returns a load vector, net 3D resultant/torque, and virtual power when
    velocities are supplied. Does not claim force equilibrium or a solve.
    """
    require(gpe_ownership == SYNTHETIC_GPE_OWNER,
            "G3_A_GPE_OWNERSHIP_NOT_CLOSED_OR_UNAUTHORIZED")
    ids=list(map(int,node_order))
    require(len(ids)>=3 and len(set(ids))==len(ids) and all(i>0 for i in ids),
            "G3_A_FORCE_DUPLICATE_PARENT_MECHANICAL_DOF")
    loc={int(k):v for k,v in node_lat_lon.items()}
    require(set(loc)==set(ids), "G3_A_FORCE_SOURCE_LATLON_COVERAGE")
    latlon=np.asarray([loc[n] for n in ids],dtype=float)
    xyz,radial,east,north=frames_and_cartesian(latlon)
    require(np.all(np.isfinite(latlon)), "G3_A_FORCE_SOURCE_COORDINATES_INVALID")
    pos={n:i for i,n in enumerate(ids)}
    fline=np.zeros((len(ids),2))
    fbase=np.zeros((len(ids),2))
    cuts={}
    for row in source_cut_edges:
        edge=row["source_parent_node_ids"]
        key=edge_key(edge)
        require(key not in cuts and all(int(n) in pos for n in edge)
                and row["side"] in ("north","south","east","west")
                and isinstance(row["adjacent_plate_id"],int),
                "G3_A_FORCE_CUT_SOURCE_INVENTORY_INVALID")
        cuts[key]=row
    provided={str(k):v for k,v in line_tractions_by_edge.items()}
    require(set(provided)==set(cuts) and len(cuts)>0,
            "G3_A_FORCE_ALL_EXTERNAL_CUT_TRACTIONS_REQUIRED")
    max_edge_deficit=0.
    for key,source in cuts.items():
        a,b=[int(n) for n in source["source_parent_node_ids"]]
        ia,ib=pos[a],pos[b]
        trdata=provided[key]
        require(trdata.get("source_parent_node_ids")==[a,b]
                and trdata.get("side")==source["side"]
                and trdata.get("adjacent_plate_id")==source["adjacent_plate_id"]
                and trdata.get("force_channel")=="EXTERIOR_BOUNDARY",
                "G3_A_FORCE_BOUNDARY_OWNER_OR_ORIENTATION_INVALID")
        t=_validated_traction(trdata,radial[[ia,ib]],2,"line")
        chord=float(np.linalg.norm(xyz[ib]-xyz[ia]))
        angle=math.atan2(float(np.linalg.norm(np.cross(radial[ia],radial[ib]))),
                         float(radial[ia]@radial[ib]))
        arc=angle*float(np.linalg.norm(xyz[ia]))
        require(chord>0 and arc>0,"G3_A_FORCE_SOURCE_EDGE_DEGENERATE")
        max_edge_deficit=max(max_edge_deficit,1-chord/arc)
        load_a=(chord/6.)*(2*t[0]+t[1])
        load_b=(chord/6.)*(t[0]+2*t[1])
        fline[ia]+=np.array([east[ia]@load_a,north[ia]@load_a])
        fline[ib]+=np.array([east[ib]@load_b,north[ib]@load_b])

    faces={int(tid):tuple(map(int,values))
           for tid,values in exterior_triangles.items()}
    loads={int(tid):v for tid,v in basal_tractions_by_triangle.items()}
    require(faces and set(faces)==set(loads) and
            all(len(v)==3 and len(set(v))==3 and
                all(n in pos for n in v) for v in faces.values()),
            "G3_A_FORCE_ALL_BASAL_TRIANGLE_TRACTIONS_REQUIRED")
    area_total=0.
    for tid, verts in sorted(faces.items()):
        positions=[pos[n] for n in verts]
        entry=loads[tid]
        require(entry.get("parent_triangle_id")==tid
                and entry.get("parent_node_ids")==list(verts)
                and entry.get("force_channel")=="BASAL_TANGENTIAL",
                "G3_A_FORCE_BASAL_OWNER_OR_ORIENTATION_INVALID")
        tr=_validated_traction(entry,radial[positions],3,"basal")
        geo=spherical_triangle_geometry(latlon[positions])
        area=float(geo["facet_area_m2"])
        area_total+=area
        tsum=np.sum(tr,axis=0)
        for i,p in enumerate(positions):
            load=(area/12.)*(tsum+tr[i])
            fbase[p]+=np.array([east[p]@load,north[p]@load])
    f=fline+fbase
    fxyz=east*f[:,0,None]+north*f[:,1,None]
    resultant=np.sum(fxyz,axis=0)
    torque=np.sum(np.cross(xyz,fxyz),axis=0)
    virtual_power=None
    if velocity_en_by_node is not None:
        vel={int(k):v for k,v in velocity_en_by_node.items()}
        require(set(vel)==set(ids),"G3_A_FORCE_VELOCITY_PARENT_DOF_COVERAGE")
        u=np.asarray([vel[n] for n in ids],dtype=float)
        require(u.shape==(len(ids),2) and np.all(np.isfinite(u)),
                "G3_A_FORCE_VELOCITY_INVALID")
        virtual_power=float(np.sum(f*u))
    return {
        "candidate_external_line_force_N":fline.ravel(),
        "candidate_basal_tangential_force_N":fbase.ravel(),
        "candidate_total_nodal_force_N":f.ravel(),
        "source_node_order":ids,
        "global_force_xyz_N":resultant,
        "global_torque_xyz_N_m":torque,
        "virtual_power_W_if_velocity_supplied":virtual_power,
        "external_cut_edges_count":len(cuts),
        "basal_triangles_count":len(faces),
        "facet_basal_area_m2":area_total,
        "maximum_chord_arc_relative_deficit":max_edge_deficit,
        "gpe_accounting":"NOT_MODELED_IN_SYNTHETIC_KERNEL",
        "resultant_or_torque_balanced":False,
        "physical_traction_laws_source_qualified":False,
        "mechanical_solve_authorized":False,
        "physical_T1":None}


def source_force_requirements(multiscale_dir:Path, interface_dir:Path,
                              nodal_dir:Path, output:Path):
    """Read-only physical provider inventory, pins prior verified FAIR sources.

    Does not accept nor create any force values. The 5/8/11 source contact
    node 34587 is retained. All G3 physical force/basal and GPE fields null.
    """
    require(not output.exists(),"G3_A_FORCE_OUTPUT_ALREADY_EXISTS")
    filenames=("CONTINUATION_A.json","MULTISCALE_INTERFACE.json",
               "SOURCE_NODAL_ELEMENT_G2.json")
    folders=(multiscale_dir,interface_dir,nodal_dir)
    expected=(
        "PASS_G3_A_MULTISCALE_SOURCE_CONTINUATION__BC_AND_G2_UNRESOLVED",
        "PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED",
        "PASS_G2_SOURCE_NODAL_ELEMENT_BINDING__CONSTITUTIVE_AND_G3_FORCING_OPEN")
    artifacts=[]
    for folder, name, status in zip(folders,filenames,expected,strict=True):
        manifest=json.loads((folder/"MANIFEST.json").read_text())
        row=json.loads((folder/name).read_text())
        require(manifest["status"]==row["status"]==status and
                manifest["no_solver_run"] and manifest["no_T1"] and
                manifest["no_canonical_promotion"] and name in manifest["files"]
                and all(sha(folder/f)==h for f,h in manifest["files"].items()),
                "G3_A_FORCE_UPSTREAM_EVIDENCE_INVALID")
        artifacts.append(row)
    a,b,c=artifacts
    require(b["source_multiscale_manifest_sha256"]==
            sha(multiscale_dir/"MANIFEST.json") and
            c["source_multiscale_manifest_sha256"]==
            sha(multiscale_dir/"MANIFEST.json") and
            c["source_interface_manifest_sha256"]==
            sha(interface_dir/"MANIFEST.json"),
            "G3_A_FORCE_UPSTREAM_CHAIN_MISMATCH")
    regions={x["cell_extent_per_side"]:x
             for x in a["topological_comparative_extents"]}
    interfaces={x["extent_cells_per_side"]:x for x in b["scales"]}
    nodal={x["extent_cells"]:x for x in c["scales"]}
    require(set(regions)==set(interfaces)==set(nodal)=={8,16}
            and c["source_node_34587_PRE_record"]["node_id"]==34587
            and not c["mechanical_solve_authorized"],
            "G3_A_FORCE_UPSTREAM_SOURCE_COVERAGE_CHANGED")
    payload=[]
    for width in (8,16):
        region, inter, sources=regions[width],interfaces[width],nodal[width]
        edges=[]
        for side in ("north","south","west","east"):
            for e in region["outer_cut_edges"][side]:
                key=edge_key(e["source_parent_node_ids"])
                edges.append({
                    "source_edge_id":key,"side":side,
                    "source_parent_node_ids":e["source_parent_node_ids"],
                    "adjacent_plate_id":e["single_adjacent_plate_id"],
                    "physical_cut_traction_xyz_N_per_m":None,
                    "physical_mechanical_provider":None})
        require(len(edges)==4*width and
                len({e["source_edge_id"] for e in edges})==len(edges),
                "G3_A_FORCE_DUPLICATED_OR_MISSING_SOURCE_CUT")
        plate_by_triangle=dict(zip(map(int,region["parent_triangle_ids"]),
                                   map(int,region["parent_triangle_plate_ids"]),
                                   strict=True))
        triangles=[]
        for tid, data in sources["exterior_triangles"].items():
            t=int(tid)
            require(t in plate_by_triangle and
                    t in inter["source_exterior_triangles"],
                    "G3_A_FORCE_PARENT_TRIANGLE_DRIFT")
            triangles.append({
                "source_parent_triangle_id":t,
                "source_parent_node_ids":data["parent_node_ids"],
                "source_plate_id":plate_by_triangle[t],
                "physical_basal_shear_xyz_N_per_m2":None,
                "GPE_contribution_owner":None,
                "physical_provider":None})
        require(len(triangles)==2*width**2-8
                and len({x["source_parent_triangle_id"]
                         for x in triangles})==len(triangles),
                "G3_A_FORCE_BASAL_TRIANGLE_SOURCE_INCOMPLETE")
        payload.append({
            "extent_cells":width,
            "contact_graph_by_plate_pair":inter["contact_graph_by_plate_pair"],
            "triple_plate_junctions":inter["actual_3plus_plate_junctions"],
            "source_plates":inter["plate_ids_present"],
            "source_external_cut_edges":edges,
            "source_exterior_triangles_requiring_basal_provider":triangles,
            "external_cut_edge_count":len(edges),
            "basal_triangle_count":len(triangles),
            "source_interface_nodes":inter["source_interface_node_ids"],
            "G2_material_provider":None,
            "GPE_single_owner":None,
            "G3_A_NS_traction_provider":None,
            "G3_A_basal_shear_and_normal_provider":None,
            "force_torque_work_physical_closure":None,
            "physical_force_vector":None})
    result={
        "schema":"ARCANA_R6_G3_A_SOURCE_BOUND_FORCE_BUDGET_REQUIREMENTS_V1",
        "status":STATUS,
        "parent_multiscale_manifest_sha256":sha(multiscale_dir/"MANIFEST.json"),
        "parent_interface_manifest_sha256":sha(interface_dir/"MANIFEST.json"),
        "parent_G2_binding_manifest_sha256":sha(nodal_dir/"MANIFEST.json"),
        "exact_triple_node_id":34587,
        "scales":payload,
        "GPE_duplicate_count_excluded":None,
        "physical_material_model":None,
        "physical_load_forcing":None,
        "force_balance_qualified":False,
        "no_real_traction_inferred":True,
        "mechanical_solve_authorized":False,"solver_runs":0,
        "physical_T1":None}
    output.mkdir(parents=True,exist_ok=False)
    file=output/"FORCE_BUDGET_REQUIREMENTS.json"
    file.write_bytes(_json(result))
    (output/"MANIFEST.json").write_bytes(_json({
        "schema":"ARCANA_R6_G3_A_FORCE_BUDGET_REQUIREMENTS_MANIFEST_V1",
        "status":STATUS,"files":{file.name:sha(file)},
        "no_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True}))
    return {
        "status":STATUS,
        "scales":[{
            "extent":r["extent_cells"],
            "outer_cut_edges":r["external_cut_edge_count"],
            "basal_exterior_triangles":r["basal_triangle_count"],
            "plates":r["source_plates"],
            "actual_three_plate_junctions":len(r["triple_plate_junctions"])}
            for r in payload],
        "mechanical_solve_authorized":False,
        "solver_runs":0,"physical_T1":None}


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("multiscale",type=Path)
    ap.add_argument("mechanical_interface",type=Path)
    ap.add_argument("G2_nodal_source",type=Path)
    ap.add_argument("output",type=Path)
    p=ap.parse_args()
    print(json.dumps(source_force_requirements(
        p.multiscale,p.mechanical_interface,p.G2_nodal_source,p.output),
        indent=2))
