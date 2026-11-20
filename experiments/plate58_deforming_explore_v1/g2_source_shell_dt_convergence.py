"""R6 source-original matched shell gap: bounded dt-convergence diagnostic.

Engineering-only OLD fixed-T0 QP/KKT material trajectory at dt 1,.5,.25.
No moving contact KKT, 3D solid penetration, real tectonic forces or T1.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, sha256, source_inputs, usage,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    SparseP1Error,
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
from experiments.plate58_deforming_explore_v1.g2_source_owned_face_topology import (
    source_face_incidence,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_conormal_gap import (
    matched_shell_gap,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_differential_kinematics import (
    SAMPLE_YEARS, sign_class, triple_material_view_audit,
)
from experiments.plate58_deforming_explore_v1.g2_source_shell_event_1y_refinement import (
    EXPECTED_BRACKETS,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)

SCHEMA="ARCANA_R6_SHELL_ORIGINAL_KKT_DT_CONVERGENCE_DIAGNOSTIC_V1"
STATUS="PASS_SOURCE_SHELL_ORIGINAL_DT_COMPARISON_INVENTORY__PHYSICAL_CONTACT_OPEN"
PRIOR_REPORT_SHA="3a122e0ddccd0944b2478dda41abf452e00ec6f230edcb9313c0e8d3961b220c"
YEARS=tuple(SAMPLE_YEARS)
STEP_SIZES=(.5,.25)
SOURCE_BOUNDARY_REPLAY_MAX_ABS_M=1e-7


def need(ok,label):
    if not ok:
        raise SparseP1Error(label)


def original_source_row_map(rows):
    values={r["source_boundary_id"]:r for r in rows}
    need(len(values)==len(rows),"DTC_SOURCE_BOUNDARY_DUPLICATE")
    return values


def source_matched_gaps(source_faces,index,positions):
    result={}
    for row in source_faces:
        bid=row["source_boundary_id"]
        need(bid not in result,"DTC_ORIGINAL_SOURCE_EDGE_DUPLICATED")
        p,q=row["plate_pair"]
        nodes=row["source_edge_node_ids"]
        A=np.asarray([positions[index[(p,n)]]
                      for n in row["plate_p_original_triangle_node_ids"]])
        B=np.asarray([positions[index[(q,n)]]
                      for n in row["plate_q_original_triangle_node_ids"]])
        EA=np.asarray([positions[index[(p,n)]] for n in nodes])
        EB=np.asarray([positions[index[(q,n)]] for n in nodes])
        measure=matched_shell_gap(A,B,EA,EB)
        need(measure["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP"
             and measure["signed_shell_midpoint_gap_m"] is not None,
             "DTC_SOURCE_ORIGINAL_FACE_SIDEDNESS_LOST")
        result[bid]=float(measure["signed_shell_midpoint_gap_m"])
    return result


def compare_original_source_samples(prior_rows,current_gap,dt,year):
    original=original_source_row_map(prior_rows)
    need(set(original)==set(current_gap) and len(original)==36,
         "DTC_ORIGINAL_SOURCE_25Y_ID_DRIFT")
    errors={}
    for bid,record in original.items():
        need(record["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP"
             and record["signed_shell_midpoint_gap_m"] is not None,
             "DTC_PRIOR_ORIGINAL_SHELL_GAP_NOT_QUALIFIED")
        delta=current_gap[bid]-float(record["signed_shell_midpoint_gap_m"])
        need(math.isfinite(delta),"DTC_NONFINITE_SOURCE_DIFFERENCE")
        errors[bid]=delta
    return {
        "model_year":int(year),"tested_timestep_model_years":float(dt),
        "max_abs_change_from_verified_dt1_m":max(map(abs,errors.values())),
        "mean_abs_change_from_verified_dt1_m":
            sum(map(abs,errors.values()))/len(errors),
        "source_matched_edge_count":len(errors),
        "negative_gap_count":sum(v<-1e-6 for v in current_gap.values()),
        "sign_disagreements_from_dt1":sum(
            sign_class(current_gap[bid])!=
            sign_class(original[bid]["signed_shell_midpoint_gap_m"])
            for bid in original),
        "numerical_dt_convergence_proven":False,
    }


def analyze_subyear_samples(source_boundary_id,previous_bracket,samples,dt):
    """Sampled dt subbrackets, not exact roots and not physical collision."""
    a,b,expected_from,expected_to=previous_bracket
    need(dt in STEP_SIZES and
         len(samples)==int(round((b-a)/dt))+1,
         "DTC_SOURCE_SUBYEAR_SAMPLE_COUNT_CHANGED")
    for i,row in enumerate(samples):
        expected_year=a+i*dt
        need(abs(row["model_year"]-expected_year)<1e-8
             and math.isfinite(row["signed_shell_midpoint_gap_m"]),
             "DTC_SOURCE_SUBYEAR_CLOCK_OR_GAP_INVALID")
    signs=[sign_class(row["signed_shell_midpoint_gap_m"]) for row in samples]
    definite=[]
    near_zero=[]
    for i,sign in enumerate(signs):
        if sign=="NEAR_ZERO":
            near_zero.append(samples[i]["model_year"])
        if i:
            if (signs[i-1] in ("POSITIVE","NEGATIVE")
                and signs[i] in ("POSITIVE","NEGATIVE")
                and signs[i-1]!=signs[i]):
                definite.append({
                    "from_model_year":samples[i-1]["model_year"],
                    "to_model_year":samples[i]["model_year"],
                    "from_sign":signs[i-1],"to_sign":signs[i],
                    "exact_zero_year_known":False,
                })
    same_endpoints=signs[0]==expected_from and signs[-1]==expected_to
    status=("OUTSIDE_PRIOR_1Y_BRACKET_OR_SIGN_DRIFT" if not same_endpoints
            else "SAMPLED_DEFINITE_BRACKETS" if definite
            else "SAMPLED_NEAR_ZERO_NO_DEFINITE_PAIR" if near_zero
            else "NO_SAMPLED_DEFINITE_SIGN_CHANGE")
    return {
        "source_boundary_id":source_boundary_id,
        "previous_one_year_bracket":[a,b],
        "dt_model_years":float(dt),"observed_status":status,
        "prior_endpoint_signs_reproduced":same_endpoints,
        "actual_endpoint_signs":[signs[0],signs[-1]],
        "definite_sampled_sign_brackets":definite,
        "near_zero_samples":near_zero,
        "no_exact_continuous_time_root_claim":True,
        "no_guarantee_absence_of_substep_crossings":True,
        "source_subyear_gap_samples":samples,
    }


def assess_timestep_differences(dt1,dt05,dt025):
    """Compare same original material ID at common source checkpoint years."""
    need(set(dt1)==set(dt05)==set(dt025)==set(YEARS),
         "DTC_SOURCE_COMMON_CLOCKS_CHANGED")
    err_1_05=0.
    err_05_025=0.
    source_n=0
    for year in YEARS:
        a,b,c=dt1[year],dt05[year],dt025[year]
        need(set(a)==set(b)==set(c) and len(a)==36,
             "DTC_SOURCE_COMMON_IDS_CHANGED")
        for key in a:
            source_n+=1
            err_1_05=max(err_1_05,abs(a[key]-b[key]))
            err_05_025=max(err_05_025,abs(b[key]-c[key]))
    ratio=(err_05_025/err_1_05 if err_1_05>0 else None)
    return {
        "identical_original_source_pairs_common_checkpoint_count":source_n,
        "max_abs_dt1_vs_dt0p5_m":err_1_05,
        "max_abs_dt0p5_vs_dt0p25_m":err_05_025,
        "successive_difference_ratio":ratio,
        "observed_difference_contraction":
            bool(err_05_025<err_1_05) if err_1_05>0 else None,
        "physical_time_step_convergence_certified":False,
        "numerical_order_of_accuracy_claimed":False,
    }


def original_1y_events(prior):
    report=prior["result_16"]
    need(report["original_source_boundary_count"]==36
         and report["original_source_contact_link_count"]==39
         and report["original_source_triple_parent_node_id"]==34587,
         "DTC_PRIOR_ORIGINAL_SOURCE_16_SCOPE_CHANGED")
    rows=report["one_model_year_source_bracket_refinements"]
    byid={r["source_boundary_id"]:r for r in rows}
    need(len(rows)==len(byid)==len(EXPECTED_BRACKETS),
         "DTC_PRIOR_ORIGINAL_ONE_YEAR_BRACKET_DUPLICATE")
    events={}
    for bid,r in byid.items():
        need(bid in EXPECTED_BRACKETS
             and len(r["definite_1y_opposite_nonzero_sign_brackets"])==1
             and not r["sampled_near_zero_years"],
             "DTC_PRIOR_ONE_YEAR_BRACKET_NOT_DEFINITE")
        br=r["definite_1y_opposite_nonzero_sign_brackets"][0]
        co=EXPECTED_BRACKETS[bid]
        need(co[0]<=br["from_year"]<br["to_year"]<=co[1]
             and br["to_year"]-br["from_year"]==1
             and br["from_sign"]==co[2] and br["to_sign"]==co[3],
             "DTC_PRIOR_ONE_YEAR_EVENT_DIRECTION_CHANGED")
        events[bid]=(int(br["from_year"]),int(br["to_year"]),
                     br["from_sign"],br["to_sign"])
    return events


def get_original_geometry(mdir,ndir,omegas):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre, validate_column_for_potential,
    )
    a=next(x for x in json.loads((mdir/"CONTINUATION_A.json").read_text())[
        "topological_comparative_extents"] if int(x["cell_extent_per_side"])==16)
    b=next(x for x in json.loads((ndir/"SOURCE_NODAL_ELEMENT_G2.json").read_text())[
        "scales"] if int(x["extent_cells"])==16)
    ids=list(map(int,a["parent_node_ids"]))
    feg_path=mdir/"OUTER_A_16x16.feg"
    pre_path=mdir/"OUTER_A_16x16_PRE_T0_PASSIVE.dat"
    need(sha256(feg_path)==a["output_FEG_sha256"]
         and sha256(pre_path)==a["output_PRE_sha256"],
         "DTC_AUTHENTIC_FEG_PRE_CHANGED")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    pre=parse_regional_pre(pre_path,a["PRE_source_field_order"],ids)
    need({str(k):v for k,v in pre.items()}==
         {str(k):v for k,v in b["source_PRE_by_parent_node"].items()},
         "DTC_SOURCE_NODAL_BINDING_CHANGED")
    for row in pre.values():
        validate_column_for_potential(row)
    latlon={ids[i]:(float(n.latitude_deg),float(n.longitude_deg))
            for i,n in enumerate(feg.nodes)}
    faces=[tuple(ids[int(n)-1] for n in e.node_ids)
           for e in feg.elements]
    owners=list(map(int,a["parent_triangle_plate_ids"]))
    registry=contact_registry(ids,faces,owners,latlon,a["source_contact_edges"])
    face_rows=source_face_incidence(faces,owners,a["source_contact_edges"])
    need(len(face_rows)==36 and len(registry["contacts"])==39
         and registry["triple_junction_parent_ids"]==[34587],
         "DTC_ORIGINAL_REGION_16_CHANGED")
    K,index,coords,plates,stats=assemble_split_source(
        ids,faces,owners,latlon,pre)
    drive=euler_source_en(coords,plates,omegas)
    J=normal_constraint_matrix(registry["contacts"],index,K.shape[0])
    xyz,radial,east,north=frames_and_cartesian(coords)
    zero=np.zeros_like(drive)
    p0,v0,R0=rigid_motion_with_residual(
        xyz,east,north,plates,omegas,drive,zero,drive,0.)
    return {
        "K":K,"J":J,"drive":drive,
        "index":index,"xyz":xyz,"east":east,"north":north,
        "plates":plates,"faces":face_rows,"positions_0":p0,"velocities_0":v0,
    }


def source_position_and_velocity(state,time_year,source,omegas):
    return rigid_motion_with_residual(
        source["xyz"],source["east"],source["north"],source["plates"],
        omegas,source["drive"],state["displacement"],
        state["velocity"],time_year)[:2]


def advance_source_restart_state(K,J,drive,dt,previous_state):
    """One old T0-KKT step without integer-only checkpoint recording.

    The original integrator stores fractional-step state in 'state', but
    snapshots only at integral model years. Recover its actual endpoint
    velocity via the same u_next = u_previous + dt*v update it uses.
    """
    need(dt in STEP_SIZES,"DTC_UNAUTHORIZED_LOCAL_STEP")
    before=np.asarray(previous_state["displacement"],dtype=float)
    gap_before=np.asarray(previous_state["gap"],dtype=float)
    need(before.shape==np.asarray(drive).shape
         and gap_before.shape==(J.shape[0],)
         and np.all(np.isfinite(before)) and np.all(np.isfinite(gap_before)),
         "DTC_LOCAL_RESTART_INPUT_INVALID")
    result=integrate(K,J,drive,dt,1,initial=previous_state,checkpoints=())
    need(result["steps"]==1
         and result["max_scaled_complementarity"]<1e-8,
         "DTC_SOURCE_LOCAL_RESTART_FAILED")
    state=result["state"]
    after=np.asarray(state["displacement"],dtype=float)
    gap_after=np.asarray(state["gap"],dtype=float)
    velocity=(after-before)/dt
    need(after.shape==before.shape and gap_after.shape==gap_before.shape
         and np.all(np.isfinite(after))
         and np.all(np.isfinite(gap_after))
         and np.all(np.isfinite(velocity)),
         "DTC_LOCAL_RESTART_OUTPUT_INVALID")
    return {
        "displacement":after,
        "gap":gap_after,
        "velocity":velocity,
    },state


def collect_dt(dt,source,omegas,prior_25,events,source_zero):
    need(dt in STEP_SIZES,"DTC_UNAUTHORIZED_DT")
    checkpoint_years=tuple(sorted(set(YEARS[1:]).union(
        [year for a,b,*_ in events.values() for year in (a,b)])))
    n=int(round(1000/dt))
    need(abs(n*dt-1000)<1e-8,
         "DTC_STEP_CLOCK_NOT_INTEGER_YEAR_END")
    integ=integrate(source["K"],source["J"],source["drive"],dt,n,
                    checkpoints=checkpoint_years)
    need(integ["max_scaled_complementarity"]<1e-8,
         "DTC_ORIGINAL_LINEARIZED_KKT_COMPLEMENTARITY_FAILED")
    need(set(integ["snapshots"])==set(checkpoint_years),
         "DTC_EXPECTED_COMMON_SOURCE_SNAPSHOTS_MISSING")
    old25={int(y):original_source_row_map(rows)
           for y,rows in prior_25.items()}
    need(set(old25)==set(YEARS),
         "DTC_SHA_PINNED_25Y_SCOPE_CHANGED")
    zero=source_matched_gaps(
        source["faces"],source["index"],source["positions_0"])
    need(max(abs(v) for v in zero.values())<1e-8
         and set(zero)==set(source_zero),
         "DTC_ORIGINAL_T0_SOURCE_GAP_CHANGED")
    all_gap={0:zero}
    same_clock_comparisons=[]
    for year in checkpoint_years:
        ss=integ["snapshots"][year]
        pos,vel=source_position_and_velocity(ss,year,source,omegas)
        gaps=source_matched_gaps(source["faces"],source["index"],pos)
        all_gap[year]=gaps
        if year in YEARS:
            same_clock_comparisons.append(
                compare_original_source_samples(
                    list(old25[year].values()),gaps,dt,year))
    # Only source 25y samples are public common-clock provenance anchors.
    all25={year:all_gap[year] for year in YEARS}
    bysource={x["source_boundary_id"]:x for x in source["faces"]}
    need(all(k in bysource for k in events),"DTC_1YEAR_SOURCE_EDGE_MISSING")
    refined=[]
    local_replay_max=0.
    for bid,event in sorted(events.items()):
        begin,end,sig0,sig1=event
        key=bysource[bid]
        begin_state=integ["snapshots"][begin]
        cur={
            "displacement":begin_state["displacement"].copy(),
            "gap":begin_state["gap"].copy(),
        }
        samples=[{"model_year":float(begin),
                  "signed_shell_midpoint_gap_m":all_gap[begin][bid]}]
        count=int(round((end-begin)/dt))
        need(count in (2,4),"DTC_WRONG_LOCAL_SUBSTEPS")
        for step in range(1,count+1):
            year=begin+dt*step
            snapshot,next_state=advance_source_restart_state(
                source["K"],source["J"],source["drive"],dt,cur)
            pos,vel=source_position_and_velocity(snapshot,year,source,omegas)
            # Include the entire authentic source edge set to preserve
            # original paired IDs under restarted local stepping.
            gap=source_matched_gaps(source["faces"],source["index"],pos)
            samples.append({
                "model_year":float(year),
                "signed_shell_midpoint_gap_m":gap[bid],
            })
            cur=next_state
        end_err=abs(samples[-1]["signed_shell_midpoint_gap_m"]-
                    all_gap[end][bid])
        local_replay_max=max(local_replay_max,end_err)
        need(end_err<SOURCE_BOUNDARY_REPLAY_MAX_ABS_M,
             "DTC_SUBSTEP_RESTART_DRIFT_FROM_FULL_TRAJECTORY")
        refined.append(analyze_subyear_samples(bid,event,samples,dt))
    triple={}
    for year in (0,100,500,1000):
        if year==0:
            pos=source["positions_0"];vel=source["velocities_0"]
        else:
            pos,vel=source_position_and_velocity(
                integ["snapshots"][year],year,source,omegas)
        triple[str(year)]=triple_material_view_audit(
            34587,(5,8,11),source["index"],pos,vel)
    return {
        "dt_model_years":float(dt),
        "steps":n,
        "original_source_checkpoint_count":len(YEARS),
        "source_gap_at_all_original_25y_clocks":all25,
        "comparisons_to_original_verified_dt1":same_clock_comparisons,
        "one_year_source_brackets_refined_at_this_dt":refined,
        "max_local_restart_vs_global_endpoint_gap_error_m":local_replay_max,
        "triple_source_views_at_original_years":triple,
        "numeric_time_step_convergence_claimed":False,
        "physical_contact_response_solved":False,
    }


def execute(multiscale,nodal,unilateral,prior_event,prior_differential,out,root=ROOT):
    mdir,ndir,un,event,prior25,out,root=map(
        Path,(multiscale,nodal,unilateral,prior_event,prior_differential,out,root))
    need(not out.exists(),"DTC_OUTPUT_ALREADY_EXISTS")
    began=time.perf_counter()
    pins=certify_priors(mdir,ndir,un,root)
    man=json.loads((event/"MANIFEST.json").read_text())
    report=json.loads((event/"REPORT.json").read_text())
    need(man["schema"]=="ARCANA_R6_SHELL_1YEAR_EVENT_REFINEMENT_MANIFEST_V1"
         and man["files"]["REPORT.json"]==sha256(event/"REPORT.json")
         and sha256(event/"REPORT.json")==PRIOR_REPORT_SHA
         and report["status"]==
         "PASS_SOURCE_SHELL_1Y_EVENT_BRACKET_REFINEMENT__PHYSICAL_SOLID_CONTACT_OPEN"
         and report["physical_T1"] is None and report["D_024"]=="ACTIVE"
         and report["updated_3D_KKT_executed"] is False,
         "DTC_PRIOR_ONE_YEAR_SOURCE_REPORT_AUTHORITY_FAILED")
    for path,digest in report["source_sha256"].items():
        need(Path(path).is_file() and sha256(Path(path))==digest,
             "DTC_PRIOR_SOURCE_SHA_PIN_DRIFT")
    man25=json.loads((prior25/"MANIFEST.json").read_text())
    old25=json.loads((prior25/"REPORT.json").read_text())
    need(man25["schema"]=="ARCANA_R6_SHELL_DIFFERENTIAL_KINEMATICS_MANIFEST_V1"
         and man25["files"]["REPORT.json"]==sha256(prior25/"REPORT.json")
         and sha256(prior25/"REPORT.json")==
         "29ce93ffed7dae94be7cff16f92b3bb8a4f82020140a2adc0d6056270f38c1d5"
         and old25["physical_T1"] is None
         and old25["D_024"]=="ACTIVE",
         "DTC_PRIOR_25Y_SOURCE_REPORT_INVALID")
    pins[str(event/"REPORT.json")]=sha256(event/"REPORT.json")
    pins[str(event/"MANIFEST.json")]=sha256(event/"MANIFEST.json")
    pins[str(prior25/"REPORT.json")]=sha256(prior25/"REPORT.json")
    pins[str(prior25/"MANIFEST.json")]=sha256(prior25/"MANIFEST.json")
    mesh,omega,raw,horizon,meta=source_inputs(root)
    need(horizon>1000,"DTC_SOURCE_HORIZON_INVALID")
    regions={int(r["extent"]):r for r in old25["results"]}
    need(set(regions)=={8,16},"DTC_25Y_SOURCE_REGIONS_CHANGED")
    prior=regions[16]["source_original_midpoint_gap_per_year"]
    event_rows=report["result_16"]["one_model_year_source_bracket_refinements"]
    need(len(event_rows)==4,"DTC_ORIGINAL_ONE_YEAR_EVENT_COUNT_CHANGED")
    events=original_1y_events(report)
    source=get_original_geometry(mdir,ndir,omega)
    orig25={int(year):{
        bid:r["signed_shell_midpoint_gap_m"]
        for bid,r in original_source_row_map(rows).items()}
        for year,rows in prior.items()}
    need(set(orig25)==set(YEARS),"DTC_PREVIOUS_SOURCE_25Y_YEAR_SET_CHANGED")
    original=source_matched_gaps(
        source["faces"],source["index"],source["positions_0"])
    need(max(abs(original[bid]-orig25[0][bid]) for bid in original)
         <SOURCE_BOUNDARY_REPLAY_MAX_ABS_M,
         "DTC_T0_SOURCE_PRIOR_REPLAY_CHANGED")
    results=[
        collect_dt(dt,source,omega,prior,events,original)
        for dt in STEP_SIZES
    ]
    compare=assess_timestep_differences(
        orig25,
        results[0]["source_gap_at_all_original_25y_clocks"],
        results[1]["source_gap_at_all_original_25y_clocks"])
    need(all(sha256(Path(p))==h for p,h in pins.items()),
         "DTC_SOURCE_PROVIDER_CHANGED_DURING_COMPARISON")
    output={
        "schema":SCHEMA,"status":STATUS,
        "tested_original_source_prior_1y_report_SHA":PRIOR_REPORT_SHA,
        "source_world_mesh_sha256":mesh.normalized_sha256,
        "source_sha256":pins,
        "results":results,
        "source_25y_original_clock_timestep_differences":compare,
        "only_old_T0_fixed_normal_KKT_trajectory_integrated":True,
        "no_physical_solid_signorini_criterion_qualified":True,
        "rate_or_event_convergence_not_auto_certified":True,
        "physical_solver_runs":0,
        "updated_geometry_KKT_executed":False,"physical_T1":None,
        "D_024":"ACTIVE","HistoryStore_modified":False,
        "canonical_promotion":False,
        "total_wall_seconds":time.perf_counter()-began,
        "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    rp=out/"REPORT.json"
    rp.write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_SOURCE_SHELL_DT_CONVERGENCE_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(rp)},
        "physical_T1":None,"no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":STATUS,
        "source_25y_original_clock_timestep_differences":compare,
        "results":[{
            "dt_model_years":r["dt_model_years"],
            "steps":r["steps"],
            "max_local_restart_replay_error_m":
                r["max_local_restart_vs_global_endpoint_gap_error_m"],
            "source_one_year_event_sub_brackets":[{
                "source_boundary_id":e["source_boundary_id"],
                "status":e["observed_status"],
                "definite_sampled_sign_brackets":
                    e["definite_sampled_sign_brackets"],
                "near_zero_samples":e["near_zero_samples"],
            } for e in r["one_year_source_brackets_refined_at_this_dt"]],
        } for r in results],
        "physical_T1":None,"D_024":"ACTIVE",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--prior-unilateral",type=Path,required=True)
    p.add_argument("--prior-event",type=Path,required=True)
    p.add_argument("--prior-differential",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    print(json.dumps(execute(
        args.multiscale,args.nodal,args.prior_unilateral,args.prior_event,
        args.prior_differential,args.output,args.root),
        indent=2,allow_nan=False))


if __name__=="__main__":
    main()
