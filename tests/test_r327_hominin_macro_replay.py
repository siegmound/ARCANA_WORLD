from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r327_hominin_macro_replay import *
from arcana_worldsim.scientific_engines.r327_hominin_macro_replay import _norm_rank
def test_stage():assert STAGE=='v0.6D1-R3.27'
def test_candidate_count_constant():assert EXPECTED_CANDIDATES==6
def test_member_count_constant():assert EXPECTED_MEMBERS==96
def test_state_names_unique():assert len(VAR_NAMES)==8 and len(set(VAR_NAMES))==8
def test_evidence_multisource():assert len(EVIDENCE)>=5
def test_rank_norm():
 x=_norm_rank(np.array([10.,1.,5.]));assert np.all((x>0)&(x<1)) and len(set(x))==3
def test_forcing_geometry():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));f=forcing_ensemble(cfg);assert len(f['ages_ma'])==141 and f['stress'].shape==(96,141)
def test_forcing_reaches_200ka():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));f=forcing_ensemble(cfg);assert abs(f['ages_ma'][-1]-.2)<1e-12
def test_forcing_three_regimes_equal():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));f=forcing_ensemble(cfg);u,c=np.unique(f['regime'],return_counts=True);assert sorted(c.tolist())==[32,32,32]
def test_forcing_deterministic():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));a=forcing_ensemble(cfg);b=forcing_ensemble(cfg);assert np.array_equal(a['stress'],b['stress']) and np.array_equal(a['bottleneck'],b['bottleneck'])
def test_thresholds_fixed():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));assert cfg['qualification']['survival_frequency_min']==.8 and cfg['qualification']['sensitivity_qualification_frequency_min']==.7
def test_no_human_similarity_target():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));assert cfg['human_similarity_target'] is False and cfg['unique_human_body_plan_target'] is False
def test_no_deep():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));assert cfg['deep_biological_coupling'] is False
def test_no_parent_mutation():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));assert all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation','r326_mutation'))
def test_no_direct_cb_selection():
 cfg=json.load(open(ROOT/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json'));assert cfg['h3_cb_direct_selection'] is False
