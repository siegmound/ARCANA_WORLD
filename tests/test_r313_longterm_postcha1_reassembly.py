from pathlib import Path
import json, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r312_postcha1_diversity_recovery as r312
from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313


def _rows():
    d=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
    return d['species'] if isinstance(d,dict) and 'species' in d else d


def test_parent_r312_sealed_boundary_exact():
    a=r313.validate_parent_r312_authority(ROOT); st=a['state']
    assert st.age_ma == 46.0 and st.elapsed_year == 164_000_000.0
    assert len(set(st.current_species)) == 104 and len(st.component_ids) == 223
    assert a['checkpoint_json_sha256'] == '6189f16fd3d7b390ad33afb57eaa36fef0bdbcf7f1498fa7396d3d1f81843269'
    assert a['checkpoint_npz_sha256'] == '92b410ce3258c44ba0f4b911776628d880fbe5a5fe3be3b9b6fe13dc34973948'


def test_scientific_parameters_are_inherited_not_retuned():
    a=r313.R313Config(); b=r312.R312Config()
    fields=['biology_cadence_years','transport_cadence_years','speciation_check_interval_years',
    'ordinary_extinction_check_interval_years','ordinary_extinction_minimum_persistence_years',
    'founder_minimum_persistence_years','vicariance_persistence_min_years','reconnection_persistence_min_years',
    'mutation_variance_supply_normalized_per_myr','nonlinear_stabilizing_variance_depletion_per_myr_per_q',
    'selection_variance_depletion_per_generation','variance_ceiling_normalized','migration_reference_years',
    'migration_fraction_ceiling','gene_flow_ceiling_per_step','minimum_effective_isolation_generations',
    'minimum_intrinsic_ri','minimum_trait_distance','maximum_effective_exchange_pressure','adaptive_k_eff',
    'segregation_recombination_fraction_per_generation','deme_fission_check_interval_years','reconnection_check_interval_years']
    for f in fields: assert getattr(a,f)==getattr(b,f),f
    assert a.end_age_ma == 30.0


def test_canonical_window_hits_existing_late_cenozoic_boundary():
    c=r313.R313Config()
    assert r313.START_AGE_MA == 46.0 and r313.END_AGE_MA == 30.0
    assert int(round((46.0-30.0)*1e6/c.biology_cadence_years)) == 128


def test_30ma_environmental_handoff_is_exact_endpoint_identity():
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    d=r313.validate_30ma_environment_handoff(a1)
    assert d['environmental_endpoint_identity_exact'] is True
    assert all(v['exact'] and v['max_abs_error']==0.0 for v in d['fields'].values())
    assert d['biology_switched_in_r313'] is False


def test_one_step_no_cha1_thaw_or_crossguild_insertion():
    p=r313.validate_parent_r312_authority(ROOT)['state']; before=r313.event_counts(p)
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    out,recs=r313.run_longterm_reassembly(p,a1,_rows(),r313.R313Config(),45.875)
    after=r313.event_counts(out)
    assert len(recs)==1 and out.age_ma==45.875
    assert after['CHA1_species_extinction']==before['CHA1_species_extinction']==212
    assert after['CHA1_high_resolution_event_bridge_complete']==before['CHA1_high_resolution_event_bridge_complete']==1
    assert after['post_CHA1_ordinary_lifecycle_thaw']==before['post_CHA1_ordinary_lifecycle_thaw']==1
    assert p.age_ma==46.0


def test_reassembly_diagnostic_does_not_require_guild_recreation():
    p=r313.validate_parent_r312_authority(ROOT)['state']
    d=r313.ecological_reassembly_report(p,p)
    assert d['descriptive_not_acceptance_target'] is True
    assert d['cross_guild_recreation_authorized'] is False
    assert 6 in d['guilds_absent_at_46Ma']
