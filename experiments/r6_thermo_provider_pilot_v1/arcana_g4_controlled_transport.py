#!/usr/bin/env python3
"""G4 controlled Lagrangian thin-shell transport, not canonical physical T1.

Frozen archived S0 velocity, no mechanical re-solve, thermal PDE, erosion,
basal mass exchange or natural exterior. Each element has three equal-area
column parcels, with original PRE owner identity and separate layer masses.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from collections import Counter, defaultdict

import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c

D_PIN='d4fd8680a35052446c9db93c08fc3384d54cb4ce9fdaccc6b046a87d511d7179'
D_STATUS='C11D_NATIVE_WEAK_FORM_CROSSCHECK_PASS__EXTERIOR_AND_TRANSPORT_PENDING'
CAP_PIN='d44d4893bd82f391a610938cd5c7be31474e60860444002ff58d88f754d5fa30'
CAP_STATUS='C11C_CAP_DIAGNOSTICS_BOUNDED__PHYSICAL_REVIEW_REQUIRED'
YEAR=365.25*86400.
SCHEMA='ARCANA_R6_G4_CONTROLLED_MOVING_COLUMN_CHECKPOINT_V1'
TOL={'mass_relative':1e-12,'area_sweep_over_initial_area':1e-11,
     'geometry_fraction':1e-4,'halfstep_position_m':1e-5,
     'halfstep_thickness_relative':1e-10,'unit_norm':2e-14}

def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),
        allow_nan=False).encode()).hexdigest()

def signed_area(p,q,r,R):
    # Algebraically equivalent to det(p,q,r), but differences avoid
    # cancellation for narrow swept spherical quadrilaterals.
    num=np.sum(p*np.cross(q-p,r-p),axis=-1)
    den=1+np.sum(p*q,axis=-1)+np.sum(q*r,axis=-1)+np.sum(r*p,axis=-1)
    a.need(np.all(den>0),'SPHERICAL_TRIANGLE_OUTSIDE_SMALL_CAP')
    return 2*R*R*np.arctan2(num,den)

def areas(p,t,R):
    return signed_area(p[t[:,0]],p[t[:,1]],p[t[:,2]],R)

def geometry_edges(t):
    edges=defaultdict(list)
    for i,row in enumerate(t):
        for j in range(3):
            u,v=int(row[j]),int(row[(j+1)%3])
            edges[tuple(sorted((u,v)))].append((i,u,v))
    a.need(all(len(v) in (1,2) for v in edges.values()),'EDGE_MULTIPLICITY')
    for v in edges.values():
        if len(v)==2:
            a.need(v[0][1:]==v[1][1:][::-1],'EDGE_ORIENTATION')
    return edges

def swept(p,q,t,R):
    # Positive area gain for outward motion of CCW edge.
    edges=geometry_edges(t)
    expected=np.zeros(len(t)); perimeter=[]; internal=[]
    for records in edges.values():
        vals=[]
        for i,u,v in records:
            gain=-float(signed_area(p[u],p[v],q[v],R)+signed_area(p[u],q[v],q[u],R))
            expected[i]+=gain; vals.append(gain)
        if len(records)==1:
            i,u,v=records[0]
            perimeter.append({'element_local_id':i+1,'directed_local_node_ids':[u+1,v+1],
                              'signed_area_gain_m2':vals[0]})
        else: internal.append(sum(vals))
    return expected,perimeter,np.array(internal)

def advect(p,velocity,R,dt):
    # Frozen canonical ambient velocity projected at current point, then
    # exponential map on sphere. First-order, no new rheology solution.
    v=velocity-np.sum(velocity*p,axis=1)[:,None]*p
    speed=np.linalg.norm(v,axis=1)
    angle=speed*dt/R
    q=np.cos(angle)[:,None]*p+(dt/R*np.sinc(angle/np.pi))[:,None]*v
    return q/np.linalg.norm(q,axis=1)[:,None]

def relative(x,y):
    x=np.asarray(x); y=np.asarray(y)
    return float(np.max(abs(x-y))/max(float(np.max(abs(x))),float(np.max(abs(y))),1e-300))

def seal(state):
    return {'schema':SCHEMA,'state_sha256':digest(state),'state':state}

def unseal(p):
    z=a.read(p)
    a.need(z['schema']==SCHEMA and z['state_sha256']==digest(z['state']),'CHECKPOINT_HASH')
    return z['state']

def layer_profiles(rows):
    # Polynomial in normalized material depth s, carried as a passive tracer.
    h=[]; coeff=[]; rho=[]; alpha=[]; cp=[]
    for row in rows:
        hh=[]; cc=[]; rr=[]; aa=[]; pp=[]
        for k,role in ((1,'crust'),(2,'mantle')):
            pre=f'layer{k}_'; thick=row[pre+'z1_m']-row[pre+'z0_m']
            a.need(thick>0,'PRE_LAYER_THICKNESS')
            hh.append(thick)
            cc.append([row[pre+name]*thick**power for power,name in enumerate(
                ('c0_k','c1_k_m','c2_k_m2','c3_k_m3'))])
            rr.append(row[role+'_density_kg_m3']); aa.append(row[role+'_expansivity_k_1'])
            pp.append(row[role+'_cp_j_kg_k'])
        h.append(hh); coeff.append(cc); rho.append(rr); alpha.append(aa); cp.append(pp)
    return tuple(np.array(x,dtype=float) for x in (h,coeff,rho,alpha,cp))

def material_moments(coeff,rho,alpha,cp):
    # Analytic integral for density rho0*(1-alpha*T), plus independent
    # 4-point Gauss quadrature for the cubic and its degree-six energy tracer.
    mean=np.sum(coeff/np.arange(1,5),axis=-1)
    analytic=rho*(1-alpha*mean)
    x,w=np.polynomial.legendre.leggauss(4); s=(x+1)/2
    temp=np.einsum('...k,gk->...g',coeff,s[:,None]**np.arange(4))
    effective=rho[...,None]*(1-alpha[...,None]*temp)
    a.need(np.isfinite(temp).all() and np.all(temp>0) and np.all(effective>0),'PRE_DENSITY_TEMPERATURE')
    numeric=np.sum(effective*w/2,axis=-1)
    a.need(relative(analytic,numeric)<=1e-13,'ANALYTIC_DENSITY_QUADRATURE')
    tracer=np.sum(effective*cp[...,None]*temp*w/2,axis=-1)
    return analytic,numeric,tracer

def initial(package,mapped,pretext,state,manifest):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
    from experiments.shellset_regional_explore_v1.build_case import MARKER, SCHEMA as PRE_SCHEMA
    from arcana_worldsim.r6.shellset_mesh.coordinates import rotation_matrices
    lines=pretext.splitlines()
    a.need(lines[0].split()==[MARKER,PRE_SCHEMA,'81'] and len(lines)==82,'PRE_HEADER')
    rows=[]
    for i,line in enumerate(lines[1:],1):
        fields=line.split()
        a.need(len(fields)==len(FIELDS) and int(fields[0])==i,'PRE_LOCAL_ID')
        row=dict(zip(FIELDS,map(float,fields),strict=True))
        a.need(np.isfinite(list(row.values())).all(),'PRE_FINITE')
        rows.append(row)
    m=package['G4_mapping']; nodes=m['nodes']; elems=m['elements']
    a.need([x['local_id'] for x in nodes]==list(range(1,82)) and
           [x['local_id'] for x in elems]==list(range(1,129)),'MAPPING_ORDER')
    ids=[x['parent_id'] for x in nodes]; eids=[x['parent_id'] for x in elems]
    a.need(len(set(ids))==81 and len(set(eids))==128,'PARENT_ID_UNIQUENESS')
    lookup={p:i for i,p in enumerate(ids)}
    t=np.array([[lookup[p] for p in e['parent_node_ids']] for e in elems],dtype=int)
    lat,lon=np.deg2rad(np.array([x['runtime_lat_lon_deg'] for x in nodes])).T
    runtime=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    _,inverse=rotation_matrices(); p=runtime@inverse.T
    v=np.array([mapped['canonical_xyz_m_s_by_parent_node'][str(k)] for k in ids])
    a.need(v.shape==(81,3) and np.isfinite(v).all() and
           np.max(abs(np.sum(p*v,axis=1)))<=1e-21,'CANONICAL_TANGENCY')
    R=float(package['lr_native_parameters']['radius'])
    # Preserve native ordering and record any orientation permutation.
    native_t=t.copy(); signed=areas(p,t,R)
    a.need(np.all(abs(signed)>0),'INITIAL_DEGENERATE')
    flip=signed<0; t[flip]=t[flip][:,[0,2,1]]
    area=areas(p,t,R); edges=geometry_edges(t)
    a.need(np.all(area>0) and sum(len(x)==1 for x in edges.values())==32,'REGION_GEOMETRY')
    h,coeff,rho,alpha,cp=layer_profiles(rows)
    feg=np.asarray(package['feg_columns'],dtype=float)
    a.need(feg.shape==(81,4) and np.array_equal(feg[:,0],np.arange(1,82)) and
           np.allclose(h,feg[:,2:4],rtol=1e-12,atol=1e-6),'PRE_FEG_LAYER_BINDING')
    density,independent,heat=material_moments(coeff,rho,alpha,cp)
    h=h[t]; coeff=coeff[t]; rho=rho[t]; alpha=alpha[t]; cp=cp[t]
    mass=area[:,None,None]/3*h*density[t]
    sensible=area[:,None,None]/3*h*heat[t]
    a.need(np.all(mass>0),'MASS_POSITIVE')
    clock=package['initial_time_proposal']
    a.need(clock['candidate_trial_year']==1. and clock['same_start_halving_year']==.5
           and clock['event_horizon_exclusive_year']>1.,'CLOCK_POLICY')
    strain=state['strain_rate']; w=state['quadrature_area']
    a.need(strain.shape==(128,7,3) and w.shape==(128,7) and np.all(w>0),'NATIVE_QUADRATURE')
    div=np.sum(w*(strain[:,:,0]+strain[:,:,1]),axis=1)/np.sum(w,axis=1)
    return {'source_sha':a.SHA,'C11D_manifest_sha256':D_PIN,'C10_manifest_sha256':a.PIN,
        'PRE_source_sha256':manifest,'elapsed_years':0.,'event_horizon_year':clock['event_horizon_exclusive_year'],
        'radius_m':R,'node_parent_ids':ids,'element_parent_ids':eids,
        'native_triangles_zero_based':native_t.tolist(),'transport_triangles_zero_based':t.tolist(),
        'canonical_unit_xyz':p.tolist(),'frozen_canonical_velocity_m_s':v.tolist(),
        'original_PRE_rows_tokens':[line.split() for line in lines[1:]],
        'area_m2':area.tolist(),'initial_area_m2':area.tolist(),
        'thickness_m':h.tolist(),'initial_thickness_m':h.tolist(),
        'normalized_depth_temperature_coefficients_K':coeff.tolist(),
        'rho_reference_kg_m3':rho.tolist(),'alpha_K_inverse':alpha.tolist(),'cp_J_kg_K':cp.tolist(),
        'layer_mass_kg':mass.tolist(),'passive_sensible_heat_tracer_J':sensible.tolist(),
        'native_mean_horizontal_divergence_s_inv':div.tolist(),
        'policy':'Lagrangian equal-area corner parcels, shallow-column area times thickness; fixed mass, frozen T(s), no external mass exchange relative to moving boundary.',
        **c.SCOPE}

def advance(s,years):
    a.need(years in (.5,1.) and s['elapsed_years']+years<=1.
           and s['elapsed_years']+years<s['event_horizon_year'],'TIME_GUARD')
    p=np.asarray(s['canonical_unit_xyz']); t=np.asarray(s['transport_triangles_zero_based'])
    R=s['radius_m']; v=np.asarray(s['frozen_canonical_velocity_m_s'])
    old=np.asarray(s['area_m2']); h=np.asarray(s['thickness_m'])
    mass=np.asarray(s['layer_mass_kg']); coeff=np.asarray(s['normalized_depth_temperature_coefficients_K'])
    rho=np.asarray(s['rho_reference_kg_m3']); alpha=np.asarray(s['alpha_K_inverse']); cp=np.asarray(s['cp_J_kg_K'])
    a.need(relative(areas(p,t,R),old)<=1e-13,'CHECKPOINT_AREA')
    den,ind,heat=material_moments(coeff,rho,alpha,cp)
    a.need(relative(old[:,None,None]/3*h*ind,mass)<=TOL['mass_relative'],'CHECKPOINT_MASS')
    q=advect(p,v,R,years*YEAR); new=areas(q,t,R)
    a.need(np.all(new>0) and np.max(abs(np.linalg.norm(q,axis=1)-1))<=TOL['unit_norm'],'POSITIVE_GEOMETRY')
    newh=h*(old/new)[:,None,None]
    a.need(np.all(newh>0),'POSITIVE_LAYER')
    newmass=new[:,None,None]/3*newh*ind
    # Independent reintegration of the transported normalized temperature
    # profile, not an assertion of conductive or thermodynamic equilibrium.
    newheat=new[:,None,None]/3*newh*heat
    masserr=float(np.max(abs(newmass-mass)/mass))
    heaterr=float(np.max(abs(newheat-np.asarray(s['passive_sensible_heat_tracer_J']))/
                            np.asarray(s['passive_sensible_heat_tracer_J'])))
    gain,boundary,internal=swept(p,q,t,R)
    delta=new-old
    boundary_gain=sum(x['signed_area_gain_m2'] for x in boundary)
    areaerr=float(np.max(abs(delta-gain)/old))
    globalerr=abs(float(delta.sum())-boundary_gain)/float(old.sum())
    internalerr=float(np.max(abs(internal)))/float(old.min())
    displacement=R*np.arctan2(np.linalg.norm(np.cross(p,q),axis=1),np.sum(p*q,axis=1))
    relarea=float(np.max(abs(new/old-1)))
    relthick=float(np.max(abs(newh/h-1)))
    edges=geometry_edges(t)
    edge_min=min(R*math.atan2(np.linalg.norm(np.cross(p[u],p[w])),p[u]@p[w]) for u,w in edges)
    native_rate=np.asarray(s['native_mean_horizontal_divergence_s_inv'])
    geom_rate=delta/old/(years*YEAR)
    report={'years':years,'model_elapsed_years':s['elapsed_years']+years,
        'min_area_m2':float(new.min()),'min_layer_thickness_m':float(newh.min()),
        'max_displacement_m':float(displacement.max()),
        'max_displacement_over_min_edge':float(displacement.max()/edge_min),
        'max_relative_area_change':relarea,'max_relative_thickness_change':relthick,
        'max_parcel_relative_mass_error':masserr,'max_passive_heat_tracer_relative_error':heaterr,
        'mass_before_kg_by_layer':mass.sum(axis=(0,1)).tolist(),
        'mass_reintegrated_after_kg_by_layer':newmass.sum(axis=(0,1)).tolist(),
        'relative_boundary_mass_flux_kg_by_layer':[0.,0.],
        'boundary_flux_scope':'Zero by Lagrangian co-motion assumption; not zero flux through original fixed geographic mask.',
        'moving_boundary_signed_swept_area_m2':boundary_gain,
        'boundary_sweep_by_edge':boundary,'per_element_area_sweep_relative_error':areaerr,
        'global_boundary_area_closure_relative_error':globalerr,'internal_edge_sweep_cancellation_relative_error':internalerr,
        'native_vs_geometric_area_rate_max_difference_s_inv':float(np.max(abs(native_rate-geom_rate))),
        'native_vs_geometric_area_rate_normalized_difference':relative(native_rate,geom_rate),
        'native_rate_comparison_scope':'Diagnostic only: frozen nodal geodesic transport is not exactly native FE interior interpolation.',
        **c.SCOPE}
    report['screen_pass']=bool(max(masserr,heaterr)<=TOL['mass_relative'] and
        max(areaerr,globalerr,internalerr)<=TOL['area_sweep_over_initial_area'] and
        max(relarea,relthick,report['max_displacement_over_min_edge'])<=TOL['geometry_fraction'])
    result=dict(s,elapsed_years=s['elapsed_years']+years,canonical_unit_xyz=q.tolist(),
                area_m2=new.tolist(),thickness_m=newh.tolist())
    return result,report

def owner_budgets(s):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
    t=np.asarray(s['transport_triangles_zero_based'])
    area=np.asarray(s['area_m2'])
    h=np.asarray(s['thickness_m'])
    coeff=np.asarray(s['normalized_depth_temperature_coefficients_K'])
    rho=np.asarray(s['rho_reference_kg_m3']); alpha=np.asarray(s['alpha_K_inverse']); cp=np.asarray(s['cp_J_kg_K'])
    _,density,_=material_moments(coeff,rho,alpha,cp)
    observed=area[:,None,None]/3*h*density
    rows=[dict(zip(FIELDS,x,strict=True)) for x in s['original_PRE_rows_tokens']]
    before=np.asarray(s['layer_mass_kg'])
    groups=defaultdict(lambda:[0.,0.])
    for i,tri in enumerate(t):
        for j,n in enumerate(tri):
            row=rows[n]
            for k,role in enumerate(('crust','mantle')):
                key=(int(float(row['owner_row'])),int(float(row['owner_column'])),
                     int(float(row['owner_domain_id'])),role,
                     int(float(row[role+'_material_code'])))
                groups[key][0]+=float(before[i,j,k])
                groups[key][1]+=float(observed[i,j,k])
    return [{'source_owner_row':k[0],'source_owner_column':k[1],'source_domain_id':k[2],
             'layer':k[3],'reference_material_code':k[4],
             'initial_mass_kg':v[0],'reintegrated_mass_kg':v[1],
             'relative_mass_error':abs(v[1]-v[0])/v[0]}
            for k,v in sorted(groups.items())]

def selftest():
    p=np.array([[1.,0,0],[1,.01,0],[1,0,.01]])
    p/=np.linalg.norm(p,axis=1)[:,None]
    t=np.array([[0,1,2]])
    R=6371000.
    q=advect(p,np.array([[0.,0,0],[0,1e-9,0],[0,0,1e-9]]),R,YEAR)
    gain,b,internal=swept(p,q,t,R)
    a.need(abs(float((areas(q,t,R)-areas(p,t,R)-gain)[0]))/float(areas(p,t,R)[0])<1e-11,
           'SWEPT_AREA_SELFTEST')
    coeff=np.array([[[300.,500.,-20.,10.]]]); rho=np.array([[2800.]])
    d,g,heat=material_moments(coeff,rho,np.array([[3e-5]]),np.array([[1000.]]))
    a.need(relative(d,g)<1e-13 and np.all(heat>0),'MATERIAL_SELFTEST')
    print('G4_SYNTHETIC_SELFTEST_PASS',flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-controlled-transport',choices=[a.SCENARIO])
    ap.add_argument('--restart',type=Path)
    ap.add_argument('--restart-file-sha256')
    args=ap.parse_args()
    selftest()
    out=args.output.resolve()
    a.need(not out.exists(),'OUTPUT_NOT_FRESH')
    if args.restart:
        a.need(args.restart_file_sha256==a.sha(args.restart),'RESTART_FILE_PIN')
        s=unseal(args.restart)
        a.need(s['elapsed_years']==.5 and s['C11D_manifest_sha256']==D_PIN,'RESTART_STATE')
        out.mkdir()
        end,rep=advance(s,.5)
        a.write(out/'CHECKPOINT.json',seal(end)); a.write(out/'STEP_REPORT.json',rep)
        return 0 if rep['screen_pass'] else 2
    a.need(args.authorize_controlled_transport==a.SCENARIO,'CONTROLLED_TRANSPORT_AUTHORITY')
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    d=c10.OUT.with_name('R6_THERMO_C11D_NATIVE_BALANCE_NEW01')
    caps=c10.OUT.with_name('R6_THERMO_C11C_CAP_BOUNDS_NEW01')
    base=c10.OUT.with_name('R6_THERMO_C11BR1_CONVERGENCE_NEW01')
    dm=c.verified(d,D_PIN,D_STATUS); c.verified(caps,CAP_PIN,CAP_STATUS); c.verified(base,c.R1_PIN,c.R1_STATUS)
    a.need(dm['source_sha']==a.SHA and dm['cap_manifest_sha256']==CAP_PIN and
        dm['R1_manifest_sha256']==c.R1_PIN and dm['additional_native_solves']==0 and
        all(dm[k]==v for k,v in c.SCOPE.items()),'C11D_LINEAGE')
    dr=a.read(d/'C11D_ANALYSIS.json')
    a.need(dr['screen_pass'] and dr['native_fault_and_basal_tangential_terms_exact_zero'],'C11D_SCREEN')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(cm[k]==v for k,v in c10.SCOPE.items()),'C10_SCOPE')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    a.need(not any(out.is_relative_to(p) for p in (root,d,caps,base,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'scenario':a.SCENARIO,'C11D_manifest':D_PIN,'tolerances':TOL,
        'runner_sha256':a.sha(Path(__file__)),'additional_native_solves':0,
        'natural_exterior_qualified':False,'thermal_equation_advanced':False,
        'physical_acceptance':False,**c.SCOPE})
    pre=c10.OUT/'regional_PRE.dat'
    with np.load(base/'C11B_FINAL_STATE.npz') as state:
        s=initial(a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json'),
            a.read(d/'G4_PARENT_BOUND_FIELDS.json'),pre.read_text(),state,a.sha(pre))
    a.write(out/'INITIAL_CHECKPOINT.json',seal(s))
    one,rep1=advance(s,1.)
    half,reph=advance(s,.5)
    two,rep2=advance(half,.5)
    a.write(out/'ONE_YEAR_CHECKPOINT.json',seal(one))
    a.write(out/'HALF_YEAR_CHECKPOINT.json',seal(half))
    a.write(out/'TWO_HALF_STEPS_CHECKPOINT.json',seal(two))
    a.write(out/'ONE_YEAR_STEP_REPORT.json',rep1)
    a.write(out/'HALF_YEAR_STEP_REPORT.json',reph)
    a.write(out/'SECOND_HALF_STEP_REPORT.json',rep2)
    # Restart must be performed by a fresh Python interpreter reading a
    # serialized checkpoint, not an in-memory alias of the previous state.
    hp=out/'HALF_YEAR_CHECKPOINT.json'; restart=out/'restart'
    cmd=[sys.executable,str(Path(__file__).resolve()),'--restart',str(hp),
         '--restart-file-sha256',a.sha(hp),'--output',str(restart)]
    with (out/'restart.log').open('x') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    replay=unseal(restart/'CHECKPOINT.json')
    exact=digest(replay)==digest(two)
    p,q=np.array(one['canonical_unit_xyz']),np.array(two['canonical_unit_xyz'])
    position=float(s['radius_m']*np.max(np.linalg.norm(p-q,axis=1)))
    thickness=relative(one['thickness_m'],two['thickness_m'])
    # Retain per-owner parcel identities and layer inventories; no mixing.
    identities=all(one[k]==s[k]==two[k] for k in ('node_parent_ids','element_parent_ids',
        'transport_triangles_zero_based','original_PRE_rows_tokens','layer_mass_kg',
        'normalized_depth_temperature_coefficients_K','passive_sensible_heat_tracer_J'))
    budgets=owner_budgets(one)
    budget_error=max(x['relative_mass_error'] for x in budgets)
    a.write(out/'OWNER_LAYER_MASS_BUDGETS.json',{'owner_layer_group_count':len(budgets),
        'max_relative_mass_error':budget_error,'groups':budgets})
    success=budget_error<=TOL['mass_relative'] and all(x['screen_pass'] for x in (rep1,reph,rep2)) and result.returncode==0 and exact and identities and \
        position<=TOL['halfstep_position_m'] and thickness<=TOL['halfstep_thickness_relative']
    status='G4_CONTROLLED_MOVING_COLUMN_TRANSPORT_PASS__PHYSICAL_ACCEPTANCE_PENDING' if success else 'G4_CONTROLLED_TRANSPORT_BLOCKED'
    report={'status':status,'screen_pass':success,'one_year':rep1,'first_half':reph,'second_half':rep2,
        'separate_process_restart_exact':exact,'restart_exit':result.returncode,'parent_and_material_identity_preserved':identities,
        'one_vs_two_half_max_position_difference_m':position,'one_vs_two_half_relative_thickness_difference':thickness,
        'tolerances':TOL,'owner_layer_group_count':len(budgets),'max_owner_layer_relative_mass_error':budget_error,
        'additional_native_solves':0,'physical_acceptance':False,
        'limitations':['Moving material control volume, not fixed geographic patch; natural exterior flux unresolved.',
            'Three equal-area corner parcels per triangle, thin-shell column mass; no deep spherical volume correction.',
            'Temperature carried as passive normalized-depth profile; no thermal PDE, pressure re-equilibration or rheology update.',
            'No geological or mineral assignment, surface erosion, phase change or basal exchange.',
            'Half-step test covers frozen-velocity transport only, not coupled mechanics. Independent exterior traction reconstruction still open.',
            'Checkpoint schema is experimental and not a HistoryStore production input.'],**c.SCOPE}
    a.write(out/'G4_TRANSPORT_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'C11D_manifest_sha256':D_PIN,
        'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    # Concise operator receipt, full per-edge and parcel records retained.
    print(json.dumps({k:v for k,v in report.items() if k not in ('one_year','first_half','second_half')},indent=2),flush=True)
    print(json.dumps({'one_year':{k:v for k,v in rep1.items() if k!='boundary_sweep_by_edge'}},indent=2),flush=True)
    print('G4_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if success else 2

if __name__=='__main__':
    raise SystemExit(main())
