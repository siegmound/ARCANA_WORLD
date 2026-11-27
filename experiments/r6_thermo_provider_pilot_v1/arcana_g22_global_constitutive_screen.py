#!/usr/bin/env python3
"""G22 global constitutive sensitivity on source PRE columns.

Native Legacy and Diorite2 are evaluated on ALL numerical owner columns;
Yu analogues are evaluated on deterministic strata with the existing C09
scalar evaluator. These are comparative strength envelopes, not lithology
assignments, native nonlinear solves, or physical admission.
"""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c

G19_PIN='79f2ea1a004cbb65a9b6a1967e833eba8e3c171bfc07fe9bd65f9eec641e91ca'
G19_STATUS='G19_GLOBAL_SUPPORT_ATLAS_PASS__MATERIAL_AND_BOUNDARY_CLOSURE_REQUIRED'
G21_PIN='b46d2d3659948be1769f69807ccd8af7e179fe074294b7dc6d47223f784f5a54'
G21_STATUS='G21_CONTACT_DEMAND_AND_SPECTRAL_SPATIAL_PILOT_PASS__PROCESS_AUTHORITY_REQUIRED'
G20_PIN='abb7cfad2ee7439dd3f0c1b9a6863b27a922f5b3c38858b93234bdd7effe7f47'
MODELS=('native_legacy','native_diorite2')
MODES=('dry','hydrostatic')
N=256
BATCH=256
Q_SCREEN=.005 # diagnostic quadrature comparison, not a physical error budget

def norm(v): return float(np.max(np.abs(v)))

def span(x):
    x=np.asarray(x)
    a.need(x.size>0 and np.isfinite(x).all(),'NONFINITE_SUMMARY')
    return {k:float(v) for k,v in zip(('min','p05','median','p95','max'),
        np.percentile(x,[0,5,50,95,100]))}

def integrated(rows,fields,models,rates,gravity,water,g2,n=N):
    """Return [node, model, rate, pore scenario, layer] strength and
    coarse quadrature differences, native exponent and C08 common exponent.
    Reuse exact C09 pressure and stress conventions; vectorized only.
    """
    idx={k:i for i,k in enumerate(fields)}
    nr=len(rows); shape=(nr,2,len(rates),2,2)
    result=np.empty(shape); coarse=np.empty(shape); common=np.empty(shape)
    mechanism=np.zeros(shape+(3,),dtype=np.int32)
    pivot=math.sqrt(min(rates.values())*max(rates.values()))
    grid=np.linspace(0,1,n+1)[None,:]
    a.need(n%2==0 and np.isfinite(rows).all(),'BATCH_INPUT')
    p={k:rows[:,i,None] for k,i in idx.items()}
    alpha={key:p[key+'_expansivity_k_1'] for key in ('crust','mantle')}
    for layer in (1,2):
        prefix=f'layer{layer}_'
        start,stop=p[prefix+'z0_m'],p[prefix+'z1_m']
        z=start+(stop-start)*grid; x=z-start
        T=p[prefix+'c0_k']+x*(p[prefix+'c1_k_m']+x*(p[prefix+'c2_k_m2']+x*p[prefix+'c3_k_m3']))
        P=g2.pressure(p,z,gravity,alpha)
        a.need(np.isfinite(T).all() and np.all(T>0) and np.all(P>=0)
            and np.all(stop>start),'THERMAL_PRESSURE_DOMAIN')
        for mi,key in enumerate(MODELS):
            model=models[key]
            for ri,rate in enumerate(rates.values()):
                for wi,mode in enumerate(MODES):
                    eff=P-(water*gravity*z if mode=='hydrostatic' else 0.)
                    a.need(np.all(eff>=0),'NEGATIVE_EFFECTIVE_PRESSURE')
                    creep,brittle,cap=g2.native_components(model,layer-1,z,T,eff,rate,model['eCreep'],pivot)
                    comp,_,_=g2.native_components(model,layer-1,z,T,eff,rate,g2.COMMON_E,pivot)
                    stress=np.minimum(np.minimum(creep,cap),brittle)
                    other=np.minimum(np.minimum(comp,cap),brittle)
                    ix=(slice(None),mi,ri,wi,layer-1)
                    a.need(np.isfinite(stress).all() and np.all(stress>=0) and np.isfinite(other).all(),'STRESS_FINITE')
                    result[ix]=np.trapezoid(stress,z,axis=1)
                    coarse[ix]=np.trapezoid(stress[:,::2],z[:,::2],axis=1)
                    common[ix]=np.trapezoid(other,z,axis=1)
                    b=brittle<=np.minimum(creep,cap)
                    d=(~b)&(cap<=creep)
                    mechanism[ix+(0,)]=b.sum(axis=1)
                    mechanism[ix+(1,)]=d.sum(axis=1)
                    mechanism[ix+(2,)]=(~(b|d)).sum(axis=1)
    a.need(np.all(result>0) and np.all(coarse>0) and np.all(common>0)
        and np.all(mechanism.sum(axis=-1)==n+1),'INTEGRAL_OR_MECHANISM')
    return result,coarse,common,mechanism

