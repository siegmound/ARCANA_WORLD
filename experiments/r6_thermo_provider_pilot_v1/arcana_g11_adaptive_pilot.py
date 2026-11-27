#!/usr/bin/env python3
"""G11 bounded adaptive pilot, with G10R1 sidecar regenerated at endpoints.

Screen 1,5,10,25,50-year macro intervals from the same corrected year2
checkpoint. Thermal/geometry substeps remain <=1 year. Select largest
consecutive passing preflight; compare one mechanical macrostep against
two half-macrosteps using matched half-year thermal steps. No automatic
acceptance of rejected trials, no canonical physical T1.
"""
import argparse
import copy
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
import arcana_g10r1_thermal_consumer as t10
import arcana_g10b_consumer_resolve as b10

B_PIN='d204b3b172dae9f26ffe101ebbda39583e4646c564ad39e6d4698cb84eee1826'
B_STATUS='G10B_THERMAL_CONSUMER_MECHANICAL_COMPATIBILITY_PASS__ADAPTIVE_PILOT_PENDING'
CANDIDATES=(1,5,10,25,50)
SIDE=t10.SIDE
SCHEMA='ARCANA_G11_SIDECAR_CHECKPOINT_V1'
FILES=(*g8.FILES,SIDE)
TOL={'macro_geometry_fraction':g4.TOL['geometry_fraction'],
     'position_m':g4.TOL['halfstep_position_m'],
     'thickness_relative':g4.TOL['halfstep_thickness_relative'],
     'mechanical_increment_fraction':g7.SIGNAL_RATIO,
     'energy_increment_relative':0.01,'energy_budget_relative':1e-11,
     'corrected_cell_absolute_K':g6.TOL['projection_cell_max_K']}

def seal(path,year,lineage):
    inv=c.inventory(path)
    a.need(set(inv)==set(FILES),'CHECKPOINT_INVENTORY')
    a.write(path/'MANIFEST.json',{'schema':SCHEMA,'elapsed_years':year,'lineage':lineage,
        'files':inv,**c.SCOPE})
    return a.sha(path/'MANIFEST.json')

def load(path,pin):
    m=a.read(path/'MANIFEST.json')
    a.need(a.sha(path/'MANIFEST.json')==pin and m['schema']==SCHEMA and
        set(m['files'])==set(FILES) and c.inventory(path)==m['files'] and
        all(m[k]==v for k,v in c.SCOPE.items()),'CHECKPOINT_PIN')
    s=g4.unseal(path/'initial.json'); z=g4.unseal(path/'geometry.json')
    a.need(s['elapsed_years']==0 and z['elapsed_years']==m['elapsed_years'],'CHECKPOINT_CLOCK')
    with np.load(path/'thermal.npz') as f: th={k:f[k] for k in g8.THERMAL_KEYS}
    with np.load(path/'mechanical.npz') as f: v=g8.velocity(z,(path/'regional.feg').read_text(),f)
    a.need((path/SIDE).read_text().splitlines()[0]==t10.MAGIC+' 81 64','SIDECAR_HEADER')
    return s,z,th,v

def checkpoint(original,deck,mech,out,year,lineage):
    out.mkdir()
    for n in ('initial.json','package.json','original.feg','original_PRE.dat','regional.in'):
        shutil.copyfile(original/n,out/n)
    for n in ('geometry.json','thermal.npz',*g7.DECK,SIDE):
        shutil.copyfile(deck/n,out/n)
    shutil.copyfile(mech,out/'mechanical.npz')
    pin=seal(out,year,lineage)
    load(out,pin)
    return pin

def distance(z,w):
    p=np.asarray(z['canonical_unit_xyz']); q=np.asarray(w['canonical_unit_xyz'])
    return float(z['radius_m']*np.max(np.arctan2(np.linalg.norm(np.cross(p,q),axis=1),
                                                  np.sum(p*q,axis=1))))

