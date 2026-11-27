#!/usr/bin/env python3
"""G32: corrected global first-linearization assembly and revised torque budget.
One retained Diorite2 deck, no global solve or active-source changes.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback
import numpy as np
from scipy import sparse
import arcana_g23_conditional_global_csr as g23
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27
import arcana_g29_native_metric_candidate as g29

SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
P29='fb2ce020ba500e231032696311face81f94298e6ad606608c18f8d76083d2149'
P31='28ebbee110fa1e3e96f1842e7542deef6c26277cac9ee0ec535b3a267f9ee7fb'
S29='G29_NATIVE_GLOBAL_METRIC_PARITY_PASS__REGIONAL_AND_TORQUE_REVIEW_REQUIRED'
S31='G31_CORRECTED_DIRECT_CSR_PARITY_PASS__TRAJECTORY_AND_GLOBAL_CLOSURE_REQUIRED'
P30='3298f0b7ef41083068ada52e71d62a0238a96076372625cc8fa42dd210d7cee2'
AUTH='G32_CORRECTED_GLOBAL_ASSEMBLY_ONLY_V1'
DECK=(*g25.DECK,'G18_GRAPH.dat','CONDITIONAL_CONTROLS.json')
def verify(p,pin,status):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==pin and m['status']==status and m['source_sha']==SOURCE
         and all(m[k]==v for k,v in SCOPE.items()),'PARENT_PIN_SCOPE:'+p.name)
    need(inventory(p)==m['files'],'PARENT_INVENTORY:'+p.name)
    return m
def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json'); argv=meta['argv']
    need(argv[-2:]==['-o','assembly_only.exe'] and all(x in argv for x in ('-O0','-Mbounds','-Kieee')),'BUILD_FLAGS')
    need(sha(Path(argv[0]))==meta['compiler_sha256'] and sha(old/'assembly_only.exe')==meta['exe_sha256'],'COMPILER_OR_EXE')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for n,pin in meta['library_sha256'].items(): need(sha(libs[0]/n)==pin,'LIB_DRIFT:'+n)
    new.mkdir()
    for n,pin in meta['source_sha256'].items():
        need(Path(n).name==n and sha(old/n)==pin,'SOURCE_DRIFT:'+n)
        shutil.copyfile(old/n,new/n)
    p=new/'MOD_Shells.f90'; p.write_text(g29.patch_fixed(p.read_text()))
    need([n for n,pin in meta['source_sha256'].items() if sha(new/n)!=pin]==['MOD_Shells.f90'],'PATCH_SCOPE')
    need('G23_STOP_AFTER_GLOBAL_CSR_BEFORE_VBC_AND_SOLVER' in p.read_text(),'HARD_STOP')
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'assembly_only.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe
def rel(x,y): return float(np.max(abs(x-y))/max(float(np.max(abs(y))),1e-300))
def audit(work,p,q):
    old=p/'native_diorite2'
    A0=sparse.load_npz(old/'GLOBAL_PRE_BC_CSR.npz').tocsr()
    need(A0.shape==(g23.N,g23.N) and A0.nnz==g23.NNZ and A0.has_canonical_format,'G23_STRUCTURE')
    with (work/'G18_GRAPH.dat').open() as f:
        need(f.readline().split()==[str(g23.N),str(g23.NNZ)],'GRAPH_HEADER')
        raw=np.loadtxt(f,dtype=np.int64)
    need(np.array_equal(raw,np.r_[A0.indptr+1,A0.indices+1]),'G23_GRAPH')
    A,b=g23.read_csr(work,A0)
    with np.load(old/'GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:
        G=d['rotation_candidates']; xyz=d['native_xyz']; b0=d['rhs']; f0=d['fixed_load']
    with np.load(q/'G29_CANDIDATE_FIXED_COMPONENTS.npz',allow_pickle=False) as d:
        expected=d['full']; need(list(d['labels'])==list(g25.LABELS),'G29_LABELS')
    x=np.loadtxt(work/'G23_NATIVE_LOAD.dat')
    need(x.shape==(g25.N,5) and np.array_equal(x[:,0],np.arange(1,g25.N+1))
         and np.isfinite(x).all() and np.all(x[:,1:3]==0),'ZERO_VELOCITY')
    fixed=x[:,3:5].ravel()
    need(np.array_equal(b0,f0) and np.array_equal(b,fixed),'RHS_FIXED_IDENTITY')
    exact=bool(np.array_equal(A.indptr,A0.indptr) and np.array_equal(A.indices,A0.indices)
               and np.array_equal(A.data,A0.data))
    need(A.has_canonical_format and A.nnz==g23.NNZ,'CSR_STRUCTURE')
    scale=float(np.max(np.asarray(abs(A0).sum(axis=1))))
    matrix_err=float(np.max(np.asarray(abs(A-A0).sum(axis=1)))/scale)
    err=rel(b,expected)
    R=float(read(old/'CONDITIONAL_CONTROLS.json')['radius'])
    torque=G.T@b; oldtorque=G.T@b0
    sparse.save_npz(work/'GLOBAL_PRE_BC_CSR.npz',A)
    np.savez_compressed(work/'GLOBAL_PRE_BC_FIELDS.npz',rhs=b,fixed_load=fixed,rotation_candidates=G,native_xyz=xyz)
    return {'matrix_exact':exact,'matrix_relative_inf':matrix_err,'rhs_vs_G29_relative_inf':err,
        'rhs_fixed_exact':True,'rhs_relative_change_l2':float(np.linalg.norm(b-b0)/np.linalg.norm(b0)),
        'rotation_right_scaled':[float(np.max(abs(v))/scale) for v in (A@G).T],
        'rotation_left_scaled':[float(np.max(abs(v))/scale) for v in (A.T@G).T],
        'old_torque_Nm':(R*oldtorque).tolist(),'corrected_torque_Nm':(R*torque).tolist(),
        'torque_norm_ratio':float(np.linalg.norm(torque)/np.linalg.norm(oldtorque)),
        'corrected_rhs':g25.metric(b,G),'global_rank_formally_proven':False,
        'screen_pass':bool(exact and err<=1e-12)}
def torque_budget(work,q,out):
    # Recompute the G27 diagnostic using the corrected load. No added RHS
    # is exported or applied; the 3x3 restriction is not a mantle PDE.
    with np.load(work/'GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:
        G=d['rotation_candidates']; xyz=d['native_xyz']; b=d['rhs']
    R=float(read(work/'CONDITIONAL_CONTROLS.json')['radius'])
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    need(len(f)==g26.Q and np.isfinite(f['v']).all(),'QUADRATURE')
    ids=f['ids']; v=f['v']
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,g26.E+1),7))
         and np.array_equal(ids[:,1],np.repeat(np.arange(1,8),g26.E)),'IP_ORDER')
    nodes=ids[:,2:].astype(np.int64)-1
    need(nodes.min()>=0 and nodes.max()<g25.N,'NODE_RANGE')
    pos=np.einsum('qj,qji->qi',v[:,4:7],xyz[nodes])
    st=np.hypot(pos[:,0],pos[:,1])/np.linalg.norm(pos,axis=1)
    need(np.all(st>0),'POLE')
    w=v[:,0]*R; need(np.all(w>0) and abs(w.sum()/(4*np.pi*R**2)-1)<1e-8,'AREA')
    phi=v[:,7:].reshape(g26.Q,3,2,2).transpose(0,1,3,2)
    H=np.einsum('qnab,qnac->qbc',phi,G.reshape(g25.N,2,3)[nodes])
    normal=-v[:,1,None]*np.column_stack((v[:,2],v[:,3]/st))/R
    def projection(t): return np.einsum('q,qba,qb->a',w,H,t)
    target=G.T@b; tnormal=projection(normal)
    need(np.linalg.norm(tnormal-target)/np.linalg.norm(target)<1e-10,'CORRECTED_FB2_VIRTUAL_WORK')
    K=np.einsum('q,qba,qbc->ac',w,H,H); K=(K+K.T)*.5
    ev=np.linalg.eigvalsh(K); need(ev[0]>0,'DRAG_GRAM')
    c=np.linalg.solve(K,target); shear=-np.einsum('qba,a->qb',H,c)
    tshear=projection(shear)
    loc=w[:,None,None]*np.einsum('qnab,qb->qna',phi,shear)
    force=np.zeros((g25.N,2)); np.add.at(force,nodes.ravel(),loc.reshape(-1,2))
    residual=G.T@(b+force.ravel()); relative=float(np.linalg.norm(residual)/np.linalg.norm(target))
    workerr=float(np.linalg.norm(tshear-G.T@force.ravel())/np.linalg.norm(target))
    scenarios=[]
    for kap in g27.KAPPAS:
        u=c/kap; vel=np.einsum('qba,a->qb',H,u)
        diss=float(np.einsum('q,qb,qb->',w,vel,vel)*kap); conjugate=float(-u@tshear)
        scenarios.append({'kappa_Pa_s_per_m':kap,'relative_speed_cm_yr':g27.qstats(vel*g27.YEAR*100,w),
            'dissipation_W':diss,'work_relative_error':abs(diss-conjugate)/max(diss,1e-300)})
    need(relative<1e-12 and workerr<1e-12 and all(s['dissipation_W']>0 and s['work_relative_error']<1e-12 for s in scenarios),'DRAG_DIAGNOSTIC')
    return {'corrected_normal_traction_Pa':g27.qstats(normal,w),'conditional_shear_traction_Pa':g27.qstats(shear,w),
        'drag_gram_eigenvalues_m2':ev.tolist(),'conditional_residual_relative_l2':relative,
        'virtual_work_relative_error':workerr,'conditional_drag_scenarios':scenarios,
        'diagnostic_3x3_systems':1,'physical_mantle_authority':False,'traction_applied':False}
def main():
    ap=argparse.ArgumentParser()
    for k in ('g23','g24','g26','g29','g31','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-corrected-global-assembly-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,h,q,r,s,out=(x.resolve() for x in (a.g23,a.g24,a.g26,a.g29,a.g31,a.output))
    parents=((p,lambda x:g25.verify(x,0)),(h,lambda x:g25.verify(x,1)),(q,g27.verify),
             (r,lambda x:verify(x,P29,S29)),(s,lambda x:verify(x,P31,S31)))
    before=[fn(x) for x,fn in parents]
    need(before[1]['G23_manifest_sha256']==g25.PINS[0] and before[3]['G28_manifest_sha256']==g29.PIN
         and before[4]['G30_manifest_sha256']==P30,'LINEAGE')
    need(read(h/'G24_REPORT.json')['screen_pass'] and read(s/'G31_REPORT.json')['screen_pass'],'PARENT_SCREEN')
    need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,h,q,r,s)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G24_manifest_sha256':g25.PINS[1],
        'G26_manifest_sha256':g27.PIN,'G29_manifest_sha256':P29,'G31_manifest_sha256':P31,
        'additional_builds':0,'native_assemblies_attempted':0,'additional_global_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'active_source_modified':False,
        'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        print('G32_BUILD_CORRECTED_GLOBAL_CSR',flush=True)
        exe=build(p/'build',out/'build'); report['additional_builds']=1
        old=p/'native_diorite2'; work=out/'native_diorite2'; work.mkdir()
        for n in DECK: shutil.copyfile(old/n,work/n)
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        print('G32_NATIVE_GLOBAL_ASSEMBLY_ONLY',flush=True)
        report['native_assemblies_attempted']=1
        rc=g23.run(exe,work,env); report['native_exit']=rc
        log=(work/'run.log').read_text()
        need(rc==0 and 'G23_STOP_AFTER_GLOBAL_CSR_BEFORE_VBC_AND_SOLVER' in log
             and 'G23_NATIVE_READY' in log and 'G18_CSR_ALLOC' in log
             and not (work/'FatalError.txt').exists(),'NATIVE_STOP')
        need(all(sha(work/n)==sha(old/n) for n in DECK),'DECK_MUTATION')
        need(sha(work/'G23_NATIVE_GEOMETRY.dat')==sha(old/'G23_NATIVE_GEOMETRY.dat'),'GEOMETRY')
        report['audit']=audit(work,p,r)
        need(report['audit']['screen_pass'],'CORRECTED_GLOBAL_PARITY')
        print('G32_GLOBAL_MATRIX_EXACT__RHS_PARITY_PASS',flush=True)
        report['torque_budget']=torque_budget(work,q,out)
        report.update(screen_pass=True,status='G32_CORRECTED_GLOBAL_OPERATOR_PASS__PHYSICAL_CLOSURE_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G32_CORRECTED_GLOBAL_OPERATOR_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G32_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
        'G23_manifest_sha256':g25.PINS[0],'G24_manifest_sha256':g25.PINS[1],
        'G26_manifest_sha256':g27.PIN,'G29_manifest_sha256':P29,'G31_manifest_sha256':P31,
        'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G32_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