def scalar_check(row,fields,models,rates,gravity,water,g2,arrays):
    # Original C09 scalar implementation: check every native scenario,
    # including all layers, before using the vectorized global kernel.
    p=dict(zip(fields,map(float,row)))
    pivot=math.sqrt(min(rates.values())*max(rates.values()))
    alpha={k:p[k+'_expansivity_k_1'] for k in ('crust','mantle')}
    S,C,E,M=arrays
    worst=0.
    for ri,rate in enumerate(rates.values()):
        for wi,mode in enumerate(MODES):
            vals=g2.column_runs(p,models,rate,pivot,gravity,water,alpha,mode,False)
            for mi,key in enumerate(MODELS):
                q=vals[key]; ref=np.array(q['layers_N_m']); other=np.array(q['common_e_layers_N_m'])
                d=max(norm((S[mi,ri,wi]-ref)/ref),norm((E[mi,ri,wi]-other)/other))
                worst=max(worst,d)
                rel=abs(C[mi,ri,wi].sum()/S[mi,ri,wi].sum()-1)
                a.need(abs(rel-q['relative_128_vs_256'])<=1e-12,'COARSE_SCALAR_PARITY')
    a.need(worst<=1e-12,'VECTOR_SCALAR_PARITY')
    return worst

def load(root,p,c10):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
    from experiments.shellset_regional_explore_v1 import build_case
    from experiments.r6_thermo_provider_pilot_v1 import c09_column_scenarios as g2,c09_mechanical_case as c09
    report=c09.global_route(root)
    path=root/(build_case.PRE+'.dat')
    a.need(a.sha(path)==report['source_PRE_sha256'],'PRE_PIN')
    with path.open() as f:
        a.need(int(f.readline().split()[-1])==64442,'PRE_HEADER')
        rows=np.loadtxt(f)
    a.need(rows.shape==(64442,len(FIELDS)) and np.array_equal(rows[:,0],np.arange(1,64443)),'PRE_SHAPE')
    with (p/'GLOBAL_NODAL_SUPPORT.csv').open() as f: atlas=list(csv.DictReader(f))
    a.need(len(atlas)==len(rows) and all(int(x['node_id'])==i+1 and int(x['PRE_owner_domain'])==int(rows[i,3])
        and x['constitutive_assignment']=='UNASSIGNED' for i,x in enumerate(atlas)),'ATLAS_LINK')
    domain=rows[:,3].astype(int)
    support=np.array([x['conditional_support_status'] for x in atlas])
    a.need(dict(Counter(support))=={'SOURCE_DERIVED_CONDITIONAL':58916,'MIXED_OR_CONFLICTING_SUPPORT':4370,
        'UNKNOWN':1156} and set(domain)==set(range(1,7)),'SUPPORT_INVENTORY')
    catalog=g2.model_catalog(root,a.sha)
    old=a.read(p/'RETAINED_CONSTITUTIVE_CANDIDATES.json')
    a.need(all(catalog[k]==v for k,v in old.items()),'CATALOG_REPLAY')
    reference=c10.c09.c08.c07.native_candidate(root)
    gravity=reference['parameters']['gMean']['value']
    water=reference['parameters']['reference_densities']['seawater']['nominal']
    a.need(np.all(rows[:,FIELDS.index('rho_water_kg_m3')]==water),'REFERENCE_WATER')
    assessment=root/c10.c09.c08.c07.PLATE/'R6_G2_G3_CALIBRATION_ASSESSMENT_20261120.json'
    original=a.read(assessment)['source_records']['kinematic_rate_proxies_s_inv']
    rates={f'C08_{k}km_proxy':float(v) for k,v in original.items()}
    rates['Yu_reference']=float(catalog['layered_yu_initial']['reference_rate_s_inv'])
    a.need(len(rates)==4 and all(0<v<1 for v in rates.values()),'RATE_SCENARIOS')
    return rows,FIELDS,atlas,domain,support,catalog,rates,gravity,water,g2,report['source_PRE_sha256']

