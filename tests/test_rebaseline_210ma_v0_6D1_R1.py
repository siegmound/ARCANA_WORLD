from pathlib import Path
import json, math
import numpy as np
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rebaseline_210ma_v0_6D1_R1 import (
    RebaselineConfig, validate_d1_metadata, decompose_guild_state, build_common_state,
    semantic_hash, conservation_diagnostics, paired_manifests, allowed_branch_delta,
)

def load_npz(p):
    z=np.load(p,allow_pickle=False); return {k:z[k] for k in z.files}

def inputs():
    ref=ROOT/'references'/'v0_6D1_R1'
    meta=json.loads((ref/'D1_species_metadata_120.json').read_text())
    a1=load_npz(ref/'A1_WORLD1_210Ma_REFERENCE.npz')
    deep=load_npz(ref/'DEEP_WORLD1_210Ma_REFERENCE_v0_5.npz')
    cal=json.loads((ref/'WORLD1_DEEP_FREE_ENERGY_CALIBRATION_v0_5.json').read_text())
    return meta,a1,deep,cal

def test_d1_identity_surface_exact_counts_and_no_hsg025():
    meta,*_=inputs(); info=validate_d1_metadata(meta)
    assert info['species_count']==120
    assert info['guild_counts']=={1:24,2:16,3:20,4:24,5:24,6:12}
    assert 'HSG_025' not in info['species_ids']

def test_cellwise_population_and_capacity_closure():
    meta,a1,*_=inputs(); d=decompose_guild_state(meta,a1,RebaselineConfig())
    gids=d['guild_id']
    for gid in range(1,7):
        ix=np.where(gids==gid)[0]
        assert np.max(np.abs(d['species_population'][ix].sum(0)-a1['guild_population'][gid-1])) < 1e-12
        assert np.max(np.abs(d['species_carrying_capacity'][ix].sum(0)-a1['guild_carrying_capacity'][gid-1])) < 1e-12

def test_no_initial_population_outside_land_or_above_capacity():
    meta,a1,*_=inputs(); d=decompose_guild_state(meta,a1,RebaselineConfig())
    assert not np.any((d['species_population']>0) & (~a1['land_mask'].astype(bool))[None,:,:])
    assert not np.any(d['species_population'] > d['species_carrying_capacity']+1e-12)
    assert np.all(d['species_population'].sum((1,2))>0)

def test_latent_va_is_exact_d33a_zero_selection_equilibrium():
    cfg=RebaselineConfig(); cfg.validate()
    q=math.sqrt(cfg.mutation_variance_supply_per_myr/cfg.nonlinear_variance_depletion_per_myr_per_q)
    assert q==0.045
    assert cfg.latent_va_equilibrium==q

def test_common_state_is_deterministic_semantically():
    meta,a1,deep,cal=inputs(); cfg=RebaselineConfig()
    a,m=build_common_state(meta,a1,deep,cal,cfg); b,n=build_common_state(meta,a1,deep,cal,cfg)
    assert semantic_hash(a,m)==semantic_hash(b,n)
    assert semantic_hash(a,m)=='f0b15dc9dd3df479df1f48e286a64e28dc29c62674acc9792c4297049e600452'

def test_photo_deep_is_additive_five_percent_only_E_and_th():
    meta,a1,deep,cal=inputs(); arrays,_=build_common_state(meta,a1,deep,cal,RebaselineConfig())
    u=arrays['deep_u_base_DFEU']; p=arrays['deep_photo_u_DFEU']
    np.testing.assert_allclose(p[:2],0.05*u[:2],rtol=0,atol=0)
    np.testing.assert_array_equal(p[2:],np.zeros(3))
    assert float(arrays['deep_photo_energy_j'].sum())>0

def test_h0_hx_reference_same_state_and_only_allowed_authority_delta():
    cfg=RebaselineConfig(); h0,hx=paired_manifests('abc',cfg); audit=allowed_branch_delta(h0,hx)
    assert audit['pass']
    assert set(audit['delta'])=={'branch_id','counterfactual_role','deep_biological_coupling_enabled'}
    assert h0['common_state_semantic_sha256']==hx['common_state_semantic_sha256']=='abc'
    assert h0['paired_rng_seed']==hx['paired_rng_seed']==917231
    assert h0['physical_deep_present'] and hx['physical_deep_present']

def test_materialized_conservation_audit_passes():
    d=json.loads((ROOT/'outputs'/'v0_6D1_R1'/'REBASELINE_CONSERVATION_AUDIT_v0_6D1_R1.json').read_text())
    assert d['status']=='PASS'
    assert d['max_cell_population_closure_abs']<1e-12
    assert d['max_cell_capacity_closure_abs']<1e-12
    assert d['population_exceeds_capacity_count']==0
    assert d['nonland_population_cells']==0

def test_initial_deep_exposure_is_noncatastrophic_and_unselected_by_construction():
    d=json.loads((ROOT/'outputs'/'v0_6D1_R1'/'INITIAL_DEEP_EXPOSURE_AUDIT_v0_6D1_R1.json').read_text())
    assert d['status']=='PASS_INITIAL_DEEP_EXPOSURE_NONCATASTROPHIC'
    assert d['regime_population_fraction']['negligible']==1.0
    assert d['regime_population_fraction']['tolerance_exceeded']==0.0
    assert d['regime_population_fraction']['injury']==0.0

def test_radius_compatibility_sensitivity_is_bounded():
    meta,a1,*_=inputs(); base=decompose_guild_state(meta,a1,RebaselineConfig())['species_population'].sum((1,2))
    for factor in (0.95,1.05):
        test=decompose_guild_state(meta,a1,RebaselineConfig(compatibility_radius_km=6371.0088*factor))['species_population'].sum((1,2))
        rel=np.abs(test-base)/np.maximum(base,1e-30)
        assert float(np.max(rel))<0.05
        assert float(np.median(rel))<0.011

def test_output_common_state_has_expected_shape_and_identity():
    z=np.load(ROOT/'outputs'/'v0_6D1_R1'/'WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz',allow_pickle=False)
    assert z['species_population'].shape==(120,90,180)
    assert z['deep_latent_mean'].shape==(120,10)
    assert z['deep_latent_additive_variance'].shape==(120,10)
    assert np.all(z['deep_latent_mean']==0)
    assert np.all(z['deep_latent_additive_variance']==0.045)
