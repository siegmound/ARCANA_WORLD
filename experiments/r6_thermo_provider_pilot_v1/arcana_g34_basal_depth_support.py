#!/usr/bin/env python3
"""G34: independent OneBar depth/support sensitivity on retained PRE columns.
No native runs, solve, mantle field, material admission, or time advance.
The 300 km ceiling is an exploratory C10 compatibility bound, not physical authority.
"""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_g33_native_basal_coupling_audit as g33
import arcana_g32_corrected_global_operator as g32
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27

PIN='3b371431b299c3f6b4f419ff8d4da1f4ab94c7ede19c0bc15efddd306e80be98'
STATUS='G33_NATIVE_BASAL_CONSTITUTIVE_PASS__MANTLE_PROVIDER_AUTHORITY_REQUIRED'
AUTH='G34_BASAL_DEPTH_SUPPORT_DIAGNOSTIC_ONLY_V1'
need,sha,read,write,inventory=g33.need,g33.sha,g33.read,g33.write,g33.inventory
SOURCE,SCOPE=g33.SOURCE,g33.SCOPE
N,E,Q=g33.N,g33.E,g33.Q
DEPTHS=(1000,50000,100000,150000,200000,250000,300000)
STEPS=(1000,500)
BLOCK=4096
MODELS=g33.MODELS
def verify(p):
    m=g32.verify(p,PIN,STATUS)
    need(m['G23_manifest_sha256']==g25.PINS[0] and m['G26_manifest_sha256']==g27.PIN
         and m['G32_manifest_sha256']==g33.PIN,'G33_LINEAGE')
    need(read(p/'G33_REPORT.json')['screen_pass'],'G33_SCREEN')
    return m
def read_pre(p):
    with p.open() as f:
        need(f.readline().split()==['ARCANA_R6_PRE_ORBDATA_RUNTIME_V1',
            'arcana_worldsim.r6.shellset_owner_bound_runtime.v1',str(N)],'PRE_HEADER')
        x=np.loadtxt(f,dtype=np.float64)
    need(x.shape==(N,51) and np.isfinite(x).all()
         and np.array_equal(x[:,0],np.arange(1,N+1)),'PRE_RECORDS')
    need(np.all(x[:,15]>=0) and np.all(x[:,16]>=0) and np.all(x[:,17]>0)
         and np.max(abs(x[:,15]+x[:,16]-x[:,17]))<1e-6,'PRE_LAYER_DEPTHS')
    need(np.all(x[:,34]>0) and np.all(x[:,36]>0) and np.all(x[:,20]>0),'PRE_ADIABAT')
    return x
def node_temperature(x,z):
    # Direct translation of the frozen evaluator, using its 1-based fields.
    z=np.asarray(z)[:,None]
    d=z-x[None,:,39]; a=((x[None,:,41]*d+x[None,:,42])*d+x[None,:,43])*d+x[None,:,44]
    d=z-x[None,:,45]; b=((x[None,:,47]*d+x[None,:,48])*d+x[None,:,49])*d+x[None,:,50]
    c=x[None,:,20]*np.exp(x[None,:,34]*9.82*(z-x[None,:,17])/x[None,:,36])
    t=np.where(z<x[None,:,15],a,np.where(z<=x[None,:,17],b,c))
    need(np.isfinite(t).all() and np.all(t>0),'NODE_TEMPERATURE')
    return t
def coefficients(ctl):
    e=float(ctl['eCreep'])
    A,B,C=(np.asarray(ctl[k],dtype=float) for k in ('aCreep','bCreep','cCreep'))
    need(A.shape==B.shape==C.shape==(2,) and np.all(A>0) and e>0,'REOLOGY')
    return e,-np.log(A)/e,-B/e,-C/e
def distribution(x,w):
    return g33.distribution(x,w)
