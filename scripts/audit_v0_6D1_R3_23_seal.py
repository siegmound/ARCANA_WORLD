from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

STAGE='v0.6D1-R3.23'
PASS='PASS_R323_COMPARATIVE_FUNCTIONAL_PRIOR_CALIBRATION_ANCESTRAL_ENSEMBLE_AND_H0_CONDITIONED_PHYLOGENETIC_FUNCTIONAL_REPLAY_SEALED'
PARENT='PASS_R322_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_TRADEOFF_GOVERNANCE_AND_REPLAY_INTERFACE_SEALED'
R319J='658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71'
R319N='f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406'
EXPECTED={
'R3_23_AUDIT.md':(391,'0a17719bf5b0079b9f30c1a147ecbe3c3732e1351742f936f4f41d5619ae48c0'),
'R3_23_COMPARATIVE_CALIBRATION_AUTHORITY.json':(33415,'f805ef379c2b93734e0ec98a76b06aad2a92baf6a25d6576b23f16bbfb11cc82'),
'R3_23_INTEGRATED_AUDIT.json':(4160,'d82ff13f73075099b02e2a378cae63c38a9c108dbdd0e4f362176a7a6ee2baf4'),
'R3_23_OUTPUT_MANIFEST.json':(1205,'cdd613742f5d3c1d8d98e0654f63c9b018a75fe962085aeb54b4412e97f9de97'),
'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz':(10201608,'d827da2b3cc283b8dcf1d65dfd430814c999229e14babba26483dad025685606'),
'R3_23_PRESENT_FUNCTIONAL_SUMMARY.json':(1099921,'1b944edfc4bb648a8356d252d5f9628a57e38a1664c00be00e5c7a7bdca6b765'),
'R3_23_REPLAY_PROVENANCE.json':(13598,'e66130e452086c8ecf0515d279713a2f4fd213b107af5856e61bf65d9855f07f'),
'R3_23_ROOT_ANCESTRAL_PRIOR_SUMMARY.json':(104045,'720880ccbd7b35e88d1fdaf8cc715a0f1c88a3506bf61a42a4b6e0d713e5202d')}

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def js(p:Path):
    return json.loads(p.read_text(encoding='utf-8'))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    a=ap.parse_args()
    root=Path(a.root)
    out=root/'outputs'/'v0_6D1_R3_23'
    parent_seal=root/'outputs'/'v0_6D1_R3_22_SEAL'
    seal=root/'outputs'/'v0_6D1_R3_23_SEAL'
    checks=[]
    def ck(name, cond, detail=None):
        checks.append({'name':name,'pass':bool(cond),'detail':detail})

    ck('output_dir_exists', out.is_dir(), str(out))
    actual={p.name for p in out.iterdir() if p.is_file()} if out.is_dir() else set()
    ck('exact_output_file_set', actual==set(EXPECTED), {'missing':sorted(set(EXPECTED)-actual),'unexpected':sorted(actual-set(EXPECTED))})
    for n,(sz,h) in EXPECTED.items():
        p=out/n
        ok=p.is_file() and p.stat().st_size==sz and sha(p)==h
        ck('exact_binding::'+n, ok, {'bytes':p.stat().st_size if p.exists() else None, 'sha256':sha(p) if p.exists() else None})

    if not out.is_dir() or not set(EXPECTED)<=actual:
        raise SystemExit(2)

    # Parent R3.22 authority chain.
    pa=parent_seal/'R3_22_FINAL_SEAL_AUDIT.json'
    pm=parent_seal/'R3_22_FINAL_SEAL_MANIFEST.json'
    ck('parent_seal_audit_present', pa.is_file(), str(pa))
    ck('parent_seal_manifest_present', pm.is_file(), str(pm))
    if pa.is_file() and pm.is_file():
        paj=js(pa); pmj=js(pm)
        ck('parent_stage_exact', paj.get('stage')=='v0.6D1-R3.22')
        ck('parent_status_exact', paj.get('status')==PARENT)
        ck('parent_74_of_74', paj.get('checks_passed')==74 and paj.get('checks_total')==74 and paj.get('checks_failed')==0)
        files=pmj.get('files',{})
        parent_manifest_ok=True
        for name,meta in files.items():
            p=parent_seal/name
            parent_manifest_ok &= p.is_file() and p.stat().st_size==meta.get('bytes') and sha(p)==meta.get('sha256')
        ck('parent_seal_manifest_hash_size_closure', parent_manifest_ok, files)
    else:
        ck('parent_stage_exact', False)
        ck('parent_status_exact', False)
        ck('parent_74_of_74', False)
        ck('parent_seal_manifest_hash_size_closure', False)

    aud=js(out/'R3_23_INTEGRATED_AUDIT.json')
    prov=js(out/'R3_23_REPLAY_PROVENANCE.json')
    summ=js(out/'R3_23_PRESENT_FUNCTIONAL_SUMMARY.json')
    cal=js(out/'R3_23_COMPARATIVE_CALIBRATION_AUTHORITY.json')
    roots=js(out/'R3_23_ROOT_ANCESTRAL_PRIOR_SUMMARY.json')
    man=js(out/'R3_23_OUTPUT_MANIFEST.json')

    ck('candidate_36_of_36', aud.get('checks_passed')==36 and aud.get('checks_total')==36 and aud.get('checks_failed')==0 and len(aud.get('checks',[]))==36 and all(x.get('pass') for x in aud.get('checks',[])))
    ck('parent_r322_sealed_in_provenance', prov.get('parent_r322_seal_status')==PARENT)
    ck('source_checkpoint_exact', prov.get('source_checkpoint')=={'json_sha256':R319J,'npz_sha256':R319N})
    ck('governance_source_checkpoint_exact', summ.get('governance',{}).get('source_checkpoint')=={'json_sha256':R319J,'npz_sha256':R319N})
    ck('counts_exact', summ.get('governance',{}).get('present_species')==134 and summ.get('governance',{}).get('present_components')==295 and summ.get('governance',{}).get('historical_species')==348 and summ.get('governance',{}).get('historical_events')==2925)
    ck('ensemble_design_exact', summ.get('ensemble',{}).get('members')==96 and summ.get('ensemble',{}).get('replicates_per_rate_regime')==32 and summ.get('ensemble',{}).get('rate_regimes')==['CONSERVATIVE','BASELINE','LABILE'] and summ.get('ensemble',{}).get('seed')==230823)
    gov=summ.get('governance',{})
    ck('no_human_target', gov.get('human_target') is False and gov.get('human_readiness_ranking_executed') is False)
    ck('deep_off', gov.get('deep_biological_coupling') is False)
    ck('h0_cha2_immutable', gov.get('h0_mutated') is False and gov.get('cha2_mutated') is False)
    ck('unsupported_quantgen_not_materialized', all(gov.get(k) is False for k in ['functional_va_materialized','functional_gcov_materialized','functional_plasticity_beta_materialized','functional_applicability_code_materialized']))
    ck('ensemble_variance_semantics', gov.get('macroevolutionary_ensemble_variance_is_not_additive_genetic_variance') is True)
    ck('derived_semantics_conditional', 'CONDITIONAL_POTENTIAL' in str(gov.get('derived_capability_semantics')))
    ck('summary_row_counts', len(summ.get('species',[]))==134 and len(summ.get('components',[]))==295)
    ck('all_human_readiness_null', all(x.get('human_readiness_score') is None for x in summ.get('species',[])))
    ck('root_prior_count', roots.get('root_count')==120 and len(roots.get('roots',[]))==120)
    ck('root_prior_dimensions', all(len(r.get('prior_center',[]))==31 and r.get('prior_sd')==0.72 for r in roots.get('roots',[])))
    ck('calibration_31_traits', len(cal.get('trait_calibration',[]))==31)
    ck('calibration_no_human_anchor', cal.get('human_anchor') is False and cal.get('deep_biological_coupling') is False)
    ck('calibration_sources_multitaxon', len(cal.get('evidence_sources',{}))>=8 and all(len(r.get('empirical_source_set',[]))>=2 for r in cal.get('trait_calibration',[])))
    ck('manifest_candidate_binding', man.get('stage')==STAGE and man.get('status')=='CANDIDATE_OUTPUT_MANIFEST')
    manifest_ok=True
    for name,meta in man.get('files',{}).items():
        p=out/name
        manifest_ok &= p.is_file() and p.stat().st_size==meta.get('bytes') and sha(p)==meta.get('sha256')
    ck('candidate_manifest_hash_size_closure', manifest_ok, man.get('files',{}))

    # Independent numerical audit.
    z=np.load(out/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz', allow_pickle=False)
    expected_keys={'component_ids','species_ids','trait_ids','rate_regime','functional_mean_z_ensemble','species_mean_z_ensemble','tool_use_potential_ensemble','environmental_problem_solving_ensemble'}
    ck('npz_keys_exact', set(z.files)==expected_keys, sorted(z.files))
    F=z['functional_mean_z_ensemble']; S=z['species_mean_z_ensemble']; T=z['tool_use_potential_ensemble']; Q=z['environmental_problem_solving_ensemble']; rr=z['rate_regime']
    ck('npz_shapes_exact', F.shape==(96,295,31) and S.shape==(96,134,31) and T.shape==(96,295) and Q.shape==(96,295), {'F':list(F.shape),'S':list(S.shape),'T':list(T.shape),'Q':list(Q.shape)})
    ck('all_numeric_finite', all(np.all(np.isfinite(x)) for x in [F,S,T,Q]))
    ck('latent_clip_respected', float(np.max(np.abs(F)))<=4.0+1e-12 and float(np.max(np.abs(S)))<=4.0+1e-12, {'F_abs_max':float(np.max(np.abs(F))),'S_abs_max':float(np.max(np.abs(S)))})
    ck('derived_bounded_0_1', float(T.min())>=0 and float(T.max())<=1 and float(Q.min())>=0 and float(Q.max())<=1, {'T':[float(T.min()),float(T.max())],'Q':[float(Q.min()),float(Q.max())]})
    ck('rate_regime_order_exact', list(rr[:32])==['CONSERVATIVE']*32 and list(rr[32:64])==['BASELINE']*32 and list(rr[64:])==['LABILE']*32)
    ck('component_order_exact', list(map(str,z['component_ids']))==list(map(str,prov.get('component_order',[]))))
    ck('species_order_exact', list(map(str,z['species_ids']))==list(map(str,prov.get('present_species_order',[]))))
    ck('trait_count_and_unique', len(z['trait_ids'])==31 and len(set(map(str,z['trait_ids'])))==31)

    comps=summ['components']; comp_ok=True; max_comp=0.0; max_tool=0.0; max_prob=0.0
    for i,row in enumerate(comps):
        comp_ok &= row['component_id']==str(z['component_ids'][i])
        d=float(np.max(np.abs(np.asarray(row['trait_mean_z'],dtype=float)-F[:,i,:].mean(0))))
        max_comp=max(max_comp,d)
        d2=abs(float(row['tool_use_potential']['mean'])-float(T[:,i].mean()))
        d3=abs(float(row['environmental_problem_solving']['mean'])-float(Q[:,i].mean()))
        max_tool=max(max_tool,d2); max_prob=max(max_prob,d3)
        comp_ok &= d<=1e-12 and d2<=1e-12 and d3<=1e-12
    ck('component_summary_recomputed', comp_ok, {'max_trait_mean_diff':max_comp,'max_tool_mean_diff':max_tool,'max_problem_mean_diff':max_prob})

    species=summ['species']; sid_to_i={str(s):i for i,s in enumerate(z['species_ids'])}; comp_by_sid={}
    for i,row in enumerate(comps):
        comp_by_sid.setdefault(str(row['species_id']),[]).append((i,float(row['population_total'])))
    sp_ok=True; max_species_ensemble=0.0; max_species_summary=0.0
    for row in species:
        sid=str(row['species_id']); si=sid_to_i[sid]; members=comp_by_sid[sid]
        inds=[i for i,w in members]; ws=np.asarray([w for i,w in members],dtype=float); ws=ws/ws.sum()
        rec=np.tensordot(F[:,inds,:],ws,axes=([1],[0]))
        d=float(np.max(np.abs(rec-S[:,si,:]))); d2=float(np.max(np.abs(np.asarray(row['trait_mean_z'],dtype=float)-S[:,si,:].mean(0))))
        max_species_ensemble=max(max_species_ensemble,d); max_species_summary=max(max_species_summary,d2)
        sp_ok &= d<=2e-12 and d2<=2e-12
    ck('species_population_weighted_ensemble_recomputed', sp_ok, {'max_ensemble_diff':max_species_ensemble,'max_summary_diff':max_species_summary})

    failed=[x for x in checks if not x['pass']]
    report={
        'stage':STAGE,
        'audit':'FINAL_SEAL_SINGLE_STAGE_OUTPUT_AUTHORITY_CLOSURE_FIX1',
        'status':PASS if not failed else 'FAIL_R323_FINAL_SEAL_AUDIT',
        'verdict':'SEALED' if not failed else 'FAIL_CLOSED',
        'checks_passed':len(checks)-len(failed),
        'checks_total':len(checks),
        'checks_failed':len(failed),
        'source_checkpoint':{'json_sha256':R319J,'npz_sha256':R319N},
        'bound_candidate_manifest_sha256':EXPECTED['R3_23_OUTPUT_MANIFEST.json'][1],
        'summary':{'ensemble_members':96,'present_species':134,'present_components':295,'primitive_traits':31,'derived_capabilities':2,'human_target':False,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False},
        'checks':checks,
    }
    seal.mkdir(parents=True, exist_ok=True)
    apath=seal/'R3_23_FINAL_SEAL_AUDIT.json'; apath.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    md=seal/'R3_23_FINAL_SEAL_AUDIT.md'; md.write_text(f"# R3.23 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8')
    files={}
    for p in [apath,md]: files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
    m={'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':files}
    (seal/'R3_23_FINAL_SEAL_MANIFEST.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if not failed else 1

if __name__=='__main__':
    raise SystemExit(main())
