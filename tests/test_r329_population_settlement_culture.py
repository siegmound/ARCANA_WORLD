from pathlib import Path
import json, numpy as np, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r329_population_settlement_culture import *

def test_sigmoid_bounds():
 x=np.linspace(-100,100,100);y=sigmoid(x);assert np.all((y>=0)&(y<=1))
def test_state_names_unique():assert len(TIME_NAMES)==len(set(TIME_NAMES))==10
def test_anchor_names_unique():assert len(ANCHOR_NAMES)==len(set(ANCHOR_NAMES))==7
def test_candidates_frozen():assert EXPECTED_CANDIDATES==['RPT_010_D02','RPT_009_D02']
def test_evidence_multisource():assert len(EVIDENCE)>=5
def test_no_identity_semantics():assert 'CULTURAL_PRECONDITION' in CANDIDATE_PASS
def test_final_pass_semantics():assert 'CULTURAL_TRANSMISSION_PRECONDITIONS' in FINAL_PASS
def test_config_no_culture_identity_materialization():
 c=json.load(open(ROOT/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json'))
 for k in ('language_materialized','religion_materialized','agriculture_materialized','city_state_materialized','unique_human_identity_materialized','deep_biological_coupling'):assert c[k] is False
def test_config_no_parent_mutation():
 c=json.load(open(ROOT/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json'))
 for k in ('h0_mutation','cha2_mutation','r323_mutation','r328_mutation'):assert c[k] is False
def test_census_not_materialized():
 c=json.load(open(ROOT/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json'));assert c['absolute_census_calibration_materialized'] is False and c['absolute_camp_headcounts_materialized'] is False
def test_sensitivity_count():
 c=json.load(open(ROOT/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json'));assert len(c['sensitivity_multipliers'])==11
def test_culture_rate_positive():
 c=json.load(open(ROOT/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json'));assert 0<c['culture_stock_rate_per_kyr']<1
