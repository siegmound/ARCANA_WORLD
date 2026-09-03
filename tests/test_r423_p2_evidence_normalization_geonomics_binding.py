from pathlib import Path
import json
import numpy as np

from arcana_worldsim.scientific_engines.r423_p2_evidence_normalization_geonomics_binding import (
    summarize, normalize_raw, build_p2_cell_candidate_registry, build_geonomics_binding_registry,
    J14, J18, J21,
)


def _audit(engine='NEMO', job='J', window='W'):
    return {'engine':engine,'job_id':job,'window_id':window,'raw_evidence_sha256':'abc','exact_seed_ledger_match':True}


def test_summary_quantiles_deterministic():
    s=summarize([1,2,3,4])
    assert s['n']==4
    assert s['median']==2.5
    assert abs(s['q10']-1.3)<1e-12
    assert abs(s['q90']-3.7)<1e-12


def test_cdmetapop_matched_control_is_candidate_not_auto_promoted():
    raw={'replicates':[{'dynamic':{'population_response_ratio':0.8+i*0.01},'neutral':{'population_response_ratio':0.9+i*0.01},'matched_control_population_effect_ratio':0.9+i*0.01} for i in range(4)]}
    n=normalize_raw(_audit('CDMetaPOP'),raw)
    m=n['normalized_metrics']['matched_control_population_effect_ratio']
    assert m['summary']['n']==4
    assert m['comparability_disposition']=='NORMALIZABLE_CANDIDATE_PENDING_ARCANA_CAUSAL_TARGET'
    assert n['adjudicative_promotion_authorized_in_r423'] is False


def test_nemo_and_slim_semantic_inequalities_remain_context_only():
    nraw={'replicates':[{'metrics':{'mean_expected_heterozygosity':0.2,'mean_population_frequency_range':0.4}} for _ in range(4)]}
    n=normalize_raw(_audit('NEMO'),nraw)
    assert n['normalized_metrics']['mean_expected_heterozygosity']['comparability_disposition'].startswith('CONTEXT_ONLY')
    sraw={'replicates':[{'metrics':{'global_diversity_per_site':0.01,'fst_between_current_population_samples':0.2}} for _ in range(4)]}
    s=normalize_raw(_audit('SLiM'),sraw)
    assert s['normalized_metrics']['fst_between_current_population_samples']['comparability_disposition'].startswith('CONTEXT_ONLY')


def test_p2_cell_candidate_only_cdmetapop_population_persistence_gets_gate_candidate():
    norm={'records':[
        {'engine':'CDMetaPOP','window_id':'W1','job_id':'J1','normalized_metrics':{'matched_control_population_effect_ratio':{}}},
        {'engine':'NEMO','window_id':'W2','job_id':'J2','normalized_metrics':{'mean_expected_heterozygosity':{}}},
    ]}
    p2={'cells':[
        {'static_validation_pass':True,'engine':'CDMetaPOP','window_id':'W1','domain':'population_persistence','source_stage':'R4.17'},
        {'static_validation_pass':True,'engine':'NEMO','window_id':'W2','domain':'additive_variance','source_stage':'R4.15-R1'},
    ]}
    r=build_p2_cell_candidate_registry(p2,norm)
    assert r['cell_count']==2
    assert r['semantic_promotion_gate_candidate_count']==1
    assert all(x['adjudicative_in_r423'] is False for x in r['records'])


def _write_npz(root:Path):
    (root/'outputs/v0_6D1_R3_27').mkdir(parents=True)
    np.savez(root/'outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz',
             age_ma=np.array([3.0,0.2]), state=np.zeros((1,1,2,2)), candidate_ids=np.array(['a']), variable_names=np.array(['effective_population','deme_count']))
    (root/'outputs/v0_6D1_R3_28').mkdir(parents=True)
    state_names=np.array(['population_proxy','grid_row','grid_col','local_suitability','genetic_diversity_proxy','adaptive_integration','lineage0_ancestry_fraction'])
    np.savez(root/'outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz',
             snapshot_age_ka=np.array([200.,0.]), snapshot_deme_state=np.zeros((1,1,2,2,7)), snapshot_active=np.ones((1,1,2,2),dtype=np.uint8), state_variable_names=state_names)
    (root/'outputs/v0_6D1_R3_33').mkdir(parents=True)
    np.savez(root/'outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz',
             anchor_age_ka=np.array([20.,0.]), environment_fields=np.zeros((2,2,2,1)), environment_variable_names=np.array(['resource']))
    (root/'outputs/v0_6D1_R3_34').mkdir(parents=True)
    np.savez(root/'outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz',
             anchor_age_ka=np.array([20.,0.]), producer_landscape=np.zeros((2,2,2,1)), landscape_variable_names=np.array(['producer']))
    (root/'local_runs/v0_6D1_R3_15').mkdir(parents=True)
    np.savez(root/'local_runs/v0_6D1_R3_15/WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.npz',
             population=np.zeros((1,2,2)),current_accessible=np.ones((2,2),dtype=np.uint8),lat=np.array([0.,1.]),lon=np.array([0.,1.]))


def test_geonomics_binding_freezes_two_and_keeps_j14_deferred(tmp_path):
    _write_npz(tmp_path)
    g=build_geonomics_binding_registry(tmp_path)
    assert g['record_count']==3
    assert g['binding_translation_materialized_count']==2
    assert g['binding_deferred_count']==1
    assert g['j14_pre_200ka_spatial_authority_gap_confirmed'] is True
    assert g['geonomics_execution_authorized_in_r423'] is False
    by={r['job_id']:r for r in g['records']}
    assert by[J14]['binding_materialized'] is False
    assert by[J18]['binding_materialized'] is True
    assert by[J21]['binding_materialized'] is True


def test_geonomics_j18_requires_explicit_grid_fields(tmp_path):
    _write_npz(tmp_path)
    p=tmp_path/'outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz'
    np.savez(p,snapshot_age_ka=np.array([200.,0.]),snapshot_deme_state=np.zeros((1,1,2,2,2)),snapshot_active=np.ones((1,1,2,2),dtype=np.uint8),state_variable_names=np.array(['population_proxy','local_suitability']))
    g=build_geonomics_binding_registry(tmp_path)
    by={r['job_id']:r for r in g['records']}
    assert by[J18]['binding_materialized'] is False
    assert g['geonomics_execution_authorized_in_r423'] is False
