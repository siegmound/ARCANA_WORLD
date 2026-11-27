#!/usr/bin/env python3
"""G10B: paired full mechanical solves with zero and corrected G10R1 sidecar.

Same G9 year2 deck, exact archived G7 instrumentation, new verified loader.
Reuse G10R1 presolve references, assemble both operators, compare against
retained G9 solution and annual mechanical response. No time advancement.
"""
import argparse
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
import arcana_g8_staggered_restart as g8

G10R1_PIN='fe7a3ba7ef0c66f5c69a2817b16c9741e8f830fb8be06bd501808f1ec70c1e3d'
G10R1_STATUS='G10R1_C1_THERMAL_CONSUMER_SCREEN_PASS__RESOLVE_SENSITIVITY_REQUIRED'
G9_PIN='d900b3aa3dcc38241f298ee30182c068cb089bd7e104aebacb57ed3902b8cfb0'
G9_STATUS='G9_COUPLING_STEP_HALVING_SCREEN_PASS__THERMAL_CONSUMER_UPGRADE_REQUIRED'
G9_CP='df6d932f19f1159dad1f42bb8365cdac940ecc398bfe513fed8ecac3bcaeba30'
YEAR1_PIN='f95eff297b77826d3069beedcbb58dc689894bae08b4ebd44ee116115d4930d4'
G8_PIN='9b9583ee3fe27ec8e0aa16a6ae746fa0151b516e0e4bafdbf8a6a127bfcc254b'
G8_STATUS='G8_CONTROLLED_STAGGERED_CONTINUATION_RESTART_PASS__ADAPTIVE_COUPLING_PENDING'
SIDE='regional_thermal_correction.dat'
ZERO_LIMIT=1e-12
ANNUAL_LIMIT=g7.SIGNAL_RATIO

def field_metrics(start,old,zero,new,indicator):
    a.need(start.shape==old.shape==zero.shape==new.shape and
        all(np.isfinite(v).all() for v in (start,old,zero,new)),'FIELD_INVENTORY')
    signal=g7.maxabs(old-start)
    scale=max(g7.maxabs(old),g7.maxabs(zero),g7.maxabs(new),np.finfo(float).tiny)
    drift=g7.maxabs(zero-old); effect=g7.maxabs(new-zero)
    a.need(signal>0,'ZERO_ANNUAL_REFERENCE')
    # Historical G7R1 empirical indicator is only context, not a certified
    # uncertainty bound for this different endpoint or updated consumer.
    return {'zero_replay_exact':bool(np.array_equal(zero,old)),
        'zero_replay_relative':drift/scale,'zero_replay_screen':drift/scale<=ZERO_LIMIT,
        'correction_absolute_max':effect,'correction_relative_to_field':effect/scale,
        'retained_annual_signal_absolute_max':signal,'correction_over_annual_signal':effect/signal,
        'historical_G7R1_numerical_indicator_absolute_max':indicator,
        'correction_over_historical_indicator':effect/indicator if indicator>0 else None,
        'compatibility_screen':effect<=ANNUAL_LIMIT*signal}

def selftest():
    x=np.array([1.,2.]); old=x+1e-4
    good=field_metrics(x,old,old,old+1e-6,1e-8)
    bad=field_metrics(x,old,old+1e-3,old+1e-3,1e-8)
    large=field_metrics(x,old,old,old+2e-5,1e-8)
    a.need(good['zero_replay_screen'] and good['compatibility_screen'] and
           not bad['zero_replay_screen'] and not large['compatibility_screen'],'METRIC_FIXTURES')
    print('G10B_METRICS_SELFTEST_PASS',flush=True)

def stage(work,cp,source,native,ctl):
    g7.stage(work,cp,native,ctl)
    shutil.copyfile(source/SIDE,work/SIDE)
    a.need(a.sha(work/SIDE)==a.sha(source/SIDE),'SIDECAR_COPY')

