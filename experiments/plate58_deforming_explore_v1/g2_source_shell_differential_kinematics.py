"""ARCANA R6: source-matched shell gap differential kinematics and triple junction.

Engineering-only original material-edge midpoint opening rates and sampled
sign-change BRACKETS. No physical solid contact, KKT, or natural rock traction.
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
    ROOT, sha256, source_inputs, usage,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry, assemble_split_source, euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time import (
    normal_constraint_matrix, integrate,
)
from experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel import (
    rigid_motion_with_residual, certify_priors,
)
from experiments.plate58_deforming_explore_v1.g2_source_owned_face_topology import (
    source_face_incidence,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_conormal_gap import (
    matched_shell_gap,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)

STATUS="PASS_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_AND_TRIPLE_AUDIT__SOLID_CONTACT_OPEN"
SCHEMA="ARCANA_R6_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_AND_TRIPLE_V1"
SOURCE_SHELL_REPORT_SHA="2fa5615788eab08bd02cd4bd5d9a4d78e84aeb8b38425c17cadbaf5ed9fe4f27"
SAMPLE_YEARS=(0,)+tuple(range(25,1001,25))
REPLAY_YEARS=(0,100,500,1000)
GAP_SIGN_EPS_M=1e-6
KINEMATIC_H_YEARS=.05


def need(value,label):
    if not value:
        raise SparseP1Error(label)


def _gap(x):
    p,q,ep,eq=x
    return matched_shell_gap(p,q,ep,eq)


def directional_rate_audit(p,q,ep,eq,vp,vq,vep,veq,h=KINEMATIC_H_YEARS,
                           verify_SO3=True):
    """Differentiate the EXACT same gap along the source velocity field.

    dot(g) = (midVq-midVp).n + (midQ-midP).dot(n).
    n_dot is numerical *co-normal orientation transport*, not a rock force.
    The perturbation x +/- h*v is a kinematic directional derivative,
    not a re-integration of the original unilateral T0 trajectory.
    """
    vertices=tuple(np.asarray(a,dtype=float) for a in (p,q,ep,eq))
    speeds=tuple(np.asarray(a,dtype=float) for a in (vp,vq,vep,veq))
    need(all(a.shape==(3,3) for a in vertices[:2]) and
         all(a.shape==(2,3) for a in vertices[2:]) and
         all(a.shape==v.shape and np.all(np.isfinite(a)) and
             np.all(np.isfinite(v)) for a,v in zip(vertices,speeds,strict=True)),
         "SHELL_RATE_SOURCE_STATE_INVALID")
    base=_gap(vertices)
    if base["classification"]!="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP":
        return {
            "classification":"NOT_QUALIFIED",
            "reason":"SHELL_RATE_"+str(base["reason"]),
            "gdot_m_per_model_year":None,
            "normal_rotation_contribution_m_per_model_year":None,
            "frozen_normal_contribution_m_per_model_year":None,
        }
    n=np.asarray(base["shell_opening_normal_cartesian"],dtype=float)
    separation=np.mean(eq,axis=0)-np.mean(ep,axis=0)
    vrel=np.mean(veq,axis=0)-np.mean(vep,axis=0)
    frozen=float(vrel@n)
    def eval_h(step):
        plus=_gap(tuple(a+step*v for a,v in zip(vertices,speeds,strict=True)))
        minus=_gap(tuple(a-step*v for a,v in zip(vertices,speeds,strict=True)))
        need(plus["classification"]==base["classification"] and
             minus["classification"]==base["classification"],
             "SHELL_RATE_DIRECTIONAL_FEATURE_SWITCH")
        np1=np.asarray(plus["shell_opening_normal_cartesian"])
        nm1=np.asarray(minus["shell_opening_normal_cartesian"])
        ndot=(np1-nm1)/(2*step)
        rate_fd=(plus["signed_shell_midpoint_gap_m"]-
                 minus["signed_shell_midpoint_gap_m"])/(2*step)
        return float(rate_fd),float(separation@ndot)
    rate_h,rotation_h=eval_h(h)
    rate_h2,rotation_h2=eval_h(h/2)
    result=frozen+rotation_h2
    residual=abs(rate_h2-result)
    refinement=abs(rate_h-rate_h2)
    need(residual<1e-4 and refinement<1e-4,
         "SHELL_DIFFERENTIAL_KINEMATICS_DECOMPOSITION_FAILED")
    obj_error=0.
    if verify_SO3:
        Q=Rotation.from_rotvec([.4,-.7,.2]).as_matrix()
        original_n=np.asarray(base["shell_opening_normal_cartesian"])
        rot_a=tuple(a@Q.T for a in vertices)
        rot_v=tuple(a@Q.T for a in speeds)
        rotated=directional_rate_audit(*rot_a,*rot_v,h=h,verify_SO3=False)
        need(rotated["classification"]==base["classification"],
             "SHELL_RATE_SO3_CLASS_CHANGED")
        obj_error=abs(float(rotated["gdot_m_per_model_year"])-result)
        need(obj_error<1e-5,"SHELL_RATE_SO3_OBJECTIVITY_FAILED")
    return {
        "classification":"ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
        "gdot_m_per_model_year":result,
        "frozen_normal_contribution_m_per_model_year":frozen,
        "normal_rotation_contribution_m_per_model_year":rotation_h2,
        "max_fd_rate_refinement_m_per_model_year":refinement,
        "rate_decomposition_residual_m_per_model_year":residual,
        "SO3_rate_absolute_error_m_per_model_year":obj_error,
        "physical_contact_force_derived":False,
    }


def sign_class(g):
    if g is None:
        return "NOT_QUALIFIED"
    return "POSITIVE" if g>GAP_SIGN_EPS_M else (
        "NEGATIVE" if g<-GAP_SIGN_EPS_M else "NEAR_ZERO")


def detect_sampled_sign_events(snapshots,source_ids):
    """Samples locate *BRACKETS*, never prove exact event times/continuity."""
    times=sorted(snapshots)
    departed=[];switches=[];uncertain=[]
    for bid in sorted(source_ids):
        prev=None
        for year in times:
            row=snapshots[year][bid]
            cur=sign_class(row["signed_shell_midpoint_gap_m"])
            if prev is not None:
                old_year,old=prev
                if old_year==0 and old=="NEAR_ZERO" and cur in ("NEGATIVE","POSITIVE"):
                    departed.append({
                        "source_boundary_id":bid,
                        "from_year":old_year,"to_year":year,
                        "initial_departure_direction":cur,
                    })
                elif old in ("POSITIVE","NEGATIVE") and cur in ("POSITIVE","NEGATIVE") and old!=cur:
                    switches.append({
                        "source_boundary_id":bid,"from_year":old_year,
                        "to_year":year,"from_sign":old,"to_sign":cur,
                        "event_time_exactly_known":False,
                    })
                elif old!=cur and (
                    old in ("NOT_QUALIFIED","NEAR_ZERO")
                    or cur in ("NOT_QUALIFIED","NEAR_ZERO")
                ) and old_year!=0:
                    uncertain.append({
                        "source_boundary_id":bid,
                        "from_year":old_year,"to_year":year,
                        "from_sign":old,"to_sign":cur,
                    })
            prev=(year,cur)
    return {
        "initial_T0_zero_departures":departed,
        "opposite_nonzero_sign_brackets":switches,
        "ambiguous_near_zero_or_unqualified_brackets":uncertain,
        "all_crossings_in_continuous_time_proven":False,
        "exact_zero_crossing_time_claimed":False,
        "sampling_cadence_model_years":25,
    }


def triple_material_view_audit(node_id,plate_ids,index,positions,velocities):
    plates=sorted(map(int,plate_ids))
    need(len(plates)==3 and len(set(plates))==3 and
         all((p,node_id) in index for p in plates),
         "SHELL_TRIPLE_PARENT_VIEW_PROVENANCE_INVALID")
    x=[np.asarray(positions[index[(p,node_id)]]) for p in plates]
    v=[np.asarray(velocities[index[(p,node_id)]]) for p in plates]
    pairs=[(0,1),(1,2),(2,0)]
    edges=[x[b]-x[a] for a,b in pairs]
    rates=[v[b]-v[a] for a,b in pairs]
    closure=float(np.linalg.norm(np.sum(edges,axis=0)))
    rate_closure=float(np.linalg.norm(np.sum(rates,axis=0)))
    need(closure<1e-7 and rate_closure<1e-8,
         "SHELL_TRIPLE_MATERIAL_VECTOR_CLOSURE_FAILED")
    return {
        "source_parent_node_id":int(node_id),"original_plate_ids":plates,
        "paired_material_view_separations_m":[
            float(np.linalg.norm(d)) for d in edges],
        "paired_material_relative_speed_m_per_model_year":[
            float(np.linalg.norm(v)) for v in rates],
        "material_displacement_vector_closure_error_m":closure,
        "material_velocity_vector_closure_error_m_per_model_year":rate_closure,
        "scalar_shell_gap_sum_constrained":False,
        "three_body_contact_or_force_balance_solved":False,
    }


def snapshot_rows(source_faces,index,pos,vel,year,prior=None):
    existing={r["source_boundary_id"]:r for r in prior} if prior is not None else None
    rows=[]
    for original in source_faces:
        bid=original["source_boundary_id"]
        p,q=original["plate_pair"]
        a,b=original["source_edge_node_ids"]
        pt=original["plate_p_original_triangle_node_ids"]
        qt=original["plate_q_original_triangle_node_ids"]
        P=np.asarray([pos[index[(p,n)]] for n in pt])
        Q=np.asarray([pos[index[(q,n)]] for n in qt])
        EP=np.asarray([pos[index[(p,n)]] for n in (a,b)])
        EQ=np.asarray([pos[index[(q,n)]] for n in (a,b)])
        VP=np.asarray([vel[index[(p,n)]] for n in pt])
        VQ=np.asarray([vel[index[(q,n)]] for n in qt])
        VEP=np.asarray([vel[index[(p,n)]] for n in (a,b)])
        VEQ=np.asarray([vel[index[(q,n)]] for n in (a,b)])
        match=matched_shell_gap(P,Q,EP,EQ)
        derivative=directional_rate_audit(
            P,Q,EP,EQ,VP,VQ,VEP,VEQ,verify_SO3=year in (0,100,500,1000))
        need((match["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP")==
             (derivative["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP"),
             "SHELL_RATE_CLASSIFICATION_PARITY_FAILED")
        g=match["signed_shell_midpoint_gap_m"]
        if existing is not None:
            need(bid in existing and
                 existing[bid]["classification"]==match["classification"] and
                 (g is None and existing[bid]["signed_shell_midpoint_gap_m"] is None or
                  g is not None and
                  abs(g-existing[bid]["signed_shell_midpoint_gap_m"])<1e-7),
                 "SHELL_RATE_PRIOR_FAIR_PER_EDGE_REPLAY_MISMATCH")
        rows.append({
            "source_boundary_id":bid,"source_plate_pair":[p,q],
            "source_parent_edge_nodes":[a,b],
            "source_triangle_p":pt,"source_triangle_q":qt,
            "classification":match["classification"],
            "reason":match["reason"],
            "signed_shell_midpoint_gap_m":g,
            "gap_sign_class":sign_class(g),
            "velocity_audit":derivative,
            "physical_solid_contact_qualified":False,
        })
    return rows


def run_region(width,mdir,ndir,omegas,prior_region):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential,
    )
    source=next(x for x in json.loads((mdir/"CONTINUATION_A.json").read_text())[
        "topological_comparative_extents"]
        if int(x["cell_extent_per_side"])==width)
    bound=next(x for x in json.loads((ndir/"SOURCE_NODAL_ELEMENT_G2.json").read_text())[
        "scales"] if int(x["extent_cells"])==width)
    ids=list(map(int,source["parent_node_ids"]))
    feg_path=mdir/f"OUTER_A_{width:02d}x{width:02d}.feg"
    pre_path=mdir/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
    need(sha256(feg_path)==source["output_FEG_sha256"]
         and sha256(pre_path)==source["output_PRE_sha256"],
         "SHELL_RATE_SOURCE_FEG_PRE_SHA_CHANGED")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    pre=parse_regional_pre(pre_path,source["PRE_source_field_order"],ids)
    need({str(k):v for k,v in pre.items()}==
         {str(k):v for k,v in bound["source_PRE_by_parent_node"].items()},
         "SHELL_RATE_NODAL_BINDING_CHANGED")
    for row in pre.values():
        validate_column_for_potential(row)
    ll={ids[i]:(float(n.latitude_deg),float(n.longitude_deg))
        for i,n in enumerate(feg.nodes)}
    faces=[tuple(ids[int(n)-1] for n in e.node_ids) for e in feg.elements]
    owners=list(map(int,source["parent_triangle_plate_ids"]))
    registry=contact_registry(ids,faces,owners,ll,source["source_contact_edges"])
    source_faces=source_face_incidence(
        faces,owners,source["source_contact_edges"])
    K,index,coords,plates,stats=assemble_split_source(
        ids,faces,owners,ll,pre)
    drive=euler_source_en(coords,plates,omegas)
    J=normal_constraint_matrix(registry["contacts"],index,K.shape[0])
    xyz,radial,east,north=frames_and_cartesian(coords)
    zero=np.zeros_like(drive)
    p0,v0,R0=rigid_motion_with_residual(
        xyz,east,north,plates,omegas,drive,zero,drive,0.)
    trajectory=integrate(K,J,drive,1.,1000,checkpoints=SAMPLE_YEARS[1:])
    need(abs(trajectory["max_scaled_complementarity"])<1e-8,
         "SHELL_RATE_PRIOR_T0_KKT_REPLAY_FAILED")
    snapshots={}
    triples={}
    need(registry["triple_junction_parent_ids"]==
         ([] if width==8 else [34587]),
         "SHELL_RATE_ORIGINAL_TRIPLE_SOURCE_CHANGED")
    for year in SAMPLE_YEARS:
        if year==0:
            pos,vel=p0,v0
            prior_sample=prior_region["T0"]["per_source_matched_edge"]
        else:
            ss=trajectory["snapshots"][year]
            pos,vel,R=rigid_motion_with_residual(
                xyz,east,north,plates,omegas,drive,
                ss["displacement"],ss["velocity"],year)
            prior_sample=(
                prior_region["checkpoints"][str(year)]["per_source_matched_edge"]
                if year in (100,500,1000) else None)
        rows=snapshot_rows(
            source_faces,index,pos,vel,year,prior=prior_sample)
        record={r["source_boundary_id"]:r for r in rows}
        need(len(record)==len(source_faces),
             "SHELL_RATE_ORIGINAL_ID_COVERAGE_FAILED")
        snapshots[year]=record
        if width==16:
            triples[year]=triple_material_view_audit(
                34587,(5,8,11),index,pos,vel)
    need(len(source_faces)==(12 if width==8 else 36)
         and len(registry["contacts"])==(13 if width==8 else 39),
         "SHELL_RATE_ORIGINAL_SOURCE_COUNTS_CHANGED")
    events=detect_sampled_sign_events(
        snapshots,[x["source_boundary_id"] for x in source_faces])
    summaries={}
    for year,rows in snapshots.items():
        vals=[x["signed_shell_midpoint_gap_m"] for x in rows.values()
              if x["signed_shell_midpoint_gap_m"] is not None]
        audits=[x["velocity_audit"] for x in rows.values()
                if x["velocity_audit"]["gdot_m_per_model_year"] is not None]
        summaries[str(year)]={
            "classification_counts":dict(Counter(
                x["classification"] for x in rows.values())),
            "source_edges":len(rows),
            "eligible_gap_count":len(vals),
            "negative_gap_count_below_minus_1um":sum(v<-GAP_SIGN_EPS_M for v in vals),
            "min_shell_gap_m":min(vals) if vals else None,
            "max_shell_gap_m":max(vals) if vals else None,
            "min_instantaneous_gdot_m_per_model_year":min(
                (a["gdot_m_per_model_year"] for a in audits),default=None),
            "max_instantaneous_gdot_m_per_model_year":max(
                (a["gdot_m_per_model_year"] for a in audits),default=None),
            "max_rate_decomposition_residual_m_per_model_year":max(
                (a["rate_decomposition_residual_m_per_model_year"] for a in audits),
                default=None),
            "max_SO3_rate_error_m_per_model_year":max(
                (a["SO3_rate_absolute_error_m_per_model_year"] for a in audits),
                default=None),
            "T0_rate_origin":(
                "UNCONSTRAINED_SOURCE_EULER_BASELINE_ONLY" if year==0
                else "PREVIOUS_T0_KKT_ENDPOINT_VELOCITY_DIAGNOSTIC"),
        }
    for yr in (0,100,500,1000):
        earlier=prior_region["T0"] if yr==0 else (
            prior_region["checkpoints"][str(yr)])
        s=summaries[str(yr)]
        need(s["eligible_gap_count"]==earlier["qualified_engineered_shell_gap_count"]
             and s["negative_gap_count_below_minus_1um"]==
                 earlier["negative_engineered_shell_gap_below_minus_1um_count"]
             and abs(s["min_shell_gap_m"]-earlier["min_engineered_shell_gap_m"])<1e-7
             and abs(s["max_shell_gap_m"]-earlier["max_engineered_shell_gap_m"])<1e-7,
             "SHELL_RATE_PRIOR_FAIR_CHECKPOINT_SUMMARY_MISMATCH")
    return {
        "extent":width,
        "source_edges":len(source_faces),
        "source_contact_links":len(registry["contacts"]),
        "source_triple_parent_nodes":registry["triple_junction_parent_ids"],
        "source_sampling_model_years":list(SAMPLE_YEARS),
        "source_original_midpoint_gap_per_year":{
            str(year):list(records.values()) for year,records in snapshots.items()},
        "summaries_by_year":summaries,
        "sampled_sign_event_brackets":events,
        "triple_material_view_kinematics_by_year":{
            str(year):r for year,r in triples.items()},
        "physical_contact_validated":False,
    }


def execute(multiscale,nodal,unilateral,prior_shell,out,root=ROOT):
    mdir,ndir,un,old,out,root=map(
        Path,(multiscale,nodal,unilateral,prior_shell,out,root))
    need(not out.exists(),"SHELL_RATE_OUTPUT_ALREADY_EXISTS")
    began=time.perf_counter()
    source_pins=certify_priors(mdir,ndir,un,root)
    manifest=json.loads((old/"MANIFEST.json").read_text())
    prior=json.loads((old/"REPORT.json").read_text())
    need(manifest["schema"]=="ARCANA_R6_SOURCE_SHELL_MATCHED_EDGE_GAP_MANIFEST_V1"
         and manifest["files"]["REPORT.json"]==sha256(old/"REPORT.json")
         and sha256(old/"REPORT.json")==SOURCE_SHELL_REPORT_SHA
         and prior["status"]==
         "PASS_SOURCE_SHELL_MATCHED_EDGE_CONORMAL_GAP_DIAGNOSTIC__SOLID_CONTACT_OPEN"
         and prior["physical_T1"] is None
         and prior["D_024"]=="ACTIVE"
         and prior["physical_signed_solid_contact_gap_available"] is False
         and prior["updated_geometry_KKT_executed"] is False,
         "SHELL_RATE_PRIOR_FAIR_REPORT_SHA_STATUS_INVALID")
    for source_path,digest in prior["source_sha256"].items():
        need(Path(source_path).is_file() and sha256(Path(source_path))==digest,
             "SHELL_RATE_PRIOR_SOURCE_SHA_CHANGED")
    source_pins[str(old/"REPORT.json")]=sha256(old/"REPORT.json")
    source_pins[str(old/"MANIFEST.json")]=sha256(old/"MANIFEST.json")
    mesh,omegas,pins,horizon,pre=source_inputs(root)
    need(horizon>1000,"SHELL_RATE_SOURCE_HORIZON_INVALID")
    regions={int(r["extent"]):r for r in prior["results"]}
    need(set(regions)=={8,16},"SHELL_RATE_PRIOR_REGION_SET_CHANGED")
    results=[run_region(width,mdir,ndir,omegas,regions[width])
             for width in (8,16)]
    need(all(sha256(Path(p))==h for p,h in source_pins.items()),
         "SHELL_RATE_INPUT_CHANGED_DURING_AUDIT")
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_world_mesh_sha256":mesh.normalized_sha256,
        "source_sha256":source_pins,
        "results":results,
        "kinematics_from_previous_T0_KKT_NOT_NEW_CONTACT_LAW":True,
        "sign_event_brackets_are_sampled_not_exact":True,
        "source_2D_shell_gap_not_a_physical_solid_clearance":True,
        "triple_loop_vector_identity_not_force_balance":True,
        "updated_3D_KKT_executed":False,
        "physical_solver_runs":0,"physical_T1":None,
        "D_024":"ACTIVE","HistoryStore_modified":False,
        "canonical_promotion":False,
        "computation_workers":1,
        "total_wall_seconds":time.perf_counter()-began,
        "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    rp=out/"REPORT.json"
    rp.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_SHELL_DIFFERENTIAL_KINEMATICS_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(rp)},
        "physical_T1":None,"no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":STATUS,
        "source_sample_years":len(SAMPLE_YEARS),
        "regions":[{
            "extent":r["extent"],"source_edges":r["source_edges"],
            "triple_parent_nodes":r["source_triple_parent_nodes"],
            "checkpoint_summaries":{
                str(y):r["summaries_by_year"][str(y)]
                for y in REPLAY_YEARS},
            "sampled_nonzero_sign_switch_brackets":len(
                r["sampled_sign_event_brackets"]["opposite_nonzero_sign_brackets"]),
            "initial_zero_departures":len(
                r["sampled_sign_event_brackets"]["initial_T0_zero_departures"]),
            "ambiguous_brackets":len(
                r["sampled_sign_event_brackets"][
                    "ambiguous_near_zero_or_unqualified_brackets"]),
        } for r in results],
        "physical_T1":None,"D_024":"ACTIVE",
        "total_wall_seconds":report["total_wall_seconds"],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--prior-unilateral",type=Path,required=True)
    p.add_argument("--prior-shell",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(
        a.multiscale,a.nodal,a.prior_unilateral,a.prior_shell,
        a.output,a.root),indent=2,allow_nan=False))


if __name__=="__main__":
    main()
