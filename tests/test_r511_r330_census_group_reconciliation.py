from pathlib import Path
import hashlib, json
import numpy as np
import pytest

from arcana_worldsim.state_query import r511_r330_census_group_reconciliation as r511


def wj(p:Path,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def manifest(base:Path,names,status):
 return {'stage':'synthetic','status':status,'files':{n:{'bytes':(base/n).stat().st_size,'sha256':r511.sha256_file(base/n)} for n in names}}


def bind_hashes(root:Path,mp:pytest.MonkeyPatch):
 pairs={
  'EXPECTED_R510_SOURCE_MANIFEST_SHA256':r511.R510_SOURCE_MANIFEST,'EXPECTED_R510_SOURCE_MODULE_SHA256':r511.R510_SOURCE_MODULE,'EXPECTED_R510_CONFIG_SHA256':r511.R510_CONFIG,'EXPECTED_R510_CONTRACT_SHA256':r511.R510_CONTRACT,
  'EXPECTED_R330_FINAL_SEAL_AUDIT_SHA256':r511.R330_SEAL_AUDIT,'EXPECTED_R330_FINAL_SEAL_MANIFEST_SHA256':r511.R330_SEAL_MANIFEST,'EXPECTED_R330_OUTPUT_MANIFEST_SHA256':r511.R330_OUTPUT_MANIFEST,
  'EXPECTED_R330_CENSUS_NPZ_SHA256':r511.R330_CENSUS_NPZ,'EXPECTED_R330_ABM_NPZ_SHA256':r511.R330_ABM_NPZ,'EXPECTED_R330_AUTHORITY_SHA256':r511.R330_AUTHORITY,'EXPECTED_R330_CHECKPOINT_SHA256':r511.R330_CHECKPOINT,
  'EXPECTED_R330_OUTCOMES_SHA256':r511.R330_OUTCOMES,'EXPECTED_R330_SENSITIVITY_SHA256':r511.R330_SENSITIVITY,'EXPECTED_R330_HISTORY_SHA256':r511.R330_HISTORY,'EXPECTED_R330_AUDIT_SHA256':r511.R330_AUDIT,
  'EXPECTED_R330_SOURCE_MANIFEST_SHA256':r511.R330_SOURCE_MANIFEST,'EXPECTED_R330_SOURCE_MODULE_SHA256':r511.R330_SOURCE_MODULE,'EXPECTED_R330_CONFIG_SHA256':r511.R330_CONFIG,'EXPECTED_R330_CONTRACT_SHA256':r511.R330_CONTRACT,
  'EXPECTED_R329_REPLAY_SHA256':r511.R329_REPLAY,'EXPECTED_R328_REPLAY_SHA256':r511.R328_REPLAY,
 }
 for name,rel in pairs.items(): mp.setattr(r511,name,r511.sha256_file(root/rel))


def build_tree(tmp:Path,mp:pytest.MonkeyPatch)->Path:
 root=tmp
 wj(root/'configs/world1_r511_r330_census_group_reconciliation_v0_6D1_R5_11.json',{
  'target_cohort':list(r511.TARGET_COHORT),'external_engine_execution':False,'rerun_r330':False,'r330_census_equivalent_historical_truth':False,'r330_residential_group_equivalents_historical_truth':False,
  'r330_fission_fusion_equivalents_literal_events':False,'r330_legacy_calibration_values_canonical':False,'r330_evidence_basis_revalidated_in_r511':False,'numeric_historical_truth_claimed':False,'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False,'auto_authorize_downstream_r331':False})

 # Synthetic exact R5.10 source + outputs.
 for rel,txt in [(r511.R510_SOURCE_MODULE,'# r510\n'),(r511.R510_CONTRACT,'# r510 contract\n')]: (root/rel).parent.mkdir(parents=True,exist_ok=True);(root/rel).write_text(txt,encoding='utf-8')
 wj(root/r511.R510_CONFIG,{'stage':'v0.6D1-R5.10'}); wj(root/r511.R510_SOURCE_MANIFEST,{'stage':'v0.6D1-R5.10','files':{}})
 o510=root/r511.R510_OUT;o510.mkdir(parents=True)
 wj(root/r511.R510_AUDIT,{'status':'PASS_R510_R59_TO_R329_POPULATION_SETTLEMENT_CULTURAL_PRECONDITION_RECONCILIATION_CANDIDATE','scientific_candidate_eligible':True,'checks_passed':33,'checks_total':33,'failed':[]})
 wj(root/r511.R510_HANDOFF,{'status':'R510_RECONCILED_COMMUNITY_PRECONDITION_HANDOFF_0KA','age_ka':0.0,'candidate_cohort':list(r511.TARGET_COHORT),'community_precondition_cohort':list(r511.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'absolute_census_materialized':False,'ready_for_r330_reconciliation':True,'downstream_r330_auto_authorized':False,'gene_flow_semantics':'R329_INTERLINEAGE_EXCHANGE_OPPORTUNITY_IS_DIAGNOSTIC_ONLY_NOT_REALIZED_GENE_FLOW_OR_ADMIXTURE'})
 wj(root/r511.R510_BINDING,{'status':'R510_PARENT_AUTHORITY_BINDING'})
 wj(root/r511.R510_MANIFEST,manifest(o510,['R5_10_INTEGRATED_RECONCILIATION.json','R5_10_0KA_COMMUNITY_PRECONDITION_HANDOFF.json','R5_10_PARENT_AUTHORITY_BINDING.json'],'PASS'))

 ids=np.array(r511.TARGET_COHORT); members=np.arange(0,96,3,dtype=int)
 ages=np.arange(50.,-1.,-1.)
 # append noninteger ages to reach 175 while retaining exact same parent axis for R3.29/R3.30
 extra=np.linspace(49.75,0.25,124); ages=np.sort(np.unique(np.concatenate([ages,extra])))[::-1]
 assert len(ages)==175
 ages28=np.concatenate([np.array([200.]),ages])
 summary28=np.zeros((32,2,len(ages28),1),float)
 base=np.linspace(12000,18000,32)[:,None]
 summary28[:,:,0,0]=base*np.array([[1.,.9]])
 for t in range(1,len(ages28)): summary28[:,:,t,0]=summary28[:,:,0,0]*(1.0+0.002*t)
 (root/r511.R328_REPLAY).parent.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(root/r511.R328_REPLAY,candidate_ids=ids,parent_member_indices=members,age_ka=ages28,species_summary=summary28)

 names29=np.array(['population_support_norm','residential_mobility_index','aggregation_potential','network_connectivity','cultural_transmission_support','cumulative_culture_precondition_stock','settlement_persistence_potential','resource_stress_proxy','interlineage_exchange_opportunity','cha2_community_disruption'])
 C=np.zeros((32,2,len(ages),10),float); C[...,1]=.35;C[...,2]=.45;C[...,3]=.55;C[...,5]=.4;C[...,6]=.5;C[...,7]=.2;C[...,8]=.1;C[...,9]=.05
 anchors=np.array([50.,30.,20.,15.,14.,13.,12.,11.,10.,5.,0.])
 (root/r511.R329_REPLAY).parent.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(root/r511.R329_REPLAY,candidate_ids=ids,parent_member_indices=members,age_ka=ages,community_variable_names=names29,community_summary=C,anchor_age_ka=anchors)

 cfg330={'stage':'v0.6D1-R3.30','ne_to_total_census_ratio_prior':{'distribution':'triangular','low':.18,'mode':.34,'high':.60,'seed':330029},'residential_group_size':{'minimum':10.,'dispersed_reference':14.,'central_reference':30.,'aggregated_reference':42.,'maximum':80.},'active_network_reference':150.,'regional_network_reference':550.,'weighted_agents_per_deme':8,'sensitivity_ratio_multipliers':[.8,.9,1.,1.1,1.2],'sensitivity_group_size_multipliers':[.8,.9,1.,1.1,1.2]}
 wj(root/r511.R330_CONFIG,cfg330); (root/r511.R330_CONTRACT).write_text('# r330 contract\n',encoding='utf-8'); (root/r511.R330_SOURCE_MODULE).parent.mkdir(parents=True,exist_ok=True);(root/r511.R330_SOURCE_MODULE).write_text('# r330 source\n',encoding='utf-8');wj(root/r511.R330_SOURCE_MANIFEST,{'stage':'v0.6D1-R3.30','files':{}})

 ratio=r511._ratio_draws(cfg330); p200=summary28[:,:,0,0]; ix=np.arange(1,len(ages28)); pop=summary28[:,:,ix,0]; c200=p200/ratio;census=c200[:,:,None]*(pop/np.maximum(p200[:,:,None],1.0))
 agg=C[...,2];mob=C[...,1];sett=C[...,6];net=C[...,3];dis=C[...,9]; gs=cfg330['residential_group_size'];mean=np.clip(gs['dispersed_reference']+30*agg+7*sett-10*mob,gs['minimum'],gs['maximum']);group=census/mean;active_size=np.clip(150*(.75+.5*net),80,260);regional=np.clip(550*(.65+.7*net),250,1100);S=np.stack([census,mean,group,census/active_size,census/regional,group*dis],axis=-1)
 o330=root/r511.R330_OUT;o330.mkdir(parents=True)
 np.savez_compressed(root/r511.R330_CENSUS_NPZ,candidate_ids=ids,parent_member_indices=members,age_ka=ages,census_variable_names=np.array(r511.EXPECTED_CENSUS_NAMES),census_group_series=S,ne_to_total_census_ratio=ratio,census_200ka_anchor=c200)
 # 48 weighted agents, use first one to conserve exactly.
 A=np.zeros((32,2,11,48,12),float);AA=np.zeros((32,2,11,48),np.uint8);H=np.zeros((32,2,11,10),float)
 for ai,a in enumerate(anchors):
  ti=int(np.where(np.isclose(ages,a))[0][0]);A[:,:,ai,0,0]=S[:,:,ti,0];A[:,:,ai,0,1]=S[:,:,ti,2];A[:,:,ai,0,2]=S[:,:,ti,0]/np.maximum(S[:,:,ti,2],1e-9);AA[:,:,ai,0]=1;H[:,:,ai,0]=S[:,:,ti,0];H[:,:,ai,1]=S[:,:,ti,2]
 np.savez_compressed(root/r511.R330_ABM_NPZ,candidate_ids=ids,parent_member_indices=members,anchor_age_ka=anchors,agent_variable_names=np.array(r511.EXPECTED_AGENT_NAMES),agent_state=A,agent_active=AA,history_variable_names=np.array(r511.EXPECTED_HISTORY_NAMES),history_summary=H)
 evidence={f'E{i}':{} for i in range(8)}
 wj(root/r511.R330_AUTHORITY,{'census_semantics':'UNCERTAINTY_AWARE_CENSUS_EQUIVALENT_POSTERIOR_NOT_ARCHAEOLOGICAL_OBSERVATION','group_abm_semantics':'WEIGHTED_RESIDENTIAL_GROUP_AGENTS_NOT_PERSON_LEVEL','deep_biological_coupling':False,'evidence_basis':evidence})
 wj(root/r511.R330_CHECKPOINT,{'candidate_cohort':list(r511.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'absolute_census_equivalent_materialized':True,'archaeological_census_observation_claimed':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False})
 wj(root/r511.R330_OUTCOMES,{'unique_human_identity_materialized':False,'candidate_lineages':list(r511.TARGET_COHORT)})
 variants=[{'ratio_multiplier':rm,'group_size_multiplier':gm} for rm in [.8,.9,1.,1.1,1.2] for gm in [.8,.9,1.,1.1,1.2]]
 wj(root/r511.R330_SENSITIVITY,{'variant_count':25,'variants':variants,'candidate_retention':list(r511.TARGET_COHORT),'selection_gate':False})
 wj(root/r511.R330_HISTORY,{'status':'LATE_PLEISTOCENE_WEIGHTED_GROUP_COMMUNITY_HISTORY','anchors':[]})
 wj(root/r511.R330_AUDIT,{'status':'PASS_R330_CENSUS_GROUP_ABM_AND_COMMUNITY_HISTORY_CANDIDATE','checks_passed':27,'checks_total':27,'checks_failed':0})
 # filler audit md for manifest
 (o330/'R3_30_AUDIT.md').write_text('# audit\n',encoding='utf-8')
 names=['R3_30_AUDIT.md','R3_30_CENSUS_AND_GROUP_TIMESERIES.npz','R3_30_CENSUS_CALIBRATION_AUTHORITY.json','R3_30_COMMUNITY_HISTORY_CHECKPOINT.json','R3_30_INTEGRATED_AUDIT.json','R3_30_LATE_PLEISTOCENE_COMMUNITY_HISTORY.json','R3_30_LINEAGE_CENSUS_AND_GROUP_OUTCOMES.json','R3_30_SENSITIVITY_AND_ROBUSTNESS.json','R3_30_WEIGHTED_GROUP_ABM.npz']
 wj(root/r511.R330_OUTPUT_MANIFEST,manifest(o330,names,'CANDIDATE_OUTPUT_MANIFEST'))
 s330=root/r511.R330_SEAL_OUT;s330.mkdir(parents=True)
 wj(root/r511.R330_SEAL_AUDIT,{'verdict':'SEALED','status':'PASS_R330_CENSUS_EQUIVALENT_CALIBRATION_WEIGHTED_GROUP_ABM_LATE_PLEISTOCENE_COMMUNITY_HISTORY_AND_CHA2_GROUP_EXPOSURE_SEALED','checks_passed':27,'checks_failed':0})
 wj(root/r511.R330_SEAL_MANIFEST,{'files':{'R3_30_FINAL_SEAL_AUDIT.json':{'bytes':(root/r511.R330_SEAL_AUDIT).stat().st_size,'sha256':r511.sha256_file(root/r511.R330_SEAL_AUDIT)}}})
 bind_hashes(root,mp)
 return root


def test_r511_passes_and_emits_diagnostic_handoff(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);a=r511.reconcile(root);assert a['scientific_candidate_eligible'] and a['checks_passed']==a['checks_total']
 h=json.loads((root/r511.OUT_REL/'R5_11_0KA_CENSUS_GROUP_RECONCILED_HANDOFF.json').read_text());assert h['candidate_cohort']==list(r511.TARGET_COHORT);assert h['census_equivalent_layer_available'] is True;assert h['literal_absolute_census_materialized'] is False;assert h['downstream_r331_auto_authorized'] is False


def test_ratio_draw_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch)
 with np.load(root/r511.R330_CENSUS_NPZ,allow_pickle=False) as z:d={k:z[k] for k in z.files}
 d['ne_to_total_census_ratio']=d['ne_to_total_census_ratio'].copy();d['ne_to_total_census_ratio'][0,0]+=.01;np.savez_compressed(root/r511.R330_CENSUS_NPZ,**d)
 # permit parent hash checks to pass so semantic check is exercised
 monkeypatch.setattr(r511,'EXPECTED_R330_CENSUS_NPZ_SHA256',r511.sha256_file(root/r511.R330_CENSUS_NPZ));wj(root/r511.R330_OUTPUT_MANIFEST,manifest(root/r511.R330_OUT,['R3_30_AUDIT.md','R3_30_CENSUS_AND_GROUP_TIMESERIES.npz','R3_30_CENSUS_CALIBRATION_AUTHORITY.json','R3_30_COMMUNITY_HISTORY_CHECKPOINT.json','R3_30_INTEGRATED_AUDIT.json','R3_30_LATE_PLEISTOCENE_COMMUNITY_HISTORY.json','R3_30_LINEAGE_CENSUS_AND_GROUP_OUTCOMES.json','R3_30_SENSITIVITY_AND_ROBUSTNESS.json','R3_30_WEIGHTED_GROUP_ABM.npz'],'CANDIDATE_OUTPUT_MANIFEST'));monkeypatch.setattr(r511,'EXPECTED_R330_OUTPUT_MANIFEST_SHA256',r511.sha256_file(root/r511.R330_OUTPUT_MANIFEST))
 a=r511.reconcile(root);assert not a['scientific_candidate_eligible'];assert 'r330_ne_to_total_ratio_draws_exact' in a['failed']


def test_weighted_agent_census_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch)
 with np.load(root/r511.R330_ABM_NPZ,allow_pickle=False) as z:d={k:z[k] for k in z.files}
 d['agent_state']=d['agent_state'].copy();d['agent_state'][0,0,0,0,0]+=100.;np.savez_compressed(root/r511.R330_ABM_NPZ,**d)
 monkeypatch.setattr(r511,'EXPECTED_R330_ABM_NPZ_SHA256',r511.sha256_file(root/r511.R330_ABM_NPZ));wj(root/r511.R330_OUTPUT_MANIFEST,manifest(root/r511.R330_OUT,['R3_30_AUDIT.md','R3_30_CENSUS_AND_GROUP_TIMESERIES.npz','R3_30_CENSUS_CALIBRATION_AUTHORITY.json','R3_30_COMMUNITY_HISTORY_CHECKPOINT.json','R3_30_INTEGRATED_AUDIT.json','R3_30_LATE_PLEISTOCENE_COMMUNITY_HISTORY.json','R3_30_LINEAGE_CENSUS_AND_GROUP_OUTCOMES.json','R3_30_SENSITIVITY_AND_ROBUSTNESS.json','R3_30_WEIGHTED_GROUP_ABM.npz'],'CANDIDATE_OUTPUT_MANIFEST'));monkeypatch.setattr(r511,'EXPECTED_R330_OUTPUT_MANIFEST_SHA256',r511.sha256_file(root/r511.R330_OUTPUT_MANIFEST))
 a=r511.reconcile(root);assert not a['scientific_candidate_eligible'];assert 'r330_weighted_agents_conserve_census' in a['failed']


def test_r510_unique_identity_drift_blocks_parent(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);h=json.loads((root/r511.R510_HANDOFF).read_text());h['unique_human_identity_materialized']=True;wj(root/r511.R510_HANDOFF,h);wj(root/r511.R510_MANIFEST,manifest(root/r511.R510_OUT,['R5_10_INTEGRATED_RECONCILIATION.json','R5_10_0KA_COMMUNITY_PRECONDITION_HANDOFF.json','R5_10_PARENT_AUTHORITY_BINDING.json'],'PASS'))
 a=r511.reconcile(root);assert not a['scientific_candidate_eligible'];assert 'parent_authority_pass' in a['failed']