def trajectory(s,z,th,v,years,dt):
    m=g5.setup(s,64)
    for k,key in [('mass','mass_kg'),('heat','initial_energy_J'),('capacity','heat_capacity_J_K'),('temp0','initial_temperature_K')]:
        a.need(g5.rel(m[k],th[key])<=1e-14,'THERMAL_REFERENCE:'+key)
    old=th['two_half_energy_increment_J']
    a.need(old.shape==(384,2,64) and np.isfinite(old).all() and
        g5.rel(m['temp0']+old/m['capacity'],th['two_half_temperature_K'])<=1e-14,'THERMAL_CHECKPOINT')
    n=round(years/dt)
    a.need(n>0 and n*dt==years and dt in (.5,1.) and z['elapsed_years']+years<z['event_horizon_year'],
        'TIME_GUARD')
    end=z; delta=old.copy(); geoms=[]; heats=[]
    for _ in range(n):
        end,gr=g8.move(end,v,dt)
        delta,tr=g5.step(m,delta,end,dt)
        geoms.append(gr); heats.append(tr)
    final=dict(th,two_half_energy_increment_J=delta,two_half_temperature_K=m['temp0']+delta/m['capacity'])
    p=np.asarray(z['canonical_unit_xyz']); R=z['radius_m']
    edges=g4.geometry_edges(np.asarray(z['transport_triangles_zero_based']))
    emin=min(R*np.arctan2(np.linalg.norm(np.cross(p[u],p[w])),p[u]@p[w]) for u,w in edges)
    macro=max(distance(z,end)/emin,float(np.max(abs(np.asarray(end['area_m2'])/np.asarray(z['area_m2'])-1))),
              float(np.max(abs(np.asarray(end['thickness_m'])/np.asarray(z['thickness_m'])-1))))
    inc=float((delta-old).sum())
    expected=sum(x['internal_energy_increment_J'] for x in heats)
    closure=abs(inc-expected)/max(sum(abs(x['internal_energy_increment_J']) for x in heats),1.)
    report={'years':years,'substep_years':dt,'substeps':n,'elapsed_years':end['elapsed_years'],
        'macro_geometry_fraction':macro,'displacement_m':distance(z,end),
        'max_mass_error':max(x['max_owner_layer_mass_error'] for x in geoms),
        'max_area_closure_error':max(x['max_area_closure_relative_error'] for x in geoms),
        'max_CFL':max(x['max_explicit_cfl'] for x in heats),
        'max_layer_energy_error':max(x['max_layer_transfer_relative_error'] for x in heats),
        'energy_increment_J':inc,'energy_closure_relative':closure,
        'max_temperature_increment_K':float(np.max(abs((delta-old)/m['capacity']))),
        'screen_pass':bool(all(x['screen_pass'] for x in geoms+heats) and
            macro<=TOL['macro_geometry_fraction'] and closure<=TOL['energy_budget_relative'])}
    return end,final,report,m

def project(cp,s,end,thermal,out):
    out.mkdir()
    shutil.copyfile(cp/'initial.json',out/'initial.json')
    rows,feg,budgets,base=g8.projection(s,end,thermal,a.read(cp/'package.json'),(cp/'original.feg').read_text())
    (out/'regional.feg').write_text(feg)
    (out/'regional_PRE.dat').write_text((cp/'original_PRE.dat').read_text().splitlines()[0]+'\n'+'\n'.join(rows)+'\n')
    for n in g7.DECK[2:]: shutil.copyfile(cp/n,out/n)
    a.write(out/'geometry.json',g4.seal(end))
    np.savez(out/'thermal.npz',**thermal)
    a.write(out/'NODAL_PROJECTION_BUDGETS.json',budgets)
    v,profiles,rows=t10.project(out)
    a.write(out/'PROFILE_BUDGETS.json',profiles)
    (out/SIDE).write_text(t10.sidecar(v))
    old=max(x['base_error_K'] for x in profiles)
    new=max(x['corrected_error_K'] for x in profiles)
    density=max(x['density_relative_change'] for x in profiles)
    energy=max(abs(x['mass_specific_temperature_change_K']) for x in profiles)/max(base['max_cumulative_mean_signal_K'],1e-300)
    # The old cubic-only pointwise gate is replaced by the same absolute
    # ceiling on the ACTUAL consumer (cubic+sidecar). Other G6 constraints
    # are unchanged. Preserve the original cubic result in the report.
    other=base['mass_relative']<=g6.TOL['mass_relative'] and \
        base['heat_increment_relative']+energy<=g6.TOL['heat_increment_relative'] and \
        base['max_moho_flux_gap_W_m2']<=g6.TOL['moho_flux_W_m2'] and \
        base['max_moho_temperature_gap_K']<=g6.TOL['moho_temperature_K']
    r={'base_projection':base,'base_cell_error_K':old,'corrected_cell_error_K':new,
       'corrected_over_base':new/max(old,1e-300),'added_density_relative':density,
       'added_energy_over_signal':energy,'max_correction_K':float(np.max(abs(v))),
       'screen_pass':bool(other and new<=TOL['corrected_cell_absolute_K'] and
         new<=t10.TOL['cell_error_reduction_factor']*old and density<=t10.TOL['density_relative'] and
         energy<=t10.TOL['energy_over_signal'] and np.max(abs(v))<=1e-2)}
    a.write(out/'PROJECTION_REPORT.json',r)
    return r,v,rows

