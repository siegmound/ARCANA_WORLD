#!/usr/bin/env python3
"""G9: matched thermal stepping, different mechanical refresh frequency.

Compare retained G8 year1->year2 (two thermal halfsteps with frozen year1
velocity) to two half-year coupled steps with midpoint mechanical refresh.
Reuse G8 helpers and archived native binaries. No new history beyond year2.
This is a two-level coupling sensitivity screen, not an order estimate,
a general adaptive integrator, or physical T1 authorization.
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
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g5_column_heat as g5
import arcana_g6_feedback_projection as g6
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8

G8_PIN='9b9583ee3fe27ec8e0aa16a6ae746fa0151b516e0e4bafdbf8a6a127bfcc254b'
G8_STATUS='G8_CONTROLLED_STAGGERED_CONTINUATION_RESTART_PASS__ADAPTIVE_COUPLING_PENDING'
YEAR1_PIN='f95eff297b77826d3069beedcbb58dc689894bae08b4ebd44ee116115d4930d4'
YEAR2_PIN='0954018b3d15c386e31890febe4e0fc2e17f092356d970448df7d28c36de879c'
G8_BLOB='0fd003aeb5a52e59ad33550eaa740e363a582b59'
TOL={'position_m':g4.TOL['halfstep_position_m'],
     'thickness_relative':g4.TOL['halfstep_thickness_relative'],
     'annual_mechanical_signal_fraction':g7.SIGNAL_RATIO,
     'energy_increment_relative':0.01,'energy_budget_relative':1e-11}
DT=.5

def maxabs(x):
    return float(np.max(abs(x)))

def response(initial,coarse,refined):
    """Global max norm; relative to the annual response, not total field."""
    a.need(initial.shape==coarse.shape==refined.shape and
           all(np.isfinite(v).all() for v in (initial,coarse,refined)),'FIELD_INVENTORY')
    d=refined-coarse
    signal=max(maxabs(coarse-initial),maxabs(refined-initial))
    err=maxabs(d)
    return {'max_endpoint_difference':err,'max_annual_signal':signal,
        'difference_over_annual_signal':err/signal if signal>0 else None,
        'screen_pass':bool(signal>0 and err<=TOL['annual_mechanical_signal_fraction']*signal)}

def selftest():
    x=np.array([1.,2.]); y=x+1e-5
    a.need(response(x,y,y+1e-8)['screen_pass'],'COUPLING_SMALL_FIXTURE')
    a.need(not response(x,y,y+2e-6)['screen_pass'],'COUPLING_LARGE_FIXTURE')
    a.need(not response(x,x,x)['screen_pass'],'COUPLING_ZERO_FIXTURE')
    print('G9_COUPLING_SELFTEST_PASS',flush=True)

def halfstep(cp,pin,out):
    s,z,th,v=g8.load_state(cp,pin)
    model=g5.setup(s,64)
    for k,key in [('mass','mass_kg'),('heat','initial_energy_J'),
                  ('capacity','heat_capacity_J_K'),('temp0','initial_temperature_K')]:
        a.need(g5.rel(model[k],th[key])<=1e-14,'THERMAL_REFERENCE:'+key)
    old=th['two_half_energy_increment_J']
    a.need(old.shape==(384,2,64) and np.isfinite(old).all() and
           g5.rel(model['temp0']+old/model['capacity'],th['two_half_temperature_K'])<=1e-14,
           'THERMAL_CHECKPOINT')
    out.mkdir()
    end,geom=g8.move(z,v,DT)
    delta,heat=g5.step(model,old,end,DT)
    full=dict(th,two_half_energy_increment_J=delta,
              two_half_temperature_K=model['temp0']+delta/model['capacity'])
    rows,body,budgets,proj=g8.projection(s,end,full,a.read(cp/'package.json'),
                                        (cp/'original.feg').read_text())
    (out/'regional.feg').write_text(body)
    (out/'regional_PRE.dat').write_text((cp/'original_PRE.dat').read_text().splitlines()[0]+
                                        '\n'+'\n'.join(rows)+'\n')
    for n in g7.DECK[2:]: shutil.copyfile(cp/n,out/n)
    a.write(out/'geometry.json',g4.seal(end))
    np.savez(out/'thermal.npz',**full)
    a.write(out/'NODAL_PROJECTION_BUDGETS.json',budgets)
    r={'screen_pass':bool(all(x['screen_pass'] for x in (geom,heat,proj))),
       'elapsed_years':end['elapsed_years'],'geometry':geom,'thermal':heat,'projection':proj,
       'temperature_reinitialized_from_cubic':False}
    a.write(out/'HALF_STEP_REPORT.json',r)
    return r

def checkpoint(cp,deck,state,out,year,lineage):
    out.mkdir()
    for n in ('initial.json','package.json','original.feg','original_PRE.dat','regional.in'):
        shutil.copyfile(cp/n,out/n)
    for n in ('geometry.json','thermal.npz',*g7.DECK): shutil.copyfile(deck/n,out/n)
    shutil.copyfile(state,out/'mechanical.npz')
    pin=g8.seal(out,year,lineage)
    g8.load_state(out,pin)
    return pin

def compare(cp1,cp2,cp_ref,r1,r2):
    s,z1,th1,_=g8.load_state(cp1,YEAR1_PIN)
    _,zc,tc,_=g8.load_state(cp2,YEAR2_PIN)
    zr=g4.unseal(cp_ref/'geometry.json')
    with np.load(cp_ref/'thermal.npz') as f: tr={k:f[k] for k in g8.THERMAL_KEYS}
    a.need(zc['elapsed_years']==zr['elapsed_years']==2.,'ENDPOINT_CLOCK')
    for k in ('node_parent_ids','element_parent_ids','transport_triangles_zero_based',
              'original_PRE_rows_tokens','layer_mass_kg','normalized_depth_temperature_coefficients_K'):
        a.need(z1[k]==zc[k]==zr[k],'IDENTITY_DRIFT:'+k)
    for k in ('mass_kg','initial_energy_J','heat_capacity_J_K','initial_temperature_K',
              'element_parent_ids','parcel_node_local_ids'):
        a.need(np.array_equal(th1[k],tc[k]) and np.array_equal(th1[k],tr[k]),'THERMAL_IDENTITY:'+k)
    pos=float(zr['radius_m']*np.max(np.linalg.norm(np.asarray(zr['canonical_unit_xyz'])-
                                                    np.asarray(zc['canonical_unit_xyz']),axis=1)))
    thickness=g4.relative(zr['thickness_m'],zc['thickness_m'])
    model=g5.setup(s,64)
    d0=th1['two_half_energy_increment_J']; dc=tc['two_half_energy_increment_J']-d0
    dr=tr['two_half_energy_increment_J']-d0
    td=g5.difference(model,dc,model,dr)
    # Check the new year's increment per parcel/layer, rather than the large
    # initial heat content. Use sum of absolute signals to avoid cancellation.
    ec=dc.sum(axis=-1); er=dr.sum(axis=-1)
    energy_error=float(np.sum(abs(er-ec))/max(np.sum(abs(ec)),np.sum(abs(er)),1.))
    expected=r1['thermal']['internal_energy_increment_J']+r2['thermal']['internal_energy_increment_J']
    actual=float(dr.sum())
    closure=abs(actual-expected)/max(abs(r1['thermal']['internal_energy_increment_J'])+
                                     abs(r2['thermal']['internal_energy_increment_J']),1.)
    fields={}
    with np.load(cp1/'mechanical.npz') as x,np.load(cp2/'mechanical.npz') as y,np.load(cp_ref/'mechanical.npz') as z:
        for f in g7.FIELDS: fields[f]=response(x[f],y[f],z[f])
    good=pos<=TOL['position_m'] and thickness<=TOL['thickness_relative'] and td['screen_pass'] and \
         energy_error<=TOL['energy_increment_relative'] and closure<=TOL['energy_budget_relative'] and \
         all(x['screen_pass'] for x in fields.values())
    return {'screen_pass':bool(good),'max_position_difference_m':pos,
        'max_passive_thickness_relative_difference':thickness,'thermal_increment_comparison':td,
        'parcel_layer_energy_increment_relative_L1_difference':energy_error,
        'refined_second_year_energy_J':actual,'coarse_second_year_energy_J':float(dc.sum()),
        'refined_energy_budget_relative_error':closure,'mechanical_fields':fields,
        'original_material_identity_preserved':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-controlled-coupling-test',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); selftest(); g8.check_helpers()
    a.need(g7.blob(Path(__file__).with_name('arcana_g8_staggered_restart.py'))==G8_BLOB,'G8_RUNNER_PIN')
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
           not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g8','R6_THERMO_G8_STAGGERED_RESTART_NEW01',G8_PIN,G8_STATUS),
          ('g7','R6_THERMO_G7_PAIRED_RESOLVE_NEW01',g8.G7_PIN,g8.G7_STATUS),
          ('g6','R6_THERMO_G6_FEEDBACK_PROJECTION_NEW01',g7.G6_PIN,g7.G6_STATUS),
          ('r1','R6_THERMO_G7R1_REFINE_RESPONSE_NEW01',g8.R1_PIN,g8.R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
    m=manifests['g8']
    a.need(m['source_sha']==a.SHA and m['G7R1_manifest_sha256']==g8.R1_PIN and
           all(m[k]==v for k,v in c.SCOPE.items()),'G8_LINEAGE')
    prior=a.read(parents['g8']/'G8_REPORT.json')
    a.need(prior['screen_pass'] and prior['separate_process_material_thermal_restart_exact'] and
           prior['separate_native_endpoint_state_exact'] and prior['checkpoint_year1_sha256']==YEAR1_PIN and
           prior['checkpoint_year2_sha256']==YEAR2_PIN,'G8_RECEIPT')
    cp1=parents['g8']/'checkpoint_year1'; cp2=parents['g8']/'checkpoint_year2'
    g8.open_checkpoint(cp1,YEAR1_PIN); g8.open_checkpoint(cp2,YEAR2_PIN)
    a.need(g8.same_npz(cp1/'mechanical.npz',parents['r1']/'evolved/ultra/C11B_FINAL_STATE.npz'),
           'YEAR1_MECHANICS_LINEAGE')
    a.need(g8.same_npz(cp2/'mechanical.npz',parents['g8']/'direct_mechanics/ultra/C11B_FINAL_STATE.npz'),
           'YEAR2_MECHANICS_LINEAGE')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in
           (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G8_manifest':G8_PIN,'year1_checkpoint':YEAR1_PIN,
        'year2_coarse_checkpoint':YEAR2_PIN,'runner_sha256':a.sha(Path(__file__)),
        'coarse':'Retained G8: two thermal halfsteps, velocity frozen throughout year.',
        'refined':'Two thermal halfsteps with midpoint mechanical solve and final solve.',
        'tolerances':TOL,'max_additional_native_solves':2,'additional_builds':0,
        'native_tolerance':g8.ULTRA,'scope':'Empirical splitting sensitivity only; no new calendar advance.',**c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'additional_builds':0,'additional_native_solves_attempted':0,
            'additional_time_advance_years':0,'physical_acceptance':False,**c.SCOPE}
    try:
        probe=g8.binary(parents['g6'],'probe.exe',native)
        asm=g8.binary(parents['g7']/'assembly_build','assembly_only.exe',native)
        exe=g8.binary(parents['g7']/'solve_build','solve.exe',native)
        a.need(a.sha(exe)==a.sha(parents['r1']/'solve.exe'),'SOLVER_IDENTITY')
        ctl=dict(a.read(cp1/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
        a.need((cp1/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
        print('G9_FIRST_HALF_ADVANCE',flush=True)
        first=halfstep(cp1,YEAR1_PIN,out/'midpoint_deck')
        report['first_half']=first
        a.need(first['screen_pass'] and first['elapsed_years']==1.5,'FIRST_HALF')
        print('G9_MIDPOINT_SOLVE',flush=True)
        report['additional_native_solves_attempted']+=1
        mr,ms=g8.mechanical(out/'midpoint_mechanics',out/'midpoint_deck',cp1,probe,asm,exe,native,ctl,env)
        report['midpoint_mechanics']=mr
        a.need(mr['screen_pass'],'MIDPOINT_MECHANICS')
        mid=out/'checkpoint_year1_5'
        pin=checkpoint(cp1,out/'midpoint_deck',ms,mid,1.5,
                       {'G8_manifest':G8_PIN,'parent_checkpoint':YEAR1_PIN})
        report['midpoint_checkpoint_sha256']=pin
        print('G9_SECOND_HALF_ADVANCE',flush=True)
        second=halfstep(mid,pin,out/'refined_deck')
        report['second_half']=second
        a.need(second['screen_pass'] and second['elapsed_years']==2.,'SECOND_HALF')
        print('G9_REFINED_ENDPOINT_SOLVE',flush=True)
        report['additional_native_solves_attempted']+=1
        er,es=g8.mechanical(out/'refined_mechanics',out/'refined_deck',mid,probe,asm,exe,native,ctl,env)
        report['refined_mechanics']=er
        a.need(er['screen_pass'],'REFINED_MECHANICS')
        final=out/'checkpoint_year2_refined'
        finalpin=checkpoint(mid,out/'refined_deck',es,final,2.,
                            {'G8_manifest':G8_PIN,'parent_checkpoint':pin})
        report['refined_checkpoint_sha256']=finalpin
        cmp=compare(cp1,cp2,final,first,second)
        report['coupling_comparison']=cmp
        report['screen_pass']=cmp['screen_pass']
        g8.open_checkpoint(mid,pin); g8.open_checkpoint(final,finalpin)
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and
               a.sha(parents[key]/'MANIFEST.json')==pin,'PARENT_MUTATION:'+key)
    status=('G9_COUPLING_STEP_HALVING_SCREEN_PASS__THERMAL_CONSUMER_UPGRADE_REQUIRED'
            if report['screen_pass'] else 'G9_COUPLING_STEP_HALVING_BLOCKED')
    report.update(status=status,limitations=[
        'Two-level matched-step comparison only; no asymptotic order or rigorous forward-error bound.',
        'G4 passive material thickness and G6 lumped cubic thermal projection retained.',
        'No annual response tolerance sweep on new midpoint; mechanical screens remain unchanged.',
        'No increase of timestep or continuation beyond elapsed year2; cubic projection ceiling still active.',
        'No natural exterior, canonical T1, or production history authorization.'])
    a.write(out/'G9_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G8_manifest_sha256':G8_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G9_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2

if __name__=='__main__':
    raise SystemExit(main())
