from __future__ import annotations
import hashlib, json, tempfile
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
from arcana_worldsim.scientific_engines.r37i_production_runtime import validate_promotion_seal
from arcana_worldsim.scientific_engines.r38_restartable_checkpoint import (
    R38Config,RUNTIME_SCHEMA,CHECKPOINT_SCHEMA,NOMINAL_K,initialize_210ma_state,advance_state,state_projection,
    save_runtime_state,load_runtime_state,save_checkpoint,compare_runtime_states)

def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

@pytest.fixture(scope='module')
def setup_state():
    common=np.load(ROOT/'outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz',allow_pickle=False)
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); rows=md['species'] if isinstance(md,dict) and 'species' in md else md
    cfg=R38Config(end_age_ma=149.0); st=initialize_210ma_state(common,a1,rows,cfg); s209,recs=advance_state(st,a1,rows,cfg,209.0)
    return common,a1,rows,cfg,s209,recs

def test_r38_nominal_reference_is_operational_center_only():
    c=R38Config(); assert c.branch_label=='K_CENTER' and c.adaptive_k_eff==NOMINAL_K==38.470
    with pytest.raises(ValueError): R38Config(adaptive_k_eff=41.002)

def test_r38_seal_is_real_and_pass():
    p=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'; s=validate_promotion_seal(p)
    assert s['status']=='PASS_PRODUCTION_PROMOTION_SEAL'; assert s['authority']['scalar_k_physical_constant_authorized'] is False

def test_r38_r37h_center_reference_hash_matches_seal():
    seal=json.loads((ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json').read_text())
    ref=ROOT/'references/v0_6D1_R3_8/R37H_210_150_K_CENTER_SEALED_REFERENCE.json'
    assert _sha(ref)==seal['r37h_full_closed_loop_evidence']['json_sha256']['K_CENTER']

def test_r38_210_209_matches_sealed_r37i_smoke(setup_state):
    _,_,rows,cfg,s209,recs=setup_state; p=state_projection(s209,rows,cfg)
    old=json.loads((ROOT/'local_runs/v0_6D1_R3_7I/210_to_209p0Ma_R3_7I_canonical.json').read_text())
    assert len(recs)==8 and abs(p['final_total_population']-old['final_total_population'])<2e-12 and abs(p['q_max']-old['peak_q'])<2e-12
    assert p['species_count']==old['species_count'] and p['component_count']==old['component_count'] and p['event_counts']==old['event_counts']

def test_r38_serialization_preserves_full_reduced_state(setup_state):
    _,_,_,cfg,s209,_=setup_state; sealp=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'state.json'; save_runtime_state(s209,p,cfg,_sha(sealp)); loaded=load_runtime_state(p,RUNTIME_SCHEMA); cmp=compare_runtime_states(s209,loaded)
    assert cmp['equivalent'] and all(v['same'] for v in cmp['reduced_state'].values())

def test_r38_restart_is_exact_across_serialization_boundary(setup_state):
    _,a1,rows,cfg,s209,_=setup_state; sealp=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'state.json'; save_runtime_state(s209,p,cfg,_sha(sealp)); loaded=load_runtime_state(p,RUNTIME_SCHEMA)
        direct,_=advance_state(s209,a1,rows,cfg,208.0); restart,_=advance_state(loaded,a1,rows,cfg,208.0); cmp=compare_runtime_states(direct,restart)
    assert cmp['equivalent']

def test_canonical_checkpoint_rejects_wrong_age(setup_state):
    _,_,_,cfg,s209,_=setup_state
    with tempfile.TemporaryDirectory() as td, pytest.raises(ValueError): save_checkpoint(s209,Path(td),'x'*64,cfg)

def test_checkpoint_schema_names_full_reduced_state_arrays():
    src=(ROOT/'src/arcana_worldsim/scientific_engines/r38_restartable_checkpoint.py').read_text()
    for token in ('reduced_va_within','reduced_ancestry_covariance','reduced_neutral_segregation_potential','reduced_adaptive_coordinate'): assert token in src
    assert CHECKPOINT_SCHEMA=='ARCANA_R38_CANONICAL_150MA_CHECKPOINT_V1'
