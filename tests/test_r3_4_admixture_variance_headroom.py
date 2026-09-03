import json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
import rebased_natural_control_runtime_v0_6D1_R3_3 as r33


def _metadata():
    x=json.loads((ROOT/'references/D1_species_metadata.json').read_text())
    if isinstance(x,dict) and 'species' in x:x=x['species']
    return {r['species_id']:r for r in x}

def _env():
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    return r34.bp.environment_at(190.0,a1,r34.barrier_cfg(r34.R34Config()))

def test_ceiling_candidate_is_0p08_and_homeostasis_unchanged():
    c=r34.R34Config()
    assert c.variance_ceiling_normalized == 0.08
    assert c.mutation_variance_supply_normalized_per_myr == 0.002
    assert abs(c.nonlinear_stabilizing_variance_depletion_per_myr_per_q-0.9876543209876544)<1e-15

def test_pair_metrics_are_current_species_bound():
    md=_metadata(); env=_env(); cfg=r34.R34Config()
    pop=np.zeros((2,90,180),float); pop[:,45,90]=1.0
    trait=np.zeros((2,3),float)
    roots=['HSG_001','HSG_001']; current=['HSG_001','HSG_001_D01']
    G,contact,td=r34._pair_metrics_barrier_coupled(pop,trait,roots,current,md,np.linspace(-89,89,90),np.linspace(-179,179,180),env,cfg)
    assert G[0,1] == 0.0 and contact[0,1] == 0.0

def test_same_current_species_retains_gene_flow():
    md=_metadata(); env=_env(); cfg=r34.R34Config()
    pop=np.zeros((2,90,180),float); pop[:,45,90]=1.0
    trait=np.zeros((2,3),float)
    roots=['HSG_001','HSG_001']; current=['HSG_001','HSG_001']
    G,contact,td=r34._pair_metrics_barrier_coupled(pop,trait,roots,current,md,np.linspace(-89,89,90),np.linspace(-179,179,180),env,cfg)
    assert G[0,1] > 0.0 and contact[0,1] > 0.0

def test_headroom_audit_selects_nonbinding_0p08():
    p=ROOT/'outputs/v0_6D1_R3_4/HEADROOM_AUDIT_v0_6D1_R3_4.json'
    d=json.loads(p.read_text())
    assert d['verdict'].startswith('PASS_')
    assert d['calibration_decision']['selected_candidate_ceiling']==0.08
    by={x['ceiling']:x for x in d['experiments']}
    assert by[0.075]['fraction_ge_99pct_ceiling'] > 0
    assert by[0.08]['fraction_ge_99pct_ceiling'] == 0
    assert abs(by[0.08]['max_q']-by[0.1]['max_q']) < 1e-12

def test_r33_reference_contains_cross_current_species_geometric_contacts():
    d=json.loads((ROOT/'outputs/v0_6D1_R3_4/HEADROOM_AUDIT_v0_6D1_R3_4.json').read_text())
    assert d['semantic_identity_audit']['cross_current_species_contact_edges_within_same_root'] == 131
