import json, numpy as np
from pathlib import Path
from arcana_worldsim.scientific_engines import r330_census_group_abm as m

def test_stage(): assert m.STAGE=='v0.6D1-R3.30'
def test_candidates(): assert m.EXPECTED_CANDIDATES==['RPT_010_D02','RPT_009_D02']
def test_evidence_multisource(): assert len(m.EVIDENCE)>=8
def test_census_names_unique(): assert len(m.CENSUS_NAMES)==len(set(m.CENSUS_NAMES))==6
def test_agent_names_unique(): assert len(m.AGENT_NAMES)==len(set(m.AGENT_NAMES))==12
def test_history_names_unique(): assert len(m.HISTORY_NAMES)==len(set(m.HISTORY_NAMES))==10
def test_no_person_level_label(): assert 'person' not in m.AGENT_NAMES
def test_sha(tmp_path):
 p=tmp_path/'x';p.write_bytes(b'abc');assert m.sha256_file(p)=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
def test_ratio_prior_bounds():
 cfg={'ne_to_total_census_ratio_prior':{'distribution':'triangular','low':.18,'mode':.34,'high':.60,'seed':1}}
 r=m._ratio_prior(cfg,1000);assert r.min()>=.18 and r.max()<=.60 and r.shape==(1000,2)
def test_anchor_index(): assert m._anchor_time_index(np.array([2.,1.,0.]),1.)==1
def test_final_pass_name(): assert m.FINAL_PASS.startswith('PASS_R330_')
def test_semantic_output_names(): assert 'census_equivalent_total' in m.CENSUS_NAMES and 'represented_camps' in m.AGENT_NAMES
def test_candidate_pass_name(): assert m.CANDIDATE_PASS.startswith('PASS_R330_')
