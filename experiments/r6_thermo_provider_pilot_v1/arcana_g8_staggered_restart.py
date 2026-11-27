#!/usr/bin/env python3
"""G8: restartable second controlled staggered year, preserving G5 cell energy.

The G4 parcel geometry remains the passive-density material measure for
thermal FV; G6 applies thermal expansion only in the native nodal consumer.
No reset of cell temperatures to projected PRE cubics. No canonical T1.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g5_column_heat as g5
import arcana_g6_feedback_projection as g6
import arcana_g7_paired_resolve as g7

R1_PIN='91ffd89ac6c0150ee08bfcc49e382a7cc9441b604cad348aa0e3a5d05f7fa954'
R1_STATUS='G7R1_ANNUAL_RESPONSE_NUMERICAL_SCREEN_PASS__COUPLED_RESTART_REQUIRED'
G7_PIN='2316a0a115f6a5e4d41a4c87096ed65f105e6c586d226f440cbf748b2385b9d6'
G7_STATUS='G7_CONTROLLED_ENDPOINT_RESOLVES_PASS__ANNUAL_RESPONSE_UNRESOLVED'
G6_PIN=g7.G6_PIN
ULTRA=5e-14
SCHEMA='ARCANA_G8_STAGGERED_CHECKPOINT_V1'
PINS={'arcana_c11a_assembly.py':'49d2a1545b5900f362603b5bb6745efc2e314f91',
      'arcana_c11br1_convergence.py':'1e0de22d6db7f166c4ec1ce00df626fe2df0b2ee',
      'arcana_c11c_sensitivity.py':'822ea9f80d4c1b1a0f820f8e6c2d44b9073dd41b',
      'arcana_g4_controlled_transport.py':'932dd4ac5762a3b01ed12b78f595092fc4fa2ab4',
      'arcana_g5_column_heat.py':'7927289ae17b154a7cfb31f28b761b7d04431bc2',
      'arcana_g6_feedback_projection.py':'cd78d97c8d395ed6e9e69e9cc05d1ddc20ca64c2',
      'arcana_g7_paired_resolve.py':'35d92094bf82e2b77ca54147f185c10833c8d858'}
FILES=('initial.json','geometry.json','package.json','original.feg','original_PRE.dat',
       'thermal.npz','mechanical.npz',*g7.DECK,'regional.in')
THERMAL_KEYS=('mass_kg','initial_energy_J','heat_capacity_J_K','initial_temperature_K',
              'two_half_energy_increment_J','two_half_temperature_K',
              'element_parent_ids','parcel_node_local_ids')

def check_helpers():
    here=Path(__file__).resolve().parent
    for n,p in PINS.items(): a.need(g7.blob(here/n)==p,'HELPER_PIN:'+n)

def seal(path,year,lineage):
    a.need(set(c.inventory(path))==set(FILES),'CHECKPOINT_FILE_INVENTORY')
    a.write(path/'MANIFEST.json',{'schema':SCHEMA,'elapsed_years':year,'lineage':lineage,
        'files':c.inventory(path),**c.SCOPE})
    return a.sha(path/'MANIFEST.json')

def open_checkpoint(path,pin):
    m=a.read(path/'MANIFEST.json')
    a.need(a.sha(path/'MANIFEST.json')==pin and m['schema']==SCHEMA and
        set(m['files'])==set(FILES) and c.inventory(path)==m['files'] and
        all(m[k]==v for k,v in c.SCOPE.items()),'CHECKPOINT_PIN')
    return m

def velocity(geom,deck,mechanical):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from arcana_worldsim.r6.shellset_mesh.coordinates import rotation_matrices
    mesh=parse_feg(deck,mode='SHELLS_READY')
    lat,lon=np.deg2rad(np.array([[n.latitude_deg,n.longitude_deg] for n in mesh.nodes])).T
    runtime=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    south=np.column_stack((np.sin(lat)*np.cos(lon),np.sin(lat)*np.sin(lon),-np.cos(lat)))
    east=np.column_stack((-np.sin(lon),np.cos(lon),np.zeros(len(lat))))
    _,inverse=rotation_matrices()
    p=np.asarray(geom['canonical_unit_xyz'])
    a.need(np.max(abs(runtime@inverse.T-p))<=1e-13,'MECHANICAL_GEOMETRY_BINDING')
    v=mechanical['velocity']
    a.need(v.shape==(81,2) and np.isfinite(v).all(),'VELOCITY_INVENTORY')
    xyz=(v[:,0,None]*south+v[:,1,None]*east)@inverse.T
    a.need(np.max(abs(np.sum(xyz*p,axis=1)))<=1e-21,'TANGENCY')
    return xyz

def move(s,v,dt):
    p=np.asarray(s['canonical_unit_xyz']); t=np.asarray(s['transport_triangles_zero_based'])
    R=s['radius_m']; old=np.asarray(s['area_m2']); h=np.asarray(s['thickness_m'])
    a.need(dt in (.5,1.) and s['elapsed_years']+dt<s['event_horizon_year'],'EVENT_GUARD')
    a.need(g4.relative(g4.areas(p,t,R),old)<=1e-13,'GEOMETRY_AREA')
    q=g4.advect(p,v,R,dt*g4.YEAR); new=g4.areas(q,t,R)
    a.need(np.all(new>0) and np.max(abs(np.linalg.norm(q,axis=1)-1))<=g4.TOL['unit_norm'],'POSITIVE_AREA')
    nh=h*(old/new)[:,None,None]
    a.need(np.all(nh>0),'POSITIVE_LAYER')
    gain,perim,internal=g4.swept(p,q,t,R)
    delta=new-old
    errs=[float(np.max(abs(delta-gain)/old)),
          abs(float(delta.sum())-sum(r['signed_area_gain_m2'] for r in perim))/float(old.sum()),
          float(np.max(abs(internal)))/float(old.min())]
    displacement=R*np.arctan2(np.linalg.norm(np.cross(p,q),axis=1),np.sum(p*q,axis=1))
    edges=g4.geometry_edges(t)
    edge_min=min(R*np.arctan2(np.linalg.norm(np.cross(p[u],p[w])),p[u]@p[w]) for u,w in edges)
    changes=[float(np.max(abs(new/old-1))),float(np.max(abs(nh/h-1))),float(displacement.max()/edge_min)]
    z=dict(s,elapsed_years=s['elapsed_years']+dt,canonical_unit_xyz=q.tolist(),
           area_m2=new.tolist(),thickness_m=nh.tolist(),frozen_canonical_velocity_m_s=v.tolist())
    budgets=g4.owner_budgets(z)
    mass=max(x['relative_mass_error'] for x in budgets)
    rep={'years':dt,'max_displacement_m':float(displacement.max()),'max_geometry_fraction':max(changes),
         'max_area_closure_relative_error':max(errs),'max_owner_layer_mass_error':mass,
         'owner_layer_group_count':len(budgets),'boundary_sweep_m2':sum(r['signed_area_gain_m2'] for r in perim),
         'screen_pass':bool(max(errs)<=g4.TOL['area_sweep_over_initial_area'] and
         max(changes)<=g4.TOL['geometry_fraction'] and mass<=g4.TOL['mass_relative'])}
    return z,rep

def projection(s,z,thermal,package,feg):
    rows,body,budgets=g6.project(s,z,thermal,package,feg)
    mass=np.array([x['mass_kg'] for x in budgets]); mn=np.array([x['projected_mass_kg'] for x in budgets])
    E=np.array([x['target_increment_J'] for x in budgets]); En=np.array([x['projected_increment_J'] for x in budgets])
    cap=np.array([x['heat_capacity_J_K'] for x in budgets])
    signal=float(np.max(abs(E/cap)))
    r={'mass_relative':float(np.max(abs(mn-mass)/mass)),
       'heat_increment_relative':float(np.max(abs(En-E)/cap))/max(signal,1e-300),
       'max_cell_projection_error_K':max(x['max_cell_projection_error_K'] for x in budgets),
       'max_moho_flux_gap_W_m2':max(x['moho_flux_gap_W_m2'] for x in budgets),
       'max_moho_temperature_gap_K':max(x['moho_temperature_gap_K'] for x in budgets),
       'max_cumulative_mean_signal_K':signal,
       'projected_increment_J':En.sum(axis=0).tolist(),'target_increment_J':E.sum(axis=0).tolist()}
    r['screen_pass']=bool(r['mass_relative']<=g6.TOL['mass_relative'] and
        r['heat_increment_relative']<=g6.TOL['heat_increment_relative'] and
        r['max_cell_projection_error_K']<=g6.TOL['projection_cell_max_K'] and
        r['max_moho_flux_gap_W_m2']<=g6.TOL['moho_flux_W_m2'] and
        r['max_moho_temperature_gap_K']<=g6.TOL['moho_temperature_K'])
    return rows,body,budgets,r

def load_state(path,pin):
    m=open_checkpoint(path,pin)
    s=g4.unseal(path/'initial.json'); z=g4.unseal(path/'geometry.json')
    a.need(z['elapsed_years']==m['elapsed_years'] and s['elapsed_years']==0,'CHECKPOINT_CLOCK')
    with np.load(path/'thermal.npz') as f: th={k:f[k] for k in THERMAL_KEYS}
    with np.load(path/'mechanical.npz') as f: v=velocity(z,(path/'regional.feg').read_text(),f)
    return s,z,th,v

def advance(path,pin,out,loaded=None):
    a.need(not out.exists() and not out.is_relative_to(path),'OUTPUT_NOT_FRESH')
    s,z,th,v=load_state(path,pin) if loaded is None else loaded
    model=g5.setup(s,64)
    for k,key in [('mass','mass_kg'),('heat','initial_energy_J'),('capacity','heat_capacity_J_K'),('temp0','initial_temperature_K')]:
        a.need(g5.rel(model[k],th[key])<=1e-14,'THERMAL_REFERENCE_DRIFT:'+key)
    delta=th['two_half_energy_increment_J']
    a.need(delta.shape==(384,2,64) and np.isfinite(delta).all() and
        g5.rel(model['temp0']+delta/model['capacity'],th['two_half_temperature_K'])<=1e-14,'THERMAL_CHECKPOINT')
    out.mkdir()
    one,r1g=move(z,v,1.); d1,r1t=g5.step(model,delta,one,1.)
    half,rhg=move(z,v,.5); dh,rht=g5.step(model,delta,half,.5)
    two,r2g=move(half,v,.5); d2,r2t=g5.step(model,dh,two,.5)
    # Compare the NEW heat signal, not the accumulated two-year temperature.
    temporal=g5.difference(model,d1-delta,model,d2-delta)
    pos=float(z['radius_m']*np.max(np.linalg.norm(np.asarray(one['canonical_unit_xyz'])-
                                                  np.asarray(two['canonical_unit_xyz']),axis=1)))
    thickness=g4.relative(one['thickness_m'],two['thickness_m'])
    final=dict(th,two_half_energy_increment_J=d2,two_half_temperature_K=model['temp0']+d2/model['capacity'])
    package=a.read(path/'package.json')
    rows,body,budgets,proj=projection(s,two,final,package,(path/'original.feg').read_text())
    (out/'regional.feg').write_text(body)
    (out/'regional_PRE.dat').write_text((path/'original_PRE.dat').read_text().splitlines()[0]+'\n'+'\n'.join(rows)+'\n')
    for n in g7.DECK[2:]: shutil.copyfile(path/n,out/n)
    a.write(out/'geometry.json',g4.seal(two))
    np.savez(out/'thermal.npz',**final)
    a.write(out/'NODAL_PROJECTION_BUDGETS.json',budgets)
    err=abs(float((d2-delta).sum())-(rht['internal_energy_increment_J']+r2t['internal_energy_increment_J']))
    scale=abs(rht['internal_energy_increment_J'])+abs(r2t['internal_energy_increment_J'])
    budget=err/max(scale,1.)
    ok=all(x['screen_pass'] for x in (r1g,r1t,rhg,rht,r2g,r2t,temporal,proj)) and \
        pos<=g4.TOL['halfstep_position_m'] and thickness<=g4.TOL['halfstep_thickness_relative'] and budget<=1e-11
    report={'screen_pass':bool(ok),'elapsed_years':two['elapsed_years'],'full_geometry':r1g,'half_geometry':rhg,
        'second_half_geometry':r2g,'full_thermal':r1t,'half_thermal':rht,'second_half_thermal':r2t,
        'thermal_time_refinement':temporal,'position_refinement_m':pos,'thickness_refinement_relative':thickness,
        'second_year_energy_increment_J':float((d2-delta).sum()),'cumulative_energy_increment_J':float(d2.sum()),
        'cumulative_energy_increment_closure_relative':budget,'projection':proj,
        'temperature_reinitialized_from_cubic':False,'parcel_thermal_expansion_applied':False}
    a.write(out/'ADVANCE_REPORT.json',report)
    return report

def binary(build,name,native,identity_name='BUILD_IDENTITY.json'):
    b=a.read(build/identity_name)
    exe=build/name
    libs=b.get('library_sha256',b.get('lapack_blas_sha256'))
    a.need(a.sha(exe)==b['exe_sha256'] and a.sha(native.COMPILER)==b['compiler_sha256'] and
        all(a.sha(build/n)==h for n,h in b['source_sha256'].items()) and libs is not None and
        all(a.sha(native.LIB/n)==h for n,h in libs.items()),'BINARY_IDENTITY:'+name)
    return exe

def mechanical(out,deck,cp,probe_exe,asm_exe,solve_exe,native,ctl,env):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    folder=out; folder.mkdir()
    probe=folder/'probe_reference/native_pre_solve/hydrostatic'
    probe.parent.mkdir(parents=True)
    g7.stage(probe,deck,native,ctl)
    rc,log=g7.run(probe_exe,probe,env)
    a.need(rc==0 and 'C10_STOP_AFTER_FIXED_BEFORE_PURE' in log and not (probe/'FatalError.txt').exists(),'PRESOLVE_STOP')
    asm=folder/'reference'; g7.stage(asm,deck,native,ctl)
    rc,log=g7.run(asm_exe,asm,env)
    a.need(rc==0 and 'C11A_STOP_AFTER_VBCS_BEFORE_SOLVER' in log and not (asm/'FatalError.txt').exists(),'ASSEMBLY_STOP')
    g7.controls_readback(log,ctl)
    ar=a.analyse(asm,probe.parent.parent)
    a.need(ar['rank_screen_pass'] and ar['initial_velocity_max_m_s']==0,'ASSEMBLY_RANK')
    a.write(asm/'ASSEMBLY_ANALYSIS.json',ar)
    view=copy.deepcopy(a.read(cp/'package.json'))
    mesh=parse_feg((deck/'regional.feg').read_text(),mode='SHELLS_READY')
    for item,node in zip(view['G4_mapping']['nodes'],mesh.nodes,strict=True):
        a.need(item['local_id']==node.node_id,'LOCAL_NODE_ID')
        item['runtime_lat_lon_deg']=[node.latitude_deg,node.longitude_deg]
    vdir=folder/g7.C10_NAME; vdir.mkdir()
    a.write(vdir/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json',view)
    work=folder/'ultra'; g7.stage(work,deck,native,ctl)
    rc,log=g7.run(solve_exe,work,env)
    a.need(rc==0 and 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log and not (work/'FatalError.txt').exists(),'SOLVE_STOP:'+str(rc))
    g7.controls_readback(log,ctl)
    r1.MAX_ITER=g7.MAX_ITER; r1.NATIVE_TOL=ULTRA
    r=r1.analysis(work,asm,a); a.write(work/'MECHANICAL_ANALYSIS.json',r)
    summary={'screen_pass':bool(r['screen_pass'] and max(r[k] for k in ('final_free_relative_residual',
        'work_balance_relative_defect','stress_refresh_relative_max_component'))<=g7.FINE_SCREEN),
        'iterations':len(r['iterations']),'native_scoreB':r['native_final_scoreB'],
        'residual':r['final_free_relative_residual'],'work_defect':r['work_balance_relative_defect'],
        'stress_refresh':r['stress_refresh_relative_max_component'],'power_W':r['quadrature_power_W']}
    return summary,work/'C11B_FINAL_STATE.npz'

def same_npz(p,q):
    with np.load(p) as x,np.load(q) as y:
        return set(x.files)==set(y.files) and all(np.array_equal(x[k],y[k]) for k in x.files)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-controlled-continuation',choices=[a.SCENARIO])
    ap.add_argument('--restart',type=Path); ap.add_argument('--checkpoint-pin')
    args=ap.parse_args(); check_helpers()
    out=args.output.resolve()
    if args.restart:
        a.need(args.checkpoint_pin is not None,'RESTART_PIN_REQUIRED')
        r=advance(args.restart.resolve(),args.checkpoint_pin,out)
        return 0 if r['screen_pass'] else 2
    a.need(args.authorize_controlled_continuation==a.SCENARIO,'CONTROLLED_CONTINUATION_AUTHORITY')
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    archives=[
        ('g4','R6_THERMO_G4_CONTROLLED_TRANSPORT_NEW01',g7.G4_PIN,g6.G4_STATUS),
        ('g5','R6_THERMO_G5_COLUMN_HEAT_NEW01',g7.G5_PIN,g6.G5_STATUS),
        ('g6','R6_THERMO_G6_FEEDBACK_PROJECTION_NEW01',G6_PIN,g7.G6_STATUS),
        ('g7','R6_THERMO_G7_PAIRED_RESOLVE_NEW01',G7_PIN,G7_STATUS),
        ('r1','R6_THERMO_G7R1_REFINE_RESPONSE_NEW01',R1_PIN,R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in archives:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
    a.need(manifests['r1']['G7_manifest_sha256']==G7_PIN and manifests['r1']['G6_manifest_sha256']==G6_PIN and
        manifests['r1']['source_sha']==a.SHA and all(manifests['r1'][k]==v for k,v in c.SCOPE.items()),'R1_LINEAGE')
    prior=a.read(parents['r1']/'G7R1_REPORT.json')
    a.need(prior['numerical_screen_pass'] and prior['annual_response_screen_pass'] and
        all(v['screen_pass'] for v in prior['cases'].values()),'R1_SCREEN')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(cm[k]==v for k,v in c10.SCOPE.items()),'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'parents':{k:v for k,_,v,_ in archives},'runner_sha256':a.sha(Path(__file__)),
        'scope':'Second controlled year, two frozen-velocity halfsteps and thermal carry, then endpoint re-solve.',
        'max_native_solve_runs':2,'additional_builds':0,'native_tol':ULTRA,
        'thermal_geometry':'G4 passive parcel thickness; expansion in G6 nodal consumer only.',
        'restart':'Independent Python process advancing serialized checkpoint, followed by separate identical native endpoint solve.',
        'tolerances':{'G4':g4.TOL,'G5':g5.TOL,'G6':g6.TOL,'native':g7.FINE_SCREEN},**c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'physical_acceptance':False,'additional_builds':0,**c.SCOPE}
    try:
        probe_exe=binary(parents['g6'],'probe.exe',native)
        asm_exe=binary(parents['g7']/'assembly_build','assembly_only.exe',native)
        solve_exe=binary(parents['g7']/'solve_build','solve.exe',native)
        a.need(a.sha(solve_exe)==a.sha(parents['r1']/'solve.exe'),'R1_EXECUTABLE')
        cp=out/'checkpoint_year1'; cp.mkdir()
        for source,name in [(parents['g4']/'INITIAL_CHECKPOINT.json','initial.json'),
            (parents['g4']/'TWO_HALF_STEPS_CHECKPOINT.json','geometry.json'),
            (c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json','package.json'),
            (c10.OUT/'regional.feg','original.feg'),(c10.OUT/'regional_PRE.dat','original_PRE.dat'),
            (parents['r1']/'evolved/ultra/C11B_FINAL_STATE.npz','mechanical.npz')]:
            shutil.copyfile(source,cp/name)
        with np.load(parents['g5']/'columns_64.npz') as th:
            np.savez(cp/'thermal.npz',**{k:th[k] for k in THERMAL_KEYS})
        for n in (*g7.DECK,'regional.in'): shutil.copyfile(parents['r1']/'evolved/ultra'/n,cp/n)
        for n in g7.DECK: a.need(a.sha(cp/n)==a.sha(parents['g6']/n),'YEAR1_DECK:'+n)
        pin=seal(cp,1.,{'G7R1_manifest':R1_PIN,'G4_manifest':g7.G4_PIN,'G5_manifest':g7.G5_PIN})
        loaded=load_state(cp,pin)
        print('G8_IN_MEMORY_ADVANCE',flush=True)
        direct=advance(cp,pin,out/'direct',loaded)
        print('G8_RESTART_ADVANCE',flush=True)
        cmd=[sys.executable,str(Path(__file__).resolve()),'--restart',str(cp),'--checkpoint-pin',pin,
            '--output',str(out/'restart')]
        with (out/'restart.log').open('x') as log:
            run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=120)
        a.need((out/'restart/ADVANCE_REPORT.json').is_file(),'RESTART_NO_REPORT')
        replay=a.read(out/'restart/ADVANCE_REPORT.json')
        exact=all(a.sha(out/'direct'/n)==a.sha(out/'restart'/n) for n in
            (*g7.DECK,'geometry.json','NODAL_PROJECTION_BUDGETS.json','ADVANCE_REPORT.json')) and \
            same_npz(out/'direct/thermal.npz',out/'restart/thermal.npz')
        report.update(direct_advance=direct,restart_advance_exit=run.returncode,
            separate_process_material_thermal_restart_exact=exact,checkpoint_year1_sha256=pin)
        a.need(direct['screen_pass'] and replay['screen_pass'] and exact and run.returncode==0,'ADVANCE_OR_RESTART_SCREEN')
        ctl=dict(a.read(cp/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=ULTRA)
        a.need((cp/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
        states=[]; results={}
        for name in ('direct','restart'):
            print('G8_ENDPOINT_SOLVE',name,flush=True)
            result,state=mechanical(out/(name+'_mechanics'),out/name,cp,probe_exe,asm_exe,solve_exe,native,ctl,env)
            states.append(state); results[name]=result
            report['mechanical_cases']=results
        exact_mech=same_npz(*states)
        report['separate_native_endpoint_state_exact']=exact_mech
        a.need(exact_mech and all(x['screen_pass'] for x in results.values()),'ENDPOINT_SCREEN')
        final=out/'checkpoint_year2'; final.mkdir()
        for n in ('initial.json','package.json','original.feg','original_PRE.dat','regional.in'):
            shutil.copyfile(cp/n,final/n)
        for n in ('geometry.json','thermal.npz',*g7.DECK): shutil.copyfile(out/'direct'/n,final/n)
        shutil.copyfile(states[0],final/'mechanical.npz')
        finalpin=seal(final,2.,{'checkpoint_year1':pin,'G7R1_manifest':R1_PIN})
        # Reload new endpoint and verify its mechanical frame for future use.
        load_state(final,finalpin)
        open_checkpoint(cp,pin)
        report.update(screen_pass=True,checkpoint_year2_sha256=finalpin,
            additional_time_advance_years=1.,additional_native_solves=2,
            temperature_reinitialized_from_cubic=False)
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin,_ in archives:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and
            a.sha(parents[key]/'MANIFEST.json')==pin,'PARENT_MUTATION:'+key)
    status=('G8_CONTROLLED_STAGGERED_CONTINUATION_RESTART_PASS__ADAPTIVE_COUPLING_PENDING'
            if report['screen_pass'] else 'G8_CONTROLLED_CONTINUATION_BLOCKED')
    report.update(status=status,limitations=[
        'Second year uses G7R1 endpoint velocity; two halfsteps freeze mechanics, so this is not coupled temporal convergence.',
        'Full thermal cell history retained; G4 passive thermal geometry, G6 nodal thermal expansion only.',
        'No pressure work, isostasy, physical exterior, phase changes or true thermodynamic closure.',
        'No adaptive multi-event stepping or HistoryStore production. Experimental elapsed year 2 is not canonical physical T1.'])
    a.write(out/'G8_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G7R1_manifest_sha256':R1_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G8_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2

if __name__=='__main__':
    raise SystemExit(main())
