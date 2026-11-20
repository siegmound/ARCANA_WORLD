"""ARCANA R6: refine source-matched shell opening sign-event brackets to 1 model year.

Read-only genuine source replay; the OLD fixed-T0 KKT supplies the trajectory.
No exact crossing time, new contact response, rock collision or physical T1.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

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
    source_face_incidence,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_conormal_gap import (
    matched_shell_gap,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_differential_kinematics import (
    SAMPLE_YEARS, sign_class,directional_rate_audit,triple_material_view_audit,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)

SCHEMA="ARCANA_R6_SOURCE_SHELL_ONE_YEAR_EVENT_TEMPORAL_COHERENCE_V1"
STATUS="PASS_SOURCE_SHELL_1Y_EVENT_BRACKET_REFINEMENT__PHYSICAL_SOLID_CONTACT_OPEN"
PRIOR_REPORT_SHA="29ce93ffed7dae94be7cff16f92b3bb8a4f82020140a2adc0d6056270f38c1d5"
SOURCE_YEAR_END=1000
REPLAY_EPS_M=1e-7
EXPECTED_BRACKETS={
    "R6BND-T0-f679f4c97f1e7445d8d9":(175,200,"NEGATIVE","POSITIVE"),
    "R6BND-T0-4d168aac7492e7c418de":(475,500,"POSITIVE","NEGATIVE"),
    "R6BND-T0-1569360d5844c75db0d3":(625,650,"NEGATIVE","POSITIVE"),
    "R6BND-T0-16d7dc72630ecb414c04":(875,900,"NEGATIVE","POSITIVE"),
}


def need(ok,tag):
    if not ok:
        raise SparseP1Error(tag)


def _by_id(rows):
    mapped={x["source_boundary_id"]:x for x in rows}
    need(len(mapped)==len(rows),"EVENT_ORIGINAL_R6BND_DUPLICATE")
    return mapped


def assert_prior_brackets(prior_regions):
    need(set(prior_regions)=={8,16},"EVENT_ORIGINAL_REGION_SET_INVALID")
    reg8=prior_regions[8];reg16=prior_regions[16]
    need(reg8["source_edges"]==12 and reg8["source_contact_links"]==13
         and reg8["source_triple_parent_nodes"]==[]
         and reg16["source_edges"]==36 and reg16["source_contact_links"]==39
         and reg16["source_triple_parent_nodes"]==[34587],
         "EVENT_ORIGINAL_SOURCE_SCOPE_INVALID")
    need(reg8["sampled_sign_event_brackets"]["opposite_nonzero_sign_brackets"]==[],
         "EVENT_REGION_8_SIGN_SWITCH_UNEXPECTED")
    brackets=reg16["sampled_sign_event_brackets"]["opposite_nonzero_sign_brackets"]
    need(len(brackets)==len(EXPECTED_BRACKETS),
         "EVENT_ORIGINAL_25Y_BRACKET_COUNT_CHANGED")
    found={}
    for b in brackets:
        bid=b["source_boundary_id"]
        need(bid not in found,"EVENT_BRACKET_DUPLICATE")
        found[bid]=(int(b["from_year"]),int(b["to_year"]),
                    b["from_sign"],b["to_sign"])
    need(found==EXPECTED_BRACKETS,
         "EVENT_ORIGINAL_25Y_BRACKET_ID_OR_DIRECTION_CHANGED")
    return found


def summarize_integer_bracket(samples,from_year,to_year,from_sign,to_sign):
    """Only integer-sample evidence, no inferred exact zero crossing."""
    need(set(samples)==set(range(from_year,to_year+1)),
         "EVENT_ONE_YEAR_SAMPLES_INCOMPLETE")
    rows=[samples[k] for k in range(from_year,to_year+1)]
    def s(row):
        return sign_class(row["signed_shell_midpoint_gap_m"])
    need(s(rows[0])==from_sign and s(rows[-1])==to_sign,
         "EVENT_COARSE_BRACKET_ENDPOINT_SIGN_CHANGED")
    crossings=[];zero_samples=[]
    for i,r in enumerate(rows):
        need(math.isfinite(float(r["signed_shell_midpoint_gap_m"])) and
             math.isfinite(float(r["instantaneous_gdot_m_per_model_year"])),
             "EVENT_NONFINITE_GAP_OR_RATE")
        if s(r)=="NEAR_ZERO":
            zero_samples.append(r["model_year"])
        if i:
            before=rows[i-1]
            sb,sa=s(before),s(r)
            if sb in ("NEGATIVE","POSITIVE") and sa in ("NEGATIVE","POSITIVE") and sb!=sa:
                crossings.append({
                    "from_year":before["model_year"],
                    "to_year":r["model_year"],
                    "from_sign":sb,"to_sign":sa,
                    "exact_crossing_year_known":False,
                })
    temporal=[]
    for k in range(1,len(rows)-1):
        prev,curr,nxt=rows[k-1:k+2]
        centered=(nxt["signed_shell_midpoint_gap_m"]-
                  prev["signed_shell_midpoint_gap_m"])/2.
        discrepancy=centered-curr["instantaneous_gdot_m_per_model_year"]
        temporal.append({
            "year":curr["model_year"],
            "trajectory_centered_one_year_rate_m_per_model_year":centered,
            "instantaneous_original_velocity_rate_m_per_model_year":
                curr["instantaneous_gdot_m_per_model_year"],
            "discrepancy_m_per_model_year":discrepancy,
        })
    return {
        "from_year":from_year,"to_year":to_year,
        "original_25y_from_sign":from_sign,
        "original_25y_to_sign":to_sign,
        "definite_1y_opposite_nonzero_sign_brackets":crossings,
        "sampled_near_zero_years":zero_samples,
        "no_crossing_outside_sampled_integer_years_proven":False,
        "continuous_zero_crossing_time_exactly_known":False,
        "temporal_rate_comparisons":temporal,
        "max_absolute_instantaneous_vs_1y_centered_trajectory_rate_difference":
            max((abs(r["discrepancy_m_per_model_year"]) for r in temporal),
                default=None),
        "temporal_rate_discrepancy_pass_asserted":False,
        "per_integer_source_history":rows,
    }


def _material_row(original,index,pos,vel,year):
    p,q=original["plate_pair"]
    edge=original["source_edge_node_ids"]
    pf=original["plate_p_original_triangle_node_ids"]
    qf=original["plate_q_original_triangle_node_ids"]
    P=np.asarray([pos[index[(p,n)]] for n in pf])
    Q=np.asarray([pos[index[(q,n)]] for n in qf])
    EP=np.asarray([pos[index[(p,n)]] for n in edge])
    EQ=np.asarray([pos[index[(q,n)]] for n in edge])
    VP=np.asarray([vel[index[(p,n)]] for n in pf])
    VQ=np.asarray([vel[index[(q,n)]] for n in qf])
    VEP=np.asarray([vel[index[(p,n)]] for n in edge])
    VEQ=np.asarray([vel[index[(q,n)]] for n in edge])
    gap=matched_shell_gap(P,Q,EP,EQ)
    need(gap["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
         "EVENT_ORIGINAL_SHELL_GEOMETRY_LOST_QUALIFICATION")
    rate=directional_rate_audit(P,Q,EP,EQ,VP,VQ,VEP,VEQ,
                                verify_SO3=False)
    need(rate["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP",
         "EVENT_SOURCE_INSTANTANEOUS_RATE_UNQUALIFIED")
    return {
        "model_year":int(year),
        "signed_shell_midpoint_gap_m":gap["signed_shell_midpoint_gap_m"],
        "instantaneous_gdot_m_per_model_year":
            rate["gdot_m_per_model_year"],
        "frozen_normal_rate_m_per_model_year":
            rate["frozen_normal_contribution_m_per_model_year"],
        "conormal_rotation_rate_m_per_model_year":
            rate["normal_rotation_contribution_m_per_model_year"],
        "gap_sign_class":sign_class(gap["signed_shell_midpoint_gap_m"]),
        "physical_solid_collision_proven":False,
    }


def run_source_region_16(mdir,ndir,omegas,prior16,original_events):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential,
    )
    width=16
    a=next(x for x in json.loads((mdir/"CONTINUATION_A.json").read_text())[
        "topological_comparative_extents"] if int(x["cell_extent_per_side"])==width)
    b=next(x for x in json.loads((ndir/"SOURCE_NODAL_ELEMENT_G2.json").read_text())[
        "scales"] if int(x["extent_cells"])==width)
    ids=list(map(int,a["parent_node_ids"]))
    feg_path=mdir/"OUTER_A_16x16.feg"
    pre_path=mdir/"OUTER_A_16x16_PRE_T0_PASSIVE.dat"
    need(sha256(feg_path)==a["output_FEG_sha256"]
         and sha256(pre_path)==a["output_PRE_sha256"],
         "EVENT_FEG_PRE_SHA_CHANGED")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    pre=parse_regional_pre(pre_path,a["PRE_source_field_order"],ids)
    need({str(k):v for k,v in pre.items()}==
         {str(k):v for k,v in b["source_PRE_by_parent_node"].items()},
         "EVENT_NODAL_SOURCE_BINDING_INVALID")
    for r in pre.values():validate_column_for_potential(r)
    latlon={ids[i]:(float(n.latitude_deg),float(n.longitude_deg))
            for i,n in enumerate(feg.nodes)}
    faces=[tuple(ids[int(n)-1] for n in tri.node_ids)
           for tri in feg.elements]
    plates=list(map(int,a["parent_triangle_plate_ids"]))
    registry=contact_registry(ids,faces,plates,latlon,a["source_contact_edges"])
    face_rows=source_face_incidence(faces,plates,a["source_contact_edges"])
    need(len(face_rows)==36
         and len(registry["contacts"])==39
         and registry["triple_junction_parent_ids"]==[34587],
         "EVENT_16_SOURCE_COUNTS_CHANGED")
    by_source=_by_id(face_rows)
    for bid in original_events:
        need(bid in by_source,"EVENT_SOURCE_EVENT_ID_NOT_ORIGINAL")
    K,index,coords,views,stats=assemble_split_source(
        ids,faces,plates,latlon,pre)
    drive=euler_source_en(coords,views,omegas)
    J=normal_constraint_matrix(registry["contacts"],index,K.shape[0])
    xyz,radial,east,north=frames_and_cartesian(coords)
    zero=np.zeros_like(drive)
    t0,vel0,R0=rigid_motion_with_residual(
        xyz,east,north,views,omegas,drive,zero,drive,0.)
    detailed=sorted({year for s,e,*_ in original_events.values()
                     for year in range(s,e+1)})
    capture=sorted(set(SAMPLE_YEARS[1:]).union(detailed))
    trajectory=integrate(K,J,drive,1.,SOURCE_YEAR_END,checkpoints=capture)
    need(abs(trajectory["max_scaled_complementarity"])<1e-8,
         "EVENT_ORIGINAL_FIXED_T0_KKT_REPLAY_FAILED")
    previous={int(year):_by_id(rows)
              for year,rows in prior16["source_original_midpoint_gap_per_year"].items()}
    need(set(previous)==set(SAMPLE_YEARS),
         "EVENT_25Y_SOURCE_HISTORY_INCOMPLETE")
    replay_error=0.
    samples_by_event={bid:{} for bid in original_events}
    triple_checkpoints={}
    def at(year,pos,vel):
        nonlocal replay_error
        if year in previous:
            for src in face_rows:
                bid=src["source_boundary_id"]
                rr=matched_shell_gap(
                    np.asarray([pos[index[(src["plate_pair"][0],n)]]
                                for n in src["plate_p_original_triangle_node_ids"]]),
                    np.asarray([pos[index[(src["plate_pair"][1],n)]]
                                for n in src["plate_q_original_triangle_node_ids"]]),
                    np.asarray([pos[index[(src["plate_pair"][0],n)]]
                                for n in src["source_edge_node_ids"]]),
                    np.asarray([pos[index[(src["plate_pair"][1],n)]]
                                for n in src["source_edge_node_ids"]]))
                value=rr["signed_shell_midpoint_gap_m"]
                old=previous[year][bid]["signed_shell_midpoint_gap_m"]
                need(value is not None and old is not None,
                     "EVENT_25Y_SHELL_GAP_INELIGIBLE")
                err=abs(value-old)
                replay_error=max(replay_error,err)
                need(err<REPLAY_EPS_M,
                     "EVENT_PRIOR_SHA_VERIFIED_25Y_GAP_REPLAY_FAILED")
        for bid,(s,e,*_) in original_events.items():
            if s<=year<=e:
                samples_by_event[bid][year]=_material_row(
                    by_source[bid],index,pos,vel,year)
        if year in (0,100,500,1000):
            triple_checkpoints[str(year)]=triple_material_view_audit(
                34587,(5,8,11),index,pos,vel)
    at(0,t0,vel0)
    for year in capture:
        s=trajectory["snapshots"][year]
        pos,vel,R=rigid_motion_with_residual(
            xyz,east,north,views,omegas,drive,
            s["displacement"],s["velocity"],year)
        at(year,pos,vel)
    results=[]
    for bid,(start,end,fromsign,tosign) in sorted(original_events.items()):
        result=summarize_integer_bracket(
            samples_by_event[bid],start,end,fromsign,tosign)
        result["source_boundary_id"]=bid
        result["source_original_plate_pair"]=by_source[bid]["plate_pair"]
        result["source_original_parent_nodes"]=by_source[bid]["source_edge_node_ids"]
        results.append(result)
    need(len(triple_checkpoints)==4 and all(
        r["material_displacement_vector_closure_error_m"]<1e-7
        for r in triple_checkpoints.values()),
        "EVENT_TRIPLE_SOURCE_CHECKPOINT_REPLAY_FAILED")
    return {
        "extent":16,
        "original_source_boundary_count":36,
        "original_source_contact_link_count":39,
        "original_source_triple_parent_node_id":34587,
        "all_previous_25_model_year_samples_replayed":True,
        "max_25y_prior_gap_replay_abs_error_m":replay_error,
        "one_model_year_source_bracket_refinements":results,
        "source_triple_at_original_checkpoints":triple_checkpoints,
        "original_fixed_T0_KKT_only":True,
    }


def execute(multiscale,nodal,unilateral,prior_differential,out,root=ROOT):
    mdir,ndir,un,old,out,root=map(
        Path,(multiscale,nodal,unilateral,prior_differential,out,root))
    need(not out.exists(),"EVENT_OUTPUT_ALREADY_EXISTS")
    started=time.perf_counter()
    pins=certify_priors(mdir,ndir,un,root)
    manifest=json.loads((old/"MANIFEST.json").read_text())
    prior=json.loads((old/"REPORT.json").read_text())
    need(manifest["schema"]=="ARCANA_R6_SHELL_DIFFERENTIAL_KINEMATICS_MANIFEST_V1"
         and manifest["files"]["REPORT.json"]==sha256(old/"REPORT.json")
         and sha256(old/"REPORT.json")==PRIOR_REPORT_SHA
         and prior["status"]==
         "PASS_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_AND_TRIPLE_AUDIT__SOLID_CONTACT_OPEN"
         and prior["physical_T1"] is None
         and prior["D_024"]=="ACTIVE"
         and prior["updated_3D_KKT_executed"] is False,
         "EVENT_PRIOR_DIFFERENTIAL_FAIR_SHA_STATUS_INVALID")
    for path,digest in prior["source_sha256"].items():
        need(Path(path).is_file() and sha256(Path(path))==digest,
             "EVENT_PRIOR_SOURCE_SHA_CHANGED")
    pins[str(old/"REPORT.json")]=sha256(old/"REPORT.json")
    pins[str(old/"MANIFEST.json")]=sha256(old/"MANIFEST.json")
    mesh,omegas,source_pins,horizon,meta=source_inputs(root)
    need(horizon>1000,"EVENT_SOURCE_HORIZON_CHANGED")
    regions={int(r["extent"]):r for r in prior["results"]}
    found=assert_prior_brackets(regions)
    result=run_source_region_16(mdir,ndir,omegas,regions[16],found)
    need(all(sha256(Path(path))==digest for path,digest in pins.items()),
         "EVENT_SHA_PINNED_INPUTS_MUTATED")
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_world_mesh_sha256":mesh.normalized_sha256,
        "source_sha256":pins,
        "prior_25_year_report_sha256":PRIOR_REPORT_SHA,
        "original_region_8_only_prior_verified_no_events":True,
        "result_16":result,
        "no_exact_continuous_time_zero_crossing_claim":True,
        "instantaneous_vs_one_year_trajectory_rate_is_DIAGNOSTIC_ONLY":True,
        "physical_signed_solid_contact_gap_available":False,
        "updated_3D_KKT_executed":False,"physical_solver_runs":0,
        "physical_T1":None,"D_024":"ACTIVE",
        "HistoryStore_modified":False,"canonical_promotion":False,
        "total_wall_seconds":time.perf_counter()-started,
        "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    rp=out/"REPORT.json"
    rp.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_SHELL_1YEAR_EVENT_REFINEMENT_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(rp)},
        "physical_T1":None,"no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":STATUS,
        "original_25y_source_gap_replay_error_m":
            result["max_25y_prior_gap_replay_abs_error_m"],
        "refined_original_brackets":[{
            "source_boundary_id":r["source_boundary_id"],
            "original_25y_bracket":[r["from_year"],r["to_year"]],
            "one_year_definite_brackets":
                r["definite_1y_opposite_nonzero_sign_brackets"],
            "near_zero_sample_years":r["sampled_near_zero_years"],
            "max_temporal_velocity_vs_trajectory_m_per_year":
                r["max_absolute_instantaneous_vs_1y_centered_trajectory_rate_difference"],
        } for r in result["one_model_year_source_bracket_refinements"]],
        "physical_T1":None,"D_024":"ACTIVE",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--prior-unilateral",type=Path,required=True)
    p.add_argument("--prior-differential",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(
        a.multiscale,a.nodal,a.prior_unilateral,a.prior_differential,
        a.output,a.root),indent=2,allow_nan=False))


if __name__=="__main__":
    main()
