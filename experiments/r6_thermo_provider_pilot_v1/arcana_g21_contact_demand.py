#!/usr/bin/env python3
"""G21: source-bound contact demand and local conservative counterfactuals.
Also isolate vertical spatial error using exact frozen semidiscrete solutions.
No physical contact typing, event application, admission or time advancement.
"""
import argparse
from collections import defaultdict,Counter
import csv
import json
import math
from pathlib import Path
import subprocess
import traceback
import numpy as np
from scipy.linalg import eigh_tridiagonal
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g20_excluded_ocean_heat as g20

G20_PIN='abb7cfad2ee7439dd3f0c1b9a6863b27a922f5b3c38858b93234bdd7effe7f47'
G20_STATUS='G20_EXCLUDED_OCEAN_REFERENCE_AND_HEAT_SCREEN_PASS__CONTACT_AND_MATERIAL_AUTHORITY_REQUIRED'
HORIZON=1000.
TOL=1e-11

def exact(op,years):
    """Exact frozen semidiscrete heat increment and integrated flux ledger.
    Symmetric similarity transform with positive cell capacities.
    """
    T,C,H,g,Q=op; sec=years*g20.YEAR
    result=[]; budgets=[]; worst=0.; eigenerr=0.
    for cap,h,gg,q in zip(C,H,g,Q,strict=True):
        s=np.sqrt(cap)
        diag=-(gg[:-1]+gg[1:])/cap
        off=gg[1:-1]/(s[:-1]*s[1:])
        lam,V=eigh_tridiagonal(diag,off)
        a.need(np.all(lam<0),'SPECTRAL_NEGATIVE_OPERATOR')
        av=diag[:,None]*V
        av[1:]+=off[:,None]*V[:-1]; av[:-1]+=off[:,None]*V[1:]
        eigenerr=max(eigenerr,g20.norm(av-V*lam)/max(g20.norm(diag),1e-300))
        f=V.T@((np.diff(q)+h)/s)
        x=lam*sec
        phi=np.expm1(x)/lam
        # Integral of expm1(lambda*t)/lambda, using series near zero.
        small=abs(x)<1e-3
        psi=np.empty_like(x)
        psi[small]=sec**2*(.5+x[small]/6+x[small]**2/24+x[small]**3/120+x[small]**4/720)
        psi[~small]=(np.expm1(x[~small])-x[~small])/lam[~small]**2
        d=(V@(phi*f))/s
        integral=(V@(psi*f))/s
        iq=sec*q+gg*np.diff(np.r_[0.,integral,0.])
        E=cap*d
        expect=np.diff(iq)+sec*h
        scale=abs(iq[:-1])+abs(iq[1:])+sec*h+abs(E)
        worst=max(worst,g20.norm((E-expect)/np.maximum(scale,1.)))
        a.need(np.isfinite(d).all(),'SPECTRAL_FINITE')
        result.append(d)
        budgets.append([float(E.sum()),float(sec*h.sum()),float(iq[0]),float(iq[-1])])
    a.need(worst<=TOL and eigenerr<=1e-12,'SPECTRAL_CONSERVATION')
    return np.array(result),np.array(budgets),{'max_cell_energy_defect':worst,'max_eigen_residual':eigenerr}