def integrate(x,nodes,weights,zc,lab,controls,dz):
    z=(np.arange(DEPTHS[-1]//dz)+.5)*dz
    T=node_temperature(x,z)
    z=z[:,None]
    out={k:{'glue':np.empty((len(DEPTHS),Q)),
            'below_lab_fraction':np.empty((len(DEPTHS),Q)),
            'floor_depth_fraction':np.empty((len(DEPTHS),Q))} for k in MODELS}
    ix=np.asarray(DEPTHS)//dz-1
    for j in range(0,Q,BLOCK):
        sl=slice(j,min(j+BLOCK,Q)); n=nodes[sl]; w=weights[sl]
        t=T[:,n[:,0]]*w[None,:,0]+T[:,n[:,1]]*w[None,:,1]+T[:,n[:,2]]*w[None,:,2]
        need(np.isfinite(t).all() and np.min(t)>=200.,'IP_TEMPERATURE')
        layer=z>=zc[None,sl]
        below=z>lab[None,sl]
        for k in MODELS:
            e,al,b,c=controls[k]
            arg=al[layer.astype(np.int8)]+(b[layer.astype(np.int8)]+c[layer.astype(np.int8)]*z)/t
            floor=arg<=-87.
            inc=dz*np.exp(np.maximum(arg,-87.))
            cum=np.cumsum(inc,axis=0)
            vals=cum[ix]
            out[k]['glue'][:,sl]=np.power(vals,-e)
            out[k]['below_lab_fraction'][:,sl]=np.cumsum(inc*below,axis=0)[ix]/vals
            out[k]['floor_depth_fraction'][:,sl]=np.cumsum(floor,axis=0)[ix]/(ix[:,None]+1)
    for k in MODELS:
        v=out[k]
        need(np.isfinite(v['glue']).all() and np.all(v['glue']>0)
             and np.all(np.diff(v['glue'],axis=0)<=0),'COMPLIANCE_MONOTONIC')
        need(np.all((v['below_lab_fraction']>=0)&(v['below_lab_fraction']<=1+1e-12)),'FRACTION')
    return out
def audit(p,q,r,s,out):
    geo=g33.geometry(r,q)
    ids,w,H,target,R=geo
    base=p/MODELS[0]
    x=read_pre(base/'regional_PRE.dat')
    need(sha(base/'regional_PRE.dat')==sha(p/MODELS[1]/'regional_PRE.dat'),'PRE_PAIR')
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    nodes=f['ids'][:,2:].astype(np.int64)-1; weights=f['v'][:,4:7].copy()
    need(np.array_equal(f['ids'][:,:2],ids) and np.max(abs(weights.sum(axis=1)-1))<1e-10,'IP_JOIN')
    del f,H
    controls={k:coefficients(read(p/k/'CONDITIONAL_CONTROLS.json')) for k in MODELS}
    native={}
    for k in MODELS:
        d=np.fromfile(s/k/'G33_NATIVE_BASAL.bin',dtype=g33.DT)
        need(len(d)==Q and np.array_equal(d['ids'],ids) and np.isfinite(d['v']).all(),'G33_RECORDS')
        need(np.all(d['v'][:,1]==controls[k][0]) and np.all(d['v'][:,7]==1000),'G33_CONTROLS')
        native[k]=d['v'].copy()
    zc=native[MODELS[0]][:,2]; lab=zc+native[MODELS[0]][:,3]
    need(np.array_equal(native[MODELS[0]][:,2:4],native[MODELS[1]][:,2:4]),'G33_LAYER_PAIR')
    def ip(v): return np.sum(weights*v[nodes],axis=1)
    need(g33.rel(zc,ip(x[:,15]))<1e-10 and g33.rel(lab,ip(x[:,17]))<1e-10,'PRE_LAYER_REPLAY')
    print('G34_PRE_AND_QUADRATURE_VERIFIED',flush=True)
    coarse=integrate(x,nodes,weights,zc,lab,controls,1000)
    print('G34_NATIVE_STEP_RECONSTRUCTION_DONE',flush=True)
    for k in MODELS:
        need(g33.rel(coarse[k]['glue'][0],native[k][:,0])<1e-11,'G33_GLUE_REPLAY:'+k)
    fine=integrate(x,nodes,weights,zc,lab,controls,500)
    print('G34_HALF_STEP_SENSITIVITY_DONE',flush=True)
    results={}
    for k in MODELS:
        v=coarse[k]; vf=fine[k]; e=controls[k][0]
        rows=[]
        for i,depth in enumerate(DEPTHS):
            glue=v['glue'][i]; gf=vf['glue'][i]
            # Compare traction at identical speeds, rather than comparing glue with unlike units.
            speed=.05/g33.YEAR
            traction=glue*speed**e
            tf=gf*speed**e
            rows.append({'depth_m':depth,'area_fraction_LAB_reached':float(w[lab<=depth].sum()/w.sum()),
                'unclipped_traction_at_5cm_yr_Pa':distribution(traction,w),
                'area_weighted_mean_floor_depth_fraction':float(np.average(v['floor_depth_fraction'][i],weights=w)),
                'below_LAB_compliance_fraction':distribution(v['below_lab_fraction'][i],w),
                'half_step_traction_relative_inf':g33.rel(tf,traction),
                'half_step_traction_relative_l2_area_weighted':float(np.sqrt(np.sum(w*(tf-traction)**2)/np.sum(w*traction**2))),
                'half_step_traction_relative_pointwise_p95':distribution(abs(tf/traction-1),w)['area_weighted_quantiles']['0.95']})
        results[k]={'native_exponent':e,'native_1km_glue_replay_relative_inf':g33.rel(v['glue'][0],native[k][:,0]),
                    'depth_sensitivity':rows}
        np.savez_compressed(out/(k+'_DEPTH_DIAGNOSTICS.npz'),element_id=ids[:,0],ip_id=ids[:,1],
            depths_m=np.array(DEPTHS),lab_m=lab,area_m2=w,glue_1km_step=v['glue'],glue_500m_step=vf['glue'],
            below_lab_compliance_1km_step=v['below_lab_fraction'],floor_depth_fraction_1km_step=v['floor_depth_fraction'])
    return {'quadrature_points':Q,'LAB_m':distribution(lab,w),'LAB_max_nodal_m':float(x[:,17].max()),
        'depths_m':list(DEPTHS),'vertical_midpoint_steps_m':list(STEPS),'cases':results,
        'physical_depth_selected':False,'physical_mantle_reology_selected':False,
        'limitations':['Below-LAB temperatures use the existing governed adiabatic extension; not a mantle dynamics solution.',
        'OneBar uses the interpolated Moho to select two uniform analogue creep laws; D12 exclusions remain.',
        'Below-LAB compliance partition uses midpoint classification at interpolated LAB.',
        'Half-step differences are recorded, not a proof of convergence or a physical depth selection.',
        'No active shear law or corrected global RHS is generated.']}
def main():
    ap=argparse.ArgumentParser()
    for k in ('g23','g26','g32','g33','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-depth-diagnostic-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,r,s,out=(x.resolve() for x in (a.g23,a.g26,a.g32,a.g33,a.output))
    parents=((p,lambda x:g25.verify(x,0)),(q,g27.verify),(r,lambda x:g32.verify(x,g33.PIN,g33.STATUS)),(s,verify))
    before=[fn(x) for x,fn in parents]
    need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,r,s)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,
        'G32_manifest_sha256':g33.PIN,'G33_manifest_sha256':PIN,'additional_builds':0,'additional_native_assemblies':0,
        'additional_global_solves':0,'additional_time_advance_years':0,'material_assignments':0,
        'active_source_modified':False,'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        report['audit']=audit(p,q,r,s,out)
        report.update(screen_pass=True,status='G34_BASAL_DEPTH_SUPPORT_PASS__PHYSICAL_DEPTH_AND_MANTLE_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G34_BASAL_DEPTH_SUPPORT_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G34_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,'G33_manifest_sha256':PIN,
        'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,
        'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G34_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
