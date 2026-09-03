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
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a=ap.parse_args(); root=a.root.resolve(); run=a.run_dir.resolve(); out=a.out.resolve()
    sys.path.insert(0, str(root/'src'))
    from arcana_worldsim.scientific_engines import r312_postcha1_diversity_recovery as r312
    from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38

    checks=[]
    def ck(name, cond, actual=None, expected=None):
        checks.append({'name':name,'pass':bool(cond),'actual':actual,'expected':expected})

    sp=run/'R3_12_POST_CHA1_DIVERSITY_RECOVERY_SUMMARY.json'
    jp=run/'WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12.json'
    npzp=run/'WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12.npz'
    for p in (sp,jp,npzp): ck(f'file_exists::{p.name}',p.exists())
    summary=json.loads(sp.read_text()); meta=json.loads(jp.read_text())
    runr=summary['run']; gov=summary['governance']; m_gov=meta['governance']

    ck('summary_schema',summary.get('schema')==r312.SUMMARY_SCHEMA,summary.get('schema'),r312.SUMMARY_SCHEMA)
    ck('summary_stage',summary.get('stage')==r312.STAGE,summary.get('stage'),r312.STAGE)
    ck('summary_mode',summary.get('mode')=='CANONICAL_61P0_TO_46P0',summary.get('mode'),'CANONICAL_61P0_TO_46P0')
    ck('summary_verdict',summary.get('verdict')=='PASS_CANONICAL_POST_CHA1_61_TO_46_H0_DIVERSITY_RECOVERY_OBSERVATION__46MA_CHECKPOINT_READY',summary.get('verdict'))
    ck('run_start_age',abs(runr['start_age_ma']-61.0)<1e-12,runr['start_age_ma'],61.0)
    ck('run_end_age',abs(runr['end_age_ma']-46.0)<1e-12,runr['end_age_ma'],46.0)
    ck('biology_steps',runr['ordinary_biology_steps']==120,runr['ordinary_biology_steps'],120)
    ck('parent_species',runr['parent_species']==95,runr['parent_species'],95)
    ck('parent_components',runr['parent_components']==236,runr['parent_components'],236)
    ck('final_species',runr['final_species']==104,runr['final_species'],104)
    ck('final_components',runr['final_components']==223,runr['final_components'],223)
    ck('finite_final_population',math.isfinite(runr['final_total_population']),runr['final_total_population'])

    # artifact hashes
    ck('checkpoint_json_hash',sha256(jp)==summary['checkpoint']['json_sha256'],sha256(jp),summary['checkpoint']['json_sha256'])
    ck('checkpoint_npz_hash',sha256(npzp)==summary['checkpoint']['npz_sha256'],sha256(npzp),summary['checkpoint']['npz_sha256'])
    ck('checkpoint_json_hash_expected',sha256(jp)=='6189f16fd3d7b390ad33afb57eaa36fef0bdbcf7f1498fa7396d3d1f81843269',sha256(jp))
    ck('checkpoint_npz_hash_expected',sha256(npzp)=='92b410ce3258c44ba0f4b911776628d880fbe5a5fe3be3b9b6fe13dc34973948',sha256(npzp))

    # parent authority independently validates hashes + chronology
    parent=r312.validate_parent_r311_authority(root)
    ck('parent_age',abs(parent['state'].age_ma-61.0)<1e-12,parent['state'].age_ma,61.0)
    ck('parent_json_hash',parent['checkpoint_json_sha256']=='bdf75d08bd39181dee3331f91b1dd6864ab8e0c1e88c94eed7813d148aebda3b',parent['checkpoint_json_sha256'])
    ck('parent_npz_hash',parent['checkpoint_npz_sha256']=='4f4582ca7f83926941f7224033a83356b2f5df196dcb8d3dbafae2e9b16e987c',parent['checkpoint_npz_sha256'])
    ck('parent_summary_hash',parent['summary_sha256']=='b8194132711925d7ea2f67d0bf9bd7d9ad995ae37bef2f18df6c2fab49524bbd',parent['summary_sha256'])
    ck('parent_seal_verdict',str(parent['seal_verdict']).endswith('61MA_RESTART_BOUNDARY_SEALED'),parent['seal_verdict'])

    # checkpoint metadata / load
    ck('checkpoint_schema',meta['schema']==r312.SCHEMA,meta['schema'],r312.SCHEMA)
    ck('checkpoint_stage',meta['stage']==r312.STAGE,meta['stage'])
    ck('checkpoint_parent_stage',meta['parent_stage']==r312.PARENT_STAGE,meta['parent_stage'],r312.PARENT_STAGE)
    ck('checkpoint_age',abs(meta['age_ma']-46.0)<1e-12,meta['age_ma'],46.0)
    ck('checkpoint_event_side',meta['event_side']=='POST_CHA1_20MY_DIVERSITY_RECOVERY',meta['event_side'])
    ck('checkpoint_elapsed',abs(meta['elapsed_year']-164_000_000.0)<1e-6,meta['elapsed_year'],164_000_000.0)
    ck('npz_filename',meta['npz_file']==npzp.name,meta['npz_file'],npzp.name)

    st=r312.load_diversity_checkpoint(jp, smoke=False)
    rowsj=json.loads((root/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text())
    rows=rowsj['species'] if isinstance(rowsj,dict) and 'species' in rowsj else rowsj
    cfg=r312.R312Config()
    inv=r312.invariant_report(st, rows, cfg)
    ck('loaded_age',abs(st.age_ma-46.0)<1e-12,st.age_ma,46.0)
    ck('loaded_elapsed',abs(st.elapsed_year-164_000_000.0)<1e-6,st.elapsed_year)
    ck('loaded_components',len(st.component_ids)==223,len(st.component_ids),223)
    ck('loaded_species_unique',len(set(st.current_species))==104,len(set(st.current_species)),104)
    ck('loaded_population_sum',abs(float(st.pop.sum())-runr['final_total_population'])<1e-9,float(st.pop.sum()),runr['final_total_population'])
    ck('population_nonnegative',float(st.pop.min())>=-1e-14,float(st.pop.min()),'>=-1e-14')
    ck('population_inaccessible_zero',abs(inv['population_on_inaccessible_cells'])<=1e-12,inv['population_on_inaccessible_cells'],0.0)
    ck('q_max_recomputed',abs(inv['q_max']-runr['invariants']['q_max'])<2e-12,inv['q_max'],runr['invariants']['q_max'])
    ck('q_median_recomputed',abs(inv['q_median']-runr['invariants']['q_median'])<2e-12,inv['q_median'],runr['invariants']['q_median'])
    ck('q_below_ceiling',inv['q_max']<=0.08+1e-12,inv['q_max'],0.08)
    ck('q_positive_headroom',inv['q_headroom']>0,inv['q_headroom'])
    ck('S_symmetry',inv['s_symmetry_max_abs']<=2e-12,inv['s_symmetry_max_abs'])
    ck('S_diagonal_zero',inv['s_diagonal_max_abs']<=2e-12,inv['s_diagonal_max_abs'])
    ck('S_nonnegative',inv['s_min']>=-2e-12,inv['s_min'])

    # npz arrays
    z=np.load(npzp,allow_pickle=False)
    expected_shapes={
        'guild':(223,), 'population':(223,90,180), 'trait':(223,3), 'va':(223,3),
        'generation_time':(223,), 'current_accessible':(90,180), 'reduced_va_within':(223,3),
        'reduced_ancestry_covariance':(223,3), 'reduced_neutral_segregation_potential':(223,223,3),
        'reduced_adaptive_coordinate':(223,3), 'lat':(90,), 'lon':(180,)
    }
    for k,shape in expected_shapes.items():
        ck(f'npz_key::{k}',k in z.files)
        if k in z.files:
            arr=z[k]; ck(f'npz_shape::{k}',tuple(arr.shape)==shape,tuple(arr.shape),shape)
            ck(f'npz_finite::{k}',bool(np.isfinite(arr).all()))
    ck('guild6_absent_final',6 not in set(z['guild'].astype(int).tolist()),sorted(set(z['guild'].astype(int).tolist())),[1,2,3,4,5])

    # events independently recount
    before=r312.event_counts(parent['state']); after=r312.event_counts(st); delta=r312.delta_event_counts(parent['state'],st)
    for k,v in runr['event_counts_before'].items(): ck(f'events_before::{k}',before[k]==v,before[k],v)
    for k,v in runr['event_counts_after'].items(): ck(f'events_after::{k}',after[k]==v,after[k],v)
    for k,v in runr['event_counts_delta'].items(): ck(f'events_delta::{k}',delta[k]==v,delta[k],v)
    ck('no_new_CHA1_species_extinction',delta['CHA1_species_extinction']==0,delta['CHA1_species_extinction'],0)
    ck('exactly_one_historical_CHA1_bridge',after['CHA1_high_resolution_event_bridge_complete']==1,after['CHA1_high_resolution_event_bridge_complete'],1)
    ck('no_second_CHA1_bridge',delta['CHA1_high_resolution_event_bridge_complete']==0,delta['CHA1_high_resolution_event_bridge_complete'],0)
    ck('exactly_one_historical_thaw',after['post_CHA1_ordinary_lifecycle_thaw']==1,after['post_CHA1_ordinary_lifecycle_thaw'],1)
    ck('no_second_thaw',delta['post_CHA1_ordinary_lifecycle_thaw']==0,delta['post_CHA1_ordinary_lifecycle_thaw'],0)
    ck('speciation_count_11',delta['speciation']==11,delta['speciation'],11)
    ck('ordinary_extinction_count_2',delta['ordinary_background_extinction']==2,delta['ordinary_background_extinction'],2)

    # telemetry
    ck('peak_q',abs(runr['peak_q_recorded']-0.04694482744771825)<2e-15,runr['peak_q_recorded'])
    ck('peak_unclipped_q',abs(runr['peak_unclipped_q_recorded']-runr['peak_q_recorded'])<2e-15,runr['peak_unclipped_q_recorded'],runr['peak_q_recorded'])
    ck('clipping_steps_zero',runr['clipping_steps']==0,runr['clipping_steps'],0)
    ck('clipping_contacts_zero',runr['clipping_contacts']==0,runr['clipping_contacts'],0)

    # diversity descriptive metrics
    dr=runr['diversity_recovery']
    ck('recovery_not_target',dr['reference_only_not_acceptance_targets'] is True)
    ck('pre_CHA1_reference_305',dr['pre_CHA1_species_reference']==305,dr['pre_CHA1_species_reference'],305)
    ck('post_CHA1_reference_93',dr['post_CHA1_500ky_species_reference']==93,dr['post_CHA1_500ky_species_reference'],93)
    ck('R311_reference_95',dr['R3_11_61Ma_species']==95,dr['R3_11_61Ma_species'],95)
    ck('final_reference_104',dr['final_species']==104,dr['final_species'],104)
    ck('net_since_immediate_11',dr['net_species_recovered_since_post_CHA1_500ky']==11,dr['net_species_recovered_since_post_CHA1_500ky'],11)
    ck('net_since_R311_9',dr['net_species_change_since_R3_11_61Ma']==9,dr['net_species_change_since_R3_11_61Ma'],9)
    ck('fraction_direct_loss_recovered',abs(dr['fraction_of_direct_CHA1_species_loss_recovered']-11/212)<1e-15,dr['fraction_of_direct_CHA1_species_loss_recovered'],11/212)
    ck('fraction_pre_CHA1_present',abs(dr['fraction_of_pre_CHA1_species_richness_present']-104/305)<1e-15,dr['fraction_of_pre_CHA1_species_richness_present'],104/305)
    final_guild={k:int(v['species_at_end']) for k,v in dr['guild_richness'].items()}
    ck('guild_final_sum',sum(final_guild.values())==104,sum(final_guild.values()),104)
    expected_g={'1':50,'2':1,'3':6,'4':42,'5':5,'6':0}
    for g,v in expected_g.items(): ck(f'guild_final::{g}',final_guild.get(g)==v,final_guild.get(g),v)
    ck('root_lineages_final_55',dr['root_lineages_final']['active_root_lineages']==55,dr['root_lineages_final']['active_root_lineages'],55)
    ck('multi_species_roots_27',dr['root_lineages_final']['root_lineages_with_multiple_current_species']==27,dr['root_lineages_final']['root_lineages_with_multiple_current_species'],27)

    # provenance / chronologies
    so=runr['speciation_origin_diagnostic']
    ck('founders_at_61_1',so['founder_candidates_at_61Ma']==1,so['founder_candidates_at_61Ma'],1)
    ck('carryover_speciations_zero',so['matched_61Ma_founder_carryover_speciations']==0,so['matched_61Ma_founder_carryover_speciations'],0)
    ck('new_boundary_unmatched_11',so['not_matched_to_61Ma_founder_state']==11,so['not_matched_to_61Ma_founder_state'],11)
    ck('origin_rows_11',len(so['rows'])==11,len(so['rows']),11)
    ck('origin_rows_all_unmatched',all(r['classification']=='NOT_MATCHED_TO_R311_BOUNDARY_FOUNDER_STATE' for r in so['rows']))
    ck('first_speciation_56Ma',abs(runr['first_speciation_age_ma']-56.0)<1e-12,runr['first_speciation_age_ma'],56.0)
    ck('first_extinction_57Ma',abs(runr['first_ordinary_extinction_age_ma']-57.0)<1e-12,runr['first_ordinary_extinction_age_ma'],57.0)
    ex=runr['ordinary_extinction_chronology']
    ck('extinction_species_exact',[r['species_id'] for r in ex]==['APX_005','APX_001'],[r['species_id'] for r in ex],['APX_005','APX_001'])

    # config and governance
    expected_cfg=asdict(cfg)
    ck('config_exact_R312',meta['config']==expected_cfg,'exact compare')
    important_cfg={
      'biology_cadence_years':125000.0,'speciation_check_interval_years':500000.0,
      'founder_minimum_persistence_years':1000000.0,'vicariance_persistence_min_years':2000000.0,
      'reconnection_persistence_min_years':2000000.0,'mutation_variance_supply_normalized_per_myr':0.002,
      'nonlinear_stabilizing_variance_depletion_per_myr_per_q':0.9876543209876544,'variance_ceiling_normalized':0.08,
      'adaptive_k_eff':38.47,'end_age_ma':46.0,'recovery_observation_start_age_ma':61.0,'recovery_horizon_myr_after_impact':20.0}
    for k,v in important_cfg.items(): ck(f'config::{k}',meta['config'].get(k)==v,meta['config'].get(k),v)
    expected_gov_false=['cha1_reapplied','lifecycle_thaw_reapplied','deep_biological_coupling','post_cha1_radiation_multiplier_used','richness_target_used','positive_diversification_required_for_pass','earth_analogue_target_used','mu_changed','b_changed','q_ceiling_changed','K_center_reinterpreted_as_physical_constant']
    for k in expected_gov_false: ck(f'summary_governance_false::{k}',gov.get(k) is False,gov.get(k),False)
    expected_gov_true=['cha1_already_applied','ordinary_lifecycle_continued','ordinary_speciation_enabled','ordinary_background_extinction_enabled','persistent_vicariance_fission_enabled','persistent_reconnection_coalescence_enabled','production_r37i_r38_runtime_used']
    for k in expected_gov_true: ck(f'summary_governance_true::{k}',gov.get(k) is True,gov.get(k),True)
    for k,v in {'cha1_already_applied':True,'cha1_reapplied':False,'post_cha1_lifecycle_thaw_reapplied':False,'deep_biological_coupling':False,'ordinary_lifecycle_continued':True,'post_cha1_radiation_multiplier_used':False,'richness_target_used':False,'earth_analogue_target_used':False,'r37i_r38_production_runtime_reused':True,'mu_changed':False,'b_changed':False,'q_ceiling_changed':False,'scalar_k_physical_constant_authorized':False}.items(): ck(f'checkpoint_governance::{k}',m_gov.get(k) is v,m_gov.get(k),v)

    # independently test a load-save-load roundtrip of the final state
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        parent_public={k:v for k,v in parent.items() if k!='state'}
        cp=r312.save_diversity_checkpoint(st,td,parent_public,cfg,runr)
        st2=r312.load_diversity_checkpoint(Path(cp['json']),smoke=False)
        comp=r38.compare_runtime_states(st,st2)
    ck('independent_roundtrip_equivalent',comp['equivalent'] is True,comp['equivalent'],True)
    for k,v in comp['arrays'].items(): ck(f'roundtrip_array::{k}',v['same'] and v['max_abs_error']==0.0,v)
    for k,v in comp['reduced_state'].items(): ck(f'roundtrip_reduced::{k}',v['same'] and v['max_abs_error']==0.0,v)
    for k,v in comp['exact_fields'].items(): ck(f'roundtrip_exact::{k}',v is True,v,True)
    for k,v in comp['scalar_abs_errors'].items(): ck(f'roundtrip_scalar::{k}',v==0.0,v,0.0)

    passed=sum(c['pass'] for c in checks); total=len(checks)
    verdict='PASS_R312_CANONICAL_POST_CHA1_61_TO_46_H0_DIVERSITY_RECOVERY__46MA_RESTART_BOUNDARY_SEALED' if passed==total else 'FAIL_R312_SEALED_AUDIT'
    result={
      'schema':'ARCANA_R312_SEALED_POST_RUN_AUDIT_V1','stage':'v0.6D1-R3.12','verdict':verdict,
      'checks_passed':passed,'checks_total':total,'all_pass':passed==total,
      'artifact_hashes':{'summary':sha256(sp),'checkpoint_json':sha256(jp),'checkpoint_npz':sha256(npzp)},
      'boundary':{'age_ma':46.0,'event_side':'POST_CHA1_20MY_DIVERSITY_RECOVERY','species':104,'components':223,'population':runr['final_total_population']},
      'telemetry':{'peak_q':runr['peak_q_recorded'],'final_q_max':inv['q_max'],'final_q_headroom':inv['q_headroom'],'clipping_steps':runr['clipping_steps'],'clipping_contacts':runr['clipping_contacts']},
      'diversity':dr,'speciation_origin':so,'ordinary_extinctions':ex,
      'checks':checks,
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'verdict':verdict,'checks':f'{passed}/{total}','out':str(out)},indent=2))
    return 0 if passed==total else 2
if __name__=='__main__': raise SystemExit(main())
