#!/usr/bin/env python3
"""G15 explicit midpoint coupling of quasi-static mechanics and heat.

One predicted midpoint solve, then recompute the full interval from the
original authoritative state using its midpoint ambient velocity. Compare
one macrostep to two independently predicted halfsteps. Keep predictor
states distinct from accepted trajectory. Retain failed trials. No new
physics, event transition, or promotion.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g5_column_heat as g5
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g10b_consumer_resolve as b10
import arcana_g11_adaptive_pilot as g11
import arcana_g12_joint_profile_extended as g12
import arcana_g13_cn_multiscale as g13
import arcana_g14_adaptive_trajectory as g14

G14_PIN='cd1f3637b194107309af51e0658986eba3d976beb25b1bfec6004d941f5fbd4d'
G14_STATUS='G14_ADAPTIVE_REGIONAL_TRAJECTORY_PASS__EVENT_AND_SCALE_REQUIRED'
CP_PIN='e6b8f2e11027e2c64bb3fc1d2fab1fb045954f2372b71a7a1c7c243a3d621470'
START=112.
TARGET=162.
MAX_TRIALS=3
MAX_SOLVES=18
MIN_STEP=25.

def selftest():
    # Unit-sphere analytic test: autonomous angular speed 1+0.2*sin(angle).
    # Independent high-accuracy scalar IVP reference, not a test of ShellSet.
    from scipy.integrate import solve_ivp
    p=np.array([[1.,0.,0.]])
    def v(q):
        return (1.+.2*q[:,1,None])*np.column_stack((-q[:,1],q[:,0],np.zeros(len(q))))
    T=.004
    angle=solve_ivp(lambda t,y:1+.2*np.sin(y),[0,T],[0.],rtol=1e-13,atol=1e-15).y[0,-1]
    exact=np.array([[np.cos(angle),np.sin(angle),0.]])
    errors=[]
    for n in (1,2,4):
        q=p.copy(); dt=T/n
        for _ in range(n):
            mid=g14.flow(q,v(q),1.,dt/2)
            q=g14.flow(q,v(mid),1.,dt)
        errors.append(float(np.max(abs(q-exact))))
    a.need(errors[0]>3.5*errors[1] and errors[1]>3.5*errors[2],'MIDPOINT_ORDER_FIXTURE')
    print('G15_MIDPOINT_SELFTEST_PASS',errors,flush=True)

def ledger(st,end,segments):
    """Only accepted corrector paths contribute, never predictors."""
    old=st[2]['two_half_energy_increment_J']; new=end[2]['two_half_energy_increment_J']
    actual=float((new-old).sum())
    increments=[q['corrector']['refined']['thermal']['energy_increment_J'] for q in segments]
    residual=abs(actual-sum(increments))/max(sum(abs(v) for v in increments),1.)
    return {'actual_increment_J':actual,'corrector_increment_J':sum(increments),
        'relative_closure':residual,'predictor_energy_counted':False,
        'screen_pass':bool(residual<=g11.TOL['energy_budget_relative'])}

def step(folder,cp,pin,years,steps,probe,asm,exe,native,ctl,env,report):
    folder.mkdir(); st=g11.load(cp,pin); s,z,th,v=st
    year=z['elapsed_years']; result={'years':years,'start_year':year,'screen_pass':False}
    def finish(reason=None):
        if reason: result['reason']=reason
        a.write(folder/'STEP_REPORT.json',result)
        return result,None,None
    def solve(label,deck,vals,rows):
        report['native_solves_attempted']+=1
        a.need(report['native_solves_attempted']<=MAX_SOLVES,'SOLVE_BUDGET')
        return g11.mechanical(folder/(label+'_mechanics'),deck,cp,vals,rows,probe,asm,exe,native,ctl,env)
    if year+years>=z['event_horizon_year']: return finish('EVENT_HORIZON')
    # Midpoint predictor is a temporary state, never an accepted checkpoint.
    print('G15_PREDICTOR',folder.name,year,years/2,flush=True)
    e,t,r=g14.preflight(st,years/2,steps//2)
    result['predictor']=r
    if not r['screen_pass']: return finish('PREDICTOR_PREFLIGHT')
    d=folder/'predictor_deck'; pr,vals,rows=g12.project(cp,s,e,t,d)
    result['predictor_projection']=pr
    if not pr['screen_pass']: return finish('PREDICTOR_PROJECTION')
    mr,ms=solve('predictor',d,vals,rows)
    result['predictor_mechanics']=mr
    if not mr['screen_pass']: return finish('PREDICTOR_MECHANICS')
    with np.load(ms) as f: vm=g8.velocity(e,(d/'regional.feg').read_text(),f)
    result['midpoint_velocity_max_change_m_s']=g7.maxabs(vm-v)
    # Recompute from exactly the original material and thermal state.
    # Ambient vector is expressed in a common canonical frame; the analytic
    # flow projects it on the sphere throughout the interval.
    print('G15_CORRECTOR',folder.name,year,years,flush=True)
    end,thermal,cr=g14.preflight((s,z,th,vm),years,steps)
    result['corrector']=cr
    if not cr['screen_pass']: return finish('CORRECTOR_PREFLIGHT')
    d=folder/'corrector_deck'; pr,vals,rows=g12.project(cp,s,end,thermal,d)
    result['corrector_projection']=pr
    if not pr['screen_pass']: return finish('CORRECTOR_PROJECTION')
    mr,ms=solve('corrector',d,vals,rows)
    result['corrector_mechanics']=mr
    if not mr['screen_pass']: return finish('CORRECTOR_MECHANICS')
    nxt=folder/'checkpoint_endpoint'
    npin=g11.checkpoint(cp,d,ms,nxt,year+years,
        {'parent':pin,'integrator':'G15_EXPLICIT_MIDPOINT','predictor_only':False,
         'macro_years':years})
    result['energy_ledger']=ledger(st,g11.load(nxt,npin),[result])
    if not result['energy_ledger']['screen_pass']: return finish('ENERGY_LEDGER')
    result.update(screen_pass=True,checkpoint_sha256=npin)
    a.write(folder/'STEP_REPORT.json',result)
    return result,nxt,npin

def trial(folder,cp,pin,years,probe,asm,exe,native,ctl,env,report):
    folder.mkdir(); st=g11.load(cp,pin)
    year=st[1]['elapsed_years']; result={'years':years,'start_year':year,'screen_pass':False}
    def finish(reason=None):
        if reason: result['reason']=reason
        a.write(folder/'TRIAL_REPORT.json',result)
        return result
    args=(probe,asm,exe,native,ctl,env,report)
    # Matched CN grids: eight corrector updates per full step, four per half.
    r,coarse,cpin=step(folder/'coarse',cp,pin,years,8,*args)
    result['coarse']=r
    if not r['screen_pass']: return finish('COARSE:'+r['reason'])
    current=cp; curpin=pin; segments=[]
    for i in (1,2):
        r,nxt,npin=step(folder/f'half_{i}',current,curpin,years/2,4,*args)
        result[f'half_{i}']=r
        if not r['screen_pass']: return finish('HALF:'+str(i)+':'+r['reason'])
        segments.append(r); current,curpin=nxt,npin
    end=g11.load(current,curpin)
    cmp=g11.compare(st,g11.load(coarse,cpin),end)
    fields=g11.field_compare(cp,coarse,current)
    en=ledger(st,end,segments)
    result.update(coupling_comparison=cmp,mechanical_fields=fields,accepted_path_energy_ledger=en)
    result['screen_pass']=bool(cmp['screen_pass'] and en['screen_pass'] and all(x['screen_pass'] for x in fields.values()))
    if not result['screen_pass']: return finish('COUPLING_REFINEMENT')
    result.update(accepted_year=year+years,accepted_checkpoint=str(current.relative_to(folder)),
        accepted_checkpoint_sha256=curpin,accepted_midpoint_checkpoint='half_1/checkpoint_endpoint',
        accepted_midpoint_sha256=segments[0]['checkpoint_sha256'])
    return finish()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-midpoint-coupling',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); g8.check_helpers(); selftest()
    for n,p in [('arcana_g14_adaptive_trajectory.py','9b5e3d0fdac72cc5245a370e177f3bb0a7b11d7b'),('arcana_g13_cn_multiscale.py','d5711c9668539a284f165efd368879f1ab93c77e'),('arcana_g11_adaptive_pilot.py','caafab6df23e7b9a51e6463a435c1013d83ff173'),
        ('arcana_g12_joint_profile_extended.py','9f00582e7948635bdac23b4e65584fe5291a0e7b'),
        ('arcana_g10r1_thermal_consumer.py','63178aa33312c1be425a9c52eb945f762a2c1349'),
        ('arcana_g10b_consumer_resolve.py','837f5102b8216226c15d255961e5f6c862795469'),
        ('arcana_g8_staggered_restart.py','0fd003aeb5a52e59ad33550eaa740e363a582b59')]:
        a.need(g7.blob(Path(__file__).with_name(n))==p,'HELPER_PIN:'+n)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g14','R6_THERMO_G14_ADAPTIVE_TRAJECTORY_NEW01',G14_PIN,G14_STATUS),
          ('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',g11.B_PIN,g11.B_STATUS),
          ('t','R6_THERMO_G10R1_THERMAL_CONSUMER_NEW01',b10.G10R1_PIN,b10.G10R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g14']; prior=a.read(p/'G14_REPORT.json')
    a.need(prior['screen_pass'] and prior['accepted_checkpoint_sha256']==CP_PIN and
        prior['accepted_experimental_elapsed_years']==START and manifests['g14']['G13_manifest_sha256']==g14.G13_PIN,'G14_LINEAGE')
    cp=p/prior['accepted_checkpoint']; start=g11.load(cp,CP_PIN); s,z,th,v=start
    m=g5.setup(s,64); old=th['two_half_energy_increment_J']
    for k,key in [('mass','mass_kg'),('heat','initial_energy_J'),('capacity','heat_capacity_J_K'),('temp0','initial_temperature_K')]:
        a.need(g5.rel(m[k],th[key])<=1e-14,'THERMAL_REFERENCE:'+key)
    a.need(z['elapsed_years']==START and g5.rel(m['temp0']+old/m['capacity'],th['two_half_temperature_K'])<=1e-14,'THERMAL_CHECKPOINT')
    cm=a.read(c10.OUT/'MANIFEST.json'); a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    probe=g8.binary(parents['t']/'build','probe.exe',native)
    asm=g8.binary(parents['b']/'assembly_build','assembly_only.exe',native)
    exe=g8.binary(parents['b']/'solve_build','solve.exe',native)
    for q in (parents['b']/'assembly_build',parents['b']/'solve_build'):
        a.need(a.sha(q/'MOD_ArcanaRuntime.f90')==a.sha(parents['t']/'build/MOD_ArcanaRuntime.f90'),'LOADER_LINEAGE')
    ctl=dict(a.read(cp/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
    a.need((cp/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(q) for q in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.need(prior['legacy_comparison']['screen_pass'] and len(prior['trials'])==3 and
        not prior['trials'][0]['screen_pass'] and prior['trials'][0]['reason']=='COUPLING_REFINEMENT' and
        all(r['screen_pass'] for r in prior['trials'][1:]),'G14_BACKOFF_LINEAGE')
    a.write(out/'POLICY.json',{'G14_manifest':G14_PIN,'checkpoint':CP_PIN,'runner_sha256':a.sha(Path(__file__)),
        'target_year':TARGET,'initial_macrostep_years':50.,'minimum_macrostep_years':MIN_STEP,
        'max_trials':MAX_TRIALS,'max_native_solves':MAX_SOLVES,'additional_builds':0,
        'method':'Explicit midpoint mechanical refresh; recompute from original state; matched midpoint CN',
        'predictor_policy':'Retained diagnostic only; excluded from accepted trajectory and energy ledger',
        'tolerances':g11.TOL,'thermal_tolerances':g5.TOL,**c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'native_solves_attempted':0,'additional_builds':0,'physical_acceptance':False,
        'trials':[],'accepted_experimental_elapsed_years':START,'additional_time_advance_years':0,**c.SCOPE}
    history=[{'elapsed_years':START,'archive_manifest_sha256':G14_PIN,'checkpoint_sha256':CP_PIN,
              'checkpoint':prior['accepted_checkpoint'],'external_parent':True}]
    accepted_increments=[]
    try:
        cur=cp; pin=CP_PIN; year=START; dt=50.
        for k in range(1,MAX_TRIALS+1):
            if year==TARGET: break
            dt=min(dt,TARGET-year)
            if dt<MIN_STEP or report['native_solves_attempted']+6>MAX_SOLVES: break
            folder=out/f'trial_{k:02d}'
            print('G15_TRIAL',k,year,dt,flush=True)
            r=trial(folder,cur,pin,dt,probe,asm,exe,native,ctl,env,report)
            report['trials'].append({'path':folder.name,**r})
            if r['screen_pass']:
                for i in (1,2):
                    seg=r[f'half_{i}']; entry=folder/f'half_{i}/checkpoint_endpoint'
                    history.append({'elapsed_years':year+i*dt/2,'checkpoint':str(entry.relative_to(out)),
                         'checkpoint_sha256':seg['checkpoint_sha256'],'parent_checkpoint_sha256':history[-1]['checkpoint_sha256'],
                         'external_parent':False})
                    accepted_increments.append(seg['corrector']['refined']['thermal']['energy_increment_J'])
                cur=folder/r['accepted_checkpoint']; pin=r['accepted_checkpoint_sha256']; year=r['accepted_year']
                report.update(accepted_experimental_elapsed_years=year,additional_time_advance_years=year-START,
                    accepted_checkpoint=str(cur.relative_to(out)),accepted_checkpoint_sha256=pin)
                print('G15_ACCEPT',year,flush=True)
            else:
                print('G15_REJECT',r['reason'],flush=True); dt/=2
        end=g11.load(cur,pin)
        actual=float((end[2]['two_half_energy_increment_J']-start[2]['two_half_energy_increment_J']).sum())
        closure=abs(actual-sum(accepted_increments))/max(sum(abs(x) for x in accepted_increments),1.)
        report['accepted_trajectory_energy_ledger']={'actual_increment_J':actual,
            'accepted_corrector_sum_J':sum(accepted_increments),'relative_closure':closure,
            'screen_pass':bool(closure<=g11.TOL['energy_budget_relative'])}
        report['screen_pass']=bool(year==TARGET and report['accepted_trajectory_energy_ledger']['screen_pass'])
    except Exception as exc:
        report['screen_pass']=False
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    a.write(out/'ACCEPTED_CHECKPOINT_INDEX.json',{'scope':'Experimental regional accepted endpoints only; not HistoryStore production',
        'entries':history,'campaign_screen_pass':report['screen_pass'],**c.SCOPE})
    for key,_,pin0,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin0,'PARENT_MUTATION:'+key)
    status='G15_MIDPOINT_COUPLING_PILOT_PASS__EVENT_AND_SCALE_REQUIRED' if report['screen_pass'] else 'G15_MIDPOINT_COUPLING_RETAINED__TARGET_NOT_QUALIFIED'
    report.update(status=status,limitations=[
        'Explicit midpoint is second-order for smooth reduced ODE under exact stage solves; actual coupled order not established by a two-level screen.',
        'The predictor is not a historical state; only accepted corrector endpoints enter the experimental index.',
        'Fixed regional boundary scenario, passive parcel geometry, fixed heat capacities and native vertical quadrature remain.',
        'Maximum 50-year macrostep, no event transition, no global dynamics or canonical T1.'])
    a.write(out/'G15_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G14_manifest_sha256':G14_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G15_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
