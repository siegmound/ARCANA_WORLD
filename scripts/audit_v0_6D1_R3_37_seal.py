from pathlib import Path
import argparse,json,numpy as np,sys
from arcana_worldsim.scientific_engines.r337_managed_forager_economy import *
from arcana_worldsim.scientific_engines.r337_managed_forager_economy import _close_manifest
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);out=root/'outputs'/'v0_6D1_R3_37';seal=root/'outputs'/'v0_6D1_R3_37_SEAL';seal.mkdir(parents=True,exist_ok=True);checks=[]
def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
try:
 inp=validate_inputs(root);_close_manifest(out,'R3_37_OUTPUT_MANIFEST.json');audit=load_json(out/'R3_37_INTEGRATED_AUDIT.json');auth=load_json(out/'R3_37_MANAGED_FORAGER_ECONOMY_AUTHORITY.json');outs=load_json(out/'R3_37_LINEAGE_ECONOMY_OUTCOMES.json');sens=load_json(out/'R3_37_SENSITIVITY_AND_ROBUSTNESS.json');cp=load_json(out/'R3_37_ECONOMY_PATHWAY_CHECKPOINT.json');z=np.load(out/'R3_37_MANAGED_FORAGER_ECONOMY_REPLAY.npz',allow_pickle=False);nodes=np.load(out/'R3_37_WEIGHTED_ECONOMIC_NODES.npz',allow_pickle=False);cfg=load_json(root/'configs/world1_r337_managed_forager_economy_v0_6D1_R3_37.json')
 ck('parent_authorities_validate',inp['a36']['status']==PARENT_PASS and inp['a30']['status']==R330_PASS and inp['a31']['status']==R331_PASS and inp['a32']['status']==R332_PASS)
 ck('r336_pathway_exact',inp['cp36']['resolved_pathway']=='INTENSIVE_MANAGED_FORAGER_PATHWAY')
 ck('output_manifest_closure',True)
 ck('integrated_audit_all_pass',audit['checks_failed']==0,[audit['checks_passed'],audit['checks_total']])
 ck('authority_parent_exact',auth['parent']==PARENT_PASS)
 ck('authority_window_exact',auth['window_ka']==[20.0,0.0])
 ck('authority_census_semantics','POSTERIOR' in auth['census_semantics'] and 'NOT_AN_ARCHAEOLOGICAL_HEADCOUNT' in auth['census_semantics'])
 ck('authority_settlement_semantics','NOT_A_VILLAGE' in auth['settlement_semantics'])
 ck('authority_inequality_semantics','DIAGNOSTIC_ONLY' in auth['inequality_semantics'])
 ck('parent_hashes_exact',auth['parent_hashes']['r330_census_sha256']==sha256_file(inp['r30']/'R3_30_CENSUS_AND_GROUP_TIMESERIES.npz') and auth['parent_hashes']['r331_technology_sha256']==sha256_file(inp['r31']/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz') and auth['parent_hashes']['r332_subsistence_sha256']==sha256_file(inp['r32']/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz') and auth['parent_hashes']['r336_replay_sha256']==sha256_file(inp['r36']/'R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz'))
 ck('replay_keys_exact',set(z.files)=={'candidate_ids','parent_member_indices','age_ka','economic_variable_names','economic_state','economy_census_multiplier','economy_coupled_census_equivalent','economy_coupled_group_count_equivalent','economy_coupled_group_mean_size','parent_census_equivalent'})
 ck('candidate_order_exact',list(map(str,z['candidate_ids']))==EXPECTED_CANDIDATES)
 ck('member_mapping_exact',np.array_equal(z['parent_member_indices'],inp['z36']['parent_member_indices']))
 ck('time_axis_exact',np.array_equal(z['age_ka'],inp['z32']['age_ka']))
 ck('economic_names_exact',list(map(str,z['economic_variable_names']))==ECON_NAMES)
 ck('economic_geometry',z['economic_state'].shape==(32,2,145,len(ECON_NAMES)))
 ck('economic_numeric_finite',np.isfinite(z['economic_state']).all())
 ck('economic_bounded',z['economic_state'].min()>=0 and z['economic_state'].max()<=1)
 ck('census_geometry',z['economy_coupled_census_equivalent'].shape==(32,2,145))
 ck('census_anchor_parent_exact',np.max(np.abs(z['economy_coupled_census_equivalent'][:,:,0]-z['parent_census_equivalent'][:,:,0]))<1e-9)
 ck('census_multiplier_bounds',z['economy_census_multiplier'].min()>=cfg['economy_census_multiplier_min']-1e-12 and z['economy_census_multiplier'].max()<=cfg['economy_census_multiplier_max']+1e-12)
 ck('group_census_closure',np.max(np.abs(z['economy_coupled_group_count_equivalent']*z['economy_coupled_group_mean_size']-z['economy_coupled_census_equivalent']))<1e-8)
 ck('node_keys_exact',set(nodes.files)=={'candidate_ids','parent_member_indices','anchor_age_ka','economic_node_variable_names','economic_node_state','economic_node_active'})
 ck('node_anchor_exact',np.array_equal(nodes['anchor_age_ka'],inp['a32z']['anchor_age_ka']))
 ck('node_names_exact',list(map(str,nodes['economic_node_variable_names']))==NODE_NAMES)
 ck('node_geometry',nodes['economic_node_state'].shape==(32,2,9,48,len(NODE_NAMES)))
 ck('node_active_exact_parent',np.array_equal(nodes['economic_node_active'],inp['a32z']['regional_active']))
 ck('node_numeric_finite',np.isfinite(nodes['economic_node_state']).all())
 ck('sensitivity_15',sens['variant_count']==15)
 ck('sensitivity_no_selection',sens['selection_gate'] is False)
 allowed={'DISTRIBUTED_MANAGED_FORAGER_ECONOMY','SEASONALLY_AGGREGATED_EXCHANGE_ECONOMY','PERSISTENT_CENTRAL_PLACE_FORAGER_ECONOMY','REGIONAL_COMPLEX_FORAGER_ECONOMY'}
 ck('pathway_enum',all(v in allowed for v in cp['resolved_lineage_economic_pathways'].values()),cp['resolved_lineage_economic_pathways'])
 ck('checkpoint_no_agriculture',cp['agriculture_materialized'] is False and cp['domesticated_species_materialized'] is False)
 ck('checkpoint_no_village_city_state',cp['village_materialized'] is False and cp['city_state_materialized'] is False)
 ck('checkpoint_no_class_hierarchy',cp['class_hierarchy_materialized'] is False)
 ck('checkpoint_no_currency_market',cp['currency_market_materialized'] is False)
 ck('no_unique_human_identity',cp['unique_human_identity_materialized'] is False)
 ck('deep_off',cp['deep_biological_coupling'] is False)
 ck('evidence_multisource',len(auth['evidence_basis'])>=9)
