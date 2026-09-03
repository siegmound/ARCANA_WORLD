from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r338_exchange_technology_cultural_genealogy import *
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT);CFG=load_json(ROOT/'configs/world1_r338_exchange_technology_cultural_genealogy_v0_6D1_R3_38.json');REP=replay_exchange_technology_genealogy(I,CFG)
def test_parent_pathway(): assert all(v=='DISTRIBUTED_MANAGED_FORAGER_ECONOMY' for v in I['cp37']['resolved_lineage_economic_pathways'].values())
def test_parent_seals(): assert I['a37']['status']==PARENT_PASS and I['a31']['status']==R331_PASS and I['a32']['status']==R332_PASS and I['a33']['status']==R333_PASS
def test_time_axis(): assert REP['age_ka'].shape==(145,) and REP['age_ka'][0]==20 and REP['age_ka'][-1]==0
def test_anchor_axis(): assert np.array_equal(REP['anchor_age_ka'],I['a32z']['anchor_age_ka'])
def test_implementation_geometry(): assert REP['implementation_stock'].shape==(32,2,145,12)
def test_implementation_bounded(): assert REP['implementation_stock'].min()>=0 and REP['implementation_stock'].max()<=1
def test_material_geometry(): assert REP['material_affordance_time'].shape==(32,2,145,4)
def test_group_geometry(): assert REP['group_implementation_support'].shape==(32,2,9,48,12)
def test_group_active_parent(): assert np.array_equal(REP['group_active'],I['a32z']['regional_active'])
def test_regional_geometry(): assert REP['regional_profile'].shape==(32,2,9,6,12)
def test_regional_state_geometry(): assert REP['regional_state'].shape==(32,2,9,6,len(REGIONAL_STATE_NAMES))
def test_exchange_geometry(): assert REP['exchange_matrix'].shape==(32,9,12,12)
def test_exchange_symmetric(): assert np.max(np.abs(REP['exchange_matrix']-np.swapaxes(REP['exchange_matrix'],-1,-2)))<1e-12
def test_exchange_diagonal_zero(): assert np.max(np.abs(np.diagonal(REP['exchange_matrix'],axis1=-2,axis2=-1)))==0
def test_all_finite(): assert all(np.isfinite(REP[k]).all() for k in ['implementation_stock','group_implementation_support','regional_profile','regional_state','exchange_matrix'])
def test_nonzero_implementations(): assert float(np.median(REP['implementation_stock'][:,:,-1]))>0.15
def test_nonzero_exchange(): assert float(np.median(REP['exchange_matrix'][:,-1].max(axis=-1)))>0.02
def test_generic_hard_material_prior_explicit(): assert 0<CFG['generic_hard_material_access_prior']<1 and CFG['governance']['generic_hard_material_access_is_explicit_prior_not_geology_observation'] is True
def test_no_named_culture_language_religion(): assert CFG['governance']['no_named_culture_materialization'] is True and CFG['governance']['no_language_or_religion_materialization'] is True
def test_no_metallurgy(): assert CFG['governance']['no_metallurgy_without_material_authority'] is True
def test_no_lineage_rescale(): assert CFG['governance']['no_lineage_specific_rescaling'] is True
def test_replay_deterministic():
 b=replay_exchange_technology_genealogy(I,CFG);assert np.array_equal(REP['implementation_stock'],b['implementation_stock']) and np.array_equal(REP['regional_profile'],b['regional_profile']) and np.array_equal(REP['exchange_matrix'],b['exchange_matrix'])
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