def global_runs(rows,fields,domain,support,models,rates,gravity,water,g2,out):
    # Unique numeric column records, not geographic deduplication.
    idx=[fields.index(k) for k in fields if k.startswith(('crust_','mantle_','layer1_','layer2_'))]
    _,first,inv=np.unique(rows[:,idx],axis=0,return_index=True,return_inverse=True)
    inv=inv.reshape(-1)
    data=rows[first]
    shape=(len(data),2,len(rates),2,2)
    S=np.empty(shape); C=np.empty(shape); E=np.empty(shape); M=np.empty(shape+(3,),np.int32)
    for i in range(0,len(data),BATCH):
        sl=slice(i,min(i+BATCH,len(data)))
        S[sl],C[sl],E[sl],M[sl]=integrated(data[sl],fields,models,rates,gravity,water,g2)
    # Check all six owner domains against the retained independent scalar path.
    worst=0.
    for d in range(1,7):
        j=int(np.flatnonzero(domain==d)[0]); i=inv[j]
        worst=max(worst,scalar_check(rows[j],fields,models,rates,gravity,water,g2,(S[i],C[i],E[i],M[i])))
    total=S.sum(axis=-1); err=abs(C.sum(axis=-1)/total-1); ce=E.sum(axis=-1)/total-1
    layer_error=abs(C/S-1)
    bad=np.any(err>Q_SCREEN,axis=(1,2,3)) | np.any(layer_error>Q_SCREEN,axis=(1,2,3,4))
    # Refine only columns exceeding the provisional numerical screen.
    refined=np.flatnonzero(bad)
    final_n=np.full(len(data),N,dtype=int)
    for start in range(0,len(refined),BATCH):
        ii=refined[start:start+BATCH]
        f,co,com,m=integrated(data[ii],fields,models,rates,gravity,water,g2,2*N)
        a.need(np.allclose(co,S[ii],rtol=1e-12,atol=0),'REFINEMENT_NESTING')
        S[ii]=f; C[ii]=co; E[ii]=com; M[ii]=m; final_n[ii]=2*N
    total=S.sum(axis=-1); err=abs(C.sum(axis=-1)/total-1); ce=E.sum(axis=-1)/total-1
    layer_error=abs(C/S-1)
    remain=np.any(err>Q_SCREEN,axis=(1,2,3)) | np.any(layer_error>Q_SCREEN,axis=(1,2,3,4))
    np.savez_compressed(out/'GLOBAL_NATIVE_STRENGTH.npz',node_ids=rows[:,0].astype(int),unique_source_node_ids=data[:,0].astype(int),
        node_to_column=inv,models=np.array(MODELS),rate_names=np.array(list(rates)),rates_s_inv=np.array(list(rates.values())),
        modes=np.array(MODES),strength_N_m=S,coarse_strength_N_m=C,common_e_strength_N_m=E,
        mechanism_sample_counts=M,intervals_per_layer=final_n,quadrature_screen_pass=~remain)
    # Sample counts are diagnostics, not depth fractions or likelihoods.
    idx_rate=list(rates).index('C08_100km_proxy')
    ref=total[:,1,idx_rate,1]
    ratio=total[:,1]/total[:,0]
    strata=[]
    chosen=set()
    for d in range(1,7):
        for st in sorted(set(support[domain==d])):
            nodes=np.flatnonzero((domain==d)&(support==st))
            if not len(nodes): continue
            ii=inv[nodes]
            # Min/median/max of a common diagnostic plus extrema of LAB and flux.
            for v in (ref[ii],rows[nodes,fields.index('lab_depth_m')],rows[nodes,fields.index('surface_heat_flow_w_m2')]):
                order=np.lexsort((nodes,v)); chosen.update(int(nodes[order[k]]) for k in (0,len(order)//2,len(order)-1))
            strata.append({'domain_id':d,'support':str(st),'nodes':len(nodes),
                'native_Diorite2_reference_strength_N_m':span(ref[ii]),
                'native_Legacy_reference_strength_N_m':span(total[ii,0,idx_rate,1]),
                'Diorite2_over_Legacy_all_scenarios':span(ratio[ii]),
                'dry_over_hydrostatic_all_models_rates':span(total[ii,:,:,0]/total[ii,:,:,1]),
                'common_exponent_relative_change':span(ce[ii]),
                'max_quadrature_relative_layer_difference':norm(layer_error[ii]),
                'nodes_remaining_outside_quadrature_screen':int(remain[ii].sum())})
    a.write(out/'GLOBAL_STRENGTH_STRATA.json',strata)
    return {'screen_pass':True,'nodes':len(rows),'unique_numeric_columns':len(data),
        'native_scenarios_per_column':2*len(rates)*2,'source_rates_s_inv':rates,
        'scalar_vector_max_relative':worst,'refined_unique_columns':len(refined),
        'remaining_unique_columns_outside_provisional_quadrature_screen':int(remain.sum()),
        'remaining_nodes_outside_provisional_quadrature_screen':int(remain[inv].sum()),
        'max_total_quadrature_relative_difference':norm(err),'max_layer_quadrature_relative_difference':norm(layer_error),
        'Diorite2_over_Legacy_all_scenarios':span(ratio[inv]),
        'common_exponent_relative_change':span(ce[inv]),
        'domain_summary':[{'domain_id':d,'nodes':int((domain==d).sum()),
          'Diorite2_reference_N_m':span(ref[inv[domain==d]]),
          'Legacy_reference_N_m':span(total[inv[domain==d],0,idx_rate,1])} for d in range(1,7)],
        'strata':len(strata),'stratified_nodes':len(chosen),'physical_assignments':0}, sorted(chosen)

def layered_runs(rows,fields,domain,support,chosen,models,rates,gravity,water,g2,out):
    pivot=math.sqrt(min(rates.values())*max(rates.values()))
    records=[]; summaries=defaultdict(list)
    for j in chosen:
        p=dict(zip(fields,map(float,rows[j])))
        alpha={k:p[k+'_expansivity_k_1'] for k in ('crust','mantle')}
        for name,rate in rates.items():
            for mode in MODES:
                vals=g2.column_runs(p,models,rate,pivot,gravity,water,alpha,mode,False)
                # All comparisons retain C09 synthetic analogue semantics,
                # including on oceanic columns; not geological assignments.
                r={'node_id':int(rows[j,0]),'domain_id':int(domain[j]),'support':str(support[j]),
                    'rate_s_inv':rate,'rate_name':name,'mode':mode,'cases':vals,
                    'material_assignment':None,'source_validity_qualified':False}
                records.append(r)
                for key in ('layered_homogeneous','layered_two_crust'):
                    v=vals[key]
                    a.need(math.isfinite(v['total_N_m']) and v['total_N_m']>0,'LAYERED_INTEGRAL')
                    summaries[(int(domain[j]),key)].append((v['total_N_m']/vals['native_diorite2']['total_N_m'],
                        v['relative_128_vs_256'],v['common_e_relative_total_error']))
    a.write(out/'STRATIFIED_LAYERED_SCENARIOS.json',records)
    return {'screen_pass':True,'nodes':len(chosen),'scenario_records':len(records),
        'domain_analogue_comparisons':[{'domain_id':d,'analogue':k,'strength_over_Diorite2':span(np.array(v)[:,0]),
            'max_quadrature_relative_difference':norm(np.array(v)[:,1]),
            'common_e_relative_change':span(np.array(v)[:,2])} for (d,k),v in sorted(summaries.items())],
        'mineralogical_inference':False,'physical_assignments':0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-global-constitutive-screen',choices=[a.SCENARIO],required=True)
    args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    p=c10.OUT.with_name('R6_THERMO_G19_GLOBAL_SUPPORT_ATLAS_NEW01')
    q=c10.OUT.with_name('R6_THERMO_G21_CONTACT_DEMAND_NEW01')
    pm=c.verified(p,G19_PIN,G19_STATUS); qm=c.verified(q,G21_PIN,G21_STATUS)
    a.need(qm['G19_manifest_sha256']==G19_PIN and qm['G20_manifest_sha256']==G20_PIN and
        all(m['source_sha']==a.SHA and all(m[k]==v for k,v in c.SCOPE.items()) for m in (pm,qm))
        and a.read(q/'G21_REPORT.json')['screen_pass'],'PARENT_SCOPE')
    files=c10.verify_c09(c10.c09.OUT)
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,c10.OUT,c10.c09.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'runner_sha256':a.sha(Path(__file__)),'G19_manifest':G19_PIN,'G21_manifest':G21_PIN,
        'scope':'Source PRE owner column strength, comparative hypotheses only. Not physical material assignment.',
        'quadrature_relative_screen':Q_SCREEN,'quadrature_screen_is_physical_authority':False,
        'rates':'Retained C08 regional proxies and Yu reference; not a global strain-rate field.',
        'pore_scenarios':'Zero and hydrostatic reference pore pressure, no actual fluid field.',
        **c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,'additional_builds':0,'additional_time_advance_years':0,
        'physical_acceptance':False,'material_assignments':0,**c.SCOPE}
    try:
        print('G22_SOURCE_AND_CATALOG',flush=True)
        rows,fields,atlas,domain,support,models,rates,gravity,water,g2,pre_pin=load(root,p,c10)
        a.write(out/'SOURCE_AND_MODELS.json',{'PRE_sha256':pre_pin,'fields':fields,'models':models,
            'rates_s_inv':rates,'gravity_m_s2':gravity,'reference_water_kg_m3':water})
        print('G22_GLOBAL_NATIVE_STRENGTH',flush=True)
        report['native'],chosen=global_runs(rows,fields,domain,support,models,rates,gravity,water,g2,out)
        print('G22_STRATIFIED_LAYERED_COMPARISON',len(chosen),flush=True)
        report['layered']=layered_runs(rows,fields,domain,support,chosen,models,rates,gravity,water,g2,out)
        a.write(out/'DOMAIN_DECISION_SHEET.json',{'domains':[{'domain_id':d,'physical_lithology':None,
            'native_candidate':None,'layered_candidate':None,'water_policy':None,'constitutive_admission':False}
            for d in range(1,7)],'global_assembly_authorized':False,
            'next_requirements':['Select explicit reduced-model constitutive hypotheses and applicability per support class.',
                'Qualify pressure, cold branch, rate and common exponent versus separate-exponent implementation.',
                'Resolve mixed nodal support and elementwise/sided assignment, not PRE owner overwrite.',
                'Native global coefficients currently scalar by layer: heterogeneous assignments need consumer implementation and parity.',
                'Close donor/sink, basal and contact authority independently; no physical T1.'],**c.SCOPE})
        report['screen_pass']=True
    except Exception as exc: report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for path,m,pin in ((p,pm,G19_PIN),(q,qm,G21_PIN)):
        a.need(c.inventory(path)==m['files'] and a.sha(path/'MANIFEST.json')==pin,'PARENT_MUTATION')
    a.need(c10.verify_c09(c10.c09.OUT)==files,'C09_MUTATION')
    status='G22_GLOBAL_CONSTITUTIVE_SENSITIVITY_PASS__DOMAIN_HYPOTHESIS_SELECTION_REQUIRED' if report['screen_pass'] else 'G22_GLOBAL_CONSTITUTIVE_SCREEN_BLOCKED'
    report.update(status=status,limitations=[
        'Numerical PRE owner profiles include mixed and excluded support; calculated strength is not their admission.',
        'C09 reduced pressure and stress conventions, not actual native nonlinear fields or experimental material validation.',
        'Native parameters and Yu analogues are counterfactual model families; oceanic quartzite comparisons are not oceanic lithology.',
        'Rate proxies, pore scenarios, common exponent and quadrature budget are diagnostics only.',
        'No probability, phase, water, composition, global assembly, event or physical T1 assigned.'])
    a.write(out/'G22_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G19_manifest_sha256':G19_PIN,
        'G21_manifest_sha256':G21_PIN,'files':c.inventory(out),**c.SCOPE})
    # Full per-stratum and layered summaries remain in archive.
    concise=dict(report)
    if 'layered' in concise:
        concise['layered']={k:v for k,v in report['layered'].items() if k!='domain_analogue_comparisons'}
    print(json.dumps(concise,indent=2,allow_nan=False),flush=True)
    print('G22_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True); print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
