#!/usr/bin/env python3
"""G20 excluded-ocean reference columns and conservative fixed-column heat test.
Existing PRE authority only; no material admission or topology changes.
Physical age remains unchanged, including at ridge cells.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c

G19_PIN='79f2ea1a004cbb65a9b6a1967e833eba8e3c171bfc07fe9bd65f9eec641e91ca'
G19_STATUS='G19_GLOBAL_SUPPORT_ATLAS_PASS__MATERIAL_AND_BOUNDARY_CLOSURE_REQUIRED'
R3_PIN='f294108dc146f3507cd23a919ce28fd303e97b523ccafa0c7ab5e4a9f4e213f9'
YEAR=365.25*86400
HORIZON=1000.
ENERGY_TOL=1e-11
TIME_REL=1e-3
TIME_ABS=1e-7

def norm(x): return float(np.max(np.abs(x)))

def setup(polys,properties,n):
    # Polynomial coefficients in SI local depth; exact cell averages and
    # exact reference flux on every face, constant reference rho*Cp.
    p=np.asarray(polys); h=p[:,:,1]-p[:,:,0]; dx=h/n
    k,rho,cp,H=(properties[:,i][None,:] for i in range(4))
    f=np.arange(n+1)[None,None,:]*dx[:,:,None]
    aa,bb,cc,dd=(p[:,:,i,None] for i in range(2,6))
    q=k[:,:,None]*(3*aa*f*f+2*bb*f+cc)
    a.need(norm(q[:,0,-1]-q[:,1,0])<=2e-12,'MOHO_FLUX')
    q[:,1,0]=q[:,0,-1]
    l=f[:,:,:-1]; u=f[:,:,1:]
    # Polynomial integral divided by dx using stable power differences.
    T=dd+cc*(u+l)/2+bb*(u*u+u*l+l*l)/3+aa*(u**3+u*u*l+u*l*l+l**3)/4
    C=np.broadcast_to((rho*cp*dx)[:,:,None],T.shape).copy().reshape(len(p),-1)
    rad=np.broadcast_to((H*dx)[:,:,None],T.shape).copy().reshape(len(p),-1)
    g=np.empty((len(p),2*n+1))
    g[:,0]=2*k[:,0]/dx[:,0]; g[:,1:n]=k[:,0,None]/dx[:,0,None]
    g[:,n]=1/(dx[:,0]/(2*k[:,0])+dx[:,1]/(2*k[:,1]))
    g[:,n+1:-1]=k[:,1,None]/dx[:,1,None]; g[:,-1]=2*k[:,1]/dx[:,1]
    Q=np.concatenate((q[:,0],q[:,1,1:]),axis=1)
    a.need(np.all(C>0) and np.all(g>0) and np.isfinite(T).all(),'COLUMN_OPERATOR')
    return T.reshape(len(p),-1),C,rad,g,Q

def cn(op,years,steps):
    T0,C,H,g,Q=op; dt=years*YEAR/steps
    gamma=dt*(g[:,:-1]+g[:,1:])/C
    a.need(norm(gamma)<=2.,'CN_MONOTONICITY')
    lo=-.5*dt*g[:,1:-1]/C[:,1:]; hi=-.5*dt*g[:,1:-1]/C[:,:-1]
    diag=1+.5*gamma
    d=diag.copy(); factor=np.empty_like(lo)
    for j in range(1,d.shape[1]):
        factor[:,j-1]=lo[:,j-1]/d[:,j-1]
        d[:,j]-=factor[:,j-1]*hi[:,j-1]
    a.need(np.all(d>0),'THOMAS_PIVOT')
    E=np.zeros_like(C); total=np.zeros((len(C),4)); max_local=0.; max_linear=0.
    def flux(T): return Q+g*np.diff(np.pad(T,((0,0),(1,1))),axis=1)
    for _ in range(steps):
        old=E/C; q=flux(old); rhs=dt*(np.diff(q,axis=1)+H)/C
        y=rhs.copy()
        for j in range(1,d.shape[1]): y[:,j]-=factor[:,j-1]*y[:,j-1]
        x=np.empty_like(y); x[:,-1]=y[:,-1]/d[:,-1]
        for j in range(d.shape[1]-2,-1,-1): x[:,j]=(y[:,j]-hi[:,j]*x[:,j+1])/d[:,j]
        ax=diag*x; ax[:,1:]+=lo*x[:,:-1]; ax[:,:-1]+=hi*x[:,1:]
        max_linear=max(max_linear,norm(ax-rhs)/max(norm(rhs),1e-30))
        nxt=E+C*x; actual=nxt-E; mid=flux(old+.5*actual/C)
        expected=dt*(np.diff(mid,axis=1)+H)
        scale=dt*(abs(mid[:,:-1])+abs(mid[:,1:])+H)+abs(actual)
        max_local=max(max_local,norm((actual-expected)/np.maximum(scale,1.)))
        n=C.shape[1]//2
        total+=dt*np.column_stack((H.sum(axis=1),mid[:,0],mid[:,-1],mid[:,n]))
        E=nxt
    # Units J/m2, upward flux at surface and LAB. Moho cancels internally.
    expected=total[:,0]-total[:,1]+total[:,2]
    closure=norm((E.sum(axis=1)-expected)/np.maximum(abs(total[:,:3]).sum(axis=1)+abs(E).sum(axis=1),1.))
    a.need(max(max_local,closure)<=ENERGY_TOL and max_linear<=1e-12 and
        np.isfinite(E).all() and np.all(T0+E/C>0),'CN_ENERGY_OR_LINEAR')
    return E/C,E,total,{'steps':steps,'dt_years':years/steps,'max_gamma':norm(gamma),
        'max_cell_energy_defect':max_local,'max_column_energy_defect':closure,'max_linear_residual':max_linear}

def refine(op):
    T,C,H,g,Q=op
    gamma=HORIZON*YEAR*norm((g[:,:-1]+g[:,1:])/C)
    steps=max(1,int(np.ceil(gamma/1.5)))
    old=cn(op,HORIZON,steps)
    for _ in range(7):
        steps*=2
        a.need(steps<=2048,'TEMPORAL_REFINEMENT_BUDGET')
        new=cn(op,HORIZON,steps)
        err=np.max(abs(new[0]-old[0]),axis=1)
        signal=np.max(abs(new[0]),axis=1)
        ratio=norm(err/(TIME_ABS+TIME_REL*signal))
        if ratio<=1.:
            return new,{'coarse_steps':steps//2,'fine_steps':steps,'max_error_K':norm(err),
                'max_error_over_budget':ratio,'screen_pass':True}
        old=new
    raise RuntimeError('TEMPORAL_REFINEMENT_UNRESOLVED')

def selftest():
    # Constant profile, zero internal production, zero perturbation.
    p=np.array([[[0,1000,0,0,0,300],[1000,2000,0,0,0,300]]],float)
    prop=np.array([[2.2,2890,1000,0],[3.3,3300,1200,0]])
    op=setup(p,prop,16)
    d,E,b,r=cn(op,1.,1)
    a.need(np.all(d==0) and np.all(E==0) and np.all(b==0),'CONSTANT_FIXTURE')
    prop[:,3]=1e-7; op=setup(p,prop,16)
    d,E,b,r=cn(op,1.,1)
    a.need(np.all(d>0) and E.sum()>0,'HEATING_FIXTURE')
    print('G20_FIXED_COLUMN_SELFTEST_PASS',flush=True)

def columns(root,parent,c06):
    from arcana_worldsim.r6 import pre_orbdata_runtime_package as runtime
    from experiments.shellset_regional_explore_v1 import build_case
    f,_,_,membership=c06.load_native(root)
    excl=a.read(parent/'EXCLUDED_CELL_ATLAS.json')
    a.need(len(excl)==1180 and len({x['cell_id'] for x in excl})==1180,'EXCLUDED_ATLAS')
    material,refs=runtime._material_config(root)
    cm=material['crusts']['OCEANIC_CRUST_REFERENCE']; mm=material['mantle']; model=refs['hwr_model']
    props=np.array([[m.k,m.rho,m.cp,m.radiogenic_w_m3] for m in (cm,mm)])
    source=root/(build_case.PRE+'.dat')
    meta=a.read(root/(build_case.PRE+'.json'))
    a.need(a.sha(source)==meta['runtime_data_sha256'],'PRE_PIN')
    with source.open() as h:
        a.need(int(h.readline().split()[-1])==64442,'PRE_HEADER')
        pre=np.loadtxt(h)
    a.need(pre.shape==(64442,51) and np.isfinite(pre).all(),'PRE_SHAPE')
    owner={(int(r[1]),int(r[2])):r for r in pre}
    cache={}; polys=[]; records=[]; owner_hits=0; max_replay=0.
    for x in excl:
        r,col=x['row'],x['column']; key=x['cell_id']
        a.need(key==f'R6G1D-R{r:03d}-C{col:03d}' and 'ADMITTED_INITIALIZER_SUPPORT' not in membership[key]
            and int(f['physical_crust_domain_id'][r,col])==1,'EXCLUDED_SOURCE')
        age=float(f['oceanic_lithosphere_age_ma'][r,col]); hc=float(f['crustal_thickness_m'][r,col])
        ridge=x['D12_class']=='ZERO_AGE_RIDGE'
        a.need(age==x['physical_ocean_age_Ma'] and ridge==(age==0),'AGE_SOURCE')
        q=.3 if ridge else model.flux(age)
        k=(ridge,age,hc,q)
        if k not in cache:
            column=runtime.ocean_column(age_ma=age,crust_m=hc,q_surface=q,ridge=ridge,crust=cm,model=model)
            pp=runtime.validate_column(column,q,refs['surface_temperature_k'],cm.k,mm.k)
            cache[k]=(column,pp)
        column,pp=cache[k]; polys.append(pp)
        # Compare source owner node when present; polar cells without a
        # numerical owner still receive an independently derived cell column.
        own=owner.get((r,col))
        if own is not None:
            expected=np.array([q,column.crust_m,column.mantle_m,column.lab_m,column.moho_temperature_k,
                column.moho_flux_w_m2,column.lab_temperature_k,column.lab_flux_w_m2])
            a.need(int(own[8])==(2 if ridge else 3) and own[10]==age and bool(own[11])==ridge
                and np.allclose(own[14:22],expected,rtol=1e-12,atol=1e-12)
                and np.allclose(own[39:],np.ravel(pp),rtol=1e-12,atol=1e-15)
                and (not ridge or abs(own[12]-column.effective_age_ma)<=1e-12),'OWNER_PRE_REPLAY')
            owner_hits+=1
            max_replay=max(max_replay,norm(own[14:22]-expected))
        records.append({'cell_id':key,'D12_class':x['D12_class'],'physical_age_Ma':age,
            'effective_thermal_age_Ma':column.effective_age_ma,'crust_m':hc,'LAB_m':column.lab_m,
            'surface_flux_W_m2':q,'Moho_T_K':column.moho_temperature_k,'Moho_flux_W_m2':column.moho_flux_w_m2,
            'LAB_T_K':column.lab_temperature_k,'LAB_flux_W_m2':column.lab_flux_w_m2,
            'PRE_owner_replay':own is not None,'material_admitted':False,'boundary_ids':x['boundary_ids']})
    a.need(Counter(x['D12_class'] for x in records)=={'ZERO_AGE_RIDGE':108,
        'UNRESOLVED_POSITIVE_AGE_OCEAN':1072},'CLASS_COUNTS')
    return np.array(polys),props,records,{'unique_columns':len(cache),'owner_nodes_replayed':owner_hits,
        'owner_max_boundary_absolute_difference':max_replay,'ridge_effective_age_Ma':model.positive_equivalent_age(.3),
        'all_1180_existing_reference_columns_valid':True}

def run_heat(polys,props,records,out):
    previous=None; results={}
    for n in (16,32,64):
        print('G20_FIXED_COLUMN_REFINEMENT',n,flush=True)
        op=setup(polys,props,n)
        result,temporal=refine(op); delta,E,b,report=result
        np.savez_compressed(out/f'FIXED_COLUMN_{n}.npz',temperature0_K=op[0],temperature_increment_K=delta,
            capacity_J_m2_K=op[1],increment_J_m2=E,integrated_flux_and_radiogenic_J_m2=b)
        r={'temporal':temporal,'conservation':report,'max_temperature_increment_K':norm(delta)}
        if previous is not None:
            coarse=delta.reshape(len(polys),-1,2).mean(axis=-1)
            r['spatial_difference_to_previous_K']=norm(coarse-previous)
            r['spatial_difference_over_signal']=norm(coarse-previous)/max(norm(delta),1e-30)
        results[str(n)]=r; previous=delta
    for j,x in enumerate(records):
        x['diagnostic_1000yr']={'net_sensible_heat_increment_J_m2':float(E[j].sum()),
            'max_abs_temperature_increment_K':norm(delta[j]),'radiogenic_J_m2':float(b[j,0]),
            'surface_outward_J_m2':float(b[j,1]),'LAB_inward_J_m2':float(b[j,2])}
    summary={}
    for cls in ('ZERO_AGE_RIDGE','UNRESOLVED_POSITIVE_AGE_OCEAN'):
        inds=[j for j,x in enumerate(records) if x['D12_class']==cls]
        def span(v): return [float(np.min(v)),float(np.max(v))]
        summary[cls]={'count':len(inds),'LAB_range_m':span([records[j]['LAB_m'] for j in inds]),
            'surface_flux_range_W_m2':span([records[j]['surface_flux_W_m2'] for j in inds]),
            'net_energy_increment_range_J_m2':span(E[inds].sum(axis=1)),
            'max_abs_delta_T_K':norm(delta[inds])}
    a.write(out/'EXCLUDED_COLUMN_DIAGNOSTICS.json',records)
    np.savez_compressed(out/'SOURCE_COLUMN_COEFFICIENTS.npz',cell_ids=np.array([x['cell_id'] for x in records]),
        coefficients=polys,reference_material_properties=props)
    return {'resolutions':results,'classes':summary,'spatial_accuracy_qualified':False,
        'fixed_geometry_only':True,'screen_pass':True}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-ocean-column-diagnostic',choices=[a.SCENARIO],required=True)
    args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    c06=c10.c09.c08.c07.c06
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    p=c10.OUT.with_name('R6_THERMO_G19_GLOBAL_SUPPORT_ATLAS_NEW01')
    pm=c.verified(p,G19_PIN,G19_STATUS); old=a.read(p/'G19_REPORT.json')
    a.need(pm['source_sha']==a.SHA and pm['G18R3_manifest_sha256']==R3_PIN and
        all(pm[k]==v for k,v in c.SCOPE.items()) and old['screen_pass'] and old['atlas']['excluded_cells']==1180,'PARENT_SCOPE')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,c10.OUT,c06.d12.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G19_manifest':G19_PIN,'runner_sha256':a.sha(Path(__file__)),
        'diagnostic_horizon_years':HORIZON,'reference_capacity':'constant rho_ref*Cp; per unit horizontal area',
        'boundary':'fixed surface and LAB temperature; source flux at t0, subsequently evolves',
        'time_error_budget_relative':TIME_REL,'time_error_budget_absolute_K':TIME_ABS,
        'energy_tolerance':ENERGY_TOL,'spatial_refinement':'16/32/64 cells per layer; diagnostic only',
        'physical_admissions_authorized':0,**c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,'additional_builds':0,
        'additional_time_advance_years':0,'physical_acceptance':False,'material_assignments':0,**c.SCOPE}
    try:
        selftest()
        print('G20_RECONSTRUCT_EXCLUDED_COLUMNS',flush=True)
        polys,props,records,r=columns(root,p,c06); report['reference_columns']=r
        report['fixed_column_heat']=run_heat(polys,props,records,out)
        report['screen_pass']=True
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    a.need(c.inventory(p)==pm['files'] and a.sha(p/'MANIFEST.json')==G19_PIN,'PARENT_MUTATION')
    status='G20_EXCLUDED_OCEAN_REFERENCE_AND_HEAT_SCREEN_PASS__CONTACT_AND_MATERIAL_AUTHORITY_REQUIRED' if report['screen_pass'] else 'G20_EXCLUDED_OCEAN_DIAGNOSTIC_BLOCKED'
    report.update(status=status,limitations=[
        'Existing HWR/PRE numerical reference is not D12 admission or a material phase assignment.',
        '1000-year fixed-column diagnostic is not historical evolution; no age, mass, geometry or contact update.',
        'Constant reference density heat capacity, no latent heat, pressure work, advection, magmatism or hydrothermal transport.',
        'Temporal budget is provisional diagnostic; spatial accuracy and physical closure remain unqualified.',
        'G18 adjudication remains open; no global mechanical assembly, solve or physical T1.'])
    a.write(out/'G20_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G19_manifest_sha256':G19_PIN,
        'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G20_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True);print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
