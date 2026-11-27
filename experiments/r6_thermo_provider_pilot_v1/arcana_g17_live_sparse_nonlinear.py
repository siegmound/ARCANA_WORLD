#!/usr/bin/env python3
"""G17 live sparse nonlinear bridge on G15 accepted endpoint, no time advance.
Native assembly remains banded. Replace DGBSV by persistent SuperLU worker
using committed iteration dumps and atomic response files. Regional only.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import numpy as np
from scipy import sparse
from scipy.sparse import linalg as sl
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g10b_consumer_resolve as b10
import arcana_g11_adaptive_pilot as g11
import arcana_g16_scale_sparse_bridge as g16

G16_PIN='4c2d63744871ed84b0e1f3e6f30a12dbd6aebc0b7ab7c5359c9ecd3513356d0a'
G16_STATUS='G16_SPARSE_LINEAR_BRIDGE_AND_SCALE_AUDIT_PASS__GLOBAL_ASSEMBLY_REQUIRED'
LIMIT=1e-12
FIELD_LIMIT=1e-10

def patch(s):
    start=s.index('SUBROUTINE Solver ('); end=s.index('END SUBROUTINE Solver',start)
    part=s[start:end]
    part=a.replace1(part,'IMPLICIT NONE','''USE, INTRINSIC :: ISO_C_BINDING, ONLY: C_INT
IMPLICIT NONE
INTERFACE
  INTEGER(C_INT) FUNCTION g17_usleep(usec) BIND(C,NAME="usleep")
    IMPORT C_INT
    INTEGER(C_INT), VALUE :: usec
  END FUNCTION g17_usleep
END INTERFACE''')
    part=a.replace1(part,'INTEGER info, kl, ku, ldab, ldb, n, nrhs','''INTEGER info, kl, ku, ldab, ldb, n, nrhs
INTEGER, SAVE :: g17_iter=0
INTEGER :: g17_u,g17_io,g17_j,g17_id,g17_wait,g17_sleep
CHARACTER(40) :: g17_prefix
LOGICAL :: g17_ready,g17_failed''')
    part=a.replace1(part,'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )','''! C11B FEM has closed the matching post-BC dump before calling Solver.
IF(n/=162 .OR. nrhs/=1) STOP 97
g17_iter=g17_iter+1
WRITE(g17_prefix,'(A,I3.3)') 'iter_',g17_iter
OPEN(NEWUNIT=g17_u,file=TRIM(g17_prefix)//'_sparse_request',status='new',iostat=g17_io)
IF(g17_io/=0) STOP 97
CLOSE(g17_u)
DO g17_wait=1,10000
  INQUIRE(file='G17_WORKER_FAILED',exist=g17_failed)
  IF(g17_failed) STOP 97
  INQUIRE(file=TRIM(g17_prefix)//'_sparse_response.dat',exist=g17_ready)
  IF(g17_ready) EXIT
  g17_sleep=g17_usleep(1000_C_INT)
END DO
IF(.NOT.g17_ready) STOP 97
OPEN(NEWUNIT=g17_u,file=TRIM(g17_prefix)//'_sparse_response.dat',status='old',action='read',iostat=g17_io)
IF(g17_io/=0) STOP 97
DO g17_j=1,n
  READ(g17_u,*,iostat=g17_io) g17_id,b(g17_j,1)
  IF(g17_io/=0 .OR. g17_id/=g17_j) STOP 97
END DO
CLOSE(g17_u)
info=0
PRINT '(A,I6)','G17_SPARSE_SOLVED ',g17_iter''')
    return s[:start]+part+s[end:]

def read_sparse(path):
    # Decode the actual native post-BC band, without materializing dense A.
    with path.open() as f:
        n,nr,d,kl,ku,nd=map(int,f.readline().split()); raw=np.loadtxt(f)
    a.need((n,nr,d,kl,ku,nd)==(162,64,43,21,21,162),'HEADER')
    a.need(raw.shape==(n,nr+2) and np.array_equal(raw[:,0],np.arange(1,n+1))
        and np.isfinite(raw).all(),'BAND_INVENTORY')
    j,k=np.nonzero(raw[:,2:])
    i=j+k-(d-1)
    # LAPACK work slots outside the physical band must not enter operator.
    mask=(i>=0)&(i<n)&(i-j<=kl)&(j-i<=ku)
    mat=sparse.coo_matrix((raw[j[mask],k[mask]+2],(i[mask],j[mask])),shape=(n,n)).tocsc()
    return mat,raw[:,1]

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'matrix.dat'
        A=np.zeros((162,162)); np.fill_diagonal(A,4.)
        A[np.arange(161),np.arange(1,162)]=-1.; A[np.arange(1,162),np.arange(161)]=2.
        raw=np.zeros((162,66)); raw[:,0]=np.arange(1,163); raw[:,1]=np.arange(162)
        i,j=np.nonzero(A); raw[j,2+42+i-j]=A[i,j]
        with p.open('w') as f:
            f.write('162 64 43 21 21 162\n'); np.savetxt(f,raw)
        B,b=read_sparse(p)
        a.need(np.array_equal(A,B.toarray()) and np.array_equal(b,raw[:,1]),'BAND_FIXTURE')
        x=sl.splu(B).solve(b)
        a.need(g16.backward(B,x,b)<=LIMIT and g16.relative(x,np.linalg.solve(A,b))<=FIELD_LIMIT,'SOLVE_FIXTURE')
    print('G17_SPARSE_CODEC_SELFTEST_PASS',flush=True)

def worker(work):
    try:
        with (work/'G17_WORKER.jsonl').open('x') as log:
            j=1; deadline=time.monotonic()+120
            while j<=g7.MAX_ITER+1:
                prefix=f'iter_{j:03d}'
                req=work/(prefix+'_sparse_request')
                if not req.exists():
                    if (work/'C11B_FINAL_REQUEST').exists(): return 0
                    if time.monotonic()>deadline: raise RuntimeError('WORKER_TIMEOUT')
                    time.sleep(.001); continue
                a.need(j<=g7.MAX_ITER,'ITERATION_BUDGET')
                t=time.perf_counter()
                A,b=read_sparse(work/(prefix+'_post.dat'))
                lu=sl.splu(A,permc_spec='COLAMD')
                x=lu.solve(b)
                residual=g16.backward(A,x,b)
                a.need(np.isfinite(x).all() and residual<=LIMIT,'SPARSE_BACKWARD')
                temp=work/(prefix+'_sparse_tmp')
                with temp.open('x') as f:
                    for i,v in enumerate(x,1): f.write(f'{i} {v:.17e}\n')
                os.replace(temp,work/(prefix+'_sparse_response.dat'))
                log.write(json.dumps({'iteration':j,'nnz':A.nnz,'lu_nnz':lu.L.nnz+lu.U.nnz,
                    'backward':residual,'seconds_including_io':time.perf_counter()-t})+'\n')
                log.flush(); j+=1
        raise RuntimeError('WORKER_ITERATION_LIMIT')
    except Exception:
        (work/'G17_WORKER_FAILED').write_text(traceback.format_exc())
        return 2

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--worker',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--authorize-live-sparse-bridge',choices=[a.SCENARIO])
    args=ap.parse_args()
    if args.worker is not None: return worker(args.worker)
    a.need(args.output is not None and args.authorize_live_sparse_bridge==a.SCENARIO,'AUTHORIZATION')
    g8.check_helpers(); selftest()
    a.need(g7.blob(Path(__file__).with_name('arcana_g16_scale_sparse_bridge.py'))==
        'f39258ad725847e885ba44c8af188a42d74f10ce','G16_HELPER')
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g16','R6_THERMO_G16_SCALE_SPARSE_BRIDGE_NEW01',G16_PIN,G16_STATUS),
        ('g15','R6_THERMO_G15_MIDPOINT_COUPLING_NEW01',g16.G15_PIN,g16.G15_STATUS),
        ('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',g11.B_PIN,g11.B_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g15']; prior=a.read(p/'G15_REPORT.json'); audit=a.read(parents['g16']/'G16_REPORT.json')
    a.need(audit['screen_pass'] and manifests['g16']['G15_manifest_sha256']==g16.G15_PIN and
        prior['screen_pass'] and prior['accepted_checkpoint_sha256']==g16.CP_PIN,'SOURCE_LINEAGE')
    cp=p/prior['accepted_checkpoint']; g11.load(cp,g16.CP_PIN)
    src=cp.parent/'corrector_mechanics'
    # Accepted checkpoint is next to corrector_mechanics, not its parent trial.
    a.need(g8.same_npz(cp/'mechanical.npz',src/'ultra/C11B_FINAL_STATE.npz'),'MECHANICAL_LINEAGE')
    for n in (*g7.DECK,'regional.in',b10.SIDE):
        a.need(a.sha(cp/n)==a.sha(src/'ultra'/n),'DECK:'+n)
    build=parents['b']/'solve_build'; g8.binary(build,'solve.exe',native)
    ctl=dict(a.read(cp/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
    a.need((cp/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G16_manifest':G16_PIN,'G15_checkpoint':g16.CP_PIN,
        'runner_sha256':a.sha(Path(__file__)),'linear_backward_limit':LIMIT,'field_relative_limit':FIELD_LIMIT,
        'scope':'Regional full native nonlinear replay; band assembly retained, SuperLU only linear solve.',
        **c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'additional_builds':0,'native_nonlinear_solves_attempted':0,
        'additional_time_advance_years':0,'physical_acceptance':False,**c.SCOPE}
    try:
        print('G17_BUILD',flush=True)
        dest=out/'build'
        exe=g7.build(dest,root,native,(build/'SHELLS_g7.f90').read_text(),
            patch((build/'MOD_Shells.f90').read_text()),(build/'driver.f90').read_text(),
            False,env,build/'MOD_ArcanaRuntime.f90')
        old=a.read(build/'BUILD_IDENTITY.json')['source_sha256']; new=a.read(dest/'BUILD_IDENTITY.json')['source_sha256']
        a.need(set(old)==set(new) and all(old[k]==new[k] for k in old if k!='MOD_Shells.f90')
            and old['MOD_Shells.f90']!=new['MOD_Shells.f90'],'BUILD_DRIFT')
        report['additional_builds']=1
        ref=out/'reference'; ref.mkdir()
        shutil.copyfile(src/'reference/C11_MATRICES.npz',ref/'C11_MATRICES.npz')
        view=out/g7.C10_NAME; view.mkdir()
        shutil.copyfile(src/g7.C10_NAME/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',view/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
        work=out/'ultra'; b10.stage(work,cp,cp,native,ctl)
        print('G17_NATIVE_NONLINEAR_SPARSE_REPLAY',flush=True)
        report['native_nonlinear_solves_attempted']=1
        with (out/'worker.log').open('x') as log:
            w=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(work)],
                env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=a.limit)
            try:
                rc,nlog=g7.run(exe,work,env)
                if rc==0: wrc=w.wait(timeout=5)
                else: wrc=None
            finally:
                if w.poll() is None: w.terminate(); w.wait(timeout=5)
        report.update(native_exit=rc,worker_exit=wrc)
        a.need(rc==wrc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in nlog and
            not (work/'G17_WORKER_FAILED').exists(),'NATIVE_OR_WORKER_FAILURE')
        g7.controls_readback(nlog,ctl)
        r1.MAX_ITER=g7.MAX_ITER; r1.NATIVE_TOL=g8.ULTRA
        ar=r1.analysis(work,ref,a); a.write(work/'MECHANICAL_ANALYSIS.json',ar)
        records=[json.loads(x) for x in (work/'G17_WORKER.jsonl').read_text().splitlines()]
        n=len(ar['iterations'])
        a.need(len(records)==n and [v['iteration'] for v in records]==list(range(1,n+1))
            and nlog.count('G17_SPARSE_SOLVED ')==n and len(list(work.glob('iter_*_sparse_response.dat')))==n,'WORKER_COVERAGE')
        for j in range(1,n+1):
            ans=r1.load_vector(work/f'iter_{j:03d}_sparse_response.dat',a)
            actual=r1.load_vector(work/f'iter_{j:03d}_solution.dat',a)
            a.need(np.array_equal(ans,actual),'WORKER_SOLUTION_READBACK')
        fields={}
        with np.load(cp/'mechanical.npz') as x,np.load(work/'C11B_FINAL_STATE.npz') as y:
            for f in g7.FIELDS:
                d=g16.relative(x[f],y[f]); fields[f]={'relative_difference':d,'screen_pass':d<=FIELD_LIMIT}
        report['native_mechanics']={'iterations':n,'native_scoreB':ar['native_final_scoreB'],
            'residual':ar['final_free_relative_residual'],'work_defect':ar['work_balance_relative_defect'],
            'stress_refresh':ar['stress_refresh_relative_max_component'],'power_W':ar['quadrature_power_W'],
            'max_linear_backward':max(x['linear_backward_error'] for x in ar['iterations'])}
        report['worker']={'iterations':n,'max_backward':max(x['backward'] for x in records),
            'max_lu_nnz':max(x['lu_nnz'] for x in records),'summed_worker_seconds_including_io':sum(x['seconds_including_io'] for x in records)}
        report['fields']=fields
        report['screen_pass']=bool(ar['screen_pass'] and max(report['native_mechanics'][k] for k in ('residual','work_defect','stress_refresh'))<=g7.FINE_SCREEN
            and report['worker']['max_backward']<=LIMIT and all(x['screen_pass'] for x in fields.values()))
    except Exception as exc:
        report['screen_pass']=False
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin,'PARENT_MUTATION')
    status='G17_LIVE_SPARSE_NONLINEAR_REPLAY_PASS__NATIVE_SPARSE_ASSEMBLY_REQUIRED' if report['screen_pass'] else 'G17_LIVE_SPARSE_NONLINEAR_REPLAY_BLOCKED'
    report.update(status=status,limitations=[
        'One regional nonlinear replay, original band storage and textual instrumentation retained.',
        'Persistent worker is an engineering bridge, not a production HPC interface; no speedup claim.',
        'No actual global stiffness assembly, global gauge, material admission, exterior or event transition.',
        'No new temporal advancement, physical T1 or scientific promotion.'])
    a.write(out/'G17_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G16_manifest_sha256':G16_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G17_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True); print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
