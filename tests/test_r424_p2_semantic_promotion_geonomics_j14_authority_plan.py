from arcana_worldsim.scientific_engines.r424_p2_semantic_promotion_geonomics_j14_authority_plan import (
    build_semantic_gate, build_geonomics_authority_plan, J14, J18, J21,
)


def test_zero_parent_candidates_close_four_nonadjudicative():
    p={'records':[
        {'window_id':'W1','domain':'additive_variance','engine':'NEMO','disposition':'CONTEXT_ONLY_SEMANTIC_MISMATCH','reason':'HETEROZYGOSITY_IS_NOT_ADDITIVE_VARIANCE'},
        {'window_id':'W2','domain':'admixture','engine':'CDMetaPOP','disposition':'NO_AUTHORIZED_DOMAIN_METRIC_FROM_R422_NORMALIZATION','reason':'NO_EXPLICIT_DOMAIN_IDENTITY_TRANSFORM_FROZEN'},
        {'window_id':'W3','domain':'managed_wild_isolation','engine':'SLiM','disposition':'NO_AUTHORIZED_DOMAIN_METRIC_FROM_R422_NORMALIZATION'},
        {'window_id':'W3','domain':'producer_divergence','engine':'SLiM','disposition':'NO_AUTHORIZED_DOMAIN_METRIC_FROM_R422_NORMALIZATION'},
    ]}
    g=build_semantic_gate(p)
    assert g['record_count']==4
    assert g['parent_semantic_promotion_candidate_count']==0
    assert g['adjudicative_promotion_count']==0
    assert g['terminal_nonadjudicative_closure_count']==4
    assert all(r['numeric_reinterpretation_authorized'] is False for r in g['records'])


def test_unexpected_candidate_fails_closed_not_promoted():
    g=build_semantic_gate({'records':[{'disposition':'R424_SEMANTIC_PROMOTION_GATE_CANDIDATE'}]})
    assert g['parent_semantic_promotion_candidate_count']==1
    assert g['adjudicative_promotion_count']==0
    assert g['status'].startswith('BLOCKED_')


def _geo():
    return {'j14_pre_200ka_spatial_authority_gap_confirmed':True,'records':[
        {'job_id':J14,'binding_materialized':False},
        {'job_id':J18,'binding_materialized':True},
        {'job_id':J21,'binding_materialized':True},
    ]}


def test_geonomics_plan_preserves_gap_and_two_bindings():
    p=build_geonomics_authority_plan(_geo())
    assert p['j14_parent_gap_confirmed'] is True
    assert p['j18_binding_translation_preserved'] is True
    assert p['j21_binding_translation_preserved'] is True
    assert len(p['closure_routes_in_priority_order'])==3
    assert p['geonomics_execution_authorized_in_r424'] is False


def test_geonomics_plan_forbids_result_selected_shortcuts():
    p=build_geonomics_authority_plan(_geo())
    text=' '.join(p['forbidden_shortcuts'])
    assert 'SYNTHESIZE_3MA_SPATIAL_COORDINATES' in text
    assert 'MUTATE_R4_2_J14' in text
    assert 'EXTERNAL_ENGINE_RESULTS' in text


def test_geonomics_missing_j18_binding_blocks_plan():
    g=_geo(); g['records'][1]['binding_materialized']=False
    p=build_geonomics_authority_plan(g)
    assert p['status'].startswith('BLOCKED_')
