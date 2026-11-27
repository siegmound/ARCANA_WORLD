#!/usr/bin/env python3
"""G5 controlled 1-D material-column heat update on the accepted G4 paths.

Energy-conservative perturbation FV of the PRE initial polynomials. Frozen
mechanical density/geometry within each thermal substep, prescribed initial
surface/LAB temperature, shared Moho flux, radiogenic heat. No latent heat,
adiabatic work, thermal expansion feedback, lateral diffusion or new solve.
Experimental, never canonical T1.
"""
import argparse
from pathlib import Path
import json
import hashlib
import subprocess
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4

G4_PIN='9207eefd69425a013a32e117a8f515b40682a269a0cf5495b238a87898af3747'
G4_STATUS='G4_CONTROLLED_MOVING_COLUMN_TRANSPORT_PASS__PHYSICAL_ACCEPTANCE_PENDING'
G4_BLOB='932dd4ac5762a3b01ed12b78f595092fc4fa2ab4'
LEVELS=(16,32,64)
TOL={'energy_transfer_relative':1e-11,'absolute_energy_relative':1e-12,
     'initial_inventory_relative':1e-12,'interface_flux_relative':1e-10,
     'temperature_absolute_K':1e-7,'temperature_signal_relative':0.01,
     'temperature_signal_floor_K':1e-8,'explicit_cfl':0.45}
YEAR=g4.YEAR

def blob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def rel(x,y):
    x=np.asarray(x); y=np.asarray(y)
    return float(np.max(abs(x-y))/max(float(np.max(abs(x))),float(np.max(abs(y))),1e-300))

def flatten(s,name,tail):
    return np.asarray(s[name],float).reshape((384,)+tail)

def setup(s,n):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
    t=np.asarray(s['transport_triangles_zero_based'])
    rows=[dict(zip(FIELDS,map(float,r),strict=True)) for r in s['original_PRE_rows_tokens']]
    a.need(len(rows)==81 and t.shape==(128,3),'OWNER_INVENTORY')
    area=np.repeat(np.asarray(s['area_m2'])/3,3)
    h=flatten(s,'thickness_m',(2,))
    coeff=flatten(s,'normalized_depth_temperature_coefficients_K',(2,4))
    rho=flatten(s,'rho_reference_kg_m3',(2,))
    alpha=flatten(s,'alpha_K_inverse',(2,))
    cp=flatten(s,'cp_J_kg_K',(2,))
    k=np.array([[r[role+'_conductivity_w_m_k'] for role in ('crust','mantle')]
                 for r in rows])[t].reshape(384,2)
    H=np.array([[r[role+'_heat_production_w_m3'] for role in ('crust','mantle')]
                 for r in rows])[t].reshape(384,2)
    a.need(np.all(k>0) and np.all(H>=0) and np.all(cp>0),'MATERIAL_THERMAL_PROPERTIES')
    # Four point Gauss: exact for rho(T) and rho(T)*T with cubic T(s).
    x,w=np.polynomial.legendre.leggauss(4)
    z=(np.arange(n)[:,None]+(x+1)/2)/n
    temp=np.einsum('plk,jgk->pljg',coeff,z[:,:,None]**np.arange(4))
    dens=rho[:,:,None,None]*(1-alpha[:,:,None,None]*temp)
    a.need(np.isfinite(temp).all() and np.all(temp>0) and np.all(dens>0),'CELL_PROPERTIES')
    vol=area[:,None,None]*h[:,:,None]/n
    mass=vol*np.sum(dens*w/2,axis=-1)
    heat=vol*cp[:,:,None]*np.sum(dens*temp*w/2,axis=-1)
    cap=mass*cp[:,:,None]
    m=flatten(s,'layer_mass_kg',(2,))
    e=flatten(s,'passive_sensible_heat_tracer_J',(2,))
    a.need(rel(mass.sum(axis=-1),m)<=TOL['initial_inventory_relative'] and
           rel(heat.sum(axis=-1),e)<=TOL['initial_inventory_relative'],'G4_CELL_INVENTORY')
    return {'n':n,'mass':mass,'heat':heat,'capacity':cap,'temp0':heat/cap,
            'coeff':coeff,'k':k,'H':H,'cp':cp,'rho':rho,'alpha':alpha}

def geometry(s,n):
    area=np.repeat(np.asarray(s['area_m2'])/3,3)
    h=flatten(s,'thickness_m',(2,))
    a.need(np.all(h>0) and np.all(area>0),'THERMAL_GEOMETRY')
    return area,h

