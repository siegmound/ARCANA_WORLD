from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pytest
from arcana_worldsim.state_query import r510_r329_settlement_cultural_reconciliation as r510


def wj(p: Path, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def manifest(base: Path, names: list[str], status: str):
    return {'stage':'x','status':status,'files':{n:{'bytes':(base/n).stat().st_size,'sha256':r510.sha256_file(base/n)} for n in names}}


def bind_r329(root: Path, mp: pytest.MonkeyPatch):
    pairs = {
        'EXPECTED_R329_FINAL_SEAL_AUDIT_SHA256': r510.R329_SEAL_AUDIT,
        'EXPECTED_R329_FINAL_SEAL_MANIFEST_SHA256': r510.R329_SEAL_MANIFEST,
        'EXPECTED_R329_OUTPUT_MANIFEST_SHA256': r510.R329_OUTPUT_MANIFEST,
        'EXPECTED_R329_REPLAY_SHA256': r510.R329_REPLAY,
        'EXPECTED_R329_AUTHORITY_SHA256': r510.R329_AUTHORITY,
        'EXPECTED_R329_CHECKPOINT_SHA256': r510.R329_CHECKPOINT,
        'EXPECTED_R329_OUTCOMES_SHA256': r510.R329_OUTCOMES,
        'EXPECTED_R329_AUDIT_SHA256': r510.R329_AUDIT,
        'EXPECTED_R329_SOURCE_MANIFEST_SHA256': r510.R329_SOURCE_MANIFEST,
        'EXPECTED_R329_SOURCE_MODULE_SHA256': r510.R329_SOURCE_MODULE,
        'EXPECTED_R329_CONFIG_SHA256': r510.R329_CONFIG,
        'EXPECTED_R329_CONTRACT_SHA256': r510.R329_CONTRACT,
    }
    for attr, rel in pairs.items(): mp.setattr(r510, attr, r510.sha256_file(root/rel))


def refresh_r329_output_manifest(root: Path, mp: pytest.MonkeyPatch):
    out=root/r510.R329_OUT
    names=['R3_29_COMMUNITY_NETWORK_REPLAY.npz','R3_29_COMMUNITY_PRECONDITION_AUTHORITY.json','R3_29_COMMUNITY_PRECONDITION_CHECKPOINT.json','R3_29_LINEAGE_COMMUNITY_OUTCOMES.json','R3_29_SENSITIVITY_AND_ROBUSTNESS.json','R3_29_INTEGRATED_AUDIT.json']
    wj(root/r510.R329_OUTPUT_MANIFEST, manifest(out,names,'CANDIDATE_OUTPUT_MANIFEST'))
    mp.setattr(r510,'EXPECTED_R329_OUTPUT_MANIFEST_SHA256',r510.sha256_file(root/r510.R329_OUTPUT_MANIFEST))
    mp.setattr(r510,'EXPECTED_R329_REPLAY_SHA256',r510.sha256_file(root/r510.R329_REPLAY))
    mp.setattr(r510,'EXPECTED_R329_CHECKPOINT_SHA256',r510.sha256_file(root/r510.R329_CHECKPOINT))
    mp.setattr(r510,'EXPECTED_R329_OUTCOMES_SHA256',r510.sha256_file(root/r510.R329_OUTCOMES))
    mp.setattr(r510,'EXPECTED_R329_AUDIT_SHA256',r510.sha256_file(root/r510.R329_AUDIT))


def build_tree(tmp: Path, mp: pytest.MonkeyPatch) -> Path:
    root=tmp
    wj(root/'configs/world1_r510_r329_settlement_cultural_reconciliation_v0_6D1_R5_10.json',{
        'target_cohort':list(r510.TARGET_COHORT),'external_engine_execution':False,'rerun_r329':False,
        'r329_legacy_numeric_parameters_historical_truth':False,'numeric_historical_truth_claimed':False,
        'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False,
        'auto_authorize_downstream_r330':False,
    })

    # R5.9 candidate handoff.
    o59=root/r510.R59_OUT; o59.mkdir(parents=True)
    wj(root/r510.R59_AUDIT,{'status':'PASS_R59_R58_TO_R328_200KA_0KA_HIGH_RESOLUTION_RECONCILIATION_CANDIDATE','scientific_candidate_eligible':True,'checks_passed':30,'checks_total':30,'failed':[]})
    wj(root/r510.R59_HANDOFF,{'stage':'v0.6D1-R5.9','status':'R59_RECONCILED_0KA_HANDOFF','age_ka':0.0,'candidate_cohort':list(r510.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'downstream_r329_reconciliation_required':True,'downstream_r329_auto_authorized':False,'ready_for_post_r328_population_settlement_reconciliation':True,'admixture_semantics':'R328_ADMIXTURE_OPPORTUNITY_PROXY_ONLY_NOT_REALIZED_HISTORICAL_ADMIXTURE_OR_TRUE_LOCAL_ANCESTRY','source_r328_replay_sha256':'placeholder'})
    wj(root/r510.R59_BINDING,{'r328_replay_sha256':'placeholder'})

    # Minimal R3.28 parent geometry.
    o28=(root/r510.R328_REPLAY).parent; o28.mkdir(parents=True)
    ages28=np.concatenate([np.arange(200.,125.-1e-12,-2.5),np.arange(124.,20.-1e-12,-1.),np.arange(19.75,15.-1e-12,-.25),np.arange(14950,10999,-50,dtype=float)/1000.,np.arange(10.75,-1e-12,-.25)])
    members=np.arange(0,96,3,dtype=int); ids=np.array(r510.TARGET_COHORT)
    snap=np.array([200.,125.,100.,75.,50.,30.,20.,15.,14.,13.,12.,11.,10.,5.,0.])
    D=np.zeros((32,2,len(snap),6,7),dtype=np.float32); active=np.zeros((32,2,len(snap),6),dtype=np.uint8)
    for q in range(len(snap)):
        D[:,:,q,:,0]=10+q; D[:,:,q,:,1]=q; D[:,:,q,:,2]=q+1; active[:,:,q,0]=1
    np.savez_compressed(root/r510.R328_REPLAY,candidate_ids=ids,parent_member_indices=members,age_ka=ages28,
        species_summary_variable_names=np.array(['population_proxy','active_demes','spatial_spread','genetic_diversity_proxy','adaptive_integration','admixture_fraction_proxy','cha2_population_weighted_hazard','cha2_displacement_pressure']),
        snapshot_age_ka=snap,snapshot_deme_state=D,snapshot_active=active)
    mp.setattr(r510,'EXPECTED_R328_REPLAY_SHA256',r510.sha256_file(root/r510.R328_REPLAY))
    h= r510.sha256_file(root/r510.R328_REPLAY)
    h59=json.loads((root/r510.R59_HANDOFF).read_text());h59['source_r328_replay_sha256']=h;wj(root/r510.R59_HANDOFF,h59)
    wj(root/r510.R59_BINDING,{'r328_replay_sha256':h})
    wj(root/r510.R328_AUTHORITY,{'contact_semantics':'SYMMETRIC_ADMIXTURE_OPPORTUNITY_DIAGNOSTIC_NO_FORCED_REPLACEMENT'})
    wj(root/r510.R59_MANIFEST,manifest(o59,['R5_9_INTEGRATED_RECONCILIATION.json','R5_9_0KA_RECONCILED_HANDOFF.json','R5_9_PARENT_AUTHORITY_BINDING.json'],'PASS_R59_R58_TO_R328_200KA_0KA_HIGH_RESOLUTION_RECONCILIATION_CANDIDATE'))

    # R3.29 source/config authority.
    src="admix=np.clip(S[...,5],0,1)\nexch=np.clip(contact[:,t,None]*foo*(0.55+0.45*admix[:,:,t]),0,1)\n"
    (root/r510.R329_SOURCE_MODULE).parent.mkdir(parents=True,exist_ok=True);(root/r510.R329_SOURCE_MODULE).write_text(src,encoding='utf-8')
    wj(root/r510.R329_CONFIG,{'start_age_ka':50.0,'culture_stock_rate_per_kyr':0.09,'qualification':{'network_min':.46,'transmission_min':.50,'culture_stock_min':.38,'settlement_min':.42,'cha2_stock_retention_min':.78,'sensitivity_frequency_min':.70},'sensitivity_multipliers':[.9,.94,.97,1.0,1.03,1.06,1.1,.92,1.08,.96,1.04]})
    (root/r510.R329_CONTRACT).write_text('# synthetic R3.29\n',encoding='utf-8')
    wj(root/r510.R329_SOURCE_MANIFEST,{'stage':'v0.6D1-R3.29','files':{}})

    # R3.29 sealed output.
    o29=root/r510.R329_OUT; o29.mkdir(parents=True)
    ages29=ages28[ages28<=50.+1e-12]; sm=snap<=50.+1e-12; anchor_age=snap[sm]
    X=np.zeros((32,2,len(ages29),10),dtype=np.float32); P=np.full((32,2,6),.5,dtype=np.float32)
    A=np.zeros((32,2,len(anchor_age),6,7),dtype=np.float32); A[...,:3]=D[:,:,sm,:,:3]
    active29=active[:,:,sm,:]
    np.savez_compressed(root/r510.R329_REPLAY,candidate_ids=ids,parent_member_indices=members,age_ka=ages29,
        community_variable_names=np.array(r510.EXPECTED_R329_TIME_NAMES),community_summary=X,
        functional_prior_names=np.array(r510.EXPECTED_R329_PRIOR_NAMES),functional_priors=P,anchor_age_ka=anchor_age,
        community_anchor_variable_names=np.array(r510.EXPECTED_R329_ANCHOR_NAMES),community_anchor_state=A,community_anchor_active=active29)
    wj(root/r510.R329_AUTHORITY,{'candidate_cohort':list(r510.TARGET_COHORT),'parent':'PASS_R328_HIGH_RESOLUTION_200KA_TO_0_POPULATION_STRUCTURE_MIGRATION_ADMIXTURE_CHA2_EXPOSURE_AND_HUMAN_0KA_CHECKPOINT_SEALED','population_semantics':'R328_POPULATION_PROXY_NOT_LITERAL_CENSUS','settlement_semantics':'PERSISTENCE_POTENTIAL_NOT_ARCHAEOLOGICALLY_OBSERVED_SETTLEMENT','culture_semantics':'TRANSMISSION_AND_CUMULATION_PRECONDITIONS_NOT_LANGUAGE_RELIGION_TECHNOLOGY_OR_CULTURAL_IDENTITY','spatial_semantics':'R328_EXPLICIT_DEME_SNAPSHOT_ANCHORS_ONLY_NO_INVENTED_CONTINUOUS_DEME_PATHS','state_semantics':'DIMENSIONLESS_COMMUNITY_AND_CULTURAL_PRECONDITION_INDICES_CONDITIONED_ON_R328_POPULATION_REPLAY','deep_biological_coupling':False,'human_similarity_target':False,'unique_human_identity_materialized':False})
    wj(root/r510.R329_CHECKPOINT,{'age_ka':0.0,'candidate_cohort':list(r510.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False})
    cand=[{'species_id':'RPT_010_D02','baseline_qualified':True},{'species_id':'RPT_009_D02','baseline_qualified':True}]
    wj(root/r510.R329_OUTCOMES,{'candidates':cand,'community_precondition_cohort':list(r510.TARGET_COHORT),'robust_priority_cohort':['RPT_010_D02'],'borderline_retained_cohort':['RPT_009_D02'],'interpretation':'PRECONDITIONS_ONLY;_BASELINE_CAPABLE_LINEAGES_RETAINED;_SENSITIVITY_USED_AS_PRIORITY_NOT_EXTINCTION_OR_IDENTITY_GATE'})
    wj(root/r510.R329_SENSITIVITY,{'variant_count':11,'variants':[{'multiplier':x,'cohort':list(r510.TARGET_COHORT)} for x in [.9,.94,.97,1.0,1.03,1.06,1.1,.92,1.08,.96,1.04]]})
    wj(root/r510.R329_AUDIT,{'status':'PASS_R329_POPULATION_MOBILITY_SETTLEMENT_AND_CULTURAL_PRECONDITIONS_CANDIDATE','checks_passed':24,'checks_total':24,'checks_failed':0})
    refresh_r329_output_manifest(root,mp)
    s29=root/r510.R329_SEAL_OUT; s29.mkdir(parents=True)
    wj(root/r510.R329_SEAL_AUDIT,{'verdict':'SEALED','status':'PASS_R329_POPULATION_MOBILITY_SETTLEMENT_CULTURAL_TRANSMISSION_PRECONDITIONS_AND_CHA2_COMMUNITY_EXPOSURE_SEALED','checks_passed':37,'checks_failed':0})
    wj(root/r510.R329_SEAL_MANIFEST,{'files':{'R3_29_FINAL_SEAL_AUDIT.json':{'bytes':(root/r510.R329_SEAL_AUDIT).stat().st_size,'sha256':r510.sha256_file(root/r510.R329_SEAL_AUDIT)}}})
    bind_r329(root,mp)
    return root


def test_r510_passes_and_preserves_two_lineage_precondition_handoff(tmp_path,monkeypatch):
    root=build_tree(tmp_path,monkeypatch); a=r510.reconcile(root)
    assert a['scientific_candidate_eligible'] is True and a['checks_passed']==a['checks_total']
    h=json.loads((root/r510.OUT_REL/'R5_10_0KA_COMMUNITY_PRECONDITION_HANDOFF.json').read_text())
    assert h['candidate_cohort']==list(r510.TARGET_COHORT)
    assert h['robust_priority_cohort']==['RPT_010_D02']
    assert h['borderline_retained_cohort']==['RPT_009_D02']
    assert h['downstream_r330_auto_authorized'] is False


def test_r59_unique_identity_drift_blocks_parent(tmp_path,monkeypatch):
    root=build_tree(tmp_path,monkeypatch); h=json.loads((root/r510.R59_HANDOFF).read_text());h['unique_human_identity_materialized']=True;wj(root/r510.R59_HANDOFF,h)
    wj(root/r510.R59_MANIFEST,manifest(root/r510.R59_OUT,['R5_9_INTEGRATED_RECONCILIATION.json','R5_9_0KA_RECONCILED_HANDOFF.json','R5_9_PARENT_AUTHORITY_BINDING.json'],'PASS'))
    p=r510.validate_parent_authority(root); assert 'r59_handoff_exact' in p['failed']


def test_r329_age_axis_drift_fails_reconciliation(tmp_path,monkeypatch):
    root=build_tree(tmp_path,monkeypatch)
    with np.load(root/r510.R329_REPLAY,allow_pickle=False) as z: d={k:z[k] for k in z.files}
    d['age_ka']=d['age_ka'].copy();d['age_ka'][10]-=.001;np.savez_compressed(root/r510.R329_REPLAY,**d)
    refresh_r329_output_manifest(root,monkeypatch); monkeypatch.setattr(r510,'EXPECTED_R329_REPLAY_SHA256',r510.sha256_file(root/r510.R329_REPLAY))
    a=r510.reconcile(root); assert a['scientific_candidate_eligible'] is False and 'r329_age_axis_exact_r328_subset_50ka_to_0' in a['failed']


def test_r329_admixture_proxy_cannot_be_recast_as_realized_ancestry(tmp_path,monkeypatch):
    root=build_tree(tmp_path,monkeypatch); (root/r510.R329_SOURCE_MODULE).write_text('admix=np.clip(S[...,5],0,1)\n# realized ancestry misuse\n',encoding='utf-8')
    monkeypatch.setattr(r510,'EXPECTED_R329_SOURCE_MODULE_SHA256',r510.sha256_file(root/r510.R329_SOURCE_MODULE))
    a=r510.reconcile(root); assert a['scientific_candidate_eligible'] is False and 'r329_uses_r328_admixture_proxy_only_as_exchange_opportunity_modifier' in a['failed']
