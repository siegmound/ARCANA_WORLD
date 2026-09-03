from pathlib import Path
import hashlib,json,shutil
import numpy as np
from arcana_worldsim.state_query import r512_r331_abstract_technological_ecology_reconciliation as r512
from arcana_worldsim.scientific_engines import r331_cultural_technological_ecology as r331

def wj(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def man(base,names,status='PASS'):return {'status':status,'files':{n:{'bytes':(base/n).stat().st_size,'sha256':r512.sha256_file(base/n)} for n in names}}
def patch_hash(monkeypatch,name,p):monkeypatch.setattr(r512,name,r512.sha256_file(p))

def build_tree(tmp_path,monkeypatch):
 root=tmp_path; srcroot=Path(__file__).resolve().parents[1]
 # Current R5.12 config used by reconcile.
 q=root/r512.R512_CONFIG;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(srcroot/r512.R512_CONFIG,q)
 # R5.11 source authority files
 for rel,const in [(r512.R511_SOURCE_MODULE,'EXPECTED_R511_SOURCE_MODULE_SHA256'),(r512.R511_CONFIG,'EXPECTED_R511_CONFIG_SHA256'),(r512.R511_CONTRACT,'EXPECTED_R511_CONTRACT_SHA256')]:
  p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(srcroot/rel,p);patch_hash(monkeypatch,const,p)
 wj(root/r512.R511_SOURCE_MANIFEST,{'stage':'v0.6D1-R5.11','files':{}});patch_hash(monkeypatch,'EXPECTED_R511_SOURCE_MANIFEST_SHA256',root/r512.R511_SOURCE_MANIFEST)
 # R5.11 candidate outputs
 o11=root/r512.R511_OUT;o11.mkdir(parents=True)
 wj(root/r512.R511_AUDIT,{'status':'PASS_R511_R510_TO_R330_CENSUS_GROUP_ABM_RECONCILIATION_CANDIDATE','scientific_candidate_eligible':True,'checks_passed':36,'checks_total':36,'failed':[]})
 wj(root/r512.R511_HANDOFF,{'status':'R511_RECONCILED_CENSUS_EQUIVALENT_WEIGHTED_GROUP_HANDOFF_0KA','age_ka':0.0,'candidate_cohort':list(r512.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'literal_absolute_census_materialized':False,'person_level_abm_materialized':False,'ready_for_r331_reconciliation':True,'downstream_r331_auto_authorized':False})
 wj(root/r512.R511_BINDING,{'status':'R511_PARENT_AUTHORITY_BINDING'})
 wj(root/r512.R511_MANIFEST,man(o11,['R5_11_INTEGRATED_RECONCILIATION.json','R5_11_0KA_CENSUS_GROUP_RECONCILED_HANDOFF.json','R5_11_PARENT_AUTHORITY_BINDING.json']))
 # Exact R3.31 source copied into temp tree, source manifest closes it.
 for rel,const in [(r512.R331_SOURCE_MODULE,'EXPECTED_R331_SOURCE_MODULE_SHA256'),(r512.R331_CONFIG,'EXPECTED_R331_CONFIG_SHA256'),(r512.R331_CONTRACT,'EXPECTED_R331_CONTRACT_SHA256')]:
  p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(srcroot/rel,p);patch_hash(monkeypatch,const,p)
 smfiles={}
 for rel in [r512.R331_SOURCE_MODULE,r512.R331_CONFIG,r512.R331_CONTRACT]:
  p=root/rel;smfiles[rel.as_posix()]={'bytes':p.stat().st_size,'sha256':r512.sha256_file(p)}
 wj(root/r512.R331_SOURCE_MANIFEST,{'stage':'v0.6D1-R3.31','files':smfiles});patch_hash(monkeypatch,'EXPECTED_R331_SOURCE_MANIFEST_SHA256',root/r512.R331_SOURCE_MANIFEST)
 # Synthetic exact R3.29/R3.30 parents.
 ids=np.array(r512.TARGET_COHORT);members=np.arange(0,96,3,dtype=int)
 ages=np.arange(50.,-1.,-1.);extra=np.linspace(49.75,0.25,124);ages=np.sort(np.unique(np.concatenate([ages,extra])))[::-1];assert len(ages)==175;anchors=np.array([50.,30.,20.,15.,14.,13.,12.,11.,10.,5.,0.])
 cn=np.array(['population_support_norm','residential_mobility_index','aggregation_potential','network_connectivity','cultural_transmission_support','cumulative_culture_precondition_stock','settlement_persistence_potential','resource_stress_proxy','interlineage_exchange_opportunity','cha2_community_disruption'])
 C=np.zeros((32,2,175,10),np.float32);C[...,0]=.5;C[...,1]=.35;C[...,2]=.45;C[...,3]=.55;C[...,4]=.6;C[...,5]=.4;C[...,6]=.5;C[...,7]=.2;C[...,8]=.1;C[...,9]=.05
 fn=np.array(['social_learning','coordination','mobility','flexibility','development','cognition']);F=np.full((32,2,6),.55,np.float32)
 (root/r512.R329_REPLAY).parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(root/r512.R329_REPLAY,candidate_ids=ids,parent_member_indices=members,age_ka=ages,community_variable_names=cn,community_summary=C,functional_prior_names=fn,functional_priors=F,anchor_age_ka=anchors)
 census=np.zeros((32,2,175,6),float);census[...,0]=1000.;census[...,2]=40.
 (root/r512.R330_CENSUS).parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(root/r512.R330_CENSUS,candidate_ids=ids,parent_member_indices=members,age_ka=ages,census_group_series=census)
 av=np.array(['represented_people','represented_camps','mean_group_size','deme_id','grid_row','grid_col','community_viability','network_access','culture_stock','resource_stress','interlineage_exchange','cha2_disruption'])
 A=np.zeros((32,2,11,48,12),float);AA=np.zeros((32,2,11,48),np.uint8);A[:,:,:,0,0]=1000.;A[:,:,:,0,1]=40.;A[:,:,:,0,7]=.55;A[:,:,:,0,8]=.4;A[:,:,:,0,9]=.2;A[:,:,:,0,10]=.1;AA[:,:,:,0]=1
 np.savez_compressed(root/r512.R330_GROUP,candidate_ids=ids,parent_member_indices=members,anchor_age_ka=anchors,agent_variable_names=av,agent_state=A,agent_active=AA)
 patch_hash(monkeypatch,'EXPECTED_R329_REPLAY_SHA256',root/r512.R329_REPLAY);patch_hash(monkeypatch,'EXPECTED_R330_CENSUS_SHA256',root/r512.R330_CENSUS);patch_hash(monkeypatch,'EXPECTED_R330_GROUP_SHA256',root/r512.R330_GROUP)
 # Generate R3.31 arrays using frozen code.
 cfg331=json.loads((root/r512.R331_CONFIG).read_text());inp={'z29':np.load(root/r512.R329_REPLAY,allow_pickle=False),'z30':np.load(root/r512.R330_CENSUS,allow_pickle=False),'g30':np.load(root/r512.R330_GROUP,allow_pickle=False)}
 tech=r331.replay_technology(inp,cfg331);grp=r331.build_group_anchors(inp,tech);outs,sens=r331.summarize(inp,cfg331,tech,grp)
 o31=root/r512.R331_OUT;o31.mkdir(parents=True)
 np.savez_compressed(root/r512.R331_REPLAY,candidate_ids=ids,parent_member_indices=members,age_ka=ages,technology_domain_names=np.array(r331.TECH_NAMES),technology_domain_stock=tech['domain_stock'],ecology_variable_names=np.array(r331.ECO_NAMES),cultural_technological_ecology=tech['ecology'])
 np.savez_compressed(root/r512.R331_GROUP,candidate_ids=ids,parent_member_indices=members,anchor_age_ka=anchors,group_variable_names=np.array(r331.GROUP_NAMES),group_state=grp['group_state'],group_active=grp['group_active'])
 auth={'technology_semantics':'ABSTRACT_FUNCTIONAL_TECHNOLOGY_DOMAIN_STOCK_NOT_SPECIFIC_ARCHAEOLOGICAL_ARTIFACT','culture_semantics':'TRANSMISSION_RETENTION_AND_CUMULATION_ECOLOGY_NOT_NAMED_CULTURE_OR_LANGUAGE','dynamics':{'innovation_rate_per_kyr':.055,'loss_rate_per_kyr':.032,'cross_lineage_transfer_rate_per_kyr':.018,'repertoire_operational_threshold':.4},'specific_artifact_materialized':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False,'ethnicity_materialized':False,'named_culture_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'evidence_basis':{f'E{i}':{} for i in range(8)}}
 wj(root/r512.R331_AUTHORITY,auth);wj(root/r512.R331_CHECKPOINT,{'candidate_cohort':list(r512.TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False});wj(root/r512.R331_OUTCOMES,outs);wj(root/r512.R331_SENSITIVITY,sens);wj(root/r512.R331_AUDIT,{'status':'PASS_R331_CULTURAL_TECHNOLOGICAL_ECOLOGY_CANDIDATE','checks_passed':27,'checks_total':27,'checks_failed':0});(o31/'R3_31_AUDIT.md').write_text('# audit\n')
 names=['R3_31_AUDIT.md','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY.json','R3_31_LINEAGE_TECHNOLOGICAL_ECOLOGY_OUTCOMES.json','R3_31_SENSITIVITY_AND_ROBUSTNESS.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz','R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz','R3_31_INTEGRATED_AUDIT.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json']
 wj(root/r512.R331_OUTPUT_MANIFEST,man(o31,names,'PASS_R331_CULTURAL_TECHNOLOGICAL_ECOLOGY_CANDIDATE'))
 for rel,const in [(r512.R331_REPLAY,'EXPECTED_R331_REPLAY_SHA256'),(r512.R331_GROUP,'EXPECTED_R331_GROUP_SHA256'),(r512.R331_AUTHORITY,'EXPECTED_R331_AUTHORITY_SHA256'),(r512.R331_CHECKPOINT,'EXPECTED_R331_CHECKPOINT_SHA256'),(r512.R331_OUTCOMES,'EXPECTED_R331_OUTCOMES_SHA256'),(r512.R331_SENSITIVITY,'EXPECTED_R331_SENSITIVITY_SHA256'),(r512.R331_AUDIT,'EXPECTED_R331_AUDIT_SHA256'),(r512.R331_OUTPUT_MANIFEST,'EXPECTED_R331_OUTPUT_MANIFEST_SHA256')]:patch_hash(monkeypatch,const,root/rel)
 s=root/r512.R331_SEAL_OUT;s.mkdir(parents=True);wj(root/r512.R331_SEAL_AUDIT,{'verdict':'SEALED','status':'PASS_R331_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY_TRANSMISSION_RETENTION_AND_TECHNICAL_REPERTOIRE_SEALED','checks_passed':29,'checks_failed':0});wj(root/r512.R331_SEAL_MANIFEST,{'files':{'R3_31_FINAL_SEAL_AUDIT.json':{'bytes':(root/r512.R331_SEAL_AUDIT).stat().st_size,'sha256':r512.sha256_file(root/r512.R331_SEAL_AUDIT)}}});patch_hash(monkeypatch,'EXPECTED_R331_FINAL_SEAL_AUDIT_SHA256',root/r512.R331_SEAL_AUDIT);patch_hash(monkeypatch,'EXPECTED_R331_FINAL_SEAL_MANIFEST_SHA256',root/r512.R331_SEAL_MANIFEST)
 return root

def test_r512_passes_and_emits_abstract_handoff(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);a=r512.reconcile(root);assert a['scientific_candidate_eligible'] and a['checks_passed']==a['checks_total'];h=json.loads((root/r512.OUT_REL/'R5_12_0KA_ABSTRACT_TECHNOLOGICAL_ECOLOGY_RECONCILED_HANDOFF.json').read_text());assert h['candidate_cohort']==list(r512.TARGET_COHORT);assert h['specific_artifact_inventory_materialized'] is False;assert h['downstream_r332_auto_authorized'] is False

def test_domain_stock_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch)
 with np.load(root/r512.R331_REPLAY,allow_pickle=False) as z:d={k:z[k] for k in z.files}
 d['technology_domain_stock']=d['technology_domain_stock'].copy();d['technology_domain_stock'][0,0,0,0]+=.01;np.savez_compressed(root/r512.R331_REPLAY,**d);patch_hash(monkeypatch,'EXPECTED_R331_REPLAY_SHA256',root/r512.R331_REPLAY);wj(root/r512.R331_OUTPUT_MANIFEST,man(root/r512.R331_OUT,['R3_31_AUDIT.md','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY.json','R3_31_LINEAGE_TECHNOLOGICAL_ECOLOGY_OUTCOMES.json','R3_31_SENSITIVITY_AND_ROBUSTNESS.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz','R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz','R3_31_INTEGRATED_AUDIT.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json'],'PASS'));patch_hash(monkeypatch,'EXPECTED_R331_OUTPUT_MANIFEST_SHA256',root/r512.R331_OUTPUT_MANIFEST)
 a=r512.reconcile(root);assert not a['scientific_candidate_eligible'];assert 'r331_deterministic_domain_stock_replay_exact' in a['failed']

def test_specific_artifact_semantic_drift_fails_closed(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);o=json.loads((root/r512.R331_AUTHORITY).read_text());o['specific_artifact_materialized']=True;wj(root/r512.R331_AUTHORITY,o);patch_hash(monkeypatch,'EXPECTED_R331_AUTHORITY_SHA256',root/r512.R331_AUTHORITY);wj(root/r512.R331_OUTPUT_MANIFEST,man(root/r512.R331_OUT,['R3_31_AUDIT.md','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY.json','R3_31_LINEAGE_TECHNOLOGICAL_ECOLOGY_OUTCOMES.json','R3_31_SENSITIVITY_AND_ROBUSTNESS.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz','R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz','R3_31_INTEGRATED_AUDIT.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json'],'PASS'));patch_hash(monkeypatch,'EXPECTED_R331_OUTPUT_MANIFEST_SHA256',root/r512.R331_OUTPUT_MANIFEST)
 a=r512.reconcile(root);assert not a['scientific_candidate_eligible'];assert 'r331_no_specific_artifact_or_named_invention' in a['failed']

def test_r511_unique_identity_drift_blocks_parent(tmp_path,monkeypatch):
 root=build_tree(tmp_path,monkeypatch);h=json.loads((root/r512.R511_HANDOFF).read_text());h['unique_human_identity_materialized']=True;wj(root/r512.R511_HANDOFF,h);wj(root/r512.R511_MANIFEST,man(root/r512.R511_OUT,['R5_11_INTEGRATED_RECONCILIATION.json','R5_11_0KA_CENSUS_GROUP_RECONCILED_HANDOFF.json','R5_11_PARENT_AUTHORITY_BINDING.json']))
 a=r512.reconcile(root);assert not a['scientific_candidate_eligible'];assert 'parent_authority_pass' in a['failed']
