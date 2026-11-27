#!/usr/bin/env python3
"""G7 paired controlled mechanical re-solves at T0 and evolved +1y.

Use the exact retained C11R1 instrumentation and a separate no-solve
assembly on the G6 deck. Two convergence tolerances on both endpoints
distinguish the small annual response from numerical iteration error.
No new time advance, no canonical T1, no natural exterior qualification.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c

G6_PIN='8f0b2e956640b95c55e38495de7b9abdf758df34a82ebe4c580650d5728c8b95'
G6_STATUS='G6_CONSERVATIVE_NODAL_FEEDBACK_PROJECTION_PASS__CONTROLLED_RESOLVE_REQUIRED'
G4_PIN='9207eefd69425a013a32e117a8f515b40682a269a0cf5495b238a87898af3747'
G5_PIN='48fbfb6d452840c0086517d557acb6d1cc76850d500c4225aae007f75aeeec14'
TOLS={'coarse':5e-10,'fine':5e-12}
MAX_ITER=500
FINE_SCREEN=1e-8
SIGNAL_RATIO=0.1
FIELDS=('velocity','strain_rate','tau_relative','reaction')
DECK=('regional.feg','regional_PRE.dat','controlled.bcs','runtime.control','regional_reporting_plates.dat')
C10_NAME='R6_THERMO_C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_NEW01'

def blob(p):
    x=p.read_bytes()
    return hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()

def run(exe,work,env):
    with (work/'run.log').open('x') as log:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o','run.time',str(exe)],
            cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,
            preexec_fn=a.limit,start_new_session=True)
        try: rc=proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait(); rc=124
    return rc,(work/'run.log').read_text()

def build(work,root,native,entry,subs,driver,assembly,env,loader):
    work.mkdir()
    src=root/native.VENDOR
    for n in native.STOCK: shutil.copyfile(src/n,work/n)
    (work/'MOD_Shells.f90').write_text(subs)
    (work/'SHELLS_g7.f90').write_text(entry)
    (work/'driver.f90').write_text(driver)
    shutil.copyfile(loader,work/'MOD_ArcanaRuntime.f90')
    names=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_g7.f90','driver.f90')
    compiler=native.COMPILER; lib=native.LIB
    exe=work/('assembly_only.exe' if assembly else 'solve.exe')
    cmd=[str(compiler),'-O0','-Mbackslash','-Kieee','-Mbounds',*names,
         '-L'+str(lib),'-Wl,-rpath,'+str(lib),'-llapack','-lblas','-o',exe.name]
    with (work/'build.log').open('x') as log:
        subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    a.write(work/'BUILD_IDENTITY.json',{'argv':cmd,'exe_sha256':a.sha(exe),
        'compiler_sha256':a.sha(compiler),'source_sha256':{n:a.sha(work/n) for n in names},
        'library_sha256':{n:a.sha(lib/n) for n in ('liblapack.so','libblas.so')}})
    return exe

def stage(work,deck,native,controls):
    work.mkdir()
    for n in DECK: shutil.copyfile(deck/n,work/n)
    (work/'regional.in').write_text(native.serialize_lr(controls))

def controls_readback(log,controls):
    rows=[l.split()[1:] for l in log.splitlines() if l.startswith('G7_CONTROLS ')]
    expected=[controls['maxItr'],controls['okToQt'],controls['okDelV'],controls['Biot'],controls['zBAsth']]
    a.need(len(rows)==1 and len(rows[0])==5 and np.allclose(np.array(rows[0],float),
        expected,rtol=1e-13,atol=0),'G7_NATIVE_CONTROLS')

def maxabs(x):
    return float(np.max(np.abs(x)))

def response(bc,ec,bf,ef):
    # Difference of paired solutions at two tolerances. The sum of endpoint
    # changes is a conservative numerical sensitivity indicator, not a bound.
    dc=ec-bc; df=ef-bf
    signal=maxabs(df); scale=max(maxabs(bf),maxabs(ef),np.finfo(float).tiny)
    endpoint=maxabs(bf-bc)+maxabs(ef-ec)
    delta_change=maxabs(df-dc)
    noise=max(endpoint,delta_change,64*np.finfo(float).eps*scale)
    return {'annual_signal_absolute_max':signal,'annual_signal_relative_max':signal/scale,
        'coarse_annual_signal_absolute_max':maxabs(dc),
        'paired_delta_refinement_absolute_max':delta_change,
        'endpoint_refinement_sum_absolute_max':endpoint,
        'numerical_sensitivity_indicator_absolute_max':noise,
        'indicator_over_signal':noise/signal if signal>0 else None,
        'resolved_at_provisional_screen':bool(signal>0 and noise<=SIGNAL_RATIO*signal)}

def selftest():
    x=np.array([1.,2.])
    y=x+np.array([1e-5,-1e-5])
    a.need(response(x,y,x+1e-9,y-1e-9)['resolved_at_provisional_screen'],'RESOLVED_FIXTURE')
    a.need(not response(x,x,x,x)['resolved_at_provisional_screen'],'ZERO_SIGNAL_FIXTURE')
    a.need(not response(x,y,x,y+1e-5)['resolved_at_provisional_screen'],'UNRESOLVED_FIXTURE')
    print('G7_RESPONSE_SELFTEST_PASS',flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorize-controlled-resolve',choices=[a.SCENARIO],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    selftest()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    here=Path(__file__).resolve().parent
    a.need(a.sha(here/'arcana_c11a_assembly.py')==r1.A_SCRIPT_PIN and
        a.sha(here/'arcana_c11br1_convergence.py')==c.R1_SCRIPT and
        blob(here/'arcana_c11c_sensitivity.py')=='822ea9f80d4c1b1a0f820f8e6c2d44b9073dd41b','HELPER_PINS')
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA
        and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    g6=c10.OUT.with_name('R6_THERMO_G6_FEEDBACK_PROJECTION_NEW01')
    g4=c10.OUT.with_name('R6_THERMO_G4_CONTROLLED_TRANSPORT_NEW01')
    g5=c10.OUT.with_name('R6_THERMO_G5_COLUMN_HEAT_NEW01')
    assembly0=c10.OUT.with_name('R6_THERMO_C11A_OPERATOR_ASSEMBLY_NEW01')
    base=c10.OUT.with_name('R6_THERMO_C11BR1_CONVERGENCE_NEW01')
    gm=c.verified(g6,G6_PIN,G6_STATUS)
    c.verified(g4,G4_PIN,'G4_CONTROLLED_MOVING_COLUMN_TRANSPORT_PASS__PHYSICAL_ACCEPTANCE_PENDING')
    c.verified(g5,G5_PIN,'G5_CONTROLLED_COLUMN_HEAT_UPDATE_PASS__THERMOMECHANICAL_FEEDBACK_PENDING')
    c.verified(assembly0,r1.A_PIN,r1.A_STATUS); c.verified(base,c.R1_PIN,c.R1_STATUS)
    a.need(gm['source_sha']==a.SHA and gm['G4_manifest_sha256']==G4_PIN and
        gm['G5_manifest_sha256']==G5_PIN and gm['additional_native_solves']==0 and
        all(gm[k]==v for k,v in c.SCOPE.items()),'G6_LINEAGE')
    gr=a.read(g6/'G6_REPORT.json')
    a.need(gr['projection']['screen_pass'] and gr['native_probe']['status']=='PASS','G6_SCREEN')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(cm[k]==v for k,v in c10.SCOPE.items()),'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    for n in DECK[2:]: a.need(a.sha(g6/n)==a.sha(c10.OUT/n),'G6_BOUNDARY_DRIFT:'+n)
    package=a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    p0=parse_feg((c10.OUT/'regional.feg').read_text(),mode='SHELLS_READY')
    p1=parse_feg((g6/'regional.feg').read_text(),mode='SHELLS_READY')
    a.need(p0.elements==p1.elements and p0.faults==p1.faults and len(p1.nodes)==81 and
           all(x.node_id==y.node_id and x.elevation_m==y.elevation_m for x,y in zip(p0.nodes,p1.nodes,strict=True)),'GEOMETRY_TOPOLOGY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in
        (root,g6,g4,g5,assembly0,base,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G6_manifest':G6_PIN,'runner_sha256':a.sha(Path(__file__)),
        'native_tolerances':TOLS,'maxItr':MAX_ITER,'fine_residual_work_stress_screen':FINE_SCREEN,
        'signal_numerical_sensitivity_ratio':SIGNAL_RATIO,'max_native_solve_runs':4,
        'wall_s_per_run':120,'native_address_space_bytes':1073741824,
        'comparison_frame':'Same parent local south/east tangent components and native element/IP ordering; rotation and geometry change included in response.',
        'limitations':'Numerical refinement indicator is not a rigorous forward-error bound. No thermal projection or constitutive-model uncertainty inferred.',**c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    src=root/native.VENDOR
    entry=(src/'SHELLS_v5.0.f90').read_text(); subs=(src/'MOD_Shells.f90').read_text()
    driver=Path(native.__file__).with_name('c10_pre_solve_driver.f90').read_text()
    key='  if (Biot/=1d0 .and. Biot/=0d0) stop 16'
    driver=a.replace1(driver,key,key+'''
  print '(A,I6,4(1X,ES26.17E3))','G7_CONTROLS ',maxItr,okToQt,okDelV,Biot,zBAsth
''')
    loader=c10.OUT/'MOD_ArcanaRuntime.regional.f90'
    controls=dict(package['lr_native_parameters'],maxItr=MAX_ITER,okToQt=TOLS['fine'])
    results={}; attempted=0
    try:
        # Independent first assembly for the evolved deck. Use G6 native
        # pre-solve readback as reference, not a self-generated matrix.
        print('G7_EVOLVED_ASSEMBLY',flush=True)
        asmexe=build(out/'assembly_build',root,native,a.gen_entry(entry,native),
            a.gen_subs(subs),driver,True,env,loader)
        asm=out/'evolved'/'reference'
        asm.parent.mkdir()
        stage(asm,g6,native,controls)
        rc,log=run(asmexe,asm,env)
        a.need(rc==0 and 'C11A_STOP_AFTER_VBCS_BEFORE_SOLVER' in log
            and not (asm/'FatalError.txt').exists(),'EVOLVED_ASSEMBLY_STOP')
        controls_readback(log,controls)
        # a.analyse expects the historical C10 relative probe layout.
        # Explicit isolated adapter directory with the verified G6 probe.
        probe=out/'evolved'/'probe_reference'/'native_pre_solve'/'hydrostatic'
        probe.mkdir(parents=True)
        shutil.copyfile(g6/'native_pre_solve.txt',probe/'native_pre_solve.txt')
        ar=a.analyse(asm,probe.parent.parent)
        a.need(ar['rank_screen_pass'] and ar['initial_velocity_max_m_s']==0,'EVOLVED_RANK')
        a.write(asm/'ASSEMBLY_ANALYSIS.json',ar)
        # C11R1 analysis expects a sibling package under the C10 name.
        # Store per-endpoint coordinate views to prevent using stale geometry.
        # Both are analysis-only, not new C10 authority.
        (out/'baseline').mkdir()
        ref0=out/'baseline'/'reference'; ref0.mkdir()
        shutil.copyfile(assembly0/'C11_MATRICES.npz',ref0/'C11_MATRICES.npz')
        for name,mesh,deck,ref in [('baseline',p0,c10.OUT,ref0),('evolved',p1,g6,asm)]:
            folder=out/name
            view=copy.deepcopy(package)
            for item,node in zip(view['G4_mapping']['nodes'],mesh.nodes,strict=True):
                a.need(item['local_id']==node.node_id,'MAPPING_LOCAL_ID')
                item['runtime_lat_lon_deg']=[node.latitude_deg,node.longitude_deg]
            vp=folder/C10_NAME; vp.mkdir()
            a.write(vp/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',view)
            a.write(folder/'ANALYSIS_VIEW_PROVENANCE.json',{'source_deck':str(deck),
                'purpose':'C11R1 torque-frame compatibility only; not C10 authority.',
                'feg_sha256':a.sha(deck/'regional.feg'),'reference_matrix_sha256':a.sha(ref/'C11_MATRICES.npz')})
        e,s=r1.native_sources(entry,subs,a,native)
        exe=build(out/'solve_build',root,native,e,s,driver,False,env,loader)
        r1.MAX_ITER=MAX_ITER
        for label,tol in TOLS.items():
            for name,deck,ref in [('baseline',c10.OUT,ref0),('evolved',g6,asm)]:
                print('G7_CASE',name,label,flush=True)
                w=out/name/label
                ctl=dict(controls,okToQt=tol)
                stage(w,deck,native,ctl)
                attempted+=1
                try:
                    rc,log=run(exe,w,env)
                    a.need(rc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log
                        and not (w/'FatalError.txt').exists(),'NATIVE_STOP:'+str(rc))
                    controls_readback(log,ctl)
                    r1.NATIVE_TOL=tol
                    r=r1.analysis(w,ref,a)
                    fine=max(r[k] for k in ('final_free_relative_residual','work_balance_relative_defect',
                                            'stress_refresh_relative_max_component'))<=FINE_SCREEN
                    a.write(w/'MECHANICAL_ANALYSIS.json',r)
                    summary={'screen_pass':bool(r['screen_pass'] and (label!='fine' or fine)),
                        'native_scoreB':r['native_final_scoreB'],'iterations':len(r['iterations']),
                        'max_linear_backward':max(x['linear_backward_error'] for x in r['iterations']),
                        'residual':r['final_free_relative_residual'],'work_defect':r['work_balance_relative_defect'],
                        'stress_refresh':r['stress_refresh_relative_max_component'],
                        'free_cond2':r['final_free_rank']['cond2'],'power_W':r['quadrature_power_W'],
                        'fine_residual_screen':fine}
                except Exception as exc:
                    summary={'screen_pass':False,'error':repr(exc),'traceback':traceback.format_exc(),
                        'completed_linear_solves':len(list(w.glob('iter_*_solution.dat')))}
                results[name+'_'+label]=summary
                print(json.dumps({name+'_'+label:summary},allow_nan=False),flush=True)
        numerical=len(results)==4 and all(r['screen_pass'] for r in results.values())
        comparisons={}
        if numerical:
            paths=[out/n/l/'C11B_FINAL_STATE.npz' for l in TOLS for n in ('baseline','evolved')]
            from contextlib import ExitStack
            with ExitStack() as stack:
                bc,ec,bf,ef=[stack.enter_context(np.load(p)) for p in paths]
                for f in FIELDS:
                    arrays=[v[f] for v in (bc,ec,bf,ef)]
                    a.need(all(x.shape==arrays[0].shape and np.isfinite(x).all() for x in arrays),'FIELD_INVENTORY:'+f)
                    comparisons[f]=response(*arrays)
                np.savez(out/'PAIRED_ANNUAL_RESPONSE.npz',**{f:ef[f]-bf[f] for f in FIELDS})
        resolved=numerical and all(v['resolved_at_provisional_screen'] for v in comparisons.values())
        status=('G7_CONTROLLED_ENDPOINT_RESOLVES_PASS__ANNUAL_RESPONSE_RESOLVED__COUPLED_RESTART_PENDING' if resolved
                else 'G7_CONTROLLED_ENDPOINT_RESOLVES_PASS__ANNUAL_RESPONSE_UNRESOLVED' if numerical
                else 'G7_CONTROLLED_RESOLVE_BLOCKED')
        error=None
    except Exception as exc:
        numerical=False; resolved=False; comparisons={}
        status='G7_CONTROLLED_RESOLVE_BLOCKED'
        error={'error':repr(exc),'traceback':traceback.format_exc()}
    report={'status':status,'numerical_screen_pass':numerical,'annual_response_screen_pass':resolved,
        'cases':results,'paired_response':comparisons,'additional_native_solve_runs_attempted':attempted,
        'additional_time_advance_years':0,'physical_acceptance':False,'error':error,
        'limitations':['Controlled local Dirichlet components unchanged, natural exterior unresolved.',
            'G6 cubic projection and numerical viscosity regularization uncertainty not removed by paired solve.',
            'Resolved refers only to numerical tolerance sensitivity, not to physical predictive accuracy.',
            'No coupled restart or new thermal advance, no canonical T1.'],**c.SCOPE}
    a.need(c.inventory(g6)==gm['files'] and a.sha(g6/'MANIFEST.json')==G6_PIN,'G6_MUTATION')
    a.write(out/'G7_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G6_manifest_sha256':G6_PIN,
        'additional_native_solve_runs_attempted':attempted,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G7_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if resolved else 2

if __name__=='__main__':
    raise SystemExit(main())
