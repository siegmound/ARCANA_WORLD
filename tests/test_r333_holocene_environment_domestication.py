from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r333_holocene_environment_domestication import *
ROOT=Path(__file__).resolve().parents[1]
I=validate_inputs(ROOT); P=build_partner_registry(I); E=build_environment(I); CFG=load_json(ROOT/'configs/world1_r333_holocene_environment_domestication_v0_6D1_R3_33.json'); R=replay_domestication(I,P,E,CFG)
def test_parent_inputs_validate(): assert I['a32']['status']==PARENT_PASS
def test_anchor_axis_exact(): assert np.array_equal(ANCHOR_AGES,np.array([20.,15.,14.,13.,12.,11.,10.,5.,0.]))
def test_partner_quota_total(): assert sum(PARTNER_QUOTAS.values())==24
def test_partner_registry_deterministic(): assert P==build_partner_registry(I) and len(P)==24
def test_partner_registry_all_present_guilds(): assert {x['guild_id'] for x in P}==set(PARTNER_QUOTAS)
def test_apex_absent_at_present(): assert all(int(x['guild_id'])!=6 for x in I['reg']['lineages'])
def test_partner_registry_excludes_sapients(): assert not ({x['species_id'] for x in P}&set(EXPECTED_CANDIDATES))
def test_environment_geometry(): assert E['fields'].shape==(9,90,180,7)
def test_environment_finite_bounded_land(): assert np.isfinite(E['fields']).all() and E['fields'][...,3].min()>=0 and E['fields'][...,3].max()<=1
def test_direct_provider_geometry(): assert I['hist']['time_year_before_book'].shape==(1201,) and I['snaps']['temperature_anomaly_c'].shape==(5,720,1440)
def test_replay_geometry(): assert R['traj'].shape==(32,2,24,9,9) and R['stage'].shape==(32,2,24)
def test_no_initial_reproductive_control(): assert np.max(R['traj'][:,:,:,0,3:5])==0
def test_replay_deterministic():
 b=replay_domestication(I,P,E,CFG); assert np.array_equal(R['traj'],b['traj']) and np.array_equal(R['stage'],b['stage'])
def test_no_plant_species_authority(): assert CFG['governance']['plant_species_registry_available'] is False
def test_deep_off(): assert CFG['governance']['deep_biological_coupling'] is False
def test_agriculture_requires_explicit_flora(): assert CFG['governance']['agriculture_requires_explicit_plant_or_equivalent_domesticate'] is True
