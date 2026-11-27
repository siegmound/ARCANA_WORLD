#!/usr/bin/env python3
"""G13: conservative CN thermal stepping, independent frozen spectral reference,
and moving regional 25-year continuation from G12. No physical promotion.
Geometry substeps remain 0.5 year; only thermal refresh is accelerated.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import traceback
import numpy as np
from scipy.linalg import eigh_tridiagonal
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g5_column_heat as g5
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g10r1_thermal_consumer as t10
import arcana_g10b_consumer_resolve as b10
import arcana_g11_adaptive_pilot as g11
import arcana_g12_joint_profile_extended as g12

G12_PIN='38e77544e72253ea83c7b7260c83fccb54519288099f08a35dc4eaaeb1215059'
G12_STATUS='G12_JOINT_PROFILE_EXTENDED_TRAJECTORY_PASS__MULTISCALE_REQUIRED'
CP_PIN='cc4a7b6c4795f9fdbfe7546010c9fe4427095fe7e430e8854603f470e08fb5c0'
START=37.
YEARS=25.
DT_CANDIDATES=(12.5,6.25,2.5,1.25,.5)
# 6.25 and 1.25 do not align with the retained half-year geometry grid.
DT_CANDIDATES=tuple(x for x in DT_CANDIDATES if x/.5==int(x/.5))
LINEAR_TOL=1e-12
ENERGY_TOL=g5.TOL['energy_transfer_relative']

def operator(m,z):
    n=m['n']; area,h=g5.geometry(z,n)
    k,H,coeff,cap=(m[x] for x in ('k','H','coeff','capacity'))
    dx=h/n
    faces=np.linspace(0.,1.,n+1)
    qref=k[:,:,None]/h[:,:,None]*np.einsum('plk,jk->plj',
              coeff[:,:,1:]*np.arange(1,4),faces[:,None]**np.arange(3))
    gap=g5.rel(qref[:,0,-1],qref[:,1,0])
    a.need(gap<=g5.TOL['interface_flux_relative'],'REFERENCE_MOHO')
    moho=.5*(qref[:,0,-1]+qref[:,1,0])
    qref[:,0,-1]=moho; qref[:,1,0]=moho
    # Conductance in W/K; face ordering top to LAB, one shared Moho.
    g=np.empty((384,2*n+1))
    g[:,0]=2*k[:,0]/dx[:,0]; g[:,1:n]=k[:,0,None]/dx[:,0,None]
    g[:,n]=1/(dx[:,0]/(2*k[:,0])+dx[:,1]/(2*k[:,1]))
    g[:,n+1:-1]=k[:,1,None]/dx[:,1,None]; g[:,-1]=2*k[:,1]/dx[:,1]
    g*=area[:,None]
    q=np.concatenate((qref[:,0],qref[:,1,1:]),axis=1)*area[:,None]
    H=np.broadcast_to((area[:,None]*H*dx)[:,:,None],cap.shape).reshape(384,-1)
    C=cap.reshape(384,-1)
    a.need(np.all(g>0) and np.all(C>0) and np.isfinite(q).all(),'OPERATOR_PROPERTIES')
    return g,q,H,C,gap

def flux(g,q,T):
    return q+g*np.diff(np.pad(T,((0,0),(1,1))),axis=1)

def tri_solve(lo,d,hi,b):
    # Batched Thomas, strictly diagonally dominant M-matrix.
    d=d.copy(); b=b.copy()
    for j in range(1,d.shape[1]):
        f=lo[:,j-1]/d[:,j-1]
        d[:,j]-=f*hi[:,j-1]; b[:,j]-=f*b[:,j-1]
    a.need(np.all(d>0) and np.isfinite(d).all(),'THOMAS_PIVOT')
    x=np.empty_like(b); x[:,-1]=b[:,-1]/d[:,-1]
    for j in range(d.shape[1]-2,-1,-1):
        x[:,j]=(b[:,j]-hi[:,j]*x[:,j+1])/d[:,j]
    return x

def cn(m,delta,z,years,op=None):
    g,q,H,C,gap=operator(m,z) if op is None else op
    dt=years*g5.YEAR; n=m['n']; theta=.5
    old=delta.reshape(384,-1); T=old/C
    f=flux(g,q,T)
    r=dt/C*(np.diff(f,axis=1)+H)
    l=dt*g[:,1:-1]/C[:,1:]; u=dt*g[:,1:-1]/C[:,:-1]
    gamma=dt*(g[:,:-1]+g[:,1:])/C
    # CN monotonicity sufficient condition; do not claim arbitrary dt accuracy.
    a.need(np.max((1-theta)*gamma)<=1,'CN_MONOTONICITY')
    d=1+theta*gamma; lo=-theta*l; hi=-theta*u
    incT=tri_solve(lo,d,hi,r)
    ax=d*incT
    ax[:,1:]+=lo*incT[:,:-1]; ax[:,:-1]+=hi*incT[:,1:]
    residual=g5.rel(ax,r)
    end=old+C*incT; actual=end-old
    ff=flux(g,q,T+theta*actual/C)
    expected=dt*(np.diff(ff,axis=1)+H)
    layer_actual=actual.reshape(384,2,n).sum(axis=-1)
    layer_expected=np.column_stack((dt*(ff[:,n]-ff[:,0]+H[:,:n].sum(axis=1)),
                                   dt*(ff[:,-1]-ff[:,n]+H[:,n:].sum(axis=1))))
    scale=np.column_stack((dt*(abs(ff[:,n])+abs(ff[:,0])+H[:,:n].sum(axis=1)),
                          dt*(abs(ff[:,-1])+abs(ff[:,n])+H[:,n:].sum(axis=1))))
    scale+=np.abs(actual).reshape(384,2,n).sum(axis=-1)
    le=float(np.max(abs(layer_actual-layer_expected)/np.maximum(scale,1.)))
    ce=float(np.max(abs(actual.sum(axis=1)-dt*(ff[:,-1]-ff[:,0]+H.sum(axis=1)))/
                     np.maximum(scale.sum(axis=1),1.)))
    cell=float(np.max(abs(actual-expected)/np.maximum(dt*(abs(ff[:,:-1])+abs(ff[:,1:])+H)+abs(actual),1.)))
    final=end.reshape(delta.shape)
    temp=m['temp0']+final/m['capacity']
    a.need(np.isfinite(temp).all() and np.all(temp>0),'CN_POSITIVE_T')
    total=m['heat']+final
    te=g5.rel(total.sum(axis=(1,2)),m['heat'].sum(axis=(1,2))+final.sum(axis=(1,2)))
    return final,{'years':years,'explicit_equivalent_CFL':float(gamma.max()),
        'linear_residual':residual,'max_layer_transfer_relative_error':le,
        'max_column_transfer_relative_error':ce,'max_cell_transfer_relative_error':cell,
        'max_absolute_state_energy_relative_error':te,'reference_moho_flux_gap':gap,
        'radiogenic_energy_J':float(dt*H.sum()),'surface_outward_energy_J':float(dt*ff[:,0].sum()),
        'LAB_inward_energy_J':float(dt*ff[:,-1].sum()),'moho_upward_energy_J':float(dt*ff[:,n].sum()),
        'internal_energy_increment_J':float(actual.sum()),'screen_pass':bool(
            residual<=LINEAR_TOL and max(le,ce,cell)<=ENERGY_TOL and te<=g5.TOL['absolute_energy_relative'])}

def spectral(m,delta,z):
    """Exact-in-time frozen semidiscrete reference in mass-normalized basis.
    Separate symmetric eigenproblem per column. Stable expm1 for increments.
    """
    g,q,H,C,gap=operator(m,z); S=np.sqrt(C); T=delta.reshape(384,-1)/C
    diag=-(g[:,:-1]+g[:,1:])/C
    off=g[:,1:-1]/(S[:,:-1]*S[:,1:])
    f=(np.diff(flux(g,q,T),axis=1)+H)/S
    spec=[]; err=0.; ortho=0.
    for i in range(384):
        w,V=eigh_tridiagonal(diag[i],off[i])
        a.need(np.all(w<0),'SPECTRAL_NEGATIVE')
        av=diag[i,:,None]*V; av[1:]+=off[i,:,None]*V[:-1]; av[:-1]+=off[i,:,None]*V[1:]
        err=max(err,g5.rel(av,V*w))
        ortho=max(ortho,float(np.max(abs(V.T@V-np.eye(len(w))))))
        spec.append((w,V,V.T@f[i]))
    a.need(err<=1e-10 and ortho<=1e-10,'SPECTRAL_EIGEN_CHECK')
    def exact(years):
        d=np.array([S[i]*(V@((np.expm1(w*years*g5.YEAR)/w)*b)) for i,(w,V,b) in enumerate(spec)])
        return delta+d.reshape(delta.shape)
    return exact,{'max_eigen_residual':err,'max_orthogonality_error':ortho}

def frozen(m,delta,z,years,step):
    op=operator(m,z); d=delta.copy(); reports=[]
    n=round(years/step); a.need(n>0 and n*step==years,'FROZEN_TIME')
    for _ in range(n):
        d,r=cn(m,d,z,step,op); reports.append(r)
    a.need(all(r['screen_pass'] for r in reports),'FROZEN_CN')
    return d,summary(reports,delta,d)

def summary(reports,old,new):
    net=float((new-old).sum()); expect=sum(x['internal_energy_increment_J'] for x in reports)
    closure=abs(net-expect)/max(sum(abs(x['internal_energy_increment_J']) for x in reports),1.)
    return {'substeps':len(reports),'max_explicit_equivalent_CFL':max(x['explicit_equivalent_CFL'] for x in reports),
        'max_linear_residual':max(x['linear_residual'] for x in reports),
        'max_layer_energy_error':max(x['max_layer_transfer_relative_error'] for x in reports),
        'max_column_energy_error':max(x['max_column_transfer_relative_error'] for x in reports),
        'max_cell_energy_error':max(x['max_cell_transfer_relative_error'] for x in reports),
        'energy_increment_J':net,'cumulative_budget_error':closure,
        'screen_pass':bool(all(x['screen_pass'] for x in reports) and closure<=ENERGY_TOL)}

def selftest():
    n=8; shape=(384,2,n)
    coeff=np.zeros((384,2,4)); coeff[:,:,0]=300.
    cap=np.full(shape,1e6*(1000/n)*2800*1000)
    m={'n':n,'coeff':coeff,'k':np.full((384,2),2.5),'H':np.zeros((384,2)),
       'capacity':cap,'heat':cap*300.,'temp0':np.full(shape,300.)}
    z={'area_m2':np.full(128,3e6).tolist(),'thickness_m':np.full((128,3,2),1000.).tolist()}
    d,r=cn(m,np.zeros(shape),z,1.)
    a.need(r['screen_pass'] and np.all(d==0),'CONSTANT_CN')
    coeff[:,:,1]=100.; coeff[:,1,0]=400.
    d,r=cn(m,np.zeros(shape),z,1.)
    a.need(r['screen_pass'] and np.all(d==0),'LINEAR_STEADY_CN')
    m['H'][:]=8e-7
    d,r=cn(m,np.zeros(shape),z,1.)
    exact,sp=spectral(m,np.zeros(shape),z)
    coarse=g5.difference(m,d,m,exact(1.))
    fine,_=frozen(m,np.zeros(shape),z,1.,.5)
    f=g5.difference(m,fine,m,exact(1.))
    a.need(r['screen_pass'] and f['max_temperature_difference_K']<coarse['max_temperature_difference_K']/3.5,'CN_ORDER_FIXTURE')
    # dt above explicit sufficient stability, but inside CN monotonicity.
    d,r=cn(m,np.zeros(shape),z,150.)
    a.need(r['screen_pass'] and r['explicit_equivalent_CFL']>g5.TOL['explicit_cfl'],'CN_ABOVE_EXPLICIT_CFL')
    print('G13_CN_SELFTEST_PASS',flush=True)

def path(z,v,years):
    n=round(years/.5); a.need(n*.5==years and n>0,'MOVING_TIME')
    states=[]; reports=[]
    for _ in range(n):
        z,r=g8.move(z,v,.5); states.append(z); reports.append(r)
    a.need(all(r['screen_pass'] for r in reports),'GEOMETRY_SCREEN')
    return states,reports

def moving(m,old,states,dt):
    stride=round(dt/.5); a.need(stride*.5==dt and len(states)%stride==0,'THERMAL_GRID_ALIGNMENT')
    d=old.copy(); reports=[]
    for z in states[stride-1::stride]:
        d,r=cn(m,d,z,dt); reports.append(r)
    return d,summary(reports,old,d)

def reference(m,old,states):
    d=old.copy()
    for z in states:
        d,r=g5.step(m,d,z,.5); a.need(r['screen_pass'],'EXPLICIT_REFERENCE')
    return d

def thermal_state(th,m,d):
    return dict(th,two_half_energy_increment_J=d,two_half_temperature_K=m['temp0']+d/m['capacity'])

def compare_heat(m,old,d,ref):
    return g5.difference(m,d-old,m,ref-old)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-multiscale-pilot',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); g8.check_helpers(); selftest()
    for n,p in [('arcana_g11_adaptive_pilot.py','caafab6df23e7b9a51e6463a435c1013d83ff173'),
        ('arcana_g12_joint_profile_extended.py','9f00582e7948635bdac23b4e65584fe5291a0e7b'),
        ('arcana_g10r1_thermal_consumer.py','63178aa33312c1be425a9c52eb945f762a2c1349'),
        ('arcana_g10b_consumer_resolve.py','837f5102b8216226c15d255961e5f6c862795469'),
        ('arcana_g8_staggered_restart.py','0fd003aeb5a52e59ad33550eaa740e363a582b59')]:
        a.need(g7.blob(Path(__file__).with_name(n))==p,'HELPER_PIN:'+n)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g12','R6_THERMO_G12_JOINT_PROFILE_EXTENDED_NEW01',G12_PIN,G12_STATUS),
          ('b','R6_THERMO_G10B_CONSUMER_RESOLVE_NEW01',g11.B_PIN,g11.B_STATUS),
          ('t','R6_THERMO_G10R1_THERMAL_CONSUMER_NEW01',b10.G10R1_PIN,b10.G10R1_STATUS)]
    parents={}; manifests={}
    for key,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[key]=p; manifests[key]=c.verified(p,pin,status)
        a.need(manifests[key]['source_sha']==a.SHA and all(manifests[key][k]==v for k,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g12']; prior=a.read(p/'G12_REPORT.json')
    a.need(prior['screen_pass'] and prior['accepted_checkpoint_sha256']==CP_PIN and
        prior['accepted_experimental_elapsed_years']==START and manifests['g12']['G11_manifest_sha256']==g12.G11_PIN,'G12_LINEAGE')
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
    a.write(out/'POLICY.json',{'G12_manifest':G12_PIN,'checkpoint':CP_PIN,'runner_sha256':a.sha(Path(__file__)),
        'frozen_horizons_years':[25,100,1000,10000],'frozen_max_steps':1000,
        'moving_macro_years':YEARS,'geometry_dt_years':.5,'thermal_dt_candidates':DT_CANDIDATES,
        'thermal_tolerances':g5.TOL,'coupling_tolerances':g11.TOL,'linear_tol':LINEAR_TOL,
        'max_native_solves':3,'additional_builds':0,'frozen_scope':'Numerical reference only, no calendar advance.',
        'moving_scope':'Matched geometry path for thermal comparison; mechanical midpoint refresh for coupling.',
        **c.SCOPE})
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    report={'screen_pass':False,'native_solves_attempted':0,'additional_builds':0,'physical_acceptance':False,**c.SCOPE}
    try:
        print('G13_FROZEN_SPECTRAL_REFERENCE',flush=True)
        exact,sp=spectral(m,old,z); report['spectral_reference']=sp
        frozen_reports={}
        for years in (25,100,1000,10000):
            ref=exact(years); trials={}; accepted=None
            for steps in (1,2,4,10,20,40,100,200,400,1000):
                dt=years/steps
                g,_,_,C,_=operator(m,z)
                if float(np.max(dt*g5.YEAR*(g[:,:-1]+g[:,1:])/C))>2.:
                    trials[str(steps)]={'screen_pass':False,'reason':'CN_MONOTONICITY'}; continue
                d,r=frozen(m,old,z,years,dt); cmp=compare_heat(m,old,d,ref)
                trials[str(steps)]={'dt_years':dt,'conservation':r,'comparison':cmp,
                    'screen_pass':bool(r['screen_pass'] and cmp['screen_pass'])}
                if trials[str(steps)]['screen_pass']:
                    accepted=steps; break
            frozen_reports[str(years)]={'trials':trials,'accepted_steps':accepted,
                'accepted_dt_years':years/accepted if accepted else None,'screen_pass':accepted is not None}
            report['frozen_benchmarks']=frozen_reports
            print('G13_FROZEN_RESULT',years,accepted,flush=True)
        # Long frozen benchmarks are characterization; the 25y case is required.
        a.need(frozen_reports['25']['screen_pass'],'FROZEN_25Y')
        print('G13_MOVING_THERMAL_PREFLIGHT',flush=True)
        states,geom=path(z,v,YEARS)
        ref=reference(m,old,states)
        selected=None; trials={}
        for dt in DT_CANDIDATES:
            d,r=moving(m,old,states,dt); cmp=compare_heat(m,old,d,ref)
            trials[str(dt)]={'conservation':r,'explicit_comparison':cmp,
                'screen_pass':bool(r['screen_pass'] and cmp['screen_pass'])}
            report['moving_thermal_trials']=trials
            if trials[str(dt)]['screen_pass']:
                selected=dt; break
        a.need(selected is not None,'NO_THERMAL_STEP')
        report['selected_thermal_dt_years']=selected
        report['moving_geometry_max_mass_error']=max(x['max_owner_layer_mass_error'] for x in geom)
        report['moving_geometry_max_area_error']=max(x['max_area_closure_relative_error'] for x in geom)
        # Guard macro deformation in addition to each half-year move.
        pp=np.asarray(z['canonical_unit_xyz']); R=z['radius_m']
        edges=g4.geometry_edges(np.asarray(z['transport_triangles_zero_based']))
        emin=min(R*np.arctan2(np.linalg.norm(np.cross(pp[u],pp[w])),pp[u]@pp[w]) for u,w in edges)
        macro=max(g11.distance(z,states[-1])/emin,
            float(np.max(abs(np.asarray(states[-1]['area_m2'])/np.asarray(z['area_m2'])-1))),
            g4.relative(states[-1]['thickness_m'],z['thickness_m']))
        report['macro_geometry_fraction']=macro
        a.need(macro<=g11.TOL['macro_geometry_fraction'],'MACRO_GEOMETRY')
        deck=out/'coarse_deck'; pr,vals,rows=g12.project(cp,s,states[-1],thermal_state(th,m,d),deck)
        report['coarse_projection']=pr; a.need(pr['screen_pass'],'COARSE_PROJECTION')
        print('G13_COARSE_SOLVE',flush=True); report['native_solves_attempted']+=1
        cr,cs=g11.mechanical(out/'coarse_mechanics',deck,cp,vals,rows,probe,asm,exe,native,ctl,env)
        report['coarse_mechanics']=cr; a.need(cr['screen_pass'],'COARSE_MECHANICS')
        coarse=out/'checkpoint_coarse'
        cpin=g11.checkpoint(cp,deck,cs,coarse,START+YEARS,{'parent':CP_PIN,'G12_manifest':G12_PIN,'integrator':'CN'})
        current=cp; pin=CP_PIN
        for i in (1,2):
            print('G13_REFINED_HALF',i,flush=True)
            st=g11.load(current,pin); ss,zz,tt,vv=st
            # Each path uses the same selected thermal grid; compare independently
            # against explicit on its own geometry. No implicit error cancellation.
            hs,hg=path(zz,vv,YEARS/2); od=tt['two_half_energy_increment_J']
            nd,nr=moving(m,od,hs,selected); re=reference(m,od,hs)
            tc=compare_heat(m,od,nd,re)
            dk=out/f'half_{i}_deck'; pr,vals,rows=g12.project(current,ss,hs[-1],thermal_state(tt,m,nd),dk)
            report[f'half_{i}']={'thermal':nr,'explicit_comparison':tc,'projection':pr,
                'max_mass_error':max(x['max_owner_layer_mass_error'] for x in hg)}
            a.need(nr['screen_pass'] and tc['screen_pass'] and pr['screen_pass'],'HALF_THERMAL_PROJECTION')
            report['native_solves_attempted']+=1
            mr,ms=g11.mechanical(out/f'half_{i}_mechanics',dk,current,vals,rows,probe,asm,exe,native,ctl,env)
            report[f'half_{i}']['mechanics']=mr; a.need(mr['screen_pass'],'HALF_MECHANICS')
            nxt=out/f'checkpoint_half_{i}'
            pin=g11.checkpoint(current,dk,ms,nxt,START+i*YEARS/2,{'parent':pin,'integrator':'CN'})
            report[f'half_{i}']['checkpoint_sha256']=pin; current=nxt
        cmp=g11.compare(start,g11.load(coarse,cpin),g11.load(current,pin))
        fields=g11.field_compare(cp,coarse,current)
        report.update(coupling_comparison=cmp,mechanical_fields=fields)
        report['screen_pass']=bool(cmp['screen_pass'] and all(x['screen_pass'] for x in fields.values()))
        if report['screen_pass']:
            report.update(accepted_experimental_elapsed_years=START+YEARS,additional_time_advance_years=YEARS,
                accepted_checkpoint=str(current.relative_to(out)),accepted_checkpoint_sha256=pin,
                thermal_substeps_per_macro=int(YEARS/selected),explicit_reference_substeps=50)
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for key,_,pin0,_ in refs:
        a.need(c.inventory(parents[key])==manifests[key]['files'] and a.sha(parents[key]/'MANIFEST.json')==pin0,'PARENT_MUTATION')
    status='G13_CN_MULTISCALE_PILOT_PASS__ADAPTIVE_TRAJECTORY_REQUIRED' if report['screen_pass'] else 'G13_CN_MULTISCALE_PILOT_BLOCKED'
    report.update(status=status,limitations=[
        'Frozen spectral reference is exact for the discrete linear operator only; not a geological trajectory.',
        'Moving geometry still uses half-year steps and explicit references for qualification; no wall-time speedup claimed.',
        'Same G12 nodal reconstruction, passive parcel geometry and fixed cell capacities.',
        'Only bounded 25-year moving macrostep; no global, natural exterior, full thermodynamics or canonical T1.'])
    a.write(out/'G13_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G12_manifest_sha256':G12_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G13_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
