from pathlib import Path
import argparse,json,numpy as np,sys
from arcana_worldsim.scientific_engines.r338_exchange_technology_cultural_genealogy import *
from arcana_worldsim.scientific_engines.r338_exchange_technology_cultural_genealogy import _close_manifest
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);out=root/'outputs'/'v0_6D1_R3_38';seal=root/'outputs'/'v0_6D1_R3_38_SEAL';seal.mkdir(parents=True,exist_ok=True);checks=[]
def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
try:
 inp=validate_inputs(root);_close_manifest(out,'R3_38_OUTPUT_MANIFEST.json');audit=load_json(out/'R3_38_INTEGRATED_AUDIT.json');auth=load_json(out/'R3_38_EXCHANGE_TECHNOLOGY_CULTURAL_GENEALOGY_AUTHORITY.json');outs=load_json(out/'R3_38_LINEAGE_TECHNOLOGY_OUTCOMES.json');gen=load_json(out/'R3_38_RETICULATE_CULTURAL_GENEALOGY.json');sens=load_json(out/'R3_38_SENSITIVITY_AND_ROBUSTNESS.json');z=np.load(out/'R3_38_CONCRETE_TECHNOLOGY_REPLAY.npz',allow_pickle=False);g=np.load(out/'R3_38_GROUP_IMPLEMENTATION_ANCHORS.npz',allow_pickle=False);r=np.load(out/'R3_38_REGIONAL_CULTURAL_NETWORKS.npz',allow_pickle=False);cfg=load_json(root/'configs/world1_r338_exchange_technology_cultural_genealogy_v0_6D1_R3_38.json')
 ck('parent_authorities_validate',inp['a37']['status']==PARENT_PASS and inp['a31']['status']==R331_PASS and inp['a32']['status']==R332_PASS and inp['a33']['status']==R333_PASS)
 ck('r337_pathway_exact',all(v=='DISTRIBUTED_MANAGED_FORAGER_ECONOMY' for v in inp['cp37']['resolved_lineage_economic_pathways'].values()))
 ck('output_manifest_closure',True)
 ck('integrated_audit_all_pass',audit['checks_failed']==0,[audit['checks_passed'],audit['checks_total']])
 ck('authority_parent_exact',auth['parent']==PARENT_PASS)
 ck('authority_window_exact',auth['window_ka']==[20.0,0.0])
 ck('authority_implementation_semantics','NOT_DIRECT_ARCHAEOLOGICAL_OBSERVATIONS' in auth['implementation_semantics'])
 ck('authority_material_limitation','EXPLICIT_GLOBAL_PRIOR' in auth['material_semantics'])
 ck('authority_genealogy_reticulate','HORIZONTAL_BORROWING' in auth['genealogy_semantics'])
 ck('parent_hashes_exact',auth['parent_hashes']['r331_technology_sha256']==sha256_file(inp['r31']/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz') and auth['parent_hashes']['r332_regional_sha256']==sha256_file(inp['r32']/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz') and auth['parent_hashes']['r333_environment_sha256']==sha256_file(inp['r33']/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz') and auth['parent_hashes']['r337_economy_sha256']==sha256_file(inp['r37']/'R3_37_MANAGED_FORAGER_ECONOMY_REPLAY.npz'))
 ck('implementation_keys_exact',set(z.files)=={'candidate_ids','parent_member_indices','age_ka','implementation_family_names','implementation_stock','material_affordance_names','material_affordance_time'})
 ck('candidate_order_exact',list(map(str,z['candidate_ids']))==EXPECTED_CANDIDATES)
 ck('member_mapping_exact',np.array_equal(z['parent_member_indices'],inp['z37']['parent_member_indices']))
 ck('time_axis_exact',np.array_equal(z['age_ka'],inp['z32']['age_ka']))
 ck('implementation_names_exact',list(map(str,z['implementation_family_names']))==IMPLEMENTATION_NAMES)
 ck('implementation_geometry',z['implementation_stock'].shape==(32,2,145,12))
 ck('implementation_numeric_finite',np.isfinite(z['implementation_stock']).all())
 ck('implementation_bounded',z['implementation_stock'].min()>=0 and z['implementation_stock'].max()<=1)
 ck('group_keys_exact',set(g.files)=={'candidate_ids','parent_member_indices','anchor_age_ka','implementation_family_names','group_implementation_support','group_material_affordance_names','group_material_affordance','group_active'})
 ck('group_anchor_exact',np.array_equal(g['anchor_age_ka'],inp['a32z']['anchor_age_ka']))
 ck('group_geometry',g['group_implementation_support'].shape==(32,2,9,48,12))
 ck('group_active_parent_exact',np.array_equal(g['group_active'],inp['a32z']['regional_active']))
 ck('group_numeric_finite',np.isfinite(g['group_implementation_support']).all() and np.isfinite(g['group_material_affordance']).all())
 ck('regional_keys_exact',set(r.files)=={'candidate_ids','parent_member_indices','anchor_age_ka','regional_state_variable_names','regional_state','regional_implementation_profile','regional_active','exchange_matrix','borrowing_inflow','fission_pressure','fusion_pressure','regional_distinctiveness'})
 ck('regional_state_names_exact',list(map(str,r['regional_state_variable_names']))==REGIONAL_STATE_NAMES)
 ck('regional_geometry',r['regional_implementation_profile'].shape==(32,2,9,6,12) and r['regional_state'].shape==(32,2,9,6,len(REGIONAL_STATE_NAMES)))
 ck('exchange_geometry',r['exchange_matrix'].shape==(32,9,12,12))
 ck('exchange_symmetric',np.max(np.abs(r['exchange_matrix']-np.swapaxes(r['exchange_matrix'],-1,-2)))<1e-12)
 ck('exchange_diagonal_zero',np.max(np.abs(np.diagonal(r['exchange_matrix'],axis1=-2,axis2=-1)))==0)
 ck('regional_numeric_finite',np.isfinite(r['regional_implementation_profile']).all() and np.isfinite(r['exchange_matrix']).all())
 ck('genealogy_stems_12',len(gen['stem_ids'])==12)
 ck('genealogy_reticulate',gen['reticulate_genealogy_materialized'] is True and gen['pure_tree_claimed'] is False)
 ck('vertical_continuity_count',gen['vertical_continuity_edges_count']==96)
 ck('sensitivity_12',sens['variant_count']==12)
 ck('sensitivity_no_selection',sens['selection_gate'] is False)
 ck('no_named_culture_language_religion',outs['named_culture_materialized'] is False and outs['language_materialized'] is False and outs['religion_materialized'] is False)
 ck('no_direct_archaeological_observation',outs['specific_archaeological_artifact_observation_claimed'] is False)
 ck('no_metallurgy',outs['metallurgy_materialized'] is False)
 ck('no_city_state',outs['city_state_materialized'] is False)
 ck('hard_material_prior_explicit',0<cfg['generic_hard_material_access_prior']<1 and cfg['governance']['generic_hard_material_access_is_explicit_prior_not_geology_observation'] is True)
 ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True)
 ck('no_unique_human_identity',cfg['governance']['unique_human_identity_materialized'] is False)
 ck('deep_off',cfg['governance']['deep_biological_coupling'] is False)
 ck('evidence_multisource',len(auth['evidence_basis'])>=9)
except Exception as e: ck('audit_exception',False,repr(e))
failed=[x for x in checks if not x['pass']];status=FINAL_PASS if not failed else 'FAIL_R338_FINAL_SEAL_AUDIT'
if not failed:
 paths={x['lineage_id']:x['resolved_cultural_network_pathway'] for x in outs['lineages']}
 nxt='CULTURAL_SYMBOLIC_MEMORY_LANGUAGE_PRECONDITIONS_AND_INTERLINEAGE_IDENTITY_DYNAMICS'
else: paths={};nxt='R338_REPAIR_REQUIRED'
res={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_REGIONAL_EXCHANGE_CONCRETE_TECHNOLOGY_AND_CULTURAL_GENEALOGY_AUTHORITY_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'FAIL','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'candidate_lineages':2,'implementation_families':12,'regional_stems':12,'resolved_cultural_network_pathways':paths,'robust_borrowing_edges':len(gen.get('robust_borrowing_edges',[])),'robust_fission_pressure_events':len(gen.get('robust_fission_pressure_events',[])),'robust_fusion_pressure_events':len(gen.get('robust_fusion_pressure_events',[])),'named_culture_language_religion_materialized':False,'metallurgy_city_state_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'next_stage':nxt},'checks':checks}
write_json(seal/'R3_38_FINAL_SEAL_AUDIT.json',res);(seal/'R3_38_FINAL_SEAL_AUDIT.md').write_text(f"# R3.38 Final Seal\n\n- Status: `{status}`\n- Checks: **{res['checks_passed']}/{res['checks_total']}**\n- Cultural-network pathways: `{res['summary']['resolved_cultural_network_pathways']}`\n",encoding='utf-8');files={}
for n in ['R3_38_FINAL_SEAL_AUDIT.json','R3_38_FINAL_SEAL_AUDIT.md']:
 q=seal/n;files[n]={'bytes':q.stat().st_size,'sha256':sha256_file(q)}
write_json(seal/'R3_38_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':status,'files':files});print(json.dumps(res,indent=2));sys.exit(1 if failed else 0)
