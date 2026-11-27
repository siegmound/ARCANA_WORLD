#!/usr/bin/env python3
"""C11-C: bounded serial sensitivity campaign; no T1 or natural-model promotion.
Execute from the pinned clean C10 checkout with archived sibling runners.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1

R1_PIN = 'ab2c576dee82f9feb797568d1ec7ee873a15523877140427df11f3bff755e974'
R1_STATUS = 'C11BR1_CONTROLLED_SOLVE_NUMERICAL_SCREEN_PASS__SENSITIVITY_REQUIRED'
R1_SCRIPT = 'ba76597ceb1d40eca8939f21764e4667048d2b4428430bd820efe11007a8d65b'
CASES = {
    'S0': ({}, 'controlled.bcs', 'baseline instrumented replay'),
    'S1': ({'Biot': 0.}, 'controlled.bcs', 'physical dry pore hypothesis'),
    'S2': ({}, 'linear_arc_sensitivity.bcs', 'physical linear imposed trace'),
    'S3': ({'zBAsth': 2000.}, 'controlled.bcs', 'inactive free-slip compatibility'),
    'S4': ({'okDelV': 5e-12}, 'controlled.bcs', 'numerical viscosity limit'),
    'S5': ({'okDelV': 2e-11}, 'controlled.bcs', 'numerical viscosity limit'),
    'S6': ({'okToQt': 5e-8}, 'controlled.bcs', 'numerical convergence refinement'),
}
SCOPE = {'physical_T1': None, 'WORLD_HISTORY_PRODUCTION_AUTHORIZED': False,
         'D_024': 'ACTIVE', 'D_025': 'ACTIVE', 'scientific_promotion': False}

def inventory(path):
    return {str(p.relative_to(path)): a.sha(p) for p in sorted(path.rglob('*'))
            if p.is_file() and p != path/'MANIFEST.json'}

def verified(path, pin, status):
    m = a.read(path/'MANIFEST.json')
    a.need(a.sha(path/'MANIFEST.json') == pin and m['status'] == status,
           'PARENT_PIN:'+path.name)
    a.need(inventory(path) == m['files'], 'PARENT_INVENTORY:'+path.name)
    return m

def caps(source):
    """Counters at actual native clamp sites, final constitutive refresh only.
    Counts of trial evaluations are not a depth fraction or a mineral assignment.
    """
    start = source.index('SUBROUTINE Diamnd (')
    end = source.index('END SUBROUTINE Diamnd', start)
    d = source[start:end]
    d = a.replace1(d, 'IMPLICIT NONE', '''IMPLICIT NONE
LOGICAL c11audit
INTEGER c11search,c11creep,c11mean,c11regionv,c11samples''')
    d = a.replace1(d, 'ez = -(e1 + e2)', '''INQUIRE(file='C11B_FINAL_REQUEST',exist=c11audit)
c11search=0
c11creep=0
c11mean=0
c11regionv=0
c11samples=0
ez = -(e1 + e2)''')
    for x in ('sc0', 'sc1', 'sch'):
        key = f'{x} = MIN({x}, dCreep)'
        d = a.replace1(d,key,f'IF ({x}>dCreep) c11search=c11search+1\n'+key)
    d = a.replace1(d, 'vis = MIN(vis, visDCr)', '''c11samples=c11samples+1
IF (vis>visDCr) c11creep=c11creep+1
vis = MIN(vis, visDCr)''')
    d = a.replace1(d, 'visInt = MIN(visInt, visMax * (thick - zTran))',
        'IF (visInt>visMax*(thick-zTran)) c11mean=1\nvisInt = MIN(visInt, visMax * (thick - zTran))')
    key = 'sigma1 = sz + visMax * (4.0D0 * e1 + 2.0D0 * e2)'
    d = a.replace1(d,key,'c11regionv=1\n'+key)
    d = a.replace1(d,'RETURN', '''IF (c11audit) THEN
  WRITE(*,'(A,3(1X,ES26.17E3),5(1X,I6))') 'C11CAP', &
    zOfTop,thick,zTran,c11search,c11creep,c11mean,c11regionv,c11samples
END IF
RETURN''')
    source = source[:start]+d+source[end:]
    start=source.index('SUBROUTINE Viscos (')
    end=source.index('END SUBROUTINE Viscos',start)
    v=source[start:end]
    v=a.replace1(v,'IMPLICIT NONE','IMPLICIT NONE\nLOGICAL c11audit')
    key='IF ((exx == 0.0D0).AND.(exy == 0.0D0).AND.(eyy == 0.0D0)) THEN'
    v=a.replace1(v,key,key+'''
  INQUIRE(file='C11B_FINAL_REQUEST',exist=c11audit)
  IF (c11audit) WRITE(*,'(A,2(1X,I6))') 'C11ZERO',i,m''')
    return source[:start]+v+source[end:]

def cap_report(log):
    rows=np.array([[float(v) for v in l.split()[1:]] for l in log.splitlines()
                   if l.startswith('C11CAP ')],dtype=float).reshape(-1,8)
    zeros=[[int(v) for v in l.split()[1:]] for l in log.splitlines()
           if l.startswith('C11ZERO ')]
    a.need(len(rows)+2*len(zeros)==1792 and np.isfinite(rows).all(),
           'FINAL_CAP_LAYER_INVENTORY')
    a.need(len({tuple(x) for x in zeros})==len(zeros),'ZERO_IP_DUPLICATE')
    out={}
    for layer,mask in (('crust',rows[:,0]==0),('mantle',rows[:,0]>0)):
        x=rows[mask]
        a.need(len(x)==896-len(zeros) and np.all(x[:,1]>0) and
               np.all((x[:,2]>=0)&(x[:,2]<=x[:,1])),'CAP_LAYER_SCOPE')
        a.need(np.all(x[:,4]<=x[:,7]) and np.all(x[:,3:]>=0),'CAP_COUNTER_RANGE')
        out[layer]={'layer_calls':len(x),
            'dCreep_transition_trial_hits':int(x[:,3].sum()),
            'dCreep_transition_layer_calls_with_hits':int(np.count_nonzero(x[:,3])),
            'dCreep_creep_quadrature_hits':int(x[:,4].sum()),
            'creep_trial_samples':int(x[:,7].sum()),
            'dCreep_creep_layer_calls_with_hits':int(np.count_nonzero(x[:,4])),
            'visMax_mean_creep_clamped_layer_calls':int(x[:,5].sum()),
            'visMax_brittle_region_V_layer_calls':int(x[:,6].sum())}
    return {'final_refresh_only':True,'zero_strain_IP_visMax_initialization':len(zeros),
            'zero_strain_IP_ids':zeros,'layers':out,
            'limitations':'Actual clamp-site counts, not depth fractions. Other visMax-dependent brittle stiffness terms remain active and are tested through okDelV sensitivity. No all-iteration cap inventory.'}

def reference(path,c10,parent,case,controls,bcfile):
    """Predict first linearization from independent C11A and C10 native BC.
    Zero strain Viscos stiffness scales exactly with visMax, hence 1/okDelV;
    pore pressure has not entered the zero-strain branch. Fixed GPE unchanged.
    """
    old=np.load(parent/'C11_MATRICES.npz')
    variant='linear_arc' if bcfile!='controlled.bcs' else 'hydrostatic'
    p=c10/'native_pre_solve'/variant/'native_pre_solve.txt'
    bc=np.array([[float(v) for v in l.split()[1:]] for l in p.read_text().splitlines()
                 if l.startswith('BC ')])
    held=np.column_stack((2*(bc[:,1].astype(int)-1),2*(bc[:,1].astype(int)-1)+1)).ravel()
    a.need(np.array_equal(held,old['held']) and np.all(bc[:,2]==2),'REFERENCE_BC')
    target=bc[:,3:5].ravel()
    A=old['A_pre']*(1e-11/controls['okDelV']); b=old['b_pre']
    B=A.copy(); top=float(np.diag(A).max()); B[held,:]=0; B[held,held]=top
    c=b.copy(); c[held]=target*top
    path.mkdir()
    np.savez(path/'C11_MATRICES.npz',A_pre=A,b_pre=b,A_post=B,b_post=c,
             held=held,free=old['free'],target=target)

def main():
    from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    ap=argparse.ArgumentParser()
    ap.add_argument('--authorize-controlled-sensitivity',choices=[a.SCENARIO],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    for n,pin in [('arcana_c11a_assembly.py',r1.A_SCRIPT_PIN),
                  ('arcana_c11b_first_solve.py',r1.B_SCRIPT_PIN),
                  ('arcana_c11br1_convergence.py',R1_SCRIPT)]:
        a.need(a.sha(here/n)==pin,'RUNNER_HASH:'+n)
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA
           and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),
           'C10_CHECKOUT')
    parent=c10.OUT.with_name('R6_THERMO_C11A_OPERATOR_ASSEMBLY_NEW01')
    b=c10.OUT.with_name('R6_THERMO_C11B_FIRST_CONTROLLED_SOLVE_NEW01')
    baseline=c10.OUT.with_name('R6_THERMO_C11BR1_CONVERGENCE_NEW01')
    verified(parent,r1.A_PIN,r1.A_STATUS)
    verified(b,r1.B_PIN,r1.B_STATUS)
    rm=verified(baseline,R1_PIN,R1_STATUS)
    a.need(rm['source_sha']==a.SHA and rm['C11A_manifest_sha256']==r1.A_PIN and
           rm['C11B_manifest_sha256']==r1.B_PIN and rm['physical_solves']==1 and
           rm['physical_T1'] is None,'R1_LINEAGE')
    old=a.read(baseline/'C11BR1_ANALYSIS.json')
    a.need(old['screen_pass'] and len(old['iterations'])==79,'R1_RESULT')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and
           all(cm[k]==v for k,v in c10.SCOPE.items()),'C10_SCOPE')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in
          (root,c10.OUT,parent,b,baseline)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'CAMPAIGN_POLICY.json',{'scenario':a.SCENARIO,'cases':CASES,
        'maxItr':250,'baseline_okToQt':5e-7,'per_native_run_wall_s':120,
        'per_native_run_address_space_bytes':1073741824,'serial':True,
        'R1_manifest':R1_PIN,'runner_sha256':a.sha(Path(__file__)),
        'acceptance':'Original R1 numerical screen unchanged except S6 native score target. S0 replay and S3 inactive parameter invariance relative 1e-10 for full fields. Other sensitivities measured, not accepted automatically.',**SCOPE})
    # r1.analysis expects this exact sibling package for the unchanged frame.
    package_dir=out/c10.OUT.name; package_dir.mkdir()
    shutil.copyfile(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',
                    package_dir/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    controls0=a.read(package_dir/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')['lr_native_parameters']
    a.need(native.serialize_lr(controls0).encode()==(c10.OUT/'regional.in').read_bytes(),'LR_REPLAY')
    src=root/native.VENDOR
    entry,subs=r1.native_sources((src/'SHELLS_v5.0.f90').read_text(),
                                  (src/'MOD_Shells.f90').read_text(),a,native)
    subs=caps(subs)
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    reports={}; base_state=np.load(baseline/'C11B_FINAL_STATE.npz')
    fields=('velocity','strain_rate','tau_relative','reaction')
    for case,(change,bcfile,kind) in CASES.items():
        print('C11C_CASE',case,kind,flush=True)
        work=out/case; work.mkdir()
        ctl=dict(controls0,maxItr=250,okToQt=5e-7); ctl.update(change)
        a.write(work/'CASE_POLICY.json',{'kind':kind,'controls':ctl,'bc_file':bcfile,**SCOPE})
        try:
            for n in ('regional.feg','regional_PRE.dat','runtime.control','regional_reporting_plates.dat'):
                shutil.copyfile(c10.OUT/n,work/n)
            shutil.copyfile(c10.OUT/bcfile,work/'controlled.bcs')
            (work/'regional.in').write_text(native.serialize_lr(ctl))
            for n in native.STOCK: shutil.copyfile(src/n,work/n)
            (work/'MOD_Shells.f90').write_text(subs)
            (work/'SHELLS_solve.f90').write_text(entry)
            shutil.copyfile(c10.OUT/'MOD_ArcanaRuntime.regional.f90',work/'MOD_ArcanaRuntime.f90')
            driver=Path(native.__file__).with_name('c10_pre_solve_driver.f90').read_text()
            key='  if (Biot/=1d0 .and. Biot/=0d0) stop 16'
            driver=a.replace1(driver,key,key+'''
  print '(A,I6,4(1X,ES26.17E3))','C11C_CONTROLS ',maxItr,okToQt,okDelV,Biot,zBAsth
''')
            (work/'driver.f90').write_text(driver)
            compiler=native.COMPILER; lib=native.LIB
            sources=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_solve.f90','driver.f90')
            cmd=[str(compiler),'-O0','-Mbackslash','-Kieee','-Mbounds',*sources,
                 '-L'+str(lib),'-Wl,-rpath,'+str(lib),'-llapack','-lblas','-o','controlled_solve.exe']
            with (work/'build.log').open('x') as log:
                subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
            exe=work/'controlled_solve.exe'
            a.write(work/'BUILD_IDENTITY.json',{'argv':cmd,'compiler_sha256':a.sha(compiler),
                'exe_sha256':a.sha(exe),'source_sha256':{n:a.sha(work/n) for n in sources},
                'lapack_blas_sha256':{n:a.sha(lib/n) for n in ('liblapack.so','libblas.so')}})
            with (work/'run.log').open('x') as log:
                p=subprocess.Popen(['/usr/bin/time','-v','-o','run.time',str(exe)],
                   cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,
                   preexec_fn=a.limit,start_new_session=True)
                try: rc=p.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL); p.wait(); rc=124
            log=(work/'run.log').read_text()
            a.need(rc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log and
                   not (work/'FatalError.txt').exists(),'NATIVE_STOP:'+str(rc))
            readback=[l.split()[1:] for l in log.splitlines() if l.startswith('C11C_CONTROLS ')]
            expected=[250,ctl['okToQt'],ctl['okDelV'],ctl['Biot'],ctl['zBAsth']]
            a.need(len(readback)==1 and np.allclose(np.array(readback[0],float),expected,
                   rtol=1e-13,atol=0),'CONTROL_READBACK')
            ref=out/('reference_'+case)
            reference(ref,c10.OUT,parent,case,ctl,bcfile)
            r1.NATIVE_TOL=ctl['okToQt']
            report=r1.analysis(work,ref,a)
            report['first_linearization_reference']='Independent C11A zero-strain stiffness scaled by inverse okDelV and C10 native BC readback'
            report['cap_audit']=cap_report(log)
            state=np.load(work/'C11B_FINAL_STATE.npz')
            comparison={}
            for f in fields:
                x=state[f]; y=base_state[f]
                a.need(x.shape==y.shape,'FIELD_SHAPE')
                comparison[f]={'relative_max':r1.ratio(float(np.max(abs(x-y))),max(float(np.max(abs(x))),float(np.max(abs(y))))),
                  'relative_L2':r1.ratio(float(np.linalg.norm(x-y)),max(float(np.linalg.norm(x)),float(np.linalg.norm(y)))),
                  'absolute_max':float(np.max(abs(x-y)))}
            report['baseline_field_comparison']=comparison
            invariant=all(v['relative_max']<=1e-10 for v in comparison.values()) if case in ('S0','S3') else None
            report['invariance_screen']=invariant
            a.write(work/'C11C_ANALYSIS.json',report)
            reports[case]={'status':'SCREEN_PASS' if report['screen_pass'] and invariant is not False else 'SCREEN_BLOCKED',
                'iterations':len(report['iterations']),'residual':report['final_free_relative_residual'],
                'work_defect':report['work_balance_relative_defect'],'stress_refresh':report['stress_refresh_relative_max_component'],
                'free_cond2':report['final_free_rank']['cond2'],'max_speed_m_s':report['max_final_speed_m_s'],
                'max_strain_s_inv':report['max_strain_component_s_inv'],'power_W':report['quadrature_power_W'],
                'fields':comparison,'caps':report['cap_audit'],'invariance_screen':invariant}
        except Exception as exc:
            reports[case]={'status':'EXECUTION_OR_DIAGNOSTIC_ERROR','error':repr(exc),
                'completed_linear_solves':len(list(work.glob('iter_*_solution.dat')))}
        print(json.dumps({case:reports[case]},allow_nan=False),flush=True)
    success=all(x['status']=='SCREEN_PASS' for x in reports.values())
    status='C11C_SENSITIVITY_CAMPAIGN_NUMERICAL_SCREEN_PASS__PHYSICAL_REVIEW_REQUIRED' if success else 'C11C_SENSITIVITY_CAMPAIGN_RETAINED__BLOCKED'
    a.write(out/'C11C_CAMPAIGN_REPORT.json',{'status':status,'cases':reports,
        'physical_acceptance':False,'baseline_manifest':R1_PIN,**SCOPE})
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,
        'C11BR1_manifest_sha256':R1_PIN,'files':inventory(out),**SCOPE})
    print('C11C_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if success else 2

if __name__=='__main__':
    raise SystemExit(main())
