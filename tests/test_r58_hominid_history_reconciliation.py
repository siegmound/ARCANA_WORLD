from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pytest
from arcana_worldsim.state_query import r58_hominid_history_reconciliation as r58

def wj(p:Path,o):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def manifest(base:Path,names:list[str],status='X'):
 files={}
 for n in names:
  p=base/n;files[n]={'bytes':p.stat().st_size,'sha256':r58.sha256_file(p)}
 return {'stage':'x','status':status,'files':files}

def build_tree(tmp:Path,monkeypatch:pytest.MonkeyPatch)->Path:
 root=tmp
 # R3.21 directly attested registry and history.
 reg={'stage':'v0.6D1-R3.21','lineages':[
  {'species_id':'RPT_010_D02','birth_age_ma':81.0,'parent_species_id':'RPT_010','root_species_id':'RPT_010','ancestry_chain_root_to_present':['RPT_010','RPT_010_D02']},
  {'species_id':'RPT_009_D02','birth_age_ma':71.5,'parent_species_id':'RPT_009','root_species_id':'RPT_009','ancestry_chain_root_to_present':['RPT_009','RPT_009_D02']},
 ]}
 clos={'stage':'v0.6D1-R3.21','historical_events':[
  {'event_id':'E002910','raw':{'age_ma':2.0,'event':'deme_fission','species_id_at_fission':'RPT_010_D02','parent_component_id':'a','daughter_component_id':'b'}},
  {'event_id':'E002909','raw':{'age_ma':2.0,'event':'deme_fission','species_id_at_fission':'RPT_009_D02','parent_component_id':'c','daughter_component_id':'d'}},
  {'event_id':'OLD','raw':{'age_ma':81.0,'event':'speciation','daughter_species_id':'RPT_010_D02'}},
 ]}
 wj(root/r58.R321_REGISTRY,reg);wj(root/r58.R321_CLOSURE,clos)
 monkeypatch.setattr(r58,'EXPECTED_R321_REGISTRY_SHA256',r58.sha256_file(root/r58.R321_REGISTRY));monkeypatch.setattr(r58,'EXPECTED_R321_CLOSURE_SHA256',r58.sha256_file(root/r58.R321_CLOSURE))
 # R3.27 sealed macro replay.
 out327=root/r58.R327_OUT;out327.mkdir(parents=True)
 cp={'age_ka':200.0,'candidate_cohort':list(r58.TARGET_COHORT),'candidate_count':2,'unique_human_identity_materialized':False,'interpretation':'QUALIFIED_MACROEVOLUTIONARY_COHORT_FOR_NEXT_HIGH_RESOLUTION_REPLAY_NOT_FINAL_HUMAN_SPECIES_IDENTITY'};wj(root/r58.R327_CHECKPOINT,cp)
 ids=np.array(['RPT_010_D02','RPT_009_D02','RPT_020_D02','RPT_007_D05','RPT_019_D02','RPT_006_D04'])
 ages=np.arange(3.0,0.2-1e-12,-.02);vars=np.array(['effective_population','deme_count','ecological_breadth','cumulative_buffering','dispersal_capacity','developmental_investment','genetic_diversity_proxy','adaptive_integration'])
 state=np.ones((96,6,len(ages),8),dtype=float)
 np.savez_compressed(root/r58.R327_TRAJECTORIES,candidate_ids=ids,age_ma=ages,variable_names=vars,state=state)
 wj(out327/'dummy.json',{'x':1});wj(root/r58.R327_OUTPUT_MANIFEST,manifest(out327,['R3_27_HUMAN_200KA_CHECKPOINT.json','R3_27_MACRO_REPLAY_TRAJECTORIES.npz','dummy.json'],'CANDIDATE_OUTPUT_MANIFEST'))
 seal327={'status':'PASS_R327_HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA_ROBUSTNESS_AND_HUMAN_200KA_CHECKPOINT_SEALED','verdict':'SEALED','checks_passed':28,'checks_failed':0};wj(root/r58.R327_SEAL_AUDIT,seal327)
 monkeypatch.setattr(r58,'EXPECTED_R327_OUTPUT_MANIFEST_SHA256',r58.sha256_file(root/r58.R327_OUTPUT_MANIFEST));monkeypatch.setattr(r58,'EXPECTED_R327_FINAL_SEAL_AUDIT_SHA256',r58.sha256_file(root/r58.R327_SEAL_AUDIT))
 # R5.5 atlas/history and manifest: 35 pair schedules all identical.
 o55=root/r58.R55_OUT;o55.mkdir(parents=True)
 pair_ids=np.array([f'P{i:02d}' for i in range(35)]);near=np.zeros((35,len(ages)));near[:,20:80]=.5;exact=np.zeros_like(near);exact[:,30:40]=.2
 np.savez_compressed(root/r58.R55_ATLAS,age_ma=ages,pair_ids=pair_ids,exact_contact_ensemble_fraction=exact,one_cell_contact_ensemble_fraction=near,contact_support_thresholds=np.array([0,.25,.5,.75,1.]))
 wj(root/r58.R55_HISTORY,{'candidate_ids':list(r58.TARGET_COHORT),'cross_lineage_pair_count':35,'age_state_count':141,'semantics':'NOT_REALIZED_ADMIXTURE'})
 wj(o55/'R5_5_INTEGRATED_AUDIT.json',{'x':1});wj(root/r58.R55_MANIFEST,manifest(o55,['R5_5_CONTACT_OPPORTUNITY_ATLAS.npz','R5_5_CONTACT_ZONE_HISTORY.json','R5_5_INTEGRATED_AUDIT.json'],'PASS_R55_CONTACT_ZONE_AND_GENE_FLOW_HISTORY_CONSOLIDATION_CANDIDATE'))
 # R5.6 plan and manifest.
 o56=root/r58.R56_OUT;o56.mkdir(parents=True);wj(root/r58.R56_PLAN,{'schedule_class_count':1,'planned_stream_count':6});wj(o56/'R5_6_INTEGRATED_AUDIT.json',{'x':1});wj(root/r58.R56_MANIFEST,manifest(o56,['R5_6_SLIM_EXECUTION_PLAN.json','R5_6_INTEGRATED_AUDIT.json'],'PASS_R56_TARGETED_ANCESTRY_AND_ADMIXTURE_CHALLENGE_EVIDENCE_CANDIDATE'))
 # R5.7 final seal binds R5.5/R5.6 manifests.
 o57=root/r58.R57_OUT;o57.mkdir(parents=True)
 seal57={'sealed':True,'status':'PASS_R57_R53_R56_HOMINID_DEMOGRAPHY_GENE_FLOW_ANCESTRY_BLOCK_SEALED','checks_passed':43,'checks_total':43,'summary':{'closure_readiness':'SEALED_R53_R56_GOVERNED_EVIDENCE_BLOCK_READY_FOR_POST_BLOCK_HOMINID_HISTORY_RECONCILIATION','numeric_historical_truth_claimed':False,'realized_historical_admixture_claimed':False,'canonical_state_changed':False,'deep_biological_coupling':False},'block_input_binding':{'candidate_stages':{'R5.5':{'output_manifest_sha256':r58.sha256_file(root/r58.R55_MANIFEST)},'R5.6':{'output_manifest_sha256':r58.sha256_file(root/r58.R56_MANIFEST)}}}}
 wj(root/r58.R57_SEAL,seal57);wj(root/r58.R57_SEAL_MANIFEST,{'final_seal_file':{'sha256':r58.sha256_file(root/r58.R57_SEAL)}});monkeypatch.setattr(r58,'EXPECTED_R57_FINAL_SEAL_SHA256',r58.sha256_file(root/r58.R57_SEAL))
 # Config.
 cfg={'target_cohort':list(r58.TARGET_COHORT),'external_engine_execution':False,'numeric_historical_truth_claimed':False,'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False};wj(root/'configs/world1_r58_hominid_history_reconciliation_v0_6D1_R5_8.json',cfg)
 return root

def test_reconciliation_passes_and_emits_clean_handoff(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);a=r58.reconcile(root);assert a['scientific_candidate_eligible'] is True;assert a['checks_passed']==a['checks_total'];h=json.loads((root/r58.OUT_REL/'R5_8_200KA_RECONCILED_HANDOFF.json').read_text());assert h['candidate_cohort']==list(r58.TARGET_COHORT) and h['unique_human_identity_materialized'] is False

def test_direct_event_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);d=json.loads((root/r58.R321_CLOSURE).read_text());d['historical_events'][0]['raw']['age_ma']=1.98;wj(root/r58.R321_CLOSURE,d);monkeypatch.setattr(r58,'EXPECTED_R321_CLOSURE_SHA256',r58.sha256_file(root/r58.R321_CLOSURE));a=r58.reconcile(root);assert a['scientific_candidate_eligible'] is False;assert 'RPT_010_D02_direct_event_exact' in a['failed']

