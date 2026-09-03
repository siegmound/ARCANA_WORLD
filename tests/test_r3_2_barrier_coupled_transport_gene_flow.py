from pathlib import Path
import hashlib, json, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import rebased_natural_control_runtime_v0_6D1_R3_2 as r32


def _q_from_state(path):
    st=np.load(path,allow_pickle=False)
    md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text())
    rows=md['species'] if isinstance(md,dict) and 'species' in md else md
    M={r['species_id']:r for r in rows}
    q=[]
    for i,s in enumerate(st['component_root_species'].astype(str)):
        m=M[s]
        sc=np.array([m['thermal_niche_sigma_c'], max(m['aridity_niche_sigma']/1.55,1e-4), 5.0])
        q.extend((st['va'][i]/(sc*sc)).tolist())
    return np.asarray(q)


def test_d3_2b_source_hash_is_exact():
    p=ROOT/'references/v0_6D1_R2_1/d3_sealed/diversification_adequacy_v0_6_3D3_2B.py'
    assert hashlib.sha256(p.read_bytes()).hexdigest() == '9c2338cd8904bd6f9972c253be375384f6ec57193b4e3f5acf404f1ef2f344b2'


def test_no_custom_vectorized_migration_is_retained():
    src=(ROOT/'src/rebased_natural_control_runtime_v0_6D1_R3_2.py').read_text()
    assert '_migration_with_permeability_vectorized' not in src
    assert 'd3b._migration_with_permeability' in src
    assert 'd3b._pair_metrics_extended' in src


def test_210_205_validation_keeps_vicariance_without_birth_or_extinction():
    d=json.loads((ROOT/'outputs/v0_6D1_R3_2/R3_2_210_205_VALIDATION_SUMMARY.json').read_text())
    assert d['species_count'] == 120
    assert d['component_count'] == 151
    assert d['event_counts'].get('deme_fission') == 18
    assert d['event_counts'].get('speciation',0) == 0
    assert d['event_counts'].get('ordinary_background_extinction',0) == 0


def test_210_205_va_is_far_below_hard_ceiling():
    q=_q_from_state(ROOT/'outputs/v0_6D1_R3_2/R3_2_210_205_VALIDATION_STATE.npz')
    assert float(q.max()) < 0.02
    assert not np.any(q > 0.05 + 1e-12)
    assert not np.any(q >= 0.0495)


def test_210_205_gene_flow_moment_closure():
    d=json.loads((ROOT/'outputs/v0_6D1_R3_2/R3_2_210_205_VALIDATION_SUMMARY.json').read_text())
    c=d['gene_flow_closure']
    assert c['first_moment_conservation_max_abs'] < 1e-9
    assert c['second_moment_conservation_max_abs'] < 1e-8
    assert c['edge_count'] > 0


def test_210_206_validation_matures_persistent_vicariance():
    d=json.loads((ROOT/'outputs/v0_6D1_R3_2/R3_2_210_206_VALIDATION_SUMMARY.json').read_text())
    assert d['species_count'] == 120
    assert d['component_count'] == 148
    assert d['event_counts'].get('deme_fission') == 15
    assert d['event_counts'].get('speciation',0) == 0
