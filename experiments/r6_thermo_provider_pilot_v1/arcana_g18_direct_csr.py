#!/usr/bin/env python3
"""G18: native direct CSR assembly and nonlinear parity, controlled R8.
All element coefficients and their accumulation order retained. A fixed
CSR graph is supplied from the actual FEG; no band coefficient allocation.
Regional dense audit only after completion; no global physical promotion.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
import numpy as np
from scipy import sparse
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g10b_consumer_resolve as b10
import arcana_g11_adaptive_pilot as g11
import arcana_g16_scale_sparse_bridge as g16
import arcana_g17_live_sparse_nonlinear as g17

G16_PIN=g17.G16_PIN
G16_STATUS=g17.G16_STATUS
G17_PIN='0cb0b2610ebeecc78747e2fc89235018f618d44432e3f25d893ed6e7c9f928d1'
G17_STATUS='G17_LIVE_SPARSE_NONLINEAR_REPLAY_PASS__NATIVE_SPARSE_ASSEMBLY_REQUIRED'
LIMIT=g17.LIMIT
FIELD_LIMIT=g17.FIELD_LIMIT
CSR_MODULE='''
module G18CSR
  implicit none
  private
  integer, allocatable, save :: rp(:), ci(:)
  real(8), allocatable, save :: av(:)
  public :: g18_reset,g18_add,g18_get,g18_set,g18_zero_row,g18_dump
contains
  subroutine g18_reset(n)
    integer,intent(in) :: n
    integer :: u,ios,nn,nz,i,k
    if(.not.allocated(av)) then
      open(newunit=u,file='G18_GRAPH.dat',status='old',action='read',iostat=ios)
      if(ios/=0) stop 98
      read(u,*,iostat=ios) nn,nz
      if(ios/=0) stop 98
      if(nn/=n.or.nz<n.or.nz>100*n) stop 98
      allocate(rp(n+1),ci(nz),av(nz),stat=ios)
      if(ios/=0) stop 98
      read(u,*,iostat=ios) rp
      if(ios/=0) stop 98
      read(u,*,iostat=ios) ci
      if(ios/=0) stop 98
      close(u)
      if(rp(1)/=1.or.rp(n+1)/=nz+1) stop 98
      if(any(rp<1).or.any(rp>nz+1).or.any(ci<1).or.any(ci>n)) stop 98
      do i=1,n
        if(rp(i+1)<=rp(i)) stop 98
        do k=rp(i)+1,rp(i+1)-1
          if(ci(k)<=ci(k-1)) stop 98
        end do
        if(.not.any(ci(rp(i):rp(i+1)-1)==i)) stop 98
      end do
      open(newunit=u,file='G18_GRAPH_READBACK.dat',status='new')
      do i=1,n+1
        write(u,'(I12)') rp(i)
      end do
      do i=1,nz
        write(u,'(I12)') ci(i)
      end do
      close(u)
      print '(A,3(1X,I12))','G18_CSR_ALLOC',n,nz,4*(n+1)+12*nz
    end if
    if(size(rp)/=n+1) stop 98
    av=0d0
  end subroutine

  integer function g18_slot(i,j) result(k)
    integer,intent(in) :: i,j
    integer :: t
    if(i<1.or.i>=size(rp).or.j<1.or.j>=size(rp)) stop 98
    do t=rp(i),rp(i+1)-1
      if(ci(t)==j) then
        k=t
        return
      end if
    end do
    stop 98 ! missing structural entry is never silently dropped
  end function

  subroutine g18_add(i,j,value)
    integer,intent(in) :: i,j
    real(8),intent(in) :: value
    integer :: k
    k=g18_slot(i,j)
    av(k)=av(k)+value
  end subroutine

  real(8) function g18_get(i,j)
    integer,intent(in) :: i,j
    g18_get=av(g18_slot(i,j))
  end function

  subroutine g18_set(i,j,value)
    integer,intent(in) :: i,j
    real(8),intent(in) :: value
    av(g18_slot(i,j))=value
  end subroutine

  subroutine g18_zero_row(i)
    integer,intent(in) :: i
    if(i<1.or.i>=size(rp)) stop 98
    av(rp(i):rp(i+1)-1)=0d0
  end subroutine

  subroutine g18_dump(filename,n,b)
    character(*),intent(in) :: filename
    integer,intent(in) :: n
    real(8),intent(in) :: b(n)
    integer :: u,i
    if(n/=size(rp)-1) stop 98
    open(newunit=u,file=filename,status='new',action='write')
    write(u,'(A,2(1X,I12))') 'G18_CSR_V1',n,size(av)
    do i=1,n
      write(u,'(I8,*(1X,ES26.17E3))') i,b(i),av(rp(i):rp(i+1)-1)
    end do
    close(u)
  end subroutine
end module G18CSR

'''

def patch_entry(s):
    return a.replace1(s,'ALLOCATE ( stiff(nKRows, nRank) )','ALLOCATE ( stiff(1, 1) )')

def patch(s):
    def edit(name,fn):
        nonlocal s
        i=s.index('SUBROUTINE '+name+' ('); j=s.index('END SUBROUTINE '+name,i)
        s=s[:i]+fn(s[i:j])+s[j:]
    def dummy(t,var):
        # Only actual DIMENSION lines; the legacy explanatory comments stay.
        lines=t.splitlines(keepends=True)
        n=0
        for i,line in enumerate(lines):
            if not line.lstrip().startswith('!') and var+'(nKRows, nRank)' in line:
                lines[i]=line.replace(var+'(nKRows, nRank)',var+'(1, 1)'); n+=1
        a.need(n==1,'DUMMY_DIMENSION:'+var)
        return ''.join(lines)
    def buildk(t):
        t=dummy(t,'stiff')
        t=a.replace1(t,'IMPLICIT NONE','USE G18CSR, ONLY: g18_reset,g18_add\nIMPLICIT NONE')
        t=a.replace1(t,'stiff = 0.0D0 ! whole matrix (per power of Fortran 90)','stiff = 0.0D0\nCALL g18_reset(nRank)')
        for ir,jc,ii,jj in [('irx','jcx',1,1),('irx','jcy',1,2),('iry','jcx',2,1),('iry','jcy',2,2)]:
            key=f'stiff(iq, {jc}) = stiff(iq, {jc}) + elK({ii}, {jj}, i3, j3)'
            t=a.replace1(t,key,f'CALL g18_add({ir}, {jc}, elK({ii}, {jj}, i3, j3))')
        return t
    def faults(t):
        t=dummy(t,'k')
        # No fault stiffness in this qualified scenario. Fail closed.
        t=a.replace1(t,'DO 500 iFE = 1, nFl','IF(nFl/=0) STOP 98\nDO 500 iFE = 1, nFl')
        return t
    def vbc(t):
        t=dummy(t,'k')
        t=a.replace1(t,'IMPLICIT NONE','USE G18CSR, ONLY: g18_get,g18_set,g18_zero_row\nIMPLICIT NONE')
        i=t.index('topOne = 0.D0')
        return t[:i]+'''
IF(nDOF/=nRank) STOP 98
IF(ANY(iCond(1:nCond)/=2)) STOP 98
topOne=0d0
DO i=1,nDOF
  topOne=MAX(topOne,g18_get(i,i))
END DO
IF(topOne<=0d0) STOP 98
DO i=1,nCond
  node=nodCon(i)
  vbcx=vBCMag(i)*COS(vBCArg(i))
  vbcy=vBCMag(i)*SIN(vBCArg(i))
  iRowx=2*node-1
  iRowy=2*node
  f(iRowx,1)=vbcx*topOne
  f(iRowy,1)=vbcy*topOne
  CALL g18_zero_row(iRowx)
  CALL g18_set(iRowx,iRowx,topOne)
  CALL g18_zero_row(iRowy)
  CALL g18_set(iRowy,iRowy,topOne)
END DO
RETURN
'''
    def fem(t):
        t=dummy(t,'k')
        t=a.replace1(t,'IMPLICIT NONE','USE G18CSR, ONLY: g18_dump\nIMPLICIT NONE')
        for u,suffix in [(72,'pre'),(73,'post')]:
            old=f"""OPEN({u},file=trim(c11prefix)//'_{suffix}.dat',status='new',action='write')
WRITE({u},*) nRank,nKRows,iDiagonal,nLB,nUB,nDOF
DO j=1,nRank
  WRITE({u},'(I6,*(1X,ES26.17E3))') j,f(j,1),k(:,j)
END DO
CLOSE({u})
"""
            t=a.replace1(t,old,f"CALL g18_dump(trim(c11prefix)//'_{suffix}.dat',nRank,f(1:nRank,1))\n")
        return t
    edit('BuildK',buildk); edit('AddFSt',faults); edit('VBCs',vbc); edit('FEM',fem)
    edit('Pure',lambda t:dummy(t,'k')); edit('Solver',lambda t:dummy(t,'ab'))
    return CSR_MODULE+s

def stage_graph(work):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    mesh=parse_feg((work/'regional.feg').read_text(),mode='SHELLS_READY')
    graph=g16.pattern(mesh); graph.sort_indices()
    a.need(graph.shape==(162,162) and graph.nnz==1988,'GRAPH_INVENTORY')
    with (work/'G18_GRAPH.dat').open('x') as f:
        f.write(f'{graph.shape[0]} {graph.nnz}\n')
        np.savetxt(f,np.r_[graph.indptr+1,graph.indices+1],fmt='%d')
    return graph

def read_sparse(path):
    with (path.parent/'G18_GRAPH.dat').open() as f:
        n,nz=map(int,f.readline().split()); raw=np.loadtxt(f,dtype=np.int64)
    a.need(n==162 and nz==1988 and raw.shape==(n+1+nz,),'GRAPH_FILE')
    rp=raw[:n+1]-1; ci=raw[n+1:]-1
    a.need(rp[0]==0 and rp[-1]==nz and np.all(np.diff(rp)>0) and np.all((ci>=0)&(ci<n)),'GRAPH_INDEX')
    vals=np.empty(nz); b=np.empty(n)
    with path.open() as f:
        a.need(f.readline().split()==['G18_CSR_V1',str(n),str(nz)],'CSR_DUMP_HEADER')
        for i in range(n):
            row=np.fromstring(f.readline(),sep=' ')
            a.need(len(row)==2+rp[i+1]-rp[i] and row[0]==i+1 and np.isfinite(row).all(),'CSR_DUMP_ROW')
            b[i]=row[1]; vals[rp[i]:rp[i+1]]=row[2:]
        a.need(not f.read().strip(),'CSR_DUMP_TRAILING')
    mat=sparse.csr_matrix((vals,ci,rp),shape=(n,n))
    a.need(mat.has_canonical_format,'CSR_CANONICAL')
    # Match the exact nonzero structure of G17's band decoder after row replacement.
    mat.eliminate_zeros()
    return mat.tocsc(),b

def dense_for_audit(path):
    mat,b=read_sparse(path)
    return mat.toarray(),b

def selftest():
    import tempfile
    # Full regional-size synthetic codec with deterministic 1988-position pattern.
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp); n=162
        # 12 entries per row plus one extra on 44 rows; sorted, unique.
        indices=[]; rp=[0]
        for i in range(n):
            cols=sorted((i+j)%n for j in range(13 if i<44 else 12))
            indices.extend(cols); rp.append(len(indices))
        a.need(len(indices)==1988,'FIXTURE_NNZ')
        with (p/'G18_GRAPH.dat').open('w') as f:
            f.write('162 1988\n'); np.savetxt(f,np.r_[rp,indices]+1,fmt='%d')
        vals=np.arange(1988,dtype=float); b=np.arange(n,dtype=float)
        d=p/'test.dat'
        with d.open('w') as f:
            f.write('G18_CSR_V1 162 1988\n')
            for i in range(n):
                f.write(' '.join(map(str,[i+1,b[i],*vals[rp[i]:rp[i+1]]]))+'\n')
        mat,q=read_sparse(d)
        expected=sparse.csr_matrix((vals,indices,rp),shape=(n,n))
        a.need(np.array_equal(mat.toarray(),expected.toarray()) and np.array_equal(q,b),'CSR_FIXTURE')
    print('G18_CSR_CODEC_SELFTEST_PASS',flush=True)

def assembly_parity(work,old,band_matrix):
    keys=['iter_001_pre.dat','iter_001_post.dat','final_pre.dat','final_post.dat']
    cases={}
    for key in keys:
        A,b=dense_for_audit(work/key); B,q=band_matrix(old/key)
        d=g16.relative(A,B); e=g16.relative(b,q)
        exact=bool(np.array_equal(A,B) and np.array_equal(b,q))
        cases[key]={'matrix_relative':d,'rhs_relative':e,'exact':exact,
                    'screen_pass':bool(exact if key.startswith('iter_001') else max(d,e)<=FIELD_LIMIT)}
    # Matching iteration numbers provide empirical trajectory agreement, not
    # identical nonlinear states if the solver changes rounding.
    files=sorted(work.glob('iter_*_pre.dat')); other=sorted(old.glob('iter_*_pre.dat'))
    common=sorted(set(x.name for x in files)&set(x.name for x in other))
    maxrel=0.
    for key in common:
        for name in (key,key.replace('_pre.dat','_post.dat')):
            A,b=dense_for_audit(work/name); B,q=band_matrix(old/name)
            maxrel=max(maxrel,g16.relative(A,B),g16.relative(b,q))
    return {'cases':cases,'matched_iterations':len(common),'max_matched_iteration_matrix_rhs_relative':maxrel,
            'screen_pass':bool(all(x['screen_pass'] for x in cases.values()) and maxrel<=FIELD_LIMIT)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--worker',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--authorize-direct-sparse-assembly',choices=[a.SCENARIO])
    args=ap.parse_args()
    if args.worker is not None:
        g17.read_sparse=read_sparse
        return g17.worker(args.worker)
    a.need(args.output is not None and args.authorize_direct_sparse_assembly==a.SCENARIO,'AUTHORIZATION')
    g8.check_helpers(); selftest()
    a.need(g7.blob(Path(__file__).with_name('arcana_g16_scale_sparse_bridge.py'))==
        'f39258ad725847e885ba44c8af188a42d74f10ce','G16_HELPER')
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g17','R6_THERMO_G17_LIVE_SPARSE_NONLINEAR_NEW01',G17_PIN,G17_STATUS),('g16','R6_THERMO_G16_SCALE_SPARSE_BRIDGE_NEW01',G16_PIN,G16_STATUS),
        ('g15','R6_THERMO_G15_MIDPOINT_COUPLING_NEW01',g16.G15_PIN,g16.G15_STATUS),
        ('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',g11.B_PIN,g11.B_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g15']; prior=a.read(p/'G15_REPORT.json'); audit=a.read(parents['g16']/'G16_REPORT.json')
    a.need(audit['screen_pass'] and manifests['g16']['G15_manifest_sha256']==g16.G15_PIN and
        prior['screen_pass'] and prior['accepted_checkpoint_sha256']==g16.CP_PIN,'SOURCE_LINEAGE')
    prev=parents['g17']; pr=a.read(prev/'G17_REPORT.json')
    a.need(pr['screen_pass'] and manifests['g17']['G16_manifest_sha256']==G16_PIN,'G17_LINEAGE')
    cp=p/prior['accepted_checkpoint']; g11.load(cp,g16.CP_PIN)
    src=cp.parent/'corrector_mechanics'
    # Accepted checkpoint is next to corrector_mechanics, not its parent trial.
    a.need(g8.same_npz(cp/'mechanical.npz',src/'ultra/C11B_FINAL_STATE.npz'),'MECHANICAL_LINEAGE')
    for n in (*g7.DECK,'regional.in',b10.SIDE):
        a.need(a.sha(cp/n)==a.sha(src/'ultra'/n),'DECK:'+n)
    build=prev/'build'; g8.binary(build,'solve.exe',native)
    a.need(g7.blob(Path(__file__).with_name('arcana_g17_live_sparse_nonlinear.py'))=='b553083798713e40b8998d40e3a81fbf94c218c1','G17_HELPER')
    ctl=dict(a.read(cp/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
    a.need((cp/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G16_manifest':G16_PIN,'G15_checkpoint':g16.CP_PIN,
        'runner_sha256':a.sha(Path(__file__)),'linear_backward_limit':LIMIT,'field_relative_limit':FIELD_LIMIT,
        'G17_manifest':G17_PIN,'scope':'Regional direct CSR assembly, same persistent SuperLU worker, no band allocation.',
        **c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'additional_builds':0,'native_nonlinear_solves_attempted':0,
        'additional_time_advance_years':0,'physical_acceptance':False,**c.SCOPE}
    try:
        print('G18_BUILD',flush=True)
        dest=out/'build'
        exe=g7.build(dest,root,native,patch_entry((build/'SHELLS_g7.f90').read_text()),
            patch((build/'MOD_Shells.f90').read_text()),(build/'driver.f90').read_text(),
            False,env,build/'MOD_ArcanaRuntime.f90')
        old=a.read(build/'BUILD_IDENTITY.json')['source_sha256']; new=a.read(dest/'BUILD_IDENTITY.json')['source_sha256']
        a.need(set(old)==set(new) and all(old[k]==new[k] for k in old if k not in ('MOD_Shells.f90','SHELLS_g7.f90'))
            and all(old[k]!=new[k] for k in ('MOD_Shells.f90','SHELLS_g7.f90')),'BUILD_DRIFT')
        report['additional_builds']=1
        ref=out/'reference'; ref.mkdir()
        shutil.copyfile(src/'reference/C11_MATRICES.npz',ref/'C11_MATRICES.npz')
        view=out/g7.C10_NAME; view.mkdir()
        shutil.copyfile(src/g7.C10_NAME/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',view/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
        work=out/'ultra'; b10.stage(work,cp,cp,native,ctl)
        graph=stage_graph(work)
        report['structure']={'n':graph.shape[0],'nnz':graph.nnz,'csr_bytes':int(8*graph.nnz+4*graph.nnz+4*(graph.shape[0]+1)), 'legacy_dummy_bytes':8}
        print('G18_NATIVE_DIRECT_CSR_REPLAY',flush=True)
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
        a.need(np.array_equal(np.loadtxt(work/'G18_GRAPH_READBACK.dat',dtype=int),np.loadtxt(work/'G18_GRAPH.dat',dtype=int,skiprows=1)),'NATIVE_GRAPH_READBACK')
        a.need(nlog.count('G18_CSR_ALLOC ')==1,'NATIVE_ALLOCATION_RECEIPT')
        band_matrix=a.matrix
        a.matrix=lambda path: dense_for_audit(path)
        try: ar=r1.analysis(work,ref,a)
        finally: a.matrix=band_matrix
        a.write(work/'MECHANICAL_ANALYSIS.json',ar)
        report['assembly_parity']=assembly_parity(work,prev/'ultra',band_matrix)
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
            and report['worker']['max_backward']<=LIMIT and all(x['screen_pass'] for x in fields.values())
            and report['assembly_parity']['screen_pass'])
    except Exception as exc:
        report['screen_pass']=False
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin,'PARENT_MUTATION')
    status='G18_DIRECT_CSR_NONLINEAR_PARITY_PASS__GLOBAL_INPUT_AND_GAUGE_REQUIRED' if report['screen_pass'] else 'G18_DIRECT_CSR_NONLINEAR_BLOCKED'
    report.update(status=status,limitations=[
        'One regional nonlinear replay, native direct CSR with a scalar legacy ABI dummy; offline dense audit is regional only.',
        'Graph supplied from pinned FEG, fixed topology, code-2 boundaries only, faults prohibited; textual worker is not production HPC.',
        'No actual global stiffness assembly, global gauge, material admission, exterior or event transition.',
        'No new temporal advancement, physical T1 or scientific promotion.'])
    a.write(out/'G18_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G16_manifest_sha256':G16_PIN,'G17_manifest_sha256':G17_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G18_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True); print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
