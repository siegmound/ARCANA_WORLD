from pathlib import Path
import json,sys
import numpy as np
import pytest
from arcana_worldsim.scientific_engines.r37e_short_shadow_replay import R37EShortShadowConfig,run_short_world1_shadow
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def result():
    common=np.load(ROOT/'outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz',allow_pickle=False)
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text())
    rows=md['species'] if isinstance(md,dict) and 'species' in md else md
    return run_short_world1_shadow(common,a1,rows,R37EShortShadowConfig(end_age_ma=209.0,diagnostic_smoke=True))

def test_governed_window_is_210_to_205():
    c=R37EShortShadowConfig(); assert c.start_age_ma==210 and c.end_age_ma==205
    with pytest.raises(ValueError): R37EShortShadowConfig(end_age_ma=204)
    s=R37EShortShadowConfig(end_age_ma=209,diagnostic_smoke=True); assert s.end_age_ma==209

def test_parent_canonical_state_is_bit_exact(result):
    assert result['canonical_parity']['all_core_parity'] is True

def test_smoke_has_expected_biology_steps(result):
    assert result['shadow']['window']['biology_steps']==8

def test_all_variants_stay_below_existing_ceiling(result):
    assert result['shadow']['ceiling_contacts_by_variant']=={'K_LOW':0,'K_CENTER':0,'K_HIGH':0}

def test_k_envelope_order_is_preserved(result):
    e=result['shadow']['K_envelope']; assert e['K_LOW'] < e['K_CENTER'] < e['K_HIGH']

def test_shadow_is_noncanonical(result):
    g=result['shadow']['governance']; assert g['shadow_only'] and not g['canonical_write_allowed'] and not g['production_runtime_replacement_authorized']


def test_final_state_dimensions_match_parent(result):
    assert result['shadow']['component_count_final']==result['canonical_final']['component_count']

def test_no_mu_b_or_ceiling_authority_change(result):
    assert result['shadow']['governance']['mu_b_or_ceiling_change_authorized'] is False