except Exception as e: ck('audit_exception',False,repr(e))
failed=[x for x in checks if not x['pass']];status=FINAL_PASS if not failed else 'FAIL_R337_FINAL_SEAL_AUDIT'
if not failed:
 pset=set(cp['resolved_lineage_economic_pathways'].values())
 if 'REGIONAL_COMPLEX_FORAGER_ECONOMY' in pset or 'PERSISTENT_CENTRAL_PLACE_FORAGER_ECONOMY' in pset: nxt='CONCRETE_SETTLEMENT_POLITICAL_ECONOMY_AND_SOCIAL_DIFFERENTIATION'
 else: nxt='REGIONAL_FORAGER_EXCHANGE_NETWORKS_CONCRETE_TECHNOLOGY_AND_CULTURAL_GENEALOGIES'
else: nxt='R337_REPAIR_REQUIRED'
res={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_INTENSIVE_MANAGED_FORAGER_DEMOGRAPHY_SETTLEMENT_AND_EXCHANGE_ECONOMY_AUTHORITY_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'FAIL','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'candidate_lineages':2,'resolved_lineage_economic_pathways':cp.get('resolved_lineage_economic_pathways',{}),'agriculture_materialized':False,'village_city_state_materialized':False,'class_hierarchy_materialized':False,'currency_market_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'next_stage':nxt},'checks':checks}
write_json(seal/'R3_37_FINAL_SEAL_AUDIT.json',res);(seal/'R3_37_FINAL_SEAL_AUDIT.md').write_text(f"# R3.37 Final Seal\n\n- Status: `{status}`\n- Checks: **{res['checks_passed']}/{res['checks_total']}**\n- Economic pathways: `{res['summary']['resolved_lineage_economic_pathways']}`\n",encoding='utf-8');files={}
for n in ['R3_37_FINAL_SEAL_AUDIT.json','R3_37_FINAL_SEAL_AUDIT.md']:
 q=seal/n;files[n]={'bytes':q.stat().st_size,'sha256':sha256_file(q)}
write_json(seal/'R3_37_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':status,'files':files});print(json.dumps(res,indent=2));sys.exit(1 if failed else 0)
