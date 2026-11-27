#!/usr/bin/env python3
"""G23 conditional global first-linearization CSR assembly, NO solve.
Two uniform effective analogues on authentic global PRE and FEG, no faults,
no imposed regional BC, zero basal tangential traction. Engineering only.
The original D12 exclusions remain excluded; this is not physical admission.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import traceback
import numpy as np
from scipy import sparse
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g7_paired_resolve as g7
import arcana_g16_scale_sparse_bridge as g16
import arcana_g18_direct_csr as g18

G22_PIN='5ea0a8787361f0701690654d110678a7ee55c5e386c12be6595c2da80a10a3ee'
G22_STATUS='G22_GLOBAL_CONSTITUTIVE_SENSITIVITY_PASS__DOMAIN_HYPOTHESIS_SELECTION_REQUIRED'
G19_PIN='79f2ea1a004cbb65a9b6a1967e833eba8e3c171bfc07fe9bd65f9eec641e91ca'
G19_STATUS='G19_GLOBAL_SUPPORT_ATLAS_PASS__MATERIAL_AND_BOUNDARY_CLOSURE_REQUIRED'
N=128884
NNZ=1804328
MEM=2*1024**3
TIMEOUT=1200
MODELS=('native_diorite2','native_legacy')
AUTH='G23_GLOBAL_CONDITIONAL_ASSEMBLY_ONLY_V1'

def c10_inventory(c10):
    # C10 uses the original {sha256, bytes} inventory schema.
    # Later G-series archives use a different, hash-only schema.
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT)
    a.need('MANIFEST.json' in inv,'C10_MANIFEST_INVENTORY_ENTRY')
    inv.pop('MANIFEST.json')
    return inv


def entry(stock,native):
    s=a.gen_entry(stock,native)
    s=g18.patch_entry(s)
    # C11A preserves the C10 regional pre-Pure geometry guard. Replace
    # that exact guard in the generated G23 source, never in frozen C10.
    regional_guard='       if (sphere .or. numNod/=81 .or. numEl/=128 .or. nCond/=32) stop 26'
    s=a.replace1(s,regional_guard,"""       print '(A,1X,L1,5(1X,I12))','G23_GLOBAL_GEOMETRY_CHECK',sphere,numNod,numEl,nCond,nFl,nRank
       if (.not.sphere .or. numNod/=64442 .or. numEl/=128880 .or. nCond/=0 .or. nFl/=0) stop 93
       if (nRank/=128884 .or. nDOF/=128884) stop 93
       print '(A)','G23_GLOBAL_GEOMETRY_GUARD_PASS'""")
    a.need(not re.search(r'(?im)^\\s*if\\s*\\([^\\n]*\\)\\s*stop\\s+26\\b',s),'G23_STALE_REGIONAL_GUARD')
    # The C10 source generator added a regional ReadBC guard. Remove that
    # guard and the whole actual ReadBC call, only for a closed fault-free sphere.
    start=s.index("       read(iUnitB,'(A)',iostat=ios) title2")
    end=s.index("       IF(Verbose) WRITE(iUnitVerb, \"(' Boundary-conditions file has been read...')\")",start)
    s=s[:start]+"""       if (.not.sphere .or. nCond/=0 .or. nFl/=0) stop 93
       title2='G23 closed sphere, no prescribed velocity'
       iCond=0
       vBCArg=0d0
       vBCMag=0d0
       skipBC=.TRUE.
