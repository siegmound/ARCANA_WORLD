from pathlib import Path
import sys,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r326_h3_quant_genetics_bridge import *
from arcana_worldsim.scientific_engines.r326_h3_quant_genetics_bridge import _read_cb_rows

def test_h3_weights_unit_variance():assert abs(W_INF**2+W_UR**2+W_EPS**2-1)<1e-15
def test_zr_ur_roundtrip():
 zi=np.array([-2.,0.,1.]);u=np.array([.4,-.2,1.2]);assert np.max(np.abs(ur_from_zr(zi,zr_from_latents(zi,u))-u))<1e-15
def test_h3_formula_fixture():
 zi=np.array([1.]);u=np.array([0.]);e=np.array([0.]);assert abs(float(h3_from_latents(zi,u,e)[0])-math.sqrt(.75))<1e-15
def test_expected_parent_corr():assert abs(EXPECTED_ZH_PARENT_CORR-.45)<1e-15
def test_authority_hashes_count():assert len(AUTH_HASHES)==4
def test_mapper_nodes(tmp_path):
 m=load_json(ROOT/'authority'/'h3_cb'/'H3_CB_CONTINUOUS_MAPPING_v0_3_70.json');f=hard_ceiling_mapper(m);z=np.array([x['Z_H'] for x in m['nodes']]);j=np.array([x['J_lower_W'] for x in m['nodes']]);assert np.max(np.abs(f(z)-j)/j)<1e-12
def test_mapper_monotone():
 m=load_json(ROOT/'authority'/'h3_cb'/'H3_CB_CONTINUOUS_MAPPING_v0_3_70.json');f=hard_ceiling_mapper(m);assert np.all(np.diff(f(np.linspace(-6,7,5000)))>0)
def test_cb_labels_boundaries():
 cb=_read_cb_rows(ROOT/'authority'/'h3_cb'/'cb_scale.csv');z=np.array([cb[1]['z']-1e-8,cb[1]['z'],cb[-1]['z']]);lab=cb_labels(z,cb);assert lab.tolist()==[1,2,12]
def test_analytic_probs_sum_one():
 cb=_read_cb_rows(ROOT/'authority'/'h3_cb'/'cb_scale.csv');assert abs(sum(analytic_cb_probs(cb).values())-1)<1e-15
def test_rare_tail_cb12_per_billion():
 cb=_read_cb_rows(ROOT/'authority'/'h3_cb'/'cb_scale.csv');assert abs(rare_tail_table(cb)[-1]['expected_CB12_compatible']-43.98)<1e-12
def test_character_fixture_mapping():
 m=load_json(ROOT/'authority'/'h3_cb'/'H3_CB_CONTINUOUS_MAPPING_v0_3_70.json');f=hard_ceiling_mapper(m);assert abs(float(f(np.array([5.4445840918]))[0])/1e12-133.59)<.02
def test_reproduction_smoke():
 r=reproduction_reference(30000,1234);assert abs(r['child_ZH_std']-1)<.03 and abs(r['corr_child_mother_ZH']-.45)<.03
def test_neutral_smoke():
 cb=_read_cb_rows(ROOT/'authority'/'h3_cb'/'cb_scale.csv');r=neutral_reference(50000,456,cb);assert abs(r['mean']['Z_H'])<.02 and abs(r['std']['Z_H']-1)<.02
def test_no_cb_input_in_reproduction_contract():
 r=reproduction_reference(1000,7);assert r['parental_CB_label_input'] is False and r['offspring_from_upstream_latents_only'] is True
def test_candidate_bridge_no_rescale_fixture():
 class X:pass
 d={'species_id':'A','module_envelope':{k:{'median':.5} for k in ('embodied_manipulation','neurocognitive_integration','learning_development_integration','social_transmission_communication','life_history_sustainability','ecological_resource_buffering')}}
 rows=candidate_bridge({'candidates':['A'],'dby':{'A':d}});assert rows[0]['h3_hard_ceiling_distribution_shift']==0 and rows[0]['cb_distribution_rescaled_for_lineage'] is False
