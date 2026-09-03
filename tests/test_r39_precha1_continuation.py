from __future__ import annotations
from pathlib import Path
import json, numpy as np, pytest
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines.r39_precha1_continuation import (
 R39Config,PRE_CHA1_AGE_MA,EXPECTED_STEPS_150_TO_66,PRE_CHA1_SCHEMA,
 validate_r38_checkpoint_authority,validate_cha1_exact_event_authority,
 save_precha1_checkpoint,load_precha1_checkpoint)
from arcana_worldsim.scientific_engines.segregation_potential_lifecycle import ReducedGeneticLifecycleState
ROOT=Path(__file__).resolve().parents[1]

def dummy_state():
 n=2; t=3
 st=r38.R38RuntimeState(
  age_ma=66.0,elapsed_year=144_000_000.0,component_ids=['c0','c1'],root_species=['s0','s1'],current_species=['s0','s1'],
  guild=np.array([1,2],np.uint8),pop=np.ones((n,2,3)),trait=np.zeros((n,t)),va=np.full((n,t),0.01),gen=np.array([4.,5.]),
  registry={'s0':{},'s1':{}},child_counters={},current_accessible=np.ones((2,3),bool),baselines={},ri_state={},clock_state={},
  ext_state={},founder_state={},vicariance_state={},reconnection_state={},events=[],snapshots=[],founder_stats_last=[],gene_flow_closure={},
  topology_remap_mass=0.,initial_total_population=12.,reduced_state=ReducedGeneticLifecycleState(np.full((n,t),.01),np.zeros((n,t)),np.zeros((n,n,t)),np.zeros((n,t))))
 st._lat=np.array([-45.,45.]); st._lon=np.array([-120.,0.,120.]); return st

def test_fixed_boundary_and_step_count():
 assert PRE_CHA1_AGE_MA==66.0
 assert EXPECTED_STEPS_150_TO_66==672
 assert abs((150.0-66.0)*1e6/125000-672)<1e-12
 assert R39Config().end_age_ma==66.0

def test_r38_checkpoint_authority_is_sealed_and_hash_valid():
 a=validate_r38_checkpoint_authority(ROOT)
 assert a['state'].age_ma==150.0
 assert a['json_sha256']=='8a8fbe9da857c6b278c2c8856a4b989a40a0a5ec2087af64a2ce0e9c1a6a2853'
 assert a['npz_sha256']=='0d253babcd74bdfcf4590bb6f51ac4ce99aabcb8f224d00a4c59fd148021cc32'

def test_cha1_exact_event_authority():
 a=validate_cha1_exact_event_authority(ROOT)
 assert a['audit']['exact_event_time_preferred'] is True
 assert a['audit']['pulse_before_impact_j']==[0.0]*5
 assert a['audit']['pulse_at_impact_total_j']>0

def test_precha1_serializer_roundtrip(tmp_path):
 st=dummy_state(); cfg=R39Config()
 r38a={'json_sha256':'j'*64,'npz_sha256':'n'*64}
 cha={'sha256':'c'*64,'audit':{'pulse_before_impact_j':[0.0]*5,'pulse_at_impact_total_j':1.0}}
 cp=save_precha1_checkpoint(st,tmp_path,r38a,cha,cfg)
 meta=json.loads(Path(cp['json']).read_text())
 assert meta['schema']==PRE_CHA1_SCHEMA and meta['event_side']=='PRE_IMPACT_66P0_MINUS'
 assert meta['governance']['cha1_applied'] is False
 out=load_precha1_checkpoint(Path(cp['json']))
 assert r38.compare_runtime_states(st,out)['equivalent'] is True

def test_save_rejects_non66(tmp_path):
 st=dummy_state(); st.age_ma=66.125
 with pytest.raises(ValueError):
  save_precha1_checkpoint(st,tmp_path,{'json_sha256':'j','npz_sha256':'n'},{'sha256':'c','audit':{'pulse_before_impact_j':[0]*5,'pulse_at_impact_total_j':1}},R39Config())

def test_candidate_contains_no_full_precha1_checkpoint():
 p=ROOT/'local_runs/v0_6D1_R3_9'
 assert not p.exists() or not list(p.glob('WORLD1_H0_66Ma_PRE_CHA1_CANONICAL_CHECKPOINT_v0_6D1_R3_9.*'))

def test_smoke_passed_and_did_not_apply_cha1():
 d=json.loads((ROOT/'outputs/v0_6D1_R3_9/R3_9_DIAGNOSTIC_SMOKE.json').read_text())
 assert d['verdict'].startswith('PASS_') and d['biology_steps']==1 and d['cha1_applied'] is False

def test_governance_does_not_change_physics():
 text=(ROOT/'src/arcana_worldsim/scientific_engines/r39_precha1_continuation.py').read_text()
 assert 'scalar_k_physical_constant_authorized' in text
 assert 'mu_b_or_ceiling_change_authorized' in text
 assert "'cha1_applied':False" in text
