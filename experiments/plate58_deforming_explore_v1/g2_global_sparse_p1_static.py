"""ARCANA R6 real spherical P1 G2 sparse tangent: regional dense parity then global static probe.

ENGINEERING_ONLY: authentic G1 mesh/Euler and PRE thickness; invented material
viscosities; no real G2 constitutive calibration or G3 loads. Source-global
plate-local views remain separate at contacts. NO global time integration.
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
from scipy.sparse.linalg import LinearOperator, cg

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, NODES, TRIANGLES, PLATES, source_inputs, build_views, sha256,
    usage, RADIUS_M,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    assemble_spherical_exterior, spherical_element_tangent,
    frames_and_cartesian,
)
from experiments.plate58_deforming_explore_v1.g1_g2_manufactured_feedback import (
    ETA_CRUST_PA_S, ETA_MANTLE_PA_S, DASHPOT_TO_MEAN_TANGENT,
)

SCHEMA = "ARCANA_R6_GLOBAL_SOURCE_SPARSE_P1_STATIC_G2_V1"
STATUS = "PASS_REGIONAL_DENSE_SPARSE_P1_PARITY_AND_12_PLATE_GLOBAL_STATIC_ENGINEERING__PHYSICS_OPEN"


class SparseP1Error(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise SparseP1Error(code)


def sparse_p1_tangent(latlon, faces, eta_h, lambda_h):
    """Assemble exactly the existing spherical_element_tangent in sparse COO.

    Local indices of faces are zero-based and must match latlon source view
    order. Element DOFs are [E0,N0,E1,N1,E2,N2]. No synthetic graph Laplacian.
    """
    ll = np.asarray(latlon, dtype=np.float64)
    tri = np.asarray(faces, dtype=np.int32)
    eta = np.asarray(eta_h, dtype=np.float64)
    bulk = np.asarray(lambda_h, dtype=np.float64)
    n = len(ll); m = len(tri)
    need(ll.shape == (n,2) and n>=3 and
         tri.shape == (m,3) and m>0 and
         eta.shape == bulk.shape == (m,) and
         bool(np.all(np.isfinite(ll))) and
         bool(np.all(np.isfinite(eta))) and
         bool(np.all(np.isfinite(bulk))) and
         bool(np.all(eta>0)) and bool(np.all(bulk>=0)) and
         bool(np.all((tri>=0)&(tri<n))) and
         bool(np.all((tri[:,0]!=tri[:,1]) &
                     (tri[:,0]!=tri[:,2]) &
                     (tri[:,1]!=tri[:,2]))),
         "SPARSE_P1_INVALID_MATERIAL_GEOMETRY_OR_INDEX")
    rows=np.empty(m*36,dtype=np.int32)
    cols=np.empty(m*36,dtype=np.int32)
    vals=np.empty(m*36,dtype=np.float64)
    facet_sum=0.; sphere_sum=0.; worst_deficit=0.
    for i in range(m):
        nodes=tri[i]
        ke,geo=spherical_element_tangent(ll[nodes],float(eta[i]),float(bulk[i]))
        dof=(np.repeat(2*nodes,2)+np.tile(np.array([0,1],dtype=np.int32),3))
        sl=slice(36*i,36*(i+1))
        rows[sl]=np.repeat(dof,6)
        cols[sl]=np.tile(dof,6)
        vals[sl]=ke.reshape(36)
        facet_sum+=geo["facet_area_m2"]
        sphere_sum+=geo["spherical_area_m2"]
        worst_deficit=max(worst_deficit,geo["facet_sphere_relative_area_deficit"])
    # Addition of per-element contributions is the only assembly rule.
    K=sparse.coo_matrix((vals,(rows,cols)),shape=(2*n,2*n)).tocsr()
    K.sum_duplicates()
    K.eliminate_zeros()
    need(K.nnz>0 and np.all(np.isfinite(K.data)),
         "SPARSE_P1_NONFINITE_ASSEMBLY")
    skew=K-K.T
    max_skew=float(np.max(np.abs(skew.data))) if skew.nnz else 0.
    scale=max(float(np.max(np.abs(K.data))),1e-300)
    need(max_skew/scale<=1e-12,"SPARSE_P1_ASYMMETRIC_ASSEMBLY")
    return K,{
        "source_nodes":n,"source_triangles":m,
        "EN_dofs":2*n,"nnz":int(K.nnz),
        "one_csr_bytes":int(K.data.nbytes+K.indices.nbytes+K.indptr.nbytes),
        "maximum_relative_symmetry_defect":max_skew/scale,
        "total_facet_area_m2":float(facet_sum),
        "total_geodesic_area_m2":float(sphere_sum),
        "worst_facet_sphere_area_deficit_fraction":worst_deficit,
    }


def local_law_from_pre(parent_nodes, faces, pre):
    """Invented Kelvin–Voigt viscosity times authentic T0 layer thickness."""
    arr_c=np.asarray([float(pre[int(i)]["crust_thickness_m"])
                      for i in parent_nodes],dtype=float)
    arr_m=np.asarray([float(pre[int(i)]["mantle_lithosphere_thickness_m"])
                      for i in parent_nodes],dtype=float)
    tri=np.asarray(faces,dtype=int)
    need(bool(np.all(np.isfinite(arr_c))) and
         bool(np.all(np.isfinite(arr_m))) and
         bool(np.all(arr_c>0)) and bool(np.all(arr_m>0)),
         "SPARSE_P1_PRE_LAYER_THICKNESS_INVALID")
    eta=ETA_CRUST_PA_S*np.mean(arr_c[tri],axis=1)+ETA_MANTLE_PA_S*np.mean(arr_m[tri],axis=1)
    return eta,eta.copy()


def regional_dense_parity(multiscale_dir:Path,nodal_dir:Path):
    """Read original sealed FEG and nodal-PRE before checking identical P1."""
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential)
    from experiments.plate58_deforming_explore_v1.prepare import sha

    def read(path):return json.loads(path.read_text())
    mm=read(multiscale_dir/"MANIFEST.json")
    model=read(multiscale_dir/"CONTINUATION_A.json")
    nm=read(nodal_dir/"MANIFEST.json")
    nodal=read(nodal_dir/"SOURCE_NODAL_ELEMENT_G2.json")
    need(mm["files"]["CONTINUATION_A.json"]==sha(multiscale_dir/"CONTINUATION_A.json")
         and nm["files"]["SOURCE_NODAL_ELEMENT_G2.json"]==sha(nodal_dir/"SOURCE_NODAL_ELEMENT_G2.json")
         and nodal["source_multiscale_manifest_sha256"]==sha(multiscale_dir/"MANIFEST.json")
         and model["mechanical_solve_authorized"] is False,
         "SPARSE_P1_REGIONAL_PROVENANCE_FAILED")
    scales={int(s["extent_cells"]):s for s in nodal["scales"]}
    reg={int(s["cell_extent_per_side"]):s for s in model["topological_comparative_extents"]}
    need(set(scales)==set(reg)=={8,16},"SPARSE_P1_REGIONAL_SCALE_INVENTORY")
    results=[]
    for width in (8,16):
        r=reg[width];s=scales[width]
        ids=list(map(int,r["parent_node_ids"]))
        f=multiscale_dir/f"OUTER_A_{width:02d}x{width:02d}.feg"
        pf=multiscale_dir/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
        need(sha(f)==r["output_FEG_sha256"] and sha(pf)==r["output_PRE_sha256"],
             "SPARSE_P1_REGIONAL_FEG_PRE_SHA_MISMATCH")
        model_feg=parse_feg(f.read_text(),mode="SHELLS_READY")
        pre=parse_regional_pre(pf,r["PRE_source_field_order"],ids)
        need({str(k):v for k,v in pre.items()}==
             {str(k):v for k,v in s["source_PRE_by_parent_node"].items()},
             "SPARSE_P1_REGIONAL_NODAL_BINDING_FAILED")
        for item in pre.values():
            validate_column_for_potential(item)
        ll=np.array([[float(n.latitude_deg),float(n.longitude_deg)]
                     for n in model_feg.nodes],dtype=float)
        faces=np.array([[int(node)-1 for node in el.node_ids]
                        for el in model_feg.elements],dtype=np.int32)
        eta,bulk=local_law_from_pre(ids,faces,pre)
        triangles={}
        materials={}
        for j,tid in enumerate(r["parent_triangle_ids"]):
            triangles[int(tid)]=tuple(ids[k] for k in faces[j])
            materials[int(tid)]={
                "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
                "source_reference":"MANUFACTURED_TWO_LAYER_KELVIN_VOIGT_20261120",
                "eta_h_pa_s_m":float(eta[j]),
                "lambda_h_pa_s_m":float(bulk[j])
            }
        dense=assemble_spherical_exterior(
            ids,triangles,dict(zip(ids,ll)),materials)["tangent"]
        K,stats=sparse_p1_tangent(ll,faces,eta,bulk)
        rng=np.random.default_rng(810+width)
        x=rng.normal(size=2*len(ids));y=rng.normal(size=2*len(ids))
        kx=K@x;dx=dense@x
        norm=max(np.linalg.norm(dx),1e-100)
        error=float(np.linalg.norm(kx-dx)/norm)
        energy=float(abs(x@(K@y)-y@(K@x))/
                    max(abs(x@(K@y))+abs(y@(K@x)),1e-100))
        diff=K.toarray()-dense
        entry=float(np.max(np.abs(diff))/max(np.max(np.abs(dense)),1e-100))
        need(error<5e-12 and energy<5e-12 and entry<5e-12,
             "SPARSE_P1_REGIONAL_DENSE_PARITY_FAILED")
        results.append({
            "extent":width,"source_nodes":len(ids),
            "source_triangles":len(faces),
            "relative_Kx_error":error,
            "relative_xKy_symmetry_error":energy,
            "relative_max_matrix_entry_error":entry,
            **stats,
        })
    return results,sha(multiscale_dir/"MANIFEST.json"),sha(nodal_dir/"MANIFEST.json")


def read_pre_thickness(path:Path, metadata:dict):
    """Read actual global 51-field PRE; no default or fictional materials."""
    order=metadata["field_order"]
    ids=[order.index("node_id"),order.index("crust_thickness_m"),
         order.index("mantle_lithosphere_thickness_m")]
    c=np.empty(NODES,dtype=np.float64)
    m=np.empty(NODES,dtype=np.float64)
    with path.open(encoding="utf-8") as f:
        head=f.readline().split()
        expected=metadata["header"]
        need(head==[expected["magic"],expected["schema"],str(NODES)],
             "SPARSE_P1_GLOBAL_PRE_HEADER_INVALID")
        count=0
        for count,line in enumerate(f,1):
            need(count<=NODES,"SPARSE_P1_GLOBAL_PRE_TOO_MANY_ROWS")
            parts=line.split()
            need(len(parts)==51 and int(parts[ids[0]])==count,
                 "SPARSE_P1_GLOBAL_PRE_ORDER_INVALID")
            c[count-1]=float(parts[ids[1]])
            m[count-1]=float(parts[ids[2]])
    need(count==NODES and np.all(np.isfinite(c)) and
         np.all(np.isfinite(m)) and np.all(c>0) and np.all(m>0),
         "SPARSE_P1_GLOBAL_PRE_THICKNESS_INVALID")
    return c,m


def assemble_real_global_source(root:Path):
    """Full authentic P1 12-plate assembly; contact copies are *not* welded."""
    mesh,omegas,pins,horizon,pre_metadata=source_inputs(root)
    need(horizon>1000 and len(omegas)==12,
         "SPARSE_P1_FIRST_EVENT_HORIZON_INSUFFICIENT")
    views=build_views(mesh)
    cth,mth=read_pre_thickness(
        root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",pre_metadata)
    ll=[]; tri=[];eta=[];bulk=[];plate_view=[];node_parent=[]
    offset=0
    for plate in PLATES:
        view=views[plate]
        ids0=np.asarray(view["ids"],dtype=int)
        local=np.asarray(view["triangles"],dtype=np.int32)
        need(local.ndim==2 and local.shape[1]==3 and
             np.all(ids0>=0) and np.all(ids0<NODES),
             "SPARSE_P1_GLOBAL_PLATE_LOCAL_ID_INVALID")
        ll.append(np.asarray(mesh.vertices_lat_lon,dtype=float)[ids0])
        tri.append(local+offset)
        hc=np.mean(cth[ids0][local],axis=1)
        hm=np.mean(mth[ids0][local],axis=1)
        e=ETA_CRUST_PA_S*hc+ETA_MANTLE_PA_S*hm
        eta.append(e);bulk.append(e.copy())
        plate_view.append(np.full(len(ids0),int(plate),dtype=np.int16))
        node_parent.append(ids0.copy())
        offset+=len(ids0)
    ll=np.concatenate(ll,axis=0); faces=np.concatenate(tri,axis=0)
    eta=np.concatenate(eta);bulk=np.concatenate(bulk)
    plate_view=np.concatenate(plate_view);node_parent=np.concatenate(node_parent)
    need(len(ll)==66435 and len(faces)==TRIANGLES and
         len(eta)==TRIANGLES and len(set(plate_view))==12 and
         len(set(node_parent))==NODES,
         "SPARSE_P1_GLOBAL_SOURCE_INVENTORY_CHANGED")
    K,stats=sparse_p1_tangent(ll,faces,eta,bulk)
    need(K.shape==(132870,132870),"SPARSE_P1_GLOBAL_DOF_COUNT_CHANGED")
    # Fail closed if ANY K entry couples two different plate material views.
    csr_rows=np.repeat(np.arange(K.shape[0],dtype=np.int32),
                       np.diff(K.indptr))
    need(not bool(np.any(plate_view[csr_rows//2] !=
                         plate_view[K.indices//2])),
         "SPARSE_P1_GLOBAL_UNAUTHORIZED_CROSS_PLATE_WELD")
    del csr_rows
    # Exact Euler per-plate tangent target at 210 Ma, not a natural load.
    xyz,unit,east,north=frames_and_cartesian(ll)
    omega=np.array([omegas[int(p)] for p in plate_view])
    target_xyz=np.cross(omega,xyz)
    euler=np.stack((np.einsum("ij,ij->i",target_xyz,east),
                    np.einsum("ij,ij->i",target_xyz,north)),axis=1).reshape(-1)
    # Synthetic non-rigid added target makes K action observable even though
    # pure plate Euler rotation is a rigid null mode.
    lat=np.deg2rad(ll[:,0]);lon=np.deg2rad(ll[:,1])
    trial=np.stack((.004*np.sin(3*lat+2*lon),
                    .003*np.cos(2*lat-3*lon)),axis=1).reshape(-1)
    g=euler+trial
    return K,stats,{
        "euler":euler,"manufactured_target":g,
        "synthetic_nonrigid_part":trial,
        "node_parent_zero_based":node_parent,
        "plate_id_per_view":plate_view,
        "source_pins":pins,
        "source_mesh_sha256":mesh.normalized_sha256,
        "topology_no_welded_plate_cross_edges":True,
    }


def static_global_spd_probe(K, stats, fields):
    """A manufactured full-global FEM response, not a G3 force inversion."""
    diag=K.diagonal()
    need(np.all(np.isfinite(diag)) and np.min(diag)>0,
         "SPARSE_P1_GLOBAL_DIAGONAL_UNQUALIFIED")
    c=float(DASHPOT_TO_MEAN_TANGENT*np.mean(diag))
    need(math.isfinite(c) and c>0,"SPARSE_P1_GLOBAL_DRAG_INVALID")
    g=fields["manufactured_target"]
    er=fields["euler"]
    # Euler velocity must be a null mode *on each independent plate*.
    ke=K@er
    normalizer=max(float(np.max(diag))*float(np.linalg.norm(er)),1e-99)
    rigid_rel=float(np.linalg.norm(ke)/normalizer)
    need(rigid_rel<1e-9,"SPARSE_P1_GLOBAL_EULER_RIGID_NULL_MODE_FAILED")
    # A = I + K/C, where K is the authentic synthetic P1 tangent.
    A=K.multiply(1/c).tocsr()+sparse.eye(K.shape[0],format="csr")
    d=A.diagonal()
    need(np.min(d)>0 and np.all(np.isfinite(d)),
         "SPARSE_P1_GLOBAL_SPD_PRECONDITIONER_INVALID")
    M=LinearOperator(A.shape,matvec=lambda x:x/d,dtype=np.float64)
    iterations=[0]
    def count(_):iterations[0]+=1
    result,info=cg(A,g,rtol=1e-8,atol=0.,maxiter=1200,M=M,callback=count)
    residual=float(np.linalg.norm(A@result-g)/np.linalg.norm(g))
    work_in=float(g@result)
    work_drag=float(result@result)
    work_internal=float(result@(K@result)/c)
    work_rel=abs(work_in-work_drag-work_internal)/max(abs(work_in),1e-99)
    nonrigid_force_ratio=float(np.linalg.norm(K@fields["synthetic_nonrigid_part"])/
                              max(np.max(diag)*np.linalg.norm(fields["synthetic_nonrigid_part"]),1e-99))
    need(info==0 and residual<2e-8 and work_rel<2e-8 and
         nonrigid_force_ratio>1e-10 and
         np.all(np.isfinite(result)),
         "SPARSE_P1_GLOBAL_STATIC_FORCE_WORK_OR_CG_FAILED")
    return {
        "global_synthetic_static_P1_solve":"PASS",
        "cg_info":int(info),"cg_iterations":iterations[0],
        "cg_final_relative_residual":residual,
        "synthetic_static_work_balance_relative":work_rel,
        "pure_euler_rigid_rotation_K_action_relative":rigid_rel,
        "synthetic_nonrigid_K_action_relative":nonrigid_force_ratio,
        "g1_target_RMS_m_per_year":float(np.sqrt(np.mean(g**2))),
        "coupled_static_RMS_m_per_year":float(np.sqrt(np.mean(result**2))),
        "relative_velocity_correction":float(np.linalg.norm(result-g)/np.linalg.norm(g)),
        "K_sparse_csr_bytes":stats["one_csr_bytes"],
        "A_sparse_csr_bytes":int(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes),
        "K_nonzero_entries":int(K.nnz),
        "sparse_diagonal_preconditioner":True,
        "not_a_100_or_1000_year_evolution":True,
    }


def execute(multiscale:Path,nodal:Path,out:Path,root:Path=ROOT):
    need(not out.exists(),"SPARSE_P1_OUTPUT_EXISTS")
    start=time.perf_counter()
    before=usage()
    source_files=[
        multiscale/"MANIFEST.json",
        multiscale/"CONTINUATION_A.json",
        nodal/"MANIFEST.json",
        nodal/"SOURCE_NODAL_ELEMENT_G2.json",
        root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
        root/"R6_T0_CANONICAL_PLATE_KINEMATICS.json",
    ]
    hashes={str(p):sha256(p) for p in source_files}
    regional,mm,nm=regional_dense_parity(multiscale,nodal)
    stage1=time.perf_counter()
    K,stats,fields=assemble_real_global_source(root)
    stage2=time.perf_counter()
    global_results=static_global_spd_probe(K,stats,fields)
    stage3=time.perf_counter()
    need(all(sha256(p)==h for p,h in
             [(Path(k),v) for k,v in hashes.items()]),
         "SPARSE_P1_SOURCE_MODIFIED_DURING_TEST")
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_commit_expected_from_operator":"RUN_ON_CHECKED_OUT_GITHUB_HEAD",
        "source_files_sha256":hashes,
        "mesh_SHA256":fields["source_mesh_sha256"],
        "source_synthesized_material":"eta_h=1e20*PRE_crust_m + 1e21*PRE_mantle_m; lambda_h=eta_h",
        "regional_dense_sparse_PARITY":regional,
        "source_global_sparse_P1":stats,
        "global_static_manufactured_probe":global_results,
        "benchmark_wall_s":{
            "regional_parity":stage1-start,
            "global_assembly":stage2-stage1,
            "global_static_solve":stage3-stage2,
            "total":time.perf_counter()-start,
        },
        "peak_process_memory":usage(),
        "baseline_process_memory":before,
        "source_global_12_plates_separate_views":True,
        "genuine_mechanical_plate_contact_and_slip_laws":None,
        "natural_G3_loads":None,
        "calibrated_G2_material":None,
        "physical_solver_runs":0,"physical_T1":None,
        "mechanical_solve_authorized":False,
        "HistoryStore_modified":False,"D_024":"ACTIVE",
    }
    out.mkdir(parents=True,exist_ok=False)
    p=out/"REPORT.json"
    p.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    manifest={
        "schema":"ARCANA_R6_GLOBAL_SPARSE_P1_STATIC_MANIFEST_V1",
        "status":STATUS,
        "files":{"REPORT.json":sha256(p)},
        "no_physical_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True,
    }
    (out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {"status":STATUS,
            "regional_dense_sparse_parity":regional,
            "global_source_scale":stats,
            "global_static_solve":global_results,
            "wall_s":report["benchmark_wall_s"],
            "physical_solver_runs":0,"physical_T1":None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(a.multiscale,a.nodal,a.output,a.root),indent=2))


if __name__=="__main__":
    main()
