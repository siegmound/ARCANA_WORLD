#!/usr/bin/env python3
"""G12: joint mass/heat-consistent profile + bounded extended trajectory.

Reuse qualified G10R1 native sidecar format and binaries. Instead of forcing
the correction to preserve the old cubic's density moment, match the cell
means, solve the nonlinear sensible-heat constraint, update thickness from
the corrected density, and restore Moho flux continuity. The actual thermal
cell state is retained. No physical T1 or global authorization.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import traceback
import numpy as np
from dataclasses import replace
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g5_column_heat as g5
import arcana_g6_feedback_projection as g6
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g10r1_thermal_consumer as t10
import arcana_g10b_consumer_resolve as b10
import arcana_g11_adaptive_pilot as g11

G11_PIN='4308c734eeee3bcac48410b160ae4e2bec4dbde809ad2f327067f1bc4f02a09c'
G11_STATUS='G11_ADAPTIVE_MACROSTEP_PILOT_PASS__EXTENDED_TRAJECTORY_PENDING'
CP_PIN='ff2237474f12cf8f1ca3ac2169ff6e06fe03d786327c23d61de2fb30eae48a80'
START_YEAR=12.
CANDIDATES=(25,10,5,1)
B,P,W=t10.B,t10.P,t10.W
DER=np.arange(4.)
TOL=dict(g11.TOL,relative_reduction=.25,sidecar_max_K=1e-2,
    fit_matrix_cond=1e5,migration_signal_fraction=.1)

def integrals(initial,base,v,alpha):
    t0=P@initial; d=P@(base-initial)+B@v
    den0=W@(1-alpha*t0)
    mean0=(W@((1-alpha*t0)*t0))/den0
    den=den0-alpha*(W@d)
    dm=(W@((1-2*alpha*t0+alpha*mean0)*d-alpha*d*d))/den
    a.need(den>0 and np.all(t0+d>0) and np.all(1-alpha*(t0+d)>0),'POSITIVE_PROFILE')
    return den,dm,t0+d

def weights(initial,alpha):
    w=(1-alpha*(P@initial))*W
    w=w.reshape(64,8)
    a.need(np.all(w>0),'POSITIVE_WEIGHTS')
    return w/w.sum(axis=1)[:,None]

def averages(x,w):
    return (x.reshape(64,8)*w).sum(axis=1)

def fit_layer(initial,base,alpha,target,want):
    w=weights(initial,alpha)
    A=(B.reshape(64,8,64)*w[:,:,None]).sum(axis=1)
    cond=float(np.linalg.cond(A))
    a.need(cond<=TOL['fit_matrix_cond'],'CELL_MATRIX_CONDITION')
    residual=target-averages(P@(base-initial),w)
    v,direction=np.linalg.solve(A,np.column_stack((residual,np.ones(64)))).T
    shape=B@direction
    for _ in range(5):
        den,dm,T=integrals(initial,base,v,alpha)
        t0=P@initial; den0=W@(1-alpha*t0)
        mean0=(W@((1-alpha*t0)*t0))/den0
        derivative=(W@((1-2*alpha*T+alpha*(mean0+dm))*shape))/den
        a.need(abs(derivative)>.5,'ENERGY_DERIVATIVE')
        v=v+((want-dm)/derivative)*direction
    return v,cond

def fit_node(initial,base,alpha,rho,k,mass,area,target,want):
    # Surface, Moho and LAB temperatures are fixed by the original G6 base.
    # Adjust crust derivative by a quadratic that vanishes at both ends.
    base=base.copy()
    for _ in range(8):
        fits=[fit_layer(initial[j],base[j],alpha[j],target[j],want[j]) for j in range(2)]
        v=np.array([x[0] for x in fits])
        moments=[integrals(initial[j],base[j],v[j],alpha[j]) for j in range(2)]
        den=np.array([x[0] for x in moments]); h=mass/(area*rho*den)
        desired=(k[1]/h[1])/(k[0]/h[0])*base[1,1]
        change=base[0]@DER-desired
        if abs(change)<=1e-10: break
        base[0,1]+=change; base[0,2]-=change
    else: raise RuntimeError('MOHO_ITERATION')
    return base,v,h,max(x[1] for x in fits)

def selftest():
    initial=np.array([[280.,500.,-10.,2.],[772.,490.,0.,0.]])
    alpha=np.array([3e-5,3e-5]); rho=np.array([2800.,3300.]); k=np.array([2.5,2.5])
    area=1e8; h=np.array([30000.,30000.*490/486])
    mass=np.array([area*h[j]*rho[j]*integrals(initial[j],initial[j],np.zeros(64),alpha[j])[0] for j in range(2)])
    # Generate cell means and energy targets from a known smooth correction.
    expected=np.array([np.sin(np.pi*(np.arange(64)+.5)/64)*1e-4,
                       -np.sin(np.pi*(np.arange(64)+.5)/64)*2e-4])
    target=np.array([averages(B@expected[j],weights(initial[j],alpha[j])) for j in range(2)])
    want=np.array([integrals(initial[j],initial[j],expected[j],alpha[j])[1] for j in range(2)])
    base,v,hn,cond=fit_node(initial,initial,alpha,rho,k,mass,area,target,want)
    for j in range(2):
        den,dm,_=integrals(initial[j],base[j],v[j],alpha[j])
        a.need(abs(dm-want[j])<1e-12 and abs(area*hn[j]*rho[j]*den/mass[j]-1)<1e-12 and
            np.max(abs(averages(P@(base[j]-initial[j])+B@v[j],weights(initial[j],alpha[j]))-target[j]))<1e-9,
            'JOINT_FIXTURE')
    a.need(abs(k[0]/hn[0]*(base[0]@DER)-k[1]/hn[1]*base[1,1])<2e-12,'MOHO_FIXTURE')
    print('G12_JOINT_PROJECTION_SELFTEST_PASS',flush=True)

def project(cp,s,end,thermal,out):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS,RuntimeNode
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg,write_feg
    out.mkdir()
    shutil.copyfile(cp/'initial.json',out/'initial.json')
    lines,feg,old_budgets,old=g8.projection(s,end,thermal,a.read(cp/'package.json'),(cp/'original.feg').read_text())
    mesh=parse_feg(feg,mode='SHELLS_READY')
    tri=np.asarray(s['transport_triangles_zero_based']).ravel()
    areas=np.repeat(np.asarray(end['area_m2'])/3,3)
    mass=np.asarray(s['layer_mass_kg']).reshape(384,2)
    ini=np.asarray(s['normalized_depth_temperature_coefficients_K']).reshape(384,2,4)
    cap=thermal['heat_capacity_J_K']; E=thermal['two_half_energy_increment_J']
    a.need(cap.shape==E.shape==(384,2,64) and np.isfinite(E).all(),'THERMAL_INVENTORY')
    nodes=[]; vals=[]; rows=[]; budgets=[]; final_lines=[]
    for i,line in enumerate(lines):
        row=dict(zip(FIELDS,map(float,line.split()),strict=True))
        a.need(row['node_id']==i+1,'NODE_ORDER')
        idx=np.flatnonzero(tri==i); area=float(areas[idx].sum()); M=mass[idx].sum(axis=0)
        C=cap[idx].sum(axis=0); en=E[idx].sum(axis=0)
        target=en/C; want=en.sum(axis=1)/C.sum(axis=1)
        initial=ini[idx[0]]
        a.need(np.all(ini[idx]==initial),'OWNER_PROFILE')
        alpha,rho,k=[np.array([row[role+'_'+key] for role in ('crust','mantle')])
                     for key in ('expansivity_k_1','density_kg_m3','conductivity_w_m_k')]
        base=np.empty((2,4)); oldh=[]
        for j in range(2):
            pre=f'layer{j+1}_'; h=row[pre+'z1_m']-row[pre+'z0_m']; oldh.append(h)
            base[j]=[row[pre+key]*h**p for p,key in enumerate(('c0_k','c1_k_m','c2_k_m2','c3_k_m3'))]
        co,v,h,cond=fit_node(initial,base,alpha,rho,k,M,area,target,want)
        row.update(crust_thickness_m=float(h[0]),mantle_lithosphere_thickness_m=float(h[1]),
                   lab_depth_m=float(h.sum()),surface_temperature_k=float(co[0,0]),
                   surface_heat_flow_w_m2=float(k[0]/h[0]*co[0,1]),
                   moho_temperature_k=float(co[0].sum()),moho_flux_w_m2=float(k[0]/h[0]*(co[0]@DER)),
                   lab_temperature_k=float(co[1].sum()),lab_flux_w_m2=float(k[1]/h[1]*(co[1]@DER)))
        for j in range(2):
            pre=f'layer{j+1}_'; row[pre+'z0_m']=float(h[:j].sum()); row[pre+'z1_m']=float(h[:j+1].sum())
            for p,key in enumerate(('c0_k','c1_k_m','c2_k_m2','c3_k_m3')):
                row[pre+key]=float(co[j,p]/h[j]**p)
        text=RuntimeNode(tuple(row[f] for f in FIELDS)).line()
        final_lines.append(text); rr=dict(zip(FIELDS,map(float,text.split()),strict=True))
        # Check actual serialized polynomial and sidecar, not unrounded fit.
        vv=np.array([[float(format(x,'.17e')) for x in q] for q in v]); vals.append(vv)
        cc=[]; hh=[]
        for j in range(2):
            pre=f'layer{j+1}_'; hj=rr[pre+'z1_m']-rr[pre+'z0_m']; hh.append(hj)
            bj=np.array([rr[pre+key]*hj**p for p,key in enumerate(('c0_k','c1_k_m','c2_k_m2','c3_k_m3'))])
            cc.append(bj)
            den,dm,T=integrals(initial[j],bj,vv[j],alpha[j])
            w=weights(initial[j],alpha[j])
            baseerr=float(np.max(abs(averages(P@(base[j]-initial[j]),w)-target[j])))
            err=float(np.max(abs(averages(P@(bj-initial[j])+B@vv[j],w)-target[j])))
            budgets.append({'node':i+1,'layer':j+1,'mass_relative':float(abs(area*hj*rho[j]*den/M[j]-1)),
                'target_mean_increment_K':float(want[j]),'mean_increment_error_K':float(abs(dm-want[j])),
                'base_cell_error_K':baseerr,'corrected_cell_error_K':err,
                'thickness_change_from_cubic_m':float(hj-oldh[j]),'cell_matrix_cond':cond,
                'max_abs_correction_K':float(np.max(abs(vv[j]))),
                'max_abs_total_perturbation_K':float(np.max(abs(T-P@initial[j])))})
            rows.append((i+1,j+1,hj,bj,rho[j],alpha[j]))
        budgets[-1]['moho_flux_gap_W_m2']=float(abs(k[0]/hh[0]*(cc[0]@DER)-k[1]/hh[1]*cc[1][1]))
        budgets[-1]['moho_temperature_gap_K']=float(abs(cc[0].sum()-cc[1][0]))
        nodes.append(replace(mesh.nodes[i],crustal_thickness_m=rr['crust_thickness_m'],
            mantle_lithosphere_thickness_m=rr['mantle_lithosphere_thickness_m'],
            heat_flow_w_m2=rr['surface_heat_flow_w_m2']))
    newmesh=replace(mesh,nodes=tuple(nodes)); body=write_feg(newmesh)
    a.need(parse_feg(body,mode='SHELLS_READY')==newmesh,'FEG_ROUNDTRIP')
    (out/'regional.feg').write_text(body)
    (out/'regional_PRE.dat').write_text((cp/'original_PRE.dat').read_text().splitlines()[0]+'\n'+'\n'.join(final_lines)+'\n')
    for n in g7.DECK[2:]: shutil.copyfile(cp/n,out/n)
    a.write(out/'geometry.json',g4.seal(end)); np.savez(out/'thermal.npz',**thermal)
    v=np.asarray(vals); (out/t10.SIDE).write_text(t10.sidecar(v))
    a.write(out/'JOINT_PROFILE_BUDGETS.json',budgets)
    mx=lambda key:max(x.get(key,0.) for x in budgets)
    signal=max(abs(x['target_mean_increment_K']) for x in budgets)
    r={'old_cubic_projection':old,'base_cell_error_K':mx('base_cell_error_K'),
       'corrected_cell_error_K':mx('corrected_cell_error_K'),'mass_relative':mx('mass_relative'),
       'heat_increment_relative':mx('mean_increment_error_K')/max(signal,1e-300),
       'max_moho_flux_gap_W_m2':mx('moho_flux_gap_W_m2'),'max_moho_temperature_gap_K':mx('moho_temperature_gap_K'),
       'max_abs_correction_K':mx('max_abs_correction_K'),
       'max_abs_thickness_change_from_cubic_m':max(abs(x['thickness_change_from_cubic_m']) for x in budgets),
       'max_cell_matrix_cond':mx('cell_matrix_cond')}
    r['screen_pass']=bool(r['mass_relative']<=g6.TOL['mass_relative'] and
        r['heat_increment_relative']<=g6.TOL['heat_increment_relative'] and
        r['max_moho_flux_gap_W_m2']<=g6.TOL['moho_flux_W_m2'] and
        r['max_moho_temperature_gap_K']<=g6.TOL['moho_temperature_K'] and
        r['corrected_cell_error_K']<=TOL['corrected_cell_absolute_K'] and
        r['corrected_cell_error_K']<=TOL['relative_reduction']*r['base_cell_error_K'] and
        r['max_abs_correction_K']<=TOL['sidecar_max_K'])
    a.write(out/'PROJECTION_REPORT.json',r)
    return r,v,rows

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-extended-pilot',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); g8.check_helpers(); selftest()
    for n,p in [('arcana_g11_adaptive_pilot.py','caafab6df23e7b9a51e6463a435c1013d83ff173'),
        ('arcana_g10r1_thermal_consumer.py','63178aa33312c1be425a9c52eb945f762a2c1349'),
        ('arcana_g10b_consumer_resolve.py','837f5102b8216226c15d255961e5f6c862795469'),
        ('arcana_g8_staggered_restart.py','0fd003aeb5a52e59ad33550eaa740e363a582b59')]:
        a.need(g7.blob(Path(__file__).with_name(n))==p,'HELPER_PIN:'+n)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g11','R6_THERMO_G11_ADAPTIVE_PILOT_NEW01',G11_PIN,G11_STATUS),
          ('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',g11.B_PIN,g11.B_STATUS),
          ('t','R6_THERMO_G10R1_THERMAL_CONSUMER_NEW01',b10.G10R1_PIN,b10.G10R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g11']; prior=a.read(p/'G11_REPORT.json')
    a.need(prior['screen_pass'] and prior['accepted_checkpoint_sha256']==CP_PIN and
        prior['accepted_experimental_elapsed_years']==START_YEAR and
        manifests['g11']['G10B_manifest_sha256']==g11.B_PIN,'G11_LINEAGE')
    old=p/prior['accepted_checkpoint']; startold=g11.load(old,CP_PIN)
    cm=a.read(c10.OUT/'MANIFEST.json'); a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    probe=g8.binary(parents['t']/'build','probe.exe',native)
    asm=g8.binary(parents['b']/'assembly_build','assembly_only.exe',native)
    exe=g8.binary(parents['b']/'solve_build','solve.exe',native)
    for q in (parents['b']/'assembly_build',parents['b']/'solve_build'):
        a.need(a.sha(q/'MOD_ArcanaRuntime.f90')==a.sha(parents['t']/'build/MOD_ArcanaRuntime.f90'),'LOADER_LINEAGE')
    ctl=dict(a.read(old/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
    a.need((old/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'CONTROL_REPLAY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(q) for q in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G11_manifest':G11_PIN,'start_checkpoint':CP_PIN,'runner_sha256':a.sha(Path(__file__)),
        'candidates_years':CANDIDATES,'tolerances':TOL,'maximum_native_solves':4,'additional_builds':0,
        'selection':'Descending preflight 25,10,5,1; no coupled retry in this run.',
        'projection':'Match fixed-capacity cell means up to nonlinear energy shift; update density and thickness jointly, restore Moho flux; original thermal state retained.',
        'thermal_substep_years':.5,'thermal_refinement_substep_years':1.,**c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'native_solves_attempted':0,'preflight':{},'additional_builds':0,'physical_acceptance':False,**c.SCOPE}
    try:
        s,z,th,_=startold
        print('G12_MIGRATE_YEAR12',flush=True)
        deck=out/'migration_deck'; pr,v,rows=project(old,s,z,th,deck)
        report['migration_projection']=pr; a.need(pr['screen_pass'],'MIGRATION_PROJECTION')
        report['native_solves_attempted']+=1
        mr,ms=g11.mechanical(out/'migration_mechanics',deck,old,v,rows,probe,asm,exe,native,ctl,env)
        report['migration_mechanics']=mr; a.need(mr['screen_pass'],'MIGRATION_MECHANICS')
        migration={}
        with np.load(old/'mechanical.npz') as x,np.load(ms) as y:
            for f in g7.FIELDS:
                signal=prior['mechanical_fields'][f]['signal']
                diff=g7.maxabs(y[f]-x[f])
                migration[f]={'difference':diff,'previous_10year_signal':signal,
                    'ratio':diff/signal,'screen_pass':bool(diff<=TOL['migration_signal_fraction']*signal)}
        report['migration_response']=migration
        a.need(all(x['screen_pass'] for x in migration.values()),'MIGRATION_RESPONSE')
        cp=out/'checkpoint_start'
        pin=g11.checkpoint(old,deck,ms,cp,START_YEAR,{'parent':CP_PIN,'G11_manifest':G11_PIN,'projection':'G12_JOINT'})
        report['start_checkpoint_sha256']=pin; start=g11.load(cp,pin)
        selected=None
        for years in CANDIDATES:
            print('G12_PREFLIGHT',years,flush=True)
            end,thermal,tr,m=g11.trajectory(*start,years,.5)
            rough,roughth,rr,_=g11.trajectory(*start,years,1.)
            oldE=start[2]['two_half_energy_increment_J']
            td=g5.difference(m,roughth['two_half_energy_increment_J']-oldE,m,thermal['two_half_energy_increment_J']-oldE)
            pos=g11.distance(end,rough); h=g4.relative(end['thickness_m'],rough['thickness_m'])
            d=out/f'candidate_{years}'; pr,v,rows=project(cp,start[0],end,thermal,d)
            r={'trajectory':tr,'coarser_trajectory':rr,'thermal_refinement':td,
                'position_refinement_m':pos,'thickness_refinement_relative':h,'projection':pr,
                'screen_pass':bool(tr['screen_pass'] and rr['screen_pass'] and td['screen_pass'] and pr['screen_pass'] and
                    pos<=TOL['position_m'] and h<=TOL['thickness_relative'])}
            a.write(d/'PREFLIGHT_REPORT.json',r); report['preflight'][str(years)]=r
            print('G12_PREFLIGHT_RESULT',years,r['screen_pass'],pr['corrected_cell_error_K'],flush=True)
            if r['screen_pass']: selected=(years,d,v,rows); break
        a.need(selected is not None,'NO_ADMISSIBLE_CANDIDATE')
        years,d,v,rows=selected; report['selected_years']=years
        report['native_solves_attempted']+=1
        cr,cs=g11.mechanical(out/'coarse_mechanics',d,cp,v,rows,probe,asm,exe,native,ctl,env)
        report['coarse_mechanics']=cr; a.need(cr['screen_pass'],'COARSE_MECHANICS')
        coarse=out/'checkpoint_coarse'
        cpin=g11.checkpoint(cp,d,cs,coarse,START_YEAR+years,{'parent':pin,'macro_years':years,'projection':'G12_JOINT'})
        current=cp; curpin=pin
        for i in (1,2):
            print('G12_REFINED_HALF',i,years/2,flush=True)
            st=g11.load(current,curpin); e,t,tr,_=g11.trajectory(*st,years/2,.5)
            d=out/f'half_{i}_deck'; pr,v,rows=project(current,st[0],e,t,d)
            report[f'half_{i}']={'trajectory':tr,'projection':pr}
            a.need(tr['screen_pass'] and pr['screen_pass'],'HALF_PREFLIGHT')
            report['native_solves_attempted']+=1
            mr,ms=g11.mechanical(out/f'half_{i}_mechanics',d,current,v,rows,probe,asm,exe,native,ctl,env)
            report[f'half_{i}']['mechanics']=mr; a.need(mr['screen_pass'],'HALF_MECHANICS')
            nxt=out/f'checkpoint_half_{i}'
            npin=g11.checkpoint(current,d,ms,nxt,START_YEAR+i*years/2,
                {'parent':curpin,'macro_years':years/2,'projection':'G12_JOINT'})
            report[f'half_{i}']['checkpoint_sha256']=npin; current,curpin=nxt,npin
        cmp=g11.compare(start,g11.load(coarse,cpin),g11.load(current,curpin))
        fields=g11.field_compare(cp,coarse,current)
        report.update(coupling_comparison=cmp,mechanical_fields=fields)
        report['screen_pass']=bool(cmp['screen_pass'] and all(x['screen_pass'] for x in fields.values()))
        if report['screen_pass']:
            report.update(accepted_experimental_elapsed_years=START_YEAR+years,additional_time_advance_years=years,
                accepted_checkpoint=str(current.relative_to(out)),accepted_checkpoint_sha256=curpin)
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin,'PARENT_MUTATION')
    status='G12_JOINT_PROFILE_EXTENDED_TRAJECTORY_PASS__MULTISCALE_REQUIRED' if report['screen_pass'] else 'G12_EXTENDED_TRAJECTORY_BLOCKED'
    report.update(status=status,limitations=[
        'Nodal lumped mass and sensible heat, not native FE weighted mass; fixed G5 cell capacities.',
        'Sidecar matches cell means, not unique pointwise temperature or within-cell gradients.',
        'The old cubic density moment is not invariant; thickness is recalculated from corrected density.',
        'Passive parcel geometry remains; no isostasy, phase changes, pressure work or natural exterior.',
        'Only bounded macrostep; no general adaptive retry or production authorization.'])
    a.write(out/'G12_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G11_manifest_sha256':G11_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G12_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
