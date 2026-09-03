import json
from pathlib import Path
import pytest

from arcana_worldsim.scientific_engines.r37i_production_runtime import (
    NOMINAL_K_REFERENCE, R37IProductionConfig, SEAL_SCHEMA, validate_promotion_seal
)
from scripts.review_and_seal_v0_6D1_R3_7I import review_evidence, _materialize_seal


def fake_branch(label,k):
    return {
        'stage':'v0.6D1-R3.7H','branch_label':label,'K_eff':k,'biology_steps':480,'valid_biology_steps':True,
        'closed_loop_gate_pass':True,'clipping_contacts':0,'peak_q':0.047,'final_total_population':1800.0,
        'species_count':130,'component_count':400,'event_counts':{'deme_fission':100}
    }


def fake_summary():
    return {
        'stage':'v0.6D1-R3.7H',
        'comparison':{
            'all_branches_valid':True,'all_branches_clear_of_ceiling':True,'qualitative_ceiling_coherence':True,
            'peak_q_by_branch':{'K_LOW':.047,'K_CENTER':.046,'K_HIGH':.045},'max_peak_q_spread':.002,
            'final_population_by_branch':{'K_LOW':1800,'K_CENTER':1801,'K_HIGH':1802},
            'final_population_relative_span_vs_center':2/1801,
            'species_count_by_branch':{'K_LOW':130,'K_CENTER':130,'K_HIGH':131},
            'component_count_by_branch':{'K_LOW':400,'K_CENTER':401,'K_HIGH':402},
            'event_counts_by_branch':{'K_LOW':{},'K_CENTER':{},'K_HIGH':{}},
            'species_count_exactly_equal':False,'component_count_exactly_equal':False,'event_counts_exactly_equal':True,
        },
        'production_promotion_gate':{'governed_closed_loop_pass':True}
    }


def test_nominal_k_is_operational_reference_not_user_tunable_scalar():
    assert NOMINAL_K_REFERENCE == pytest.approx(38.470)
    R37IProductionConfig()
    with pytest.raises(ValueError): R37IProductionConfig(nominal_k_reference=37.614)


def test_review_accepts_valid_three_branch_evidence_without_macro_fitted_threshold():
    branches={'K_LOW':fake_branch('K_LOW',37.614),'K_CENTER':fake_branch('K_CENTER',38.470),'K_HIGH':fake_branch('K_HIGH',41.002)}
    out=review_evidence(fake_summary(),branches)
    assert out['promotion_eligible'] is True
    assert out['macro_and_event_divergence_review']['review_semantics']=='REPORTED_NOT_THRESHOLD_FITTED'


def test_review_fails_if_any_branch_clips():
    branches={'K_LOW':fake_branch('K_LOW',37.614),'K_CENTER':fake_branch('K_CENTER',38.470),'K_HIGH':fake_branch('K_HIGH',41.002)}
    branches['K_LOW']['clipping_contacts']=1
    out=review_evidence(fake_summary(),branches)
    assert out['promotion_eligible'] is False


def test_seal_keeps_scalar_k_physical_constant_denied(tmp_path):
    branches={'K_LOW':fake_branch('K_LOW',37.614),'K_CENTER':fake_branch('K_CENTER',38.470),'K_HIGH':fake_branch('K_HIGH',41.002)}
    review=review_evidence(fake_summary(),branches)
    seal=_materialize_seal(review,{'summary':'0','K_LOW':'1','K_CENTER':'2','K_HIGH':'3'},None)
    p=tmp_path/'seal.json'; p.write_text(json.dumps(seal),encoding='utf-8')
    loaded=validate_promotion_seal(p)
    assert loaded['authority']['canonical_runtime_binding_authorized'] is True
    assert loaded['authority']['scalar_k_physical_constant_authorized'] is False
    assert loaded['authority']['mu_b_or_ceiling_change_authorized'] is False


def test_runtime_refuses_missing_seal(tmp_path):
    with pytest.raises(RuntimeError): validate_promotion_seal(tmp_path/'missing.json')


def test_runtime_refuses_nonpass_seal(tmp_path):
    p=tmp_path/'seal.json'; p.write_text(json.dumps({'schema':SEAL_SCHEMA,'stage':'v0.6D1-R3.7I','status':'BLOCKED'}),encoding='utf-8')
    with pytest.raises(RuntimeError): validate_promotion_seal(p)