def case(folder,cp,source,view,asmexe,solveexe,native,ctl,env):
    folder.mkdir()
    probe=folder/'probe_reference/native_pre_solve/hydrostatic'
    probe.mkdir(parents=True)
    shutil.copyfile(source/'native_pre_solve.txt',probe/'native_pre_solve.txt')
    asm=folder/'reference'
    stage(asm,cp,source,native,ctl)
    rc,log=g7.run(asmexe,asm,env)
    a.need(rc==0 and 'C11A_STOP_AFTER_VBCS_BEFORE_SOLVER' in log and
        not (asm/'FatalError.txt').exists(),'ASSEMBLY_STOP:'+str(rc))
    g7.controls_readback(log,ctl)
    ar=a.analyse(asm,probe.parent.parent)
    a.need(ar['rank_screen_pass'] and ar['initial_velocity_max_m_s']==0,'ASSEMBLY_RANK')
    a.write(asm/'ASSEMBLY_ANALYSIS.json',ar)
    vdir=folder/g7.C10_NAME; vdir.mkdir()
    shutil.copyfile(view,vdir/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    work=folder/'ultra'; stage(work,cp,source,native,ctl)
    print('G10B_NATIVE_SOLVE',folder.name,flush=True)
    rc,log=g7.run(solveexe,work,env)
    a.need(rc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log and
        not (work/'FatalError.txt').exists(),'SOLVE_STOP:'+str(rc))
    g7.controls_readback(log,ctl)
    r1.MAX_ITER=g7.MAX_ITER; r1.NATIVE_TOL=g8.ULTRA
    r=r1.analysis(work,asm,a)
    a.write(work/'MECHANICAL_ANALYSIS.json',r)
    summary={'screen_pass':bool(r['screen_pass'] and max(r[k] for k in (
        'final_free_relative_residual','work_balance_relative_defect',
        'stress_refresh_relative_max_component'))<=g7.FINE_SCREEN),
        'iterations':len(r['iterations']),'native_scoreB':r['native_final_scoreB'],
        'residual':r['final_free_relative_residual'],'work_defect':r['work_balance_relative_defect'],
        'stress_refresh':r['stress_refresh_relative_max_component'],
        'power_W':r['quadrature_power_W'],'free_cond2':r['final_free_rank']['cond2'],
        'max_linear_backward':max(v['linear_backward_error'] for v in r['iterations'])}
    return summary,work/'C11B_FINAL_STATE.npz'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-thermal-consumer-resolve',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); selftest(); g8.check_helpers()
    a.need(g7.blob(Path(__file__).with_name('arcana_g8_staggered_restart.py'))==
           '0fd003aeb5a52e59ad33550eaa740e363a582b59','G8_RUNNER_PIN')
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
           not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g10','R6_THERMO_G10R1_THERMAL_CONSUMER_NEW01',G10R1_PIN,G10R1_STATUS),
          ('g9','R6_THERMO_G9_COUPLING_HALVING_NEW01',G9_PIN,G9_STATUS),
          ('g8','R6_THERMO_G8_STAGGERED_RESTART_NEW01',G8_PIN,G8_STATUS),
          ('g7','R6_THERMO_G7_PAIRED_RESOLVE_NEW01',g8.G7_PIN,g8.G7_STATUS),
          ('r1','R6_THERMO_G7R1_REFINE_RESPONSE_NEW01',g8.R1_PIN,g8.R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),
            'PARENT_SCOPE:'+key)
    p=parents['g10']; g9=parents['g9']; cp=g9/'checkpoint_year2_refined'
    start=parents['g8']/'checkpoint_year1'
    g8.open_checkpoint(cp,G9_CP); g8.open_checkpoint(start,YEAR1_PIN)
    pr=a.read(p/'G10R1_REPORT.json'); gr=a.read(g9/'G9_REPORT.json')
    rr=a.read(parents['r1']/'G7R1_REPORT.json')
    a.need(manifests['g10']['G9_manifest_sha256']==G9_PIN and pr['screen_pass'] and
        pr['projection']['screen_pass'] and all(v==0 for v in pr['native']['zero_sidecar_vs_original_relative'].values())
        and all(pr['native']['cases'][n]['screen_pass'] for n in ('zero','corrected')) and
        all(pr['native']['cases'][n]['rejected'] for n in ('missing','bad')) and
        gr['screen_pass'] and gr['refined_checkpoint_sha256']==G9_CP and
        rr['annual_response_screen_pass'],'SOURCE_SCREEN')
    a.need(g8.same_npz(cp/'mechanical.npz',g9/'refined_mechanics/ultra/C11B_FINAL_STATE.npz'),'G9_MECHANICAL_LINEAGE')
    for n in (*g7.DECK,'regional.in'):
        for name in ('zero','corrected'):
            a.need(a.sha(cp/n)==a.sha(p/name/n),'G10_DECK_DRIFT:'+name+':'+n)
    with np.load(p/'CORRECTIONS.npz') as f:
        values=f['values_K']
        a.need(values.shape==(81,2,64) and np.isfinite(values).all(),'CORRECTION_INVENTORY')
    for name,target in [('zero',np.zeros_like(values)),('corrected',values)]:
        side=p/name/SIDE
        a.need(side.read_text().splitlines()[0]=='ARCANA_G10_C1_RESIDUAL_V1 81 64','SIDECAR_HEADER')
        tab=np.loadtxt(side,skiprows=1)
        a.need(tab.shape==(162,66) and np.array_equal(tab[:,:2],np.array(
            [(i,j) for i in range(1,82) for j in (1,2)])) and
            np.array_equal(tab[:,2:].reshape(81,2,64),target),'SIDECAR_CONTENT')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    # Check the actual archived source, compiler, libraries and binary identities.
    g8.binary(p/'build','probe.exe',native)
    ab=parents['g7']/'assembly_build'; sb=parents['g7']/'solve_build'
    g8.binary(ab,'assembly_only.exe',native); oldexe=g8.binary(sb,'solve.exe',native)
    a.need(a.sha(oldexe)==a.sha(parents['r1']/'solve.exe'),'SOLVER_LINEAGE')
    loader=p/'build/MOD_ArcanaRuntime.f90'
    ctl=dict(a.read(cp/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
    a.need((cp/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
    view=g9/'refined_mechanics'/g7.C10_NAME/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json'
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(q) for q in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G10R1_manifest':G10R1_PIN,'G9_manifest':G9_PIN,'checkpoint':G9_CP,
        'runner_sha256':a.sha(Path(__file__)),'loader_sha256':a.sha(loader),
        'zero_replay_relative_limit':ZERO_LIMIT,'compatibility_over_annual_limit':ANNUAL_LIMIT,
        'native_tol':g8.ULTRA,'max_native_solves':2,'max_native_builds':2,
        'scope':'Paired engineering comparison; compatibility is not physical accuracy. Historical indicator not an error bound.',
        **c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'numerical_screen_pass':False,'compatibility_screen_pass':False,
        'additional_time_advance_years':0,'physical_acceptance':False,'cases':{},**c.SCOPE}
    try:
        exes=[]
        for key,b,is_assembly in [('assembly',ab,True),('solve',sb,False)]:
            print('G10B_BUILD',key,flush=True)
            work=out/(key+'_build')
            exe=g7.build(work,root,native,(b/'SHELLS_g7.f90').read_text(),
                (b/'MOD_Shells.f90').read_text(),(b/'driver.f90').read_text(),is_assembly,env,loader)
            # All build input sources other than the thermal loader must
            # remain byte-identical to the qualified G7 implementation.
            old=a.read(b/'BUILD_IDENTITY.json')['source_sha256']
            new=a.read(work/'BUILD_IDENTITY.json')['source_sha256']
            a.need(set(old)==set(new) and all(old[n]==new[n] for n in old if n!='MOD_ArcanaRuntime.f90')
                and new['MOD_ArcanaRuntime.f90']==a.sha(loader),'BUILD_SOURCE_DRIFT:'+key)
            exes.append(exe)
        states=[]
        for key in ('zero','corrected'):
            print('G10B_CASE',key,flush=True)
            res,state=case(out/key,cp,p/key,view,*exes,native,ctl,env)
            report['cases'][key]=res; states.append(state)
            print(json.dumps({key:res},allow_nan=False),flush=True)
        report['numerical_screen_pass']=all(v['screen_pass'] for v in report['cases'].values())
        fields={}
        with np.load(start/'mechanical.npz') as x,np.load(cp/'mechanical.npz') as old, \
            np.load(states[0]) as z,np.load(states[1]) as y:
            for f in g7.FIELDS:
                fields[f]=field_metrics(x[f],old[f],z[f],y[f],
                    rr['paired_response'][f]['numerical_sensitivity_indicator_absolute_max'])
            np.savez(out/'THERMAL_CONSUMER_RESPONSE.npz',**{f:y[f]-z[f] for f in g7.FIELDS})
        report['fields']=fields
        report['zero_replay_screen_pass']=all(v['zero_replay_screen'] for v in fields.values())
        report['compatibility_screen_pass']=all(v['compatibility_screen'] for v in fields.values())
        report['screen_pass']=bool(report['numerical_screen_pass'] and report['zero_replay_screen_pass']
            and report['compatibility_screen_pass'])
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and
            a.sha(parents[key]/'MANIFEST.json')==pin,'PARENT_MUTATION:'+key)
    status=('G10B_THERMAL_CONSUMER_MECHANICAL_COMPATIBILITY_PASS__ADAPTIVE_PILOT_PENDING'
            if report['screen_pass'] else
            'G10B_SOLVES_PASS__CONSUMER_RESPONSE_REVIEW_REQUIRED' if report['numerical_screen_pass']
            and report.get('zero_replay_screen_pass',False) else 'G10B_CONTROLLED_RESOLVE_BLOCKED')
    report.update(status=status,limitations=[
        'Comparison on a single retained year2 state; no new temporal evolution or tolerance sweep.',
        'The 10% annual-signal screen measures compatibility, not accuracy; a larger correction could be physically meaningful.',
        'Historical G7R1 sensitivity is contextual, not a certified error bound for G10B.',
        'No improvement claimed for native vertical quadrature or unresolved natural exterior.',
        'Adaptive continuation must retain authoritative cell temperatures and regenerate both PRE and sidecar; no canonical T1.'])
    a.write(out/'G10B_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G10R1_manifest_sha256':G10R1_PIN,
        'G9_manifest_sha256':G9_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G10B_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2

if __name__=='__main__': raise SystemExit(main())
