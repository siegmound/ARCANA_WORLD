#!/usr/bin/env python3
"""G7R1: two extra endpoint solves, using the exact verified G7 executable.
Retain all G7 archives, refs, and thresholds. No new time advance.
"""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_g7_paired_resolve as g7

G7_PIN='2316a0a115f6a5e4d41a4c87096ed65f105e6c586d226f440cbf748b2385b9d6'
G7_STATUS='G7_CONTROLLED_ENDPOINT_RESOLVES_PASS__ANNUAL_RESPONSE_UNRESOLVED'
ULTRA=5e-14
MAX_ITER=g7.MAX_ITER

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorize-controlled-resolve',choices=[a.SCENARIO],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    g7.selftest()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    here=Path(__file__).resolve().parent
    a.need(a.sha(here/'arcana_c11a_assembly.py')==r1.A_SCRIPT_PIN and
        a.sha(here/'arcana_c11br1_convergence.py')==c.R1_SCRIPT and
        g7.blob(here/'arcana_c11c_sensitivity.py')=='822ea9f80d4c1b1a0f820f8e6c2d44b9073dd41b' and
        g7.blob(here/'arcana_g7_paired_resolve.py')=='35d92094bf82e2b77ca54147f185c10833c8d858','HELPER_PINS')
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    parent=c10.OUT.with_name('R6_THERMO_G7_PAIRED_RESOLVE_NEW01')
    g6=c10.OUT.with_name('R6_THERMO_G6_FEEDBACK_PROJECTION_NEW01')
    pm=c.verified(parent,G7_PIN,G7_STATUS)
    gm=c.verified(g6,g7.G6_PIN,g7.G6_STATUS)
    a.need(pm['source_sha']==a.SHA and pm['G6_manifest_sha256']==g7.G6_PIN and
        pm['additional_native_solve_runs_attempted']==4 and all(pm[k]==v for k,v in c.SCOPE.items()),'G7_LINEAGE')
    pr=a.read(parent/'G7_REPORT.json')
    a.need(pr['numerical_screen_pass'] is True and pr['annual_response_screen_pass'] is False and
        set(pr['cases'])=={'baseline_coarse','baseline_fine','evolved_coarse','evolved_fine'} and
        all(v['screen_pass'] for v in pr['cases'].values()) and pr['error'] is None,'G7_SCREEN')
    policy=a.read(parent/'POLICY.json')
    a.need(policy['native_tolerances']==g7.TOLS and policy['maxItr']==MAX_ITER and
        policy['fine_residual_work_stress_screen']==g7.FINE_SCREEN and
        policy['signal_numerical_sensitivity_ratio']==g7.SIGNAL_RATIO,'G7_POLICY')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(cm[k]==v for k,v in c10.SCOPE.items()),'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    # Reuse exact binary, not a subtly different rebuild. Verify both its
    # archived provenance and the current compiler/library identities.
    build=parent/'solve_build'
    ident=a.read(build/'BUILD_IDENTITY.json')
    exe0=build/'solve.exe'
    a.need(a.sha(exe0)==ident['exe_sha256'] and
        all(a.sha(build/n)==h for n,h in ident['source_sha256'].items()) and
        a.sha(native.COMPILER)==ident['compiler_sha256'] and
        all(a.sha(native.LIB/n)==h for n,h in ident['library_sha256'].items()),'NATIVE_BUILD_IDENTITY')
    package=a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    controls=dict(package['lr_native_parameters'],maxItr=MAX_ITER,okToQt=ULTRA)
    oldctl=dict(controls,okToQt=g7.TOLS['fine'])
    for name,deck in [('baseline',c10.OUT),('evolved',g6)]:
        w=parent/name/'fine'
        a.need((w/'regional.in').read_bytes()==native.serialize_lr(oldctl).encode() and
            all(a.sha(w/n)==a.sha(deck/n) for n in g7.DECK),'RETAINED_DECK:'+name)
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in
        (root,parent,g6,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G7_manifest':G7_PIN,'G6_manifest':g7.G6_PIN,
        'runner_sha256':a.sha(Path(__file__)),'reused_executable_sha256':ident['exe_sha256'],
        'previous_tolerance':g7.TOLS['fine'],'new_tolerance':ULTRA,'maxItr':MAX_ITER,
        'max_additional_native_solve_runs':2,'additional_builds':0,
        'unchanged_fine_residual_screen':g7.FINE_SCREEN,'unchanged_signal_ratio':g7.SIGNAL_RATIO,
        'wall_s_per_run':120,'native_address_space_bytes':1073741824,
        'note':'Refinement indicator is empirical, not a rigorous error bound. Original G7 unresolved result preserved.',**c.SCOPE})
    exe=out/'solve.exe'; shutil.copy2(exe0,exe)
    a.need(a.sha(exe)==ident['exe_sha256'],'EXECUTABLE_COPY')
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    r1.MAX_ITER=MAX_ITER; r1.NATIVE_TOL=ULTRA
    reports={}; attempted=0
    for name,deck in [('baseline',c10.OUT),('evolved',g6)]:
        print('G7R1_CASE',name,flush=True)
        folder=out/name; folder.mkdir()
        ref=folder/'reference'; ref.mkdir()
        shutil.copyfile(parent/name/'reference/C11_MATRICES.npz',ref/'C11_MATRICES.npz')
        view=folder/g7.C10_NAME; view.mkdir()
        shutil.copyfile(parent/name/g7.C10_NAME/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',
            view/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
        work=folder/'ultra'
        g7.stage(work,deck,native,controls)
        attempted+=1
        try:
            rc,log=g7.run(exe,work,env)
            a.need(rc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log and
                not (work/'FatalError.txt').exists(),'NATIVE_STOP:'+str(rc))
            g7.controls_readback(log,controls)
            report=r1.analysis(work,ref,a)
            fine=max(report[k] for k in ('final_free_relative_residual','work_balance_relative_defect',
                'stress_refresh_relative_max_component'))<=g7.FINE_SCREEN
            a.write(work/'MECHANICAL_ANALYSIS.json',report)
            summary={'screen_pass':bool(report['screen_pass'] and fine),
                'iterations':len(report['iterations']),'native_scoreB':report['native_final_scoreB'],
                'residual':report['final_free_relative_residual'],'work_defect':report['work_balance_relative_defect'],
                'stress_refresh':report['stress_refresh_relative_max_component'],
                'free_cond2':report['final_free_rank']['cond2'],'power_W':report['quadrature_power_W'],
                'max_linear_backward':max(v['linear_backward_error'] for v in report['iterations'])}
        except Exception as exc:
            summary={'screen_pass':False,'error':repr(exc),'traceback':traceback.format_exc(),
                'completed_linear_solves':len(list(work.glob('iter_*_solution.dat')))}
        reports[name]=summary
        print(json.dumps({name:summary},allow_nan=False),flush=True)
    numerical=all(v['screen_pass'] for v in reports.values())
    compare={}
    if numerical:
        with ExitStack() as stack:
            bf,ef,bu,eu=[stack.enter_context(np.load(p)) for p in (
                parent/'baseline/fine/C11B_FINAL_STATE.npz',parent/'evolved/fine/C11B_FINAL_STATE.npz',
                out/'baseline/ultra/C11B_FINAL_STATE.npz',out/'evolved/ultra/C11B_FINAL_STATE.npz')]
            for f in g7.FIELDS:
                arrays=[v[f] for v in (bf,ef,bu,eu)]
                a.need(all(x.shape==arrays[0].shape and np.isfinite(x).all() for x in arrays),'FIELD_INVENTORY:'+f)
                compare[f]=g7.response(*arrays)
                compare[f]['previous_indicator_over_signal']=pr['paired_response'][f]['indicator_over_signal']
                compare[f]['paired_delta_refinement_over_signal']=(
                    compare[f]['paired_delta_refinement_absolute_max']/compare[f]['annual_signal_absolute_max']
                    if compare[f]['annual_signal_absolute_max']>0 else None)
            np.savez(out/'PAIRED_ANNUAL_RESPONSE.npz',**{f:eu[f]-bu[f] for f in g7.FIELDS})
    resolved=numerical and all(v['resolved_at_provisional_screen'] for v in compare.values())
    status=('G7R1_ANNUAL_RESPONSE_NUMERICAL_SCREEN_PASS__COUPLED_RESTART_REQUIRED' if resolved else
            'G7R1_ENDPOINT_RESOLVES_PASS__ANNUAL_RESPONSE_UNRESOLVED' if numerical else
            'G7R1_CONTROLLED_RESOLVE_BLOCKED')
    for path,m,pin in ((parent,pm,G7_PIN),(g6,gm,g7.G6_PIN)):
        a.need(c.inventory(path)==m['files'] and a.sha(path/'MANIFEST.json')==pin,'PARENT_MUTATION')
    report={'status':status,'numerical_screen_pass':numerical,'annual_response_screen_pass':resolved,
        'cases':reports,'paired_response':compare,'additional_native_solve_runs_attempted':attempted,
        'additional_builds':0,'additional_time_advance_years':0,'physical_acceptance':False,
        'limitations':['Empirical convergence refinement only; not a rigorous error bound.',
            'Thermal projection, viscosity regularization and natural exterior uncertainty remain.',
            'No coupled continuation, no canonical T1.'],**c.SCOPE}
    a.write(out/'G7R1_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G7_manifest_sha256':G7_PIN,
        'G6_manifest_sha256':g7.G6_PIN,'additional_native_solve_runs_attempted':attempted,
        'additional_builds':0,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G7R1_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if resolved else 2

if __name__=='__main__':
    raise SystemExit(main())
