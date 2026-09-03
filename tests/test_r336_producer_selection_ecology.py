from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r336_producer_selection_ecology import *
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT);CFG=load_json(ROOT/'configs/world1_r336_producer_selection_ecology_v0_6D1_R3_36.json');ECO=build_resource_selection_ecology(I,CFG);REP=replay_selection_ecology(I,CFG)
def test_parent_sealed(): assert I['a35']['status']==PARENT_PASS
def test_producer_count(): assert len(I['reg34']['taxa'])==36
def test_resource_anchor_geometry(): assert ECO['resource_concentration_anchor'].shape==(36,9)
def test_resource_time_geometry(): assert ECO['resource_concentration_time'].shape==(36,145)
def test_concentration_bounded(): assert ECO['resource_concentration_time'].min()>=0 and ECO['resource_concentration_time'].max()<=1
def test_persistence_bounded(): assert ECO['resource_persistence_time'].min()>=0 and ECO['resource_persistence_time'].max()<=1
def test_replay_genetic_geometry(): assert REP['managed_mean_shift'].shape==(32,2,36,145,6)
def test_patch_geometry(): assert REP['managed_patch_persistence'].shape==(32,2,36,145)
def test_isolation_geometry(): assert REP['managed_population_isolation'].shape==(32,2,36,145)
def test_wild_geometry(): assert REP['effective_wild_gene_flow'].shape==(32,2,36,145)
def test_states_finite(): assert np.isfinite(REP['managed_mean_shift']).all() and np.isfinite(REP['managed_patch_persistence']).all()
def test_states_bounded(): assert REP['managed_patch_persistence'].min()>=0 and REP['managed_patch_persistence'].max()<=1 and REP['managed_population_isolation'].min()>=0 and REP['managed_population_isolation'].max()<=1
def test_effective_wild_not_above_parent(): assert np.max(REP['effective_wild_gene_flow']-np.asarray(I['z34']['trajectory_state'],float)[...,6])<=1e-6
def test_propagation_not_below_r335(): assert np.min(REP['effective_propagation_control']-np.asarray(I['z35']['effective_propagation_control'],float))>=-2e-4
def test_stage_bounded(): assert set(np.unique(REP['stage'])).issubset(set(range(6)))
def test_thresholds_inherited(): assert CFG['governance']['inherit_r334_r335_domestication_gates_exactly'] is True and CFG['governance']['no_domestication_threshold_relaxation'] is True
def test_replay_deterministic():
 b=replay_selection_ecology(I,CFG);assert np.array_equal(REP['managed_mean_shift'],b['managed_mean_shift']) and np.array_equal(REP['effective_wild_gene_flow'],b['effective_wild_gene_flow']) and np.array_equal(REP['stage'],b['stage'])
def test_no_lineage_rescale(): assert CFG['governance']['no_lineage_specific_rescaling'] is True
def test_unique_human_off(): assert CFG['governance']['unique_human_identity_materialized'] is False
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
