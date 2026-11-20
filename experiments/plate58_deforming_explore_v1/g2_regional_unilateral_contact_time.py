"""R6: source-exact regional manufactured unilateral contact time experiment.

A real active-set quadratic-program normal complementarity solve replaces the
earlier *finite penalty* approximation. Gaps are accumulated in the ORIGINAL
T0 contact-normal EN frame. This is NOT a moving-geometry/contact-normal
transport solver, not friction, not real G3 forces, not a physical T1.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.linalg import solve_triangular
from scipy.optimize import nnls
from scipy.sparse.linalg import splu

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT,source_inputs,sha256,usage,
)
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry,assemble_split_source,euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g1_g2_manufactured_feedback import (
    TAU_YEARS,DASHPOT_TO_MEAN_TANGENT,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    SparseP1Error,
)

STATUS="PASS_SOURCE_REGIONAL_UNILATERAL_COMPLEMENTARITY_TIME__MOVING_GEOMETRY_OPEN"
SCHEMA="ARCANA_R6_REGIONAL_SOURCE_UNILATERAL_CONTACT_TIME_V1"

def need(ok,code):
    if not ok:raise SparseP1Error(code)


def normal_constraint_matrix(contact_links,source_index,ndof):
    """One source-matched normal gap DOF per true plate-pair node link."""
    rows=[];cols=[];vals=[]
    for k,row in enumerate(contact_links):
        p,q=tuple(map(int,row["plate_pair"]))
        node=int(row["parent_node_id"])
        i,j=source_index[(p,node)],source_index[(q,node)]
        n=np.asarray(row["normal_EN"],dtype=float)
        need(i!=j and n.shape==(2,) and
             np.all(np.isfinite(n)) and abs(np.linalg.norm(n)-1)<1e-9,
             "UNILATERAL_SOURCE_CONTACT_NORMAL_INVALID")
        for c in range(2):
            rows.extend((k,k));cols.extend((2*i+c,2*j+c))
            vals.extend((-float(n[c]),float(n[c])))
    J=sparse.coo_matrix((vals,(rows,cols)),
          shape=(len(contact_links),ndof)).tocsr()
    need(J.shape[0]>0,"UNILATERAL_NO_ACTUAL_SOURCE_CONTACTS")
    return J


def prepare_qp(A,J):
    """Factor once per timestep size; Schur complement is tiny (<=39 links)."""
    A=sparse.csc_matrix(A)
    J=sparse.csr_matrix(J)
    need(A.shape[0]==A.shape[1]==J.shape[1] and J.shape[0]>0
         and np.all(np.isfinite(A.data)),"UNILATERAL_QP_PREPARE_INVALID")
    lu=splu(A)
    W=lu.solve(J.T.toarray())
    S=np.asarray(J@W)
    S=.5*(S+S.T)
    diag=np.diag(S)
    scale=max(float(np.max(np.abs(diag))),1e-30)
    eig=np.linalg.eigvalsh(S)
    need(float(np.min(eig))>1e-11*scale,
         "UNILATERAL_CONTACT_CONSTRAINTS_REDUNDANT_OR_DEPENDENT")
    return {"A":A,"J":J,"lu":lu,"W":W,"L":np.linalg.cholesky(S)}


def frictionless_normal_qp(A,b,J,lower,*,prepared=None,tol=1e-9):
    """Primal constrained quadratic response via exactly bounded dual NNLS.

    A v=b+J^T lam; w=Jv-lower>=0; lam>=0; lam*w=0.
    Multipliers are in the NORMALIZED manufactured force units.
    """
    prepared=prepare_qp(A,J) if prepared is None else prepared
    rhs=np.asarray(b,dtype=float)
    bound=np.asarray(lower,dtype=float)
    A=prepared["A"];J=prepared["J"]
    need(A.shape==(len(rhs),len(rhs)) and
         J.shape[1]==len(rhs) and J.shape[0]==len(bound)>0
         and np.all(np.isfinite(rhs)) and np.all(np.isfinite(bound))
         and math.isfinite(tol) and 0<tol<1e-5,
         "UNILATERAL_QP_INPUT_INVALID")
    v0=prepared["lu"].solve(rhs)
    W=prepared["W"]; L=prepared["L"]
    gap0=np.asarray(J@v0-bound).ravel()
    target=-solve_triangular(L,gap0,lower=True)
    lam,residual_nnls=nnls(L.T,target,maxiter=50*len(bound))
    v=v0+W@lam
    w=np.asarray(J@v-bound).ravel()
    force_resid=np.linalg.norm(A@v-rhs-J.T@lam)/max(
        np.linalg.norm(rhs)+np.linalg.norm(J.T@lam),1e-20)
    minlam=float(np.min(lam))
    comp=float(np.max(np.abs(lam*w))) if len(lam) else 0.
    scaled_comp=comp/max(1.,float(np.max(np.abs(lam)))*max(1.,float(np.max(np.abs(w)))))
    need(force_resid<tol and float(np.min(w))>=-tol
         and minlam>=-tol and scaled_comp<tol,
         "UNILATERAL_QP_KKT_FAILED")
    return {
      "velocity":v,"lambda":lam,"constraint_slack":w,
      "force_relative_residual":float(force_resid),
      "minimum_gap_rate_slack":float(np.min(w)),
      "minimum_contact_reaction":float(minlam),
      "max_scaled_complementarity":scaled_comp,
      "active_contact_count":int(np.count_nonzero(lam>tol*max(1.,np.max(lam)))),
      "max_contact_reaction":float(np.max(lam)),
      "dual_nnls_residual":float(residual_nnls),
    }


def min_gap_safe(x):
    return float(np.min(x))


def integrate(K,J,drive,dt,steps,*,initial=None,start_year=0,
              checkpoints=(100,500,1000),tau=TAU_YEARS):
    """Implicit Kelvin–Voigt in fixed plate-material EN frame.

    gap is updated from dt * Jv, not a measured 3D surface separation.
    """
    dt=float(dt);tau=float(tau)
    K=sparse.csr_matrix(K)
    g=np.asarray(drive,dtype=float)
    need(dt>0 and math.isfinite(dt) and
         int(steps)==steps and steps>0 and tau>0
         and K.shape==(len(g),len(g)) and
         J.shape[1]==len(g),"UNILATERAL_TIME_INPUT_INVALID")
    c=DASHPOT_TO_MEAN_TANGENT*float(np.mean(K.diagonal()))
    need(c>0,"UNILATERAL_DRAG_INVALID")
    # Use a dimensionless manufactured force scale, avoiding the
    # 1e25-1e27 stiffness range in the LCP Schur solver.
    L=K*(1./c)
    A=(sparse.eye(len(g),format="csr")+
       L*(1.+dt/tau)).tocsc()
    prepared=prepare_qp(A,J)
    if initial is None:
        displacement=np.zeros_like(g)
        gap=np.zeros(J.shape[0],dtype=float)
    else:
        displacement=np.asarray(initial["displacement"],dtype=float).copy()
        gap=np.asarray(initial["gap"],dtype=float).copy()
    need(displacement.shape==g.shape and gap.shape==(J.shape[0],)
         and np.all(np.isfinite(displacement)) and
         np.all(np.isfinite(gap)) and np.min(gap)>=-1e-9,
         "UNILATERAL_RESTART_INVALID")
    checkpoints=set(map(int,checkpoints))
    snapshots={}; max_complementarity=0.;min_gap=math.inf
    max_force=0.;max_work=0.;max_reaction=0;activations=0
    previous_active=np.zeros(len(gap),dtype=bool)
    for k in range(1,int(steps)+1):
        rhs=g-L@displacement/tau
        qp=frictionless_normal_qp(A,rhs,J,-gap/dt,prepared=prepared)
        v=qp["velocity"];lam=qp["lambda"]
        next_disp=displacement+dt*v
        next_gap=gap+dt*(J@v)
        min_gap=min(min_gap,float(np.min(next_gap)))
        # Discrete exact complementarity at end of step.
        gap_scale=max(1.,float(np.max(np.abs(next_gap))))
        reaction_scale=max(1.,float(np.max(lam)))
        end_comp=float(np.max(np.abs(next_gap*lam))/(gap_scale*reaction_scale))
        max_complementarity=max(max_complementarity,end_comp)
        max_reaction=max(max_reaction,float(np.max(lam)))
        max_force=max(max_force,qp["force_relative_residual"])
        # Constraint does non-negative work on updated gap-rate with
        # consistently signed normal reaction; do not call this
        # geological energy or exact Signorini under moving geometry.
        reaction_velocity=float(lam@(J@v))
        reaction_gap_change=float(lam@(next_gap-gap))
        work_error=abs(reaction_gap_change-dt*reaction_velocity)/max(
            1.,abs(reaction_gap_change),abs(dt*reaction_velocity))
        max_work=max(max_work,work_error)
        active=lam>1e-9*reaction_scale
        activations+=int(np.count_nonzero(active & ~previous_active))
        previous_active=active
        need(float(np.min(next_gap))>=-1e-8 and
             end_comp<1e-8 and work_error<1e-8,
             "UNILATERAL_DYNAMIC_GAP_COMPLEMENTARITY_FAILED")
        displacement=next_disp;gap=next_gap
        year=start_year+dt*k
        if any(abs(year-y)<1e-8 for y in checkpoints):
            snapshots[int(round(year))]={
               "displacement":displacement.copy(),"gap":gap.copy(),
               "velocity":v.copy(),"lambda":lam.copy(),
               "active_count":int(np.count_nonzero(active)),
               "minimum_gap":float(np.min(gap)),
               "maximum_gap":float(np.max(gap)),
               "maximum_relative_normal_rate":float(np.max(J@v)),
               "minimum_relative_normal_rate":float(np.min(J@v)),
            }
    return {
     "state":{"displacement":displacement,"gap":gap},
     "snapshots":snapshots,
     "max_force_residual":max_force,
     "min_gap_over_run":min_gap,
     "max_scaled_complementarity":max_complementarity,
     "max_discrete_reaction_work_identity":max_work,
     "max_reaction":max_reaction,
     "new_contact_activations":activations,
     "linearized_source_normals_not_updated":True,
     "steps":int(steps),
    }


def verify_and_run(multiscale:Path,nodal:Path,prior:Path,out:Path,root:Path=ROOT):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
       parse_regional_pre,validate_column_for_potential)
    need(not out.exists(),"UNILATERAL_OUTPUT_EXISTS")
    import time
    wall_start=time.perf_counter()
    prior_manifest=json.loads((prior/"MANIFEST.json").read_text())
    prior_report=json.loads((prior/"REPORT.json").read_text())
    need(prior_manifest["schema"]=="ARCANA_R6_SOURCE_CONTACT_OBJECTIVITY_MANIFEST_V1"
         and prior_manifest["files"]["REPORT.json"]==sha256(prior/"REPORT.json")
         and prior_report["status"]==
          "PASS_SOURCE_REGIONAL_CONTACT_POLICY_AND_FINITE_ROTATION_OBJECTIVITY__PHYSICS_OPEN"
         and prior_report["physical_T1"] is None,
         "UNILATERAL_PRIOR_SOURCE_CONTACT_RECEIPT_INVALID")
    mm=json.loads((multiscale/"MANIFEST.json").read_text())
    parent=json.loads((multiscale/"CONTINUATION_A.json").read_text())
    nm=json.loads((nodal/"MANIFEST.json").read_text())
    nb=json.loads((nodal/"SOURCE_NODAL_ELEMENT_G2.json").read_text())
    need(mm["files"]["CONTINUATION_A.json"]==
         sha256(multiscale/"CONTINUATION_A.json") and
         nm["files"]["SOURCE_NODAL_ELEMENT_G2.json"]==
         sha256(nodal/"SOURCE_NODAL_ELEMENT_G2.json") and
         nb["source_multiscale_manifest_sha256"]==
         sha256(multiscale/"MANIFEST.json"),
         "UNILATERAL_SOURCE_MANIFEST_INVALID")
    mesh,omegas,pins,horizon,metadata=source_inputs(root)
    source_paths=[prior/"MANIFEST.json",prior/"REPORT.json",
                  multiscale/"MANIFEST.json",multiscale/"CONTINUATION_A.json",
                  nodal/"MANIFEST.json",nodal/"SOURCE_NODAL_ELEMENT_G2.json",
                  root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
                  root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json"]
    hashes={str(p):sha256(p) for p in source_paths}
    reg={int(x["cell_extent_per_side"]):x
         for x in parent["topological_comparative_extents"]}
    nod={int(x["extent_cells"]):x for x in nb["scales"]}
    need(set(reg)==set(nod)=={8,16},"UNILATERAL_SCALE_CHANGED")
    outcomes=[]
    for width in (8,16):
        src=reg[width]
        ids=list(map(int,src["parent_node_ids"]))
        fegpath=multiscale/f"OUTER_A_{width:02d}x{width:02d}.feg"
        prepath=multiscale/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
        need(sha256(fegpath)==src["output_FEG_sha256"]
             and sha256(prepath)==src["output_PRE_sha256"],
             "UNILATERAL_FEG_PRE_SOURCE_SHA_MISMATCH")
        feg=parse_feg(fegpath.read_text(),mode="SHELLS_READY")
        pre=parse_regional_pre(prepath,src["PRE_source_field_order"],ids)
        need({str(k):v for k,v in pre.items()}==
             {str(k):v for k,v in nod[width]["source_PRE_by_parent_node"].items()},
             "UNILATERAL_PRE_NODE_BINDING_DRIFT")
        for item in pre.values():validate_column_for_potential(item)
        ll={ids[i]:(float(v.latitude_deg),float(v.longitude_deg))
            for i,v in enumerate(feg.nodes)}
        faces=[tuple(ids[int(n)-1] for n in e.node_ids) for e in feg.elements]
        plates=list(map(int,src["parent_triangle_plate_ids"]))
        from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
             contact_registry,assemble_split_source,euler_source_en)
        edges=contact_registry(ids,faces,plates,ll,src["source_contact_edges"])
        K,index,coords,pv,stats=assemble_split_source(ids,faces,plates,ll,pre)
        links=edges["contacts"]
        J=normal_constraint_matrix(links,index,K.shape[0])
        g=euler_source_en(coords,pv,omegas)
        # Check true Euler-closing links before constraints.
        initial_rates=np.asarray(J@g).ravel()
        closing=int(np.count_nonzero(initial_rates < -1e-12))
        need(closing==(0 if width==8 else 4),
             "UNILATERAL_REAL_SOURCE_CLOSING_INVENTORY_CHANGED")
        boundaries={
          (tuple(sorted(map(int,row["plate_pair"]))),
           int(node)):[] for row in src["source_contact_edges"]
          for node in row["source_edge_node_ids"]}
        for row in src["source_contact_edges"]:
            keypair=tuple(sorted(map(int,row["plate_pair"])))
            for node in row["source_edge_node_ids"]:
                boundaries[(keypair,int(node))].append(row["source_boundary_id"])

        one=integrate(K,J,g,1.,1000,checkpoints=(100,500,1000))
        five=integrate(K,J,g,5.,200,checkpoints=(100,500,1000))
        ten=integrate(K,J,g,10.,100,checkpoints=(100,500,1000))
        part=integrate(K,J,g,1.,500,
            initial={
                "displacement":one["snapshots"][500]["displacement"],
                "gap":one["snapshots"][500]["gap"]},
            start_year=500,checkpoints=(1000,))
        restart=float(np.max(np.abs(part["state"]["displacement"]-
                                     one["state"]["displacement"])))
        need(restart<1e-8,"UNILATERAL_RESTART_DIVERGENCE")
        snapshots={}
        for year in (100,1000):
            base=one["snapshots"][year]
            err5=float(np.max(np.abs(
               five["snapshots"][year]["displacement"]-base["displacement"])))
            err10=float(np.max(np.abs(
               ten["snapshots"][year]["displacement"]-base["displacement"])))
            need(err5<=err10+1e-7,
                 "UNILATERAL_TIMESTEP_ORDER_FAILED")
            snapshots[str(year)]={
              "max_source_tangent_displacement_m":float(np.max(
                  np.linalg.norm(base["displacement"].reshape(-1,2),axis=1))),
              "min_normal_contact_gap_m":base["minimum_gap"],
              "max_normal_contact_gap_m":base["maximum_gap"],
              "active_contact_links":base["active_count"],
              "negative_normal_rate_links":int(np.count_nonzero(
                   J@base["velocity"] < -1e-9)),
              "max_abs_displacement_dt5_minus_dt1_m":err5,
              "max_abs_displacement_dt10_minus_dt1_m":err10,
            }
        outcomes.append({
           "extent":width,"real_source_nodes":len(ids),
           "real_source_plate_ids":sorted(set(plates)),
           "source_contact_edges":len(edges["edges"]),
           "source_contact_pair_links":len(links),
           "source_triple_junction_ids":edges["triple_junction_parent_ids"],
           "source_plate_local_views":len(pv),
           "source_mechanical_dofs":K.shape[0],
           "Euler_initial_closing_link_count":closing,
           "source_contact_metadata":[{
              "plate_pair":list(x["plate_pair"]),
              "parent_node_id":x["parent_node_id"],
              "source_segments":x["source_segments"],
              "source_boundary_ids":sorted(set(
                  boundaries[(tuple(x["plate_pair"]),int(x["parent_node_id"]))])),
              "initial_normal_rate_m_per_year":float(initial_rates[i])}
              for i,x in enumerate(links)],
           "horizons":snapshots,
           "dt1_max_force_residual":one["max_force_residual"],
           "dt1_max_scaled_complementarity":one["max_scaled_complementarity"],
           "dt1_min_normal_gap_m":one["min_gap_over_run"],
           "dt1_max_reaction":one["max_reaction"],
           "restart_500_plus_500_m":restart,
           "contact_normal_frame":"FIXED_SOURCE_T0_EN_NOT_OBJECTIVE_MOVING_GEOMETRY",
           "source_G2_P1_tangent":"FIXED_T0_MANUFACTURED_K",
        })
    need(all(sha256(Path(p))==sha for p,sha in hashes.items()),
         "UNILATERAL_SOURCE_MODIFIED_DURING_TEST")
    report={
      "schema":SCHEMA,"status":STATUS,
      "scales":outcomes,"source_sha256":hashes,
      "prior_source_contact_manifest_sha256":sha256(prior/"MANIFEST.json"),
      "model_horizons_years":[100,1000],
      "model_step_years":[1,5,10],
      "contact_rule":"LINEAR_T0_SOURCE_NORMAL_SIGNORINI_VELOCITY_DISPLACEMENT_COMPLEMENTARITY",
      "normal_gap_is_source_frame_integral_not_current_3D_separation":True,
      "normal_and_tangent_transport_under_3D_deformation":None,
      "real_G3_contact_traction":None,"real_G2_rock_law":None,
      "G4_layer_transport":None,"physical_solver_runs":0,
      "physical_T1":None,"D_024":"ACTIVE",
      "total_wall_seconds":time.perf_counter()-wall_start,
      "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    p=out/"REPORT.json"
    p.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
      "schema":"ARCANA_R6_REGIONAL_UNILATERAL_MANIFEST_V1",
      "status":STATUS,"files":{"REPORT.json":sha256(p)},
      "no_physical_solver_run":True,"physical_T1":None},indent=2)+"\n")
    return {"status":STATUS,"scales":outcomes,
            "physical_solver_runs":0,"physical_T1":None}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multiscale",type=Path,required=True)
    ap.add_argument("--nodal",type=Path,required=True)
    ap.add_argument("--prior-contact",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--root",type=Path,default=ROOT)
    a=ap.parse_args()
    result=verify_and_run(a.multiscale,a.nodal,a.prior_contact,a.output,a.root)
    compact=[{k:v for k,v in r.items() if k!="source_contact_metadata"}
             for r in result["scales"]]
    print(json.dumps({**result,"scales":compact},indent=2,allow_nan=False))


if __name__=="__main__":
    main()
