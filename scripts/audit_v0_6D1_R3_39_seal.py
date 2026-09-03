from pathlib import Path
import argparse,json,numpy as np,sys
from arcana_worldsim.scientific_engines.r339_symbolic_memory_language_identity import *
from arcana_worldsim.scientific_engines.r339_symbolic_memory_language_identity import _close_manifest,_aggregate_r32_continuity
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);out=root/'outputs'/'v0_6D1_R3_39';seal=root/'outputs'/'v0_6D1_R3_39_SEAL';seal.mkdir(parents=True,exist_ok=True);checks=[]
def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
try:
 inp=validate_inputs(root);_close_manifest(out,'R3_39_OUTPUT_MANIFEST.json');audit=load_json(out/'R3_39_INTEGRATED_AUDIT.json');auth=load_json(out/'R3_39_SYMBOLIC_MEMORY_LANGUAGE_IDENTITY_AUTHORITY.json');outs=load_json(out/'R3_39_LINEAGE_SYMBOLIC_LANGUAGE_IDENTITY_OUTCOMES.json');mem=load_json(out/'R3_39_SYMBOLIC_MEMORY_EVENT_LEDGER.json');sens=load_json(out/'R3_39_SENSITIVITY_AND_ROBUSTNESS.json');z=np.load(out/'R3_39_SYMBOLIC_MEMORY_REPLAY.npz',allow_pickle=False);h=np.load(out/'R3_39_CHA2_REGIONAL_MEMORY_BINDING.npz',allow_pickle=False);r=np.load(out/'R3_39_REGIONAL_SYMBOLIC_LANGUAGE_IDENTITY_ANCHORS.npz',allow_pickle=False);cfg=load_json(root/'configs/world1_r339_symbolic_memory_language_identity_v0_6D1_R3_39.json')
 ck('parent_authorities_validate',inp['a38']['status']==PARENT_PASS and inp['a29']['status']==R329_PASS and inp['s20']['verdict']==R320_PASS)
 ck('output_manifest_closure',True)
 ck('integrated_audit_all_pass',audit['checks_failed']==0,[audit['checks_passed'],audit['checks_total']])
 ck('authority_parent_exact',auth['parent']==PARENT_PASS)
 ck('authority_window_exact',auth['window_ka']==[20.0,0.0])
 ck('authority_cha2_direct','DIRECT_R320_80_STATE_50_YEAR' in auth['cha2_binding'])
 ck('authority_symbolic_semantics','NOT_A_NAMED_MYTH' in auth['symbolic_memory_semantics'])
 ck('authority_identity_semantics','NOT_ETHNICITY' in auth['identity_semantics'])
 ck('authority_language_semantics','PRECONDITIONS_ONLY' in auth['language_semantics'])
 ck('parent_hashes_exact',auth['parent_hashes']['r338_regional_network_sha256']==sha256_file(inp['r38']/'R3_38_REGIONAL_CULTURAL_NETWORKS.npz') and auth['parent_hashes']['r338_technology_sha256']==sha256_file(inp['r38']/'R3_38_CONCRETE_TECHNOLOGY_REPLAY.npz') and auth['parent_hashes']['r329_community_sha256']==sha256_file(inp['r29']/'R3_29_COMMUNITY_NETWORK_REPLAY.npz') and auth['parent_hashes']['r332_regional_sha256']==sha256_file(inp['r32']/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz') and auth['parent_hashes']['r320_cha2_hazard_sha256']==sha256_file(inp['hzp']))
 ck('symbolic_keys_exact',set(z.files)=={'candidate_ids','parent_member_indices','age_ka','symbolic_state_variable_names','regional_symbolic_state'})
 ck('candidate_order_exact',list(map(str,z['candidate_ids']))==EXPECTED_CANDIDATES)
 ck('member_mapping_exact',np.array_equal(z['parent_member_indices'],inp['z38']['parent_member_indices']))
 ck('time_axis_exact',np.array_equal(z['age_ka'],inp['t38']['age_ka']))
 ck('symbolic_names_exact',list(map(str,z['symbolic_state_variable_names']))==SYMBOLIC_STATE_NAMES)
 ck('symbolic_geometry',z['regional_symbolic_state'].shape==(32,2,145,6,10))
 ck('symbolic_numeric_finite',np.isfinite(z['regional_symbolic_state']).all())
 ck('symbolic_bounded',z['regional_symbolic_state'].min()>=0 and z['regional_symbolic_state'].max()<=1)
 ck('cha2_keys_exact',set(h.files)=={'candidate_ids','parent_member_indices','cha2_age_ka','cha2_exposure_variable_names','regional_position','regional_cha2_exposure','composite_event_severity'})
 ck('cha2_axis_exact',h['cha2_age_ka'].shape==(80,) and h['cha2_age_ka'][0]==14.95 and h['cha2_age_ka'][-1]==11.0)
 ck('cha2_names_exact',list(map(str,h['cha2_exposure_variable_names']))==CHA2_EXPOSURE_NAMES)
 ck('cha2_geometry',h['regional_cha2_exposure'].shape==(32,2,80,6,5) and h['regional_position'].shape==(32,2,80,6,2))
 ck('cha2_numeric_finite',np.isfinite(h['regional_cha2_exposure']).all() and np.isfinite(h['composite_event_severity']).all())
 ck('cha2_direct_source_hash',sha256_file(inp['hzp'])==inp['s20']['canonical_artifacts']['hazard_npz_sha256'])
 ck('pre_event_memory_zero',np.max(z['regional_symbolic_state'][:,:,z['age_ka']>14.95,:,0])==0)
 ck('regional_keys_exact',set(r.files)=={'candidate_ids','parent_member_indices','anchor_age_ka','regional_anchor_variable_names','regional_anchor_state'})
 ck('regional_names_exact',list(map(str,r['regional_anchor_variable_names']))==REGIONAL_ANCHOR_NAMES)
 ck('regional_geometry',r['regional_anchor_state'].shape==(32,2,9,6,len(REGIONAL_ANCHOR_NAMES)))
 ck('regional_anchor_exact',np.array_equal(r['anchor_age_ka'],inp['z38']['anchor_age_ka']))
 # independently reconstruct first six anchor columns from parents
 rs=np.asarray(inp['z38']['regional_state'],float);rn=list(map(str,inp['z38']['regional_state_variable_names']));cont=_aggregate_r32_continuity(inp);base=np.stack([rs[...,rn.index('represented_people')],rs[...,rn.index('represented_camps')],rs[...,rn.index('grid_row')],rs[...,rn.index('grid_col')],rs[...,rn.index('regional_lineage_code')],cont],axis=-1)
 ck('regional_parent_columns_recomputed',np.max(np.abs(r['regional_anchor_state'][...,:6]-base))<1e-12)
 ck('sensitivity_12',sens['variant_count']==12)
 ck('sensitivity_no_selection',sens['selection_gate'] is False)
 ck('memory_ledger_not_myth',mem['named_myth_materialized'] is False and all(e['named_myth_claimed'] is False for e in mem['robust_persistent_cha2_event_memory_stems']))
 ck('no_religion',outs['religion_materialized'] is False)
 ck('no_ethnicity',outs['ethnicity_materialized'] is False)
 ck('no_language',outs['language_materialized'] is False and outs['named_language_family_materialized'] is False)
 ck('no_unique_human_identity',outs['unique_human_identity_materialized'] is False)
 ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True)
 ck('deep_off',cfg['governance']['deep_biological_coupling'] is False)
 ck('evidence_multisource',len(auth['evidence_basis'])>=9)
except Exception as e: ck('audit_exception',False,repr(e))
failed=[x for x in checks if not x['pass']];status=FINAL_PASS if not failed else 'FAIL_R339_FINAL_SEAL_AUDIT'
paths={x['lineage_id']:x['resolved_symbolic_language_identity_pathway'] for x in outs['lineages']} if not failed else {}
nxt='SYMBOLIC_TRADITIONS_LANGUAGE_DIVERGENCE_REASSESSMENT_AND_NAMED_CULTURE_GATE' if not failed else 'R339_REPAIR_REQUIRED'
res={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_CULTURAL_SYMBOLIC_MEMORY_LANGUAGE_PRECONDITIONS_AND_INTERLINEAGE_IDENTITY_AUTHORITY_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'FAIL','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'candidate_lineages':2,'regional_stems':12,'cha2_direct_50y_states':80,'resolved_symbolic_language_identity_pathways':paths,'robust_persistent_cha2_memory_stems':len(mem.get('robust_persistent_cha2_event_memory_stems',[])),'named_myth_religion_ethnicity_language_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'next_stage':nxt},'checks':checks}
write_json(seal/'R3_39_FINAL_SEAL_AUDIT.json',res);(seal/'R3_39_FINAL_SEAL_AUDIT.md').write_text(f"# R3.39 Final Seal\n\n- Status: `{status}`\n- Checks: **{res['checks_passed']}/{res['checks_total']}**\n- Pathways: `{res['summary']['resolved_symbolic_language_identity_pathways']}`\n- Persistent CHA-2 memory stems: **{res['summary']['robust_persistent_cha2_memory_stems']}**\n",encoding='utf-8');files={}
for n in ['R3_39_FINAL_SEAL_AUDIT.json','R3_39_FINAL_SEAL_AUDIT.md']:
 q=seal/n;files[n]={'bytes':q.stat().st_size,'sha256':sha256_file(q)}
write_json(seal/'R3_39_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':status,'files':files});print(json.dumps(res,indent=2));sys.exit(1 if failed else 0)