def step(model,delta,s,years):
    """Conservative explicit heat increment, with a polynomial reference flux.

    Initial exact PRE polynomial flux plus FV conductance times temperature
    perturbation. Material masses and heat capacities fixed from T0. End-of-
    mechanical-substep geometry defines volume for radiogenic production.
    Positive flux is upward (depth z increases downward).
    """
    n=model['n']; area,h=geometry(s,n)
    k,H,coeff,cap=(model[x] for x in ('k','H','coeff','capacity'))
    dx=h/n
    faces=np.linspace(0.,1.,n+1)
    qref=k[:,:,None]/h[:,:,None]*np.einsum('plk,jk->plj',
              coeff[:,:,1:]*np.arange(1,4),faces[:,None]**np.arange(3))
    # The accepted G4 deformation scales both layers equally per parcel;
    # verify reference interface continuity instead of imposing it silently.
    gap=rel(qref[:,0,-1],qref[:,1,0])
    a.need(gap<=TOL['interface_flux_relative'],'PRE_MOHO_FLUX_DISCONTINUITY')
    moho=.5*(qref[:,0,-1]+qref[:,1,0])
    qref[:,0,-1]=moho; qref[:,1,0]=moho
    # FV correction only on the perturbation. Exact initial polynomial
    # derivatives avoid coarse-grid boundary/interface truncation at T0.
    dT=delta/cap
    q=qref.copy()
    q[:,:,1:-1]+=k[:,:,None]/dx[:,:,None]*np.diff(dT,axis=-1)
    q[:,0,0]+=2*k[:,0]/dx[:,0]*dT[:,0,0]
    q[:,1,-1]-=2*k[:,1]/dx[:,1]*dT[:,1,-1]
    cross=1/(dx[:,0]/(2*k[:,0])+dx[:,1]/(2*k[:,1]))
    dq=cross*(dT[:,1,0]-dT[:,0,-1])
    q[:,0,-1]+=dq; q[:,1,0]+=dq
    # All conductances are positive; verify sufficient explicit stability.
    cond=np.broadcast_to((2*k/dx)[:,:,None],cap.shape).copy()
    cond[:,0,0]+=k[:,0]/dx[:,0]
    cond[:,1,-1]+=k[:,1]/dx[:,1]
    cond[:,0,-1]=k[:,0]/dx[:,0]+cross
    cond[:,1,0]=k[:,1]/dx[:,1]+cross
    dt=years*YEAR
    cfl=float(np.max(dt*area[:,None,None]*cond/cap))
    a.need(cfl<=TOL['explicit_cfl'],'EXPLICIT_STABILITY')
    production=np.broadcast_to((area[:,None]*H*dx)[:,:,None],cap.shape)
    flux=area[:,None,None]*q
    inc=dt*(np.diff(flux,axis=-1)+production)
    end=delta+inc
    actual=end-delta
    a.need(np.isfinite(end).all() and np.all(model['temp0']+end/cap>0),'THERMAL_FINITE')
    # Independent per-parcel budget from boundary powers and source.
    top=dt*flux[:,0,0]; bottom=dt*flux[:,1,-1]
    source=dt*production.sum(axis=(1,2))
    expected=bottom-top+source
    obtained=actual.sum(axis=(1,2))
    scale=abs(top)+abs(bottom)+abs(source)+np.sum(abs(actual),axis=(1,2))
    err=float(np.max(abs(obtained-expected)/np.maximum(scale,1.)))
    # Check crust/mantle separately (same Moho face, opposite signs).
    layer_expected=dt*(flux[:,:,-1]-flux[:,:,0]+production.sum(axis=-1))
    layer_actual=actual.sum(axis=-1)
    layer_scale=dt*(abs(flux[:,:,-1])+abs(flux[:,:,0])+production.sum(axis=-1))+np.sum(abs(actual),axis=-1)
    layer_err=float(np.max(abs(layer_actual-layer_expected)/np.maximum(layer_scale,1.)))
    full=model['heat']+end
    absolute_error=rel((full-model['heat']).sum(axis=(1,2)),end.sum(axis=(1,2)))
    # The absolute-state cancellation above is reported relative to the
    # small increment, not used as an acceptance test; compare total energy.
    total_error=rel(full.sum(axis=(1,2)),model['heat'].sum(axis=(1,2))+end.sum(axis=(1,2)))
    a.need(np.array_equal(q[:,0,-1],q[:,1,0]),'MOHO_SHARED_FACE')
    report={'years':years,'max_explicit_cfl':cfl,
        'max_reference_moho_flux_relative_gap':gap,
        'shared_moho_flux_exact':True,'max_column_transfer_relative_error':err,
        'max_layer_transfer_relative_error':layer_err,
        'max_absolute_state_energy_relative_error':total_error,
        'absolute_subtraction_relative_to_increment_diagnostic':absolute_error,
        'radiogenic_energy_J':float(source.sum()),
        'surface_outward_energy_J':float(top.sum()),
        'LAB_inward_energy_J':float(bottom.sum()),
        'moho_upward_energy_J':float((dt*flux[:,0,-1]).sum()),
        'internal_energy_increment_J':float(actual.sum()),
        'max_temperature_increment_K':float(np.max(abs(actual/cap))),
        'max_cumulative_temperature_increment_K':float(np.max(abs(end/cap))),
        'minimum_temperature_K':float((model['temp0']+end/cap).min()),
        'maximum_temperature_K':float((model['temp0']+end/cap).max())}
    report['screen_pass']=bool(max(err,layer_err)<=TOL['energy_transfer_relative'] and
                         total_error<=TOL['absolute_energy_relative'])
    return end,report