def spatial(p,out):
    with np.load(p/'SOURCE_COLUMN_COEFFICIENTS.npz') as z:
        ids=z['cell_ids']; polys=z['coefficients']; props=z['reference_material_properties']
    with np.load(p/'FIXED_COLUMN_32.npz') as z: d32=z['temperature_increment_K']
    with np.load(p/'FIXED_COLUMN_64.npz') as z: d64=z['temperature_increment_K']
    rec=a.read(p/'EXCLUDED_COLUMN_DIAGNOSTICS.json')
    a.need(len(rec)==len(ids)==1180 and np.array_equal(ids,[r['cell_id'] for r in rec]),'SOURCE_COLUMN_ID')
    mismatch=np.max(abs(d64.reshape(len(ids),64,2).mean(axis=2)-d32),axis=1)
    chosen=set()
    for cls in ('ZERO_AGE_RIDGE','UNRESOLVED_POSITIVE_AGE_OCEAN'):
        ii=np.array([i for i,r in enumerate(rec) if r['D12_class']==cls])
        for metric in (mismatch,np.max(abs(d64),axis=1),np.array([r['LAB_m'] for r in rec])):
            chosen.add(int(ii[np.argmax(metric[ii])]))
            chosen.add(int(ii[np.argmin(metric[ii])]))
    # Deduplicate identical coefficients; retain original chosen IDs as well.
    ind=sorted(chosen); unique={}
    for i in ind: unique.setdefault(polys[i].tobytes(),i)
    test=list(unique.values())
    previous=None; results={}; differences=[]
    for n in (16,32,64,128,256,512):
        print('G21_SPECTRAL_SPATIAL',n,len(test),flush=True)
        op=g20.setup(polys[test],props,n)
        d,b,rr=exact(op,HORIZON)
        np.savez_compressed(out/f'SPECTRAL_{n}.npz',cell_ids=ids[test],delta_T_K=d,energy_budget_J_m2=b)
        rr.update(max_abs_delta_T_K=g20.norm(d))
        if n==64: rr['G20_CN_difference_K']=g20.norm(d-d64[test])
        if previous is not None:
            diff=d.reshape(len(test),2*(n//2),2).mean(axis=2)-previous
            h=polys[test,:,1]-polys[test,:,0]
            weights=np.repeat(h/(n//2),n//2,axis=1)
            l2=np.sqrt(np.sum(diff**2*weights,axis=1)/weights.sum(axis=1))
            rr.update(max_restricted_difference_K=g20.norm(diff),max_depth_RMS_difference_K=g20.norm(l2))
            differences.append([n,g20.norm(diff),g20.norm(l2)])
        results[str(n)]=rr; previous=d
    return {'screen_pass':True,'selected_source_cells':[str(ids[i]) for i in ind],
        'unique_test_columns':[str(ids[i]) for i in test],'resolutions':results,
        'last_two_max_difference_decreasing':differences[-1][1]<differences[-2][1],
        'last_two_RMS_difference_decreasing':differences[-1][2]<differences[-2][2],
        'all_1180_spatial_accuracy_qualified':False,'time_discretization_removed':True}

def aggregate(rows):
    return {'segments':len(rows),'length_m':math.fsum(r['length_m'] for r in rows),
        'opening_area_rate_m2_per_year':math.fsum(r['opening_area_rate_m2_per_year'] for r in rows),
        'max_opening_m_per_year':max((r['normal_m_per_year'] for r in rows),default=0.),
        'plate_pairs':sorted(set(r['plate_pair'] for r in rows)),
        'min_guard_year':min((r['lower_guard_year'] for r in rows),default=None)}

def components(rows):
    # Graph components by same pair and shared source endpoint, not a new
    # geological branch classification.
    incident=defaultdict(list); by_id={r['id']:r for r in rows}
    for r in rows:
        for v in r['vertices']: incident[(r['plate_pair'],v)].append(r['id'])
    unused=set(by_id); groups=[]
    while unused:
        seed=min(unused); todo=[seed]; unused.remove(seed); ids=[]
        while todo:
            j=todo.pop(); ids.append(j); r=by_id[j]
            for v in r['vertices']:
                for k in incident[(r['plate_pair'],v)]:
                    if k in unused: unused.remove(k); todo.append(k)
        group=[by_id[i] for i in sorted(ids)]
        groups.append({'segment_ids':sorted(ids),**aggregate(group)})
    return sorted(groups,key=lambda r:(-r['length_m'],r['segment_ids'][0]))

def contact(root,p,q,out,c06):
    from arcana_worldsim.r6 import geological_source_t0_adapter as geo
    d12=c06.d12; pins=geo.verify_manifests(root)
    boundary=root/d12.BOUNDARY_FILE
    a.need(geo.gitblob(boundary.read_bytes())==d12.BOUNDARY_BLOB,'BOUNDARY_PIN')
    source=a.read(boundary); segments=source['segments']; by_id={r['boundary_id']:r for r in segments}
    age_source=pins['field']['derived_fields']['oceanic_age']
    selected=set(age_source['selected_source_boundary_ids'])
    a.need(len(by_id)==1983 and len(selected)==79 and selected<=set(by_id),'CONTACT_INVENTORY')
    law=root/'R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json'
    width=root/'R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.json'
    event=root/'contracts/R6_RIFT_PROCESS_ACTIVATION_MODEL_V1.json'
    guard=a.read(law); w=a.read(width); activation=a.read(event)
    theta=float(guard['threshold_authority']['lower_guard_bound_m'])
    upper=float(guard['threshold_authority']['upper_bound_m'])
    widths=w['candidate_prior']['full_width_range_m']
    a.need(theta==5000 and upper==30000 and widths==[100000.,1000000.]
        and w['candidate_prior']['canonical_realization'] is None,'AUTHORITY_SCOPE')
    fastest=max(segments,key=lambda s:s['relative_normal_velocity_m_per_year'])
    first=theta/fastest['relative_normal_velocity_m_per_year']
    a.need(fastest['ordered_plate_pair']==activation['scope']['plate_pair']==[1,3]
        and abs(first-27123.405156307464)<1e-7 and HORIZON<first,'EVENT_GUARD')
    with (p/'BOUNDARY_CLASSIFICATION.csv').open() as f: atlas=list(csv.DictReader(f))
    a.need(len(atlas)==1983 and len({r['boundary_id'] for r in atlas})==1983,'ATLAS_CONTACTS')
    excluded=a.read(p/'EXCLUDED_CELL_ATLAS.json'); ex={r['cell_id']:r for r in excluded}
    col=a.read(q/'EXCLUDED_COLUMN_DIAGNOSTICS.json'); cd={r['cell_id']:r for r in col}
    a.need(set(ex)==set(cd) and len(ex)==1180,'COLUMN_ATLAS_LINK')
    with np.load(q/'SOURCE_COLUMN_COEFFICIENTS.npz') as z:
        prop=z['reference_material_properties']; poly=z['coefficients']; ids=z['cell_ids']
    a.need(np.array_equal(ids,[r['cell_id'] for r in col]),'COLUMN_ORDER')
    # Reference areal inventories (constant rho_ref and fixed zero of sensible
    # heat at T=0 K, not a phase enthalpy model).
    t,C,_,_,_=g20.setup(poly,prop,16)
    h=poly[:,:,1]-poly[:,:,0]
    mass=h*prop[:,1]; heat=(t*C).reshape(len(col),2,16).sum(axis=2)
    inv={str(i):(mass[j],heat[j]) for j,i in enumerate(ids)}
    ridges=[r for r in col if r['D12_class']=='ZERO_AGE_RIDGE']
    a.need(len(ridges)==108,'RIDGE_SUPPORT')
    refm,refe=inv[ridges[0]['cell_id']]
    a.need(all(np.array_equal(inv[r['cell_id']][0],refm) and np.array_equal(inv[r['cell_id']][1],refe) for r in ridges),'RIDGE_REFERENCE_NOT_UNIQUE')
    rows=[]; groups=defaultdict(list); max_closure=0.; missing_side=0
    for r in atlas:
        role=r['source_role']; bid=r['boundary_id']; s=by_id[bid]
        a.need(float(r['relative_normal_m_per_year'])==s['relative_normal_velocity_m_per_year']
            and sorted([int(r['plate_a']),int(r['plate_b'])])==s['ordered_plate_pair'],'CONTACT_JOIN')
        if role not in ('SELECTED_AGE_SOURCE','UNSELECTED_POSITIVE_NORMAL_OCEAN_OCEAN'): continue
        a.need((bid in selected)==(role=='SELECTED_AGE_SOURCE'),'SOURCE_SELECTION')
        u=float(s['relative_normal_velocity_m_per_year']); length=float(s['length_m'])
        a.need(u>0 and length>0 and all(k in ex for k in (r['cell_a'],r['cell_b'])),'OPENING_SUPPORT')
        rate=length*u
        area=rate*HORIZON
        sides=[]
        for cell in (r['cell_a'],r['cell_b']):
            m,e=inv[cell]
            # Unit-length local strip, both widths from unselected design
            # envelope. Assign full relative opening to a single hypothetical
            # strip in each scenario, never sum two side alternatives.
            cases=[]
            for W in widths:
                J=1+u*HORIZON/W
                new_m=m/J; new_e=e/J
                m_err=g20.norm((new_m*J-m)/m)
                e_err=g20.norm((new_e*J-e)/e)
                max_closure=max(max_closure,m_err,e_err)
                cases.append({'initial_width_m':W,'area_ratio':J,'thickness_ratio':1/J,
                    'mass_inventory_relative_defect':m_err,'sensible_inventory_relative_defect':e_err,
                    'status':'LOCAL_CONSERVATIVE_STRETCHING_COUNTERFACTUAL_NO_WORK_OR_HEAT'})
            sides.append({'cell_id':cell,'source_age_Ma':cd[cell]['physical_age_Ma'],
                'cases':cases})
        # Alternate, mutually exclusive diagnostic: all local opening demand
        # supplied by the existing ridge reference. No donor is assigned.
        demand={'area_m2':area,'reference_crust_mass_kg':float(area*refm[0]),
            'reference_mantle_mass_kg':float(area*refm[1]),
            'reference_crust_sensible_J':float(area*refe[0]),
            'reference_mantle_sensible_J':float(area*refe[1]),
            'donor_reservoir':None,'transfer_authorized':False}
        x={'id':bid,'source_role':role,'plate_pair':':'.join(map(str,s['ordered_plate_pair'])),
            'vertices':s['endpoint_vertex_ids'],'length_m':length,'normal_m_per_year':u,
            'tangential_m_per_year':s['relative_tangential_velocity_m_per_year'],
            'opening_area_rate_m2_per_year':rate,'lower_guard_year':theta/u,'upper_guard_year':upper/u,
            'local_opening_demand_m':u*HORIZON,'local_area_demand_m2':area,
            'stretching_side_alternatives':sides,'reference_creation_demand_counterfactual':demand,
            'physical_boundary_type':None,'physical_process_selected':False}
        rows.append(x); groups[role].append(x)
    a.need(len(rows)==713 and len(groups['SELECTED_AGE_SOURCE'])==79
        and len(groups['UNSELECTED_POSITIVE_NORMAL_OCEAN_OCEAN'])==634 and max_closure<=TOL,'CONTACT_CASES')
    summaries={}
    for role,rs in groups.items():
        sm=aggregate(rs); sm['connected_components']=len(components(rs))
        sm['local_area_demand_sum_m2']=math.fsum(x['local_area_demand_m2'] for x in rs)
        sm['reference_crust_mass_demand_sum_kg']=math.fsum(x['reference_creation_demand_counterfactual']['reference_crust_mass_kg'] for x in rs)
        sm['reference_mantle_mass_demand_sum_kg']=math.fsum(x['reference_creation_demand_counterfactual']['reference_mantle_mass_kg'] for x in rs)
        sm['max_local_thinning_fraction']=max(1-z['thickness_ratio'] for x in rs for y in x['stretching_side_alternatives'] for z in y['cases'])
        summaries[role]=sm
    a.write(out/'CONTACT_DEMAND_CASES.json',rows)
    a.write(out/'OPENING_COMPONENTS.json',{role:components(rs) for role,rs in groups.items()})
    a.write(out/'CONTACT_AUTHORITY_LINEAGE.json',{str(x.relative_to(root)):a.sha(x) for x in (boundary,law,width,event)})
    return {'screen_pass':True,'horizon_years':HORIZON,'first_global_guard_year':first,
        'first_global_guard_segment':fastest['boundary_id'],'first_global_guard_pair':fastest['ordered_plate_pair'],
        'selected_age_source_pair':summaries['SELECTED_AGE_SOURCE']['plate_pairs'],
        'groups':summaries,'width_scenarios_m':widths,'max_local_inventory_relative_defect':max_closure,
        'ridge_reference_mass_kg_m2':refm.tolist(),'ridge_reference_sensible_J_m2':refe.tolist(),
        'area_sum_is_unique_new_surface':False,'donor_or_sink_admitted':False,'contacts_physically_closed':0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-contact-demand-pilot',choices=[a.SCENARIO],required=True)
    args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    c06=c10.c09.c08.c07.c06
    p=c10.OUT.with_name('R6_THERMO_G19_GLOBAL_SUPPORT_ATLAS_NEW01')
    q=c10.OUT.with_name('R6_THERMO_G20_EXCLUDED_OCEAN_HEAT_NEW01')
    pm=c.verified(p,g20.G19_PIN,g20.G19_STATUS); qm=c.verified(q,G20_PIN,G20_STATUS)
    a.need(qm['G19_manifest_sha256']==g20.G19_PIN and all(m['source_sha']==a.SHA and
        all(m[k]==v for k,v in c.SCOPE.items()) for m in (pm,qm)),'SOURCE_SCOPE')
    a.need(a.read(q/'G20_REPORT.json')['screen_pass'],'G20_SOURCE')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,c10.OUT,c06.d12.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'runner_sha256':a.sha(Path(__file__)),'G20_manifest':G20_PIN,
        'diagnostic_horizon_years':HORIZON,'scope':'Independent local counterfactual inventories; no unique global area, no physical transfer.',
        'spectral_scope':'Selected unique columns, exact semidiscrete time evolution, spatial convergence diagnostic.',
        **c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,'additional_builds':0,'additional_time_advance_years':0,
        'physical_acceptance':False,'material_assignments':0,**c.SCOPE}
    try:
        print('G21_CONTACT_DEMAND',flush=True)
        report['contacts']=contact(root,p,q,out,c06)
    except Exception as exc: report['contact_error']={'error':repr(exc),'traceback':traceback.format_exc()}
    try:
        pp=np.array([[[0,1000,0,0,0,300],[1000,2000,0,0,0,300]]],float)
        props=np.array([[2.2,2890,1000,0],[3.3,3300,1200,0]])
        z,_,_=exact(g20.setup(pp,props,16),HORIZON)
        a.need(np.array_equal(z,np.zeros_like(z)),'SPECTRAL_STEADY_FIXTURE')
        print('G21_SPECTRAL_SELFTEST_PASS',flush=True)
        report['spatial']=spatial(q,out)
    except Exception as exc: report['spatial_error']={'error':repr(exc),'traceback':traceback.format_exc()}
    report['screen_pass']=bool(report.get('contacts',{}).get('screen_pass') and report.get('spatial',{}).get('screen_pass'))
    for path,m,pin in ((p,pm,g20.G19_PIN),(q,qm,G20_PIN)):
        a.need(c.inventory(path)==m['files'] and a.sha(path/'MANIFEST.json')==pin,'PARENT_MUTATION')
    status='G21_CONTACT_DEMAND_AND_SPECTRAL_SPATIAL_PILOT_PASS__PROCESS_AUTHORITY_REQUIRED' if report['screen_pass'] else 'G21_CONTACT_OR_SPATIAL_PILOT_BLOCKED'
    report.update(status=status,limitations=[
        'Positive normal demand does not imply spreading. Selected age source is not a geological process class.',
        'Local strips are mutually exclusive scenarios; sums are demand indicators, not a gap-free spherical area or actual mass transfer.',
        'Constant reference density and sensible heat; no pressure work, latent heat, melt supply or energy of deformation.',
        'Width endpoints are unselected design bounds, not physical corridor assignments.',
        'Spectral time solution is exact for frozen semidiscrete operator only; selected columns do not qualify global spatial resolution.',
        'No changes to D12 support, G18 adjudication, event state, global assembly or physical T1.'])
    a.write(out/'G21_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G19_manifest_sha256':g20.G19_PIN,
        'G20_manifest_sha256':G20_PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G21_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True);print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
