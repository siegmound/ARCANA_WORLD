from __future__ import annotations
from arcana_worldsim.state_query import r52_seal as s


def _row(cid='RPT_010_D02',fid='F1',hab='LAND_SUPPORT_UPPER_BOUND',mov='D1_STANDARDIZED_1_CELL_CHARACTERISTIC',both=True,any_=True):
    return {
        'candidate_id':cid,'family_id':fid,'habitat_profile':hab,'movement_profile':mov,
        'seed_membership':[520201,520202],'seed_membership_exact':True,
        'both_seeds_final_target_intersection':both,'any_seed_final_target_intersection':any_,
        'target_intersection_state_fraction_minmax':[0.1,0.4],
        'max_jaccard_minmax':[0.2,0.5],
        'max_target_coverage_fraction_minmax':[0.3,0.8],
        'automatic_scientific_pass_fail_from_values':False,
    }


def test_descriptive_readout_never_selects_winner_or_numeric_truth():
    rows=[_row(),_row(cid='RPT_009_D02',fid='F2',both=False,any_=False)]
    r=s.build_descriptive_readout(rows)
    assert r['majority_vote'] is False
    assert r['automatic_numeric_scientific_pass_fail'] is False
    assert r['external_engine_defines_arcana_target'] is False
    assert r['new_external_engine_execution_required_for_r52_closure'] is False
    assert r['r52_closure_readiness']=='READY_FOR_R52_SEAL_GOVERNED_DESCRIPTIVE_CORRIDOR_EVIDENCE_COMPLETE'


def test_descriptive_readout_preserves_counts_and_envelopes():
    rows=[_row(),_row(mov='D2_STANDARDIZED_2_CELL_CHARACTERISTIC',both=False,any_=True)]
    r=s.build_descriptive_readout(rows)
    o=r['overall']
    assert o['record_count']==2
    assert o['both_seeds_final_target_intersection_record_count']==1
    assert o['any_seed_final_target_intersection_record_count']==2
    assert o['max_jaccard_observed_envelope']==[0.2,0.5]


def test_next_engine_decision_is_domain_based_not_range_vote():
    r=s.build_descriptive_readout([])
    assert r['engine_adjudication']['RangeShifter']['action']=='NO_ADDITIONAL_R52_EXECUTION_REQUIRED'
    assert r['engine_adjudication']['CDMetaPOP']['action']=='PRIMARY_CANDIDATE_FOR_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_VALIDATION'
    assert r['engine_adjudication']['SLiM']['action']=='DEFER_TO_ANCESTRY_ADMIXTURE_STAGE'


def test_scientific_candidate_plan_hash_is_frozen_to_r52_r1_run():
    assert s.EXPECTED_PLAN_SHA256=='49704d285c416714c0c262769e97b34300004be268482a806cd8d9baf4f990dd'


def test_runner_has_seal_only_path_that_preserves_live_execution_bridge():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    runner=(root/'run_v0_6D1_R5_2.ps1').read_text(encoding='utf-8')
    assert '[switch]$SealOnly' in runner
    assert 'PASS_R52_SEAL_ONLY_RUN' in runner
    seal_pos=runner.index('if($SealOnly)')
    execution_pos=runner.index('fresh RangeShiftR 3.0.1 runtime identity')
    assert seal_pos < execution_pos


def test_final_seal_authority_constants_resolve_to_governed_corridor_constants():
    c=s.c
    assert c.EXPECTED_R51_FINAL_SEAL_SHA256=='74f13a6b397a2926db0ebcf6b45a4976678b598d241fe05acb3c3317d383e74c'
    assert c.EXPECTED_R51_ATLAS_SHA256=='9d4a70780785bdda7d1a51549d3b842450d6b563cab44684229157f073707caa'
    assert c.EXPECTED_R51_CANDIDATE_MANIFEST_SHA256=='a7540f66e037df808d2f63a722a4e554fcbb394444f6761e7054ec14d7f5f54d'
    assert c.EXPECTED_R51_STRUCTURE_MANIFEST_SHA256=='d97fbe2288391cd1df5bf587eeee6ea77e2d9ccd258ae908bb5b608b95b06509'
    assert c.EXPECTED_J14_SHA256=='eed2d1e350783f1d2dc31c5b7e697330ccbfcf63024062bc9f4ed2f8905f4756'
    assert c.EXPECTED_R314_SEAL_SHA256=='4a97e2c5aa7e0d7583aff89b3507bbe9555abe151aec96ed1667045080a468f0'
