"""R6 authentic plate-owned triangle-patch topology and orientation audit.

ENGINEERING_ONLY and SOURCE_READ_ONLY. This inventory is NOT a signed
solid-contact gap, no manufactured extrusion, no updated geometry Signorini.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, sha256, source_inputs, usage, RADIUS_M,
)
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry, assemble_split_source, euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time import (
    normal_constraint_matrix, integrate,
)
from experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel import (
    rigid_motion_with_residual, certify_priors,
)
from experiments.plate58_deforming_explore_v1.g2_t0_normal_segment_jacobian import (
    closest_segments,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    SparseP1Error,
)

SCHEMA="ARCANA_R6_G2_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_AUDIT_V1"
STATUS="PASS_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_AUDIT__CLOSED_SOLID_CONTACT_UNPROVEN"
YEARS=(100,500,1000)


def need(value,label):
    if not value:
        raise SparseP1Error(label)


def normalize(v,label):
    v=np.asarray(v,dtype=np.float64)
    size=float(np.linalg.norm(v))
    need(v.shape==(3,) and np.all(np.isfinite(v))
         and math.isfinite(size) and size>1e-12,label)
    return v/size


def source_face_incidence(faces,plates,source_edges):
    """Each genuine R6BND edge must have exactly two original owner faces."""
    incidence=defaultdict(list)
    for face,owner in zip(faces,plates,strict=True):
        face=tuple(map(int,face))
        need(len(face)==3 and len(set(face))==3,
             "SURFACE_SOURCE_TRIANGLE_DEGENERATE")
        for a,b in ((face[0],face[1]),(face[1],face[2]),(face[2],face[0])):
            incidence[tuple(sorted((a,b)))].append((int(owner),face))
    ids=set()
    result=[]
    for source in sorted(source_edges,key=lambda r:r["source_boundary_id"]):
        edge=tuple(sorted(map(int,source["source_edge_node_ids"])))
        pair=tuple(sorted(map(int,source["plate_pair"])))
        bid=source["source_boundary_id"]
        need(bid not in ids and isinstance(bid,str)
             and bid.startswith("R6BND-T0-"),
             "SURFACE_SOURCE_ID_DUPLICATE_OR_INVALID")
        ids.add(bid)
        owners=incidence.get(edge,[])
        need(len(owners)==2
             and {p for p,_ in owners}==set(pair),
             "SURFACE_SOURCE_FACE_OWNER_MISMATCH")
        by_plate={p:face for p,face in owners}
        need(all(len(set(by_plate[p])-set(edge))==1 for p in pair),
             "SURFACE_SOURCE_FACE_THIRD_VERTEX_INVALID")
        result.append({
            "source_boundary_id":bid,
            "source_edge_node_ids":list(edge),
            "plate_pair":list(pair),
            "plate_p_original_triangle_node_ids":list(by_plate[pair[0]]),
            "plate_q_original_triangle_node_ids":list(by_plate[pair[1]]),
            "source_two_distinct_plate_faces":True,
        })
    need(len(result)==len(source_edges)>0,
         "SURFACE_SOURCE_FACE_INVENTORY_INCOMPLETE")
    return result


def triangle_patch_metrics(p_triangle,q_triangle,source_edge_p,source_edge_q):
    """Geometric orientation diagnostics for two OPEN source P1 facets.

    No closed volume boundary and no signed nonpenetration gap follows.
    Faces may have either source winding; record rather than silently flip.
    """
    p=np.asarray(p_triangle,dtype=float)
    q=np.asarray(q_triangle,dtype=float)
    ep=np.asarray(source_edge_p,dtype=float)
    eq=np.asarray(source_edge_q,dtype=float)
    need(p.shape==q.shape==(3,3) and ep.shape==eq.shape==(2,3)
         and all(np.all(np.isfinite(x)) for x in (p,q,ep,eq)),
         "SURFACE_PATCH_COORDINATES_INVALID")
    cross_p=np.cross(p[1]-p[0],p[2]-p[0])
    cross_q=np.cross(q[1]-q[0],q[2]-q[0])
    ap=float(np.linalg.norm(cross_p)/2)
    aq=float(np.linalg.norm(cross_q)/2)
    need(ap>1e-7 and aq>1e-7,"SURFACE_PATCH_DEGENERATE_FACET")
    np_raw=normalize(cross_p,"SURFACE_FACET_P_NORMAL_INVALID")
    nq_raw=normalize(cross_q,"SURFACE_FACET_Q_NORMAL_INVALID")
    rp=normalize(np.mean(p,axis=0),"SURFACE_FACET_P_RADIAL_INVALID")
    rq=normalize(np.mean(q,axis=0),"SURFACE_FACET_Q_RADIAL_INVALID")
    dot_p=float(np_raw@rp)
    dot_q=float(nq_raw@rq)
    def conormal(triangle,edge):
        edge_vector=normalize(edge[1]-edge[0],
                              "SURFACE_BOUNDARY_EDGE_DEGENERATE")
        remaining=[]
        for x in triangle:
            if min(float(np.linalg.norm(x-e)) for e in edge)>1e-7:
                remaining.append(x)
        need(len(remaining)==1,
             "SURFACE_FACET_EDGE_THIRD_VERTEX_MATCH_INVALID")
        into=remaining[0]-np.mean(edge,axis=0)
        return normalize(into-(into@edge_vector)*edge_vector,
                         "SURFACE_FACET_INTERIOR_CONORMAL_INVALID")
    into_p=conormal(p,ep)
    into_q=conormal(q,eq)
    _,_,s,t,edge_dist=closest_segments(*ep,*eq)
    return {
        "facet_p_area_m2":ap,
        "facet_q_area_m2":aq,
        "facet_p_raw_winding_outward_radial_dot":dot_p,
        "facet_q_raw_winding_outward_radial_dot":dot_q,
        "facet_p_radially_outward_by_source_winding":dot_p>0,
        "facet_q_radially_outward_by_source_winding":dot_q>0,
        "raw_source_facet_normal_alignment":float(np_raw@nq_raw),
        "inward_face_conormal_alignment":float(into_p@into_q),
        "nearest_boundary_edge_unsigned_distance_m":edge_dist,
        "closest_edge_s":s,
        "closest_edge_t":t,
        "source_2D_open_sheet_facets_only":True,
        "source_owned_closed_solid_volume_proven":False,
        "qualified_signed_rock_contact_gap_m":None,
        "physical_contact_force_authorized":False,
    }


def objective_triangle_patch_check(p,q,ep,eq,original):
    Q=Rotation.from_rotvec([.4,-.7,.2]).as_matrix()
    rotated=triangle_patch_metrics(p@Q.T,q@Q.T,ep@Q.T,eq@Q.T)
    scalar_keys=(
        "facet_p_raw_winding_outward_radial_dot",
        "facet_q_raw_winding_outward_radial_dot",
        "raw_source_facet_normal_alignment",
        "inward_face_conormal_alignment",
    )
    orientation_error=max(abs(original[k]-rotated[k]) for k in scalar_keys)
    edge_error=abs(original["nearest_boundary_edge_unsigned_distance_m"]-
                   rotated["nearest_boundary_edge_unsigned_distance_m"])
    relative_area_error=max(
        abs(original[k]-rotated[k])/original[k]
        for k in ("facet_p_area_m2","facet_q_area_m2"))
    need(orientation_error<1e-9 and edge_error<1e-7
         and relative_area_error<1e-9,
         "SURFACE_TRIANGLE_PATCH_SO3_OBJECTIVITY_FAILED")
    return {
        "max_SO3_orientation_dot_error":orientation_error,
        "max_SO3_edge_distance_error_m":edge_error,
        "max_relative_SO3_facet_area_error":relative_area_error,
    }


def source_surface_patch_inventory(source_face_records,index,positions,
                                   prior_feature_rows,verify_SO3=True):
    priors={r["source_boundary_id"]:r for r in prior_feature_rows}
    need(len(priors)==len(source_face_records),
         "SURFACE_PRIOR_FEATURE_COUNT_MISMATCH")
    rows=[]
    for source in source_face_records:
        key=source["source_boundary_id"]
        need(key in priors,"SURFACE_PRIOR_FEATURE_ID_MISSING")
        a,b=source["source_edge_node_ids"]
        p,q=source["plate_pair"]
        t_p=source["plate_p_original_triangle_node_ids"]
        t_q=source["plate_q_original_triangle_node_ids"]
        P=np.asarray([positions[index[(p,n)]] for n in t_p])
        Q=np.asarray([positions[index[(q,n)]] for n in t_q])
        EP=np.asarray([positions[index[(p,n)]] for n in (a,b)])
        EQ=np.asarray([positions[index[(q,n)]] for n in (a,b)])
        geometry=triangle_patch_metrics(P,Q,EP,EQ)
        need(abs(geometry["nearest_boundary_edge_unsigned_distance_m"]-
                 priors[key]["unsigned_closest_segment_distance_m"])<1e-7,
             "SURFACE_PRIOR_FAIR_FEATURE_REPLAY_MISMATCH")
        geometry["SO3"]=objective_triangle_patch_check(
            P,Q,EP,EQ,geometry) if verify_SO3 else None
        geometry.update({
            "source_boundary_id":key,
            "source_edge_node_ids":[a,b],
            "plate_pair":[p,q],
            "plate_p_original_triangle_node_ids":t_p,
            "plate_q_original_triangle_node_ids":t_q,
            "original_feature_eligibility":priors[key]["classification"],
        })
        rows.append(geometry)
    need(len(rows)==len(source_face_records),"SURFACE_FACE_COVERAGE_INCOMPLETE")
    return {
        "source_faces_at_original_boundary":len(rows)*2,
        "source_edges":len(rows),
        "source_original_2D_open_sheet_faces_complete":True,
        "physically_closed_3D_volume_count":0,
        "qualified_signed_solid_contact_count":0,
        "face_winding_p_outward_count":sum(
            r["facet_p_radially_outward_by_source_winding"] for r in rows),
        "face_winding_q_outward_count":sum(
            r["facet_q_radially_outward_by_source_winding"] for r in rows),
        "source_feature_eligibility_counts":dict(Counter(
            r["original_feature_eligibility"] for r in rows)),
        "max_SO3_orientation_dot_error":max(
            r["SO3"]["max_SO3_orientation_dot_error"] for r in rows),
        "max_SO3_edge_distance_error_m":max(
            r["SO3"]["max_SO3_edge_distance_error_m"] for r in rows),
        "max_relative_SO3_facet_area_error":max(
            r["SO3"]["max_relative_SO3_facet_area_error"] for r in rows),
        "per_source_boundary_patch":rows,
    }


def run_region(width,multiscale,nodal,omegas,prior_region):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential,
    )
    mdir,ndir=Path(multiscale),Path(nodal)
    r=next(x for x in json.loads((mdir/"CONTINUATION_A.json").read_text())[
        "topological_comparative_extents"]
        if int(x["cell_extent_per_side"])==width)
    nod=next(x for x in json.loads((ndir/"SOURCE_NODAL_ELEMENT_G2.json").read_text())[
        "scales"] if int(x["extent_cells"])==width)
    ids=list(map(int,r["parent_node_ids"]))
    feg_path=mdir/f"OUTER_A_{width:02d}x{width:02d}.feg"
    pre_path=mdir/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
    need(sha256(feg_path)==r["output_FEG_sha256"]
         and sha256(pre_path)==r["output_PRE_sha256"],
         "SURFACE_SOURCE_FEG_PRE_SHA_CHANGED")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    pre=parse_regional_pre(pre_path,r["PRE_source_field_order"],ids)
    need({str(k):v for k,v in pre.items()}==
         {str(k):v for k,v in nod["source_PRE_by_parent_node"].items()},
         "SURFACE_NODAL_BINDING_CHANGED")
    for row in pre.values():
        validate_column_for_potential(row)
    ll={ids[i]:(float(n.latitude_deg),float(n.longitude_deg))
        for i,n in enumerate(feg.nodes)}
    faces=[tuple(ids[int(n)-1] for n in e.node_ids) for e in feg.elements]
    owners=list(map(int,r["parent_triangle_plate_ids"]))
    registry=contact_registry(ids,faces,owners,ll,r["source_contact_edges"])
    source_faces=source_face_incidence(
        faces,owners,r["source_contact_edges"])
    K,index,coords,plate_views,stats=assemble_split_source(
        ids,faces,owners,ll,pre)
    g=euler_source_en(coords,plate_views,omegas)
    J=normal_constraint_matrix(registry["contacts"],index,K.shape[0])
    xyz,radial,east,north=frames_and_cartesian(coords)
    zero=np.zeros(K.shape[0],dtype=float)
    pos,vel,R=rigid_motion_with_residual(
        xyz,east,north,plate_views,omegas,g,zero,g,0.)
    T0=source_surface_patch_inventory(
        source_faces,index,pos,
        prior_region["T0_feature_admissibility_inventory"][
            "source_original_feature_rows"])
    need(T0["source_edges"]==(12 if width==8 else 36)
         and registry["triple_junction_parent_ids"]==
            ([] if width==8 else [34587]),
         "SURFACE_SOURCE_SCOPE_OR_TRIPLE_INVALID")
    trajectory=integrate(K,J,g,1.,1000,checkpoints=YEARS)
    need(abs(trajectory["max_scaled_complementarity"])<1e-8,
         "SURFACE_PRIOR_T0_KKT_REPLAY_FAILED")
    checkpoints={}
    for year in YEARS:
        s=trajectory["snapshots"][year]
        p,velocity,rotations=rigid_motion_with_residual(
            xyz,east,north,plate_views,omegas,g,
            s["displacement"],s["velocity"],year)
        inv=source_surface_patch_inventory(
            source_faces,index,p,prior_region["checkpoints"][str(year)][
                "feature_admissibility_inventory"]["source_original_feature_rows"])
        checkpoints[str(year)]=inv
    return {
        "extent":width,
        "source_contact_links":len(registry["contacts"]),
        "source_original_boundary_edges":len(source_faces),
        "source_triple_parent_node_ids":registry["triple_junction_parent_ids"],
        "T0":T0,
        "checkpoints":checkpoints,
        "source_P1_open_triangle_facets_are_not_closed_solid_rock":True,
        "source_crust_thickness_PRE_does_not_define_extruded_face_topology":True,
        "signed_solid_nonpenetration_proved":False,
    }


def execute(multiscale,nodal,unilateral,prior_feature,out,root=ROOT):
    mdir,ndir,un,old,out,root=map(Path,(
        multiscale,nodal,unilateral,prior_feature,out,root))
    need(not out.exists(),"SURFACE_OUTPUT_ALREADY_EXISTS")
    began=time.perf_counter()
    source_pins=certify_priors(mdir,ndir,un,root)
    man=json.loads((old/"MANIFEST.json").read_text())
    prior=json.loads((old/"REPORT.json").read_text())
    need(man["schema"]=="ARCANA_R6_CONTACT_FEATURE_ADMISSIBILITY_MANIFEST_V1"
         and man["files"]["REPORT.json"]==sha256(old/"REPORT.json")
         and prior["status"]==
         "PASS_SOURCE_EDGE_FEATURE_ADMISSIBILITY_INVENTORY__PHYSICAL_CONTACT_OPEN"
         and prior["physical_T1"] is None
         and prior["D_024"]=="ACTIVE"
         and prior["engineered_contact_solver_runs"]==0,
         "SURFACE_PRIOR_FEATURE_REPORT_INVALID")
    for path,checksum in prior["source_sha256"].items():
        need(Path(path).is_file() and sha256(Path(path))==checksum,
             "SURFACE_PRIOR_SOURCE_PIN_CHANGED")
    # The pinned FAIR operator-reported previous report checksum is fixed,
    # not inferred from an arbitrary nearby artifact with the same status.
    need(sha256(old/"REPORT.json")==
         "e7b8f9c47bcd9f46a35f9edb06ee52ba641747f006482a1efc766f25b5b1fc21",
         "SURFACE_EXPECTED_FAIR_FEATURE_SHA_CHANGED")
    source_pins[str(old/"REPORT.json")]=sha256(old/"REPORT.json")
    source_pins[str(old/"MANIFEST.json")]=sha256(old/"MANIFEST.json")
    mesh,omegas,pins,horizon,pre=source_inputs(root)
    need(horizon>1000,"SURFACE_SOURCE_HORIZON_INSUFFICIENT")
    prior_regions={int(r["extent"]):r for r in prior["results"]}
    need(set(prior_regions)=={8,16},"SURFACE_PRIOR_REGION_SET_INVALID")
    results=[run_region(width,mdir,ndir,omegas,prior_regions[width])
             for width in (8,16)]
    need(all(sha256(Path(path))==checksum
             for path,checksum in source_pins.items()),
         "SURFACE_INPUT_MUTATED_DURING_AUDIT")
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_world_mesh_sha256":mesh.normalized_sha256,
        "source_sha256":source_pins,
        "results":results,
        "geometry_2D_open_P1_surface_only":True,
        "original_boundary_faces_paired_without_invented_faces":True,
        "no_closed_solid_boundary_surface_qualified":True,
        "physical_signed_surface_contact_gap_available":False,
        "moving_KKT_executed":False,
        "physical_solver_runs":0,
        "physical_T1":None,
        "D_024":"ACTIVE",
        "HistoryStore_modified":False,
        "canonical_promotion":False,
        "total_wall_seconds":time.perf_counter()-began,
        "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    report_file=out/"REPORT.json"
    report_file.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(report_file)},
        "physical_T1":None,"no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":STATUS,
        "regions":[{
            "extent":r["extent"],
            "source_edges":r["source_original_boundary_edges"],
            "triple":r["source_triple_parent_node_ids"],
            "summary_at_T0":{k:v for k,v in r["T0"].items()
                if k!="per_source_boundary_patch"},
            "at_years":{year:{
                k:v for k,v in section.items()
                if k!="per_source_boundary_patch"}
                for year,section in r["checkpoints"].items()},
        } for r in results],
        "total_wall_seconds":report["total_wall_seconds"],
        "physical_T1":None,
        "D_024":"ACTIVE",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--prior-unilateral",type=Path,required=True)
    p.add_argument("--prior-feature",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(
        a.multiscale,a.nodal,a.prior_unilateral,
        a.prior_feature,a.output,a.root),indent=2,allow_nan=False))


if __name__=="__main__":
    main()
