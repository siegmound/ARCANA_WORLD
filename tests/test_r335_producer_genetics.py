from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r335_producer_genetics import *
from arcana_worldsim.scientific_engines.r335_producer_genetics import _corr_matrix
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT);CFG=load_json(ROOT/'configs/world1_r335_producer_genetics_v0_6D1_R3_35.json');PRI=build_genetic_priors(I,CFG);REP=replay_genetics(I,CFG)
def test_parent_sealed(): assert I['a34']['status']==PARENT_PASS
def test_producer_count(): assert len(I['reg34']['taxa'])==36
def test_six_genetic_traits(): assert len(GENETIC_TRAIT_NAMES)==6
def test_prior_geometry(): assert PRI['va0'].shape==(36,6) and PRI['h20'].shape==(36,6)
def test_va_prior_positive(): assert PRI['va0'].min()>0 and PRI['va0'].max()<=CFG['va_ceiling']
def test_h2_prior_bounded(): assert PRI['h20'].min()>0 and PRI['h20'].max()<1
def test_generation_intervals_positive(): assert np.all(PRI['generation_interval_years']>0)
def test_correlation_psd(): assert np.linalg.eigvalsh(_corr_matrix(CFG['genetic_covariance_offdiag'])).min()>0
def test_replay_geometry(): assert REP['mean_shift'].shape==(32,2,36,145,6)
def test_va_geometry(): assert REP['additive_variance'].shape==(32,2,36,145,6)
def test_heritability_geometry(): assert REP['heritability'].shape==(32,2,36,145,6)
def test_response_geometry(): assert REP['selection_response'].shape==(32,2,36,145,6)
def test_initial_wild_reference_zero(): assert np.max(REP['mean_shift'][:,:,:,0,:])==0
def test_genetic_means_bounded(): assert REP['mean_shift'].min()>=0 and REP['mean_shift'].max()<=1
def test_va_positive_bounded(): assert REP['additive_variance'].min()>0 and REP['additive_variance'].max()<=CFG['va_ceiling']+1e-12
def test_h2_bounded(): assert REP['heritability'].min()>=0 and REP['heritability'].max()<=1
def test_effective_propagation_not_below_parent(): assert np.min(REP['effective_propagation_control']-np.asarray(I['z34']['trajectory_state'],float)[...,3])>=-1e-7
def test_stage_bounded(): assert set(np.unique(REP['stage'])).issubset(set(range(6)))
def test_replay_deterministic():
 b=replay_genetics(I,CFG);assert np.array_equal(REP['mean_shift'],b['mean_shift']) and np.array_equal(REP['additive_variance'],b['additive_variance']) and np.array_equal(REP['stage'],b['stage'])
def test_no_lineage_rescaling(): assert CFG['governance']['no_lineage_specific_rescaling'] is True
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
