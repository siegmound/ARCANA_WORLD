"""R6: global 100/1000 model-year manufactured G1<->G2 sparse P1 time test.

Fixed source-T0 spherical-facet tangent and co-rotating source material frame.
12 plate-local views stay INDEPENDENT (unwelded). The constant Euler velocity
is a rigid mode on each view. Small nonrigid input is purely ENGINEERING.
No contact/slip/open law, G3 real load, evolving mesh stiffness, history or T1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import cg, LinearOperator

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, PLATES, NODES, TRIANGLES, source_inputs, build_views,
    spherical_area_sr, sha256, usage,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    assemble_real_global_source, SparseP1Error,
)
from experiments.plate58_deforming_explore_v1.g1_g2_manufactured_feedback import (
    TAU_YEARS, DASHPOT_TO_MEAN_TANGENT,
)

STATUS="PASS_SOURCE_GLOBAL_SPARSE_P1_G1_G2_MANUFACTURED_100_1000Y__PHYSICS_OPEN"
SCHEMA="ARCANA_R6_SOURCE_GLOBAL_SPARSE_P1_MANUFACTURED_TIME_V1"

def require(ok,code):
    if not ok:
        raise SparseP1Error(code)


def iterate_global(K_over_C, driving, dt_years, steps,
                   *,tau_years=200.,initial=None,start_year=0,
                   checkpoints=(100,500,1000),rtol=1e-8):
    """Implicit Euler: g=v+L(v+u_new/tau), u_new=u+dt*v.

    K/C is dimensionless. v in metres/model-year, u in metres.
    Source frame is FIXED and plate co-moving, not Euler-updated geometry.
    """
    L=sparse.csr_matrix(K_over_C)
    target=np.asarray(driving,dtype=np.float64)
    dt=float(dt_years);tau=float(tau_years);steps=int(steps)
    require(L.shape==(len(target),len(target)) and len(target)>=2 and
            np.all(np.isfinite(L.data)) and np.all(np.isfinite(target)) and
            bool(np.all(np.isfinite(L.diagonal()))) and
            bool(np.all(L.diagonal()>=0)) and
            dt>0 and tau>0 and math.isfinite(dt) and math.isfinite(tau) and
            steps>0 and math.isfinite(start_year) and start_year>=0 and
            math.isfinite(rtol) and 0<rtol<=1e-6,
            "GLOBAL_TIME_INVALID_INPUT")
    if initial is None:
        u=np.zeros_like(target)
        velocity=np.zeros_like(target)
    else:
        u=np.asarray(initial["u"],dtype=np.float64).copy()
        velocity=np.asarray(initial["v"],dtype=np.float64).copy()
        require(u.shape==target.shape and velocity.shape==target.shape and
                np.all(np.isfinite(u)) and np.all(np.isfinite(velocity)),
                "GLOBAL_TIME_RESTART_INVALID")
    A=sparse.eye(len(target),format="csr")+L*(1.+dt/tau)
    diag=A.diagonal()
    require(np.all(np.isfinite(diag)) and bool(np.all(diag>0)),
            "GLOBAL_TIME_BAD_JACOBI_DIAGONAL")
    inv_diag=1./diag
    M=LinearOperator(A.shape,matvec=lambda x:inv_diag*x,dtype=np.float64)
    checkpoints=set(map(int,checkpoints))
    snapshots={}
    total_iters=0; max_iters=0; max_residual=0.;max_energy=0.
    t0=time.perf_counter()
    for step in range(1,steps+1):
        prev=u
        Lu=L@prev
        rhs=target-Lu/tau
        its=[0]
        def cb(_):its[0]+=1
        v,info=cg(A,rhs,x0=velocity,rtol=rtol,atol=0.,
                  M=M,maxiter=1200,callback=cb)
        require(info==0 and np.all(np.isfinite(v)),
                "GLOBAL_TIME_CG_FAILED")
        u=prev+dt*v
        Lv=L@v
        residual_vec=(target-v)-Lv-(Lu+dt*Lv)/tau
        residual=float(np.linalg.norm(residual_vec)/
                       max(np.linalg.norm(target)+np.linalg.norm(v)+
                           np.linalg.norm(Lv)+
                           np.linalg.norm((Lu+dt*Lv)/tau),1e-30))
        # Discrete implicit-Euler virtual-work identity, including
        # the positive backward-Euler numerical dissipation term.
        drive=dt*float(target@v)
        dissipation=dt*float(v@v+v@Lv)
        delta_elastic=(float(u@(Lu+dt*Lv))-float(prev@Lu))/(2*tau)
        numerical_dissipation=dt*dt*float(v@Lv)/(2*tau)
        energy=abs(drive-dissipation-delta_elastic-numerical_dissipation) / (
            max(abs(drive),abs(dissipation+delta_elastic+
                              numerical_dissipation),1e-20))
        require(math.isfinite(residual) and math.isfinite(energy) and
                residual<2e-7 and energy<2e-7,
                "GLOBAL_TIME_WORK_OR_IMPLICIT_BALANCE_FAILED")
        max_residual=max(max_residual,residual)
        max_energy=max(max_energy,energy)
        total_iters+=its[0]
        max_iters=max(max_iters,its[0])
        velocity=v
        year=start_year+step*dt
        if any(abs(year-k)<1e-8 for k in checkpoints):
            snapshots[int(round(year))]={
                "u":u.copy(),"v":velocity.copy(),
                "elastic_energy_normalized":float(u@(L@u))/(2*tau),
                "step_relative_balance":residual,
                "step_relative_energy_identity":energy,
            }
    return {
        "state":{"u":u,"v":velocity},
        "snapshots":snapshots,
        "linear_steps":steps,"total_cg_iterations":total_iters,
        "maximum_cg_iterations_per_step":max_iters,
        "maximum_relative_force_balance":max_residual,
        "maximum_relative_energy_identity":max_energy,
        "wall_seconds":time.perf_counter()-t0,
        "matrix_nnz":int(A.nnz),
        "matrix_csr_bytes":int(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes),
    }


def original_geometry_audit(mesh,views,source_parent_views,source_plate_views,displacements):
    """Source-faithful signed spherical area, not re-meshing or G4 transport."""
    from experiments.global_t0_kinematic_baseline_v1.benchmark import unit_xyz
    offset=0
    min_j=math.inf;max_j=-math.inf
    max_angular=0.;area_total_0=0.;area_total_1=0.
    for plate in PLATES:
        v=views[plate]
        ids0=np.asarray(v["ids"],dtype=int)
        count=len(ids0)
        require(np.array_equal(ids0,source_parent_views[offset:offset+count])
                and np.all(source_plate_views[offset:offset+count]==plate),
                "GLOBAL_TIME_SOURCE_VIEW_IDENTITY_MISMATCH")
        latlon=np.asarray(mesh.vertices_lat_lon)[ids0]
        xyz,unit,e,n=frames_and_cartesian(latlon)
        local_u=displacements[2*offset:2*(offset+count)].reshape(count,2)
        shifted=xyz+e*local_u[:,0,None]+n*local_u[:,1,None]
        new_unit=shifted/np.linalg.norm(shifted,axis=1)[:,None]
        area0=np.asarray(v["area0"])
        area1=spherical_area_sr(new_unit,np.asarray(v["triangles"]))
        require(bool(np.all(np.isfinite(area1))) and
                bool(np.all(area0>0)) and bool(np.all(area1>0)),
                "GLOBAL_TIME_TRIANGLE_OR_AREA_INVALID")
        jac=area1/area0
        min_j=min(min_j,float(np.min(jac)))
        max_j=max(max_j,float(np.max(jac)))
        area_total_0+=float(np.sum(area0))
        area_total_1+=float(np.sum(area1))
        max_angular=max(max_angular,float(np.max(
            np.arccos(np.clip(np.einsum("ij,ij->i",unit,new_unit),-1,1)))))
        offset+=count
    require(offset==len(source_parent_views),"GLOBAL_TIME_VIEW_COUNT_DRIFT")
    return {
        "minimum_signed_area_J":min_j,"maximum_signed_area_J":max_j,
        "maximum_absolute_area_ratio_minus_one":max(abs(min_j-1),abs(max_j-1)),
        "sum_signed_plate_local_area_ratio":area_total_1/area_total_0,
        "maximum_angular_material_shift_rad":max_angular,
        "no_triangle_inversions":True,
        "source_mesh_not_recomputed_or_moved":True,
        "no_G4_layer_mass_thermic_transport":True,
    }


def verify_static_prior(folder:Path,root:Path):
    manifest=json.loads((folder/"MANIFEST.json").read_text())
    report_path=folder/"REPORT.json"
    report=json.loads(report_path.read_text())
    require(manifest["schema"]=="ARCANA_R6_GLOBAL_SPARSE_P1_STATIC_MANIFEST_V1"
            and manifest["files"]["REPORT.json"]==sha256(report_path)
            and report["schema"]=="ARCANA_R6_GLOBAL_SOURCE_SPARSE_P1_STATIC_G2_V1"
            and report["status"]==
               "PASS_REGIONAL_DENSE_SPARSE_P1_PARITY_AND_12_PLATE_GLOBAL_STATIC_ENGINEERING__PHYSICS_OPEN"
            and report["global_static_manufactured_probe"]["cg_info"]==0
            and report["source_global_sparse_P1"]["EN_dofs"]==132870
            and report["physical_solver_runs"]==0
            and report["physical_T1"] is None
            and report["D_024"]=="ACTIVE",
            "GLOBAL_TIME_PRIOR_STATIC_FAIR_RECEIPT_INVALID")
    for path,checksum in report["source_files_sha256"].items():
        require(sha256(Path(path))==checksum,
                "GLOBAL_TIME_PRIOR_STATIC_SOURCE_PIN_CHANGED")
    require(report["source_files_sha256"][
            str(root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat")]==
            sha256(root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"),
            "GLOBAL_TIME_GLOBAL_PRE_PIN_MISMATCH")
    return sha256(folder/"MANIFEST.json"),report


def execute(static_dir:Path,out:Path,root:Path=ROOT):
    require(not out.exists(),"GLOBAL_TIME_OUTPUT_ALREADY_EXISTS")
    beginning=time.perf_counter()
    static_hash,static_report=verify_static_prior(static_dir,root)
    inputs_to_pin=[
        static_dir/"MANIFEST.json",static_dir/"REPORT.json",
        root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
        root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json",
    ]
    before={str(p):sha256(p) for p in inputs_to_pin}
    K,stats,fields=assemble_real_global_source(root)
    require(stats["EN_dofs"]==132870 and
            stats["source_triangles"]==TRIANGLES and
            stats["nnz"]==static_report["source_global_sparse_P1"]["nnz"],
            "GLOBAL_TIME_STATIC_K_PARITY_DRIFT")
    diagonal=K.diagonal()
    c=float(DASHPOT_TO_MEAN_TANGENT*np.mean(diagonal))
    require(c>0 and math.isfinite(c),"GLOBAL_TIME_DRAG_ZERO")
    L=K.copy()
    L.data/=c
    euler=fields["euler"]
    target=fields["manufactured_target"]
    euler_null=float(np.linalg.norm(L@euler)/
        max(float(np.max(L.diagonal()))*float(np.linalg.norm(euler)),1e-30))
    require(euler_null<1e-9,"GLOBAL_TIME_G1_RIGID_NULL_MODE_BROKEN")
    # Source frame is fixed and co-rotating in a plate-material sense;
    # DO NOT use Euler(t)-rotated physical geometry with T0 stiffness.
    t1=iterate_global(L,target,1.,1000,checkpoints=(100,500,1000))
    t5=iterate_global(L,target,5.,200,checkpoints=(100,500,1000))
    t10=iterate_global(L,target,10.,100,checkpoints=(100,500,1000))
    resumed=iterate_global(L,target,1.,500,initial=t1["snapshots"][500],
                           start_year=500,checkpoints=(1000,))
    restart_error=float(np.max(np.abs(
        resumed["state"]["u"]-t1["state"]["u"])))
    require(restart_error<1e-8,"GLOBAL_TIME_RESTART_DISPLACEMENT_FAILED")
    mesh,omegas,pins,horizon,pre=source_inputs(root)
    views=build_views(mesh)
    require(mesh.normalized_sha256==fields["source_mesh_sha256"] and
            len(views)==12 and horizon>1000,
            "GLOBAL_TIME_SOURCE_MESH_REOPEN_DRIFT")
    horizon_outputs={}
    for year in (100,1000):
        a=t1["snapshots"][year]
        reference=max(float(np.max(np.abs(a["u"]))),1.)
        err5=float(np.max(np.abs(t5["snapshots"][year]["u"]-a["u"])))
        err10=float(np.max(np.abs(t10["snapshots"][year]["u"]-a["u"])))
        require(err5<=err10+1e-8 and err10/reference<0.025,
                "GLOBAL_TIME_STEP_CONVERGENCE_FAILED")
        geometry=original_geometry_audit(
            mesh,views,fields["node_parent_zero_based"],
            fields["plate_id_per_view"],a["u"])
        require(geometry["maximum_absolute_area_ratio_minus_one"]<0.02,
                "GLOBAL_TIME_GEOMETRY_DRIFT_EXCEEDS_2_PERCENT")
        v=a["v"]
        displacement=a["u"]
        feedback=float(np.linalg.norm(v-target)/np.linalg.norm(target))
        need_velocity=float(np.sqrt(np.mean((v-target)**2)))
        horizon_outputs[str(year)]={
            "year":year,
            "max_nodal_material_displacement_m":float(np.max(
                np.linalg.norm(displacement.reshape(-1,2),axis=1))),
            "G1_plus_manufactured_target_RMS_m_per_year":float(
                np.sqrt(np.mean(target**2))),
            "coupled_RMS_m_per_year":float(np.sqrt(np.mean(v**2))),
            "coupled_minus_target_RMS_m_per_year":need_velocity,
            "relative_feedback_norm":feedback,
            "max_displacement_dt5_vs_dt1_m":err5,
            "max_displacement_dt10_vs_dt1_m":err10,
            "energy_normalized":a["elastic_energy_normalized"],
            "source_plate_area_diagnostic":geometry,
        }
    require(all(sha256(Path(p))==h for p,h in before.items()),
            "GLOBAL_TIME_INPUTS_CHANGED_DURING_TEST")
    report={
        "schema":SCHEMA,"status":STATUS,
        "experiment":"12_PLATE_GLOBAL_SOURCE_P1_FIXED_T0_TANGENT_MANUFACTURED_TIME",
        "global_source_mesh_sha256":fields["source_mesh_sha256"],
        "static_fair_manifest_sha256":static_hash,
        "source_input_sha256":before,
        "source_en_dofs":stats["EN_dofs"],
        "source_plate_local_material_views":stats["source_nodes"],
        "source_triangles":stats["source_triangles"],
        "time_steps_model_years":[1,5,10],
        "horizons_model_years":[100,1000],
        "G1_source_Euler_reference_frame":
            "PLATE_MATERIAL_SOURCE_T0_FIXED_FRAME__RIGID_NULL_EULER_VELOCITY",
        "G1_Euler_rigid_null_relative":euler_null,
        "G2_material":"ENGINEERING_ONLY_SYNTHETIC_H_THICKNESS_KELVIN_VOIGT",
        "G2_internal_tangent_static_T0":True,
        "G3_real_basal_outer_or_normal_forces":None,
        "contacts":"PLATE_LOCAL_VIEWS_UNWELDED_NO_SLIP_OPENING_LAW",
        "model_memory_tau_years":TAU_YEARS,
        "horizons":horizon_outputs,
        "dt1_diagnostics":{k:t1[k] for k in (
            "linear_steps","total_cg_iterations",
            "maximum_cg_iterations_per_step",
            "maximum_relative_force_balance",
            "maximum_relative_energy_identity",
            "wall_seconds","matrix_csr_bytes")},
        "dt5_diagnostics":{k:t5[k] for k in (
            "linear_steps","total_cg_iterations",
            "maximum_relative_force_balance","maximum_relative_energy_identity",
            "wall_seconds")},
        "dt10_diagnostics":{k:t10[k] for k in (
            "linear_steps","total_cg_iterations",
            "maximum_relative_force_balance","maximum_relative_energy_identity",
            "wall_seconds")},
        "restart_500_plus_500_max_displacement_error_m":restart_error,
        "restart_extra_steps":resumed["linear_steps"],
        "engineering_linear_step_count":sum(x["linear_steps"]
                for x in (t1,t5,t10,resumed)),
        "global_assembly_CSR_bytes":stats["one_csr_bytes"],
        "global_matrix_nnz":stats["nnz"],
        "total_wall_seconds":time.perf_counter()-beginning,
        "peak_process_memory":usage(),
        "fixed_initial_geometry_and_no_thermal_evolution":True,
        "no_plate_contact_dynamic_or_G4_material_transport":True,
        "no_world_history_changes":True,
        "physical_solver_runs":0,"physical_T1":None,
        "mechanical_solve_authorized":False,"D_024":"ACTIVE",
    }
    out.mkdir(parents=True,exist_ok=False)
    p=out/"REPORT.json"
    p.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_GLOBAL_MANUFACTURED_P1_TIME_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(p)},
        "static_source_manifest_sha256":static_hash,
        "no_physical_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True},indent=2)+"\n")
    return {
        "status":STATUS,
        "horizons":horizon_outputs,
        "dt1_iterations":t1["total_cg_iterations"],
        "dt5_iterations":t5["total_cg_iterations"],
        "restart_error_m":restart_error,
        "global_matrix_nnz":stats["nnz"],
        "total_wall_seconds":report["total_wall_seconds"],
        "physical_solver_runs":0,"physical_T1":None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--static",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(a.static,a.output,a.root),indent=2))


if __name__=="__main__":
    main()
