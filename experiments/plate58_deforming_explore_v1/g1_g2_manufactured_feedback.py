"""R6: source-keyed manufactured G1 <-> G2 Kelvin-Voigt feedback.

Only an ENGINEERING numerical experiment. Original plate Euler and 51-field
T0 PRE source IDs are preserved. Viscosity, relaxation time and driving
dashpot are invented, NOT ARCANA geology or a valid natural G3 force.
No HistoryStore, no physical solver, no physical T1.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import numpy as np

SECONDS_PER_YEAR = 31557600.0
TAU_YEARS = 200.0
ETA_CRUST_PA_S = 1.e20
ETA_MANTLE_PA_S = 1.e21
DASHPOT_TO_MEAN_TANGENT = 0.5
STATUS = "PASS_G1_G2_MANUFACTURED_TWO_WAY_FEEDBACK__REAL_PHYSICS_OPEN"


class ManufacturedError(ValueError):
    pass


def need(ok, tag):
    if not ok:
        raise ManufacturedError(tag)


def linear_feedback_modes(K, drag_coefficient):
    """Diagonalize manufactured K/C, where both K,C have units N s/m."""
    k=np.asarray(K,dtype=float)
    c=float(drag_coefficient)
    need(k.ndim==2 and k.shape[0]==k.shape[1] and k.shape[0]>=2
         and np.all(np.isfinite(k))
         and np.allclose(k,k.T,rtol=1e-12,atol=0)
         and math.isfinite(c) and c>0, "COUPLED_STIFFNESS_OR_DASHPOT_INVALID")
    lam,Q=np.linalg.eigh(k/c)
    scale=max(1.,float(np.max(np.abs(lam))))
    need(lam[0]>=-1e-9*scale,"COUPLED_STIFFNESS_NOT_POSITIVE_SEMIDEFINITE")
    return np.maximum(lam,0.),Q


def evolve_modes(lam,Q,drives,dt_years,*,tau_years=TAU_YEARS,
                 initial=None,years_start=0,checkpoints=()):
    """Implicit Euler: C(v_G1-v)=K v + (K/tau) u_new, u_new=u+dt*v.

    v and G1 drive are in m/model-year, u in m. Units of force are
    recovered by division by seconds/year. This is a manufactured
    Kelvin-Voigt/linearized test, not experimentally calibrated creep.
    """
    lam=np.asarray(lam,dtype=float)
    q=np.asarray(Q,dtype=float)
    g=np.asarray(drives,dtype=float)
    dt=float(dt_years);tau=float(tau_years)
    need(lam.ndim==1 and q.shape==(len(lam),len(lam))
         and g.ndim==2 and g.shape[1]==len(lam) and len(g)>0
         and np.all(np.isfinite(lam)) and np.all(lam>=0)
         and np.all(np.isfinite(q)) and np.all(np.isfinite(g))
         and math.isfinite(dt) and dt>0 and math.isfinite(tau) and tau>0
         and math.isfinite(years_start) and years_start>=0,
         "COUPLED_EVOLUTION_INPUT_INVALID")
    z=np.zeros(len(lam)) if initial is None else np.asarray(initial,dtype=float).copy()
    need(z.shape==lam.shape and np.all(np.isfinite(z)),
         "COUPLED_RESTART_STATE_INVALID")
    projections=g@q
    checkpoints=set(map(int,checkpoints))
    states={};maximum_velocity=0.;max_balance=0.;max_energy=0.
    denominator=1.+lam+dt*lam/tau
    for i,driver in enumerate(projections,1):
        previous=z.copy()
        v=(driver-lam*previous/tau)/denominator
        z=previous+dt*v
        balance=(driver-v)-lam*(v+z/tau)
        ref=np.linalg.norm(driver)+np.linalg.norm(v)+np.linalg.norm(lam*(v+z/tau))
        max_balance=max(max_balance,float(np.linalg.norm(balance)/max(ref,1e-30)))
        eprev=0.5*np.sum(lam*previous**2)/tau
        enext=0.5*np.sum(lam*z**2)/tau
        drive_work=dt*float(driver@v)
        dissipative=dt*float(np.sum((1.+lam)*v**2))
        elastic_backwards=(enext-eprev)+0.5*dt**2*float(np.sum(lam*v**2))/tau
        max_energy=max(max_energy,abs(drive_work-dissipative-elastic_backwards)/
                       max(abs(drive_work),abs(dissipative+elastic_backwards),1e-25))
        maximum_velocity=max(maximum_velocity,float(np.max(np.abs(v))))
        year=years_start+i*dt
        if any(abs(year-cp)<1e-8 for cp in checkpoints):
            states[int(round(year))]={
                "modes":z.copy(),"velocity_modes":v.copy(),
                "driver_modes":driver.copy(),
                "elastic_energy_normalized":float(enext)}
    return {"final_modes":z,"states":states,"last_velocity_modes":v,
            "max_balance_relative":max_balance,
            "max_backward_euler_energy_identity_relative":max_energy,
            "max_velocity_mode_m_per_year":maximum_velocity,
            "linear_solve_count":len(g)}


def source_plate_weights(region):
    ids=list(map(int,region["parent_node_ids"]))
    triangles=list(map(int,region["parent_triangle_ids"]))
    plates=list(map(int,region["parent_triangle_plate_ids"]))
    faces=region["faces_parent_nodes"]
    need(len(ids)==len(set(ids)) and len(plates)==len(triangles)==len(faces),
         "COUPLED_PARENT_PLATE_OWNERSHIP_INVALID")
    weights=defaultdict(Counter)
    for plate,face in zip(plates,faces,strict=True):
        for node in face:
            weights[int(node)][plate]+=1
    need(set(weights)==set(ids),"COUPLED_EULER_NODE_NOT_OWNED")
    return weights


def euler_driver(ll,weights,omegas,year):
    """One invented weighted-mean tangent G1 drive for each shared source DOF."""
    from experiments.global_t0_kinematic_baseline_v1.benchmark import rotate_xyz
    from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
    ids=list(weights)
    xyz,radial,east,north=frames_and_cartesian(np.array([ll[n] for n in ids]))
    result=np.zeros((len(ids),2))
    for plate in sorted({p for node in ids for p in weights[node]}):
        inds=np.array([i for i,node in enumerate(ids) if plate in weights[node]],
                      dtype=int)
        omega=np.asarray(omegas[plate],dtype=float)
        need(omega.shape==(3,) and np.all(np.isfinite(omega)),
             "COUPLED_EULER_ANGULAR_VELOCITY_INVALID")
        moved=rotate_xyz(radial[inds],omega,year)
        vxyz=np.cross(omega,moved)*np.linalg.norm(xyz[inds],axis=1)[:,None]
        vv=np.stack((np.sum(vxyz*east[inds],axis=1),
                     np.sum(vxyz*north[inds],axis=1)),axis=1)
        frac=np.array([weights[ids[i]][plate]/sum(weights[ids[i]].values())
                       for i in inds],dtype=float)
        result[inds]+=frac[:,None]*vv
    need(bool(np.all(np.isfinite(result))),"COUPLED_G1_DRIVER_NONFINITE")
    return result.reshape(-1)


def triangle_areas_and_mass(ll,faces,ids,pre,displacement):
    from experiments.global_t0_kinematic_baseline_v1.benchmark import spherical_area_sr
    from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
    loc=np.stack([ll[i] for i in ids])
    xyz,unit,e,n=frames_and_cartesian(loc)
    uv=np.asarray(displacement).reshape(len(ids),2)
    moved=xyz+e*uv[:,0,None]+n*uv[:,1,None]
    moved/=np.linalg.norm(moved,axis=1)[:,None]
    ix={node:i for i,node in enumerate(ids)}
    faces_idx=np.array([[ix[n] for n in face] for face in faces],dtype=int)
    a0=spherical_area_sr(unit,faces_idx)
    a1=spherical_area_sr(moved,faces_idx)
    need(np.all(a0>0) and np.all(a1>0),"COUPLED_TRIANGLE_INVERTED")
    jac=a1/a0
    areal=np.array([
        float(pre[node]["crust_density_kg_m3"])*float(pre[node]["crust_thickness_m"])
        +float(pre[node]["mantle_density_kg_m3"])*
         float(pre[node]["mantle_lithosphere_thickness_m"])
        for node in ids])
    val=np.mean(areal[faces_idx],axis=1)
    mass0=float(np.sum(val*a0))
    mass1=float(np.sum((val/jac)*a1))
    return {"min_jacobian_area":float(np.min(jac)),
            "max_jacobian_area":float(np.max(jac)),
            "max_absolute_area_ratio_minus_one":float(np.max(np.abs(jac-1.))),
            "manufactured_layer_mass_relative_residual":abs(mass1-mass0)/mass0,
            "mass_rule":"LAGRANGIAN_H_NEW_EQ_H_T0_DIVIDED_BY_AREA_JACOBIAN__NOT_REAL_G4"}


def run_scale(region,omegas):
    from experiments.plate58_deforming_explore_v1.spherical_exterior import assemble_spherical_exterior
    width=int(region["width"])
    ids=list(map(int,region["parent_node_ids"]))
    need(width in (8,16) and len(ids)==(width+1)**2
         and len(set(ids))==len(ids)
         and len(region["faces_parent_nodes"])==2*width**2,
         "COUPLED_SOURCE_REGION_SIZE_INVALID")
    faces={int(tid):tuple(face) for tid,face in zip(
        region["parent_triangle_ids"],region["faces_parent_nodes"],strict=True)}
    ll=region["latlon"];pre=region["PRE_by_node"]
    need(set(ll)==set(pre)==set(ids),"COUPLED_SOURCE_PRE_COVERAGE_INVALID")
    material={}
    for tid,face in faces.items():
        hc=np.mean([pre[node]["crust_thickness_m"] for node in face])
        hm=np.mean([pre[node]["mantle_lithosphere_thickness_m"] for node in face])
        viscosity_thickness=ETA_CRUST_PA_S*hc+ETA_MANTLE_PA_S*hm
        material[tid]={
            "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "source_reference":"MANUFACTURED_TWO_LAYER_KELVIN_VOIGT_20261120",
            "eta_h_pa_s_m":float(viscosity_thickness),
            "lambda_h_pa_s_m":float(viscosity_thickness)}
    fem=assemble_spherical_exterior(ids,faces,ll,material)
    K=np.asarray(fem["tangent"],dtype=float)
    c=DASHPOT_TO_MEAN_TANGENT*float(np.mean(np.diag(K)))
    lam,Q=linear_feedback_modes(K,c)
    weights=source_plate_weights(region)
    ordered={i:weights[i] for i in ids}
    def solve(dt):
        need(100%dt==0 and 500%dt==0 and 1000%dt==0,
             "COUPLED_DT_MUST_DIVIDE_CHECKPOINTS")
        times=np.arange(0,1000,dt,dtype=float)+dt/2
        drives=np.stack([euler_driver(ll,ordered,omegas,float(t)) for t in times])
        full=evolve_modes(lam,Q,drives,dt,checkpoints=(100,500,1000))
        first=evolve_modes(lam,Q,drives[:500//dt],dt,checkpoints=(500,))
        second=evolve_modes(lam,Q,drives[500//dt:],dt,
                            initial=first["final_modes"],years_start=500,
                            checkpoints=(1000,))
        restart=float(np.max(np.abs(full["final_modes"]-second["final_modes"])))
        need(restart<=1e-8,"COUPLED_RESTART_DIVERGENCE")
        return full,restart
    f1,restart=solve(1)
    f5,_=solve(5)
    f10,_=solve(10)
    by_year={}
    for year in (100,1000):
        state=f1["states"][year]
        u=Q@state["modes"]
        v=Q@state["velocity_modes"]
        v_g1=Q@state["driver_modes"]
        drive_force=c*(v_g1-v)
        g2_force=K@(v+u/TAU_YEARS)
        relative_balance=float(np.linalg.norm(drive_force-g2_force)/
            max(np.linalg.norm(drive_force)+np.linalg.norm(g2_force),1e-30))
        need(relative_balance<1e-9,"COUPLED_FORCE_BALANCE_FAILED")
        metric=triangle_areas_and_mass(ll,list(faces.values()),ids,pre,u)
        need(metric["max_absolute_area_ratio_minus_one"]<0.05
             and metric["manufactured_layer_mass_relative_residual"]<1e-10,
             "COUPLED_AREA_OR_MANUFACTURED_MASS_FAILED")
        err5=float(np.max(np.abs(Q@(f5["states"][year]["modes"]-state["modes"]))))
        err10=float(np.max(np.abs(Q@(f10["states"][year]["modes"]-state["modes"]))))
        max_displacement=float(np.max(np.linalg.norm(u.reshape(-1,2),axis=1)))
        need(err10/max(float(np.max(np.abs(u))),1.)<0.1,
             "COUPLED_TIMESTEP_REFINEMENT_FAILED")
        speed_difference=float(np.sqrt(np.mean((v-v_g1)**2)))
        need(speed_difference>0,"COUPLED_NO_G2_FEEDBACK_DETECTED")
        by_year[str(year)]={
            "max_displacement_m":max_displacement,
            "g1_target_rms_speed_m_per_year":float(np.sqrt(np.mean(v_g1**2))),
            "coupled_rms_speed_m_per_year":float(np.sqrt(np.mean(v**2))),
            "coupled_minus_g1_velocity_rms_m_per_year":speed_difference,
            "manufactured_internal_force_balance_relative":relative_balance,
            "stored_elastic_energy_normalized":state["elastic_energy_normalized"],
            "area_and_mass":metric,
            "max_displacement_dt5_minus_dt1_m":err5,
            "max_displacement_dt10_minus_dt1_m":err10}
    need(f1["max_balance_relative"]<1e-9
         and f1["max_backward_euler_energy_identity_relative"]<1e-8,
         "COUPLED_VIRTUAL_WORK_OR_ENERGY_CHECK_FAILED")
    return {
        "extent":width,"source_nodes":len(ids),
        "source_triangles":len(faces),
        "source_plates":sorted(set(region["parent_triangle_plate_ids"])),
        "triple_node_34587_present":34587 in ids,
        "mechanical_dofs":2*len(ids),
        "manufactured_source":"SPHERICAL_P1_TWO_LAYER_PRE_THICKNESS_KELVIN_VOIGT",
        "manufactured_crust_viscosity_pa_s":ETA_CRUST_PA_S,
        "manufactured_mantle_viscosity_pa_s":ETA_MANTLE_PA_S,
        "manufactured_memory_time_years":TAU_YEARS,
        "manufactured_drag_to_mean_K_diagonal":DASHPOT_TO_MEAN_TANGENT,
        "G1_multiplate_interface_rule":
           "INCIDENT_TRIANGLE_WEIGHTED_MEAN_ONLY__SYNTHETIC_WELDED_DOF",
        "G2_velocity_tangent_positive_semidefinite":bool(np.min(lam)>=0),
        "max_implicit_balance_relative":f1["max_balance_relative"],
        "max_energy_identity_relative":f1["max_backward_euler_energy_identity_relative"],
        "restart_500_plus_500_max_modal_displacement_error_m":restart,
        "engineering_primary_linear_step_solutions":
            int(f1["linear_solve_count"]+f5["linear_solve_count"]+
                f10["linear_solve_count"]),
        "engineering_restart_replay_linear_step_solutions":1300,
        "physical_solver_runs":0,
        "results":by_year,
        "physical_g2_material_rheology":None,
        "physical_g3_force_provider":None,
        "mechanical_solve_authorized":False,"physical_T1":None}


def run(multiscale_dir:Path,nodal_dir:Path,g1_audit_dir:Path,
        output:Path,root:Path):
    from experiments.plate58_deforming_explore_v1.prepare import sha
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential)
    from experiments.global_t0_kinematic_baseline_v1.benchmark import sha256
    need(not output.exists(),"COUPLED_OUTPUT_EXISTS")
    def j(path):return json.loads(path.read_text())
    mm=j(multiscale_dir/"MANIFEST.json")
    m=j(multiscale_dir/"CONTINUATION_A.json")
    nm=j(nodal_dir/"MANIFEST.json")
    n=j(nodal_dir/"SOURCE_NODAL_ELEMENT_G2.json")
    ga=j(g1_audit_dir/"MANIFEST.json")
    gr=j(g1_audit_dir/"REPORT.json")
    need(mm["files"]["CONTINUATION_A.json"]==
         sha(multiscale_dir/"CONTINUATION_A.json")
         and nm["files"]["SOURCE_NODAL_ELEMENT_G2.json"]==
         sha(nodal_dir/"SOURCE_NODAL_ELEMENT_G2.json")
         and ga["files"]["REPORT.json"]==sha(g1_audit_dir/"REPORT.json")
         and n["source_multiscale_manifest_sha256"]==
             sha(multiscale_dir/"MANIFEST.json")
         and gr["status"]==
             "PASS_G1_G2_100_1000Y_PASSIVE_SOURCE_COUPLING__REAL_G2_PHYSICS_OPEN"
         and gr["G2_source_profile_audit"]["source_columns_eligible"]==64442
         and gr["physical_T1"] is None and n["physical_T1"] is None
         and m["mechanical_solve_authorized"] is False,
         "COUPLED_SOURCE_MANIFEST_OR_AUTHORITY_INVALID")
    need(gr["source_PRE_SHA256"]==
         sha256(root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat")
         and m["source_PRE_sha256"]==gr["source_PRE_SHA256"],
         "COUPLED_G2_SOURCE_PRE_LINEAGE_MISMATCH")
    euler=j(root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    omegas={int(x["plate_id"]):np.asarray(x["euler_vector_rad_per_year"],dtype=float)
            for x in euler["plates"]}
    regions={int(v["cell_extent_per_side"]):v
             for v in m["topological_comparative_extents"]}
    nodal={int(v["extent_cells"]):v for v in n["scales"]}
    need(set(regions)==set(nodal)=={8,16},
         "COUPLED_NESTED_SCALE_INVENTORY_CHANGED")
    pinned_sources={
        "multiscale_manifest":sha(multiscale_dir/"MANIFEST.json"),
        "multiscale_context":sha(multiscale_dir/"CONTINUATION_A.json"),
        "nodal_manifest":sha(nodal_dir/"MANIFEST.json"),
        "nodal_binding":sha(nodal_dir/"SOURCE_NODAL_ELEMENT_G2.json"),
        "g1_audit_manifest":sha(g1_audit_dir/"MANIFEST.json"),
        "g1_audit_report":sha(g1_audit_dir/"REPORT.json"),
        "global_pre":sha(root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"),
        "global_euler":sha(root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json"),
    }
    outputs=[]
    for width in (8,16):
        region=regions[width];bound=nodal[width]
        ids=list(map(int,region["parent_node_ids"]))
        feg_path=multiscale_dir/f"OUTER_A_{width:02d}x{width:02d}.feg"
        pre_path=multiscale_dir/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
        need(sha(feg_path)==region["output_FEG_sha256"]
             and sha(pre_path)==region["output_PRE_sha256"],
             "COUPLED_SOURCE_FEG_OR_PRE_HASH_FAILED")
        feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
        actual_pre=parse_regional_pre(pre_path,region["PRE_source_field_order"],ids)
        need({str(k):v for k,v in actual_pre.items()}==
             {str(k):v for k,v in bound["source_PRE_by_parent_node"].items()},
             "COUPLED_G2_SOURCE_BINDING_DIFFERENCE")
        for row in actual_pre.values():
            validate_column_for_potential(row)
        faces=[tuple(ids[int(v)-1] for v in el.node_ids) for el in feg.elements]
        need(len(faces)==len(region["parent_triangle_ids"]),
             "COUPLED_SOURCE_FACES_INVALID")
        ll={ids[i]:(float(node.latitude_deg),float(node.longitude_deg))
            for i,node in enumerate(feg.nodes)}
        r={"width":width,"parent_node_ids":ids,
           "parent_triangle_ids":list(map(int,region["parent_triangle_ids"])),
           "parent_triangle_plate_ids":list(map(int,region["parent_triangle_plate_ids"])),
           "faces_parent_nodes":faces,"latlon":ll,"PRE_by_node":actual_pre}
        outputs.append(run_scale(r,omegas))
    need(outputs[0]["source_nodes"]==81 and outputs[1]["source_nodes"]==289
         and outputs[1]["triple_node_34587_present"],
         "COUPLED_SOURCE_TRIPLE_NODE_OR_WIDTH_INVALID")
    need(pinned_sources=={
        "multiscale_manifest":sha(multiscale_dir/"MANIFEST.json"),
        "multiscale_context":sha(multiscale_dir/"CONTINUATION_A.json"),
        "nodal_manifest":sha(nodal_dir/"MANIFEST.json"),
        "nodal_binding":sha(nodal_dir/"SOURCE_NODAL_ELEMENT_G2.json"),
        "g1_audit_manifest":sha(g1_audit_dir/"MANIFEST.json"),
        "g1_audit_report":sha(g1_audit_dir/"REPORT.json"),
        "global_pre":sha(root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"),
        "global_euler":sha(root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json"),
    }, "COUPLED_SOURCE_CHANGED_DURING_ENGINEERING_TEST")
    report={
        "schema":"ARCANA_R6_G1_G2_MANUFACTURED_FEEDBACK_100_1000Y_V1",
        "status":STATUS,
        "source_g1_audit_manifest_sha256":sha(g1_audit_dir/"MANIFEST.json"),
        "source_multiscale_manifest_sha256":sha(multiscale_dir/"MANIFEST.json"),
        "source_g2_nodal_manifest_sha256":sha(nodal_dir/"MANIFEST.json"),
        "time_steps_years":[1,5,10],"horizons_years":[100,1000],
        "engineering_viscoelastic_solutions_made":True,
        "no_actual_G2_lab_rock_parameters":True,
        "no_G3_natural_force_or_basal_normal":True,
        "source_G1_Euler_kinematics_was_modified":False,
        "source_G2_PRE_was_modified":False,
        "HistoryStore_modified":False,"scales":outputs,
        "physical_solver_runs":0,
        "mechanical_solve_authorized":False,
        "physical_T1":None,"D_024":"ACTIVE"}
    output.mkdir(parents=True,exist_ok=False)
    p=output/"REPORT.json"
    p.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_G1_G2_MANUFACTURED_FEEDBACK_MANIFEST_V1",
        "status":STATUS,
        "files":{"REPORT.json":sha(p)},
        "no_physical_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True},indent=2)+"\n")
    return {"status":STATUS,"scales":outputs,
            "physical_solver_runs":0,"physical_T1":None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",required=True,type=Path)
    p.add_argument("--nodal",required=True,type=Path)
    p.add_argument("--g1-audit",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2])
    a=p.parse_args()
    print(json.dumps(run(a.multiscale,a.nodal,a.g1_audit,a.output,a.root),indent=2))


if __name__=="__main__":
    main()