"""+s[end:]
    s=a.replace1(s,'       dv = 0d0\n       dVLast = 0d0',"""       if (.not.sphere .or. numNod/=64442 .or. numEl/=128880 .or. nCond/=0 .or. nFl/=0) stop 93
       if (any(pulled) .or. etaMax/=0d0 .or. any(oVB/=0d0) .or. any(vM/=0d0)) stop 94
       if (any(delta_rho/=0d0) .or. any(glue<=0d0) .or. any(.not.ieee_is_finite(glue))) stop 94
       if (any(v/=0d0)) stop 94
       if (any(continuum_LRi(1:numEl)/=0)) stop 94
       open(74,file='G23_NATIVE_GEOMETRY.dat',status='new')
       do i=1,numNod
         write(74,'(I8,2(1X,ES26.17E3))') i,xNode(i),yNode(i)
       end do
       close(74)
       print '(A,4(1X,I12))','G23_NATIVE_READY',numNod,numEl,nCond,nRank
       dv = 0d0
       dVLast = 0d0""")
    return s

def subs(stock):
    s=stock
    def edit(name,fn):
        nonlocal s
        i=s.index('SUBROUTINE '+name+' ('); j=s.index('END SUBROUTINE '+name,i)
        s=s[:i]+fn(s[i:j])+s[j:]
    def dummy(t,var):
        lines=t.splitlines(keepends=True); n=0
        for j,line in enumerate(lines):
            if not line.lstrip().startswith('!') and var+'(nKRows, nRank)' in line:
                lines[j]=line.replace(var+'(nKRows, nRank)',var+'(1, 1)'); n+=1
        a.need(n==1,'DUMMY_DIMENSION:'+var)
        return ''.join(lines)
    def build(t):
        t=dummy(t,'stiff')
        t=a.replace1(t,'IMPLICIT NONE','USE G18CSR, ONLY: g18_reset,g18_add\nIMPLICIT NONE')
        t=a.replace1(t,'stiff = 0.0D0 ! whole matrix (per power of Fortran 90)','stiff = 0.0D0\nCALL g18_reset(nRank)')
        for ir,jc,i,j in [('irx','jcx',1,1),('irx','jcy',1,2),('iry','jcx',2,1),('iry','jcy',2,2)]:
            t=a.replace1(t,f'stiff(iq, {jc}) = stiff(iq, {jc}) + elK({i}, {j}, i3, j3)',
                f'CALL g18_add({ir}, {jc}, elK({i}, {j}, i3, j3))')
        return t
    def fault(t):
        t=dummy(t,'k')
        return a.replace1(t,'DO 500 iFE = 1, nFl','IF(nFl/=0) STOP 98\nDO 500 iFE = 1, nFl')
    def fem(t):
        t=dummy(t,'k')
        t=a.replace1(t,'IMPLICIT NONE','USE G18CSR, ONLY: g18_dump\nIMPLICIT NONE')
        i=t.index('CALL VBCs (iCond, mxBn, mxDOF,')
        return t[:i]+"""IF(nCond/=0.or.nFl/=0.or.nRank/=nDOF) STOP 95
CALL g18_dump('G23_PRE_BC.dat',nRank,f(1:nRank,1))
OPEN(75,file='G23_NATIVE_LOAD.dat',status='new')
DO i=1,numNod
  WRITE(75,'(I8,4(1X,ES26.17E3))') i,v(:,i),fBase(2*i-1),fBase(2*i)
