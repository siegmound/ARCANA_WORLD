#!/usr/bin/env python3
"""G14: exact frozen-field spherical flow, midpoint CN, bounded adaptive
coupled trajectory with rejection/backoff and immutable trial evidence.
No global or physical promotion.
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

G13_PIN='db1da82d2845805f90557f7b9a1c18bb784fb2c200b9e7dc45ce8d190b4876ec'
G13_STATUS='G13_CN_MULTISCALE_PILOT_PASS__ADAPTIVE_TRAJECTORY_REQUIRED'
CP_PIN='7de43bcb72732b20943ac8ab30a930ba45874ec770702c983b4e26d8eb195bee'
START=62.
TARGET=112.
MAX_TRIALS=4
MIN_STEP=6.25
MAX_SOLVES=12

def flow(p,v,R,dt):
    """Exact solution of dp/dt=(v-(v.p)p)/R, constant ambient v.
    This is the continuous ODE approximated by G4's projected exp map.
    """
    speed=np.linalg.norm(v,axis=1)
    e=np.divide(v,speed[:,None],out=np.zeros_like(v),where=speed[:,None]>0)
    u=np.sum(p*e,axis=1)
    x=speed*dt/R
    a.need(np.max(abs(x))<.01,'FLOW_SMALL_CAP')
    sh=np.sinh(x); cm1=2*np.sinh(x/2)**2
    den=1+cm1+u*sh
    q=(p+(sh+u*cm1)[:,None]*e)/den[:,None]
    a.need(np.max(abs(np.linalg.norm(q,axis=1)-1))<=g4.TOL['unit_norm'],'FLOW_NORM')
    return q/np.linalg.norm(q,axis=1)[:,None]

def exact_move(s,v,dt):
    p=np.asarray(s['canonical_unit_xyz']); t=np.asarray(s['transport_triangles_zero_based'])
    R=s['radius_m']; old=np.asarray(s['area_m2']); h=np.asarray(s['thickness_m'])
    a.need(0<dt<=50. and s['elapsed_years']+dt<s['event_horizon_year'],'EVENT_GUARD')
    a.need(g4.relative(g4.areas(p,t,R),old)<=1e-13,'GEOMETRY_AREA')
    q=flow(p,v,R,dt*g4.YEAR); new=g4.areas(q,t,R)
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


def selftest():
    p=np.array([[1.,0,0],[0,1.,0],[0,0,1.]])
    v=np.array([[0.,1.,0.],[0.,1.,0.],[0.,0.,0.]])
    q=flow(p,v,1.,.001)
    a.need(np.max(abs(q[0]-[1/np.cosh(.001),np.tanh(.001),0]))<1e-15,'ANALYTIC_FLOW')
    a.need(np.array_equal(q[1:],p[1:]),'STATIONARY_FLOW')
    a.need(np.max(abs(flow(flow(p,v,1.,.0005),v,1.,.0005)-q))<1e-15,'FLOW_SEMIGROUP')
    print('G14_EXACT_FLOW_SELFTEST_PASS',flush=True)

def advance(st,years,steps):
    s,z,th,v=st; m=g5.setup(s,64)
    old=th['two_half_energy_increment_J']
    for k,key in [('mass','mass_kg'),('heat','initial_energy_J'),('capacity','heat_capacity_J_K'),('temp0','initial_temperature_K')]:
        a.need(g5.rel(m[k],th[key])<=1e-14,'THERMAL_REFERENCE:'+key)
    a.need(g5.rel(m['temp0']+old/m['capacity'],th['two_half_temperature_K'])<=1e-14,'THERMAL_STATE')
    end,geom=exact_move(z,v,years)
    d=old.copy(); reports=[]; geometry=[geom]; dt=years/steps
    for j in range(steps):
        mid,gr=exact_move(z,v,(j+.5)*dt)
        geometry.append(gr)
        d,r=g13.cn(m,d,mid,dt); reports.append(r)
    tr=g13.summary(reports,old,d)
    r={'geometry':geom,'max_geometry_mass_error':max(x['max_owner_layer_mass_error'] for x in geometry),
       'max_geometry_area_error':max(x['max_area_closure_relative_error'] for x in geometry),
       'geometry_evaluations':len(geometry),'thermal':tr,'thermal_dt_years':dt,
       'screen_pass':bool(all(x['screen_pass'] for x in geometry) and tr['screen_pass'])}
    return end,g13.thermal_state(th,m,d),r

def preflight(st,years,steps):
    e,t,r=advance(st,years,steps)
    _,tc,rc=advance(st,years,steps//2)
    m=g5.setup(st[0],64); old=st[2]['two_half_energy_increment_J']
    cmp=g5.difference(m,t['two_half_energy_increment_J']-old,m,tc['two_half_energy_increment_J']-old)
    report={'refined':r,'coarse':rc,'thermal_refinement':cmp,
        'screen_pass':bool(r['screen_pass'] and rc['screen_pass'] and cmp['screen_pass'])}
    return e,t,report

def legacy_check(st):
    s,z,th,v=st; m=g5.setup(s,64); old=th['two_half_energy_increment_J']
    states,gr=g13.path(z,v,25.)
    ref=g13.reference(m,old,states)
    e,t,r=advance(st,25.,4)
    cmp=g5.difference(m,t['two_half_energy_increment_J']-old,m,ref-old)
    pos=g11.distance(e,states[-1]); h=g4.relative(e['thickness_m'],states[-1]['thickness_m'])
    mid,_=exact_move(z,v,12.5)
    two,_=exact_move(mid,v,12.5)
    semigroup=g11.distance(e,two)
    return {'screen_pass':bool(r['screen_pass'] and cmp['screen_pass'] and
        pos<=g11.TOL['position_m'] and h<=g11.TOL['thickness_relative'] and semigroup<=1e-7),
        'legacy_geometry_updates':50,'new_geometry_evaluations':r['geometry_evaluations'],
        'legacy_thermal_updates':50,'new_thermal_updates':4,'position_difference_m':pos,
        'thickness_relative_difference':h,'flow_semigroup_difference_m':semigroup,
        'thermal_comparison':cmp,'new_path':r}

def trial(folder,cp,pin,years,probe,asm,exe,native,ctl,env,report):
    folder.mkdir(); st=g11.load(cp,pin)
    start=st[1]['elapsed_years']
    result={'years':years,'start_year':start,'screen_pass':False,'native_solves_attempted':0}
    def retain():
        a.write(folder/'TRIAL_REPORT.json',result)
        return result
    if start+years>=st[1]['event_horizon_year']:
        result['reason']='EVENT_HORIZON'; return retain()
    e,t,r=preflight(st,years,8); result['preflight']=r
    if not r['screen_pass']:
        result['reason']='TRANSPORT_THERMAL_PREFLIGHT'; return retain()
    d=folder/'coarse_deck'; pr,v,rows=g12.project(cp,st[0],e,t,d); result['coarse_projection']=pr
    if not pr['screen_pass']:
        result['reason']='PROJECTION_PREFLIGHT'; return retain()
    def solve(label,deck,source,vals,rows):
        result['native_solves_attempted']+=1; report['native_solves_attempted']+=1
        a.need(report['native_solves_attempted']<=MAX_SOLVES,'SOLVE_BUDGET')
        return g11.mechanical(folder/(label+'_mechanics'),deck,source,vals,rows,probe,asm,exe,native,ctl,env)
    cr,cs=solve('coarse',d,cp,v,rows); result['coarse_mechanics']=cr
    if not cr['screen_pass']:
        result['reason']='COARSE_MECHANICS'; return retain()
    coarse=folder/'checkpoint_coarse'
    cpin=g11.checkpoint(cp,d,cs,coarse,start+years,{'parent':pin,'integrator':'G14_EXACT_FLOW_MIDPOINT_CN'})
    result['coarse_checkpoint_sha256']=cpin
    current=cp; curpin=pin
    for i in (1,2):
        hs=g11.load(current,curpin)
        e,t,r=preflight(hs,years/2,4)
        label=f'half_{i}'; result[label]={'preflight':r}
        if not r['screen_pass']:
            result['reason']='HALF_PREFLIGHT:'+str(i); return retain()
        d=folder/(label+'_deck'); pr,v,rows=g12.project(current,hs[0],e,t,d)
        result[label]['projection']=pr
        if not pr['screen_pass']:
            result['reason']='HALF_PROJECTION:'+str(i); return retain()
        mr,ms=solve(label,d,current,v,rows); result[label]['mechanics']=mr
        if not mr['screen_pass']:
            result['reason']='HALF_MECHANICS:'+str(i); return retain()
        nxt=folder/('checkpoint_'+label)
        npin=g11.checkpoint(current,d,ms,nxt,start+i*years/2,{'parent':curpin,'integrator':'G14_EXACT_FLOW_MIDPOINT_CN'})
        result[label]['checkpoint_sha256']=npin; current,curpin=nxt,npin
    cmp=g11.compare(st,g11.load(coarse,cpin),g11.load(current,curpin))
    fields=g11.field_compare(cp,coarse,current)
    result.update(coupling_comparison=cmp,mechanical_fields=fields)
    result['screen_pass']=bool(cmp['screen_pass'] and all(x['screen_pass'] for x in fields.values()))
    if result['screen_pass']:
        result.update(accepted_year=start+years,accepted_checkpoint=current.name,accepted_checkpoint_sha256=curpin)
    else: result['reason']='COUPLING_REFINEMENT'
    return retain()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-adaptive-trajectory',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); g8.check_helpers(); selftest()
    for n,p in [('arcana_g13_cn_multiscale.py','d5711c9668539a284f165efd368879f1ab93c77e'),('arcana_g11_adaptive_pilot.py','caafab6df23e7b9a51e6463a435c1013d83ff173'),
        ('arcana_g12_joint_profile_extended.py','9f00582e7948635bdac23b4e65584fe5291a0e7b'),
        ('arcana_g10r1_thermal_consumer.py','63178aa33312c1be425a9c52eb945f762a2c1349'),
        ('arcana_g10b_consumer_resolve.py','837f5102b8216226c15d255961e5f6c862795469'),
        ('arcana_g8_staggered_restart.py','0fd003aeb5a52e59ad33550eaa740e363a582b59')]:
        a.need(g7.blob(Path(__file__).with_name(n))==p,'HELPER_PIN:'+n)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g13','R6_THERMO_G13_CN_MULTISCALE_NEW01',G13_PIN,G13_STATUS),
          ('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',g11.B_PIN,g11.B_STATUS),
          ('t','R6_THERMO_G10R1_THERMAL_CONSUMER_NEW01',b10.G10R1_PIN,b10.G10R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g13']; prior=a.read(p/'G13_REPORT.json')
    a.need(prior['screen_pass'] and prior['accepted_checkpoint_sha256']==CP_PIN and
        prior['accepted_experimental_elapsed_years']==START and manifests['g13']['G12_manifest_sha256']==g13.G12_PIN,'G13_LINEAGE')
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
    a.write(out/'POLICY.json',{'G13_manifest':G13_PIN,'checkpoint':CP_PIN,'runner_sha256':a.sha(Path(__file__)),
        'target_year':TARGET,'initial_macrostep_years':50.,'minimum_macrostep_years':MIN_STEP,
        'max_trials':MAX_TRIALS,'max_native_solves':MAX_SOLVES,'additional_builds':0,
        'geometry':'Exact continuous frozen ambient projected velocity, conservative spherical sweep',
        'thermal':'Midpoint geometry CN, 8 coarse macro thermal steps or 4 per coupled half, compared to half count',
        'backoff':'On failed numerical screen halve from last accepted checkpoint; exceptions abort, never accepted.',
        'tolerances':g11.TOL,'thermal_tolerances':g5.TOL,**c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'native_solves_attempted':0,'additional_builds':0,'physical_acceptance':False,
        'trials':[],'accepted_experimental_elapsed_years':START,'additional_time_advance_years':0,**c.SCOPE}
    try:
        print('G14_LEGACY_REPLAY_25Y',flush=True)
        report['legacy_comparison']=legacy_check(start)
        a.need(report['legacy_comparison']['screen_pass'],'LEGACY_SCREEN')
        cur=cp; pin=CP_PIN; year=START; dt=50.
        for k in range(1,MAX_TRIALS+1):
            if year==TARGET: break
            dt=min(dt,TARGET-year)
            if dt<MIN_STEP or report['native_solves_attempted']+3>MAX_SOLVES: break
            folder=out/f'trial_{k:02d}'
            print('G14_TRIAL',k,year,dt,flush=True)
            r=trial(folder,cur,pin,dt,probe,asm,exe,native,ctl,env,report)
            report['trials'].append({'path':folder.name,**r})
            if r['screen_pass']:
                cur=folder/r['accepted_checkpoint']; pin=r['accepted_checkpoint_sha256']; year=r['accepted_year']
                report.update(accepted_experimental_elapsed_years=year,additional_time_advance_years=year-START,
                    accepted_checkpoint=str(cur.relative_to(out)),accepted_checkpoint_sha256=pin)
                print('G14_ACCEPT',year,flush=True)
            else:
                print('G14_REJECT',r['reason'],flush=True); dt/=2
        report['screen_pass']=year==TARGET
        if report['screen_pass']: g11.load(cur,pin)
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin0,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin0,'PARENT_MUTATION:'+key)
    status='G14_ADAPTIVE_REGIONAL_TRAJECTORY_PASS__EVENT_AND_SCALE_REQUIRED' if report['screen_pass'] else 'G14_ADAPTIVE_REGIONAL_TRAJECTORY_RETAINED__TARGET_NOT_QUALIFIED'
    report.update(status=status,limitations=[
        'Exact flow is for frozen ambient field only, not evolving mechanics.',
        'Thermal midpoint geometry and two-level coupled sensitivity are empirical numerical screens, not rigorous global error bounds.',
        'Passive parcel geometry, fixed heat capacities, nodal lumped reconstruction and original native vertical quadrature retained.',
        'Event crossing forbidden, no event transition, no natural exterior, physical T1 or history production.'])
    a.write(out/'G14_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G13_manifest_sha256':G13_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G14_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