def difference(coarse_model,coarse,fine_model,fine):
    """Compare thermal changes at equal material-depth support via energy sums."""
    n=coarse_model['n']; f=fine_model['n']
    a.need(f%n==0,'REFINEMENT_RATIO')
    ref=fine.reshape(384,2,n,f//n).sum(axis=-1)/fine_model['capacity'].reshape(384,2,n,f//n).sum(axis=-1)
    obs=coarse/coarse_model['capacity']
    error=float(np.max(abs(obs-ref)))
    scale=max(float(np.max(abs(obs))),float(np.max(abs(ref))))
    limit=min(TOL['temperature_absolute_K'],max(TOL['temperature_signal_floor_K'],
              TOL['temperature_signal_relative']*scale))
    return {'max_temperature_difference_K':error,'max_signal_K':scale,
            'relative_to_max_signal':error/max(scale,1e-300),'limit_K':limit,'screen_pass':error<=limit}

def selftest():
    # Constant T, equal materials, insulated by matching Dirichlet boundaries:
    # uniform production gives the analytic first Euler increment H/(rho*cp).
    n=8; shape=(384,2,n)
    h=np.full((128,3,2),1000.); area=np.full(128,3e6)
    coeff=np.zeros((384,2,4)); coeff[:,:,0]=300.
    cap=np.full(shape,1e6*(1000/n)*2800*1000)
    m={'n':n,'coeff':coeff,'k':np.full((384,2),2.5),'H':np.full((384,2),8e-7),
        'capacity':cap,'heat':cap*300.,'temp0':np.full(shape,300.)}
    s={'area_m2':area.tolist(),'thickness_m':h.tolist()}
    inc,r=step(m,np.zeros(shape),s,1.)
    a.need(r['screen_pass'] and np.allclose(inc/cap,8e-7*YEAR/(2800*1000),rtol=1e-14,atol=0),'UNIFORM_SOURCE_SELFTEST')
    m['H'][:]=0.
    inc,r=step(m,np.zeros(shape),s,1.)
    a.need(r['screen_pass'] and np.all(inc==0),'CONSTANT_T_SELFTEST')
    # Linear continuous steady conduction across equal layers.
    coeff[:,:,1]=100.; coeff[:,1,0]=400.
    inc,r=step(m,np.zeros(shape),s,1.)
    a.need(r['screen_pass'] and np.all(inc==0),'STEADY_FLUX_SELFTEST')
    print('G5_THERMAL_SELFTEST_PASS',flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorize-controlled-thermal',choices=[a.SCENARIO],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    selftest()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    here=Path(__file__).resolve().parent
    a.need(blob(here/'arcana_g4_controlled_transport.py')==G4_BLOB,'G4_RUNNER_PIN')
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
           not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    parent=c10.OUT.with_name('R6_THERMO_G4_CONTROLLED_TRANSPORT_NEW01')
    manifest=c.verified(parent,G4_PIN,G4_STATUS)
    a.need(manifest['source_sha']==a.SHA and manifest['C11D_manifest_sha256']==g4.D_PIN and
           manifest['additional_native_solves']==0 and all(manifest[k]==v for k,v in c.SCOPE.items()),'G4_LINEAGE')
    prior=a.read(parent/'G4_TRANSPORT_REPORT.json')
    a.need(prior['screen_pass'] and prior['separate_process_restart_exact'] and
           prior['parent_and_material_identity_preserved'],'G4_SCREEN')
    s,one,half,two=[g4.unseal(parent/p) for p in ('INITIAL_CHECKPOINT.json','ONE_YEAR_CHECKPOINT.json',
                              'HALF_YEAR_CHECKPOINT.json','TWO_HALF_STEPS_CHECKPOINT.json')]
    a.need([x['elapsed_years'] for x in (s,one,half,two)]==[0.,1.,.5,1.] and
           all(s[k]==z[k] for z in (one,half,two) for k in ('node_parent_ids','element_parent_ids',
               'original_PRE_rows_tokens','layer_mass_kg','normalized_depth_temperature_coefficients_K',
               'rho_reference_kg_m3','alpha_K_inverse','cp_J_kg_K','passive_sensible_heat_tracer_J')),
           'G4_THERMAL_SOURCE_BINDING')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in (root,parent,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G4_manifest':G4_PIN,'runner_sha256':a.sha(Path(__file__)),
        'levels_per_layer':LEVELS,'tolerances':TOL,'scope':'One-way split thermal experiment on G4 geometry. No thermomechanical feedback.',
        'boundary':'Fixed initial surface and LAB temperature; perturbation flux with exact initial PRE polynomial.',
        'heat_capacity':'G4 effective-density parcel mass times PRE cp. Distinct from reference-density PRE initialization rate.',
        'radiogenic':'PRE volumetric production on end-of-substep geometry; no decay over one year.',**c.SCOPE})
    reports={}; results={}
    for n in LEVELS:
        m=setup(s,n)
        zero=np.zeros_like(m['capacity'])
        full,rfull=step(m,zero,one,1.)
        h1,rh1=step(m,zero,half,.5)
        h2,rh2=step(m,h1,two,.5)
        temporal=difference(m,full,m,h2)
        reports[str(n)]={'one_year':rfull,'first_half':rh1,'second_half':rh2,'time_refinement':temporal}
        results[n]=(m,full,h2)
        np.savez(out/f'columns_{n}.npz',mass_kg=m['mass'],initial_energy_J=m['heat'],
            heat_capacity_J_K=m['capacity'],initial_temperature_K=m['temp0'],
            one_step_energy_increment_J=full,two_half_energy_increment_J=h2,
            two_half_temperature_K=m['temp0']+h2/m['capacity'],
            element_parent_ids=np.asarray(s['element_parent_ids']),parcel_node_local_ids=np.asarray(s['transport_triangles_zero_based'])+1)
        print('G5_LEVEL',n,'TEMPORAL',json.dumps(temporal),flush=True)
    spatial={}
    for low,high in zip(LEVELS[:-1],LEVELS[1:]):
        ml,_,dl=results[low]; mh,_,dh=results[high]
        spatial[f'{low}_to_{high}']=difference(ml,dl,mh,dh)
    success=all(v['screen_pass'] for v in spatial.values()) and all(
        all(x['screen_pass'] for x in r.values()) for r in reports.values())
    m,_,d=results[LEVELS[-1]]
    density_proxy_change=-m['alpha'][:,:,None]*(d/m['capacity'])/(1-m['alpha'][:,:,None]*m['temp0'])
    status='G5_CONTROLLED_COLUMN_HEAT_UPDATE_PASS__THERMOMECHANICAL_FEEDBACK_PENDING' if success else 'G5_CONTROLLED_COLUMN_HEAT_UPDATE_BLOCKED'
    report={'status':status,'screen_pass':success,'levels':reports,'space_refinement':spatial,
        'max_unapplied_relative_thermal_density_change_proxy':float(np.max(abs(density_proxy_change))),
        'physical_acceptance':False,'additional_native_solves':0,'thermal_feedback_applied':False,
        'limitations':['Perturbation FV around exact PRE profile, not general thermal solver qualification.',
            'No pressure work, lateral conduction, latent heat, mechanical dissipation heating, erosion or basal material exchange.',
            'Fixed layer mass, geometry and thermal inertia over each thermal substep; expansion proxy not applied.',
            'No native PRE polynomial projection, T1 solve, or natural exterior closure. No new HistoryStore state.'],**c.SCOPE}
    a.need(c.inventory(parent)==manifest['files'] and a.sha(parent/'MANIFEST.json')==G4_PIN,'G4_MUTATION')
    a.write(out/'G5_THERMAL_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G4_manifest_sha256':G4_PIN,
         'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G5_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if success else 2

if __name__=='__main__':
    raise SystemExit(main())