def mechanical(folder,deck,cp,vals,rows,probe,asm,exe,native,ctl,env):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    p=folder.with_name(folder.name+'_probe')
    b10.stage(p,deck,deck,native,ctl)
    rc,log=g7.run(probe,p,env)
    a.need(rc==0 and 'C10_STOP_AFTER_FIXED_BEFORE_PURE' in log and
        'G10R1_POST_LOAD_SAMPLES_COMPLETE' in log and not (p/'FatalError.txt').exists(),'NATIVE_PROBE')
    samples=t10.sample_check(p/'g10_native_samples.dat',vals,rows)
    a.need(samples['screen_pass'],'NATIVE_SAMPLE_SCREEN')
    view=copy.deepcopy(a.read(cp/'package.json'))
    mesh=parse_feg((deck/'regional.feg').read_text(),mode='SHELLS_READY')
    for item,node in zip(view['G4_mapping']['nodes'],mesh.nodes,strict=True):
        a.need(item['local_id']==node.node_id,'LOCAL_NODE_ID')
        item['runtime_lat_lon_deg']=[node.latitude_deg,node.longitude_deg]
    vp=folder.with_name(folder.name+'_analysis_view.json'); a.write(vp,view)
    # b10.case uses source directory both for sidecar and presolve reference.
    result,state=b10.case(folder,deck,p,vp,asm,exe,native,ctl,env)
    result['native_samples']=samples
    return result,state

def compare(start,coarse,refined):
    s,z0,t0,_=start
    _,zc,tc,_=coarse
    _,zr,tr,_=refined
    a.need(zc['elapsed_years']==zr['elapsed_years'],'COMPARISON_CLOCK')
    for k in ('node_parent_ids','element_parent_ids','transport_triangles_zero_based',
              'original_PRE_rows_tokens','layer_mass_kg','normalized_depth_temperature_coefficients_K'):
        a.need(z0[k]==zc[k]==zr[k],'IDENTITY:'+k)
    for k in ('mass_kg','initial_energy_J','heat_capacity_J_K','initial_temperature_K','element_parent_ids','parcel_node_local_ids'):
        a.need(np.array_equal(t0[k],tc[k]) and np.array_equal(t0[k],tr[k]),'THERMAL_IDENTITY:'+k)
    m=g5.setup(s,64); dc=tc['two_half_energy_increment_J']-t0['two_half_energy_increment_J']
    dr=tr['two_half_energy_increment_J']-t0['two_half_energy_increment_J']
    td=g5.difference(m,dc,m,dr)
    ec=dc.sum(axis=-1); er=dr.sum(axis=-1)
    en=float(np.sum(abs(ec-er))/max(np.sum(abs(ec)),np.sum(abs(er)),1.))
    pos=distance(zc,zr); h=g4.relative(zc['thickness_m'],zr['thickness_m'])
    return {'position_m':pos,'thickness_relative':h,'thermal_comparison':td,'energy_increment_relative':en,
        'screen_pass':bool(pos<=TOL['position_m'] and h<=TOL['thickness_relative'] and
            td['screen_pass'] and en<=TOL['energy_increment_relative'])}

