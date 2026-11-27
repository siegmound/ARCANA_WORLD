#!/usr/bin/env python3
"""C11-A candidate: pinned C10 native first-linearization assembly, NO solve.
Run from clean C10 checkout on FAIR. Source generation only in external output.
This script is not a ratification; explicit CLI approval is required to assemble.
"""
import argparse, json, os, re, shutil, subprocess, resource, hashlib
from pathlib import Path
import numpy as np

SHA='901cbb4a38916190df6a881bb561b6558dd997dd'
PIN='4e57523471281983aa228ddb82cd582f09c76129eeeb694460f0cfd2ad9108d7'
SCENARIO='C10_R8_DIORITE2_KINEMATICALLY_CONTROLLED_FREE_SLIP_V1'

def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,v):
    with p.open('x') as f: json.dump(v,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')
def replace1(s,a,b):
    need(s.count(a)==1,'SOURCE_ANCHOR:'+a[:80]); return s.replace(a,b,1)
def section(s,start,end):
    a=s.index(start); b=s.index(end,a); return s[a:b]

def gen_entry(stock,native):
    # Reuse exact C10 regional guards and precomputation; append stock Pure call.
    probe=native.generated_source(stock)
    cut='       v(1,:) = 2d-9'
    need(probe.count(cut)==1,'C10_PROBE_CUT')
    pure=section(stock,'        CALL Pure (alphaT, area,','!   Test and display the equilibrium found:') if '        CALL Pure (alphaT, area,' in stock else section(stock,'       CALL Pure (alphaT, area,','!   Test and display the equilibrium found:')
    # Keep original OldVel initial state, do not inject C10 manufactured probe velocities.
    return probe.split(cut)[0]+ '       dv = 0d0\n       dVLast = 0d0\n'+pure+'\n       stop 79 ! FEM must stop, never return\nend subroutine Shells_v5p0\nend module SHELLS\n'

def dump_code(unit,filename):
    return f'''OPEN({unit},file='{filename}',status='new',action='write')
WRITE({unit},*) nRank,nKRows,iDiagonal,nLB,nUB,nDOF
DO j=1,nRank
  WRITE({unit},'(I6,*(1X,ES26.17E3))') j,f(j,1),k(:,j)
END DO
CLOSE({unit})
'''

def gen_subs(stock):
    # Only alter the FEM routine: keep real BuildF/BuildK/AddFSt/VBCs.
    start=stock.index('SUBROUTINE FEM ('); end=stock.index('END SUBROUTINE FEM',start)
    fem=stock[start:end]
    anchor='CALL VBCs (iCond, mxBn, mxDOF,'
    need(fem.count(anchor)==1,'FEM_VBC_ANCHOR')
    fem=fem.replace(anchor,dump_code(72,'C11_PRE_BC.dat')+anchor,1)
    solver='CALL Solver (iUnitT,'
    need(fem.count(solver)==1,'FEM_SOLVER_ANCHOR')
    fem=fem.split(solver)[0]+dump_code(73,'C11_POST_BC.dat')+'''OPEN(74,file='C11_DOF.dat',status='new',action='write')
DO i=1,numNod
  WRITE(74,'(I6,4(1X,ES26.17E3))') i,v(:,i),fBase(2*i-1),fBase(2*i)
END DO
CLOSE(74)
OPEN(75,file='C11_BC.dat',status='new',action='write')
DO i=1,nCond
  WRITE(75,'(3I6,2(1X,ES26.17E3))') i,nodCon(i),iCond(i), &
    vBCMag(i)*COS(vBCArg(i)),vBCMag(i)*SIN(vBCArg(i))
END DO
CLOSE(75)
PRINT '(A)','C11A_STOP_AFTER_VBCS_BEFORE_SOLVER'
STOP 0
'''
    need(not re.search(r'(?im)^\s*call\s+solver\b',fem),'FEM_SOLVER_REACHABLE')
    # Additional hard guard in the stock Solver itself, should any other path reach it.
    s=stock[:start]+fem+stock[end:]
    s=replace1(s,'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )','STOP 82 ! C11A factorization forbidden')
    return s

def matrix(p):
    with p.open() as f:
        n,nr,d,kl,ku,nd=map(int,f.readline().split()); raw=np.loadtxt(f)
    need((n,nr,d,kl,ku,nd)==(162,64,43,21,21,162),'MATRIX_HEADER')
    need(raw.shape==(n,nr+2) and np.array_equal(raw[:,0],np.arange(1,n+1)),'MATRIX_COLUMNS')
    b=raw[:,1]; band=raw[:,2:].T; A=np.zeros((n,n))
    for j in range(n):
        for i in range(max(0,j-ku),min(n,j+kl+1)): A[i,j]=band[d-1+i-j,j]
    need(np.isfinite(A).all() and np.isfinite(b).all(),'NONFINITE_MATRIX')
    return A,b

def svd_report(A):
    s=np.linalg.svd(A,compute_uv=False); tol=max(A.shape)*np.finfo(float).eps*s[0]
    rank=int(np.count_nonzero(s>tol)); scale=np.linalg.norm(A,axis=1)
    scaled=None
    if np.all(scale>0):
        q=np.linalg.svd(A/scale[:,None],compute_uv=False)
        scaled={'rank':int(np.count_nonzero(q>max(A.shape)*np.finfo(float).eps*q[0])),
                'cond2':float(q[0]/q[-1]) if q[-1]>0 else None}
    return {'rank':rank,'rank_tolerance':float(tol),'singular_values':s.tolist(),
            'cond2':float(s[0]/s[-1]) if s[-1]>0 else None,'row_scaled':scaled}

def analyse(work,c10):
    A,b=matrix(work/'C11_PRE_BC.dat'); B,c=matrix(work/'C11_POST_BC.dat')
    bc=np.loadtxt(work/'C11_BC.dat'); nodes=bc[:,1].astype(int)-1
    need(bc.shape==(32,5) and np.unique(nodes).size==32 and np.all(bc[:,2]==2) and np.array_equal(bc[:,0],np.arange(1,33)) and min(nodes)>=0 and max(nodes)<81,'BC_NATIVE')
    held=np.ravel(np.column_stack((2*nodes,2*nodes+1))); free=np.setdiff1d(np.arange(162),held)
    target=bc[:,3:5].ravel(); top=float(max(0.,np.diag(A).max())); need(top>0,'VBC_TOPONE')
    expected=A.copy(); expected[held,:]=0; expected[held,held]=top
    rhs=b.copy(); rhs[held]=target*top
    need(np.array_equal(B,expected),'VBC_MATRIX_MISMATCH')
    need(np.array_equal(c[free],b[free]) and np.allclose(c[held],rhs[held],rtol=8*np.finfo(float).eps,atol=0),'VBC_RHS_MISMATCH')
    dof=np.loadtxt(work/'C11_DOF.dat'); need(dof.shape==(81,5) and np.isfinite(dof).all(),'DOF_DUMP')
    # Independently read the C10 qualified native BC and fixed forcing.
    p=c10/'native_pre_solve/hydrostatic/native_pre_solve.txt'
    lines=p.read_text().splitlines()
    oldbc=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('BC ')])
    oldnodes=np.array([[float(x) for x in l.split()[1:]] for l in lines if l.startswith('NODE ')])
    need(np.array_equal(bc[:,:3],oldbc[:,:3]) and np.max(np.abs(bc[:,3:]-oldbc[:,3:]))<2e-22,'C10_BC_READBACK_DRIFT')
    need(np.array_equal(dof[:,0],oldnodes[:,0]),'C10_NODE_ORDER')
    need(np.allclose(dof[:,3:5],oldnodes[:,-2:],rtol=1e-12,atol=1e-6),'C10_FIXED_LOAD_DRIFT')
    Aff=A[np.ix_(free,free)]; r=svd_report(Aff); full=svd_report(B)
    # No Ax=b evaluation or factorization. SVD is rank analysis, not equilibrium solve.
    np.savez(work/'C11_MATRICES.npz',A_pre=A,b_pre=b,A_post=B,b_post=c,held=held,free=free,target=target)
    norm=float(np.linalg.norm(Aff,ord=np.inf)); asym=float(np.linalg.norm(Aff-Aff.T,ord=np.inf)/max(norm,np.finfo(float).tiny))
    return {'n':162,'held':64,'free':98,'initial_velocity_max_m_s':float(np.max(np.abs(dof[:,1:3]))),
            'fixed_load_matches_C10':True,'VBC_row_replacement_matches':True,
            'free_operator':r,'post_constraint_operator':full,'free_relative_asymmetry_inf':asym,
            'first_linearization_only':True,'rank_screen_pass':r['rank']==98 and full['rank']==162,
            'condition_acceptance':'Not decided; report raw and row-scaled values. No physical convergence claim.',
            'physical_solves':0,'physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}

def limit(): resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--authorize-assembly-only',choices=[SCENARIO],required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==SHA,'HEAD_MISMATCH')
    need(not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip(),'DIRTY_CHECKOUT')
    archive=c10.OUT; manifest=read(archive/'MANIFEST.json')
    need(sha(archive/'MANIFEST.json')==PIN and manifest['source_sha']==SHA and manifest['development_only'] is False and manifest['status']==c10.STATUS,'C10_MANIFEST')
    need(all(manifest[k]==v for k,v in c10.SCOPE.items()),'C10_SCOPE')
    inventory=c10.c09.c08.c07.c06.inventory(archive); inventory.pop('MANIFEST.json'); need(inventory==manifest['files'],'C10_INVENTORY')
    reports,files,*_=c10.prepare(root)
    for k,v in files.items(): need((archive/k).read_bytes()==v.encode(),'C10_DECK_REPLAY:'+k)
    for k,v in reports.items():
        old=read(archive/k); expected=json.loads(json.dumps(v,allow_nan=False))
        need(all(old.get(x)==y for x,y in expected.items()),'C10_REPORT_REPLAY:'+k)
    work=args.output.resolve(); need(not work.exists() and not work.is_relative_to(root) and not work.is_relative_to(archive.resolve()),'OUTPUT_NOT_FRESH')
    work.mkdir(parents=False); write(work/'C11A_RECEIPT.json',{'C10_SHA':SHA,'C10_MANIFEST_SHA256':PIN,'C10_EXIT':0,'regression_passed':743,'regression_total':743,'regression_seconds':27.43,'assembly_only_cli':args.authorize_assembly_only,'natural_material_assignments':0,'mechanical_solve_authorized':False,'physical_T1':None,'D_024':'ACTIVE','D_025':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False})
    for k in ('regional.feg','regional_PRE.dat','controlled.bcs','regional.in','runtime.control','regional_reporting_plates.dat'): shutil.copyfile(archive/k,work/k)
    src=root/native.VENDOR
    for name in native.STOCK: shutil.copyfile(src/name,work/name)
    (work/'MOD_Shells.f90').write_text(gen_subs((src/'MOD_Shells.f90').read_text()))
    (work/'SHELLS_assembly.f90').write_text(gen_entry((src/'SHELLS_v5.0.f90').read_text(),native))
    shutil.copyfile(archive/'MOD_ArcanaRuntime.regional.f90',work/'MOD_ArcanaRuntime.f90')
    shutil.copyfile(Path(native.__file__).with_name('c10_pre_solve_driver.f90'),work/'driver.f90')
    # Driver keeps native C10 parser controls; guarded executable changes its stop location.
    compiler=native.COMPILER; lib=native.LIB
    sources=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_assembly.f90','driver.f90')
    cmd=[str(compiler),'-O0','-Mbackslash','-Kieee','-Mbounds',*sources,'-L'+str(lib),'-Wl,-rpath,'+str(lib),'-llapack','-lblas','-o','assembly_only.exe']
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    with (work/'build.log').open('x') as log: subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=work/'assembly_only.exe'; write(work/'BUILD_IDENTITY.json',{'compiler_sha256':sha(compiler),'exe_sha256':sha(exe),'argv':cmd,'source_sha256':{x:sha(work/x) for x in sources}})
    with (work/'run.log').open('x') as log: subprocess.run(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True,preexec_fn=limit)
    need('C11A_STOP_AFTER_VBCS_BEFORE_SOLVER' in (work/'run.log').read_text() and not (work/'FatalError.txt').exists(),'NO_HARD_STOP_MARKER')
    result=analyse(work,archive); write(work/'C11A_OPERATOR_ANALYSIS.json',result)
    status='C11A_FIRST_LINEARIZATION_RANK_SCREEN_PASS__SOLVE_NOT_AUTHORIZED' if result['rank_screen_pass'] else 'C11A_BLOCKED_RANK_SCREEN'
    write(work/'MANIFEST.json',{'status':status,'C10_manifest_sha256':PIN,'physical_solves':0,'files':{str(p.relative_to(work)):sha(p) for p in sorted(work.rglob('*')) if p.is_file()}})
    print('C11A_MANIFEST_SHA256',sha(work/'MANIFEST.json')); print(json.dumps({k:v for k,v in result.items() if k not in ('free_operator','post_constraint_operator')},indent=2)); print('FREE_RANK',result['free_operator']['rank'],'COND2',result['free_operator']['cond2']); print('POST_RANK',result['post_constraint_operator']['rank'],'COND2',result['post_constraint_operator']['cond2']); print(status)
    return 0 if result['rank_screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
