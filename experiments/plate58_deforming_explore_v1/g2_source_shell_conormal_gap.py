"""R6 original source plate-shell matched-edge co-normal signed opening audit.

ENGINEERING_ONLY: one mathematical, material-matched shell interface gap;
no closed rock solid, natural traction or updated-geometry KKT.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT,sha256,source_inputs,usage,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry,assemble_split_source,euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time import (
    normal_constraint_matrix,integrate,
)
from experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel import (
    rigid_motion_with_residual,certify_priors,
)
from experiments.plate58_deforming_explore_v1.g2_source_owned_face_topology import (
    source_face_incidence,triangle_patch_metrics,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)

STATUS="PASS_SOURCE_SHELL_MATCHED_EDGE_CONORMAL_GAP_DIAGNOSTIC__SOLID_CONTACT_OPEN"
SCHEMA="ARCANA_R6_G2_ORIGINAL_SHELL_MATCHED_EDGE_CONORMAL_GAP_V1"
YEARS=(100,500,1000)
OPPOSING_CONORMAL_MAX_DOT=-0.95
SO3_GAP_TOL_M=1e-7


def need(ok,label):
    if not ok:
        raise SparseP1Error(label)


def unit(v,label):
    v=np.asarray(v,dtype=np.float64)
    mag=float(np.linalg.norm(v))
    need(v.shape==(3,) and np.all(np.isfinite(v))
         and math.isfinite(mag) and mag>1e-12,label)
    return v/mag


def into_face_conormal(triangle,edge):
    """Unit vector in a plate-owned ORIGINAL triangular sheet toward face interior."""
    tri=np.asarray(triangle,dtype=np.float64)
    ed=np.asarray(edge,dtype=np.float64)
    need(tri.shape==(3,3) and ed.shape==(2,3)
         and np.all(np.isfinite(tri)) and np.all(np.isfinite(ed)),
         "SHELL_FACET_VERTEX_SHAPE_INVALID")
    tangent=unit(ed[1]-ed[0],"SHELL_SOURCE_EDGE_DEGENERATE")
    other=[x for x in tri if min(np.linalg.norm(x-e) for e in ed)>1e-7]
    need(len(other)==1,"SHELL_SOURCE_FACE_THIRD_VERTEX_UNMATCHED")
    direction=other[0]-.5*(ed[0]+ed[1])
    return unit(direction-(direction@tangent)*tangent,
                "SHELL_INWARD_CONORMAL_DEGENERATE")


def matched_shell_gap(p_triangle,q_triangle,p_edge,q_edge):
    """Mathematical matched-original-edge midpoint gap, NOT solid penetration.

    For opposite plate-owned inner face co-normals m_p,m_q, define opening
    n=(m_q-m_p)/||m_q-m_p||, g=(mid_q-mid_p)·n. Not a pointwise
    3D surface minimum or signed solid-wall Signorini constraint.
    """
    p=np.asarray(p_triangle,dtype=float)
    q=np.asarray(q_triangle,dtype=float)
    ep=np.asarray(p_edge,dtype=float)
    eq=np.asarray(q_edge,dtype=float)
    mp=into_face_conormal(p,ep)
    mq=into_face_conormal(q,eq)
    alignment=float(mp@mq)
    record={
        "classification":"NOT_QUALIFIED",
        "reason":None,
        "inward_conormal_alignment":alignment,
        "signed_shell_midpoint_gap_m":None,
        "signed_solid_nonpenetration_m":None,
        "shell_opening_normal_cartesian":None,
        "physical_contact_authorized":False,
    }
    if alignment>OPPOSING_CONORMAL_MAX_DOT:
        record["reason"]="SOURCE_PLATE_FACE_SIDEDNESS_NOT_OPPOSING"
        return record
    normal=unit(mq-mp,"SHELL_OPENING_NORMAL_DEGENERATE")
    delta=np.mean(eq,axis=0)-np.mean(ep,axis=0)
    gap=float(delta@normal)
    need(math.isfinite(gap),"SHELL_NONFINITE_GAP")
    record.update({
        "classification":"ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
        "reason":"MATHEMATICAL_SHELL_OPENING_NOT_CLOSED_SOLID_GAP",
        "signed_shell_midpoint_gap_m":gap,
        "shell_opening_normal_cartesian":normal.tolist(),
        "midpoint_relative_displacement_m":delta.tolist(),
        "positive_means_q_moves_into_q_side":True,
    })
    return record


def edge_indices(face,edge_ids):
    face=list(map(int,face))
    inds=[face.index(n) for n in edge_ids]
    need(len(set(inds))==2,"SHELL_INVALID_FACE_EDGE_INDEX")
    return inds


def from_six_vertices(x,ids):
    # x=(p0,p1,p2,q0,q1,q2), ids=((ip0,ip1),(iq0,iq1))
    x=np.asarray(x,dtype=float).reshape(2,3,3)
    return matched_shell_gap(x[0],x[1],x[0][ids[0]],x[1][ids[1]])


def source_shell_consistency(x,ids,step=.5):
    """Numerical gradient/virtual-work consistency only; NOT force law."""
    x=np.asarray(x,dtype=float).reshape(2,3,3)
    base=from_six_vertices(x,ids)
    need(base["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
         "SHELL_AUDIT_WITNESS_INELIGIBLE")
    gradients=[]
    for h in (step,step/2):
        grad=np.zeros_like(x)
        for i in range(2):
            for j in range(3):
                for k in range(3):
                    d=np.zeros_like(x)
                    d[i,j,k]=h
                    plus=from_six_vertices(x+d,ids)
                    minus=from_six_vertices(x-d,ids)
                    need(plus["classification"]==base["classification"]
                         and minus["classification"]==base["classification"],
                         "SHELL_FD_FEATURE_BRANCH_SWITCH")
                    grad[i,j,k]=(
                        plus["signed_shell_midpoint_gap_m"]-
                        minus["signed_shell_midpoint_gap_m"])/(2*h)
        gradients.append(grad)
    err=float(np.max(np.abs(gradients[0]-gradients[1])))
    need(err<3e-4,"SHELL_GAP_FD_REFINEMENT_FAILED")
    gradient=gradients[1]
    force_balance=float(np.linalg.norm(np.sum(gradient,axis=(0,1))))
    # The numerically differentiated g must be translationally invariant.
    need(force_balance<3e-5,"SHELL_TRANSLATION_VIRTUAL_WORK_FAILED")
    rng=np.array([
        [[.1,-.2,.08],[-.12,.3,.05],[.04,-.15,.1]],
        [[-.07,.03,-.06],[.23,-.1,.2],[-.16,.12,-.04]]
    ])
    d=.25
    plus=from_six_vertices(x+d*rng,ids)
    minus=from_six_vertices(x-d*rng,ids)
    need(plus["classification"]==base["classification"]
         and minus["classification"]==base["classification"],
         "SHELL_VIRTUAL_WORK_FEATURE_SWITCH")
    predicted=float(np.sum(gradient*rng))
    observed=float((plus["signed_shell_midpoint_gap_m"]-
                    minus["signed_shell_midpoint_gap_m"])/(2*d))
    virtual_work_error=abs(predicted-observed)
    need(virtual_work_error<3e-4,"SHELL_VIRTUAL_WORK_FD_FAILED")
    return {
        "max_FD_refinement_error":err,
        "normalized_force_translation_residual":force_balance,
        "normalized_virtual_work_error":virtual_work_error,
        "contact_multiplier_solved":False,
        "physical_force_calibrated":False,
    }


def check_SO3(p,q,ep,eq,base):
    Q=Rotation.from_rotvec([.4,-.7,.2]).as_matrix()
    moved=matched_shell_gap(p@Q.T,q@Q.T,ep@Q.T,eq@Q.T)
    need(moved["classification"]==base["classification"],
         "SHELL_SO3_CLASSIFICATION_CHANGED")
    align_error=abs(moved["inward_conormal_alignment"]-
                    base["inward_conormal_alignment"])
    if base["signed_shell_midpoint_gap_m"] is not None:
        gap_error=abs(moved["signed_shell_midpoint_gap_m"]-
                      base["signed_shell_midpoint_gap_m"])
        normal_error=float(np.linalg.norm(
            np.asarray(moved["shell_opening_normal_cartesian"])-
            Q@np.asarray(base["shell_opening_normal_cartesian"])))
    else:
        gap_error=0.
        normal_error=0.
    need(gap_error<SO3_GAP_TOL_M and align_error<1e-9
         and normal_error<1e-9,"SHELL_SO3_OBJECTIVITY_FAILED")
    return {
        "signed_gap_error_m":gap_error,
        "conormal_alignment_error":align_error,
        "normal_rotation_error":normal_error,
    }


def snapshot_inventory(source_faces,index,positions,prior_faces,year):
    old={r["source_boundary_id"]:r for r in prior_faces}
    need(len(old)==len(source_faces),"SHELL_PRIOR_FACE_SOURCE_COUNT_INVALID")
    rows=[]
    for source in source_faces:
        bid=source["source_boundary_id"]
        need(bid in old,"SHELL_PRIOR_FACE_SOURCE_ID_MISSING")
        pair=source["plate_pair"]
        a,b=source["source_edge_node_ids"]
        pf=source["plate_p_original_triangle_node_ids"]
        qf=source["plate_q_original_triangle_node_ids"]
        p=np.asarray([positions[index[(pair[0],n)]] for n in pf])
        q=np.asarray([positions[index[(pair[1],n)]] for n in qf])
        ep=np.asarray([positions[index[(pair[0],n)]] for n in (a,b)])
        eq=np.asarray([positions[index[(pair[1],n)]] for n in (a,b)])
        gm=triangle_patch_metrics(p,q,ep,eq)
        ref=old[bid]
        need(ref["plate_p_original_triangle_node_ids"]==pf
             and ref["plate_q_original_triangle_node_ids"]==qf
             and abs(ref["inward_face_conormal_alignment"]-
                     gm["inward_face_conormal_alignment"])<1e-9
             and abs(ref["nearest_boundary_edge_unsigned_distance_m"]-
                     gm["nearest_boundary_edge_unsigned_distance_m"])<1e-7,
             "SHELL_PRIOR_FAIR_FACE_ORIENTATION_REPLAY_CHANGED")
        feature=matched_shell_gap(p,q,ep,eq)
        fso3=check_SO3(p,q,ep,eq,feature)
        pa=edge_indices(pf,(a,b))
        qa=edge_indices(qf,(a,b))
        record={
            "source_boundary_id":bid,"plate_pair":pair,
            "source_edge_node_ids":[a,b],
            "source_original_plate_p_triangle":pf,
            "source_original_plate_q_triangle":qf,
            **feature,
            "SO3":fso3,
            "gradient_audit":None,
        }
        # Test all source edges at each checkpoint, not merely nearest-pair snippets.
        if feature["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP":
            record["gradient_audit"]=source_shell_consistency(
                np.stack((p,q)),(pa,qa))
        if year==0 and record["signed_shell_midpoint_gap_m"] is not None:
            need(abs(record["signed_shell_midpoint_gap_m"])<1e-8,
                 "SHELL_T0_MATERIAL_BOUNDARY_MISMATCH")
        rows.append(record)
    need(len(rows)==len(source_faces),"SHELL_SOURCE_EDGE_INVENTORY_INCOMPLETE")
    finite=[r["signed_shell_midpoint_gap_m"] for r in rows
            if r["signed_shell_midpoint_gap_m"] is not None]
    return {
        "year":year,
        "source_edges":len(rows),
        "classification_counts":dict(Counter(r["classification"] for r in rows)),
        "reason_counts":dict(Counter(r["reason"] for r in rows)),
        "qualified_engineered_shell_gap_count":len(finite),
        "negative_engineered_shell_gap_below_minus_1um_count":
            sum(v<-1e-6 for v in finite),
        "min_engineered_shell_gap_m":min(finite) if finite else None,
        "max_engineered_shell_gap_m":max(finite) if finite else None,
        "max_SO3_gap_error_m":max(r["SO3"]["signed_gap_error_m"] for r in rows),
        "max_fd_refinement_error":max(
            (r["gradient_audit"]["max_FD_refinement_error"]
             for r in rows if r["gradient_audit"] is not None),default=None),
        "physical_solid_gap_count":0,
        "per_source_matched_edge":rows,
    }


def run_region(width,mdir,ndir,omegas,prior_region):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential,
    )
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
         "SHELL_SOURCE_FEG_PRE_SHA_CHANGED")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    pre=parse_regional_pre(pre_path,r["PRE_source_field_order"],ids)
    need({str(k):v for k,v in pre.items()}==
         {str(k):v for k,v in nod["source_PRE_by_parent_node"].items()},
         "SHELL_NODAL_BINDING_CHANGED")
    for item in pre.values():
        validate_column_for_potential(item)
    ll={ids[i]:(float(n.latitude_deg),float(n.longitude_deg))
        for i,n in enumerate(feg.nodes)}
    faces=[tuple(ids[int(n)-1] for n in e.node_ids) for e in feg.elements]
    plates=list(map(int,r["parent_triangle_plate_ids"]))
    registry=contact_registry(ids,faces,plates,ll,r["source_contact_edges"])
    source_faces=source_face_incidence(faces,plates,r["source_contact_edges"])
    K,index,coords,plate_views,stats=assemble_split_source(
        ids,faces,plates,ll,pre)
    g=euler_source_en(coords,plate_views,omegas)
    J=normal_constraint_matrix(registry["contacts"],index,K.shape[0])
    xyz,radial,east,north=frames_and_cartesian(coords)
    zeros=np.zeros(K.shape[0],dtype=float)
    t0,vel,R=rigid_motion_with_residual(
        xyz,east,north,plate_views,omegas,g,zeros,g,0.)
    t0_inventory=snapshot_inventory(
        source_faces,index,t0,prior_region["T0"]["per_source_boundary_patch"],0)
    trajectory=integrate(K,J,g,1.,1000,checkpoints=YEARS)
    need(abs(trajectory["max_scaled_complementarity"])<1e-8,
         "SHELL_PRIOR_T0_KKT_REPLAY_FAILED")
    checkpoints={}
    for year in YEARS:
        ss=trajectory["snapshots"][year]
        pos,vel,R=rigid_motion_with_residual(
            xyz,east,north,plate_views,omegas,g,
            ss["displacement"],ss["velocity"],year)
        checkpoints[str(year)]=snapshot_inventory(
            source_faces,index,pos,prior_region["checkpoints"][str(year)][
                "per_source_boundary_patch"],year)
    need(len(source_faces)==(12 if width==8 else 36)
         and registry["triple_junction_parent_ids"]==
         ([] if width==8 else [34587]),
         "SHELL_ORIGINAL_SOURCE_SCOPE_CHANGED")
    return {
        "extent":width,
        "source_edges":len(source_faces),
        "source_pair_node_links":len(registry["contacts"]),
        "original_triple_parent_node_ids":registry["triple_junction_parent_ids"],
        "T0":t0_inventory,"checkpoints":checkpoints,
    }


def execute(multiscale,nodal,unilateral,prior_face,out,root=ROOT):
    mdir,ndir,un,old,out,root=map(
        Path,(multiscale,nodal,unilateral,prior_face,out,root))
    need(not out.exists(),"SHELL_OUTPUT_ALREADY_EXISTS")
    began=time.perf_counter()
    source_pins=certify_priors(mdir,ndir,un,root)
    prior_manifest=json.loads((old/"MANIFEST.json").read_text())
    prior=json.loads((old/"REPORT.json").read_text())
    need(prior_manifest["schema"]==
         "ARCANA_R6_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_MANIFEST_V1"
         and prior_manifest["files"]["REPORT.json"]==
         sha256(old/"REPORT.json")
         and sha256(old/"REPORT.json")==
         "3e42e1321cfb72f73bd72c82c32030969c908ec112ef5fb1255b9d7a767e4d07"
         and prior["status"]==
         "PASS_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_AUDIT__CLOSED_SOLID_CONTACT_UNPROVEN"
         and prior["physical_T1"] is None
         and prior["D_024"]=="ACTIVE"
         and prior["physical_signed_surface_contact_gap_available"] is False,
         "SHELL_PRIOR_FACE_FAIR_SHA_STATUS_INVALID")
    for path,checksum in prior["source_sha256"].items():
        need(Path(path).is_file() and sha256(Path(path))==checksum,
             "SHELL_PRIOR_SOURCE_PIN_CHANGED")
    source_pins[str(old/"REPORT.json")]=sha256(old/"REPORT.json")
    source_pins[str(old/"MANIFEST.json")]=sha256(old/"MANIFEST.json")
    mesh,omegas,pins,horizon,pre=source_inputs(root)
    need(horizon>1000,"SHELL_SOURCE_HORIZON_INVALID")
    original_regions={int(x["extent"]):x for x in prior["results"]}
    need(set(original_regions)=={8,16},"SHELL_PRIOR_REGIONS_INVALID")
    results=[run_region(width,mdir,ndir,omegas,original_regions[width])
             for width in (8,16)]
    need(all(sha256(Path(p))==h for p,h in source_pins.items()),
         "SHELL_INPUT_FILES_CHANGED_DURING_AUDIT")
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_world_mesh_sha256":mesh.normalized_sha256,
        "source_sha256":source_pins,
        "results":results,
        "source_matched_edge_gap_is_engineering_shell_diagnostic_only":True,
        "source_original_shell_sidedness_uses_authentic_adjacent_faces":True,
        "physical_signed_solid_contact_gap_available":False,
        "updated_geometry_KKT_executed":False,
        "physical_solver_runs":0,"physical_T1":None,
        "D_024":"ACTIVE","HistoryStore_modified":False,
        "canonical_promotion":False,
        "total_wall_seconds":time.perf_counter()-began,
        "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    report_path=out/"REPORT.json"
    report_path.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_SOURCE_SHELL_MATCHED_EDGE_GAP_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(report_path)},
        "physical_T1":None,"no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":STATUS,"regions":[{
            "extent":r["extent"],
            "source_edges":r["source_edges"],
            "triple_nodes":r["original_triple_parent_node_ids"],
            "T0":{k:v for k,v in r["T0"].items()
                  if k!="per_source_matched_edge"},
            "checkpoints":{year:{
                k:v for k,v in entry.items()
                if k!="per_source_matched_edge"}
                for year,entry in r["checkpoints"].items()},
        } for r in results],
        "physical_T1":None,"D_024":"ACTIVE",
        "total_wall_seconds":report["total_wall_seconds"],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",required=True,type=Path)
    p.add_argument("--nodal",required=True,type=Path)
    p.add_argument("--prior-unilateral",required=True,type=Path)
    p.add_argument("--prior-face",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(
        a.multiscale,a.nodal,a.prior_unilateral,a.prior_face,
        a.output,a.root),indent=2,allow_nan=False))


if __name__=="__main__":
    main()