def field_compare(cp,coarse,refined):
    r={}
    with np.load(cp/'mechanical.npz') as x,np.load(coarse/'mechanical.npz') as y,np.load(refined/'mechanical.npz') as z:
        for f in g7.FIELDS:
            a.need(x[f].shape==y[f].shape==z[f].shape and all(np.isfinite(k[f]).all() for k in (x,y,z)),'FIELDS')
            signal=max(g7.maxabs(y[f]-x[f]),g7.maxabs(z[f]-x[f]))
            error=g7.maxabs(z[f]-y[f])
            r[f]={'signal':signal,'difference':error,'difference_over_signal':error/signal if signal>0 else None,
                  'screen_pass':bool(signal>0 and error<=TOL['mechanical_increment_fraction']*signal)}
    return r

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-adaptive-pilot',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); g8.check_helpers(); t10.selftest()
    for n,p in [('arcana_g8_staggered_restart.py','0fd003aeb5a52e59ad33550eaa740e363a582b59'),
        ('arcana_g10r1_thermal_consumer.py','63178aa33312c1be425a9c52eb945f762a2c1349'),
        ('arcana_g10b_consumer_resolve.py','837f5102b8216226c15d255961e5f6c862795469')]:
        a.need(g7.blob(Path(__file__).with_name(n))==p,'HELPER_PIN:'+n)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',B_PIN,B_STATUS),
        ('t','R6_THERMO_G10R1_THERMAL_CONSUMER_NEW01',b10.G10R1_PIN,b10.G10R1_STATUS),
        ('g9','R6_THERMO_G9_COUPLING_HALVING_NEW01',b10.G9_PIN,b10.G9_STATUS)]
    parents={}; manifests={}
    for key,n,pin,status in refs:
        p=c10.OUT.with_name(n); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'SCOPE')
    br=a.read(parents['b']/'G10B_REPORT.json')
    a.need(br['screen_pass'] and br['numerical_screen_pass'] and br['compatibility_screen_pass'] and
        br['zero_replay_screen_pass'] and manifests['b']['G10R1_manifest_sha256']==b10.G10R1_PIN and
        manifests['b']['G9_manifest_sha256']==b10.G9_PIN,'G10B_LINEAGE')
    orig=parents['g9']/'checkpoint_year2_refined'; g8.open_checkpoint(orig,b10.G9_CP)
    corrected=parents['b']/'corrected/ultra'
    for n in (*g7.DECK,'regional.in'):
        a.need(a.sha(orig/n)==a.sha(corrected/n),'START_DECK:'+n)
    a.need(a.sha(corrected/SIDE)==a.sha(parents['t']/'corrected'/SIDE),'START_SIDECAR')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    probe=g8.binary(parents['t']/'build','probe.exe',native)
    asm=g8.binary(parents['b']/'assembly_build','assembly_only.exe',native)
    exe=g8.binary(parents['b']/'solve_build','solve.exe',native)
    for p in (parents['b']/'assembly_build',parents['b']/'solve_build'):
        a.need(a.sha(p/'MOD_ArcanaRuntime.f90')==a.sha(parents['t']/'build/MOD_ArcanaRuntime.f90'),'LOADER_LINEAGE')
    ctl=dict(a.read(orig/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
    a.need((orig/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'runner_sha256':a.sha(Path(__file__)),'G10B_manifest':B_PIN,'start_checkpoint':b10.G9_CP,
        'candidates_years':CANDIDATES,'selection':'Largest consecutive passing preflight; stop at first rejection; no automatic solve retry.',
        'thermal_substep_years':.5,'preflight_comparison_substep_years':1.,'tolerances':TOL,
        'projection_gate':'Same 10 microkelvin ceiling on corrected actual consumer, original cubic gate reported separately; integrated G6 limits retained.',
        'maximum_native_solves':3,'additional_builds':0,**c.SCOPE})
    report={'screen_pass':False,'preflight':{},'native_solves_attempted':0,'additional_builds':0,
        'physical_acceptance':False,**c.SCOPE}
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    try:
        cp=out/'checkpoint_start'; cp.mkdir()
        for n in g8.FILES:
            if n=='mechanical.npz': shutil.copyfile(corrected/'C11B_FINAL_STATE.npz',cp/n)
            else: shutil.copyfile(orig/n,cp/n)
        shutil.copyfile(corrected/SIDE,cp/SIDE)
        pin=seal(cp,2.,{'G10B_manifest':B_PIN,'G9_checkpoint':b10.G9_CP})
        start=load(cp,pin); s,z,th,v=start
        report['start_checkpoint_sha256']=pin
        selected=None
        for years in CANDIDATES:
            print('G11_PREFLIGHT',years,flush=True)
            if z['elapsed_years']+years>=z['event_horizon_year']:
                report['preflight'][str(years)]={'screen_pass':False,'reason':'EVENT_HORIZON'}
                break
            end,thermal,tr,m=trajectory(*start,years,.5)
            rough,roughth,rr,_=trajectory(*start,years,1.)
            old=th['two_half_energy_increment_J']
            td=g5.difference(m,roughth['two_half_energy_increment_J']-old,m,thermal['two_half_energy_increment_J']-old)
            pos=distance(end,rough); h=g4.relative(end['thickness_m'],rough['thickness_m'])
            deck=out/f'candidate_{years}'
            pr,vals,rows=project(cp,s,end,thermal,deck)
            r={'trajectory':tr,'coarser_trajectory':rr,'thermal_refinement':td,
                'geometry_refinement_m':pos,'thickness_refinement_relative':h,'projection':pr}
            r['screen_pass']=bool(tr['screen_pass'] and rr['screen_pass'] and td['screen_pass'] and pr['screen_pass']
                and pos<=TOL['position_m'] and h<=TOL['thickness_relative'])
            a.write(deck/'PREFLIGHT_REPORT.json',r); report['preflight'][str(years)]=r
            print('G11_PREFLIGHT_RESULT',years,r['screen_pass'],pr['corrected_cell_error_K'],flush=True)
            if not r['screen_pass']: break
            selected=(years,deck,vals,rows)
        a.need(selected is not None,'NO_ADMISSIBLE_CANDIDATE')
        years,deck,vals,rows=selected; report['selected_years']=years
        # Coarse endpoint at selected duration.
        report['native_solves_attempted']+=1
        print('G11_COARSE_SOLVE',years,flush=True)
        cr,cs=mechanical(out/'coarse_mechanics',deck,cp,vals,rows,probe,asm,exe,native,ctl,env)
        report['coarse_mechanics']=cr; a.need(cr['screen_pass'],'COARSE_MECHANICS')
        coarse=out/'checkpoint_coarse'
        cpin=checkpoint(cp,deck,cs,coarse,2.+years,{'parent':pin,'macro_years':years})
        report['coarse_checkpoint_sha256']=cpin
        current=cp; curpin=pin
        for i in (1,2):
            print('G11_REFINED_HALF',i,years/2,flush=True)
            st=load(current,curpin)
            e,t,tr,_=trajectory(*st,years/2,.5)
            d=out/f'half_{i}_deck'; pr,vals,rows=project(current,st[0],e,t,d)
            report[f'half_{i}']={'trajectory':tr,'projection':pr}
            a.need(tr['screen_pass'] and pr['screen_pass'],'HALF_PREFLIGHT:'+str(i))
            report['native_solves_attempted']+=1
            mr,ms=mechanical(out/f'half_{i}_mechanics',d,current,vals,rows,probe,asm,exe,native,ctl,env)
            report[f'half_{i}']['mechanics']=mr
            a.need(mr['screen_pass'],'HALF_MECHANICS:'+str(i))
            nxt=out/f'checkpoint_half_{i}'
            npin=checkpoint(current,d,ms,nxt,2.+i*years/2,{'parent':curpin,'macro_years':years/2})
            report[f'half_{i}']['checkpoint_sha256']=npin
            current,curpin=nxt,npin
        comp=compare(start,load(coarse,cpin),load(current,curpin))
        fields=field_compare(cp,coarse,current)
        report['coupling_comparison']=comp; report['mechanical_fields']=fields
        report['screen_pass']=bool(comp['screen_pass'] and all(x['screen_pass'] for x in fields.values()))
        if report['screen_pass']:
            report.update(accepted_experimental_elapsed_years=2.+years,additional_time_advance_years=years,
                accepted_checkpoint=str(current.relative_to(out)),accepted_checkpoint_sha256=curpin)
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin0,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin0,'PARENT_MUTATION:'+key)
    status='G11_ADAPTIVE_MACROSTEP_PILOT_PASS__EXTENDED_TRAJECTORY_PENDING' if report['screen_pass'] else 'G11_ADAPTIVE_MACROSTEP_PILOT_BLOCKED'
    report.update(status=status,limitations=[
        'Single selected macrostep, not general adaptive integration; rejected trials retained and no automatic coupled backoff.',
        'Thermal substeps remain half-year; mechanical refresh interval only is increased.',
        'Corrected thermal projection absolute ceiling retained; no canonical T1 or physics promotion.',
        'Passive parcel geometry, no pressure work, isostasy, natural exterior or phase changes.',
        'No independent native vertical quadrature refinement or coupled restart in a new interpreter in this pilot.'])
    a.write(out/'G11_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G10B_manifest_sha256':B_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G11_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
