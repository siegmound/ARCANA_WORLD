#!/usr/bin/env python3
"""G24 retained global operator audit. No equilibrium solve, native run or load correction."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, eigsh, ArpackNoConvergence
from scipy.sparse.csgraph import connected_components

PIN='ddb51be4fb3e7d5a6e56f7caaa11f3861792a25239489b532e6350d726637abc'
SOURCE='901cbb4a38916190df6a881bb561b6558dd997dd'
PARENT_STATUS='G23_CONDITIONAL_GLOBAL_CSR_ASSEMBLY_PASS__OPERATOR_AND_PHYSICAL_AUTHORITY_REQUIRED'
AUTH='G24_RETAINED_OPERATOR_AND_LOAD_DIAGNOSTIC_ONLY_V1'
SCOPE={'physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
       'D_024':'ACTIVE','D_025':'ACTIVE','scientific_promotion':False}
N=128884
MODELS=('native_diorite2','native_legacy')

def need(ok,msg):
    if not ok: raise RuntimeError(msg)

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def read(p): return json.loads(p.read_text())
def write(p,d):
    with p.open('x') as f: json.dump(d,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')

def inventory(p):
    return {str(x.relative_to(p)):sha(x) for x in sorted(p.rglob('*'))
            if x.is_file() and x!=p/'MANIFEST.json'}

def verify(p):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==PIN and m['status']==PARENT_STATUS
         and m['source_sha']==SOURCE,'G23_PIN_SCOPE')
    need(all(m[k]==v for k,v in SCOPE.items()),'G23_SCOPE')
    need(inventory(p)==m['files'],'G23_INVENTORY')
    return m

def norminf(A): return float(np.max(np.asarray(abs(A).sum(axis=1)).ravel()))

def load(p):
    A=sparse.load_npz(p/'GLOBAL_PRE_BC_CSR.npz').tocsr()
    with np.load(p/'GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as f:
        b,G,xyz,fixed=(f[k].copy() for k in ('rhs','rotation_candidates','native_xyz','fixed_load'))
    need(A.shape==(N,N) and A.nnz==1804328 and A.has_canonical_format,'CSR_SHAPE')
    need(b.shape==fixed.shape==(N,) and G.shape==(N,3) and xyz.shape==(N//2,3),'FIELDS_SHAPE')
    need(all(np.isfinite(x).all() for x in (A.data,b,G,xyz,fixed)),'NONFINITE')
    need(np.max(abs(np.linalg.norm(xyz,axis=1)-1))<1e-12,'UNIT_GEOMETRY')
    # Verify the Cartesian rigid rotations independently of the archived basis.
    geo=np.loadtxt(p/'G23_NATIVE_GEOMETRY.dat')
    need(geo.shape==(N//2,3) and np.array_equal(geo[:,0],np.arange(1,N//2+1)),'GEOMETRY_ORDER')
    t,l=geo[:,1:].T
    xx=np.column_stack((np.sin(t)*np.cos(l),np.sin(t)*np.sin(l),np.cos(t)))
    south=np.column_stack((np.cos(t)*np.cos(l),np.cos(t)*np.sin(l),-np.sin(t)))
    east=np.column_stack((-np.sin(l),np.cos(l),np.zeros_like(l)))
    rot=np.cross(np.eye(3)[None,:,:],xx[:,None,:])
    expected=np.stack((np.einsum('nki,ni->nk',rot,south),
                       np.einsum('nki,ni->nk',rot,east)),axis=1).reshape(N,3)
    need(np.max(abs(xx-xyz))<1e-12 and np.max(abs(expected-G))<1e-12,'ROTATION_REPLAY')
    return A,b,G,xyz,fixed

def basis(G):
    Q,R=np.linalg.qr(G,mode='reduced')
    need(np.min(abs(np.diag(R)))>1e-10*np.max(abs(np.diag(R))),'ROTATION_RANK')
    return Q

def load_audit(p,b,G,xyz,fixed,Q,out):
    contrib=(G*b[:,None]).reshape(-1,2,3).sum(axis=1)
    fp=(G*fixed[:,None]).reshape(-1,2,3).sum(axis=1)
    denom=np.sum(abs(G)*abs(b[:,None]),axis=0)
    owners=np.loadtxt(p/'regional_reporting_plates.dat',dtype=np.int64)
    need(owners.shape==(N//2,2) and np.array_equal(owners[:,0],np.arange(1,N//2+1))
         and np.all((owners[:,1]>=2)&(owners[:,1]<=13)),'PLATE_ORDER')
    lat=np.rad2deg(np.arcsin(np.clip(xyz[:,2],-1,1)))
    lon=np.rad2deg(np.arctan2(xyz[:,1],xyz[:,0]))
    def group(mask):
        return {'nodes':int(mask.sum()),'signed_projection':contrib[mask].sum(axis=0).tolist(),
                'absolute_node_projection':abs(contrib[mask]).sum(axis=0).tolist()}
    plates={str(i-2):group(owners[:,1]==i) for i in range(2,14)}
    bands={}
    for lo in range(-90,90,15):
        mask=(lat>=lo)&((lat<lo+15) if lo<75 else (lat<=90))
        bands[str(lo)]=group(mask)
    top=[]
    for axis in range(3):
        for j in np.argsort(abs(contrib[:,axis]))[-20:][::-1]:
            top.append({'axis':axis,'node_id':int(j+1),'lat_deg':float(lat[j]),'lon_deg':float(lon[j]),
                        'owner_plate':int(owners[j,1]-2),'signed_projection':float(contrib[j,axis])})
    write(out/'LOAD_LOCALIZATION.json',{'by_reporting_plate':plates,'by_latitude_band':bands,
                                       'top_nodes_per_axis':top,
                                       'note':'Reporting groups, not causal force-source attribution.'})
    return {'rhs_equals_fixed_exact':bool(np.array_equal(b,fixed)),
            'rhs_minus_fixed_max_abs':float(np.max(abs(b-fixed))),
            'rotation_projection':(G.T@b).tolist(),
            'fixed_rotation_projection':(G.T@fixed).tolist(),
            'nonfixed_rotation_projection':(G.T@(b-fixed)).tolist(),
            'rotation_projection_relative':(abs(G.T@b)/np.maximum(denom,1e-300)).tolist(),
            'orthogonal_projection_fraction_l2':float(np.linalg.norm(Q.T@b)/np.linalg.norm(b)),
            'load_modified':False}

def spectral(A,G):
    d=A.diagonal()
    need(np.all(d>0),'NONPOSITIVE_DIAGONAL')
    inv=1/np.sqrt(d)
    M=A.multiply(inv[:,None]).multiply(inv[None,:]).tocsr()
    # Symmetrization is confined to the diagnostic operator and measured.
    asym=norminf(M-M.T)/norminf(M)
    M=((M+M.T)*0.5).tocsr()
    scale=norminf(M)
    Q=basis(np.sqrt(d)[:,None]*G)
    lift=2*scale
    def mv(x):
        q=Q.T@x
        y=x-Q@q
        z=M@y
        return z-Q@(Q.T@z)+lift*(Q@q)
    op=LinearOperator(M.shape,matvec=mv,dtype=np.float64)
    rng=np.random.default_rng(2401)
    v0=rng.normal(size=M.shape[0]); v0-=Q@(Q.T@v0)
    converged=True
    try:
        w,V=eigsh(op,k=6,which='SA',tol=1e-9,ncv=48,maxiter=1200,v0=v0)
    except ArpackNoConvergence as e:
        converged=False; w=e.eigenvalues; V=e.eigenvectors
    if w is None or V is None:
        w=np.empty(0); V=np.empty((M.shape[0],0))
    order=np.argsort(w); w=w[order]; V=V[:,order]
    residual=[float(np.linalg.norm(mv(x)-lam*x)) for lam,x in zip(w,V.T)]
    original=[float(np.linalg.norm(M@x-lam*x)) for lam,x in zip(w,V.T)]
    overlap=np.linalg.norm(Q.T@V,axis=0)
    screen=bool(converged and len(w)==6 and min(w)>1e-8*scale
                and max(residual)<1e-8*scale and max(original)<1e-8*scale
                and max(overlap)<1e-6)
    return {'method':'smallest algebraic Ritz values, diagonal congruence, projected symmetric diagnostic with known modes lifted',
            'converged':converged,'scaled_asymmetry_before_symmetrization':asym,
            'scaled_operator_inf_norm':scale,'scaled_rotation_residual_l2':np.linalg.norm(M@Q,axis=0).tolist(),
            'lift':lift,'ritz_values':w.tolist(),'ritz_residual_l2':residual,
            'original_scaled_operator_residual_l2':original,'rotation_overlap_l2':overlap.tolist(),
            'positive_complement_screen':screen,'rank_proven':False,'factorization_performed':False,
            'thresholds':{'gap_over_inf_norm':1e-8,'residual_over_inf_norm':1e-8,'overlap':1e-6},
            'maxiter':1200,'ncv':48,'seed':2401}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-diagnostic-only',choices=[AUTH],required=True)
    args=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'FROZEN_SOURCE')
    p=args.parent.resolve(); out=args.output.resolve()
    m=verify(p)
    need(not out.exists() and not out.is_relative_to(p) and not out.is_relative_to(root),'OUTPUT_NOT_FRESH')
    out.mkdir()
    report={'additional_native_assemblies':0,'additional_native_solves':0,'additional_time_advance_years':0,
            'material_assignments':0,'global_solve_authorized':False,'physical_acceptance':False,
            'source_sha':SOURCE,'G23_manifest_sha256':PIN,**SCOPE}
    try:
        print('G24_PARENT_VERIFIED',flush=True)
        A,b,G,xyz,fixed=load(p/MODELS[0])
        B,c,H,uvw,other=load(p/MODELS[1])
        identical=all(np.array_equal(x,y) for x,y in ((A.data,B.data),(A.indices,B.indices),(A.indptr,B.indptr),
                          (b,c),(G,H),(xyz,uvw),(fixed,other)))
        need(identical,'G23_PAIR_NOT_EXACT')
        del B,c,H,uvw,other
        ctl=[read(p/k/'CONDITIONAL_CONTROLS.json') for k in MODELS]
        report['controls_differ']={k:[ctl[0].get(k),ctl[1].get(k)] for k in sorted(set(ctl[0])|set(ctl[1]))
                                   if ctl[0].get(k)!=ctl[1].get(k)}
        Q=basis(G)
        scale=norminf(A)
        report['operator']={'paired_exact':identical,'relative_asymmetry':norminf(A-A.T)/scale,
            'structural_connected_components':int(connected_components(A,directed=False,return_labels=False)),
            'rotation_basis_gram_eigenvalues':np.linalg.eigvalsh(G.T@G).tolist(),
            'right_rotation_residual_inf_scaled':(np.max(abs(A@G),axis=0)/scale).tolist(),
            'left_rotation_residual_inf_scaled':(np.max(abs(A.T@G),axis=0)/scale).tolist()}
        report['load']=load_audit(p/MODELS[0],b,G,xyz,fixed,Q,out)
        write(out/'PRE_SPECTRAL_DIAGNOSTIC.json',report)
        print('G24_LOAD_AUDIT',json.dumps(report['load']),flush=True)
        print('G24_SPECTRAL_SCREEN_START',flush=True)
        report['spectrum']=spectral(A,G)
        print('G24_SPECTRAL_SCREEN_RESULT',json.dumps(report['spectrum']),flush=True)
        report['status']=('G24_OPERATOR_DIAGNOSTIC_PASS__LOAD_CLOSURE_REQUIRED'
                          if report['spectrum']['positive_complement_screen']
                          else 'G24_OPERATOR_DIAGNOSTIC_RETAINED__SPECTRUM_UNRESOLVED')
    except Exception as e:
        report['status']='G24_DIAGNOSTIC_BLOCKED'; report['error']=repr(e)
    need(verify(p)==m,'G23_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G24_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
          'G23_manifest_sha256':PIN,'runner_sha256':sha(Path(__file__)),
          'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G24_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['status'].startswith('G24_OPERATOR_DIAGNOSTIC_PASS') else 2

if __name__=='__main__': raise SystemExit(main())
