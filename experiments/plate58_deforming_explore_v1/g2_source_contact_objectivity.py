"""R6 source-keyed regional interface policies + finite-rotation objectivity.

AUTHORITY: genuine source_contact_edges and plate-parent triangle owners,
not guessed shared-node plate combinations. Three STATIC manufactured policies:
UNWELDED, PENALTY_WELDED, NORMAL_ONLY_CLOSING_VELOCITY.
No Signorini mechanics, real fault friction, G3 loads, geology or physical T1.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import cg
from scipy.spatial.transform import Rotation

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, sha256, source_inputs, rotate_xyz, usage,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    sparse_p1_tangent, local_law_from_pre, SparseP1Error,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,spherical_element_tangent,
)
from experiments.plate58_deforming_explore_v1.g1_g2_manufactured_feedback import (
    DASHPOT_TO_MEAN_TANGENT,
)

STATUS="PASS_SOURCE_REGIONAL_CONTACT_POLICY_AND_FINITE_ROTATION_OBJECTIVITY__PHYSICS_OPEN"
SCHEMA="ARCANA_R6_SOURCE_CONTACT_OBJECTIVITY_ENGINEERING_V1"
POLICIES=("UNWELDED","PENALTY_WELDED","CLOSING_NORMAL_ONLY")
CONTACT_PENALTY_RATIO=30.0


def need(ok,tag):
    if not ok:
        raise SparseP1Error(tag)


def _edges(nodes):
    a,b,c=map(int,nodes)
    need(len({a,b,c})==3,"CONTACT_DEGENERATE_SOURCE_TRIANGLE")
    return (tuple(sorted((a,b))),tuple(sorted((b,c))),
            tuple(sorted((c,a))))


def contact_registry(parent_nodes,faces,face_plates,latlon,source_contacts):
    """Exact edge incidence and plate/node ownership; no implicit welding."""
    ids=list(map(int,parent_nodes))
    tri=[tuple(map(int,f)) for f in faces]
    owners=list(map(int,face_plates))
    need(len(ids)==len(set(ids)) and len(tri)==len(owners)>0 and
         set(n for t in tri for n in t)==set(ids) and
         set(latlon)==set(ids),"CONTACT_SOURCE_INVENTORY_INVALID")
    incidence=defaultdict(list)
    node_owners=defaultdict(set)
    for face,plate in zip(tri,owners,strict=True):
        for n in face:node_owners[n].add(plate)
        for edge in _edges(face):incidence[edge].append((plate,face))
    need(all(1<=len(rows)<=2 for rows in incidence.values()),
         "CONTACT_NONMANIFOLD_SOURCE_EDGE")
    actual={}
    for edge,rows in incidence.items():
        if len(rows)==2 and rows[0][0]!=rows[1][0]:
            pair=tuple(sorted((rows[0][0],rows[1][0])))
            actual[edge]=pair
    expected={}
    for row in source_contacts:
        edge=tuple(sorted(map(int,row["source_edge_node_ids"])))
        pair=tuple(sorted(map(int,row["plate_pair"])))
        bid=row["source_boundary_id"]
        need(edge not in expected and isinstance(bid,str) and
             bid.startswith("R6BND-T0-"),"CONTACT_SOURCE_BOUNDARY_ID_INVALID")
        expected[edge]=pair
    need(actual==expected,"CONTACT_SOURCE_EDGE_PLATE_PAIR_MISMATCH")
    # Normals are defined in the single source EN frame of a source vertex.
    # For pair (p,q), the positive normal points from p's triangle centroid
    # toward q's triangle centroid. Multiple segments are averaged per pair.
    normals=defaultdict(list)
    for edge,pair in sorted(actual.items()):
        a,b=edge
        rows=incidence[edge]
        centroids={p:np.mean(
            frames_and_cartesian([latlon[n] for n in face])[0],axis=0)
            for p,face in rows}
        direction=centroids[pair[1]]-centroids[pair[0]]
        for node in edge:
            xyz,unit,e,n=frames_and_cartesian([latlon[node]])
            en=np.array([float(direction@e[0]),float(direction@n[0])])
            length=float(np.linalg.norm(en))
            need(length>0 and math.isfinite(length),
                 "CONTACT_SOURCE_NORMAL_DEGENERATE")
            normals[(pair,node)].append(en/length)
    contacts=[]
    for (pair,node),vectors in sorted(normals.items()):
        summed=np.sum(vectors,axis=0)
        size=float(np.linalg.norm(summed))
        need(size>1e-8,"CONTACT_JUNCTION_NORMAL_AMBIGUOUS")
        normal=summed/size
        contacts.append({"parent_node_id":node,"plate_pair":pair,
                         "normal_EN":normal,
                         "source_segments":len(vectors)})
    need(contacts and sum(len(v) for v in normals.values())==
         2*len(actual),"CONTACT_SOURCE_EDGE_INCIDENCE_BROKEN")
    return {
        "edges":actual,
        "owner_by_parent_node":{n:tuple(sorted(ps))
                                for n,ps in node_owners.items()},
        "contacts":contacts,
        "contact_pair_count":len({v for v in actual.values()}),
        "contact_parent_node_count":len({x["parent_node_id"]
                                        for x in contacts}),
        "triple_junction_parent_ids":[int(n) for n,p in sorted(node_owners.items())
                                      if len(p)>=3],
    }


def assemble_split_source(parent_nodes,faces,face_plates,latlon,pre):
    """Rebuild exactly P1 6x6 from same original source per-plate triangles."""
    grouped=defaultdict(list)
    for i,p in enumerate(face_plates):grouped[int(p)].append(i)
    index={};ll=[];tri=[];eta=[];bulk=[];node_plate=[]
    for p,idx in sorted(grouped.items()):
        localids=sorted({n for i in idx for n in faces[i]})
        mapping={}
        for n in localids:
            mapping[n]=len(ll)
            index[(p,n)]=len(ll)
            ll.append(latlon[n]);node_plate.append(p)
        for i in idx:
            face=tuple(faces[i])
            tri.append([mapping[n] for n in face])
            e=1e20*np.mean([pre[n]["crust_thickness_m"] for n in face])+\
              1e21*np.mean([pre[n]["mantle_lithosphere_thickness_m"] for n in face])
            need(math.isfinite(e) and e>0,"CONTACT_SOURCE_PRE_INVALID")
            eta.append(e);bulk.append(e)
    ll=np.asarray(ll,dtype=float);tri=np.asarray(tri,dtype=np.int32)
    K,stats=sparse_p1_tangent(ll,tri,eta,bulk)
    need(stats["source_triangles"]==len(faces) and
         len(set(node_plate))==len(grouped),
         "CONTACT_P1_SOURCE_VIEW_MISMATCH")
    return K,index,ll,np.asarray(node_plate,dtype=np.int16),stats


def euler_source_en(latlon,plate_by_view,omegas):
    """One velocity for every plate-local source material view."""
    xyz,radial,e,n=frames_and_cartesian(latlon)
    vv=np.empty((len(latlon),2),dtype=float)
    for p in sorted(set(plate_by_view)):
        rows=np.flatnonzero(plate_by_view==p)
        omega=np.asarray(omegas[int(p)],dtype=float)
        need(omega.shape==(3,) and np.all(np.isfinite(omega)),
             "CONTACT_EULER_SOURCE_INVALID")
        cart=np.cross(omega,xyz[rows])
        vv[rows,0]=np.einsum("ij,ij->i",cart,e[rows])
        vv[rows,1]=np.einsum("ij,ij->i",cart,n[rows])
    return vv.reshape(-1)


def active_contacts(contacts,index,unconstrained_velocity):
    """Manufactured unilateral *closing-velocity* selector only.

    No physical gap/complementarity law. Opening is deliberately free;
    tangential slip is always free. Active set is frozen from Euler target,
    not reselected from the solved state.
    """
    velocity=np.asarray(unconstrained_velocity,dtype=float)
    out=[]
    for entry in contacts:
        p,q=entry["plate_pair"];node=entry["parent_node_id"]
        i,j=index[(p,node)],index[(q,node)]
        n=np.asarray(entry["normal_EN"],dtype=float)
        rel=velocity[2*j:2*j+2]-velocity[2*i:2*i+2]
        closing=float(n@rel)<0
        out.append({**entry,"view_i":i,"view_j":j,
                    "Euler_relative_normal_velocity_m_per_year":float(n@rel),
                    "closing_under_Euler_target":bool(closing)})
    return out


def penalty_matrix(ndof,contacts,policy,weight):
    """Velocity penalties: J^T W J. Spring dimensions follow synthetic K."""
    need(policy in POLICIES and math.isfinite(weight) and weight>0,
         "CONTACT_SYNTHETIC_POLICY_INVALID")
    rows=[];cols=[];values=[];active=0
    for row in contacts:
        if policy=="UNWELDED":continue
        if policy=="CLOSING_NORMAL_ONLY" and not row["closing_under_Euler_target"]:
            continue
        dirs=[np.array([1.,0.]),np.array([0.,1.])] if policy=="PENALTY_WELDED" else [
            np.asarray(row["normal_EN"],dtype=float)]
        i,j=row["view_i"],row["view_j"]
        need(i!=j and 2*max(i,j)+1<ndof,"CONTACT_PAIR_DOF_INVALID")
        for d in dirs:
            idx=np.array([2*i,2*i+1,2*j,2*j+1],dtype=int)
            coeff=np.r_[-d,d]
            matrix=weight*np.outer(coeff,coeff)
            for a in range(4):
                for b in range(4):
                    rows.append(int(idx[a]));cols.append(int(idx[b]))
                    values.append(float(matrix[a,b]))
        active+=1
    H=sparse.coo_matrix((values,(rows,cols)),shape=(ndof,ndof)).tocsr()
    H.sum_duplicates()
    return H,active


def solve_contact_policy(K,reference,contacts,policy,c,weight):
    """(cI+K+H)v=c*g; H constructed symmetric-positive semidefinite."""
    g=np.asarray(reference,dtype=float)
    need(K.shape==(len(g),len(g)) and c>0 and
         math.isfinite(c),"CONTACT_STATIC_INPUT_INVALID")
    H,active=penalty_matrix(len(g),contacts,policy,weight)
    A=(K+H+sparse.eye(len(g),format="csr")*c).tocsr()
    d=A.diagonal()
    need(bool(np.all(d>0)),"CONTACT_STATIC_JACOBI_INVALID")
    rhs=c*g
    from scipy.sparse.linalg import LinearOperator
    inv=1/d
    M=LinearOperator(A.shape,matvec=lambda x:inv*x,dtype=float)
    count=[0]
    def callback(_):count[0]+=1
    v,info=cg(A,rhs,rtol=1e-10,atol=0.,M=M,maxiter=2500,callback=callback)
    residual=float(np.linalg.norm(A@v-rhs)/max(np.linalg.norm(rhs),1e-30))
    work_in=float(rhs@v)
    work_drag=float(c*(v@v))
    work_internal=float(v@(K@v))
    work_contact=float(v@(H@v))
    work_error=abs(work_in-work_drag-work_internal-work_contact)/max(
        abs(work_in),1e-30)
    need(info==0 and residual<2e-9 and work_error<2e-9,
         "CONTACT_STATIC_FORCE_OR_WORK_FAILED")
    differences=[]
    for row in contacts:
        i,j=row["view_i"],row["view_j"]
        diff=v[2*j:2*j+2]-v[2*i:2*i+2]
        n=row["normal_EN"]
        differences.append((float(np.linalg.norm(diff)),float(n@diff),
                            float(n[0]*diff[1]-n[1]*diff[0])))
    rel=np.array(differences,dtype=float)
    need(np.all(np.isfinite(rel)),"CONTACT_STATIC_NONFINITE_RELATIVE_MOTION")
    return {
        "policy":policy,"active_penalty_contacts":active,
        "total_source_contact_links":len(contacts),
        "cg_iterations":count[0],
        "relative_force_balance":residual,
        "relative_virtual_work_identity":work_error,
        "synthetic_drag_work":work_drag,
        "synthetic_P1_internal_work":work_internal,
        "synthetic_contact_work":work_contact,
        "max_relative_contact_velocity_m_per_year":float(np.max(rel[:,0])),
        "max_absolute_normal_velocity_m_per_year":float(np.max(np.abs(rel[:,1]))),
        "max_absolute_tangential_velocity_m_per_year":float(np.max(np.abs(rel[:,2]))),
        "closing_relative_velocity_count_after_solve":
            int(np.count_nonzero(rel[:,1]<0)),
        "relative_velocity_to_G1_norm":float(np.linalg.norm(v-g)/
                                            max(np.linalg.norm(g),1e-30)),
        "velocity_vector":v,
    }


def finite_rotation_objectivity(latlon,eta_h,lambda_h,rotmat):
    """K'_EN = T K_EN T^T for physically rotated xyz and tangent frames.

    This compares the exact *existing faceted P1 kernel* before and after
    finite SO(3) rotation; not full geometric stiffness update in time.
    """
    ll=np.asarray(latlon,dtype=float)
    Q=np.asarray(rotmat,dtype=float)
    need(ll.shape==(3,2) and Q.shape==(3,3) and
         np.all(np.isfinite(ll)) and np.all(np.isfinite(Q)) and
         np.linalg.norm(Q.T@Q-np.eye(3))<1e-11 and
         np.linalg.det(Q)>0,"CONTACT_OBJECTIVE_ROTATION_INVALID")
    K,_=spherical_element_tangent(ll,eta_h,lambda_h)
    xyz,unit,e,n=frames_and_cartesian(ll)
    new_xyz=xyz@Q.T
    new_unit=new_xyz/np.linalg.norm(new_xyz,axis=1)[:,None]
    moved_ll=np.column_stack((
        np.rad2deg(np.arcsin(np.clip(new_unit[:,2],-1,1))),
        np.rad2deg(np.arctan2(new_unit[:,1],new_unit[:,0]))
    ))
    Kr,_=spherical_element_tangent(moved_ll,eta_h,lambda_h)
    _,_,er,nr=frames_and_cartesian(moved_ll)
    T=np.zeros((6,6))
    for i in range(3):
        old=np.column_stack((e[i],n[i]))
        new=np.column_stack((er[i],nr[i]))
        T[2*i:2*i+2,2*i:2*i+2]=new.T@Q@old
    transformed=T@K@T.T
    error=float(np.linalg.norm(Kr-transformed)/max(np.linalg.norm(K),1e-30))
    need(error<3e-9,"CONTACT_OBJECTIVE_FINITE_ROTATION_PARITY_FAILED")
    return error


def run(multiscale:Path,nodal:Path,out:Path,root:Path=ROOT):
    """Read-only sealed regions. All solves are static synthetic velocities."""
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential)
    need(not out.exists(),"CONTACT_OUTPUT_EXISTS")
    mm=json.loads((multiscale/"MANIFEST.json").read_text())
    parent=json.loads((multiscale/"CONTINUATION_A.json").read_text())
    nm=json.loads((nodal/"MANIFEST.json").read_text())
    nb=json.loads((nodal/"SOURCE_NODAL_ELEMENT_G2.json").read_text())
    need(mm["files"]["CONTINUATION_A.json"]==
         sha256(multiscale/"CONTINUATION_A.json") and
         nm["files"]["SOURCE_NODAL_ELEMENT_G2.json"]==
         sha256(nodal/"SOURCE_NODAL_ELEMENT_G2.json") and
         nb["source_multiscale_manifest_sha256"]==
         sha256(multiscale/"MANIFEST.json") and
         parent["mechanical_solve_authorized"] is False,
         "CONTACT_SOURCE_REGIONAL_MANIFEST_INVALID")
    mesh,omegas,pins,horizon,metadata=source_inputs(root)
    need(horizon>1000,"CONTACT_FIRST_EVENT_1000Y_INVALID")
    regimes={int(r["cell_extent_per_side"]):r
             for r in parent["topological_comparative_extents"]}
    regional={int(s["extent_cells"]):s for s in nb["scales"]}
    need(set(regimes)==set(regional)=={8,16},
         "CONTACT_AUTHORIZED_REGION_SCALES_CHANGED")
    source_paths=[multiscale/"MANIFEST.json",multiscale/"CONTINUATION_A.json",
                  nodal/"MANIFEST.json",nodal/"SOURCE_NODAL_ELEMENT_G2.json",
                  root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
                  root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json"]
    pinned={str(path):sha256(path) for path in source_paths}
    results=[]
    for width in (8,16):
        entry=regimes[width];ids=list(map(int,entry["parent_node_ids"]))
        fegfile=multiscale/f"OUTER_A_{width:02d}x{width:02d}.feg"
        prefile=multiscale/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
        need(sha256(fegfile)==entry["output_FEG_sha256"] and
             sha256(prefile)==entry["output_PRE_sha256"],
             "CONTACT_SOURCE_FEG_PRE_PIN_CHANGED")
        feg=parse_feg(fegfile.read_text(),mode="SHELLS_READY")
        pre=parse_regional_pre(prefile,entry["PRE_source_field_order"],ids)
        need({str(k):v for k,v in pre.items()}==
             {str(k):v for k,v in regional[width]["source_PRE_by_parent_node"].items()},
             "CONTACT_SOURCE_NODAL_BINDING_MISMATCH")
        for p in pre.values():validate_column_for_potential(p)
        ll={ids[i]:(float(v.latitude_deg),float(v.longitude_deg))
            for i,v in enumerate(feg.nodes)}
        faces=[tuple(ids[int(n)-1] for n in el.node_ids) for el in feg.elements]
        plates=list(map(int,entry["parent_triangle_plate_ids"]))
        require_ct=contact_registry(ids,faces,plates,ll,entry["source_contact_edges"])
        need(len(require_ct["edges"])==entry["source_contact_count"],
             "CONTACT_SOURCE_BOUNDARY_COUNT_DRIFT")
        need((width==8 and set(plates)=={5,8}) or
             (width==16 and set(plates)=={5,8,11} and
              34587 in require_ct["triple_junction_parent_ids"]),
             "CONTACT_SOURCE_REGIONAL_PLATE_OR_TRIPLE_INVENTORY_CHANGED")
        K,index,loc,plate_views,stats=assemble_split_source(ids,faces,plates,ll,pre)
        g=euler_source_en(loc,plate_views,omegas)
        pairs=active_contacts(require_ct["contacts"],index,g)
        c=DASHPOT_TO_MEAN_TANGENT*float(np.mean(K.diagonal()))
        need(c>0 and math.isfinite(c),"CONTACT_SOURCE_DRAG_INVALID")
        response={}
        raw={}
        for name in POLICIES:
            result=solve_contact_policy(K,g,pairs,name,c,CONTACT_PENALTY_RATIO*c)
            raw[name]=result
            response[name]={k:v for k,v in result.items()
                            if k!="velocity_vector"}
        # Require the manufactured welded policy actually modifies the
        # Euler-driven source response; do not report a decorative PASS.
        delta=float(np.linalg.norm(
            raw["PENALTY_WELDED"]["velocity_vector"]-
            raw["UNWELDED"]["velocity_vector"]))
        need(delta>1e-10 and
             response["PENALTY_WELDED"]["synthetic_contact_work"]>0,
             "CONTACT_WELDED_POLICY_NO_EFFECT")
        need(response["UNWELDED"]["active_penalty_contacts"]==0 and
             response["PENALTY_WELDED"]["active_penalty_contacts"]==len(pairs),
             "CONTACT_POLICY_INVENTORY_INVALID")
        # Test geometric *input* objectivity on every sampled source contact
        # element at both real 100/1000yr Euler angle and synthetic finite SO(3).
        contact_parent_nodes={n for x in pairs for n in [x["parent_node_id"]]}
        test_faces=[(plate,face) for plate,face in zip(plates,faces)
                    if any(n in contact_parent_nodes for n in face)]
        need(test_faces,"CONTACT_NO_SOURCE_FACES_NEAR_CONTACT")
        sampled=test_faces[:min(6,len(test_faces))]
        large=Rotation.from_rotvec(np.array([.6,-.35,.24])).as_matrix()
        worst=0.;counts=0
        for plate,face in sampled:
            locs=[ll[n] for n in face]
            e=1e20*np.mean([pre[n]["crust_thickness_m"] for n in face])+\
              1e21*np.mean([pre[n]["mantle_lithosphere_thickness_m"] for n in face])
            for years in (100,1000):
                R=Rotation.from_rotvec(np.asarray(omegas[plate])*years).as_matrix()
                worst=max(worst,finite_rotation_objectivity(locs,e,e,R));counts+=1
            worst=max(worst,finite_rotation_objectivity(locs,e,e,large));counts+=1
        results.append({
            "extent_cells":width,
            "real_source_parent_nodes":len(ids),
            "real_source_triangles":len(faces),
            "source_plates":sorted(set(plates)),
            "exact_source_contact_edges":len(require_ct["edges"]),
            "contact_plate_pairs":sorted([list(p) for p in set(require_ct["edges"].values())]),
            "parent_nodes_incident_to_contacts":require_ct["contact_parent_node_count"],
            "contact_pair_node_links":len(pairs),
            "triple_junction_parent_node_ids":require_ct["triple_junction_parent_ids"],
            "source_plate_local_views":len(plate_views),
            "source_EN_dofs":K.shape[0],
            "source_P1_K_nnz":stats["nnz"],
            "synthetic_contact_penalty_to_drag":CONTACT_PENALTY_RATIO,
            "Euler_predicted_closing_link_count":sum(
                x["closing_under_Euler_target"] for x in pairs),
            "Euler_predicted_opening_link_count":sum(
                not x["closing_under_Euler_target"] for x in pairs),
            "policies":response,
            "objective_SO3_rigid_frame_parity_max_relative":worst,
            "objective_test_instances":counts,
            "large_rotation_test_rad":float(np.linalg.norm([.6,-.35,.24])),
            "status":"PASS_SOURCE_CONTACT_TOPOLOGY_AND_STATIC_SYNTHETIC_POLICIES",
        })
    need(all(sha256(Path(path))==old for path,old in pinned.items()),
         "CONTACT_SOURCE_CHANGED_DURING_TEST")
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_sha256":pinned,
        "source_global_mesh_sha256":mesh.normalized_sha256,
        "regional_results":results,
        "contact_policy_semantics":{
            "UNWELDED":"NO_CONTACT_FORCE;SOURCE_PLATE_LOCAL_INDEPENDENT",
            "PENALTY_WELDED":"SYNTHETIC_FINITE_FULL_EN_RELATIVE_VELOCITY_PENALTY_NOT_EXACT_CONSTRAINT",
            "CLOSING_NORMAL_ONLY":"SYNTHETIC_FROZEN_EULER_CLOSING_RATE_ACTIVATION_NO_SIGNORINI_GAP_COMPLEMENTARITY",
        },
        "model_years":[100,1000],
        "model_years_used_for_SO3_frame_objectivity_only":True,
        "contact_policy_time_evolution_100_1000_performed":False,
        "all_contact_static_velocity_fields_in_T0_tangent_basis":True,
        "genuine_moving_G2_geometry_or_FEM_remesh":False,
        "G2_physical_rheology":None,"G3_natural_contact_forces":None,
        "HistoryStore_modified":False,"physical_solver_runs":0,
        "physical_T1":None,"D_024":"ACTIVE",
        "peak_process_memory":usage(),
    }
    out.mkdir(parents=True,exist_ok=False)
    p=out/"REPORT.json"
    p.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_SOURCE_CONTACT_OBJECTIVITY_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(p)},
        "no_physical_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True},indent=2)+"\n")
    return {"status":STATUS,
            "regional_results":results,
            "contact_time_evolution_performed":False,
            "physical_solver_runs":0,"physical_T1":None}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multiscale",required=True,type=Path)
    ap.add_argument("--nodal",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--root",type=Path,default=ROOT)
    args=ap.parse_args()
    print(json.dumps(run(args.multiscale,args.nodal,args.output,args.root),
                     indent=2,allow_nan=False))


if __name__=="__main__":
    main()
