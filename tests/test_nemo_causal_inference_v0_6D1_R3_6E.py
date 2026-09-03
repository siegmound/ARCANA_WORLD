from pathlib import Path
from arcana_worldsim.scientific_engines.r36e_inference import analyze_r36d_results_zip

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'reference_results'/'v0_6D1_R3_6D_RAW_RESULTS.zip'

def result():
    return analyze_r36d_results_zip(RESULTS)

def test_r36d_evidence_complete():
    r=result(); assert (r['source_job_count'],r['source_executed_count'],r['source_parsed_complete_count'])==(40,40,40)

def test_structural_mismatch_supported():
    assert result()['verdict'].startswith('STRUCTURAL_ADMIXTURE_OPERATOR_MISMATCH_SUPPORTED')

def test_arcana_whole_trait_mixing_far_above_polygenic_reference():
    vals=[x['arcana_1x125k_over_analytic'] for x in result()['three_way_causal_comparison']]
    assert min(vals)>100.0

def test_nemo_same_order_as_analytic_polygenic_reference():
    vals=[x['nemo_over_analytic'] for x in result()['three_way_causal_comparison']]
    assert min(vals)>0.25 and max(vals)<4.0

def test_b1_amplification_near_two_times_loci():
    vals=[x['arcana_1x125k_over_analytic'] for x in result()['three_way_causal_comparison'] if x['pair']=='B1_TWO_DEME_ADMIXTURE']
    assert all(abs(v-128.0)<2.0 for v in vals)

def test_nemo_flow_retains_between_deme_structure():
    q=[x['nemo_stat_Qst_min'] for x in result()['nemo_flow_structure']]
    assert min(q)>0.90

def test_fail_closed_governance():
    r=result(); assert not r['canonical_write_allowed']; assert not r['automatic_calibration_allowed']; assert not r['mu_b_recalibration_authorized']; assert not r['ceiling_change_authorized']; assert not r['production_r3_5_replay_authorized']