END DO
CLOSE(75)
PRINT '(A)','G23_STOP_AFTER_GLOBAL_CSR_BEFORE_VBC_AND_SOLVER'
STOP 0
"""
    def solver(t):
        t=dummy(t,'ab')
        return a.replace1(t,'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )','STOP 96 ! no factorization permitted')
    edit('BuildK',build); edit('AddFSt',fault); edit('FEM',fem)
    edit('Pure',lambda t:dummy(t,'k')); edit('Solver',solver)
    a.need(not re.search(r'(?im)^\s*call\s+dgbsv\b',s),'SOLVER_REACHABLE')
    return g18.CSR_MODULE+s

def stage(work,root,atlas,native,ctl,graph,feg,pre):
    work.mkdir()
    shutil.copyfile(feg,work/'regional.feg')
    shutil.copyfile(pre,work/'regional_PRE.dat')
    (work/'regional.in').write_text(native.serialize_lr(ctl))
    (work/'runtime.control').write_text('C10_PRE_SOLVE_ONLY\n')
    (work/'controlled.bcs').write_text('G23 closed sphere, zero BC\n')
    with (work/'regional_reporting_plates.dat').open('x') as f:
        for j,row in enumerate(atlas,1):
            a.need(int(row['node_id'])==j and 0<=int(row['owner_plate'])<=11,'OWNER_PLATE')
            f.write(f"{j} {int(row['owner_plate'])+2}\n")
    with (work/'G18_GRAPH.dat').open('x') as f:
        f.write(f'{N} {NNZ}\n')
        np.savetxt(f,np.r_[graph.indptr+1,graph.indices+1],fmt='%d')

def limit():
    resource.setrlimit(resource.RLIMIT_AS,(MEM,MEM))

def run(exe,work,env):
    with (work/'run.log').open('x') as log:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o','run.time',str(exe)],
            cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit,start_new_session=True)
        try: rc=proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL); proc.wait(); rc=124
    return rc

def read_csr(work,P):
    n,nz=P.shape[0],P.nnz
    ptr=P.indptr; ix=P.indices
    readback=np.loadtxt(work/'G18_GRAPH_READBACK.dat',dtype=np.int64)
    a.need(np.array_equal(readback,np.r_[ptr+1,ix+1]),'NATIVE_GRAPH_READBACK')
    val=np.empty(nz); b=np.empty(n)
    with (work/'G23_PRE_BC.dat').open() as f:
        a.need(f.readline().split()==['G18_CSR_V1',str(n),str(nz)],'CSR_HEADER')
        for i in range(n):
            row=np.fromstring(f.readline(),sep=' ')
            a.need(len(row)==2+ptr[i+1]-ptr[i] and row[0]==i+1 and np.isfinite(row).all(),'CSR_ROW:'+str(i))
            b[i]=row[1]; val[ptr[i]:ptr[i+1]]=row[2:]
        a.need(not f.read().strip(),'CSR_TRAILING')
    A=sparse.csr_matrix((val,ix.copy(),ptr.copy()),shape=(n,n))
    a.need(A.has_canonical_format,'CSR_FORMAT')
    A.eliminate_zeros()
    return A,b

def analyse(work,P,mesh):
    log=(work/'run.log').read_text()
    a.need('G23_STOP_AFTER_GLOBAL_CSR_BEFORE_VBC_AND_SOLVER' in log
        and 'G23_NATIVE_READY' in log and 'G18_CSR_ALLOC' in log
        and not (work/'FatalError.txt').exists(),'NATIVE_STOP')
    A,b=read_csr(work,P)
    x=np.loadtxt(work/'G23_NATIVE_LOAD.dat'); geo=np.loadtxt(work/'G23_NATIVE_GEOMETRY.dat')
    a.need(x.shape==(64442,5) and geo.shape==(64442,3)
        and np.array_equal(x[:,0],geo[:,0]) and np.array_equal(x[:,0],np.arange(1,64443))
        and np.isfinite(x).all() and np.isfinite(geo).all() and np.all(x[:,1:3]==0),'NATIVE_INITIAL_STATE')
    # Native xNode is colatitude and yNode longitude, in radians.
    th,lon=geo[:,1:].T
    xyz=np.column_stack((np.sin(th)*np.cos(lon),np.sin(th)*np.sin(lon),np.cos(th)))
    lat0,lon0=np.deg2rad(np.array([[v.latitude_deg,v.longitude_deg] for v in mesh.nodes])).T
    source=np.column_stack((np.cos(lat0)*np.cos(lon0),np.cos(lat0)*np.sin(lon0),np.sin(lat0)))
    geomdiff=float(np.max(np.linalg.norm(xyz-source,axis=1)))
    a.need(geomdiff<=1e-7,'NATIVE_GEOGRAPHIC_BASIS')
    south=np.column_stack((np.cos(th)*np.cos(lon),np.cos(th)*np.sin(lon),-np.sin(th)))
    east=np.column_stack((-np.sin(lon),np.cos(lon),np.zeros_like(lon)))
    rot=np.cross(np.eye(3)[None,:,:],xyz[:,None,:])
    G=np.stack((np.einsum('nki,ni->nk',rot,south),np.einsum('nki,ni->nk',rot,east)),axis=1).reshape(N,3)
    def infnorm(M): return float(np.max(np.asarray(abs(M).sum(axis=1)).ravel()))
    scale=infnorm(A)
    a.need(scale>0 and np.isfinite(scale) and A.nnz>0,'OPERATOR_ZERO')
    rhsmax=float(np.max(abs(b)))
    denom=np.sum(abs(G)*abs(b[:,None]),axis=0)
    torque=G.T@b
    diagonal=A.diagonal()
    sparse.save_npz(work/'GLOBAL_PRE_BC_CSR.npz',A)
    np.savez_compressed(work/'GLOBAL_PRE_BC_FIELDS.npz',rhs=b,fixed_load=x[:,3:5].ravel(),
        rotation_candidates=G,native_xyz=xyz)
    timing=(work/'run.time').read_text()
    m=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',timing)
    return {'screen_pass':True,'dofs':N,'structural_nnz':NNZ,'actual_nnz':int(A.nnz),
        'csr_bytes':int(A.data.nbytes+A.indices.nbytes+A.indptr.nbytes),
        'native_geometry_max_chord_difference':geomdiff,'operator_inf_norm':scale,
        'relative_asymmetry_inf':infnorm(A-A.T)/scale,
        'diagonal_range':[float(diagonal.min()),float(diagonal.max())],
        'zero_rows':int(np.count_nonzero(np.diff(A.indptr)==0)),
        'rotation_candidate_right_residual_scaled':[float(np.max(abs(v))/scale) for v in (A@G).T],
        'rotation_candidate_left_residual_scaled':[float(np.max(abs(v))/scale) for v in (A.T@G).T],
        'rotation_projected_rhs':torque.tolist(),
        'rotation_projected_rhs_relative':(abs(torque)/np.maximum(denom,1e-300)).tolist(),
        'rhs_max_abs':rhsmax,'fixed_load_max_abs':float(np.max(abs(x[:,3:5]))),
        'max_RSS_KiB':int(m.group(1)) if m else None,'global_rank_qualified':False,
        'global_gauge_qualified':False,'factorization_performed':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-conditional-global-assembly-only',choices=[AUTH],required=True)
    args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native,c09_mechanical_case as c09
    from experiments.shellset_regional_explore_v1 import build_case
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA
        and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    p=c10.OUT.with_name('R6_THERMO_G19_GLOBAL_SUPPORT_ATLAS_NEW01')
    q=c10.OUT.with_name('R6_THERMO_G22_GLOBAL_CONSTITUTIVE_SCREEN_NEW01')
    pm=c.verified(p,G19_PIN,G19_STATUS); qm=c.verified(q,G22_PIN,G22_STATUS)
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_MANIFEST_PIN')
    a.need(c10_inventory(c10)==cm['files'],'C10_INVENTORY')
    print('G23_C10_NATIVE_INVENTORY_PASS',flush=True)
    a.need(qm['G19_manifest_sha256']==G19_PIN and all(m['source_sha']==a.SHA and
        all(m[k]==v for k,v in c.SCOPE.items()) for m in (pm,qm,cm)),'PARENT_SCOPE')
    a.need(a.read(q/'G22_REPORT.json')['screen_pass'],'G22_SCREEN')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,c10.OUT,c10.c09.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'runner_sha256':a.sha(Path(__file__)),'G22_manifest':G22_PIN,
        'scope':AUTH,'physical_material_admission':False,'models':MODELS,
        'conditions':'Closed shared sphere, no faults, zero initial velocities, no Dirichlet BC, free-slip tangential limiting case; native internal fixed terms retained.',
        'per_native_process_address_space_limit_bytes':MEM,'timeout_seconds_per_case':TIMEOUT,
        'D12_excluded_cells_retained':1180,'global_physical_assembly_authorized':False,
        'global_solve_authorized':False,**c.SCOPE})
    report={'screen_pass':False,'additional_builds':0,'native_assemblies_attempted':0,
        'additional_native_solves':0,'additional_time_advance_years':0,'physical_acceptance':False,
        'material_assignments':0,**c.SCOPE}
    try:
        source=c09.global_route(root)
        feg=root/build_case.FEG; pre=root/(build_case.PRE+'.dat')
        a.need(a.sha(feg)==source['source_FEG_sha256'] and a.sha(pre)==source['source_PRE_sha256'],'SOURCE_PIN')
        models=a.read(q/'SOURCE_AND_MODELS.json')
        a.need(models['PRE_sha256']==a.sha(pre),'G22_PRE_LINEAGE')
        mesh=parse_feg(feg.read_text(),mode='SHELLS_READY')
        graph=g16.pattern(mesh); graph.sort_indices()
        a.need(graph.shape==(N,N) and graph.nnz==NNZ and not mesh.faults,'GLOBAL_GRAPH')
        with (p/'GLOBAL_TRIANGLE_SUPPORT.csv').open() as f:
            owners={r['parent_cell_id']:r['plate_id'] for r in csv.DictReader(f)}
        with (p/'GLOBAL_NODAL_SUPPORT.csv').open() as f:
            atlas=[dict(r,owner_plate=owners[r['PRE_owner_cell']]) for r in csv.DictReader(f)]
        a.need(len(atlas)==64442 and len(owners)==64800,'REPORTING_OWNER_MAP')
        baseline=a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')['lr_native_parameters']
        vendor=root/native.VENDOR
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        print('G23_BUILD_ASSEMBLY_ONLY',flush=True)
        driver=(root/'experiments/r6_thermo_provider_pilot_v1/c10_pre_solve_driver.f90').read_text()
        exe=g7.build(out/'build',root,native,entry((vendor/'SHELLS_v5.0.f90').read_text(),native),
            subs((vendor/'MOD_Shells.f90').read_text()),driver,True,env,vendor/'MOD_ArcanaRuntime.f90')
        report['additional_builds']=1
        report['cases']={}
        for key in MODELS:
            model=models['models'][key]
            ctl=dict(baseline,aCreep=model['A_Pa_s_to_e'],bCreep=model['B_K'],cCreep=model['C_K_per_m'],
                dCreep=model['dCreep_Pa'],eCreep=model['eCreep'],cFric=model['cFric'],Biot=1.)
            work=out/key
            try:
                stage(work,root,atlas,native,ctl,graph,feg,pre)
                a.write(work/'CONDITIONAL_CONTROLS.json',ctl)
                print('G23_ASSEMBLE',key,flush=True)
                report['native_assemblies_attempted']+=1
                rc=run(exe,work,env)
                a.need(rc==0,'NATIVE_EXIT:'+str(rc))
                report['cases'][key]=dict(analyse(work,graph,mesh),native_exit=rc)
                print('G23_CASE',key,json.dumps(report['cases'][key]),flush=True)
            except Exception as exc:
                report['cases'][key]={'screen_pass':False,'error':repr(exc),'traceback':traceback.format_exc()}
                if (work/'run.log').exists():
                    report['cases'][key]['native_log_tail']=(work/'run.log').read_text()[-3500:]
        if all(report['cases'][k]['screen_pass'] for k in MODELS):
            A=sparse.load_npz(out/MODELS[0]/'GLOBAL_PRE_BC_CSR.npz'); B=sparse.load_npz(out/MODELS[1]/'GLOBAL_PRE_BC_CSR.npz')
            with np.load(out/MODELS[0]/'GLOBAL_PRE_BC_FIELDS.npz') as x,np.load(out/MODELS[1]/'GLOBAL_PRE_BC_FIELDS.npz') as y:
                b=x['rhs']; d=y['rhs']
                report['paired_comparison']={'matrix_relative_inf':float(np.max(np.asarray(abs(A-B).sum(axis=1)))/max(report['cases'][MODELS[0]]['operator_inf_norm'],report['cases'][MODELS[1]]['operator_inf_norm'])),
                    'rhs_relative_inf':float(np.max(abs(b-d))/max(np.max(abs(b)),np.max(abs(d)),1e-300)),
                    'fixed_load_exact':bool(np.array_equal(x['fixed_load'],y['fixed_load']))}
            report['screen_pass']=True
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for path,m,pin in ((p,pm,G19_PIN),(q,qm,G22_PIN)):
        a.need(c.inventory(path)==m['files'] and a.sha(path/'MANIFEST.json')==pin,'PARENT_MUTATION:'+path.name)
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and c10_inventory(c10)==cm['files'],'PARENT_MUTATION:C10')
    print('G23_C10_NATIVE_INVENTORY_POSTCHECK_PASS',flush=True)
    status='G23_CONDITIONAL_GLOBAL_CSR_ASSEMBLY_PASS__OPERATOR_AND_PHYSICAL_AUTHORITY_REQUIRED' if report['screen_pass'] else 'G23_CONDITIONAL_GLOBAL_ASSEMBLY_BLOCKED'
    report.update(status=status,limitations=[
        'Assembly-only engineering alternatives: uniform effective analogue parameters on all original numerical PRE nodes, including D12 exclusions; not material or contact admission.',
        'Native zero-velocity first linearization is not nonlinear equilibrium. No constraints imposed, no factorization or solve.',
        'Rotation tests are diagnostic, not a proof of nullspace dimension or gauge suitability.',
        'No physical T1, contact transition, global physical assembly or production authorization. G18 documentary blocker retained.'])
    a.write(out/'G23_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G19_manifest_sha256':G19_PIN,
        'G22_manifest_sha256':G22_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G23_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True);print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