def test_r55_age_axis_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);with_np=np.load(root/r58.R55_ATLAS);data={k:with_np[k] for k in with_np.files};with_np.close();data['age_ma']=data['age_ma'].copy();data['age_ma'][10]-=.001;np.savez_compressed(root/r58.R55_ATLAS,**data);m=json.loads((root/r58.R55_MANIFEST).read_text());p=root/r58.R55_ATLAS;m['files']['R5_5_CONTACT_OPPORTUNITY_ATLAS.npz']={'bytes':p.stat().st_size,'sha256':r58.sha256_file(p)};wj(root/r58.R55_MANIFEST,m);seal=json.loads((root/r58.R57_SEAL).read_text());seal['block_input_binding']['candidate_stages']['R5.5']['output_manifest_sha256']=r58.sha256_file(root/r58.R55_MANIFEST);wj(root/r58.R57_SEAL,seal);wj(root/r58.R57_SEAL_MANIFEST,{'final_seal_file':{'sha256':r58.sha256_file(root/r58.R57_SEAL)}});monkeypatch.setattr(r58,'EXPECTED_R57_FINAL_SEAL_SHA256',r58.sha256_file(root/r58.R57_SEAL));a=r58.reconcile(root);assert a['scientific_candidate_eligible'] is False;assert 'r55_age_axis_exactly_matches_r327' in a['failed']

def test_schedule_class_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);d=json.loads((root/r58.R56_PLAN).read_text());d['schedule_class_count']=2;wj(root/r58.R56_PLAN,d);m=json.loads((root/r58.R56_MANIFEST).read_text());p=root/r58.R56_PLAN;m['files']['R5_6_SLIM_EXECUTION_PLAN.json']={'bytes':p.stat().st_size,'sha256':r58.sha256_file(p)};wj(root/r58.R56_MANIFEST,m);seal=json.loads((root/r58.R57_SEAL).read_text());seal['block_input_binding']['candidate_stages']['R5.6']['output_manifest_sha256']=r58.sha256_file(root/r58.R56_MANIFEST);wj(root/r58.R57_SEAL,seal);wj(root/r58.R57_SEAL_MANIFEST,{'final_seal_file':{'sha256':r58.sha256_file(root/r58.R57_SEAL)}});monkeypatch.setattr(r58,'EXPECTED_R57_FINAL_SEAL_SHA256',r58.sha256_file(root/r58.R57_SEAL));a=r58.reconcile(root);assert a['scientific_candidate_eligible'] is False;assert 'r56_schedule_class_recomputed_exact' in a['failed']
