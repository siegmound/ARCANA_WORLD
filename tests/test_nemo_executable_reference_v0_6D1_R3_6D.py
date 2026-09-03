from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import numpy as np
import pytest

from arcana_worldsim.scientific_engines.nemo_qtl_ensemble import NemoQTLArchitectureSpec, build_qtl_realization
from arcana_worldsim.scientific_engines.nemo242_r36d import (
    NEMO_REQUIRED_EXECUTABLE,
    Nemo242ExecutableReferenceSpec,
    canonical_r36d_scenarios,
    collect_nemo242_evidence,
    parse_qfreq,
    preflight_nemo242,
    render_nemo242_axis_ini,
)


def _realization(s, seed=1, loci=16):
    return build_qtl_realization(
        s.normalized_trait_means, s.normalized_additive_variance,
        trait_axes=(0,1), seed=seed,
        spec=NemoQTLArchitectureSpec(loci_per_trait=loci, individual_sample_size=int(s.population_individuals[0])),
        individuals_per_patch=s.population_individuals,
    )


def test_r36d_scenarios_are_b0_b1_c3_and_b3_is_not_rewritten():
    ss=canonical_r36d_scenarios(n_individuals=200)
    assert [s.name for s in ss] == ["B0_EQUILIBRIUM_NO_FLOW","B1_TWO_DEME_ADMIXTURE","C3_EMBEDDABLE_HIGH_ADMIXTURE_STRESS"]
    assert all(len(s.phases)==1 for s in ss)


def test_primary_reference_refuses_nonzero_mutation_or_nonfree_recombination():
    with pytest.raises(ValueError, match="mutation rate"):
        Nemo242ExecutableReferenceSpec(mutation_rate_per_locus=1e-5)
    with pytest.raises(ValueError, match="free recombination"):
        Nemo242ExecutableReferenceSpec(recombination_rate=0.1)


def test_renderer_uses_only_upstream_bound_core_parameters_and_half_effect_mapping(tmp_path: Path):
    s=canonical_r36d_scenarios(n_individuals=200)[1]
    r=_realization(s,loci=16)
    m=render_nemo242_axis_ini(s,r,trait_local_index=0,seed=123,output_dir=tmp_path)
    text=(tmp_path/'Nemo2_ARCANA_R36D.ini').read_text()
    for token in [
        'quanti_init             1','quanti_init_freq','quanti_allele_value',
        'quanti_allele_model     diallelic','quanti_mutation_rate    0',
        'quanti_recombination_rate 0.5','breed_disperse_matrix','quanti_freq_output      1',
        'stat                    adlt.demography adlt.quanti','patch_nbfem','patch_nbmal             0','breed_disperse          2',
    ]:
        assert token in text
    half=np.loadtxt(tmp_path/'nemo_allele_half_effects.tsv',delimiter='\t',ndmin=2)[0]
    assert np.allclose(half,0.5*r.effect_sizes[0])
    assert m['canonical_write_allowed'] is False
    assert m['automatic_calibration_allowed'] is False
    assert m['protocol']=='ADMIXTURE_RECOMBINATION_DRIFT_ONLY'
    assert 'disperse                3' not in text
    assert 'breed                   2' not in text
    assert m['dispersal_semantics'].startswith('NEMO_BREED_DISPERSE_BACKWARD_GAMETIC')


def test_renderer_cadence_normalizes_b1_to_small_per_generation_migration(tmp_path: Path):
    s=canonical_r36d_scenarios(n_individuals=200)[1]; r=_realization(s,loci=16)
    render_nemo242_axis_ini(s,r,trait_local_index=0,seed=3,output_dir=tmp_path)
    d=np.loadtxt(tmp_path/'nemo_per_generation_dispersal.tsv',delimiter='\t')
    assert np.allclose(d.sum(axis=1),1.0,atol=1e-12)
    assert np.allclose(d.sum(axis=0),1.0,atol=1e-12)
    assert np.allclose(d,d.T,atol=1e-12)
    assert 0 < d[0,1] < 1e-5


def test_renderer_maps_125k_to_25000_transitions_plus_initialized_generation(tmp_path: Path):
    s=canonical_r36d_scenarios(n_individuals=200)[0]; r=_realization(s,loci=16)
    m=render_nemo242_axis_ini(s,r,trait_local_index=0,seed=3,output_dir=tmp_path)
    assert m['nemo_transitions']==25000
    assert m['nemo_generations_parameter']==25001




