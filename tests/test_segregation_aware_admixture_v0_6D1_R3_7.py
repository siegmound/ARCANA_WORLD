from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

import numpy as np

from arcana_worldsim.post_cha1 import additive_variance as legacy
from arcana_worldsim.scientific_engines.segregation_aware_admixture import (
    SegregationAwareAdmixtureConfig,
    build_exchange_transition,
    qtl_segregation_potential,
    recombination_decay_factors,
    segregation_aware_gene_flow_mix,
    transform_segregation_potential,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "reference_results" / "v0_6D1_R3_6D_RAW_RESULTS.zip"


def _simple_qtl():
    a = np.array([[0.1, 0.2, 0.15], [0.07, 0.11, 0.13]])
    p = np.array([
        [[0.2, 0.3, 0.4], [0.25, 0.35, 0.45]],
        [[0.8, 0.7, 0.6], [0.75, 0.65, 0.55]],
    ])
    return a, p


def _moments(a, p):
    z = np.sum(a[None, :, :] * (2.0 * p - 1.0), axis=-1)
    va = np.sum(2.0 * a[None, :, :] ** 2 * p * (1.0 - p), axis=-1)
    return z, va


def test_qtl_segregation_potential_exact_two_source_identity():
    a, p = _simple_qtl(); s = qtl_segregation_potential(a, p)
    w = 0.2
    pm = (1-w)*p[0] + w*p[1]
    _, v = _moments(a, p)
    vm = np.sum(2.0*a*a*pm*(1-pm), axis=-1)
    expected = (1-w)*v[0] + w*v[1] + w*(1-w)*s[0,1]
    assert np.allclose(vm, expected, atol=1e-14, rtol=0)


def test_transition_mean_semantics_match_legacy_d3_3a():
    z=np.array([[-0.5,0.3,0.0],[0.5,-0.3,0.0]])
    va=np.full_like(z,0.045); n=np.array([1000.,1000.]); g=np.array([[0,.05],[.05,0.]])
    ri=np.zeros((2,2)); sid=np.zeros(2,dtype=int)
    cfg=SegregationAwareAdmixtureConfig()
    p,_=build_exchange_transition(n,g,ri,sid,cfg)
    z_old,_,_=legacy.gene_flow_moment_mix(z,va,n,g,ri,sid,legacy.AdditiveVarianceConfig(maximum_total_exchange_fraction_per_deme=.45))
    assert np.allclose(p@z,z_old,atol=1e-14,rtol=0)


def test_repaired_operator_matches_direct_qtl_allele_frequency_mixing():
    a,pfreq=_simple_qtl(); z,va=_moments(a,pfreq); s=qtl_segregation_potential(a,pfreq)
    n=np.array([1000.,1000.]); g=np.array([[0,.05],[.05,0.]]); ri=np.zeros((2,2)); sid=np.zeros(2,dtype=int)
    out=segregation_aware_gene_flow_mix(z,va,np.zeros_like(va),s,n,g,ri,sid,np.full(2,5.),125000.)
    z2,v2,_,s2,diag=out
    trans,_=build_exchange_transition(n,g,ri,sid)
    pm=np.einsum('ij,jtl->itl',trans,pfreq)
    z_direct,v_direct=_moments(a,pm)
    s_direct=qtl_segregation_potential(a,pm)
    assert np.allclose(z2,z_direct,atol=2e-14,rtol=0)
    assert np.allclose(v2,v_direct,atol=2e-14,rtol=0)
    assert np.allclose(s2,s_direct,atol=2e-14,rtol=0)
    assert diag['pre_recombination_total_variance_closure_max_abs'] < 1e-14


def test_free_recombination_decays_transient_ancestry_not_genic_va():
    inh,uniform=recombination_decay_factors(np.array([5.0]),125000.0,0.5)
    assert inh[0] < 1e-100
    assert 0.0 < uniform[0] < 1e-4


def test_no_flow_identity():
    a,pfreq=_simple_qtl(); z,va=_moments(a,pfreq); s=qtl_segregation_potential(a,pfreq)
    out=segregation_aware_gene_flow_mix(z,va,np.zeros_like(va),s,np.array([1000.,1000.]),np.zeros((2,2)),np.zeros((2,2)),np.zeros(2,dtype=int),np.full(2,5.),125000.)
    assert np.allclose(out[0],z); assert np.allclose(out[1],va); assert np.allclose(out[3],s)


def test_current_species_gate_blocks_cross_species_exchange():
    a,pfreq=_simple_qtl(); z,va=_moments(a,pfreq); s=qtl_segregation_potential(a,pfreq)
    g=np.array([[0,.2],[.2,0.]])
    out=segregation_aware_gene_flow_mix(z,va,np.zeros_like(va),s,np.array([1000.,1000.]),g,np.zeros((2,2)),np.array([0,1]),np.full(2,5.),125000.)
    assert np.allclose(out[0],z); assert np.allclose(out[1],va)


def test_r36d_qtl_references_close_exactly_under_r37_operator():
    with zipfile.ZipFile(RAW) as zf:
        jobs=[]
        for name in zf.namelist():
            if not name.endswith('/R3_6D_JOB.json'): continue
            job=json.loads(zf.read(name))
            if job.get('variant')=='FLOW' and int(job['population_size'])==2000 and int(job['replicate'])==0:
                jobs.append((name,job))
        assert len(jobs)==4  # B1/C3 x 2 axes
        for job_path,job in jobs:
            job_dir=job_path.rsplit('/',1)[0]+'/'
            variant_dir=job_dir.rsplit('axis_',1)[0]
            with np.load(io.BytesIO(zf.read(variant_dir+'qtl/qtl_expected_state.npz'))) as data:
                effects=np.asarray(data['effect_sizes'],float)
                freqs=np.asarray(data['allele_frequencies'],float)
                expected_va=np.asarray(data['expected_variances'],float)
                expected_means=np.asarray(data['expected_means'],float)
            axis=int(job['axis'])
            m=np.loadtxt(io.StringIO(zf.read(job_dir+'nemo_per_generation_dispersal.tsv').decode()))
            manifest=json.loads(zf.read(job_dir+'R3_6D_NEMO_BINDING_MANIFEST.json'))
            interval=np.linalg.matrix_power(m,int(manifest['nemo_transitions']))
            g=interval.copy(); np.fill_diagonal(g,0.0)
            z=expected_means[:,axis:axis+1]
            va=expected_va[:,axis:axis+1]
            s=qtl_segregation_potential(effects[axis:axis+1],freqs[:,axis:axis+1,:])
            n=np.full(z.shape[0],2000.,float)
            z2,v2,_,s2,_=segregation_aware_gene_flow_mix(z,va,np.zeros_like(va),s,n,g,np.zeros_like(g),np.zeros(z.shape[0],dtype=int),np.full(z.shape[0],5.),125000.)
            pm=interval@freqs[:,axis,:]
            direct=2.0*np.sum((effects[axis][None,:]**2)*pm*(1-pm),axis=1)
            assert np.allclose(v2[:,0],direct,atol=2e-10,rtol=0)
            assert np.allclose(s2,qtl_segregation_potential(effects[axis:axis+1],pm[:,None,:]),atol=2e-10,rtol=0)


def test_r37_candidate_is_fail_closed():
    cfg=SegregationAwareAdmixtureConfig()
    assert cfg.maximum_total_exchange_fraction_per_deme == 0.45
    # R3.7 does not expose mu, b, q_star or a production/canonical switch.
    assert not hasattr(cfg,'mutation_q_per_myr')
    assert not hasattr(cfg,'nonlinear_b_per_myr_per_q')
