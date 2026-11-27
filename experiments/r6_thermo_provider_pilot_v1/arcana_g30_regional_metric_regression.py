#!/usr/bin/env python3
"""G30: regional nonlinear metric regression on the retained G17 endpoint.
Exactly one candidate solve, no global solve, time advance or checkpoint promotion.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import numpy as np
import arcana_g17_live_sparse_nonlinear as g17
import arcana_g29_native_metric_candidate as g29
import arcana_g25_fixed_load_decomposition as g25

a,r1,g7,g8,b10=g17.a,g17.r1,g17.g7,g17.g8,g17.b10
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
P17='0cb0b2610ebeecc78747e2fc89235018f618d44432e3f25d893ed6e7c9f928d1'
P29='fb2ce020ba500e231032696311face81f94298e6ad606608c18f8d76083d2149'
S17='G17_LIVE_SPARSE_NONLINEAR_REPLAY_PASS__NATIVE_SPARSE_ASSEMBLY_REQUIRED'
S29='G29_NATIVE_GLOBAL_METRIC_PARITY_PASS__REGIONAL_AND_TORQUE_REVIEW_REQUIRED'
AUTH='G30_REGIONAL_METRIC_REGRESSION_ONLY_V1'
DECK=(*g7.DECK,'regional.in',b10.SIDE)
def verify(p,pin,status):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==pin and m['status']==status and m['source_sha']==SOURCE
         and all(m[k]==v for k,v in SCOPE.items()),'PARENT_PIN_SCOPE:'+p.name)
    need(inventory(p)==m['files'],'PARENT_INVENTORY:'+p.name)
    return m
def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json'); argv=meta['argv']
    need(argv[-2:]==['-o','solve.exe'] and all(x in argv for x in ('-O0','-Mbounds','-Kieee')),'BUILD_FLAGS')
    need(sha(old/'solve.exe')==meta['exe_sha256'] and sha(Path(argv[0]))==meta['compiler_sha256'],'COMPILER_OR_EXE')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for n,pin in meta['library_sha256'].items(): need(sha(libs[0]/n)==pin,'LIB_DRIFT:'+n)
    new.mkdir()
    for n,pin in meta['source_sha256'].items():
        need(Path(n).name==n and sha(old/n)==pin,'SOURCE_DRIFT:'+n)
        shutil.copyfile(old/n,new/n)
    p=new/'MOD_Shells.f90'; p.write_text(g29.patch_fixed(p.read_text()))
    need([n for n,pin in meta['source_sha256'].items() if sha(new/n)!=pin]==['MOD_Shells.f90'],'PATCH_SCOPE')
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'solve.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe
def rel(x,y): return float(np.max(abs(x-y))/max(float(np.max(abs(y))),1e-300))
def metrics(x,y):
    return {'original_l2':float(np.linalg.norm(x)),'candidate_l2':float(np.linalg.norm(y)),
        'relative_change_l2':float(np.linalg.norm(y-x)/max(float(np.linalg.norm(x)),1e-300)),
        'relative_change_inf':rel(y,x),'exact':bool(np.array_equal(x,y))}
def audit(p,out,work):
    old=p/'ultra'
    ref=out/'reference'; ref.mkdir()
    view=out/g7.C10_NAME; view.mkdir()
    shutil.copyfile(p/g7.C10_NAME/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',view/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    with np.load(p/'reference/C11_MATRICES.npz',allow_pickle=False) as d:
        held=d['held']; free=d['free']; target=d['target']
        refold={k:d[k] for k in ('A_pre','A_post','b_pre','b_post')}
    A,b=a.matrix(old/'iter_001_pre.dat'); B,c=a.matrix(old/'iter_001_post.dat')
    X,y=a.matrix(work/'iter_001_pre.dat'); Y,z=a.matrix(work/'iter_001_post.dat')
    need(max(rel(x,refold[k]) for x,k in ((A,'A_pre'),(B,'A_post'),(b,'b_pre'),(c,'b_post')))<1e-12,'OLD_FIRST_REFERENCE')
    oldnodes=np.loadtxt(old/'final_nodes.dat'); newnodes=np.loadtxt(work/'final_nodes.dat')
    need(oldnodes.shape==newnodes.shape==(81,5) and np.array_equal(oldnodes[:,0],newnodes[:,0]),'NODE_ORDER')
    delta=(newnodes[:,3:5]-oldnodes[:,3:5]).ravel()
    expected_b=b+delta; expected_c=c.copy(); expected_c[free]+=delta[free]
    first={'A_pre_relative_inf':rel(X,A),'A_post_relative_inf':rel(Y,B),
        'rhs_pre_delta_replay_relative_inf':rel(y,expected_b),
        'rhs_post_delta_replay_relative_inf':rel(z,expected_c),
        'held_rhs_exact':bool(np.array_equal(z[held],c[held])),
        'fixed_load':metrics(oldnodes[:,3:5],newnodes[:,3:5])}
    need(max(first[k] for k in ('A_pre_relative_inf','A_post_relative_inf',
        'rhs_pre_delta_replay_relative_inf','rhs_post_delta_replay_relative_inf'))<1e-12
        and first['held_rhs_exact'],'FIRST_LINEARIZATION_SCOPE')
    # Keep the old operator and boundary targets; only the force delta is
    # derived from the newly measured native fixed load, not an independent oracle.
    np.savez(ref/'C11_MATRICES.npz',held=held,free=free,target=target,
             A_pre=A,A_post=B,b_pre=expected_b,b_post=expected_c)
    r1.MAX_ITER=g7.MAX_ITER; r1.NATIVE_TOL=g8.ULTRA
    ar=r1.analysis(work,ref,a); write(work/'MECHANICAL_ANALYSIS.json',ar)
    records=[json.loads(x) for x in (work/'G17_WORKER.jsonl').read_text().splitlines()]
    n=len(ar['iterations'])
    need(len(records)==n and [x['iteration'] for x in records]==list(range(1,n+1))
         and len(list(work.glob('iter_*_sparse_request')))==n
         and len(list(work.glob('iter_*_sparse_response.dat')))==n,'WORKER_COVERAGE')
    for j in range(1,n+1):
        x=r1.load_vector(work/f'iter_{j:03d}_sparse_response.dat',a)
        y=r1.load_vector(work/f'iter_{j:03d}_solution.dat',a)
        need(np.array_equal(x,y),'WORKER_READBACK')
    with np.load(old/'C11B_FINAL_STATE.npz',allow_pickle=False) as x,np.load(work/'C11B_FINAL_STATE.npz',allow_pickle=False) as y:
        fields={k:metrics(x[k],y[k]) for k in g7.FIELDS}
    native={'iterations':n,'native_scoreB':ar['native_final_scoreB'],
        'residual':ar['final_free_relative_residual'],'work_defect':ar['work_balance_relative_defect'],
        'stress_refresh':ar['stress_refresh_relative_max_component'],'power_W':ar['quadrature_power_W'],
        'max_linear_backward':max(x['linear_backward_error'] for x in ar['iterations']),
        'worker_max_backward':max(x['backward'] for x in records)}
    screen=bool(ar['screen_pass'] and max(native[k] for k in ('residual','work_defect','stress_refresh'))<=g7.FINE_SCREEN
        and native['worker_max_backward']<=g17.LIMIT)
    return {'first_linearization':first,'candidate_mechanics':native,'original_mechanics':read(p/'G17_REPORT.json')['native_mechanics'],
        'fields':fields,'screen_pass':screen,'first_rhs_reference_uses_measured_native_delta':True,
        'regional_case_count':1,'historical_checkpoint_promoted':False,'regional_trajectory_replayed':False}
def main():
    ap=argparse.ArgumentParser()
    for k in ('g17','g29','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-regional-regression-only',choices=[AUTH],required=True)
    args=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,out=(x.resolve() for x in (args.g17,args.g29,args.output))
    pm=verify(p,P17,S17); qm=verify(q,P29,S29)
    need(qm['G28_manifest_sha256']==g29.PIN,'G29_LINEAGE')
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,q,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G17_manifest_sha256':P17,'G29_manifest_sha256':P29,
        'additional_builds':0,'regional_nonlinear_solves_attempted':0,'additional_global_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'active_source_modified':False,
        'physical_acceptance':False,'global_solve_authorized':False,**SCOPE}
    try:
        print('G30_BUILD_REGIONAL_METRIC_CANDIDATE',flush=True)
        exe=build(p/'build',out/'build'); report['additional_builds']=1
        work=out/'ultra'; work.mkdir()
        for n in DECK: shutil.copyfile(p/'ultra'/n,work/n)
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        print('G30_REGIONAL_NONLINEAR_REGRESSION',flush=True)
        report['regional_nonlinear_solves_attempted']=1
        with (out/'worker.log').open('x') as log:
            w=subprocess.Popen([sys.executable,str(Path(g17.__file__).resolve()),'--worker',str(work)],
                env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=a.limit)
            try:
                rc,nlog=g7.run(exe,work,env)
                wrc=w.wait(timeout=5) if rc==0 else None
            finally:
                if w.poll() is None: w.terminate(); w.wait(timeout=5)
        report.update(native_exit=rc,worker_exit=wrc)
        need(rc==wrc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in nlog
             and not (work/'G17_WORKER_FAILED').exists() and not (work/'FatalError.txt').exists(),'NATIVE_OR_WORKER')
        need(all(sha(work/n)==sha(p/'ultra'/n) for n in DECK),'DECK_MUTATION')
        controls=lambda log:[l.split() for l in log.splitlines() if l.startswith('G7_CONTROLS ')]
        need(len(controls(nlog))==1 and controls(nlog)==controls((p/'ultra/run.log').read_text()),'CONTROL_REPLAY')
        report['audit']=audit(p,out,work)
        report['screen_pass']=report['audit']['screen_pass']
        report['status']=('G30_REGIONAL_METRIC_REGRESSION_PASS__TRAJECTORY_AND_GLOBAL_CLOSURE_REQUIRED'
                          if report['screen_pass'] else 'G30_REGIONAL_METRIC_REGRESSION_RETAINED__NUMERICAL_REVIEW')
    except Exception as e:
        report.update(screen_pass=False,status='G30_REGIONAL_METRIC_REGRESSION_BLOCKED',
                      error=repr(e),traceback=traceback.format_exc())
    need(verify(p,P17,S17)==pm and verify(q,P29,S29)==qm,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G30_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
         'G17_manifest_sha256':P17,'G29_manifest_sha256':P29,'runner_sha256':sha(Path(__file__)),
         'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G30_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
