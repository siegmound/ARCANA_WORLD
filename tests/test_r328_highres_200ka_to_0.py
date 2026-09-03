from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r328_highres_200ka_to_0 import *
def cfg():return json.load(open(ROOT/'configs'/'world1_r328_high_resolution_200ka_to_0_v0_6D1_R3_28.json'))
def test_stage():assert STAGE=='v0.6D1-R3.28'
def test_parent():assert PARENT_STAGE=='v0.6D1-R3.27' and EXPECTED_PARENT_CHECKS==28
def test_candidates():assert EXPECTED_CANDIDATES==2 and EXPECTED_MEMBERS==32
def test_demes():assert MAX_DEMES==6
def test_state_names():assert len(STATE_NAMES)==7 and len(set(STATE_NAMES))==7
def test_evidence():assert len(EVIDENCE)>=5
def test_time_axis_endpoints():
 a=build_time_axis();assert a[0]==200 and a[-1]==0 and len(np.unique(a))==len(a)
def test_cha2_exact_axis():
 a=build_time_axis();h=a[(a<=14.95)&(a>=11)];assert len(h)==80 and np.array_equal(np.rint(h*1000).astype(int),np.arange(14950,10999,-50))
def test_r318_not_false_direct():assert cfg()['r318_is_direct_high_resolution_timeseries'] is False
def test_cha2_semantics():assert cfg()['cha2_hazard_semantics']=='DIAGNOSTIC_RANKING_NOT_FLOOD_DEPTH'
def test_no_human_similarity():assert cfg()['human_similarity_target'] is False and cfg()['unique_human_body_plan_target'] is False
def test_no_deep():assert cfg()['deep_biological_coupling'] is False
def test_no_mutation():assert all(cfg()[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation','r326_mutation','r327_mutation'))
def test_no_direct_cb():assert cfg()['h3_cb_direct_selection'] is False
def test_thresholds_precommitted():
 q=cfg()['qualification'];assert q['survival_frequency_min']==.85 and q['sensitivity_frequency_min']==.70 and q['cha2_population_retention_median_min']==.75
