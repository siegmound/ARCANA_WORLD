from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines import r312_postcha1_diversity_recovery as r312
from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313

checks=[]
def ck(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})

def main():
 a=r313.validate_parent_r312_authority(ROOT); st=a['state']; cfg=r313.R313Config()
 ck('stage',r313.STAGE=='v0.6D1-R3.13'); ck('start_age',r313.START_AGE_MA==46.0); ck('end_age',r313.END_AGE_MA==30.0)
 ck('steps',r313.EXPECTED_STEPS==128); ck('parent_species',len(set(st.current_species))==104); ck('parent_components',len(st.component_ids)==223)
 ck('parent_json_hash',a['checkpoint_json_sha256']=='6189f16fd3d7b390ad33afb57eaa36fef0bdbcf7f1498fa7396d3d1f81843269')
 ck('parent_npz_hash',a['checkpoint_npz_sha256']=='92b410ce3258c44ba0f4b911776628d880fbe5a5fe3be3b9b6fe13dc34973948')
 counts=r313.event_counts(st); ck('cha1_extinction_cumulative',counts['CHA1_species_extinction']==212); ck('cha1_bridge_once',counts['CHA1_high_resolution_event_bridge_complete']==1); ck('thaw_once',counts['post_CHA1_ordinary_lifecycle_thaw']==1)
 parent=r312.R312Config()
 fields=['biology_cadence_years','transport_cadence_years','speciation_check_interval_years','ordinary_extinction_check_interval_years','ordinary_extinction_minimum_persistence_years','founder_minimum_persistence_years','vicariance_persistence_min_years','reconnection_persistence_min_years','mutation_variance_supply_normalized_per_myr','nonlinear_stabilizing_variance_depletion_per_myr_per_q','selection_variance_depletion_per_generation','variance_ceiling_normalized','migration_reference_years','migration_fraction_ceiling','gene_flow_ceiling_per_step','minimum_effective_isolation_generations','minimum_intrinsic_ri','minimum_trait_distance','maximum_effective_exchange_pressure','adaptive_k_eff','segregation_recombination_fraction_per_generation','deme_fission_check_interval_years','reconnection_check_interval_years']
 for f in fields: ck('param_'+f,getattr(cfg,f)==getattr(parent,f),[getattr(cfg,f),getattr(parent,f)])
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False); h=r313.validate_30ma_environment_handoff(a1,cfg)
 ck('handoff_exact',h['environmental_endpoint_identity_exact'])
 for f,d in h['fields'].items(): ck('handoff_'+f,d['exact'] and d['max_abs_error']==0.0,d)
 smoke=json.loads((ROOT/'local_runs/v0_6D1_R3_13/R3_13_SMOKE_SUMMARY.json').read_text(encoding='utf-8'))
 ck('smoke_verdict',smoke['verdict']=='PASS_R313_LONGTERM_REASSEMBLY_SMOKE__ORDINARY_CONTINUATION_VALID')
 run=smoke['run']; ck('smoke_steps',run['ordinary_biology_steps']==4); ck('smoke_age',run['end_age_ma']==45.5); ck('smoke_no_clipping',run['clipping_steps']==0 and run['clipping_contacts']==0)
 d=run['event_counts_delta']; ck('smoke_no_cha1',d['CHA1_species_extinction']==0 and d['CHA1_high_resolution_event_bridge_complete']==0); ck('smoke_no_thaw',d['post_CHA1_ordinary_lifecycle_thaw']==0)
 inv=run['invariants']; ck('smoke_population_nonnegative',inv['population_min']>=-1e-14); ck('smoke_inaccessible_zero',abs(inv['population_on_inaccessible_cells'])<=1e-12); ck('smoke_q_below_ceiling',inv['q_max']<=0.08+1e-12); ck('smoke_s_symmetric',inv['s_symmetry_max_abs']<=2e-12); ck('smoke_s_diag_zero',inv['s_diagonal_max_abs']<=2e-12); ck('smoke_s_nonnegative',inv['s_min']>=-2e-12)
 ck('smoke_serialization',smoke['serialization_identity']['equivalent'] is True)
 re=run['ecological_reassembly']; ck('no_crossguild_authority',re['cross_guild_recreation_authorized'] is False); ck('guild6_absent_recorded',6 in re['guilds_absent_at_end'])
 gov=smoke['governance']; ck('no_richness_target',gov['richness_target_used'] is False); ck('no_guild_target',gov['guild_target_used'] is False); ck('deep_off',gov['deep_biological_coupling'] is False); ck('no_crossguild_activation',gov['cross_guild_transition_operator_activated'] is False)
 passed=sum(x['pass'] for x in checks); out={'stage':r313.STAGE,'verdict':'PASS_R313_CANDIDATE_FORMAL_AUDIT' if passed==len(checks) else 'FAIL_R313_CANDIDATE_FORMAL_AUDIT','checks':f'{passed}/{len(checks)}','items':checks}
 p=ROOT/'outputs/v0_6D1_R3_13/FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_13.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps({'verdict':out['verdict'],'checks':out['checks'],'out':str(p)},indent=2)); return 0 if passed==len(checks) else 2
if __name__=='__main__': raise SystemExit(main())
