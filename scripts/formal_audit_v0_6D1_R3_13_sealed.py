from __future__ import annotations
import argparse, json, hashlib, math, tempfile, sys
from pathlib import Path
from dataclasses import asdict
import numpy as np

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024), b''): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--run-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); root=a.root.resolve(); run=a.run_dir.resolve(); out=a.out.resolve(); sys.path.insert(0,str(root/'src'))
    from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313
    from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
    checks=[]
    def ck(name,cond,actual=None,expected=None): checks.append({'name':name,'pass':bool(cond),'actual':actual,'expected':expected})
    sp=run/'R3_13_LONGTERM_POST_CHA1_REASSEMBLY_SUMMARY.json'; jp=run/'WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.json'; npzp=jp.with_suffix('.npz')
    for p in (sp,jp,npzp): ck(f'file_exists::{p.name}',p.exists())
    summary=json.loads(sp.read_text()); meta=json.loads(jp.read_text()); rr=summary['run']; gov=summary['governance']; mg=meta['governance']
    ck('summary_schema',summary.get('schema')==r313.SUMMARY_SCHEMA,summary.get('schema'),r313.SUMMARY_SCHEMA)
    ck('summary_stage',summary.get('stage')==r313.STAGE,summary.get('stage'),r313.STAGE)
    ck('summary_mode',summary.get('mode')=='CANONICAL_46P0_TO_30P0',summary.get('mode'))
    ck('summary_verdict',summary.get('verdict')=='PASS_CANONICAL_POST_CHA1_46_TO_30_H0_LONGTERM_DIVERSIFICATION_REASSEMBLY__30MA_LATE_CENOZOIC_HANDOFF_CHECKPOINT_READY',summary.get('verdict'))
    for n,a0,e in [('start_age',rr['start_age_ma'],46.0),('end_age',rr['end_age_ma'],30.0)]: ck(n,abs(a0-e)<1e-12,a0,e)
    ck('biology_steps',rr['ordinary_biology_steps']==128,rr['ordinary_biology_steps'],128)
    ck('parent_species',rr['parent_species']==104,rr['parent_species'],104); ck('parent_components',rr['parent_components']==223,rr['parent_components'],223)
    ck('final_species',rr['final_species']==111,rr['final_species'],111); ck('final_components',rr['final_components']==219,rr['final_components'],219)
    ck('finite_population',math.isfinite(rr['final_total_population']),rr['final_total_population'])
    ck('summary_hash_expected',sha256(sp)=='2406b0c8fa374bcf4d77db368475e2da1a60368f93d42f8c0f8818d64944f3c9',sha256(sp))
    ck('checkpoint_json_hash',sha256(jp)==summary['checkpoint']['json_sha256'],sha256(jp),summary['checkpoint']['json_sha256'])
    ck('checkpoint_npz_hash',sha256(npzp)==summary['checkpoint']['npz_sha256'],sha256(npzp),summary['checkpoint']['npz_sha256'])
    ck('checkpoint_json_expected',sha256(jp)=='2c1cc49f04b7b489b6deab45caedf1cc3144a153d518e7646a4bc02ea235f869',sha256(jp))
    ck('checkpoint_npz_expected',sha256(npzp)=='2c576735a8268476cb5da91095a1bb549cf4edd1940ac539777144a156f66226',sha256(npzp))
    parent=r313.validate_parent_r312_authority(root); pst=parent['state']
    ck('parent_age',abs(pst.age_ma-46.0)<1e-12,pst.age_ma,46.0); ck('parent_species_loaded',len(set(pst.current_species))==104,len(set(pst.current_species)),104); ck('parent_components_loaded',len(pst.component_ids)==223,len(pst.component_ids),223)
    ck('parent_json_hash',parent['checkpoint_json_sha256']=='6189f16fd3d7b390ad33afb57eaa36fef0bdbcf7f1498fa7396d3d1f81843269',parent['checkpoint_json_sha256'])
    ck('parent_npz_hash',parent['checkpoint_npz_sha256']=='92b410ce3258c44ba0f4b911776628d880fbe5a5fe3be3b9b6fe13dc34973948',parent['checkpoint_npz_sha256'])
    ck('parent_summary_hash',parent['summary_sha256']=='404c43c80af5f10ff1d00ad0cfc51f21abbe3e566e3d040e4faa2e84d33a6230',parent['summary_sha256'])
    ck('parent_sealed',str(parent['seal_verdict']).endswith('46MA_RESTART_BOUNDARY_SEALED'),parent['seal_verdict'])
    ck('checkpoint_schema',meta['schema']==r313.SCHEMA,meta['schema'],r313.SCHEMA); ck('checkpoint_stage',meta['stage']==r313.STAGE,meta['stage']); ck('parent_stage',meta['parent_stage']==r313.PARENT_STAGE,meta['parent_stage'],r313.PARENT_STAGE)
    ck('checkpoint_age',abs(meta['age_ma']-30.0)<1e-12,meta['age_ma'],30.0); ck('event_side',meta['event_side']=='POST_CHA1_36MY_LONG_TERM_REASSEMBLY',meta['event_side']); ck('elapsed',abs(meta['elapsed_year']-180_000_000.0)<1e-6,meta['elapsed_year'],180_000_000.0); ck('npz_filename',meta['npz_file']==npzp.name,meta['npz_file'],npzp.name)
    st=r313.load_checkpoint(jp,smoke=False)
    rowsj=json.loads((root/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); rows=rowsj['species'] if isinstance(rowsj,dict) and 'species' in rowsj else rowsj
    cfg=r313.R313Config(); inv=r313.invariant_report(st,rows,cfg)
    ck('loaded_age',abs(st.age_ma-30.0)<1e-12,st.age_ma,30.0); ck('loaded_elapsed',abs(st.elapsed_year-180_000_000.0)<1e-6,st.elapsed_year); ck('loaded_components',len(st.component_ids)==219,len(st.component_ids),219); ck('loaded_species',len(set(st.current_species))==111,len(set(st.current_species)),111)
    ck('population_sum',abs(float(st.pop.sum())-rr['final_total_population'])<1e-9,float(st.pop.sum()),rr['final_total_population']); ck('population_nonnegative',float(st.pop.min())>=-1e-14,float(st.pop.min())); ck('inaccessible_zero',abs(inv['population_on_inaccessible_cells'])<=1e-12,inv['population_on_inaccessible_cells'])
    for k in ('q_max','q_median','q_headroom','s_symmetry_max_abs','s_diagonal_max_abs','s_min'): ck(f'invariant_recomputed::{k}',abs(inv[k]-rr['invariants'][k])<2e-12,inv[k],rr['invariants'][k])
    ck('q_below_ceiling',inv['q_max']<=0.08+1e-12,inv['q_max'],0.08); ck('q_headroom_positive',inv['q_headroom']>0,inv['q_headroom']); ck('S_symmetric',inv['s_symmetry_max_abs']<=2e-12,inv['s_symmetry_max_abs']); ck('S_diag_zero',inv['s_diagonal_max_abs']<=2e-12,inv['s_diagonal_max_abs']); ck('S_nonnegative',inv['s_min']>=-2e-12,inv['s_min'])
    z=np.load(npzp,allow_pickle=False); shapes={'guild':(219,),'population':(219,90,180),'trait':(219,3),'va':(219,3),'generation_time':(219,),'current_accessible':(90,180),'reduced_va_within':(219,3),'reduced_ancestry_covariance':(219,3),'reduced_neutral_segregation_potential':(219,219,3),'reduced_adaptive_coordinate':(219,3),'lat':(90,),'lon':(180,)}
    for k,s in shapes.items():
        ck(f'npz_key::{k}',k in z.files)
        if k in z.files: ck(f'npz_shape::{k}',tuple(z[k].shape)==s,tuple(z[k].shape),s); ck(f'npz_finite::{k}',bool(np.isfinite(z[k]).all()))
    guildset=sorted(set(z['guild'].astype(int).tolist())); ck('guilds_exact_1_to_5',guildset==[1,2,3,4,5],guildset,[1,2,3,4,5]); ck('guild6_absent',6 not in guildset,guildset)
    before=r313.event_counts(pst); after=r313.event_counts(st); delta=r313.delta_event_counts(pst,st)
    for k,v in rr['event_counts_before'].items(): ck(f'events_before::{k}',before[k]==v,before[k],v)
    for k,v in rr['event_counts_after'].items(): ck(f'events_after::{k}',after[k]==v,after[k],v)
    for k,v in rr['event_counts_delta'].items(): ck(f'events_delta::{k}',delta[k]==v,delta[k],v)
    ck('speciation_7',delta['speciation']==7,delta['speciation'],7); ck('ordinary_extinction_0',delta['ordinary_background_extinction']==0,delta['ordinary_background_extinction'],0); ck('no_new_cha1',delta['CHA1_species_extinction']==0 and delta['CHA1_high_resolution_event_bridge_complete']==0,delta); ck('no_new_thaw',delta['post_CHA1_ordinary_lifecycle_thaw']==0,delta['post_CHA1_ordinary_lifecycle_thaw'])
    ck('peak_q_expected',abs(rr['peak_q_recorded']-0.047307019500333794)<2e-15,rr['peak_q_recorded']); ck('peak_unclipped_equal',abs(rr['peak_unclipped_q_recorded']-rr['peak_q_recorded'])<2e-15,rr['peak_unclipped_q_recorded'],rr['peak_q_recorded']); ck('clipping_steps_zero',rr['clipping_steps']==0,rr['clipping_steps'],0); ck('clipping_contacts_zero',rr['clipping_contacts']==0,rr['clipping_contacts'],0)
    re=rr['ecological_reassembly']; ck('reassembly_descriptive',re['descriptive_not_acceptance_target'] is True); ck('active_guilds_start_5',re['active_guild_count_at_46Ma']==5,re['active_guild_count_at_46Ma'],5); ck('active_guilds_end_5',re['active_guild_count_at_end']==5,re['active_guild_count_at_end'],5); ck('guild6_absent_start',re['guilds_absent_at_46Ma']==[6],re['guilds_absent_at_46Ma']); ck('guild6_absent_end',re['guilds_absent_at_end']==[6],re['guilds_absent_at_end']); ck('crossguild_unauthorized',re['cross_guild_recreation_authorized'] is False)
    expected_guild_end={'1':51,'2':1,'3':7,'4':45,'5':7,'6':0}
    for g,v in expected_guild_end.items(): ck(f'guild_end_species::{g}',re['guilds'][g]['species_at_end']==v,re['guilds'][g]['species_at_end'],v)
    ck('root_lineages_preserved',re['root_lineages_at_end']['active_root_lineages']==55,re['root_lineages_at_end']['active_root_lineages'],55)
    so=rr['speciation_origin_diagnostic']; ck('founder_candidates_2',so['founder_candidates_at_46Ma']==2,so['founder_candidates_at_46Ma'],2); ck('carryover_zero',so['matched_46Ma_founder_carryover_speciations']==0,so['matched_46Ma_founder_carryover_speciations'],0); ck('unmatched_7',so['not_matched_to_46Ma_founder_state']==7,so['not_matched_to_46Ma_founder_state'],7); ck('origin_rows_7',len(so['rows'])==7,len(so['rows']),7); ck('all_origin_unmatched',all(r['classification']=='NOT_MATCHED_TO_R312_BOUNDARY_FOUNDER_STATE' for r in so['rows']))
    ages=[r['age_ma'] for r in rr['speciation_chronology']]; ck('speciation_ages_exact',ages==[43.0,42.5,40.5,40.0,38.0,35.5,30.5],ages); ck('no_extinction_chronology',rr['ordinary_extinction_chronology']==[],rr['ordinary_extinction_chronology'])
    h=rr['late_cenozoic_30ma_environment_handoff']; ck('handoff_exact',h['environmental_endpoint_identity_exact'] is True); ck('handoff_age_30',h['age_ma']==30.0,h['age_ma'],30.0); ck('late_provider_not_activated',h['biology_switched_in_r313'] is False)
    for f,d in h['fields'].items(): ck(f'handoff::{f}',d['exact'] is True and d['max_abs_error']==0.0,d)
    ck('config_exact',meta['config']==asdict(cfg),'exact compare')
    for k,v in {'cha1_already_applied':True,'cha1_reapplied':False,'lifecycle_thaw_reapplied':False,'deep_biological_coupling':False,'ordinary_lifecycle_continued':True,'richness_target_used':False,'guild_target_used':False,'positive_diversification_required_for_pass':False,'cross_guild_transition_operator_activated':False,'late_cenozoic_provider_activated_inside_stage':False,'late_cenozoic_30ma_boundary_identity_required':True,'production_r37i_r38_runtime_used':True,'mu_changed':False,'b_changed':False,'q_ceiling_changed':False,'K_center_reinterpreted_as_physical_constant':False}.items(): ck(f'summary_governance::{k}',gov.get(k) is v,gov.get(k),v)
    for k,v in {'cha1_already_applied':True,'cha1_reapplied':False,'post_cha1_lifecycle_thaw_reapplied':False,'deep_biological_coupling':False,'ordinary_lifecycle_continued':True,'post_cha1_radiation_multiplier_used':False,'richness_target_used':False,'guild_target_used':False,'cross_guild_transition_operator_activated':False,'late_cenozoic_provider_activated_inside_stage':False,'r37i_r38_production_runtime_reused':True,'mu_changed':False,'b_changed':False,'q_ceiling_changed':False,'scalar_k_physical_constant_authorized':False}.items(): ck(f'checkpoint_governance::{k}',mg.get(k) is v,mg.get(k),v)
    # independent environment handoff recomputation
    a1=np.load(root/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False); hh=r313.validate_30ma_environment_handoff(a1,cfg); ck('handoff_recomputed_exact',hh['environmental_endpoint_identity_exact'] is True)
    for f,d in hh['fields'].items(): ck(f'handoff_recomputed::{f}',d['exact'] is True and d['max_abs_error']==0.0,d)
    # independent load-save-load roundtrip
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); parent_public={k:v for k,v in parent.items() if k!='state'}; cp=r313.save_checkpoint(st,td,parent_public,cfg,rr,smoke=False); st2=r313.load_checkpoint(Path(cp['json']),smoke=False); comp=r38.compare_runtime_states(st,st2)
    ck('roundtrip_equivalent',comp['equivalent'] is True,comp['equivalent'],True)
    for k,v in comp['arrays'].items(): ck(f'roundtrip_array::{k}',v['same'] and v['max_abs_error']==0.0,v)
    for k,v in comp['reduced_state'].items(): ck(f'roundtrip_reduced::{k}',v['same'] and v['max_abs_error']==0.0,v)
    for k,v in comp['exact_fields'].items(): ck(f'roundtrip_exact::{k}',v is True,v,True)
    for k,v in comp['scalar_abs_errors'].items(): ck(f'roundtrip_scalar::{k}',v==0.0,v,0.0)
    passed=sum(c['pass'] for c in checks); total=len(checks); verdict='PASS_R313_CANONICAL_POST_CHA1_46_TO_30_H0_LONGTERM_DIVERSIFICATION_REASSEMBLY__30MA_LATE_CENOZOIC_HANDOFF_BOUNDARY_SEALED' if passed==total else 'FAIL_R313_SEALED_AUDIT'
    result={'schema':'ARCANA_R313_SEALED_POST_RUN_AUDIT_V1','stage':'v0.6D1-R3.13','verdict':verdict,'checks_passed':passed,'checks_total':total,'all_pass':passed==total,'artifact_hashes':{'summary':sha256(sp),'checkpoint_json':sha256(jp),'checkpoint_npz':sha256(npzp)},'boundary':{'age_ma':30.0,'event_side':'POST_CHA1_36MY_LONG_TERM_REASSEMBLY','species':111,'components':219,'population':rr['final_total_population']},'telemetry':{'peak_q':rr['peak_q_recorded'],'final_q_max':inv['q_max'],'final_q_headroom':inv['q_headroom'],'clipping_steps':rr['clipping_steps'],'clipping_contacts':rr['clipping_contacts']},'ecological_reassembly':re,'speciation_origin':so,'late_cenozoic_handoff':hh,'checks':checks}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps({'verdict':verdict,'checks':f'{passed}/{total}','out':str(out)},indent=2)); return 0 if passed==total else 2
if __name__=='__main__': raise SystemExit(main())
