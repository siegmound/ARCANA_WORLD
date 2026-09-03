from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r416_recovered_metric_target_protocol import recovered_metric_disposition,_target_protocol_record

def test_nemo_additive_variance_not_equated_to_heterozygosity():
    x=recovered_metric_disposition('additive_variance','NEMO','ALLELE_FREQUENCY_DERIVATIVES_RECOVERED_RAW_ONLY')
    assert x['adjudicative_promotion_authorized'] is False
    assert x['promotion_gate']=='TRANSFORM_REQUIRED_EFFECT_SIZE_MODEL_ABSENT'

def test_nemo_frequency_structure_not_called_gene_flow():
    x=recovered_metric_disposition('gene_flow','NEMO','ALLELE_FREQUENCY_DERIVATIVES_RECOVERED_RAW_ONLY')
    assert 'PROXY_ONLY' in x['promotion_gate']

def test_slim_fst_requires_population_and_time_binding():
    x=recovered_metric_disposition('producer_divergence','SLiM','TREE_SEQUENCE_DERIVATIVES_RECOVERED_RAW_ONLY')
    assert x['promotion_gate']=='CONDITIONAL_STRUCTURE_METRIC_REQUIRES_LABEL_AND_TIME_BINDING'
    assert x['promotion_performed'] is False

def test_cdmetapop_absolute_population_response_stays_proxy_only():
    x=recovered_metric_disposition('population_persistence','CDMetaPOP','SUMMARY_POPULATION_DERIVATIVES_RECOVERED_RAW_ONLY')
    assert x['promotion_gate']=='PROXY_ONLY_BY_R412_NEUTRAL_INVARIANCE_FAILURE'

def test_target_filename_hit_is_not_materialized_target():
    cfg=json.loads(Path('configs/world1_r416_recovered_metric_target_protocol_v0_6D1_R4_16.json').read_text())
    r=_target_protocol_record({'window_id':'W','domain':'gene_flow','candidate_artifact_hits':['outputs/x_gene_flow.json']},cfg['domain_protocols'])
    assert r['candidate_artifact_count']==1
    assert r['target_value_materialized'] is False
    assert r['adjudicative_target_authorized'] is False

def test_all_15_domains_have_protocols():
    cfg=json.loads(Path('configs/world1_r416_recovered_metric_target_protocol_v0_6D1_R4_16.json').read_text())
    expected={'additive_variance','admixture','ancestry','biomass','connectivity','extinction_risk','founder_persistence','gene_flow','managed_wild_isolation','population_persistence','producer_divergence','range_occupancy','range_shift_rate','trait_response','trophic_opportunity'}
    assert set(cfg['domain_protocols'])==expected

def test_r416_forbids_readjudication_and_engine_execution():
    cfg=json.loads(Path('configs/world1_r416_recovered_metric_target_protocol_v0_6D1_R4_16.json').read_text())
    assert cfg['engine_execution_performed'] is False
    assert cfg['rules']['no_readjudication_in_r416'] is True
    assert cfg['rules']['no_external_result_may_define_arcana_target'] is True
