from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r334_producer_domestication import *
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT); CFG=load_json(ROOT/'configs/world1_r334_producer_domestication_v0_6D1_R3_34.json'); REG=build_producer_registry(); LAND=build_producer_landscape(I,REG); REP=replay_coevolution(I,REG,LAND,CFG)
def test_parent_inputs_validate(): assert I['a33']['status']==PARENT_PASS
def test_registry_count(): assert len(REG)==36
def test_archetypes_exact(): assert {x['archetype'] for x in REG}==set(ARCHETYPES)
def test_taxa_per_archetype(): assert all(sum(x['archetype']==a for x in REG)==6 for a in ARCHETYPES)
def test_registry_deterministic(): assert REG==build_producer_registry()
def test_taxa_operational_not_phylogeny(): assert all('OPERATIONAL_TAXON' in x['authority_semantics'] for x in REG)
def test_trait_bounds(): assert all(0<=v<=1 for x in REG for v in x['trait_values'].values())
def test_landscape_geometry(): assert LAND['fields'].shape==(36,9,90,180,4)
def test_landscape_bounds(): assert np.isfinite(LAND['fields']).all() and LAND['fields'].min()>=0 and LAND['fields'].max()<=1
def test_time_geometry(): assert I['z32']['age_ka'].shape==(145,)
def test_replay_geometry(): assert REP['traj'].shape==(32,2,36,145,10) and REP['stage'].shape==(32,2,36)
def test_overlap_geometry(): assert REP['overlap_anchor'].shape==(32,2,36,9)
def test_overlap_bounded(): assert REP['overlap_anchor'].min()>=0 and REP['overlap_anchor'].max()<=1
def test_initial_no_propagation_divergence(): assert np.max(REP['traj'][:,:,:,0,3:6])==0
def test_replay_bounded(): assert np.isfinite(REP['traj']).all() and REP['traj'].min()>=0 and REP['traj'].max()<=1
def test_stage_bounded(): assert set(np.unique(REP['stage'])).issubset(set(range(6)))
def test_replay_deterministic():
 b=replay_coevolution(I,REG,LAND,CFG); assert np.array_equal(REP['traj'],b['traj']) and np.array_equal(REP['stage'],b['stage'])
def test_governance_no_named_crops(): assert CFG['governance']['no_named_earth_crop_analogues'] is True
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
