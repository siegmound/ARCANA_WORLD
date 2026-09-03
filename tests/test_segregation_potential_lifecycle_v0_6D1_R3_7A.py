from __future__ import annotations

from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines.segregation_aware_admixture import qtl_segregation_potential
from arcana_worldsim.scientific_engines.segregation_potential_lifecycle import (
    ReducedGeneticLifecycleState,
    advance_directional_selection_coordinate,
    advance_neutral_potential_by_drift,
    coalesce_group_state,
    compose_total_segregation_potential,
    fission_clone_state,
    initialize_minimum_information_state,
    mutation_supply_effect_on_segregation_potential,
    reproductive_pair_authority_mask,
    speciation_identity_transition,
)
from arcana_worldsim.scientific_engines.r37a_validation import analyze_r37a_parent_reference

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'reference_results'/'v0_6D1_R3_6D_RAW_RESULTS.zip'


def _qtl_state():
    effects=np.array([[0.08,0.12,0.10,0.07]])
    p=np.array([
        [[0.25,0.30,0.35,0.40]],
        [[0.75,0.70,0.65,0.60]],
    ])
    z=np.sum(effects[None,:,:]*(2*p-1),axis=-1)
    va=np.sum(2*effects[None,:,:]**2*p*(1-p),axis=-1)
    s=qtl_segregation_potential(effects,p)
    return effects,p,z,va,s


def test_210ma_initialization_is_minimum_information_and_species_masked():
    va=np.full((3,2),0.045)
    st,diag=initialize_minimum_information_state(va,['A','A','B'])
    assert np.all(st.total_segregation_potential==0)
    assert np.all(st.ancestry_covariance==0)
    mask=reproductive_pair_authority_mask(['A','A','B'])
    assert mask[0,1] and not mask[0,2] and not mask[1,2]
    assert not diag['hidden_genomic_divergence_invented']


def test_selection_coordinate_matches_equal_participation_qtl_identity():
    # L equally participating loci shifted by the same dp have
    # S = dz^2/(2L), exactly the R3.7A selection-coordinate mapping.
    L=64; a=np.full(L,0.01); p0=np.full(L,0.4); dp=0.05
    p1=p0+dp
    dz=2*np.sum(a*(p1-p0))
    direct=2*np.sum(a*a*(p1-p0)**2)
    h=np.zeros((2,1)); z0=np.zeros((2,1)); z1=np.array([[0.0],[dz]])
    hout,_=advance_directional_selection_coordinate(h,z0,z1,effective_polygenic_dimension=L)
    s=compose_total_segregation_potential(np.zeros((2,2,1)),hout)
    assert np.isclose(s[0,1,0],direct,atol=1e-16,rtol=0)


def test_drift_transfer_uses_d3_3a_rate_and_preserves_euclidean_state():
    sn=np.zeros((2,2,1)); va=np.full((2,1),0.045)
    out,lost,diag=advance_neutral_potential_by_drift(sn,va,np.array([2000.,2000.]),np.array([5.,5.]),125000.)
    retain=np.exp(-25000/(2*2000))
    expected=2*0.045*(1-retain)
    assert np.isclose(out[0,1,0],expected,atol=1e-15,rtol=0)
    assert np.isclose(lost[0,0],0.045*(1-retain),atol=1e-15,rtol=0)
    assert not diag['new_drift_rate_introduced']


def test_mutation_supply_does_not_invent_directional_between_deme_motion():
    sn=np.zeros((2,2,1))
    out,diag=mutation_supply_effect_on_segregation_potential(sn)
    assert np.array_equal(out,sn)
    assert diag['deterministic_segregation_increment']==0.0
    assert not diag['mu_changed']


def test_fission_clones_latent_position_exactly():
    _,_,z,va,s=_qtl_state()
    st=ReducedGeneticLifecycleState(va,np.zeros_like(va),s,np.zeros_like(va))
    out,diag=fission_clone_state(st,0)
    total=out.total_segregation_potential
    assert total.shape==(3,3,1)
    assert total[0,2,0]==0
    assert np.isclose(total[2,1,0],total[0,1,0])
    assert np.allclose(out.va_within[2],out.va_within[0])
    assert diag['parent_daughter_segregation_max_abs']==0


def test_coalescence_matches_direct_qtl_allele_frequency_pooling():
    effects,p,z,va,s=_qtl_state()
    st=ReducedGeneticLifecycleState(va,np.zeros_like(va),s,np.zeros_like(va))
    masses=np.array([300.,700.]); w=masses/masses.sum()
    out,zout,keep,diag=coalesce_group_state(st,z,masses,[0,1],survivor_index=0)
    pm=w[0]*p[0]+w[1]*p[1]
    direct_va=np.sum(2*effects**2*pm*(1-pm),axis=-1)
    direct_z=np.sum(effects*(2*pm-1),axis=-1)
    assert out.deme_count==1
    assert np.allclose(out.va_within[0],direct_va,atol=1e-15,rtol=0)
    assert np.allclose(zout[0],direct_z,atol=1e-15,rtol=0)
    assert diag['first_moment_conservation_max_abs']<2e-14
    assert not diag['despeciation_authorized']


def test_speciation_changes_identity_only_and_never_resets_genetics():
    _,_,z,va,s=_qtl_state()
    st=ReducedGeneticLifecycleState(va,np.zeros_like(va),s,np.zeros_like(va))
    out,sids,diag=speciation_identity_transition(st,['A','A'],[1],'A_D1')
    assert out is st
    assert sids==['A','A_D1']
    assert diag['segregation_state_change_max_abs']==0
    assert diag['va_state_change_max_abs']==0
    assert not diag['cross_species_gene_flow_authorized']


def test_parent_nemo_b0_validates_drift_transfer_and_keff_is_not_silently_literal_loci():
    r=analyze_r37a_parent_reference(RAW)
    assert r['verdict'].startswith('PASS_PARENT_NEMO_DRIFT_REFERENCE')
    d=r['drift_reference']
    assert d['row_count']==8
    assert d['max_abs_fractional_deviation']<0.30
    k=r['polygenic_participation_reference']
    assert 40 < k['minimum'] < k['maximum'] <= 64.1
    assert k['literal_qtl_loci']==64


def test_r37a_remains_fail_closed_for_production_selection_mapping():
    r=analyze_r37a_parent_reference(RAW)
    assert not r['canonical_write_allowed']
    assert not r['production_selection_mapping_authorized']
