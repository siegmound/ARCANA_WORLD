from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r337_managed_forager_economy import *
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT);CFG=load_json(ROOT/'configs/world1_r337_managed_forager_economy_v0_6D1_R3_37.json');REP=replay_managed_forager_economy(I,CFG)
def test_parent_pathway(): assert I['cp36']['resolved_pathway']=='INTENSIVE_MANAGED_FORAGER_PATHWAY'
def test_parent_seals(): assert I['a30']['status']==R330_PASS and I['a31']['status']==R331_PASS and I['a32']['status']==R332_PASS and I['a36']['status']==PARENT_PASS
def test_time_axis(): assert REP['age_ka'].shape==(145,) and REP['age_ka'][0]==20.0 and REP['age_ka'][-1]==0.0
def test_economy_geometry(): assert REP['economic_state'].shape==(32,2,145,len(ECON_NAMES))
def test_economy_bounded(): assert REP['economic_state'].min()>=0 and REP['economic_state'].max()<=1
def test_census_geometry(): assert REP['economy_coupled_census_equivalent'].shape==(32,2,145)
def test_census_anchor_parent(): assert np.max(np.abs(REP['economy_coupled_census_equivalent'][:,:,0]-REP['parent_census_equivalent'][:,:,0]))<1e-9
def test_census_multiplier_bounds(): assert REP['economy_census_multiplier'].min()>=CFG['economy_census_multiplier_min'] and REP['economy_census_multiplier'].max()<=CFG['economy_census_multiplier_max']
def test_group_closure(): assert np.max(np.abs(REP['economy_coupled_group_count_equivalent']*REP['economy_coupled_group_mean_size']-REP['economy_coupled_census_equivalent']))<1e-8
def test_node_geometry(): assert REP['economic_node_state'].shape==(32,2,9,48,len(NODE_NAMES))
def test_node_active_parent(): assert np.array_equal(REP['economic_node_active'],I['a32z']['regional_active'])
def test_node_numeric_finite(): assert np.isfinite(REP['economic_node_state']).all()
def test_managed_support_nonzero(): assert float(np.median(REP['economic_state'][:,:,-1,0]))>0.2
def test_network_nonzero(): assert float(np.median(REP['economic_state'][:,:,-1,6]))>0.2
def test_no_agriculture(): assert I['cp36']['agriculture_materialized'] is False and CFG['governance']['no_agriculture_or_domesticate_materialization'] is True
def test_no_village_state(): assert CFG['governance']['no_village_city_state_materialization'] is True
def test_no_hierarchy(): assert CFG['governance']['no_class_hierarchy_materialization'] is True
def test_no_lineage_rescale(): assert CFG['governance']['no_lineage_specific_rescaling'] is True
def test_replay_deterministic():
 b=replay_managed_forager_economy(I,CFG);assert np.array_equal(REP['economic_state'],b['economic_state']) and np.array_equal(REP['economy_coupled_census_equivalent'],b['economy_coupled_census_equivalent']) and np.array_equal(REP['economic_node_state'],b['economic_node_state'])
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
