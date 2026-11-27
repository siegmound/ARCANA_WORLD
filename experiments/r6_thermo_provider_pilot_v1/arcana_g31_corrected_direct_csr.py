#!/usr/bin/env python3
"""G31: direct CSR regression against corrected band assembly G30.
Same regional state and controls; no global solve, time advance or promotion.
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
import arcana_g18_direct_csr as g18
import arcana_g30_regional_metric_regression as g30

a,r1,g7,g8,g17,g16=g18.a,g18.r1,g18.g7,g18.g8,g18.g17,g18.g16
need,sha,read,write,inventory=g30.need,g30.sha,g30.read,g30.write,g30.inventory
SOURCE,SCOPE=g30.SOURCE,g30.SCOPE
PIN='3298f0b7ef41083068ada52e71d62a0238a96076372625cc8fa42dd210d7cee2'
STATUS='G30_REGIONAL_METRIC_REGRESSION_PASS__TRAJECTORY_AND_GLOBAL_CLOSURE_REQUIRED'
AUTH='G31_CORRECTED_DIRECT_CSR_REGRESSION_ONLY_V1'
FIELD_LIMIT=1e-10
def verify(p):
    m=g30.verify(p,PIN,STATUS)
    need(m['G17_manifest_sha256']==g30.P17 and m['G29_manifest_sha256']==g30.P29,'G30_LINEAGE')
    need(read(p/'G30_REPORT.json')['screen_pass'],'G30_SCREEN')
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
    for n,fn in [('MOD_Shells.f90',g18.patch),('SHELLS_g7.f90',g18.patch_entry)]:
        p=new/n; p.write_text(fn(p.read_text()))
    need(set(n for n,pin in meta['source_sha256'].items() if sha(new/n)!=pin)==
         {'MOD_Shells.f90','SHELLS_g7.f90'},'PATCH_SCOPE')
    need('slopey = slopey + zA * dYSP(j, m, i) / sinA' in (new/'MOD_Shells.f90').read_text(),'METRIC_LOST')
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'solve.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe
def audit(p,out,work,nlog):
    old=p/'ultra'
    ref=out/'reference'; ref.mkdir()
    shutil.copyfile(p/'reference/C11_MATRICES.npz',ref/'C11_MATRICES.npz')
    view=out/g7.C10_NAME; view.mkdir()
    shutil.copyfile(p/g7.C10_NAME/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',view/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    need(np.array_equal(np.loadtxt(work/'G18_GRAPH_READBACK.dat',dtype=int),
                        np.loadtxt(work/'G18_GRAPH.dat',dtype=int,skiprows=1)),'GRAPH_READBACK')
    need(nlog.count('G18_CSR_ALLOC ')==1,'CSR_ALLOC_RECEIPT')
    band=a.matrix
    r1.MAX_ITER=g7.MAX_ITER; r1.NATIVE_TOL=g8.ULTRA
    a.matrix=g18.dense_for_audit
    try: ar=r1.analysis(work,ref,a)
    finally: a.matrix=band
    write(work/'MECHANICAL_ANALYSIS.json',ar)
    n=len(ar['iterations'])
    records=[json.loads(x) for x in (work/'G17_WORKER.jsonl').read_text().splitlines()]
    expected=list(range(1,n+1))
    need([x['iteration'] for x in records]==expected,'WORKER_ORDER')
    for suffix in ('_pre.dat','_post.dat','_solution.dat','_sparse_request','_sparse_response.dat'):
        need(sorted(x.name for x in work.glob('iter_*'+suffix))==
             [f'iter_{j:03d}'+suffix for j in expected],'ITERATION_COVERAGE:'+suffix)
    for j in expected:
        prefix=f'iter_{j:03d}'
        x=r1.load_vector(work/(prefix+'_sparse_response.dat'),a)
        y=r1.load_vector(work/(prefix+'_solution.dat'),a)
        need(np.array_equal(x,y),'WORKER_READBACK')
        A,b=g18.read_sparse(work/(prefix+'_post.dat'))
        need(g16.backward(A,y,b)<=g17.LIMIT,'INDEPENDENT_BACKWARD')
    parity=g18.assembly_parity(work,old,band)
    oldn=len(list(old.glob('iter_*_solution.dat')))
    solmax=0.
    for j in range(1,min(n,oldn)+1):
        name=f'iter_{j:03d}_solution.dat'
        solmax=max(solmax,g16.relative(r1.load_vector(work/name,a),r1.load_vector(old/name,a)))
    with np.load(old/'C11B_FINAL_STATE.npz',allow_pickle=False) as x,np.load(work/'C11B_FINAL_STATE.npz',allow_pickle=False) as y:
        fields={k:g30.metrics(x[k],y[k]) for k in g7.FIELDS}
    oldnodes=np.loadtxt(old/'final_nodes.dat'); newnodes=np.loadtxt(work/'final_nodes.dat')
    fixed_exact=bool(np.array_equal(oldnodes[:,3:5],newnodes[:,3:5]))
    native={'iterations':n,'native_scoreB':ar['native_final_scoreB'],
        'residual':ar['final_free_relative_residual'],'work_defect':ar['work_balance_relative_defect'],
        'stress_refresh':ar['stress_refresh_relative_max_component'],'power_W':ar['quadrature_power_W'],
        'max_linear_backward':max(x['linear_backward_error'] for x in ar['iterations']),
        'worker_max_backward':max(x['backward'] for x in records)}
    screen=bool(ar['screen_pass'] and max(native[k] for k in ('residual','work_defect','stress_refresh'))<=g7.FINE_SCREEN
        and native['worker_max_backward']<=g17.LIMIT and parity['screen_pass'] and fixed_exact
        and n==oldn==parity['matched_iterations'] and solmax<=FIELD_LIMIT
        and all(v['relative_change_inf']<=FIELD_LIMIT for v in fields.values()))
    return {'candidate_mechanics':native,'band_mechanics':read(p/'G30_REPORT.json')['audit']['candidate_mechanics'],
        'assembly_parity':parity,'max_matched_solution_relative_inf':solmax,'fields':fields,
        'fixed_load_exact':fixed_exact,'worker_records':len(records),'band_iterations':oldn,
        'worker_artifact_coverage_complete':True,'text_marker_count':nlog.count('G17_SPARSE_SOLVED '),
        'historical_G18_documentary_block_closed':False,'screen_pass':screen}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--worker',type=Path)
    ap.add_argument('--g30',type=Path); ap.add_argument('--output',type=Path)
    ap.add_argument('--authorize-corrected-csr-only',choices=[AUTH])
    args=ap.parse_args()
    if args.worker is not None:
        g17.read_sparse=g18.read_sparse
        return g17.worker(args.worker)
    need(args.g30 is not None and args.output is not None and args.authorize_corrected_csr_only==AUTH,'AUTH')
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,out=(x.resolve() for x in (args.g30,args.output))
    pm=verify(p)
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G30_manifest_sha256':PIN,'additional_builds':0,
        'regional_nonlinear_solves_attempted':0,'additional_global_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'active_source_modified':False,
        'physical_acceptance':False,'global_solve_authorized':False,**SCOPE}
    try:
        g18.selftest()
        print('G31_BUILD_CORRECTED_CSR',flush=True)
        exe=build(p/'build',out/'build'); report['additional_builds']=1
        work=out/'ultra'; work.mkdir()
        for n in g30.DECK: shutil.copyfile(p/'ultra'/n,work/n)
        graph=g18.stage_graph(work)
        report['structure']={'n':graph.shape[0],'nnz':graph.nnz,
            'csr_bytes':int(12*graph.nnz+4*(graph.shape[0]+1)),'legacy_dummy_bytes':8}
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        print('G31_CORRECTED_CSR_REGRESSION',flush=True)
        report['regional_nonlinear_solves_attempted']=1
        with (out/'worker.log').open('x') as log:
            w=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(work)],
                env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=a.limit)
            try:
                rc,nlog=g7.run(exe,work,env)
                wrc=w.wait(timeout=5) if rc==0 else None
            finally:
                if w.poll() is None: w.terminate(); w.wait(timeout=5)
        report.update(native_exit=rc,worker_exit=wrc)
        need(rc==wrc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in nlog
             and not (work/'G17_WORKER_FAILED').exists() and not (work/'FatalError.txt').exists(),'NATIVE_OR_WORKER')
        need(all(sha(work/n)==sha(p/'ultra'/n) for n in g30.DECK),'DECK_MUTATION')
        controls=lambda log:[l.split() for l in log.splitlines() if l.startswith('G7_CONTROLS ')]
        need(len(controls(nlog))==1 and controls(nlog)==controls((p/'ultra/run.log').read_text()),'CONTROL_REPLAY')
        report['audit']=audit(p,out,work,nlog); report['screen_pass']=report['audit']['screen_pass']
        report['status']=('G31_CORRECTED_DIRECT_CSR_PARITY_PASS__TRAJECTORY_AND_GLOBAL_CLOSURE_REQUIRED'
                          if report['screen_pass'] else 'G31_CORRECTED_DIRECT_CSR_RETAINED__PARITY_REVIEW')
    except Exception as e:
        report.update(screen_pass=False,status='G31_CORRECTED_DIRECT_CSR_BLOCKED',
                      error=repr(e),traceback=traceback.format_exc())
    need(verify(p)==pm,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G31_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
         'G30_manifest_sha256':PIN,'runner_sha256':sha(Path(__file__)),
         'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G31_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