def test_renderer_qfreq_schedule_hits_final_generation(tmp_path: Path):
    s=canonical_r36d_scenarios(n_individuals=200)[0]; r=_realization(s,loci=16)
    m=render_nemo242_axis_ini(s,r,trait_local_index=0,seed=3,output_dir=tmp_path)
    text=(tmp_path/'Nemo2_ARCANA_R36D.ini').read_text()
    assert m['nemo_generations_parameter']==25001
    assert m['quanti_freq_logtime']==25001
    assert 'quanti_freq_logtime     25001' in text
    assert m['qfreq_persistence_semantics'].startswith('FINAL_GENERATION_CALLBACK_REQUIRED')


def test_renderer_refuses_qfreq_schedule_that_misses_final_generation(tmp_path: Path):
    s=canonical_r36d_scenarios(n_individuals=200)[0]; r=_realization(s,loci=16)
    spec=Nemo242ExecutableReferenceSpec(quanti_freq_logtime=25000)
    with pytest.raises(ValueError, match='must divide the NEMO generations parameter'):
        render_nemo242_axis_ini(s,r,trait_local_index=0,seed=3,output_dir=tmp_path,spec=spec)


def test_qfreq_parser_reconstructs_known_moments(tmp_path: Path):
    # two loci, two patches, two recorded generations; p is the increasing allele.
    q=tmp_path/'x.qfreq'
    q.write_text(
        'pop trait locus allele g1 g2\n'
        '1 1 1 0.5 0.5 0.75\n'
        '1 1 2 0.5 0.5 0.25\n'
        '2 1 1 0.5 0.25 0.5\n'
        '2 1 2 0.5 0.75 0.5\n',encoding='utf-8')
    p=parse_qfreq(q,arcana_effect_a=[1.0,1.0])
    assert p['allele_frequencies'].shape==(2,2,2)
    assert np.allclose(p['trait_mean'][0],[0.0,0.0])
    assert np.allclose(p['additive_variance'][0],[1.0,0.75])
    assert np.allclose(p['trait_mean'][1],[0.0,0.0])


def test_evidence_bundle_never_promotes_and_parses_qfreq(tmp_path: Path):
    (tmp_path/'run.qfreq').write_text('pop trait locus allele g1\n1 1 1 0.5 0.5\n',encoding='utf-8')
    ev=collect_nemo242_evidence(experiment_sha256='a'*64,run_id='r',workdir=tmp_path,arcana_effect_a=[1.0],execution_returncode=0)
    assert ev.status=='ENGINE_COMPLETED_QFREQ_PARSED'
    assert ev.engine.canonical_write_allowed is False
    assert np.isfinite(ev.arrays['additive_variance']).all()


def test_preflight_exact_executable_name_is_fail_closed_when_missing():
    p=preflight_nemo242(NEMO_REQUIRED_EXECUTABLE)
    assert p.exact_version_name is True
    # CI/container may or may not have NEMO; both states are valid, but wrong names aren't.
    bad=preflight_nemo242('nemo')
    assert bad.pass_exact_242 is False
    assert bad.reason=='WRONG_EXECUTABLE_BASENAME'


def test_matched_no_flow_preserves_start_state_only_removes_exchange():
    from arcana_worldsim.scientific_engines.nemo242_r36d import matched_no_flow_scenario
    s=canonical_r36d_scenarios(n_individuals=200)[1]; c=matched_no_flow_scenario(s)
    assert np.array_equal(c.normalized_trait_means,s.normalized_trait_means)
    assert np.array_equal(c.normalized_additive_variance,s.normalized_additive_variance)
    assert np.array_equal(c.population_individuals,s.population_individuals)
    assert np.count_nonzero(c.phases[0].exchange_matrix)==0


def test_arcana_admixture_only_flow_exceeds_matched_no_flow_in_b1():
    from arcana_worldsim.scientific_engines.nemo242_r36d import matched_no_flow_scenario, simulate_arcana_admixture_only_probe
    s=canonical_r36d_scenarios(n_individuals=2000)[1]; c=matched_no_flow_scenario(s)
    f=simulate_arcana_admixture_only_probe(s,macro_intervals=1,substeps_per_interval=1)
    z=simulate_arcana_admixture_only_probe(c,macro_intervals=1,substeps_per_interval=1)
    assert f['final_mean_va'] > z['final_mean_va']
    assert z['final_mean_va'] == pytest.approx(0.045)
