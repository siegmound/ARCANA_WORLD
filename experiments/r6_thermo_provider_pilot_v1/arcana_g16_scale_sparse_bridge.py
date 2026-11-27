#!/usr/bin/env python3
"""G16 numerical scale and sparse operator bridge. Real archived regional
operators; actual global FEG structural graph only. No new native solve,
time advancement, physical error threshold or global stiffness fabricated.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
import numpy as np
from scipy import sparse
from scipy.sparse import linalg as sl
from scipy.sparse.csgraph import reverse_cuthill_mckee, connected_components
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g11_adaptive_pilot as g11

G15_PIN='5dc476169e04a2bc31f79addfb04ee8804209e677efa2ee4c4ce5de0edc7d619'
G15_STATUS='G15_MIDPOINT_COUPLING_PILOT_PASS__EVENT_AND_SCALE_REQUIRED'
G14_PIN='cd1f3637b194107309af51e0658986eba3d976beb25b1bfec6004d941f5fbd4d'
G14_STATUS='G14_ADAPTIVE_REGIONAL_TRAJECTORY_PASS__EVENT_AND_SCALE_REQUIRED'
CP_PIN='7d1e4ebb3dfb1f80a6099575e55d63ba19f20b7423f63b45d5bf12cbabc578c3'
START_PIN='e6b8f2e11027e2c64bb3fc1d2fab1fb045954f2372b71a7a1c7c243a3d621470'
TOL={'direct_solution_relative':1e-10,'linear_backward':1e-12,'held_relative':1e-12}
def norm(v): return float(np.max(np.abs(v)))
def relative(x,y): return norm(x-y)/max(norm(x),norm(y),np.finfo(float).tiny)
def backward(A,x,b):
    return norm(A@x-b)/max(float(np.max(np.asarray(abs(A).sum(axis=1)).ravel()))*norm(x)+norm(b),np.finfo(float).tiny)

def sparse_case(feg_file,state,out):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    mesh=parse_feg(feg_file.read_text(),mode='SHELLS_READY')
    with np.load(state) as z:
        A=z['A_pre']; b=z['b_pre'].reshape(-1); B=z['A_post']; q=z['b_post'].reshape(-1)
        held=z['held']; free=z['free']; x=z['velocity'].reshape(-1)
    n=len(x)
    # Support both boolean masks and zero-based index arrays.
    held=np.flatnonzero(held) if held.dtype==bool else held.astype(int).ravel()
    free=np.flatnonzero(free) if free.dtype==bool else free.astype(int).ravel()
    a.need(n==2*len(mesh.nodes)==162 and len(held)==64 and len(free)==98 and
        np.array_equal(np.sort(np.r_[held,free]),np.arange(n)),'DOF_PARTITION')
    a.need(A.shape==B.shape==(n,n) and all(np.isfinite(v).all() for v in (A,b,B,q,x)),'OPERATOR_INVENTORY')
    graph=pattern(mesh)
    coo=sparse.coo_matrix(A)
    a.need(np.all(np.asarray(graph[coo.row,coo.col]).ravel()==1),'NONLOCAL_STIFFNESS')
    diag=B[held,held]
    a.need(np.all(diag>0),'HELD_DIAGONAL')
    target=q[held]/diag
    rhs=b[free]-A[np.ix_(free,held)]@target
    K=A[np.ix_(free,free)]
    sp=sparse.csc_matrix(K)
    t=time.perf_counter(); dense=np.linalg.solve(K,rhs); dense_time=time.perf_counter()-t
    t=time.perf_counter(); lu=sl.splu(sp,permc_spec='COLAMD'); sol=lu.solve(rhs); sparse_time=time.perf_counter()-t
    full=np.empty(n); full[held]=target; full[free]=sol
    post=sl.spsolve(sparse.csc_matrix(B),q)
    dr=relative(sol,dense); pp=relative(full,post)
    br=backward(sp,sol,rhs); bp=backward(sparse.csc_matrix(B),full,q)
    # The saved nonlinear iterate is not the exact solution of the final
    # refreshed linearization. Its difference is reported, not forced zero.
    hist=[]
    try:
        ilu=sl.spilu(sp,drop_tol=1e-6,fill_factor=10)
        pre=sl.LinearOperator(sp.shape,matvec=ilu.solve)
        guess,info=sl.gmres(sp,rhs,M=pre,rtol=1e-12,atol=0.,restart=40,maxiter=10,
                          callback=lambda v:hist.append(float(v)),callback_type='pr_norm')
        iterative={'info':int(info),'iterations':len(hist),'backward':backward(sp,guess,rhs),
                   'difference_vs_direct':relative(guess,sol),'ilu_nnz':int(ilu.L.nnz+ilu.U.nnz)}
    except Exception as exc: iterative={'error':repr(exc)}
    r={'dofs':n,'free_dofs':len(free),'actual_pre_nnz':int(coo.nnz),'graph_upper_bound_nnz':int(graph.nnz),
       'reduced_nnz':int(sp.nnz),'lu_nnz':int(lu.L.nnz+lu.U.nnz),'dense_seconds_single_sample':dense_time,
       'sparse_factor_and_solve_seconds_single_sample':sparse_time,'dense_sparse_relative':dr,
       'elimination_vs_row_replacement_relative':pp,'reduced_backward':br,'full_post_backward':bp,
       'held_relative':relative(full[held],target),'saved_nonlinear_iterate_difference_relative':relative(full,x),
       'iterative_diagnostic':iterative}
    r['screen_pass']=bool(max(dr,pp)<=TOL['direct_solution_relative'] and
        max(br,bp)<=TOL['linear_backward'] and r['held_relative']<=TOL['held_relative'])
    np.savez(out,solution=full,reference_dense_free=dense,held=held,free=free)
    return r

def pattern(mesh):
    n=len(mesh.nodes)
    a.need([v.node_id for v in mesh.nodes]==list(range(1,n+1)) and not mesh.faults,'GRAPH_NODE_IDS_OR_FAULTS')
    tri=np.array([e.node_ids for e in mesh.elements],dtype=np.int64)-1
    a.need(tri.shape==(len(mesh.elements),3) and tri.min()==0 and tri.max()==n-1,'GRAPH_TRIANGLES')
    # All 2x2 blocks associated with the three nodes of each triangle.
    dofs=(2*tri[:,:,None]+np.arange(2)).reshape(-1,6)
    i=np.broadcast_to(dofs[:,:,None],(len(tri),6,6)).ravel()
    j=np.broadcast_to(dofs[:,None,:],(len(tri),6,6)).ravel()
    p=sparse.coo_matrix((np.ones(len(i),dtype=np.int32),(i,j)),shape=(2*n,2*n)).tocsr()
    p.data[:]=1
    return p

def global_graph(root,out):
    from experiments.shellset_regional_explore_v1 import build_case
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    clos=a.read(root/'R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json')
    src=root/build_case.FEG
    pin=clos['evidence']['raw_feg_sha256']
    a.need(a.sha(src)==pin,'GLOBAL_FEG_PIN')
    mesh=parse_feg(src.read_text(),mode='SHELLS_READY')
    a.need(len(mesh.nodes)==64442 and len(mesh.elements)==128880 and not mesh.faults,'GLOBAL_INVENTORY')
    tri=np.array([e.node_ids for e in mesh.elements],dtype=np.int64)-1
    edges=np.sort(np.concatenate((tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]])),axis=1)
    unique,counts=np.unique(edges,axis=0,return_counts=True)
    a.need(len(unique)==193320 and np.all(counts==2) and len(mesh.nodes)-len(unique)+len(tri)==2,'CLOSED_SPHERE')
    P=pattern(mesh); n=P.shape[0]; nnz=P.nnz
    a.need(nnz==4*(len(mesh.nodes)+2*len(unique)),'STRUCTURE_COUNT')
    count,_=connected_components(P,directed=False)
    a.need(count==1,'GLOBAL_CONNECTED')
    def band(M):
        co=M.tocoo()
        return int(np.max(np.abs(co.row-co.col)))
    bw=band(P); perm=reverse_cuthill_mckee(P,symmetric_mode=True)
    rbw=band(P[perm,:][:,perm])
    # Gauge candidates only: tangent velocities of three rigid rotations.
    lat,lon=np.deg2rad(np.array([[v.latitude_deg,v.longitude_deg] for v in mesh.nodes])).T
    xyz=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    south=np.column_stack((np.sin(lat)*np.cos(lon),np.sin(lat)*np.sin(lon),-np.cos(lat)))
    east=np.column_stack((-np.sin(lon),np.cos(lon),np.zeros(len(lat))))
    rot=np.cross(np.eye(3)[None,:,:],xyz[:,None,:])
    G=np.stack((np.einsum('nki,ni->nk',rot,south),np.einsum('nki,ni->nk',rot,east)),axis=1).reshape(n,3)
    gram=G.T@G
    rank=int(np.linalg.matrix_rank(gram))
    a.need(rank==3,'ROTATION_CANDIDATE_RANK')
    sparse.save_npz(out/'GLOBAL_STRUCTURAL_GRAPH.npz',P)
    np.savez(out/'GLOBAL_ORDERING_AND_GAUGE_CANDIDATES.npz',rcm=perm,rotation_modes=G)
    return {'source_FEG_sha256':pin,'nodes':len(mesh.nodes),'triangles':len(tri),'edges':len(unique),'dofs':n,
        'structural_nnz_upper_bound':int(nnz),'connected_components':count,'original_half_bandwidth':bw,
        'rcm_half_bandwidth':rbw,'fp64_csr_bytes_int32':int(8*nnz+4*nnz+4*(n+1)),
        'original_general_band_bytes':int(8*(3*bw+1)*n),'rcm_general_band_bytes':int(8*(3*rbw+1)*n),
        'historical_F2AV_general_band_bytes':int(8*2182*n),'rotation_candidate_rank':rank,
        'rotation_candidate_gram_eigenvalues':np.linalg.eigvalsh(gram).tolist(),
        'global_stiffness_assembled':False,'global_factorization_measured':False,
        'gauge_qualification':False,'screen_pass':True}

def scales(start,coarse,end,trial):
    s,z,t,v=start; _,zz,tt,vv=end
    p=np.asarray(z['canonical_unit_xyz']); R=z['radius_m']
    edges=g4.geometry_edges(np.asarray(z['transport_triangles_zero_based']))
    h=min(R*np.arctan2(np.linalg.norm(np.cross(p[i],p[j])),p[i]@p[j]) for i,j in edges)
    duration=zz['elapsed_years']-z['elapsed_years']
    cmp=g11.compare(start,coarse,end)
    disp=g11.distance(z,zz)
    vmax=float(np.max(np.linalg.norm(v,axis=1)))
    geom_bound=g4.TOL['geometry_fraction']*h/(vmax*g4.YEAR)
    e0=t['two_half_energy_increment_J']; e1=tt['two_half_energy_increment_J']
    T=(e1-e0)/t['heat_capacity_J_K']
    energy=float((e1-e0).sum())
    remaining=z['event_horizon_year']-zz['elapsed_years']
    a.need(duration==50 and remaining>0 and cmp['screen_pass'],'SCALE_SOURCE')
    return {'elapsed_years':zz['elapsed_years'],'interval_years':duration,'min_edge_m':h,'max_displacement_m':disp,
        'max_speed_m_s':vmax,'geometry_difference_m':cmp['position_m'],
        'geometry_difference_over_min_edge':cmp['position_m']/h,
        'geometry_difference_over_interval_displacement':cmp['position_m']/disp,
        'absolute_geometry_tolerance_over_min_edge':g11.TOL['position_m']/h,
        'frozen_speed_displacement_limit_years':geom_bound,
        'event_horizon_exclusive_year':z['event_horizon_year'],'remaining_to_event_years':remaining,
        'max_interval_temperature_increment_K':norm(T),'interval_sensible_heat_increment_J':energy,
        'field_error_ratios':{k:v['difference_over_signal'] for k,v in trial['mechanical_fields'].items()},
        'physical_error_budget_authorized':False,
        'screen_pass':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-scale-bridge',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); g8.check_helpers()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    p=c10.OUT.with_name('R6_THERMO_G15_MIDPOINT_COUPLING_NEW01')
    q=c10.OUT.with_name('R6_THERMO_G14_ADAPTIVE_TRAJECTORY_NEW01')
    pm=c.verified(p,G15_PIN,G15_STATUS); qm=c.verified(q,G14_PIN,G14_STATUS)
    a.need(pm['G14_manifest_sha256']==G14_PIN and all(m['source_sha']==a.SHA and
        all(m[k]==v for k,v in c.SCOPE.items()) for m in (pm,qm)),'SOURCE_SCOPE')
    r=a.read(p/'G15_REPORT.json'); old=a.read(q/'G14_REPORT.json')
    a.need(r['screen_pass'] and r['accepted_checkpoint_sha256']==CP_PIN and
        old['accepted_checkpoint_sha256']==START_PIN and len(r['trials'])==1,'ACCEPTED_LINEAGE')
    tr=r['trials'][0]; folder=p/tr['path']; cp=p/r['accepted_checkpoint']
    start=g11.load(q/old['accepted_checkpoint'],START_PIN); end=g11.load(cp,CP_PIN)
    coarse=g11.load(folder/'coarse/checkpoint_endpoint',tr['coarse']['checkpoint_sha256'])
    index=a.read(p/'ACCEPTED_CHECKPOINT_INDEX.json')
    a.need(index['campaign_screen_pass'] and len(index['entries'])==3 and
        [v['elapsed_years'] for v in index['entries']]==[112.,137.,162.] and
        index['entries'][-1]['checkpoint_sha256']==CP_PIN,'ACCEPTED_INDEX')
    prev=START_PIN
    for entry in index['entries'][1:]:
        a.need(entry['parent_checkpoint_sha256']==prev,'INDEX_CHAIN')
        g11.load(p/entry['checkpoint'],entry['checkpoint_sha256']); prev=entry['checkpoint_sha256']
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G15_manifest':G15_PIN,'checkpoint':CP_PIN,'runner_sha256':a.sha(Path(__file__)),
        'tolerances':TOL,'scope':'Sparse final linearizations only, global structural graph only, no invented coefficients or physical threshold.',
        **c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,'additional_time_advance_years':0,
        'physical_acceptance':False,'cases':{},**c.SCOPE}
    try:
        report['scales']=scales(start,coarse,end,tr)
        for label in ('coarse','half_1','half_2'):
            for stage in ('predictor','corrector'):
                print('G16_SPARSE_REAL_OPERATOR',label,stage,flush=True)
                k=label+'_'+stage
                d=folder/label
                report['cases'][k]=sparse_case(d/(stage+'_deck')/'regional.feg',
                    d/(stage+'_mechanics')/'ultra/C11B_FINAL_STATE.npz',out/(k+'_solution.npz'))
        print('G16_GLOBAL_STRUCTURAL_GRAPH',flush=True)
        report['global_graph']=global_graph(root,out)
        report['screen_pass']=bool(all(x['screen_pass'] for x in report['cases'].values()) and
            report['global_graph']['screen_pass'] and report['scales']['screen_pass'])
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for path,man,pin in ((p,pm,G15_PIN),(q,qm,G14_PIN)):
        a.need(c.inventory(path)==man['files'] and a.sha(path/'MANIFEST.json')==pin,'PARENT_MUTATION')
    status='G16_SPARSE_LINEAR_BRIDGE_AND_SCALE_AUDIT_PASS__GLOBAL_ASSEMBLY_REQUIRED' if report['screen_pass'] else 'G16_SCALE_BRIDGE_BLOCKED'
    report.update(status=status,limitations=[
        'Six final regional linearizations, not full sparse nonlinear native execution.',
        'Global graph is connectivity-derived structural support, not a mechanical operator; LU fill and runtime unknown.',
        'Rotation modes have algebraic rank three only; no actual global nullspace, torque or gauge qualification.',
        'No physical error budget inferred from numerical tolerances, no event transition or canonical T1.'])
    a.write(out/'G16_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G15_manifest_sha256':G15_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G16_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True); print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
