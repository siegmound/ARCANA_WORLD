from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r339_symbolic_memory_language_identity import *
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT);CFG=load_json(ROOT/'configs/world1_r339_symbolic_memory_language_identity_v0_6D1_R3_39.json');REP=replay_symbolic_memory_language_identity(I,CFG)

def test_parent_r338_sealed(): assert I['a38']['status']==PARENT_PASS
def test_parent_r329_sealed(): assert I['a29']['status']==R329_PASS
def test_parent_r320_sealed(): assert I['s20']['verdict']==R320_PASS
def test_time_axis(): assert REP['age_ka'].shape==(145,) and REP['age_ka'][0]==20 and REP['age_ka'][-1]==0
def test_anchor_axis(): assert REP['anchor_age_ka'].shape==(9,) and np.array_equal(REP['anchor_age_ka'],I['z38']['anchor_age_ka'])
def test_symbolic_geometry(): assert REP['regional_symbolic_state'].shape==(32,2,145,6,10)
def test_symbolic_finite(): assert np.isfinite(REP['regional_symbolic_state']).all()
def test_symbolic_bounded(): assert REP['regional_symbolic_state'].min()>=0 and REP['regional_symbolic_state'].max()<=1
def test_cha2_geometry(): assert REP['binding']['regional_cha2_exposure'].shape==(32,2,80,6,5)
def test_cha2_axis(): assert REP['binding']['cha2_age_ka'][0]==14.95 and REP['binding']['cha2_age_ka'][-1]==11.0
def test_cha2_direct_fields_nonzero(): assert float(REP['binding']['regional_cha2_exposure'].max())>0.05
def test_memory_zero_pre_cha2(): assert np.max(REP['regional_symbolic_state'][:,:,REP['age_ka']>14.95,:,0])==0
def test_memory_nonzero_post_cha2(): assert float(REP['regional_symbolic_state'][:,:,-1,:,0].max())>0.05
def test_collective_memory_nonzero(): assert float(np.median(REP['regional_symbolic_state'][:,:,-1,:,1]))>0.30
def test_communication_conventionalization_nonzero(): assert float(np.median(REP['regional_symbolic_state'][:,:,-1,:,6]))>0.40
def test_language_precondition_not_language(): assert CFG['governance']['language_precondition_is_not_materialized_language'] is True
def test_identity_marker_not_ethnicity(): assert CFG['governance']['identity_marker_is_not_ethnicity'] is True
def test_no_named_language(): assert CFG['governance']['no_named_language_or_language_family_materialization'] is True
def test_no_religion(): assert CFG['governance']['no_religion_materialization'] is True
def test_no_lineage_rescale(): assert CFG['governance']['no_lineage_specific_rescaling'] is True
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
def test_replay_deterministic():
 b=replay_symbolic_memory_language_identity(I,CFG);assert np.array_equal(REP['regional_symbolic_state'],b['regional_symbolic_state']) and np.array_equal(REP['binding']['regional_cha2_exposure'],b['binding']['regional_cha2_exposure'])
